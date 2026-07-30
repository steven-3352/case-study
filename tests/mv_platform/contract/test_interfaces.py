import importlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from apps.mv_api import create_app
from apps.mv_cli import main as cli_main
from apps.mv_codex import main as codex_main
from apps.runtime import build_service
from mv_platform.application.service import (
    ApplicationBlocked,
    ApplicationConflict,
    ApplicationNotFound,
)
from mv_platform.domain import Event
from mv_platform.domain.states import RuntimeState


HASH = "sha256:" + "a" * 64


@pytest.fixture
def service(tmp_path):
    instance = build_service(tmp_path, with_supervisor=False)
    yield instance


def create_project_and_job(service):
    project = service.create_project("demo", {"title": "MV", "nested": {"b": 2, "a": 1}})
    job = service.submit_job(project.project_id, "analyze", HASH)
    return project, job


def test_health_ready_and_strict_requests(service):
    client = TestClient(create_app(service=service))
    assert client.get("/healthz").json() == {"status": "alive"}
    assert client.get("/readyz").json() == {"status": "ready"}
    assert TestClient(create_app()).get("/readyz").status_code == 503
    response = client.post(
        "/api/v1/projects", json={"slug": "demo", "brief": {}, "unknown": True}
    )
    assert response.status_code == 422


def test_api_and_cli_return_identical_canonical_digests(service, tmp_path, capsys):
    brief_path = tmp_path / "brief.json"
    brief_path.write_text('{"nested":{"a":1,"b":2},"title":"MV"}', encoding="utf-8")
    code = cli_main(
        ["project", "create", "--brief", str(brief_path), "--slug", "demo", "--json"],
        service=service,
    )
    cli_project = json.loads(capsys.readouterr().out)
    client = TestClient(create_app(service=service))
    api_project = client.post(
        "/api/v1/projects",
        json={"slug": "demo", "brief": {"title": "MV", "nested": {"b": 2, "a": 1}}},
    ).json()
    assert code == 0
    assert cli_project["brief_sha256"] == api_project["brief_sha256"]

    code = cli_main(
        [
            "job", "submit", "--project", api_project["project_id"],
            "--operation", "analyze", "--input-digest", HASH, "--json",
        ],
        service=service,
    )
    cli_job = json.loads(capsys.readouterr().out)
    api_job = client.post(
        f"/api/v1/projects/{api_project['project_id']}/jobs",
        json={"operation": "analyze", "input_digest": HASH},
    ).json()
    assert code == 0
    assert cli_job["canonical_job_digest"] == api_job["canonical_job_digest"]


@pytest.mark.parametrize(
    ("exception", "status"),
    [
        (ApplicationNotFound("missing"), 404),
        (ApplicationConflict("conflict"), 409),
        (ApplicationBlocked("blocked"), 423),
        (ValueError("invalid"), 400),
    ],
)
def test_api_error_mapping(exception, status):
    class BrokenService:
        def inspect_job(self, _job_id):
            raise exception

    response = TestClient(
        create_app(service=BrokenService()), raise_server_exceptions=False
    ).get("/api/v1/jobs/x")
    assert response.status_code == status


def test_unexpected_api_and_cli_errors_do_not_leak_absolute_paths(capsys):
    secret_path = "/Users/example/private/secrets.txt"

    class BrokenService:
        def inspect_job(self, _job_id):
            raise RuntimeError(secret_path)

    response = TestClient(
        create_app(service=BrokenService()), raise_server_exceptions=False
    ).get("/api/v1/jobs/x")
    assert response.status_code == 400
    assert secret_path not in response.text

    class BrokenCliService:
        supervisor = None

        def inspect_job(self, _job_id):
            raise OSError(secret_path)

    assert cli_main(["job", "inspect", "x", "--json"], service=BrokenCliService()) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert secret_path not in captured.err


def test_start_cancel_inspect_and_artifacts(service):
    project, job = create_project_and_job(service)

    class Supervisor:
        def __init__(self):
            self.started = []

        def submit(self, job_id, executor, executor_input):
            self.started.append((job_id, executor, executor_input))
            return service.inspect_job(job_id)

        def cancel(self, job_id, grace):
            status = service.repository.get_status(job_id)
            service.repository.set_status(
                status.transition(RuntimeState.CANCELLED, datetime.now(timezone.utc))
            )

    supervisor = Supervisor()
    service.supervisor = supervisor
    client = TestClient(create_app(service=service))
    started = client.post(
        f"/api/v1/jobs/{job.job_id}/start",
        json={"executor": "fake", "executor_input": {"steps": 2}},
    )
    assert started.status_code == 200
    assert supervisor.started == [(job.job_id, "fake", {"steps": 2})]
    assert client.get(f"/api/v1/jobs/{job.job_id}").status_code == 200
    assert client.get(f"/api/v1/jobs/{job.job_id}/artifacts").json() == []
    cancelled = client.post(
        f"/api/v1/jobs/{job.job_id}/cancel", json={"grace_seconds": 0.25}
    )
    assert cancelled.status_code == 200
    assert cancelled.json()["status"]["runtime_state"] == "cancelled"


def test_api_auto_start_preserves_executor_fields():
    class RecordingService:
        def __init__(self):
            self.call = None

        def submit_job(self, project_id, **values):
            self.call = (project_id, values)
            return {"accepted": True}

    service = RecordingService()
    response = TestClient(create_app(service=service)).post(
        "/api/v1/projects/project-1/jobs",
        json={
            "operation": "analyze",
            "input_digest": HASH,
            "auto_start": True,
            "executor": "fake",
            "executor_input": {"steps": 3},
        },
    )
    assert response.status_code == 200
    assert service.call[1]["executor"] == "fake"
    assert service.call[1]["executor_input"] == {"steps": 3}


def test_sse_is_ordered_replayable_and_follow_false_closes(service):
    _project, job = create_project_and_job(service)
    now = datetime.now(timezone.utc)
    service.repository.append_event(Event(job.job_id, 1, "job.first", now, {"z": 2, "a": 1}))
    service.repository.append_event(Event(job.job_id, 2, "job.second", now, {"step": 2}))
    client = TestClient(create_app(service=service))

    response = client.get(f"/api/v1/jobs/{job.job_id}/events?follow=false")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert response.text.index("id: 1") < response.text.index("id: 2")
    assert 'data: {"a":1,"z":2}' in response.text

    replay = client.get(
        f"/api/v1/jobs/{job.job_id}/events?follow=false",
        headers={"Last-Event-ID": "1"},
    )
    assert "id: 1" not in replay.text
    assert "id: 2" in replay.text
    assert client.get("/api/v1/jobs/missing/events?follow=false").status_code == 404
    assert client.get(
        f"/api/v1/jobs/{job.job_id}/events", headers={"Last-Event-ID": "bad"}
    ).status_code == 400


def test_cli_follow_polls_until_terminal_and_keeps_stdout_machine_readable(capsys):
    now = datetime.now(timezone.utc)

    class FollowingService:
        supervisor = None

        def __init__(self):
            self.calls = 0

        def list_events(self, job_id, after):
            self.calls += 1
            if self.calls == 1:
                return ()
            return (Event(job_id, 1, "job.succeeded", now, {}),)

        def inspect_job(self, _job_id):
            state = "running" if self.calls < 2 else "succeeded"
            status = type("Status", (), {"runtime_state": type("State", (), {"value": state})()})()
            return type("Inspection", (), {"status": status})()

    following = FollowingService()
    assert cli_main(["job", "events", "job-1", "--follow"], service=following) == 0
    captured = capsys.readouterr()
    assert following.calls >= 2
    assert json.loads(captured.out)["event"] == "job.succeeded"
    assert captured.err == ""


def test_cli_exit_codes_stderr_and_codex_delegation(service, capsys):
    assert codex_main is cli_main
    assert cli_main(["job", "inspect", "missing", "--json"], service=service) == 3
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.strip() == "not found"


def test_runtime_import_has_no_filesystem_side_effects(tmp_path):
    output_root = Path(__file__).resolve().parents[3]
    code = "import apps.runtime; from mv_platform.config import Settings; print(Settings().host)"
    env = dict(os.environ)
    env["PYTHONPATH"] = str(output_root)
    completed = subprocess.run(
        [sys.executable, "-c", code], cwd=tmp_path, env=env,
        text=True, capture_output=True, check=True,
    )
    assert completed.stdout.strip() == "127.0.0.1"
    assert list(tmp_path.iterdir()) == []


def test_lifespan_shutdown_ownership(monkeypatch):
    class Service:
        def __init__(self):
            self.shutdown_calls = 0

        def shutdown(self):
            self.shutdown_calls += 1

    injected = Service()
    with TestClient(create_app(service=injected)):
        pass
    assert injected.shutdown_calls == 0

    owned = Service()
    api_module = importlib.import_module("apps.mv_api")
    monkeypatch.setattr(api_module, "build_service", lambda _root: owned)
    with TestClient(create_app(workspace_root=".")):
        pass
    assert owned.shutdown_calls == 1


def test_interface_modules_have_no_forbidden_dependencies():
    output_root = Path(__file__).resolve().parents[3]
    forbidden = (
        "mingyue_render", "paperdoll_engine", "render_frame", "multiprocessing",
        "ffmpeg", "openai", "codex exec", "subprocess",
    )
    for path in (output_root / "apps").rglob("*.py"):
        content = path.read_text(encoding="utf-8").lower()
        assert not any(term in content for term in forbidden), path
