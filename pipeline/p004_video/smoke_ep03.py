#!/usr/bin/env python3
"""EP03 场景冒烟测试 · 每个模板在关键时刻截一帧,抓 JS 错误 + 目视排版。"""
import pathlib
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent
T = ROOT / "templates"
OUT = ROOT / "out" / "ep03full" / "smoke"
OUT.mkdir(parents=True, exist_ok=True)

JOBS = [
    ("ep03f_hook.html",       [2.6, 5.4, 7.0]),
    ("ep03f_dumbfix.html",    [1.5, 5.5, 8.2, 10.3]),
    ("ep03f_read.html",       [2.0, 4.3, 6.2]),
    ("ep03f_deadends.html",   [3.6, 6.7, 9.0, 11.8]),
    ("ep03f_mechanical.html", [2.4, 4.2, 8.6, 11.3]),
    ("ep03f_rule.html",       [1.4, 3.8, 6.6, 9.0]),
    ("ep03f_land.html",       [1.6, 5.5, 9.0, 11.7, 13.8]),
    ("ep03f_subtitles.html",  [12.0, 40.0, 70.0]),
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
