#!/usr/bin/env python3
"""③ 真实截图 · 在 demo 站点上把 content.yaml 的 shots 截成 9:16 PNG.

每个 shot 的最终 URL = demo 根 + shot.url（相对路径）。
截图成功 → projects/{id}/shots/{ref}.png；失败 → 记进 shots_status.yaml，
由 render.py 回落到仿真/网络素材（不静默）。

用法:
  python3 pipeline/shoot.py --id P002 --demo https://demo.example.com
"""
from __future__ import annotations

import argparse
import pathlib
import sys
from urllib.parse import urljoin

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from pipeline.render_core import shoot_url


def main() -> None:
    ap = argparse.ArgumentParser(description="demo 站点真实截图")
    ap.add_argument("--id", required=True)
    ap.add_argument("--demo", default="", help="demo 根 URL；为空则全部跳过待回落")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    out_dir = ROOT / "projects" / args.id
    content_path = out_dir / "content.yaml"
    if not content_path.exists():
        sys.exit(f"先跑 author：缺 {content_path}")
    content = yaml.safe_load(content_path.read_text(encoding="utf-8"))
    shots = content.get("shots", []) or []

    shots_dir = out_dir / "shots"
    shots_dir.mkdir(parents=True, exist_ok=True)
    status: dict[str, str] = {}

    for s in shots:
        ref = s["ref"]
        out = shots_dir / f"{ref}.png"
        if out.exists() and not args.force:
            status[ref] = "ok"
            print(f"  {ref}: 已存在，跳过")
            continue
        if not args.demo:
            status[ref] = "no-demo"
            print(f"  {ref}: 无 demo URL → 待回落")
            continue
        url = urljoin(args.demo.rstrip("/") + "/", s["url"].lstrip("/"))
        try:
            shoot_url(url, out)
            if out.exists() and out.stat().st_size > 1024:
                status[ref] = "ok"
                print(f"  {ref}: ✓ {url}")
            else:
                status[ref] = "empty"
                print(f"  {ref}: ⚠ 截图为空 → 待回落 ({url})")
        except Exception as e:  # noqa: BLE001 — 截图失败不阻断
            status[ref] = "fail"
            print(f"  {ref}: ⚠ 失败 → 待回落 ({e})")

    (out_dir / "shots_status.yaml").write_text(
        yaml.safe_dump(status, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )
    ok = sum(1 for v in status.values() if v == "ok")
    print(f"\n✓ shots: {ok}/{len(shots)} 张真实截图，其余 render 阶段回落")


if __name__ == "__main__":
    main()
