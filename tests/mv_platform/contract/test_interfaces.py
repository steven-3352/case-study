import importlib
import io
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from apps.mv_api import create_app
from apps.mv_cli import main as cli_main
from apps.mv_codex import main as codex_main
from apps.runtime import build_service, load_runtime_environment
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


def test_web_shell_and_safe_project_job_lists(service):
    project, job = create_project_and_job(service)
    client = TestClient(create_app(service=service))

    page = client.get("/")
    assert page.status_code == 200
    assert "本地音乐视频制作台" in page.text

    projects = client.get("/api/v1/projects").json()
    assert projects == [{
        "project_id": project.project_id,
        "slug": "demo",
        "brief_sha256": project.brief_sha256,
        "created_at": project.project.created_at.isoformat(),
    }]
    assert "root" not in projects[0]

    jobs = client.get(f"/api/v1/projects/{project.project_id}/jobs").json()
    assert jobs[0]["job_spec"]["job_id"] == job.job_id
    assert jobs[0]["status"]["runtime_state"] == "queued"
    assert client.get("/api/v1/projects/missing/jobs").status_code == 404


def test_daily_frontend_and_backend_error_logs_are_local_and_redacted(service):
    original_inspect = service.inspect_job
    app = create_app(service=service)
    with TestClient(app, raise_server_exceptions=False) as client:
        paths = client.get("/api/v1/logs").json()
        assert paths["directory"].startswith(str(service.workspace_root))
        assert Path(paths["frontend"]).name.startswith("frontend-")
        assert Path(paths["backend"]).name.startswith("backend-")

        response = client.post(
            "/api/v1/logs/frontend",
            json={"message": "request failed sk-secret123", "path": "/api/test", "status": 409},
        )
        assert response.status_code == 204
        service.inspect_job = lambda _job_id: (_ for _ in ()).throw(RuntimeError("boom"))
        assert client.get("/api/v1/jobs/broken").status_code == 400
    service.inspect_job = original_inspect

    frontend = Path(paths["frontend"]).read_text(encoding="utf-8")
    backend = Path(paths["backend"]).read_text(encoding="utf-8")
    assert "sk-secret123" not in frontend
    assert "[REDACTED]" in frontend
    assert '"source":"frontend"' in frontend
    assert '"source":"backend"' in backend
    assert "RuntimeError" in backend


def test_web_polling_advances_supervisor_before_reading_lists():
    class Supervisor:
        def __init__(self):
            self.ticks = 0

        def tick(self):
            self.ticks += 1

    class Service:
        def __init__(self):
            self.supervisor = Supervisor()

        def list_project_jobs(self, project_id):
            assert project_id == "project-1"
            return ()

    service = Service()
    response = TestClient(create_app(service=service)).get("/api/v1/projects/project-1/jobs")
    assert response.status_code == 200
    assert service.supervisor.ticks == 1


def test_project_delete_requires_slug_and_removes_records_and_files(service):
    project, job = create_project_and_job(service)
    project_root = service.workspace_root / "projects" / project.slug
    staging = service.workspace_root / ".mvstudio" / "jobs" / job.job_id
    staging.mkdir(parents=True)
    (staging / "worker.tmp").write_text("temporary", encoding="utf-8")
    client = TestClient(create_app(service=service))

    mismatch = client.request(
        "DELETE", f"/api/v1/projects/{project.project_id}",
        json={"confirmation_slug": "wrong"},
    )
    assert mismatch.status_code == 409
    assert project_root.exists() and staging.exists()

    deleted = client.request(
        "DELETE", f"/api/v1/projects/{project.project_id}",
        json={"confirmation_slug": project.slug},
    )
    assert deleted.status_code == 200
    assert deleted.json() == {
        "project_id": project.project_id, "slug": project.slug, "deleted": True,
    }
    assert not project_root.exists() and not staging.exists()
    assert client.get(f"/api/v1/projects/{project.project_id}/jobs").status_code == 404
    with service.database.connect() as db:
        assert db.execute("SELECT COUNT(*) FROM projects").fetchone()[0] == 0
        assert db.execute("SELECT COUNT(*) FROM jobs").fetchone()[0] == 0
        assert db.execute("SELECT COUNT(*) FROM job_status").fetchone()[0] == 0


def test_project_delete_blocks_while_a_job_is_running(service):
    project, job = create_project_and_job(service)
    status = service.repository.get_status(job.job_id)
    service.repository.set_status(
        status.transition(RuntimeState.RUNNING, datetime.now(timezone.utc))
    )
    response = TestClient(create_app(service=service)).request(
        "DELETE", f"/api/v1/projects/{project.project_id}",
        json={"confirmation_slug": project.slug},
    )
    assert response.status_code == 423
    assert (service.workspace_root / "projects" / project.slug).exists()
    assert service.repository.get_project(project.project_id).slug == project.slug


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


def test_browser_asset_upload_uses_server_selected_destination():
    class RecordingService:
        def import_project_asset(self, project_id, source_path, filename):
            assert project_id == "project-1"
            assert Path(source_path).read_bytes() == b"selected file"
            assert filename == "role.png"
            return {"ignored": False, "kind": "characters", "relative_path": "inputs/characters/role.png"}

    response = TestClient(create_app(service=RecordingService())).post(
        "/api/v1/projects/project-1/assets?filename=role.png",
        content=b"selected file",
        headers={"Content-Type": "image/png"},
    )
    assert response.status_code == 200
    assert response.json()["relative_path"] == "inputs/characters/role.png"


def test_shot_background_and_keyframe_http_contract(service):
    project = service.create_project("shot-reference-api", {"title": "MV"})
    root = service.workspace_root / "projects" / project.slug
    (root / "creative" / "visual_score.yaml").write_text(
        json.dumps({"shots": [{"id": "S001", "time": [0, 2]}]}), encoding="utf-8",
    )
    image = io.BytesIO()
    Image.new("RGB", (24, 32), (130, 90, 50)).save(image, format="PNG")
    image_bytes = image.getvalue()
    client = TestClient(create_app(service=service))

    imported = client.post(
        f"/api/v1/projects/{project.project_id}/assets?filename=stage.png&kind=backgrounds",
        content=image_bytes,
        headers={"Content-Type": "image/png"},
    )
    assert imported.status_code == 200
    background_path = imported.json()["relative_path"]

    bound = client.put(
        f"/api/v1/projects/{project.project_id}/shots/S001/background",
        json={"relative_path": background_path},
    )
    assert bound.status_code == 200
    storyboard = next(item for item in bound.json()["stages"] if item["id"] == "storyboard")
    assert storyboard["data"]["shots"][0]["background"]["reference"] == background_path

    uploaded = client.post(
        f"/api/v1/projects/{project.project_id}/shots/S001/keyframes?filename=complete.png",
        content=image_bytes,
        headers={"Content-Type": "image/png"},
    )
    assert uploaded.status_code == 200
    keyframes = next(item for item in uploaded.json()["stages"] if item["id"] == "keyframes")
    candidate = keyframes["data"]["shots"][0]["keyframes"][0]

    selected = client.put(
        f"/api/v1/projects/{project.project_id}/shots/S001/keyframes/selection",
        json={"relative_path": candidate},
    )
    assert selected.status_code == 200
    selected_stage = next(
        item for item in selected.json()["stages"] if item["id"] == "keyframes"
    )
    assert selected_stage["data"]["shots"][0]["selected_keyframe"] == candidate

    invalid_candidate = client.put(
        f"/api/v1/projects/{project.project_id}/shots/S001/keyframes/selection",
        json={"relative_path": "assets/source/keyframes/S001/missing.png"},
    )
    assert invalid_candidate.status_code == 409
    assert invalid_candidate.json()["detail"] == "所选组合首帧不属于当前镜头，请重新选择"

    invalid_image = client.post(
        f"/api/v1/projects/{project.project_id}/shots/S001/keyframes?filename=fake.png",
        content=b"not a png",
        headers={"Content-Type": "image/png"},
    )
    assert invalid_image.status_code == 409
    assert invalid_image.json()["detail"] == "参考图片无法读取，请选择有效的 PNG、JPG 或 WebP 图片"


def test_director_api_actions_are_fixed_job_only_commands():
    class RecordingService:
        def __init__(self):
            self.calls = []

        def start_director_intake(self, job_id):
            self.calls.append(("intake", job_id))
            return {"action": "intake"}

        def start_director_animatic_test(self, job_id):
            self.calls.append(("animatic-test", job_id))
            return {"action": "animatic-test"}

        def start_director_animatic_offline_test(self, job_id):
            self.calls.append(("animatic-offline-test", job_id))
            return {"action": "animatic-offline-test"}

        def run_director_plan(self, job_id):
            self.calls.append(("plan", job_id))
            return {"action": "plan"}

        def approve_director_artifacts(self, job_id):
            self.calls.append(("approve", job_id))
            return {"action": "approve"}

        def publish_director_artifacts(self, job_id):
            self.calls.append(("publish", job_id))
            return {"action": "publish"}

    service = RecordingService()
    client = TestClient(create_app(service=service))
    paths = (
        ("/api/v1/jobs/job-1/director/intake", "intake"),
        ("/api/v1/jobs/job-1/director/animatic-test", "animatic-test"),
        ("/api/v1/jobs/job-1/director/animatic-offline-test", "animatic-offline-test"),
        ("/api/v1/jobs/job-1/director/plan", "plan"),
        ("/api/v1/jobs/job-1/director/approve", "approve"),
        ("/api/v1/jobs/job-1/director/publish", "publish"),
    )
    for path, action in paths:
        response = client.post(path)
        assert response.status_code == 200
        assert response.json() == {"action": action}
        assert client.post(path, json={"path": "/tmp/escape"}).status_code == 200
    assert service.calls == [
        ("intake", "job-1"), ("intake", "job-1"),
        ("animatic-test", "job-1"), ("animatic-test", "job-1"),
        ("animatic-offline-test", "job-1"), ("animatic-offline-test", "job-1"),
        ("plan", "job-1"), ("plan", "job-1"),
        ("approve", "job-1"), ("approve", "job-1"),
        ("publish", "job-1"), ("publish", "job-1"),
    ]


def test_director_cli_actions_delegate_without_path_or_executor_arguments(capsys):
    class RecordingService:
        supervisor = None

        def __init__(self):
            self.calls = []

        def start_director_intake(self, job_id):
            self.calls.append(("intake", job_id))
            return {"action": "intake"}

        def start_director_animatic_test(self, job_id):
            self.calls.append(("animatic-test", job_id))
            return {"action": "animatic-test"}

        def start_director_animatic_offline_test(self, job_id):
            self.calls.append(("animatic-offline-test", job_id))
            return {"action": "animatic-offline-test"}

        def approve_director_artifacts(self, job_id):
            self.calls.append(("approve", job_id))
            return {"action": "approve"}

        def publish_director_artifacts(self, job_id):
            self.calls.append(("publish", job_id))
            return {"action": "publish"}

    service = RecordingService()
    for command, action in (
        ("director-intake", "intake"),
        ("director-animatic-test", "animatic-test"),
        ("director-animatic-offline-test", "animatic-offline-test"),
        ("director-approve", "approve"),
        ("director-publish", "publish"),
    ):
        assert cli_main(["job", command, "job-1", "--json"], service=service) == 0
        assert json.loads(capsys.readouterr().out) == {"action": action}
    assert service.calls == [
        ("intake", "job-1"),
        ("animatic-test", "job-1"),
        ("animatic-offline-test", "job-1"),
        ("approve", "job-1"),
        ("publish", "job-1"),
    ]


def test_seedance_actions_are_fixed_job_only_commands(capsys):
    class RecordingService:
        supervisor = None

        def __init__(self):
            self.calls = []

        def start_seedance_shot(self, job_id):
            self.calls.append(job_id)
            return {"action": "seedance-shot", "job_id": job_id}

    service = RecordingService()
    client = TestClient(create_app(service=service))

    response = client.post("/api/v1/jobs/job-1/seedance/shot")
    assert response.status_code == 200
    assert response.json() == {"action": "seedance-shot", "job_id": "job-1"}
    with_body = client.post(
        "/api/v1/jobs/job-1/seedance/shot",
        json={"path": "/tmp/escape", "prompt": "override"},
    )
    assert with_body.status_code == 200
    assert cli_main(["job", "seedance-shot", "job-2", "--json"], service=service) == 0
    assert json.loads(capsys.readouterr().out) == {
        "action": "seedance-shot",
        "job_id": "job-2",
    }
    with pytest.raises(SystemExit):
        cli_main(
            ["job", "seedance-shot", "job-3", "--path", "/tmp/escape"],
            service=service,
        )
    assert service.calls == ["job-1", "job-1", "job-2"]


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


def test_cli_owned_service_loads_runtime_environment(monkeypatch, capsys):
    class Service:
        supervisor = None

    loaded = []
    cli_module = importlib.import_module("apps.mv_cli")
    monkeypatch.setattr(cli_module, "load_runtime_environment", lambda: loaded.append(True))
    monkeypatch.setattr(cli_module, "build_service", lambda _root: Service())

    assert cli_main(["doctor", "--json"]) == 0
    assert loaded == [True]
    assert json.loads(capsys.readouterr().out) == {"status": "ready"}


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


def test_runtime_environment_loads_dotenv_without_overriding_explicit_values(
    tmp_path, monkeypatch
):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "LLM_BASE_URL=https://example.invalid/v1\n"
        "LLM_API_KEY=from-dotenv\n"
        "LLM_MODEL=from-dotenv-model\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("LLM_BASE_URL", raising=False)
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.setenv("LLM_MODEL", "explicit-model")

    assert load_runtime_environment(env_file) is True
    assert os.environ["LLM_BASE_URL"] == "https://example.invalid/v1"
    assert os.environ["LLM_API_KEY"] == "from-dotenv"
    assert os.environ["LLM_MODEL"] == "explicit-model"


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
    loaded = []
    monkeypatch.setattr(api_module, "load_runtime_environment", lambda: loaded.append(True))
    monkeypatch.setattr(api_module, "build_service", lambda _root: owned)
    with TestClient(create_app(workspace_root=".")):
        pass
    assert owned.shutdown_calls == 1

    assert loaded == [True]


def test_interface_modules_have_no_forbidden_dependencies():
    output_root = Path(__file__).resolve().parents[3]
    forbidden = (
        "mingyue_render", "paperdoll_engine", "render_frame", "multiprocessing",
        "ffmpeg", "openai", "codex exec", "subprocess",
    )
    for path in (output_root / "apps").rglob("*.py"):
        content = path.read_text(encoding="utf-8").lower()
        assert not any(term in content for term in forbidden), path
