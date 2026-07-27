"""纯标量曲线 —— 输入进度,输出进度。不碰图像。"""
from __future__ import annotations

import numpy as np
from ._contract import atom

RGB = tuple[int, int, int]


@atom(touches_alpha=False)
def fold_press(k: float) -> float:
    """一折的三阶段进度曲线 —— 「折不动 / 回弹」.

    k 是这一折的归一化时间 0→1,返回 0→1 的压下量。
    A(0~30%) 用力压到 70% → B(30~50%) 鼓起回弹到 50% → C(50~100%) 压到底。
    纯 ease 曲线,不需要物理引擎,帧耗时不变(motion_tech_plan §1.3)。
    """
    k = float(np.clip(k, 0.0, 1.0))
    if k < 0.30:
        return 0.70 * (k / 0.30) ** 0.6
    if k < 0.50:
        return 0.70 - 0.20 * ((k - 0.30) / 0.20)
    e = (k - 0.50) / 0.50
    return 0.50 + 0.50 * (1 - (1 - e) ** 3)

@atom(touches_alpha=False, name="_compress")
def _compress(n: int) -> float:
    """第 n 折翻过去那半的厚度压缩比 —— 纸越折越厚,越压不平."""
    return 0.7 * (0.5 ** (n / 4.0))
