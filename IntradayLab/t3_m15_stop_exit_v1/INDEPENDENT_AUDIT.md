# Independent implementation audit — T3/M15 Stop & Exit v1

**Implementation audit PASS; external independent reviewer PENDING. GROSS_ONLY / COSTS_DEFERRED / NOT_LIVE_READY.**

The standard-library auditor is a separate implementation by the same author. It imports no experiment engine, research runner, pandas or TradingSystemLab. The only read-only reuse is PR #490's independent prefix parser, hash function and recursive exponential smoother. Feature arithmetic is reconstructed independently: daily ordinal H1 blocks, missing/incomplete block rejection, cross-day Wilder ATR and ADX, EMA75/slope, H1 regime and causal Donchian20 signals.

For each of the 32 instrument/version/mechanic replays, `simulate()` reconstructs favorable extrema from the survived post-entry path, independently chooses a monotone Stop from candidates, checks the old Stop first with adverse Open gaps, and simulates complete entry occupancy/re-entry. It never edits a saved trade or filters its outcome. An exit candle supplies no favorable threshold, new Stop or MFE. The independent path reconstruction differs from the primary incremental extrema engine.

Verified against complete raw 2023–2024 prefixes:

- 5,789 CLOSED records, all generated mechanical fields, including fixed initial risk, Stop, timestamps, labels, activation state and Gross R.
- Eight terminal OPEN states, no forced liquidation; direction, entry, initial/active Stop, extrema, activation time, updates and final quote/unrealized Gross R.
- 109,941 bar-by-bar Stop decisions, including exited bars, old Stop, activation, current proposal, next Stop, source and gap.
- 16,136 raw signal/occupancy/accepted-entry decisions.
- 2,888 central metric rows: pooled/instrument/annual/monthly/direction/monthly-direction, all PF/R/expectancy/counts, calendar signs, worst month, trade/month losing streaks, DD and top5/top10 removal sensitivities.
- 4,326 exact-entry lineage rows; all winner/loss change and original top5/top10 cohort aggregates.
- 40 November sensitivity rows, full R attribution and activation aggregates.
- All copied historical A6/A7 rows exactly against frozen #495; no A6/A7 execution.
- Pinned source bytes and all preregistered read-only reference files, ROADMAP, implementation and generated checksums.

Exact comparisons for identity, timestamps, categories and booleans. Absolute numeric tolerance **1e-8**; observed maximum numeric difference **5.4569682106375694e-12**. See [AUDIT_RESULTS.json](AUDIT_RESULTS.json) for per-field differences and all replay counts.

The primary runner separately reconciles all 1,442 original CLOSED records and both terminal OPEN against #490 and #495 before any S replay. All 19 #490 mechanical fields and all 39 common #495 gross-only fields match; original C1/net economics are excluded from this gross-only comparison. Exact sequence and prices are retained. [CONTROL_REPRODUCTION.json](results/CONTROL_REPRODUCTION.json).

Twenty causal unit tests ran before variant results. They cover LONG/SHORT, Stop-before-ratchet/activation, BE/LOCK next-candle activation, same-bar ambiguity, gaps, initial-risk immutability, both trail multipliers, terminal OPEN, occupancy/re-entry, intersession/weekend/year transitions, H1 gaps/prefix invariance and the future-OHLC ingestion guard. [TEST_RESULTS.txt](TEST_RESULTS.txt).

[REPEATABILITY.json](REPEATABILITY.json) compares the primary output with two fresh-process complete runs using **direct byte equality and SHA-256 for every generated file**, including source manifest, reconciliation, CLOSED/OPEN, all Stop/entry paths and reports. Presentation has a separate repeat certificate. [SCOPE_CHECK.json](SCOPE_CHECK.json) checks the new-directory-only diff and clean pinned data checkout. [ARTIFACT_SHA256.json](ARTIFACT_SHA256.json) inventories the complete review package.

These checks demonstrate agreement between implementations and deterministic outputs under the frozen historical OHLC model. They do not establish executable signal-Close fills, tick-safe continuous Stops, economic net profitability, market independence or a human audit. Closed-trade cumulative R is bookkeeping, not portfolio capital/mark-to-market return. 2024 is already exposed development data, not independent WF. No 2025+ OHLC analysis, extra mechanics, Optimization, Robustness, Walk Forward, TRUE OOS or LIVE was run.

**STOP for external review and the user's decision; Draft PR only, no merge or auto-merge.**
