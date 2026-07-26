#!/usr/bin/env python3
"""《明月天涯》创意 A(扫描仪)/ B(对折)的新原子件.

规格来源:
- 物理参数与实现路线 → `publish/语音厅/design/motion_tech_plan.md` §1-§3
- 颜色 → `publish/语音厅/design/design_language.md` §1

**本模块的原子不带默认颜色。** 依 design_language.md §9:
「新原子的颜色参数一律从 §1 表取,不得自带默认色」——原子不知道自己在哪部片里用,
一旦自带默认色,它就偷偷带了一套色板进来。

所有 `arr` 参数都是 float ndarray (H, W, 3),值域 0-255,函数不就地修改。
"""
from __future__ import annotations

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

RGB = tuple[int, int, int]


# ————————————————— A · 扫描仪 —————————————————

def scan_bar(arr: np.ndarray, y_frac: float, width_px: int, glow_radius_px: int,
             glow_color: RGB, glow_alpha: float, direction: str = "down",
             scanned_brightness_add: float = 0.0) -> np.ndarray:
    """一道硬边高亮光条 + 前沿辉光,扫过的区域留下亮度差.

    design_language.md §3.1 规定光条边缘梯度 ≥0.9 L/px、软过渡 >120px 判 FAIL,
    所以光条本体是**硬边**(直接赋值,不做羽化),只有前沿辉光是衰减带。

    y_frac 0.0=顶 1.0=底。direction 决定"已扫描"是哪一侧,以及辉光往哪边拖。
    """
    h, w = arr.shape[:2]
    out = arr.copy()
    axis_len = h if direction in ("down", "up") else w
    pos = int(np.clip(y_frac, 0.0, 1.0) * axis_len)
    glow = np.asarray(glow_color, dtype=float)

    def band(lo: int, hi: int) -> tuple:
        lo, hi = max(0, lo), min(axis_len, hi)
        return (slice(lo, hi), slice(None)) if direction in ("down", "up") \
            else (slice(None), slice(lo, hi))

    if scanned_brightness_add:
        scanned = (0, pos) if direction in ("down", "right") else (pos, axis_len)
        sl = band(*scanned)
        out[sl] = np.clip(out[sl] + scanned_brightness_add * 255.0, 0, 255)

    # 前沿辉光:沿行进方向拖一条高斯衰减带(光条已经走过的地方不拖,那是"已扫描")
    sign = 1 if direction in ("down", "right") else -1
    sigma = max(1.0, glow_radius_px * 0.4)
    for d in range(1, glow_radius_px + 1):
        decay = float(np.exp(-(d ** 2) / (2 * sigma ** 2))) * glow_alpha
        if decay < 0.004:
            break
        p = pos + sign * d
        if 0 <= p < axis_len:
            sl = band(p, p + 1)
            out[sl] = np.clip(out[sl] + glow * decay, 0, 255)

    sl = band(pos - width_px // 2, pos - width_px // 2 + max(1, width_px))
    out[sl] = np.clip(np.maximum(out[sl], glow), 0, 255)
    return out


def banding(arr: np.ndarray, t: float, frequency: float, amplitude: float,
            scroll_speed: float = 0.0, phase_offset: float = 0.0) -> np.ndarray:
    """CCD 行噪:周期性横向暗条带,可垂直滚动.

    frequency = 全画高内的条带周期数。amplitude 0=不可见 1=纯黑条。
    scroll_speed 单位 px/s。
    """
    h = arr.shape[0]
    yy = np.arange(h, dtype=float)
    phase = phase_offset + t * scroll_speed / h * (2 * np.pi)
    mask = 0.5 - 0.5 * np.cos(yy / h * frequency * 2 * np.pi + phase)
    return np.clip(arr * (1.0 - amplitude * mask)[:, None, None], 0, 255)


def lid_flare(arr: np.ndarray, intensity: float, gradient_falloff: float,
              color: RGB, bloom_radius_px: int = 0) -> np.ndarray:
    """掀盖漏光:从顶部灌入的日光,screen 合成,上强下弱.

    intensity 0=无 1=顶部全白冲淡。gradient_falloff 越大衰减越快(1.5 缓 / 4.0 仅上沿)。
    """
    if intensity <= 0:
        return arr
    h = arr.shape[0]
    ramp = ((1.0 - np.linspace(0.0, 1.0, h)) ** gradient_falloff)[:, None, None] * intensity
    light = np.asarray(color, dtype=float) * ramp
    out = 255.0 - (255.0 - arr) * (255.0 - light) / 255.0
    if bloom_radius_px > 0:
        im = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))
        blur = np.asarray(im.filter(ImageFilter.GaussianBlur(bloom_radius_px)), dtype=float)
        out = 255.0 - (255.0 - out) * (255.0 - blur * 0.3) / 255.0
    return np.clip(out, 0, 255)


def jam_smear(arr: np.ndarray, smear_amount_px: int, smear_start_frac: float,
              falloff: float, alpha: float, direction: str = "vertical") -> np.ndarray:
    """卡纸拖影:从某一行/列起,把那一行的像素沿扫描方向拖长.

    干净区到拖影区是**硬边界**(SOURCES.md 记的"扫描扫坏了"的视觉签名),
    所以 smear_start 之前一个像素都不动。
    """
    out = arr.copy()
    vertical = direction == "vertical"
    axis_len = arr.shape[0] if vertical else arr.shape[1]
    start = int(np.clip(smear_start_frac, 0.0, 1.0) * (axis_len - 1))
    src = arr[start] if vertical else arr[:, start]

    for d in range(1, smear_amount_px + 1):
        k = alpha * float(np.exp(-falloff * d / smear_amount_px))
        if k < 0.01:
            break
        p = start + d
        if p >= axis_len:
            break
        if vertical:
            out[p] = out[p] * (1 - k) + src * k
        else:
            out[:, p] = out[:, p] * (1 - k) + src * k
    return np.clip(out, 0, 255)


# ————————————————— B · 对折 —————————————————

def solve_perspective(out_quad: list, in_quad: list) -> list:
    """解 PIL `Image.Transform.PERSPECTIVE` 的 8 系数.

    PIL 用的是**反向映射**:输出像素 (x,y) 去输入图的
    ((ax+by+c)/(gx+hy+1), (dx+ey+f)/(gx+hy+1)) 取色。
    所以这里的参数顺序是 (输出四点, 输入四点),不是通常的 (src, dst)——
    传反了图像会以奇怪的方式外扩,而不会报错。

    四点顺序需一致(如均为 左上→右上→右下→左下)。
    """
    a, b = [], []
    for (ox, oy), (ix, iy) in zip(out_quad, in_quad):
        a.append([ox, oy, 1, 0, 0, 0, -ix * ox, -ix * oy])
        a.append([0, 0, 0, ox, oy, 1, -iy * ox, -iy * oy])
        b += [ix, iy]
    coeffs = np.linalg.solve(np.asarray(a, dtype=float), np.asarray(b, dtype=float))
    return coeffs.tolist()


def _compress(n: int) -> float:
    """第 n 折翻过去那半的厚度压缩比 —— 纸越折越厚,越压不平."""
    return 0.7 * (0.5 ** (n / 4.0))


def paper_fold(layer: Image.Image, fold_count: int) -> Image.Image:
    """把一张 RGBA 图对折 fold_count 次,交替竖折/横折.

    每折:远端那半沿折痕翻过来盖在近端那半上,并做透视收缩(靠折痕的边保持原宽,
    远端那条边收窄)——这是射影变换不是仿射,PIL AFFINE 做不了,见 motion_tech_plan §1.1。
    翻过来的半张压在上面,所以看得见的是背面那半的内容。

    返回折后的图(尺寸随之减半),bbox 由调用方按返回尺寸重算。
    """
    im = layer
    for n in range(1, fold_count + 1):
        w, h = im.size
        vertical_crease = (n % 2 == 1)          # 奇数折竖着折,偶数折横着折
        if vertical_crease:
            half, far = w // 2, im.crop((w // 2, 0, w, h))
            if half < 2:
                break
            thick = max(1, int(half * _compress(n)))
            # 远端半张翻过来:折痕边(原 x=0)贴住折痕,远端边(原 x=half)收到 thick
            coeffs = solve_perspective(
                [(0, 0), (thick, 0), (thick, h), (0, h)],
                [(0, 0), (half, 0), (half, h), (0, h)])
            flipped = far.transpose(Image.FLIP_LEFT_RIGHT).transform(
                (thick, h), Image.Transform.PERSPECTIVE, coeffs, Image.BICUBIC)
            base = im.crop((0, 0, half, h))
            base.alpha_composite(flipped, (half - thick, 0))
            im = base
        else:
            half, far = h // 2, im.crop((0, h // 2, w, h))
            if half < 2:
                break
            thick = max(1, int(half * _compress(n)))
            coeffs = solve_perspective(
                [(0, 0), (w, 0), (w, thick), (0, thick)],
                [(0, 0), (w, 0), (w, half), (0, half)])
            flipped = far.transpose(Image.FLIP_TOP_BOTTOM).transform(
                (w, thick), Image.Transform.PERSPECTIVE, coeffs, Image.BICUBIC)
            base = im.crop((0, 0, w, half))
            base.alpha_composite(flipped, (0, half - thick))
            im = base
    return im


def fold_press(k: float) -> float:
    """一折的三阶段进度曲线 —— 「折不动 / 回弹」.

    k 是这一折的归一化时间 0→1,返回 0→1 的压下量。
    A(0~30%) 用力压到 70% → B(30~50%) 鼓起回弹到 50% → C(50~100%) 压到底。
    纯 ease 曲线,不需要物理引擎,帧耗时不变(motion_tech_plan §1.3)。
    """
    k = float(np.clip(k, 0.0, 1.0))
    if k < 0.30:
        return 0.70 * (k / 0.30) ** 0.6
    if k < 0.50:
        return 0.70 - 0.20 * ((k - 0.30) / 0.20)
    e = (k - 0.50) / 0.50
    return 0.50 + 0.50 * (1 - (1 - e) ** 3)


def crease(canvas: Image.Image, frac: float, axis: str,
           highlight_color: RGB, shadow_color: RGB,
           highlight_width_px: int, shadow_width_px: int,
           highlight_alpha: float, shadow_alpha: float) -> None:
    """折痕:中心一条亮线 + 两侧阴影带,就地画在 RGBA canvas 上.

    design_language.md §3.1:亮线与暗线**相邻 3–5px,中间没有过渡** —— 一条折痕
    就是一次高频对比事件。所以阴影带先糊,亮线后画且不糊。
    """
    w, h = canvas.size
    vertical = axis == "vertical"
    p = int(np.clip(frac, 0.0, 1.0) * ((w if vertical else h) - 1))

    sh = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(sh)
    a = int(np.clip(shadow_alpha, 0, 1) * 255)
    box = [p - shadow_width_px, 0, p + shadow_width_px, h] if vertical \
        else [0, p - shadow_width_px, w, p + shadow_width_px]
    d.rectangle(box, fill=(*shadow_color, a))
    canvas.alpha_composite(sh.filter(ImageFilter.GaussianBlur(shadow_width_px * 0.5)))

    hl = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(hl)
    a = int(np.clip(highlight_alpha, 0, 1) * 255)
    hw = max(1, highlight_width_px)
    box = [p - hw // 2, 0, p - hw // 2 + hw, h] if vertical \
        else [0, p - hw // 2, w, p - hw // 2 + hw]
    d.rectangle(box, fill=(*highlight_color, a))
    canvas.alpha_composite(hl)


def stack_edge(canvas: Image.Image, x0: int, y0: int, x1: int, y1: int,
               fold_count: int, base_thickness_px: float,
               edge_color: RGB, side: str, shadow_color: RGB | None = None) -> None:
    """叠层侧边:折 n 次后纸厚 = base * 2ⁿ,画在纸块的某一侧.

    第 7 折 2⁷=128px 已经是一块厚纸块 —— 这正是"折不动"的视觉依据。
    宽度钳到画宽 1/4,否则第 10 折就 2048px 冲出画面(motion_tech_plan §3.2)。
    """
    thick = min(canvas.size[0] / 4.0, base_thickness_px * (2 ** fold_count))
    if thick < 1:
        return
    ov = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    t = int(thick)
    box = {"right": [x1, y0, x1 + t, y1], "left": [x0 - t, y0, x0, y1],
           "bottom": [x0, y1, x1, y1 + t], "top": [x0, y0 - t, x1, y0]}[side]
    d.rectangle(box, fill=(*edge_color, 255))
    if shadow_color is not None and t >= 3:
        inner = [box[0], box[1], box[0] + max(1, t // 3), box[3]] if side in ("right", "left") \
            else [box[0], box[1], box[2], box[1] + max(1, t // 3)]
        d.rectangle(inner, fill=(*shadow_color, 190))
    # 层线:折 n 次是 2ⁿ 层纸,侧边看得见的就是这些层。少了这一步,"厚"只是一条色带,
    # 读不出「这是折了十几次的同一张纸」。层多到画不下时按可分辨间距(3px)封顶。
    if shadow_color is not None and t >= 6:
        layers = min(2 ** fold_count, int(t / 3))
        for i in range(1, layers):
            p = i / layers
            if side in ("right", "left"):
                q = box[0] + (box[2] - box[0]) * p
                d.line([(q, box[1]), (q, box[3])], fill=(*shadow_color, 120), width=1)
            else:
                q = box[1] + (box[3] - box[1]) * p
                d.line([(box[0], q), (box[2], q)], fill=(*shadow_color, 120), width=1)
    canvas.alpha_composite(ov)
