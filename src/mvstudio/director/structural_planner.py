"""Deterministic structural visual-score planning for low-cost animatics."""

from __future__ import annotations

import os
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path

import yaml


class StructuralPlanError(ValueError):
    pass


def _sequence(value, label):
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise StructuralPlanError(label + " must be a sequence")
    return value


def _text(value, label):
    if not isinstance(value, str) or not value.strip():
        raise StructuralPlanError(label + " must be non-empty text")
    return value.strip()


def _atomic_yaml(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".score-", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(yaml.safe_dump(value, allow_unicode=True, sort_keys=False).encode("utf-8"))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _timeline(sections, duration):
    result = []
    for index, section in enumerate(sections):
        if not isinstance(section, Mapping):
            raise StructuralPlanError("music section must be a mapping")
        section_id = _text(section.get("id"), "music section id")
        times = _sequence(section.get("time"), section_id + ".time")
        if len(times) != 2:
            raise StructuralPlanError(section_id + ".time must contain start and end")
        if any(isinstance(value, bool) or not isinstance(value, (int, float)) for value in times):
            raise StructuralPlanError(section_id + ".time must be numeric")
        start, end = float(times[0]), float(times[1])
        if start < 0 or end <= start:
            raise StructuralPlanError(section_id + ".time is invalid")
        if index == 0 and start > 0.05:
            raise StructuralPlanError("music sections must start at zero")
        if result and abs(result[-1][2] - start) > 0.05:
            raise StructuralPlanError("music sections must be contiguous")
        energy = section.get("energy")
        if isinstance(energy, bool) or not isinstance(energy, int) or energy not in range(1, 6):
            raise StructuralPlanError("music section energy must be 1 through 5")
        result.append((section_id, start, end, energy, section))
    if not result or abs(result[-1][2] - duration) > 0.05:
        raise StructuralPlanError("music sections must cover the audio duration")
    if len({item[3] for item in result}) == 1:
        raise StructuralPlanError("structural visual score requires a non-flat energy arc")
    return result


def _lyrics_by_section(lyrics_semantic):
    if not isinstance(lyrics_semantic, Mapping):
        raise StructuralPlanError("lyrics semantic map must be a mapping")
    lines = {}
    for line in _sequence(lyrics_semantic.get("lines"), "semantic lines"):
        if not isinstance(line, Mapping):
            raise StructuralPlanError("semantic line must be a mapping")
        lines[_text(line.get("id"), "semantic line id")] = line
    result = {}
    for group in _sequence(lyrics_semantic.get("groups"), "semantic groups"):
        if not isinstance(group, Mapping):
            raise StructuralPlanError("semantic group must be a mapping")
        group_id = _text(group.get("id"), "semantic group id")
        members = [lines.get(item) for item in _sequence(group.get("line_ids"), "semantic line ids")]
        if not members or any(item is None for item in members):
            raise StructuralPlanError("semantic group references an unknown line")
        result[group_id] = {
            "text": " / ".join(_text(item.get("text"), "semantic line text") for item in members),
            "onset": float(members[0]["start_seconds"]),
            "summary": _text(group.get("summary"), "semantic group summary"),
        }
    return result


def _cast_for(index, section_id, characters, relationships, peak_index):
    ids = [item["id"] for item in characters]
    if len(ids) == 1:
        return ids
    if index == peak_index:
        return ids
    for relationship in relationships:
        if relationship.get("reveal_section") == section_id:
            return list(relationship["pair"])
    return [ids[index % len(ids)]]


def plan_structural_score(music_map, character_map, lyrics_semantic, brief, staging=None):
    """Build one structural shot per music section without making approval claims."""
    for label, value in (("music_map", music_map), ("character_map", character_map), ("brief", brief)):
        if not isinstance(value, Mapping):
            raise StructuralPlanError(label + " must be a mapping")
    if music_map.get("status") != "draft_self_generated" or character_map.get("status") != "draft_self_generated":
        raise StructuralPlanError("structural planning requires draft_self_generated maps")
    duration = music_map.get("duration")
    if isinstance(duration, bool) or not isinstance(duration, (int, float)) or duration <= 0:
        raise StructuralPlanError("music duration must be positive")
    timeline = _timeline(_sequence(music_map.get("sections"), "music sections"), float(duration))
    characters = list(_sequence(character_map.get("characters"), "characters"))
    if not characters or any(not isinstance(item, Mapping) for item in characters):
        raise StructuralPlanError("character map must contain characters")
    for item in characters:
        _text(item.get("id"), "character id")
        _text(item.get("source_asset"), "character source asset")
    relationships = list(_sequence(character_map.get("relationships", []), "relationships"))
    if len(characters) > 1 and not relationships:
        raise StructuralPlanError("multi-character structural plans require a relationship")
    lyrics = _lyrics_by_section(lyrics_semantic)
    cues = list(_sequence(music_map.get("cues", []), "music cues"))
    peak_index = max(range(len(timeline)), key=lambda item: (timeline[item][3], item))
    shots = []
    for index, (section_id, start, end, energy, section) in enumerate(timeline):
        cast = _cast_for(index, section_id, characters, relationships, peak_index)
        semantic = lyrics.get(section_id)
        purpose_detail = semantic["summary"] if semantic else section.get("emotion", "instrumental structure")
        shot_cues = []
        for cue in cues:
            if not isinstance(cue, Mapping):
                raise StructuralPlanError("music cue must be a mapping")
            at = cue.get("at")
            if isinstance(at, bool) or not isinstance(at, (int, float)):
                raise StructuralPlanError("music cue time must be numeric")
            if start - 0.001 <= float(at) <= end + 0.001:
                level = cue.get("level")
                if level not in (1, 2, 3):
                    raise StructuralPlanError("music cue level must be 1 through 3")
                shot_cues.append({"at": round(float(at), 6), "level": level, "event": cue.get("source", "music_cue")})
        if not shot_cues:
            shot_cues = [{"at": round(start, 6), "level": 1, "event": "section_start"}]
        sources = [item["source_asset"] for item in characters if item["id"] in cast]
        relation = len(cast) >= 2
        last = index == len(timeline) - 1
        shots.append({
            "id": f"S{index + 1:03d}",
            "time": [round(start, 6), round(end, 6)],
            "section": section_id,
            "energy": energy,
            "purpose": f"Structure test {index + 1}: {_text(str(purpose_detail), 'section purpose')}",
            "leverage": "completion_3s" if index == 0 else "completion_rate",
            "characters": cast,
            "lyric": {"text": semantic["text"] if semantic else "", "onset": semantic["onset"] if semantic else start},
            "composition": {
                "shot_size": "close" if energy >= 4 else ("full" if energy <= 2 else "medium"),
                "arrangement": "relationship composition" if relation else "single-character composition",
            },
            "primary_action": "The characters become readable in one shared composition" if relation else "The character changes scale visibly across the section",
            "beats": shot_cues,
            "first_frame": f"Section {section_id} begins with energy {energy}",
            "last_frame": "The final structural cover holds" if last else f"The section resolves toward {timeline[index + 1][0]}",
            "transition_out": {
                "type": "none" if last else "hard_cut",
                "shared_element": "final structural cover" if last else "subject position and motion direction",
            },
            "technique": "2.5d",
            "assets": {"use": sources, "missing": []},
        })
    score = {
        "version": 1,
        "status": "draft_self_generated",
        "purpose": "structural_animatic_test_only",
        "approval_required": True,
        "project": {
            "duration": round(float(duration), 6),
            "canvas": brief.get("canvas", "9:16"),
            "premise": brief.get("premise", "Structural timing and relationship test"),
        },
        "shots": shots,
    }
    if staging is not None:
        root = Path(staging).resolve()
        creative = root / "creative"
        if creative.is_symlink():
            raise StructuralPlanError("visual score output directory cannot be a symlink")
        _atomic_yaml(creative / "visual_score.yaml", score)
    return score
