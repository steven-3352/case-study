from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parent
CASE_STUDY_OUT = Path("/Users/bubu/Documents/projects/case-study/publish/2026-W27/D02-会议纪要/openmontage_true")
W, H = 1080, 1920
FONT = "/System/Library/Fonts/STHeiti Medium.ttc"


def font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT, size=size)


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def rounded(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], radius: int, fill, outline=None, width: int = 1) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def fit_cover(img: Image.Image, size: tuple[int, int]) -> Image.Image:
    target_w, target_h = size
    scale = max(target_w / img.width, target_h / img.height)
    resized = img.resize((int(img.width * scale), int(img.height * scale)), Image.Resampling.LANCZOS)
    left = (resized.width - target_w) // 2
    top = (resized.height - target_h) // 2
    return resized.crop((left, top, left + target_w, top + target_h))


def wrap_text(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    lines: list[str] = []
    line = ""
    for ch in text:
        candidate = line + ch
        if draw.textbbox((0, 0), candidate, font=fnt)[2] <= max_width:
            line = candidate
        else:
            if line:
                lines.append(line)
            line = ch
    if line:
        lines.append(line)
    return lines


def draw_text_block(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    fnt: ImageFont.FreeTypeFont,
    fill,
    max_width: int,
    line_gap: int = 12,
) -> int:
    x, y = xy
    for line in wrap_text(draw, text, fnt, max_width):
        draw.text((x, y), line, font=fnt, fill=fill)
        y += draw.textbbox((0, 0), line, font=fnt)[3] + line_gap
    return y


def save_overlay(name: str, title: str, subtitle: str, badge: str | None = None) -> Path:
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if badge:
        rounded(d, (52, 80, 360, 148), 34, (18, 125, 99, 235))
        d.text((82, 98), badge, font=font(36), fill=(255, 255, 255, 255))
    rounded(d, (52, 1320, 1028, 1780), 42, (18, 24, 38, 218))
    d.text((96, 1370), title, font=font(74), fill=(255, 255, 255, 255))
    draw_text_block(d, (96, 1490), subtitle, font(44), (229, 236, 246, 255), 880, 16)
    out = ROOT / "assets/overlays" / name
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out)
    return out


def scene_card(name: str, bg_path: Path, title: str, body: str, bullets: list[str], accent=(37, 99, 235)) -> Path:
    bg = fit_cover(Image.open(bg_path).convert("RGB"), (W, H))
    bg = bg.filter(ImageFilter.GaussianBlur(2))
    veil = Image.new("RGBA", (W, H), (246, 248, 252, 196))
    img = Image.alpha_composite(bg.convert("RGBA"), veil)
    d = ImageDraw.Draw(img)

    rounded(d, (70, 88, 1010, 226), 36, (255, 255, 255, 242), (219, 226, 236, 255), 2)
    d.ellipse((106, 126, 154, 174), fill=accent + (255,))
    d.text((178, 124), "工作群 · 自动纪要", font=font(40), fill=(25, 35, 52, 255))
    d.text((800, 126), "刚刚", font=font(32), fill=(104, 116, 133, 255))

    rounded(d, (70, 300, 1010, 1410), 44, (255, 255, 255, 248), (213, 222, 235, 255), 2)
    d.text((118, 360), title, font=font(74), fill=(17, 24, 39, 255))
    y = draw_text_block(d, (118, 485), body, font(42), (71, 85, 105, 255), 830, 18)
    y += 40
    for item in bullets:
        rounded(d, (118, y, 962, y + 132), 30, (242, 247, 255, 255), (202, 214, 230, 255), 2)
        d.ellipse((154, y + 42, 202, y + 90), fill=(34, 197, 94, 255))
        d.text((222, y + 38), item, font=font(38), fill=(29, 45, 68, 255))
        y += 158

    rounded(d, (86, 1548, 994, 1762), 40, (15, 23, 42, 234))
    d.text((132, 1595), "人负责讨论拍板", font=font(56), fill=(255, 255, 255, 255))
    d.text((132, 1680), "AI 负责记录追办", font=font(56), fill=(147, 197, 253, 255))

    out = ROOT / "assets/overlays" / name
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out)
    return out


def value_cta_card() -> Path:
    img = Image.new("RGBA", (W, H), (246, 248, 252, 255))
    d = ImageDraw.Draw(img)
    rounded(d, (70, 132, 1010, 520), 48, (17, 24, 39, 255))
    d.text((122, 204), "开会的价值", font=font(72), fill=(255, 255, 255, 255))
    d.text((122, 318), "是讨论和拍板", font=font(86), fill=(147, 197, 253, 255))

    rounded(d, (70, 650, 1010, 1180), 48, (255, 255, 255, 255), (210, 220, 235, 255), 2)
    d.text((124, 725), "记录和追待办", font=font(72), fill=(17, 24, 39, 255))
    d.text((124, 840), "根本不该是人干的活", font=font(64), fill=(220, 38, 38, 255))
    d.line((124, 980, 940, 980), fill=(226, 232, 240, 255), width=3)
    d.text((124, 1048), "这套我真在用。", font=font(50), fill=(71, 85, 105, 255))

    rounded(d, (70, 1340, 1010, 1770), 48, (37, 99, 235, 255))
    d.text((124, 1415), "你们公司开会", font=font(66), fill=(255, 255, 255, 255))
    d.text((124, 1514), "纪要是谁整理？", font=font(76), fill=(255, 255, 255, 255))
    d.text((124, 1630), "评论区吐槽一句", font=font(48), fill=(219, 234, 254, 255))

    out = ROOT / "assets/overlays/05_value_cta.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out)
    return out


def make_video_scene(src_video: Path, overlay: Path, out: Path, duration: float, loop: int = 0) -> None:
    cmd = [
        "ffmpeg", "-y",
    ]
    if loop:
        cmd += ["-stream_loop", str(loop)]
    cmd += [
        "-i", str(src_video),
        "-i", str(overlay),
        "-t", str(duration),
        "-filter_complex",
        "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1[bg];"
        "[bg][1:v]overlay=0:0,format=yuv420p[v]",
        "-map", "[v]",
        "-an",
        "-r", "24",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        str(out),
    ]
    run(cmd)


def make_image_scene(src_png: Path, out: Path, duration: float) -> None:
    run([
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", str(src_png),
        "-t", str(duration),
        "-vf", "scale=1080:1920,format=yuv420p",
        "-an",
        "-r", "24",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        str(out),
    ])


def concat_and_audio(scene_paths: list[Path], audio: Path, out: Path) -> None:
    concat_file = ROOT / "assets/overlays/concat.txt"
    concat_file.write_text("".join(f"file '{p.resolve()}'\n" for p in scene_paths), encoding="utf-8")
    silent = ROOT / "renders/final_silent.mp4"
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file), "-c", "copy", str(silent)])
    run([
        "ffmpeg", "-y",
        "-i", str(silent),
        "-i", str(audio),
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "160k",
        "-shortest",
        str(out),
    ])


def main() -> None:
    overlays = ROOT / "assets/overlays"
    scenes = ROOT / "assets/scenes"
    renders = ROOT / "renders"
    for d in (overlays, scenes, renders, CASE_STUDY_OUT):
        d.mkdir(parents=True, exist_ok=True)

    scene1_overlay = save_overlay(
        "01_hook_overlay.png",
        "散会了，我直接走了",
        "同事还在写纪要，群里已经弹出自动纪要。",
        "0-3s 停划",
    )
    scene2 = scene_card(
        "02_minutes_card.png",
        ROOT / "assets/images/02_minutes_card_support.png",
        "纪要已发群",
        "不是我摆烂，是系统已经把会议信息整理成结构化纪要。",
        ["关键结论", "争议点", "下一步"],
    )
    scene3 = scene_card(
        "03_todo_card.png",
        ROOT / "assets/images/03_todo_tracking_support.png",
        "待办自动落人",
        "每条任务都带责任人、时间和提醒，不再靠会后人肉追进度。",
        ["@ 张三 · 今天 18:00", "@ 李四 · 明天 12:00", "到期自动提醒"],
        accent=(22, 163, 74),
    )
    scene4_overlay = save_overlay(
        "04_contrast_overlay.png",
        "以前最烦的是会后",
        "回放录音、整理白板、追每个人要进度。",
        "反差",
    )
    scene5 = value_cta_card()

    scene_paths = [
        scenes / "01_hook.mp4",
        scenes / "02_minutes.mp4",
        scenes / "03_todo.mp4",
        scenes / "04_contrast.mp4",
        scenes / "05_cta.mp4",
    ]
    make_video_scene(ROOT / "assets/video/01_hook_meeting_exit.mp4", scene1_overlay, scene_paths[0], 4.0)
    make_image_scene(scene2, scene_paths[1], 7.0)
    make_image_scene(scene3, scene_paths[2], 11.0)
    make_video_scene(ROOT / "assets/video/04_contrast_old_new.mp4", scene4_overlay, scene_paths[3], 8.0, loop=1)
    make_image_scene(scene5, scene_paths[4], 5.2)

    final = renders / "final.mp4"
    concat_and_audio(scene_paths, ROOT / "assets/audio/voiceover.mp3", final)
    shutil.copy2(final, CASE_STUDY_OUT / "final.mp4")

    report = {
        "pipeline": "hybrid",
        "render_runtime": "ffmpeg_composition_with_openmontage_assets",
        "duration_target_seconds": 35.2,
        "output": str(final),
        "case_study_output": str(CASE_STUDY_OUT / "final.mp4"),
        "scene_paths": [str(p) for p in scene_paths],
        "source_support_mix": {
            "anchor_medium": "grok_generated_workplace_video",
            "support_layers": ["gpt-image-2 UI support cards", "Chinese overlay cards", "MiniMax narration"],
            "ratio": "2 generated-video anchor scenes / 3 support-led scenes",
        },
    }
    (ROOT / "artifacts/render_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    shutil.copy2(ROOT / "artifacts/render_report.json", CASE_STUDY_OUT / "render_report.json")


if __name__ == "__main__":
    main()
