# Backtest Engine v1

## Architecture and lineage

`BacktestEngine` is the evaluation-only continuation of the governed lineage:

`TradingCandidate → StrategyCandidate → Trade simulation → BacktestResult`.

It accepts one immutable `StrategyCandidate`; it neither creates nor changes a
strategy and contains no ranking, parameter search, optimization, or winner
selection. The result retains `strategy_id`. Its ID is a deterministic hash of
that ID, the caller-supplied data version, and the engine version.

## Causal market data and multiple timeframes

Input is either an execution-candle iterable or a mapping keyed by timeframe.
Every candle timestamp denotes its close/availability time, must be timezone
aware, and must be strictly increasing. Entries and open trades do not cross a
calendar trading-day boundary. The strategy's execution timeframe is
selected explicitly and every declared context timeframe is required. At a
signal decision, context is filtered to candles whose close time is no later
than the signal close. Thus an unfinished higher-timeframe candle is never
visible. The normal combinations (M1/M5 with M15, M5/M15/M30 with H1/D1, and
H1/D1) are data-driven rather than hard-coded. Calendar 2025 TRUE OOS is locked
by default; disabling that guard is an explicit validation-stage decision.

## Entries, risk, and exits

`CLOSE_ENTRY` fills at the next candle open, after the signal candle is known.
`BREAKOUT_ENTRY` scans forward for the first causal crossing of the signal high
for LONG or low for SHORT. `CONFIRMATION_ENTRY` requires the following candle
to close in the trade direction and fills after its close.

Stops are computed only from information available by entry. `ATR_STOP` uses
prior true ranges, `STRUCTURE_STOP` uses the signal low/high, and
`FIXED_DISTANCE_STOP` uses the declared price distance. Stop handling is
conservative: when a stop and another exit are possible in the same candle,
the stop wins. `TIME_EXIT`, `STATE_INVALIDATION_EXIT`, and
`SIMPLE_TARGET_EXIT` respectively close after a fixed number of bars, when the
declared state ceases to hold, or at a fixed target. An open terminal position
is closed on the final candle.

## Costs and metrics

`CostModel` makes fixed round-trip commission and per-fill slippage mandatory
and explicit. Gross PnL is the before-cost move. Net PnL applies adverse entry
and exit slippage plus commission. Reports contain gross profit/loss, net
result, after-cost profit factor (undefined when there is no net loss), expectancy, win
rate, maximum closed-trade equity drawdown, extremes, and average holding bars
and elapsed time.

## Persistence and restart

`ResearchMemory` appends canonical results to `backtest_results.jsonl`. It
requires the referenced strategy already be present, reloads complete trades,
and treats an identical deterministic ID as an idempotent skip. A conflicting
payload under the same identity is rejected, so process restarts cannot create
duplicates.

## Limitations

Version 1 models one unit, one position at a time, fixed price-unit costs,
bar-level OHLC fills, and no partial fills or gaps beyond adverse slippage.
Intrabar ordering is intentionally conservative. It evaluates supplied signals
and simple equality-based market state fields; signal generation, portfolio
sizing, data ingestion, optimization, and strategy selection remain separate.
