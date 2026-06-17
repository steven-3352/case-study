"""从仓库根目录 `.env` 加载密钥到 os.environ.

所有 pipeline 入口脚本应在启动时 import 本模块（或调用 load_dotenv）。
"""
from __future__ import annotations

import os
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / ".env"
_loaded = False


def _strip_quotes(v: str) -> str:
    v = v.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        return v[1:-1]
    return v


def load_dotenv(path: pathlib.Path | None = None, *, override: bool = False) -> dict[str, str]:
    """解析 `.env` 并写入 os.environ。默认不覆盖已有环境变量。"""
    global _loaded
    path = path or ENV_PATH
    parsed: dict[str, str] = {}
    if not path.is_file():
        _loaded = True
        return parsed
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].strip()
        if "=" not in line:
            continue
        key, val = line.split("=", 1)
        key, val = key.strip(), _strip_quotes(val.strip())
        if not key:
            continue
        parsed[key] = val
        if override or key not in os.environ:
            os.environ[key] = val
    _loaded = True
    return parsed


def get_env(key: str, default: str | None = None) -> str | None:
    if not _loaded:
        load_dotenv()
    return os.getenv(key, default)


def api_base(env_key: str, *, cfg: str | None = None, default: str | None = None) -> str:
    """API 根地址：.env 中转 URL 优先 → config → 官方默认。"""
    for v in (os.getenv(env_key), cfg, default):
        if v and str(v).strip():
            return str(v).strip().rstrip("/")
    return ""


# 被 import 时自动加载
load_dotenv()
