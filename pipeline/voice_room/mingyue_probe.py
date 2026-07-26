#!/usr/bin/env python3
"""样段抽帧探针 —— 每镜取几帧拼一张联络表,供调参时快速目视。

全片 219 帧渲一次 4 分半,改一个参数等一轮太慢;本工具按 shot 抽帧,
默认每镜 2 帧,十几秒出一张联络表。**不是验收工具** —— 验收看全片。
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))

import mingyue_render as R  # noqa: E402
import paperdoll_engine as pe  # noqa: E402


def probe(version: str, per_shot: int, cols: int, out: Path) -> None:
    shots = R.A_SHOTS if version == "a" else R.B_SHOTS
    picks = []
    for sh in shots:
        for i in range(per_shot):
            f = (i + 0.5) / per_shot
            picks.append((sh.sid, sh.t0 + f * (sh.t1 - sh.t0)))

    tw, th = 480, 270
    rows = (len(picks) + cols - 1) // cols
    sheet = Image.new("RGB", (tw * cols, th * rows), (16, 16, 16))
    for n, (sid, t) in enumerate(picks):
        im, _ = R.render_frame(t, shots, version)
        im = im.resize((tw, th), Image.LANCZOS)
        ImageDraw.Draw(im).text((8, 6), f"{sid} {t:.2f}", fill=(255, 60, 60))
        sheet.paste(im, (tw * (n % cols), th * (n // cols)))
    sheet.save(out)
    print(f"{out}  {len(picks)} 帧")


def main() -> int:
    ap = argparse.ArgumentParser(description="抽帧联络表")
    ap.add_argument("--version", default="a", choices=["a", "b"])
    ap.add_argument("--per-shot", type=int, default=2)
    ap.add_argument("--cols", type=int, default=4)
    ap.add_argument("--out", default="/tmp/probe.png")
    a = ap.parse_args()
    pe._PATHS = pe.PVPaths(assets_dir=R.ASSETS, wav=R.WAV, out_dir=R.OUT, slug="mingyue")
    probe(a.version, a.per_shot, a.cols, Path(a.out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
