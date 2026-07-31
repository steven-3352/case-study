"""原子回归锁 —— 固定输入 × 固定参数 → sha256 摘要。

**为什么和 `pipeline/paperdoll/probes.py` 是两件事**:

- `probes.py` 的 `check_*` 管**效果够不够强**(判据是度量值,阈值是地板)。
- 本模块管**行为有没有变**(判据是逐字节相等,没有阈值)。

跨片复用的前提是敢改,敢改的前提是改坏了立刻有人喊。本模块就是那个喊的人。

**输入是本模块自己造的,不复用 `probes.neutral_bed()`** —— 锁的输入一旦会随
别的模块演进而变,它就不是锁了,只是又一个会漂的测试。造出来的图是确定的:
无随机数,全部由 `np.arange` / 常量算出。

摘要一律先 clip 到 uint8 再哈希:float 尾数在不同 BLAS 后端下可能差最低位,
而那一位在画面上不存在。锁要锁的是画面,不是浮点表示。

用法::

    python3 -m mvstudio.engines.mv.atoms.lock --write src/mvstudio/engines/mv/atoms/lock.json
    python3 -m mvstudio.engines.mv.atoms.lock --check src/mvstudio/engines/mv/atoms/lock.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Callable

import numpy as np
from PIL import Image

from . import _contract
from .ease import _compress, fold_press
from .geometry import solve_perspective
from .motion import jam_smear
from .optical import banding, lid_flare, scan_bar
from .paper import crease, paper_fold, stack_edge

W, H = 240, 135
INK = (38, 34, 30)
LINE = (214, 90, 60)
DARK = (26, 30, 44)


def _bed() -> np.ndarray:
    """确定性中性底 + 一道横向渐变 + 一个非对称剪影。

    非对称是有意的:左右对称的图形量不出方向性的原子(jam_smear / scan_bar
    的 direction 传反了也照样过)。
    """
    x = np.linspace(0.0, 1.0, W)[None, :, None]
    y = np.linspace(0.0, 1.0, H)[:, None, None]
    bed = 96.0 + 64.0 * x + 24.0 * y
    bed = np.repeat(bed, 3, axis=2)
    bed[:, :, 2] += 18.0
    yy, xx = np.mgrid[0:H, 0:W]
    head = ((xx - W * 0.44) ** 2 + (yy - H * 0.30) ** 2) < (H * 0.14) ** 2
    body = (yy > H * 0.42) & (xx > W * 0.34) & (xx < W * 0.62) & (yy < H * 0.86)
    bed[head | body] = np.asarray(INK, dtype=float)
    return np.clip(bed, 0, 255)


def _rgba() -> Image.Image:
    """确定性 RGBA 印张 —— 给改 alpha 的原子用,四角 alpha 不同以便看出翻折方向。"""
    a = _bed().astype(np.uint8)
    im = Image.fromarray(a, "RGB").convert("RGBA")
    x = np.linspace(60.0, 255.0, W)[None, :]
    y = np.linspace(255.0, 140.0, H)[:, None]
    im.putalpha(Image.fromarray(np.minimum(x, y).astype(np.uint8), "L"))
    return im


def _h(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()[:32]


def _arr(a: np.ndarray) -> str:
    return _h(np.clip(np.asarray(a, dtype=float), 0, 255).astype(np.uint8).tobytes())


def _img(im: Image.Image) -> str:
    return _h(f"{im.size}|{im.mode}|".encode() + im.tobytes())


def _nums(v) -> str:
    return _h(json.dumps([round(float(q), 9) for q in np.ravel(v)]).encode())


def _canvas(fn: Callable, **kw) -> str:
    c = _rgba()
    fn(c, **kw)
    return _img(c)


CASES: dict[str, Callable[[], str]] = {
    "scan_bar": lambda: _arr(scan_bar(
        _bed(), y_frac=0.37, width_px=5, glow_radius_px=22, glow_color=LINE,
        glow_alpha=0.66, direction="down", scanned_brightness_add=0.08)),
    "scan_bar/right": lambda: _arr(scan_bar(
        _bed(), y_frac=0.61, width_px=3, glow_radius_px=14, glow_color=LINE,
        glow_alpha=0.5, direction="right")),
    "banding": lambda: _arr(banding(
        _bed(), t=1.37, frequency=48.0, amplitude=0.09, scroll_speed=34.0)),
    "lid_flare": lambda: _arr(lid_flare(
        _bed(), intensity=0.72, gradient_falloff=2.4, color=LINE, bloom_radius_px=7)),
    "jam_smear": lambda: _arr(jam_smear(
        _bed(), smear_amount_px=40, smear_start_frac=0.44, falloff=2.2, alpha=0.85)),
    "jam_smear/horizontal": lambda: _arr(jam_smear(
        _bed(), smear_amount_px=30, smear_start_frac=0.28, falloff=1.5,
        alpha=0.7, direction="horizontal")),
    "solve_perspective": lambda: _nums(solve_perspective(
        [(0, 0), (W, 0), (W, H), (0, H)],
        [(11, 4), (W - 6, 19), (W - 23, H - 3), (7, H - 14)])),
    "fold_press": lambda: _nums([fold_press(i / 64.0) for i in range(65)]),
    "_compress": lambda: _nums([_compress(n) for n in range(1, 13)]),
    "paper_fold/1": lambda: _img(paper_fold(_rgba(), 1)),
    "paper_fold/5": lambda: _img(paper_fold(_rgba(), 5)),
    "crease/vertical": lambda: _canvas(
        crease, frac=0.5, axis="vertical", highlight_color=(240, 236, 228),
        shadow_color=DARK, highlight_width_px=3, shadow_width_px=9,
        highlight_alpha=0.9, shadow_alpha=0.55),
    "crease/horizontal": lambda: _canvas(
        crease, frac=0.33, axis="horizontal", highlight_color=(240, 236, 228),
        shadow_color=DARK, highlight_width_px=2, shadow_width_px=6,
        highlight_alpha=0.75, shadow_alpha=0.4),
    "stack_edge": lambda: _canvas(
        stack_edge, x0=40, y0=24, x1=190, y1=110, fold_count=6,
        base_thickness_px=0.9, edge_color=(228, 222, 210), side="right",
        shadow_color=DARK),
    "stack_edge/bottom": lambda: _canvas(
        stack_edge, x0=40, y0=24, x1=190, y1=110, fold_count=3,
        base_thickness_px=1.4, edge_color=(228, 222, 210), side="bottom",
        shadow_color=DARK),
}


def run() -> dict[str, str]:
    return {k: fn() for k, fn in sorted(CASES.items())}


def uncovered() -> list[str]:
    """登记了却没有任何 case 覆盖的原子 —— 契约第 4 条靠这个兜底。"""
    covered = {k.split("/", 1)[0] for k in CASES}
    return sorted(set(_contract.REGISTRY) - covered)


def main() -> int:
    ap = argparse.ArgumentParser(description="原子回归锁")
    ap.add_argument("--write", type=Path)
    ap.add_argument("--check", type=Path)
    args = ap.parse_args()

    missing = uncovered()
    got = run()
    print(f"{len(got)} 个 case · {len(_contract.REGISTRY)} 个已登记原子")
    if missing:
        print(f"✗ 未被探针覆盖的原子: {missing}")
        return 1

    if args.write:
        args.write.write_text(json.dumps(got, indent=1, sort_keys=True, ensure_ascii=False))
        print(f"→ {args.write}")

    if args.check:
        want = json.loads(args.check.read_text())
        bad = [k for k in sorted(set(want) | set(got)) if want.get(k) != got.get(k)]
        if bad:
            print(f"\n✗ {len(bad)} 个 case 变了:")
            for k in bad:
                print(f"  {k}: {want.get(k)} → {got.get(k)}")
            return 1
        print("✓ 原子行为逐字节未变")
    return 0


if __name__ == "__main__":
    sys.exit(main())
