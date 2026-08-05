"""艺术字样式库 · 可查表的国风艺术字参数(纯样式参数,不含 PIL 画法).

`paperdoll_engine.py` 里的标题字/歌词字/印章原语（`_seal` / `_title_char` /
`_lyric_char`）原来把颜色、字体写死成模块级常量（GOLD/INK/SEAL_RED/...）。
本模块把这些参数抽成可查表的 `ArtTextStyle`，引擎按 `Shot.art_style` 查表取值，
画法本身仍留在引擎里 —— 这里只是样式参数库 + 未来新画法（如 neon/flat）的
renderer 名字注册表，不重复实现 PIL 绘制逻辑。

默认样式「金墨朱砂」的参数与引擎里原硬编码值逐字节对应，保证接线后行为不变。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

# 与 paperdoll_engine.py 的 ROOT 定义等价，指向仓库根
# （本文件比 paperdoll_engine.py 多一层 artstyle/ 目录，故 parents 多取一层）
ROOT = Path(__file__).resolve().parents[3]


def _first_font(*cands: str) -> str:
    """返回第一个存在的字体路径；全缺则回退系统苹方（保证不崩）。
    与 paperdoll_engine.py 第 49 行同款逻辑，供 title_fonts/lyric_fonts 解析用。"""
    for c in cands:
        if c and Path(c).exists():
            return c
    return "/System/Library/Fonts/PingFang.ttc"


@dataclass(frozen=True)
class ArtTextStyle:
    """一套艺术字风格的完整参数（颜色/字体/画法绑定），供引擎查表读取。"""

    name: str                    # 样式名（映射键），如 "金墨朱砂"
    prompt: str                  # 自然语言样式描述（给用户选/给 LLM 看）
    renderer: str                # 绑定哪个渲染方法名，如 "stroke_glow"
    ink: tuple                   # 字芯色 RGB
    outline: tuple                # 描边色 RGB
    seal_color: tuple            # 印章色 RGB
    warm_white: tuple            # 反白/浅色
    title_fonts: list = field(default_factory=list)   # 标题字体回退链（路径候选）
    lyric_fonts: list = field(default_factory=list)   # 歌词字体回退链
    glow: bool = True            # 是否金辉光晕
    seal: bool = True            # 是否朱砂印章

    def resolved_title_font(self) -> str:
        """解析标题字体回退链为实际可用路径。"""
        return _first_font(*self.title_fonts)

    def resolved_lyric_font(self) -> str:
        """解析歌词字体回退链为实际可用路径。"""
        return _first_font(*self.lyric_fonts)


STYLES: dict[str, ArtTextStyle] = {
    "金墨朱砂": ArtTextStyle(
        name="金墨朱砂",
        prompt=(
            "国风行草艺术字：金色 (212,175,55) 八向描边双钩勾边、墨色 (74,52,38) "
            "字芯填充、朱砂 (176,42,34) 圆角方印反白落款、暖金辉光晕；标题用宋体/"
            "黑体，歌词用马善政行草飘逸手写体；全暖色系，严禁蓝紫冷色（遵守项目"
            "禁蓝紫铁律）。"
        ),
        renderer="stroke_glow",
        ink=(74, 52, 38),
        outline=(212, 175, 55),
        seal_color=(176, 42, 34),
        warm_white=(255, 246, 230),
        title_fonts=[
            "/System/Library/Fonts/Supplemental/Songti.ttc",
            "/System/Library/Fonts/STHeiti Medium.ttc",
        ],
        lyric_fonts=[
            str(ROOT / "assets/fonts/MaShanZheng-Regular.ttf"),
            str(ROOT / "assets/fonts/ZCOOLXiaoWei-Regular.ttf"),
            "/System/Library/Fonts/Supplemental/Songti.ttc",
            "/System/Library/Fonts/STHeiti Medium.ttc",
        ],
        glow=True,
        seal=True,
    ),
}


def get_style(name: str) -> ArtTextStyle:
    """查 STYLES；找不到回退默认样式「金墨朱砂」（不抛异常，保证不崩）。"""
    return STYLES.get(name, STYLES["金墨朱砂"])


# renderer 名字 → 画法实现的注册表。
# 实际画法在 paperdoll_engine.py 的 _title_char/_lyric_char/_seal 里，本表
# 只预留给未来新画法（如 neon 霓虹描边、flat 无描边平涂）扩展；当前只登记
# "stroke_glow" 一个键，值先占位为 None（画法留在引擎，不在此重复实现）。
RENDERERS: dict[str, object] = {
    "stroke_glow": None,  # 现有画法：_title_char/_lyric_char/_seal（金描边+墨填+金辉光晕+朱砂印）
}
