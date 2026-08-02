"""PRD-004 unit tests: video generation preconditions, QC, metadata, workflow."""
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

from mv_platform.application.service import ApplicationService, ApplicationBlocked
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


def _make_mp4_bytes(duration_seconds: float, timescale: int = 1000) -> bytes:
    """Build a minimal valid MP4 with mvhd box for duration parsing tests."""
    duration_units = int(duration_seconds * timescale)
    # version=0 mvhd: 4+4 box header + 1 version + 3 flags + 4 ctime + 4 mtime
    #                  + 4 timescale + 4 duration + rest (76 bytes total content)
    mvhd_content = (
        b"\x00"           # version 0
        + b"\x00\x00\x00"  # flags
        + b"\x00\x00\x00\x00"  # creation_time
        + b"\x00\x00\x00\x00"  # modification_time
        + timescale.to_bytes(4, "big")
        + duration_units.to_bytes(4, "big")
        + b"\x00" * 76    # rate, volume, matrix, pre_defined, next_track_id
    )
    def box(name: bytes, content: bytes) -> bytes:
        size = 8 + len(content)
        return size.to_bytes(4, "big") + name + content

    mvhd_box = box(b"mvhd", mvhd_content)
    moov_box = box(b"moov", mvhd_box)
    # ftyp box to pass magic bytes check
    ftyp_content = b"isom" + b"\x00\x00\x02\x00" + b"isom" + b"iso2" + b"avc1" + b"mp41"
    ftyp_box = box(b"ftyp", ftyp_content)
    # mdat with padding to pass 100KB size check
    padding = b"\x00" * (110_000 - len(ftyp_box) - len(moov_box) - 8)
    mdat_box = box(b"mdat", padding)
    return ftyp_box + moov_box + mdat_box


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


def _setup_project_with_keyframe(tmp_path, slug, selected_keyframe=True):
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
    kf_path = "assets/generated/keyframes/S001-test.png"
    kf_file = root / kf_path
    kf_file.parent.mkdir(parents=True, exist_ok=True)
    kf_file.write_bytes(TINY_PNG)

    shot_data: dict = {
        "background": "assets/generated/backgrounds/S001-bg.png",
        "background_master_id": "BG001",
        "keyframes": [{"path": kf_path, "source": "generated", "background_master_id": "BG001",
                        "character_ids": [], "prompt_zh": "", "prompt_en": "test",
                        "model": "gpt-image-2", "request_id": "r1", "cost_yuan": 0.5, "created_at": now}],
    }
    if selected_keyframe:
        shot_data["selected_keyframe"] = kf_path

    _write_json(root / "creative" / "shot-references.json", {
        "version": 3,
        "shots": {"S001": shot_data},
    })
    bg_path = root / "assets/generated/backgrounds/S001-bg.png"
    bg_path.parent.mkdir(parents=True, exist_ok=True)
    bg_path.write_bytes(TINY_PNG)

    _write_decision(root, "story")
    _write_decision(root, "storyboard")
    _write_decision(root, "scenes")

    return service, project_id, root


class _MockVideoProvider:
    """Video provider that returns a minimal valid MP4."""
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
# UT-030: no selected_keyframe → blocked
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_start_seedance_blocked_without_keyframe(tmp_path, monkeypatch):
    """UT-030: start_seedance_shot blocked when shot has no selected_keyframe."""
    monkeypatch.setenv("SEEDANCE_BASE_URL", "http://fake.example.com")
    service, project_id, _ = _setup_project_with_keyframe(tmp_path, "ut030", selected_keyframe=False)
    service.video_provider = _MockVideoProvider()

    with pytest.raises(ApplicationBlocked) as exc_info:
        service.generate_shot_video(project_id, "S001", duration=5)

    assert exc_info.value.error_stage == "precondition"
    assert "keyframe" in str(exc_info.value).lower()


# ---------------------------------------------------------------------------
# UT-031: SEEDANCE_BASE_URL not configured → blocked
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_start_seedance_blocked_without_config(tmp_path, monkeypatch):
    """UT-031: generate_shot_video blocked when SEEDANCE_BASE_URL is missing."""
    monkeypatch.delenv("SEEDANCE_BASE_URL", raising=False)
    service, project_id, _ = _setup_project_with_keyframe(tmp_path, "ut031")
    service.video_provider = _MockVideoProvider()

    with pytest.raises(ApplicationBlocked) as exc_info:
        service.generate_shot_video(project_id, "S001", duration=5)

    assert exc_info.value.error_stage == "configuration"


# ---------------------------------------------------------------------------
# UT-032: QC fails on duration mismatch > 2s
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_qc_fails_on_duration_mismatch():
    """UT-032: _qc_video returns qc_passed=False when duration differs by >2s."""
    video_bytes_8s = _make_mp4_bytes(8.0)
    qc_passed, info = ApplicationService._qc_video(video_bytes_8s, duration_requested=5)
    assert not qc_passed
    assert any("duration_mismatch" in issue for issue in info["qc_issues"])


# ---------------------------------------------------------------------------
# UT-033: QC passes on valid MP4
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_qc_passes_on_valid_video():
    """UT-033: _qc_video returns qc_passed=True for a valid 5s MP4."""
    video_bytes_5s = _make_mp4_bytes(5.0)
    qc_passed, info = ApplicationService._qc_video(video_bytes_5s, duration_requested=5)
    assert qc_passed, f"QC should pass, issues: {info['qc_issues']}"
    assert abs(info["duration_actual"] - 5.0) < 0.5


# ---------------------------------------------------------------------------
# UT-034: video_entry written after generation
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_video_entry_written_after_generation(tmp_path, monkeypatch):
    """UT-034: generate_shot_video writes video_entries to shot-references.json."""
    monkeypatch.setenv("SEEDANCE_BASE_URL", "http://fake.example.com")
    monkeypatch.setenv("SEEDANCE_MODEL", "seedance-2.0-mock")
    service, project_id, root = _setup_project_with_keyframe(tmp_path, "ut034")
    service.video_provider = _MockVideoProvider()

    service.generate_shot_video(project_id, "S001", duration=5)

    refs = service._shot_references(root)
    entries = refs["shots"]["S001"]["video_entries"]
    assert len(entries) == 1
    entry = entries[0]
    assert entry["cost_yuan"] == 4.0
    assert entry["task_id"] != ""
    assert "duration_actual" in entry
    assert entry["source_keyframe"] != ""
    assert entry["path"].startswith("assets/generated/videos/S001-")


# ---------------------------------------------------------------------------
# UT-035: workflow returns video_entries
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_workflow_includes_video_entries(tmp_path, monkeypatch):
    """UT-035: get_project_workflow includes video_entries and selected_video in shots stage."""
    monkeypatch.setenv("SEEDANCE_BASE_URL", "http://fake.example.com")
    service, project_id, root = _setup_project_with_keyframe(tmp_path, "ut035")
    now = datetime.now(timezone.utc).isoformat()

    video_path = "assets/generated/videos/S001-abc123.mp4"
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
                     "duration_requested": 5, "duration_actual": 4.97,
                     "resolution": "720p", "file_size_bytes": 110_000,
                     "model": "seedance-2.0", "task_id": "task-abc",
                     "cost_yuan": 3.0, "qc_passed": True, "created_at": now},
                ],
                "selected_video": video_path,
            }
        },
    })
    kf_file = root / "assets/generated/keyframes/S001-test.png"
    kf_file.parent.mkdir(parents=True, exist_ok=True)
    kf_file.write_bytes(TINY_PNG)

    wf = service.get_project_workflow(project_id)
    shots_stage = next(s for s in wf["stages"] if s["id"] == "shots")
    shots = shots_stage["data"]["shots"]
    assert len(shots) > 0
    shot = shots[0]
    assert "video_entries" in shot
    assert len(shot["video_entries"]) == 1
    assert shot["video_entries"][0]["qc_passed"] is True
    assert shot["video_entries"][0]["is_selected"] is True
    assert shot["selected_video"] == video_path
