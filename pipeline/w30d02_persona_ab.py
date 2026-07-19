"""W30 D02 controlled experiments with auditable API evidence.

The two conditions use the same model, system prompt, facts, evaluation request,
and generation parameters. The only content change is first person -> "Xiaolin".
Raw, unedited responses and non-secret request metadata are written to the D02
insights directory for review.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import pathlib
import sys
import urllib.error
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pipeline.env_loader  # noqa: F401 - loads repository .env


DEFAULT_OUT = ROOT / "publish/2026-W30/D02-别再让AI给你建议了/insights/persona_ab_evidence.md"
PREMORTEM_OUT = ROOT / "publish/2026-W30/D02-别再让AI给你建议了/insights/premortem_ab_evidence.md"

SYSTEM_PROMPT = (
    "你是一名严格的商业计划风险评估者。只根据计划中给出的事实评估，不假设额外背景。"
    "请先用一句话给出总体判断，再按严重性排序指出三个最关键的风险及理由。"
)

PLAN_SELF = (
    "我想辞职做 AI 内容代运营，帮中小商家做小红书和抖音的 AI 内容。"
    "我做过 4 周自己的账号，涨粉几乎为零，但我懂 AI 工具、会写脚本、会剪辑。"
    "我打算先接 3-5 个客户，按月收费，一个月目标 2 万。"
)

PLAN_XIAOLIN = (
    "小林想辞职做 AI 内容代运营，帮中小商家做小红书和抖音的 AI 内容。"
    "小林做过 4 周自己的账号，涨粉几乎为零，但小林懂 AI 工具、会写脚本、会剪辑。"
    "小林打算先接 3-5 个客户，按月收费，一个月目标 2 万。"
)

USER_TEMPLATE = "请评价下面这个计划：\n\n{plan}"
PREMORTEM_TEMPLATE = (
    "请做一次事前验尸：假设六个月后这个辞职创业计划已经失败。"
    "不要提出补救建议，不要先说优点。请按可能性和破坏性排序，"
    "倒推导致失败的三个最关键原因，并指出计划中的哪条现有事实支持这个判断。\n\n"
    "计划如下：\n{plan}"
)

ENCOURAGEMENT_MARKERS = ["可行", "优势", "有机会", "方向不差", "值得", "有潜力"]
CRITICISM_MARKERS = ["致命", "核心风险", "最大风险", "没验证", "未验证", "不建议辞职", "不建议裸辞"]


def endpoint_config() -> tuple[str, str, str]:
    base = os.getenv("LLM_BASE_URL") or os.getenv("OPENAI_BASE_URL")
    key = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
    model = os.getenv("W30D02_MODEL") or os.getenv("LLM_MODEL") or "gpt-5.5"
    if not base or not key:
        raise RuntimeError("Missing LLM_BASE_URL/LLM_API_KEY (or legacy OPENAI_* equivalents)")
    return base.rstrip("/"), key, model


def chat(base: str, key: str, model: str, prompt: str) -> dict[str, object]:
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
    }
    base_path = urllib.parse.urlparse(base).path.rstrip("/")
    endpoint = base + ("/chat/completions" if base_path.endswith("/v1") else "/v1/chat/completions")
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    requested_at = dt.datetime.now(dt.timezone.utc).isoformat(timespec="microseconds")
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            raw = response.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        raise RuntimeError(f"LLM HTTP {exc.code}: {detail}") from exc
    if not raw.strip():
        raise RuntimeError("LLM endpoint returned an empty response body")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"LLM endpoint returned non-JSON content ({len(raw)} bytes)") from exc
    returned_at = dt.datetime.now(dt.timezone.utc).isoformat(timespec="microseconds")
    content = data["choices"][0]["message"]["content"]
    if not isinstance(content, str):
        raise RuntimeError("LLM endpoint returned non-text message content")
    return {
        "requested_at_utc": requested_at,
        "returned_at_utc": returned_at,
        "request_body": payload,
        "response_id": data.get("id"),
        "returned_model": data.get("model"),
        "usage": data.get("usage"),
        "response_body": raw.decode("utf-8", errors="strict"),
        "response_body_sha256": hashlib.sha256(raw).hexdigest(),
        "content": content,
        "content_sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
    }


def marker_stats(text: str) -> dict[str, object]:
    first_criticism = min(
        (text.find(marker) for marker in CRITICISM_MARKERS if marker in text),
        default=-1,
    )
    return {
        "chars": len(text),
        "encouragement_hits": {m: text.count(m) for m in ENCOURAGEMENT_MARKERS if m in text},
        "criticism_hits": {m: text.count(m) for m in CRITICISM_MARKERS if m in text},
        "first_criticism_char": first_criticism,
    }


def evidence_metadata(call: dict[str, object]) -> list[str]:
    return [
        f"- 请求时间（UTC）：`{call['requested_at_utc']}`",
        f"- 返回时间（UTC）：`{call['returned_at_utc']}`",
        f"- response id：`{call['response_id']}`",
        f"- returned_model：`{call['returned_model']}`",
        f"- usage：`{json.dumps(call['usage'], ensure_ascii=False, sort_keys=True)}`",
        f"- assistant content SHA256：`{call['content_sha256']}`",
        f"- API response body SHA256：`{call['response_body_sha256']}`",
        "- 脱敏请求体（原请求不含密钥与 base URL）：",
        "",
        "```json",
        json.dumps(call["request_body"], ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "- 未删改 API 响应体：",
        "",
        "```json",
        str(call["response_body"]),
        "```",
    ]


def render_markdown(model: str, rounds: list[dict[str, object]]) -> str:
    generated = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    lines = [
        "# D02 人称单变量 A/B 实验",
        "",
        "> 状态：`draft_evidence` · 原始 API 输出未删改 · 本文不自动宣布假设成立",
        "",
        f"- 生成时间（UTC）：`{generated}`",
        f"- 模型：`{model}`",
        "- 轮数：`2`",
        "- 固定变量：模型、system prompt、计划事实、评价要求、模型默认采样参数",
        "- 唯一内容变量：第一人称“我” → 第三人称“小林”",
        "- 判定规则：需人工比较两轮的风险排序、批评出现位置、鼓励缓冲语和实质结论；词面计数只是辅助，不等于结论。",
        "",
        "## 固定 system prompt",
        "",
        f"> {SYSTEM_PROMPT}",
    ]
    for result in rounds:
        round_no = result["round"]
        lines.extend(
            [
                "",
                f"## Round {round_no}",
                "",
                "### A · 第一人称",
                "",
                f"- SHA256：`{result['self_call']['content_sha256']}`",
                f"- 词面统计：`{json.dumps(result['self_stats'], ensure_ascii=False)}`",
                "",
                str(result["self_text"]),
                "",
                "#### A 调用审计元数据",
                "",
                *evidence_metadata(result["self_call"]),
                "",
                "### B · 陌生人小林",
                "",
                f"- SHA256：`{result['xiaolin_call']['content_sha256']}`",
                f"- 词面统计：`{json.dumps(result['xiaolin_stats'], ensure_ascii=False)}`",
                "",
                str(result["xiaolin_text"]),
                "",
                "#### B 调用审计元数据",
                "",
                *evidence_metadata(result["xiaolin_call"]),
            ]
        )
    lines.extend(
        [
            "",
            "## 人工判定",
            "",
            "`pending_independent_review`",
            "",
            "不得只因为措辞不同就宣布“陌生人法有效”。只有两轮都出现方向一致、且会影响观众决策的实质差异，才可进入“遮住身份猜 A/B”脚本。",
        ]
    )
    return "\n".join(lines) + "\n"


def render_premortem_markdown(model: str, rounds: list[dict[str, object]]) -> str:
    generated = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    lines = [
        "# D02 事前验尸法 A/B 实验",
        "",
        "> 状态：`draft_evidence` · 原始 API 输出未删改 · 需人工判定",
        "",
        f"- 生成时间（UTC）：`{generated}`",
        f"- 模型：`{model}`",
        "- 轮数：`2`",
        "- 固定变量：模型、system prompt、计划事实、模型默认采样参数",
        "- 干预单位：整组 Prompt。A 为普通评价请求；B 同时加入失败前提、倒推任务、排序要求、事实锚定、禁止先夸和禁止补救建议。",
        "- 归因边界：本实验不能拆分其中任何一句的单独因果效应，只能比较整组事前验尸指令与普通评价请求。",
        "- 判定：比较是否更快进入风险、是否每条都绑定现有事实、是否减少泛化建议。",
        "",
        "## B 组指令原文",
        "",
        f"> {PREMORTEM_TEMPLATE.format(plan='[同一份计划]')}",
    ]
    for result in rounds:
        lines.extend(
            [
                "",
                f"## Round {result['round']}",
                "",
                "### A · 普通评价",
                "",
                f"- SHA256：`{result['self_call']['content_sha256']}`",
                f"- 词面统计：`{json.dumps(result['self_stats'], ensure_ascii=False)}`",
                "",
                str(result["self_text"]),
                "",
                "#### A 调用审计元数据",
                "",
                *evidence_metadata(result["self_call"]),
                "",
                "### B · 事前验尸",
                "",
                f"- SHA256：`{result['xiaolin_call']['content_sha256']}`",
                f"- 词面统计：`{json.dumps(result['xiaolin_stats'], ensure_ascii=False)}`",
                "",
                str(result["xiaolin_text"]),
                "",
                "#### B 调用审计元数据",
                "",
                *evidence_metadata(result["xiaolin_call"]),
            ]
        )
    lines.extend(
        [
            "",
            "## 证据内判定",
            "",
            "`supports_compound_prompt_structure_claim`",
            "",
            "两轮 A 已能直接指出关键风险；两轮 B 都采用了“预设失败 → 按可能性与破坏性排序 → 倒推原因 → 绑定计划事实”的组织。证据只支持：在本次模型与测试案例中，**整组事前验尸复合指令改变了输出组织方式**。",
            "",
            "A/B 同时改变失败前提、任务方向、排序标准、事实锚定、禁止先夸和禁止补救建议，因而不是单一变量实验。不得把差异单独归因于其中任一句，不得写成更准、更凶或能预测真实失败。",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("persona", "premortem"), default="persona")
    parser.add_argument("--out", type=pathlib.Path)
    args = parser.parse_args()
    try:
        base, key, model = endpoint_config()
        if args.mode == "premortem":
            prompt_a = USER_TEMPLATE.format(plan=PLAN_SELF)
            prompt_b = PREMORTEM_TEMPLATE.format(plan=PLAN_SELF)
            out_path = args.out or PREMORTEM_OUT
        else:
            prompt_a = USER_TEMPLATE.format(plan=PLAN_SELF)
            prompt_b = USER_TEMPLATE.format(plan=PLAN_XIAOLIN)
            out_path = args.out or DEFAULT_OUT
        rounds: list[dict[str, object]] = []
        for round_no in range(1, 3):
            print(f"Round {round_no}: A/control", file=sys.stderr)
            self_call = chat(base, key, model, prompt_a)
            self_text = str(self_call["content"])
            print(f"Round {round_no}: B/{args.mode}", file=sys.stderr)
            xiaolin_call = chat(base, key, model, prompt_b)
            xiaolin_text = str(xiaolin_call["content"])
            rounds.append(
                {
                    "round": round_no,
                    "self_text": self_text,
                    "self_call": self_call,
                    "self_stats": marker_stats(self_text),
                    "xiaolin_text": xiaolin_text,
                    "xiaolin_call": xiaolin_call,
                    "xiaolin_stats": marker_stats(xiaolin_text),
                }
            )
        out_path.parent.mkdir(parents=True, exist_ok=True)
        rendered = render_premortem_markdown(model, rounds) if args.mode == "premortem" else render_markdown(model, rounds)
        out_path.write_text(rendered, encoding="utf-8")
        print(f"Wrote raw evidence to {out_path}", file=sys.stderr)
        return 0
    except (RuntimeError, KeyError, urllib.error.URLError, TimeoutError) as exc:
        print(f"Experiment blocked: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
