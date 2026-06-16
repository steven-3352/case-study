#!/usr/bin/env python3
"""⑤ 发布文案 · content.yaml → 各平台 publish.md（标题/正文/标签/规格）.

结构对齐 templates/publish_三平台.md。

用法:
  python3 pipeline/write_publish.py --id P002
"""
from __future__ import annotations

import argparse
import pathlib
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]

SPEC = {
    "douyin": "1080×1920 · 竖屏 · 前 1s 大字钩子",
    "xhs": "1080×1920 · ≤60s · 演示满铺 + 底部字幕",
    "channels": "1080×1920 · 分享向 · 60s 内",
}
NAME = {"douyin": "抖音", "xhs": "小红书", "channels": "视频号"}


def publish_md(pid: str, plat: str, topic: dict, spec: dict) -> str:
    tags = " ".join(f"#{t}" for t in (spec.get("tags") or []))
    lines = [
        f"# {NAME[plat]} · {pid}",
        "",
        f"> 痛点：{topic.get('pain','')}",
        f"> 解决：{topic.get('solves','')}",
        f"> 钩子：{topic.get('hook','')}（{topic.get('angle','')}）",
        "",
        "## 标题",
        spec.get("title", ""),
        "",
        "## 正文",
        spec.get("body", ""),
        "",
        "## 标签",
        tags,
        "",
        "## 互动钩子",
        spec.get("interaction", ""),
        "",
        "## 封面",
        f"大字钩子：{(spec.get('cover') or {}).get('hook','')}",
        f"封面图：publish/{pid}/{plat}/cover.png",
        "",
        "## 规格",
        f"- {SPEC[plat]}",
        f"- 目标时长：{spec.get('duration_s','?')}s",
        f"- 视频：publish/{pid}/{plat}/video.mp4",
        "",
        "## 口播分镜",
    ]
    for i, seg in enumerate(spec.get("segments", []) or [], 1):
        kind = seg.get("evidence_kind", "none")
        src = seg.get("source") if kind in ("none", None) else f"{seg.get('source')}/{kind}"
        lines.append(f"{i}. [{src}] 「{seg.get('sub')}」 {seg.get('vo')}")
    lines.append("")
    lines.append("## 发布后")
    lines.append("- 复制 content_id 到 ops/metrics.csv，48h / 7d 回填数据")
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description="content.yaml → publish.md")
    ap.add_argument("--id", required=True)
    ap.add_argument("--platform", nargs="*", choices=["douyin", "xhs", "channels"])
    args = ap.parse_args()

    content = yaml.safe_load((ROOT / "projects" / args.id / "content.yaml").read_text(encoding="utf-8"))
    topic = content.get("topic", {}) or {}
    plats = args.platform or ["douyin", "xhs", "channels"]
    for plat in plats:
        out_dir = ROOT / "publish" / args.id / plat
        out_dir.mkdir(parents=True, exist_ok=True)
        md = publish_md(args.id, plat, topic, content.get(plat, {}) or {})
        (out_dir / "publish.md").write_text(md, encoding="utf-8")
        print(f"  ✓ publish/{args.id}/{plat}/publish.md")


if __name__ == "__main__":
    main()
