"""PRD-003 unit tests: keyframe metadata, preconditions, compatibility."""
import io
import json
import sys
import struct
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
        c = struct.pack('>I', len(data)) + name + data
        return c + struct.pack('>I', zlib.crc32(name + data) & 0xffffffff)
    header = b'\x89PNG\r\n\x1a\n'
    ihdr = chunk(b'IHDR', struct.pack('>IIBBBBB', 1, 1, 8, 2, 0, 0, 0))
    idat = chunk(b'IDAT', zlib.compress(b'\x00\xff\xff\xff'))
    iend = chunk(b'IEND', b'')
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


def _project_root(service, slug):
    return service.workspace_root / "projects" / slug


def _write_yaml(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True)


def _write_json(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _write_decision(root, stage, action="approve"):
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


def _setup_project_with_scenes_approved(tmp_path, slug):
    service = make_service(tmp_path)
    result = service.create_project(slug, {"title": "测试"})
    project_id = result.project_id
    root = _project_root(service, slug)
    now = datetime.now(timezone.utc).isoformat()

    _write_yaml(root / "creative" / "visual_score.yaml", {
        "shots": [{"id": "S001", "section": "A"}],
        "sections": [],
    })
    _write_json(root / "creative" / "scene-groups.json", {
        "version": 1,
        "generated_by": "test",
        "generated_at": now,
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
    _write_json(root / "creative" / "shot-references.json", {
        "version": 2,
        "shots": {
            "S001": {
                "background": "assets/generated/backgrounds/S001-bg.png",
                "background_master_id": "BG001",
            },
        },
    })
    # Write fake background file so it passes file existence check
    bg_path = root / "assets/generated/backgrounds/S001-bg.png"
    bg_path.parent.mkdir(parents=True, exist_ok=True)
    bg_path.write_bytes(TINY_PNG)

    _write_decision(root, "story")
    _write_decision(root, "storyboard")
    _write_decision(root, "scenes")

    return service, project_id, root


# ---------------------------------------------------------------------------
# UT-022: _read_keyframe_entries upgrades legacy string entries
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_read_keyframe_entries_upgrades_strings():
    shot = {"keyframes": ["assets/generated/keyframes/S001-old.png", "assets/generated/keyframes/S001-new.png"]}
    entries = ApplicationService._read_keyframe_entries(shot)
    assert all(isinstance(e, dict) for e in entries)
    assert entries[0]["source"] == "legacy"
    assert entries[0]["path"] == "assets/generated/keyframes/S001-old.png"
    assert entries[0]["cost_yuan"] == 0.0
    assert entries[0]["character_ids"] == []


@pytest.mark.unit
def test_read_keyframe_entries_passes_through_dicts():
    entry = {
        "path": "assets/generated/keyframes/S001-abc.png",
        "source": "generated", "background_master_id": "BG001",
        "character_ids": ["C001"], "prompt_zh": "夜晚", "prompt_en": "night",
        "model": "gpt-image-2", "request_id": "req-123", "cost_yuan": 0.5,
        "created_at": "2026-08-01T00:00:00+00:00",
    }
    shot = {"keyframes": [entry]}
    entries = ApplicationService._read_keyframe_entries(shot)
    assert entries[0] is entry


@pytest.mark.unit
def test_read_keyframe_entries_mixed_formats():
    shot = {
        "keyframes": [
            "assets/generated/keyframes/old.png",
            {"path": "assets/generated/keyframes/new.png", "source": "uploaded",
             "background_master_id": "", "character_ids": [], "prompt_zh": "", "prompt_en": "",
             "model": "", "request_id": "", "cost_yuan": 0.0, "created_at": ""},
        ]
    }
    entries = ApplicationService._read_keyframe_entries(shot)
    assert len(entries) == 2
    assert entries[0]["source"] == "legacy"
    assert entries[1]["source"] == "uploaded"


# ---------------------------------------------------------------------------
# UT-021: import_shot_keyframe writes metadata object
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_import_keyframe_writes_metadata_entry(tmp_path):
    service, project_id, root = _setup_project_with_scenes_approved(tmp_path, "importtest")

    png_file = tmp_path / "test_frame.png"
    png_file.write_bytes(TINY_PNG)

    service.import_shot_keyframe(project_id, "S001", str(png_file), "test_frame.png")

    refs = service._shot_references(root)
    keyframes = refs["shots"]["S001"]["keyframes"]
    assert len(keyframes) == 1
    entry = keyframes[0]
    assert isinstance(entry, dict), "keyframe entry must be a dict, not a string"
    assert entry["source"] == "uploaded"
    assert entry["cost_yuan"] == 0.0
    assert entry["prompt_en"] == ""
    assert entry["background_master_id"] == ""
    assert entry["character_ids"] == []
    assert "created_at" in entry
    assert entry["path"].startswith("assets/source/keyframes/S001/")


# ---------------------------------------------------------------------------
# UT-023: scenes not approved → blocked
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_generate_keyframe_blocked_without_scenes_approval(tmp_path):
    service = make_service(tmp_path)
    result = service.create_project("nostage", {"title": "测试"})
    project_id = result.project_id
    root = _project_root(service, "nostage")

    _write_yaml(root / "creative" / "visual_score.yaml", {
        "shots": [{"id": "S001", "section": "A"}], "sections": [],
    })
    _write_decision(root, "story")
    _write_decision(root, "storyboard")
    # scenes NOT approved

    with pytest.raises(ApplicationBlocked) as exc_info:
        service.generate_shot_keyframe(project_id, "S001")

    msg = str(exc_info.value).lower()
    assert "scenes" in msg
    assert exc_info.value.error_stage == "precondition"


# ---------------------------------------------------------------------------
# UT-024: background_master_id empty → blocked
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_generate_keyframe_blocked_without_background_master(tmp_path):
    service = make_service(tmp_path)
    result = service.create_project("nobg", {"title": "测试"})
    project_id = result.project_id
    root = _project_root(service, "nobg")

    _write_yaml(root / "creative" / "visual_score.yaml", {
        "shots": [{"id": "S001", "section": "A"}], "sections": [],
    })
    # shot-references has background but NO background_master_id
    _write_json(root / "creative" / "shot-references.json", {
        "version": 2,
        "shots": {
            "S001": {
                "background": "assets/generated/backgrounds/S001-bg.png",
            },
        },
    })
    _write_decision(root, "story")
    _write_decision(root, "storyboard")
    _write_decision(root, "scenes")

    with pytest.raises(ApplicationBlocked) as exc_info:
        service.generate_shot_keyframe(project_id, "S001")

    msg = str(exc_info.value).lower()
    assert "background master" in msg


# ---------------------------------------------------------------------------
# UT-025: workflow returns keyframe_entries list
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_workflow_includes_keyframe_entries(tmp_path):
    service, project_id, root = _setup_project_with_scenes_approved(tmp_path, "wfentries")
    now = datetime.now(timezone.utc).isoformat()

    kf_path = "assets/generated/keyframes/S001-test.png"
    kf_file = root / kf_path
    kf_file.parent.mkdir(parents=True, exist_ok=True)
    kf_file.write_bytes(TINY_PNG)

    _write_json(root / "creative" / "shot-references.json", {
        "version": 3,
        "shots": {
            "S001": {
                "background": "assets/generated/backgrounds/S001-bg.png",
                "background_master_id": "BG001",
                "keyframes": [
                    {
                        "path": kf_path,
                        "source": "generated",
                        "background_master_id": "BG001",
                        "character_ids": ["C001"],
                        "prompt_zh": "夜晚",
                        "prompt_en": "night garden",
                        "model": "gpt-image-2",
                        "request_id": "req-001",
                        "cost_yuan": 0.5,
                        "created_at": now,
                    }
                ],
                "selected_keyframe": kf_path,
            },
        },
    })

    wf = service.get_project_workflow(project_id)
    kf_stage = next(s for s in wf["stages"] if s["id"] == "keyframes")
    shots = kf_stage["data"]["shots"]
    assert len(shots) > 0
    shot = shots[0]
    assert "keyframe_entries" in shot, "keyframe_entries must be present in workflow shot data"
    assert len(shot["keyframe_entries"]) == 1
    entry = shot["keyframe_entries"][0]
    assert entry["source"] == "generated"
    assert entry["background_master_id"] == "BG001"
    assert entry["cost_yuan"] == 0.5
    assert entry["is_selected"] is True


# ---------------------------------------------------------------------------
# UT-020: generate_shot_keyframe writes metadata entry (mock provider)
# ---------------------------------------------------------------------------

class _MockImageProvider:
    model = "gpt-image-2-mock"

    def generate(self, prompt, references=None, size=None):
        return TINY_PNG


@pytest.mark.unit
def test_generate_keyframe_writes_metadata_entry(tmp_path, monkeypatch):
    service, project_id, root = _setup_project_with_scenes_approved(tmp_path, "gentest")

    service.image_provider = _MockImageProvider()

    def _mock_translate(self_inner, project_id_inner, event_type, context, request_id):
        return "test english prompt", {"source_prompt_hash": "sha256:" + "0" * 64}

    monkeypatch.setattr(ApplicationService, "_translate_image_prompt", _mock_translate)

    service.generate_shot_keyframe(project_id, "S001")

    refs = service._shot_references(root)
    keyframes = refs["shots"]["S001"]["keyframes"]
    assert len(keyframes) == 1
    entry = keyframes[0]
    assert isinstance(entry, dict), "keyframe entry must be a metadata dict"
    assert entry["source"] == "generated"
    assert entry["background_master_id"] == "BG001"
    assert entry["prompt_en"] == "test english prompt"
    assert entry["cost_yuan"] == 0.5
    assert entry["model"] == "gpt-image-2-mock"
    assert entry["path"].startswith("assets/generated/keyframes/S001-")
