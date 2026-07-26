#!/usr/bin/env python3
"""艺术字 · 海报排版层 · 内容厚度的真正来源.

厚度不是特效堆出来的。渐变+外发光+投影+描边四件套只会让画面显得廉价,
根因是「用效果补层级不够」——和 R9「构图动 > 特效动」是同一条原理。

真正让画面变厚的是**信息层级数**:
    2 层(标题 + 歌词)= 薄。5-7 层 = 海报感。
    字号跨度 ≥6:1(最大字 / 最小字),小于这个数说明层级在打架不在分工。

七个标准层(不必全用,但少于 5 层过不了 §10 的层级计数门):
    hero      主字(角色名/歌名),画面最大的东西
    hero_sub  主字副行(拼音/英文/罗马音),贴着 hero 走
    label     身份标签(定位/CP/期数),中号
    lyric     歌词/文案行
    meta      元信息(日期/厂牌/专辑)
    micro     极小等宽层(编号/时间码/坐标)—— 最便宜的厚度来源
    seal      印章/徽标

排版与立绘咬合(三明治):背景 → behind 层大字 → 立绘 → 前景层。
大字被立绘挡住一截,才是海报;全部浮在人前面是字幕不是海报。
"""
from __future__ import annotations

import unicodedata
from dataclasses import dataclass, replace

from PIL import Image, ImageDraw

from . import fonts
from .style_packs import StylePack

# 七层的相对字号(占画布高的比例)。跨度 hero/micro = 0.20/0.012 ≈ 16:1
TIER_ORDER = ("hero", "hero_sub", "label", "lyric", "meta", "micro", "seal")


@dataclass(frozen=True)
class Slot:
    """一个排版位。size/pos 都是归一化值,换画幅时重排而不是 resize。"""

    role: str  # fonts.py 的字体角色
    size: float  # 占画布高的比例
    pos: tuple[float, float]  # 锚点,归一化
    align: str = "lt"  # l/m/r + t/m/b
    color: str = "fg"  # 文字角色(fg/fg_dim/accent)或字面 hex
    tracking: float = 0.0  # 字距,em 倍数
    vertical: bool = False  # 竖排(CJK)
    behind: bool = False  # 压在立绘后面
    opacity: float = 1.0
    line_gap: float = 1.25


@dataclass(frozen=True)
class PosterLayout:
    name: str
    kind: str  # single / duo / group
    rule: str  # 这套版式为什么这么排
    slots: dict[str, Slot]
    dolls: tuple[tuple[float, float, float], ...] = ()  # (锚点x, 底边y, 高占画布比)

    def size_span(self) -> float:
        sizes = [s.size for s in self.slots.values()]
        return max(sizes) / min(sizes)

    def place(self, n: int) -> list[tuple[tuple[float, float], float]]:
        """给 n 个立绘算落位——**落位属于版式,不属于调用方**。

        谁站哪、站多高是构图决定的:baseline-strip 的人必须停在字条上沿,
        vertical-name 的人必须让开右侧竖排。让调用方每次现猜等于每次重新设计版式,
        也是「同一套版式在不同片子里长得不一样」的来源。

        group 版式按实际人数重排横向分布(成员数每期不同),高度/底边循环取声明的错落节奏。
        """
        if not self.dolls:
            raise ValueError(f"版式 {self.name} 没声明立绘落位")
        if self.kind != "group":
            if n != len(self.dolls):
                raise ValueError(
                    f"{self.name} 是 {self.kind} 版式,要 {len(self.dolls)} 个立绘,给了 {n}")
            return [((x, b), h) for x, b, h in self.dolls]

        xs = [d[0] for d in self.dolls]
        lo, hi = min(xs), max(xs)
        out = []
        for i in range(n):
            _, base, h = self.dolls[i % len(self.dolls)]
            t = 0.5 if n == 1 else i / (n - 1)
            out.append(((lo + (hi - lo) * t, base), h))
        return out


# ---------------------------------------------------------------- 混排测量

def _is_cjk(ch: str) -> bool:
    if ch in "，。、；：？！「」『』（）《》——…·":
        return True
    return unicodedata.east_asian_width(ch) in ("W", "F")


def _runs(text: str) -> list[tuple[str, bool]]:
    """切成 [(片段, 是否CJK)],让中西文各用各的字体。"""
    out: list[tuple[str, bool]] = []
    for ch in text:
        cjk = _is_cjk(ch)
        if out and out[-1][1] == cjk:
            out[-1] = (out[-1][0] + ch, cjk)
        else:
            out.append((ch, cjk))
    return out


def _measure(text: str, cjk_f, lat_f, tracking: float, em: int) -> int:
    w = 0
    for seg, cjk in _runs(text):
        f = cjk_f if cjk else lat_f
        w += f.getlength(seg) + tracking * em * len(seg)
    return round(w)


def _draw_line(d: ImageDraw.ImageDraw, xy, text, cjk_f, lat_f, fill,
               tracking: float, em: int) -> None:
    """混排绘制。

    CJK 没有基线概念,按字面框视觉中心对齐;拉丁有基线,在 PIL 里
    直接同 y 画会显得偏高,补 -0.06em 才和汉字对齐。
    """
    x, y = xy
    for seg, cjk in _runs(text):
        f = cjk_f if cjk else lat_f
        dy = 0 if cjk else -em * 0.06
        if tracking:
            for ch in seg:
                d.text((x, y + dy), ch, font=f, fill=fill)
                x += f.getlength(ch) + tracking * em
        else:
            d.text((x, y + dy), seg, font=f, fill=fill)
            x += f.getlength(seg)


def _color(spec: str, pack: StylePack) -> str:
    if spec.startswith("#"):
        return spec
    return getattr(pack.palette, spec)


def draw_slot(canvas: Image.Image, slot: Slot, text: str, pack: StylePack) -> None:
    """把一个排版位画到画布(RGBA)上。多行用 \\n 分隔。"""
    if not text:
        return
    w, h = canvas.size
    em = max(8, round(slot.size * h))
    cjk_f = fonts.load(slot.role, em)
    lat_f = fonts.load("latin", em)
    fill = _color(slot.color, pack)

    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    ax, ay = slot.pos[0] * w, slot.pos[1] * h

    if slot.vertical:
        step = em * slot.line_gap
        total = step * len(text)
        y = ay - total * {"t": 0.0, "m": 0.5, "b": 1.0}[slot.align[1]]
        for ch in text:
            cw = cjk_f.getlength(ch) if _is_cjk(ch) else lat_f.getlength(ch)
            x = ax - cw * {"l": 0.0, "m": 0.5, "r": 1.0}[slot.align[0]]
            _draw_line(d, (x, y), ch, cjk_f, lat_f, fill, 0.0, em)
            y += step
    else:
        lines = text.split("\n")
        step = em * slot.line_gap
        y = ay - step * len(lines) * {"t": 0.0, "m": 0.5, "b": 1.0}[slot.align[1]]
        for line in lines:
            lw = _measure(line, cjk_f, lat_f, slot.tracking, em)
            x = ax - lw * {"l": 0.0, "m": 0.5, "r": 1.0}[slot.align[0]]
            _draw_line(d, (x, y), line, cjk_f, lat_f, fill, slot.tracking, em)
            y += step

    if slot.opacity < 1.0:
        a = layer.getchannel("A").point(lambda v: round(v * slot.opacity))
        layer.putalpha(a)
    canvas.alpha_composite(layer)


def render_poster(
    background: Image.Image,
    dolls: list[Image.Image],
    layout: PosterLayout,
    content: dict[str, str],
    pack: StylePack,
) -> Image.Image:
    """三明治合成:背景 → behind 大字 → 立绘 → 前景排版。

    dolls 按顺序落到 layout.place() 声明的位上;立绘只做等比缩放 + 落位,
    像素零改动(R1)。
    """
    canvas = background.convert("RGBA")
    w, h = canvas.size

    for name, slot in layout.slots.items():
        if slot.behind:
            draw_slot(canvas, slot, content.get(name, ""), pack)

    for doll, ((dx, dy), dh) in zip(dolls, layout.place(len(dolls))):
        target_h = round(dh * h)
        scale = target_h / doll.height
        d = doll.resize((round(doll.width * scale), target_h), Image.LANCZOS)
        canvas.alpha_composite(d, (round(dx * w - d.width / 2), round(dy * h - d.height)))

    for name, slot in layout.slots.items():
        if not slot.behind:
            draw_slot(canvas, slot, content.get(name, ""), pack)
    return canvas


# ------------------------------------------------------- 版式库 · 单人 6 套

LAYOUTS: dict[str, PosterLayout] = {
    "single-vertical-name": PosterLayout(
        name="single-vertical-name", kind="single",
        rule="竖排大名贴右缘,人物偏左——竖排是汉字独有的版式资源,横排海报做不出这个纵向压迫感。",
        slots={
            "hero": Slot("display_kai", 0.115, (0.88, 0.14), "mt", "accent",
                         vertical=True, line_gap=1.06),
            "hero_sub": Slot("latin", 0.026, (0.735, 0.16), "lt", "fg_dim", tracking=0.34),
            "label": Slot("body_bold", 0.030, (0.10, 0.20), "lt", "fg", tracking=0.12),
            "lyric": Slot("body", 0.036, (0.10, 0.845), "lb", "fg", line_gap=1.5),
            "meta": Slot("body", 0.018, (0.10, 0.935), "lb", "fg_dim", tracking=0.06),
            "micro": Slot("micro", 0.0125, (0.90, 0.955), "rb", "fg_dim", tracking=0.18),
        },
        dolls=((0.36, 0.995, 0.86),),  # 人偏左让开右侧竖排,几乎顶满高度
    ),
    "single-stacked-hero": PosterLayout(
        name="single-stacked-hero", kind="single",
        rule="巨大横排名字压顶,人物从字后穿出——被遮挡才是海报,全浮在前面只是字幕。",
        slots={
            "hero": Slot("display", 0.205, (0.5, 0.30), "mm", "accent",
                         tracking=-0.02, behind=True),
            "hero_sub": Slot("latin", 0.030, (0.5, 0.395), "mm", "fg", tracking=0.42),
            "label": Slot("body_bold", 0.026, (0.5, 0.115), "mm", "fg_dim", tracking=0.30),
            "lyric": Slot("body", 0.034, (0.5, 0.885), "mb", "fg", line_gap=1.45),
            "meta": Slot("body", 0.017, (0.5, 0.945), "mb", "fg_dim", tracking=0.10),
            "micro": Slot("micro", 0.012, (0.055, 0.955), "lb", "fg_dim", tracking=0.15),
        },
        dolls=((0.5, 1.0, 0.82),),  # 居中,头部从 hero 大字里穿出来
    ),
    "single-side-column": PosterLayout(
        name="single-side-column", kind="single",
        rule="左窄栏塞满层级、右侧大留白给人——信息密度和呼吸量同时拉满,杂志封面常用。",
        slots={
            "hero": Slot("heavy", 0.088, (0.075, 0.30), "lm", "fg", line_gap=0.98),
            "hero_sub": Slot("latin", 0.022, (0.075, 0.375), "lt", "accent", tracking=0.30),
            "label": Slot("body_bold", 0.024, (0.075, 0.44), "lt", "fg_dim", tracking=0.14),
            "lyric": Slot("body", 0.026, (0.075, 0.545), "lt", "fg", line_gap=1.55),
            "meta": Slot("body", 0.016, (0.075, 0.90), "lb", "fg_dim", line_gap=1.4),
            "micro": Slot("micro", 0.0115, (0.075, 0.945), "lb", "fg_dim", tracking=0.22),
        },
        dolls=((0.68, 1.0, 0.90),),  # 人贴右,左栏留给密集层级
    ),
    "single-baseline-strip": PosterLayout(
        name="single-baseline-strip", kind="single",
        rule="信息全压底部条带,上方净空——电影主视觉的排法,靠人物剪影和留白说话。",
        slots={
            "hero": Slot("display_serif", 0.078, (0.5, 0.795), "mt", "fg", tracking=0.05),
            "hero_sub": Slot("latin", 0.020, (0.5, 0.875), "mt", "accent", tracking=0.52),
            "label": Slot("body_bold", 0.019, (0.5, 0.075), "mt", "fg_dim", tracking=0.42),
            "lyric": Slot("body", 0.030, (0.5, 0.715), "mb", "fg"),
            "meta": Slot("body", 0.0145, (0.5, 0.945), "mt", "fg_dim",
                         tracking=0.08, line_gap=1.35),
            "micro": Slot("micro", 0.011, (0.945, 0.055), "rt", "fg_dim", tracking=0.20),
        },
        # 底边停在字条上沿(lyric 在 0.715),满高立绘会把整条信息压掉
        dolls=((0.5, 0.70, 0.62),),
    ),
    "single-poster-grid": PosterLayout(
        name="single-poster-grid", kind="single",
        rule="四角挂元信息 + 中轴大字,网格感最强——平面设计味,厚度全来自层级不是特效。",
        slots={
            "hero": Slot("heavy", 0.155, (0.5, 0.475), "mm", "accent",
                         tracking=-0.015, behind=True),
            "hero_sub": Slot("latin", 0.024, (0.5, 0.565), "mm", "fg", tracking=0.48),
            "label": Slot("body_bold", 0.022, (0.055, 0.075), "lt", "fg", tracking=0.24),
            "lyric": Slot("body", 0.028, (0.945, 0.855), "rb", "fg", line_gap=1.5),
            "meta": Slot("body", 0.015, (0.945, 0.075), "rt", "fg_dim", tracking=0.10),
            "micro": Slot("micro", 0.0115, (0.055, 0.945), "lb", "fg_dim", tracking=0.24),
            "seal": Slot("display_kai", 0.042, (0.90, 0.50), "mm", "accent"),
        },
        dolls=((0.5, 0.98, 0.78),),
    ),
    "single-zen-void": PosterLayout(
        name="single-zen-void", kind="single",
        rule="极简三层 + 大量空白,人物偏置黄金分割位——**唯一允许少于 5 层的版式**,"
             "留白本身是内容,但只用于前奏/间奏/收尾这类静段,不能全片这么排。",
        slots={
            "hero": Slot("display_kai", 0.072, (0.80, 0.20), "mt", "fg",
                         vertical=True, line_gap=1.35),
            "lyric": Slot("body", 0.028, (0.16, 0.86), "lb", "fg", line_gap=1.7),
            "seal": Slot("display_kai", 0.034, (0.80, 0.62), "mm", "accent"),
        },
        dolls=((0.34, 0.97, 0.72),),  # 偏置到左侧黄金分割位,右上留白给竖排
    ),
    # ------------------------------------------------- 多人 3 套
    "duo-split": PosterLayout(
        name="duo-split", kind="duo",
        rule="双人左右分立、中缝竖排 CP 名——中缝把两人绑在一起,"
             "两人各自贴自己那侧的名牌,谁是谁一眼分清(双人图最容易糊的就是这个)。",
        slots={
            "hero": Slot("display_kai", 0.082, (0.5, 0.22), "mt", "accent",
                         vertical=True, line_gap=1.10),
            "hero_sub": Slot("latin", 0.021, (0.5, 0.735), "mt", "fg", tracking=0.40),
            "name_l": Slot("body_bold", 0.032, (0.145, 0.885), "lb", "fg", tracking=0.14),
            "name_r": Slot("body_bold", 0.032, (0.855, 0.885), "rb", "fg", tracking=0.14),
            "label": Slot("body_bold", 0.020, (0.5, 0.085), "mt", "fg_dim", tracking=0.36),
            "lyric": Slot("body", 0.026, (0.5, 0.935), "mb", "fg"),
            "micro": Slot("micro", 0.011, (0.055, 0.955), "lb", "fg_dim", tracking=0.20),
        },
        dolls=((0.235, 0.99, 0.80), (0.765, 0.99, 0.80)),  # 左右分立,中缝留给竖排 CP 名
    ),
    "group-grid": PosterLayout(
        name="group-grid", kind="group",
        rule="成员均分格 + 逐人编号名牌——男团一手物料的标准排法,"
             "编号层几乎不占视觉重量却立刻加一层厚度,还解决多人辨认问题。",
        slots={
            "hero": Slot("heavy", 0.105, (0.5, 0.088), "mt", "accent", tracking=-0.01),
            "hero_sub": Slot("latin", 0.020, (0.5, 0.205), "mt", "fg", tracking=0.50),
            "label": Slot("body_bold", 0.018, (0.055, 0.055), "lt", "fg", tracking=0.28),
            "member_row": Slot("body_bold", 0.023, (0.5, 0.885), "mb", "fg", tracking=0.22),
            "index_row": Slot("micro", 0.013, (0.5, 0.925), "mb", "fg_dim", tracking=0.60),
            "meta": Slot("body", 0.015, (0.945, 0.055), "rt", "fg_dim", tracking=0.10),
            "micro": Slot("micro", 0.011, (0.055, 0.955), "lb", "fg_dim", tracking=0.24),
        },
        # 底边停在名牌行上沿(member_row 0.885),等高排列——网格版式不做错落
        dolls=((0.13, 0.855, 0.60), (0.37, 0.855, 0.60), (0.63, 0.855, 0.60),
               (0.87, 0.855, 0.60)),
    ),
    "group-stack": PosterLayout(
        name="group-stack", kind="group",
        rule="成员错落叠放 + 巨字压在人后——纵深靠遮挡关系而不是缩放,"
             "队名从人群里穿出来,是 performance 主视觉最常见的一种。",
        slots={
            "hero": Slot("display", 0.235, (0.5, 0.40), "mm", "accent",
                         tracking=-0.03, behind=True),
            "hero_sub": Slot("latin", 0.026, (0.5, 0.525), "mm", "fg",
                             tracking=0.46, behind=True),
            "label": Slot("body_bold", 0.021, (0.5, 0.075), "mt", "fg_dim", tracking=0.34),
            "member_row": Slot("body_bold", 0.021, (0.5, 0.895), "mb", "fg", tracking=0.18),
            "lyric": Slot("body", 0.028, (0.5, 0.845), "mb", "fg"),
            "meta": Slot("body", 0.015, (0.5, 0.945), "mb", "fg_dim", tracking=0.10),
            "micro": Slot("micro", 0.011, (0.945, 0.955), "rb", "fg_dim", tracking=0.20),
        },
        # 高度/底边交替 = 错落;纵深靠遮挡与高低差,不靠透视缩放
        dolls=((0.14, 0.845, 0.62), (0.50, 0.815, 0.70), (0.86, 0.845, 0.62)),
    ),
}


def get(name: str) -> PosterLayout:
    if name not in LAYOUTS:
        raise KeyError(f"未知版式 {name!r};可用: {', '.join(sorted(LAYOUTS))}")
    return LAYOUTS[name]


def by_kind(kind: str) -> list[PosterLayout]:
    return [lay for lay in LAYOUTS.values() if lay.kind == kind]


# ------------------------------------------------------------- 层级计数门

MIN_TIERS = 5
MIN_SPAN = 6.0


def check_thickness(layout: PosterLayout, content: dict[str, str]) -> tuple[bool, str]:
    """§10 第五道机器门:信息层级数 ≥5、字号跨度 ≥6:1。

    zen-void 一类刻意极简的版式在 rule 里写明豁免理由,单独放行。
    """
    used = [k for k, v in content.items() if v and k in layout.slots]
    sizes = [layout.slots[k].size for k in used]
    if not sizes:
        return False, "没有任何排版位有内容"
    span = max(sizes) / min(sizes)
    exempt = layout.name == "single-zen-void"

    if len(used) < MIN_TIERS and not exempt:
        return False, (
            f"信息层级只有 {len(used)} 层(门槛 {MIN_TIERS})。"
            f"缺的层: {[t for t in TIER_ORDER if t in layout.slots and t not in used]}。"
            "加层级,不要靠加特效补厚度。")
    if span < MIN_SPAN and not exempt:
        return False, (
            f"字号跨度只有 {span:.1f}:1(门槛 {MIN_SPAN}:1)。"
            "层级在打架不在分工——把主字加大或把 micro 层缩小。")
    return True, f"{len(used)} 层 · 跨度 {span:.1f}:1" + ("(zen 豁免)" if exempt else "")


if __name__ == "__main__":
    for lay in LAYOUTS.values():
        print(f"{lay.kind:6} {lay.name:22} 层={len(lay.slots)} 跨度={lay.size_span():.1f}:1")
        print(f"       {lay.rule}")
