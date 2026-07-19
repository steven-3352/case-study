"""Run and record the W30 D01 controlled fatal-flaw prompt experiment.

The two arms use the same model, plan, system message, and generation
parameters. Only the user instruction differs. Two rounds are recorded.
No credential or authorization header is written to the evidence file.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import sys
import urllib.parse
import urllib.error
import urllib.request

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
import pipeline.env_loader  # noqa: F401


MODEL = os.getenv("W30D01_MODEL") or os.getenv("LLM_MODEL") or "gpt-5.5"
BASE_URL = (os.getenv("LLM_BASE_URL") or os.environ["OPENAI_BASE_URL"]).rstrip("/")
API_KEY = os.getenv("LLM_API_KEY") or os.environ["OPENAI_API_KEY"]
OUTPUT = (
    REPO_ROOT
    / "publish/2026-W30/D01-让AI说真话致命漏洞/design/实测_致命漏洞法.md"
)

SYSTEM = (
    "你是计划评估助手。只依据用户提供的信息作答；区分事实、假设和建议；"
    "不要把推断写成已证实事实。"
)
PLAN = (
    "举例测试（虚构计划）：一个人准备辞职做 AI 内容代运营，帮中小商家做小红书和抖音内容。"
    "他做过 4 周自己的账号，涨粉几乎为零；会使用 AI 工具、写脚本和剪辑。"
    "计划先接 3 至 5 个客户，按月收费，目标月收入 2 万元。"
)
PROMPT_A = PLAN + "\n\n请评估这个计划，并给出你的建议。"
PROMPT_B = (
    PLAN
    + "\n\n请优先指出这个计划中最致命的一个漏洞：如果不解决，会让计划直接失败的前提或假设。"
    "不要先夸，不要罗列多个小问题。先用一句话指出它，再用两三句话解释原因。"
    "如果存在一个尚未验证、却决定成败的假设，优先指出它。"
)
PARAMS = {"max_tokens": 1400}


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def call(prompt: str) -> dict[str, object]:
    body = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": prompt},
        ],
        **PARAMS,
    }
    request_bytes = json.dumps(body, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    started = dt.datetime.now(dt.timezone.utc)
    base_path = urllib.parse.urlparse(BASE_URL).path.rstrip("/")
    endpoint_path = "/chat/completions" if base_path.endswith("/v1") else "/v1/chat/completions"
    request = urllib.request.Request(
        BASE_URL + endpoint_path,
        data=request_bytes,
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            raw = response.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:1000]
        raise RuntimeError(f"LLM HTTP {exc.code}: {detail}") from exc
    ended = dt.datetime.now(dt.timezone.utc)
    payload = json.loads(raw)
    content = payload["choices"][0]["message"]["content"]
    return {
        "started_at_utc": started.isoformat(),
        "ended_at_utc": ended.isoformat(),
        "requested_model": MODEL,
        "returned_model": payload.get("model"),
        "response_id": payload.get("id"),
        "finish_reason": payload["choices"][0].get("finish_reason"),
        "usage": payload.get("usage"),
        "request_body_sha256": sha256_text(request_bytes.decode("utf-8")),
        "response_text_sha256": sha256_text(content),
        "endpoint_path": endpoint_path,
        "content": content,
    }


def render_record(round_number: int, arm: str, prompt: str, result: dict[str, object]) -> str:
    metadata = {key: value for key, value in result.items() if key != "content"}
    return (
        f"## 第 {round_number} 轮 · {arm}\n\n"
        "### 脱敏请求配置\n\n"
        "```json\n"
        + json.dumps(
            {
                "endpoint_path": result["endpoint_path"],
                "model": MODEL,
                "system": SYSTEM,
                "user_prompt": prompt,
                **PARAMS,
                "credential_recorded": False,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n```\n\n### 返回元数据\n\n```json\n"
        + json.dumps(metadata, ensure_ascii=False, indent=2)
        + "\n```\n\n### 原始未删改响应\n\n"
        + str(result["content"])
        + "\n"
    )


def main() -> None:
    records: list[tuple[int, str, str, dict[str, object]]] = []
    for round_number in (1, 2):
        records.append((round_number, "A · 普通问法", PROMPT_A, call(PROMPT_A)))
        records.append((round_number, "B · 致命漏洞问法", PROMPT_B, call(PROMPT_B)))

    header = f"""# D01 受控 A/B 实测 · 致命漏洞问法

> 执行日期：{dt.date.today().isoformat()}
> 实验对象：举例测试的虚构计划，不是作者经历或客户案例
> 设计：双轮重复；每轮 A/B 使用同一模型、同一系统消息、同一计划与同一生成参数，仅用户问法不同
> 证据口径：本实验只能证明这些调用中模型输出的变化，不能证明 Prompt 找到客观真实的“致命漏洞”，也不能外推到所有模型或计划
> 隐私：未保存 API 密钥、Authorization header 或 API base URL

## 固定实验材料

**计划：** {PLAN}

**控制变量：** 模型 `{MODEL}`；system message；计划文本；`max_tokens=1400`；其余采样参数均省略并使用同一服务端默认值。

**唯一自变量：** A 要求“评估并建议”；B 要求优先只指出一个尚未验证、决定成败的前提或假设。

**判读规则：** 只描述输出中可观察到的优先级变化。可写“模型优先指出核心能力尚未验证”；不可写“模型发现了客观真漏洞”。

---
"""
    OUTPUT.write_text(
        header
        + "\n---\n".join(render_record(*record) for record in records)
        + "\n---\n\n## 实验结论边界\n\n"
        "本次双轮中，若 B 组都把“能否为客户做出可付费、可持续的结果尚未验证”置于首位，"
        "视频只据此表述为：**在这组受控调用中，致命漏洞问法让模型优先指出核心能力尚未验证。** "
        "A 组即使更长或列出更多建议，也不得改写成“AI 只会夸”或“AI 夸了三千字”。\n",
        encoding="utf-8",
    )
    print(f"wrote {OUTPUT}")


if __name__ == "__main__":
    main()
