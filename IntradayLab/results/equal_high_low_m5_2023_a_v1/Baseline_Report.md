# EQUAL_HIGH_LOW_M5 — A_v1 Baseline 2023

**Baseline: INCONCLUSIVE. No Optimization authorized.**

One fixed family A hypothesis, four instruments, entire available 2023 M5. Profit is after model C1 costs, not confirmed actual commissions. All economics shown are conditional known closures. Incomplete coverage/UNKNOWN prevents full annual PF, Net and continuous equity/DD claims. Incompatible futures price P&L is never summed into portfolio money.

Base main `d438c72f9fce5c3bf1d30c9b169d14b97079e768`; pre-P&L freeze `f880b3c4ac0fd2cb6d997d7680a1e427a2537340`; config SHA-256 `cec9b815e1479d7999acf77442840d507eaa5f4e078573e0da4b9d34abc6521a`.

## Frozen parameters and execution

| Parameter | Value |
|---|---|
| max_hold_calendar_minutes | 120 |
| maximum_rebound_ticks | 4 |
| maximum_risk_ticks | 12 |
| minimum_risk_ticks | 3 |
| signal_tf | M5 |
| stop_buffer_ticks | 1 |
| target_mode | FULL_NET_C1_R |
| target_net_R | 3 |
| tolerance_ticks | 0 |
| touches | 3 |
| version | A_v1 |

Signal M5 must be fully complete. At its end: process previous exposed interval, current Open protection/deadline, signal, then admission and fill at the immediate next M5 Open at that same timestamp. No waiting M5. Only that Open scalar reaches admission/geometry. Stop is never shifted; FULL_NET_C1_R=3 sets gross distance=3s+8t with outward rounding. net_R_c1 uses initial gross risk s; planned full net/net ratio uses s+2t.

One opportunity per maximal equal-extreme run: consume on first qualifying three-bar window, including busy/rejected/ambiguous cases. Reset only when that extreme changes, or gap/invalid/session/day/tick boundary occurs. Close at the extreme does not qualify; a later first valid three-bar window may qualify once. Cluster ID includes symbol, day, side, run start and historical-grid level. Simultaneous sides are both rejected and consumed. No round-level or indicator filter.

Inherited approved daytime windows 10:00–14:00 and 14:05–18:50 MSK (dated March lunch adjustment); flat at window end−5m. No extra 17:00 deadline or reserve filter. Hold <=120 calendar minutes. Entry-bar Take remains disabled; Stop permitted, Stop-first on conflict, adverse Stop gaps use actual Open. Missing/invalid next Open is UNKNOWN possible fill, never replaced by later Open. Missing exposed path leaves P&L blank, blocks current day; later days assume conditional FLAT.

## Signals and admission

| Instrument | Raw directional | Signals | Ambiguous candidates | Accepted fills | Known refusals | Unknown entries | CLOSED | UNKNOWN | Fills/day |
|---|---|---|---|---|---|---|---|---|---|
| USDRUBF | 654 | 632 | 22 | 237 | 393 | 2 | 235 | 4 | 0.933071 |
| CNYRUBF | 2418 | 2356 | 62 | 297 | 2011 | 48 | 234 | 111 | 1.169291 |
| GLDRUBF | 180 | 178 | 2 | 12 | 159 | 7 | 9 | 10 | 0.096774 |
| IMOEXF | 61 | 61 | 0 | 16 | 42 | 3 | 13 | 6 | 0.470588 |

Raw directional candidates include the two sides of ambiguous M5 events. Signals exclude those ambiguity rejections. Accepted means model fill; orders include submission attempts before Open geometry is resolved.

## Conditional C1 economics

| Instrument | Gross price | C1 price | Net price | Gross R | C1 R | Net R | PF price | PF R | Expectancy R | DD R |
|---|---|---|---|---|---|---|---|---|---|---|
| USDRUBF | 1.740000 | 4.700000 | -2.960000 | 46.833333 | 127.900000 | -81.066667 | 0.708374 | 0.699345 | -0.344965 | 92.466667 |
| CNYRUBF | -1.037000 | 3.888000 | -4.925000 | 5.383333 | 143.900000 | -138.516667 | 0.294918 | 0.458284 | -0.591952 | 154.916667 |
| GLDRUBF | 10.400000 | 1.800000 | 8.600000 | 22.800000 | 4.600000 | 18.200000 | 4.071429 | 3.166667 | 2.022222 | 6.733333 |
| IMOEXF | -9.000000 | 13.000000 | -22.000000 | -4.083333 | 7.233333 | -11.316667 | 0.254237 | 0.306435 | -0.870513 | 13.316667 |

| Instrument | Avg win R | Avg loss R | Avg win price | Avg loss price | Trade days | + / − months | Largest winner | Top3 winners | Largest + month |
|---|---|---|---|---|---|---|---|---|---|
| USDRUBF | 3.771333 | -1.497963 | 0.143800 | -0.056389 | 149 | 4/8 | 0.026516 | 0.079547 | 0.857639 |
| CNYRUBF | 2.547464 | -1.420556 | 0.044783 | -0.038806 | 131 | 2/10 | 0.042668 | 0.128005 | 0.767327 |
| GLDRUBF | 4.433333 | -2.800000 | 1.900000 | -0.933333 | 9 | 4/1 | 0.187970 | 0.526316 | 0.457093 |
| IMOEXF | 5.000000 | -1.359722 | 7.500000 | -2.458333 | 11 | 0/2 | 1.000000 | 1.000000 | — |

USDRUBF: **INCONCLUSIVE**; conditional economy **NO ECONOMIC BASELINE PASS**.
Refusals: `{"AMBIGUOUS_BOTH_SIDES": 22, "ENTRY_MORE_THAN_4_TICKS_FROM_CLUSTER": 144, "MISSING_EXECUTION_BAR": 2, "OPEN_WRONG_SIDE_OF_CLUSTER": 13, "POSITION_BUSY": 34, "SESSION_LIMIT": 33, "STOP_ABOVE_12_TICKS": 16, "STOP_BELOW_3_TICKS": 150, "UNKNOWN_POSITION_BLOCK": 3}`.
Exits: `{"SESSION_FLAT": 26, "STOP": 171, "TAKE": 35, "TIME": 3}`; UNKNOWN: `{"MISSING_EXECUTION_BAR": 2, "MISSING_EXPOSED_BAR": 2}`.

CNYRUBF: **INCONCLUSIVE**; conditional economy **NO ECONOMIC BASELINE PASS**.
Refusals: `{"AMBIGUOUS_BOTH_SIDES": 62, "ENTRY_MORE_THAN_4_TICKS_FROM_CLUSTER": 29, "MISSING_EXECUTION_BAR": 48, "OPEN_WRONG_SIDE_OF_CLUSTER": 25, "POSITION_BUSY": 343, "SESSION_LIMIT": 57, "STOP_ABOVE_12_TICKS": 4, "STOP_BELOW_3_TICKS": 925, "UNKNOWN_POSITION_BLOCK": 628}`.
Exits: `{"SESSION_FLAT": 40, "STOP": 140, "TAKE": 14, "TIME": 40}`; UNKNOWN: `{"MISSING_EXECUTION_BAR": 48, "MISSING_EXPOSED_BAR": 63}`.

GLDRUBF: **INCONCLUSIVE**; conditional economy **INSUFFICIENT_EVIDENCE**.
Refusals: `{"AMBIGUOUS_BOTH_SIDES": 2, "ENTRY_MORE_THAN_4_TICKS_FROM_CLUSTER": 23, "MISSING_EXECUTION_BAR": 7, "OPEN_WRONG_SIDE_OF_CLUSTER": 12, "SESSION_LIMIT": 7, "STOP_ABOVE_12_TICKS": 82, "STOP_BELOW_3_TICKS": 32, "UNKNOWN_POSITION_BLOCK": 3}`.
Exits: `{"STOP": 3, "TAKE": 6}`; UNKNOWN: `{"MISSING_EXECUTION_BAR": 7, "MISSING_EXPOSED_BAR": 3}`.

IMOEXF: **INCONCLUSIVE**; conditional economy **NO ECONOMIC BASELINE PASS**.
Refusals: `{"ENTRY_MORE_THAN_4_TICKS_FROM_CLUSTER": 12, "MISSING_EXECUTION_BAR": 3, "OPEN_WRONG_SIDE_OF_CLUSTER": 5, "POSITION_BUSY": 1, "SESSION_LIMIT": 4, "STOP_ABOVE_12_TICKS": 1, "STOP_BELOW_3_TICKS": 15, "UNKNOWN_POSITION_BLOCK": 4}`.
Exits: `{"SESSION_FLAT": 2, "STOP": 10, "TAKE": 1}`; UNKNOWN: `{"MISSING_EXECUTION_BAR": 3, "MISSING_EXPOSED_BAR": 3}`.

## LONG / SHORT

| Instrument | Side | Signals | Fills | CLOSED | UNKNOWN | Net R | PF price | PF R |
|---|---|---|---|---|---|---|---|---|
| USDRUBF | SHORT | 336 | 127 | 126 | 2 | -68.516667 | 0.594306 | 0.549331 |
| USDRUBF | LONG | 296 | 110 | 109 | 2 | -12.550000 | 0.849890 | 0.893282 |
| CNYRUBF | SHORT | 1203 | 144 | 110 | 53 | -66.300000 | 0.359704 | 0.467541 |
| CNYRUBF | LONG | 1153 | 153 | 124 | 58 | -72.216667 | 0.234349 | 0.449498 |
| GLDRUBF | SHORT | 110 | 8 | 6 | 7 | 11.166667 | 3.260870 | 2.658416 |
| GLDRUBF | LONG | 68 | 4 | 3 | 3 | 7.033333 | 7.800000 | 5.220000 |
| IMOEXF | SHORT | 31 | 4 | 3 | 4 | -3.566667 | 0.000000 | 0.000000 |
| IMOEXF | LONG | 30 | 12 | 10 | 2 | -7.750000 | 0.326087 | 0.392157 |

## All twelve calendar months

| Month | Instrument | Signals | Fills | CLOSED | UNKNOWN | Net R | PF price | PF R | Coverage |
|---|---|---|---|---|---|---|---|---|---|
| 2023-01 | USDRUBF | 63 | 22 | 22 | 0 | -13.600000 | 0.520000 | 0.492537 | PARTIAL_DATA |
| 2023-01 | CNYRUBF | 241 | 32 | 26 | 11 | -15.150000 | 0.414634 | 0.393596 | UNKNOWN |
| 2023-01 | GLDRUBF | 0 | 0 | 0 | 0 | — | — | — | NO_COVERAGE |
| 2023-01 | IMOEXF | 0 | 0 | 0 | 0 | — | — | — | NO_COVERAGE |
| 2023-02 | USDRUBF | 54 | 23 | 23 | 0 | 1.866667 | 0.979167 | 1.076503 | PARTIAL_DATA |
| 2023-02 | CNYRUBF | 244 | 20 | 16 | 11 | -17.300000 | 0.000000 | 0.000000 | UNKNOWN |
| 2023-02 | GLDRUBF | 0 | 0 | 0 | 0 | — | — | — | NO_COVERAGE |
| 2023-02 | IMOEXF | 0 | 0 | 0 | 0 | — | — | — | NO_COVERAGE |
| 2023-03 | USDRUBF | 68 | 27 | 25 | 2 | 16.466667 | 1.900000 | 1.753049 | UNKNOWN |
| 2023-03 | CNYRUBF | 238 | 13 | 7 | 15 | -5.500000 | 0.142857 | 0.153846 | UNKNOWN |
| 2023-03 | GLDRUBF | 0 | 0 | 0 | 0 | — | — | — | NO_COVERAGE |
| 2023-03 | IMOEXF | 0 | 0 | 0 | 0 | — | — | — | NO_COVERAGE |
| 2023-04 | USDRUBF | 60 | 26 | 26 | 2 | -14.983333 | 0.609756 | 0.541560 | UNKNOWN |
| 2023-04 | CNYRUBF | 251 | 27 | 20 | 12 | -10.250000 | 0.507692 | 0.504032 | UNKNOWN |
| 2023-04 | GLDRUBF | 0 | 0 | 0 | 0 | — | — | — | NO_COVERAGE |
| 2023-04 | IMOEXF | 0 | 0 | 0 | 0 | — | — | — | NO_COVERAGE |
| 2023-05 | USDRUBF | 49 | 16 | 16 | 0 | -3.283333 | 0.826087 | 0.827041 | PARTIAL_DATA |
| 2023-05 | CNYRUBF | 262 | 26 | 15 | 17 | -9.900000 | 0.346154 | 0.377358 | UNKNOWN |
| 2023-05 | GLDRUBF | 0 | 0 | 0 | 0 | — | — | — | NO_COVERAGE |
| 2023-05 | IMOEXF | 0 | 0 | 0 | 0 | — | — | — | NO_COVERAGE |
| 2023-06 | USDRUBF | 49 | 14 | 14 | 0 | 0.366667 | 0.850000 | 1.026506 | PARTIAL_DATA |
| 2023-06 | CNYRUBF | 245 | 23 | 14 | 14 | -12.500000 | 0.224490 | 0.226804 | UNKNOWN |
| 2023-06 | GLDRUBF | 0 | 0 | 0 | 0 | — | — | — | NO_COVERAGE |
| 2023-06 | IMOEXF | 0 | 0 | 0 | 0 | — | — | — | NO_COVERAGE |
| 2023-07 | USDRUBF | 41 | 17 | 17 | 0 | -16.500000 | 0.212500 | 0.255639 | PARTIAL_DATA |
| 2023-07 | CNYRUBF | 230 | 35 | 22 | 16 | -15.783333 | 0.301370 | 0.293284 | UNKNOWN |
| 2023-07 | GLDRUBF | 23 | 4 | 3 | 4 | 1.133333 | 1.750000 | 1.369565 | UNKNOWN |
| 2023-07 | IMOEXF | 0 | 0 | 0 | 0 | — | — | — | NO_COVERAGE |
| 2023-08 | USDRUBF | 42 | 12 | 12 | 0 | -9.533333 | 0.372881 | 0.379610 | PARTIAL_DATA |
| 2023-08 | CNYRUBF | 253 | 48 | 44 | 8 | -44.100000 | 0.246154 | 0.239874 | UNKNOWN |
| 2023-08 | GLDRUBF | 21 | 0 | 0 | 1 | 0.000000 | — | — | UNKNOWN |
| 2023-08 | IMOEXF | 0 | 0 | 0 | 0 | — | — | — | NO_COVERAGE |
| 2023-09 | USDRUBF | 47 | 24 | 24 | 0 | -7.766667 | 0.689320 | 0.713759 | PARTIAL_DATA |
| 2023-09 | CNYRUBF | 283 | 32 | 29 | 5 | -15.000000 | 0.200893 | 0.500000 | UNKNOWN |
| 2023-09 | GLDRUBF | 26 | 2 | 2 | 1 | -0.833333 | 1.125000 | 0.843750 | UNKNOWN |
| 2023-09 | IMOEXF | 0 | 0 | 0 | 0 | — | — | — | NO_COVERAGE |
| 2023-10 | USDRUBF | 39 | 13 | 13 | 0 | -14.533333 | 0.156250 | 0.146771 | CONDITIONAL_AFTER_UNKNOWN |
| 2023-10 | CNYRUBF | 29 | 10 | 10 | 1 | -3.133333 | 0.733333 | 0.751979 | UNKNOWN |
| 2023-10 | GLDRUBF | 33 | 4 | 2 | 3 | 8.700000 | — | — | UNKNOWN |
| 2023-10 | IMOEXF | 0 | 0 | 0 | 0 | — | — | — | NO_COVERAGE |
| 2023-11 | USDRUBF | 73 | 26 | 26 | 0 | 0.500000 | 1.075269 | 1.020161 | PARTIAL_DATA |
| 2023-11 | CNYRUBF | 46 | 21 | 21 | 1 | 7.750000 | 1.360000 | 1.377129 | UNKNOWN |
| 2023-11 | GLDRUBF | 38 | 1 | 1 | 0 | 5.000000 | — | — | PARTIAL_DATA |
| 2023-11 | IMOEXF | 13 | 3 | 2 | 3 | -3.166667 | 0.000000 | 0.000000 | UNKNOWN |
| 2023-12 | USDRUBF | 47 | 17 | 17 | 0 | -20.066667 | 0.204545 | 0.183175 | CONDITIONAL_AFTER_UNKNOWN |
| 2023-12 | CNYRUBF | 34 | 10 | 10 | 0 | 2.350000 | 1.410256 | 1.220657 | CONDITIONAL_AFTER_UNKNOWN |
| 2023-12 | GLDRUBF | 37 | 1 | 1 | 1 | 4.200000 | — | — | UNKNOWN |
| 2023-12 | IMOEXF | 48 | 13 | 11 | 3 | -8.150000 | 0.312500 | 0.380228 | UNKNOWN |

## Coverage and limits

| Instrument | Rows | First | Complete / incomplete / pre-inception days | Missing / invalid slots |
|---|---|---|---|---|
| USDRUBF | 42576 | 2023-01-03 09:00:00+03:00 | 224/30/0 | 187/0 |
| CNYRUBF | 39362 | 2023-01-03 09:00:00+03:00 | 82/172/0 | 1270/0 |
| GLDRUBF | 18428 | 2023-07-11 10:00:00+03:00 | 5/119/130 | 932/0 |
| IMOEXF | 4429 | 2023-11-14 10:00:00+03:00 | 2/32/220 | 566/0 |

Only four exact read-only 2023 prefixes from `f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8`. CNY tick 0.01 → 0.001 from 2023-09-27 19:00 MSK. Zero price bytes 2024+ read. Source/grid receipts in input_provenance.json and validation.json. Real execution/funding/margin/capital are unproved; normalized research only.

Implementation-independent backward-run/forward-path auditor, coverage and CSV economics: Independent_Audit.md and audit.json. Byte repeats, default-mode regressions and protected-file receipts: validation.json. This is task-agent algorithmic audit, not external human signoff.

ENTRY_CLOSE_ORACLE is isolated under diagnostics/. It uses an idealized signal Close and can never qualify economic PASS. Its metrics are excluded from this report and Baseline classification.

## Allowed next action

STOP after this first Baseline and Draft PR without merge. Review the audit and limitations; negative C1 expectancy has NO ECONOMIC BASELINE PASS and cannot advance to Optimization. No automatic new candidate. B 4/7/10 (eventually 4–10), C separate approaches, touch/Stop/Take 2/3/5/7/10R optimization, trailing, MTF and filters remain documented future tasks only. 2024 WF and 2025+ TRUE OOS remain closed.
