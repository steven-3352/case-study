from __future__ import annotations

import io
from pathlib import Path

import pytest
import yaml
from PIL import Image

from conductor import media, tools
from conductor.tools import _normalize_shots, gen_keyframe, gen_video


def _png_bytes(color=(230, 220, 200)) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (64, 64), color).save(buffer, format="PNG")
    return buffer.getvalue()


def test_generated_static_motion_is_preserved_with_multimodal_references() -> None:
    shot = _normalize_shots([{
        "id": "SH001", "type": "generated", "motion": "static",
        "reference_audio_url": " https://media.example/audio.mp3 ",
        "reference_image_urls": [" https://media.example/a.png ", ""],
    }], set())[0]

    assert shot["motion"] == "static"
    assert shot["reference_audio_url"] == "https://media.example/audio.mp3"
    assert shot["reference_image_urls"] == ["https://media.example/a.png"]


def test_display_keyframe_records_source_and_composite_digests_and_only_isolated(
        monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    inputs = tmp_path / "inputs"
    storyboard = inputs / "02_storyboard"
    intake = inputs / "00_intake"
    out_dir = tmp_path / "03_keyframes"
    storyboard.mkdir(parents=True)
    intake.mkdir(parents=True)
    out_dir.mkdir()
    product = tmp_path / "product.png"
    product.write_bytes(_png_bytes((200, 40, 30)))
    audio_url = "https://media.example/audio.mp3"
    image_urls = ["https://media.example/start.png", "https://media.example/end.png"]
    shots = [
        {"id": "SH001", "type": "generated", "motion": "static", "duration": 5},
        {"id": "SH002", "type": "display", "motion": "static", "duration": 5,
         "product_ref": "hero", "reference_audio_url": audio_url,
         "reference_image_urls": image_urls},
    ]
    (storyboard / "shots.yaml").write_text(
        yaml.safe_dump({"shots": shots}), encoding="utf-8")
    (intake / "manifest.yaml").write_text(yaml.safe_dump({
        "aspect_ratio": "1:1",
        "images": [{"name": "hero", "role": "product", "path": str(product)}],
    }), encoding="utf-8")
    old_entry = {"id": "SH001", "keyframe": "SH001_keyframe.png",
                 "type": "generated", "motion": "static", "duration": 5,
                 "digest": "sha256:old", "sentinel": "unchanged"}
    (out_dir / "SH001_keyframe.png").write_bytes(b"old-keyframe")
    (out_dir / "keyframes_index.yaml").write_text(
        yaml.safe_dump({"keyframes": [old_entry]}), encoding="utf-8")

    class ImageProviderStub:
        def generate(self, *args, **kwargs):
            return _png_bytes()

    monkeypatch.setattr(tools, "_image_provider", lambda: ImageProviderStub())
    result = gen_keyframe([inputs], out_dir, {"only": ["SH002"]})
    index = yaml.safe_load((out_dir / "keyframes_index.yaml").read_text(encoding="utf-8"))

    assert result.ok
    assert index["keyframes"][0] == old_entry
    assert (out_dir / "SH001_keyframe.png").read_bytes() == b"old-keyframe"
    display = index["keyframes"][1]
    assert display["source_digest"] == media.sha256_file(product)
    assert display["composite_digest"] == display["digest"]
    assert display["source_digest"] != display["composite_digest"]
    assert display["reference_audio_url"] == audio_url
    assert display["reference_image_urls"] == image_urls


def test_generated_static_uses_local_route_and_only_preserves_other_shot(
        monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    inputs = tmp_path / "inputs"
    keyframes = inputs / "03_keyframes"
    intake = inputs / "00_intake"
    out_dir = tmp_path / "04_shots"
    keyframes.mkdir(parents=True)
    intake.mkdir(parents=True)
    out_dir.mkdir()
    (keyframes / "SH001.png").write_bytes(b"one")
    (keyframes / "SH002.png").write_bytes(b"two")
    (keyframes / "keyframes_index.yaml").write_text(yaml.safe_dump({"keyframes": [
        {"id": "SH001", "keyframe": "SH001.png", "type": "generated",
         "motion": "static", "duration": 5},
        {"id": "SH002", "keyframe": "SH002.png", "type": "generated",
         "motion": "static", "duration": 6},
    ]}), encoding="utf-8")
    (intake / "manifest.yaml").write_text(
        yaml.safe_dump({"aspect_ratio": "9:16"}), encoding="utf-8")
    old_entry = {"id": "SH001", "video": "SH001.mp4", "duration": 5,
                 "type": "generated", "source": "static", "sentinel": "unchanged"}
    (out_dir / "SH001.mp4").write_bytes(b"old-video")
    (out_dir / "shots_index.yaml").write_text(
        yaml.safe_dump({"shots": [old_entry]}), encoding="utf-8")

    def local_static(source, output, seconds, canvas):
        Path(output).write_bytes(b"new-local-video")
        return True

    monkeypatch.setattr(media, "still_to_mp4", local_static)
    from mvstudio.providers.seedance import SeedancePort
    monkeypatch.setattr(
        SeedancePort, "from_env",
        lambda: pytest.fail("generated+static must not initialize Seedance"),
    )
    result = gen_video([inputs], out_dir, {"only": ["SH002"]})
    index = yaml.safe_load((out_dir / "shots_index.yaml").read_text(encoding="utf-8"))

    assert result.ok
    assert index["shots"][0] == old_entry
    assert (out_dir / "SH001.mp4").read_bytes() == b"old-video"
    assert index["shots"][1]["source"] == "static"
    assert index["shots"][1]["edit_duration"] == 6


def test_i2v_records_generation_and_edit_duration_without_network(
        monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    inputs = tmp_path / "inputs"
    keyframes = inputs / "03_keyframes"
    intake = inputs / "00_intake"
    out_dir = tmp_path / "04_shots"
    keyframes.mkdir(parents=True)
    intake.mkdir(parents=True)
    out_dir.mkdir()
    (keyframes / "SH001.png").write_bytes(b"keyframe")
    (keyframes / "keyframes_index.yaml").write_text(yaml.safe_dump({"keyframes": [{
        "id": "SH001", "keyframe": "SH001.png", "type": "generated",
        "motion": "i2v", "duration": 7, "generation_duration": 9,
        "edit_duration": 7, "reference_audio_url": "https://media.example/audio.mp3",
        "reference_image_urls": ["https://media.example/ref.png"],
    }]}), encoding="utf-8")
    (intake / "manifest.yaml").write_text(
        yaml.safe_dump({"aspect_ratio": "16:9"}), encoding="utf-8")
    captured = {}

    class SeedanceStub:
        def generate(self, task):
            captured["task"] = task
            return type("Result", (), {"video_bytes": b"video"})()

    from mvstudio.providers.seedance import SeedancePort
    monkeypatch.setattr(SeedancePort, "from_env", lambda: SeedanceStub())
    result = gen_video([inputs], out_dir, {})
    index = yaml.safe_load((out_dir / "shots_index.yaml").read_text(encoding="utf-8"))

    assert result.ok
    assert captured["task"].duration_seconds == 9
    assert captured["task"].reference_audio_url == "https://media.example/audio.mp3"
    assert captured["task"].reference_image_urls == ("https://media.example/ref.png",)
    assert index["shots"][0]["generation_duration"] == 9
    assert index["shots"][0]["edit_duration"] == 7
    assert index["shots"][0]["duration"] == 7
