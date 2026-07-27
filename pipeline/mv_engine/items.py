"""世界平面上一块内容的最小描述 —— 不认色板、不认素材,只声明 key + rect。

**为什么 Item 不带自己的图**:`key` 是缓存路由(例如 `("doll", "cy", crop)`),
真正的位图由每片自己的 `layer()` 按 key 取。这层间接性让引擎里的合成
(`compose.place`)不用知道有多少种素材,只要能"按 key 拿到一张 RGBA"就够了。

`scan_split` 是 A 版扫描仪镜专用的语义标志(光条以下用原色,以上用灰版)——
它不是通用属性,但放这里比放在每个 shot 的 fx 字典里省事,且引擎默认忽略。
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Item:
    """世界平面上的一块内容。`key` 决定去哪儿取图,`rect` 是它在世界里占的矩形。"""
    key: tuple
    rect: tuple                      # (x, y, w, h) 世界像素,左上角
    grey: float = 0.0                # 0 原色 · 1 全灰(未扫描的那半)
    opacity: float = 1.0
    scan_split: bool = False         # 光条以下用原色,以上用灰版
