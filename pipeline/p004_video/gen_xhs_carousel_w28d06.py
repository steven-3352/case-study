#!/usr/bin/env python3
"""W28D06 xhs 7 页图文轮播 PNG 生成 · Chrome headless.

form_strategy 判定 xhs 首选图文轮播（收藏权重 > 完播 · "抄下来" > "看下来"）。
选题: AI 改简历不用找人改 · 简历纸面 + HR 扫描 + before/after 三处硬伤对照。

H6 差异化 (vs D05 暗夜主题): 暖白纸面 #f5f0e6 · 简历文档质感 · 无睡姿场景。
每页自带大字（图文轮播无字幕 · 大字即信息）· 3 处硬伤对照为收藏动机核心。

页面:
  p1_cover.png        封面 · 简历 + 已读不回红戳 + 钩子「不是文笔·是没被看到」
  p2_hr_scan.png      HR 视角 · 只有几秒 · 扫描概念（为什么被刷）
  p3_three_flaws.png  三处硬伤预告 · 反面三格（意向空/没数字/没关键词）
  p4_fix1_intent.png  第一处 求职意向 · before/after 分屏（收藏）
  p5_fix2_numbers.png 第二处 成果数字 · 对照句卡（最强收藏帧 · 可截图照抄）
  p6_fix3_ats.png     第三处 ATS 关键词 · 8 格命中 + 补词
  p7_boundary_cta.png 边界（数字填真的别编）+ CTA（私信发我简历）

色板 (同 gen_ui_w28d06 · design_language.md 硬门):
  paper_bg #f5f0e6 · pure_white #ffffff · ink #1a1a1a · hard_red #e53935
  pass_green #2e7d32 · scan_amber #d98c00 · muted #6b6b6b · grey_line #d8d0c0
  禁: #bd93f9 · #ff79c6 · #8be9fd · 蓝紫渐变 · linear-gradient 蓝紫端

真实性: 简历全化名「示例·化名·陈默」· 数字为示例占位

用法:
  python3 pipeline/p004_video/gen_xhs_carousel_w28d06.py
  # 跑完立即: for p in publish/.../xhs/pages/*.png; do python3 pipeline/gate_check_palette.py "$p"; done
"""
from __future__ import annotations

import pathlib
import subprocess
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "publish" / "2026-W28" / "D06-AI改简历不用找人改" / "xhs" / "pages"
OUT.mkdir(parents=True, exist_ok=True)

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
W, H = 1080, 1920

TOK = {
    "paper_bg": "#f5f0e6",
    "pure_white": "#ffffff",
    "ui_frame": "#14171c",
    "ink": "#1a1a1a",
    "ink_soft": "#33312c",
    "hard_red": "#e53935",
    "pass_green": "#2e7d32",
    "scan_amber": "#d98c00",
    "muted": "#6b6b6b",
    "grey_line": "#d8d0c0",
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
  font-family: -apple-system, "PingFang SC", "SF Pro Text", sans-serif;
  background: {TOK['paper_bg']}; color: {TOK['ink']}; }}
.page-tag {{ position: absolute; top: 56px; right: 60px; font-size: 26px;
  color: {TOK['muted']}; opacity: 0.7; letter-spacing: 2px; font-weight: 700; }}
"""


def page(body: str, extra_css: str = "", tag: str = "") -> str:
    tag_html = f'<div class="page-tag">{tag}</div>' if tag else ""
    return (f'<!DOCTYPE html><html><head><meta charset="utf-8"><style>{BASE_CSS}{extra_css}'
            f'</style></head><body>{tag_html}{body}</body></html>')


# ═══ P1 · 封面 · 简历 + 已读不回红戳 + 钩子 ═══
def gen_p1_cover() -> None:
    css = f"""
body {{ display: flex; flex-direction: column; justify-content: center; align-items: center;
  padding: 0 80px; position: relative; }}
.resume {{ background: {TOK['pure_white']}; border-radius: 16px; width: 100%;
  padding: 50px 48px; box-shadow: 0 14px 46px rgba(0,0,0,0.16); position: relative; }}
.watermark {{ position: absolute; top: 20px; right: 26px; font-size: 22px; color: {TOK['muted']}; }}
.r-name {{ font-size: 52px; font-weight: 800; color: {TOK['ink']}; letter-spacing: 3px; }}
.r-line {{ height: 18px; background: {TOK['grey_line']}; border-radius: 4px; margin: 20px 0;
  opacity: 0.7; }}
.r-line.short {{ width: 45%; }} .r-line.mid {{ width: 70%; }}
.stamp {{ position: absolute; top: 200px; left: 50%; transform: translateX(-50%) rotate(-11deg);
  border: 7px solid {TOK['hard_red']}; color: {TOK['hard_red']}; font-size: 66px; font-weight: 900;
  padding: 14px 38px; border-radius: 14px; letter-spacing: 5px; opacity: 0.92; }}
.headline {{ margin-top: 90px; text-align: center; }}
.headline .l {{ font-size: 82px; font-weight: 900; line-height: 1.34; color: {TOK['ink']}; }}
.headline .em {{ color: {TOK['hard_red']}; }}
.sub {{ margin-top: 40px; font-size: 34px; color: {TOK['muted']}; text-align: center; }}
"""
    body = f"""
<div class="resume">
  <div class="watermark">示例 · 化名 · 陈默</div>
  <div class="r-name">陈 默</div>
  <div class="r-line mid"></div>
  <div class="r-line short"></div>
  <div class="r-line"></div>
  <div class="r-line mid"></div>
  <div class="stamp">已读不回</div>
</div>
<div class="headline">
  <div class="l">投了很多份</div>
  <div class="l"><span class="em">全是已读不回</span></div>
</div>
<div class="sub">多半不是文笔差 · 是没被 HR 看到</div>
"""
    shot(page(body, css, "1/7"), "p1_cover.png")


# ═══ P2 · HR 视角 · 只有几秒 ═══
def gen_p2_hr_scan() -> None:
    css = f"""
body {{ display: flex; flex-direction: column; justify-content: center; padding: 0 80px; }}
.head {{ font-size: 64px; font-weight: 900; line-height: 1.4; margin-bottom: 70px; }}
.head .em {{ color: {TOK['scan_amber']}; }}
.card {{ background: {TOK['pure_white']}; border-radius: 20px; padding: 60px 54px;
  box-shadow: 0 10px 40px rgba(0,0,0,0.14); position: relative; overflow: hidden; }}
.scan-band {{ position: absolute; left: 0; right: 0; top: 190px; height: 92px;
  background: rgba(217,140,0,0.16); border-top: 3px solid {TOK['scan_amber']};
  border-bottom: 3px solid {TOK['scan_amber']}; }}
.row {{ display: flex; align-items: center; gap: 22px; margin: 30px 0; position: relative; z-index: 2; }}
.dot {{ width: 40px; height: 40px; border-radius: 50%; background: {TOK['scan_amber']};
  color: {TOK['pure_white']}; font-size: 24px; font-weight: 800; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center; }}
.rt {{ font-size: 34px; color: {TOK['ink_soft']}; font-weight: 600; }}
.foot {{ margin-top: 60px; font-size: 34px; color: {TOK['ink']}; font-weight: 700;
  text-align: center; line-height: 1.6; }}
.foot .em {{ color: {TOK['hard_red']}; }}
"""
    body = f"""
<div class="head">HR 初筛一份简历<br/><span class="em">只有几秒到几十秒</span></div>
<div class="card">
  <div class="scan-band"></div>
  <div class="row"><div class="dot">1</div><div class="rt">求职意向 —— 你要哪个岗？</div></div>
  <div class="row"><div class="dot">2</div><div class="rt">工作成果 —— 有没有数字？</div></div>
  <div class="row"><div class="dot">3</div><div class="rt">岗位关键词 —— 机器先筛</div></div>
</div>
<div class="foot">这几秒里没被看到 · <span class="em">简历就被划走</span></div>
"""
    shot(page(body, css, "2/7"), "p2_hr_scan.png")


# ═══ P3 · 三处硬伤预告 · 反面三格 ═══
def gen_p3_three_flaws() -> None:
    flaws = [
        ("①", "求职意向空着", "HR 定位不了你要哪个岗 · 直接划走"),
        ("②", "全是「负责」没数字", "看不出你做出过什么 · 没记忆点"),
        ("③", "岗位关键词一个没写", "机器初筛就刷掉 · 没到 HR 手里"),
    ]
    cards = ""
    for num, title, sub in flaws:
        cards += f"""
<div class="card">
  <div class="num">{num}</div>
  <div class="card-body"><div class="t">{title}</div><div class="s">{sub}</div></div>
  <div class="x">✕</div>
</div>"""
    css = f"""
body {{ display: flex; flex-direction: column; justify-content: center; padding: 0 74px; }}
.head {{ font-size: 62px; font-weight: 900; margin-bottom: 70px; line-height: 1.4; }}
.head .em {{ color: {TOK['hard_red']}; }}
.card {{ display: flex; align-items: center; gap: 34px; background: {TOK['pure_white']};
  border: 2px solid rgba(229,57,53,0.35); border-radius: 22px; padding: 46px 42px; margin: 22px 0;
  box-shadow: 0 6px 24px rgba(0,0,0,0.1); }}
.num {{ font-size: 54px; font-weight: 900; color: {TOK['hard_red']}; }}
.t {{ font-size: 40px; font-weight: 800; color: {TOK['ink']}; }}
.s {{ font-size: 27px; color: {TOK['muted']}; margin-top: 12px; }}
.x {{ margin-left: auto; font-size: 50px; color: {TOK['hard_red']}; opacity: 0.85; }}
.card-body {{ flex: 1; }}
"""
    body = f"""
<div class="head">简历被刷 · <span class="em">多半这 3 处</span><br/>HR 根本没看到</div>
{cards}
"""
    shot(page(body, css, "3/7"), "p3_three_flaws.png")


# ═══ P4 · 第一处 求职意向 · before/after 分屏 ═══
def gen_p4_fix1_intent() -> None:
    css = f"""
body {{ display: flex; flex-direction: column; justify-content: center; padding: 0 70px; }}
.head {{ font-size: 58px; font-weight: 900; margin-bottom: 20px; }}
.head .em {{ color: {TOK['hard_red']}; }}
.sub {{ font-size: 30px; color: {TOK['muted']}; margin-bottom: 56px; }}
.pane {{ border-radius: 18px; padding: 46px 44px; position: relative; margin: 18px 0;
  box-shadow: 0 8px 30px rgba(0,0,0,0.12); }}
.before {{ background: #e9e4d8; }}
.after {{ background: {TOK['pure_white']}; border: 3px solid {TOK['pass_green']}; }}
.tag {{ position: absolute; top: -20px; left: 36px; font-size: 28px; font-weight: 800;
  padding: 8px 22px; border-radius: 10px; }}
.tag-b {{ background: {TOK['muted']}; color: {TOK['pure_white']}; }}
.tag-a {{ background: {TOK['pass_green']}; color: {TOK['pure_white']}; }}
.k {{ font-size: 32px; font-weight: 700; color: {TOK['ink_soft']}; }}
.v-empty {{ font-size: 42px; color: {TOK['muted']}; font-style: italic; margin-top: 14px; }}
.v-fix {{ font-size: 46px; color: {TOK['ink']}; font-weight: 800; margin-top: 14px; }}
.v-time {{ font-size: 32px; color: {TOK['pass_green']}; font-weight: 700; margin-top: 14px; }}
.mark {{ position: absolute; right: 40px; bottom: 34px; font-size: 60px; }}
.mark-x {{ color: {TOK['hard_red']}; }}
.mark-v {{ color: {TOK['pass_green']}; }}
"""
    body = f"""
<div class="head">第一处 · <span class="em">求职意向</span></div>
<div class="sub">HR 第一眼要定位：你要哪个岗</div>
<div class="pane before">
  <div class="tag tag-b">before</div>
  <div class="k">求职意向</div>
  <div class="v-empty">（空着 / 运营相关）</div>
  <div class="mark mark-x">✕</div>
</div>
<div class="pane after">
  <div class="tag tag-a">after</div>
  <div class="k">求职意向</div>
  <div class="v-fix">新媒体运营（内容方向）</div>
  <div class="v-time">✓ 可 2 周内到岗</div>
  <div class="mark mark-v">✓</div>
</div>
"""
    shot(page(body, css, "4/7"), "p4_fix1_intent.png")


# ═══ P5 · 第二处 成果数字 · 对照句卡（最强收藏帧）═══
def gen_p5_fix2_numbers() -> None:
    css = f"""
body {{ display: flex; flex-direction: column; justify-content: center; padding: 0 70px; }}
.head {{ font-size: 58px; font-weight: 900; margin-bottom: 20px; }}
.head .em {{ color: {TOK['hard_red']}; }}
.sub {{ font-size: 30px; color: {TOK['muted']}; margin-bottom: 50px; }}
.card {{ background: {TOK['pure_white']}; border-radius: 20px; padding: 60px 54px;
  box-shadow: 0 12px 44px rgba(0,0,0,0.16); }}
.line {{ display: flex; align-items: flex-start; gap: 24px; padding: 32px 0; }}
.line + .line {{ border-top: 2px dashed {TOK['grey_line']}; }}
.m {{ font-size: 56px; font-weight: 900; line-height: 1; flex-shrink: 0; }}
.m-x {{ color: {TOK['hard_red']}; }}
.m-v {{ color: {TOK['pass_green']}; }}
.txt {{ font-size: 44px; line-height: 1.4; }}
.txt-x {{ color: {TOK['muted']}; text-decoration: line-through; }}
.txt-v {{ color: {TOK['ink']}; font-weight: 800; }}
.txt-v b {{ color: {TOK['pass_green']}; }}
.tpl {{ margin-top: 46px; background: rgba(217,140,0,0.12); border-left: 6px solid {TOK['scan_amber']};
  border-radius: 12px; padding: 34px 38px; font-size: 32px; color: {TOK['ink_soft']}; line-height: 1.6; }}
.tpl b {{ color: {TOK['ink']}; }}
"""
    body = f"""
<div class="head">第二处 · <span class="em">全是职责·没数字</span></div>
<div class="sub">同一段经历 · 换个写法 HR 记住你</div>
<div class="card">
  <div class="line"><div class="m m-x">✕</div><div class="txt txt-x">负责社群运营</div></div>
  <div class="line"><div class="m m-v">✓</div><div class="txt txt-v">从 <b>0 搭 3000 人</b> 社群，转化 <b>涨 40%</b></div></div>
</div>
<div class="tpl">句式：把「<b>负责 X</b>」改成「<b>用什么方法 · 做出什么数字</b>」<br/>（数字填你真的，别编）</div>
"""
    shot(page(body, css, "5/7"), "p5_fix2_numbers.png")


# ═══ P6 · 第三处 ATS 关键词 · 8 格 + 补词 ═══
def gen_p6_fix3_ats() -> None:
    kws = [("短视频运营", True), ("用户增长", True), ("数据分析", True),
           ("内容策划", True), ("社群转化", True), ("投放优化", False),
           ("A/B 测试", True), ("SOP 搭建", False)]
    cells = ""
    for kw, hit in kws:
        cls = "hit" if hit else "miss"
        icon = "✓" if hit else "✕"
        cells += f'<div class="kw {cls}"><span class="kw-ic">{icon}</span>{kw}</div>'
    css = f"""
body {{ display: flex; flex-direction: column; justify-content: center; padding: 0 66px; }}
.head {{ font-size: 58px; font-weight: 900; margin-bottom: 16px; }}
.head .em {{ color: {TOK['scan_amber']}; }}
.sub {{ font-size: 30px; color: {TOK['muted']}; margin-bottom: 50px; }}
.panel {{ background: {TOK['ui_frame']}; border-radius: 20px; padding: 50px 44px; }}
.panel-h {{ display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 36px; }}
.panel-t {{ font-size: 32px; font-weight: 700; color: {TOK['paper_bg']}; }}
.score {{ font-size: 30px; color: {TOK['paper_bg']}; }}
.score b {{ font-size: 50px; font-weight: 900; color: {TOK['scan_amber']}; }}
.grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; }}
.kw {{ display: flex; align-items: center; gap: 14px; font-size: 32px; font-weight: 600;
  padding: 22px 24px; border-radius: 12px; }}
.kw.hit {{ background: rgba(46,125,50,0.9); color: {TOK['pure_white']}; }}
.kw.miss {{ background: rgba(245,240,230,0.1); color: #b9b3a6;
  border: 2px dashed {TOK['hard_red']}; }}
.kw-ic {{ font-size: 30px; font-weight: 900; }}
.foot {{ margin-top: 46px; font-size: 32px; color: {TOK['ink']}; font-weight: 700;
  text-align: center; line-height: 1.6; }}
.foot .em {{ color: {TOK['hard_red']}; }}
"""
    body = f"""
<div class="head">第三处 · <span class="em">机器先筛关键词</span></div>
<div class="sub">要的词没写 · 简历没到 HR 就被刷</div>
<div class="panel">
  <div class="panel-h"><div class="panel-t">机器初筛 · 关键词匹配</div>
    <div class="score">匹配 <b>6/8</b></div></div>
  <div class="grid">{cells}</div>
</div>
<div class="foot">缺的 2 个词 · <span class="em">照招聘描述补上</span></div>
"""
    shot(page(body, css, "6/7"), "p6_fix3_ats.png")


# ═══ P7 · 边界 + CTA ═══
def gen_p7_boundary_cta() -> None:
    css = f"""
body {{ display: flex; flex-direction: column; justify-content: center; align-items: center;
  padding: 0 80px; text-align: center; }}
.no {{ font-size: 40px; font-weight: 700; color: {TOK['muted']}; text-decoration: line-through;
  margin-bottom: 40px; }}
.yes {{ font-size: 78px; font-weight: 900; line-height: 1.4; color: {TOK['ink']}; }}
.yes .em {{ color: {TOK['hard_red']}; }}
.bound {{ margin-top: 44px; font-size: 34px; color: {TOK['pass_green']}; font-weight: 700; }}
.bound .g {{ color: {TOK['muted']}; font-weight: 400; font-size: 30px; }}
.cta {{ margin-top: 110px; background: {TOK['pure_white']}; border: 3px solid {TOK['hard_red']};
  border-radius: 22px; padding: 50px 60px; box-shadow: 0 10px 36px rgba(0,0,0,0.12); }}
.cta-t {{ font-size: 46px; font-weight: 900; color: {TOK['ink']}; }}
.cta-t .kw {{ color: {TOK['hard_red']}; }}
.cta-s {{ font-size: 30px; color: {TOK['muted']}; margin-top: 20px; }}
"""
    body = f"""
<div class="no">花钱找人代改 · 包装虚假经历</div>
<div class="yes">被看到<br/><span class="em">是不花钱的第一步</span></div>
<div class="bound">数字填你真的 · 别编 <span class="g">（HR 一问就露）</span></div>
<div class="cta">
  <div class="cta-t">私信「<span class="kw">发我简历</span>」</div>
  <div class="cta-s">脱敏就行 · 我用 HR 视角帮你圈重点</div>
</div>
"""
    shot(page(body, css, "7/7"), "p7_boundary_cta.png")


def main() -> None:
    print(f"→ W28D06 xhs 7 页轮播生成 · out={OUT}")
    gen_p1_cover()
    gen_p2_hr_scan()
    gen_p3_three_flaws()
    gen_p4_fix1_intent()
    gen_p5_fix2_numbers()
    gen_p6_fix3_ats()
    gen_p7_boundary_cta()
    print(f"✓ 7 页全生成 · {OUT}")
    print("下一步 · palette gate 逐张:")
    print(f'  for p in "{OUT}"/*.png; do python3 pipeline/gate_check_palette.py "$p"; done')


if __name__ == "__main__":
    main()
