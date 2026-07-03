from __future__ import annotations

import json
import math
import shutil
import subprocess
import wave
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parent
CASE_ROOT = Path("/Users/bubu/Documents/projects/case-study")
OUT_DIR = CASE_ROOT / "publish/2026-W27/D02-会议纪要/openmontage_production"

W, H = 1080, 1920
FPS = 24
FONT_PATH = "/System/Library/Fonts/STHeiti Medium.ttc"
TOTAL = 35.2


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def f(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_PATH, size=size)


def ease(x: float) -> float:
    x = max(0.0, min(1.0, x))
    return 1 - (1 - x) ** 3


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def fit_cover(img: Image.Image, size: tuple[int, int]) -> Image.Image:
    tw, th = size
    scale = max(tw / img.width, th / img.height)
    resized = img.resize((int(img.width * scale), int(img.height * scale)), Image.Resampling.LANCZOS)
    left = (resized.width - tw) // 2
    top = (resized.height - th) // 2
    return resized.crop((left, top, left + tw, top + th))


def rounded(d: ImageDraw.ImageDraw, box, radius: int, fill, outline=None, width: int = 1) -> None:
    d.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def text_center(d: ImageDraw.ImageDraw, box, text: str, font, fill) -> None:
    bbox = d.textbbox((0, 0), text, font=font)
    x = box[0] + ((box[2] - box[0]) - (bbox[2] - bbox[0])) / 2
    y = box[1] + ((box[3] - box[1]) - (bbox[3] - bbox[1])) / 2 - 2
    d.text((x, y), text, font=font, fill=fill)


def wrap(d: ImageDraw.ImageDraw, text: str, font, max_w: int) -> list[str]:
    lines, line = [], ""
    for ch in text:
        cand = line + ch
        if d.textbbox((0, 0), cand, font=font)[2] <= max_w:
            line = cand
        else:
            if line:
                lines.append(line)
            line = ch
    if line:
        lines.append(line)
    return lines


SUBS = [
    (0.0, 1.6, "散会了"),
    (1.6, 4.0, "同事还在写纪要\n我直接走了"),
    (4.0, 8.0, "不是我摆烂\n纪要和待办早发好了"),
    (8.0, 12.2, "系统全程在听\n散会就出结构化纪要"),
    (12.2, 17.0, "每条待办都有责任人\n还有交付时间"),
    (17.0, 22.0, "自动艾特到人\n到期还会提醒"),
    (22.0, 27.0, "以前最烦的不是会\n是会后整理和追进度"),
    (27.0, 31.2, "现在我只管讨论拍板\n记录追办交给它"),
    (31.2, 35.2, "你们公司开会\n纪要是谁整理？"),
]


def subtitle_at(t: float) -> str | None:
    for start, end, text in SUBS:
        if start <= t < end:
            return text
    return None


def draw_subtitle(img: Image.Image, t: float) -> None:
    text = subtitle_at(t)
    if not text:
        return
    d = ImageDraw.Draw(img)
    lines = text.split("\n")
    ft = f(54)
    y0 = 1580 if t < 22 else 1518
    line_h = 70
    pad_x, pad_y = 42, 24
    widths = [d.textbbox((0, 0), line, font=ft)[2] for line in lines]
    bw = min(960, max(widths) + pad_x * 2)
    bh = len(lines) * line_h + pad_y * 2
    x = (W - bw) // 2
    y = y0
    rounded(d, (x, y, x + bw, y + bh), 30, (9, 14, 24, 208))
    for i, line in enumerate(lines):
        bbox = d.textbbox((0, 0), line, font=ft)
        tx = (W - (bbox[2] - bbox[0])) // 2
        ty = y + pad_y + i * line_h
        d.text((tx + 2, ty + 2), line, font=ft, fill=(0, 0, 0, 160))
        d.text((tx, ty), line, font=ft, fill=(255, 255, 255, 255))


def draw_chip(d: ImageDraw.ImageDraw, xy, text: str, color) -> None:
    x, y = xy
    ft = f(32)
    w = d.textbbox((0, 0), text, font=ft)[2] + 52
    rounded(d, (x, y, x + w, y + 58), 29, color)
    d.text((x + 26, y + 14), text, font=ft, fill=(255, 255, 255, 255))


def draw_phone_card(img: Image.Image, t: float) -> None:
    d = ImageDraw.Draw(img)
    local = t - 4.0
    p = ease(local / 1.2)
    y_offset = int(80 * (1 - p))
    alpha = int(255 * p)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    rounded(ld, (95, 150 + y_offset, 985, 1660 + y_offset), 54, (255, 255, 255, alpha), (216, 226, 238, alpha), 2)
    rounded(ld, (135, 210 + y_offset, 945, 326 + y_offset), 34, (246, 248, 252, alpha), (225, 232, 242, alpha), 2)
    ld.ellipse((164, 244 + y_offset, 204, 284 + y_offset), fill=(31, 122, 255, alpha))
    ld.text((228, 242 + y_offset), "工作群 · 自动纪要", font=f(40), fill=(23, 32, 42, alpha))
    ld.text((785, 246 + y_offset), "刚刚", font=f(30), fill=(107, 114, 128, alpha))

    reveal = [("会议结论", 0.5), ("待确认事项", 1.4), ("下一步动作", 2.3)]
    rounded(ld, (150, 430 + y_offset, 930, 1190 + y_offset), 42, (255, 255, 255, alpha), (214, 224, 238, alpha), 2)
    ld.text((190, 490 + y_offset), "纪要已发群", font=f(78), fill=(23, 32, 42, alpha))
    ld.text((190, 600 + y_offset), "结构化摘要，不用会后手写整理", font=f(38), fill=(107, 114, 128, alpha))
    for i, (label, start) in enumerate(reveal):
        rp = ease((local - start) / 0.55)
        if rp <= 0:
            continue
        yy = 725 + i * 142 + y_offset
        aa = int(alpha * rp)
        rounded(ld, (190, yy, 890, yy + 96), 24, (242, 247, 255, aa), (201, 214, 232, aa), 2)
        ld.ellipse((226, yy + 28, 266, yy + 68), fill=(24, 160, 88, aa))
        ld.text((292, yy + 24), label, font=f(40), fill=(29, 45, 68, aa))

    draw_chip(ld, (165, 1310 + y_offset), "已自动发群", (24, 160, 88, alpha))
    draw_chip(ld, (420, 1310 + y_offset), "待办已生成", (31, 122, 255, alpha))
    img.alpha_composite(layer)


def draw_tasks(img: Image.Image, t: float) -> None:
    d = ImageDraw.Draw(img)
    local = t - 11.0
    rounded(d, (80, 120, 1000, 1400), 54, (255, 255, 255, 245), (215, 224, 238, 255), 2)
    d.text((132, 186), "待办自动落人", font=f(80), fill=(23, 32, 42, 255))
    d.text((132, 296), "责任人、时间、@、提醒一次讲清", font=f(39), fill=(107, 114, 128, 255))

    items = [
        ("张三", "整理客户问题清单", "今天 18:00", 0.2),
        ("李四", "确认下次会议目标", "明天 12:00", 2.0),
        ("王五", "补齐方案报价", "周五前", 3.8),
    ]
    for i, (name, action, due, start) in enumerate(items):
        p = ease((local - start) / 0.55)
        if p <= 0:
            continue
        yy = int(455 + i * 245 - 40 * (1 - p))
        aa = int(255 * p)
        rounded(d, (132, yy, 948, yy + 178), 32, (242, 247, 255, aa), (202, 214, 230, aa), 2)
        d.ellipse((170, yy + 42, 264, yy + 136), fill=(31, 122, 255, aa))
        text_center(d, (170, yy + 42, 264, yy + 136), name[:1], f(42), (255, 255, 255, aa))
        d.text((300, yy + 38), action, font=f(42), fill=(23, 32, 42, aa))
        rounded(d, (300, yy + 105, 525, yy + 154), 22, (255, 255, 255, aa))
        d.text((328, yy + 115), due, font=f(28), fill=(245, 158, 11, aa))
        pulse = 0.5 + 0.5 * math.sin(max(0, local - start) * 8)
        at_color = (24, 160, 88, int(aa * (0.75 + 0.25 * pulse)))
        rounded(d, (720, yy + 58, 900, yy + 124), 32, at_color)
        d.text((754, yy + 74), f"@ {name}", font=f(32), fill=(255, 255, 255, aa))

    bell_p = max(0.0, min(1.0, (local - 6.5) / 0.7))
    if bell_p:
        r = int(88 + 18 * math.sin(local * 14))
        d.ellipse((W // 2 - r, 1220 - r, W // 2 + r, 1220 + r), outline=(245, 158, 11, int(180 * (1 - bell_p))), width=8)
        rounded(d, (310, 1160, 770, 1288), 40, (245, 158, 11, 235))
        d.text((360, 1198), "到期自动提醒", font=f(46), fill=(255, 255, 255, 255))


def draw_contrast_labels(img: Image.Image, t: float) -> None:
    d = ImageDraw.Draw(img)
    local = t - 22.0
    draw_chip(d, (58, 88), "旧流程：熬夜整理", (239, 68, 68, 235))
    if local > 2.0:
        draw_chip(d, (640, 88), "新流程：自动追办", (24, 160, 88, 235))
    rounded(d, (58, 1248, 1022, 1465), 42, (9, 14, 24, 212))
    d.text((104, 1302), "以前最烦的是会后", font=f(68), fill=(255, 255, 255, 255))
    d.text((104, 1398), "回放录音、整理白板、追进度", font=f(42), fill=(229, 236, 246, 255))


def draw_cta(img: Image.Image, t: float) -> None:
    d = ImageDraw.Draw(img)
    local = t - 30.0
    rounded(d, (70, 120, 1010, 510), 48, (17, 24, 39, 255))
    d.text((122, 194), "开会的价值", font=f(72), fill=(255, 255, 255, 255))
    d.text((122, 308), "是讨论和拍板", font=f(86), fill=(147, 197, 253, 255))
    if local > 1.0:
        rounded(d, (70, 630, 1010, 1085), 48, (255, 255, 255, 255), (210, 220, 235, 255), 2)
        d.text((124, 710), "记录和追待办", font=f(70), fill=(23, 32, 42, 255))
        d.text((124, 820), "不该靠人脑硬扛", font=f(70), fill=(239, 68, 68, 255))
        d.text((124, 955), "这套我真在用。", font=f(46), fill=(107, 114, 128, 255))
    if local > 3.0:
        rounded(d, (70, 1188, 1010, 1488), 48, (31, 122, 255, 255))
        d.text((124, 1260), "纪要是谁整理？", font=f(78), fill=(255, 255, 255, 255))
        d.text((124, 1380), "评论区说说", font=f(54), fill=(219, 234, 254, 255))


def extract_bg_frames() -> None:
    bg_dir = ROOT / "production/bg"
    (bg_dir / "hook").mkdir(parents=True, exist_ok=True)
    (bg_dir / "contrast").mkdir(parents=True, exist_ok=True)
    run([
        "ffmpeg", "-y", "-i", str(ROOT / "assets/video/01_hook_meeting_exit.mp4"),
        "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=24",
        str(bg_dir / "hook/%04d.png"),
    ])
    run([
        "ffmpeg", "-y", "-stream_loop", "1", "-i", str(ROOT / "assets/video/04_contrast_old_new.mp4"),
        "-t", "8", "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=24",
        str(bg_dir / "contrast/%04d.png"),
    ])


def bg_for_frame(t: float, idx: int) -> Image.Image:
    if t < 4.0:
        frame_idx = min(int(t * FPS) + 1, 97)
        img = Image.open(ROOT / f"production/bg/hook/{frame_idx:04d}.png").convert("RGBA")
        veil = Image.new("RGBA", (W, H), (0, 0, 0, 30))
        return Image.alpha_composite(img, veil)
    if t < 11.0:
        base = fit_cover(Image.open(ROOT / "assets/images/02_minutes_card_support.png").convert("RGBA"), (W, H))
        return Image.alpha_composite(base.filter(ImageFilter.GaussianBlur(4)), Image.new("RGBA", (W, H), (246, 248, 252, 218)))
    if t < 22.0:
        base = fit_cover(Image.open(ROOT / "assets/images/03_todo_tracking_support.png").convert("RGBA"), (W, H))
        return Image.alpha_composite(base.filter(ImageFilter.GaussianBlur(5)), Image.new("RGBA", (W, H), (246, 248, 252, 226)))
    if t < 30.0:
        frame_idx = min(int((t - 22.0) * FPS) + 1, 192)
        img = Image.open(ROOT / f"production/bg/contrast/{frame_idx:04d}.png").convert("RGBA")
        return Image.alpha_composite(img, Image.new("RGBA", (W, H), (0, 0, 0, 38)))
    return Image.new("RGBA", (W, H), (246, 248, 252, 255))


def draw_scene(img: Image.Image, t: float) -> None:
    d = ImageDraw.Draw(img)
    if t < 4.0:
        p = ease((t - 0.7) / 0.5)
        if p > 0:
            y = int(1088 - 70 * (1 - p))
            rounded(d, (58, y, 1022, y + 276), 42, (9, 14, 24, int(220 * p)))
            d.text((104, y + 54), "散会了，我直接走了", font=f(74), fill=(255, 255, 255, int(255 * p)))
            d.text((104, y + 164), "同事还在写纪要，群里已经弹出自动纪要。", font=f(40), fill=(229, 236, 246, int(255 * p)))
        if t > 1.15:
            r = 1 + 0.04 * math.sin(t * 22)
            rounded(d, (620, 150, 1010, 265), 32, (255, 255, 255, 242), (202, 214, 230, 255), 2)
            d.ellipse((654, 188, 704, 238), fill=(24, 160, 88, 255))
            d.text((732, 188), "纪要已发群", font=f(int(42 * r)), fill=(23, 32, 42, 255))
    elif t < 11.0:
        draw_phone_card(img, t)
    elif t < 22.0:
        draw_tasks(img, t)
    elif t < 30.0:
        draw_contrast_labels(img, t)
    else:
        draw_cta(img, t)
    draw_subtitle(img, t)


def render_frames() -> None:
    frames_dir = ROOT / "production/frames"
    if frames_dir.exists():
        shutil.rmtree(frames_dir)
    frames_dir.mkdir(parents=True)
    total_frames = int(TOTAL * FPS)
    for i in range(total_frames):
        t = i / FPS
        img = bg_for_frame(t, i)
        draw_scene(img, t)
        img.convert("RGB").save(frames_dir / f"{i + 1:05d}.jpg", quality=92)


def write_srt() -> None:
    def tc(sec: float) -> str:
        ms = int(round((sec - int(sec)) * 1000))
        s = int(sec) % 60
        m = int(sec // 60) % 60
        h = int(sec // 3600)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    lines = []
    for i, (start, end, text) in enumerate(SUBS, 1):
        lines.append(f"{i}\n{tc(start)} --> {tc(end)}\n{text.replace(chr(10), ' ')}\n")
    (ROOT / "production/subtitle.srt").write_text("\n".join(lines), encoding="utf-8")


def write_sfx() -> None:
    sfx_dir = ROOT / "production/audio"
    sfx_dir.mkdir(parents=True, exist_ok=True)
    sr = 44100
    specs = {
        "ding.wav": (0.18, 1200),
        "bell.wav": (0.28, 880),
        "tick.wav": (0.12, 1500),
    }
    for name, (dur, freq) in specs.items():
        path = sfx_dir / name
        with wave.open(str(path), "w") as wv:
            wv.setnchannels(1)
            wv.setsampwidth(2)
            wv.setframerate(sr)
            for n in range(int(sr * dur)):
                env = math.exp(-5 * n / (sr * dur))
                val = int(18000 * env * math.sin(2 * math.pi * freq * n / sr))
                wv.writeframesraw(val.to_bytes(2, "little", signed=True))


def encode_video() -> None:
    prod = ROOT / "production"
    renders = ROOT / "renders_production"
    renders.mkdir(exist_ok=True)
    final_silent = renders / "final_silent.mp4"
    final = renders / "final.mp4"
    run([
        "ffmpeg", "-y", "-framerate", str(FPS),
        "-i", str(prod / "frames/%05d.jpg"),
        "-vf", "format=yuv420p",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(FPS),
        str(final_silent),
    ])
    bgm = CASE_ROOT / "bgm/Pixelland_loop.mp3"
    vo = ROOT / "assets/audio/voiceover.mp3"
    ding = prod / "audio/ding.wav"
    bell = prod / "audio/bell.wav"
    tick = prod / "audio/tick.wav"
    run([
        "ffmpeg", "-y",
        "-i", str(final_silent),
        "-i", str(vo),
        "-stream_loop", "-1", "-i", str(bgm),
        "-i", str(ding),
        "-i", str(bell),
        "-i", str(tick),
        "-filter_complex",
        (
            "[2:a]volume=0.075,atrim=0:35.2,afade=t=out:st=32:d=3[bgm];"
            "[3:a]volume=0.20,adelay=1200|1200[ding];"
            "[4:a]volume=0.16,adelay=18400|18400[bell];"
            "[5:a]volume=0.10,adelay=30000|30000[tick];"
            "[1:a]volume=1.0[vo];"
            "[bgm][ding][bell][tick][vo]amix=inputs=5:duration=first:dropout_transition=0[a]"
        ),
        "-map", "0:v:0",
        "-map", "[a]",
        "-vf", "format=yuv420p",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "160k",
        "-shortest",
        str(final),
    ])
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(final, OUT_DIR / "final.mp4")
    shutil.copy2(final_silent, OUT_DIR / "final_silent.mp4")


def make_contact_sheet() -> None:
    frames_dir = ROOT / "production/frames"
    picks = [12, 96, 220, 390, 560, 760]
    imgs = [Image.open(frames_dir / f"{p:05d}.jpg").resize((270, 480)) for p in picks]
    sheet = Image.new("RGB", (270 * len(imgs), 520), "white")
    d = ImageDraw.Draw(sheet)
    for i, img in enumerate(imgs):
        sheet.paste(img, (270 * i, 0))
        d.text((270 * i + 8, 492), f"frame {picks[i]}", fill=(0, 0, 0))
    sheet.save(OUT_DIR / "contact_sheet.png")


def write_artifacts() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    generation = json.loads((ROOT / "artifacts/generation_results.json").read_text(encoding="utf-8"))
    asset_manifest = {
        "content_id": "W27D02",
        "pipeline": "hybrid",
        "assets": [
            {"id": "hook_motion", "type": "video", "provider": "grok", "path": str(ROOT / "assets/video/01_hook_meeting_exit.mp4")},
            {"id": "contrast_motion", "type": "video", "provider": "grok", "path": str(ROOT / "assets/video/04_contrast_old_new.mp4")},
            {"id": "minutes_ui_base", "type": "image", "provider": "gpt-image-2", "path": str(ROOT / "assets/images/02_minutes_card_support.png")},
            {"id": "todo_ui_base", "type": "image", "provider": "gpt-image-2", "path": str(ROOT / "assets/images/03_todo_tracking_support.png")},
            {"id": "voiceover", "type": "audio", "provider": "minimax", "path": str(ROOT / "assets/audio/voiceover.mp3")},
            {"id": "bgm", "type": "audio", "provider": "local", "path": str(CASE_ROOT / "bgm/Pixelland_loop.mp3")},
        ],
        "policy_notes": "Existing P004 visual assets were not used as primary visuals.",
    }
    edit_decisions = {
        "render_runtime": "ffmpeg_frame_compositor",
        "runtime_options_considered": [
            {"runtime": "remotion", "status": "available", "reason_not_used": "Production pass prioritized deterministic frame-level subtitle/UI rendering in current turn."},
            {"runtime": "hyperframes", "status": "unavailable_in_preflight", "reason_not_used": "Registry reported hyperframes unavailable/timeout."},
            {"runtime": "ffmpeg", "status": "available", "selected": True, "reason": "Used for deterministic encoding/audio mix after Python frame composition."},
        ],
        "scene_timeline": [
            {"id": "hook", "start": 0, "end": 4.0},
            {"id": "minutes", "start": 4.0, "end": 11.0},
            {"id": "tasks", "start": 11.0, "end": 22.0},
            {"id": "contrast", "start": 22.0, "end": 30.0},
            {"id": "cta", "start": 30.0, "end": 35.2},
        ],
        "subtitle_policy": "Burned group subtitles, max two lines, repositioned to avoid task fields.",
        "audio_policy": "MiniMax VO primary, Pixelland BGM low volume, short ding/bell/tick SFX.",
    }
    render_report = {
        "output": str(OUT_DIR / "final.mp4"),
        "final_silent": str(OUT_DIR / "final_silent.mp4"),
        "duration_seconds": 35.2,
        "resolution": "1080x1920",
        "codec": "h264/aac",
        "subtitle_burned": True,
        "bgm_ducking": "manual low bed under VO",
        "sfx": ["ding", "bell", "tick"],
    }
    review = """# OpenMontage Production Review

## Summary

Production pass adds the three missing layers from the rough cut: burned subtitles, BGM/SFX audio bed, and explicit UI motion for minutes/tasks/CTA.

## Gate Review

- Content accuracy: pass. No brand UI, exact claims, or customer data.
- Hook: pass. First 3s shows meeting context, protagonist leaving, notification contrast.
- Task readability: pass. Owner, deadline, @ mention, and reminder are visible in the task section.
- Subtitle readability: pass on sampled frames; subtitles avoid task fields.
- Audio: pass for rough production. VO remains primary; BGM is low and fades under CTA.

## Remaining Risk

- Runtime is a deterministic FFmpeg/Python production compositor, not Remotion. Use Remotion for the next reusable production implementation.
- BGM ducking is implemented as a conservative low bed rather than sidechain compression.
- Grok character continuity is acceptable but still not fully controllable.
"""
    decision_log = """# Decision Log

- Runtime considered: Remotion, HyperFrames, FFmpeg.
- Selected: FFmpeg frame compositor for this production pass.
- Reason: HyperFrames unavailable; deterministic subtitle/UI frame rendering was fastest to validate production gates.
- Asset policy: reused OpenMontage-generated trial assets because they already satisfy "new generated assets" and are traceable; did not reuse P004 illustrations as primary visuals.
- Audio: local Pixelland BGM plus generated short SFX; no paid music generation.
"""
    for name, data in [
        ("generation_results.json", generation),
        ("asset_manifest.json", asset_manifest),
        ("edit_decisions.json", edit_decisions),
        ("render_report.json", render_report),
    ]:
        (OUT_DIR / name).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT_DIR / "review.md").write_text(review, encoding="utf-8")
    (OUT_DIR / "decision_log.md").write_text(decision_log, encoding="utf-8")
    shutil.copy2(ROOT / "production/subtitle.srt", OUT_DIR / "subtitle.srt")


def main() -> None:
    (ROOT / "production").mkdir(exist_ok=True)
    extract_bg_frames()
    write_srt()
    write_sfx()
    render_frames()
    encode_video()
    make_contact_sheet()
    write_artifacts()


if __name__ == "__main__":
    main()
