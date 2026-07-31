"""Fail-closed validation for director compiler inputs."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence


class DirectorContractError(ValueError):
    pass


TECHNIQUES = frozenset({"2.5d", "static", "i2v", "hybrid"})
LEVERAGES = frozenset({"completion_3s", "completion_rate", "comprehension", "save", "comment"})
TRANSITIONS = frozenset({
    "none", "hard_cut", "occlusion_cut", "action_match", "crossfade",
    "flash_white", "ink_wipe", "light_wipe", "bridge_clip",
})
SHOT_FIELDS = frozenset({
    "id", "time", "section", "energy", "purpose", "leverage", "characters",
    "composition", "primary_action", "beats", "first_frame", "last_frame",
    "transition_out", "technique", "assets",
})


def _mapping(value, label):
    if not isinstance(value, Mapping):
        raise DirectorContractError(label + " must be a mapping")
    return value


def _sequence(value, label):
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise DirectorContractError(label + " must be a sequence")
    return value


def _text(value, label):
    if not isinstance(value, str) or not value.strip():
        raise DirectorContractError(label + " must be non-empty text")
    return value.strip()


def _number(value, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise DirectorContractError(label + " must be a finite number")
    return float(value)


def _time_pair(value, label):
    values = _sequence(value, label)
    if len(values) != 2:
        raise DirectorContractError(label + " must contain start and end")
    start, end = _number(values[0], label), _number(values[1], label)
    if start < 0 or end <= start:
        raise DirectorContractError(label + " must satisfy 0 <= start < end")
    return start, end


def _project_path(value, label):
    value = _text(value, label)
    if value.startswith("/") or "\\" in value:
        raise DirectorContractError(label + " must be a project-relative POSIX path")
    parts = value.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise DirectorContractError(label + " must be a project-relative POSIX path")
    return value


def validate_package(value):
    root = _mapping(value, "director package")
    allowed = {"project_id", "brief", "music_map", "character_map", "visual_score", "animatic"}
    if set(root) - allowed:
        raise DirectorContractError("unknown director package field")
    _text(root.get("project_id"), "project_id")
    brief = _mapping(root.get("brief"), "brief")
    music = _mapping(root.get("music_map"), "music_map")
    characters = _mapping(root.get("character_map"), "character_map")
    score = _mapping(root.get("visual_score"), "visual_score")

    canvas = brief.get("canvas", score.get("project", {}).get("canvas", "9:16"))
    if canvas not in {"9:16", "16:9"}:
        raise DirectorContractError("canvas must be 9:16 or 16:9")
    duration = _number(music.get("duration"), "music_map.duration")
    if duration <= 0:
        raise DirectorContractError("music_map.duration must be positive")

    sections = _sequence(music.get("sections"), "music_map.sections")
    section_ids = set()
    for index, section in enumerate(sections):
        section = _mapping(section, f"music_map.sections[{index}]")
        section_id = _text(section.get("id"), f"music_map.sections[{index}].id")
        if section_id in section_ids:
            raise DirectorContractError("duplicate music section id")
        section_ids.add(section_id)
        _time_pair(section.get("time"), f"music_map.sections[{index}].time")
        energy = section.get("energy")
        if isinstance(energy, bool) or not isinstance(energy, int) or energy not in range(1, 6):
            raise DirectorContractError("music section energy must be 1 through 5")

    character_items = _sequence(characters.get("characters"), "character_map.characters")
    character_ids = set()
    for index, character in enumerate(character_items):
        character = _mapping(character, f"character_map.characters[{index}]")
        character_id = _text(character.get("id"), f"character_map.characters[{index}].id")
        _text(character.get("director_function"), f"character_map.characters[{index}].director_function")
        if character.get("source_asset") is not None:
            _project_path(character.get("source_asset"), f"character_map.characters[{index}].source_asset")
        if character_id in character_ids:
            raise DirectorContractError("duplicate character id")
        character_ids.add(character_id)
    if not character_ids:
        raise DirectorContractError("character_map.characters cannot be empty")

    shots = _sequence(score.get("shots"), "visual_score.shots")
    if not shots:
        raise DirectorContractError("visual_score.shots cannot be empty")
    seen = set()
    timeline = []
    energies = set()
    relation_count = 0
    for index, shot in enumerate(shots):
        shot = _mapping(shot, f"visual_score.shots[{index}]")
        missing = SHOT_FIELDS - set(shot)
        if missing:
            raise DirectorContractError("shot is missing fields: " + ", ".join(sorted(missing)))
        shot_id = _text(shot.get("id"), f"visual_score.shots[{index}].id")
        if shot_id in seen:
            raise DirectorContractError("duplicate shot id")
        seen.add(shot_id)
        start, end = _time_pair(shot.get("time"), f"{shot_id}.time")
        timeline.append((start, end, shot_id))
        if shot.get("section") not in section_ids:
            raise DirectorContractError(f"{shot_id} references an unknown section")
        energy = shot.get("energy")
        if isinstance(energy, bool) or not isinstance(energy, int) or energy not in range(1, 6):
            raise DirectorContractError(f"{shot_id}.energy must be 1 through 5")
        energies.add(energy)
        for field in ("purpose", "primary_action", "first_frame", "last_frame"):
            _text(shot.get(field), f"{shot_id}.{field}")
        if shot.get("leverage") not in LEVERAGES:
            raise DirectorContractError(f"{shot_id} has unsupported leverage")
        if shot.get("technique") not in TECHNIQUES:
            raise DirectorContractError(f"{shot_id} has unsupported technique")
        cast = _sequence(shot.get("characters"), f"{shot_id}.characters")
        if set(cast) - character_ids:
            raise DirectorContractError(f"{shot_id} references an unknown character")
        relation_count += int(len(cast) >= 2)
        composition = _mapping(shot.get("composition"), f"{shot_id}.composition")
        _text(composition.get("shot_size"), f"{shot_id}.composition.shot_size")
        transition = _mapping(shot.get("transition_out"), f"{shot_id}.transition_out")
        if transition.get("type") not in TRANSITIONS:
            raise DirectorContractError(f"{shot_id} has unsupported transition")
        if transition.get("type") != "none":
            _text(transition.get("shared_element"), f"{shot_id}.transition_out.shared_element")
        beats = _sequence(shot.get("beats"), f"{shot_id}.beats")
        if not beats:
            raise DirectorContractError(f"{shot_id}.beats cannot be empty")
        for beat in beats:
            beat = _mapping(beat, f"{shot_id}.beat")
            at = _number(beat.get("at"), f"{shot_id}.beat.at")
            if at < start - 0.001 or at > end + 0.001 or beat.get("level") not in (1, 2, 3):
                raise DirectorContractError(f"{shot_id} has an invalid beat")
        assets = _mapping(shot.get("assets"), f"{shot_id}.assets")
        for asset_index, path in enumerate(_sequence(assets.get("use", []), f"{shot_id}.assets.use")):
            _project_path(path, f"{shot_id}.assets.use[{asset_index}]")
        for missing in _sequence(assets.get("missing", []), f"{shot_id}.assets.missing"):
            _text(missing, f"{shot_id}.assets.missing item")

    timeline.sort()
    if timeline[0][0] > 0.05 or abs(timeline[-1][1] - duration) > 0.05:
        raise DirectorContractError("visual score does not cover the music duration")
    for previous, current in zip(timeline, timeline[1:]):
        if abs(previous[1] - current[0]) > 0.05:
            raise DirectorContractError("visual score timeline has a gap or overlap")
    if len(energies) == 1:
        raise DirectorContractError("visual score must contain an energy arc")
    if len(character_ids) > 1 and relation_count == 0:
        raise DirectorContractError("multi-character score requires a relation shot")

    animatic = root.get("animatic", {})
    if animatic is None:
        animatic = {}
    animatic = _mapping(animatic, "animatic")
    if set(animatic) - {"enabled", "fps"}:
        raise DirectorContractError("unknown animatic field")
    fps = animatic.get("fps", 6)
    if isinstance(fps, bool) or not isinstance(fps, int) or fps not in range(1, 31):
        raise DirectorContractError("animatic.fps must be 1 through 30")
    return root
