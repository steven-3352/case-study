#!/usr/bin/env python3
"""Render real-screenshot showcase frames (1080x1920) for the video."""
import subprocess, tempfile, pathlib, base64

ROOT = pathlib.Path(__file__).resolve().parent
SL = ROOT / "slides"; SHOTS = ROOT / "assets" / "shots"; PINS = pathlib.Path("/Users/bubu/Documents/projects/Pinterest/pins/final")
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

def b64(p): return base64.b64encode(pathlib.Path(p).read_bytes()).decode()
def img(p): return f"data:image/png;base64,{b64(p)}"

CSS = """*{margin:0;padding:0;box-sizing:border-box;}
html,body{width:1080px;height:1920px;}
body{font-family:"Hiragino Sans GB",sans-serif;background:radial-gradient(130% 70% at 50% -10%,rgba(224,176,94,.16),rgba(11,13,16,0) 55%),#0b0d10;color:#ede6da;}
.slide{width:1080px;height:1920px;padding:120px 80px 110px;display:flex;flex-direction:column;}
.eyebrow{display:flex;align-items:center;gap:18px;color:#e0b15e;font-size:30px;letter-spacing:.12em;font-weight:600;margin-bottom:40px;}
.eyebrow .dot{width:10px;height:10px;border-radius:50%;background:#e0b15e;}
h2{font-size:72px;font-weight:800;color:#fff;margin-bottom:50px;letter-spacing:-.01em;}
.cap{font-size:30px;color:#9aa0a8;margin-top:18px;text-align:center;}
.grow{flex:1;}
.foot{display:flex;align-items:center;justify-content:space-between;border-top:1px solid rgba(237,230,218,.12);padding-top:30px;margin-top:30px;}
.foot .who{font-size:32px;color:#ede6da;font-weight:700;}
.foot .tag{font-size:26px;color:#7c8088;}
.phones{display:flex;gap:34px;justify-content:center;align-items:flex-start;}
.phone{width:380px;border-radius:30px;overflow:hidden;border:3px solid rgba(224,176,94,.45);box-shadow:0 24px 60px rgba(0,0,0,.6);}
.phone img{width:100%;display:block;}
.pins{display:flex;gap:24px;justify-content:center;}
.pin{width:288px;border-radius:18px;overflow:hidden;border:2px solid rgba(224,176,94,.4);box-shadow:0 18px 44px rgba(0,0,0,.55);}
.pin img{width:100%;display:block;}
.lab{display:flex;gap:34px;justify-content:center;}
.lab div{width:380px;}
"""

def shell(eyebrow, inner, foot_tag="真实上线 · 非样机"):
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{CSS}</style></head>
<body><div class="slide"><div class="eyebrow"><span class="dot"></span>{eyebrow}</div>{inner}
<div class="foot"><div class="who">腾铂森科技 · AI 服务商</div><div class="tag">{foot_tag}</div></div></div></body></html>"""

def render(name, html):
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False) as f:
        f.write(html); path=f.name
    out = SL / f"{name}.png"
    subprocess.run([CHROME,"--headless=new","--disable-gpu","--hide-scrollbars",
        f"--screenshot={out}","--window-size=1080,1920","--force-device-scale-factor=1",
        f"file://{path}"], capture_output=True, timeout=120)
    print("OK" if out.exists() else "FAIL", out)

# 实拍页面
pages = f"""<h2>真实上线的页面</h2>
<div class="phones">
  <div class="phone"><img src="{img(SHOTS/'landing.png')}"></div>
  <div class="phone"><img src="{img(SHOTS/'blueprint.png')}"></div>
</div>
<div class="lab"><div class="cap">品牌落地页</div><div class="cap">蓝图 Waitlist</div></div>
<div class="grow"></div>"""
render("shot_pages", shell("真实交付 · 页面实拍", pages))

# 实拍内容
pins = f"""<h2>真实内容产出</h2>
<div class="pins">
  <div class="pin"><img src="{img(PINS/'pin01_wealth_corner.png')}"></div>
  <div class="pin"><img src="{img(PINS/'b2_06_pixiu.png')}"></div>
  <div class="pin"><img src="{img(PINS/'b2_02_colors.png')}"></div>
</div>
<div class="cap" style="margin-top:34px;">AI 只出背景图 · 文字用代码精排 · 风格统一防「AI 味」</div>
<div class="grow"></div>"""
render("shot_pins", shell("真实交付 · 内容实拍", pins))
print("done")
