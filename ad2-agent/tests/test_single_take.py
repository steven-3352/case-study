from __future__ import annotations

import io
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml
from PIL import Image

from conductor import media
from conductor.tools import _normalize_shots, compose


def test_normalize_single_take_timeline() -> None:
    shots = _normalize_shots(
        [{
            "id": "SH001",
            "type": "generated",
            "duration": 15,
            "delivery_mode": "single_take",
            "product_overlays": [
                {"product_ref": "hero", "start": 4, "end": 8},
                {"product_ref": "missing", "start": 9, "end": 12},
                {"product_ref": "hero", "start": 14, "end": 30},
            ],
            "text_overlays": [
                {"text": "hook", "start": -2, "end": 2},
                {"text": "invalid", "start": 8, "end": 7},
            ],
        }],
        {"hero"},
    )

    assert shots[0]["delivery_mode"] == "single_take"
    assert shots[0]["duration"] == 15
    assert shots[0]["product_ref"] == ""
    assert shots[0]["product_overlays"] == [
        {"product_ref": "hero", "start": 4.0, "end": 8.0},
        {"product_ref": "hero", "start": 14.0, "end": 15},
    ]
    assert shots[0]["text_overlays"] == [
        {"text": "hook", "start": 0.0, "end": 2.0},
    ]


def test_normalize_legacy_shot_defaults_to_standard() -> None:
    shot = _normalize_shots([{"id": "SH001", "type": "display"}], {"hero"})[0]
    assert shot["delivery_mode"] == "standard"
    assert shot["product_overlays"] == []
    assert shot["text_overlays"] == []


def test_generated_keyframe_covers_canvas_without_black_bars() -> None:
    source = Image.new("RGB", (200, 300), (240, 220, 180))
    encoded = io.BytesIO()
    source.save(encoded, format="PNG")

    result = Image.open(io.BytesIO(media.fit_image_to_canvas(encoded.getvalue(), (90, 160))))

    assert result.size == (90, 160)
    assert result.getpixel((0, 0)) == (240, 220, 180)
    assert result.getpixel((89, 159)) == (240, 220, 180)


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg unavailable")
def test_compose_single_take_skips_concat_and_overlays_product(tmp_path: Path) -> None:
    inputs = tmp_path / "inputs"
    shot_dir = inputs / "04_shots"
    intake_dir = inputs / "00_intake"
    out_dir = tmp_path / "delivery"
    shot_dir.mkdir(parents=True)
    intake_dir.mkdir(parents=True)
    out_dir.mkdir()

    source = shot_dir / "SH001.mp4"
    subprocess.run(
        [
            shutil.which("ffmpeg"), "-y", "-f", "lavfi", "-i",
            "color=c=white:s=186x320:d=2:r=30", "-c:v", "libx264",
            "-pix_fmt", "yuv420p", str(source),
        ],
        check=True,
        capture_output=True,
    )
    product = tmp_path / "product.png"
    Image.new("RGB", (80, 80), (220, 30, 30)).save(product)

    (shot_dir / "shots_index.yaml").write_text(
        yaml.safe_dump({"shots": [{
            "id": "SH001",
            "video": "SH001.mp4",
            "duration": 2,
            "type": "generated",
            "source": "seedance",
            "delivery_mode": "single_take",
            "product_overlays": [{"product_ref": "hero", "start": 0.5, "end": 1.5}],
            "text_overlays": [],
        }]}),
        encoding="utf-8",
    )
    (intake_dir / "manifest.yaml").write_text(
        yaml.safe_dump({
            "aspect_ratio": "9:16",
            "images": [{"name": "hero", "path": str(product), "role": "product"}],
        }),
        encoding="utf-8",
    )

    result = compose([inputs], out_dir, {})

    assert result.ok
    assert result.meta["single_take"] is True
    assert result.meta["product_overlays"] == 1
    assert (out_dir / "final.mp4").is_file()
    assert "单次生成，不拼接" in (out_dir / "delivery_report.md").read_text(encoding="utf-8")

    opening_frame = tmp_path / "opening-frame.png"
    subprocess.run(
        [
            shutil.which("ffmpeg"), "-y", "-ss", "0.25", "-i",
            str(out_dir / "final.mp4"), "-frames:v", "1", str(opening_frame),
        ],
        check=True,
        capture_output=True,
    )
    opening = Image.open(opening_frame).convert("RGB")
    assert min(opening.getpixel((0, 0))) > 235

    clean_frame = tmp_path / "clean-frame.png"
    subprocess.run(
        [
            shutil.which("ffmpeg"), "-y", "-ss", "1.75", "-i",
            str(out_dir / "final.mp4"), "-frames:v", "1", str(clean_frame),
        ],
        check=True,
        capture_output=True,
    )
    pixel = Image.open(clean_frame).convert("RGB").getpixel((90, 160))
    assert pixel[0] > 235 and pixel[1] > 230 and pixel[2] > 220
