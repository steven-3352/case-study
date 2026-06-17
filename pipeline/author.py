#!/usr/bin/env python3
"""② 创意核心 · context.md → research.md → content.yaml（调 Claude API）.

两次调用，避免服务端工具与结构化输出混用：
  A 调研补充：web_search 服务端工具，结合「AI 创业」背景补数据/案例 → research.md
  B 结构化产出：messages.parse + Pydantic，注入 persona/约束 → content.yaml

凭证：仓库根目录 `.env` 中的 ANTHROPIC_API_KEY + ANTHROPIC_BASE_URL（中转），或 `ant auth login`。

用法:
  python3 pipeline/author.py --id P002
"""
from __future__ import annotations

import argparse
import pathlib
import sys
from typing import Literal

import pipeline.env_loader  # noqa: F401 — 加载 .env
import os

import yaml
from pydantic import BaseModel, Field

try:
    import anthropic
except ImportError:
    sys.exit("需要 anthropic：.venv/bin/pip install anthropic")

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODEL = "claude-opus-4-8"

# ── 去 AI 味 / 平台口味 / demo_only 约束（蒸馏自 docs/DECISIONS.md Q8/Q9 + templates）──
SYSTEM = """你是一名中文短视频内容操盘手，为一个「用 AI 给小老板做真实项目改造」的获客 IP 服务。
目标：把输入的开源/产品项目，改写成抖音/小红书/视频号都吃的 30–60s 竖屏口播视频选题，
吸引对 AI 创业感兴趣的人，最终转化为「找我做定制项目」的客户。

【先把项目想透 · 这是第一步，写在 topic 里】
- pain：谁（具体哪类人/老板/岗位）在什么场景下、被什么事反复折磨？要具体到能让人“说的就是我”。
- solves：这个项目到底替他干掉了哪件麻烦事？用结果说（省了什么时间/避免了什么错/接住了什么）。
- hook：前 3 秒用什么冲突/反常识/结果把人钉住？必须是钩子，不是介绍。
- 互动：这条想让评论区吵起来/对号入座的点是什么？做成“有立场的问题”，落在每个平台的 interaction 字段。

【硬约束 · 必须遵守】
1. 画面 demo_only：全屏演示（真实截图/后台/数据/终端/代码/对话），不出真人、不出数字人、不出任何人物画面。
2. 9:16 竖屏。每条 30–60s，按 duration_s；段落口播合计时长落在区间（中文约 4 字/秒）。
3. 去 AI 味：第一人称、口语、具体、克制、不喊口号；像活人随手分享。
4. 严禁营销腔与“术语黑话”。标题与前三秒禁用 persona.banned_words.title 列出的词。
5. 钩子前置：每条前 3 秒是冲突/反常识/结果，用大字字幕承载。
6. 标题不做标题党到失真；正文落到“帮哪类人省时间/减少错误/接住线索/提高转化”。

【素材策略 · 关键】
- 有 demo（HAS_DEMO=true）：能用真实界面就用 source=shot，列进 shots（ref 唯一、url 相对路径、caption 说明）。
- 无 demo 或非界面项目（HAS_DEMO=false）：不要编造 shot 的 URL。改用 source=evidence 自己“整理素材”，
  每个 evidence 段必须给出 evidence_kind + detail，让画面能被真实地画出来：
    · terminal：命令行演示。detail 写多行“命令 + 输出”，像真实跑了一遍。
    · code：关键代码片段。detail 写十几行内的核心代码。
    · chat：对话/需求/反馈。detail 每行一句，用“客户：/我：”开头区分。
    · metric：数据或前后对比。detail 写几条“指标 = 数值”或“改造前→改造后”。
    · note：随手记/复盘要点。detail 写 2-4 行。
  detail 要具体、可信、和项目真实功能一致，不许空泛。仿真不等于编造里程碑（见数据规范）。
- web：网络补充素材，最少用；同样写清 detail（要展示什么）。

【口播与字幕】
- vo 是要被 TTS 念的整句口播；sub 是叠画面的短字幕（≤14字，提炼 vo 的钩子词）。
- 三平台口播/文案要差异化，不复用同一套话术。

【三平台口味差异】
- douyin：标题≤30字冲突前置；节奏快；30–45s；标签窄。
- xhs：复盘体、可稍长、“踩坑→复盘”叙事；40–60s；正文偏长，结尾抛有立场的问题。
- channels：分享感、少标题党；45–60s；正文可加“分享给也在做类似小系统的朋友”。

输出严格符合给定 JSON schema。所有文本中文。CTA 用“有立场的问题”，禁止“私信我/扣1”这类。"""


# ── content.yaml schema ──
class Shot(BaseModel):
    ref: str = Field(description="唯一引用名，如 s1")
    url: str = Field(description="相对 demo 根的路径，如 / 或 /pricing")
    caption: str = Field(description="这个页面是什么")


class Segment(BaseModel):
    source: Literal["shot", "evidence", "web"]
    ref: str = Field(description="source=shot 时为 shots 的 ref；evidence/web 为素材名")
    evidence_kind: Literal["none", "terminal", "code", "chat", "metric", "note"] = Field(
        description="source=evidence/web 时选体裁让画面可渲染；source=shot 填 none"
    )
    detail: str = Field(description="evidence/web 的可渲染内容（多行）；shot 段留空字符串")
    vo: str = Field(description="该段完整口播（被 TTS 念）")
    sub: str = Field(description="叠画面的短字幕，≤14字")


class Cover(BaseModel):
    hook: str = Field(description="封面大字钩子，≤16字")
    shot_ref: str = Field(description="封面用哪张 shot；无 shot 时留空")


class Platform(BaseModel):
    title: str
    body: str = Field(description="发布正文")
    tags: list[str] = Field(description="3-6 个标签，不带#")
    duration_s: int = Field(description="目标时长秒，30-60")
    interaction: str = Field(description="这条想引发互动的点 / 评论区钩子（有立场的问题）")
    cover: Cover
    segments: list[Segment]


class Topic(BaseModel):
    id: str
    pain: str = Field(description="谁在什么场景被什么事反复折磨，具体到能对号入座")
    solves: str = Field(description="项目替他干掉了哪件麻烦事，用结果说")
    hook: str = Field(description="前3秒的冲突/反常识/结果钩子")
    angle: str = Field(description="切入角度，如 踩坑/效果/拆解")


class Content(BaseModel):
    topic: Topic
    shots: list[Shot]
    douyin: Platform
    xhs: Platform
    channels: Platform


def load_persona() -> str:
    return (ROOT / "persona" / "persona.yaml").read_text(encoding="utf-8")


def banned_titles() -> list[str]:
    p = yaml.safe_load((ROOT / "persona" / "persona.yaml").read_text(encoding="utf-8"))
    return (p.get("banned_words") or {}).get("title", []) or []


def research(client: "anthropic.Anthropic", context: str) -> str:
    """调用 A：web_search 补充「AI 创业」背景下的相关数据/案例。"""
    prompt = (
        "下面是一个项目的原料。请联网检索，补充与该项目相关、且在『AI 创业 / 用 AI 解决具体业务问题』"
        "语境下能增强说服力的：行业现状、同类做法、可引用的数据点或真实痛点。"
        "只输出一份精炼的中文要点清单（带来源），不要展开成文章。\n\n" + context
    )
    messages = [{"role": "user", "content": prompt}]
    tools = [{"type": "web_search_20260209", "name": "web_search"}]
    for _ in range(6):  # 处理 server-tool 的 pause_turn
        resp = client.messages.create(
            model=MODEL,
            max_tokens=8000,
            thinking={"type": "adaptive"},
            tools=tools,
            messages=messages,
        )
        if resp.stop_reason == "pause_turn":
            messages = [messages[0], {"role": "assistant", "content": resp.content}]
            continue
        break
    return "".join(b.text for b in resp.content if b.type == "text").strip()


def draft(client: "anthropic.Anthropic", context: str, research_notes: str, has_demo: bool) -> str:
    """调用 B1：自由发挥写出三平台完整方案（创意在此完成，不受 schema 束缚）。"""
    system = SYSTEM + "\n\n【persona 配置 · 以此为准】\n```yaml\n" + load_persona() + "\n```"
    if has_demo:
        material = (
            "- 本项目有可访问的 demo（HAS_DEMO=true）：优先 shots（每个 ref / 相对路径 url / 该页面是什么）；"
            "真实拿不到的画面才用 evidence。\n"
        )
    else:
        material = (
            "- 本项目无 demo 或非界面项目（HAS_DEMO=false）：不要编造 shot 的 URL，shots 留空。\n"
            "  画面全部用 source=evidence（必要时 web），每段写清 evidence_kind"
            "（terminal/code/chat/metric/note）和 detail（多行、具体、可被真实画出来）。\n"
        )
    user = (
        "项目原料：\n" + context
        + "\n\n联网调研要点（可选用）：\n" + (research_notes or "(无)")
        + "\n\n先把项目想透：这个项目解决了谁的什么痛点（具体到能对号入座）、替他干掉了哪件麻烦事、"
        "前3秒钩子是什么、每个平台想用什么有立场的问题引发评论区互动。\n\n"
        "然后产出 1 个核心选题 × 抖音/小红书/视频号三平台适配的完整内容方案，用清晰的中文 markdown 写出。必须包含：\n"
        "- 核心选题：pain（谁的什么痛点）/ solves（解决了什么，用结果说）/ hook（前3秒钩子）/ angle（切入角度）\n"
        + material
        + "- 三个平台各自的：标题、发布正文、3-6 个标签、目标时长秒、interaction（评论区互动钩子）、"
        "封面(大字钩子+用哪张shot/无shot留空)、"
        "分镜 segments（每段：source、ref、evidence_kind、detail、整句口播 vo、短字幕 sub）。\n"
        "口播要把每段都写满、写成能直接念的话；三平台文案要差异化。"
    )
    resp = client.messages.create(
        model=MODEL,
        max_tokens=16000,
        thinking={"type": "adaptive"},
        output_config={"effort": "high"},
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return "".join(b.text for b in resp.content if b.type == "text").strip()


def structure(client: "anthropic.Anthropic", plan_md: str) -> Content:
    """调用 B2：把已写好的方案转录进 JSON schema（纯格式化，不再创作）。"""
    sys_msg = (
        "你是格式转换器。把给定的中文内容方案原样转录进 JSON schema，"
        "不要省略、不要改写、不要留空：每个字段都要从方案里找到对应内容填满。\n"
        "【关键】方案里每个平台的『分镜 segments』通常是一个 markdown 表格，"
        "表格的每一行（# 1,2,3…）就是一个 segment 对象，必须逐行转录、一行都不能漏。"
        "把行内的 source / evidence_kind / detail / vo（口播）/ sub（字幕）分别填进对应字段；"
        "detail 里的 <br> 换成真实换行。\n"
        "三个平台 douyin/xhs/channels 都必须有非空 segments 和 title/body/tags。\n"
        "source 只能是 shot/evidence/web；source=shot 时 evidence_kind 填 none、detail 留空字符串；"
        "source=evidence/web 时 evidence_kind 选 terminal/code/chat/metric/note 之一并把 detail 填满。"
    )
    content = client.messages.parse(
        model=MODEL,
        max_tokens=16000,
        system=sys_msg,
        messages=[{"role": "user", "content": "内容方案：\n\n" + plan_md}],
        output_format=Content,
    ).parsed_output

    # 重试一次：若任一平台 segments 为空（多半是表格没转进来），强调逐行转录再试
    empty = [n for n in ("douyin", "xhs", "channels") if not getattr(content, n).segments]
    if empty:
        print(f"      ↻ {','.join(empty)} segments 为空，重试转录…")
        retry = client.messages.parse(
            model=MODEL,
            max_tokens=16000,
            system=sys_msg + "\n\n上一次转录把分镜表格漏成了空数组。这次务必把每个平台分镜表格的"
                             "每一行都转成一个 segment 对象，确保三个平台 segments 都非空。",
            messages=[{"role": "user", "content": "内容方案：\n\n" + plan_md}],
            output_format=Content,
        ).parsed_output
        # 用重试结果补齐仍为空的平台
        for n in empty:
            if getattr(retry, n).segments:
                setattr(content, n, getattr(retry, n))
    return content


def check_banned(content: Content) -> list[str]:
    bad = banned_titles()
    warns: list[str] = []
    for name in ("douyin", "xhs", "channels"):
        plat: Platform = getattr(content, name)
        for w in bad:
            if w in plat.title:
                warns.append(f"{name} 标题命中禁用词「{w}」: {plat.title}")
        total_vo = sum(len(s.vo) for s in plat.segments)
        est_s = total_vo / 4  # 约 4 字/秒
        if not (25 <= est_s <= 70):
            warns.append(f"{name} 口播估算 {est_s:.0f}s 偏离 30-60s 区间（共 {total_vo} 字）")
    return warns


def detect_has_demo(context: str) -> bool:
    """从 context.md 的 '- Demo:' 行判断是否有可访问 demo。"""
    for line in context.splitlines():
        s = line.strip()
        if s.startswith("- Demo:"):
            val = s.split(":", 1)[1].strip()
            return bool(val) and val not in ("(无)", "(未提供 demo URL)")
    return False


def main() -> None:
    ap = argparse.ArgumentParser(description="context.md → content.yaml")
    ap.add_argument("--id", required=True)
    ap.add_argument("--skip-research", action="store_true", help="跳过联网调研")
    ap.add_argument("--no-demo", action="store_true", help="强制无 demo 模式（自整理 evidence 素材）")
    args = ap.parse_args()

    out_dir = ROOT / "projects" / args.id
    ctx_path = out_dir / "context.md"
    if not ctx_path.exists():
        sys.exit(f"先跑 ingest：缺 {ctx_path}")
    context = ctx_path.read_text(encoding="utf-8")
    has_demo = (not args.no_demo) and detect_has_demo(context)
    print(f"  素材模式：{'有 demo → 真实截图优先' if has_demo else '无 demo → 自整理 evidence 素材'}")

    client = anthropic.Anthropic(
        **({"base_url": os.environ["ANTHROPIC_BASE_URL"].rstrip("/")} if os.getenv("ANTHROPIC_BASE_URL") else {})
    )

    research_notes = ""
    if not args.skip_research:
        print("  [A] 联网调研补充…")
        try:
            research_notes = research(client, context)
            (out_dir / "research.md").write_text(research_notes, encoding="utf-8")
            print(f"      ✓ research.md · {len(research_notes)} 字")
        except Exception as e:  # noqa: BLE001 — 调研失败不阻断主流程
            print(f"      ⚠ 调研失败，继续：{e}")

    print("  [B] 结构化产出 content.yaml…")
    plan_md = draft(client, context, research_notes, has_demo)
    (out_dir / "plan.md").write_text(plan_md, encoding="utf-8")
    print(f"      · 方案草稿 plan.md · {len(plan_md)} 字")
    content = structure(client, plan_md)
    out = out_dir / "content.yaml"
    out.write_text(
        yaml.safe_dump(content.model_dump(), allow_unicode=True, sort_keys=False, width=100),
        encoding="utf-8",
    )
    print(f"      ✓ {out}")

    for w in check_banned(content):
        print(f"  ⚠ {w}")


if __name__ == "__main__":
    main()
