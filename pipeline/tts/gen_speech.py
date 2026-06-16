#!/usr/bin/env python3
"""Edge TTS · 从 script.md 提取口播 → speech 文件.

用法:
  python3 pipeline/tts/gen_speech.py --script pipeline/dry-run-001/script.md -o pipeline/dry-run-001/speech.mp3
  python3 pipeline/tts/gen_speech.py --text "你好" -o /tmp/test.mp3
"""
from __future__ import annotations

import argparse
import pathlib
import random
import re
import subprocess
import sys

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
