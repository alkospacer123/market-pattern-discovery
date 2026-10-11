# IntradayLab — HIGH_LOW_CLUSTER B4/B7/B10 final handoff

**Completed: exactly three fixed 2023 Baselines. Draft PR only; STOP.**

Actual GitHub origin/main `8db73e6338bc5b89eda385e21167e22c74e5a299` equals the supplied base. [PR #474](https://github.com/alkospacer123/market-pattern-discovery/pull/474) MERGED (2026-10-11 11:50:09 MSK), merge SHA `8db73e6338bc5b89eda385e21167e22c74e5a299`. Existing ENTRY_NEXT_OPEN reused unchanged.

All three pre-P&L configs/code/auditor/tests/manifest frozen together at `e969f85f85c59dc03e3c88b35ea7ba5ea1f4f296`. Final PR head SHA is recorded in the PR description and chat after committing this handoff (a document cannot contain its own Git commit SHA).

## Verification

496 full IntradayLab unittest PASS, including 20 new B scenarios; no changes to common core or existing tests. Pre-P&L 2023 technical feasibility: 363588 independently compared construction fields, no trade paths or historical P&L.

| Model | Independent audit | Checked fields | Byte repeats | Deterministic files/repeat |
|---|---|---|---|---|
| B4 | PASS | 823403 | 2 | 20 |
| B7 | PASS | 408930 | 2 | 20 |
| B10 | PASS | 250152 | 2 | 20 |

Separate raw batch partition/slice/forward-path/CSV arithmetic oracle; no strategy, Backtester, production loader or production metrics as expected results. External human reviewer signoff has not been obtained.

All six old default-mode shared Baselines (canonical ORB, Level Rejection, R16, R17, Swing Pullback, Trend Pullback) plus A_v1 have byte-identical economic artifacts and independent audit PASS. Replay provenance may record current core hashes; frozen original configs and archived files are untouched.

The first verification completed all six B repeats but the old ORB regression could not read its historical #463 CSV from the locally available Git history. Fetching pinned commit `9c65d03aae117c6d88bbb4e6186f6a4fbb6b73ec` resolved access. The unchanged frozen validator was rerun in fresh scratch directories and completed PASS; no code/config/trade output was amended.

## Conditional economics after model C1

The table is known CLOSED-only evidence. UNKNOWN includes both unresolved filled paths and possible entries with unknown Open. Full annual PF/Net/DD remain null. Instruments are never pooled in price units.

| Model | Instrument | Detected | Signals | Fills | Known refusals | CLOSED | UNKNOWN | PF R | PF price | Gross R | C1 R | Net R | E[R] | + / − months |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| B4 | CNYRUBF | 2985 | 1967 | 425 | 1522 | 319 | 126 | 0.420 | 0.355 | 2.700 | 184.000 | -181.300 | -0.568 | 1/11 |
| B4 | GLDRUBF | 125 | 88 | 13 | 70 | 12 | 6 | 0.909 | 0.750 | 4.467 | 5.867 | -1.400 | -0.117 | 2/3 |
| B4 | IMOEXF | 175 | 115 | 14 | 90 | 9 | 16 | 0.412 | 0.333 | -2.083 | 5.067 | -7.150 | -0.794 | 0/1 |
| B4 | USDRUBF | 1819 | 1467 | 556 | 909 | 549 | 9 | 0.558 | 0.559 | 7.083 | 288.667 | -281.583 | -0.513 | 1/11 |
| B7 | CNYRUBF | 1979 | 1211 | 318 | 876 | 217 | 118 | 0.465 | 0.462 | 33.617 | 125.700 | -92.083 | -0.424 | 1/11 |
| B7 | GLDRUBF | 10 | 7 | 2 | 5 | 2 | 0 | 0.000 | 0.000 | -2.000 | 1.167 | -3.167 | -1.583 | 0/2 |
| B7 | IMOEXF | 24 | 15 | 4 | 9 | 4 | 2 | 1.712 | 1.750 | 4.250 | 2.067 | 2.183 | 0.546 | 1/0 |
| B7 | USDRUBF | 377 | 305 | 125 | 179 | 123 | 3 | 0.487 | 0.462 | -8.900 | 66.133 | -75.033 | -0.610 | 3/9 |
| B10 | CNYRUBF | 1285 | 806 | 250 | 539 | 164 | 103 | 0.396 | 0.361 | 11.600 | 93.500 | -81.900 | -0.499 | 1/10 |
| B10 | GLDRUBF | 5 | 4 | 0 | 4 | 0 | 0 | — | — | 0.000 | 0.000 | 0.000 | — | 0/0 |
| B10 | IMOEXF | 2 | 2 | 1 | 1 | 1 | 0 | 0.000 | 0.000 | -1.000 | 0.667 | -1.667 | -1.667 | 0/1 |
| B10 | USDRUBF | 82 | 65 | 35 | 30 | 34 | 1 | 0.220 | 0.261 | -13.800 | 18.700 | -32.500 | -0.956 | 1/9 |

B4, B7 and B10 each: **INCONCLUSIVE for full Baseline evidence; NO ECONOMIC BASELINE PASS is demonstrated.** Every nonempty known cohort has negative expectation except B7 IMOEX: +2.183R on only four closures (PF R 1.712, PF price 1.750), which is INSUFFICIENT_EVIDENCE. B10 GLD has no model fills and is INCONCLUSIVE. No winner is chosen.

## Why losses and refusals occur

Buffer 1 tick plus favorable entry cap 4 ticks implies accepted Stops of only 3–5 ticks. C1 is 40–66.7% of initial risk; FULL_NET_C1_R=3 requires gross Take 17–23 ticks. Stops are structural, never widened.

B4 USD gross +7.083R minus C1 288.667R = net −281.583R; B4 CNY gross +2.700R minus 184.000R = −181.300R. B7 CNY +33.617R minus 125.700R = −92.083R; B10 CNY +11.600R minus 93.500R = −81.900R. These cases lose their small gross edge to C1. B7/B10 USD are already gross-negative.

B4 USD: 408 Stop /65 Take /8 Time /68 Session Flat exits. B4 CNY: 171 Stop /13 Take /70 Time /65 Session Flat. B7 CNY: 88 Stop /5 Take /65 Time /59 Session Flat; B10 CNY: 69 Stop /4 Take /41 Time /50 Session Flat. Stop losses dominate; CNY frequently fails to reach Take before time/session closing. Full gross/cost/net attribution by exit and holding bounds is in every metrics.json and Baseline_Report.md.

Accepted USD/CNY mean Open-minus-signal-Close displacement is about −0.011 to +0.176 tick in the rebound direction. The small mean does not establish that earlier signal timing would fix the strategy; rejected impulsive entries and incomplete paths remain separate. GLD B4 mean is −9.692 ticks on a tiny filled cohort, indicating returns toward the boundary before Open, not a profitable executable Close counterfactual. No Close-oracle run was added.

B4 all refusal/diagnostic reasons: `{"AMBIGUOUS_BOTH_SIDES": 342, "CLOSE_AT_BOUNDARY": 1125, "ENTRY_MORE_THAN_4_TICKS_FROM_CLUSTER": 525, "MISSING_EXECUTION_BAR": 38, "OPEN_WRONG_SIDE_OF_CLUSTER": 25, "POSITION_BUSY": 503, "SESSION_LIMIT": 101, "STOP_ABOVE_12_TICKS": 97, "STOP_BELOW_3_TICKS": 608, "UNKNOWN_POSITION_BLOCK": 732}`.

B7 all refusal/diagnostic reasons: `{"AMBIGUOUS_BOTH_SIDES": 306, "CLOSE_AT_BOUNDARY": 546, "ENTRY_MORE_THAN_4_TICKS_FROM_CLUSTER": 108, "MISSING_EXECUTION_BAR": 20, "OPEN_WRONG_SIDE_OF_CLUSTER": 4, "POSITION_BUSY": 245, "SESSION_LIMIT": 37, "STOP_ABOVE_12_TICKS": 7, "STOP_BELOW_3_TICKS": 310, "UNKNOWN_POSITION_BLOCK": 358}`.

B10 all refusal/diagnostic reasons: `{"AMBIGUOUS_BOTH_SIDES": 218, "CLOSE_AT_BOUNDARY": 279, "ENTRY_MORE_THAN_4_TICKS_FROM_CLUSTER": 26, "MISSING_EXECUTION_BAR": 17, "OPEN_WRONG_SIDE_OF_CLUSTER": 2, "POSITION_BUSY": 129, "SESSION_LIMIT": 23, "STOP_ABOVE_12_TICKS": 3, "STOP_BELOW_3_TICKS": 189, "UNKNOWN_POSITION_BLOCK": 202}`.

CLOSE_AT_BOUNDARY consumes a formed construction without signal; AMBIGUOUS_BOTH_SIDES rejects both. STOP_BELOW_3_TICKS / STOP_ABOVE_12_TICKS reject actual-Open risk. ENTRY_MORE_THAN_4_TICKS_FROM_CLUSTER rejects chasing; OPEN_WRONG_SIDE_OF_CLUSTER rejects wrong-side Open. POSITION_BUSY / UNKNOWN_POSITION_BLOCK are execution-state gates; SESSION_LIMIT preserves intraday closing. MISSING_EXECUTION_BAR creates UNKNOWN possible entry, and MISSING_EXPOSED_BAR creates UNKNOWN path with blank P&L. A reason follows fixed precedence and may coexist with other failed constraints.

## Comparison with frozen A_v1

USD A expectancy −0.345R is higher than B4 −0.513, B7 −0.610 and B10 −0.956. CNY A −0.592R is slightly lower than B4 −0.568, B7 −0.424 and B10 −0.499; all remain negative. GLD A +18.200R on nine closures versus B4 −1.400R on twelve, B7 −3.167R on two, B10 no fills. IMOEX A −11.317R on thirteen closures; B7 positivity on four does not establish an advantage. Different signal/reset grammars and overlapping B episodes prevent a significance claim.

Increasing N sharply reduces detected events and closures; it produces no consistently positive after-C1 expectancy. Boundary-touch effects are inconsistent: B4 USD three touches lose less than two, CNY does not show the same effect. B10 CNY four touches have +1.400R /30 closures, PF 1.079, below the research goal; this diagnostic does not authorize a filter.

Round versus ordinary levels both lose on USD/CNY in every model. Positive tiny subsets (B4 GLD ROUND_NEAR three closures; B7 IMOEX ORDINARY_FAR three) are insufficient. Fixed grids and all group tables are in the comparison report. CNY ROUND_NEAR uses a dated one-tick distance, so its price radius changes with the historical tick schedule; no post-results threshold adjustment.

## Calendar months

Each cell is conditional known Net R. NO_COVERAGE before inception is not a zero trading return. Individual monthly reports retain unknowns, no-trade months and completeness.

### CNYRUBF

| Month | B4 Net R | B7 Net R | B10 Net R |
|---|---|---|---|
| 2023-01 | -24.783 | -17.983 | -10.833 |
| 2023-02 | -11.750 | -5.650 | -15.783 |
| 2023-03 | -18.433 | -3.750 | -6.500 |
| 2023-04 | 0.417 | 7.333 | 7.383 |
| 2023-05 | -7.350 | -6.983 | -11.217 |
| 2023-06 | -20.333 | -5.750 | -9.267 |
| 2023-07 | -9.583 | -18.500 | -10.267 |
| 2023-08 | -20.700 | -26.383 | -14.533 |
| 2023-09 | -17.767 | -6.167 | -7.983 |
| 2023-10 | -4.333 | -1.033 | -1.500 |
| 2023-11 | -28.717 | -4.150 | 0.000 |
| 2023-12 | -17.967 | -3.067 | -1.400 |

### GLDRUBF

| Month | B4 Net R | B7 Net R | B10 Net R |
|---|---|---|---|
| 2023-01 | NO_COVERAGE | NO_COVERAGE | NO_COVERAGE |
| 2023-02 | NO_COVERAGE | NO_COVERAGE | NO_COVERAGE |
| 2023-03 | NO_COVERAGE | NO_COVERAGE | NO_COVERAGE |
| 2023-04 | NO_COVERAGE | NO_COVERAGE | NO_COVERAGE |
| 2023-05 | NO_COVERAGE | NO_COVERAGE | NO_COVERAGE |
| 2023-06 | NO_COVERAGE | NO_COVERAGE | NO_COVERAGE |
| 2023-07 | 0.000 | 0.000 | 0.000 |
| 2023-08 | -1.500 | 0.000 | 0.000 |
| 2023-09 | 4.500 | 0.000 | 0.000 |
| 2023-10 | 3.700 | 0.000 | 0.000 |
| 2023-11 | -4.500 | -1.500 | 0.000 |
| 2023-12 | -3.600 | -1.667 | 0.000 |

### IMOEXF

| Month | B4 Net R | B7 Net R | B10 Net R |
|---|---|---|---|
| 2023-01 | NO_COVERAGE | NO_COVERAGE | NO_COVERAGE |
| 2023-02 | NO_COVERAGE | NO_COVERAGE | NO_COVERAGE |
| 2023-03 | NO_COVERAGE | NO_COVERAGE | NO_COVERAGE |
| 2023-04 | NO_COVERAGE | NO_COVERAGE | NO_COVERAGE |
| 2023-05 | NO_COVERAGE | NO_COVERAGE | NO_COVERAGE |
| 2023-06 | NO_COVERAGE | NO_COVERAGE | NO_COVERAGE |
| 2023-07 | NO_COVERAGE | NO_COVERAGE | NO_COVERAGE |
| 2023-08 | NO_COVERAGE | NO_COVERAGE | NO_COVERAGE |
| 2023-09 | NO_COVERAGE | NO_COVERAGE | NO_COVERAGE |
| 2023-10 | NO_COVERAGE | NO_COVERAGE | NO_COVERAGE |
| 2023-11 | 0.000 | 0.000 | 0.000 |
| 2023-12 | -7.150 | 2.183 | -1.667 |

### USDRUBF

| Month | B4 Net R | B7 Net R | B10 Net R |
|---|---|---|---|
| 2023-01 | -29.200 | -5.900 | -5.067 |
| 2023-02 | -28.550 | -1.817 | -2.867 |
| 2023-03 | -42.500 | -16.250 | -2.833 |
| 2023-04 | -26.133 | -10.167 | -2.433 |
| 2023-05 | 10.783 | -9.333 | 0.000 |
| 2023-06 | -29.700 | 6.333 | -3.167 |
| 2023-07 | -36.950 | 1.933 | -1.667 |
| 2023-08 | -13.500 | 3.067 | 0.000 |
| 2023-09 | -21.417 | -9.567 | -4.667 |
| 2023-10 | -28.250 | -6.883 | 0.600 |
| 2023-11 | -26.367 | -17.150 | -9.900 |
| 2023-12 | -9.800 | -9.300 | -0.500 |

## Coverage and protected trees

Pinned read-only source `f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8`, 104795 M5 rows in four verified exact 2023 prefixes (5833704 bytes per complete input load). Zero source price bytes 2024+; 2024 WF and 2025+ TRUE OOS remain reserved/locked. GLD begins 2023-07-11, IMOEX 2023-11-14; CNY tick 0.01→0.001 from 2023-09-27 19:00 MSK.

| Instrument | Complete / incomplete / pre-inception days | Missing M5 slots |
|---|---|---|
| USDRUBF | 224/30/0 | 187 |
| CNYRUBF | 82/172/0 | 1270 |
| GLDRUBF | 5/119/130 | 932 |
| IMOEXF | 2/32/220 | 566 |

553 preexisting IntradayLab files and 3303 repository files outside IntradayLab match the protected manifest. TradingSystemLab diff empty; live robot/settings/configs/results unchanged. Source checkout clean and same HEAD. All changes are additions inside IntradayLab; A_v1 and other frozen results are untouched. Core files are byte-identical to base.

## Artifacts and next action

[Unified comparison and A/B/round/touch/overlap tables](../results/high_low_cluster_b4_b7_b10_comparison_v1/HIGH_LOW_CLUSTER_B4_B7_B10_COMPARISON.md). [Full added-file list](../results/high_low_cluster_b4_b7_b10_comparison_v1/changed_files.txt).

[B4 Baseline_Report](../results/high_low_cluster_m5_2023_b4_v1/Baseline_Report.md); config, signals, rejected_entries, trades, metrics, monthly/instrument/direction/unknown reports, audit, validation and artifact_hashes are in that directory. Additional episodes, round, boundary-touch and daily coverage ledgers preserve event independence and data limitations.

[B7 Baseline_Report](../results/high_low_cluster_m5_2023_b7_v1/Baseline_Report.md); config, signals, rejected_entries, trades, metrics, monthly/instrument/direction/unknown reports, audit, validation and artifact_hashes are in that directory. Additional episodes, round, boundary-touch and daily coverage ledgers preserve event independence and data limitations.

[B10 Baseline_Report](../results/high_low_cluster_m5_2023_b10_v1/Baseline_Report.md); config, signals, rejected_entries, trades, metrics, monthly/instrument/direction/unknown reports, audit, validation and artifact_hashes are in that directory. Additional episodes, round, boundary-touch and daily coverage ledgers preserve event independence and data limitations.

All model code/config hashes unchanged after first P&L. Two full repeats per model (plus the completed repeats before the Git-history regression failure) are byte-identical. No extra N/width/target, ML, parameter sweep, MTF/filter/trailing, Optimization, Robustness, WF, TRUE OOS or model C ran. Only a separate user decision can authorize further work. **STOP; Draft PR without Merge.**
