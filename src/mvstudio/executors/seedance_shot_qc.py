"""Credential-free technical gate for one generated Seedance shot."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path


_FIELDS = frozenset({
    "project_id", "shot_id", "video_path", "video_sha256",
    "duration_seconds", "width", "height",
})


def validate_input(value):
    if not isinstance(value, dict) or set(value) != _FIELDS:
        raise ValueError("seedance shot QC input fields are invalid")
    for key in ("project_id", "shot_id"):
        if not isinstance(value[key], str) or not value[key]:
            raise ValueError(key + " is required")
    path = Path(value["video_path"]) if isinstance(value["video_path"], str) else Path()
    if (
        path.is_absolute()
        or "\\" in str(value["video_path"])
        or path.parts[:1] != ("generated",)
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        raise ValueError("video_path must be under generated")
    digest = value["video_sha256"]
    if (
        not isinstance(digest, str)
        or len(digest) != 71
        or not digest.startswith("sha256:")
        or any(character not in "0123456789abcdef" for character in digest[7:])
    ):
        raise ValueError("video_sha256 is invalid")
    duration = value["duration_seconds"]
    if isinstance(duration, bool) or not isinstance(duration, int) or not 4 <= duration <= 15:
        raise ValueError("duration_seconds is invalid")
    if value["width"] != 720 or value["height"] != 1280:
        raise ValueError("first M4 slice requires 720x1280")
    return dict(value)


def _digest(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _probe(path):
    completed = subprocess.run(
        [
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries", "stream=codec_name,width,height:format=duration",
            "-of", "json", str(path),
        ],
        check=False,
        capture_output=True,
        timeout=30,
    )
    if completed.returncode != 0 or len(completed.stdout) > 64 * 1024:
        raise ValueError("generated shot cannot be probed")
    try:
        payload = json.loads(completed.stdout)
        stream = payload["streams"][0]
        duration = float(payload["format"]["duration"])
    except (KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise ValueError("generated shot probe output is invalid") from exc
    return stream, duration


def run_seedance_shot_qc(value, staging, cancelled, send):
    value = validate_input(value)
    root = Path(staging).resolve()
    video = root / value["video_path"]
    if video.is_symlink() or not video.is_file():
        raise ValueError("generated shot is missing or unsafe")
    try:
        video.resolve(strict=True).relative_to(root)
    except (FileNotFoundError, ValueError) as exc:
        raise ValueError("generated shot escapes staging") from exc
    if cancelled.is_set():
        send({"kind": "cancelled"})
        return
    send({"kind": "progress", "step": 1, "steps": 2})
    if _digest(video) != value["video_sha256"]:
        raise ValueError("generated shot hash mismatch")
    stream, actual_duration = _probe(video)
    if stream.get("codec_name") != "h264":
        raise ValueError("generated shot codec must be H.264")
    if stream.get("width") != value["width"] or stream.get("height") != value["height"]:
        raise ValueError("generated shot dimensions differ from contract")
    if abs(actual_duration - value["duration_seconds"]) > 1.0:
        raise ValueError("generated shot duration differs from contract")
    report = {
        "version": 1,
        "project_id": value["project_id"],
        "shot_id": value["shot_id"],
        "video_path": value["video_path"],
        "video_sha256": value["video_sha256"],
        "codec": "h264",
        "width": stream["width"],
        "height": stream["height"],
        "duration_seconds": actual_duration,
        "status": "pass_gate_checked",
        "diagnosis_required": True,
        "user_approval_required": True,
    }
    output = root / "generated" / "shot_qc.json"
    output.write_text(json.dumps(report, ensure_ascii=True, sort_keys=True, separators=(",", ":")))
    send({"kind": "progress", "step": 2, "steps": 2})
    send({"kind": "succeeded"})
