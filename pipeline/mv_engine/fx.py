"""屏幕层 FX 通用工具 —— 与内容无关的部分。

**放这里的**:纯数学的运动/亮度算子(`_hblur`)、pair 插值(`_lerp`)。
**不放这里的**:调用哪些原子件、按什么曲线插值、往哪儿加哪种色 —— 那些是每片
`design_language.md §3` 声明的,写在片内 `fx_pass` 里。

`_hblur` 是横向盒糊(甩镜运动模糊):高斯核会把竖边也糊掉,甩镜只糊一个轴。
"""
from __future__ import annotations

import numpy as np


def _hblur(arr: np.ndarray, px: int) -> np.ndarray:
    """横向盒糊 —— 甩镜的运动模糊。高斯会把竖边也糊掉,甩镜只糊一个轴。"""
    if px < 2:
        return arr
    pad = np.pad(arr, ((0, 0), (px, px), (0, 0)), mode="edge")
    c = np.cumsum(np.pad(pad, ((0, 0), (1, 0), (0, 0))), axis=1)
    n = 2 * px + 1
    return (c[:, n:, :] - c[:, :-n, :]) / n


def _lerp(pair, e: float) -> float:
    return pair[0] + (pair[1] - pair[0]) * e
