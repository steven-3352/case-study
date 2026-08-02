"""PRD-007B unit tests: scene group planning, LLM suggest, approve, override."""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest
import yaml

SOURCE_ROOT = Path(__file__).resolve().parents[4] / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from mv_platform.application.service import ApplicationBlocked, ApplicationService
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


def _write_decision(root: Path, stage: str, action: str = "approve"):
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


def _setup_storyboard_approved(tmp_path, slug):
    """Project with 2 shots (S001, S002) and storyboard approved."""
    service = make_service(tmp_path)
    result = service.create_project(slug, {"title": "测试"})
    project_id = result.project_id
    root = _project_root(service, slug)

    _write_yaml(root / "creative" / "visual_score.yaml", {
        "shots": [
            {"id": "S001", "section": "A", "purpose": "intro"},
            {"id": "S002", "section": "A", "purpose": "bridge"},
        ],
        "sections": [{"id": "A", "emotion": "孤独"}],
    })
    _write_decision(root, "story")
    _write_decision(root, "storyboard")
    return service, project_id, root


def _setup_planning_approved(tmp_path, slug):
    """Project with storyboard approved + scene planning approved (SG001: S001+S002)."""
    service, project_id, root = _setup_storyboard_approved(tmp_path, slug)

    sp_data = {
        "version": 1, "status": "approved",
        "groups": [
            {
                "group_id": "SG001", "name": "书房-白天",
                "shots": ["S001", "S002"], "prompt_zh": "书房阳光",
                "notes": "", "locked": False,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
        ],
        "llm_suggestion_used": True,
    }
    _write_json(root / "creative" / "scene-planning.json", sp_data)

    # Write scene-groups.json to mirror planning
    sg_doc = {
        "version": 1, "generated_by": "scene_planning",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scene_groups": [
            {
                "id": "SG001", "name": "书房-白天",
                "source_section_id": "", "shot_ids": ["S001", "S002"],
                "location": "", "time_of_day": "", "weather": "",
                "emotional_state": "", "narrative_world_state": "",
                "created_by": "user",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
        ],
    }
    _write_json(root / "creative" / "scene-groups.json", sg_doc)
    return service, project_id, root


def _setup_with_master(tmp_path, slug):
    """Planning approved + BG001 selected for SG001."""
    service, project_id, root = _setup_planning_approved(tmp_path, slug)

    bg_doc = {
        "version": 1,
        "backgrounds": [
            {
                "id": "BG001", "scene_group_id": "SG001",
                "status": "selected", "source": "generated",
                "relative_path": "backgrounds/bg001.png",
                "prompt_zh": "", "prompt_en": "", "model": "",
                "request_id": "", "cost_yuan": 0.5,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        ],
    }
    _write_json(root / "creative" / "background-masters.json", bg_doc)

    refs = {
        "version": 1,
        "shots": {
            "S001": {"background_master_id": "BG001", "background_override": None, "scene_group_id": "SG001"},
            "S002": {"background_master_id": "BG001", "background_override": None, "scene_group_id": "SG001"},
        },
    }
    _write_json(root / "creative" / "shot-references.json", refs)
    return service, project_id, root


# ---------------------------------------------------------------------------
# Fake LLM client
# ---------------------------------------------------------------------------

class FakeLLMClient:
    def __init__(self, groups):
        self._groups = groups

    def run(self, task):
        from dataclasses import dataclass
        @dataclass
        class _R:
            output: dict
            input_tokens: int = 0
            output_tokens: int = 0
            cache_read_tokens: int = 0
        return _R(output={"groups": self._groups})


# ---------------------------------------------------------------------------
# UT-080: suggest_scene_groups_llm returns groups
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_suggest_scene_groups_returns_groups(tmp_path, monkeypatch):
    service, project_id, root = _setup_storyboard_approved(tmp_path, "ut080")
    monkeypatch.setattr(
        service, "semantic_port",
        FakeLLMClient([{"group_name": "书房-白天", "shots": ["S001", "S002"], "prompt_zh": "书房阳光"}]),
    )
    monkeypatch.setattr(service, "semantic_model", "test-model")
    result = service.suggest_scene_groups_llm(project_id)
    assert "groups" in result
    assert len(result["groups"]) >= 1
    grp = result["groups"][0]
    assert grp["shots"] == ["S001", "S002"]
    assert grp["group_id"] == "SG001"
    assert grp["prompt_zh"] == "书房阳光"
    # scene-planning.json must exist with status=draft
    sp = json.loads((root / "creative" / "scene-planning.json").read_text())
    assert sp["status"] == "draft"
    assert sp["llm_suggestion_used"] is True


# ---------------------------------------------------------------------------
# UT-081: approve fails if uncategorized shots exist
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_approve_fails_if_uncategorized_shots_exist(tmp_path):
    service, project_id, root = _setup_storyboard_approved(tmp_path, "ut081")
    # Only assign S001, leaving S002 uncategorized
    service.update_scene_planning(project_id, {
        "action": "update_groups",
        "groups": [{"group_id": "SG001", "name": "书房", "shots": ["S001"], "prompt_zh": "书房"}],
    })
    with pytest.raises(ApplicationBlocked, match="uncategorized"):
        service.approve_scene_planning(project_id)


# ---------------------------------------------------------------------------
# UT-082: approve_scene_planning sets stage to approved
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_approve_scene_planning_sets_stage_approved(tmp_path):
    service, project_id, root = _setup_storyboard_approved(tmp_path, "ut082")
    # Create planning covering all shots
    service.update_scene_planning(project_id, {
        "action": "update_groups",
        "groups": [
            {"group_id": "SG001", "name": "书房", "shots": ["S001", "S002"], "prompt_zh": "书房"},
        ],
    })
    result = service.approve_scene_planning(project_id)
    assert result["status"] == "approved"
    assert result["groups"] == 1
    assert result["shots_assigned"] == 2
    sp = json.loads((root / "creative" / "scene-planning.json").read_text())
    assert sp["status"] == "approved"
    # scene-groups.json should be updated
    sg = json.loads((root / "creative" / "scene-groups.json").read_text())
    assert len(sg["scene_groups"]) == 1
    assert sg["scene_groups"][0]["id"] == "SG001"
    # shot-references.json should have scene_group_id set
    refs = json.loads((root / "creative" / "shot-references.json").read_text())
    assert refs["shots"]["S001"]["scene_group_id"] == "SG001"
    assert refs["shots"]["S002"]["scene_group_id"] == "SG001"


# ---------------------------------------------------------------------------
# UT-083: select_background_master auto-updates shots
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_select_background_master_auto_updates_shots(tmp_path):
    service, project_id, root = _setup_planning_approved(tmp_path, "ut083")
    # Add two background candidates for SG001
    now = datetime.now(timezone.utc).isoformat()
    bg_doc = {
        "version": 1,
        "backgrounds": [
            {"id": "BG001", "scene_group_id": "SG001", "status": "candidate",
             "source": "generated", "relative_path": "bg001.png",
             "prompt_zh": "", "prompt_en": "", "model": "",
             "request_id": "", "cost_yuan": 0.5, "created_at": now},
            {"id": "BG002", "scene_group_id": "SG001", "status": "candidate",
             "source": "generated", "relative_path": "bg002.png",
             "prompt_zh": "", "prompt_en": "", "model": "",
             "request_id": "", "cost_yuan": 0.5, "created_at": now},
        ],
    }
    _write_json(root / "creative" / "background-masters.json", bg_doc)

    result = service.select_background_master(project_id, "SG001", "BG001")
    assert result["master_id"] == "BG001"
    assert set(result["shots_updated"]) == {"S001", "S002"}
    # Verify shot-references.json updated
    refs = json.loads((root / "creative" / "shot-references.json").read_text())
    assert refs["shots"]["S001"]["background_master_id"] == "BG001"
    assert refs["shots"]["S002"]["background_master_id"] == "BG001"
    # BG001 should be selected, BG002 should remain candidate
    bg_updated = json.loads((root / "creative" / "background-masters.json").read_text())
    statuses = {b["id"]: b["status"] for b in bg_updated["backgrounds"]}
    assert statuses["BG001"] == "selected"
    assert statuses["BG002"] == "candidate"


# ---------------------------------------------------------------------------
# UT-084: set_shot_background_override sets override
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_set_shot_background_override_sets_value(tmp_path):
    service, project_id, root = _setup_with_master(tmp_path, "ut084")
    result = service.set_shot_background_override(project_id, "S001", "backgrounds/custom.png")
    assert result["shot_id"] == "S001"
    assert result["background_override"] == "backgrounds/custom.png"
    refs = json.loads((root / "creative" / "shot-references.json").read_text())
    assert refs["shots"]["S001"]["background_override"] == "backgrounds/custom.png"


# ---------------------------------------------------------------------------
# UT-085: set_shot_background_override clears override when None
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_set_shot_background_override_clears_value(tmp_path):
    service, project_id, root = _setup_with_master(tmp_path, "ut085")
    # First set an override
    service.set_shot_background_override(project_id, "S001", "backgrounds/custom.png")
    # Then clear it
    result = service.set_shot_background_override(project_id, "S001", None)
    assert result["background_override"] is None
    refs = json.loads((root / "creative" / "shot-references.json").read_text())
    assert refs["shots"]["S001"]["background_override"] is None


# ---------------------------------------------------------------------------
# UT-086: get_scene_planning returns not_started when no file
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_get_scene_planning_returns_not_started_initially(tmp_path):
    service, project_id, root = _setup_storyboard_approved(tmp_path, "ut086")
    result = service.get_scene_planning(project_id)
    assert result["status"] == "not_started"
    assert result["groups"] == []
