#!/usr/bin/env python3
"""纸片人立绘卡点 MV · 公共渲染引擎（16:9·1920×1080·确定性 motion-graphics）.

这是**引擎库**，不是某一条片。所有原语与片无关：分层动态背景 Ken-Burns、§2 立体
三件套（rim/落影/接触影）、premium FX（真高斯 bloom + 锥形光 streak + 漏光 + 颗粒 +
散景 Field）、设计转场、分段调色弧、编排缓动、出画兜底运镜、艺术字。立绘像素零改动
（仅仿射+裁切换景别+alpha 羽化 · R1）。

每条片 = 一个**薄片脚本**只声明 `build_shots()` + `PVPaths`，import 本引擎调 `render()`：

    from paperdoll_engine import render, PVPaths, Shot, AMBER, ROSE
    PATHS = PVPaths(assets_dir=..., wav=..., out_dir=..., bg_plate="bg_x.png", slug="x")
    def build_shots(): return [Shot(...), ...]
    sys.exit(render(PATHS, build_shots(), 0.0, 10.73))

分镜（build_shots）是每条片一次性的创意产物，禁 clone 上一条（template-clone 铁律）；
引擎（本文件）是固定工具，禁复制改。
"""
from __future__ import annotations

import json
import math
import random
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[2]

# —— 画布/机器级默认（片无关，可被 PVConfig 覆盖）——
W, H = 1920, 1080
FPS = 30
FFMPEG = "/opt/homebrew/bin/ffmpeg"

CREAM = (248, 244, 234)
GOLD = (212, 175, 55)
PEACH = (244, 199, 199)
ORANGE = (255, 154, 92)
ROSE = (240, 170, 150)
AMBER = (230, 175, 120)
WARM_WHITE = (255, 246, 230)
INK = (74, 52, 38)


def _first_font(*cands: str) -> str:
    """返回第一个存在的字体路径；全缺则回退系统苹方（保证不崩）。"""
    for c in cands:
        if c and Path(c).exists():
            return c
    return "/System/Library/Fonts/PingFang.ttc"


FONT_TITLE = _first_font(
    "/System/Library/Fonts/Supplemental/Songti.ttc",
    "/System/Library/Fonts/STHeiti Medium.ttc",
)
FONT_LABEL = _first_font(
    str(Path.home() / "Library/Fonts/SourceHanSansSC-Heavy.otf"),
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/Supplemental/Songti.ttc",
)
# 歌词飘逸创意美术字：马善政行草（OFL），落回站酷小薇 → 宋体
FONT_LYRIC = _first_font(
    str(ROOT / "assets/fonts/MaShanZheng-Regular.ttf"),
    str(ROOT / "assets/fonts/ZCOOLXiaoWei-Regular.ttf"),
    FONT_TITLE,
)


# —— 片专属素材路径（render() 开头注入；FX 原语一律不碰它，只 3 个 IO 函数读）——
@dataclass(frozen=True)
class PVPaths:
    assets_dir: Path            # 立绘 cutout 与素材根目录
    wav: Path                   # 卡点时基音源
    out_dir: Path               # 成片/帧/motion sidecar 输出目录
    bg_plate: str = "bg.png"    # 背景 plate 文件名（相对 out_dir）
    slug: str = "pv"            # 片标识（用于输出命名）
    beats_json: Path | None = None

    @property
    def frame_dir(self) -> Path:
        return self.out_dir / "_frames"

    @property
    def beats_path(self) -> Path:
        return self.beats_json or (self.assets_dir / "beats.json")

    @property
    def bg_path(self) -> Path:
        return self.out_dir / self.bg_plate


_PATHS: PVPaths | None = None    # render() 开头 set；模块级私有，勿在片脚本直接改


# ————————————————— 节拍 —————————————————
def load_beats():
    bj = _PATHS.beats_path
    if bj.exists():
        d = json.loads(bj.read_text())
        return d["tempo"], d["beats"]
    import librosa
    y, sr = librosa.load(str(_PATHS.wav), sr=44100, mono=True)
    tempo, beats = librosa.beat.beat_track(y=y, sr=sr, units="time")
    tempo = float(np.atleast_1d(tempo)[0])
    beats = [float(b) for b in beats]
    bj.write_text(json.dumps({"tempo": tempo, "beats": beats}))
    return tempo, beats


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease_out(x):
    return 1.0 - (1.0 - clamp(x)) ** 3


def ease_in_out(x):
    x = clamp(x)
    return 3 * x * x - 2 * x * x * x


def back_out(x):
    """过冲缓动（入场落位带回弹）。"""
    x = clamp(x)
    c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2


def pulse(t, marks, decay):
    p = 0.0
    for b in marks:
        if b <= t:
            p = math.exp(-(t - b) / decay)
        else:
            break
    return p


def screen(base, add):
    return 255.0 - (255.0 - base) * (255.0 - add) / 255.0


def lerp_col(a, b, k):
    return tuple(a[i] * (1 - k) + b[i] * k for i in range(3))


# ————————————————— 立绘 —————————————————
_DOLL: dict = {}


def full_doll(name):
    if name not in _DOLL:
        im = Image.open(_PATHS.assets_dir / f"{name}_cutout.png").convert("RGBA")
        a = im.getchannel("A").point(lambda v: 0 if v < 28 else (255 if v > 96 else int((v - 28) / 68 * 255)))
        im.putalpha(a)
        _DOLL[name] = im.crop(im.getbbox())
    return _DOLL[name]


def prep_layer(name, crop_rel, target_h):
    d = full_doll(name)
    feather = False
    if crop_rel:
        l, tp, r, b = crop_rel
        d = d.crop((int(l * d.width), int(tp * d.height),
                    int(r * d.width), int(b * d.height)))
        bb = d.getbbox()
        if bb:
            d = d.crop(bb)
        feather = True
    s = target_h / d.height
    d = d.resize((max(1, round(d.width * s)), target_h), Image.LANCZOS)
    if feather:
        d = _feather_edges(d)
    return d


def _feather_edges(im, frac=0.09):
    """裁切景别时把被切平的身体硬边羽化成柔性肖像渐隐（立绘内部像素不变）。"""
    w, h = im.size
    a = np.array(im.getchannel("A"), float)
    mx, my = max(2, int(w * frac)), max(2, int(h * frac))
    rx = np.clip(np.minimum(np.arange(w), w - 1 - np.arange(w)) / mx, 0, 1)
    ry = np.clip(np.minimum(np.arange(h), h - 1 - np.arange(h)) / my, 0, 1)
    mask = np.minimum(rx[None, :], ry[:, None])
    mask = mask * mask * (3 - 2 * mask)
    im.putalpha(Image.fromarray((a * mask).astype(np.uint8)))
    return im


# ————————————————— sprite / FX 基元 —————————————————
def soft_dot(size, color):
    yy, xx = np.mgrid[0:size, 0:size]
    c = (size - 1) / 2
    dd = np.sqrt((xx - c) ** 2 + (yy - c) ** 2) / (size / 2)
    a = np.clip(1 - dd, 0, 1) ** 2
    return a[:, :, None] * np.array(color, float)[None, None, :]


DOT_SP: dict = {}


def dot(size, col):
    k = (size, tuple(col))
    if k not in DOT_SP:
        DOT_SP[k] = soft_dot(size, col)
    return DOT_SP[k]


def make_rays(size):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    dr = ImageDraw.Draw(img)
    c = size / 2
    for i in range(20):
        a = i / 20 * 2 * math.pi
        dr.polygon([(c, c),
                    (c + math.cos(a - .025) * size, c + math.sin(a - .025) * size),
                    (c + math.cos(a + .025) * size, c + math.sin(a + .025) * size)],
                   fill=(*GOLD, 34))
    return img.filter(ImageFilter.GaussianBlur(8))


def make_flare(size):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c = size / 2
    d.ellipse([c - size * .16, c - size * .16, c + size * .16, c + size * .16],
              fill=(*WARM_WHITE, 210))
    d.line([(0, c), (size, c)], fill=(*WARM_WHITE, 130), width=4)
    d.line([(c, 0), (c, size)], fill=(*GOLD, 100), width=3)
    return img.filter(ImageFilter.GaussianBlur(5))


def make_moon(size):
    """暖白月盘 + 柔halo（贯穿全片的场景锚，非仅片头）。"""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c = size / 2
    for rr, al in ((0.50, 55), (0.42, 90), (0.34, 150), (0.27, 215), (0.22, 255)):
        d.ellipse([c - size * rr, c - size * rr, c + size * rr, c + size * rr],
                  fill=(*WARM_WHITE, al))
    return img.filter(ImageFilter.GaussianBlur(size * 0.03))


def make_ridges():
    """4 层山脊 · 大气透视：远浅/虚/淡融进雾 → 近深/实；末层=前景暗脊(大虚化)，
    立绘站其前，靠"前景虚 vs 立绘实"的对比生纵深。par=视差系数(远小近大)。"""
    rng = np.random.default_rng(99)
    # (col, par, ybase, amp, blur, alpha)
    specs = (((240, 216, 180), 0.18, 0.46, 0.055, 11, 150),  # 远：几乎融进地平雾
             ((216, 178, 132), 0.42, 0.58, 0.095, 6, 205),   # 中远
             ((150, 112, 76), 0.85, 0.74, 0.140, 3, 236),    # 中近：最实
             ((70, 48, 32), 1.55, 0.94, 0.075, 17, 224))     # 前景暗脊：大虚化
    out = []
    for col, par, ybase, amp, blur, al in specs:
        img = Image.new("RGBA", (int(W * 1.5), H), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        xs = np.linspace(0, W * 1.5, 90)
        base = ybase * H
        prof = (np.sin(xs / W * 3 + rng.uniform(0, 6)) * amp * H
                + np.sin(xs / W * 7 + rng.uniform(0, 6)) * amp * H * 0.45
                + np.sin(xs / W * 15 + rng.uniform(0, 6)) * amp * H * 0.18)
        poly = [(0, H)] + [(float(x), float(base - p)) for x, p in zip(xs, prof)] + [(W * 1.5, H)]
        d.polygon(poly, fill=(*col, al))
        out.append((img.filter(ImageFilter.GaussianBlur(blur)), par))
    return out


def clouds(t):
    """暖云霭横向漂移带（god-ray 的水平柔化版）。"""
    layer = np.zeros((H, W, 3))
    yy = np.arange(H)
    for i in range(4):
        cy = H * (0.16 + 0.13 * i) + math.sin(t * 0.2 + i) * 22
        band = np.exp(-((yy - cy) / (34 + i * 12)) ** 2)
        layer += band[:, None, None] * np.array([255, 226, 182], float) \
            * (0.055 + 0.02 * math.sin(t * 0.3 + i * 1.7))
    return layer


RAYS = FLARE = MOON = None
RIDGES: list = []
_BG_CACHE: dict = {}


def scene_backdrop(t, bg_plate, px, plate_path: str = ""):
    """对 gpt-image-2 插画 plate 做轻微 pan/zoom（Ken-Burns 呼吸）。
    plate_path 非空时走文件缓存（多背景支持），否则沿用传入 numpy 数组。"""
    global _BG_CACHE
    key = plate_path if plate_path else "__default__"
    if key not in _BG_CACHE:
        bw, bh = int(W * 1.08), int(H * 1.08)
        if plate_path:
            img = Image.open(plate_path).convert("RGB").resize((W, H), Image.LANCZOS)
            _BG_CACHE[key] = img.resize((bw, bh), Image.LANCZOS)
        else:
            _BG_CACHE[key] = Image.fromarray(
                np.clip(bg_plate, 0, 255).astype(np.uint8)).resize((bw, bh), Image.LANCZOS)
    big = _BG_CACHE[key]
    bw, bh = big.size
    max_dx, max_dy = bw - W, bh - H
    cx = max(0, min(max_dx, int(max_dx * 0.5 + px * 0.6)))
    cy = max(0, min(max_dy, int(max_dy * (0.5 + 0.35 * math.sin(t * 0.22)))))
    return np.array(big.crop((cx, cy, cx + W, cy + H)), float)


def bloom(arr, thr=205, strength=0.7):
    """真辉光：抽亮部→高斯→screen 回叠。让金/粒子像 MV 一样发光。"""
    lum = arr.mean(axis=2)
    mask = np.clip((lum - thr) / (255 - thr), 0, 1)[:, :, None]
    bright = arr * mask
    b = Image.fromarray(np.clip(bright, 0, 255).astype(np.uint8)).filter(
        ImageFilter.GaussianBlur(18))
    return screen(arr, np.array(b, float) * strength)


def grain(arr, t, amp=7.0):
    rng = np.random.default_rng(int(t * 1000) % 99999)
    n = (rng.random((H // 2, W // 2, 1)) - 0.5) * 2 * amp
    n = np.array(Image.fromarray(
        np.clip(128 + n, 0, 255).astype(np.uint8).repeat(3, 2)).resize((W, H)), float) - 128
    return np.clip(arr + n, 0, 255)


def light_leak(t, k):
    """暖光漏光大团 · 斜向缓移 · screen。"""
    if k <= 0.01:
        return np.zeros((H, W, 3))
    yy, xx = np.mgrid[0:H, 0:W]
    cx = W * (0.15 + 0.7 * ((t * 0.12) % 1))
    cy = H * 0.3
    r = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / (W * 0.5)
    g = np.clip(1 - r, 0, 1)[:, :, None] ** 2 * k
    return g * np.array(ORANGE, float)


def light_shafts(t):
    """斜向移动光轴（god rays）· 暖白 · screen。"""
    layer = np.zeros((H, W, 3))
    xx = np.arange(W)
    for i in range(5):
        cx = (W * (i / 5) + t * 60) % (W * 1.3) - W * 0.15
        band = np.exp(-((xx - cx) / 70) ** 2)
        layer += band[None, :, None] * np.array(WARM_WHITE, float) * 0.10
    return layer


class Field:
    def __init__(self, n, kind, seed, depth=1.0):
        rng = np.random.default_rng(seed)
        self.x = rng.uniform(0, W, n)
        self.y = rng.uniform(0, H, n)
        self.kind = kind
        self.depth = depth
        if kind == "petal":
            self.vy = rng.uniform(30, 80, n)
            self.vx = rng.uniform(-40, 40, n)
            self.size = rng.integers(10, 28, n)
            self.col = [PEACH if rng.random() > .3 else (255, 220, 180) for _ in range(n)]
        else:
            self.vy = rng.uniform(-28, -6, n)
            self.vx = rng.uniform(-8, 8, n)
            self.size = rng.integers(int(6 * depth), int(30 * depth), n)
            self.col = [GOLD if rng.random() > .4 else WARM_WHITE for _ in range(n)]
        self.ph = rng.uniform(0, 6.28, n)

    def render(self, t, boost=1.0, px=0.0):
        layer = np.zeros((H, W, 3))
        for i in range(len(self.x)):
            X = (self.x[i] + self.vx[i] * t + px * self.depth) % W
            Y = (self.y[i] + self.vy[i] * t) % H
            tw = (0.45 + 0.55 * math.sin(t * 2.2 + self.ph[i])) * boost
            sp = dot(int(self.size[i]), self.col[i]) * tw
            s = sp.shape[0]
            x0, y0 = int(X - s / 2), int(Y - s / 2)
            sx0, sy0 = max(0, -x0), max(0, -y0)
            sx1, sy1 = s - max(0, x0 + s - W), s - max(0, y0 + s - H)
            if sx1 <= sx0 or sy1 <= sy0:
                continue
            dx0, dy0 = max(0, x0), max(0, y0)
            reg = layer[dy0:dy0 + sy1 - sy0, dx0:dx0 + sx1 - sx0]
            layer[dy0:dy0 + sy1 - sy0, dx0:dx0 + sx1 - sx0] = screen(reg, sp[sy0:sy1, sx0:sx1])
        return layer


def streaks(t, direction, strength, seed=3):
    """粗锥形光 streak（PIL 画粗线+blur → 高级感，替代像素细线）。"""
    if strength <= 0.01:
        return np.zeros((H, W, 3))
    img = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(img)
    rng = np.random.default_rng(seed)
    if direction == "radial":
        cx, cy = W / 2, H * 0.45
        for i in range(28):
            a = i / 28 * 2 * math.pi + t * 0.25
            r0 = 240 + (t * 700 + i * 61) % 820
            x0, y0 = cx + math.cos(a) * r0, cy + math.sin(a) * r0
            x1, y1 = cx + math.cos(a) * (r0 + 220), cy + math.sin(a) * (r0 + 220)
            w = rng.integers(2, 6)
            d.line([(x0, y0), (x1, y1)], fill=GOLD, width=int(w))
    else:
        sgn = -1 if direction == "left" else 1
        for i in range(30):
            y = (i * H / 30 + t * 50) % H
            x0 = (t * 1900 * sgn + i * 67) % (W + 500) - 250
            w = rng.integers(2, 7)
            d.line([(x0, y), (x0 + sgn * 280, y)], fill=GOLD, width=int(w))
    img = img.filter(ImageFilter.GaussianBlur(3))
    return np.array(img, float) * strength


# ————————————————— 背景动效层（真动，非静态 plate）—————————————————
_RAIN_SEED = np.random.default_rng(4242)
_RAIN = None  # (x0,y0,speed,length,alpha) 固定粒子集，逐帧按 t 位移


def _rain_particles(n=260):
    global _RAIN
    if _RAIN is None:
        r = np.random.default_rng(4242)
        _RAIN = (r.uniform(-120, W, n), r.uniform(0, H, n),
                 r.uniform(820, 1520, n), r.uniform(15, 42, n),
                 r.uniform(0.20, 0.60, n))
    return _RAIN


def rain_layer(t, intensity=1.0, wind=-0.28):
    """真下落雨丝：固定粒子逐帧按 t 位移（帧间真运动）· 暖白细线 · 供 screen 叠加。
    与背景 plate 无关——即使背景是静态图，这一层也让画面'在下雨'。"""
    if intensity <= 0.01:
        return np.zeros((H, W, 3))
    x0, y0, sp, ln, al = _rain_particles()
    img = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(img)
    for i in range(len(x0)):
        y = (y0[i] + sp[i] * t) % (H + 140) - 70
        x = (x0[i] + wind * sp[i] * t) % (W + 240) - 120
        dx, dy = wind * ln[i], ln[i]
        c = int(255 * al[i] * intensity)
        d.line([(x, y), (x + dx, y + dy)], fill=(c, int(c * 0.95), int(c * 0.84)), width=1)
    img = img.filter(ImageFilter.GaussianBlur(0.6))
    return np.array(img, float)


_BRANCH = None  # 前景树枝层（gpt-image 真素材抠图，非 PIL 现搓）


def branch_layer(canvas, t):
    """前景花枝随风摆动：水平剪切随行号增大（树梢摆幅 > 枝根）· 逐帧振荡 = 真摇晃。
    最顶前景层（在立绘之前），带轻虚化做景深视差。缺素材则跳过（不 fail）。"""
    global _BRANCH
    if _BRANCH is None:
        p = _PATHS.out_dir / "branch_fg.png"
        if not p.exists():
            return
        im = Image.open(p).convert("RGBA")
        s = W / im.width
        im = im.resize((W, int(im.height * s)), Image.LANCZOS)
        _BRANCH = im.filter(ImageFilter.GaussianBlur(1.3))  # 前景 DOF
    bh = _BRANCH.height
    sway = math.sin(t * 1.15) * 0.045 + math.sin(t * 2.1 + 1.0) * 0.018  # 主摆 + 细颤
    # PIL AFFINE 反向映射：input_x = out_x + b*out_y；b=-sway → 下行(树梢)右移更多
    swayed = _BRANCH.transform((W, bh), Image.AFFINE, (1, -sway, 0, 0, 1, 0),
                               resample=Image.BICUBIC)
    canvas.alpha_composite(swayed, (0, 0))


# ————————————————— §13 人物运动感技法 —————————————————

def breath_sway_delta(lt: float, seed: int = 0) -> tuple:
    """A轴微动增强：返回 (dx, dy, dangle) 叠加到 place_doll 的 breathe 上。"""
    rng = seed * 1.31
    dy = 6.0 * math.sin(lt * 1.55 + rng)
    dx = 3.5 * math.sin(lt * 0.97 + rng + 0.8)
    dangle = 1.2 * math.sin(lt * 1.23 + rng + 1.4)
    return dx, dy, dangle


def motion_echo(canvas: Image.Image, layer: Image.Image,
                cx: int, cy: int, direction: str,
                lt: float, dur: float = 0.35) -> None:
    """C1轴残影：在主体后叠3层ghost，alpha随lt淡出。direction: 'left'|'right'|'up'."""
    if lt > dur:
        return
    cx, cy = int(cx), int(cy)
    fade = 1.0 - lt / dur
    offsets = [(-30, 0), (-60, 0), (-90, 0)] if direction != "right" else [(30, 0), (60, 0), (90, 0)]
    if direction == "up":
        offsets = [(0, -30), (0, -60), (0, -90)]
    alphas = [int(128 * fade), int(64 * fade), int(26 * fade)]
    lw, lh = layer.size
    x0, y0 = cx - lw // 2, cy - lh
    for (ox, oy), a in zip(offsets, alphas):
        ghost = layer.copy()
        ghost.putalpha(ghost.getchannel("A").point(lambda v: min(v, a)))
        canvas.alpha_composite(ghost, (int(x0 + ox), int(y0 + oy)))


def shatter_reveal(canvas: Image.Image, layer: Image.Image,
                   cx: int, cy: int, lt: float,
                   n: int = 5, duration: float = 0.55) -> None:
    """C3轴碎片聚合登场：NxN 瓦片从随机偏移飞向目标位置，ease_out。"""
    cx, cy = int(cx), int(cy)
    progress = min(1.0, lt / duration)
    ease = 1.0 - (1.0 - progress) ** 3  # ease_out_cubic
    lw, lh = layer.size
    x0, y0 = cx - lw // 2, cy - lh
    tile_w, tile_h = lw // n, lh // n
    rng = np.random.RandomState(42)
    for i in range(n):
        for j in range(n):
            box = (j * tile_w, i * tile_h,
                   (j + 1) * tile_w if j < n - 1 else lw,
                   (i + 1) * tile_h if i < n - 1 else lh)
            tile = layer.crop(box)
            delay = (i * 0.02 + j * 0.01)
            local_ease = min(1.0, max(0.0, (lt - delay) / (duration - delay))) if lt > delay else 0.0
            local_ease = 1.0 - (1.0 - local_ease) ** 3
            rand_ox = int(rng.randint(-220, 220) * (1 - local_ease))
            rand_oy = int(rng.randint(-320, 320) * (1 - local_ease))
            tx = x0 + box[0] + rand_ox
            ty = y0 + box[1] + rand_oy
            if tile.mode != "RGBA":
                tile = tile.convert("RGBA")
            a_val = int(255 * local_ease)
            tile.putalpha(tile.getchannel("A").point(lambda v: min(v, a_val)))
            canvas.alpha_composite(tile, (int(tx), int(ty)))


def film_strip_composite(canvas: Image.Image, doll_imgs: list,
                         t: float, beats: np.ndarray, downbeats: np.ndarray,
                         scroll_speed: float = 100.0, tilt_deg: float = 4.0,
                         cell_w: int = 420) -> None:
    """B1轴胶片走带：N格胶片横向滚动，每格里放一个立绘，重拍时速度爆发。
    doll_imgs: list of PIL RGBA Image (已载入的立绘)."""
    n = len(doll_imgs)
    if n == 0:
        return
    dbp = pulse(t, downbeats, 0.22)
    speed = scroll_speed * (1.8 if dbp > 0.3 else 1.0)
    offset = int(t * speed) % (cell_w * n)

    cell_h = int(cell_w * 1.55)
    strip_w = cell_w * n
    strip = Image.new("RGBA", (strip_w * 2, cell_h + 80), (0, 0, 0, 0))
    d = ImageDraw.Draw(strip)

    for rep in range(2):
        for idx, doll in enumerate(doll_imgs):
            bx = rep * strip_w + idx * cell_w
            # 黑色胶片格
            d.rectangle([bx + 6, 40, bx + cell_w - 6, cell_h + 40], fill=(10, 8, 6, 220))
            # 齿孔
            for hy in range(48, cell_h + 30, 36):
                d.rectangle([bx + 10, hy, bx + 26, hy + 22], fill=(60, 52, 40, 200))
                d.rectangle([bx + cell_w - 26, hy, bx + cell_w - 10, hy + 22], fill=(60, 52, 40, 200))
            # 立绘缩放贴入
            scale = (cell_w - 60) / doll.width
            dh = int(doll.height * scale)
            dw = cell_w - 60
            thumb = doll.resize((dw, dh), Image.LANCZOS)
            paste_y = 40 + max(0, (cell_h - dh) // 2)
            strip.alpha_composite(thumb, (bx + 30, paste_y))

    # 倾斜 + 裁剪可见区
    strip_rot = strip.rotate(-tilt_deg, expand=True, resample=Image.BICUBIC)
    vis_x = offset % (cell_w * n)
    vis_w = min(W + 80, strip_rot.width)
    crop_box = (vis_x % strip_rot.width, 0,
                min(vis_x % strip_rot.width + vis_w, strip_rot.width), strip_rot.height)
    visible = strip_rot.crop(crop_box)
    cy_pos = (H - cell_h) // 2
    canvas.alpha_composite(visible, (-(vis_x % cell_w), cy_pos))


# ————————————————— 分镜 —————————————————
@dataclass
class Shot:
    t0: float
    t1: float
    doll: str
    crop: tuple | None
    hfrac: float
    cam: str
    enter: str
    grade: tuple             # 该镜暖调 tint
    fx: list = field(default_factory=list)
    text: str = ""
    trans: str = "flash"     # 入场转场 flash/swipe_l/swipe_r/zoomblur
    montage_crops: list = field(default_factory=list)
    group: list = field(default_factory=list)  # 多人合体：≥1 立绘名 → 走 place_group（覆盖 doll）
    name: str = ""           # 艺术字名牌（个人展示）· 竖排国风 + 印章
    epithet: str = ""        # 名牌旁小字词牌（配 name 用）
    title_mode: str = ""     # "opening" | "ending" | ""（大标题艺术字）
    lyric: dict | None = None  # 逐句歌词美术字：{"singer","text","chars":[[字,时点],...]}
    singer: str = ""         # 演唱者标签（右上小字，如"轩珩"/"合"）
    bg: str = ""             # 覆盖背景图路径（留空=用默认 bg0）


def active_shot(shots, t):
    for s in shots:
        if s.t0 <= t < s.t1:
            return s
    return shots[-1]


# ————————————————— 大字 · 艺术字 —————————————————
SEAL_RED = (176, 42, 34)   # 朱砂印泥（真实红，非霓虹；hue≈5°不触蓝紫门）


def _seal(canvas, cx, cy, size, char, alpha=235):
    """国风朱砂印章：圆角红方 + 反白艺术字。"""
    ov = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    d.rounded_rectangle([cx - size / 2, cy - size / 2, cx + size / 2, cy + size / 2],
                        radius=int(size * 0.16), fill=(*SEAL_RED, int(alpha)))
    f = ImageFont.truetype(FONT_TITLE, int(size * 0.60))
    w = d.textlength(char, font=f)
    d.text((cx - w / 2, cy - size * 0.37), char, font=f, fill=(255, 246, 234, int(alpha)))
    canvas.alpha_composite(ov)


def _title_char(canvas, ch, cx, y, size, alpha, ink=INK, outline=GOLD, ow=3,
                angle=0.0, glow=0.0):
    """单个艺术字：金色多向描边双钩 + 墨填 + 可选倾斜(飘逸)+ 金辉光晕(大胆/想象力)。
    angle≠0 → 单字微旋（书法飞白感，非整块刚体）；glow>0 → 字底暖金放射光晕。
    仅绘制文字层（R1 不管文字），(cx,y) 为该字左上锚点，旋转绕字心避免位移漂。"""
    font = ImageFont.truetype(FONT_TITLE, size)
    # 字层独立小画布：便于绕字心旋转，避免全屏旋转开销
    pad = max(ow * 3, int(size * 0.35)) + 8
    cell = Image.new("RGBA", (size + pad * 2, size + pad * 2), (0, 0, 0, 0))
    dc = ImageDraw.Draw(cell)
    ax, ay = pad, pad
    if glow > 0.01:                       # 金辉光晕：字形外扩高斯 → 暖金背光
        gl = Image.new("RGBA", cell.size, (0, 0, 0, 0))
        ImageDraw.Draw(gl).text((ax, ay), ch, font=font, fill=(*GOLD, int(alpha)))
        gl = gl.filter(ImageFilter.GaussianBlur(int(size * 0.13)))
        gl.putalpha(gl.getchannel("A").point(lambda v: int(v * glow)))
        cell.alpha_composite(gl)
    for ox, oy in ((-ow, 0), (ow, 0), (0, -ow), (0, ow),
                   (-ow, -ow), (ow, ow), (-ow, ow), (ow, -ow)):
        dc.text((ax + ox, ay + oy), ch, font=font, fill=(*outline, alpha))
    dc.text((ax, ay), ch, font=font, fill=(*ink, alpha))
    if abs(angle) > 0.1:
        cell = cell.rotate(angle, expand=True, resample=Image.BICUBIC)
    # 字心与 cell 心重合（pad 对称）→ 旋转后按字心对回原锚点，无位移漂
    canvas.alpha_composite(cell, (int(cx + size / 2 - cell.width / 2),
                                  int(y + size / 2 - cell.height / 2)))


def kinetic_text(canvas, shot, t):
    lt = t - shot.t0

    # —— 开场大标题：逐字"飞白弹入"（更大·带旋转甩入·落位后持续漂浮 + 金辉呼吸）——
    if shot.title_mode == "opening":
        chars, size, gap, y = shot.text, 172, 38, 158
        total = size * len(chars) + gap * (len(chars) - 1)
        x0 = (W - total) // 2
        reveal = [shot.t0 + i * 0.42 for i in range(len(chars))]
        for i, ch in enumerate(chars):
            if t < reveal[i]:
                continue
            e = (t - reveal[i])
            k = ease_out(e / 0.32)
            bo = back_out(clamp(e / 0.46))
            dy = int((1 - bo) * 64)                       # 从下方过冲弹起
            dx = int((1 - bo) * (18 if i % 2 else -18))   # 左右交错甩入
            settle = clamp(e / 0.5)                       # 落位进度
            # 入场大倾角 → 落位微摆（飘逸），末字定后整体轻漂
            spin = (1 - settle) * (14 if i % 2 else -14)
            drift = math.sin(e * 1.3 + i * 0.9) * 2.4 * settle
            fy = math.sin((t - shot.t0) * 1.1 + i * 0.7) * 5 * settle
            glow = 0.35 + 0.35 * math.sin(e * 2.0 + i)
            _title_char(canvas, ch, x0 + i * (size + gap) + dx,
                        y - dy + fy, size, int(255 * k),
                        angle=spin + drift, glow=glow * settle)
        if t > 1.8:
            k = clamp((t - 1.8) / 0.5)
            f2 = ImageFont.truetype(FONT_LABEL, 34)
            ov = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
            d = ImageDraw.Draw(ov)
            sub = "语 音 厅 · 群 星"
            w = d.textlength(sub, font=f2)
            sy = y + size + 40
            # 副题左右描边（更立体）+ 展开金线
            for ox, oy in ((-2, 0), (2, 0), (0, -2), (0, 2)):
                d.text(((W - w) / 2 + ox, sy + oy), sub, font=f2, fill=(*INK, int(150 * k)))
            d.text(((W - w) / 2, sy), sub, font=f2, fill=(*GOLD, int(220 * k)))
            lw = (total * 0.5) * k
            d.rectangle([W / 2 - lw, sy - 18, W / 2 + lw, sy - 14], fill=(*GOLD, int(200 * k)))
            canvas.alpha_composite(ov)
        return

    # —— 结尾大标题：逐字上浮定版 + 金线展开 + 双印落章 + 呼吸金辉（更大·更盛）——
    if shot.title_mode == "ending":
        chars, size, gap = shot.text, 196, 40
        total = size * len(chars) + gap * (len(chars) - 1)
        x0 = (W - total) // 2
        y = 292
        for i, ch in enumerate(chars):
            e = lt - i * 0.16
            ki = ease_out(clamp(e / 0.7))
            gi = 0.45 + 0.4 * math.sin(lt * 1.5 + i * 0.8)   # 逐字错相呼吸
            fy = math.sin(lt * 0.9 + i * 0.6) * 4 * ki        # 定版后极缓漂浮
            _title_char(canvas, ch, x0 + i * (size + gap),
                        y - int((1 - ki) * 52) + fy, size, int(255 * ki),
                        ow=int(4 + gi * 3), glow=gi * ki)
        k = ease_out(clamp(lt / 0.7))
        a = int(255 * k)
        ov = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(ov)
        ly = y + size + 40
        d.rectangle([W / 2 - total / 2 * k, ly, W / 2 + total / 2 * k, ly + 7], fill=(*GOLD, a))
        f2 = ImageFont.truetype(FONT_LABEL, 40)
        sub = "愿 得 长 相 见"
        w = d.textlength(sub, font=f2)
        for ox, oy in ((-2, 0), (2, 0), (0, -2), (0, 2)):
            d.text(((W - w) / 2 + ox, ly + 30 + oy), sub, font=f2, fill=(*INK, int(160 * k)))
        d.text(((W - w) / 2, ly + 30), sub, font=f2, fill=(*GOLD, int(230 * k)))
        canvas.alpha_composite(ov)
        if lt > 0.5:
            _seal(canvas, W / 2 - total / 2 - 84, y + 88, 118, "明", int(235 * clamp((lt - 0.5) / 0.4)))
            _seal(canvas, W / 2 + total / 2 + 84, y + 88, 118, "月", int(235 * clamp((lt - 0.7) / 0.4)))
        return

    # —— 个人展示名牌：竖排艺术字名 + 词牌 + 朱砂印（国风）——
    if shot.name:
        chars = shot.name
        size = 92
        k = back_out(clamp(lt / 0.34))
        a = int(240 * clamp(lt / 0.22))
        dx = int((1 - k) * 80)
        bx = W - 210 + dx
        by = 150
        ov = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(ov)
        d.rectangle([bx - 24, by - 10, bx - 13, by + (size + 6) * len(chars)], fill=(*GOLD, a))
        canvas.alpha_composite(ov)
        for i, ch in enumerate(chars):
            _title_char(canvas, ch, bx, by + i * (size + 6), size, a,
                        ink=INK, outline=WARM_WHITE, ow=2)
        if shot.epithet:
            fe = ImageFont.truetype(FONT_TITLE, 36)
            ov2 = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
            d2 = ImageDraw.Draw(ov2)
            ex = bx - 66 + int((1 - k) * 40)
            for j, ec in enumerate(shot.epithet):
                for ox, oy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    d2.text((ex + ox, by + 8 + j * 44 + oy), ec, font=fe, fill=(*INK, int(a * 0.7)))
                d2.text((ex, by + 8 + j * 44), ec, font=fe, fill=(*WARM_WHITE, a))
            canvas.alpha_composite(ov2)
        if lt > 0.3:
            sy = by + (size + 6) * len(chars) + 60
            _seal(canvas, bx + 2, sy, 74, chars[0], int(235 * clamp((lt - 0.3) / 0.35)))
        return

    # —— 普通竖排词牌 ——
    if shot.text:
        chars = shot.text
        font = ImageFont.truetype(FONT_TITLE, 86)
        k = back_out(lt / 0.3)
        a = int(235 * clamp(lt / 0.2))
        dx = int((1 - k) * 70)
        ov = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(ov)
        bx, by = W - 220 + dx, 130
        d.rectangle([bx - 26, by - 8, bx - 15, by + 100 * len(chars)], fill=(*GOLD, a))
        for i, ch in enumerate(chars):
            for ox, oy in ((-2, 0), (2, 0), (0, -2), (0, 2)):
                d.text((bx + ox, by + i * 100 + oy), ch, font=font, fill=(*WARM_WHITE, a))
            d.text((bx, by + i * 100), ch, font=font, fill=(*INK, a))
        canvas.alpha_composite(ov)


# —— 逐句歌词美术字（卡拉OK点亮 · 每字随演唱真时点亮起 = 真卡点）——
def _lyric_char(canvas, ch, cx, y, size, ink, outline, ow, alpha, angle=0.0, glow=0.0):
    """底部歌词单字：飘逸行草 + 金多向描边双钩 + 墨填。点亮瞬间可带微旋(angle)+金辉(glow)。
    (cx,y) 为左上锚点；旋转绕字心（对称 pad）避免位移漂。"""
    font = ImageFont.truetype(FONT_LYRIC, size)
    pad = max(ow * 3, int(size * 0.4)) + 6
    cell = Image.new("RGBA", (size + pad * 2, size + pad * 2), (0, 0, 0, 0))
    dc = ImageDraw.Draw(cell)
    ax = ay = pad
    if glow > 0.01:
        gl = Image.new("RGBA", cell.size, (0, 0, 0, 0))
        ImageDraw.Draw(gl).text((ax, ay), ch, font=font, fill=(*GOLD, alpha))
        gl = gl.filter(ImageFilter.GaussianBlur(int(size * 0.16)))
        gl.putalpha(gl.getchannel("A").point(lambda v: int(v * glow)))
        cell.alpha_composite(gl)
    for ox, oy in ((-ow, 0), (ow, 0), (0, -ow), (0, ow),
                   (-ow, -ow), (ow, ow), (-ow, ow), (ow, -ow)):
        dc.text((ax + ox, ay + oy), ch, font=font, fill=(*outline, alpha))
    dc.text((ax, ay), ch, font=font, fill=(*ink, alpha))
    if abs(angle) > 0.1:
        cell = cell.rotate(angle, expand=True, resample=Image.BICUBIC)
    canvas.alpha_composite(cell, (int(cx + size / 2 - cell.width / 2),
                                  int(y + size / 2 - cell.height / 2)))


def lyric_karaoke(canvas, shot, t):
    """底部横排国风歌词：逐字在演唱时点亮起（真卡点），未唱字幽微预览，
    点亮瞬间金辉脉冲。底部暖墨渐层 scrim 保可读、不挡脸（脸在画面上半）。"""
    ly = shot.lyric
    if not ly:
        return
    # 淡入淡出按"整句显示窗口"（跨多镜连续，不在镜界闪烁）
    d0 = ly.get("disp0", shot.t0)
    d1 = ly.get("disp1", shot.t1)
    fade = clamp((t - d0) / 0.3) * clamp((d1 - t) / 0.3)
    if fade <= 0.01:
        return

    size, gap, space_extra = 76, 22, 54   # 行草笔画细、需更大字号+更宽字距透气
    chars = ly["chars"]
    # 布局宽度（空格=乐句留白）
    font = ImageFont.truetype(FONT_LYRIC, size)
    d0 = ImageDraw.Draw(canvas)
    widths = []
    for ch, _ct in chars:
        if ch == " ":
            widths.append(space_extra)
        else:
            widths.append(int(d0.textlength(ch, font=font)) + gap)
    total = sum(widths)
    x = (W - total) // 2
    base_y = int(H * 0.80)          # 底部带（避开上半身脸部）

    # 暖墨底 scrim（禁冷色；只在底部，背景仍可见）
    scrim = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ds = ImageDraw.Draw(scrim)
    top = int(H * 0.72)
    for yy in range(top, H):
        a = int(150 * fade * ((yy - top) / (H - top)) ** 1.3)
        ds.line([(0, yy), (W, yy)], fill=(30, 19, 11, a))
    canvas.alpha_composite(scrim)

    idx_c = 0
    for (ch, ct), w in zip(chars, widths):
        if ch == " ":
            x += w
            continue
        if ct is None or t >= ct:            # 已唱：点亮（金钩墨填 + 弹跳微旋金辉）
            age = (t - ct) if ct is not None else 1.0
            pop = clamp(1 - age / 0.26)       # 点亮瞬间脉冲
            a = int(255 * fade)
            ow = 3 + int(pop * 4)
            dy = int(pop * -14)               # 更明显弹起
            spin = pop * (7 if idx_c % 2 else -7)  # 点亮甩一下（飘逸）
            _lyric_char(canvas, ch, x, base_y + dy, size, INK, GOLD, ow, a,
                        angle=spin, glow=pop * 0.6)
            if pop > 0.05:                    # 点亮金辉描边
                _lyric_char(canvas, ch, x, base_y + dy, size, GOLD, GOLD, ow + 2,
                            int(160 * pop * fade), angle=spin)
        else:                                 # 未唱：幽微预览（可见全句，不抢眼）
            _lyric_char(canvas, ch, x, base_y, size, (150, 120, 92),
                        (90, 66, 44), 2, int(70 * fade))
        idx_c += 1
        x += w

    # 演唱者标签（左下角小金牌 · 国风）
    if shot.singer:
        f2 = ImageFont.truetype(FONT_TITLE, 40)
        tag = f"· {shot.singer} ·"
        tw = int(d0.textlength(tag, font=f2))
        ov = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(ov)
        tx, ty = 70, base_y - 96
        d.rounded_rectangle([tx - 18, ty - 8, tx + tw + 18, ty + 54],
                            radius=10, fill=(*SEAL_RED, int(210 * fade)))
        d.text((tx, ty), tag, font=f2, fill=(255, 246, 234, int(240 * fade)))
        canvas.alpha_composite(ov)


# ————————————————— 立绘落位 —————————————————
# ————————————————— V4 新手法（V3 无 · 手法层创新 · 全 R1 安全）—————————————————
_SPLIT_CROPS = [(0.16, 0.0, 0.84, 0.30),   # 面部近景
                (0.05, 0.0, 0.95, 0.56),   # 半身
                None]                       # 全身


def _place_split(canvas, shot, t, downbeats):
    """分屏切割：竖切 3 格，每格同角色不同景别，错位上下滑入，金线分隔。
    affine(缩放/位移)+crop(景别)+alpha 合成，立绘像素零改 · R1 安全。"""
    lt = t - shot.t0
    dur = shot.t1 - shot.t0
    dbp = pulse(t, downbeats, 0.22)
    n = 3
    pw = W // n
    for i in range(n):
        crop = _SPLIT_CROPS[i]
        target_h = int(H * (0.94 if crop is None else 0.80))
        layer = prep_layer(shot.doll, crop, target_h)
        sc = 1.0 + 0.06 * math.sin(lt * 1.6 + i) + dbp * 0.05
        d = layer.resize((max(1, int(layer.width * sc)),
                          max(1, int(layer.height * sc))), Image.LANCZOS)
        ea = clamp((lt - i * 0.13) / 0.5)
        if ea <= 0:
            continue
        slide = int((1 - back_out(ea)) * H * 0.42) * (1 if i % 2 else -1)
        panel = Image.new("RGBA", (pw, H), (0, 0, 0, 0))
        dx = pw // 2 - d.width // 2
        dy = (H - d.height) // 2 + slide
        dy = max(int(H * 0.045), min(dy, H - d.height - int(H * 0.02)))
        composite_depth(panel, d, dx, dy)
        panel.alpha_composite(d, (dx, dy))
        if ea < 1.0:
            panel.putalpha(panel.getchannel("A").point(
                lambda v: int(v * ease_out(ea))))
        canvas.alpha_composite(panel, (i * pw, 0))
    dd = ImageDraw.Draw(canvas)
    for i in range(1, n):
        x = i * pw
        dd.rectangle([x - 3, 0, x + 3, H], fill=(*GOLD, 235))
    return (W / 2, H * 0.5, float(W), float(H))


def _place_kaleido(canvas, shot, t, beats, downbeats):
    """节奏分身：同立绘 5 个缩放副本沿横弧排开，中心大、两侧虚，逐拍 pop。
    affine(缩放/位移)+alpha 合成 · R1 安全。"""
    lt = t - shot.t0
    dbp = pulse(t, downbeats, 0.22)
    base = prep_layer(shot.doll, shot.crop, int(H * shot.hfrac))
    n = 5
    cx0, cy0, R = W / 2, H * 0.56, W * 0.34
    order = [2, 1, 3, 0, 4]                 # 中心先出 → 两侧铺开
    bx0, bx1 = W, 0
    for rank, i in enumerate(order):
        fx = (i - (n - 1) / 2) / ((n - 1) / 2)   # -1..1
        cx = cx0 + fx * R
        cy = cy0 - (1 - fx * fx) * H * 0.06
        base_sc = 0.50 + 0.30 * (1 - abs(fx))
        ea = clamp((lt - rank * 0.09) / 0.42)
        if ea <= 0:
            continue
        sc = base_sc * (0.2 + 0.8 * back_out(ea)) * (1 + dbp * 0.10)
        d = base.resize((max(1, int(base.width * sc)),
                         max(1, int(base.height * sc))), Image.LANCZOS)
        px = int(cx - d.width / 2)
        py = int(cy - d.height * 0.5)
        py = max(int(H * 0.045), min(py, H - d.height - int(H * 0.02)))
        center = abs(fx) < 0.34
        amul = 1.0 if center else 0.70
        if amul < 1.0 or ea < 1.0:
            d = d.copy()
            d.putalpha(d.getchannel("A").point(
                lambda v: int(v * amul * ease_out(ea))))
        if center:
            composite_depth(canvas, d, px, py)
        canvas.alpha_composite(d, (px, py))
        bx0, bx1 = min(bx0, px), max(bx1, px + d.width)
    return ((bx0 + bx1) / 2, cy0, float(max(1, bx1 - bx0)), float(H * 0.42))


def speed_impact_overlay(canvas, t, beats, downbeats, cx, cy):
    """漫画冲击框：重拍放射速度线 + 扩张冲击环。overlay 绘制 · R1 安全。"""
    dbp = pulse(t, downbeats, 0.30)
    bp = pulse(t, beats, 0.16)
    k = max(dbp, bp * 0.6)
    if k < 0.06:
        return
    ov = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    dd = ImageDraw.Draw(ov)
    rng = random.Random(7)
    r1 = max(W, H) * 0.9
    for _ in range(48):
        ang = rng.uniform(0, 2 * math.pi)
        r0 = min(W, H) * (0.30 + 0.06 * rng.random())
        w = rng.choice([2, 3, 4])
        dd.line([cx + math.cos(ang) * r0, cy + math.sin(ang) * r0,
                 cx + math.cos(ang) * r1, cy + math.sin(ang) * r1],
                fill=(255, 238, 196, int(150 * k)), width=w)
    rr = min(W, H) * (0.16 + 0.32 * (1 - k))
    dd.ellipse([cx - rr, cy - rr, cx + rr, cy + rr],
               outline=(255, 230, 170, int(210 * k)), width=max(2, int(11 * k)))
    canvas.alpha_composite(ov)


def _silhouette_sweep(canvas, d, px, py, ea):
    """剪影点亮登场：在真立绘上叠 alpha 塑形的暗剪影，一道金光从左扫到右把它擦除。
    只叠暗层+擦除+金边，真立绘像素在下方原样不动 · R1 安全。"""
    w, h = d.width, d.height
    a = np.array(d.getchannel("A"), float) / 255.0
    xs = np.arange(w)[None, :].astype(float)
    edge = ea * (w + 160) - 80
    m = np.clip((xs - edge) / 70.0, 0, 1)   # 右侧仍为剪影，左侧已露真身
    sil = np.zeros((h, w, 4), np.uint8)
    sil[..., 0], sil[..., 1], sil[..., 2] = 34, 24, 18
    sil[..., 3] = (a * m * 255).astype(np.uint8)
    canvas.alpha_composite(Image.fromarray(sil, "RGBA"), (px, py))
    gx = np.exp(-((xs - edge) ** 2) / (2 * 42.0 ** 2))
    glow = np.zeros((h, w, 4), np.uint8)
    glow[..., 0], glow[..., 1], glow[..., 2] = 255, 224, 150
    glow[..., 3] = (a * gx * 205).astype(np.uint8)
    canvas.alpha_composite(Image.fromarray(glow, "RGBA"), (px, py))


def place_doll(canvas, shot, t, beats, downbeats, montage_beats):
    if shot.cam == "split":
        return _place_split(canvas, shot, t, downbeats)
    if shot.cam == "kaleido":
        return _place_kaleido(canvas, shot, t, beats, downbeats)
    dbp = pulse(t, downbeats, 0.22)
    lt = t - shot.t0
    dur = shot.t1 - shot.t0
    prog = lt / dur

    crop = shot.crop
    if shot.cam == "montage":
        idx = sum(1 for mb in montage_beats if mb <= t) - 1
        crop = shot.montage_crops[max(0, idx) % len(shot.montage_crops)]

    layer = prep_layer(shot.doll, crop, int(H * shot.hfrac))

    # —— 运镜幅度较 V3 抬 3 档（动效提升3个档次）：推拉更狠、环绕/甩/摇/荷兰角更大、
    #    入场更决绝。纵向过缩由下方"出画兜底"等比钳回 → 头脚永不砍（R1 安全）。——
    scale, angle, ox, oy = 1.0, 0.0, 0.0, 0.0
    breathe = 1 + 0.018 * math.sin(lt * 2)
    if shot.cam == "push_in":           # 推入：0.18→0.42，逼近式冲镜
        scale = 1.0 + ease_in_out(prog) * 0.42
    elif shot.cam == "pull_out":        # 拉远：1.20→1.46 起手，收 0.20→0.42
        scale = 1.46 - ease_in_out(prog) * 0.42
    elif shot.cam == "dutch":           # 荷兰角：-6°→-14°，倾斜更狠 + 推进
        scale = 1.08 + ease_in_out(prog) * 0.20
        angle = -14 + prog * 7
    elif shot.cam == "orbit":
        scale = 1.10 + ease_in_out(prog) * 0.10
        angle = math.sin(lt * 1.1) * 9
        ox = math.sin(lt * 0.9) * 110
    elif shot.cam == "whip_left":       # 甩镜：520→860 横扫（settle 回中心可见）
        ox = (0.5 - prog) * 860
        angle = -7
    elif shot.cam == "whip_right":      # 甩镜：向右高速甩出 + 残影
        ox = -(0.5 - prog) * 860
        angle = 7
    elif shot.cam == "pan":             # 摇镜：横移 300→560，背景差速视差更强
        ox = (prog - 0.5) * 560
        scale = 1.10 + ease_in_out(prog) * 0.08
    elif shot.cam == "track":           # 跟拍：弧线随焦幅度加大
        ox = math.sin(lt * 0.65) * 64 + (prog - 0.5) * 150
        scale = 1.04 + ease_in_out(prog) * 0.18
    elif shot.cam == "low_angle":       # 仰拍：向上延伸 0.07H→0.14H，压迫感翻倍
        scale = 1.10 + ease_in_out(prog) * 0.26
        oy = -int(H * 0.14 * ease_in_out(prog))
    elif shot.cam == "bird_eye":        # 俯视：压缩 + 上移加大（俯冲感）
        scale = 0.82 + ease_in_out(prog) * 0.14
        oy = -int(H * 0.11)
    elif shot.cam == "orbit_fast":      # 环绕：角±9→±18、横摆 90→190，大弧戏剧
        scale = 1.12 + ease_in_out(prog) * 0.14
        angle = math.sin(lt * 2.4) * 18
        ox = math.sin(lt * 1.9) * 190
    elif shot.cam == "spin":            # 旋转：360°整圈爆发落位（原 270°）
        k = clamp(lt / 0.5)
        angle = (1 - ease_out(k)) * 360
        scale = 0.82 + ease_out(k) * 0.30
    elif shot.cam == "montage":
        mi = sum(1 for mb in montage_beats if mb <= t)
        scale = 1.04 + (mi % 2) * 0.12
        angle = (-1) ** mi * 6
    scale *= breathe * (1 + dbp * 0.08)

    ea = clamp(lt / 0.5)
    if shot.enter == "slam_up":         # 砸地登场：从更低处更狠弹起 + 落地过冲缩放
        oy += (1 - back_out(ea)) * 660
        scale *= (1.22 - 0.22 * ease_out(ea))
    elif shot.enter == "pop":           # 爆现：更小起手 → 过冲放大定位
        scale *= (0.40 + 0.60 * back_out(ea))
    elif shot.enter == "slide_right":   # 侧滑入：横移更长
        ox += (back_out(ea) - 1) * 1020

    if "shake" in shot.fx:
        sh = pulse(t, downbeats, 0.10)
        ox += math.sin(t * 90) * sh * 15
        oy += math.cos(t * 84) * sh * 11

    d = layer.resize((max(1, int(layer.width * scale)), max(1, int(layer.height * scale))),
                     Image.LANCZOS)
    if abs(angle) > 0.1:
        d = d.rotate(angle, expand=True, resample=Image.BICUBIC)

    if "rays" in shot.fx:
        rsz = int(min(W, H) * (1.2 + dbp * 0.15))
        rr = RAYS.resize((rsz, rsz), Image.LANCZOS).rotate(lt * 10, resample=Image.BICUBIC)
        rr.putalpha(rr.getchannel("A").point(lambda v: int(v * (0.55 + dbp * 0.45))))
        canvas.alpha_composite(rr, (int(W / 2 - rsz / 2 + ox), int(H * 0.44 - rsz / 2)))

    # —— 出画兜底（禁砍头/禁掉脚 · R1 安全：仅等比缩放+定位，不动立绘像素）——
    top_margin = int(H * 0.045)               # 头顶留白
    if crop is None:                          # 整 figure：头顶+脚都必须留在画内
        foot_margin = int(H * 0.02)
        avail = H - top_margin - foot_margin
        if d.height > avail:                  # 卡点缩放叠爆画布 → 等比钳回
            rr = avail / d.height
            d = d.resize((max(1, round(d.width * rr)), avail), Image.LANCZOS)
        px = int(W / 2 - d.width / 2 + ox)
        # 仰拍/俯视上移（oy<0）绝不把头顶推出画外：py 以 top_margin 兜底。
        # 因人物已刻意压小（hfrac 0.58–0.76），缩放运镜仍有生长空间，floor 只在极端处生效。
        py = max(top_margin, int(H - foot_margin - d.height + oy))
    else:                                     # 景别裁切：保证头顶不砍，底部可出血
        px = int(W / 2 - d.width / 2 + ox)
        py = max(top_margin, int(H - d.height + oy + 30))

    if "mirror" in shot.fx:
        m = d.transpose(Image.FLIP_LEFT_RIGHT)
        lx, rx = int(W * 0.02 + ox), int(W * 0.52 + ox)
        composite_depth(canvas, m, lx, py)
        composite_depth(canvas, d, rx, py)
        canvas.alpha_composite(m, (lx, py))
        canvas.alpha_composite(d, (rx, py))
        x0, x1 = min(lx, rx), max(lx + d.width, rx + d.width)
        return ((x0 + x1) / 2, py + d.height / 2, float(x1 - x0), float(d.height))

    if shot.cam.startswith("whip") or (shot.enter == "slide_right" and ea < 0.6):
        for k in range(1, 6):
            g = d.copy()
            g.putalpha(g.getchannel("A").point(lambda v: int(v * 0.14)))
            canvas.alpha_composite(g, (px - k * 30, py))
    ent_fade = ease_out(ea) if shot.enter in ("pop", "slide_right", "flash") else 1.0
    if ent_fade > 0.55:
        composite_depth(canvas, d, px, py)
    if ent_fade < 1.0:
        d.putalpha(d.getchannel("A").point(lambda v: int(v * ent_fade)))
    canvas.alpha_composite(d, (px, py))
    if shot.enter == "silhouette":            # 剪影点亮登场（暗层擦除 · R1 安全）
        se = clamp(lt / 0.62)
        if se < 1.0:
            _silhouette_sweep(canvas, d, px, py, se)
    return (px + d.width / 2, py + d.height / 2, float(d.width), float(d.height))


# —— 多人合体（solo/2p/4p 并排 · 每人保 §2 三件套 · 错位卡点入场）——
_GROUP_CENTERS = {1: (0.5,), 2: (0.31, 0.69), 3: (0.21, 0.5, 0.79),
                  4: (0.15, 0.385, 0.615, 0.85)}


def place_group(canvas, shot, t, beats, downbeats):
    names = shot.group
    n = len(names)
    centers = _GROUP_CENTERS.get(n, tuple((i + 0.5) / n for i in range(n)))
    dbp = pulse(t, downbeats, 0.22)
    lt = t - shot.t0
    dur = shot.t1 - shot.t0
    prog = lt / dur

    # 整组相机（共享缩放/横移）· 幅度较 V3 抬 3 档（多人合体同样要"活"）
    gscale = 1.0
    gox = 0.0
    if shot.cam == "push_in":
        gscale = 1.0 + ease_in_out(prog) * 0.28
    elif shot.cam == "pull_out":
        gscale = 1.34 - ease_in_out(prog) * 0.32
    elif shot.cam == "sway":
        gox = math.sin(lt * 0.9) * 95
    elif shot.cam == "pan":
        gox = (prog - 0.5) * 420
    elif shot.cam == "orbit_fast":
        gscale = 1.10 + ease_in_out(prog) * 0.12
        gox = math.sin(lt * 2.0) * 140
    elif shot.cam == "low_angle":
        gscale = 1.10 + ease_in_out(prog) * 0.18
    elif shot.cam == "spin":
        k = clamp(lt / 0.5)
        gscale = 0.82 + ease_out(k) * 0.30
    elif shot.cam == "track":
        gox = math.sin(lt * 0.65) * 52 + (prog - 0.5) * 120
    gscale *= (1 + 0.014 * math.sin(lt * 2)) * (1 + dbp * 0.06)

    top_margin = int(H * 0.045)
    foot_margin = int(H * 0.02)
    avail = H - top_margin - foot_margin

    # 外→内绘制（中心角色压顶），错位入场（依次弹入）
    order = sorted(range(n), key=lambda i: abs(centers[i] - 0.5), reverse=True)
    xs = []
    for i in order:
        # 中心角色略高，营造层次
        hh = shot.hfrac * (1.06 if abs(centers[i] - 0.5) < 0.22 else 0.92) if n >= 3 else shot.hfrac
        layer = prep_layer(names[i], None, int(H * hh))
        d = layer.resize((max(1, int(layer.width * gscale)),
                          max(1, int(layer.height * gscale))), Image.LANCZOS)
        if d.height > avail:                        # 出画钳回（禁砍头掉脚 · R1 安全）
            rr = avail / d.height
            d = d.resize((max(1, round(d.width * rr)), avail), Image.LANCZOS)
        # 错位入场：第 k 个在前 0.5s 内依次 slam_up
        stag = order.index(i) / max(1, n) * 0.30
        ea = clamp((lt - stag) / 0.5)
        oy = (1 - back_out(ea)) * 620 if shot.enter in ("cascade", "slam_up") else 0.0
        fade = ease_out(ea) if shot.enter in ("cascade", "pop", "flash") else 1.0
        px = int(centers[i] * W - d.width / 2 + gox)
        py = int(H - foot_margin - d.height + oy)
        if fade > 0.55:
            composite_depth(canvas, d, px, py)
        if fade < 1.0:
            d = d.copy()
            d.putalpha(d.getchannel("A").point(lambda v: int(v * fade)))
        canvas.alpha_composite(d, (px, py))
        xs += [px, px + d.width]
    x0, x1 = min(xs), max(xs)
    return ((x0 + x1) / 2, H * 0.55, float(x1 - x0), float(avail))


# ————————————————— 背景 —————————————————
def make_bg():
    """加载 gpt-image-2 生成的插画级背景 plate（禁 PIL 现搓渐变——见 memory
    feedback_no-cheap-procedural-background）。plate 缺失 = fail-closed 停。"""
    plate = _PATHS.bg_path
    if not plate.exists():
        sys.exit(f"[err] 背景 plate 缺失: {plate}\n"
                 f"      先跑: python3 pipeline/voice_room/gen_paperdoll_bg.py "
                 f"--prompt-file <提示词> --out {plate}")
    img = Image.open(plate).convert("RGB").resize((W, H), Image.LANCZOS)
    return np.array(img, float)


def _alpha_halo(layer, color, blur, gain=1.0):
    """从 alpha 生成柔光晕（背光 rim / 落影用）· 返回 (RGBA, pad)。"""
    pad = int(blur * 3)
    a = layer.getchannel("A")
    big = Image.new("L", (a.width + pad * 2, a.height + pad * 2), 0)
    big.paste(a, (pad, pad))
    big = big.filter(ImageFilter.GaussianBlur(blur))
    glow = Image.new("RGBA", big.size, (*color, 0))
    glow.putalpha(big.point(lambda v: min(255, int(v * gain))))
    return glow, pad


def composite_depth(canvas, d, px, py):
    """§2 三件套：把立绘从背景里"拔"出来 —— 地面接触影 + 斜后落影 + 金色背光 rim。
    全部走 alpha 合成(不动立绘像素，R1 安全)。顺序：影→rim→(调用方再贴立绘)。"""
    cx = px + d.width / 2
    foot = py + d.height
    # 1) 地面接触椭圆影（把脚"钉"在地上）
    ell = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ew = d.width * 0.60
    ImageDraw.Draw(ell).ellipse(
        [cx - ew / 2, foot - 30, cx + ew / 2, foot + 18], fill=(38, 24, 14, 165))
    canvas.alpha_composite(ell.filter(ImageFilter.GaussianBlur(20)))
    # 2) 斜后方落影（暗、虚、偏移）
    sa = d.getchannel("A").point(lambda v: int(v * 0.42))
    shadow = Image.new("RGBA", d.size, (28, 18, 12, 0))
    shadow.putalpha(sa)
    shadow = shadow.filter(ImageFilter.GaussianBlur(13))
    canvas.alpha_composite(shadow, (px + 22, py + 14))
    # 3) 金色背光 rim（立绘遮住光核中心，只剩边缘 halo = 背光轮廓）
    halo, pad = _alpha_halo(d, GOLD, 15, gain=1.35)
    canvas.alpha_composite(halo, (px - pad, py - pad))


def _montage_cuts(shots):
    """montage 镜的子切时点 = 把该镜窗口按 crop 数等分（片无关；与手排的
    半拍卡点在 30fps 帧边界上落点一致）。"""
    cuts = []
    for s in shots:
        if s.cam == "montage" and s.montage_crops:
            n = len(s.montage_crops)
            cuts += [s.t0 + k * (s.t1 - s.t0) / n for k in range(n)]
    return cuts


# ————————————————— 单帧 —————————————————
def render_frame(t, shots, beats, downbeats, bg0, fields):
    shot = active_shot(shots, t)
    bp = pulse(t, beats, 0.14)
    dbp = pulse(t, downbeats, 0.22)
    lt = t - shot.t0
    px_par = math.sin(t * 0.45) * 70  # 背景基准摆幅（各层差速见 scene_backdrop）

    frame = scene_backdrop(t, bg0, px_par, plate_path=shot.bg)
    if "shafts" in shot.fx:
        frame = screen(frame, light_shafts(t))
    if "bokeh_far" in shot.fx:
        frame = screen(frame, fields["far"].render(t * 0.5, 1.2, px_par))
    if "streak_radial" in shot.fx:
        frame = screen(frame, streaks(t, "radial", 0.5 + dbp * 0.5))
    if "spark" in shot.fx:
        frame = screen(frame, fields["spark"].render(t, 1 + bp, px_par * 0.5))
    if "bokeh" in shot.fx:
        frame = screen(frame, fields["spark"].render(t * 0.4, 1.4))

    canvas = Image.fromarray(np.clip(frame, 0, 255).astype(np.uint8)).convert("RGBA")

    if "branch_sway" in shot.fx:  # 花枝摆动：铺在立绘之后（背景动效，不挡脸）
        branch_layer(canvas, t)

    doll_bbox = None
    if "film_strip" in shot.fx:
        # B1轴胶片走带：加载本镜所有立绘，整体走带展示
        names = shot.group if shot.group else ([shot.doll] if shot.doll else [])
        strip_dolls = []
        for dn in names:
            p = _PATHS.assets_dir / f"{dn}_cutout.png"
            if p.exists():
                strip_dolls.append(Image.open(p).convert("RGBA"))
        if strip_dolls:
            film_strip_composite(canvas, strip_dolls, t, beats, downbeats)
    elif shot.group:                     # 多人合体展示（solo/2p/4p）
        doll_bbox = place_group(canvas, shot, t, beats, downbeats)
        if "echo" in shot.fx and doll_bbox:
            x0, y0, x1, y1 = doll_bbox
            cx_d, cy_d = (x0 + x1) // 2, y1
            if shot.cam in ("push", "dutch"):
                direction = "right"
            elif shot.cam == "pull":
                direction = "up"
            else:
                direction = "left"
            # Use canvas snapshot as echo source — render echo before front layer
        elif "shatter" in shot.fx and doll_bbox:
            pass  # shatter handled per-doll below
    elif shot.doll:                      # 单人展示
        if "shatter" in shot.fx:
            # C3轴碎片聚合：先用普通 place_doll 出结果，再对立绘做 shatter
            p = _PATHS.assets_dir / f"{shot.doll}_cutout.png"
            if p.exists():
                doll_img = Image.open(p).convert("RGBA")
                scale = shot.hfrac * H / doll_img.height
                dw, dh = int(doll_img.width * scale), int(doll_img.height * scale)
                doll_scaled = doll_img.resize((dw, dh), Image.LANCZOS)
                cx_d = W // 2
                cy_d = int(H * 0.88)
                shatter_reveal(canvas, doll_scaled, cx_d, cy_d, lt)
                doll_bbox = (cx_d - dw // 2, cy_d - dh, cx_d + dw // 2, cy_d)
        else:
            doll_bbox = place_doll(canvas, shot, t, beats, downbeats, _montage_cuts(shots))
            if "echo" in shot.fx and doll_bbox:
                p = _PATHS.assets_dir / f"{shot.doll}_cutout.png"
                if p.exists():
                    doll_img = Image.open(p).convert("RGBA")
                    scale = shot.hfrac * H / doll_img.height
                    dw = int(doll_img.width * scale)
                    doll_small = doll_img.resize((dw, int(doll_img.height * scale)), Image.LANCZOS)
                    x0, y0, x1, y1 = doll_bbox
                    motion_echo(canvas, doll_small, (x0 + x1) // 2, y1, "left", lt)

    if "speed_impact" in shot.fx:            # 漫画冲击框（重拍放射线+冲击环 · R1 安全）
        if doll_bbox:
            icx, icy = doll_bbox[0], doll_bbox[1]
        else:
            icx, icy = W / 2, H * 0.5
        speed_impact_overlay(canvas, t, beats, downbeats, icx, icy)

    front = np.zeros((H, W, 3))
    if shot.cam != "static":  # 前景散景：大而虚的暖光斑，飘在立绘之前 = 纵深线索
        fg = fields["fg"].render(t * 0.6, 0.7, px_par * 1.7)
        fg = np.array(Image.fromarray(np.clip(fg, 0, 255).astype(np.uint8))
                      .filter(ImageFilter.GaussianBlur(10)), float)
        front = screen(front, fg)
    if "streak_left" in shot.fx:
        front = screen(front, streaks(t, "left", 0.85))
    if "petal" in shot.fx:
        front = screen(front, fields["petal"].render(t, 1 + dbp))
    if "rain" in shot.fx:     # 前景暖白雨丝（逐帧真下落 = 背景非静态）
        front = screen(front, rain_layer(t, 1.0))
    if front.any():
        arr = screen(np.array(canvas.convert("RGB"), float), front)
        canvas = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")


    if "flare" in shot.fx:
        fk = 0.4 + pulse(t, downbeats, 0.25) * 0.6
        fsz = 720
        fl = FLARE.resize((fsz, fsz))
        fl.putalpha(fl.getchannel("A").point(lambda v: int(v * fk)))
        fxx = int(W * (0.2 + 0.6 * ((t * 0.3) % 1)))
        canvas.alpha_composite(fl, (fxx - fsz // 2, int(H * 0.3)))

    kinetic_text(canvas, shot, t)
    lyric_karaoke(canvas, shot, t)  # 底部逐字点亮歌词美术字（真卡点）

    arr = np.array(canvas.convert("RGB"), float)

    # —— 转场（入场 0.30s · 较 V3 抬 3 档：更长、更狠、带整帧冲击）——
    TR = 0.30
    if lt < TR:
        k = 1 - lt / TR                        # 1→0 缓出
        ke = ease_out(k)
        if shot.trans == "flash":
            # 闪白 + 整帧过冲缩放砸入（1.12→1.0），切换有"撞击"感
            arr = screen(arr, np.ones((H, W, 3)) * np.array(WARM_WHITE, float) * k * 0.85)
            zf = 1 + ke * 0.12
            z = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).resize(
                (int(W * zf), int(H * zf)))
            z = z.crop(((z.width - W) // 2, (z.height - H) // 2,
                        (z.width - W) // 2 + W, (z.height - H) // 2 + H))
            arr = arr * (1 - ke * 0.7) + np.array(z, float) * (ke * 0.7)
        elif shot.trans in ("swipe_l", "swipe_r"):
            d = "left" if shot.trans == "swipe_l" else "right"
            # 甩镜横扫：光条 + 整帧横向位移 260px 冲入
            arr = screen(arr, streaks(t, d, k * 1.9))
            sh = int((260 * ke) * (1 if d == "left" else -1))
            arr = np.roll(arr, sh, axis=1)
        elif shot.trans == "zoomblur":
            zf = 1 + ke * 0.30                  # 0.12→0.30 缩放模糊更猛
            z = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).resize(
                (int(W * zf), int(H * zf)))
            z = z.crop(((z.width - W) // 2, (z.height - H) // 2,
                        (z.width - W) // 2 + W, (z.height - H) // 2 + H))
            arr = arr * (1 - ke * 0.75) + np.array(z, float) * (ke * 0.75)

    # —— 卡点闪白 + 重拍缩放模糊 ——
    flash = min(0.7, bp * 0.09 + dbp * 0.15)
    if flash > 0.01:
        arr = screen(arr, np.ones((H, W, 3)) * np.array(WARM_WHITE, float) * flash)
    if dbp > 0.15:
        z = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).resize(
            (int(W * 1.06), int(H * 1.06)))
        z = z.crop(((z.width - W) // 2, (z.height - H) // 2,
                    (z.width - W) // 2 + W, (z.height - H) // 2 + H))
        arr = arr * (1 - dbp * 0.32) + np.array(z, float) * (dbp * 0.32)

    # —— 漏光 + 分段调色 + 辉光 + 颗粒 + 暗角 ——
    arr = screen(arr, light_leak(t, 0.16 + dbp * 0.12))
    g = np.array(shot.grade, float) / np.array(CREAM, float)
    arr = np.clip(arr * (0.85 + 0.15 * g[None, None, :]), 0, 255)
    arr = bloom(arr, 205, 0.6)
    arr = grain(arr, t, 6.0)
    yy, xx = np.mgrid[0:H, 0:W]
    r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
    vig = np.clip((r - 0.72) / 0.6, 0, 1)[:, :, None] * 0.30
    arr = arr * (1 - vig) + np.array([150, 110, 78], float) * vig
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)), doll_bbox


def render(paths: PVPaths, shots: list, start: float = 0.0, end: float | None = None) -> int:
    """渲染一条纸片人卡点 MV。paths=片专属素材，shots=片专属分镜（build_shots 产物）。
    返回 exit code：0 ok / 1 ffmpeg fail / 3 冻结门 fail。"""
    global RAYS, FLARE, MOON, RIDGES, _PATHS, _BG_CACHE, _BRANCH
    _PATHS = paths
    _BG_CACHE.clear()
    _BRANCH = None
    if end is None:
        end = max(s.t1 for s in shots)
    paths.out_dir.mkdir(parents=True, exist_ok=True)
    paths.frame_dir.mkdir(parents=True, exist_ok=True)
    for f in paths.frame_dir.glob("*.png"):
        f.unlink()

    tempo, beats = load_beats()
    downbeats = beats[::2]
    RAYS = make_rays(1200)
    FLARE = make_flare(720)
    bg0 = make_bg()
    fields = {"spark": Field(56, "spark", 7, 1.0),
              "far": Field(30, "spark", 21, 1.8),
              "fg": Field(13, "spark", 33, 2.8),
              "petal": Field(40, "petal", 11, 1.0)}
    print(f"[info] {tempo:.0f}BPM · {len(shots)}镜 · {start}-{end}s")

    n = int((end - start) * FPS)
    track = []
    for i in range(n):
        t = start + i / FPS
        img, bbox = render_frame(t, shots, beats, downbeats, bg0, fields)
        img.save(paths.frame_dir / f"f{i:05d}.png")
        si = next((j for j, s in enumerate(shots) if s.t0 <= t < s.t1), len(shots) - 1)
        track.append({"t": round(t, 4), "shot": si,
                      "bbox": [round(v, 2) for v in bbox] if bbox else None})
        if i % 30 == 0:
            print(f"[frame] {i}/{n} t={t:.2f}")

    track_path = paths.out_dir / f"pv_{start:.0f}_{end:.0f}s_v3.motion.json"
    track_path.write_text(json.dumps(
        {"fps": FPS, "w": W, "h": H, "start": start, "end": end, "track": track},
        ensure_ascii=False))

    out = paths.out_dir / f"pv_{start:.0f}_{end:.0f}s_v3.mp4"
    cmd = [FFMPEG, "-y", "-framerate", str(FPS), "-i", str(paths.frame_dir / "f%05d.png"),
           "-ss", str(start), "-t", str(end - start), "-i", str(paths.wav),
           "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-pix_fmt", "yuv420p",
           "-crf", "18", "-c:a", "aac", "-b:a", "192k", "-shortest", str(out)]
    print("[ffmpeg] 合成+混音…")
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        print(r.stderr[-800:])
        return 1
    print(f"[ok] {out} ({out.stat().st_size // 1024}KB)")

    # —— 冻结自检门（R9 · 2s 硬线，fail-closed）——
    sys.path.insert(0, str(ROOT))
    from pipeline.gate_check_motion import check_track
    passed, report = check_track(track_path)
    print(report)
    if not passed:
        print("[gate] 冻结自检 FAIL —— 见上；本片按 R9 不得外发")
        return 3
    return 0
