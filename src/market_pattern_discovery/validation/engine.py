"""Evaluation-only robustness checks for an immutable strategy candidate."""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from enum import StrEnum
from statistics import mean, pstdev
from typing import Any, Mapping

from market_pattern_discovery.backtest import BacktestEngine, BacktestResult, CostModel
from market_pattern_discovery.contracts import deterministic_hash
from market_pattern_discovery.research.strategy_candidates import RiskDefinition, StrategyCandidate


class DataPartition(StrEnum):
    TRAIN = "TRAIN"
    VALIDATION = "VALIDATION"
    TRUE_OOS = "TRUE_OOS"


class ValidationStatus(StrEnum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


@dataclass(frozen=True, slots=True)
class Period:
    start: datetime
    end: datetime

    def __post_init__(self) -> None:
        start, end = _time(self.start), _time(self.end)
        if start >= end:
            raise ValueError("period start must precede its exclusive end")
        object.__setattr__(self, "start", start)
        object.__setattr__(self, "end", end)

    def contains(self, value: datetime) -> bool:
        return self.start <= _time(value) < self.end

    def to_dict(self) -> dict[str, str]:
        return {"start": self.start.isoformat(), "end": self.end.isoformat()}


@dataclass(frozen=True, slots=True)
class WalkForwardWindow:
    train: Period
    test: Period

    def __post_init__(self) -> None:
        if self.train.end > self.test.start:
            raise ValueError("walk-forward train data must end before test data starts")


@dataclass(frozen=True, slots=True)
class DataSplit:
    training_period: Period
    validation_period: Period
    true_oos_period: Period
    walk_forward_windows: tuple[WalkForwardWindow, ...]
    version: str = "calendar-split-v1"

    def __post_init__(self) -> None:
        if not self.version:
            raise ValueError("split version is required")
        if not (self.training_period.end <= self.validation_period.start
                and self.validation_period.end <= self.true_oos_period.start):
            raise ValueError("TRAIN, VALIDATION, and TRUE_OOS must be ordered and disjoint")
        if self.true_oos_period.start.year != 2025:
            raise ValueError("TRUE_OOS must begin in locked calendar year 2025")
        object.__setattr__(self, "walk_forward_windows", tuple(self.walk_forward_windows))

    @classmethod
    def calendar_v1(cls) -> "DataSplit":
        at = lambda year: datetime(year, 1, 1, tzinfo=timezone.utc)
        return cls(Period(at(2019), at(2024)), Period(at(2024), at(2025)),
                   Period(at(2025), at(2026)), (
                       WalkForwardWindow(Period(at(2019), at(2022)), Period(at(2022), at(2023))),
                       WalkForwardWindow(Period(at(2020), at(2023)), Period(at(2023), at(2024))),
                       WalkForwardWindow(Period(at(2021), at(2024)), Period(at(2024), at(2025))),
                   ))

    def partition_at(self, timestamp: datetime, *, observed_at: datetime) -> DataPartition:
        """Classify only a candle already closed at ``observed_at``."""
        timestamp, observed_at = _time(timestamp), _time(observed_at)
        if timestamp > observed_at:
            raise ValueError("future data is unavailable")
        for name, period in ((DataPartition.TRAIN, self.training_period),
                             (DataPartition.VALIDATION, self.validation_period),
                             (DataPartition.TRUE_OOS, self.true_oos_period)):
            if period.contains(timestamp):
                return name
        raise ValueError("timestamp is outside the versioned split")


@dataclass(frozen=True, slots=True)
class ValidationThresholds:
    minimum_trades: int = 3
    minimum_profit_factor: float = 1.0
    minimum_expectancy: float = 0.0
    maximum_drawdown: float = 10.0
    minimum_walk_forward_score: float = .5
    minimum_stability_score: float = .5
    minimum_parameter_sensitivity_score: float = .5
    version: str = "validation-thresholds-v1"


@dataclass(frozen=True, slots=True)
class ValidationReport:
    validation_id: str
    backtest_id: str
    strategy_id: str
    symbol: str
    timeframe: str
    validation_version: str
    training_period: Period
    validation_period: Period
    true_oos_period: Period
    training_result_reference: str
    validation_result_reference: str
    oos_result_reference: str
    walk_forward_result_references: tuple[str, ...]
    walk_forward_score: float
    stability_score: float
    parameter_sensitivity_score: float
    sample_size: int
    trade_count: int
    profit_factor: float | None
    expectancy: float
    max_drawdown: float
    status: ValidationStatus
    reason: str
    engine_version: str
    data_version: str

    def __post_init__(self) -> None:
        for name in ("training_period", "validation_period", "true_oos_period"):
            value = getattr(self, name)
            object.__setattr__(self, name, value if isinstance(value, Period) else Period(**value))
        object.__setattr__(self, "walk_forward_result_references", tuple(self.walk_forward_result_references))
        object.__setattr__(self, "status", ValidationStatus(self.status))

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        for name in ("training_period", "validation_period", "true_oos_period"):
            value[name] = getattr(self, name).to_dict()
        value["status"] = self.status.value
        return value

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "ValidationReport":
        return cls(**dict(value))


def _time(value: Any) -> datetime:
    result = value if isinstance(value, datetime) else datetime.fromisoformat(str(value))
    if result.tzinfo is None:
        raise ValueError("timestamps must be timezone-aware")
    return result


class ValidationEngine:
    """Run fixed checks; no outcome-driven search or strategy selection exists here."""

    SENSITIVITY_MULTIPLIERS = (.9, 1.1)

    def __init__(self, costs: CostModel, *, thresholds: ValidationThresholds | None = None,
                 engine_version: str = "validation-engine-v1") -> None:
        self.costs = costs
        self.thresholds = thresholds or ValidationThresholds()
        self.engine_version = engine_version

    def validate(self, strategy: StrategyCandidate, backtest: BacktestResult, market_data: Any,
                 *, split: DataSplit, data_version: str) -> ValidationReport:
        if backtest.strategy_id != strategy.strategy_id:
            raise ValueError("backtest does not reference the supplied StrategyCandidate")
        before = deterministic_hash(strategy)
        train = self._run(strategy, market_data, split.training_period, data_version, "train")
        validation = self._run(strategy, market_data, split.validation_period, data_version, "validation")
        oos = self._run(strategy, market_data, split.true_oos_period, data_version, "true-oos")
        window_pairs = tuple((
            self._run(strategy, market_data, window.train, data_version, f"wf-{i}-train"),
            self._run(strategy, market_data, window.test, data_version, f"wf-{i}-test"),
        ) for i, window in enumerate(split.walk_forward_windows, 1))
        windows = tuple(test for _, test in window_pairs)
        sensitivity = self._sensitivity(strategy, market_data, split.validation_period, data_version,
                                        validation.expectancy)
        if deterministic_hash(strategy) != before:
            raise RuntimeError("validation modified StrategyCandidate")
        wf_score = mean(result.expectancy > 0 for result in windows) if windows else 0.0
        values = [result.expectancy for result in windows]
        stability = 1.0 / (1.0 + pstdev(values)) if len(values) > 1 else (1.0 if values else 0.0)
        total = validation.total_trades + oos.total_trades
        status, reason = self._decision(validation, oos, total, wf_score, stability, sensitivity)
        validation_version = f"{self.engine_version}/{self.thresholds.version}/{split.version}"
        identity = deterministic_hash({"backtest_id": backtest.backtest_id,
            "validation_version": validation_version, "data_version": data_version})
        sample_size = sum(len(self._rows(rows)) for rows in self._mapping(market_data).values())
        return ValidationReport(identity, backtest.backtest_id, strategy.strategy_id, strategy.symbol,
            strategy.execution_timeframe, validation_version, split.training_period, split.validation_period,
            split.true_oos_period, train.backtest_id, validation.backtest_id, oos.backtest_id,
            tuple(row.backtest_id for pair in window_pairs for row in pair),
            wf_score, stability, sensitivity, sample_size,
            total, oos.profit_factor, oos.expectancy, max(validation.max_drawdown, oos.max_drawdown),
            status, reason, self.engine_version, data_version)

    def _run(self, strategy: StrategyCandidate, data: Any, period: Period,
             data_version: str, label: str) -> BacktestResult:
        subset = {tf: [row for row in self._rows(rows) if period.contains(self._stamp(row))]
                  for tf, rows in self._mapping(data).items()}
        return BacktestEngine(self.costs, engine_version=f"{self.engine_version}:{label}",
                              forbid_true_oos=False).run(strategy, subset,
                                                         data_version=f"{data_version}:{label}")

    def _sensitivity(self, strategy: StrategyCandidate, data: Any, period: Period,
                     version: str, baseline: float) -> float:
        params = dict(strategy.risk.parameters)
        key = "distance_units" if "distance_units" in params else "atr_multiple"
        if key not in params:
            return 1.0
        signs = []
        for multiplier in self.SENSITIVITY_MULTIPLIERS:  # fixed protocol; never ranked or selected
            varied = replace(strategy, risk=RiskDefinition(strategy.risk.risk_type,
                             {**params, key: float(params[key]) * multiplier}))
            result = self._run(varied, data, period, version, f"sensitivity-{multiplier}")
            signs.append((result.expectancy >= 0) == (baseline >= 0))
        return mean(signs)

    def _decision(self, validation: BacktestResult, oos: BacktestResult, trades: int,
                  walk: float, stability: float, sensitivity: float) -> tuple[ValidationStatus, str]:
        t = self.thresholds
        if trades < t.minimum_trades:
            return ValidationStatus.INSUFFICIENT_DATA, f"trade_count {trades} < {t.minimum_trades}"
        checks = (validation.expectancy > t.minimum_expectancy,
                  oos.expectancy > t.minimum_expectancy,
                  oos.profit_factor is None or oos.profit_factor >= t.minimum_profit_factor,
                  max(validation.max_drawdown, oos.max_drawdown) <= t.maximum_drawdown,
                  walk >= t.minimum_walk_forward_score, stability >= t.minimum_stability_score,
                  sensitivity >= t.minimum_parameter_sensitivity_score)
        return ((ValidationStatus.ACCEPTED, f"passed {t.version}") if all(checks)
                else (ValidationStatus.REJECTED, f"failed robustness under {t.version}"))

    @staticmethod
    def _mapping(data: Any) -> Mapping[str, Any]:
        if not isinstance(data, Mapping):
            raise TypeError("validation requires timeframe-keyed market data")
        return data

    @staticmethod
    def _rows(rows: Any) -> list[Any]:
        return rows.to_dict("records") if hasattr(rows, "to_dict") else list(rows)

    @staticmethod
    def _stamp(row: Any) -> datetime:
        raw = dict(row) if isinstance(row, Mapping) else asdict(row)
        return _time(raw.get("close_time", raw.get("time", raw.get("timestamp"))))
