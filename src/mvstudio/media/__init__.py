"""Shared local media utilities reusable across agents (mv-agent / ad-agent).

Providers under ``mvstudio.providers`` wrap external APIs; this package holds
dependency-light, local media transforms (pose extraction, …) that any agent
may call without touching engine or provider code.
"""

from .pose_reference import (
    PoseReferenceError,
    PoseReferenceResult,
    generate_pose_reference,
    resolve_model_path,
)

__all__ = [
    "PoseReferenceError",
    "PoseReferenceResult",
    "generate_pose_reference",
    "resolve_model_path",
]
