from enum import Enum


class RuntimeState(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


class BusinessStage(str, Enum):
    INTAKE_PENDING = "intake_pending"
    INTAKE_VALIDATED = "intake_validated"
    MAPS_GENERATED = "maps_generated"
    STORY_FRAMEWORK_PENDING_USER = "story_framework_pending_user"
    STORY_FRAMEWORK_APPROVED = "story_framework_approved"
    VISUAL_SCORE_PENDING_USER = "visual_score_pending_user"
    VISUAL_SCORE_APPROVED = "visual_score_approved"
    KEYFRAMES_PENDING_USER = "keyframes_pending_user"
    KEYFRAMES_APPROVED = "keyframes_approved"
    GENERATION_PENDING = "generation_pending"
    GENERATION_PARTIAL = "generation_partial"
    GENERATION_APPROVED = "generation_approved"
    COMPOSITING_PENDING = "compositing_pending"
    QC_PASSED = "qc_passed"
    EXPORTED = "exported"
    SUPERSEDED = "superseded"
