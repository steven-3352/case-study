"""Independent M0-M1 security and end-to-end gate coverage."""

import json
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from apps.mv_api import create_app
from apps.mv_cli import main as cli_main
from apps.runtime import SOURCE_ROOT, build_service, default_workspace_root
from mv_platform.application.service import ApplicationBlocked, ApplicationConflict
from mv_platform.config import InfrastructureError, Settings
from mv_platform.domain.states import RuntimeState
from mv_platform.supervisor import InvalidExecutorInput, UnknownExecutor
import mv_platform.supervisor as supervisor_module


HASH = "sha256:" + "e" * 64


def make_service(tmp_path, *, max_active_jobs=2):
    return build_service(tmp_path, settings=Settings(max_active_jobs=max_active_jobs))


def create_project(service, slug="demo"):
    return service.create_project(slug, {"title": "review fixture", "slug": slug})


def wait(service, job_id, timeout=8):
    return service.supervisor.wait(job_id, timeout)


def test_rejects_arbitrary_executor_and_interface_parameters(tmp_path):
    service = make_service(tmp_path)
    project = create_project(service)
    job = service.submit_job(project.project_id, "analyze", HASH)
    with pytest.raises(UnknownExecutor):
        service.start_job(job.job_id, "; touch pwned", {})
    with pytest.raises(InvalidExecutorInput):
        service.start_job(job.job_id, "fake", {"cwd": "/tmp", "env": {"X": "Y"}})

    client = TestClient(create_app(service=service))
    response = client.post(
        f"/api/v1/projects/{project.project_id}/jobs",
        json={"operation": "analyze", "input_digest": HASH, "command": "id", "cwd": "/", "env": {"X": "Y"}, "flags": ["--unsafe"]},
    )
    assert response.status_code == 422
    assert not (tmp_path / "pwned").exists()
    service.shutdown()


@pytest.mark.parametrize("value", ["../escape", "/tmp/escape", r"C:\\escape", "assets/../escape", "assets\\escape"])
def test_paths_and_unsafe_configured_roots_fail_closed(tmp_path, value):
    with pytest.raises(InfrastructureError):
        Settings(project_root=value)

    service = make_service(tmp_path)
    project = create_project(service)
    with pytest.raises(ApplicationConflict):
        service.submit_job(project.project_id, "analyze", HASH, input_refs=(value,))
    service.shutdown()


def test_symlink_escape_fails_before_initialize_or_project_write(tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    (tmp_path / "projects").symlink_to(outside, target_is_directory=True)
    with pytest.raises(ApplicationBlocked):
        build_service(tmp_path)
    assert not (tmp_path / ".mvstudio" / "app.sqlite3").exists()


def test_workspace_defaults_can_be_owned_by_the_user(tmp_path):
    assert default_workspace_root({"MV_WORKSPACE_ROOT": str(tmp_path)}) == tmp_path


def test_source_tree_cannot_be_used_as_runtime_workspace():
    database_path = SOURCE_ROOT / ".mvstudio" / "app.sqlite3"
    before = database_path.exists()
    with pytest.raises(ApplicationBlocked):
        build_service(SOURCE_ROOT)
    assert database_path.exists() is before


def test_api_and_cli_do_not_disclose_paths_or_inherited_secrets(tmp_path, capsys, monkeypatch):
    secret = "M0_M1_REVIEW_SECRET_VALUE"
    monkeypatch.setenv("M0_M1_REVIEW_SECRET", secret)

    class BrokenApiService:
        def inspect_job(self, _job_id):
            raise ApplicationBlocked("/private/review/secret.txt " + os.environ["M0_M1_REVIEW_SECRET"])

    response = TestClient(create_app(service=BrokenApiService()), raise_server_exceptions=False).get("/api/v1/jobs/job")
    assert response.status_code == 423
    assert "/private/review/secret.txt" not in response.text
    assert secret not in response.text

    class BrokenCliService:
        supervisor = None

        def inspect_job(self, _job_id):
            raise ApplicationBlocked("/private/review/secret.txt " + os.environ["M0_M1_REVIEW_SECRET"])

    assert cli_main(["job", "inspect", "job", "--json"], service=BrokenCliService()) == 2
    captured = capsys.readouterr()
    assert "/private/review/secret.txt" not in captured.err
    assert secret not in captured.err


def test_worker_environment_is_reduced_to_allowlist(monkeypatch):
    original_environment = dict(os.environ)
    observed = {}

    class Messages:
        def put(self, _message):
            pass

    class Cancelled:
        def is_set(self):
            return False

    def capture_environment(_value, _staging, _cancelled, _send):
        observed.update(os.environ)

    monkeypatch.setenv("M0_M1_REVIEW_SECRET", "must-not-reach-worker")
    monkeypatch.setattr(supervisor_module, "run_fake", capture_environment)
    try:
        supervisor_module._worker({}, ".", Cancelled(), Messages())
    finally:
        os.environ.clear()
        os.environ.update(original_environment)

    assert "M0_M1_REVIEW_SECRET" not in observed
    assert observed["PYTHONDONTWRITEBYTECODE"] == "1"
    assert set(observed) <= supervisor_module._CHILD_ENV_ALLOWLIST


def test_two_fake_jobs_are_isolated_and_events_replay_in_sequence(tmp_path):
    service = make_service(tmp_path)
    left_project = create_project(service, "left")
    right_project = create_project(service, "right")
    left = service.submit_job(left_project.project_id, "analyze", HASH, auto_start=True, executor_input={"steps": 2, "artifact_text": "left-only"})
    right = service.submit_job(right_project.project_id, "analyze", HASH, auto_start=True, executor_input={"steps": 2, "artifact_text": "right-only"})
    assert wait(service, left.job_id).runtime_state is RuntimeState.SUCCEEDED
    assert wait(service, right.job_id).runtime_state is RuntimeState.SUCCEEDED

    left_events = service.list_events(left.job_id)
    right_events = service.list_events(right.job_id)
    assert [event.seq for event in left_events] == list(range(1, len(left_events) + 1))
    assert [event.seq for event in right_events] == list(range(1, len(right_events) + 1))
    assert service.list_events(left.job_id, left_events[0].seq) == left_events[1:]
    assert {event.job_id for event in left_events} == {left.job_id}
    assert {event.job_id for event in right_events} == {right.job_id}
    left_stage = tmp_path / ".mvstudio" / "jobs" / left.job_id
    right_stage = tmp_path / ".mvstudio" / "jobs" / right.job_id
    assert (left_stage / "result.txt").read_text() == "left-only"
    assert (right_stage / "result.txt").read_text() == "right-only"
    assert right.job_id not in "\n".join(path.read_text() for path in left_stage.rglob("*") if path.is_file())
    assert left.job_id not in "\n".join(path.read_text() for path in right_stage.rglob("*") if path.is_file())
    assert service.list_artifacts(left.job_id) == ()
    assert service.list_artifacts(right.job_id) == ()
    service.shutdown()


def test_running_cancellation_reaps_worker_and_publishes_no_artifact(tmp_path):
    service = make_service(tmp_path, max_active_jobs=1)
    project = create_project(service)
    job = service.submit_job(project.project_id, "analyze", HASH, auto_start=True, executor_input={"steps": 100, "delay_seconds": 0.2, "artifact_text": "must-not-publish"})
    before = service.supervisor.snapshot(job.job_id)
    assert before.runtime_state is RuntimeState.RUNNING
    assert before.alive
    cancelled = service.cancel_job(job.job_id, grace_seconds=0)
    assert cancelled.status.runtime_state is RuntimeState.CANCELLED
    after = service.supervisor.snapshot(job.job_id)
    assert not after.alive
    assert service.list_artifacts(job.job_id) == ()
    assert not (tmp_path / ".mvstudio" / "jobs" / job.job_id / "result.txt").exists()
    service.shutdown()


def test_idempotency_counters_and_cli_api_canonical_digests(tmp_path, capsys):
    service = make_service(tmp_path)
    project = create_project(service)
    one = service.submit_job(project.project_id, "analyze", HASH, idempotency_key="one", auto_start=True, executor_input={"artifact_text": "one"})
    assert wait(service, one.job_id).runtime_state is RuntimeState.SUCCEEDED
    duplicate = service.submit_job(project.project_id, "analyze", HASH, idempotency_key="one")
    assert duplicate.job_id == one.job_id
    assert list((tmp_path / ".mvstudio" / "jobs").iterdir()) == [tmp_path / ".mvstudio" / "jobs" / one.job_id]
    assert service.supervisor.model_call_count == 0
    assert service.supervisor.token_count == 0

    brief = tmp_path / "brief.json"
    brief.write_text(json.dumps({"title": "api cli"}), encoding="utf-8")
    assert cli_main(["project", "create", "--brief", str(brief), "--slug", "api-cli", "--json"], service=service) == 0
    cli_project = json.loads(capsys.readouterr().out)
    client = TestClient(create_app(service=service))
    api_project = client.post("/api/v1/projects", json={"slug": "api-cli", "brief": {"title": "api cli"}}).json()
    assert cli_project["brief_sha256"] == api_project["brief_sha256"]
    assert cli_main(["job", "submit", "--project", api_project["project_id"], "--operation", "analyze", "--input-digest", HASH, "--json"], service=service) == 0
    cli_job = json.loads(capsys.readouterr().out)
    api_job = client.post(f"/api/v1/projects/{api_project['project_id']}/jobs", json={"operation": "analyze", "input_digest": HASH}).json()
    assert cli_job["canonical_job_digest"] == api_job["canonical_job_digest"]
    assert Settings().host == "127.0.0.1"
    service.shutdown()
