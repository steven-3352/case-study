#!/usr/bin/env python3
"""W28D02 UI 仿真素材生成 · 走 gen_evidence.py 高保真仿真体裁路径（Q9 允许）.

产出 1080×1920（9:16）PNG，遵循 design_language.md token（纸黑白+傍晚暖+accent红/黄）。
所有画面标 generated_fact，声明为示例数据。

产出：
  publish/2026-W28/D02-打工人5分钟出周报/build/assets_ui/*.png

用法：python3 pipeline/p004_video/gen_ui_w28d02.py
"""
from __future__ import annotations

import pathlib
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "publish" / "2026-W28" / "D02-打工人5分钟出周报" / "build" / "assets_ui"
OUT.mkdir(parents=True, exist_ok=True)

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
W, H = 1080, 1920

# ── design_language.md token ──
TOK = {
    "canvas": "#0f0f0f",
    "surface": "#f5f5f0",
    "ink": "#1a1a1a",
    "muted": "#7a7a7a",
    "accent_red": "#e53935",
    "accent_soft": "#ffc857",
    "system_blue": "#007aff",
    "wechat_green": "#95ec69",
    "excel_green": "#217346",
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


# ═══ M1/M2 · iPhone 锁屏 18:55·周五 ═══
def gen_iphone_lockscreen() -> None:
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
{BASE_CSS}
body {{ background: linear-gradient(180deg, #1a1710 0%, #2b2519 45%, #0a0908 100%); color: white; position: relative; }}
.dot {{ position: absolute; top: 12px; left: 50%; transform: translateX(-50%); width: 120px; height: 40px; background: #000; border-radius: 20px; }}
.time {{ position: absolute; top: 220px; left: 50%; transform: translateX(-50%);
  font-family: -apple-system, "SF Pro Display", sans-serif; font-weight: 200;
  font-size: 340px; letter-spacing: -12px; line-height: 1; text-shadow: 0 4px 24px rgba(0,0,0,.4); }}
.date {{ position: absolute; top: 620px; left: 50%; transform: translateX(-50%);
  font-size: 44px; font-weight: 400; letter-spacing: 3px; opacity: .95; }}
.status {{ position: absolute; top: 32px; left: 44px; font-size: 30px; font-weight: 600; }}
.right {{ position: absolute; top: 32px; right: 44px; font-size: 30px; font-weight: 500; letter-spacing: 4px; }}
.bottom {{ position: absolute; bottom: 60px; left: 0; right: 0; text-align: center;
  font-size: 32px; opacity: .5; letter-spacing: 2px; }}
</style></head><body>
<div class="status">中国移动 5G</div>
<div class="right">72%</div>
<div class="dot"></div>
<div class="time">18:55</div>
<div class="date">7 月 4 日 周五</div>
<div class="bottom">向上滑动以打开</div>
</body></html>"""
    shot(html, "01_iphone_lockscreen_1855.png")


# ═══ M2 · 微信通知气泡「老板：周报呢？」═══
def gen_wechat_boss_ping() -> None:
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
{BASE_CSS}
body {{ background: linear-gradient(180deg, #1a1710 0%, #2b2519 50%, #0a0908 100%); color: white; position: relative; }}
.status {{ position: absolute; top: 32px; left: 44px; font-size: 30px; font-weight: 600; }}
.right {{ position: absolute; top: 32px; right: 44px; font-size: 30px; font-weight: 500; letter-spacing: 4px; }}
.time-small {{ position: absolute; top: 130px; left: 50%; transform: translateX(-50%);
  font-family: "SF Pro Display", sans-serif; font-weight: 200; font-size: 200px; letter-spacing: -8px; opacity: .95; line-height:1; }}
.card {{ position: absolute; top: 400px; left: 40px; right: 40px;
  background: rgba(50, 50, 50, .70); backdrop-filter: blur(30px);
  border-radius: 32px; padding: 32px 36px; color: white; }}
.card-head {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; font-size: 28px; opacity: .8; }}
.card-title {{ font-weight: 700; letter-spacing: 1px; }}
.card-time {{ font-weight: 500; letter-spacing: 2px; }}
.msg-line {{ display: flex; align-items: flex-start; gap: 20px; margin-top: 6px; }}
.avatar {{ width: 88px; height: 88px; border-radius: 20px; background: {TOK['wechat_green']}; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center; font-size: 44px; font-weight: 700; color: white; }}
.msg-body {{ flex: 1; padding-top: 4px; }}
.msg-name {{ font-size: 34px; font-weight: 700; margin-bottom: 10px; letter-spacing: 1px; }}
.msg-text {{ font-size: 36px; line-height: 1.4; opacity: .95; }}
.bottom {{ position: absolute; bottom: 60px; left: 0; right: 0; text-align: center; font-size: 32px; opacity: .5; letter-spacing: 2px; }}
</style></head><body>
<div class="status">中国移动 5G</div>
<div class="right">72%</div>
<div class="time-small">18:55</div>
<div class="card">
  <div class="card-head"><div class="card-title">微信</div><div class="card-time">现在</div></div>
  <div class="msg-line">
    <div class="avatar">L</div>
    <div class="msg-body">
      <div class="msg-name">老板</div>
      <div class="msg-text">周报呢？</div>
    </div>
  </div>
</div>
<div class="bottom">向上滑动以打开</div>
</body></html>"""
    shot(html, "02_wechat_boss_ping.png")


# ═══ M2 · Excel 空白周报模板 ═══
def gen_excel_empty() -> None:
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
{BASE_CSS}
body {{ background: {TOK['surface']}; color: {TOK['ink']}; font-family: "Helvetica Neue", Arial, sans-serif; }}
.titlebar {{ background: #f7f5f2; border-bottom: 1px solid #d0cec8; padding: 20px 30px; display: flex; align-items: center; gap: 20px; }}
.dot {{ width: 20px; height: 20px; border-radius: 50%; }}
.dot.r {{ background: #ff5f57; }}.dot.y {{ background: #febc2e; }}.dot.g {{ background: #28c840; }}
.file-name {{ margin-left: 40px; font-size: 28px; font-weight: 600; color: #333; }}
.ribbon {{ background: {TOK['excel_green']}; height: 90px; display: flex; align-items: center; padding: 0 40px; color: white; font-size: 32px; font-weight: 600; }}
.formulabar {{ background: #f7f5f2; border-bottom: 1px solid #d0cec8; padding: 20px 30px; font-family: "SF Mono", Menlo, monospace; font-size: 28px; color: {TOK['muted']}; }}
.grid {{ position: relative; }}
.row {{ display: flex; border-bottom: 1px solid #d0cec8; }}
.col-a {{ width: 90px; border-right: 1px solid #d0cec8; background: #f7f5f2; text-align: center;
  padding: 22px 0; font-size: 26px; color: #666; }}
.col {{ flex: 1; padding: 22px 24px; font-size: 30px; color: {TOK['ink']}; border-right: 1px solid #d0cec8; }}
.head-row .col-a {{ background: #e8e6e0; }}
.head-row .col {{ background: #e8e6e0; font-weight: 600; text-align: center; }}
.cursor {{ position: absolute; background: transparent; border: 4px solid {TOK['excel_green']}; width: 660px; height: 80px; top: 190px; left: 90px;
  animation: blink 1s infinite; box-sizing: border-box; }}
@keyframes blink {{ 50% {{ border-color: transparent; }} }}
.footer {{ position: absolute; bottom: 0; left: 0; right: 0; background: {TOK['excel_green']}; color: white;
  padding: 24px 40px; font-size: 28px; display: flex; gap: 40px; }}
</style></head><body>
<div class="titlebar">
  <div class="dot r"></div><div class="dot y"></div><div class="dot g"></div>
  <div class="file-name">本周工作总结.xlsx</div>
</div>
<div class="ribbon">开始 · 插入 · 布局 · 公式 · 数据 · 审阅</div>
<div class="formulabar">A1  |  fx</div>
<div class="grid">
  <div class="row head-row"><div class="col-a"></div>
    <div class="col">A · 本周工作总结</div><div class="col">B · 完成度</div><div class="col">C · 备注</div></div>
  <div class="row"><div class="col-a">1</div><div class="col"></div><div class="col"></div><div class="col"></div></div>
  <div class="row"><div class="col-a">2</div><div class="col"></div><div class="col"></div><div class="col"></div></div>
  <div class="row"><div class="col-a">3</div><div class="col"></div><div class="col"></div><div class="col"></div></div>
  <div class="row"><div class="col-a">4</div><div class="col"></div><div class="col"></div><div class="col"></div></div>
  <div class="row"><div class="col-a">5</div><div class="col"></div><div class="col"></div><div class="col"></div></div>
  <div class="row"><div class="col-a">6</div><div class="col"></div><div class="col"></div><div class="col"></div></div>
  <div class="row"><div class="col-a">7</div><div class="col"></div><div class="col"></div><div class="col"></div></div>
  <div class="row"><div class="col-a">8</div><div class="col"></div><div class="col"></div><div class="col"></div></div>
  <div class="cursor"></div>
</div>
<div class="footer"><span>就绪</span><span>Sheet1</span></div>
</body></html>"""
    shot(html, "03_excel_empty.png")


# ═══ M4 · AI 对话框 · 错误 prompt「帮我写周报」出通用垃圾 ═══
def gen_ai_wrong_prompt() -> None:
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
{BASE_CSS}
body {{ background: {TOK['surface']}; color: {TOK['ink']}; padding: 40px; }}
.title {{ font-size: 40px; font-weight: 600; margin-bottom: 30px; letter-spacing: 1px; }}
.msg-user {{ display: flex; justify-content: flex-end; margin: 30px 0; }}
.bubble-user {{ background: #d1e7ff; border-radius: 24px; padding: 26px 32px; max-width: 720px;
  font-size: 36px; color: {TOK['ink']}; }}
.msg-ai {{ display: flex; margin: 30px 0; }}
.avatar {{ width: 68px; height: 68px; border-radius: 16px; background: {TOK['ink']}; color: white;
  display: flex; align-items: center; justify-content: center; font-size: 32px; margin-right: 20px; flex-shrink: 0; }}
.bubble-ai {{ background: #f0efec; border-radius: 24px; padding: 28px 32px; max-width: 820px;
  font-size: 30px; color: {TOK['ink']}; line-height: 1.55; }}
.bubble-ai h4 {{ font-size: 32px; font-weight: 700; margin: 10px 0 12px; }}
.bubble-ai p {{ margin: 6px 0; }}
.stamp {{ position: absolute; top: 220px; right: 60px; transform: rotate(-8deg);
  border: 6px solid {TOK['accent_red']}; padding: 12px 40px;
  font-size: 44px; font-weight: 900; color: {TOK['accent_red']}; letter-spacing: 4px;
  background: rgba(255,255,255,.5); }}
.footlabel {{ position: absolute; bottom: 60px; left: 0; right: 0; text-align: center;
  font-size: 32px; color: {TOK['muted']}; letter-spacing: 2px; }}
</style></head><body>
<div class="title">ChatGPT</div>
<div class="msg-user">
  <div class="bubble-user">帮我写周报</div>
</div>
<div class="stamp">通用垃圾</div>
<div class="msg-ai">
  <div class="avatar">AI</div>
  <div class="bubble-ai">
    <h4>周报</h4>
    <p><b>本周工作：</b></p>
    <p>1. 参加了会议，讨论了相关事项</p>
    <p>2. 完成了本周的工作任务</p>
    <p>3. 与同事进行了有效的沟通</p>
    <p style="margin-top:14px"><b>下周计划：</b></p>
    <p>1. 继续推进相关工作</p>
    <p>2. 优化现有流程</p>
    <p>3. 加强团队协作</p>
  </div>
</div>
<div class="footlabel">↑ 一眼假 · 老板看得穿</div>
</body></html>"""
    shot(html, "04_ai_wrong_prompt.png")


# ═══ M6 · AI 对话框 · 黄金 prompt 五段结构（可截图带走）═══
def gen_ai_gold_prompt() -> None:
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
{BASE_CSS}
body {{ background: {TOK['canvas']}; color: {TOK['surface']}; padding: 60px 50px;
  font-family: "SF Mono", "JetBrains Mono", Menlo, monospace; }}
.title {{ font-family: -apple-system, "PingFang SC", sans-serif; font-size: 46px; font-weight: 700;
  margin-bottom: 20px; letter-spacing: 2px; }}
.subtitle {{ font-family: -apple-system, "PingFang SC", sans-serif; font-size: 26px; color: {TOK['muted']}; margin-bottom: 40px; }}
.line {{ font-size: 30px; line-height: 1.7; margin: 6px 0; letter-spacing: 0.5px; }}
.tag {{ display: inline-block; background: {TOK['accent_soft']}; color: {TOK['ink']};
  padding: 6px 14px; border-radius: 6px; font-weight: 700; font-size: 26px;
  font-family: -apple-system, "PingFang SC", sans-serif; margin-right: 16px; }}
.p-title {{ margin: 34px 0 10px; font-family: -apple-system, "PingFang SC", sans-serif;
  font-size: 34px; font-weight: 600; color: {TOK['accent_soft']}; }}
.p-text {{ font-size: 28px; line-height: 1.6; color: {TOK['surface']}; opacity: .9; padding-left: 20px; }}
.footlabel {{ position: absolute; bottom: 60px; left: 50px; font-family: -apple-system, "PingFang SC", sans-serif;
  font-size: 30px; color: {TOK['muted']}; letter-spacing: 2px; }}
</style></head><body>
<div class="title">下班前 5 分钟 · 救命 prompt</div>
<div class="subtitle">收藏本页 · 复制到 AI 对话框 · 300 字周报出</div>

<div class="p-title"><span class="tag">1 · 角色</span>你是谁</div>
<div class="p-text">你是一位职场写作助手，别整那些花的。</div>

<div class="p-title"><span class="tag">2 · 规矩</span>三块结构</div>
<div class="p-text">格式分三块：本周总结 / 下周计划 / 遇到的问题。每块用一句话概括。</div>

<div class="p-title"><span class="tag">3 · 反例</span>不写什么</div>
<div class="p-text">别写「参加了会议」「进行了沟通」这种没有信息量的话。</div>

<div class="p-title"><span class="tag">4 · 兜底</span>缺什么补什么</div>
<div class="p-text">如果原始记录里没有「下周计划」，请根据本周工作合理推断。</div>

<div class="p-title"><span class="tag">5 · 字数</span>不啰嗦</div>
<div class="p-text">总字数控制在 300 字以内。</div>

<div class="footlabel">→ 后附：把这周乱七八糟的记录粘在下面</div>
</body></html>"""
    shot(html, "05_ai_gold_prompt.png")


# ═══ M5 · 备忘录乱七八糟记录（generated_fact 示例）═══
def gen_memo_random() -> None:
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
{BASE_CSS}
body {{ background: {TOK['surface']}; color: {TOK['ink']}; padding: 60px 50px;
  font-family: "SF Mono", "JetBrains Mono", Menlo, monospace; }}
.title {{ font-family: -apple-system, "PingFang SC", sans-serif; font-size: 44px; font-weight: 700; margin-bottom: 10px; }}
.date {{ color: {TOK['muted']}; font-size: 26px; margin-bottom: 30px; font-family: "SF Mono"; }}
.line {{ font-size: 32px; line-height: 1.7; margin: 8px 0; letter-spacing: 0.5px; }}
.line em {{ font-style: normal; color: {TOK['muted']}; }}
.tag {{ color: {TOK['accent_red']}; }}
.stamp {{ position: absolute; top: 100px; right: 60px; transform: rotate(6deg);
  border: 4px solid {TOK['ink']}; padding: 10px 26px;
  font-family: -apple-system, "PingFang SC", sans-serif;
  font-size: 26px; font-weight: 600; letter-spacing: 2px;
  background: rgba(245,245,240,.9); }}
</style></head><body>
<div class="stamp">generated_fact · 示例</div>
<div class="title">本周记事</div>
<div class="date">周一 07/01 → 周五 07/04</div>

<div class="line">周一 09:30 <em>—</em> 客户 A 来电，改需求，第三次</div>
<div class="line">周一 14:00 <em>—</em> 跟运营对齐 landing 页文案</div>
<div class="line">周二 <em>—</em> 帮小张改 PPT 两次 <span class="tag">又是这个</span></div>
<div class="line">周二 16:00 <em>—</em> 数据周会，讲了 Q3 目标</div>
<div class="line">周三 <em>—</em> 处理售后工单 14 条，午饭都没吃</div>
<div class="line">周三 21:30 <em>—</em> 老板问 XX 项目进度</div>
<div class="line">周四 <em>—</em> 面试 3 个候选，都不太行</div>
<div class="line">周四 <em>—</em> 改合同附件版本 v3 v4 v5</div>
<div class="line">周五上午 <em>—</em> 报销 · 打车 · 差旅</div>
<div class="line">周五 15:00 <em>—</em> 周会，被点名下周要出方案</div>
<div class="line">周五 17:00 <em>—</em> 客户 B 突然来问价格 <span class="tag">急</span></div>
<div class="line">周五 18:55 <em>—</em> 老板问「周报呢」</div>
<div class="line">周五 18:56 <em>—</em> 我：草</div>
</body></html>"""
    shot(html, "06_memo_random.png")


# ═══ M5 · 微信群消息 ═══
def gen_wechat_group() -> None:
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
{BASE_CSS}
body {{ background: #ededed; color: {TOK['ink']}; }}
.header {{ background: #ededed; padding: 24px 30px; text-align: center; border-bottom: 1px solid #d5d5d5; }}
.hname {{ font-size: 36px; font-weight: 600; }}
.hcount {{ font-size: 26px; color: {TOK['muted']}; margin-top: 6px; }}
.msgs {{ padding: 30px 20px; }}
.time-div {{ text-align: center; margin: 20px 0; font-size: 24px; color: {TOK['muted']}; }}
.row {{ display: flex; gap: 20px; margin: 30px 0; align-items: flex-start; }}
.row.me {{ flex-direction: row-reverse; }}
.avatar {{ width: 80px; height: 80px; border-radius: 12px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center; font-size: 36px; font-weight: 700; color: white; }}
.a1 {{ background: {TOK['wechat_green']}; }}.a2 {{ background: #ff9500; }}.a3 {{ background: #af52de; }}
.a4 {{ background: #ff375f; }}.a5 {{ background: #64d2ff; }}
.body {{ max-width: 720px; }}
.name {{ font-size: 24px; color: {TOK['muted']}; margin-bottom: 8px; padding: 0 4px; }}
.row.me .name {{ text-align: right; display: none; }}
.bubble {{ background: white; padding: 22px 26px; border-radius: 16px; font-size: 32px; line-height: 1.4;
  box-shadow: 0 1px 2px rgba(0,0,0,.04); }}
.row.me .bubble {{ background: {TOK['wechat_green']}; }}
.stamp {{ position: absolute; top: 130px; right: 60px; transform: rotate(6deg);
  border: 4px solid {TOK['ink']}; padding: 10px 26px;
  font-family: -apple-system, "PingFang SC", sans-serif;
  font-size: 26px; font-weight: 600; letter-spacing: 2px;
  background: rgba(255,255,255,.9); }}
</style></head><body>
<div class="stamp">generated_fact · 示例</div>
<div class="header">
  <div class="hname">项目群 · Q3 冲刺</div>
  <div class="hcount">15 人</div>
</div>
<div class="msgs">
  <div class="time-div">周五 15:24</div>
  <div class="row"><div class="avatar a1">刘</div><div class="body">
    <div class="name">刘总</div><div class="bubble">下周的 review 大家准备一下</div></div></div>
  <div class="row"><div class="avatar a2">小</div><div class="body">
    <div class="name">小张</div><div class="bubble">收到 老板</div></div></div>
  <div class="row"><div class="avatar a3">阿</div><div class="body">
    <div class="name">阿泽</div><div class="bubble">数据要不要更新到最新的？</div></div></div>
  <div class="time-div">周五 17:41</div>
  <div class="row"><div class="avatar a4">M</div><div class="body">
    <div class="name">Mia · 运营</div><div class="bubble">周报模板换新的吗？</div></div></div>
  <div class="row"><div class="avatar a5">王</div><div class="body">
    <div class="name">王工</div><div class="bubble">周报不写行不行……</div></div></div>
  <div class="row me"><div class="avatar" style="background:#95ec69">我</div><div class="body">
    <div class="bubble">在写在写</div></div></div>
</div>
</body></html>"""
    shot(html, "07_wechat_group.png")


# ═══ M5 · 日历本周 ═══
def gen_calendar_week() -> None:
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
{BASE_CSS}
body {{ background: {TOK['surface']}; color: {TOK['ink']};
  font-family: -apple-system, "PingFang SC", sans-serif; padding: 40px 30px; }}
.title {{ font-size: 44px; font-weight: 700; margin-bottom: 20px; }}
.week {{ font-size: 30px; color: {TOK['muted']}; margin-bottom: 30px; }}
.grid {{ display: grid; grid-template-columns: 100px repeat(5, 1fr); gap: 6px; }}
.dow {{ text-align: center; padding: 16px 0; font-weight: 600; font-size: 26px; color: {TOK['muted']}; }}
.dow.today {{ color: {TOK['accent_red']}; }}
.hour {{ text-align: right; padding: 12px 12px 0 0; font-size: 22px; color: {TOK['muted']}; font-family: "SF Mono"; }}
.slot {{ background: #efede8; min-height: 90px; border-radius: 6px; padding: 12px; font-size: 22px; line-height: 1.4; }}
.slot.event-1 {{ background: {TOK['accent_soft']}; color: {TOK['ink']}; }}
.slot.event-2 {{ background: #ffb1a1; color: {TOK['ink']}; }}
.slot.event-3 {{ background: #b1e1ff; color: {TOK['ink']}; }}
.slot.event-4 {{ background: {TOK['accent_red']}; color: white; }}
.slot .t {{ font-weight: 700; }}
.stamp {{ position: absolute; top: 60px; right: 40px; transform: rotate(6deg);
  border: 4px solid {TOK['ink']}; padding: 10px 26px;
  font-size: 26px; font-weight: 600; letter-spacing: 2px;
  background: rgba(245,245,240,.9); }}
</style></head><body>
<div class="stamp">generated_fact · 示例</div>
<div class="title">日历 · 本周</div>
<div class="week">7 月 1 日 · 周一 → 7 月 5 日 · 周五</div>
<div class="grid">
  <div class="hour"></div>
  <div class="dow">周一</div><div class="dow">周二</div><div class="dow">周三</div><div class="dow">周四</div><div class="dow today">周五</div>

  <div class="hour">10:00</div>
  <div class="slot event-1"><div class="t">客户 A</div>改需求</div>
  <div class="slot"></div>
  <div class="slot event-2"><div class="t">工单激增</div>14 条</div>
  <div class="slot event-3"><div class="t">面试</div>3 位候选人</div>
  <div class="slot"></div>

  <div class="hour">14:00</div>
  <div class="slot event-3"><div class="t">对齐 landing</div>运营</div>
  <div class="slot event-1"><div class="t">改 PPT</div>小张</div>
  <div class="slot"></div>
  <div class="slot event-1"><div class="t">改合同 v3</div></div>
  <div class="slot event-2"><div class="t">周会</div>要出方案</div>

  <div class="hour">17:00</div>
  <div class="slot"></div>
  <div class="slot event-3"><div class="t">数据周会</div>Q3 目标</div>
  <div class="slot event-2"><div class="t">老板问 XX</div>21:30</div>
  <div class="slot"></div>
  <div class="slot event-4"><div class="t">客户 B</div>问价格 · 急</div>

  <div class="hour">18:55</div>
  <div class="slot"></div><div class="slot"></div><div class="slot"></div><div class="slot"></div>
  <div class="slot event-4"><div class="t">老板 @我</div>「周报呢？」</div>
</div>
</body></html>"""
    shot(html, "08_calendar_week.png")


# ═══ M7 · 原始流水账（红字标注混乱）═══
def gen_raw_annotated() -> None:
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
{BASE_CSS}
body {{ background: {TOK['surface']}; color: {TOK['ink']}; padding: 60px 50px;
  font-family: "SF Mono", "JetBrains Mono", Menlo, monospace; }}
.title {{ font-family: -apple-system, "PingFang SC", sans-serif; font-size: 42px; font-weight: 700; margin-bottom: 10px; }}
.stamp {{ position: absolute; top: 100px; right: 60px; transform: rotate(6deg);
  border: 4px solid {TOK['accent_red']}; padding: 10px 26px;
  font-family: -apple-system, "PingFang SC", sans-serif;
  font-size: 30px; font-weight: 700; color: {TOK['accent_red']}; letter-spacing: 2px;
  background: rgba(245,245,240,.9); }}
.subtitle {{ color: {TOK['muted']}; font-size: 26px; margin-bottom: 30px; }}
.line {{ font-size: 28px; line-height: 1.6; margin: 6px 0; letter-spacing: 0.3px; position: relative; }}
.line em {{ font-style: normal; color: {TOK['muted']}; }}
.crit {{ position: absolute; right: -10px; top: 4px; color: {TOK['accent_red']}; font-size: 22px;
  font-family: -apple-system, "PingFang SC", sans-serif; font-weight: 600; }}
.underline {{ text-decoration: line-through wavy; text-decoration-color: {TOK['accent_red']}; }}
</style></head><body>
<div class="stamp">改造前</div>
<div class="title">本周记事（原始流水账）</div>
<div class="subtitle">时间顺序 · 缺归类 · 缺重点 · 缺下周</div>
<div class="line"><span class="underline">周一 09:30 客户 A 改需求 第三次</span><span class="crit">← 归到"客户 A"</span></div>
<div class="line">周一 14:00 跟运营对齐 landing 文案</div>
<div class="line"><span class="underline">周二 帮小张改 PPT 两次</span><span class="crit">← 帮工不该在总结</span></div>
<div class="line">周二 16:00 数据周会，讲了 Q3 目标</div>
<div class="line"><span class="underline">周三 处理售后工单 14 条 午饭都没吃</span><span class="crit">← 数字对但情绪不必写</span></div>
<div class="line">周三 21:30 老板问 XX 项目进度</div>
<div class="line"><span class="underline">周四 面试 3 个候选</span><span class="crit">← 结果没写</span></div>
<div class="line">周四 改合同附件版本 v3 v4 v5</div>
<div class="line"><span class="underline">周五上午 报销 打车 差旅</span><span class="crit">← 事务不算工作</span></div>
<div class="line">周五 15:00 周会，被点名下周要出方案</div>
<div class="line">周五 17:00 客户 B 突然来问价格</div>
<div class="line"><span class="underline">周五 18:56 我：草</span><span class="crit">← 别发出去 :)</span></div>
</body></html>"""
    shot(html, "09_raw_annotated.png")


# ═══ M7 · AI 整理后周报（结构清爽）═══
def gen_ai_organized() -> None:
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
{BASE_CSS}
body {{ background: {TOK['surface']}; color: {TOK['ink']};
  font-family: -apple-system, "PingFang SC", sans-serif; padding: 60px 50px; }}
.stamp {{ position: absolute; top: 100px; right: 60px; transform: rotate(-6deg);
  border: 4px solid {TOK['excel_green']}; padding: 10px 26px;
  font-size: 30px; font-weight: 700; color: {TOK['excel_green']}; letter-spacing: 2px;
  background: rgba(245,245,240,.9); }}
.title {{ font-size: 44px; font-weight: 700; margin-bottom: 12px; }}
.meta {{ color: {TOK['muted']}; font-size: 26px; margin-bottom: 34px; }}
.sec {{ margin: 30px 0; }}
.sec h2 {{ font-size: 34px; font-weight: 700; color: {TOK['ink']}; margin-bottom: 16px;
  padding-left: 22px; border-left: 8px solid {TOK['excel_green']}; }}
.sec ol, .sec ul {{ padding-left: 40px; }}
.sec li {{ font-size: 30px; line-height: 1.6; margin: 12px 0; }}
.footlabel {{ position: absolute; bottom: 60px; left: 50px; font-size: 26px; color: {TOK['muted']}; letter-spacing: 2px; }}
</style></head><body>
<div class="stamp">改造后</div>
<div class="title">本周工作周报</div>
<div class="meta">姓名 · 部门 · 06/30 – 07/04 · 共 268 字</div>

<div class="sec">
  <h2>本周完成</h2>
  <ol>
    <li>客户 A 需求 3 轮迭代收敛，本周确认最终版</li>
    <li>Q3 目标数据梳理并周会同步，产运达成一致</li>
    <li>售后 14 条工单当天清零，SLA 保住</li>
    <li>面试 3 名候选，未通过，Q3 用人计划待调</li>
  </ol>
</div>

<div class="sec">
  <h2>下周计划</h2>
  <ol>
    <li>7/8 前出下周复盘方案（周会被点名）</li>
    <li>客户 B 报价单本周内敲定</li>
    <li>合同 v6 定稿并归档</li>
  </ol>
</div>

<div class="sec">
  <h2>遇到的问题</h2>
  <ul>
    <li>Q3 用人缺口未补，招聘节奏偏慢</li>
    <li>需求变更频次仍偏高，希望 PM 前置</li>
  </ul>
</div>
<div class="footlabel">总字数 268 · 300 字以内</div>
</body></html>"""
    shot(html, "10_ai_organized.png")


# ═══ M8 · 傍晚窗外 + 大字价值锚 ═══
def gen_value_anchor() -> None:
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
{BASE_CSS}
body {{ background: linear-gradient(180deg, #2a1f14 0%, #4a2e1a 40%, #241812 100%);
  color: {TOK['surface']}; position: relative;
  font-family: -apple-system, "PingFang SC", sans-serif; }}
.glow {{ position: absolute; top: 20%; left: -20%; right: -20%; height: 60%;
  background: radial-gradient(ellipse at center, rgba(255, 180, 90, 0.25) 0%, transparent 60%);
  pointer-events: none; }}
.wrap {{ position: absolute; top: 50%; left: 60px; right: 60px; transform: translateY(-50%); text-align: center; }}
.line1 {{ font-size: 92px; font-weight: 700; line-height: 1.25; letter-spacing: 3px; margin-bottom: 26px; }}
.line2 {{ font-size: 92px; font-weight: 900; line-height: 1.25; letter-spacing: 4px;
  color: {TOK['accent_soft']}; }}
.dot-sep {{ font-size: 60px; margin: 0 8px; color: rgba(255,255,255,0.4); }}
</style></head><body>
<div class="glow"></div>
<div class="wrap">
  <div class="line1">不是教你写周报</div>
  <div class="line2">是把我下班前 5 分钟的救命 prompt 给你</div>
</div>
</body></html>"""
    shot(html, "11_value_anchor.png")


# ═══ M9 · CTA 便签 ═══
def gen_cta_note() -> None:
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
{BASE_CSS}
body {{ background: #26221c; position: relative;
  display: flex; align-items: center; justify-content: center; }}
.note {{ background: {TOK['surface']}; width: 900px; height: 1200px; padding: 80px 70px;
  border-radius: 8px; box-shadow: 0 40px 80px rgba(0,0,0,.5);
  transform: rotate(-2deg);
  font-family: -apple-system, "PingFang SC", sans-serif; color: {TOK['ink']}; position: relative; }}
.note::before {{ content: ""; position: absolute; top: 60px; left: 50%; transform: translateX(-50%);
  width: 200px; height: 40px; background: #d4a05b; border-radius: 4px;
  box-shadow: 0 6px 12px rgba(0,0,0,.15); }}
.title {{ margin-top: 100px; font-size: 60px; font-weight: 700; line-height: 1.35; letter-spacing: 2px; }}
.sub {{ margin-top: 40px; font-size: 46px; font-weight: 400; line-height: 1.4; color: {TOK['ink']}; }}
.cursor {{ display: inline-block; width: 6px; height: 60px; background: {TOK['ink']};
  animation: blink 1s infinite; vertical-align: -12px; margin-left: 4px; }}
@keyframes blink {{ 50% {{ opacity: 0; }} }}
.line-hr {{ margin-top: 60px; font-size: 32px; color: {TOK['muted']}; }}
.hint {{ margin-top: 20px; font-size: 32px; color: {TOK['muted']}; letter-spacing: 1px; }}
</style></head><body>
<div class="note">
  <div class="title">评论你的岗位</div>
  <div class="sub">和上次因为周报<br>加班到几点<span class="cursor"></span></div>
  <div class="line-hr">─────</div>
  <div class="hint">按行业发一版 prompt</div>
</div>
</body></html>"""
    shot(html, "12_cta_note.png")


def main() -> None:
    print(f"→ 输出到 {OUT}")
    gen_iphone_lockscreen()
    gen_wechat_boss_ping()
    gen_excel_empty()
    gen_ai_wrong_prompt()
    gen_ai_gold_prompt()
    gen_memo_random()
    gen_wechat_group()
    gen_calendar_week()
    gen_raw_annotated()
    gen_ai_organized()
    gen_value_anchor()
    gen_cta_note()
    print(f"\n✓ 12 张 UI 仿真素材生成完成")
    print(f"  查看：ls {OUT}")


if __name__ == "__main__":
    main()
