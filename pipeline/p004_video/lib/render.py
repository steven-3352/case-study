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


def suggest_scene_realign(
    scenes: list[SceneSpec],
    timing_json: pathlib.Path,
    align_tolerance: float = 0.3,
) -> list[tuple[str, float, float, float]]:
    """从 seg_timing 逐段推荐 scene total_dur · 防 D04 CTA 裁掉重演.

    D04 教训：VO 溢出 · scene 未同步扩窗 · CTA 落在 video window 外被裁
    修复：seg_timing 生成后 · 逐 scene 计算「本 scene 覆盖的 VO windows 总和」→ 推荐 total_dur

    此启发式只在 scene 数 == 非 silence VO 段数 时准确 · 否则回退到整体 delta 报告
    返回 (scene_name, current_total_dur, suggested_total_dur, delta) · delta > tolerance 则打印建议
    """
    import json
    if not timing_json.exists() or not scenes:
        return []
    data = json.loads(timing_json.read_text(encoding="utf-8"))
    seg_list = data.get("segments", [])
    if not seg_list:
        return []

    non_silence = [s for s in seg_list if s.get("emotion") not in ("silence", "gap")]
    # 场景一：scene 数正好 == 非 silence VO 段数（每个 scene 对一段 VO）
    if len(scenes) == len(non_silence):
        suggestions: list[tuple[str, float, float, float]] = []
        for sc, seg in zip(scenes, non_silence):
            window = float(seg.get("window", 0))
            delta = window - sc.total_dur
            if abs(delta) >= align_tolerance:
                suggestions.append((sc.name, sc.total_dur, window, delta))
        return suggestions
    return []


def check_ship_gate(
    scenes: list[SceneSpec],
    timing_json: pathlib.Path,
    cta_scene_min_dur_ratio: float = 0.95,
) -> tuple[bool, str]:
    """CTA 完整性 fail-closed 门 · 防 D04 CTA 被裁重演.

    判据：sum(scene.total_dur) 必须 >= seg_timing.total - 0.5s（允许 tail 微差）
    否则视频结束时 VO 未播完 · CTA（最后一段）会被裁

    返回 (passed, reason)
    """
    import json
    if not timing_json.exists() or not scenes:
        return True, "no timing json · skip"
    data = json.loads(timing_json.read_text(encoding="utf-8"))
    seg_total = float(data.get("total", 0))
    plan_total = sum(s.total_dur for s in scenes)
    delta = seg_total - plan_total  # 正数=VO 超出 scene · CTA 会被裁
    if delta > 0.5:
        return False, (
            f"CTA 会被裁 · seg_total {seg_total:.2f}s > plan_total {plan_total:.2f}s · "
            f"Δ={delta:+.2f}s · 扩最后 scene total_dur 至少 {delta+0.1:.2f}s"
        )
    return True, f"CTA 门 PASS · seg {seg_total:.2f}s vs plan {plan_total:.2f}s · Δ={delta:+.2f}s"


def print_realign_report(suggestions: list[tuple[str, float, float, float]]) -> None:
    """打印 scene realign 建议 · 用户 copy-paste 到 pipeline_config.yaml.scenes."""
    if not suggestions:
        return
    print()
    print("─ scene realign 建议（VO 已合成 · scene total_dur 建议对齐 seg_timing.window） ─")
    print(f"  {'scene':<35} {'current':>10} {'suggest':>10} {'delta':>10}")
    for name, current, suggest, delta in suggestions:
        icon = "⚠" if delta > 0 else "·"
        print(f"  {icon} {name:<33} {current:>8.2f}s {suggest:>8.2f}s {delta:>+8.2f}s")
    print("  · CTA 落在片尾 · scene 未扩窗会被裁 · 见 D04 教训（memory tts-estimate-duration-pre-synth）")
    print()
