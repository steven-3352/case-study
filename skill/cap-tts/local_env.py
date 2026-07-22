"""本地 .env 加载 + API 根地址解析(能力封装版,不绑项目根)。

替代原 `pipeline/env_loader.py`:原模块 import 即从仓库根 `.env` 自动加载;
这里改为**显式** load_dotenv(path),由调用方指定 .env 位置(或纯用已有环境变量)。
"""
from __future__ import annotations

import os
import pathlib

_loaded = False


def _strip_quotes(v: str) -> str:
    v = v.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        return v[1:-1]
    return v


def load_dotenv(path: pathlib.Path | str | None = None, *, override: bool = False) -> dict[str, str]:
    """解析 .env 并写入 os.environ。默认不覆盖已有环境变量。path 不存在则静默跳过。"""
    global _loaded
    parsed: dict[str, str] = {}
    if path is None:
        _loaded = True
        return parsed
    path = pathlib.Path(path)
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


def api_base(env_key: str, *, cfg: str | None = None, default: str | None = None) -> str:
    """API 根地址:.env 中转 URL 优先 → config → 官方默认。"""
    for v in (os.getenv(env_key), cfg, default):
        if v and str(v).strip():
            return str(v).strip().rstrip("/")
    return ""
