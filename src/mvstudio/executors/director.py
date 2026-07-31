"""Bounded supervisor executor for deterministic director compilation."""

from __future__ import annotations

from mvstudio.director import compile_package, validate_package


def validate_input(value):
    return validate_package(value)


def run_director(value, staging, cancelled, send):
    value = validate_input(value)
    if cancelled.is_set():
        send({"kind": "cancelled"})
        return
    send({"kind": "progress", "step": 1, "steps": 2})
    compile_package(value, staging, job_id="supervised")
    if cancelled.is_set():
        send({"kind": "cancelled"})
        return
    send({"kind": "progress", "step": 2, "steps": 2})
    send({"kind": "succeeded"})
