"""硬约束 H1-H7 —— 求解器"合法/不合法"的判据。

**为什么把冻结门做成硬约束不做成目标**:观众看到 2s 完全冻结的窗口会立刻出戏,
这是分级门(R9)而不是分级损失。放进硬约束的意思是"不过就淘汰",
不给求解器"我扣一点分换别的地方补回来"的空间。

**H1 的门是"报告字符串完全一致"不只是 ok 位**:`gate_check_motion.check_track`
的 report 里带冻结窗区间、最死窗口、硬切数,只比 ok 会放过「同样 FAIL 但冻在别处」
这种失真(Phase 0 实施笔记里已经踩过)。所以这里也用相同判据 —— 但求解阶段
我们要的是"不 FAIL",不必比 report 到字节。
"""
from __future__ import annotations

from collections import Counter
from typing import Sequence


# H1: freeze gate on predicted track (调用方注入 gate_check 函数,避免耦合)
FREEZE_MAX_S = 2.0  # 冻结窗口上限,与 gate_check_motion 里的常量对齐


def h1_freeze_gate(check_track_fn, motion_path) -> tuple[bool, str]:
    """H1 · 每镜内不出现 2s 冻结窗(在**预测轨迹**上判)。

    这个函数只是薄壳:真正的判定逻辑在 `pipeline/gate_check_motion.check_track`,
    求解器复用它保证与验收判据一致。返回 (ok, 一句人话)。
    """
    ok, report = check_track_fn(motion_path)
    if ok:
        return True, "H1 ok"
    # 报告首行常是「✗ 冻结窗 …」——只留第一行做候选选择时的调试提示
    first_line = report.strip().splitlines()[0] if report else "(无 report)"
    return False, f"H1 fail: {first_line}"


# H2: 相邻镜不共享 (move family, size0)
def h2_adjacent(shots: Sequence[dict]) -> tuple[bool, str]:
    for i in range(1, len(shots)):
        a, b = shots[i - 1], shots[i]
        if a.get("family") == b.get("family") and a.get("size0") == b.get("size0"):
            return False, f"H2 fail: {a['sid']}→{b['sid']} 共 ({a['family']},{a['size0']})"
    return True, "H2 ok"


# H3: 任一 move family 或 trans 占比 ≤ 50%
def h3_cap(shots: Sequence[dict], cap: float = 0.50) -> tuple[bool, str]:
    n = len(shots)
    if n == 0:
        return True, "H3 ok (空)"
    fam_c = Counter(s["family"] for s in shots)
    tr_c  = Counter(s.get("trans", "cut") for s in shots if s.get("trans"))
    for name, c in fam_c.items():
        if c / n > cap:
            return False, f"H3 fail: move `{name}` {c}/{n} > {cap*100:.0f}%"
    for name, c in tr_c.items():
        n_tr = sum(tr_c.values())
        if n_tr and c / n_tr > cap:
            return False, f"H3 fail: trans `{name}` {c}/{n_tr} > {cap*100:.0f}%"
    return True, "H3 ok"


# H4: 家族多样性下限
def h4_diversity(shots: Sequence[dict], min_moves: int = 6, min_trans: int = 5) -> tuple[bool, str]:
    fams  = {s["family"] for s in shots}
    trans = {s.get("trans", "cut") for s in shots if s.get("trans")}
    if len(fams) < min_moves:
        return False, f"H4 fail: 只用了 {len(fams)} 种 move family (需 ≥ {min_moves})"
    if len(trans) < min_trans:
        return False, f"H4 fail: 只用了 {len(trans)} 种 trans (需 ≥ {min_trans})"
    return True, f"H4 ok ({len(fams)} moves, {len(trans)} trans)"


# H6: 硬切两侧 elev 不得变号(除非转场是 flip / flash_white)
def h6_elev_sign(shots: Sequence[dict]) -> tuple[bool, str]:
    """硬切(trans=cut)两侧 elev 起止不得变号 —— 让观众能读出「哪边是天哪边是地」。"""
    exempt = {"flip", "flash_white"}
    for i in range(1, len(shots)):
        a, b = shots[i - 1], shots[i]
        tr = b.get("trans", "cut")
        if tr in exempt or tr != "cut":
            continue
        e0a = a.get("cam_kwargs", {}).get("e1", a.get("cam_kwargs", {}).get("e0", 90.0))
        e0b = b.get("cam_kwargs", {}).get("e0", 90.0)
        if e0a * e0b < 0:
            return False, f"H6 fail: {a['sid']}→{b['sid']} elev 变号 {e0a}→{e0b} (cut 场景)"
    return True, "H6 ok"


def check_all(shots: Sequence[dict], skip: Sequence[str] = ()) -> tuple[bool, list[str]]:
    """全套硬约束检查。返回 (是否全过, 每条判据的一句话)。

    H1 需要 track/motion 生成,不在此函数里跑;由 solver 主循环单独触发。
    """
    checks = []
    if "H2" not in skip: checks.append(h2_adjacent(shots))
    if "H3" not in skip: checks.append(h3_cap(shots))
    if "H4" not in skip: checks.append(h4_diversity(shots))
    if "H6" not in skip: checks.append(h6_elev_sign(shots))
    lines = [msg for _, msg in checks]
    ok = all(o for o, _ in checks)
    return ok, lines
