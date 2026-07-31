"""运镜模板 M · 转场模板 X —— 求解器的**候选空间**。

**为什么模板不是"参数默认值 + 覆盖"**:那样每个 shot 都会长成 15 个字段,
diversity 计数没法算(要按"运镜家族"分桶而不是按字段值)。模板给每个家族
一个名字,连续旋钮离散成 3 档,`(family, size0, size1, level)` 四元组就能
用来算 H2/H3/H4 硬约束。

**12 族的选择依据**:枚举 A_SHOTS/B_SHOTS 21 镜的 Cam 参数,按主导运动分组
—— push_in(6)、pull_out(2)、track_lr(4)、tilt_ud(3)、pan_ud(2)、roll(3)、
whip(2)、orbit(2)、flip(1)、hold(1)、handheld(0)、rack_focus(0)。
后 3 族当前未被手工分镜用到,但求解器可以按需选,让候选空间够宽。

**9 种转场**:cut / dissolve / flash_black / flash_white / whip / match_cut /
flip / wipe / tail_fade。cut 是默认,其他 8 种需要 shot.fx 里挂对应参数
(scan 光条切、white_flash、black_flash、blur、flip 手势)——转场是**镜间**的事,
不是镜内 fx,但因为 fx 是唯一挂点,复用 fx 字典表达。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class MoveTemplate:
    name: str                          # 家族名(diversity 计数按此分桶)
    ease: str                          # 缓动族
    build: Callable[[dict], dict]      # (args) -> Cam kwargs 部分

    def apply(self, size0: str, size1: str, args: dict) -> dict:
        """→ Cam 关键字参数 dict,由调用方 `Cam(**out)` 组装。"""
        base = {"size0": size0, "size1": size1, "ease": self.ease}
        base.update(self.build(args))
        return base


def _push(args: dict) -> dict:
    """慢推:size0 → size1(size1 更近),ease_out。"""
    return {"dx": args.get("dx", 0.0), "dy": args.get("dy", 0.0)}


def _pushfast(args: dict) -> dict:
    """快推:zoom 显式给大值,snap<1 让主要运动在前 60% 走完。"""
    return {"zoom": args.get("zoom", 1.25),
            "dx": args.get("dx", 0.0), "snap": args.get("snap", 0.6)}


def _pull(args: dict) -> dict:
    """拉:size0 → size1(size1 更远,或 zoom<1)。"""
    return {"zoom": args.get("zoom", 0.75), "dx": args.get("dx", 0.0)}


def _tracklr(args: dict) -> dict:
    """横移(dx 主导)。sign +1 = 右移, -1 = 左移。"""
    return {"dx": args.get("magnitude", 0.28) * args.get("sign", 1)}


def _panud(args: dict) -> dict:
    """纵移(dy 主导)。sign +1 = 下移, -1 = 上移。"""
    return {"dy": args.get("magnitude", 0.24) * args.get("sign", 1)}


def _tiltud(args: dict) -> dict:
    """俯仰(elev 变):sign +1 = 起(视线抬高), -1 = 压。"""
    e0 = args.get("e0", 90.0)
    e1 = args.get("e1", 60.0 if args.get("sign", 1) < 0 else 90.0)
    return {"e0": e0, "e1": e1, "dx": args.get("dx", 0.0)}


def _roll(args: dict) -> dict:
    """滚转(r 变):magnitude 度数。"""
    return {"r0": args.get("r0", 0.0),
            "r1": args.get("r1", args.get("magnitude", 12.0)),
            "dx": args.get("dx", 0.0)}


def _whip(args: dict) -> dict:
    """甩:大 dx + blur。snap=0.5 让运动集中在前半。"""
    return {"dx": args.get("magnitude", 0.35) * args.get("sign", 1),
            "snap": 0.5}


def _orbit(args: dict) -> dict:
    """环绕:同时 r + elev 变化。"""
    return {"r0": args.get("r0", 0.0),
            "r1": args.get("r1", args.get("magnitude", 20.0)),
            "e0": args.get("e0", 90.0),
            "e1": args.get("e1", 68.0)}


def _flip(args: dict) -> dict:
    """翻面:elev 大幅变化 + snap<1(短暂动作)。"""
    return {"e0": args.get("e0", 24.0), "e1": 90.0,
            "ease": "ease_out_back",
            "back": args.get("back", 0.06),
            "snap": args.get("snap", 0.28)}


def _hold(args: dict) -> dict:
    """静镜:所有偏移为 0,elev 起止相等。"""
    return {"dx": 0.0, "dy": 0.0}


def _handheld(args: dict) -> dict:
    """手持:小 dx/dy 抖动(通过 back 参数模拟）。"""
    return {"dx": args.get("dx", 0.05),
            "ease": "ease_in_out_sine",
            "back": args.get("back", 0.02)}


def _rack(args: dict) -> dict:
    """变焦(rack focus):zoom 变化配合 elev 微调 —— 不同于纯 push。"""
    return {"zoom": args.get("zoom", 1.15),
            "e0": args.get("e0", 90.0),
            "e1": args.get("e1", 82.0)}


MOVE_TEMPLATES: dict[str, MoveTemplate] = {
    "push_slow": MoveTemplate("push", "ease_out_quad",   _push),
    "push_fast": MoveTemplate("push", "ease_out_expo",   _pushfast),
    "pull":      MoveTemplate("pull", "ease_out_quart",  _pull),
    "track_l":   MoveTemplate("track", "ease_in_out_sine", lambda a: _tracklr({**a, "sign": -1})),
    "track_r":   MoveTemplate("track", "ease_in_out_sine", lambda a: _tracklr({**a, "sign": +1})),
    "pan_u":     MoveTemplate("pan",   "ease_in_out_cubic", lambda a: _panud({**a, "sign": -1})),
    "pan_d":     MoveTemplate("pan",   "ease_in_out_cubic", lambda a: _panud({**a, "sign": +1})),
    "tilt_u":    MoveTemplate("tilt",  "ease_out_cubic",  lambda a: _tiltud({**a, "sign": -1})),
    "tilt_d":    MoveTemplate("tilt",  "ease_out_cubic",  lambda a: _tiltud({**a, "sign": +1})),
    "roll":      MoveTemplate("roll",  "ease_in_sine",    _roll),
    "whip":      MoveTemplate("whip",  "ease_out_quart",  _whip),
    "orbit":     MoveTemplate("orbit", "ease_in_out_expo", _orbit),
    "flip":      MoveTemplate("flip",  "ease_out_back",   _flip),
    "hold":      MoveTemplate("hold",  "linear",          _hold),
    "handheld":  MoveTemplate("handheld", "ease_in_out_sine", _handheld),
    "rack":      MoveTemplate("rack",  "ease_out_quart",  _rack),
}


# ---------- 转场 X ----------

@dataclass(frozen=True)
class TransTemplate:
    name: str
    fx_apply: Callable[[dict], dict]   # (fx_dict) -> updated fx


def _cut(fx: dict) -> dict:
    return fx


def _dissolve(fx: dict) -> dict:
    fx = dict(fx)
    fx.setdefault("blur", (2, 8))
    return fx


def _flash_white(fx: dict) -> dict:
    fx = dict(fx)
    fx.setdefault("flash", ("white", 0.067, 0.92))
    return fx


def _flash_black(fx: dict) -> dict:
    fx = dict(fx)
    fx.setdefault("flash", ("black", 0.067, 0.92))
    return fx


def _whip_trans(fx: dict) -> dict:
    fx = dict(fx)
    fx.setdefault("blur", (2, 34))
    return fx


def _flip_trans(fx: dict) -> dict:
    return dict(fx)  # 靠 flip move 承载,fx 不动


def _match(fx: dict) -> dict:
    return dict(fx)  # 依赖 subject/景别对齐,不改 fx


def _wipe(fx: dict) -> dict:
    fx = dict(fx)
    fx.setdefault("scan", (0.35, 0.35, 0.60, 0.60))
    return fx


def _tail_fade(fx: dict) -> dict:
    fx = dict(fx)
    fx.setdefault("dark", (0.42, 1.0))
    fx.setdefault("leak", (0.0, 0.34))
    return fx


TRANS_TEMPLATES: dict[str, TransTemplate] = {
    "cut":         TransTemplate("cut",         _cut),
    "dissolve":    TransTemplate("dissolve",    _dissolve),
    "flash_white": TransTemplate("flash_white", _flash_white),
    "flash_black": TransTemplate("flash_black", _flash_black),
    "whip":        TransTemplate("whip",        _whip_trans),
    "flip":        TransTemplate("flip",        _flip_trans),
    "match_cut":   TransTemplate("match_cut",   _match),
    "wipe":        TransTemplate("wipe",        _wipe),
    "tail_fade":   TransTemplate("tail_fade",   _tail_fade),
}


def move_families() -> set[str]:
    return {m.name for m in MOVE_TEMPLATES.values()}


def trans_names() -> list[str]:
    return list(TRANS_TEMPLATES.keys())
