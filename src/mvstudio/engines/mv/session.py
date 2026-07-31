"""每片运行时状态 —— 路径 + 各级缓存。

**为什么需要 Session**:`_LAYER / _PLATE / _TEX` 原来是 `adapter runtime.py` 里的
模块级全局 —— 无界、不可注入、spawn 子进程各建各的。把它们收进 Session 有三个好处:
1. `_init_worker` 不再靠 monkey-patch 全局路径,只要拿到同一个 Session 对象
2. 单进程测试里可以用独立 Session 隔离状态,不会跨用例污染
3. Phase 3 帧缓存的 cache key 里需要「这帧用了哪些素材」——Session 是计入的天然位置

产品代码显式创建并传递 Session。模块级单例只保留给迁移期 legacy 调用，
不得由新 executor 使用。

**`configure()` 一定要在任何 `tex/plate/layer` 调用之前调用**。
`adapter runtime.py` 在模块顶部调一次;`_init_worker` 在 spawn 子进程里再调一次
(spawn 子进程从头 import,模块级 configure 不会重跑)。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Session:
    assets_dir: Path = field(default_factory=Path)
    tex_dir: Path = field(default_factory=Path)
    gen_dir: Path = field(default_factory=Path)

    _tex: dict = field(default_factory=dict)
    _plate: dict = field(default_factory=dict)
    _plate_arr: dict = field(default_factory=dict)
    _layer: dict = field(default_factory=dict)
    _sheet: dict = field(default_factory=dict)
    _ground: dict = field(default_factory=dict)


_CURRENT: Session | None = None


def get(session: Session | None = None) -> Session:
    if session is not None:
        return session
    if _CURRENT is None:
        raise RuntimeError("mv_engine.session 未初始化 —— 先调 mv_engine.session.configure()")
    return _CURRENT


def configure(assets_dir: Path, tex_dir: Path, gen_dir: Path) -> Session:
    global _CURRENT
    _CURRENT = Session(
        assets_dir=Path(assets_dir),
        tex_dir=Path(tex_dir),
        gen_dir=Path(gen_dir),
    )
    return _CURRENT
