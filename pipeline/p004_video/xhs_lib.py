#!/usr/bin/env python3
"""小红书图文轮播 · 共享皮肤库(1080×1440 · 与视频同终端皮肤)。

各集 gen_xhs_ep0X 只需提供:cover_html + [dark_page(...)] 列表。
"""
from __future__ import annotations
import pathlib
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[2]
DESK = (ROOT/"pipeline/p004_video/templates/ep01f_desk.jpg").resolve().as_uri()
W, H = 1080, 1440

def base_css():
    return f"""
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
:root{{ --ink:#e6edf3; --muted:#8b949e; --green:#3fb950; --amber:#d29922; --red:#e5484d; --blue:#4c9aff; }}
html,body{{ width:{W}px; height:{H}px; overflow:hidden; font-family:"PingFang SC","Heiti SC","SF Mono",sans-serif; }}
.page{{ position:relative; width:{W}px; height:{H}px; overflow:hidden; }}
.dark{{ background-image:url("{DESK}"); background-size:cover; background-position:center 58%; color:var(--ink); }}
.dark .scrim{{ position:absolute; inset:0; background:
  linear-gradient(180deg, rgba(6,9,14,.86) 0%, rgba(6,9,14,.62) 32%, rgba(6,9,14,.66) 60%, rgba(6,9,14,.94) 100%); }}
.tag{{ position:absolute; top:70px; left:70px; font-size:34px; font-weight:900; letter-spacing:2px;
  color:#fff; padding:14px 26px; border-radius:14px; font-family:"SF Mono",monospace; }}
.idx{{ position:absolute; top:78px; right:70px; font-size:30px; color:var(--muted); font-family:"SF Mono",monospace; letter-spacing:2px; }}
.term{{ position:absolute; left:70px; right:70px; top:230px; background:rgba(13,17,23,.94); border-radius:22px; padding:0 0 26px;
  box-shadow:0 30px 80px rgba(0,0,0,.6),0 0 0 1px rgba(255,255,255,.05); }}
.bar{{ height:70px; background:rgba(22,27,34,.95); border-radius:20px 20px 0 0; display:flex; align-items:center; gap:12px; padding:0 26px; }}
.bar i{{ width:20px; height:20px; border-radius:50%; }} .bar .r{{background:#ff5f56}} .bar .y{{background:#febc2e}} .bar .g{{background:#27c93f}}
.bar .p{{ color:var(--muted); font-size:26px; margin-left:12px; font-family:"SF Mono",monospace; }}
.termbody{{ padding:30px 34px 6px; font-size:37px; line-height:1.5; font-family:"SF Mono","PingFang SC",monospace; }}
.termbody .u{{ color:var(--ink); }} .termbody .a{{ color:var(--muted); }}
.termbody .ok{{ color:var(--green); font-weight:800; }} .termbody .hot{{ color:#ffb3b5; font-weight:800; }}
.termbody .h{{ color:var(--amber); }} .termbody .red{{ color:var(--red); font-weight:900; font-style:normal; }}
.headline{{ position:absolute; left:70px; right:70px; bottom:150px; font-size:74px; font-weight:900;
  line-height:1.24; letter-spacing:1px; color:#fff; text-shadow:0 4px 26px rgba(0,0,0,.9); }}
.headline b{{ color:var(--red); }} .headline .amb{{ color:var(--amber); }} .headline .blu{{ color:#8fbaff; }}
.foot{{ position:absolute; left:70px; bottom:70px; font-size:28px; color:var(--muted); letter-spacing:2px; }}
</style>
"""

def dark_page(tag, idx, term_html, headline, foot, tag_bg="#e5484d", path="claude ~/my-ai-assistant"):
    return f"""
<div class="page dark">
  <div class="scrim"></div>
  <div class="tag" style="background:{tag_bg};">{tag}</div>
  <div class="idx">{idx}</div>
  <div class="term">
    <div class="bar"><i class="r"></i><i class="y"></i><i class="g"></i><span class="p">{path}</span></div>
    <div class="termbody">{term_html}</div>
  </div>
  <div class="headline">{headline}</div>
  <div class="foot">{foot}</div>
</div>
"""

def render(pages, out_dir):
    out_dir = pathlib.Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    css = base_css()
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True, args=["--font-render-hinting=none"])
        ctx = b.new_context(viewport={"width":W,"height":H}, device_scale_factor=1, locale="zh-CN")
        pg = ctx.new_page()
        for pid, body in pages:
            pg.set_content(f"<!DOCTYPE html><html><head><meta charset='utf-8'>{css}</head><body>{body}</body></html>")
            pg.wait_for_timeout(180)
            out = out_dir/f"{pid}.png"
            pg.screenshot(path=str(out), clip={"x":0,"y":0,"width":W,"height":H})
            print("✓", out.name)
        b.close()
    print("→", out_dir)
