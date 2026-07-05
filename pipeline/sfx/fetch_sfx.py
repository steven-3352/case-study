#!/usr/bin/env python3
"""Freesound API v2 · 按 catalog.yaml 拉 CC0 音效落本地素材库.

用途:
  assets/sfx/catalog.yaml 里 source: freesound_TBD 的 candidate 全是占位。
  本脚本按 catalog 的 freesound_search_hints 逐条检索 Freesound,
  只取 CC0 (Creative Commons 0) 授权, 下载 HQ preview 转 wav 落 candidate path,
  并回写 catalog 的 source / fetched_at。sfx-mixer (pipeline/p004_video/lib/sfx.py)
  即可消费, 不再走 gap-skip。

依赖:
  - 环境变量 FREESOUND_API_KEY (.env)
    注册: https://freesound.org/apiv2/apply/ (免费 · 选 "Token" 认证即可)
  - ffmpeg (mp3 preview → wav 48k)
  - pyyaml (读 catalog)

用法:
  python3 pipeline/sfx/fetch_sfx.py                    # 拉全部 fetched_at: null 的 candidate
  python3 pipeline/sfx/fetch_sfx.py --family hit       # 只拉 hit 家族
  python3 pipeline/sfx/fetch_sfx.py --id impact_soft_boom
  python3 pipeline/sfx/fetch_sfx.py --dry-run          # 只搜不下载
  python3 pipeline/sfx/fetch_sfx.py --force            # 已 fetched 的也重拉

输出:
  assets/sfx/<family>/<id>.wav
  assets/sfx/<family>/<id>.json   # Freesound 元数据 + 作者署名 (CC0 仍保留)
  catalog.yaml 就地回写 source: freesound_<fsid> + fetched_at
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Any

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    load_dotenv = None
try:
    import requests
except ModuleNotFoundError:
    requests = None
    import urllib.error
    import urllib.parse
    import urllib.request

try:
    import yaml
except ModuleNotFoundError:
    sys.exit("缺 pyyaml: pip install pyyaml")

ROOT = pathlib.Path(__file__).resolve().parent
PROJECT_ROOT = ROOT.parent.parent
CATALOG = PROJECT_ROOT / "assets" / "sfx" / "catalog.yaml"

FS_SEARCH = "https://freesound.org/apiv2/search/text/"
FS_APPLY_URL = "https://freesound.org/apiv2/apply/"
HEADERS = {
    "User-Agent": "case-study-sfx-pipeline/1.0",
    "Accept": "application/json",
}
FIELDS = "id,name,previews,duration,license,username,tags,num_downloads,avg_rating"

FFMPEG_FULL = "/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg"
FFMPEG = FFMPEG_FULL if pathlib.Path(FFMPEG_FULL).exists() else (shutil.which("ffmpeg") or "ffmpeg")


def load_env_file(path: pathlib.Path) -> None:
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


def http_get_json(url: str, params: dict[str, Any], token: str) -> dict[str, Any]:
    params = {**params, "token": token}
    if requests:
        r = requests.get(url, headers=HEADERS, params=params, timeout=30)
        if r.status_code == 401:
            sys.exit(f"FREESOUND_API_KEY 无效 (.env) · 注册: {FS_APPLY_URL}")
        r.raise_for_status()
        return r.json()
    full = url + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(full, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=30) as res:
            return json.loads(res.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 401:
            sys.exit(f"FREESOUND_API_KEY 无效 (.env) · 注册: {FS_APPLY_URL}")
        raise


def download(url: str, out: pathlib.Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    if requests:
        with requests.get(url, stream=True, timeout=(10, 45), headers=HEADERS) as r:
            r.raise_for_status()
            with out.open("wb") as f:
                for chunk in r.iter_content(chunk_size=1 << 16):
                    if chunk:
                        f.write(chunk)
        return
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=120) as res, out.open("wb") as f:
        while True:
            chunk = res.read(1 << 16)
            if not chunk:
                break
            f.write(chunk)


def to_wav(src: pathlib.Path, dst: pathlib.Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [FFMPEG, "-y", "-i", str(src), "-ar", "48000", "-ac", "2",
         "-c:a", "pcm_s16le", str(dst)],
        capture_output=True, check=True, timeout=120,
    )


def _search_once(token: str, query: str, dur_lo: float, dur_hi: float) -> list[dict[str, Any]]:
    filt = f'license:"Creative Commons 0" duration:[{dur_lo:.2f} TO {dur_hi:.2f}]'
    data = http_get_json(FS_SEARCH, {
        "query": query,
        "filter": filt,
        "fields": FIELDS,
        "sort": "score",
        "page_size": 15,
    }, token)
    return data.get("results", [])


def _simplify(query: str, keep: int) -> str:
    """取前 keep 个显著词 · CC0 池小 · 4 词 query 常空, 2 词命中数百."""
    words = query.split()
    return " ".join(words[:keep])


def search_cc0(token: str, query: str, dur_lo: float, dur_hi: float) -> tuple[list[dict[str, Any]], str]:
    """渐进降级检索 · 返回 (results, 实际命中的 query)。

    CC0 授权池远小于全库 · 多词 query + CC0 过滤常返空 (实测
    "whoosh transition swish soft"+CC0=15, "whoosh transition"=603, "whoosh"=2305)。
    逐步砍词直到有结果。
    """
    words = query.split()
    tried: list[str] = []
    for keep in (len(words), 3, 2, 1):
        if keep > len(words):
            continue
        q = _simplify(query, keep)
        if q in tried:
            continue
        tried.append(q)
        results = _search_once(token, q, dur_lo, dur_hi)
        if results:
            return results, q
    return [], query


def pick_best(results: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not results:
        return None
    # 相关度前 15 里按下载数取最热 · 下载数是质量代理
    return max(results, key=lambda r: r.get("num_downloads", 0))


def rewrite_catalog_entry(text: str, cid: str, fsid: int, today: str) -> str:
    """就地回写 candidate 的 source/fetched_at · 保留 catalog 全部注释."""
    m = re.search(rf"(- id: {re.escape(cid)}\n(?:        .*\n)+)", text)
    if not m:
        print(f"  ⚠ catalog 未找到 candidate {cid} · 跳过回写")
        return text
    block = m.group(1)
    new_block = re.sub(r"source: \S+", f"source: freesound_{fsid}", block, count=1)
    new_block = re.sub(r"fetched_at: \S+", f'fetched_at: "{today}"', new_block, count=1)
    return text.replace(block, new_block)


def main() -> None:
    load_env_file(PROJECT_ROOT / ".env")
    ap = argparse.ArgumentParser()
    ap.add_argument("--family", help="只拉指定家族 (ambient/tick/whoosh/hit/riser)")
    ap.add_argument("--id", dest="only_id", help="只拉指定 candidate id")
    ap.add_argument("--dry-run", action="store_true", help="只搜索打印 · 不下载不回写")
    ap.add_argument("--force", action="store_true", help="已 fetched 的也重拉")
    args = ap.parse_args()

    token = os.getenv("FREESOUND_API_KEY")
    if not token:
        sys.exit(
            "缺 FREESOUND_API_KEY (.env)\n"
            f"  1. 注册 Freesound 账号并申请 API key: {FS_APPLY_URL}\n"
            "  2. .env 添加一行: FREESOUND_API_KEY=<key>\n"
            "  (Token 认证即可 · 不需要 OAuth2 · preview 下载不限量)"
        )

    catalog_text = CATALOG.read_text(encoding="utf-8")
    catalog = yaml.safe_load(catalog_text)
    families: dict[str, Any] = catalog["sfx_families"]
    hints: dict[str, dict[str, str]] = catalog.get("freesound_search_hints", {})
    today = datetime.date.today().isoformat()

    done, skipped, failed = 0, 0, 0
    for fam_key, fam in families.items():
        if fam.get("alias_of"):
            continue
        if args.family and fam_key != args.family:
            continue
        dur_lo, dur_hi = fam.get("duration_range_s", [0.05, 10.0])
        # 放宽时长过滤: Freesound 原始素材普遍比目标长 · mixer 会截。
        # ambient: 只取短可循环铺底 (8-90s) · 避开数分钟 room-tone 大文件 (下载慢/易挂)。
        if fam_key == "ambient":
            f_lo, f_hi = 8.0, 90.0
        else:
            f_lo, f_hi = max(0.01, dur_lo * 0.5), dur_hi * 3
        for cand in fam.get("candidates", []):
            cid = cand["id"]
            if args.only_id and cid != args.only_id:
                continue
            if cand.get("fetched_at") and not args.force:
                skipped += 1
                continue
            query = hints.get(fam_key, {}).get(cid)
            if not query:
                print(f"⚠ {fam_key}/{cid} 无 freesound_search_hints · 跳过")
                failed += 1
                continue
            print(f"→ {fam_key}/{cid} · \"{query}\" · dur [{f_lo:.2f}, {f_hi:.2f}]s")
            results, used_q = search_cc0(token, query, f_lo, f_hi)
            best = pick_best(results)
            if not best:
                print(f"  ✗ 无 CC0 结果 · 换关键词试 search_keywords.py")
                failed += 1
                continue
            if used_q != query:
                print(f"  ↺ 降级 query: \"{used_q}\"")
            preview = best.get("previews", {}).get("preview-hq-mp3") \
                or best.get("previews", {}).get("preview-lq-mp3")
            print(f"  ✓ fs#{best['id']} \"{best['name']}\" {best['duration']:.2f}s "
                  f"↓{best.get('num_downloads', 0)} by {best['username']}")
            if args.dry_run:
                done += 1
                continue
            if not preview:
                print("  ✗ 无 preview URL")
                failed += 1
                continue
            wav_path = PROJECT_ROOT / cand["path"]
            meta_path = wav_path.with_suffix(".json")
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tf:
                tmp_mp3 = pathlib.Path(tf.name)
            try:
                download(preview, tmp_mp3)
                to_wav(tmp_mp3, wav_path)
            finally:
                tmp_mp3.unlink(missing_ok=True)
            meta_path.write_text(json.dumps({
                "freesound_id": best["id"],
                "name": best["name"],
                "username": best["username"],
                "license": best["license"],
                "duration": best["duration"],
                "tags": best.get("tags", []),
                "num_downloads": best.get("num_downloads"),
                "query": query,
                "url": f"https://freesound.org/s/{best['id']}/",
                "fetched_at": today,
            }, ensure_ascii=False, indent=2), encoding="utf-8")
            catalog_text = rewrite_catalog_entry(catalog_text, cid, best["id"], today)
            done += 1
            print(f"  → {wav_path.relative_to(PROJECT_ROOT)}")

    if not args.dry_run and done:
        CATALOG.write_text(catalog_text, encoding="utf-8")
        print(f"\n✓ catalog.yaml 回写 {done} 条")
    print(f"完成 {done} · 跳过(已有) {skipped} · 失败 {failed}")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
