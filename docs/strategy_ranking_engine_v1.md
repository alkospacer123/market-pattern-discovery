# Strategy Ranking Engine v1

## Purpose and architecture

The ranking engine is an evaluation-only layer after validation:

`PatternEffect → TradingCandidate → StrategyCandidate → BacktestResult → ValidationReport → StrategyRanking`

It compares already validated strategies. It neither constructs or mutates a
strategy, creates trades, searches parameters, nor selects a configuration.
The caller supplies the immutable validation report and its strategy/trading
lineage solely so the output can carry auditable identifiers and market scope.

## Versioned scoring formula

Formula `strategy-ranking-formula-v1` has five equally visible components,
each bounded to `[0, 20]`. Values are rounded to eight decimal places.

* **Scientific:** `clamp(sample_size / 50, 0, 20)`.
* **Statistical:** `10 × clamp(stability_score, 0, 1) + 10 × clamp(parameter_sensitivity_score, 0, 1)`.
* **Backtest:** `5 × clamp(profit_factor or 0, 0, 2) + 5 × clamp(expectancy, 0, 1) + 5 × clamp(trade_count / 20, 0, 1)`.
* **Validation:** `10 × clamp(walk_forward_score, 0, 1) + 10 × indicator(TRUE OOS expectancy > 0)`.
* **Risk:** `20 / (1 + max(0, max_drawdown))`; a larger value means lower risk.

For eligible records, `composite_score = scientific + statistical + backtest
+ validation + risk`. Thus all weights and caps are public and fixed. There is
no learned model, metric-dependent weighting, parameter search, or profit-factor
optimization.

## Acceptance and deterministic positions

Only an `ACCEPTED` validation becomes `RANKED`. `REJECTED` and
`INSUFFICIENT_DATA` validations produce audit records with no position and a
zero composite score. Active records sort by descending composite score, then
strategy ID and validation ID. Positions begin at one. These explicit tie
breaks make repeated runs reproducible.

## Memory and restart behavior

`ResearchMemory` appends rankings to `strategy_rankings.jsonl`. It verifies the
persisted validation, strategy, trading-candidate, and pattern-effect identifier
chain. The ranking ID is the deterministic hash of `validation_id` plus
`ranking_version`; therefore the same pair is skipped after restart. A reused
ID with a different payload is rejected as a collision. Existing records are
never updated.

## Limitations

Version 1 uses only scalar facts already present in `ValidationReport`. Its
TRUE OOS component records the validation engine's result; ranking never reads
market data. It does not estimate correlations, portfolio fit, capacity,
regime-specific risk, or uncertainty beyond the reported stability measures.
Those concerns belong to later evaluation layers and require a new versioned
formula rather than silent changes to this one.
