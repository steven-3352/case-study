#!/usr/bin/env python3
"""④ 通用渲染 · content.yaml → 三平台 video.mp4 + cover.png.

为了「像真实剪辑、去 AI 味」：每段 Ken Burns 运镜（缓推/移）、段间 xfade 转场、
字幕做成半透明叠层（不是写死在帧上）、封面用真实截图叠手写感大字。

素材回落：source=shot 用真实截图；缺失/evidence/web 回落到干净的备忘录风卡片
（非黑金 PPT，见 DECISIONS Q9），并打印出来不静默。

用法:
  python3 pipeline/render.py --id P002 [--platform douyin xhs channels]
"""
from __future__ import annotations

import argparse
import html
import pathlib
import random
import re
import subprocess
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import pipeline.env_loader  # noqa: F401 — 加载 .env
from pipeline.render_core import CHROME, VH, VW, dur
from pipeline.tts.gen_speech import synthesize_text

FONT_STACK = '"Hiragino Sans GB","STHeiti","PingFang SC",sans-serif'
PAD = 0.15          # 每段尾部留白（节奏更紧）
XFADE = 0.22        # 转场时长（更利落）
XF_KINDS = ["fade", "slideleft", "slideup", "fade", "smoothleft"]

# 背景音乐：bgm/ 下的免版税循环曲，随机截取一段（--bgm 可覆盖）
BGM_DEFAULT = ROOT / "bgm" / "bgm_main.mp3"
BGM_PATH = BGM_DEFAULT          # main() 按 --bgm 覆盖
# 情绪弧线兜底（content 段未标 emotion 时按位置取）：钩子兴奋→踩坑无奈→方案笃定→收尾真诚
EMOTION_ARC = ["happy", "sad", "happy", "neutral"]

# 周产线 W26D* 等 → .staging/，避免与 publish/2026-W26 重复；P00x 大项目仍落 publish/P00x/
def publish_out_root(pid: str) -> pathlib.Path:
    if re.match(r"^W\d", pid):
        return ROOT / "publish" / ".staging" / pid
    return ROOT / "publish" / pid


# ── Chrome 截图（支持透明） ──
def _chrome(html_str: str, out: pathlib.Path, transparent: bool = False) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    import tempfile
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as f:
        f.write(html_str)
        path = f.name
    cmd = [CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
           f"--screenshot={out}", f"--window-size={VW},{VH}", "--force-device-scale-factor=1"]
    if transparent:
        cmd.append("--default-background-color=00000000")
    cmd.append(f"file://{path}")
    subprocess.run(cmd, capture_output=True, timeout=120, check=True)


# ── 字幕叠层（透明 PNG，底部渐变 + 大字） ──
def subtitle_png(text: str, out: pathlib.Path) -> None:
    t = html.escape(text)
    css = f"""*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:{VW}px;height:{VH}px;background:transparent}}
.sub{{position:absolute;left:0;right:0;bottom:0;padding:30px 40px 70px;text-align:center;
  background:linear-gradient(180deg,rgba(11,13,16,0) 0%,rgba(11,13,16,.82) 50%,rgba(11,13,16,.94) 100%);
  font-family:{FONT_STACK};font-size:46px;font-weight:800;line-height:1.32;color:#fff;
  text-shadow:0 2px 12px rgba(0,0,0,.95),0 0 2px rgba(0,0,0,.9)}}"""
    _chrome(f"<!DOCTYPE html><html><head><meta charset=utf-8><style>{css}</style></head>"
            f"<body><div class=sub>{t}</div></body></html>", out, transparent=True)


# ── 回落卡片（干净备忘录风，非黑金 PPT） ──
def fallback_card(text: str, out: pathlib.Path, tag: str = "项目笔记") -> None:
    t = html.escape(text)
    css = f"""*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:{VW}px;height:{VH}px;background:#f5f2ea;font-family:{FONT_STACK}}}
.wrap{{width:100%;height:100%;padding:120px 90px;display:flex;flex-direction:column}}
.bar{{display:flex;gap:14px;align-items:center;margin-bottom:40px}}
.dot{{width:16px;height:16px;border-radius:50%}}
.r{{background:#ff5f57}}.y{{background:#febc2e}}.g{{background:#28c840}}
.tag{{font-size:30px;color:#9b8c70;letter-spacing:.06em;margin-bottom:30px}}
.txt{{font-size:62px;font-weight:800;line-height:1.5;color:#23201a;flex:1}}
.foot{{font-size:28px;color:#b3a88f;margin-top:auto}}"""
    _chrome(f"<!DOCTYPE html><html><head><meta charset=utf-8><style>{css}</style></head>"
            f"<body><div class=wrap><div class=bar><span class='dot r'></span>"
            f"<span class='dot y'></span><span class='dot g'></span></div>"
            f"<div class=tag>{html.escape(tag)}</div><div class=txt>{t}</div>"
            f"<div class=foot>真实项目 · 随手记</div></div></body></html>", out)


# ── evidence 体裁卡片：把 author 给的 detail 画成像真实截图的素材 ──
def _win_chrome(title: str, body_html: str, body_css: str, out: pathlib.Path) -> None:
    """macOS 窗口外壳（红黄绿点 + 标题栏）包裹内容。"""
    css = f"""*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:{VW}px;height:{VH}px;background:#0d1117;font-family:{FONT_STACK}}}
.pad{{width:100%;height:100%;padding:90px 60px;display:flex;align-items:center}}
.win{{width:100%;border-radius:22px;overflow:hidden;box-shadow:0 30px 80px rgba(0,0,0,.5);background:#fff}}
.tb{{height:74px;display:flex;align-items:center;gap:16px;padding:0 28px;background:#e9e6df}}
.d{{width:18px;height:18px;border-radius:50%}}.r{{background:#ff5f57}}.y{{background:#febc2e}}.g{{background:#28c840}}
.tt{{margin-left:14px;font-size:30px;color:#6b6256}}
{body_css}"""
    _chrome(f"<!DOCTYPE html><html><head><meta charset=utf-8><style>{css}</style></head>"
            f"<body><div class=pad><div class=win><div class=tb>"
            f"<span class='d r'></span><span class='d y'></span><span class='d g'></span>"
            f"<span class=tt>{html.escape(title)}</span></div>{body_html}</div></div></body></html>", out)


def evidence_card(kind: str, detail: str, sub: str, out: pathlib.Path) -> None:
    lines = [ln for ln in (detail or "").splitlines() if ln.strip()] or [sub]
    esc = [html.escape(ln) for ln in lines]

    if kind == "terminal":
        rows = "".join(
            f"<div class='ln {'cmd' if (l.startswith('$') or l.startswith('>')) else 'out'}'>{l}</div>"
            for l in esc)
        body_css = (".body{background:#0c0f14;padding:44px 48px;min-height:900px}"
                    ".ln{font-family:'SF Mono','Menlo',monospace;font-size:38px;line-height:1.7;color:#c8d3e0;white-space:pre-wrap;word-break:break-word}"
                    ".cmd{color:#7ee787}")
        _win_chrome("zsh — 终端", f"<div class=body>{rows}</div>", body_css, out)

    elif kind == "code":
        rows = "".join(f"<div class=ln><span class=n>{i+1}</span>{l}</div>" for i, l in enumerate(esc))
        body_css = (".body{background:#0d1117;padding:40px 36px;min-height:900px}"
                    ".ln{font-family:'SF Mono','Menlo',monospace;font-size:36px;line-height:1.7;color:#e6edf3;white-space:pre-wrap;word-break:break-word}"
                    ".n{display:inline-block;width:70px;color:#4d5566;user-select:none}")
        _win_chrome("源码", f"<div class=body>{rows}</div>", body_css, out)

    elif kind == "chat":
        bubbles = []
        for l in lines:
            s = l.strip()
            if re.match(r"^\d{1,2}:\d{2}$", s) or s.startswith("（") and "小时" in s:
                bubbles.append(f"<div class=ts>{html.escape(s)}</div>")
                continue
            if s.startswith("—") or s.startswith("-"):
                bubbles.append(f"<div class=ts>{html.escape(s.lstrip('—- '))}</div>")
                continue
            me = bool(re.match(r"^(我|店主|前台|老板)[：:]", s))
            txt = re.sub(r"^(我|你|客人|店主|前台|老板|技师)[：:]\s*", "", s)
            txt = html.escape(txt)
            side = "me" if me else "you"
            bubbles.append(f"<div class='row {side}'><div class=b>{txt}</div></div>")
        body_css = (".body{background:#ededed;padding:60px 50px;min-height:1000px;display:flex;flex-direction:column;gap:24px}"
                    ".row{display:flex}.row.me{justify-content:flex-end}"
                    ".b{max-width:78%;font-size:40px;line-height:1.45;padding:28px 32px;border-radius:24px;color:#16331c;background:#fff;box-shadow:0 2px 8px rgba(0,0,0,.06)}"
                    ".me .b{background:#95ec69}"
                    ".ts{align-self:center;font-size:28px;color:#9a9a9a;padding:8px 0}")
        title = "微信"
        if any("窗口" in l for l in lines):
            title = "5个窗口 · 预约消息"
        _win_chrome(title, f"<div class=body>{''.join(bubbles)}</div>", body_css, out)

    elif kind == "metric":
        items = "".join(
            f"<div class=mrow><span class=k>{html.escape(re.split('[=：]', l, maxsplit=1)[0].strip())}</span>"
            f"<span class=v>{html.escape(re.split('[=：]', l, maxsplit=1)[-1].strip())}</span></div>" for l in lines)
        body_css = (".body{background:#fbfaf7;padding:80px 70px;min-height:900px;display:flex;flex-direction:column;gap:40px}"
                    ".mrow{display:flex;justify-content:space-between;align-items:baseline;border-bottom:2px solid #ece7dd;padding-bottom:30px}"
                    ".k{font-size:42px;color:#6b6256}.v{font-size:64px;font-weight:800;color:#1a7f4b}")
        _win_chrome("数据", f"<div class=body>{items}</div>", body_css, out)

    elif kind == "hook":
        def _hl(ln: str) -> str:
            m = re.match(r"^(.+?)【(.+?)】(.*)$", ln)
            if m:
                return (f"{html.escape(m.group(1))}<em>{html.escape(m.group(2))}</em>"
                        f"{html.escape(m.group(3))}")
            return html.escape(ln)

        hook_lines = [_hl(ln) for ln in lines[:3]]
        hook_tag = (sub or "真实小店 · 场景").strip()
        body_css = (".body{background:#faf8f5;padding:0;min-height:1000px;display:flex;flex-direction:column;"
                    "justify-content:center;align-items:center;text-align:center}"
                    ".hl{font-size:96px;font-weight:900;line-height:1.18;color:#1a1a1a;letter-spacing:.02em}"
                    ".hl em{font-style:normal;color:#e03e2f}"
                    ".tag{margin-top:48px;font-size:34px;color:#8a8278;letter-spacing:.08em}")
        inner = "".join(f"<div class=hl>{ln}</div>" for ln in hook_lines)
        _win_chrome("钩子", f"<div class=body>{inner}<div class=tag>{html.escape(hook_tag)}</div></div>", body_css, out)

    elif kind == "flow":
        steps = [ln.strip() for ln in lines if ln.strip() and not ln.startswith("—")]
        step_html = "".join(
            f'<span class=step>{html.escape(s)}</span><span class=arr>→</span>' for s in steps[:4]
        ).rstrip('<span class=arr>→</span>')
        body_css = (
            ".body{background:#f7f5f0;padding:70px 40px;min-height:900px;display:flex;flex-direction:column;"
            "justify-content:center;gap:36px}"
            ".flowline{font-size:34px;line-height:1.5;text-align:center;color:#3d3830}"
            ".step{display:inline-block;background:#fff;border:3px solid #2e7d52;border-radius:14px;"
            "padding:20px 24px;margin:6px;font-weight:700;color:#1b5e20;vertical-align:middle}"
            ".arr{color:#9a9080;font-weight:400;margin:0 6px;font-size:32px}"
            ".cap{font-size:30px;color:#8a8278;text-align:center;margin-top:20px}"
        )
        cap = "一条链跑通，不用五个窗口来回翻"
        _win_chrome("改造后 · 接单链", f"<div class=body><div class=flowline>{step_html}</div>"
                    f"<div class=cap>{cap}</div></div>", body_css, out)

    elif kind == "table":
        rows_html = []
        for l in lines:
            cells = [c.strip() for c in re.split(r"\||\t", l)]
            if len(cells) < 2:
                cells = re.split(r"\s{2,}", l.strip())
            alert = "撞档" in l or "标红" in l or "冲突" in l or "已满" in l
            cls = "row alert" if alert else "row"
            tds = "".join(f"<td>{html.escape(c)}</td>" for c in cells)
            rows_html.append(f"<tr class='{cls}'>{tds}</tr>")
        body_css = (
            ".body{background:#fff;padding:50px 40px;min-height:900px;overflow:auto}"
            "table{width:100%;border-collapse:collapse;font-size:36px}"
            "th{background:#f3f0ea;color:#5c5348;font-weight:700;padding:28px 20px;text-align:left;border-bottom:3px solid #e8e2d8}"
            "td{padding:26px 20px;border-bottom:1px solid #eee;color:#2a2520;vertical-align:top}"
            ".alert td{background:#fff0f0;color:#c62828;font-weight:700}"
        )
        thead = "<tr><th>时段</th><th>技师</th><th>状态</th><th>来源</th></tr>" if rows_html else ""
        _win_chrome("共享预约表 · 周六", f"<div class=body><table>{thead}{''.join(rows_html)}</table></div>", body_css, out)

    elif kind == "notify":
        items = []
        app_name = lines[0].strip() if lines else "通知"
        for l in lines[1:]:
            s = l.strip()
            if not s or (s.startswith("（") and s.endswith("）")):
                continue
            if "·" in s and len(s.split("·", 1)[0]) < 12:
                parts = s.split("·", 1)
                items.append((parts[0].strip(), parts[1].strip()))
            else:
                items.append((app_name, s))
        if not items:
            items.append((app_name, app_name))
        notif_html = "".join(
            f'<div class=n><div class=app>{html.escape(app)}</div><div class=tx>{html.escape(txt)}</div></div>'
            for app, txt in items[:4]
        )
        css = f"""*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:{VW}px;height:{VH}px;background:#1a1a1a;font-family:{FONT_STACK}}}
.wrap{{width:100%;height:100%;padding:120px 80px;display:flex;justify-content:center;align-items:center}}
.phone{{width:920px;border-radius:48px;background:#0f0f0f;padding:24px;box-shadow:0 40px 100px rgba(0,0,0,.6)}}
.screen{{border-radius:32px;background:linear-gradient(180deg,#2a2a2e 0%,#1c1c1e 100%);padding:80px 36px 60px;min-height:1400px}}
.time{{text-align:center;font-size:88px;font-weight:200;color:#fff;margin-bottom:60px}}
.date{{text-align:center;font-size:32px;color:#8e8e93;margin-bottom:48px}}
.stack{{display:flex;flex-direction:column;gap:20px}}
.n{{background:rgba(255,255,255,.92);border-radius:24px;padding:28px 32px;backdrop-filter:blur(20px)}}
.app{{font-size:26px;font-weight:700;color:#8e8e93;text-transform:uppercase;margin-bottom:8px}}
.tx{{font-size:38px;font-weight:600;line-height:1.35;color:#1c1c1e}}"""
        _chrome(
            f"<!DOCTYPE html><html><head><meta charset=utf-8><style>{css}</style></head>"
            f"<body><div class=wrap><div class=phone><div class=screen>"
            f"<div class=time>17:30</div><div class=date>周五 · 晚高峰</div>"
            f"<div class=stack>{notif_html}</div></div></div></div></body></html>", out)

    elif kind == "tally":
        title_line = lines[0].strip() if lines else "今日核销 tally"
        data_lines = lines[1:] if len(lines) > 1 else lines
        rows = "".join(
            f'<div class=row><span class=chk>{"☑" if "✓" in l or "☑" in l else "☐"}</span>'
            f'<span class=tx>{html.escape(re.sub(r"^[☐☑✓]\s*", "", l.strip()))}</span></div>'
            for l in data_lines if l.strip()
        )
        css = f"""*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:{VW}px;height:{VH}px;background:#3d3428;font-family:{FONT_STACK}}}
.pad{{width:100%;height:100%;padding:100px 70px;display:flex;justify-content:center;align-items:center}}
.paper{{width:100%;max-width:960px;background:#fef9e7;border-radius:8px;padding:60px 56px;
  box-shadow:0 8px 40px rgba(0,0,0,.35);transform:rotate(-1.5deg);
  background-image:repeating-linear-gradient(transparent,transparent 54px,#e8dcc0 54px,#e8dcc0 55px);
  background-position:0 40px}}
.title{{font-size:52px;font-weight:800;color:#5c4033;margin-bottom:36px;border-bottom:4px solid #c4a574;padding-bottom:16px}}
.row{{display:flex;align-items:flex-start;gap:20px;font-size:42px;line-height:1.6;color:#3d2914;margin:20px 0}}
.chk{{font-size:44px;color:#8b6914;flex-shrink:0}}
.tx{{font-family:'Bradley Hand','Snell Roundhand','PingFang SC',cursive}}"""
        title = html.escape(title_line)
        body_rows = rows
        _chrome(
            f"<!DOCTYPE html><html><head><meta charset=utf-8><style>{css}</style></head>"
            f"<body><div class=pad><div class=paper><div class=title>{title}</div>{body_rows}</div></div></body></html>",
            out)

    elif kind == "profile":
        name = lines[0].strip() if lines else "客资 · 匿名"
        fields = []
        for l in lines[1:]:
            if "：" in l or ":" in l:
                k, v = re.split(r"[：:]", l, maxsplit=1)
                fields.append((k.strip(), v.strip()))
            elif l.strip():
                fields.append(("", l.strip()))
        rows = "".join(
            f'<div class=fr><span class=fk>{html.escape(k)}</span><span class=fv>{html.escape(v)}</span></div>'
            if k else f'<div class=fn>{html.escape(v)}</div>'
            for k, v in fields
        )
        css = f"""*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:{VW}px;height:{VH}px;background:#eceff1;font-family:{FONT_STACK}}}
.wrap{{width:100%;height:100%;padding:100px 70px;display:flex;justify-content:center;align-items:center}}
.card{{width:100%;background:#fff;border-radius:28px;overflow:hidden;box-shadow:0 20px 60px rgba(0,0,0,.12)}}
.head{{background:linear-gradient(135deg,#ff6f00,#ff9800);padding:48px 56px;color:#fff}}
.name{{font-size:56px;font-weight:800;margin-bottom:8px}}
.tag{{font-size:30px;opacity:.9}}
.body{{padding:48px 56px}}
.fr{{display:flex;justify-content:space-between;padding:24px 0;border-bottom:1px solid #eee;font-size:38px}}
.fk{{color:#757575;font-weight:600}}.fv{{color:#212121;font-weight:700;text-align:right;max-width:58%}}
.fn{{font-size:44px;font-weight:800;color:#c62828;padding:20px 0}}"""
        name_esc = html.escape(name)
        tag = html.escape(sub or "客资档案")
        body_inner = rows
        _chrome(
            f"<!DOCTYPE html><html><head><meta charset=utf-8><style>{css}</style></head>"
            f"<body><div class=wrap><div class=card><div class=head>"
            f"<div class=name>{name_esc}</div><div class=tag>{tag}</div></div>"
            f"<div class=body>{body_inner}</div></div></div></body></html>", out)

    elif kind == "checklist":
        items = [l.strip().lstrip("①②③④⑤⑥⑦⑧ ").strip() for l in lines if l.strip()]
        rows = "".join(
            f'<div class=it><span class=box>{"✓" if l.startswith("✓") else ""}</span>'
            f'<span class=tx>{html.escape(l.lstrip("✓ ").strip())}</span></div>'
            for l in items
        )
        css = f"""*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:{VW}px;height:{VH}px;background:#fff8f0;font-family:{FONT_STACK}}}
.wrap{{width:100%;height:100%;padding:100px 64px}}
.h{{font-size:56px;font-weight:900;color:#bf360c;margin-bottom:48px}}
.it{{display:flex;align-items:flex-start;gap:24px;padding:32px 0;border-bottom:2px dashed #ffccbc;font-size:42px;line-height:1.4;color:#3e2723}}
.box{{width:52px;height:52px;border:4px solid #bf360c;border-radius:10px;flex-shrink:0;
  display:flex;align-items:center;justify-content:center;font-size:36px;font-weight:800;color:#bf360c}}"""
        _chrome(
            f"<!DOCTYPE html><html><head><meta charset=utf-8><style>{css}</style></head>"
            f"<body><div class=wrap><div class=h>{html.escape(sub or '最小清单')}</div>{rows}</div></body></html>",
            out)

    else:  # note
        fallback_card("\n".join(lines)[:120], out, tag="项目笔记")


# ── 封面底图选择：品牌美图模糊打底 > shot > 渐变 ──
def pick_cover_bg(pid: str, cv: dict, status: dict, shots_dir: pathlib.Path) -> pathlib.Path | None:
    proj = ROOT / "projects" / pid
    # 1) content 显式指定 cover.bg（repo 相对路径或 glob）
    explicit = (cv.get("bg") or "").strip()
    if explicit:
        cands = sorted((ROOT.glob(explicit) if any(c in explicit for c in "*?[") else [ROOT / explicit]))
        cands = [p for p in cands if p.exists()]
        if cands:
            return _pick_by_hook(cands, cv)
    # 2) cover.shot_ref 对应的真实截图
    cref = (cv.get("shot_ref") or "").strip()
    if cref and status.get(cref) == "ok":
        p = shots_dir / f"{cref}.png"
        if p.exists():
            return p
    # 3) 项目自带品牌图：coverbg/ 或 仓库产出 pins/final（启发式）
    pools: list[pathlib.Path] = sorted((proj / "coverbg").glob("*.png")) if (proj / "coverbg").exists() else []
    if not pools:
        pools = sorted(proj.glob("repo/**/pins/final/*.png"))
    if pools:
        return _pick_by_hook(pools, cv)
    # 4) 无图 → 设计版深色暖金渐变（在 cover_png 内处理）
    return None


def _pick_by_hook(cands: list[pathlib.Path], cv: dict) -> pathlib.Path:
    """按 hook 文案做确定性选择，使 douyin/channels 自动错开同一张图。"""
    seed = (cv.get("hook", "") + cv.get("kicker", "")) or "x"
    return cands[sum(ord(c) for c in seed) % len(cands)]


# ── 封面：light_split（证据风）| dark（旧版，非必要不用） ──
def cover_light_split(cv: dict, out: pathlib.Path, panel: pathlib.Path | None) -> None:
    hook = (cv.get("hook") or "").strip()
    kicker = (cv.get("kicker") or "真实小店").strip()
    sub = (cv.get("sub") or "").strip()
    badge = (cv.get("badge") or "").strip()
    theme = (cv.get("theme") or "").strip()
    accent = "#2e7d52" if theme == "health" else "#d32f2f"
    lines = [ln for ln in re.split(r"[\n｜]", hook) if ln.strip()] or [hook]
    l1 = html.escape(lines[0]) if lines else ""
    l2 = html.escape(lines[1]) if len(lines) > 1 else ""
    panel_html = ""
    if panel and panel.exists():
        import base64
        b64 = base64.b64encode(panel.read_bytes()).decode()
        panel_html = (
            f'<div class=panel><img src="data:image/png;base64,{b64}" alt=""></div>'
        )
    badge_html = f'<div class=badge>{html.escape(badge)}</div>' if badge else ""
    sub_html = f'<div class=sub>{html.escape(sub)}</div>' if sub else ""
    css = f"""*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:{VW}px;height:{VH}px;font-family:{FONT_STACK};background:#faf8f5}}
.c{{width:100%;height:100%;display:flex;position:relative;overflow:hidden}}
.left{{flex:0 0 58%;padding:100px 56px 120px 64px;display:flex;flex-direction:column;background:#faf8f5;z-index:2}}
.right{{flex:1;position:relative;background:#e8e8e8;overflow:hidden}}
.panel{{position:absolute;inset:40px 20px 40px 0;border-radius:20px;overflow:hidden;
  box-shadow:-8px 0 40px rgba(0,0,0,.12)}}
.panel img{{width:100%;height:100%;object-fit:cover;object-position:left top}}
.kicker{{font-size:30px;font-weight:700;color:#8a7560;letter-spacing:.06em;margin-bottom:36px}}
.hk1{{font-size:88px;font-weight:900;line-height:1.12;color:#1a1a1a;margin-bottom:12px}}
.hk2{{font-size:88px;font-weight:900;line-height:1.12;color:{accent};margin-bottom:auto}}
.badge{{align-self:flex-start;margin-top:32px;font-size:32px;font-weight:800;color:#fff;
  background:{accent};padding:16px 28px;border-radius:12px}}
.sub{{margin-top:28px;font-size:40px;font-weight:700;line-height:1.35;color:#4a4540;
  border-left:6px solid {accent};padding-left:24px}}"""
    _chrome(
        f"<!DOCTYPE html><html><head><meta charset=utf-8><style>{css}</style></head>"
        f"<body><div class=c><div class=left>"
        f"<div class=kicker>{html.escape(kicker)}</div>"
        f"<div class=hk1>{l1}</div><div class=hk2>{l2}</div>"
        f"{badge_html}{sub_html}</div>"
        f"<div class=right>{panel_html}</div></div></body></html>",
        out,
    )


def cover_xhs_clean(cv: dict, out: pathlib.Path) -> None:
    """小红书封面：纯排版、无仿微信/UI，降低审核风险。"""
    hook = (cv.get("hook") or "").strip()
    kicker = (cv.get("kicker") or "小店流程改造").strip()
    sub = (cv.get("sub") or "").strip()
    steps = [s.strip() for s in (cv.get("steps") or "先回模板,写入同表,标红提醒").split(",") if s.strip()]
    foot = (cv.get("foot") or "改造实录 · 非教程非广告").strip()
    lines = [ln for ln in re.split(r"[\n｜]", hook) if ln.strip()] or [hook]
    l1 = html.escape(lines[0]) if lines else ""
    l2 = html.escape(lines[1]) if len(lines) > 1 else ""
    l3 = html.escape(lines[2]) if len(lines) > 2 else ""
    step_html = "".join(f"<span class=pill>{html.escape(s)}</span>" for s in steps[:3])
    sub_html = f'<div class=sub>{html.escape(sub)}</div>' if sub else ""
    l3_html = f'<div class=hk3>{l3}</div>' if l3 else ""
    css = f"""*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:{VW}px;height:{VH}px;font-family:{FONT_STACK};background:#f4f6f2}}
.c{{width:100%;height:100%;padding:88px 64px 100px;display:flex;flex-direction:column;
  background:linear-gradient(165deg,#fafbf8 0%,#eef2ea 55%,#e8ede3 100%)}}
.kicker{{font-size:32px;font-weight:700;color:#6b7c62;letter-spacing:.04em;margin-bottom:28px}}
.hk1{{font-size:82px;font-weight:900;line-height:1.14;color:#1c1c1c;margin-bottom:8px}}
.hk2{{font-size:82px;font-weight:900;line-height:1.14;color:#2e6b4a;margin-bottom:8px}}
.hk3{{font-size:56px;font-weight:800;line-height:1.25;color:#4a4a4a;margin-bottom:32px}}
.steps{{display:flex;flex-wrap:wrap;gap:20px;margin-top:auto;margin-bottom:36px}}
.pill{{font-size:34px;font-weight:700;color:#1e4d32;background:#fff;border:3px solid #8fbc8f;
  border-radius:999px;padding:18px 32px;box-shadow:0 4px 16px rgba(46,107,74,.08)}}
.sub{{font-size:38px;font-weight:600;line-height:1.45;color:#5a5a5a;margin-bottom:24px;
  padding:28px 32px;background:rgba(255,255,255,.75);border-radius:16px;border-left:6px solid #2e6b4a}}
.foot{{font-size:28px;color:#9aa393;letter-spacing:.04em}}"""
    _chrome(
        f"<!DOCTYPE html><html><head><meta charset=utf-8><style>{css}</style></head>"
        f"<body><div class=c><div class=kicker>{html.escape(kicker)}</div>"
        f"<div class=hk1>{l1}</div><div class=hk2>{l2}</div>{l3_html}"
        f"{sub_html}<div class=steps>{step_html}</div>"
        f"<div class=foot>{html.escape(foot)}</div></div></body></html>",
        out,
    )


def cover_phone_ui(cv: dict, out: pathlib.Path, panel: pathlib.Path | None) -> None:
    """F3 封面：手机锁屏 + 通知栈。"""
    hook = (cv.get("hook") or "").strip()
    kicker = (cv.get("kicker") or "小馆 · 团购").strip()
    sub = (cv.get("sub") or "").strip()
    lines = [ln for ln in re.split(r"[\n｜]", hook) if ln.strip()] or [hook]
    l1 = html.escape(lines[0]) if lines else ""
    l2 = html.escape(lines[1]) if len(lines) > 1 else ""
    panel_html = ""
    if panel and panel.exists():
        import base64
        b64 = base64.b64encode(panel.read_bytes()).decode()
        panel_html = f'<div class=mini><img src="data:image/png;base64,{b64}"></div>'
    sub_html = f'<div class=sub>{html.escape(sub)}</div>' if sub else ""
    css = f"""*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:{VW}px;height:{VH}px;font-family:{FONT_STACK};background:#1a1814}}
.c{{width:100%;height:100%;display:flex;position:relative}}
.left{{flex:0 0 52%;padding:88px 48px 100px 56px;display:flex;flex-direction:column;z-index:2}}
.right{{flex:1;display:flex;align-items:center;justify-content:center;padding:40px 20px 40px 0}}
.kicker{{font-size:28px;font-weight:700;color:#ffb74d;letter-spacing:.08em;margin-bottom:32px}}
.hk1{{font-size:76px;font-weight:900;line-height:1.12;color:#fff;margin-bottom:10px}}
.hk2{{font-size:76px;font-weight:900;line-height:1.12;color:#ff7043;margin-bottom:auto}}
.sub{{margin-top:24px;font-size:36px;font-weight:600;line-height:1.4;color:#bcaaa4;
  border-left:5px solid #ff7043;padding-left:20px}}
.mini{{width:100%;max-width:480px;border-radius:32px;overflow:hidden;
  box-shadow:0 24px 80px rgba(0,0,0,.5)}}
.mini img{{width:100%;display:block}}"""
    _chrome(
        f"<!DOCTYPE html><html><head><meta charset=utf-8><style>{css}</style></head>"
        f"<body><div class=c><div class=left>"
        f"<div class=kicker>{html.escape(kicker)}</div>"
        f"<div class=hk1>{l1}</div><div class=hk2>{l2}</div>{sub_html}</div>"
        f"<div class=right>{panel_html}</div></div></body></html>", out)


def cover_newspaper(cv: dict, out: pathlib.Path) -> None:
    """F4 封面：报纸头版风。"""
    hook = (cv.get("hook") or "").strip()
    kicker = (cv.get("kicker") or "经营号外").strip()
    sub = (cv.get("sub") or "").strip()
    stamp = (cv.get("stamp") or "号外").strip()
    lines = [ln for ln in re.split(r"[\n｜]", hook) if ln.strip()] or [hook]
    l1 = html.escape(lines[0]) if lines else ""
    l2 = html.escape(lines[1]) if len(lines) > 1 else ""
    sub_html = f'<div class=sub>{html.escape(sub)}</div>' if sub else ""
    css = f"""*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:{VW}px;height:{VH}px;font-family:{FONT_STACK};background:#f5f0e6}}
.c{{width:100%;height:100%;padding:72px 56px 80px;background:#faf6ee;
  background-image:radial-gradient(circle at 20% 80%,rgba(0,0,0,.03) 0%,transparent 50%)}}
.stamp{{position:absolute;top:80px;right:64px;background:#c62828;color:#fff;font-size:36px;font-weight:900;
  padding:16px 28px;border-radius:999px;transform:rotate(12deg);box-shadow:0 4px 16px rgba(198,40,40,.4)}}
.mast{{text-align:center;border-bottom:6px double #1a1a1a;padding-bottom:20px;margin-bottom:28px}}
.kicker{{font-size:32px;font-weight:700;color:#5d4037;letter-spacing:.2em;margin-bottom:12px}}
.name{{font-size:48px;font-weight:900;color:#1a1a1a;letter-spacing:.15em}}
.hk1{{font-size:92px;font-weight:900;line-height:1.1;color:#1a1a1a;margin:40px 0 8px}}
.hk2{{font-size:92px;font-weight:900;line-height:1.1;color:#b71c1c;margin-bottom:32px}}
.sub{{font-size:40px;font-weight:600;line-height:1.45;color:#4e342e;padding:28px 32px;
  background:#fff;border:3px solid #1a1a1a;margin-top:auto}}
.rule{{height:4px;background:#1a1a1a;margin:24px 0}}"""
    _chrome(
        f"<!DOCTYPE html><html><head><meta charset=utf-8><style>{css}</style></head>"
        f"<body><div class=c style=position:relative><div class=stamp>{html.escape(stamp)}</div>"
        f"<div class=mast><div class=kicker>{html.escape(kicker)}</div>"
        f"<div class=name>小 店 经 营 参 考</div></div>"
        f"<div class=rule></div><div class=hk1>{l1}</div><div class=hk2>{l2}</div>"
        f"{sub_html}</div></body></html>", out)


def _carousel_slide_newspaper(slide: dict, out: pathlib.Path, idx: int, *, theme: str = "") -> None:
    title = (slide.get("title") or "").strip()
    body = (slide.get("body") or "").strip()
    foot = (slide.get("foot") or "").strip()
    stamp = (slide.get("stamp") or "").strip()
    body_lines = [html.escape(ln.strip()) for ln in body.splitlines() if ln.strip()]
    if not body_lines and body:
        body_lines = [html.escape(body)]
    list_html = "".join(f"<li>{ln}</li>" for ln in body_lines)
    stamp_html = f'<div class=stamp>{html.escape(stamp)}</div>' if stamp else ""
    foot_html = f'<div class=foot>{html.escape(foot)}</div>' if foot else ""
    num = f"{idx:02d}"
    if theme == "health":
        bg, accent, ink, bullet = "#f4faf6", "#2e7d52", "#1b4332", "#2e7d52"
        stamp_bg = "#2e7d52"
    else:
        bg, accent, ink, bullet = "#faf6ee", "#bf360c", "#3e2723", "#bf360c"
        stamp_bg = "#c62828"
    css = f"""*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:{VW}px;height:{VH}px;font-family:{FONT_STACK};background:{bg}}}
.c{{width:100%;height:100%;padding:80px 56px 100px;position:relative;display:flex;flex-direction:column}}
.stamp{{position:absolute;top:72px;right:56px;background:{stamp_bg};color:#fff;font-size:30px;font-weight:800;
  padding:12px 22px;border-radius:999px;transform:rotate(8deg)}}
.num{{font-size:28px;color:#6b7c62;letter-spacing:.1em;margin-bottom:16px}}
.title{{font-size:72px;font-weight:900;line-height:1.15;color:#1a1a1a;margin-bottom:36px;
  border-bottom:5px solid {accent};padding-bottom:24px}}
ul{{list-style:none;padding:0;margin:0;flex:1}}
li{{font-size:42px;line-height:1.55;color:{ink};padding:20px 0 20px 36px;position:relative;
  border-bottom:1px dashed #bcaaa4}}
li::before{{content:'▪';position:absolute;left:0;color:{bullet};font-size:36px}}
.foot{{margin-top:auto;font-size:34px;font-weight:700;color:#5d4037;padding-top:32px;
  border-top:3px double {accent}}}"""
    _chrome(
        f"<!DOCTYPE html><html><head><meta charset=utf-8><style>{css}</style></head>"
        f"<body><div class=c>{stamp_html}<div class=num>— {num} —</div>"
        f"<div class=title>{html.escape(title)}</div><ul>{list_html}</ul>{foot_html}</div></body></html>",
        out)


def render_carousel(car_spec: dict, out_dir: pathlib.Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    style = (car_spec.get("style") or "newspaper").strip()
    theme = (car_spec.get("theme") or "").strip()
    slides = car_spec.get("slides") or []
    for i, slide in enumerate(slides, 1):
        out = out_dir / f"{i:02d}.png"
        if style == "newspaper":
            _carousel_slide_newspaper(slide, out, i, theme=theme)
        else:
            fallback_card(slide.get("title", ""), out, tag=f"清单 {i:02d}")
        print(f"    carousel/{out.name}")


def _resolve_cover_video(pid: str, cv: dict) -> pathlib.Path | None:
    """定位抖音成片，供 video_frame 封面截取。"""
    explicit = (cv.get("video") or "").strip()
    if explicit:
        p = pathlib.Path(explicit) if pathlib.Path(explicit).is_absolute() else ROOT / explicit
        if p.exists():
            return p
    candidates: list[pathlib.Path] = [
        publish_out_root(pid) / "douyin" / "video.mp4",
        ROOT / "pipeline" / "p004_video" / "out" / "final" / "video.mp4",
    ]
    for week_dir in sorted((ROOT / "publish").glob("20*"), reverse=True):
        for day_dir in week_dir.iterdir():
            meta_f = day_dir / "meta.yaml"
            if not meta_f.exists():
                continue
            try:
                meta = yaml.safe_load(meta_f.read_text(encoding="utf-8")) or {}
            except Exception:
                continue
            if meta.get("project_id") == pid:
                v = day_dir / "douyin" / "video.mp4"
                if v.exists():
                    candidates.insert(0, v)
    for p in candidates:
        if p.exists():
            return p
    return None


def cover_video_frame(video: pathlib.Path, at_sec: float, out: pathlib.Path) -> None:
    """抖音原生：成片定格帧，封面=视频缩略图感。"""
    subprocess.run(
        ["ffmpeg", "-y", "-ss", f"{at_sec:.3f}", "-i", str(video),
         "-frames:v", "1", "-q:v", "2", str(out)],
        capture_output=True, check=True,
    )


def cover_douyin_punch(cv: dict, out: pathlib.Path) -> None:
    """抖音原生：全屏黑底 punch 大字（P004 首镜风），禁分屏幻灯片。"""
    hook = (cv.get("hook") or "").strip()
    sub = (cv.get("sub") or "").strip()
    lines = [ln for ln in re.split(r"[\n｜]", hook) if ln.strip()] or [hook]
    l1 = html.escape(lines[0]) if lines else ""
    l2 = html.escape(lines[1]) if len(lines) > 1 else ""
    l2_html = f'<div class=big2>{l2}</div>' if l2 else ""
    sub_html = f'<div class=sub>{html.escape(sub)}</div>' if sub else ""
    css = f"""*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:{VW}px;height:{VH}px;font-family:{FONT_STACK};background:#000}}
.c{{width:100%;height:100%;display:flex;flex-direction:column;align-items:center;justify-content:center;
  padding:80px 48px;text-align:center}}
.big1{{font-size:168px;font-weight:900;line-height:1.05;color:#fff;letter-spacing:-4px}}
.big2{{font-size:168px;font-weight:900;line-height:1.05;color:#50fa7b;letter-spacing:-4px;margin-top:8px}}
.sub{{margin-top:48px;font-size:52px;font-weight:700;color:#8b93a7;line-height:1.35;max-width:920px}}"""
    _chrome(
        f"<!DOCTYPE html><html><head><meta charset=utf-8><style>{css}</style></head>"
        f"<body><div class=c><div class=big1>{l1}</div>{l2_html}{sub_html}</div></body></html>",
        out,
    )


def _render_cover_file(pid: str, plat: str, cv: dict, title: str, out: pathlib.Path,
                       *, status: dict, shots_dir: pathlib.Path, tmp: pathlib.Path) -> None:
    style = (cv.get("style") or "").strip()
    if style == "video_frame":
        video = _resolve_cover_video(pid, cv)
        if not video:
            raise SystemExit(
                f"封面 video_frame 需要 douyin/video.mp4（{pid}），先出 P004 成片再 render cover"
            )
        at = float(cv.get("at", 1.0))
        cover_video_frame(video, at, out)
        print(f"    cover ← video_frame @{at}s · {video.name}")
        return
    if style == "douyin_punch":
        cover_douyin_punch(cv, out)
        return
    if plat == "douyin" and style in ("light_split", "phone_ui"):
        raise SystemExit(
            f"抖音封面禁止 style={style}（分屏+窗口 mock，非平台原生）。"
            "改用 video_frame 或 douyin_punch。见 templates/design/cover_standards.md"
        )
    bg = pick_cover_bg(pid, cv, status, shots_dir)
    panel_path = _cover_panel(cv, tmp)
    cover_png(cv, title, bg, out, panel=panel_path)


def _cover_panel(cv: dict, tmp: pathlib.Path) -> pathlib.Path | None:
    """从 panel_detail 生成封面证据卡（light_split / phone_ui 右栏）。"""
    pd = (cv.get("panel_detail") or "").strip()
    style = (cv.get("style") or "").strip()
    if not pd or style in ("xhs_clean", "newspaper"):
        return None
    panel = tmp / "cover_panel.png"
    evidence_card(cv.get("panel_kind", "chat"), pd, cv.get("sub", ""), panel)
    return panel


def cover_png(cv: dict, title: str, bg_img: pathlib.Path | None, out: pathlib.Path,
              *, panel: pathlib.Path | None = None) -> None:
    style = (cv.get("style") or "").strip()
    if style == "xhs_clean":
        cover_xhs_clean(cv, out)
        return
    if style == "phone_ui":
        cover_phone_ui(cv, out, panel)
        return
    if style == "newspaper":
        cover_newspaper(cv, out)
        return
    if style == "light_split":
        cover_light_split(cv, out, panel)
        return

    # 禁止无 style 回落黑金渐变——须显式 cover.style 或 panel_detail/背景图
    pd = (cv.get("panel_detail") or "").strip()
    if not style and not bg_img and not pd:
        raise SystemExit(
            "封面拒绝渲染：未指定 cover.style，且无 panel_detail/背景图。\n"
            "禁止回落黑金渐变模板。见 templates/design/cover_standards.md"
        )

    hook = (cv.get("hook") or title or "").strip()
    kicker = (cv.get("kicker") or "真实项目 · AI 小系统").strip()
    sub = (cv.get("sub") or "").strip()
    mark = (cv.get("mark") or "").strip()       # 要高亮的关键词（可选）

    # 钩子多行 + 关键词高亮
    lines = [ln for ln in re.split(r"[\n｜]", hook) if ln.strip()] or [hook]
    def _fmt(line: str) -> str:
        e = html.escape(line)
        if mark and mark in line:
            e = e.replace(html.escape(mark), f"<span class=mark>{html.escape(mark)}</span>")
        return e
    hook_html = "<br>".join(_fmt(ln) for ln in lines)
    # 末行无显式 mark 时，整条末行加底纹高亮，制造视觉落点
    if not mark and len(lines) >= 1:
        parts = hook_html.rsplit("<br>", 1)
        last = f"<span class=mark>{parts[-1]}</span>"
        hook_html = (parts[0] + "<br>" + last) if len(parts) == 2 else last

    if bg_img and bg_img.exists():
        import base64
        b64 = base64.b64encode(bg_img.read_bytes()).decode()
        bg_layer = (f".bg{{position:absolute;inset:-40px;"
                    f"background:url(data:image/png;base64,{b64}) center/cover;"
                    f"filter:blur(22px) brightness(.5) saturate(1.1);}}")
    else:
        bg_layer = (".bg{position:absolute;inset:0;"
                    "background:radial-gradient(120% 90% at 50% 8%,#3a2c12 0%,#1c150b 48%,#0c0a06 100%);}")

    sub_html = f"<div class=sub>{html.escape(sub)}</div>" if sub else ""
    css = f"""*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:{VW}px;height:{VH}px;font-family:{FONT_STACK}}}
.c{{width:100%;height:100%;position:relative;overflow:hidden;background:#0c0a06}}
{bg_layer}
.scrim{{position:absolute;inset:0;background:
  linear-gradient(180deg,rgba(8,8,6,.78) 0%,rgba(8,8,6,.30) 34%,rgba(8,8,6,.55) 70%,rgba(8,8,6,.9) 100%)}}
.wrap{{position:absolute;inset:0;padding:130px 70px 150px;display:flex;flex-direction:column}}
.kicker{{align-self:flex-start;font-size:34px;font-weight:700;letter-spacing:.12em;color:#ffd98a;
  border:2px solid rgba(255,217,138,.55);border-radius:999px;padding:14px 30px;margin-bottom:48px;
  background:rgba(0,0,0,.25);text-shadow:0 2px 8px rgba(0,0,0,.6)}}
.hk{{font-size:108px;font-weight:900;line-height:1.16;color:#fff;letter-spacing:.01em;
  text-shadow:0 4px 22px rgba(0,0,0,.92),0 0 3px rgba(0,0,0,.9)}}
.mark{{box-decoration-break:clone;-webkit-box-decoration-break:clone;
  background:linear-gradient(transparent 6%,#ffcf2e 6% 96%,transparent 96%);
  color:#1a1206;padding:0 10px;border-radius:4px}}
.sub{{margin-top:auto;font-size:46px;font-weight:700;line-height:1.4;color:#ffe7b0;
  text-shadow:0 3px 14px rgba(0,0,0,.9)}}
.sub::before{{content:'';display:block;width:90px;height:6px;border-radius:3px;
  background:#ffcf2e;margin-bottom:26px}}"""
    _chrome(
        f"<!DOCTYPE html><html><head><meta charset=utf-8><style>{css}</style></head>"
        f"<body><div class=c><div class=bg></div><div class=scrim></div>"
        f"<div class=wrap><div class=kicker>{html.escape(kicker)}</div>"
        f"<div class=hk>{hook_html}</div>{sub_html}</div></div></body></html>",
        out,
    )


# ── 素材解析：每个 segment → 一张底图 ──
def resolve_image(seg: dict, shots_dir: pathlib.Path, status: dict, tmp: pathlib.Path, idx: int) -> pathlib.Path:
    src, ref = seg.get("source"), seg.get("ref", "")
    if src == "shot" and status.get(ref) == "ok":
        p = shots_dir / f"{ref}.png"
        if p.exists():
            return p
    card = tmp / f"card_{idx:02d}.png"
    kind = seg.get("evidence_kind", "none") or "none"
    detail = seg.get("detail", "") or ""
    if src in ("evidence", "web") and kind != "none" and detail.strip():
        # author 已整理素材 → 渲染成像真实截图的体裁卡
        evidence_card(kind, detail, seg.get("sub", ""), card)
        print(f"    seg{idx} evidence/{kind}")
    else:
        # 兜底：shot 缺失或缺 detail → 干净备忘录卡
        tag = {"evidence": "仿真演示", "web": "资料补充", "shot": "项目画面"}.get(src, "项目笔记")
        fallback_card(seg.get("sub") or ref or "", card, tag)
        note = f"shot 缺失({status.get(ref,'?')})" if src == "shot" else f"{src} 缺 detail"
        print(f"    seg{idx} 回落卡片 · {note}")
    return card


# ── 单段 Ken Burns + 字幕 + 口播 → 一段 mp4 ──
def render_segment(img: pathlib.Path, sub_png: pathlib.Path, aud: pathlib.Path,
                   out: pathlib.Path, idx: int) -> float:
    d = dur(aud) + PAD
    frames = max(2, round(d * 30))
    # 交替运镜方向，制造剪辑感
    if idx % 3 == 0:
        z = "min(zoom+0.0008,1.14)"; x = "iw/2-(iw/zoom/2)"; y = "ih/2-(ih/zoom/2)"
    elif idx % 3 == 1:
        z = "min(zoom+0.0007,1.13)"; x = "0"; y = "ih/2-(ih/zoom/2)"          # 向左推
    else:
        z = "min(zoom+0.0007,1.13)"; x = "iw-(iw/zoom)"; y = "0"               # 向右下推
    vf = (
        f"[0:v]scale={VW*2}:{VH*2}:force_original_aspect_ratio=increase,crop={VW*2}:{VH*2},"
        f"zoompan=z='{z}':d={frames}:x='{x}':y='{y}':s={VW}x{VH}:fps=30,format=yuv420p[bg];"
        f"[bg][1:v]overlay=0:0,fade=t=in:st=0:d=0.25,fade=t=out:st={d-0.25:.2f}:d=0.25,format=yuv420p[v];"
        f"[2:a]apad,atrim=0:{d:.2f},afade=t=out:st={d-0.3:.2f}:d=0.3[a]"
    )
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(img), "-loop", "1", "-i", str(sub_png), "-i", str(aud),
         "-filter_complex", vf, "-map", "[v]", "-map", "[a]", "-t", f"{d:.2f}",
         "-c:v", "libx264", "-preset", "medium", "-crf", "20",
         "-c:a", "aac", "-b:a", "160k", "-ar", "44100", "-pix_fmt", "yuv420p", str(out)],
        capture_output=True, check=True,
    )
    return d


# ── xfade 转场拼接 ──
def xfade_concat(clips: list[pathlib.Path], durs: list[float], out: pathlib.Path) -> None:
    if len(clips) == 1:
        subprocess.run(["ffmpeg", "-y", "-i", str(clips[0]), "-c", "copy",
                        "-movflags", "+faststart", str(out)], capture_output=True, check=True)
        return
    inputs: list[str] = []
    for c in clips:
        inputs += ["-i", str(c)]
    vparts, aparts = [], []
    vprev, aprev, D = "[0:v]", "[0:a]", durs[0]
    for k in range(1, len(clips)):
        off = D - XFADE
        vlab, alab = f"[vx{k}]", f"[ax{k}]"
        kind = XF_KINDS[k % len(XF_KINDS)]
        vparts.append(f"{vprev}[{k}:v]xfade=transition={kind}:duration={XFADE}:offset={off:.2f}{vlab}")
        aparts.append(f"{aprev}[{k}:a]acrossfade=d={XFADE}{alab}")
        vprev, aprev = vlab, alab
        D += durs[k] - XFADE
    fc = ";".join(vparts + aparts)
    subprocess.run(
        ["ffmpeg", "-y", *inputs, "-filter_complex", fc,
         "-map", vprev, "-map", aprev,
         "-c:v", "libx264", "-preset", "medium", "-crf", "20",
         "-c:a", "aac", "-b:a", "160k", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(out)],
        capture_output=True, check=True,
    )


# ── 情绪弧线：段未显式标 emotion 时，按位置给一条起伏曲线 ──
def emotion_for(seg: dict, idx: int, total: int) -> str:
    explicit = (seg.get("emotion") or "").strip()
    if explicit:
        return explicit
    if total <= 1:
        return "happy"
    if idx == 0:
        return "happy"               # 首段兴奋钩子
    if idx == total - 1:
        return "neutral"             # 末段真诚收尾
    return EMOTION_ARC[idx % len(EMOTION_ARC)]


# ── BGM：随机截取一段，sidechain 闪避（说话压低/间隙浮起）后与口播混合 ──
def mix_bgm(video: pathlib.Path, bgm: pathlib.Path, out: pathlib.Path, *, gain: float = 0.55) -> bool:
    """把 bgm 随机一段叠到 video 的口播下。失败/缺失返回 False，不阻断主流程。"""
    if not bgm.exists():
        print(f"    ⚠ BGM 不存在，跳过：{bgm}")
        return False
    try:
        vdur, bdur = dur(video), dur(bgm)
    except Exception as e:  # noqa: BLE001
        print(f"    ⚠ BGM 探测时长失败，跳过：{e}")
        return False
    start = round(random.uniform(0, max(0.0, bdur - vdur - 0.5)), 2) if bdur > vdur + 1 else 0.0
    fo = max(0.5, vdur - 1.6)
    # [1] BGM：截取→压低增益→进出淡化；用口播 [0:a] 作 sidechain 触发闪避；再与口播混合
    fc = (
        f"[1:a]atrim={start}:{start + vdur},asetpts=PTS-STARTPTS,"
        f"volume={gain},afade=t=in:st=0:d=0.8,afade=t=out:st={fo:.2f}:d=1.2[bg];"
        f"[bg][0:a]sidechaincompress=threshold=0.03:ratio=8:attack=12:release=320:makeup=1[bgd];"
        f"[0:a][bgd]amix=inputs=2:normalize=0:duration=first:dropout_transition=0[a]"
    )
    tmp_out = out.with_name(out.stem + "_bgm.mp4")
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(video), "-i", str(bgm),
             "-filter_complex", fc, "-map", "0:v", "-map", "[a]",
             "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-ar", "44100",
             "-movflags", "+faststart", str(tmp_out)],
            capture_output=True, check=True,
        )
    except subprocess.CalledProcessError as e:
        msg = e.stderr.decode()[-300:] if e.stderr else str(e)
        print(f"    ⚠ BGM 混音失败，保留无 BGM 版：{msg}")
        tmp_out.unlink(missing_ok=True)
        return False
    tmp_out.replace(out)
    print(f"    ♪ BGM 叠加：{bgm.name} @ {start:.1f}s（gain {gain} · 闪避）")
    return True


def render_platform(pid: str, plat: str, spec: dict, shots_dir: pathlib.Path,
                    status: dict, shots_meta: dict) -> None:
    out_dir = publish_out_root(pid) / plat
    tmp = out_dir / "_tmp"
    tmp.mkdir(parents=True, exist_ok=True)

    car_spec = spec.get("carousel")
    if car_spec:
        render_carousel(car_spec, out_dir / "carousel")

    segs = spec.get("segments", []) or []
    cv = spec.get("cover", {}) or {}

    if not segs:
        if car_spec:
            _render_cover_file(pid, plat, cv, spec.get("title", ""), out_dir / "cover.png",
                               status=status, shots_dir=shots_dir, tmp=tmp)
            print(f"  [{plat}] ✓ carousel {len(car_spec.get('slides') or [])} 张 + cover.png")
        elif cv:
            _render_cover_file(pid, plat, cv, spec.get("title", ""), out_dir / "cover.png",
                               status=status, shots_dir=shots_dir, tmp=tmp)
            print(f"  [{plat}] ✓ cover.png only（无 video）")
        else:
            print(f"  [{plat}] 无 segments，跳过")
        return

    clips, durs = [], []
    n = len(segs)
    for i, seg in enumerate(segs):
        img = resolve_image(seg, shots_dir, status, tmp, i)
        sub = tmp / f"sub_{i:02d}.png"
        subtitle_png(seg.get("sub", ""), sub)
        aud = tmp / f"a_{i:02d}.mp3"
        emo = emotion_for(seg, i, n)
        prov = synthesize_text(seg.get("vo", ""), aud, emotion=emo)
        clip = tmp / f"seg_{i:02d}.mp4"
        d = render_segment(img, sub, aud, clip, i)
        clips.append(clip); durs.append(d)
        print(f"    seg{i}: {d:.1f}s · {seg.get('source')} · tts={prov} · 情绪={emo}")

    video = out_dir / "video.mp4"
    xfade_concat(clips, durs, video)
    mix_bgm(video, BGM_PATH, video)          # 叠 BGM（失败/缺失则保留无 BGM 版）
    total = dur(video)

    # 封面
    _render_cover_file(pid, plat, cv, spec.get("title", ""), out_dir / "cover.png",
                       status=status, shots_dir=shots_dir, tmp=tmp)
    print(f"  [{plat}] ✓ video.mp4 {total:.1f}s + cover.png")


def main() -> None:
    ap = argparse.ArgumentParser(description="content.yaml → 三平台视频")
    ap.add_argument("--id", required=True)
    ap.add_argument("--platform", nargs="*", choices=["douyin", "xhs", "channels"])
    ap.add_argument("--bgm", type=pathlib.Path, default=BGM_DEFAULT, help="背景音乐 mp3（随机截取）")
    args = ap.parse_args()

    global BGM_PATH
    BGM_PATH = args.bgm

    proj = ROOT / "projects" / args.id
    content = yaml.safe_load((proj / "content.yaml").read_text(encoding="utf-8"))
    shots_dir = proj / "shots"
    sp = proj / "shots_status.yaml"
    status = yaml.safe_load(sp.read_text(encoding="utf-8")) if sp.exists() else {}
    shots_meta = {s["ref"]: s for s in (content.get("shots") or [])}

    plats = args.platform or ["douyin", "xhs", "channels"]
    for plat in plats:
        print(f"[{plat}]")
        render_platform(args.id, plat, content.get(plat, {}), shots_dir, status, shots_meta)

    print("\n完成：")
    root = publish_out_root(args.id)
    for plat in plats:
        print(f"  {root.relative_to(ROOT)}/{plat}/video.mp4 + cover.png")


if __name__ == "__main__":
    main()
