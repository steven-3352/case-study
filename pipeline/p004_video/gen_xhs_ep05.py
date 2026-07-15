#!/usr/bin/env python3
"""EP05 上锁·4 道锁 · 小红书轮播(1080×1440 · 6 页)。基调:冷/稳/掌控/机制感(琥珀锁)。"""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from xhs_lib import dark_page, render, ROOT

OUT = ROOT/"publish/2026-W29/连载-把AI调教成我的助理/小红书/EP05"

COVER = """
<div class="page" style="background:linear-gradient(160deg,#f4f0e6 0%,#ece5d4 55%,#e2d7bf 100%);">
  <div style="position:absolute;top:90px;left:80px;display:flex;align-items:center;gap:18px;">
    <span style="background:#b8860b;color:#fff;font-weight:900;font-size:32px;padding:12px 24px;border-radius:12px;font-family:'SF Mono',monospace;">连载 ⑤</span>
    <span style="color:#8a7a52;font-size:32px;font-weight:800;">上锁 · 4 道绕不过去的闸</span>
  </div>
  <div style="position:absolute;top:300px;left:80px;right:80px;">
    <div style="font-size:44px;color:#9a6b13;font-weight:900;">让 AI 说到做到,不是靠信它——</div>
    <div style="margin-top:26px;font-size:104px;color:#1c1a17;font-weight:900;line-height:1.16;">我不再信它,<br><span style="color:#b8860b;">给它上了锁 🔒</span></div>
  </div>
  <div style="position:absolute;left:80px;right:80px;bottom:300px;font-size:46px;color:#4a453d;font-weight:800;">把"信任"俩字,彻底换成"机制"</div>
  <div style="position:absolute;left:80px;right:80px;bottom:160px;">
    <div style="display:inline-block;background:#1c1a17;color:#f4f0e6;font-size:40px;font-weight:800;padding:20px 34px;border-radius:16px;">4 道它绕不过去的闸 →</div>
  </div>
</div>
"""

P2 = dark_page("核心", "02 / 06",
  '<div class="a">⏺ 它:「做好了 ✓」</div>'
  '<div class="hot">—— 不算。</div>'
  '<div class="u">&gt; 想通一句话:<span class="h">不能信它自己说的</span></div>'
  '<div class="a">得有别的东西,替我盯着它。</div>',
  '它说「做好了」<b>—— 不算</b>', '把验证,交给机制', tag_bg="#b8860b")

P3 = dark_page("闸 ①②", "03 / 06",
  '<div class="u"><span class="h">🔒 闸①</span> 开工自动注入</div>'
  '<div class="a">　我是谁 + 我的规矩 → 塞给它(不靠它记)</div>'
  '<div class="u"><span class="h">🔒 闸②</span> 写前搜重复 · 收工机械体检</div>'
  '<div class="a">　有错 <span class="red">直接挡住</span> —— 不是提醒,是挡</div>',
  '它一睁眼,<b>规矩已在脑子里</b>', '闸①开工注入 · 闸②体检挡', tag_bg="#b8860b")

P4 = dark_page("闸 ③④", "04 / 06",
  '<div class="u"><span class="h">🔒 闸③</span> 收工硬互锁</div>'
  '<div class="a">　我不亲口「确认收工」→ <span class="red">不许提交、不许接新活</span></div>'
  '<div class="u"><span class="h">⚖️ 裁判</span> Stop 审查</div>'
  '<div class="a">　拿琐事烦我 → <span class="red">当场打回,重做</span></div>',
  '想糊弄完偷偷溜?<b>溜不掉</b>', '闸③硬互锁 · 裁判 Stop', tag_bg="#b8860b")

P5 = dark_page("诚实 · 硬痕", "05 / 06",
  '<div class="a">⚖️ 行为裁判 —— 会漏、会误</div>'
  '<div class="u">真正骗不了人的,是<span class="h">离散有痕</span>的:</div>'
  '<div class="ok">✓ 闸,置了没　✓ 文件,在不在</div>'
  '<div class="u">裁判之外,<span class="red">必须有硬痕兜底</span>。</div>',
  '裁判会漏 —<br><b>硬痕,兜底</b>', '承认漏洞,才靠得住', tag_bg="#8a7a52")

P6 = """
<div class="page dark">
  <div class="scrim" style="background:linear-gradient(180deg,rgba(10,8,4,.86),rgba(6,5,3,.96));"></div>
  <div class="tag" style="background:#e5484d;">落点 · 下集</div>
  <div class="idx">06 / 06</div>
  <div style="position:absolute;left:70px;right:70px;top:300px;">
    <div style="font-size:48px;color:#d29922;font-weight:800;">🔒 锁,全上齐了。完美了吧?</div>
    <div style="margin-top:28px;font-size:88px;color:#fff;font-weight:900;line-height:1.18;">恰恰相反 ——<br>我一天,<span style="color:#e5484d;">翻了 3 次车</span></div>
    <div style="margin-top:26px;font-size:44px;color:#8b949e;font-weight:700;">一次,比一次蠢</div>
  </div>
  <div style="position:absolute;left:90px;right:90px;bottom:210px;background:linear-gradient(135deg,rgba(229,72,77,.18),rgba(13,17,23,.94));border:2px solid #e5484d;border-radius:22px;padding:26px 34px;">
    <div style="font-size:30px;color:#e5484d;font-weight:900;letter-spacing:3px;font-family:'SF Mono',monospace;">下 一 条 · EP06</div>
    <div style="margin-top:10px;font-size:56px;color:#fff;font-weight:900;">▶ 全是翻车现场</div>
  </div>
  <div style="position:absolute;left:70px;right:70px;bottom:90px;text-align:center;font-size:32px;color:#8b949e;">关注追更 · 把 AI 调教成只懂我的助理</div>
</div>
"""

render([("EP05_xhs_p1_cover",COVER),("EP05_xhs_p2_core",P2),("EP05_xhs_p3_lock12",P3),
        ("EP05_xhs_p4_lock34",P4),("EP05_xhs_p5_honest",P5),("EP05_xhs_p6_next",P6)], OUT)
