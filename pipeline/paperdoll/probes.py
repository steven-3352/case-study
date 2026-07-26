#!/usr/bin/env python3
"""原子探针库 —— 纸片人卡点 MV 阶段 ④ 的 L-原子 / L-镜 两级即时检查。

依据 `.agents/skills/paperdoll-mv-packaging/SKILL.md` §9.2 / §9.3 / §9.4。

**为什么存在**:阶段 ④ 的铁律是「原子产出即自检,检不过的原子不进装配」。
没有本模块,阶段 ④ 退化回「渲完整片再翻接触表」—— 那正是《明月天涯》连续
返工的直接原因(根因两条:判据是文字不是数、验收器建在渲染之后)。

三条纪律(§9.2,违反即判流程未跑):

1. **判据先于原子写** —— 本模块的 `check_*` 必须在原子实现之前落地。
2. **判据是数不是话** —— 每个 `check_*` 返回度量值,不返回形容词。
3. **探针在中性底上跑** —— `neutral_bed()` 不带任何风格包颜色、不带其他原子,
   测的是这个能力本身成不成立;混进底色就测不出是谁的问题。

**所有阈值都是地板不是目标**(§9.4)。每到「我觉得这个能过」的时刻,先问能不能
把验收目标提 3 档。**门全绿不等于成片可用** —— 原子级全过仍可能坏在原子与底色
的乘法关系上,那一级由 `shot_assay()` 抓。

约定:
- `arr` 一律是 float ndarray (H, W, 3),值域 0-255 —— 与 `mingyue_atoms` 同契约。
- bbox 一律是 `[cx, cy, w, h]`(像素)—— 与 `motion.json` / `gate_check_motion` 同契约。

CLI::

    python3 -m pipeline.paperdoll.probes selftest     # 拿真原子跑一遍全表(含反例)
    python3 -m pipeline.paperdoll.probes shot <帧目录> --track motion.json --shot A08 \
        --framing 特写 --declared "$(cat design/declared_palette_A.txt)"

退出码 0 = 全过,1 = 有 fail。
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib
import sys
from dataclasses import dataclass, field
from typing import Callable, Sequence

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

_REPO = pathlib.Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

# R9 冻结口径与色板 ΔE 数学都不在这里重造 —— 单一来源在两道门里
from pipeline.gate_check_motion import AREA_FRAC, DISP_FRAC  # noqa: E402
from pipeline.gate_check_palette import analyze_declared, parse_hex  # noqa: E402

RGB = tuple[int, int, int]

NEUTRAL_LEVEL = 128  # 中性中灰底:既不偏亮也不偏暗,原子往两边走都量得出
LYRIC_WINDOW_S = 0.15  # 歌词落笔的「同窗」窗口(§9.2)

# 景别 → 主体 bbox 面积 / 画幅面积。大特写 >1 表示主体溢出画幅(脸切边)。
FRAMING_SHARE = {
    "极端全景": 0.05, "全景": 0.13, "中景": 0.30,
    "近景": 0.48, "特写": 0.72, "大特写": 1.15,
}
FRAMING_TOLERANCE = 0.70  # 实测占幅 ≥ 声明 share 的 70%(§9.3)


# ————————————————— 结果类型 —————————————————

@dataclass(frozen=True)
class ProbeResult:
    """一条判据一个数。`floor` 是地板,不是目标(§9.4)。"""

    metric: str
    value: float
    floor: float
    ok: bool
    detail: str = ""
    unit: str = ""

    def __str__(self) -> str:
        mark = "PASS" if self.ok else "FAIL"
        d = f"  {self.detail}" if self.detail else ""
        return (f"  [{mark}] {self.metric} = {self.value:.4g}{self.unit} "
                f"(地板 {self.floor:.4g}{self.unit}){d}")


@dataclass(frozen=True)
class ProbeReport:
    """一个原子的完整体检。多判据原子(如歌词落笔三项同窗)全过才算过。"""

    atom: str
    results: tuple[ProbeResult, ...] = field(default_factory=tuple)
    note: str = ""

    @property
    def ok(self) -> bool:
        return all(r.ok for r in self.results) and bool(self.results)

    @property
    def failures(self) -> tuple[ProbeResult, ...]:
        return tuple(r for r in self.results if not r.ok)

    def __str__(self) -> str:
        head = f"{'PASS' if self.ok else 'FAIL'} · {self.atom}"
        if self.note:
            head += f"  — {self.note}"
        return "\n".join([head, *(str(r) for r in self.results)])


def _r(metric: str, value: float, floor: float, *, ceil: bool = False,
       detail: str = "", unit: str = "") -> ProbeResult:
    """ceil=True 时判据是「不得超过」,否则是「不得低于」。"""
    ok = value <= floor if ceil else value >= floor
    return ProbeResult(metric, float(value), float(floor), bool(ok), detail, unit)


# ————————————————— 中性底与标准立绘 —————————————————

def neutral_bed(w: int = 960, h: int = 540, level: int = NEUTRAL_LEVEL) -> np.ndarray:
    """纯中灰底。**不带任何风格包颜色** —— 探针要测的是原子本身。"""
    return np.full((h, w, 3), float(level), dtype=float)


def neutral_canvas(w: int = 960, h: int = 540, level: int = NEUTRAL_LEVEL) -> Image.Image:
    """给就地画在 RGBA 上的原子(crease / stack_edge)用的中性画布。"""
    return Image.new("RGBA", (w, h), (level, level, level, 255))


def standard_subject(bed: np.ndarray, *, height_frac: float = 0.62,
                     center: tuple[float, float] | None = None,
                     ink: RGB = (38, 34, 30)) -> np.ndarray:
    """在中性底上贴一张**标准立绘替身**(头 + 身,非对称肩线)。

    故意不用项目里的真立绘:探针要跨片复用,绑死素材就成了那一部片的测试。
    非对称是有意的 —— 左右对称的剪影量不出 roll,四角也退化。
    """
    h, w = bed.shape[:2]
    cx, cy = center or (w * 0.5, h * 0.5)
    sh = height_frac * h
    im = Image.fromarray(bed.astype(np.uint8))
    d = ImageDraw.Draw(im)
    head_r = sh * 0.16
    hy = cy - sh * 0.32
    d.ellipse([cx - head_r, hy - head_r, cx + head_r, hy + head_r], fill=ink)
    d.polygon([(cx - sh * 0.24, cy + sh * 0.5), (cx - sh * 0.15, hy + head_r * 0.6),
               (cx + sh * 0.19, hy + head_r * 0.8), (cx + sh * 0.30, cy + sh * 0.5)],
              fill=ink)
    return np.asarray(im, dtype=float)


def probe(atom_fn: Callable[..., np.ndarray],
          criterion: Callable[[np.ndarray, np.ndarray], ProbeReport],
          *, size: tuple[int, int] = (960, 540), level: int = NEUTRAL_LEVEL,
          subject: bool = False, **kw) -> ProbeReport:
    """在中性底上单渲一个原子并立刻判据。

    `atom_fn(arr, **kw) -> arr`(`mingyue_atoms` 契约:不就地修改)。
    `criterion(before, after) -> ProbeReport`。
    """
    bed = neutral_bed(*size, level=level)
    if subject:
        bed = standard_subject(bed)
    after = np.asarray(atom_fn(bed, **kw), dtype=float)
    return criterion(bed, after)


def probe_canvas(atom_fn: Callable[..., None],
                 criterion: Callable[[np.ndarray, np.ndarray], ProbeReport],
                 *, size: tuple[int, int] = (960, 540),
                 level: int = NEUTRAL_LEVEL, **kw) -> ProbeReport:
    """同 `probe()`,给就地画在 RGBA canvas 上的原子用(crease / stack_edge)。"""
    canvas = neutral_canvas(*size, level=level)
    before = np.asarray(canvas.convert("RGB"), dtype=float)
    atom_fn(canvas, **kw)
    return criterion(before, np.asarray(canvas.convert("RGB"), dtype=float))


# ————————————————— 基础度量 —————————————————

def luma(arr: np.ndarray) -> np.ndarray:
    """Rec.709 亮度 (H, W) float 0-255。"""
    a = np.asarray(arr, dtype=float)
    return a[..., 0] * 0.2126 + a[..., 1] * 0.7152 + a[..., 2] * 0.0722


def diff_mask(before: np.ndarray, after: np.ndarray, tol: float = 6.0) -> np.ndarray:
    """原子改动了哪些像素。比「按颜色抠」稳:不假设原子往哪个方向改。"""
    return np.abs(luma(after) - luma(before)) > tol


def bbox_of(mask: np.ndarray) -> tuple[float, float, float, float] | None:
    """(cx, cy, w, h) —— 与 motion.json 同契约。空 mask 返回 None。"""
    ys, xs = np.nonzero(mask)
    if xs.size == 0:
        return None
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    return ((x0 + x1) / 2.0, (y0 + y1) / 2.0, float(x1 - x0 + 1), float(y1 - y0 + 1))


def edge_profile(lum: np.ndarray, axis: int = 0) -> tuple[float, int, int]:
    """沿 axis 求最陡边缘。返回 (最大梯度 L/px, 过渡带宽 px, 位置)。

    axis=0 量竖直方向变化(横向光条),axis=1 量水平方向(竖向光条)。
    过渡带宽 = 最陡处附近同号且 ≥10% 峰值梯度的连续段长度 —— 硬边是 1-2px,
    羽化过的会拖到几十上百 px,这正是「软过渡 >120px 判 fail」要抓的。
    """
    prof = lum.mean(axis=1 - axis)
    g = np.diff(prof)
    if g.size == 0:
        return 0.0, 0, 0
    i = int(np.argmax(np.abs(g)))
    peak = float(abs(g[i]))
    if peak <= 0:
        return 0.0, 0, i
    sign = np.sign(g[i])
    lo = hi = i
    thr = 0.10 * peak
    while lo > 0 and np.sign(g[lo - 1]) == sign and abs(g[lo - 1]) >= thr:
        lo -= 1
    while hi < g.size - 1 and np.sign(g[hi + 1]) == sign and abs(g[hi + 1]) >= thr:
        hi += 1
    return peak, int(hi - lo + 1), i


def mask_corners(mask: np.ndarray) -> np.ndarray | None:
    """轮廓四角 (4, 2) —— 取四个对角方向上的极值点,顺序稳定。"""
    ys, xs = np.nonzero(mask)
    if xs.size == 0:
        return None
    p = np.stack([xs, ys], axis=1).astype(float)
    s, d = p[:, 0] + p[:, 1], p[:, 0] - p[:, 1]
    return np.stack([p[np.argmin(s)], p[np.argmax(d)],
                     p[np.argmax(s)], p[np.argmin(d)]])


def similarity_residual(c0: np.ndarray, c1: np.ndarray) -> float:
    """扣掉平移+旋转+等比缩放之后,四角还剩多少位移(px)。

    **这是「pitch 到底生效没有」的唯一诚实问法**:纯推拉也会让四角动,
    不扣掉相似变换就会把一次 zoom 判成仰拍。剩下的残差才是透视形变。
    """
    a, b = np.asarray(c0, float), np.asarray(c1, float)
    ac, bc = a - a.mean(0), b - b.mean(0)
    denom = float((ac ** 2).sum())
    if denom <= 0:
        return 0.0
    u, sv, vt = np.linalg.svd(ac.T @ bc)
    r = vt.T @ np.diag([1.0, np.sign(np.linalg.det(vt.T @ u.T))]) @ u.T
    s = float(sv.sum()) / denom
    return float(np.linalg.norm(bc - s * (ac @ r.T), axis=1).max())


def autocorr_peak(lum: np.ndarray, exclude_radius: int = 3) -> float:
    """归一化自相关的**次峰**。噪声 → 低;规则栅格/重复贴图 → 高。"""
    f = lum - lum.mean()
    if not np.any(f):
        return 1.0
    power = np.abs(np.fft.fft2(f)) ** 2
    ac = np.fft.fftshift(np.fft.ifft2(power).real)
    ac /= ac.max()
    cy, cx = np.array(ac.shape) // 2
    yy, xx = np.ogrid[:ac.shape[0], :ac.shape[1]]
    ac[(yy - cy) ** 2 + (xx - cx) ** 2 <= exclude_radius ** 2] = -1.0
    return float(ac.max())


def alpha_moments(alpha: np.ndarray) -> tuple[float, float, float, float]:
    """(cx, cy, 主轴角度°, alpha 总量) —— 图像矩,给歌词落笔三项用。"""
    a = np.asarray(alpha, dtype=float)
    total = float(a.sum())
    if total <= 0:
        return 0.0, 0.0, 0.0, 0.0
    h, w = a.shape
    yy, xx = np.mgrid[:h, :w]
    cx, cy = float((a * xx).sum() / total), float((a * yy).sum() / total)
    mu20 = float((a * (xx - cx) ** 2).sum() / total)
    mu02 = float((a * (yy - cy) ** 2).sum() / total)
    mu11 = float((a * (xx - cx) * (yy - cy)).sum() / total)
    theta = 0.5 * math.degrees(math.atan2(2 * mu11, mu20 - mu02))
    return cx, cy, theta, total


def _dilate(mask: np.ndarray, px: int) -> np.ndarray:
    if px <= 0:
        return mask
    im = Image.fromarray((mask * 255).astype(np.uint8))
    return np.asarray(im.filter(ImageFilter.MaxFilter(2 * px + 1))) > 127


def peak_disp(bboxes: Sequence[Sequence[float]], w: float) -> float:
    """主体中心位移峰值 / 画宽(R9 口径)。"""
    c = np.array([[b[0], b[1]] for b in bboxes], dtype=float)
    if len(c) < 2 or w <= 0:
        return 0.0
    return float(np.linalg.norm(c - c[0], axis=1).max() / w)


def peak_area(bboxes: Sequence[Sequence[float]]) -> float:
    """主体面积变化峰值(相对首帧,R9 口径)。"""
    a = np.array([max(1.0, b[2] * b[3]) for b in bboxes], dtype=float)
    if a.size < 2:
        return 0.0
    return float(np.abs(a / a[0] - 1.0).max())


# ————————————————— 原子探针 · 运镜(§9.2 表 1-5 行)—————————————————

def check_dolly(bboxes: Sequence[Sequence[float]], *, floor: float = AREA_FRAC) -> ProbeReport:
    """推 / 拉:主体面积变化峰值 ≥8%。"""
    v = peak_area(bboxes)
    return ProbeReport("运镜·推拉", (_r("面积变化峰值", v, floor, unit="", detail="R9 口径"),))


def check_pan(bboxes: Sequence[Sequence[float]], w: float,
              *, floor: float = DISP_FRAC) -> ProbeReport:
    """摇 / 移 / 甩:主体中心位移峰值 ≥ 画宽 4%。"""
    v = peak_disp(bboxes, w)
    return ProbeReport("运镜·摇移甩", (_r("中心位移峰值/画宽", v, floor, detail="R9 口径"),))


def check_pitch(mask_start: np.ndarray, mask_end: np.ndarray, h: float,
                *, floor: float = 0.02) -> ProbeReport:
    """仰拍 / 俯视:扣掉相似变换后四角残差 ≥ 画高 2%。

    不扣相似变换就会把「只是缩放」判成 pitch 生效 —— 这一条是本表最容易假 pass 的。
    """
    c0, c1 = mask_corners(mask_start), mask_corners(mask_end)
    if c0 is None or c1 is None:
        return ProbeReport("运镜·仰拍俯视", (_r("四角残差/画高", 0.0, floor,
                                            detail="主体 mask 为空"),))
    v = similarity_residual(c0, c1) / max(1.0, h)
    return ProbeReport("运镜·仰拍俯视",
                       (_r("四角残差/画高", v, floor, detail="已扣平移+旋转+等比缩放"),))


def check_roll(rolls: Sequence[float], declared_deg: float,
               *, ratio: float = 0.90, reverse_ceil: float = 0.15) -> ProbeReport:
    """环绕 / 旋转:roll 峰值 ≥ 声明值 90%,且中途不回零。

    「不回零」量的是**反向行程占比**,不是中途最小值 —— 一次单调的环绕在起手处
    本来就接近 0,用最小值判会把画对了的环绕判掉;而「转过去又荡回来」的抖动,
    它的病就在反向行程上。
    """
    r = np.asarray(rolls, dtype=float)
    peak = float(np.abs(r).max()) if r.size else 0.0
    d = np.diff(r)
    total = float(np.abs(d).sum())
    net = float(abs(d.sum()))
    reverse = (total - net) / (2 * total) if total > 0 else 1.0
    return ProbeReport("运镜·环绕旋转", (
        _r("roll 峰值", peak, ratio * abs(declared_deg), unit="°",
           detail=f"声明 {declared_deg:g}°"),
        _r("反向行程占比", reverse, reverse_ceil, ceil=True,
           detail="荡回来 = 抖一下,不是环绕"),
    ))


def check_follow(subject_bboxes: Sequence[Sequence[float]],
                 bg_bboxes: Sequence[Sequence[float]], w: float,
                 *, drift_ceil: float = 0.03, bg_floor: float = 0.08) -> ProbeReport:
    """跟拍:主体钉住(漂移 <3%)而世界在走(背景位移 ≥8%)。"""
    return ProbeReport("运镜·跟拍", (
        _r("主体漂移/画宽", peak_disp(subject_bboxes, w), drift_ceil, ceil=True),
        _r("背景位移/画宽", peak_disp(bg_bboxes, w), bg_floor),
    ))


# ————————————————— 原子探针 · 特效(§9.2 表 6-12 行)—————————————————

def check_scan_bar(before: np.ndarray, after: np.ndarray, *, axis: int = 0,
                   grad_floor: float = 0.9, rise_ceil: int = 120) -> ProbeReport:
    """扫光 / 光条:边缘梯度 ≥0.9 L/px;软过渡 >120px 判 fail。"""
    grad, rise, pos = edge_profile(luma(after), axis=axis)
    return ProbeReport("特效·扫光光条", (
        _r("边缘梯度", grad, grad_floor, unit=" L/px", detail=f"位置 {pos}px"),
        _r("过渡带宽", rise, rise_ceil, ceil=True, unit=" px",
           detail="羽化过的光条不是光条,是渐变"),
    ))


def check_rim_light(off: np.ndarray, on: np.ndarray, subject: np.ndarray,
                    *, diff_floor: float = 8.0, gain_floor: float = 0.08) -> ProbeReport:
    """描边光:轮廓带内开关差 ≥ 阈;轮廓亮度 ≥ 邻域 +8%。

    开关差只在**轮廓带内**量,不在全画幅量:全画幅均值随画幅大小稀释,
    同一道边在 480p 过、在 4K 就不过 —— 那是画幅在决定判据,不是能力。
    """
    band = _dilate(subject, 3) & ~subject
    neigh = _dilate(subject, 14) & ~_dilate(subject, 5)
    d = float(np.abs(luma(on) - luma(off))[band].mean()) if band.any() else 0.0
    lo = luma(on)
    gain = 0.0
    if band.any() and neigh.any():
        gain = float(lo[band].mean() / max(1e-6, float(lo[neigh].mean())) - 1.0)
    return ProbeReport("特效·描边光", (
        _r("轮廓带内开关差", d, diff_floor, unit=" L"),
        _r("轮廓相对邻域增益", gain, gain_floor, detail="低于此值肉眼读不出「有边」"),
    ))


def check_drop_shadow(subject_bbox: Sequence[float], shadow_bbox: Sequence[float],
                      *, floor: float = 8.0) -> ProbeReport:
    """投影:影子 bbox 与主体 bbox 偏移 ≥8px(L5 口径)。贴合的影子读作脏。"""
    d = math.hypot(shadow_bbox[0] - subject_bbox[0], shadow_bbox[1] - subject_bbox[1])
    return ProbeReport("特效·投影", (_r("影子偏移", d, floor, unit=" px"),))


def check_crease(before: np.ndarray, after: np.ndarray, *, axis: str = "vertical",
                 gap_hi: float = 5.0) -> ProbeReport:
    """折痕:亮线与暗线相邻(≤5px)且中间无过渡带。一条折痕 = 一次高频对比事件。

    规格写的是「相邻 3-5px」,但**判据只有上界**:亮暗线贴得比 3px 更紧不是缺陷,
    缺陷是两者之间糊出一条过渡带。给这条设下界会把画对了的折痕判掉。
    """
    lum = luma(after)
    prof = lum.mean(axis=0 if axis == "vertical" else 1)
    hi = int(np.argmax(prof))
    left, right = prof[:hi], prof[hi + 1:]
    cands = []
    if left.size:
        cands.append(hi - int(np.argmin(left[::-1])) - 1)
    if right.size:
        cands.append(hi + 1 + int(np.argmin(right)))
    if not cands:
        return ProbeReport("特效·折痕", (_r("亮暗线间距", 99.0, gap_hi, ceil=True,
                                          unit=" px", detail="找不到暗线"),))
    lo_i = min(cands, key=lambda i: abs(i - hi))
    gap = abs(lo_i - hi)
    a, b = sorted((hi, lo_i))
    seg = prof[a:b + 1]
    plateau = 0
    if seg.size > 2:
        rng = max(1e-6, seg.max() - seg.min())
        plateau = int((np.abs(np.diff(seg)) < 0.05 * rng).sum())
    return ProbeReport("特效·折痕", (
        _r("亮暗线间距", gap, gap_hi, ceil=True, unit=" px",
           detail="只有上界:更紧不是缺陷"),
        _r("过渡带像素数", plateau, 0, ceil=True, detail="有过渡 = 糊了,不是折痕"),
    ))


def check_stack_edge(profiles: dict[int, np.ndarray], *,
                     axis: int = 1) -> ProbeReport:
    """叠层厚度:层缝条数随折数增长,且相邻层缝间距单调不增。

    `profiles` = {fold_count: 侧边区域的 2D 亮度}。读得出「一沓」的判据是
    **层缝密度**,不是厚度 —— 只画粗一条色带的话厚度达标而层缝为 0。
    """
    counts, spacings = {}, {}
    for n, region in sorted(profiles.items()):
        prof = np.asarray(region, dtype=float).mean(axis=1 - axis)
        rng = max(1e-6, prof.max() - prof.min())
        seams = [i for i in range(1, prof.size - 1)
                 if prof[i] < prof[i - 1] and prof[i] <= prof[i + 1]
                 and (prof[i - 1] - prof[i]) > 0.05 * rng]
        counts[n] = len(seams)
        spacings[n] = float(np.diff(seams).mean()) if len(seams) > 1 else float("inf")
    ns = sorted(counts)
    grow = all(counts[b] >= counts[a] for a, b in zip(ns, ns[1:]))
    tighten = all(spacings[b] <= spacings[a] + 1e-6 for a, b in zip(ns, ns[1:]))
    return ProbeReport("特效·叠层厚度", (
        _r("最少层缝条数", min(counts.values()) if counts else 0, 1,
           detail=f"实测 {counts}"),
        _r("层缝随折数增长", float(grow), 1.0, detail="不增长 = 只是变粗的色带"),
        _r("层缝间距单调不增", float(tighten), 1.0, detail=f"实测 {spacings}"),
    ))


def check_beat_breath(series: Sequence[float], times: Sequence[float],
                      beats: Sequence[float], fps: float,
                      *, offset_frames: float = 1.0) -> ProbeReport:
    """卡点呼吸:参数时间序列 std > 0(动态基准门);峰值帧 vs 拍点帧偏差 ≤1 帧。"""
    s = np.asarray(series, dtype=float)
    t = np.asarray(times, dtype=float)
    std = float(s.std())
    peaks = [i for i in range(1, s.size - 1) if s[i] >= s[i - 1] and s[i] > s[i + 1]]
    worst = 0.0
    if peaks and len(beats):
        pt = t[peaks]
        worst = float(max(np.abs(pt - b).min() for b in beats) * fps)
    return ProbeReport("特效·卡点呼吸", (
        _r("参数序列 std", std, 1e-6, detail="std=0 就是没动"),
        _r("峰点对拍偏差", worst, offset_frames, ceil=True, unit=" 帧"),
    ))


def check_grain(arr: np.ndarray, *, zoom: int = 4, peak_ceil: float = 0.6) -> ProbeReport:
    """胶片颗粒 / banding:400% 放大颗粒不重复(自相关次峰 <0.6);规则栅格判 fail。"""
    lum = luma(arr)
    h, w = lum.shape
    ch, cw = h // (2 * zoom), w // (2 * zoom)
    crop = lum[h // 2 - ch:h // 2 + ch, w // 2 - cw:w // 2 + cw]
    v = autocorr_peak(crop if crop.size else lum)
    return ProbeReport("特效·颗粒/banding", (
        _r("自相关次峰", v, peak_ceil, ceil=True,
           detail=f"{zoom * 100}% 裁切;高 = 图案在重复"),
    ))


# ————————————————— 原子探针 · 排版(§9.2 表 13-16 行)—————————————————

def check_lyric_stroke(alphas: Sequence[np.ndarray], times: Sequence[float],
                       glyph_h: float, *, window_s: float = LYRIC_WINDOW_S,
                       disp_floor: float = 0.26, rot_floor: float = 7.0
                       ) -> ProbeReport:
    """歌词落笔:0.15s 窗口内位移 ≥0.26 字高 **且** 旋转收 ≥7° **且** alpha 0→1。

    **三项必须同窗**:只做位移 = 字幕淡入,只做旋转 = 贴纸。分开量会把两者都放行。
    """
    m = [alpha_moments(a) for a in alphas]
    t = np.asarray(times, dtype=float)
    best = (0.0, 0.0, 0.0)
    best_score = -1.0
    for i in range(len(m)):
        js = np.nonzero((t > t[i]) & (t <= t[i] + window_s))[0]
        if not js.size:
            continue
        j = int(js[-1])
        (x0, y0, th0, a0), (x1, y1, th1, a1) = m[i], m[j]
        if a0 <= 0 or a1 <= 0:
            continue
        disp = math.hypot(x1 - x0, y1 - y0) / max(1.0, glyph_h)
        rot = abs((th1 - th0 + 90) % 180 - 90)
        gain = (a1 - a0) / max(a0, a1)
        score = min(disp / disp_floor, rot / rot_floor, gain / 0.5)
        if score > best_score:
            best_score, best = score, (disp, rot, gain)
    disp, rot, gain = best
    return ProbeReport("排版·歌词落笔", (
        _r("窗内位移/字高", disp, disp_floor),
        _r("窗内旋转收", rot, rot_floor, unit="°"),
        _r("窗内 alpha 增益", gain, 0.5, detail="0→1 才是落笔,不是常驻字"),
    ), note=f"同窗 {window_s:g}s")


def check_line_arc(glyphs: Sequence[Sequence[float]], glyph_h: float,
                   *, rise_floor: float = 0.10, arch_floor: float = 0.04
                   ) -> ProbeReport:
    """行笔势:行尾比行首高 ≥0.10 字高;中段拱起 ≥0.04 字高。

    没有拱起的「高低差」只是整行歪了;没有行尾抬升的拱起只是随机抖动。
    """
    p = np.array([[g[0], g[1]] for g in glyphs], dtype=float)
    if len(p) < 3:
        return ProbeReport("排版·行笔势", (_r("字数", len(p), 3, detail="不足以量笔势"),))
    rise = (p[0, 1] - p[-1, 1]) / max(1.0, glyph_h)  # y 向下为正,抬升即差为正
    k = (p[:, 0] - p[0, 0]) / max(1e-6, p[-1, 0] - p[0, 0])
    chord = p[0, 1] + k * (p[-1, 1] - p[0, 1])
    arch = float((chord[1:-1] - p[1:-1, 1]).max()) / max(1.0, glyph_h)
    return ProbeReport("排版·行笔势", (
        _r("行尾抬升/字高", rise, rise_floor),
        _r("中段拱起/字高", arch, arch_floor, detail="相对首尾连线"),
    ))


def check_typography_tiers(sizes: Sequence[float], *, tiers_floor: int = 7,
                           span_floor: float = 10.0) -> ProbeReport:
    """艺术字层级:层级 ≥7、字号跨度 ≥10:1。

    比 `poster.check_thickness()`(5 层 / 6:1)严 —— 那是全项目地板,
    本 skill 按 §9.4 抬了 3 档。层级在打架不在分工时,加层级,不要加特效补厚度。
    """
    s = [float(x) for x in sizes if x > 0]
    span = (max(s) / min(s)) if s else 0.0
    return ProbeReport("排版·艺术字层级", (
        _r("信息层级数", len(s), tiers_floor, unit=" 层"),
        _r("字号跨度", span, span_floor, unit=":1"),
    ))


def check_stroke_width(size: float, width: float, *, ratio: float = 0.038) -> ProbeReport:
    """描边:描边宽 = round(size*0.038),**禁写死 px**。

    按小字号调的固定宽度,放大后轮廓相对变细,字在乱底子上糊边。
    """
    want = round(size * ratio)
    return ProbeReport("排版·描边", (
        _r("与 round(size*0.038) 的偏差", abs(width - want), 0, ceil=True,
           unit=" px", detail=f"size {size:g} → 应为 {want}px,实测 {width:g}px"),
    ))


# ————————————————— L-镜 装配判据(§9.3)—————————————————

def shot_assay(frames: Sequence[pathlib.Path | np.ndarray],
               *, bboxes: Sequence[Sequence[float]] | None = None,
               framing: str | None = None, share: float | None = None,
               declared: str | None = None, tolerance: float = 18.0,
               sample: int = 4, p95_floor: float = 150.0,
               spread_floor: float = 90.0) -> ProbeReport:
    """一镜装配完立刻量 —— **这一级是《明月天涯》缺的那一级**。

    原子各自合格、乘起来不合格,只有在这里抓得住:`tint(im, color, contrast)`
    是把声明色当这块面的**中位明度**用的,改一个 bg 的颜色不是「换个色」,
    是给整镜的明度结构重定基准。这类耦合肉眼在单帧上看不出来,一量就出来。
    """
    if not frames:
        return ProbeReport("L-镜 装配", (_r("帧数", 0, 1),))

    p95s, p5s, wh = [], [], None
    for f in frames:
        if isinstance(f, (str, pathlib.Path)):
            arr = np.asarray(Image.open(f).convert("RGB")
                             .resize((240, 135)), dtype=float)
            if wh is None:
                wh = Image.open(f).size
        else:
            arr = np.asarray(f, dtype=float)
            if wh is None:
                wh = (arr.shape[1], arr.shape[0])
            arr = np.asarray(Image.fromarray(arr.astype(np.uint8))
                             .resize((240, 135)), dtype=float)
        lum = luma(arr)
        p95s.append(float(np.percentile(lum, 95)))
        p5s.append(float(np.percentile(lum, 5)))

    p95, p5 = float(np.mean(p95s)), float(np.mean(p5s))
    w, h = wh or (1, 1)
    results = [
        _r("p95", p95, p95_floor, unit=" L", detail="低 = 这镜没有一处高光"),
        _r("p95-p5 跨度", p95 - p5, spread_floor, unit=" L",
           detail="小 = 一片糊色,主体读不出轮廓"),
    ]

    if bboxes:
        want = share if share is not None else FRAMING_SHARE.get(framing or "", None)
        occ = float(np.mean([b[2] * b[3] for b in bboxes]) / max(1.0, w * h))
        if want is not None:
            results.append(_r("主体占幅", occ, want * FRAMING_TOLERANCE,
                              detail=f"景别 {framing or share} → share {want:g}"))
        d, a = peak_disp(bboxes, w), peak_area(bboxes)
        results.append(_r("冻结(位移或面积达标)",
                          max(d / DISP_FRAC, a / AREA_FRAC), 1.0,
                          detail=f"位移 {d:.3f}/{DISP_FRAC} · 面积 {a:.3f}/{AREA_FRAC}"))

    if declared:
        pal = parse_hex(declared)
        ratios = [analyze_declared(pathlib.Path(f), pal, tolerance, sample)[0]
                  for f in frames if isinstance(f, (str, pathlib.Path))]
        if ratios:
            results.append(_r(f"ΔE{tolerance:g} 跑偏占比", float(np.mean(ratios)),
                              0.05, ceil=True))

    return ProbeReport("L-镜 装配", tuple(results))


# ————————————————— CLI —————————————————

def _selftest() -> list[ProbeReport]:
    """拿真原子跑一遍表 —— 探针自己也要有证据,不能只是「写了」。"""
    sys.path.insert(0, str(_REPO / "pipeline" / "voice_room"))
    import mingyue_atoms as A

    reports: list[ProbeReport] = []

    # 扫光光条:硬边 → 梯度高、过渡窄
    reports.append(probe(A.scan_bar, check_scan_bar, y_frac=0.5, width_px=16,
                         glow_radius_px=88, glow_color=(255, 244, 214),
                         glow_alpha=0.5, direction="up"))

    # 反例:同一位置换成 120px 的高斯羽化带,必须 fail —— 探针分不出软硬就是废的
    def _soft(arr: np.ndarray, **_) -> np.ndarray:
        h = arr.shape[0]
        y = np.arange(h)[:, None, None]
        band = np.exp(-((y - h / 2) ** 2) / (2 * 60.0 ** 2)) * 127.0
        return np.clip(arr + band, 0, 255)

    soft = probe(_soft, check_scan_bar)
    reports.append(ProbeReport("反例·羽化带(应 FAIL)", soft.results,
                               note="探针必须把它判掉,否则硬边判据是摆设"))

    # 折痕:亮线 + 两侧糊过的暗带
    crease_kw = dict(frac=0.5, axis="vertical",
                     highlight_color=(255, 250, 236), shadow_color=(60, 52, 44),
                     highlight_width_px=3, shadow_width_px=4,
                     highlight_alpha=0.95, shadow_alpha=0.75)
    reports.append(probe_canvas(A.crease, check_crease, **crease_kw))

    # 反例:整条折痕糊掉 —— 亮暗之间开出过渡带,必须 fail
    def _soft_crease(canvas: Image.Image, **kw) -> None:
        A.crease(canvas, **kw)
        canvas.paste(canvas.filter(ImageFilter.GaussianBlur(9)), (0, 0))

    sc = probe_canvas(_soft_crease, check_crease, **crease_kw)
    reports.append(ProbeReport("反例·糊掉的折痕(应 FAIL)", sc.results))

    # 叠层厚度:折 3/5/7 次的侧边
    profiles = {}
    for n in (3, 5, 7):
        c = neutral_canvas(960, 540)
        A.stack_edge(c, 200, 120, 600, 420, fold_count=n, base_thickness_px=1.2,
                     edge_color=(232, 224, 208), side="right",
                     shadow_color=(70, 62, 52))
        profiles[n] = luma(np.asarray(c.convert("RGB"), dtype=float))[120:420, 600:840]
    reports.append(check_stack_edge(profiles))

    # 颗粒:白噪 vs 规则栅格(后者必须 fail)
    rng = np.random.default_rng(7)
    noise = np.clip(neutral_bed(320, 320) + rng.normal(0, 14, (320, 320, 3)), 0, 255)
    reports.append(check_grain(noise))
    yy = np.arange(320)[:, None, None]
    grid = np.clip(neutral_bed(320, 320) + 40 * np.sin(yy / 3.0), 0, 255)
    g = check_grain(grid)
    reports.append(ProbeReport("反例·规则栅格(应 FAIL)", g.results))

    # 运镜:一次推 + 一次甩
    push = [[480, 270, 200 + 8 * i, 300 + 12 * i] for i in range(12)]
    reports.append(check_dolly(push))
    swish = [[480 + 24 * i, 270, 200, 300] for i in range(12)]
    reports.append(check_pan(swish, w=960))

    # 仰拍:真透视 vs 纯缩放(后者必须 fail)
    base = standard_subject(neutral_bed(960, 540))
    m0 = diff_mask(neutral_bed(960, 540), base, tol=20)
    warped = np.asarray(Image.fromarray(base.astype(np.uint8)).transform(
        (960, 540), Image.QUAD,
        data=(180, 40, 780, 40, 700, 500, 260, 500), resample=Image.BILINEAR),
        dtype=float)
    m1 = diff_mask(neutral_bed(960, 540), warped, tol=20)
    reports.append(check_pitch(m0, m1, h=540))
    zoomed = standard_subject(neutral_bed(960, 540), height_frac=0.80)
    m2 = diff_mask(neutral_bed(960, 540), zoomed, tol=20)
    z = check_pitch(m0, m2, h=540)
    reports.append(ProbeReport("反例·纯缩放当仰拍(应 FAIL)", z.results))

    # 环绕:单调转到 12°;反例是转过去又回零(抖一下不是环绕)
    reports.append(check_roll([12.0 * i / 11 for i in range(12)], 12.0))
    wob = check_roll([0, 5, 11, 12, 4, 0.2, 6, 11.5], 12.0)
    reports.append(ProbeReport("反例·roll 中途回零(应 FAIL)", wob.results))

    # 跟拍:主体钉住、世界在走
    reports.append(check_follow(
        [[480 + (i % 2), 270, 200, 300] for i in range(10)],
        [[100 + 30 * i, 270, 400, 300] for i in range(10)], w=960))

    # 描边光:立绘轮廓外一圈提亮
    off = standard_subject(neutral_bed(960, 540))
    smask = diff_mask(neutral_bed(960, 540), off, tol=20)
    ring = _dilate(smask, 3) & ~smask
    on = off.copy()
    on[ring] = np.clip(on[ring] + 120.0, 0, 255)
    reports.append(check_rim_light(off, on, smask))
    nolight = check_rim_light(off, off, smask)
    reports.append(ProbeReport("反例·没有描边光(应 FAIL)", nolight.results))

    # 投影 / 卡点呼吸 / 行笔势
    reports.append(check_drop_shadow([480, 270, 200, 300], [492, 288, 200, 300]))
    fps, beats = 30.0, [0.5, 1.0, 1.5]
    ts = [i / fps for i in range(60)]
    reports.append(check_beat_breath(
        [1.0 + 0.06 * math.cos(2 * math.pi * (t - 0.5) / 0.5) for t in ts],
        ts, beats, fps))
    reports.append(check_line_arc(
        [[80 * i, 300 - 9 * i - 7 * math.sin(math.pi * i / 7), 60] for i in range(8)],
        glyph_h=60))

    # 歌词落笔:位移 + 旋转 + alpha 三项同窗;反例是只淡入(= 字幕)
    def _glyph(dy: float, ang: float, a: float) -> np.ndarray:
        g = Image.new("L", (240, 200), 0)
        ImageDraw.Draw(g).rectangle([70, 80, 170, 120], fill=int(255 * a))
        g = g.rotate(ang, center=(120, 100), resample=Image.BILINEAR)
        return np.asarray(g.transform((240, 200), Image.AFFINE,
                                      (1, 0, 0, 0, 1, -dy),
                                      resample=Image.BILINEAR), dtype=float)

    lt = [0.0, 0.05, 0.10, 0.15]
    reports.append(check_lyric_stroke(
        [_glyph(-24 + 8 * i, -16 + 16 * i / 3, 0.08 + 0.92 * i / 3) for i in range(4)],
        lt, glyph_h=40))
    fade = check_lyric_stroke([_glyph(0, 0, 0.08 + 0.92 * i / 3) for i in range(4)],
                              lt, glyph_h=40)
    reports.append(ProbeReport("反例·只淡入的字幕(应 FAIL)", fade.results))

    # L-镜:亮部 + 暗部俱全的合成镜 vs 压成一片黑的镜(后者是《明月天涯》A 的病)
    def _shot(gain: float) -> list[np.ndarray]:
        out = []
        for i in range(6):
            f = neutral_bed(480, 270, level=40)
            f[60:210, 120 + 12 * i:340 + 12 * i] = 235.0
            out.append(f * gain)
        return out

    bb = [[230 + 12 * i, 135, 220, 150] for i in range(6)]
    reports.append(shot_assay(_shot(1.0), bboxes=bb, framing="中景"))
    dark = shot_assay(_shot(0.45), bboxes=bb, framing="中景")
    reports.append(ProbeReport("反例·整镜没有高光(应 FAIL)", dark.results))

    # 排版:描边宽公式 + 层级
    reports.append(check_stroke_width(152, round(152 * 0.038)))
    reports.append(check_typography_tiers([420, 168, 96, 64, 48, 36, 28]))

    return reports


def main() -> int:
    ap = argparse.ArgumentParser(description="纸片人 MV 原子探针(SKILL §9.2/§9.3)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("selftest", help="拿真原子跑一遍标准表(含反例)")
    sp = sub.add_parser("shot", help="对一个镜头的帧跑 L-镜 装配判据")
    sp.add_argument("dir", type=pathlib.Path)
    sp.add_argument("--glob", default="*.png")
    sp.add_argument("--track", type=pathlib.Path, default=None,
                    help="motion.json —— 给出它才量得到主体占幅与冻结")
    sp.add_argument("--shot", default=None, help="只量这一镜(要 --track)")
    sp.add_argument("--framing", default=None, choices=sorted(FRAMING_SHARE))
    sp.add_argument("--declared", default=None, help="色板 hex 列表内容(不是文件路径)")
    sp.add_argument("--tolerance", type=float, default=18.0)
    args = ap.parse_args()

    if args.cmd == "selftest":
        reports = _selftest()
        expect_fail = {"反例·羽化带(应 FAIL)", "反例·糊掉的折痕(应 FAIL)",
                       "反例·规则栅格(应 FAIL)", "反例·纯缩放当仰拍(应 FAIL)",
                       "反例·roll 中途回零(应 FAIL)", "反例·只淡入的字幕(应 FAIL)",
                       "反例·没有描边光(应 FAIL)", "反例·整镜没有高光(应 FAIL)"}
        bad = []
        for rep in reports:
            print(rep)
            want_fail = rep.atom in expect_fail
            if rep.ok == want_fail:
                bad.append(rep.atom)
        print()
        if bad:
            print(f"探针自检不通过:{bad}")
            return 1
        print(f"探针自检通过 · {len(reports)} 项(含 {len(expect_fail)} 个反例)")
        return 0

    frames = sorted(args.dir.glob(args.glob))
    if not frames:
        print(f"没有帧:{args.dir}/{args.glob}")
        return 1

    bboxes = None
    if args.track:
        track = json.loads(args.track.read_text())["track"]
        if len(track) != len(frames):
            print(f"track {len(track)} 条 ≠ 帧 {len(frames)} 张,对不上就不敢按序号配对")
            return 1
        pairs = [(f, e) for f, e in zip(frames, track)
                 if args.shot is None or e.get("shot") == args.shot]
        if not pairs:
            print(f"track 里没有 shot={args.shot}")
            return 1
        frames = [f for f, _ in pairs]
        bboxes = [e["bbox"] for _, e in pairs]

    rep = shot_assay(frames, bboxes=bboxes, framing=args.framing,
                     declared=args.declared, tolerance=args.tolerance)
    print(f"{args.shot or args.dir.name} · {len(frames)} 帧")
    print(rep)
    return 0 if rep.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
