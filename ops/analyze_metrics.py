#!/usr/bin/env python3
"""Metrics 闭环 · 读 metrics.csv + rules.yaml → 出 verdict + 推荐动作.

用户每次回填 publish_date / exposure / completion_rate / likes / saves / comments
之后跑这个脚本,自动吐每条内容的状态和下一步建议。

用法:
  python3 ops/analyze_metrics.py                # 全部
  python3 ops/analyze_metrics.py --topic T008   # 只看 T008
  python3 ops/analyze_metrics.py --pending      # 只列待发布
"""
from __future__ import annotations

import argparse
import csv
import pathlib
import sys
from typing import Any

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
METRICS = ROOT / "ops" / "metrics.csv"
RULES = ROOT / "ops" / "rules.yaml"


def load_rows() -> list[dict[str, str]]:
    with METRICS.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_rules() -> dict[str, Any]:
    with RULES.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def to_float(s: str | None) -> float | None:
    if not s or not s.strip():
        return None
    try:
        v = float(s)
        return v / 100.0 if v > 1.5 and "rate" in s.lower() else v
    except ValueError:
        return None


def to_int(s: str | None) -> int | None:
    if not s or not s.strip():
        return None
    try:
        return int(float(s))
    except ValueError:
        return None


def evaluate(row: dict[str, str], rules: dict[str, Any]) -> dict[str, Any]:
    """单行 verdict."""
    cid = row["content_id"]
    platform = row["platform"]
    pdate = row.get("publish_date", "").strip()

    if not pdate:
        return {"id": cid, "platform": platform, "status": "pending",
                "verdict": "未发布", "actions": []}

    exposure = to_int(row.get("exposure_48h")) or to_int(row.get("exposure_7d"))
    cr = to_float(row.get("completion_rate_48h"))
    likes = to_int(row.get("likes_48h")) or to_int(row.get("likes_7d")) or 0
    saves = to_int(row.get("saves_48h")) or to_int(row.get("saves_7d")) or 0
    comments = to_int(row.get("comments_48h")) or to_int(row.get("comments_7d")) or 0

    if exposure is None and cr is None:
        return {"id": cid, "platform": platform, "status": "awaiting_data",
                "verdict": "已发,等数据", "actions": []}

    th = rules["thresholds"]
    actions: list[str] = []
    signals: list[str] = []

    # 曝光分级
    exp_band = "low"
    if exposure is not None:
        if exposure >= th["exposure"]["good"]:
            exp_band = "good"; signals.append(f"曝光 {exposure} ≥ good({th['exposure']['good']})")
        elif exposure >= th["exposure"]["ok"]:
            exp_band = "ok"; signals.append(f"曝光 {exposure} ≥ ok({th['exposure']['ok']})")
        elif exposure >= th["exposure"]["low"]:
            exp_band = "ok-low"; signals.append(f"曝光 {exposure}(中下)")
        else:
            exp_band = "low"; signals.append(f"⚠ 曝光 {exposure} < low({th['exposure']['low']})")

    # 完播
    if cr is not None:
        if cr < th["completion_rate"]["low"]:
            signals.append(f"⚠ 完播 {cr:.0%} < {th['completion_rate']['low']:.0%}")
            actions.append("R03: 砍到 45s,加强前 3s 字幕(钩子重做)")
        elif cr < th["completion_rate"]["ok"]:
            signals.append(f"完播 {cr:.0%} 中等")
        else:
            signals.append(f"✓ 完播 {cr:.0%} ≥ {th['completion_rate']['ok']:.0%}")

    # saves > likes 强信号
    if saves > 0 and saves > likes:
        signals.append(f"✓ 收藏 {saves} > 赞 {likes}(强正向)")
        actions.append("R04: 下批同项目可加干货拆解形态")

    # 评论数
    if comments >= 3:
        signals.append(f"✓ 评论 {comments} 条")
        actions.append("R05: 下批可加故事踩坑形态")

    # 私信信号(从 notes 字段抽)
    notes = row.get("notes", "").lower()
    if "私信" in notes or "dm" in notes or "lead" in notes:
        signals.append("★★ 收到私信(最强信号)")
        actions.append("R06: 截图存 assets/leads/,考虑做 S5 复盘")

    if exp_band == "low" and (cr is None or cr < th["completion_rate"]["low"]):
        verdict = "weak"
    elif exp_band in ("good", "ok"):
        verdict = "ok" if (cr is None or cr >= th["completion_rate"]["low"]) else "watch"
    else:
        verdict = "neutral"

    return {
        "id": cid, "platform": platform,
        "status": "scored", "verdict": verdict,
        "exposure": exposure, "completion_rate": cr,
        "likes": likes, "saves": saves, "comments": comments,
        "signals": signals, "actions": actions,
    }


def print_row(r: dict[str, Any]) -> None:
    bar = "─" * 60
    print(f"\n{r['id']:12s} · {r['platform']:6s} · {r['status']}")
    print(bar)
    if r["status"] == "pending":
        print("  待发布")
        return
    if r["status"] == "awaiting_data":
        print("  已发,数据未回填")
        return
    print(f"  verdict: {r['verdict']}")
    cr = r.get("completion_rate")
    cr_s = f"{cr:.0%}" if cr is not None else "-"
    print(f"  曝光 {r.get('exposure','-')} · 完播 {cr_s} · 赞 {r['likes']} · 藏 {r['saves']} · 评 {r['comments']}")
    print("  信号:")
    for s in r["signals"]:
        print(f"    · {s}")
    if r["actions"]:
        print("  推荐动作:")
        for a in r["actions"]:
            print(f"    → {a}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--topic", help="只看含此前缀的 content_id")
    ap.add_argument("--pending", action="store_true", help="只列待发布")
    args = ap.parse_args()

    rows = load_rows()
    rules = load_rules()
    if args.topic:
        rows = [r for r in rows if r["content_id"].startswith(args.topic)]

    results = [evaluate(r, rules) for r in rows]
    if args.pending:
        results = [r for r in results if r["status"] == "pending"]

    if not results:
        sys.exit("无匹配行")

    for r in results:
        print_row(r)

    print()
    print("─" * 60)
    by_status: dict[str, int] = {}
    for r in results:
        by_status[r["status"]] = by_status.get(r["status"], 0) + 1
    print("汇总: " + " · ".join(f"{k}={v}" for k, v in by_status.items()))


if __name__ == "__main__":
    main()
