#!/usr/bin/env python3
"""风格包 · 每套自己声明色板(取代原来的全局暖板铁律).

原手册把「全暖色板」写成跨风格铁律,连带把水墨/宣纸/卷轴当默认背景库。
那套其实是国乙一年跑两三次的古风限定活动皮,不是通用底。
现代都市线、高奢室内、男团影棚/暗调舞台各有自己的原生色语言,
把它们统一暖化 = 把限定皮当通用底,世界观直接崩。

所以色板下放成风格包属性,每包写清 rationale;
反 AI 味的判据不再是「够不够暖」,而是两条实质规则(见 R2_RULES)。
成片体检走 gate_check_palette.py --declared,查的是「有没有跑出它自己声明的那套」。
"""
from __future__ import annotations

from dataclasses import dataclass, replace

# ---- 暖板常量(古风线沿用,不再是全局铁律)----
CREAM = "#f8f4ea"
GOLD = "#d4af37"
PEACH = "#f4c7c7"
ORANGE = "#ff9a5c"
ROSE = "#f0aa96"
AMBER = "#e6af78"
WARM_WHITE = "#fff6e6"
INK = "#4a3426"
PAPER = "#efe0b0"
VERMILION = "#c0392b"

R2_RULES = """R2 · 反 AI 味的两条实质规则(取代「必须全暖」):
  ① 禁 Linear/Vercel/Cursor 式开发者工具暗色气质
     (自造 #0a0e14/#141922 一类冷蓝灰画布 + 克制 accent + 高对比无质感)。
  ② 禁无意义赛博紫青渐变(#bd93f9/#ff79c6/#8be9fd 三件套及其渐变)。
  冷色本身不违规——夜戏、雨戏、暗调舞台、角色主色是蓝/青/紫,
  都是题材原生语言。判据是「这颜色是不是这个世界该有的」,不是「暖不暖」。
"""

# 立绘肤色/发色跑不掉,R1 规定像素零改动 → 声明色板必须把它们算进去
DEFAULT_SKIN = ("#f2d3bd", "#e0b49b", "#c08e73")


@dataclass(frozen=True)
class Palette:
    """一套风格包声明的色板。gate 只认这里写的。

    main/aux/accent/ink 是**画面**角色(底色/次色/强调/暗部),
    fg/fg_dim 是**文字**角色。两者必须分开——暗调包的 main 就是深色画布本身,
    拿它当文字色等于把字画进背景里。
    """

    main: str
    aux: str
    accent: str
    ink: str
    fg: str  # 主文字色,必须与该包背景有足够反差
    fg_dim: str  # 次级文字色(meta/micro 层)
    extra: tuple[str, ...] = ()

    def declared(
        self,
        character_color: str | tuple[str, ...] | None = None,
        skin: tuple[str, ...] = DEFAULT_SKIN,
    ) -> tuple[str, ...]:
        """交给 gate 的完整声明色板。

        character_color: 角色主题色(萧逸深蓝 / 齐司礼青 / 查理苏紫 一类)。
        它压过风格包基色——角色身份标识优先于包装配色。
        """
        chars: tuple[str, ...] = ()
        if isinstance(character_color, str):
            chars = (character_color,)
        elif character_color:
            chars = tuple(character_color)
        return (self.main, self.aux, self.accent, self.ink, self.fg, self.fg_dim,
                *self.extra, *chars, *skin)

    def gate_arg(self, character_color=None, skin=DEFAULT_SKIN) -> str:
        """拼成 gate_check_palette.py --declared 的入参。"""
        return ",".join(self.declared(character_color, skin))


@dataclass(frozen=True)
class StylePack:
    """一套完整包装配方。立绘像素都不变,只换外层。"""

    name: str
    genre: str  # 古风国乙 / 现代国乙 / 男团 / 通用
    tagline: str
    palette: Palette
    rationale: str  # 为什么是这套色 —— 取代「全暖」的举证义务
    background: str  # backgrounds.BACKGROUNDS 的键
    frame: str  # none / letterbox / scroll / gilded / corner_only
    film: str  # heavy / medium / soft / paper / clean
    light: str  # single_ray / diffuse / gold_dust / bokeh_glow / minimal / hard_rim
    type_style: str  # poster.LAYOUTS 的键前缀
    beat_bias: str
    letterbox_ratio: float = 0.0
    grain_amp: float = 0.04
    bloom_strength: float = 0.5
    particle_density: float = 0.3
    levels: tuple[str, ...] = ()  # 适配的七级支线

    def with_character(self, color: str) -> "StylePack":
        """角色主题色覆盖 accent —— 角色身份优先于风格包基色。"""
        return replace(self, palette=replace(self.palette, accent=color))


_GUFENG = "古风国乙"
_MODERN = "现代国乙"
_BOYGROUP = "男团"

PACKS: dict[str, StylePack] = {
    "cinematic-letterbox": StylePack(
        name="cinematic-letterbox",
        genre="通用",
        tagline="克制、高级、留白多,靠光影和运动撑场",
        palette=Palette(CREAM, AMBER, GOLD, INK, fg=WARM_WHITE, fg_dim="#c9ab86"),
        rationale="低饱和暖褐是电影调色的中性底,不带题材指向,古今都能压住。",
        background="bokeh_light_gradient",
        frame="letterbox",
        film="heavy",
        light="single_ray",
        type_style="minimal",
        beat_bias="cut_punch",
        letterbox_ratio=2.35,
        grain_amp=0.07,
        bloom_strength=0.45,
        particle_density=0.08,
        levels=("L5", "L7"),
    ),
    "ink-scroll": StylePack(
        name="ink-scroll",
        genre=_GUFENG,
        tagline="宣纸水墨 + 卷轴装裱,最国风、装饰最满",
        palette=Palette(PAPER, INK, VERMILION, INK, fg=INK, fg_dim="#8a7358", extra=(GOLD,)),
        rationale="宣纸米黄 + 墨褐 + 朱砂是古画本身的材料色,不是设计选择。"
        "只用于古风限定/非遗联动/古代副本,现代设定套这套是世界观穿帮。",
        background="ink_scroll",
        frame="scroll",
        film="paper",
        light="diffuse",
        type_style="calligraphy_vertical",
        beat_bias="ink_wipe",
        grain_amp=0.05,
        bloom_strength=0.25,
        particle_density=0.25,
        levels=("L2", "L5", "L6-B"),
    ),
    "gongbi-vermilion": StylePack(
        name="gongbi-vermilion",
        genre=_GUFENG,
        tagline="传统重彩工笔,浓艳华丽金碧辉煌",
        palette=Palette(PEACH, VERMILION, GOLD, INK, fg=INK, fg_dim="#9c6b55", extra=(ROSE,)),
        rationale="工笔重彩的矿物颜料色(朱砂/石青对位的暖侧/真金),华服神话题材原生。",
        background="ink_scroll",
        frame="gilded",
        film="soft",
        light="gold_dust",
        type_style="gilded",
        beat_bias="gold_burst",
        grain_amp=0.02,
        bloom_strength=0.8,
        particle_density=0.9,
        levels=("L3-A", "L6-C", "L7-C"),
    ),
    "modern-magazine": StylePack(
        name="modern-magazine",
        genre=_MODERN,
        tagline="无框满画幅 + 大字排版冲击,年轻、快",
        palette=Palette(WARM_WHITE, ORANGE, GOLD, INK, fg=INK, fg_dim="#8a7b6b"),
        rationale="杂志白底高对比,让排版而非配色承担识别度。",
        background="flat_color_negative_space",
        frame="none",
        film="medium",
        light="diffuse",
        type_style="big_type",
        beat_bias="max_kinetic",
        grain_amp=0.05,
        bloom_strength=0.4,
        particle_density=0.4,
        levels=("L3", "L4"),
    ),
    "dream-glow": StylePack(
        name="dream-glow",
        genre="通用",
        tagline="梦幻柔焦、光晕流动,唯美抒情向",
        palette=Palette(WARM_WHITE, AMBER, GOLD, INK, fg=INK, fg_dim="#a8896a", extra=(PEACH,)),
        rationale="暖金梦幻:一切都在发光,靠光而不是硬切推进。",
        background="bokeh_light_gradient",
        frame="corner_only",
        film="soft",
        light="bokeh_glow",
        type_style="minimal",
        beat_bias="glow_pulse",
        grain_amp=0.02,
        bloom_strength=0.95,
        particle_density=0.7,
        levels=("L2-A", "L3-A", "L6-A"),
    ),
    "zen-void": StylePack(
        name="zen-void",
        genre=_GUFENG,
        tagline="极致留白、近单色,用静和空制造高级感",
        palette=Palette(CREAM, INK, VERMILION, INK, fg=INK, fg_dim="#9a8b78"),
        rationale="近单色宣纸,留白本身是内容;节奏最慢,适合前奏/间奏/收尾。",
        background="material_texture",
        frame="none",
        film="paper",
        light="minimal",
        type_style="zen",
        beat_bias="slow",
        grain_amp=0.03,
        bloom_strength=0.15,
        particle_density=0.05,
        levels=("L1", "L5-B"),
    ),
    # ---- 现代国乙线(取代把水墨当默认底)----
    "urban-night": StylePack(
        name="urban-night",
        genre=_MODERN,
        tagline="都市夜景虚化霓虹,现代 AU 主线日常卡",
        palette=Palette("#1b1f27", "#7fb3d5", "#e8a04a", "#0d1014",
                        fg="#f2e2c4", fg_dim="#a89880", extra=("#c94f4f",)),
        rationale="夜城的原生光源是钠灯暖橙 + 玻璃幕墙冷反光,冷暖同框才是真的夜。"
        "这是题材原生语言,不是自造深色画布——底色带城市光污染的褐调,"
        "不是 #0a0e14 那种无质感冷蓝灰。冷蓝放 aux(反光,退到背景里),"
        "accent 给钠灯暖橙——大字用暖橙不用冷蓝,否则就滑回赛博霓虹那套。见 R2_RULES。",
        background="urban_night_neon",
        frame="letterbox",
        film="medium",
        light="hard_rim",
        type_style="big_type",
        beat_bias="cut_punch",
        letterbox_ratio=2.35,
        grain_amp=0.08,
        bloom_strength=0.7,
        particle_density=0.25,
        levels=("L3", "L5", "L6-B"),
    ),
    "luxe-interior": StylePack(
        name="luxe-interior",
        genre=_MODERN,
        tagline="高奢室内暖光,矜贵成熟男主约会/家宴场",
        palette=Palette("#f0e3d0", "#b98a52", GOLD, "#3a2b21",
                        fg="#f6ece0", fg_dim="#c9a377", extra=("#8c5a3c",)),
        rationale="胡桃木 + 黄铜 + 暖白灯带,高端室内摄影的实拍色,不是滤镜。",
        background="luxury_interior_warm",
        frame="corner_only",
        film="soft",
        light="diffuse",
        type_style="minimal",
        grain_amp=0.03,
        beat_bias="glow_pulse",
        bloom_strength=0.6,
        particle_density=0.15,
        levels=("L2", "L5"),
    ),
    "starfield-epic": StylePack(
        name="starfield-epic",
        genre=_MODERN,
        tagline="星海/异空间,幻想线与高光副歌",
        palette=Palette("#141826", "#4e6ea8", "#f4d58d", "#080a12",
                        fg="#f2f0ea", fg_dim="#a8c4e8", extra=("#e8955c",)),
        rationale="星空是具体天体,不是紫青渐变;暖金星点 + 靛蓝夜空是天文实拍色。"
        "蓝在这里是天空不是套路色板。",
        background="particle_starfield",
        frame="none",
        film="clean",
        light="bokeh_glow",
        type_style="big_type",
        beat_bias="gold_burst",
        grain_amp=0.03,
        bloom_strength=0.85,
        particle_density=1.0,
        levels=("L4", "L6-C", "L7"),
    ),
    # ---- 男团宣传线(一手物料里出现频率最高的三种)----
    "studio-seamless": StylePack(
        name="studio-seamless",
        genre=_BOYGROUP,
        tagline="纯色影棚 seamless,成员单人/合体识别卡",
        palette=Palette("#e9e4dc", "#c9542f", "#1c1c1c", "#3a3a3a", fg="#1c1c1c", fg_dim="#6b665e"),
        rationale="纯色 seamless 背景纸是男团一手物料出现频率最高的一种,"
        "作用是把注意力全给人和服装。色由本期概念定,常见是单一高饱和纯色。",
        background="studio_seamless",
        frame="none",
        film="clean",
        light="diffuse",
        type_style="big_type",
        beat_bias="max_kinetic",
        grain_amp=0.02,
        bloom_strength=0.3,
        particle_density=0.0,
        levels=("L3", "L4"),
    ),
    "dark-stage": StylePack(
        name="dark-stage",
        genre=_BOYGROUP,
        tagline="暗调舞台 + 烟雾硬光,performance / 主打歌",
        palette=Palette("#111013", "#d8b26a", "#e6e2da", "#050506",
                        fg="#e6e2da", fg_dim="#9a8f7c", extra=("#7a4a2e",)),
        rationale="舞台暗场 + 单侧硬光 + 烟是演出现场的物理条件。"
        "暗是灯没打到的地方,不是自造深色画布;高光是暖钨丝灯不是冷 LED。",
        background="dark_studio_fog",
        frame="letterbox",
        film="heavy",
        light="hard_rim",
        type_style="minimal",
        beat_bias="cut_punch",
        letterbox_ratio=2.0,
        grain_amp=0.09,
        bloom_strength=0.75,
        particle_density=0.35,
        levels=("L4", "L6", "L7"),
    ),
    "industrial-raw": StylePack(
        name="industrial-raw",
        genre=_BOYGROUP,
        tagline="水泥/金属粗粝质感,概念照与预告",
        palette=Palette("#b7b0a6", "#6e6862", "#c2452d", "#2b2926", fg="#2b2926", fg_dim="#5c574f"),
        rationale="清水混凝土 + 锈迹金属的材质本色,靠肌理而非配色出高级感。",
        background="industrial_concrete",
        frame="corner_only",
        film="heavy",
        light="hard_rim",
        type_style="big_type",
        beat_bias="cut_punch",
        grain_amp=0.10,
        bloom_strength=0.25,
        particle_density=0.1,
        levels=("L3", "L5"),
    ),
    "flat-graphic": StylePack(
        name="flat-graphic",
        genre="通用",
        tagline="平面大色块 + 负空间,海报感最强",
        palette=Palette("#f2ece1", "#22252b", "#d8542f", "#101215", fg="#101215", fg_dim="#6a655c"),
        rationale="单一大色块 + 大留白,厚度全靠排版层级而不是特效。",
        background="flat_color_negative_space",
        frame="none",
        film="clean",
        light="minimal",
        type_style="poster_grid",
        beat_bias="cut_punch",
        grain_amp=0.02,
        bloom_strength=0.2,
        particle_density=0.0,
        levels=("L1", "L3", "L5"),
    ),
    "liminal-dream": StylePack(
        name="liminal-dream",
        genre=_MODERN,
        tagline="失焦雾面/梦核,回忆与破防段",
        palette=Palette("#e6dcd0", "#b9a894", "#d8a06a", "#6b5c4d", fg="#5a4a3c", fg_dim="#907f6d"),
        rationale="过曝雾面是记忆的视觉隐喻;低对比高亮度,靠形状不靠边缘。",
        background="liminal_dreamcore",
        frame="none",
        film="soft",
        light="minimal",
        type_style="zen",
        beat_bias="slow",
        grain_amp=0.06,
        bloom_strength=0.9,
        particle_density=0.1,
        levels=("L1", "L2-C", "L6-B"),
    ),
}


def get(name: str) -> StylePack:
    if name not in PACKS:
        raise KeyError(f"未知风格包 {name!r};可用: {', '.join(sorted(PACKS))}")
    return PACKS[name]


def by_genre(genre: str) -> list[StylePack]:
    return [p for p in PACKS.values() if p.genre in (genre, "通用")]


if __name__ == "__main__":
    print(R2_RULES)
    for g in (_GUFENG, _MODERN, _BOYGROUP):
        print(f"\n== {g} ==")
        for p in PACKS.values():
            if p.genre == g:
                print(f"  {p.name:20} bg={p.background:26} {p.tagline}")
    print("\n示例 gate 入参(urban-night + 萧逸深蓝):")
    print("  " + get("urban-night").palette.gate_arg("#1b3a6b"))
