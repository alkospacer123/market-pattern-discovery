# TREND_PULLBACK_M15_H1 — Canonical Baseline 2023

**Research phase: BASELINE. Final classification: INCONCLUSIVE.**

One initial structural hypothesis supplied before results, one fixed configuration, four instruments, entire available 2023. No Optimization or alternative scenario.
All economics below are conditional known closures after C1 (one dated tick per side). Annual complete metrics remain null on incomplete coverage/UNKNOWN. Conditional DD is not proven continuous equity. Instrument price P&L is never pooled as portfolio money.

## Fixed parameters and causal contract

| Parameter | Value |
|---|---|
| confirmation_bars | 1 |
| confirmation_break_ticks | 1 |
| context_tf | H1 |
| cost | C1 |
| daily_trade_deadline | 17:00 |
| h1_children_m15 | 4 |
| h1_delivery_delay_minutes | 5 |
| h1_direction | ONE_CLOSE_VS_OPEN |
| m15_children_m5 | 3 |
| max_hold_calendar_minutes | 120 |
| min_entry_to_flat_minutes | 35 |
| min_initial_risk_ticks | 4 |
| pullback_bars | 1 |
| signal_tf | M15 |
| stop_buffer_ticks | 1 |
| stop_mode | CORRECTION_AND_SIGNAL_EXTREME |
| target_mode | FULL_NET_C1_R |
| target_net_R | 3 |
| wait_complete_m15_bars | 1 |

Pre-P&L commit `297ab911e6c34ab4cfa574fbae8b805da099f481`; config SHA-256 `ffa6a43e9e734fdc40c25af122b73a8a963e0a364dbf0aaecb222339199460fc`. Config, signal/M15/H1 and common core hashes are verified against this freeze. No result-driven changes.

- **H1:** Exact four valid M15, one day/window. Available start+65. Latest nominally released hour only. Detected M15/M5 gaps immediately clear context; next full post-gap H1 restores it. No stale fallback.
- **M15:** Exact three consecutive valid completed M5 in one full MSK quarter-hour window. Missing later child preserves observed first Open only; NaN HLC/zero volume prevent fabricated observation.
- **entry:** Signal close -> one complete waiting M15 -> next M15 Open. H1 direction and structural Stop fixed at signal. Four tick initial risk and dated grid at Open.
- **exit:** Shared Stop-first/adverse gap and entry-bar Take prohibition. M15 session flat uses last full calendar M15 Open <= window.end-15; time cap120 and <=17:00. Scheduled Open never consults future HLC.
- **reserve:** 35 minutes to actual mandatory flat min(last full session Open,17:00); no PM eligibility and no morning context carry through lunch.
- **selection:** Single user-supplied fixed hypothesis; no parameter search or later economic tuning.
- **signal:** One latest H1 Close vs Open. One immediately previous opposite-color M15; distinct trend-color M15 closes >=1 historical tick beyond correction high/low.
- **stop:** Min low / max high of correction and signal plus one adverse historical tick.
- **target:** Unchanged shared FULL_NET_C1_R: d=3s+8t with outward rounding; net_R_c1 and fully net/net R retained.
- **unknown:** Missing waiting rejected. Known first Open/incomplete interval permits observable model fill then UNKNOWN path. Missing first Open => UNKNOWN possible fill. Current day blocks; following day conditional FLAT.

## H1 → M15 → entry → exit

Context/trend counts are per M15 decision, not unique independent trend episodes. h1_context.csv links every decision to one H1, four M15 and twelve child M5 timestamps; all times are MSK and child clocks use their parent date. Unavailable buckets retain expected lineage, blank prices and explicit reasons.

| Instrument | Valid H1 | LONG | SHORT | Pullbacks | Signals | Rejected | Pending | Orders | Fills | Closed | UNKNOWN |
|---|---|---|---|---|---|---|---|---|---|---|---|
| USDRUBF | 5674 | 2975 | 2556 | 2332 | 307 | 236 | 84 | 84 | 71 | 70 | 1 |
| CNYRUBF | 3737 | 1769 | 1669 | 1259 | 139 | 107 | 40 | 40 | 32 | 29 | 4 |
| GLDRUBF | 1182 | 583 | 595 | 508 | 85 | 65 | 25 | 22 | 20 | 11 | 11 |
| IMOEXF | 214 | 97 | 101 | 80 | 17 | 13 | 4 | 4 | 4 | 1 | 3 |

| Instrument | Exact M15 | Incomplete M15 | Known Open / incomplete | Exact H1 | Unique available H1 | Unique directional H1 |
|---|---|---|---|---|---|---|
| USDRUBF | 8553 | 83 | 21 | 1740 | 1487 | 1450 |
| CNYRUBF | 7661 | 975 | 551 | 1277 | 1050 | 957 |
| GLDRUBF | 3450 | 5186 | 477 | 461 | 362 | 361 |
| IMOEXF | 769 | 7867 | 225 | 89 | 65 | 61 |

## Calendar reachability fixed before P&L

{"AM_slots_per_day": ["11:30", "11:45", "12:00", "12:15", "12:30", "12:45", "13:00"], "PM_admissible_slots": 0, "PM_structurally_impossible": true, "contract": "calendar-only before first P&L; full aligned M15 Opens, H1 start+65, wait1, reserve35", "trading_days": 254}

PM entries are structurally impossible: first H1 15:00–16:00 is delivered 16:05; earliest M15 decision 16:15 and entry 16:30 leave only 30 minutes to 17:00 (<35). No morning H1 crosses lunch.

## Conditional C1 economics

| Instrument | Closed | Days | PF price | PF R | Net R | Expectancy R | Win rate | Conditional DD R |
|---|---|---|---|---|---|---|---|---|
| USDRUBF | 70 | 68 | 0.905882 | 0.953308 | -1.515720 | -0.021653 | 0.371429 | 12.868931 |
| CNYRUBF | 29 | 28 | 0.726368 | 0.962734 | -0.547283 | -0.018872 | 0.275862 | 5.685880 |
| GLDRUBF | 11 | 10 | 0.964948 | 0.749660 | -1.111069 | -0.101006 | 0.454545 | 2.756851 |
| IMOEXF | 1 | 1 | 0.000000 | 0.000000 | -1.500000 | -1.500000 | 0.000000 | 1.500000 |

| Instrument | Avg win R | Avg loss R | Avg win price | Avg loss price | Largest winner share | Top 3 share | Largest positive month share |
|---|---|---|---|---|---|---|---|
| USDRUBF | 1.190243 | -0.737773 | 0.207308 | -0.135227 | 0.109868 | 0.327275 | 0.253607 |
| CNYRUBF | 1.767323 | -0.734293 | 0.036500 | -0.020100 | 0.282914 | 0.754016 | 0.700727 |
| GLDRUBF | 0.665435 | -0.739707 | 9.360000 | -8.083333 | 0.233765 | 0.691814 | 1.000000 |
| IMOEXF | — | -1.500000 | — | -3.000000 | — | — | — |

## Calendar regularity

| Instrument | Positive /12 | Positive /active | Worst known month | Worst Net R | Fills /available day |
|---|---|---|---|---|---|
| USDRUBF | 0.666667 | 0.666667 | 2023-08 | -6.746418 | 0.279528 |
| CNYRUBF | 0.166667 | 0.333333 | 2023-12 | -1.654970 | 0.125984 |
| GLDRUBF | 0.083333 | 0.250000 | 2023-09 | -2.082694 | 0.161290 |
| IMOEXF | 0.000000 | 0.000000 | 2023-12 | -1.500000 | 0.117647 |

Positive known closures in a month do not establish a complete positive calendar result. Zero-trade and pre-inception months are not positive. Every month remains in the tables.

## Planned and actual 3R

The planned full-net ratio is (take distance−2t)/(initial price risk+2t). Shared FULL_NET_C1_R sets distance=3s+8t with outward rounding. Actual net/net uses realized net price P&L/(s+actual C1); net_R_c1 and PF_R use s. These are different denominators. Target geometry never guarantees attainment.

| Instrument | Plan min | Plan max | TAKE | TAKE /closed | Actual TAKE min | Actual TAKE max | Closed >=3 net/net | Filled UNKNOWN |
|---|---|---|---|---|---|---|---|---|
| USDRUBF | 3.000000 | 3.000000 | 3 | 0.042857 | 3.000000 | 3.000000 | 3 | 1 |
| CNYRUBF | 3.000000 | 3.000000 | 3 | 0.103448 | 3.000000 | 3.000000 | 3 | 3 |
| GLDRUBF | 3.000000 | 3.000000 | 0 | 0.000000 | — | — | 0 | 9 |
| IMOEXF | 3.000000 | 3.000000 | 0 | 0.000000 | — | — | 0 | 3 |

USDRUBF: **INCONCLUSIVE**; conditional diagnosis **NO ECONOMIC BASELINE PASS**.
Exit counts / costs / target details: `{"actual_Take_net_net_R_max": "3", "actual_Take_net_net_R_min": "3", "adverse_Stop_gaps": 0, "cost_R_known_closed": "9.116074220952855938853123649", "cost_price_known_closed": "1.40", "exit_reasons": {"SESSION_FLAT": 37, "STOP": 22, "TAKE": 3, "TIME": 8}, "gross_R_known_closed": "7.600353801691670879076773485", "gross_price_known_closed": "0.84", "initial_R_denominator": "initial gross price risk; unchanged common metric contract", "known_closures_reaching_full_net_3R": 3, "mean_positive_realized_net_net_R": "1.039606105773661768355527434", "planned_full_net_R_max": "3", "planned_full_net_R_min": "3", "target_hit_closed": 3, "target_hit_fraction_known_closed": "0.04285714285714285714285714286", "target_ratio_denominator": "initial gross risk + round-trip C1", "unresolved_filled_targets": 1}`.
Rejected events: `{"H1_DOJI": 143, "H1_INCOMPLETE_OR_GAP_RESET": 113, "H1_NOT_YET_AVAILABLE": 2766, "INVALID_RISK": 7, "M15_INVALID_BAR": 21, "M15_MISSING_BAR": 62, "NO_M15_CONTINUATION": 2025, "NO_M15_CORRECTION": 3199, "POSITION_BUSY": 10, "RISK_BELOW_FOUR_TICKS": 6, "SESSION_ENTRY_CUTOFF": 45, "SESSION_LIMIT": 46, "TRADE_DEADLINE": 121, "UNKNOWN_POSITION_BLOCK": 1}`.
UNKNOWN: `{"INVALID_EXPOSED_BAR": 1}`.
Evidence checks: `{"PF_goal_met": false, "complete": false, "concentration_acceptable": true, "enough_sample": true, "monthly_stability": true, "positive_expectancy": false}`.

CNYRUBF: **INCONCLUSIVE**; conditional diagnosis **NO ECONOMIC BASELINE PASS**.
Exit counts / costs / target details: `{"actual_Take_net_net_R_max": "3", "actual_Take_net_net_R_min": "3", "adverse_Stop_gaps": 0, "cost_R_known_closed": "3.502233269013385147268669903", "cost_price_known_closed": "0.094", "exit_reasons": {"SESSION_FLAT": 16, "STOP": 9, "TAKE": 3, "TIME": 1}, "gross_R_known_closed": "2.954950298534736965676294772", "gross_price_known_closed": "-0.016", "initial_R_denominator": "initial gross price risk; unchanged common metric contract", "known_closures_reaching_full_net_3R": 3, "mean_positive_realized_net_net_R": "1.53828125000000000000000000", "planned_full_net_R_max": "3", "planned_full_net_R_min": "3", "target_hit_closed": 3, "target_hit_fraction_known_closed": "0.1034482758620689655172413793", "target_ratio_denominator": "initial gross risk + round-trip C1", "unresolved_filled_targets": 3}`.
Rejected events: `{"H1_DOJI": 299, "H1_INCOMPLETE_OR_GAP_RESET": 1426, "H1_NOT_YET_AVAILABLE": 2498, "INVALID_RISK": 3, "M15_INVALID_BAR": 551, "M15_MISSING_BAR": 424, "MISSING_EXECUTION_BAR": 1, "NO_M15_CONTINUATION": 1120, "NO_M15_CORRECTION": 2179, "POSITION_BUSY": 4, "RISK_BELOW_FOUR_TICKS": 4, "SESSION_ENTRY_CUTOFF": 18, "SESSION_LIMIT": 15, "TRADE_DEADLINE": 62}`.
UNKNOWN: `{"INVALID_EXPOSED_BAR": 3, "MISSING_EXECUTION_BAR": 1}`.
Evidence checks: `{"PF_goal_met": false, "complete": false, "concentration_acceptable": false, "enough_sample": false, "monthly_stability": false, "positive_expectancy": false}`.

GLDRUBF: **INCONCLUSIVE**; conditional diagnosis **NO ECONOMIC BASELINE PASS**.
Exit counts / costs / target details: `{"actual_Take_net_net_R_max": null, "actual_Take_net_net_R_min": null, "adverse_Stop_gaps": 0, "cost_R_known_closed": "0.2107967483524998302047165606", "cost_price_known_closed": "2.2", "exit_reasons": {"SESSION_FLAT": 5, "STOP": 3, "TIME": 3}, "gross_R_known_closed": "-0.9002722085393262538992578392", "gross_price_known_closed": "0.5", "initial_R_denominator": "initial gross price risk; unchanged common metric contract", "known_closures_reaching_full_net_3R": 0, "mean_positive_realized_net_net_R": "0.6553298511367607122977483844", "planned_full_net_R_max": "3", "planned_full_net_R_min": "3", "target_hit_closed": 0, "target_hit_fraction_known_closed": "0", "target_ratio_denominator": "initial gross risk + round-trip C1", "unresolved_filled_targets": 9}`.
Rejected events: `{"H1_DOJI": 4, "H1_INCOMPLETE_OR_GAP_RESET": 1144, "H1_NOT_YET_AVAILABLE": 1124, "M15_INVALID_BAR": 477, "M15_MISSING_BAR": 289, "MISSING_EXECUTION_BAR": 2, "NO_M15_CONTINUATION": 423, "NO_M15_CORRECTION": 670, "NO_WAITING_BAR": 3, "POSITION_BUSY": 3, "SESSION_ENTRY_CUTOFF": 11, "SESSION_LIMIT": 9, "TRADE_DEADLINE": 33, "UNKNOWN_POSITION_BLOCK": 4}`.
UNKNOWN: `{"INVALID_EXPOSED_BAR": 7, "MISSING_EXECUTION_BAR": 2, "MISSING_EXPOSED_BAR": 2}`.
Evidence checks: `{"PF_goal_met": false, "complete": false, "concentration_acceptable": false, "enough_sample": false, "monthly_stability": false, "positive_expectancy": false}`.

IMOEXF: **INCONCLUSIVE**; conditional diagnosis **NO ECONOMIC BASELINE PASS**.
Exit counts / costs / target details: `{"actual_Take_net_net_R_max": null, "actual_Take_net_net_R_min": null, "adverse_Stop_gaps": 0, "cost_R_known_closed": "0.5", "cost_price_known_closed": "1.0", "exit_reasons": {"STOP": 1}, "gross_R_known_closed": "-1", "gross_price_known_closed": "-2.0", "initial_R_denominator": "initial gross price risk; unchanged common metric contract", "known_closures_reaching_full_net_3R": 0, "mean_positive_realized_net_net_R": null, "planned_full_net_R_max": "3", "planned_full_net_R_min": "3", "target_hit_closed": 0, "target_hit_fraction_known_closed": "0", "target_ratio_denominator": "initial gross risk + round-trip C1", "unresolved_filled_targets": 3}`.
Rejected events: `{"H1_DOJI": 16, "H1_INCOMPLETE_OR_GAP_RESET": 294, "H1_NOT_YET_AVAILABLE": 261, "M15_INVALID_BAR": 225, "M15_MISSING_BAR": 162, "NO_M15_CONTINUATION": 63, "NO_M15_CORRECTION": 118, "SESSION_ENTRY_CUTOFF": 2, "SESSION_LIMIT": 4, "TRADE_DEADLINE": 7}`.
UNKNOWN: `{"INVALID_EXPOSED_BAR": 2, "MISSING_EXPOSED_BAR": 1}`.
Evidence checks: `{"PF_goal_met": false, "complete": false, "concentration_acceptable": false, "enough_sample": false, "monthly_stability": false, "positive_expectancy": false}`.

## LONG / SHORT

| Instrument | Side | Signals | Fills | Closed | UNKNOWN | PF price | PF R | Net R | Expectancy R |
|---|---|---|---|---|---|---|---|---|---|
| USDRUBF | SHORT | 135 | 40 | 40 | 0 | 0.836957 | 0.790259 | -4.080221 | -0.102006 |
| USDRUBF | LONG | 172 | 31 | 30 | 1 | 1.017621 | 1.197141 | 2.564500 | 0.085483 |
| CNYRUBF | SHORT | 66 | 19 | 16 | 4 | 0.599278 | 0.607223 | -3.461778 | -0.216361 |
| CNYRUBF | LONG | 73 | 13 | 13 | 0 | 1.008000 | 1.496315 | 2.914495 | 0.224192 |
| GLDRUBF | SHORT | 47 | 12 | 6 | 7 | 0.610526 | 0.396110 | -1.920140 | -0.320023 |
| GLDRUBF | LONG | 38 | 8 | 5 | 4 | 2.247619 | 1.642822 | 0.809071 | 0.161814 |
| IMOEXF | SHORT | 10 | 2 | 0 | 2 | — | — | 0.000000 | — |
| IMOEXF | LONG | 7 | 2 | 1 | 1 | 0.000000 | 0.000000 | -1.500000 | -1.500000 |

## All twelve calendar months

| Month | Instrument | Signals | Fills | Closed | UNKNOWN | PF price | PF R | Net R | Expectancy R | Coverage |
|---|---|---|---|---|---|---|---|---|---|---|
| 2023-01 | USDRUBF | 24 | 8 | 7 | 1 | 0.858407 | 1.298671 | 1.049883 | 0.149983 | UNKNOWN |
| 2023-01 | CNYRUBF | 3 | 0 | 0 | 0 | — | — | 0.000000 | — | PARTIAL_DATA |
| 2023-01 | GLDRUBF | 0 | 0 | 0 | 0 | — | — | — | — | NO_COVERAGE |
| 2023-01 | IMOEXF | 0 | 0 | 0 | 0 | — | — | — | — | NO_COVERAGE |
| 2023-02 | USDRUBF | 24 | 5 | 5 | 0 | 0.863636 | 0.402753 | -1.575595 | -0.315119 | PARTIAL_DATA |
| 2023-02 | CNYRUBF | 3 | 1 | 1 | 0 | 0.000000 | 0.000000 | -0.333333 | -0.333333 | PARTIAL_DATA |
| 2023-02 | GLDRUBF | 0 | 0 | 0 | 0 | — | — | — | — | NO_COVERAGE |
| 2023-02 | IMOEXF | 0 | 0 | 0 | 0 | — | — | — | — | NO_COVERAGE |
| 2023-03 | USDRUBF | 28 | 4 | 4 | 0 | 3.846154 | 2.880178 | 2.222028 | 0.555507 | PARTIAL_DATA |
| 2023-03 | CNYRUBF | 2 | 0 | 0 | 0 | — | — | 0.000000 | — | PARTIAL_DATA |
| 2023-03 | GLDRUBF | 0 | 0 | 0 | 0 | — | — | — | — | NO_COVERAGE |
| 2023-03 | IMOEXF | 0 | 0 | 0 | 0 | — | — | — | — | NO_COVERAGE |
| 2023-04 | USDRUBF | 20 | 5 | 5 | 0 | 3.481481 | 2.281532 | 2.133283 | 0.426657 | PARTIAL_DATA |
| 2023-04 | CNYRUBF | 4 | 1 | 0 | 1 | — | — | 0.000000 | — | UNKNOWN |
| 2023-04 | GLDRUBF | 0 | 0 | 0 | 0 | — | — | — | — | NO_COVERAGE |
| 2023-04 | IMOEXF | 0 | 0 | 0 | 0 | — | — | — | — | NO_COVERAGE |
| 2023-05 | USDRUBF | 27 | 6 | 6 | 0 | 1.433333 | 1.424088 | 0.655861 | 0.109310 | PARTIAL_DATA |
| 2023-05 | CNYRUBF | 5 | 0 | 0 | 1 | — | — | 0.000000 | — | UNKNOWN |
| 2023-05 | GLDRUBF | 0 | 0 | 0 | 0 | — | — | — | — | NO_COVERAGE |
| 2023-05 | IMOEXF | 0 | 0 | 0 | 0 | — | — | — | — | NO_COVERAGE |
| 2023-06 | USDRUBF | 19 | 7 | 7 | 0 | 1.272727 | 2.959632 | 2.994589 | 0.427798 | PARTIAL_DATA |
| 2023-06 | CNYRUBF | 4 | 2 | 0 | 2 | — | — | 0.000000 | — | UNKNOWN |
| 2023-06 | GLDRUBF | 0 | 0 | 0 | 0 | — | — | — | — | NO_COVERAGE |
| 2023-06 | IMOEXF | 0 | 0 | 0 | 0 | — | — | — | — | NO_COVERAGE |
| 2023-07 | USDRUBF | 27 | 6 | 6 | 0 | 0.320000 | 0.135683 | -3.088551 | -0.514759 | PARTIAL_DATA |
| 2023-07 | CNYRUBF | 5 | 0 | 0 | 0 | — | — | 0.000000 | — | PARTIAL_DATA |
| 2023-07 | GLDRUBF | 5 | 2 | 0 | 2 | — | — | 0.000000 | — | UNKNOWN |
| 2023-07 | IMOEXF | 0 | 0 | 0 | 0 | — | — | — | — | NO_COVERAGE |
| 2023-08 | USDRUBF | 29 | 8 | 8 | 0 | 0.076923 | 0.030573 | -6.746418 | -0.843302 | PARTIAL_DATA |
| 2023-08 | CNYRUBF | 9 | 1 | 1 | 0 | 0.000000 | 0.000000 | -1.333333 | -1.333333 | PARTIAL_DATA |
| 2023-08 | GLDRUBF | 9 | 1 | 0 | 2 | — | — | 0.000000 | — | UNKNOWN |
| 2023-08 | IMOEXF | 0 | 0 | 0 | 0 | — | — | — | — | NO_COVERAGE |
| 2023-09 | USDRUBF | 35 | 7 | 7 | 0 | 1.253968 | 1.160475 | 0.619176 | 0.088454 | PARTIAL_DATA |
| 2023-09 | CNYRUBF | 11 | 2 | 2 | 0 | 1.411765 | 3.529412 | 2.866667 | 1.433333 | PARTIAL_DATA |
| 2023-09 | GLDRUBF | 10 | 2 | 2 | 0 | 0.000000 | 0.000000 | -2.082694 | -1.041347 | PARTIAL_DATA |
| 2023-09 | IMOEXF | 0 | 0 | 0 | 0 | — | — | — | — | NO_COVERAGE |
| 2023-10 | USDRUBF | 31 | 8 | 8 | 0 | 0.719512 | 1.264881 | 0.776268 | 0.097033 | CONDITIONAL_AFTER_UNKNOWN |
| 2023-10 | CNYRUBF | 36 | 10 | 10 | 0 | 1.117188 | 1.291333 | 1.224322 | 0.122432 | PARTIAL_DATA |
| 2023-10 | GLDRUBF | 17 | 7 | 3 | 4 | 0.426295 | 0.673601 | -0.362572 | -0.120857 | UNKNOWN |
| 2023-10 | IMOEXF | 0 | 0 | 0 | 0 | — | — | — | — | NO_COVERAGE |
| 2023-11 | USDRUBF | 22 | 3 | 3 | 0 | 0.000000 | 0.000000 | -1.913165 | -0.637722 | PARTIAL_DATA |
| 2023-11 | CNYRUBF | 29 | 7 | 7 | 0 | 1.185185 | 0.455955 | -1.316635 | -0.188091 | PARTIAL_DATA |
| 2023-11 | GLDRUBF | 24 | 6 | 4 | 3 | — | — | 2.578923 | 0.644731 | UNKNOWN |
| 2023-11 | IMOEXF | 1 | 0 | 0 | 0 | — | — | 0.000000 | — | PARTIAL_DATA |
| 2023-12 | USDRUBF | 21 | 4 | 4 | 0 | 2.000000 | 2.176982 | 1.356922 | 0.339230 | CONDITIONAL_AFTER_UNKNOWN |
| 2023-12 | CNYRUBF | 28 | 8 | 8 | 0 | 0.592233 | 0.685564 | -1.654970 | -0.206871 | CONDITIONAL_AFTER_UNKNOWN |
| 2023-12 | GLDRUBF | 20 | 2 | 2 | 0 | 0.000000 | 0.000000 | -1.244726 | -0.622363 | PARTIAL_DATA |
| 2023-12 | IMOEXF | 16 | 4 | 1 | 3 | 0.000000 | 0.000000 | -1.500000 | -1.500000 | UNKNOWN |

## Coverage and UNKNOWN

| Instrument | Rows 2023 | First observation | Complete/incomplete/pre-inception days | Missing/invalid M5 |
|---|---|---|---|---|
| USDRUBF | 42576 | 2023-01-03 09:00:00+03:00 | 224/30/0 | 187/0 |
| CNYRUBF | 39362 | 2023-01-03 09:00:00+03:00 | 82/172/0 | 1270/0 |
| GLDRUBF | 18428 | 2023-07-11 10:00:00+03:00 | 5/119/130 | 932/0 |
| IMOEXF | 4429 | 2023-11-14 10:00:00+03:00 | 2/32/220 | 566/0 |

Coverage uses the entire accepted research windows, including post-17:00 slots, conservatively. No OHLCV filled. Missing waiting rejects before order submission; missing entry Open is UNKNOWN possible fill. Missing exposed/exit path is UNKNOWN with blank P&L. UNKNOWN blocks its day; subsequent independent research days assume FLAT conditionally. Annual equity and Max DD are unconfirmed.

## Validation, isolation and classification

Independent batch H1/M15/signal and forward-path oracle imports no production strategy, core or metrics. It verifies lineage, availability, gaps, signals, ledger, C1 and CSV-only economics. This is independent implementation verification by the task agent, not external human acceptance. See Independent_Audit.md / audit.json.
validation.json records technical tests, two full repeats with byte equality, complete reruns and independent audits of ORB A BASE, R17, R16, Level Rejection and Swing Pullback. Old stored results and M5 strategies remain byte unchanged. The shared Backtester adds only the approved M15 clock; this adapter owns no orders, positions or P&L. TradingSystemLab and all paths outside IntradayLab are unchanged.
Predeclared evidence policy: complete coverage/outcomes, >=30 closures, >=15 trade days, >=3 active and positive months, >=60% positive active months, positive C1 expectancy, both PF >=1.6, largest winner <=25% and largest positive month <=50%. Incomplete coverage/outcomes gives INCONCLUSIVE; negative known expectancy gives separate NO ECONOMIC BASELINE PASS diagnosis. Controlled annual drawdown cannot be certified without full coverage.
Reproduce: `python3 IntradayLab/tools/run_trend_pullback_baseline.py --data-root /workspace/market-pattern-data --output IntradayLab/work/trend_replay` then the matching `audit_trend_pullback_baseline.py` command.
Pinned source `f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8`; only exact 2023 prefixes. Zero 2024/2025+ price bytes. No selection of profitable instruments/directions/months.
Stops after Draft PR. No Merge, Optimization, Robustness, Walk Forward, TRUE OOS or LIVE.
