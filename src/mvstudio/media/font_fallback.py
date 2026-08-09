"""CJK 字体 fallback 解析 · mvstudio 层独立(不 import paperdoll)。

storyboard 拼图等 mvstudio 层的图像合成用这里的 resolve_cjk_font()。
链上常量参考 pipeline/paperdoll/fonts.py 但**不 import**——mvstudio 是下层,
不能反向依赖 pipeline/。全部候选都找不到时返回 None,caller 用 PIL 默认字体。
"""
from __future__ import annotations

from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_FONT_DIR = _PROJECT_ROOT / "assets" / "fonts"
_USER_FONTS = Path.home() / "Library" / "Fonts"
_SYS_FONTS = Path("/System/Library/Fonts")

# CJK-capable 字体 fallback 链(优先级从高到低)
_CJK_FALLBACK_CHAIN: list[Path] = [
    _FONT_DIR / "SmileySans-Oblique.ttf",
    _FONT_DIR / "SmileySans-Oblique.otf",
    _FONT_DIR / "LXGWWenKai-Regular.ttf",
    _USER_FONTS / "SourceHanSansSC-Normal.otf",
    _SYS_FONTS / "PingFang.ttc",
    Path("/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"),
]


def resolve_cjk_font(chain: list[Path] | None = None) -> Path | None:
    """返回 fallback 链中第一个存在的 CJK 字体路径;全找不到返回 None。

    chain 参数便于测试时替换。生产调用无需传参。
    """
    for path in (chain if chain is not None else _CJK_FALLBACK_CHAIN):
        if path.exists():
            return path
    return None
