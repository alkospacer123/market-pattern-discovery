# LEVEL_REJECTION_M5 — Canonical Economic Baseline 2023

**Research phase: BASELINE. Status: INCONCLUSIVE. No automatic Optimization.**

One fixed hypothesis, one common M5 Backtester, four instruments, entire available 2023. No optimizer or alternative execution scenarios.
All economic tables below describe conditional known closures after C1, one dated historical tick per side. Confirmed annual PF, Net R, expectancy, win rate and DD stay null on incomplete coverage/UNKNOWN. Known-closure DD is a conditional diagnostic sequence, not continuous broker equity. No cross-instrument price-unit portfolio pooling.

| Instrument | Raw | Confirmed | Pending | Orders submitted | Admitted Open | Fills | Closed | UNKNOWN |
|---|---|---|---|---|---|---|---|---|
| USDRUBF | 2881 | 2135 | 916 | 916 | 623 | 623 | 614 | 9 |
| CNYRUBF | 1120 | 904 | 434 | 431 | 223 | 223 | 213 | 15 |
| GLDRUBF | 867 | 647 | 260 | 247 | 176 | 176 | 128 | 56 |
| IMOEXF | 121 | 100 | 45 | 43 | 35 | 35 | 22 | 16 |

Admitted Open means the observed scalar Open passes reclaim/risk conditions; submitted orders also include unknown possible fills and rejected Open geometry. Confirmed signals consume directional dedup even when the common engine rejects busy/time/unknown state. Raw one-sided rejection rows and DEDUP_30MIN remain in signals.csv.

| Instrument | Closed | Trade days | PF C1 price | PF C1 R | Net R | Expectancy R | Win rate | Conditional DD R | +/- months |
|---|---|---|---|---|---|---|---|---|---|
| USDRUBF | 614 | 243 | 0.607497 | 0.573855 | -213.194513 | -0.347222 | 0.270358 | 217.625068 | 2/10 |
| CNYRUBF | 213 | 99 | 0.714714 | 0.789354 | -32.741715 | -0.153717 | 0.328638 | 53.958519 | 4/7 |
| GLDRUBF | 128 | 70 | 0.656142 | 0.644927 | -36.477707 | -0.284982 | 0.226562 | 49.021233 | 2/4 |
| IMOEXF | 22 | 12 | 0.199095 | 0.120416 | -18.504856 | -0.841130 | 0.090909 | 18.504856 | 0/1 |

## Distribution, costs and realized target attainment

| Instrument | Average winner R | Average loser R | Average winner price | Average loser price | Largest winner share R | Top 3 winner share R | Largest positive month share |
|---|---|---|---|---|---|---|---|
| USDRUBF | 1.729468 | -1.137014 | 0.184518 | -0.114591 | 0.015674 | 0.047023 | 0.697010 |
| CNYRUBF | 1.752760 | -1.118237 | 0.030671 | -0.021612 | 0.034232 | 0.101065 | 0.898040 |
| GLDRUBF | 2.284661 | -1.037706 | 15.048276 | -6.718182 | 0.052246 | 0.150694 | 0.895357 |
| IMOEXF | 1.266667 | -1.107273 | 11.000000 | -5.815789 | 0.605263 | 1.000000 | — |

| Instrument | Gross R known | Cost R C1 | Take closures | Take / known closed | Actual Take net/net R min | Closures >= full-net 3R | Unresolved filled targets |
|---|---|---|---|---|---|---|---|
| USDRUBF | -69.992356 | 143.202157 | 42 | 0.068404 | 3.000000 | 42 | 9 |
| CNYRUBF | 17.836253 | 50.577968 | 19 | 0.089202 | 3.000000 | 19 | 10 |
| GLDRUBF | -30.438924 | 6.038782 | 17 | 0.132812 | 3.000000 | 17 | 48 |
| IMOEXF | -13.988095 | 4.516761 | 0 | 0.000000 | — | 0 | 13 |

Target 3R uses **net-win / net-Stop-loss**, unlike the unchanged common net_R_c1 metric using initial gross risk. Planned primary distance d_full=3s+8t, diagnostic-only d_legacy=3s+2t; targets round outward. Their geometry never guarantees the target will be reached. Actual Take closures, TIME/SESSION/STOP and UNKNOWN come from real forward 2023 paths under the one frozen execution contract. Adverse Stop gaps can exceed ideal Stop loss.

USDRUBF: status **INCONCLUSIVE**, conditional diagnosis **NO ECONOMIC BASELINE PASS**.
Funnel / dedup / busy: `{"admitted_Open_entries": 623, "closed": 614, "confirmed_signals": 2135, "dedup_30min": 746, "model_fills": 623, "pending_entries": 916, "position_busy": 462, "raw_rejections": 2881, "submitted_orders": 916, "unknown": 9, "unknown_possible_fills": 0}`.
Rejection reasons: `{"AMBIGUOUS_BOTH_SIDES": 12, "DEDUP_30MIN": 746, "OPEN_RECLAIM_NOT_PERSISTENT": 270, "POSITION_BUSY": 462, "RANGE_MISSING_BAR": 187, "RANGE_UNAVAILABLE": 508, "RISK_BELOW_FOUR_TICKS": 23, "SESSION_ENTRY_CUTOFF": 157, "SESSION_LIMIT": 59, "TRADE_DEADLINE": 517, "UNKNOWN_POSITION_BLOCK": 24}`.
UNKNOWN reasons: `{"MISSING_EXPOSED_BAR": 9}`.
Exit / target / C1 diagnostics: `{"actual_Take_net_net_R_max": "3", "actual_Take_net_net_R_min": "3", "adverse_Stop_gaps": 8, "cost_R_known_closed": "143.2021569959769992925970650", "cost_price_known_closed": "12.28", "exit_reasons": {"SESSION_FLAT": 74, "STOP": 379, "TAKE": 42, "TIME": 60, "TRADE_DEADLINE": 59}, "gross_R_known_closed": "-69.99235574357247716960008645", "gross_price_known_closed": "-7.51", "initial_R_denominator": "initial gross price risk; unchanged common metric contract", "known_closures_reaching_full_net_3R": 42, "mean_positive_realized_net_net_R": "1.393471757586084137114529473", "planned_full_net_R_max": "3", "planned_full_net_R_min": "3", "target_hit_closed": 42, "target_hit_fraction_known_closed": "0.06840390879478827361563517915", "target_ratio_denominator": "initial gross risk + round-trip C1", "unresolved_filled_targets": 9}`.
Evidence checks: `{"PF_goal_met": false, "complete": false, "concentration_acceptable": false, "enough_sample": true, "monthly_stability": false, "positive_expectancy": false}`.

CNYRUBF: status **INCONCLUSIVE**, conditional diagnosis **NO ECONOMIC BASELINE PASS**.
Funnel / dedup / busy: `{"admitted_Open_entries": 223, "closed": 213, "confirmed_signals": 904, "dedup_30min": 216, "model_fills": 223, "pending_entries": 434, "position_busy": 134, "raw_rejections": 1120, "submitted_orders": 431, "unknown": 15, "unknown_possible_fills": 5}`.
Rejection reasons: `{"AMBIGUOUS_BOTH_SIDES": 4, "DEDUP_30MIN": 216, "MISSING_EXECUTION_BAR": 5, "NO_WAITING_BAR": 3, "OPEN_RECLAIM_NOT_PERSISTENT": 144, "POSITION_BUSY": 134, "RANGE_MISSING_BAR": 1270, "RANGE_UNAVAILABLE": 508, "RISK_BELOW_FOUR_TICKS": 59, "SESSION_ENTRY_CUTOFF": 72, "SESSION_LIMIT": 23, "TRADE_DEADLINE": 226, "UNKNOWN_POSITION_BLOCK": 15}`.
UNKNOWN reasons: `{"MISSING_EXECUTION_BAR": 5, "MISSING_EXPOSED_BAR": 10}`.
Exit / target / C1 diagnostics: `{"actual_Take_net_net_R_max": "3", "actual_Take_net_net_R_min": "3", "adverse_Stop_gaps": 4, "cost_R_known_closed": "50.57796759766464640285667860", "cost_price_known_closed": "1.164", "exit_reasons": {"SESSION_FLAT": 22, "STOP": 111, "TAKE": 19, "TIME": 32, "TRADE_DEADLINE": 29}, "gross_R_known_closed": "17.83625289930928551298896874", "gross_price_known_closed": "0.307", "initial_R_denominator": "initial gross price risk; unchanged common metric contract", "known_closures_reaching_full_net_3R": 19, "mean_positive_realized_net_net_R": "1.454130231443559520785834653", "planned_full_net_R_max": "3", "planned_full_net_R_min": "3", "target_hit_closed": 19, "target_hit_fraction_known_closed": "0.08920187793427230046948356808", "target_ratio_denominator": "initial gross risk + round-trip C1", "unresolved_filled_targets": 10}`.
Evidence checks: `{"PF_goal_met": false, "complete": false, "concentration_acceptable": false, "enough_sample": true, "monthly_stability": false, "positive_expectancy": false}`.

GLDRUBF: status **INCONCLUSIVE**, conditional diagnosis **NO ECONOMIC BASELINE PASS**.
Funnel / dedup / busy: `{"admitted_Open_entries": 176, "closed": 128, "confirmed_signals": 647, "dedup_30min": 220, "model_fills": 176, "pending_entries": 260, "position_busy": 75, "raw_rejections": 867, "submitted_orders": 247, "unknown": 56, "unknown_possible_fills": 8}`.
Rejection reasons: `{"AMBIGUOUS_BOTH_SIDES": 14, "DEDUP_30MIN": 220, "MISSING_EXECUTION_BAR": 8, "NO_WAITING_BAR": 13, "OPEN_RECLAIM_NOT_PERSISTENT": 63, "POSITION_BUSY": 75, "RANGE_MISSING_BAR": 932, "RANGE_UNAVAILABLE": 248, "SESSION_ENTRY_CUTOFF": 31, "SESSION_LIMIT": 10, "TRADE_DEADLINE": 92, "UNKNOWN_POSITION_BLOCK": 179}`.
UNKNOWN reasons: `{"MISSING_EXECUTION_BAR": 8, "MISSING_EXPOSED_BAR": 48}`.
Exit / target / C1 diagnostics: `{"actual_Take_net_net_R_max": "3", "actual_Take_net_net_R_min": "3", "adverse_Stop_gaps": 7, "cost_R_known_closed": "6.038782443861774390480242608", "cost_price_known_closed": "25.6", "exit_reasons": {"SESSION_FLAT": 9, "STOP": 92, "TAKE": 17, "TIME": 4, "TRADE_DEADLINE": 6}, "gross_R_known_closed": "-30.43892421065404634021326732", "gross_price_known_closed": "-203.1", "initial_R_denominator": "initial gross price risk; unchanged common metric contract", "known_closures_reaching_full_net_3R": 17, "mean_positive_realized_net_net_R": "2.184773498154423764322816898", "planned_full_net_R_max": "3", "planned_full_net_R_min": "3", "target_hit_closed": 17, "target_hit_fraction_known_closed": "0.1328125", "target_ratio_denominator": "initial gross risk + round-trip C1", "unresolved_filled_targets": 48}`.
Evidence checks: `{"PF_goal_met": false, "complete": false, "concentration_acceptable": false, "enough_sample": true, "monthly_stability": false, "positive_expectancy": false}`.

IMOEXF: status **INCONCLUSIVE**, conditional diagnosis **NO ECONOMIC BASELINE PASS**.
Funnel / dedup / busy: `{"admitted_Open_entries": 35, "closed": 22, "confirmed_signals": 100, "dedup_30min": 21, "model_fills": 35, "pending_entries": 45, "position_busy": 15, "raw_rejections": 121, "submitted_orders": 43, "unknown": 16, "unknown_possible_fills": 3}`.
Rejection reasons: `{"AMBIGUOUS_BOTH_SIDES": 1, "DEDUP_30MIN": 21, "MISSING_EXECUTION_BAR": 3, "NO_WAITING_BAR": 2, "OPEN_RECLAIM_NOT_PERSISTENT": 4, "POSITION_BUSY": 15, "RANGE_MISSING_BAR": 566, "RANGE_UNAVAILABLE": 68, "RISK_BELOW_FOUR_TICKS": 1, "SESSION_ENTRY_CUTOFF": 4, "SESSION_LIMIT": 2, "TRADE_DEADLINE": 13, "UNKNOWN_POSITION_BLOCK": 21}`.
UNKNOWN reasons: `{"MISSING_EXECUTION_BAR": 3, "MISSING_EXPOSED_BAR": 13}`.
Exit / target / C1 diagnostics: `{"actual_Take_net_net_R_max": null, "actual_Take_net_net_R_min": null, "adverse_Stop_gaps": 1, "cost_R_known_closed": "4.516761016761016761016761015", "cost_price_known_closed": "22.0", "exit_reasons": {"SESSION_FLAT": 1, "STOP": 17, "TIME": 2, "TRADE_DEADLINE": 2}, "gross_R_known_closed": "-13.98809523809523809523809523", "gross_price_known_closed": "-66.5", "initial_R_denominator": "initial gross price risk; unchanged common metric contract", "known_closures_reaching_full_net_3R": 0, "mean_positive_realized_net_net_R": "1.132992327365728900255754476", "planned_full_net_R_max": "3", "planned_full_net_R_min": "3", "target_hit_closed": 0, "target_hit_fraction_known_closed": "0", "target_ratio_denominator": "initial gross risk + round-trip C1", "unresolved_filled_targets": 13}`.
Evidence checks: `{"PF_goal_met": false, "complete": false, "concentration_acceptable": false, "enough_sample": false, "monthly_stability": false, "positive_expectancy": false}`.

## LONG / SHORT

| Instrument | Side | Signals | Fills | Closed | UNKNOWN | PF price | PF R | Net R | Expectancy R | Win rate |
|---|---|---|---|---|---|---|---|---|---|---|
| USDRUBF | SHORT | 1098 | 319 | 312 | 7 | 0.577254 | 0.511006 | -127.240421 | -0.407822 | 0.259615 |
| USDRUBF | LONG | 1037 | 304 | 302 | 2 | 0.641621 | 0.641974 | -85.954092 | -0.284616 | 0.281457 |
| CNYRUBF | SHORT | 446 | 111 | 107 | 8 | 0.688543 | 0.657009 | -29.294997 | -0.273785 | 0.289720 |
| CNYRUBF | LONG | 458 | 112 | 106 | 7 | 0.750592 | 0.950778 | -3.446718 | -0.032516 | 0.367925 |
| GLDRUBF | SHORT | 334 | 89 | 68 | 22 | 0.502716 | 0.478639 | -29.817310 | -0.438490 | 0.191176 |
| GLDRUBF | LONG | 313 | 87 | 60 | 34 | 0.808511 | 0.853751 | -6.660396 | -0.111007 | 0.266667 |
| IMOEXF | SHORT | 43 | 15 | 9 | 7 | 0.250000 | 0.209884 | -5.772294 | -0.641366 | 0.111111 |
| IMOEXF | LONG | 57 | 20 | 13 | 9 | 0.162791 | 0.072820 | -12.732562 | -0.979428 | 0.076923 |

## All twelve calendar months

Signal-month attribution; zero closures with observed data have Net R 0 and undefined PF. Before instrument inception: NO_COVERAGE and no manufactured flat returns.

| Month | Instrument | Signals | Fills | Closed | UNKNOWN | PF price | Net R | Expectancy R | Coverage | Complete/incomplete/pre-inception days |
|---|---|---|---|---|---|---|---|---|---|---|
| 2023-01 | USDRUBF | 187 | 57 | 56 | 1 | 0.548828 | -17.396841 | -0.310658 | UNKNOWN | 16/5/0 |
| 2023-01 | CNYRUBF | 47 | 8 | 7 | 1 | 0.000000 | -5.331818 | -0.761688 | UNKNOWN | 3/18/0 |
| 2023-01 | GLDRUBF | 0 | 0 | 0 | 0 | — | — | — | NO_COVERAGE | 0/0/21 |
| 2023-01 | IMOEXF | 0 | 0 | 0 | 0 | — | — | — | NO_COVERAGE | 0/0/21 |
| 2023-02 | USDRUBF | 152 | 53 | 50 | 3 | 0.272727 | -34.568585 | -0.691372 | UNKNOWN | 15/4/0 |
| 2023-02 | CNYRUBF | 27 | 1 | 1 | 1 | — | 0.250000 | 0.250000 | UNKNOWN | 1/18/0 |
| 2023-02 | GLDRUBF | 0 | 0 | 0 | 0 | — | — | — | NO_COVERAGE | 0/0/19 |
| 2023-02 | IMOEXF | 0 | 0 | 0 | 0 | — | — | — | NO_COVERAGE | 0/0/19 |
| 2023-03 | USDRUBF | 161 | 50 | 50 | 0 | 0.544262 | -26.249579 | -0.524992 | PARTIAL_DATA | 19/3/0 |
| 2023-03 | CNYRUBF | 15 | 1 | 0 | 1 | — | 0.000000 | — | UNKNOWN | 0/22/0 |
| 2023-03 | GLDRUBF | 0 | 0 | 0 | 0 | — | — | — | NO_COVERAGE | 0/0/22 |
| 2023-03 | IMOEXF | 0 | 0 | 0 | 0 | — | — | — | NO_COVERAGE | 0/0/22 |
| 2023-04 | USDRUBF | 149 | 44 | 44 | 0 | 0.855124 | -12.947816 | -0.294269 | PARTIAL_DATA | 15/5/0 |
| 2023-04 | CNYRUBF | 29 | 5 | 4 | 1 | 1.312500 | 1.533333 | 0.383333 | UNKNOWN | 2/18/0 |
| 2023-04 | GLDRUBF | 0 | 0 | 0 | 0 | — | — | — | NO_COVERAGE | 0/0/20 |
| 2023-04 | IMOEXF | 0 | 0 | 0 | 0 | — | — | — | NO_COVERAGE | 0/0/20 |
| 2023-05 | USDRUBF | 167 | 39 | 37 | 2 | 1.526316 | 8.894255 | 0.240385 | UNKNOWN | 18/3/0 |
| 2023-05 | CNYRUBF | 44 | 4 | 3 | 1 | 0.500000 | -1.450000 | -0.483333 | UNKNOWN | 0/21/0 |
| 2023-05 | GLDRUBF | 0 | 0 | 0 | 0 | — | — | — | NO_COVERAGE | 0/0/21 |
| 2023-05 | IMOEXF | 0 | 0 | 0 | 0 | — | — | — | NO_COVERAGE | 0/0/21 |
| 2023-06 | USDRUBF | 176 | 52 | 50 | 2 | 0.486239 | -20.147336 | -0.402947 | UNKNOWN | 17/4/0 |
| 2023-06 | CNYRUBF | 35 | 4 | 2 | 4 | 0.250000 | -0.550000 | -0.275000 | UNKNOWN | 1/20/0 |
| 2023-06 | GLDRUBF | 0 | 0 | 0 | 0 | — | — | — | NO_COVERAGE | 0/0/21 |
| 2023-06 | IMOEXF | 0 | 0 | 0 | 0 | — | — | — | NO_COVERAGE | 0/0/21 |
| 2023-07 | USDRUBF | 185 | 51 | 51 | 0 | 0.684549 | -12.227856 | -0.239762 | PARTIAL_DATA | 20/1/0 |
| 2023-07 | CNYRUBF | 42 | 5 | 4 | 2 | 1.857143 | 0.022222 | 0.005556 | UNKNOWN | 2/19/0 |
| 2023-07 | GLDRUBF | 38 | 9 | 5 | 5 | 0.033937 | -3.936478 | -0.787296 | UNKNOWN | 0/15/6 |
| 2023-07 | IMOEXF | 0 | 0 | 0 | 0 | — | — | — | NO_COVERAGE | 0/0/21 |
| 2023-08 | USDRUBF | 209 | 60 | 60 | 0 | 0.457718 | -15.826522 | -0.263775 | PARTIAL_DATA | 21/2/0 |
| 2023-08 | CNYRUBF | 68 | 14 | 13 | 2 | 0.404762 | -5.410714 | -0.416209 | UNKNOWN | 9/14/0 |
| 2023-08 | GLDRUBF | 102 | 26 | 14 | 14 | 0.759097 | -0.821845 | -0.058703 | UNKNOWN | 0/23/0 |
| 2023-08 | IMOEXF | 0 | 0 | 0 | 0 | — | — | — | NO_COVERAGE | 0/0/23 |
| 2023-09 | USDRUBF | 171 | 53 | 53 | 0 | 0.420290 | -27.615605 | -0.521049 | PARTIAL_DATA | 19/2/0 |
| 2023-09 | CNYRUBF | 64 | 12 | 12 | 0 | 0.227723 | -7.615714 | -0.634643 | PARTIAL_DATA | 7/14/0 |
| 2023-09 | GLDRUBF | 96 | 24 | 16 | 11 | 1.179811 | 0.823371 | 0.051461 | UNKNOWN | 0/21/0 |
| 2023-09 | IMOEXF | 0 | 0 | 0 | 0 | — | — | — | NO_COVERAGE | 0/0/21 |
| 2023-10 | USDRUBF | 200 | 60 | 60 | 0 | 1.059603 | 3.866328 | 0.064439 | CONDITIONAL_AFTER_UNKNOWN | 22/0/0 |
| 2023-10 | CNYRUBF | 175 | 57 | 57 | 0 | 1.248134 | -3.565627 | -0.062555 | PARTIAL_DATA | 20/2/0 |
| 2023-10 | GLDRUBF | 154 | 42 | 35 | 9 | 0.290292 | -20.318607 | -0.580532 | UNKNOWN | 1/21/0 |
| 2023-10 | IMOEXF | 0 | 0 | 0 | 0 | — | — | — | NO_COVERAGE | 0/0/22 |
| 2023-11 | USDRUBF | 186 | 57 | 56 | 1 | 0.384000 | -42.027863 | -0.750498 | UNKNOWN | 21/1/0 |
| 2023-11 | CNYRUBF | 176 | 60 | 58 | 2 | 0.426710 | -26.526313 | -0.457350 | UNKNOWN | 16/6/0 |
| 2023-11 | GLDRUBF | 127 | 34 | 27 | 7 | 0.202780 | -19.269163 | -0.713673 | UNKNOWN | 1/21/0 |
| 2023-11 | IMOEXF | 13 | 4 | 0 | 6 | — | 0.000000 | — | UNKNOWN | 0/13/9 |
| 2023-12 | USDRUBF | 192 | 47 | 47 | 0 | 0.665761 | -16.947092 | -0.360576 | CONDITIONAL_AFTER_UNKNOWN | 21/0/0 |
| 2023-12 | CNYRUBF | 182 | 52 | 52 | 0 | 1.525714 | 15.902916 | 0.305825 | CONDITIONAL_AFTER_UNKNOWN | 21/0/0 |
| 2023-12 | GLDRUBF | 130 | 41 | 31 | 10 | 1.575269 | 7.045015 | 0.227259 | UNKNOWN | 3/18/0 |
| 2023-12 | IMOEXF | 87 | 31 | 22 | 10 | 0.199095 | -18.504856 | -0.841130 | UNKNOWN | 2/19/0 |

## Coverage and unresolved outcomes

| Instrument | 2023 rows | First observation | Complete/incomplete/pre-inception days | Missing/invalid research slots |
|---|---|---|---|---|
| USDRUBF | 42576 | 2023-01-03 09:00:00+03:00 | 224/30/0 | 187/0 |
| CNYRUBF | 39362 | 2023-01-03 09:00:00+03:00 | 82/172/0 | 1270/0 |
| GLDRUBF | 18428 | 2023-07-11 10:00:00+03:00 | 5/119/130 | 932/0 |
| IMOEXF | 4429 | 2023-11-14 10:00:00+03:00 | 2/32/220 | 566/0 |

Unchanged full calendar research-window coverage is assessed conservatively, including source slots outside the trade deadline. coverage_report.csv has every instrument/month; coverage_daily.csv and coverage_events.csv preserve gaps. Missing waiting bars reject before submission; missing execution Open stays UNKNOWN possible fill; missing exposed/mandatory exit observations stay UNKNOWN with blank economics. No bar or Open replacement.
UNKNOWN blocks only its research day. Later independent research days conditionally assume FLAT; this is not broker reconciliation or a confirmed continuous equity curve.

## Historical opportunity provenance and frozen adaptation

Historical freeze `1487d7e041e9e32122a5df9ae280386da8ebadb1`, six-bar Level Rejection opportunity preregistration/config, its report and runner. Historical OPPORTUNITY_FEASIBLE: 1754 T10 / 1648 T15 conditional opportunities, no Stop/Take/position/P&L. Those schedules entered at test START+20/+25. New canonical economic Baseline enters at START+10 after one full waiting M5 and simulates actual position occupancy/exits, so counts are not directly comparable.
Config and actual execution/strategy source frozen before first P&L in commit `c785d0d94133a72b97143f5b9348d6e373da7fd9`; config SHA-256 `e677ffb54d45d953d5a61f60838276b79e229d33da3ce183621aae49504cc5e4`. No outcome-driven changes.

- **Open_admission:** Common execution.entry_admission receives only scalar Open, direction, frozen Stop, observed entry tick and frozen constraints. Reclaim direction*(Open-level)>=1 entry tick; adverse risk>0 then risk>=4 entry ticks. Reasons OPEN_RECLAIM_NOT_PERSISTENT, INVALID_RISK, RISK_BELOW_FOUR_TICKS. Missing/invalid execution Open remains UNKNOWN possible fill before admission. No entry-bar Volume/HLC admission check.
- **R_reporting:** Existing gross initial price risk denominator retained for net_R_c1/PF_R. Separately record planned and realized net-win/(initial gross risk+round-trip C1); ideal Take must achieve >=3, ordinary Stop -1 in this net-stop denominator; adverse Stop gaps may lose more. Report actual Take closures versus unreachable/unknown targets.
- **Take_full_net_C1:** Optional universal entry_geometry FULL_NET_C1_R: r*(s+c)+c, c=2*observed entry tick*C1 ticks_per_side. r=3 gives d_full=3s+8t; primary target outward entry-grid rounding LONG ceiling / SHORT floor. Plan assumes equal entry/exit ticks, justified by mandatory exits <=17:00 and CNY transition at 19:00. Actual exits still charged their actual dated tick. Core records d_legacy=3s+2t as diagnostic only; not an alternative strategy or filter.
- **cost:** Common ledger one corresponding historical tick per side, no own cost or execution in strategy. No C2 or optimizer runs.
- **dedup:** Raw one-sided rejections retained; only one confirmed same-direction signal each 30 calendar minutes from prior confirmed test START, regardless of later busy/nonfill/UNKNOWN. Opposite sides separate. All full approved session test bars retained even when execution is later excluded by 17:00/reserve.
- **entry_clock:** Canonical START T -> completed signal at T+5 -> full waiting M5 T+5..T+10 -> conditional model Open T+10. One clock only, no extra T10/T15 matrix. Historical opportunity scenarios entered at START T+20 / T+25, so counts 1754 / 1648 are upper-bound historical opportunity provenance under different conditions, not matched trades.
- **exit:** 120 calendar minutes from model entry, or earlier common window.end-5-minute flat, or exact Open 17:00. Stop-first, adverse gap at Open, no Take on entry bar; no overnight carry, break-even, trailing or partial exits.
- **local_range:** Exactly six immediately preceding valid completed positive-volume grid-aligned M5, same day and continuous approved session, at 5-minute spacing. Test bar excluded. Missing/invalid/callback gap/day/window resets range and directional dedup, preserving historical analyze() behavior.
- **scope:** One fixed Baseline only; no Optimization, Robustness, Walk Forward, TRUE OOS, LIVE, next candidate or Merge.
- **signal:** LONG low<=range_low-1 dated tick AND close>=range_low+1 tick; SHORT high>=range_high+1 tick AND close<=range_high-1 tick. Both full conditions => AMBIGUOUS_BOTH_SIDES, no raw one-sided rejection or confirmed signal. No indicators or MTF filters.
- **source:** Same pinned raw 2023 byte prefixes, accepted calendar and dated tick grid. No filling, truncation for economics, or 2024/2025+ reads.
- **stop:** One signal historical tick beyond completed test extreme: LONG low-1 tick / SHORT high+1 tick. Exact source grid, no invented extrema; core validates actual entry risk and four-tick minimum.
- **time_reserve:** Causal schedule requires entry+35 minutes<=min(calendar session end, exact daily 17:00). Equality allowed. Reserve evaluated at confirmed-signal scheduling because entry time/boundary are already known. Core session flat remains end-5, so historical 35-minute reserve includes the 5-minute flatten buffer. No pending order at/after effective flat deadline.
- **unknown:** No imputed UNKNOWN economics. UNKNOWN blocks its own research day; later independent days explicitly conditionally assume FLAT. Coverage/UNKNOWN mean complete annual metrics null; conditional known closures separate.

## Computed classification, audit and regression

Existing shared assess_baseline computes the verdict. Fixed policy: complete coverage/resolved outcomes, >=30 known closures, >=15 trade days, >=3 active and positive months, >=60% positive active months, positive C1 expectancy, price and R PF >=1.6, largest winner <=25% of positive R and largest positive month <=50% of positive monthly R. Overall four-instrument assessment requires credible evidence across every declared instrument; sparse high PF is insufficient.
Independent raw-source signal/admission/forward-path oracle and CSV metric reconstruction: audit.json / Independent_Audit.md. All tests, two complete repeats, three canonical economic regressions and protected-byte checks: validation.json. Implementation independence is not external human review; PR remains Draft.
Only optional generic entry constraints and FULL_NET_C1_R geometry extend execution.py/backtester.py. All old default behavior and stored ORB/R17/R16 strategies/config/results remain unchanged; rerun result bytes match. Separate replay provenance records current core code hashes, the newly enumerated strategy, and previously merged base-main code where older runners enumerate all current strategies/metrics. Exact differences and their explanations are in validation.json. TradingSystemLab and market-pattern-data untouched.
Reproduce: `python3 IntradayLab/tools/run_level_rejection_baseline.py --data-root /workspace/market-pattern-data --output IntradayLab/work/level_rejection_replay` then `python3 IntradayLab/tools/audit_level_rejection_baseline.py --data-root /workspace/market-pattern-data --output IntradayLab/work/level_rejection_replay`.
Source commit `f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8`; exact pinned unbuffered 2023 prefixes only. Zero 2024/WF or 2025+/TRUE OOS price bytes read.
Baseline → Optimization → Robustness → Walk Forward → TRUE OOS. Stops after this Baseline and Draft PR. No Merge, next candidate, Optimization, Robustness, WF, TRUE OOS or LIVE.
