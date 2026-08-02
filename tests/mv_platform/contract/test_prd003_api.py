"""PRD-003 API contract tests: keyframe metadata, preconditions, workflow entries."""
import io
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

from fastapi.testclient import TestClient
from apps.mv_api import create_app
from apps.runtime import build_service


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


def _make_project_storyboard_approved(client, service_obj):
    """Create project with story + storyboard approved, no scenes approval."""
    resp = client.post("/api/v1/projects", json={
        "slug": "ct003stb",
        "brief": {"title": "CT003测试", "canvas": "9:16", "target_platforms": ["douyin"]},
    })
    assert resp.status_code == 200
    project_id = resp.json()["project_id"]
    root = service_obj.workspace_root / "projects" / "ct003stb"

    _write_yaml(root / "creative" / "visual_score.yaml", {
        "shots": [{"id": "S001", "section": "A"}], "sections": [],
    })
    _write_decision(root, "story")
    _write_decision(root, "storyboard")
    return project_id, root


def _make_project_scenes_approved(client, service_obj):
    """Create project with scenes approved and shot S001 with background_master_id."""
    resp = client.post("/api/v1/projects", json={
        "slug": "ct003sc",
        "brief": {"title": "CT003场景测试", "canvas": "9:16", "target_platforms": ["douyin"]},
    })
    assert resp.status_code == 200
    project_id = resp.json()["project_id"]
    root = service_obj.workspace_root / "projects" / "ct003sc"
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
        "shots": {"S001": {"background": "assets/generated/backgrounds/S001-bg.png",
                           "background_master_id": "BG001"}},
    })
    _write_decision(root, "story")
    _write_decision(root, "storyboard")
    _write_decision(root, "scenes")
    return project_id, root


# ---------------------------------------------------------------------------
# CT-020: keyframe generate without scenes approval returns 423
# ---------------------------------------------------------------------------

@pytest.mark.contract
def test_keyframe_generate_without_scenes_approval_returns_423(client, service, tmp_path):
    project_id, _ = _make_project_storyboard_approved(client, service)
    resp = client.post(f"/api/v1/projects/{project_id}/shots/S001/keyframes/generate")
    assert resp.status_code == 423
    data = resp.json()
    assert data.get("error_stage") == "precondition"


# ---------------------------------------------------------------------------
# CT-021: workflow keyframe_entries have source field
# ---------------------------------------------------------------------------

@pytest.mark.contract
def test_workflow_keyframe_entries_have_source(client, service, tmp_path):
    project_id, root = _make_project_scenes_approved(client, service)
    now = datetime.now(timezone.utc).isoformat()

    kf_path = "assets/generated/keyframes/S001-abc.png"
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
                    {"path": kf_path, "source": "generated", "background_master_id": "BG001",
                     "character_ids": [], "prompt_zh": "", "prompt_en": "test",
                     "model": "gpt-image-2", "request_id": "req-001",
                     "cost_yuan": 0.5, "created_at": now},
                ],
                "selected_keyframe": kf_path,
            }
        },
    })

    resp = client.get(f"/api/v1/projects/{project_id}/workflow")
    assert resp.status_code == 200
    stages = resp.json()["stages"]
    kf_stage = next(s for s in stages if s["id"] == "keyframes")
    shots = kf_stage["data"]["shots"]
    assert len(shots) > 0
    entries = shots[0]["keyframe_entries"]
    assert len(entries) == 1
    assert entries[0]["source"] in ("generated", "uploaded", "legacy")


# ---------------------------------------------------------------------------
# CT-022: upload keyframe appears in workflow keyframe_entries
# ---------------------------------------------------------------------------

@pytest.mark.contract
def test_upload_keyframe_appears_in_workflow(client, service, tmp_path):
    project_id, root = _make_project_scenes_approved(client, service)

    resp = client.post(
        f"/api/v1/projects/{project_id}/shots/S001/keyframes",
        content=TINY_PNG,
        params={"filename": "frame.png"},
        headers={"Content-Type": "image/png"},
    )
    assert resp.status_code == 200

    stages = resp.json()["stages"]
    kf_stage = next(s for s in stages if s["id"] == "keyframes")
    shots = kf_stage["data"]["shots"]
    assert any(e["source"] == "uploaded" for e in shots[0]["keyframe_entries"]), \
        "uploaded keyframe must appear in keyframe_entries with source='uploaded'"
