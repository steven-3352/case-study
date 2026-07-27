#!/usr/bin/env python3
"""生成即梦 i2v 首帧图（22 张 1920x1080）· 《明月天涯》立绘 MV

裁切清单见 publish/语音厅/design/storyboard_jimeng.md §5。
铁律：立绘像素零改动（只做无损裁切与等比缩放，不调色不变形）。
背景来自实拍纹理文件（grey_plaster_4k.jpg），不用 PIL 现搓渐变。
"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter, ImageEnhance

Image.MAX_IMAGE_PIXELS = None

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "publish/语音厅"
TEX = SRC / "assets/textures/grey_plaster_4k.jpg"
OUT = SRC / "jimeng/frames"
W, H = 1920, 1080

TACHIE = {
    "XH": SRC / "轩珩.png",
    "ZL": SRC / "中里毅2.png",
    "NL": SRC / "诺兰.png",
    "CY": SRC / "cy.png",
}

# 背景明度档：暗场 #221F1A / 阴影 #4A463E（design_language.md §1.A）
BG_LEVELS = {"dark": (0x22, 0x1F, 0x1A), "mid": (0x4A, 0x46, 0x3E), "lift": (0x6A, 0x63, 0x56)}

# clip -> (角色, 裁切框 fx0,fy0,fx1,fy1 相对 alpha bbox, 人物占画幅高比例, 水平锚 0=左 .5=中 1=右, 背景档, 背景虚化)
CLIPS = {
    "C01": ("XH", (0.00, 0.00, 1.00, 1.00), 0.86, 0.50, "mid", 14),
    "C02": ("XH", (0.00, 0.00, 1.00, 0.50), 0.96, 0.68, "mid", 14),
    "C03": ("XH", (0.22, 0.058, 0.78, 0.112), 0.95, 0.50, "dark", 26),
    "C04": ("XH", (0.14, 0.360, 0.88, 0.495), 0.92, 0.50, "dark", 30),
    "C05": ("XH", (0.00, 0.560, 1.00, 0.920), 0.95, 0.50, "mid", 20),
    "C06": ("ZL", (0.00, 0.00, 1.00, 1.00), 0.86, 0.50, "lift", 14),
    "C07": ("ZL", (0.00, 0.00, 1.00, 0.50), 0.96, 0.34, "lift", 14),
    "C08": ("ZL", (0.20, 0.020, 0.80, 0.140), 0.95, 0.50, "lift", 24),
    "C09": ("ZL", (0.42, 0.220, 0.98, 0.370), 0.92, 0.50, "lift", 28),
    "C10": ("ZL", (0.04, 0.330, 0.56, 0.470), 0.92, 0.50, "dark", 28),
    "C11": ("NL", (0.00, 0.00, 1.00, 1.00), 0.86, 0.50, "mid", 14),
    "C12": ("NL", (0.00, 0.00, 1.00, 0.48), 0.96, 0.62, "lift", 14),
    "C13": ("NL", (0.18, 0.020, 0.82, 0.135), 0.95, 0.50, "dark", 26),
    "C14": ("NL", (0.24, 0.145, 0.76, 0.260), 0.92, 0.50, "dark", 28),
    "C15": ("NL", (0.48, 0.370, 1.00, 0.490), 0.92, 0.50, "dark", 28),
    "C16": ("CY", (0.00, 0.00, 1.00, 1.00), 0.86, 0.50, "dark", 14),
    "C17": ("CY", (0.00, 0.00, 1.00, 0.52), 0.96, 0.62, "dark", 16),
    "C18": ("CY", (0.20, 0.020, 0.80, 0.135), 0.95, 0.50, "dark", 26),
    "C19": ("CY", (0.40, 0.140, 0.84, 0.250), 0.92, 0.50, "dark", 28),
    "C20": ("CY", (0.24, 0.135, 0.78, 0.290), 0.92, 0.50, "dark", 26),
}

# 组合镜：(clip -> [角色...], 人物占画幅高比例, 背景档)
GROUPS = {
    "C21": (["XH", "ZL"], 0.84, "mid"),
    "C22": (["NL", "CY"], 0.84, "dark"),
    "C23": (["XH", "ZL", "NL", "CY"], 0.68, "mid"),
}


def alpha_bbox(im):
    a = np.array(im)[:, :, 3]
    ys, xs = np.where(a > 16)
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def make_bg(level, blur):
    """背景来自实拍石膏墙纹理，只做明度映射与虚化，不生成渐变。"""
    tex = Image.open(TEX).convert("RGB")
    # 等比覆盖 1920x1080
    s = max(W / tex.width, H / tex.height)
    tex = tex.resize((int(tex.width * s + 1), int(tex.height * s + 1)), Image.LANCZOS)
    left = (tex.width - W) // 2
    top = (tex.height - H) // 2
    tex = tex.crop((left, top, left + W, top + H))
    if blur:
        tex = tex.filter(ImageFilter.GaussianBlur(blur))
    arr = np.asarray(tex, dtype=np.float32) / 255.0
    lum = arr.mean(axis=2, keepdims=True)
    lo, hi = lum.min(), lum.max()
    norm = (lum - lo) / max(hi - lo, 1e-6)          # 保留真实纹理的相对起伏
    target = np.array(BG_LEVELS[level], dtype=np.float32) / 255.0
    out = target * (0.82 + 0.36 * norm)             # 纹理起伏 ±18% 明度
    # 暖调渐晕：靠边压暗（不是渐变底色，是压暗已有纹理）
    yy, xx = np.mgrid[0:H, 0:W]
    r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
    out *= (1.0 - 0.26 * np.clip(r - 0.40, 0, None) ** 1.6)[:, :, None]
    return Image.fromarray(np.clip(out * 255, 0, 255).astype(np.uint8), "RGB")


def crop_tachie(key, frac):
    im = Image.open(TACHIE[key]).convert("RGBA")
    x0, y0, x1, y1 = alpha_bbox(im)
    bw, bh = x1 - x0, y1 - y0
    fx0, fy0, fx1, fy1 = frac
    cx0 = int(x0 + fx0 * bw)
    cx1 = int(x0 + fx1 * bw)
    cy0 = int(y0 + fy0 * bh)
    cy1 = int(y0 + fy1 * bh)
    return im.crop((cx0, cy0, cx1, cy1))


def place(bg, fg, height_frac, anchor_x, bottom_frac=0.955):
    target_h = int(H * height_frac)
    scale = target_h / fg.height
    fg = fg.resize((max(1, int(fg.width * scale)), target_h), Image.LANCZOS)
    if fg.width > W * 0.98:  # 过宽时按宽度回退
        scale = (W * 0.98) / fg.width
        fg = fg.resize((int(fg.width * scale), int(fg.height * scale)), Image.LANCZOS)
    x = int((W - fg.width) * anchor_x)
    y = int(H * bottom_frac) - fg.height
    y = max(min(y, H - fg.height), min(0, H - fg.height))
    out = bg.copy()
    out.paste(fg, (x, y), fg)
    return out


def contact_shadow(img, fg_box):
    return img


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    bg_cache = {}

    for cid, (key, frac, hfrac, ax, level, blur) in CLIPS.items():
        ck = (level, blur)
        if ck not in bg_cache:
            bg_cache[ck] = make_bg(level, blur)
        fg = crop_tachie(key, frac)
        is_full = frac[3] >= 0.99
        bottom = 0.955 if is_full else 0.99
        img = place(bg_cache[ck], fg, hfrac, ax, bottom)
        img.save(OUT / f"{cid}.png")
        print(f"{cid}  {key}  crop={fg.size}  -> {OUT / (cid + '.png')}")

    for cid, (keys, hfrac, level) in GROUPS.items():
        ck = (level, 14)
        if ck not in bg_cache:
            bg_cache[ck] = make_bg(level, 14)
        bg = bg_cache[ck].copy()
        figs = []
        for k in keys:
            im = Image.open(TACHIE[k]).convert("RGBA")
            im = im.crop(alpha_bbox(im))
            th = int(H * hfrac)
            im = im.resize((max(1, int(im.width * th / im.height)), th), Image.LANCZOS)
            figs.append(im)
        gap = int(W * 0.02)
        total = sum(f.width for f in figs) + gap * (len(figs) - 1)
        if total > W * 0.92:
            s = (W * 0.92) / total
            figs = [f.resize((int(f.width * s), int(f.height * s)), Image.LANCZOS) for f in figs]
            total = sum(f.width for f in figs) + gap * (len(figs) - 1)
        x = (W - total) // 2
        baseline = int(H * 0.955)
        for f in figs:
            bg.paste(f, (x, baseline - f.height), f)
            x += f.width + gap
        bg.save(OUT / f"{cid}.png")
        print(f"{cid}  {'+'.join(keys)}  -> {OUT / (cid + '.png')}")


if __name__ == "__main__":
    main()
