"""W30 D03 two-round prompt-organization A/B with auditable API evidence."""
from __future__ import annotations

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
sys.path.insert(0, str(ROOT))
import pipeline.env_loader  # noqa: E402,F401

OUTPUT = ROOT / "publish/2026-W30/D03-迷茫十问/insights/questions_ab_evidence.md"
MODEL = os.getenv("W30D03_MODEL") or os.getenv("LLM_MODEL") or "gpt-5.5"
BASE_URL = (os.getenv("LLM_BASE_URL") or os.environ["OPENAI_BASE_URL"]).rstrip("/")
API_KEY = os.getenv("LLM_API_KEY") or os.environ["OPENAI_API_KEY"]
SYSTEM = "只依据用户提供的信息回答；不要虚构背景、经历、资源或目标。"
SCENARIO = (
    "我失业后有些迷茫，今天在 AI 中转、桌面应用和做找方向服务之间来回跳。"
    "我会写代码，也在做内容，但还没有真实付费用户。我该怎么办？"
)
CONTROL = SCENARIO
QUESTIONS = (
    SCENARIO
    + "\n\n先不要给建议。请按顺序逐个问我下面的问题，每次只问一个并等待回答；"
    "信息没有收齐前不要替我假设。\n"
    "自我画像：现在靠什么活着？钱还能撑多久？真正做过并会的是什么？过去放弃过什么，为什么？\n"
    "目标边界：现在最怕的一件事是什么？三个月后什么状态算没白过？\n"
    "逼问推进：我是买方还是卖方？第一个真实用户是谁？这周能做的最小验证是什么？\n"
    "事实收齐后，再给选择题和你的建议。最后问我：聊完以后，你能不能说出一个之前没有的具体下一步？"
)


def sha(value: bytes | str) -> str:
    raw = value.encode("utf-8") if isinstance(value, str) else value
    return hashlib.sha256(raw).hexdigest()


def call(prompt: str) -> dict[str, object]:
    payload = {
        "model": MODEL,
        "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}],
    }
    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    base_path = urllib.parse.urlparse(BASE_URL).path.rstrip("/")
    endpoint = BASE_URL + ("/chat/completions" if base_path.endswith("/v1") else "/v1/chat/completions")
    request = urllib.request.Request(
        endpoint,
        data=body,
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
    )
    started = dt.datetime.now(dt.timezone.utc).isoformat(timespec="microseconds")
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            raw = response.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:800]
        raise RuntimeError(f"LLM HTTP {exc.code}: {detail}") from exc
    returned = dt.datetime.now(dt.timezone.utc).isoformat(timespec="microseconds")
    data = json.loads(raw)
    content = data["choices"][0]["message"]["content"]
    return {
        "requested_at_utc": started,
        "returned_at_utc": returned,
        "response_id": data.get("id"),
        "returned_model": data.get("model"),
        "usage": data.get("usage"),
        "request_body_sha256": sha(body),
        "response_body_sha256": sha(raw),
        "content_sha256": sha(content),
        "content": content,
    }


def metrics(text: str) -> dict[str, object]:
    advice = ("建议", "可以", "应该", "先做", "选择")
    questions = ("？", "?")
    return {
        "chars": len(text),
        "question_marks": sum(text.count(mark) for mark in questions),
        "advice_marker_hits": {mark: text.count(mark) for mark in advice if mark in text},
        "first_80_chars": text[:80],
    }


def main() -> None:
    records: list[dict[str, object]] = []
    for round_no in (1, 2):
        for arm, prompt in (("A · 直接问怎么办", CONTROL), ("B · 九问流程+第十问验收", QUESTIONS)):
            print(f"Round {round_no}: {arm}", file=sys.stderr)
            result = call(prompt)
            records.append({"round": round_no, "arm": arm, "prompt": prompt, "result": result})

    lines = [
        "# D03 九问流程 A/B 实测",
        "",
        "> 状态：`draft_evidence` · 双轮原始 API 输出未删改 · 不证明效用提升",
        "",
        f"- 执行日期：`{dt.date.today().isoformat()}`",
        f"- 模型：`{MODEL}`",
        "- 固定变量：模型、system、迷茫情境、服务端默认生成参数",
        "- 干预单位：整组九问流程 + 逐个提问/等待/不假设/事实未齐不建议 + 第十问验收",
        "- 归因边界：只能比较本组调用的首答组织；不能拆分单句效果，不能声称更准、更有用或能帮人找到方向。",
        "",
    ]
    for record in records:
        result = record["result"]
        content = str(result["content"])
        metadata = {key: value for key, value in result.items() if key != "content"}
        lines.extend([
            f"## Round {record['round']} · {record['arm']}",
            "",
            f"- 输出统计：`{json.dumps(metrics(content), ensure_ascii=False)}`",
            f"- assistant SHA256：`{result['content_sha256']}`",
            "",
            "### 脱敏请求",
            "",
            "```json",
            json.dumps({"model": MODEL, "system": SYSTEM, "user": record["prompt"]}, ensure_ascii=False, indent=2),
            "```",
            "",
            "### 返回元数据",
            "",
            "```json",
            json.dumps(metadata, ensure_ascii=False, indent=2),
            "```",
            "",
            "### 原始响应",
            "",
            content,
            "",
        ])
    lines.extend([
        "## 人工结论",
        "",
        "`pending_independent_review`",
        "",
        "若两轮 B 都先问一个具体事实并等待，而 A 直接给方案，只允许写：本组调用中，复合流程把首答从直接建议改成先收集事实。没有真人多轮和行动结果，不得写成更有效。",
    ])
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {OUTPUT}")


if __name__ == "__main__":
    main()
