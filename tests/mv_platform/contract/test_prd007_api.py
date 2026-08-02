"""PRD-007 API contract tests: en_prompt optional body for background/keyframe generate."""
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
        c = struct.pack(">I", len(data)) + name + data
        return c + struct.pack(">I", zlib.crc32(name + data) & 0xFFFFFFFF)
    header = b"\x89PNG\r\n\x1a\n"
    ihdr = chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
    idat = chunk(b"IDAT", zlib.compress(b"\x00\xff\xff\xff"))
    iend = chunk(b"IEND", b"")
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


def _make_background_ready_project(client, service_obj, slug="ct071bg"):
    resp = client.post("/api/v1/projects", json={
        "slug": slug,
        "brief": {"title": "CT007背景就绪", "canvas": "9:16", "target_platforms": ["douyin"]},
    })
    assert resp.status_code == 200
    project_id = resp.json()["project_id"]
    root = service_obj.workspace_root / "projects" / slug
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
    return project_id


def _make_keyframe_ready_project(client, service_obj, slug="ct073kf"):
    resp = client.post("/api/v1/projects", json={
        "slug": slug,
        "brief": {"title": "CT007首帧就绪", "canvas": "9:16", "target_platforms": ["douyin"]},
    })
    assert resp.status_code == 200
    project_id = resp.json()["project_id"]
    root = service_obj.workspace_root / "projects" / slug
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
    return project_id


# ---------------------------------------------------------------------------
# CT-071: POST background/generate with en_prompt → 202 + job_id
# ---------------------------------------------------------------------------

@pytest.mark.contract
def test_background_generate_with_en_prompt_returns_202(client, service):
    """CT-071: POST background/generate body {en_prompt} returns 202 with job_id."""
    project_id = _make_background_ready_project(client, service, "ct071")
    resp = client.post(
        f"/api/v1/projects/{project_id}/shots/S001/background/generate",
        json={"en_prompt": "blue sky at dusk"},
    )
    assert resp.status_code == 202
    assert "job_id" in resp.json()
    assert resp.json()["job_id"]


# ---------------------------------------------------------------------------
# CT-072: POST background/generate without en_prompt → still 202
# ---------------------------------------------------------------------------

@pytest.mark.contract
def test_background_generate_without_en_prompt_returns_202(client, service):
    """CT-072: POST background/generate with no body returns 202 with job_id."""
    project_id = _make_background_ready_project(client, service, "ct072")
    resp = client.post(
        f"/api/v1/projects/{project_id}/shots/S001/background/generate",
    )
    assert resp.status_code == 202
    assert "job_id" in resp.json()


# ---------------------------------------------------------------------------
# CT-073: POST keyframes/generate with en_prompt → 202 + job_id
# ---------------------------------------------------------------------------

@pytest.mark.contract
def test_keyframe_generate_with_en_prompt_returns_202(client, service):
    """CT-073: POST keyframes/generate body {en_prompt} returns 202 with job_id."""
    project_id = _make_keyframe_ready_project(client, service, "ct073")
    resp = client.post(
        f"/api/v1/projects/{project_id}/shots/S001/keyframes/generate",
        json={"en_prompt": "close-up portrait in warm light"},
    )
    assert resp.status_code == 202
    assert "job_id" in resp.json()


# ---------------------------------------------------------------------------
# CT-074: en_prompt=null behaves same as absent
# ---------------------------------------------------------------------------

@pytest.mark.contract
def test_background_generate_null_en_prompt_behaves_same_as_absent(client, service):
    """CT-074: en_prompt=null is treated as absent (no bypass, still 202)."""
    project_id = _make_background_ready_project(client, service, "ct074")
    resp = client.post(
        f"/api/v1/projects/{project_id}/shots/S001/background/generate",
        json={"en_prompt": None},
    )
    assert resp.status_code == 202
    assert "job_id" in resp.json()
