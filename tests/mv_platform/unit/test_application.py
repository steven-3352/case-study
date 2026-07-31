import json
import sqlite3
from datetime import datetime, timezone

import pytest

from mv_platform.application import (
    ApplicationBlocked,
    ApplicationConflict,
    ApplicationError,
    ApplicationNotFound,
    ApplicationService,
)
from mv_platform.config import Settings
from mv_platform.domain import JobStatus
from mv_platform.domain.states import RuntimeState
from mv_platform.infrastructure import Database


H1 = "sha256:" + "1" * 64


def make_service(tmp_path, supervisor=None, initialize=True):
    settings = Settings()
    database = Database(tmp_path / settings.db_path)
    service = ApplicationService(settings, database, supervisor=supervisor, workspace_root=tmp_path)
    if initialize:
        service.initialize()
    return service, database


def test_construction_has_no_side_effect_and_initialize_is_idempotent(tmp_path):
    service, database = make_service(tmp_path, initialize=False)
    assert not database.path.exists()
    assert not (tmp_path / "projects").exists()
    service.initialize()
    service.initialize()
    assert database.path.exists()
    assert (tmp_path / "projects").is_dir()
    assert (tmp_path / ".mvstudio" / "jobs").is_dir()


def test_initialize_rejects_symlink_escape_before_database_write(tmp_path):
    outside = tmp_path.parent / (tmp_path.name + "-outside")
    outside.mkdir()
    (tmp_path / "projects").symlink_to(outside, target_is_directory=True)
    settings = Settings(project_root="projects")
    database = Database(tmp_path / settings.db_path)
    service = ApplicationService(settings, database, workspace_root=tmp_path)
    with pytest.raises(ApplicationBlocked):
        service.initialize()
    assert not database.path.exists()


def test_project_is_canonical_atomic_and_slug_participates_in_identity(tmp_path):
    service, _ = make_service(tmp_path)
    first = service.create_project("first", {"b": [2], "a": 1})
    same = service.create_project("first", {"a": 1, "b": [2]})
    second = service.create_project("second", {"a": 1, "b": [2]})
    assert same.project_id == first.project_id
    assert second.project_id != first.project_id
    brief_path = tmp_path / "projects" / "first" / "brief.json"
    assert brief_path.read_bytes() == b'{"a":1,"b":[2]}'
    assert not list(brief_path.parent.glob(".brief-*"))
    expected_directories = {
        "inputs/audio", "inputs/lyrics", "inputs/characters", "creative",
        "assets/source", "assets/generated", "outputs",
        ".mvstudio/jobs", ".mvstudio/work", ".mvstudio/logs",
    }
    assert expected_directories <= {
        path.relative_to(brief_path.parent).as_posix() for path in brief_path.parent.rglob("*") if path.is_dir()
    }
    with pytest.raises(TypeError):
        first.brief["x"] = 1


def test_project_idempotency_detects_disk_tampering_and_conflicts(tmp_path):
    service, _ = make_service(tmp_path)
    created = service.create_project("film", {"a": 1})
    brief_path = tmp_path / "projects" / "film" / "brief.json"
    brief_path.write_text('{"a":2}', encoding="utf-8")
    with pytest.raises(ApplicationConflict):
        service.create_project("film", {"a": 1})
    with pytest.raises(ApplicationConflict):
        service.create_project("film", {"a": 2}, project_id=created.project_id)


def test_project_rejects_non_json_and_project_symlink(tmp_path):
    service, _ = make_service(tmp_path)
    with pytest.raises(ApplicationConflict):
        service.create_project("bad", {"x": object()})
    outside = tmp_path / "outside"
    outside.mkdir()
    (tmp_path / "projects" / "linked").symlink_to(outside, target_is_directory=True)
    with pytest.raises(ApplicationBlocked):
        service.create_project("linked", {"x": 1})


def test_job_submission_is_deterministic_and_idempotency_conflicts(tmp_path):
    service, _ = make_service(tmp_path)
    project = service.create_project("film", {"x": 1})
    first = service.submit_job(project.project_id, "analyze", H1, input_refs=("assets/a.png",))
    same = service.submit_job(project.project_id, "analyze", H1, input_refs=("assets/a.png",))
    assert same.job_id == first.job_id
    assert same.canonical_job_digest == first.canonical_job_digest
    with pytest.raises(ApplicationConflict):
        service.submit_job(project.project_id, "render", H1, idempotency_key=first.job_spec.idempotency_key)
    for kwargs in ({"input_refs": "assets/a.png"}, {"input_digest": "bad"}, {"operation": "bad"}):
        request = {"project_id": project.project_id, "operation": "analyze", "input_digest": H1}
        request.update(kwargs)
        with pytest.raises(ApplicationConflict):
            service.submit_job(**request)


def test_job_and_status_insert_roll_back_together(tmp_path):
    service, database = make_service(tmp_path)
    project = service.create_project("film", {"x": 1})
    with database.connect() as connection:
        connection.execute("CREATE TRIGGER reject_status BEFORE INSERT ON job_status BEGIN SELECT RAISE(ABORT, 'no status'); END")
    with pytest.raises(ApplicationConflict):
        service.submit_job(project.project_id, "analyze", H1)
    with database.connect() as connection:
        assert connection.execute("SELECT COUNT(*) FROM jobs").fetchone()[0] == 0


class RecordingSupervisor:
    def __init__(self):
        self.service = None
        self.started = []
        self.cancelled = []
        self.recovered = False
        self.stopped = False

    def submit(self, job_id, executor, executor_input):
        inspection = self.service.inspect_job(job_id)
        assert inspection.status.runtime_state is RuntimeState.QUEUED
        self.started.append((job_id, executor, executor_input))
        return inspection

    def cancel(self, job_id, grace):
        self.cancelled.append((job_id, grace))
        status = self.service.repository.get_status(job_id)
        self.service.repository.set_status(status.transition(RuntimeState.CANCELLED, datetime.now(timezone.utc)))

    def recover(self): self.recovered = True
    def shutdown(self): self.stopped = True


def test_auto_start_occurs_after_atomic_persistence_and_delegates(tmp_path):
    supervisor = RecordingSupervisor()
    service, _ = make_service(tmp_path, supervisor)
    supervisor.service = service
    project = service.create_project("film", {"x": 1})
    result = service.submit_job(project.project_id, "analyze", H1, auto_start=True, executor_input={"steps": 1})
    assert result.job_id == supervisor.started[0][0]
    service.recover()
    service.shutdown()
    assert supervisor.recovered and supervisor.stopped


def test_inspect_events_artifacts_cursor_and_missing(tmp_path):
    service, _ = make_service(tmp_path)
    project = service.create_project("film", {"x": 1})
    job = service.submit_job(project.project_id, "analyze", H1)
    inspection = service.inspect_job(job.job_id)
    assert inspection.events == () and inspection.artifacts == ()
    assert inspection.job_digest == job.canonical_job_digest
    for value in (True, -1, 1.5, "1"):
        with pytest.raises(ApplicationConflict):
            service.list_events(job.job_id, value)
    with pytest.raises(ApplicationNotFound):
        service.inspect_job("missing")


def test_no_supervisor_start_recover_shutdown_are_blocked(tmp_path):
    service, _ = make_service(tmp_path)
    for call in (lambda: service.start_job("missing"), service.recover, service.shutdown):
        with pytest.raises(ApplicationBlocked):
            call()


def test_queued_cancel_status_and_event_are_atomic(tmp_path):
    service, database = make_service(tmp_path)
    project = service.create_project("film", {"x": 1})
    job = service.submit_job(project.project_id, "analyze", H1)
    with database.connect() as connection:
        connection.execute("CREATE TRIGGER reject_event BEFORE INSERT ON events BEGIN SELECT RAISE(ABORT, 'no event'); END")
    with pytest.raises(ApplicationError):
        service.cancel_job(job.job_id)
    assert service.inspect_job(job.job_id).status.runtime_state is RuntimeState.QUEUED
    assert service.list_events(job.job_id) == ()


def test_terminal_cancel_is_idempotent_and_does_not_overwrite_success(tmp_path):
    service, _ = make_service(tmp_path)
    project = service.create_project("film", {"x": 1})
    cancelled = service.submit_job(project.project_id, "analyze", H1)
    first = service.cancel_job(cancelled.job_id)
    second = service.cancel_job(cancelled.job_id)
    assert first.status.runtime_state is second.status.runtime_state is RuntimeState.CANCELLED
    assert len(service.list_events(cancelled.job_id)) == 1

    success = service.submit_job(project.project_id, "render", H1)
    status = service.repository.get_status(success.job_id)
    service.repository.set_status(status.transition(RuntimeState.RUNNING, datetime.now(timezone.utc)).transition(RuntimeState.SUCCEEDED, datetime.now(timezone.utc)))
    assert service.cancel_job(success.job_id).status.runtime_state is RuntimeState.SUCCEEDED
