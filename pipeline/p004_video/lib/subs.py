"""字幕生成 + 烧录 · 从 gen_subs_w28d02 抽取的稳定件.

核心：
- tokenize/greedy_pack：按标点切、贪心装箱
- fmt_time / fmt_time_ass：SRT / ASS 时间格式
- gen_srt / gen_ass：从 seg_timing.json 出字幕文件
- burn_subs：ffmpeg libass 烧字幕

字号/margin/max_cue_chars 由调用方给（三平台差异化 → platforms.py）。
"""
from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass, field
from typing import Iterable

from .ffmpeg import FFMPEG, run

_PUNCT: frozenset[str] = frozenset("。！？，、 ")


def fmt_time(sec: float) -> str:
    """SRT 时间格式：HH:MM:SS,MMM."""
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = int(sec % 60)
    ms = int(round((sec - int(sec)) * 1000))
    if ms == 1000:
        s += 1
        ms = 0
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def fmt_time_ass(sec: float) -> str:
    """ASS 时间格式：H:MM:SS.CC."""
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = int(sec % 60)
    cs = int(round((sec - int(sec)) * 100))
    if cs == 100:
        s += 1
        cs = 0
    return f"{h:d}:{m:02d}:{s:02d}.{cs:02d}"


def tokenize(text: str) -> list[str]:
    """按标点切 tokens · 标点保留在 token 末尾."""
    tokens: list[str] = []
    cur = ""
    for ch in text:
        cur += ch
        if ch in _PUNCT:
            tokens.append(cur)
            cur = ""
    if cur:
        tokens.append(cur)
    return tokens


def greedy_pack(tokens: list[str], max_chars: int) -> list[str]:
    """贪心装箱 · 每箱 ≤ max_chars；单 token 超长则硬切."""
    boxes: list[str] = []
    cur = ""
    for tok in tokens:
        if len(tok) > max_chars:
            if cur:
                boxes.append(cur)
                cur = ""
            for i in range(0, len(tok), max_chars):
                chunk = tok[i:i + max_chars]
                if i + max_chars >= len(tok):
                    cur = chunk
                else:
                    boxes.append(chunk)
            continue
        if len(cur) + len(tok) > max_chars and cur:
            boxes.append(cur)
            cur = tok
        else:
            cur += tok
    if cur:
        boxes.append(cur)
    return boxes


def split_long_line(text: str, max_chars: int = 17) -> str:
    """单 cue 内折行 · \\n 表示 SRT/ASS 换行."""
    if len(text) <= max_chars:
        return text
    return "\n".join(greedy_pack(tokenize(text), max_chars))


def split_into_cues(text: str, max_cue_chars: int = 32) -> list[str]:
    """长段拆多个 cue · 每 cue ≤ max_cue_chars."""
    if len(text) <= max_cue_chars:
        return [text]
    return greedy_pack(tokenize(text), max_cue_chars)


@dataclass(frozen=True)
class SubStyle:
    """ASS 字幕样式."""
    fontname: str = "PingFang SC"
    fontsize: int = 42
    primary: str = "&H00f0f5f5"      # 白
    outline: str = "&H00000000"      # 黑描边
    outline_w: int = 3
    alignment: int = 2               # 底居中
    margin_v: int = 200
    max_cue_chars: int = 32
    max_line_chars: int = 17


@dataclass(frozen=True)
class CueSlice:
    """一个字幕 cue（可能是 seg 中的一部分）."""
    start: float
    end: float
    text: str


def _seg_to_slices(seg: dict, style: SubStyle) -> list[CueSlice]:
    """seg (含 start/seg_dur/text) → cue 列表；按字符数分配 seg_dur."""
    start = float(seg["start"])
    seg_dur = float(seg["seg_dur"])
    cues = split_into_cues(seg["text"], max_cue_chars=style.max_cue_chars)
    total_chars = sum(len(c) for c in cues) or 1
    slices: list[CueSlice] = []
    t = start
    for c in cues:
        share = seg_dur * (len(c) / total_chars)
        end = t + share
        slices.append(CueSlice(start=t, end=end, text=c))
        t = end
    return slices


def gen_srt(
    timing_path: pathlib.Path,
    out_path: pathlib.Path,
    *,
    style: SubStyle | None = None,
    skip_emotions: Iterable[str] = ("silence", "gap"),
) -> pathlib.Path:
    """从 seg_timing.json 出 .srt · 跳过 silence/gap 段（真英文对话音自带字幕）."""
    style = style or SubStyle()
    data = json.loads(timing_path.read_text(encoding="utf-8"))
    skip = set(skip_emotions)
    lines: list[str] = []
    idx = 0
    for seg in data["segments"]:
        if seg.get("emotion") in skip:
            continue
        for cue in _seg_to_slices(seg, style):
            idx += 1
            lines.append(str(idx))
            lines.append(f"{fmt_time(cue.start)} --> {fmt_time(cue.end)}")
            lines.append(split_long_line(cue.text, max_chars=style.max_line_chars))
            lines.append("")
    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path


def _ass_header(style: SubStyle) -> str:
    return (
        "[Script Info]\n"
        "ScriptType: v4.00+\n"
        "PlayResX: 1080\n"
        "PlayResY: 1920\n"
        "WrapStyle: 0\n"
        "ScaledBorderAndShadow: yes\n"
        "\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
        "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, "
        "ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
        "Alignment, MarginL, MarginR, MarginV, Encoding\n"
        f"Style: VO,{style.fontname},{style.fontsize},{style.primary},&H00ffffff,"
        f"{style.outline},&H80000000,0,0,0,0,100,100,0,0,1,{style.outline_w},0,"
        f"{style.alignment},60,60,{style.margin_v},1\n"
        "\n"
        "[Events]\n"
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    )


def gen_ass(
    timing_path: pathlib.Path,
    out_path: pathlib.Path,
    *,
    style: SubStyle | None = None,
    skip_emotions: Iterable[str] = ("silence", "gap"),
) -> pathlib.Path:
    """从 seg_timing.json 出 .ass（内置样式）."""
    style = style or SubStyle()
    data = json.loads(timing_path.read_text(encoding="utf-8"))
    skip = set(skip_emotions)
    events: list[str] = []
    for seg in data["segments"]:
        if seg.get("emotion") in skip:
            continue
        for cue in _seg_to_slices(seg, style):
            text = split_long_line(cue.text, max_chars=style.max_line_chars).replace("\n", r"\N")
            events.append(
                f"Dialogue: 0,{fmt_time_ass(cue.start)},{fmt_time_ass(cue.end)},VO,,0,0,0,,{text}"
            )
    out_path.write_text(_ass_header(style) + "\n".join(events) + "\n", encoding="utf-8")
    return out_path


def burn_subs(
    in_mp4: pathlib.Path,
    ass_path: pathlib.Path,
    out_mp4: pathlib.Path,
    *,
    crf: int = 20,
) -> pathlib.Path:
    """ffmpeg libass 烧字幕 · ASS 路径的冒号需转义."""
    ass_escaped = str(ass_path).replace(":", r"\:")
    run([
        FFMPEG, "-y",
        "-i", str(in_mp4),
        "-vf", f"ass='{ass_escaped}'",
        "-c:v", "libx264", "-preset", "medium", "-crf", str(crf),
        "-pix_fmt", "yuv420p",
        "-c:a", "copy",
        str(out_mp4),
    ])
    return out_mp4
