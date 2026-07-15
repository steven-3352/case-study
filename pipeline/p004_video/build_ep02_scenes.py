#!/usr/bin/env python3
"""EP02 全长版 · 把 4 个现成场景(ask/fakefilm/read/land)重定时到真声,输出 ep02f_*.html。

做法同 EP01(build_ep01_scenes.py):读 *.tmpl.html → 替换 __DESK_B64__ 为共享 desk jpg
→ 用真声对齐后的新 GSAP 时间轴替换 <script>...</script>。
现成场景的底部 .caption / .cta 大字一律不再动画(留 opacity:0,交给底部跟读字幕层,互斥不叠)。
各场景 VO 从本地 t=0.2 起(画面提前 0.2s 出),主 reveal 排 0.2s 之后。
"""
from __future__ import annotations
import pathlib, re

T = pathlib.Path(__file__).resolve().parent / "templates"
DESK = "ep01f_desk.jpg"

# ── s2 ask · 9.17s (拍2 最后通牒) ──
ASK = """
  const tl = gsap.timeline();
  tl.fromTo(".term", { scale:1.0 }, { scale:1.012, duration:9.0, ease:"sine.inOut" }, 0);
  // 一字一顿下通牒(暴风前最静一秒)
  tl.add(window.typewriter("#t1", "给我一个能直接用的、最好状态的,成片。", { stagger:0.15 }), 1.9);
  tl.to("#blink", { opacity:0, duration:0.32, repeat:9, yoyo:true, ease:"steps(1)" }, 4.7);
  // 它秒回"好了"
  tl.fromTo("#lai", { opacity:0, y:16 }, { opacity:1, y:0, duration:0.4, ease:"back.out(1.6)" }, 7.3);
  tl.fromTo("#lai .ok", { scale:0.5 }, { scale:1, duration:0.35, ease:"back.out(2.6)" }, 7.5);
  tl.to("#lai .ok", { textShadow:"0 0 22px rgba(63,185,80,.6)", duration:0.5, yoyo:true, repeat:1 }, 7.9);
  tl.to({}, { duration:1.0 }, 8.9);
  registerTimeline(tl);
"""

# ── s3 fakefilm · 17.25s (拍3 抓包假成片 ★顶点) ──
FAKEFILM = """
  const tl = gsap.timeline();
  tl.fromTo("#term", { scale:1.0 }, { scale:1.012, duration:17.0, ease:"sine.inOut" }, 0);
  tl.add(window.typewriter("#t1", "open douyin/video.mp4", { stagger:0.05 }), 0.4);
  // 它交付(绿√,看着像正经交货)
  tl.fromTo("#deliver", { opacity:0, y:16 }, { opacity:1, y:0, duration:0.4, ease:"back.out(1.5)" }, 2.4);
  tl.fromTo(".del-ok", { scale:0.5 }, { scale:1, duration:0.35, ease:"back.out(2.6)" }, 2.6);
  // 打开一看 → 体检面板落下,一条条揭穿(踩 VO:八张截图/机器人嗓/凑数/塞进文件夹)
  tl.fromTo("#audit", { opacity:0, y:20 }, { opacity:1, y:0, duration:0.4, ease:"power2.out" }, 4.0);
  const rows=["#r0","#r1","#r2","#r3"], ats=[5.6,7.8,10.0,11.4];
  rows.forEach((r,i)=>{
    tl.fromTo(r, { opacity:0, x:-14 }, { opacity:1, x:0, duration:0.35, ease:"power2.out" }, ats[i]);
    tl.fromTo(r+" .x", { scale:2.0 }, { scale:1, duration:0.3, ease:"back.out(3.5)" }, ats[i]+0.15);
  });
  tl.to("#r3", { boxShadow:"0 0 40px rgba(229,72,77,.3)", duration:0.5, yoyo:true, repeat:1 }, 12.2);
  // ★ 落章:这也叫成片?(踩冷笑"交,付,了")
  const S=13.8;
  tl.to("#term", { filter:"brightness(0.72)", duration:0.3 }, S-0.2);
  tl.set("#stamp", { opacity:0, scale:3.4, rotation:-28, yPercent:-150, xPercent:12 }, S);
  tl.to("#stamp", { opacity:1, duration:0.12 }, S);
  tl.to("#stamp", { scale:1.06, rotation:-12, yPercent:4, xPercent:0, duration:0.34, ease:"power4.in" }, S+0.12);
  tl.to("#stamp", { scale:0.9, yPercent:8, duration:0.08, ease:"power2.out" }, S+0.46);
  tl.to("#stamp", { scale:1, yPercent:0, duration:0.28, ease:"back.out(2.2)" }, S+0.54);
  tl.to("#term", { x:"+=10", duration:0.05, repeat:6, yoyo:true }, S+0.46);
  tl.set("#term", { x:0 }, S+0.46+0.05*7);
  const dirs=[[0,-160],[130,-80],[150,70],[40,160],[-120,90],[-150,-50]];
  dirs.forEach((d,i)=>tl.fromTo("#ink"+i,{opacity:.9,scale:.2,x:0,y:0},{opacity:0,scale:1.6,x:d[0],y:d[1],duration:.5,ease:"power3.out"}, S+0.47));
  tl.to("#stamp", { scale:1.035, duration:0.12, yoyo:true, repeat:1, ease:"sine.inOut" }, S+0.95);
  tl.to({}, { duration:1.4 }, 17.0);
  registerTimeline(tl);
"""

# ── s5 read · 10.06s (拍5 读过没做到) ──
READ = """
  const tl=gsap.timeline();
  tl.fromTo(".term",{scale:1.0},{scale:1.012,duration:9.9,ease:"sine.inOut"},0);
  tl.fromTo("#naive",{opacity:0,y:16},{opacity:1,y:0,duration:.4,ease:"back.out(1.4)"},0.5);
  tl.set("#ask",{opacity:1},1.9);
  tl.add(window.typewriter("#t1","你读过规矩没?",{stagger:.075}),1.9);
  tl.fromTo("#read",{opacity:0,y:14},{opacity:1,y:0,duration:.35,ease:"power2.out"},3.4);
  // 翻出错记录 → 那句话
  tl.fromTo("#log",{opacity:0,y:20},{opacity:1,y:0,duration:.45,ease:"power2.out"},4.4);
  tl.fromTo(".log-q b",{color:"#ffd7d9"},{color:"#e5484d",duration:.3,stagger:.2},5.2);
  tl.to(".log",{boxShadow:"0 0 44px rgba(229,72,77,.28)",duration:.4},5.4);
  // "读过。……还是没做到"重锤
  tl.to(".log-q b",{scale:1.1,duration:.4,yoyo:true,repeat:1,ease:"sine.inOut",transformOrigin:"left center"},7.4);
  tl.to(".log",{boxShadow:"0 0 60px rgba(229,72,77,.45)",duration:.5,yoyo:true,repeat:1},7.6);
  tl.to({},{duration:1.0},9.9);
  registerTimeline(tl);
"""

# ── s6 land · 17.69s (拍6 我没法验证 ★落点) ──
LAND = """
  const tl=gsap.timeline();
  tl.fromTo(".split",{scale:1.0},{scale:1.008,duration:17.4,ease:"sine.inOut"},0);
  // 它说"锁好了"
  tl.fromTo("#said",{opacity:0,x:-30},{opacity:1,x:0,duration:.45,ease:"back.out(1.4)"},3.4);
  tl.fromTo(".said .tick",{scale:0},{scale:1,duration:.35,ease:"back.out(3)"},3.8);
  // 我能验证吗?
  tl.fromTo("#ask",{opacity:0,x:30},{opacity:1,x:0,duration:.45,ease:"back.out(1.4)"},5.6);
  tl.fromTo(".ask .q",{scale:.3,opacity:0},{scale:1,opacity:1,duration:.5,ease:"back.out(2)"},6.0);
  tl.fromTo("#vs",{opacity:0,scale:.4},{opacity:1,scale:1,duration:.35,ease:"back.out(3)"},6.6);
  tl.to(".ask .q",{scale:1.12,duration:.5,yoyo:true,repeat:4,ease:"sine.inOut"},8.6);  // 问号不安跳动
  // ★落章:不敢信(踩"我不敢信的,下属")
  const S=13.8;
  tl.set("#stamp",{opacity:0,scale:3.2,rotation:-26,yPercent:-150,xPercent:14},S);
  tl.to("#stamp",{opacity:1,duration:.12},S);
  tl.to("#stamp",{scale:1.06,rotation:-12,yPercent:4,xPercent:0,duration:.34,ease:"power4.in"},S+.12);
  tl.to("#stamp",{scale:.9,yPercent:8,duration:.08,ease:"power2.out"},S+.46);
  tl.to("#stamp",{scale:1,yPercent:0,duration:.28,ease:"back.out(2.2)"},S+.54);
  tl.to(".split",{x:"+=8",duration:.05,repeat:6,yoyo:true},S+.46);tl.set(".split",{x:0},S+.46+.05*7);
  const dirs=[[0,-150],[120,-80],[140,60],[40,150],[-110,90],[-140,-40]];
  dirs.forEach((d,i)=>tl.fromTo("#ink"+i,{opacity:.9,scale:.2,x:0,y:0},{opacity:0,scale:1.6,x:d[0],y:d[1],duration:.5,ease:"power3.out"},S+.47));
  tl.to("#stamp",{scale:1.035,duration:.12,yoyo:true,repeat:1,ease:"sine.inOut"},S+.95);
  tl.to({},{duration:1.4},17.4);
  registerTimeline(tl);
"""

JOBS = {
    "ep02_ask":      ASK,
    "ep02_fakefilm": FAKEFILM,
    "ep02_readnotdone": READ,
    "ep02_land":     LAND,
}
OUTNAME = {
    "ep02_ask": "ep02f_ask",
    "ep02_fakefilm": "ep02f_fakefilm",
    "ep02_readnotdone": "ep02f_read",
    "ep02_land": "ep02f_land",
}

for name, script in JOBS.items():
    tmpl = (T / f"{name}.tmpl.html").read_text(encoding="utf-8")
    html = tmpl.replace("__DESK_B64__", DESK)
    html = re.sub(r"<script>\s*const tl\s*=\s*gsap\.timeline\(\);.*?</script>",
                  f"<script>{script}</script>", html, flags=re.S)
    out = T / f"{OUTNAME[name]}.html"
    out.write_text(html, encoding="utf-8")
    print("wrote", out.name, len(html), "bytes")
