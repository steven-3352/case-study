#!/usr/bin/env python3
"""Playwright · 把 HTML+GSAP 模板按帧渲成 PNG 序列(并行 + 去重).

每个模板需要:
  1. 引入 shared/gsap_helpers.js
  2. 末尾构建 paused 的 gsap.timeline 并调 registerTimeline(tl)
  3. 通过 window.__data 读取参数(由本脚本注入)

提速原理(均不改变输出像素):
  · 并行 — window.__renderFrame(t) 是对 paused timeline 的确定性 seek,
    第 i 帧只依赖 t=i/fps、帧间无状态。每个 scene 分到独立进程+独立
    Chromium page 并行截帧,产出逐字节相同。
  · 去重 — 若模板定义 window.__contentKey(),仅在 key 变化时真截图,
    其余帧硬链(os.link)到上一张。key 完整决定可见像素时,硬链与重截
    像素一致(如字幕层:透明间隙 / 静态保持帧大量重复)。

用法:
  python3 pipeline/p004_video/capture_frames.py --all
  python3 pipeline/p004_video/capture_frames.py --scene 01_hook
  python3 pipeline/p004_video/capture_frames.py \\
      --template _subtitles.html --duration 55.42 --out-id _subtitles --transparent
  # 并行度默认 = min(CPU, 任务数);--workers 1 退回串行
"""
from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import os
import pathlib
import shutil
import sys
import time
from dataclasses import dataclass

import yaml

ROOT = pathlib.Path(__file__).resolve().parent
TEMPLATES = ROOT / "templates"
FRAMES_OUT = ROOT / "out" / "frames"


@dataclass(frozen=True)
class SceneSpec:
    id: str
    template: str
    duration: float
    data: dict
    type: str = "html"          # html | broll
    source: str | None = None   # broll 模式: 源视频路径(相对 PROJECT_ROOT)
    source_in: float = 0.0      # broll 模式: 切起点(秒)


@dataclass(frozen=True)
class CaptureJob:
    """一个独立可并行的截帧任务(一个 scene 或单模板)。"""
    out_id: str
    template: str
    duration: float
    data: dict
    width: int
    height: int
    fps: int
    transparent: bool = False
    dedup: bool = True          # 模板定义 __contentKey 时才实际生效


def load_storyboard(path: pathlib.Path) -> tuple[dict, list[SceneSpec]]:
    with path.open(encoding="utf-8") as f:
        sb = yaml.safe_load(f)
    scenes = [
        SceneSpec(
            id=s["id"],
            template=s.get("template", ""),
            duration=float(s["duration"]),
            data=s.get("data", {}) or {},
            type=s.get("type", "html"),
            source=s.get("source"),
            source_in=float(s.get("source_in", 0.0)),
        )
        for s in sb.get("scenes", [])
    ]
    return sb.get("video", {}), scenes


def _run_job(job: CaptureJob) -> str:
    """单进程内渲一个任务的全部帧。被进程池调用,故所有依赖在函数内导入。"""
    from playwright.sync_api import sync_playwright

    template_path = TEMPLATES / job.template
    if not template_path.exists():
        raise SystemExit(f"找不到模板 {template_path}")

    out_dir = FRAMES_OUT / job.out_id
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    n_frames = int(round(job.duration * job.fps))
    clip = {"x": 0, "y": 0, "width": job.width, "height": job.height}

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True, args=["--font-render-hinting=none"]
        )
        ctx = browser.new_context(
            viewport={"width": job.width, "height": job.height},
            device_scale_factor=1,
            reduced_motion="no-preference",
            locale="zh-CN",
        )
        page = ctx.new_page()
        page.add_init_script(
            "window.__data = " + json.dumps(job.data, ensure_ascii=False) + ";"
        )
        page.goto(template_path.resolve().as_uri())

        page.wait_for_function("() => window.__timeline !== null", timeout=15000)
        page.wait_for_load_state("networkidle", timeout=15000)
        page.wait_for_function(
            "() => Array.from(document.images).every(img => img.complete)",
            timeout=15000,
        )

        has_key = bool(
            job.dedup
            and page.evaluate("() => typeof window.__contentKey === 'function'")
        )

        t0 = time.time()
        sentinel = object()
        last_key: object = sentinel
        last_path: pathlib.Path | None = None
        shots = 0

        for i in range(n_frames):
            t = i / job.fps
            page.evaluate("(t) => window.__renderFrame(t)", t)
            page.wait_for_timeout(0)
            out_path = out_dir / f"frame_{i:04d}.png"

            if has_key:
                key = page.evaluate("() => window.__contentKey()")
                if key == last_key and last_path is not None:
                    # 像素与上一张完全相同 → 硬链复用,省一次截图与一份磁盘
                    try:
                        os.link(last_path, out_path)
                    except OSError:
                        shutil.copyfile(last_path, out_path)
                    continue
                last_key = key

            page.screenshot(
                path=str(out_path),
                clip=clip,
                omit_background=job.transparent,
                animations="disabled",
            )
            last_path = out_path
            shots += 1

        dt = time.time() - t0
        browser.close()

    extra = f" · 实截 {shots}/{n_frames}(去重)" if has_key else ""
    rate = n_frames / dt if dt > 0 else 0.0
    return f"  ✓ {job.out_id}: {n_frames} 帧 / {dt:.1f}s ({rate:.1f} fps){extra}"


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
    ap.add_argument("--transparent", action="store_true",
                    help="透明背景截图(字幕层用)")
    ap.add_argument("--workers", type=int, default=0,
                    help="并行进程数(默认 = min(CPU, 任务数);1 = 串行)")
    ap.add_argument("--no-dedup", action="store_true",
                    help="禁用 __contentKey 去重(逐帧全截)")
    args = ap.parse_args()

    # 单模板模式
    if args.template:
        if not args.duration:
            sys.exit("单模板模式需要 --duration")
        out_id = args.out_id or args.template.replace(".html", "")
        jobs = [CaptureJob(
            out_id=out_id, template=args.template, duration=args.duration,
            data={}, width=1080, height=1920, fps=30,
            transparent=args.transparent, dedup=not args.no_dedup,
        )]
    else:
        if not args.scene and not args.all:
            sys.exit("请指定 --scene <id> 或 --all 或 --template <html>")
        video_cfg, scenes = load_storyboard(args.storyboard.resolve())
        if args.scene:
            scenes = [s for s in scenes if s.id == args.scene]
            if not scenes:
                sys.exit(f"storyboard 里没有 scene id={args.scene}")
        # broll 不截帧(后期由 build.py 切源视频)
        html_scenes = [s for s in scenes if s.type != "broll"]
        for s in scenes:
            if s.type == "broll":
                print(f"  ⏭  {s.id}: broll 模式,跳过截帧 (source={s.source})")
        jobs = [
            CaptureJob(
                out_id=s.id,
                template=s.template, duration=s.duration, data=s.data,
                width=int(video_cfg.get("width", 1080)),
                height=int(video_cfg.get("height", 1920)),
                fps=int(video_cfg.get("fps", 30)),
                transparent=args.transparent, dedup=not args.no_dedup,
            )
            for s in html_scenes
        ]

    if not jobs:
        print("没有需要截帧的 scene")
        return

    workers = args.workers or min(os.cpu_count() or 1, len(jobs))
    print(f"开始截帧 {len(jobs)} 个任务 · 并行 {workers}")

    t0 = time.time()
    if workers <= 1 or len(jobs) == 1:
        for job in jobs:
            print(_run_job(job))
    else:
        ctx = mp.get_context("spawn")
        with ctx.Pool(workers) as pool:
            for msg in pool.imap_unordered(_run_job, jobs):
                print(msg)

    print(f"全部完成 · 截帧总耗时 {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
