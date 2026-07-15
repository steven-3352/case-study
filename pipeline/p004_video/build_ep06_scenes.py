#!/usr/bin/env python3
"""EP06 连载全长版 · 把现成场景皮肤重定时到真声,输出 ep06f_*.html。

复刻 EP05 做法:读 ep06_*.tmpl.html → 替换 __DESK_B64__ 为 ep01f_desk.jpg
→ 用真声对齐后的新 GSAP 时间轴替换 timeline 段;必要处注入 CSS 覆盖。

场景来源:
  stance  ← ep06_stance   (拍1 立场:翻车才是真的)
  crash1  ← ep06_crash12  (只显 #c1,隐藏 #c2 与内嵌 .fix —— 修法各有独立场景)
  crash2  ← ep06_crash12  (只显 #c2,隐藏 #c1 与内嵌 .fix)
  crash3  ← ep06_crash3   (★金句 航母送快递,caption 提为大字停划)
land 单独建 ep06f_land.html(不复用 ep06_land,其 repos/EP04边界 已移到 s7_boundary)。
底部 .caption 大字:与底部跟读字幕(bottom:132)互斥 —— 除 crash3 金句抬到中屏保留外,其余不动画(留给字幕)。
"""
from __future__ import annotations
import pathlib, re

T = pathlib.Path(__file__).resolve().parent / "templates"
DESK = "ep01f_desk.jpg"

# ── s1 stance · 10.15s (拍1 别人发炸裂我发翻车 · in-scene 0.20 起) ──
STANCE = """const tl=gsap.timeline();
  tl.fromTo(".stage",{scale:1.0},{scale:1.01,duration:10.0,ease:"sine.inOut"},0);
  // 三条"炸裂"标题划掉
  ["#f1","#f2","#f3"].forEach((f,i)=>{
    tl.fromTo(f,{opacity:0},{opacity:.85,duration:.3},0.4+i*0.55);
    tl.fromTo("#st"+(i+1),{width:0},{width:"108%",duration:.3,ease:"power2.in"},0.62+i*0.55);
  });
  // 我发"翻车实录"
  tl.fromTo("#real",{opacity:0,scale:.6,rotation:-6},{opacity:1,scale:1,rotation:-3,duration:.5,ease:"back.out(2)"},3.4);
  tl.to("#real .tag",{scale:1.06,duration:.5,yoyo:true,repeat:2,ease:"sine.inOut",transformOrigin:"center"},4.6);
  // "真有用的部分恰恰是它翻过的车" —— 再拉一次注意
  tl.to("#real",{rotation:-1.5,duration:.6,yoyo:true,repeat:1,ease:"sine.inOut"},7.2);
  tl.to({},{duration:1.2},10.0);
  registerTimeline(tl);"""

# ── s2 crash1 · 14.47s (拍2 盲签 · 只显 c1) ──
CRASH1 = """const tl=gsap.timeline();
  tl.fromTo(".stage",{scale:1.0},{scale:1.01,duration:14.3,ease:"sine.inOut"},0);
  tl.fromTo("#c1",{opacity:0,y:28,scale:.97},{opacity:1,y:0,scale:1,duration:.55,ease:"back.out(1.3)"},0.4);
  tl.fromTo("#c1 .no",{opacity:0,scale:1.6},{opacity:1,scale:1,duration:.4,ease:"back.out(3)",transformOrigin:"left center"},0.7);
  tl.fromTo("#c1 .t",{opacity:0,x:-14},{opacity:1,x:0,duration:.45,ease:"power2.out"},1.5);
  tl.fromTo("#c1 .d",{opacity:0,y:14},{opacity:1,y:0,duration:.5,ease:"power2.out"},3.6);
  // "把我挡在门外" —— 卡片轻震
  tl.to("#c1",{keyframes:[{x:-8},{x:8},{x:-5},{x:0}],duration:.3},7.0);
  tl.to("#c1",{boxShadow:"0 20px 60px rgba(0,0,0,.5),0 0 46px rgba(229,72,77,.3)",duration:.5,yoyo:true,repeat:1},7.3);
  // "只能……盲签" —— punch
  tl.to("#c1 .d b",{color:"#ff5a5f",scale:1.14,duration:.5,yoyo:true,repeat:3,ease:"sine.inOut",transformOrigin:"center"},11.0);
  tl.to({},{duration:1.2},14.3);
  registerTimeline(tl);"""

# ── s4 crash2 · 11.21s (拍4 拿琐事问 · 只显 c2) ──
CRASH2 = """const tl=gsap.timeline();
  tl.fromTo(".stage",{scale:1.0},{scale:1.01,duration:11.0,ease:"sine.inOut"},0);
  tl.fromTo("#c2",{opacity:0,y:28,scale:.97},{opacity:1,y:0,scale:1,duration:.55,ease:"back.out(1.3)"},0.4);
  tl.fromTo("#c2 .no",{opacity:0,scale:1.6},{opacity:1,scale:1,duration:.4,ease:"back.out(3)",transformOrigin:"left center"},0.7);
  tl.fromTo("#c2 .t",{opacity:0,x:-14},{opacity:1,x:0,duration:.45,ease:"power2.out"},1.2);
  tl.fromTo("#c2 .d",{opacity:0,y:14},{opacity:1,y:0,duration:.5,ease:"power2.out"},4.0);
  // "屁大的事" —— t 抖一下强调无语
  tl.to("#c2 .t",{scale:1.06,duration:.4,yoyo:true,repeat:2,ease:"sine.inOut",transformOrigin:"left center"},6.6);
  // "踩了我立的规矩" —— 卡片红光
  tl.to("#c2",{boxShadow:"0 20px 60px rgba(0,0,0,.5),0 0 46px rgba(229,72,77,.3)",duration:.5,yoyo:true,repeat:1},8.2);
  tl.to({},{duration:1.0},11.0);
  registerTimeline(tl);"""

# ── s6 crash3 · 15.67s (拍6 ★金句 航母送快递 · 有 .term) ──
CRASH3 = """const tl=gsap.timeline();
  tl.fromTo(".term",{scale:1.0},{scale:1.012,duration:15.4,ease:"sine.inOut"},0);
  tl.fromTo("#l0",{opacity:0,y:12},{opacity:1,y:0,duration:.4},1.6);   // 为了把大脑可视化
  tl.fromTo("#l1",{opacity:0,y:12},{opacity:1,y:0,duration:.4},3.4);   // docker 部署
  tl.fromTo("#l2",{opacity:0,y:12},{opacity:1,y:0,duration:.4},6.8);   // 全跑通了图看上了
  tl.fromTo("#l3",{opacity:0,y:16,scale:.96},{opacity:1,y:0,scale:1,duration:.45,ease:"back.out(1.4)"},9.2); // 一拍脑袋
  // ★金句大字停划:航母,送快递(caption 提到中屏,砸出)
  tl.fromTo("#cap",{opacity:0,scale:2.1,y:-30},{opacity:1,scale:1,y:0,duration:.5,ease:"power4.in"},10.4);
  tl.to("#cap",{scale:1.09,duration:.12,yoyo:true,repeat:1,transformOrigin:"center"},10.95);
  tl.to(".term",{x:"+=8",duration:.05,repeat:5,yoyo:true},10.4);
  // 整条清退全删
  tl.fromTo("#l4",{opacity:0,x:-14},{opacity:1,x:0,duration:.45,ease:"power2.out"},12.8);
  tl.to("#l4",{boxShadow:"0 0 40px rgba(229,72,77,.32)",scale:1.02,duration:.4,yoyo:true,repeat:1},13.2);
  tl.to({},{duration:1.4},15.4);
  registerTimeline(tl);"""

# out_name: (tmpl_name, script, extra_head_style, html_replacements[(old,new),...])
JOBS = {
    "ep06_stance":  (STANCE, "", []),
    "ep06_crash1":  (CRASH1,
        "#c2{display:none!important} #c1 .fix{display:none!important} #c1{top:520px!important}", []),
    "ep06_crash2":  (CRASH2,
        "#c1{display:none!important} #c2 .fix{display:none!important} #c2{top:520px!important}", []),
    "ep06_crash3":  (CRASH3,
        "#cap{bottom:auto!important;top:1200px!important;font-size:120px!important;letter-spacing:6px!important}",
        [('<div class="caption" id="cap">全,<b>删</b>。</div>',
          '<div class="caption" id="cap">航母,<b>送快递</b></div>')]),
}

# crash1/crash2 都源自 ep06_crash12
SRC_TMPL = {
    "ep06_stance": "ep06_stance",
    "ep06_crash1": "ep06_crash12",
    "ep06_crash2": "ep06_crash12",
    "ep06_crash3": "ep06_crash3",
}

for name, (script, extra_style, repls) in JOBS.items():
    src = SRC_TMPL[name]
    tmpl = (T / f"{src}.tmpl.html").read_text(encoding="utf-8")
    html = tmpl.replace("__DESK_B64__", DESK)
    for old, new in repls:
        html = html.replace(old, new)
    if extra_style:
        html = html.replace("</style>", f"\n  {extra_style}\n</style>", 1)
    html = re.sub(r"const tl\s*=\s*gsap\.timeline\(\);.*?registerTimeline\(tl\);",
                  script, html, flags=re.S)
    out = T / f"{name.replace('ep06_','ep06f_')}.html"
    out.write_text(html, encoding="utf-8")
    print("wrote", out.name, len(html), "bytes")
