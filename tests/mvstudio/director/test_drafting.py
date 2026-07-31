import json
import math
import wave

import pytest
import yaml
from PIL import Image

from mvstudio.director.drafting import MapDraftError, ModelBudget, ModelResult, draft_maps
from mvstudio.director.intake import inspect_intake


class FixturePort:
    def __init__(self, bad_groups=False):
        self.tasks = []
        self.bad_groups = bad_groups

    def run(self, task):
        self.tasks.append(task)
        if task.event_type == "lyrics.semantic_segment.requested":
            line_ids = [item["id"] for item in task.payload["lines"]]
            if self.bad_groups:
                line_ids = list(reversed(line_ids))
            output = {
                "groups": [
                    {
                        "id": "verse",
                        "line_ids": line_ids[:2],
                        "semantic_type": "verse",
                        "emotion": "restrained",
                        "summary": "The leads enter the same world.",
                    },
                    {
                        "id": "chorus",
                        "line_ids": line_ids[2:],
                        "semantic_type": "chorus",
                        "emotion": "release",
                        "summary": "The relationship becomes a choice.",
                    },
                ]
            }
            return ModelResult(output, input_tokens=120, output_tokens=80)
        if task.event_type == "visual_score.creative_draft_requested":
            shots = task.payload["shots"]
            return ModelResult(
                {
                    "shots": [
                        {
                            "id": shot["id"],
                            "purpose": f"Creative purpose {index + 1}",
                            "leverage": "completion_3s" if index == 0 else "completion_rate",
                            "composition": {
                                "shot_size": "close" if shot["energy"] >= 4 else "medium",
                                "arrangement": f"Observable arrangement {index + 1}",
                            },
                            "primary_action": f"Observable primary action {index + 1}",
                            "first_frame": f"Observable opening state {index + 1}",
                            "last_frame": f"Observable exit state {index + 1}",
                            "transition_out": {
                                "type": "none" if index == len(shots) - 1 else "hard_cut",
                                "shared_element": (
                                    "final held composition"
                                    if index == len(shots) - 1
                                    else f"screen position {index + 1}"
                                ),
                            },
                            "technique": "2.5d",
                            "missing_assets": [],
                        }
                        for index, shot in enumerate(shots)
                    ]
                },
                input_tokens=180,
                output_tokens=140,
            )
        output = {
            "characters": [
                {
                    "id": "A",
                    "director_function": "lead the audience",
                    "traits": ["restrained"],
                    "symbols": ["light"],
                },
                {
                    "id": "B",
                    "director_function": "create relationship tension",
                    "traits": ["direct"],
                    "symbols": ["shadow"],
                },
            ],
            "relationships": [
                {
                    "pair": ["A", "B"],
                    "dramatic_function": "allies choosing together",
                    "reveal_group": "chorus",
                }
            ],
        }
        return ModelResult(output, input_tokens=100, output_tokens=70)


def _wave(path):
    rate = 8000
    samples = []
    for index in range(rate * 2):
        phase = index / rate
        pulse = 0.75 if any(abs(phase - beat) < 0.035 for beat in (0.25, 0.75, 1.25, 1.75)) else 0.04
        samples.append(int(32767 * pulse * math.sin(2 * math.pi * 220 * phase)))
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(rate)
        handle.writeframes(b"".join(value.to_bytes(2, "little", signed=True) for value in samples))


def _contracts(tmp_path):
    audio = tmp_path / "inputs/audio/song.wav"
    audio.parent.mkdir(parents=True)
    _wave(audio)
    lyrics = tmp_path / "inputs/lyrics/song.lrc"
    lyrics.parent.mkdir(parents=True)
    lyrics.write_text(
        "[00:00.10]first\n[00:00.60]second\n[00:01.10]third\n[00:01.55]fourth\n",
        encoding="utf-8",
    )
    character_dir = tmp_path / "inputs/characters"
    character_dir.mkdir(parents=True)
    Image.new("RGBA", (12, 16), (20, 30, 40, 255)).save(character_dir / "a.png")
    Image.new("RGBA", (12, 16), (50, 60, 70, 255)).save(character_dir / "b.png")
    intake = inspect_intake(
        {
            "project_id": "project-a",
            "audio": "inputs/audio/song.wav",
            "lyrics": "inputs/lyrics/song.lrc",
            "characters": ["inputs/characters/a.png", "inputs/characters/b.png"],
        },
        tmp_path,
    )
    timed = json.loads((tmp_path / "intake/lyrics_timed.json").read_text())
    brief = {
        "characters": [
            {"id": "A", "name": "Lead", "traits": ["quiet"]},
            {"id": "B", "name": "Counterpart", "traits": ["bold"]},
        ]
    }
    return intake, timed, brief


def test_bounded_port_drafts_maps_and_audit_without_portrait_payload(tmp_path):
    intake, timed, brief = _contracts(tmp_path)
    port = FixturePort()
    result = draft_maps(intake, timed, brief, port, tmp_path, "low-cost-fixture")
    assert [task.event_type for task in port.tasks] == [
        "lyrics.semantic_segment.requested",
        "relationship_map.draft_requested",
    ]
    payloads = json.dumps([task.payload for task in port.tasks], sort_keys=True)
    assert "inputs/characters" not in payloads
    assert "digest" not in payloads
    assert result["music_map"]["sections"][0]["id"] == "intro"
    assert result["music_map"]["sections"][-1]["time"][1] == pytest.approx(2.0)
    assert result["character_map"]["relationships"][0]["pair"] == ["A", "B"]
    assert len(result["beats"]["onsets"]) >= 3
    assert {task.model for task in port.tasks} == {"low-cost-fixture"}
    assert all(task.input_contract_hash.startswith("sha256:") for task in port.tasks)
    assert all(task.output_schema_hash.startswith("sha256:") for task in port.tasks)
    assert (tmp_path / "creative/beats.json").is_file()
    assert yaml.safe_load((tmp_path / "creative/music_map.yaml").read_text())["status"] == "draft_self_generated"
    audit = json.loads((tmp_path / "creative/model_audit.json").read_text())
    assert len(audit["calls"]) == 2
    assert "response_hash" in audit["calls"][0]
    assert audit["calls"][0]["usage"]["output_tokens"] == 80


def test_semantic_groups_cannot_reorder_or_skip_timed_lines(tmp_path):
    intake, timed, brief = _contracts(tmp_path)
    with pytest.raises(MapDraftError, match="cover timed lines"):
        draft_maps(intake, timed, brief, FixturePort(bad_groups=True), tmp_path, "fixture")
    assert not (tmp_path / "creative/music_map.yaml").exists()


def test_bounded_port_enforces_input_budget_before_call(tmp_path):
    intake, timed, brief = _contracts(tmp_path)
    port = FixturePort()
    with pytest.raises(MapDraftError, match="input exceeds budget"):
        draft_maps(
            intake, timed, brief, port, tmp_path, "fixture",
            budget=ModelBudget(max_input_bytes=10, max_output_bytes=1000, max_tokens=10),
        )
    assert port.tasks == []


def test_plain_lyrics_cannot_enter_semantic_drafting(tmp_path):
    intake, _timed, brief = _contracts(tmp_path)
    with pytest.raises(MapDraftError, match="timed lyrics"):
        draft_maps(intake, {"version": 1, "entries": []}, brief, FixturePort(), tmp_path, "fixture")


def test_bounded_port_enforces_reported_token_usage(tmp_path):
    intake, timed, brief = _contracts(tmp_path)
    with pytest.raises(MapDraftError, match="token usage exceeds budget"):
        draft_maps(
            intake, timed, brief, FixturePort(), tmp_path, "fixture",
            budget=ModelBudget(max_input_bytes=10000, max_output_bytes=10000, max_tokens=10),
        )


def test_drafting_rechecks_audio_hash_before_model_cost(tmp_path):
    intake, timed, brief = _contracts(tmp_path)
    (tmp_path / "inputs/audio/song.wav").write_bytes(b"tampered")
    port = FixturePort()
    with pytest.raises(MapDraftError, match="hash differs"):
        draft_maps(intake, timed, brief, port, tmp_path, "fixture")
    assert port.tasks == []


def test_drafting_rejects_symlink_output_before_model_cost(tmp_path):
    intake, timed, brief = _contracts(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    (tmp_path / "creative").symlink_to(outside, target_is_directory=True)
    port = FixturePort()
    with pytest.raises(MapDraftError, match="output directory cannot be a symlink"):
        draft_maps(intake, timed, brief, port, tmp_path, "fixture")
    assert port.tasks == []
