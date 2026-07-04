"""VO 合成 · 分段 → apad(whole_dur) → concat → loudnorm.

D03 教训（memory feedback_dense-vo-no-dead-air）修正内建：
- apad=whole_dur=<窗口>，不用 apad=pad_dur=0.3（后者不能补到目标窗口）
- concat 用 -c:a libmp3lame -ar 24000 -b:a 128k 强制重编码；
  用 -c copy 会丢帧（原生 D03 build bug 已在此修复）
- loudnorm I=-16 TP=-1.5 LRA=11
- 沉默钉子/gap 段生成静音 mp3 供 concat 对齐（emotion=silence/gap 标记）
"""
from __future__ import annotations

import json
import pathlib
import subprocess
from dataclasses import dataclass, field
from typing import Callable

from .ffmpeg import FFMPEG, dur, run


@dataclass(frozen=True)
class VOSegment:
    """一段 VO."""
    sid: str                   # s1_silence / gap_36s / s2 / ...
    target_start: float        # 期望窗口起点
    target_dur: float          # 期望窗口时长
    emotion: str               # neutral / sad / happy / silence / gap
    speed: float               # TTS speed（0 表示不合成 · silence/gap）
    text: str                  # 台词（silence/gap 存说明文本，不合成）
    tail_pad: float = 0.3      # 尾部静音补足（合成后 vo_dur + tail_pad 与 target_dur 取 max）


def _synth_silence(out: pathlib.Path, seconds: float) -> pathlib.Path:
    run([
        FFMPEG, "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono",
        "-t", f"{seconds:.3f}", "-q:a", "9", "-acodec", "libmp3lame", str(out),
    ])
    return out


def _pad_to_window(raw: pathlib.Path, padded: pathlib.Path, window: float) -> pathlib.Path:
    """VO raw → 补足到 window 长度 · apad=whole_dur 保证到目标."""
    run([
        FFMPEG, "-y", "-i", str(raw),
        "-af", f"apad=whole_dur={window:.3f}", "-t", f"{window:.3f}",
        "-ar", "24000", "-b:a", "128k",
        str(padded),
    ])
    return padded


def synthesize_segments(
    segments: list[VOSegment],
    out_dir: pathlib.Path,
    *,
    prefix: str,
    synthesize_text: Callable[[str, pathlib.Path, str, float], str],
) -> tuple[pathlib.Path, list[dict], set[str]]:
    """按 segments 顺序合成 VO 分段 · 处理 silence/gap 静音填充.

    参数:
        prefix: 输出文件名前缀（如 "vo_w29d01"）
        synthesize_text: 回调 (text, out_mp3, emotion, speed) -> engine_name

    返回:
        (concat_list_file, timing_entries, engine_names)
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    padded_paths: list[pathlib.Path] = []
    timing: list[dict] = []
    engines: set[str] = set()
    cum = 0.0

    for seg in segments:
        # target_start > cum → 补 gap 静音
        if seg.target_start > cum + 0.01:
            gap = seg.target_start - cum
            gap_path = out_dir / f"{prefix}_gap_{int(cum)}s.mp3"
            _synth_silence(gap_path, gap)
            padded_paths.append(gap_path)
            timing.append({
                "id": f"gap_{int(cum)}s",
                "window": round(gap, 2), "vo_dur": 0.0,
                "start": round(cum, 2), "seg_dur": round(gap, 2),
                "emotion": "gap", "speed": 0.0,
                "text": f"(gap {int(cum)}-{int(seg.target_start)}s · 填充占位)",
            })
            cum = seg.target_start

        if seg.emotion in ("silence", "gap"):
            silence_path = out_dir / f"{prefix}_{seg.sid}.mp3"
            _synth_silence(silence_path, seg.target_dur)
            padded_paths.append(silence_path)
            timing.append({
                "id": seg.sid,
                "window": round(seg.target_dur, 2), "vo_dur": 0.0,
                "start": round(cum, 2), "seg_dur": round(seg.target_dur, 2),
                "emotion": seg.emotion, "speed": 0.0,
                "text": seg.text,
            })
            cum += seg.target_dur
            continue

        raw = out_dir / f"{prefix}_{seg.sid}_raw.mp3"
        engine = synthesize_text(seg.text, raw, seg.emotion, seg.speed)
        engines.add(engine)
        vo_d = dur(raw)
        window = round(max(vo_d + seg.tail_pad, seg.target_dur), 2)
        padded = out_dir / f"{prefix}_{seg.sid}.mp3"
        _pad_to_window(raw, padded, window)
        padded_paths.append(padded)
        timing.append({
            "id": seg.sid,
            "window": window, "vo_dur": round(vo_d, 2),
            "start": round(cum, 2), "seg_dur": window,
            "emotion": seg.emotion, "speed": seg.speed, "text": seg.text,
        })
        cum += window

    listf = out_dir / f"{prefix}_concat.txt"
    listf.write_text("".join(f"file '{p}'\n" for p in padded_paths))
    return listf, timing, engines


def concat_with_loudnorm(
    listf: pathlib.Path,
    out_dir: pathlib.Path,
    *,
    prefix: str,
) -> pathlib.Path:
    """concat 分段 → loudnorm -16 dB · 内建重编码修复 mp3 concat 丢帧 bug."""
    concat_raw = out_dir / f"{prefix}_concat_raw.mp3"
    run([
        FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", str(listf),
        "-c:a", "libmp3lame", "-ar", "24000", "-b:a", "128k", str(concat_raw),
    ])
    final = out_dir / f"{prefix}.mp3"
    run([
        FFMPEG, "-y", "-i", str(concat_raw),
        "-af", "loudnorm=I=-16:LRA=11:TP=-1.5",
        "-ar", "24000", "-b:a", "128k",
        str(final),
    ])
    return final


def write_timing_json(
    timing: list[dict],
    engines: set[str],
    total: float,
    out_path: pathlib.Path,
) -> pathlib.Path:
    """落盘 seg_timing.json（下游 subs / preview / platforms 消费）."""
    out_path.write_text(
        json.dumps(
            {"engine": sorted(engines), "total": round(total, 2), "segments": timing},
            ensure_ascii=False, indent=2,
        ),
        encoding="utf-8",
    )
    return out_path
