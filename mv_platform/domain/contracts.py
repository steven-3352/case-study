import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Mapping, Optional, Tuple

from .errors import DomainValidationError, InvalidStateTransition
from .hashing import canonical_hash, freeze_json
from .states import BusinessStage, RuntimeState

_HASH = re.compile(r"^sha256:[0-9a-f]{64}$")
_SLUG = re.compile(r"^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$")
_OPS = {"analyze", "compile", "animatic", "generate", "render", "qc", "export",
        "generate_background", "generate_keyframe"}


def _nonempty(value: str, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise DomainValidationError(label + " must be non-empty")
    return value


def _aware(value: datetime) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise DomainValidationError("datetime must be timezone-aware")
    return value


def _hash(value: str) -> str:
    _nonempty(value, "hash")
    if not _HASH.fullmatch(value):
        raise DomainValidationError("invalid hash")
    return value


def _path(value: str) -> str:
    _nonempty(value, "path")
    if value.startswith("/") or "\\" in value:
        raise DomainValidationError("path must be project-relative POSIX")
    parts = value.split("/")
    if any(part in ("", ".", "..") for part in parts):
        raise DomainValidationError("invalid project-relative path")
    return value


def _refs(values, label: str) -> Tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise DomainValidationError(label + " must be a sequence")
    try:
        return tuple(_path(item) for item in values)
    except TypeError as exc:
        raise DomainValidationError(label + " must be a sequence") from exc


@dataclass(frozen=True)
class Project:
    project_id: str
    slug: str
    root: str
    brief_sha256: str
    created_at: datetime

    def __post_init__(self):
        _nonempty(self.project_id, "project_id")
        if not isinstance(self.slug, str) or not _SLUG.fullmatch(self.slug):
            raise DomainValidationError("invalid slug")
        if self.root != "projects/" + self.slug:
            raise DomainValidationError("root must match project slug")
        _hash(self.brief_sha256)
        _aware(self.created_at)


@dataclass(frozen=True)
class JobSpec:
    job_id: str
    project_id: str
    operation: str
    input_refs: Tuple[str, ...]
    input_digest: str
    pipeline_version: str
    contract_version: str
    model_policy_ref: str
    privacy_consent_ref: str
    requested_outputs: Tuple[str, ...]
    idempotency_key: str

    def __post_init__(self):
        for value, label in ((self.job_id, "job_id"), (self.project_id, "project_id"),
                             (self.pipeline_version, "pipeline_version"), (self.contract_version, "contract_version"),
                             (self.model_policy_ref, "model_policy_ref"), (self.privacy_consent_ref, "privacy_consent_ref"),
                             (self.idempotency_key, "idempotency_key")):
            _nonempty(value, label)
        if self.operation not in _OPS:
            raise DomainValidationError("invalid operation")
        object.__setattr__(self, "input_refs", _refs(self.input_refs, "input_refs"))
        object.__setattr__(self, "requested_outputs", _refs(self.requested_outputs, "requested_outputs"))
        _hash(self.input_digest)

    def canonical_digest(self) -> str:
        return canonical_hash(self)


_TRANSITIONS = {
    RuntimeState.QUEUED: {RuntimeState.RUNNING, RuntimeState.BLOCKED, RuntimeState.CANCELLED, RuntimeState.FAILED},
    RuntimeState.BLOCKED: {RuntimeState.QUEUED, RuntimeState.CANCELLED, RuntimeState.FAILED},
    RuntimeState.RUNNING: {RuntimeState.SUCCEEDED, RuntimeState.FAILED, RuntimeState.BLOCKED, RuntimeState.CANCELLED},
}


@dataclass(frozen=True)
class JobStatus:
    job_id: str
    runtime_state: RuntimeState
    business_stage: BusinessStage
    attempt: int
    updated_at: datetime
    error_code: Optional[str] = None

    def __post_init__(self):
        _nonempty(self.job_id, "job_id")
        if not isinstance(self.runtime_state, RuntimeState):
            raise DomainValidationError("invalid runtime state")
        if not isinstance(self.business_stage, BusinessStage):
            raise DomainValidationError("invalid business stage")
        if isinstance(self.attempt, bool) or not isinstance(self.attempt, int) or self.attempt < 1:
            raise DomainValidationError("attempt must be >= 1")
        _aware(self.updated_at)

    def transition(self, runtime_state: RuntimeState, updated_at: datetime, error_code: Optional[str] = None):
        if runtime_state not in _TRANSITIONS.get(self.runtime_state, set()):
            raise InvalidStateTransition(self.runtime_state.value + " -> " + getattr(runtime_state, "value", str(runtime_state)))
        return JobStatus(self.job_id, runtime_state, self.business_stage, self.attempt, updated_at, error_code)


@dataclass(frozen=True)
class Event:
    job_id: str
    seq: int
    event_type: str
    occurred_at: datetime
    payload: Mapping = field(default_factory=dict)

    def __post_init__(self):
        _nonempty(self.job_id, "job_id")
        if isinstance(self.seq, bool) or not isinstance(self.seq, int) or self.seq < 1:
            raise DomainValidationError("seq must be >= 1")
        _nonempty(self.event_type, "event_type")
        _aware(self.occurred_at)
        if not isinstance(self.payload, Mapping):
            raise DomainValidationError("payload must be a mapping")
        object.__setattr__(self, "payload", freeze_json(self.payload))


@dataclass(frozen=True)
class Artifact:
    artifact_id: str
    project_id: str
    job_id: str
    schema_version: str
    relative_path: str
    input_hashes: Tuple[str, ...]
    content_hash: str
    created_at: datetime
    producer: str
    status: str

    def __post_init__(self):
        for value, label in ((self.artifact_id, "artifact_id"), (self.project_id, "project_id"),
                             (self.job_id, "job_id"), (self.schema_version, "schema_version"), (self.producer, "producer")):
            _nonempty(value, label)
        _path(self.relative_path)
        try:
            hashes = tuple(_hash(value) for value in self.input_hashes)
        except TypeError as exc:
            raise DomainValidationError("input_hashes must be a sequence") from exc
        object.__setattr__(self, "input_hashes", hashes)
        _hash(self.content_hash)
        _aware(self.created_at)
        if self.status not in {"staged", "published", "superseded", "rejected"}:
            raise DomainValidationError("invalid artifact status")
