"""Bounded stage executors used by the job supervisor."""

from .legacy import run_legacy, validate_input

__all__ = ["run_legacy", "validate_input"]
