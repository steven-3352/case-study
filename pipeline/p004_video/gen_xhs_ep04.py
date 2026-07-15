#!/usr/bin/env python3
"""EP04 组织·拆公司 · 小红书轮播(1080×1440 · 6 页)。基调:掌控/得意/有秩序感。"""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from xhs_lib import dark_page, render, ROOT

OUT = ROOT/"publish/2026-W29/连载-把AI调教成我的助理/小红书/EP04"

COVER = """
<div class="page" style="background:linear-gradient(160deg,#eef2f6 0%,#e4ebf1 55%,#d6e2ea 100%);">
  <div style="position:absolute;top:90px;left:80px;display:flex;align-items:center;gap:18px;">
    <span style="background:#2f81f7;color:#fff;font-weight:900;font-size:32px;padding:12px 24px;border-radius:12px;font-family:'SF Mono',monospace;">连载 ④</span>
    <span style="color:#5b7182;font-size:32px;font-weight:800;">组织 · 给 AI 拆公司</span>
  </div>
  <div style="position:absolute;top:300px;left:80px;right:80px;">
    <div style="font-size:44px;color:#2f6fd6;font-weight:900;">管 AI 别把它当一个人——</div>
    <div style="margin-top:26px;font-size:104px;color:#16202a;font-weight:900;line-height:1.16;">我把 AI,<br>拆成了<span style="color:#2f81f7;">一家公司</span></div>
  </div>
  <div style="position:absolute;left:80px;right:80px;bottom:300px;font-size:48px;color:#3a4a56;font-weight:800;">我只跟 <b style="color:#2f81f7;">3 个人</b> 说话,剩下的自己转 🔄</div>
  <div style="position:absolute;left:80px;right:80px;bottom:160px;">
    <div style="display:inline-block;background:#16202a;color:#eef2f6;font-size:40px;font-weight:800;padding:20px 34px;border-radius:16px;">25 节点·72 条线·零孤立点 →</div>
  </div>
</div>
"""

P2 = dark_page("乱的根 → 规矩", "02 / 06",
  '<div class="a">$ ls ~/大脑/规矩/</div>'
  '<div class="u" style="opacity:.7">rules_v1.md  规范.md  约定/  临时/… <span class="red">散一地</span></div>'
  '<div class="a">⏺ 我自己都找不着,它更别提。</div>'
  '<div class="u">&gt; 于是我立一条:<span class="h">只对 3 个头儿说话</span></div>',
  '与其记"哪个文件放啥"<br><b>不如只对 3 个头儿说话</b>', '一条规矩,收住乱', tag_bg="#2f81f7")

P3 = dark_page("三个头儿", "03 / 06",
  '<div class="u"><span class="h">参谋长</span> — 管我是谁、往哪走</div>'
  '<div class="u"><span class="h">前台</span> — 指路 + 记录/归档/体检</div>'
  '<div class="u"><span class="h">项目经理</span> — 管在办项目、派活</div>'
  '<div class="a">⏺ 仨人,各带一队。</div>',
  '我只跟这 <b>3 个头儿</b> 说话', '一句话,自动往下分', tag_bg="#2f81f7")

P4 = dark_page("自动下分", "04 / 06",
  '<div class="u">我 → <span class="h">3 个头儿</span></div>'
  '<div class="a">　　↳ 研究员 · 史官 · 门卫 …自动接活</div>'
  '<div class="ok">✓ 我不用记:谁管谁</div>',
  '我说一句,<b>他们自动派活</b>', '不用记谁管谁', tag_bg="#2f81f7")

P5 = """
<div class="page dark">
  <div class="scrim"></div>
  <div class="tag" style="background:#2f81f7;">零孤立点</div>
  <div class="idx">05 / 06</div>
  <div style="position:absolute;left:70px;right:70px;top:230px;text-align:center;">
    <div style="font-size:40px;color:#8b949e;">它自己长出来的关系图</div>
    <div style="margin-top:20px;display:flex;justify-content:center;gap:40px;">
      <div><div style="font-size:96px;color:#2f81f7;font-weight:900;">25</div><div style="font-size:32px;color:#c9d1d9;">节点</div></div>
      <div style="align-self:center;font-size:60px;color:#30363d;">·</div>
      <div><div style="font-size:96px;color:#3fb950;font-weight:900;">72</div><div style="font-size:32px;color:#c9d1d9;">条线</div></div>
    </div>
    <div style="margin-top:16px;font-size:34px;color:#8b949e;">枢纽 = 参谋长 + 前台</div>
  </div>
  <div style="position:absolute;left:70px;right:70px;bottom:330px;text-align:center;font-size:84px;color:#fff;font-weight:900;line-height:1.2;">没有,<span style="color:#3fb950;">一个孤立点</span></div>
  <div style="position:absolute;left:70px;right:70px;bottom:160px;text-align:center;font-size:44px;color:#c9d1d9;font-weight:800;">乱文件夹 → 真变成了一支队伍</div>
</div>
"""

P6 = """
<div class="page dark">
  <div class="scrim" style="background:linear-gradient(180deg,rgba(6,10,16,.86),rgba(4,8,14,.96));"></div>
  <div class="tag" style="background:#e5484d;">落点 · 下集</div>
  <div class="idx">06 / 06</div>
  <div style="position:absolute;left:70px;right:70px;top:290px;">
    <div style="font-size:46px;color:#3fb950;font-weight:800;">✓ 团队,是搭好了</div>
    <div style="margin-top:24px;font-size:52px;color:#c9d1d9;font-weight:700;">可它……还是嘴上答应、背地敷衍</div>
    <div style="margin-top:36px;font-size:80px;color:#fff;font-weight:900;line-height:1.2;">组织能治「乱」,<br><span style="color:#e5484d;">治不了「骗」</span></div>
  </div>
  <div style="position:absolute;left:90px;right:90px;bottom:210px;background:linear-gradient(135deg,rgba(229,72,77,.18),rgba(13,17,23,.94));border:2px solid #e5484d;border-radius:22px;padding:26px 34px;">
    <div style="font-size:30px;color:#e5484d;font-weight:900;letter-spacing:3px;font-family:'SF Mono',monospace;">下 一 条 · EP05</div>
    <div style="margin-top:10px;font-size:56px;color:#fff;font-weight:900;">▶ 给它上 4 道绕不过去的锁</div>
  </div>
  <div style="position:absolute;left:70px;right:70px;bottom:90px;text-align:center;font-size:32px;color:#8b949e;">关注追更 · 把 AI 调教成只懂我的助理</div>
</div>
"""

render([("EP04_xhs_p1_cover",COVER),("EP04_xhs_p2_rule",P2),("EP04_xhs_p3_heads",P3),
        ("EP04_xhs_p4_auto",P4),("EP04_xhs_p5_graph",P5),("EP04_xhs_p6_next",P6)], OUT)
