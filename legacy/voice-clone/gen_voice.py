#!/usr/bin/env python3
"""Voice clone CLI — 参考音 + 文案 → 口播 wav.

依赖：本地已启动 GPT-SoVITS api_v2（或其它兼容 HTTP 服务）。
用法：
  python3 pipeline/voice/gen_voice.py --script pipeline/dry-run-001/script.md -o out.wav
  python3 pipeline/voice/gen_voice.py --text "你好" -o out.wav
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import subprocess
import sys
import urllib.error
import urllib.request

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore

ROOT = pathlib.Path(__file__).resolve().parents[2]
CFG_PATH = pathlib.Path(__file__).resolve().parent / "config.yaml"


def _resolve_cfg_path(base: pathlib.Path, rel: str) -> pathlib.Path:
    p = pathlib.Path(rel)
    return p.resolve() if p.is_absolute() else (base / p).resolve()


def load_config(path: pathlib.Path, preset: str | None = None) -> dict:
    if yaml is None:
        sys.exit("需要 PyYAML: pip install pyyaml")
    with path.open(encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    voice = dict(cfg.get("voice", {}))
    if preset:
        presets = cfg.get("presets", {})
        if preset not in presets:
            sys.exit(f"未知 preset: {preset}，可选: {', '.join(presets) or '(无)'}")
        voice.update(presets[preset])
    ref = _resolve_cfg_path(path.parent, voice["ref_audio"])
    voice["ref_audio"] = str(ref)
    pf = voice.get("prompt_text_file")
    if pf and not voice.get("prompt_text"):
        ppath = _resolve_cfg_path(path.parent, pf)
        voice["prompt_text"] = ppath.read_text(encoding="utf-8").strip()
    cfg["voice"] = voice
    return cfg


def extract_speech_from_script(script_path: pathlib.Path, markers: list[str]) -> str:
    text = script_path.read_text(encoding="utf-8")
    parts: list[str] = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        hit = False
        for m in markers:
            if m in line:
                seg = line.split(m, 1)[-1].strip()
                if seg:
                    parts.append(seg)
                else:
                    # 口播在下一行（无 marker）
                    j = i + 1
                    while j < len(lines):
                        nxt = lines[j].strip()
                        if not nxt or nxt.startswith("#") or nxt.startswith("**") or nxt.startswith("[") or nxt.startswith("|") or nxt.startswith("---"):
                            break
                        parts.append(nxt)
                        j += 1
                    i = j - 1
                hit = True
                break
        i += 1
    if parts:
        return "".join(parts)
    return _extract_speech_fallback(text)


def extract_speech_sections_from_script(script_path: pathlib.Path, markers: list[str]) -> list[str]:
    """按「口播：」块提取，每块一段（与 script.md 结构对齐）。"""
    text = script_path.read_text(encoding="utf-8")
    sections: list[str] = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        for m in markers:
            if m not in line:
                continue
            seg = line.split(m, 1)[-1].strip()
            block: list[str] = [seg] if seg else []
            if not seg:
                j = i + 1
                while j < len(lines):
                    nxt = lines[j].strip()
                    if not nxt or nxt.startswith("#") or nxt.startswith("**") or nxt.startswith("[") or nxt.startswith("|") or nxt.startswith("---"):
                        break
                    block.append(nxt)
                    j += 1
                i = j - 1
            joined = "".join(block)
            joined = re.sub(r"\s+", "", joined)
            if joined:
                sections.append(joined)
            break
        i += 1
    if sections:
        return sections
    fallback = _extract_speech_fallback(text)
    return [fallback] if fallback else []


def _extract_speech_fallback(text: str) -> str:
    # fallback: 连续非空行（跳过 markdown 结构）
    body: list[str] = []
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("#") or s.startswith("|") or s.startswith("- ["):
            continue
        if s.startswith("**") and s.endswith("**") and "：" not in s:
            continue
        if s.startswith("**") and "：" in s:
            body.append(s.split("：", 1)[-1].rstrip("*").strip())
        elif not s.startswith("**") and not s.startswith("["):
            body.append(s)
    joined = "".join(body)
    if len(joined) < 10:
        return ""
    return joined


def split_text_chunks(text: str, max_chars: int = 50) -> list[str]:
    """按句号切分后合并为 ≤max_chars 的块，Mac MPS 上短段更稳。"""
    sentences = re.split(r"(?<=[。！？])", text)
    sentences = [s for s in sentences if s.strip()]
    if not sentences:
        return [text]
    chunks: list[str] = []
    buf = ""
    for s in sentences:
        if len(buf) + len(s) <= max_chars:
            buf += s
        else:
            if buf:
                chunks.append(buf)
            buf = s if len(s) <= max_chars else s
            while len(buf) > max_chars:
                chunks.append(buf[:max_chars])
                buf = buf[max_chars:]
    if buf:
        chunks.append(buf)
    return chunks


def synthesize_bytes(cfg: dict, text: str) -> bytes:
    base = cfg["api"]["base_url"].rstrip("/")
    path = cfg["api"].get("tts_path", "/tts")
    url = f"{base}{path}"
    infer = cfg.get("infer", {})
    payload = {
        "text": text,
        "text_lang": cfg["voice"]["text_lang"],
        "ref_audio_path": cfg["voice"]["ref_audio"],
        "prompt_text": cfg["voice"]["prompt_text"],
        "prompt_lang": cfg["voice"]["prompt_lang"],
        "speed_factor": cfg["voice"].get("speed", 1.0),
        "text_split_method": infer.get("text_split_method", "cut0"),
        "parallel_infer": infer.get("parallel_infer", False),
        "split_bucket": infer.get("split_bucket", False),
        "streaming_mode": False,
        "repetition_penalty": infer.get("repetition_penalty", 1.35),
        "top_k": infer.get("top_k", 15),
        "top_p": infer.get("top_p", 1.0),
        "temperature": infer.get("temperature", 1.0),
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    timeout = cfg["api"].get("timeout_sec", 120)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read()
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        sys.exit(f"API HTTP {e.code}: {body[:500]}")
    except urllib.error.URLError as e:
        sys.exit(
            f"无法连接 {url}\n"
            f"  {e.reason}\n"
            "请先启动 GPT-SoVITS: python api_v2.py -a 127.0.0.1 -p 9880\n"
            "详见 pipeline/voice/README.md"
        )


def concat_wavs(wav_paths: list[pathlib.Path], out: pathlib.Path, *, crossfade_ms: int = 0) -> None:
    if len(wav_paths) == 1:
        out.write_bytes(wav_paths[0].read_bytes())
        return
    if crossfade_ms <= 0:
        lst = out.with_suffix(".concat.txt")
        lst.write_text("\n".join(f"file '{p.resolve()}'" for p in wav_paths), encoding="utf-8")
        subprocess.run(
            ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(out)],
            check=True,
            capture_output=True,
        )
        lst.unlink(missing_ok=True)
        return
    d = crossfade_ms / 1000
    inputs: list[str] = []
    for p in wav_paths:
        inputs.extend(["-i", str(p)])
    label = "[0:a][1:a]acrossfade=d={d}[mix1]".format(d=d)
    out_label = "mix1"
    for i in range(2, len(wav_paths)):
        nxt = f"mix{i}"
        label += f";[{out_label}][{i}:a]acrossfade=d={d}[{nxt}]"
        out_label = nxt
    subprocess.run(
        ["ffmpeg", "-y", *inputs, "-filter_complex", label, "-map", f"[{out_label}]", str(out)],
        check=True,
        capture_output=True,
    )


def call_gpt_sovits(
    cfg: dict,
    text: str,
    out: pathlib.Path,
    *,
    chunks: list[str] | None = None,
    chunked: bool = False,
) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    chunk_cfg = cfg.get("chunk", {})
    chunk_size = chunk_cfg.get("max_chars", 50)
    auto_chunk = chunk_cfg.get("auto_above", 80)
    crossfade_ms = chunk_cfg.get("crossfade_ms", 0)

    if chunks:
        use_chunks = True
    elif chunked or len(text) > auto_chunk:
        use_chunks = True
        chunks = split_text_chunks(text, chunk_size)
    else:
        use_chunks = False

    if use_chunks:
        chunks = chunks or split_text_chunks(text, chunk_size)
        label = chunk_cfg.get("mode", "chars")
        print(f"分段合成 {len(chunks)} 段（{label}）")
        tmp_dir = out.parent / ".voice_chunks"
        tmp_dir.mkdir(exist_ok=True)
        parts: list[pathlib.Path] = []
        for i, chunk in enumerate(chunks, 1):
            part = tmp_dir / f"part_{i:02d}.wav"
            print(f"  [{i}/{len(chunks)}] {len(chunk)} 字 …")
            part.write_bytes(synthesize_bytes(cfg, chunk))
            parts.append(part)
        concat_wavs(parts, out, crossfade_ms=crossfade_ms)
        for p in parts:
            p.unlink(missing_ok=True)
        tmp_dir.rmdir()
    else:
        out.write_bytes(synthesize_bytes(cfg, text))

    if cfg["output"].get("format") == "mp3" and out.suffix == ".wav":
        mp3 = out.with_suffix(".mp3")
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(out), "-q:a", "2", str(mp3)],
            check=True,
            capture_output=True,
        )
        out.unlink()
        print("OK", mp3)
        return
    print("OK", out)


def main() -> None:
    ap = argparse.ArgumentParser(description="声音克隆：参考音 + 文案 → wav")
    ap.add_argument("--config", type=pathlib.Path, default=CFG_PATH)
    ap.add_argument("--script", type=pathlib.Path, help="从 script.md 提取口播")
    ap.add_argument("--text", help="直接指定口播全文")
    ap.add_argument("-o", "--output", type=pathlib.Path, required=True)
    ap.add_argument("--chunked", action="store_true", help="强制按字数分段合成")
    ap.add_argument("--preset", help="config.yaml presets 键名，如 narrative / turn / intro")
    args = ap.parse_args()

    cfg = load_config(args.config.resolve(), preset=args.preset)
    ref = pathlib.Path(cfg["voice"]["ref_audio"])
    if not ref.exists():
        sys.exit(f"参考音不存在: {ref}\n请录音放到 assets/avatar/dry_audio/dry_v1.wav")

    sections: list[str] | None = None
    if args.text:
        text = re.sub(r"\s+", "", args.text)
    elif args.script:
        markers = cfg.get("script_extract", {}).get("markers", ["**口播：**"])
        script_path = args.script.resolve()
        if cfg.get("chunk", {}).get("mode") == "script_sections" and not args.chunked:
            sections = extract_speech_sections_from_script(script_path, markers)
            text = "".join(sections)
        else:
            text = extract_speech_from_script(script_path, markers)
    else:
        sys.exit("请指定 --script 或 --text")

    text = re.sub(r"\s+", "", text)
    if len(text) < 10:
        sys.exit(f"口播过短（{len(text)}字），请检查 script 或 --text")
    if args.preset:
        print(f"preset: {args.preset}")
    print(f"合成 {len(text)} 字 → {args.output}")
    backend = cfg.get("backend", "gpt-sovits")
    if backend == "gpt-sovits":
        call_gpt_sovits(
            cfg, text, args.output.resolve(), chunks=sections, chunked=args.chunked
        )
    else:
        sys.exit(f"暂仅实现 backend=gpt-sovits，当前: {backend}")


if __name__ == "__main__":
    main()
