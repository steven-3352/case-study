#!/usr/bin/env python3
"""EP07 复刻·收官 · 小红书轮播(1080×1440 · 6 页)。基调:交底/笃定/克制诚恳,不炫成果。"""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from xhs_lib import dark_page, render, ROOT

OUT = ROOT/"publish/2026-W29/连载-把AI调教成我的助理/小红书/EP07"

COVER = """
<div class="page" style="background:linear-gradient(160deg,#eef1ec 0%,#e3e9df 55%,#d5ddcd 100%);">
  <div style="position:absolute;top:90px;left:80px;display:flex;align-items:center;gap:18px;">
    <span style="background:#2f7a3f;color:#fff;font-weight:900;font-size:32px;padding:12px 24px;border-radius:12px;font-family:'SF Mono',monospace;">连载 ⑦ · 收官</span>
    <span style="color:#5f7359;font-size:32px;font-weight:800;">复刻 · 交底</span>
  </div>
  <div style="position:absolute;top:300px;left:80px;right:80px;">
    <div style="font-size:44px;color:#2f7a3f;font-weight:900;">想自己造一个?</div>
    <div style="margin-top:26px;font-size:112px;color:#16221a;font-weight:900;line-height:1.14;">5 步复刻,<br><span style="color:#2f7a3f;">坑我都替你<br>标好了</span></div>
  </div>
  <div style="position:absolute;left:80px;right:80px;bottom:290px;font-size:46px;color:#3a4a3e;font-weight:800;">这套 AI 助理你能抄 —— 但我先说丑话</div>
  <div style="position:absolute;left:80px;right:80px;bottom:160px;">
    <div style="display:inline-block;background:#16221a;color:#eef1ec;font-size:40px;font-weight:800;padding:20px 34px;border-radius:16px;">复刻清单 + 软肋,一起交给你 →</div>
  </div>
</div>
"""

P2 = dark_page("回望", "02 / 06",
  '<div class="u">被它骗 → 想通<span class="h">机械 &gt; 自觉</span></div>'
  '<div class="u">→ 搭团队 → 上锁 → 翻了一路车</div>'
  '<div class="ok">→ 现在,它总算像个能用的助理了</div>'
  '<div class="a">你要也想搞一个 —— 来,我把路给你铺平。</div>',
  '一路走过来,<br><b>它终于能用了</b>', '从被骗到能用', tag_bg="#2f7a3f")

P3 = dark_page("复刻 5 步", "03 / 06",
  '<div class="u"><span class="h">①</span> 常驻核心文件:写清你是谁,开工自动注入</div>'
  '<div class="u"><span class="h">②</span> 铁律+固化流程+体检脚本,提交前自动跑</div>'
  '<div class="u"><span class="h">③</span> 关键纪律用 hooks 落地(注入/阻断/裁判),逃生门先建先测</div>'
  '<div class="u"><span class="h">④</span> 结构人格化成组织　<span class="h">⑤</span> 只报告不擅改,留能自救的口子</div>',
  '5 步,<b>照着抄</b>', '核心文件 · 铁律 · hooks · 组织 · 自救口', tag_bg="#2f7a3f")

P4 = dark_page("效果(克制)", "04 / 06",
  '<div class="ok">✓ 体检全绿</div>'
  '<div class="ok">✓ 结构零孤立</div>'
  '<div class="ok">✓ 一天十几次提交,零脏改</div>'
  '<div class="u">就……这些。是「<span class="ok">绿</span>」—— <span class="h">不是「炸裂」</span>。</div>',
  '是「绿」<br><b>不是「炸裂」</b>', '收官不炫成果', tag_bg="#2f7a3f")

P5 = dark_page("丑话 · 局限", "05 / 06",
  '<div class="a">· 只是雏形,实战时长以「天」计</div>'
  '<div class="a">· 行为约束没有 100%,裁判会漏</div>'
  '<div class="a">· hooks 吃平台,换环境得重搭</div>'
  '<div class="a">· 单人单机纯文字,多 agent/语音都还没做</div>'
  '<div class="u">—— 是<span class="h">路线</span>,不是现状。</div>',
  '丑话说前面:<br><b>这只是雏形</b>', '4 条局限,不回避', tag_bg="#8a7150")

P6 = """
<div class="page dark">
  <div class="scrim" style="background:linear-gradient(180deg,rgba(6,10,7,.88),rgba(4,8,5,.97));"></div>
  <div class="tag" style="background:#2f7a3f;">自警 · 收官</div>
  <div class="idx">06 / 06</div>
  <div style="position:absolute;left:64px;right:64px;top:270px;">
    <div style="font-size:40px;color:#8b949e;font-weight:700;">我做这一整个连载,就守一条:</div>
    <div style="margin-top:30px;font-size:72px;color:#fff;font-weight:900;line-height:1.28;">写成<span style="color:#3fb950;">真实记录</span>,是内容;<br>写成<span style="color:#e5484d;">效果炸裂</span>,就是元叙事。</div>
  </div>
  <div style="position:absolute;left:90px;right:90px;bottom:250px;text-align:center;">
    <div style="font-size:44px;color:#c9d1d9;font-weight:800;">我不求它多牛,也不求这条爆。</div>
    <div style="margin-top:16px;font-size:52px;color:#fff;font-weight:900;">求的是,真能一起造的人。</div>
  </div>
  <div style="position:absolute;left:70px;right:70px;bottom:120px;text-align:center;font-size:56px;color:#3fb950;font-weight:900;">你也在折腾这个?评论区,见。</div>
</div>
"""

render([("EP07_xhs_p1_cover",COVER),("EP07_xhs_p2_recap",P2),("EP07_xhs_p3_steps",P3),
        ("EP07_xhs_p4_effect",P4),("EP07_xhs_p5_limits",P5),("EP07_xhs_p6_creed",P6)], OUT)
