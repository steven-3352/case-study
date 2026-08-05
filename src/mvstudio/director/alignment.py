"""Validated plain-lyric alignment with explicit provider evidence."""

from __future__ import annotations

import hashlib
import json
import math
import os
import tempfile
import unicodedata
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


class LyricAlignmentError(ValueError):
    pass


def normalize_token(value):
    """Casefolded, punctuation-free NFKC token used to align transcript↔lyrics.

    Single definition shared by the strict provider path and the tolerant
    proportional mapper so both count characters identically (CJK included —
    ``str.isalnum`` is True for CJK ideographs).
    """
    return "".join(
        character.casefold()
        for character in unicodedata.normalize("NFKC", value or "")
        if character.isalnum()
    )


def proportional_entries(words, lines, duration):
    """Tolerant lyric→time mapping: supplied ``lines`` are authoritative, Whisper
    word timestamps supply timing only.

    Unlike the strict provider gate (transcript must exactly cover the lyrics —
    impossible for sung audio), this maps each line's cumulative normalized-char
    ratio onto the transcript's char→time sequence. Transcript and lyric char
    counts need not match. Falls back to an even spread when Whisper returns no
    words (instrumental/silence). Output satisfies ``_validated_entries``: one
    entry per line, strictly-advancing starts inside ``[0, duration)``, text and
    ``source_line`` preserved, confidence in ``[0, 1]``.

    Args:
        words: list of ``{text, start, end, probability}`` (probability optional).
        lines: list of ``{text, source_line}`` — the authoritative lyric lines.
        duration: audio duration in seconds (> 0).

    Returns:
        list of ``{text, source_line, start_seconds, confidence}``.
    """
    duration = float(duration)
    if duration <= 0:
        raise LyricAlignmentError("proportional alignment duration must be positive")
    prepared = [
        {"text": line["text"], "source_line": line["source_line"], "norm": normalize_token(line["text"])}
        for line in lines
    ]
    line_lengths = [max(len(item["norm"]), 1) for item in prepared]
    total_chars = sum(line_lengths)

    char_times = []
    char_probs = []
    for word in words:
        span = len(normalize_token(word.get("text", "")))
        if span <= 0:
            continue
        start = float(word["start"])
        prob = word.get("probability")
        prob = float(prob) if isinstance(prob, (int, float)) else 0.5
        char_times.extend([start] * span)
        char_probs.extend([prob] * span)

    raw = []
    if char_times:
        n_time = len(char_times)
        cumulative = 0
        for item, length in zip(prepared, line_lengths):
            position = int(round(cumulative / total_chars * (n_time - 1)))
            position = min(position, n_time - 1)
            raw.append((item, char_times[position], char_probs[position]))
            cumulative += length
    else:
        step = duration / len(prepared)
        for index, item in enumerate(prepared):
            raw.append((item, index * step, 0.0))

    # Enforce strictly-increasing starts inside [0, duration). ``epsilon`` shrinks
    # with the line count so ``count`` entries always fit: a per-entry ceiling
    # ``duration - (count - i) * epsilon`` reserves room for the entries that
    # follow, so even lines that all map to the same late timestamp spread out
    # cleanly instead of marching past the end.
    count = len(raw)
    epsilon = min(0.05, duration / (count + 1))
    entries = []
    previous = -epsilon
    for index, (item, start, prob) in enumerate(raw):
        ceiling = duration - (count - index) * epsilon
        start = min(max(float(start), previous + epsilon), ceiling)
        confidence = max(0.0, min(1.0, float(prob)))
        entries.append({
            "text": item["text"],
            "source_line": item["source_line"],
            "start_seconds": round(start, 6),
            "confidence": round(confidence, 6),
        })
        previous = start
    return entries


@dataclass(frozen=True)
class AlignmentTask:
    audio_path: Path
    audio_digest: str
    duration_seconds: float
    lines: tuple


@dataclass(frozen=True)
class AlignmentResult:
    entries: tuple
    provider: str
    model: str
    evidence: Mapping


class LyricAlignmentPort(Protocol):
    def align(self, task: AlignmentTask) -> AlignmentResult:
        ...


def _canonical(value):
    try:
        return json.dumps(
            value,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise LyricAlignmentError("alignment contract must be JSON-compatible") from exc


def _atomic_write(path, content):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".alignment-", dir=str(path.parent))
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
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _load_mapping(path, label):
    try:
        value = json.loads(Path(path).read_bytes())
    except (OSError, json.JSONDecodeError) as exc:
        raise LyricAlignmentError(label + " is invalid") from exc
    if not isinstance(value, Mapping):
        raise LyricAlignmentError(label + " must be a mapping")
    return value


def _source_audio(staging, manifest):
    relative = manifest.get("audio", {}).get("path")
    if not isinstance(relative, str):
        raise LyricAlignmentError("intake audio path is invalid")
    root = Path(staging).resolve()
    candidate = root / relative
    current = root
    for part in Path(relative).parts:
        current = current / part
        if current.is_symlink():
            raise LyricAlignmentError("alignment audio path contains a symlink")
    if not candidate.is_file():
        raise LyricAlignmentError("alignment audio must be a regular non-symlink file")
    try:
        candidate.resolve(strict=True).relative_to(root)
    except (FileNotFoundError, ValueError) as exc:
        raise LyricAlignmentError("alignment audio escapes staging") from exc
    expected = manifest["audio"].get("digest")
    if not isinstance(expected, str) or _digest(candidate) != expected:
        raise LyricAlignmentError("alignment audio hash differs from intake")
    return candidate


def _plain_lines(value):
    if value.get("version") != 1:
        raise LyricAlignmentError("plain lyrics contract version is invalid")
    raw = value.get("lines")
    if isinstance(raw, (str, bytes)) or not isinstance(raw, Sequence) or not raw:
        raise LyricAlignmentError("plain lyrics must contain lines")
    lines = []
    for item in raw:
        if not isinstance(item, Mapping) or set(item) != {"text", "source_line"}:
            raise LyricAlignmentError("plain lyric line contract is invalid")
        text = item["text"]
        source_line = item["source_line"]
        if not isinstance(text, str) or not text.strip():
            raise LyricAlignmentError("plain lyric text must be non-empty")
        if isinstance(source_line, bool) or not isinstance(source_line, int) or source_line < 1:
            raise LyricAlignmentError("plain lyric source line is invalid")
        lines.append({"text": text.strip(), "source_line": source_line})
    return lines


def _validated_entries(result, lines, duration):
    if not isinstance(result, AlignmentResult):
        raise LyricAlignmentError("alignment provider must return AlignmentResult")
    if (
        not isinstance(result.provider, str)
        or not result.provider.strip()
        or not isinstance(result.model, str)
        or not result.model.strip()
    ):
        raise LyricAlignmentError("alignment provider identity is required")
    if not isinstance(result.evidence, Mapping) or not result.evidence:
        raise LyricAlignmentError("alignment provider evidence is required")
    if (
        isinstance(result.entries, (str, bytes))
        or not isinstance(result.entries, Sequence)
    ):
        raise LyricAlignmentError("alignment provider entries must be a sequence")
    entries = list(result.entries)
    if len(entries) != len(lines):
        raise LyricAlignmentError("alignment must cover every plain lyric line")
    validated = []
    previous_start = -1.0
    for expected, entry in zip(lines, entries):
        if not isinstance(entry, Mapping):
            raise LyricAlignmentError("aligned lyric entry must be a mapping")
        if set(entry) != {"text", "source_line", "start_seconds", "confidence"}:
            raise LyricAlignmentError("aligned lyric entry contract is invalid")
        if entry["text"] != expected["text"] or entry["source_line"] != expected["source_line"]:
            raise LyricAlignmentError("alignment changed plain lyric text or order")
        start = entry["start_seconds"]
        confidence = entry["confidence"]
        if (
            isinstance(start, bool)
            or not isinstance(start, (int, float))
            or not math.isfinite(float(start))
            or float(start) < 0
            or float(start) >= duration
            or float(start) <= previous_start
        ):
            raise LyricAlignmentError("aligned lyric starts must strictly advance within audio")
        if (
            isinstance(confidence, bool)
            or not isinstance(confidence, (int, float))
            or not math.isfinite(float(confidence))
            or not 0 <= float(confidence) <= 1
        ):
            raise LyricAlignmentError("alignment confidence is invalid")
        previous_start = float(start)
        validated.append({
            "start_seconds": round(float(start), 6),
            "text": expected["text"],
            "source_line": expected["source_line"],
            "confidence": round(float(confidence), 6),
        })
    for current, following in zip(validated, validated[1:]):
        current["end_seconds"] = following["start_seconds"]
    validated[-1]["end_seconds"] = round(duration, 6)
    return validated


def align_plain_lyrics(intake, staging, port):
    if not isinstance(intake, Mapping) or intake.get("status") != "intake_validated":
        raise LyricAlignmentError("validated intake manifest is required")
    lyrics = intake.get("lyrics")
    if not isinstance(lyrics, Mapping) or lyrics.get("kind") != "plain_text":
        raise LyricAlignmentError("plain lyrics intake is required")
    if lyrics.get("alignment_state") != "alignment_required":
        raise LyricAlignmentError("plain lyrics are not awaiting alignment")
    duration = intake.get("audio", {}).get("duration_seconds")
    if (
        isinstance(duration, bool)
        or not isinstance(duration, (int, float))
        or not math.isfinite(float(duration))
        or duration <= 0
    ):
        raise LyricAlignmentError("alignment audio duration is invalid")
    staging_path = Path(staging)
    if staging_path.is_symlink():
        raise LyricAlignmentError("alignment staging cannot be a symlink")
    root = staging_path.resolve()
    intake_directory = root / "intake"
    if intake_directory.is_symlink():
        raise LyricAlignmentError("alignment intake directory cannot be a symlink")
    plain_path = root / "intake/lyrics_plain.json"
    if plain_path.is_symlink():
        raise LyricAlignmentError("plain lyrics contract cannot be a symlink")
    plain = _load_mapping(plain_path, "plain lyrics contract")
    if plain.get("source_digest") != lyrics.get("digest"):
        raise LyricAlignmentError("plain lyrics hash differs from intake")
    lines = _plain_lines(plain)
    audio_path = _source_audio(root, intake)
    task = AlignmentTask(
        audio_path=audio_path,
        audio_digest=intake["audio"]["digest"],
        duration_seconds=float(duration),
        lines=tuple(lines),
    )
    try:
        result = port.align(task)
    except LyricAlignmentError:
        raise
    except Exception as exc:
        raise LyricAlignmentError("lyric alignment provider failed") from exc
    entries = _validated_entries(result, lines, float(duration))
    evidence_bytes = _canonical(result.evidence)
    evidence_hash = "sha256:" + hashlib.sha256(evidence_bytes).hexdigest()
    timed = {
        "version": 1,
        "source": plain["source"],
        "alignment": {
            "mode": "provider_word_timestamps",
            "provider": result.provider,
            "model": result.model,
            "audio_digest": task.audio_digest,
            "lyrics_digest": lyrics["digest"],
            "evidence_hash": evidence_hash,
        },
        "entries": entries,
    }
    updated = json.loads(_canonical(intake))
    updated["lyrics"]["alignment_state"] = "aligned_provider"
    audit = {"version": 1, "status": "draft_self_generated", **timed["alignment"]}
    evidence = {
        "version": 1,
        "status": "draft_self_generated",
        "provider": result.provider,
        "model": result.model,
        "evidence_hash": evidence_hash,
        "evidence": result.evidence,
    }
    _atomic_write(root / "intake/lyrics_timed.json", _canonical(timed))
    _atomic_write(root / "intake/lyrics_alignment_audit.json", _canonical(audit))
    _atomic_write(root / "intake/lyrics_alignment_evidence.json", _canonical(evidence))
    _atomic_write(root / "intake/intake_manifest.json", _canonical(updated))
    return updated, timed
