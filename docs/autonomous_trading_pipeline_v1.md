# Autonomous trading pipeline v1

## Architecture and execution flow

`AutonomousTradingPipeline` is a thin, deterministic orchestrator over the
existing production components. It advances qualified scientific findings in
this fixed order:

`PatternEffect → TradingCandidate → StrategyCandidate → BacktestResult → ValidationReport → StrategyRanking`

It does not create hypotheses, change discovery, tune parameters, compare
strategy variants to choose a winner, or mutate a strategy. Strategy expansion
is the fixed, reviewed `StrategyBuilder` catalogue. Backtests must be configured
with explicit transaction costs and slippage.

## Lineage and persistence

Every object retains the identifier of its immediate parent. `ResearchMemory`
enforces those references when appending backtests, validations, and rankings.
All registries are append-only JSON Lines files. Identities are deterministic,
so rerunning after process restart skips every completed object rather than
duplicating it. An incomplete chain resumes at the first missing stage.

## Failure handling

Candidate and strategy failures are isolated by source; backtest and validation
failures are isolated by strategy. A failed backtest cannot create a validation,
and a failed validation cannot create a ranking. Ranking failures leave the
already-persisted validation untouched. Failures are appended to
`pipeline_failures.jsonl` with stage, object identifier, exception type, and
message. Repeated identical failures are recorded once.

## Multi-timeframe and anti-leakage behavior

The pipeline preserves each candidate's execution and context timeframes. This
supports SCALPING (`M1`/`M5` with `M15` context), INTRADAY (`M5`/`M15`/`M30`
with `H1`/`D1` context), and MEDIUM_TERM (`H1`/`D1`) definitions without
rewriting them. The existing backtest engine exposes a context candle only when
its close timestamp is no later than the execution signal timestamp. Entries
occur after the signal close, and intraday entries/exits do not cross the
trading-day boundary.

Calendar 2025 remains locked TRUE OOS. The data provider is responsible for
serving the correct versioned dataset, while the backtest and validation
engines enforce ordering, split, timestamp, and OOS rules. Source data is never
persisted by the pipeline.

## Limitations

The pipeline consumes only complete scientific findings that persist their
originating `Hypothesis`; older memories without that field resume from any
already-persisted trading or strategy object. Ranking positions describe the
new deterministic ranking batch and are immutable facts; this version does not
rewrite historical positions as later research arrives. Operational scheduling
and data loading remain responsibilities of the caller.
