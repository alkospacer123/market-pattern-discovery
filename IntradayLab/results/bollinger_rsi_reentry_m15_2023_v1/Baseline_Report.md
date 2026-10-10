# BOLLINGER_RSI_REENTRY_M15 — Baseline 2023

**Research phase: BASELINE. Classification: INCONCLUSIVE.**

One user-supplied fixed hypothesis, all four instruments and all available 2023. No selection or tuning.
Economics are conditional known closures after C1. Annual Net R, PF, expectancy, win rate and DD remain null with incomplete coverage/UNKNOWN. Price P&L is never pooled across instruments.

## Frozen parameters and causal rules

| Parameter | Value |
|---|---|
| bollinger_ddof | 0 |
| bollinger_period | 20 |
| bollinger_stddev | 2.0 |
| confirmation_bars | 1 |
| cost | C1 |
| daily_trade_deadline | 17:00 |
| directions | ['LONG', 'SHORT'] |
| m15_children_m5 | 3 |
| max_hold_calendar_minutes | 120 |
| min_entry_to_flat_minutes | 35 |
| min_initial_risk_ticks | 4 |
| rsi_long_threshold | 35 |
| rsi_method | WILDER |
| rsi_period | 14 |
| rsi_short_threshold | 65 |
| signal_tf | M15 |
| stop_buffer_ticks | 1 |
| target_mode | FULL_NET_C1_R |
| target_net_R | 1.5 |
| wait_complete_m15_bars | 1 |

Pre-P&L commit `9c2013ea249f1a27a65ac99d8acd81c91c312b5d`; config SHA-256 `997ccb003f4fe122523f8552ffbf102402c3b751d33aa78b9254324d265e01e7`. Executable research hashes in provenance.json and config. All checked before source reading.

- **B_C:** Adjacent calendar M15 in one approved window/day. LONG B close<own lower and RSI<=35; C within own inclusive bands and RSI_C>RSI_B. SHORT mirrored >upper, RSI>=65, RSI_C<RSI_B. No other filters.
- **M15:** Existing aggregate_m15: three consecutive valid completed M5, aligned full calendar M15 inside research windows. Incomplete parent never supplies Close; known first Open is retained only for shared execution.
- **entry:** C Close -> complete waiting D -> E Open. Shared Open-only side/grid/minimum four-tick risk. One pending/open position per instrument.
- **exit:** Unchanged common Stop-first, adverse Stop gap, no entry-bar Take, C1 one dated tick each side. Hold120 calendar minutes or earlier session flat/deadline17:00.
- **indicators:** Close of 20 real completed M15, inclusive current: SMA20 plus/minus 2 population sigma (ddof=0). RSI14 seeds 14 real close changes and uses Wilder smoothing. Both zero=>50; no loss=>100; no gain=>0.
- **reserve:** 35 minutes from planned E Open to min(shared actual mandatory M15 session-flat Open,17:00). No shortening after P&L.
- **selection:** Single fixed user hypothesis; no alternate thresholds/filters/instrument selection or optimization.
- **stop:** Fixed at C close: LONG min(B.low,C.low)-one historical signal tick; SHORT max(B.high,C.high)+one tick.
- **target:** Shared FULL_NET_C1_R 1.5: distance=1.5*risk+5*entry_tick, rounded outward. Report gross-risk R and full net/net separately.
- **unknown:** Missing waiting rejects; missing execution Open => UNKNOWN possible fill; incomplete exposed/exit path => UNKNOWN. No P&L. Current day blocked; next day conditionally FLAT.
- **warmup:** Explicit cross-session/day real Close history from pinned 2023 only; no synthetic break observations. Every expected missing/incomplete M15 clears all warm-up. No outside-window/native-M15/future substitution.

## Signals → Pending → Orders → Model fills → CLOSED / UNKNOWN

| Instrument | M15 decisions | Ready | B candidates | Signals | Pending | Orders | Fills | CLOSED | UNKNOWN |
|---|---|---|---|---|---|---|---|---|---|
| USDRUBF | 8636 | 7929 | 676 | 249 | 141 | 141 | 129 | 128 | 1 |
| CNYRUBF | 8636 | 3552 | 305 | 101 | 60 | 60 | 48 | 44 | 4 |
| GLDRUBF | 4216 | 485 | 28 | 14 | 9 | 9 | 7 | 5 | 2 |
| IMOEXF | 1156 | 119 | 7 | 4 | 3 | 3 | 3 | 3 | 0 |

## Conditional known C1 economics

| Instrument | Closed | Days | PF price | PF R | Net R | Expectancy R | Win rate | Conditional DD R |
|---|---|---|---|---|---|---|---|---|
| USDRUBF | 128 | 112 | 0.831220 | 0.811102 | -12.253218 | -0.095728 | 0.382812 | 13.382531 |
| CNYRUBF | 44 | 39 | 0.870343 | 0.849212 | -2.760678 | -0.062743 | 0.363636 | 5.342790 |
| GLDRUBF | 5 | 5 | 0.330677 | 0.186924 | -3.438395 | -0.687679 | 0.200000 | 4.228871 |
| IMOEXF | 3 | 2 | 0.097561 | 0.076996 | -2.084828 | -0.694943 | 0.333333 | 2.258741 |

| Instrument | Avg win R | Avg loss R | Avg win price | Avg loss price | Largest winner share | Top 3 share | Largest positive month share |
|---|---|---|---|---|---|---|---|
| USDRUBF | 1.073744 | -0.842425 | 0.214082 | -0.163896 | 0.041814 | 0.121642 | 0.905891 |
| CNYRUBF | 0.971731 | -0.704168 | 0.036500 | -0.025808 | 0.128636 | 0.349519 | 0.534655 |
| GLDRUBF | 0.790476 | -1.057218 | 8.300000 | -6.275000 | 1.000000 | 1.000000 | 1.000000 |
| IMOEXF | 0.173913 | -1.129371 | 2.000000 | -10.250000 | 1.000000 | 1.000000 | — |

## Frequency and calendar regularity

| Instrument | Positive /12 | Positive /active | Worst known month | Worst Net R | Fills /available day |
|---|---|---|---|---|---|
| USDRUBF | 0.250000 | 0.250000 | 2023-11 | -6.639879 | 0.507874 |
| CNYRUBF | 0.166667 | 0.222222 | 2023-11 | -1.826782 | 0.188976 |
| GLDRUBF | 0.083333 | 0.333333 | 2023-10 | -2.141949 | 0.056452 |
| IMOEXF | 0.000000 | 0.000000 | 2023-12 | -2.084828 | 0.088235 |

Zero-trade months and NO_COVERAGE are never positive. Known monthly sums are conditional, not confirmed full calendar returns. Calendar-admissible entry slots are in calendar_reachability.json.

## FULL_NET_C1_R 1.5 and exits

The shared target distance is 1.5 × initial gross risk + 5 entry ticks, rounded outward. Planned net/net ratio uses (risk + 2 ticks); net_R_c1 uses initial gross risk. Realized exit C1 uses its historical dated tick.

| Instrument | Available days | Fill days | No-fill days | Pending /signals | Orders /signals | Fills /orders |
|---|---|---|---|---|---|---|
| USDRUBF | 254 | 113 | 141 | 0.566265 | 0.566265 | 0.914894 |
| CNYRUBF | 254 | 43 | 211 | 0.594059 | 0.594059 | 0.800000 |
| GLDRUBF | 124 | 7 | 117 | 0.642857 | 0.642857 | 0.777778 |
| IMOEXF | 34 | 2 | 32 | 0.750000 | 0.750000 | 1.000000 |

| Instrument | Plan min | Plan max | TAKE | TAKE /closed | Actual TAKE min | Actual TAKE max | Closed ≥1.5 net/net | Filled UNKNOWN |
|---|---|---|---|---|---|---|---|---|
| USDRUBF | 1.500000 | 1.571429 | 23 | 0.179688 | 1.500000 | 1.571429 | 23 | 1 |
| CNYRUBF | 1.500000 | 1.571429 | 7 | 0.159091 | 1.500000 | 1.523810 | 7 | 4 |
| GLDRUBF | 1.500000 | 1.514286 | 0 | 0.000000 | — | — | 0 | 2 |
| IMOEXF | 1.500000 | 1.538462 | 0 | 0.000000 | — | — | 0 | 0 |

USDRUBF: **INCONCLUSIVE**; conditional diagnosis **NO ECONOMIC BASELINE PASS**.
Exit counts / costs / targets: `{"actual_Take_net_net_R_max": "1.571428571428571428571428571", "actual_Take_net_net_R_min": "1.5", "adverse_Stop_gaps": 1, "cost_R_known_closed": "16.25745255192586680883814631", "cost_price_known_closed": "2.56", "exit_reasons": {"SESSION_FLAT": 17, "STOP": 45, "TAKE": 23, "TIME": 28, "TRADE_DEADLINE": 15}, "gross_R_known_closed": "4.004234737788161015310710339", "gross_price_known_closed": "0.43", "initial_R_denominator": "initial gross price risk; unchanged common metric contract", "known_closures_reaching_full_net_1_5R": 23, "mean_positive_realized_net_net_R": "0.9292981310858186520928006035", "planned_full_net_R_max": "1.571428571428571428571428571", "planned_full_net_R_min": "1.5", "target_hit_closed": 23, "target_hit_fraction_known_closed": "0.1796875", "target_ratio_denominator": "initial gross risk + round-trip C1", "unresolved_filled_targets": 1}`.
Rejected checks: `{"B_NOT_READY_OR_BOUNDARY": 497, "INDICATORS_NOT_READY": 624, "INVALID_RISK": 6, "M15_INVALID_BAR": 21, "M15_MISSING_BAR": 62, "NO_BREACH_B": 6756, "NO_REENTRY_C": 385, "NO_RSI_IMPROVEMENT": 42, "POSITION_BUSY": 3, "RISK_BELOW_FOUR_TICKS": 6, "SESSION_ENTRY_CUTOFF": 21, "SESSION_LIMIT": 8, "TRADE_DEADLINE": 76}`.
UNKNOWN: `{"MISSING_EXPOSED_BAR": 1}`.
Evidence checks: `{"PF_goal_met": false, "complete": false, "concentration_acceptable": false, "enough_sample": true, "monthly_stability": false, "positive_expectancy": false}`.

CNYRUBF: **INCONCLUSIVE**; conditional diagnosis **NO ECONOMIC BASELINE PASS**.
Exit counts / costs / targets: `{"actual_Take_net_net_R_max": "1.523809523809523809523809524", "actual_Take_net_net_R_min": "1.5", "adverse_Stop_gaps": 0, "cost_R_known_closed": "6.221389563905839857835042911", "cost_price_known_closed": "0.304", "exit_reasons": {"SESSION_FLAT": 8, "STOP": 11, "TAKE": 7, "TIME": 13, "TRADE_DEADLINE": 5}, "gross_R_known_closed": "3.460711959642083796951164297", "gross_price_known_closed": "0.217", "initial_R_denominator": "initial gross price risk; unchanged common metric contract", "known_closures_reaching_full_net_1_5R": 7, "mean_positive_realized_net_net_R": "0.8612278228458156401488106419", "planned_full_net_R_max": "1.571428571428571428571428571", "planned_full_net_R_min": "1.5", "target_hit_closed": 7, "target_hit_fraction_known_closed": "0.1590909090909090909090909091", "target_ratio_denominator": "initial gross risk + round-trip C1", "unresolved_filled_targets": 4}`.
Rejected checks: `{"B_NOT_READY_OR_BOUNDARY": 280, "INDICATORS_NOT_READY": 4109, "INVALID_RISK": 3, "M15_INVALID_BAR": 551, "M15_MISSING_BAR": 424, "NO_BREACH_B": 2967, "NO_REENTRY_C": 177, "NO_RSI_IMPROVEMENT": 27, "POSITION_BUSY": 1, "RISK_BELOW_FOUR_TICKS": 9, "SESSION_ENTRY_CUTOFF": 4, "SESSION_LIMIT": 1, "TRADE_DEADLINE": 35}`.
UNKNOWN: `{"INVALID_EXPOSED_BAR": 4}`.
Evidence checks: `{"PF_goal_met": false, "complete": false, "concentration_acceptable": false, "enough_sample": true, "monthly_stability": false, "positive_expectancy": false}`.

GLDRUBF: **INCONCLUSIVE**; conditional diagnosis **NO ECONOMIC BASELINE PASS**.
Exit counts / costs / targets: `{"actual_Take_net_net_R_max": null, "actual_Take_net_net_R_min": null, "adverse_Stop_gaps": 0, "cost_R_known_closed": "0.2479186216697367455619016726", "cost_price_known_closed": "1.0", "exit_reasons": {"SESSION_FLAT": 1, "STOP": 4}, "gross_R_known_closed": "-3.190476190476190476190476190", "gross_price_known_closed": "-15.8", "initial_R_denominator": "initial gross price risk; unchanged common metric contract", "known_closures_reaching_full_net_1_5R": 0, "mean_positive_realized_net_net_R": "0.7757009345794392523364485981", "planned_full_net_R_max": "1.514285714285714285714285714", "planned_full_net_R_min": "1.5", "target_hit_closed": 0, "target_hit_fraction_known_closed": "0", "target_ratio_denominator": "initial gross risk + round-trip C1", "unresolved_filled_targets": 2}`.
Rejected checks: `{"B_NOT_READY_OR_BOUNDARY": 56, "INDICATORS_NOT_READY": 2965, "INVALID_RISK": 2, "M15_INVALID_BAR": 477, "M15_MISSING_BAR": 289, "NO_BREACH_B": 401, "NO_REENTRY_C": 11, "NO_RSI_IMPROVEMENT": 3, "SESSION_ENTRY_CUTOFF": 2, "TRADE_DEADLINE": 3}`.
UNKNOWN: `{"MISSING_EXPOSED_BAR": 2}`.
Evidence checks: `{"PF_goal_met": false, "complete": false, "concentration_acceptable": false, "enough_sample": false, "monthly_stability": false, "positive_expectancy": false}`.

IMOEXF: **INCONCLUSIVE**; conditional diagnosis **NO ECONOMIC BASELINE PASS**.
Exit counts / costs / targets: `{"actual_Take_net_net_R_max": null, "actual_Take_net_net_R_min": null, "adverse_Stop_gaps": 0, "cost_R_known_closed": "0.3456977804803891760413499544", "cost_price_known_closed": "3.0", "exit_reasons": {"STOP": 2, "TIME": 1}, "gross_R_known_closed": "-1.739130434782608695652173913", "gross_price_known_closed": "-15.5", "initial_R_denominator": "initial gross price risk; unchanged common metric contract", "known_closures_reaching_full_net_1_5R": 0, "mean_positive_realized_net_net_R": "0.16", "planned_full_net_R_max": "1.538461538461538461538461538", "planned_full_net_R_min": "1.5", "target_hit_closed": 0, "target_hit_fraction_known_closed": "0", "target_ratio_denominator": "initial gross risk + round-trip C1", "unresolved_filled_targets": 0}`.
Rejected checks: `{"B_NOT_READY_OR_BOUNDARY": 11, "INDICATORS_NOT_READY": 650, "M15_INVALID_BAR": 225, "M15_MISSING_BAR": 162, "NO_BREACH_B": 101, "NO_REENTRY_C": 3, "TRADE_DEADLINE": 1}`.
UNKNOWN: `{}`.
Evidence checks: `{"PF_goal_met": false, "complete": false, "concentration_acceptable": false, "enough_sample": false, "monthly_stability": false, "positive_expectancy": false}`.

## LONG / SHORT

| Instrument | Side | Signals | Fills | Closed | UNKNOWN | PF price | PF R | Net R | Expectancy R |
|---|---|---|---|---|---|---|---|---|---|
| USDRUBF | SHORT | 156 | 81 | 80 | 1 | 0.692875 | 0.712195 | -11.924939 | -0.149062 |
| USDRUBF | LONG | 93 | 48 | 48 | 0 | 1.082589 | 0.985990 | -0.328279 | -0.006839 |
| CNYRUBF | SHORT | 50 | 22 | 19 | 3 | 0.954545 | 1.098976 | 0.665247 | 0.035013 |
| CNYRUBF | LONG | 51 | 26 | 25 | 1 | 0.807792 | 0.704332 | -3.425925 | -0.137037 |
| GLDRUBF | SHORT | 5 | 2 | 2 | 0 | 0.000000 | 0.000000 | -2.043265 | -1.021632 |
| GLDRUBF | LONG | 9 | 5 | 3 | 2 | 1.566038 | 0.361674 | -1.395130 | -0.465043 |
| IMOEXF | SHORT | 2 | 2 | 2 | 0 | 0.000000 | 0.000000 | -2.258741 | -1.129371 |
| IMOEXF | LONG | 2 | 1 | 1 | 0 | — | — | 0.173913 | 0.173913 |

## All twelve calendar months

| Month | Instrument | Signals | Fills | Closed | UNKNOWN | PF price | PF R | Net R | Expectancy R | Coverage |
|---|---|---|---|---|---|---|---|---|---|---|
| 2023-01 | USDRUBF | 18 | 6 | 6 | 0 | 0.397959 | 0.524520 | -1.990752 | -0.331792 | PARTIAL_DATA |
| 2023-01 | CNYRUBF | 4 | 1 | 1 | 0 | — | — | 0.000000 | 0.000000 | PARTIAL_DATA |
| 2023-01 | GLDRUBF | 0 | 0 | 0 | 0 | — | — | — | — | NO_COVERAGE |
| 2023-01 | IMOEXF | 0 | 0 | 0 | 0 | — | — | — | — | NO_COVERAGE |
| 2023-02 | USDRUBF | 13 | 6 | 6 | 0 | 0.508475 | 0.267236 | -2.952381 | -0.492063 | PARTIAL_DATA |
| 2023-02 | CNYRUBF | 3 | 0 | 0 | 0 | — | — | 0.000000 | — | PARTIAL_DATA |
| 2023-02 | GLDRUBF | 0 | 0 | 0 | 0 | — | — | — | — | NO_COVERAGE |
| 2023-02 | IMOEXF | 0 | 0 | 0 | 0 | — | — | — | — | NO_COVERAGE |
| 2023-03 | USDRUBF | 24 | 15 | 15 | 0 | 0.762238 | 1.097597 | 0.811127 | 0.054075 | PARTIAL_DATA |
| 2023-03 | CNYRUBF | 1 | 1 | 0 | 1 | — | — | 0.000000 | — | UNKNOWN |
| 2023-03 | GLDRUBF | 0 | 0 | 0 | 0 | — | — | — | — | NO_COVERAGE |
| 2023-03 | IMOEXF | 0 | 0 | 0 | 0 | — | — | — | — | NO_COVERAGE |
| 2023-04 | USDRUBF | 16 | 8 | 8 | 0 | 0.247059 | 0.584992 | -1.391210 | -0.173901 | PARTIAL_DATA |
| 2023-04 | CNYRUBF | 4 | 2 | 1 | 1 | 0.000000 | 0.000000 | -0.400000 | -0.400000 | UNKNOWN |
| 2023-04 | GLDRUBF | 0 | 0 | 0 | 0 | — | — | — | — | NO_COVERAGE |
| 2023-04 | IMOEXF | 0 | 0 | 0 | 0 | — | — | — | — | NO_COVERAGE |
| 2023-05 | USDRUBF | 19 | 11 | 11 | 0 | 1.202128 | 0.998378 | -0.008971 | -0.000816 | PARTIAL_DATA |
| 2023-05 | CNYRUBF | 2 | 1 | 1 | 0 | 0.000000 | 0.000000 | -1.400000 | -1.400000 | PARTIAL_DATA |
| 2023-05 | GLDRUBF | 0 | 0 | 0 | 0 | — | — | — | — | NO_COVERAGE |
| 2023-05 | IMOEXF | 0 | 0 | 0 | 0 | — | — | — | — | NO_COVERAGE |
| 2023-06 | USDRUBF | 25 | 12 | 11 | 1 | 0.760000 | 1.018444 | 0.072720 | 0.006611 | UNKNOWN |
| 2023-06 | CNYRUBF | 2 | 1 | 0 | 1 | — | — | 0.000000 | — | UNKNOWN |
| 2023-06 | GLDRUBF | 0 | 0 | 0 | 0 | — | — | — | — | NO_COVERAGE |
| 2023-06 | IMOEXF | 0 | 0 | 0 | 0 | — | — | — | — | NO_COVERAGE |
| 2023-07 | USDRUBF | 16 | 9 | 9 | 0 | 1.087912 | 0.481531 | -2.750480 | -0.305609 | PARTIAL_DATA |
| 2023-07 | CNYRUBF | 4 | 2 | 2 | 0 | — | — | 2.000000 | 1.000000 | PARTIAL_DATA |
| 2023-07 | GLDRUBF | 0 | 0 | 0 | 0 | — | — | 0.000000 | — | PARTIAL_DATA |
| 2023-07 | IMOEXF | 0 | 0 | 0 | 0 | — | — | — | — | NO_COVERAGE |
| 2023-08 | USDRUBF | 32 | 11 | 11 | 0 | 1.362745 | 0.960853 | -0.164911 | -0.014992 | PARTIAL_DATA |
| 2023-08 | CNYRUBF | 20 | 6 | 5 | 1 | 1.272727 | 0.650382 | -0.568570 | -0.113714 | UNKNOWN |
| 2023-08 | GLDRUBF | 1 | 1 | 0 | 1 | — | — | 0.000000 | — | UNKNOWN |
| 2023-08 | IMOEXF | 0 | 0 | 0 | 0 | — | — | — | — | NO_COVERAGE |
| 2023-09 | USDRUBF | 11 | 8 | 8 | 0 | 0.860759 | 0.396549 | -2.990183 | -0.373773 | PARTIAL_DATA |
| 2023-09 | CNYRUBF | 7 | 2 | 2 | 0 | 0.000000 | 0.000000 | -1.291667 | -0.645833 | PARTIAL_DATA |
| 2023-09 | GLDRUBF | 0 | 0 | 0 | 0 | — | — | 0.000000 | — | PARTIAL_DATA |
| 2023-09 | IMOEXF | 0 | 0 | 0 | 0 | — | — | — | — | NO_COVERAGE |
| 2023-10 | USDRUBF | 25 | 16 | 16 | 0 | 3.072464 | 3.697632 | 8.507906 | 0.531744 | CONDITIONAL_AFTER_UNKNOWN |
| 2023-10 | CNYRUBF | 18 | 11 | 11 | 0 | 2.482759 | 1.437162 | 1.740728 | 0.158248 | PARTIAL_DATA |
| 2023-10 | GLDRUBF | 5 | 3 | 2 | 1 | 0.000000 | 0.000000 | -2.141949 | -1.070975 | UNKNOWN |
| 2023-10 | IMOEXF | 0 | 0 | 0 | 0 | — | — | — | — | NO_COVERAGE |
| 2023-11 | USDRUBF | 27 | 13 | 13 | 0 | 0.247423 | 0.349707 | -6.639879 | -0.510760 | PARTIAL_DATA |
| 2023-11 | CNYRUBF | 15 | 8 | 8 | 0 | 0.403101 | 0.603128 | -1.826782 | -0.228348 | PARTIAL_DATA |
| 2023-11 | GLDRUBF | 3 | 2 | 2 | 0 | 0.000000 | 0.000000 | -2.086922 | -1.043461 | PARTIAL_DATA |
| 2023-11 | IMOEXF | 0 | 0 | 0 | 0 | — | — | 0.000000 | — | PARTIAL_DATA |
| 2023-12 | USDRUBF | 23 | 14 | 14 | 0 | 0.641892 | 0.640999 | -2.756203 | -0.196872 | CONDITIONAL_AFTER_UNKNOWN |
| 2023-12 | CNYRUBF | 21 | 13 | 13 | 0 | 0.831169 | 0.797350 | -1.014387 | -0.078030 | CONDITIONAL_AFTER_UNKNOWN |
| 2023-12 | GLDRUBF | 5 | 1 | 1 | 0 | — | — | 0.790476 | 0.790476 | PARTIAL_DATA |
| 2023-12 | IMOEXF | 4 | 3 | 3 | 0 | 0.097561 | 0.076996 | -2.084828 | -0.694943 | PARTIAL_DATA |

## Coverage and UNKNOWN

| Instrument | Rows 2023 | First observation | Complete/incomplete/pre-inception days | Missing/invalid M5 |
|---|---|---|---|---|
| USDRUBF | 42576 | 2023-01-03 09:00:00+03:00 | 224/30/0 | 187/0 |
| CNYRUBF | 39362 | 2023-01-03 09:00:00+03:00 | 82/172/0 | 1270/0 |
| GLDRUBF | 18428 | 2023-07-11 10:00:00+03:00 | 5/119/130 | 932/0 |
| IMOEXF | 4429 | 2023-11-14 10:00:00+03:00 | 2/32/220 | 566/0 |

Only exact3 real M5 parents within approved full M15 calendar windows are observations. Indicator warm-up explicitly crosses real sessions/days but resets on every expected missing/incomplete parent. B/C reset at each day/window. Native M15 and future history are never read.
Coverage conservatively includes entire approved M5 windows. No interpolation. Missing waiting rejects; missing first entry Open is UNKNOWN possible fill; observed Open with incomplete path may fill then become UNKNOWN. UNKNOWN keeps blank P&L and blocks its day. Next research day only conditionally assumes FLAT; no continuous equity claim.

## Classification and verification

Policy is copied unchanged from PR #471: complete data/outcomes, ≥30 CLOSED, ≥15 trade days, ≥3 active/positive months, ≥60% positive active months, positive C1 expectancy, both PF ≥1.6, largest winner ≤25%, largest positive month ≤50%. Incomplete coverage/outcomes => INCONCLUSIVE; negative known expectancy => separate NO ECONOMIC BASELINE PASS. Positive subsets cannot select new instruments/directions.
Independent oracle rebuilds exact3 parents, Bollinger population variance, Wilder RSI from weighted raw changes, adjacent B/C and forward execution without production strategy/indicators/Backtester/metrics imports. CSV-only metrics, all CLOSED/UNKNOWN, 12 months, coverage and corruption checks are audited. See Independent_Audit.md and audit.json.
validation.json records the full IntradayLab test suite, two byte-identical repeats, six old Baseline regressions, and byte preservation of every existing file. Common core is unchanged. No changes outside IntradayLab.
Pinned read-only source `f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8`; unbuffered exact 2023 byte prefixes. Zero price bytes 2024+. Independent LF-budget reader verifies the same hashes.
Reproduce: `python3 IntradayLab/tools/run_bollinger_rsi_reentry_baseline.py --data-root /workspace/market-pattern-data` then matching audit and validate tools.
Stops after one Draft PR. No Merge, Optimization, Robustness, Walk Forward, TRUE OOS or LIVE.

## Independent audit limitation — frozen numeric comparison

**Signal logic audit: NEEDS_FIX.** Exact numeric-program, execution, trade, economic and coverage checks pass. Mathematical Wilder RSI is unchanged on a flat Close; two frozen formal signals come from Decimal28 last-digit drift. One failed the deadline, one failed minimum risk. No filled trade/P&L changed, but a complete technical signal PASS is withheld.

- `USDRUBF_2023-03-16_1800`: frozen SIGNAL, mathematical NO_RSI_IMPROVEMENT; REJECTED / TRADE_DEADLINE. B/C Close=76.87; RSI 74.43901149162470461788723299 → 74.43901149162470461788723298.
- `CNYRUBF_2023-08-14_1100`: frozen SIGNAL, mathematical NO_RSI_IMPROVEMENT; NONFILL / RISK_BELOW_FOUR_TICKS. B/C Close=13.9; RSI 87.72075370164252626441372009 → 87.72075370164252626441372008.

Canonical signal/pending/order counts are retained, including these two events. Mathematical-oracle funnel diagnostics appear in audit.json. No parameter, indicator or rule changed after P&L. Original auditor remains frozen and fails standalone; final verifier supplies both conformance and semantic checks. No repaired variant or second economic Baseline.
