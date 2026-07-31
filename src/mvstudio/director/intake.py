"""Deterministic media intake from a job-local copy of project inputs."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path

from PIL import Image


class IntakeContractError(ValueError):
    pass


_LRC_TIMESTAMP = re.compile(r"\[(\d{1,3}):(\d{2})(?:[.:](\d{1,3}))?\]")
_ALLOWED_PREFIXES = {
    "audio": "inputs/audio/",
    "lyrics": "inputs/lyrics/",
    "characters": "inputs/characters/",
}


def _canonical_bytes(value):
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _atomic_write(path, content):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".intake-", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _digest(path):
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
            size += len(chunk)
    return "sha256:" + digest.hexdigest(), size


def _project_path(value, kind):
    if not isinstance(value, str) or not value or value.startswith("/") or "\\" in value:
        raise IntakeContractError(kind + " path must be project-relative POSIX")
    parts = value.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise IntakeContractError(kind + " path must be project-relative POSIX")
    if not value.startswith(_ALLOWED_PREFIXES[kind]):
        raise IntakeContractError(kind + " path is outside its input directory")
    return value


def validate_intake(value):
    if not isinstance(value, Mapping):
        raise IntakeContractError("intake must be a mapping")
    if set(value) - {"project_id", "audio", "lyrics", "characters"}:
        raise IntakeContractError("unknown intake field")
    project_id = value.get("project_id")
    if not isinstance(project_id, str) or not project_id:
        raise IntakeContractError("project_id must be non-empty text")
    audio = _project_path(value.get("audio"), "audio")
    lyrics = _project_path(value.get("lyrics"), "lyrics")
    characters = value.get("characters")
    if isinstance(characters, (str, bytes)) or not isinstance(characters, Sequence) or not characters:
        raise IntakeContractError("characters must be a non-empty sequence")
    normalized = tuple(_project_path(item, "characters") for item in characters)
    if len(set(normalized)) != len(normalized):
        raise IntakeContractError("character paths must be unique")
    return {"project_id": project_id, "audio": audio, "lyrics": lyrics, "characters": normalized}


def _regular_file(root, relative):
    root = Path(root).resolve()
    candidate = root / relative
    current = root
    for part in Path(relative).parts:
        current = current / part
        if current.is_symlink():
            raise IntakeContractError("input path contains a symlink")
    try:
        candidate.resolve(strict=True).relative_to(root)
    except (FileNotFoundError, ValueError) as exc:
        raise IntakeContractError("input path is missing or escapes staging") from exc
    if not candidate.is_file():
        raise IntakeContractError("input path must be a regular file")
    return candidate


def _probe_audio(path):
    command = [
        "ffprobe", "-v", "error", "-show_entries",
        "format=format_name,duration,size:stream=index,codec_type,codec_name,sample_rate,channels",
        "-of", "json", str(path),
    ]
    try:
        result = subprocess.run(command, capture_output=True, check=False, timeout=30)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise IntakeContractError("audio probe unavailable") from exc
    if result.returncode != 0:
        raise IntakeContractError("audio probe failed")
    try:
        payload = json.loads(result.stdout)
        audio_streams = [item for item in payload.get("streams", []) if item.get("codec_type") == "audio"]
        duration = float(payload["format"]["duration"])
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise IntakeContractError("audio probe returned invalid metadata") from exc
    if duration <= 0 or not audio_streams:
        raise IntakeContractError("audio must contain a positive-duration audio stream")
    stream = audio_streams[0]
    return {
        "format": payload["format"].get("format_name", "unknown"),
        "duration_seconds": round(duration, 6),
        "codec": stream.get("codec_name", "unknown"),
        "sample_rate": int(stream["sample_rate"]) if stream.get("sample_rate") else None,
        "channels": int(stream["channels"]) if stream.get("channels") else None,
    }


def parse_lrc(text):
    entries = []
    for line_number, line in enumerate(text.splitlines(), 1):
        matches = list(_LRC_TIMESTAMP.finditer(line))
        if not matches:
            continue
        lyric = _LRC_TIMESTAMP.sub("", line).strip()
        for match in matches:
            minute, second = int(match.group(1)), int(match.group(2))
            if second >= 60:
                raise IntakeContractError("invalid LRC timestamp")
            fraction_text = match.group(3) or "0"
            fraction = int(fraction_text) / (10 ** len(fraction_text))
            entries.append({
                "start_seconds": round(minute * 60 + second + fraction, 6),
                "text": lyric,
                "source_line": line_number,
            })
    entries.sort(key=lambda item: (item["start_seconds"], item["source_line"]))
    for current, following in zip(entries, entries[1:]):
        current["end_seconds"] = following["start_seconds"]
    if entries:
        entries[-1]["end_seconds"] = None
    return entries


def _probe_lyrics(path):
    try:
        text = path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError as exc:
        raise IntakeContractError("lyrics must be UTF-8 text") from exc
    timed = parse_lrc(text)
    plain_lines = [
        {"text": line.strip(), "source_line": line_number}
        for line_number, line in enumerate(text.splitlines(), 1)
        if line.strip() and not line.lstrip().startswith("[")
    ]
    if timed and plain_lines:
        raise IntakeContractError("lyrics cannot mix timed and plain lines")
    if not timed and not plain_lines:
        raise IntakeContractError("lyrics cannot be empty")
    return {
        "kind": "timed_lrc" if timed else "plain_text",
        "alignment_state": "aligned" if timed else "alignment_required",
        "timed_entries": timed,
        "plain_lines": plain_lines,
        "plain_line_count": len(plain_lines),
    }


def _probe_character(path):
    try:
        with Image.open(path) as image:
            image.verify()
        with Image.open(path) as image:
            bands = image.getbands()
            metadata = {
                "format": image.format,
                "width": image.width,
                "height": image.height,
                "mode": image.mode,
                "has_alpha": "A" in bands or "transparency" in image.info,
            }
    except (OSError, ValueError) as exc:
        raise IntakeContractError("character input is not a supported image") from exc
    return metadata


def inspect_intake(value, staging):
    value = validate_intake(value)
    staging_path = Path(staging)
    if staging_path.is_symlink():
        raise IntakeContractError("staging directory cannot be a symlink")
    root = staging_path.resolve()
    intake_directory = root / "intake"
    if intake_directory.is_symlink():
        raise IntakeContractError("intake output directory cannot be a symlink")
    intake_directory.mkdir(parents=True, exist_ok=True)
    audio_path = _regular_file(root, value["audio"])
    lyrics_path = _regular_file(root, value["lyrics"])
    audio_hash, audio_size = _digest(audio_path)
    lyrics_hash, lyrics_size = _digest(lyrics_path)
    audio = _probe_audio(audio_path)
    lyrics = _probe_lyrics(lyrics_path)
    if any(
        item["start_seconds"] > audio["duration_seconds"] + 0.05
        for item in lyrics["timed_entries"]
    ):
        raise IntakeContractError("timed lyrics exceed audio duration")
    characters = []
    for relative in value["characters"]:
        path = _regular_file(root, relative)
        digest, size = _digest(path)
        characters.append({"path": relative, "digest": digest, "size_bytes": size, **_probe_character(path)})
    manifest = {
        "version": 1,
        "project_id": value["project_id"],
        "status": "intake_validated",
        "audio": {"path": value["audio"], "digest": audio_hash, "size_bytes": audio_size, **audio},
        "lyrics": {
            "path": value["lyrics"], "digest": lyrics_hash, "size_bytes": lyrics_size,
            "kind": lyrics["kind"], "alignment_state": lyrics["alignment_state"],
            "plain_line_count": lyrics["plain_line_count"],
        },
        "characters": characters,
    }
    _atomic_write(root / "intake/intake_manifest.json", _canonical_bytes(manifest))
    if lyrics["timed_entries"]:
        timed = {"version": 1, "source": value["lyrics"], "entries": lyrics["timed_entries"]}
        _atomic_write(root / "intake/lyrics_timed.json", _canonical_bytes(timed))
    elif lyrics["plain_lines"]:
        plain = {
            "version": 1,
            "source": value["lyrics"],
            "source_digest": lyrics_hash,
            "lines": lyrics["plain_lines"],
        }
        _atomic_write(root / "intake/lyrics_plain.json", _canonical_bytes(plain))
    return manifest
