from datetime import datetime, timezone

import pytest

from mv_platform.domain import (
    Artifact,
    BusinessStage,
    DomainValidationError,
    Event,
    JobSpec,
    JobStatus,
    RuntimeState,
)


NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)
H = "sha256:" + "a" * 64


def test_boolean_is_not_a_valid_integer_counter():
    with pytest.raises(DomainValidationError):
        Event("job", True, "created", NOW, {})
    with pytest.raises(DomainValidationError):
        JobStatus("job", RuntimeState.QUEUED, BusinessStage.INTAKE_PENDING, True, NOW)


def test_invalid_sequences_fail_with_domain_error():
    kwargs = dict(
        job_id="job",
        project_id="project",
        operation="render",
        input_refs=None,
        input_digest=H,
        pipeline_version="1",
        contract_version="1",
        model_policy_ref="policy",
        privacy_consent_ref="consent",
        requested_outputs=("out/final.mp4",),
        idempotency_key="key",
    )
    with pytest.raises(DomainValidationError):
        JobSpec(**kwargs)
    with pytest.raises(DomainValidationError):
        Artifact("a", "p", "j", "1", "out/a", None, H, NOW, "worker", "staged")


def test_event_payload_must_be_a_mapping():
    with pytest.raises(DomainValidationError):
        Event("job", 1, "created", NOW, ["not", "a", "mapping"])
