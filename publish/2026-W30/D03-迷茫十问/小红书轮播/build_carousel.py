#!/usr/bin/env python3
"""T042 小红书图文轮播 · 8 页真实出图.

内容来源:Hermes 原矿参谋 system prompt 真实三步九问(raw-export/raw/2026-07-15-bot.md)+
design/retention_beat_sheet.md「小红书图文轮播(另拆·8页)」表。
色板/结构复用 T040(`D01-让AI说真话致命漏洞/小红书轮播/build_carousel.py`)同款 design_language.md v2
浅色 token(暖白底,禁AI味暗色)+ vgroup 排版平衡方案。
画布:1080x1920(pipeline/screen_dims.py 锁定 9:16)。

红线(见 CLAUDE.md 任务说明):
- P7 诚实收尾不可包装成"AI给完美方案"的爽感——用留白 checkbox + 平静字色,不加打勾/金色高亮
- 不虚构第三方案例/身份,不画"多角色顾问团"
- P4 自我画像 4 问必须完整呈现(含口播未念的第 4 问"过去放弃过什么,为什么"),这是原矿真实内容
  的完整呈现,不是新增卖点

用法: .venv/bin/python publish/2026-W30/D03-迷茫十问/小红书轮播/build_carousel.py
"""
from __future__ import annotations

import pathlib
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent
W, H = 1080, 1920

# ── design_language.md v2 token(与 T040 同源)──
CANVAS = "#faf9f6"
SURFACE = "#eeece5"
INK = "#1c1e22"
MUTED = "#767b85"
ACCENT = "#c0392b"
SECONDARY = "#9c6b0a"

BASE_CSS = f"""
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{
  width:{W}px; height:{H}px; background:{CANVAS}; color:{INK};
  font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Helvetica Neue",sans-serif;
  overflow:hidden; position:relative;
}}
.mono {{ font-family:"SF Mono","JetBrains Mono",Menlo,monospace; }}
.card {{ background:{SURFACE}; border-radius:16px; border:1px solid rgba(28,30,34,0.10);
  box-shadow:0 4px 20px rgba(28,30,34,0.08); }}
.accent-box {{ border:2px solid {ACCENT}; border-radius:12px; }}
.page-num {{ position:absolute; bottom:56px; right:64px; font-size:24px; color:{MUTED}; }}
.tag {{ display:inline-block; padding:8px 20px; border-radius:999px; font-size:24px; font-weight:600; }}
.vgroup {{ min-height:{H}px; display:flex; flex-direction:column; justify-content:center; }}
"""

PAGES = []

# ── P1 封面 ──
PAGES.append(("P1_封面", f"""
<style>{BASE_CSS}
.p1-wrap {{ padding:0 72px; }}
.p1-eyebrow {{ font-size:28px; color:{MUTED}; margin-bottom:24px; letter-spacing:1px; }}
.p1-title {{ font-size:74px; font-weight:800; line-height:1.3; color:{INK}; }}
.p1-strike {{ color:{MUTED}; text-decoration:line-through; text-decoration-color:{ACCENT};
  text-decoration-thickness:6px; }}
.p1-sub {{ margin-top:40px; font-size:56px; font-weight:800; color:{ACCENT}; line-height:1.4; }}
.p1-tags {{ margin-top:64px; display:flex; gap:16px; padding:0 72px; }}
.p1-tag {{ background:{SURFACE}; color:{INK}; }}
.p1-tag-accent {{ background:{CANVAS}; color:{ACCENT}; border:2px solid {ACCENT}; }}
</style>
<div class="vgroup">
<div class="p1-wrap">
  <div class="p1-eyebrow">迷茫的时候,别再这样问 AI</div>
  <div class="p1-title">千万别问 AI<br>「<span class="p1-strike">我该怎么办</span>」</div>
  <div class="p1-sub">迷茫时,问这 9 个问题</div>
</div>
<div class="p1-tags">
  <div class="tag p1-tag">真实方法论原矿</div>
  <div class="tag p1-tag-accent">可截图收藏</div>
</div>
</div>
<div class="page-num">1/8</div>
"""))

# ── P2 痛点 ──
PAGES.append(("P2_痛点", f"""
<style>{BASE_CSS}
.p2-wrap {{ padding:0 72px; }}
.p2-line {{ font-size:54px; font-weight:700; line-height:1.55; color:{INK}; }}
.p2-line .hl {{ color:{ACCENT}; }}
.p2-card {{ margin:96px 72px 0; padding:48px; }}
.p2-card-title {{ font-size:28px; color:{MUTED}; margin-bottom:20px; }}
.p2-card-body {{ font-size:34px; line-height:1.65; color:{INK}; }}
</style>
<div class="vgroup">
<div class="p2-wrap">
  <div class="p2-line">问 AI「我该怎么办」<br>只会顺着你的焦虑<br>瞎给方案,<span class="hl">越答越飘</span></div>
</div>
<div class="p2-card card">
  <div class="p2-card-title">上个月真实经历</div>
  <div class="p2-card-body">我也这么问过——AI 顺着焦虑一路夸,方案越读越飘,却没一句戳中要害。</div>
</div>
</div>
<div class="page-num">2/8</div>
"""))

# ── P3 方法转场 ──
PAGES.append(("P3_方法转场", f"""
<style>{BASE_CSS}
.p3-wrap {{ padding:0 72px; }}
.p3-eyebrow {{ font-size:28px; color:{MUTED}; margin-bottom:24px; }}
.p3-title {{ font-size:68px; font-weight:800; line-height:1.35; color:{INK}; }}
.p3-title .hl {{ color:{ACCENT}; }}
.p3-flow {{ margin-top:88px; padding:0 56px; display:flex; flex-direction:column; gap:24px; }}
.p3-step {{ display:flex; align-items:center; gap:24px; padding:32px 36px; }}
.p3-step-num {{ font-size:40px; font-weight:800; color:{ACCENT}; width:56px; flex-shrink:0; }}
.p3-step-label {{ font-size:34px; font-weight:700; color:{INK}; }}
.p3-caption {{ margin-top:40px; text-align:center; font-size:26px; color:{MUTED}; }}
</style>
<div class="vgroup">
<div class="p3-wrap">
  <div class="p3-eyebrow">后来发现,有用的问法是反过来</div>
  <div class="p3-title">反过来:<br><span class="hl">让 AI 逼问我</span></div>
</div>
<div class="p3-flow">
  <div class="p3-step card"><div class="p3-step-num">①</div><div class="p3-step-label">自我画像</div></div>
  <div class="p3-step card"><div class="p3-step-num">②</div><div class="p3-step-label">定目标</div></div>
  <div class="p3-step card"><div class="p3-step-num">③</div><div class="p3-step-label">逼问推进</div></div>
</div>
<div class="p3-caption">往下翻,三步共 9 问 →</div>
</div>
<div class="page-num">3/8</div>
"""))

# ── P4 ①自我画像 4问(收藏物1) ──
PAGES.append(("P4_自我画像", f"""
<style>{BASE_CSS}
.p4-wrap {{ padding:0 64px; }}
.p4-eyebrow {{ font-size:26px; color:{MUTED}; margin-bottom:12px; }}
.p4-title {{ font-size:52px; font-weight:800; color:{INK}; margin-bottom:56px; }}
.p4-title .num {{ color:{ACCENT}; }}
.p4-item {{ display:flex; gap:24px; margin-bottom:40px; align-items:flex-start; }}
.p4-num {{ font-size:38px; font-weight:800; color:{ACCENT}; width:56px; flex-shrink:0; }}
.p4-text {{ font-size:38px; line-height:1.5; font-weight:700; color:{INK}; }}
.p4-text .note {{ display:block; font-size:24px; color:{MUTED}; font-weight:400; margin-top:6px; }}
</style>
<div class="vgroup">
<div class="p4-wrap">
  <div class="p4-eyebrow">STEP 1 · 可截图</div>
  <div class="p4-title"><span class="num">①</span> 自我画像</div>
  <div class="p4-item"><div class="p4-num">1</div><div class="p4-text">现在靠什么活着?</div></div>
  <div class="p4-item"><div class="p4-num">2</div><div class="p4-text">钱还能撑几个月?</div></div>
  <div class="p4-item"><div class="p4-num">3</div><div class="p4-text">真正会的、做过的是什么?
    <span class="note">不是"以为会"</span></div></div>
  <div class="p4-item"><div class="p4-num">4</div><div class="p4-text">过去放弃过什么,为什么?</div></div>
</div>
</div>
<div class="page-num">4/8</div>
"""))

# ── P5 ②定目标 2问(收藏物2) ──
PAGES.append(("P5_定目标", f"""
<style>{BASE_CSS}
.p5-wrap {{ padding:0 64px; }}
.p5-eyebrow {{ font-size:26px; color:{MUTED}; margin-bottom:12px; }}
.p5-title {{ font-size:52px; font-weight:800; color:{INK}; margin-bottom:80px; }}
.p5-title .num {{ color:{ACCENT}; }}
.p5-item {{ margin-bottom:88px; }}
.p5-num {{ font-size:38px; font-weight:800; color:{ACCENT}; margin-bottom:16px; }}
.p5-text {{ font-size:46px; line-height:1.5; font-weight:700; color:{INK}; }}
</style>
<div class="vgroup">
<div class="p5-wrap">
  <div class="p5-eyebrow">STEP 2 · 可截图</div>
  <div class="p5-title"><span class="num">②</span> 定目标</div>
  <div class="p5-item"><div class="p5-num">1</div><div class="p5-text">你现在最怕的一件事是什么?</div></div>
  <div class="p5-item"><div class="p5-num">2</div><div class="p5-text">三个月后,什么状态算没白过?</div></div>
</div>
</div>
<div class="page-num">5/8</div>
"""))

# ── P6 ③逼问推进 3问(收藏物3) ──
PAGES.append(("P6_逼问推进", f"""
<style>{BASE_CSS}
.p6-wrap {{ padding:0 64px; }}
.p6-eyebrow {{ font-size:26px; color:{MUTED}; margin-bottom:12px; }}
.p6-title {{ font-size:52px; font-weight:800; color:{INK}; margin-bottom:56px; }}
.p6-title .num {{ color:{ACCENT}; }}
.p6-item {{ display:flex; gap:24px; margin-bottom:44px; align-items:flex-start; }}
.p6-num {{ font-size:38px; font-weight:800; color:{ACCENT}; width:56px; flex-shrink:0; }}
.p6-text {{ font-size:38px; line-height:1.5; font-weight:700; color:{INK}; }}
.p6-text .note {{ display:block; font-size:24px; color:{MUTED}; font-weight:400; margin-top:6px; }}
</style>
<div class="vgroup">
<div class="p6-wrap">
  <div class="p6-eyebrow">STEP 3 · 可截图</div>
  <div class="p6-title"><span class="num">③</span> 逼问推进</div>
  <div class="p6-item"><div class="p6-num">1</div><div class="p6-text">你是买方还是卖方?
    <span class="note">想要这个 ≠ 能做这个</span></div></div>
  <div class="p6-item"><div class="p6-num">2</div><div class="p6-text">谁是第一个真实用户?
    <span class="note">脑补的不算</span></div></div>
  <div class="p6-item"><div class="p6-num">3</div><div class="p6-text">这周能做的最小验证是什么?</div></div>
</div>
</div>
<div class="page-num">6/8</div>
"""))

# ── P7 诚实收尾(红线:不可包装成爽感) ──
PAGES.append(("P7_诚实收尾", f"""
<style>{BASE_CSS}
.p7-wrap {{ padding:0 72px; text-align:center; }}
.p7-checks {{ display:flex; justify-content:center; gap:28px; margin-bottom:80px; }}
.p7-check {{ width:120px; height:120px; border:2px solid rgba(28,30,34,0.22); border-radius:12px;
  display:flex; align-items:center; justify-content:center; font-size:32px; color:{MUTED}; font-weight:700; }}
.p7-line1 {{ font-size:44px; line-height:1.6; color:{INK}; margin-bottom:56px; }}
.p7-line2 {{ font-size:60px; font-weight:800; line-height:1.5; color:{INK}; }}
.p7-line2 .hl {{ color:{ACCENT}; text-decoration:underline; text-decoration-thickness:4px;
  text-underline-offset:8px; }}
</style>
<div class="vgroup">
<div class="p7-wrap">
  <div class="p7-checks">
    <div class="p7-check">①</div>
    <div class="p7-check">②</div>
    <div class="p7-check">③</div>
  </div>
  <div class="p7-line1">三个问题问完了,<br>没拿到答案。</div>
  <div class="p7-line2">但知道自己在怕什么了,<br>拍板还是<span class="hl">我自己</span>。</div>
</div>
</div>
<div class="page-num">7/8</div>
"""))

# ── P8 CTA:9问合集 + 评论区 ──
PAGES.append(("P8_CTA", f"""
<style>{BASE_CSS}
.p8-wrap {{ padding:88px 56px 0; }}
.p8-title {{ font-size:40px; font-weight:800; color:{INK}; margin-bottom:8px; }}
.p8-sub {{ font-size:24px; color:{MUTED}; margin-bottom:40px; }}
.p8-group {{ padding:28px 32px; margin-bottom:20px; }}
.p8-group-title {{ font-size:26px; font-weight:700; color:{ACCENT}; margin-bottom:14px; }}
.p8-q {{ font-size:26px; line-height:1.7; color:{INK}; }}
.p8-cta {{ margin-top:44px; text-align:center; }}
.p8-cta-q {{ font-size:38px; font-weight:800; color:{INK}; margin-bottom:24px; }}
.p8-cta-btn {{ display:inline-block; font-size:28px; color:{ACCENT}; font-weight:700;
  padding:20px 44px; border:2px solid {ACCENT}; border-radius:999px; }}
</style>
<div class="p8-wrap">
  <div class="p8-title">迷茫时问这 9 个问题</div>
  <div class="p8-sub">↓ 截图保存,下次迷茫直接甩给 AI</div>
  <div class="p8-group card">
    <div class="p8-group-title">① 自我画像</div>
    <div class="p8-q">现在靠什么活着? / 钱还能撑几个月? / 真正会的、做过的是什么? / 过去放弃过什么,为什么?</div>
  </div>
  <div class="p8-group card">
    <div class="p8-group-title">② 定目标</div>
    <div class="p8-q">你现在最怕的一件事是什么? / 三个月后,什么状态算没白过?</div>
  </div>
  <div class="p8-group card">
    <div class="p8-group-title">③ 逼问推进</div>
    <div class="p8-q">你是买方还是卖方? / 谁是第一个真实用户? / 这周能做的最小验证是什么?</div>
  </div>
  <div class="p8-cta">
    <div class="p8-cta-q">你现在卡在哪一步?</div>
    <div class="p8-cta-btn">评论区聊聊 👇</div>
  </div>
</div>
<div class="page-num">8/8</div>
"""))


def main() -> None:
    out_dir = ROOT
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": W, "height": H}, device_scale_factor=2)
        for name, html in PAGES:
            page.set_content(f"<!DOCTYPE html><html><body>{html}</body></html>")
            page.wait_for_timeout(150)
            out_path = out_dir / f"{name}.png"
            page.screenshot(path=str(out_path))
            print(f"  ✓ {out_path.name}")
        browser.close()
    print(f"\n共 {len(PAGES)} 页,输出到 {out_dir}")


if __name__ == "__main__":
    main()
