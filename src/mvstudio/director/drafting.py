"""Bounded semantic tasks and deterministic director map drafting."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import yaml

from .audio_analysis import analyze_audio, energy_level
from .intake import IntakeContractError


class MapDraftError(ValueError):
    pass


@dataclass(frozen=True)
class ModelBudget:
    max_input_bytes: int = 65536
    max_output_bytes: int = 65536
    max_tokens: int = 4000

    def __post_init__(self):
        for value in (self.max_input_bytes, self.max_output_bytes, self.max_tokens):
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise MapDraftError("model budget values must be positive integers")


@dataclass(frozen=True)
class ModelTask:
    event_type: str
    model: str
    budget: ModelBudget
    reason: str
    input_contract_hash: str
    output_schema_hash: str
    output_schema: Mapping
    payload: Mapping


@dataclass(frozen=True)
class ModelResult:
    output: Mapping
    input_tokens: int
    output_tokens: int

    def __post_init__(self):
        if not isinstance(self.output, Mapping):
            raise MapDraftError("semantic task output must be a mapping")
        for value in (self.input_tokens, self.output_tokens):
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise MapDraftError("semantic task token usage must be non-negative integers")


class BoundedModelPort(Protocol):
    def run(self, task: ModelTask) -> ModelResult:
        ...


_SCHEMAS = {
    "lyrics.semantic_segment.requested": {
        "groups": [{"id": "text", "line_ids": ["line_id"], "semantic_type": "text",
                    "emotion": "text", "summary": "text"}],
    },
    "relationship_map.draft_requested": {
        "characters": [{"id": "character_id", "director_function": "text",
                        "traits": ["text"], "symbols": ["text"]}],
        "relationships": [{"pair": ["character_id", "character_id"],
                           "dramatic_function": "text", "reveal_group": "group_id"}],
    },
    "visual_score.creative_draft_requested": {
        "shots": [{
            "id": "shot_id",
            "purpose": "text",
            "leverage": "completion_3s|completion_rate|comprehension|save|comment",
            "composition": {"shot_size": "extreme_close|close|medium|full|wide",
                            "arrangement": "text"},
            "primary_action": "text",
            "first_frame": "text",
            "last_frame": "text",
            "transition_out": {
                "type": (
                    "none|hard_cut|occlusion_cut|action_match|crossfade|"
                    "flash_white|ink_wipe|light_wipe|bridge_clip"
                ),
                "shared_element": "text; may be empty only when type is none",
            },
            "technique": "2.5d|static|i2v|hybrid",
            "missing_assets": ["description"],
        }],
    },
}


def _canonical(value):
    try:
        return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise MapDraftError("model contract must be JSON-compatible") from exc


def _hash(value):
    return "sha256:" + hashlib.sha256(_canonical(value)).hexdigest()


def _text(value, label):
    if not isinstance(value, str) or not value.strip():
        raise MapDraftError(label + " must be non-empty text")
    return value.strip()


def _sequence(value, label):
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise MapDraftError(label + " must be a sequence")
    return value


def _atomic_write(path, content):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".maps-", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def run_bounded_task(port, event_type, payload, model, budget, reason):
    if event_type not in _SCHEMAS:
        raise MapDraftError("semantic task is not allowlisted")
    if not isinstance(model, str) or not model.strip():
        raise MapDraftError("model must be configured")
    schema = _SCHEMAS[event_type]
    request_contract = {"output_schema": schema, "payload": payload}
    contract_bytes = _canonical(request_contract)
    if len(contract_bytes) > budget.max_input_bytes:
        raise MapDraftError("semantic task input exceeds budget")
    task = ModelTask(
        event_type=event_type,
        model=model.strip(),
        budget=budget,
        reason=_text(reason, "reason"),
        input_contract_hash="sha256:" + hashlib.sha256(contract_bytes).hexdigest(),
        output_schema_hash=_hash(schema),
        output_schema=schema,
        payload=payload,
    )
    try:
        result = port.run(task)
    except Exception as exc:
        raise MapDraftError("semantic model port failed") from exc
    if not isinstance(result, ModelResult):
        raise MapDraftError("semantic model port must return ModelResult")
    if result.input_tokens + result.output_tokens > budget.max_tokens:
        raise MapDraftError("semantic task token usage exceeds budget")
    response = result.output
    response_bytes = _canonical(response)
    if len(response_bytes) > budget.max_output_bytes:
        raise MapDraftError("semantic task output exceeds budget")
    audit = {
        "event_type": task.event_type,
        "model": task.model,
        "budget": {
            "max_input_bytes": budget.max_input_bytes,
            "max_output_bytes": budget.max_output_bytes,
            "max_tokens": budget.max_tokens,
        },
        "reason": task.reason,
        "input_contract_hash": task.input_contract_hash,
        "output_schema_hash": task.output_schema_hash,
        "response_hash": "sha256:" + hashlib.sha256(response_bytes).hexdigest(),
        "usage": {"input_tokens": result.input_tokens, "output_tokens": result.output_tokens},
    }
    return response, audit


def _timed_lines(value, duration):
    if not isinstance(value, Mapping) or value.get("version") != 1:
        raise MapDraftError("timed lyrics contract is invalid")
    raw = _sequence(value.get("entries"), "timed lyrics entries")
    lines = []
    previous = -1.0
    for index, entry in enumerate(raw, 1):
        if not isinstance(entry, Mapping):
            raise MapDraftError("timed lyric entry must be a mapping")
        start = entry.get("start_seconds")
        if isinstance(start, bool) or not isinstance(start, (int, float)) or start < 0 or start < previous:
            raise MapDraftError("timed lyric starts must be ordered")
        if start >= duration:
            raise MapDraftError("timed lyric exceeds audio duration")
        previous = float(start)
        lines.append({
            "id": f"line_{index:03d}",
            "start_seconds": round(float(start), 6),
            "text": _text(entry.get("text"), "timed lyric text"),
        })
    if not lines:
        raise MapDraftError("timed lyrics cannot be empty")
    for current, following in zip(lines, lines[1:]):
        current["end_seconds"] = following["start_seconds"]
    lines[-1]["end_seconds"] = round(float(duration), 6)
    return lines


def _characters(intake, brief):
    assets = _sequence(intake.get("characters"), "intake characters")
    declared = brief.get("characters", [])
    if declared and (isinstance(declared, (str, bytes)) or not isinstance(declared, Sequence)):
        raise MapDraftError("brief characters must be a sequence")
    if declared and len(declared) != len(assets):
        raise MapDraftError("brief character count must match portrait count")
    result = []
    for index, asset in enumerate(assets, 1):
        source = asset.get("path") if isinstance(asset, Mapping) else None
        if not isinstance(source, str):
            raise MapDraftError("intake character path is invalid")
        item = declared[index - 1] if declared else {}
        if not isinstance(item, Mapping):
            raise MapDraftError("brief character must be a mapping")
        character_id = item.get("id", f"C{index:02d}")
        name = item.get("name", Path(source).stem)
        result.append({
            "id": _text(character_id, "character id"),
            "name": _text(name, "character name"),
            "traits": [
                _text(value, "character trait")
                for value in _sequence(item.get("traits", []), "character traits")
            ],
            "source_asset": source,
        })
    ids = [item["id"] for item in result]
    if len(ids) != len(set(ids)):
        raise MapDraftError("character ids must be unique")
    return result


def _semantic_groups(response, lines):
    if set(response) != {"groups"}:
        raise MapDraftError("semantic response has unknown or missing fields")
    groups = _sequence(response["groups"], "semantic groups")
    line_ids = [line["id"] for line in lines]
    flattened = []
    result = []
    seen = set()
    for item in groups:
        if not isinstance(item, Mapping) or set(item) != {"id", "line_ids", "semantic_type", "emotion", "summary"}:
            raise MapDraftError("semantic group contract is invalid")
        group_id = _text(item["id"], "semantic group id")
        if group_id in seen:
            raise MapDraftError("semantic group ids must be unique")
        seen.add(group_id)
        members = list(_sequence(item["line_ids"], "semantic group line_ids"))
        if not members:
            raise MapDraftError("semantic group cannot be empty")
        flattened.extend(members)
        result.append({
            "id": group_id,
            "line_ids": members,
            "semantic_type": _text(item["semantic_type"], "semantic type"),
            "emotion": _text(item["emotion"], "semantic emotion"),
            "summary": _text(item["summary"], "semantic summary"),
        })
    if flattened != line_ids:
        raise MapDraftError("semantic groups must cover timed lines once in original order")
    return result


def _relationship_map(response, characters, group_ids):
    if set(response) != {"characters", "relationships"}:
        raise MapDraftError("relationship response has unknown or missing fields")
    character_ids = {item["id"] for item in characters}
    profiles = {}
    for item in _sequence(response["characters"], "relationship characters"):
        if not isinstance(item, Mapping) or set(item) != {"id", "director_function", "traits", "symbols"}:
            raise MapDraftError("relationship character contract is invalid")
        character_id = item.get("id")
        if character_id not in character_ids or character_id in profiles:
            raise MapDraftError("relationship response has an unknown or duplicate character")
        profiles[character_id] = {
            "director_function": _text(item["director_function"], "director function"),
            "traits": [_text(value, "trait") for value in _sequence(item["traits"], "traits")],
            "symbols": [_text(value, "symbol") for value in _sequence(item["symbols"], "symbols")],
        }
    if set(profiles) != character_ids:
        raise MapDraftError("relationship response must cover every character")
    relationships = []
    for item in _sequence(response["relationships"], "relationships"):
        if not isinstance(item, Mapping) or set(item) != {"pair", "dramatic_function", "reveal_group"}:
            raise MapDraftError("relationship contract is invalid")
        pair = list(_sequence(item["pair"], "relationship pair"))
        if len(pair) != 2 or len(set(pair)) != 2 or set(pair) - character_ids:
            raise MapDraftError("relationship pair is invalid")
        reveal = item["reveal_group"]
        if reveal not in group_ids:
            raise MapDraftError("relationship reveal group is invalid")
        relationships.append({
            "pair": pair,
            "dramatic_function": _text(item["dramatic_function"], "dramatic function"),
            "reveal_section": reveal,
        })
    if len(characters) > 1 and not relationships:
        raise MapDraftError("multi-character maps require a relationship")
    return profiles, relationships


def draft_maps(intake, lyrics_timed, brief, port, staging, model, budget=None):
    if not isinstance(intake, Mapping) or intake.get("status") != "intake_validated":
        raise MapDraftError("validated intake manifest is required")
    if not isinstance(brief, Mapping):
        raise MapDraftError("brief must be a mapping")
    audio_manifest = intake.get("audio")
    if not isinstance(audio_manifest, Mapping):
        raise MapDraftError("intake audio contract is invalid")
    duration = audio_manifest.get("duration_seconds")
    if isinstance(duration, bool) or not isinstance(duration, (int, float)) or duration <= 0:
        raise MapDraftError("audio duration is invalid")
    lines = _timed_lines(lyrics_timed, float(duration))
    characters = _characters(intake, brief)
    budget = budget or ModelBudget()
    staging_path = Path(staging)
    if staging_path.is_symlink():
        raise MapDraftError("map staging cannot be a symlink")
    root = staging_path.resolve()
    creative = root / "creative"
    if creative.is_symlink():
        raise MapDraftError("map output directory cannot be a symlink")
    creative.mkdir(parents=True, exist_ok=True)
    try:
        analysis = analyze_audio(staging, dict(audio_manifest))
    except IntakeContractError as exc:
        raise MapDraftError(str(exc)) from exc
    semantic_response, semantic_audit = run_bounded_task(
        port,
        "lyrics.semantic_segment.requested",
        {"duration_seconds": duration, "lines": lines},
        model,
        budget,
        "Group timed lyric lines by complete semantic meaning without changing timing.",
    )
    groups = _semantic_groups(semantic_response, lines)
    relationship_response, relationship_audit = run_bounded_task(
        port,
        "relationship_map.draft_requested",
        {
            "characters": [
                {"id": item["id"], "name": item["name"], "traits": item["traits"]}
                for item in characters
            ],
            "semantic_groups": [
                {"id": item["id"], "semantic_type": item["semantic_type"],
                 "emotion": item["emotion"], "summary": item["summary"]}
                for item in groups
            ],
        },
        model,
        budget,
        "Draft director functions and relationships without accessing portrait pixels.",
    )
    profiles, relationships = _relationship_map(
        relationship_response, characters, {item["id"] for item in groups}
    )
    line_by_id = {line["id"]: line for line in lines}
    sections = []
    first_start = lines[0]["start_seconds"]
    if first_start > 0.05:
        sections.append({
            "id": "intro", "time": [0.0, first_start], "music_role": "intro",
            "energy": energy_level(analysis, 0.0, first_start), "emotion": "instrumental opening",
        })
    for index, group in enumerate(groups):
        start = line_by_id[group["line_ids"][0]]["start_seconds"]
        end = (
            line_by_id[groups[index + 1]["line_ids"][0]]["start_seconds"]
            if index + 1 < len(groups) else float(duration)
        )
        if end <= start:
            raise MapDraftError("semantic group boundaries must advance in time")
        sections.append({
            "id": group["id"], "time": [start, round(end, 6)],
            "music_role": group["semantic_type"], "energy": energy_level(analysis, start, end),
            "emotion": group["emotion"],
        })
    cues = {}
    for at in analysis["onsets"]:
        cues[at] = {"at": at, "level": 3, "source": "audio_onset"}
    for line in lines:
        cues[line["start_seconds"]] = {
            "at": line["start_seconds"], "level": 2,
            "source": "lyric_start",
        }
    for section in sections:
        cues[section["time"][0]] = {
            "at": section["time"][0], "level": 1, "source": "semantic_section_start",
        }
    music_map = {
        "version": 1, "status": "draft_self_generated", "duration": round(float(duration), 6),
        "bpm": analysis["bpm_candidate"], "sections": sections,
        "cues": [cues[key] for key in sorted(cues)],
    }
    character_map = {
        "version": 1,
        "status": "draft_self_generated",
        "characters": [
            {
                **item,
                **profiles[item["id"]],
                "appearance_budget": {"intro": 1, "solo": 1, "relation": 1 if len(characters) > 1 else 0, "group": 1},
            }
            for item in characters
        ],
        "relationships": relationships,
    }
    semantic_map = {
        "version": 1, "status": "draft_self_generated", "lines": lines, "groups": groups,
    }
    audit = {
        "version": 1, "status": "draft_self_generated",
        "calls": [semantic_audit, relationship_audit],
    }
    outputs = {
        "creative/beats.json": _canonical(analysis),
        "creative/lyrics_semantic.json": _canonical(semantic_map),
        "creative/music_map.yaml": yaml.safe_dump(music_map, allow_unicode=True, sort_keys=False).encode("utf-8"),
        "creative/character_map.yaml": yaml.safe_dump(character_map, allow_unicode=True, sort_keys=False).encode("utf-8"),
        "creative/model_audit.json": _canonical(audit),
    }
    for relative, content in outputs.items():
        _atomic_write(root / relative, content)
    return {
        "beats": analysis,
        "lyrics_semantic": semantic_map,
        "music_map": music_map,
        "character_map": character_map,
        "model_audit": audit,
    }
