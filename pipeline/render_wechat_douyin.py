#!/usr/bin/env python3
"""抖音视觉升级 v2 · 微信群聊体（仿真聊天 UI + 状态标签）· 仅 P005 douyin.

铁律①试点之二：把「见异思迁」做成「我和 5 个 AI 编程工具的聊天记录」——
撤回/已读不回/加好友验证/拍了拍/现任，原生网感、代入感强。
口播/字幕/时长沿用 content.yaml 的 douyin segments，只重做画面。

默认只出 7 张静态画面预览（不跑 TTS、不刷余额）：
  .venv/bin/python3 pipeline/render_wechat_douyin.py
出带配音的完整视频（确认画面后再跑）：
  .venv/bin/python3 pipeline/render_wechat_douyin.py --render
"""
from __future__ import annotations
import argparse, html, pathlib, subprocess, sys
import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import pipeline.env_loader  # noqa: F401
import pipeline.render as R
from pipeline.render_core import VW, VH, dur

PAD = 0.18
FONT = '"Hiragino Sans GB","PingFang SC","STHeiti",sans-serif'
MONO = '"SF Mono","Menlo",monospace'

# 工具头像：品牌色渐变 + 标识字
AV = {
    "me":      ("😎", "linear-gradient(135deg,#4b9bff,#2b6fe0)"),
    "copilot": ("C",  "linear-gradient(135deg,#6e7681,#30363d)"),
    "cursor":  ("⌘",  "linear-gradient(135deg,#222,#000)"),
    "windsurf":("🏄", "linear-gradient(135deg,#19c37d,#0e8a5a)"),
    "claude":  ("✦",  "linear-gradient(135deg,#d97757,#b45309)"),
    "codex":   ("◎",  "linear-gradient(135deg,#10a37f,#0b6e56)"),
}

# 7 段聊天剧本，与 content.yaml douyin 7 段一一对应
# row = (who, type, text)  who∈me/them ; type∈text/code/sys/tag/time
SPECS = [
    {"nav": "我的聊天", "avatar": "me", "rows": [
        ("time", "", "2021 – 2025"),
        ("them", "text", "（5 个 AI 编程工具排队等你翻牌）"),
        ("me", "text", "我换工具，比有些人换对象还勤 🙈"),
        ("tag", "", "AI 编程工具情史 · 共 5 任"),
    ]},
    {"nav": "Copilot（初恋）", "avatar": "copilot", "rows": [
        ("time", "", "2021 · 初恋"),
        ("them", "text", "你刚敲一行，我灰字替你补完下一行～"),
        ("me", "text", "天呐，第一次有人这么懂我 ❤️"),
        ("sys", "", "后来你发现：他只会接话茬"),
        ("tag", "", "💔 已分手"),
    ]},
    {"nav": "Cursor（会读心）", "avatar": "cursor", "rows": [
        ("time", "", "2023"),
        ("me", "text", "你怎么知道我要改哪一行？"),
        ("them", "text", "光标停哪我改哪呀，Cmd+K 一片都帮你改好 😘"),
        ("me", "text", "如胶似漆…但你也太黏、太费钱了"),
        ("tag", "", "💔 腻了，分"),
    ]},
    {"nav": "Windsurf 想加你为好友", "avatar": "windsurf", "rows": [
        ("sys", "", "Windsurf 请求添加你为好友"),
        ("them", "text", "我更年轻、界面更顺，活儿自己往下跑哦"),
        ("me", "text", "（一眼移情）通过验证 ✅"),
        ("tag", "", "💔 新鲜劲过了"),
    ]},
    {"nav": "Claude Code", "avatar": "claude", "rows": [
        ("me", "text", "这堆脏活累活，谁接？"),
        ("them", "text", "我来。读了 18 个文件，改了 6 个"),
        ("them", "code", "✓ 41 passed\n  全绿，已跑通"),
        ("me", "text", "素颜不打扮，但是真能扛 🥹"),
        ("tag", "", "💚 现任"),
    ]},
    {"nav": "Codex", "avatar": "codex", "rows": [
        ("sys", "", "Codex 拍了拍你"),
        ("them", "text", "我在云端开好沙箱、自己跑完了"),
        ("them", "text", "改完直接给你提个 PR ✌️"),
        ("me", "text", "（又心痒）这么主动的吗…"),
        ("tag", "", "💛 暧昧中 · 最新最热"),
    ]},
    {"nav": "我的聊天", "avatar": "me", "rows": [
        ("time", "", "情史总结"),
        ("them", "text", "前任 ×3　现任 ×1　暧昧 ×1"),
        ("me", "text", "心动的一大把，能陪我干完活的没几个"),
        ("tag", "", "你处到第几个了？👇"),
    ]},
]


def _row_html(who: str, typ: str, text: str, avatar: str) -> str:
    if typ == "time":
        return f'<div class="time">{html.escape(text)}</div>'
    if typ == "sys":
        return f'<div class="sys">{html.escape(text)}</div>'
    if typ == "tag":
        return f'<div class="tagwrap"><span class="tag">{html.escape(text)}</span></div>'
    # text / code bubble
    av_char, av_bg = AV.get(avatar if who == "them" else "me", AV["me"])
    av = f'<div class="av" style="background:{av_bg}">{av_char}</div>'
    if typ == "code":
        inner = "".join(f'<div class="cl">{html.escape(l)}</div>' for l in text.splitlines())
        bubble = f'<div class="bub code">{inner}</div>'
    else:
        bubble = f'<div class="bub">{html.escape(text)}</div>'
    if who == "me":
        return f'<div class="row me">{bubble}{av}</div>'
    return f'<div class="row them">{av}{bubble}</div>'


def chat_png(spec: dict, out: pathlib.Path) -> None:
    rows = "".join(_row_html(w, t, x, spec["avatar"]) for (w, t, x) in spec["rows"])
    nav = html.escape(spec["nav"])
    css = f"""*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:{VW}px;height:{VH}px;font-family:{FONT};background:#ededed}}
.phone{{width:100%;height:100%;display:flex;flex-direction:column}}
.nav{{flex:0 0 auto;background:#ededed;border-bottom:1px solid #d6d6d6;
  padding:70px 40px 30px;display:flex;align-items:center;gap:24px;position:relative}}
.back{{font-size:60px;color:#181818;line-height:1}}
.title{{flex:1;text-align:center;font-size:52px;font-weight:700;color:#181818;
  margin-right:84px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.body{{flex:1;padding:46px 40px;display:flex;flex-direction:column;gap:40px;overflow:hidden}}
.time{{align-self:center;font-size:32px;color:#fff;background:#c2c2c2;
  padding:8px 24px;border-radius:10px}}
.sys{{align-self:center;font-size:34px;color:#8a8a8a;text-align:center;line-height:1.4;max-width:80%}}
.row{{display:flex;align-items:flex-start;gap:24px;max-width:100%}}
.row.me{{flex-direction:row-reverse}}
.av{{flex:0 0 auto;width:96px;height:96px;border-radius:18px;color:#fff;
  font-size:50px;font-weight:800;display:flex;align-items:center;justify-content:center;
  box-shadow:0 4px 12px rgba(0,0,0,.18)}}
.bub{{position:relative;max-width:680px;font-size:46px;line-height:1.45;
  padding:30px 38px;border-radius:24px;background:#fff;color:#1a1a1a;
  box-shadow:0 2px 8px rgba(0,0,0,.06);word-break:break-word}}
.row.me .bub{{background:#95ec69}}
.bub.code{{background:#1e1e1e;color:#d6f5d6;font-family:{MONO};font-size:40px;line-height:1.6}}
.cl{{white-space:pre-wrap}}
.tagwrap{{display:flex;justify-content:center;margin-top:14px}}
.tag{{font-size:56px;font-weight:900;color:#fff;
  background:linear-gradient(135deg,#ff4d6d,#c026d3);
  padding:22px 52px;border-radius:999px;box-shadow:0 10px 30px rgba(192,38,211,.4);
  transform:rotate(-3deg)}}"""
    R._chrome(
        f"<!DOCTYPE html><html><head><meta charset=utf-8><style>{css}</style></head>"
        f'<body><div class=phone><div class=nav><span class=back>‹</span>'
        f'<span class=title>{nav}</span></div>'
        f'<div class=body>{rows}</div></div></body></html>', out)


def cover_png(out: pathlib.Path) -> None:
    css = f"""*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:{VW}px;height:{VH}px;font-family:{FONT};
  background:radial-gradient(120% 90% at 20% 0%,#25d366 0%,#0b8a4f 42%,#063d24 100%)}}
.w{{width:100%;height:100%;padding:150px 80px 120px;display:flex;flex-direction:column}}
.k{{align-self:flex-start;font-size:42px;font-weight:800;color:#063d24;
  background:#eafff0;padding:16px 36px;border-radius:999px;margin-bottom:54px}}
.h{{font-size:132px;font-weight:900;line-height:1.12;color:#fff;text-shadow:0 6px 30px rgba(0,0,0,.45)}}
.m{{box-decoration-break:clone;-webkit-box-decoration-break:clone;
  background:linear-gradient(transparent 8%,#ffe14d 8% 94%,transparent 94%);color:#0b3d24;padding:0 12px}}
.chips{{margin-top:70px;display:flex;flex-direction:column;gap:26px}}
.chip{{font-size:48px;color:#063d24;background:#fff;border-radius:22px;padding:26px 36px;
  box-shadow:0 8px 24px rgba(0,0,0,.2);font-weight:700}}
.chip .badge{{float:right;color:#ff4d6d;font-weight:900}}
.s{{margin-top:auto;font-size:54px;font-weight:800;color:#eafff0;text-shadow:0 3px 14px rgba(0,0,0,.5)}}"""
    body = ('<div class=k>聊天记录 · 程序员实录</div>'
            '<div class=h>我和5个AI工具<br><span class=m>的聊天记录</span></div>'
            '<div class=chips>'
            '<div class=chip>Copilot：你还在吗？<span class=badge>已分手</span></div>'
            '<div class=chip>Claude Code：我来扛<span class=badge style="color:#19c37d">现任</span></div>'
            '<div class=chip>Codex 拍了拍你<span class=badge style="color:#f59e0b">暧昧中</span></div>'
            '</div>'
            '<div class=s>你处到第几个了？👇</div>')
    R._chrome(f"<!DOCTYPE html><html><head><meta charset=utf-8><style>{css}</style></head>"
              f"<body><div class=w>{body}</div></body></html>", out)


def render_seg(card: pathlib.Path, sub: pathlib.Path, aud: pathlib.Path,
               out: pathlib.Path) -> float:
    d = dur(aud) + PAD
    frames = max(2, round(d * 30))
    # 聊天截图轻微缓推（像在往下看记录）+ 字幕叠层
    vf = (
        f"[0:v]scale={VW*2}:{VH*2}:force_original_aspect_ratio=increase,crop={VW*2}:{VH*2},"
        f"zoompan=z='min(zoom+0.0005,1.04)':d={frames}:x='iw/2-(iw/zoom/2)':y='0'"
        f":s={VW}x{VH}:fps=30,format=yuv420p[bg];"
        f"[bg][1:v]overlay=0:0,fade=t=in:st=0:d=0.22,fade=t=out:st={d-0.25:.2f}:d=0.25,format=yuv420p[v];"
        f"[2:a]apad,atrim=0:{d:.2f},afade=t=out:st={d-0.3:.2f}:d=0.3[a]"
    )
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(card), "-loop", "1", "-i", str(sub), "-i", str(aud),
         "-filter_complex", vf, "-map", "[v]", "-map", "[a]", "-t", f"{d:.2f}",
         "-c:v", "libx264", "-preset", "medium", "-crf", "20",
         "-c:a", "aac", "-b:a", "160k", "-ar", "44100", "-pix_fmt", "yuv420p", str(out)],
        capture_output=True, check=True)
    return d


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--render", action="store_true", help="出带配音完整视频（默认只出静态预览）")
    args = ap.parse_args()

    content = yaml.safe_load((ROOT / "projects/P005/content.yaml").read_text(encoding="utf-8"))
    segs = content["douyin"]["segments"]
    assert len(segs) == len(SPECS), f"段数不匹配 {len(segs)} vs {len(SPECS)}"
    out_dir = ROOT / "publish/P005/douyin"
    prev = out_dir / "_preview_wechat"
    prev.mkdir(parents=True, exist_ok=True)

    # 先出 7 张聊天画面 + 封面预览
    cover_png(prev / "cover.png")
    for i, spec in enumerate(SPECS):
        chat_png(spec, prev / f"frame_{i:02d}.png")
        print(f"  预览 frame_{i:02d}.png · {spec['nav']}")
    print(f"\n✓ 静态预览：{prev}/  （cover.png + frame_00..06.png）")

    if not args.render:
        print("画面 OK 后加 --render 出带配音完整视频。")
        return

    # --render：跑 TTS + 合成完整视频
    from pipeline.tts.gen_speech import synthesize_text
    tmp = out_dir / "_tmp_wechat"
    tmp.mkdir(parents=True, exist_ok=True)
    clips, durs, n = [], [], len(segs)
    for i, (seg, spec) in enumerate(zip(segs, SPECS)):
        card = prev / f"frame_{i:02d}.png"
        sub = tmp / f"sub_{i:02d}.png"
        R.subtitle_png(seg.get("sub", ""), sub)
        aud = tmp / f"a_{i:02d}.mp3"
        emo = R.emotion_for(seg, i, n)
        prov = synthesize_text(seg.get("vo", ""), aud, emotion=emo)
        clip = tmp / f"seg_{i:02d}.mp4"
        d = render_seg(card, sub, aud, clip)
        clips.append(clip); durs.append(d)
        print(f"  seg{i}: {d:.1f}s · {spec['nav']} · tts={prov} · {emo}")

    video = out_dir / "video.mp4"
    R.xfade_concat(clips, durs, video)
    R.mix_bgm(video, R.BGM_DEFAULT, video)
    cover_png(out_dir / "cover.png")
    print(f"\n✓ {video}  {dur(video):.1f}s + cover.png（微信群聊体）")


if __name__ == "__main__":
    main()
