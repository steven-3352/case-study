#!/usr/bin/env python3
"""MiniMax T2A async v2 · 通过 yunwu.ai 代理调用.

用法:
  python3 pipeline/tts/gen_speech_minimax.py \\
      --script pipeline/dry-run-001/script.md \\
      -o pipeline/dry-run-001/speech.mp3
  python3 pipeline/tts/gen_speech_minimax.py --text "你好" -o /tmp/test.mp3

环境变量(写在仓库根目录 .env):
  TTS_API_KEY    — yunwu.ai 中转 key
  TTS_BASE_URL   — 默认 https://yunwu.ai
  TTS_MODEL      — 默认 speech-2.8-turbo
  TTS_VOICE      — 默认 male-qn-jingying-jingpin (voice_id)

文档: https://platform.minimaxi.com/docs/api-reference/speech-t2a-async-create
"""
from __future__ import annotations

import argparse
import logging
import os
import pathlib
import random
import re
import subprocess
import sys
import time
from dataclasses import dataclass

import requests
import yaml
from dotenv import load_dotenv

ROOT = pathlib.Path(__file__).resolve().parent
CFG_PATH = ROOT / "config_minimax.yaml"
ENV_PATH = ROOT.parent.parent / ".env"

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("gen_speech_minimax")


@dataclass(frozen=True)
class Settings:
    api_key: str
    base_url: str
    model: str
    voice: str

    @property
    def submit_url(self) -> str:
        return f"{self.base_url.rstrip('/')}/minimax/v1/t2a_async_v2"

    @property
    def query_url(self) -> str:
        return f"{self.base_url.rstrip('/')}/minimax/v1/query/t2a_async_query_v2"

    @property
    def files_url(self) -> str:
        return f"{self.base_url.rstrip('/')}/minimax/v1/files/retrieve"

    @property
    def headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }


@dataclass(frozen=True)
class VoiceJitter:
    speed: float
    pitch: int
    vol: float
    emotion: str


def load_settings() -> Settings:
    load_dotenv(ENV_PATH)
    try:
        api_key = os.environ["TTS_API_KEY"]
    except KeyError:
        sys.exit("缺少 TTS_API_KEY,检查 .env")
    return Settings(
        api_key=api_key,
        base_url=os.environ.get("TTS_BASE_URL", "https://yunwu.ai"),
        model=os.environ.get("TTS_MODEL", "speech-2.8-turbo"),
        voice=os.environ.get("TTS_VOICE", "male-qn-jingying-jingpin"),
    )


def load_config(path: pathlib.Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def extract_speech_from_script(script_path: pathlib.Path, markers: list[str]) -> str:
    text = script_path.read_text(encoding="utf-8")
    parts: list[str] = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        for marker in markers:
            if marker in line:
                seg = line.split(marker, 1)[-1].strip()
                if seg:
                    parts.append(seg)
                else:
                    j = i + 1
                    while j < len(lines):
                        nxt = lines[j].strip()
                        if (
                            not nxt
                            or nxt.startswith("#")
                            or nxt.startswith("**")
                            or nxt.startswith("[")
                            or nxt.startswith("|")
                            or nxt.startswith("---")
                        ):
                            break
                        parts.append(nxt)
                        j += 1
                    i = j - 1
                break
        i += 1
    if not parts:
        sys.exit(f"未能从 {script_path} 提取口播")
    return re.sub(r"\s+", "", "".join(parts))


def pick_jitter(cfg: dict, *, jitter: bool) -> VoiceJitter:
    vs = cfg.get("voice_setting", {})
    if jitter and cfg.get("jitter", False):
        return VoiceJitter(
            speed=float(random.choice(vs.get("speed_options", [vs.get("speed", 1.0)]))),
            pitch=int(random.choice(vs.get("pitch_options", [vs.get("pitch", 0)]))),
            vol=float(random.choice(vs.get("vol_options", [vs.get("vol", 1.0)]))),
            emotion=str(vs.get("emotion", "neutral")),
        )
    return VoiceJitter(
        speed=float(vs.get("speed", 1.0)),
        pitch=int(vs.get("pitch", 0)),
        vol=float(vs.get("vol", 1.0)),
        emotion=str(vs.get("emotion", "neutral")),
    )


def request_with_retry(
    method: str,
    url: str,
    *,
    http_cfg: dict,
    **kw,
) -> requests.Response:
    timeout = http_cfg.get("request_timeout", 30)
    retries = max(1, int(http_cfg.get("retries", 3)))
    backoff = float(http_cfg.get("backoff_seconds", 3))
    last_err: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            return requests.request(method, url, timeout=timeout, **kw)
        except requests.exceptions.RequestException as exc:
            last_err = exc
            if attempt < retries:
                time.sleep(backoff * attempt)
    sys.exit(f"网络请求失败 {method} {url}: {last_err}")


def _check_base_resp(payload: dict, action: str) -> None:
    base = payload.get("base_resp") or {}
    code = base.get("status_code", 0)
    if code != 0:
        sys.exit(f"{action} 失败 status_code={code}: {base.get('status_msg')}")


def submit_task(
    settings: Settings,
    text: str,
    voice: VoiceJitter,
    audio_cfg: dict,
    http_cfg: dict,
) -> int:
    body = {
        "model": settings.model,
        "text": text,
        "voice_setting": {
            "voice_id": settings.voice,
            "speed": voice.speed,
            "pitch": voice.pitch,
            "vol": voice.vol,
            "emotion": voice.emotion,
            "english_normalization": bool(audio_cfg.get("english_normalization", False)),
        },
        "audio_setting": {
            "format": audio_cfg.get("format", "mp3"),
            "sample_rate": int(audio_cfg.get("sample_rate", 32000)),
            "bitrate": int(audio_cfg.get("bitrate", 128000)),
            "channel": int(audio_cfg.get("channel", 1)),
        },
    }
    r = request_with_retry(
        "POST",
        settings.submit_url,
        http_cfg=http_cfg,
        headers=settings.headers,
        json=body,
    )
    if r.status_code != 200:
        sys.exit(f"提交失败 HTTP {r.status_code}: {r.text[:500]}")
    data = r.json()
    _check_base_resp(data, "提交任务")
    task_id = data.get("task_id")
    if not task_id:
        sys.exit(f"未拿到 task_id: {data}")
    return int(task_id)


def poll_task(
    settings: Settings,
    task_id: int,
    poll_cfg: dict,
    http_cfg: dict,
) -> int:
    interval = float(poll_cfg.get("interval_seconds", 3))
    timeout = float(poll_cfg.get("timeout_seconds", 300))
    deadline = time.time() + timeout
    last_status = ""
    while time.time() < deadline:
        r = request_with_retry(
            "GET",
            settings.query_url,
            http_cfg=http_cfg,
            headers=settings.headers,
            params={"task_id": task_id},
        )
        if r.status_code != 200:
            sys.exit(f"查询失败 HTTP {r.status_code}: {r.text[:500]}")
        data = r.json()
        _check_base_resp(data, "查询任务")
        status = str(data.get("status", ""))
        if status != last_status:
            log.info("  task %s: %s", task_id, status or "(no status)")
            last_status = status
        if status == "Success":
            file_id = data.get("file_id")
            if not file_id:
                sys.exit(f"任务成功但缺 file_id: {data}")
            return int(file_id)
        if status in {"Failed", "Expired"}:
            sys.exit(f"任务终止 status={status}: {data}")
        time.sleep(interval)
    sys.exit(f"轮询超时 ({timeout:.0f}s),task_id={task_id}")


def retrieve_file_url(settings: Settings, file_id: int, http_cfg: dict) -> str:
    r = request_with_retry(
        "GET",
        settings.files_url,
        http_cfg=http_cfg,
        headers=settings.headers,
        params={"file_id": file_id},
    )
    if r.status_code != 200:
        sys.exit(f"取文件失败 HTTP {r.status_code}: {r.text[:500]}")
    data = r.json()
    _check_base_resp(data, "取文件")
    file_obj = data.get("file") or {}
    url = file_obj.get("download_url") or file_obj.get("file_url")
    if not url:
        sys.exit(f"未拿到下载链接: {data}")
    return str(url)


def download(url: str, out: pathlib.Path, http_cfg: dict) -> None:
    r = request_with_retry("GET", url, http_cfg=http_cfg)
    if r.status_code != 200:
        sys.exit(f"下载失败 HTTP {r.status_code}")
    out.write_bytes(r.content)


def save_params(
    out: pathlib.Path,
    cfg: dict,
    settings: Settings,
    voice: VoiceJitter,
) -> None:
    if not cfg.get("output", {}).get("save_params", True):
        return
    sidecar = out.with_suffix(".tts.yaml")
    body = (
        "provider: minimax-async\n"
        f"model: {settings.model}\n"
        f"voice_id: {settings.voice}\n"
        f"speed: {voice.speed}\n"
        f"pitch: {voice.pitch}\n"
        f"vol: {voice.vol}\n"
        f"emotion: {voice.emotion}\n"
    )
    sidecar.write_text(body, encoding="utf-8")


def to_wav(mp3: pathlib.Path, wav: pathlib.Path, sample_rate: int) -> None:
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(mp3), "-ar", str(sample_rate), "-ac", "1", str(wav)],
        check=True,
        capture_output=True,
    )
    mp3.unlink()


def main() -> None:
    ap = argparse.ArgumentParser(description="MiniMax T2A async v2 · 通过 yunwu.ai 代理")
    ap.add_argument("--config", type=pathlib.Path, default=CFG_PATH)
    ap.add_argument("--script", type=pathlib.Path)
    ap.add_argument("--text")
    ap.add_argument("-o", "--output", type=pathlib.Path, required=True)
    ap.add_argument("--no-jitter", action="store_true", help="使用 config 固定 speed/pitch/vol")
    args = ap.parse_args()

    settings = load_settings()
    cfg = load_config(args.config.resolve())

    if args.text:
        text = re.sub(r"\s+", "", args.text)
    elif args.script:
        markers = cfg.get("script_extract", {}).get("markers", ["**口播："])
        text = extract_speech_from_script(args.script.resolve(), markers)
    else:
        sys.exit("请指定 --script 或 --text")

    if len(text) < 10:
        sys.exit(f"口播过短({len(text)}字)")
    if len(text) > 1_000_000:
        sys.exit(f"口播过长({len(text)}字),MiniMax 单次上限 100 万字")

    out = args.output.resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    fmt = cfg.get("output", {}).get("format", "mp3")
    tmp = out if out.suffix == ".mp3" else out.with_suffix(".mp3")

    voice = pick_jitter(cfg, jitter=not args.no_jitter)
    log.info(
        "MiniMax · %d 字 · %s · %s · speed %.2f · pitch %d · vol %.2f · %s",
        len(text), settings.model, settings.voice,
        voice.speed, voice.pitch, voice.vol, voice.emotion,
    )

    audio_cfg = cfg.get("audio_setting", {})
    http_cfg = cfg.get("http", {})
    poll_cfg = cfg.get("poll", {})

    task_id = submit_task(settings, text, voice, audio_cfg, http_cfg)
    log.info("已提交 task_id=%s,轮询中...", task_id)
    file_id = poll_task(settings, task_id, poll_cfg, http_cfg)
    log.info("任务完成 file_id=%s,取下载链接...", file_id)
    url = retrieve_file_url(settings, file_id, http_cfg)
    download(url, tmp, http_cfg)
    save_params(out, cfg, settings, voice)

    if fmt == "wav" or out.suffix == ".wav":
        sr = int(cfg.get("output", {}).get("sample_rate", 24000))
        to_wav(tmp, out, sr)
        log.info("OK %s", out)
    else:
        if out != tmp:
            tmp.rename(out)
        log.info("OK %s", out)


if __name__ == "__main__":
    main()
