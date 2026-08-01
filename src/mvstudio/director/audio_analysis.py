"""Deterministic audio features used by director map drafting."""

from __future__ import annotations

import hashlib
import json
import math
import os
import shutil
import subprocess
from pathlib import Path

import numpy as np

from .intake import IntakeContractError


def _audio_file(staging, relative):
    if (
        not isinstance(relative, str)
        or not relative.startswith("inputs/audio/")
        or relative.startswith("/")
        or "\\" in relative
        or any(part in {"", ".", ".."} for part in relative.split("/"))
    ):
        raise IntakeContractError("audio analysis path must be under inputs/audio")
    staging_path = Path(staging)
    if staging_path.is_symlink():
        raise IntakeContractError("audio analysis staging cannot be a symlink")
    root = staging_path.resolve()
    candidate = root / relative
    current = root
    for part in Path(relative).parts:
        current = current / part
        if current.is_symlink():
            raise IntakeContractError("audio analysis path contains a symlink")
    try:
        candidate.resolve(strict=True).relative_to(root)
    except (FileNotFoundError, ValueError) as exc:
        raise IntakeContractError("audio analysis path is missing or escapes staging") from exc
    if not candidate.is_file():
        raise IntakeContractError("audio analysis input must be a regular file")
    return candidate


def _decode(path, duration):
    if not isinstance(duration, (int, float)) or isinstance(duration, bool) or not math.isfinite(duration):
        raise IntakeContractError("audio duration must be finite")
    if duration <= 0 or duration > 1800:
        raise IntakeContractError("audio analysis supports durations up to 1800 seconds")
    ffmpeg = os.environ.get("MVSTUDIO_FFMPEG_PATH") or shutil.which("ffmpeg")
    if not ffmpeg:
        raise IntakeContractError("audio decode unavailable")
    command = [
        ffmpeg, "-v", "error", "-nostdin", "-i", str(path), "-t", str(duration + 0.1),
        "-f", "s16le", "-ac", "1", "-ar", "8000", "pipe:1",
    ]
    try:
        result = subprocess.run(
            command, capture_output=True, check=False, timeout=min(300, max(30, duration * 2))
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise IntakeContractError("audio decode unavailable") from exc
    if result.returncode != 0 or len(result.stdout) < 2:
        raise IntakeContractError("audio decode failed")
    return np.frombuffer(result.stdout, dtype="<i2").astype(np.float32) / 32768.0


def analyze_audio(staging, audio_manifest):
    if not isinstance(audio_manifest, dict):
        raise IntakeContractError("audio manifest must be a mapping")
    path = _audio_file(staging, audio_manifest.get("path"))
    expected_digest = audio_manifest.get("digest")
    if not isinstance(expected_digest, str) or not expected_digest.startswith("sha256:"):
        raise IntakeContractError("audio manifest digest is invalid")
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    if "sha256:" + digest.hexdigest() != expected_digest:
        raise IntakeContractError("audio input hash differs from intake manifest")
    samples = _decode(path, audio_manifest.get("duration_seconds"))
    sample_rate = 8000
    frame_samples = 400
    frame_count = len(samples) // frame_samples
    if frame_count < 2:
        raise IntakeContractError("audio is too short for analysis")
    framed = samples[:frame_count * frame_samples].reshape(frame_count, frame_samples)
    rms = np.sqrt(np.mean(np.square(framed), axis=1))
    flux = np.maximum(0.0, np.diff(rms, prepend=rms[0]))
    threshold = max(0.01, float(np.median(flux) + 1.5 * np.std(flux)))
    candidates = []
    minimum_gap = 3
    for index in range(1, len(flux) - 1):
        if flux[index] >= threshold and flux[index] >= flux[index - 1] and flux[index] >= flux[index + 1]:
            if not candidates or index - candidates[-1] >= minimum_gap:
                candidates.append(index)
            elif flux[index] > flux[candidates[-1]]:
                candidates[-1] = index
    onset_times = [round(index * frame_samples / sample_rate, 6) for index in candidates]
    intervals = np.diff(onset_times)
    intervals = intervals[(intervals >= 0.25) & (intervals <= 2.0)]
    bpm = None
    if len(intervals) >= 2:
        bpm = 60.0 / float(np.median(intervals))
        while bpm < 60:
            bpm *= 2
        while bpm > 180:
            bpm /= 2
        bpm = round(bpm, 3)
    frames = [
        {"at": round(index * frame_samples / sample_rate, 6), "rms": round(float(level), 8)}
        for index, level in enumerate(rms)
    ]
    digest = hashlib.sha256(
        json.dumps(frames, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {
        "version": 1,
        "source": audio_manifest["path"],
        "source_digest": audio_manifest.get("digest"),
        "sample_rate": sample_rate,
        "frame_ms": 50,
        "bpm_candidate": bpm,
        "onsets": onset_times,
        "energy_frames": frames,
        "analysis_hash": "sha256:" + digest,
        "producer": "mvstudio.director.audio_analysis",
        "status": "draft_self_generated",
    }


def energy_level(analysis, start, end):
    frames = analysis["energy_frames"]
    all_values = np.asarray([item["rms"] for item in frames], dtype=np.float64)
    selected = [item["rms"] for item in frames if start <= item["at"] < end]
    if not selected:
        return 1
    value = float(np.mean(selected))
    if float(np.max(all_values) - np.min(all_values)) < 1e-8:
        return 2
    thresholds = np.quantile(all_values, [0.2, 0.4, 0.6, 0.8])
    return 1 + int(sum(value > float(threshold) for threshold in thresholds))
