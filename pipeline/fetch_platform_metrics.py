#!/usr/bin/env python3
"""抖音 / 小红书 · 账号数据自动拉取 → performance.yaml → evolution_apply.

  # 首次登录（弹窗 + 浏览器扫码）
  python3 pipeline/fetch_platform_metrics.py --login-all
  python3 pipeline/fetch_platform_metrics.py --login douyin

  # 定时任务（launchd · 过期自动弹扫码）
  python3 pipeline/fetch_platform_metrics.py --scheduled

  # 手动单条
  python3 pipeline/fetch_platform_metrics.py --sync --id W26D04
"""
from __future__ import annotations

import argparse
import datetime as dt
import pathlib
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "pipeline"))

from platform_metrics.providers.manual_import import load_import_file
from platform_metrics.providers.playwright_provider import (
    SessionExpiredError,
    ensure_session,
    fetch_with_playwright,
    login_and_save_session,
    notify_mac,
    probe_session,
)
from platform_metrics.sync import (
    find_day_dir,
    full_sync,
    full_sync_48h,
    load_match_keywords,
)

CONFIG_PATH = ROOT / "pipeline" / "platform_metrics" / "config.yaml"
WEEK_DEFAULT = ROOT / "publish" / "2026-W26"
LOG_DIR = ROOT / "ops" / "logs"


def load_config() -> dict:
    return yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")) or {}


def log(msg: str) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    line = f"[{dt.datetime.now().isoformat(timespec='seconds')}] {msg}"
    print(line)
    with (LOG_DIR / "metrics_sync.log").open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def sync_project_with_retry(
    project_id: str,
    platform: str,
    *,
    week_dir: pathlib.Path,
    config: dict,
) -> int:
    keywords = load_match_keywords(project_id, week_dir)
    log(f"  keywords: {keywords[:3]}")
    for attempt in range(2):
        try:
            ensure_session(platform, config)
            metrics = fetch_with_playwright(platform, keywords, config)
            paths = full_sync(project_id, platform, metrics, week_dir=week_dir)
            log(f"OK {project_id}/{platform} → {paths['performance']}")
            for k, v in metrics.items():
                if not k.startswith("_"):
                    log(f"    {k}={v}")
            return 0
        except SessionExpiredError as e:
            log(f"SESSION_EXPIRED {e}")
            notify_mac("平台数据同步", f"{platform} 会话过期，请扫码")
            login_and_save_session(platform, config, wait="dialog")
            if attempt == 0:
                continue
            return 1
        except Exception as e:
            log(f"FAIL {project_id}/{platform}: {e}")
            return 1
    return 1


def sync_week(week_dir: pathlib.Path, platform: str, config: dict) -> int:
    perf_week = week_dir / "performance_data.yaml"
    if not perf_week.exists():
        print(f"✗ 无 {perf_week}")
        return 1
    data = yaml.safe_load(perf_week.read_text(encoding="utf-8")) or {}
    code = 0
    for entry in data.get("entries") or []:
        pid = entry.get("project_id")
        actual = ((entry.get("platforms") or {}).get(platform) or {}).get("actual") or {}
        if actual.get("views") and platform == "douyin":
            print(f"  跳过 {pid}（已有 actual）")
            continue
        print(f"\n── 拉取 {pid} ──")
        if sync_project_with_retry(pid, platform, week_dir=week_dir, config=config) != 0:
            code = 1
    return code


def _is_published(entry: dict, platform: str, week_dir: pathlib.Path) -> bool:
    """已发布或计划时间已过才拉数."""
    pid = entry.get("project_id")
    if entry.get("published_at"):
        return True
    day_dir = find_day_dir(week_dir, pid) if pid else None
    if not day_dir:
        return False
    meta = yaml.safe_load((day_dir / "meta.yaml").read_text(encoding="utf-8")) or {}
    sched = (meta.get("schedule") or {}).get(platform)
    if not sched:
        return True  # 无计划时间视为可拉
    try:
        when = dt.datetime.fromisoformat(str(sched).replace(" ", "T"))
        return dt.datetime.now() >= when
    except ValueError:
        return True


def run_scheduled(week_dir: pathlib.Path, platforms: list[str]) -> int:
    log("=== scheduled sync start ===")
    config = load_config()
    perf_week = week_dir / "performance_data.yaml"
    if not perf_week.exists():
        log(f"no performance_data.yaml")
        return 1

    data = yaml.safe_load(perf_week.read_text(encoding="utf-8")) or {}
    code = 0
    synced = skipped = 0

    for platform in platforms:
        session = ROOT / config["accounts"][platform]["session_file"]
        if not session.exists():
            log(f"no session {platform} → login")
            try:
                login_and_save_session(platform, config, wait="dialog")
            except Exception as e:
                log(f"login failed {platform}: {e}")
                code = 1
                continue

        for entry in data.get("entries") or []:
            pid = entry.get("project_id")
            if not pid:
                continue
            actual = ((entry.get("platforms") or {}).get(platform) or {}).get("actual") or {}
            if actual.get("views") and platform == "douyin":
                skipped += 1
                continue
            if actual.get("collects") and platform == "xhs":
                skipped += 1
                continue
            if not _is_published(entry, platform, week_dir):
                log(f"skip {pid}/{platform} 未到发布时间")
                skipped += 1
                continue
            day_dir = find_day_dir(week_dir, pid)
            if platform == "douyin" and day_dir and not (day_dir / "douyin" / "video.mp4").exists():
                continue
            log(f"sync {pid}/{platform}")
            if sync_project_with_retry(pid, platform, week_dir=week_dir, config=config) == 0:
                synced += 1
            else:
                code = 1

    log(f"=== done synced={synced} skipped={skipped} exit={code} ===")
    if synced:
        notify_mac("平台数据同步", f"已同步 {synced} 条")
    return 0 if synced > 0 or code == 0 else code


def main() -> int:
    ap = argparse.ArgumentParser(description="抖音/小红书账号数据自动拉取")
    ap.add_argument("--login", choices=["douyin", "xhs"])
    ap.add_argument("--login-all", action="store_true", help="抖音+小红书依次扫码")
    ap.add_argument("--check-session", choices=["douyin", "xhs"])
    ap.add_argument("--scheduled", action="store_true", help="定时任务入口")
    ap.add_argument("--sync", action="store_true")
    ap.add_argument("--sync-week", type=pathlib.Path)
    ap.add_argument("--id")
    ap.add_argument("--platform", choices=["douyin", "xhs"], default="douyin")
    ap.add_argument("--week", type=pathlib.Path, default=WEEK_DEFAULT)
    ap.add_argument("--force", action="store_true", help="忽略已有 actual 强制重拉")
    ap.add_argument("--import-json", type=pathlib.Path)
    args = ap.parse_args()

    config = load_config()

    if args.login_all:
        for p in ("douyin", "xhs"):
            login_and_save_session(p, config, wait="dialog")
        return 0

    if args.check_session:
        ok = probe_session(args.check_session, config)
        print(f"{'✓' if ok else '✗'} {args.check_session} 会话{'有效' if ok else '无效/过期'}")
        return 0 if ok else 1

    if args.login:
        login_and_save_session(args.login, config, wait="dialog")
        return 0

    if args.scheduled:
        return run_scheduled(args.week.resolve(), ["douyin", "xhs"])

    if args.import_json:
        payload = load_import_file(args.import_json.resolve())
        pid = payload.get("project_id") or args.id
        if not pid:
            return 2
        platform = payload.get("platform", args.platform)
        metrics = dict(payload["metrics"])
        metrics.setdefault("data_window", "48h")
        metrics["_source"] = payload.get("source", "manual_48h")
        if payload.get("published_at"):
            metrics["published_at"] = payload["published_at"]
        paths = full_sync_48h(
            pid, platform, metrics,
            week_dir=args.week.resolve(),
            run_evolution=not args.no_evolve,
        )
        print(f"✓ 48h 导入 {pid} → {paths['performance']}")
        if not args.no_evolve:
            print("  进化已触发 · 见 evolution_brief.yaml")
        return 0

    if args.sync_week:
        return sync_week(args.sync_week.resolve(), args.platform, config)

    if args.sync:
        if not args.id:
            print("--sync 需要 --id", file=sys.stderr)
            return 2
        return sync_project_with_retry(
            args.id, args.platform, week_dir=args.week.resolve(), config=config
        )

    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
