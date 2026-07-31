"""Bounded supervisor executor for deterministic director intake."""

from __future__ import annotations

from mvstudio.director.intake import inspect_intake, validate_intake


def validate_input(value):
    return validate_intake(value)


def run_director_intake(value, staging, cancelled, send):
    value = validate_input(value)
    if cancelled.is_set():
        send({"kind": "cancelled"})
        return
    send({"kind": "progress", "step": 1, "steps": 2})
    inspect_intake(value, staging)
    if cancelled.is_set():
        send({"kind": "cancelled"})
        return
    send({"kind": "progress", "step": 2, "steps": 2})
    send({"kind": "succeeded"})
