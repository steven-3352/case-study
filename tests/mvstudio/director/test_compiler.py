import json

import pytest
import yaml

from mvstudio.director import DirectorContractError, compile_package, validate_package


def test_compile_emits_registered_project_relative_artifacts(tmp_path, director_package):
    manifest = compile_package(director_package, tmp_path, job_id="job-fixture")

    paths = {item["path"] for item in manifest["artifacts"]}
    assert paths == {
        "creative/asset_plan.yaml",
        "creative/generation_plan.yaml",
        "creative/shots.yaml",
        "creative/story_framework.yaml",
        "creative/storyboard.md",
    }
    assert all(item["project_id"] == "project-fixture" for item in manifest["artifacts"])
    assert all(item["job_id"] == "job-fixture" for item in manifest["artifacts"])
    assert all(item["content_hash"].startswith("sha256:") for item in manifest["artifacts"])
    assert json.loads((tmp_path / "artifact-manifest.json").read_text())["project_id"] == "project-fixture"


def test_generation_clip_is_distinct_and_at_least_four_seconds(tmp_path, director_package):
    compile_package(director_package, tmp_path)
    plan = yaml.safe_load((tmp_path / "creative/generation_plan.yaml").read_text())

    assert len(plan["editorial_shots"]) == 2
    assert plan["editorial_shots"][0]["duration_ms"] == 500
    assert len(plan["generation_clips"]) == 1
    assert plan["generation_clips"][0]["duration_ms"] == 4000
    assert plan["generation_clips"][0]["usable_range_ms"] == [1750, 2250]


def test_invalid_or_flat_contract_fails_closed(director_package):
    director_package["visual_score"]["shots"][1]["energy"] = 2
    with pytest.raises(DirectorContractError, match="energy arc"):
        validate_package(director_package)


def test_unknown_fields_fail_closed(director_package):
    director_package["output_path"] = "/tmp/escape"
    with pytest.raises(DirectorContractError, match="unknown director package field"):
        validate_package(director_package)


def test_asset_path_traversal_fails_closed(director_package):
    director_package["visual_score"]["shots"][0]["assets"]["use"] = ["../../outside.png"]
    with pytest.raises(DirectorContractError, match="project-relative"):
        validate_package(director_package)


def test_vertical_animatic_is_validated_540p(tmp_path, director_package):
    director_package["animatic"]["enabled"] = True
    manifest = compile_package(director_package, tmp_path)

    qc = json.loads((tmp_path / "outputs/qc_report.json").read_text())
    assert qc["status"] == "pass_gate_checked"
    assert (qc["width"], qc["height"]) == (540, 960)
    assert qc["audio_present"] is False
    assert qc["duration"] == pytest.approx(1.0, abs=0.26)
    assert (tmp_path / "outputs/animatic.mp4").stat().st_size > 0
    assert "outputs/animatic.mp4" in {item["path"] for item in manifest["artifacts"]}
