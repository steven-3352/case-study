"""Validated contract binding one approved storyboard shot to its first frame."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import PurePosixPath
from types import MappingProxyType
from typing import Mapping

from mv_platform.domain.hashing import canonical_hash, freeze_json


_HASH = re.compile(r"^sha256:[0-9a-f]{64}$")
_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")
_FIELDS = frozenset({
    "version", "status", "project_id", "shot_id", "model", "prompt",
    "duration_seconds", "aspect_ratio", "resolution", "first_frame",
    "approved_by", "approved_at",
})
_FRAME_FIELDS = frozenset({"path", "sha256"})


class ApprovedShotError(ValueError):
    pass


def _text(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ApprovedShotError(label + " is required")
    return value.strip()


def _approved_at(value):
    value = _text(value, "approved_at")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ApprovedShotError("approved_at must be ISO-8601") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ApprovedShotError("approved_at must include a timezone")
    return value


def _frame_path(value):
    value = _text(value, "first_frame.path")
    path = PurePosixPath(value)
    if (
        path.is_absolute()
        or "\\" in value
        or any(part in {"", ".", ".."} for part in path.parts)
        or len(path.parts) < 4
        or path.parts[:3] != ("assets", "source", "keyframes")
    ):
        raise ApprovedShotError("first frame must be under assets/source/keyframes")
    return value


@dataclass(frozen=True)
class ApprovedShot:
    version: int
    status: str
    project_id: str
    shot_id: str
    model: str
    prompt: str
    duration_seconds: int
    aspect_ratio: str
    resolution: str
    first_frame_path: str
    first_frame_sha256: str
    approved_by: str
    approved_at: str
    contract_sha256: str
    source: Mapping


def parse_approved_shot(value, expected_project_id=None):
    if not isinstance(value, Mapping) or set(value) != _FIELDS:
        raise ApprovedShotError("approved shot fields are invalid")
    if value.get("version") != 1 or value.get("status") != "approved":
        raise ApprovedShotError("shot must be explicitly approved using contract version 1")
    project_id = _text(value.get("project_id"), "project_id")
    if expected_project_id is not None and project_id != expected_project_id:
        raise ApprovedShotError("approved shot project identity mismatch")
    shot_id = _text(value.get("shot_id"), "shot_id")
    if not _IDENTIFIER.fullmatch(shot_id):
        raise ApprovedShotError("shot_id is invalid")
    duration = value.get("duration_seconds")
    if isinstance(duration, bool) or not isinstance(duration, int) or not 4 <= duration <= 15:
        raise ApprovedShotError("duration_seconds must be between 4 and 15")
    if value.get("aspect_ratio") != "9:16" or value.get("resolution") != "720p":
        raise ApprovedShotError("first M4 slice requires 9:16 at 720p")
    frame = value.get("first_frame")
    if not isinstance(frame, Mapping) or set(frame) != _FRAME_FIELDS:
        raise ApprovedShotError("first_frame fields are invalid")
    frame_hash = frame.get("sha256")
    if not isinstance(frame_hash, str) or not _HASH.fullmatch(frame_hash):
        raise ApprovedShotError("first_frame.sha256 is invalid")
    try:
        frozen = freeze_json(value)
        digest = canonical_hash(frozen)
    except Exception as exc:
        raise ApprovedShotError("approved shot must be JSON-compatible") from exc
    return ApprovedShot(
        version=1,
        status="approved",
        project_id=project_id,
        shot_id=shot_id,
        model=_text(value.get("model"), "model"),
        prompt=_text(value.get("prompt"), "prompt"),
        duration_seconds=duration,
        aspect_ratio="9:16",
        resolution="720p",
        first_frame_path=_frame_path(frame.get("path")),
        first_frame_sha256=frame_hash,
        approved_by=_text(value.get("approved_by"), "approved_by"),
        approved_at=_approved_at(value.get("approved_at")),
        contract_sha256=digest,
        source=MappingProxyType(dict(frozen)),
    )
