"""运动 / 拖影瑕疵 —— 只改 RGB,不动 alpha。"""
from __future__ import annotations

import numpy as np
from ._contract import atom

RGB = tuple[int, int, int]


@atom(touches_alpha=False)
def jam_smear(arr: np.ndarray, smear_amount_px: int, smear_start_frac: float,
              falloff: float, alpha: float, direction: str = "vertical") -> np.ndarray:
    """卡纸拖影:从某一行/列起,把那一行的像素沿扫描方向拖长.

    干净区到拖影区是**硬边界**(SOURCES.md 记的"扫描扫坏了"的视觉签名),
    所以 smear_start 之前一个像素都不动。
    """
    out = arr.copy()
    vertical = direction == "vertical"
    axis_len = arr.shape[0] if vertical else arr.shape[1]
    start = int(np.clip(smear_start_frac, 0.0, 1.0) * (axis_len - 1))
    src = arr[start] if vertical else arr[:, start]

    for d in range(1, smear_amount_px + 1):
        k = alpha * float(np.exp(-falloff * d / smear_amount_px))
        if k < 0.01:
            break
        p = start + d
        if p >= axis_len:
            break
        if vertical:
            out[p] = out[p] * (1 - k) + src * k
        else:
            out[:, p] = out[:, p] * (1 - k) + src * k
    return np.clip(out, 0, 255)
