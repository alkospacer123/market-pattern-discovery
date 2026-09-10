# Autonomous pipeline execution integration

## Previous limitation

The production multi-horizon runner persisted qualified `PatternEffect`,
`TradingCandidate`, and `StrategyCandidate` objects and then stopped. Although
`AutonomousTradingPipeline` already implemented the trading stages, the runner
never called it, so production runs could not create backtests, validation
reports, or rankings.

## Execution flow and orchestration point

After a bounded call to `MultiHorizonResearchRunner.run` finishes its research
cycles, the runner now calls the existing `AutonomousTradingPipeline.run`
exactly once. The resulting flow is:

`ResearchCell → Hypothesis → Evaluation → Evidence → PatternEffect →`
`TradingCandidate → StrategyCandidate → BacktestResult → ValidationReport →`
`StrategyRanking`.

There is no direct research-to-backtest route. The pipeline reads only
persisted `StrategyCandidate` objects as trading-engine inputs. It uses the
existing `BacktestEngine`, `ValidationEngine`, and `StrategyRankingEngine`; it
does not modify their scientific, simulation, validation, or ranking logic.
The production engine configuration uses fixed transaction cost `0.001` and
per-fill slippage `0.0005`, rather than selecting costs from observed results.

## Lineage, restart, and failures

`ResearchMemory` stores the three additional immutable registries in
`backtest_results.jsonl`, `validation_reports.jsonl`, and
`strategy_rankings.jsonl`. Each append checks its immediate parent lineage and
its deterministic identity. On restart, the pipeline loads those registries
and resumes at the first absent stage; an identical completed object is a skip,
not another JSONL event.

Each candidate's backtest and validation execute independently. A backtest
exception leaves its strategy intact and creates no downstream report. A
validation exception leaves its backtest intact and creates no ranking. A
ranking exception leaves all validations intact. Deterministic failure facts
are recorded once in `pipeline_failures.jsonl`.

## Multi-horizon and causal behavior

The data adapter loads precisely the strategy's symbol, execution timeframe,
and context timeframes. It preserves the profiles without substitution:

* SCALPING: M1/M5 execution with M15 context;
* INTRADAY: M5/M15/M30 execution with H1/D1 context;
* MEDIUM_TERM: H1/D1 execution with H1/D1 context.

Loader timestamps denote candle opens, so the adapter advances each timestamp
by the canonical timeframe duration before exposing it to trading engines.
Consequently, a candle enters the execution/context stream only at its close.
The data stays outside research memory, and the adapter retains only in-process
read-only-derived frames. No strategy definition is mutated and no parameter
search or profit-based selection is introduced.

## Validation results

The focused integration suite completed with 15 passing tests, including the
complete persisted chain, deterministic restart, all three isolated failure
stages, every configured horizon/timeframe profile, strategy immutability, and
the new production hand-off/close-availability adapter. The full repository
suite completed with 388 passing tests.

The requested fresh real-data Process A was also started for 20 cycles at
`/tmp/marketai_pipeline_execution_validation_001`. Research completed all 20
cycles and persisted 20 attempts/findings, 12 trading candidates, and 324
strategies. The existing backtest engine's current context-prefix simulation is
quadratic on the full M1 history; after more than five minutes it had completed
only one of 324 backtests. The run was stopped rather than reporting a false
successful audit. Process B was therefore not run, and this interrupted audit
cannot supply complete-chain or duplicate totals. This is an observed runtime
limitation of the unchanged engine, not a bypass or an optimization of the
research protocol.

The integration and deterministic fixture restart are verified, but the exact
two-process real-data acceptance run remains incomplete until the existing
engine can finish that workload under an appropriate execution window.
