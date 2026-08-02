"""PRD-005 unit tests: async job submit, SSE event emission, active_jobs workflow field."""
import json
import struct
import sys
import zlib
from datetime import datetime, timezone
from pathlib import Path

import pytest
import yaml

SOURCE_ROOT = Path(__file__).resolve().parents[4] / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from mv_platform.application.service import ApplicationService, ApplicationBlocked
from mv_platform.config import Settings
from mv_platform.infrastructure import Database


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_tiny_png():
    def chunk(name, data):
        c = struct.pack(">I", len(data)) + name + data
        return c + struct.pack(">I", zlib.crc32(name + data) & 0xFFFFFFFF)
    header = b"\x89PNG\r\n\x1a\n"
    ihdr = chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
    idat = chunk(b"IDAT", zlib.compress(b"\x00\xff\xff\xff"))
    iend = chunk(b"IEND", b"")
    return header + ihdr + idat + iend


TINY_PNG = _make_tiny_png()


def make_service(tmp_path):
    settings = Settings()
    database = Database(tmp_path / settings.db_path)
    service = ApplicationService(
        settings, database, workspace_root=tmp_path,
        semantic_port=None, semantic_model="test-model",
    )
    service.initialize()
    return service


def _write_yaml(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True)


def _write_json(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _write_decision(root: Path, stage: str, action: str = "approve"):
    decisions_path = root / "creative" / "workflow-decisions.json"
    decisions_path.parent.mkdir(parents=True, exist_ok=True)
    decisions = {}
    if decisions_path.exists():
        decisions = json.loads(decisions_path.read_text())
    decisions[stage] = {
        "action": action, "note": "test",
        "decided_at": datetime.now(timezone.utc).isoformat(),
        "actor": "local_user",
    }
    decisions_path.write_text(json.dumps(decisions, ensure_ascii=False))


def _setup_project_for_background(tmp_path, slug="ut040"):
    """Project with story+storyboard approved and scene_groups containing S001."""
    service = make_service(tmp_path)
    result = service.create_project(slug, {"title": "SSE测试"})
    project_id = result.project_id
    root = service.workspace_root / "projects" / slug
    now = datetime.now(timezone.utc).isoformat()

    _write_yaml(root / "creative" / "visual_score.yaml", {
        "shots": [{"id": "S001", "section": "A"}], "sections": [],
    })
    _write_json(root / "creative" / "scene-groups.json", {
        "version": 1, "generated_by": "test", "generated_at": now,
        "scene_groups": [
            {"id": "SG001", "name": "场景A", "source_section_id": "A",
             "shot_ids": ["S001"], "location": "", "time_of_day": "",
             "weather": "", "emotional_state": "", "narrative_world_state": "",
             "created_by": "system", "created_at": now, "updated_at": now},
        ],
    })
    _write_json(root / "creative" / "shot-references.json", {
        "version": 2, "shots": {"S001": {}},
    })
    _write_decision(root, "story")
    _write_decision(root, "storyboard")
    return service, project_id, root


def _setup_project_for_keyframe(tmp_path, slug="ut040kf"):
    """Project with scenes approved and S001 background_master_id set."""
    service = make_service(tmp_path)
    result = service.create_project(slug, {"title": "SSE首帧测试"})
    project_id = result.project_id
    root = service.workspace_root / "projects" / slug
    now = datetime.now(timezone.utc).isoformat()

    _write_yaml(root / "creative" / "visual_score.yaml", {
        "shots": [{"id": "S001", "section": "A"}], "sections": [],
    })
    _write_json(root / "creative" / "scene-groups.json", {
        "version": 1, "generated_by": "test", "generated_at": now,
        "scene_groups": [
            {"id": "SG001", "name": "场景A", "source_section_id": "A",
             "shot_ids": ["S001"], "location": "", "time_of_day": "",
             "weather": "", "emotional_state": "", "narrative_world_state": "",
             "created_by": "system", "created_at": now, "updated_at": now},
        ],
    })
    _write_json(root / "creative" / "background-masters.json", {
        "version": 1,
        "backgrounds": [
            {"id": "BG001", "scene_group_id": "SG001", "status": "selected",
             "source": "generated", "relative_path": "assets/generated/backgrounds/S001-bg.png",
             "prompt_zh": "", "prompt_en": "", "model": "", "request_id": "",
             "cost_yuan": 0.5, "created_at": now},
        ],
    })
    bg_path = root / "assets/generated/backgrounds/S001-bg.png"
    bg_path.parent.mkdir(parents=True, exist_ok=True)
    bg_path.write_bytes(TINY_PNG)
    _write_json(root / "creative" / "shot-references.json", {
        "version": 2,
        "shots": {"S001": {
            "background": "assets/generated/backgrounds/S001-bg.png",
            "background_master_id": "BG001",
        }},
    })
    _write_decision(root, "story")
    _write_decision(root, "storyboard")
    _write_decision(root, "scenes")
    return service, project_id, root


# ---------------------------------------------------------------------------
# UT-040: submit_generate_background_job returns job_id + queued
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_submit_background_job_returns_job_id(tmp_path):
    """UT-040: submit_generate_background_job returns {job_id, status: queued}."""
    service, project_id, _ = _setup_project_for_background(tmp_path, "ut040")
    result = service.submit_generate_background_job(project_id, "S001")
    assert "job_id" in result
    assert result["job_id"]
    assert result["status"] == "queued"


# ---------------------------------------------------------------------------
# UT-041: _run_pending_jobs_sync emits progress + done events
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_background_job_emits_progress_events(tmp_path, monkeypatch):
    """UT-041: background job emits progress/done SSE events on success."""
    service, project_id, _ = _setup_project_for_background(tmp_path, "ut041")
    monkeypatch.setattr(service, "generate_shot_background", lambda pid, sid, **kw: None)
    monkeypatch.setattr(service, "_translate_prompt", lambda *a, **kw: "translated")

    result = service.submit_generate_background_job(project_id, "S001")
    job_id = result["job_id"]

    service._run_pending_jobs_sync()

    events = service.repository.list_events(job_id)
    event_types = [e.event_type for e in events]
    stages = [e.payload.get("stage", "") for e in events]

    assert "progress" in event_types
    assert "done" in event_types
    assert "error" not in event_types
    assert "translate_prompt" in stages
    assert "generate_image" in stages
    assert "save_result" in stages


# ---------------------------------------------------------------------------
# UT-042: error on translate failure emits error event with correct stage
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_background_job_emits_error_on_translate_fail(tmp_path, monkeypatch):
    """UT-042: when generate_shot_background raises with error_stage, error event has that stage."""
    service, project_id, _ = _setup_project_for_background(tmp_path, "ut042")

    def _fail(pid, sid, **kw):
        raise ApplicationBlocked("翻译超时", error_stage="translate_prompt")

    monkeypatch.setattr(service, "generate_shot_background", _fail)
    monkeypatch.setattr(service, "_translate_prompt", lambda *a, **kw: "translated")

    result = service.submit_generate_background_job(project_id, "S001")
    job_id = result["job_id"]
    service._run_pending_jobs_sync()

    events = service.repository.list_events(job_id)
    event_types = [e.event_type for e in events]
    assert "error" in event_types
    assert "done" not in event_types

    error_event = next(e for e in events if e.event_type == "error")
    assert error_event.payload["stage"] == "translate_prompt"


# ---------------------------------------------------------------------------
# UT-043: workflow active_jobs non-empty while job is queued
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_workflow_active_jobs_while_queued(tmp_path):
    """UT-043: active_jobs in workflow includes the job before it runs."""
    service, project_id, _ = _setup_project_for_background(tmp_path, "ut043")
    result = service.submit_generate_background_job(project_id, "S001")
    job_id = result["job_id"]

    wf = service.get_project_workflow(project_id)
    active = wf.get("active_jobs", [])
    assert len(active) > 0
    job_entry = next((j for j in active if j["job_id"] == job_id), None)
    assert job_entry is not None
    assert job_entry["status"] in ("queued", "running")
    assert job_entry["shot_id"] == "S001"


# ---------------------------------------------------------------------------
# UT-044: workflow active_jobs empty after job completes
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_workflow_no_active_jobs_after_done(tmp_path, monkeypatch):
    """UT-044: active_jobs is empty after _run_pending_jobs_sync completes the job."""
    service, project_id, _ = _setup_project_for_background(tmp_path, "ut044")
    monkeypatch.setattr(service, "generate_shot_background", lambda pid, sid, **kw: None)

    service.submit_generate_background_job(project_id, "S001")
    service._run_pending_jobs_sync()

    wf = service.get_project_workflow(project_id)
    assert wf.get("active_jobs", []) == []
