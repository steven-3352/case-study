"""Low-cost 540p structural animatic rendering."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


class AnimaticError(RuntimeError):
    pass


def _dimensions(canvas):
    return (540, 960) if canvas == "9:16" else (960, 540)


def _shot_card(shot, size, destination):
    width, height = size
    energy = int(shot["energy"])
    backgrounds = ((235, 232, 224), (221, 228, 218), (232, 220, 205),
                   (214, 205, 196), (185, 174, 166))
    image = Image.new("RGB", size, backgrounds[energy - 1])
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    margin = max(20, width // 20)
    draw.rectangle((margin, margin, width - margin, height - margin), outline=(45, 43, 39), width=3)
    draw.rectangle((margin, margin, margin + width * energy // 5, margin + 10), fill=(182, 55, 42))
    cast = list(shot.get("characters", [])) or ["SPACE"]
    slot_width = (width - margin * 3) // len(cast)
    body_top = height * 0.24
    body_bottom = height * 0.72
    for index, character in enumerate(cast):
        left = margin * 2 + index * slot_width
        right = left + slot_width * 0.72
        draw.rounded_rectangle((left, body_top, right, body_bottom), radius=8,
                               fill=(247, 245, 239), outline=(55, 88, 74), width=3)
        draw.text((left + 8, body_top + 8), str(character)[:18], fill=(32, 31, 29), font=font)
    draw.text((margin * 2, margin * 2), f"{shot['id']}  E{energy}  {shot['technique']}",
              fill=(32, 31, 29), font=font)
    draw.text((margin * 2, height - margin * 2), f"LEVER: {shot['leverage']}",
              fill=(32, 31, 29), font=font)
    image.save(destination, format="PNG")


def render_animatic(shots, canvas, fps, destination):
    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    if not ffmpeg or not ffprobe:
        raise AnimaticError("ffmpeg and ffprobe are required for animatic rendering")
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    size = _dimensions(canvas)
    total_duration = float(shots[-1]["time"][1])
    with tempfile.TemporaryDirectory(prefix="animatic-", dir=str(destination.parent)) as temporary:
        temporary = Path(temporary)
        concat = temporary / "frames.txt"
        lines = []
        for index, shot in enumerate(shots):
            frame = temporary / f"shot-{index:04d}.png"
            _shot_card(shot, size, frame)
            duration = float(shot["time"][1]) - float(shot["time"][0])
            lines.extend((f"file '{frame.as_posix()}'", f"duration {duration:.6f}"))
        lines.append(f"file '{frame.as_posix()}'")
        concat.write_text("\n".join(lines) + "\n", encoding="utf-8")
        target = temporary / "animatic.mp4"
        command = [
            ffmpeg, "-v", "error", "-f", "concat", "-safe", "0", "-i", str(concat),
            "-vf", f"fps={fps},format=yuv420p", "-t", f"{total_duration:.6f}",
            "-an", "-c:v", "libx264", "-movflags", "+faststart",
            "-y", str(target),
        ]
        completed = subprocess.run(command, capture_output=True, text=True, timeout=120, check=False)
        if completed.returncode:
            raise AnimaticError("ffmpeg failed to render animatic")
        os.replace(target, destination)
    probe = subprocess.run(
        [ffprobe, "-v", "error", "-select_streams", "v:0", "-show_entries",
         "stream=width,height,avg_frame_rate:format=duration", "-of", "json", str(destination)],
        capture_output=True, text=True, timeout=30, check=False,
    )
    if probe.returncode:
        raise AnimaticError("ffprobe failed to validate animatic")
    data = json.loads(probe.stdout)
    stream = data["streams"][0]
    expected_width, expected_height = size
    if stream.get("width") != expected_width or stream.get("height") != expected_height:
        raise AnimaticError("animatic dimensions do not match the canvas contract")
    duration = float(data["format"]["duration"])
    if abs(duration - total_duration) > (1.0 / fps + 0.05):
        raise AnimaticError("animatic duration does not match the director timeline")
    return {
        "status": "pass_gate_checked",
        "width": expected_width,
        "height": expected_height,
        "duration": duration,
        "fps": fps,
        "audio_present": False,
        "limitations": ["structural approval only", "silent animatic", "not for external release"],
    }
