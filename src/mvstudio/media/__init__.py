"""Shared local media utilities reusable across agents (mv-agent / ad-agent).

Providers under ``mvstudio.providers`` wrap external APIs; this package holds
dependency-light, local media transforms (pose extraction, …) that any agent
may call without touching engine or provider code.
"""

from .helpers import (
    err,
    ffmpeg_bin,
    ffprobe_bin,
    max_shots,
    provider_config,
    sha256_bytes,
    sha256_file,
)
from .pose_reference import (
    PoseReferenceError,
    PoseReferenceResult,
    generate_pose_reference,
    resolve_model_path,
)

__all__ = [
    "err",
    "ffmpeg_bin",
    "ffprobe_bin",
    "max_shots",
    "provider_config",
    "sha256_bytes",
    "sha256_file",
    "PoseReferenceError",
    "PoseReferenceResult",
    "generate_pose_reference",
    "resolve_model_path",
]
