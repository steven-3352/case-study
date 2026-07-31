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
    assert len(result["model_audit"]["calls"]) == 3
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
    assert score["shots"][-1]["transition_out"] == {
        "type": "none",
        "shared_element": "final held composition",
    }
    payload = json.dumps(port.tasks[-1].payload, sort_keys=True)
    assert "inputs/characters/" not in payload
    assert "digest" not in payload
    assert "hard_cut" in port.tasks[-1].output_schema["shots"][0]["transition_out"]["type"]
    assert "bridge_clip" in port.tasks[-1].output_schema["shots"][0]["transition_out"]["type"]
    assert yaml.safe_load((tmp_path / "creative/visual_score.yaml").read_text()) == score


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


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda value: value["shots"][0].update(id="changed"), "preserve structural order"),
        (lambda value: value["shots"].pop(), "cover every structural shot"),
        (
            lambda value: value["shots"][0]["transition_out"].update(type="unknown"),
            "not allowlisted",
        ),
        (
            lambda value: value["shots"][-1]["transition_out"].update(type="hard_cut"),
            "final creative shot",
        ),
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
