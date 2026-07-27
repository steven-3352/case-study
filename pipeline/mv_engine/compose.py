"""平面合成 —— 把已经拿到手的一张 RGBA 贴到取景框某个 quad 上。

**只做**:透视变换 + 包围盒裁切。**不做**:去哪儿取图、上色、扫描仪光条切分。
调用方拿到图之后才决定要不要 `desat`、要不要 `scan_split`,那些是内容的事。

`warp` 只在图层的包围盒里做变换 —— 整张 3840×1836 的画布做透视太贵,
本片实测一帧最多 8 个 item,每个 warp 平均 30ms。
"""
from __future__ import annotations

import math

from PIL import Image

from .atoms import solve_perspective


def warp(lay: Image.Image, quad: list, bound: tuple) -> tuple | None:
    """把图层贴到 quad 上,只在它的包围盒里做变换(整张画布做太贵)。"""
    xs, ys = [p[0] for p in quad], [p[1] for p in quad]
    x0, y0 = max(0, int(math.floor(min(xs)))), max(0, int(math.floor(min(ys))))
    x1, y1 = min(bound[0], int(math.ceil(max(xs)))), min(bound[1], int(math.ceil(max(ys))))
    if x1 - x0 < 1 or y1 - y0 < 1:
        return None
    lw, lh = lay.size
    coeffs = solve_perspective(
        [(p[0] - x0, p[1] - y0) for p in quad],
        [(0, 0), (lw, 0), (lw, lh), (0, lh)])
    im = lay.transform((x1 - x0, y1 - y0), Image.Transform.PERSPECTIVE, coeffs, Image.BICUBIC)
    return im, (x0, y0)
