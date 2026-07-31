"""Bounded executor for draft-only structural animatic compilation."""

from pathlib import Path

from mvstudio.director.compiler import compile_package
from mvstudio.director.contracts import validate_package


def validate_input(value):
    return validate_package(value, required_status="draft_self_generated")


def run_director_structural(value, staging, cancelled, send):
    value = validate_input(value)
    if cancelled.is_set():
        send({"kind": "cancelled"})
        return
    send({"kind": "progress", "step": 1, "steps": 2})
    compile_package(value, staging, job_id=Path(staging).name, required_status="draft_self_generated")
    if cancelled.is_set():
        send({"kind": "cancelled"})
        return
    send({"kind": "progress", "step": 2, "steps": 2})
    send({"kind": "succeeded"})
