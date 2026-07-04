"""三平台差异化输出 · 抖音 / 小红书 / 视频号.

- 字号：抖音 42 / 小红书 50 / 视频号 42
- max_cue_chars：抖音/视频号 32 / 小红书 26
- drawtext overlay（时间戳大字、白闪快切等）由 config 声明
"""
from __future__ import annotations

import pathlib
from dataclasses import dataclass, field
from typing import Literal

from .ffmpeg import FFMPEG, dur, run
from .subs import SubStyle, gen_ass

FONT_PINGFANG = "/System/Library/Fonts/PingFang.ttc"
FONT_SFMONO = "/System/Library/Fonts/SFNSMono.ttf"


@dataclass(frozen=True)
class PlatformSpec:
    """一个平台的字幕差异 + 输出目录名."""
    name: str            # douyin / xhs / weixin
    subs_size: int
    margin_v: int
    max_cue_chars: int
    max_line_chars: int

    def to_style(self) -> SubStyle:
        return SubStyle(
            fontsize=self.subs_size,
            margin_v=self.margin_v,
            max_cue_chars=self.max_cue_chars,
            max_line_chars=self.max_line_chars,
        )


DEFAULT_PLATFORMS: tuple[PlatformSpec, ...] = (
    PlatformSpec(name="douyin", subs_size=42, margin_v=200, max_cue_chars=32, max_line_chars=17),
    PlatformSpec(name="xhs", subs_size=50, margin_v=220, max_cue_chars=26, max_line_chars=14),
    PlatformSpec(name="weixin", subs_size=42, margin_v=200, max_cue_chars=32, max_line_chars=17),
)


@dataclass(frozen=True)
class DrawTextOverlay:
    """drawtext 大字覆盖 · 用于 M1 时间戳、白闪快切等."""
    text: str
    t_start: float
    t_end: float
    fontsize: int = 64
    color: str = "white"
    border_w: int = 4
    border_color: str = "black"
    y_expr: str = "h-500"     # 底部偏上 · 避开底部字幕
    x_expr: str = "(w-text_w)/2"
    fontfile: str = FONT_PINGFANG


def _escape_drawtext(text: str) -> str:
    """drawtext text= 需转义特殊字符（冒号、引号、百分号、反斜杠）."""
    return (
        text.replace("\\", "\\\\")
            .replace(":", "\\:")
            .replace("'", "’")
            .replace("%", "\\%")
    )


def build_filter_chain(
    ass_path: pathlib.Path,
    overlays: list[DrawTextOverlay] | None = None,
) -> str:
    """组 -vf filter 链：ass 字幕 + 若干 drawtext 覆盖."""
    ass_escaped = str(ass_path).replace(":", r"\:")
    parts: list[str] = [f"ass='{ass_escaped}'"]
    for ov in overlays or []:
        parts.append(
            f"drawtext=fontfile='{ov.fontfile}':"
            f"text='{_escape_drawtext(ov.text)}':"
            f"fontsize={ov.fontsize}:fontcolor={ov.color}:"
            f"borderw={ov.border_w}:bordercolor={ov.border_color}:"
            f"x={ov.x_expr}:y={ov.y_expr}:"
            f"enable='between(t,{ov.t_start:.2f},{ov.t_end:.2f})'"
        )
    return ",".join(parts)


@dataclass(frozen=True)
class PlatformRenderResult:
    spec: PlatformSpec
    out_mp4: pathlib.Path
    duration_s: float
    size_mb: float


def render_platform(
    spec: PlatformSpec,
    *,
    src_mp4: pathlib.Path,
    timing_json: pathlib.Path,
    out_dir: pathlib.Path,
    overlays: list[DrawTextOverlay] | None = None,
    crf: int = 20,
) -> PlatformRenderResult:
    """一个平台：出 ASS → filter 链 → 一次 ffmpeg 落盘 <platform>/video_no_bgm.mp4."""
    out_dir.mkdir(parents=True, exist_ok=True)
    ass_out = src_mp4.parent / f"vo_{spec.name}.ass"
    gen_ass(timing_json, ass_out, style=spec.to_style())
    vf = build_filter_chain(ass_out, overlays)

    out_mp4 = out_dir / "video_no_bgm.mp4"
    run([
        FFMPEG, "-y",
        "-i", str(src_mp4),
        "-vf", vf,
        "-c:v", "libx264", "-preset", "medium", "-crf", str(crf),
        "-pix_fmt", "yuv420p",
        "-c:a", "copy",
        str(out_mp4),
    ])
    return PlatformRenderResult(
        spec=spec,
        out_mp4=out_mp4,
        duration_s=dur(out_mp4),
        size_mb=out_mp4.stat().st_size / (1024 * 1024),
    )
