#!/usr/bin/env python3
"""EP04 连载全长版 · 把 4 个现成场景重定时到真声,输出 ep04f_*.html。

做法: 读 ep04_*.tmpl.html → 替换 __DESK_B64__ 为 ep01f_desk.jpg
→ 用真声对齐后的新 GSAP 时间轴替换 timeline 段(保留 timeline 前的构图代码,如 graph 的建点建线)。
底部 .caption 大字一律不再动画(留给底部跟读字幕层,互斥不叠);land 的 caption 在 top:960 中屏,是转折金句,保留。
"""
from __future__ import annotations
import pathlib, re

T = pathlib.Path(__file__).resolve().parent / "templates"
DESK = "ep01f_desk.jpg"

# ── s1 scatter · 12.98s (拍1 乱的根) ──
SCATTER = """const tl=gsap.timeline();
  tl.fromTo(".term",{opacity:0,y:22},{opacity:1,y:0,duration:.6,ease:"power2.out"},0.1);
  tl.fromTo(".term",{scale:1.0},{scale:1.012,duration:12.8,ease:"sine.inOut"},0);
  // VO"规矩散得到处都是" —— 9 个文件逐条散落
  tl.to("#files .f",{opacity:1,duration:.25,stagger:.55,ease:"power1.out"},4.6);
  tl.fromTo("#find",{opacity:0,y:12},{opacity:1,y:0,duration:.45,ease:"back.out(1.4)"},9.1);
  tl.to("#find",{textShadow:"0 0 26px rgba(229,72,77,.5)",duration:.5,yoyo:true,repeat:2,ease:"sine.inOut"},9.6);
  tl.to({},{duration:1.4},12.9);
  registerTimeline(tl);"""

# ── s3 heads · 15.63s (拍3 三个头儿 ★得意点) ──
HEADS = """const tl=gsap.timeline();
  tl.fromTo(".heads",{scale:1.0},{scale:1.012,duration:15.5,ease:"sine.inOut"},0);
  tl.fromTo("#h1",{opacity:0,x:-30},{opacity:1,x:0,duration:.5,ease:"back.out(1.5)"},0.5);
  tl.fromTo("#s1",{opacity:0,x:14},{opacity:1,x:0,duration:.4,ease:"power2.out"},2.6);
  tl.fromTo("#h2",{opacity:0,x:-30},{opacity:1,x:0,duration:.5,ease:"back.out(1.5)"},4.3);
  tl.fromTo("#s2",{opacity:0,x:14},{opacity:1,x:0,duration:.4,ease:"power2.out"},6.6);
  tl.fromTo("#h3",{opacity:0,x:-30},{opacity:1,x:0,duration:.5,ease:"back.out(1.5)"},8.8);
  tl.fromTo("#s3",{opacity:0,x:14},{opacity:1,x:0,duration:.4,ease:"power2.out"},11.1);
  // 仨人各带一队 —— 三卡齐亮微脉冲
  tl.to(["#h1","#h2","#h3"],{boxShadow:"0 20px 60px rgba(0,0,0,.5),0 0 46px rgba(63,185,80,.32)",duration:.5,yoyo:true,repeat:1,ease:"sine.inOut"},12.9);
  tl.to(["#s1","#s2","#s3"],{scale:1.06,duration:.4,yoyo:true,repeat:1,ease:"sine.inOut",transformOrigin:"right center"},13.0);
  tl.to({},{duration:1.5},15.5);
  registerTimeline(tl);"""

# ── s5 graph · 15.62s (拍5 零孤立点) —— 保留 tmpl 里建点建线代码,只换 timeline ──
GRAPH = """const tl=gsap.timeline();
  tl.fromTo("#svg",{scale:.985},{scale:1.0,duration:2.2,ease:"power2.out"},0.3);
  tl.to(nodeEls,{opacity:1,duration:.25,stagger:.045,ease:"back.out(2)"},0.5);
  tl.to(edgeEls,{opacity:1,duration:.3,stagger:.02},2.6);
  tl.to("#counter",{opacity:1,duration:.4},4.6);
  tl.add(window.countUp("#cn",0,25,{duration:2.4}),4.8);
  tl.add(window.countUp("#ce",0,72,{duration:2.4}),4.8);
  // 枢纽=参谋长+前台(hubs 0/1)高亮
  tl.to([nodeEls[0],nodeEls[1]],{scale:1.5,duration:.5,yoyo:true,repeat:1,ease:"sine.inOut",transformOrigin:"50% 50%"},7.8);
  // "没有,一个,孤立点" —— 全节点绿闪一遍
  tl.to(nodeEls,{fill:"#3fb950",duration:.3,stagger:.02},10.4);
  tl.to("#counter",{scale:1.08,duration:.5,yoyo:true,repeat:1,ease:"sine.inOut",transformOrigin:"50% 50%"},10.6);
  tl.to({},{duration:1.4},15.5);
  registerTimeline(tl);"""

# ── s7 land · 13.47s (拍7 转折落点 ★勾EP05) ──
LAND = """const tl=gsap.timeline();
  tl.fromTo(".stage",{scale:1.0},{scale:1.008,duration:13.4,ease:"sine.inOut"},0);
  // 可它……还是嘴上答应背地敷衍
  tl.fromTo("#bubble",{opacity:0,y:20,scale:.95},{opacity:1,y:0,scale:1,duration:.5,ease:"back.out(1.5)"},2.2);
  // 组织能治乱 / 治不了骗
  tl.to("#verdict",{opacity:1,duration:.1},5.8);
  tl.fromTo(".verdict .lz",{opacity:0,scale:.6},{opacity:1,scale:1,duration:.4,ease:"back.out(2.4)"},5.8);
  tl.fromTo(".verdict .bh",{opacity:0,scale:.6},{opacity:1,scale:1,duration:.4,ease:"back.out(2.4)"},6.5);
  // 转折金句(中屏大字,保留)
  tl.fromTo("#cap",{opacity:0,y:28},{opacity:1,y:0,duration:.55,ease:"power3.out"},7.1);
  tl.fromTo("#cap b",{scale:1.5},{scale:1,duration:.4,ease:"back.out(3)",transformOrigin:"center"},7.6);
  // 下集 EP05 · 4 道锁 勾更
  tl.fromTo("#next",{opacity:0,y:24},{opacity:1,y:0,duration:.5,ease:"back.out(1.4)"},9.9);
  tl.to("#next b",{scale:1.08,duration:.5,yoyo:true,repeat:3,ease:"sine.inOut",transformOrigin:"center"},10.5);
  tl.to({},{duration:1.3},13.4);
  registerTimeline(tl);"""

JOBS = {
    "ep04_scatter": SCATTER,
    "ep04_heads":   HEADS,
    "ep04_graph":   GRAPH,
    "ep04_land":    LAND,
}

for name, script in JOBS.items():
    tmpl = (T / f"{name}.tmpl.html").read_text(encoding="utf-8")
    html = tmpl.replace("__DESK_B64__", DESK)
    if name == "ep04_land":
        # 抬高 EP05 追更卡,避开底部跟读字幕(bottom:132)
        html = html.replace("bottom:210px", "bottom:330px")
    # 只替换 timeline 段(从 const tl=gsap.timeline() 到 registerTimeline(tl);),
    # 保留 timeline 之前的构图代码(如 graph 建点建线)。
    html = re.sub(r"const tl\s*=\s*gsap\.timeline\(\);.*?registerTimeline\(tl\);",
                  script, html, flags=re.S)
    out = T / f"{name.replace('ep04_','ep04f_')}.html"
    out.write_text(html, encoding="utf-8")
    print("wrote", out.name, len(html), "bytes")
