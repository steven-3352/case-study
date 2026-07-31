"""Isolated compatibility executor for deterministic legacy stages."""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
import time
from pathlib import Path

from mvstudio.engines.mv.session import Session


def validate_input(value):
    if value is None:
        value = {}
    if not isinstance(value, dict):
        raise ValueError("executor input must be a mapping")
    allowed = {"renderer", "marker", "steps", "delay_seconds"}
    if set(value) - allowed:
        raise ValueError("unknown legacy executor input key")
    renderer = value.get("renderer", "synthetic")
    marker = value.get("marker", "fixture")
    steps = value.get("steps", 1)
    delay = value.get("delay_seconds", 0.0)
    if renderer != "synthetic":
        raise ValueError("unknown legacy renderer")
    if not isinstance(marker, str) or not marker or len(marker) > 128:
        raise ValueError("marker must be a non-empty string of at most 128 characters")
    if isinstance(steps, bool) or not isinstance(steps, int) or not 1 <= steps <= 100:
        raise ValueError("steps must be an integer from 1 through 100")
    if isinstance(delay, bool) or not isinstance(delay, (int, float)) or not 0 <= delay <= 0.2:
        raise ValueError("delay_seconds must be from 0 through 0.2")
    return {"renderer": renderer, "marker": marker, "steps": steps,
            "delay_seconds": float(delay)}


def _atomic_json(destination: Path, value: dict) -> None:
    fd, temporary = tempfile.mkstemp(prefix=".legacy-result-", dir=str(destination.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, sort_keys=True, separators=(",", ":"))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, destination)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def run_legacy(value, staging, cancelled, send):
    value = validate_input(value)
    root = Path(staging).resolve()
    session_root = root / ".session"
    session = Session(session_root / "assets", session_root / "textures",
                      session_root / "generated")
    for directory in (session.assets_dir, session.tex_dir, session.gen_dir):
        directory.mkdir(parents=True, exist_ok=True)
    for step in range(1, value["steps"] + 1):
        if cancelled.is_set():
            send({"kind": "cancelled"})
            return
        if value["delay_seconds"]:
            time.sleep(value["delay_seconds"])
        send({"kind": "progress", "step": step, "steps": value["steps"]})
    marker = value["marker"]
    _atomic_json(root / "legacy-result.json", {
        "renderer": value["renderer"],
        "marker": marker,
        "digest": "sha256:" + hashlib.sha256(marker.encode("utf-8")).hexdigest(),
    })
    send({"kind": "succeeded"})
