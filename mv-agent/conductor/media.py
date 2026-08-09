"""共享媒体/配置助手 — tools.py 六步工具都用它。

职责单一：环境与 provider 配置、ffprobe 时长、sha256 摘要、.lrc 解析、
本地 whisper 兜底时间码、结构化错误。不做业务判断、不碰状态机。

所有 provider 类来自 src/mvstudio/*（只读复用，不改引擎）。
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional

# ── 让 mv_platform / mvstudio 可 import（项目根 = mv-agent 的上两级）
_REPO_ROOT = Path(__file__).resolve().parents[2]
for _p in (str(_REPO_ROOT), str(_REPO_ROOT / "src")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# ── 加载项目根 .env（统一 KEY 源，不再用 mv-agent/.env）
try:
    from dotenv import load_dotenv
    load_dotenv(_REPO_ROOT / ".env", override=False)
except ImportError:
    pass

try:
    from mv_platform.application.control_plane import detect_local_whisper_model
    _MV_PLATFORM_OK = True
except ImportError:
    _MV_PLATFORM_OK = False
    def detect_local_whisper_model():  # type: ignore
        return ""

from mvstudio.media import (
    err,
    ffmpeg_bin,
    ffprobe_bin,
    max_shots as _max_shots,
    provider_config,
    sha256_bytes,
    sha256_file,
)


AUDIO_EXT = {".wav", ".mp3", ".aac", ".m4a", ".flac", ".ogg"}
IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp"}


def max_shots() -> Optional[int]:
    return _max_shots("MV_MAX_SHOTS")


def ensure_whisper_env() -> None:
    """faster-whisper 需要 MVSTUDIO_WHISPER_MODEL；没配就自动发现本地 medium。"""
    if not os.environ.get("MVSTUDIO_WHISPER_MODEL"):
        found = detect_local_whisper_model()
        if found:
            os.environ["MVSTUDIO_WHISPER_MODEL"] = found


def audio_duration_seconds(path: Path) -> float:
    """ffprobe 取音频总时长（秒）。失败抛 RuntimeError。"""
    cmd = [ffprobe_bin(), "-v", "error", "-show_entries", "format=duration",
           "-of", "default=noprint_wrappers=1:nokey=1", str(path)]
    try:
        out = subprocess.run(cmd, capture_output=True, check=True, timeout=60)
    except (OSError, subprocess.SubprocessError) as exc:
        raise RuntimeError(f"ffprobe 读取时长失败：{exc}") from exc
    try:
        return float(out.stdout.decode().strip())
    except ValueError as exc:
        raise RuntimeError("ffprobe 未返回有效时长") from exc


_LRC_TS = re.compile(r"\[(\d{1,2}):(\d{2})(?:[.:](\d{1,3}))?\]")


def parse_lrc(text: str) -> list[dict]:
    """解析 .lrc → [{start_seconds, text}]，按时间排序。无有效时间轴返回 []。"""
    entries: list[dict] = []
    for line in text.splitlines():
        stamps = _LRC_TS.findall(line)
        if not stamps:
            continue
        body = _LRC_TS.sub("", line).strip()
        if not body:
            continue
        for mm, ss, frac in stamps:
            start = int(mm) * 60 + int(ss)
            if frac:
                start += int(frac) / (10 ** len(frac))
            entries.append({"start_seconds": round(float(start), 3), "text": body})
    entries.sort(key=lambda e: e["start_seconds"])
    # 去重同时间轴 & 强制严格递增（draft_maps 要求 start 有序且不相等）
    out: list[dict] = []
    last = -1.0
    for e in entries:
        if e["start_seconds"] <= last:
            e["start_seconds"] = round(last + 0.01, 3)
        out.append(e)
        last = e["start_seconds"]
    return out


def whisper_timed_lyrics(audio_path: Path, duration: float) -> list[dict]:
    """本地 faster-whisper 转录 → [{start_seconds, text}]（按词聚成行）。

    用 transcribe()（自由转录，不做歌词精确覆盖校验，鲁棒），
    再按停顿（>0.6s 间隔或标点）把词聚成行。
    """
    ensure_whisper_env()
    from mvstudio.providers.alignment_faster_whisper import FasterWhisperAlignmentPort
    port = FasterWhisperAlignmentPort.from_env()
    result = port.transcribe(str(audio_path), language="zh")
    words = [w for w in result.segments if w.get("text", "").strip()]
    lines: list[dict] = []
    buf, line_start, prev_end = "", None, None
    for w in words:
        t = w["text"].strip()
        if line_start is None:
            line_start = float(w["start"])
        gap = (float(w["start"]) - prev_end) if prev_end is not None else 0.0
        buf += t
        prev_end = float(w["end"])
        if gap > 0.6 or re.search(r"[，。！？、,.!?；;]$", buf):
            lines.append({"start_seconds": round(line_start, 3), "text": buf.strip("，。！？、,.!?；; ")})
            buf, line_start = "", None
    if buf.strip():
        lines.append({"start_seconds": round(line_start or 0.0, 3), "text": buf.strip()})
    # 强制严格递增且不超时长
    out, last = [], -1.0
    for e in lines:
        if not e["text"]:
            continue
        if e["start_seconds"] <= last:
            e["start_seconds"] = round(last + 0.01, 3)
        if e["start_seconds"] >= duration:
            break
        out.append(e)
        last = e["start_seconds"]
    return out


# ──────────────────────────────────────────────────────────────────────────────
# 歌词文件读取（.txt / .xlsx）+ 容错对齐 —— 均委托 src/mvstudio 共享核心。
#   读取：director.intake.read_plain_lyric_lines（.txt/.xlsx 自动选列）
#   对齐：providers.alignment_faster_whisper.FasterWhisperAlignmentPort(tolerant=True)
#         文字权威、whisper 只出时间，按字符占比贴合（director.alignment.proportional_entries）
#   ——本模块只做「格式壳」：.xls 提示 + 映射成 conductor 的 {start_seconds,text}。
# ──────────────────────────────────────────────────────────────────────────────

def read_lyrics_lines(path: Path, column: Optional[str] = None) -> list[str]:
    """读 .txt / .xlsx 歌词 → 一行一句纯文本（无时间轴）。委托共享核心。

    .xls（旧格式）本核心不支持 → 提示另存为 .xlsx。
    """
    path = Path(path).expanduser()
    if path.suffix.lower() == ".xls":
        raise RuntimeError(".xls（旧格式）请在 Excel 里「另存为 .xlsx」后再用")
    from mvstudio.director.intake import IntakeContractError, read_plain_lyric_lines
    try:
        return read_plain_lyric_lines(path, column)
    except IntakeContractError as exc:
        raise RuntimeError(str(exc)) from exc


def align_lyrics_to_audio(lines: list[str], audio_path: Path, duration: float) -> list[dict]:
    """容错对齐：文字用 lines（权威），时间轴由共享核心的 tolerant 对齐端产出。

    委托 FasterWhisperAlignmentPort(tolerant=True) + proportional_entries，
    再把 {text,source_line,start_seconds,confidence} 映射成 conductor 的
    {start_seconds,text}（保证严格递增、落在 [0,duration) 内由核心负责）。
    """
    lines = [ln.strip() for ln in lines if ln.strip()]
    if not lines:
        raise RuntimeError("歌词为空")
    ensure_whisper_env()
    from mvstudio.director.alignment import AlignmentTask, LyricAlignmentError
    from mvstudio.providers.alignment_faster_whisper import FasterWhisperAlignmentPort
    task = AlignmentTask(
        audio_path=Path(audio_path),
        audio_digest=sha256_file(Path(audio_path)),
        duration_seconds=float(duration),
        lines=tuple({"text": ln, "source_line": i} for i, ln in enumerate(lines, 1)),
    )
    try:
        result = FasterWhisperAlignmentPort.from_env(tolerant=True).align(task)
    except LyricAlignmentError as exc:
        raise RuntimeError(str(exc)) from exc
    return [{"start_seconds": round(float(e["start_seconds"]), 3), "text": e["text"]}
            for e in result.entries]
