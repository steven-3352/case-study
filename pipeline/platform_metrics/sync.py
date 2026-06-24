"""Sync fetched metrics → performance.yaml · metrics.csv · evolution_apply."""
from __future__ import annotations

import csv
import datetime as dt
import pathlib
import subprocess
import sys
from typing import Any

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[2]


def _read_yaml(path: pathlib.Path) -> dict:
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _write_yaml(path: pathlib.Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")


def find_day_dir(week_dir: pathlib.Path, project_id: str) -> pathlib.Path | None:
    for d in week_dir.iterdir():
        if not d.is_dir() or not d.name.startswith("D"):
            continue
        meta = _read_yaml(d / "meta.yaml")
        if meta.get("project_id") == project_id:
            return d
    return None


def load_match_keywords(project_id: str, week_dir: pathlib.Path) -> list[str]:
    day_dir = find_day_dir(week_dir, project_id)
    keys: list[str] = []
    if day_dir:
        content = _read_yaml(ROOT / "projects" / project_id / "content.yaml")
        dy = content.get("douyin") or {}
        for k in ("title", "hook"):
            v = dy.get(k) or content.get("topic", {}).get(k)
            if v:
                keys.append(str(v).strip())
        meta = _read_yaml(day_dir / "meta.yaml")
        if meta.get("topic", {}).get("hook"):
            keys.append(str(meta["topic"]["hook"]))
        xh = content.get("xhs") or {}
        if xh.get("title"):
            keys.append(str(xh["title"]).strip())
    return [k for k in keys if k and len(k) >= 4]


def sync_performance_yaml(
    project_id: str,
    platform: str,
    metrics: dict[str, Any],
    *,
    week_dir: pathlib.Path,
    data_window: str | None = None,
) -> pathlib.Path:
    day_dir = find_day_dir(week_dir, project_id)
    if not day_dir:
        raise FileNotFoundError(f"找不到 {project_id} 发布目录")
    perf_path = day_dir / "design" / "performance.yaml"
    perf = _read_yaml(perf_path)
    perf.setdefault("project_id", project_id)
    window = data_window or metrics.get("data_window")
    if window:
        perf["data_window"] = window
        perf["retro_status"] = "retro_complete"
    else:
        perf["retro_status"] = perf.get("retro_status") or "pending_actual"
    perf["fetched_at"] = dt.datetime.now().isoformat(timespec="seconds")
    perf["fetch_source"] = metrics.get("_source", "playwright")

    plat = perf.setdefault("platforms", {}).setdefault(platform, {})
    if window:
        plat["data_window"] = window
        plat["collected_at"] = dt.datetime.now().isoformat(timespec="seconds")
    actual = plat.setdefault("actual", {})
    for key in (
        "completion_3s", "completion_rate", "interaction_rate",
        "avg_watch_s", "views", "likes", "comments", "shares", "collects",
    ):
        if metrics.get(key) is not None:
            actual[key] = metrics[key]

    if metrics.get("views") and metrics.get("likes") is not None:
        comments = metrics.get("comments") or 0
        likes = metrics.get("likes") or 0
        views = metrics["views"]
        if views > 0:
            actual["interaction_rate"] = round((likes + comments) / views, 4)

    _write_yaml(perf_path, perf)
    return perf_path


def sync_metrics_csv(
    project_id: str,
    topic_id: str,
    platform: str,
    fmt: str,
    metrics: dict[str, Any],
    title: str = "",
) -> None:
    csv_path = ROOT / "ops" / "metrics.csv"
    rows: list[dict[str, str]] = []
    if csv_path.exists():
        with csv_path.open(encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
    fieldnames = [
        "content_id", "platform", "format", "series", "title", "publish_date",
        "exposure_48h", "completion_rate_48h", "likes_48h", "saves_48h",
        "comments_48h", "exposure_7d", "likes_7d", "saves_7d", "comments_7d",
        "verdict", "notes",
    ]
    plat_label = "douyin" if platform == "douyin" else "小红书"
    today = dt.date.today().isoformat()
    found = False
    for row in rows:
        if row.get("content_id") == topic_id and row.get("platform") == plat_label:
            row["publish_date"] = row.get("publish_date") or today
            if metrics.get("views"):
                row["exposure_48h"] = str(int(metrics["views"]))
            if metrics.get("completion_rate") is not None:
                cr = metrics["completion_rate"]
                row["completion_rate_48h"] = (
                    f"{cr:.2%}" if cr <= 1 else f"{cr:.1f}"
                )
            if metrics.get("likes") is not None:
                row["likes_48h"] = str(int(metrics["likes"]))
            if metrics.get("collects") is not None:
                row["saves_48h"] = str(int(metrics["collects"]))
            if metrics.get("comments") is not None:
                row["comments_48h"] = str(int(metrics["comments"]))
            row["notes"] = f"auto_fetch {today} {metrics.get('_source', '')}"
            found = True
            break
    if not found:
        rows.append({
            "content_id": topic_id,
            "platform": plat_label,
            "format": fmt,
            "series": "S1",
            "title": title,
            "publish_date": today,
            "exposure_48h": str(metrics.get("views") or ""),
            "completion_rate_48h": (
                f"{metrics['completion_rate']:.2%}"
                if metrics.get("completion_rate") is not None and metrics["completion_rate"] <= 1
                else str(metrics.get("completion_rate") or "")
            ),
            "likes_48h": str(metrics.get("likes") or ""),
            "saves_48h": str(metrics.get("collects") or ""),
            "comments_48h": str(metrics.get("comments") or ""),
            "exposure_7d": "",
            "likes_7d": "",
            "saves_7d": "",
            "comments_7d": "",
            "verdict": "",
            "notes": f"auto_fetch {today}",
        })
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


def sync_week_performance_data(
    project_id: str,
    platform: str,
    metrics: dict[str, Any],
    week_dir: pathlib.Path,
    *,
    data_window: str | None = None,
) -> None:
    week_path = week_dir / "performance_data.yaml"
    week_data = _read_yaml(week_path)
    window = data_window or metrics.get("data_window")
    for entry in week_data.get("entries") or []:
        if entry.get("project_id") == project_id:
            plat = entry.setdefault("platforms", {}).setdefault(platform, {})
            if window:
                plat["data_window"] = window
                plat["collected_at"] = dt.datetime.now().isoformat(timespec="seconds")
            plat["actual"] = {
                k: metrics[k]
                for k in (
                    "completion_3s", "completion_rate", "interaction_rate",
                    "avg_watch_s", "views", "likes", "comments", "shares", "collects",
                )
                if metrics.get(k) is not None
            }
            if window:
                entry["status"] = "retro_complete"
                if metrics.get("published_at"):
                    entry["published_at"] = str(metrics["published_at"])[:10]
            break
    week_data["updated_at"] = dt.datetime.now().isoformat(timespec="seconds")
    _write_yaml(week_path, week_data)


def run_evolution_apply(project_id: str) -> None:
    script = ROOT / "pipeline" / "evolution_apply.py"
    subprocess.run(
        [sys.executable, str(script), "--id", project_id],
        cwd=str(ROOT),
        check=False,
    )


def full_sync(
    project_id: str,
    platform: str,
    metrics: dict[str, Any],
    *,
    week_dir: pathlib.Path | None = None,
    run_evolution: bool = False,
) -> dict[str, pathlib.Path]:
    """Playwright 自动拉数 · 默认不触发进化（改用手动 48h 导入）."""
    week_dir = week_dir or ROOT / "publish" / "2026-W26"
    day_dir = find_day_dir(week_dir, project_id)
    meta = _read_yaml(day_dir / "meta.yaml") if day_dir else {}
    topic_id = meta.get("topic_id", "")
    fmt = (meta.get("formats") or {}).get(platform, "")
    content = _read_yaml(ROOT / "projects" / project_id / "content.yaml")
    title = (content.get("douyin") or {}).get("title", "")

    perf_path = sync_performance_yaml(project_id, platform, metrics, week_dir=week_dir)
    sync_week_performance_data(project_id, platform, metrics, week_dir)
    if topic_id:
        sync_metrics_csv(project_id, topic_id, platform, fmt, metrics, title=title)
    if run_evolution:
        run_evolution_apply(project_id)
    return {"performance": perf_path, "week_dir": week_dir}


def full_sync_48h(
    project_id: str,
    platform: str,
    metrics: dict[str, Any],
    *,
    week_dir: pathlib.Path | None = None,
    run_evolution: bool = True,
) -> dict[str, pathlib.Path]:
    """用户手动 48h 数据 · 写入后可触发进化."""
    week_dir = week_dir or ROOT / "publish" / "2026-W26"
    window = metrics.get("data_window") or "48h"
    day_dir = find_day_dir(week_dir, project_id)
    meta = _read_yaml(day_dir / "meta.yaml") if day_dir else {}
    topic_id = meta.get("topic_id", "")
    fmt = (meta.get("formats") or {}).get(platform, "")
    content = _read_yaml(ROOT / "projects" / project_id / "content.yaml")
    title = (content.get("douyin") or {}).get("title", "")

    perf_path = sync_performance_yaml(
        project_id, platform, metrics, week_dir=week_dir, data_window=window,
    )
    sync_week_performance_data(
        project_id, platform, metrics, week_dir, data_window=window,
    )
    if topic_id:
        sync_metrics_csv(project_id, topic_id, platform, fmt, metrics, title=title)
    if run_evolution:
        run_evolution_apply(project_id)
    return {"performance": perf_path, "week_dir": week_dir}
