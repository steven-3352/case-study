"""Contract tests for the shared pose-reference library.

Kept dependency-light: the module must import cleanly even when cv2/mediapipe
are absent, and model resolution / friendly errors must not need them. An
end-to-end render (which needs the CV stack + model + a video) is exercised
separately and skipped when deps are missing.
"""
from __future__ import annotations

import importlib
from pathlib import Path

import pytest

from mvstudio.media import (
    PoseReferenceError,
    PoseReferenceResult,
    generate_pose_reference,
    resolve_model_path,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_MODEL = REPO_ROOT / "assets" / "models" / "pose_landmarker_lite.task"


def _has_cv() -> bool:
    return all(importlib.util.find_spec(m) for m in ("cv2", "mediapipe"))


def test_module_imports_without_cv_stack() -> None:
    # Importing the package must never require the heavy CV deps.
    mod = importlib.import_module("mvstudio.media.pose_reference")
    assert callable(mod.generate_pose_reference)


def test_resolve_model_prefers_explicit_arg(tmp_path: Path) -> None:
    fake = tmp_path / "m.task"
    fake.write_bytes(b"x")
    assert resolve_model_path(fake) == fake


def test_resolve_model_reads_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fake = tmp_path / "env.task"
    fake.write_bytes(b"x")
    monkeypatch.setenv("POSE_LANDMARKER_MODEL", str(fake))
    assert resolve_model_path() == fake


def test_resolve_model_missing_raises(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("POSE_LANDMARKER_MODEL", raising=False)
    with pytest.raises(PoseReferenceError):
        resolve_model_path(tmp_path / "nope.task")


def test_default_model_asset_shipped() -> None:
    # The canonical shared model lives under assets/models so both agents reach it.
    assert DEFAULT_MODEL.is_file(), f"missing shared model at {DEFAULT_MODEL}"


def test_missing_source_raises(tmp_path: Path) -> None:
    with pytest.raises(PoseReferenceError):
        generate_pose_reference(tmp_path / "nope.mp4", tmp_path / "out.mp4",
                                model=DEFAULT_MODEL)


def test_result_coverage() -> None:
    r = PoseReferenceResult(output=Path("x.mp4"), frames=100, detected=80,
                            fps=30.0, width=10, height=10)
    assert r.coverage == pytest.approx(0.8)
    empty = PoseReferenceResult(output=Path("x.mp4"), frames=0, detected=0,
                                fps=30.0, width=10, height=10)
    assert empty.coverage == 0.0


@pytest.mark.skipif(not _has_cv(), reason="opencv-python/mediapipe not installed")
def test_end_to_end_render(tmp_path: Path) -> None:
    import cv2
    import numpy as np

    # Synthesize a tiny clip with a moving high-contrast blob. Pose detection
    # will likely be sparse on a non-human subject, so we only assert that low
    # coverage raises the structured error (not a crash).
    src = tmp_path / "src.mp4"
    writer = cv2.VideoWriter(str(src), cv2.VideoWriter_fourcc(*"mp4v"), 10.0, (160, 160))
    for i in range(20):
        frame = np.zeros((160, 160, 3), dtype=np.uint8)
        cv2.circle(frame, (20 + i * 6, 80), 15, (255, 255, 255), -1)
        writer.write(frame)
    writer.release()

    if not DEFAULT_MODEL.is_file():
        pytest.skip("model asset missing")
    with pytest.raises(PoseReferenceError):
        generate_pose_reference(src, tmp_path / "out.mp4", model=DEFAULT_MODEL,
                                min_coverage=0.65)
