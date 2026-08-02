"""PRD-007 unit tests: en_prompt bypass for background/keyframe generation."""
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

from mv_platform.application.service import ApplicationService
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


def _setup_project_for_background(tmp_path, slug="ut071bg"):
    service = make_service(tmp_path)
    result = service.create_project(slug, {"title": "PRD007背景测试"})
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


def _setup_project_for_keyframe(tmp_path, slug="ut071kf"):
    service = make_service(tmp_path)
    result = service.create_project(slug, {"title": "PRD007首帧测试"})
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
# UT-071: en_prompt provided → translate skipped
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_submit_background_with_en_prompt_skips_translation(tmp_path, monkeypatch):
    """UT-071: submit_generate_background_job with en_prompt does not call _translate_prompt."""
    service, project_id, _ = _setup_project_for_background(tmp_path, "ut071")
    translate_called = []
    monkeypatch.setattr(service, "_translate_prompt",
                        lambda *a, **kw: translate_called.append(1) or "translated")
    monkeypatch.setattr(service, "generate_shot_background", lambda *a, **kw: None)

    service.submit_generate_background_job(project_id, "S001", en_prompt="sky at dusk")
    service._run_pending_jobs_sync()

    assert len(translate_called) == 0, "translate should be skipped when en_prompt provided"


# ---------------------------------------------------------------------------
# UT-072: no en_prompt → translate is called
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_submit_background_without_en_prompt_calls_translation(tmp_path, monkeypatch):
    """UT-072: submit_generate_background_job without en_prompt calls _translate_prompt."""
    service, project_id, _ = _setup_project_for_background(tmp_path, "ut072")
    translate_called = []
    monkeypatch.setattr(service, "_translate_prompt",
                        lambda *a, **kw: translate_called.append(1) or "translated")
    monkeypatch.setattr(service, "generate_shot_background", lambda *a, **kw: None)

    service.submit_generate_background_job(project_id, "S001")
    service._run_pending_jobs_sync()

    assert len(translate_called) == 1


# ---------------------------------------------------------------------------
# UT-073: translate done event includes en_prompt field
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_translate_done_event_includes_en_prompt(tmp_path, monkeypatch):
    """UT-073: after translation, progress event at pct=30 carries en_prompt field."""
    service, project_id, _ = _setup_project_for_background(tmp_path, "ut073")
    monkeypatch.setattr(service, "_translate_prompt", lambda *a, **kw: "blue sky")
    monkeypatch.setattr(service, "generate_shot_background", lambda *a, **kw: None)

    result = service.submit_generate_background_job(project_id, "S001")
    service._run_pending_jobs_sync()

    events = service.repository.list_events(result["job_id"])
    translate_done = next(
        (e for e in events
         if e.event_type == "progress"
         and e.payload.get("stage") == "translate_prompt"
         and e.payload.get("pct", 0) >= 30),
        None,
    )
    assert translate_done is not None, "expected translate_prompt progress event at pct>=30"
    assert translate_done.payload.get("en_prompt") == "blue sky"


# ---------------------------------------------------------------------------
# UT-074: job with en_prompt has no translate_prompt stage event
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_no_translate_progress_event_when_en_prompt_cached(tmp_path, monkeypatch):
    """UT-074: when en_prompt provided, events contain no translate_prompt stage."""
    service, project_id, _ = _setup_project_for_background(tmp_path, "ut074")
    monkeypatch.setattr(service, "generate_shot_background", lambda *a, **kw: None)

    result = service.submit_generate_background_job(
        project_id, "S001", en_prompt="blue sky"
    )
    service._run_pending_jobs_sync()

    events = service.repository.list_events(result["job_id"])
    stages = [e.payload.get("stage") for e in events if e.event_type == "progress"]
    assert "translate_prompt" not in stages
    assert "generate_image" in stages


# ---------------------------------------------------------------------------
# UT-075: keyframe job with en_prompt skips translation
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_submit_keyframe_with_en_prompt_skips_translation(tmp_path, monkeypatch):
    """UT-075: submit_generate_keyframe_job with en_prompt does not call _translate_prompt."""
    service, project_id, _ = _setup_project_for_keyframe(tmp_path, "ut075")
    translate_called = []
    monkeypatch.setattr(service, "_translate_prompt",
                        lambda *a, **kw: translate_called.append(1) or "translated")
    monkeypatch.setattr(service, "generate_shot_keyframe", lambda *a, **kw: None)

    service.submit_generate_keyframe_job(project_id, "S001", en_prompt="close-up portrait")
    service._run_pending_jobs_sync()

    assert len(translate_called) == 0
