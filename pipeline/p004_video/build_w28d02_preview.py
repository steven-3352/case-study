#!/usr/bin/env python3
"""W28D02 ffmpeg 合成 · v2 预览版（无 BGM · 无叠字幕 · VO 覆盖 0-68s · 响度归一化）.

vB 变更（2026-07-04）：
- 沉默钉子已砍 · VO 从 0s 覆盖到底
- 新时长 68.91s（旧 67.91s）
- SCENES 逐段按新 seg_timing 重排
- 音轨叠加 loudnorm=I=-16:TP=-1.5:LRA=11（对齐参考视频响度）

按 seg_timing_w28d02.json 真实时长合成分镜画面 + VO。
输出：publish/2026-W28/D02-打工人5分钟出周报/build/final/preview_no_bgm_v2.mp4

注意：按 SYSTEM §2.4b，无 BGM 不叠字幕的初版只作 build/ 临时预览，
不得写成 douyin/video.mp4 发布候选。BGM + 字幕 + 三平台适配统一去剪映做。
"""
from __future__ import annotations

import json
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[2]
D02 = ROOT / "publish" / "2026-W28" / "D02-打工人5分钟出周报"
BUILD = D02 / "build"
UI = BUILD / "assets_ui"
AUDIO = BUILD / "audio"
FINAL = BUILD / "final"
FINAL.mkdir(parents=True, exist_ok=True)
CLIPS = BUILD / "clips"
CLIPS.mkdir(parents=True, exist_ok=True)

BROLL = ROOT / "assets" / "broll" / "raw"
VO_MP3 = AUDIO / "vo_w28d02.mp3"
TIMING = json.loads((AUDIO / "seg_timing_w28d02.json").read_text())

W, H, FPS = 1080, 1920, 30

# (id, [(src_type, src_path, sub_dur)], total_dur)
# src_type: img | broll
# 时长对齐 seg_timing_w28d02.json（vB · 8 段 · 68.91s）
SCENES: list[tuple[str, list, float]] = [
    # M1 0-3.69s (s1 · 3.69s)：Pexels 傍晚办公室
    ("M1_office_dusk", [
        ("broll", BROLL / "office_desk_dusk_evening_empty__26609644.mp4", 3.69),
    ], 3.69),
    # M2 3.69-6.80s (s2 · 3.11s)：iPhone 锁屏 → 微信通知 → Excel 空白
    ("M2_lockscreen_ping_excel", [
        ("img", UI / "01_iphone_lockscreen_1855.png", 1.04),
        ("img", UI / "02_wechat_boss_ping.png", 1.04),
        ("img", UI / "03_excel_empty.png", 1.03),
    ], 3.11),
    # M3 6.80-19.20s (s3 · 12.4s)：痛点点破 + 反例
    ("M3_pain_and_wrong", [
        ("img", UI / "03_excel_empty.png", 4.0),
        ("img", UI / "04_ai_wrong_prompt.png", 8.4),
    ], 12.4),
    # M4 19.20-29.19s (s4 · 9.99s)：反转 · 素材拖入
    ("M4_reverse_dump", [
        ("img", UI / "06_memo_random.png", 3.33),
        ("img", UI / "07_wechat_group.png", 3.33),
        ("img", UI / "08_calendar_week.png", 3.33),
    ], 9.99),
    # M5 29.19-46.76s (s5 · 17.57s)：黄金 prompt 五段全屏
    ("M5_gold_prompt_demo", [
        ("img", UI / "05_ai_gold_prompt.png", 17.57),
    ], 17.57),
    # M6 46.76-57.46s (s6 · 10.7s)：前后对比
    ("M6_before_after", [
        ("img", UI / "09_raw_annotated.png", 5.35),
        ("img", UI / "10_ai_organized.png", 5.35),
    ], 10.7),
    # M7 57.46-64.26s (s7 · 6.8s)：价值锚 + 傍晚窗外
    ("M7_value_anchor", [
        ("broll", BROLL / "city_window_dusk_sunset_evening_lights__26346258.mp4", 3.4),
        ("img", UI / "11_value_anchor.png", 3.4),
    ], 6.8),
    # M8 64.26-68.51s (s8 · 4.25s)：CTA
    ("M8_cta", [
        ("img", UI / "12_cta_note.png", 4.25),
    ], 4.25),
]


def to_clip(idx: int, src_type: str, src: pathlib.Path, dur: float) -> pathlib.Path:
    out = CLIPS / f"c{idx:02d}.mp4"
    if src_type == "img":
        # PNG loop → mp4 with silent audio
        # scale + pad to 1080x1920 (画布已按 W/H 出)
        subprocess.run([
            "ffmpeg", "-y",
            "-loop", "1", "-i", str(src),
            "-f", "lavfi", "-i", f"anullsrc=r=48000:cl=stereo",
            "-t", f"{dur}",
            "-vf", f"scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1,fps={FPS}",
            "-c:v", "libx264", "-preset", "medium", "-crf", "20",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "128k",
            "-shortest",
            str(out),
        ], capture_output=True, check=True)
    else:  # broll
        # crop + scale 到 1080×1920 · trim 到 dur · 静音
        # 用 force_original_aspect_ratio=increase 保证短边>=目标，再中心 crop
        subprocess.run([
            "ffmpeg", "-y",
            "-ss", "0", "-t", f"{dur}", "-i", str(src),
            "-f", "lavfi", "-i", f"anullsrc=r=48000:cl=stereo",
            "-t", f"{dur}",
            "-vf", f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,fps={FPS}",
            "-c:v", "libx264", "-preset", "medium", "-crf", "20",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "128k",
            "-map", "0:v", "-map", "1:a",
            "-shortest",
            str(out),
        ], capture_output=True, check=True)
    return out


def concat_and_mix() -> pathlib.Path:
    # 收集所有 sub-clips
    idx = 0
    all_clips: list[pathlib.Path] = []
    for m_name, items, m_total in SCENES:
        for src_type, src, dur in items:
            all_clips.append(to_clip(idx, src_type, src, dur))
            print(f"  ✓ c{idx:02d} · {m_name} · {src_type} · {src.name} · {dur}s")
            idx += 1

    # concat 全部段
    listf = CLIPS / "concat.txt"
    listf.write_text("".join(f"file '{c}'\n" for c in all_clips))
    video_only = FINAL / "preview_video_only.mp4"
    subprocess.run([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", str(listf),
        "-c", "copy",
        str(video_only),
    ], capture_output=True, check=True)
    print(f"\n✓ 视频轨拼接完成: {video_only}")

    # VO 响度归一化（对齐参考视频 -13~-23dB 范围 · loudnorm I=-16 TP=-1.5 LRA=11）
    vo_normalized = AUDIO / "vo_w28d02_loudnorm.mp3"
    subprocess.run([
        "ffmpeg", "-y",
        "-i", str(VO_MP3),
        "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
        "-ar", "48000",
        str(vo_normalized),
    ], capture_output=True, check=True)
    print(f"✓ VO 响度归一化: {vo_normalized}")

    # 用归一化后 VO 替换整段音轨 → v2
    final = FINAL / "preview_no_bgm_v2.mp4"
    subprocess.run([
        "ffmpeg", "-y",
        "-i", str(video_only),
        "-i", str(vo_normalized),
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k",
        "-map", "0:v:0", "-map", "1:a:0",
        "-shortest",
        str(final),
    ], capture_output=True, check=True)

    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "json", str(final)],
        capture_output=True, text=True,
    )
    total = float(json.loads(r.stdout)["format"]["duration"])
    print(f"\n✓ 预览版合成完成 · 总长 {total:.2f}s")
    print(f"  输出: {final}")
    return final


if __name__ == "__main__":
    print(f"→ D02 preview 合成开始")
    print(f"  UI 素材: {UI}")
    print(f"  VO: {VO_MP3}")
    print(f"  输出: {FINAL}")
    print()
    print("─ Sub-clips 生成 ─")
    concat_and_mix()
