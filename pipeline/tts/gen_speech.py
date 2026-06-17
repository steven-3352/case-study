#!/usr/bin/env python3
"""Edge TTS · 从 script.md 提取口播 → speech 文件.

用法:
  python3 pipeline/tts/gen_speech.py --script pipeline/dry-run-001/script.md -o pipeline/dry-run-001/speech.mp3
  python3 pipeline/tts/gen_speech.py --text "你好" -o /tmp/test.mp3
"""
from __future__ import annotations

import argparse
import os
import pathlib
import random
import re
import subprocess
import sys

import pipeline.env_loader  # noqa: F401 — 加载 .env
from pipeline.env_loader import api_base

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore

CFG_PATH = pathlib.Path(__file__).resolve().parent / "config.yaml"


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


def save_params(out: pathlib.Path, cfg: dict, rate: str, pitch: str, volume: str) -> None:
    if not cfg.get("output", {}).get("save_params", True):
        return
    sidecar = out.with_suffix(".tts.yaml")
    body = (
        f"voice: {cfg['voice']}\n"
        f"rate: {rate}\n"
        f"pitch: {pitch}\n"
        f"volume: {volume}\n"
    )
    sidecar.write_text(body, encoding="utf-8")


def synthesize(text: str, voice: str, rate: str, pitch: str, volume: str, out: pathlib.Path) -> None:
    import shutil

    edge = shutil.which("edge-tts") or str(pathlib.Path(sys.executable).parent / "edge-tts")
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            edge,
            "--voice", voice,
            "--rate", rate,
            "--pitch", pitch,
            "--volume", volume,
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
        "user": {"uid": "case-study"},
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
        raise RuntimeError(f"火山 TTS 无音频返回：{data.get('message') or data}")
    out_mp3.write_bytes(base64.b64decode(audio))
    return True


def _synth_minimax(text: str, cfg: dict, out_mp3: pathlib.Path) -> bool:
    """MiniMax TTS。async → t2a_async_v2 + speech-2.8-turbo。"""
    from pipeline.tts.minimax_client import synth_async

    m = cfg.get("minimax", {})
    if m.get("mode", "async") == "async":
        return synth_async(text, cfg, out_mp3)

    # 旧版同步 t2a_v2 保底
    import json
    import urllib.request

    gid, key = os.getenv("MINIMAX_GROUP_ID"), os.getenv("MINIMAX_API_KEY")
    if not key:
        return False
    host = api_base("MINIMAX_BASE_URL", cfg=m.get("api_host"), default="https://api.minimaxi.com")
    url = f"{host}/v1/t2a_v2"
    if gid:
        url += f"?GroupId={gid}"
    body = {
        "model": m.get("model", "speech-2.8-turbo"),
        "text": text,
        "stream": False,
        "language_boost": m.get("language_boost", "Chinese"),
        "voice_setting": {
            "voice_id": m.get("voice_id", "male-qn-badao"),
            "speed": m.get("speed", 1.0),
        },
        "audio_setting": {"format": "mp3", "sample_rate": m.get("sample_rate", 32000)},
    }
    req = urllib.request.Request(
        url, data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.loads(r.read())
    hex_audio = (data.get("data") or {}).get("audio")
    if not hex_audio:
        raise RuntimeError(f"MiniMax 无音频返回：{data.get('base_resp') or data}")
    out_mp3.write_bytes(bytes.fromhex(hex_audio))
    return True


def synthesize_text(text: str, out_mp3: pathlib.Path, config_path: pathlib.Path = CFG_PATH) -> str:
    """供 render.py 调用：按 config.provider 合成口播 mp3，自然 TTS 不可用则回落 edge。

    返回实际使用的 provider 名。
    """
    text = re.sub(r"\s+", "", text)
    out_mp3.parent.mkdir(parents=True, exist_ok=True)
    cfg = load_config(config_path.resolve())
    provider = cfg.get("provider", "edge")
    try:
        if provider == "volcengine" and _synth_volcengine(text, cfg, out_mp3):
            return "volcengine"
        if provider == "minimax" and _synth_minimax(text, cfg, out_mp3):
            return "minimax"
        if provider not in ("edge", "volcengine", "minimax"):
            print(f"  ⚠ 未知 provider {provider}，回落 edge")
        elif provider != "edge":
            print(f"  ⚠ {provider} 凭证缺失，回落 edge")
    except Exception as e:  # noqa: BLE001 — 自然 TTS 失败回落 edge
        print(f"  ⚠ {provider} 合成失败回落 edge：{e}")
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
    ap = argparse.ArgumentParser(description="Edge TTS：script.md → 口播")
    ap.add_argument("--config", type=pathlib.Path, default=CFG_PATH)
    ap.add_argument("--script", type=pathlib.Path)
    ap.add_argument("--text")
    ap.add_argument("-o", "--output", type=pathlib.Path, required=True)
    ap.add_argument("--no-jitter", action="store_true", help="使用 config 固定 rate/pitch/volume")
    args = ap.parse_args()

    cfg = load_config(args.config.resolve())
    if args.text:
        text = re.sub(r"\s+", "", args.text)
    elif args.script:
        markers = cfg.get("script_extract", {}).get("markers", ["**口播：**"])
        text = extract_speech_from_script(args.script.resolve(), markers)
    else:
        sys.exit("请指定 --script 或 --text")

    if len(text) < 10:
        sys.exit(f"口播过短（{len(text)}字）")

    out = args.output.resolve()
    fmt = cfg.get("output", {}).get("format", "mp3")
    tmp = out if out.suffix == ".mp3" else out.with_suffix(".mp3")

    rate, pitch, volume = pick_tts_params(cfg, jitter=not args.no_jitter)
    print(f"Edge TTS · {len(text)} 字 · {cfg['voice']} · rate {rate} · pitch {pitch} · volume {volume}")
    synthesize(text, cfg["voice"], rate, pitch, volume, tmp)
    save_params(out, cfg, rate, pitch, volume)

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
