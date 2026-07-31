"""Model-assisted creative decisions merged into a Python-owned visual score."""

from __future__ import annotations

import copy
import json
import os
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path

import yaml

from .contracts import LEVERAGES, TECHNIQUES, TRANSITIONS
from .drafting import ModelBudget, run_bounded_task


class CreativePlanError(ValueError):
    pass


_SHOT_SIZES = frozenset({"extreme_close", "close", "medium", "full", "wide"})
_FIELDS = frozenset({
    "id", "purpose", "leverage", "composition", "primary_action",
    "first_frame", "last_frame", "transition_out", "technique", "missing_assets",
})


def _sequence(value, label):
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise CreativePlanError(label + " must be a sequence")
    return value


def _text(value, label, maximum=600):
    if not isinstance(value, str) or not value.strip():
        raise CreativePlanError(label + " must be non-empty text")
    value = value.strip()
    if len(value.encode("utf-8")) > maximum:
        raise CreativePlanError(label + " exceeds its text budget")
    return value


def _atomic_write(path, content):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".creative-score-", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _payload(structural_score, character_map, lyrics_semantic, brief):
    line_text = {
        line["id"]: line["text"]
        for line in _sequence(lyrics_semantic.get("lines", []), "semantic lines")
        if isinstance(line, Mapping) and isinstance(line.get("id"), str)
    }
    group_summary = {}
    for group in _sequence(lyrics_semantic.get("groups", []), "semantic groups"):
        if not isinstance(group, Mapping):
            raise CreativePlanError("semantic group must be a mapping")
        group_summary[group.get("id")] = {
            "summary": group.get("summary", ""),
            "emotion": group.get("emotion", ""),
            "lyrics": [
                line_text[item]
                for item in group.get("line_ids", [])
                if item in line_text
            ],
        }
    characters = []
    for item in _sequence(character_map.get("characters", []), "characters"):
        if not isinstance(item, Mapping):
            raise CreativePlanError("character must be a mapping")
        characters.append({
            "id": item.get("id"),
            "name": item.get("name"),
            "director_function": item.get("director_function"),
            "traits": list(item.get("traits", [])),
            "symbols": list(item.get("symbols", [])),
        })
    shots = []
    for shot in _sequence(structural_score.get("shots", []), "structural shots"):
        if not isinstance(shot, Mapping):
            raise CreativePlanError("structural shot must be a mapping")
        shots.append({
            "id": shot.get("id"),
            "section": shot.get("section"),
            "energy": shot.get("energy"),
            "characters": list(shot.get("characters", [])),
            "lyric": shot.get("lyric", {}).get("text", ""),
            "section_semantics": group_summary.get(shot.get("section"), {}),
            "structural_purpose": shot.get("purpose"),
        })
    return {
        "project": {
            "canvas": brief.get("canvas", "9:16"),
            "premise": brief.get("premise", ""),
            "audience": brief.get("audience", ""),
        },
        "characters": characters,
        "shots": shots,
        "constraints": {
            "preserve_shot_ids_and_order": True,
            "one_primary_action_per_shot": True,
            "last_transition_must_be_none": True,
            "source_assets_are_python_owned": True,
        },
    }


def _creative_shots(response, structural_shots):
    if not isinstance(response, Mapping) or set(response) != {"shots"}:
        raise CreativePlanError("creative response has unknown or missing fields")
    raw = _sequence(response["shots"], "creative shots")
    if len(raw) != len(structural_shots):
        raise CreativePlanError("creative response must cover every structural shot")
    result = []
    for index, (item, structural) in enumerate(zip(raw, structural_shots)):
        if not isinstance(item, Mapping) or set(item) != _FIELDS:
            raise CreativePlanError("creative shot contract is invalid")
        if item.get("id") != structural.get("id"):
            raise CreativePlanError("creative shot ids must preserve structural order")
        composition = item.get("composition")
        if not isinstance(composition, Mapping) or set(composition) != {"shot_size", "arrangement"}:
            raise CreativePlanError("creative composition contract is invalid")
        shot_size = composition.get("shot_size")
        if shot_size not in _SHOT_SIZES:
            raise CreativePlanError("creative shot size is not allowlisted")
        transition = item.get("transition_out")
        if not isinstance(transition, Mapping) or set(transition) != {"type", "shared_element"}:
            raise CreativePlanError("creative transition contract is invalid")
        transition_type = transition.get("type")
        if transition_type not in TRANSITIONS:
            raise CreativePlanError("creative transition is not allowlisted")
        if index == len(raw) - 1 and transition_type != "none":
            raise CreativePlanError("final creative shot transition must be none")
        technique = item.get("technique")
        if technique not in TECHNIQUES:
            raise CreativePlanError("creative technique is not allowlisted")
        leverage = item.get("leverage")
        if leverage not in LEVERAGES:
            raise CreativePlanError("creative leverage is not allowlisted")
        missing = [
            _text(value, "missing asset", 300)
            for value in _sequence(item.get("missing_assets"), "missing assets")
        ]
        if len(missing) > 12:
            raise CreativePlanError("creative shot has too many missing assets")
        result.append({
            "purpose": _text(item.get("purpose"), "creative purpose"),
            "leverage": leverage,
            "composition": {
                "shot_size": shot_size,
                "arrangement": _text(composition.get("arrangement"), "creative arrangement"),
            },
            "primary_action": _text(item.get("primary_action"), "creative primary action"),
            "first_frame": _text(item.get("first_frame"), "creative first frame"),
            "last_frame": _text(item.get("last_frame"), "creative last frame"),
            "transition_out": {
                "type": transition_type,
                "shared_element": _text(
                    transition.get("shared_element"), "creative shared element"
                ),
            },
            "technique": technique,
            "missing_assets": missing,
        })
    purposes = [item["purpose"] for item in result]
    actions = [item["primary_action"] for item in result]
    if len(set(purposes)) != len(purposes) or len(set(actions)) != len(actions):
        raise CreativePlanError("creative shots require distinct purposes and primary actions")
    return result


def draft_creative_score(
    structural_score,
    music_map,
    character_map,
    lyrics_semantic,
    brief,
    port,
    model,
    staging,
    upstream_audit,
    budget=None,
):
    for label, value in (
        ("structural_score", structural_score),
        ("music_map", music_map),
        ("character_map", character_map),
        ("lyrics_semantic", lyrics_semantic),
        ("brief", brief),
        ("upstream_audit", upstream_audit),
    ):
        if not isinstance(value, Mapping):
            raise CreativePlanError(label + " must be a mapping")
    if structural_score.get("status") != "draft_self_generated":
        raise CreativePlanError("creative drafting requires a draft structural score")
    root = Path(staging)
    if root.is_symlink():
        raise CreativePlanError("creative score staging cannot be a symlink")
    root = root.resolve()
    creative = root / "creative"
    if creative.is_symlink():
        raise CreativePlanError("creative score output directory cannot be a symlink")
    creative.mkdir(parents=True, exist_ok=True)
    try:
        response, call_audit = run_bounded_task(
            port,
            "visual_score.creative_draft_requested",
            _payload(structural_score, character_map, lyrics_semantic, brief),
            model,
            budget or ModelBudget(max_tokens=5000),
            "Draft observable shot-level creative decisions without changing structure or source assets.",
        )
    except Exception as exc:
        if isinstance(exc, CreativePlanError):
            raise
        raise CreativePlanError("creative visual score model task failed") from exc
    structural_shots = list(_sequence(structural_score.get("shots"), "structural shots"))
    decisions = _creative_shots(response, structural_shots)
    score = copy.deepcopy(structural_score)
    score["purpose"] = "creative_visual_score_draft"
    for shot, decision in zip(score["shots"], decisions):
        used_assets = copy.deepcopy(shot["assets"]["use"])
        shot.update({key: value for key, value in decision.items() if key != "missing_assets"})
        shot["assets"] = {"use": used_assets, "missing": decision["missing_assets"]}
    calls = list(_sequence(upstream_audit.get("calls"), "upstream model calls"))
    audit = {
        "version": 1,
        "status": "draft_self_generated",
        "calls": calls + [call_audit],
    }
    _atomic_write(
        creative / "visual_score.yaml",
        yaml.safe_dump(score, allow_unicode=True, sort_keys=False).encode("utf-8"),
    )
    _atomic_write(
        creative / "model_audit.json",
        json.dumps(
            audit, ensure_ascii=True, sort_keys=True, separators=(",", ":")
        ).encode("utf-8"),
    )
    return {"visual_score": score, "model_audit": audit}
