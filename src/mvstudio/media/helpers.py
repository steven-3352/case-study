"""共享底层助手 — ad-agent 与 mv-agent 都可调用，无业务逻辑。"""
from __future__ import annotations

import hashlib
import os
import shutil
from pathlib import Path
from typing import Optional

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
