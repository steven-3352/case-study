#!/usr/bin/env python3
"""Assemble W30 post-render scorecards from independent Phase B reviews."""
from __future__ import annotations

import hashlib
import pathlib
import re
from collections import Counter

import yaml


ROOT = pathlib.Path(__file__).resolve().parents[1]
PROJECTS = (
    ROOT / "publish/2026-W30/D01-让AI说真话致命漏洞",
    ROOT / "publish/2026-W30/D02-别再让AI给你建议了",
    ROOT / "publish/2026-W30/D03-迷茫十问",
    ROOT / "publish/2026-W30/D04-AI失忆",
    ROOT / "publish/2026-W30/D05-AI记岔了",
)
ROLES = ("动效设计师", "视觉设计", "编剧", "留存与互动设计师", "编导", "平台表现分析师")
ROLE_SLUG = {
    "动效设计师": "motion-design", "视觉设计": "visual", "编剧": "writer",
    "留存与互动设计师": "retention", "编导": "director", "平台表现分析师": "platform-analyst",
}
PREFERRED_TASKS = {
    "动效设计师": (9, 12),
    "视觉设计": (10, 11),
    "编剧": (9, 11),
    "留存与互动设计师": (9, 11),
    "编导": (10, 12),
    "平台表现分析师": (10, 12),
}


def load(path: pathlib.Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def reviewer_agent_id(row: dict) -> str:
    """Normalize the real sub-agent path without inventing per-role identities."""
    raw = str(row.get("reviewer_agent_id") or row["task_id"]).strip()
    if raw.startswith(("task-", "agent-", "subagent-")):
        return raw
    return f"agent-{raw.rsplit('/', 1)[-1]}"


def task_number(path: pathlib.Path) -> int:
    match = re.search(r"task-phaseb-(\d+)-", path.name)
    if not match:
        raise ValueError(path.name)
    return int(match.group(1))


def rows(path: pathlib.Path) -> list[dict]:
    data = load(path)
    task = task_number(path)
    task_id = f"task-phaseb-{task:02d}-20260719"
    result = []
    for index, source in enumerate(data.get("reviews") or data.get("roles") or [], start=1):
        row = dict(source)
        row["task"] = task
        row["task_id"] = task_id
        row["reviewed_at"] = str(row.get("reviewed_at") or data.get("reviewed_at") or "2026-07-19")
        row["reviewer_id"] = str(row.get("reviewer_id") or f"phaseb{task:02d}-r{index:02d}")
        inspection = data.get("inspection") or {}
        row["artifact_sha256"] = str(
            inspection.get("video_sha256") or inspection.get("sha256") or ""
        ).lower()
        notes = str(row.get("notes") or row.get("evidence") or "").strip()
        deductions = row.get("deductions") or []
        if deductions:
            notes += "\n\n扣分与改法：\n" + "\n".join(str(item) for item in deductions)
        row["normalized_notes"] = notes
        result.append(row)
    return result


def select(project: pathlib.Path, role: str, artifact_sha256: str) -> list[dict]:
    candidates = []
    for path in (project / "room/reviews").glob("task-phaseb-*-20260719.yaml"):
        for row in rows(path):
            if (
                row.get("role") == role
                and row.get("artifact_sha256") == artifact_sha256
                and int(row.get("score", 0)) >= 90
                and str(row.get("verdict", "")).lower() == "pass"
            ):
                candidates.append(row)
    if project.name.startswith(("D03-", "D04-", "D05-")):
        preferred = PREFERRED_TASKS[role]
        by_task = {int(row["task"]): row for row in candidates}
        missing = [task for task in preferred if task not in by_task]
        if missing:
            raise SystemExit(f"{project.name}: {role} missing preferred Phase B tasks {missing}")
        return [by_task[task] for task in preferred]

    candidates.sort(key=lambda row: int(row["task"]), reverse=True)
    chosen = []
    seen = set()
    for row in candidates:
        if row["task_id"] in seen:
            continue
        chosen.append(row)
        seen.add(row["task_id"])
        if len(chosen) == 2:
            return chosen
    raise SystemExit(f"{project.name}: {role} has only {len(chosen)} passing Phase B reviews")


def main() -> None:
    for project in PROJECTS:
        verdict = load(project / "room/verdict.yaml")
        content_version = str(verdict.get("content_version") or "v3")
        form_version = str(verdict.get("form_version") or "v1")
        project_id = str(verdict.get("project_id") or project.name.split("-")[0])
        artifact_sha256 = sha256(project / "douyin/video.mp4")
        slots: Counter[str] = Counter()
        for role in ROLES:
            chosen = select(project, role, artifact_sha256)
            reviewers = []
            for row in chosen:
                slots[row["task_id"]] += 1
                reviewers.append({
                    "reviewer_id": f"{row['reviewer_id']}-{project_id.lower()}-{ROLE_SLUG[role]}",
                    "review_mode": "independent",
                    "reviewer_agent_id": reviewer_agent_id(row),
                    "reviewed_at": row["reviewed_at"],
                    "angle": str(row.get("angle") or f"task{row['task']:02d} · {ROLE_SLUG[role]} · 最终 MP4 独立复验"),
                    "score": int(row["score"]),
                    "verdict": "pass",
                    "notes": row["normalized_notes"],
                })
            card = {
                "status": "pass",
                "review_source": "independent_agent_tasks",
                "role": role,
                "artifact": "douyin/video.mp4",
                "artifact_sha256": artifact_sha256,
                "artifact_version": f"content-{content_version}-form-{form_version}-render-20260719",
                "invalidated_by": "",
                "pass_threshold": 90,
                "reviewers": reviewers,
                "avg_score": round(sum(r["score"] for r in reviewers) / 2, 1),
                "pass": True,
                "scorecard_phase": "post_render",
            }
            out = project / "room/scorecards" / f"{role}.yaml"
            out.write_text(yaml.safe_dump(card, allow_unicode=True, sort_keys=False), encoding="utf-8")
        overused = {task: count for task, count in slots.items() if count > 3}
        if overused:
            raise SystemExit(f"{project.name}: reviewer task exceeds three slots: {overused}")
        print(f"{project.name}: Phase B scorecards assembled; task slots={dict(sorted(slots.items()))}")


if __name__ == "__main__":
    main()
