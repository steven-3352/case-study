#!/usr/bin/env python3
"""语音厅《明月天涯》· 纸片人立绘卡点 PV · v3 premium（16:9·1920×1080）.

立绘像素零改动（仿射+裁切换景别）。多分镜快切卡点。目标对标参考级国乙 PV：
- 分层动态背景：暖色渐变 + 移动光轴 + 多层景深散景 + 水墨月 + 视差
- premium FX：真高斯辉光 bloom + 粗锥形光 streak + 暖光漏光 + 胶片颗粒 + 尘埃
- 设计转场：光streak扫切 / zoom-blur match cut / 闪白
- 分段调色弧：晨金→暖玫→琥珀
- 编排缓动：预备+过冲(back-ease) 入场
全暖色（palette 铁律）。音源 明月天涯 导唱(1).WAV(53.08s·129BPM)=卡点时基。
调用：python gen_paperdoll_pv.py [start] [end]  默认 0 10.73
"""
from __future__ import annotations

import json
import math
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "publish" / "语音厅" / "script_v2_assets"
WAV = ROOT / "publish" / "语音厅" / "明月天涯 导唱(1).WAV"
OUT_DIR = ASSETS / "pv"
FRAME_DIR = OUT_DIR / "_frames"
BEATS_JSON = ASSETS / "beats.json"

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

FONT_TITLE = "/System/Library/Fonts/Supplemental/Songti.ttc"
FONT_LABEL = "/Users/wmzuo/Library/Fonts/SourceHanSansSC-Heavy.otf"


# ————————————————— 节拍 —————————————————
def load_beats():
    if BEATS_JSON.exists():
        d = json.loads(BEATS_JSON.read_text())
        return d["tempo"], d["beats"]
    import librosa
    y, sr = librosa.load(str(WAV), sr=44100, mono=True)
    tempo, beats = librosa.beat.beat_track(y=y, sr=sr, units="time")
    tempo = float(np.atleast_1d(tempo)[0])
    beats = [float(b) for b in beats]
    BEATS_JSON.write_text(json.dumps({"tempo": tempo, "beats": beats}))
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
        im = Image.open(ASSETS / f"{name}_cutout.png").convert("RGBA")
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
    """3 层水墨山脊剪影（远→近 · 暖调 · 视差）。远浅近深、远虚近实。"""
    rng = np.random.default_rng(99)
    specs = (((236, 208, 168), 0.35, 0.60, 0.10, 7),
             ((214, 172, 124), 0.60, 0.72, 0.13, 4),
             ((150, 112, 76), 1.00, 0.86, 0.16, 2))
    out = []
    for col, par, ybase, amp, blur in specs:
        img = Image.new("RGBA", (int(W * 1.3), H), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        xs = np.linspace(0, W * 1.3, 80)
        base = ybase * H
        prof = (np.sin(xs / W * 3 + rng.uniform(0, 6)) * amp * H
                + np.sin(xs / W * 7 + rng.uniform(0, 6)) * amp * H * 0.45
                + np.sin(xs / W * 15 + rng.uniform(0, 6)) * amp * H * 0.18)
        poly = [(0, H)] + [(float(x), float(base - p)) for x, p in zip(xs, prof)] + [(W * 1.3, H)]
        d.polygon(poly, fill=(*col, 232))
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


def scene_backdrop(t, bg_grad, px_par):
    """分层古风场景：暖渐变 → 云霭 → 月盘 → 山脊(视差) → 供人物落位。"""
    frame = screen(bg_grad.copy(), clouds(t))
    canvas = Image.fromarray(np.clip(frame, 0, 255).astype(np.uint8)).convert("RGBA")
    mb = int(math.sin(t * 0.3) * 8)
    canvas.alpha_composite(MOON, (int(W * 0.58), int(H * 0.02) + mb))
    for img, par in RIDGES:
        canvas.alpha_composite(img, (int(-W * 0.15 + px_par * par), 0))
    return np.array(canvas.convert("RGB"), float)


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


def build_shots():
    return [
        Shot(0.00, 2.30, "cy", None, 0.0, "static", "flash", CREAM,
             fx=["shafts", "spark", "streak_radial"], text="明月天涯", trans="flash"),
        Shot(2.30, 4.17, "cy", None, 0.96, "push_in", "slam_up", AMBER,
             fx=["rays", "streak_radial", "spark", "shake", "shafts"], text="明月", trans="zoomblur"),
        Shot(4.17, 5.11, "cy", (0.12, 0.0, 0.88, 0.30), 0.92, "dutch", "pop", ROSE,
             fx=["petal", "flare", "spark"], text="其一", trans="swipe_l"),
        Shot(5.11, 6.04, "cy", (0.05, 0.05, 0.95, 0.58), 0.86, "whip_left", "slide_right", AMBER,
             fx=["streak_left", "mirror"], text="", trans="swipe_r"),
        Shot(6.04, 7.92, "cy", None, 0.9, "orbit", "pop", (240, 200, 160),
             fx=["rays", "petal", "bokeh_far", "shafts"], text="天涯", trans="flash"),
        Shot(7.92, 9.79, "cy", None, 0.9, "montage", "flash", ORANGE,
             fx=["spark", "shake", "streak_radial"], text="",
             trans="flash",
             montage_crops=[(0.18, 0.02, 0.82, 0.26), (0.0, 0.32, 1.0, 0.72),
                            None, (0.1, 0.0, 0.9, 0.4)]),
        Shot(9.79, 10.73, "cy", None, 0.97, "push_in", "slam_up", (250, 210, 165),
             fx=["rays", "spark", "flare", "shafts"], text="明月天涯", trans="zoomblur"),
    ]


def active_shot(shots, t):
    for s in shots:
        if s.t0 <= t < s.t1:
            return s
    return shots[-1]


# ————————————————— 大字 —————————————————
def kinetic_text(canvas, shot, t):
    if not shot.text:
        return
    lt = t - shot.t0
    chars = shot.text
    if chars == "明月天涯":
        size = 132
        y = 150 if shot.t0 < 1 else 128
        gap = 30
        total = size * len(chars) + gap * (len(chars) - 1)
        x0 = (W - total) // 2
        reveal = [shot.t0 + i * 0.47 for i in range(len(chars))] if shot.t0 < 1 \
            else [shot.t0 + 0.05] * len(chars)
        font = ImageFont.truetype(FONT_TITLE, size)
        for i, ch in enumerate(chars):
            if t < reveal[i]:
                continue
            k = ease_out((t - reveal[i]) / 0.3)
            a = int(255 * k)
            dy = int((1 - back_out((t - reveal[i]) / 0.4)) * 50)
            ov = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
            d = ImageDraw.Draw(ov)
            cx = x0 + i * (size + gap)
            for ox, oy in ((-3, 0), (3, 0), (0, -3), (0, 3)):
                d.text((cx + ox, y - dy + oy), ch, font=font, fill=(*GOLD, a))
            d.text((cx, y - dy), ch, font=font, fill=(*INK, a))
            canvas.alpha_composite(ov)
        if t > 2.0 and shot.t0 < 1:
            k = clamp((t - 2.0) / 0.5)
            f2 = ImageFont.truetype(FONT_LABEL, 30)
            ov = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
            d = ImageDraw.Draw(ov)
            sub = "语 音 厅 · 群 星"
            w = d.textlength(sub, font=f2)
            d.text(((W - w) / 2, 312), sub, font=f2, fill=(*GOLD, int(200 * k)))
            canvas.alpha_composite(ov)
    else:
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


# ————————————————— 立绘落位 —————————————————
def place_doll(canvas, shot, t, beats, downbeats, montage_beats):
    dbp = pulse(t, downbeats, 0.22)
    lt = t - shot.t0
    dur = shot.t1 - shot.t0
    prog = lt / dur

    crop = shot.crop
    if shot.cam == "montage":
        idx = sum(1 for mb in montage_beats if mb <= t) - 1
        crop = shot.montage_crops[max(0, idx) % len(shot.montage_crops)]

    layer = prep_layer(shot.doll, crop, int(H * shot.hfrac))

    scale, angle, ox, oy = 1.0, 0.0, 0.0, 0.0
    breathe = 1 + 0.012 * math.sin(lt * 2)
    if shot.cam == "push_in":
        scale = 1.0 + ease_in_out(prog) * 0.18
    elif shot.cam == "pull_out":
        scale = 1.20 - ease_in_out(prog) * 0.20
    elif shot.cam == "dutch":
        scale = 1.05 + ease_in_out(prog) * 0.10
        angle = -6 + prog * 3
    elif shot.cam == "orbit":
        scale = 1.05
        angle = math.sin(lt * 1.1) * 4
        ox = math.sin(lt * 0.9) * 45
    elif shot.cam == "whip_left":
        ox = (0.5 - prog) * 520
        angle = -3
    elif shot.cam == "montage":
        mi = sum(1 for mb in montage_beats if mb <= t)
        scale = 1.02 + (mi % 2) * 0.06
        angle = (-1) ** mi * 3
    scale *= breathe * (1 + dbp * 0.05)

    ea = clamp(lt / 0.5)
    if shot.enter == "slam_up":
        oy += (1 - back_out(ea)) * 480
        scale *= (1.14 - 0.14 * ease_out(ea))
    elif shot.enter == "pop":
        scale *= (0.55 + 0.45 * back_out(ea))
    elif shot.enter == "slide_right":
        ox += (back_out(ea) - 1) * 720

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

    px = int(W / 2 - d.width / 2 + ox)
    py = int(H - d.height + oy + 30)

    if "mirror" in shot.fx:
        m = d.transpose(Image.FLIP_LEFT_RIGHT)
        canvas.alpha_composite(m, (int(W * 0.02 + ox), py))
        canvas.alpha_composite(d, (int(W * 0.52 + ox), py))
        return

    if shot.cam.startswith("whip") or (shot.enter == "slide_right" and ea < 0.6):
        for k in range(1, 6):
            g = d.copy()
            g.putalpha(g.getchannel("A").point(lambda v: int(v * 0.14)))
            canvas.alpha_composite(g, (px - k * 30, py))
    if ea < 1.0 and shot.enter in ("pop", "slide_right", "flash"):
        d.putalpha(d.getchannel("A").point(lambda v: int(v * ease_out(ea))))
    canvas.alpha_composite(d, (px, py))


# ————————————————— 背景 —————————————————
def make_bg():
    top = np.array(CREAM, float)
    bot = np.array([236, 206, 170], float)
    ramp = np.linspace(0, 1, H)[:, None]
    grad = top[None] * (1 - ramp) + bot[None] * ramp
    bg = np.repeat(grad[:, None, :], W, axis=1)
    yy, xx = np.mgrid[0:H, 0:W]
    r = np.sqrt((xx - W * .5) ** 2 + (yy - H * .42) ** 2) / (W * .6)
    glow = np.clip(1 - r, 0, 1)[:, :, None] ** 2
    return np.clip(bg + glow * (np.array(WARM_WHITE, float) - bg) * .35, 0, 255)


# ————————————————— 单帧 —————————————————
def render_frame(t, shots, beats, downbeats, bg0, fields):
    shot = active_shot(shots, t)
    bp = pulse(t, beats, 0.14)
    dbp = pulse(t, downbeats, 0.22)
    lt = t - shot.t0
    px_par = math.sin(t * 0.5) * 30  # 背景视差

    frame = scene_backdrop(t, bg0, px_par)
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

    if shot.t0 >= 1.0 or shot.cam != "static":
        place_doll(canvas, shot, t, beats, downbeats, [7.92, 8.39, 8.86, 9.32])

    front = np.zeros((H, W, 3))
    if "streak_left" in shot.fx:
        front = screen(front, streaks(t, "left", 0.85))
    if "petal" in shot.fx:
        front = screen(front, fields["petal"].render(t, 1 + dbp))
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

    arr = np.array(canvas.convert("RGB"), float)

    # —— 转场（入场 0.16s）——
    if lt < 0.16:
        k = 1 - lt / 0.16
        if shot.trans == "flash":
            arr = screen(arr, np.ones((H, W, 3)) * np.array(WARM_WHITE, float) * k * 0.75)
        elif shot.trans in ("swipe_l", "swipe_r"):
            d = "left" if shot.trans == "swipe_l" else "right"
            arr = screen(arr, streaks(t, d, k * 1.4))
        elif shot.trans == "zoomblur":
            z = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).resize(
                (int(W * (1 + k * 0.12)), int(H * (1 + k * 0.12))))
            z = z.crop(((z.width - W) // 2, (z.height - H) // 2,
                        (z.width - W) // 2 + W, (z.height - H) // 2 + H))
            arr = arr * (1 - k * 0.6) + np.array(z, float) * (k * 0.6)

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
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


def main():
    global RAYS, FLARE, MOON, RIDGES
    start = float(sys.argv[1]) if len(sys.argv) > 1 else 0.0
    end = float(sys.argv[2]) if len(sys.argv) > 2 else 10.73
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    FRAME_DIR.mkdir(parents=True, exist_ok=True)
    for f in FRAME_DIR.glob("*.png"):
        f.unlink()

    tempo, beats = load_beats()
    downbeats = beats[::2]
    RAYS = make_rays(1200)
    FLARE = make_flare(720)
    MOON = make_moon(560)
    RIDGES = make_ridges()
    bg0 = make_bg()
    fields = {"spark": Field(56, "spark", 7, 1.0),
              "far": Field(30, "spark", 21, 1.8),
              "petal": Field(40, "petal", 11, 1.0)}
    shots = build_shots()
    print(f"[info] {tempo:.0f}BPM · {len(shots)}镜 · {start}-{end}s")

    n = int((end - start) * FPS)
    for i in range(n):
        t = start + i / FPS
        render_frame(t, shots, beats, downbeats, bg0, fields).save(FRAME_DIR / f"f{i:05d}.png")
        if i % 30 == 0:
            print(f"[frame] {i}/{n} t={t:.2f}")

    out = OUT_DIR / f"pv_{start:.0f}_{end:.0f}s_v3.mp4"
    cmd = [FFMPEG, "-y", "-framerate", str(FPS), "-i", str(FRAME_DIR / "f%05d.png"),
           "-ss", str(start), "-t", str(end - start), "-i", str(WAV),
           "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-pix_fmt", "yuv420p",
           "-crf", "18", "-c:a", "aac", "-b:a", "192k", "-shortest", str(out)]
    print("[ffmpeg] 合成+混音…")
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        print(r.stderr[-800:])
        return 1
    print(f"[ok] {out} ({out.stat().st_size // 1024}KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
