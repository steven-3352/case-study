#!/usr/bin/env python3
"""S01 冬夜卧室 · 4 段视频 + VO + BGM + 字幕 → 最终 mp4.

时间轴：
  0.0 - 5.0s   S01 女主叉腰（VO 0.5s 起）
  5.0 - 10.0s  S02 男主掀被（VO 5.5s 起）
  10.0 - 18.0s S03 相拥入睡（VO_a 10.5s / VO_b 15s，中间 3s 沉默）
  18.0 - 24.0s S04 清晨亲吻（VO 20s 起，前 2s 静音）

BGM：从原曲第 40s 截 24s，fade-in/out。
字幕：ASS 硬字幕，思源宋体，底部居中。
用法：
  python3 pipeline/assemble_shortfilm.py
"""
from __future__ import annotations

import logging
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCENE_DIR = ROOT / "tmp" / "shortfilm_memory" / "scenes" / "S01_winter_bedroom"
VIDEO_DIR = SCENE_DIR / "videos"
AUDIO_DIR = SCENE_DIR / "audio"
OUT_DIR = SCENE_DIR / "final"
WORK_DIR = SCENE_DIR / ".work"

BGM_SRC = ROOT / "assets" / "audio" / "hook_pack_01" / "我爱的女孩叫丫头-最终版本.mp3"
BGM_START = 40.0  # 从原曲第 40 秒截
BGM_VOL_DB = -14.0
VO_VOL_DB = 0.0
FADE_IN = 0.5
FADE_OUT = 1.5

# 优先用 ffmpeg-full（含 libass 字幕烧录 · 详见 memory feedback_pipeline-burn-subs）
FFMPEG = shutil.which("/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg") or "ffmpeg"
FFPROBE = shutil.which("/opt/homebrew/opt/ffmpeg-full/bin/ffprobe") or "ffprobe"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("shortfilm.assemble")


@dataclass(frozen=True)
class SceneClip:
    slug: str
    duration: float  # 用户设定的视频秒数（Grok 生成时定的）


CLIPS: tuple[SceneClip, ...] = (
    SceneClip("S01_fake_angry", 5.0),
    SceneClip("S02_quilt_invite", 5.0),
    SceneClip("S03_sleep_hug", 8.0),
    SceneClip("S04_morning_kiss", 6.0),
)


@dataclass(frozen=True)
class VOEvent:
    audio_file: Path
    start_sec: float
    text: str


def get_vo_events() -> tuple[VOEvent, ...]:
    """每段 VO 的绝对起始时间（相对于最终视频 0s）."""
    return (
        VOEvent(AUDIO_DIR / "S01_female.mp3", 0.5, "哎呀，你不开空调，是要冻死熊熊啊？"),
        VOEvent(AUDIO_DIR / "S02_male.mp3", 5.5, "过来，我给你暖着。"),
        VOEvent(AUDIO_DIR / "S03a_female.mp3", 10.5, "真暖和……"),
        VOEvent(AUDIO_DIR / "S03b_male.mp3", 15.0, "睡吧。"),
        VOEvent(AUDIO_DIR / "S04_male.mp3", 20.0, "我走了，再睡会儿。"),
    )


def total_duration() -> float:
    return sum(c.duration for c in CLIPS)


def ffprobe_duration(path: Path) -> float:
    out = subprocess.check_output(
        [
            FFPROBE,
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        text=True,
    ).strip()
    return float(out)


def check_inputs() -> None:
    missing: list[Path] = []
    for c in CLIPS:
        p = VIDEO_DIR / f"{c.slug}.mp4"
        if not p.exists():
            missing.append(p)
    for ev in get_vo_events():
        if not ev.audio_file.exists():
            missing.append(ev.audio_file)
    if not BGM_SRC.exists():
        missing.append(BGM_SRC)
    if missing:
        log.error("缺资产：")
        for m in missing:
            log.error("  - %s", m)
        sys.exit(2)


def concat_videos(out_path: Path) -> None:
    """concat demuxer 拼 4 段视频（去除各段原音轨）."""
    list_file = WORK_DIR / "concat.txt"
    lines = [f"file '{(VIDEO_DIR / (c.slug + '.mp4')).as_posix()}'" for c in CLIPS]
    list_file.write_text("\n".join(lines), encoding="utf-8")

    cmd = [
        FFMPEG,
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(list_file),
        "-c:v",
        "copy",
        "-an",  # 剥离原始音轨
        str(out_path),
    ]
    log.info("concat videos → %s", out_path.name)
    subprocess.check_call(cmd)


def build_ass_subtitle(out_path: Path) -> None:
    """字幕 ASS，底部居中大字，思源宋 + 白字黑描边."""
    events = get_vo_events()
    header = """[Script Info]
Title: 短片《回忆·思念》 S01 字幕
ScriptType: v4.00+
PlayResX: 720
PlayResY: 1280
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Source Han Serif SC,48,&H00FFFFFF,&H000000FF,&H80000000,&H80000000,-1,0,0,0,100,100,0,0,1,3,2,2,60,60,90,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    def fmt(sec: float) -> str:
        h = int(sec // 3600)
        m = int((sec % 3600) // 60)
        s = sec % 60
        return f"{h:d}:{m:02d}:{s:05.2f}"

    lines: list[str] = [header]
    for ev in events:
        try:
            dur = ffprobe_duration(ev.audio_file)
        except Exception:
            dur = max(2.0, len(ev.text) * 0.28)
        start = ev.start_sec
        end = start + dur + 0.3  # 尾部多留 0.3s
        text = ev.text.replace(",", "，").replace(".", "。")
        lines.append(f"Dialogue: 0,{fmt(start)},{fmt(end)},Default,,0,0,0,,{text}")

    out_path.write_text("\n".join(lines), encoding="utf-8")
    log.info("ASS 字幕 → %s", out_path.name)


def mix_audio(out_audio: Path, total_dur: float) -> None:
    """混音：BGM (截段, fade, 音量) + 5 条 VO (各自 delay + 音量)."""
    events = get_vo_events()

    inputs: list[str] = [
        "-ss",
        f"{BGM_START:.2f}",
        "-t",
        f"{total_dur + 0.5:.2f}",
        "-i",
        str(BGM_SRC),
    ]
    for ev in events:
        inputs.extend(["-i", str(ev.audio_file)])

    # 滤镜图
    # [0:a] BGM: volume + fade
    filter_parts: list[str] = [
        f"[0:a]volume={BGM_VOL_DB}dB,"
        f"afade=t=in:st=0:d={FADE_IN},"
        f"afade=t=out:st={total_dur - FADE_OUT:.2f}:d={FADE_OUT}[bgm]"
    ]
    # 每条 VO：delay + volume
    for i, ev in enumerate(events, start=1):
        delay_ms = int(ev.start_sec * 1000)
        filter_parts.append(
            f"[{i}:a]adelay={delay_ms}|{delay_ms},volume={VO_VOL_DB}dB[vo{i}]"
        )
    # 混合所有轨
    mix_labels = "[bgm]" + "".join(f"[vo{i}]" for i in range(1, len(events) + 1))
    filter_parts.append(
        f"{mix_labels}amix=inputs={len(events) + 1}:duration=first:dropout_transition=0,"
        f"loudnorm=I=-16:LRA=11:TP=-1.5[out]"
    )
    filter_complex = ";".join(filter_parts)

    cmd = [
        FFMPEG,
        "-y",
        *inputs,
        "-filter_complex",
        filter_complex,
        "-map",
        "[out]",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-t",
        f"{total_dur:.2f}",
        str(out_audio),
    ]
    log.info("mix audio → %s", out_audio.name)
    subprocess.check_call(cmd)


def mux_final(
    concat_video: Path, mixed_audio: Path, ass_subs: Path, out_path: Path
) -> None:
    """把混好的音轨 + 硬字幕烧进 concat 后的视频."""
    escaped = ass_subs.as_posix().replace(":", r"\:")
    cmd = [
        FFMPEG,
        "-y",
        "-i",
        str(concat_video),
        "-i",
        str(mixed_audio),
        "-filter_complex",
        f"[0:v]subtitles={escaped}[v]",
        "-map",
        "[v]",
        "-map",
        "1:a",
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-crf",
        "18",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-pix_fmt",
        "yuv420p",
        "-shortest",
        str(out_path),
    ]
    log.info("mux final → %s", out_path.name)
    subprocess.check_call(cmd)


def main() -> int:
    check_inputs()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    WORK_DIR.mkdir(parents=True, exist_ok=True)

    total = total_duration()
    log.info("总时长 %.2fs · BGM 截 %ss 起 · %d 段", total, BGM_START, len(CLIPS))

    concat_video = WORK_DIR / "concat.mp4"
    mixed_audio = WORK_DIR / "mixed.m4a"
    ass_subs = WORK_DIR / "subs.ass"
    final = OUT_DIR / "S01_winter_bedroom_final.mp4"

    concat_videos(concat_video)
    build_ass_subtitle(ass_subs)
    mix_audio(mixed_audio, total)
    mux_final(concat_video, mixed_audio, ass_subs, final)

    log.info("✓ 完成: %s", final)
    return 0


if __name__ == "__main__":
    sys.exit(main())
