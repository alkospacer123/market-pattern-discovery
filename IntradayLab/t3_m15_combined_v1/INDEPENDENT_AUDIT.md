# Independent implementation audit — T3/M15 Combined v1

**Algorithmic audit PASS; external independent human reviewer PENDING. GROSS_ONLY / COSTS_DEFERRED / NOT_LIVE_READY.**

The auditor is a separate standard-library implementation by the same author. It imports no primary experiment engine/research/diagnostics, pandas or TradingSystemLab. Its only immutable reuse is #490's independent timestamp-guarded prefix parser, hashing and recursive exponential smoother. It independently rebuilds daily ordinal H1 blocks, rejects incomplete/gapped blocks, computes Wilder ATR/ADX, EMA75/slope, ATRMean20, H1 regime, prior breakout20 and causal signals.

It implements strict A6 and A7 comparisons independently and performs 48 complete causal replays (six variants × two versions × four instruments). Each replay has its own position occupancy and same-Close re-entry. Post-entry extrema are reconstructed from the survived path rather than incrementally reused from the primary engine. Candidate Stops are chosen independently; the old Stop and adverse Open are settled before favorable extrema or activation. Initial risk remains fixed and new S1 Stops act on the next actual observed bar. No trade journal is combined or retrospectively edited.

Raw permitted 2023–2024 prefixes verified against saved outputs:

- 7,447 CLOSED records, all generated mechanical fields, features, Gross R and activation/Stop chronology.
- 12 terminal OPEN positions, including direction, entry, initial/active Stop, fixed risk, accumulated extreme, activation time, update counts and last quote/unrealized R. No forced liquidation.
- 151,669 bar-by-bar Stop decisions, including exited candles, initial risk, active Stop, gap, favorable path, activation, proposal and next Stop.
- 24,204 raw-signal entry decisions, including the A6/A7 operands and predecessor availability, filter passes/failures, occupancy, accepted entries and reason labels.
- 4,332 central rows across overall/yearly/monthly/instrument/direction/monthly-direction reports, every PF/R/count/calendar/drawdown/concentration/streak field.
- 60 November 2024 sensitivity rows, including removal R/PF/drawdown and positive months.
- 7,210 CONTROL-based trade lineage rows and all original winner/loss, top5/top10, Gross R attribution and activation summaries.
- 8,021 component-reference lineage rows; 180 >=2R component cohort summaries, 38,556 component metric comparisons, 180 frequency/occupancy rows and 180 frequency comparisons.
- All 39 generated artifacts against SHA-256, pinned sources, original research/ROADMAP checksums and frozen executable-code checksums.

Identity, booleans, categories and timestamps match exactly. Absolute numeric tolerance is **1e-8**; the maximum observed difference is **5.4569682106375694e-12**. Detailed field maxima and all 48 replay counts are in [AUDIT_RESULTS.json](AUDIT_RESULTS.json); process output is in [AUDIT_LOG.txt](AUDIT_LOG.txt).

Before any C1/C2 execution, the primary runner reproduces all common CLOSED and terminal OPEN fields of CONTROL (1,442 CLOSED), A6 (1,023), A7 (1,300) and S1 (1,407) against immutable #495/#496 journals; each has two terminal OPEN. CONTROL is separately reconciled to #490's mechanical fields and #495's common fields, excluding original net/cost economics. All diffs are empty. [REFERENCE_REPRODUCTION](results/REFERENCE_REPRODUCTION.json) lists fields, counts, reference hashes and numeric maxima. Frozen raw-signal paths for all four and Stop paths for CONTROL/S1 are also reproduced: [REFERENCE_PATH_REPRODUCTION](results/REFERENCE_PATH_REPRODUCTION.json). #495 did not save A6/A7 Stop paths; their new full paths are verified by the independent replay instead.

Twenty symmetric causal synthetic tests passed before market results. They cover exact allowed scope, signal/exit-candle extrema exclusion, initial Stop before 1R, threshold equality, no retrospective exit, immutable risk, no Stop loosening, gaps/touches, terminal OPEN, session/weekend/year state, occupancy/re-entry, both trail multipliers, strict/missing A6/A7 predecessors, existing-position management after a filter failure, raw future-OHLC boundary, incomplete/gapped H1 and prefix invariance. [TEST_RESULTS](TEST_RESULTS.txt).

Two additional fresh processes repeat the entire primary replay and reports, comparing **direct bytes plus SHA-256 for every generated file and the hash manifest itself**. Presentation repeatability and scope/code/source guards are separately certified. [REPEATABILITY](REPEATABILITY.json), [PRESENTATION_REPEATABILITY](PRESENTATION_REPEATABILITY.json), [SCOPE_CHECK](SCOPE_CHECK.json), [ARTIFACT_SHA256](ARTIFACT_SHA256.json).

This audit establishes deterministic agreement under the frozen historical OHLC execution model. It is not an independent human review, market independence, executable Close-fill proof, tick-safe Stop proof or net-profitability validation. Closed R is risk-unit bookkeeping, not portfolio capital/MTM return. Both 2023 and 2024 are development-exposed. The external reviewer remains pending, and the Draft PR is stopped for that review. No Merge or Auto-Merge.
