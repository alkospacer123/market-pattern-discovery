"""Explicit configuration constraints with no strategy-specific hidden rules."""
from __future__ import annotations

from datetime import date, datetime
from typing import Any, Mapping, Sequence

from .parameter_space import ParameterSpace

TRUE_OOS_START = datetime(2025, 1, 1)
_OPERATORS = {"<": lambda a, b: a < b, "<=": lambda a, b: a <= b,
              ">": lambda a, b: a > b, ">=": lambda a, b: a >= b,
              "==": lambda a, b: a == b, "!=": lambda a, b: a != b}


class ConstraintViolation(ValueError):
    pass


def validate_configuration(config: Mapping[str, Any], space: ParameterSpace,
                           constraints: Sequence[Mapping[str, Any]] = ()) -> None:
    """Validate membership plus explicitly declared relational/forbidden rules."""
    for name, value in config.items():
        if _looks_oos_parameter(name) or _is_true_oos_value(value):
            raise ConstraintViolation(f"TRUE_OOS_PARAMETER_BLOCKED: {name}")
        if name not in space.definition:
            raise ConstraintViolation(f"unknown parameter: {name}")
    for name in space.definition:
        if name not in config:
            raise ConstraintViolation(f"missing parameter: {name}")
        if not space.contains(name, config[name]):
            raise ConstraintViolation(f"parameter outside bounded space: {name}")
    for rule in constraints:
        if set(rule) == {"left", "operator", "right"}:
            left, right, operator = rule["left"], rule["right"], rule["operator"]
            if left not in config or right not in config or operator not in _OPERATORS:
                raise ConstraintViolation(f"invalid explicit relation: {rule}")
            if not _OPERATORS[operator](config[left], config[right]):
                raise ConstraintViolation(f"constraint failed: {left} {operator} {right}")
        elif set(rule) == {"forbidden"} and isinstance(rule["forbidden"], Mapping):
            if all(config.get(key) == value for key, value in rule["forbidden"].items()):
                raise ConstraintViolation("forbidden parameter combination")
        else:
            raise ConstraintViolation(f"unknown explicit constraint: {rule}")


def _looks_oos_parameter(name: str) -> bool:
    normalized = name.lower().replace("-", "_")
    return "true_oos" in normalized or normalized in {"oos", "oos_data", "oos_period"}


def _is_true_oos_value(value: Any) -> bool:
    if isinstance(value, datetime):
        return value.replace(tzinfo=None) >= TRUE_OOS_START
    if isinstance(value, date):
        return value >= TRUE_OOS_START.date()
    return False
