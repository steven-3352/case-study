"""相机模型 · 平面采样 · 俯仰透视 —— 只碰几何,不碰内容。

**5 个自由度**:`(cx, cy)` 世界中心 · `s` 缩放 · `r` 滚转 · `elev` 俯仰。
前 4 个在平面内解决(取景框 = 世界里一个旋转矩形);俯仰单独做一次透视变形。

**缩放为什么是解出来的**:分镜写景别(极端全景/大特写),`FRAMING` 表把景别翻成
「主体占画幅的比例」,再由 `solve_scale` 反解出 `s`。逐帧解会让占比恒等于目标,
物体自己的尺寸变化在画面上被完全抵消(B 段每半拍面积减半 → 折了跟没折一样)。
所以只解镜首镜末,中间做对数插值 —— 见 `adapter runtime` docstring。

`sample_plane` 走一次透视反解而不是 `rotate + crop + resize` 三步:三步会累计三次
重采样,平移小于一个像素时还会抖。`tilt` 的 `in_quad / out_quad` 传给
`atoms.solve_perspective` —— PIL 用**反向映射**,顺序传反了图像会以奇怪的方式
外扩,不会报错。
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import NamedTuple

from PIL import Image

from .atoms import solve_perspective
from .config import FRAMING, H, OX, OY, PAD_W, PAD_H, W
from .ease import _clamp, ease


class View(NamedTuple):
    cx: float
    cy: float
    s: float
    r: float


@dataclass(frozen=True)
class Cam:
    """一镜的相机轨迹。位移/滚转/俯仰照抄分镜,缩放由目标占比反解(见模块 docstring)。"""
    size0: str                       # 起始景别
    size1: str = ""                  # 结束景别(空 = 用 zoom 比值推)
    zoom: float = 1.0                # 镜内缩放比值(分镜声明的 scale 末/初)
    dx: float = 0.0                  # 中心横移,取景框宽的几分之几
    dy: float = 0.0                  # 中心纵移,取景框高的几分之几
    look: tuple = (0.0, 0.0)         # 看向哪个世界点(默认世界原点 = 主体所在)
    r0: float = 0.0
    r1: float = 0.0
    e0: float = 90.0                 # 俯仰:90 正俯视 · 0 平视 · 负 仰拍
    e1: float | None = None
    ease: str = "linear"
    back: float = 0.0
    hold_from: float = 1.0           # k 过此值后相机锁死(A06 提前 0.22s 停)
    snap: float = 1.0                # <1 表示运动在镜内前 snap 比例就走完(A10 4 帧)
    delay: float = 0.0               # k 到此值之前完全静止(B06 死寂 0.244s)
    hold_size: bool = False          # 镜末不按占比重解缩放(见 shot_scales)

    def progress(self, k: float) -> float:
        k = _clamp((k - self.delay) / max(1e-6, self.snap - self.delay))
        return ease(self.ease, min(k, self.hold_from), self.back)

    def scale_progress(self, k: float) -> float:
        """缩放专用的进度 —— 夹在 [0,1]。

        `ease_out_back` 的回弹越过 1 是要的:位移多滑一点、转多转几度,然后荡回来。
        但缩放是**比值**插值,B06 镜首镜末差 200 倍,越界 46% 就是 200^0.46 ≈ 11 倍,
        整块纸直接缩成一个点(画面只剩桌面)。回弹给位移和滚转,不给推拉。
        """
        return _clamp(self.progress(k))

    def at(self, k: float, s: float) -> tuple[float, float, float, float]:
        """→ (中心偏移x, 中心偏移y, 滚转, 俯仰)。偏移是**世界**量,所以要先有缩放。

        `dx/dy` 是"横移过取景框的几分之几",取景框在世界里有 W/s 宽 —— 早期版本
        直接写成 `W*(0.5+dx*...)`,那是屏幕坐标,而所有物件都摆在世界原点附近,
        于是相机永远在看主体旁边的空地,主体被挤到角上或干脆出画。
        偏移的基准点(看向谁)由 `shot_scales` 给。
        """
        e = self.progress(k)
        cx = (W / s) * self.dx * (e - 0.5)
        cy = (H / s) * self.dy * (e - 0.5)
        r = self.r0 + (self.r1 - self.r0) * e
        e1 = self.e0 if self.e1 is None else self.e1
        el = self.e0 + (e1 - self.e0) * e
        # ease_out_back 会让 e 越过 1;位移越界是要的回弹,俯仰越过 90° 却是平面翻个面
        # (观众看到人物上下颠倒),必须夹住。
        return cx, cy, r, _clamp(el, -88.0, 90.0)

    @property
    def share0(self) -> float:
        return FRAMING[self.size0]

    @property
    def share1(self) -> float:
        return FRAMING[self.size1] if self.size1 else FRAMING[self.size0] * self.zoom ** 2


def solve_scale(share: float, world_w: float, world_h: float) -> float:
    """由目标占比与主体的世界尺寸反解相机缩放。"""
    area = max(1.0, world_w * world_h)
    return math.sqrt(_clamp(share, 0.002, 4.0) * W * H / area)


def sample_plane(src: Image.Image, cx: float, cy: float, s: float, r: float,
                 out_size: tuple[int, int]) -> Image.Image:
    """从世界底图取一个取景框:中心 (cx,cy) 世界像素、缩放 s、滚转 r 度。

    走一次透视反解而不是 rotate+crop+resize 三步 —— 三步会累计三次重采样,
    平移小于一个像素时还会抖。
    """
    ow, oh = out_size
    a = math.radians(-r)
    ca, sa = math.cos(a), math.sin(a)
    out_quad = [(0, 0), (ow, 0), (ow, oh), (0, oh)]
    in_quad = []
    for (u, v) in out_quad:
        dx, dy = (u - ow / 2) / s, (v - oh / 2) / s
        in_quad.append((cx + dx * ca - dy * sa, cy + dx * sa + dy * ca))
    coeffs = solve_perspective(out_quad, in_quad)
    return src.transform(out_size, Image.Transform.PERSPECTIVE, coeffs, Image.BICUBIC)


def w2s(pt: tuple[float, float], cx: float, cy: float, s: float, r: float,
        origin: tuple[int, int] = (OX, OY)) -> tuple[float, float]:
    """世界像素 → 平面画布像素(与 `sample_plane` 互逆)。"""
    a = math.radians(r)
    ca, sa = math.cos(a), math.sin(a)
    dx, dy = pt[0] - cx, pt[1] - cy
    return (origin[0] + W / 2 + s * (dx * ca - dy * sa),
            origin[1] + H / 2 + s * (dx * sa + dy * ca))


def tilt(im: Image.Image, elev: float) -> Image.Image:
    """把画好的平面按俯仰角做一次透视,并裁回画幅。

    elev=90 正俯视 → 直接中心裁切(不重采样)。
    elev<90 远端(上沿)变宽变高 → 透视收缩,读作"镜头压低了"。
    elev<0 仰拍 → 换成近端(下沿)变宽。
    """
    box = (OX, OY, OX + W, OY + H)
    if abs(elev) >= 89.5:
        return im.crop(box)
    k = _clamp(math.cos(math.radians(_clamp(elev, -89.0, 90.0))), 0.0, 1.0)
    dx, dy = W * 0.50 * k, H * 0.30 * k
    if elev >= 0:
        in_quad = [(OX - dx, OY - dy), (OX + W + dx, OY - dy),
                   (OX + W, OY + H), (OX, OY + H)]
    else:
        in_quad = [(OX, OY), (OX + W, OY),
                   (OX + W + dx, OY + H + dy), (OX - dx, OY + H + dy)]
    out_quad = [(0, 0), (W, 0), (W, H), (0, H)]
    coeffs = solve_perspective(out_quad, in_quad)
    return im.transform((W, H), Image.Transform.PERSPECTIVE, coeffs, Image.BICUBIC)


def quad_of(rect: tuple, v: View) -> list:
    x, y, w, h = rect
    return [w2s(p, v.cx, v.cy, v.s, v.r)
            for p in ((x, y), (x + w, y), (x + w, y + h), (x, y + h))]
