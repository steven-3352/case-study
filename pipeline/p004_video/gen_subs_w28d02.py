#!/usr/bin/env python3
"""W28D02 字幕生成 + 烧录 · 从 seg_timing_w28d02.json 出 .srt 并烧进 mp4.

背景：VO 是我们自己合成的，seg_timing 里有精确 start + text，
不用剪映"智能识别"再跑一遍——直接出 srt + ffmpeg subtitles filter 烧字幕。

输出：
- build/final/vo_w28d02.srt（标准 srt · 剪映/PR/DaVinci 均可导入）
- build/final/preview_no_bgm_subs_v3.mp4（v2 上烧 VO 主字幕）

3 处大字覆盖（18:55·周五 / 三连快切 / CTA 便签）仍归剪映——那是设计元素。
"""
from __future__ import annotations

import json
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[2]
D02 = ROOT / "publish" / "2026-W28" / "D02-打工人5分钟出周报"
BUILD = D02 / "build"
AUDIO = BUILD / "audio"
FINAL = BUILD / "final"

# ffmpeg-full 才带 libass/subtitles filter；系统 brew ffmpeg 精简版没编
FFMPEG = "/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg"
FFPROBE = "/opt/homebrew/opt/ffmpeg-full/bin/ffprobe"

TIMING_PATH = AUDIO / "seg_timing_w28d02.json"
SRT_PATH = FINAL / "vo_w28d02.srt"
ASS_PATH = FINAL / "vo_w28d02.ass"
IN_MP4 = FINAL / "preview_no_bgm_v2.mp4"
OUT_MP4 = FINAL / "preview_no_bgm_subs_v3.mp4"


def fmt_time(sec: float) -> str:
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = int(sec % 60)
    ms = int(round((sec - int(sec)) * 1000))
    if ms == 1000:
        s += 1
        ms = 0
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def fmt_time_ass(sec: float) -> str:
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = int(sec % 60)
    cs = int(round((sec - int(sec)) * 100))
    if cs == 100:
        s += 1
        cs = 0
    return f"{h:d}:{m:02d}:{s:02d}.{cs:02d}"


_PUNCT = set("。！？，、 ")


def _tokenize(text: str) -> list[str]:
    """按标点切 tokens · 标点保留在 token 末尾。"""
    tokens: list[str] = []
    cur = ""
    for ch in text:
        cur += ch
        if ch in _PUNCT:
            tokens.append(cur)
            cur = ""
    if cur:
        tokens.append(cur)
    return tokens


def _greedy_pack(tokens: list[str], max_chars: int) -> list[str]:
    """贪心装箱 · 每箱 ≤ max_chars；单 token 超长则硬切。"""
    boxes: list[str] = []
    cur = ""
    for tok in tokens:
        # 单 token 超长：先关掉 cur，硬切 tok
        if len(tok) > max_chars:
            if cur:
                boxes.append(cur)
                cur = ""
            for i in range(0, len(tok), max_chars):
                chunk = tok[i:i + max_chars]
                if i + max_chars >= len(tok):
                    cur = chunk
                else:
                    boxes.append(chunk)
            continue
        if len(cur) + len(tok) > max_chars and cur:
            boxes.append(cur)
            cur = tok
        else:
            cur += tok
    if cur:
        boxes.append(cur)
    return boxes


def split_long_line(text: str, max_chars: int = 17) -> str:
    """单 cue 内折行 · SRT/ASS 中 \\N 即换行。42pt × 17 中文 ≈ 714px < 可用 960px。"""
    if len(text) <= max_chars:
        return text
    lines = _greedy_pack(_tokenize(text), max_chars)
    return "\n".join(lines)


def split_into_cues(text: str, max_cue_chars: int = 32) -> list[str]:
    """长段拆多个 cue · 每 cue ≤ max_cue_chars（≈2 行 × 17 - 部分空白）。"""
    if len(text) <= max_cue_chars:
        return [text]
    return _greedy_pack(_tokenize(text), max_cue_chars)


def gen_srt() -> None:
    data = json.loads(TIMING_PATH.read_text(encoding="utf-8"))
    segments = data["segments"]
    lines: list[str] = []
    idx = 0
    for seg in segments:
        start = float(seg["start"])
        seg_dur = float(seg["seg_dur"])
        cues = split_into_cues(seg["text"])
        total_chars = sum(len(c) for c in cues)
        t = start
        for c in cues:
            share = seg_dur * (len(c) / total_chars) if total_chars else seg_dur
            end = t + share
            idx += 1
            text = split_long_line(c)
            lines.append(str(idx))
            lines.append(f"{fmt_time(t)} --> {fmt_time(end)}")
            lines.append(text)
            lines.append("")
            t = end
    SRT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"✓ SRT 生成: {SRT_PATH} · {idx} 个 cue（{len(segments)} 段拆出）")


def gen_ass() -> None:
    """ASS 内置样式 · 1080×1920 画布，PingFang SC 白字黑描边，底部 margin 220。"""
    data = json.loads(TIMING_PATH.read_text(encoding="utf-8"))
    segments = data["segments"]
    header = (
        "[Script Info]\n"
        "ScriptType: v4.00+\n"
        "PlayResX: 1080\n"
        "PlayResY: 1920\n"
        "WrapStyle: 0\n"
        "ScaledBorderAndShadow: yes\n"
        "\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
        "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, "
        "ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
        "Alignment, MarginL, MarginR, MarginV, Encoding\n"
        # PingFang SC · 42pt · 白 &Hf0f5f5& · 描边 &H000000& 粗 3 · Alignment 2（底居中）· MarginV 200
        "Style: VO,PingFang SC,42,&H00f0f5f5,&H00ffffff,&H00000000,&H80000000,"
        "0,0,0,0,100,100,0,0,1,3,0,2,60,60,200,1\n"
        "\n"
        "[Events]\n"
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    )
    events: list[str] = []
    for seg in segments:
        start = float(seg["start"])
        seg_dur = float(seg["seg_dur"])
        cues = split_into_cues(seg["text"])
        total_chars = sum(len(c) for c in cues)
        t = start
        for c in cues:
            share = seg_dur * (len(c) / total_chars) if total_chars else seg_dur
            end = t + share
            text = split_long_line(c).replace("\n", r"\N")
            events.append(
                f"Dialogue: 0,{fmt_time_ass(t)},{fmt_time_ass(end)},VO,,0,0,0,,{text}"
            )
            t = end
    ASS_PATH.write_text(header + "\n".join(events) + "\n", encoding="utf-8")
    print(f"✓ ASS 生成: {ASS_PATH} · {len(segments)} 段")


def burn_subs() -> None:
    # 用 ASS · 样式已内置到文件，subtitles filter 只需路径
    # ASS 文件路径的冒号需转义（filter 语法保留字符）
    ass_escaped = str(ASS_PATH).replace(":", r"\:")
    vf = f"ass='{ass_escaped}'"
    subprocess.run(
        [
            FFMPEG, "-y",
            "-i", str(IN_MP4),
            "-vf", vf,
            "-c:v", "libx264", "-preset", "medium", "-crf", "20",
            "-pix_fmt", "yuv420p",
            "-c:a", "copy",
            str(OUT_MP4),
        ],
        check=True,
    )
    r = subprocess.run(
        [FFPROBE, "-v", "error", "-show_entries", "format=duration",
         "-of", "json", str(OUT_MP4)],
        capture_output=True, text=True,
    )
    total = float(json.loads(r.stdout)["format"]["duration"])
    print(f"✓ v3 生成: {OUT_MP4} · {total:.2f}s")


if __name__ == "__main__":
    print("→ D02 字幕生成 + 烧录")
    gen_srt()
    gen_ass()
    burn_subs()
