#!/usr/bin/env python3
"""Build W27D02 OpenMontage local surrogate preview.

This script is intentionally scoped to the trial directory. It does not modify
the main pipeline or overwrite the platform video.
"""

from __future__ import annotations

import asyncio
import json
import pathlib
import shutil
import subprocess
import sys
from dataclasses import dataclass

from playwright.async_api import async_playwright


ROOT = pathlib.Path(__file__).resolve().parents[4]
PACKAGE = ROOT / "publish" / "2026-W27" / "D02-会议纪要"
OUT = PACKAGE / "openmontage"
SCENES = OUT / "scenes"
ASSETS = ROOT / "assets" / "characters" / "w27d02"
ORIGINAL = PACKAGE / "douyin" / "video_with_bgm.mp4"


@dataclass(frozen=True)
class Scene:
    idx: int
    name: str
    duration: float
    bg: pathlib.Path
    label: str
    title: str
    subtitle: str
    cards: tuple[str, ...]
    mode: str = "normal"


SCENE_DATA = [
    Scene(
        1,
        "01_hook",
        3.0,
        ASSETS / "meeting_room.png",
        "0-3s / 停划",
        "散会了",
        "同事还在写纪要，我直接走了",
        ("群里叮一声", "纪要 + 待办 已自动发出"),
    ),
    Scene(
        2,
        "02_minutes",
        8.0,
        ASSETS / "meeting_room.png",
        "3-11s / 纪要已发群",
        "不是摆烂",
        "纪要和待办，群里早自动发好了",
        ("会议主题：本周项目同步", "决策：方案 A 先跑", "要点：风险、负责人、时间节点"),
    ),
    Scene(
        3,
        "03_todos",
        11.0,
        ASSETS / "test_worker.png",
        "11-22s / 待办追办",
        "AI 全程在听",
        "谁负责、什么时候交，自动 @ 到人",
        ("@ 小周  明晚 20:00 交初稿", "@ 小林  周五前补数据", "@ 我  今天同步结论"),
    ),
    Scene(
        4,
        "04_contrast",
        8.0,
        ASSETS / "tired.png",
        "22-30s / 反差",
        "以前会后才是噩梦",
        "整理纪要、追进度、催 deadline",
        ("旧流程：回放录音 + 熬夜整理", "新流程：散会即同步 + 到期提醒"),
        "split",
    ),
    Scene(
        5,
        "05_cta",
        10.0,
        ASSETS / "me_phone.png",
        "30-40s / 自证 + CTA",
        "我只管讨论拍板",
        "记录和追办，交给它",
        ("你们公司开会，纪要是谁整理？", "是不是最烦的活？评论区说说"),
    ),
]


def run(cmd: list[str], cwd: pathlib.Path | None = None) -> None:
    print(" ".join(cmd[:4]), "...")
    res = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)
    if res.returncode != 0:
        print(res.stdout)
        print(res.stderr)
        raise SystemExit(res.returncode)


def rel(path: pathlib.Path) -> str:
    return path.resolve().as_uri()


def html(scene: Scene) -> str:
    bg2 = rel(ASSETS / "relaxed.png") if scene.mode == "split" else ""
    cards = "".join(f"<li>{c}</li>" for c in scene.cards)
    split = ""
    if scene.mode == "split":
        split = f"""
        <div class="split">
          <div class="pane bad"><img src="{rel(scene.bg)}"><b>旧流程</b></div>
          <div class="pane good"><img src="{bg2}"><b>新流程</b></div>
        </div>
        """
    else:
        split = f'<img class="hero" src="{rel(scene.bg)}">'

    return f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<style>
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    width: 1080px;
    height: 1920px;
    overflow: hidden;
    font-family: "PingFang SC", "Hiragino Sans", Arial, sans-serif;
    background: #f6f7f9;
    color: #17202a;
  }}
  .stage {{
    position: relative;
    width: 1080px;
    height: 1920px;
    overflow: hidden;
    background: linear-gradient(180deg, #f6f7f9 0%, #e9eef5 100%);
  }}
  .hero {{
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    object-fit: cover;
    filter: saturate(1.04) contrast(1.02);
  }}
  .shade {{
    position: absolute;
    inset: 0;
    background: linear-gradient(180deg, rgba(246,247,249,.10) 0%, rgba(246,247,249,.35) 45%, rgba(23,32,42,.48) 100%);
  }}
  .label {{
    position: absolute;
    left: 56px;
    top: 64px;
    padding: 14px 22px;
    border-radius: 999px;
    background: #ffffff;
    color: #1f7aff;
    font-size: 30px;
    font-weight: 800;
    box-shadow: 0 14px 38px rgba(17, 24, 39, .16);
  }}
  .headline {{
    position: absolute;
    left: 56px;
    right: 56px;
    bottom: 500px;
    color: #ffffff;
    text-shadow: 0 10px 30px rgba(0,0,0,.45);
  }}
  h1 {{
    margin: 0 0 18px;
    font-size: 86px;
    line-height: 1.05;
    letter-spacing: 0;
  }}
  .sub {{
    font-size: 50px;
    font-weight: 800;
    line-height: 1.18;
  }}
  .card {{
    position: absolute;
    left: 56px;
    right: 56px;
    bottom: 90px;
    background: rgba(255,255,255,.96);
    border-radius: 28px;
    box-shadow: 0 22px 60px rgba(17,24,39,.25);
    padding: 34px 38px;
    border-left: 14px solid #1f7aff;
  }}
  .card ul {{
    margin: 0;
    padding: 0;
    list-style: none;
  }}
  .card li {{
    margin: 16px 0;
    padding: 18px 22px;
    border-radius: 18px;
    background: #f6f7f9;
    font-size: 38px;
    line-height: 1.25;
    font-weight: 700;
  }}
  .card li:nth-child(2) {{ color: #1f7aff; }}
  .card li:nth-child(3) {{ color: #18a058; }}
  .split {{
    position: absolute;
    inset: 0;
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0;
  }}
  .pane {{
    position: relative;
    overflow: hidden;
  }}
  .pane img {{
    width: 100%;
    height: 100%;
    object-fit: cover;
  }}
  .pane::after {{
    content: "";
    position: absolute;
    inset: 0;
    background: linear-gradient(180deg, rgba(0,0,0,.02), rgba(0,0,0,.48));
  }}
  .pane b {{
    position: absolute;
    z-index: 2;
    left: 34px;
    bottom: 610px;
    padding: 14px 20px;
    border-radius: 16px;
    color: white;
    font-size: 38px;
  }}
  .pane.bad b {{ background: #ef4444; }}
  .pane.good b {{ background: #18a058; }}
</style>
</head>
<body>
  <div class="stage">
    {split}
    <div class="shade"></div>
    <div class="label">{scene.label}</div>
    <div class="headline">
      <h1>{scene.title}</h1>
      <div class="sub">{scene.subtitle}</div>
    </div>
    <div class="card"><ul>{cards}</ul></div>
  </div>
</body>
</html>"""


async def render_scene_pngs() -> None:
    SCENES.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--font-render-hinting=none"])
        ctx = await browser.new_context(
            viewport={"width": 1080, "height": 1920},
            device_scale_factor=1,
            locale="zh-CN",
        )
        page = await ctx.new_page()
        for scene in SCENE_DATA:
            html_path = SCENES / f"{scene.name}.html"
            html_path.write_text(html(scene), encoding="utf-8")
            await page.goto(html_path.resolve().as_uri())
            await page.wait_for_load_state("networkidle")
            await page.screenshot(path=str(SCENES / f"{scene.name}.png"), full_page=True)
        await browser.close()


def make_scene_videos() -> list[pathlib.Path]:
    outputs: list[pathlib.Path] = []
    for scene in SCENE_DATA:
        img = SCENES / f"{scene.name}.png"
        out = SCENES / f"{scene.name}.mp4"
        run([
            "ffmpeg", "-y",
            "-loop", "1",
            "-t", f"{scene.duration:.3f}",
            "-i", str(img),
            "-vf", "scale=1080:1920:flags=lanczos,format=yuv420p",
            "-r", "30",
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "18",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            str(out),
        ])
        outputs.append(out)
    return outputs


def concat_and_audio(scene_videos: list[pathlib.Path]) -> None:
    concat = SCENES / "concat.txt"
    concat.write_text("".join(f"file '{p.resolve()}'\n" for p in scene_videos), encoding="utf-8")
    silent = OUT / "preview_silent.mp4"
    run([
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat),
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        str(silent),
    ])
    preview = OUT / "preview.mp4"
    run([
        "ffmpeg", "-y",
        "-i", str(silent),
        "-i", str(ORIGINAL),
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-t", "40",
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        "-movflags", "+faststart",
        str(preview),
    ])
    shutil.copyfile(preview, OUT / "final.mp4")


async def main() -> None:
    missing = [str(s.bg) for s in SCENE_DATA if not s.bg.exists()]
    if missing:
        raise SystemExit("Missing assets: " + json.dumps(missing, ensure_ascii=False))
    if not ORIGINAL.exists():
        raise SystemExit(f"Missing original audio source: {ORIGINAL}")
    await render_scene_pngs()
    videos = make_scene_videos()
    concat_and_audio(videos)
    print(f"wrote {OUT / 'preview.mp4'}")
    print(f"wrote {OUT / 'final.mp4'}")


if __name__ == "__main__":
    asyncio.run(main())
