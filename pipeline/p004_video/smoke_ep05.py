#!/usr/bin/env python3
"""EP05 场景冒烟测试 · 每个模板在关键时刻截一帧,抓 JS 错误 + 目视排版。"""
import pathlib
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent
T = ROOT / "templates"
OUT = ROOT / "out" / "ep05full" / "smoke"
OUT.mkdir(parents=True, exist_ok=True)

# (模板, [关键时刻...])
JOBS = [
    ("ep05f_hook.html",      [1.9, 4.6, 6.0, 7.6]),
    ("ep05f_seed.html",      [2.6, 6.5, 9.2, 11.0]),
    ("ep05f_locks12.html",   [1.6, 5.4, 8.3, 11.9, 15.9, 19.0]),
    ("ep05f_locks34.html",   [1.7, 5.7, 8.8, 12.2, 17.3, 20.0]),
    ("ep05f_honest.html",    [0.6, 2.6, 4.7, 6.3, 7.6]),
    ("ep05f_land.html",      [1.3, 3.6, 6.0, 8.5, 10.4]),
    ("ep05f_subtitles.html", [5.0, 25.0, 50.0, 70.0, 82.0]),
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
