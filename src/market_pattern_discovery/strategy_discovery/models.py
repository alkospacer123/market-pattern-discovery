"""Serializable Phase 6A contracts; deliberately contains no training/backtesting."""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from enum import StrEnum
from typing import Any
from .governance import canonical_sha256

class OriginTrack(StrEnum):
    KNOWN="KNOWN"; ORACLE="ORACLE"; ML_DISCOVERY="ML_DISCOVERY"

FUTURE_OUTCOME_FIELDS = frozenset({"signed_displacement", "mfe", "mae", "mfe_before_mae",
 "mae_before_mfe", "time_to_mfe", "time_to_mae", "normalized_mfe", "normalized_mae",
 "breakout_outcome", "reversal_outcome", "return_to_reference_level", "continuation_after_level",
 "barrier_outcome", "future_return", "target"})

class FutureFieldLeakage(ValueError): pass

def validate_predictors(predictors: list[str], future_fields: set[str] | frozenset[str] = FUTURE_OUTCOME_FIELDS) -> None:
    leaked = sorted(set(predictors) & set(future_fields))
    if leaked: raise FutureFieldLeakage(f"future outcomes cannot be predictors: {leaked}")
    if any(x.startswith(("future_", "target_")) for x in predictors):
        raise FutureFieldLeakage("future/target-prefixed field cannot be executable")

@dataclass(frozen=True)
class OracleTarget:
    target_id: str; horizon: str; future_outcome_fields: tuple[str, ...]
    causal_predictor_fields: tuple[str, ...]; side: str = "BOTH"
    upper_atr_barrier: float | None = None; lower_atr_barrier: float | None = None
    def __post_init__(self):
        if self.horizon not in {"5m","15m","30m","60m","120m"}: raise ValueError("unsupported horizon")
        validate_predictors(list(self.causal_predictor_fields), frozenset(self.future_outcome_fields) | FUTURE_OUTCOME_FIELDS)

@dataclass(frozen=True)
class MLHypothesisConfig:
    model_family: str; causal_x_fields: tuple[str,...]; future_y_field: str
    walk_forward: bool = True; deterministic_seed: int = 617
    feature_importance: bool = True; permutation_importance: bool = True
    rule_extraction: bool = True; interaction_discovery: bool = True; simplify_candidate: bool = True
    provenance: dict[str, Any] = field(default_factory=dict)
    def __post_init__(self):
        if self.model_family not in {"LOGISTIC_REGRESSION","EXTRA_TREES","RANDOM_FOREST","GRADIENT_BOOSTING"}: raise ValueError("non-preregistered model")
        validate_predictors(list(self.causal_x_fields))
    @property
    def config_sha256(self): return canonical_sha256(asdict(self))

REQUIRED_STRATEGY_FIELDS = {"strategy_id","parent_family_id","origin_track","version","instrument","timeframe",
 "decision_clock","causal_predicates","entry_side","entry_timing","reference_level_definition","context_filters",
 "position_constraints","exit_definition","stop_definition","target_definition","time_exit","transaction_cost_model_ref",
 "slippage_model_ref","parameters","lineage","parent_candidate_ids","creation_stage","status","strategy_sha256"}

def validate_causal_strategy(spec: dict[str, Any]) -> None:
    missing = REQUIRED_STRATEGY_FIELDS-set(spec)
    if missing: raise ValueError(f"missing strategy fields: {sorted(missing)}")
    fields = [p["field"] for p in spec["causal_predicates"]] + [f["field"] for f in spec["context_filters"]]
    validate_predictors(fields)
    if not spec.get("causal_validation_passed", False): raise ValueError("strategy is not executable without causal validation PASS")

@dataclass(frozen=True)
class BacktestMetrics:
    gross_pnl: float; net_pnl: float; commissions: float; slippage: float; number_of_trades: int
    win_rate: float; average_win: float; average_loss: float; payoff_ratio: float; expectancy_per_trade: float
    profit_factor: float; max_drawdown: float; recovery_factor: float; sharpe: float; sortino: float
    max_consecutive_losses: int; average_holding_time: float
    long_metrics: dict=field(default_factory=dict); short_metrics: dict=field(default_factory=dict)
    monthly_metrics: dict=field(default_factory=dict); instrument_metrics: dict=field(default_factory=dict); timeframe_metrics: dict=field(default_factory=dict)

@dataclass(frozen=True)
class RobustnessPlan:
    transaction_cost_stress: bool=True; doubled_cost_stress: bool=True; slippage_stress: bool=True
    one_candle_entry_delay: bool=True; parameter_perturbation: bool=True; parameter_plateau_analysis: bool=True
    month_stability: bool=True; side_consistency: bool=True; instrument_consistency: bool=True
    timeframe_consistency: bool=True; walk_forward_consistency: bool=True
    preregistered_metric_weights: dict[str,float] | None=None

def plateau_summary(values: list[float], within_fraction: float=.1) -> dict[str, float]:
    """Transparent breadth/sharpness descriptors, not an outcome-derived score."""
    if not values: raise ValueError("empty plateau")
    peak=max(values); threshold=peak-abs(peak)*within_fraction
    broad=sum(v>=threshold for v in values)/len(values)
    neighbours=sum(values[i]>=threshold for i in range(1,len(values)-1) if values[i-1]>=threshold and values[i+1]>=threshold)
    return {"peak":peak,"near_peak_fraction":broad,"supported_interior_points":float(neighbours)}
