"""原子准入契约 —— 跨片累积的前提。

判据是**函数体是否引用模块级内容常量**(色板 / 字体 / 素材名),客观可判,
不靠人工感觉。四条:

1. **不带默认颜色** —— 原子不知道自己在哪部片里用,一旦自带默认色,
   它就偷偷带了一套色板进来。颜色一律由调用方按该片 design_language §1 传入。
2. **纯函数** —— 无 I/O、无模块级全局、`(arr | Image, **纯标量) -> 同类型`。
   就地画在 canvas 上的(`crease` / `stack_edge`)是显式例外,返回 None。
3. **必须声明 `touches_alpha`** —— 这是原子库与 `track.py` 预测器之间的接口。
   不动 alpha 的原子对主体包围盒没有贡献,预测器整个跳过;动 alpha 的才进几何链。
   声明错了不会报错,只会让预测器安静地算错 —— 所以它是契约不是注释。
4. **必须能被 `lock.py` 摘要覆盖** —— 跨片复用的前提是敢改,敢改的前提是
   改坏了立刻有人喊。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, TypeVar

F = TypeVar("F", bound=Callable)


@dataclass(frozen=True)
class AtomSpec:
    name: str
    touches_alpha: bool
    fn: Callable

    @property
    def module(self) -> str:
        return self.fn.__module__.rsplit(".", 1)[-1]


REGISTRY: dict[str, AtomSpec] = {}


def atom(*, touches_alpha: bool, name: str = "") -> Callable[[F], F]:
    """登记一个原子。`touches_alpha` 无默认值 —— 必须显式想过。"""
    def deco(fn: F) -> F:
        key = name or fn.__name__
        if key in REGISTRY:
            raise ValueError(f"原子重名: {key}")
        REGISTRY[key] = AtomSpec(key, touches_alpha, fn)
        return fn
    return deco


def alpha_touching() -> frozenset[str]:
    """会改 alpha 的原子名集合 —— 预测器据此决定谁进几何链。"""
    return frozenset(k for k, s in REGISTRY.items() if s.touches_alpha)
