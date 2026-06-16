#!/usr/bin/env python3
"""路线 1 · 仿真证据素材。画布 1206×1608（3:4 一屏满铺）.

  python3 pipeline/gen_evidence.py
"""
from __future__ import annotations

import base64
import pathlib
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from pipeline.screen_dims import IPHONE_H, IPHONE_W

OUT = ROOT / "assets" / "broll" / "generated"
SHOTS = ROOT / "assets" / "shots"
PINS = pathlib.Path("/Users/bubu/Documents/projects/Pinterest/pins/final")
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
W, H = IPHONE_W, IPHONE_H

ST_H, HOME_H, TAB_H = 54, 34, 83
MEMO_TOOL_H = 44


def body_h(*, tab: bool = False, tool: bool = False) -> int:
    h = H - ST_H - HOME_H
    if tab:
        h -= TAB_H
    if tool:
        h -= MEMO_TOOL_H
    return h


def b64(p: pathlib.Path) -> str:
    return base64.b64encode(p.read_bytes()).decode()


def src(p: pathlib.Path) -> str:
    return f"data:image/png;base64,{b64(p)}"


def shot(html: str, name: str) -> pathlib.Path:
    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / name
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as f:
        f.write(html)
        path = f.name
    subprocess.run(
        [CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
         f"--screenshot={out}", f"--window-size={W},{H}", "--force-device-scale-factor=1",
         f"file://{path}"],
        capture_output=True, timeout=120, check=True,
    )
    print("OK", out.name)
    return out


BASE = f"""
*{{margin:0;padding:0;box-sizing:border-box;}}
html,body{{width:{W}px;height:{H}px;overflow:hidden;
  font-family:-apple-system,BlinkMacSystemFont,"Hiragino Sans GB","PingFang SC",sans-serif;}}
.shell{{width:{W}px;height:{H}px;display:grid;
  grid-template-rows:{ST_H}px 1fr {TAB_H}px {HOME_H}px;}}
.shell > *:nth-child(2){{min-height:0;}}
.shell-notab{{grid-template-rows:{ST_H}px 1fr {HOME_H}px;}}
.shell-notab-tool{{grid-template-rows:{ST_H}px 1fr {MEMO_TOOL_H}px {HOME_H}px;}}
.st{{padding:14px 28px 0;display:flex;justify-content:space-between;font:600 15px -apple-system,sans-serif;}}
.st-w{{color:#fff;}}
.home{{display:flex;align-items:center;justify-content:center;padding-bottom:8px;}}
.home i{{display:block;width:134px;height:5px;background:#000;border-radius:3px;opacity:.18;}}
.home-w i{{background:#fff;opacity:.35;}}
.tab{{background:#f9f9f9;border-top:1px solid #e5e5ea;display:flex;justify-content:space-around;
  padding-top:10px;font-size:10px;color:#8e8e93;}}
.tab b{{display:block;font-size:22px;margin-bottom:3px;font-weight:400;}}
.tab .on{{color:#007aff;}}
.memo-tool{{background:#f2f2f0;border-top:1px solid #d1d1d6;display:flex;align-items:center;
  justify-content:space-around;font-size:22px;color:#007aff;}}
"""

ST = '<div class="st"><span>9:41</span><span class="r"><span>5G</span><span>▮▮▮</span><span>🔋</span></span></div>'
STW = '<div class="st st-w"><span>9:41</span><span class="r"><span>5G</span><span>▮▮▮</span><span>🔋</span></span></div>'
HOME = '<div class="home"><i></i></div>'
HOMEW = '<div class="home home-w"><i></i></div>'
TABM = '<div class="tab"><span class="on"><b>✉️</b>邮件</span><span><b>📅</b>日历</span><span><b>👤</b>联系人</span><span><b>📁</b>文件</span></div>'
TABA = '<div class="tab"><span class="on"><b>📊</b>概览</span><span><b>📄</b>页面</span><span><b>✉️</b>邮件</span><span><b>⚙️</b>设置</span></div>'
MTOOL = '<div class="memo-tool"><span>☑</span><span>📷</span><span>✏️</span><span>≡</span></div>'


def mail_row(who, subj, prev, time, letter, color="#aaa", unread=False):
    bg = "background:#f9f9fb;" if unread else ""
    op = "" if unread else "opacity:.48;"
    return f"""<div style="padding:14px 16px;border-bottom:1px solid #e5e5ea;display:flex;gap:12px;{bg}{op}">
  <div style="width:42px;height:42px;border-radius:21px;background:{color};color:#fff;font-weight:700;
    display:flex;align-items:center;justify-content:center;flex-shrink:0;font-size:16px;">{letter}</div>
  <div style="flex:1;min-width:0;">
    <div style="display:flex;justify-content:space-between;gap:8px;">
      <b style="font-size:16px;">{who}</b><span style="color:#8e8e93;font-size:14px;flex-shrink:0;">{time}</span></div>
    <div style="font-weight:600;font-size:15px;margin:2px 0;">{subj}</div>
    <div style="color:#8e8e93;font-size:14px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{prev}</div>
  </div></div>"""


def note_row(title, meta, preview=""):
    return f"""<div class="nr">
  <div class="nt">{title}</div>
  <div class="nm"><span>{preview}</span><span>{meta}</span></div></div>"""


def gen_memo01() -> pathlib.Path:
    items = [
        ("Project-001 背景", "6月16日", "海外小品牌 · 预算≈0"),
        ("Day5 复盘草稿", "6月15日", "曝光有了留资少…"),
        ("邮件序列文案 v2", "6月14日", "Welcome + 6封养熟…"),
        ("落地页 headline", "6月13日", "Your phoenix is rising…"),
        ("Pinterest 选题", "6月12日", "wealth corner / pixiu…"),
        ("免费工具清单", "6月11日", "Formspree / Brevo / CF…"),
        ("Pin 尺寸备忘", "6月10日", "1000×1500 · 2:3"),
        ("Brevo 发信限额", "6月9日", "免费 300封/天"),
        ("域名 DNS 记录", "6月8日", "SPF / DKIM 已配"),
        ("竞品 landing 截图", "6月7日", "3 家参考链接"),
        ("邮件 subject 备选", "6月6日", "A/B 各写 3 条"),
        ("表单字段精简", "6月5日", "只要名+邮箱"),
        ("UTM 命名规范", "6月4日", "pinterest / pin-id"),
        ("周报模板", "6月3日", "曝光·点击·留资"),
        ("素材版权说明", "6月2日", "图库可商用清单"),
        ("下周待办", "6月1日", "改 Pin 文案 · 测 headline"),
        ("灵感收藏", "5月31日", "植物+金饰构图"),
        ("用户画像草稿", "5月30日", "25-40 · 海外华人"),
        ("落地页配色", "5月29日", "黑金 · 别用紫渐变"),
        ("自动化节点图", "5月28日", "提交→欢迎→序列"),
    ]
    rows = "".join(note_row(t, m, p) for t, m, p in items)
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{BASE}
.main{{background:#fff;overflow:hidden;display:flex;flex-direction:column;min-height:0;}}
.hdr{{background:#f2f2f0;padding:14px 20px 12px;font-size:34px;font-weight:700;border-bottom:1px solid #e5e5ea;flex-shrink:0;}}
.scroll{{flex:1;overflow:hidden;}}
.nr{{padding:13px 20px;border-bottom:1px solid #e5e5ea;}}
.nt{{font-size:17px;font-weight:600;margin-bottom:3px;}}
.nm{{font-size:14px;color:#8e8e93;display:flex;justify-content:space-between;gap:12px;}}
.nm span:first-child{{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}}
</style></head><body><div class="shell shell-notab-tool">
{ST}<div class="main"><div class="hdr">备忘录</div><div class="scroll">{rows}</div></div>
{MTOOL}{HOME}</div></body></html>"""
    return shot(html, "MEMO01_background.png")


def gen_memo02() -> pathlib.Path:
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{BASE}
.main{{background:#fff;display:flex;flex-direction:column;overflow:hidden;min-height:0;}}
.nav{{background:#ffcc00;padding:11px 18px;font-size:17px;border-bottom:1px solid #e6b800;flex-shrink:0;}}
.nav .b{{color:#007aff;font-size:26px;margin-right:6px;}}
.body{{padding:16px 22px 12px;flex:1;overflow:hidden;display:flex;flex-direction:column;justify-content:space-between;}}
.body-top{{display:flex;flex-direction:column;gap:16px;}}
.meta{{color:#8e8e93;font-size:13px;}}
.lead{{font-size:28px;font-weight:700;line-height:1.4;}}
.sec h3{{font-size:16px;color:#8e8e93;margin-bottom:8px;font-weight:600;}}
.sec p,.sec li{{font-size:22px;line-height:1.6;}}
.sec ul{{padding-left:22px;}}
.sec li{{margin-bottom:10px;}}
.sec p{{margin-top:4px;}}
.q{{margin-top:8px;padding:18px;background:#f2f2f7;border-radius:12px;font-size:23px;font-weight:600;line-height:1.45;}}
</style></head><body><div class="shell shell-notab-tool">
{ST}<div class="main">
  <div class="nav"><span class="b">‹</span>Day 5 复盘</div>
  <div class="body">
    <div class="body-top">
    <div class="meta">6月16日 上午9:41</div>
    <div class="lead">系统能跑。内容太机器。</div>
    <div class="sec"><h3>数据</h3>
      <ul><li>曝光 847 · 留资 4</li><li>Pinterest 占 72% 流量</li><li>欢迎邮件打开率还行</li></ul></div>
    <div class="sec"><h3>问题</h3>
      <ul><li>Pin 像 AI 一键出的</li><li>落地页 headline 太长</li><li>没人愿意停下滑动</li></ul></div>
    <div class="sec"><h3>改法</h3>
      <p>AI 出背景图，文字自己排。<br>别一把梭。</p></div>
    <div class="sec"><h3>明天</h3>
      <ul><li>重做 3 张 Pin</li><li>缩短 headline</li><li>测一版手动排版</li></ul></div>
    <div class="sec"><h3>笔记</h3>
      <p>花了一天把表单、邮件、落地页串起来。<br>
      第5天看数据：曝光起来了，没人留邮箱。<br>
      不是工具问题，是内容像流水线出来的。</p></div>
    </div>
    <div class="q">你们会先搞系统，还是先搞内容？</div>
  </div>
</div>{MTOOL}{HOME}</div></body></html>"""
    return shot(html, "MEMO02_cta.png")


def gen_br004_annotated(cover_title: str, tag: str) -> pathlib.Path:
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{BASE}
.main{{background:#f2f2f7;overflow:hidden;display:flex;flex-direction:column;min-height:0;}}
.hdr{{padding:8px 18px 10px;background:#fff;border-bottom:1px solid #e5e5ea;flex-shrink:0;}}
.hdr h1{{font-size:26px;font-weight:700;}} .hdr p{{color:#8e8e93;font-size:13px;margin-top:2px;}}
.sc{{flex:1;overflow:hidden;padding:10px 0;display:flex;flex-direction:column;gap:10px;}}
.hook{{margin:0 14px;background:linear-gradient(135deg,#1c1c1e,#444);color:#fff;border-radius:12px;padding:20px 16px;flex-shrink:0;}}
.hook .t{{font-size:13px;opacity:.75;margin-bottom:8px;}}
.hook h2{{font-size:28px;font-weight:800;line-height:1.3;}}
.card{{margin:0 14px;background:#fff;border-radius:12px;padding:14px;position:relative;flex-shrink:0;}}
.card h3{{font-size:11px;color:#8e8e93;margin-bottom:6px;letter-spacing:.05em;}}
.n{{font-size:34px;font-weight:700;}} .up{{color:#34c759;font-size:14px;font-weight:600;}}
.dn{{color:#ff3b30;font-size:14px;font-weight:600;}}
.chart{{height:220px;display:flex;align-items:flex-end;gap:5px;margin-top:8px;position:relative;}}
.bar{{flex:1;background:#007aff;border-radius:3px 3px 0 0;}}
.r2{{display:flex;gap:8px;margin:0 14px;flex-shrink:0;}} .r2 .card{{flex:1;margin:0;}}
.mk{{position:absolute;inset:-4px;border:3px solid #ff3b30;border-radius:50%;}}
.lb{{position:absolute;background:#ff3b30;color:#fff;font-size:13px;font-weight:700;padding:3px 8px;border-radius:5px;}}
.row{{display:flex;justify-content:space-between;padding:9px 0;border-bottom:1px solid #f2f2f7;font-size:14px;}}
.row:last-child{{border:none;}}
.fill{{margin:0 14px;background:#fff;border-radius:12px;padding:16px 14px;flex-shrink:0;}}
.fill h3{{font-size:11px;color:#8e8e93;margin-bottom:8px;}}
.fill .row{{padding:13px 0;}}
</style></head><body><div class="shell">
{ST}<div class="main">
  <div class="hdr"><h1>Analytics</h1><p>Last 7 days · Project-001</p></div>
  <div class="sc">
    <div class="hook"><div class="t">{tag}</div><h2>{cover_title}</h2></div>
    <div class="card"><h3>页面曝光</h3><div><span class="n">847</span> <span class="up">↑ 312%</span></div>
      <div class="chart"><div class="mk"></div><div class="lb" style="top:0;right:0">曝光↑</div>
        <div class="bar" style="height:28%"></div><div class="bar" style="height:38%"></div>
        <div class="bar" style="height:48%"></div><div class="bar" style="height:62%"></div>
        <div class="bar" style="height:78%"></div><div class="bar" style="height:92%"></div>
        <div class="bar" style="height:100%"></div></div></div>
    <div class="r2">
      <div class="card"><div class="mk"></div><div class="lb" style="bottom:-24px;left:50%;transform:translateX(-50%)">留资↓</div>
        <h3>邮箱留资</h3><div><span class="n">4</span> <span class="dn">↓偏少</span></div></div>
      <div class="card"><h3>转化率</h3><div><span class="n">0.5%</span> <span class="dn">↓</span></div></div>
    </div>
    <div class="card"><h3>流量来源</h3>
      <div class="row"><span>Pinterest</span><span>612</span></div>
      <div class="row"><span>Direct</span><span>154</span></div>
      <div class="row"><span>Other</span><span>81</span></div></div>
    <div class="card"><h3>邮件漏斗</h3>
      <div class="row"><span>欢迎信发送</span><span>4</span></div>
      <div class="row"><span>打开</span><span>38%</span></div>
      <div class="row"><span>点击下载</span><span>12%</span></div>
      <div class="row"><span>序列第2封</span><span>50% 打开</span></div></div>
    <div class="fill"><h3>转化漏斗 · 设备 · 地域</h3>
      <div class="row"><span>曝光→点击</span><span>847→356</span></div>
      <div class="row"><span>点击→留资</span><span>356→<b style="color:#ff3b30">4</b></span></div>
      <div class="row"><span>Mobile / Desktop</span><span>78% / 22%</span></div>
      <div class="row"><span>US / CA / AU</span><span>61% / 18% / 9%</span></div>
      <div class="row"><span>平均停留</span><span>42s</span></div>
      <div class="row"><span>表单放弃率</span><span style="color:#ff3b30">71%</span></div>
      <div class="row"><span>Pin 收藏</span><span>23</span></div>
      <div class="row"><span>欢迎信打开</span><span>38%</span></div>
      <div class="row"><span>序列完成率</span><span>45%</span></div>
      <div class="row"><span>本周目标</span><span style="color:#ff3b30">4/20 留资</span></div></div>
    <div class="card"><h3>落地页热区</h3>
      <div class="row"><span>Headline 停留</span><span>8.2s</span></div>
      <div class="row"><span>表单区域到达</span><span>34%</span></div>
      <div class="row"><span>CTA 点击率</span><span style="color:#ff3b30">1.1%</span></div>
      <div class="row"><span>滚动深度</span><span>62%</span></div></div>
  </div>
</div>{TABA}{HOME}</div></body></html>"""
    return shot(html, "BR004_analytics_annotated.png")


def gen_br004_day5_tagged() -> pathlib.Path:
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{BASE}
.main{{background:#f2f2f7;overflow:hidden;display:flex;flex-direction:column;min-height:0;}}
.hdr{{padding:8px 18px 10px;background:#fff;border-bottom:1px solid #e5e5ea;flex-shrink:0;}}
.hdr h1{{font-size:26px;font-weight:700;}} .hdr p{{color:#8e8e93;font-size:13px;}}
.sc{{flex:1;overflow:hidden;padding:10px 0;display:flex;flex-direction:column;gap:10px;}}
.badge{{margin:0 14px;display:inline-block;background:#ff9500;color:#fff;padding:8px 14px;
  border-radius:16px;font-size:18px;font-weight:700;transform:rotate(-2deg);}}
.note{{margin:0 14px;background:#fff;border-radius:12px;padding:14px;font-size:18px;line-height:1.55;}}
.note em{{color:#ff3b30;font-style:normal;font-weight:600;}}
.card{{margin:0 14px;background:#fff;border-radius:12px;padding:14px;flex-shrink:0;}}
.card h3{{font-size:11px;color:#8e8e93;margin-bottom:6px;}}
.n{{font-size:34px;font-weight:700;}} .up{{color:#34c759;}} .dn{{color:#ff3b30;}}
.chart{{height:160px;display:flex;align-items:flex-end;gap:5px;margin-top:6px;}}
.bar{{flex:1;background:#007aff;border-radius:3px 3px 0 0;}}
.r2{{display:flex;gap:8px;margin:0 14px;flex-shrink:0;}} .r2 .card{{flex:1;margin:0;}}
.row{{display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid #f2f2f7;font-size:14px;}}
.row:last-child{{border:none;}}
.fill{{margin:0 14px;background:#fff;border-radius:12px;padding:16px 14px;flex-shrink:0;}}
.fill h3{{font-size:11px;color:#8e8e93;margin-bottom:8px;}}
.fill .row{{padding:13px 0;}}
</style></head><body><div class="shell">
{ST}<div class="main">
  <div class="hdr"><h1>Analytics</h1><p>Last 7 days · Project-001</p></div>
  <div class="sc">
    <div style="padding:0 14px"><span class="badge">Day 5</span></div>
    <div class="note">曝光有了，<em>留资寥寥无几</em><br>复盘：问题不在系统，在内容。</div>
    <div class="card"><h3>页面曝光</h3><div><span class="n">847</span> <span class="up">↑312%</span></div>
      <div class="chart"><div class="bar" style="height:30%"></div><div class="bar" style="height:45%"></div>
      <div class="bar" style="height:60%"></div><div class="bar" style="height:75%"></div>
      <div class="bar" style="height:90%"></div><div class="bar" style="height:100%"></div></div></div>
    <div class="r2">
      <div class="card"><h3>邮箱留资</h3><div><span class="n">4</span> <span class="dn">↓偏少</span></div></div>
      <div class="card"><h3>转化率</h3><div><span class="n">0.5%</span> <span class="dn">↓</span></div></div>
    </div>
    <div class="card"><h3>最近7天</h3>
      <div class="row"><span>6/12</span><span>118访问·1留资</span></div>
      <div class="row"><span>6/13</span><span>134访问·0留资</span></div>
      <div class="row"><span>6/14</span><span>156访问·1留资</span></div>
      <div class="row"><span>6/15</span><span>198访问·0留资</span></div>
      <div class="row"><span>6/16</span><span>247访问·1留资</span></div></div>
    <div class="r2">
      <div class="card"><h3>资料下载</h3><div><span class="n">12</span></div></div>
      <div class="card"><h3>跳出率</h3><div><span class="n">68%</span> <span class="dn">偏高</span></div></div>
    </div>
    <div class="card"><h3>设备分布</h3>
      <div class="row"><span>iPhone</span><span>62%</span></div>
      <div class="row"><span>Android</span><span>24%</span></div>
      <div class="row"><span>Desktop</span><span>14%</span></div></div>
    <div class="fill"><h3>页面洞察</h3>
      <div class="row"><span>Pin 点击率</span><span>2.1%</span></div>
      <div class="row"><span>落地页加载</span><span>1.8s</span></div>
      <div class="row"><span>邮件打开率</span><span>38%</span></div>
      <div class="row"><span>欢迎信点击</span><span>12%</span></div>
      <div class="row"><span>最热门 Pin</span><span>wealth corner</span></div>
      <div class="row"><span>次热门</span><span>pixiu desk</span></div>
      <div class="row"><span>本周目标</span><span style="color:#ff3b30">4/20 留资</span></div>
      <div class="row"><span>下一步</span><span>改 Pin 文案</span></div>
  </div>
</div>{TABA}{HOME}</div></body></html>"""
    return shot(html, "BR004_day5_tagged.png")


def gen_br001_safari() -> pathlib.Path:
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{BASE}
.main{{background:#1c1c1e;display:flex;flex-direction:column;overflow:hidden;}}
.url{{flex-shrink:0;background:#2c2c2e;padding:9px 12px;display:flex;gap:8px;align-items:center;}}
.u{{flex:1;background:#3a3a3c;border-radius:9px;padding:9px;color:#ebebf5;font-size:14px;text-align:center;}}
.pg{{flex:1;position:relative;overflow:hidden;}}
.pg img{{width:100%;height:100%;object-fit:cover;object-position:center 18%;}}
.sf{{flex-shrink:0;height:44px;background:#2c2c2e;display:flex;justify-content:space-between;
  align-items:center;padding:0 22px;color:#0a84ff;font-size:20px;}}
.mk{{position:absolute;bottom:100px;right:24px;width:76px;height:76px;border:3px solid #ff3b30;border-radius:50%;}}
.ml{{position:absolute;bottom:44px;right:14px;background:#ff3b30;color:#fff;padding:5px 10px;
  border-radius:7px;font-size:14px;font-weight:700;}}
</style></head><body><div class="shell shell-notab" style="background:#1c1c1e">
{STW}<div class="main">
  <div class="url"><span style="color:#0a84ff">‹›</span><div class="u">🔒 brand-site.com/guide</div></div>
  <div class="pg"><img src="{src(SHOTS / "landing.png")}"><div class="mk"></div><div class="ml">3秒讲清</div></div>
  <div class="sf"><span>‹</span><span>›</span><span>↗</span><span>⊞</span></div>
</div>{HOMEW}</div></body></html>"""
    return shot(html, "BR001_safari_landing.png")


def gen_stack_submit_mail() -> pathlib.Path:
    rows = mail_row("Tonfire", "Your free guide is inside ✦",
                    "Welcome — tap below to open your Wealth Phoenix Guide…", "刚刚", "T", "#c9a55c", True)
    fillers = [
        ("Mailchimp", "Campaign report ready", "Weekly summary for Project-001…", "昨天", "M"),
        ("GitHub", "Weekly digest", "3 notifications in your repos…", "昨天", "G", "#24292e"),
        ("Notion", "Content calendar", "Your queue was updated…", "周二", "N", "#888"),
        ("Stripe", "Payout scheduled", "Payout arriving Thursday…", "周一", "S", "#635bff"),
        ("Google", "Security alert", "New sign-in from Chrome…", "周一", "G", "#4285f4"),
        ("noreply", "Verify your email", "Click to confirm your address…", "周日", "@", "#bbb"),
        ("Pinterest", "Pin performance", "Your pin got 89 saves…", "周日", "P", "#e60023"),
        ("Cloudflare", "Traffic spike", "Unusual traffic on /guide…", "周六", "C", "#f38020"),
        ("Brevo", "Daily limit", "298 of 300 emails sent…", "周六", "B", "#0b996e"),
        ("Formspree", "New submission", "Someone filled your form…", "周五", "F", "#ff5a5f"),
        ("Canva", "Design shared", "Pin draft v3 is ready…", "周五", "C", "#00c4cc"),
        ("LinkedIn", "Profile views", "12 people viewed you…", "周四", "L", "#0a66c2"),
        ("Apple", "Receipt", "Your App Store purchase…", "周四", "A", "#555"),
        ("Substack", "New post", "Newsletter draft reminder…", "周三", "S", "#ff6719"),
        ("Zoom", "Meeting recap", "Recording is available…", "周三", "Z", "#2d8cff"),
        ("Amazon", "Delivery update", "Package out for delivery…", "周二", "@", "#ff9900"),
    ]
    for args in fillers:
        rows += mail_row(*args)
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{BASE}
.main{{background:#f2f2f7;overflow:hidden;display:flex;flex-direction:column;min-height:0;}}
.toast{{flex-shrink:0;margin:8px 14px 0;background:#1c1c1e;color:#fff;border-radius:10px;padding:11px 14px;font-size:15px;}}
.toast b{{color:#34c759;margin-right:8px;}}
.nav{{padding:12px 16px 8px;flex-shrink:0;}} .nav h1{{font-size:32px;font-weight:700;}}
.list{{flex:1;overflow:hidden;background:#fff;border-radius:10px 10px 0 0;}}
</style></head><body><div class="shell">
{ST}<div class="main">
  <div class="toast"><b>✓</b>提交成功 · 12:04<span style="float:right;opacity:.55;font-size:13px">刚刚</span></div>
  <div class="nav"><h1>收件箱</h1></div>
  <div class="list">{rows}</div>
</div>{TABM}{HOME}</div></body></html>"""
    return shot(html, "STACK_submit_welcome.png")


def _slop_png() -> pathlib.Path:
    html = """<!DOCTYPE html><html><head><meta charset="utf-8"><style>
*{margin:0} html,body{width:1206px;height:700px}
.p{width:1206px;height:700px;background:linear-gradient(160deg,#7b2ff7,#f107a3 50%,#ffd700);
 display:flex;flex-direction:column;align-items:center;justify-content:center;
 font-family:Impact,sans-serif;color:#fff;text-align:center}
h1{font-size:48px;text-shadow:2px 2px 0 #000;line-height:1.1}
p{font-size:24px;color:#ff0;margin-top:12px}
</style></head><body><div class="p"><h1>WEALTH<br>MANIFEST<br>NOW!!!</h1><p>10 SECRET HABITS ✨</p></div></body></html>"""
    out = OUT / "_ai_slop_raw.png"
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as f:
        f.write(html)
        p = f.name
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", f"--screenshot={out}",
                    "--window-size=1206,700", "--force-device-scale-factor=1", f"file://{p}"],
                   capture_output=True, check=True)
    return out


def gen_br006_compare() -> pathlib.Path:
    slop, good = _slop_png(), PINS / "pin01_wealth_corner.png"
    mid = body_h()
    half = (mid - 44 - 36) // 2  # hd ~36 + foot 44
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{BASE}
.shell-notab-tool{{grid-template-rows:{ST_H}px 1fr 44px {HOME_H}px;}}
.main{{background:#000;display:flex;flex-direction:column;overflow:hidden;}}
.hd{{flex-shrink:0;height:36px;padding:8px 14px;color:#fff;font-size:14px;display:flex;justify-content:space-between;align-items:center;}}
.pane{{height:{half}px;position:relative;overflow:hidden;}}
.pane img{{width:100%;height:100%;object-fit:cover;}}
.tag{{position:absolute;top:8px;left:8px;padding:5px 10px;border-radius:6px;font-size:13px;font-weight:700;color:#fff;}}
.bad{{background:#ff3b30}} .good{{background:#34c759}}
.cap{{position:absolute;bottom:10px;left:0;right:0;text-align:center;color:#fff;font-size:16px;font-weight:600;
 text-shadow:0 2px 6px #000}}
.foot{{flex-shrink:0;height:44px;background:#1c1c1e;color:#fff;display:flex;align-items:center;justify-content:center;font-size:16px;font-weight:600;}}
</style></head><body><div class="shell shell-notab" style="background:#000">
{STW}<div class="main">
  <div class="hd"><span>✕</span><span>对比 · 内容改法</span><span>↗</span></div>
  <div class="pane"><img src="{src(slop)}"><div class="tag bad">AI一键</div><div class="cap">谁都刷过·没人停</div></div>
  <div class="pane"><img src="{src(good)}"><div class="tag good">精排后</div><div class="cap">AI出背景·文字自己排</div></div>
  <div class="foot">改法：别一把梭</div>
</div>{HOMEW}</div></body></html>"""
    return shot(html, "BR006_ai_vs_manual.png")


def gen_br003_mail() -> pathlib.Path:
    rows = mail_row("Tonfire", "Your free guide is inside ✦",
                    "Welcome — tap below to open your Wealth Phoenix Guide…", "刚刚", "T", "#c9a55c", True)
    for args in [
        ("Mailchimp", "Campaign report", "Weekly summary…", "昨天", "M"),
        ("GitHub", "Weekly digest", "3 notifications…", "昨天", "G", "#24292e"),
        ("Notion", "Reminder", "Content queue…", "周二", "N", "#888"),
        ("Stripe", "Payout", "Scheduled…", "周一", "S", "#635bff"),
        ("Google", "Security", "New sign-in…", "周一", "G", "#4285f4"),
        ("noreply", "Verify", "Confirm email…", "周日", "@", "#bbb"),
    ]:
        rows += mail_row(*args)
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{BASE}
.main{{background:#f2f2f7;overflow:hidden;display:flex;flex-direction:column;}}
.nav{{padding:12px 16px;}} .nav h1{{font-size:32px;font-weight:700;}}
.list{{flex:1;overflow:hidden;background:#fff;}}
</style></head><body><div class="shell">
{ST}<div class="main"><div class="nav"><h1>收件箱</h1></div><div class="list">{rows}</div></div>
{TABM}{HOME}</div></body></html>"""
    return shot(html, "BR003_welcome_mail.png")


def main() -> None:
    print(f"生成仿真素材 {W}×{H} →", OUT)
    gen_memo01()
    gen_memo02()
    gen_br003_mail()
    gen_br004_annotated("花一天搭完邮件获客，第5天我傻眼了", "第5天 · 打码数据")
    gen_br001_safari()
    gen_br006_compare()
    gen_stack_submit_mail()
    gen_br004_day5_tagged()
    print("done.")


if __name__ == "__main__":
    main()
