"""光学 / 传感器瑕疵 —— 只改 RGB,不动 alpha。

所有 `arr` 都是 float ndarray (H, W, 3),值域 0-255,函数不就地修改。"""
from __future__ import annotations

import numpy as np
from PIL import Image, ImageFilter
from ._contract import atom

RGB = tuple[int, int, int]


@atom(touches_alpha=False)
def scan_bar(arr: np.ndarray, y_frac: float, width_px: int, glow_radius_px: int,
             glow_color: RGB, glow_alpha: float, direction: str = "down",
             scanned_brightness_add: float = 0.0) -> np.ndarray:
    """一道硬边高亮光条 + 前沿辉光,扫过的区域留下亮度差.

    design_language.md §3.1 规定光条边缘梯度 ≥0.9 L/px、软过渡 >120px 判 FAIL,
    所以光条本体是**硬边**(直接赋值,不做羽化),只有前沿辉光是衰减带。

    y_frac 0.0=顶 1.0=底。direction 决定"已扫描"是哪一侧,以及辉光往哪边拖。
    """
    h, w = arr.shape[:2]
    out = arr.copy()
    axis_len = h if direction in ("down", "up") else w
    pos = int(np.clip(y_frac, 0.0, 1.0) * axis_len)
    glow = np.asarray(glow_color, dtype=float)

    def band(lo: int, hi: int) -> tuple:
        lo, hi = max(0, lo), min(axis_len, hi)
        return (slice(lo, hi), slice(None)) if direction in ("down", "up") \
            else (slice(None), slice(lo, hi))

    if scanned_brightness_add:
        scanned = (0, pos) if direction in ("down", "right") else (pos, axis_len)
        sl = band(*scanned)
        out[sl] = np.clip(out[sl] + scanned_brightness_add * 255.0, 0, 255)

    # 前沿辉光:沿行进方向拖一条高斯衰减带(光条已经走过的地方不拖,那是"已扫描")
    sign = 1 if direction in ("down", "right") else -1
    sigma = max(1.0, glow_radius_px * 0.4)
    for d in range(1, glow_radius_px + 1):
        decay = float(np.exp(-(d ** 2) / (2 * sigma ** 2))) * glow_alpha
        if decay < 0.004:
            break
        p = pos + sign * d
        if 0 <= p < axis_len:
            sl = band(p, p + 1)
            out[sl] = np.clip(out[sl] + glow * decay, 0, 255)

    sl = band(pos - width_px // 2, pos - width_px // 2 + max(1, width_px))
    out[sl] = np.clip(np.maximum(out[sl], glow), 0, 255)
    return out

@atom(touches_alpha=False)
def banding(arr: np.ndarray, t: float, frequency: float, amplitude: float,
            scroll_speed: float = 0.0, phase_offset: float = 0.0) -> np.ndarray:
    """CCD 行噪:周期性横向暗条带,可垂直滚动.

    frequency = 全画高内的条带周期数。amplitude 0=不可见 1=纯黑条。
    scroll_speed 单位 px/s。
    """
    h = arr.shape[0]
    yy = np.arange(h, dtype=float)
    phase = phase_offset + t * scroll_speed / h * (2 * np.pi)
    mask = 0.5 - 0.5 * np.cos(yy / h * frequency * 2 * np.pi + phase)
    return np.clip(arr * (1.0 - amplitude * mask)[:, None, None], 0, 255)

@atom(touches_alpha=False)
def lid_flare(arr: np.ndarray, intensity: float, gradient_falloff: float,
              color: RGB, bloom_radius_px: int = 0) -> np.ndarray:
    """掀盖漏光:从顶部灌入的日光,screen 合成,上强下弱.

    intensity 0=无 1=顶部全白冲淡。gradient_falloff 越大衰减越快(1.5 缓 / 4.0 仅上沿)。
    """
    if intensity <= 0:
        return arr
    h = arr.shape[0]
    ramp = ((1.0 - np.linspace(0.0, 1.0, h)) ** gradient_falloff)[:, None, None] * intensity
    light = np.asarray(color, dtype=float) * ramp
    out = 255.0 - (255.0 - arr) * (255.0 - light) / 255.0
    if bloom_radius_px > 0:
        im = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))
        blur = np.asarray(im.filter(ImageFilter.GaussianBlur(bloom_radius_px)), dtype=float)
        out = 255.0 - (255.0 - out) * (255.0 - blur * 0.3) / 255.0
    return np.clip(out, 0, 255)
