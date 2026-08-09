from __future__ import annotations

import io
import json
from pathlib import Path

import pytest
import yaml
from PIL import Image

from conductor import tools
from mvstudio.providers.seedance import (
    SeedanceFrame,
    SeedancePort,
    SeedanceProviderError,
    SeedanceTask,
    _digest,
)


PNG = b"\x89PNG\r\n\x1a\nfixture"
MP4 = b"\x00\x00\x00\x18ftypisomfixture-video"


class _Response:
    def __init__(self, value: bytes):
        self.value = value

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def read(self, limit: int) -> bytes:
        return self.value[:limit]


def _png_bytes(color: tuple[int, int, int] = (235, 225, 205)) -> bytes:
    encoded = io.BytesIO()
    Image.new("RGB", (24, 32), color).save(encoded, format="PNG")
    return encoded.getvalue()


def _write_keyframe_inputs(root: Path, keyframes: list[dict]) -> Path:
    inputs = root / "inputs"
    keyframe_dir = inputs / "03_keyframes"
    intake_dir = inputs / "00_intake"
    keyframe_dir.mkdir(parents=True)
    intake_dir.mkdir(parents=True)
    for item in keyframes:
        (keyframe_dir / item["keyframe"]).write_bytes(_png_bytes())
    (keyframe_dir / "keyframes_index.yaml").write_text(
        yaml.safe_dump({"keyframes": keyframes}), encoding="utf-8"
    )
    (intake_dir / "manifest.yaml").write_text(
        yaml.safe_dump({"aspect_ratio": "9:16"}), encoding="utf-8"
    )
    return inputs


def test_keyframe_routes_display_to_composite_and_generated_to_cover(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    inputs = tmp_path / "inputs"
    storyboard_dir = inputs / "02_storyboard"
    intake_dir = inputs / "00_intake"
    out_dir = tmp_path / "03_keyframes"
    storyboard_dir.mkdir(parents=True)
    intake_dir.mkdir(parents=True)
    out_dir.mkdir()
    product = tmp_path / "product.png"
    product.write_bytes(_png_bytes((210, 30, 30)))
    shots = [
        {
            "id": "SH001", "type": "display", "motion": "static",
            "duration": 4, "product_ref": "hero", "scene": "display",
        },
        {
            "id": "SH002", "type": "generated", "motion": "i2v",
            "duration": 5, "product_ref": "hero", "scene": "action",
        },
    ]
    (storyboard_dir / "shots.yaml").write_text(
        yaml.safe_dump({"shots": shots}), encoding="utf-8"
    )
    (intake_dir / "manifest.yaml").write_text(
        yaml.safe_dump({
            "aspect_ratio": "9:16",
            "images": [{"name": "hero", "role": "product", "path": str(product)}],
        }),
        encoding="utf-8",
    )

    provider_calls: list[dict] = []

    class _ImageProvider:
        def generate(self, prompt, **kwargs):
            provider_calls.append({"prompt": prompt, **kwargs})
            return _png_bytes()

    routed: list[tuple] = []

    def fake_composite(bg_bytes, product_path, canvas):
        routed.append(("display", Path(product_path), canvas))
        return b"display-result"

    def fake_cover(src_bytes, canvas):
        routed.append(("generated", canvas))
        return b"generated-result"

    monkeypatch.setattr(tools, "_image_provider", lambda: _ImageProvider())
    monkeypatch.setattr(tools.media, "compose_product_on_background", fake_composite)
    monkeypatch.setattr(tools.media, "fit_image_to_canvas", fake_cover)

    result = tools.gen_keyframe([inputs], out_dir, {})
    index = yaml.safe_load((out_dir / "keyframes_index.yaml").read_text(encoding="utf-8"))

    assert result.ok
    assert [entry[0] for entry in routed] == ["display", "generated"]
    assert routed[0][1] == product
    assert "references" not in provider_calls[0]
    assert provider_calls[1]["references"] == [str(product)]
    assert [item["id"] for item in index["keyframes"]] == ["SH001", "SH002"]
    assert (out_dir / "SH001_keyframe.png").read_bytes() == b"display-result"
    assert (out_dir / "SH002_keyframe.png").read_bytes() == b"generated-result"


def test_keyframe_only_merges_target_without_changing_existing_entries(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    inputs = tmp_path / "inputs"
    storyboard_dir = inputs / "02_storyboard"
    intake_dir = inputs / "00_intake"
    out_dir = tmp_path / "03_keyframes"
    storyboard_dir.mkdir(parents=True)
    intake_dir.mkdir(parents=True)
    out_dir.mkdir()
    shots = [
        {"id": f"SH00{number}", "type": "generated", "motion": "i2v", "duration": 5}
        for number in (1, 2, 3)
    ]
    (storyboard_dir / "shots.yaml").write_text(
        yaml.safe_dump({"shots": shots}), encoding="utf-8"
    )
    (intake_dir / "manifest.yaml").write_text(
        yaml.safe_dump({"aspect_ratio": "9:16", "images": []}), encoding="utf-8"
    )
    existing = {
        "id": "SH001", "keyframe": "SH001_keyframe.png", "type": "generated",
        "motion": "i2v", "duration": 5, "digest": "sha256:unchanged",
    }
    (out_dir / "keyframes_index.yaml").write_text(
        yaml.safe_dump({"keyframes": [existing]}), encoding="utf-8"
    )

    calls = []

    class _ImageProvider:
        def generate(self, *args, **kwargs):
            calls.append((args, kwargs))
            return _png_bytes()

    monkeypatch.setattr(tools, "_image_provider", lambda: _ImageProvider())
    monkeypatch.setattr(tools.media, "fit_image_to_canvas", lambda *_args: b"only-sh002")

    result = tools.gen_keyframe([inputs], out_dir, {"only": ["SH002"]})
    entries = yaml.safe_load(
        (out_dir / "keyframes_index.yaml").read_text(encoding="utf-8")
    )["keyframes"]

    assert result.ok
    assert len(calls) == 1
    assert entries[0] == existing
    assert [entry["id"] for entry in entries] == ["SH001", "SH002"]
    assert "SH003" in result.meta["missing"]
    assert not (out_dir / "SH003_keyframe.png").exists()


@pytest.mark.parametrize("motion", ["static", "ken_burns"])
def test_local_video_routes_never_initialize_seedance(
    motion: str, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    keyframe = {
        "id": "SH001", "keyframe": "SH001_keyframe.png", "type": "display",
        "motion": motion, "duration": 4,
    }
    inputs = _write_keyframe_inputs(tmp_path, [keyframe])
    out_dir = tmp_path / "04_shots"
    out_dir.mkdir()

    from mvstudio.providers.seedance import SeedancePort

    monkeypatch.setattr(
        SeedancePort,
        "from_env",
        classmethod(lambda cls, *args, **kwargs: pytest.fail("Seedance initialized")),
    )

    def local_render(_source, output, _seconds, _canvas):
        Path(output).write_bytes(MP4)
        return True

    monkeypatch.setattr(tools.media, "still_to_mp4", local_render)
    monkeypatch.setattr(tools.media, "ken_burns_to_mp4", local_render)

    result = tools.gen_video([inputs], out_dir, {})

    assert result.ok
    assert yaml.safe_load(
        (out_dir / "shots_index.yaml").read_text(encoding="utf-8")
    )["shots"][0]["source"] == motion


def test_gen_video_clamps_paid_tasks_to_seedance_duration_contract(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    keyframes = [
        {
            "id": "SH001", "keyframe": "SH001_keyframe.png", "type": "generated",
            "motion": "i2v", "duration": 1,
        },
        {
            "id": "SH002", "keyframe": "SH002_keyframe.png", "type": "generated",
            "motion": "i2v", "duration": 99,
        },
    ]
    inputs = _write_keyframe_inputs(tmp_path, keyframes)
    out_dir = tmp_path / "04_shots"
    out_dir.mkdir()
    captured = []

    class _SeedanceStub:
        def generate(self, task):
            captured.append(task)
            return type("Result", (), {"video_bytes": MP4})()

    monkeypatch.setenv("SEEDANCE_MODEL", "doubao-seedance-2-0")
    monkeypatch.setattr(SeedancePort, "from_env", lambda *args, **kwargs: _SeedanceStub())

    result = tools.gen_video([inputs], out_dir, {})

    assert result.ok
    assert [task.duration_seconds for task in captured] == [4, 15]


@pytest.mark.parametrize("duration", [4, 15])
def test_seedance_provider_accepts_duration_boundaries(duration: int) -> None:
    captured = []

    def opener(request, timeout):
        captured.append(json.loads(request.data) if request.data else None)
        if request.method == "POST":
            return _Response(json.dumps({"url": "https://cdn.example/clip.mp4"}).encode())
        return _Response(MP4)

    port = SeedancePort(
        "https://seedance.example", "secret", "doubao-seedance-2-0", opener=opener
    )
    task = SeedanceTask(
        shot_id="SH001",
        model="doubao-seedance-2-0",
        prompt="subtle camera motion",
        duration_seconds=duration,
        first_frame=SeedanceFrame(PNG, _digest(PNG)),
    )

    port.generate(task)

    assert captured[0]["metadata"]["duration"] == duration


def test_reference_content_order_is_images_then_video_then_audio() -> None:
    captured = {}

    def opener(request, timeout):
        if request.method == "POST":
            captured.update(json.loads(request.data))
            return _Response(json.dumps({"url": "https://cdn.example/clip.mp4"}).encode())
        return _Response(MP4)

    port = SeedancePort(
        "https://seedance.example", "secret", "doubao-seedance-2-0", opener=opener
    )
    port.generate(SeedanceTask(
        shot_id="SH001",
        model="doubao-seedance-2-0",
        prompt="follow reference motion",
        duration_seconds=5,
        first_frame=SeedanceFrame(PNG, _digest(PNG)),
        reference_image_urls=(
            "https://cdn.example/ref-1.png", "https://cdn.example/ref-2.png"
        ),
        reference_video_url="https://cdn.example/ref.mp4",
        reference_audio_url="https://cdn.example/ref.mp3",
    ))

    assert [entry["role"] for entry in captured["metadata"]["content"]] == [
        "reference_image", "reference_image", "reference_video", "reference_audio"
    ]
    assert captured["metadata"]["generate_audio"] is True


@pytest.mark.parametrize(
    "field,url",
    [
        ("reference_video_url", "http://cdn.example/ref.mp4"),
        ("reference_video_url", "https://user:pass@cdn.example/ref.mp4"),
        ("reference_audio_url", "https://cdn.example/ref.mp3#secret"),
        ("reference_image_urls", ("https://cdn.example/ref.png#secret",)),
    ],
)
def test_reference_urls_reject_unsafe_authority_scheme_or_fragment(field, url) -> None:
    port = SeedancePort("https://seedance.example", "secret", "doubao-seedance-2-0")
    values = {field: url}
    task = SeedanceTask(
        shot_id="SH001",
        model="doubao-seedance-2-0",
        prompt="follow reference motion",
        duration_seconds=5,
        first_frame=SeedanceFrame(PNG, _digest(PNG)),
        **values,
    )

    with pytest.raises(SeedanceProviderError, match="URL"):
        port.generate(task)


def test_reference_url_allows_https_signed_query() -> None:
    captured = {}

    def opener(request, timeout):
        if request.method == "POST":
            captured.update(json.loads(request.data))
            return _Response(json.dumps({"url": "https://cdn.example/clip.mp4"}).encode())
        return _Response(MP4)

    signed = "https://cdn.example/ref.mp4?signature=temporary"
    port = SeedancePort(
        "https://seedance.example", "secret", "doubao-seedance-2-0", opener=opener
    )
    port.generate(SeedanceTask(
        shot_id="SH001",
        model="doubao-seedance-2-0",
        prompt="follow reference motion",
        duration_seconds=5,
        first_frame=SeedanceFrame(PNG, _digest(PNG)),
        reference_video_url=signed,
    ))

    assert captured["metadata"]["content"][0]["video_url"]["url"] == signed
