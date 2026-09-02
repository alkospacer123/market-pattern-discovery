"""Causal, one-way PATTERN_SURVIVOR to V3 strategy synthesis.

This module defines signals only.  Trade creation, exits, costs and ledgers
remain exclusively in :mod:`market_pattern_discovery.backtest.phase6b`.
It deliberately has no dependency on discovery targets or behaviour builders.
"""
from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd

from market_pattern_discovery.contracts import deterministic_hash
from market_pattern_discovery.discovery.execution_contract import feature_inventory
from market_pattern_discovery.features.builder import build_features
from market_pattern_discovery.features.schema import RoundLevelConfig
from market_pattern_discovery.research.memory import PatternEffectRecord, PatternStatus
from market_pattern_discovery.research.protocol import load_protocol

ACTIVATION_RULE = "FALSE_TO_TRUE_ON_CLOSED_BAR_RESET_MOSCOW_TRADING_DATE"
QUANTILE_SOURCE = "TRAIN_ONLY_QUANTILE_CUTPOINTS"


@dataclass(frozen=True, slots=True)
class DirectionDecision:
    direction: str | None
    provenance: str
    reason: str

    @property
    def actionable(self) -> bool:
        return self.direction in {"LONG", "SHORT"}


def map_direction(family: str, target_type: str, contrast: str,
                  primary_effect_signed: float) -> DirectionDecision:
    """Apply the exact, frozen semantic whitelist; ambiguity is rejected."""
    try:
        effect = float(primary_effect_signed)
    except (TypeError, ValueError):
        effect = math.nan
    if not math.isfinite(effect) or effect == 0:
        return DirectionDecision(None, "FROZEN_TARGET_SEMANTIC_WHITELIST_V1",
                                 "NOT_DIRECTIONALLY_ACTIONABLE: ZERO_OR_NONFINITE_EFFECT")
    positive = effect > 0
    mapping: str | None = None
    semantic = ""
    if family == "DIRECTIONAL" and target_type == "continuous" and contrast == "median_difference":
        mapping, semantic = ("LONG" if positive else "SHORT"), "SIGNED_DISPLACEMENT"
    elif family == "DIRECTIONAL" and contrast == "P(+1 | feature_state) - P(+1 | baseline)":
        mapping, semantic = ("LONG" if positive else "SHORT"), "DIRECTION_CLASS_PLUS_ONE"
    elif family == "DIRECTIONAL" and contrast == "P(-1 | feature_state) - P(-1 | baseline)":
        mapping, semantic = ("SHORT" if positive else "LONG"), "DIRECTION_CLASS_MINUS_ONE"
    elif family == "FIRST_PASSAGE" and contrast == "P(+1 upper-first | feature_state) - P(+1 upper-first | baseline)":
        mapping, semantic = ("LONG" if positive else "SHORT"), "FIRST_PASSAGE_UPPER"
    elif family == "FIRST_PASSAGE" and contrast == "P(-1 lower-first | feature_state) - P(-1 lower-first | baseline)":
        mapping, semantic = ("SHORT" if positive else "LONG"), "FIRST_PASSAGE_LOWER"
    if mapping is None:
        return DirectionDecision(None, "FROZEN_TARGET_SEMANTIC_WHITELIST_V1",
                                 f"NOT_DIRECTIONALLY_ACTIONABLE: UNWHITELISTED:{family}:{target_type}:{contrast}")
    return DirectionDecision(mapping, f"FROZEN_TARGET_SEMANTIC_WHITELIST_V1:{semantic}", "ACTIONABLE")


@dataclass(frozen=True, slots=True)
class PatternStrategySpec:
    source_pattern_cell_id: str
    source_scientific_definition: Mapping[str, Any]
    instrument: str
    timeframe: str
    feature_conditions: tuple[tuple[str, Any], ...]
    direction: str
    direction_mapping: str
    signal_activation_rule: str
    state_definition_semantics: str
    contract_signatures: tuple[tuple[str, str], ...]
    execution_contract_lineage: str = "V3_PHASE6B_DEFAULT_EXIT_SURFACE_V1"
    research_track: str = "SYNTHESIZED_STRATEGY"

    def __post_init__(self) -> None:
        if self.direction not in {"LONG", "SHORT"} or self.timeframe not in {"M1", "M5"}:
            raise ValueError("actionable direction and supported timeframe required")
        if self.signal_activation_rule != ACTIVATION_RULE:
            raise ValueError("PatternStrategy v1 activation rule is frozen")
        if self.research_track != "SYNTHESIZED_STRATEGY":
            raise ValueError("invalid synthesized routing identity")
        object.__setattr__(self, "source_scientific_definition", dict(self.source_scientific_definition))
        object.__setattr__(self, "feature_conditions", tuple(tuple(x) for x in self.feature_conditions))
        object.__setattr__(self, "contract_signatures", tuple(sorted(tuple(x) for x in self.contract_signatures)))

    @property
    def pattern_strategy_id(self) -> str:
        # Every field is signal-semantic; runtime roots, cycle and exits cannot enter.
        return deterministic_hash(asdict(self))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self) | {"pattern_strategy_id": self.pattern_strategy_id}

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "PatternStrategySpec":
        fields = dict(value); fields.pop("pattern_strategy_id", None)
        return cls(**fields)


def synthesize_pattern(record: PatternEffectRecord) -> tuple[PatternStrategySpec | None, DirectionDecision]:
    """Accept only an effective persistent survivor, never an incomplete fixture."""
    if record.screening_status is not PatternStatus.PATTERN_SURVIVOR:
        raise ValueError(f"production synthesis requires PATTERN_SURVIVOR, got {record.screening_status.value}")
    definition, evaluation = record.scientific_definition, record.evaluation
    contrast = str(definition.get("contrast"))
    target_type = str(definition.get("target_type", evaluation.get("target_type",
        "continuous" if contrast == "median_difference" else "multiclass")))
    decision = map_direction(str(definition.get("target_family")), target_type,
        contrast, evaluation.get("primary_effect_signed"))
    if not decision.actionable:
        return None, decision
    signatures = definition.get("contract_signatures", evaluation.get("contract_signatures", {}))
    if isinstance(signatures, Mapping): signatures = tuple(signatures.items())
    spec = PatternStrategySpec(record.pattern_cell_id, definition,
        str(definition["instrument"]), str(definition["timeframe"]),
        tuple(tuple(x) for x in definition["feature_conditions"]), decision.direction or "",
        decision.provenance, ACTIVATION_RULE, QUANTILE_SOURCE,
        tuple(tuple(x) for x in signatures))
    return spec, decision


def execution_cell_id(pattern_strategy_id: str, exit_configuration: Sequence[Any]) -> str:
    return deterministic_hash({"pattern_strategy_id": pattern_strategy_id,
                               "exit_configuration": list(exit_configuration)})


def _cutpoints(series: pd.Series) -> tuple[float, float, float, float]:
    clean = pd.to_numeric(series, errors="coerce").dropna()
    values = clean.quantile([.10, .25, .75, .90], interpolation="linear").to_numpy(float)
    return tuple(float(x) for x in values)  # type: ignore[return-value]


def _apply_quantile(series: pd.Series, cuts: Sequence[float]) -> pd.Series:
    p10, p25, p75, p90 = cuts; numeric = pd.to_numeric(series, errors="coerce")
    out = pd.Series("MISSING", index=series.index, dtype="object")
    out.loc[numeric.notna() & (numeric <= p10)] = "LE_P10"
    out.loc[numeric.notna() & (numeric > p10) & (numeric <= p25)] = "P10_P25"
    out.loc[numeric.notna() & (numeric > p25) & (numeric <= p75)] = "P25_P75"
    out.loc[numeric.notna() & (numeric > p75) & (numeric <= p90)] = "P75_P90"
    out.loc[numeric.notna() & (numeric > p90)] = "GE_P90"
    return out


def generate_pattern_signals(frame: pd.DataFrame, spec: PatternStrategySpec,
                             *, native_m5: pd.DataFrame | None = None) -> pd.DataFrame:
    """Regenerate validation-only signals from raw bars and a serializable spec."""
    alias = {"CNY": "CNYRUBF", "Si": "USDRUBF"}.get(spec.instrument, spec.instrument)
    settings = {"CNYRUBF": (.001, .05), "USDRUBF": (.01, .10)}
    tick, step = settings[alias]
    built = build_features(frame, timeframe=spec.timeframe,
        round_levels=RoundLevelConfig(tick, step, tick), native_m5=native_m5).frame
    inventory = {x["feature"]: x["representation"] for x in feature_inventory(spec.timeframe, included_only=True)}
    folds = load_protocol()["walk_forward_folds"]
    events: list[dict[str, Any]] = []
    direction = 1 if spec.direction == "LONG" else -1
    for fold in folds:
        ts = pd.to_datetime(frame.open_time, utc=True)
        tr0, tr1 = map(pd.Timestamp, fold["train"]); va0, va1 = map(pd.Timestamp, fold["validate"])
        train = (ts >= tr0) & (ts < tr1); validate = (ts >= va0) & (ts < va1)
        condition = pd.Series(True, index=frame.index); audit = {}
        for feature, desired in spec.feature_conditions:
            if feature not in built or feature not in inventory:
                raise ValueError(f"frozen feature unavailable: {feature}")
            rep = inventory[feature]
            if "quantile" in rep:
                cuts = _cutpoints(built.loc[train, feature])
                state = _apply_quantile(built[feature], cuts); audit[feature] = {"cutpoints": cuts, "source": QUANTILE_SOURCE}
            else:
                numeric = pd.to_numeric(built[feature], errors="coerce")
                state = numeric.astype("Int64").astype(str) if rep == "binary" else built[feature].astype(str)
            condition &= state.eq(str(desired))
        # Transition memory is evaluated within validation and resets every Moscow date.
        dates = frame.trading_date if "trading_date" in frame else frame.open_time.dt.tz_convert("Europe/Moscow").dt.date
        rising = condition & ~condition.groupby(dates, sort=False).shift(1, fill_value=False) & validate
        for i in frame.index[rising]:
            atr = frame.at[i, "atr14"] if "atr14" in frame else np.nan
            if not math.isfinite(float(atr)): continue
            events.append({"strategy_id": spec.pattern_strategy_id, "pattern_strategy_id": spec.pattern_strategy_id,
                "bar_index": int(i), "side": spec.direction, "direction": direction,
                "ATR_at_signal": float(atr), "reference_level": None,
                "signal_time": frame.at[i, "close_time"], "instrument": alias,
                "source_pattern_cell_id": spec.source_pattern_cell_id, "fold_id": fold["fold_id"],
                "feature_state_audit": audit, "definition_source": QUANTILE_SOURCE,
                "train_interval": fold["train"], "validation_interval": fold["validate"]})
    columns = ["strategy_id","pattern_strategy_id","bar_index","side","direction","ATR_at_signal",
               "reference_level","signal_time","instrument","source_pattern_cell_id","fold_id",
               "feature_state_audit","definition_source","train_interval","validation_interval"]
    return pd.DataFrame(events, columns=columns).sort_values(["bar_index"], kind="mergesort").reset_index(drop=True)


FROZEN_TRADING_SURVIVOR_POLICY = {
    "minimum_base_trades": 30, "minimum_unique_trading_days": 15,
    "minimum_base_profit_factor": 2.0, "minimum_base_expectancy": 0.0,
    "minimum_stress_profit_factor": 1.5, "minimum_stress_expectancy": 0.0,
    "minimum_positive_calendar_blocks": 3, "maximum_largest_winner_share": .25,
    "neighbour_base_pf_floor": 1.25, "neighbour_base_expectancy_floor": 0.0,
    "minimum_passing_neighbours": 2,
}


def exit_neighbours(name: str) -> tuple[str, ...]:
    grid = [(s, t) for s in (.5, 1.) for t in (1., 1.5, 2.)]
    if name.startswith("TIME_"):
        times = [15, 30, 60]; value = int(name.split("_")[1]); i = times.index(value)
        return tuple(f"TIME_{times[j]}" for j in range(len(times)) if abs(i-j) == 1)
    _, s, _, t = name.split("_"); cell = (float(s), float(t)); i = grid.index(cell)
    return tuple(f"STOP_{a}_TARGET_{b}" for a,b in grid
                 if abs((.5,1.).index(a)-(.5,1.).index(cell[0])) +
                    abs((1.,1.5,2.).index(b)-(1.,1.5,2.).index(cell[1])) == 1)


def assess_exit_surface(evidence: Mapping[str, Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    """Apply the preregistered transparent gate to persisted V3 facts only.

    ``evidence`` is keyed by exit name and contains BASE/STRESS metrics plus
    temporal and concentration facts derived by the caller from V3 CSVs.  This
    function never imports or invokes the simulator.
    """
    policy = FROZEN_TRADING_SURVIVOR_POLICY; result = {}
    for name in sorted(evidence):
        row = evidence[name]; base = row.get("BASE", {}); stress = row.get("STRESS", {})
        neighbours = []
        for neighbour_id in exit_neighbours(name):
            neighbour_base = evidence.get(neighbour_id, {}).get("BASE", {})
            passes = (neighbour_base.get("profit_factor", -math.inf) >= policy["neighbour_base_pf_floor"]
                      and neighbour_base.get("expectancy", -math.inf) > policy["neighbour_base_expectancy_floor"])
            neighbours.append({"exit_configuration": neighbour_id, "BASE": dict(neighbour_base), "passes": passes})
        checks = {
            "base_trades": base.get("trades", 0) >= policy["minimum_base_trades"],
            "unique_trading_days": row.get("unique_trading_days", 0) >= policy["minimum_unique_trading_days"],
            "base_profit_factor": base.get("profit_factor", -math.inf) >= policy["minimum_base_profit_factor"],
            "base_expectancy": base.get("expectancy", -math.inf) > policy["minimum_base_expectancy"],
            "stress_profit_factor": stress.get("profit_factor", -math.inf) >= policy["minimum_stress_profit_factor"],
            "stress_expectancy": stress.get("expectancy", -math.inf) > policy["minimum_stress_expectancy"],
            "positive_calendar_blocks": row.get("positive_calendar_blocks", 0) >= policy["minimum_positive_calendar_blocks"],
            "winner_concentration": row.get("largest_winner_share", math.inf) <= policy["maximum_largest_winner_share"],
            "neighbour_plateau": sum(x["passes"] for x in neighbours) >= policy["minimum_passing_neighbours"],
        }
        result[name] = {"exit_configuration": name, "BASE": dict(base), "STRESS": dict(stress),
                        "neighbours": neighbours, "checks": checks,
                        "trading_survivor": all(checks.values()),
                        "candidate_status": "GENERATED"}
    return result
