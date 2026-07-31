"""跨片累积的原子库。

**这里只放与内容无关的东西。** 判据见 `_contract.py`:函数体不得引用任何
模块级内容常量(色板 / 字体 / 素材名)。颜色一律由调用方传入。

来源与去向:第一批 10 个原子从《明月天涯》的 `mingyue_atoms.py` 整体搬入
(函数体逐字未改)。`paperdoll_engine.py` 里还有约 25 个够格的,后续按片增补
—— 每做一部片,把那部片里通用的部分留在这里。

分层:

    ease      纯标量曲线,不碰图像
    geometry  变换解算,不碰像素
    optical   光学 / 传感器瑕疵(只改 RGB)
    motion    运动 / 拖影瑕疵(只改 RGB)
    paper     纸的物理(改 alpha)

每个原子都带 `touches_alpha` 声明,见 `_contract.REGISTRY`。
回归锁见 `lock.py`,质量地板见 `pipeline/paperdoll/probes.py` —— 两者不同:
前者管「搬家后行为没变」,后者管「效果够不够强」。
"""
from __future__ import annotations

from ._contract import REGISTRY, AtomSpec, alpha_touching, atom
from .ease import _compress, fold_press
from .geometry import solve_perspective
from .motion import jam_smear
from .optical import banding, lid_flare, scan_bar
from .paper import crease, paper_fold, stack_edge

__all__ = [
    "REGISTRY", "AtomSpec", "alpha_touching", "atom",
    "_compress", "fold_press",
    "solve_perspective",
    "jam_smear",
    "banding", "lid_flare", "scan_bar",
    "crease", "paper_fold", "stack_edge",
]
