"""Finite parameter-space definitions; unbounded searches are not representable."""
from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from math import prod
from typing import Any, Iterator, Mapping


class SearchSpaceError(ValueError):
    """A parameter-space definition is invalid or unbounded."""


_TYPES = {"int": int, "integer": int, "float": float, "categorical": object}


@dataclass(frozen=True)
class ParameterSpace:
    definition: Mapping[str, Mapping[str, Any]]

    def __post_init__(self) -> None:
        canonical: dict[str, dict[str, Any]] = {}
        for name in sorted(self.definition):
            spec = self.definition[name]
            if not isinstance(name, str) or not name or not isinstance(spec, Mapping):
                raise SearchSpaceError("parameter names and specifications must be explicit")
            kind = spec.get("type")
            if kind not in _TYPES:
                raise SearchSpaceError(f"unsupported type for {name}: {kind!r}")
            if set(spec) != {"type", "values"}:
                raise SearchSpaceError(f"{name} must contain only type and finite values")
            values = spec["values"]
            if not isinstance(values, (list, tuple)) or not values:
                raise SearchSpaceError(f"{name} requires a non-empty finite values list")
            checked = tuple(_validate_value(name, kind, value) for value in values)
            if len({repr(value) for value in checked}) != len(checked):
                raise SearchSpaceError(f"{name} contains duplicate values")
            canonical[name] = {"type": "int" if kind == "integer" else kind, "values": checked}
        object.__setattr__(self, "definition", canonical)

    @property
    def size(self) -> int:
        return prod(len(spec["values"]) for spec in self.definition.values())

    def contains(self, name: str, value: Any) -> bool:
        if name not in self.definition:
            return False
        spec = self.definition[name]
        try:
            checked = _validate_value(name, spec["type"], value)
        except SearchSpaceError:
            return False
        return checked in spec["values"]

    def generate(self, baseline: Mapping[str, Any] | None = None) -> Iterator[dict[str, Any]]:
        """Generate the complete finite grid in deterministic lexical order."""
        base = dict(baseline or {})
        names = tuple(self.definition)
        pools = [self.definition[name]["values"] for name in names]
        for values in product(*pools):
            yield {**base, **dict(zip(names, values))}

    def generate_valid(self, constraints=()) -> Iterator[dict[str, Any]]:
        """Generate only configurations satisfying the supplied explicit rules."""
        from .constraints import ConstraintViolation, validate_configuration
        for config in self.generate():
            try:
                validate_configuration(config, self, constraints)
            except ConstraintViolation:
                continue
            yield config

    def as_dict(self) -> dict[str, dict[str, Any]]:
        return {name: {"type": spec["type"], "values": list(spec["values"])}
                for name, spec in self.definition.items()}


def _validate_value(name: str, kind: str, value: Any) -> Any:
    if kind in ("int", "integer") and (isinstance(value, bool) or not isinstance(value, int)):
        raise SearchSpaceError(f"{name} must contain integers")
    if kind == "float" and (isinstance(value, bool) or not isinstance(value, (int, float))):
        raise SearchSpaceError(f"{name} must contain finite numeric values")
    if kind == "float":
        value = float(value)
        if value != value or value in (float("inf"), float("-inf")):
            raise SearchSpaceError(f"{name} must contain finite numeric values")
    if kind == "categorical" and isinstance(value, (dict, list, set)):
        raise SearchSpaceError(f"{name} categorical values must be scalar")
    return value
