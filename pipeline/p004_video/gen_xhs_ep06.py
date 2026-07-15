#!/usr/bin/env python3
"""EP06 翻车·上锁翻车现场 · 小红书轮播(1080×1440 · 6 页)。基调:自嘲/坦荡/松弛,翻车✗修复✓对比。"""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from xhs_lib import dark_page, render, ROOT

OUT = ROOT/"publish/2026-W29/连载-把AI调教成我的助理/小红书/EP06"

COVER = """
<div class="page" style="background:linear-gradient(160deg,#f5ede2 0%,#eee1cd 55%,#e6d5ba 100%);">
  <div style="position:absolute;top:90px;left:80px;display:flex;align-items:center;gap:18px;">
    <span style="background:#d1671f;color:#fff;font-weight:900;font-size:32px;padding:12px 24px;border-radius:12px;font-family:'SF Mono',monospace;">连载 ⑥</span>
    <span style="color:#8a7150;font-size:32px;font-weight:800;">翻车 · 全是现场</span>
  </div>
  <div style="position:absolute;top:300px;left:80px;right:80px;">
    <div style="font-size:44px;color:#c0651c;font-weight:900;">别人发「炸裂」,我发翻车——</div>
    <div style="margin-top:26px;font-size:108px;color:#1c1a17;font-weight:900;line-height:1.14;">我做 AI 助理<br>第一天,<span style="color:#d1671f;">翻了 3 次车</span></div>
  </div>
  <div style="position:absolute;left:80px;right:80px;bottom:300px;font-size:46px;color:#4a453d;font-weight:800;">今天全给你看,包括最蠢那次 🚢</div>
  <div style="position:absolute;left:80px;right:80px;bottom:160px;">
    <div style="display:inline-block;background:#1c1a17;color:#f5ede2;font-size:40px;font-weight:800;padding:20px 34px;border-radius:16px;">真有用的,恰恰是它翻过的车 →</div>
  </div>
</div>
"""

P2 = dark_page("翻车 ①", "02 / 06",
  '<div class="u"><span class="red">✗ 盲签</span> —— 我刚上的收工锁,坑了我自己</div>'
  '<div class="a">它置了闸,让我「去看那份报告」</div>'
  '<div class="a">可那闸,把我<span class="red">挡在门外</span> —— 我啥也看不了</div>'
  '<div class="ok">✓ 修:置闸必须把摘要贴脸上,别让我去别处找</div>',
  '第一次实战,<b>就把我锁门外</b>', '翻车①盲签 → 摘要贴脸', tag_bg="#d1671f")

P3 = dark_page("翻车 ②", "03 / 06",
  '<div class="a">⏺ 它:「要不要记一句日志?」</div>'
  '<div class="u">屁大的事,也来烦我一句 —— <span class="red">踩了我立的规矩</span></div>'
  '<div class="ok">✓ 当场立规 + 加 Stop 裁判做机械后盾</div>'
  '<div class="hot">EP05 那个裁判 —— 就是这么被逼出来的</div>',
  '拿琐事烦我?<b>裁判由此而生</b>', '翻车②→EP05 裁判的来历', tag_bg="#d1671f")

P4 = dark_page("翻车 ③ · 最蠢", "04 / 06",
  '<div class="a">为「把大脑可视化」,我部署了整套开源笔记系统</div>'
  '<div class="u">容器 · 镜像 · 导入 —— 全跑通了,图我都看上了</div>'
  '<div class="hot">然后我一拍脑袋:航母……送快递 🚢</div>'
  '<div class="red">整条,清退,全删。</div>',
  '航母,<b>送快递</b>', '最蠢那次 · 全集金句', tag_bg="#c0392b")

P5 = dark_page("边界救命", "05 / 06",
  '<div class="a">还好 —— 它在<span class="h">平行仓库</span>里</div>'
  '<div class="u">(就是 EP04 我写死的那条边界)</div>'
  '<div class="ok">✓ 删地盘,一了百了;大脑只摘一条门牌</div>'
  '<div class="u">那条边界,<span class="h">真救了我一命</span>。</div>',
  '写死的那条边界<br><b>真救了我一命</b>', '回扣 EP04 · 平行仓库', tag_bg="#3fb950")

P6 = """
<div class="page dark">
  <div class="scrim" style="background:linear-gradient(180deg,rgba(10,8,4,.86),rgba(6,5,3,.96));"></div>
  <div class="tag" style="background:#e5484d;">落点 · 下集</div>
  <div class="idx">06 / 06</div>
  <div style="position:absolute;left:70px;right:70px;top:300px;">
    <div style="font-size:56px;color:#c9d1d9;font-weight:800;">翻车不可怕 ——</div>
    <div style="margin-top:22px;font-size:80px;color:#fff;font-weight:900;line-height:1.2;">可怕的是<span style="color:#e5484d;">不留痕</span></div>
    <div style="margin-top:30px;font-size:44px;color:#8b949e;font-weight:700;">每翻一次,立一条规矩、刻一块墓碑,系统就硬一分</div>
  </div>
  <div style="position:absolute;left:90px;right:90px;bottom:210px;background:linear-gradient(135deg,rgba(63,185,80,.16),rgba(13,17,23,.94));border:2px solid #3fb950;border-radius:22px;padding:26px 34px;">
    <div style="font-size:30px;color:#3fb950;font-weight:900;letter-spacing:3px;font-family:'SF Mono',monospace;">收 官 · EP07</div>
    <div style="margin-top:10px;font-size:52px;color:#fff;font-weight:900;">▶ 复刻 5 步,坑我全给你标好</div>
  </div>
  <div style="position:absolute;left:70px;right:70px;bottom:90px;text-align:center;font-size:32px;color:#8b949e;">关注追更 · 把 AI 调教成只懂我的助理</div>
</div>
"""

render([("EP06_xhs_p1_cover",COVER),("EP06_xhs_p2_crash1",P2),("EP06_xhs_p3_crash2",P3),
        ("EP06_xhs_p4_crash3",P4),("EP06_xhs_p5_boundary",P5),("EP06_xhs_p6_next",P6)], OUT)
