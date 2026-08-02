"""PRD-002 unit tests: SceneGroup, BackgroundMaster, migration, CRUD."""
import json
import sys
from pathlib import Path
from datetime import datetime, timezone

import pytest
import yaml

SOURCE_ROOT = Path(__file__).resolve().parents[4] / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from mv_platform.application.service import (
    ApplicationBlocked,
    ApplicationService,
)
from mv_platform.config import Settings
from mv_platform.infrastructure import Database


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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
    """Write a workflow decision directly, bypassing gate validation."""
    decisions_path = root / "creative" / "workflow-decisions.json"
    decisions_path.parent.mkdir(parents=True, exist_ok=True)
    decisions = {}
    if decisions_path.exists():
        decisions = json.loads(decisions_path.read_text())
    decisions[stage] = {
        "action": action,
        "note": "test",
        "decided_at": datetime.now(timezone.utc).isoformat(),
        "actor": "local_user",
    }
    decisions_path.write_text(json.dumps(decisions, ensure_ascii=False))


def _setup_project_with_visual_score(tmp_path, slug, shots, story_sections=None):
    service = make_service(tmp_path)
    result = service.create_project(slug, {"title": "测试"})
    project_id = result.project_id
    root = _project_root(service, slug)

    _write_yaml(root / "creative" / "visual_score.yaml", {
        "shots": shots,
        "sections": [],
    })
    if story_sections is not None:
        _write_yaml(root / "creative" / "story_framework.yaml", {
            "sections": story_sections,
        })
    return service, project_id, root


# ---------------------------------------------------------------------------
# UT-010: suggest_scene_groups groups by section
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_suggest_scene_groups_groups_by_section():
    shots = [
        {"id": "S001", "section": "A"},
        {"id": "S002", "section": "A"},
        {"id": "S003", "section": "A"},
        {"id": "S004", "section": "B"},
        {"id": "S005", "section": "B"},
    ]
    story_sections = [
        {"id": "A", "emotion": "孤独"},
        {"id": "B", "emotion": "思念"},
    ]
    result = ApplicationService.suggest_scene_groups(shots, story_sections)

    assert len(result) == 2
    sg_a = next(sg for sg in result if sg.source_section_id == "A")
    sg_b = next(sg for sg in result if sg.source_section_id == "B")

    assert set(sg_a.shot_ids) == {"S001", "S002", "S003"}
    assert set(sg_b.shot_ids) == {"S004", "S005"}
    assert sg_a.name == "孤独"
    assert sg_b.name == "思念"


@pytest.mark.unit
def test_suggest_scene_groups_fallback_name_when_no_section_match():
    shots = [{"id": "S001", "section": "X"}]
    result = ApplicationService.suggest_scene_groups(shots, [])
    assert result[0].name == "场景1"


@pytest.mark.unit
def test_suggest_scene_groups_no_section_field_goes_to_default():
    shots = [{"id": "S001"}, {"id": "S002"}]
    result = ApplicationService.suggest_scene_groups(shots, [])
    assert len(result) == 1
    assert set(result[0].shot_ids) == {"S001", "S002"}


# ---------------------------------------------------------------------------
# UT-011: migration creates BackgroundMaster from existing background path
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_migration_creates_background_master_from_existing(tmp_path):
    shots = [{"id": "S001", "section": "A"}, {"id": "S002", "section": "A"}]
    service, project_id, root = _setup_project_with_visual_score(
        tmp_path, "migtest", shots
    )

    # Write v1 shot-references with a background already set
    _write_json(root / "creative" / "shot-references.json", {
        "version": 1,
        "shots": {
            "S001": {"background": "assets/generated/backgrounds/S001-bg.png"},
            "S002": {},
        },
    })

    # Approve story and storyboard directly (bypass gate checks)
    _write_decision(root, "story")
    _write_decision(root, "storyboard")

    # Trigger migration by calling get_project_workflow
    service.get_project_workflow(project_id)

    # background-masters.json must be created
    bg_path = root / "creative" / "background-masters.json"
    assert bg_path.exists(), "background-masters.json should be created"
    bg_doc = json.loads(bg_path.read_text())
    backgrounds = bg_doc["backgrounds"]
    assert len(backgrounds) == 1
    bg = backgrounds[0]
    assert bg["id"] == "BG001"
    assert bg["status"] == "selected"
    assert bg["source"] == "uploaded"
    assert bg["relative_path"] == "assets/generated/backgrounds/S001-bg.png"

    # shot-references.json must be upgraded to v2
    refs = json.loads((root / "creative" / "shot-references.json").read_text())
    assert refs["version"] == 2
    assert refs["shots"]["S001"].get("background_master_id") == "BG001"
    # Old background field preserved
    assert refs["shots"]["S001"].get("background") == "assets/generated/backgrounds/S001-bg.png"


# ---------------------------------------------------------------------------
# UT-012: migration silently skips when visual_score.yaml is absent
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_migration_skips_when_no_visual_score(tmp_path):
    service = make_service(tmp_path)
    result = service.create_project("novisual", {"title": "无分镜项目"})
    project_id = result.project_id
    root = _project_root(service, "novisual")

    _write_decision(root, "story")
    _write_decision(root, "storyboard")

    # Should not raise
    service.get_project_workflow(project_id)

    # No files should be created
    assert not (root / "creative" / "scene-groups.json").exists()
    assert not (root / "creative" / "background-masters.json").exists()


# ---------------------------------------------------------------------------
# UT-013: shot can only belong to one scene group (update moves it out)
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_shot_cannot_belong_to_two_groups(tmp_path):
    shots = [
        {"id": "S001", "section": "A"},
        {"id": "S002", "section": "A"},
        {"id": "S003", "section": "B"},
    ]
    service, project_id, root = _setup_project_with_visual_score(
        tmp_path, "moveshot", shots
    )
    _write_decision(root, "story")
    _write_decision(root, "storyboard")

    # Trigger migration to create SG001 (A: S001,S002) and SG002 (B: S003)
    service.get_project_workflow(project_id)

    # Move S001 and S003 to SG002 (S001 must leave SG001)
    service.update_scene_group(project_id, "SG002", shot_ids=["S001", "S003"])

    sg_doc = json.loads((root / "creative" / "scene-groups.json").read_text())
    groups = {g["id"]: g for g in sg_doc["scene_groups"]}

    assert "S001" not in groups["SG001"]["shot_ids"], "S001 must be removed from SG001"
    assert "S001" in groups["SG002"]["shot_ids"], "S001 must be in SG002"


# ---------------------------------------------------------------------------
# UT-014: selecting a background deselects the previous selected one
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_select_background_deselects_previous(tmp_path):
    shots = [{"id": "S001", "section": "A"}, {"id": "S002", "section": "A"}]
    service, project_id, root = _setup_project_with_visual_score(
        tmp_path, "selbgtest", shots
    )

    now = datetime.now(timezone.utc).isoformat()
    _write_json(root / "creative" / "scene-groups.json", {
        "version": 1,
        "generated_by": "test",
        "generated_at": now,
        "scene_groups": [
            {"id": "SG001", "name": "测试场景", "source_section_id": "A",
             "shot_ids": ["S001", "S002"], "location": "", "time_of_day": "",
             "weather": "", "emotional_state": "", "narrative_world_state": "",
             "created_by": "system", "created_at": now, "updated_at": now},
        ],
    })
    _write_json(root / "creative" / "background-masters.json", {
        "version": 1,
        "backgrounds": [
            {"id": "BG001", "scene_group_id": "SG001", "status": "selected",
             "source": "generated", "relative_path": "assets/bg1.png",
             "prompt_zh": "", "prompt_en": "", "model": "", "request_id": "",
             "cost_yuan": 0.5, "created_at": now},
            {"id": "BG002", "scene_group_id": "SG001", "status": "candidate",
             "source": "generated", "relative_path": "assets/bg2.png",
             "prompt_zh": "", "prompt_en": "", "model": "", "request_id": "",
             "cost_yuan": 0.5, "created_at": now},
        ],
    })

    service.select_background_master(project_id, "SG001", "BG002")

    bg_doc = json.loads((root / "creative" / "background-masters.json").read_text())
    bgs = {b["id"]: b for b in bg_doc["backgrounds"]}
    assert bgs["BG001"]["status"] == "candidate", "BG001 must be downgraded to candidate"
    assert bgs["BG002"]["status"] == "selected", "BG002 must be selected"


# ---------------------------------------------------------------------------
# UT-015: scenes approve blocked when a group has no selected background
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_scenes_approve_blocked_when_group_has_no_selected(tmp_path):
    shots = [{"id": "S001", "section": "A"}]
    service, project_id, root = _setup_project_with_visual_score(
        tmp_path, "noselappr", shots
    )

    now = datetime.now(timezone.utc).isoformat()
    _write_json(root / "creative" / "scene-groups.json", {
        "version": 1,
        "generated_by": "test",
        "generated_at": now,
        "scene_groups": [
            {"id": "SG001", "name": "无背景场景", "source_section_id": "A",
             "shot_ids": ["S001"], "location": "", "time_of_day": "",
             "weather": "", "emotional_state": "", "narrative_world_state": "",
             "created_by": "system", "created_at": now, "updated_at": now},
        ],
    })
    _write_json(root / "creative" / "background-masters.json", {
        "version": 1,
        "backgrounds": [],
    })

    _write_decision(root, "story")
    _write_decision(root, "storyboard")

    with pytest.raises((ApplicationBlocked, Exception)):
        service.record_workflow_decision(project_id, "scenes", "approve", "")
