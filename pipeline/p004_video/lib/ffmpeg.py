"""ffmpeg-full 路径 + 时长探测.

memory feedback_read-env-example-first · 系统 ffmpeg 精简版无 libass·
必用 /opt/homebrew/opt/ffmpeg-full/bin/ffmpeg。
"""
from __future__ import annotations

import json
import pathlib
import subprocess
from dataclasses import dataclass

FFMPEG = "/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg"
FFPROBE = "/opt/homebrew/opt/ffmpeg-full/bin/ffprobe"


@dataclass(frozen=True)
class FFmpegError(Exception):
    cmd: tuple[str, ...]
    stderr: str

    def __str__(self) -> str:  # pragma: no cover
        return f"ffmpeg failed:\n  cmd: {' '.join(self.cmd)}\n  stderr: {self.stderr}"


def dur(path: pathlib.Path) -> float:
    """媒体文件时长（秒）· ffprobe 精确读 format.duration."""
    r = subprocess.run(
        [FFPROBE, "-v", "error", "-show_entries", "format=duration",
         "-of", "json", str(path)],
        capture_output=True, text=True, check=True,
    )
    return float(json.loads(r.stdout)["format"]["duration"])


def run(cmd: list[str], *, check: bool = True, capture: bool = True) -> subprocess.CompletedProcess:
    """执行 ffmpeg/ffprobe 命令 · check=True 抛 FFmpegError.

    与 subprocess.run(check=True) 差别：
    - 抛出 FFmpegError 携带 stderr（比 CalledProcessError 直观）
    - 默认 capture_output=True，避免 pipeline 输出被 ffmpeg 洪泛
    """
    r = subprocess.run(cmd, capture_output=capture, text=True, check=False)
    if check and r.returncode != 0:
        raise FFmpegError(cmd=tuple(cmd), stderr=(r.stderr or "")[-2000:])
    return r
