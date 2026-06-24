#!/usr/bin/env python3
"""投后数据 → 进化简报 · L3 闭环.

  # 填 D04 design/performance.yaml actual 后
  python3 pipeline/evolution_apply.py --id W26D04
  python3 pipeline/evolution_apply.py --week publish/2026-W26
  python3 pipeline/evolution_apply.py --id W26D05 --check   # 开工前验 evolution

数据源:
  publish/{week}/performance_data.yaml
  publish/{week}/Dxx-*/design/performance.yaml
产出/更新:
  publish/{week}/evolution_brief.yaml
  publish/{week}/Dxx-*/design/post_publish_retro.md (variance 段)
  docs/design/PERFORMANCE_EVOLUTION_LOG.md (追加)
"""
from __future__ import annotations

import argparse
import datetime as dt
import pathlib
import sys
from typing import Any

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
WEEK_DEFAULT = ROOT / "publish" / "2026-W26"


def _read_yaml(path: pathlib.Path) -> dict:
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _write_yaml(path: pathlib.Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")


def _mid(lo: float, hi: float) -> float:
    return (lo + hi) / 2


def _in_range(val: float, lo: float, hi: float) -> bool:
    return lo <= val <= hi


def _variance_pct(actual: float, forecast_mid: float) -> float | None:
    if forecast_mid == 0:
        return None
    return (actual - forecast_mid) / forecast_mid


def find_day_dir(week_dir: pathlib.Path, project_id: str) -> pathlib.Path | None:
    for d in week_dir.iterdir():
        if not d.is_dir() or not d.name.startswith("D"):
            continue
        meta = _read_yaml(d / "meta.yaml")
        if meta.get("project_id") == project_id:
            return d
    return None


def has_48h_actual(entry: dict, platform: str = "douyin") -> bool:
    plat = (entry.get("platforms") or {}).get(platform) or {}
    if plat.get("data_window") != "48h":
        return False
    actual = plat.get("actual") or {}
    return any(
        actual.get(k) is not None
        for k in ("completion_3s", "completion_rate", "avg_watch_s", "views")
    )


def load_entry(week_dir: pathlib.Path, project_id: str) -> dict | None:
    week_data = _read_yaml(week_dir / "performance_data.yaml")
    for e in week_data.get("entries") or []:
        if e.get("project_id") == project_id:
            return e
    day_dir = find_day_dir(week_dir, project_id)
    if day_dir:
        perf = _read_yaml(day_dir / "design" / "performance.yaml")
        if perf:
            return perf
    return None


def analyze_entry(entry: dict) -> dict[str, Any]:
    """Compare actual vs forecast · return variance + learnings."""
    pid = entry.get("project_id", "?")
    out: dict[str, Any] = {
        "project_id": pid,
        "status": "pending_actual",
        "variance": {},
        "learnings": [],
        "hypothesis_updates": [],
    }

    douyin = (entry.get("platforms") or {}).get("douyin") or {}
    forecast = douyin.get("forecast") or {}
    actual = douyin.get("actual") or {}

    if not forecast:
        return out

    metrics = [
        ("completion_3s", "3s完播"),
        ("completion_rate", "完播率"),
        ("interaction_rate", "互动率"),
        ("avg_watch_s", "均播(s)"),
    ]

    has_any_actual = False
    for key, label in metrics:
        f = forecast.get(key)
        a = actual.get(key)
        if f is None or a is None:
            continue
        if isinstance(f, list) and len(f) == 2:
            lo, hi = float(f[0]), float(f[1])
        else:
            lo = hi = float(f)
        av = float(a)
        has_any_actual = True
        mid = _mid(lo, hi)
        var = _variance_pct(av, mid)
        verdict = "in_range"
        if av < lo:
            verdict = "below_forecast"
        elif av > hi:
            verdict = "above_forecast"

        out["variance"][key] = {
            "label": label,
            "forecast": [lo, hi],
            "forecast_mid": round(mid, 4),
            "actual": av,
            "variance_pct": round(var, 4) if var is not None else None,
            "verdict": verdict,
        }

        if verdict == "below_forecast" and var is not None and var < -0.15:
            out["learnings"].append({
                "id": f"{pid}_{key}_miss",
                "signal": f"{label} 低于预估 >15%",
                "action": "下条：压时长 / 抬首镜变化 / 减 catalog",
                "confidence": "confirmed_by_data",
            })
        elif verdict == "above_forecast" and var is not None and var > 0.10:
            out["learnings"].append({
                "id": f"{pid}_{key}_beat",
                "signal": f"{label} 高于预估",
                "action": "强化当前形式信号（如 number_punch / 0% catalog）",
                "confidence": "confirmed_by_data",
            })

    if has_any_actual:
        out["status"] = "retro_complete"
    return out


def update_hypotheses(brief: dict, analysis: dict, entry: dict) -> list[str]:
    """Promote/reject hypotheses in evolution_brief based on actual."""
    changes: list[str] = []
    var = analysis.get("variance") or {}
    c3 = var.get("completion_3s")
    avg = var.get("avg_watch_s")

    for hyp in brief.get("hypotheses") or []:
        hid = hyp.get("id", "")
        if hid == "E001" and c3:
            threshold = 0.58
            if c3["actual"] >= threshold:
                hyp["confidence"] = "confirmed"
                hyp["verified_at"] = dt.date.today().isoformat()
                hyp["verified_by"] = f"completion_3s={c3['actual']:.2%}"
                changes.append(f"E001 confirmed: 3s={c3['actual']:.1%} ≥ 58%")
            elif c3["actual"] < 0.50:
                hyp["confidence"] = "rejected"
                hyp["verified_at"] = dt.date.today().isoformat()
                changes.append(f"E001 rejected: 3s={c3['actual']:.1%} < 50% → 试场景入戏")

        if hid == "E004" and avg:
            if avg["actual"] >= 12:
                hyp["confidence"] = "confirmed"
                changes.append(f"E004 confirmed: 均播 {avg['actual']:.1f}s ≥ 12s")
            elif avg["actual"] < 10:
                hyp["confidence"] = "rejected"
                changes.append(f"E004 rejected: 均播 {avg['actual']:.1f}s → 压至 45s")

    # Move confirmed hypotheses to learnings（去重）
    existing_ids = {L.get("id") for L in brief.get("learnings") or []}
    for hyp in brief.get("hypotheses") or []:
        hid = hyp.get("id")
        if hyp.get("confidence") != "confirmed" or not hid or hid in existing_ids:
            continue
        rule = hyp.get("if_confirmed")
        if isinstance(rule, list):
            rule = rule[0] if rule else ""
        brief.setdefault("learnings", []).append({
            "id": hid,
            "confidence": "confirmed_by_data",
            "source": hyp.get("source"),
            "signal": hyp.get("signal"),
            "evidence": hyp.get("verified_by") or hyp.get("verify_with"),
            "rule": rule,
            "apply_to": ["D05", "D06", "D07"],
        })
        existing_ids.add(hid)

    # Threshold adjustments
    th = brief.setdefault("thresholds", {})
    if c3 and c3.get("verdict") == "above_forecast":
        old = th.get("form_exclusive_min", 3)
        if old < 4:
            th["form_exclusive_min"] = 4
            changes.append(f"threshold form_exclusive_min: {old} → 4 (3s beat forecast)")
    if c3 and c3.get("verdict") == "below_forecast":
        th["form_catalog_max"] = min(th.get("form_catalog_max", 0.35), 0.25)
        changes.append("threshold form_catalog_max → 0.25 (3s miss)")

    return changes


def sync_week_performance(week_dir: pathlib.Path, project_id: str, entry: dict, analysis: dict) -> None:
    week_path = week_dir / "performance_data.yaml"
    week_data = _read_yaml(week_path)
    entries = week_data.setdefault("entries", [])
    for i, e in enumerate(entries):
        if e.get("project_id") == project_id:
            e["status"] = analysis["status"]
            e["learnings"] = analysis["learnings"]
            if analysis.get("variance"):
                e.setdefault("platforms", {}).setdefault("douyin", {})["variance"] = analysis["variance"]
            entries[i] = e
            break
    else:
        entries.append({**entry, "status": analysis["status"], "learnings": analysis["learnings"]})
    week_data["updated_at"] = dt.datetime.now().isoformat(timespec="seconds")
    _write_yaml(week_path, week_data)

    day_dir = find_day_dir(week_dir, project_id)
    if day_dir:
        perf_path = day_dir / "design" / "performance.yaml"
        perf = _read_yaml(perf_path)
        perf["variance"] = analysis.get("variance", {})
        perf["learnings"] = analysis.get("learnings", [])
        perf["retro_status"] = analysis["status"]
        _write_yaml(perf_path, perf)


def append_evolution_log(week_id: str, project_id: str, changes: list[str], analysis: dict) -> None:
    log_path = ROOT / "docs/design/PERFORMANCE_EVOLUTION_LOG.md"
    if not log_path.exists():
        log_path.write_text("# 投后数据进化日志\n\n", encoding="utf-8")
    lines = [
        f"\n## {dt.date.today().isoformat()} · {week_id} · {project_id}\n",
    ]
    for k, v in (analysis.get("variance") or {}).items():
        lines.append(f"- **{v['label']}:** 预估 {v['forecast'][0]:.0%}–{v['forecast'][1]:.0%} · 实际 **{v['actual']:.1%}** · {v['verdict']}\n")
    for c in changes:
        lines.append(f"- {c}\n")
    for L in analysis.get("learnings") or []:
        lines.append(f"- 学习: {L.get('signal')} → {L.get('action')}\n")
    with log_path.open("a", encoding="utf-8") as f:
        f.writelines(lines)


def print_report(project_id: str, analysis: dict, changes: list[str]) -> None:
    print(f"\n{'='*60}")
    print(f"  进化报告 · {project_id}")
    print(f"{'='*60}")
    print(f"  状态: {analysis['status']}")
    var = analysis.get("variance") or {}
    if not var:
        print("  ⚠ 无 actual 数据 — 填 design/performance.yaml 后重跑")
    else:
        print("\n  偏差:")
        for k, v in var.items():
            pct = v.get("variance_pct")
            pct_s = f"{pct:+.0%}" if pct is not None else "—"
            mid = _mid(v["forecast"][0], v["forecast"][1])
            if k == "avg_watch_s":
                print(
                    f"    · {v['label']}: 预估 {mid:.1f}s → 实际 {v['actual']:.1f}s "
                    f"({pct_s}) [{v['verdict']}]"
                )
            else:
                print(
                    f"    · {v['label']}: 预估 {mid:.1%} → 实际 {v['actual']:.1%} "
                    f"({pct_s}) [{v['verdict']}]"
                )
    if changes:
        print("\n  进化动作:")
        for c in changes:
            print(f"    → {c}")
    if analysis.get("learnings"):
        print("\n  数据学习:")
        for L in analysis["learnings"]:
            print(f"    · {L.get('signal')}: {L.get('action')}")
    print(f"\n  下一步: 读 publish/2026-W26/evolution_brief.yaml · D05 design/evolution_overlay.md")


def check_evolution_applied(week_dir: pathlib.Path, project_id: str) -> int:
    """Verify next topic has evolution overlay before form production."""
    brief = _read_yaml(week_dir / "evolution_brief.yaml")
    if not brief:
        print(f"✗ 缺少 {week_dir.name}/evolution_brief.yaml")
        return 1
    overrides = brief.get("topic_overrides") or {}
    ov = overrides.get(project_id)
    if not ov:
        print(f"⚠ {project_id} 无 topic_overrides（可能尚未发布前置条）")
        return 0
    day_dir = find_day_dir(week_dir, project_id)
    if not day_dir:
        print(f"✗ 找不到 {project_id} 发布目录")
        return 1
    overlay = day_dir / "design" / "evolution_overlay.md"
    if not overlay.exists():
        print(f"✗ 缺少 design/evolution_overlay.md — D05+ 开工前必填")
        return 1
    status = ov.get("status", "")
    if status == "evolution_required":
        print(f"⚠ {project_id} status=evolution_required — 形式层须按 overlay 重做")
    print(f"✓ {project_id} evolution overlay 存在 · brief 已配置")
    src = brief.get("source_days") or []
    print(f"  数据源: {src} · 阈值 exclusive_min={brief.get('thresholds', {}).get('form_exclusive_min')}")
    return 0


def apply_one(week_dir: pathlib.Path, project_id: str, *, require_48h: bool = True) -> int:
    entry = load_entry(week_dir, project_id)
    if not entry:
        print(f"✗ 无 performance 数据: {project_id}")
        return 1

    if require_48h and not has_48h_actual(entry):
        print(f"⏸ {project_id} · 无 48h actual · 进化暂停，等待数据")
        print(f"  → python3 pipeline/import_metrics_48h.py --file your.json")
        return 2

    analysis = analyze_entry(entry)
    brief_path = week_dir / "evolution_brief.yaml"
    brief = _read_yaml(brief_path)
    if not brief:
        print(f"✗ 缺少 evolution_brief.yaml")
        return 1

    changes = []
    if analysis["status"] == "retro_complete":
        changes = update_hypotheses(brief, analysis, entry)
        src = set(brief.get("source_days") or [])
        day = entry.get("day") or project_id.replace("W26", "D")
        src.add(day if day.startswith("D") else f"D{day}")
        brief["source_days"] = sorted(src, key=lambda x: int(x.replace("D", "") or 0))
        pending = [d for d in (brief.get("pending_actual") or []) if d != day]
        brief["pending_actual"] = pending
        brief["updated_at"] = dt.datetime.now().isoformat(timespec="seconds")
        brief.setdefault("changelog", []).append({
            "at": dt.date.today().isoformat(),
            "by": "evolution_apply.py",
            "project_id": project_id,
            "changes": changes,
        })
        _write_yaml(brief_path, brief)
        append_evolution_log(week_dir.name, project_id, changes, analysis)

    sync_week_performance(week_dir, project_id, entry, analysis)
    print_report(project_id, analysis, changes)
    return 0


def apply_week(week_dir: pathlib.Path) -> int:
    week_data = _read_yaml(week_dir / "performance_data.yaml")
    entries = week_data.get("entries") or []
    code = 0
    applied = 0
    for e in entries:
        pid = e.get("project_id")
        if not pid:
            continue
        if not has_48h_actual(e):
            print(f"  跳过 {pid}（无 48h actual · 进化暂停）")
            continue
        rc = apply_one(week_dir, pid, require_48h=False)
        if rc == 0:
            applied += 1
        elif rc != 2:
            code = 1
    if applied == 0:
        print("\n整周：尚无 48h 数据。发布后约 48h 导入 JSON 再跑进化。")
        print("  python3 pipeline/import_metrics_48h.py --status")
    return code


def main() -> int:
    ap = argparse.ArgumentParser(description="投后数据 → 进化简报")
    ap.add_argument("--week", type=pathlib.Path, default=WEEK_DEFAULT)
    ap.add_argument("--id", help="project_id 如 W26D04")
    ap.add_argument("--status", action="store_true", help="查看 48h 数据 / 进化暂停状态")
    ap.add_argument("--check", action="store_true", help="验下一条 evolution 已应用")
    ap.add_argument("--force", action="store_true", help="忽略 48h 标记（调试用）")
    args = ap.parse_args()

    week_dir = args.week.resolve()
    if not week_dir.exists():
        print(f"找不到 {week_dir}", file=sys.stderr)
        return 2

    if args.status:
        import subprocess
        script = ROOT / "pipeline" / "import_metrics_48h.py"
        return subprocess.call([sys.executable, str(script), "--status", "--week", str(week_dir)])

    if args.check:
        if not args.id:
            print("--check 需要 --id W26D05", file=sys.stderr)
            return 2
        return check_evolution_applied(week_dir, args.id)

    if args.id:
        return apply_one(week_dir, args.id, require_48h=not args.force)
    return apply_week(week_dir)


if __name__ == "__main__":
    sys.exit(main())
