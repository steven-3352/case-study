"""Render a short two-shot paperdoll MVP from real project inputs."""

from __future__ import annotations

import math
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


class MvpRenderError(RuntimeError):
    pass


_LRC = re.compile(r"^\[(\d+):(\d+(?:\.\d+)?)\](.*)$")


def _lyrics(path):
    rows = []
    for raw in Path(path).read_text(encoding="utf-8-sig").splitlines():
        match = _LRC.match(raw.strip())
        if match and match.group(3).strip():
            rows.append((int(match.group(1)) * 60 + float(match.group(2)), match.group(3).strip()))
    if len(rows) < 2:
        raise MvpRenderError("two timed lyric lines are required")
    return rows


def _font(size, serif=False):
    path = "/System/Library/Fonts/Supplemental/Songti.ttc" if serif else "/System/Library/Fonts/PingFang.ttc"
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default()


def _fit_character(path, target_height):
    image = Image.open(path).convert("RGBA")
    box = image.getbbox()
    if box:
        image = image.crop(box)
    scale = target_height / image.height
    return image.resize((max(1, round(image.width * scale)), target_height), Image.Resampling.LANCZOS)


def _background(size, shot):
    width, height = size
    base = Image.new("RGB", size, (239, 235, 224) if shot == 0 else (226, 221, 209))
    draw = ImageDraw.Draw(base, "RGBA")
    if shot == 0:
        draw.rectangle((0, 0, width, 88), fill=(33, 34, 31, 255))
        draw.rectangle((42, 128, 54, height - 76), fill=(170, 48, 39, 230))
        for index in range(7):
            y = 190 + index * 102
            draw.arc((-120 + index * 17, y, width + 80, y + 180), 190, 340,
                     fill=(52, 76, 64, 70), width=3)
    else:
        draw.polygon(((0, 0), (width, 0), (width, 330), (0, 520)), fill=(44, 43, 39, 255))
        draw.rectangle((width - 64, 80, width - 48, height - 64), fill=(170, 48, 39, 235))
        for index in range(5):
            x = 34 + index * 105
            draw.ellipse((x, 680 + (index % 2) * 38, x + 58, 738 + (index % 2) * 38),
                         outline=(189, 144, 55, 130), width=2)
    return base


def _caption(frame, title, lyric, shot):
    draw = ImageDraw.Draw(frame, "RGBA")
    width, height = frame.size
    title_font = _font(26, serif=True)
    lyric_font = _font(25, serif=True)
    small_font = _font(12)
    if shot == 0:
        draw.text((28, 26), title, font=title_font, fill=(245, 241, 232, 255))
        draw.text((width - 86, 32), "TWO SHOT TEST", font=small_font, fill=(210, 202, 185, 255), anchor="ra")
    else:
        draw.text((28, 34), title, font=title_font, fill=(245, 241, 232, 255))
        draw.text((28, 74), "MVP / 02", font=small_font, fill=(200, 182, 149, 255))
    lyric_box = draw.textbbox((0, 0), lyric, font=lyric_font)
    text_width = lyric_box[2] - lyric_box[0]
    pad = 16
    x = max(24, (width - text_width) // 2)
    y = height - 92
    draw.rounded_rectangle((x - pad, y - 10, x + text_width + pad, y + 43), radius=4,
                           fill=(24, 24, 22, 205))
    draw.text((x, y), lyric, font=lyric_font, fill=(250, 247, 239, 255))


def render_two_shot_mvp(audio_path, lyrics_path, character_paths, destination, ffmpeg=None, ffprobe=None):
    ffmpeg = ffmpeg or os.environ.get("MVSTUDIO_FFMPEG_PATH") or shutil.which("ffmpeg")
    ffprobe = ffprobe or os.environ.get("MVSTUDIO_FFPROBE_PATH") or shutil.which("ffprobe")
    if not ffmpeg or not ffprobe:
        raise MvpRenderError("ffmpeg and ffprobe are required")
    characters = sorted({Path(path).stem.split("-")[0]: Path(path) for path in character_paths}.items())
    if len(characters) < 2:
        raise MvpRenderError("two distinct character images are required")
    lyric_rows = _lyrics(lyrics_path)
    start = lyric_rows[0][0]
    boundary = lyric_rows[1][0]
    end = lyric_rows[2][0] if len(lyric_rows) > 2 else boundary + 6.0
    duration = max(6.0, min(14.0, end - start))
    split = max(2.5, min(duration - 2.5, boundary - start))
    fps, size = 12, (540, 960)
    first = _fit_character(characters[0][1], 790)
    second = _fit_character(characters[1][1], 760)
    total_frames = round(duration * fps)
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="mvp-two-shot-", dir=str(destination.parent)) as raw:
        temporary = Path(raw)
        frames = temporary / "frames"
        frames.mkdir()
        for index in range(total_frames):
            elapsed = index / fps
            shot = 0 if elapsed < split else 1
            local = elapsed if shot == 0 else elapsed - split
            shot_duration = split if shot == 0 else duration - split
            progress = min(1.0, local / max(shot_duration, 0.001))
            frame = _background(size, shot).convert("RGBA")
            draw = ImageDraw.Draw(frame, "RGBA")
            pulse = math.sin(local * math.pi * 1.1)
            for petal in range(12):
                phase = (petal * 0.083 + local * (0.10 + petal % 3 * 0.015)) % 1
                x = int((petal * 97 + local * 31) % 610) - 35
                y = int(90 + phase * 760)
                draw.ellipse((x, y, x + 7, y + 14), fill=(170, 48, 39, 80 + petal * 8))
            if shot == 0:
                a_scale = 0.74 + 0.05 * progress
                b_scale = 0.62 + 0.04 * (1 - progress)
                a = first.resize((round(first.width * a_scale), round(first.height * a_scale)), Image.Resampling.LANCZOS)
                b = second.resize((round(second.width * b_scale), round(second.height * b_scale)), Image.Resampling.LANCZOS)
                frame.alpha_composite(b, (330 - b.width // 2 + round(8 * pulse), 180 - round(10 * pulse)))
                frame.alpha_composite(a, (84 - a.width // 2 - round(12 * pulse), 216 + round(8 * pulse)))
            else:
                a_scale = 0.82 + 0.07 * progress
                b_scale = 0.50 + 0.05 * progress
                a = second.resize((round(second.width * a_scale), round(second.height * a_scale)), Image.Resampling.LANCZOS)
                b = first.resize((round(first.width * b_scale), round(first.height * b_scale)), Image.Resampling.LANCZOS)
                shadow = a.getchannel("A").filter(ImageFilter.GaussianBlur(10))
                shade = Image.new("RGBA", a.size, (22, 20, 18, 0)); shade.putalpha(shadow.point(lambda value: value // 3))
                frame.alpha_composite(shade, (246 - a.width // 2 + 12, 182 + 12))
                frame.alpha_composite(a, (246 - a.width // 2 + round(10 * pulse), 182 - round(8 * pulse)))
                frame.alpha_composite(b, (448 - b.width // 2 - round(7 * pulse), 360 + round(5 * pulse)))
            lyric = lyric_rows[0][1] if shot == 0 else lyric_rows[1][1]
            _caption(frame, "青衣", lyric, shot)
            frame.convert("RGB").save(frames / f"f{index:05d}.jpg", quality=92, subsampling=0)

        target = temporary / "final.mp4"
        command = [
            ffmpeg, "-v", "error", "-framerate", str(fps), "-i", str(frames / "f%05d.jpg"),
            "-ss", f"{start:.3f}", "-i", str(audio_path), "-t", f"{duration:.3f}",
            "-map", "0:v:0", "-map", "1:a:0", "-c:v", "libx264", "-preset", "medium",
            "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
            "-movflags", "+faststart", "-shortest", "-y", str(target),
        ]
        completed = subprocess.run(command, capture_output=True, text=True, timeout=240, check=False)
        if completed.returncode:
            raise MvpRenderError("ffmpeg failed to encode the two-shot MVP")
        os.replace(target, destination)

    probe = subprocess.run([
        ffprobe, "-v", "error", "-show_entries", "stream=codec_type,width,height:format=duration",
        "-of", "json", str(destination),
    ], capture_output=True, text=True, timeout=30, check=False)
    if probe.returncode:
        raise MvpRenderError("ffprobe failed to validate the two-shot MVP")
    return {"duration": duration, "width": size[0], "height": size[1], "fps": fps,
            "shot_count": 2, "audio_present": True, "source_audio_offset": start}
