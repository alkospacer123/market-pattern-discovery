# IntradayLab — approved methodology and independent architecture

## Prospective execution policy implemented — 2026-10-11

The common engine now supports explicitly selected `DATA_GAP_SKIP_V2` for new
versioned M5 studies, while `LEGACY_UNKNOWN` remains the default. ENTRY_NEXT_OPEN
and ENTRY_WAIT_ONE_BAR clocks are independent of this policy and unchanged.
Skipped entry Opens have no fill or day latch. Unverifiable opened-position
outcomes retain known entry evidence in a separate exclusion ledger, contribute
no closed economics, and block same-day re-entry. Independent later days use
explicit assumed, unproven FLAT. Reporting reconciles accepted fills with CLOSED
plus exclusions and discloses missing coverage and sample bias. The new API,
independent synthetic audit and frozen compatibility receipts are documented in
the [technical handoff](reports/DATA_GAP_SKIP_V2_TECHNICAL_HANDOFF.md).
This completes only the separate engineering task anticipated below; it changes
no frozen strategy, config, old journal or research lifecycle and starts no C or
Optimization. Draft PR only, no merge.

## Superseding user decision — 2026-10-11

**The initial positive-Baseline prerequisite for Optimization in the historical architecture below is superseded.** Preserve the common IntradayLab engine isolation, causality, research cost model and unchanged five-step **Baseline → Optimization → Robustness → Walk Forward (2024) → TRUE OOS (2025+)** lifecycle. Finish the current B task unchanged and separately authorized C / other Baselines, then optimize **every strategy family with sufficient audited fully resolved trades**, including earlier negative IntradayLab candidates. Publish consistent minimum-count and month-coverage eligibility rules before ranking. Search/fitting is deliberate on 2023; aim for after-C1 **net PF >= 2** with meaningful trade count, positive expectancy and monthly regularity, not a guarantee or a tiny-sample PF maximum. Keep all old artifact identities and results frozen, then freeze selected candidates before Robustness / reserved WF / locked OOS. Do not tune on WF/OOS.

The user requests **no UNKNOWN status in future ordinary trade ledgers**. Missing signal or execution M5: skip the entry and record a data-quality reason. After a modeled entry, missing exposure/exit data mean the outcome must be separately **excluded and auditable**, with entry evidence retained, no invented fill/flat/Stop/Take/P&L and no claim of complete continuous returns. Report excluded count/coverage and possible selection bias. This is a **future versioned implementation task**, not a retroactive edit of archived A_v1 or ongoing B. TradingSystemLab and the running robot remain READ-ONLY; see latest ROADMAP policy.

**Decision:** 2026-10-10. **Status:** USER APPROVED; the independent common Backtester is implemented and technically audited. Its first [canonical ORB A BASE 2023 Baseline](results/orb_a_base_2023_canonical_v1/Baseline_Report.md) is **INCONCLUSIVE**, with negative conditional C1 expectancy on known closures for every instrument (**NO ECONOMIC BASELINE PASS**); no Optimization advancement. See [core contract](core/README.md) and [validation receipt](results/orb_a_base_2023_canonical_v1/validation.json). This remains the canonical architectural and methodology decision for IntradayLab; previously frozen results remain unchanged.

## 1. Isolation is mandatory

IntradayLab adopts **methodology and structural patterns** from TradingSystemLab, but remains an entirely independent research and future trading project.

- TradingSystemLab is a **read-only design reference**. NEVER edit its files, strategies, configurations, datasets, results, research identities, deployments, or live robot. NEVER import any TradingSystemLab production/research module into IntradayLab.
- Store all new code, strategy rules, params, backtests, tests, reports and results inside `IntradayLab/` only. `market-pattern-data` is an independent pinned **read-only** source, with exact commit and input provenance.
- Future IntradayLab brokerage account, order authority, credentials, risk, capital, runtime state, kill switch and safety auditing are separate from TradingSystemLab. No shared broker permission or current robot state.
- The concurrently running **Draft PR #463** remains in progress on its own branch. This decision does not merge, rewrite, invalidate or reclassify that PR's old frozen results, nor interrupt its Codex task.

## 2. One simple, common IntradayLab Backtester

Build **one** independently implemented and tested IntradayLab historical research engine based on the tested structure (not imported code) of `TradingSystemLab/core/backtester.py`, `core/indicators.py`, loader, metrics, audits and reproducible result artifacts.

For each candidate, input is **strategy + frozen initial parameters + instrument + timeframe + development data**. The common engine owns:

1. Chronological market OHLCV validation, actual coverage, timestamp availability, gaps, frozen source provenance; no invented candles or OHLC, no future reads.
2. Causal indicators calculated with the *available preceding bar history* for warm-up (no arbitrary reset at daily opening). MTF context only if explicitly integral to a strategy, exclusively from completed and available higher-timeframe candles.
3. One standard execution/cost/trade ledger. For the **current M5 program**, signal after a completed M5; then **one whole subsequent M5 must close**; only then conditional order submission and model entry at next M5 interval Open. No legacy T10/T15/FAST, extra price confirmation or other delays unless explicitly instructed. Time assumptions are frozen before P&L. Individual new timeframes get their own explicit causal timing.
4. Simple position handling under the declared intraday contract; genuine unknown fills/exits remain unknown and are never given invented P&L. **Do not latch one UNKNOWN to block all independent subsequent research days**; report coverage, conditional flat-at-next-day assumptions and limitations separately. Do not report a continuous broker equity curve unless all required events are resolved.
5. Default research costs **C1: one historical tick per side**; optional C2 stress on **identical fills**. Report net PF in price units and in initial-risk R consistently, net expectancy R, Net R, max drawdown (when valid), win rate, monthly/instrument/direction breakdowns and concentration.
6. Deterministic `trades.csv`, `metrics.json`, month report and independent audit before classifying a candidate.

Do **not** mix historical strategy assessment with live brokerage safety. Unknown broker orders/positions, reconciliation, kill switch and fail-closed authorization belong in a **separate future production/runtime module**, never in the entire historical Baseline sample.

## 3. Exactly the TradingSystemLab research lifecycle

**Baseline → Optimization → Robustness → Walk Forward → TRUE OOS** — no additional methodological phases.

- **Baseline:** ONE strategy with justified fixed initial parameters; a complete declared historical window and unchanged cost/execution rules. Presently the 2023 development period with the four approved MOEX perpetual instruments where available, M5 as first execution timeframe. Produce full trade ledger and honest 12-month coverage, monthly net performance, direction/instrument splits, C1 PF and expectancy, Net R, risk and DD. **Do not require a 4-way BASE/ATR/MTF/combined experiment or any additional indicator unless it is intrinsic to that strategy.**
- **Optimization:** only after Baseline supplies credible positive **after-C1 expectancy** with enough known independent trades, reasonable monthly stability and no cost fragility. The research goal is **net PF ≥1.6, preferably >2**, supported by the sample and not a few winners. Optimization is the only stage for controlled tuning; no mass searches during Baseline.
- **Robustness:** assess a stable neighborhood of parameters, different instruments/months, costs and concentrated winners.
- **Walk Forward:** **2024** remains reserved and is not consumed in Baseline or optimization.
- **TRUE OOS:** **2025 onward locked** until all prior stage gates pass.

If the candidate is economically negative, preserve **NO ECONOMIC BASELINE PASS** and move to the next strategy; if data/outcomes are insufficient, mark **INCONCLUSIVE**, investigate the engineering problem without cherry-picking PF. Seek positive net **calendar months** as an important target, but never force or guarantee 12/12.

## 4. Operating order

1. **Historical prerequisite:** finish and independently audit the retest for **Draft PR #463**; do not interfere with its branch. The subsequent implementation uses only its frozen `9c65d03` A BASE parameters/ledgers as historical reference.
2. **Completed separate technical task:** shared standalone IntradayLab Backtester, contract tests, first canonical A BASE replay and independent implementation audit. All previous frozen studies remain untouched. The new task has its own branch and Draft PR; no Merge.
3. Connect candidate intraday strategies by strategy module/config; run Baseline first, advance sequentially only after approved evidence. Keep roadmaps and handoffs up to date.
4. All changes must be auditable from actual GitHub main, with reviewed diff. No TradingSystemLab changes, no LIVE authorization, no automatic Merge or unauthorized next research stage.

**Precedence:** this explicit user decision governs *future architecture and methodology* over historical recommendations or old experiment-specific constraints appearing in existing project reports. It does not retroactively alter prior results.
