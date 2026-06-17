#!/usr/bin/env python3
"""一条命令产线 · GitHub 项目 → 三平台短视频成品.

阶段：ingest → author → shoot → render → publish。
各阶段独立可跑；产物已存在则跳过（--force 全量重跑）。

用法:
  python3 pipeline/produce.py --id P002 \
      --github https://github.com/owner/repo \
      --demo   https://demo.example.com \
      --note   "一句话定位（可选）"

需要仓库根目录 `.env` 中的 ANTHROPIC_API_KEY（或 `ant auth login`）；自然 TTS 见 pipeline/tts/config.yaml。
"""
from __future__ import annotations

import argparse
import pathlib
import subprocess
import sys

import pipeline.env_loader  # noqa: F401 — 加载 .env

ROOT = pathlib.Path(__file__).resolve().parents[1]
PY = sys.executable


def run(stage: str, cmd: list[str]) -> None:
    print(f"\n========== {stage} ==========")
    r = subprocess.run([PY, *cmd])
    if r.returncode != 0:
        sys.exit(f"✗ {stage} 失败（退出码 {r.returncode}）")


def main() -> None:
    ap = argparse.ArgumentParser(description="一条命令：项目 → 三平台短视频")
    ap.add_argument("--id", required=True)
    ap.add_argument("--github", required=True)
    ap.add_argument("--demo", default="")
    ap.add_argument("--note", default="")
    ap.add_argument("--platform", nargs="*", choices=["douyin", "xhs", "channels"])
    ap.add_argument("--skip-research", action="store_true")
    ap.add_argument("--force", action="store_true", help="忽略已存在产物，全量重跑")
    args = ap.parse_args()

    proj = ROOT / "projects" / args.id
    P = lambda *a: str(ROOT / "pipeline" / a[0])  # noqa: E731
    plat_args = (["--platform", *args.platform] if args.platform else [])

    # ① ingest
    if args.force or not (proj / "context.md").exists():
        cmd = ["ingest.py", "--id", args.id, "--github", args.github]
        if args.demo:
            cmd += ["--demo", args.demo]
        if args.note:
            cmd += ["--note", args.note]
        if args.force:
            cmd += ["--force"]
        run("① ingest 抓原料", [P("ingest.py"), *cmd[1:]])
    else:
        print("\n① ingest：context.md 已存在，跳过")

    # ② author
    if args.force or not (proj / "content.yaml").exists():
        cmd = ["author.py", "--id", args.id]
        if args.skip_research:
            cmd += ["--skip-research"]
        run("② author 写脚本文案", [P("author.py"), *cmd[1:]])
    else:
        print("② author：content.yaml 已存在，跳过")

    # ③ shoot
    if args.force or not (proj / "shots_status.yaml").exists():
        cmd = ["shoot.py", "--id", args.id]
        if args.demo:
            cmd += ["--demo", args.demo]
        if args.force:
            cmd += ["--force"]
        run("③ shoot 真实截图", [P("shoot.py"), *cmd[1:]])
    else:
        print("③ shoot：shots_status.yaml 已存在，跳过")

    # ④ render（始终重跑，确保拿到最新文案/截图）
    run("④ render 渲染视频+封面", [P("render.py"), "--id", args.id, *plat_args])

    # ⑤ publish 文案
    run("⑤ publish 生成发布文案", [P("write_publish.py"), "--id", args.id, *plat_args])

    plats = args.platform or ["douyin", "xhs", "channels"]
    print("\n========== 完成 ==========")
    for plat in plats:
        print(f"  publish/{args.id}/{plat}/ : video.mp4 · cover.png · publish.md")
    print("\n抽查：随机播一条，确认像活人剪的；标题无禁用词；时长 30–60s。")


if __name__ == "__main__":
    main()
