# Strategy Builder v1

## Purpose and architecture

Strategy Builder v1 turns a scientifically qualified `TradingCandidate` into a
small set of unevaluated `StrategyCandidate` execution hypotheses. It does not
backtest, rank, select, or optimize them. The mandatory lineage is:

```text
ResearchCell → Hypothesis → Evaluation → Evidence → PatternEffect
             → TradingCandidate → StrategyCandidate
```

The builder accepts only a `TradingCandidate` whose status is
`READY_FOR_STRATEGY_SEARCH` and whose direction is `LONG` or `SHORT`. Direct
construction from a `PatternEffect` or `ResearchCell` is rejected. Every
strategy stores `source_trading_candidate_id`, market scope, hypothesis,
condition, family, and direction.

## Controlled definitions

Entry definitions are `CLOSE_ENTRY` (after the signal candle closes),
`BREAKOUT_ENTRY` (through the signal extreme), and `CONFIRMATION_ENTRY` (after
one confirmation candle). An M5 signal can therefore only trigger after the M5
candle is closed; the builder does not relax causal availability.

Risk definitions are `ATR_STOP`, `STRUCTURE_STOP`, and `FIXED_DISTANCE_STOP`.
Exit definitions are `TIME_EXIT`, `STATE_INVALIDATION_EXIT`, and
`SIMPLE_TARGET_EXIT`. Their v1 parameters are fixed definitions, not parameter
ranges. They contain no position sizing or performance-based selection.

## Bounded deterministic generation

For each input, the builder enumerates the Cartesian product of three entries,
three risks, and three exits: exactly 27 candidates at most. The strategy ID is
a deterministic hash of the source TradingCandidate ID, builder version,
schema version, and the three definitions. It is independent of profitability
metrics. Changing the builder version creates a distinct identity namespace.

For example, a `Si M1 SHORT` TradingCandidate describing qualified negative
conditional future return produces, among the 27 candidates, a strategy with
`BREAKOUT_ENTRY`, `ATR_STOP`, and `TIME_EXIT`, retaining the input candidate ID.

## Memory and restart

`ResearchMemory` appends strategies to `strategy_candidates.jsonl`. It requires
the source TradingCandidate to exist in the same memory, preventing lineage
bypass. Existing deterministic IDs are skipped rather than appended, so a
restart can safely regenerate the same set. A later TradingCandidate appends
its new strategies without changing earlier records.

Strategy creation does not read market data—including locked TRUE OOS 2025—and
does not use profit factor, expectancy, win rate, Sharpe ratio, target search,
or any other profitability criterion. Evaluation belongs to a later backtest
layer, where costs and slippage must be explicit.
