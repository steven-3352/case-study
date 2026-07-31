import pytest

from mvstudio.director.drafting import ModelBudget, ModelTask
from mvstudio.providers.semantic_offline import OfflineStructuralPort


def _task(event_type, payload, model="offline-structural-v1"):
    return ModelTask(
        event_type=event_type,
        model=model,
        budget=ModelBudget(),
        reason="offline structural fixture",
        input_contract_hash="sha256:" + "a" * 64,
        output_schema_hash="sha256:" + "b" * 64,
        payload=payload,
    )


def test_offline_port_preserves_line_order_without_semantic_claims():
    result = OfflineStructuralPort().run(
        _task(
            "lyrics.semantic_segment.requested",
            {"lines": [{"id": "line_001"}, {"id": "line_002"}]},
        )
    )
    assert [item["line_ids"] for item in result.output["groups"]] == [
        ["line_001"],
        ["line_002"],
    ]
    assert {item["emotion"] for item in result.output["groups"]} == {"unclassified"}
    assert (result.input_tokens, result.output_tokens) == (0, 0)


def test_offline_port_uses_declared_order_and_marks_relationship_unclassified():
    result = OfflineStructuralPort().run(
        _task(
            "relationship_map.draft_requested",
            {
                "characters": [
                    {"id": "A", "name": "A", "traits": ["quiet"]},
                    {"id": "B", "name": "B", "traits": ["direct"]},
                ],
                "semantic_groups": [{"id": "structural_001"}],
            },
        )
    )
    assert result.output["characters"][0]["director_function"] == "structural lead by declared order"
    assert result.output["relationships"] == [{
        "pair": ["A", "B"],
        "dramatic_function": "unclassified structural relationship placeholder",
        "reveal_group": "structural_001",
    }]


def test_offline_port_rejects_wrong_model_and_unknown_task():
    port = OfflineStructuralPort()
    with pytest.raises(ValueError, match="fixed model"):
        port.run(_task("lyrics.semantic_segment.requested", {"lines": [{"id": "line_001"}]}, "other"))
    with pytest.raises(ValueError, match="not allowlisted"):
        port.run(_task("other", {}))
