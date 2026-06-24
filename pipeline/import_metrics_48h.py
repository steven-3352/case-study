#!/usr/bin/env python3
"""手动导入 48h 平台数据 · 有数据才进化，无数据则暂停.

  # 查看本周哪些条在等待 48h 数据
  python3 pipeline/import_metrics_48h.py --status

  # 导入一条（发布后约 48h 从创作者中心下载填 JSON）
  python3 pipeline/import_metrics_48h.py --file path/to/W26D04_48h.json

  # 导入后只写 performance，不跑进化（调试用）
  python3 pipeline/import_metrics_48h.py --file path.json --no-evolve

JSON 模板: templates/design/platform_metrics_import.example.json
"""
from __future__ import annotations

import argparse
import datetime as dt
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "pipeline"))

from platform_metrics.providers.manual_import import load_import_file
from platform_metrics.sync import full_sync_48h

WEEK_DEFAULT = ROOT / "publish" / "2026-W26"

EVOLUTION_SCRIPT = ROOT / "pipeline" / "evolution_apply.py"


def _read_yaml(path: pathlib.Path) -> dict:
    import yaml

    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _write_yaml(path: pathlib.Path, data: dict) -> None:
    import yaml

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")


def _has_48h_actual(entry: dict, platform: str = "douyin") -> bool:
    plat = (entry.get("platforms") or {}).get(platform) or {}
    actual = plat.get("actual") or {}
    if plat.get("data_window") != "48h":
        return False
    core = ("completion_3s", "completion_rate", "avg_watch_s", "views")
    return any(actual.get(k) is not None for k in core)


def print_status(week_dir: pathlib.Path) -> int:
    week_data = _read_yaml(week_dir / "performance_data.yaml")
    brief = _read_yaml(week_dir / "evolution_brief.yaml")
    entries = week_data.get("entries") or []

    print(f"\n{'='*56}")
    print(f"  48h 数据 · 进化状态 · {week_dir.name}")
    print(f"{'='*56}")
    policy = brief.get("data_policy") or {}
    print(f"  策略: {policy.get('mode', 'manual_48h')} · 衡量窗口 {policy.get('measure_window', '48h')}")
    print(f"  进化: {brief.get('evolution_status', 'paused')}")
    pending = brief.get("pending_actual") or []
    if pending:
        print(f"  待数据: {', '.join(pending)}")
    print()

    waiting = ready = done = 0
    for e in entries:
        pid = e.get("project_id", "?")
        day = e.get("day", "")
        pub = e.get("published_at") or "未发布"
        if _has_48h_actual(e):
            tag = "✓ 已有 48h 数据"
            done += 1
        elif pub == "未发布":
            tag = "○ 未发布 · 跳过"
            waiting += 1
        else:
            tag = "⏸ 等待 48h 数据 · 进化暂停"
            ready += 1
        print(f"  {day or pid:6} {pid:8}  {tag}  (发布: {pub})")

    print(f"\n  汇总: {done} 条已导入 · {ready} 条待你提供 48h 数据")
    if ready or (pending and not done):
        print("\n  → 你从创作者中心下载 48h 数据后:")
        print("     python3 pipeline/import_metrics_48h.py --file your.json")
    if brief.get("evolution_status") == "paused" and done == 0:
        print("\n  D05+ 形式进化暂不动 · 等 D04 等条目的 48h actual")
    print()
    return 0


def import_file(
    path: pathlib.Path,
    *,
    week_dir: pathlib.Path,
    run_evolution: bool = True,
) -> int:
    payload = load_import_file(path.resolve())
    pid = payload.get("project_id")
    if not pid:
        print("✗ JSON 缺少 project_id", file=sys.stderr)
        return 2

    platform = payload.get("platform", "douyin")
    metrics = dict(payload["metrics"])
    metrics["_source"] = payload.get("source") or "manual_48h"
    metrics["data_window"] = "48h"
    if payload.get("published_at"):
        metrics["published_at"] = payload["published_at"]

    paths = full_sync_48h(
        pid,
        platform,
        metrics,
        week_dir=week_dir,
        run_evolution=False,
    )
    print(f"✓ 48h 数据已写入 {paths['performance']}")

    if not run_evolution:
        print("  （未触发进化 · --no-evolve）")
        return 0

    import subprocess

    r = subprocess.run(
        [sys.executable, str(EVOLUTION_SCRIPT), "--id", pid, "--week", str(week_dir)],
        cwd=str(ROOT),
    )
    if r.returncode != 0:
        return r.returncode

    brief_path = week_dir / "evolution_brief.yaml"
    brief = _read_yaml(brief_path)
    brief["evolution_status"] = "applied"
    brief["updated_at"] = dt.datetime.now().isoformat(timespec="seconds")
    brief.setdefault("data_policy", {}).update({
        "mode": "manual_48h",
        "measure_window": "48h",
        "last_import_at": dt.datetime.now().isoformat(timespec="seconds"),
        "last_import_project": pid,
    })
    _write_yaml(brief_path, brief)
    print(f"\n✓ 进化已应用 · 见 {brief_path}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="手动 48h 数据导入 · 有数据才进化")
    ap.add_argument("--file", type=pathlib.Path, help="48h 数据 JSON")
    ap.add_argument("--status", action="store_true", help="查看等待/已导入状态")
    ap.add_argument("--week", type=pathlib.Path, default=WEEK_DEFAULT)
    ap.add_argument("--no-evolve", action="store_true", help="只写 performance，不跑进化")
    args = ap.parse_args()

    week_dir = args.week.resolve()
    if not week_dir.exists():
        print(f"找不到 {week_dir}", file=sys.stderr)
        return 2

    if args.status or not args.file:
        if args.file:
            pass
        else:
            return print_status(week_dir)

    if args.file:
        return import_file(
            args.file,
            week_dir=week_dir,
            run_evolution=not args.no_evolve,
        )

    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
