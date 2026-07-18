#!/usr/bin/env python3
"""D06 武侠MV《一弦入江湖》· 48.25s 完整成片 v2.

修复:
  1. 长度 40→48.25s (原曲全长,歌词唱完再收) · 按剧本情绪弧线重排每段时长
  2. S34 末帧冻结 3.25s + 淡出黑
  3. 加 8 处 SFX 音效 (assets/sfx/ CC0 素材) 与歌曲混音
  4. mux -map 强制音轨映射防 Grok 自带音轨 bug

情绪弧线 (严格按剧本节奏):
  段1 现代唤醒 (0-8s)   | 慢推特写      | S01/S02/S03 = 3/2/3
  段2 拉弦穿越 (8-12s)  | 蓄力          | S04/S05 = 2/2
  段3 江湖闪回 (12-24s) | 鼓点·快切    | 12镜×1s
  段4 低武动作 (24-34s) | 强节奏快切    | 10镜×1s
  段5 高光混剪 (34-42s) | 慢+快交替     | S28/S29 1.5s(慢) S30/S31 0.8s(快) S32 2.4s(带字幕) S33 1s
  段6 尾音收束 (42-48s) | 定格收尾      | S34 3s动 + 3.25s 冻结末帧 + 淡出

SFX (assets/sfx/ CC0 · 音量克制到 -14~-20 dB 不抢人声):
  8.5s S04 琴弓横扫  → whoosh_air_pass       -18 dB
  9.5s S04→S05转场   → riser_short_ascending -16 dB
  23.2s S17 布靴踩水 → impact_soft_boom      -16 dB
  24.5s S18 短刀入画 → subtle_ui_tap_soft    -22 dB (极轻)
  25.4s S19 拨刀火花 → check_tick_soft       -14 dB
  27.5s S21 剑落地   → impact_soft_boom      -14 dB
  33.5s S27 敲刀鞘   → check_tick_soft       -14 dB
  38.0s S31 挡刀最重 → impact_hard_cut       -11 dB (全片最响)
"""
from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V = ROOT / "tmp" / "d06_wuxia" / "videos"
OUT = ROOT / "tmp" / "d06_wuxia"
SRC = ROOT / "publish" / "2026-W30" / "D06" / "5cb1ed3798646bfe3638707510040f0d.mp4"
FFMPEG = "/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg"
FFPROBE = "/opt/homebrew/opt/ffmpeg-full/bin/ffprobe"
FONT = "/System/Library/Fonts/PingFang.ttc"

TOTAL_DURATION = 48.25


# (slug, 该段裁多长, 起, 止)
CUTS: list[tuple[str, float, float, float]] = [
    # 段1 现代唤醒 · 慢推 (0-8s)
    ("S01_modern_window",            3.0,  0.0,  3.0),
    ("S02_finger_string",            2.0,  3.0,  5.0),
    ("S03_lift_eyes",                3.0,  5.0,  8.0),
    # 段2 拉弦穿越 · 蓄力 (8-12s)
    ("S04_bow_sweep",                2.0,  8.0, 10.0),
    ("S05_town_arrival",             2.0, 10.0, 12.0),
    # 段3 江湖闪回 · 快切 (12-24s)
    ("S06_street_gate",              1.0, 12.0, 13.0),
    ("S07_tea_stall",                1.0, 13.0, 14.0),
    ("S08_eave_rain",                1.0, 14.0, 15.0),
    ("S09_market_walk",              1.0, 15.0, 16.0),
    ("S10_carriage_pass",            1.0, 16.0, 17.0),
    ("S11_bridge_glance",            1.0, 17.0, 18.0),
    ("S12_inn_door",                 1.0, 18.0, 19.0),
    ("S13_wineflag_gaze",            1.0, 19.0, 20.0),
    ("S14_bow_string_macro",         1.0, 20.0, 21.0),
    ("S15_alley_bamboo_hat",         1.0, 21.0, 22.0),
    ("S16_sleeve_sweep",             1.0, 22.0, 23.0),
    ("S17_boot_splash",              1.0, 23.0, 24.0),
    # 段4 低武动作 · 强快切 (24-34s)
    ("S18_blade_tip_in",             1.0, 24.0, 25.0),
    ("S19_bow_deflect",              1.0, 25.0, 26.0),
    ("S20_side_dodge",               1.0, 26.0, 27.0),
    ("S21_erhu_wrist_tap",           1.0, 27.0, 28.0),
    ("S22_rooftop_run",              1.0, 28.0, 29.0),
    ("S23_long_street_backlight",    1.0, 29.0, 30.0),
    ("S24_gourd_toss",               1.0, 30.0, 31.0),
    ("S25_erhu_wind",                1.0, 31.0, 32.0),
    ("S26_opponents_retreat",        1.0, 32.0, 33.0),
    ("S27_scabbard_tap",             1.0, 33.0, 34.0),
    # 段5 高光混剪 · 慢+快交替 (34-42s)
    ("S28_dusk_rooftop_wide",        1.5, 34.0, 35.5),
    ("S29_wind_smile_closeup",       1.5, 35.5, 37.0),
    ("S30_street_dash",              0.8, 37.0, 37.8),
    ("S31_bow_block_sword",          0.8, 37.8, 38.6),
    ("S32_bridge_lanterns_glance",   2.4, 38.6, 41.0),
    ("S33_wave_farewell",            1.0, 41.0, 42.0),
    # 段6 尾音收束 · 定格 (42-48.25s)
    ("S34_back_walkaway",            3.0, 42.0, 45.0),  # 3s Grok 自然走
    # S34 末帧后续用 tpad 冻结 3.25s + 淡出黑
]

SUBTITLES = [
    ("风来了。",              5.5,  7.5),
    ("我有一弦，清风作伴。",  39.0, 41.0),
    ("一弦在手，江湖随走。",  43.5, 46.5),
]

# (t_start, sfx_path, gain_db)
SFX_EVENTS = [
    (8.5,  "assets/sfx/whoosh/whoosh_air_pass.wav",       -18),
    (9.5,  "assets/sfx/riser/riser_short_ascending.wav",  -16),
    (23.2, "assets/sfx/hit/impact_soft_boom.wav",         -16),
    (24.5, "assets/sfx/tick/subtle_ui_tap_soft.wav",      -22),
    (25.4, "assets/sfx/hit/check_tick_soft.wav",          -14),
    (27.5, "assets/sfx/hit/impact_soft_boom.wav",         -14),
    (33.5, "assets/sfx/hit/check_tick_soft.wav",          -14),
    (38.0, "assets/sfx/hit/impact_hard_cut.wav",          -11),
]

FADE_OUT_START = 46.5
FADE_OUT_DURATION = 1.75


def run(*cmd: str) -> None:
    print(">", " ".join(cmd))
    subprocess.run(cmd, check=True)


def main() -> None:
    seg_dir = OUT / "assembly_segs"
    seg_dir.mkdir(exist_ok=True)

    # 裁每段
    for slug, dur, _, _ in CUTS:
        src = V / f"{slug}.mp4"
        dst = seg_dir / f"{slug}_seg.mp4"
        run(FFMPEG, "-y", "-loglevel", "error",
            "-i", str(src), "-t", str(dur),
            "-c:v", "libx264", "-preset", "fast", "-crf", "20",
            "-pix_fmt", "yuv420p", "-an", str(dst))

    # S34 末帧冻结 3.25s
    s34_seg = seg_dir / "S34_back_walkaway_seg.mp4"
    s34_extended = seg_dir / "S34_extended.mp4"
    run(FFMPEG, "-y", "-loglevel", "error",
        "-i", str(s34_seg),
        "-vf", "tpad=stop_mode=clone:stop_duration=3.25",
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-pix_fmt", "yuv420p", "-an", str(s34_extended))

    # 拼接 (S34 用 extended 版)
    concat_txt = seg_dir / "concat.txt"
    lines = []
    for slug, _, _, _ in CUTS:
        if slug == "S34_back_walkaway":
            lines.append("file 'S34_extended.mp4'")
        else:
            lines.append(f"file '{slug}_seg.mp4'")
    concat_txt.write_text("\n".join(lines))

    silent = OUT / "assembly_silent.mp4"
    run(FFMPEG, "-y", "-loglevel", "error",
        "-f", "concat", "-safe", "0", "-i", str(concat_txt),
        "-c", "copy", str(silent))

    # 烧字幕 + 淡出黑
    drawtext = ",".join(
        f"drawtext=fontfile={FONT}:text='{t}':fontsize=60:fontcolor=white:"
        f"borderw=3:bordercolor=black@0.7:x=(w-text_w)/2:y=h-text_h-180:"
        f"enable='between(t,{a},{b})'"
        for t, a, b in SUBTITLES
    )
    fade = f"fade=t=out:st={FADE_OUT_START}:d={FADE_OUT_DURATION}"
    subbed = OUT / "assembly_subbed.mp4"
    run(FFMPEG, "-y", "-loglevel", "error",
        "-i", str(silent), "-vf", f"{drawtext},{fade}",
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-pix_fmt", "yuv420p", "-an", str(subbed))

    # 原曲全长 48.25s
    audio = OUT / "assembly_audio.m4a"
    run(FFMPEG, "-y", "-loglevel", "error",
        "-i", str(SRC), "-t", str(TOTAL_DURATION), "-vn",
        "-c:a", "aac", "-b:a", "192k", str(audio))

    # 混音: 原曲 + 8 处 SFX
    # ffmpeg 命令构造: -i song + 每个 sfx -i · filter_complex 混合
    audio_mixed = OUT / "assembly_audio_mixed.m4a"
    ff_inputs = ["-i", str(audio)]
    for _, sfx_path, _ in SFX_EVENTS:
        ff_inputs += ["-i", str(ROOT / sfx_path)]

    # filter chain
    filters = []
    for i, (t, _, gain_db) in enumerate(SFX_EVENTS, start=1):
        delay_ms = int(t * 1000)
        filters.append(
            f"[{i}:a]adelay={delay_ms}|{delay_ms},volume={gain_db}dB[sfx{i}]"
        )
    sfx_labels = "".join(f"[sfx{i}]" for i in range(1, len(SFX_EVENTS) + 1))
    filters.append(
        f"[0:a]{sfx_labels}amix=inputs={len(SFX_EVENTS) + 1}:normalize=0:duration=first[aout]"
    )
    filter_complex = ";".join(filters)

    run(FFMPEG, "-y", "-loglevel", "error",
        *ff_inputs,
        "-filter_complex", filter_complex,
        "-map", "[aout]",
        "-c:a", "aac", "-b:a", "192k", str(audio_mixed))

    # 最终 mux
    final = OUT / "d06_wuxia_48s.mp4"
    run(FFMPEG, "-y", "-loglevel", "error",
        "-i", str(subbed), "-i", str(audio_mixed),
        "-map", "0:v:0", "-map", "1:a:0",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart", "-shortest", str(final))

    print(f"\n成片: {final}")


if __name__ == "__main__":
    main()
