import copy

import pytest

from mvstudio.generation.shot_contract import ApprovedShotError, parse_approved_shot


H = "sha256:" + "a" * 64


@pytest.fixture
def approved_shot():
    return {
        "version": 1,
        "status": "approved",
        "project_id": "project-qingyi",
        "shot_id": "shot-001",
        "model": "doubao-seedance-2-0",
        "prompt": "The camera advances slowly as fabric and hair respond to a soft breeze.",
        "duration_seconds": 5,
        "aspect_ratio": "9:16",
        "resolution": "720p",
        "first_frame": {
            "path": "assets/source/keyframes/shot-001.png",
            "sha256": H,
        },
        "approved_by": "user",
        "approved_at": "2026-07-31T12:00:00+08:00",
    }


def test_approved_shot_is_strict_and_deterministic(approved_shot):
    original = copy.deepcopy(approved_shot)
    left = parse_approved_shot(approved_shot, "project-qingyi")
    right = parse_approved_shot(copy.deepcopy(approved_shot), "project-qingyi")

    assert approved_shot == original
    assert left.shot_id == "shot-001"
    assert left.first_frame_path == "assets/source/keyframes/shot-001.png"
    assert left.contract_sha256 == right.contract_sha256


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("status", "draft", "explicitly approved"),
        ("project_id", "project-other", "identity mismatch"),
        ("shot_id", "../shot", "shot_id is invalid"),
        ("duration_seconds", 16, "between 4 and 15"),
        ("aspect_ratio", "16:9", "9:16"),
        ("approved_at", "2026-07-31T12:00:00", "timezone"),
    ],
)
def test_approved_shot_rejects_invalid_values(approved_shot, field, value, message):
    approved_shot[field] = value
    with pytest.raises(ApprovedShotError, match=message):
        parse_approved_shot(approved_shot, "project-qingyi")


def test_approved_shot_rejects_unknown_fields(approved_shot):
    approved_shot["provider_response"] = {"secret": "must-not-enter-contract"}
    with pytest.raises(ApprovedShotError, match="fields"):
        parse_approved_shot(approved_shot, "project-qingyi")


@pytest.mark.parametrize(
    "path",
    [
        "/tmp/shot.png",
        "assets/source/shot.png",
        "assets/source/keyframes/../shot.png",
        "assets\\source\\keyframes\\shot.png",
    ],
)
def test_approved_shot_rejects_unsafe_first_frame_paths(approved_shot, path):
    approved_shot["first_frame"]["path"] = path
    with pytest.raises(ApprovedShotError, match="keyframes"):
        parse_approved_shot(approved_shot, "project-qingyi")
