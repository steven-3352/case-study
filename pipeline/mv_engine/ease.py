"""缓动 —— 纯函数,不碰画面。

`ease_out_back` 单独走一支:它的回弹越过 1 是要的(位移多滑一点、转多转几度,
然后荡回来),不能被 `_clamp` 提前压回来。缩放专用的进度另在 `Cam.scale_progress`
里再 clamp 一次(比值插值越界会把主体缩成一个点)。
"""
from __future__ import annotations

import math


def _clamp(x: float, a: float = 0.0, b: float = 1.0) -> float:
    return max(a, min(b, x))


def _out_back(x: float, amount: float) -> float:
    c1 = 1.70158 * (amount / 0.10) if amount else 1.70158
    return 1 + (c1 + 1) * (x - 1) ** 3 + c1 * (x - 1) ** 2


EASES = {
    "linear": lambda x: x,
    "ease_out_quad": lambda x: 1 - (1 - x) ** 2,
    "ease_out_cubic": lambda x: 1 - (1 - x) ** 3,
    "ease_out_quart": lambda x: 1 - (1 - x) ** 4,
    "ease_out_expo": lambda x: 1.0 if x >= 1 else 1 - 2 ** (-10 * x),
    "ease_in_sine": lambda x: 1 - math.cos(x * math.pi / 2),
    "ease_out_sine": lambda x: math.sin(x * math.pi / 2),
    "ease_in_out_quad": lambda x: 2 * x * x if x < .5 else 1 - (-2 * x + 2) ** 2 / 2,
    "ease_in_out_cubic": lambda x: 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2,
    "ease_in_out_sine": lambda x: -(math.cos(math.pi * x) - 1) / 2,
    "ease_in_out_expo": lambda x: (
        0.0 if x <= 0 else 1.0 if x >= 1 else
        2 ** (20 * x - 10) / 2 if x < .5 else (2 - 2 ** (-20 * x + 10)) / 2),
}


def ease(name: str, x: float, back: float = 0.0) -> float:
    x = _clamp(x)
    if name == "ease_out_back":
        return _out_back(x, back)
    return EASES[name](x)
