# TradingSystemLab project context

## Authority and purpose

This file describes the repository state; it is not a new research result.
TradingSystemLab is the repository's deterministic, fixed-risk research domain
for independently specified trend systems T1–T3 and range-reversal systems
R1–R3.  It covers baseline reproduction, explicitly authorized bounded
optimization, robustness, chronological walk-forward evaluation, TRUE OOS
validation, multi-timeframe (MTF) research, execution/cost audits, and portfolio
construction.  The implementation is split conceptually into a **TREND ENGINE**
(`strategies/trend/`, T1–T3) and a **RANGE ENGINE** (`strategies/range/`, R1–R3).
The current corrected Baseline uses only the trend-engine T2 and T3 strategies;
the existence of range implementations or artifacts does not make them part of
that matrix.

## Canonical methodology authority

**Every new timeframe must use the original H1 research cycle and frozen H1
strategy identities as its sole methodological authority:** **Baseline →
Optimization → Robustness → Walk Forward → TRUE OOS**.  A timeframe must pass
each stage independently; no intermediate phase or result from another
timeframe may substitute for one of these five stages.  Later M1/M5/M15/M30/H4/
D1 implementations and MTF work are historical evidence, not alternative
templates.  Failed or superseded attempts remain immutable provenance but do
not control future methodology.

### Methodological source versus current research expansion

The **methodological source** is the original H1 cycle and frozen H1 candidate
provenance. The **current research expansion** is T2/T3 × Si/CNY/GD/BR/MIX/NG ×
M30/H1: 2 strategies × 6 instruments × 2 timeframes = **24 Baseline runs** over
the declared development interval 2020-01-01 through 2024-12-31. TRUE OOS is
locked from 2025-01-01 onward. Expanding instruments, timeframes, and history is
research coverage, not a methodological change, and does not restore the old
Si/CNY-only H1 universe. Actual source availability can begin later (the
historical matrix records later starts for CNY and NG) and must be disclosed in
run/data-quality artifacts.

## Identity generations

The identities must not be conflated:

1. **Original H1 baseline / current corrected Baseline identity.** The frozen
   strategy sources identify T2 as `T2_Trend_Pullback_Continuation_v1.0` with
   default `max_initial_stop_atr = 3.0`, and T3 as `T3_MTF_Trend_v1.0` with
   default `ema_period = 100`.  These baseline defaults, the original H1 cycle,
   and its provenance are authoritative for the corrected Baseline rerun.
2. **Frozen post-Optimization H1 candidates.** The original Phase 3.3 registry
   names `T2_candidate_v1` (`T2-0007-608dc87d09f1`) and `T3_candidate_v1`
   (`T3-0014-0050d828c1a8`).  Their candidate parameters include 2.5 and 75,
   respectively.  They are downstream frozen H1 candidates, not evidence that
   those values were original Baseline defaults.
3. **Historical v2 Phase 1 identity.** `baseline_v2.py` independently applied
   those 2.5/75 values to its rejected/unaudited baseline matrix and recorded:

| Name / implementation ID | Strategy source SHA-256 | v2 parameter hash | Frozen v2 overrides |
|---|---|---|---|
| T2 / `T2_Trend_Pullback_Continuation_v1.0` | `376df085cfda85eefccb31343aad40ed4fbb1078f1314496472a3a4ac9507774` | `2b0494cdd24bfbfa8ce7d657d6f83d1408f07b9f565d38d093dec5b4856e3c00` | EMA 20/50/200; ADX threshold 20; confirmation 3; impulse distance 0.5 ATR; maximum initial stop 2.5 ATR; trailing 3 ATR |
| T3 / `T3_MTF_Trend_v1.0` | `840dd3b2cda43fa00259445cd0a22ace6d82e677f4c793028ccc8126f9ad9a8c` | `938b6b3b78f680010115a204b9a49e7eef962db119f4ea121e388c00741920ba` | EMA 75; ADX threshold 20; ATR average 20; breakout 20; stop 2 ATR; trail 3 ATR |

The hashes remain authoritative only for the historical v2 runs.  They do not
define the corrected Baseline.  Do not silently replace one generation's
identity with another or invent a new parameter set.

Earlier artifacts also use candidate labels such as `T2_candidate_v1`,
`T3_candidate_v1`, and timeframe-specific variants.  Their identities and
eligibility belong to their own manifests; they must not be silently treated as
the v2 matrix above.

## Implemented scope

The v2 matrix is T2/T3 × `Si`, `CNY`, `GD`, `BR`, `MIX`, `NG` × M30/H1.  Its
declared development interval is 2020-01-01 through 2024-12-31, although the
audited files show CNY begins 2022-04-21 and NG begins 2020-02-03.  Other
committed, independent generations contain USDRUBF/CNYRUBF research on M1, M5,
M15, M30, H1, H4, and D1 and true MTF combinations H1→M15, H1→M30, and H4→H1.
Presence in the tree means “supported by a recorded workflow,” not “validated”
or “currently selected.”

The current cycle intentionally freezes `FROZEN_TICK_SIZE = 0.001` for every
instrument through all five canonical stages.  Instrument-specific tick-size
work is not a prerequisite and may occur only later as a separately authorized
audit/recalculation branch; it must not rewrite current or historical results.

For T3 in the corrected matrix, the original causal higher-context principle is
adapted deterministically: H1 execution consumes context only from complete
consecutive 4×H1 blocks, and M30 execution consumes context only from complete
consecutive 4×M30 blocks. Incomplete blocks are not emitted, aggregation cannot
cross trading-day boundaries, and future fill/look-ahead is prohibited. This is
causal construction within Baseline, not a new phase or optimization.

Validated historical work is immutable evidence with its own code, manifest,
ledger, metrics, classification, and provenance.  New research must receive a
new, explicit identity and repeat the applicable lifecycle.  It may not rewrite
an earlier verdict or use later diagnostics to retroactively select a candidate.

## Current v2 lifecycle state

The accepted current cycle has completed **Phase 1 Baseline**, **Phase 2
Optimization**, **Phase 3 Candidate Selection / Freeze**, and **Phase 3
Robustness**. The final artifact-only Phase 2 audit verified 82 bounded OAT
configuration studies and classified T2/M30, T2/H1, T3/M30, and T3/H1 as
`ROBUST_PLATEAU`. This is not a performance ranking and no strategy/timeframe is
declared superior.

The immutable registry freezes T2/M30 `T2_M30_candidate_v2`, T2/H1
`T2_H1_candidate_v2`, T3/M30 `T3_M30_candidate_v2`, and T3/H1
`T3_H1_candidate_v2` before validation. The freeze is anchored at merge
`ff0db54b35544086f4265c303b1018d57d3849e7`. Phase 3 Robustness consumed those
identities unchanged and classified T2/M30 `ROBUST_READY`, T2/H1 `BORDERLINE`,
T3/M30 `ROBUST_READY`, and T3/H1 `ROBUST_READY`. T2/H1 records the factual
`INSTRUMENT_DEPENDENT` flag; no replacement was selected. **Phase 4 Walk
Forward** is the next permitted stage. TRUE OOS 2025+ remains sealed, and no
Walk Forward or TRUE OOS has been executed for these candidates. Any parameter
change requires an earlier research stage and a new identity.

## Evaluation and execution contract

- Results are evaluated in fixed-risk multiples (`R`); the ledgers distinguish
  gross R, cost R, and net R.  Position sizing uses the initial stop and the
  configured fixed-risk portfolio.  PF is a reported metric, not an optimization
  objective to chase.
- Signals and indicators may use only information observable at that instant.
  Candle timestamps are close timestamps; a candle is unavailable before it
  closes.  Higher-timeframe context must be based on fully closed candles and
  aligned without future fill.  Rolling/session features must respect their
  documented day boundary.
- Input ordering, trade IDs, result ordering, tie-breaking, serialization, and
  reruns must be deterministic.  Manifests should bind strategy/config hashes,
  source provenance, date bounds, costs, and relevant artifact hashes.
- Market data is external, read-only, and must not be copied into this repository.
  Results must identify the input paths/ranges and record enough hashes to audit
  the admitted data.  The current v2 audit identifies missing source hashes as a
  defect, not permission to omit provenance.
- Calendar year 2025 is locked **TRUE OOS**.  It must not be read during
  ingestion, feature engineering, discovery, optimization, ranking, selection,
  or candidate freeze.  TRUE OOS is accessed only by its preauthorized phase and
  cannot be used to retune a failed or borderline system.
- Target leakage, look-ahead, favorable-subset selection, omitted configured
  costs, and silent strategy changes are prohibited.  Validation reproduces the
  frozen strategy; a logic change creates a new identity and requires a new
  lifecycle.

## Domain boundary

TradingSystemLab is not the repository's BBW pattern-discovery domain and is not
Round Level / Touch Optimization research.  Similar indicator names do not make
features, candidates, thresholds, results, or OOS evidence interchangeable.
Do not ingest or copy artifacts across those domains.  The repository-level
separation is defined in `../research_domains.md`; if that file is absent in a
checkout, the explicit prohibitions in this document and `README.md` still
apply.

## Evidence map

The statements above derive from `README.md`, `baseline_v2.py`,
`strategies/trend/`, `strategies/range/`, `core/portfolio.py`,
`core/data_loader.py`, `multitimeframe/`, `true_oos/`, and the manifests and
reports below `results/`.  Current defects and conflicts are recorded in
`CURRENT_STATE.md`, not resolved by this context summary.
