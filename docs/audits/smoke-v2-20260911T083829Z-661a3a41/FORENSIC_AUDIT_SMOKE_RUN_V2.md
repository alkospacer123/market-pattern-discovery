# FORENSIC AUDIT v1 — SMOKE RUN V2

## Scope and safety controls

- Requested artifact bundle: `/workspace/market-pattern-artifacts/smoke-v2-20260911T083829Z-661a3a41/`
- Audit date (UTC): 2026-09-11
- Evidence policy: saved artifact bundle only.
- No research cycle, strategy generation, backtest, validation, optimization, or parameter search was run.
- No market data, including locked TRUE OOS 2025 data, was read.

## ARTIFACT INTEGRITY STATUS

**Status: BLOCKED — the requested artifact bundle is absent from the filesystem.**

The canonical absolute path does not exist. A filesystem lookup by the exact
bundle directory name also returned no match. Consequently none of the required
files could be opened:

| Required file | Status |
|---|---|
| `manifest.json` | Missing (bundle absent) |
| `source_commit.txt` | Missing (bundle absent) |
| `data_manifest.sha256` | Missing (bundle absent) |
| `hypotheses.jsonl` | Missing (bundle absent) |
| `strategies.jsonl` | Missing (bundle absent) |
| `signals.jsonl` | Missing (bundle absent) |
| `backtests.jsonl` | Missing (bundle absent) |
| `validations.jsonl` | Missing (bundle absent) |
| `rankings.jsonl` | Missing (bundle absent) |
| `strategy_candidates.jsonl` | Missing (bundle absent) |
| `executable_signal_definitions.jsonl` | Missing (bundle absent) |
| `backtest_results.jsonl` | Missing (bundle absent) |
| `validation_reports.jsonl` | Missing (bundle absent) |
| `strategy_rankings.jsonl` | Missing (bundle absent) |

SHA256 agreement, JSONL readability, declared-versus-observed record counts,
identifier references, and end-to-end lineage therefore cannot be verified.
No substitute run, repository fixture, market-data directory, or inferred value
was used because that would violate the bundle-only evidence constraint.

## Actual pipeline map

No evidence-backed object count can be reported.

| Stage | Count | Audit result |
|---|---:|---|
| Research Hypothesis | unknown | Source JSONL unavailable |
| Evaluation | unknown | Source JSONL unavailable |
| PatternEffect | unknown | Source JSONL unavailable |
| TradingCandidate | unknown | Source JSONL unavailable |
| StrategyCandidate | unknown | Source JSONL unavailable |
| ExecutableSignal | unknown | Source JSONL unavailable |
| BacktestResult | unknown | Source JSONL unavailable |
| ValidationReport | unknown | Source JSONL unavailable |
| Ranking | unknown | Source JSONL unavailable |

The requested chain cannot be reconstructed or tested for broken, orphaned, or
many-to-one lineage without the records and manifest.

## Direction and SHORT-bias analysis

LONG/SHORT percentages for PatternEffect, TradingCandidate,
StrategyCandidate, ExecutableSignal, and executed trades are unknown. The first
stage at which a directional imbalance appears cannot be located. Accordingly,
none of hypotheses A–E (research generation, PatternEffect interpretation,
StrategyBuilder, signal translation, or execution engine) is selected.

Assigning the bias to any stage without the bundle would be speculation. The
machine's near-aggregate SHORT exposure, mentioned in the task, is a claim to
test rather than sufficient evidence of where the bias originated. The
machine-readable blocked result is in `direction_bias_analysis.json`.

## Strategy inventory and performance

The asserted population of 54 strategies and 346,176 trades cannot be
independently verified. Strategy IDs, symbols, horizons, timeframes, direction,
signal and entry/exit logic, SL, TP, risk/reward, trade counts, win rate, profit
factor, expectancy, net result, drawdown, and holding duration are all unknown.

`strategy_performance_report.csv` contains the requested stable schema and no
data rows. Fabricating rows from the task's aggregate figures would incorrectly
attribute results to strategies.

### Best and worst strategies

TOP/BOTTOM 20 lists by profit factor, expectancy, net result, or drawdown
cannot be calculated. It is also not possible to determine whether any of the
54 asserted strategies were profitable or whether all had negative expectancy.

## Trading logic

Signal features, candle roles, levels, confirmation rules, execution price,
fixed or dynamic SL/TP, time exits, end-of-day exits, and realized risk/reward
cannot be recovered without the executable signal definitions, candidates, and
backtest records. See `trade_logic_report.md` for the per-strategy report status.

## Trade analysis

The following cannot be computed from the two aggregate values supplied in the
task:

- average gross/net PnL, commission, and slippage;
- winning/losing trade counts and average win/loss;
- average, median, and maximum holding duration;
- best and worst trades;
- maximum winning and losing streaks;
- LONG and SHORT trade counts or percentages.

The supplied aggregate PF `0.9402606696` and expectancy `-0.0031017290` are not
treated as bundle-verified. Even if accepted, they establish only that the
reported aggregate payoff was negative: they do not separate gross edge from
cost drag or diagnose entry, exit, or direction.

## Horizon analysis

Actual creation, candidate promotion, signal generation, backtest coverage, and
executed-trade participation for SCALPING, INTRADAY, and MEDIUM TERM are unknown.
Likewise, actual use of M1, M5, M15, M30, H1, and D1 cannot be verified. The
requested timeframe lists describe expectations, not evidence of participation.
See `horizon_forensic_report.json`.

## Why the aggregate result was negative

No defensible choice among causes A–G can be made. PF below 1 and negative
expectancy describe the outcome but do not identify its cause. Distinguishing
bad ideas, wrong side, poor entry/exit, insufficient edge, or transaction-cost
drag requires at least gross and net trade PnL, fees/slippage, direction, entry,
exit, and strategy lineage. Those records are unavailable.

## Ranking quality and diversity

Ranking eligibility, score inputs, tie-breaking, duplicate strategies, and
whether poor strategies were ranked cannot be checked. Counts of unique
concepts, signal types, horizons, and timeframes cannot be computed. Any claim
about ranking quality or diversity would be unsupported.

## Answers to the required questions

1. **What did the machine trade?** Unknown; trade records are unavailable.
2. **On which instruments?** Unknown.
3. **Which timeframes were actually used?** Unknown.
4. **Was there scalping?** Not verifiable.
5. **Was there intraday trading?** Not verifiable.
6. **Was there medium-term trading?** Not verifiable.
7. **What was the entry logic?** Unknown.
8. **What was the exit logic?** Unknown.
9. **What were SL/TP/RR?** Unknown.
10. **Why were almost all trades SHORT?** The premise and cause cannot be verified.
11. **Where did SHORT bias appear?** Unknown; no pipeline stage can be selected.
12. **Were any strategies profitable?** Unknown.
13. **Why was the overall result negative?** The supplied aggregates describe but do not diagnose it.
14. **What must be fixed before 20-cycle validation?** Restore or mount the exact immutable artifact bundle, then rerun this read-only audit. Do not begin validation until hashes, counts, lineage, causal candle timing, day/session boundaries, cost fields, directional propagation, ranking provenance, and horizon participation have all been verified from that bundle. This is an audit prerequisite, not a recommendation to alter or optimize trading logic.

## Required unblock condition

Make the requested directory available at the exact path, complete with all 14
listed files and without regenerating or modifying the run. The audit can then
perform streaming JSONL analysis and hash/lineage verification solely against
that immutable evidence.

# AUDIT BLOCKED

**Reason:** `/workspace/market-pattern-artifacts/smoke-v2-20260911T083829Z-661a3a41/` does not exist, so the mandatory artifact-only analysis has no admissible evidence source.
