#!/usr/bin/env python3
"""W28D03 三平台 mp4 直出 · pipeline 端一键，剪映零手操.

- VO 主字幕：从 seg_timing_w28d03.json 精确对齐（复用 gen_subs 的 tokenize/pack）
- 三平台字号差异（抖音 42 / 小红书 50 / 视频号 42）
- 大字覆盖直接由 UI PNG（drawtext 只用于极简大字如 23:12 时间戳、白闪快切）
- BGM off · 密 VO 演示型默认无 BGM · 外发命名 video_no_bgm.mp4

依据 memory: feedback_pipeline-burn-subs · feedback_pipeline-full-platform-output ·
    feedback_dense-vo-no-bgm-default · CLAUDE.md 铁律「pipeline 直出，剪映零手操」。

前置依赖（未生成时给出提示，不 hard fail）：
  - build/final/preview_no_bgm_v2.mp4（底片 · 由 build_w28d03_preview.py 拼合）
  - build/audio/seg_timing_w28d03.json（VO 分段 · 由 gen_vo_w28d03.py 生成）
"""
from __future__ import annotations

import json
import pathlib
import subprocess
from dataclasses import dataclass

from gen_subs_w28d02 import fmt_time_ass, split_into_cues, split_long_line

ROOT = pathlib.Path(__file__).resolve().parents[2]
D03 = ROOT / "publish" / "2026-W28" / "D03-AI陪练英语口语"
BUILD = D03 / "build"
AUDIO = BUILD / "audio"
FINAL = BUILD / "final"
FINAL.mkdir(parents=True, exist_ok=True)

FFMPEG = "/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg"
FFPROBE = "/opt/homebrew/opt/ffmpeg-full/bin/ffprobe"

FONT_PINGFANG = "/System/Library/Fonts/PingFang.ttc"
FONT_SFMONO = "/System/Library/Fonts/SFNSMono.ttf"

TIMING_PATH = AUDIO / "seg_timing_w28d03.json"
IN_MP4 = FINAL / "preview_no_bgm_v2.mp4"

# M7 段位跳过字幕（真英文对话音 · 屏录字幕自带）
SKIP_EMOTIONS = {"silence", "gap"}


@dataclass(frozen=True)
class PlatformSpec:
    name: str            # douyin / xhs / weixin
    subs_size: int       # VO 字幕字号
    margin_v: int        # 字幕底 margin
    max_cue_chars: int   # 单 cue 最大字数（字号大要给短点）
    max_line_chars: int  # 单行折行阈值


PLATFORMS: tuple[PlatformSpec, ...] = (
    PlatformSpec(name="douyin", subs_size=42, margin_v=200, max_cue_chars=32, max_line_chars=17),
    PlatformSpec(name="xhs", subs_size=50, margin_v=220, max_cue_chars=26, max_line_chars=14),
    PlatformSpec(name="weixin", subs_size=42, margin_v=200, max_cue_chars=32, max_line_chars=17),
)


# ── M1 时间戳「23:12·又一次决心学英语」大字（2-3s 处淡入）─────
M1_TIME_TAG: tuple[str, float, float] = ("23:12 · 又一次决心学英语", 2.0, 3.0)


def _escape_drawtext(text: str) -> str:
    """drawtext text= 需转义特殊字符（冒号、引号、百分号）。"""
    return (
        text.replace("\\", "\\\\")
            .replace(":", "\\:")
            .replace("'", "’")
            .replace("%", "\\%")
    )


def gen_platform_ass(spec: PlatformSpec) -> pathlib.Path:
    """生成平台专属 ASS（字号/margin 差异化）· 落盘到 build/final/vo_w28d03_<platform>.ass."""
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
        f"Style: VO,PingFang SC,{spec.subs_size},&H00f0f5f5,&H00ffffff,&H00000000,&H80000000,"
        f"0,0,0,0,100,100,0,0,1,3,0,2,60,60,{spec.margin_v},1\n"
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
        cues = split_into_cues(seg["text"], max_cue_chars=spec.max_cue_chars)
        total_chars = sum(len(c) for c in cues)
        t = start
        for c in cues:
            share = seg_dur * (len(c) / total_chars) if total_chars else seg_dur
            end = t + share
            text = split_long_line(c, max_chars=spec.max_line_chars).replace("\n", r"\N")
            events.append(
                f"Dialogue: 0,{fmt_time_ass(t)},{fmt_time_ass(end)},VO,,0,0,0,,{text}"
            )
            t = end
    ass_path = FINAL / f"vo_w28d03_{spec.name}.ass"
    ass_path.write_text(header + "\n".join(events) + "\n", encoding="utf-8")
    return ass_path


def build_filter_chain(ass_path: pathlib.Path) -> str:
    """组 -vf filter 链：ass 字幕 + M1 3s 处时间戳大字."""
    ass_escaped = str(ass_path).replace(":", r"\:")
    parts: list[str] = [f"ass='{ass_escaped}'"]

    # M1 时间戳大字（3s 处入 · 140pt 白字黑描边）
    text, t0, t1 = M1_TIME_TAG
    parts.append(
        f"drawtext=fontfile='{FONT_PINGFANG}':"
        f"text='{_escape_drawtext(text)}':"
        f"fontsize=64:fontcolor=white:"
        f"borderw=4:bordercolor=black:"
        f"x=(w-text_w)/2:y=h-500:"
        f"enable='between(t,{t0:.2f},{t1:.2f})'"
    )

    return ",".join(parts)


def render_platform(spec: PlatformSpec) -> pathlib.Path | None:
    """跑一个平台：出 ass → 走 ffmpeg → 落盘 <platform>/video_no_bgm.mp4."""
    if not IN_MP4.exists():
        print(f"⚠ 底片未生成: {IN_MP4}")
        print(f"  请先跑 build_w28d03_preview.py 拼合底片（Pexels B-roll + UI PNG + 真机屏录）")
        return None
    if not TIMING_PATH.exists():
        print(f"⚠ VO 时间线未生成: {TIMING_PATH}")
        print(f"  请先跑 gen_vo_w28d03.py 生成 VO 与 seg_timing_w28d03.json")
        return None

    ass_path = gen_platform_ass(spec)
    vf = build_filter_chain(ass_path)

    out_dir = D03 / spec.name
    out_dir.mkdir(parents=True, exist_ok=True)
    out_mp4 = out_dir / "video_no_bgm.mp4"

    subprocess.run(
        [
            FFMPEG, "-y",
            "-i", str(IN_MP4),
            "-vf", vf,
            "-c:v", "libx264", "-preset", "medium", "-crf", "20",
            "-pix_fmt", "yuv420p",
            "-c:a", "copy",
            str(out_mp4),
        ],
        check=True,
    )
    r = subprocess.run(
        [FFPROBE, "-v", "error", "-show_entries", "format=duration",
         "-of", "json", str(out_mp4)],
        capture_output=True, text=True, check=True,
    )
    dur = float(json.loads(r.stdout)["format"]["duration"])
    size_mb = out_mp4.stat().st_size / (1024 * 1024)
    print(f"✓ {spec.name:<7} · {dur:5.2f}s · {size_mb:5.1f} MB · {out_mp4}")
    return out_mp4


def main() -> None:
    print("→ D03 三平台 mp4 直出（pipeline 端一键，无剪映）")
    print(f"  底片: {IN_MP4.name}")
    for spec in PLATFORMS:
        render_platform(spec)
    print("\n✓ 完成 · 三平台 mp4 已落盘：")
    print(f"  抖音   → publish/2026-W28/D03-*/douyin/video_no_bgm.mp4")
    print(f"  小红书 → publish/2026-W28/D03-*/xhs/video_no_bgm.mp4")
    print(f"  视频号 → publish/2026-W28/D03-*/weixin/video_no_bgm.mp4")


if __name__ == "__main__":
    main()
