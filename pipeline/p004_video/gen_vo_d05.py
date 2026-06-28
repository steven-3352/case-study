#!/usr/bin/env python3
"""W27D05 VO 生成 · MiniMax 真诚青年 · 7 镜 ~40s.

各镜窗口(s): s1=3 s2=3 s3=6 s4=10 s5=6 s6=5 s7=7  → 合计 40s
逐段 emotion/speed 见 publish/2026-W27/D05-招人前先数群/audio_plan.yaml.
失败回落 edge(synthesize_text 内置兜底).
输出 pipeline/p004_video/out/audio/vo_d05.mp3 + 每段 mp3 + seg_timing_d05.json
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

CFG_OVERRIDE = ROOT / "_d05_tts_config.yaml"
import yaml  # noqa: E402

base_cfg = yaml.safe_load((PROJECT / "pipeline" / "tts" / "config.yaml").read_text(encoding="utf-8"))
base_cfg["minimax"]["voice_id"] = "Chinese (Mandarin)_Sincere_Adult"
CFG_OVERRIDE.write_text(yaml.safe_dump(base_cfg, allow_unicode=True), encoding="utf-8")

# (id, window_s, emotion, speed, text)
# vA 自然语速 ~38s, 各段微差: 反差句平稳, 教学段略快, 内核句慢
SEGMENTS: list[tuple[str, float, str, float, str]] = [
    ("s1", 3.0, "neutral", 1.05, "有个母婴店老板上个月跟我说，得招个人专门回客户消息。"),
    ("s2", 3.0, "neutral", 1.00, "我说，先别招。"),
    ("s3", 6.0, "neutral", 1.10, "我让她把 90 天微信群聊天记录，全部导出来，贴给 AI。归类、统计、出表。"),
    ("s4", 10.0, "neutral", 1.08, "1200 多条客户问题，真不一样的就 10 来类。前 5 类：营业时间、价格、改约、产品适用、退换。占了 7 成多。"),
    ("s5", 6.0, "sad", 1.00, "她看完柱图沉默了三秒。当晚发群：招人推迟，先做个表。"),
    ("s6", 5.0, "neutral", 0.95, "你不是缺人，你是缺数据。"),
    ("s7", 7.0, "happy", 1.08, "评论扣\"也想数\"，我把数法和 Excel 模板发你。凑 10 个发模板。"),
]

TAIL_PAD: dict[str, float] = {
    "s1": 0.3, "s2": 0.4, "s3": 0.3, "s4": 0.4,
    "s5": 0.5, "s6": 0.5, "s7": 0.8,
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
        raw = OUT / f"vo_d05_{sid}_raw.mp3"
        eng = synthesize_text(text, raw, config_path=CFG_OVERRIDE, emotion=emo, speed=spd)
        engines.add(eng)
        d = dur(raw)
        pad = TAIL_PAD.get(sid, 0.4)
        window = round(d + pad, 2)
        print(f"  {sid}: {eng} emo={emo} spd={spd} → VO {d:.2f}s + pad {pad}s = 窗口 {window}s")
        padded = OUT / f"vo_d05_{sid}.mp3"
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

    listf = OUT / "vo_d05_concat.txt"
    listf.write_text("".join(f"file '{p}'\n" for p in padded_paths))
    final = OUT / "vo_d05.mp3"
    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(listf),
         "-c", "copy", str(final)],
        capture_output=True,
    )
    total = dur(final)
    (OUT / "seg_timing_d05.json").write_text(
        json.dumps({"engine": sorted(engines), "total": round(total, 2), "segments": timing},
                   ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\n✓ VO 引擎: {sorted(engines)}  总时长: {total:.2f}s → {final}")
    print(f"  时序: {OUT / 'seg_timing_d05.json'}")


if __name__ == "__main__":
    main()
