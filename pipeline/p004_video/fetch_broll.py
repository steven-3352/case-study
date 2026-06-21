#!/usr/bin/env python3
"""Pexels Videos API · 关键词拉竖屏 b-roll 落本地素材库.

用途:
  反差钩子第 1 帧(chaos)需要真实手机质感的素材。Pexels 视频库 CC0 可商用,
  竖屏方向直接搜,1-2s 切片即可入 contrast_pairs。

依赖:
  - requests (项目已装)
  - 环境变量 PEXELS_API_KEY (从 https://www.pexels.com/api/ 申请,免费 200 req/h)

用法:
  python3 pipeline/p004_video/fetch_broll.py --q "messy desk late night" --count 5
  python3 pipeline/p004_video/fetch_broll.py --q "tired entrepreneur" --count 3 --min-dur 2 --max-dur 8

输出:
  assets/broll/raw/<slug>__<id>.mp4
  assets/broll/raw/<slug>__<id>.json   # Pexels 元数据 + 作者署名(CC0 仍建议保留)
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import sys
from typing import Any

import requests
from dotenv import load_dotenv

ROOT = pathlib.Path(__file__).resolve().parent
PROJECT_ROOT = ROOT.parent.parent
RAW_DIR = PROJECT_ROOT / "assets" / "broll" / "raw"

PEXELS_ENDPOINT = "https://api.pexels.com/videos/search"


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")[:40] or "broll"


def pick_file(video: dict[str, Any], min_h: int = 1080) -> dict[str, Any] | None:
    """Pexels 一条视频含多分辨率 video_files. 选竖屏 + 高度 ≥ min_h 的最小档."""
    portraits = [
        f for f in video.get("video_files", [])
        if f.get("width") and f.get("height")
        and f["height"] > f["width"]               # 竖屏
        and f["height"] >= min_h
        and f.get("file_type", "").endswith("mp4")
    ]
    if not portraits:
        return None
    return min(portraits, key=lambda f: f["height"])


def search(api_key: str, query: str, per_page: int, page: int = 1) -> dict[str, Any]:
    r = requests.get(
        PEXELS_ENDPOINT,
        headers={"Authorization": api_key},
        params={
            "query": query,
            "orientation": "portrait",
            "per_page": per_page,
            "page": page,
            "size": "medium",
        },
        timeout=20,
    )
    if r.status_code == 401:
        sys.exit("PEXELS_API_KEY 无效或未设置 (.env)")
    r.raise_for_status()
    return r.json()


def download(url: str, out: pathlib.Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, stream=True, timeout=60) as r:
        r.raise_for_status()
        with out.open("wb") as f:
            for chunk in r.iter_content(chunk_size=1 << 16):
                if chunk:
                    f.write(chunk)


def main() -> None:
    load_dotenv(PROJECT_ROOT / ".env")
    ap = argparse.ArgumentParser()
    ap.add_argument("--q", required=True, help="搜索关键词,英文最佳")
    ap.add_argument("--count", type=int, default=5, help="目标条数")
    ap.add_argument("--min-dur", type=float, default=1.5, help="最短时长(秒)")
    ap.add_argument("--max-dur", type=float, default=15.0, help="最长时长(秒)")
    ap.add_argument("--min-height", type=int, default=1080, help="最低分辨率高度")
    ap.add_argument("--dry-run", action="store_true", help="只打印,不下载")
    args = ap.parse_args()

    api_key = os.getenv("PEXELS_API_KEY")
    if not api_key:
        sys.exit("缺 PEXELS_API_KEY,在 .env 添加 (https://www.pexels.com/api/)")

    slug_q = slugify(args.q)
    saved: list[pathlib.Path] = []
    page = 1
    while len(saved) < args.count:
        data = search(api_key, args.q, per_page=15, page=page)
        videos = data.get("videos", [])
        if not videos:
            print(f"  ⚠ 无更多结果 (page={page})")
            break
        for v in videos:
            d = float(v.get("duration", 0))
            if not (args.min_dur <= d <= args.max_dur):
                continue
            f = pick_file(v, min_h=args.min_height)
            if not f:
                continue
            vid = v["id"]
            stem = f"{slug_q}__{vid}"
            mp4_path = RAW_DIR / f"{stem}.mp4"
            meta_path = RAW_DIR / f"{stem}.json"
            if mp4_path.exists():
                print(f"  ✓ 已有 {mp4_path.name}")
                saved.append(mp4_path)
                if len(saved) >= args.count:
                    break
                continue
            print(f"  ↓ {stem}.mp4 ({f['height']}p, {d:.1f}s, by {v['user']['name']})")
            if args.dry_run:
                saved.append(mp4_path)
            else:
                download(f["link"], mp4_path)
                meta_path.write_text(json.dumps({
                    "pexels_id": vid,
                    "url": v["url"],
                    "user": v["user"],
                    "duration": d,
                    "width": f["width"],
                    "height": f["height"],
                    "query": args.q,
                    "license": "Pexels (CC0-like, free for commercial use)",
                }, ensure_ascii=False, indent=2), encoding="utf-8")
                saved.append(mp4_path)
            if len(saved) >= args.count:
                break
        page += 1
        if page > 10:
            break

    print(f"\n✓ 落地 {len(saved)} 条到 {RAW_DIR}")
    for p in saved:
        print(f"  {p.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
