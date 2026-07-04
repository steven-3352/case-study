#!/usr/bin/env python3
"""W28D03 字幕生成 + 烧录 · 从 seg_timing_w28d03.json 出 .srt/.ass 并烧进 mp4.

复用 gen_subs_w28d02 的 tokenize/pack 工具。
输出：
- build/final/vo_w28d03.srt（标准 srt · 剪映/PR/DaVinci 均可导入）
- build/final/vo_w28d03.ass（1080×1920 · PingFang SC 42pt 白字黑描边）
- build/final/preview_no_bgm_subs_v3.mp4（v2 上烧 VO 主字幕）

memory feedback_pipeline-burn-subs · 系统 ffmpeg 无 libass 用 /opt/homebrew/opt/ffmpeg-full/bin/ffmpeg。
"""
from __future__ import annotations

import json
import pathlib
import subprocess

from gen_subs_w28d02 import (
    fmt_time, fmt_time_ass, split_into_cues, split_long_line,
)

ROOT = pathlib.Path(__file__).resolve().parents[2]
D03 = ROOT / "publish" / "2026-W28" / "D03-AI陪练英语口语"
BUILD = D03 / "build"
AUDIO = BUILD / "audio"
FINAL = BUILD / "final"
FINAL.mkdir(parents=True, exist_ok=True)

FFMPEG = "/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg"
FFPROBE = "/opt/homebrew/opt/ffmpeg-full/bin/ffprobe"

TIMING_PATH = AUDIO / "seg_timing_w28d03.json"
SRT_PATH = FINAL / "vo_w28d03.srt"
ASS_PATH = FINAL / "vo_w28d03.ass"
IN_MP4 = FINAL / "preview_no_bgm_v2.mp4"
OUT_MP4 = FINAL / "preview_no_bgm_subs_v3.mp4"

# 段位标记：'silence' / 'gap' 不生成字幕（M1 沉默钉子 · M7 真对话音）
SKIP_EMOTIONS = {"silence", "gap"}


def gen_srt() -> None:
    data = json.loads(TIMING_PATH.read_text(encoding="utf-8"))
    segments = data["segments"]
    lines: list[str] = []
    idx = 0
    for seg in segments:
        if seg.get("emotion") in SKIP_EMOTIONS:
            continue
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
    print(f"✓ SRT 生成: {SRT_PATH} · {idx} 个 cue（{len(segments)} 段 · 跳过 silence/gap）")


def gen_ass() -> None:
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
        if seg.get("emotion") in SKIP_EMOTIONS:
            continue
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
    print(f"✓ ASS 生成: {ASS_PATH} · {len(events)} 个事件")


def burn_subs() -> None:
    if not IN_MP4.exists():
        print(f"⚠ 底片未生成: {IN_MP4} · 跳过烧录（build_platforms_w28d03 会直接烧到平台版）")
        return
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
    print("→ D03 字幕生成 + 烧录")
    gen_srt()
    gen_ass()
    burn_subs()
