"""引擎级帧渲染入口 —— 给定 shot 列表和时间戳,返回一帧图像和 bbox。

**不放这里的**:调色板常量、素材路径、FX 的具体参数解析(scan 颜色 / flare 颜色)——
那些是每片 `voice_room/<film>/` 的事。这里只做:
- 找当前 shot → 解相机状态
- 铺背景 → 逐 item place → tilt
- 把 arr 交给片级 `fx_pass` → draw_lyrics → return (im, bb)

`fx_pass` 和 `draw_lyrics` 由调用方注入(None 表示跳过),保持引擎与内容解耦。
Phase 1a 里 `mingyue_render.py` 直接传自己的 `fx_pass` / `draw_lyrics`。
"""
from __future__ import annotations

from typing import Callable

import numpy as np
from PIL import Image

from .camera import View, tilt
from .config import PAD_H, PAD_W
from .shot import MShot, active, shot_scales


def render_frame(
    t: float,
    shots: list,
    version: str,
    bg_color: tuple[int, int, int],
    tiled_fn: Callable,
    place_fn: Callable,
    fx_pass_fn: Callable | None,
    draw_lyrics_fn: Callable | None,
) -> tuple[Image.Image, tuple | None]:
    sh = active(shots, t)
    k = sh.k(t)
    s0, s1, look = shot_scales(sh)
    s = s0 * (s1 / s0) ** sh.cam.scale_progress(k)
    cx, cy, r, elev = sh.cam.at(k, s)
    v = View(cx + look[0], cy + look[1], s, r)

    scan_y = None
    if "scan" in sh.fx:
        from .ease import _lerp  # noqa: PLC0415 — 局部 import 避免顶层 dep
        y0, y1 = sh.fx["scan"][0], sh.fx["scan"][1]
        hold = sh.fx["scan"][4] if len(sh.fx["scan"]) > 4 else 1.0
        e = sh.cam.progress(k)
        scan_y = _lerp((y0, y1), min(e / hold, 1.0) if hold < 1 else e)

    canvas = Image.new("RGBA", (PAD_W, PAD_H), (*bg_color, 255))
    if sh.bg:
        base = Image.new("RGB", (PAD_W, PAD_H))
        tiled_fn(base, sh.bg[0], sh.bg[1], sh.bg[2], sh.bg[3], v)
        canvas.paste(base, (0, 0))
    mask = Image.new("L", (PAD_W, PAD_H), 0)

    items = sh.items(t, k)
    for i, it in enumerate(items):
        place_fn(canvas, it, v, mask if i in sh.subject else None, scan_y)

    frame = tilt(canvas.convert("RGB"), elev)
    bb = tilt(mask, elev).getbbox()

    arr = np.asarray(frame, dtype=float)
    if fx_pass_fn is not None:
        arr = fx_pass_fn(arr, sh, t, k)
    im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    if draw_lyrics_fn is not None:
        draw_lyrics_fn(im, t, version, scan_y)
    return im, bb
