"""解析式 bbox 预测器 —— 不渲染,直接算出主体包围盒轨迹。

`render_frame` 里产出 bbox 的那条链路是**纯几何**:

    shot_scales → Cam.at → View → quad_of/w2s → warp → tilt → mask.getbbox()

一个像素值都不参与。所以 bbox 可以在不渲染的情况下解析求出:把每个主体图层的
alpha **凸包**(不是外接矩形 —— 有滚转时角点 AABB 会高估几个百分点)沿同一条
链路映射过去,再取包围盒。

这把 R9 冻结门从「渲 3 分钟再看」变成「毫秒级预检」,也就是 Phase 2 求解器
能存在的前提。

本模块**不重写几何**,一律 import `mingyue_render` 里那份 —— 重写就会漂移。
Phase 1 拆包后把 import 指向 `mv_engine` 即可。
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Iterable, NamedTuple, Sequence

import numpy as np
from PIL import Image

Pt = tuple[float, float]
Poly = list[Pt]


# ————————————————— 凸包 —————————————————

def _monotone_chain(pts: Sequence[Pt]) -> Poly:
    """Andrew 单调链 —— 逆时针凸包。不引 scipy,省一个依赖。"""
    p = sorted(set(pts))
    if len(p) <= 2:
        return list(p)

    def half(seq: Sequence[Pt]) -> Poly:
        out: Poly = []
        for q in seq:
            while len(out) >= 2:
                (ax, ay), (bx, by) = out[-2], out[-1]
                if (bx - ax) * (q[1] - ay) - (by - ay) * (q[0] - ax) > 0:
                    break
                out.pop()
            out.append(q)
        return out

    return half(p)[:-1] + half(p[::-1])[:-1]


# `place()` 写 mask 走的是 `mask.paste(alpha, pos, alpha)` —— 拿 alpha 当自己的
# 蒙版贴,等于 alpha²/255(带舍入)。实测 alpha < 12 会被压成 0,所以 mask 的有效
# 支撑集比图层 alpha 的支撑集**内缩**一圈。
#
# 对硬边图层(B 的纸)几乎没区别,但 doll 经过 `_feather` 后边缘有 10% 宽的渐隐带,
# 这一圈内缩在画面上是几十像素 —— 按 >0 取包围盒会系统性预测得更宽。
MASK_ALPHA_MIN = 12


# `place()` 写 mask 走的是 `mask.paste(alpha, pos, alpha)` —— 拿 alpha 当自己的
# 蒙版贴,等于 alpha²/255(带舍入)。实测 alpha < 12 会被压成 0,所以 mask 的有效
# 支撑集比图层 alpha 的支撑集**内缩**一圈。
#
# 对硬边图层(B 的纸)几乎没区别,但 doll 经过 `_feather` 后边缘有 10% 宽的渐隐带,
# 这一圈内缩在画面上是几十像素 —— 按 >0 取包围盒会系统性预测得更宽。
MASK_ALPHA_MIN = 12

# 分带数。**一整张的凸包不够用**:人物剪影横向极不凸(头 → 肩之间是斜的),
# 当画幅只框住头部时,整张凸包在头那几行给出的是「朝肩宽插值过去」的宽度,
# 比真实的头宽出几十像素。实测 A 版 w_p95 因此差 48px,而 B 版(纸,近似凸)只差 3px。
# 按源图行分带、逐带取凸包,把这个高估限制在带内。
BANDS = 64


class Hull(NamedTuple):
    """逐带凸包。`pts` 是拼接后的全部顶点,`starts` 是每带的切片边界。

    拼成一个数组是为了让 w2s / tilt 一次向量化算完;裁剪才需要按带拆开
    —— 裁剪必须逐个凸多边形做,拼在一起裁会把不同带的顶点连成一个假多边形。
    """

    pts: np.ndarray      # (N, 2) 归一化到 [0,1]²
    starts: np.ndarray   # (B+1,) 索引


def banded_hull(im: Image.Image, bands: int = BANDS) -> Hull:
    """图层 alpha 的逐带凸包,归一化到 [0,1]²。

    凸包顶点必然是所在行的最左/最右像素,所以只需逐行取两端 —— O(H) 个候选点
    而不是 O(W·H)。
    """
    a = np.asarray(im.getchannel("A"))
    h, w = a.shape
    nz = a >= MASK_ALPHA_MIN
    rows = np.flatnonzero(nz.any(axis=1))
    if rows.size == 0:
        return Hull(np.zeros((0, 2), dtype=float), np.asarray([0]))

    idx = np.arange(w)
    lo_col = np.empty(h, dtype=float)
    hi_col = np.empty(h, dtype=float)
    for y in rows:
        cols = idx[nz[y]]
        lo_col[y] = cols[0]
        hi_col[y] = cols[-1]

    edges = np.linspace(rows[0], rows[-1] + 1, bands + 1)
    chunks: list[np.ndarray] = []
    starts = [0]
    for bi in range(bands):
        ys = rows[(rows >= edges[bi]) & (rows < edges[bi + 1])]
        if ys.size == 0:
            starts.append(starts[-1])
            continue
        pts: list[Pt] = []
        for y in ys:
            lo, hi = lo_col[y], hi_col[y] + 1.0   # getbbox() 的 right/lower 是开区间
            pts.append((lo, float(y)))
            pts.append((hi, float(y)))
            pts.append((lo, float(y) + 1.0))
            pts.append((hi, float(y) + 1.0))
        hull = np.asarray(_monotone_chain(pts), dtype=float)
        chunks.append(hull)
        starts.append(starts[-1] + len(hull))

    pts_all = np.concatenate(chunks) / np.asarray([w, h], dtype=float)
    return Hull(pts_all, np.asarray(starts))


# ————————————————— 多边形裁剪 —————————————————

def clip_rect(poly: np.ndarray, x0: float, y0: float, x1: float, y1: float) -> np.ndarray:
    """Sutherland–Hodgman 把凸多边形裁到矩形内。

    不能先取 AABB 再裁 —— 一个大部分在画外、只有一角进画的主体,
    裁 AABB 会得到一个比真实包围盒宽得多的框。
    """
    def clip(pts: np.ndarray, keep, inter) -> np.ndarray:
        if len(pts) == 0:
            return pts
        out: list = []
        for i in range(len(pts)):
            cur, prv = pts[i], pts[i - 1]
            cin, pin = keep(cur), keep(prv)
            if cin:
                if not pin:
                    out.append(inter(prv, cur))
                out.append(cur)
            elif pin:
                out.append(inter(prv, cur))
        return np.asarray(out, dtype=float) if out else np.zeros((0, 2))

    def lerp(a, b, f):
        return a + (b - a) * f

    poly = clip(poly, lambda p: p[0] >= x0,
                lambda a, b: lerp(a, b, (x0 - a[0]) / (b[0] - a[0])))
    poly = clip(poly, lambda p: p[0] <= x1,
                lambda a, b: lerp(a, b, (x1 - a[0]) / (b[0] - a[0])))
    poly = clip(poly, lambda p: p[1] >= y0,
                lambda a, b: lerp(a, b, (y0 - a[1]) / (b[1] - a[1])))
    poly = clip(poly, lambda p: p[1] <= y1,
                lambda a, b: lerp(a, b, (y1 - a[1]) / (b[1] - a[1])))
    return poly


# ————————————————— 正向 tilt —————————————————

def tilt_forward(poly: np.ndarray, elev: float, mr) -> np.ndarray:
    """`mingyue_render.tilt` 的正向映射(平面画布 px → 画幅 px)。

    PIL 的 PERSPECTIVE 系数是**反向**映射(输出→输入),`tilt` 里解的就是那个方向。
    这里要输入→输出,所以把两个 quad 对调再解一次 —— 直接拿 `tilt` 的系数
    反着用会得到一个看似合理但完全错误的结果(不会报错,这是最难查的那种)。
    """
    if len(poly) == 0:
        return poly
    OX, OY, W, H = mr.OX, mr.OY, mr.W, mr.H
    if abs(elev) >= 89.5:
        return poly - np.asarray([OX, OY], dtype=float)

    k = mr._clamp(math.cos(math.radians(mr._clamp(elev, -89.0, 90.0))), 0.0, 1.0)
    dx, dy = W * 0.50 * k, H * 0.30 * k
    if elev >= 0:
        in_quad = [(OX - dx, OY - dy), (OX + W + dx, OY - dy),
                   (OX + W, OY + H), (OX, OY + H)]
    else:
        in_quad = [(OX, OY), (OX + W, OY),
                   (OX + W + dx, OY + H + dy), (OX - dx, OY + H + dy)]
    out_quad = [(0, 0), (W, 0), (W, H), (0, H)]

    a, b, c, d, e, f, g, h = mr.atoms.solve_perspective(in_quad, out_quad)
    x, y = poly[:, 0], poly[:, 1]
    den = g * x + h * y + 1.0
    den = np.where(np.abs(den) < 1e-9, 1e-9, den)
    return np.stack([(a * x + b * y + c) / den, (d * x + e * y + f) / den], axis=1)


# ————————————————— 单帧 bbox —————————————————

class Session:
    """逐带凸包缓存 —— 一个图层 key 只标定一次。"""

    def __init__(self, mr) -> None:
        self.mr = mr
        self._hull: dict[tuple, Hull] = {}
        _assert_w2s(mr)

    def hull_of(self, key: tuple) -> Hull:
        if key not in self._hull:
            self._hull[key] = banded_hull(self.mr.layer(key))
        return self._hull[key]


def _w2s_vec(pts: np.ndarray, v, mr) -> np.ndarray:
    """`mingyue_render.w2s` 的向量化版本(相似变换:旋转 + 缩放 + 平移)。

    这是本模块唯一一处重写了 `mingyue_render` 的几何 —— 逐点调 `w2s` 在
    64 带 × 上千顶点下太慢。代价是可能漂移,所以 `Session` 构造时用
    `_assert_w2s` 拿真函数对一遍。
    """
    a = math.radians(v.r)
    ca, sa = math.cos(a), math.sin(a)
    d = pts - np.asarray([v.cx, v.cy], dtype=float)
    return np.stack([
        mr.OX + mr.W / 2 + v.s * (d[:, 0] * ca - d[:, 1] * sa),
        mr.OY + mr.H / 2 + v.s * (d[:, 0] * sa + d[:, 1] * ca),
    ], axis=1)


def _assert_w2s(mr) -> None:
    v = mr.View(137.0, -49.0, 0.83, 23.0)
    p = np.asarray([[0.0, 0.0], [911.0, -320.0], [-77.0, 640.5]])
    got = _w2s_vec(p, v, mr)
    want = np.asarray([mr.w2s(tuple(q), v.cx, v.cy, v.s, v.r) for q in p])
    if not np.allclose(got, want, atol=1e-9):
        raise AssertionError(f"_w2s_vec 与 mingyue_render.w2s 漂移了\n{got}\n{want}")


def _band_minmax(pts: np.ndarray, starts: np.ndarray
                 ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """每个非空带的 min/max,一次 reduceat 算完。

    逐带调 `p.min(axis=0)` 在 ~10 个点的小数组上全是 numpy 调用开销 ——
    实测 64 带 × 219 帧下这一项占 `_clip_bands` 的一大半。

    空带的 `starts[j] == starts[j+1]`,过滤掉之后剩下的起点严格递增,
    `reduceat` 的分段恰好就是各带。
    """
    live = np.flatnonzero(starts[:-1] != starts[1:])
    if live.size == 0:
        return live, np.zeros((0, 2)), np.zeros((0, 2))
    idx = starts[live]
    return live, np.minimum.reduceat(pts, idx, axis=0), np.maximum.reduceat(pts, idx, axis=0)


def _clip_bands(pts: np.ndarray, starts: np.ndarray,
                x0: float, y0: float, x1: float, y1: float
                ) -> tuple[np.ndarray, np.ndarray]:
    """逐带裁到矩形内。整带在内的原样带过,整带在外的丢掉,只有跨边的才真裁。

    必须逐带裁:把所有带拼成一个点集去裁,等于把不同带的顶点连成一个并不存在的
    多边形。
    """
    if len(pts) == 0:
        return pts, starts
    # 整体就在框内(远景常态)—— 一次判定,连分带都不用拆。
    g_mn, g_mx = pts.min(axis=0), pts.max(axis=0)
    if g_mn[0] >= x0 and g_mn[1] >= y0 and g_mx[0] <= x1 and g_mx[1] <= y1:
        return pts, starts

    live, mn, mx = _band_minmax(pts, starts)
    out: list[np.ndarray] = []
    idx = [0]
    for j, b in enumerate(live):
        if mx[j, 0] < x0 or mn[j, 0] > x1 or mx[j, 1] < y0 or mn[j, 1] > y1:
            continue
        p = pts[starts[b]:starts[b + 1]]
        if mn[j, 0] >= x0 and mn[j, 1] >= y0 and mx[j, 0] <= x1 and mx[j, 1] <= y1:
            keep = p
        else:
            keep = clip_rect(p, x0, y0, x1, y1)
            if len(keep) == 0:
                continue
        out.append(keep)
        idx.append(idx[-1] + len(keep))
    if not out:
        return np.zeros((0, 2)), np.asarray([0])
    return np.concatenate(out), np.asarray(idx)


def bbox_at(sh, t: float, session: Session) -> tuple[float, float, float, float] | None:
    """`render_frame` 返回的那个 bb,不渲染。返回 (l, u, r, b) 或 None。"""
    mr = session.mr
    k = sh.k(t)
    s0, s1, look = mr.shot_scales(sh)
    s = s0 * (s1 / s0) ** sh.cam.scale_progress(k)
    cx, cy, r, elev = sh.cam.at(k, s)
    v = mr.View(cx + look[0], cy + look[1], s, r)

    items = sh.items(t, k)
    lo = np.array([np.inf, np.inf])
    hi = np.array([-np.inf, -np.inf])
    for i, it in enumerate(items):
        if i not in sh.subject or it.opacity <= 0.0:
            continue
        hull = session.hull_of(it.key)
        if len(hull.pts) == 0:
            continue
        x, y, w, h = it.rect
        world = hull.pts * np.asarray([w, h]) + np.asarray([x, y])
        plane = _w2s_vec(world, v, mr)
        # warp 先按画布尺寸裁,tilt 才发生 —— 顺序反了会把画布外的部分错误带进画幅。
        plane, st = _clip_bands(plane, hull.starts, 0.0, 0.0,
                                float(mr.PAD_W), float(mr.PAD_H))
        if len(plane) == 0:
            continue
        scr = tilt_forward(plane, elev, mr)
        scr, _ = _clip_bands(scr, st, 0.0, 0.0, float(mr.W), float(mr.H))
        if len(scr) == 0:
            continue
        lo = np.minimum(lo, scr.min(axis=0))
        hi = np.maximum(hi, scr.max(axis=0))

    if not np.isfinite(lo).all():
        return None
    return float(lo[0]), float(lo[1]), float(hi[0]), float(hi[1])


def predict_track(shots: list, t0: float, t1: float, fps: int,
                  session: Session) -> dict:
    """直出 `motion.json` 的结构,供 gate_check_motion 直接吃。"""
    mr = session.mr
    n = round((t1 - t0) * fps)
    track = []
    for i in range(n):
        t = round(t0 + i / fps, 4)
        sh = mr.active(shots, t)
        bb = bbox_at(sh, t, session)
        if bb:
            track.append({"t": t, "shot": sh.sid,
                          "bbox": [(bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2,
                                   bb[2] - bb[0], bb[3] - bb[1]]})
    return {"fps": fps, "w": mr.W, "h": mr.H, "start": t0, "end": t1, "track": track}
