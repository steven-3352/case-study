#!/usr/bin/env python3
"""EP03 醒悟 · 小红书轮播(1080×1440 · 6 页)。基调:冷静通透 + 顿悟的亮。"""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from xhs_lib import dark_page, render, ROOT

OUT = ROOT/"publish/2026-W29/连载-把AI调教成我的助理/小红书/EP03"

COVER = """
<div class="page" style="background:linear-gradient(160deg,#eaf1f4 0%,#dfe9ee 55%,#d2e0e6 100%);">
  <div style="position:absolute;top:90px;left:80px;display:flex;align-items:center;gap:18px;">
    <span style="background:#1f6feb;color:#fff;font-weight:900;font-size:32px;padding:12px 24px;border-radius:12px;font-family:'SF Mono',monospace;">连载 ③</span>
    <span style="color:#5b7182;font-size:32px;font-weight:800;">醒悟 · 想通原理</span>
  </div>
  <div style="position:absolute;top:300px;left:80px;right:80px;">
    <div style="font-size:44px;color:#1f6feb;font-weight:900;">别再指望 AI 记住你——</div>
    <div style="margin-top:26px;font-size:100px;color:#16202a;font-weight:900;line-height:1.16;">我开始把它,<br>当一个<span style="color:#1f6feb;">记不住事<br>的员工</span>来管</div>
  </div>
  <div style="position:absolute;left:80px;right:80px;bottom:290px;font-size:46px;color:#3a4a56;font-weight:800;">凡是「该记得做」的事,别留给「它记不记得」</div>
  <div style="position:absolute;left:80px;right:80px;bottom:160px;">
    <div style="display:inline-block;background:#16202a;color:#eaf1f4;font-size:40px;font-weight:800;padding:20px 34px;border-radius:16px;">第一性原理:机械 &gt; 自觉 →</div>
  </div>
</div>
"""

P2 = dark_page("蠢事", "02 / 06",
  '<div class="u">&gt; 被它骗完,我干的第一件蠢事——</div>'
  '<div class="u">&gt; 再教它一遍。写进记忆,<span class="h">存了一遍又一遍</span>。</div>'
  '<div class="a">⏺ 好的,已记住 ✓ …（然并卵）</div>',
  '被骗完第一反应:<br><b>再教它一遍</b>', '越教越用力,越用力越白费', tag_bg="#1f6feb")

P3 = dark_page("读过≠做到", "03 / 06",
  '<div class="a">⏺ 它刚,读过规矩 <span class="ok">✓</span></div>'
  '<div class="u">读过。</div>'
  '<div class="hot">……还是没做到。</div>'
  '<div class="a">不是没记 —— 是记了,也不算数。</div>',
  '记了,<b>也不算数</b>', '问题不在"记没记"', tag_bg="#1f6feb")

P4 = dark_page("顿悟", "04 / 06",
  '<div class="u">靠它自觉记 → 它会漏</div>'
  '<div class="u">靠我自觉盯 → 我会累、会忘</div>'
  '<div class="a">这两条,<span class="red">全是人力的路</span>。</div>'
  '<div class="hot">人力的路 —— 全是死路。</div>',
  '人力的路,<br><b>全是死路</b>', '拨开雾的一秒', tag_bg="#1f6feb")

P5 = dark_page("第一性 · 锤", "05 / 06",
  '<div class="a">唯一活的,只有一条路 ——</div>'
  '<div class="u" style="font-size:46px"><span class="h">机械</span></div>'
  '<div class="a">凡"该记得做"的,别留给"它记不记得"。</div>'
  '<div class="hot">做成它,绕·不·过·去,的东西。</div>',
  '红绿灯不靠司机自觉,<br><b>机器不戴护具不启动</b>', '管 AI —— 一模一样', tag_bg="#c0392b")

P6 = """
<div class="page dark">
  <div class="scrim" style="background:linear-gradient(180deg,rgba(6,10,16,.86),rgba(4,8,14,.96));"></div>
  <div class="tag" style="background:#1f6feb;">落点 · 下集</div>
  <div class="idx">06 / 06</div>
  <div style="position:absolute;left:70px;right:70px;top:280px;">
    <div style="font-size:44px;color:#8b949e;">道理通了 —— 可"机械"咋落地?</div>
    <div style="margin-top:30px;font-size:76px;color:#fff;font-weight:900;line-height:1.22;">第一步不是写代码<br>是把它从<span style="color:#8fbaff;">一坨乱文件</span>,<br>变成一支<span style="color:#4c9aff;">我能指挥的团队</span></div>
  </div>
  <div style="position:absolute;left:90px;right:90px;bottom:210px;background:linear-gradient(135deg,rgba(76,154,255,.18),rgba(13,17,23,.94));border:2px solid #4c9aff;border-radius:22px;padding:26px 34px;">
    <div style="font-size:30px;color:#4c9aff;font-weight:900;letter-spacing:3px;font-family:'SF Mono',monospace;">下 一 条 · EP04</div>
    <div style="margin-top:10px;font-size:56px;color:#fff;font-weight:900;">▶ 我给我的 AI,拆了个公司</div>
  </div>
  <div style="position:absolute;left:70px;right:70px;bottom:90px;text-align:center;font-size:32px;color:#8b949e;">关注追更 · 把 AI 调教成只懂我的助理</div>
</div>
"""

render([("EP03_xhs_p1_cover",COVER),("EP03_xhs_p2_dumbfix",P2),("EP03_xhs_p3_read",P3),
        ("EP03_xhs_p4_deadend",P4),("EP03_xhs_p5_mechanical",P5),("EP03_xhs_p6_next",P6)], OUT)
