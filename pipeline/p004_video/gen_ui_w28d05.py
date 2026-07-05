#!/usr/bin/env python3
"""W28D05 UI 叠层 PNG 生成 · Chrome headless 静态素材路径.

对齐 pipeline_config.yaml 的 9 张 assets_ui/*.png：
  01_m2_reveal_bigtext.png     · M2 睡姿续图 + 90pt 双行大字 (无 drawtext overlay · 必须 baked)
  02_m3_split_40h_8h.png       · M3 分屏底图 (大字 40h→8h 由 drawtext)
  03_m4_5_ai_icon_grid.png     · M4 5 AI 图标网格 (小 SVG · 禁大 logo)
  04_m5_n8n_half.png           · M5 n8n workflow 半成品 8 节点 (每节点 "需 review" 红标)
  05_m6_split_typing_wechat.png · M6 打字 vs 微信客户沟通分屏底图 (化名 · 打码)
  06_m7_3_layer_stack.png      · M7 Notion + Cursor + n8n 三层堆叠 UI (本片最重)
  07_m8_60_20_20_table.png     · M8 3 列表格框 + 底注 (60/20/20 数字由 drawtext)
  08_m9_value_anchor.png       · M9 纯黑底 (大字全 drawtext)
  09_m10_cta.png               · M10 纯黑底 (CTA 全 drawtext)

色板 (design_language.md 硬门):
  canvas_office_dark  #1a1a1a
  canvas_pure_dark    #000000
  ink_light           #f5f5f0
  muted               #7a7a7a
  accent_red          #e53935 (禁 #ff5252 偏粉红)
  notion_dark         #191919 · cursor_dark #181818 · n8n_dark #101330 · n8n_orange #ff6d5a
  cursor_teal         #00d4aa (代码高亮)
  禁 Dracula: #bd93f9 · #ff79c6 · #8be9fd (gate_check_palette.py 硬拦)

用法:
  python3 pipeline/p004_video/gen_ui_w28d05.py

依赖:
  Chrome + macOS · headless=new
"""
from __future__ import annotations

import pathlib
import subprocess
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "publish" / "2026-W28" / "D05-AI帮我一周活干成一天" / "build" / "assets_ui"
OUT.mkdir(parents=True, exist_ok=True)

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
W, H = 1080, 1920

TOK = {
    "canvas_office_dark": "#1a1a1a",
    "canvas_pure_dark": "#000000",
    "ink_light": "#f5f5f0",
    "muted": "#7a7a7a",
    "accent_red": "#e53935",
    "notion_dark": "#191919",
    "cursor_dark": "#181818",
    "n8n_dark": "#101330",
    "n8n_orange": "#ff6d5a",
    "cursor_teal": "#00d4aa",
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


# ═══ M2 · 1.4s · 全屏黑蒙层 + 90pt 双行大字 (无 drawtext overlay · 必 baked) ═══
def gen_m2_reveal_bigtext() -> None:
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
{BASE_CSS}
body {{ background: {TOK['canvas_pure_dark']}; color: {TOK['ink_light']};
       display: flex; flex-direction: column; justify-content: center; align-items: center;
       padding: 0 60px; }}
.line {{ font-size: 90px; font-weight: 900; line-height: 1.35; letter-spacing: -1px;
        text-align: center; text-shadow: 0 4px 20px rgba(0,0,0,0.8); }}
.mask {{ position: absolute; top: 0; left: 0; width: 100%; height: 100%;
        background: rgba(0,0,0,0.65); z-index: 1; }}
.text-wrap {{ position: relative; z-index: 2; }}
</style></head><body>
<div class="mask"></div>
<div class="text-wrap">
  <div class="line">我睡着的时候</div>
  <div class="line" style="margin-top: 24px;">系统已经跑完了昨晚的活</div>
</div>
</body></html>"""
    shot(html, "01_m2_reveal_bigtext.png")


# ═══ M3 · 5s · 分屏底图 40h vs 8h (大字 headline 由 drawtext 覆盖) ═══
def gen_m3_split_40h_8h() -> None:
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
{BASE_CSS}
body {{ background: {TOK['canvas_pure_dark']}; color: {TOK['ink_light']}; position: relative; }}
.split {{ display: flex; height: 100%; }}
.side {{ flex: 1; display: flex; flex-direction: column; align-items: center;
        justify-content: flex-end; padding: 80px 40px; }}
.left {{ background: #0a0e14; }}
.right {{ background: #1a1611; }}
.divider {{ position: absolute; left: 50%; top: 0; width: 3px; height: 100%;
           background: {TOK['ink_light']}; opacity: 0.3; transform: translateX(-50%); }}
.label {{ font-size: 42px; font-weight: 700; opacity: 0.75; letter-spacing: 1px; }}
.sub {{ font-size: 28px; opacity: 0.55; margin-top: 12px; }}
.clock {{ font-family: "SF Mono", monospace; font-size: 96px; font-weight: 800;
         color: {TOK['ink_light']}; opacity: 0.9; margin-bottom: 40px;
         text-shadow: 0 0 30px rgba(255,200,150,0.3); }}
.clock-left {{ text-shadow: 0 0 20px rgba(200,180,150,0.25); }}
</style></head><body>
<div class="split">
  <div class="side left">
    <div class="clock clock-left">01:00</div>
    <div class="label">凌晨 · 改方案</div>
    <div class="sub">还在改方案 / 疲惫</div>
  </div>
  <div class="side right">
    <div class="clock">08:00</div>
    <div class="label">晨光 · 看推送</div>
    <div class="sub">系统已跑完昨晚活</div>
  </div>
</div>
<div class="divider"></div>
</body></html>"""
    shot(html, "02_m3_split_40h_8h.png")


# ═══ M4 · 7s · 5 AI 图标网格 (小 SVG · 禁大 logo) ═══
def gen_m4_5_ai_icon_grid() -> None:
    icons = [
        ("ChatGPT", "#10a37f", "◐"),
        ("Claude", "#c9884b", "✦"),
        ("Cursor", "#00d4aa", "▲"),
        ("Notion", "#f5f5f0", "◧"),
        ("n8n", "#ff6d5a", "⬢"),
    ]
    cells = ""
    for name, color, glyph in icons:
        cells += f"""
      <div class="cell">
        <div class="icon" style="color: {color};">{glyph}</div>
        <div class="name">{name}</div>
      </div>"""
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
{BASE_CSS}
body {{ background: {TOK['canvas_pure_dark']}; color: {TOK['ink_light']};
       display: flex; flex-direction: column; align-items: center;
       justify-content: center; padding: 60px; }}
.grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 60px 80px;
        margin-top: 60px; }}
.cell {{ display: flex; flex-direction: column; align-items: center; gap: 24px;
        padding: 40px 30px; border: 2px solid rgba(245,245,240,0.15);
        border-radius: 20px; width: 260px; background: rgba(255,255,255,0.03); }}
.icon {{ font-size: 120px; line-height: 1; }}
.name {{ font-size: 36px; font-weight: 600; opacity: 0.85; }}
.hint {{ font-size: 28px; opacity: 0.5; margin-top: 40px; }}
</style></head><body>
<div class="grid">{cells}</div>
<div class="hint">切换 5 个应用 · 40 min 没了</div>
</body></html>"""
    shot(html, "03_m4_5_ai_icon_grid.png")


# ═══ M5 · 5s · n8n workflow 半成品 8 节点 (每节点 "需 review" 红标) ═══
def gen_m5_n8n_half() -> None:
    nodes = [
        ("Webhook", 120, 500),
        ("Filter", 320, 500),
        ("OpenAI", 520, 500),
        ("If Node", 720, 500),
        ("HTTP", 220, 900),
        ("Merge", 420, 900),
        ("Sheet", 620, 900),
        ("Email", 820, 900),
    ]
    node_html = ""
    for name, x, y in nodes:
        node_html += f"""
      <div class="node" style="left: {x}px; top: {y}px;">
        <div class="node-name">{name}</div>
        <div class="node-flag">需 review</div>
      </div>"""
    # crude connecting lines (SVG)
    lines = """
      <line x1="240" y1="580" x2="320" y2="580" />
      <line x1="440" y1="580" x2="520" y2="580" />
      <line x1="640" y1="580" x2="720" y2="580" />
      <line x1="180" y1="660" x2="180" y2="900" />
      <line x1="340" y1="980" x2="420" y2="980" />
      <line x1="540" y1="980" x2="620" y2="980" />
      <line x1="740" y1="980" x2="820" y2="980" />
    """
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
{BASE_CSS}
body {{ background: {TOK['n8n_dark']}; color: {TOK['ink_light']}; position: relative; }}
.canvas {{ position: absolute; top: 0; left: 0; width: 100%; height: 100%; }}
.node {{ position: absolute; width: 200px; height: 120px; border-radius: 12px;
        background: rgba(255,109,90,0.18); border: 2px solid {TOK['n8n_orange']};
        display: flex; flex-direction: column; align-items: center; justify-content: center;
        gap: 8px; }}
.node-name {{ font-size: 30px; font-weight: 600; color: {TOK['ink_light']}; }}
.node-flag {{ font-size: 22px; color: {TOK['accent_red']}; font-weight: 700;
             letter-spacing: 1px; }}
.title {{ position: absolute; top: 100px; left: 60px; font-size: 44px; font-weight: 700;
         opacity: 0.85; }}
.subtitle {{ position: absolute; top: 170px; left: 60px; font-size: 28px;
            opacity: 0.55; }}
.footer {{ position: absolute; bottom: 200px; left: 0; right: 0; text-align: center;
          font-size: 32px; color: {TOK['accent_red']}; font-weight: 700; }}
svg {{ position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; }}
svg line {{ stroke: {TOK['n8n_orange']}; stroke-width: 3; stroke-dasharray: 6 6;
           opacity: 0.6; }}
</style></head><body>
<div class="title">workflow_v0.3</div>
<div class="subtitle">Project-001 · 每节点都要人 review · 3 个月没跑通</div>
<svg>{lines}</svg>
<div class="canvas">{node_html}</div>
<div class="footer">8 节点 × 每节点人 review = 半成品</div>
</body></html>"""
    shot(html, "04_m5_n8n_half.png")


# ═══ M6 · 5s · 打字 vs 微信客户沟通分屏底图 (化名 · 打码) ═══
def gen_m6_split_typing_wechat() -> None:
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
{BASE_CSS}
body {{ background: {TOK['canvas_pure_dark']}; color: {TOK['ink_light']}; position: relative; }}
.split {{ display: flex; flex-direction: column; height: 100%; }}
.pane {{ flex: 1; padding: 60px 50px; position: relative; }}
.left {{ background: #2a2620; border-bottom: 2px solid rgba(245,245,240,0.15); }}
.right {{ background: #0f1a12; }}
.label {{ font-size: 34px; font-weight: 700; opacity: 0.9; letter-spacing: 1px;
         margin-bottom: 30px; }}
.time-cost {{ font-family: "SF Mono", monospace; font-size: 88px; font-weight: 800;
             margin-top: 20px; }}
.small {{ font-size: 26px; opacity: 0.55; margin-top: 12px; }}
.text-input {{ background: #191919; border: 1px solid #333; border-radius: 8px;
              padding: 20px; font-family: "SF Mono", monospace; font-size: 24px;
              color: #7a7a7a; margin-top: 20px; height: 200px; }}
.wechat-msg {{ background: #95ec69; color: #111; border-radius: 12px;
              padding: 18px 24px; font-size: 26px; max-width: 480px; margin: 12px 0;
              position: relative; }}
.wechat-mine {{ background: #f0f0f0; margin-left: auto; }}
.mosaic {{ display: inline-block; background: repeating-linear-gradient(45deg, #666, #666 4px, #888 4px, #888 8px);
          padding: 0 8px; color: transparent; border-radius: 4px; }}
</style></head><body>
<div class="split">
  <div class="pane left">
    <div class="label">打字自动化 · 好搞</div>
    <div class="text-input">for each row in sheet:<br/>&nbsp;&nbsp;send(email, template)<br/>&nbsp;&nbsp;log(row.id)<br/>...</div>
    <div class="time-cost" style="color: {TOK['accent_red']};">10 min</div>
    <div class="small">脚本 20 行 · 一次搞定</div>
  </div>
  <div class="pane right">
    <div class="label">客户沟通 · <span class="mosaic">王总</span> 6h</div>
    <div class="wechat-msg">这方案我们董事会讨论过 · 有几个点想再确认</div>
    <div class="wechat-msg wechat-mine">好 · 我发个补充文档</div>
    <div class="wechat-msg">对了 · 上次那个报价能不能调</div>
    <div class="time-cost" style="color: {TOK['accent_red']};">6 h</div>
    <div class="small">一个字没碰 · 全靠人</div>
  </div>
</div>
</body></html>"""
    shot(html, "05_m6_split_typing_wechat.png")


# ═══ M7 · 15s · Notion + Cursor + n8n 三层堆叠 UI (本片最重镜) ═══
def gen_m7_3_layer_stack() -> None:
    # 3 卡纵向堆叠 · 每层约 500px 高 · 顶部 20px 留白给"散架"红字
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
{BASE_CSS}
body {{ background: {TOK['canvas_pure_dark']}; color: {TOK['ink_light']};
       padding: 120px 60px 60px; display: flex; flex-direction: column; gap: 30px; }}
.layer {{ flex: 1; border-radius: 20px; padding: 40px 50px; position: relative;
         box-shadow: 0 8px 32px rgba(0,0,0,0.5); overflow: hidden; }}
.layer-order {{ position: absolute; top: 20px; right: 30px; font-size: 100px;
               font-weight: 900; opacity: 0.08; line-height: 1; }}
.layer-title {{ font-size: 34px; font-weight: 700; opacity: 0.85;
                margin-bottom: 20px; letter-spacing: 1px; }}

/* Notion */
.notion {{ background: {TOK['notion_dark']}; border: 1px solid #2a2a2a; }}
.notion-title {{ color: {TOK['ink_light']}; }}
.sop-item {{ display: flex; align-items: center; gap: 16px; font-size: 26px;
             padding: 10px 0; opacity: 0.85; }}
.sop-item .box {{ width: 24px; height: 24px; border: 2px solid #666; border-radius: 4px;
                 background: {TOK['notion_dark']}; }}
.sop-item.done .box {{ background: #4caf50; border-color: #4caf50; }}

/* Cursor */
.cursor {{ background: {TOK['cursor_dark']}; border: 1px solid #262626; }}
.cursor-tab {{ background: #222; padding: 6px 20px; border-radius: 6px 6px 0 0;
              font-size: 22px; opacity: 0.7; display: inline-block; margin-bottom: 8px; }}
.code {{ font-family: "SF Mono", monospace; font-size: 22px; line-height: 1.55;
        color: {TOK['ink_light']}; opacity: 0.9; }}
.kw {{ color: {TOK['cursor_teal']}; }}
.str {{ color: #ffc857; }}
.cm {{ color: #7a7a7a; }}

/* n8n */
.n8n {{ background: {TOK['n8n_dark']}; border: 1px solid #1a1e40; }}
.n8n-flow {{ display: flex; align-items: center; gap: 16px; margin-top: 20px;
            flex-wrap: wrap; }}
.n8n-node {{ background: rgba(255,109,90,0.2); border: 1.5px solid {TOK['n8n_orange']};
            border-radius: 8px; padding: 12px 20px; font-size: 24px; color: {TOK['ink_light']}; }}
.n8n-arrow {{ color: {TOK['n8n_orange']}; font-size: 28px; opacity: 0.7; }}
</style></head><body>

<div class="layer notion">
  <div class="layer-order">1</div>
  <div class="layer-title notion-title">◧ Notion · 手工 SOP</div>
  <div class="sop-item done"><div class="box"></div>询盘进 · 打标签 (客户类型 / 预算)</div>
  <div class="sop-item done"><div class="box"></div>3 分钟内首回 · 模板 A/B/C 选一个</div>
  <div class="sop-item done"><div class="box"></div>方案生成 · 参考历史成交案例</div>
  <div class="sop-item"><div class="box"></div>决策点 · 报价 / 交付周期 (人)</div>
</div>

<div class="layer cursor">
  <div class="layer-order">2</div>
  <div class="layer-title">▲ Cursor + Claude · AI 辅助</div>
  <div class="cursor-tab">sop_to_prompt.md</div>
  <div class="code">
    <span class="cm"># 按 SOP 生成客户方案草稿</span><br/>
    <span class="kw">def</span> draft_proposal(inquiry, sop):<br/>
    &nbsp;&nbsp;prompt = <span class="str">"按 SOP 步骤 1-3 · 生成初稿"</span><br/>
    &nbsp;&nbsp;<span class="kw">return</span> claude.chat(sop, inquiry, prompt)<br/>
    <span class="cm"># prompt 模板 → Cursor 项目 rules</span>
  </div>
</div>

<div class="layer n8n">
  <div class="layer-order">3</div>
  <div class="layer-title">⬢ n8n · 系统自跑</div>
  <div class="n8n-flow">
    <div class="n8n-node">Webhook</div>
    <span class="n8n-arrow">→</span>
    <div class="n8n-node">分类 (Claude)</div>
    <span class="n8n-arrow">→</span>
    <div class="n8n-node">草稿 (SOP)</div>
    <span class="n8n-arrow">→</span>
    <div class="n8n-node">待决策</div>
    <span class="n8n-arrow">→</span>
    <div class="n8n-node">发出</div>
  </div>
  <div style="font-size: 22px; opacity: 0.55; margin-top: 24px;">
    SOP 变了 · workflow 只改 1 处 · 不散架
  </div>
</div>

</body></html>"""
    shot(html, "06_m7_3_layer_stack.png")


# ═══ M8 · 8s · 3 列表格底图 · 60/20/20 (数字大字由 drawtext) ═══
def gen_m8_60_20_20_table() -> None:
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
{BASE_CSS}
body {{ background: {TOK['canvas_pure_dark']}; color: {TOK['ink_light']};
       padding: 100px 40px 60px; }}
.header {{ text-align: center; font-size: 40px; font-weight: 700; opacity: 0.85;
          margin-bottom: 40px; }}
.grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px;
        margin-top: 480px; }}
.col {{ background: rgba(255,255,255,0.04); border-radius: 20px; padding: 40px 24px;
       border: 1.5px solid rgba(245,245,240,0.1); text-align: center; }}
.col.hi {{ background: rgba(229,57,53,0.12); border-color: rgba(229,57,53,0.4); }}
.col-label {{ font-size: 36px; font-weight: 700; opacity: 0.85;
             margin-bottom: 20px; }}
.col-hi-label {{ color: {TOK['accent_red']}; }}
.item {{ font-size: 26px; opacity: 0.75; margin: 12px 0; }}
.footer {{ text-align: center; font-size: 28px; opacity: 0.55; margin-top: 40px;
          letter-spacing: 2px; }}
</style></head><body>
<div class="header">每天 100% 时间 · 我这么分配</div>
<div class="grid">
  <div class="col hi">
    <div class="col-label col-hi-label">塞 AI</div>
    <div class="item">分类</div>
    <div class="item">草稿</div>
    <div class="item">翻译</div>
    <div class="item">答客户</div>
    <div class="item">搜索</div>
  </div>
  <div class="col">
    <div class="col-label">自动化</div>
    <div class="item">webhook</div>
    <div class="item">分类</div>
    <div class="item">推送</div>
    <div class="item">归档</div>
  </div>
  <div class="col">
    <div class="col-label">你决策</div>
    <div class="item">审美</div>
    <div class="item">关系</div>
    <div class="item">战略</div>
  </div>
</div>
<div class="footer">Project-001 实测 · 参考不套用</div>
</body></html>"""
    shot(html, "07_m8_60_20_20_table.png")


# ═══ M9 · 6s · 纯黑底 (大字全 drawtext) ═══
def gen_m9_value_anchor() -> None:
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
{BASE_CSS}
body {{ background: {TOK['canvas_pure_dark']}; }}
</style></head><body></body></html>"""
    shot(html, "08_m9_value_anchor.png")


# ═══ M10 · 4s · 纯黑底 (CTA 全 drawtext) ═══
def gen_m10_cta() -> None:
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
{BASE_CSS}
body {{ background: {TOK['canvas_pure_dark']}; }}
</style></head><body></body></html>"""
    shot(html, "09_m10_cta.png")


def main() -> None:
    print(f"→ W28D05 UI PNG 生成 · out={OUT}")
    gen_m2_reveal_bigtext()
    gen_m3_split_40h_8h()
    gen_m4_5_ai_icon_grid()
    gen_m5_n8n_half()
    gen_m6_split_typing_wechat()
    gen_m7_3_layer_stack()
    gen_m8_60_20_20_table()
    gen_m9_value_anchor()
    gen_m10_cta()
    print(f"✓ 9 张 UI PNG 全生成 · {OUT}")


if __name__ == "__main__":
    main()
