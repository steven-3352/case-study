#!/usr/bin/env python3
"""语音厅 · 两人动效小样 v2（卡点硬切换角度 + 风摆微动，非交叉溶解）.

v1 教训：三张离散角度做**交叉溶解**模拟转身 → 两个不同轮廓半透明叠加 = 鬼影 = 假。
2D 立绘插值模拟旋转是物理死穴，无真实中间帧。v2 换确定性路线（用户拍板）：

核心 1 · 卡点硬切换（零鬼影）：
  姿态之间不溶解，**硬切**；切换那一帧用 闪白 + 推镜 punch + 金光斜扫 遮住切点，
  观众看到"唰地换了角度"，而非两图重叠。切点卡在真 downbeat（129BPM）。

核心 2 · 停驻不是死图（风摆微动）：
  wind_warp：逐行正弦水平位移，发梢/衣摆摆幅大、身体锚点摆幅小 → 头发衣服真在飘。
  纯几何位移，不碰像素颜色（R1 守住）。叠 呼吸起伏 + 轻摇。

核心 3 · 连续生命感：慢推拉镜 + 背景视差（背景比人物慢移）。

两人：诺兰(左) / 轩珩(右) 相向。切点姿态序列见 SEQ_L / SEQ_R。
6.0s @30fps=180帧，中段 downbeat 处叠一次背景 wipe 当场景切。

用法：.venv/bin/python pipeline/voice_room/gen_turn_demo.py
输出：publish/语音厅/pv_v4/turn_demo/turn_demo.mp4
"""
from __future__ import annotations

import math
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "pipeline" / "voice_room"))

import paperdoll_engine as E  # 复用 scene_backdrop / bloom / grain / ease 原语

W, H, FPS = 1920, 1080, 30
VOICE = ROOT / "publish" / "语音厅"
POSES = VOICE / "pv_v4" / "poses_cutout"
FRONTS = VOICE / "script_v2_assets"
OUT = VOICE / "pv_v4" / "turn_demo"
BG_A = VOICE / "pv_v4" / "bg_v4b.png"
BG_B = VOICE / "pv_v4" / "bg_v4c.png"
GOLD = (212, 175, 55)
DUR = 6.0


def ease_out(x: float) -> float:
    return 1 - (1 - x) ** 3


def back_out(x: float) -> float:
    c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2


def _clean_alpha(im: Image.Image) -> Image.Image:
    a = im.getchannel("A").point(
        lambda v: 0 if v < 28 else (255 if v > 96 else int((v - 28) / 68 * 255)))
    im.putalpha(a)
    return im.crop(im.getbbox())


# ————————————————— 角度立绘加载（R1：像素零改，只 crop/scale/flip/alpha）—————————————————
_CACHE: dict = {}


def _load(path: Path, flip: bool, target_h: int) -> Image.Image:
    key = (str(path), flip, target_h)
    if key not in _CACHE:
        im = _clean_alpha(Image.open(path).convert("RGBA"))
        if flip:
            im = im.transpose(Image.FLIP_LEFT_RIGHT)
        s = target_h / im.height
        _CACHE[key] = im.resize((max(1, round(im.width * s)), target_h), Image.LANCZOS)
    return _CACHE[key]


def angles(name: str, flip: bool, target_h: int) -> dict:
    """返回 {"front","tq","side"} 三张同高立绘。flip=True 整组水平翻转（相向）。
    姿态之间**不做插值溶解**（v1 假的根因），只在卡点硬切其中一张。"""
    fronts = {"cy": "cy", "诺兰": "诺兰", "轩珩": "轩珩", "中里毅2": "中里毅2"}
    return {
        "front": _load(FRONTS / f"{fronts[name]}_cutout.png", flip, target_h),
        "tq":    _load(POSES / f"{name}_three_quarter_cutout.png", flip, target_h),
        "side":  _load(POSES / f"{name}_side_cutout.png", flip, target_h),
    }


def hem_sway(layer: Image.Image, t: float, seed: float,
             amp: float = 11.0, freq: float = 1.15, waist: float = 0.56) -> Image.Image:
    """裙摆/下摆飘动：逐行水平正弦位移，**只作用腰线以下**，腰以上(脸/躯干)一律锁死。
    v1 教训：per-row 位移分不清发/脸(同高) → 脸被剪切=melt。故只动下摆，脸绝不碰。
    纯几何位移，不改像素颜色（R1）。返回同尺寸 RGBA。"""
    arr = np.array(layer)                       # (h,w,4)
    h, w = arr.shape[:2]
    yn = np.arange(h) / max(1, h - 1)
    # 腰线以上=0（刚体），以下从 0 平滑爬到 1（脚踝/裙角摆幅最大）
    below = np.clip((yn - waist) / (1.0 - waist), 0, 1)
    envelope = below * below * (3 - 2 * below)  # smoothstep
    phase = below * math.pi * 1.8
    shift = amp * envelope * np.sin(t * freq * 2 * math.pi + phase + seed)
    xs = np.arange(w)
    src = xs[None, :] - shift[:, None]
    x0 = np.floor(src).astype(int)
    fr = (src - x0)[:, :, None]
    rows = np.arange(h)[:, None]
    x0c = np.clip(x0, 0, w - 1)
    x1c = np.clip(x0 + 1, 0, w - 1)
    out = arr[rows, x0c].astype(float) * (1 - fr) + arr[rows, x1c].astype(float) * fr
    out[..., 3][(src < 0) | (src > w - 1)] = 0.0
    return Image.fromarray(out.clip(0, 255).astype("uint8"))


def body_rotate(layer: Image.Image, deg: float) -> Image.Image:
    """整体刚体微旋（绕底脚中心）→ 上半身"活"感，且脸不变形（无 shear）。"""
    if abs(deg) < 0.05:
        return layer
    w, h = layer.size
    # 绕底脚中心旋转：扩画布防裁切，再按底脚重对齐由 place 处理
    return layer.rotate(deg, resample=Image.BICUBIC, center=(w / 2, h),
                        expand=False)


def pose_at(marks: list, t: float, order: list) -> tuple:
    """按 downbeat marks 决定当前姿态 key + 距上一切点的时长 lt（供 punch/flash 用）。
    order 是姿态 key 序列，随切点推进循环取用。"""
    idx = sum(1 for m in marks if t >= m)       # 已过几个切点
    key = order[idx % len(order)]
    last = marks[idx - 1] if idx > 0 else 0.0
    return key, t - last, idx


# ————————————————— 合成：落地影 / 投影 / 重拍 rim —————————————————
def ground_shadow(canvas: Image.Image, cx: int, foot_y: int, w: int) -> None:
    ov = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    rw, rh = int(w * 0.62), int(w * 0.10)
    d.ellipse([cx - rw, foot_y - rh, cx + rw, foot_y + rh], fill=(20, 12, 8, 120))
    canvas.alpha_composite(ov.filter(ImageFilter.GaussianBlur(18)))


def place(canvas: Image.Image, layer: Image.Image, cx: int, foot_y: int,
          fade: float = 1.0, rim: float = 0.0, scale: float = 1.0) -> None:
    """底脚锁定放置：投影 + 立绘 + 可选重拍暖白 rim 光。scale=切点 punch 缩放。"""
    if abs(scale - 1.0) > 0.002:
        layer = layer.resize((max(1, int(layer.width * scale)),
                              max(1, int(layer.height * scale))), Image.LANCZOS)
    x0 = int(cx - layer.width / 2)
    y0 = int(foot_y - layer.height)
    # 软投影
    sh = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    tint = layer.copy()
    tint.putalpha(tint.getchannel("A").point(lambda v: int(v * 0.42 * fade)))
    blk = Image.new("RGBA", layer.size, (12, 8, 6, 255))
    blk.putalpha(tint.getchannel("A"))
    sh.alpha_composite(blk, (x0 + 14, y0 + 10))
    canvas.alpha_composite(sh.filter(ImageFilter.GaussianBlur(9)))
    # 主体
    body = layer
    if fade < 1.0:
        body = layer.copy()
        body.putalpha(body.getchannel("A").point(lambda v: int(v * fade)))
    canvas.alpha_composite(body, (x0, y0))
    # 重拍 rim：沿 alpha 边缘描暖白，screen 感
    if rim > 0.02:
        edge = layer.getchannel("A").filter(ImageFilter.MaxFilter(5))
        edge = Image.fromarray(
            (np.array(edge, float) - np.array(layer.getchannel("A"), float)).clip(0, 255).astype("uint8"))
        glow = Image.new("RGBA", layer.size, (255, 246, 230, 0))
        glow.putalpha(edge.point(lambda v: int(v * rim)))
        canvas.alpha_composite(glow.filter(ImageFilter.GaussianBlur(2)), (x0, y0))


def bg_at(path: Path, t: float) -> np.ndarray:
    """复用引擎 Ken-Burns 呼吸（scene_backdrop 走文件缓存）。"""
    return E.scene_backdrop(t, None, 0.0, plate_path=str(path))


def wipe(base: np.ndarray, nxt: np.ndarray, k: float) -> np.ndarray:
    """金缝斜扫 wipe：k 0→1 从右向左揭出 nxt，缝口一道暖金亮边。"""
    k = ease_out(max(0.0, min(1.0, k)))
    xx = np.arange(W)[None, :, None]
    seam = W * (1.0 - k)
    slope = (np.arange(H)[:, None, None] - H / 2) * 0.18   # 轻微斜切
    edge = seam + slope
    out = np.where(xx >= edge, nxt, base).astype(float)
    band = np.exp(-((xx - edge) / 26.0) ** 2)
    return np.clip(out + band * np.array(GOLD, float) * 0.9, 0, 255)


def light_sweep(canvas: Image.Image, cx: int, k: float) -> None:
    """切点金光斜扫：一道暖白光带横掠人物位置，遮住硬切瞬间。k 0→1。"""
    if k <= 0.01 or k >= 0.99:
        return
    band = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(band)
    sx = int(cx - W * 0.28 + k * W * 0.56)          # 从左掠到右
    for off, al in ((-46, 60), (0, 150), (46, 60)):
        d.line([(sx + off - 90, 0), (sx + off + 90, H)],
               fill=(255, 246, 230, al), width=30)
    env = math.sin(k * math.pi)                     # 中途最亮
    band = band.filter(ImageFilter.GaussianBlur(22))
    a = band.getchannel("A").point(lambda v: int(v * env))
    band.putalpha(a)
    canvas.alpha_composite(band)


def switch_flash(k: float) -> float:
    """切点闪白强度：k=距切点归一化时长(0=刚切)。前 0.18 一记暖白闪，快落。"""
    return max(0.0, 1.0 - k / 0.18) ** 2 * 0.5


# ————————————————— 分镜时间轴 —————————————————
TH = int(H * 0.86)              # 立绘目标高
FOOT = int(H * 0.99)           # 底脚锁定线
CX_L, CX_R = int(W * 0.33), int(W * 0.67)

DOWNBEATS = [1.358, 2.299, 3.228, 4.168, 5.108]   # 129BPM 实测拍点（切姿态处）
WIPE_AT = 3.228                 # 中段这一拍叠背景 wipe 当场景切
# 两人姿态序列（相向 → 内转 → 侧身 → 回望正面…），错开取用制造对话感
SEQ_L = ["front", "tq", "side", "tq", "front", "tq"]
SEQ_R = ["front", "tq", "front", "side", "tq", "front"]


def micro(seed: float, t: float) -> tuple:
    """停驻微动：返回 (bob_dy, sway_dx)。呼吸起伏 + 轻摇（与 wind_warp 叠加）。"""
    bob = 5.0 * math.sin(t * 1.5 + seed)
    sway = 5.0 * math.sin(t * 0.85 + seed + 0.7)
    return bob, sway


def punch(lt: float) -> float:
    """切点推镜 punch：刚切时放大一点，0.28s 内 ease_out 回落。"""
    if lt >= 0.28:
        return 1.0
    return 1.0 + (1.0 - ease_out(lt / 0.28)) * 0.07


def render() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    fdir = OUT / "_frames"
    fdir.mkdir(exist_ok=True)
    for f in fdir.glob("*.png"):
        f.unlink()

    poses_L = angles("诺兰", flip=True, target_h=TH)    # 左：翻转→朝右(向内)
    poses_R = angles("轩珩", flip=False, target_h=TH)   # 右：原朝左(向内)
    wipe_k_span = 0.5                                   # wipe 持续 0.5s

    n = int(DUR * FPS)
    print(f"[info] 动效小样 v2 · {n}帧 @ {FPS}fps · {DUR}s · 卡点硬切+风摆")
    for i in range(n):
        t = i / FPS
        # —— 背景（中段 downbeat 处一次 wipe 场景切）——
        w0, w1 = WIPE_AT, WIPE_AT + wipe_k_span
        if t < w0:
            base = bg_at(BG_A, t)
        elif t < w1:
            base = wipe(bg_at(BG_A, t), bg_at(BG_B, t), (t - w0) / wipe_k_span)
        else:
            base = bg_at(BG_B, t)
        # 背景视差：整体随时间极缓横移（比人物慢 → 纵深生命感）
        canvas = Image.fromarray(base.clip(0, 255).astype("uint8")).convert("RGBA")

        # —— 相机推拉：全片缓慢呼吸 + 每个切点一记 punch（作用于人物 scale）——
        entering = t < 0.55                            # 入场
        for poses, cx, seed, seq in ((poses_L, CX_L, 0.0, SEQ_L),
                                     (poses_R, CX_R, 1.7, SEQ_R)):
            key, lt, idx = pose_at(DOWNBEATS, t, seq)
            layer = poses[key]
            layer = hem_sway(layer, t, seed)           # 只动下摆（脸/躯干锁死）
            rot = 1.3 * math.sin(t * 0.8 + seed)       # 整体刚体微旋（脸不变形）
            layer = body_rotate(layer, rot)
            bob, sway = micro(seed, t)
            foot = FOOT + bob
            sc = punch(lt)
            if entering:                               # 入场 slam_up + fade
                e = back_out(min(1.0, t / 0.55))
                foot += (1 - e) * 480
                fade = ease_out(min(1.0, t / 0.45))
            else:
                fade = 1.0
            rim = switch_flash(lt) * 1.4               # 切点边缘暖光
            ground_shadow(canvas, int(cx + sway), int(foot), int(layer.width * sc))
            place(canvas, layer, int(cx + sway), int(foot),
                  fade=fade, rim=rim, scale=sc)
            # 切点金光斜扫（0.28s 内）遮住硬切
            if 0.0 < lt < 0.28 and not entering:
                light_sweep(canvas, int(cx + sway), lt / 0.28)

        # —— 全画面切点闪白（叠加，非常克制）——
        arr = np.array(canvas.convert("RGB"), float)
        flash = max(switch_flash(pose_at(DOWNBEATS, t, SEQ_L)[1]),
                    0.0) if not entering else 0.0
        if flash > 0.01:
            arr = E.screen(arr, np.full_like(arr, 255.0) * flash * 0.5)
        # —— 收尾：辉光 + 颗粒（复用引擎）——
        arr = E.bloom(arr, thr=210, strength=0.55)
        arr = E.grain(arr, t, amp=5.0)
        Image.fromarray(arr.clip(0, 255).astype("uint8")).save(fdir / f"f{i:05d}.png")
        if i % 30 == 0:
            print(f"[frame] {i}/{n} t={t:.2f}")

    out = OUT / "turn_demo.mp4"
    cmd = [E.FFMPEG, "-y", "-framerate", str(FPS),
           "-i", str(fdir / "f%05d.png"),
           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", str(out)]
    print("[ffmpeg] 编码小样…")
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        print(r.stderr[-800:])
        return 1
    print(f"[ok] {out} ({out.stat().st_size // 1024}KB)")
    return 0


if __name__ == "__main__":
    sys.exit(render())
