#!/usr/bin/env python3
"""《明月天涯》原子件 —— 现在是 `mv_engine.atoms` 的薄壳。

原本 10 个原子的实现都在本文件里。它们与内容无关(不带默认色、不认素材名),
所以整体搬进了跨片累积的 `pipeline/mv_engine/atoms/`,函数体逐字未改
(`mv_engine/atoms/lock.json` 锁着 15 个 case 的 sha256)。

本文件留着只为不改调用方:`mingyue_render.py` 的 `import mingyue_atoms as atoms`
和 `pipeline/paperdoll/probes.py::_selftest` 的 `import mingyue_atoms as A` 照旧。
新代码直接 `from mv_engine.atoms import ...`,别再走这层。

契约(不变,现在写在 `mv_engine/atoms/_contract.py`):所有 `arr` 参数都是
float ndarray (H, W, 3),值域 0-255,函数不就地修改;颜色一律由调用方按该片
design_language §1 传入。
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mv_engine.atoms import (  # noqa: E402
    _compress,
    banding,
    crease,
    fold_press,
    jam_smear,
    lid_flare,
    paper_fold,
    scan_bar,
    solve_perspective,
    stack_edge,
)

RGB = tuple[int, int, int]

__all__ = [
    "RGB",
    "_compress",
    "banding",
    "crease",
    "fold_press",
    "jam_smear",
    "lid_flare",
    "paper_fold",
    "scan_bar",
    "solve_perspective",
    "stack_edge",
]
