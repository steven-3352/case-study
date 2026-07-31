"""分镜求解器 —— 从"镜头边界固定 + 素材固定"求出运镜/景别/转场。

**接口**:

    from mv_engine.solver import solve
    solved_shots, report = solve(shot_metas)

`shot_metas` 是一个字典列表,每条至少有 `sid`;已填的 `family/size0/size1/trans`
被当作 pin 保留(H7)。返回 `solved_shots` 是同结构但填齐了空位。
"""
from __future__ import annotations

from typing import Sequence

from ..config import FRAMING

from .constraints import check_all
from .objective import score
from .search import beam_search


def solve(shot_metas: Sequence[dict], width: int = 16,
          hard_check_extra=None) -> tuple[list[dict], dict]:
    """→ (最优 shot 序列, report dict)。"""
    def hc(prefix):
        ok, msgs = check_all(prefix)
        if hard_check_extra:
            ok2, msgs2 = hard_check_extra(prefix)
            ok = ok and ok2
            msgs = msgs + msgs2
        return ok, msgs

    beams = beam_search(shot_metas, FRAMING, width=width, hard_check=hc)
    if not beams:
        return [], {"error": "no beam survived"}

    best = beams[0]
    sc, parts = score(best, FRAMING)
    return best, {
        "score": sc,
        "parts": parts,
        "beam_width": width,
        "candidates_considered": len(beams),
    }


__all__ = ["solve", "check_all", "score", "beam_search"]
