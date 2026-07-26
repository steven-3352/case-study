"""字体注册表：语义角色 → 实际字体文件。

排版代码只应该按角色取字体（`load("display", 120)`），不要在业务代码里写死路径。
换字体只改本文件。

字体来源分三档（授权风险递增）：
  1. SIL OFL（assets/fonts/，由 fetch_fonts.py 下载）——可商用/可嵌入/可改
  2. macOS 系统自带（思源黑体装在 ~/Library/Fonts）——本机可用，不随仓库分发
  3. 厂商声明类（阿里普惠 / OPPO Sans / HarmonyOS Sans）——本项目不自动下载

每个角色给一条回退链，第一个存在的文件胜出；整条链都缺才报错，错误信息里带补救命令。
"""
from __future__ import annotations

import functools
from pathlib import Path

from PIL import ImageFont

ROOT = Path(__file__).resolve().parents[2]
FONT_DIR = ROOT / "assets" / "fonts"
USER_FONTS = Path.home() / "Library" / "Fonts"
SYS_FONTS = Path("/System/Library/Fonts/Supplemental")

# 角色 -> [(路径, ttc 内索引), ...] 回退链
ROLES: dict[str, list[tuple[Path, int]]] = {
    # 潮流/速度感大字。得意黑自带 6° 倾斜，男团/现代国乙主标题首选
    "display": [
        (FONT_DIR / "SmileySans-Oblique.ttf", 0),
        (FONT_DIR / "SmileySans-Oblique.otf", 0),
        (USER_FONTS / "SourceHanSansSC-Heavy.otf", 0),
    ],
    # 高衬线宋体标题。细长笔画+柳叶撇捺 = 爱情/古典气质
    "display_serif": [
        (SYS_FONTS / "Songti.ttc", 3),
        (SYS_FONTS / "Songti.ttc", 0),
    ],
    # 楷体。古风/文艺/书法感，霞鹜文楷是 OFL 里质量最好的开源楷
    "display_kai": [
        (FONT_DIR / "LXGWWenKai-Medium.ttf", 0),
        (FONT_DIR / "LXGWWenKai-Regular.ttf", 0),
        (SYS_FONTS / "Kailasa.ttc", 0),
    ],
    # 超粗黑体骨架，用于压扁大字（scale_y < 1）
    "heavy": [
        (USER_FONTS / "SourceHanSansSC-Heavy.otf", 0),
        (FONT_DIR / "SmileySans-Oblique.ttf", 0),
    ],
    "body_bold": [
        (USER_FONTS / "SourceHanSansSC-Bold.otf", 0),
        (USER_FONTS / "SourceHanSansSC-Heavy.otf", 0),
    ],
    # 歌词/正文
    "body": [
        (USER_FONTS / "SourceHanSansSC-Normal.otf", 0),
        (FONT_DIR / "LXGWWenKai-Regular.ttf", 0),
    ],
    # 小字信息层（编号/日期/credit）。等宽数字对齐才不显乱
    "micro": [
        (SYS_FONTS.parent / "Menlo.ttc", 0),
        (Path("/System/Library/Fonts/Menlo.ttc"), 0),
        (USER_FONTS / "SourceHanSansSC-Normal.otf", 0),
    ],
    # 拉丁大写标语/英文名
    "latin": [
        (Path("/System/Library/Fonts/HelveticaNeue.ttc"), 0),
        (SYS_FONTS / "Futura.ttc", 0),
        (FONT_DIR / "SmileySans-Oblique.ttf", 0),
    ],
}


def resolve(role: str) -> tuple[Path, int]:
    """返回该角色实际可用的 (字体路径, ttc 索引)。整条回退链都缺则抛错。"""
    if role not in ROLES:
        raise KeyError(f"未知字体角色 {role!r}，可用：{sorted(ROLES)}")
    for path, index in ROLES[role]:
        if path.exists():
            return path, index
    tried = "\n  ".join(str(p) for p, _ in ROLES[role])
    raise FileNotFoundError(
        f"字体角色 {role!r} 无可用文件。已尝试：\n  {tried}\n"
        f"补救：python3 {FONT_DIR / 'fetch_fonts.py'}"
    )


@functools.lru_cache(maxsize=256)
def load(role: str, size: int) -> ImageFont.FreeTypeFont:
    """按角色 + 字号取 PIL 字体对象（带缓存，逐帧渲染时不会重复解析字体文件）。"""
    path, index = resolve(role)
    return ImageFont.truetype(str(path), size, index=index)


def audit() -> list[tuple[str, str]]:
    """返回 [(角色, 状态)]，供开工前自检。状态为实际命中的文件名或 MISSING。"""
    report = []
    for role in ROLES:
        try:
            path, _ = resolve(role)
            report.append((role, path.name))
        except FileNotFoundError:
            report.append((role, "MISSING"))
    return report


if __name__ == "__main__":
    width = max(len(r) for r in ROLES)
    for role, status in audit():
        print(f"{role:<{width}}  {status}")
