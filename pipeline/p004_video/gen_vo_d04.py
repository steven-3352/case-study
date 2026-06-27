#!/usr/bin/env python3
"""W27D04 VO 生成 · MiniMax 真诚青年 · 逐段情绪 · 8 镜 ~42s.

各镜窗口(s)：s1=3 s2=4 s3=4 s4=8 s5=7 s6=6 s7=5 s8=5  → 合计 42s
逐段 emotion/speed 见 publish/2026-W27/D04-内容服务测水/audio_plan.yaml.
失败回落 edge(synthesize_text 内置兜底).
输出 pipeline/p004_video/out/audio/vo_d04.mp3 + 每段 mp3 + seg_timing_d04.json
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent
PROJECT = ROOT.parent.parent
sys.path.insert(0, str(PROJECT))

from pipeline.tts.gen_speech import synthesize_text  # noqa: E402

OUT = ROOT / "out" / "audio"
OUT.mkdir(parents=True, exist_ok=True)

# voice_id 覆盖：audio_plan 指定真诚青年(对齐 D03 选用)
CFG_OVERRIDE = ROOT / "_d04_tts_config.yaml"
import yaml  # noqa: E402

base_cfg = yaml.safe_load((PROJECT / "pipeline" / "tts" / "config.yaml").read_text(encoding="utf-8"))
base_cfg["minimax"]["voice_id"] = "Chinese (Mandarin)_Sincere_Adult"
CFG_OVERRIDE.write_text(yaml.safe_dump(base_cfg, allow_unicode=True), encoding="utf-8")

# (id, window_s, emotion, speed, text)
# 总目标 42s; 各段窗口 = VO + 尾静音.
# vA 自然语速 ~40s, 逐段速度做轻微差异化(自燃段慢些, 报价段平稳, CTA 略快)
SEGMENTS: list[tuple[str, float, str, float, str]] = [
    ("s1", 3.0, "sad",     1.05, "我做 AI 内容 4 周，粉丝几乎没动过。"),
    ("s2", 4.0, "neutral", 1.10, "但今早 3 个实体店老板私信我：能给我店里也做一套吗？"),
    ("s3", 4.0, "happy",   1.05, "你可能想笑——自己都做不起来，凭啥收钱？"),
    ("s4", 8.0, "neutral", 1.05, "我反过来想：我已经扑得很彻底，每个坑我都精确知道在哪。这是花钱买不到的清单。"),
    ("s5", 7.0, "neutral", 1.10, "4 周，AI 全自动出片，一条不到 3 块。"),
    ("s6", 6.0, "neutral", 1.18, "我开 3 档实体店老板看：99 一月 4 条，299 一月 14 条，599 一月 14 条加周复盘。14 条交付不行你说停，剩下原路退。"),
    ("s7", 5.0, "sad",     1.00, "但我不知道有没有人愿意付。"),
    ("s8", 5.0, "neutral", 1.10, "评论扣个档位号，或扣 0：不付。扣到 10 个，我免费做 3 个 demo。"),
]

TAIL_PAD: dict[str, float] = {
    "s1": 0.3, "s2": 0.3, "s3": 0.4, "s4": 0.4,
    "s5": 0.4, "s6": 0.4, "s7": 0.5, "s8": 0.8,
}


def dur(p: pathlib.Path) -> float:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "json", str(p)],
        capture_output=True, text=True,
    )
    return float(json.loads(r.stdout)["format"]["duration"])


def main() -> None:
    engines: set[str] = set()
    timing: list[dict] = []
    padded_paths: list[pathlib.Path] = []
    cum = 0.0
    for sid, _window, emo, spd, text in SEGMENTS:
        raw = OUT / f"vo_d04_{sid}_raw.mp3"
        eng = synthesize_text(text, raw, config_path=CFG_OVERRIDE, emotion=emo, speed=spd)
        engines.add(eng)
        d = dur(raw)
        pad = TAIL_PAD.get(sid, 0.4)
        window = round(d + pad, 2)
        print(f"  {sid}: {eng} emo={emo} spd={spd} → VO {d:.2f}s + pad {pad}s = 窗口 {window}s")
        padded = OUT / f"vo_d04_{sid}.mp3"
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(raw),
             "-af", f"apad=pad_dur={pad:.3f}", "-t", f"{window:.3f}",
             str(padded)],
            capture_output=True,
        )
        padded_paths.append(padded)
        timing.append({
            "id": sid, "window": window, "vo_dur": round(d, 2),
            "start": round(cum, 2), "seg_dur": window,
            "emotion": emo, "speed": spd, "text": text,
        })
        cum += window

    listf = OUT / "vo_d04_concat.txt"
    listf.write_text("".join(f"file '{p}'\n" for p in padded_paths))
    final = OUT / "vo_d04.mp3"
    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(listf),
         "-c", "copy", str(final)],
        capture_output=True,
    )
    total = dur(final)
    (OUT / "seg_timing_d04.json").write_text(
        json.dumps({"engine": sorted(engines), "total": round(total, 2), "segments": timing},
                   ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\n✓ VO 引擎: {sorted(engines)}  总时长: {total:.2f}s → {final}")
    print(f"  时序: {OUT / 'seg_timing_d04.json'}")


if __name__ == "__main__":
    main()
