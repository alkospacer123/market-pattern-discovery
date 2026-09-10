# Validation Engine v1

## Purpose and architecture

The validation engine is the evaluation-only continuation of the governed lineage
`StrategyCandidate → BacktestResult → ValidationReport`. It asks whether one already-defined
strategy's after-cost historical behaviour is sufficiently stable for further consideration.
It does not create strategies, tune parameters, rank alternatives, select a winner, or change
the input candidate. A report retains both strategy and backtest identities.

## Deterministic data split and TRUE OOS

`calendar-split-v1` defines half-open, UTC periods: TRAIN is 2019–2023, VALIDATION is 2024,
and locked TRUE_OOS is 2025. Periods are ordered and disjoint. Classification requires an
explicit observation time and rejects a candle whose close is still in the future. The
backtest engine's normal 2025 lock remains enabled everywhere else; only this validation
stage explicitly unlocks 2025 for final evaluation. TRUE_OOS results never feed strategy
construction, sensitivity definitions, or selection.

## Walk-forward evaluation

The fixed expanding chronology has three train/test windows: 2019–2021/2022,
2020–2022/2023, and 2021–2023/2024. Every test follows its train period. Version 1 records
each train and test result reference, the fraction of positive test expectancies, and a deterministic
dispersion-derived stability score. No window is selected or discarded based on its result.

## Controlled robustness

Parameter sensitivity uses exactly two protocol constants, 0.9 and 1.1, on the declared fixed
stop distance (or ATR multiple). These copies are evaluation probes only: they are never
persisted as candidates, compared to find a best value, or returned. The score is the fraction
that preserve the baseline validation expectancy sign. The original frozen strategy is hashed
before and after the complete evaluation and mutation is an error.

## Acceptance rules

`validation-thresholds-v1` is explicit and configurable. Insufficient combined validation/OOS
trades yields `INSUFFICIENT_DATA`. Otherwise `ACCEPTED` requires positive validation and TRUE
OOS expectancy, acceptable OOS profit factor, drawdown within its limit, and walk-forward,
stability, and sensitivity scores at their minima. Failure yields `REJECTED`. This is a gate,
not an optimization objective; profit factor is never maximized and configured transaction
costs and slippage apply to every run.

## Memory and identity

`ResearchMemory` appends canonical reports to `validation_reports.jsonl` only after confirming
the referenced persisted backtest and its strategy lineage. Identity is the deterministic hash
of backtest ID, validation-engine version, and data version. Identical replays after restart are
idempotent; conflicting content under the same identity is rejected.

## Limitations

Version 1 uses calendar rather than exchange-session split policies, closed-trade expectancy,
simple dispersion stability, and two fixed stop perturbations. It does not provide statistical
confidence intervals, regime attribution, portfolio effects, parameter search, ranking, or
promotion. Data ingestion remains external and source market data remains read-only.
