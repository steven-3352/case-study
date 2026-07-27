#!/usr/bin/env python3
"""Validate the structural director contract for a paper-doll MV."""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path
from typing import Any

import yaml


TECHNIQUES = {"2.5d", "static", "i2v", "hybrid"}
TRANSITIONS = {
    "none",
    "hard_cut",
    "occlusion_cut",
    "action_match",
    "crossfade",
    "flash_white",
    "ink_wipe",
    "light_wipe",
    "bridge_clip",
}
LEVERAGES = {"completion_3s", "completion_rate", "comprehension", "save", "comment"}
REQUIRED_SHOT_FIELDS = {
    "id",
    "time",
    "section",
    "energy",
    "purpose",
    "leverage",
    "characters",
    "composition",
    "primary_action",
    "beats",
    "first_frame",
    "last_frame",
    "transition_out",
    "technique",
    "assets",
}


class Report:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)


def _time_pair(value: Any) -> tuple[float, float] | None:
    if not isinstance(value, list) or len(value) != 2:
        return None
    try:
        start, end = float(value[0]), float(value[1])
    except (TypeError, ValueError):
        return None
    if not math.isfinite(start) or not math.isfinite(end):
        return None
    return start, end


def validate(data: Any) -> Report:
    report = Report()
    if not isinstance(data, dict):
        report.error("root must be a mapping")
        return report

    for field in ("project", "characters", "sections", "shots"):
        if field not in data:
            report.error(f"missing top-level field: {field}")

    project = data.get("project", {})
    if not isinstance(project, dict):
        report.error("project must be a mapping")
        return report

    try:
        duration = float(project.get("duration"))
    except (TypeError, ValueError):
        duration = -1
        report.error("project.duration must be a positive number")
    if duration <= 0:
        report.error("project.duration must be > 0")

    characters = data.get("characters", [])
    if not isinstance(characters, list) or not characters:
        report.error("characters must be a non-empty list")
        characters = []
    character_ids = {
        str(item.get("id"))
        for item in characters
        if isinstance(item, dict) and item.get("id") is not None
    }
    if len(character_ids) != len(characters):
        report.error("each character needs a unique id")

    sections = data.get("sections", [])
    if not isinstance(sections, list) or not sections:
        report.error("sections must be a non-empty list")
        sections = []
    section_ids = {
        str(item.get("id"))
        for item in sections
        if isinstance(item, dict) and item.get("id") is not None
    }

    shots = data.get("shots", [])
    if not isinstance(shots, list) or not shots:
        report.error("shots must be a non-empty list")
        return report

    parsed: list[tuple[str, float, float, dict[str, Any]]] = []
    seen_shot_ids: set[str] = set()
    energies: list[int] = []
    relation_shots = 0

    for index, raw in enumerate(shots):
        label = f"shots[{index}]"
        if not isinstance(raw, dict):
            report.error(f"{label} must be a mapping")
            continue
        sid = str(raw.get("id", label))
        missing = sorted(REQUIRED_SHOT_FIELDS - raw.keys())
        if missing:
            report.error(f"{sid}: missing fields: {', '.join(missing)}")
        if sid in seen_shot_ids:
            report.error(f"duplicate shot id: {sid}")
        seen_shot_ids.add(sid)

        times = _time_pair(raw.get("time"))
        if times is None or times[1] <= times[0]:
            report.error(f"{sid}: time must be [start, end] with end > start")
            continue
        start, end = times
        parsed.append((sid, start, end, raw))

        section = str(raw.get("section", ""))
        if section_ids and section not in section_ids:
            report.error(f"{sid}: unknown section {section!r}")

        try:
            energy = int(raw.get("energy"))
        except (TypeError, ValueError):
            energy = 0
        if energy not in range(1, 6):
            report.error(f"{sid}: energy must be an integer from 1 to 5")
        else:
            energies.append(energy)

        for field in ("purpose", "primary_action", "first_frame", "last_frame"):
            value = raw.get(field)
            if not isinstance(value, str) or not value.strip():
                report.error(f"{sid}: {field} must be a non-empty string")

        if raw.get("leverage") not in LEVERAGES:
            report.error(f"{sid}: leverage must be one of {sorted(LEVERAGES)}")
        if raw.get("technique") not in TECHNIQUES:
            report.error(f"{sid}: technique must be one of {sorted(TECHNIQUES)}")

        shot_characters = raw.get("characters")
        if not isinstance(shot_characters, list):
            report.error(f"{sid}: characters must be a list")
        else:
            unknown = sorted(set(map(str, shot_characters)) - character_ids)
            if unknown:
                report.error(f"{sid}: unknown characters: {', '.join(unknown)}")
            if len(shot_characters) >= 2:
                relation_shots += 1

        composition = raw.get("composition")
        if not isinstance(composition, dict) or not composition.get("shot_size"):
            report.error(f"{sid}: composition.shot_size is required")

        transition = raw.get("transition_out")
        if not isinstance(transition, dict):
            report.error(f"{sid}: transition_out must be a mapping")
        else:
            if transition.get("type") not in TRANSITIONS:
                report.error(f"{sid}: unsupported transition type {transition.get('type')!r}")
            if transition.get("type") != "none" and not transition.get("shared_element"):
                report.error(f"{sid}: non-terminal transition needs shared_element")

        beats = raw.get("beats")
        if not isinstance(beats, list) or not beats:
            report.error(f"{sid}: beats must contain at least one event")
        else:
            for beat_index, beat in enumerate(beats):
                if not isinstance(beat, dict):
                    report.error(f"{sid}: beats[{beat_index}] must be a mapping")
                    continue
                try:
                    beat_at = float(beat.get("at"))
                except (TypeError, ValueError):
                    report.error(f"{sid}: beats[{beat_index}].at must be numeric")
                    continue
                if beat_at < start - 0.001 or beat_at > end + 0.001:
                    report.error(f"{sid}: beat {beat_at} lies outside shot [{start}, {end}]")
                if beat.get("level") not in (1, 2, 3):
                    report.error(f"{sid}: beat level must be 1, 2, or 3")

    parsed.sort(key=lambda item: item[1])
    for index, (sid, start, end, raw) in enumerate(parsed):
        if index == 0 and start > 0.05:
            report.error(f"timeline starts at {start:.3f}s instead of 0")
        if index:
            prev_sid, _, prev_end, prev_raw = parsed[index - 1]
            delta = start - prev_end
            if abs(delta) > 0.05:
                kind = "gap" if delta > 0 else "overlap"
                report.error(f"timeline {kind} of {abs(delta):.3f}s between {prev_sid} and {sid}")
            prev_comp = prev_raw.get("composition", {})
            comp = raw.get("composition", {})
            if (
                isinstance(prev_comp, dict)
                and isinstance(comp, dict)
                and prev_comp.get("shot_size") == comp.get("shot_size")
                and prev_raw.get("characters") == raw.get("characters")
            ):
                report.warn(f"{prev_sid} -> {sid}: same characters and shot size; check slideshow repetition")
    if parsed and duration > 0 and abs(parsed[-1][2] - duration) > 0.05:
        report.error(f"timeline ends at {parsed[-1][2]:.3f}s, project.duration is {duration:.3f}s")

    if energies and len(set(energies)) == 1:
        report.error("all shots have the same energy; build an energy arc")
    if len(character_ids) > 1 and relation_shots == 0:
        report.error("multi-character video has no relation/group shot")

    if energies and parsed:
        peak = max(energies)
        peak_indices = [i for i, (_, _, _, shot) in enumerate(parsed) if shot.get("energy") == peak]
        if peak >= 4 and peak_indices:
            peak_start = parsed[peak_indices[0]][1]
            if duration > 0 and peak_start / duration < 0.30:
                report.warn("main energy peak starts in the first 30%; reserve room to escalate after the hook")
            after_peak = [parsed[i][3].get("energy") for i in range(peak_indices[-1] + 1, len(parsed))]
            if after_peak and not any(isinstance(value, int) and value <= peak - 2 for value in after_peak):
                report.warn("no clear energy release after the final peak")

    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("visual_score", type=Path)
    args = parser.parse_args()

    try:
        data = yaml.safe_load(args.visual_score.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"ERROR: file not found: {args.visual_score}", file=sys.stderr)
        return 2
    except yaml.YAMLError as exc:
        print(f"ERROR: invalid YAML: {exc}", file=sys.stderr)
        return 2

    report = validate(data)
    for message in report.warnings:
        print(f"WARN: {message}")
    for message in report.errors:
        print(f"ERROR: {message}")

    if report.errors:
        print(f"FAIL: {len(report.errors)} error(s), {len(report.warnings)} warning(s)")
        return 1
    print(f"PASS: 0 errors, {len(report.warnings)} warning(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
