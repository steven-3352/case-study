"""Deterministic media intake from a job-local copy of project inputs."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import tempfile
import zipfile
import xml.etree.ElementTree as ET
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
_XLSX_NS = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


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


def _xlsx_shared_strings(archive):
    try:
        root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
    except KeyError:
        return []
    return ["".join(node.itertext()).strip() for node in root.findall("x:si", _XLSX_NS)]


def _xlsx_cell_value(cell, shared):
    value_node = cell.find("x:v", _XLSX_NS)
    if cell.get("t") == "inlineStr":
        inline = cell.find("x:is", _XLSX_NS)
        return "".join(inline.itertext()).strip() if inline is not None else ""
    if value_node is None or value_node.text is None:
        return ""
    value = value_node.text.strip()
    if cell.get("t") == "s":
        try:
            return shared[int(value)].strip()
        except (ValueError, IndexError) as exc:
            raise IntakeContractError("lyrics spreadsheet has an invalid shared string") from exc
    return value


def _split_character_names(value):
    value = value.strip()
    if not value:
        raise IntakeContractError("lyrics spreadsheet character cannot be empty")
    if value == "合":
        return ["合"]
    names = [item.strip() for item in re.split(r"[+＋、,，/&]", value) if item.strip()]
    if not names:
        raise IntakeContractError("lyrics spreadsheet character is invalid")
    return names


def parse_xlsx_director_sheet(path):
    """Read the first XLSX sheet as an immutable lyric/director timing contract."""
    try:
        with zipfile.ZipFile(path) as archive:
            infos = archive.infolist()
            if len(infos) > 200 or any(item.file_size > 20 * 1024 * 1024 for item in infos):
                raise IntakeContractError("lyrics spreadsheet is too large")
            shared = _xlsx_shared_strings(archive)
            workbook = ET.fromstring(archive.read("xl/workbook.xml"))
            sheet_root = ET.fromstring(archive.read("xl/worksheets/sheet1.xml"))
    except (KeyError, OSError, zipfile.BadZipFile, ET.ParseError) as exc:
        raise IntakeContractError("lyrics spreadsheet is invalid") from exc
    sheet_node = workbook.find(".//x:sheets/x:sheet", _XLSX_NS)
    sheet_name = sheet_node.get("name", "工作表1") if sheet_node is not None else "工作表1"
    rows = []
    for row in sheet_root.findall(".//x:sheetData/x:row", _XLSX_NS):
        values = {}
        for cell in row.findall("x:c", _XLSX_NS):
            reference = cell.get("r", "")
            column = "".join(char for char in reference if char.isalpha())
            if column:
                values[column] = _xlsx_cell_value(cell, shared)
        if values:
            rows.append((int(row.get("r", len(rows) + 1)), values))
    if len(rows) < 2:
        raise IntakeContractError("lyrics spreadsheet is empty")
    headers = {value.strip(): column for column, value in rows[0][1].items() if value.strip()}
    required = ("角色", "歌词", "起始时间", "结束时间")
    if any(name not in headers for name in required):
        raise IntakeContractError("lyrics spreadsheet requires 角色、歌词、起始时间、结束时间 columns")
    entries = []
    previous_end = -1.0
    for source_row, values in rows[1:]:
        lyric = values.get(headers["歌词"], "").strip()
        if not lyric:
            continue
        try:
            start = float(values.get(headers["起始时间"], ""))
            end = float(values.get(headers["结束时间"], ""))
        except ValueError as exc:
            raise IntakeContractError("lyrics spreadsheet time is invalid") from exc
        if start < 0 or end <= start or start < previous_end - 0.001:
            raise IntakeContractError("lyrics spreadsheet timeline is invalid")
        previous_end = end
        raw_characters = values.get(headers["角色"], "").strip()
        entries.append({
            "start_seconds": round(start, 6),
            "end_seconds": round(end, 6),
            "text": lyric,
            "character_names": _split_character_names(raw_characters),
            "character_label": raw_characters,
            "source_row": source_row,
            "source_sheet": sheet_name,
        })
    if not entries:
        raise IntakeContractError("lyrics spreadsheet has no lyric rows")
    return {
        "kind": "timed_spreadsheet",
        "alignment_state": "aligned_director_contract",
        "timed_entries": entries,
        "plain_lines": [],
        "plain_line_count": 0,
        "director_contract": {
            "sheet_name": sheet_name,
            "columns": list(required),
            "entry_count": len(entries),
            "characters_are_binding": True,
        },
    }


def _probe_lyrics(path):
    if path.suffix.lower() == ".xlsx":
        return parse_xlsx_director_sheet(path)
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
        "director_contract": None,
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
            "director_contract": lyrics.get("director_contract"),
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
