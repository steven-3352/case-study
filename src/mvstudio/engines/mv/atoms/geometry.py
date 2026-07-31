"""几何解算 —— 不碰像素,只解变换系数。"""
from __future__ import annotations

import numpy as np
from ._contract import atom

RGB = tuple[int, int, int]


@atom(touches_alpha=False)
def solve_perspective(out_quad: list, in_quad: list) -> list:
    """解 PIL `Image.Transform.PERSPECTIVE` 的 8 系数.

    PIL 用的是**反向映射**:输出像素 (x,y) 去输入图的
    ((ax+by+c)/(gx+hy+1), (dx+ey+f)/(gx+hy+1)) 取色。
    所以这里的参数顺序是 (输出四点, 输入四点),不是通常的 (src, dst)——
    传反了图像会以奇怪的方式外扩,而不会报错。

    四点顺序需一致(如均为 左上→右上→右下→左下)。
    """
    a, b = [], []
    for (ox, oy), (ix, iy) in zip(out_quad, in_quad):
        a.append([ox, oy, 1, 0, 0, 0, -ix * ox, -ix * oy])
        a.append([0, 0, 0, ox, oy, 1, -iy * ox, -iy * oy])
        b += [ix, iy]
    coeffs = np.linalg.solve(np.asarray(a, dtype=float), np.asarray(b, dtype=float))
    return coeffs.tolist()
