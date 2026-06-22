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
    """取异步任务音频。

    云雾中转下：/v1/files/retrieve 返回 {file:{download_url}}，下载得到 .tar
    包（content-*.mp3 + .titles + .extra）；需解包取 mp3。官方裸二进制也兼容。
    """
    host = _minimax_host(cfg)
    # 先拿元信息（含 OSS download_url）。云雾把 retrieve_content 路由吞成首页 HTML，
    # 真正可用的是 /v1/files/retrieve。
    meta_url = _with_group(f"{host}/v1/files/retrieve?file_id={file_id}", group_id)
    meta = _request("GET", meta_url, key)
    _check_base_resp(meta)
    dl = ((meta.get("file") or {}).get("download_url") or "").strip()
    if not dl:
        raise RuntimeError(f"MiniMax 未返回 download_url：{meta}")
    req = urllib.request.Request(dl, method="GET")  # OSS 预签名 URL，无需鉴权头
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            raw = r.read()
    except urllib.error.HTTPError as e:
        err = e.read().decode(errors="replace")
        raise RuntimeError(f"MiniMax 下载 HTTP {e.code}: {err}") from e
    return _extract_audio(raw)


def _extract_audio(raw: bytes) -> bytes:
    """从下载内容里取音频字节：.tar 包则解出 mp3，裸音频则原样返回。"""
    import io
    import tarfile

    if raw[:1] == b"{":  # 误拿到 JSON 错误体
        raise RuntimeError(f"MiniMax 下载返回 JSON 而非音频：{raw[:300]!r}")
    if not (len(raw) > 262 and raw[257:262] == b"ustar") and raw[:1] in (b"<",):
        raise RuntimeError("MiniMax 下载返回 HTML（中转路由未命中）")
    try:
        with tarfile.open(fileobj=io.BytesIO(raw)) as tf:
            mp3 = next((m for m in tf.getmembers() if m.name.endswith(".mp3")), None)
            if mp3 is None:
                raise RuntimeError(f"tar 内无 mp3：{[m.name for m in tf.getmembers()]}")
            f = tf.extractfile(mp3)
            return f.read() if f else b""
    except tarfile.ReadError:
        return raw  # 不是 tar，按裸音频处理（官方直连）


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
