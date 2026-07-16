#!/usr/bin/env python3
"""T044 小红书图文轮播 · 7 页真实出图.

内容来源:script/T044_录音提词稿.md(定稿口播原文,7段)+ design/retention_beat_sheet.md
(小红书图文轮播 7 页规划表)+ Hermes 原矿 raw-export 2026-07-14 真实对话事件(接着昨天的
方向往下问,AI翻遍聊天记录/笔记后回"没有这条线",后补充是"没走收尾、没记进本子")。
色板:沿用 T040 design_language.md v2 浅色 token(暖白底,禁AI味暗色/禁霓虹蓝紫)。
画布:1080x1920(pipeline/screen_dims.py 锁定 9:16)。

⚠️ T044 与 T040/T043 差异化:本条基调"故事+反讽"(不是教程/清单感)——除 P6 的
"检测向 vs 预防向"轻量对比外,不做纵向堆叠清单卡片;P2/P3/P5 走叙事/演示节奏。
⚠️ 工作向框定:全片消息/通知容器一律用矩形工作卡片,禁圆角气泡+尾巴的社交聊天视觉;
示例文本一律用"聊天记录/今天的笔记/流程/本子"等工作场景措辞,禁暖粉色、禁心形图标、
禁"想念/陪伴/记住我"类文案。

用法: .venv/bin/python publish/2026-W30/D05-AI记岔了/小红书轮播/build_carousel.py
"""
from __future__ import annotations

import pathlib
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent
W, H = 1080, 1920

# ── design_language.md v2 token(与 T040 一致,不重新定义)──
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
.card {{ background:{SURFACE}; border-radius:14px; border:1px solid rgba(28,30,34,0.10);
  box-shadow:0 4px 20px rgba(28,30,34,0.08); }}
.accent-box {{ border:2px solid {ACCENT}; border-radius:14px; }}
.page-num {{ position:absolute; bottom:56px; right:64px; font-size:24px; color:{MUTED}; }}
.tag {{ display:inline-block; align-self:center; width:fit-content; padding:8px 20px; border-radius:8px; font-size:24px; font-weight:600; }}
.vgroup {{ min-height:{H}px; display:flex; flex-direction:column; justify-content:center; }}
/* 矩形工作卡片(禁气泡+尾巴)*/
.wcard {{ border-radius:14px; padding:32px 36px; }}
.wcard-label {{ font-size:22px; color:{MUTED}; margin-bottom:10px; letter-spacing:0.5px; }}
.wcard-body {{ font-size:30px; line-height:1.55; color:{INK}; }}
"""

PAGES = []

# ── P1 封面(叙事悬念,非对比栏)──
PAGES.append(("P1_封面", f"""
<style>{BASE_CSS}
.p1-wrap {{ padding:0 72px; }}
.p1-eyebrow {{ font-size:26px; color:{MUTED}; margin-bottom:28px; letter-spacing:1px; }}
.p1-eyebrow .dot {{ color:{ACCENT}; }}
.p1-title {{ font-size:72px; font-weight:800; line-height:1.32; color:{INK}; }}
.p1-title .hl {{ color:{ACCENT}; }}
.p1-teaser {{ margin:88px 72px 0; padding:40px 40px; position:relative; overflow:hidden; }}
.p1-teaser-label {{ font-size:22px; color:{MUTED}; margin-bottom:16px; }}
.p1-teaser-body {{ font-size:32px; line-height:1.6; color:{INK}; font-weight:600; filter:blur(0.4px); }}
.p1-teaser-mask {{ position:absolute; left:0; right:0; bottom:0; height:120px;
  background:linear-gradient(to bottom, rgba(238,236,229,0), {SURFACE}); }}
.p1-teaser-hint {{ margin-top:18px; font-size:24px; color:{ACCENT}; font-weight:700; }}
</style>
<div class="vgroup">
<div class="p1-wrap">
  <div class="p1-eyebrow">真实经历<span class="dot"> · </span>工作 AI 助理翻车实录</div>
  <div class="p1-title">我造 AI 助理<br>为了不用自己记<br>结果<span class="hl">它自己先漏了</span></div>
</div>
<div class="p1-teaser card">
  <div class="p1-teaser-label">翻遍聊天记录和笔记后,它回我</div>
  <div class="p1-teaser-body">"没有这条线,<span style="color:{ACCENT}">我这边没有记录,不能装作记得。</span>"</div>
  <div class="p1-teaser-mask"></div>
  <div class="p1-teaser-hint">↓ 滑动看完整经过</div>
</div>
</div>
<div class="page-num">1/7</div>
"""))

# ── P2 痛点还原(叙事推进,非清单)──
PAGES.append(("P2_痛点还原", f"""
<style>{BASE_CSS}
.p2-wrap {{ padding:0 72px; }}
.p2-lead {{ font-size:34px; line-height:1.7; color:{INK}; margin-bottom:40px; }}
.p2-user {{ background:{CANVAS}; border:1px solid rgba(28,30,34,0.14); margin-left:auto; max-width:760px; }}
.p2-user .wcard-label {{ text-align:right; }}
.p2-user .wcard-body {{ text-align:right; }}
.p2-scan {{ display:flex; gap:20px; margin:36px 0; }}
.p2-scan-item {{ flex:1; padding:26px 24px; text-align:center; }}
.p2-scan-icon {{ font-size:40px; margin-bottom:10px; }}
.p2-scan-label {{ font-size:24px; color:{INK}; font-weight:700; margin-bottom:6px; }}
.p2-scan-status {{ font-size:20px; color:{MUTED}; }}
.p2-reply {{ margin-top:8px; }}
.p2-reply-body {{ color:{ACCENT}; font-weight:700; }}
</style>
<div class="p2-wrap vgroup">
  <div class="p2-lead">前几天在手机上,<br>接着昨天聊的那个方向往下问。</div>
  <div class="wcard card p2-user">
    <div class="wcard-label">你</div>
    <div class="wcard-body">接着昨天那个方向,再往下推一下</div>
  </div>
  <div class="p2-scan">
    <div class="card p2-scan-item">
      <div class="p2-scan-icon">📃</div>
      <div class="p2-scan-label">聊天记录</div>
      <div class="p2-scan-status">翻遍 · 未找到</div>
    </div>
    <div class="card p2-scan-item">
      <div class="p2-scan-icon">📓</div>
      <div class="p2-scan-label">今天的笔记</div>
      <div class="p2-scan-status">翻遍 · 未找到</div>
    </div>
  </div>
  <div class="wcard accent-box p2-reply">
    <div class="wcard-label" style="color:{ACCENT}">AI 助理</div>
    <div class="wcard-body p2-reply-body">没有这条线,我这边没有记录,不能装作记得。</div>
  </div>
</div>
<div class="page-num">2/7</div>
"""))

# ── P3 反转·信任(AI自曝不甩锅)──
PAGES.append(("P3_反转", f"""
<style>{BASE_CSS}
.p3-wrap {{ padding:0 72px; }}
.p3-eyebrow {{ font-size:26px; color:{MUTED}; margin-bottom:24px; }}
.p3-quote {{ font-size:46px; font-weight:800; line-height:1.55; color:{INK}; margin-bottom:12px; }}
.p3-quote .hl {{ color:{ACCENT}; }}
.p3-caption {{ font-size:24px; color:{MUTED}; margin-bottom:64px; }}
.p3-flow {{ display:flex; align-items:center; justify-content:space-between; padding:0 8px; }}
.p3-node {{ flex:1; text-align:center; }}
.p3-node-dot {{ width:20px; height:20px; border-radius:5px; background:{SECONDARY}; margin:0 auto 16px; }}
.p3-node-label {{ font-size:24px; color:{INK}; font-weight:600; line-height:1.4; }}
.p3-line {{ flex:0 0 60px; height:2px; background:rgba(28,30,34,0.18); margin-top:-40px; }}
</style>
<div class="p3-wrap vgroup">
  <div class="p3-eyebrow">它没有敷衍,反而说了实话</div>
  <div class="p3-quote">"不是它坏了,<br><span class="hl">是流程还没补上。</span>"</div>
  <div class="p3-caption">—— 它自己补的一句</div>
  <div class="card" style="padding:56px 44px;">
    <div class="p3-flow">
      <div class="p3-node"><div class="p3-node-dot"></div><div class="p3-node-label">聊完</div></div>
      <div class="p3-line"></div>
      <div class="p3-node"><div class="p3-node-dot"></div><div class="p3-node-label">没走<br>收尾</div></div>
      <div class="p3-line"></div>
      <div class="p3-node"><div class="p3-node-dot" style="background:{ACCENT}"></div><div class="p3-node-label" style="color:{ACCENT}">没记进<br>本子</div></div>
    </div>
  </div>
</div>
<div class="page-num">3/7</div>
"""))

# ── P4 情绪金句(可截图传播)──
PAGES.append(("P4_情绪金句", f"""
<style>{BASE_CSS}
.p4-wrap {{ padding:0 80px; text-align:center; }}
.p4-tag {{ background:{CANVAS}; border:1px solid rgba(28,30,34,0.16); color:{MUTED};
  margin-bottom:56px; }}
.p4-quote {{ font-size:52px; font-weight:800; line-height:1.6; color:{INK}; }}
.p4-quote .hl {{ color:{ACCENT}; }}
.p4-compare {{ display:flex; justify-content:center; gap:28px; margin-top:80px; }}
.p4-item {{ padding:28px 40px; border-radius:14px; text-align:center; min-width:220px; }}
.p4-item-no {{ background:transparent; border:1.5px dashed rgba(28,30,34,0.25); opacity:0.5; }}
.p4-item-no .p4-item-mark {{ color:{MUTED}; }}
.p4-item-yes {{ border:2px solid {ACCENT}; }}
.p4-item-yes .p4-item-mark {{ color:{ACCENT}; }}
.p4-item-mark {{ font-size:44px; font-weight:800; margin-bottom:10px; }}
.p4-item-text {{ font-size:24px; color:{INK}; }}
</style>
<div class="p4-wrap vgroup">
  <div class="tag p4-tag">可截图</div>
  <div class="p4-quote">挺讽刺,但也挺庆幸——<br>它<span class="hl">没顺着我瞎编,</span><br>漏了就老实认。</div>
  <div class="p4-compare">
    <div class="p4-item p4-item-no"><div class="p4-item-mark">✕</div><div class="p4-item-text">瞎编</div></div>
    <div class="p4-item p4-item-yes card"><div class="p4-item-mark">✓</div><div class="p4-item-text">老实认</div></div>
  </div>
</div>
<div class="page-num">4/7</div>
"""))

# ── P5 抓包验证法(收藏主页 · 轻量演示非清单)──
PAGES.append(("P5_抓包验证法", f"""
<style>{BASE_CSS}
.p5-wrap {{ padding:0 72px; }}
.p5-tag {{ border:2px solid {ACCENT}; color:{ACCENT}; font-weight:700; margin-bottom:28px; }}
.p5-title {{ font-size:44px; font-weight:800; color:{INK}; margin-bottom:16px; }}
.p5-sub {{ font-size:28px; color:{MUTED}; margin-bottom:56px; }}
.p5-actions {{ display:flex; gap:24px; padding:44px 36px; }}
.p5-action {{ flex:1; text-align:center; }}
.p5-action-icon {{ font-size:52px; margin-bottom:16px; }}
.p5-action-text {{ font-size:28px; font-weight:700; color:{INK}; line-height:1.5; }}
.p5-plus {{ font-size:32px; color:{MUTED}; align-self:center; }}
.p5-result {{ margin-top:56px; text-align:center; }}
.p5-result-flag {{ font-size:40px; font-weight:800; color:{ACCENT}; line-height:1.5; }}
</style>
<div class="p5-wrap vgroup">
  <div class="tag p5-tag">抓包验证法</div>
  <div class="p5-title">真要紧的事,别只问一次</div>
  <div class="p5-sub">现在学乖了,会多验一步再信</div>
  <div class="card p5-actions">
    <div class="p5-action"><div class="p5-action-icon">📱→💻</div><div class="p5-action-text">换个设备<br>再问一遍</div></div>
    <div class="p5-plus">+</div>
    <div class="p5-action"><div class="p5-action-icon">🗓️</div><div class="p5-action-text">隔天<br>再问一遍</div></div>
  </div>
  <div class="p5-result">
    <div class="p5-result-flag">⚑ 答不上来,才是真信号</div>
  </div>
</div>
<div class="page-num">5/7</div>
"""))

# ── P6 检测向 vs 预防向(干货深度 · 客观并列不贬低)──
PAGES.append(("P6_检测向", f"""
<style>{BASE_CSS}
.p6-wrap {{ padding:0 72px; }}
.p6-title {{ font-size:42px; font-weight:800; color:{INK}; margin-bottom:56px; }}
.p6-title .hl {{ color:{ACCENT}; }}
.p6-compare {{ display:flex; gap:24px; }}
.p6-col {{ flex:1; padding:36px 28px; }}
.p6-col-a {{ background:{SURFACE}; }}
.p6-col-b {{ border:2px solid {ACCENT}; }}
.p6-col-label {{ font-size:24px; font-weight:700; color:{MUTED}; margin-bottom:14px; }}
.p6-col-b .p6-col-label {{ color:{ACCENT}; }}
.p6-col-desc {{ font-size:24px; line-height:1.6; color:{INK}; }}
.p6-note {{ margin-top:48px; font-size:26px; line-height:1.7; color:{INK}; text-align:center; }}
.p6-caveat {{ margin-top:24px; font-size:22px; color:{MUTED}; text-align:center; line-height:1.6; }}
</style>
<div class="p6-wrap vgroup">
  <div class="p6-title">这是<span class="hl">"检测"</span>,不是"预防"</div>
  <div class="p6-compare">
    <div class="card p6-col p6-col-a">
      <div class="p6-col-label">预防向 · 常见做法</div>
      <div class="p6-col-desc">提前设置一次:写好规则、建好记忆库,尽量让它"别忘"</div>
    </div>
    <div class="card p6-col p6-col-b">
      <div class="p6-col-label">检测向 · 抓包验证法</div>
      <div class="p6-col-desc">事后验一次:换设备/隔天复测,发现它"真忘了"</div>
    </div>
  </div>
  <div class="p6-note">两种思路不冲突——<br>一个负责"尽量别忘",一个负责"发现真忘了"</div>
  <div class="p6-caveat">不是百分百测出所有遗忘,但至少能抓到最要命的那次</div>
</div>
<div class="page-num">6/7</div>
"""))

# ── P7 CTA ──
PAGES.append(("P7_CTA", f"""
<style>{BASE_CSS}
.p7-wrap {{ padding:0 80px; height:{H}px; display:flex; flex-direction:column;
  align-items:center; justify-content:center; text-align:center; }}
.p7-q {{ font-size:54px; font-weight:800; line-height:1.5; color:{INK}; margin-bottom:48px; }}
.p7-cta {{ font-size:32px; color:{ACCENT}; font-weight:700; padding:24px 48px;
  border:2px solid {ACCENT}; border-radius:10px; }}
</style>
<div class="p7-wrap">
  <div class="p7-q">你有没有被 AI<br>"记岔"过?</div>
  <div class="p7-cta">评论区说说 👇</div>
</div>
<div class="page-num">7/7</div>
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
