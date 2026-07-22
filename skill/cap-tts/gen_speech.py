#!/usr/bin/env python3
"""TTS 口播合成(能力封装版)· edge / minimax / volcengine 三 provider.

从 script.md 提取口播(按 markers)或直接给 --text,按 config.provider 合成 mp3/wav。
封装自 pipeline/tts/gen_speech.py + minimax_client.py + env_loader.py,解耦为可移植 bundle。

用法:
  python3 gen_speech.py --text "你好世界这是一段测试口播文本" -o out.mp3
  python3 gen_speech.py --script script.md -o out.mp3 --env ./.env
  python3 gen_speech.py --text "..." -o out.wav --provider edge

依赖:pyyaml(必需)· ffmpeg(仅 wav 输出需要)· edge-tts(edge provider 保底)。
env:MINIMAX_API_KEY/_BASE_URL/_GROUP_ID · VOLC_TTS_APPID/_TOKEN/_BASE_URL · edge 无需 key。
许可:自有代码,随引擎分发(MIT)。
"""
from __future__ import annotations

import argparse
import os
import pathlib
import random
import re
import subprocess
import sys

from local_env import api_base, load_dotenv

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore

CFG_PATH = pathlib.Path(__file__).resolve().parent / "config.yaml"
MINIMAX_EMOTIONS = {"happy", "sad", "angry", "fearful", "disgusted", "surprised", "neutral"}
MINIMAX_EMOTION_ALIASES = {"serious": "neutral", "calm": "neutral", "confident": "neutral"}


def normalize_minimax_emotion(emotion: str | None) -> str | None:
    if not emotion:
        return None
    normalized = MINIMAX_EMOTION_ALIASES.get(emotion, emotion)
    return normalized if normalized in MINIMAX_EMOTIONS else "neutral"


def load_config(path: pathlib.Path) -> dict:
    if yaml is None:
        sys.exit("需要 PyYAML: pip install pyyaml")
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def extract_speech_from_script(script_path: pathlib.Path, markers: list[str]) -> str:
    text = script_path.read_text(encoding="utf-8")
    parts: list[str] = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        for m in markers:
            if m in line:
                seg = line.split(m, 1)[-1].strip()
                if seg:
                    parts.append(seg)
                else:
                    j = i + 1
                    while j < len(lines):
                        nxt = lines[j].strip()
                        if not nxt or nxt.startswith("#") or nxt.startswith("**") or nxt.startswith("[") or nxt.startswith("|") or nxt.startswith("---"):
                            break
                        parts.append(nxt)
                        j += 1
                    i = j - 1
                break
        i += 1
    if not parts:
        sys.exit(f"未能从 {script_path} 提取口播")
    return re.sub(r"\s+", "", "".join(parts))


def pick_tts_params(cfg: dict, *, jitter: bool) -> tuple[str, str, str]:
    if jitter and cfg.get("jitter", False):
        rate = random.choice(cfg.get("rate_options", [cfg.get("rate", "+0%")]))
        pitch = random.choice(cfg.get("pitch_options", [cfg.get("pitch", "+0Hz")]))
        volume = random.choice(cfg.get("volume_options", [cfg.get("volume", "+0%")]))
        return rate, pitch, volume
    return cfg.get("rate", "+0%"), cfg.get("pitch", "+0Hz"), cfg.get("volume", "+0%")


def save_params(out: pathlib.Path, cfg: dict, provider: str) -> None:
    if not cfg.get("output", {}).get("save_params", True):
        return
    sidecar = out.with_suffix(".tts.yaml")
    voice = cfg.get("voice", "")
    if provider == "minimax":
        voice = cfg.get("minimax", {}).get("voice_id", voice)
    elif provider == "volcengine":
        voice = cfg.get("volcengine", {}).get("voice_type", voice)
    sidecar.write_text(f"provider: {provider}\nvoice: {voice}\n", encoding="utf-8")


def synthesize(text: str, voice: str, rate: str, pitch: str, volume: str, out: pathlib.Path) -> None:
    import shutil

    edge = shutil.which("edge-tts") or str(pathlib.Path(sys.executable).parent / "edge-tts")
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            edge,
            "--voice", voice,
            f"--rate={rate}",
            f"--pitch={pitch}",
            f"--volume={volume}",
            "--text", text,
            "--write-media", str(out),
        ],
        check=True,
        capture_output=True,
        text=True,
    )


def _synth_volcengine(text: str, cfg: dict, out_mp3: pathlib.Path) -> bool:
    """火山/豆包 大模型 TTS。需 VOLC_TTS_APPID + VOLC_TTS_TOKEN。返回是否成功。"""
    import base64
    import json
    import urllib.request

    appid, token = os.getenv("VOLC_TTS_APPID"), os.getenv("VOLC_TTS_TOKEN")
    if not (appid and token):
        return False
    v = cfg.get("volcengine", {})
    base = api_base("VOLC_TTS_BASE_URL", cfg=v.get("api_base"), default="https://openspeech.bytedance.com")
    body = {
        "app": {"appid": appid, "token": token, "cluster": v.get("cluster", "volcano_tts")},
        "user": {"uid": "content-engine"},
        "audio": {"voice_type": v.get("voice_type", "zh_male_M392_conversation_wvae_bigtts"),
                  "encoding": v.get("encoding", "mp3"), "speed_ratio": v.get("speed_ratio", 1.0)},
        "request": {"reqid": f"req-{random.randint(10**9, 10**10)}", "text": text, "operation": "query"},
    }
    req = urllib.request.Request(
        f"{base}/api/v1/tts",
        data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer;{token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.loads(r.read())
    audio = data.get("data")
    if not audio:
        raise RuntimeError(f"火山 TTS 无音频返回:{data.get('message') or data}")
    out_mp3.write_bytes(base64.b64decode(audio))
    return True


def _synth_minimax(
    text: str, cfg: dict, out_mp3: pathlib.Path, *, emotion: str | None = None, speed: float | None = None
) -> bool:
    """MiniMax TTS。async → t2a_async_v2 + speech-2.8-turbo。emotion/speed 可逐段覆盖。"""
    m = cfg.get("minimax", {})
    emotion = normalize_minimax_emotion(emotion)
    if m.get("mode", "async") == "async":
        from minimax_client import synth_async

        return synth_async(text, cfg, out_mp3, emotion=emotion, speed=speed)

    import json
    import urllib.request

    gid, key = os.getenv("MINIMAX_GROUP_ID"), os.getenv("MINIMAX_API_KEY")
    if not key:
        return False
    host = api_base("MINIMAX_BASE_URL", cfg=m.get("api_host"), default="https://api.minimaxi.com")
    url = f"{host}/v1/t2a_v2"
    if gid:
        url += f"?GroupId={gid}"
    voice_setting = {
        "voice_id": m.get("voice_id", "male-qn-badao"),
        "speed": speed if speed is not None else m.get("speed", 1.0),
        "vol": m.get("vol", 1.0),
        "pitch": m.get("pitch", 0),
    }
    emo = emotion or m.get("emotion")
    if emo:
        voice_setting["emotion"] = emo
    body = {
        "model": m.get("model", "speech-2.8-turbo"),
        "text": text,
        "stream": False,
        "language_boost": m.get("language_boost", "Chinese"),
        "voice_setting": voice_setting,
        "audio_setting": {"format": "mp3", "sample_rate": m.get("sample_rate", 32000)},
    }

    def _post(payload: dict) -> dict:
        req = urllib.request.Request(
            url, data=json.dumps(payload).encode(),
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())

    try:
        data = _post(body)
    except Exception:  # noqa: BLE001 — emotion 字段中转可能不支持,去掉重试一次
        if "emotion" in voice_setting:
            voice_setting.pop("emotion")
            data = _post(body)
        else:
            raise
    hex_audio = (data.get("data") or {}).get("audio")
    if not hex_audio:
        if "emotion" in voice_setting:
            voice_setting.pop("emotion")
            data = _post(body)
            hex_audio = (data.get("data") or {}).get("audio")
        if not hex_audio:
            raise RuntimeError(f"MiniMax 无音频返回:{data.get('base_resp') or data}")
    out_mp3.write_bytes(bytes.fromhex(hex_audio))
    return True


def synthesize_text(
    text: str,
    out_mp3: pathlib.Path,
    config_path: pathlib.Path = CFG_PATH,
    *,
    emotion: str | None = None,
    speed: float | None = None,
    provider: str | None = None,
) -> str:
    """按 config.provider(或 provider 覆盖)合成口播 mp3;自然 TTS 不可用则回落 edge。

    返回实际使用的 provider 名。
    """
    text = re.sub(r"\s+", "", text)
    out_mp3.parent.mkdir(parents=True, exist_ok=True)
    cfg = load_config(config_path.resolve())
    provider = provider or cfg.get("provider", "edge")
    strict_provider = bool(cfg.get("strict_provider", False))
    try:
        if provider == "volcengine" and _synth_volcengine(text, cfg, out_mp3):
            return "volcengine"
        if provider == "minimax" and _synth_minimax(text, cfg, out_mp3, emotion=emotion, speed=speed):
            return "minimax"
        if provider not in ("edge", "volcengine", "minimax"):
            if strict_provider:
                raise RuntimeError(f"未知 TTS provider: {provider}")
            print(f"  ⚠ 未知 provider {provider},回落 edge")
        elif provider != "edge":
            if strict_provider:
                raise RuntimeError(f"{provider} 凭证缺失或未返回音频")
            print(f"  ⚠ {provider} 凭证缺失,回落 edge")
    except Exception as e:  # noqa: BLE001 — 自然 TTS 失败回落 edge
        if strict_provider:
            raise RuntimeError(f"{provider} 合成失败;strict_provider 禁止回退") from e
        print(f"  ⚠ {provider} 合成失败回落 edge:{e}")
    rate, pitch, volume = pick_tts_params(cfg, jitter=cfg.get("jitter", False))
    synthesize(text, cfg["voice"], rate, pitch, volume, out_mp3)
    return "edge"


def to_wav(mp3: pathlib.Path, wav: pathlib.Path, sample_rate: int) -> None:
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(mp3), "-ar", str(sample_rate), "-ac", "1", str(wav)],
        check=True,
        capture_output=True,
    )
    mp3.unlink()


def main() -> None:
    ap = argparse.ArgumentParser(description="TTS 口播合成 · edge/minimax/volcengine")
    ap.add_argument("--config", type=pathlib.Path, default=CFG_PATH)
    ap.add_argument("--script", type=pathlib.Path, help="从 md 按 markers 提取口播")
    ap.add_argument("--text", help="直接给口播文本")
    ap.add_argument("-o", "--output", type=pathlib.Path, required=True)
    ap.add_argument("--provider", choices=["edge", "minimax", "volcengine"], help="覆盖 config.provider")
    ap.add_argument("--env", type=pathlib.Path, help="可选 .env 文件路径")
    args = ap.parse_args()

    if args.env:
        load_dotenv(args.env)

    cfg = load_config(args.config.resolve())
    if args.text:
        text = re.sub(r"\s+", "", args.text)
    elif args.script:
        markers = cfg.get("script_extract", {}).get("markers", ["**口播：**"])
        text = extract_speech_from_script(args.script.resolve(), markers)
    else:
        sys.exit("请指定 --script 或 --text")

    if len(text) < 10:
        sys.exit(f"口播过短({len(text)}字)")

    out = args.output.resolve()
    fmt = cfg.get("output", {}).get("format", "mp3")
    tmp = out if out.suffix == ".mp3" else out.with_suffix(".mp3")

    provider_used = synthesize_text(text, tmp, config_path=args.config, provider=args.provider)
    print(f"TTS · {len(text)} 字 · provider={provider_used}")
    save_params(out, cfg, provider_used)

    if fmt == "wav" or out.suffix == ".wav":
        sr = cfg.get("output", {}).get("sample_rate", 24000)
        to_wav(tmp, out, sr)
        print("OK", out)
    else:
        if out != tmp:
            tmp.rename(out)
        print("OK", out)


if __name__ == "__main__":
    main()
