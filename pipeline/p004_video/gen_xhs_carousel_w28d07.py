#!/usr/bin/env python3
"""W28D07 xhs 7 页图文轮播 PNG 生成 · Chrome headless.

form_strategy 判定 xhs 首选图文轮播（收藏权重 > 完播 · "抄下来" > "看下来"）。
选题: 家长陪孩子学英语 · 3 年龄段 AI 陪练 prompt 卡为收藏核心（可截图照抄）。

H6 差异化 (vs D06 简历纸面): 暖奶油 #fdf3e8 聊天气泡 · AI 薄荷绿↔孩子暖橙 · 无简历/扫描线。
每页自带大字（图文轮播无字幕 · 大字即信息）· 3 张 prompt 卡为收藏动机核心。

页面:
  p1_cover.png        封面 · 聊天气泡孩子不敢开口 + 钩子「不是不努力·缺个陪练」
  p2_why.png          为什么又报班没用 · 缺的是陪聊说错不尴尬的人 · AI 正好能干
  p3_three_ages.png   三年龄段预告 · 3 格 6-8/9-12/13-15
  p4_age1_prompt.png  6-8 岁 角色扮演 · 点餐气泡 + prompt 卡①（收藏）
  p5_age2_prompt.png  9-12 岁 复述+三句话 · 先夸再纠一处 + prompt 卡②（最强收藏帧）
  p6_age3_prompt.png  13-15 岁 单话题+影子跟读 + prompt 卡③（收藏）
  p7_boundary_cta.png 边界（陪练不替课·家长把关·每天20min）+ CTA（私信孩子几岁·学到哪一步）

色板 (同 gen_ui_w28d07 · design_language.md 硬门):
  cream_bg #fdf3e8 · pure_white #ffffff · ai_bubble #d9f0e3/字 #1f6b45 · kid_bubble #ffe4cf/字 #7a4a2b
  accent_red #e05a3a · pass_green #2e9c5e · star_gold #f0a92e · ink #2a2320 · muted #8a7f72
  禁: #bd93f9 · #ff79c6 · #8be9fd · 蓝紫渐变 · 多色蓝/紫 emoji (🤖🛡)

真实性/合规 (fact_check R1/R7): 无第一人称英语老师 · prompt 卡为方法示例 · 效果只说"敢开口"非承诺
  · 不贬低培训班 · 不售卖/导流 K12 课程

用法:
  python3 pipeline/p004_video/gen_xhs_carousel_w28d07.py
  # 跑完立即: for p in publish/.../xhs/pages/*.png; do python3 pipeline/gate_check_palette.py "$p"; done
"""
from __future__ import annotations

import pathlib
import subprocess
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "publish" / "2026-W28" / "D07-家长陪孩子学英语" / "xhs" / "pages"
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
  font-family: "SF Pro Text", "Source Han Sans SC", "PingFang SC", sans-serif;
  background: {TOK['cream_bg']}; color: {TOK['ink']}; }}
.page-tag {{ position: absolute; top: 56px; right: 60px; font-size: 26px;
  color: {TOK['muted']}; opacity: 0.7; letter-spacing: 2px; font-weight: 700; }}
"""

# 聊天气泡组件 (复用视频侧组件)
BUBBLE_CSS = f"""
.chat {{ display: flex; flex-direction: column; gap: 26px; }}
.msg {{ display: flex; align-items: flex-end; gap: 16px; max-width: 84%; }}
.msg.ai {{ align-self: flex-start; }}
.msg.kid {{ align-self: flex-end; flex-direction: row-reverse; }}
.avatar {{ width: 72px; height: 72px; border-radius: 50%; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center; font-size: 38px; font-weight: 800; }}
.av-ai {{ background: {TOK['ai_bubble']}; color: {TOK['ai_text']}; }}
.av-kid {{ background: {TOK['kid_bubble']}; }}
.bubble {{ padding: 24px 30px; border-radius: 26px; font-size: 36px; line-height: 1.4; }}
.b-ai {{ background: {TOK['ai_bubble']}; color: {TOK['ai_text']}; border-bottom-left-radius: 8px; }}
.b-kid {{ background: {TOK['kid_bubble']}; color: {TOK['kid_text']}; border-bottom-right-radius: 8px; }}
.b-en {{ font-weight: 600; }}
.tick {{ color: {TOK['pass_green']}; font-weight: 900; font-size: 36px; margin-bottom: 6px; }}
"""

# prompt 卡 (金虚线框 · 长按截屏金标 · 正文 baked · 收藏核心)
PROMPT_CSS = f"""
.pcard {{ background: {TOK['pure_white']}; border: 4px dashed {TOK['star_gold']};
  border-radius: 22px; padding: 50px 46px; box-shadow: 0 12px 44px rgba(0,0,0,0.10);
  position: relative; }}
.pcard-tag {{ position: absolute; top: -26px; left: 40px; background: {TOK['star_gold']};
  color: {TOK['pure_white']}; font-size: 30px; font-weight: 800; padding: 10px 26px;
  border-radius: 12px; }}
.pcard-star {{ position: absolute; top: -26px; right: 40px; background: {TOK['accent_red']};
  color: {TOK['pure_white']}; font-size: 28px; font-weight: 700; padding: 10px 24px;
  border-radius: 12px; }}
.pcard-title {{ font-size: 40px; font-weight: 800; color: {TOK['ink']}; margin-bottom: 24px;
  padding-bottom: 20px; border-bottom: 2px solid {TOK['card_line']}; }}
.pcard-body {{ font-size: 38px; line-height: 1.65; color: {TOK['ink']}; }}
.pcard-body b {{ color: {TOK['accent_red']}; }}
"""


def page(body: str, extra_css: str = "", tag: str = "") -> str:
    tag_html = f'<div class="page-tag">{tag}</div>' if tag else ""
    return (f'<!DOCTYPE html><html><head><meta charset="utf-8"><style>{BASE_CSS}{extra_css}'
            f'</style></head><body>{tag_html}{body}</body></html>')


# ═══ P1 · 封面 · 聊天气泡孩子不敢开口 + 钩子 ═══
def gen_p1_cover() -> None:
    css = BUBBLE_CSS + f"""
body {{ display: flex; flex-direction: column; justify-content: center;
  padding: 0 78px; position: relative; }}
.appbar {{ text-align: center; font-size: 28px; color: {TOK['muted']}; font-weight: 600;
  margin-bottom: 40px; }}
.appbar b {{ color: {TOK['ai_text']}; }}
.empty-b {{ background: {TOK['kid_bubble']}; border-radius: 26px; border-bottom-right-radius: 8px;
  padding: 24px 32px; min-width: 140px; display: flex; align-items: center; }}
.cursor {{ width: 5px; height: 40px; background: {TOK['kid_text']}; display: inline-block;
  opacity: 0.55; }}
.kid-shrink {{ transform: translateX(40px); opacity: 0.9; }}
.headline {{ margin-top: 90px; text-align: center; }}
.headline .l {{ font-size: 80px; font-weight: 900; line-height: 1.34; color: {TOK['ink']}; }}
.headline .em {{ color: {TOK['accent_red']}; }}
.sub {{ margin-top: 40px; font-size: 34px; color: {TOK['muted']}; text-align: center; line-height: 1.5; }}
"""
    body = f"""
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
<div class="headline">
  <div class="l">报了两年班</div>
  <div class="l"><span class="em">一开口还是往后缩</span></div>
</div>
<div class="sub">不是不努力 · 缺个能陪他瞎聊、说错不尴尬的人</div>
"""
    shot(page(body, css, "1/7"), "p1_cover.png")


# ═══ P2 · 为什么又报班没用 · AI 正好能干 ═══
def gen_p2_why() -> None:
    css = f"""
body {{ display: flex; flex-direction: column; justify-content: center; padding: 0 80px; }}
.head {{ font-size: 62px; font-weight: 900; line-height: 1.4; margin-bottom: 60px; }}
.head .em {{ color: {TOK['accent_red']}; }}
.card {{ background: {TOK['pure_white']}; border-radius: 20px; padding: 52px 48px;
  box-shadow: 0 10px 40px rgba(0,0,0,0.10); }}
.row {{ display: flex; align-items: flex-start; gap: 22px; margin: 26px 0; }}
.dot {{ width: 44px; height: 44px; border-radius: 50%; background: {TOK['ai_bubble']};
  color: {TOK['ai_text']}; font-size: 26px; font-weight: 900; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center; }}
.rt {{ font-size: 36px; color: {TOK['ink']}; font-weight: 600; line-height: 1.45; }}
.rt b {{ color: {TOK['ai_text']}; }}
.foot {{ margin-top: 56px; font-size: 36px; color: {TOK['ink']}; font-weight: 800;
  text-align: center; line-height: 1.6; }}
.foot .em {{ color: {TOK['accent_red']}; }}
"""
    body = f"""
<div class="head">缺的不是又一个班<br/><span class="em">是个陪练</span></div>
<div class="card">
  <div class="row"><div class="dot">1</div><div class="rt"><b>不会不耐烦</b> · 说一百遍也不叹气</div></div>
  <div class="row"><div class="dot">2</div><div class="rt"><b>随时能练</b> · 饭后十分钟就开聊</div></div>
  <div class="row"><div class="dot">3</div><div class="rt"><b>说错不批评</b> · 敢说错才敢开口</div></div>
</div>
<div class="foot">这事 AI 正好能干 · <span class="em">按年龄三套玩法</span></div>
"""
    shot(page(body, css, "2/7"), "p2_why.png")


# ═══ P3 · 三年龄段预告 · 3 格 ═══
def gen_p3_three_ages() -> None:
    ages = [
        ("6-8 岁", "角色扮演", "点餐 · 买东西 · 你来我往"),
        ("9-12 岁", "复述 + 三句话", "先夸 · 再只纠一处"),
        ("13-15 岁", "单话题深聊", "随时纠 · 影子跟读"),
    ]
    cards = ""
    for i, (age, play, sub) in enumerate(ages, 1):
        cards += f"""
<div class="card">
  <div class="badge">{i}</div>
  <div class="card-body"><div class="num">{age}</div>
    <div class="play">{play}</div><div class="sub">{sub}</div></div>
</div>"""
    css = f"""
body {{ display: flex; flex-direction: column; justify-content: center; padding: 0 74px; }}
.head {{ font-size: 62px; font-weight: 900; margin-bottom: 60px; line-height: 1.4; }}
.head .em {{ color: {TOK['accent_red']}; }}
.card {{ display: flex; align-items: center; gap: 34px; background: {TOK['pure_white']};
  border-left: 12px solid {TOK['accent_red']}; border-radius: 20px; padding: 42px 40px; margin: 22px 0;
  box-shadow: 0 6px 24px rgba(0,0,0,0.10); position: relative; }}
.badge {{ width: 60px; height: 60px; border-radius: 50%; background: {TOK['star_gold']};
  color: {TOK['pure_white']}; font-size: 34px; font-weight: 900; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center; }}
.num {{ font-size: 48px; font-weight: 900; color: {TOK['ink']}; }}
.play {{ font-size: 36px; font-weight: 700; color: {TOK['accent_red']}; margin: 8px 0 4px; }}
.sub {{ font-size: 27px; color: {TOK['muted']}; }}
.card-body {{ flex: 1; }}
"""
    body = f"""
<div class="head">按年龄 · <span class="em">三套现成玩法</span><br/>每天 20 分钟</div>
{cards}
"""
    shot(page(body, css, "3/7"), "p3_three_ages.png")


# ═══ P4 · 6-8 岁 角色扮演 · 点餐气泡 + prompt 卡① ═══
def gen_p4_age1_prompt() -> None:
    css = BUBBLE_CSS + PROMPT_CSS + f"""
body {{ display: flex; flex-direction: column; justify-content: center; padding: 0 62px; }}
.scene-tag {{ display: inline-block; align-self: flex-start; background: {TOK['kid_bubble']};
  color: {TOK['kid_text']}; font-size: 28px; font-weight: 700; padding: 10px 24px;
  border-radius: 30px; margin-bottom: 30px; }}
.chat {{ margin-bottom: 54px; }}
.bubble {{ font-size: 34px; }}
"""
    body = f"""
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
"""
    shot(page(body, css, "4/7"), "p4_age1_prompt.png")


# ═══ P5 · 9-12 岁 复述+三句话 · 先夸再纠 + prompt 卡②（最强收藏帧）═══
def gen_p5_age2_prompt() -> None:
    css = PROMPT_CSS + f"""
body {{ display: flex; flex-direction: column; justify-content: center; padding: 0 62px; }}
.scene-tag {{ display: inline-block; align-self: flex-start; background: {TOK['ai_bubble']};
  color: {TOK['ai_text']}; font-size: 28px; font-weight: 700; padding: 10px 24px;
  border-radius: 30px; margin-bottom: 30px; }}
.demo {{ display: flex; flex-direction: column; gap: 18px; margin-bottom: 50px; }}
.d-praise {{ background: {TOK['ai_bubble']}; border: 3px solid {TOK['pass_green']};
  color: {TOK['ai_text']}; border-radius: 20px; padding: 22px 28px; font-size: 34px; font-weight: 600; }}
.fix-row {{ background: {TOK['pure_white']}; border-left: 8px solid {TOK['star_gold']};
  border-radius: 14px; padding: 22px 28px; font-size: 32px; color: {TOK['ink']}; }}
.fix-row b {{ color: {TOK['accent_red']}; }}
"""
    body = f"""
<div class="scene-tag">📖 三句话说今天 · 先夸再纠</div>
<div class="demo">
  <div class="d-praise">✓ Good job！三句话都说出来啦 👍</div>
  <div class="fix-row">只纠一处：<b>go → went</b>（说昨天用过去式）</div>
</div>
<div class="pcard">
  <div class="pcard-tag">prompt ②</div>
  <div class="pcard-star">最值得收藏</div>
  <div class="pcard-title">9-12 岁 · 复述 + 三句话</div>
  <div class="pcard-body">用简单英语问我孩子今天做了什么，让他<b>用三句话</b>回答。说完先真诚夸一句，<b>再只纠正一个</b>最明显的错误，然后请他重说一遍。</div>
</div>
"""
    shot(page(body, css, "5/7"), "p5_age2_prompt.png")


# ═══ P6 · 13-15 岁 单话题+影子跟读 + prompt 卡③ ═══
def gen_p6_age3_prompt() -> None:
    bars = ""
    heights = [24, 46, 34, 58, 40, 70, 50, 32, 62, 42, 54, 28, 48, 66, 36, 56, 30, 52, 42, 60]
    for hgt in heights:
        bars += f'<div class="bar" style="height:{hgt}px;"></div>'
    css = BUBBLE_CSS + PROMPT_CSS + f"""
body {{ display: flex; flex-direction: column; justify-content: center; padding: 0 62px; }}
.scene-tag {{ display: inline-block; align-self: flex-start; background: {TOK['kid_bubble']};
  color: {TOK['kid_text']}; font-size: 28px; font-weight: 700; padding: 10px 24px;
  border-radius: 30px; margin-bottom: 28px; }}
.chat {{ margin-bottom: 26px; }}
.bubble {{ font-size: 32px; }}
.wave {{ display: flex; align-items: center; justify-content: center; gap: 7px; height: 96px;
  background: {TOK['pure_white']}; border-radius: 16px; padding: 0 28px; margin-bottom: 44px;
  box-shadow: 0 6px 24px rgba(0,0,0,0.06); }}
.wave-label {{ font-size: 26px; color: {TOK['ai_text']}; font-weight: 700; margin-right: 12px; white-space: nowrap; }}
.bar {{ width: 9px; background: {TOK['pass_green']}; border-radius: 5px; opacity: 0.85; }}
.pcard-body {{ font-size: 36px; }}
"""
    body = f"""
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
"""
    shot(page(body, css, "6/7"), "p6_age3_prompt.png")


# ═══ P7 · 边界 + CTA ═══
def gen_p7_boundary_cta() -> None:
    css = f"""
body {{ display: flex; flex-direction: column; justify-content: center; align-items: center;
  padding: 0 78px; text-align: center; }}
.bd-row {{ display: flex; gap: 22px; width: 100%; margin-bottom: 60px; }}
.bd-card {{ flex: 1; background: {TOK['pure_white']}; border-radius: 18px; padding: 36px 16px;
  box-shadow: 0 8px 30px rgba(0,0,0,0.09); border-top: 8px solid {TOK['pass_green']}; }}
.bd-emoji {{ font-size: 60px; margin-bottom: 16px; }}
.bd-t {{ font-size: 32px; font-weight: 800; color: {TOK['ink']}; margin-bottom: 8px; }}
.bd-s {{ font-size: 24px; color: {TOK['muted']}; line-height: 1.4; }}
.yes {{ font-size: 62px; font-weight: 900; line-height: 1.4; color: {TOK['ink']}; }}
.yes .em {{ color: {TOK['pass_green']}; }}
.cta {{ margin-top: 70px; width: 100%; background: {TOK['pure_white']};
  border: 4px solid {TOK['accent_red']}; border-radius: 22px; padding: 46px 44px;
  box-shadow: 0 10px 36px rgba(0,0,0,0.12); }}
.cta-t {{ font-size: 44px; font-weight: 900; color: {TOK['ink']}; line-height: 1.4; }}
.cta-t .kw {{ color: {TOK['accent_red']}; }}
.cta-s {{ font-size: 30px; color: {TOK['muted']}; margin-top: 20px; }}
"""
    body = f"""
<div class="bd-row">
  <div class="bd-card"><div class="bd-emoji">⏰</div><div class="bd-t">时长把关</div><div class="bd-s">家长定每天多久</div></div>
  <div class="bd-card"><div class="bd-emoji">👂</div><div class="bd-t">陪练不替课</div><div class="bd-s">AI 是陪练不替课</div></div>
  <div class="bd-card"><div class="bd-emoji">✋</div><div class="bd-t">话题把关</div><div class="bd-s">聊什么家长说了算</div></div>
</div>
<div class="yes">重点是<span class="em">敢开口</span><br/>不是背多少</div>
<div class="cta">
  <div class="cta-t">私信「<span class="kw">孩子几岁 · 学到哪一步</span>」</div>
  <div class="cta-s">我把这三套玩法发你 · 不用报付费课</div>
</div>
"""
    shot(page(body, css, "7/7"), "p7_boundary_cta.png")


def main() -> None:
    print(f"→ W28D07 xhs 7 页轮播生成 · out={OUT}")
    gen_p1_cover()
    gen_p2_why()
    gen_p3_three_ages()
    gen_p4_age1_prompt()
    gen_p5_age2_prompt()
    gen_p6_age3_prompt()
    gen_p7_boundary_cta()
    print(f"✓ 7 页全生成 · {OUT}")
    print("下一步 · palette gate 逐张:")
    print(f'  for p in "{OUT}"/*.png; do python3 pipeline/gate_check_palette.py "$p"; done')


if __name__ == "__main__":
    main()
