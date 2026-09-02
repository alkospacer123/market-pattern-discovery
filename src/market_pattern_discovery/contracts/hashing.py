"""Canonical serialization and hashing shared by the V3.5 boundary layers."""
from __future__ import annotations

import dataclasses
import hashlib
import json
import math
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Any, Mapping


def _canonical(value: Any) -> Any:
    if dataclasses.is_dataclass(value):
        value = dataclasses.asdict(value)
    if isinstance(value, Mapping):
        return {str(key): _canonical(item) for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))}
    if isinstance(value, (list, tuple)):
        return [_canonical(item) for item in value]
    if isinstance(value, (set, frozenset)):
        return sorted((_canonical(item) for item in value), key=canonical_json)
    if isinstance(value, Enum):
        return _canonical(value.value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, Path):
        return value.as_posix()
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("canonical hashes do not permit NaN or infinity")
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise TypeError(f"unsupported canonical value: {type(value).__name__}")


def canonical_json(value: Any) -> str:
    """Return the unique UTF-8 JSON representation used by all identifiers."""
    return json.dumps(_canonical(value), ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False)


def deterministic_hash(value: Any) -> str:
    """Return a stable SHA-256 hex digest independent of mapping insertion order."""
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()
