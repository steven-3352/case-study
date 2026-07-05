#!/usr/bin/env python3
"""W28D07 UI 叠层 PNG 生成 · Chrome headless 静态素材路径.

选题: 家长陪孩子学英语 · 聊天气泡 + 3 年龄段 prompt 卡 (H6 全新族群 vs D06 简历纸面扫描线)

对齐 pipeline_config.yaml 的 11 张 assets_ui/*.png:
  01_m1_chat_freeze.png   · M1 聊天界面 AI 气泡已发 + 孩子空气泡光标闪 + 头像后缩 (巨标由 drawtext)
  02_m2_punch.png         · M2 淡出聊天背景 (反差大字全 drawtext)
  03_m3_dialogue.png      · M3 AI↔孩子气泡你来我往 3 轮 + ✓ 渐亮 (顶小字由 drawtext)
  04_m4_preview.png       · M4 三年龄卡 6-8/9-12/13-15 金角标 (段标由 drawtext)
  05_m5_age1.png          · M5 6-8 岁点餐气泡演示 + prompt 卡① (正文 baked · 段标 drawtext)
  06a_m6_age2_demo.png    · M6a 9-12 岁三句话气泡 + AI 先夸✓再纠一处 (段标 drawtext)
  06b_m6_age2_prompt.png  · M6b prompt 卡②独占全屏静帧 38pt (最强收藏 · 正文 baked)
  07_m7_age3.png          · M7 13-15 岁单话题气泡 + 影子跟读波形 + prompt 卡③居中 (baked)
  08_m8_anchor.png        · M8 ⏰20min 时钟卡 (价值锚大字全 drawtext)
  09_m9_boundary.png      · M9 边界三图标卡 时长/发音/把关 (大字由 drawtext)
  10_m10_cta.png          · M10 私信话术卡「孩子几岁·学到哪一步」框 (CTA 大字由 drawtext)

色板 (design_language.md 硬门 · gate_check_palette.py 蓝紫 H=240~290 <5%):
  cream_bg     #fdf3e8 (暖奶油底 · H30 · 区别 D06 简历暖白)
  pure_white   #ffffff
  ai_bubble    #d9f0e3 / 字 #1f6b45 (AI 薄荷绿 · H145)
  kid_bubble   #ffe4cf / 字 #7a4a2b (孩子暖橙 · H28)
  accent_red   #e05a3a (强调暖红橙 · H12 · 禁 #ff5252 粉红)
  pass_green   #2e9c5e (通过绿 ✓ · H145)
  star_gold    #f0a92e (星标金 · H38)
  ink          #2a2320 (墨字)
  muted        #8a7f72 (副文灰)
  禁: #bd93f9 · #ff79c6 · #8be9fd Dracula 三色 · 蓝紫渐变 · 多色蓝/紫 emoji (🤖🛡)

真实性/合规: 无第一人称英语老师 (fact_check R7) · prompt 卡为方法示例 · 无效果承诺 (R1)

用法:
  python3 pipeline/p004_video/gen_ui_w28d07.py

依赖: Chrome + macOS · headless=new
"""
from __future__ import annotations

import pathlib
import subprocess
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "publish" / "2026-W28" / "D07-家长陪孩子学英语" / "build" / "assets_ui"
OUT.mkdir(parents=True, exist_ok=True)

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
W, H = 1080, 1920

TOK = {
    "cream_bg": "#fdf3e8",
    "pure_white": "#ffffff",
    "ai_bubble": "#d9f0e3",
    "ai_text": "#1f6b45",
    "kid_bubble": "#ffe4cf",
    "kid_text": "#7a4a2b",
    "accent_red": "#e05a3a",
    "pass_green": "#2e9c5e",
    "star_gold": "#f0a92e",
    "ink": "#2a2320",
    "muted": "#8a7f72",
    "card_line": "#ecdcc8",
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
  font-family: "SF Pro Text", "Source Han Sans SC", "PingFang SC", sans-serif; }}
"""

# 复用: 聊天气泡组件 (AI 薄荷绿左 · 孩子暖橙右 · 头像用文字/安全 emoji 不用蓝紫多色)
BUBBLE_CSS = f"""
.chat {{ display: flex; flex-direction: column; gap: 30px; }}
.msg {{ display: flex; align-items: flex-end; gap: 18px; max-width: 82%; }}
.msg.ai {{ align-self: flex-start; }}
.msg.kid {{ align-self: flex-end; flex-direction: row-reverse; }}
.avatar {{ width: 78px; height: 78px; border-radius: 50%; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center; font-size: 42px; font-weight: 800; }}
.av-ai {{ background: {TOK['ai_bubble']}; color: {TOK['ai_text']}; }}
.av-kid {{ background: {TOK['kid_bubble']}; }}
.bubble {{ padding: 26px 32px; border-radius: 28px; font-size: 40px; line-height: 1.42; }}
.b-ai {{ background: {TOK['ai_bubble']}; color: {TOK['ai_text']}; border-bottom-left-radius: 8px; }}
.b-kid {{ background: {TOK['kid_bubble']}; color: {TOK['kid_text']}; border-bottom-right-radius: 8px; }}
.b-en {{ font-weight: 600; }}
.tick {{ color: {TOK['pass_green']}; font-weight: 900; font-size: 40px; margin-bottom: 6px; }}
"""

# prompt 卡 (金虚线框 · 长按截屏金标 · 正文 baked)
PROMPT_CSS = f"""
.pcard {{ background: {TOK['pure_white']}; border: 4px dashed {TOK['star_gold']};
  border-radius: 22px; padding: 46px 44px; box-shadow: 0 12px 44px rgba(0,0,0,0.10);
  position: relative; }}
.pcard-tag {{ position: absolute; top: -26px; left: 40px; background: {TOK['star_gold']};
  color: {TOK['pure_white']}; font-size: 28px; font-weight: 800; padding: 9px 24px;
  border-radius: 12px; }}
.pcard-star {{ position: absolute; top: -26px; right: 40px; background: {TOK['accent_red']};
  color: {TOK['pure_white']}; font-size: 26px; font-weight: 700; padding: 9px 22px;
  border-radius: 12px; }}
.pcard-title {{ font-size: 36px; font-weight: 800; color: {TOK['ink']}; margin-bottom: 22px;
  padding-bottom: 18px; border-bottom: 2px solid {TOK['card_line']}; }}
.pcard-body {{ font-size: 34px; line-height: 1.6; color: {TOK['ink']}; }}
.pcard-body b {{ color: {TOK['accent_red']}; }}
"""


# ═══ M1 · 3.5s · 聊天界面 AI 气泡已发 + 孩子空气泡光标闪 + 头像后缩 ═══
def gen_m1_chat_freeze() -> None:
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
{BASE_CSS}{BUBBLE_CSS}
body {{ background: {TOK['cream_bg']}; padding: 150px 70px 0; position: relative; }}
.appbar {{ text-align: center; font-size: 30px; color: {TOK['muted']}; font-weight: 600;
  margin-bottom: 46px; }}
.appbar b {{ color: {TOK['ai_text']}; }}
.kid-shrink {{ transform: translateX(46px); opacity: 0.9; }}
.empty-b {{ background: {TOK['kid_bubble']}; border-radius: 28px; border-bottom-right-radius: 8px;
  padding: 26px 34px; min-width: 150px; display: flex; align-items: center; }}
.cursor {{ width: 5px; height: 44px; background: {TOK['kid_text']}; display: inline-block;
  opacity: 0.55; }}
.nervous {{ position: absolute; font-size: 40px; }}
</style></head><body>
<div class="appbar">AI 英语陪练 · <b>随时能聊</b></div>
<div class="chat">
  <div class="msg ai">
    <div class="avatar av-ai">AI</div>
    <div class="bubble b-ai b-en">What did you do today?</div>
  </div>
  <div class="msg kid kid-shrink">
    <div class="avatar av-kid">🧒</div>
    <div class="empty-b"><span class="cursor"></span></div>
  </div>
</div>
</body></html>"""
    shot(html, "01_m1_chat_freeze.png")


# ═══ M2 · 6s · 淡出聊天背景 (反差大字全 drawtext) ═══
def gen_m2_punch() -> None:
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
{BASE_CSS}{BUBBLE_CSS}
body {{ background: {TOK['cream_bg']}; padding: 150px 70px 0; position: relative; }}
.chat {{ filter: grayscale(0.5); opacity: 0.16; }}
</style></head><body>
<div class="chat">
  <div class="msg ai"><div class="avatar av-ai">AI</div><div class="bubble b-ai b-en">Try again?</div></div>
  <div class="msg kid"><div class="avatar av-kid">🧒</div><div class="bubble b-kid">…</div></div>
  <div class="msg ai"><div class="avatar av-ai">AI</div><div class="bubble b-ai b-en">Take your time.</div></div>
</div>
</body></html>"""
    shot(html, "02_m2_punch.png")


# ═══ M3 · 6s · AI↔孩子气泡你来我往 3 轮 + ✓ 渐亮 ═══
def gen_m3_dialogue() -> None:
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
{BASE_CSS}{BUBBLE_CSS}
body {{ background: {TOK['cream_bg']}; padding: 200px 66px 0; }}
.msg.kid .tick {{ align-self: flex-end; }}
</style></head><body>
<div class="chat">
  <div class="msg ai"><div class="avatar av-ai">AI</div><div class="bubble b-ai b-en">What's your favorite fruit?</div></div>
  <div class="msg kid"><span class="tick">✓</span><div class="avatar av-kid">🧒</div><div class="bubble b-kid b-en">I like… apple!</div></div>
  <div class="msg ai"><div class="avatar av-ai">AI</div><div class="bubble b-ai b-en">Nice! Why apple?</div></div>
  <div class="msg kid"><span class="tick">✓</span><div class="avatar av-kid">🧒</div><div class="bubble b-kid b-en">It's sweet and red.</div></div>
  <div class="msg ai"><div class="avatar av-ai">AI</div><div class="bubble b-ai">很棒！再说一句试试～</div></div>
</div>
</body></html>"""
    shot(html, "03_m3_dialogue.png")


# ═══ M4 · 2.8s · 三年龄卡 6-8/9-12/13-15 金角标 ═══
def gen_m4_preview() -> None:
    ages = [("6-8 岁", "角色扮演", "点餐 · 买东西"),
            ("9-12 岁", "复述 + 三句话", "先夸 · 再纠一处"),
            ("13-15 岁", "单话题深聊", "影子跟读")]
    cards = ""
    for i, (age, play, sub) in enumerate(ages, 1):
        cards += f"""
    <div class="age-card">
      <div class="age-badge">{i}</div>
      <div class="age-num">{age}</div>
      <div class="age-play">{play}</div>
      <div class="age-sub">{sub}</div>
    </div>"""
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
{BASE_CSS}
body {{ background: {TOK['cream_bg']}; display: flex; flex-direction: column;
  justify-content: center; padding: 0 64px 340px; gap: 40px; }}
.age-card {{ background: {TOK['pure_white']}; border-radius: 22px; padding: 46px 50px;
  box-shadow: 0 10px 40px rgba(0,0,0,0.10); position: relative;
  border-left: 12px solid {TOK['accent_red']}; }}
.age-badge {{ position: absolute; top: -22px; right: 40px; width: 60px; height: 60px;
  border-radius: 50%; background: {TOK['star_gold']}; color: {TOK['pure_white']};
  font-size: 34px; font-weight: 900; display: flex; align-items: center; justify-content: center; }}
.age-num {{ font-size: 54px; font-weight: 900; color: {TOK['ink']}; }}
.age-play {{ font-size: 40px; font-weight: 700; color: {TOK['accent_red']}; margin: 10px 0 6px; }}
.age-sub {{ font-size: 30px; color: {TOK['muted']}; }}
</style></head><body>
{cards}
</body></html>"""
    shot(html, "04_m4_preview.png")


# ═══ M5 · 6.5s · 6-8 岁点餐气泡 + prompt 卡① (正文 baked) ═══
def gen_m5_age1() -> None:
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
{BASE_CSS}{BUBBLE_CSS}{PROMPT_CSS}
body {{ background: {TOK['cream_bg']}; padding: 210px 60px 0; }}
.scene-tag {{ display: inline-block; background: {TOK['kid_bubble']}; color: {TOK['kid_text']};
  font-size: 28px; font-weight: 700; padding: 10px 24px; border-radius: 30px; margin-bottom: 30px; }}
.chat {{ margin-bottom: 56px; }}
.bubble {{ font-size: 36px; }}
</style></head><body>
<div class="scene-tag">🍔 餐厅点餐 · 角色扮演</div>
<div class="chat">
  <div class="msg ai"><div class="avatar av-ai">AI</div><div class="bubble b-ai b-en">Hi! What would you like?</div></div>
  <div class="msg kid"><div class="avatar av-kid">🧒</div><div class="bubble b-kid b-en">A… hamburger, please.</div></div>
  <div class="msg ai"><div class="avatar av-ai">AI</div><div class="bubble b-ai b-en">Great! Anything to drink?</div></div>
</div>
<div class="pcard">
  <div class="pcard-tag">prompt ①</div>
  <div class="pcard-star">长按截屏</div>
  <div class="pcard-title">6-8 岁 · 角色扮演</div>
  <div class="pcard-body">你是餐厅服务员，用<b>最简单的英语</b>和我 6 岁孩子玩「点餐」。一次一句，他说错就温柔再示范一遍，多鼓励。</div>
</div>
</body></html>"""
    shot(html, "05_m5_age1.png")


# ═══ M6a · 3.8s · 9-12 岁三句话气泡 + AI 先夸✓再纠一处 ═══
def gen_m6a_age2_demo() -> None:
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
{BASE_CSS}{BUBBLE_CSS}
body {{ background: {TOK['cream_bg']}; padding: 210px 60px 0; }}
.scene-tag {{ display: inline-block; background: {TOK['ai_bubble']}; color: {TOK['ai_text']};
  font-size: 28px; font-weight: 700; padding: 10px 24px; border-radius: 30px; margin-bottom: 34px; }}
.b-praise {{ border: 3px solid {TOK['pass_green']}; }}
.fix-row {{ background: {TOK['pure_white']}; border-left: 8px solid {TOK['star_gold']};
  border-radius: 14px; padding: 22px 28px; font-size: 34px; color: {TOK['ink']};
  margin-top: 8px; max-width: 82%; align-self: flex-start; }}
.fix-row b {{ color: {TOK['accent_red']}; }}
</style></head><body>
<div class="scene-tag">📖 三句话说今天</div>
<div class="chat">
  <div class="msg kid"><div class="avatar av-kid">🧒</div><div class="bubble b-kid b-en">Today I go to school. I play. I eat noodle.</div></div>
  <div class="msg ai"><div class="avatar av-ai">AI</div><div class="bubble b-ai b-praise">Good job! 三句话都说出来啦 👍</div></div>
  <div class="fix-row">只纠一处：<b>go → went</b>（昨天用过去式）</div>
</div>
</body></html>"""
    shot(html, "06a_m6_age2_demo.png")


# ═══ M6b · 3.7s · prompt 卡②独占全屏静帧 38pt (最强收藏) ═══
def gen_m6b_age2_prompt() -> None:
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
{BASE_CSS}{PROMPT_CSS}
body {{ background: {TOK['cream_bg']}; display: flex; flex-direction: column;
  justify-content: center; align-items: center; padding: 200px 64px 120px; }}
.pcard {{ width: 100%; padding: 64px 56px; }}
.pcard-title {{ font-size: 44px; }}
.pcard-body {{ font-size: 38px; line-height: 1.7; }}
.save-hint {{ margin-top: 44px; text-align: center; font-size: 30px; color: {TOK['muted']}; }}
.save-hint b {{ color: {TOK['accent_red']}; }}
</style></head><body>
<div class="pcard">
  <div class="pcard-tag">prompt ②</div>
  <div class="pcard-star">长按截屏</div>
  <div class="pcard-title">9-12 岁 · 复述 + 三句话</div>
  <div class="pcard-body">用简单英语问我孩子今天做了什么，让他<b>用三句话</b>回答。说完先真诚夸一句，<b>再只纠正一个</b>最明显的错误，然后请他重说一遍。</div>
</div>
<div class="save-hint">这条最值得 <b>收藏</b> · 每天照着用</div>
</body></html>"""
    shot(html, "06b_m6_age2_prompt.png")


# ═══ M7 · 6.8s · 13-15 岁单话题气泡 + 影子跟读波形 + prompt 卡居中 ═══
def gen_m7_age3() -> None:
    bars = ""
    heights = [30, 58, 44, 72, 50, 88, 62, 40, 76, 54, 68, 34, 60, 82, 46, 70, 38, 64, 52, 78]
    for hgt in heights:
        bars += f'<div class="bar" style="height:{hgt}px;"></div>'
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
{BASE_CSS}{BUBBLE_CSS}{PROMPT_CSS}
body {{ background: {TOK['cream_bg']}; padding: 200px 60px 0; }}
.scene-tag {{ display: inline-block; background: {TOK['kid_bubble']}; color: {TOK['kid_text']};
  font-size: 28px; font-weight: 700; padding: 10px 24px; border-radius: 30px; margin-bottom: 28px; }}
.chat {{ margin-bottom: 34px; }}
.bubble {{ font-size: 34px; }}
.wave {{ display: flex; align-items: center; justify-content: center; gap: 8px; height: 110px;
  background: {TOK['pure_white']}; border-radius: 18px; padding: 0 30px; margin-bottom: 40px;
  box-shadow: 0 6px 24px rgba(0,0,0,0.06); }}
.wave-label {{ font-size: 26px; color: {TOK['ai_text']}; font-weight: 700; margin-right: 14px; white-space: nowrap; }}
.bar {{ width: 10px; background: {TOK['pass_green']}; border-radius: 5px; opacity: 0.85; }}
.pcard {{ padding: 40px 42px; }}
.pcard-body {{ font-size: 32px; }}
</style></head><body>
<div class="scene-tag">🎮 单话题深聊 · 最喜欢的游戏</div>
<div class="chat">
  <div class="msg ai"><div class="avatar av-ai">AI</div><div class="bubble b-ai b-en">Which game do you like most, and why?</div></div>
  <div class="msg kid"><div class="avatar av-kid">🧒</div><div class="bubble b-kid b-en">I like it because I can play with friends.</div></div>
</div>
<div class="wave"><span class="wave-label">影子跟读</span>{bars}</div>
<div class="pcard">
  <div class="pcard-tag">prompt ③</div>
  <div class="pcard-star">长按截屏</div>
  <div class="pcard-title">13-15 岁 · 单话题 + 影子跟读</div>
  <div class="pcard-body">就他<b>最感兴趣的一个话题</b>用英语聊下去，随时纠发音语法。每聊几句，带他把你的话<b>跟读一遍</b>。</div>
</div>
</body></html>"""
    shot(html, "07_m7_age3.png")


# ═══ M8 · 4s · ⏰20min 时钟卡 (价值锚大字全 drawtext) ═══
def gen_m8_anchor() -> None:
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
{BASE_CSS}
body {{ background: {TOK['cream_bg']}; display: flex; justify-content: center;
  align-items: flex-start; padding-top: 300px; }}
.clock-pill {{ background: {TOK['pure_white']}; border-radius: 28px; padding: 40px 64px;
  box-shadow: 0 12px 44px rgba(0,0,0,0.10); display: flex; align-items: center; gap: 30px;
  border: 4px solid {TOK['star_gold']}; }}
.clock-emoji {{ font-size: 96px; }}
.clock-num {{ font-size: 108px; font-weight: 900; color: {TOK['accent_red']}; line-height: 1; }}
.clock-unit {{ font-size: 40px; color: {TOK['muted']}; font-weight: 700; margin-top: 14px; }}
</style></head><body>
<div class="clock-pill">
  <div class="clock-emoji">⏰</div>
  <div><div class="clock-num">20<span style="font-size:52px;"> min</span></div>
  <div class="clock-unit">每天 · 在家陪聊</div></div>
</div>
</body></html>"""
    shot(html, "08_m8_anchor.png")


# ═══ M9 · 5.2s · 边界三图标卡 时长/发音/把关 (大字由 drawtext) ═══
def gen_m9_boundary() -> None:
    items = [("⏰", "时长把关", "家长定每天多久"),
             ("👂", "发音参考", "AI 陪练不替课"),
             ("✋", "话题把关", "聊什么家长说了算")]
    cards = ""
    for emoji, title, sub in items:
        cards += f"""
    <div class="bd-card">
      <div class="bd-emoji">{emoji}</div>
      <div class="bd-title">{title}</div>
      <div class="bd-sub">{sub}</div>
    </div>"""
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
{BASE_CSS}
body {{ background: {TOK['cream_bg']}; display: flex; align-items: flex-end;
  justify-content: center; padding: 0 50px 300px; }}
.bd-row {{ display: flex; gap: 26px; width: 100%; }}
.bd-card {{ flex: 1; background: {TOK['pure_white']}; border-radius: 20px; padding: 40px 20px;
  box-shadow: 0 8px 30px rgba(0,0,0,0.09); text-align: center; border-top: 8px solid {TOK['pass_green']}; }}
.bd-emoji {{ font-size: 72px; margin-bottom: 20px; }}
.bd-title {{ font-size: 36px; font-weight: 800; color: {TOK['ink']}; margin-bottom: 12px; }}
.bd-sub {{ font-size: 26px; color: {TOK['muted']}; line-height: 1.4; }}
</style></head><body>
<div class="bd-row">{cards}</div>
</body></html>"""
    shot(html, "09_m9_boundary.png")


# ═══ M10 · 5s · 私信话术卡「孩子几岁·学到哪一步」框 (CTA 大字由 drawtext) ═══
def gen_m10_cta() -> None:
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
{BASE_CSS}
body {{ background: {TOK['cream_bg']}; position: relative; }}
.dm-card {{ position: absolute; left: 80px; right: 80px; top: 1180px;
  background: {TOK['pure_white']}; border: 4px solid {TOK['accent_red']}; border-radius: 24px;
  padding: 44px 46px; box-shadow: 0 12px 44px rgba(0,0,0,0.12); }}
.dm-tag {{ position: absolute; top: -26px; left: 44px; background: {TOK['accent_red']};
  color: {TOK['pure_white']}; font-size: 28px; font-weight: 800; padding: 10px 26px; border-radius: 12px; }}
.dm-row {{ display: flex; align-items: center; gap: 20px; margin-top: 12px; }}
.dm-fill {{ flex: 1; background: {TOK['cream_bg']}; border-radius: 16px; padding: 26px 30px;
  font-size: 40px; color: {TOK['ink']}; font-weight: 700; }}
.dm-fill b {{ color: {TOK['accent_red']}; }}
.dm-send {{ width: 78px; height: 78px; border-radius: 50%; background: {TOK['accent_red']};
  color: {TOK['pure_white']}; font-size: 40px; display: flex; align-items: center;
  justify-content: center; flex-shrink: 0; }}
</style></head><body>
<div class="dm-card">
  <div class="dm-tag">私信这句</div>
  <div class="dm-row">
    <div class="dm-fill">孩子<b>〔几岁〕</b>· 学到<b>〔哪一步〕</b></div>
    <div class="dm-send">➤</div>
  </div>
</div>
</body></html>"""
    shot(html, "10_m10_cta.png")


def main() -> None:
    print(f"→ W28D07 UI PNG 生成 · out={OUT}")
    gen_m1_chat_freeze()
    gen_m2_punch()
    gen_m3_dialogue()
    gen_m4_preview()
    gen_m5_age1()
    gen_m6a_age2_demo()
    gen_m6b_age2_prompt()
    gen_m7_age3()
    gen_m8_anchor()
    gen_m9_boundary()
    gen_m10_cta()
    print(f"✓ 11 张 UI PNG 全生成 · {OUT}")


if __name__ == "__main__":
    main()
