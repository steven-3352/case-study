"""软目标 —— 硬约束过后的排序依据。

**遵 `gate-floor-not-target`(门是地板不是目标)**:硬约束已经保证冻结门过、
多样性够、相邻不撞;这里做的是"合法解里更好的那些"。

主项是 **move family 多重集的 Shannon 熵** —— 熵越高越多样。次项是相邻景别
对比度(有大小差才有节奏)、bigram 重复惩罚(4 镜窗口内 (move,trans)
二元组不重复)。所有分量都做**饱和上限**,不给求解器"堆一个维度换分"的空间
—— 熵到 log2(min(6, n)) 就封顶,对比度差 8× 也封顶。
"""
from __future__ import annotations

import math
from collections import Counter
from typing import Sequence


def _shannon_entropy(counts: dict) -> float:
    n = sum(counts.values())
    if n <= 1:
        return 0.0
    return -sum((c / n) * math.log2(c / n) for c in counts.values() if c > 0)


def obj_move_entropy(shots: Sequence[dict]) -> float:
    """move family 多重集熵 → [0, log2(min(6, n))]。"""
    if len(shots) <= 1:
        return 0.0
    c = Counter(s["family"] for s in shots)
    return min(_shannon_entropy(c), math.log2(min(6, len(shots))))


def obj_trans_entropy(shots: Sequence[dict]) -> float:
    if len(shots) <= 1:
        return 0.0
    c = Counter(s.get("trans", "cut") for s in shots)
    return min(_shannon_entropy(c), math.log2(min(5, len(shots))))


def obj_size_contrast(shots: Sequence[dict], framing_table: dict) -> float:
    """相邻镜景别对比度求和(饱和上限 3.0 = 8×)。"""
    if len(shots) < 2:
        return 0.0
    total = 0.0
    for i in range(1, len(shots)):
        a = framing_table.get(shots[i - 1].get("size0", "中景"), 0.3)
        b = framing_table.get(shots[i].get("size0", "中景"), 0.3)
        ratio = max(a, b) / max(1e-6, min(a, b))
        total += min(math.log2(ratio), 3.0)
    return total / max(1, len(shots) - 1)


def obj_bigram_penalty(shots: Sequence[dict], window: int = 4) -> float:
    """4 镜窗口内 (move, trans) 二元组重复惩罚 —— 返回**惩罚**(越大越差)。"""
    if len(shots) < window:
        return 0.0
    pen = 0.0
    for i in range(len(shots) - window + 1):
        pairs = [(s["family"], s.get("trans", "cut")) for s in shots[i:i + window]]
        c = Counter(pairs)
        pen += sum((v - 1) for v in c.values() if v > 1)
    return pen


def score(shots: Sequence[dict], framing_table: dict) -> tuple[float, dict]:
    """→ (总分, 分项 dict)。总分越大越好。"""
    parts = {
        "move_H":       obj_move_entropy(shots)   * 1.0,
        "trans_H":      obj_trans_entropy(shots)  * 0.6,
        "size_contrast": obj_size_contrast(shots, framing_table) * 0.4,
        "bigram_penalty": -obj_bigram_penalty(shots) * 0.3,
    }
    return sum(parts.values()), parts
