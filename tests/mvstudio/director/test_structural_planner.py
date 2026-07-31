import copy

import pytest
import yaml

from mvstudio.director.contracts import validate_package
from mvstudio.director.structural_planner import StructuralPlanError, plan_structural_score


def _maps():
    music = {
        "version": 1,
        "status": "draft_self_generated",
        "duration": 3.0,
        "bpm": 96.0,
        "sections": [
            {"id": "intro", "time": [0.0, 0.5], "music_role": "intro", "energy": 1, "emotion": "arrival"},
            {"id": "verse", "time": [0.5, 1.5], "music_role": "verse", "energy": 2, "emotion": "recognition"},
            {"id": "chorus", "time": [1.5, 3.0], "music_role": "chorus", "energy": 5, "emotion": "choice"},
        ],
        "cues": [
            {"at": 0.0, "level": 1, "source": "semantic_section_start"},
            {"at": 0.5, "level": 1, "source": "semantic_section_start"},
            {"at": 1.5, "level": 1, "source": "semantic_section_start"},
            {"at": 2.0, "level": 3, "source": "audio_onset"},
        ],
    }
    characters = {
        "version": 1,
        "status": "draft_self_generated",
        "characters": [
            {"id": "A", "name": "A", "director_function": "lead", "source_asset": "inputs/characters/a.png"},
            {"id": "B", "name": "B", "director_function": "counterpart", "source_asset": "inputs/characters/b.png"},
        ],
        "relationships": [
            {"pair": ["A", "B"], "dramatic_function": "choose together", "reveal_section": "chorus"}
        ],
    }
    semantic = {
        "version": 1,
        "status": "draft_self_generated",
        "lines": [
            {"id": "line_001", "start_seconds": 0.5, "end_seconds": 1.5, "text": "first"},
            {"id": "line_002", "start_seconds": 1.5, "end_seconds": 3.0, "text": "second"},
        ],
        "groups": [
            {"id": "verse", "line_ids": ["line_001"], "semantic_type": "verse", "emotion": "quiet", "summary": "A enters"},
            {"id": "chorus", "line_ids": ["line_002"], "semantic_type": "chorus", "emotion": "release", "summary": "A and B choose"},
        ],
    }
    return music, characters, semantic


def test_structural_planner_builds_contiguous_draft_score_and_relationship_shot(tmp_path):
    music, characters, semantic = _maps()
    score = plan_structural_score(
        music, characters, semantic, {"canvas": "9:16", "premise": "A and B choose"}, tmp_path
    )
    assert score["status"] == "draft_self_generated"
    assert score["approval_required"] is True
    assert len(score["shots"]) == len(music["sections"])
    assert score["shots"][0]["time"][0] == 0.0
    assert score["shots"][-1]["time"][1] == music["duration"]
    assert any(len(shot["characters"]) >= 2 for shot in score["shots"])
    assert len({shot["purpose"] for shot in score["shots"]}) == len(score["shots"])
    assert all(shot["assets"]["missing"] == [] for shot in score["shots"])
    assert yaml.safe_load((tmp_path / "creative/visual_score.yaml").read_text()) == score

    package = {
        "project_id": "project",
        "brief": {"canvas": "9:16"},
        "music_map": copy.deepcopy(music),
        "character_map": copy.deepcopy(characters),
        "visual_score": copy.deepcopy(score),
        "animatic": {"enabled": True, "fps": 4},
    }
    validate_package(package, required_status="draft_self_generated")
    for key in ("music_map", "character_map", "visual_score"):
        package[key]["status"] = "approved"
    validate_package(package)


def test_structural_planner_blocks_flat_energy():
    music, characters, semantic = _maps()
    for section in music["sections"]:
        section["energy"] = 2
    with pytest.raises(StructuralPlanError, match="non-flat energy"):
        plan_structural_score(music, characters, semantic, {})


def test_structural_planner_blocks_missing_multi_character_relationship():
    music, characters, semantic = _maps()
    characters["relationships"] = []
    with pytest.raises(StructuralPlanError, match="require a relationship"):
        plan_structural_score(music, characters, semantic, {})


def test_structural_planner_blocks_timeline_gap():
    music, characters, semantic = _maps()
    music["sections"][1]["time"][0] = 0.75
    with pytest.raises(StructuralPlanError, match="contiguous"):
        plan_structural_score(music, characters, semantic, {})
