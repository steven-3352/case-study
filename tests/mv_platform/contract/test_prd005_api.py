"""PRD-005 API contract tests: async background/keyframe generation, SSE events endpoint."""
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


def _make_project_no_approval(client, slug="ct040na"):
    """Create project with no approvals at all."""
    resp = client.post("/api/v1/projects", json={
        "slug": slug,
        "brief": {"title": "CT005无批准", "canvas": "9:16", "target_platforms": ["douyin"]},
    })
    assert resp.status_code == 200
    return resp.json()["project_id"]


def _make_project_background_ready(client, service_obj, slug="ct041bg"):
    """Create project with story+storyboard approved and scene_groups for S001."""
    resp = client.post("/api/v1/projects", json={
        "slug": slug,
        "brief": {"title": "CT005背景就绪", "canvas": "9:16", "target_platforms": ["douyin"]},
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
    return project_id, root


def _make_project_keyframe_ready(client, service_obj, slug="ct043kf"):
    """Create project with scenes approved and S001 background_master_id set."""
    resp = client.post("/api/v1/projects", json={
        "slug": slug,
        "brief": {"title": "CT005首帧就绪", "canvas": "9:16", "target_platforms": ["douyin"]},
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
    return project_id, root


# ---------------------------------------------------------------------------
# CT-040: no story approval → 423 on background/generate
# ---------------------------------------------------------------------------

@pytest.mark.contract
def test_background_generate_without_approval_returns_423(client):
    """CT-040: POST /background/generate without story approval returns 423."""
    project_id = _make_project_no_approval(client, "ct040na")
    resp = client.post(
        f"/api/v1/projects/{project_id}/shots/S001/background/generate",
    )
    assert resp.status_code == 423


# ---------------------------------------------------------------------------
# CT-041: story approved + scene_groups → 202 + X-Async + job_id
# ---------------------------------------------------------------------------

@pytest.mark.contract
def test_background_generate_returns_202_with_job_id(client, service):
    """CT-041: POST /background/generate with valid project returns 202, X-Async, job_id."""
    project_id, _ = _make_project_background_ready(client, service, "ct041bg")
    resp = client.post(
        f"/api/v1/projects/{project_id}/shots/S001/background/generate",
    )
    assert resp.status_code == 202
    assert resp.headers.get("X-Async") == "true"
    assert resp.headers.get("X-Deprecated", "") != ""
    data = resp.json()
    assert "job_id" in data
    assert data["job_id"]
    assert data["status"] == "queued"


# ---------------------------------------------------------------------------
# CT-042: no scenes approval → 423 on keyframes/generate
# ---------------------------------------------------------------------------

@pytest.mark.contract
def test_keyframe_generate_without_scenes_approval_returns_423(client, service):
    """CT-042: POST /keyframes/generate without scenes approval returns 423."""
    project_id, _ = _make_project_background_ready(client, service, "ct042na")
    resp = client.post(
        f"/api/v1/projects/{project_id}/shots/S001/keyframes/generate",
    )
    assert resp.status_code == 423


# ---------------------------------------------------------------------------
# CT-043: scenes approved → 202 + job_id + events readable via SSE endpoint
# ---------------------------------------------------------------------------

@pytest.mark.contract
def test_keyframe_generate_returns_202_and_events_readable(client, service, monkeypatch):
    """CT-043: POST /keyframes/generate returns 202; GET /jobs/{job_id}/events returns events after sync run."""
    project_id, _ = _make_project_keyframe_ready(client, service, "ct043kf")
    monkeypatch.setattr(service, "_translate_prompt", lambda *a, **kw: "translated")
    monkeypatch.setattr(service, "generate_shot_keyframe", lambda pid, sid, **kw: None)

    resp = client.post(
        f"/api/v1/projects/{project_id}/shots/S001/keyframes/generate",
    )
    assert resp.status_code == 202
    job_id = resp.json()["job_id"]
    assert job_id

    service._run_pending_jobs_sync()

    events_resp = client.get(f"/api/v1/jobs/{job_id}/events")
    assert events_resp.status_code == 200
    raw = events_resp.text
    assert "event: progress" in raw
    assert "event: done" in raw
