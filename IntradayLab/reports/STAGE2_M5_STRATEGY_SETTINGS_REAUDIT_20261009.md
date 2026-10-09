# IntradayLab — Stage 2 M5: independent strategy/settings re-audit (2026-10-09)

**Verdict: NEEDS FIX. NOT a usable annual Baseline. Do not merge PR #443.** Research-only; TradingSystemLab, the real robot, other trees, market-pattern-data and protected 2024 WF / 2025+ TRUE OOS remain untouched.

**Source authority:** PR #443 at `dd12847b014932e7efc34ac8bb41e793af96db38`, its frozen manifest `IntradayLab/config/stage2_m5_baseline_v1.json`, implementation `IntradayLab/tools/m5_baseline.py`, full `signals.csv`, `trade_ledger.csv`, `metrics.csv`, `results.json`. The actual GitHub main before this documentation update is `f5dec0a73bf1273f9490502fbc0b9588f9315260`. No re-optimization, new fills or historical data retrieval occurred in this review.

## 1. Actual frozen settings, not recommended replacements

| Setting | VWAP Mean Reversion | Session Momentum |
| --- | --- | --- |
| Signal bars | M5 | M5 |
| ATR | simple mean of 12 shifted true ranges, 13 prior bars warmup | same |
| Signal | past close outside prior VWAP±1 ATR; current close re-enters band before VWAP | current close crosses highest high / lowest low of preceding 12 bars |
| Stop | 1.5 ATR from **signal close** | same |
| Take | decision-time approximated VWAP | signal close ±3 ATR |
| Max hold | 60 min | 90 min |
| Entry adverse cap | 0.25 ATR from signal close | same |
| Data availability | at least bar start +10 min | same |
| First scheduled entry | bar start strictly later than ready, nominal +15 min | same |
| C1 | one historical tick each executed side; two per round-trip | same |
| Missing expected execution bar | unknown possible fill; persistent latch blocks subsequent entries through end-2023 | same |

VWAP implementation is an OHLCV **typical-price** approximation, not trade-by-trade session VWAP. On any missing five-minute bar, features and weighted-VWAP accumulators reset; resulting later features are **contiguous-fragment VWAP**, not the same cumulative entire-session VWAP.

## 2. Critical research-coverage failure

Across **7,813** signal records, **7,279 (93.16%)** are `BLOCKED`, **6,032** would otherwise pass the pre-known level/time entry constraints, and only **147** conditional entry ledger records survive (**135** completely accounted, **12** unresolved). Eight more possible-entry orders are unknown, one per run. No eight-run annual full Net/PF can be reported. The first such unknown appears Jan/Feb for USD/CNY, July/August for GLD, November for IMOEXF. This explains 0 reported entries in most later months: it is **not** an observed lack of trading opportunities.

The missing-bar UNKNOWN must **not** be converted to a confirmed NONFILL, fake zero exposure or guessed fill. However its year-long latch makes this an **unusable continuous 2023 economic Baseline**, despite internal code/test correctness. Distinguish complete-year **signal-frequency diagnostics** from verified/conditional **trade P&L**. Do not reset live-like position state merely to manufacture more trades. If no externally justified resolution exists, full-year P&L remains unavailable: **FAIL annual acceptance**, not PASS.

### 2023 data coverage inside authorized daytime research windows, from committed results.json

| Symbol | Available 2023 months | Expected M5 slots | Missing slots | Missing % |
| --- | ---: | ---: | ---: | ---: |
| USDRUBF | 12 | 26,658 | 187 | 0.70% |
| CNYRUBF | 12 | 26,658 | 1,270 | 4.76% |
| GLDRUBF | 6 | 13,020 | 932 | 7.16% |
| IMOEXF | 2 | 3,570 | 566 | 15.85% |

**These are missing slots relative to a simplified expected daytime window, NOT proof of corrupted exports:** some may be genuine no-trade intervals / scheduled pauses. Classify by source, historical session evidence and adjacent OHLC without fetching 2024 or future prices.

## 3. Pre-block settings/unit-economics findings

Statistics below were independently calculated from actual pre-block `signals.csv` (non-BLOCKED signals), with the frozen 2023 tick grids. Medians are **descriptive**, not optimal settings or proof of profitability.

| Diagnostic | VWAP USD | VWAP CNY | Momentum USD | Momentum CNY |
| --- | ---: | ---: | ---: | ---: |
| Median shifted ATR in historical ticks | 6.17 | 1.58 | 5.92 | 1.50 |
| Median Stop distance from **signal close**, ticks | 9 | 2 | 8 | 2 |
| Median Take distance from **signal close**, ticks | 4 | 1 | 18 | 5 |
| Median adverse-cap distance after tick rounding, ticks | 1 | **0** | 1 | **0** |
| C1 complete round-trip cost, ticks | 2 | 2 | 2 | 2 |
| % signal take-distance ≤ 2 ticks | 20.1% | **76.7%** | 0% | 1.6% |

**Observed structural issues to investigate before performance selection:**
1. VWAP target reversion from the **signal close** frequently offers less upside than its **1.5 ATR** stop risk; CNY median target is **one tick vs two ticks round-trip C1**. No positive net reward at that median target unless a more favourable actual entry/reference price occurs. A favourable target near one tick cannot support a cost-inclusive strategy merely by tuning exits.
2. CNY early-2023 ATR is ~1.5 ticks and `0.25 ATR` entry cap rounds to zero tick for most signals. All nominal ATR ratios translate poorly to this discrete tick grid. Do **not** use today's post-2023-09 CNY 0.001 tick for Jan 2023.
3. The delayed +15-minute scheduled entry is not the signal close: actual payoff/risk, cap and fill/nonfill depend on later reference Open. Diagnose adverse cap vs closed-only attrition without peeking at that Open in signal formation.
4. Momentum USD: 54 completely accounted trades, **34 Stop**, 10 Take, 10 other exits; net PF ~0.770. CNY: 15 completely accounted, **12 Stop**, 2 Take, 1 other; net PF ~0.167. Check false breakouts / hold durations / stops and sensitivity only with bounded, predeclared variants — not PF-maximizing parameter sweeps.
5. VWAP USD closed-only 45 trades, 19 Stop, 22 Take, 4 other. Closed-only gross PF ~1.51 falls to ~0.86 after C1. Thus **C1 alone can erase a weak gross edge** in this sample; CNY VWAP gross PF ~0.08 is already adverse **before** C1.

NO claim is made that these strategies lose all year; partial known trades are not representative full-year evidence. Trading cadence target must be explicitly defined. The current `ROADMAP.md` says **20–60 trades/month aggregate across all four symbols**, not per symbol. The user's new request describes **1–3/day per instrument**. Record this new objective for next design review without treating any frequency target as a mandate to overtrade or sacrifice net profitability.

## 4. Corrective Stage 2 work order — one bounded research cycle

**A. Validate the backtest input/execution contract first.**
- Enumerate **all 2023-only** missing target bars and missing session slots by symbol/date/time; classify market closed / legitimate no-trade / suspect missing export / genuinely unknown. Require independent source evidence for any asserted nonfill or position resolution. Leave unknown exposure unknown otherwise.
- Review bar clock, historical sessions, reset/warm-up, volume denominators, tick grids (especially CNY switch), rounding, trigger conditions, entry delays, TTL, Stop-first, same-bar entry/exit, TP penetration, gap handling, funding and B−30/B−20/B−10. Independently test long and short with hand-calculated fixtures.
- Repair actual coding defects with minimal causal changes. **No forward-price/order-existence lookahead**, no invented entries or flat states. Do not retrospectively exclude hard periods for better PF.
- Provide per-calendar-month complete/partial/missing coverage, 2023 signals, rejected entries by reason, observed conditional fills, unresolved starts and their impact; include a separate full-year signal opportunity report without claiming those signals were executed.

**B. Recheck frozen settings before any change.**
- For each strategy/instrument/month: report median ATR/tick, entry cap after rounding, pre-known target/tick vs two-tick C1, stop/target risk-reward at signal **and** upon eligible observed execution, losses to stop vs exits by time, ambiguous bars, gross→C1→net.
- Explain why VWAP fragment reset and per-symbol tick-size distort indicators; test corrections as **separately versioned, explicitly labeled candidate variants**, never silently edit the original `stage2_m5_baseline_v1.json` or overwrite original ledger.

**C. Investigate limited, prejustified alternatives ONLY after A/B quality gates:**
1. **Cost/tick-aware VWAP MR candidate**, with a pre-known minimum potential target/net reward relative to C1, a coherent risk-to-reward bound and explicit tick rounding; no retrospective fill selection.
2. **Filtered M5 Session Momentum**, hypothesis: avoid low-quality 12-bar false breaks and too-tight ATR stops. If needed, **ADX/+DI/−DI** as a directional-strength candidate, as already proposed in separate PR #444; no mass grid or post-hoc ranking.
3. **Volatility Squeeze Breakout**, already predeclared in IntradayLab roadmap as the next alternate strategy. Do not start arbitrary unrelated indicators, ML or portfolio logic.
4. ATR-based stop/take/hold settings may receive a **small frozen prejustified variant comparison**, but no unconstrained fitting and no cherry-picking of January.

For each authorized new variant: immutable configuration before its result, 2023-only data, exact run matrix, C1, independent month/week/year reports, missing/UNRESOLVED and fill coverage, tests, SHA/provenance. No 2024 WF/2025+ OOS reads. Profit after C1 and stable trade count are **research acceptance goals, not guaranteed outcomes**; if absent, report FAIL/no viable candidate, not PASS.

**D. Quality gate prior to future merge/optimization:**
- 2023 coverage must support **meaningful valid out-of-sample-of-the-code-month comparisons within development history**, not just Jan/Feb. A whole-year rate/PF is not permitted if unknown execution prevents reconciliation.
- Require trade_count/month per instrument and combined, wins/losses, gross, one C1 only, net, PF, drawdowns and reason distribution; months with no coverage or a blocked latch are not zero-trade months.
- Independent check must verify research utility *as well as* code-level correctness. No premature PASS on deterministic SHA/test compliance.
- Only `IntradayLab/` may change. No edits to `TradingSystemLab`, robot, BBW, other projects or `market-pattern-data`. No merge in this task.

**Current status: `STAGE2_M5_BASELINE_NEEDS_FIX_RESEARCH_AND_SETTINGS`.** This is an audit and corrective-work specification only: no parameter optimization/backtest was run and no profitability certified in this document.
