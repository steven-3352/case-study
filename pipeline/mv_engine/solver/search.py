"""Beam search —— 从左到右扫每一镜,每步保留最好的 `width` 个前缀。

**为什么是 beam 不是 DP**:H3/H4 是**全局基数约束**(某个 family 占比 ≤ 50% ·
需要 ≥ 6 种 family),纯 DP 只能看局部,基数看不见。Beam 状态里带
`family_count / trans_count` 就能让基数出现在剪枝里。宽度默认 16 是权衡:
21 镜 × ~30 候选 × 16 束 ≈ 一万次评估,秒级跑完。

**候选生成**:枚举 (move template, size0, size1, trans),连续旋钮暂只留
[low, mid, high] 3 档 —— 见 plan §Phase 2。
"""
from __future__ import annotations

import heapq
from dataclasses import dataclass, field
from typing import Callable, Sequence

from .templates import MOVE_TEMPLATES, TRANS_TEMPLATES
from .objective import score


@dataclass(order=True)
class Beam:
    neg_score: float                       # 用负分做小顶堆的最大堆
    shots: list = field(compare=False)     # 已选前缀
    fam_count: dict = field(compare=False, default_factory=dict)
    trans_count: dict = field(compare=False, default_factory=dict)


SIZES = ["极端全景", "全景", "中景", "近景", "特写", "大特写"]


def _candidates_for(shot_meta: dict) -> list[dict]:
    """为一镜枚举候选(move, size0, size1, trans, level)。

    `shot_meta` 里已声明的字段(pinned)覆盖枚举 —— H7 靠这个实现:
    yaml 里 size0/family/trans 任何一项非空就锁住那个维度。
    """
    pinned_family = shot_meta.get("family")
    pinned_size0  = shot_meta.get("size0")
    pinned_size1  = shot_meta.get("size1", pinned_size0)
    pinned_trans  = shot_meta.get("trans")

    moves = ([m for m in MOVE_TEMPLATES if MOVE_TEMPLATES[m].name == pinned_family]
             if pinned_family else list(MOVE_TEMPLATES))
    sizes = [pinned_size0] if pinned_size0 else SIZES
    trans = [pinned_trans] if pinned_trans else list(TRANS_TEMPLATES)

    out = []
    for m_name in moves:
        m = MOVE_TEMPLATES[m_name]
        for s0 in sizes:
            s1 = pinned_size1 if pinned_size1 else s0   # 大多数镜 size1==size0
            for tr in trans:
                for level in ("mid",):    # 只用中档,压缩候选空间
                    kw = m.apply(s0, s1, {"level": level})
                    out.append({
                        "sid": shot_meta["sid"],
                        "move": m_name,
                        "family": m.name,
                        "size0": s0,
                        "size1": s1,
                        "trans": tr,
                        "cam_kwargs": kw,
                    })
    return out


def beam_search(
    shot_metas: Sequence[dict],
    framing_table: dict,
    width: int = 16,
    hard_check: Callable[[list], tuple[bool, list]] | None = None,
) -> list[list[dict]]:
    """→ 每个 beam 的最终 shot 序列列表(按分数降序)。

    `hard_check(prefix) -> (ok, msgs)` 用来在扩展时剪枝(H2/H3/H4/H6 之类)。
    """
    beams: list[Beam] = [Beam(0.0, [])]
    for meta in shot_metas:
        cands = _candidates_for(meta)
        next_pool: list[Beam] = []
        for b in beams:
            for c in cands:
                nb_shots = b.shots + [c]
                if hard_check is not None:
                    ok, _ = hard_check(nb_shots)
                    # 前缀阶段允许 H4(全局多样性)未满足;末端才严判
                    if not ok and len(nb_shots) == len(shot_metas):
                        continue
                sc, _ = score(nb_shots, framing_table)
                heapq.heappush(next_pool,
                               Beam(-sc, nb_shots,
                                    _bump(b.fam_count, c["family"]),
                                    _bump(b.trans_count, c.get("trans", "cut"))))
        # 保留 top-width
        beams = heapq.nsmallest(width, next_pool) if next_pool else beams
    beams.sort()
    return [b.shots for b in beams]


def _bump(counter: dict, k: str) -> dict:
    c = dict(counter)
    c[k] = c.get(k, 0) + 1
    return c
