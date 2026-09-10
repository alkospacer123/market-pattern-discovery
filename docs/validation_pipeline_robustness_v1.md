# Validation Pipeline Robustness v1

## Discovered issue

The validation engine split market data into fixed evaluation periods and sent every
slice to the backtest engine. A slice containing fewer than two execution candles
raised an exception. Consequently, the pipeline recorded a failure rather than the
scientifically meaningful result that the available evidence could not support a
conclusion. Declared H1 and D1 context keys could also be absent at the adapter
boundary, causing an earlier backtest failure.

## Old and new behavior

Previously, insufficient execution data or an absent context timeframe interrupted
the `BacktestResult` to `ValidationReport` transition. The pipeline now represents
absent declared context explicitly and validation performs a deterministic preflight.
Missing observations produce a persisted report with `INSUFFICIENT_DATA`, the sample
size, a reason, and a sorted list of missing requirements. Qualification thresholds
and trading behavior are unchanged.

## Status semantics

* `ACCEPTED`: sufficient evidence passes every fixed qualification check.
* `REJECTED`: sufficient evidence fails one or more fixed qualification checks.
* `INSUFFICIENT_DATA`: validation cannot run; no scientific conclusion is possible.

An insufficient report is neither accepted nor rejected. Ranking retains it as an
auditable, unpositioned insufficient-data record.

## Contract and lineage

The required lineage remains `PatternEffect` → `TradingCandidate` →
`StrategyCandidate` → `BacktestResult` → `ValidationReport` → `StrategyRanking`.
Validation requires an actual `BacktestResult` and checks strategy identity, symbol,
execution and context timeframes, execution period, trade consistency, and data
version. Reports preserve the source backtest identifier and execution period.
Research memory continues enforcing persisted backtest lineage, deterministic report
identity, append-only storage, collision detection, and restart-safe deduplication.

## Context and causality

The pipeline adds an empty key for a declared but absent context timeframe. This is
not treated as available evidence: validation records that timeframe as a missing
requirement. The backtest causal alignment remains unchanged and only exposes a
context candle when `context_close_time <= observation_close_time`. Context is never
silently skipped or forward-filled from the future.

## Tests

Tests cover insufficient execution candles, normal accepted and rejected decisions,
missing H1 and D1 context, deterministic output, append-only restart behavior, and
the mandatory `BacktestResult` lineage and data-version contract.

## Limitations

This change does not manufacture missing candles, alter thresholds, redefine a
strategy, or modify entries, stops, exits, transaction costs, slippage, or backtest
trading logic. Data availability still depends on the configured market-data source.
An `INSUFFICIENT_DATA` result must not be interpreted as evidence for or against a
strategy.
