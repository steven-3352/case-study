"""纹理 · 素材缓存 —— 不认任何内容常量,路径由 Session 注入。

**tint() 的两个关键决策**:
1. 调制围绕 1.0 相乘(不把纹理归一到绝对亮度):声明色是这块面的平均色,纹理在上下浮动。
2. 中位数归一(不是均值):纸纤维图 L 跨 7~242,均值归一后幅度 ±50%,声明的近白色渲出
   一块脏灰板 —— 中位数后幅度由 `contrast` 写死,不随纹理本身有多脏而放大。

**flat_tex()** 减掉低频打光、保留高频材质:实拍纹理同时带着「那时候的光」,搬进本片
就是一块跟声明色无关的阴影。GaussianBlur + resize 去低频,剩下的是纤维本身。

**plate_arr()** 供 `tiled()` 的超大缩放分支用 —— 极端全景时取景框宽一万多世界像素,
一块砖被整体放大时走取模环绕采样,需要 ndarray 而不是 PIL Image。
"""
from __future__ import annotations

import numpy as np
from PIL import Image, ImageFilter

from . import session as _sess


def tex(name: str) -> Image.Image:
    s = _sess.get()
    if name not in s._tex:
        for base in (s.gen_dir, s.tex_dir):
            for ext in (".png", ".jpg"):
                p = base / f"{name}{ext}"
                if p.exists():
                    s._tex[name] = Image.open(p).convert("RGB")
                    return s._tex[name]
        raise FileNotFoundError(f"找不到素材 {name} (在 {s.gen_dir} / {s.tex_dir})")
    return s._tex[name]


def flat_tex(name: str) -> str:
    """派生一张「只剩纹理、不带原片打光」的素材,返回新素材名.

    实拍素材里同时有两种东西:高频的**材质**(纸纤维、木纹)和低频的**当时的打光**。
    我们要的是前者 —— 后者是别人现场的光,搬进本片就成了一块跟画面无关的阴影
    (纸纤维那张左半边压着一道大暗影,上色后整张纸看着像一块脏灰板)。
    减掉低频、保留高频,纸就回到「一张平整的纸,凑近能看见纤维」。
    """
    s = _sess.get()
    out = f"{name}__flat"
    if out not in s._tex:
        im = tex(name)
        small = im.convert("L").resize((160, 160), Image.LANCZOS)
        lo = np.asarray(small.filter(ImageFilter.GaussianBlur(24)), dtype=float)
        lo = np.asarray(Image.fromarray(lo.astype(np.uint8)).resize(im.size, Image.BICUBIC),
                        dtype=float)
        hi = np.asarray(im.convert("L"), dtype=float) - lo + lo.mean()
        s._tex[out] = Image.fromarray(
            np.clip(hi, 0, 255).astype(np.uint8)).convert("RGB")
    return out


def tint(im: Image.Image, color, contrast: float = 1.0) -> Image.Image:
    """把一张实拍/生成纹理压成某个声明色的明暗变化.

    只保留纹理的**相对明暗**,色相整体换成声明色 —— 这样纹理是真的(不是现搓的),
    颜色是声明色板里的(不偷带一套色进来)。`contrast` 放大明暗差。

    调制是**围绕 1.0 相乘**,不是把纹理拉到某个绝对亮度:声明色就是这块面的
    平均色,纹理只在它上下浮动。早期版本把每张纹理都归一到 0.5,象牙白的
    玻璃板和深色木地板于是渲成同一坨中灰 —— 声明色等于白写了。

    归一用的是**分位数不是均值**:纸纤维那张实拍图 L 跨 7~242(带阴影和折痕),
    除以均值后浮动能到 ±50%,声明的近白 #F6F3EC 渲出来是一块脏灰板。
    改成「中位数 = 声明色,contrast 就是上下摆动的幅度」后,幅度是写死的,
    不再随纹理本身有多脏而放大。
    """
    g = np.asarray(im.convert("L"), dtype=float) / 255.0
    p5, p50, p95 = np.percentile(g, (5, 50, 95))
    g = np.clip(1.0 + (g - p50) / max(p95 - p5, 1e-3) * contrast, 0.25, 1.55)
    out = g[:, :, None] * np.asarray(color, dtype=float)[None, None, :]
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))


def plate(name: str, color=None, contrast: float = 1.0, size=None) -> Image.Image:
    """取一张纹理,按需上色并缩放到世界尺寸,结果缓存(每帧重算太贵)."""
    s = _sess.get()
    key = (name, color, contrast, size)
    if key not in s._plate:
        im = tex(name)
        if color is not None:
            im = tint(im, color, contrast)
        if size is not None:
            im = im.resize(size, Image.LANCZOS)
        s._plate[key] = im
    return s._plate[key]


def plate_arr(name: str, color=None, contrast: float = 1.0) -> np.ndarray:
    """`plate` 的 ndarray 版(缓存)—— 供需要按取模索引环绕采样的地方用。"""
    s = _sess.get()
    key = (name, color, contrast)
    if key not in s._plate_arr:
        s._plate_arr[key] = np.asarray(plate(name, color, contrast).convert("RGB"))
    return s._plate_arr[key]
