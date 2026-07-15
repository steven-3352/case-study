#!/usr/bin/env python3
"""EP07 场景冒烟测试 · 每个模板在关键时刻截一帧,抓 JS 错误 + 目视排版。"""
import pathlib
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent
T = ROOT / "templates"
OUT = ROOT / "out" / "ep07full" / "smoke"
OUT.mkdir(parents=True, exist_ok=True)

# (模板, [关键时刻...])
JOBS = [
    ("ep07f_hook.html",      [1.2, 2.6, 4.0]),
    ("ep07f_recap.html",     [3.0, 7.0, 9.5, 12.5]),
    ("ep07f_steps12.html",   [3.0, 7.0, 11.5]),
    ("ep07f_steps345.html",  [3.0, 10.0, 14.0, 18.0]),
    ("ep07f_effect.html",    [2.5, 5.0, 8.0]),
    ("ep07f_limits.html",    [3.0, 7.0, 10.5, 14.0, 18.5]),
    ("ep07f_creed.html",     [2.5, 4.5, 6.5]),
    ("ep07f_cta.html",       [1.0, 3.5, 5.5, 7.5]),
    ("ep07f_subtitles.html", [10.0, 40.0, 85.0, 93.0]),
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
