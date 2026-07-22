#!/usr/bin/env python3
"""Pexels Videos API · 关键词拉竖屏免费 b-roll 素材到本地.

能力封装版(可移植):不绑任何项目路径,输出目录由 --out-dir 决定,
凭证走环境变量 PEXELS_API_KEY(或 --env 指向的 .env 文件)。

依赖:
  - 仅标准库即可运行(requests 缺失时自动回退 urllib;dotenv 缺失时自带 .env 解析)
  - 环境变量 PEXELS_API_KEY(https://www.pexels.com/api/ 免费申请,200 req/h)

用法:
  python3 fetch_stock_footage.py --q "messy desk late night" --count 5
  python3 fetch_stock_footage.py --q "tired entrepreneur" --count 3 --min-dur 2 --max-dur 8 --out-dir ./broll
  python3 fetch_stock_footage.py --q "city night" --dry-run

输出(默认 ./stock_footage/ 下):
  <out-dir>/<slug>__<id>.mp4
  <out-dir>/<slug>__<id>.json   # Pexels 元数据 + 作者署名(CC0 仍建议保留署名)

素材许可:Pexels 内容为 CC0-like,免费可商用。本脚本本身随引擎分发(自有代码)。
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import sys
from typing import Any

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:  # Keep fetch usable without installing python-dotenv.
    load_dotenv = None
try:
    import requests
except ModuleNotFoundError:  # Homebrew Python may be externally managed; keep usable.
    requests = None
    import urllib.error
    import urllib.parse
    import urllib.request

PEXELS_ENDPOINT = "https://api.pexels.com/videos/search"
PEXELS_HEADERS = {
    "User-Agent": "content-engine-stock-footage/1.0",
    "Accept": "application/json",
}


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
    params = {
        "query": query,
        "orientation": "portrait",
        "per_page": per_page,
        "page": page,
        "size": "medium",
    }
    if requests:
        r = requests.get(
            PEXELS_ENDPOINT,
            headers={**PEXELS_HEADERS, "Authorization": api_key},
            params=params,
            timeout=20,
        )
        if r.status_code == 401:
            sys.exit("PEXELS_API_KEY 无效或未设置")
        r.raise_for_status()
        return r.json()

    url = PEXELS_ENDPOINT + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={**PEXELS_HEADERS, "Authorization": api_key})
    try:
        with urllib.request.urlopen(req, timeout=20) as res:
            return json.loads(res.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 401:
            sys.exit("PEXELS_API_KEY 无效或未设置")
        raise


def download(url: str, out: pathlib.Path, referer: str | None = None) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    headers = dict(PEXELS_HEADERS)
    if referer:
        headers["Referer"] = referer
    if requests:
        with requests.get(url, stream=True, timeout=60, headers=headers) as r:
            r.raise_for_status()
            with out.open("wb") as f:
                for chunk in r.iter_content(chunk_size=1 << 16):
                    if chunk:
                        f.write(chunk)
        return

    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=60) as res, out.open("wb") as f:
        while True:
            chunk = res.read(1 << 16)
            if not chunk:
                break
            f.write(chunk)


def load_env_file(path: pathlib.Path) -> None:
    """加载 .env(若存在)。dotenv 缺失时用自带解析,不覆盖已存在的环境变量。"""
    if load_dotenv:
        load_dotenv(path)
        return
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def main() -> None:
    ap = argparse.ArgumentParser(description="拉 Pexels CC0 竖屏 b-roll 到本地")
    ap.add_argument("--q", required=True, help="搜索关键词,英文最佳")
    ap.add_argument("--count", type=int, default=5, help="目标条数")
    ap.add_argument("--min-dur", type=float, default=1.5, help="最短时长(秒)")
    ap.add_argument("--max-dur", type=float, default=15.0, help="最长时长(秒)")
    ap.add_argument("--min-height", type=int, default=1080, help="最低分辨率高度")
    ap.add_argument("--out-dir", default="stock_footage", help="输出目录(默认 ./stock_footage)")
    ap.add_argument("--env", default=".env", help="可选 .env 文件路径(默认 ./.env)")
    ap.add_argument("--dry-run", action="store_true", help="只打印,不下载")
    args = ap.parse_args()

    env_path = pathlib.Path(args.env)
    if env_path.exists():
        load_env_file(env_path)

    api_key = os.getenv("PEXELS_API_KEY")
    if not api_key:
        sys.exit("缺 PEXELS_API_KEY(环境变量或 --env 指向的 .env,见 https://www.pexels.com/api/)")

    out_dir = pathlib.Path(args.out_dir).resolve()
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
            mp4_path = out_dir / f"{stem}.mp4"
            meta_path = out_dir / f"{stem}.json"
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
                download(f["link"], mp4_path, referer=v.get("url"))
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

    print(f"\n✓ 落地 {len(saved)} 条到 {out_dir}")
    for p in saved:
        print(f"  {p.name}")


if __name__ == "__main__":
    main()
