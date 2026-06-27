#!/usr/bin/env python3
"""主视觉色域自检 · 禁霓虹色细则的自动兜底 (DECISIONS Q9).

用法:
    python3 pipeline/gate_check_palette.py <png_path> [<png_path> ...]
    python3 pipeline/gate_check_palette.py publish/2026-W*/D*/douyin/cover.png
    python3 pipeline/gate_check_palette.py --threshold 0.05 path.png

判定:
    - HSL H ∈ [240°, 290°] (蓝紫色域) 的像素占比 > threshold (默认 5%) → FAIL
    - 真截屏例外: 文件名/路径含 screenshot/screen_grab/real_/wxchat_/ios_ → 跳过
    - 输出 hex 主色 top-5 + 蓝紫占比,fail 时退出码 1

为什么这个色域:
    Dracula 主题霓虹三件套(紫 #bd93f9 / 粉 #ff79c6 / 青 #8be9fd) 全在 H=240~290.
    暖红→冷蓝渐变(#2a0e0e→#0a0e14) 的过渡色也落在这区间.
    系统蓝(iOS #007AFF H≈215, 微信绿 H=120) 都在区间外, 不误伤.

为什么 5%:
    主背景一片色 ≥ 30%, 强调色块 ≥ 5%. 真截屏里偶尔有 logo 紫(<2%) 不算违规.
"""
from __future__ import annotations

import argparse
import colorsys
import pathlib
import sys
from collections import Counter

from PIL import Image

REAL_SCREENSHOT_HINTS = (
    "screenshot", "screen_grab", "real_", "wxchat_", "ios_",
    "android_", "douyin_native_", "xhs_native_",
)

VIOLET_HUE_LOW = 240 / 360
VIOLET_HUE_HIGH = 290 / 360


def is_real_screenshot(path: pathlib.Path) -> bool:
    s = str(path).lower()
    return any(h in s for h in REAL_SCREENSHOT_HINTS)


def analyze(path: pathlib.Path, sample: int = 4) -> tuple[float, list[tuple[str, int]]]:
    """返回 (蓝紫像素占比, 主色 top5 hex).

    sample: 下采样步长 (默认 4 = 1/16 像素, 1080x1920 → ~12 万像素采样).
    """
    img = Image.open(path).convert("RGB")
    pixels = list(img.getdata())[::sample * sample]
    violet = 0
    bucket: Counter[tuple[int, int, int]] = Counter()
    for r, g, b in pixels:
        h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
        # 只统计有饱和度的像素(s>0.15 排除纯黑/白/灰)
        if s > 0.15 and l > 0.1 and l < 0.9 and VIOLET_HUE_LOW <= h <= VIOLET_HUE_HIGH:
            violet += 1
        # 主色量化到 32 级
        bucket[(r >> 5 << 5, g >> 5 << 5, b >> 5 << 5)] += 1
    total = len(pixels)
    ratio = violet / total if total else 0
    top5 = [(f"#{r:02x}{g:02x}{b:02x}", n) for (r, g, b), n in bucket.most_common(5)]
    return ratio, top5


def main() -> int:
    ap = argparse.ArgumentParser(description="主视觉禁霓虹色自检")
    ap.add_argument("paths", nargs="+", type=pathlib.Path)
    ap.add_argument("--threshold", type=float, default=0.05,
                    help="蓝紫像素占比阈值,默认 0.05 (5%%)")
    ap.add_argument("--sample", type=int, default=4,
                    help="下采样步长,默认 4")
    ap.add_argument("--strict", action="store_true",
                    help="真截屏路径例外也参与判定")
    args = ap.parse_args()

    failed: list[pathlib.Path] = []
    for path in args.paths:
        if not path.exists():
            print(f"  ⨯ {path}: 文件不存在", file=sys.stderr)
            failed.append(path)
            continue
        if not args.strict and is_real_screenshot(path):
            print(f"  ⏭ {path}: 真截屏例外,跳过")
            continue
        ratio, top5 = analyze(path, sample=args.sample)
        flag = "✗ FAIL" if ratio > args.threshold else "✓ OK"
        print(f"  {flag} {path}")
        print(f"     蓝紫占比: {ratio:.2%} (阈值 {args.threshold:.0%})")
        print(f"     主色 top5: {', '.join(f'{h}×{n}' for h, n in top5)}")
        if ratio > args.threshold:
            failed.append(path)

    if failed:
        print(f"\n禁霓虹色门 FAIL · {len(failed)}/{len(args.paths)} 张违规")
        print("  → 改色,或确认是真截屏后改路径名加 screenshot/wxchat_ 一类标记")
        print("  → 规则: docs/DECISIONS.md Q9 「禁霓虹色细则」")
        return 1
    print(f"\n禁霓虹色门 PASS · {len(args.paths)} 张全部 OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
