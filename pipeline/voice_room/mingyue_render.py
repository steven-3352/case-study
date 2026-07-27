#!/usr/bin/env python3
"""《明月天涯》22.465–29.780s 样段 · 创意 A(扫描仪) / B(对折) 的合成与渲染.

设计已冻结在 `publish/语音厅/design/storyboard_sample_22465_29780.md`,
本模块只做实现,不做设计判断。原子件 → `mingyue_atoms.py`,颜色 → `design_language.md` §1。

**为什么不复用 `paperdoll_engine.render_frame`:** 那套合成层是国风水墨原生的 ——
`make_bg()` 程序化背景(违反 `feedback_no-cheap-procedural-background`)、暖金晕影、
`CREAM #f8f4ea` 调色、朱砂印章、月/山脊/雨/云。本片两个世界的色板把这些全部禁掉了。
可迁移的只有通用基元(缓动、screen、bloom、grain、羽化、beats),那些直接 import。

## 相机模型

世界是一张平面(扫描仪台面 / 木桌),相机有 5 个自由度:

    (cx, cy) 世界坐标中心 · s 缩放 · r 滚转 · elev 俯仰

前四个在平面内解决(取景框 = 世界里一个旋转矩形);**俯仰单独做一次透视变形**,
因为平面上所有东西共享同一个平面,一次变形就够了 —— 分开对每个元素做透视会各自算错。
`elev=90` 正俯视(不变形),`0` 平视,**负值仰拍**(近的那条边变宽而不是远的)。

透视要采样到取景框以外的内容,所以平面先画在 `PW×PH` 的加宽画布上再变形,
`PAD_*` 就是为此留的余量;不留余量,仰拍/俯视时画面边缘会出现采样不到的黑边。

## 缩放为什么是**解出来的**不是抄分镜的

分镜里 B 段声明的 `scale` 绝对值与「折 16 次」的几何自相矛盾:16 次真对折是
每轴 /2⁸,任何合理开幅的纸到第 16 折都只剩几个像素,再乘声明的 +650% 也远达不到
声明的「占画面 31–36%」。两者只能保一个。

**保观众看到的那个**(铁律 0:交付判据是观众看到什么)。所以:

- 分镜的**景别**(极端全景/全景/中景/近景/特写/大特写)→ `FRAMING` 表 → 目标画面占比
- **只在镜首和镜末**按主体那一刻的真实世界尺寸反解 `s`,镜内在两者之间做对数插值

**为什么只解两头,不逐帧解:** 逐帧解会让占比恒等于目标,于是「每折面积 -50%」
在画面上被相机完全抵消,折纸变成看不见的事(R9 会判 FAIL,而且观众真的看不到)。
只锁两头,相机就按分镜声明的曲线平滑推拉,主体自己的尺寸台阶原样露在画面上 ——
这正是 B05「逐折跳变 ≥18%」的来源。

位移、滚转、俯仰、缓动、切点、折次时刻全部照抄分镜,只有 `s` 是解出来的。
"""
from __future__ import annotations

import argparse
import json
import logging
import math
import multiprocessing as mp
import subprocess
import sys
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import NamedTuple

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import mingyue_atoms as atoms  # noqa: E402
import paperdoll_engine as pe  # noqa: E402
from paperdoll_engine import bloom, full_doll, grain, screen  # noqa: E402
from mv_engine.camera import (  # noqa: E402
    Cam, View, quad_of, sample_plane, solve_scale, tilt, w2s,
)
from mv_engine.assets import flat_tex, plate, plate_arr, tex, tint  # noqa: E402
from mv_engine.compose import warp  # noqa: E402
from mv_engine.config import FPS, FRAMING, H, OX, OY, PAD_H, PAD_W, W  # noqa: E402
from mv_engine.ease import EASES, _clamp, _out_back, ease  # noqa: E402
from mv_engine.fx import _hblur, _lerp  # noqa: E402
from mv_engine.items import Item  # noqa: E402
import mv_engine.session as _mvsession  # noqa: E402
from mv_engine.shot import MShot, active, shot_scales  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "publish" / "语音厅" / "script_v2_assets"
TEX = ROOT / "publish" / "语音厅" / "assets" / "textures"
GEN = TEX / "scanner_gen"
OUT = ROOT / "publish" / "语音厅" / "sample_22465_29780"
WAV = ROOT / "publish" / "语音厅" / "明月天涯 导唱(1).WAV"

SEG_T0, SEG_T1 = 22.465, 29.780

_mvsession.configure(ASSETS, TEX, GEN)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("mingyue")


def _hex(s: str) -> tuple[int, int, int]:
    return tuple(int(s[i:i + 2], 16) for i in (1, 3, 5))


# design_language.md §1.A — 每个色都能回答"这是那台机器的哪个部位"
A_BASE = _hex("#E8E3D6")        # 机身塑料本色
A_BASE_OLD = _hex("#D6CDB8")    # 泛黄面
A_MAIN = _hex("#F4F2EC")        # 上盖白海绵内衬 / 白背板
A_GLASS = _hex("#A9C4B4")       # 浮法玻璃切口绿边(全片唯一冷色)
A_LAMP = _hex("#E6FBF0")        # CCFL 灯管 6500K 绿白
A_LEAK = _hex("#FFF4E2")        # 掀盖灌进来的日光 5500K
A_SHADOW = _hex("#4A463E")      # 机身缝隙(暖深灰,不是冷灰)
A_DARK = _hex("#221F1A")        # 合盖时机内(有漫反射,不是死黑)

# design_language.md §1.B
B_WOOD = _hex("#D9C7A8")        # 白蜡木桌面
B_WOOD_DEEP = _hex("#B79E7A")   # 木纹深线
B_PAPER = _hex("#F6F3EC")       # 160g 蛋壳白
B_FIBER = _hex("#E4DDCF")       # 麻纤维絮点
B_CREASE_HL = _hex("#FFFDF7")   # 折痕亮线(纤维被破坏会发白)
B_CREASE_SH = _hex("#C9C0AE")   # 折痕暗线
B_STACK = _hex("#B5AB98")       # 叠层缝
B_DROP = _hex("#A08A6B")        # 投影(桌面色的暗版偏暖,不是灰)


# 缓动 / 景别表已迁至 mv_engine.{ease,config},见模块顶部 import。


# tex / flat_tex / tint / plate / plate_arr 已迁至 mv_engine.assets,见模块顶部 import。
# 相机 · View · 平面采样已迁至 mv_engine.camera,见模块顶部 import。


# ————————————————— 世界元件 —————————————————
# Item 已迁至 mv_engine.items。


_LAYER: dict = {}


def _key_prop(im: Image.Image, thresh: int = 30) -> Image.Image:
    """把生成的道具立绘从它那张平底色背景上抠下来.

    四角泛洪而不是按亮度阈值 —— 机身本身是象牙白,跟背景一样浅,
    按亮度抠会把机器一起抠掉;泛洪只吃与角落连通的那片。
    """
    im = im.convert("RGB")
    w, h = im.size
    tmp = im.copy()
    for pt in ((2, 2), (w - 3, 2), (2, h - 3), (w - 3, h - 3)):
        ImageDraw.floodfill(tmp, pt, (255, 0, 255), thresh=thresh)
    a = np.asarray(tmp)
    keyed = (a[:, :, 0] > 240) & (a[:, :, 1] < 20) & (a[:, :, 2] > 240)
    alpha = Image.fromarray(np.where(keyed, 0, 255).astype(np.uint8))
    alpha = alpha.filter(ImageFilter.GaussianBlur(1.2))
    out = im.convert("RGBA")
    out.putalpha(alpha)
    return out.crop(out.getbbox() or (0, 0, w, h))


def layer(key: tuple) -> Image.Image:
    """key → RGBA 图层(缓存)。key[0] 是种类,其余是参数。"""
    if key in _LAYER:
        return _LAYER[key]
    kind = key[0]
    if kind == "doll":
        _, name, crop = key
        d = full_doll(name)
        if crop:
            l, tp, r, b = crop
            d = d.crop((int(l * d.width), int(tp * d.height),
                        int(r * d.width), int(b * d.height)))
            bb = d.getbbox()
            if bb:
                d = d.crop(bb)
            d = _feather(d)
        if d.height > 2200:
            d = d.resize((max(1, round(d.width * 2200 / d.height)), 2200), Image.LANCZOS)
        im = d
    elif kind == "tex":
        _, name, col, contrast, keying = key
        im = plate(name, col, contrast).convert("RGBA")
        if keying:
            im = key_by_lum(im, keying)
    elif kind == "prop":
        im = _key_prop(tex(key[1]))
    elif kind == "paper":
        im = paper_layer(key[1], key[2])
    else:
        raise KeyError(key)
    _LAYER[key] = im
    return im


def key_by_lum(im: Image.Image, mode: str) -> Image.Image:
    """按自身明暗抠出 alpha —— 让一张纹理当"叠加物"而不是一块贴片.

    灰尘/划痕/污渍这类东西,拍下来是「亮玻璃上的暗点」。整块贴上去只会
    盖出一个方板;要的是暗点留下、亮处透明。`mode="dark"` 留暗、`"bright"` 留亮。
    """
    a = np.asarray(im.convert("L"), dtype=float) / 255.0
    lo, hi = np.percentile(a, 4), np.percentile(a, 96)
    n = np.clip((a - lo) / max(hi - lo, 1e-3), 0.0, 1.0)
    alpha = (1.0 - n) if mode == "dark" else n
    out = im.copy()
    out.putalpha(Image.fromarray((alpha ** 1.6 * 255).astype(np.uint8)))
    return out


def _feather(im: Image.Image, frac: float = 0.10) -> Image.Image:
    """裁景别时把切平的硬边化成渐隐 —— 立绘内部像素一个不动。"""
    w, h = im.size
    a = np.asarray(im.getchannel("A"), dtype=float)
    mx, my = max(2, int(w * frac)), max(2, int(h * frac))
    rx = np.clip(np.minimum(np.arange(w), w - 1 - np.arange(w)) / mx, 0, 1)
    ry = np.clip(np.minimum(np.arange(h), h - 1 - np.arange(h)) / my, 0, 1)
    m = np.minimum(rx[None, :], ry[:, None])
    m = m * m * (3 - 2 * m)
    im = im.copy()
    im.putalpha(Image.fromarray((a * m).astype(np.uint8)))
    return im


def desat(im: Image.Image, amount: float, toward=A_SHADOW) -> Image.Image:
    """往灰里退 —— 未被光条扫到的那半张脸。"""
    if amount <= 0:
        return im
    a = np.asarray(im, dtype=float)
    g = a[:, :, :3].mean(axis=2, keepdims=True)
    g = g * 0.72 + np.asarray(toward, dtype=float)[None, None, :] * 0.28
    a[:, :, :3] = a[:, :, :3] * (1 - amount) + g * amount
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def doll_item(name: str, world_h: float, center=(0.0, 0.0), crop=None, **kw) -> Item:
    lay = layer(("doll", name, crop))
    ww = world_h * lay.width / lay.height
    return Item(("doll", name, crop), (center[0] - ww / 2, center[1] - world_h / 2, ww, world_h), **kw)


def tex_item(name: str, rect: tuple, col=None, contrast: float = 1.0,
             keying: str = "", **kw) -> Item:
    return Item(("tex", name, col, contrast, keying), rect, **kw)


# ————————————————— 平面合成 —————————————————
# quad_of 已迁至 mv_engine.camera。


# warp 已迁至 mv_engine.compose。


def place(canvas: Image.Image, it: Item, v: View, mask: Image.Image | None,
          scan_y: float | None) -> None:
    lay = layer(it.key)
    if it.grey > 0:
        lay = desat(lay, it.grey)
    if it.opacity < 1.0:
        lay = lay.copy()
        lay.putalpha(lay.getchannel("A").point(lambda p: int(p * it.opacity)))
    q = quad_of(it.rect, v)

    if it.scan_split and scan_y is not None:
        got = warp(desat(lay, 0.86), q, canvas.size)
        if got:
            canvas.alpha_composite(got[0], got[1])
        got = warp(lay, q, canvas.size)
        if got:
            im, (ox, oy) = got
            cut = int(OY + scan_y * H) - oy
            if cut > 0:
                a = np.asarray(im.getchannel("A"), dtype=np.uint8).copy()
                a[:max(0, min(a.shape[0], cut)), :] = 0
                im.putalpha(Image.fromarray(a))
            canvas.alpha_composite(im, (ox, oy))
    else:
        got = warp(lay, q, canvas.size)
        if got:
            canvas.alpha_composite(got[0], got[1])

    if mask is not None:
        got = warp(lay, q, mask.size)
        if got:
            mask.paste(got[0].getchannel("A"), got[1],
                       got[0].getchannel("A"))


def tiled(canvas: Image.Image, name: str, col, contrast: float,
          tile_world: float, v: View) -> None:
    """无限平面底(桌面/地面):按相机缩放铺瓷砖,再整体旋转.

    不用一张大底图采样 —— 极端全景时取景框有一万多世界像素宽,
    大到任何合理尺寸的底图都装不下,只能铺。

    反过来在大特写里(纸折到 12 世界像素宽时 s 会到 128),一块瓷砖被放大到
    二十多万像素宽,铺之前那一步 `resize` 就把内存吃光了(SIGKILL)。这种时候
    画面里根本不到一块砖,直接从原图裁出可见的那一小块再放大 —— 木纹的世界尺度
    不变(B04 拿木纹当尺子,变了就作弊了),只是换了个采样路径。
    """
    src = plate(name, col, contrast)
    d = int(math.hypot(*canvas.size)) + 2
    tw = max(6.0, tile_world * v.s)
    th = max(6.0, tile_world * v.s * src.height / src.width)

    if tw >= d and th >= d:
        # 可见区域落在一块砖内:算出它在原图里的 uv,按环绕取窗再放大。
        # 直接 crop 会在砖缝上越界(窗口跨了两块砖),所以用取模索引绕回去。
        a = plate_arr(name, col, contrast)
        sh_, sw_ = a.shape[0], a.shape[1]
        cw = max(2, int(round(sw_ * d / tw)))
        ch = max(2, int(round(sh_ * d / th)))
        x0 = int(round((1 - ((0.5 * d - v.cx * v.s) % tw) / tw) * sw_ - cw / 2))
        y0 = int(round((1 - ((0.5 * d - v.cy * v.s) % th) / th) * sh_ - ch / 2))
        xi = (np.arange(cw) + x0) % sw_
        yi = (np.arange(ch) + y0) % sh_
        big = Image.fromarray(a[np.ix_(yi, xi)]).resize((d, d), Image.BICUBIC)
    else:
        tw, th = int(tw), int(th)
        tile = src.resize((tw, th), Image.LANCZOS)
        big = Image.new("RGB", (d, d))
        px = (d / 2 - v.cx * v.s) % tw - tw
        py = (d / 2 - v.cy * v.s) % th - th
        for yy in range(int(py), d, th):
            for xx in range(int(px), d, tw):
                big.paste(tile, (xx, yy))
    if abs(v.r) > 1e-3:
        big = big.rotate(-v.r, Image.BICUBIC, center=(d / 2, d / 2))
    ox, oy = (d - canvas.width) // 2, (d - canvas.height) // 2
    canvas.paste(big.crop((ox, oy, ox + canvas.width, oy + canvas.height)), (0, 0))


# ————————————————— B · 纸 —————————————————
SHEET_W, SHEET_H = 2048, 1365          # 印张的位图分辨率
PAPER_W, PAPER_H = 3000.0, 2000.0      # 印张的世界尺寸(未折)
_SHEET: dict = {}


_GROUND: dict = {}


def _paper_ground(size: tuple) -> Image.Image:
    """真纸纹当底 —— 不是现搓渐变(feedback_no-cheap-procedural-background)。

    取一块裁切而不是把整张 5616px 实拍图压进目标尺寸:压缩比一变,纤维的观感尺度
    就跟着变。而且这张实拍图拍的是**一叠卷边的纸**,随便裁一块就会裁到某条卷边 ——
    折到第 16 折那块纸砖于是变成一道横贯画面的大白弧,像一团揉皱的东西。
    所以按局部方差挑**最平的那一块**:要的是"一张平整的纸",不是别人那叠纸的边。
    """
    if size not in _GROUND:
        src = tex(flat_tex("paper_fiber_0"))
        cw = min(src.width, max(size[0] * 3, 640))
        ch = min(src.height, max(size[1] * 3, 440))
        scan = np.asarray(src.convert("L").resize((320, 213), Image.LANCZOS), dtype=float)
        sx, sy = 320 / src.width, 213 / src.height
        wx, wy = max(2, int(cw * sx)), max(2, int(ch * sy))
        best = None
        for gy in range(0, 213 - wy + 1, max(1, (213 - wy) // 8)):
            for gx in range(0, 320 - wx + 1, max(1, (320 - wx) // 8)):
                v = float(scan[gy:gy + wy, gx:gx + wx].std())
                if best is None or v < best[0]:
                    best = (v, int(gx / sx), int(gy / sy))
        _, x, y = best
        im = src.crop((x, y, x + cw, y + ch)).resize(size, Image.LANCZOS)
        _GROUND[size] = tint(im, B_PAPER, 0.55).convert("RGBA")
    return _GROUND[size].copy()


def sheet(kind: str) -> Image.Image:
    """未折的印张。`cy` = Cy 一个人 · `grid` = 弹开后的 4×4(不是原来那张画)。"""
    if kind in _SHEET:
        return _SHEET[kind]
    im = _paper_ground((SHEET_W, SHEET_H))
    if kind == "cy":
        # 印**一张脸**不印全身:全身立绘是 815×2200 的细长条,不管怎么摆进 2048×1365 的
        # 横张,四周都是大片空白 —— 对折一次剩下的那半就是白纸,观众看到的是折纸,
        # 不是"她被折起来"。取头肩那一段、按**覆盖**(不是内接)铺满印张。
        #
        # 再往下要处理的是**折痕往哪儿收敛**:paper_fold 每次留近端那半(竖折留左、横折留上),
        # 所以折到深处,顶面永远是印张的**左上角**。整张只印一张脸时,左上角是她鬓边的
        # 淡背景 —— 于是第 8 折往后整块纸砖是空白奶油色,前面铺垫的十几折全白折。
        # 解法不是把脸挪到角上(那只救一档深度),是**自相似地印**:每一档折深对应的
        # 左上角区域里,再印一张缩小的她。这样每折一次露出来的还是她,越折越小,
        # 一直到纸砖那么大 —— 这正是「对折」想让观众看见的事。
        d = layer(("doll", "cy", None))
        head = d.crop((0, 0, d.width, int(d.height * 0.34)))
        head = head.crop(head.getbbox() or (0, 0, head.width, head.height))
        for m in range(6):
            rw, rh = SHEET_W >> m, SHEET_H >> m
            if rw < 16 or rh < 12:
                break
            sc = max(rw / head.width, rh / head.height)
            hd = head.resize((max(1, round(head.width * sc)), max(1, round(head.height * sc))),
                             Image.LANCZOS)
            # 隔档镜像:同一朝向套娃会被读成"贴重了",镜像后读成印张上的对开排版
            if m % 2:
                hd = hd.transpose(Image.FLIP_LEFT_RIGHT)
            im.alpha_composite(hd, ((rw - hd.width) // 2, 0))
    else:
        names = ("cy", "诺兰", "轩珩", "中里毅2")
        cw, ch = SHEET_W // 4, SHEET_H // 4
        for r in range(4):
            for c in range(4):
                d = layer(("doll", names[(r + c) % 4], (0.20, 0.02, 0.84, 0.26)))
                hh = int(ch * 0.80)
                d = d.resize((max(1, round(d.width * hh / d.height)), hh), Image.LANCZOS)
                im.alpha_composite(d, (c * cw + (cw - d.width) // 2, r * ch + (ch - hh) // 2))
        for i in range(1, 4):
            atoms.crease(im, i / 4, "vertical", B_CREASE_HL, B_CREASE_SH, 3, 7, 0.85, 0.45)
            atoms.crease(im, i / 4, "horizontal", B_CREASE_HL, B_CREASE_SH, 3, 7, 0.85, 0.45)
    _SHEET[kind] = im
    return im


def fold_world(n: int) -> tuple[float, float]:
    """折 n 次后纸的世界尺寸 —— 奇数折竖着折(减半宽),偶数折横着折。"""
    return PAPER_W / 2 ** ((n + 1) // 2), PAPER_H / 2 ** (n // 2)


def paper_layer(n: int, kind: str) -> Image.Image:
    """折 n 次后的纸(位图)。折得越深,顶面看到的就是原画越小的一块碎片。"""
    base = sheet(kind)
    # 真折到第 10 折为止。此前这里的阈值是 6,超过就换成一块**干净的空白纸砖** ——
    # 于是 B02 往后整版 B 全是白纸,观众从头到尾没看见她被折过,「对折」这个创意没了。
    # 第 10 折的碎片是 2048/32 × 1365/32,还看得出是脸上的一块;再往下才真的糊成一团,
    # 那时候复用第 10 折的碎片(不是换成白纸)——纸上有印痕,才读得出这砖是画折出来的。
    im = atoms.paper_fold(base, min(n, 10))
    if im.width < 96 or im.height < 72:
        sc = max(96 / im.width, 72 / im.height)
        im = im.resize((round(im.width * sc), round(im.height * sc)), Image.LANCZOS)
    if n > 10:
        atoms.crease(im, 0.5, "vertical" if n % 2 else "horizontal",
                     B_CREASE_HL, B_CREASE_SH, 4, 9, 0.95, 0.5)
    pad = Image.new("RGBA", (im.width + 140, im.height + 110), (0, 0, 0, 0))
    pad.alpha_composite(im, (0, 0))
    atoms.stack_edge(pad, 0, 0, im.width, im.height, min(n, 9), 1.6,
                     B_STACK, "right", B_DROP)
    atoms.stack_edge(pad, 0, 0, im.width, im.height, min(n, 9), 1.6,
                     B_STACK, "bottom", B_DROP)
    return pad.crop(pad.getbbox() or (0, 0, pad.width, pad.height))


FOLD_TIMES = [22.465, 22.697, 22.918, 23.150, 23.394, 23.627, 23.859, 24.091,
              24.323, 24.556, 24.799, 25.020, 25.252, 25.485, 25.728, 25.960]


def fold_at(t: float) -> int:
    """到 t 为止压死了几折 —— 半拍一折,第 16 折 25.960 落定。"""
    n = 0
    for i, ft in enumerate(FOLD_TIMES):
        span = (FOLD_TIMES[i + 1] - ft) if i + 1 < len(FOLD_TIMES) else 0.2325
        if t >= ft + span * 0.5:      # fold_press 过半才算压过去(前半是「折不动」)
            n = i + 1
    return n


def paper_item(t: float, kind: str = "cy", center=(0.0, 0.0), n: int | None = None) -> Item:
    n = fold_at(t) if n is None else n
    ww, hh = fold_world(n)
    return Item(("paper", n, kind), (center[0] - ww / 2, center[1] - hh / 2, ww, hh))


# ————————————————— 镜 —————————————————
# MShot · active · shot_scales 已迁至 mv_engine.shot。


# ————————————————— 屏幕层 FX —————————————————
# 明度事件最多把画面压到这个比例(见 fx_pass "dark")。
# 0.40 是**底色还是奶白**那版调的:那时整版明度上不去,靠 dark 往下压才有暗场。
# 底色翻成暗箱之后这两层叠乘,A07–A10 实测 p95 只剩 113–148 —— 整镜没有一处高光,
# 犯的是同一条铁律的另一半「禁全片压暗无亮」。抬到 0.62 只压缩幅度,不改曲线形状:
# A07 仍是全段最深的坑,4 次明度事件的相对次序一个不动。
DARK_FLOOR = 0.62


# _hblur · _lerp 已迁至 mv_engine.fx。


def fx_pass(arr: np.ndarray, sh: MShot, t: float, k: float) -> np.ndarray:
    f = sh.fx
    e = sh.cam.progress(k)

    if "smear" in f:
        amt, start, alpha = f["smear"]
        arr = atoms.jam_smear(arr, amt, start, 2.4, alpha)

    if "band" in f:
        freq, amp, sp = f["band"]
        arr = atoms.banding(arr, t, freq, amp, sp)

    # 明度事件先压环境,光条后画 —— 顺序反过来的话灯本身也被压暗,
    # "灯灭了,只剩这一道光照着她"就变成"整个画面一起变黑",人物直接看不见。
    if "dark" in f:
        # 分镜写的是**相对**明度曲线,直接当乘数用会压到 0.20,人物变成纯黑剪影 ——
        # 暗是设计,看不见不是。抬起地板只压缩幅度,不改曲线形状(A07 仍是全段最深的坑)。
        d = DARK_FLOOR + (1 - DARK_FLOOR) * _lerp(f["dark"], e)
        arr = arr * d + np.asarray(A_DARK, dtype=float)[None, None, :] * (1 - d) * 0.55

    if "scan" in f:
        y0, y1, a0, a1 = f["scan"][:4]
        hold = f["scan"][4] if len(f["scan"]) > 4 else 1.0
        y = _lerp((y0, y1), min(e / hold, 1.0) if hold < 1 else e)
        arr = atoms.scan_bar(arr, y, 16, 88, A_LAMP, _lerp((a0, a1), e),
                             direction="up", scanned_brightness_add=0.055)

    if "leak" in f:
        arr = atoms.lid_flare(arr, _lerp(f["leak"], e), 2.6, A_LEAK, bloom_radius_px=40)

    if "white" in f:
        k0, k1, lv = f["white"]
        if k0 <= k <= k1:
            w = lv * (1 - abs((k - k0) / max(1e-6, k1 - k0) * 2 - 1))
            arr = arr + (255.0 - arr) * w

    if "blur" in f:
        arr = _hblur(arr, int(_lerp(f["blur"], e)))

    if "flash" in f:
        kind, secs, lv = f["flash"]
        if t - sh.t0 < secs:
            g = lv * (1 - (t - sh.t0) / secs)
            arr = arr + (255.0 - arr) * g if kind == "white" else arr * (1 - g)

    arr = bloom(arr, thr=214, strength=0.55)
    return grain(arr, t, amp=5.0)


# ————————————————— 歌词 —————————————————
FONT_BRUSH = ROOT / "publish" / "语音厅" / "pv_v3_package" / "fonts" / "MaShanZheng-Regular.ttf"
_LYR_JSON = ROOT / "publish" / "语音厅" / "pv_v3_package" / "assets" / "lyric_timing.json"

# 加载与本段 [SEG_T0, SEG_T1] 重叠的行;每行保留 start + chars 列表
# chars 元素格式 [glyph, time_or_None],空格分隔符 time=null 不画字形
_LYR_LINES: list[dict] = []
with open(_LYR_JSON, encoding="utf-8") as _f:
    for _entry in json.load(_f):
        if _entry["end"] > SEG_T0 and _entry["start"] < SEG_T1:
            _LYR_LINES.append({"start": _entry["start"], "end": _entry["end"],
                               "cast": _entry["cast"], "chars": _entry["chars"]})

# V3 的 cast 段就是"这句谁在唱"。本段两句:22.68–26.10 Cy 独唱、26.74–29.78 诺兰·Cy 对唱。
# 四张脸同框的镜(A09/A10/A11)以前是按下标定灰度的 —— 谁在唱和画面谁亮没关系,
# 卡点卡的只是节拍不是人。接上之后:唱的人上墨,没唱的退到灰里。
_CAST_DOLL = {"CY": "cy", "NL": "诺兰", "XH": "轩珩", "ZL": "中里毅2"}


def singing(t: float) -> frozenset[str]:
    """t 时刻正在唱的角色(立绘名)。句与句之间的空档沿用上一句,不让四张脸集体熄掉。"""
    cur: list[str] = []
    for ln in _LYR_LINES:
        if ln["start"] <= t + 0.02:
            cur = ln["cast"]
    return frozenset(_CAST_DOLL[c] for c in cur if c in _CAST_DOLL)

_FONT_BRUSH_CACHE: dict[int, ImageFont.FreeTypeFont] = {}


def font(size: int) -> ImageFont.FreeTypeFont:
    # 马善政毛笔行书 —— 比通用标签字体多出书法节奏感
    if size not in _FONT_BRUSH_CACHE:
        _FONT_BRUSH_CACHE[size] = ImageFont.truetype(str(FONT_BRUSH), size)
    return _FONT_BRUSH_CACHE[size]


def _glyph_posture(ch: str, idx: int, u: float = 0.0) -> tuple[float, float, float]:
    """每个字位的姿态。返回 (rot_deg, dy_px, scale) —— dy/rot 是**相对字号的倍数**。

    `u` = 这个字在整行里的位置 0(行首)→1(行末)。

    哈希只负责"每个字不一样",不负责"这行像手写的"。此前只有哈希:字沿一条水平线
    随机上下 ±10px、随机歪 ±3.5° —— 那是抖动,不是笔迹,读起来像字幕做了防盗版处理。
    行书之所以读作行书,是因为整行有**一致的笔势**:统一往右后仰、行尾往上挑、
    中段微微拱起。所以这里把姿态拆成「行的笔势」+「字的个性」两项相加,
    笔势是主项,哈希退成小扰动。
    """
    h = (ord(ch) * 2654435761 + idx * 40503) & 0xFFFFFFFF
    b0 = (h & 0xFF) / 255.0
    b1 = ((h >> 8) & 0xFF) / 255.0
    b2 = ((h >> 16) & 0xFF) / 255.0
    sweep = -0.115 * u                       # 行尾比行首高 11.5% 字高
    camber = (1.0 - (2.0 * u - 1.0) ** 2) * 0.055   # 中段拱起
    rot = -4.2 + (b0 - 0.5) * 5.0            # 统一后仰 4.2° + 个性 ±2.5°
    dy = sweep + camber + (b1 - 0.5) * 0.075
    scale = 0.94 + b2 * 0.13
    return rot, dy, scale


def draw_lyrics(im: Image.Image, t: float, version: str, scan_y: float | None) -> None:
    """逐字落在自己的时间点上。A 版:光条以上的字是灰的,和脸同一条规则。"""
    # 最后一行 start <= t+0.02 就是当前行;不再用 LINE_BREAK 硬截
    active_line: dict | None = None
    for ln in _LYR_LINES:
        if ln["start"] <= t + 0.02:
            active_line = ln
    if active_line is None:
        return

    # 整行一次排版,没到时间的字**留位不画** —— 只排已出现的字,整行会随每个新字往左滑,
    # 一句唱完滑掉大半个字宽。书法写在一张定好的纸上,纸不动。
    tokens = active_line["chars"]   # [[glyph, time|null], ...]
    if not tokens:
        return

    # A 版底子暗(机器腔体),字用亮的;B 版底子是白纸,再用近白就是白写白 ——
    # 之前 B 的字只剩描边看得见,像一行淡金色小字。字幕不是字幕,是 MV 的字。
    ink, edge = (A_MAIN, A_SHADOW) if version == "a" else (A_DARK, B_CREASE_HL)

    BASE_SIZE = 152
    # 度量行宽;若超出画幅 92% 则等比缩字号
    LETTER_GAP = 8          # 字间固定间距
    SPACE_RATIO = 0.45      # 空格宽 = 字宽 × 0.45

    def measure_line(sz: int) -> tuple[list[float], float]:
        """返回 (每个 token 的 advance 列表, 总宽)。空格用 SPACE_RATIO*em。"""
        f = font(sz)
        advances: list[float] = []
        for ch, _lt in tokens:
            if ch == " ":
                # 用 em 近似字宽来算空格宽度
                bb = f.getbbox("国")
                em = bb[2] - bb[0]
                advances.append(em * SPACE_RATIO)
            else:
                bb = f.getbbox(ch)
                advances.append(bb[2] - bb[0] + LETTER_GAP)
        total = sum(advances) - LETTER_GAP  # 最后一个字不加尾部间距
        return advances, total

    size = BASE_SIZE
    advances, total_w = measure_line(size)
    max_w = W * 0.92
    if total_w > max_w:
        size = max(92, int(size * max_w / total_w))
        advances, total_w = measure_line(size)

    BASE_Y = int(H * 0.79)
    # 行左起点让整行水平居中
    x_start = (W - total_w) / 2.0

    # 非空格字形的位置索引(连续计数,不含空格),用于姿态哈希
    n_glyph = max(1, sum(1 for ch, _ in tokens if ch != " ") - 1)
    glyph_idx = 0
    x_cur = x_start
    for tok_i, (ch, lt) in enumerate(tokens):
        adv = advances[tok_i]
        # 空格只推进光标
        if ch == " ":
            x_cur += adv + LETTER_GAP
            continue

        rot, d_y, sc = _glyph_posture(ch, glyph_idx, glyph_idx / n_glyph)
        d_y *= size
        glyph_idx += 1
        x_here, x_cur = x_cur, x_cur + adv
        if lt is None or lt > t + 0.02:      # 还没唱到:占位,不画
            continue

        # 入场:字从下方 0.26 字高处**落笔**,同时把多歪的 7° 收回到本位、渐显。
        # 三项一起收才读作"写上去的";只做位移是字幕淡入,只做旋转是贴纸。
        k = _clamp((t - lt) / 0.15)
        a = ease("ease_out_quart", k)
        rise = (1 - a) * size * 0.26
        rot += (1 - a) * 7.0

        gf = font(max(24, int(size * sc)))
        bb = gf.getbbox(ch)
        gw, gh = bb[2] - bb[0], bb[3] - bb[1]
        cx = x_here + (bb[2] - bb[0] + LETTER_GAP) / 2
        cy = BASE_Y + d_y + rise

        # scan-bar 规则先于 tile 构建,避免事后改 tile 数组破坏描边色
        col: tuple[int, ...] = ink
        if version == "a" and scan_y is not None and cy / H < scan_y:
            col = tuple(int(c * 0.42 + A_SHADOW[j] * 0.58) for j, c in enumerate(ink))

        # 在独立 tile 上渲染字形(先描边后填色),再整体旋转
        # 描边宽度跟着字号走 —— 写死 4px 是按 106 号字调的,放大到 152 号后
        # 轮廓相对变细,字在乱底子上又开始糊边。
        ow = max(3, round(size * 0.038))
        tile = Image.new("RGBA", (gw + ow * 10, gh + ow * 10), (0, 0, 0, 0))
        td = ImageDraw.Draw(tile)
        tx, ty = tile.size[0] // 2, tile.size[1] // 2

        # 描边:落影 + 8 方向轮廓
        td.text((tx + round(ow * 1.7), ty + round(ow * 2.0)), ch,
                font=gf, fill=(*edge, 255), anchor="mm")
        for ox, oy in ((-ow, 0), (ow, 0), (0, -ow), (0, ow),
                       (-ow * 3 // 4, -ow * 3 // 4), (ow * 3 // 4, ow * 3 // 4),
                       (-ow * 3 // 4, ow * 3 // 4), (ow * 3 // 4, -ow * 3 // 4)):
            td.text((tx + ox, ty + oy), ch, font=gf, fill=(*edge, 255), anchor="mm")
        td.text((tx, ty), ch, font=gf, fill=(*col, 255), anchor="mm")

        # 渐显作用在**整块 tile** 上。只淡入填色会让入场那几帧只剩描边 ——
        # B 版描边是近白,白纸上等于这个字凭空缺了一块。
        if a < 1.0:
            tile.putalpha(tile.getchannel("A").point(lambda v: int(v * a)))

        rotated = tile.rotate(-rot, resample=Image.BICUBIC, expand=True)
        im.paste(rotated, (int(cx - rotated.width / 2), int(cy - rotated.height / 2)),
                 rotated)


# ————————————————— 世界布局 · A —————————————————
A_PLATEN = (-1400.0, -900.0, 2800.0, 1800.0)
A_CHASSIS = (-1780.0, -1240.0, 3560.0, 2480.0)
FACE = (0.22, 0.015, 0.84, 0.30)
EYE = (0.34, 0.055, 0.68, 0.165)


def _bed(*extra: Item) -> tuple:
    # 台板与玻璃也是暗箱的一部分:从机器**里面**往外看,玻璃底下没有光源,
    # 只有那道扫过去的灯管。此前这两层是 A_BASE_OLD/A_MAIN 的奶白大板,
    # 立绘压在上面等于白纸贴白墙,人物边缘全糊在底板里。
    return (tex_item("chassis_plastic", A_CHASSIS, A_SHADOW, 0.8),
            tex_item("glass_platen", A_PLATEN, A_DARK, 0.7), *extra)


def _ink(name: str, t: float, off: float = 0.58) -> float:
    """唱的人上墨(去饱和 0.16),没唱的退灰。四张脸同框的镜与双人镜共用这一条规则 ——
    A08 此前是写死的 0.55/0.34,于是正在唱的 Cy 反而比没唱的诺兰更灰,
    「谁在唱谁就活」这条规则在段界那一镜断了。"""
    return 0.16 if name in singing(t) else off


def _four(t: float, k: float, crop=FACE, h: float = 760.0) -> tuple:
    """四张脸一层压一层 —— 边缘对不齐才看得出是一沓。唱的人上墨,没唱的退灰。"""
    names = ("cy", "诺兰", "轩珩", "中里毅2")
    out = []
    for i, n in enumerate(names):
        dy = -560 + i * 380 + k * 40 * i
        out.append(doll_item(n, h, ((i - 1.5) * 96, dy), crop,
                             grey=_ink(n, t, 0.58 + 0.06 * i)))
    return tuple(out)


def _grid_four(t: float, h: float = 900.0) -> tuple:
    """四宫格 · 同一道光切开四个人 —— 灰度同样跟着 V3 的 cast 走。"""
    return tuple(
        doll_item(n, h, ((i % 2 - 0.5) * 1180, (i // 2 - 0.5) * 800), FACE,
                  grey=_ink(n, t, 0.60))
        for i, n in enumerate(("cy", "诺兰", "轩珩", "中里毅2")))



A_SHOTS = [
    # A 版的明度结构:**暗箱 + 一道光**。此前整版底色是 A_MAIN(#F4F2EC)——
    # 奶白墙 + 奶白机器 + 去饱和的立绘,全片挤在明度最高的 15% 里,画面没有一个暗锚点,
    # 于是每一镜都"看得见但不响"。可扫描仪工作时本来就是**盖着盖子的暗箱**,
    # 里头唯一的光就是那道扫过去的灯管 —— 照实景做,对比自己就回来了:
    # 底色压到 A_DARK/A_SHADOW,立绘和 scan 光条成为画面里仅有的亮部。
    MShot("A01", 22.465, 23.394,
          Cam("大特写", size1="特写", dy=0.27, e0=-34.0, e1=-22.0, ease="linear"),
          lambda t, k: (Item(("prop", "scanner_body"), (-1780, -2380, 3560, 2390)),),
          bg=("grey_plaster_4k", A_DARK, 0.55, 2600.0),
          fx={"scan": (0.98, 0.86, 0.62, 0.62), "band": (46.0, 0.05, 30.0)},
          note="仰拍进场 · 机器高得像一栋楼 —— 分镜写的「极端全景」按 0.05 占比渲出来是"
               "一枚邮票,读不出压迫感;以「看到什么」为准改成主体压满画幅、上沿切边"),

    MShot("A02", 23.394, 24.323,
          Cam("大特写", zoom=1.22, dx=0.16, ease="ease_out_quad"),
          lambda t, k: (*_bed(doll_item("cy", 2600, crop=EYE, scan_split=True)),
                        tex_item("glass_dust", (-620, -420, 1240, 840),
                                 A_SHADOW, 2.4, keying="dark")),
          subject=(2,), bg=("glass_platen", A_SHADOW, 0.62, 1400.0),
          fx={"scan": (0.86, 0.62, 0.66, 0.66), "band": (60.0, 0.06, 40.0)},
          note="与 A01 尺寸差 90× —— 原设计是「同一粒灰尘」,但灰尘在 A01 里根本没被看见过,"
               "跳过来只是一块认不出的金属板;换成她的眼睛,尺寸差照旧而且看得懂,"
               "灰尘降为压在玻璃上的脏(它本来就该是脏,不是主角)"),

    MShot("A03", 24.323, 24.799,
          Cam("特写", dx=0.32, ease="ease_in_out_expo"),
          lambda t, k: _bed(doll_item("cy", 1500, crop=FACE, scan_split=True)),
          subject=(2,), bg=("grey_plaster_4k", A_DARK, 0.55, 2600.0),
          fx={"scan": (0.62, 0.54, 0.66, 0.66), "band": (52.0, 0.05, 30.0),
              "blur": (2, 34)},
          note="甩 · 本段唯一快动作"),

    MShot("A04", 24.799, 25.252,
          Cam("特写", zoom=1.06, dx=0.21, r1=14.0, ease="ease_in_sine"),
          lambda t, k: _bed(doll_item("cy", 1620, scan_split=True)),
          subject=(2,), bg=("grey_plaster_4k", A_DARK, 0.55, 2600.0),
          fx={"scan": (0.54, 0.46, 0.66, 0.66), "band": (52.0, 0.06, 30.0),
              "flash": ("black", 0.067, 0.92)},
          note="正俯 + 旋转 · 黑闪入(电已经不稳了)"),

    MShot("A05", 25.252, 25.728,
          Cam("近景", zoom=1.075, dx=0.24, r0=-9.0, r1=4.0, e0=90.0, e1=68.0,
              ease="ease_out_cubic"),
          lambda t, k: _bed(doll_item("cy", 2050, crop=FACE, scan_split=True)),
          subject=(2,), bg=("glass_platen", A_SHADOW, 0.62, 1400.0),
          fx={"scan": (0.46, 0.38, 0.70, 0.70), "band": (44.0, 0.05, 30.0)},
          note="环绕 · 嘴那半活的,眼睛那半死的"),

    MShot("A06", 25.728, 26.204,
          Cam("特写", size1="大特写", dx=0.20, e0=68.0, e1=84.0, ease="ease_out_expo"),
          lambda t, k: _bed(doll_item("cy", 2150, crop=EYE, scan_split=True)),
          subject=(2,), bg=("glass_platen", A_SHADOW, 0.62, 1400.0),
          fx={"scan": (0.38, 0.355, 0.70, 0.55, 0.53), "band": (40.0, 0.07, 22.0)},
          note="光条比镜头先停 0.22s · 唯一不挂转场的切"),

    MShot("A07", 26.204, 26.668,
          Cam("大特写", size1="中景", dx=0.26, e0=84.0, e1=90.0, ease="ease_out_quart"),
          lambda t, k: _bed(doll_item("cy", 2150, crop=FACE, scan_split=True)),
          subject=(2,), bg=("glass_platen", A_SHADOW, 0.62, 1400.0),
          fx={"scan": (0.355, 0.355, 0.55, 0.34), "band": (36.0, 0.09, 14.0),
              "dark": (0.62, 0.20)},
          note="⭐ 空拍 · 明度事件 4 · 唯一一次镜头往后退"),

    MShot("A08", 26.668, 27.609,
          Cam("特写", e0=78.0, e1=59.0, ease="ease_out_sine"),
          lambda t, k: _bed(
              doll_item("cy", 1420, (-W * 0.21 * k, -120), FACE, grey=_ink("cy", t)),
              doll_item("诺兰", 1020 + 400 * k, (W * 0.24 * k, 210), FACE,
                        grey=_ink("诺兰", t))),
          subject=(2, 3), bg=("glass_platen", A_SHADOW, 0.7, 1400.0),
          fx={"scan": (0.355, 0.355, 0.50, 0.52), "band": (36.0, 0.09, 14.0),
              "dark": (0.34, 0.46)},
          note="段界 · 相对位移 45% 画宽(全段最大)· 本镜不是 4 次明度事件之一,"
               "dark 只是环境;压到 A07 那个深度会让全段最大的一次位移发生在看不见的地方。"
               "景别取特写不取近景:两张脸边分开边被相机拉远时,暗台板越占越大,"
               "全段最大的一次位移反而发生在一片黑里 —— 顶到特写,人脸撑住画面,"
               "分离才读得出是「被扯开」。光条同理回到基准 0.50,"
               "它是这个暗箱里唯一的光,非事件镜不该比事件镜还弱"),

    MShot("A09", 27.609, 28.514,
          Cam("大特写", dx=0.38, e0=30.0, e1=24.0, ease="linear"),
          lambda t, k: _bed(*_four(t, k),
                            tex_item("glass_platen", (-1420, -80, 2840, 150),
                                     A_GLASS, 1.3, opacity=0.85)),
          subject=(2, 3, 4, 5), bg=("chassis_plastic", A_DARK, 0.62, 2000.0),
          fx={"scan": (0.355, 0.355, 0.36, 0.36), "band": (36.0, 0.08, 14.0),
              "dark": (0.30, 0.34)},
          note="唯一匀速镜 · 玻璃绿边拉到全片最大 7% · 本镜起唱的是诺兰+Cy,这两张上墨"),

    MShot("A10", 28.514, 29.013,
          Cam("大特写", e0=24.0, e1=90.0, ease="ease_out_back", back=0.06, snap=0.28),
          lambda t, k: _bed(*_grid_four(t)),
          subject=(2, 3, 4, 5), bg=("chassis_plastic", A_DARK, 0.62, 2000.0),
          fx={"scan": (0.355, 0.355, 0.36, 0.40), "band": (36.0, 0.07, 14.0),
              "dark": (0.34, 0.42)},
          note="90° 翻面 4 帧 · 同一道光切开四个人的眼睛"),

    MShot("A11", 29.013, 29.780,
          Cam("大特写", size1="中景", dy=0.29, e0=90.0, e1=72.0,
              ease="ease_in_out_cubic"),
          lambda t, k: _bed(*_grid_four(t)),
          subject=(0,), bg=("grey_plaster_4k", A_DARK, 0.55, 2600.0),
          fx={"scan": (0.355, 0.355, 0.40, 0.46), "band": (30.0, 0.05, 14.0),
              "dark": (0.42, 1.0), "leak": (0.0, 0.40)},
          note="升镜出场 · 暗场被日光顶开 · 与 A01 一对(最低进,最高出)"),
]


# ————————————————— 世界布局 · B —————————————————
# 一块板宽 900 世界单位 ≈ 印张宽的 3/10 —— 木纹要能当尺子(B04),就得是**板**的尺度,
# 不是一整张木纹照片糊满画面的尺度。
#
# 桌面色取 B_DROP(#A08A6B)不取 B_WOOD(#D9C7A8):tint() 把声明色当作这块面的**中位明度**,
# 用 B_WOOD 时桌面中位 L≈200,而纸是 B_PAPER L≈242 —— 全画面挤在明度最高的 20% 里,
# 纸和桌子只差一点点,「一张纸」于是读不出轮廓,只读得出一片暖色。桌面 40–60% 占幅,
# 这一片暖色就是整版 B。压到 L≈143 之后纸是画面里唯一的亮部,折痕的亮线才有东西可对比。
B_BG = ("old_wood_floor_4k", B_DROP, 0.72, 900.0)


def _grid_item(k: float = 0.0) -> Item:
    return Item(("paper", 0, "grid"), (-PAPER_W / 2, -PAPER_H / 2, PAPER_W, PAPER_H))


B_SHOTS = [
    MShot("B01", 22.465, 23.394,
          Cam("特写", dx=0.23, e0=90.0, e1=68.0, ease="ease_out_quart", hold_size=True),
          lambda t, k: (paper_item(t),), bg=B_BG,
          note="折 1–4 · 每折面积 -50% —— 相机不跟,纸从压满画幅缩到五分之一"),

    MShot("B02", 23.394, 24.323,
          Cam("特写", zoom=1.44, dx=0.25, e0=40.0, e1=6.0, ease="ease_in_out_quad"),
          lambda t, k: (paper_item(t),), bg=B_BG,
          note="折 5–8 · 相机降到桌面高度 · 单层纸边 3px→40px —— 本镜起相机**跟**:"
               "hold_size 从 B01 一路挂到 B04 会累乘,折到第 12 折纸只剩一条白丝浮在木地板上,"
               "「对折」看不见了。缩得看得见是 B01 一镜的活,之后由叠层厚度和折痕密度接着讲"),

    MShot("B03", 24.323, 24.799,
          Cam("特写", zoom=0.91, dx=0.34, r0=0.0, r1=86.0, e0=30.0, e1=52.0,
              ease="ease_in_out_sine"),
          lambda t, k: (paper_item(t),), bg=B_BG,
          note="环绕 86° · 折不动:压下去弹回来,第二下才压死"),

    MShot("B04", 24.799, 25.252,
          Cam("近景", zoom=0.61, dx=0.37, e0=52.0, e1=70.0, ease="ease_in_out_expo"),
          lambda t, k: (paper_item(t),), bg=B_BG,
          fx={"blur": (2, 40)},
          note="甩 · 用木纹当尺子"),

    MShot("B05", 25.252, 25.960,
          Cam("中景", size1="近景", dx=0.21, e0=70.0, e1=58.0,
              ease="ease_out_back", back=0.12),
          lambda t, k: (paper_item(t),), bg=B_BG,
          note="折 13–16 · 物理面积 -94% 而占比维持(本镜相机反而追下去)· 逐折跳变 ≥18%"),

    MShot("B06", 25.960, 26.668,
          Cam("中景", size1="近景", dx=0.28, e0=58.0, e1=84.0,
              ease="ease_out_back", back=0.34, delay=0.345),
          lambda t, k: (paper_item(
              t, "grid", n=0 if t < 26.204 else
              max(0, round(16 * (1 - ease("ease_out_back",
                                          (t - 26.204) / 0.464, 0.34))))) if t >= 26.204
              else paper_item(t, "cy", n=16),),
          bg=B_BG,
          fx={"white": (0.34, 0.52, 0.88)},
          note="⭐ 空拍 · 死寂 0.244s 完全静止,然后弹开 · 弹开的不是原来那张画"),

    MShot("B07", 26.668, 27.609,
          Cam("中景", zoom=1.22, dx=0.44, dy=0.19, e0=84.0, e1=90.0,
              ease="ease_in_out_cubic"),
          lambda t, k: (_grid_item(k),), bg=B_BG,
          note="段界 · 斜向摇 · 16 条折痕全可见"),

    MShot("B08", 27.609, 28.514,
          Cam("特写", dx=0.39, e0=90.0, e1=74.0, ease="linear"),
          lambda t, k: (_grid_item(k),), bg=B_BG,
          note="本段唯一匀速镜 · 透光"),

    MShot("B09", 28.514, 29.013,
          Cam("中景", zoom=1.105, dx=0.30, r0=0.0, r1=118.0, e0=74.0, e1=88.0,
              ease="ease_out_back", back=0.05, snap=0.32),
          lambda t, k: (_grid_item(k),), bg=B_BG,
          note="旋转甩入 118°"),

    MShot("B10", 29.013, 29.780,
          Cam("近景", size1="全景", dy=0.27, e0=88.0, e1=66.0,
              ease="ease_in_out_cubic"),
          lambda t, k: (_grid_item(k),), bg=B_BG,
          fx={"leak": (0.0, 0.34)},
          note="升镜出场 · 画面上沿 6% 由窗光占走 · 与 A11 同拍反向呼应"),
]


# ————————————————— 渲染 —————————————————
def render_frame(t: float, shots: list, version: str) -> tuple[Image.Image, tuple | None]:
    sh = active(shots, t)
    k = sh.k(t)
    s0, s1, look = shot_scales(sh)
    s = s0 * (s1 / s0) ** sh.cam.scale_progress(k)
    cx, cy, r, elev = sh.cam.at(k, s)
    v = View(cx + look[0], cy + look[1], s, r)

    scan_y = None
    if "scan" in sh.fx:
        y0, y1 = sh.fx["scan"][0], sh.fx["scan"][1]
        hold = sh.fx["scan"][4] if len(sh.fx["scan"]) > 4 else 1.0
        e = sh.cam.progress(k)
        scan_y = _lerp((y0, y1), min(e / hold, 1.0) if hold < 1 else e)

    canvas = Image.new("RGBA", (PAD_W, PAD_H), (*A_DARK, 255))
    if sh.bg:
        base = Image.new("RGB", (PAD_W, PAD_H))
        tiled(base, sh.bg[0], sh.bg[1], sh.bg[2], sh.bg[3], v)
        canvas.paste(base, (0, 0))
    mask = Image.new("L", (PAD_W, PAD_H), 0)

    items = sh.items(t, k)
    for i, it in enumerate(items):
        place(canvas, it, v, mask if i in sh.subject else None, scan_y)

    frame = tilt(canvas.convert("RGB"), elev)
    bb = tilt(mask, elev).getbbox()

    arr = fx_pass(np.asarray(frame, dtype=float), sh, t, k)
    im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    draw_lyrics(im, t, version, scan_y)
    return im, bb


_WORKER: dict = {}


def _init_worker(version: str) -> None:
    """spawn 出来的子进程什么都没有:路径要重设,纹理/印张缓存各建各的。

    用 spawn 不用 fork:macOS 的 Accelerate(numpy 底层)在 fork 后的子进程里
    调 BLAS 会挂,而本片每帧都在跑 numpy。代价是每个 worker 各建一份纹理缓存,
    分摊到每人几十帧上可以忽略。
    """
    pe._PATHS = pe.PVPaths(assets_dir=ASSETS, wav=WAV, out_dir=OUT, slug="mingyue")
    _mvsession.configure(ASSETS, TEX, GEN)   # spawn 子进程不继承父进程模块级状态
    _WORKER["version"] = version
    _WORKER["shots"] = A_SHOTS if version == "a" else B_SHOTS
    _WORKER["dir"] = OUT / version / "_frames"


def _render_one(i: int) -> tuple:
    t = SEG_T0 + i / FPS
    im, bb = render_frame(t, _WORKER["shots"], _WORKER["version"])
    im.save(_WORKER["dir"] / f"f{i:05d}.png")
    return i, round(t, 4), active(_WORKER["shots"], t).sid, bb


def render(version: str, make_video: bool = True, jobs: int = 1) -> int:
    shots = A_SHOTS if version == "a" else B_SHOTS
    out = OUT / version
    frames = out / "_frames"
    frames.mkdir(parents=True, exist_ok=True)

    n = round((SEG_T1 - SEG_T0) * FPS)
    rows: list[tuple] = []
    if jobs > 1:
        # imap_unordered 的返回顺序不是帧序,所以先收齐再按 i 排 —— motion.json 的
        # track 是逐帧时间序列,乱序会让 gate_check_motion 把相邻帧当成跳变。
        ctx = mp.get_context("spawn")
        with ctx.Pool(jobs, initializer=_init_worker, initargs=(version,)) as pool:
            for done, row in enumerate(
                    pool.imap_unordered(_render_one, range(n), chunksize=4), 1):
                rows.append(row)
                if done % 20 == 0:
                    log.info("[%s] %d/%d (%d 进程)", version, done, n, jobs)
        rows.sort()
    else:
        for i in range(n):
            t = SEG_T0 + i / FPS
            im, bb = render_frame(t, shots, version)
            im.save(frames / f"f{i:05d}.png")
            rows.append((i, round(t, 4), active(shots, t).sid, bb))
            if i % 20 == 0:
                log.info("[%s] %d/%d  %s", version, i, n, active(shots, t).sid)

    track = [{"t": t, "shot": sid,
              "bbox": [(bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2,
                       bb[2] - bb[0], bb[3] - bb[1]]}
             for _i, t, sid, bb in rows if bb]
    (out / "motion.json").write_text(json.dumps(
        {"fps": FPS, "w": W, "h": H, "start": SEG_T0, "end": SEG_T1, "track": track},
        ensure_ascii=False))
    log.info("[%s] %d 帧 · motion.json %d 条", version, n, len(track))

    if not make_video:
        return 0
    mp4 = out / f"mingyue_sample_{version}.mp4"
    cmd = [pe.FFMPEG, "-y", "-framerate", str(FPS), "-i", str(frames / "f%05d.png"),
           "-ss", str(SEG_T0), "-t", str(SEG_T1 - SEG_T0), "-i", str(WAV),
           "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-pix_fmt", "yuv420p",
           "-crf", "17", "-preset", "slow", "-c:a", "aac", "-b:a", "192k",
           "-shortest", str(mp4)]
    subprocess.run(cmd, check=True, capture_output=True)
    log.info("[%s] → %s (%d KB)", version, mp4, mp4.stat().st_size // 1024)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="《明月天涯》22.465–29.780s 样段渲染")
    ap.add_argument("--version", nargs="*", default=["a", "b"], choices=["a", "b"])
    ap.add_argument("--no-video", action="store_true")
    # 默认 4 不是 8:机器 8 核但只有 8 GB 内存,单个渲染进程实测约 1.3 GB
    # (每帧画布 3840×1836 的 float RGB 就是 169 MB),开满核会换页,比串行还慢。
    ap.add_argument("--jobs", type=int, default=4, help="并行渲染进程数")
    args = ap.parse_args()

    pe._PATHS = pe.PVPaths(assets_dir=ASSETS, wav=WAV, out_dir=OUT, slug="mingyue")
    OUT.mkdir(parents=True, exist_ok=True)
    for v in args.version:
        render(v, make_video=not args.no_video, jobs=args.jobs)
    return 0


if __name__ == "__main__":
    sys.exit(main())
