#!/usr/bin/env python3
"""EP04 场景冒烟测试 · 每个模板在关键时刻截一帧,抓 JS 错误 + 目视排版。"""
import pathlib
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent
T = ROOT / "templates"
OUT = ROOT / "out" / "ep04full" / "smoke"
OUT.mkdir(parents=True, exist_ok=True)

# (模板, [关键时刻...])
JOBS = [
    ("ep04f_hook.html",      [1.6, 3.6, 4.8, 5.6]),
    ("ep04f_scatter.html",   [2.0, 6.5, 9.4, 11.5]),
    ("ep04f_rule3.html",     [1.0, 4.6, 5.8, 8.0]),
    ("ep04f_heads.html",     [1.0, 5.0, 9.5, 13.2]),
    ("ep04f_auto.html",      [0.6, 2.4, 4.4, 5.2, 8.0]),
    ("ep04f_graph.html",     [1.5, 5.5, 8.2, 11.0, 14.0]),
    ("ep04f_parallel.html",  [1.8, 3.2, 5.0, 9.2, 11.5]),
    ("ep04f_land.html",      [2.6, 6.6, 7.8, 10.5, 12.5]),
    ("ep04f_subtitles.html", [3.0, 30.0, 60.0, 90.0]),
]

with sync_playwright() as p:
    b = p.chromium.launch(headless=True, args=["--font-render-hinting=none"])
    for tmpl, times in JOBS:
        errs = []
        ctx = b.new_context(viewport={"width":1080,"height":1920}, device_scale_factor=1, locale="zh-CN")
        pg = ctx.new_page()
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.on("console", lambda m: errs.append("console:"+m.text) if m.type=="error" else None)
        pg.goto((T/tmpl).resolve().as_uri())
        try:
            pg.wait_for_function("() => window.__timeline !== null", timeout=8000)
        except Exception as ex:
            print(f"✗ {tmpl}: __timeline 未注册 → {ex}")
            print("   errs:", errs[:3]); ctx.close(); continue
        dur = pg.evaluate("() => window.__timeline.duration()")
        transp = "subtitles" in tmpl
        for t in times:
            pg.evaluate("(t)=>window.__renderFrame(t)", t)
            pg.wait_for_timeout(0)
            pg.screenshot(path=str(OUT/f"{tmpl.replace('.html','')}_{t:05.1f}.png"), omit_background=transp)
        flag = "⚠ ERRORS" if errs else "ok"
        print(f"✓ {tmpl}: dur={dur:.2f}s  {flag}")
        if errs: print("   ", errs[:3])
        ctx.close()
    b.close()
print("smoke frames →", OUT)
