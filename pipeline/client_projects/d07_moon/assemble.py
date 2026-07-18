#!/usr/bin/env python3
"""D07 · 男厅《明月天涯》立绘卡点 MV · 方案 C(FFmpeg 自动合成).

客户借用能力单,与项目主旨分线(见 publish/2026-W30/D07/production_plan.md §7)。
本脚本不进 SYSTEM §4.2 候选清单,只服务本条客户交付。

流水线:
  Stage 1 · 15 个分镜片段(角色立绘 Ken-Burns 缓推 + 4 处场景背景板 xfade 揭幕)
  Stage 2 · concat 拼接(片段时长已精确对齐 SRT 起止,拼接后时间轴天然对齐歌词)
  Stage 3 · 一次性叠加: 大字歌词(竖排/横排,淡入淡出) + DV UI(第8段起) +
            动态时间码 + 【明月天涯】常驻小 tag + 高光段闪光 + 尾段淡出黑
  Stage 4 · mux 导唱 WAV(53.08s,-map 强制映射防音轨污染)
  Stage 5 · 拷贝到 publish/2026-W30/D07/final/ 交付

用法:
  python3 pipeline/client_projects/d07_moon/assemble.py            # 全流程
  python3 pipeline/client_projects/d07_moon/assemble.py --stage 1  # 只跑某阶段(调试用)
"""
from __future__ import annotations

import argparse
import subprocess
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
STILLS = ROOT / "tmp" / "d07_moon" / "stills"
BG_MOTION = ROOT / "tmp" / "d07_moon" / "bg_motion"  # grok-imagine-video i2v 生成,见 gen_bg_motion.py
OUT = ROOT / "tmp" / "d07_moon"
SEG_DIR = OUT / "assembly_segs"
WAV = ROOT / "publish" / "2026-W30" / "D07" / "明月天涯 导唱(1).WAV"
DV_UI = ROOT / "tmp" / "d07_moon" / "dv_ui_overlay.png"
FINAL_DIR = ROOT / "publish" / "2026-W30" / "D07" / "final"

FFMPEG = "/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg"
FFPROBE = "/opt/homebrew/opt/ffmpeg-full/bin/ffprobe"
FONT_HEAVY = "/Users/wmzuo/Library/Fonts/SourceHanSansSC-Heavy.otf"

W, H = 1920, 1080
FPS = 30
WAV_DURATION = 53.08
DV_UI_ON_FROM = 22.0
TIMECODE_BASE_OFFSET = 4478  # t=22.0 时显示 01:15:00,此后递增


@dataclass(frozen=True)
class Shot:
    slug: str
    start: float
    end: float
    text: str          # drawtext 用,竖排用 \n 隔字
    fontsize: int
    align: str          # "left" | "center"
    flash: bool = False
    dv_ui: bool = False
    bg_intro: str | None = None   # bg slug,仅 4 个场景开场镜头设(对应 bg_motion/<slug>.mp4 真动效素材)
    bg_intro_dur: float = 1.6     # 背景 i2v 片段展示时长,按镜头总时长留够角色画面再定
    zoom_max: float = 1.18        # 1.08~1.12 给多人全景镜头,避免裁太狠


SHOTS: tuple[Shot, ...] = (
    Shot("S01_xuanheng_flute_distant", 0.0, 3.5, "游\n侠", 130, "left",
         bg_intro="bg_mountain_night"),
    Shot("S02_xuanheng_side_moon", 3.5, 7.0, "江\n湖", 130, "left"),
    Shot("S03_zly_sword_back", 7.0, 9.8, "仇\n友", 130, "left"),
    Shot("S04_zly_face_sword", 9.8, 12.3, "敌\n手\n难", 120, "left"),
    Shot("S05_xh_zly_bridge_rain", 12.3, 15.8, "雨\n风", 130, "left",
         bg_intro="bg_bridge_rain", zoom_max=1.10),
    Shot("S06_flute_sword_clash", 15.8, 18.8, "狂\n澜", 165, "center",
         flash=True),
    Shot("S07_four_toast_silhouette", 18.8, 22.0, "皆醉了", 110, "center",
         zoom_max=1.08),
    Shot("S08_nolan_turn_back", 22.0, 25.0, "回\n首", 130, "left", dv_ui=True),
    Shot("S09_nolan_distant_moon", 25.0, 28.0, "明月", 150, "center", dv_ui=True,
         zoom_max=1.12),
    Shot("S10_cy_mountain_top", 28.0, 31.0, "天\n地", 130, "left", dv_ui=True),
    Shot("S11_cy_side_walk_street", 31.0, 34.0, "长安", 150, "center", dv_ui=True,
         bg_intro="bg_tavern_street", bg_intro_dur=1.3),
    Shot("S12_nolan_cy_tavern", 34.0, 37.0, "灯\n暖", 130, "left", dv_ui=True),
    Shot("S13_four_tavern_wide", 37.0, 40.0, "贪欢", 110, "center", dv_ui=True,
         zoom_max=1.08),
    Shot("S14_four_summit_clouds", 40.0, 46.0, "拂\n衣\n散", 170, "center",
         flash=True, dv_ui=True, bg_intro="bg_summit_moon", bg_intro_dur=2.6,
         zoom_max=1.12),
    Shot("S15_four_back_farewell", 46.0, 52.5, "江\n湖\n年\n少", 150, "center",
         dv_ui=True, zoom_max=1.10),
)

BG_XFADE_DUR_S = 0.4     # 交叉溶解时长
TAIL_FREEZE_EXTRA = WAV_DURATION - SHOTS[-1].end  # 补到与 WAV 等长
FADE_OUT_DUR = 1.6


def run(*cmd: str) -> None:
    print(">", " ".join(cmd))
    subprocess.run(cmd, check=True)


def _scale_crop_zoompan(zoom_max: float, dur: float, pan_dir: int = 0) -> str:
    """统一各尺寸立绘(1264x848/1536x1024/1672x941)到 1920x1080·30fps·缓推变焦+横向漂移.

    先放大 2x(3840 宽)再 zoompan 保清晰度;scale 按宽对齐、crop 只切上下
    (所有立绘都比 16:9 更"方",按宽走不会切到画面左右的人物构图)。
    zoom_max 之前定得太保守(1.02~1.05)+ 无横向漂移,3~7s 内几乎看不出变化,
    实际效果像静态 PPT;现改为居中变焦叠加横向 pan(pan_dir=+1/-1/0),
    漂移量按 zoom_max 算出的可用余量的 35% 取值,避免越界。
    """
    total_frames = max(round(dur * FPS), 1)
    zoom_rate = (zoom_max - 1.0) / total_frames
    x_expr = "(iw-iw/zoom)/2"
    if pan_dir:
        slack_px = 3840 * (1 - 1 / zoom_max)
        pan_px = slack_px * 0.35
        x_expr += f"+{pan_dir}*{pan_px:.1f}*(on/{total_frames})"
    return (
        f"scale=3840:-2:flags=lanczos,"
        f"crop=3840:2160,"
        f"zoompan=z='min(zoom+{zoom_rate:.8f},{zoom_max})':"
        f"x='{x_expr}':y='(ih-ih/zoom)/2':d=1:"
        f"s={W}x{H}:fps={FPS}"
    )


def build_char_clip(png: Path, dur: float, zoom_max: float, out: Path,
                     pan_dir: int = 0) -> None:
    vf = _scale_crop_zoompan(zoom_max, dur, pan_dir)
    run(FFMPEG, "-y", "-loglevel", "error",
        "-loop", "1", "-framerate", str(FPS), "-t", f"{dur:.3f}", "-i", str(png),
        "-vf", vf, "-frames:v", str(round(dur * FPS)),
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-pix_fmt", "yuv420p", str(out))


def build_bg_motion_clip(bg_mp4: Path, dur: float, out: Path) -> None:
    """背景开场用 grok-imagine-video 生成的真动效素材(云雾/雨丝/灯笼摇曳),
    只做尺寸/帧率归一(1280x720·24fps → 1920x1080·30fps),不再叠加 zoompan——
    素材本身已有画面内容运动,叠加镜头缓推是画蛇添足。
    """
    run(FFMPEG, "-y", "-loglevel", "error",
        "-i", str(bg_mp4),
        "-map", "0:v:0", "-t", f"{dur:.3f}",
        "-vf", f"scale={W}:{H}:flags=lanczos,fps={FPS}",
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-pix_fmt", "yuv420p", str(out))


def stage1_segments() -> None:
    SEG_DIR.mkdir(parents=True, exist_ok=True)
    for i, shot in enumerate(SHOTS):
        dur = shot.end - shot.start
        if i == len(SHOTS) - 1:
            dur += TAIL_FREEZE_EXTRA  # 末段冻结补到与 WAV 等长

        seg_out = SEG_DIR / f"{shot.slug}_seg.mp4"
        if seg_out.exists():
            print(f"skip 已存在: {seg_out.name}")
            continue

        png = STILLS / f"{shot.slug}.png"
        pan_dir = 1 if i % 2 == 0 else -1

        if shot.bg_intro:
            bg_mp4 = BG_MOTION / f"{shot.bg_intro}.mp4"
            bg_clip = SEG_DIR / f"{shot.slug}_bgintro.mp4"
            char_dur = dur - (shot.bg_intro_dur - BG_XFADE_DUR_S)
            char_clip = SEG_DIR / f"{shot.slug}_char.mp4"
            build_bg_motion_clip(bg_mp4, shot.bg_intro_dur, bg_clip)
            build_char_clip(png, char_dur, shot.zoom_max, char_clip, pan_dir)
            offset = shot.bg_intro_dur - BG_XFADE_DUR_S
            run(FFMPEG, "-y", "-loglevel", "error",
                "-i", str(bg_clip), "-i", str(char_clip),
                "-filter_complex",
                f"xfade=transition=fade:duration={BG_XFADE_DUR_S}:offset={offset:.3f}",
                "-c:v", "libx264", "-preset", "fast", "-crf", "18",
                "-pix_fmt", "yuv420p", str(seg_out))
        else:
            build_char_clip(png, dur, shot.zoom_max, seg_out, pan_dir)

        print(f"✓ 段 {i + 1}/{len(SHOTS)}: {seg_out.name} ({dur:.2f}s)")


def stage2_concat() -> Path:
    concat_txt = SEG_DIR / "concat.txt"
    lines = [f"file '{shot.slug}_seg.mp4'" for shot in SHOTS]
    concat_txt.write_text("\n".join(lines))

    silent = OUT / "assembly_silent.mp4"
    run(FFMPEG, "-y", "-loglevel", "error",
        "-f", "concat", "-safe", "0", "-i", str(concat_txt),
        "-c", "copy", str(silent))
    return silent


def _lyric_drawtext(shot: Shot) -> str:
    ts, te = shot.start, shot.end
    fade = 0.3
    alpha = (
        f"if(lt(t,{ts}),0,"
        f"if(lt(t,{ts}+{fade}),(t-{ts})/{fade},"
        f"if(lt(t,{te}-{fade}),1,"
        f"if(lt(t,{te}),({te}-t)/{fade},0))))"
    )
    y_drift = f"(h*0.5-text_h*0.5)-20*(1-min((t-{ts})/{fade}\\,1))"
    if shot.align == "left":
        x = "w*0.12"
        y = y_drift
    else:
        x = "(w-text_w)/2"
        y = f"(h*0.42-text_h*0.5)-20*(1-min((t-{ts})/{fade}\\,1))"

    text_escaped = shot.text.replace("'", "\\'")
    return (
        f"drawtext=fontfile={FONT_HEAVY}:text='{text_escaped}':"
        f"fontsize={shot.fontsize}:fontcolor=white:"
        f"borderw=4:bordercolor=black@0.75:line_spacing=8:"
        f"x={x}:y={y}:alpha='{alpha}':"
        f"enable='between(t,{ts},{te})'"
    )


def _flash_eq(shot: Shot) -> str:
    ts = shot.start
    return f"eq=brightness=0.22:enable='between(t,{ts},{ts + 0.12})'"


def stage3_overlays(silent: Path) -> Path:
    flash_filters = [_flash_eq(s) for s in SHOTS if s.flash]
    lyric_filters = [_lyric_drawtext(s) for s in SHOTS]

    timecode = (
        f"drawtext=fontfile={FONT_HEAVY}:"
        f"text='%{{pts\\:hms\\:{TIMECODE_BASE_OFFSET}}}':"
        f"fontsize=26:fontcolor=white@0.85:"
        f"x=(w-text_w)/2:y=996:"
        f"enable='gte(t,{DV_UI_ON_FROM})'"
    )
    static_tag = (
        f"drawtext=fontfile={FONT_HEAVY}:text='【明月天涯】':"
        f"fontsize=28:fontcolor=white@0.55:"
        f"x=w-text_w-42:y=h-70:"
        f"enable='gte(t,1.0)'"
    )
    tail_start = SHOTS[-1].end + TAIL_FREEZE_EXTRA - FADE_OUT_DUR
    fade = f"fade=t=out:st={tail_start:.3f}:d={FADE_OUT_DUR}"

    total_dur = SHOTS[-1].end + TAIL_FREEZE_EXTRA

    chain = flash_filters + [
        f"overlay=0:0:enable='gte(t,{DV_UI_ON_FROM})'"
    ]
    # overlay 需要两路输入,单独走 filter_complex;先把 flash 串到 [0:v]
    pre_overlay = ",".join(flash_filters) if flash_filters else "null"

    filter_complex = (
        f"[0:v]{pre_overlay}[vpre];"
        f"[vpre][1:v]overlay=0:0:enable='gte(t,{DV_UI_ON_FROM})'[vdv];"
        f"[vdv]{','.join(lyric_filters)}[vlyr];"
        f"[vlyr]{timecode}[vtc];"
        f"[vtc]{static_tag},{fade}[vout]"
    )

    subbed = OUT / "assembly_subbed.mp4"
    run(FFMPEG, "-y", "-loglevel", "error",
        "-i", str(silent), "-loop", "1", "-i", str(DV_UI),
        "-filter_complex", filter_complex,
        "-map", "[vout]", "-t", f"{total_dur:.3f}",
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-pix_fmt", "yuv420p", str(subbed))
    return subbed


def stage4_mux(subbed: Path) -> Path:
    total_dur = SHOTS[-1].end + TAIL_FREEZE_EXTRA
    audio = OUT / "assembly_audio.m4a"
    run(FFMPEG, "-y", "-loglevel", "error",
        "-i", str(WAV), "-t", f"{total_dur:.3f}",
        "-c:a", "aac", "-b:a", "192k", str(audio))

    final = OUT / "d07_moon_final.mp4"
    run(FFMPEG, "-y", "-loglevel", "error",
        "-i", str(subbed), "-i", str(audio),
        "-map", "0:v:0", "-map", "1:a:0",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart", "-shortest", str(final))
    return final


def stage5_deliver(final: Path) -> Path:
    FINAL_DIR.mkdir(parents=True, exist_ok=True)
    dst = FINAL_DIR / "d07_moon_final.mp4"
    run("cp", str(final), str(dst))
    return dst


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", type=int, default=0,
                         help="只跑某阶段(1-5),0=全部")
    args = parser.parse_args()

    if args.stage in (0, 1):
        stage1_segments()
    if args.stage == 1:
        return 0

    silent = OUT / "assembly_silent.mp4"
    if args.stage in (0, 2) or not silent.exists():
        silent = stage2_concat()
    if args.stage == 2:
        return 0

    subbed = OUT / "assembly_subbed.mp4"
    if args.stage in (0, 3) or not subbed.exists():
        subbed = stage3_overlays(silent)
    if args.stage == 3:
        return 0

    final = OUT / "d07_moon_final.mp4"
    if args.stage in (0, 4) or not final.exists():
        final = stage4_mux(subbed)
    if args.stage == 4:
        return 0

    dst = stage5_deliver(final)
    print(f"\n交付: {dst}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
