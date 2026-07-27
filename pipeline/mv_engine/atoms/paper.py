"""纸的物理 —— 折叠、折痕、叠层侧边。

这三个吃任意 RGBA 吐任意 RGBA,是纯像素算子,所以归 atoms 而不是某一部片。
真正属于内容的是「第几拍折第几折」那张表,不在这里。"""
from __future__ import annotations

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from .ease import _compress
from .geometry import solve_perspective
from ._contract import atom

RGB = tuple[int, int, int]


@atom(touches_alpha=True)
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

@atom(touches_alpha=True)
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

@atom(touches_alpha=True)
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
