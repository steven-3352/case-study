"""Structured recommendation packages for blocked adfilm workflow nodes."""
from __future__ import annotations

import os
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import yaml


BLOCKED_STATUS = "blocked_with_recommendations"

_TOP_LEVEL_TEXT_FIELDS = (
    "node",
    "reason_code",
    "plain_reason",
    "recommended_option",
    "recommendation_reason",
    "resume_from",
)
_OPTION_TEXT_FIELDS = (
    "id",
    "action",
    "expected_visual_quality",
    "product_fidelity",
    "cost_delta",
    "time_delta",
)


class RecommendationValidationError(ValueError):
    """Raised when a recommendation package violates its public schema."""


def _is_nonempty_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _require_string_list(value: Any, field: str) -> list[str]:
    if not isinstance(value, list) or any(not _is_nonempty_text(item) for item in value):
        raise RecommendationValidationError(f"{field} must be a list of non-empty strings")
    return value


def validate_recommendation(package: Mapping[str, Any]) -> dict[str, Any]:
    """Validate and return a plain copy of a recommendation package."""
    if not isinstance(package, Mapping):
        raise RecommendationValidationError("recommendation package must be a mapping")

    result = dict(package)
    if result.get("status") != BLOCKED_STATUS:
        raise RecommendationValidationError(
            f"status must be {BLOCKED_STATUS!r}"
        )
    for field in _TOP_LEVEL_TEXT_FIELDS:
        if not _is_nonempty_text(result.get(field)):
            raise RecommendationValidationError(f"{field} must be a non-empty string")

    evidence = result.get("evidence", [])
    _require_string_list(evidence, "evidence")

    options = result.get("options")
    if not isinstance(options, list) or not options:
        raise RecommendationValidationError("options must contain at least one option")

    option_ids: list[str] = []
    normalized_options: list[dict[str, Any]] = []
    for index, option in enumerate(options):
        if not isinstance(option, Mapping):
            raise RecommendationValidationError(f"options[{index}] must be a mapping")
        item = dict(option)
        for field in _OPTION_TEXT_FIELDS:
            if not _is_nonempty_text(item.get(field)):
                raise RecommendationValidationError(
                    f"options[{index}].{field} must be a non-empty string"
                )
        _require_string_list(item.get("invalidates"), f"options[{index}].invalidates")
        option_ids.append(item["id"])
        normalized_options.append(item)

    if len(option_ids) != len(set(option_ids)):
        raise RecommendationValidationError("option ids must be unique")
    if result["recommended_option"] not in option_ids:
        raise RecommendationValidationError("recommended_option must reference an option id")
    if len(normalized_options) == 1 and not _is_nonempty_text(result.get("single_option_reason")):
        raise RecommendationValidationError(
            "single_option_reason is required when only one option is available"
        )
    if "single_option_reason" in result and not _is_nonempty_text(result["single_option_reason"]):
        raise RecommendationValidationError("single_option_reason must be a non-empty string")

    result["evidence"] = list(evidence)
    result["options"] = normalized_options
    return result


def build_recommendation(
    *,
    node: str,
    reason_code: str,
    plain_reason: str,
    evidence: Sequence[str] = (),
    options: Sequence[Mapping[str, Any]],
    recommended_option: str,
    recommendation_reason: str,
    resume_from: str,
    single_option_reason: str | None = None,
) -> dict[str, Any]:
    """Build a validated ``blocked_with_recommendations`` package."""
    package: dict[str, Any] = {
        "status": BLOCKED_STATUS,
        "node": node,
        "reason_code": reason_code,
        "plain_reason": plain_reason,
        "evidence": list(evidence),
        "options": [dict(option) for option in options],
        "recommended_option": recommended_option,
        "recommendation_reason": recommendation_reason,
        "resume_from": resume_from,
    }
    if single_option_reason is not None:
        package["single_option_reason"] = single_option_reason
    return validate_recommendation(package)


def write_recommendation(path: str | os.PathLike[str], package: Mapping[str, Any]) -> Path:
    """Validate and atomically write a recommendation package as YAML."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    validated = validate_recommendation(package)
    body = yaml.safe_dump(validated, allow_unicode=True, sort_keys=False)

    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=target.parent,
            prefix=f".{target.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary = Path(handle.name)
            handle.write(body)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, target)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()
    return target
