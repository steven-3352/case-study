#!/usr/bin/env python3
"""抖音视觉升级 · 前任情史档案体（纯 CSS + 动效）· 仅 P005 douyin 测试.

铁律①试点：把「见异思迁」拟人成一段恋爱情史，每个工具一张「前任档案卡」
（颜值/能力星级 + 状态章 + 评语），状态章「砸」下来的入场动效，整卡缓推。
口播/字幕/时长沿用 content.yaml 的 douyin segments，只重做画面。

用法: .venv/bin/python3 pipeline/render_meme_douyin.py
"""
from __future__ import annotations
import html, pathlib, subprocess, sys
import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import pipeline.env_loader  # noqa: F401
import pipeline.render as R
from pipeline.render_core import VW, VH, dur
from pipeline.tts.gen_speech import synthesize_text

PAD = 0.18
FONT = '"Hiragino Sans GB","PingFang SC","STHeiti",sans-serif'
STAMP = {"red": "#ff3b4e", "green": "#23d18b", "gold": "#ffb302"}

# 背景：俏皮的粉紫渐变（替掉原来的暗金 PPT 感）
BG = ("radial-gradient(130% 100% at 18% -5%,#ff5e8a 0%,#a84bf0 38%,#5b2bd6 60%,#180f33 100%)")

# 每段画面规格（与 content.yaml 的 douyin 7 段一一对应）
SPECS = [
    {"kind": "cover", "title": "我的 AI 编程工具情史",
     "sub": "5 任前任 · 没一个长久", "stamp": ("海王预警", "red")},
    {"kind": "dossier", "n": "①", "year": "2021", "name": "GitHub Copilot",
     "tag": "初恋", "look": 3, "skill": 2, "note": "只会接话茬，补全完就没下文",
     "stamp": ("已分手", "red")},
    {"kind": "dossier", "n": "②", "year": "2023", "name": "Cursor",
     "tag": "会读心", "look": 4, "skill": 3, "note": "又黏又费钱，腻了",
     "stamp": ("已分手", "red")},
    {"kind": "dossier", "n": "③", "year": "2024", "name": "Windsurf",
     "tag": "新欢", "look": 4, "skill": 3, "note": "更年轻更顺，一时新鲜",
     "stamp": ("已分手", "red")},
    {"kind": "dossier", "n": "④", "year": "2025", "name": "Claude Code",
     "tag": "素颜实力派", "look": 2, "skill": 5, "note": "不打扮，但脏活全包最能扛",
     "stamp": ("现任", "green")},
    {"kind": "dossier", "n": "⑤", "year": "2025", "name": "OpenAI Codex",
     "tag": "最新最热", "look": 5, "skill": 4, "note": "云端自己跑，又让我心痒了",
     "stamp": ("暧昧中", "gold")},
    {"kind": "summary", "title": "情史总结",
     "lines": ["心动的 ⭐ 一大把", "能过日子的 💚 没几个", "那你呢？用到第几任了"],
     "stamp": ("你第几任？", "red")},
]


def _stars(n: int) -> str:
    full = '<span class="s f">★</span>' * n
    empty = '<span class="s e">★</span>' * (5 - n)
    return full + empty


def card_png(spec: dict, out: pathlib.Path) -> None:
    """渲染一张档案卡底图（不含状态章，章由动效层叠加）。"""
    k = spec["kind"]
    if k == "dossier":
        body = f"""
<div class="badge">第 {html.escape(spec['n'])} 任 · {html.escape(spec['year'])}</div>
<div class="name">{html.escape(spec['name'])}</div>
<div class="tag">「{html.escape(spec['tag'])}」</div>
<div class="rate"><span class="rl">颜值</span>{_stars(spec['look'])}</div>
<div class="rate"><span class="rl">能力</span>{_stars(spec['skill'])}</div>
<div class="note"><span class="nk">评</span>{html.escape(spec['note'])}</div>"""
    elif k == "cover":
        body = f"""
<div class="ctag">恋爱脑 · 程序员实录</div>
<div class="ctitle">{html.escape(spec['title'])}</div>
<div class="csub">{html.escape(spec['sub'])}</div>
<div class="row">💔 💔 💔 💚 💛</div>"""
    else:  # summary
        lines = "".join(f'<div class="sline">{html.escape(l)}</div>' for l in spec["lines"])
        body = f'<div class="stitle">{html.escape(spec["title"])}</div>{lines}'

    css = f"""*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:{VW}px;height:{VH}px;font-family:{FONT};background:{BG}}}
.wrap{{width:100%;height:100%;display:flex;align-items:center;justify-content:center;padding:90px 70px}}
.card{{width:100%;background:linear-gradient(160deg,rgba(38,24,66,.92),rgba(20,12,40,.96));
  border:3px solid rgba(255,255,255,.16);border-radius:48px;padding:90px 70px;
  box-shadow:0 40px 120px rgba(0,0,0,.55),inset 0 1px 0 rgba(255,255,255,.12)}}
.badge{{display:inline-block;font-size:40px;font-weight:800;color:#1a0f33;
  background:linear-gradient(90deg,#ffe08a,#ffc04d);padding:14px 34px;border-radius:999px;margin-bottom:46px}}
.name{{font-size:104px;font-weight:900;line-height:1.05;color:#fff;
  text-shadow:0 4px 24px rgba(0,0,0,.5);letter-spacing:.5px}}
.tag{{font-size:50px;font-weight:800;color:#ff9ec4;margin:14px 0 56px}}
.rate{{display:flex;align-items:center;gap:24px;margin-bottom:30px}}
.rl{{font-size:46px;color:#cdbff0;width:140px;font-weight:700}}
.s{{font-size:64px;line-height:1}}.s.f{{color:#ffcf2e;text-shadow:0 0 18px rgba(255,207,46,.6)}}
.s.e{{color:rgba(255,255,255,.22)}}
.note{{margin-top:46px;font-size:48px;line-height:1.5;color:#efe9ff;font-weight:600;
  background:rgba(255,255,255,.08);border-left:10px solid #ff5e8a;border-radius:18px;padding:34px 40px}}
.nk{{display:inline-block;background:#ff3b4e;color:#fff;font-weight:900;border-radius:12px;
  padding:4px 18px;margin-right:22px}}
.ctag{{display:inline-block;font-size:40px;font-weight:800;color:#fff;letter-spacing:.12em;
  border:3px solid rgba(255,255,255,.5);border-radius:999px;padding:14px 34px;margin-bottom:60px}}
.ctitle{{font-size:122px;font-weight:900;line-height:1.12;color:#fff;text-shadow:0 6px 30px rgba(0,0,0,.5)}}
.csub{{font-size:56px;font-weight:800;color:#ffd98a;margin-top:40px}}
.row{{font-size:84px;letter-spacing:18px;margin-top:80px}}
.stitle{{font-size:90px;font-weight:900;color:#fff;margin-bottom:60px}}
.sline{{font-size:72px;font-weight:800;color:#fff;line-height:1.5;margin-bottom:30px;
  text-shadow:0 3px 16px rgba(0,0,0,.45)}}"""
    R._chrome(
        f"<!DOCTYPE html><html><head><meta charset=utf-8><style>{css}</style></head>"
        f"<body><div class=wrap><div class=card>{body}</div></div></body></html>", out)


def stamp_png(text: str, color: str, out: pathlib.Path) -> None:
    """状态章：透明全画布，右上角红/绿/金印章（轻微旋转），由 ffmpeg 砸入。"""
    c = STAMP.get(color, STAMP["red"])
    css = f"""*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:{VW}px;height:{VH}px;background:transparent;font-family:{FONT}}}
.stamp{{position:absolute;top:235px;right:70px;transform:rotate(-11deg);
  border:9px solid {c};color:{c};font-size:58px;font-weight:900;letter-spacing:4px;
  padding:18px 38px;border-radius:22px;background:rgba(0,0,0,.06);
  box-shadow:0 0 0 4px rgba(255,255,255,.12);text-shadow:0 2px 6px rgba(0,0,0,.25)}}"""
    R._chrome(f"<!DOCTYPE html><html><head><meta charset=utf-8><style>{css}</style></head>"
              f"<body><div class=stamp>{html.escape(text)}</div></body></html>", out, transparent=True)


def render_seg(card: pathlib.Path, stamp: pathlib.Path, sub: pathlib.Path,
               aud: pathlib.Path, out: pathlib.Path) -> float:
    d = dur(aud) + PAD
    frames = max(2, round(d * 30))
    # 整卡缓推（轻微，保字幕清晰）+ 状态章砸入（上方滑入 + 透明渐显）+ 字幕叠层
    vf = (
        f"[0:v]scale={VW*2}:{VH*2}:force_original_aspect_ratio=increase,crop={VW*2}:{VH*2},"
        f"zoompan=z='min(zoom+0.0006,1.05)':d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
        f":s={VW}x{VH}:fps=30,format=yuv420p[bg];"
        f"[1:v]format=rgba,fade=t=in:st=0.10:d=0.22:alpha=1[st];"
        f"[bg][st]overlay=x=0:y='if(lt(t,0.34),(t/0.34-1)*240,0)':eval=frame[v1];"
        f"[v1][2:v]overlay=0:0,fade=t=in:st=0:d=0.22,fade=t=out:st={d-0.25:.2f}:d=0.25,format=yuv420p[v];"
        f"[3:a]apad,atrim=0:{d:.2f},afade=t=out:st={d-0.3:.2f}:d=0.3[a]"
    )
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(card), "-loop", "1", "-i", str(stamp),
         "-loop", "1", "-i", str(sub), "-i", str(aud),
         "-filter_complex", vf, "-map", "[v]", "-map", "[a]", "-t", f"{d:.2f}",
         "-c:v", "libx264", "-preset", "medium", "-crf", "20",
         "-c:a", "aac", "-b:a", "160k", "-ar", "44100", "-pix_fmt", "yuv420p", str(out)],
        capture_output=True, check=True)
    return d


def cover_png(out: pathlib.Path) -> None:
    """抖音封面：情史档案主题大字钩子。"""
    css = f"""*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:{VW}px;height:{VH}px;font-family:{FONT};background:{BG}}}
.w{{width:100%;height:100%;padding:150px 80px 130px;display:flex;flex-direction:column}}
.k{{align-self:flex-start;font-size:42px;font-weight:800;color:#1a0f33;
  background:linear-gradient(90deg,#ffe08a,#ffc04d);padding:16px 36px;border-radius:999px;margin-bottom:60px}}
.h{{font-size:130px;font-weight:900;line-height:1.12;color:#fff;text-shadow:0 6px 30px rgba(0,0,0,.5)}}
.m{{box-decoration-break:clone;-webkit-box-decoration-break:clone;
  background:linear-gradient(transparent 8%,#ffcf2e 8% 94%,transparent 94%);color:#1a0f33;padding:0 12px}}
.row{{font-size:90px;letter-spacing:20px;margin-top:64px}}
.s{{margin-top:auto;font-size:54px;font-weight:800;color:#ffd98a;text-shadow:0 3px 14px rgba(0,0,0,.6)}}
.s::before{{content:'';display:block;width:100px;height:8px;border-radius:4px;background:#ffcf2e;margin-bottom:28px}}"""
    body = ('<div class=k>恋爱脑 · 程序员实录</div>'
            '<div class=h>我换AI编程工具<br><span class=m>比换对象还勤</span></div>'
            '<div class=row>💔💔💔💚💛</div>'
            '<div class=s>5任前任档案 · 你用到第几任了</div>')
    R._chrome(f"<!DOCTYPE html><html><head><meta charset=utf-8><style>{css}</style></head>"
              f"<body><div class=w>{body}</div></body></html>", out)


def main() -> None:
    content = yaml.safe_load((ROOT / "projects/P005/content.yaml").read_text(encoding="utf-8"))
    segs = content["douyin"]["segments"]
    assert len(segs) == len(SPECS), f"段数不匹配 {len(segs)} vs {len(SPECS)}"
    out_dir = ROOT / "publish/P005/douyin"
    tmp = out_dir / "_tmp_meme"
    tmp.mkdir(parents=True, exist_ok=True)

    clips, durs = [], []
    n = len(segs)
    for i, (seg, spec) in enumerate(zip(segs, SPECS)):
        card = tmp / f"card_{i:02d}.png"
        card_png(spec, card)
        stamp = tmp / f"stamp_{i:02d}.png"
        stamp_png(spec["stamp"][0], spec["stamp"][1], stamp)
        sub = tmp / f"sub_{i:02d}.png"
        R.subtitle_png(seg.get("sub", ""), sub)
        aud = tmp / f"a_{i:02d}.mp3"
        emo = R.emotion_for(seg, i, n)
        prov = synthesize_text(seg.get("vo", ""), aud, emotion=emo)
        clip = tmp / f"seg_{i:02d}.mp4"
        d = render_seg(card, stamp, sub, aud, clip)
        clips.append(clip); durs.append(d)
        print(f"  seg{i}: {d:.1f}s · {spec['kind']}/{spec.get('name','')} · 章={spec['stamp'][0]} · tts={prov} · {emo}")

    video = out_dir / "video.mp4"
    R.xfade_concat(clips, durs, video)
    R.mix_bgm(video, R.BGM_DEFAULT, video)
    cover_png(out_dir / "cover.png")
    print(f"\n✓ {video}  {dur(video):.1f}s + cover.png（前任情史档案版）")


if __name__ == "__main__":
    main()
