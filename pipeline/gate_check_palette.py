#!/usr/bin/env python3
"""主视觉色域自检 · 两种模式.

模式 1 · 禁霓虹（默认，DECISIONS Q9）:
    python3 pipeline/gate_check_palette.py <png_path> ...
    HSL H ∈ [240°, 290°] (蓝紫色域) 像素占比 > threshold → FAIL

模式 2 · 声明式色板（--declared，纸片人 MV / 国乙 · 男团物料）:
    python3 pipeline/gate_check_palette.py --declared "#f8f4ea,#d4af37,#1b3a6b" frame.png
    检查成片主色是否落在「该风格包自己声明的色板」容差内,跑偏即 FAIL.

为什么要两种模式:
    模式 1 硬编码「蓝紫 = 违规」,它的立论是 Dracula 主题霓虹三件套
    (紫 #bd93f9 / 粉 #ff79c6 / 青 #8be9fd) 是 AI 工具类内容的视觉签名.
    但国乙角色主色本身就有一半在蓝/青/紫(萧逸深蓝 / 齐司礼青 / 查理苏紫),
    那是角色身份标识,不是套路色板——模式 1 会把正确配色判成违规.
    模式 2 把判据从「是不是暖的」换成「是不是它自己声明的那套」,
    对古风暖板包行为与模式 1 等价,同时能抓模式 1 抓不到的
    「没跑到蓝紫、但整体偏离了声明色板」的漂移.两种模式都 fail-closed.
"""
from __future__ import annotations

import argparse
import colorsys
import pathlib
import sys
from collections import Counter

import numpy as np
from PIL import Image

REAL_SCREENSHOT_HINTS = (
    "screenshot", "screen_grab", "real_", "wxchat_", "ios_",
    "android_", "douyin_native_", "xhs_native_",
)

VIOLET_HUE_LOW = 240 / 360
VIOLET_HUE_HIGH = 290 / 360

# 霓虹判据: Dracula 三件套实测饱和度 紫 #bd93f9 S=0.89 / 粉 #ff79c6 S=1.00 /
# 青 #8be9fd S=0.97。而低饱和的灰调紫(角色立绘的发色、缎面布料)实测 S=0.14~0.25,
# 与"AI 工具类内容视觉签名"毫无关系。本门叫「禁霓虹色」,判据里就必须有霓虹这一项。
NEON_SAT_MIN = 0.45


def is_real_screenshot(path: pathlib.Path) -> bool:
    s = str(path).lower()
    return any(h in s for h in REAL_SCREENSHOT_HINTS)


def analyze(
    path: pathlib.Path, sample: int = 4, neon_sat: float = NEON_SAT_MIN
) -> tuple[float, float, list[tuple[str, int]]]:
    """返回 (霓虹蓝紫占比, 低饱和蓝紫占比, 主色 top5 hex).

    sample: 下采样步长 (默认 4 = 1/16 像素, 1080x1920 → ~12 万像素采样).
    第二个返回值只作诊断打印,不参与 fail 判定——它是「画面里有多少灰调紫」,
    用于人眼复核,不该因为角色发色是薰衣草色就毙掉整帧.
    """
    img = Image.open(path).convert("RGB")
    pixels = list(img.getdata())[::sample * sample]
    neon = 0
    muted = 0
    bucket: Counter[tuple[int, int, int]] = Counter()
    for r, g, b in pixels:
        h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
        # 只统计有饱和度的像素(s>0.15 排除纯黑/白/灰)
        if s > 0.15 and l > 0.1 and l < 0.9 and VIOLET_HUE_LOW <= h <= VIOLET_HUE_HIGH:
            if s >= neon_sat:
                neon += 1
            else:
                muted += 1
        # 主色量化到 32 级
        bucket[(r >> 5 << 5, g >> 5 << 5, b >> 5 << 5)] += 1
    total = len(pixels)
    top5 = [(f"#{r:02x}{g:02x}{b:02x}", n) for (r, g, b), n in bucket.most_common(5)]
    if not total:
        return 0.0, 0.0, top5
    return neon / total, muted / total, top5


def parse_hex(spec: str) -> np.ndarray:
    """把 "#f8f4ea,#d4af37" 解析成 (N,3) uint8 RGB 数组."""
    out = []
    for token in spec.split(","):
        h = token.strip().lstrip("#")
        if len(h) != 6:
            raise ValueError(f"色板项格式错误: {token!r} (要 #rrggbb)")
        out.append([int(h[i:i + 2], 16) for i in (0, 2, 4)])
    if not out:
        raise ValueError("色板为空")
    return np.array(out, dtype=np.uint8)


def rgb_to_lab(rgb: np.ndarray) -> np.ndarray:
    """(N,3) uint8 sRGB → (N,3) float CIE Lab (D65)."""
    c = rgb.astype(np.float64) / 255
    lin = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    m = np.array([
        [0.4124564, 0.3575761, 0.1804375],
        [0.2126729, 0.7151522, 0.0721750],
        [0.0193339, 0.1191920, 0.9503041],
    ])
    xyz = lin @ m.T / np.array([0.95047, 1.0, 1.08883])
    eps = 216 / 24389
    kappa = 24389 / 27
    f = np.where(xyz > eps, np.cbrt(xyz), (kappa * xyz + 16) / 116)
    fx, fy, fz = f[:, 0], f[:, 1], f[:, 2]
    return np.stack([116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)], axis=1)


def analyze_declared(
    path: pathlib.Path,
    declared: np.ndarray,
    tolerance: float,
    sample: int = 4,
) -> tuple[float, list[tuple[str, float]]]:
    """返回 (跑偏像素占比, 偏得最狠的 top5 [(hex, ΔE)]).

    只对有饱和度的像素判定:中性色(黑边、留白、宣纸灰、阴影)是结构不是色板,
    任何风格包都用得到,不该因为「没在声明色板里」被判违规.
    """
    img = Image.open(path).convert("RGB")
    arr = np.asarray(img)[::sample, ::sample].reshape(-1, 3)

    mx = arr.max(axis=1).astype(np.int16)
    mn = arr.min(axis=1).astype(np.int16)
    chroma = mx - mn
    keep = (chroma > 30) & (mx > 25) & (mn < 245)
    if not keep.any():
        return 0.0, []
    pix = arr[keep]

    # 量化到 16 级去重,1080p 全帧 ~ 几千个唯一色,ΔE 矩阵才算得动
    quant = (pix >> 4 << 4).astype(np.uint8)
    uniq, counts = np.unique(quant, axis=0, return_counts=True)
    delta = np.linalg.norm(
        rgb_to_lab(uniq)[:, None, :] - rgb_to_lab(declared)[None, :, :], axis=2
    ).min(axis=1)

    off = delta > tolerance
    ratio = float(counts[off].sum() / counts.sum())
    top5 = []
    for i in np.argsort(-delta * counts * off)[:5]:
        if not off[i]:
            break
        r, g, b = uniq[i]
        top5.append((f"#{r:02x}{g:02x}{b:02x}", float(delta[i])))
    return ratio, top5


def main() -> int:
    ap = argparse.ArgumentParser(description="主视觉色域自检(禁霓虹 / 声明式色板)")
    ap.add_argument("paths", nargs="+", type=pathlib.Path)
    ap.add_argument("--declared", type=str, default=None,
                    help='声明式色板模式,逗号分隔 hex,如 "#f8f4ea,#d4af37,#1b3a6b"。'
                         "须含角色立绘自身主色与肤色(立绘像素不可改)")
    ap.add_argument("--tolerance", type=float, default=30.0,
                    help="声明式模式 ΔE76 容差,默认 30")
    ap.add_argument("--threshold", type=float, default=0.05,
                    help="违规像素占比阈值,默认 0.05 (5%%)")
    ap.add_argument("--sample", type=int, default=4,
                    help="下采样步长,默认 4")
    ap.add_argument("--strict", action="store_true",
                    help="真截屏路径例外也参与判定")
    ap.add_argument("--neon-sat", type=float, default=NEON_SAT_MIN,
                    help=f"霓虹饱和度下限,默认 {NEON_SAT_MIN}。"
                         "低于此值的蓝紫只诊断不判 fail(角色立绘的灰调紫发/缎面)")
    args = ap.parse_args()

    declared = parse_hex(args.declared) if args.declared else None
    label = "跑偏占比" if declared is not None else "霓虹蓝紫占比"
    gate = "声明式色板门" if declared is not None else "禁霓虹色门"

    failed: list[pathlib.Path] = []
    for path in args.paths:
        if not path.exists():
            print(f"  ⨯ {path}: 文件不存在", file=sys.stderr)
            failed.append(path)
            continue
        if not args.strict and is_real_screenshot(path):
            print(f"  ⏭ {path}: 真截屏例外,跳过")
            continue
        muted = None
        if declared is not None:
            ratio, worst = analyze_declared(
                path, declared, args.tolerance, sample=args.sample)
            detail = ", ".join(f"{h}(ΔE{d:.0f})" for h, d in worst) or "无"
        else:
            ratio, muted, top5 = analyze(
                path, sample=args.sample, neon_sat=args.neon_sat)
            detail = ", ".join(f"{h}×{n}" for h, n in top5)
        flag = "✗ FAIL" if ratio > args.threshold else "✓ OK"
        print(f"  {flag} {path}")
        print(f"     {label}: {ratio:.2%} (阈值 {args.threshold:.0%}"
              f"{'' if declared is not None else f', 饱和度 ≥{args.neon_sat}'})")
        if muted is not None and muted > args.threshold:
            print(f"     ⓘ 低饱和蓝紫: {muted:.2%} — 不判 fail,人眼复核是否为立绘自带色")
        print(f"     {'跑偏最狠' if declared is not None else '主色'} top5: {detail}")
        if ratio > args.threshold:
            failed.append(path)

    if failed:
        print(f"\n{gate} FAIL · {len(failed)}/{len(args.paths)} 张违规")
        if declared is not None:
            print("  → 改色回到风格包声明的色板,或改风格包的 palette 声明(要写清为什么)")
            print("  → 规则: .agents/skills/paperdoll-mv-packaging/SKILL.md R6")
        else:
            print("  → 改色,或确认是真截屏后改路径名加 screenshot/wxchat_ 一类标记")
            print("  → 规则: docs/DECISIONS.md Q9 「禁霓虹色细则」")
        return 1
    print(f"\n{gate} PASS · {len(args.paths)} 张全部 OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
