# IntradayLab — Stage 2 M5 research completeness gate and corrective decision

Date: 2026-10-09 (MSK). **Verdict: STAGE2_M5_BASELINE_NEEDS_FIX_RESEARCH_COMPLETENESS.** This is a separate acceptance audit and corrective task, not a changed Baseline strategy, new optimization, completed annual backtest or Stage 3 authorization.

## Verified authority and boundaries

- GitHub main during source audit: `f5dec0a73bf1273f9490502fbc0b9588f9315260`; PR #443 latest examined head: `0da11cf86169d5cedf3386549ebe244ca5204fd0`; PR #444 head: `f33e236e1a4f69cd614bb77bd988ba2b6d3f153e`. Both PRs remain unmerged.
- Original immutable 2023 M5 Baseline manifest: `stage2_m5_baseline_v1.json`, SHA256 `7b3a1bd786cee3eca09111f906481a3ab38067c79ec9d0d0d0720c21710319ac`. Do not modify this manifest or original results.
- Eight runs: `VWAP_MR` and `MOMENTUM` × USDRUBF, CNYRUBF, GLDRUBF, IMOEXF. Research windows 10:00–14:00 and 14:05–18:50 MSK (March exception), M5 only, 2023 only. 2024 WF reserved; 2025+ TRUE OOS locked. None of their price data is required by this derived-artifact audit.
- One dated historical tick per filled entry/exit side (C1). CNYRUBF tick 0.01 until 2023-09-27 19:00 MSK, then 0.001. No real quantity/capital/GO or exchange-fill claims.
- GitHub audit has separately documented an earlier source-access incident: a reviewer fetched full immutable USD/CNY M5 files that physically included post-2023 records. No future-performance assessment was reported. This incident **cannot be characterized as zero future bytes read**; do not repeat it. The new gate reads only the committed 2023-derived results, verification and signal files.

## Why Stage 2 failed as research

| Diagnostic from original PR #443 artifacts | Result |
| --- | ---: |
| Generated signals | 7,813 |
| BLOCKED due to persistent unknown entry state | 7,279 (93.17%, rounded from 7,279/7,813) |
| Otherwise rule-eligible attempted entries among blocked | 6,032, **not filled trades** |
| Known conditional model entry ledger rows | 147 |
| Fully accounted conditional trades | 135 |
| Model trades with unresolved consequences | 12 |
| Unknown possible-entry orders | 8 |
| Distinct unresolved cases | 20 |
| Full annual Net/PF across eight runs | UNAVAILABLE |
| Trading/live authorization | NONE |

A missing scheduled OHLCV M5 bar **cannot** establish whether an already submitted model order was filled. One unknown order per run persists and correctly blocks later orders; **do not** manufacture a NONFILL, FLAT confirmation or fresh entry. The long blocking period makes the calculated closed-only PF an incomplete and highly selected subset, not valid full-year performance. Signal-frequency diagnostics can cover the year without any fabricated fills.

Recorded missing research-window slots relative to simplified approved windows: USD 187/26,658 (0.70%); CNY 1,270/26,658 (4.76%); GLD 932/13,020 (7.16%); IMOEX 566/3,570 (15.85%). Missing is **not automatically a broken export**: compare historical venue schedules/no-trade periods and missing target slots using authorized 2023-only evidence. USD/CNY 2023-08-31 remains absent. GLDRUBF M5 begins 2023-07-11; IMOEXF begins 2023-11-14. Their 2023 pre-listing months are `NO_COVERAGE`, not zero-return months. **A full 12-month 2023 observation for the four-instrument matrix is physically unavailable in the pinned source**: GLD contributes at most six months and IMOEXF at most two. Do not quietly use protected 2024 WF to complete a fabricated 2023-year panel or relax the universe without a separate roadmap decision.

### Eight exact missing planned-entry M5 slots (existing unknown_entries.csv)

The following are **order-target intervals**, not merely general gaps. All timestamps are MSK, 2023; outcomes remain unknown, with no fabricated C1/fill/P&L. Prioritize independent historical session and order-evidence reconciliation for these eight intervals before attempting an economic replay.

| Run | Planned entry bar start | Missing detected (t+10m) |
| --- | --- | --- |
| VWAP USD | 2023-02-02 15:40 | 2023-02-02 15:50 |
| VWAP CNY | 2023-01-06 17:15 | 2023-01-06 17:25 |
| VWAP GLD | 2023-08-17 16:00 | 2023-08-17 16:10 |
| VWAP IMOEX | 2023-11-30 17:20 | 2023-11-30 17:30 |
| Momentum USD | 2023-02-03 16:15 | 2023-02-03 16:25 |
| Momentum CNY | 2023-01-19 15:25 | 2023-01-19 15:35 |
| Momentum GLD | 2023-07-12 11:40 | 2023-07-12 11:50 |
| Momentum IMOEX | 2023-11-15 16:25 | 2023-11-15 16:35 |


### Independent monthly-coverage aggregation (existing 2023 results.json)

Of **96** run×calendar-month slots: **32** are `NO_COVERAGE` before GLDRUBF/IMOEXF initial history, **64** have some M5 source coverage, but just **2/64** retain a provisional `net_complete && model_flat_confirmed` month-end mark (January USDRUBF for the two strategies). The other **62/64** are unresolved/unproven at month-end. This independent aggregation uses committed `results.json` month-end marks and coverage; it does **not** independently retrieve the large `signals.csv` nor prove real fills. A complete-month mark is not proof of an independently validated profitable month. **This is the concrete missing statistical coverage**, not a justification to shorten the period.

### Frozen rule economics that justify the next investigation

ATR and breakout range = 12 *prior* M5 bars, warmup 13 bars; VWAP = approximate relative-volume-weighted typical price reset per research window/after gaps. The signal is causal. VWAP entry: re-enter 1 ATR band toward session-fragment VWAP; take at signal VWAP; stop at 1.5 ATR from signal close; 60m max hold. Momentum: break previous 12-bar extremes; target 3 ATR, stop 1.5 ATR; 90m max hold. Entry deterioration cap = 0.25 ATR; t+10m data availability, earliest scheduled later-bar entry nominal t+15m; fixed one-bar entry TTL. Stop-first, no entry-bar TP, TP penetration by one tick, adverse gap and B−30/B−20/B−10 retained.

Signals before the eight blocked-state transitions show VWAP CNY median target approximately **1 historical tick** versus the **2-tick** complete C1 expense; the earlier re-audit's 76.7% CNY two-tick figure is superseded by an independent exact signal-ledger recomputation: **28/30 (93.33%)** pre-block target distances ≤2 historical ticks. Its median 0.25 ATR entry cap rounds to **zero ticks** early in 2023. VWAP USD gross PF ~1.51 on 45 closed trades became ~0.86 after C1. Momentum USD had 34 Stops vs 10 Takes on 54 closed trades; Momentum CNY had 12 Stops vs 2 Takes on 15 closed trades. These are **descriptive pre-block/closed-only diagnostics**, not optimized settings or proof of a full-year loss.

| Fixed run | Closed-only accounted | Closed-only PF C1 | Full-year PF |
| --- | ---: | ---: | --- |
| VWAP_MR_USDRUBF | 45 | 0.860 | UNAVAILABLE |
| VWAP_MR_CNYRUBF | 10 | 0.000 | UNAVAILABLE |
| VWAP_MR_GLDRUBF | 10 | 0.476 | UNAVAILABLE |
| VWAP_MR_IMOEXF | 0 | N/A | UNAVAILABLE |
| MOMENTUM_USDRUBF | 54 | 0.770 | UNAVAILABLE |
| MOMENTUM_CNYRUBF | 15 | 0.167 | UNAVAILABLE |
| MOMENTUM_GLDRUBF | 1 | 0.000 | UNAVAILABLE |
| MOMENTUM_IMOEXF | 0 | N/A | UNAVAILABLE |

PF is **not** computed across mixed underlying price units. No profitability certification is possible.


### Independent conditional trade-ledger recheck — 2023 derived artifacts

Fetched immutable PR #443 blob records **`trade_ledger.csv` (147 rows)**, **`execution_events.csv` (1,008 rows)**, `unknown_entries.csv` (8 rows) and `metrics.csv` (120 rows). Cross-referenced the entire **7,813-row** signals ledger. For each conditional trade, independently checked the signal ID, planned vs actual entry target, strictly later than ready, acknowledgement not earlier than execution interval, signed gross = direction × (Exit−Entry), historical dated C1 one tick per side (including CNY grid transition), C1 entry + exit totals and closed-only net = gross − C1 when `MODELLED`. **0 detected mismatches across 147 trade rows** with fixed-point price comparisons; this verifies arithmetic and provenance links of already recorded model trades only. It does **not** verify exchange fills, unobserved intrabar paths or full-year performance.

Model ledger exit counts: **85 Stop, 40 Take, 4 Max-hold, 12 Session-flat, 4 Data-gap emergency, 2 Pending-entry-gap emergency**. All 8 unknown-entry order IDs appear with the corresponding unresolved status in the full signal ledger.

The two `PROVISIONAL_COMPLETE` run-month marks both belong to **January 2023 USDRUBF**, with **negative conditional model after-C1 outcome**: VWAP 42 fully accounted trades, model Net C1 **−0.24** (price units), PF **0.8563**; Momentum 48 fully accounted, model Net C1 **−0.78**, PF **0.7224**. These are not portfolio capital returns, and January source coverage is marked partial. All other source-covered run-months remain unresolved.

### Structural close-confirmation timing conflict (separate from missing bars)

At a session end B, the frozen runner first requests a routine close at B−20. With a zero additional delay, `next_slot(B−20)` schedules the fill at the **open of B−15**, but data/fill acknowledgement for that M5 bar is available only at **B−5** under the t+10m contract. The existing requirement is **confirmed flat by B−10**. Thus a first close requested at B−20 cannot be confirmed in time even with a perfect model fill. This independently explains why the corrected artifacts record 12 known-position B−10 breaches; it must not be suppressed with a fabricated earlier acknowledgement.

Corrective **research hypothesis only**: predeclare an earlier exit-request lead time (for example B−30 or earlier), and prove its feasibility against late/absent M5 delivery, weekends, other session boundaries and true nonfills before any replay. This would be a separately versioned execution-spec candidate, **not** an edit to the frozen original Baseline or a post-hoc performance rescue. Position remains unresolved whenever even the earlier schedule fails.

Independent all-signal and integer-tick evidence, including the 96 run-month matrix and discrepancies with the historical re-audit, is separately archived in [STAGE2_M5_SIGNAL_DIAGNOSTICS_20261009.md](STAGE2_M5_SIGNAL_DIAGNOSTICS_20261009.md). Original artifacts remain frozen.

## Executed corrective work (this separate stacked branch)

- Added `IntradayLab/tools/stage2_research_completeness_gate.py`: read-only evidence gate consuming exclusively the frozen manifest, `results.json`, `verification.json`, `signals.csv`. No OHLCV access or backtest execution.
- Cross-checks the frozen SHA-256, exactly eight declared runs, signal counts/status distribution, unknown orders and unresolved totals; independently checks closed-only gross − C1 = net in each run using Decimal. Also inspects **all 120 metrics.csv records** (8 YEAR, 16 DIRECTION, 96 MONTH), requires unique run/group/period keys, agreement of coverage and year closed-trade counts, and rejects a non-null full annual/monthly Net or PF in rows that remain unresolved. Independent inspection of those actual 120 published records found **zero** contradictions; this is not Python CLI execution.
- Generates all 96 run×calendar-month rows: expected/missing market slots, source coverage, signal counts, blocked counts, conditional model entries and explicit month-end P&L reliability from the existing month marks. `NO_COVERAGE`, provisional complete and unknown/unproven are distinct.
- Rejects an annual Net/PF supplied despite unresolved cases. It **cannot issue PASS automatically** even if all fills were resolved, because profitability, risk and month stability still need independent analysis.
- Ten synthetic unit tests are authored (original five plus two calendar close-timing and three metrics-CSV cases), but **Python execution of those tests and the complete CLI on the GitHub branch has not been verified**. The independent cross-check of all 7,813 signals and 147 conditional ledger entries was executed as a separate exact-data audit (not by invoking the Python gate). Do not claim a Python test PASS. Full-artifact execution/CI of the committed checker and a separate independent audit remain prerequisites to any technical acceptance. No parameter or prior artifact was edited.

**Invocation from the PR #443-based checkout**: `PYTHONDONTWRITEBYTECODE=1 python IntradayLab/tools/stage2_research_completeness_gate.py > stage2-completeness-audit.json` (capture outside protected baseline result tree). Execute `PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s IntradayLab/tests -p 'test_stage2_research_completeness_gate.py' -v`.

## Next bounded corrective actions, in order

1. **Restore research completeness honestly.** Classify each 2023-only missing scheduled target and session-gap as known closure, no-trade, export defect, or genuinely unknown. Require external historical execution evidence before resolving submitted-order uncertainty. If it cannot be resolved, preserve UNAVAILABLE annual P&L. Do not reset the latch just to inflate deal count.
2. **Investigate frozen signal economics independently from order fills.** Full 2023 month-by-month signal opportunity count, tick-aware VWAP potential payout vs C1, cap-rounding and ATR-in-ticks by old/new CNY tick grids, stop/target asymmetry, time-to-entry, adverse opening movement, missing-bar frequency, stop vs take vs time exit. Use only development 2023 and label all counterfactuals distinctly from trade results.
3. **Only then predeclare a very small set of candidate rules.** First: VWAP minimum *prospective* net reward/cost and tick-consistent cap/Stop/Take. Second: Momentum false-breakout filter hypothesis with optional ADX/+DI/−DI only if evidence warrants it; ATR bounded exits. Third: roadmap Volatility Squeeze Breakout as a separately authorized comparison if the first two cannot deliver. Do not launch a mass grid, optimize on PF alone, or silently modify the original manifest. PR #444 is documentation of possible future indicators, not Stage 3 execution authority.
4. **Re-evaluate for research acceptance.** Require independently reproducible full observed development coverage and month/year outcomes, sufficient non-overlapping opportunities across four assets (roadmap planning range 20–60 aggregate trades/month, not a quota), positive net expectancy/PF after C1, direction/session stability, losing months and drawdowns, fill/cost sensitivity. Genuine failure must remain FAIL. Only after an explicit independent audit can later stages begin.

**Freeze remains:** Stage 2 `STAGE2_M5_BASELINE_NEEDS_FIX_RESEARCH_COMPLETENESS`; PR #443/#444 **NOT MERGED**; no 2024 WF, 2025+ OOS, TradingSystemLab, active robot or other trees changed. No Stage 3, MTF, Optimization, LIVE or account-order testing authorized.
