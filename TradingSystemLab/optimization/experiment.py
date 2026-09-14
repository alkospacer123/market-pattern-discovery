"""Immutable, serializable experiment definition."""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from typing import Any, Mapping, Sequence

from .parameter_space import ParameterSpace

REQUIRED_METRICS = ("PF_R_C1", "expectancy_C1", "net_R_C1", "max_DD_R_C1",
                    "recovery_factor", "trade_count", "top3_concentration")


def _json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def stable_hash(value: Any) -> str:
    return hashlib.sha256(_json_bytes(value)).hexdigest()


def deterministic_experiment_id(strategy_id: str, baseline_config: Mapping[str, Any],
                                parameter_space: ParameterSpace | Mapping[str, Any]) -> str:
    space = parameter_space.as_dict() if isinstance(parameter_space, ParameterSpace) else parameter_space
    digest = stable_hash({"strategy_id": strategy_id,
                          "baseline_config_hash": stable_hash(baseline_config),
                          "parameter_space_hash": stable_hash(space)})
    return f"phase3-{digest[:20]}"


@dataclass(frozen=True)
class Experiment:
    strategy_id: str
    baseline_config: Mapping[str, Any]
    parameter_space: ParameterSpace | Mapping[str, Any]
    constraints: Sequence[Mapping[str, Any]] = field(default_factory=tuple)
    cost_scenarios: Sequence[str] = ("C0", "C1")
    data_period: Mapping[str, str] = field(default_factory=lambda: {"start": "2023-01-01", "end": "2024-12-31"})
    symbols: Sequence[str] = ("Si", "CNY")
    metrics_required: Sequence[str] = REQUIRED_METRICS
    seed: int = 0
    optimization_enabled: bool = False
    walk_forward_enabled: bool = False
    true_oos_blocked: bool = True
    baseline_only: bool = True
    experiment_id: str = ""

    def __post_init__(self) -> None:
        space = self.parameter_space if isinstance(self.parameter_space, ParameterSpace) else ParameterSpace(self.parameter_space)
        object.__setattr__(self, "parameter_space", space)
        expected = deterministic_experiment_id(self.strategy_id, self.baseline_config, space)
        if self.experiment_id and self.experiment_id != expected:
            raise ValueError("experiment_id does not match deterministic content")
        object.__setattr__(self, "experiment_id", expected)
        if not self.baseline_only or self.optimization_enabled or self.walk_forward_enabled:
            raise ValueError("PHASE_3_1_BASELINE_ONLY")
        if not self.true_oos_blocked:
            raise ValueError("TRUE_OOS_MUST_BE_BLOCKED")

    def as_dict(self) -> dict[str, Any]:
        return {"experiment_id": self.experiment_id, "strategy_id": self.strategy_id,
                "baseline_config": dict(self.baseline_config),
                "baseline_config_hash": stable_hash(self.baseline_config),
                "parameter_space": self.parameter_space.as_dict(),
                "parameter_space_hash": stable_hash(self.parameter_space.as_dict()),
                "constraints": list(self.constraints), "cost_scenarios": list(self.cost_scenarios),
                "data_period": dict(self.data_period), "symbols": list(self.symbols),
                "metrics_required": list(self.metrics_required), "seed": self.seed,
                "optimization_enabled": self.optimization_enabled,
                "walk_forward_enabled": self.walk_forward_enabled,
                "true_oos_blocked": self.true_oos_blocked, "baseline_only": self.baseline_only}

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "Experiment":
        """Load a persisted definition and verify its content-derived identifier."""
        ignored_hashes = {"baseline_config_hash", "parameter_space_hash"}
        payload = {key: item for key, item in value.items() if key not in ignored_hashes}
        return cls(**payload)
