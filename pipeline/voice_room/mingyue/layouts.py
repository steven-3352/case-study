"""布局注册表 —— 内容层的 items 工厂，供 YAML 加载器调用。

三类 item 工厂:
- `fn: doll` — doll_item(name, world_h, center, crop, **kw)
- `fn: tex`  — tex_item(name, rect, col, contrast, keying, **kw)
- `fn: prop` — Item(("prop", name), rect)

三类 group 展开:
- `base: bed`      — 两张底层(chassis_plastic + glass_platen)
- `group: four`    — _four(t, k, crop, h) 四张叠脸
- `group: grid_four` — _grid_four(t) 四宫格
- `group: grid_item` — _grid_item(k) 折纸网格
- `group: paper_item` — paper_item(t, kind, center, n)

复杂时变镜走 `handler: <name>` 注册表:
- handler: a08_dual_doll
- handler: b06_unfold

调用约定: 所有 handler 签名均为 `(t: float, k: float, args: dict) -> tuple[Item, ...]`
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Callable

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mv_engine.config import W
from mv_engine.ease import ease
from mv_engine.items import Item

import mingyue_render as _mr

# 直接引用 mingyue_render 里现存的函数 — Phase 1b 阶段不重新实现
doll_item  = _mr.doll_item
tex_item   = _mr.tex_item
_bed       = _mr._bed
_four      = _mr._four
_grid_four = _mr._grid_four
_ink       = _mr._ink
paper_item = _mr.paper_item

FACE = _mr.FACE
EYE  = _mr.EYE

# ---------- 复杂镜 handler ----------

def _h_a08_dual_doll(t: float, k: float, args: dict) -> tuple[Item, ...]:
    """A08:双人相向运动,位置随 k 线性变化。"""
    return _bed(
        doll_item("cy", 1420, (-W * 0.21 * k, -120), FACE, grey=_ink("cy", t)),
        doll_item("诺兰", 1020 + 400 * k, (W * 0.24 * k, 210), FACE,
                  grey=_ink("诺兰", t)))


def _h_b06_unfold(t: float, k: float, args: dict) -> tuple[Item, ...]:
    """B06:死寂后折纸弹开——格纸从 n=16 按 ease_out_back 倒退展开。"""
    if t < 26.204:
        return (paper_item(t, "cy", n=16),)
    n = max(0, round(16 * (1 - ease("ease_out_back", (t - 26.204) / 0.464, 0.34))))
    return (paper_item(t, "grid", n=n),)


_HANDLERS: dict[str, Callable] = {
    "a08_dual_doll": _h_a08_dual_doll,
    "b06_unfold":    _h_b06_unfold,
}


def get_handler(name: str) -> Callable:
    if name not in _HANDLERS:
        raise KeyError(f"layout handler 未注册: {name!r}")
    return _HANDLERS[name]


# ---------- 叶子 item 工厂 ----------

def _resolve_crop(name: str | None):
    if name is None:
        return None
    return {"FACE": FACE, "EYE": EYE}[name]


def _make_item(spec: dict, palette_resolve) -> Item | None:
    """把一条 YAML item 描述转成 Item。返回 None 表示这条是 group 展开器(由调用方处理)。"""
    fn = spec.get("fn")
    if fn == "doll":
        center = spec.get("center", (0.0, 0.0))
        return doll_item(
            spec["name"],
            spec["world_h"],
            tuple(center),
            _resolve_crop(spec.get("crop")),
            grey=spec.get("grey", 0.0),
            opacity=spec.get("opacity", 1.0),
            scan_split=spec.get("scan_split", False),
        )
    if fn == "tex":
        col = spec.get("col")
        if isinstance(col, str):
            col = palette_resolve(col)
        return tex_item(
            spec["name"],
            tuple(spec["rect"]),
            col,
            spec.get("contrast", 1.0),
            spec.get("keying", ""),
            grey=spec.get("grey", 0.0),
            opacity=spec.get("opacity", 1.0),
        )
    if fn == "prop":
        return Item(("prop", spec["name"]), tuple(spec["rect"]))
    return None  # group / base / handler — handled by build_items_fn


def build_items_fn(layout: dict, palette_resolve) -> Callable:
    """把 YAML layout 块编译成 `(t, k) -> tuple[Item, ...]` 可调用对象。

    layout 结构:
        base: bed              # 可选,在所有 items 前插入 _bed 两层
        items:                 # 静态或引用 group
          - {fn: doll, ...}
          - {group: four, ...}
          - {handler: b06_unfold}
        handler: a08_dual_doll # 整镜用一个 handler 替代 items(互斥)
    """
    if "handler" in layout:
        h = get_handler(layout["handler"])
        h_args = {k: v for k, v in layout.items() if k != "handler"}
        def items_fn_handler(t, k, _h=h, _a=h_args):
            return _h(t, k, _a)
        return items_fn_handler

    use_bed = layout.get("base") == "bed"
    specs   = layout.get("items", [])

    # 预解析每条 spec 的"类型标签"，item 本身在 items_fn 里每次调用时按需构造
    # (不在 build_items_fn 里预构造 Item —— doll_item 需要 pe._PATHS 已初始化，
    #  而 loader 在 render 循环开始之前就被调用，那时 _PATHS 可能还没设好。)
    parsed: list = []
    for spec in specs:
        if "group" in spec:
            g      = spec["group"]
            g_args = {k: v for k, v in spec.items() if k != "group"}
            if g == "four":
                parsed.append(("group_four",
                                _resolve_crop(g_args.get("crop", "FACE")),
                                g_args.get("h", 760.0)))
            elif g == "grid_four":
                parsed.append(("group_grid_four",))
            elif g == "grid_item":
                parsed.append(("group_grid_item",))
            elif g == "paper_item":
                parsed.append(("group_paper_item",
                                g_args.get("kind", "cy"),
                                tuple(g_args.get("center", (0.0, 0.0))),
                                g_args.get("n")))
            else:
                raise ValueError(f"未知 group: {g!r}")
        elif "handler" in spec:
            h      = get_handler(spec["handler"])
            h_args = {k: v for k, v in spec.items() if k != "handler"}
            parsed.append(("handler", h, h_args))
        else:
            # 存 spec 字典，运行时再调用 _make_item（lazy）
            parsed.append(("spec", spec))

    def items_fn(t, k, _palette=palette_resolve, _parsed=parsed, _use_bed=use_bed):
        out: list[Item] = []
        if _use_bed:
            out.extend(_bed())
        for c in _parsed:
            kind = c[0]
            if kind == "spec":
                out.append(_make_item(c[1], _palette))
            elif kind == "group_four":
                out.extend(_four(t, k, c[1], c[2]))
            elif kind == "group_grid_four":
                out.extend(_grid_four(t))
            elif kind == "group_grid_item":
                from mingyue_render import _grid_item  # noqa: PLC0415
                out.append(_grid_item(k))
            elif kind == "group_paper_item":
                _, kind_, center_, n_ = c
                out.append(paper_item(t, kind_, center_, n_))
            elif kind == "handler":
                _, h_, a_ = c
                out.extend(h_(t, k, a_))
        return tuple(out)

    return items_fn
