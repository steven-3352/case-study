from datetime import datetime, timezone
from pathlib import Path

import pytest

from mv_platform.domain import JobSpec, JobStatus, Project
from mv_platform.domain.states import BusinessStage, RuntimeState
from mv_platform.infrastructure import Database, Repository
from mv_platform.supervisor import (
    InvalidExecutorInput,
    JobSupervisor,
    SupervisorError,
)


H = "sha256:" + "a" * 64


def make_env(tmp_path, job_ids, max_active=4):
    database = Database(tmp_path / "app.sqlite3")
    database.migrate()
    repository = Repository(database)
    now = datetime.now(timezone.utc)
    repository.add_project(Project("project", "film", "pipeline/voice_room/film", H, now))
    for job_id in job_ids:
        repository.add_job(JobSpec(job_id, "project", "analyze", (), H, "v1", "v1", "policy", "consent", (), "key-" + job_id))
        repository.set_status(JobStatus(job_id, RuntimeState.QUEUED, BusinessStage.INTAKE_PENDING, 1, now))
    return repository, JobSupervisor(database, tmp_path / "jobs", max_active)


@pytest.mark.parametrize("job_id", ["../escape", "a/b", "a\\b", ".", "/absolute"])
def test_job_identifier_cannot_escape_staging(tmp_path, job_id):
    repository, supervisor = make_env(tmp_path, [job_id])
    with pytest.raises(SupervisorError):
        supervisor.submit(job_id)
    assert not (tmp_path / "escape").exists()
    assert repository.get_status(job_id).runtime_state is RuntimeState.QUEUED


def test_existing_staging_symlink_is_rejected(tmp_path):
    repository, supervisor = make_env(tmp_path, ["job"])
    outside = tmp_path / "outside"
    outside.mkdir()
    (tmp_path / "jobs" / "job").symlink_to(outside, target_is_directory=True)
    with pytest.raises(SupervisorError):
        supervisor.submit("job")
    assert repository.get_status("job").runtime_state is RuntimeState.QUEUED


def test_persistence_failure_after_spawn_reaps_child(tmp_path, monkeypatch):
    repository, supervisor = make_env(tmp_path, ["job"])

    def fail(_status):
        raise RuntimeError("database unavailable")

    monkeypatch.setattr(supervisor.repository, "set_status", fail)
    with pytest.raises(RuntimeError):
        supervisor.submit("job", executor_input={"steps": 100, "delay_seconds": 0.2})
    assert not supervisor._workers
    assert repository.get_status("job").runtime_state is RuntimeState.QUEUED


@pytest.mark.parametrize(
    "value",
    [
        {"steps": True},
        {"steps": 0},
        {"steps": 101},
        {"delay_seconds": -1},
        {"delay_seconds": float("nan")},
        {"fail_at": True},
        {"artifact_text": "x" * 10001},
        {"unknown": 1},
        ["not-a-mapping"],
    ],
)
def test_invalid_fake_input_fails_before_spawn(tmp_path, value):
    repository, supervisor = make_env(tmp_path, ["job"])
    with pytest.raises(InvalidExecutorInput):
        supervisor.submit("job", executor_input=value)
    assert repository.get_status("job").runtime_state is RuntimeState.QUEUED
    assert supervisor.snapshot("job").pid is None


def test_timeout_does_not_false_succeed_and_forced_cancel_reaps(tmp_path):
    repository, supervisor = make_env(tmp_path, ["job"])
    supervisor.submit("job", executor_input={"steps": 100, "delay_seconds": 0.2})
    with pytest.raises(TimeoutError):
        supervisor.wait("job", 0.01)
    assert repository.get_status("job").runtime_state is RuntimeState.RUNNING
    snapshot = supervisor.cancel("job", 0)
    assert snapshot.runtime_state is RuntimeState.CANCELLED
    assert not snapshot.alive
    assert not supervisor._workers


def test_fast_exit_queue_race_never_turns_success_into_failure(tmp_path):
    job_ids = ["job-%02d" % number for number in range(12)]
    repository, supervisor = make_env(tmp_path, job_ids, max_active=1)
    try:
        for job_id in job_ids:
            supervisor.submit(job_id, executor_input={"steps": 1})
            snapshot = supervisor.wait(job_id, 3)
            assert snapshot.runtime_state is RuntimeState.SUCCEEDED
            assert not snapshot.alive
            events = repository.list_events(job_id)
            assert events[-1].event_type == "job.succeeded"
    finally:
        supervisor.shutdown()
    assert not supervisor._workers


def test_two_jobs_are_isolated_and_counters_are_read_only(tmp_path):
    repository, supervisor = make_env(tmp_path, ["left", "right"], max_active=2)
    supervisor.submit("left", executor_input={"steps": 2, "artifact_text": "L"})
    supervisor.submit("right", executor_input={"steps": 2, "artifact_text": "R"})
    assert supervisor.wait("left", 3).runtime_state is RuntimeState.SUCCEEDED
    assert supervisor.wait("right", 3).runtime_state is RuntimeState.SUCCEEDED
    assert (tmp_path / "jobs" / "left" / "result.txt").read_text() == "L"
    assert (tmp_path / "jobs" / "right" / "result.txt").read_text() == "R"
    assert {event.job_id for event in repository.list_events("left")} == {"left"}
    assert {event.job_id for event in repository.list_events("right")} == {"right"}
    assert supervisor.model_call_count == 0
    assert supervisor.token_count == 0
    with pytest.raises(AttributeError):
        supervisor.token_count = 1


def test_malformed_message_sets_one_failed_terminal_state(tmp_path):
    repository, supervisor = make_env(tmp_path, ["job"])
    supervisor.submit("job", executor_input={"steps": 100, "delay_seconds": 0.01})
    supervisor._workers["job"]["messages"].put({"kind": "not-allowed"})
    for _ in range(100):
        supervisor.tick()
        if repository.get_status("job").runtime_state is RuntimeState.FAILED:
            break
    assert repository.get_status("job").runtime_state is RuntimeState.FAILED
    supervisor.cancel("job", 0)
    assert repository.get_status("job").runtime_state is RuntimeState.FAILED
    terminal_events = [event for event in repository.list_events("job") if event.event_type in {"job.failed", "job.succeeded", "job.cancelled"}]
    assert len(terminal_events) == 1
