"""MiniMax TTS 客户端 · speech-2.8-turbo + t2a_async_v2.

凭证：仓库根目录 `.env` → MINIMAX_API_KEY、MINIMAX_BASE_URL（三方中转）、MINIMAX_GROUP_ID（可选）
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

import pipeline.env_loader  # noqa: F401 — 加载 .env
from pipeline.env_loader import api_base


def _check_base_resp(data: dict) -> None:
    base = data.get("base_resp") or {}
    code = base.get("status_code", 0)
    if code != 0:
        raise RuntimeError(f"MiniMax API 错误 {code}: {base.get('status_msg') or data}")


def _request(method: str, url: str, key: str, *, body: dict | None = None, timeout: int = 60) -> dict:
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        err = e.read().decode(errors="replace")
        raise RuntimeError(f"MiniMax HTTP {e.code}: {err}") from e


def _with_group(url: str, group_id: str | None) -> str:
    if not group_id:
        return url
    sep = "&" if "?" in url else "?"
    return f"{url}{sep}GroupId={urllib.parse.quote(group_id)}"


def _minimax_host(cfg: dict) -> str:
    m = cfg.get("minimax", cfg)
    return api_base("MINIMAX_BASE_URL", cfg=m.get("api_host"), default="https://api.minimaxi.com")


def create_async_task(
    text: str, cfg: dict, *, key: str, group_id: str | None,
    emotion: str | None = None, speed: float | None = None,
) -> tuple[str, int | None]:
    m = cfg.get("minimax", cfg)
    host = _minimax_host(cfg)
    url = _with_group(f"{host}/v1/t2a_async_v2", group_id)
    vs = m.get("voice_setting") or {}
    body: dict[str, Any] = {
        "model": m.get("model", "speech-2.8-turbo"),
        "text": text,
        "language_boost": m.get("language_boost", "Chinese"),
        "voice_setting": {
            "voice_id": vs.get("voice_id") or m.get("voice_id", "male-qn-badao"),
            "speed": speed if speed is not None else vs.get("speed", m.get("speed", 1.0)),
            "vol": vs.get("vol", m.get("vol", 1.0)),
            "pitch": vs.get("pitch", m.get("pitch", 0)),
        },
        "audio_setting": {
            "format": m.get("format", "mp3"),
            "audio_sample_rate": m.get("sample_rate", 32000),
            "bitrate": m.get("bitrate", 128000),
            "channel": m.get("channel", 1),
        },
    }
    emo = emotion or vs.get("emotion") or m.get("emotion")
    if emo:
        body["voice_setting"]["emotion"] = emo
    data = _request("POST", url, key, body=body)
    _check_base_resp(data)
    task_id = data.get("task_id")
    if not task_id:
        raise RuntimeError(f"MiniMax 未返回 task_id：{data}")
    return str(task_id), data.get("file_id")


def poll_async_task(task_id: str, cfg: dict, *, key: str, group_id: str | None,
                    poll_interval: float = 1.5, max_wait: float = 120) -> int:
    host = _minimax_host(cfg)
    url = _with_group(f"{host}/v1/query/t2a_async_query_v2?task_id={task_id}", group_id)
    deadline = time.time() + max_wait
    last_status = ""
    while time.time() < deadline:
        data = _request("GET", url, key)
        _check_base_resp(data)
        status = str(data.get("status", "")).lower()
        last_status = status
        if status in ("success", "succeeded", "completed"):
            file_id = data.get("file_id")
            if not file_id:
                raise RuntimeError(f"任务成功但无 file_id：{data}")
            return int(file_id)
        if status in ("failed", "expired"):
            raise RuntimeError(f"MiniMax 任务 {status}：{data}")
        time.sleep(poll_interval)
    raise TimeoutError(f"MiniMax 任务超时（最后状态 {last_status}）")


def download_file(file_id: int, cfg: dict, *, key: str, group_id: str | None) -> bytes:
    host = _minimax_host(cfg)
    url = _with_group(f"{host}/v1/files/retrieve_content?file_id={file_id}", group_id)
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {key}"}, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.read()
    except urllib.error.HTTPError as e:
        err = e.read().decode(errors="replace")
        raise RuntimeError(f"MiniMax 下载 HTTP {e.code}: {err}") from e


def synth_async(
    text: str, cfg: dict, out_mp3, *, emotion: str | None = None, speed: float | None = None
) -> bool:
    """异步 T2A v2 合成。凭证缺失返回 False。"""
    key = os.getenv("MINIMAX_API_KEY")
    group_id = os.getenv("MINIMAX_GROUP_ID") or cfg.get("minimax", {}).get("group_id")
    if not key:
        return False
    task_id, _ = create_async_task(
        text, cfg, key=key, group_id=group_id, emotion=emotion, speed=speed
    )
    file_id = poll_async_task(task_id, cfg, key=key, group_id=group_id)
    audio = download_file(file_id, cfg, key=key, group_id=group_id)
    out_mp3.parent.mkdir(parents=True, exist_ok=True)
    out_mp3.write_bytes(audio)
    return True
