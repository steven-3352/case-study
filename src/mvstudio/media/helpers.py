"""共享底层助手 — ad-agent 与 mv-agent 都可调用，无业务逻辑。"""
from __future__ import annotations

import hashlib
import os
import shutil
from pathlib import Path
from typing import Mapping, Optional, Sequence

from PIL import Image, ImageDraw, ImageFont

try:
    from mv_platform.application.control_plane import ENV_MAP
except ImportError:
    ENV_MAP: dict = {}


def err(code: str, message: str, hint: str = "") -> dict:
    return {"code": code, "message": message, "hint": hint}


def sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def ffmpeg_bin() -> str:
    return os.environ.get("MVSTUDIO_FFMPEG_PATH") or shutil.which("ffmpeg") or "ffmpeg"


def ffprobe_bin() -> str:
    return os.environ.get("MVSTUDIO_FFPROBE_PATH") or shutil.which("ffprobe") or "ffprobe"


def provider_config() -> dict:
    """os.environ → 嵌套 {section:{key:val}}，键遵循 ENV_MAP。"""
    cfg: dict = {}
    for dotted, env_key in ENV_MAP.items():
        section, key = dotted.split(".", 1)
        val = os.environ.get(env_key, "")
        if val:
            cfg.setdefault(section, {})[key] = val
    return cfg


def max_shots(env_var: str) -> Optional[int]:
    """镜头上限：读 env_var（未设或非正整数 = 不限）。"""
    raw = os.environ.get(env_var, "").strip()
    if not raw:
        return None
    try:
        n = int(raw)
        return n if n > 0 else None
    except ValueError:
        return None


def _load_caption_font(font_path: Path | None, size: int) -> ImageFont.ImageFont:
    if font_path is not None:
        try:
            return ImageFont.truetype(str(font_path), size=size)
        except OSError:
            pass
    try:
        return ImageFont.load_default(size=size)  # Pillow >= 10.1
    except TypeError:
        return ImageFont.load_default()


def compose_storyboard(
    entries: Sequence[Mapping[str, object]],
    out_path: Path,
    *,
    cell_width: int = 360,
    cell_height: int = 640,
    cols: int = 3,
    pad: int = 24,
    caption_height: int = 48,
    background: tuple[int, int, int] = (24, 24, 26),
    font_path: Path | None = None,
) -> Path | None:
    """合成 N 宫格分镜拼图 — 让用户一屏看完所有分镜再决定要不要跑 i2v。

    entries 每项要有 "id"、"keyframe_path"、"duration"(可选) 三个键。
    len(entries) < 2 → 返回 None、不写文件(单镜无拼图价值,由 caller 判断)。
    font_path=None → 用 PIL 默认字体(CI 安全,无 CJK 字体依赖)。
    成功返回 out_path。
    """
    n = len(entries)
    if n < 2:
        return None

    if n > 6 and cols == 3:
        cols = 4
    rows = (n + cols - 1) // cols

    total_w = cols * cell_width + (cols + 1) * pad
    total_h = rows * (cell_height + caption_height) + (rows + 1) * pad

    canvas = Image.new("RGB", (total_w, total_h), background)
    draw = ImageDraw.Draw(canvas)
    font = _load_caption_font(font_path, size=max(18, caption_height // 2))

    for i, entry in enumerate(entries):
        r, c = divmod(i, cols)
        x = pad + c * (cell_width + pad)
        y = pad + r * (cell_height + caption_height + pad)

        kf_raw = entry.get("keyframe_path")
        kf_path = Path(str(kf_raw)) if kf_raw is not None else None
        if kf_path is not None and kf_path.exists():
            try:
                with Image.open(kf_path) as img:
                    thumb = img.convert("RGB").resize(
                        (cell_width, cell_height), Image.LANCZOS
                    )
                canvas.paste(thumb, (x, y))
            except OSError:
                _draw_missing_cell(draw, x, y, cell_width, cell_height, font)
        else:
            _draw_missing_cell(draw, x, y, cell_width, cell_height, font)

        cap_y = y + cell_height
        draw.rectangle(
            [x, cap_y, x + cell_width, cap_y + caption_height],
            fill=(48, 48, 52),
        )
        caption = _format_caption(entry)
        draw.text(
            (x + cell_width // 2, cap_y + caption_height // 2),
            caption,
            fill=(230, 230, 230),
            font=font,
            anchor="mm",
        )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out_path, format="PNG", optimize=True)
    return out_path


def _draw_missing_cell(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    w: int,
    h: int,
    font: ImageFont.ImageFont,
) -> None:
    draw.rectangle([x, y, x + w, y + h], fill=(60, 60, 60))
    draw.text(
        (x + w // 2, y + h // 2),
        "MISSING",
        fill=(180, 180, 180),
        font=font,
        anchor="mm",
    )


def _format_caption(entry: Mapping[str, object]) -> str:
    shot_id = str(entry.get("id", "?"))
    duration = entry.get("duration")
    if duration is None or duration == 0 or duration == "":
        return shot_id
    return f"{shot_id} · {duration}s"
