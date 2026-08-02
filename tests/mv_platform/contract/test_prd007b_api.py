"""PRD-007B API contract tests: scene planning routes."""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest
import yaml

SOURCE_ROOT = Path(__file__).resolve().parents[4] / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from fastapi.testclient import TestClient
from apps.mv_api import create_app
from apps.runtime import build_service


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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


def _project_root(service, slug):
    return service.workspace_root / "projects" / slug


def _setup_storyboard_approved(service, slug):
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
    return project_id, root


def _setup_planning_approved(service, slug):
    project_id, root = _setup_storyboard_approved(service, slug)
    now = datetime.now(timezone.utc).isoformat()
    sp_data = {
        "version": 1, "status": "approved",
        "groups": [
            {
                "group_id": "SG001", "name": "书房-白天",
                "shots": ["S001", "S002"], "prompt_zh": "书房阳光",
                "notes": "", "locked": False,
                "created_at": now, "updated_at": now,
            }
        ],
        "llm_suggestion_used": True,
    }
    _write_json(root / "creative" / "scene-planning.json", sp_data)
    sg_doc = {
        "version": 1, "generated_by": "scene_planning", "generated_at": now,
        "scene_groups": [
            {
                "id": "SG001", "name": "书房-白天",
                "source_section_id": "", "shot_ids": ["S001", "S002"],
                "location": "", "time_of_day": "", "weather": "",
                "emotional_state": "", "narrative_world_state": "",
                "created_by": "user", "created_at": now, "updated_at": now,
            }
        ],
    }
    _write_json(root / "creative" / "scene-groups.json", sg_doc)
    return project_id, root


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def service(tmp_path):
    return build_service(tmp_path, with_supervisor=False)


@pytest.fixture
def client(service):
    return TestClient(create_app(service=service))


# ---------------------------------------------------------------------------
# CT-080: GET /api/v1/projects/{project_id}/scene-planning → not_started
# ---------------------------------------------------------------------------

@pytest.mark.contract
def test_get_scene_planning_not_started(client, service, tmp_path):
    result = service.create_project("ct080", {"title": "测试"})
    project_id = result.project_id
    resp = client.get(f"/api/v1/projects/{project_id}/scene-planning")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "not_started"
    assert data["groups"] == []


# ---------------------------------------------------------------------------
# CT-081: PUT /api/v1/projects/{project_id}/scene-planning → update_groups
# ---------------------------------------------------------------------------

@pytest.mark.contract
def test_update_scene_planning_update_groups(client, service, tmp_path):
    project_id, root = _setup_storyboard_approved(service, "ct081")
    resp = client.put(
        f"/api/v1/projects/{project_id}/scene-planning",
        json={
            "action": "update_groups",
            "groups": [
                {"group_id": "SG001", "name": "书房", "shots": ["S001", "S002"], "prompt_zh": "书房"},
            ],
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["groups"]) == 1
    assert data["groups"][0]["group_id"] == "SG001"


# ---------------------------------------------------------------------------
# CT-082: POST /api/v1/projects/{project_id}/scene-planning/approve
# ---------------------------------------------------------------------------

@pytest.mark.contract
def test_approve_scene_planning(client, service, tmp_path):
    project_id, root = _setup_storyboard_approved(service, "ct082")
    # Create planning first
    client.put(
        f"/api/v1/projects/{project_id}/scene-planning",
        json={
            "action": "update_groups",
            "groups": [
                {"group_id": "SG001", "name": "书房", "shots": ["S001", "S002"], "prompt_zh": "书房"},
            ],
        },
    )
    resp = client.post(f"/api/v1/projects/{project_id}/scene-planning/approve")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "approved"
    assert data["groups"] == 1


# ---------------------------------------------------------------------------
# CT-083: POST /api/v1/projects/{project_id}/groups/{group_id}/background/select
# ---------------------------------------------------------------------------

@pytest.mark.contract
def test_select_group_background_master(client, service, tmp_path):
    project_id, root = _setup_planning_approved(service, "ct083")
    now = datetime.now(timezone.utc).isoformat()
    bg_doc = {
        "version": 1,
        "backgrounds": [
            {
                "id": "BG001", "scene_group_id": "SG001",
                "status": "candidate", "source": "generated",
                "relative_path": "bg001.png",
                "prompt_zh": "", "prompt_en": "", "model": "",
                "request_id": "", "cost_yuan": 0.5, "created_at": now,
            }
        ],
    }
    _write_json(root / "creative" / "background-masters.json", bg_doc)
    resp = client.post(
        f"/api/v1/projects/{project_id}/groups/SG001/background/select",
        json={"candidate_id": "BG001"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["master_id"] == "BG001"
    assert set(data["shots_updated"]) == {"S001", "S002"}


# ---------------------------------------------------------------------------
# CT-084: PUT /api/v1/projects/{project_id}/shots/{shot_id}/background-override
# ---------------------------------------------------------------------------

@pytest.mark.contract
def test_set_shot_background_override(client, service, tmp_path):
    project_id, root = _setup_planning_approved(service, "ct084")
    resp = client.put(
        f"/api/v1/projects/{project_id}/shots/S001/background-override",
        json={"override_path": "backgrounds/custom.png"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["shot_id"] == "S001"
    assert data["background_override"] == "backgrounds/custom.png"
    # Clear override
    resp2 = client.put(
        f"/api/v1/projects/{project_id}/shots/S001/background-override",
        json={"override_path": None},
    )
    assert resp2.status_code == 200
    assert resp2.json()["background_override"] is None
