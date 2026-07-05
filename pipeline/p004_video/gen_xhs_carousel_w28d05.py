#!/usr/bin/env python3
"""W28D05 xhs 7 页轮播 PNG 生成 · Chrome headless.

form_strategy 判定 xhs 首选 7 页图文轮播（收藏权重 > 完播）· D05 video fallback
后补齐本生成器（verdict.yaml known_gap: xhs_carousel_generator_missing）。

页面（xhs/publish.md P1-P7 备份文案为准）：
  p1_cover.png       封面 · 睡姿场景暗示 + 3 推送 mock + 大字
  p2_group_anchor.png 群体锚 · 40h/周 → 8h/周 分屏大字
  p3_three_traps.png  反面三格 · 三个坑并列
  p4_3_layer_stack.png 三层顺序（本页最重 · 收藏动机）· 血红警示
  p5_60_20_20.png     60/20/20 表格 · 大数字 baked
  p6_project_001.png  Project-001 化名 4 步流程
  p7_boundary_cta.png 边界 + CTA 大字

色板（同 gen_ui_w28d05 · memory feedback_gen-ui-avoid-blue-purple-gradient）：
  禁 linear-gradient 蓝紫端 · 全单色底 #000/#0a0e14/#1a1611
  禁 Dracula #bd93f9/#ff79c6/#8be9fd · 强调红 #e53935

用法:
  python3 pipeline/p004_video/gen_xhs_carousel_w28d05.py
  # 跑完立即: for p in publish/.../build/xhs_carousel/*.png; do python3 pipeline/gate_check_palette.py "$p"; done
"""
from __future__ import annotations

import pathlib
import subprocess
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "publish" / "2026-W28" / "D05-AI帮我一周活干成一天" / "build" / "xhs_carousel"
OUT.mkdir(parents=True, exist_ok=True)

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
W, H = 1080, 1920

TOK = {
    "canvas_pure_dark": "#000000",
    "night_dark": "#0a0e14",
    "warm_dark": "#1a1611",
    "ink_light": "#f5f5f0",
    "muted": "#7a7a7a",
    "accent_red": "#e53935",
    "notion_dark": "#191919",
    "cursor_dark": "#181818",
    "n8n_dark": "#101330",
    "n8n_orange": "#ff6d5a",
    "cursor_teal": "#00d4aa",
    "check_green": "#4caf50",
}


def shot(html: str, name: str) -> pathlib.Path:
    out = OUT / name
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as f:
        f.write(html)
        path = f.name
    subprocess.run(
        [CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
         f"--screenshot={out}", f"--window-size={W},{H}", "--force-device-scale-factor=1",
         f"file://{path}"],
        capture_output=True, timeout=60, check=True,
    )
    print(f"OK {name}")
    return out


BASE_CSS = f"""
* {{ margin: 0; padding: 0; box-sizing: border-box; -webkit-font-smoothing: antialiased; }}
html, body {{ width: {W}px; height: {H}px; overflow: hidden;
  font-family: -apple-system, "PingFang SC", "SF Pro Text", sans-serif;
  background: {TOK['canvas_pure_dark']}; color: {TOK['ink_light']}; }}
.page-tag {{ position: absolute; top: 60px; right: 60px; font-size: 26px;
  opacity: 0.4; letter-spacing: 2px; font-weight: 600; }}
"""


def page(body: str, extra_css: str = "", tag: str = "") -> str:
    tag_html = f'<div class="page-tag">{tag}</div>' if tag else ""
    return (f'<!DOCTYPE html><html><head><meta charset="utf-8"><style>{BASE_CSS}{extra_css}'
            f'</style></head><body>{tag_html}{body}</body></html>')


# ═══ P1 · 封面 · 3 推送 mock + 大字 ═══
def gen_p1_cover() -> None:
    css = f"""
body {{ background: {TOK['night_dark']}; display: flex; flex-direction: column;
       justify-content: center; align-items: center; padding: 0 70px; }}
.time {{ font-family: "SF Mono", monospace; font-size: 60px; font-weight: 700;
        opacity: 0.5; margin-bottom: 60px; }}
.push {{ width: 100%; background: rgba(255,255,255,0.08); border-radius: 24px;
        padding: 30px 36px; margin: 14px 0; border: 1px solid rgba(245,245,240,0.1); }}
.push-app {{ font-size: 24px; opacity: 0.6; margin-bottom: 8px; letter-spacing: 1px; }}
.push-text {{ font-size: 30px; font-weight: 600; opacity: 0.9; }}
.headline {{ margin-top: 90px; text-align: center; }}
.headline .l {{ font-size: 86px; font-weight: 900; line-height: 1.35;
               text-shadow: 0 0 20px rgba(200,180,150,0.2); }}
.headline .em {{ color: {TOK['accent_red']}; }}
"""
    body = f"""
<div class="time">08:00</div>
<div class="push"><div class="push-app">n8n · workflow_daily</div>
  <div class="push-text">昨晚 12 单询盘 · 已分类 · 草稿已生成</div></div>
<div class="push"><div class="push-app">Notion · Project-001</div>
  <div class="push-text">3 份方案初稿待你决策</div></div>
<div class="push"><div class="push-app">邮件 · 自动归档</div>
  <div class="push-text">9 封已回 · 0 封需要你</div></div>
<div class="headline">
  <div class="l">我睡着的时候</div>
  <div class="l"><span class="em">系统跑完了</span>昨晚的活</div>
</div>
"""
    shot(page(body, css, "1/7"), "p1_cover.png")


# ═══ P2 · 群体锚 · 40h → 8h 分屏 ═══
def gen_p2_group_anchor() -> None:
    css = f"""
.split {{ display: flex; height: 100%; position: relative; }}
.side {{ flex: 1; display: flex; flex-direction: column; align-items: center;
        justify-content: center; padding: 60px 30px; }}
.left {{ background: {TOK['night_dark']}; }}
.right {{ background: {TOK['warm_dark']}; }}
.big {{ font-family: "SF Mono", monospace; font-size: 130px; font-weight: 900; }}
.big-l {{ opacity: 0.85; }}
.big-r {{ color: {TOK['accent_red']}; }}
.unit {{ font-size: 40px; font-weight: 700; opacity: 0.7; margin-top: 16px; }}
.desc {{ font-size: 30px; opacity: 0.55; margin-top: 40px; text-align: center; line-height: 1.6; }}
.arrow {{ position: absolute; left: 50%; top: 50%; transform: translate(-50%,-50%);
         font-size: 90px; color: {TOK['ink_light']}; opacity: 0.9; z-index: 2;
         background: {TOK['canvas_pure_dark']}; border-radius: 50%; width: 150px; height: 150px;
         display: flex; align-items: center; justify-content: center;
         border: 3px solid rgba(245,245,240,0.25); }}
.foot {{ position: absolute; bottom: 90px; left: 0; right: 0; text-align: center;
        font-size: 30px; opacity: 0.5; }}
"""
    body = f"""
<div class="split">
  <div class="side left">
    <div class="big big-l">40h</div><div class="unit">/ 周</div>
    <div class="desc">凌晨 1 点改方案<br/>早上继续跟单</div>
  </div>
  <div class="side right">
    <div class="big big-r">8h</div><div class="unit">/ 周</div>
    <div class="desc">07:00 醒来<br/>只做决策</div>
  </div>
  <div class="arrow">→</div>
</div>
<div class="foot">我的项目实测 · 参考不套用</div>
"""
    shot(page(body, css, "2/7"), "p2_group_anchor.png")


# ═══ P3 · 反面三格 ═══
def gen_p3_three_traps() -> None:
    traps = [
        ("①", "装 5 个 AI 切来切去", "40 min 没了 · 活一件没干"),
        ("②", "3 个月搭完美 workflow", "每步都要 review · 更累了"),
        ("③", "只自动化 10 分钟的打字", "6 小时客户沟通一个字没碰"),
    ]
    cards = ""
    for num, title, sub in traps:
        cards += f"""
<div class="card">
  <div class="num">{num}</div>
  <div class="card-body"><div class="t">{title}</div><div class="s">{sub}</div></div>
  <div class="x">✕</div>
</div>"""
    css = f"""
body {{ display: flex; flex-direction: column; justify-content: center; padding: 0 70px; }}
.head {{ font-size: 64px; font-weight: 900; margin-bottom: 80px; line-height: 1.4; }}
.head .em {{ color: {TOK['accent_red']}; }}
.card {{ display: flex; align-items: center; gap: 36px; background: rgba(255,255,255,0.05);
        border: 1.5px solid rgba(229,57,53,0.35); border-radius: 24px;
        padding: 50px 44px; margin: 22px 0; }}
.num {{ font-size: 56px; font-weight: 900; color: {TOK['accent_red']}; }}
.t {{ font-size: 40px; font-weight: 700; }}
.s {{ font-size: 28px; opacity: 0.6; margin-top: 12px; }}
.x {{ margin-left: auto; font-size: 52px; color: {TOK['accent_red']}; opacity: 0.8; }}
.card-body {{ flex: 1; }}
"""
    body = f"""
<div class="head">一人公司装 AI<br/>大多数走进 <span class="em">3 个坑</span></div>
{cards}
"""
    shot(page(body, css, "3/7"), "p3_three_traps.png")


# ═══ P4 · 三层顺序（本页最重 · 收藏动机）═══
def gen_p4_3_layer_stack() -> None:
    css = f"""
body {{ padding: 0 60px; display: flex; flex-direction: column; gap: 40px;
       justify-content: center; }}
.head {{ font-size: 60px; font-weight: 900; margin-bottom: 20px; }}
.head .em {{ color: {TOK['accent_red']}; }}
.layer {{ border-radius: 20px; padding: 56px 50px; position: relative;
         box-shadow: 0 8px 32px rgba(0,0,0,0.5); overflow: hidden; }}
.order {{ position: absolute; top: 24px; right: 32px; font-size: 110px; font-weight: 900;
         opacity: 0.08; line-height: 1; }}
.lt {{ font-size: 44px; font-weight: 800; margin-bottom: 20px; }}
.ld {{ font-size: 32px; opacity: 0.7; line-height: 1.7; }}
.notion {{ background: {TOK['notion_dark']}; border: 1px solid #2a2a2a; }}
.cursor {{ background: {TOK['cursor_dark']}; border: 1px solid #262626; }}
.n8n {{ background: {TOK['n8n_dark']}; border: 1px solid #1a1e40; }}
.teal {{ color: {TOK['cursor_teal']}; }}
.orange {{ color: {TOK['n8n_orange']}; }}
.warn {{ background: rgba(229,57,53,0.14); border: 2px solid {TOK['accent_red']};
        border-radius: 16px; padding: 40px; text-align: center;
        font-size: 40px; font-weight: 800; color: {TOK['accent_red']}; }}
"""
    body = f"""
<div class="head">解法<span class="em">顺序不能反</span> · 三层往上垒</div>
<div class="layer notion"><div class="order">1</div>
  <div class="lt">◧ 第 1 层 · 手工 SOP · Notion</div>
  <div class="ld">先自己做 20 单磨出来 · 每步写成checkbox<br/>没有 SOP 的自动化 = 空中楼阁</div>
</div>
<div class="layer cursor"><div class="order">2</div>
  <div class="lt"><span class="teal">▲</span> 第 2 层 · AI 辅助 · Cursor + Claude</div>
  <div class="ld">按 SOP 出草稿 · prompt 模板存 Cursor rules<br/>AI 干重复 · 你只改关键 20%</div>
</div>
<div class="layer n8n"><div class="order">3</div>
  <div class="lt"><span class="orange">⬢</span> 第 3 层 · 系统自跑 · n8n</div>
  <div class="ld">SOP 串成 workflow · 系统自己跑<br/>SOP 变了只改 1 处 · 不散架</div>
</div>
<div class="warn">跳过 SOP 直接搭自动化 = 需求一改整套散架</div>
"""
    shot(page(body, css, "4/7"), "p4_3_layer_stack.png")


# ═══ P5 · 60/20/20 表格 · 大数字 baked ═══
def gen_p5_60_20_20() -> None:
    cols = [
        ("60%", "塞 AI", ["分类", "草稿", "翻译", "答客户", "搜索"], True),
        ("20%", "自动化", ["webhook", "分类", "推送", "归档"], False),
        ("20%", "你决策", ["审美", "关系", "战略"], False),
    ]
    col_html = ""
    for pct, label, items, hi in cols:
        items_html = "".join(f'<div class="item">{i}</div>' for i in items)
        col_html += f"""
<div class="col{' hi' if hi else ''}">
  <div class="pct{' pct-hi' if hi else ''}">{pct}</div>
  <div class="col-label">{label}</div>
  {items_html}
</div>"""
    css = f"""
body {{ padding: 0 50px; display: flex; flex-direction: column; justify-content: center; }}
.head {{ text-align: center; font-size: 64px; font-weight: 900; margin-bottom: 110px;
        line-height: 1.4; }}
.grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 26px; }}
.col {{ background: rgba(255,255,255,0.04); border-radius: 24px; padding: 60px 24px;
       border: 1.5px solid rgba(245,245,240,0.1); text-align: center; }}
.col.hi {{ background: rgba(229,57,53,0.12); border-color: rgba(229,57,53,0.4); }}
.pct {{ font-family: "SF Mono", monospace; font-size: 100px; font-weight: 900;
       margin-bottom: 24px; }}
.pct-hi {{ color: {TOK['accent_red']}; }}
.col-label {{ font-size: 40px; font-weight: 700; opacity: 0.85; margin-bottom: 32px; }}
.item {{ font-size: 30px; opacity: 0.7; margin: 18px 0; }}
.foot {{ text-align: center; font-size: 34px; opacity: 0.55; margin-top: 110px;
        letter-spacing: 2px; }}
"""
    body = f"""
<div class="head">每天 100% 时间<br/>我这么分配</div>
<div class="grid">{col_html}</div>
<div class="foot">Project-001 实测 · 参考不套用</div>
"""
    shot(page(body, css, "5/7"), "p5_60_20_20.png")


# ═══ P6 · Project-001 化名 4 步流程 ═══
def gen_p6_project_001() -> None:
    steps = [
        ("询盘进", "webhook 接住 · 自动打标签"),
        ("分类", "Claude 按客户类型/预算分流"),
        ("方案", "SOP 模板 → AI 草稿 · 历史案例参考"),
        ("决策", "报价/交付周期 · 只有这步是我"),
    ]
    step_html = ""
    for i, (t, s) in enumerate(steps, 1):
        last = ' step-last' if i == len(steps) else ''
        step_html += f"""
<div class="step{last}">
  <div class="step-num">{i}</div>
  <div class="step-body"><div class="st">{t}</div><div class="ss">{s}</div></div>
</div>"""
    css = f"""
body {{ display: flex; flex-direction: column; justify-content: center; padding: 0 80px; }}
.head {{ font-size: 56px; font-weight: 900; margin-bottom: 24px; }}
.sub {{ font-size: 28px; opacity: 0.55; margin-bottom: 70px; }}
.step {{ display: flex; align-items: flex-start; gap: 40px; padding: 40px 0;
        position: relative; }}
.step:not(.step-last)::after {{ content: ""; position: absolute; left: 44px; top: 130px;
        width: 3px; height: 60px; background: rgba(245,245,240,0.2); }}
.step-num {{ width: 90px; height: 90px; border-radius: 50%; flex-shrink: 0;
        background: rgba(255,255,255,0.06); border: 2px solid rgba(245,245,240,0.3);
        display: flex; align-items: center; justify-content: center;
        font-size: 44px; font-weight: 900; }}
.step-last .step-num {{ border-color: {TOK['accent_red']}; color: {TOK['accent_red']}; }}
.st {{ font-size: 42px; font-weight: 800; }}
.ss {{ font-size: 28px; opacity: 0.6; margin-top: 10px; line-height: 1.6; }}
.foot {{ margin-top: 70px; font-size: 30px; opacity: 0.7; line-height: 1.8;
        border-left: 4px solid {TOK['accent_red']}; padding-left: 30px; }}
"""
    body = f"""
<div class="head">Project-001 长这样</div>
<div class="sub">化名 · 一人外贸咨询 · 真实结构</div>
{step_html}
<div class="foot">第 1 层手工 20 单磨 SOP<br/>第 2 层 Claude 出草稿<br/>第 3 层 n8n 串 workflow · 我只出现在第 4 步</div>
"""
    shot(page(body, css, "6/7"), "p6_project_001.png")


# ═══ P7 · 边界 + CTA ═══
def gen_p7_boundary_cta() -> None:
    css = f"""
body {{ display: flex; flex-direction: column; justify-content: center; align-items: center;
       padding: 0 80px; text-align: center; }}
.no {{ font-size: 44px; font-weight: 700; opacity: 0.55; text-decoration: line-through;
      margin-bottom: 40px; }}
.yes {{ font-size: 80px; font-weight: 900; line-height: 1.4;
       text-shadow: 0 0 20px rgba(200,180,150,0.2); }}
.yes .em {{ color: {TOK['accent_red']}; }}
.cta {{ margin-top: 130px; background: rgba(229,57,53,0.12);
       border: 2px solid {TOK['accent_red']}; border-radius: 24px; padding: 50px 60px; }}
.cta-t {{ font-size: 44px; font-weight: 800; }}
.cta-t .kw {{ color: {TOK['accent_red']}; }}
.cta-s {{ font-size: 30px; opacity: 0.7; margin-top: 20px; }}
"""
    body = f"""
<div class="no">教你搞钱 · AI 变现秘籍 · 印钞机</div>
<div class="yes">AI 帮我<span class="em">解放</span><br/>不是印钞机</div>
<div class="cta">
  <div class="cta-t">评论「<span class="kw">项目+卡点</span>」</div>
  <div class="cta-s">我给你可自动化的第 1 步</div>
</div>
"""
    shot(page(body, css, "7/7"), "p7_boundary_cta.png")


def main() -> None:
    print(f"→ W28D05 xhs 7 页轮播生成 · out={OUT}")
    gen_p1_cover()
    gen_p2_group_anchor()
    gen_p3_three_traps()
    gen_p4_3_layer_stack()
    gen_p5_60_20_20()
    gen_p6_project_001()
    gen_p7_boundary_cta()
    print(f"✓ 7 页全生成 · {OUT}")
    print("下一步 · palette gate 逐张:")
    print(f"  for p in {OUT}/*.png; do python3 pipeline/gate_check_palette.py \"$p\"; done")


if __name__ == "__main__":
    main()
