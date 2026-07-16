"""T040 实测:「致命漏洞法」真的能逼 AI 挑出致命漏洞吗?

A/B 对比,同一个真实计划:
  对照组 — 只问"你觉得怎么样"(看 AI 是不是只会夸)
  实验组 — 加「致命漏洞法」指令(看 AI 是不是挑出会崩盘的主因)

用项目 .env 的 ANTHROPIC 中转,抄 pipeline/author.py 的调用方式。
输出存 design/实测_致命漏洞法.md 当洞察/脚本的真实证据。
一次性脚本,跑完即证据,不进产线。
"""
from __future__ import annotations

import pipeline.env_loader  # noqa: F401 — 加载 .env
import os
import pathlib
import sys

try:
    import anthropic
except ModuleNotFoundError:
    sys.exit("需要 anthropic：.venv/bin/pip install anthropic")

MODEL = "claude-opus-4-8"

# 受众高频的真实计划(skin 受众:辞职做副业的人)
PLAN = (
    "我想辞职做 AI 内容代运营,帮中小商家做小红书和抖音的 AI 内容。"
    "我做过 4 周自己的账号,涨粉几乎为零,但我懂 AI 工具、会写脚本、会剪辑。"
    "打算先接 3-5 个客户,按月收费,一个月目标 2 万。你觉得这个方案怎么样?"
)

# A · 对照组:普通人默认问法
PROMPT_A = PLAN

# B · 实验组:致命漏洞法(可抄指令 · 单点,不搞多角色)
PROMPT_B = (
    "我要你做一件事:找出下面这个计划里**最致命的那一个漏洞**——"
    "就是那个如果不解决、会让整件事直接崩盘的前提或假设。"
    "规则:①禁止先夸、禁止说'很有前景''你的优势在于'这类话;"
    "②只讲那个最致命的,不要罗列一堆小建议凑数;"
    "③用一句话点破它,再用两三句说清为什么它最致命;"
    "④如果这个计划有一个根本没被验证、却决定成败的假设,优先指它。\n\n"
    "计划如下:\n" + PLAN
)


def ask(client: "anthropic.Anthropic", prompt: str) -> str:
    resp = client.messages.create(
        model=MODEL,
        max_tokens=800,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(b.text for b in resp.content if getattr(b, "type", None) == "text").strip()


def main() -> None:
    client = anthropic.Anthropic(
        **({"base_url": os.environ["ANTHROPIC_BASE_URL"].rstrip("/")} if os.getenv("ANTHROPIC_BASE_URL") else {})
    )
    print("=== 跑对照组 A(只问怎么样)…", file=sys.stderr)
    a = ask(client, PROMPT_A)
    print("=== 跑实验组 B(致命漏洞法)…", file=sys.stderr)
    b = ask(client, PROMPT_B)

    out = pathlib.Path(__file__).resolve().parents[1] / "publish/2026-W30/D01-让AI说真话致命漏洞/design/实测_致命漏洞法.md"
    out.write_text(
        "# 实测 · 致命漏洞法 A/B（真实 API 输出 · claude-opus-4-8）\n\n"
        "> 同一个计划,两种问法,真实调用项目 .env ANTHROPIC 中转所得。未删改。\n\n"
        f"## 被测计划\n\n> {PLAN}\n\n"
        "---\n\n## A · 对照组(普通人默认问法:「你觉得这个方案怎么样?」)\n\n"
        f"{a}\n\n"
        "---\n\n## B · 实验组(致命漏洞法指令)\n\n"
        f"{b}\n",
        encoding="utf-8",
    )
    print(f"\n已写入 {out}", file=sys.stderr)
    print("\n\n========== A 对照组 ==========\n" + a)
    print("\n\n========== B 实验组 ==========\n" + b)


if __name__ == "__main__":
    main()
