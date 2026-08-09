from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from conductor.recommendations import (
    BLOCKED_STATUS,
    RecommendationValidationError,
    build_recommendation,
    validate_recommendation,
    write_recommendation,
)


def _option(option_id: str = "O1") -> dict:
    return {
        "id": option_id,
        "action": "改为受控商品图层合成",
        "expected_visual_quality": "high",
        "product_fidelity": "high",
        "cost_delta": "medium",
        "time_delta": "medium",
        "invalidates": ["N11_SHOT04", "N13", "N14"],
    }


def _package(**overrides) -> dict:
    values = {
        "node": "N12",
        "reason_code": "PRODUCT_IDENTITY_DRIFT",
        "plain_reason": "商品包装文字连续三次漂移",
        "evidence": ["qa/shot-04-attempt-3.yaml"],
        "options": [_option("O1"), _option("O2")],
        "recommended_option": "O1",
        "recommendation_reason": "保住包装准确性且不降整片完成度",
        "resume_from": "N11_SHOT04",
    }
    values.update(overrides)
    return build_recommendation(**values)


def test_build_recommendation_returns_complete_validated_schema() -> None:
    package = _package()

    assert package["status"] == BLOCKED_STATUS
    assert package["recommended_option"] == "O1"
    assert package["resume_from"] == "N11_SHOT04"
    assert package["options"][0]["time_delta"] == "medium"
    assert validate_recommendation(package) == package


@pytest.mark.parametrize(
    "missing",
    [
        "expected_visual_quality",
        "product_fidelity",
        "cost_delta",
        "time_delta",
        "invalidates",
    ],
)
def test_option_requires_every_impact_field(missing: str) -> None:
    option = _option()
    option.pop(missing)

    with pytest.raises(RecommendationValidationError, match=missing):
        _package(options=[option, _option("O2")])


def test_single_option_requires_an_explanation() -> None:
    with pytest.raises(RecommendationValidationError, match="single_option_reason"):
        _package(options=[_option()], recommended_option="O1")

    package = _package(
        options=[_option()],
        recommended_option="O1",
        single_option_reason="其余路线均会伪造不可见商品面",
    )
    assert package["single_option_reason"].startswith("其余路线")


def test_recommended_option_must_exist() -> None:
    with pytest.raises(RecommendationValidationError, match="reference an option id"):
        _package(recommended_option="O9")


def test_resume_from_is_required() -> None:
    with pytest.raises(RecommendationValidationError, match="resume_from"):
        _package(resume_from="")


def test_option_ids_must_be_unique() -> None:
    with pytest.raises(RecommendationValidationError, match="unique"):
        _package(options=[_option("O1"), _option("O1")])


def test_write_recommendation_round_trips_yaml_without_temp_files(tmp_path: Path) -> None:
    package = _package()
    target = tmp_path / "qa" / "shot-04.yaml"

    assert write_recommendation(target, package) == target
    assert yaml.safe_load(target.read_text(encoding="utf-8")) == package
    assert list(target.parent.glob(f".{target.name}.*.tmp")) == []


def test_write_recommendation_validates_before_creating_file(tmp_path: Path) -> None:
    target = tmp_path / "invalid.yaml"
    invalid = _package()
    invalid["options"][0].pop("time_delta")

    with pytest.raises(RecommendationValidationError, match="time_delta"):
        write_recommendation(target, invalid)
    assert not target.exists()
