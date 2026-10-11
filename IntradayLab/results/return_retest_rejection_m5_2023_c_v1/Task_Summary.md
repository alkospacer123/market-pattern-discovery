# C_v1 Baseline 2023 — task summary

Base SHA: `f0e56f5df557ac4eae19af333b6d438524f5f6ff`. Pre-P&L freeze SHA: `16d07c2c5dc7b3fe5ceb90760e9ce4a7ed17358f`.
Audit revision 1.1 SHA: `2804513a2a848908349d5498268609302a9743cf`. Final commit SHA is in the Draft PR description and chat (cannot embed its own SHA in its commit).

Config SHA-256: `879801c71ce7d56972c17886ef3f33caf6c6c9d2df81fc3d49f068ec173e27df`. Fixed C_v1, common Backtester unchanged. **552 pre-P&L tests PASS + 4 audit-revision tests PASS**.
Independent audit **PASS: 570434 fields**, original run and both repeats. **15/15 original artifacts byte-identical** on each complete repeat.

Audit 1.0 had a pooled Decimal summation-order reporting defect of -2E-26 R. Separate committed audit 1.1 preserves exact checks; no C_v1 trading/config/runner/first-result bytes changed. [Disclosure](../../reports/RETURN_RETEST_C_V1_AUDIT_REVISION_1_1.md).

## Configuration

| Parameter | Value |
| --- | --- |
| approaches | 3 |
| local_extreme_lookback | 5 |
| local_extreme_strict | True |
| max_hold_calendar_minutes | 120 |
| maximum_construction_bars | 24 |
| maximum_rebound_ticks | 4 |
| maximum_risk_ticks | 12 |
| minimum_risk_ticks | 3 |
| rejection_close_ticks | 1 |
| retreat_ticks | 3 |
| signal_tf | M5 |
| stop_buffer_ticks | 1 |
| target_mode | FULL_NET_C1_R |
| target_net_R | 3.000 |
| tolerance_ticks | 2 |
| version | C_v1 |

ENTRY_NEXT_OPEN / DATA_GAP_SKIP_V2; actual next Open only; C1 one dated tick per side; Stop-first, Stop-gap, no entry-bar Take, flat one M5 before session end, one position per instrument. Strict local extreme versus five previous continuous same-window M5; first zone bar after each 3-tick whole-bar retreat counts once; third approach consumed even if Close/fill fails. Observed construction boundary determines Stop and displacement. Actual admitted risk is 3–5 ticks under the combined fixed bounds; no parameter correction based on returns.

## Counts and conditional after-C1 economics

| Instrument | FIRST | SECOND | THIRD | LONG / SHORT signals | Entries | CLOSED | SKIP | EXCLUDED | PF R | PF price | Gross R | Cost R | Net R |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CNYRUBF | 2903 | 535 | 144 | 73 / 59 | 77 | 61 | 0 | 16 | 0.376 | 0.055 | -5.800 | 32.567 | -38.367 |
| GLDRUBF | 2766 | 170 | 23 | 10 / 9 | 2 | 2 | 0 | 0 | 0.000 | 0.000 | -3.250 | 1.167 | -4.417 |
| IMOEXF | 378 | 78 | 17 | 9 / 6 | 5 | 3 | 0 | 2 | 1.724 | 1.154 | 3.667 | 1.567 | 2.100 |
| USDRUBF | 5352 | 1142 | 280 | 113 / 126 | 104 | 102 | 2 | 2 | 0.626 | 0.642 | 8.067 | 51.567 | -43.500 |

Totals: **188 entries = 168 CLOSED + 20 EXCLUDED**, 2 SKIP; 274 candidate refusals include 59 pattern/ambiguity failures and 215 execution/session/position refusals. **Pooled normalized R only:** Gross 2.683, Cost 86.867, Net -84.183, PF 0.545, expectancy -0.501; no pooled price PF or cash-return claim.

| Instrument | Mean win R | Mean loss R | Mean win price | Mean loss price | WR | E[R] | Known DD R | Trade days | Active months | Positive / negative months | EXCLUDED share |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CNYRUBF | 3.850 | -1.229 | 0.017 | -0.037 | 0.098 | -0.629 | 47.467 | 52 | 11 | 1 / 10 | 0.208 |
| GLDRUBF | null | -2.208 | null | -0.800 | 0.000 | -2.208 | 4.417 | 2 | 2 | 0 / 2 | 0.000 |
| IMOEXF | 5.000 | -1.450 | 7.500 | -3.250 | 0.333 | 0.700 | 2.900 | 3 | 1 | 1 / 0 | 0.400 |
| USDRUBF | 3.161 | -1.490 | 0.132 | -0.061 | 0.225 | -0.426 | 53.133 | 82 | 12 | 2 / 10 | 0.019 |

DD is the maximum observed drawdown of known closures; EXCLUDED outcomes prevent a complete annual/continuous account equity claim.

## Refusals and losses

**CNYRUBF** refusals: `{"DATA_QUALITY_POSITION_BLOCK": 4, "ENTRY_MORE_THAN_4_TICKS_FROM_CONSTRUCTION": 27, "POSITION_BUSY": 5, "SESSION_LIMIT": 9, "STOP_ABOVE_12_TICKS": 3, "STOP_BELOW_3_TICKS": 7, "THIRD_CLOSE_NOT_REJECTED": 12}`.

| Exit | CLOSED count | Net R | Losing closures | Losing Net R |
| --- | --- | --- | --- | --- |
| SESSION_FLAT | 19 | -7.333 | 14 | -7.533 |
| STOP | 33 | -50.933 | 33 | -50.933 |
| TAKE | 5 | 22.900 | 0 | 0.000 |
| TIME | 4 | -3.000 | 3 | -3.000 |

**GLDRUBF** refusals: `{"OPEN_WRONG_SIDE_OF_CONSTRUCTION": 1, "STOP_ABOVE_12_TICKS": 12, "STOP_BELOW_3_TICKS": 4, "THIRD_CLOSE_NOT_REJECTED": 4}`.

| Exit | CLOSED count | Net R | Losing closures | Losing Net R |
| --- | --- | --- | --- | --- |
| SESSION_FLAT | 0 | 0.000 | 0 | 0.000 |
| STOP | 2 | -4.417 | 2 | -4.417 |
| TAKE | 0 | 0.000 | 0 | 0.000 |
| TIME | 0 | 0.000 | 0 | 0.000 |

**IMOEXF** refusals: `{"ENTRY_MORE_THAN_4_TICKS_FROM_CONSTRUCTION": 6, "STOP_ABOVE_12_TICKS": 1, "STOP_BELOW_3_TICKS": 3, "THIRD_CLOSE_NOT_REJECTED": 2}`.

| Exit | CLOSED count | Net R | Losing closures | Losing Net R |
| --- | --- | --- | --- | --- |
| SESSION_FLAT | 0 | 0.000 | 0 | 0.000 |
| STOP | 2 | -2.900 | 2 | -2.900 |
| TAKE | 1 | 5.000 | 0 | 0.000 |
| TIME | 0 | 0.000 | 0 | 0.000 |

**USDRUBF** refusals: `{"AMBIGUOUS_BOTH_SIDES": 2, "ENTRY_MORE_THAN_4_TICKS_FROM_CONSTRUCTION": 99, "MISSING_EXECUTION_BAR": 2, "POSITION_BUSY": 2, "SESSION_LIMIT": 13, "STOP_ABOVE_12_TICKS": 4, "STOP_BELOW_3_TICKS": 15, "THIRD_CLOSE_NOT_REJECTED": 39}`.

| Exit | CLOSED count | Net R | Losing closures | Losing Net R |
| --- | --- | --- | --- | --- |
| SESSION_FLAT | 13 | 9.500 | 3 | -2.800 |
| STOP | 75 | -113.400 | 75 | -113.400 |
| TAKE | 13 | 58.200 | 0 | 0.000 |
| TIME | 1 | 2.200 | 0 | 0.000 |

112 STOP, 19 TAKE, 5 TIME, 32 SESSION_FLAT known closures. Gross pooled R is only +2.683; C1 costs 86.867 R. Thus modeled costs overwhelm the small gross result. Structural Stop exits are the main negative contribution; scheduled exits have their separate observed amounts. A fixed full-net 3R plan requires 17–23 ticks of Take travel for 3–5 ticks raw risk, so nominal RR does not imply positive expectancy. No counterfactual profitable entry, alternative Stop or filter is tested.

## Geometry and concentration

| Instrument | Retreat min / mean / max ticks | Approach gap min / mean / max M5 | Observed touch width min / mean / max ticks | Stop min / mean / max ticks | Largest winner share R | Top 3 winners share R | Largest positive month share R |
| --- | --- | --- | --- | --- | --- | --- | --- |
| CNYRUBF | 3.000 / 3.962 / 21.000 | 2 / 6.524 / 20 | 0.000 / 1.917 / 4.000 | 3.000 / 3.844 / 5.000 | 0.216 | 0.628 | 1.000 |
| GLDRUBF | 3.000 / 23.109 / 77.000 | 2 / 4.565 / 17 | 0.000 / 1.261 / 4.000 | 3.000 / 3.500 / 4.000 | null | null | null |
| IMOEXF | 3.000 / 5.382 / 15.000 | 2 / 4.118 / 15 | 0.000 / 1.706 / 4.000 | 3.000 / 3.800 / 5.000 | 1.000 | 1.000 | 1.000 |
| USDRUBF | 3.000 / 5.011 / 17.000 | 2 / 5.664 / 20 | 0.000 / 2.025 / 4.000 | 3.000 / 4.125 / 5.000 | 0.069 | 0.206 | 0.537 |

Allowed zone width is fixed at 4 ticks (+/-2). Geometry here describes completed third-approach candidates; construction_events.csv also preserves all partial first/second approaches and retreat witnesses.

## Calendar Net R — all twelve months

| Month | USDRUBF | CNYRUBF | GLDRUBF | IMOEXF | ALL R diagnostic |
| --- | --- | --- | --- | --- | --- |
| 2023-01 | 9.500 | -8.350 | NO_COVERAGE | NO_COVERAGE | 1.150 |
| 2023-02 | -11.233 | -0.967 | NO_COVERAGE | NO_COVERAGE | -12.200 |
| 2023-03 | -10.083 | 0.000 | NO_COVERAGE | NO_COVERAGE | -10.083 |
| 2023-04 | -1.100 | -0.750 | NO_COVERAGE | NO_COVERAGE | -1.850 |
| 2023-05 | -1.200 | -7.000 | NO_COVERAGE | NO_COVERAGE | -8.200 |
| 2023-06 | -4.217 | -0.600 | NO_COVERAGE | NO_COVERAGE | -4.817 |
| 2023-07 | -6.133 | -9.000 | 0.000 | NO_COVERAGE | -15.133 |
| 2023-08 | -4.467 | -15.233 | 0.000 | NO_COVERAGE | -19.700 |
| 2023-09 | -8.167 | -1.367 | -1.667 | NO_COVERAGE | -11.200 |
| 2023-10 | 11.000 | -3.067 | 0.000 | NO_COVERAGE | 7.933 |
| 2023-11 | -8.733 | 10.700 | -2.750 | 0.000 | -0.783 |
| 2023-12 | -8.667 | -2.733 | 0.000 | 2.100 | -9.300 |

Monthly CLOSED/SKIP/EXCLUDED and full metrics: monthly_report.csv (48 instrument rows + 12 normalized-R rows). NO_COVERAGE before inception is not a measured zero month; observed no-trade months have zero known closure sum.

## Source coverage and data sufficiency

| Instrument | First source | Source 2023 rows | Complete days | Incomplete days | Pre-inception days | Expected post-inception slots | Valid slots | Valid share | Missing post-inception |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CNYRUBF | 2023-01-03 09:00:00 | 39362 | 82 | 172 | 0 | 26658 | 25388 | 0.952 | 1270 |
| GLDRUBF | 2023-07-11 10:00:00 | 18428 | 5 | 119 | 130 | 13020 | 12088 | 0.928 | 932 |
| IMOEXF | 2023-11-14 10:00:00 | 4429 | 2 | 32 | 220 | 3570 | 3004 | 0.841 | 566 |
| USDRUBF | 2023-01-03 09:00:00 | 42576 | 224 | 30 | 0 | 26658 | 26471 | 0.993 | 187 |

Full coverage_report includes pre-inception expected slots as missing and explicitly PRE_INCEPTION; the table above separates these from post-inception gaps. No invalid source bars. CNY tick is 0.01 before 2023-09-27 19:00 MSK, then 0.001. Source checkout pinned and clean; exact 2023 byte reads only, zero 2024+ candle bytes. Exclusions are 20/188 = 10.638% of accepted entries overall; CNY 16/77 and IMOEX 2/5 are substantial potential selection bias. Every entry is retained in CLOSED or EXCLUDED by ID. Next independent days disclose assumed, unproven FLAT.

## Technical and future Optimization assessment

**Technical correctness: PASS** with independent reconstruction and identical repeats. **Resolved sample:** USD 102 CLOSED / 82 days / 12 months; CNY 61 / 52 / 11; GLD 2 / 2 / 2; IMOEX 3 / 3 / 1. USD/CNY offer materially broader samples to review; GLD/IMOEX are sparse. **Economics:** USD/CNY/GLD negative after C1; IMOEX positive on three closures is insufficient evidence. **Data:** incomplete for every instrument, with explicit excluded outcomes; no verified annual profitability.

**Future Optimization:** C is technically suitable for a separately versioned, bounded 2023 study after independent review and common minimum-count/month eligibility rules are preregistered. No such threshold or eligibility ranking is invented here. PF below 2 or a negative initial Baseline does not reject family C under the latest Roadmap; sparse instrument cohorts should not be optimized until they qualify. Optimization has not run.

A/B comparison and observed overlap: [Comparison.md](Comparison.md). Archived UNKNOWN were not relabeled. Frozen compatibility checks are recorded separately in legacy_regressions.json and earlier_regressions.json.

## Protected scope and STOP

TradingSystemLab, common core, every previously existing frozen IntradayLab file except the three current-status documents, source repository and Draft #472 are unchanged. Only IntradayLab additions and current-status inserts. Complete changed-file list: CHANGED_FILES.txt; protection receipt: protected_scope.json.

Separate Draft PR only. No merge/auto-merge, Optimization, Robustness, 2024 WF, 2025+ TRUE OOS, LIVE or next strategy. STOP after Baseline C.
