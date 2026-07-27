"""《明月天涯》色板 —— design_language.md §1 声明色的唯一实现处。

**§1.A 扫描仪世界**:所有色都能回答「这是那台机器的哪个部位」。
**§1.B 折纸世界**:所有色都能回答「这是那张纸/那张桌的哪个光学现象」。

工具函数 `resolve(name)` 供 YAML 加载器按名称查色,避免加载器里出现色板字面量。
"""
from __future__ import annotations


def _hex(s: str) -> tuple[int, int, int]:
    return tuple(int(s[i:i + 2], 16) for i in (1, 3, 5))


# design_language.md §1.A
A_BASE     = _hex("#E8E3D6")   # 机身塑料本色
A_BASE_OLD = _hex("#D6CDB8")   # 泛黄面
A_MAIN     = _hex("#F4F2EC")   # 上盖白海绵内衬 / 白背板
A_GLASS    = _hex("#A9C4B4")   # 浮法玻璃切口绿边(全片唯一冷色)
A_LAMP     = _hex("#E6FBF0")   # CCFL 灯管 6500K 绿白
A_LEAK     = _hex("#FFF4E2")   # 掀盖灌进来的日光 5500K
A_SHADOW   = _hex("#4A463E")   # 机身缝隙(暖深灰,不是冷灰)
A_DARK     = _hex("#221F1A")   # 合盖时机内(有漫反射,不是死黑)

# design_language.md §1.B
B_WOOD      = _hex("#D9C7A8")  # 白蜡木桌面
B_WOOD_DEEP = _hex("#B79E7A")  # 木纹深线
B_PAPER     = _hex("#F6F3EC")  # 160g 蛋壳白
B_FIBER     = _hex("#E4DDCF")  # 麻纤维絮点
B_CREASE_HL = _hex("#FFFDF7")  # 折痕亮线(纤维被破坏会发白)
B_CREASE_SH = _hex("#C9C0AE")  # 折痕暗线
B_STACK     = _hex("#B5AB98")  # 叠层缝
B_DROP      = _hex("#A08A6B")  # 投影(桌面色的暗版偏暖,不是灰)

_PALETTE: dict[str, tuple[int, int, int]] = {k: v for k, v in globals().items()
                                              if k[0].isupper() and isinstance(v, tuple)}


def resolve(name: str) -> tuple[int, int, int]:
    """按名字查色 —— YAML 加载器用这个,避免加载器里出现色板字面量。"""
    if name not in _PALETTE:
        raise KeyError(f"palette: 找不到颜色 {name!r}")
    return _PALETTE[name]
