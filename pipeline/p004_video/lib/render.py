"""视频渲染 · UI PNG / B-roll → clip → concat → 挂 VO.

从 build_w28d02/03_preview 抽取；避免 to_clip 里 dict-in-list `"-vf": None` bug.
"""
from __future__ import annotations

import pathlib
from dataclasses import dataclass, field
from typing import Literal

from .ffmpeg import FFMPEG, dur, run

W = 1080
H = 1920
FPS = 30

SrcType = Literal["img", "broll"]


@dataclass(frozen=True)
class ClipSpec:
    """一个 sub-clip · 分镜内一个视觉源.

    src_type=img: 静帧 PNG 循环 · 用于 UI PNG
    src_type=broll: B-roll mp4 · 用于 Pexels 实拍/真机屏录
    """
    src_type: SrcType
    src: pathlib.Path
    duration: float


@dataclass(frozen=True)
class SceneSpec:
    """一段 M-scene · 若干 clip 顺序拼合成 total_dur."""
    name: str
    clips: tuple[ClipSpec, ...]
    total_dur: float


def _run_img_clip(idx: int, src: pathlib.Path, duration: float, clips_dir: pathlib.Path) -> pathlib.Path:
    out = clips_dir / f"c{idx:02d}.mp4"
    vf = (
        f"scale={W}:{H}:force_original_aspect_ratio=decrease,"
        f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:color=black,"
        f"setsar=1,fps={FPS}"
    )
    run([
        FFMPEG, "-y",
        "-loop", "1", "-i", str(src),
        "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
        "-t", f"{duration}",
        "-vf", vf,
        "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k",
        "-shortest",
        str(out),
    ])
    return out


def _run_broll_clip(idx: int, src: pathlib.Path, duration: float, clips_dir: pathlib.Path) -> pathlib.Path:
    out = clips_dir / f"c{idx:02d}.mp4"
    vf = (
        f"scale={W}:{H}:force_original_aspect_ratio=increase,"
        f"crop={W}:{H},setsar=1,fps={FPS}"
    )
    run([
        FFMPEG, "-y",
        "-ss", "0", "-t", f"{duration}", "-i", str(src),
        "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
        "-t", f"{duration}",
        "-vf", vf,
        "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k",
        "-map", "0:v", "-map", "1:a",
        "-shortest",
        str(out),
    ])
    return out


def build_sub_clip(
    idx: int,
    clip: ClipSpec,
    clips_dir: pathlib.Path,
) -> pathlib.Path:
    """一个 clip → mp4；缺素材直接抛."""
    if not clip.src.exists():
        raise FileNotFoundError(f"素材缺失: {clip.src}")
    if clip.src_type == "img":
        return _run_img_clip(idx, clip.src, clip.duration, clips_dir)
    return _run_broll_clip(idx, clip.src, clip.duration, clips_dir)


def concat_video_only(
    scenes: list[SceneSpec],
    clips_dir: pathlib.Path,
    out_path: pathlib.Path,
) -> pathlib.Path:
    """遍历 scenes → 每个 clip 出 mp4 → concat → 无声视频轨."""
    clips_dir.mkdir(parents=True, exist_ok=True)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    all_clips: list[pathlib.Path] = []
    idx = 0
    for scene in scenes:
        for clip in scene.clips:
            all_clips.append(build_sub_clip(idx, clip, clips_dir))
            idx += 1

    listf = clips_dir / "concat.txt"
    listf.write_text("".join(f"file '{c}'\n" for c in all_clips))
    run([
        FFMPEG, "-y",
        "-f", "concat", "-safe", "0", "-i", str(listf),
        "-c", "copy",
        str(out_path),
    ])
    return out_path


def normalize_vo(vo_in: pathlib.Path, out: pathlib.Path) -> pathlib.Path:
    """VO 响度归一化 · loudnorm -16 dB · TP -1.5 · LRA 11."""
    run([
        FFMPEG, "-y",
        "-i", str(vo_in),
        "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
        "-ar", "48000",
        str(out),
    ])
    return out


def attach_vo(
    video_only: pathlib.Path,
    vo: pathlib.Path,
    out_path: pathlib.Path,
) -> pathlib.Path:
    """无声视频轨 + VO → 底片 · 视频 -c copy · 音频 aac 192k."""
    run([
        FFMPEG, "-y",
        "-i", str(video_only),
        "-i", str(vo),
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k",
        "-map", "0:v:0", "-map", "1:a:0",
        "-shortest",
        str(out_path),
    ])
    return out_path


def sanity_check_timing(
    scenes: list[SceneSpec],
    timing_json: pathlib.Path,
) -> tuple[float, float, float]:
    """比对 seg_timing.total 与 scenes 总长；返回 (seg_total, plan_total, delta)."""
    import json
    if not timing_json.exists():
        return (0.0, sum(s.total_dur for s in scenes), 0.0)
    data = json.loads(timing_json.read_text(encoding="utf-8"))
    seg_total = float(data.get("total", 0))
    plan_total = sum(s.total_dur for s in scenes)
    return (seg_total, plan_total, abs(seg_total - plan_total))
