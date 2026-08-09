from __future__ import annotations

import io
from pathlib import Path

import pytest
import yaml
from PIL import Image

from conductor import media
from conductor import tools
from conductor.tools import _normalize_shots, gen_keyframe, prepare_pose_reference
from mvstudio.media import PoseReferenceError, PoseReferenceResult


def test_pose_wrapper_enforces_coverage_gate(monkeypatch: pytest.MonkeyPatch,
                                             tmp_path: Path) -> None:
    captured = {}

    def fake_generate(source, output, **kwargs):
        captured.update(kwargs)
        return PoseReferenceResult(
            output=Path(output), frames=100, detected=81, fps=25.0,
            width=720, height=1280,
        )

    monkeypatch.setattr("mvstudio.media.generate_pose_reference", fake_generate)
    result = media.pose_reference_from_video(
        tmp_path / "source.mp4", tmp_path / "pose.mp4", label=False)

    assert captured["min_coverage"] == 0.65
    assert captured["label"] is False
    assert result["coverage"] == 0.81
    assert result["frames"] == 100
    assert result["detected"] == 81


def test_prepare_pose_reference_returns_structured_suggestions_and_no_output(
        monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    output = tmp_path / "sparse-pose.mp4"

    def fail(*args, **kwargs):
        output.write_bytes(b"partial")
        raise PoseReferenceError(
            "Pose detection coverage too low: 10/100 (< 65%); "
            "source may lack a clear full-body subject."
        )

    monkeypatch.setattr(media, "pose_reference_from_video", fail)
    result = prepare_pose_reference(tmp_path / "source.mp4", output)

    assert not result.ok
    assert result.outputs == []
    assert result.error["code"] == "pose_reference_low_coverage"
    assert result.meta["min_coverage"] == 0.65
    assert result.meta["suggestions"] == [
        "replace_reference_clip", "redesign_shot", "drop_reference_motion"]
    assert not output.exists()


def test_prepare_pose_reference_rejects_low_coverage_return_value(
        monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    output = tmp_path / "sparse-pose.mp4"

    def sparse(*args, **kwargs):
        output.write_bytes(b"partial")
        return {
            "output": str(output), "frames": 100, "detected": 64,
            "coverage": 0.64, "fps": 25.0,
        }

    monkeypatch.setattr(media, "pose_reference_from_video", sparse)
    result = prepare_pose_reference(tmp_path / "source.mp4", output)

    assert not result.ok
    assert result.error["code"] == "pose_reference_low_coverage"
    assert not output.exists()


def test_prepare_pose_reference_exposes_hosting_integration_point(
        monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    output = tmp_path / "pose.mp4"

    def succeed(*args, **kwargs):
        output.write_bytes(b"pose")
        return {
            "output": str(output), "frames": 40, "detected": 38,
            "coverage": 0.95, "fps": 20.0,
        }

    monkeypatch.setattr(media, "pose_reference_from_video", succeed)
    result = prepare_pose_reference(tmp_path / "source.mp4", output)

    assert result.ok
    assert result.outputs == [str(output)]
    assert result.meta["coverage"] == 0.95
    assert result.meta["hosting"] == "external_https_required"


def test_reference_video_url_survives_storyboard_normalization() -> None:
    url = "https://media.example.test/pose/shot-1.mp4"
    shot = _normalize_shots([{
        "id": "SH001",
        "type": "generated",
        "reference_video_url": f"  {url}  ",
    }], set())[0]

    assert shot["reference_video_url"] == url


def test_reference_video_url_reaches_keyframe_index(
        monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    url = "https://media.example.test/pose/shot-1.mp4"
    inputs = tmp_path / "inputs"
    shots_dir = inputs / "02_storyboard"
    intake_dir = inputs / "00_intake"
    out_dir = tmp_path / "03_keyframes"
    shots_dir.mkdir(parents=True)
    intake_dir.mkdir(parents=True)
    out_dir.mkdir()
    (shots_dir / "shots.yaml").write_text(yaml.safe_dump({"shots": [{
        "id": "SH001", "type": "generated", "motion": "i2v",
        "duration": 5, "scene": "moving subject", "reference_video_url": url,
    }]}), encoding="utf-8")
    (intake_dir / "manifest.yaml").write_text(yaml.safe_dump({
        "aspect_ratio": "1:1", "images": [],
    }), encoding="utf-8")

    encoded = io.BytesIO()
    Image.new("RGB", (64, 64), (240, 230, 210)).save(encoded, format="PNG")

    class ImageProviderStub:
        def generate(self, *args, **kwargs):
            return encoded.getvalue()

    monkeypatch.setattr(tools, "_image_provider", lambda: ImageProviderStub())
    result = gen_keyframe([inputs], out_dir, {})
    index = yaml.safe_load((out_dir / "keyframes_index.yaml").read_text(encoding="utf-8"))

    assert result.ok
    assert index["keyframes"][0]["reference_video_url"] == url


def test_gen_video_passes_pose_reference_url_to_seedance(
        monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    url = "https://media.example.test/pose/shot-1.mp4"
    inputs = tmp_path / "inputs"
    keyframes_dir = inputs / "03_keyframes"
    intake_dir = inputs / "00_intake"
    out_dir = tmp_path / "04_shots"
    keyframes_dir.mkdir(parents=True)
    intake_dir.mkdir(parents=True)
    out_dir.mkdir()
    (keyframes_dir / "SH001_keyframe.png").write_bytes(b"keyframe")
    (keyframes_dir / "keyframes_index.yaml").write_text(yaml.safe_dump({
        "keyframes": [{
            "id": "SH001", "keyframe": "SH001_keyframe.png",
            "type": "generated", "motion": "i2v", "duration": 5,
            "reference_video_url": url,
        }],
    }), encoding="utf-8")
    (intake_dir / "manifest.yaml").write_text(yaml.safe_dump({
        "aspect_ratio": "9:16",
    }), encoding="utf-8")

    captured = {}

    class SeedanceStub:
        def generate(self, task):
            captured["task"] = task
            return type("Result", (), {"video_bytes": b"video"})()

    from mvstudio.providers.seedance import SeedancePort
    monkeypatch.setattr(SeedancePort, "from_env", lambda: SeedanceStub())
    result = tools.gen_video([inputs], out_dir, {})

    assert result.ok
    assert captured["task"].reference_video_url == url
