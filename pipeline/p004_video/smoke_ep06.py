#!/usr/bin/env python3
"""EP06 场景冒烟测试 · 每个模板在关键时刻截一帧,抓 JS 错误 + 目视排版。"""
import pathlib
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent
T = ROOT / "templates"
OUT = ROOT / "out" / "ep06full" / "smoke"
OUT.mkdir(parents=True, exist_ok=True)

# (模板, [关键时刻...])
JOBS = [
    ("ep06f_hook.html",      [1.9, 3.2, 5.2]),
    ("ep06f_stance.html",    [1.2, 3.6, 5.0, 8.0]),
    ("ep06f_crash1.html",    [1.7, 4.0, 7.3, 11.5]),
    ("ep06f_fix1.html",      [1.6, 3.3, 4.5]),
    ("ep06f_crash2.html",    [1.3, 4.5, 8.3]),
    ("ep06f_fix2.html",      [1.5, 3.4, 6.9, 8.0]),
    ("ep06f_crash3.html",    [3.5, 7.0, 10.9, 13.2]),
    ("ep06f_boundary.html",  [1.2, 2.2, 5.5, 8.3]),
    ("ep06f_land.html",      [1.0, 5.0, 7.9, 11.7]),
    ("ep06f_subtitles.html", [10.0, 60.0, 95.0]),
]

with sync_playwright() as p:
    b = p.chromium.launch(headless=True, args=["--font-render-hinting=none"])
    for tmpl, times in JOBS:
        if not (T/tmpl).exists():
            print(f"⏭  {tmpl}: 不存在,跳过"); continue
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
