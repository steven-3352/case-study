#!/usr/bin/env python3
"""T040 小红书图文轮播 · 8 页真实出图.

内容来源:insights/domain_notes.md(真实指令/分寸)+ design/实测_致命漏洞法.md(真实API输出)+
retention_beat_sheet.md 的 8 页规划。色板:design_language.md v2 浅色 token(暖白底,禁AI味暗色)。
画布:1080x1920(pipeline/screen_dims.py 锁定 9:16)。

用法: .venv/bin/python publish/2026-W30/D01-让AI说真话致命漏洞/小红书轮播/build_carousel.py
"""
from __future__ import annotations

import pathlib
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent
W, H = 1080, 1920

# ── design_language.md v2 token ──
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
.p1-title {{ font-size:80px; font-weight:800; line-height:1.25; color:{INK}; }}
.p1-title .hl {{ color:{ACCENT}; }}
.p1-compare {{ margin-top:100px; display:flex; gap:32px; padding:0 72px; }}
.p1-col {{ flex:1; border-radius:20px; padding:40px 32px; }}
.p1-col-left {{ background:{SURFACE}; }}
.p1-col-right {{ background:{CANVAS}; border:2px solid {ACCENT}; }}
.p1-col-label {{ font-size:26px; color:{MUTED}; margin-bottom:16px; }}
.p1-col-right .p1-col-label {{ color:{ACCENT}; font-weight:700; }}
.p1-col-num {{ font-size:64px; font-weight:800; }}
.p1-col-sub {{ font-size:24px; color:{MUTED}; margin-top:12px; }}
</style>
<div class="vgroup">
<div class="p1-wrap">
  <div class="p1-eyebrow">真实 API 实测 · claude-opus-4-8 + gpt-5.5</div>
  <div class="p1-title">AI 只会夸你的方案?<br>加<span class="hl">这一句</span>,<br>它立刻挑出<span class="hl">致命漏洞</span></div>
</div>
<div class="p1-compare">
  <div class="p1-col p1-col-left">
    <div class="p1-col-label">只问"怎么样"</div>
    <div class="p1-col-num">3000+字</div>
    <div class="p1-col-sub">八大节正确的废话</div>
  </div>
  <div class="p1-col p1-col-right">
    <div class="p1-col-label">加一句指令后</div>
    <div class="p1-col-num" style="color:{ACCENT}">3句话</div>
    <div class="p1-col-sub">精准点破致命点</div>
  </div>
</div>
</div>
<div class="page-num">1/8</div>
"""))

# ── P2 痛点 ──
PAGES.append(("P2_痛点", f"""
<style>{BASE_CSS}
.p2-wrap {{ padding:0 72px; }}
.p2-line {{ font-size:56px; font-weight:700; line-height:1.5; color:{INK}; }}
.p2-line .weak {{ color:{MUTED}; font-weight:400; }}
.p2-line .hl {{ color:{ACCENT}; }}
.p2-card {{ margin:100px 72px 0; padding:48px; }}
.p2-card-title {{ font-size:28px; color:{MUTED}; margin-bottom:20px; }}
.p2-card-body {{ font-size:36px; line-height:1.6; color:{INK}; }}
</style>
<div class="vgroup">
<div class="p2-wrap">
  <div class="p2-line">你把方案丢给 AI<br>问一句<span class="weak">"你觉得怎么样?"</span></div>
</div>
<div class="p2-card card">
  <div class="p2-card-title">得到的是</div>
  <div class="p2-card-body">满屏夸奖 + 三千字面面俱到的分析——<br><span style="color:{ACCENT};font-weight:700">那根真正要命的针,你找不到。</span></div>
</div>
</div>
<div class="page-num">2/8</div>
"""))

# ── P3 指令原文(收藏物本体) ──
PAGES.append(("P3_指令原文", f"""
<style>{BASE_CSS}
.p3-wrap {{ padding:96px 64px 0; }}
.p3-title {{ font-size:40px; font-weight:800; color:{INK}; margin-bottom:12px; }}
.p3-sub {{ font-size:26px; color:{MUTED}; margin-bottom:48px; }}
.p3-card {{ padding:56px 48px; }}
.p3-line {{ font-family:"SF Mono","JetBrains Mono",Menlo,monospace; font-size:34px; line-height:1.9; color:{INK}; }}
.p3-num {{ color:{ACCENT}; font-weight:800; }}
.p3-caption {{ margin-top:40px; text-align:center; font-size:28px; color:{MUTED}; }}
</style>
<div class="p3-wrap">
  <div class="p3-title">📌 可直接抄的指令</div>
  <div class="p3-sub">一字不改可用 · 实测有效</div>
  <div class="p3-card card accent-box">
    <div class="p3-line">找出下面这个计划里<span class="p3-num">最致命的那一个漏洞</span>——就是那个如果不解决、会让整件事直接崩盘的前提或假设。</div>
    <div class="p3-line" style="margin-top:32px">规则:<br>
    <span class="p3-num">①</span> 禁止先夸,禁止说"很有前景""你的优势在于";<br>
    <span class="p3-num">②</span> 只讲最致命的那一个,别罗列小建议凑数;<br>
    <span class="p3-num">③</span> 一句话点破,再用两三句说清为什么;<br>
    <span class="p3-num">④</span> 优先指没被验证、却决定成败的假设。</div>
  </div>
  <div class="p3-caption">↓ 截图保存,粘上你的计划直接用</div>
</div>
<div class="page-num">3/8</div>
"""))

# ── P4 实测对比 ──
PAGES.append(("P4_实测对比", f"""
<style>{BASE_CSS}
.p4-wrap {{ padding:96px 56px 0; }}
.p4-title {{ font-size:40px; font-weight:800; margin-bottom:8px; }}
.p4-caption {{ font-size:22px; color:{MUTED}; margin-bottom:32px; }}
.p4-split {{ display:flex; gap:24px; }}
.p4-col {{ flex:1; padding:32px 28px; height:1400px; overflow:hidden; }}
.p4-col-left {{ background:{SURFACE}; }}
.p4-col-right {{ background:{CANVAS}; border:2px solid {ACCENT}; }}
.p4-col-label {{ font-size:26px; color:{MUTED}; margin-bottom:20px; font-weight:600; }}
.p4-col-right .p4-col-label {{ color:{ACCENT}; }}
.p4-body-small {{ font-size:22px; line-height:1.75; color:{MUTED}; }}
.p4-body-big {{ font-size:34px; line-height:1.7; color:{INK}; font-weight:600; margin-top:24px; }}
.p4-quote {{ color:{ACCENT}; font-weight:800; }}
</style>
<div class="p4-wrap">
  <div class="p4-title">同一个真实计划,两种问法</div>
  <div class="p4-caption">举个例子·虚构计划(辞职做AI代运营)· 真实API输出未删改</div>
  <div class="p4-split">
    <div class="p4-col card p4-col-left">
      <div class="p4-col-label">只问"怎么样"(gpt-5.5)</div>
      <div class="p4-body-small">"我觉得:方向有机会,但现在直接辞职风险偏高。你会AI工具、脚本、剪辑,这是基础能力;但你自己的账号4周涨粉几乎为零……"<br><br>接着展开八个章节:<br>一、这个方案哪里可行?<br>二、主要问题在哪里?<br>三、我建议你先不要辞职……<br>四、你的服务不要叫"AI内容代运营"<br>(附套餐一/二/三定价方案)<br>五、你前期最好不要承诺"涨粉"<br>六、你现在最应该做的5件事<br>七、辞职条件<br>八、你一个月2万的目标怎么拆<br><span style="color:{MUTED}">(全文3000余字,原样保留未删改)</span></div>
    </div>
    <div class="p4-col card p4-col-right">
      <div class="p4-col-label">加"致命漏洞法"后</div>
      <div class="p4-body-big">最致命的漏洞是:<span class="p4-quote">你还没验证"中小商家愿意为你做的AI内容持续按月付费,并且能看到实际获客/成交效果"。</span><br><br>你自己的账号4周涨粉几乎为零……而代运营卖的不是"会用AI、会剪辑、会写脚本",而是<span class="p4-quote">"能帮客户带来曝光、线索或成交"</span>。</div>
    </div>
  </div>
</div>
<div class="page-num">4/8</div>
"""))

# ── P5 为什么有效 ──
PAGES.append(("P5_为什么有效", f"""
<style>{BASE_CSS}
.p5-wrap {{ padding:0 72px; }}
.p5-title {{ font-size:44px; font-weight:800; margin-bottom:56px; }}
.p5-item {{ display:flex; gap:24px; margin-bottom:48px; align-items:flex-start; }}
.p5-num {{ font-size:44px; font-weight:800; color:{ACCENT}; width:64px; flex-shrink:0; }}
.p5-text {{ font-size:34px; line-height:1.6; color:{INK}; }}
.p5-text .weak {{ color:{MUTED}; font-size:26px; display:block; margin-top:8px; }}
</style>
<div class="p5-wrap vgroup">
  <div class="p5-title">为什么 AI 默认只会夸?</div>
  <div class="p5-item">
    <div class="p5-num">01</div>
    <div class="p5-text">训练时倾向"讨好用户",你不显式要求它挑刺,它默认给情绪价值
      <span class="weak">——这是对齐训练的副作用,不是它坏</span></div>
  </div>
  <div class="p5-item">
    <div class="p5-num">02</div>
    <div class="p5-text">"面面俱到"是另一种敷衍——它把所有角度都列一遍,把判断成本甩回给你
      <span class="weak">——3000字里,真正致命的点只占一行</span></div>
  </div>
  <div class="p5-item">
    <div class="p5-num">03</div>
    <div class="p5-text">加约束能治它:只准讲一个最致命的,不许铺开
      <span class="weak">——约束越狠,它越不敢面面俱到</span></div>
  </div>
</div>
<div class="page-num">5/8</div>
"""))

# ── P6 分寸 ──
PAGES.append(("P6_分寸", f"""
<style>{BASE_CSS}
.p6-wrap {{ padding:0 72px; }}
.p6-title {{ font-size:44px; font-weight:800; margin-bottom:64px; }}
.p6-card {{ padding:44px 40px; margin-bottom:36px; display:flex; gap:28px; align-items:center; }}
.p6-icon {{ font-size:64px; }}
.p6-body-title {{ font-size:36px; font-weight:700; margin-bottom:8px; }}
.p6-body-sub {{ font-size:26px; color:{MUTED}; }}
.p6-card-danger {{ border:2px solid {ACCENT}; }}
.p6-card-danger .p6-body-title {{ color:{ACCENT}; }}
.p6-card-safe {{ background:{SURFACE}; }}
.p6-card-safe .p6-body-title {{ color:{SECONDARY}; }}
.p6-quote {{ margin-top:56px; text-align:center; font-size:32px; font-weight:700; color:{INK}; line-height:1.6; }}
</style>
<div class="p6-wrap vgroup">
  <div class="p6-title">什么时候用,什么时候别用</div>
  <div class="p6-card card p6-card-danger">
    <div class="p6-icon">⚠️</div>
    <div><div class="p6-body-title">大赌之前 · 用它挑刺</div>
    <div class="p6-body-sub">辞职 / 借钱 / 签约 / all in 之前</div></div>
  </div>
  <div class="p6-card card p6-card-safe">
    <div class="p6-icon">🔥</div>
    <div><div class="p6-body-title">小赌之前 · 别让它灭火</div>
    <div class="p6-body-sub">低成本可逆的小尝试,需要的是动力不是冷水</div></div>
  </div>
  <div class="p6-quote">"大赌之前用它挑刺,<br>小赌之前别让它灭火。"</div>
</div>
<div class="page-num">6/8</div>
"""))

# ── P7 进阶3招 ──
PAGES.append(("P7_进阶3招", f"""
<style>{BASE_CSS}
.p7-wrap {{ padding:0 64px; }}
.p7-title {{ font-size:44px; font-weight:800; margin-bottom:16px; }}
.p7-sub {{ font-size:26px; color:{MUTED}; margin-bottom:56px; }}
.p7-item {{ padding:36px 32px; margin-bottom:28px; }}
.p7-item-title {{ font-size:32px; font-weight:700; color:{ACCENT}; margin-bottom:12px; }}
.p7-item-body {{ font-size:28px; line-height:1.6; color:{INK}; }}
.p7-item-src {{ font-size:22px; color:{MUTED}; margin-top:10px; }}
</style>
<div class="p7-wrap vgroup">
  <div class="p7-title">进阶 3 招</div>
  <div class="p7-sub">评论区网友的真实土办法 + 硬核变体</div>
  <div class="p7-item card">
    <div class="p7-item-title">① 捏人称法</div>
    <div class="p7-item-body">"别说这是我的计划,当成'我一个朋友'的,毫不留情评价 ta"</div>
    <div class="p7-item-src">用户自发 · 评论区 58 赞</div>
  </div>
  <div class="p7-item card">
    <div class="p7-item-title">② 事前验尸法</div>
    <div class="p7-item-body">"假设一年后这计划彻底失败了,最可能的死因是什么?"</div>
  </div>
  <div class="p7-item card">
    <div class="p7-item-title">③ 第十人法</div>
    <div class="p7-item-body">"如果前九个人都赞成,你必须扮演唱反调的第十人,给出让我哑口无言的理由"</div>
  </div>
</div>
<div class="page-num">7/8</div>
"""))

# ── P8 CTA ──
PAGES.append(("P8_CTA", f"""
<style>{BASE_CSS}
.p8-wrap {{ padding:0; height:{H}px; display:flex; flex-direction:column;
  align-items:center; justify-content:center; text-align:center; padding:0 80px; }}
.p8-q {{ font-size:56px; font-weight:800; line-height:1.5; color:{INK}; margin-bottom:48px; }}
.p8-cta {{ font-size:32px; color:{ACCENT}; font-weight:700; padding:24px 48px;
  border:2px solid {ACCENT}; border-radius:999px; }}
</style>
<div class="p8-wrap">
  <div class="p8-q">你想让 AI 挑<br>哪个计划的刺?</div>
  <div class="p8-cta">评论区聊聊 👇</div>
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
