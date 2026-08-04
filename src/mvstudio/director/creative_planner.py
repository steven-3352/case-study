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
    "id", "purpose", "arrangement", "primary_action", "first_frame", "last_frame",
})
_REVIEW_FIELDS = frozenset({
    "baseline_concept", "level_1", "level_2", "level_3", "selected_plan",
    "why_this_is_best", "rejected_alternatives",
})
_CREATIVE_BATCH_SIZE = 1
_CREATIVE_FIELD_MAX_BYTES = 480


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
    structural_shots = _sequence(structural_score.get("shots", []), "structural shots")
    shots = []
    for shot in structural_shots:
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
            "one_sentence_per_text_field": True,
            "max_characters_per_text_field": 120,
            "last_transition_must_be_none": bool(
                structural_shots
                and structural_shots[-1].get("transition_out", {}).get("type") == "none"
            ),
            "source_assets_are_python_owned": True,
        },
    }


def _creative_shots(response, structural_shots, require_final_transition=False):
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
        composition = structural.get("composition")
        if not isinstance(composition, Mapping):
            raise CreativePlanError("structural composition contract is invalid")
        shot_size = composition.get("shot_size")
        if shot_size not in _SHOT_SIZES:
            raise CreativePlanError("structural shot size is not allowlisted")
        transition = structural.get("transition_out")
        if not isinstance(transition, Mapping):
            raise CreativePlanError("structural transition contract is invalid")
        transition_type = transition.get("type")
        if transition_type not in TRANSITIONS:
            raise CreativePlanError("creative transition is not allowlisted")
        if require_final_transition and index == len(raw) - 1 and transition_type != "none":
            raise CreativePlanError("final creative shot transition must be none")
        shared_element = transition.get("shared_element")
        if not isinstance(shared_element, str):
            raise CreativePlanError("creative shared element must be text")
        shared_element = shared_element.strip()
        if transition_type == "none":
            shared_element = shared_element or "final held composition"
        elif not shared_element:
            raise CreativePlanError("creative shared element must be non-empty text")
        technique = structural.get("technique")
        if technique not in TECHNIQUES:
            raise CreativePlanError("creative technique is not allowlisted")
        leverage = structural.get("leverage")
        if leverage not in LEVERAGES:
            raise CreativePlanError("creative leverage is not allowlisted")
        result.append({
            "purpose": _text(
                item.get("purpose"), "creative purpose", _CREATIVE_FIELD_MAX_BYTES
            ),
            "leverage": leverage,
            "composition": {
                "shot_size": shot_size,
                "arrangement": _text(
                    item.get("arrangement"), "creative arrangement",
                    _CREATIVE_FIELD_MAX_BYTES,
                ),
            },
            "primary_action": _text(
                item.get("primary_action"), "creative primary action",
                _CREATIVE_FIELD_MAX_BYTES,
            ),
            "first_frame": _text(
                item.get("first_frame"), "creative first frame", _CREATIVE_FIELD_MAX_BYTES
            ),
            "last_frame": _text(
                item.get("last_frame"), "creative last frame", _CREATIVE_FIELD_MAX_BYTES
            ),
            "transition_out": {
                "type": transition_type,
                "shared_element": shared_element,
            },
            "technique": technique,
            "missing_assets": list(structural.get("assets", {}).get("missing", [])),
        })
    purposes = [item["purpose"] for item in result]
    actions = [item["primary_action"] for item in result]
    if len(set(purposes)) != len(purposes) or len(set(actions)) != len(actions):
        raise CreativePlanError("creative shots require distinct purposes and primary actions")
    return result


def _quality_review(response):
    if not isinstance(response, Mapping) or set(response) != _REVIEW_FIELDS:
        raise CreativePlanError("creative quality review contract is invalid")
    result = {
        key: _text(response.get(key), "creative review " + key, 1200)
        for key in _REVIEW_FIELDS - {"rejected_alternatives"}
    }
    rejected = [
        _text(item, "rejected creative alternative", 800)
        for item in _sequence(response.get("rejected_alternatives"), "rejected alternatives")
    ]
    if len(rejected) < 2:
        raise CreativePlanError("creative quality review requires two rejected alternatives")
    result["rejected_alternatives"] = rejected
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
    prompt_overrides=None,
    progress=None,
):
    emit = progress if callable(progress) else (lambda *args, **kwargs: None)
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
    structural_shots = list(_sequence(structural_score.get("shots"), "structural shots"))
    task_budget = budget or ModelBudget(max_tokens=3000)
    decisions = []
    creative_audits = []
    translation_cache = {}
    total_shots = len(structural_shots)
    try:
        for offset in range(0, len(structural_shots), _CREATIVE_BATCH_SIZE):
            batch = structural_shots[offset:offset + _CREATIVE_BATCH_SIZE]
            batch_score = copy.deepcopy(structural_score)
            batch_score["shots"] = batch
            # Draft runs one LLM call per shot, so emit incremental progress
            # across the 40→68 band (semantic=10, relationship=30 precede us;
            # visual_review=70 follows). Otherwise the bar sits frozen at a
            # single value for the whole minutes-long draft loop.
            done = offset
            pct = 40 + int(28 * done / total_shots) if total_shots else 40
            emit(
                "visual_draft", pct,
                f"正在生成视觉分镜草稿…({done}/{total_shots})",
            )
            response, call_audit = run_bounded_task(
                port,
                "visual_score.creative_draft_requested",
                _payload(batch_score, character_map, lyrics_semantic, brief),
                model,
                task_budget,
                "Draft observable shot decisions for this batch without changing time, cast, order or assets. Return exactly one concise sentence of at most 120 characters per text field.",
                prompt_overrides,
                translation_cache,
            )
            decisions.extend(_creative_shots(
                response,
                batch,
                require_final_transition=offset + len(batch) == len(structural_shots),
            ))
            creative_audits.append(call_audit)
        emit("visual_review", 70, "正在质检视觉分镜…")
        review_response, review_audit = run_bounded_task(
            port,
            "visual_score.quality_review_requested",
            {
                "project": _payload(structural_score, character_map, lyrics_semantic, brief)["project"],
                "shots": [
                    {
                        "id": shot["id"], "time": shot["time"],
                        "characters": shot["characters"], "lyric": shot["lyric"].get("text", ""),
                        "purpose": decision["purpose"], "primary_action": decision["primary_action"],
                    }
                    for shot, decision in zip(structural_shots, decisions)
                ],
            },
            model,
            ModelBudget(max_tokens=4000),
            "Audit the complete MV plan, raise it three material levels, and select the strongest executable plan. Keep every text field within 400 characters.",
            prompt_overrides,
            translation_cache,
        )
        review = _quality_review(review_response)
    except Exception as exc:
        if isinstance(exc, CreativePlanError):
            raise
        raise CreativePlanError("creative visual score model task failed") from exc
    score = copy.deepcopy(structural_score)
    score["purpose"] = "creative_visual_score_draft"
    score["creative_review"] = review
    for shot, decision in zip(score["shots"], decisions):
        used_assets = copy.deepcopy(shot["assets"]["use"])
        shot.update({key: value for key, value in decision.items() if key != "missing_assets"})
        shot["assets"] = {"use": used_assets, "missing": decision["missing_assets"]}
    calls = list(_sequence(upstream_audit.get("calls"), "upstream model calls"))
    audit = {
        "version": 1,
        "status": "draft_self_generated",
        "calls": calls + creative_audits + [review_audit],
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
