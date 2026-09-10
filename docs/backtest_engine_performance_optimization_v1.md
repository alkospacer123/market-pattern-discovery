# Backtest engine performance optimization v1

## Scope and safety constraints

This change is an implementation-only optimization of the existing
`StrategyCandidate -> BacktestResult` engine. It does not alter candidate
schemas, entries, stops, exits, costs, metrics, validation, ranking, or
discovery. Calendar year 2025 remains locked by the backtest engine. Source
market data is neither modified nor persisted.

## Bottleneck

The v1 simulator constructed a context prefix for every execution candle by
filtering every candle in every context timeframe. For `N` execution candles
and a context of comparable size, that repeated scan and allocation was
quadratic (`O(N²)`). This dominated M1 runs even when no signals fired.

## Optimization

`PreparedMarketData` validates and converts each timeframe once, then builds:

* a symbol-to-execution-position index;
* a timeframe-to-candle index;
* candle-close timestamp arrays;
* a causal context position for every execution observation; and
* reusable higher-timeframe lookup structures.

Each context position is produced by a monotonic two-pointer pass. Preparation
and simulation are therefore `O(N + C)` for one context containing `C`
candles. Callers evaluating multiple strategies against the same market data
may call `BacktestEngine.prepare(...)` once and pass the prepared object to
every run.

The prior simulator used a context prefix only for truth testing and to inspect
its final (most recent) candle. The optimized simulator supplies an empty list
or a one-element list containing exactly that same candle. No decision input
changes.

## Unchanged-behavior and causality proof

The regression oracle contains the previous prefix-scan implementation. The
equivalence test compares the complete `BacktestResult`, including identity,
trades, timestamps, prices, directions, PnL, drawdown, expectancy, and profit
factor. It passes with non-zero commission and slippage.

The alignment cursor advances only while
`context_close_time <= observation_close_time`. Tests cover M1, M5, H1, and D1
execution/index preparation and assert both that the selected candle is
observable and that the next candle is still unavailable. Existing TRUE OOS,
strict ordering, and candidate-immutability checks remain in force.

## Benchmarks

All figures below are wall-clock measurements in the repository environment;
they are indicative rather than a cross-machine performance guarantee.

### Isolated 20,000-observation benchmark

| Implementation | Runtime | Result ID | Trades |
|---|---:|---|---:|
| Reference prefix scan | 1.668195 s | `7c09f489...e25d23d7` | 0 |
| Prepared causal index | 0.193578 s | `7c09f489...e25d23d7` | 0 |

Improvement: **8.618x**.

### Controlled pipeline validation

Fresh memory: `/tmp/marketai_backtest_performance_validation_001`.

The run used 8,000 deterministic M1 fixture observations, M15 causal context,
fixed commission `0.01`, fixed per-fill slippage `0.005`, and all 27 reviewed
strategies mechanically produced from one candidate. The locked TRUE OOS data
was not read. Because repository source market data is intentionally absent,
the validation stage used a controlled lineage-preserving validator and must
not be interpreted as market-performance evidence.

| Metric | Result |
|---|---:|
| Reference pipeline runtime | 7.898667 s |
| Optimized pipeline runtime | 1.848597 s |
| Improvement | **4.273x** |
| StrategyCandidates | 27 |
| BacktestResults | 27 |
| ValidationReports | 27 |
| StrategyRankings | 27 |
| Duplicate backtest IDs | 0 |

A restart created zero additional backtests, validations, or rankings.

## Limitations

* Runtime varies with hardware, Python version, context density, and signal
  frequency; the regression benchmark checks a conservative improvement, not
  an exact duration.
* Preparation still validates and converts raw rows on each raw-data call.
  Maximum reuse requires explicitly passing one `PreparedMarketData` instance.
* The controlled pipeline run proves execution, persistence, lineage, ranking,
  and restart behavior. It is not a claim of trading profitability and does
  not substitute for an authorized market-data validation outside locked TRUE
  OOS.
