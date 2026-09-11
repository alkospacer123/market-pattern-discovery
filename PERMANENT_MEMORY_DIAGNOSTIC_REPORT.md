# Permanent Memory Diagnostic Report

## Scope and safety

This repair did **not** run research, a backtest, strategy generation, or read
market data (including locked TRUE OOS 2025). It inspected only filenames and
metadata already visible in the workspace.

## Initial-state inspection (2026-09-11 UTC)

The requested locations `/workspace/autonomous_runs/`,
`/workspace/autonomous_runs/executable_signal_validation_v2`, and
`/tmp/marketai_executable_signal_smoke_001` did not exist. Therefore no prior
run bundle in those locations was readable or recoverable.

A bounded search under `/workspace` for the six requested names found only:

| Path | Size | Logical records | Readable |
|---|---:|---:|---|
| `/workspace/market-pattern-discovery/config/unknown_universe_v1/manifest.json` | 135,163 bytes | 1 JSON document | yes |

No `backtest_results.jsonl`, `strategy_candidates.jsonl`,
`validation_reports.jsonl`, `strategy_rankings.jsonl`, or
`executable_signal_definitions.jsonl` was present. This is why the historical
SHORT bias and historically active horizons cannot be inferred safely.

## Where permanent memory now lives

The explicit default is `/workspace/market-pattern-artifacts/<run_id>/`. It is
outside `/tmp`, stable across independent processes, and documented. Persistence
across process termination is covered by a two-process test: Process A writes
and exits; Process B independently discovers, parses, hashes, and validates the
bundle. A later Codex task can audit a run by its stable path and must call the
verifier before trusting it. This assumes the platform preserves `/workspace`,
which is the environment's persistent workspace contract; no program can make
a deleted or externally reset workspace survive.

## Fail-closed audit readiness

Every bundle has all required lineage and stage files plus audit metadata,
direction bias, and horizon reports. The exporter atomically writes artifacts,
hashes them, reopens every JSONL record, validates counts and hashes, and only
then records `READY_FOR_AUDIT`. Any failure records `FAILED` and raises.

## SHORT bias

There is no surviving historical run, so **the location of the prior bias is
UNKNOWN rather than guessed**. For every future run,
`direction_bias_report.json` reports LONG/SHORT count and percentage at
PatternEffect, TradingCandidate, StrategyCandidate, ExecutableSignal, and
actual backtest-trade stages. Comparing adjacent stages identifies the first
stage where skew appears. Zero-record stages explicitly report 0%, not invented
evidence.

## Horizons

There is no surviving trading evidence, so no horizon can currently be claimed
to work or even to have traded. `horizon_report.json` records created, traded,
and missing execution timeframes for SCALPING (M1/M5, context M15), INTRADAY
(M5/M15/M30, context H1/D1), and MEDIUM TERM (H1/D1, context H1/D1). “Traded”
means a strategy has an actual persisted backtest, not merely a candidate.

## Forensic audit inventory

A verified run exposes source commit, data-manifest digest, seed, ZERO
LOOK-AHEAD/TRUE-OOS declarations, canonical hypotheses, strategies, executable
signals, backtests (including trades and costs recorded by the engine),
validations, rankings, per-file hashes/counts, full strategy definitions,
trade diagnostics, pipeline funnel counts, direction attrition, and horizon
coverage. Source market data is never copied into the repository or artifact
bundle.
