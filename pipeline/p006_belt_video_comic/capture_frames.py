#!/usr/bin/env python3
"""Playwright · 把 HTML+GSAP 模板按帧渲成 PNG 序列.

每个模板需要:
  1. 引入 shared/gsap_helpers.js
  2. 末尾构建 paused 的 gsap.timeline 并调 registerTimeline(tl)
  3. 通过 window.__data 读取参数(由本脚本注入)

用法:
  python3 pipeline/p004_video/capture_frames.py \\
      --storyboard pipeline/p004_video/storyboard.yaml \\
      --scene 01_hook                         # 只渲一个
  python3 pipeline/p004_video/capture_frames.py --all
"""
from __future__ import annotations

import argparse
import json
import pathlib
import shutil
import sys
import time
from dataclasses import dataclass

import yaml
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent
TEMPLATES = ROOT / "templates"
FRAMES_OUT = ROOT / "out" / "frames"


@dataclass(frozen=True)
class SceneSpec:
    id: str
    template: str
    duration: float
    data: dict


def load_storyboard(path: pathlib.Path) -> tuple[dict, list[SceneSpec]]:
    with path.open(encoding="utf-8") as f:
        sb = yaml.safe_load(f)
    scenes = [
        SceneSpec(
            id=s["id"],
            template=s["template"],
            duration=float(s["duration"]),
            data=s.get("data", {}) or {},
        )
        for s in sb.get("scenes", [])
    ]
    return sb.get("video", {}), scenes


def capture_scene(page, scene: SceneSpec, video_cfg: dict, transparent: bool = False) -> int:
    fps = int(video_cfg.get("fps", 30))
    width = int(video_cfg.get("width", 1080))
    height = int(video_cfg.get("height", 1920))

    out_dir = FRAMES_OUT / scene.id
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    template_path = TEMPLATES / scene.template
    if not template_path.exists():
        sys.exit(f"找不到模板 {template_path}")

    # 注入参数 - addInitScript 在每次 navigate 前运行
    data_js = "window.__data = " + json.dumps(scene.data, ensure_ascii=False) + ";"
    page.add_init_script(data_js)

    url = template_path.resolve().as_uri()
    page.goto(url)

    # 等待 GSAP timeline 注册完成
    page.wait_for_function("() => window.__timeline !== null", timeout=15000)

    # 等字体/图片加载完
    page.wait_for_load_state("networkidle", timeout=15000)
    page.wait_for_function(
        "() => Array.from(document.images).every(img => img.complete)",
        timeout=15000,
    )

    n_frames = int(round(scene.duration * fps))
    print(f"  渲染 {scene.id}: {n_frames} 帧 @ {fps}fps × {scene.duration}s"
          + (" · 透明" if transparent else ""))

    t0 = time.time()
    for i in range(n_frames):
        t = i / fps
        page.evaluate(f"window.__renderFrame({t})")
        page.wait_for_timeout(0)
        out_path = out_dir / f"frame_{i:04d}.png"
        page.screenshot(
            path=str(out_path),
            clip={"x": 0, "y": 0, "width": width, "height": height},
            omit_background=transparent,
            animations="disabled",
        )
    dt = time.time() - t0
    print(f"  ✓ {scene.id}: {n_frames} 帧 / {dt:.1f}s ({n_frames/dt:.1f} fps)")
    return n_frames


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--storyboard", type=pathlib.Path,
                    default=ROOT / "storyboard.yaml")
    ap.add_argument("--scene", help="只渲指定 scene id,例如 01_hook")
    ap.add_argument("--all", action="store_true", help="渲所有 scene")
    # 单模板模式 · 用于字幕层等不在 storyboard 里的场景
    ap.add_argument("--template", help="单个 HTML 模板文件名 (在 templates/ 下)")
    ap.add_argument("--duration", type=float, help="单模板模式的时长(秒)")
    ap.add_argument("--out-id", help="单模板模式的输出目录名 (默认从 --template 取)")
    ap.add_argument("--transparent", action="store_true", help="透明背景截图(字幕层用)")
    args = ap.parse_args()

    # 单模板模式
    if args.template:
        if not args.duration:
            sys.exit("单模板模式需要 --duration")
        out_id = args.out_id or args.template.replace(".html", "")
        scenes = [SceneSpec(id=out_id, template=args.template,
                            duration=args.duration, data={})]
        # 缺省 video_cfg
        video_cfg = {"width": 1080, "height": 1920, "fps": 30}
    else:
        if not args.scene and not args.all:
            sys.exit("请指定 --scene <id> 或 --all 或 --template <html>")
        video_cfg, scenes = load_storyboard(args.storyboard.resolve())
        if args.scene:
            scenes = [s for s in scenes if s.id == args.scene]
            if not scenes:
                sys.exit(f"storyboard 里没有 scene id={args.scene}")

    print(f"开始截帧 {len(scenes)} 个 scene")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--font-render-hinting=none"])
        ctx = browser.new_context(
            viewport={"width": int(video_cfg.get("width", 1080)),
                      "height": int(video_cfg.get("height", 1920))},
            device_scale_factor=1,
            reduced_motion="no-preference",
            locale="zh-CN",
        )
        page = ctx.new_page()
        for scene in scenes:
            capture_scene(page, scene, video_cfg, transparent=args.transparent)
        browser.close()

    print("全部完成")


if __name__ == "__main__":
    main()
