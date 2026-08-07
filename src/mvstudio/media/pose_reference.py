"""Convert any video into a face-free pose-landmark reference video.

The output keeps only skeletal motion (MediaPipe pose landmarks rendered as a
stick figure on a flat canvas) — no appearance, no identity. Use it as a
choreography/timing reference that carries motion without carrying a face.

Reusable across agents. Heavy CV deps (cv2, mediapipe) are imported lazily so
importing this module never fails when they are absent — the friendly error is
raised only if you actually call ``generate_pose_reference``.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

# ── model resolution ────────────────────────────────────────────────────────
# Repo root = .../src/mvstudio/media/pose_reference.py → parents[3]
_REPO_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_MODEL = _REPO_ROOT / "assets" / "models" / "pose_landmarker_lite.task"
_MODEL_ENV = "POSE_LANDMARKER_MODEL"

# MediaPipe pose landmark topology (indices 11..32 — torso/limbs, no face).
CONNECTIONS = (
    (11, 12),
    (11, 13), (13, 15), (15, 17), (15, 19), (15, 21),
    (12, 14), (14, 16), (16, 18), (16, 20), (16, 22),
    (11, 23), (12, 24), (23, 24),
    (23, 25), (25, 27), (27, 29), (29, 31), (27, 31),
    (24, 26), (26, 28), (28, 30), (30, 32), (28, 32),
)
JOINTS = tuple(range(11, 33))
_BG = (247, 247, 244)


class PoseReferenceError(RuntimeError):
    """Raised when pose-reference generation cannot proceed or is too sparse."""


@dataclass(frozen=True)
class PoseReferenceResult:
    """Outcome of a pose-reference render."""

    output: Path
    frames: int
    detected: int
    fps: float
    width: int
    height: int

    @property
    def coverage(self) -> float:
        return (self.detected / self.frames) if self.frames else 0.0


def resolve_model_path(model: Optional[os.PathLike | str] = None) -> Path:
    """Resolve the pose-landmarker model file.

    Priority: explicit arg → ``POSE_LANDMARKER_MODEL`` env → repo default
    (``assets/models/pose_landmarker_lite.task``).
    """
    candidate = model or os.environ.get(_MODEL_ENV) or _DEFAULT_MODEL
    path = Path(candidate).expanduser()
    if not path.is_file():
        raise PoseReferenceError(
            f"Pose model not found: {path}. Place it at {_DEFAULT_MODEL}, "
            f"or set {_MODEL_ENV}, or pass model=."
        )
    return path


def _require_cv() -> tuple:
    """Import cv2 + mediapipe lazily with a friendly error if missing."""
    try:
        import cv2  # noqa: PLC0415
        import mediapipe as mp  # noqa: PLC0415
        from mediapipe.tasks import python  # noqa: PLC0415
        from mediapipe.tasks.python import vision  # noqa: PLC0415
    except ImportError as exc:  # pragma: no cover - env dependent
        raise PoseReferenceError(
            "Pose reference needs opencv-python + mediapipe. "
            "Install: pip install 'opencv-python>=4.8' 'mediapipe>=0.10'"
        ) from exc
    return cv2, mp, python, vision


def _point(np, landmarks, index: int, width: int, height: int) -> tuple[int, int]:
    lm = landmarks[index]
    x = int(np.clip(lm.x, 0.0, 1.0) * (width - 1))
    y = int(np.clip(lm.y, 0.0, 1.0) * (height - 1))
    return x, y


def _smooth(current, previous, alpha: float):
    if previous is None:
        return current
    for now, before in zip(current, previous):
        now.x = alpha * now.x + (1.0 - alpha) * before.x
        now.y = alpha * now.y + (1.0 - alpha) * before.y
        now.z = alpha * now.z + (1.0 - alpha) * before.z
    return current


def _render(cv2, np, landmarks, width: int, height: int, frame_number: int, *, label: bool):
    canvas = np.full((height, width, 3), _BG, dtype=np.uint8)
    cv2.rectangle(canvas, (0, 0), (width - 1, height - 1), (210, 214, 211), 3)
    for start, end in CONNECTIONS:
        a = _point(np, landmarks, start, width, height)
        b = _point(np, landmarks, end, width, height)
        cv2.line(canvas, a, b, (38, 55, 70), 8, cv2.LINE_AA)
    for index in JOINTS:
        center = _point(np, landmarks, index, width, height)
        color = (28, 126, 108) if index < 23 else (40, 94, 184)
        cv2.circle(canvas, center, 9, color, -1, cv2.LINE_AA)
        cv2.circle(canvas, center, 9, (255, 255, 255), 2, cv2.LINE_AA)
    if label:
        cv2.putText(
            canvas, f"POSE MOTION  {frame_number:04d}", (24, 48),
            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (70, 76, 73), 2, cv2.LINE_AA,
        )
    return canvas


def generate_pose_reference(
    source: os.PathLike | str,
    output: os.PathLike | str,
    *,
    model: Optional[os.PathLike | str] = None,
    smoothing: float = 0.72,
    min_confidence: float = 0.35,
    min_coverage: float = 0.65,
    label: bool = True,
) -> PoseReferenceResult:
    """Render ``source`` into a face-free pose-skeleton video at ``output``.

    Args:
        source: input video (any person/appearance — none of it is kept).
        output: destination .mp4 path.
        model: pose-landmarker .task path (see ``resolve_model_path``).
        smoothing: EMA factor in (0,1]; higher = less smoothing, more responsive.
        min_confidence: detection/presence/tracking confidence floor.
        min_coverage: minimum detected/total frame ratio, else raise.
        label: draw the "POSE MOTION NNNN" frame counter overlay.

    Returns:
        PoseReferenceResult with frame counts and coverage.

    Raises:
        PoseReferenceError: deps missing, unreadable IO, or coverage too low.
    """
    cv2, mp, python, vision = _require_cv()
    import numpy as np  # noqa: PLC0415

    src = Path(source).expanduser()
    if not src.is_file():
        raise PoseReferenceError(f"Source video not found: {src}")
    model_path = resolve_model_path(model)
    out = Path(output).expanduser()
    out.parent.mkdir(parents=True, exist_ok=True)

    capture = cv2.VideoCapture(str(src))
    if not capture.isOpened():
        raise PoseReferenceError(f"Cannot open source video: {src}")
    fps = capture.get(cv2.CAP_PROP_FPS) or 30.0
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    writer = cv2.VideoWriter(
        str(out), cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height),
    )
    if not writer.isOpened():
        capture.release()
        raise PoseReferenceError(f"Cannot create output video: {out}")

    options = vision.PoseLandmarkerOptions(
        base_options=python.BaseOptions(model_asset_path=str(model_path)),
        running_mode=vision.RunningMode.VIDEO,
        min_pose_detection_confidence=min_confidence,
        min_pose_presence_confidence=min_confidence,
        min_tracking_confidence=min_confidence,
        num_poses=1,
    )
    previous = None
    detected = 0
    frame_number = 0
    try:
        with vision.PoseLandmarker.create_from_options(options) as landmarker:
            while True:
                ok, frame = capture.read()
                if not ok:
                    break
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
                timestamp_ms = round(frame_number * 1000.0 / fps)
                result = landmarker.detect_for_video(image, timestamp_ms)
                if result.pose_landmarks:
                    previous = _smooth(result.pose_landmarks[0], previous, smoothing)
                    detected += 1
                if previous:
                    canvas = _render(cv2, np, previous, width, height, frame_number, label=label)
                else:
                    canvas = np.full((height, width, 3), _BG, dtype=np.uint8)
                writer.write(canvas)
                frame_number += 1
    finally:
        capture.release()
        writer.release()

    if not frame_number or (detected / frame_number) < min_coverage:
        raise PoseReferenceError(
            f"Pose detection coverage too low: {detected}/{frame_number} "
            f"(< {min_coverage:.0%}); source may lack a clear full-body subject."
        )
    return PoseReferenceResult(
        output=out, frames=frame_number, detected=detected,
        fps=fps, width=width, height=height,
    )
