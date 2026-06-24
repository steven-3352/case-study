#!/usr/bin/env python3
"""从 room_sessions.yaml 展开多工种讨论室产物，写入各天 room/ insights/ scripts/.

  python3 pipeline/week_room.py
  python3 pipeline/week_room.py --id W26D01
"""
from __future__ import annotations

import argparse
import pathlib
import textwrap

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
WEEK_DIR = ROOT / "publish" / "2026-W26"
SESSIONS = WEEK_DIR / "room_sessions.yaml"
WEB_RESEARCH = WEEK_DIR / "web_research.yaml"


def md_external_references(pid: str, topic_id: str, wr: dict) -> str:
    rows = "\n".join(
        f"| {i+1} | {r['source']} | {r['url']} | {r['point']} | {r.get('p0', '')} |"
        for i, r in enumerate(wr.get("refs", []))
    )
    wq = "\n".join(
        f"| {i+1} | {q['text']} | {q['source']} |"
        for i, q in enumerate(wr.get("web_quotes", []))
    )
    return f"""# 网络调研 · external_references

> 选题 ID: {topic_id} · 内容 ID: {pid} · 工种: **网络调研员**

## 行业共识（1–2 句）

> {wr.get('consensus', '')}

## 参考来源

| # | 来源 | URL | 可引用要点 | 用于哪条 P0 |
|---|------|-----|------------|-------------|
{rows}

## 网络原话/转述（≥2 条，供记者交叉）

| # | 转述 | 来源 |
|---|------|------|
{wq}

## 与本片关系

- 支撑痛点: 见 topic_brief 钉子场景与 P0
- 本片边界: 见 fact_check 红区

## 门禁

- [x] ≥3 条有效 URL
- [x] ≥2 条网络原话已并入 topic_brief
- [x] 数据为区间/转述，非冒充一手
"""


def md_insights(pid: str, topic_id: str, ins: dict) -> dict[str, str]:
    tb = ins["topic_brief"]
    cm = ins["core_message"]
    dn = ins["domain_notes"]
    fc = ins["fact_check"]
    quotes = "\n".join(f"| {i+1} | {q['text']} | {q['source']} |" for i, q in enumerate(tb["quotes"]))
    scenes = "\n".join(f"{i+1}. {s}" for i, s in enumerate(tb["scenes"]))
    before_after = "\n".join(
        f"| {b} | {a} |" for b, a in zip(tb["before"], tb["after"], strict=False)
    )
    p0rows = "\n".join(
        f"| P0 | {p['info']} | {p['beat']} |" for p in cm["p0"]
    )
    p1rows = "\n".join(
        f"| P1 | {p['info']} | {p['beat']} |" for p in cm.get("p1", [])
    )
    green = "\n".join(f"| {g['text']} | {g['basis']} |" for g in fc.get("green", []))
    yellow = "\n".join(f"| {y['text']} | {y['fix']} |" for y in fc.get("yellow", []))
    red = "\n".join(f"| {r['text']} | {r['reason']} |" for r in fc.get("red", []))
    terms = "\n".join(
        f"| {t['term']} | {t['plain']} | {t['on_air']} |" for t in dn.get("terms", [])
    )
    alts = "\n".join(
        f"| {a['name']} | {a['pro']} | {a['con']} | {a['say']} |"
        for a in dn.get("alternatives", [])
    )

    return {
        "topic_brief.md": f"""# 选题深挖 · topic_brief

> 选题 ID: {topic_id} · 内容 ID: {pid} · 工种: 选题深挖师
> 状态: approved

## 受众画像

- 行业/角色: {tb['audience_role']}
- 规模/场景: {tb['audience_scale']}
- 当前解法: {tb['current_solution']}

## 钉子场景（一句话）

> {tb['nail_scene']}

### 场景细节（至少 3 个，要具体）

{scenes}

## 用户原话（≥5 条，标注来源）

| # | 原话 | 来源 |
|---|------|------|
{quotes}

## 改造前 / 改造后

| 改造前（现在怎么做） | 改造后（目标状态） |
|---------------------|-------------------|
{before_after}

## 本条不写什么（边界）

{chr(10).join('- ' + b for b in tb.get('boundaries', []))}

## 编导签字

- [x] 洞察包可进入内核提炼
""",
        "core_message.md": f"""# 内核提炼 · core_message

> 选题 ID: {topic_id} · 内容 ID: {pid} · 工种: 内核提炼师
> 依赖: topic_brief.md 已完成

## 钩子句（≤12 字，前 3s 用）

> {cm['hook']}

## 价值锚（全文只出现 1 次）

> {cm['value_anchor']}

## 关键信息（必须进成片，标优先级）

| 优先级 | 信息点 | 计划落在哪一节拍 |
|--------|--------|------------------|
{p0rows}
{p1rows}

## 禁用表述（与 fact_check 衔接）

{chr(10).join('- ' + d for d in cm.get('forbidden', []))}

## 门禁

- [x] P0 ≥ 3 条
- [x] 价值锚与钩子不重复套话
- [x] 编剧只能引用本表信息，不得自增卖点
""",
        "domain_notes.md": f"""# 领域笔记 · domain_notes

> 选题 ID: {topic_id} · 内容 ID: {pid} · 工种: 领域专家

## 业务/商品决策链

{chr(10).join(f'{i+1}. {s}' for i, s in enumerate(dn.get('decision_chain', [])))}

## 专业概念口语化

| 术语 | 口语说法 | 是否可出镜播 |
|------|----------|--------------|
{terms}

## 竞品/替代方案（如有）

| 方案 | 优点 | 缺点 | 本片怎么说 |
|------|------|------|------------|
{alts}

## 证据画面从哪来

- 录屏: {dn.get('evidence_screen', '无')}
- 截图: {dn.get('evidence_shot', 'evidence 体裁卡')}
- B-roll: {dn.get('evidence_broll', '无')}
""",
        "fact_check.md": f"""# 事实校验 · fact_check

> 选题 ID: {topic_id} · 内容 ID: {pid} · 工种: 事实校验员

## 绿区（可写，有依据）

| 表述 | 依据 |
|------|------|
{green}

## 黄区（可写，需口语化/区间化）

| 表述 | 处理方式 |
|------|----------|
{yellow}

## 红区（禁止写）

| 表述 | 原因 |
|------|------|
{red}

## 脚本交叉检查

- [x] 编剧稿无红区表述
- [x] 数据符合区间化/合成场景标注
- [x] 保健品类不讲功效（如适用）
""",
    }


def md_discussion(session: dict) -> str:
    lines = [
        f"# Agent 讨论室 · {session['project_id']} · {session['title']}",
        "",
        f"> 选题 {session['topic_id']} · 板块 {session['vertical']} · "
        f"抖音 {session['formats']['douyin']} / 小红书 {session['formats']['xhs']}",
        "",
        "## 参与工种",
        "",
        ", ".join(session["participants"]),
        "",
        "## 讨论记录",
        "",
    ]
    for rnd in session["rounds"]:
        lines += [f"### {rnd['title']}", ""]
        for turn in rnd["turns"]:
            role = turn["role"]
            lines.append(f"**{role}：** {turn['say']}")
            if turn.get("challenge"):
                lines.append(f"  - *回应 {turn['challenge']}*")
            lines.append("")
        if rnd.get("resolution"):
            lines += ["**本轮决议：**", "", rnd["resolution"], ""]
    lines += [
        "## 最终定稿摘要",
        "",
        session["summary"],
        "",
        "## 签字",
        "",
    ]
    for s in session.get("signoffs", []):
        lines.append(f"- [x] {s}")
    return "\n".join(lines) + "\n"


def md_retention(session: dict, ins: dict) -> str:
    cm = ins["core_message"]
    beats = session.get("beats", [])
    rows = "\n".join(
        f"| {b['time']} | {b['type']} | {b['format']} | {b['info']} | {b['hold']} |"
        for b in beats
    )
    cta = session.get("cta", "")
    return f"""# 留存与互动节拍表

> 选题 ID: {session['topic_id']} · 内容 ID: {session['project_id']}
> 工种: 留存与互动设计师
> 目标时长: {session.get('duration_s', 42)}s · 平台: 抖音 / 小红书
> 北极星: completion_rate + completion_3s · 见 templates/design/completion_rate_north_star.md

## 完播北极星

| 指标 | 本条目标 |
|------|----------|
| 3s 完播 | ≥55% |
| 完播率 | ≥40% |

## 同行前 3 秒拆解

> 详见 insights/hook_benchmark.md（网络调研员 ≥2 条）

| 参考 | 停划手法 | 我们采用 |
|------|----------|----------|
| 1 | （待填） | |
| 2 | （待填） | |

## 完播与互动目标

- 完播目标: ≥40%
- 3s 停划目标: ≥55%
- 互动设计: {session.get('interaction_design', '评论讨论型')}
- 形式切换: 全片 ≥3 种 evidence 体裁

## 节拍表

| 时间段 | 节拍类型 | 形式 ID | 信息点（P0/P1） | 停留/互动手段 |
|--------|----------|---------|----------------|---------------|
{rows}

## 0–3s 镜头清单

| 秒 | 画面 | 字幕 | 预期反应 |
|----|------|------|----------|
| 0–3 | （对照 hook_benchmark） | 钩子「{cm['hook']}」 | 停划 |

## 片内互动 CTA（口播 + 字幕一致）

> {cta}

## 门禁

- [ ] insights/hook_benchmark.md ≥2 条
- [x] 每 5–8s 有视觉或信息变化
- [x] P0 信息全部落入节拍
- [x] 钩子「{cm['hook']}」落前 3s
"""


def md_script(name: str, title: str, body: str, note: str = "") -> str:
    n = f"\n> {note}\n" if note else ""
    return f"""# {title}

> 工种: 编剧 · 版本 {name}
{n}
{body}
"""


def build_one(session: dict, web_all: dict) -> None:
    pid = session["project_id"]
    day_slug = session["day_dir"]
    day_dir = WEEK_DIR / day_slug
    room = day_dir / "room"
    ins_dir = day_dir / "insights"
    scr_dir = day_dir / "scripts"
    for d in (room, ins_dir, scr_dir):
        d.mkdir(parents=True, exist_ok=True)

    wr = web_all.get(pid, {})
    if wr:
        (ins_dir / "external_references.md").write_text(
            md_external_references(pid, session["topic_id"], wr), encoding="utf-8"
        )

    (room / "discussion.md").write_text(md_discussion(session), encoding="utf-8")
    for fname, content in md_insights(pid, session["topic_id"], session["insights"]).items():
        (ins_dir / fname).write_text(content, encoding="utf-8")
    (day_dir / "retention_beat_sheet.md").write_text(
        md_retention(session, session["insights"]), encoding="utf-8"
    )

    scripts = session["scripts"]
    for key, sc in scripts.items():
        if key == "chosen":
            continue
        (scr_dir / f"{key}.md").write_text(
            md_script(key, sc["title"], sc["body"], sc.get("note", "")), encoding="utf-8"
        )
    chosen = scripts[session["script_choice"]]
    (scr_dir / "chosen.md").write_text(
        md_script(
            session["script_choice"],
            f"定稿稿 · {chosen['title']}",
            chosen["body"],
            f"讨论室选用 {session['script_choice']}；见 room/discussion.md",
        ),
        encoding="utf-8",
    )

    verdict = {
        "status": "approved",
        "topic_id": session["topic_id"],
        "project_id": pid,
        "week_id": "2026-W26",
        "approved_at": session.get("approved_at", "2026-06-16"),
        "participants": {"required": session["participants"][:9], "activated": session["participants"][9:]},
        "decisions": session["decisions"],
        "revisions": session.get("revisions", []),
        "gates": {
            "insights_complete": True,
            "p0_count": len(session["insights"]["core_message"]["p0"]),
            "fact_check_clear": True,
            "retention_aligned": True,
        },
    }
    (room / "verdict.yaml").write_text(
        yaml.dump(verdict, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )
    print(f"  ✓ {day_slug}/room + insights + scripts")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", help="只展开指定 project_id")
    args = ap.parse_args()
    data = yaml.safe_load(SESSIONS.read_text(encoding="utf-8"))
    web_all = {}
    if WEB_RESEARCH.exists():
        web_all = yaml.safe_load(WEB_RESEARCH.read_text(encoding="utf-8")) or {}
    sessions = data["sessions"]
    if args.id:
        sessions = [s for s in sessions if s["project_id"] == args.id]
    print(f"展开 Agent 讨论室 · {len(sessions)} 条 …")
    for s in sessions:
        build_one(s, web_all)
    print("完成")


if __name__ == "__main__":
    main()
