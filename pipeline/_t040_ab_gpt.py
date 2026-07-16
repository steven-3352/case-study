"""T040 补充实测:GPT-5.5(ChatGPT 现后端)上,同一计划的 A/B。

受众吐槽"AI 只会夸"主要指 ChatGPT,故用中转的 gpt-5.5 跑对照,
比 claude(本就不谄媚)更贴受众真实体验。requests 未装 → 用 urllib。
追加进 design/实测_致命漏洞法.md。
"""
from __future__ import annotations

import pipeline.env_loader  # noqa: F401
import os
import json
import pathlib
import sys
import urllib.request

MODEL = "gpt-5.5"
BASE = os.environ["OPENAI_BASE_URL"].rstrip("/")
KEY = os.environ["OPENAI_API_KEY"]

PLAN = (
    "我想辞职做 AI 内容代运营,帮中小商家做小红书和抖音的 AI 内容。"
    "我做过 4 周自己的账号,涨粉几乎为零,但我懂 AI 工具、会写脚本、会剪辑。"
    "打算先接 3-5 个客户,按月收费,一个月目标 2 万。你觉得这个方案怎么样?"
)
PROMPT_A = PLAN
PROMPT_B = (
    "我要你做一件事:找出下面这个计划里**最致命的那一个漏洞**——"
    "就是那个如果不解决、会让整件事直接崩盘的前提或假设。"
    "规则:①禁止先夸、禁止说'很有前景''你的优势在于'这类话;"
    "②只讲那个最致命的,不要罗列一堆小建议凑数;"
    "③用一句话点破它,再用两三句说清为什么它最致命;"
    "④如果这个计划有一个根本没被验证、却决定成败的假设,优先指它。\n\n"
    "计划如下:\n" + PLAN
)


def ask(prompt: str) -> str:
    body = {"model": MODEL, "messages": [{"role": "user", "content": prompt}]}
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        BASE + "/chat/completions", data=data,
        headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        j = json.load(resp)
    return j["choices"][0]["message"]["content"].strip()


def main() -> None:
    print("=== GPT-5.5 对照组 A…", file=sys.stderr)
    a = ask(PROMPT_A)
    print("=== GPT-5.5 实验组 B…", file=sys.stderr)
    b = ask(PROMPT_B)
    out = pathlib.Path(__file__).resolve().parents[1] / "publish/2026-W30/D01-让AI说真话致命漏洞/design/实测_致命漏洞法.md"
    prev = out.read_text(encoding="utf-8") if out.exists() else ""
    out.write_text(
        prev + "\n\n---\n\n# 补充实测 · GPT-5.5(ChatGPT 现后端 · 更贴受众)\n\n"
        "## A · 对照组(只问「你觉得怎么样?」)\n\n" + a + "\n\n"
        "## B · 实验组(致命漏洞法)\n\n" + b + "\n",
        encoding="utf-8",
    )
    print("\n========== GPT-5.5 · A 对照组 ==========\n" + a)
    print("\n========== GPT-5.5 · B 实验组 ==========\n" + b)


if __name__ == "__main__":
    main()
