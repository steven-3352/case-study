#!/usr/bin/env python3
"""T043 小红书图文轮播 · 7 页真实出图.

内容来源:script/T043_录音提词稿.md(定稿口播原文,一字不改引用3步清单)+
design/retention_beat_sheet.md 末尾「小红书图文轮播」7页规划。
色板复用 T040 design_language.md v2 浅色 token(暖白底,禁AI味暗色)。
画布:1080x1920(pipeline/screen_dims.py 锁定 9:16)。

⚠️ T043 最高优先级约束(全篇贯穿):
- 小红书"AI失忆"话题顶流是情感陪伴/AI恋人群体,本条必须明确框定"工作向"场景
- 对话/消息容器一律用矩形工作卡片(系统消息/通知卡),禁止圆角气泡+尾巴的社交聊天视觉
- 禁用暖粉色系、禁用心形/爱心图标、禁用"想念""陪伴""记住我""认识你很久"类文案
- 示例文本一律工作场景措辞(项目/方案/排期/任务),不出现闲聊/情绪倾诉类措辞

用法: .venv/bin/python publish/2026-W30/D04-AI失忆/小红书轮播/build_carousel.py
"""
from __future__ import annotations

import pathlib
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent
W, H = 1080, 1920

# ── design_language.md v2 token(与 T040 一致,复用同一套浅色系统)──
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

/* 矩形工作卡片体系(禁圆角气泡+尾巴)*/
.work-card {{ background:{CANVAS}; border-radius:10px; border:1px solid rgba(28,30,34,0.14);
  box-shadow:0 3px 14px rgba(28,30,34,0.07); overflow:hidden; }}
.work-card-head {{ display:flex; align-items:center; gap:14px; padding:20px 28px;
  background:{SURFACE}; border-bottom:1px solid rgba(28,30,34,0.10); }}
.work-card-dot {{ width:14px; height:14px; border-radius:3px; background:{MUTED}; }}
.work-card-label {{ font-size:24px; color:{MUTED}; font-weight:600; letter-spacing:0.5px; }}
.work-card-body {{ padding:32px 28px; font-size:30px; line-height:1.6; color:{INK}; }}
.work-card-body.system {{ color:{ACCENT}; font-weight:700; }}
"""

PAGES = []

# ── P1 封面 ──
PAGES.append(("P1_封面", f"""
<style>{BASE_CSS}
.p1-wrap {{ padding:0 72px; }}
.p1-eyebrow {{ font-size:26px; color:{MUTED}; margin-bottom:24px; letter-spacing:1px; }}
.p1-title {{ font-size:74px; font-weight:800; line-height:1.3; color:{INK}; }}
.p1-title .hl {{ color:{ACCENT}; }}
.p1-mock {{ margin-top:96px; padding:0 72px; }}
.p1-mock-caption {{ font-size:24px; color:{MUTED}; margin-bottom:16px; }}
</style>
<div class="vgroup">
<div class="p1-wrap">
  <div class="p1-eyebrow">真实使用场景 · 换设备记忆丢失</div>
  <div class="p1-title">换个设备,AI就<span class="hl">"翻脸不认账"</span>?<br>3步让它<span class="hl">记住你</span></div>
</div>
<div class="p1-mock">
  <div class="p1-mock-caption">手机端 · 工作助理</div>
  <div class="work-card">
    <div class="work-card-head"><div class="work-card-dot"></div><div class="work-card-label">系统消息</div></div>
    <div class="work-card-body system">"没记录,不能装记得。"</div>
  </div>
</div>
</div>
<div class="page-num">1/7</div>
"""))

# ── P2 痛点(工作场景截图既视感)──
PAGES.append(("P2_痛点", f"""
<style>{BASE_CSS}
.p2-wrap {{ padding:0 72px; }}
.p2-line {{ font-size:52px; font-weight:700; line-height:1.5; color:{INK}; }}
.p2-line .weak {{ color:{MUTED}; font-weight:400; font-size:32px; display:block; margin-top:16px; }}
.p2-cards {{ margin-top:72px; padding:0 72px; display:flex; flex-direction:column; gap:28px; }}
.p2-mock-caption {{ font-size:24px; color:{MUTED}; margin-bottom:12px; }}
</style>
<div class="vgroup">
<div class="p2-wrap">
  <div class="p2-line">手机上问完一半<br>接着打开电脑问<span class="weak">——AI 说"没记录"</span></div>
</div>
<div class="p2-cards">
  <div>
    <div class="p2-mock-caption">📱 手机端 · 工作助理</div>
    <div class="work-card">
      <div class="work-card-head"><div class="work-card-dot"></div><div class="work-card-label">我发送</div></div>
      <div class="work-card-body">"接着上次的方案,继续往下推进一下排期。"</div>
    </div>
  </div>
  <div>
    <div class="p2-mock-caption">💻 电脑端 · 工作助理</div>
    <div class="work-card accent-box">
      <div class="work-card-head"><div class="work-card-dot" style="background:{ACCENT}"></div><div class="work-card-label" style="color:{ACCENT}">系统消息</div></div>
      <div class="work-card-body system">"我这边没有这条记录,不能装作记得。"</div>
    </div>
  </div>
</div>
</div>
<div class="page-num">2/7</div>
"""))

# ── P3 揭真相(双设备断连示意图)──
PAGES.append(("P3_揭真相", f"""
<style>{BASE_CSS}
.p3-wrap {{ padding:0 72px; }}
.p3-title {{ font-size:48px; font-weight:800; line-height:1.4; color:{INK}; margin-bottom:12px; }}
.p3-title .hl {{ color:{ACCENT}; }}
.p3-sub {{ font-size:30px; color:{MUTED}; margin-bottom:72px; }}
.p3-diagram {{ padding:0 64px; display:flex; align-items:center; gap:0; }}
.p3-panel {{ flex:1; padding:40px 24px; text-align:center; }}
.p3-panel-label {{ font-size:26px; color:{MUTED}; margin-bottom:16px; font-weight:600; }}
.p3-panel-icon {{ font-size:64px; margin-bottom:12px; }}
.p3-panel-sub {{ font-size:22px; color:{MUTED}; margin-top:12px; }}
.p3-break {{ width:120px; display:flex; flex-direction:column; align-items:center; }}
.p3-break-line {{ width:100%; height:2px; background:repeating-linear-gradient(90deg,{MUTED} 0 10px,transparent 10px 20px); }}
.p3-break-x {{ font-size:44px; color:{ACCENT}; font-weight:800; margin-top:8px; }}
.p3-caption {{ margin-top:64px; padding:0 72px; font-size:28px; color:{INK}; line-height:1.7; text-align:center; }}
</style>
<div class="vgroup">
<div class="p3-wrap">
  <div class="p3-title">查完才知道:<span class="hl">不是 AI 坏</span></div>
  <div class="p3-sub">是两套记忆,互相看不见</div>
  <div class="p3-diagram">
    <div class="p3-panel work-card">
      <div class="p3-panel-label">手机端记忆库</div>
      <div class="p3-panel-icon">📱</div>
      <div class="p3-panel-sub">只存本机对话</div>
    </div>
    <div class="p3-break"><div class="p3-break-line"></div><div class="p3-break-x">⊘</div></div>
    <div class="p3-panel work-card">
      <div class="p3-panel-label">电脑端记忆库</div>
      <div class="p3-panel-icon">💻</div>
      <div class="p3-panel-sub">只存本机对话</div>
    </div>
  </div>
  <div class="p3-caption">两边各自记东西,<span style="color:{ACCENT};font-weight:700">谁也读不到谁</span></div>
</div>
</div>
<div class="page-num">3/7</div>
"""))

# ── P4 3步清单原图(收藏物核心)──
PAGES.append(("P4_三步清单", f"""
<style>{BASE_CSS}
.p4-wrap {{ padding:96px 64px 0; }}
.p4-title {{ font-size:48px; font-weight:800; color:{INK}; margin-bottom:8px; }}
.p4-sub {{ font-size:26px; color:{MUTED}; margin-bottom:56px; }}
.p4-item {{ display:flex; gap:28px; margin-bottom:36px; align-items:flex-start; }}
.p4-num {{ font-size:44px; font-weight:800; color:{ACCENT}; width:76px; flex-shrink:0; }}
.p4-item-card {{ flex:1; padding:32px 32px; }}
.p4-item-text {{ font-size:32px; line-height:1.6; color:{INK}; font-weight:600; }}
.p4-caption {{ margin-top:40px; text-align:center; font-size:26px; color:{MUTED}; }}
</style>
<div class="vgroup">
<div class="p4-wrap" style="padding:0 64px;">
  <div class="p4-title">📌 3步让AI记住你</div>
  <div class="p4-sub">一字不改可照做 · 可截图抄走</div>
  <div class="p4-item">
    <div class="p4-num">①</div>
    <div class="p4-item-card card"><div class="p4-item-text">信息别只口头说,<span style="color:{ACCENT}">写进记忆文件</span></div></div>
  </div>
  <div class="p4-item">
    <div class="p4-num">②</div>
    <div class="p4-item-card card"><div class="p4-item-text">存到<span style="color:{ACCENT}">跨设备、跨对话</span>都能读到的位置,别锁死在一次对话框里</div></div>
  </div>
  <div class="p4-item">
    <div class="p4-num">③</div>
    <div class="p4-item-card card"><div class="p4-item-text">隔一阵回去更新——<span style="color:{ACCENT}">别指望AI自己会整理</span></div></div>
  </div>
  <div class="p4-caption">↓ 截图保存,下次直接照这三步设置</div>
</div>
</div>
<div class="page-num">4/7</div>
"""))

# ── P5 为什么有效 ──
PAGES.append(("P5_为什么有效", f"""
<style>{BASE_CSS}
.p5-wrap {{ padding:0 72px; }}
.p5-title {{ font-size:46px; font-weight:800; margin-bottom:64px; }}
.p5-compare {{ display:flex; gap:24px; margin-bottom:56px; }}
.p5-col {{ flex:1; padding:36px 28px; }}
.p5-col-left {{ background:{SURFACE}; border-radius:12px; }}
.p5-col-right {{ background:{CANVAS}; border:2px solid {ACCENT}; border-radius:12px; }}
.p5-col-label {{ font-size:24px; color:{MUTED}; margin-bottom:16px; font-weight:600; }}
.p5-col-right .p5-col-label {{ color:{ACCENT}; }}
.p5-col-body {{ font-size:28px; line-height:1.6; color:{INK}; }}
.p5-note {{ font-size:32px; line-height:1.7; color:{INK}; text-align:center; font-weight:600; }}
</style>
<div class="p5-wrap vgroup">
  <div class="p5-title">为什么这样做有效?</div>
  <div class="p5-compare">
    <div class="p5-col p5-col-left">
      <div class="p5-col-label">临时对话</div>
      <div class="p5-col-body">对话框一关,信息跟着消失<br><span style="color:{MUTED}">只存在这一次会话里</span></div>
    </div>
    <div class="p5-col p5-col-right">
      <div class="p5-col-label">记忆文件</div>
      <div class="p5-col-body">独立存在,不随对话消失<br><span style="color:{ACCENT};font-weight:700">跨设备、跨对话都能读到</span></div>
    </div>
  </div>
  <div class="p5-note">信息的"落点"不同,<br>决定了它能不能被下次找到</div>
</div>
<div class="page-num">5/7</div>
"""))

# ── P6 诚实分寸(红线安全句)──
PAGES.append(("P6_诚实分寸", f"""
<style>{BASE_CSS}
.p6-wrap {{ padding:0 72px; }}
.p6-title {{ font-size:46px; font-weight:800; margin-bottom:72px; }}
.p6-bar-label {{ display:flex; justify-content:space-between; font-size:26px; color:{MUTED}; margin-bottom:16px; }}
.p6-bar-track {{ width:100%; height:32px; background:{SURFACE}; border-radius:16px; overflow:hidden; }}
.p6-bar-fill {{ width:14%; height:100%; background:{ACCENT}; border-radius:16px; }}
.p6-bar-note {{ margin-top:16px; font-size:24px; color:{ACCENT}; }}
.p6-text {{ margin-top:80px; font-size:36px; line-height:1.7; color:{INK}; text-align:center; }}
.p6-text .strong {{ font-weight:800; }}
.p6-text .weak {{ color:{MUTED}; font-size:28px; display:block; margin-top:20px; }}
</style>
<div class="p6-wrap vgroup">
  <div class="p6-title">诚实说句实话</div>
  <div class="p6-bar-label"><span>丢失风险</span><span>大幅降低</span></div>
  <div class="p6-bar-track"><div class="p6-bar-fill"></div></div>
  <div class="p6-bar-note">⚠ 不保证 100%</div>
  <div class="p6-text"><span class="strong">做到这三步,丢失概率能大幅降低,</span><span class="weak">但没人敢保证百分百不忘。</span></div>
</div>
<div class="page-num">6/7</div>
"""))

# ── P7 CTA ──
PAGES.append(("P7_CTA", f"""
<style>{BASE_CSS}
.p7-wrap {{ padding:0 80px; height:{H}px; display:flex; flex-direction:column;
  align-items:center; justify-content:center; text-align:center; }}
.p7-q {{ font-size:56px; font-weight:800; line-height:1.5; color:{INK}; margin-bottom:56px; }}
.p7-comment-box {{ width:100%; padding:32px 36px; text-align:left; margin-bottom:48px; }}
.p7-comment-label {{ font-size:24px; color:{MUTED}; margin-bottom:12px; }}
.p7-comment-input {{ font-size:28px; color:{MUTED}; }}
.p7-cta {{ font-size:32px; color:{ACCENT}; font-weight:700; padding:24px 48px;
  border:2px solid {ACCENT}; border-radius:12px; }}
</style>
<div class="p7-wrap">
  <div class="p7-q">你的AI换个地方<br>还认你吗?</div>
  <div class="p7-comment-box work-card">
    <div class="p7-comment-label">评论区 · 讨论</div>
    <div class="p7-comment-input">说说你踩过的坑…</div>
  </div>
  <div class="p7-cta">评论区聊聊 👇</div>
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
            print(f"  ok {out_path.name}")
        browser.close()
    print(f"\n共 {len(PAGES)} 页,输出到 {out_dir}")


if __name__ == "__main__":
    main()
