#!/usr/bin/env python3
from __future__ import annotations

import json
import pathlib
import shutil
import subprocess

ROOT = pathlib.Path(__file__).resolve().parent
OUT = ROOT.parent / "video.mp4"
TMP_VIDEO = ROOT / "dynamic_silent.mp4"
VOICE = ROOT / "vo_minimax.mp3"
FRAMES = ROOT / "frames"
RENDERER = ROOT / "dynamic_renderer.html"
CAPTURE = ROOT / "capture_frames.mjs"

FPS = 15
W, H = 720, 1280


def run(cmd: list[str]) -> None:
    print(" ".join(cmd[:10]), "...")
    subprocess.run(cmd, check=True)


def duration(path: pathlib.Path) -> float:
    out = subprocess.check_output(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=nk=1:nw=1",
            str(path),
        ],
        text=True,
    )
    return float(out.strip())


def chrome_path() -> str:
    candidates = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        shutil.which("google-chrome"),
        shutil.which("chromium"),
    ]
    for item in candidates:
        if item and pathlib.Path(item).exists():
            return item
    raise SystemExit("missing Chrome/Chromium for dynamic frame capture")


def main() -> None:
    if not VOICE.exists():
        raise SystemExit(f"missing production TTS: {VOICE}")
    if not RENDERER.exists():
        raise SystemExit(f"missing dynamic renderer: {RENDERER}")
    if not CAPTURE.exists():
        raise SystemExit(f"missing frame capture script: {CAPTURE}")

    dur = duration(VOICE)
    frame_count = int(dur * FPS + 0.999)
    frame_files = list(FRAMES.glob("frame_*.png")) if FRAMES.exists() else []
    existing_frames = len(frame_files)
    renderer_mtime = RENDERER.stat().st_mtime
    stale_frames = any(frame.stat().st_mtime < renderer_mtime for frame in frame_files[:1])
    if existing_frames < frame_count or stale_frames:
        shutil.rmtree(FRAMES, ignore_errors=True)
        FRAMES.mkdir(parents=True, exist_ok=True)
        run(
            [
                "node",
                str(CAPTURE),
                "--chrome",
                chrome_path(),
                "--html",
                str(RENDERER),
                "--out",
                str(FRAMES),
                "--duration",
                f"{dur:.3f}",
                "--fps",
                str(FPS),
                "--width",
                str(W),
                "--height",
                str(H),
            ]
        )
    else:
        print(f"reuse existing frames: {existing_frames}")

    run(
        [
            "ffmpeg",
            "-y",
            "-framerate",
            str(FPS),
            "-i",
            str(FRAMES / "frame_%05d.png"),
            "-vf",
            "scale=1080:1920:flags=lanczos",
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            "-r",
            "30",
            str(TMP_VIDEO),
        ]
    )

    tick_delays = [800, 14000, 17100, 20400, 24400, 28200, 31800, 34800, 38200, 43000, 49000, 58000]
    split_labels = "".join(f"[ticksrc{i}]" for i in range(len(tick_delays)))
    tick_graph = (
        "[3:a]volume=0.022,atrim=0:0.07,asetpts=PTS-STARTPTS"
        f",asplit={len(tick_delays)}{split_labels};"
    )
    labels = []
    for i, delay in enumerate(tick_delays):
        labels.append(f"t{i}")
        tick_graph += f"[ticksrc{i}]adelay={delay}|{delay}[t{i}];"
    amix_inputs = 2 + len(labels)
    audio_graph = (
        "[2:a]lowpass=f=340,volume=0.052,afade=t=in:st=0:d=0.5,"
        f"afade=t=out:st={max(dur - 1.2, 0):.3f}:d=1.1[bg];"
        f"{tick_graph}"
        f"[1:a][bg]{''.join(f'[{x}]' for x in labels)}"
        f"amix=inputs={amix_inputs}:duration=first:dropout_transition=0[a]"
    )

    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(TMP_VIDEO),
            "-i",
            str(VOICE),
            "-f",
            "lavfi",
            "-t",
            f"{dur:.3f}",
            "-i",
            "anoisesrc=color=pink:amplitude=0.010:sample_rate=44100",
            "-f",
            "lavfi",
            "-t",
            f"{dur:.3f}",
            "-i",
            "sine=frequency=690:sample_rate=44100",
            "-filter_complex",
            audio_graph,
            "-map",
            "0:v",
            "-map",
            "[a]",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "160k",
            "-movflags",
            "+faststart",
            "-shortest",
            str(OUT),
        ]
    )

    probe = {
        "output": str(OUT),
        "duration": round(duration(OUT), 3),
        "source": "dynamic HTML renderer sampled with Chrome CDP",
        "tts": "MiniMax vo_minimax.mp3",
        "fps_capture": FPS,
        "frames": frame_count,
    }
    print(json.dumps(probe, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
