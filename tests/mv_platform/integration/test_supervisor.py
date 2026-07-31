from datetime import datetime, timezone

import pytest

from mv_platform.domain import JobSpec, JobStatus, Project
from mv_platform.domain.states import BusinessStage, RuntimeState
from mv_platform.infrastructure.database import Database
from mv_platform.infrastructure.repositories import Repository
from mv_platform.supervisor import JobAlreadyActive, JobSupervisor, UnknownExecutor


def make_supervisor(tmp_path, count=2):
    database = Database(tmp_path / "jobs.sqlite3")
    database.migrate()
    repository = Repository(database)
    now = datetime.now(timezone.utc)
    repository.add_project(Project("p1", "demo", "projects/demo", "sha256:" + "a" * 64, now))
    for number in range(1, 4):
        job_id = "job-" + str(number)
        repository.add_job(JobSpec(job_id, "p1", "analyze", (), "sha256:" + "b" * 64, "v1", "v1", "policy", "consent", (), job_id))
        repository.set_status(JobStatus(job_id, RuntimeState.QUEUED, BusinessStage.INTAKE_PENDING, 1, now))
    return database, repository, JobSupervisor(database, tmp_path / "staging", count)


def test_spawn_success_events_and_zero_counters(tmp_path):
    database, repository, supervisor = make_supervisor(tmp_path)
    assert supervisor._context.get_start_method() == "spawn"
    supervisor.submit("job-1", executor_input={"steps": 3, "artifact_text": "done"})
    result = supervisor.wait("job-1", 5)
    assert result.runtime_state is RuntimeState.SUCCEEDED
    assert (tmp_path / "staging" / "job-1" / "result.txt").read_text() == "done"
    events = repository.list_events("job-1")
    assert [event.seq for event in events] == list(range(1, len(events) + 1))
    assert any(event.event_type == "job.progress" for event in events)
    assert supervisor.model_call_count == supervisor.token_count == 0
    supervisor.shutdown()


def test_failure_cancel_limits_and_rejection(tmp_path):
    database, repository, supervisor = make_supervisor(tmp_path, 1)
    supervisor.submit("job-1", executor_input={"steps": 2, "fail_at": 1})
    with pytest.raises(JobAlreadyActive):
        supervisor.submit("job-1")
    with pytest.raises(Exception):
        supervisor.submit("job-2")
    assert supervisor.wait("job-1", 5).runtime_state is RuntimeState.FAILED
    supervisor.submit("job-2", executor_input={"steps": 100, "delay_seconds": 0.2})
    assert supervisor.cancel("job-2", 0).runtime_state is RuntimeState.CANCELLED
    assert not supervisor.snapshot("job-2").alive
    with pytest.raises(UnknownExecutor):
        supervisor.submit("job-3", executor="other")
    supervisor.shutdown()


def test_recovery_requeues_orphan_and_preserves_terminal(tmp_path):
    database, repository, supervisor = make_supervisor(tmp_path)
    supervisor.submit("job-1", executor_input={"steps": 1})
    supervisor.shutdown()
    repository.set_status(repository.get_status("job-2").transition(RuntimeState.RUNNING, datetime.now(timezone.utc)))
    supervisor.recover()
    assert repository.get_status("job-2").runtime_state is RuntimeState.QUEUED
    assert repository.list_events("job-2")[-1].event_type == "job.recovered"
    assert repository.get_status("job-1").runtime_state is RuntimeState.CANCELLED
