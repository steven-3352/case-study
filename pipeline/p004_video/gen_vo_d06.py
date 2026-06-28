#!/usr/bin/env python3
"""W27D06 VO · MiniMax 真诚青年 · 6 镜 ~42s."""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent
PROJECT = ROOT.parent.parent
sys.path.insert(0, str(PROJECT))

import yaml  # noqa: E402
from pipeline.tts.gen_speech import synthesize_text  # noqa: E402

OUT = ROOT / "out" / "audio"
OUT.mkdir(parents=True, exist_ok=True)
CFG = ROOT / "_d06_tts_config.yaml"
base = yaml.safe_load((PROJECT / "pipeline" / "tts" / "config.yaml").read_text(encoding="utf-8"))
base["minimax"]["voice_id"] = "Chinese (Mandarin)_Sincere_Adult"
CFG.write_text(yaml.safe_dump(base, allow_unicode=True), encoding="utf-8")

SEGMENTS = [
    ("s1", 3.5, "neutral", 1.05, "我只在 queue 里打了一行选题。"),
    ("s2", 8.0, "neutral", 1.08, "后面洞察包、讨论室打分、两道门禁——不是我记在备忘录里的 checklist。"),
    ("s3", 8.0, "neutral", 1.06, "网络调研、四件套洞察、脚本三版、形式策略，工种 scorecard 没过九十分，不让配音出片。"),
    ("s4", 8.0, "neutral", 1.05, "gate_check，pre_render 通过才 render；approve 通过才能外发。脚本九十分，形式不及格，照样退稿。"),
    ("s5", 6.0, "neutral", 1.00, "跑通 pipeline 不等于能发，同质、forecast、像素审计，一道过不去就拦下。"),
    ("s6", 9.0, "neutral", 1.06, "你最想先甩给 Agent 的，是写稿、找素材，还是过门禁？评论区说一件具体事。"),
]
TAIL = {"s1": 0.3, "s2": 0.4, "s3": 0.3, "s4": 0.4, "s5": 0.3, "s6": 0.6}


def dur(p: pathlib.Path) -> float:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(p)],
        capture_output=True, text=True,
    )
    return float(json.loads(r.stdout)["format"]["duration"])


def main() -> None:
    paths: list[pathlib.Path] = []
    timing: list[dict] = []
    for sid, _w, emo, spd, text in SEGMENTS:
        raw = OUT / f"vo_d06_{sid}_raw.mp3"
        synthesize_text(text, raw, config_path=CFG, emotion=emo, speed=spd)
        d = dur(raw)
        pad = TAIL.get(sid, 0.4)
        window = round(d + pad, 2)
        padded = OUT / f"vo_d06_{sid}.mp3"
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(raw), "-af", f"apad=pad_dur={pad:.3f}", "-t", f"{window:.3f}", str(padded)],
            capture_output=True,
        )
        paths.append(padded)
        timing.append({"id": sid, "vo_s": round(d, 2), "window_s": window})
        print(f"  {sid}: {d:.2f}s + {pad}s = {window}s")

    lst = OUT / "vo_d06_list.txt"
    lst.write_text("\n".join(f"file '{p.resolve()}'" for p in paths), encoding="utf-8")
    merged = OUT / "vo_d06.mp3"
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(merged)], check=True)
    (OUT / "seg_timing_d06.json").write_text(json.dumps(timing, indent=2), encoding="utf-8")
    print(f"✓ {merged} ({dur(merged):.1f}s)")


if __name__ == "__main__":
    main()
