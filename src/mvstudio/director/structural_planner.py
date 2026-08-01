"""Deterministic structural visual-score planning for low-cost animatics."""

from __future__ import annotations

import os
import tempfile
import math
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


def _lyric_timeline(lyrics_semantic):
    if not isinstance(lyrics_semantic, Mapping):
        raise StructuralPlanError("lyrics semantic map must be a mapping")
    lines = {}
    for line in _sequence(lyrics_semantic.get("lines"), "semantic lines"):
        if not isinstance(line, Mapping):
            raise StructuralPlanError("semantic line must be a mapping")
        lines[_text(line.get("id"), "semantic line id")] = line
    group_by_line = {}
    summaries = {}
    for group in _sequence(lyrics_semantic.get("groups"), "semantic groups"):
        if not isinstance(group, Mapping):
            raise StructuralPlanError("semantic group must be a mapping")
        group_id = _text(group.get("id"), "semantic group id")
        members = [lines.get(item) for item in _sequence(group.get("line_ids"), "semantic line ids")]
        if not members or any(item is None for item in members):
            raise StructuralPlanError("semantic group references an unknown line")
        summaries[group_id] = _text(group.get("summary"), "semantic group summary")
        for item in members:
            if item["id"] in group_by_line:
                raise StructuralPlanError("semantic line belongs to more than one group")
            group_by_line[item["id"]] = group_id
    ordered = sorted(lines.values(), key=lambda item: float(item["start_seconds"]))
    if set(group_by_line) != set(lines):
        raise StructuralPlanError("semantic groups must cover every lyric line")
    return ordered, group_by_line, summaries


def _section_for(timeline, at):
    for item in timeline:
        if item[1] - 0.001 <= at < item[2] + 0.001:
            return item
    return timeline[-1]


def _split_interval(start, end, maximum=3.2):
    duration = end - start
    count = max(1, int(math.ceil(duration / maximum)))
    return [
        (
            round(start + duration * index / count, 6),
            round(start + duration * (index + 1) / count, 6),
        )
        for index in range(count)
    ]


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
    """Build short shots from binding lyric-director beats without approval claims."""
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
    lyric_lines, group_by_line, group_summaries = _lyric_timeline(lyrics_semantic)
    cues = list(_sequence(music_map.get("cues", []), "music cues"))
    peak_index = max(range(len(timeline)), key=lambda item: (timeline[item][3], item))
    segments = []
    cursor = 0.0
    for line in lyric_lines:
        start = float(line.get("start_seconds"))
        end = float(line.get("end_seconds"))
        if start < cursor - 0.05 or end <= start or end > float(duration) + 0.05:
            raise StructuralPlanError("lyric director timeline is invalid")
        if start > cursor + 0.05:
            segments.append({"time": [cursor, start], "line": None})
        segments.append({"time": [start, end], "line": line})
        cursor = end
    if cursor < float(duration) - 0.05:
        segments.append({"time": [cursor, float(duration)], "line": None})
    shots = []
    for segment_index, segment in enumerate(segments):
        segment_start, segment_end = segment["time"]
        line = segment["line"]
        group_id = group_by_line.get(line["id"]) if line else None
        split_times = _split_interval(segment_start, segment_end)
        for split_index, (start, end) in enumerate(split_times):
            section_item = _section_for(timeline, (start + end) / 2)
            section_id, _section_start, _section_end, energy, section = section_item
            if group_id in {item[0] for item in timeline}:
                section_id = group_id
                matched = next(item for item in timeline if item[0] == group_id)
                energy, section = matched[3], matched[4]
            constrained_cast = line.get("character_ids") if line else None
            if constrained_cast is not None:
                cast = list(_sequence(constrained_cast, "binding director cast"))
                if not cast or set(cast) - {item["id"] for item in characters}:
                    raise StructuralPlanError("binding director cast references an unknown character")
            else:
                cast = _cast_for(segment_index, section_id, characters, relationships, peak_index)
            purpose_detail = (
                group_summaries.get(group_id, line["text"])
                if line else section.get("emotion", "instrumental bridge")
            )
            shot_number = len(shots) + 1
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
                shot_cues = [{"at": round(start, 6), "level": 2 if line else 1, "event": "internal_visual_beat"}]
            sources = [item["source_asset"] for item in characters if item["id"] in cast]
            relation = len(cast) >= 2
            last = end >= float(duration) - 0.05
            size_cycle = (
                ("close", "medium", "full") if energy >= 4
                else (("medium", "close", "wide") if energy == 3 else ("wide", "full", "medium"))
            )
            shot_size = size_cycle[split_index % len(size_cycle)]
            lyric_text = line["text"] if line else ""
            shot = {
                "id": f"S{shot_number:03d}",
                "time": [start, end],
                "section": section_id,
                "energy": energy,
                "purpose": f"导演节拍 {shot_number}：{_text(str(purpose_detail), 'shot purpose')}",
                "leverage": "completion_3s" if shot_number == 1 else "completion_rate",
                "characters": cast,
                "lyric": {
                    "text": lyric_text,
                    "onset": float(line["start_seconds"]) if line else start,
                    "source_row": line.get("source_row") if line else None,
                    "character_label": line.get("character_label", "") if line else "",
                },
                "director_beat": {
                    "line_id": line.get("id") if line else "instrumental",
                    "source_sheet": line.get("source_sheet", "") if line else "",
                    "source_row": line.get("source_row") if line else None,
                    "split_index": split_index + 1,
                    "split_count": len(split_times),
                    "cast_is_binding": bool(line and line.get("character_ids") is not None),
                },
                "composition": {
                    "shot_size": shot_size,
                    "arrangement": "关系构图" if relation else "单人物构图",
                },
                "primary_action": f"第 {split_index + 1} 个视觉节拍完成一次可观察的主体或构图变化",
                "visual_events": [
                    {"at": start, "event": "建立新的主体尺度或空间关系"},
                    {"at": round((start + end) / 2, 6), "event": "推进歌词意象或人物反应"},
                ],
                "beats": shot_cues,
                "first_frame": f"承接上一镜并建立第 {shot_number} 镜主体",
                "last_frame": "形成完整收束画面" if last else "留下明确的动作、视线或构图接力点",
                "transition_out": {
                    "type": "none" if last else ("action_match" if shot_number % 3 == 0 else "hard_cut"),
                    "shared_element": "最终定格构图" if last else "主体位置、视线或运动方向",
                },
                "technique": "2.5d",
                "assets": {"use": sources, "missing": []},
            }
            shots.append(shot)
    score = {
        "version": 1,
        "status": "draft_self_generated",
        "purpose": "director_beat_storyboard_draft",
        "approval_required": True,
        "project": {
            "duration": round(float(duration), 6),
            "canvas": brief.get("canvas", "9:16"),
            "premise": brief.get("premise", "Structural timing and relationship test"),
            "quality_review": {
                "baseline": "逐行照排歌词与人物",
                "level_1": "每个歌词导演段拆成多个短镜头",
                "level_2": "每镜承担不同的歌词意象、人物关系或节拍任务",
                "level_3": "以首尾状态和动作方向形成整支 MV 的连续视觉叙事",
                "selected": "level_3",
                "why": "避免长镜头单动作凑时长，并保护 Excel 人物出场合同",
            },
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
