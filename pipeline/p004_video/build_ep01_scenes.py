#!/usr/bin/env python3
"""EP01 连载全长版 · 把 3 个现成场景重定时到真声,输出 ep01f_*.html。

做法: 读 *.tmpl.html(可读小文件) → 替换 __DESK_B64__ 为本地 desk jpg 相对路径
→ 用真声对齐后的新 GSAP 时间轴替换 <script>...</script>。
底部大字 caption 一律不再动画(留给底部跟读字幕层,互斥不叠)。
"""
from __future__ import annotations
import pathlib, re

T = pathlib.Path(__file__).resolve().parent / "templates"
DESK = "ep01f_desk.jpg"

# 通用落章块(与原模板一致,参数化起点 S 与旋转方向)
def stamp_block(S, rot, xp):
    sign = "-" if rot < 0 else ""
    dirs = "[[0,-150],[120,-80],[140,60],[40,150],[-110,90],[-140,-40]]"
    return f"""
  const S={S};
  tl.set("#stamp", {{ opacity:0, scale:3.6, rotation:{rot}, yPercent:-170, xPercent:{xp} }}, S);
  tl.to("#stamp", {{ opacity:1, duration:0.12 }}, S);
  tl.to("#stamp", {{ scale:1.06, rotation:{int(rot/2.6)}, yPercent:4, xPercent:0, duration:0.34, ease:"power4.in" }}, S+0.12);
  tl.to("#stamp", {{ scale:0.9, yPercent:8, duration:0.08, ease:"power2.out" }}, S+0.46);
  tl.to("#stamp", {{ scale:1.0, yPercent:0, duration:0.28, ease:"back.out(2.2)" }}, S+0.54);
  tl.to("#term", {{ x:"+=9", duration:0.045, repeat:6, yoyo:true, ease:"none" }}, S+0.46);
  tl.set("#term", {{ x:0 }}, S+0.46+0.045*7);
  const dirs={dirs};
  dirs.forEach((d,i)=>{{ tl.fromTo("#ink"+i,{{opacity:0.9,scale:0.2,x:0,y:0}},{{opacity:0,scale:1.5,x:d[0],y:d[1],duration:0.5,ease:"power3.out"}},S+0.47); }});
  tl.to("#stamp", {{ scale:1.035, duration:0.12, yoyo:true, repeat:1, ease:"sine.inOut" }}, S+0.95);
"""

# ── s1 chatlog · 26.19s (拍1 当初多信 0.2–~12 / 拍2 失忆 12.9–) ──
CHATLOG = f"""
  const tl = gsap.timeline();
  tl.fromTo("#term", {{ scale:1.0 }}, {{ scale:1.014, duration:26.0, ease:"sine.inOut" }}, 0);
  // 拍1 · 亲手写进记忆
  tl.set("#l1", {{ opacity:1 }}, 0.2);
  tl.add(window.typewriter("#type1", "记住:出片先过质量门,不能跳。这是死规矩。", {{ stagger:0.05 }}), 0.2);
  tl.fromTo("#lai", {{ opacity:0,y:22,scale:0.98 }}, {{ opacity:1,y:0,scale:1,duration:0.45,ease:"back.out(1.5)" }}, 2.0);
  tl.fromTo(".ok", {{ scale:0.4,opacity:0 }}, {{ scale:1,opacity:1,duration:0.4,ease:"back.out(3)" }}, 2.5);
  tl.to(".ok", {{ boxShadow:"0 0 22px rgba(63,185,80,.6)", duration:0.5, yoyo:true, repeat:1 }}, 3.0);
  // 拍2 · 第二天换会话(VO 12.9s)
  tl.to("#div", {{ opacity:1, duration:0.25 }}, 12.9);
  tl.fromTo("#div .l", {{ scaleX:0 }}, {{ scaleX:1, duration:0.5, ease:"power2.out" }}, 12.9);
  tl.set("#l2", {{ opacity:1 }}, 13.7);
  tl.add(window.typewriter("#type2", "按之前那条规矩来", {{ stagger:0.06 }}), 13.7);
  tl.to(["#l1","#lai","#div","#l2"], {{ opacity:0.32, duration:0.5, ease:"power2.inOut" }}, 15.2);
  tl.fromTo("#punch", {{ opacity:0,y:26,scale:0.99 }}, {{ opacity:1,y:0,scale:1,duration:0.5,ease:"back.out(1.4)" }}, 15.4);
  tl.to("#blink", {{ opacity:0, duration:0.28, repeat:34, yoyo:true, ease:"steps(1)" }}, 16.0);
  {stamp_block(16.7, -34, 20)}
  tl.to({{}}, {{ duration:1.0 }}, 26.0);
  registerTimeline(tl);
"""

# ── s2 gitscar · 11.59s (拍3 文档乱) ──
GITSCAR = f"""
  const tl = gsap.timeline();
  tl.fromTo("#term", {{ scale:1.0 }}, {{ scale:1.012, duration:11.5, ease:"sine.inOut" }}, 0);
  tl.add(window.typewriter("#cmd", "git log | grep 收敛\\\\|清全尸\\\\|一事一处", {{ stagger:0.045 }}), 0.3);
  const N=6, base=2.0, step=0.52;
  for(let i=0;i<N;i++){{ tl.fromTo("#c"+i, {{opacity:0,y:-12}}, {{opacity:(i===0?1:0.62),y:0,duration:0.3,ease:"power2.out"}}, base+i*step); }}
  const F=base+N*step+0.3;
  tl.to("#c0", {{ boxShadow:"0 0 40px rgba(229,72,77,0.35)", scale:1.03, duration:0.4, ease:"power2.out" }}, F);
  tl.to("#c0", {{ scale:1.0, duration:0.4, ease:"back.out(2)" }}, F+0.4);
  {stamp_block("F+0.9", 30, -20)}
  tl.to({{}}, {{ duration:1.0 }}, 11.4);
  registerTimeline(tl);
"""

# ── s3 triquiz · 17.63s (拍4 活在过期) ──
TRIQUIZ = f"""
  const tl = gsap.timeline();
  tl.fromTo("#term", {{ scale:1.0 }}, {{ scale:1.013, duration:17.5, ease:"sine.inOut" }}, 0);
  tl.to("#badge", {{ opacity:1, duration:0.3 }}, 0.3);
  const qs=["#q0","#q1","#q2"], base=1.6, step=3.0;
  qs.forEach((q,i)=>{{
    const at=base+i*step;
    tl.fromTo(q, {{opacity:0,y:20,x:-10}}, {{opacity:1,y:0,x:0,duration:0.4,ease:"back.out(1.6)"}}, at);
    const em=document.querySelector(q+" em");
    if(em) tl.fromTo(q+" em", {{scale:1.9}}, {{scale:1,duration:0.32,ease:"back.out(3.5)"}}, at+0.22);
  }});
  const R=base+3*step;
  tl.fromTo("#rep", {{opacity:0,y:16}}, {{opacity:0.6,y:0,duration:0.4,ease:"power2.out"}}, R);
  tl.fromTo("#rep em", {{scale:1.6}}, {{scale:1,duration:0.3,ease:"back.out(3)"}}, R+0.2);
  {stamp_block("R+1.4", -32, 18)}
  tl.to({{}}, {{ duration:1.0 }}, 17.4);
  registerTimeline(tl);
"""

JOBS = {
    "ep01_chatlog": CHATLOG,
    "ep01_gitscar": GITSCAR,
    "ep01_triquiz": TRIQUIZ,
}

for name, script in JOBS.items():
    tmpl = (T / f"{name}.tmpl.html").read_text(encoding="utf-8")
    html = tmpl.replace("__DESK_B64__", DESK)
    # 替换 <script> ... </script>(最后一个,含时间轴)
    html = re.sub(r"<script>\s*const tl = gsap\.timeline\(\);.*?</script>",
                  f"<script>{script}</script>", html, flags=re.S)
    out = T / f"{name.replace('ep01_','ep01f_')}.html"
    out.write_text(html, encoding="utf-8")
    print("wrote", out.name, len(html), "bytes")
