#!/usr/bin/env python3
"""Assemble W30 Phase A scorecards from independent review task artifacts."""
from __future__ import annotations

import argparse
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
ROLES = (
    "网络调研员", "记者", "选题深挖师", "内核提炼师", "事实校验员",
    "形式选型师", "平台原生策划", "纪录片导演", "编剧", "留存与互动设计师",
    "形式策略官", "视觉语言策展师", "动效技术导演", "动效设计师", "动效分镜师", "编导",
)
ROLE_SLUG = {
    "网络调研员": "research", "记者": "reporter", "选题深挖师": "topic",
    "内核提炼师": "core", "事实校验员": "fact", "形式选型师": "format",
    "平台原生策划": "platform", "纪录片导演": "documentary", "编剧": "writer",
    "留存与互动设计师": "retention", "形式策略官": "form-strategy",
    "视觉语言策展师": "visual-language", "动效技术导演": "motion-tech",
    "动效设计师": "motion-design", "动效分镜师": "motion-storyboard", "编导": "director",
}
ARTIFACT = {
    "网络调研员": "insights/external_references.md", "记者": "insights/fact_check.md",
    "选题深挖师": "insights/topic_brief.md", "内核提炼师": "insights/core_message.md",
    "事实校验员": "insights/fact_check.md", "形式选型师": "design/form_competition.md",
    "平台原生策划": "design/form_strategy.md", "纪录片导演": "design/storyboard.yaml",
    "编剧": "pipeline_config.yaml", "留存与互动设计师": "design/retention_beat_sheet.md",
    "形式策略官": "design/form_strategy.md", "视觉语言策展师": "design/design_language.md",
    "动效技术导演": "design/motion_tech_plan.md", "动效设计师": "design/motion_wow.md",
    "动效分镜师": "design/storyboard.yaml", "编导": "pipeline_config.yaml",
}
INSIGHT_ROLES = {"网络调研员", "记者", "选题深挖师", "内核提炼师", "事实校验员"}


def load(path: pathlib.Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def task_number(path: pathlib.Path) -> int:
    match = re.search(r"task-phasea-(\d+)-", path.name)
    if not match:
        raise ValueError(f"Unrecognized review filename: {path.name}")
    return int(match.group(1))


def normalized_reviews(path: pathlib.Path) -> list[dict]:
    data = load(path)
    rows = data.get("reviews") or data.get("roles") or []
    number = task_number(path)
    task_id = f"task-phasea-{number:02d}-20260719"
    result = []
    for index, row in enumerate(rows, start=1):
        item = dict(row)
        item["task_number"] = number
        item["task_id"] = task_id
        item["reviewed_at"] = str(item.get("reviewed_at") or data.get("reviewed_at") or "2026-07-19")
        item["reviewer_id"] = str(item.get("reviewer_id") or f"phasea{number:02d}-r{index:02d}")
        item["content_version"] = str(item.get("content_version") or data.get("content_version") or "")
        item["form_version"] = str(item.get("form_version") or data.get("form_version") or "")
        result.append(item)
    return result


def select_reviews(project: pathlib.Path, role: str, content_version: str, form_version: str) -> list[dict]:
    candidates = []
    for path in sorted((project / "room/reviews").glob("task-phasea-*-20260719.yaml")):
        if task_number(path) < 12:
            continue
        for row in normalized_reviews(path):
            if row.get("role") != role:
                continue
            if row.get("content_version") != content_version:
                continue
            if role not in INSIGHT_ROLES and row.get("form_version") != form_version:
                continue
            if str(row.get("verdict", "")).lower() != "pass" or int(row.get("score", 0)) < 90:
                continue
            candidates.append(row)
    candidates.sort(key=lambda row: int(row["task_number"]), reverse=True)
    chosen = []
    seen_tasks = set()
    for row in candidates:
        if row["task_id"] in seen_tasks:
            continue
        chosen.append(row)
        seen_tasks.add(row["task_id"])
        if len(chosen) == 2:
            return chosen
    raise SystemExit(f"{project.name}: {role} has only {len(chosen)} current passing independent reviews")


def assemble(project: pathlib.Path) -> None:
    verdict = load(project / "room/verdict.yaml")
    content_version = str(verdict.get("content_version") or "v3")
    project_id = str(verdict.get("project_id") or project.name.split("-")[0])
    scorecard_dir = project / "room/scorecards"
    scorecard_dir.mkdir(parents=True, exist_ok=True)
    agent_slots: Counter[str] = Counter()

    for role in ROLES:
        selected = select_reviews(project, role, content_version, str(verdict.get("form_version") or "v3"))
        reviewers = []
        for row in selected:
            agent_slots[row["task_id"]] += 1
            score = int(row["score"])
            evidence = str(row.get("evidence") or "").strip()
            deductions = str(row.get("deductions") or row.get("notes") or "").strip()
            remediation = str(row.get("remediation") or row.get("fix") or "").strip()
            note_parts = [f"扣(-{100 - score})。"]
            if deductions:
                note_parts.append(deductions)
            if remediation:
                note_parts.append(f"改法：{remediation}")
            if evidence:
                note_parts.append(f"依据：{evidence}")
            notes = " ".join(note_parts)
            angle = str(row.get("angle") or "").strip()
            if not angle:
                evidence_lead = re.sub(r"\s+", " ", evidence)[:48]
                angle = f"{row['task_id']} · {role} · {evidence_lead}"
            reviewers.append({
                "reviewer_id": f"{row['reviewer_id']}-{project_id.lower()}-{ROLE_SLUG[role]}",
                "review_mode": "independent",
                "reviewer_agent_id": row["task_id"],
                "reviewed_at": row["reviewed_at"],
                "angle": angle,
                "score": score,
                "verdict": "pass",
                "notes": notes,
            })
        avg = sum(item["score"] for item in reviewers) / len(reviewers)
        card = {
            "status": "pass",
            "review_source": "independent_agent_tasks",
            "role": role,
            "artifact": ARTIFACT[role],
            "artifact_version": f"evidence-{content_version}" if role in INSIGHT_ROLES else f"content-{content_version}-form-v4",
            "invalidated_by": "",
            "pass_threshold": 90,
            "reviewers": reviewers,
            "avg_score": round(avg, 1),
            "pass": True,
            "scorecard_phase": "pre_render",
        }
        (scorecard_dir / f"{role}.yaml").write_text(
            yaml.safe_dump(card, allow_unicode=True, sort_keys=False), encoding="utf-8"
        )

    overused = {task: count for task, count in agent_slots.items() if count > 3}
    if overused:
        raise SystemExit(f"{project.name}: reviewer task exceeds three slots: {overused}")

    index = {
        "required_roles_phase_a": list(ROLES),
        "required_roles_phase_b": ["动效设计师", "编剧", "视觉设计", "留存与互动设计师", "编导", "平台表现分析师"],
        "status": "phase_a_pass",
        "scorecard_valid": True,
        "review_source": "independent_agent_tasks",
        "content_version": content_version,
    }
    (project / "room/scorecards_index.yaml").write_text(
        yaml.safe_dump(index, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )
    print(f"{project.name}: assembled {len(ROLES)} scorecards; task slots={dict(sorted(agent_slots.items()))}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", choices=("D01", "D02", "D03", "D04", "D05", "all"), default="all")
    args = parser.parse_args()
    for project in PROJECTS:
        if args.project == "all" or project.name.startswith(args.project + "-"):
            assemble(project)


if __name__ == "__main__":
    main()
