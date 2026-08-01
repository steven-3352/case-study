import copy
import json

import pytest
import yaml

from mvstudio.director.creative_planner import CreativePlanError, draft_creative_score
from mvstudio.director.drafting import ModelResult
from mvstudio.director.structural_planner import plan_structural_score
from tests.mvstudio.director.test_drafting import FixturePort
from tests.mvstudio.director.test_structural_planner import _maps


def _contracts():
    music, characters, semantic = _maps()
    brief = {
        "canvas": "9:16",
        "premise": "A and B choose to stand together.",
        "audience": "viewers following the relationship",
    }
    structural = plan_structural_score(music, characters, semantic, brief)
    audit = {"version": 1, "status": "draft_self_generated", "calls": [{}, {}]}
    return structural, music, characters, semantic, brief, audit


def test_creative_draft_changes_only_allowlisted_shot_decisions(tmp_path):
    structural, music, characters, semantic, brief, audit = _contracts()
    original = copy.deepcopy(structural)
    port = FixturePort()
    result = draft_creative_score(
        structural, music, characters, semantic, brief, port, "fixture", tmp_path, audit
    )
    score = result["visual_score"]

    assert score["purpose"] == "creative_visual_score_draft"
    assert result["model_audit"]["calls"][:2] == audit["calls"]
    assert len(result["model_audit"]["calls"]) == 6
    assert score["creative_review"]["selected_plan"] == "Level three relationship-led MV"
    assert [shot["id"] for shot in score["shots"]] == [shot["id"] for shot in original["shots"]]
    assert [shot["time"] for shot in score["shots"]] == [shot["time"] for shot in original["shots"]]
    assert [shot["energy"] for shot in score["shots"]] == [shot["energy"] for shot in original["shots"]]
    assert [shot["characters"] for shot in score["shots"]] == [
        shot["characters"] for shot in original["shots"]
    ]
    assert [shot["lyric"] for shot in score["shots"]] == [shot["lyric"] for shot in original["shots"]]
    assert [shot["assets"]["use"] for shot in score["shots"]] == [
        shot["assets"]["use"] for shot in original["shots"]
    ]
    assert score["shots"][-1]["transition_out"] == original["shots"][-1]["transition_out"]
    creative_task = next(
        task for task in port.tasks if task.event_type == "visual_score.creative_draft_requested"
    )
    payload = json.dumps(creative_task.payload, sort_keys=True)
    assert "inputs/characters/" not in payload
    assert "digest" not in payload
    assert set(creative_task.output_schema["shots"][0]) == {
        "id", "purpose", "arrangement", "primary_action", "first_frame", "last_frame",
    }
    assert yaml.safe_load((tmp_path / "creative/visual_score.yaml").read_text()) == score


def test_creative_batches_only_apply_final_transition_rule_to_the_full_film(tmp_path):
    structural, music, characters, semantic, brief, audit = _contracts()
    template = structural["shots"][0]
    shots = []
    for index in range(10):
        shot = copy.deepcopy(template)
        shot["id"] = f"S{index + 1:03d}"
        shot["time"] = [float(index), float(index + 1)]
        shot["transition_out"] = {
            "type": "none" if index == 9 else "hard_cut",
            "shared_element": "final held composition" if index == 9 else "matched gaze",
        }
        shots.append(shot)
    structural["shots"] = shots
    port = FixturePort()

    result = draft_creative_score(
        structural, music, characters, semantic, brief, port, "fixture", tmp_path, audit
    )

    creative_tasks = [
        task for task in port.tasks
        if task.event_type == "visual_score.creative_draft_requested"
    ]
    assert len(result["visual_score"]["shots"]) == 10
    assert len(creative_tasks) == 10
    assert all(
        task.payload["constraints"]["last_transition_must_be_none"] is False
        for task in creative_tasks[:-1]
    )
    assert creative_tasks[-1].payload["constraints"]["last_transition_must_be_none"] is True
    assert [len(task.payload["shots"]) for task in creative_tasks] == [1] * 10
    assert all(
        task.payload["constraints"]["max_characters_per_text_field"] == 120
        for task in creative_tasks
    )


class InvalidCreativePort(FixturePort):
    def __init__(self, mutation):
        super().__init__()
        self.mutation = mutation

    def run(self, task):
        result = super().run(task)
        if task.event_type != "visual_score.creative_draft_requested":
            return result
        output = copy.deepcopy(result.output)
        self.mutation(output)
        return ModelResult(output, result.input_tokens, result.output_tokens)


class TranslatingFixturePort(FixturePort):
    translate_chinese_prompts = True

    def run(self, task):
        if task.event_type == "prompt.translate_requested":
            self.tasks.append(task)
            return ModelResult(
                {
                    "english_system_prompt": "Return the requested contract.",
                    "english_task_prompt": "Keep every field concise.",
                },
                input_tokens=40,
                output_tokens=20,
            )
        return super().run(task)


def test_creative_batches_translate_each_unique_prompt_only_once(tmp_path):
    structural, music, characters, semantic, brief, audit = _contracts()
    template = structural["shots"][0]
    structural["shots"] = []
    for index in range(5):
        shot = copy.deepcopy(template)
        shot["id"] = f"S{index + 1:03d}"
        shot["time"] = [float(index), float(index + 1)]
        shot["transition_out"] = {
            "type": "none" if index == 4 else "hard_cut",
            "shared_element": "final held composition" if index == 4 else "matched gaze",
        }
        structural["shots"].append(shot)
    port = TranslatingFixturePort()

    draft_creative_score(
        structural, music, characters, semantic, brief, port, "fixture", tmp_path, audit
    )

    translations = [
        task for task in port.tasks if task.event_type == "prompt.translate_requested"
    ]
    assert len(translations) == 2
    assert {task.payload["source_event"] for task in translations} == {
        "visual_score.creative_draft_requested",
        "visual_score.quality_review_requested",
    }


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda value: value["shots"][0].update(id="changed"), "preserve structural order"),
        (lambda value: value["shots"].pop(), "cover every structural shot"),
        (lambda value: value["shots"][0].update(extra="unknown"), "contract is invalid"),
    ],
)
def test_creative_draft_rejects_structural_drift(tmp_path, mutation, message):
    structural, music, characters, semantic, brief, audit = _contracts()
    with pytest.raises(CreativePlanError, match=message):
        draft_creative_score(
            structural,
            music,
            characters,
            semantic,
            brief,
            InvalidCreativePort(mutation),
            "fixture",
            tmp_path,
            audit,
        )
    assert not (tmp_path / "creative/visual_score.yaml").exists()
