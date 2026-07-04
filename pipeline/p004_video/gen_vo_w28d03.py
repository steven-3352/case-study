#!/usr/bin/env python3
"""W28D03 VO 生成 · MiniMax 男声·精英精品 · 8 段 58s.

来源：publish/2026-W28/D03-AI陪练英语口语/audio_plan.yaml
铁律（memory feedback_dense-vo-no-dead-air）：
  - 0-3s 沉默钉子（环境音钉子，非死区，VO 覆盖起点从 3s 计）
  - 3-58s VO 全程覆盖，段间由 M7 真英文对话音填充无死区
  - VO 覆盖 ≥85%（本条 45s VO + 6s M7 段真对话 = 51s / 58s = 87.9%）
  - loudnorm 目标 -16 dB · LRA 11 · TP -1.5

失败回落 edge (synthesize_text 内置兜底)。
输出 publish/2026-W28/D03-*/build/audio/vo_w28d03.mp3 + 每段 mp3 + seg_timing_w28d03.json
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

FFMPEG = "/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg"
FFPROBE = "/opt/homebrew/opt/ffmpeg-full/bin/ffprobe"

OUT = PROJECT / "publish" / "2026-W28" / "D03-AI陪练英语口语" / "build" / "audio"
OUT.mkdir(parents=True, exist_ok=True)

# voice_id 覆盖：男声·精英精品（对齐 skin.persona_anchor "学英语同路人 · 反教程"）
CFG_OVERRIDE = ROOT / "_w28d03_tts_config.yaml"
import yaml  # noqa: E402

base_cfg = yaml.safe_load((PROJECT / "pipeline" / "tts" / "config.yaml").read_text(encoding="utf-8"))
base_cfg["minimax"]["voice_id"] = "male-qn-jingying-jingpin"
base_cfg["minimax"]["speed"] = 0.95
CFG_OVERRIDE.write_text(yaml.safe_dump(base_cfg, allow_unicode=True), encoding="utf-8")

# (id, target_start_s, target_dur_s, emotion, speed, text)
# 段位对齐 audio_plan.yaml segments
# 0-3s 沉默钉子（不生 VO · 由 env_audio 填充）
# 36-42s M7 无中文 VO（由真机豆包真英文对话音填充）
SEGMENTS: list[tuple[str, float, float, str, float, str]] = [
    # 3-8s · 群体锚 · 情绪 neutral · 沉稳克制
    ("s2", 3.0, 5.0, "neutral", 0.95,
     "晚上十一点，你在对着墙念英语。九成中国人不敢开口——不是你的问题，是没人的问题。"),
    # 8-15s · 打卡幻灭 · 情绪 sad · 稍慢
    ("s3", 8.0, 7.0, "sad", 0.93,
     "多邻国打了七百天卡，见到老外还是——嘴张开一半，脑子空了。"),
    # 15-20s · 反面正解 · 情绪 neutral
    ("s4", 15.0, 5.0, "neutral", 0.95,
     "你去问AI，怎么练口语——它给你十条建议，全是废话。"),
    # 20-24s · 顿悟锚 · 情绪 neutral · 一句短话，留白效果
    ("s5", 20.0, 4.0, "neutral", 0.92,
     "问题在这。"),
    # 24-36s · 演示核心 role prompt · 情绪 neutral · 稳
    ("s6", 24.0, 12.0, "neutral", 0.95,
     "你不是要AI教你，你要AI陪你说。先给它一张角色卡：你是我雅思口语搭档，我Part 3，你只用英文提问，我说错也别打断。"),
    # 36-42s · M7 段无中文 VO（真英文对话音填充 · 不生 mp3）
    # 42-48s · 情感落点 · 情绪 neutral · 沉稳
    ("s8", 42.0, 6.0, "neutral", 0.95,
     "先敢说三十分钟，比敢背三百单词管用。"),
    # 48-54s · 价值锚 · 情绪 neutral · 慢 · 沉稳同事口吻
    ("s9", 48.0, 6.0, "neutral", 0.92,
     "不是教你怎么问AI。是把我二十二点三十用的救命role prompt给你。"),
    # 54-58s · CTA · 情绪 neutral · 干脆
    ("s10", 54.0, 4.0, "neutral", 0.98,
     "评论 面试、雅思、日常、旅游——我把对应role prompt给你。"),
]

TAIL_PAD: dict[str, float] = {
    "s2": 0.15, "s3": 0.20, "s4": 0.15, "s5": 0.30, "s6": 0.30,
    "s8": 0.25, "s9": 0.30, "s10": 0.60,
}


def dur(p: pathlib.Path) -> float:
    r = subprocess.run(
        [FFPROBE, "-v", "error", "-show_entries", "format=duration",
         "-of", "json", str(p)],
        capture_output=True, text=True,
    )
    return float(json.loads(r.stdout)["format"]["duration"])


def main() -> None:
    engines: set[str] = set()
    timing: list[dict] = []
    padded_paths: list[pathlib.Path] = []

    # 0-3s 沉默钉子（env_audio 填充 · 生占位静音供 concat 对齐）
    silence_head = OUT / "vo_w28d03_head_silence.mp3"
    subprocess.run(
        [FFMPEG, "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono",
         "-t", "3.0", "-q:a", "9", "-acodec", "libmp3lame", str(silence_head)],
        capture_output=True,
    )
    padded_paths.append(silence_head)
    timing.append({
        "id": "s1_silence", "window": 3.0, "vo_dur": 0.0,
        "start": 0.0, "seg_dur": 3.0,
        "emotion": "silence", "speed": 0.0,
        "text": "(0-3s 沉默钉子 · 由 env_audio 深夜环境音 + 咽口水 SFX 填充)",
    })

    cum = 3.0
    for sid, target_start, target_dur, emo, spd, text in SEGMENTS:
        # 若段位起点与 cum 不匹配（M7 36-42s 空段），先补静音（M7 会由真英文对话音替换）
        if target_start > cum + 0.01:
            gap = target_start - cum
            gap_silence = OUT / f"vo_w28d03_gap_{int(cum)}s.mp3"
            subprocess.run(
                [FFMPEG, "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono",
                 "-t", f"{gap:.3f}", "-q:a", "9", "-acodec", "libmp3lame", str(gap_silence)],
                capture_output=True,
            )
            padded_paths.append(gap_silence)
            timing.append({
                "id": f"gap_{int(cum)}s", "window": round(gap, 2), "vo_dur": 0.0,
                "start": round(cum, 2), "seg_dur": round(gap, 2),
                "emotion": "gap", "speed": 0.0,
                "text": f"(M7 段 · {int(cum)}-{int(target_start)}s · 真机豆包语音真对话音填充)",
            })
            cum = target_start

        raw = OUT / f"vo_w28d03_{sid}_raw.mp3"
        eng = synthesize_text(text, raw, config_path=CFG_OVERRIDE, emotion=emo, speed=spd)
        engines.add(eng)
        d = dur(raw)
        pad = TAIL_PAD.get(sid, 0.3)
        window = round(max(d + pad, target_dur), 2)
        print(f"  {sid}: {eng} emo={emo} spd={spd} → VO {d:.2f}s + pad {pad}s = 窗口 {window}s (目标 {target_dur}s)")
        padded = OUT / f"vo_w28d03_{sid}.mp3"
        subprocess.run(
            [FFMPEG, "-y", "-i", str(raw),
             "-af", f"apad=whole_dur={window:.3f}", "-t", f"{window:.3f}",
             "-ar", "24000", "-b:a", "128k",
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

    listf = OUT / "vo_w28d03_concat.txt"
    listf.write_text("".join(f"file '{p}'\n" for p in padded_paths))
    final = OUT / "vo_w28d03.mp3"
    # 用 concat 协议 · loudnorm 一次过 target -16 dB
    # Also normalize head_silence + gap silences to same sample rate/bitrate
    # so that concat_raw with re-encode is clean.
    concat_raw = OUT / "vo_w28d03_concat_raw.mp3"
    subprocess.run(
        [FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", str(listf),
         "-c:a", "libmp3lame", "-ar", "24000", "-b:a", "128k", str(concat_raw)],
        capture_output=True,
    )
    subprocess.run(
        [FFMPEG, "-y", "-i", str(concat_raw),
         "-af", "loudnorm=I=-16:LRA=11:TP=-1.5",
         "-ar", "24000", "-b:a", "128k",
         str(final)],
        capture_output=True,
    )
    total = dur(final)
    (OUT / "seg_timing_w28d03.json").write_text(
        json.dumps({"engine": sorted(engines), "total": round(total, 2), "segments": timing},
                   ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f"\n✓ VO 合成完成 · 总长 {total:.2f}s · 段数 {len(padded_paths)}")
    print(f"  输出：{final}")
    print(f"  时间线：{OUT}/seg_timing_w28d03.json")
    print(f"\n提示：0-3s 沉默钉子由 env_audio 填充；36-42s 由真机豆包语音真英文对话音填充。")


if __name__ == "__main__":
    main()
