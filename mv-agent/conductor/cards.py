"""标题卡渲染 — 简版 PIL（不碰 paperdoll 引擎，不装 librosa）。

读 titlecard.build_title_cards 产的 spec（title_mode/text/art_style/subtitle/seal），
用 artstyle 色板 + 本地 CJK 字体，渲染 9:16 静态标题卡 PNG。
compose() 把卡当独立镜头拼到片头/片尾。
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

W, H = 720, 1280  # 9:16

# 本地 CJK 字体回退链（Linux/容器优先 Noto，其次 DejaVu）
_FONT_CANDIDATES = [
    "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
    "/System/Library/Fonts/Supplemental/Songti.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]


def _font(size: int) -> ImageFont.FreeTypeFont:
    for cand in _FONT_CANDIDATES:
        if Path(cand).is_file():
            try:
                return ImageFont.truetype(cand, size)
            except Exception:
                continue
    return ImageFont.load_default()


def _style(art_style: str):
    """查 artstyle 色板；失败回退暖金/墨/朱砂默认（不崩）。"""
    try:
        from pipeline.voice_room.artstyle import get_style
        st = get_style(art_style)
        return tuple(st.ink), tuple(st.outline), tuple(st.seal_color), tuple(st.warm_white)
    except Exception:
        return (74, 52, 38), (212, 175, 55), (176, 42, 34), (255, 246, 230)


def _centered(draw, text, font, cy):
    box = draw.textbbox((0, 0), text, font=font)
    w, h = box[2] - box[0], box[3] - box[1]
    return (W - w) // 2, cy - h // 2, w, h


def render_card(spec: dict, out_path: Path) -> Path:
    """spec: {title_mode, text, art_style, [subtitle], [seal]} → 9:16 PNG。"""
    ink, outline, seal_color, warm = _style(spec.get("art_style", "金墨朱砂"))
    img = Image.new("RGB", (W, H), (18, 14, 12))  # 暖黑底（守禁蓝紫铁律）
    draw = ImageDraw.Draw(img)

    text = spec.get("text", "").strip() or "无题"
    title_font = _font(120 if len(text) <= 4 else 84)
    x, y, tw, th = _centered(draw, text, title_font, H // 2 - 40)
    # 八向描边（金）+ 字芯（墨偏暖白，暗底上可读）
    for dx in (-4, 0, 4):
        for dy in (-4, 0, 4):
            if dx or dy:
                draw.text((x + dx, y + dy), text, font=title_font, fill=outline)
    draw.text((x, y), text, font=title_font, fill=warm)

    subtitle = spec.get("subtitle", "").strip()
    if subtitle:
        sf = _font(40)
        sx, sy, _, _ = _centered(draw, subtitle, sf, H // 2 + th)
        draw.text((sx, sy), subtitle, font=sf, fill=outline)

    seal = spec.get("seal", "").strip()
    if seal and spec.get("title_mode") == "ending":
        sf = _font(48)
        pad, side = 16, 0
        box = draw.textbbox((0, 0), seal, font=sf)
        side = max(box[2] - box[0], box[3] - box[1]) + pad * 2
        sx, sy = (W - side) // 2, y + th + 100
        draw.rounded_rectangle([sx, sy, sx + side, sy + side], radius=10, fill=seal_color)
        tx, ty, _, _ = _centered(draw, seal, sf, sy + side // 2)
        draw.text((tx, ty), seal, font=sf, fill=warm)

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path)
    return out_path
