#!/usr/bin/env python3
"""P004 视频总编排 · 把帧序列 + VO + BGM + 字幕合成最终 mp4.

阶段:
  1. per-scene: PNG 序列 → 静音 mp4 (out/scenes/<scene_id>.mp4)
  2. 全片串联: scene mp4 列表 → all_video.mp4 (静音)
  3. 加配音 + BGM + 烧字幕 → out/final/<output_name>

依赖:
  ffmpeg, ffprobe 必须在 PATH

用法:
  python3 pipeline/p004_video/build.py             # 默认全流程
  python3 pipeline/p004_video/build.py --skip-capture   # 已经截过帧,只合成
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass

import yaml

ROOT = pathlib.Path(__file__).resolve().parent
PROJECT_ROOT = ROOT.parent.parent
FRAMES = ROOT / "out" / "frames"
SCENES = ROOT / "out" / "scenes"
AUDIO = ROOT / "out" / "audio"
FINAL = ROOT / "out" / "final"

DEFAULT_BGM = PROJECT_ROOT / "我曾经的丫头.mp3"
DEFAULT_VO = AUDIO / "vo_k1_v2_padded.mp3"
DEFAULT_SUB = ROOT / "sub_k1.srt"


@dataclass(frozen=True)
class SceneSpec:
    id: str
    duration: float
    type: str = "html"          # html | broll
    source: str | None = None   # broll 模式: 源视频路径(相对 PROJECT_ROOT)
    source_in: float = 0.0


def load_storyboard(path: pathlib.Path) -> tuple[dict, list[SceneSpec]]:
    with path.open(encoding="utf-8") as f:
        sb = yaml.safe_load(f)
    scenes = [
        SceneSpec(
            id=s["id"],
            duration=float(s["duration"]),
            type=s.get("type", "html"),
            source=s.get("source"),
            source_in=float(s.get("source_in", 0.0)),
        )
        for s in sb.get("scenes", [])
    ]
    return sb.get("video", {}), scenes


def run(cmd: list[str], stage: str) -> None:
    print(f"  [{stage}] {' '.join(cmd[:3])}...")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(res.stderr[-2000:])
        sys.exit(f"ffmpeg 失败 stage={stage}")


def dur(path: pathlib.Path) -> float:
    res = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "json", str(path)],
        capture_output=True, text=True,
    )
    return float(json.loads(res.stdout)["format"]["duration"])


def scene_to_mp4(scene: SceneSpec, fps: int, width: int, height: int) -> pathlib.Path:
    src = FRAMES / scene.id
    out = SCENES / f"{scene.id}.mp4"
    if not src.exists() or not any(src.glob("frame_*.png")):
        sys.exit(f"找不到帧 {src};先跑 capture_frames.py")
    SCENES.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(fps),
        "-i", str(src / "frame_%04d.png"),
        "-vf", f"scale={width}:{height}:flags=lanczos,format=yuv420p",
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        str(out),
    ]
    run(cmd, f"scene→mp4 {scene.id}")
    return out


def broll_to_mp4(scene: SceneSpec, fps: int, width: int, height: int) -> pathlib.Path:
    """type=broll: 切源视频片段 → 1080x1920 yuv420p,统一为本片 fps."""
    out = SCENES / f"{scene.id}.mp4"
    SCENES.mkdir(parents=True, exist_ok=True)

    if not scene.source:
        sys.exit(f"{scene.id}: broll 模式必须填 source")
    src_path = (PROJECT_ROOT / scene.source).resolve()
    if not src_path.exists():
        sys.exit(
            f"{scene.id}: 找不到源视频 {src_path}\n"
            f"  ↳ 用 fetch_broll.py 拉一条,或手机自拍后放到 {scene.source}"
        )

    # cover 裁剪到 9:16(短边贴齐 → 居中裁) + 强制 yuv420p + 重设 fps
    vf = (
        f"scale={width}:{height}:force_original_aspect_ratio=increase,"
        f"crop={width}:{height},"
        f"fps={fps},format=yuv420p"
    )
    cmd = [
        "ffmpeg", "-y",
        "-ss", f"{scene.source_in:.3f}",
        "-i", str(src_path),
        "-t", f"{scene.duration:.3f}",
        "-an",                              # 静音(BGM/VO 后期合)
        "-vf", vf,
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        str(out),
    ]
    run(cmd, f"broll→mp4 {scene.id}")
    return out


def concat_scenes(scene_mp4s: list[pathlib.Path]) -> pathlib.Path:
    list_txt = SCENES / "concat_list.txt"
    list_txt.write_text("".join(f"file '{p}'\n" for p in scene_mp4s))
    out = SCENES / "all_video.mp4"
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(list_txt),
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        str(out),
    ]
    run(cmd, "concat scenes")
    return out


def compose_final(
    video: pathlib.Path,
    vo: pathlib.Path,
    bgm: pathlib.Path | None,
    subtitle_frames: pathlib.Path | None,
    output: pathlib.Path,
    vo_volume: float,
    bgm_volume: float,
    fps: int,
) -> None:
    """单次 ffmpeg 合成 · 主视频 + 透明字幕 PNG 序列 overlay + VO + BGM.

    避开本机 ffmpeg 8.1 没启 libass/drawtext 的问题。
    """
    video_dur = dur(video)

    inputs: list[str] = ["-i", str(video)]

    # 字幕 PNG 序列输入
    sub_idx = -1
    if subtitle_frames and any(subtitle_frames.glob("frame_*.png")):
        sub_idx = len(inputs) // 2
        inputs += ["-framerate", str(fps), "-i", str(subtitle_frames / "frame_%04d.png")]

    # VO 输入
    vo_idx = len([t for t in inputs if t == "-i"])
    inputs += ["-i", str(vo)]

    # BGM 输入
    bgm_idx = -1
    if bgm and bgm.exists():
        bgm_idx = len([t for t in inputs if t == "-i"])
        inputs += ["-stream_loop", "-1", "-i", str(bgm)]

    # 视频链
    if sub_idx >= 0:
        v_chain = f"[0:v][{sub_idx}:v]overlay=0:0:format=auto[v]"
    else:
        v_chain = "[0:v]copy[v]"

    # 音频链
    if bgm_idx >= 0:
        fade_out_start = max(0.0, video_dur - 2.0)
        a_chain = (
            f"[{vo_idx}:a]volume={vo_volume}[vo];"
            f"[{bgm_idx}:a]volume={bgm_volume},afade=t=in:st=0:d=1.5,"
            f"afade=t=out:st={fade_out_start:.2f}:d=2.0[bgm];"
            f"[vo][bgm]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[a]"
        )
    else:
        a_chain = f"[{vo_idx}:a]volume={vo_volume}[a]"

    filter_complex = f"{v_chain};{a_chain}"

    cmd = [
        "ffmpeg", "-y",
        *inputs,
        "-filter_complex", filter_complex,
        "-map", "[v]", "-map", "[a]",
        "-t", f"{video_dur:.2f}",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-ar", "44100",
        "-movflags", "+faststart",
        str(output),
    ]
    run(cmd, "compose final")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--storyboard", type=pathlib.Path, default=ROOT / "storyboard.yaml")
    ap.add_argument("--skip-capture", action="store_true", help="跳过截帧阶段,直接合成")
    ap.add_argument("--vo", type=pathlib.Path, default=DEFAULT_VO)
    ap.add_argument("--bgm", type=pathlib.Path, default=DEFAULT_BGM)
    ap.add_argument("--no-subtitle", action="store_true")
    args = ap.parse_args()

    sb = args.storyboard.resolve()
    m = re.search(r"W26D0([4-7])", str(sb))
    if m:
        day_map = {
            "4": "D04-复购流失",
            "5": "D05-催票轮回",
            "6": "D06-退货对账",
            "7": "D07-流程断档",
        }
        day_name = day_map.get(m.group(1))
        if day_name:
            day_dir = PROJECT_ROOT / "publish" / "2026-W26" / day_name
            if day_dir.exists():
                sys.path.insert(0, str(PROJECT_ROOT))
                from pipeline.gate_check import assert_paid_work_allowed
                assert_paid_work_allowed(day_dir, operation="P004 build")

    video_cfg, scenes = load_storyboard(sb)
    fps = int(video_cfg.get("fps", 30))
    width = int(video_cfg.get("width", 1080))
    height = int(video_cfg.get("height", 1920))
    output_name = video_cfg.get("output_name", "p004_K1.mp4")
    vo_volume = float(video_cfg.get("voice_volume", 1.0))
    bgm_volume = float(video_cfg.get("music_volume", 0.10))

    # Phase 1: 截帧(可跳过)
    if not args.skip_capture:
        print("Phase 1 · 截帧 (scene + subtitles)")
        cmd = [sys.executable, str(ROOT / "capture_frames.py"), "--all",
               "--storyboard", str(sb)]
        res = subprocess.run(cmd, cwd=str(PROJECT_ROOT))
        if res.returncode != 0:
            sys.exit("scene 截帧失败")
        if not args.no_subtitle:
            total_dur = sum(s.duration for s in scenes)
            cmd2 = [sys.executable, str(ROOT / "capture_frames.py"),
                    "--template", "_subtitles.html",
                    "--duration", f"{total_dur}",
                    "--out-id", "_subtitles",
                    "--transparent"]
            res = subprocess.run(cmd2, cwd=str(PROJECT_ROOT))
            if res.returncode != 0:
                sys.exit("字幕层截帧失败")
    else:
        print("Phase 1 · 截帧 (跳过)")

    # Phase 2: 各 scene → mp4
    print("Phase 2 · scene → mp4")
    scene_mp4s = [
        broll_to_mp4(s, fps, width, height) if s.type == "broll"
        else scene_to_mp4(s, fps, width, height)
        for s in scenes
    ]

    # Phase 3: 串联静音视频
    print("Phase 3 · concat")
    all_video = concat_scenes(scene_mp4s)
    print(f"  静音全片: {dur(all_video):.1f}s @ {all_video}")

    # Phase 4: 合成最终(overlay 字幕 + 混音)
    print("Phase 4 · compose final")
    FINAL.mkdir(parents=True, exist_ok=True)
    output = FINAL / output_name
    sub_frames = None if args.no_subtitle else (FRAMES / "_subtitles")
    if sub_frames and not sub_frames.exists():
        sub_frames = None
    compose_final(
        all_video,
        args.vo,
        args.bgm if args.bgm.exists() else None,
        sub_frames,
        output,
        vo_volume,
        bgm_volume,
        fps,
    )

    print(f"\n✓ 输出: {output}  ({dur(output):.1f}s)")


if __name__ == "__main__":
    main()
