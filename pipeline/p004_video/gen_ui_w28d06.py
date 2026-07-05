#!/usr/bin/env python3
"""W28D06 UI 叠层 PNG 生成 · Chrome headless 静态素材路径.

选题: AI 改简历不用找人改 · 简历纸面 + HR 扫描线 + before/after (H6 全新族群 vs D05 暗色卧室)

对齐 pipeline_config.yaml / storyboard.yaml 的 10 张 assets_ui/*.png:
  01_m1_stamp.png          · M1 简历纸 + 已读不回红戳 + 投递计数 + HR 光标 (巨标由 drawtext)
  02_m2_bill.png           · M2 简历 + ¥3888 账单卡 (化名·示例 · 巨标由 drawtext)
  03_m3_resume_scan.png     · M3 化名简历卡「示例·化名·陈默」+ 琥珀扫描带 + 6 打点
  04_m4_preview.png        · M4 简历 + 三处红虚线高亮框 ①②③ (段标由 drawtext)
  05_m5_split_intent.png    · M5 左 before 意向空(灰) / 右 after 写死岗位(绿✓) · 改法 baked
  06_m6_compare_card.png    · M6 居中对照卡 ❌负责社群运营 / ✅从 0 搭 3000 人·转化+40% (收藏帧 · baked)
  07_m7_ats.png            · M7 ATS 8 关键词格 (灰/绿混) + 匹配度 6/8 (段标由 drawtext)
  08_m8_checklist.png      · M8 竖向三改清单卡 + 三处 ✕→✓ 角标 (巨标由 drawtext)
  09_m9_anchor.png         · M9 纸面底 (大字全 drawtext)
  10_m10_cta.png           · M10 纸面底 + 填空模板卡框 (CTA/模板文字由 drawtext)

色板 (design_language.md 硬门 · gate_check_palette.py 蓝紫 H=240~290 <5%):
  paper_bg     #f5f0e6 (暖白纸 · 区别 D05 全黑底)
  pure_white   #ffffff (after 简历卡)
  ui_frame     #14171c (外框近黑 · 低饱和不触蓝阈)
  ink          #1a1a1a / #33312c (简历正文墨字)
  hard_red     #e53935 (硬伤/戳章 · 禁 #ff5252 粉红)
  pass_green   #2e7d32 (after/✓ 森绿)
  scan_amber   #d98c00 (HR 扫描高亮 暖调 · 替代任何蓝色扫描)
  muted        #6b6b6b (副文/示例水印)
  禁: #bd93f9 · #ff79c6 · #8be9fd Dracula 三色 · 蓝紫渐变 · linear-gradient 蓝紫端

真实性: 简历全化名「示例·化名·陈默」· 数字为示例占位

用法:
  python3 pipeline/p004_video/gen_ui_w28d06.py

依赖: Chrome + macOS · headless=new
"""
from __future__ import annotations

import pathlib
import subprocess
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "publish" / "2026-W28" / "D06-AI改简历不用找人改" / "build" / "assets_ui"
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
  font-family: -apple-system, "PingFang SC", "SF Pro Text", sans-serif; }}
"""

# 复用: 简历纸面 mock (化名·陈默) · before 版 (三处硬伤)
RESUME_BEFORE = f"""
<div class="resume">
  <div class="watermark">示例 · 化名 · 陈默</div>
  <div class="r-name">陈 默</div>
  <div class="r-contact">男 · 26 · 本科 · 新媒体方向 · 2 年经验</div>
  <div class="r-intent-row"><span class="r-key">求职意向</span><span class="r-empty">（空着 / 运营相关）</span></div>
  <div class="r-sec">工作经历</div>
  <div class="r-item">· 负责公司社群的日常运营与维护</div>
  <div class="r-item">· 配合活动策划，参与推广工作</div>
  <div class="r-item">· 负责内容排版与账号的日常更新</div>
  <div class="r-sec">技能</div>
  <div class="r-item r-skill">文案 · 排版 · 沟通 · 团队协作</div>
</div>
"""

RESUME_CSS = f"""
.resume {{ background: {TOK['pure_white']}; border-radius: 14px; padding: 60px 56px;
  box-shadow: 0 10px 40px rgba(0,0,0,0.18); position: relative; }}
.watermark {{ position: absolute; top: 22px; right: 30px; font-size: 22px;
  color: {TOK['muted']}; opacity: 0.7; }}
.r-name {{ font-size: 60px; font-weight: 800; color: {TOK['ink']}; letter-spacing: 4px; }}
.r-contact {{ font-size: 28px; color: {TOK['muted']}; margin: 14px 0 34px; }}
.r-intent-row {{ display: flex; align-items: baseline; gap: 20px; padding: 16px 0;
  border-top: 2px solid {TOK['grey_line']}; border-bottom: 2px solid {TOK['grey_line']}; }}
.r-key {{ font-size: 32px; font-weight: 700; color: {TOK['ink_soft']}; }}
.r-empty {{ font-size: 30px; color: {TOK['muted']}; font-style: italic; }}
.r-sec {{ font-size: 30px; font-weight: 700; color: {TOK['ink_soft']}; margin: 32px 0 16px;
  border-left: 6px solid {TOK['ink_soft']}; padding-left: 16px; }}
.r-item {{ font-size: 30px; color: {TOK['ink']}; line-height: 1.7; }}
.r-skill {{ color: {TOK['ink_soft']}; }}
"""


# ═══ M1 · 3s · 简历纸 + 已读不回红戳 + 投递计数 + HR 光标 ═══
def gen_m1_stamp() -> None:
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
{BASE_CSS}{RESUME_CSS}
body {{ background: {TOK['paper_bg']}; padding: 120px 70px; position: relative; }}
.counter {{ position: absolute; top: 48px; right: 60px; background: {TOK['ui_frame']};
  color: {TOK['paper_bg']}; font-size: 30px; font-weight: 700; padding: 14px 26px;
  border-radius: 10px; }}
.counter b {{ color: {TOK['hard_red']}; font-size: 38px; }}
.stamp {{ position: absolute; top: 620px; left: 50%; transform: translateX(-50%) rotate(-12deg);
  border: 7px solid {TOK['hard_red']}; color: {TOK['hard_red']}; font-size: 84px; font-weight: 900;
  padding: 18px 44px; border-radius: 16px; letter-spacing: 6px; opacity: 0.92;
  box-shadow: 0 0 0 3px rgba(229,57,53,0.25); }}
.cursor {{ position: absolute; top: 760px; left: 720px; font-size: 60px;
  filter: drop-shadow(0 3px 4px rgba(0,0,0,0.4)); }}
</style></head><body>
<div class="counter">已投 <b>268</b></div>
{RESUME_BEFORE}
<div class="stamp">已读不回</div>
<div class="cursor">➤</div>
</body></html>"""
    shot(html, "01_m1_stamp.png")


# ═══ M2 · 5s · 简历 + ¥3888 账单卡拍到桌面 ═══
def gen_m2_bill() -> None:
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
{BASE_CSS}{RESUME_CSS}
body {{ background: {TOK['paper_bg']}; padding: 120px 70px; position: relative; }}
.resume {{ filter: grayscale(0.35); opacity: 0.86; }}
.stamp-sm {{ position: absolute; top: 560px; left: 120px; transform: rotate(-10deg);
  border: 5px solid {TOK['hard_red']}; color: {TOK['hard_red']}; font-size: 50px; font-weight: 900;
  padding: 10px 26px; border-radius: 12px; letter-spacing: 3px; opacity: 0.85; }}
.bill {{ position: absolute; top: 1120px; right: 90px; transform: rotate(6deg);
  background: {TOK['pure_white']}; border-radius: 14px; padding: 40px 48px;
  box-shadow: 0 16px 50px rgba(0,0,0,0.3); border-top: 8px solid {TOK['hard_red']}; }}
.bill-title {{ font-size: 32px; color: {TOK['ink_soft']}; font-weight: 700; }}
.bill-amt {{ font-size: 92px; font-weight: 900; color: {TOK['hard_red']}; margin: 14px 0 6px; }}
.bill-note {{ font-size: 26px; color: {TOK['muted']}; }}
</style></head><body>
{RESUME_BEFORE}
<div class="stamp-sm">仍没面试</div>
<div class="bill">
  <div class="bill-title">简历修改服务</div>
  <div class="bill-amt">¥3888</div>
  <div class="bill-note">找人改 · 改完照样没回音 (示例)</div>
</div>
</body></html>"""
    shot(html, "02_m2_bill.png")


# ═══ M3 · 6s · 化名简历卡 + 琥珀扫描带 + 6 打点 ═══
def gen_m3_resume_scan() -> None:
    dots = ""
    dot_pos = [(56, 300, "姓名/联系方式"), (56, 470, "求职意向"), (56, 700, "工作经历"),
               (56, 900, "成果/数字"), (56, 1120, "技能/关键词"), (56, 1300, "教育")]
    for i, (x, y, label) in enumerate(dot_pos, 1):
        dots += f"""
    <div class="scan-dot" style="left: {x}px; top: {y}px;">
      <span class="dot-num">{i}</span><span class="dot-label">{label}</span>
    </div>"""
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
{BASE_CSS}
body {{ background: {TOK['paper_bg']}; padding: 150px 70px; position: relative; }}
.card {{ background: {TOK['pure_white']}; border-radius: 16px; height: 1500px;
  box-shadow: 0 12px 44px rgba(0,0,0,0.18); position: relative; overflow: hidden;
  padding: 56px; }}
.watermark {{ position: absolute; top: 24px; right: 34px; font-size: 24px; color: {TOK['muted']}; }}
.r-name {{ font-size: 56px; font-weight: 800; color: {TOK['ink']}; letter-spacing: 4px; }}
.r-line {{ height: 20px; background: {TOK['grey_line']}; border-radius: 4px; margin: 22px 0;
  opacity: 0.7; }}
.r-line.short {{ width: 45%; }} .r-line.mid {{ width: 70%; }}
.scan-band {{ position: absolute; left: 0; right: 0; top: 620px; height: 130px;
  background: linear-gradient(180deg, rgba(217,140,0,0) 0%, rgba(217,140,0,0.28) 50%, rgba(217,140,0,0) 100%);
  border-top: 3px solid {TOK['scan_amber']}; }}
.scan-line {{ position: absolute; left: 0; right: 0; top: 685px; height: 4px;
  background: {TOK['scan_amber']}; box-shadow: 0 0 18px 3px rgba(217,140,0,0.7); }}
.scan-dot {{ position: absolute; display: flex; align-items: center; gap: 14px; }}
.dot-num {{ width: 44px; height: 44px; border-radius: 50%; background: {TOK['scan_amber']};
  color: {TOK['pure_white']}; font-size: 26px; font-weight: 800;
  display: flex; align-items: center; justify-content: center; }}
.dot-label {{ font-size: 26px; color: {TOK['ink_soft']}; font-weight: 600;
  background: rgba(245,240,230,0.9); padding: 4px 12px; border-radius: 6px; }}
</style></head><body>
<div class="card">
  <div class="watermark">示例 · 化名 · 陈默</div>
  <div class="r-name">陈 默</div>
  <div class="r-line mid"></div>
  <div class="r-line short"></div>
  <div class="r-line"></div>
  <div class="r-line mid"></div>
  <div class="r-line"></div>
  <div class="r-line short"></div>
  <div class="r-line mid"></div>
  <div class="scan-band"></div>
  <div class="scan-line"></div>
  {dots}
</div>
</body></html>"""
    shot(html, "03_m3_resume_scan.png")


# ═══ M4 · 3.5s · 简历 + 三处红虚线高亮框 ①②③ ═══
def gen_m4_preview() -> None:
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
{BASE_CSS}{RESUME_CSS}
body {{ background: {TOK['paper_bg']}; padding: 120px 70px; position: relative; }}
.hl {{ position: absolute; border: 4px dashed {TOK['hard_red']}; border-radius: 12px;
  background: rgba(229,57,53,0.06); }}
.hl-num {{ position: absolute; left: -26px; top: -26px; width: 52px; height: 52px;
  border-radius: 50%; background: {TOK['hard_red']}; color: {TOK['pure_white']};
  font-size: 30px; font-weight: 800; display: flex; align-items: center; justify-content: center; }}
</style></head><body>
{RESUME_BEFORE}
<div class="hl" style="left: 110px; top: 400px; width: 760px; height: 90px;"><div class="hl-num">1</div></div>
<div class="hl" style="left: 110px; top: 560px; width: 760px; height: 200px;"><div class="hl-num">2</div></div>
<div class="hl" style="left: 110px; top: 900px; width: 760px; height: 90px;"><div class="hl-num">3</div></div>
</body></html>"""
    shot(html, "04_m4_preview.png")


# ═══ M5 · 8s · before/after 分屏 · 求职意向 (改法 baked) ═══
def gen_m5_split_intent() -> None:
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
{BASE_CSS}
body {{ background: {TOK['paper_bg']}; position: relative; }}
.split {{ display: flex; flex-direction: column; height: 100%; padding: 200px 60px 120px; gap: 40px; }}
.pane {{ flex: 1; border-radius: 16px; padding: 50px; position: relative;
  box-shadow: 0 8px 30px rgba(0,0,0,0.14); }}
.before {{ background: #e9e4d8; filter: grayscale(0.5); }}
.after {{ background: {TOK['pure_white']}; border: 3px solid {TOK['pass_green']}; }}
.tag {{ position: absolute; top: -22px; left: 40px; font-size: 30px; font-weight: 800;
  padding: 8px 24px; border-radius: 10px; }}
.tag-b {{ background: {TOK['muted']}; color: {TOK['pure_white']}; }}
.tag-a {{ background: {TOK['pass_green']}; color: {TOK['pure_white']}; }}
.k {{ font-size: 34px; font-weight: 700; color: {TOK['ink_soft']}; }}
.v-empty {{ font-size: 40px; color: {TOK['muted']}; font-style: italic; margin-top: 16px; }}
.v-fix {{ font-size: 46px; color: {TOK['ink']}; font-weight: 700; margin-top: 16px; }}
.v-time {{ font-size: 32px; color: {TOK['pass_green']}; font-weight: 700; margin-top: 14px; }}
.check {{ position: absolute; right: 44px; bottom: 40px; font-size: 72px; color: {TOK['pass_green']}; }}
.cross {{ position: absolute; right: 44px; bottom: 40px; font-size: 64px; color: {TOK['hard_red']}; }}
</style></head><body>
<div class="split">
  <div class="pane before">
    <div class="tag tag-b">before</div>
    <div class="k">求职意向</div>
    <div class="v-empty">（空着 / 运营相关）</div>
    <div class="cross">✕</div>
  </div>
  <div class="pane after">
    <div class="tag tag-a">after</div>
    <div class="k">求职意向</div>
    <div class="v-fix">新媒体运营（内容方向）</div>
    <div class="v-time">✓ 可 2 周内到岗</div>
    <div class="check">✓</div>
  </div>
</div>
</body></html>"""
    shot(html, "05_m5_split_intent.png")


# ═══ M6 · 8.5s · 居中对照句卡 ❌→✅ (收藏帧 · 全 baked) ═══
def gen_m6_compare_card() -> None:
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
{BASE_CSS}
body {{ background: {TOK['paper_bg']}; display: flex; flex-direction: column;
  justify-content: center; align-items: center; padding: 0 70px; }}
.card {{ background: {TOK['pure_white']}; border-radius: 20px; width: 100%; padding: 70px 60px;
  box-shadow: 0 14px 50px rgba(0,0,0,0.16); }}
.row {{ display: flex; align-items: flex-start; gap: 26px; padding: 34px 0; }}
.row + .row {{ border-top: 2px dashed {TOK['grey_line']}; }}
.mark {{ font-size: 60px; font-weight: 900; line-height: 1; flex-shrink: 0; }}
.mark-x {{ color: {TOK['hard_red']}; }}
.mark-v {{ color: {TOK['pass_green']}; }}
.txt {{ font-size: 46px; line-height: 1.35; }}
.txt-x {{ color: {TOK['muted']}; text-decoration: line-through; }}
.txt-v {{ color: {TOK['ink']}; font-weight: 700; }}
.txt-v b {{ color: {TOK['pass_green']}; }}
.tip {{ text-align: center; font-size: 30px; color: {TOK['muted']}; margin-top: 40px; }}
</style></head><body>
<div class="card">
  <div class="row">
    <div class="mark mark-x">✕</div>
    <div class="txt txt-x">负责社群运营</div>
  </div>
  <div class="row">
    <div class="mark mark-v">✓</div>
    <div class="txt txt-v">从 <b>0 搭 3000 人</b> 社群，转化 <b>涨 40%</b></div>
  </div>
</div>
<div class="tip">句式：把「负责 X」改成「用什么方法 · 做出什么数字」（数字填你真的）</div>
</body></html>"""
    shot(html, "06_m6_compare_card.png")


# ═══ M7 · 8.5s · ATS 8 关键词格 (灰/绿混) + 匹配度 ═══
def gen_m7_ats() -> None:
    # 岗位要求 8 个关键词 · 简历命中 6 个(绿) 缺 2 个(灰红)
    kws = [("短视频运营", True), ("用户增长", True), ("数据分析", True),
           ("内容策划", True), ("社群转化", True), ("投放优化", False),
           ("A/B 测试", True), ("SOP 搭建", False)]
    cells = ""
    for kw, hit in kws:
        cls = "hit" if hit else "miss"
        icon = "✓" if hit else "✕"
        cells += f'<div class="kw {cls}"><span class="kw-ic">{icon}</span>{kw}</div>'
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
{BASE_CSS}
body {{ background: {TOK['paper_bg']}; padding: 260px 60px 120px; position: relative; }}
.panel {{ background: {TOK['ui_frame']}; border-radius: 18px; padding: 50px 46px; }}
.panel-h {{ display: flex; justify-content: space-between; align-items: baseline;
  margin-bottom: 40px; }}
.panel-t {{ font-size: 34px; font-weight: 700; color: {TOK['paper_bg']}; }}
.score {{ font-size: 30px; color: {TOK['paper_bg']}; }}
.score b {{ font-size: 52px; font-weight: 900; color: {TOK['scan_amber']}; }}
.grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 22px; }}
.kw {{ display: flex; align-items: center; gap: 16px; font-size: 34px; font-weight: 600;
  padding: 22px 26px; border-radius: 12px; }}
.kw.hit {{ background: rgba(46,125,50,0.9); color: {TOK['pure_white']}; }}
.kw.miss {{ background: rgba(245,240,230,0.12); color: {TOK['muted']};
  border: 2px dashed {TOK['hard_red']}; }}
.kw-ic {{ font-size: 32px; font-weight: 900; }}
.note {{ text-align: center; font-size: 30px; color: {TOK['muted']}; margin-top: 40px; }}
</style></head><body>
<div class="panel">
  <div class="panel-h">
    <div class="panel-t">机器初筛 · 关键词匹配</div>
    <div class="score">匹配 <b>6/8</b></div>
  </div>
  <div class="grid">{cells}</div>
</div>
<div class="note">缺的 2 个词，照招聘描述补上 · 简历才进得了 HR 手里（示例）</div>
</body></html>"""
    shot(html, "07_m7_ats.png")


# ═══ M8 · 6.5s · 竖向三改清单卡 + 三处 ✕→✓ 角标 ═══
def gen_m8_checklist() -> None:
    items = [
        ("求职意向", "空着 / 运营相关", "写死岗位 + 到岗时间"),
        ("工作成果", "全是「负责」没数字", "方法 + 量化结果"),
        ("岗位关键词", "一个没写", "照 JD 补齐关键词"),
    ]
    rows = ""
    for i, (title, bad, good) in enumerate(items, 1):
        rows += f"""
  <div class="item">
    <div class="badge"><span class="b-x">✕</span><span class="b-v">✓</span></div>
    <div class="it-body">
      <div class="it-title">{i} · {title}</div>
      <div class="it-bad">✕ {bad}</div>
      <div class="it-good">✓ {good}</div>
    </div>
  </div>"""
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
{BASE_CSS}
body {{ background: {TOK['paper_bg']}; padding: 240px 64px 120px; }}
.card {{ background: {TOK['pure_white']}; border-radius: 20px; padding: 40px 44px;
  box-shadow: 0 12px 44px rgba(0,0,0,0.16); }}
.item {{ display: flex; gap: 28px; padding: 34px 0; align-items: flex-start; }}
.item + .item {{ border-top: 2px solid {TOK['grey_line']}; }}
.badge {{ display: flex; flex-direction: column; align-items: center; gap: 6px; flex-shrink: 0;
  padding-top: 6px; }}
.b-x {{ font-size: 30px; color: {TOK['hard_red']}; text-decoration: line-through; }}
.b-v {{ font-size: 44px; color: {TOK['pass_green']}; font-weight: 900; }}
.it-title {{ font-size: 38px; font-weight: 800; color: {TOK['ink']}; margin-bottom: 12px; }}
.it-bad {{ font-size: 30px; color: {TOK['muted']}; text-decoration: line-through; }}
.it-good {{ font-size: 32px; color: {TOK['pass_green']}; font-weight: 700; margin-top: 6px; }}
</style></head><body>
<div class="card">{rows}</div>
</body></html>"""
    shot(html, "08_m8_checklist.png")


# ═══ M9 · 5.5s · 纸面底 (大字全 drawtext) ═══
def gen_m9_anchor() -> None:
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
{BASE_CSS}
body {{ background: {TOK['paper_bg']}; }}
</style></head><body></body></html>"""
    shot(html, "09_m9_anchor.png")


# ═══ M10 · 5.5s · 纸面底 + 填空模板卡框 (文字由 drawtext) ═══
def gen_m10_cta() -> None:
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
{BASE_CSS}
body {{ background: {TOK['paper_bg']}; position: relative; }}
.tpl {{ position: absolute; left: 90px; right: 90px; top: 1080px; height: 340px;
  background: {TOK['pure_white']}; border: 3px dashed {TOK['scan_amber']}; border-radius: 18px;
  box-shadow: 0 10px 36px rgba(0,0,0,0.12); }}
.tpl-tag {{ position: absolute; top: -24px; left: 44px; background: {TOK['scan_amber']};
  color: {TOK['pure_white']}; font-size: 28px; font-weight: 700; padding: 8px 22px; border-radius: 10px; }}
</style></head><body>
<div class="tpl"><div class="tpl-tag">改写模板</div></div>
</body></html>"""
    shot(html, "10_m10_cta.png")


def main() -> None:
    print(f"→ W28D06 UI PNG 生成 · out={OUT}")
    gen_m1_stamp()
    gen_m2_bill()
    gen_m3_resume_scan()
    gen_m4_preview()
    gen_m5_split_intent()
    gen_m6_compare_card()
    gen_m7_ats()
    gen_m8_checklist()
    gen_m9_anchor()
    gen_m10_cta()
    print(f"✓ 10 张 UI PNG 全生成 · {OUT}")


if __name__ == "__main__":
    main()
