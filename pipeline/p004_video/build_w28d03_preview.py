#!/usr/bin/env python3
"""W28D03 ffmpeg 合成 · v2 底片版（无 BGM · 无叠字幕 · VO 覆盖 3-58s · 响度归一化）.

铁律（memory feedback_dense-vo-no-bgm-default · feedback_dense-vo-no-dead-air）:
- 0-3s 沉默钉子（环境音钉子，非死区）· 由 Pexels 深夜书桌 B-roll 提供环境
- 3-58s VO 全程覆盖，M7（36-42s）由真机豆包对话音填充（本脚本先用 05_facetime_awkward.png 占位，真机屏录到位后替换）
- 无 BGM · 外发命名走 build_platforms_w28d03.py 出 video_no_bgm.mp4

依赖：
- Pexels B-roll（已下载 · assets/broll/raw/）：
  - office_desk_dusk_evening_empty__26609644.mp4（M1 深夜书桌）
  - smartphone_screen_notification_night__32365211.mp4（M8 侧躺深夜）
- UI PNG（gen_ui_w28d03.py 生成 · 11 张）
- VO mp3 + seg_timing（gen_vo_w28d03.py 生成）

输出：publish/2026-W28/D03-AI陪练英语口语/build/final/preview_no_bgm_v2.mp4
"""
from __future__ import annotations

import json
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[2]
D03 = ROOT / "publish" / "2026-W28" / "D03-AI陪练英语口语"
BUILD = D03 / "build"
UI = BUILD / "assets_ui"
AUDIO = BUILD / "audio"
FINAL = BUILD / "final"
FINAL.mkdir(parents=True, exist_ok=True)
CLIPS = BUILD / "clips"
CLIPS.mkdir(parents=True, exist_ok=True)

BROLL = ROOT / "assets" / "broll" / "raw"
VO_MP3 = AUDIO / "vo_w28d03.mp3"
TIMING_PATH = AUDIO / "seg_timing_w28d03.json"

FFMPEG = "/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg"
FFPROBE = "/opt/homebrew/opt/ffmpeg-full/bin/ffprobe"

W, H, FPS = 1080, 1920, 30

# (M_id, [(src_type, src_path, sub_dur)], m_total_dur)
# src_type: img | broll
# 时长严格对齐 seg_timing_w28d03.json（VO 实测 · total 59.9s · 2026-07-04）
# 计划 vs 实测：s2 5→8.55s / s6 12→12.3s → 挤压 M7 到 1.7s（原 6s）
# M6/M7 若有真机豆包屏录 mov 到位，替换 08_role_prompt_full.png / 05_facetime_awkward.png
SCENES: list[tuple[str, list, float]] = [
    # M1 0-3s：Pexels 深夜书桌 B-roll（2s）+ 锁屏 23:12 UI（1s）
    ("M1_night_desk", [
        ("broll", BROLL / "office_desk_dusk_evening_empty__26609644.mp4", 2.0),
        ("img", UI / "01_lockscreen_2312.png", 1.0),
    ], 3.0),
    # M2 3-11.55s (s2 · 8.55s)：92% + 78% 群体锚定
    ("M2_group_anchor", [
        ("img", UI / "02_group_anchor_92.png", 4.28),
        ("img", UI / "03_group_anchor_78.png", 4.27),
    ], 8.55),
    # M3 11.55-18.95s (s3 · 7.4s)：700 天连击 + FaceTime 尴尬
    ("M3_streak_disillusion", [
        ("img", UI / "04_streak_700.png", 3.7),
        ("img", UI / "05_facetime_awkward.png", 3.7),
    ], 7.4),
    # M4 18.95-24s (s4 · 5.05s)：AI 错解 10 条废话
    ("M4_wrong_prompt", [
        ("img", UI / "06_ai_wrong_prompt.png", 5.05),
    ], 5.05),
    # M5 24-28s (s5 · 4s)：分屏类比 · 读教程 vs 跳进泳池
    ("M5_analogy_anchor", [
        ("img", UI / "07_analogy_split.png", 4.0),
    ], 4.0),
    # M6 28-40.3s (s6 · 12.3s)：role prompt 演示（原计划 12s，VO 溢出 0.3s 吸收）
    # ⚠ TODO 真机豆包屏录 mov 到位后，替换 08_role_prompt_full.png
    ("M6_prompt_demo", [
        ("img", UI / "08_role_prompt_full.png", 12.3),
    ], 12.3),
    # M7 40.3-42s (gap · 1.7s)：真陪练感占位（原计划 6s · s6 溢出压缩到 1.7s）
    # ⚠ TODO 真机豆包屏录 mov 到位后，此段应重新规划到 6s，需重跑 gen_vo_w28d03 加快 s2/s6
    ("M7_real_dialogue", [
        ("img", UI / "05_facetime_awkward.png", 1.7),
    ], 1.7),
    # M8 42-48s (s8 · 6s)：侧躺共同体
    ("M8_lying_side", [
        ("broll", BROLL / "smartphone_screen_notification_night__32365211.mp4", 3.0),
        ("img", UI / "09_lying_side_2245.png", 3.0),
    ], 6.0),
    # M9 48-54s (s9 · 6s)：价值锚 · 反教程 大字
    ("M9_value_anchor", [
        ("img", UI / "10_value_anchor.png", 6.0),
    ], 6.0),
    # M10 54-59.9s (s10 · 5.9s · 原计划 4s · s10 VO 溢出 1.9s)
    ("M10_cta_options", [
        ("img", UI / "11_cta_options.png", 5.9),
    ], 5.9),
]


def _run_img_clip(idx: int, src: pathlib.Path, dur: float) -> pathlib.Path:
    out = CLIPS / f"c{idx:02d}.mp4"
    subprocess.run([
        FFMPEG, "-y",
        "-loop", "1", "-i", str(src),
        "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
        "-t", f"{dur}",
        "-vf", (
            f"scale={W}:{H}:force_original_aspect_ratio=decrease,"
            f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:color=black,"
            f"setsar=1,fps={FPS}"
        ),
        "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k",
        "-shortest",
        str(out),
    ], capture_output=True, check=True)
    return out


def _run_broll_clip(idx: int, src: pathlib.Path, dur: float) -> pathlib.Path:
    out = CLIPS / f"c{idx:02d}.mp4"
    subprocess.run([
        FFMPEG, "-y",
        "-ss", "0", "-t", f"{dur}", "-i", str(src),
        "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
        "-t", f"{dur}",
        "-vf", (
            f"scale={W}:{H}:force_original_aspect_ratio=increase,"
            f"crop={W}:{H},setsar=1,fps={FPS}"
        ),
        "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k",
        "-map", "0:v", "-map", "1:a",
        "-shortest",
        str(out),
    ], capture_output=True, check=True)
    return out


def build_sub_clip(idx: int, src_type: str, src: pathlib.Path, dur: float) -> pathlib.Path:
    if not src.exists():
        raise FileNotFoundError(f"素材缺失: {src}")
    if src_type == "img":
        return _run_img_clip(idx, src, dur)
    return _run_broll_clip(idx, src, dur)


def concat_and_mix() -> pathlib.Path:
    idx = 0
    all_clips: list[pathlib.Path] = []
    for m_name, items, m_total in SCENES:
        for src_type, src, dur in items:
            clip = build_sub_clip(idx, src_type, src, dur)
            all_clips.append(clip)
            print(f"  ✓ c{idx:02d} · {m_name} · {src_type} · {src.name} · {dur}s")
            idx += 1

    listf = CLIPS / "concat.txt"
    listf.write_text("".join(f"file '{c}'\n" for c in all_clips))
    video_only = FINAL / "preview_video_only.mp4"
    subprocess.run([
        FFMPEG, "-y",
        "-f", "concat", "-safe", "0", "-i", str(listf),
        "-c", "copy",
        str(video_only),
    ], capture_output=True, check=True)
    print(f"\n✓ 视频轨拼接完成: {video_only}")

    if not VO_MP3.exists():
        print(f"⚠ VO 未生成: {VO_MP3}")
        print(f"  请先跑 gen_vo_w28d03.py。此次只出无声底片 {video_only}")
        return video_only

    vo_normalized = AUDIO / "vo_w28d03_loudnorm.mp3"
    subprocess.run([
        FFMPEG, "-y",
        "-i", str(VO_MP3),
        "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
        "-ar", "48000",
        str(vo_normalized),
    ], capture_output=True, check=True)
    print(f"✓ VO 响度归一化: {vo_normalized}")

    final = FINAL / "preview_no_bgm_v2.mp4"
    subprocess.run([
        FFMPEG, "-y",
        "-i", str(video_only),
        "-i", str(vo_normalized),
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k",
        "-map", "0:v:0", "-map", "1:a:0",
        "-shortest",
        str(final),
    ], capture_output=True, check=True)

    r = subprocess.run(
        [FFPROBE, "-v", "error", "-show_entries", "format=duration",
         "-of", "json", str(final)],
        capture_output=True, text=True, check=True,
    )
    total = float(json.loads(r.stdout)["format"]["duration"])
    print(f"\n✓ 底片合成完成 · 总长 {total:.2f}s")
    print(f"  输出: {final}")
    print(f"  下一步: gen_subs_w28d03.py → build_platforms_w28d03.py")
    return final


def sanity_check_timing() -> None:
    """比对 seg_timing 与 storyboard 计划，容差 ±0.5s 只警告不 hard fail."""
    if not TIMING_PATH.exists():
        print(f"⚠ seg_timing 未生成: {TIMING_PATH}")
        return
    data = json.loads(TIMING_PATH.read_text(encoding="utf-8"))
    total_seg = float(data.get("total", 0))
    total_plan = sum(m[2] for m in SCENES)
    delta = abs(total_seg - total_plan)
    print(f"\n[timing sanity]")
    print(f"  seg_timing 总长: {total_seg:.2f}s")
    print(f"  storyboard 计划: {total_plan:.2f}s")
    if delta > 1.0:
        print(f"  ⚠ 漂移 {delta:.2f}s > 1s · 建议手动核对分镜配比")
    else:
        print(f"  ✓ 漂移 {delta:.2f}s · 在容差内")


if __name__ == "__main__":
    print("→ D03 底片合成开始（Pexels B-roll + UI PNG + VO · 无 BGM · 无字幕）")
    print(f"  UI:  {UI}")
    print(f"  VO:  {VO_MP3}")
    print(f"  Out: {FINAL}")
    print()
    print("─ Sub-clips 生成 ─")
    concat_and_mix()
    sanity_check_timing()
