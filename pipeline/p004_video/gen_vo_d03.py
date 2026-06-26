#!/usr/bin/env python3
"""W27D03 VO 生成 · MiniMax 真诚青年 · 逐段情绪 · 按各镜时长 padding → concat ~45s.

各镜窗口(s)：s1=3 s2=8 s3=9 s4=8 s5=9 s6=8  → 合计 45s
逐段 emotion/speed 见 audio_plan.yaml emotion_arc。
失败回落 edge（synthesize_text 内置兜底）。
输出 pipeline/p004_video/out/audio/vo_d03.mp3 + 同目录每段 mp3 + seg_timing.json
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

# voice_id 覆盖：audio_plan 指定真诚青年（config.yaml 默认是 male-qn-badao）
CFG_OVERRIDE = ROOT / "_d03_tts_config.yaml"
import yaml  # noqa: E402

base_cfg = yaml.safe_load((PROJECT / "pipeline" / "tts" / "config.yaml").read_text(encoding="utf-8"))
base_cfg["minimax"]["voice_id"] = "Chinese (Mandarin)_Sincere_Adult"
CFG_OVERRIDE.write_text(yaml.safe_dump(base_cfg, allow_unicode=True), encoding="utf-8")

SEGMENTS = [
    # (id, window_s, emotion, speed, text)
    # 实测：vA 口播在自然语速下约 60s；为接近 45s 目标整体提速，但保留逐段情绪与节奏差，
    # 末段(s6)语速不赶（铁律：末5s 不赶留白）。窗口在 build 阶段按实测 VO 时长回填。
    ("s1", 3.0, "sad",     1.0,  "一天搭完，第5天我傻眼了。"),
    ("s2", 8.0, "happy",   1.18, "一个人，做老外的英文市场。我用一天，把拉客、收邮箱、自动跟进，从头搭到上线。"),
    ("s3", 9.0, "neutral", 1.22, "然后我就不管了。有人填邮箱，它立刻发欢迎信，往后每隔几天自己发一封养着，我人不在，它照样一封封地发，跟进这环我盯的时间几乎是零。"),
    ("s4", 8.0, "sad",     1.05, "它一直在替我攒老外客户。可第5天我一看，曝光是涨了，留下来的却寥寥无几。"),
    ("s5", 9.0, "happy",   1.22, "扒下来根因是内容太机器，AI一键出的图谁都刷过。改成AI只出背景、文字我自己排，才像活人发的，留资才开始动。整套基本没花钱，盯守也几乎是零。"),
    ("s6", 8.0, "neutral", 1.06, "系统能跑，内容得先像人。你有没有留了线索却总忘跟进的活？评论说说，下条我把这套自动跟进拆给你。"),
]


def dur(p: pathlib.Path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "json", str(p)], capture_output=True, text=True)
    return float(json.loads(r.stdout)["format"]["duration"])


def main() -> None:
    engines = set()
    timing = []
    padded_paths = []
    cum = 0.0
    # 策略：窗口 = 实测 VO 时长 + 尾静音留白；保证口播完整不截断（铁律：CTA 完整进 mp4）。
    # 尾 pad 给 GSAP 收尾/换镜留白；s6 末尾多留白给完播。
    TAIL_PAD = {"s1": 0.5, "s2": 0.5, "s3": 0.6, "s4": 0.5, "s5": 0.6, "s6": 1.2}
    for sid, _window, emo, spd, text in SEGMENTS:
        raw = OUT / f"vo_d03_{sid}_raw.mp3"
        eng = synthesize_text(text, raw, config_path=CFG_OVERRIDE, emotion=emo, speed=spd)
        engines.add(eng)
        d = dur(raw)
        pad = TAIL_PAD.get(sid, 0.5)
        window = round(d + pad, 2)
        print(f"  {sid}: {eng} emo={emo} spd={spd} → VO {d:.2f}s + pad {pad}s = 窗口 {window}s")
        padded = OUT / f"vo_d03_{sid}.mp3"
        subprocess.run([
            "ffmpeg", "-y", "-i", str(raw),
            "-af", f"apad=pad_dur={pad:.3f}", "-t", f"{window:.3f}",
            str(padded)], capture_output=True)
        padded_paths.append(padded)
        timing.append({"id": sid, "window": window, "vo_dur": round(d, 2),
                       "start": round(cum, 2), "seg_dur": window,
                       "emotion": emo, "speed": spd, "text": text})
        cum += window

    # concat
    listf = OUT / "vo_d03_concat.txt"
    listf.write_text("".join(f"file '{p}'\n" for p in padded_paths))
    final = OUT / "vo_d03.mp3"
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(listf),
                    "-c", "copy", str(final)], capture_output=True)
    total = dur(final)
    (OUT / "seg_timing_d03.json").write_text(
        json.dumps({"engine": sorted(engines), "total": round(total, 2), "segments": timing},
                   ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n✓ VO 引擎: {sorted(engines)}  总时长: {total:.2f}s → {final}")
    print(f"  时序: {OUT / 'seg_timing_d03.json'}")


if __name__ == "__main__":
    main()
