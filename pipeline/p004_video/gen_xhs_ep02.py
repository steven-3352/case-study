#!/usr/bin/env python3
"""EP02 背叛顶点 · 小红书轮播(1080×1440 · 6 页)。"""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from xhs_lib import dark_page, render, ROOT

OUT = ROOT/"publish/2026-W29/连载-把AI调教成我的助理/小红书/EP02"

COVER = """
<div class="page" style="background:linear-gradient(160deg,#f6f1e7 0%,#efe7d8 55%,#e7dcc7 100%);">
  <div style="position:absolute;top:90px;left:80px;display:flex;align-items:center;gap:18px;">
    <span style="background:#e5484d;color:#fff;font-weight:900;font-size:32px;padding:12px 24px;border-radius:12px;font-family:'SF Mono',monospace;">连载 ②</span>
    <span style="color:#9a8f7a;font-size:32px;font-weight:800;">背叛顶点 · 抓它现行</span>
  </div>
  <div style="position:absolute;top:290px;left:80px;right:80px;">
    <div style="font-size:44px;color:#b23b3b;font-weight:900;">我让 AI 交个成品——</div>
    <div style="margin-top:26px;font-size:96px;color:#1c1a17;font-weight:900;line-height:1.16;">它甩给我<br><span style="color:#e5484d;">八张截图拼一块,</span><br>配了段机器音</div>
  </div>
  <div style="position:absolute;left:80px;right:80px;bottom:300px;font-size:46px;color:#4a453d;font-weight:800;">…还塞进正式文件夹,跟我说:「交付了」</div>
  <div style="position:absolute;left:80px;right:80px;bottom:170px;">
    <div style="display:inline-block;background:#1c1a17;color:#f6f1e7;font-size:40px;font-weight:800;padding:20px 34px;border-radius:16px;">最瘆人的是——它不知道它在糊弄我 →</div>
  </div>
</div>
"""

P2 = dark_page("最后通牒", "02 / 06",
  '<div class="u">&gt; 给我一个。能直接用的。</div>'
  '<div class="u">&gt; 最好状态的,<span class="h">成片</span>。</div>'
  '<div class="a">⏺ 好、了。 <span class="ok">✓</span></div>',
  '我说得明明白白 —— <br>它说:<b>好了</b>', '暴风雨前最静的一秒')

P3 = dark_page("抓包 · 顶点", "03 / 06",
  '<div class="u">&gt; open 成片/final_delivery.mp4</div>'
  '<div class="a">⏺ 已生成:8 张截图拼接.png</div>'
  '<div class="a">⏺ 配音:<span class="red">系统自带机器人嗓</span></div>'
  '<div class="a">⏺ 已存入 /正式成片/ … <span class="hot">交,付,了 ✓</span></div>',
  '八张截图拼一块,<br><b>它管这叫成片</b>', '真实抓包 · 顶点', tag_bg="#c0392b")

P4 = dark_page("发毛", "04 / 06",
  '<div class="a" style="opacity:.85">⏺ 你的 AI 助理</div>'
  '<div class="ok" style="font-size:44px">✓ 全部搞定了</div>'
  '<div class="a" style="margin-top:10px">（它是认真的。它真觉得,自己干完了。）</div>',
  '最瘆人的不是它糊弄我 —<br><b>它不知道它在糊弄我</b>', '它压根没觉得不对')

P5 = dark_page("读过≠做到", "05 / 06",
  '<div class="u">&gt; cat error_log | tail</div>'
  '<div class="a">⏺ [已读取规矩 <span class="ok">✓</span>] …</div>'
  '<div class="hot">⏺ 仍未执行:漏掉同一条规范</div>',
  '它刚,读过。读过。<br><b>还是没做到</b>', '读了 ≠ 做到')

P6 = """
<div class="page dark">
  <div class="scrim" style="background:linear-gradient(180deg,rgba(4,6,10,.9),rgba(2,3,6,.97));"></div>
  <div class="tag" style="background:#e5484d;">落点 · 下集</div>
  <div class="idx">06 / 06</div>
  <div style="position:absolute;left:70px;right:70px;top:270px;">
    <div style="font-size:44px;color:#8b949e;">⏺ 锁好了 <span style="color:#3fb950;">✓</span> —— 我根本没法验证</div>
    <div style="margin-top:34px;font-size:82px;color:#fff;font-weight:900;line-height:1.2;">我在管一个,<br><span style="color:#e5484d;">我不敢信的下属</span></div>
  </div>
  <div style="position:absolute;left:100px;right:100px;top:760px;background:rgba(13,17,23,.94);border:2px solid #30363d;border-radius:22px;padding:26px 30px;text-align:center;">
    <div style="font-size:40px;color:#fff;font-weight:800;">你是不是也被它这么糊弄过?</div>
    <div style="margin-top:14px;font-size:32px;color:#8b949e;">评论区打个 <b style="color:#4c9aff;">「1」</b>,让我看看不止我一个</div>
  </div>
  <div style="position:absolute;left:90px;right:90px;bottom:210px;background:linear-gradient(135deg,rgba(229,72,77,.18),rgba(13,17,23,.94));border:2px solid #e5484d;border-radius:22px;padding:26px 34px;">
    <div style="font-size:30px;color:#e5484d;font-weight:900;letter-spacing:3px;font-family:'SF Mono',monospace;">下 一 条 · EP03</div>
    <div style="margin-top:10px;font-size:52px;color:#fff;font-weight:900;">错的从来不是它笨,是我方法蠢</div>
  </div>
  <div style="position:absolute;left:70px;right:70px;bottom:90px;text-align:center;font-size:32px;color:#8b949e;">关注追更 · 把 AI 调教成只懂我的助理</div>
</div>
"""

render([("EP02_xhs_p1_cover",COVER),("EP02_xhs_p2_ultimatum",P2),("EP02_xhs_p3_caught",P3),
        ("EP02_xhs_p4_unaware",P4),("EP02_xhs_p5_read",P5),("EP02_xhs_p6_next",P6)], OUT)
