#!/usr/bin/env python3
"""EP05 连载全长版 · 把 3 个现成场景重定时到真声,输出 ep05f_*.html。

做法: 读 ep05_*.tmpl.html → 替换 __DESK_B64__ 为 ep01f_desk.jpg
→ 用真声对齐后的新 GSAP 时间轴替换 timeline 段。
底部 .caption 大字一律不再动画(留给底部跟读字幕层,互斥不叠);
  seed/land 底部 caption 交给字幕,不再单独出;
  honest 的 caption 在 top:1120 中屏,是"行为靠裁判·底靠硬痕"金句,保留;
  land 的 caption 是勾EP06 追更卡,抬到 bottom:330 避开字幕,保留。
"""
from __future__ import annotations
import pathlib, re

T = pathlib.Path(__file__).resolve().parent / "templates"
DESK = "ep01f_desk.jpg"

# ── s1 seed · 11.83s (b1 不能信它自己说的 · in-scene 0.20 起) ──
SEED = """const tl=gsap.timeline();
  tl.fromTo(".term",{scale:1.0},{scale:1.013,duration:11.6,ease:"sine.inOut"},0);
  // "它说做好了" —— 冷开题
  tl.fromTo("#said",{opacity:0,y:14},{opacity:1,y:0,duration:.45},0.4);
  tl.fromTo("#said .g",{scale:1.5},{scale:1,duration:.4,ease:"back.out(3)",transformOrigin:"center"},2.6);
  tl.to("#said",{opacity:.5,duration:.4},5.4);   // 淡下 —— "不算"
  // "得有别的东西替我盯着它" —— 铁律浮出
  tl.fromTo("#rule",{opacity:0,y:22},{opacity:1,y:0,duration:.5,ease:"power2.out"},6.2);
  tl.fromTo(".rule .q b",{color:"#ffd7d9"},{color:"#e5484d",duration:.3,stagger:.25},8.4);
  tl.to(".rule",{boxShadow:"0 0 44px rgba(229,72,77,.3)",duration:.5,yoyo:true,repeat:1},9.0);
  // 底部大字 caption 交给字幕层,不再动画
  tl.to({},{duration:1.2},11.6);
  registerTimeline(tl);"""

# ── s4 honest · 8.02s (b6 ★诚信锚点 放下身段 · in-scene 0.20 起) ──
HONEST = """const tl=gsap.timeline();
  tl.fromTo(".stage",{scale:1.0},{scale:1.008,duration:7.9,ease:"sine.inOut"},0);
  // "但我得说句实话——" 放慢
  tl.fromTo("#honest",{opacity:0,y:12},{opacity:1,y:0,duration:.45},0.3);
  // 行为裁判(会漏会误) vs 离散有痕(骗不了人)
  tl.fromTo("#soft",{opacity:0,x:-30},{opacity:1,x:0,duration:.5,ease:"back.out(1.4)"},2.0);
  tl.fromTo("#hard",{opacity:0,x:30},{opacity:1,x:0,duration:.5,ease:"back.out(1.4)"},3.8);
  tl.to("#hard",{boxShadow:"0 30px 80px rgba(0,0,0,.6),0 0 50px rgba(63,185,80,.4)",duration:.6},4.6);
  // 金句:行为靠裁判 · 底靠硬痕(中屏,保留)
  tl.fromTo("#cap",{opacity:0,y:26},{opacity:1,y:0,duration:.55,ease:"power3.out"},5.6);
  tl.to("#cap .g",{scale:1.1,duration:.5,yoyo:true,repeat:1,ease:"sine.inOut",transformOrigin:"center"},6.3);
  tl.to({},{duration:1.0},7.9);
  registerTimeline(tl);"""

# ── s5 land · 10.92s (b7 落点自嘲翻车 勾EP06 · in-scene 0.20 起) ──
LAND = """const tl=gsap.timeline();
  tl.fromTo(".stage",{scale:1.0},{scale:1.008,duration:10.7,ease:"sine.inOut"},0);
  // 锁全上齐了
  ["#k1","#k2","#k3","#k4"].forEach((k,i)=>tl.fromTo(k,{opacity:0,scale:0,rotation:-15},{opacity:1,scale:1,rotation:0,duration:.35,ease:"back.out(2.2)"},0.4+i*0.28));
  tl.fromTo("#perfect",{opacity:0,y:14},{opacity:1,y:0,duration:.4},2.0);
  // 恰恰相反 —— 自嘲翻车
  tl.fromTo("#crash",{opacity:0,scale:2,y:-40},{opacity:1,scale:1,y:0,duration:.45,ease:"power4.in"},3.3);
  tl.to("#crash",{scale:1.06,duration:.1,yoyo:true,repeat:1},3.75);
  tl.to(".locks,#perfect",{x:"+=8",duration:.05,repeat:5,yoyo:true},3.3);
  // 追更卡:一天翻了3次车(勾EP06)
  tl.fromTo("#cap",{opacity:0,y:28},{opacity:1,y:0,duration:.5,ease:"power3.out"},5.2);
  tl.fromTo("#cap b",{scale:1.6},{scale:1,duration:.4,ease:"back.out(3)",transformOrigin:"center"},5.7);
  tl.to("#cap b",{scale:1.08,duration:.5,yoyo:true,repeat:4,ease:"sine.inOut",transformOrigin:"center"},6.4);
  tl.to({},{duration:1.0},10.7);
  registerTimeline(tl);"""

JOBS = {
    "ep05_seed":   SEED,
    "ep05_honest": HONEST,
    "ep05_land":   LAND,
}

for name, script in JOBS.items():
    tmpl = (T / f"{name}.tmpl.html").read_text(encoding="utf-8")
    html = tmpl.replace("__DESK_B64__", DESK)
    if name == "ep05_land":
        # 抬高 EP06 追更卡,避开底部跟读字幕(bottom:132)
        html = html.replace("bottom:230px", "bottom:340px")
        # 追更卡标签改 EP06
        html = html.replace('<span class="next">下 集</span>', '<span class="next">EP06 · 下集</span>')
    html = re.sub(r"const tl\s*=\s*gsap\.timeline\(\);.*?registerTimeline\(tl\);",
                  script, html, flags=re.S)
    out = T / f"{name.replace('ep05_','ep05f_')}.html"
    out.write_text(html, encoding="utf-8")
    print("wrote", out.name, len(html), "bytes")
