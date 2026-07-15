#!/usr/bin/env python3
"""EP01 小红书图文轮播 · 6 页 1080×1440(3:4)。

浅色封面(停划)+ 终端证据页(与视频同皮肤)。复用真声全长版内容:
钩子 → 症状①失忆 → 症状②文档乱 → 症状③活在过期 → 共鸣互动 → 落点勾EP02。
用法: ./.venv/bin/python pipeline/p004_video/gen_xhs_ep01.py
"""
from __future__ import annotations
import pathlib
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[2]
DESK = (ROOT/"pipeline/p004_video/templates/ep01f_desk.jpg").resolve().as_uri()
OUT = ROOT/"publish/2026-W29/连载-把AI调教成我的助理/小红书/EP01"
OUT.mkdir(parents=True, exist_ok=True)
W, H = 1080, 1440

BASE = f"""
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
:root{{ --ink:#e6edf3; --muted:#8b949e; --green:#3fb950; --amber:#d29922; --red:#e5484d; --blue:#4c9aff; }}
html,body{{ width:{W}px; height:{H}px; overflow:hidden;
  font-family:"PingFang SC","Heiti SC","SF Mono",sans-serif; }}
.page{{ position:relative; width:{W}px; height:{H}px; overflow:hidden; }}
/* 深色证据页 */
.dark{{ background-image:url("{DESK}"); background-size:cover; background-position:center 58%; color:var(--ink); }}
.dark .scrim{{ position:absolute; inset:0; background:
  linear-gradient(180deg, rgba(6,9,14,.86) 0%, rgba(6,9,14,.62) 32%, rgba(6,9,14,.66) 60%, rgba(6,9,14,.94) 100%); }}
.tag{{ position:absolute; top:70px; left:70px; font-size:34px; font-weight:900; letter-spacing:2px;
  color:#fff; background:var(--red); padding:14px 26px; border-radius:14px; font-family:"SF Mono",monospace; }}
.idx{{ position:absolute; top:78px; right:70px; font-size:30px; color:var(--muted); font-family:"SF Mono",monospace; letter-spacing:2px; }}
.term{{ position:absolute; left:70px; right:70px; top:230px;
  background:rgba(13,17,23,.94); border-radius:22px; padding:0 0 26px;
  box-shadow:0 30px 80px rgba(0,0,0,.6),0 0 0 1px rgba(255,255,255,.05); }}
.bar{{ height:70px; background:rgba(22,27,34,.95); border-radius:20px 20px 0 0; display:flex; align-items:center; gap:12px; padding:0 26px; }}
.bar i{{ width:20px; height:20px; border-radius:50%; }} .bar .r{{background:#ff5f56}} .bar .y{{background:#febc2e}} .bar .g{{background:#27c93f}}
.bar .p{{ color:var(--muted); font-size:26px; margin-left:12px; font-family:"SF Mono",monospace; }}
.termbody{{ padding:30px 34px 6px; font-size:37px; line-height:1.5; font-family:"SF Mono","PingFang SC",monospace; }}
.termbody .u{{ color:var(--ink); }} .termbody .a{{ color:var(--muted); }}
.termbody .ok{{ color:var(--green); font-weight:800; }} .termbody .cursor{{ color:var(--green); }}
.termbody .hot{{ color:#ffb3b5; font-weight:800; }} .termbody .h{{ color:var(--amber); }}
.termbody .red{{ color:var(--red); font-weight:900; font-style:normal; }}
.headline{{ position:absolute; left:70px; right:70px; bottom:150px; font-size:74px; font-weight:900;
  line-height:1.24; letter-spacing:1px; color:#fff; text-shadow:0 4px 26px rgba(0,0,0,.9); }}
.headline b{{ color:var(--red); }} .headline .amb{{ color:var(--amber); }}
.foot{{ position:absolute; left:70px; bottom:70px; font-size:28px; color:var(--muted); letter-spacing:2px; }}
</style>
"""

# ---- 各页 body ----
COVER = f"""
<div class="page" style="background:linear-gradient(160deg,#f6f1e7 0%,#efe7d8 55%,#e7dcc7 100%);">
  <div style="position:absolute;top:90px;left:80px;display:flex;align-items:center;gap:18px;">
    <span style="background:#e5484d;color:#fff;font-weight:900;font-size:32px;padding:12px 24px;border-radius:12px;font-family:'SF Mono',monospace;">连载 ①</span>
    <span style="color:#9a8f7a;font-size:32px;font-weight:800;">把 AI 调教成只懂我的助理</span>
  </div>
  <div style="position:absolute;top:300px;left:80px;right:80px;">
    <div style="font-size:44px;color:#b23b3b;font-weight:900;letter-spacing:1px;">我把规矩,一个字一个字写进它脑子——</div>
    <div style="margin-top:28px;font-size:104px;color:#1c1a17;font-weight:900;line-height:1.16;">第二天它问我:<br><span style="color:#e5484d;">「你说的规矩,<br>是啥?」</span></div>
  </div>
  <div style="position:absolute;left:80px;right:80px;bottom:250px;">
    <div style="display:inline-block;background:#1c1a17;color:#f6f1e7;font-size:40px;font-weight:800;padding:20px 34px;border-radius:16px;">AI 三个日常通病 · 你也天天中招 →</div>
  </div>
  <div style="position:absolute;left:80px;bottom:110px;font-size:30px;color:#9a8f7a;letter-spacing:2px;">失忆 · 规矩散一地 · 活在上个月</div>
</div>
"""

def dark_page(tag, idx, term_html, headline, foot):
    return f"""
<div class="page dark">
  <div class="scrim"></div>
  <div class="tag">{tag}</div>
  <div class="idx">{idx}</div>
  <div class="term">
    <div class="bar"><i class="r"></i><i class="y"></i><i class="g"></i><span class="p">claude ~/my-ai-assistant</span></div>
    <div class="termbody">{term_html}</div>
  </div>
  <div class="headline">{headline}</div>
  <div class="foot">{foot}</div>
</div>
"""

P2 = dark_page("症状 ①", "02 / 06",
  '<div class="u">&gt; 记住:出片先过质量门,这是死规矩。</div>'
  '<div class="a">⏺ 好的,已写入记忆 <span class="ok">✓ Memory updated</span></div>'
  '<div class="a" style="opacity:.6">── new session · 第二天 ──</div>'
  '<div class="hot">⏺ 你说的「规矩」…是指哪条?</div>',
  '换个会话,<b>它就跟没见过我一样</b>', '换会话 = 失忆')

P3 = dark_page("症状 ②", "03 / 06",
  '<div class="a">$ git log --oneline · ~/大脑</div>'
  '<div class="u"><span class="h">21e325f</span> <span class="red">收敛</span>三统一 — 各归一处</div>'
  '<div class="u" style="opacity:.7"><span class="h">d30e58e</span> <span class="red">清全尸</span> — 删两具化石</div>'
  '<div class="u" style="opacity:.6"><span class="h">c4be45a</span> KM 重写(一事一处)</div>'
  '<div class="u" style="opacity:.5"><span class="h">6883b47</span> 清重复 + 近似重复硬闸</div>',
  '规矩它自己写得满地,<br><b>它更找不着</b>', '规矩散一地 · 谁都找不着')

P4 = dark_page("症状 ③", "04 / 06",
  '<div class="u">&gt; 你确定是按系统的规范在做吗?<span class="a" style="font-size:26px"> 07-04</span></div>'
  '<div class="u">&gt; 为什么<span class="red">又</span>出现漏掉规范?<span class="a" style="font-size:26px"> 07-04</span></div>'
  '<div class="u">&gt; 系统的核心宗旨<span class="red">又</span>忘记了吗?<span class="a" style="font-size:26px"> 07-04</span></div>'
  '<div class="a">⏺ 抱歉,我<span class="hot">又</span>漏了…这次一定改。</div>',
  '过期的当圣旨,<br><span class="amb">活像活在上个月</span>', '同一天 · 同一个错教八百遍')

P5 = f"""
<div class="page dark">
  <div class="scrim"></div>
  <div class="tag" style="background:#4c9aff;">互 动</div>
  <div class="idx">05 / 06</div>
  <div style="position:absolute;left:70px;right:70px;top:300px;text-align:center;">
    <div style="font-size:44px;color:#c9d1d9;font-weight:800;">失忆 · 乱 · 活在过期</div>
    <div style="margin-top:34px;font-size:96px;color:#fff;font-weight:900;line-height:1.18;">你是不是,<br><span style="color:#ffd27a;">也天天这样?</span></div>
  </div>
  <div style="position:absolute;left:110px;right:110px;top:820px;background:rgba(13,17,23,.94);border:2px solid #30363d;border-radius:24px;padding:30px 34px;box-shadow:0 26px 70px rgba(0,0,0,.6);">
    <div style="display:flex;align-items:center;gap:20px;">
      <div style="width:64px;height:64px;border-radius:50%;background:linear-gradient(135deg,#4c9aff,#3fb950);display:grid;place-items:center;font-size:36px;">🙋</div>
      <div style="flex:1;background:#0d1117;border:1px solid #30363d;border-radius:14px;padding:18px 22px;font-size:42px;color:#fff;font-weight:800;">我也是</div>
      <div style="background:#4c9aff;color:#fff;font-weight:900;font-size:34px;border-radius:14px;padding:18px 26px;">发送</div>
    </div>
    <div style="margin-top:18px;text-align:center;font-size:32px;color:#8b949e;">评论区扣俩字 → <b style="color:#4c9aff;">我也是</b></div>
  </div>
  <div style="position:absolute;left:70px;right:70px;bottom:150px;text-align:center;font-size:46px;color:#c9d1d9;font-weight:800;">不是你不会用 — <span style="color:#3fb950;">是它天生这样</span></div>
</div>
"""

P6 = f"""
<div class="page dark">
  <div class="scrim" style="background:linear-gradient(180deg,rgba(4,6,10,.9),rgba(2,3,6,.97));"></div>
  <div class="tag" style="background:#e5484d;">下 集</div>
  <div class="idx">06 / 06</div>
  <div style="position:absolute;left:70px;right:70px;top:280px;">
    <div style="font-size:44px;color:#8b949e;font-weight:700;">这些…顶多让我头疼</div>
    <div style="margin-top:24px;font-size:56px;color:#cfe3ff;font-weight:800;">真正让我 <span style="color:#8fbaff;">脊背发凉</span> 的是——</div>
    <div style="margin-top:40px;font-size:88px;color:#fff;font-weight:900;line-height:1.18;">它还会,<span style="color:#e5484d;">假装,做到了</span></div>
  </div>
  <div style="position:absolute;left:90px;right:90px;bottom:230px;background:linear-gradient(135deg,rgba(229,72,77,.18),rgba(13,17,23,.94));border:2px solid #e5484d;border-radius:24px;padding:30px 36px;">
    <div style="font-size:30px;color:#e5484d;font-weight:900;letter-spacing:3px;font-family:'SF Mono',monospace;">下 一 条 · EP02</div>
    <div style="margin-top:12px;font-size:58px;color:#fff;font-weight:900;">▶ 我抓它,现行</div>
  </div>
  <div style="position:absolute;left:70px;right:70px;bottom:90px;text-align:center;font-size:34px;color:#8b949e;">关注追更 · 一条条把 AI 调教成只懂我的助理</div>
</div>
"""

PAGES = [("p1_cover", COVER), ("p2_amnesia", P2), ("p3_scatter", P3),
         ("p4_stale", P4), ("p5_interact", P5), ("p6_next", P6)]

with sync_playwright() as p:
    b = p.chromium.launch(headless=True, args=["--font-render-hinting=none"])
    ctx = b.new_context(viewport={"width":W,"height":H}, device_scale_factor=1, locale="zh-CN")
    pg = ctx.new_page()
    for pid, body in PAGES:
        pg.set_content(f"<!DOCTYPE html><html><head><meta charset='utf-8'>{BASE}</head><body>{body}</body></html>")
        pg.wait_for_timeout(180)
        out = OUT/f"EP01_xhs_{pid}.png"
        pg.screenshot(path=str(out), clip={"x":0,"y":0,"width":W,"height":H})
        print("✓", out.name)
    b.close()
print("→", OUT)
