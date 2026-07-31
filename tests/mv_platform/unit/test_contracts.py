from datetime import datetime, timezone
from dataclasses import FrozenInstanceError, is_dataclass
import math

import pytest

from mv_platform.domain import (Artifact, BusinessStage, DomainValidationError, Event,
                                InvalidStateTransition, JobSpec, JobStatus, Project,
                                RuntimeState)
from mv_platform.domain.hashing import canonical_hash

NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)
H = "sha256:" + "a" * 64


def test_canonical_hash_is_order_independent_but_lists_are_ordered():
    assert canonical_hash({"a": 1, "b": 2}) == canonical_hash({"b": 2, "a": 1})
    assert canonical_hash([1, 2]) != canonical_hash([2, 1])


@pytest.mark.parametrize("value", [math.nan, math.inf, datetime(2026, 1, 1), object(), b"x"])
def test_hash_rejects_unsafe_values(value):
    with pytest.raises(DomainValidationError):
        canonical_hash(value)


def test_dataclasses_are_frozen_and_aliases_do_not_mutate_payload():
    payload = {"items": [1, {"ok": True}]}
    event = Event("job", 1, "created", NOW, payload)
    payload["items"].append(2)
    assert event.payload["items"] == (1, {"ok": True})
    with pytest.raises(TypeError):
        event.payload["new"] = 1
    with pytest.raises(FrozenInstanceError):
        event.job_id = "other"
    assert all(is_dataclass(item) for item in (Project, JobSpec, JobStatus, Event, Artifact))


def test_project_and_paths_validate():
    Project("p", "room-1", "projects/room-1", H, NOW)
    for root in ("/projects/x", "projects/../x", "projects/X"):
        with pytest.raises(DomainValidationError):
            Project("p", "room-1", root, H, NOW)


def test_jobspec_and_digest():
    kwargs = dict(job_id="j", project_id="p", operation="render", input_refs=["in/a"],
                  input_digest=H, pipeline_version="1", contract_version="1",
                  model_policy_ref="policy", privacy_consent_ref="consent",
                  requested_outputs=["out/a"], idempotency_key="idem")
    assert JobSpec(**kwargs).canonical_digest() == JobSpec(**kwargs).canonical_digest()
    for key, value in (("operation", "bad"), ("input_digest", "bad"), ("input_refs", ["../x"]),
                       ("job_id", "")):
        bad = dict(kwargs, **{key: value})
        with pytest.raises(DomainValidationError):
            JobSpec(**bad)


def test_runtime_and_business_stage_are_distinct_and_transitions_are_frozen():
    status = JobStatus("j", RuntimeState.QUEUED, BusinessStage.INTAKE_PENDING, 1, NOW)
    for target in (RuntimeState.RUNNING, RuntimeState.BLOCKED, RuntimeState.CANCELLED, RuntimeState.FAILED):
        assert status.transition(target, NOW).runtime_state is target
    with pytest.raises(InvalidStateTransition):
        status.transition(RuntimeState.SUCCEEDED, NOW)
    terminal = status.transition(RuntimeState.CANCELLED, NOW)
    with pytest.raises(InvalidStateTransition):
        terminal.transition(RuntimeState.QUEUED, NOW)


def test_event_and_artifact_validation():
    with pytest.raises(DomainValidationError):
        Event("j", 0, "created", NOW, {})
    with pytest.raises(DomainValidationError):
        Artifact("a", "p", "j", "1", "x/y", [H], H, NOW, "worker", "invalid")
    Artifact("a", "p", "j", "1", "x/y", [H], H, NOW, "worker", "published")


def test_package_imports_and_enum_values():
    assert RuntimeState.QUEUED.value == "queued"
    assert BusinessStage.EXPORTED.value == "exported"
