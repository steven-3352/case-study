"""compose_storyboard 单元测试 · 全用 PIL 合成 fixture,不依赖 CJK 字体。"""
from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from mvstudio.media import compose_storyboard


def _make_keyframe(path: Path, color: tuple[int, int, int] = (200, 100, 50)) -> Path:
    """写一张 320×180 单色 PNG 作为假 keyframe。"""
    img = Image.new("RGB", (320, 180), color)
    img.save(path, format="PNG")
    return path


def _entries(tmp: Path, n: int, with_duration: bool = True) -> list[dict]:
    out = []
    for i in range(n):
        kf = _make_keyframe(tmp / f"kf_{i:02d}.png", (50 * (i % 4), 100, 200 - 20 * i))
        entry = {"id": f"SH{i + 1:03d}", "keyframe_path": kf}
        if with_duration:
            entry["duration"] = 3 + i
        out.append(entry)
    return out


@pytest.mark.unit
def test_compose_storyboard_writes_png(tmp_path: Path) -> None:
    entries = _entries(tmp_path, n=4)
    out = tmp_path / "storyboard_grid.png"

    result = compose_storyboard(entries, out)

    assert result == out
    assert out.exists()
    with Image.open(out) as img:
        # 4 shots · default cols=3 → 2 rows
        # W = 3 * 360 + 4 * 24 = 1080 + 96 = 1176
        # H = 2 * (640 + 48) + 3 * 24 = 1376 + 72 = 1448
        assert img.size == (1176, 1448)
        assert img.mode == "RGB"


@pytest.mark.unit
def test_compose_storyboard_promotes_cols_when_over_six(tmp_path: Path) -> None:
    entries = _entries(tmp_path, n=8)
    out = tmp_path / "grid.png"

    compose_storyboard(entries, out)

    with Image.open(out) as img:
        # 8 shots · auto cols=4 → 2 rows
        # W = 4 * 360 + 5 * 24 = 1440 + 120 = 1560
        assert img.size[0] == 1560


@pytest.mark.unit
def test_compose_storyboard_skips_single_shot(tmp_path: Path) -> None:
    entries = _entries(tmp_path, n=1)
    out = tmp_path / "grid.png"

    result = compose_storyboard(entries, out)

    assert result is None
    assert not out.exists()


@pytest.mark.unit
def test_compose_storyboard_skips_empty(tmp_path: Path) -> None:
    result = compose_storyboard([], tmp_path / "grid.png")
    assert result is None


@pytest.mark.unit
def test_compose_storyboard_missing_keyframe_does_not_crash(tmp_path: Path) -> None:
    entries = [
        {"id": "SH001", "keyframe_path": tmp_path / "does_not_exist.png", "duration": 5},
        {"id": "SH002", "keyframe_path": _make_keyframe(tmp_path / "kf.png"), "duration": 4},
    ]
    out = tmp_path / "grid.png"

    result = compose_storyboard(entries, out)

    assert result == out
    assert out.exists()


@pytest.mark.unit
def test_compose_storyboard_caption_omits_duration_when_missing(tmp_path: Path) -> None:
    """duration 缺失/为 0 时 caption 只显示 shot_id,不显示 '· 0s'。"""
    from mvstudio.media.helpers import _format_caption

    assert _format_caption({"id": "SH003"}) == "SH003"
    assert _format_caption({"id": "SH003", "duration": 0}) == "SH003"
    assert _format_caption({"id": "SH003", "duration": 5}) == "SH003 · 5s"


@pytest.mark.unit
def test_compose_storyboard_font_path_none_uses_default(tmp_path: Path) -> None:
    """font_path=None → 不 crash,使用 PIL 默认字体(CI 环境保证可用)。"""
    entries = _entries(tmp_path, n=2)
    out = tmp_path / "grid.png"

    result = compose_storyboard(entries, out, font_path=None)

    assert result == out
    assert out.exists()


@pytest.mark.unit
def test_compose_storyboard_broken_font_falls_back(tmp_path: Path) -> None:
    """font_path 指向非字体文件 → 静默 fallback 到默认字体,不 crash。"""
    fake_font = tmp_path / "not_a_font.ttf"
    fake_font.write_bytes(b"not really a font")
    entries = _entries(tmp_path, n=2)
    out = tmp_path / "grid.png"

    result = compose_storyboard(entries, out, font_path=fake_font)

    assert result == out
