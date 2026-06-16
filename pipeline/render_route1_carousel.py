#!/usr/bin/env python3
"""路线 1 图文：各平台从 gen_evidence 素材复制 PNG.

  python3 pipeline/render_route1_carousel.py --all
  python3 pipeline/render_route1_carousel.py xhs-story douyin channels
"""
from __future__ import annotations

import argparse
import pathlib
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
GEN = ROOT / "pipeline" / "gen_evidence.py"
EVID = ROOT / "assets" / "broll" / "generated"
PUB = ROOT / "publish" / "P001"

# 各平台张数可不同，素材同源
SPECS: dict[str, tuple[pathlib.Path, list[str]]] = {
    "xhs-story": (
        PUB / "xhs" / "carousel_story",
        [
            "BR004_analytics_annotated.png",
            "MEMO01_background.png",
            "BR001_safari_landing.png",
            "STACK_submit_welcome.png",
            "BR004_day5_tagged.png",
            "BR006_ai_vs_manual.png",
            "MEMO02_cta.png",
        ],
    ),
    "douyin": (
        PUB / "douyin" / "carousel",
        [
            "BR004_analytics_annotated.png",
            "BR001_safari_landing.png",
            "STACK_submit_welcome.png",
            "BR004_day5_tagged.png",
            "BR006_ai_vs_manual.png",
            "MEMO02_cta.png",
        ],
    ),
    "channels": (
        PUB / "channels" / "carousel",
        [
            "BR004_analytics_annotated.png",
            "MEMO01_background.png",
            "STACK_submit_welcome.png",
            "BR004_day5_tagged.png",
            "BR006_ai_vs_manual.png",
            "MEMO02_cta.png",
        ],
    ),
}


def ensure_evidence(names: list[str]) -> None:
    missing = [n for n in names if not (EVID / n).exists()]
    if missing:
        print("缺素材，运行 gen_evidence.py …", missing)
        subprocess.run([sys.executable, str(GEN)], check=True)


def render(key: str) -> None:
    out_dir, slides = SPECS[key]
    ensure_evidence(slides)
    out_dir.mkdir(parents=True, exist_ok=True)
    for i, name in enumerate(slides, start=1):
        dst = out_dir / f"{i:02d}.png"
        shutil.copy2(EVID / name, dst)
        print(f"  [{key}] {dst.name} ← {name}")
    print(f"✓ {key}: {len(slides)} 张 → {out_dir}")


def main() -> None:
    ap = argparse.ArgumentParser(description="路线 1 图文渲染")
    ap.add_argument("platforms", nargs="*", choices=list(SPECS) + ["all"])
    ap.add_argument("--all", action="store_true", help="渲染全部平台")
    args = ap.parse_args()
    if args.all or not args.platforms:
        keys = list(SPECS)
    elif "all" in args.platforms:
        keys = list(SPECS)
    else:
        keys = args.platforms
    for k in keys:
        render(k)


if __name__ == "__main__":
    main()
