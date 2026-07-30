import dataclasses
import datetime as _datetime
import hashlib
import json
import math
from types import MappingProxyType
from enum import Enum
from typing import Any, Mapping

from .errors import DomainValidationError


def _normal(value: Any) -> Any:
    if isinstance(value, Enum):
        return _normal(value.value)
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {field.name: _normal(getattr(value, field.name)) for field in dataclasses.fields(value)}
    if isinstance(value, Mapping):
        result = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise DomainValidationError("mapping keys must be strings")
            result[key] = _normal(item)
        return result
    if isinstance(value, (list, tuple)):
        return [_normal(item) for item in value]
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise DomainValidationError("non-finite numbers are not allowed")
        return value
    if isinstance(value, _datetime.datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise DomainValidationError("datetime must be timezone-aware")
        return value.isoformat()
    raise DomainValidationError("value is not JSON-compatible")


def canonical_json(value: Any) -> bytes:
    try:
        return json.dumps(_normal(value), ensure_ascii=False, sort_keys=True,
                          separators=(",", ":"), allow_nan=False).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise DomainValidationError("value cannot be canonically encoded") from exc


def canonical_hash(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(value)).hexdigest()


def freeze_json(value: Any) -> Any:
    """Validate JSON data and replace mutable containers with immutable ones."""
    if isinstance(value, Mapping):
        if any(not isinstance(k, str) for k in value):
            raise DomainValidationError("mapping keys must be strings")
        return MappingProxyType({k: freeze_json(v) for k, v in value.items()})
    if isinstance(value, list):
        return tuple(freeze_json(v) for v in value)
    if isinstance(value, tuple):
        return tuple(freeze_json(v) for v in value)
    _normal(value)
    return value
