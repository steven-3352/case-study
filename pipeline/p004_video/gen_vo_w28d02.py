#!/usr/bin/env python3
"""W28D02 VO 生成 · MiniMax 真诚青年 · vB 版 8 段 ~50s.

vB 变更（2026-07-04）：**砍掉沉默钉子**，VO 从 0s 覆盖到底。
参考 3 支密 VO 无 BGM 视频（WaytoAGI / 七七 / 浙大猫学长）：全片无死区。

窗口(s): s1=3 s2=3 s3=6 s4=6 s5=14 s6=8 s7=6 s8=4 → 合计 50s
逐段 emotion/speed 见 audio_plan.yaml
失败回落 edge (synthesize_text 内置兜底)
输出 publish/2026-W28/D02-*/build/audio/vo_w28d02.mp3 + 每段 mp3 + seg_timing_w28d02.json
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

OUT = PROJECT / "publish" / "2026-W28" / "D02-打工人5分钟出周报" / "build" / "audio"
OUT.mkdir(parents=True, exist_ok=True)

# voice_id 覆盖：真诚青年（对齐 skin.persona_anchor "老兵同事口吻"）
CFG_OVERRIDE = ROOT / "_w28d02_tts_config.yaml"
import yaml  # noqa: E402

base_cfg = yaml.safe_load((PROJECT / "pipeline" / "tts" / "config.yaml").read_text(encoding="utf-8"))
base_cfg["minimax"]["voice_id"] = "Chinese (Mandarin)_Sincere_Adult"
CFG_OVERRIDE.write_text(yaml.safe_dump(base_cfg, allow_unicode=True), encoding="utf-8")

# (id, window_s, emotion, speed, text)
# vB 版 8 段（新增 s1/s2 覆盖 0-6s，砍沉默钉子）
SEGMENTS: list[tuple[str, float, str, float, str]] = [
    # 0-3s · 情境开场 · sad
    ("s1", 3.0, "sad", 1.05, "周五快下班，办公室只剩你。"),
    # 3-6s · 老板一句 · neutral（配合 kick sting + 大字 18:55·周五）
    ("s2", 3.0, "neutral", 1.05, "手机一亮：老板发的，周报呢？"),
    # 6-12s · 痛点点破 + 反面（合并）· 情绪 sad
    ("s3", 6.0, "sad", 1.05,
     "周报难写不是事情多。是没得写、写不出、占私人时间。而大部分人都在做同一件蠢事——打开AI说，帮我写周报。"),
    # 12-18s · 反转开场 · 情绪 neutral
    ("s4", 6.0, "neutral", 1.08,
     "关键动作不是prompt，是把这一周乱七八糟的东西全扔进去。备忘录、微信截图、日程、群消息，越乱越好。"),
    # 18-32s · 演示核心 · 情绪 neutral、速度稳
    ("s5", 14.0, "neutral", 1.05,
     "然后是5段prompt。角色，你是职场写作助手。规矩，三块，本周总结、下周计划、问题。反例，别写参加了会议这种。兜底，AI自己合理补全。字数，300字以内。"),
    # 32-40s · 效果对比 · 情绪 happy（释放）
    ("s6", 8.0, "happy", 1.08,
     "2分钟出草稿，3分钟改。18:15你在下班的路上，同事还在改到20点。京东员工的周报要5000字，你现在300字够用了。"),
    # 40-46s · 价值锚 · 情绪 neutral、慢
    ("s7", 6.0, "neutral", 0.98,
     "这不是AI教程。是我周五18:55，救过我自己无数次的prompt。"),
    # 46-50s · CTA · 情绪 neutral
    ("s8", 4.0, "neutral", 1.05,
     "评论区告诉我你什么岗位，我按行业发一版。"),
]

TAIL_PAD: dict[str, float] = {
    "s1": 0.2, "s2": 0.2, "s3": 0.4, "s4": 0.4, "s5": 0.5, "s6": 0.4, "s7": 0.5, "s8": 0.8,
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
    cum = 0.0  # 从 0s 起（沉默钉子已砍）

    # 清理旧的沉默文件（若存在）
    old_silence = OUT / "vo_w28d02_s1s2_silence.mp3"
    if old_silence.exists():
        old_silence.unlink()

    for sid, _window, emo, spd, text in SEGMENTS:
        raw = OUT / f"vo_w28d02_{sid}_raw.mp3"
        eng = synthesize_text(text, raw, config_path=CFG_OVERRIDE, emotion=emo, speed=spd)
        engines.add(eng)
        d = dur(raw)
        pad = TAIL_PAD.get(sid, 0.4)
        window = round(d + pad, 2)
        print(f"  {sid}: {eng} emo={emo} spd={spd} → VO {d:.2f}s + pad {pad}s = 窗口 {window}s")
        padded = OUT / f"vo_w28d02_{sid}.mp3"
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

    listf = OUT / "vo_w28d02_concat.txt"
    listf.write_text("".join(f"file '{p}'\n" for p in padded_paths))
    final = OUT / "vo_w28d02.mp3"
    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(listf),
         "-c", "copy", str(final)],
        capture_output=True,
    )
    total = dur(final)
    (OUT / "seg_timing_w28d02.json").write_text(
        json.dumps({"engine": sorted(engines), "total": round(total, 2), "segments": timing},
                   ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f"\n✓ VO 合成完成 · 总长 {total:.2f}s · 段数 {len(padded_paths)}")
    print(f"  输出：{final}")
    print(f"  时间线：{OUT}/seg_timing_w28d02.json")


if __name__ == "__main__":
    main()
