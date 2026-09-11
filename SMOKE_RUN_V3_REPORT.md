# Autonomous Trading Machine Smoke Run v3

## Final status

**SMOKE RUN V3 PASS** — **PERSISTENCE TEST PASS**. The verified bundle is
`/workspace/market-pattern-artifacts/smoke-v3-20260911T105729Z-23bc0a7/` and is
`READY_FOR_AUDIT`. No forensic audit was performed; the next stage is
**FORENSIC AUDIT v1**, reading only this bundle.

## 1. Launch parameters and provenance

| Field | Value |
|---|---|
| Cycles / budget / seed | `5 / 1 / 35` |
| Source commit | `23bc0a7d659807834852187ffa122734caef5e4e` |
| Data-manifest SHA-256 | `b09833a20259aafd980d06c2990811bf2db977e91156bb3600bfc032596ca617` |
| Bundle created | `2026-09-11T12:00:25.474904+00:00` |
| Pipeline duration | `3777.546387 s` (62 min 57.546 s) |
| Peak RSS | `948844 KiB` (926.61 MiB) |
| TRUE OOS 2025 | Not accessed (`false` in manifest) |

The production multi-horizon runner used the existing cost model, slippage,
strategy generator, risk/exit rules, and fixed seed. There was no parameter or
PF search.

## 2. Pipeline funnel

| Stage | Records |
|---|---:|
| Research hypotheses | 5 |
| Scientific findings | 5 |
| Pattern effects | 2 |
| Trading candidates | 2 |
| Strategy candidates | 54 |
| Executable signals | 54 |
| Backtests | 54 |
| Validation reports | 54 |
| Rankings | 54 |

Every cycle planned, evaluated, and recorded exactly one hypothesis. The run
continued through ranking rather than stopping at research.

## 3. Trading diagnostics

| Metric | Aggregate |
|---|---:|
| Total trades | 346,176 |
| LONG / SHORT trades | 0 / 346,176 |
| Trade-weighted win rate | 29.265460% |
| Profit factor | 0.9402606696 |
| Expectancy per trade | -0.0031017290 |
| Net result | -1073.744142859 |
| Maximum individual-strategy drawdown | 34.7600000001 |
| Trade-weighted average holding time | 616.583818 s |

The bundle's `audit_metadata.json` contains the required definition and trade
diagnostics for each of the 54 strategies, including direction, entry/exit,
SL, TP, risk/reward, LONG/SHORT counts, PF, expectancy, net result, drawdown,
and average holding time.

## 4. Direction bias

| Stage | LONG | SHORT |
|---|---:|---:|
| PatternEffect | 0% | 100% |
| TradingCandidate | 0% | 100% |
| StrategyCandidate | 0% | 100% |
| ExecutableSignal | 0% | 100% |
| Backtest trades | 0% | 100% |

The first observable SHORT bias appears at PatternEffect. Downstream stages
preserve it; they do not introduce it.

## 5. Horizon participation

| Horizon | Expected execution | Context | Created/traded | Missing |
|---|---|---|---|---|
| SCALPING | M1, M5 | M15 | M1 / M1 | M5 |
| INTRADAY | M5, M15, M30 | H1, D1 | none / none | M5, M15, M30 |
| MEDIUM TERM | H1, D1 | H1, D1 | none / none | H1, D1 |

These are observed scheduler outcomes from the bounded five-cycle production
run, not manually selected horizons.

## 6. Persistent artifact bundle

The bundle contains `manifest.json`, source commit and data-manifest bindings,
all three diagnostic JSON documents, all six primary pipeline JSONL streams,
and the five additional provenance streams: research attempts, knowledge
records, scientific findings, trading candidates, and strategy candidates.
The manifest inventories SHA-256 and record counts for every artifact.

## 7. Independent Process B verification

After Process A exited, a separate Python process received only the persistent
storage root. It called registry/latest discovery, found the run without a
supplied run ID, reopened the manifest, recomputed every hash, parsed every
JSONL row, and independently matched all manifest record counts.

**PERSISTENCE TEST PASS**. Therefore the run status remains
`READY_FOR_AUDIT`; otherwise this report would declare the run failed.
