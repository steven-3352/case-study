"""YAML 分镜加载器 —— 把 shots_{a,b}.yaml 重建成 MShot 列表。

**和 Python 版的关系**:加载结果要与 `mingyue_render.A_SHOTS / B_SHOTS` 在
`items(t, k)` 层逐元素相等 —— 断言工具 `tools/assert_items.py` 验这条。

**color 解析规则**:YAML 里的颜色引用是 palette 名(如 `A_SHADOW`)，由
`palette.resolve()` 转成 tuple。bg/fx 里的颜色也走同一套规则。

**fx 类型修正**:YAML 的 list 是 Python list，fx_pass 里做的是 pair/tuple
索引，tuple/list 都支持 `pair[0]` 语法，所以不需要转成 tuple。
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mv_engine.camera import Cam
from mv_engine.shot import MShot
from .layouts import build_items_fn
from .palette import resolve as _color


def _cam(d: dict) -> Cam:
    return Cam(**d)


def _bg(spec: list | None) -> tuple:
    if not spec:
        return ()
    name, col, contrast, tile = spec
    if isinstance(col, str):
        col = _color(col)
    return (name, col, contrast, tile)


def _fx(d: dict | None) -> dict:
    if not d:
        return {}
    out = {}
    for k, v in d.items():
        out[k] = v  # list is fine — fx_pass uses pair[0]/pair[1] indexing
    return out


def _load_shot(s: dict) -> MShot:
    t0, t1 = s["t"]
    cam    = _cam(s["cam"])
    layout = s.get("layout", {})
    items_fn = build_items_fn(layout, _color)
    subject  = tuple(s.get("subject", [0]))
    bg       = _bg(s.get("bg"))
    fx       = _fx(s.get("fx"))
    note     = s.get("note", "")
    if isinstance(note, str):
        note = note.strip()
    return MShot(
        sid=s["sid"], t0=t0, t1=t1,
        cam=cam, items=items_fn,
        subject=subject, bg=bg, fx=fx, note=note,
    )


def load(path: str | Path) -> list[MShot]:
    """从 YAML 文件加载 MShot 列表。"""
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return [_load_shot(s) for s in data["shots"]]
