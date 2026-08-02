"""PRD-002 API contract tests: scene groups, background masters, workflow stages."""
import json
import sys
from pathlib import Path
from datetime import datetime, timezone

import pytest
import yaml

SOURCE_ROOT = Path(__file__).resolve().parents[4] / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from fastapi.testclient import TestClient
from apps.mv_api import create_app
from apps.runtime import build_service


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def service(tmp_path):
    return build_service(tmp_path, with_supervisor=False)


@pytest.fixture
def client(service):
    return TestClient(create_app(service=service))


def _write_yaml(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True)


def _write_json(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _write_decision(root: Path, stage: str, action: str = "approve"):
    """Write a workflow decision directly to bypass gate validation."""
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


def _make_project_with_storyboard(client, service_obj, tmp_path_for_service):
    """Create a project, write visual_score.yaml, approve story + storyboard."""
    resp = client.post("/api/v1/projects", json={
        "slug": "ct002test",
        "brief": {"title": "契约测试项目", "canvas": "9:16", "target_platforms": ["douyin"]},
    })
    assert resp.status_code == 200
    project_id = resp.json()["project_id"]

    # Locate project root: service uses workspace_root / "projects" / slug
    root = service_obj.workspace_root / "projects" / "ct002test"
    _write_yaml(root / "creative" / "visual_score.yaml", {
        "shots": [
            {"id": "S001", "section": "A", "lyric": {"text": "歌词1"}},
            {"id": "S002", "section": "A", "lyric": {"text": "歌词2"}},
            {"id": "S003", "section": "B", "lyric": {"text": "歌词3"}},
        ],
    })
    _write_yaml(root / "creative" / "story_framework.yaml", {
        "sections": [
            {"id": "A", "emotion": "孤独"},
            {"id": "B", "emotion": "释然"},
        ],
    })
    _write_decision(root, "story")
    _write_decision(root, "storyboard")
    return project_id, root


# ---------------------------------------------------------------------------
# CT-013: workflow stages include 'scenes' between storyboard and keyframes
# ---------------------------------------------------------------------------

@pytest.mark.contract
def test_workflow_has_scenes_stage_between_storyboard_and_keyframes(client, service, tmp_path):
    project_id, _ = _make_project_with_storyboard(client, service, tmp_path)
    resp = client.get(f"/api/v1/projects/{project_id}/workflow")
    assert resp.status_code == 200
    stage_ids = [s["id"] for s in resp.json()["stages"]]

    assert "scenes" in stage_ids
    # PRD-007B: scene_planning stage sits between storyboard and scenes
    assert "scene_planning" in stage_ids
    assert stage_ids.index("scene_planning") == stage_ids.index("storyboard") + 1
    assert stage_ids.index("scenes") == stage_ids.index("scene_planning") + 1
    assert stage_ids.index("keyframes") == stage_ids.index("scenes") + 1


# ---------------------------------------------------------------------------
# CT-010: POST suggest returns scene groups in workflow
# ---------------------------------------------------------------------------

@pytest.mark.contract
def test_suggest_scene_groups_returns_groups(client, service, tmp_path):
    project_id, _ = _make_project_with_storyboard(client, service, tmp_path)

    resp = client.post(f"/api/v1/projects/{project_id}/scene-groups/suggest")
    assert resp.status_code == 200

    data = resp.json()
    scenes_stage = next((s for s in data["stages"] if s["id"] == "scenes"), None)
    assert scenes_stage is not None
    groups = scenes_stage["data"]["scene_groups"]
    assert len(groups) > 0
    assert any(g.get("id", "").startswith("SG") for g in groups)


# ---------------------------------------------------------------------------
# CT-011: PUT scene-groups/{sg_id} updates name
# ---------------------------------------------------------------------------

@pytest.mark.contract
def test_update_scene_group_name(client, service, tmp_path):
    project_id, _ = _make_project_with_storyboard(client, service, tmp_path)

    # Trigger migration to get SG ids
    wf = client.get(f"/api/v1/projects/{project_id}/workflow").json()
    scenes = next(s for s in wf["stages"] if s["id"] == "scenes")
    sg_id = scenes["data"]["scene_groups"][0]["id"]

    resp = client.put(
        f"/api/v1/projects/{project_id}/scene-groups/{sg_id}",
        json={"name": "新场景名称"},
    )
    assert resp.status_code == 200

    updated = next(
        s for s in resp.json()["stages"] if s["id"] == "scenes"
    )
    updated_sg = next(g for g in updated["data"]["scene_groups"] if g["id"] == sg_id)
    assert updated_sg["name"] == "新场景名称"


# ---------------------------------------------------------------------------
# CT-012: old background/generate route returns X-Deprecated header
# ---------------------------------------------------------------------------

@pytest.mark.contract
def test_old_background_generate_returns_deprecated_header(client, service, tmp_path):
    project_id, _ = _make_project_with_storyboard(client, service, tmp_path)

    # Trigger migration
    client.get(f"/api/v1/projects/{project_id}/workflow")

    resp = client.post(
        f"/api/v1/projects/{project_id}/shots/S001/background/generate"
    )
    # The route should return 423 (no provider configured) but must include deprecated header
    assert "x-deprecated" in resp.headers or "X-Deprecated" in resp.headers
