#!/usr/bin/env python3
"""W28D02 三平台 mp4 直出 · 无剪映交接单.

背景：pipeline 直接落盘 douyin/xhs/weixin 三份 mp4，不再走剪映。
- VO 主字幕：从 seg_timing_w28d02.json 精确对齐（复用 gen_subs 的 tokenize/pack）
- M3 三连快切 大字（6.80-8.80s，唯一 pipeline 端需 drawtext 的）
- M2 时间锚（18:55·周五）→ 已在 01_iphone_lockscreen_1855.png 里
- M8 CTA（评论你的岗位/按行业发一版）→ 已在 12_cta_note.png 里
- 三平台差异：字号（抖音 42 / 小红书 50 / 视频号 42）；时长同为 68.5s

依据 memory: feedback_pipeline-burn-subs · CLAUDE.md 铁律「pipeline 直出，剪映零手操」。
"""
from __future__ import annotations

import json
import pathlib
import subprocess
from dataclasses import dataclass

from gen_subs_w28d02 import fmt_time_ass, split_into_cues, split_long_line

ROOT = pathlib.Path(__file__).resolve().parents[2]
D02 = ROOT / "publish" / "2026-W28" / "D02-打工人5分钟出周报"
BUILD = D02 / "build"
AUDIO = BUILD / "audio"
FINAL = BUILD / "final"

# ffmpeg-full 才带 libass/libfreetype/fontconfig；系统 brew ffmpeg 精简版没编
FFMPEG = "/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg"
FFPROBE = "/opt/homebrew/opt/ffmpeg-full/bin/ffprobe"

# 中文字体（PingFang.ttc 是 TTC；drawtext 用 fontfile 直接指向，face 默认 0=常规体）
FONT_PINGFANG = "/System/Library/Fonts/PingFang.ttc"

TIMING_PATH = AUDIO / "seg_timing_w28d02.json"
IN_MP4 = FINAL / "preview_no_bgm_v2.mp4"  # 无 VO 字幕的底片


@dataclass(frozen=True)
class PlatformSpec:
    name: str            # douyin / xhs / weixin
    subs_size: int       # VO 字幕字号
    margin_v: int        # 字幕底 margin
    max_cue_chars: int   # 单 cue 最大字数（字号大要给短点）
    max_line_chars: int  # 单行折行阈值


PLATFORMS: tuple[PlatformSpec, ...] = (
    # 抖音：紧字幕 · 42pt · 底 200 · 单 cue ≤32 · 单行 ≤17
    PlatformSpec(name="douyin", subs_size=42, margin_v=200, max_cue_chars=32, max_line_chars=17),
    # 小红书：滑动阅读 · 字幕 +8pt = 50pt · 底 220 · 因字号大所以收紧
    PlatformSpec(name="xhs", subs_size=50, margin_v=220, max_cue_chars=26, max_line_chars=14),
    # 视频号：与抖音同规
    PlatformSpec(name="weixin", subs_size=42, margin_v=200, max_cue_chars=32, max_line_chars=17),
)


# ── M3 三连快切时序（对齐 storyboard.yaml 与 retention_beat_sheet.md）───────
M3_SHOTS: tuple[tuple[str, float, float], ...] = (
    ("没得写",     6.80, 7.40),
    ("写不出",     7.45, 8.05),
    ("占私人时间", 8.10, 8.70),
)
# 白闪时段（0.05s 满屏白）
M3_FLASHES: tuple[tuple[float, float], ...] = (
    (7.40, 7.45),
    (8.05, 8.10),
)
M3_FONTSIZE = 96
M3_COLOR = "white"
M3_BORDER_COLOR = "black"
M3_BORDER_W = 5


def gen_platform_ass(spec: PlatformSpec) -> pathlib.Path:
    """生成平台专属 ASS（字号/margin 差异化）· 落盘到 build/final/vo_w28d02_<platform>.ass."""
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
        # PingFang SC · <size>pt · 白 &Hf0f5f5& · 描边 &H000000& 粗 3 · Alignment 2（底居中）
        f"Style: VO,PingFang SC,{spec.subs_size},&H00f0f5f5,&H00ffffff,&H00000000,&H80000000,"
        f"0,0,0,0,100,100,0,0,1,3,0,2,60,60,{spec.margin_v},1\n"
        "\n"
        "[Events]\n"
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    )
    events: list[str] = []
    for seg in segments:
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
    ass_path = FINAL / f"vo_w28d02_{spec.name}.ass"
    ass_path.write_text(header + "\n".join(events) + "\n", encoding="utf-8")
    return ass_path


def build_filter_chain(ass_path: pathlib.Path) -> str:
    """组 -vf filter 链：ass 字幕 → 白闪 drawbox → M3 三段 drawtext."""
    ass_escaped = str(ass_path).replace(":", r"\:")
    parts: list[str] = [f"ass='{ass_escaped}'"]

    # 白闪：满屏白 · 0.05s（每次快切间隔）
    for t0, t1 in M3_FLASHES:
        parts.append(
            f"drawbox=x=0:y=0:w=1080:h=1920:color=white@1.0:t=fill:"
            f"enable='between(t,{t0:.2f},{t1:.2f})'"
        )

    # M3 大字：96pt 白字黑描边 · 屏幕中心
    for text, t0, t1 in M3_SHOTS:
        parts.append(
            f"drawtext=fontfile='{FONT_PINGFANG}':"
            f"text='{text}':"
            f"fontsize={M3_FONTSIZE}:fontcolor={M3_COLOR}:"
            f"borderw={M3_BORDER_W}:bordercolor={M3_BORDER_COLOR}:"
            f"x=(w-text_w)/2:y=(h-text_h)/2:"
            f"enable='between(t,{t0:.2f},{t1:.2f})'"
        )

    return ",".join(parts)


def render_platform(spec: PlatformSpec) -> pathlib.Path:
    """跑一个平台：出 ass → 走 ffmpeg → 落盘 <platform>/video.mp4."""
    ass_path = gen_platform_ass(spec)
    vf = build_filter_chain(ass_path)

    out_dir = D02 / spec.name
    out_dir.mkdir(parents=True, exist_ok=True)
    out_mp4 = out_dir / "video.mp4"

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
    print("→ D02 三平台 mp4 直出（pipeline 端一键，无剪映）")
    print(f"  底片: {IN_MP4.name}")
    for spec in PLATFORMS:
        render_platform(spec)
    print("\n✓ 完成 · 三平台 mp4 已落盘：")
    print(f"  抖音   → publish/2026-W28/D02-*/douyin/video.mp4")
    print(f"  小红书 → publish/2026-W28/D02-*/xhs/video.mp4")
    print(f"  视频号 → publish/2026-W28/D02-*/weixin/video.mp4")


if __name__ == "__main__":
    main()
