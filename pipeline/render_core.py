#!/usr/bin/env python3
"""渲染内核 · 跨案例复用.

从 render_p001.py 抽取的通用部件：headless Chrome 截图、ffprobe 时长、
视频帧合成、单段渲染、片段拼接、Edge TTS。render_p001.py 与新通用产线
（render.py）都从这里导入，保证 9:16 / 字幕样式 / 编码参数一处定义。

修改前先看 docs/DECISIONS.md Q8（构图）/ pipeline/screen_dims.py。
"""
from __future__ import annotations

import base64
import json
import pathlib
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import pipeline.env_loader  # noqa: F401 — 加载 .env
from pipeline.screen_dims import VIDEO_H, VIDEO_W

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
FONT_SRC = "/System/Library/Fonts/STHeiti Medium.ttc"
EDGE = str(ROOT / ".venv" / "bin" / "edge-tts")

# P001 默认口播音（gen_speech.py 的 provider 体系可覆盖）
VOICE = "zh-CN-YunjianNeural"
RATE, PITCH, VOL = "+15%", "-2Hz", "-2%"

PAD, FADE = 0.35, 0.25
VW, VH = VIDEO_W, VIDEO_H  # 9:16 视频画布

# 视频帧：主画面满铺 + 底部渐变大字字幕
VIDEO_FRAME_CSS = f"""
*{{margin:0;padding:0;box-sizing:border-box;}}
html,body{{width:{VW}px;height:{VH}px;overflow:hidden;background:#0b0d10;}}
body{{position:relative;}}
.bg{{width:100%;height:100%;object-fit:fill;display:block;}}
.sub{{position:absolute;left:0;right:0;bottom:0;padding:28px 36px 56px;text-align:center;
  background:linear-gradient(180deg,rgba(11,13,16,0) 0%,rgba(11,13,16,.88) 45%,rgba(11,13,16,.95) 100%);
  font-family:"Hiragino Sans GB","STHeiti",sans-serif;font-size:40px;font-weight:700;line-height:1.35;
  color:#fff;text-shadow:0 2px 10px rgba(0,0,0,.9);}}
"""


def b64(p: pathlib.Path) -> str:
    return base64.b64encode(p.read_bytes()).decode()


def img_src(p: pathlib.Path) -> str:
    return f"data:image/png;base64,{b64(p)}"


def dur(path: pathlib.Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(path)],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return float(json.loads(out)["format"]["duration"])


def chrome_shot(html: str, out: pathlib.Path, w: int, h: int) -> None:
    """渲染 HTML 字符串为 PNG（headless Chrome）。"""
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as f:
        f.write(html)
        path = f.name
    subprocess.run(
        [
            CHROME,
            "--headless=new",
            "--disable-gpu",
            "--hide-scrollbars",
            f"--screenshot={out}",
            f"--window-size={w},{h}",
            "--force-device-scale-factor=1",
            f"file://{path}",
        ],
        capture_output=True,
        timeout=120,
        check=True,
    )


def shoot_url(url: str, out: pathlib.Path, w: int = VW, h: int = VH) -> None:
    """对真实 URL 截图为 9:16 PNG（shoot.py 用）。"""
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            CHROME,
            "--headless=new",
            "--disable-gpu",
            "--hide-scrollbars",
            f"--screenshot={out}",
            f"--window-size={w},{h}",
            "--force-device-scale-factor=1",
            "--virtual-time-budget=4000",  # 等页面渲染/字体加载
            url,
        ],
        capture_output=True,
        timeout=120,
        check=True,
    )


def composite_video_frame(img: pathlib.Path, subtitle: str, out: pathlib.Path) -> None:
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{VIDEO_FRAME_CSS}</style></head>
<body><img class="bg" src="{img_src(img)}"><div class="sub">{subtitle}</div></body></html>"""
    chrome_shot(html, out, VW, VH)


def render_video_segment(
    img: pathlib.Path, aud: pathlib.Path, subtitle: str, seg: pathlib.Path, frame: pathlib.Path
) -> float:
    """静态帧 + 口播 → 一段 mp4（P001 路线，无运镜）。"""
    composite_video_frame(img, subtitle, frame)
    d = dur(aud) + PAD
    vf = f"scale={VW}:{VH},fps=30,format=yuv420p,fade=t=in:st=0:d={FADE},fade=t=out:st={d - FADE:.2f}:d={FADE}"
    af = f"apad,afade=t=out:st={d - 0.35:.2f}:d=0.3"
    subprocess.run(
        [
            "ffmpeg", "-y", "-loop", "1", "-i", str(frame), "-i", str(aud),
            "-filter_complex", f"[0:v]{vf}[v];[1:a]{af}[a]",
            "-map", "[v]", "-map", "[a]", "-t", f"{d:.2f}",
            "-c:v", "libx264", "-preset", "medium", "-crf", "20",
            "-c:a", "aac", "-b:a", "160k", "-ar", "44100", "-pix_fmt", "yuv420p", str(seg),
        ],
        capture_output=True,
        check=True,
    )
    return d


def concat_segments(segs: list[pathlib.Path], out: pathlib.Path, tmp_dir: pathlib.Path) -> None:
    tmp_dir.mkdir(parents=True, exist_ok=True)
    lst = tmp_dir / f"list_{out.stem}.txt"
    lst.write_text("".join(f"file '{s}'\n" for s in segs), encoding="utf-8")
    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
         "-c:v", "libx264", "-preset", "medium", "-crf", "20",
         "-c:a", "aac", "-b:a", "160k", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(out)],
        capture_output=True,
        check=True,
    )


def tts_edge(
    text: str,
    out: pathlib.Path,
    voice: str = VOICE,
    rate: str = RATE,
    pitch: str = PITCH,
    vol: str = VOL,
) -> None:
    """Edge TTS 直出 mp3（P001 默认口播；通用产线走 gen_speech.synthesize）。"""
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [EDGE, "--voice", voice, "--rate", rate, "--pitch", pitch, "--volume", vol,
         "--text", text, "--write-media", str(out)],
        check=True,
        capture_output=True,
        text=True,
    )
