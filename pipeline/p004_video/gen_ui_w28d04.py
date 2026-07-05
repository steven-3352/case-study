#!/usr/bin/env python3
"""W28D04 UI 叠层 PNG 生成 · Chrome headless 静态素材路径.

对齐 pipeline_config.yaml 的 5 张 assets_ui/*.png：
  03_m3_display_reveal_dark.png   · M3 display 140pt 反差大字两行
  05_m5_split_400w_vs_800.png     · M5 分屏（占位版 · 若真机截图存在自动合成）
  08_m8_5criteria_table_dark.png  · M8 10×5 表格 + 打勾 × 8 + 打叉 × 2 + 大结论
  09_m9_anti_tutorial_dark.png    · M9 反教程价值锚两行
  10_m10_cta_dark.png             · M10 CTA headline + caption

色板（design_language.md 硬门）：
  canvas_office_dark  #1a1a1a
  ink_light           #f5f5f0
  accent_soft         #ffc857
  accent_green        #4caf50
  accent_red          #e53935（禁 #ff5252 偏粉红）
  禁 Dracula：#bd93f9 · #ff79c6 · #8be9fd（gate_check_palette.py 硬拦）

用法：
  python3 pipeline/p004_video/gen_ui_w28d04.py

依赖：
  Chrome + macOS · headless=new
  （M5 若 assets/screenshot/raw/w28d04_M5_split_{400w,800}.png 缺失，改用马赛克占位）
"""
from __future__ import annotations

import pathlib
import subprocess
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "publish" / "2026-W28" / "D04-AI帮想视频选题" / "build" / "assets_ui"
OUT.mkdir(parents=True, exist_ok=True)

SCREENSHOT_DIR = ROOT / "assets" / "screenshot" / "raw"
SCREENSHOT_400W = SCREENSHOT_DIR / "w28d04_M5_split_400w.png"
SCREENSHOT_800 = SCREENSHOT_DIR / "w28d04_M5_split_800.png"

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
W, H = 1080, 1920

# design_language.md token · W28D04 白天办公深灰版
TOK = {
    "canvas_office_dark": "#1a1a1a",
    "ink_light": "#f5f5f0",
    "muted": "#7a7a7a",
    "accent_soft": "#ffc857",
    "accent_green": "#4caf50",
    "accent_red": "#e53935",
}


def shot(html: str, name: str) -> pathlib.Path:
    out = OUT / name
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as f:
        f.write(html)
        path = f.name
    subprocess.run(
        [CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
         f"--screenshot={out}", f"--window-size={W},{H}", "--force-device-scale-factor=1",
         f"file://{path}"],
        capture_output=True, timeout=60, check=True,
    )
    print(f"OK {name}")
    return out


BASE_CSS = f"""
* {{ margin: 0; padding: 0; box-sizing: border-box; -webkit-font-smoothing: antialiased; }}
html, body {{ width: {W}px; height: {H}px; overflow: hidden;
  font-family: -apple-system, "PingFang SC", "SF Pro Text", sans-serif; }}
"""


# ═══ M3 · 3s · 反差 display 140pt 两行 · chaos-punch-reveal 收束 ═══
def gen_m3_display_reveal() -> None:
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
{BASE_CSS}
body {{ background: {TOK['canvas_office_dark']}; color: {TOK['ink_light']}; position: relative;
  display: flex; flex-direction: column; align-items: center; justify-content: center; }}
.line-red {{ font-size: 132px; font-weight: 800; line-height: 1.25; letter-spacing: 4px;
  text-align: center; margin-bottom: 40px;
  color: {TOK['ink_light']}; }}
.line-red .quote {{ color: {TOK['accent_red']}; }}
.divider {{ width: 140px; height: 6px; background: {TOK['accent_red']};
  margin: 30px 0; }}
.line-yellow {{ font-size: 132px; font-weight: 800; line-height: 1.25; letter-spacing: 4px;
  text-align: center;
  color: {TOK['ink_light']}; }}
.line-yellow .quote {{ color: {TOK['accent_soft']}; }}
.stamp {{ position: absolute; top: 60px; right: 40px; font-size: 26px;
  color: {TOK['muted']}; letter-spacing: 2px; }}
</style></head><body>
<div class="stamp">M3 · chaos-punch-reveal</div>
<div class="line-red">打「<span class="quote">帮我想 10 个</span>」</div>
<div class="divider"></div>
<div class="line-yellow">AI 全给「<span class="quote">如何做好</span>」</div>
</body></html>"""
    shot(html, "03_m3_display_reveal_dark.png")


# ═══ M5 · 8-15s · 分屏 40w 赞 vs 800 赞（占位版：真截图缺席时用色块 + 大字兜底）═══
def gen_m5_split_placeholder() -> None:
    """若 assets/screenshot/raw/w28d04_M5_split_{400w,800}.png 都存在则用 ffmpeg hstack 合成。

    否则输出带说明的占位图（body 深灰 + 两块马赛克占位色 + drawtext 大字）。
    """
    if SCREENSHOT_400W.exists() and SCREENSHOT_800.exists():
        _compose_m5_from_real_screenshots()
        return
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
{BASE_CSS}
body {{ background: {TOK['canvas_office_dark']}; color: {TOK['ink_light']}; position: relative; }}
.split {{ display: flex; width: 100%; height: 1400px; margin-top: 260px; }}
.half {{ flex: 1; display: flex; align-items: center; justify-content: center;
  position: relative; overflow: hidden; }}
.divider {{ width: 2px; background: {TOK['ink_light']}; opacity: .85; }}
.mosaic-l {{ background:
  repeating-linear-gradient(45deg, #3a3a3a 0 40px, #4a4a4a 40px 80px, #2a2a2a 80px 120px); }}
.mosaic-r {{ background:
  repeating-linear-gradient(45deg, #2a2a2a 0 40px, #3a3a3a 40px 80px, #2a2a2a 80px 120px); }}
.big-l {{ font-size: 180px; font-weight: 900; letter-spacing: -8px;
  color: {TOK['ink_light']}; text-shadow: 0 4px 20px rgba(0,0,0,.8); line-height: 1; }}
.big-r {{ font-size: 180px; font-weight: 900; letter-spacing: -8px;
  color: {TOK['ink_light']}; text-shadow: 0 4px 20px rgba(0,0,0,.8); line-height: 1; }}
.label-l {{ position: absolute; bottom: 40px; left: 0; right: 0; text-align: center;
  font-size: 44px; font-weight: 600; color: {TOK['ink_light']}; letter-spacing: 4px; opacity: .9; }}
.label-r {{ position: absolute; bottom: 40px; left: 0; right: 0; text-align: center;
  font-size: 44px; font-weight: 600; color: {TOK['ink_light']}; letter-spacing: 4px; opacity: .9; }}
.title {{ position: absolute; top: 90px; left: 0; right: 0; text-align: center;
  font-size: 88px; font-weight: 800; color: {TOK['ink_light']}; letter-spacing: 6px; }}
.title .vs {{ color: {TOK['accent_red']}; margin: 0 24px; font-size: 88px; }}
.stamp {{ position: absolute; top: 40px; right: 40px; font-size: 26px;
  color: {TOK['accent_soft']}; letter-spacing: 2px; }}
.note {{ position: absolute; bottom: 100px; left: 0; right: 0; text-align: center;
  font-size: 32px; color: {TOK['muted']}; letter-spacing: 3px; padding: 0 60px;
  line-height: 1.5; }}
</style></head><body>
<div class="stamp">M5 · 占位版 · 待真截图合成</div>
<div class="title">同行 <span class="vs">vs</span> 我</div>
<div class="split">
  <div class="half mosaic-l">
    <div class="big-l">40w<br>赞</div>
    <div class="label-l">真截图待入</div>
  </div>
  <div class="divider"></div>
  <div class="half mosaic-r">
    <div class="big-r">800<br>赞</div>
    <div class="label-r">真截图待入</div>
  </div>
</div>
<div class="note">用户提供 assets/screenshot/raw/w28d04_M5_split_{{400w,800}}.png 后重跑本脚本自动 hstack 合成</div>
</body></html>"""
    shot(html, "05_m5_split_400w_vs_800.png")


def _compose_m5_from_real_screenshots() -> None:
    """ffmpeg hstack 两张真截图 + drawtext 大字 · 单位「赞」显式。"""
    out = OUT / "05_m5_split_400w_vs_800.png"
    ffmpeg = "/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg"
    if not pathlib.Path(ffmpeg).exists():
        ffmpeg = "ffmpeg"
    half_w = W // 2
    fc = (
        f"[0:v]scale={half_w}:{H}:force_original_aspect_ratio=increase,"
        f"crop={half_w}:{H}[l];"
        f"[1:v]scale={half_w}:{H}:force_original_aspect_ratio=increase,"
        f"crop={half_w}:{H}[r];"
        f"[l][r]hstack=inputs=2[base];"
        f"[base]drawbox=x={half_w - 1}:y=0:w=2:h={H}:color=white@0.85:t=fill,"
        f"drawtext=text='40w 赞':fontsize=120:fontcolor=#f5f5f0:"
        f"x=(w/4-text_w/2):y=100:box=1:boxcolor=black@0.5:boxborderw=20,"
        f"drawtext=text='800 赞':fontsize=120:fontcolor=#f5f5f0:"
        f"x=(3*w/4-text_w/2):y=100:box=1:boxcolor=black@0.5:boxborderw=20[out]"
    )
    subprocess.run(
        [ffmpeg, "-y", "-i", str(SCREENSHOT_400W), "-i", str(SCREENSHOT_800),
         "-filter_complex", fc, "-map", "[out]", "-frames:v", "1", str(out)],
        capture_output=True, timeout=60, check=True,
    )
    print(f"OK 05_m5_split_400w_vs_800.png (composed from real screenshots)")


# ═══ M8 · 34-42s · 5 判据表格 · 10×5 网格 + ✓ × 8 + ✗ × 2 + headline 10 里 8 ═══
def gen_m8_5criteria_table() -> None:
    rows_data = [
        # (选题名, [具体场景, 前3s钩子, 差异化, 可拍性, 粉丝相关])
        ("周日复盘 3 条压箱底", [True, True, True, True, True]),
        ("塑料筐 30 元 vs 亚克力 200 元", [True, True, True, True, True]),
        ("鞋柜进深小于 30 cm 怎么放", [True, True, True, True, True]),
        ("我家 5 平米收纳 SOP", [True, True, True, True, True]),
        ("宜家 5 件收纳神器", [True, True, True, True, True]),
        ("618 收纳好物", [True, True, False, True, True]),
        ("断舍离前后对比", [True, True, False, True, True]),
        ("我用 3 招搞定 60 平米", [True, True, True, True, True]),
        ("浅谈收纳的重要性", [False, False, False, False, False]),  # 反例
        ("5 个收纳误区", [False, False, False, False, False]),  # 反例
    ]

    def cell(v: bool) -> str:
        if v:
            return f"<td class='cell yes'>✓</td>"
        return f"<td class='cell no'>✗</td>"

    rows_html = ""
    for name, marks in rows_data:
        cells = "".join(cell(m) for m in marks)
        rows_html += f"<tr><td class='name'>{name}</td>{cells}</tr>\n"

    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
{BASE_CSS}
body {{ background: {TOK['canvas_office_dark']}; color: {TOK['ink_light']}; padding: 80px 40px;
  font-family: -apple-system, "PingFang SC", sans-serif; position: relative; }}
.title {{ font-size: 60px; font-weight: 800; margin-bottom: 20px; letter-spacing: 6px;
  text-align: center; color: {TOK['ink_light']}; }}
.subtitle {{ font-size: 30px; margin-bottom: 40px; letter-spacing: 3px;
  text-align: center; color: {TOK['muted']}; }}
table {{ width: 100%; border-collapse: collapse; font-size: 26px;
  background: rgba(0,0,0,.35); border: 1px solid {TOK['muted']}; }}
th {{ font-size: 24px; font-weight: 700; padding: 14px 6px; text-align: center;
  color: {TOK['accent_soft']}; letter-spacing: 2px;
  border-bottom: 2px solid {TOK['accent_soft']}; }}
td {{ padding: 20px 10px; border-bottom: 1px solid #2a2a2a; }}
td.name {{ font-size: 24px; color: {TOK['ink_light']}; padding-left: 20px;
  letter-spacing: 1px; }}
td.cell {{ text-align: center; font-size: 38px; font-weight: 900; }}
td.cell.yes {{ color: {TOK['accent_green']}; }}
td.cell.no {{ color: {TOK['accent_red']}; }}
.bigresult {{ position: absolute; bottom: 80px; left: 0; right: 0; text-align: center;
  font-size: 132px; font-weight: 900; letter-spacing: 12px;
  color: {TOK['accent_soft']}; text-shadow: 0 4px 24px rgba(255,200,87,.3); }}
.stamp {{ position: absolute; top: 40px; right: 40px; font-size: 24px;
  color: {TOK['muted']}; letter-spacing: 2px; }}
</style></head><body>
<div class="stamp">M8 · 5 判据 · 10 里 8</div>
<div class="title">5 判据一筛</div>
<div class="subtitle">具体场景 · 前 3s 钩子 · 差异化 · 可拍性 · 粉丝相关</div>
<table>
  <thead>
    <tr>
      <th style="width: 40%; text-align: left; padding-left: 20px;">候选选题</th>
      <th>场景</th>
      <th>钩子</th>
      <th>差异</th>
      <th>可拍</th>
      <th>相关</th>
    </tr>
  </thead>
  <tbody>
    {rows_html}
  </tbody>
</table>
<div class="bigresult">10 里 8</div>
</body></html>"""
    shot(html, "08_m8_5criteria_table_dark.png")


# ═══ M9 · 48-54s · 反教程价值锚 display 140pt 两行 ═══
def gen_m9_anti_tutorial() -> None:
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
{BASE_CSS}
body {{ background: {TOK['canvas_office_dark']}; color: {TOK['ink_light']}; position: relative;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  font-family: -apple-system, "PingFang SC", sans-serif; }}
.line1 {{ font-size: 132px; font-weight: 700; line-height: 1.25; letter-spacing: 6px;
  text-align: center; margin-bottom: 40px; color: {TOK['ink_light']}; opacity: .9; }}
.divider {{ width: 140px; height: 6px; background: {TOK['accent_red']}; margin: 30px 0; }}
.line2 {{ font-size: 132px; font-weight: 900; line-height: 1.25; letter-spacing: 4px;
  text-align: center; color: {TOK['accent_soft']}; padding: 0 60px; }}
.stamp {{ position: absolute; top: 60px; right: 40px; font-size: 26px;
  color: {TOK['muted']}; letter-spacing: 2px; }}
</style></head><body>
<div class="stamp">M9 · 反教程价值锚</div>
<div class="line1">不是教你用 AI</div>
<div class="divider"></div>
<div class="line2">是把 4 段 prompt<br>直接给你</div>
</body></html>"""
    shot(html, "09_m9_anti_tutorial_dark.png")


# ═══ M10 · 54-58s · CTA headline 88pt + caption ═══
def gen_m10_cta() -> None:
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
{BASE_CSS}
body {{ background: {TOK['canvas_office_dark']}; color: {TOK['ink_light']}; position: relative;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  font-family: -apple-system, "PingFang SC", sans-serif; padding: 100px 60px; }}
.headline {{ font-size: 84px; font-weight: 800; letter-spacing: 4px; line-height: 1.35;
  text-align: center; color: {TOK['ink_light']}; margin-bottom: 60px; }}
.headline .accent {{ color: {TOK['accent_soft']}; }}
.divider {{ width: 120px; height: 4px; background: {TOK['accent_red']}; margin: 40px 0; }}
.promise {{ font-size: 60px; font-weight: 700; letter-spacing: 4px;
  text-align: center; color: {TOK['ink_light']}; margin-bottom: 60px; opacity: .95; }}
.promise .num {{ color: {TOK['accent_soft']}; font-weight: 900; }}
.footer {{ font-size: 32px; color: {TOK['muted']}; letter-spacing: 3px;
  text-align: center; opacity: .85; }}
.stamp {{ position: absolute; top: 60px; right: 40px; font-size: 26px;
  color: {TOK['muted']}; letter-spacing: 2px; }}
</style></head><body>
<div class="stamp">M10 · CTA · 24h SLA</div>
<div class="headline">私信「<span class="accent">账号方向</span>」</div>
<div class="divider"></div>
<div class="promise">我给 <span class="num">5</span> 条选题</div>
<div class="footer">— 不推服务 · 只喂选题 —</div>
</body></html>"""
    shot(html, "10_m10_cta_dark.png")


# ═══ M2 · 1-1.6s · 屏录占位 · AI 对话框 + 打字光标 · 用户 QuickTime 屏录入库后可替换 ═══
def gen_m2_typing_placeholder() -> None:
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
{BASE_CSS}
body {{ background: #ffffff; color: #202124; position: relative;
  font-family: -apple-system, "PingFang SC", "SF Pro Text", sans-serif; }}
.statusbar {{ height: 44px; background: #ffffff; display: flex; align-items: center;
  justify-content: space-between; padding: 0 32px; font-size: 24px;
  color: #202124; border-bottom: 1px solid #eee; }}
.header {{ padding: 40px 60px 30px; border-bottom: 1px solid #eee;
  font-size: 44px; font-weight: 700; color: #202124; }}
.chatarea {{ padding: 60px; height: 1500px; display: flex;
  flex-direction: column; justify-content: flex-end; }}
.userbubble {{ align-self: flex-end; max-width: 780px; background: #f5f5f5;
  padding: 40px 50px; border-radius: 40px; font-size: 56px; font-weight: 500;
  color: #202124; line-height: 1.5; margin-bottom: 40px; }}
.userbubble .cursor {{ display: inline-block; width: 6px; height: 60px;
  background: #202124; margin-left: 4px; vertical-align: middle;
  animation: blink 1s step-end infinite; }}
.inputbar {{ background: #f5f5f5; border-radius: 40px; padding: 30px 50px;
  font-size: 40px; color: #999; letter-spacing: 2px; }}
.stamp {{ position: absolute; top: 60px; right: 40px; font-size: 24px;
  color: {TOK['muted']}; letter-spacing: 2px; background: rgba(0,0,0,.4);
  padding: 6px 14px; border-radius: 6px; }}
@keyframes blink {{ 50% {{ opacity: 0; }} }}
</style></head><body>
<div class="statusbar"><span>09:37</span><span>100%</span></div>
<div class="header">ChatGPT</div>
<div class="chatarea">
  <div class="userbubble">帮我想 10 个抖音选题<span class="cursor"></span></div>
  <div class="inputbar">Message ChatGPT...</div>
</div>
<div class="stamp">M2 · 屏录占位 · 用户 QuickTime 后替换</div>
</body></html>"""
    shot(html, "02_m2_typing_placeholder.png")


# ═══ M3 · 1.6-3s · AI 输出 3 条固定文案 · 用户屏录入库后可替换 ═══
def gen_m3_ai_output_placeholder() -> None:
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
{BASE_CSS}
body {{ background: #ffffff; color: #202124; position: relative;
  font-family: -apple-system, "PingFang SC", "SF Pro Text", sans-serif; }}
.statusbar {{ height: 44px; background: #ffffff; display: flex; align-items: center;
  justify-content: space-between; padding: 0 32px; font-size: 24px;
  color: #202124; border-bottom: 1px solid #eee; }}
.header {{ padding: 40px 60px 30px; border-bottom: 1px solid #eee;
  font-size: 44px; font-weight: 700; color: #202124; }}
.chatarea {{ padding: 60px; }}
.userbubble {{ align-self: flex-end; max-width: 780px; background: #f5f5f5;
  padding: 30px 45px; border-radius: 40px; font-size: 40px; color: #202124;
  margin-bottom: 30px; margin-left: auto; text-align: right; float: right; clear: both; }}
.aibubble {{ clear: both; max-width: 900px; padding: 40px 0;
  font-size: 44px; line-height: 1.6; color: #202124; }}
.ainame {{ font-size: 32px; font-weight: 600; color: #10a37f; margin-bottom: 20px;
  letter-spacing: 2px; }}
.aline {{ padding: 20px 0; border-bottom: 1px solid #eee; }}
.stamp {{ position: absolute; top: 60px; right: 40px; font-size: 24px;
  color: {TOK['muted']}; letter-spacing: 2px; background: rgba(0,0,0,.4);
  padding: 6px 14px; border-radius: 6px; }}
</style></head><body>
<div class="statusbar"><span>09:37</span><span>100%</span></div>
<div class="header">ChatGPT</div>
<div class="chatarea">
  <div class="userbubble">帮我想 10 个抖音选题</div>
  <div class="aibubble">
    <div class="ainame">ChatGPT</div>
    <div class="aline">1. 如何做好家居收纳</div>
    <div class="aline">2. 浅谈家居收纳的重要性</div>
    <div class="aline">3. 5 个家居收纳误区</div>
  </div>
</div>
<div class="stamp">M3 · 屏录占位 · 用户 QuickTime 后替换</div>
</body></html>"""
    shot(html, "03b_m3_ai_output_placeholder.png")


# ═══ M6 · 15-25s · 3 段烂 prompt 反例快切 · 全屏 3 段 stacked ═══
def gen_m6_wrong_placeholder() -> None:
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
{BASE_CSS}
body {{ background: {TOK['canvas_office_dark']}; color: {TOK['ink_light']}; position: relative;
  font-family: -apple-system, "PingFang SC", sans-serif; padding: 80px 60px; }}
.stamp {{ position: absolute; top: 40px; right: 40px; font-size: 24px;
  color: {TOK['muted']}; letter-spacing: 2px; }}
.title {{ font-size: 68px; font-weight: 800; margin-bottom: 60px;
  letter-spacing: 6px; text-align: center; color: {TOK['accent_soft']}; }}
.card {{ background: rgba(255,255,255,0.06); border-left: 8px solid {TOK['accent_red']};
  padding: 40px 50px; margin-bottom: 40px; border-radius: 12px; }}
.q {{ font-size: 38px; font-weight: 700; color: {TOK['ink_light']}; letter-spacing: 3px;
  margin-bottom: 20px; }}
.a {{ font-size: 34px; color: #d0d0d0; line-height: 1.5; letter-spacing: 2px; }}
.a .bad {{ color: {TOK['accent_red']}; font-weight: 600; }}
.cross {{ display: inline-block; font-size: 46px; color: {TOK['accent_red']};
  font-weight: 900; margin-left: 12px; }}
</style></head><body>
<div class="stamp">M6 · 屏录占位 · 用户 QuickTime 后替换</div>
<div class="title">问 AI 也 3 种烂法</div>
<div class="card">
  <div class="q">① 「帮我想 10 个抖音选题」<span class="cross">✗</span></div>
  <div class="a">→ 出的是 <span class="bad">「如何做好 XX」</span> 通用套话</div>
</div>
<div class="card">
  <div class="q">② 「加平台词：帮我想 10 个抖音选题」<span class="cross">✗</span></div>
  <div class="a">→ 出的是 <span class="bad">同行都在拍</span> 的模板</div>
</div>
<div class="card">
  <div class="q">③ 「帮我想 10 个类似 XX 的选题」<span class="cross">✗</span></div>
  <div class="a">→ 出的是 <span class="bad">换个数字</span> 的同质品</div>
</div>
</body></html>"""
    shot(html, "06_m6_wrong_placeholder.png")


# ═══ M7 · 25-40s · 4 段 prompt 演示核心 · 全屏 4 段结构（占位版）═══
def gen_m7_4prompt_placeholder() -> None:
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
{BASE_CSS}
body {{ background: #ffffff; color: #202124; position: relative;
  font-family: -apple-system, "PingFang SC", "SF Pro Text", sans-serif; padding: 60px 50px; }}
.stamp {{ position: absolute; top: 60px; right: 40px; font-size: 24px;
  color: #666; letter-spacing: 2px; background: rgba(0,0,0,.4); color: #fff;
  padding: 6px 14px; border-radius: 6px; }}
.title {{ font-size: 52px; font-weight: 800; color: #202124;
  margin-bottom: 40px; letter-spacing: 4px; text-align: center; }}
.title .accent {{ color: {TOK['accent_red']}; }}
.seg {{ background: #f8f8f8; border-left: 8px solid {TOK['accent_soft']};
  padding: 30px 40px; margin-bottom: 26px; border-radius: 8px; }}
.seg .label {{ font-size: 34px; font-weight: 800; color: {TOK['accent_red']};
  letter-spacing: 3px; margin-bottom: 14px; }}
.seg .content {{ font-size: 28px; color: #202124; line-height: 1.6;
  letter-spacing: 1px; font-family: "JetBrains Mono", "SF Mono", Menlo, monospace; }}
</style></head><body>
<div class="stamp">M7 · 屏录占位 · 用户 QuickTime 后替换</div>
<div class="title">4 段 prompt · <span class="accent">身份/账号/痛点/输出</span></div>
<div class="seg">
  <div class="label">【身份卡】</div>
  <div class="content">2 年运营经验短视频内容策划师 · 帮家居收纳中腰部博主策划 10 条抖音选题</div>
</div>
<div class="seg">
  <div class="label">【账号定位】</div>
  <div class="content">抖音（同步小红书 · 视频号）· 30 岁小家庭主妇 · 3 房 1 厅 · 2 猫 1 娃 · 租房不能大改造</div>
</div>
<div class="seg">
  <div class="label">【粉丝痛点】</div>
  <div class="content">租房不能钻墙 · 猫抓东西 · 老公不参与家务 · 娃 3 岁到处丢玩具 · 预算 ≤80 元</div>
</div>
<div class="seg">
  <div class="label">【输出约束】</div>
  <div class="content">10 条候选表格 · 列 = 标题/场景/钩子/成本/差异化 · 禁「浅谈…」「XX 神器」通用模板</div>
</div>
</body></html>"""
    shot(html, "07_m7_4prompt_placeholder.png")


def main() -> None:
    print(f"→ 输出到 {OUT}")
    gen_m2_typing_placeholder()
    gen_m3_ai_output_placeholder()
    gen_m3_display_reveal()
    gen_m5_split_placeholder()
    gen_m6_wrong_placeholder()
    gen_m7_4prompt_placeholder()
    gen_m8_5criteria_table()
    gen_m9_anti_tutorial()
    gen_m10_cta()
    m5_has_real = SCREENSHOT_400W.exists() and SCREENSHOT_800.exists()
    print()
    print(f"✓ 9 张 UI 叠层素材生成完成")
    print(f"  查看：ls {OUT}")
    if not m5_has_real:
        print()
        print("⚠ M5 走占位版：真截图未入库")
        print(f"  期望路径：")
        print(f"    {SCREENSHOT_400W}")
        print(f"    {SCREENSHOT_800}")
        print(f"  提供后重跑本脚本自动 hstack 合成")


if __name__ == "__main__":
    main()
