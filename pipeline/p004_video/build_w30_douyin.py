#!/usr/bin/env python3
"""W30 D01/D02 Douyin renderer: locked TTS -> GSAP frames -> MP4.

This renderer is deliberately content-local. It consumes a production YAML whose
scenes map one-to-one to VO segments, then derives scene duration from the real
MiniMax output. Paid work remains guarded by gate_check(pre_render).
"""
from __future__ import annotations

import argparse
import copy
import json
import pathlib
import shutil
import subprocess
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parent
PROJECT_ROOT = ROOT.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from pipeline.gate_check import assert_paid_work_allowed  # noqa: E402
from pipeline.p004_video.lib.ffmpeg import FFMPEG, dur, run  # noqa: E402
from pipeline.p004_video.lib.sfx import mix_sfx_with_vo  # noqa: E402
from pipeline.p004_video.lib.subs import SubStyle, gen_srt  # noqa: E402
from pipeline.p004_video.lib.tts import (  # noqa: E402
    VOSegment,
    concat_with_loudnorm,
    synthesize_segments,
    write_timing_json,
)
from pipeline.tts.gen_speech import synthesize_text  # noqa: E402

SFX_CATALOG = PROJECT_ROOT / "assets" / "sfx" / "catalog.yaml"
MINIMAX_EMOTION_MAP = {
    "serious": "neutral",
}


def load(path: pathlib.Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def content_root(cfg: dict) -> pathlib.Path:
    return PROJECT_ROOT / cfg["paths"]["root_rel"]


def audio_dir(cfg: dict) -> pathlib.Path:
    return content_root(cfg) / "build" / "audio"


def timing_path(cfg: dict) -> pathlib.Path:
    return audio_dir(cfg) / f"seg_timing_{cfg['content_id'].lower()}.json"


def vo_path(cfg: dict) -> pathlib.Path:
    return audio_dir(cfg) / f"vo_{cfg['content_id'].lower()}.mp3"


def write_tts_override(cfg: dict) -> pathlib.Path:
    base = load(PROJECT_ROOT / "pipeline" / "tts" / "config.yaml")
    tts = cfg["tts"]
    base["provider"] = "minimax"
    base["strict_provider"] = True
    base.setdefault("minimax", {})["voice_id"] = tts["voice_id"]
    base["minimax"]["speed"] = float(tts.get("base_speed", 1.06))
    out = audio_dir(cfg) / "tts_config.yaml"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(yaml.safe_dump(base, allow_unicode=True), encoding="utf-8")
    return out


def step_vo(cfg: dict, force: bool) -> None:
    root = content_root(cfg)
    assert_paid_work_allowed(root, operation=f"{cfg['content_id']} MiniMax TTS")
    if vo_path(cfg).exists() and timing_path(cfg).exists() and not force:
        print(f"VO locked: {vo_path(cfg)} ({dur(vo_path(cfg)):.2f}s)")
        return

    tts_cfg = write_tts_override(cfg)
    segments = [
        VOSegment(
            sid=s["sid"],
            target_start=float(s.get("target_start", 0)),
            target_dur=float(s.get("target_dur", 0)),
            emotion=s.get("emotion", "neutral"),
            speed=float(s.get("speed", cfg["tts"].get("base_speed", 1.06))),
            text=s["text"],
            tail_pad=float(s.get("tail_pad", 0.12)),
        )
        for s in cfg["tts"]["segments"]
    ]

    def synth(text: str, out: pathlib.Path, emotion: str, speed: float) -> str:
        api_emotion = MINIMAX_EMOTION_MAP.get(emotion, emotion)
        return synthesize_text(text, out, config_path=tts_cfg, emotion=api_emotion, speed=speed)

    prefix = f"vo_{cfg['content_id'].lower()}"
    listf, timing, engines = synthesize_segments(
        segments, audio_dir(cfg), prefix=prefix, synthesize_text=synth
    )
    if engines != {"minimax"}:
        raise SystemExit(f"Production VO must be MiniMax, got engines={sorted(engines)}")
    final = concat_with_loudnorm(listf, audio_dir(cfg), prefix=prefix)
    write_timing_json(timing, engines, dur(final), timing_path(cfg))
    print(f"VO ready: {final} ({dur(final):.2f}s)")


def step_tts_dry_run(cfg: dict) -> None:
    """Validate the configured provider/voice/emotion with one short sample."""
    tts_cfg = write_tts_override(cfg)
    first = cfg["tts"]["segments"][0]
    texts = [str(segment["text"]) for segment in cfg["tts"]["segments"]]
    sample_text = "".join(texts)
    sample_text = sample_text[:48]
    out = audio_dir(cfg) / "tts_dry_run.mp3"
    engine = synthesize_text(
        sample_text,
        out,
        config_path=tts_cfg,
        emotion=MINIMAX_EMOTION_MAP.get(first.get("emotion", "neutral"), first.get("emotion", "neutral")),
        speed=float(first.get("speed", cfg["tts"].get("base_speed", 1.0))),
    )
    if engine != "minimax":
        raise SystemExit(f"TTS dry-run must use MiniMax, got {engine}")
    print(f"TTS dry-run ready: {out} ({dur(out):.2f}s), engine={engine}")


def runtime_storyboard(cfg: dict) -> pathlib.Path:
    timing = json.loads(timing_path(cfg).read_text(encoding="utf-8"))
    segments = [s for s in timing["segments"] if s.get("emotion") not in ("gap", "silence")]
    scenes = cfg["scenes"]
    if len(segments) != len(scenes):
        raise SystemExit(f"VO/scenes mismatch: {len(segments)} != {len(scenes)}")

    runtime_scenes = []
    for scene, seg in zip(scenes, segments):
        data = dict(scene.get("data") or {})
        data.setdefault("subtitle", seg["text"])
        data["scene_duration"] = float(seg["window"])
        runtime_scenes.append({
            "id": f"{cfg['content_id'].lower()}__{scene['id']}",
            "template": scene["template"],
            "duration": float(seg["window"]),
            "type": "html",
            "data": data,
        })
    sb = {
        "video": {"fps": 30, "width": 1080, "height": 1920},
        "scenes": runtime_scenes,
    }
    out = content_root(cfg) / "build" / "runtime_storyboard.yaml"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(yaml.safe_dump(sb, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return out


def runtime_audio_plan(cfg: dict) -> pathlib.Path:
    root = content_root(cfg)
    source = root / cfg.get("audio_plan_rel", "audio_plan.yaml")
    plan = load(source)
    timing = json.loads(timing_path(cfg).read_text(encoding="utf-8"))
    by_id = {s["id"]: s for s in timing["segments"]}
    runtime = copy.deepcopy(plan)
    for event in (runtime.get("sfx") or {}).get("events") or []:
        if event.get("kind") == "ambient":
            event["duration"] = float(timing["total"])
        scene_sid = event.pop("scene_sid", None)
        if not scene_sid:
            continue
        if scene_sid not in by_id:
            raise SystemExit(f"SFX scene_sid={scene_sid!r} missing from TTS timing")
        start = float(by_id[scene_sid]["start"])
        if "offset_seq" in event:
            event["t_start_seq"] = [start + float(x) for x in event.pop("offset_seq")]
        else:
            event["t_start"] = start + float(event.pop("offset", 0.0))
    out = audio_dir(cfg) / "audio_plan_runtime.yaml"
    out.write_text(yaml.safe_dump(runtime, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return out


def capture(cfg: dict, storyboard: pathlib.Path) -> None:
    cmd = [
        sys.executable,
        str(ROOT / "capture_frames.py"),
        "--all",
        "--storyboard",
        str(storyboard),
        "--workers",
        str(min(4, len(cfg["scenes"]))),
    ]
    subprocess.run(cmd, cwd=PROJECT_ROOT, check=True)


def scene_mp4(cfg: dict, scene: dict, duration: float) -> pathlib.Path:
    frames = ROOT / "out" / "frames" / scene["id"]
    out_dir = content_root(cfg) / "build" / "scenes"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{scene['id']}.mp4"
    run([
        FFMPEG, "-y", "-framerate", "30", "-i", str(frames / "frame_%04d.png"),
        "-t", f"{duration:.3f}", "-vf", "format=yuv420p", "-c:v", "libx264",
        "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
        "-movflags", "+faststart", str(out),
    ])
    return out


def concat_video(cfg: dict, storyboard: pathlib.Path) -> pathlib.Path:
    sb = load(storyboard)
    clips = [scene_mp4(cfg, sc, float(sc["duration"])) for sc in sb["scenes"]]
    out_dir = content_root(cfg) / "build" / "final"
    out_dir.mkdir(parents=True, exist_ok=True)
    listf = out_dir / "scenes.txt"
    listf.write_text("".join(f"file '{p}'\n" for p in clips), encoding="utf-8")
    out = out_dir / "video_only.mp4"
    run([
        FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", str(listf),
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(out),
    ])
    return out


def compose(cfg: dict, video: pathlib.Path) -> pathlib.Path:
    root = content_root(cfg)
    plan = runtime_audio_plan(cfg)
    mixed = audio_dir(cfg) / f"vo_{cfg['content_id'].lower()}_with_sfx.mp3"
    report = mix_sfx_with_vo(
        vo_mp3=vo_path(cfg), audio_plan_yaml=plan, catalog_yaml=SFX_CATALOG,
        out_mp3=mixed, project_root=PROJECT_ROOT,
    )
    if report.gap_events:
        raise SystemExit(f"SFX has {report.gap_events} unresolved events: {report.gap_report_path}")

    out_dir = root / "douyin"
    out_dir.mkdir(parents=True, exist_ok=True)
    publish = out_dir / "video_no_bgm.mp4"
    run([
        FFMPEG, "-y", "-i", str(video), "-i", str(mixed),
        "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-shortest",
        "-movflags", "+faststart", str(publish),
    ])
    canonical = out_dir / "video.mp4"
    shutil.copy2(publish, canonical)
    gen_srt(timing_path(cfg), out_dir / "subtitles.srt", style=SubStyle(max_cue_chars=24, max_line_chars=13))
    run([
        FFMPEG, "-y", "-ss", "1.0", "-i", str(canonical), "-frames:v", "1",
        str(out_dir / "cover.png"),
    ])
    print(f"Final: {canonical} ({dur(canonical):.2f}s), SFX={report.used_events}")
    return canonical


def step_render(cfg: dict) -> None:
    root = content_root(cfg)
    assert_paid_work_allowed(root, operation=f"{cfg['content_id']} render")
    if not timing_path(cfg).exists():
        raise SystemExit("Run --step vo first")
    sb = runtime_storyboard(cfg)
    capture(cfg, sb)
    compose(cfg, concat_video(cfg, sb))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True, type=pathlib.Path)
    ap.add_argument("--step", choices=("tts-dry-run", "vo", "render", "all"), default="all")
    ap.add_argument("--force-vo", action="store_true")
    args = ap.parse_args()
    cfg_path = args.config if args.config.is_absolute() else PROJECT_ROOT / args.config
    cfg = load(cfg_path.resolve())
    if args.step == "tts-dry-run":
        step_tts_dry_run(cfg)
    if args.step in ("vo", "all"):
        step_vo(cfg, args.force_vo)
    if args.step in ("render", "all"):
        step_render(cfg)


if __name__ == "__main__":
    main()
