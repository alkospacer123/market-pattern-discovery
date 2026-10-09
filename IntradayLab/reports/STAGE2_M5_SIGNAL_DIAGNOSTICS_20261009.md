# IntradayLab — independent 2023 M5 signal completeness and tick-economics diagnostic

Date: 2026-10-09 MSK. **STAGE2_M5_BASELINE_NEEDS_FIX_RESEARCH_COMPLETENESS**, NOT an accepted annual trade backtest.

**Provenance:** full immutable `IntradayLab/results/stage2_m5/signals.csv` retrieved by Git blob SHA `5e2a6ecc572b348d917c671ce4ae3c91a761a178` at PR #443 commit `0da11cf86169d5cedf3386549ebe244ca5204fd0`; `results.json` at the same commit. Exactly 7813 signal rows were independently parsed. Only derived 2023 data: no market-pattern-data source, no 2024 WF or 2025+ TRUE OOS, no real FINAM data access or order actions. No parameters/strategy changed. Split-by-comma is exact for these 21 fixed CSV columns (all 7,813 records have consistent width; no embedded commas). Integer tick calculations use the signed-decimal fixed-point price fields, never binary-float price comparisons.

## Independent reproduction of signal counts

Total 7813 signals, 7279 BLOCKED = **93.17%**, including 534 non-BLOCKED signals. Signal counts and blocked statuses for all eight runs independently match committed `results.json`. Other statuses are not promised exchange fills.

| Run | Signals | BLOCKED | Non-BLOCKED | Median shifted ATR/tick | Median stop/tick | Median take/tick | Median cap/tick | Take distance ≤2 ticks (pre-block) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| VWAP_MR_USDRUBF | 1464 | 1330 | 134 | 6.21 | 9.00 | 4.00 | 1.00 | 33/134 (24.63%) |
| VWAP_MR_CNYRUBF | 1055 | 1025 | 30 | 1.58 | 2.00 | 1.00 | 0.00 | 28/30 (93.33%) |
| VWAP_MR_GLDRUBF | 360 | 301 | 59 | 71.83 | 107.00 | 44.00 | 17.00 | 0/59 (0.00%) |
| VWAP_MR_IMOEXF | 60 | 56 | 4 | 6.54 | 9.00 | 2.50 | 1.00 | 2/4 (50.00%) |
| MOMENTUM_USDRUBF | 2621 | 2386 | 235 | 5.92 | 8.00 | 18.00 | 1.00 | 0/235 (0.00%) |
| MOMENTUM_CNYRUBF | 1309 | 1245 | 64 | 1.50 | 2.00 | 5.00 | 0.00 | 2/64 (3.13%) |
| MOMENTUM_GLDRUBF | 821 | 817 | 4 | 43.08 | 64.50 | 129.50 | 10.50 | 0/4 (0.00%) |
| MOMENTUM_IMOEXF | 123 | 119 | 4 | 4.50 | 6.00 | 14.00 | 1.00 | 0/4 (0.00%) |

Stop/Take/cap distances above are computed from **signal close**, not a future entry Open. ATR/tick medians are descriptive floating renderings from archived Decimal ATR; exact tick-rounded stop/take/cap distances and ≤2-tick eligibility are calculated by fixed-point integer division. CNY historical step 0.01 before 2023-09-27 19:00 MSK; later 0.001. No C1 component added beyond the existing one tick per executed side.

**Important independent correction to the earlier Stage 2 re-audit:** the previous report's percentages for “signal take-distance ≤2 ticks” do not reproduce against every non-BLOCKED signal under exact integer-tick comparison. The original report stated VWAP USD **20.1%** and VWAP CNY **76.7%**; the independently recomputed figures are **33/134 = 24.63%** and **28/30 = 93.33%**, respectively. For Momentum CNY the exact count is **2/64 = 3.13%**, rather than the prior 1.6%. This discrepancy changes the descriptive cost-feasibility evidence, **not** the original trades or the already-failing quality verdict. These are diagnostic counts, not optimized performance. VWAP CNY has 16 one-tick, 12 two-tick, and 2 more-than-two-tick target distances in the pre-block observations; two ticks is the full ordinary C1 cost of a completely filled round trip.

## Full-year 2023 *pre-known* reward/cost and price-grid feasibility (ALL signals, including blocked)

These are **signal-side theoretical distances**, not backtested profits, executions or independent trade opportunities. In particular, the 7,279 blocked signals stay blocked. For each signal, historical dated tick and rounded `signal_close` / frozen `stop` / `take` / `cap` were read from the immutable signal ledger; 2 ticks is the already-approved nominal **round-trip C1**, not a confirmed tariff. A prospective Take distance at or below two ticks leaves no positive nominal reward *from signal Close* after C1, before execution shift and any other uncertainty. A zero-tick adverse cap is restrictive but **not** logically a zero-fill guarantee (a later price may be equal or better). All recorded rounded levels were on the applicable historical tick grid.

| Frozen run | 2023 signals, including blocked | Take distance ≤2 ticks | 0-tick cap | Take minus C1 > Stop distance |
| --- | ---: | ---: | ---: | ---: |
| VWAP USD | 1,464 | 246 (16.8%) | 158 (10.8%) | **0** |
| VWAP CNY | 1,055 | **693 (65.7%)** | **691 (65.5%)** | **0** |
| VWAP GLD | 360 | 9 (2.5%) | 0 | **0** |
| VWAP IMOEX | 60 | 12 (20.0%) | 4 (6.7%) | **0** |
| Momentum USD | 2,621 | 0 | 292 (11.1%) | 2,621 |
| Momentum CNY | 1,309 | 11 (0.8%) | 633 (48.4%) | 1,163 |
| Momentum GLD | 821 | 0 | 0 | 821 |
| Momentum IMOEX | 123 | 0 | 34 (27.6%) | 121 |

The VWAP entries in the last column have **no pre-signal reward greater than their Stop distance plus the two ticks C1** under these frozen rounded levels; they could still have a positive expectancy if real winning probabilities and achievable fills support it, which has **not** been shown. These descriptive diagnostics make a *prospective* reward-vs-risk and minimum-cost margin gate a defensible **future separately frozen hypothesis**, not an automatic optimized threshold. For Momentum, favourable nominal reward/risk at decision time plainly did not produce positive closed-only PF in the accounted sample — investigate false breakouts, losses to Stop and the delayed execution model before selecting new ADX/ATR thresholds.

## Full-year signal frequency (four instruments, two independently counted strategies)

| 2023 month | Signals | Blocked | Blocked share |
| --- | ---: | ---: | ---: |
| 2023-01 | 501 | 79 | 15.77% |
| 2023-02 | 441 | 400 | 90.70% |
| 2023-03 | 442 | 442 | 100.00% |
| 2023-04 | 424 | 424 | 100.00% |
| 2023-05 | 453 | 453 | 100.00% |
| 2023-06 | 466 | 466 | 100.00% |
| 2023-07 | 576 | 551 | 95.66% |
| 2023-08 | 769 | 731 | 95.06% |
| 2023-09 | 695 | 695 | 100.00% |
| 2023-10 | 1021 | 1021 | 100.00% |
| 2023-11 | 949 | 941 | 99.16% |
| 2023-12 | 1076 | 1076 | 100.00% |

Signals in months with persistent unknown entry state **cannot** be relabelled as completed orders. October and December have 100% blocked signals even though source M5 bars exist: the observed disappearance of trade P&L is dominated by unreconciled order state, not an absence of signal opportunities.

## Run × month evidence matrix (all 96 rows)

Source data-coverage flag is distinct from the economic month-end mark. `PROVISIONAL_COMPLETE` refers only to existing conditional model mark, **not** real fill or independently validated positive return. `NO_COVERAGE` is not a zero-return month.

| Run | Month | Raw-window coverage | Missing slots | Signals | Blocked | Conditional model entry signals | Unknown order signals | P&L reliability |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| VWAP_MR_USDRUBF | 2023-01 | PARTIAL_COVERAGE | 7 | 116 | 0 | 42 | 0 | PROVISIONAL_COMPLETE |
| VWAP_MR_USDRUBF | 2023-02 | PARTIAL_COVERAGE | 5 | 104 | 86 | 4 | 1 | UNRESOLVED |
| VWAP_MR_USDRUBF | 2023-03 | PARTIAL_COVERAGE | 4 | 152 | 152 | 0 | 0 | UNRESOLVED |
| VWAP_MR_USDRUBF | 2023-04 | PARTIAL_COVERAGE | 6 | 104 | 104 | 0 | 0 | UNRESOLVED |
| VWAP_MR_USDRUBF | 2023-05 | PARTIAL_COVERAGE | 7 | 129 | 129 | 0 | 0 | UNRESOLVED |
| VWAP_MR_USDRUBF | 2023-06 | PARTIAL_COVERAGE | 4 | 107 | 107 | 0 | 0 | UNRESOLVED |
| VWAP_MR_USDRUBF | 2023-07 | PARTIAL_COVERAGE | 1 | 131 | 131 | 0 | 0 | UNRESOLVED |
| VWAP_MR_USDRUBF | 2023-08 | PARTIAL_COVERAGE | 109 | 116 | 116 | 0 | 0 | UNRESOLVED |
| VWAP_MR_USDRUBF | 2023-09 | PARTIAL_COVERAGE | 43 | 134 | 134 | 0 | 0 | UNRESOLVED |
| VWAP_MR_USDRUBF | 2023-10 | COVERED | 0 | 135 | 135 | 0 | 0 | UNRESOLVED |
| VWAP_MR_USDRUBF | 2023-11 | PARTIAL_COVERAGE | 1 | 143 | 143 | 0 | 0 | UNRESOLVED |
| VWAP_MR_USDRUBF | 2023-12 | COVERED | 0 | 93 | 93 | 0 | 0 | UNRESOLVED |
| VWAP_MR_CNYRUBF | 2023-01 | PARTIAL_COVERAGE | 113 | 95 | 65 | 13 | 1 | UNRESOLVED |
| VWAP_MR_CNYRUBF | 2023-02 | PARTIAL_COVERAGE | 94 | 72 | 72 | 0 | 0 | UNRESOLVED |
| VWAP_MR_CNYRUBF | 2023-03 | PARTIAL_COVERAGE | 204 | 70 | 70 | 0 | 0 | UNRESOLVED |
| VWAP_MR_CNYRUBF | 2023-04 | PARTIAL_COVERAGE | 185 | 51 | 51 | 0 | 0 | UNRESOLVED |
| VWAP_MR_CNYRUBF | 2023-05 | PARTIAL_COVERAGE | 152 | 62 | 62 | 0 | 0 | UNRESOLVED |
| VWAP_MR_CNYRUBF | 2023-06 | PARTIAL_COVERAGE | 152 | 64 | 64 | 0 | 0 | UNRESOLVED |
| VWAP_MR_CNYRUBF | 2023-07 | PARTIAL_COVERAGE | 119 | 83 | 83 | 0 | 0 | UNRESOLVED |
| VWAP_MR_CNYRUBF | 2023-08 | PARTIAL_COVERAGE | 150 | 106 | 106 | 0 | 0 | UNRESOLVED |
| VWAP_MR_CNYRUBF | 2023-09 | PARTIAL_COVERAGE | 90 | 94 | 94 | 0 | 0 | UNRESOLVED |
| VWAP_MR_CNYRUBF | 2023-10 | PARTIAL_COVERAGE | 2 | 120 | 120 | 0 | 0 | UNRESOLVED |
| VWAP_MR_CNYRUBF | 2023-11 | PARTIAL_COVERAGE | 9 | 133 | 133 | 0 | 0 | UNRESOLVED |
| VWAP_MR_CNYRUBF | 2023-12 | COVERED | 0 | 105 | 105 | 0 | 0 | UNRESOLVED |
| VWAP_MR_GLDRUBF | 2023-01 | NO_COVERAGE | 0 | 0 | 0 | 0 | 0 | NO_COVERAGE |
| VWAP_MR_GLDRUBF | 2023-02 | NO_COVERAGE | 0 | 0 | 0 | 0 | 0 | NO_COVERAGE |
| VWAP_MR_GLDRUBF | 2023-03 | NO_COVERAGE | 0 | 0 | 0 | 0 | 0 | NO_COVERAGE |
| VWAP_MR_GLDRUBF | 2023-04 | NO_COVERAGE | 0 | 0 | 0 | 0 | 0 | NO_COVERAGE |
| VWAP_MR_GLDRUBF | 2023-05 | NO_COVERAGE | 0 | 0 | 0 | 0 | 0 | NO_COVERAGE |
| VWAP_MR_GLDRUBF | 2023-06 | NO_COVERAGE | 0 | 0 | 0 | 0 | 0 | NO_COVERAGE |
| VWAP_MR_GLDRUBF | 2023-07 | PARTIAL_COVERAGE | 183 | 21 | 0 | 7 | 0 | UNRESOLVED |
| VWAP_MR_GLDRUBF | 2023-08 | PARTIAL_COVERAGE | 212 | 65 | 27 | 10 | 1 | UNRESOLVED |
| VWAP_MR_GLDRUBF | 2023-09 | PARTIAL_COVERAGE | 238 | 41 | 41 | 0 | 0 | UNRESOLVED |
| VWAP_MR_GLDRUBF | 2023-10 | PARTIAL_COVERAGE | 90 | 96 | 96 | 0 | 0 | UNRESOLVED |
| VWAP_MR_GLDRUBF | 2023-11 | PARTIAL_COVERAGE | 143 | 72 | 72 | 0 | 0 | UNRESOLVED |
| VWAP_MR_GLDRUBF | 2023-12 | PARTIAL_COVERAGE | 66 | 65 | 65 | 0 | 0 | UNRESOLVED |
| VWAP_MR_IMOEXF | 2023-01 | NO_COVERAGE | 0 | 0 | 0 | 0 | 0 | NO_COVERAGE |
| VWAP_MR_IMOEXF | 2023-02 | NO_COVERAGE | 0 | 0 | 0 | 0 | 0 | NO_COVERAGE |
| VWAP_MR_IMOEXF | 2023-03 | NO_COVERAGE | 0 | 0 | 0 | 0 | 0 | NO_COVERAGE |
| VWAP_MR_IMOEXF | 2023-04 | NO_COVERAGE | 0 | 0 | 0 | 0 | 0 | NO_COVERAGE |
| VWAP_MR_IMOEXF | 2023-05 | NO_COVERAGE | 0 | 0 | 0 | 0 | 0 | NO_COVERAGE |
| VWAP_MR_IMOEXF | 2023-06 | NO_COVERAGE | 0 | 0 | 0 | 0 | 0 | NO_COVERAGE |
| VWAP_MR_IMOEXF | 2023-07 | NO_COVERAGE | 0 | 0 | 0 | 0 | 0 | NO_COVERAGE |
| VWAP_MR_IMOEXF | 2023-08 | NO_COVERAGE | 0 | 0 | 0 | 0 | 0 | NO_COVERAGE |
| VWAP_MR_IMOEXF | 2023-09 | NO_COVERAGE | 0 | 0 | 0 | 0 | 0 | NO_COVERAGE |
| VWAP_MR_IMOEXF | 2023-10 | NO_COVERAGE | 0 | 0 | 0 | 0 | 0 | NO_COVERAGE |
| VWAP_MR_IMOEXF | 2023-11 | PARTIAL_COVERAGE | 402 | 4 | 0 | 1 | 1 | UNRESOLVED |
| VWAP_MR_IMOEXF | 2023-12 | PARTIAL_COVERAGE | 164 | 56 | 56 | 0 | 0 | UNRESOLVED |
| MOMENTUM_USDRUBF | 2023-01 | PARTIAL_COVERAGE | 7 | 212 | 0 | 48 | 0 | PROVISIONAL_COMPLETE |
| MOMENTUM_USDRUBF | 2023-02 | PARTIAL_COVERAGE | 5 | 211 | 188 | 6 | 1 | UNRESOLVED |
| MOMENTUM_USDRUBF | 2023-03 | PARTIAL_COVERAGE | 4 | 191 | 191 | 0 | 0 | UNRESOLVED |
| MOMENTUM_USDRUBF | 2023-04 | PARTIAL_COVERAGE | 6 | 208 | 208 | 0 | 0 | UNRESOLVED |
| MOMENTUM_USDRUBF | 2023-05 | PARTIAL_COVERAGE | 7 | 197 | 197 | 0 | 0 | UNRESOLVED |
| MOMENTUM_USDRUBF | 2023-06 | PARTIAL_COVERAGE | 4 | 246 | 246 | 0 | 0 | UNRESOLVED |
| MOMENTUM_USDRUBF | 2023-07 | PARTIAL_COVERAGE | 1 | 219 | 219 | 0 | 0 | UNRESOLVED |
| MOMENTUM_USDRUBF | 2023-08 | PARTIAL_COVERAGE | 109 | 269 | 269 | 0 | 0 | UNRESOLVED |
| MOMENTUM_USDRUBF | 2023-09 | PARTIAL_COVERAGE | 43 | 206 | 206 | 0 | 0 | UNRESOLVED |
| MOMENTUM_USDRUBF | 2023-10 | COVERED | 0 | 227 | 227 | 0 | 0 | UNRESOLVED |
| MOMENTUM_USDRUBF | 2023-11 | PARTIAL_COVERAGE | 1 | 211 | 211 | 0 | 0 | UNRESOLVED |
| MOMENTUM_USDRUBF | 2023-12 | COVERED | 0 | 224 | 224 | 0 | 0 | UNRESOLVED |
| MOMENTUM_CNYRUBF | 2023-01 | PARTIAL_COVERAGE | 113 | 78 | 14 | 15 | 1 | UNRESOLVED |
| MOMENTUM_CNYRUBF | 2023-02 | PARTIAL_COVERAGE | 94 | 54 | 54 | 0 | 0 | UNRESOLVED |
| MOMENTUM_CNYRUBF | 2023-03 | PARTIAL_COVERAGE | 204 | 29 | 29 | 0 | 0 | UNRESOLVED |
| MOMENTUM_CNYRUBF | 2023-04 | PARTIAL_COVERAGE | 185 | 61 | 61 | 0 | 0 | UNRESOLVED |
| MOMENTUM_CNYRUBF | 2023-05 | PARTIAL_COVERAGE | 152 | 65 | 65 | 0 | 0 | UNRESOLVED |
| MOMENTUM_CNYRUBF | 2023-06 | PARTIAL_COVERAGE | 152 | 49 | 49 | 0 | 0 | UNRESOLVED |
| MOMENTUM_CNYRUBF | 2023-07 | PARTIAL_COVERAGE | 119 | 76 | 76 | 0 | 0 | UNRESOLVED |
| MOMENTUM_CNYRUBF | 2023-08 | PARTIAL_COVERAGE | 150 | 116 | 116 | 0 | 0 | UNRESOLVED |
| MOMENTUM_CNYRUBF | 2023-09 | PARTIAL_COVERAGE | 90 | 102 | 102 | 0 | 0 | UNRESOLVED |
| MOMENTUM_CNYRUBF | 2023-10 | PARTIAL_COVERAGE | 2 | 244 | 244 | 0 | 0 | UNRESOLVED |
| MOMENTUM_CNYRUBF | 2023-11 | PARTIAL_COVERAGE | 9 | 213 | 213 | 0 | 0 | UNRESOLVED |
| MOMENTUM_CNYRUBF | 2023-12 | COVERED | 0 | 222 | 222 | 0 | 0 | UNRESOLVED |
| MOMENTUM_GLDRUBF | 2023-01 | NO_COVERAGE | 0 | 0 | 0 | 0 | 0 | NO_COVERAGE |
| MOMENTUM_GLDRUBF | 2023-02 | NO_COVERAGE | 0 | 0 | 0 | 0 | 0 | NO_COVERAGE |
| MOMENTUM_GLDRUBF | 2023-03 | NO_COVERAGE | 0 | 0 | 0 | 0 | 0 | NO_COVERAGE |
| MOMENTUM_GLDRUBF | 2023-04 | NO_COVERAGE | 0 | 0 | 0 | 0 | 0 | NO_COVERAGE |
| MOMENTUM_GLDRUBF | 2023-05 | NO_COVERAGE | 0 | 0 | 0 | 0 | 0 | NO_COVERAGE |
| MOMENTUM_GLDRUBF | 2023-06 | NO_COVERAGE | 0 | 0 | 0 | 0 | 0 | NO_COVERAGE |
| MOMENTUM_GLDRUBF | 2023-07 | PARTIAL_COVERAGE | 183 | 46 | 42 | 1 | 1 | UNRESOLVED |
| MOMENTUM_GLDRUBF | 2023-08 | PARTIAL_COVERAGE | 212 | 97 | 97 | 0 | 0 | UNRESOLVED |
| MOMENTUM_GLDRUBF | 2023-09 | PARTIAL_COVERAGE | 238 | 118 | 118 | 0 | 0 | UNRESOLVED |
| MOMENTUM_GLDRUBF | 2023-10 | PARTIAL_COVERAGE | 90 | 199 | 199 | 0 | 0 | UNRESOLVED |
| MOMENTUM_GLDRUBF | 2023-11 | PARTIAL_COVERAGE | 143 | 165 | 165 | 0 | 0 | UNRESOLVED |
| MOMENTUM_GLDRUBF | 2023-12 | PARTIAL_COVERAGE | 66 | 196 | 196 | 0 | 0 | UNRESOLVED |
| MOMENTUM_IMOEXF | 2023-01 | NO_COVERAGE | 0 | 0 | 0 | 0 | 0 | NO_COVERAGE |
| MOMENTUM_IMOEXF | 2023-02 | NO_COVERAGE | 0 | 0 | 0 | 0 | 0 | NO_COVERAGE |
| MOMENTUM_IMOEXF | 2023-03 | NO_COVERAGE | 0 | 0 | 0 | 0 | 0 | NO_COVERAGE |
| MOMENTUM_IMOEXF | 2023-04 | NO_COVERAGE | 0 | 0 | 0 | 0 | 0 | NO_COVERAGE |
| MOMENTUM_IMOEXF | 2023-05 | NO_COVERAGE | 0 | 0 | 0 | 0 | 0 | NO_COVERAGE |
| MOMENTUM_IMOEXF | 2023-06 | NO_COVERAGE | 0 | 0 | 0 | 0 | 0 | NO_COVERAGE |
| MOMENTUM_IMOEXF | 2023-07 | NO_COVERAGE | 0 | 0 | 0 | 0 | 0 | NO_COVERAGE |
| MOMENTUM_IMOEXF | 2023-08 | NO_COVERAGE | 0 | 0 | 0 | 0 | 0 | NO_COVERAGE |
| MOMENTUM_IMOEXF | 2023-09 | NO_COVERAGE | 0 | 0 | 0 | 0 | 0 | NO_COVERAGE |
| MOMENTUM_IMOEXF | 2023-10 | NO_COVERAGE | 0 | 0 | 0 | 0 | 0 | NO_COVERAGE |
| MOMENTUM_IMOEXF | 2023-11 | PARTIAL_COVERAGE | 402 | 8 | 4 | 0 | 1 | UNRESOLVED |
| MOMENTUM_IMOEXF | 2023-12 | PARTIAL_COVERAGE | 164 | 115 | 115 | 0 | 0 | UNRESOLVED |

**Run-month gate:** 32 NO_COVERAGE, 2 provisional complete, 62 unresolved, total 96 rows. Among 64 months with source data, only 2 provisionally complete; this is not a complete-year economic baseline. Full-year net profit, PF, positive-month share, losing streak and portfolio income are not established. Never “repair” this by resetting unconfirmed exposure, inventing an execution, or cutting the 2023 period.

Next priority: resolve the eight exact submitted-order target gaps using *external 2023 historical market/session/order evidence* before variant testing; otherwise retain year-long unknown exposure and no full PF. Separately compare C1-aware pre-known reward/stop/tick economics for a small, frozen later candidate, without manipulating the initial manifest.
