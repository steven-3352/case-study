#!/usr/bin/env python3
"""P007 · 小红书漫画轮播 · 渲最终静帧 PNG.

每个 slide 播放 GSAP 时间轴到末尾，导出一张 1080×1920 PNG。

用法:
  python3 pipeline/p007_xhs_engine_comic/capture_carousel.py --all
  python3 pipeline/p007_xhs_engine_comic/capture_carousel.py --slide slide_01

依赖: playwright (pip install playwright && playwright install chromium)
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time
from dataclasses import dataclass

import yaml
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent
TEMPLATES = ROOT / "templates"
OUT = ROOT / "out" / "carousel"


@dataclass(frozen=True)
class SlideSpec:
    id: str
    template: str
    duration: float
    data: dict


def load_storyboard(path: pathlib.Path) -> tuple[dict, list[SlideSpec]]:
    with path.open(encoding="utf-8") as f:
        sb = yaml.safe_load(f)
    slides = [
        SlideSpec(
            id=s["id"],
            template=s["template"],
            duration=float(s["duration"]),
            data=s.get("data", {}) or {},
        )
        for s in sb.get("slides", [])
    ]
    return sb.get("video", {}), slides


def capture_slide(page, slide: SlideSpec, video_cfg: dict) -> pathlib.Path:
    width = int(video_cfg.get("width", 1080))
    height = int(video_cfg.get("height", 1920))

    OUT.mkdir(parents=True, exist_ok=True)
    out_path = OUT / f"{slide.id}.png"

    template_path = TEMPLATES / slide.template
    if not template_path.exists():
        sys.exit(f"找不到模板 {template_path}")

    page.add_init_script("window.__data = " + json.dumps(slide.data, ensure_ascii=False) + ";")
    page.goto(template_path.resolve().as_uri())
    page.wait_for_function("() => window.__timeline !== null", timeout=15000)
    page.wait_for_load_state("networkidle", timeout=15000)

    t_end = max(0.1, slide.duration - 0.05)
    page.evaluate(f"window.__renderFrame({t_end})")
    page.wait_for_timeout(100)

    page.screenshot(
        path=str(out_path),
        clip={"x": 0, "y": 0, "width": width, "height": height},
        animations="disabled",
    )
    print(f"  ✓ {out_path.name}")
    return out_path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--storyboard", type=pathlib.Path, default=ROOT / "storyboard_carousel.yaml")
    ap.add_argument("--slide", help="只渲指定 slide id")
    ap.add_argument("--all", action="store_true")
    args = ap.parse_args()

    if not args.slide and not args.all:
        sys.exit("请指定 --all 或 --slide <id>")

    video_cfg, slides = load_storyboard(args.storyboard.resolve())
    if args.slide:
        slides = [s for s in slides if s.id == args.slide]
        if not slides:
            sys.exit(f"storyboard 里没有 slide id={args.slide}")

    print(f"导出 {len(slides)} 张漫画轮播图 → {OUT}")
    t0 = time.time()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--font-render-hinting=none"])
        ctx = browser.new_context(
            viewport={
                "width": int(video_cfg.get("width", 1080)),
                "height": int(video_cfg.get("height", 1920)),
            },
            device_scale_factor=1,
            locale="zh-CN",
        )
        page = ctx.new_page()
        for slide in slides:
            capture_slide(page, slide, video_cfg)
        browser.close()

    print(f"完成 / {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
