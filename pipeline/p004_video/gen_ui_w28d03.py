#!/usr/bin/env python3
"""W28D03 UI 仿真素材生成 · 走 Chrome headless 高保真仿真体裁路径.

产出 1080×1920（9:16）PNG，遵循 design_language.md token
（深夜黑 + 台灯暖 + 纸黄轮播底 · 禁 Dracula 霓虹 · 系统原生色允许）。
所有仿真界面标 generated_fact，声明为示例数据；多邻国类不打 logo，只留连击数字。

产出：
  publish/2026-W28/D03-AI陪练英语口语/build/assets_ui/*.png

用法：python3 pipeline/p004_video/gen_ui_w28d03.py
"""
from __future__ import annotations

import pathlib
import subprocess
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "publish" / "2026-W28" / "D03-AI陪练英语口语" / "build" / "assets_ui"
OUT.mkdir(parents=True, exist_ok=True)

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
W, H = 1080, 1920

# design_language.md token · D03 深夜暖光克制版
TOK = {
    "canvas_night": "#0a0a0a",
    "surface_paper": "#f5f5f0",
    "ink": "#1a1a1a",
    "ink_light": "#f5f5f0",
    "muted": "#7a7a7a",
    "warm_night": "#ffb26b",
    "accent_red": "#e53935",
    "accent_soft": "#ffc857",
    "ios_blue": "#007aff",
    "wechat_green": "#95ec69",
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


# ═══ M1 · iPhone 锁屏 23:12·又一次决心学英语 ═══
def gen_iphone_lockscreen_2312() -> None:
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
{BASE_CSS}
body {{ background: linear-gradient(180deg, #050505 0%, #0a0a0a 45%, #000 100%); color: white; position: relative; }}
.dot {{ position: absolute; top: 12px; left: 50%; transform: translateX(-50%); width: 120px; height: 40px; background: #000; border-radius: 20px; }}
.time {{ position: absolute; top: 200px; left: 50%; transform: translateX(-50%);
  font-family: -apple-system, "SF Pro Display", sans-serif; font-weight: 200;
  font-size: 340px; letter-spacing: -12px; line-height: 1; color: #f5f5f0; text-shadow: 0 4px 24px rgba(0,0,0,.5); }}
.date {{ position: absolute; top: 600px; left: 50%; transform: translateX(-50%);
  font-size: 44px; font-weight: 400; letter-spacing: 3px; opacity: .85; }}
.status {{ position: absolute; top: 32px; left: 44px; font-size: 30px; font-weight: 600; }}
.right {{ position: absolute; top: 32px; right: 44px; font-size: 30px; font-weight: 500; letter-spacing: 4px; }}
.subtitle {{ position: absolute; top: 780px; left: 60px; right: 60px; text-align: center;
  font-size: 56px; font-weight: 300; letter-spacing: 4px; color: #f5f5f0; opacity: .9; line-height: 1.3; }}
.bottom {{ position: absolute; bottom: 60px; left: 0; right: 0; text-align: center;
  font-size: 32px; opacity: .4; letter-spacing: 2px; }}
</style></head><body>
<div class="status">中国移动 5G</div>
<div class="right">42%</div>
<div class="dot"></div>
<div class="time">23:12</div>
<div class="date">7 月 4 日 周五</div>
<div class="subtitle">又一次决心学英语</div>
<div class="bottom">向上滑动以打开</div>
</body></html>"""
    shot(html, "01_lockscreen_2312.png")


# ═══ M2 · 群体锚 92% 中国人不敢开口 ═══
def gen_group_anchor_92() -> None:
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
{BASE_CSS}
body {{ background: {TOK['canvas_night']}; color: {TOK['ink_light']}; position: relative;
  display: flex; flex-direction: column; align-items: center; justify-content: center; }}
.big-num {{ font-family: -apple-system, "SF Pro Display", sans-serif;
  font-size: 500px; font-weight: 900; line-height: 1; letter-spacing: -20px;
  -webkit-text-stroke: 6px {TOK['accent_red']}; color: {TOK['ink_light']};
  margin-bottom: 40px; }}
.headline {{ font-size: 96px; font-weight: 700; letter-spacing: 8px; color: {TOK['ink_light']};
  text-align: center; line-height: 1.2; margin-bottom: 100px; }}
.source {{ position: absolute; bottom: 80px; left: 0; right: 0; text-align: center;
  font-size: 30px; color: {TOK['muted']}; letter-spacing: 3px; }}
.stamp {{ position: absolute; top: 80px; right: 40px; font-size: 28px;
  color: {TOK['muted']}; letter-spacing: 2px; }}
</style></head><body>
<div class="stamp">B 级同帧口径 · 引用</div>
<div class="big-num">92%</div>
<div class="headline">中国人不敢开口</div>
<div class="source">来源：讯飞《2024 中国英语学习报告》</div>
</body></html>"""
    shot(html, "02_group_anchor_92.png")


# ═══ M2 · 群体锚 78% 缺安全场合 ═══
def gen_group_anchor_78() -> None:
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
{BASE_CSS}
body {{ background: {TOK['canvas_night']}; color: {TOK['ink_light']}; position: relative;
  display: flex; flex-direction: column; align-items: center; justify-content: center; }}
.big-num {{ font-family: -apple-system, "SF Pro Display", sans-serif;
  font-size: 500px; font-weight: 900; line-height: 1; letter-spacing: -20px;
  -webkit-text-stroke: 6px {TOK['accent_red']}; color: {TOK['ink_light']};
  margin-bottom: 40px; }}
.headline {{ font-size: 96px; font-weight: 700; letter-spacing: 8px; color: {TOK['ink_light']};
  text-align: center; line-height: 1.2; margin-bottom: 100px; }}
.source {{ position: absolute; bottom: 80px; left: 0; right: 0; text-align: center;
  font-size: 30px; color: {TOK['muted']}; letter-spacing: 3px; }}
.stamp {{ position: absolute; top: 80px; right: 40px; font-size: 28px;
  color: {TOK['muted']}; letter-spacing: 2px; }}
</style></head><body>
<div class="stamp">B 级同帧口径 · 引用</div>
<div class="big-num">78%</div>
<div class="headline">缺安全场合</div>
<div class="source">来源：讯飞《2024 中国英语学习报告》</div>
</body></html>"""
    shot(html, "03_group_anchor_78.png")


# ═══ M3 · 多邻国 700 天连击（不打 logo · 只留连击数字与火苗）═══
def gen_streak_700() -> None:
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
{BASE_CSS}
body {{ background: #58cc02; color: white; position: relative;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  font-family: -apple-system, "PingFang SC", sans-serif; }}
.flame {{ font-size: 320px; line-height: 1; margin-bottom: 20px; }}
.days {{ font-size: 380px; font-weight: 900; line-height: 1; letter-spacing: -18px; margin-bottom: 30px; }}
.label {{ font-size: 60px; font-weight: 600; letter-spacing: 6px; opacity: .95; }}
.stamp {{ position: absolute; top: 60px; right: 40px; font-size: 26px; letter-spacing: 2px;
  opacity: .7; background: rgba(0,0,0,.3); padding: 8px 16px; border-radius: 6px; }}
.mask {{ position: absolute; top: 30px; left: 30px; width: 400px; height: 80px;
  background: rgba(0,0,0,.75); border-radius: 12px;
  display: flex; align-items: center; justify-content: center;
  font-size: 28px; color: white; letter-spacing: 2px; opacity: .9; }}
</style></head><body>
<div class="mask">App Logo Masked</div>
<div class="stamp">generated_fact · 示例连击</div>
<div class="flame">🔥</div>
<div class="days">700</div>
<div class="label">天连续打卡</div>
</body></html>"""
    shot(html, "04_streak_700.png")


# ═══ M3 · 视频通话尴尬沉默（3s 静默 UI）═══
def gen_facetime_awkward() -> None:
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
{BASE_CSS}
body {{ background: #1a1a1a; color: white; position: relative;
  font-family: -apple-system, "PingFang SC", sans-serif; }}
.remote {{ position: absolute; top: 0; left: 0; right: 0; bottom: 0;
  background: linear-gradient(135deg, #2d3436 0%, #1a1a1a 100%);
  display: flex; align-items: center; justify-content: center; }}
.remote-avatar {{ width: 280px; height: 280px; border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex; align-items: center; justify-content: center;
  font-size: 140px; color: white; font-weight: 300; }}
.remote-name {{ position: absolute; bottom: 50%; margin-bottom: -260px; left: 0; right: 0;
  text-align: center; font-size: 44px; font-weight: 500; letter-spacing: 2px; }}
.self-cam {{ position: absolute; top: 100px; right: 40px; width: 240px; height: 340px;
  background: linear-gradient(180deg, #2a1f14 0%, #1a1710 100%); border-radius: 16px;
  border: 3px solid rgba(255,255,255,.2);
  display: flex; align-items: center; justify-content: center;
  font-size: 100px; opacity: .8; }}
.silence-tag {{ position: absolute; top: 50%; left: 60px; right: 60px; margin-top: 100px;
  text-align: center; background: rgba(0,0,0,.6); padding: 20px 40px; border-radius: 20px;
  font-size: 44px; color: {TOK['accent_red']}; font-weight: 600; letter-spacing: 4px;
  border: 2px solid {TOK['accent_red']}; }}
.duration {{ position: absolute; top: 60px; left: 0; right: 0; text-align: center;
  font-size: 36px; opacity: .8; letter-spacing: 3px; }}
.bottom-bar {{ position: absolute; bottom: 100px; left: 0; right: 0; display: flex;
  justify-content: center; gap: 40px; }}
.bar-btn {{ width: 100px; height: 100px; border-radius: 50%; background: rgba(255,255,255,.15);
  display: flex; align-items: center; justify-content: center; font-size: 44px; }}
.bar-btn.end {{ background: {TOK['accent_red']}; }}
.stamp {{ position: absolute; top: 20px; right: 20px; font-size: 22px;
  color: rgba(255,255,255,.5); letter-spacing: 2px; }}
</style></head><body>
<div class="stamp">generated_fact</div>
<div class="remote">
  <div class="remote-avatar">M</div>
</div>
<div class="remote-name">Mike · Australia</div>
<div class="duration">01:47</div>
<div class="self-cam">🫥</div>
<div class="silence-tag">·  ·  ·  沉默 3 秒  ·  ·  ·</div>
<div class="bottom-bar">
  <div class="bar-btn">🎤</div>
  <div class="bar-btn">📹</div>
  <div class="bar-btn end">📞</div>
</div>
</body></html>"""
    shot(html, "05_facetime_awkward.png")


# ═══ M4 · AI 反例「怎么练口语」→ 10 条废话 ═══
def gen_ai_wrong_prompt() -> None:
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
{BASE_CSS}
body {{ background: {TOK['surface_paper']}; color: {TOK['ink']}; padding: 40px 40px 0;
  font-family: -apple-system, "PingFang SC", sans-serif; position: relative; }}
.title {{ font-size: 40px; font-weight: 600; margin-bottom: 30px; letter-spacing: 1px; color: {TOK['muted']}; }}
.msg-user {{ display: flex; justify-content: flex-end; margin: 30px 0; }}
.bubble-user {{ background: #d1e7ff; border-radius: 24px; padding: 26px 32px; max-width: 720px;
  font-size: 40px; color: {TOK['ink']}; border: 3px solid {TOK['accent_red']}; }}
.msg-ai {{ display: flex; margin: 30px 0; }}
.avatar {{ width: 68px; height: 68px; border-radius: 16px; background: {TOK['ink']}; color: white;
  display: flex; align-items: center; justify-content: center; font-size: 32px; margin-right: 20px; flex-shrink: 0; }}
.bubble-ai {{ background: #efede8; border-radius: 24px; padding: 28px 32px; max-width: 820px;
  font-size: 30px; color: {TOK['ink']}; line-height: 1.55; }}
.bubble-ai h4 {{ font-size: 32px; font-weight: 700; margin: 8px 0 12px; }}
.bubble-ai p {{ margin: 6px 0; }}
.stamp {{ position: absolute; top: 260px; right: 40px; transform: rotate(-6deg);
  border: 6px solid {TOK['accent_red']}; padding: 12px 40px;
  font-size: 44px; font-weight: 900; color: {TOK['accent_red']}; letter-spacing: 4px;
  background: rgba(255,255,255,.85); z-index: 5; }}
.footlabel {{ position: absolute; bottom: 60px; left: 0; right: 0; text-align: center;
  font-size: 32px; color: {TOK['muted']}; letter-spacing: 2px; }}
</style></head><body>
<div class="title">AI 对话</div>
<div class="msg-user">
  <div class="bubble-user">怎么练口语？</div>
</div>
<div class="stamp">10 条废话</div>
<div class="msg-ai">
  <div class="avatar">AI</div>
  <div class="bubble-ai">
    <h4>练口语的 10 个建议</h4>
    <p>1. 每天坚持大声朗读</p>
    <p>2. 多听英语新闻、播客</p>
    <p>3. 使用背单词 App 每日打卡</p>
    <p>4. 看美剧不要字幕跟读</p>
    <p>5. 找语伴对话练习</p>
    <p>6. 报名口语培训班系统学习</p>
    <p>7. 参加英语角活动</p>
    <p>8. 录音自查发音问题</p>
    <p>9. 保持自信和耐心</p>
    <p>10. 持之以恒才能进步</p>
  </div>
</div>
<div class="footlabel">↑ 全是通用建议 · 没一句能马上做</div>
</body></html>"""
    shot(html, "06_ai_wrong_prompt.png")


# ═══ M5 · 分屏静图类比锚（游泳教程 vs 跳进泳池）═══
def gen_analogy_split() -> None:
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
{BASE_CSS}
body {{ background: {TOK['canvas_night']}; color: {TOK['ink_light']}; position: relative;
  display: flex; flex-direction: column; }}
.split {{ display: flex; width: 100%; height: 1200px; margin-top: 240px; }}
.half {{ flex: 1; display: flex; align-items: center; justify-content: center;
  position: relative; overflow: hidden; }}
.divider {{ width: 2px; background: {TOK['ink_light']}; opacity: .8; }}
.left {{ background: linear-gradient(180deg, #d4e4f0 0%, #e8ecf0 100%); }}
.right {{ background: linear-gradient(180deg, #4a9fc7 0%, #1a5a80 100%); }}
.icon {{ font-size: 420px; line-height: 1; }}
.label-l {{ position: absolute; bottom: 60px; left: 0; right: 0; text-align: center;
  font-size: 44px; font-weight: 600; color: {TOK['ink']}; letter-spacing: 4px; }}
.label-r {{ position: absolute; bottom: 60px; left: 0; right: 0; text-align: center;
  font-size: 44px; font-weight: 600; color: {TOK['ink_light']}; letter-spacing: 4px; }}
.headline {{ position: absolute; top: 80px; left: 0; right: 0; text-align: center;
  font-size: 92px; font-weight: 700; color: {TOK['ink_light']}; letter-spacing: 6px; line-height: 1.2; }}
.headline .vs {{ color: {TOK['accent_red']}; margin: 0 30px; }}
</style></head><body>
<div class="headline">读游泳教程 <span class="vs">vs</span> 跳进泳池</div>
<div class="split">
  <div class="half left">
    <div class="icon">📖</div>
    <div class="label-l">读游泳教程</div>
  </div>
  <div class="divider"></div>
  <div class="half right">
    <div class="icon">🏊</div>
    <div class="label-r">跳进泳池</div>
  </div>
</div>
</body></html>"""
    shot(html, "07_analogy_split.png")


# ═══ M6 · role prompt 全屏（可截图带走）═══
def gen_role_prompt_full() -> None:
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
{BASE_CSS}
body {{ background: {TOK['canvas_night']}; color: {TOK['ink_light']}; padding: 60px 50px;
  font-family: "SF Mono", "JetBrains Mono", Menlo, monospace; position: relative; }}
.title {{ font-family: -apple-system, "PingFang SC", sans-serif; font-size: 46px; font-weight: 700;
  margin-bottom: 12px; letter-spacing: 2px; }}
.subtitle {{ font-family: -apple-system, "PingFang SC", sans-serif; font-size: 26px;
  color: {TOK['muted']}; margin-bottom: 40px; }}
.tag {{ display: inline-block; background: {TOK['accent_soft']}; color: {TOK['ink']};
  padding: 6px 14px; border-radius: 6px; font-weight: 700; font-size: 26px;
  font-family: -apple-system, "PingFang SC", sans-serif; margin-right: 16px; }}
.p-title {{ margin: 30px 0 10px; font-family: -apple-system, "PingFang SC", sans-serif;
  font-size: 34px; font-weight: 600; color: {TOK['accent_soft']}; }}
.p-text {{ font-size: 30px; line-height: 1.6; color: {TOK['ink_light']}; opacity: .95; padding-left: 20px; }}
.p-text.en {{ font-family: "SF Mono", "JetBrains Mono", Menlo, monospace; font-size: 28px; }}
.footlabel {{ position: absolute; bottom: 50px; left: 50px; right: 50px;
  font-family: -apple-system, "PingFang SC", sans-serif;
  font-size: 30px; color: {TOK['muted']}; letter-spacing: 2px;
  border-top: 1px solid {TOK['muted']}; padding-top: 20px; }}
</style></head><body>
<div class="title">22:30 · 救命 role prompt</div>
<div class="subtitle">收藏本页 · 复制到豆包语音 · 长按语音键说话</div>

<div class="p-title"><span class="tag">1 · 角色卡</span>你是谁</div>
<div class="p-text">You are my IELTS Speaking Part 3 tutor.</div>

<div class="p-title"><span class="tag">2 · 场景</span>我是谁 · 在哪一 part</div>
<div class="p-text">I'm preparing Part 3, topic: Books.</div>

<div class="p-title"><span class="tag">3 · 只提问</span>不解释、不领读</div>
<div class="p-text">Ask me only in English. Follow-up like a real examiner.</div>

<div class="p-title"><span class="tag">4 · 说错不打断</span>让我先说完</div>
<div class="p-text">Don't interrupt me if I make mistakes.</div>

<div class="p-title"><span class="tag">5 · 结束反馈</span>不即时纠错</div>
<div class="p-text">Give quick feedback only at the end.</div>

<div class="footlabel">→ 长按暂停复制 · 30 分钟真开口练习</div>
</body></html>"""
    shot(html, "08_role_prompt_full.png")


# ═══ M8 · 侧躺时间戳 22:45 · 今天真开口 15 分钟 ═══
def gen_lying_side_2245() -> None:
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
{BASE_CSS}
body {{ background: linear-gradient(180deg, #1a1613 0%, #2a2018 40%, #0a0806 100%);
  color: {TOK['ink_light']}; position: relative;
  font-family: -apple-system, "PingFang SC", sans-serif; }}
.glow {{ position: absolute; top: 50%; left: -20%; right: -20%; height: 40%;
  background: radial-gradient(ellipse at center, rgba(255, 180, 100, 0.15) 0%, transparent 60%);
  pointer-events: none; }}
.phone-glow {{ position: absolute; bottom: 300px; left: 30%; width: 500px; height: 900px;
  background: radial-gradient(ellipse at center, rgba(200, 220, 255, 0.12) 0%, transparent 60%);
  pointer-events: none; }}
.time-big {{ position: absolute; top: 300px; right: 60px;
  font-family: "SF Mono", "JetBrains Mono", Menlo, monospace;
  font-size: 240px; font-weight: 200; letter-spacing: -10px;
  color: {TOK['ink_light']}; line-height: 1; }}
.sub {{ position: absolute; top: 620px; right: 60px;
  font-size: 44px; font-weight: 400; letter-spacing: 4px; opacity: .8;
  text-align: right; line-height: 1.4; }}
.hint {{ position: absolute; bottom: 100px; left: 60px; right: 60px;
  font-size: 30px; color: {TOK['muted']}; letter-spacing: 2px;
  text-align: center; }}
</style></head><body>
<div class="glow"></div>
<div class="phone-glow"></div>
<div class="time-big">22:45</div>
<div class="sub">今天真开口<br>15 分钟</div>
<div class="hint">— 侧躺 · 台灯关 · 手机屏还亮着 —</div>
</body></html>"""
    shot(html, "09_lying_side_2245.png")


# ═══ M9 · 全屏价值锚「不是教你 · 是把 prompt 给你」═══
def gen_value_anchor_full() -> None:
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
{BASE_CSS}
body {{ background: {TOK['canvas_night']}; color: {TOK['ink_light']}; position: relative;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  font-family: -apple-system, "PingFang SC", sans-serif; }}
.line1 {{ font-size: 108px; font-weight: 700; line-height: 1.3; letter-spacing: 6px;
  text-align: center; margin-bottom: 60px; color: {TOK['ink_light']}; }}
.line2 {{ font-size: 84px; font-weight: 900; line-height: 1.3; letter-spacing: 4px;
  text-align: center; color: {TOK['accent_soft']}; padding: 0 60px; }}
.divider {{ width: 120px; height: 4px; background: {TOK['accent_red']};
  margin: 40px 0 60px; }}
</style></head><body>
<div class="line1">不是教你怎么问 AI</div>
<div class="divider"></div>
<div class="line2">是把我 22:30 用的<br>救命 role prompt 给你</div>
</body></html>"""
    shot(html, "10_value_anchor.png")


# ═══ M10 · CTA 四选项 ═══
def gen_cta_options() -> None:
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
{BASE_CSS}
body {{ background: {TOK['canvas_night']}; color: {TOK['ink_light']}; position: relative;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  font-family: -apple-system, "PingFang SC", sans-serif; padding: 100px 60px; }}
.headline {{ font-size: 60px; font-weight: 600; letter-spacing: 4px; margin-bottom: 100px;
  text-align: center; opacity: .9; }}
.options {{ display: flex; flex-direction: column; gap: 60px; margin-bottom: 120px; }}
.opt {{ font-size: 120px; font-weight: 800; letter-spacing: 12px; text-align: center;
  padding: 30px 60px; position: relative; }}
.opt::before {{ content: ""; position: absolute; bottom: 20px; left: 50%;
  transform: translateX(-50%); width: 60%; height: 4px;
  background: {TOK['accent_soft']}; opacity: .6; }}
.footer {{ font-size: 36px; color: {TOK['muted']}; letter-spacing: 3px;
  text-align: center; opacity: .8; }}
</style></head><body>
<div class="headline">评论区回复 · 我发对应 role prompt</div>
<div class="options">
  <div class="opt">面试</div>
  <div class="opt">雅思</div>
  <div class="opt">日常</div>
  <div class="opt">旅游</div>
</div>
<div class="footer">— 私信过慢 · 评论区更快 —</div>
</body></html>"""
    shot(html, "11_cta_options.png")


def main() -> None:
    print(f"→ 输出到 {OUT}")
    gen_iphone_lockscreen_2312()
    gen_group_anchor_92()
    gen_group_anchor_78()
    gen_streak_700()
    gen_facetime_awkward()
    gen_ai_wrong_prompt()
    gen_analogy_split()
    gen_role_prompt_full()
    gen_lying_side_2245()
    gen_value_anchor_full()
    gen_cta_options()
    print(f"\n✓ 11 张 UI 仿真素材生成完成")
    print(f"  查看：ls {OUT}")


if __name__ == "__main__":
    main()
