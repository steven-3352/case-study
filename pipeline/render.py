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
            me = l.startswith(("我", "我：", "我:"))
            txt = html.escape(l.split("：", 1)[-1].split(":", 1)[-1].strip())
            side = "me" if me else "you"
            bubbles.append(f"<div class='row {side}'><div class=b>{txt}</div></div>")
        body_css = (".body{background:#ededed;padding:60px 50px;min-height:1000px;display:flex;flex-direction:column;gap:34px}"
                    ".row{display:flex}.row.me{justify-content:flex-end}"
                    ".b{max-width:78%;font-size:42px;line-height:1.45;padding:30px 36px;border-radius:28px;color:#16331c;background:#fff}"
                    ".me .b{background:#95ec69}")
        _win_chrome("对话", f"<div class=body>{''.join(bubbles)}</div>", body_css, out)

    elif kind == "metric":
        items = "".join(
            f"<div class=mrow><span class=k>{html.escape(re.split('[=：]', l, maxsplit=1)[0].strip())}</span>"
            f"<span class=v>{html.escape(re.split('[=：]', l, maxsplit=1)[-1].strip())}</span></div>" for l in lines)
        body_css = (".body{background:#fbfaf7;padding:80px 70px;min-height:900px;display:flex;flex-direction:column;gap:40px}"
                    ".mrow{display:flex;justify-content:space-between;align-items:baseline;border-bottom:2px solid #ece7dd;padding-bottom:30px}"
                    ".k{font-size:42px;color:#6b6256}.v{font-size:64px;font-weight:800;color:#1a7f4b}")
        _win_chrome("数据", f"<div class=body>{items}</div>", body_css, out)

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


# ── 封面：品牌美图模糊打底 + kicker + 大钩子（关键词高亮）+ 副钩子 ──
def cover_png(cv: dict, title: str, bg_img: pathlib.Path | None, out: pathlib.Path) -> None:
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
    out_dir = ROOT / "publish" / pid / plat
    tmp = out_dir / "_tmp"
    tmp.mkdir(parents=True, exist_ok=True)
    segs = spec.get("segments", []) or []
    if not segs:
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

    # 封面：品牌美图模糊打底 + kicker + 大钩子 + 副钩子
    cv = spec.get("cover", {}) or {}
    bg = pick_cover_bg(pid, cv, status, shots_dir)
    cover_png(cv, spec.get("title", ""), bg, out_dir / "cover.png")
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
    for plat in plats:
        print(f"  publish/{args.id}/{plat}/video.mp4 + cover.png")


if __name__ == "__main__":
    main()
