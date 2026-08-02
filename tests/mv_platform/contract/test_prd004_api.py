"""PRD-004 API contract tests: video generation preconditions, ping, workflow."""
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


def _make_mp4_bytes(duration_seconds: float = 5.0) -> bytes:
    timescale = 1000
    duration_units = int(duration_seconds * timescale)
    mvhd_content = (
        b"\x00" + b"\x00\x00\x00"
        + b"\x00\x00\x00\x00" + b"\x00\x00\x00\x00"
        + timescale.to_bytes(4, "big")
        + duration_units.to_bytes(4, "big")
        + b"\x00" * 76
    )
    def box(name: bytes, content: bytes) -> bytes:
        return (8 + len(content)).to_bytes(4, "big") + name + content
    ftyp_content = b"isom" + b"\x00\x00\x02\x00" + b"isom" + b"iso2" + b"avc1" + b"mp41"
    ftyp_box = box(b"ftyp", ftyp_content)
    moov_box = box(b"moov", box(b"mvhd", mvhd_content))
    padding = b"\x00" * (110_000 - len(ftyp_box) - len(moov_box) - 8)
    mdat_box = box(b"mdat", padding)
    return ftyp_box + moov_box + mdat_box


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


def _make_project_scenes_approved(client, service_obj, slug="ct004sc"):
    """Create project with scenes approved and shot S001 with selected_keyframe."""
    resp = client.post("/api/v1/projects", json={
        "slug": slug,
        "brief": {"title": "CT004测试", "canvas": "9:16", "target_platforms": ["douyin"]},
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
                "keyframes": [{"path": kf_path, "source": "generated", "background_master_id": "BG001",
                               "character_ids": [], "prompt_zh": "", "prompt_en": "",
                               "model": "", "request_id": "", "cost_yuan": 0.0, "created_at": now}],
                "selected_keyframe": kf_path,
            }
        },
    })
    _write_decision(root, "story")
    _write_decision(root, "storyboard")
    _write_decision(root, "scenes")
    return project_id, root


def _make_project_scenes_no_keyframe(client, service_obj):
    """Create project with scenes approved but no selected_keyframe."""
    resp = client.post("/api/v1/projects", json={
        "slug": "ct004nokf",
        "brief": {"title": "CT004无首帧", "canvas": "9:16", "target_platforms": ["douyin"]},
    })
    assert resp.status_code == 200
    project_id = resp.json()["project_id"]
    root = service_obj.workspace_root / "projects" / "ct004nokf"
    now = datetime.now(timezone.utc).isoformat()

    _write_yaml(root / "creative" / "visual_score.yaml", {
        "shots": [{"id": "S001", "section": "A"}], "sections": [],
    })
    _write_json(root / "creative" / "shot-references.json", {
        "version": 2,
        "shots": {"S001": {"background": "assets/generated/backgrounds/S001-bg.png",
                           "background_master_id": "BG001"}},
    })
    _write_decision(root, "story")
    _write_decision(root, "storyboard")
    _write_decision(root, "scenes")
    return project_id, root


class _MockVideoProvider:
    def generate(self, task):
        from dataclasses import dataclass
        @dataclass
        class _R:
            video_bytes: bytes
            video_sha256: str = "sha256:" + "0"*64
            provider: str = "mock"
            model: str = "mock"
            task_id: str = "mock-task"
            request_contract_sha256: str = "sha256:" + "0"*64
            first_frame_sha256: str = "sha256:" + "0"*64
            reference_frame_sha256s: tuple = ()
        return _R(video_bytes=_make_mp4_bytes(float(task.duration_seconds)))


# ---------------------------------------------------------------------------
# CT-030: no selected_keyframe → 423
# ---------------------------------------------------------------------------

@pytest.mark.contract
def test_video_generate_without_keyframe_returns_423(client, service, monkeypatch):
    """CT-030: POST /video/generate without selected_keyframe returns 423."""
    monkeypatch.setenv("SEEDANCE_BASE_URL", "http://fake.example.com")
    project_id, _ = _make_project_scenes_no_keyframe(client, service)
    resp = client.post(
        f"/api/v1/projects/{project_id}/shots/S001/video/generate",
        json={"duration": 5},
    )
    assert resp.status_code == 423
    data = resp.json()
    assert data.get("error_stage") == "precondition"


# ---------------------------------------------------------------------------
# CT-031: no SEEDANCE_BASE_URL → ping reachable=false
# ---------------------------------------------------------------------------

@pytest.mark.contract
def test_ping_unreachable_without_config(client, monkeypatch):
    """CT-031: POST /settings/video-provider/ping without config returns reachable=false."""
    monkeypatch.delenv("SEEDANCE_BASE_URL", raising=False)
    resp = client.post("/api/v1/settings/video-provider/ping")
    assert resp.status_code == 200
    data = resp.json()
    assert data["reachable"] is False
    assert data["provider"] == "seedance"


# ---------------------------------------------------------------------------
# CT-032: video generate with mock provider → 202 + workflow
# ---------------------------------------------------------------------------

@pytest.mark.contract
def test_video_generate_returns_202_with_workflow(client, service, monkeypatch):
    """CT-032: POST /video/generate with mock provider returns 202 and updated workflow."""
    monkeypatch.setenv("SEEDANCE_BASE_URL", "http://fake.example.com")
    monkeypatch.setenv("SEEDANCE_MODEL", "seedance-2.0-mock")
    project_id, root = _make_project_scenes_approved(client, service)
    service.video_provider = _MockVideoProvider()

    resp = client.post(
        f"/api/v1/projects/{project_id}/shots/S001/video/generate",
        json={"duration": 5},
    )
    assert resp.status_code == 202
    wf = resp.json()
    shots_stage = next(s for s in wf["stages"] if s["id"] == "shots")
    shots = shots_stage["data"]["shots"]
    assert len(shots) > 0
    assert len(shots[0]["video_entries"]) == 1
    assert shots[0]["video_entries"][0]["cost_yuan"] == 4.0


# ---------------------------------------------------------------------------
# CT-033: select video updates workflow
# ---------------------------------------------------------------------------

@pytest.mark.contract
def test_select_video_updates_workflow(client, service, monkeypatch):
    """CT-033: PUT /videos/selection sets selected_video in workflow."""
    monkeypatch.setenv("SEEDANCE_BASE_URL", "http://fake.example.com")
    project_id, root = _make_project_scenes_approved(client, service, slug="ct033")
    now = datetime.now(timezone.utc).isoformat()

    video_path = "assets/generated/videos/S001-test123.mp4"
    video_file = root / video_path
    video_file.parent.mkdir(parents=True, exist_ok=True)
    video_file.write_bytes(b"\x00" * 110_000)

    _write_json(root / "creative" / "shot-references.json", {
        "version": 4,
        "shots": {
            "S001": {
                "background": "assets/generated/backgrounds/S001-bg.png",
                "background_master_id": "BG001",
                "keyframes": [{"path": "assets/generated/keyframes/S001-test.png",
                               "source": "generated", "background_master_id": "BG001",
                               "character_ids": [], "prompt_zh": "", "prompt_en": "",
                               "model": "", "request_id": "", "cost_yuan": 0.0, "created_at": now}],
                "selected_keyframe": "assets/generated/keyframes/S001-test.png",
                "video_entries": [
                    {"path": video_path, "source_keyframe": "assets/generated/keyframes/S001-test.png",
                     "duration_requested": 5, "duration_actual": 5.0,
                     "resolution": "720p", "file_size_bytes": 110_000,
                     "model": "seedance-2.0", "task_id": "task-abc",
                     "cost_yuan": 3.0, "qc_passed": True, "created_at": now},
                ],
            }
        },
    })

    resp = client.put(
        f"/api/v1/projects/{project_id}/shots/S001/videos/selection",
        json={"path": video_path},
    )
    assert resp.status_code == 200
    wf = resp.json()
    shots_stage = next(s for s in wf["stages"] if s["id"] == "shots")
    shots = shots_stage["data"]["shots"]
    assert shots[0]["selected_video"] == video_path
    assert shots[0]["video_entries"][0]["is_selected"] is True
