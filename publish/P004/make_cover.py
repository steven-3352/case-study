#!/usr/bin/env python3
"""P004 K1 · 小红书封面生成 · 1080×1440(3:4)
chaos 帧 + 黑底字幕「又是这个/问八百遍」+ 角标。

用法:
  python3 publish/P004/make_cover.py
  python3 publish/P004/make_cover.py --line1 "又是这个" --line2 "问八百遍"
  python3 publish/P004/make_cover.py --src pipeline/p004_video/out/scenes/01a_chaos.mp4 --t 0.4

输出: publish/P004/cover_xhs.png
"""
from __future__ import annotations

import argparse
import pathlib
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent

FONT_CANDIDATES = [
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
]


def find_font() -> str:
    for p in FONT_CANDIDATES:
        if pathlib.Path(p).exists():
            return p
    sys.exit("找不到中文字体,请补 FONT_CANDIDATES")


def grab_chaos_frame(src: pathlib.Path, t: float, out: pathlib.Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-ss", f"{t:.3f}", "-i", str(src),
        "-frames:v", "1",
        "-vf", "scale=1080:1920:flags=lanczos,crop=1080:1440",
        str(out),
    ]
    subprocess.run(cmd, check=True)


def render(bg: pathlib.Path, line1: str, line2: str, brand: str, out: pathlib.Path) -> None:
    img = Image.open(bg).convert("RGB")
    W, H = img.size

    dim = Image.new("RGB", (W, H), (0, 0, 0))
    img = Image.blend(img, dim, 0.45)

    draw = ImageDraw.Draw(img)
    fp = find_font()
    big = ImageFont.truetype(fp, 220)
    brand_f = ImageFont.truetype(fp, 38)

    bb1 = draw.textbbox((0, 0), line1, font=big)
    w1 = bb1[2] - bb1[0]
    bb2 = draw.textbbox((0, 0), line2, font=big)
    w2 = bb2[2] - bb2[0]

    y1 = int(H * 0.32)
    y2 = y1 + 280

    draw.text(((W-w1)//2, y1), line1, fill=(255, 255, 255), font=big,
              stroke_width=8, stroke_fill=(0, 0, 0))
    draw.text(((W-w2)//2, y2), line2, fill=(255, 100, 100), font=big,
              stroke_width=8, stroke_fill=(0, 0, 0))

    bbb = draw.textbbox((0, 0), brand, font=brand_f)
    wb = bbb[2] - bbb[0]
    draw.text(((W-wb)//2, H - 100), brand, fill=(180, 180, 180), font=brand_f)

    img.save(out, optimize=True)
    print(f"✓ {out} ({out.stat().st_size//1024} KB)")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=str(ROOT/"assets/broll/k1_chaos.mp4"))
    ap.add_argument("--t", type=float, default=2.0, help="从源视频第几秒抽帧")
    ap.add_argument("--line1", default="又是这个")
    ap.add_argument("--line2", default="问八百遍")
    ap.add_argument("--brand", default="AI · 小老板小系统")
    ap.add_argument("--out", default=str(ROOT/"publish/P004/cover_xhs.png"))
    args = ap.parse_args()

    chaos_frame = ROOT/"publish/P004/cover_chaos.png"
    grab_chaos_frame(pathlib.Path(args.src), args.t, chaos_frame)
    render(chaos_frame, args.line1, args.line2, args.brand, pathlib.Path(args.out))


if __name__ == "__main__":
    main()
