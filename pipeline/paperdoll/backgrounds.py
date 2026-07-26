#!/usr/bin/env python3
"""背景生成器 · 12 种,水墨只是其中之一.

原来 gen_paperdoll_pv.py 只有 make_moon / make_ridges / clouds 三个国风函数,
等于把「一年跑两三次的古风限定活动皮」当成了通用底。
本模块按题材原生视觉语言补齐:现代国乙 5 种 · 男团 3 种 · 通用 4 种。

统一契约:
    fn(size: (W, H), pack: StylePack, seed: int, **kw) -> PIL.Image (RGB)
全部确定性(同 seed 同结果),无外部素材依赖——除 photoreal_location,
它显式要一张实拍底片,拿不到就报错,不偷偷退化成程序化渐变冒充实拍。
"""
from __future__ import annotations

import pathlib
from typing import Callable

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from .style_packs import StylePack


def _rgb(hex_str: str) -> np.ndarray:
    h = hex_str.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], dtype=np.float64)


def _vgrad(size: tuple[int, int], top: str, bottom: str, gamma: float = 1.0) -> np.ndarray:
    w, h = size
    t = (np.linspace(0, 1, h) ** gamma)[:, None, None]
    return _rgb(top) * (1 - t) + _rgb(bottom) * t + np.zeros((h, w, 3))


def _radial(size: tuple[int, int], cx: float, cy: float, radius: float,
            strength: float) -> np.ndarray:
    """返回 (H,W,1) 的 0..strength 光晕权重。cx/cy/radius 都是归一化值。"""
    w, h = size
    yy, xx = np.mgrid[0:h, 0:w]
    d = np.hypot((xx / w - cx) * (w / h), yy / h - cy) / max(radius, 1e-6)
    return (np.clip(1 - d, 0, 1) ** 2 * strength)[:, :, None]


def _value_noise(size: tuple[int, int], cells: int, rng: np.random.Generator) -> np.ndarray:
    """低频值噪声 (H,W) 0..1,用双线性放大,便宜且够用。"""
    w, h = size
    small = rng.random((max(cells, 2), max(int(cells * w / h), 2)))
    return np.asarray(
        Image.fromarray((small * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC),
        dtype=np.float64,
    ) / 255


def _finish(arr: np.ndarray, grain: float, rng: np.random.Generator) -> Image.Image:
    if grain > 0:
        arr = arr + rng.normal(0, grain * 255, arr.shape)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")


# ---------------------------------------------------------------- 通用 4 种

def bokeh_light_gradient(size, pack: StylePack, seed: int = 0, **kw) -> Image.Image:
    """B类·抽象氛围:暖渐变 + 散景光斑。最省事的起手,任何题材都不出错。"""
    rng = np.random.default_rng(seed)
    w, h = size
    arr = _vgrad(size, pack.palette.main, pack.palette.ink, gamma=1.6)
    arr += _radial(size, 0.5, 0.32, 0.75, 90) * _rgb(pack.palette.aux) / 255

    glow = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(glow)
    n = int(28 * max(pack.particle_density, 0.15))
    for _ in range(n):
        r = rng.uniform(0.02, 0.09) * h
        x, y = rng.uniform(0, w), rng.uniform(0, h)
        d.ellipse([x - r, y - r, x + r, y + r], fill=int(rng.uniform(60, 170)))
    glow = glow.filter(ImageFilter.GaussianBlur(h * 0.012))
    arr += np.asarray(glow, dtype=np.float64)[:, :, None] * _rgb(pack.palette.accent) / 255
    return _finish(arr, pack.grain_amp, rng)


def flat_color_negative_space(size, pack: StylePack, seed: int = 0,
                              block: float = 0.34, **kw) -> Image.Image:
    """平面大色块 + 负空间。厚度靠排版层级,不靠特效——海报感最强的底。

    色块用 accent 而不是 ink:通栏近黑块会让同一套文字色在上下半区
    一半可读一半不可读,版式就没法跨风格包复用了。
    """
    rng = np.random.default_rng(seed)
    w, h = size
    arr = np.zeros((h, w, 3)) + _rgb(pack.palette.main)
    cut = int(h * (1 - block))
    arr[cut:] = _rgb(pack.palette.accent)
    arr[cut:cut + max(2, h // 400)] = _rgb(pack.palette.aux)
    return _finish(arr, pack.grain_amp * 0.5, rng)


def material_texture(size, pack: StylePack, seed: int = 0,
                     fiber: float = 1.0, **kw) -> Image.Image:
    """材质肌理(宣纸 / 亚麻 / 涂布纸)。近单色,靠纤维走向出质感。"""
    rng = np.random.default_rng(seed)
    w, h = size
    base = np.zeros((h, w, 3)) + _rgb(pack.palette.main)
    coarse = _value_noise(size, 6, rng)[:, :, None]
    fine = rng.normal(0, 1, (h, w, 1))
    fine = np.asarray(
        Image.fromarray(np.clip(fine[:, :, 0] * 40 + 128, 0, 255).astype(np.uint8))
        .filter(ImageFilter.GaussianBlur(0.6)), dtype=np.float64
    )[:, :, None] / 255 - 0.5
    arr = base * (0.94 + 0.10 * coarse) + fine * 26 * fiber
    arr -= _radial(size, 0.5, 0.5, 1.25, 28)  # 轻暗角
    return _finish(arr, pack.grain_amp, rng)


def liminal_dreamcore(size, pack: StylePack, seed: int = 0, **kw) -> Image.Image:
    """失焦雾面/梦核。低对比高亮度,靠形状不靠边缘——回忆与破防段。"""
    rng = np.random.default_rng(seed)
    arr = _vgrad(size, pack.palette.main, pack.palette.aux, gamma=0.7)
    blob = _value_noise(size, 4, rng)[:, :, None]
    arr = arr * (0.88 + 0.24 * blob)
    arr += _radial(size, 0.5, 0.42, 1.0, 70) * _rgb(pack.palette.accent) / 255
    arr = np.asarray(
        Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
        .filter(ImageFilter.GaussianBlur(size[1] * 0.006)), dtype=np.float64)
    return _finish(arr, pack.grain_amp, rng)


# ------------------------------------------------------------ 现代国乙 4 种

def urban_night_neon(size, pack: StylePack, seed: int = 0,
                     blur: float = 0.014, **kw) -> Image.Image:
    """都市夜景虚化。楼体剪影 + 成片窗格光 + 街灯钠黄,散焦成光斑。

    冷暖同框是夜城的物理事实,不是赛博紫青套路(见 style_packs.R2_RULES)。
    窗光按楼层网格成片出现——随机撒点会散成星空,读不出「城市」。
    """
    rng = np.random.default_rng(seed)
    w, h = size
    arr = _vgrad(size, pack.palette.ink, pack.palette.main, gamma=0.5)
    arr += _radial(size, 0.5, 0.66, 0.9, 55) * _rgb(pack.palette.accent) / 255  # 地平线辉光

    lights = Image.new("RGB", (w, h), (0, 0, 0))
    d = ImageDraw.Draw(lights)
    warm, cool = _rgb(pack.palette.accent), _rgb(pack.palette.aux)
    x = -w * 0.05
    while x < w:  # 一栋一栋排,窗格按层高网格
        bw = rng.uniform(0.10, 0.22) * w
        top = h * rng.uniform(0.10, 0.52)
        d.rectangle([x, top, x + bw, h], fill=tuple((_rgb(pack.palette.ink) * 1.4).astype(int)))
        gx, gy = bw / rng.integers(4, 8), h * rng.uniform(0.030, 0.048)
        lit = 0.45 + 0.35 * rng.random()
        cy = top + gy * 0.6
        while cy < h * 0.97:
            cx = x + gx * 0.35
            while cx < x + bw - gx * 0.5:
                if rng.random() < lit:
                    c = warm if rng.random() < 0.78 else cool
                    d.rectangle([cx, cy, cx + gx * 0.45, cy + gy * 0.42],
                                fill=tuple((c * rng.uniform(0.5, 1.15)).clip(0, 255).astype(int)))
                cx += gx
            cy += gy
        x += bw * rng.uniform(0.72, 0.96)
    for _ in range(int(20 + 14 * pack.particle_density)):  # 街灯/车灯
        r = rng.uniform(0.012, 0.04) * h
        cx, cy = rng.uniform(0, w), rng.uniform(h * 0.62, h * 1.02)
        d.ellipse([cx - r, cy - r, cx + r, cy + r],
                  fill=tuple((warm * rng.uniform(0.75, 1.15)).clip(0, 255).astype(int)))
    lights = lights.filter(ImageFilter.GaussianBlur(h * blur))
    arr += np.asarray(lights, dtype=np.float64) * 1.5
    arr -= _radial(size, 0.5, 0.5, 1.5, 40)
    return _finish(arr, pack.grain_amp, rng)


def luxury_interior_warm(size, pack: StylePack, seed: int = 0, **kw) -> Image.Image:
    """高奢室内暖光:一盏主灯 + 木饰面暗示 + 大面积柔和衰减。

    虚化到只剩明暗关系——室内背景的作用是给人物打底,细节越少越贵。
    """
    rng = np.random.default_rng(seed)
    w, h = size
    arr = _vgrad(size, pack.palette.main, pack.palette.ink, gamma=2.2)

    panel = np.zeros((h, w, 3))
    for i in range(3):  # 竖向木饰面,只留明暗节奏
        x0 = int(w * (0.10 + i * 0.32))
        panel[:, x0:x0 + int(w * 0.10)] = _rgb(pack.palette.aux)
    panel = np.asarray(
        Image.fromarray(np.clip(panel, 0, 255).astype(np.uint8))
        .filter(ImageFilter.GaussianBlur(h * 0.075)), dtype=np.float64)
    arr = arr * 0.80 + panel * 0.30

    arr += _radial(size, 0.74, 0.24, 0.62, 150) * _rgb(pack.palette.accent) / 255  # 主灯
    arr += _radial(size, 0.18, 0.70, 0.55, 55) * _rgb(pack.palette.aux) / 255  # 补光
    arr -= _radial(size, 0.5, 0.55, 1.05, 80)
    return _finish(arr, pack.grain_amp, rng)



def particle_starfield(size, pack: StylePack, seed: int = 0, **kw) -> Image.Image:
    """星海/异空间。真星点(大小亮度分布)+ 银河带,不是紫青渐变。"""
    rng = np.random.default_rng(seed)
    w, h = size
    arr = _vgrad(size, pack.palette.ink, pack.palette.main, gamma=0.8)
    arr += _value_noise(size, 5, rng)[:, :, None] * _rgb(pack.palette.aux) * 0.22

    stars = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(stars)
    for _ in range(int(700 * max(pack.particle_density, 0.3))):
        r = rng.gamma(1.4) * h * 0.0012
        x, y = rng.uniform(0, w), rng.uniform(0, h)
        d.ellipse([x - r, y - r, x + r, y + r], fill=int(rng.uniform(90, 255)))
    halo = np.asarray(stars.filter(ImageFilter.GaussianBlur(h * 0.004)), dtype=np.float64)
    arr += np.asarray(stars, dtype=np.float64)[:, :, None] * _rgb("#ffffff") / 255
    arr += halo[:, :, None] * _rgb(pack.palette.accent) / 255 * 1.6
    return _finish(arr, pack.grain_amp, rng)


def photoreal_location(size, pack: StylePack, seed: int = 0,
                       plate: str | pathlib.Path | None = None,
                       blur: float = 0.008, **kw) -> Image.Image:
    """实拍外景底片(咖啡馆/街角/车内)。要一张真底片。

    拿不到就报错,不退化成程序化渐变冒充实拍——那是把「像」当成「是」,
    正是 PPT 感事故的同一类错误。
    """
    if plate is None:
        raise ValueError(
            "photoreal_location 需要 plate=实拍底片路径。"
            "没有底片就换 urban_night_neon / luxury_interior_warm 这类程序化背景,"
            "不要用生成图冒充实拍。")
    img = Image.open(plate).convert("RGB")
    w, h = size
    scale = max(w / img.width, h / img.height)
    img = img.resize((round(img.width * scale), round(img.height * scale)), Image.LANCZOS)
    left, top = (img.width - w) // 2, (img.height - h) // 2
    img = img.crop((left, top, left + w, top + h))
    img = img.filter(ImageFilter.GaussianBlur(h * blur))
    arr = np.asarray(img, dtype=np.float64) - _radial(size, 0.5, 0.5, 1.2, 40)
    return _finish(arr, pack.grain_amp, np.random.default_rng(seed))


# -------------------------------------------------------------- 男团 3 种

def studio_seamless(size, pack: StylePack, seed: int = 0,
                    hotspot: float = 0.34, **kw) -> Image.Image:
    """纯色影棚 seamless 背景纸。一手男团物料里出现频率最高的一种。

    特征是「几乎没有特征」:单一纯色 + 中心热点 + 底部地面衔接的柔和衰减,
    注意力全给人和服装。任何肌理/装饰都会削弱它的作用。
    """
    rng = np.random.default_rng(seed)
    w, h = size
    base = _rgb(pack.palette.main)
    arr = np.zeros((h, w, 3)) + base
    arr += _radial(size, 0.5, hotspot, 0.85, 42)  # 主灯热点
    floor = np.clip((np.linspace(0, 1, h) - 0.72) / 0.28, 0, 1)[:, None, None]
    arr -= floor * 34  # 地面衔接的暗接缝
    arr -= _radial(size, 0.5, 0.5, 1.35, 26)
    return _finish(arr, pack.grain_amp * 0.6, rng)


def dark_studio_fog(size, pack: StylePack, seed: int = 0, **kw) -> Image.Image:
    """暗调舞台 + 烟雾 + 单侧硬光。暗是灯没打到,不是自造深色画布。

    烟必须看得见——没有介质的光锥在画面里不存在,只剩一块黑。
    """
    rng = np.random.default_rng(seed)
    w, h = size
    arr = np.zeros((h, w, 3)) + _rgb(pack.palette.ink)

    fog = _value_noise(size, 3, rng)[:, :, None] * 0.6 + 0.4
    fog *= np.clip(np.linspace(0.25, 1.15, h)[:, None, None], 0, 1)  # 烟沉在下半

    beam = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(beam)
    for i, (x0, x1, v) in enumerate(((0.72, 0.90, 150), (0.60, 0.74, 95))):
        d.polygon([(w * x0, -h * 0.02), (w * x1, -h * 0.02),
                   (w * (x1 - 0.62 - i * 0.1), h), (w * (x0 - 0.78 - i * 0.1), h)], fill=v)
    beam_a = np.asarray(beam.filter(ImageFilter.GaussianBlur(h * 0.05)),
                        dtype=np.float64)[:, :, None] / 255
    arr += beam_a * fog * _rgb(pack.palette.aux) * 1.25  # 光只在有烟处显形
    arr += beam_a ** 2 * _rgb(pack.palette.accent) * 0.35  # 光锥芯

    arr += fog * _rgb(pack.palette.aux) * 0.10 * (0.6 + pack.particle_density)  # 环境烟
    arr -= _radial(size, 0.5, 0.5, 1.25, 30)
    return _finish(arr, pack.grain_amp, rng)


def industrial_concrete(size, pack: StylePack, seed: int = 0, **kw) -> Image.Image:
    """清水混凝土 / 粗粝金属。靠肌理而非配色出高级感,概念照与预告常用。

    肌理要有尺度层次(大水渍斑 > 模板缝 > 细砂)——只叠细噪声会糊成一片灰粥。
    """
    rng = np.random.default_rng(seed)
    w, h = size
    arr = np.zeros((h, w, 3)) + _rgb(pack.palette.main)
    arr *= 0.72 + 0.46 * _value_noise(size, 3, rng)[:, :, None]  # 大尺度水渍/浇筑不均
    arr *= 0.90 + 0.16 * _value_noise(size, 12, rng)[:, :, None]  # 中尺度
    arr *= 0.97 + 0.06 * _value_noise(size, 60, rng)[:, :, None]  # 细砂

    marks = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(marks)
    lw = max(1, h // 500)
    for k in range(4):  # 模板拼缝(横平竖直,是混凝土的身份特征)
        y = h * (0.16 + k * 0.23) + rng.uniform(-h * 0.02, h * 0.02)
        d.line([(0, y), (w, y)], fill=95, width=lw)
        for j in range(4):  # 对拉螺栓孔,沿缝分布
            cx = w * (0.14 + j * 0.24) + rng.uniform(-w * 0.02, w * 0.02)
            r = h * 0.006
            d.ellipse([cx - r, y - r, cx + r, y + r], fill=150)
    for x0 in rng.uniform(0, w, 3):  # 竖向拼缝
        d.line([(x0, 0), (x0, h)], fill=70, width=lw)
    arr -= np.asarray(marks.filter(ImageFilter.GaussianBlur(lw * 0.8)),
                      dtype=np.float64)[:, :, None] * 0.75
    arr += _radial(size, 0.26, 0.20, 0.95, 60) * _rgb(pack.palette.aux) / 255  # 侧上方硬光
    arr -= _radial(size, 0.5, 0.5, 1.05, 65)
    return _finish(arr, pack.grain_amp, rng)


# ------------------------------------------------------------- 古风 1 种

def ink_scroll(size, pack: StylePack, seed: int = 0, ridges: int = 3, **kw) -> Image.Image:
    """宣纸 + 远山水墨。**限定活动皮,不是通用底**——现代设定套这套是世界观穿帮。"""
    rng = np.random.default_rng(seed)
    w, h = size
    arr = np.asarray(material_texture(size, pack, seed, fiber=1.3), dtype=np.float64)

    ink = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(ink)
    for i in range(ridges):
        base_y = h * (0.52 + i * 0.11)
        amp = h * 0.05 * (ridges - i) / ridges
        pts = [(x, base_y - amp * (0.5 + 0.5 * np.sin(x / w * np.pi * (2 + i) + i)))
               for x in range(0, w + 1, max(2, w // 240))]
        d.polygon([(0, h), *pts, (w, h)], fill=int(150 - i * 40))
    ink = ink.filter(ImageFilter.GaussianBlur(h * 0.006))
    a = np.asarray(ink, dtype=np.float64)[:, :, None] / 255
    arr = arr * (1 - a * 0.85) + _rgb(pack.palette.ink) * a * 0.85

    mr = h * 0.075
    moon = Image.new("L", (w, h), 0)
    ImageDraw.Draw(moon).ellipse(
        [w * 0.68 - mr, h * 0.16 - mr, w * 0.68 + mr, h * 0.16 + mr], fill=210)
    arr += np.asarray(moon.filter(ImageFilter.GaussianBlur(h * 0.01)),
                      dtype=np.float64)[:, :, None] * _rgb(pack.palette.accent) / 255
    return _finish(arr, pack.grain_amp, rng)


BACKGROUNDS: dict[str, Callable[..., Image.Image]] = {
    "bokeh_light_gradient": bokeh_light_gradient,
    "flat_color_negative_space": flat_color_negative_space,
    "material_texture": material_texture,
    "liminal_dreamcore": liminal_dreamcore,
    "urban_night_neon": urban_night_neon,
    "luxury_interior_warm": luxury_interior_warm,
    "particle_starfield": particle_starfield,
    "photoreal_location": photoreal_location,
    "studio_seamless": studio_seamless,
    "dark_studio_fog": dark_studio_fog,
    "industrial_concrete": industrial_concrete,
    "ink_scroll": ink_scroll,
}

# 题材 → 建议背景(按一手物料出现频率排,第一个不是唯一)
BY_GENRE: dict[str, tuple[str, ...]] = {
    "现代国乙": ("urban_night_neon", "luxury_interior_warm", "bokeh_light_gradient",
             "photoreal_location", "particle_starfield", "liminal_dreamcore",
             "flat_color_negative_space"),
    "古风国乙": ("ink_scroll", "material_texture", "bokeh_light_gradient",
             "particle_starfield"),
    "男团": ("studio_seamless", "dark_studio_fog", "industrial_concrete",
           "flat_color_negative_space", "urban_night_neon"),
}


def render(size: tuple[int, int], pack: StylePack, seed: int = 0, **kw) -> Image.Image:
    """按风格包声明的 background 键出图。"""
    if pack.background not in BACKGROUNDS:
        raise KeyError(f"未知背景 {pack.background!r};可用: {', '.join(sorted(BACKGROUNDS))}")
    return BACKGROUNDS[pack.background](size, pack, seed, **kw)
