"""resolve_cjk_font 单元测试 · 覆盖 CI 无字体和用户机有字体两种场景。"""
from __future__ import annotations

from pathlib import Path

import pytest

from mvstudio.media import resolve_cjk_font


@pytest.mark.unit
def test_resolve_cjk_font_returns_path_or_none() -> None:
    """真实调用:结果要么是存在的文件,要么是 None。"""
    result = resolve_cjk_font()
    assert result is None or (isinstance(result, Path) and result.exists())


@pytest.mark.unit
def test_resolve_cjk_font_empty_chain_returns_none(tmp_path: Path) -> None:
    """全部候选都不存在时返回 None,给 caller 走 PIL 默认字体。"""
    result = resolve_cjk_font(chain=[tmp_path / "nope1.ttf", tmp_path / "nope2.otf"])
    assert result is None


@pytest.mark.unit
def test_resolve_cjk_font_picks_first_existing(tmp_path: Path) -> None:
    """按优先级返回第一个存在的字体路径。"""
    missing = tmp_path / "missing.ttf"
    real = tmp_path / "real.ttf"
    real.write_bytes(b"fake bytes but the file exists")

    result = resolve_cjk_font(chain=[missing, real])
    assert result == real
