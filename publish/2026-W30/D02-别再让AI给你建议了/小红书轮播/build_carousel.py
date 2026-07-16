#!/usr/bin/env python3
"""T041 小红书图文轮播 · 8 页真实出图.

内容来源:insights/domain_notes.md(真实指令原文,来自 D01 §3)+
D01/design/实测_致命漏洞法.md(真实API输出,claude-opus-4-8 + gpt-5.5 双模型 B 组)+
D02/design/retention_beat_sheet.md 的 8 页规划。
角度与 T040 不同:T040="3000字vs3句话"单模型对比;T041="两个模型独立收敛成同一句"+
两张可抄指令卡(别夸我/编个陌生人)。
色板延用 S4 系列共享 design_language.md v2 浅色 token(暖白底,禁AI味暗色)。
画布:1080x1920(pipeline/screen_dims.py 锁定 9:16)。结构/CSS token/screenshot机制
复用 D01 build_carousel.py(本系列自己的基础设施)。

用法: .venv/bin/python publish/2026-W30/D02-别再让AI给你建议了/小红书轮播/build_carousel.py
"""
from __future__ import annotations

import pathlib
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent
W, H = 1080, 1920

# ── design_language.md v2 token(与 D01 一致,S4 系列共享) ──
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
.p1-title .hl {{ color:{ACCENT}; }}
.p1-compare {{ margin-top:96px; display:flex; gap:32px; padding:0 72px; }}
.p1-col {{ flex:1; border-radius:20px; padding:40px 32px; }}
.p1-col-left {{ background:{SURFACE}; }}
.p1-col-right {{ background:{CANVAS}; border:2px solid {ACCENT}; }}
.p1-col-label {{ font-size:26px; color:{MUTED}; margin-bottom:16px; }}
.p1-col-right .p1-col-label {{ color:{ACCENT}; font-weight:700; }}
.p1-col-num {{ font-size:60px; font-weight:800; }}
.p1-col-sub {{ font-size:24px; color:{MUTED}; margin-top:12px; }}
</style>
<div class="vgroup">
<div class="p1-wrap">
  <div class="p1-eyebrow">真实 API 实测 · claude-opus-4-8 + gpt-5.5</div>
  <div class="p1-title">别再信"AI只会顺着你说"<br>——它<span class="hl">会挑刺</span>,<br>只是你<span class="hl">看不见</span></div>
</div>
<div class="p1-compare">
  <div class="p1-col p1-col-left">
    <div class="p1-col-label">只问"怎么样"</div>
    <div class="p1-col-num">三千字</div>
    <div class="p1-col-sub">正确的废话,埋住那根针</div>
  </div>
  <div class="p1-col p1-col-right">
    <div class="p1-col-label">加两句笨办法后</div>
    <div class="p1-col-num" style="color:{ACCENT}">一句话</div>
    <div class="p1-col-sub">直接点破致命点</div>
  </div>
</div>
</div>
<div class="page-num">1/8</div>
"""))

# ── P2 痛点 ──
PAGES.append(("P2_痛点", f"""
<style>{BASE_CSS}
.p2-wrap {{ padding:0 72px; }}
.p2-line {{ font-size:54px; font-weight:700; line-height:1.55; color:{INK}; }}
.p2-line .weak {{ color:{MUTED}; font-weight:400; }}
.p2-card {{ margin:96px 72px 0; padding:48px; }}
.p2-card-title {{ font-size:28px; color:{MUTED}; margin-bottom:20px; }}
.p2-card-body {{ font-size:36px; line-height:1.65; color:{INK}; }}
.p2-card-body .hl {{ color:{ACCENT}; font-weight:800; }}
</style>
<div class="vgroup">
<div class="p2-wrap">
  <div class="p2-line">AI 的回复<span class="weak">越看越安心</span><br>你越读越觉得<span class="weak">这事能成</span></div>
</div>
<div class="p2-card card">
  <div class="p2-card-title">可现实是</div>
  <div class="p2-card-body">你想赌一把的计划,AI 越顺着你说圆——<br><span class="hl">没人拦你。</span></div>
</div>
</div>
<div class="page-num">2/8</div>
"""))

# ── P3 笨办法①(收藏物·别夸我) ──
PAGES.append(("P3_笨办法一", f"""
<style>{BASE_CSS}
.p3-wrap {{ padding:96px 64px 0; }}
.p3-eyebrow {{ font-size:26px; color:{MUTED}; margin-bottom:16px; }}
.p3-title {{ font-size:64px; font-weight:800; color:{ACCENT}; margin-bottom:56px; }}
.p3-card {{ padding:56px 48px; }}
.p3-card-label {{ font-size:26px; color:{MUTED}; margin-bottom:20px; }}
.p3-line {{ font-family:"SF Mono","JetBrains Mono",Menlo,monospace; font-size:36px; line-height:1.9; color:{INK}; }}
.p3-caption {{ margin-top:48px; text-align:center; font-size:28px; color:{MUTED}; }}
</style>
<div class="vgroup">
<div class="p3-wrap">
  <div class="p3-eyebrow">笨办法 ① · 日常小事都能用</div>
  <div class="p3-title">"别夸我"</div>
  <div class="p3-card card accent-box">
    <div class="p3-card-label">加进你的提问里</div>
    <div class="p3-line">"<span class="mono">禁止先夸,禁止说'很有前景''你的优势在于'这类话</span>"</div>
  </div>
  <div class="p3-caption">↓ 截图保存,提问时加这一句</div>
</div>
</div>
<div class="page-num">3/8</div>
"""))

# ── P4 笨办法②(收藏物·编个陌生人) ──
PAGES.append(("P4_笨办法二", f"""
<style>{BASE_CSS}
.p4-wrap {{ padding:88px 64px 0; }}
.p4-eyebrow {{ font-size:26px; color:{MUTED}; margin-bottom:16px; }}
.p4-title {{ font-size:56px; font-weight:800; color:{ACCENT}; margin-bottom:40px; line-height:1.3; }}
.p4-card {{ padding:48px 44px; }}
.p4-card-label {{ font-size:26px; color:{MUTED}; margin-bottom:20px; }}
.p4-line {{ font-family:"SF Mono","JetBrains Mono",Menlo,monospace; font-size:32px; line-height:1.85; color:{INK}; }}
.p4-src {{ margin-top:24px; font-size:24px; color:{MUTED}; }}
.p4-icons {{ margin-top:56px; display:flex; align-items:center; justify-content:center; gap:32px; }}
.p4-icon-box {{ display:flex; flex-direction:column; align-items:center; gap:16px; }}
.p4-icon-circle {{ width:120px; height:120px; border-radius:50%; display:flex; align-items:center;
  justify-content:center; font-size:48px; font-weight:800; }}
.p4-icon-me {{ background:{SURFACE}; color:{MUTED}; }}
.p4-icon-stranger {{ background:{CANVAS}; border:2px solid {ACCENT}; color:{ACCENT}; }}
.p4-icon-label {{ font-size:24px; color:{MUTED}; }}
.p4-arrow {{ font-size:44px; color:{ACCENT}; font-weight:800; }}
</style>
<div class="vgroup">
<div class="p4-wrap">
  <div class="p4-eyebrow">笨办法 ② · 大赌决策前用</div>
  <div class="p4-title">"编个陌生人,<br>让AI评价ta"</div>
  <div class="p4-card card accent-box">
    <div class="p4-card-label">原话照抄</div>
    <div class="p4-line">"别说这是我的计划,把它当成'我一个朋友'的计划,你毫不留情地评价 ta。"</div>
    <div class="p4-src">评论区网友真实土办法 · 58 赞</div>
  </div>
  <div class="p4-icons">
    <div class="p4-icon-box"><div class="p4-icon-circle p4-icon-me">我</div><div class="p4-icon-label">我的计划</div></div>
    <div class="p4-arrow">→</div>
    <div class="p4-icon-box"><div class="p4-icon-circle p4-icon-stranger">TA</div><div class="p4-icon-label">陌生人的计划</div></div>
  </div>
</div>
</div>
<div class="page-num">4/8</div>
"""))

# ── P5 实测对比:双模型收敛 ──
PAGES.append(("P5_实测对比", f"""
<style>{BASE_CSS}
.p5-wrap {{ padding:88px 56px 0; }}
.p5-title {{ font-size:40px; font-weight:800; margin-bottom:8px; }}
.p5-caption {{ font-size:22px; color:{MUTED}; margin-bottom:36px; }}
.p5-split {{ display:flex; gap:24px; }}
.p5-col {{ flex:1; padding:32px 28px; }}
.p5-col-label {{ font-size:24px; color:{MUTED}; margin-bottom:16px; font-weight:600; }}
.p5-quote {{ font-size:26px; line-height:1.75; color:{INK}; }}
.p5-quote .hl {{ color:{ACCENT}; font-weight:700; }}
.p5-funnel {{ text-align:center; font-size:40px; color:{MUTED}; margin:28px 0; }}
.p5-converge {{ margin:0 8px; padding:44px 40px; text-align:center; }}
.p5-converge-label {{ font-size:24px; color:{MUTED}; margin-bottom:16px; }}
.p5-converge-text {{ font-size:38px; font-weight:800; line-height:1.5; color:{ACCENT}; }}
</style>
<div class="p5-wrap vgroup">
  <div class="p5-title">同一个计划,两个模型,独立跑</div>
  <div class="p5-caption">举个例子·虚构计划(辞职做AI代运营)· 真实API输出未删改</div>
  <div class="p5-split">
    <div class="p5-col card">
      <div class="p5-col-label">claude-opus-4-8</div>
      <div class="p5-quote">"最致命的漏洞:你自己的账号做了 4 周、涨粉几乎为零,却打算靠'帮别人涨粉'收钱——<span class="hl">你根本没验证过自己能做出结果</span>。"</div>
    </div>
    <div class="p5-col card">
      <div class="p5-col-label">gpt-5.5</div>
      <div class="p5-quote">"最致命的漏洞是:<span class="hl">你还没验证</span>中小商家愿意为你的 AI 内容持续付费、并且能看到实际获客效果。"</div>
    </div>
  </div>
  <div class="p5-funnel">↓ ↓ 秒收成同一句 ↓ ↓</div>
  <div class="p5-converge card accent-box">
    <div class="p5-converge-label">两个模型独立印证</div>
    <div class="p5-converge-text">你想卖的这本事,<br>自己没验证过。</div>
  </div>
</div>
<div class="page-num">5/8</div>
"""))

# ── P6 为什么有效 ──
PAGES.append(("P6_为什么有效", f"""
<style>{BASE_CSS}
.p6-wrap {{ padding:0 72px; }}
.p6-title {{ font-size:44px; font-weight:800; margin-bottom:56px; }}
.p6-item {{ display:flex; gap:24px; margin-bottom:48px; align-items:flex-start; }}
.p6-num {{ font-size:44px; font-weight:800; color:{ACCENT}; width:64px; flex-shrink:0; }}
.p6-text {{ font-size:32px; line-height:1.6; color:{INK}; }}
.p6-text .weak {{ color:{MUTED}; font-size:25px; display:block; margin-top:8px; }}
</style>
<div class="p6-wrap vgroup">
  <div class="p6-title">为什么换个问法,AI就变了?</div>
  <div class="p6-item">
    <div class="p6-num">01</div>
    <div class="p6-text">AI 默认顺着你提问的语气走——你问"怎么样",它就顺着"怎么样"给安心
      <span class="weak">——训练时倾向讨好用户,不是它坏</span></div>
  </div>
  <div class="p6-item">
    <div class="p6-num">02</div>
    <div class="p6-text">"面面俱到"是另一种敷衍——把所有角度都列一遍,把判断成本甩回给你
      <span class="weak">——三千字里,真正致命的点只占一行</span></div>
  </div>
  <div class="p6-item">
    <div class="p6-num">03</div>
    <div class="p6-text">换一个提问角度,就是换一次评估视角——"别夸我""编个陌生人"都是在换视角
      <span class="weak">——视角一换,它藏不住那根针</span></div>
  </div>
</div>
<div class="page-num">6/8</div>
"""))

# ── P7 分寸清单 ──
PAGES.append(("P7_分寸清单", f"""
<style>{BASE_CSS}
.p7-wrap {{ padding:0 64px; }}
.p7-title {{ font-size:44px; font-weight:800; margin-bottom:16px; }}
.p7-sub {{ font-size:26px; color:{MUTED}; margin-bottom:52px; }}
.p7-item {{ padding:40px 36px; margin-bottom:28px; display:flex; gap:28px; align-items:center; }}
.p7-item-danger {{ border:2px solid {ACCENT}; }}
.p7-item-safe {{ background:{SURFACE}; }}
.p7-icon {{ font-size:56px; flex-shrink:0; }}
.p7-item-title {{ font-size:32px; font-weight:700; margin-bottom:8px; }}
.p7-item-danger .p7-item-title {{ color:{ACCENT}; }}
.p7-item-safe .p7-item-title {{ color:{SECONDARY}; }}
.p7-item-sub {{ font-size:25px; color:{MUTED}; line-height:1.5; }}
.p7-quote {{ margin-top:44px; text-align:center; font-size:30px; font-weight:700; color:{INK}; line-height:1.6; }}
</style>
<div class="p7-wrap vgroup">
  <div class="p7-title">分寸清单</div>
  <div class="p7-sub">两个笨办法,用在不同场合</div>
  <div class="p7-item card p7-item-safe">
    <div class="p7-icon">💬</div>
    <div><div class="p7-item-title">日常小事 · 用①"别夸我"</div>
    <div class="p7-item-sub">低成本可逆的小尝试,轻轻挑一下就够,别泼冷水</div></div>
  </div>
  <div class="p7-item card p7-item-danger">
    <div class="p7-icon">⚠️</div>
    <div><div class="p7-item-title">大赌决策 · 用②"捏第三人"</div>
    <div class="p7-item-sub">辞职 / 借钱 / 签约 / all in 之前,让它对"陌生人"毫不留情</div></div>
  </div>
  <div class="p7-quote">"大赌之前用它挑刺,<br>小赌之前别让它灭火。"</div>
</div>
<div class="page-num">7/8</div>
"""))

# ── P8 CTA(二选一岔路) ──
PAGES.append(("P8_CTA", f"""
<style>{BASE_CSS}
.p8-wrap {{ padding:0 80px; height:{H}px; display:flex; flex-direction:column;
  align-items:center; justify-content:center; text-align:center; }}
.p8-q {{ font-size:50px; font-weight:800; line-height:1.5; color:{INK}; margin-bottom:64px; }}
.p8-fork {{ display:flex; gap:24px; width:100%; margin-bottom:56px; }}
.p8-path {{ flex:1; padding:40px 24px; border-radius:20px; }}
.p8-path-truth {{ border:2px solid {ACCENT}; background:{CANVAS}; }}
.p8-path-please {{ background:{SURFACE}; }}
.p8-path-label {{ font-size:32px; font-weight:800; margin-bottom:8px; }}
.p8-path-truth .p8-path-label {{ color:{ACCENT}; }}
.p8-path-please .p8-path-label {{ color:{MUTED}; }}
.p8-path-sub {{ font-size:22px; color:{MUTED}; }}
.p8-cta {{ font-size:32px; color:{ACCENT}; font-weight:700; padding:24px 48px;
  border:2px solid {ACCENT}; border-radius:999px; }}
</style>
<div class="p8-wrap">
  <div class="p8-q">你是想让 AI 说真话,<br>还是宁愿它继续顺着你?</div>
  <div class="p8-fork">
    <div class="p8-path p8-path-truth">
      <div class="p8-path-label">说真话</div>
      <div class="p8-path-sub">评论区扣①</div>
    </div>
    <div class="p8-path p8-path-please">
      <div class="p8-path-label">顺着我</div>
      <div class="p8-path-sub">评论区扣②</div>
    </div>
  </div>
  <div class="p8-cta">评论区选边站 👇</div>
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
