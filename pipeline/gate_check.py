#!/usr/bin/env python3
"""内容门禁 · fail-closed 校验（铁律工具 enforcement）.

  python3 pipeline/gate_check.py --id W26D04
  python3 pipeline/gate_check.py --day D04-复购流失
  python3 pipeline/gate_check.py --week publish/2026-W26 --all

phase:
  pre_render   Phase A · render 前（**TTS/gpt-image 须此阶段 PASS**）
  post_render  Phase B · 有 douyin/video.mp4 后
  approve      外发前全量（含证据物 + 讨论室）

有成本工序（TTS · gpt-image · P004 build · render.py）:
  **仅当 gate_check(pre_render) PASS 后允许**；否则 fail-closed 退出。
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys
from dataclasses import dataclass, field

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
WEEK_DEFAULT = ROOT / "publish" / "2026-W26"

SCORECARD_PASS = 90

# 洞察层工种：artifact 在 insights/，不随 content_version 迭代
INSIGHT_ROLES = frozenset({
    "网络调研员", "记者", "选题深挖师", "内核提炼师", "事实校验员",
})

# 产出工种 scorecard 须随 script/render 级联作废（见 INVALIDATE_MAP）
SCRIPT_BOUND_ARTIFACT_RE = re.compile(
    r"scripts/|script_vo|retention_beat|motion_wow|storyboard|video\.mp4|cover\.png",
    re.I,
)

FAKE_REVIEWER_ID_RE = re.compile(
    r"审校|子\s*Agent|[-·][甲乙丙]$",
    re.I,
)

NOTES_MIN_LEN = 40
NOTES_DEDUCTION_RE = re.compile(r"扣|\(-?\d+\)|-\d{1,2}(?:\s|$|：)|−\d")

# 真实互评 · 2026-06-25 升级：须独立 Task 留痕
REVIEWER_AGENT_ID_RE = re.compile(r"^(task-|agent-|subagent-)[a-zA-Z0-9_-]{8,}$")
BATCH_AGENT_ID_BLOCKLIST = frozenset({"batch", "script", "auto", "self", "same-session"})

SCORECARD_ROLES_PHASE_A = [
    "网络调研员", "记者", "选题深挖师", "内核提炼师", "事实校验员",
    "形式选型师", "平台原生策划", "纪录片导演", "编剧", "留存与互动设计师",
    "形式策略官", "动效技术导演", "动效设计师", "动效分镜师", "编导",
]

SCORECARD_ROLES_PHASE_B = [
    "动效设计师", "编剧", "视觉设计", "留存与互动设计师", "编导",
]

PLATFORM_ANALYST_ROLE = "平台表现分析师"

# 表现形式层 · catalog 模板（pain/compare/cta 等通用镜）
CATALOG_TEMPLATE_RE = re.compile(
    r"^(?:01[a-z_]*|02_pain|03_|04_claude|05_|06_compare|07_|08_cta|09_)",
    re.I,
)
# 专属模板：d{NN}_ 前缀（如 d04_excel_dread）
EXCLUSIVE_TEMPLATE_RE = re.compile(r"^d\d{2}_", re.I)

FORM_LAYER_ROLES = frozenset({"动效设计师", "形式选型师", "动效分镜师", "平台原生策划"})

# 表现形式 90+ 硬门槛（与 scorecard 纸面分独立校验）
FORM_EXCLUSIVE_MIN = 3          # 至少 3 种不同专属视觉隐喻
FORM_CATALOG_RATIO_MAX = 0.35   # catalog 模板时长占比上限
FORM_TEMPLATE_MAX_REPEAT = 1    # 同一 template 最多 1 镜
FORM_MIN_DISTINCT_SCENES = 6    # 48s 视频至少 6 种不同画面节奏

# D08 教训：写了 Pexels/custom/专属看板，但实际 render 被通用 evidence/newsprint 吞掉。
# 外发前必须校验“形式承诺已兑现”，禁止重复造旧轮子。
GENERIC_RENDER_BLOCK_RE = re.compile(
    r"pipeline/render\.py|通用\s*evidence|newsprint|newspaper|render_carousel|"
    r"blocked_old_evidence_render",
    re.I,
)
CUSTOM_FORM_PROMISE_RE = re.compile(
    r"Pexels|b-roll|B-roll|custom|专属|客户看板|私域看板|agent\s*分拣|"
    r"分工卡|mixed_broll|custom_visual",
    re.I,
)
CUSTOM_TEMPLATE_RE = re.compile(r"^(?:d\d{2}_|pexels_|custom_)", re.I)
ADVANCED_MOTION_RE = re.compile(
    r"Web\s*3D|Three(?:\.js)?|GSAP|复杂\s*HTML|WebGL|3D\s*消息|3D\s*分拣|"
    r"风险雷达|HTML\s*截帧|p004|p005|three_|gsap_",
    re.I,
)
DATA_LEVER_RE = re.compile(
    r"completion_3s|3s|3秒|完播|completion_rate|理解|看懂|收藏|评论|互动|停划",
    re.I,
)
FORM_STRATEGY_REQUIRED_LABELS = ("镜头任务", "候选表达", "数据杠杆", "推荐方案")
MOTION_TECH_REQUIRED_LABELS = ("适用性", "可读性", "资产", "导出", "风险")

# 注意力引导系统（折进 form_strategy · 2026-06-26 · 直接硬门）
# 标准：templates/design/attention_guidance_system.md
ATTENTION_REQUIRED_LABELS = ("单焦点", "时刻类型", "加料不加赢家")
ATTENTION_MOMENT_RE = re.compile(r"停划|看懂|交接|收藏钩|评论钩")
ATTENTION_MOMENT_MIN = 2   # 时刻分型至少覆盖 2 类
ATTENTION_FOCUS_MIN = 3    # 单焦点声明至少覆盖 3 个关键镜

SCRIPT_REVIEW_REQUIRED_SIGNERS = ("内核提炼师", "留存设计师", "留存与互动设计师")
SCRIPT_REVIEW_POST_RENDER_SIGNERS = ("编导",)

# 变更 → 须重评的工种（级联作废）
INVALIDATE_MAP: dict[str, list[str]] = {
    "script": ["编剧", "留存与互动设计师", "编导"],
    "storyboard": ["动效分镜师", "动效设计师", "留存与互动设计师"],
    "render": ["动效设计师", "视觉设计", "编剧", "编导", "留存与互动设计师"],
    "cover": ["视觉设计", "编导"],
}


@dataclass
class GateResult:
    ok: bool
    phase: str
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _read_yaml(path: pathlib.Path) -> dict:
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _read_text(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _content_version(day_dir: pathlib.Path) -> str:
    v = _read_yaml(day_dir / "room" / "verdict.yaml")
    return str(v.get("content_version") or "")


def _has_douyin_video(day_dir: pathlib.Path) -> bool:
    return (day_dir / "douyin" / "video.mp4").exists()


def _is_forbidden_self_review(role: str, reviewer_id: str) -> bool:
    """产出者不得评自己；禁止「编剧审校-A」式假分身."""
    rid = reviewer_id.strip()
    if rid == role:
        return True
    for sep in ("-", "·", "_"):
        if rid.startswith(role + sep):
            return True
    # 工种名出现在 reviewer_id 内（如 编剧审校-A 评 留存 仍禁止）
    if len(role) >= 2 and role in rid:
        return True
    return bool(FAKE_REVIEWER_ID_RE.search(rid))


def _artifact_version_must_match_content(role: str, artifact: str, content_version: str, av: str) -> bool:
    if not content_version or not av:
        return True
    if role in INSIGHT_ROLES or str(artifact).startswith("insights/"):
        return True
    return content_version in av


def _validate_reviewer_authenticity(
    role: str,
    card: dict,
    reviewers: list[dict],
    threshold: int,
    errors: list[str],
    *,
    require_agent_id: bool = False,
) -> None:
    """真实互评：非形式盖章."""
    role_name = str(card.get("role", role))
    notes_bodies: list[str] = []

    for r in reviewers:
        rid = str(r.get("reviewer_id", "")).strip()
        angle = str(r.get("angle", "")).strip()
        score = int(r.get("score", 0))
        verdict = str(r.get("verdict", "")).strip().lower()
        notes = str(r.get("notes") or "").strip()
        review_mode = str(r.get("review_mode", "")).strip().lower()
        agent_id = str(r.get("reviewer_agent_id") or "").strip()

        if not rid:
            errors.append(f"{role}: reviewer_id 为空")
            continue

        if _is_forbidden_self_review(role_name, rid):
            errors.append(f"{role}: 禁止自评/假分身 reviewer_id={rid!r}")

        if review_mode != "independent":
            errors.append(
                f"{role}: {rid} 缺少 review_mode: independent（须独立 Agent/Task readonly 打分）"
            )

        if require_agent_id:
            if not agent_id:
                errors.append(
                    f"{role}: {rid} 缺少 reviewer_agent_id（须独立 Task，格式 task-xxx）"
                )
            elif agent_id.lower() in BATCH_AGENT_ID_BLOCKLIST or not REVIEWER_AGENT_ID_RE.match(agent_id):
                errors.append(
                    f"{role}: {rid} reviewer_agent_id={agent_id!r} 无效"
                )

        if verdict not in ("pass", "fail"):
            errors.append(f"{role}: {rid} verdict 须为 pass|fail，不得 pending/空")

        if score >= threshold and verdict != "pass":
            errors.append(f"{role}: {rid} score={score}≥{threshold} 但 verdict={verdict}")
        if score < threshold and verdict != "fail":
            errors.append(f"{role}: {rid} score={score}<{threshold} 但 verdict={verdict}")

        if card.get("pass") and len(notes) < NOTES_MIN_LEN:
            errors.append(
                f"{role}: {rid} pass 时 notes 须≥{NOTES_MIN_LEN}字且含具体扣分/改法"
            )

        if card.get("pass") and score < 100 and not NOTES_DEDUCTION_RE.search(notes):
            errors.append(
                f"{role}: {rid} score={score}<100 时 notes 须写清扣分项（如 扣(-8) 或 -8）"
            )

        # 禁止套话式放水
        if card.get("pass") and re.search(r"^微扣\(-?\d+\)[：:]\s*[\u4e00-\u9fff]{1,12}[。．]?\s*$", notes):
            errors.append(f"{role}: {rid} notes 为套话式微扣，须写可改动作")

        notes_bodies.append(notes)

    if len(notes_bodies) == 2 and notes_bodies[0] and notes_bodies[0] == notes_bodies[1]:
        errors.append(f"{role}: 两位 reviewer notes 完全相同（疑似同 Agent 复制）")


def _collect_reviewer_agent_ids(day_dir: pathlib.Path) -> list[str]:
    ids: list[str] = []
    sc_dir = day_dir / "room" / "scorecards"
    if not sc_dir.exists():
        return ids
    for path in sc_dir.glob("*.yaml"):
        card = _read_yaml(path)
        for r in card.get("reviewers") or []:
            aid = str(r.get("reviewer_agent_id") or "").strip()
            if aid:
                ids.append(aid)
    return ids


def check_reviewer_agent_isolation(day_dir: pathlib.Path, errors: list[str]) -> None:
    """同一 reviewer_agent_id 不得评超过 3 个工种（疑似单 session 批量打分）."""
    from collections import Counter

    ids = _collect_reviewer_agent_ids(day_dir)
    if not ids:
        return
    counts = Counter(ids)
    for aid, n in counts.items():
        if n > 3:
            errors.append(
                f"reviewer_agent_id={aid!r} 出现在 {n} 个评审位（>3 疑似批量互评，须独立 Task）"
            )


def check_scorecard_phase_b(day_dir: pathlib.Path, *, phase: str, errors: list[str]) -> None:
    """Phase B 工种 scorecard 须 post_render 复验."""
    if phase not in ("post_render", "approve"):
        return
    sc_dir = day_dir / "room" / "scorecards"
    for role in SCORECARD_ROLES_PHASE_B:
        path = sc_dir / f"{role}.yaml"
        if not path.exists():
            continue
        card = _read_yaml(path)
        sc_phase = str(card.get("scorecard_phase") or "")
        if sc_phase != "post_render":
            errors.append(
                f"{role}: scorecard_phase 须为 post_render（render 后独立 Task 复验）"
            )


def check_platform_analyst_scorecard(day_dir: pathlib.Path, errors: list[str]) -> None:
    if not _has_douyin_video(day_dir):
        return
    path = day_dir / "room" / "scorecards" / f"{PLATFORM_ANALYST_ROLE}.yaml"
    if not path.exists():
        errors.append(f"外发前缺少 scorecard: {PLATFORM_ANALYST_ROLE}.yaml")
        return
    card = _read_yaml(path)
    if not card.get("pass"):
        errors.append(f"{PLATFORM_ANALYST_ROLE}: pass 须为 true")


def validate_scorecards(
    day_dir: pathlib.Path,
    *,
    phase: str,
    content_version: str,
    errors: list[str],
) -> None:
    sc_dir = day_dir / "room" / "scorecards"
    if not sc_dir.exists():
        errors.append(f"缺少 room/scorecards/（铁律 ≥2 人互评 ≥{SCORECARD_PASS}）")
        return

    index_path = day_dir / "room" / "scorecards_index.yaml"
    if not index_path.exists():
        errors.append("缺少 room/scorecards_index.yaml")
    else:
        idx = _read_yaml(index_path)
        if not idx.get("required_roles_phase_a"):
            errors.append("scorecards_index 缺少 required_roles_phase_a")
        if phase in ("post_render", "approve") and not idx.get("required_roles_phase_b"):
            errors.append("scorecards_index 缺少 required_roles_phase_b")

    roles = list(SCORECARD_ROLES_PHASE_A)
    if phase in ("post_render", "approve"):
        roles = list(dict.fromkeys(roles + SCORECARD_ROLES_PHASE_B))

    for role in roles:
        path = sc_dir / f"{role}.yaml"
        if not path.exists():
            errors.append(f"缺少 scorecard: {role}.yaml")
            continue
        card = _read_yaml(path)
        reviewers = card.get("reviewers") or []
        threshold = int(card.get("pass_threshold", SCORECARD_PASS))

        if not card.get("pass"):
            errors.append(f"{role}: pass 须为 true（不可仅填 verdict gates）")

        av = str(card.get("artifact_version") or "")
        artifact = str(card.get("artifact") or "")
        if content_version and av and not _artifact_version_must_match_content(role, artifact, content_version, av):
            errors.append(
                f"{role}: artifact_version={av!r} 与 verdict.content_version={content_version!r} 不一致"
            )

        if len(reviewers) < 2:
            errors.append(f"{role}: reviewer 不足 2 人")
            continue

        ids = [str(r.get("reviewer_id", "")) for r in reviewers]
        angles = [str(r.get("angle", "")) for r in reviewers]
        if len(set(ids)) < 2:
            errors.append(f"{role}: reviewer_id 重复")
        if len(set(angles)) < 2:
            errors.append(f"{role}: angle 相同")

        _validate_reviewer_authenticity(
            role, card, reviewers, threshold, errors,
            require_agent_id=phase in ("post_render", "approve"),
        )

        scores = [int(r.get("score", 0)) for r in reviewers]
        for s, r in zip(scores, reviewers):
            if s < threshold:
                errors.append(f"{role}: {r.get('reviewer_id')} 得分 {s} < {threshold}")
            notes = str(r.get("notes") or "").strip()
            if s < threshold and len(notes) < 20:
                errors.append(f"{role}: fail 时 notes 须含具体扣分项（≥20 字）")
        if scores:
            avg = sum(scores) / len(scores)
            if avg < threshold:
                errors.append(f"{role}: avg {avg:.1f} < {threshold}")

        # 级联作废：script/render 变更后，产出层 scorecard 不得仍 pass 旧版
        if card.get("pass") and content_version and SCRIPT_BOUND_ARTIFACT_RE.search(artifact):
            if av and content_version not in av:
                errors.append(
                    f"{role}: 产出已变更至 {content_version}，scorecard 仍 pass 旧版 {av}（级联作废）"
                )
            inv = str(card.get("invalidated_by") or "")
            if inv and content_version in inv and card.get("pass"):
                errors.append(f"{role}: invalidated_by={inv} 但未重评，不得 pass")

    if phase in ("post_render", "approve"):
        check_scorecard_phase_b(day_dir, phase=phase, errors=errors)
        check_reviewer_agent_isolation(day_dir, errors=errors)


def check_script_review(day_dir: pathlib.Path, *, phase: str, errors: list[str]) -> None:
    path = day_dir / "design" / "script_review.md"
    if not path.exists():
        errors.append("缺少 design/script_review.md")
        return
    text = _read_text(path)
    if not re.search(r"status:\s*\*\*pass\*\*|status:\s*pass", text, re.I):
        errors.append("script_review 须 status: pass")

    for signer in SCRIPT_REVIEW_REQUIRED_SIGNERS:
        if signer in text and re.search(rf"\[ \].*{re.escape(signer)}", text):
            errors.append(f"script_review: {signer} 未联签")

    if phase in ("post_render", "approve"):
        for signer in SCRIPT_REVIEW_POST_RENDER_SIGNERS:
            if re.search(rf"\[ \].*{re.escape(signer)}", text):
                errors.append(f"script_review Phase B: {signer} 须听 mp4 后联签")


_VERSION_NUM_RE = re.compile(r"v(\d+)", re.I)
NARRATIVE_HOMOGENITY_RE = re.compile(
    r"叙事骨架|改造实录|flow→terminal|flow->terminal|近\s*D\d{2}|"
    r"叙事.*同质|lecture\s*感|口令感",
    re.I,
)


def _version_number(label: str) -> int | None:
    m = _VERSION_NUM_RE.search(str(label or ""))
    return int(m.group(1)) if m else None


def check_form_redo_content_gate(day_dir: pathlib.Path, errors: list[str]) -> None:
    """形式升版时禁止静默复用旧脚本 pass（D02 · content_form_split_gates §9）."""
    verdict = _read_yaml(day_dir / "room" / "verdict.yaml")
    form_v = str(verdict.get("form_version") or "").strip()
    content_v = str(verdict.get("content_version") or "").strip()
    if not form_v or not content_v:
        return

    form_n = _version_number(form_v)
    content_n = _version_number(content_v)
    if form_n is None or content_n is None or form_n <= content_n:
        return

    sr_text = _read_text(day_dir / "design" / "script_review.md")
    if not sr_text.strip():
        errors.append("form 升版但缺少 design/script_review.md")
        return

    discussion = _read_text(day_dir / "room" / "discussion.md")
    narrative_flagged = bool(NARRATIVE_HOMOGENITY_RE.search(discussion))
    has_content_redo = bool(re.search(r"content_redo:\s*(?:\*\*)?true(?:\*\*)?", sr_text, re.I))
    has_ab_frozen = bool(re.search(r"content_ab_frozen:\s*(?:\*\*)?true(?:\*\*)?", sr_text, re.I))

    if has_content_redo:
        m = re.search(r"content_redo_target:\s*(?:\*\*)?(v\d+)(?:\*\*)?", sr_text, re.I)
        if m and narrative_flagged:
            target_n = _version_number(m.group(1))
            if target_n is not None and target_n <= content_n:
                errors.append(
                    f"discussion 标叙事同质，content_redo_target 须 > {content_v}（见 content_form_split_gates §9.2）"
                )
        return

    if has_ab_frozen:
        if narrative_flagged:
            errors.append(
                f"discussion 标叙事同质（{form_v} vs {content_v}），禁止 content_ab_frozen；须 content_redo: true"
            )
        else:
            rat = re.search(r"content_ab_rationale:\s*\|?\s*\n([\s\S]+?)(?:\n\S|\Z)", sr_text)
            rat_body = (rat.group(1) if rat else "").strip()
            if len(rat_body) < 40:
                errors.append("content_ab_frozen: true 但 content_ab_rationale 不足 40 字")
            elif not re.search(r"Round|A/B|固定脚本|content_ab|形式.*实验", discussion, re.I):
                errors.append("content_ab_frozen 须在 discussion 记录形式实验 Round/理由")
        return

    errors.append(
        f"form_version={form_v} 高于 content_version={content_v}："
        "script_review 须 content_redo: true 或 content_ab_frozen: true（§9 content_form_split_gates）"
    )


def check_cover_review(day_dir: pathlib.Path, errors: list[str]) -> None:
    video = day_dir / "douyin" / "video.mp4"
    cover = day_dir / "douyin" / "cover.png"
    if not video.exists():
        return

    cr_path = day_dir / "design" / "cover_review.md"
    if not cr_path.exists():
        errors.append("有 video.mp4 但缺少 design/cover_review.md")
        return

    cr_text = _read_text(cr_path)
    cv = _content_version(day_dir)

    # 封面时间点须与 content.yaml 一致
    cover_at: float | None = None
    proj_id = _read_yaml(day_dir / "meta.yaml").get("project_id")
    if proj_id:
        content = _read_yaml(ROOT / "projects" / str(proj_id) / "content.yaml")
        cover_at = (content.get("douyin") or {}).get("cover", {}).get("at")

    m = re.search(r"@([\d.]+)s", cr_text)
    cr_at = float(m.group(1)) if m else None
    if cover_at is not None and cr_at is not None and abs(cover_at - cr_at) > 0.05:
        errors.append(f"cover_review @{cr_at}s 与 content.yaml cover.at={cover_at} 不一致")

    if cv and cv not in cr_text and "pass" in cr_text.lower():
        errors.append(f"cover_review 未标注 content_version={cv}（可能过期）")

    if cover.exists() and cr_path.stat().st_mtime < video.stat().st_mtime - 1:
        errors.append("cover_review 早于 video.mp4 修改时间（render 后须复验封面）")

    if cover.exists() and cover.stat().st_mtime < video.stat().st_mtime - 1:
        errors.append(
            "cover.png 早于 video.mp4（须从 v4 首镜重导封面，不得沿用旧 cover）"
        )
    elif not cover.exists():
        errors.append("有 video.mp4 但缺少 douyin/cover.png")

    if cover.exists():
        _check_palette_neon(cover, errors)


def _check_palette_neon(png: pathlib.Path, errors: list[str]) -> None:
    """禁霓虹色门 · 主视觉蓝紫像素占比 > 5% → fail.

    详 docs/DECISIONS.md Q9「禁霓虹色细则」.
    """
    try:
        from pipeline.gate_check_palette import analyze, is_real_screenshot
    except Exception as e:
        errors.append(f"禁霓虹色门: 无法 import gate_check_palette ({e})")
        return
    if is_real_screenshot(png):
        return
    ratio, top5 = analyze(png)
    if ratio > 0.05:
        errors.append(
            f"禁霓虹色门 FAIL · {png.name} 蓝紫像素 {ratio:.1%} > 5% (top: "
            f"{', '.join(h for h, _ in top5[:3])}) → 详 DECISIONS Q9"
        )


def check_motion_wow(day_dir: pathlib.Path, errors: list[str]) -> None:
    if not _has_douyin_video(day_dir):
        return
    path = day_dir / "design" / "motion_wow.md"
    if not path.exists():
        errors.append("缺少 design/motion_wow.md")
        return
    text = _read_text(path)
    if "CREATIVE" not in text and "创意" not in text:
        errors.append("motion_wow 缺少 CREATIVE/专属创意点说明")
    # Phase B 未勾选
    phase_b_block = text.split("复验")[-1] if "复验" in text else ""
    if re.search(r"- \[ \]", phase_b_block):
        errors.append("motion_wow Phase B 复验项仍有 [ ] 未勾选")


def check_evidence(day_dir: pathlib.Path, errors: list[str]) -> None:
    if not _has_douyin_video(day_dir):
        return
    vo_notes = day_dir / "design" / "vo_listen_notes.md"
    if not vo_notes.exists():
        errors.append("Phase B 缺少 design/vo_listen_notes.md（听片证据）")
        return
    text = _read_text(vo_notes)
    cv = _content_version(day_dir)
    if cv and cv not in text:
        errors.append(f"vo_listen_notes 未标注 content_version={cv}")
    if not re.search(r"\d+\.?\d*s", text):
        errors.append("vo_listen_notes 须含 mp4 时间戳（如 12.5s）")


def _storyboard_path(day_dir: pathlib.Path) -> pathlib.Path | None:
    proj_id = _read_yaml(day_dir / "meta.yaml").get("project_id")
    if not proj_id:
        verdict = _read_yaml(day_dir / "room" / "verdict.yaml")
        proj_id = verdict.get("project_id")
    if not proj_id:
        return None
    sb = ROOT / "projects" / str(proj_id) / "storyboard.yaml"
    return sb if sb.exists() else None


def _load_storyboard_scenes(day_dir: pathlib.Path) -> list[dict]:
    sb_path = _storyboard_path(day_dir)
    if not sb_path:
        return []
    data = _read_yaml(sb_path)
    return list(data.get("scenes") or [])


def check_visual_diversity(day_dir: pathlib.Path, errors: list[str]) -> None:
    """表现形式硬门禁 · 与 scorecard 纸面分独立 · fail-closed."""
    if not _has_douyin_video(day_dir):
        return
    scenes = _load_storyboard_scenes(day_dir)
    if not scenes:
        errors.append("有 video.mp4 但无法读取 projects/*/storyboard.yaml")
        return

    total_dur = sum(float(s.get("duration") or 0) for s in scenes)
    if total_dur <= 0:
        errors.append("storyboard 场景 duration 总和为 0")
        return

    catalog_dur = 0.0
    exclusive_kinds: set[str] = set()
    template_counts: dict[str, int] = {}

    for sc in scenes:
        tpl = str(sc.get("template") or "")
        dur = float(sc.get("duration") or 0)
        template_counts[tpl] = template_counts.get(tpl, 0) + 1
        if CATALOG_TEMPLATE_RE.match(tpl):
            catalog_dur += dur
        if EXCLUSIVE_TEMPLATE_RE.match(tpl):
            exclusive_kinds.add(tpl)

    catalog_ratio = catalog_dur / total_dur
    distinct_templates = len(template_counts)

    if len(exclusive_kinds) < FORM_EXCLUSIVE_MIN:
        errors.append(
            f"形式层：专属模板 {len(exclusive_kinds)} 种 < {FORM_EXCLUSIVE_MIN} "
            f"（{sorted(exclusive_kinds) or '无'}）"
        )
    if catalog_ratio > FORM_CATALOG_RATIO_MAX + 1e-6:
        errors.append(
            f"形式层：catalog 时长占比 {catalog_ratio:.0%} > {FORM_CATALOG_RATIO_MAX:.0%}"
        )
    repeats = {t: c for t, c in template_counts.items() if c > FORM_TEMPLATE_MAX_REPEAT}
    if repeats:
        detail = ", ".join(f"{t}×{c}" for t, c in sorted(repeats.items()))
        errors.append(f"形式层：同一 template 重复 >{FORM_TEMPLATE_MAX_REPEAT} 镜（{detail}）")
    if total_dur >= 40 and distinct_templates < FORM_MIN_DISTINCT_SCENES:
        errors.append(
            f"形式层：不同 template 仅 {distinct_templates} 种 < {FORM_MIN_DISTINCT_SCENES} "
            f"（{total_dur:.0f}s 视频）"
        )
    check_no_dark_p004_clone(day_dir, scenes, errors)


def check_no_dark_p004_clone(
    day_dir: pathlib.Path, scenes: list[dict], errors: list[str],
) -> None:
    """铁律：禁止复用 P004 暗色终端族（换 d06_ 文件名不换皮仍 fail）."""
    tpl_dir = ROOT / "pipeline" / "p004_video" / "templates"
    dark_markers = (
        'href="../shared/style.css"',
        "background: #0a0e14",
        "background: var(--bg-deep)",
        "--bg-deep:",
    )
    dark_hits: list[str] = []
    for sc in scenes:
        tpl = str(sc.get("template") or "")
        if not tpl:
            continue
        path = tpl_dir / tpl
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        if any(m in text for m in dark_markers):
            dark_hits.append(tpl)
    if dark_hits:
        errors.append(
            f"形式层：模板仍属 P004 暗色族（须自含浅色/蓝图 CSS，禁 style.css）: "
            + ", ".join(sorted(set(dark_hits)))
        )
    # 首镜禁止「黑底大红数字 punch」语法（D04/D05 族）
    if scenes:
        first = tpl_dir / str(scenes[0].get("template") or "")
        if first.exists():
            body = first.read_text(encoding="utf-8")
            if "#0a0e14" in body or "--bg-deep" in body:
                errors.append("形式层：首镜仍为暗色 P004 族 · 须形式 v2 整片重做")


def check_hook_benchmark(day_dir: pathlib.Path, errors: list[str]) -> None:
    """完播北极星 · 同行前3秒拆解 · pre_render 必填."""
    hb = day_dir / "insights" / "hook_benchmark.md"
    retention = day_dir / "retention_beat_sheet.md"
    if not hb.exists():
        errors.append("缺少 insights/hook_benchmark.md（网络调研员 · ≥2 条同行前3秒拆解）")
        return
    text = _read_text(hb)
    if not re.search(r"参考\s*1|参考1", text):
        errors.append("hook_benchmark 缺少「参考 1」")
    if not re.search(r"参考\s*2|参考2", text):
        errors.append("hook_benchmark 缺少「参考 2」")
    for label in ("人设", "镜头", "音乐"):
        if label not in text:
            errors.append(f"hook_benchmark 须拆解：{label}")
    urls = re.findall(r"https?://[^\s\)|\]>]+", text)
    if len(urls) < 2:
        errors.append(
            "hook_benchmark 须含 ≥2 条可核验 URL（https://…，禁止「抖音搜…」占位）"
        )
    if retention.exists():
        rt = _read_text(retention)
        if "0–3s" not in rt and "0-3s" not in rt:
            errors.append("retention_beat_sheet 缺少 0–3s 节拍行")
        if "完播北极星" not in rt and "完播目标" not in rt:
            errors.append("retention_beat_sheet 缺少完播北极星/完播目标")


def _combined_form_context(day_dir: pathlib.Path) -> str:
    """Collect form-related docs to decide whether advanced motion is promised."""
    parts: list[str] = []
    for rel in (
        "design/form_strategy.md",
        "design/format_spec.md",
        "design/motion_wow.md",
        "design/pre_publish_forecast.md",
        "room/verdict.yaml",
        "room/discussion.md",
    ):
        parts.append(_read_text(day_dir / rel))
    sb_path = _storyboard_path(day_dir)
    if sb_path:
        parts.append(_read_text(sb_path))
    meta = _read_yaml(day_dir / "meta.yaml")
    verdict = _read_yaml(day_dir / "room" / "verdict.yaml")
    project_id = str(meta.get("project_id") or verdict.get("project_id") or "")
    if project_id:
        parts.append(_read_text(ROOT / "projects" / project_id / "content.yaml"))
    return "\n".join(p for p in parts if p)


def check_form_strategy(day_dir: pathlib.Path, errors: list[str]) -> None:
    """形式策略会硬门禁：逐镜表达方案必须为数据假设服务."""
    path = day_dir / "design" / "form_strategy.md"
    if not path.exists():
        errors.append("缺少 design/form_strategy.md（形式策略官 · 逐镜表达方案竞争）")
        return

    text = _read_text(path)
    if len(text.strip()) < 500:
        errors.append("form_strategy 内容过短（<500 字），疑似用摘要应付；须逐镜比较表达方案")

    for label in FORM_STRATEGY_REQUIRED_LABELS:
        if label not in text:
            errors.append(f"form_strategy 缺少必填字段：{label}")

    if not DATA_LEVER_RE.search(text):
        errors.append("form_strategy 未声明数据杠杆（3s/完播/理解/收藏/评论/互动/停划）")

    candidates = ("实拍", "B-roll", "2D", "UI", "看板", "消息流", "GSAP", "Three", "Web 3D", "截图", "字幕")
    candidate_hits = sum(1 for c in candidates if re.search(re.escape(c), text, re.I))
    if candidate_hits < 3:
        errors.append("form_strategy 候选表达方式少于 3 类；须比较而不是直接指定方案")

    if re.search(r"默认用|为了快|更酷|沿用上一条|套用", text):
        errors.append("form_strategy 含非法选型理由（默认/为了快/更酷/沿用/套用）")

    recommendation_blocks = re.findall(r"推荐方案|推荐：|推荐:", text)
    if len(recommendation_blocks) < 3:
        errors.append("form_strategy 推荐方案少于 3 处；须覆盖关键镜头而非只给整体路线")

    # 注意力引导系统（折进 · 2026-06-26 硬门）· templates/design/attention_guidance_system.md
    for label in ATTENTION_REQUIRED_LABELS:
        if label not in text:
            errors.append(
                f"form_strategy 缺少注意力引导必填字段：{label}"
                "（见 templates/design/attention_guidance_system.md §6）"
            )
    moment_hits = len(set(ATTENTION_MOMENT_RE.findall(text)))
    if moment_hits < ATTENTION_MOMENT_MIN:
        errors.append(
            f"form_strategy 时刻分型不足（停划/看懂/交接/收藏钩/评论钩 ≥{ATTENTION_MOMENT_MIN} 类，"
            f"现 {moment_hits} 类）"
        )
    focus_decls = len(re.findall(r"单焦点", text))
    if focus_decls < ATTENTION_FOCUS_MIN:
        errors.append(
            f"form_strategy 单焦点声明少于 {ATTENTION_FOCUS_MIN} 处；每个关键镜须声明唯一视线落点"
        )


def check_motion_tech_plan(day_dir: pathlib.Path, errors: list[str]) -> None:
    """Web 3D / GSAP / 复杂动效被承诺时，必须有技术可行性审查."""
    combined = _combined_form_context(day_dir)
    if not ADVANCED_MOTION_RE.search(combined):
        return

    path = day_dir / "design" / "motion_tech_plan.md"
    if not path.exists():
        errors.append(
            "承诺/使用 Web 3D、GSAP、复杂 HTML 动效或风险雷达，但缺少 design/motion_tech_plan.md"
        )
        return

    text = _read_text(path)
    if len(text.strip()) < 400:
        errors.append("motion_tech_plan 内容过短（<400 字），须写清可行性、资产、导出与风险控制")
    for label in MOTION_TECH_REQUIRED_LABELS:
        if label not in text:
            errors.append(f"motion_tech_plan 缺少必填检查：{label}")
    if not DATA_LEVER_RE.search(text):
        errors.append("motion_tech_plan 未说明高级动效服务的数据指标")
    if re.search(r"更酷|炫酷|先做再说|后面再补", text):
        errors.append("motion_tech_plan 含非法技术理由（更酷/炫酷/先做再说/后面再补）")


def check_pre_publish_forecast(day_dir: pathlib.Path, errors: list[str]) -> None:
    """平台表现分析师 · 未发布数据预估 · 外发前必填."""
    if not _has_douyin_video(day_dir):
        return
    path = day_dir / "design" / "pre_publish_forecast.md"
    if not path.exists():
        errors.append("Phase B 缺少 design/pre_publish_forecast.md（平台表现分析师）")
        return
    text = _read_text(path)
    cv = _content_version(day_dir)
    if cv and cv not in text:
        errors.append(f"pre_publish_forecast 未标注 content_version={cv}")

    if not re.search(r"平台表现分析师|表现分析师", text):
        errors.append("pre_publish_forecast 须标注工种：平台表现分析师")

    # 完播北极星 · 首要预估项
    has_3s = bool(re.search(r"3s.{0,24}%|completion_3s", text, re.I))
    has_completion = bool(re.search(r"完播.{0,24}%|completion_rate", text, re.I))
    if not has_3s:
        errors.append("pre_publish_forecast 须含 3s 完播预估（如 3s 54–64%）")
    if not has_completion:
        errors.append("pre_publish_forecast 须含完播率预估（如 完播 14–19%）")

    # 表现形式层 fail → 禁止 approve 外发
    if re.search(r"表现形式.{0,40}fail|表现形式层.{0,20}fail", text, re.I | re.S):
        errors.append("pre_publish_forecast：表现形式层 fail — 须 v11+ 形式重做后再 approve")
    elif re.search(r"不建议.*外发|blocked_form|形式.*不可", text, re.I):
        errors.append("pre_publish_forecast 结论：现成片不建议外发（形式层未过关）")


def check_custom_form_fulfillment(day_dir: pathlib.Path, errors: list[str]) -> None:
    """D08 硬门禁：形式承诺必须在像素/素材/模板中兑现.

    目的不是偏好某个技术，而是阻断：
      format_spec 写 Pexels/custom/专属看板 → 实际用通用 evidence/newsprint 出片 → ready_to_publish
    """
    verdict = _read_yaml(day_dir / "room" / "verdict.yaml")
    meta = _read_yaml(day_dir / "meta.yaml")
    project_id = str(meta.get("project_id") or verdict.get("project_id") or "")
    content = _read_yaml(ROOT / "projects" / project_id / "content.yaml") if project_id else {}
    storyboard_text = ""
    sb_path = _storyboard_path(day_dir)
    if sb_path and sb_path.exists():
        storyboard_text = _read_text(sb_path)

    format_text = _read_text(day_dir / "design" / "format_spec.md")
    forecast_text = _read_text(day_dir / "design" / "pre_publish_forecast.md")
    verdict_text = (day_dir / "room" / "verdict.yaml").read_text(encoding="utf-8") if (day_dir / "room" / "verdict.yaml").exists() else ""

    combined = "\n".join([format_text, forecast_text, verdict_text, storyboard_text])

    if GENERIC_RENDER_BLOCK_RE.search(combined):
        errors.append(
            "形式层：文档/决议含通用 evidence/newsprint/render.py 阻塞或禁用信号，"
            "不得 approve；须专属视觉重做后删除阻塞结论"
        )

    promises_custom_form = bool(CUSTOM_FORM_PROMISE_RE.search(combined))
    if not promises_custom_form:
        return

    scenes = _load_storyboard_scenes(day_dir)
    templates = [str(s.get("template") or "") for s in scenes]
    custom_templates = [t for t in templates if CUSTOM_TEMPLATE_RE.match(t)]

    # 通用 render.py 的 content segments 会把 web/evidence 渲成窗口卡片；若仍有 web/evidence 且无专属模板/素材，直接 fail。
    douyin_segments = (content.get("douyin") or {}).get("segments") or []
    segment_sources = {str(s.get("source") or "") for s in douyin_segments if isinstance(s, dict)}
    has_generic_segments = bool(segment_sources & {"evidence", "web"})

    broll_paths = []
    for sc in scenes:
        data = sc.get("data") or {}
        if isinstance(data, dict):
            for key in ("source", "broll", "video", "asset"):
                val = data.get(key)
                if isinstance(val, str):
                    broll_paths.append(val)
        src = sc.get("source")
        if isinstance(src, str):
            broll_paths.append(src)

    real_broll_exists = any(
        (ROOT / p).exists() if not pathlib.Path(p).is_absolute() else pathlib.Path(p).exists()
        for p in broll_paths
        if p.endswith((".mp4", ".mov", ".webm", ".png", ".jpg", ".jpeg"))
    )

    if not custom_templates and not real_broll_exists:
        errors.append(
            "形式层：承诺了 Pexels/custom/专属视觉，但 storyboard 未使用 dNN_/pexels_/custom_ 模板，"
            "也未引用真实本地素材；禁止用通用 evidence 卡片兑现"
        )

    if has_generic_segments and not real_broll_exists and len(custom_templates) < FORM_EXCLUSIVE_MIN:
        errors.append(
            "形式层：content.yaml 仍以 evidence/web 段为主体，且缺少 ≥3 个专属模板或真实素材；"
            "会复现 D08 模板化结果，禁止外发"
        )

    if re.search(r"Pexels|b-roll|B-roll", combined) and not real_broll_exists:
        errors.append(
            "形式层：承诺使用 Pexels/B-roll，但未在 storyboard 引用已下载本地素材；"
            "不得只把 Pexels 写进说明"
        )


def check_form_layer_scorecards(day_dir: pathlib.Path, errors: list[str]) -> None:
    """形式层工种 scorecard 须 honest ≥90；纸面 90+ 但视觉审计 fail 时由 check_visual_diversity 兜底."""
    sc_dir = day_dir / "room" / "scorecards"
    if not sc_dir.exists():
        return
    cv = _content_version(day_dir)
    for role in FORM_LAYER_ROLES:
        card_path = sc_dir / f"{role}.yaml"
        if not card_path.exists():
            errors.append(f"形式层缺少 scorecard: {role}.yaml")
            continue
        card = _read_yaml(card_path)
        if not card.get("pass"):
            errors.append(f"形式层 {role}: pass=false")
            continue
        reviews = card.get("reviewers") or card.get("reviews") or []
        if len(reviews) < 2:
            errors.append(f"形式层 {role}: reviews < 2")
            continue
        scores = [float(r.get("score") or 0) for r in reviews]
        avg = sum(scores) / len(scores)
        if avg < SCORECARD_PASS:
            errors.append(f"形式层 {role}: avg {avg:.1f} < {SCORECARD_PASS}")


def check_discussion_phase_b(day_dir: pathlib.Path, errors: list[str]) -> None:
    text = _read_text(day_dir / "room" / "discussion.md")
    if not text:
        errors.append("缺少 room/discussion.md")
        return
    # 须有 Round≥6 且提及 mp4/听/像素
    if not re.search(r"Round\s*[6-9]|Round\s*1[0-9]", text):
        errors.append("discussion 缺少 Phase B Round 6+")
    tail = text[-4000:]
    if not re.search(r"mp4|听|像素|PNG|video\.mp4", tail):
        errors.append("discussion 最近 Round 未对 mp4/PNG/听感具名发言")
    if "交锋" not in text and "取舍" not in text:
        errors.append("discussion 缺少交锋或取舍记录")


def check_verdict_not_hand_waved(day_dir: pathlib.Path, result: GateResult) -> None:
    verdict = _read_yaml(day_dir / "room" / "verdict.yaml")
    if verdict.get("status") == "approved" and result.errors:
        result.errors.append(
            "verdict=approved 但 gate_check 未通过 — 禁止手填 gates.*=true 绕过工具"
        )


def assert_paid_work_allowed(day_dir: pathlib.Path, *, operation: str = "TTS/render") -> None:
    """有成本工序门禁 · 未 pre_render PASS 则 SystemExit."""
    r = gate_check(day_dir, phase="pre_render")
    if r.ok:
        return
    lines = "\n".join(f"  · {e}" for e in r.errors[:15])
    extra = f"\n  · …共 {len(r.errors)} 项" if len(r.errors) > 15 else ""
    raise SystemExit(
        f"⛔ {operation} 禁止 · {day_dir.name} gate_check(pre_render) 未 PASS\n"
        f"铁律：全工种 scorecard 90+ + script_review pass 后才允许 TTS/gpt-image/render。\n{lines}{extra}"
    )


def gate_check(
    day_dir: pathlib.Path,
    *,
    phase: str = "approve",
) -> GateResult:
    """phase: pre_render | post_render | approve"""
    errors: list[str] = []
    warnings: list[str] = []
    cv = _content_version(day_dir)

    if phase == "pre_render":
        validate_scorecards(day_dir, phase="pre_render", content_version=cv, errors=errors)
        check_script_review(day_dir, phase="pre_render", errors=errors)
        check_form_redo_content_gate(day_dir, errors=errors)
        check_form_strategy(day_dir, errors=errors)
        check_motion_tech_plan(day_dir, errors=errors)
        check_custom_form_fulfillment(day_dir, errors=errors)
        check_hook_benchmark(day_dir, errors=errors)
        mw = day_dir / "design" / "motion_wow.md"
        if not mw.exists():
            errors.append("render 前缺少 design/motion_wow.md")

    elif phase == "post_render":
        validate_scorecards(day_dir, phase="post_render", content_version=cv, errors=errors)
        check_script_review(day_dir, phase="post_render", errors=errors)
        check_cover_review(day_dir, errors=errors)
        check_motion_wow(day_dir, errors=errors)

    elif phase == "approve":
        validate_scorecards(day_dir, phase="post_render", content_version=cv, errors=errors)
        check_script_review(day_dir, phase="post_render", errors=errors)
        check_cover_review(day_dir, errors=errors)
        check_motion_wow(day_dir, errors=errors)
        check_evidence(day_dir, errors=errors)
        check_discussion_phase_b(day_dir, errors=errors)
        check_form_strategy(day_dir, errors=errors)
        check_motion_tech_plan(day_dir, errors=errors)
        check_visual_diversity(day_dir, errors=errors)
        check_custom_form_fulfillment(day_dir, errors=errors)
        check_pre_publish_forecast(day_dir, errors=errors)
        check_form_layer_scorecards(day_dir, errors=errors)
        check_platform_analyst_scorecard(day_dir, errors=errors)
        check_form_redo_content_gate(day_dir, errors=errors)

    else:
        errors.append(f"未知 phase: {phase}")

    result = GateResult(ok=len(errors) == 0, phase=phase, errors=errors, warnings=warnings)
    check_verdict_not_hand_waved(day_dir, result)
    result.ok = len(result.errors) == 0
    return result


def find_day_dir(week_dir: pathlib.Path, *, project_id: str | None, day_slug: str | None) -> pathlib.Path | None:
    if day_slug:
        p = week_dir / day_slug if (week_dir / day_slug).exists() else WEEK_DEFAULT / day_slug
        return p if p.exists() else None
    if project_id:
        for d in week_dir.iterdir():
            if not d.is_dir():
                continue
            meta = _read_yaml(d / "meta.yaml")
            if meta.get("project_id") == project_id:
                return d
            verdict = _read_yaml(d / "room" / "verdict.yaml")
            if verdict.get("project_id") == project_id:
                return d
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description="内容门禁 fail-closed 校验")
    ap.add_argument("--week", type=pathlib.Path, default=WEEK_DEFAULT)
    ap.add_argument("--id", help="project_id 如 W26D04")
    ap.add_argument("--day", help="目录名如 D04-复购流失")
    ap.add_argument("--phase", choices=["pre_render", "post_render", "approve"], default="approve")
    ap.add_argument("--all", action="store_true", help="校验周内全部 Dxx")
    args = ap.parse_args()

    week_dir = args.week
    dirs: list[pathlib.Path] = []
    if args.all:
        dirs = sorted(p for p in week_dir.iterdir() if p.is_dir() and re.match(r"D\d{2}-", p.name))
    else:
        d = find_day_dir(week_dir, project_id=args.id, day_slug=args.day)
        if not d:
            print("找不到发布目录", file=sys.stderr)
            return 2
        dirs = [d]

    exit_code = 0
    for day_dir in dirs:
        r = gate_check(day_dir, phase=args.phase)
        name = day_dir.name
        if r.ok:
            print(f"✓ {name} · gate_check({args.phase}) PASS")
        else:
            exit_code = 1
            print(f"✗ {name} · gate_check({args.phase}) FAIL ({len(r.errors)} 项)")
            for e in r.errors:
                print(f"    · {e}")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
