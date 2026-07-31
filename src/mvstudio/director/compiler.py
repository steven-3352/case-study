"""Compile validated director contracts into deterministic project artifacts."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import yaml

from .animatic import render_animatic
from .contracts import validate_package


def _canonical_bytes(value):
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _digest_bytes(value):
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _digest(value):
    return _digest_bytes(_canonical_bytes(value))


def _atomic_write(path, content):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".director-", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _yaml(value):
    return yaml.safe_dump(value, allow_unicode=True, sort_keys=False).encode("utf-8")


def _story_framework(package):
    music = package["music_map"]
    score = package["visual_score"]
    sections = []
    shots = score["shots"]
    peak = max(int(shot["energy"]) for shot in shots)
    for section in music["sections"]:
        section_shots = [shot["id"] for shot in shots if shot["section"] == section["id"]]
        sections.append({
            "id": section["id"], "time": list(section["time"]),
            "music_role": section.get("music_role", "unknown"),
            "energy": section["energy"], "emotion": section.get("emotion", "unspecified"),
            "shot_ids": section_shots,
        })
    return {
        "version": 1,
        "status": "draft_self_generated",
        "premise": score.get("project", {}).get("premise", package["brief"].get("premise", "")),
        "sections": sections,
        "peak_shots": [shot["id"] for shot in shots if int(shot["energy"]) == peak],
        "release_shots": [shot["id"] for shot in shots if int(shot["energy"]) <= peak - 2],
        "approval_required": True,
    }


def _asset_plan(package):
    entries = {}
    for character in package["character_map"]["characters"]:
        source = character.get("source_asset")
        if source:
            entries[source] = {
                "id": "source-" + character["id"], "path": source,
                "source_type": "real_private", "asset_role": "source_portrait",
                "character": character["id"], "status": "available", "used_by": [],
            }
    missing = {}
    for shot in package["visual_score"]["shots"]:
        assets = shot.get("assets", {})
        for path in assets.get("use", []):
            entry = entries.setdefault(path, {
                "id": "asset-" + hashlib.sha256(str(path).encode()).hexdigest()[:12],
                "path": path, "source_type": "unknown", "asset_role": "declared_input",
                "status": "available", "used_by": [],
            })
            entry["used_by"].append(shot["id"])
        for description in assets.get("missing", []):
            item = missing.setdefault(str(description), {
                "id": "missing-" + hashlib.sha256(str(description).encode()).hexdigest()[:12],
                "description": str(description), "source_type": "synthetic_visual",
                "asset_role": "generated_supplement", "status": "planned", "required_by": [],
            })
            item["required_by"].append(shot["id"])
    return {"version": 1, "status": "draft_self_generated", "assets": list(entries.values()) + list(missing.values())}


def _generation_plan(package):
    editorial, clips = [], []
    for shot in package["visual_score"]["shots"]:
        start_ms = round(float(shot["time"][0]) * 1000)
        end_ms = round(float(shot["time"][1]) * 1000)
        editorial.append({
            "shot_id": shot["id"], "timeline_in_ms": start_ms, "timeline_out_ms": end_ms,
            "duration_ms": end_ms - start_ms, "technique": shot["technique"],
            "lyric_span": [shot.get("lyric", {}).get("text", "")],
            "transition_out": shot["transition_out"],
        })
        if shot["technique"] in {"i2v", "hybrid"}:
            source_duration = end_ms - start_ms
            clip_duration = max(4000, source_duration)
            spare = clip_duration - source_duration
            head = spare // 2
            clips.append({
                "clip_id": "clip-" + shot["id"], "duration_ms": clip_duration,
                "source_shot_ids": [shot["id"]], "usable_range_ms": [head, head + source_duration],
                "head_handle_ms": head, "tail_handle_ms": spare - head,
                "first_frame_contract": shot["first_frame"],
                "last_frame_contract": {
                    "exit_state": shot["last_frame"],
                    "shared_element": shot["transition_out"].get("shared_element"),
                },
                "fallback": "approved still plus deterministic 2.5d",
            })
    return {"version": 1, "status": "draft_self_generated", "editorial_shots": editorial, "generation_clips": clips}


def _shots(package):
    move_families = ("push_slow", "track_r", "pull", "pan_u", "orbit", "track_l")
    compiled = []
    for index, shot in enumerate(package["visual_score"]["shots"]):
        compiled.append({
            "sid": shot["id"], "t": list(shot["time"]),
            "cam": {"template": move_families[index % len(move_families)],
                    "size0": shot["composition"]["shot_size"],
                    "size1": shot["composition"]["shot_size"]},
            "layout": {"characters": list(shot["characters"]),
                       "arrangement": shot["composition"].get("arrangement", "")},
            "subject": list(range(len(shot["characters"]))),
            "fx": {"transition": shot["transition_out"]["type"]},
            "note": shot["purpose"],
        })
    return {"version": 1, "status": "draft_self_generated", "shots": compiled}


def _storyboard(package):
    rows = ["# Director Storyboard", "", "Status: draft_self_generated", "",
            "| Shot | Time | Energy | Cast | Observable action | Exit |", "|---|---:|---:|---|---|---|"]
    for shot in package["visual_score"]["shots"]:
        time = f"{float(shot['time'][0]):.3f}-{float(shot['time'][1]):.3f}s"
        cast = ", ".join(shot["characters"]) or "empty space"
        rows.append(f"| {shot['id']} | {time} | {shot['energy']} | {cast} | {shot['primary_action']} | {shot['last_frame']} |")
    rows.extend(("", "This document explains the compiled contract. visual_score remains canonical.", ""))
    return "\n".join(rows).encode("utf-8")


def compile_package(package, staging, job_id="local", required_status="approved"):
    package = validate_package(package, required_status=required_status)
    staging_path = Path(staging)
    if staging_path.is_symlink():
        raise ValueError("staging directory cannot be a symlink")
    root = staging_path.resolve()
    root.mkdir(parents=True, exist_ok=True)
    creative = root / "creative"
    outputs = root / "outputs"
    for directory in (creative, outputs):
        if directory.is_symlink():
            raise ValueError("director output directory cannot be a symlink")
        directory.mkdir(parents=True, exist_ok=True)
    values = {
        "creative/story_framework.yaml": _yaml(_story_framework(package)),
        "creative/asset_plan.yaml": _yaml(_asset_plan(package)),
        "creative/generation_plan.yaml": _yaml(_generation_plan(package)),
        "creative/storyboard.md": _storyboard(package),
        "creative/shots.yaml": _yaml(_shots(package)),
    }
    for relative, content in values.items():
        _atomic_write(root / relative, content)

    animatic = package.get("animatic") or {}
    qc = {"status": "not_requested"}
    if animatic.get("enabled", True):
        canvas = package["brief"].get("canvas", package["visual_score"].get("project", {}).get("canvas", "9:16"))
        qc = render_animatic(package["visual_score"]["shots"], canvas, animatic.get("fps", 6), outputs / "animatic.mp4")
        _atomic_write(outputs / "qc_report.json", _canonical_bytes(qc))

    now = datetime.now(timezone.utc).isoformat()
    input_hashes = {
        key: _digest(package[key]) for key in ("brief", "music_map", "character_map", "visual_score")
    }
    artifacts = []
    artifact_paths = []
    for directory in (creative, outputs):
        artifact_paths.extend(path for path in directory.rglob("*") if path.is_file())
    for path in sorted(artifact_paths):
        if path.name == "artifact-manifest.json":
            continue
        content = path.read_bytes()
        artifacts.append({
            "schema_version": 1, "artifact_id": "artifact-" + hashlib.sha256(content).hexdigest()[:24],
            "project_id": package["project_id"], "job_id": job_id,
            "path": path.relative_to(root).as_posix(), "input_hashes": input_hashes,
            "content_hash": _digest_bytes(content), "created_at": now,
            "producer": "mvstudio.director.compiler", "status": "draft_self_generated",
        })
    manifest = {"version": 1, "project_id": package["project_id"], "job_id": job_id,
                "input_digest": _digest(input_hashes), "artifacts": artifacts, "qc": qc}
    _atomic_write(root / "artifact-manifest.json", _canonical_bytes(manifest))
    return manifest
