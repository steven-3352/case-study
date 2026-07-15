#!/usr/bin/env python3
"""EP03 全长版 · 最终合成(复刻 EP01)。

帧序列(7场景)→ 静音串接 → overlay 字幕 PNG 序列 → 混 VO(真声)+ SFX 床 → 成片。
用法: ./.venv/bin/python pipeline/p004_video/build_ep03_final.py
"""
from __future__ import annotations
import json, pathlib, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parent
FRAMES = ROOT/"out"/"frames"
OUT = ROOT/"out"/"ep03full"
SCENES = OUT/"scenes"; SCENES.mkdir(parents=True, exist_ok=True)
FPS, W, H = 30, 1080, 1920
SCENE_IDS = ["ep03_s0_hook","ep03_s1_dumbfix","ep03_s2_read","ep03_s3_deadends",
             "ep03_s4_mechanical","ep03_s5_rule","ep03_s6_land"]
VO = OUT/"vo_master.wav"
SFX = OUT/"sfx_bed_full.wav"
SUBS = FRAMES/"ep03f_subs"

def run(cmd, stage):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr[-2500:]); sys.exit(f"ffmpeg 失败 @ {stage}")

def dur(p):
    r = subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
                        "-of","json",str(p)], capture_output=True, text=True)
    return float(json.loads(r.stdout)["format"]["duration"])

# 1) 各场景帧 → mp4(静音)
scene_mp4s = []
for sid in SCENE_IDS:
    src = FRAMES/sid
    if not any(src.glob("frame_*.png")): sys.exit(f"缺帧 {src}")
    out = SCENES/f"{sid}.mp4"
    run(["ffmpeg","-y","-framerate",str(FPS),"-i",str(src/"frame_%04d.png"),
         "-vf",f"scale={W}:{H}:flags=lanczos,format=yuv420p",
         "-c:v","libx264","-preset","medium","-crf","18","-pix_fmt","yuv420p",
         "-movflags","+faststart",str(out)], f"scene {sid}")
    scene_mp4s.append(out)
    print(f"  ✓ {sid}: {dur(out):.2f}s")

# 2) 串接静音全片
lst = SCENES/"concat.txt"; lst.write_text("".join(f"file '{p}'\n" for p in scene_mp4s))
allv = SCENES/"all_video.mp4"
run(["ffmpeg","-y","-f","concat","-safe","0","-i",str(lst),
     "-c:v","libx264","-preset","medium","-crf","18","-pix_fmt","yuv420p",
     "-movflags","+faststart",str(allv)], "concat")
vdur = dur(allv)
print(f"  静音全片 {vdur:.2f}s")

# 3) overlay 字幕 + 混 VO + SFX → 成片
final = OUT/"EP03_全长版_真声_抖音.mp4"
fc = (
    "[0:v][1:v]overlay=0:0:format=auto:eof_action=repeat[v];"
    "[2:a]volume=1.0[vo];"
    "[3:a]volume=0.5[sfx];"
    "[vo][sfx]amix=inputs=2:duration=first:dropout_transition=0:normalize=0,"
    "alimiter=limit=0.97[a]"
)
run(["ffmpeg","-y",
     "-i",str(allv),
     "-framerate",str(FPS),"-i",str(SUBS/"frame_%04d.png"),
     "-i",str(VO),
     "-i",str(SFX),
     "-filter_complex",fc,
     "-map","[v]","-map","[a]",
     "-t",f"{vdur:.3f}",
     "-c:v","libx264","-preset","medium","-crf","19","-pix_fmt","yuv420p",
     "-c:a","aac","-b:a","192k","-ar","44100","-movflags","+faststart",
     str(final)], "compose final")
print(f"\n✓ 成片: {final}  ({dur(final):.2f}s)")

# 也出一版无 sfx(纯真声+字幕)备份
final_vo = OUT/"EP03_全长版_真声纯VO_抖音.mp4"
run(["ffmpeg","-y","-i",str(allv),
     "-framerate",str(FPS),"-i",str(SUBS/"frame_%04d.png"),
     "-i",str(VO),
     "-filter_complex","[0:v][1:v]overlay=0:0:format=auto:eof_action=repeat[v];[2:a]volume=1.0[a]",
     "-map","[v]","-map","[a]","-t",f"{vdur:.3f}",
     "-c:v","libx264","-preset","medium","-crf","19","-pix_fmt","yuv420p",
     "-c:a","aac","-b:a","192k","-ar","44100","-movflags","+faststart",
     str(final_vo)], "compose vo-only")
print(f"✓ 纯VO备份: {final_vo}  ({dur(final_vo):.2f}s)")
