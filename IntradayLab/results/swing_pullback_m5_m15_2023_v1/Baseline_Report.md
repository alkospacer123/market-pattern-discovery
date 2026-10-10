# SWING_PULLBACK_M5_M15 — Canonical Baseline 2023

**Research phase: BASELINE. Final classification: INCONCLUSIVE.**

One initial structural hypothesis supplied before results, one fixed configuration, four instruments, entire available 2023. No Optimization or alternative scenario.
All economics below are conditional known closures after C1 (one dated tick per side). Annual complete metrics remain null on incomplete coverage/UNKNOWN. Conditional DD is not proven continuous equity. Instrument price P&L is never pooled as portfolio money.

## Fixed parameters and causal contract

| Parameter | Value |
|---|---|
| confirmation_break_ticks | 1 |
| context_tf | M15 |
| cost | C1 |
| daily_trade_deadline | 17:00 |
| m15_availability_after_close_minutes | 5 |
| m15_parent_bars | 3 |
| max_hold_calendar_minutes | 120 |
| min_entry_to_flat_minutes | 35 |
| min_initial_risk_ticks | 4 |
| min_pullback_close_change_ticks | 1 |
| pullback_bars | 2 |
| pullback_direction | against_M15 |
| signal_tf | M5 |
| stop_buffer_ticks | 1 |
| stop_mode | CORRECTION_EXTREME |
| target_mode | FULL_NET_C1_R |
| target_net_R | 3 |
| trend_structure | HIGHER_HIGHS_AND_LOWS / LOWER_HIGHS_AND_LOWS |
| wait_complete_m5_bars | 1 |

Pre-P&L commit `2b16d7d401f00093101ba0011441905ee23ce3c1`; config SHA-256 `2fdb5978dcd8d3bac7598aa024d12775c44cad184b876dc10f119bb8cf03fd03`. Config, signal/M15 and common core hashes are verified against this freeze. No result-driven changes.

- **M15:** Streaming completed valid M5 only; exact 3 children, MSK wall-clock quarter-hours wholly in one window; release start+20. Latest nominally available parent and its two immediate predecessors only. Known M5 gap invalidates context immediately, even before incomplete parent release; three new complete parents required. No stale fallback.
- **entry:** One full waiting M5 then next Open; no future M15 recheck and no Open reference confirmation. Only adverse Stop geometry, >=4 historical ticks and common Open grid. Context state frozen at signal.
- **exit:** Unchanged core Stop-first/gap, no entry-bar Take, 120 calendar minutes, session end-5 and <=17:00, no overnight.
- **reserve:** At least 35 minutes to actual mandatory flat: min(window.end-5min,17:00). Common reserve adapter receives 40min for windows ending before 17:00, 35min for later windows; the five-minute common session buffer is not counted as holding reserve.
- **selection:** Initial structural hypothesis supplied by user, not selected using this Baseline P&L. One fixed configuration; no later economic tuning.
- **signal:** Exactly two immediately preceding opposite-color M5; second close moves >=1 tick against trend. Separate trend-color M5 closes >=1 tick beyond correction 2 high/low. Strict HH/HL or LH/LL on 3 available M15; no indicators.
- **stop:** Fixed min low / max high of both corrections and signal plus one adverse tick.
- **target:** Shared FULL_NET_C1_R; d=3s+8t outward tick rounding. Planned/actual net/net and gross-risk-normalized net_R_c1 reported separately.
- **unknown:** Missing waiting rejects without submission. Missing entry Open means UNKNOWN possible fill; missing exposed path UNKNOWN. Current day blocked; subsequent days conditional FLAT, no proven annual equity.

## M15 → M5 → entry → exit

Context/trend counts are per M5 decision, not unique independent trend episodes. mtf_context.csv links every decision to exact three M15 and nine child start clocks; all times are MSK and child clocks use their parent date. Unavailable buckets retain expected lineage, blank prices and explicit reasons.

| Instrument | Valid M15 | LONG | SHORT | Pullbacks | Signals | Rejected | Pending | Orders | Fills | Closed | UNKNOWN |
|---|---|---|---|---|---|---|---|---|---|---|---|
| USDRUBF | 21162 | 3205 | 2521 | 855 | 105 | 55 | 56 | 56 | 50 | 50 | 0 |
| CNYRUBF | 15659 | 1479 | 1281 | 270 | 47 | 29 | 21 | 21 | 18 | 18 | 0 |
| GLDRUBF | 5823 | 910 | 642 | 180 | 27 | 19 | 11 | 10 | 8 | 6 | 2 |
| IMOEXF | 1111 | 148 | 131 | 37 | 6 | 2 | 4 | 4 | 4 | 2 | 2 |

## Conditional C1 economics

| Instrument | Closed | Days | PF price | PF R | Net R | Expectancy R | Win rate | Conditional DD R |
|---|---|---|---|---|---|---|---|---|
| USDRUBF | 50 | 44 | 0.494048 | 0.606748 | -14.079381 | -0.281588 | 0.240000 | 19.550315 |
| CNYRUBF | 18 | 18 | 1.392857 | 1.191217 | 2.218342 | 0.123241 | 0.333333 | 6.089377 |
| GLDRUBF | 6 | 6 | 4.200000 | 1.367084 | 1.691765 | 0.281961 | 0.333333 | 2.448780 |
| IMOEXF | 2 | 2 | 0.000000 | 0.000000 | -2.365079 | -1.182540 | 0.000000 | 2.365079 |

| Instrument | Avg win R | Avg loss R | Avg win price | Avg loss price | Largest winner share | Top 3 share | Largest positive month share |
|---|---|---|---|---|---|---|---|
| USDRUBF | 1.810258 | -0.994513 | 0.207500 | -0.140000 | 0.168791 | 0.493121 | 0.482216 |
| CNYRUBF | 2.303253 | -0.966765 | 0.045500 | -0.016333 | 0.325626 | 0.749927 | 0.679457 |
| GLDRUBF | 3.150210 | -1.152164 | 22.050000 | -2.625000 | 0.515839 | 1.000000 | 1.000000 |
| IMOEXF | — | -1.182540 | — | -6.750000 | — | — | — |

## Calendar regularity

| Instrument | Positive /12 | Positive /active | Worst known month | Worst Net R | Fills /available day |
|---|---|---|---|---|---|
| USDRUBF | 0.250000 | 0.250000 | 2023-09 | -5.039747 | 0.196850 |
| CNYRUBF | 0.166667 | 0.400000 | 2023-09 | -1.133333 | 0.070866 |
| GLDRUBF | 0.083333 | 0.500000 | 2023-10 | -2.159875 | 0.064516 |
| IMOEXF | 0.000000 | 0.000000 | 2023-12 | -2.365079 | 0.117647 |

Positive known closures in a month do not establish a complete positive calendar result. Zero-trade and pre-inception months are not positive. Every month remains in the tables.

## Planned and actual 3R

The planned full-net ratio is (take distance−2t)/(initial price risk+2t). Shared FULL_NET_C1_R sets distance=3s+8t with outward rounding. Actual net/net uses realized net price P&L/(s+actual C1); net_R_c1 and PF_R use s. These are different denominators. Target geometry never guarantees attainment.

| Instrument | Plan min | Plan max | TAKE | TAKE /closed | Actual TAKE min | Actual TAKE max | Closed >=3 net/net | Filled UNKNOWN |
|---|---|---|---|---|---|---|---|---|
| USDRUBF | 3.000000 | 3.000000 | 3 | 0.060000 | 3.000000 | 3.000000 | 3 | 0 |
| CNYRUBF | 3.000000 | 3.000000 | 2 | 0.111111 | 3.000000 | 3.000000 | 2 | 0 |
| GLDRUBF | 3.000000 | 3.000000 | 2 | 0.333333 | 3.000000 | 3.000000 | 2 | 2 |
| IMOEXF | 3.000000 | 3.000000 | 0 | 0.000000 | — | — | 0 | 2 |

USDRUBF: **INCONCLUSIVE**; conditional diagnosis **NO ECONOMIC BASELINE PASS**.
Exit counts / costs / target details: `{"actual_Take_net_net_R_max": "3", "actual_Take_net_net_R_min": "3", "adverse_Stop_gaps": 0, "cost_R_known_closed": "8.792800192064369535401443747", "cost_price_known_closed": "1.00", "exit_reasons": {"SESSION_FLAT": 7, "STOP": 26, "TAKE": 3, "TIME": 6, "TRADE_DEADLINE": 8}, "gross_R_known_closed": "-5.286580347255642772575086446", "gross_price_known_closed": "-1.55", "initial_R_denominator": "initial gross price risk; unchanged common metric contract", "known_closures_reaching_full_net_3R": 3, "mean_positive_realized_net_net_R": "1.517376373626373626373626373", "planned_full_net_R_max": "3", "planned_full_net_R_min": "3", "target_hit_closed": 3, "target_hit_fraction_known_closed": "0.06", "target_ratio_denominator": "initial gross risk + round-trip C1", "unresolved_filled_targets": 0}`.
Rejected events: `{"INVALID_RISK": 3, "M5_MISSING_BAR": 187, "MTF_INCOMPLETE_OR_GAP_RESET": 278, "MTF_NO_TREND": 15436, "MTF_THREE_PARENTS_NOT_READY": 5031, "NO_CONTINUATION_CONFIRMATION": 750, "NO_TWO_BAR_PULLBACK": 4871, "POSITION_BUSY": 3, "RISK_BELOW_FOUR_TICKS": 3, "SESSION_ENTRY_CUTOFF": 12, "SESSION_LIMIT": 4, "TRADE_DEADLINE": 30}`.
UNKNOWN: `{}`.
Evidence checks: `{"PF_goal_met": false, "complete": false, "concentration_acceptable": true, "enough_sample": true, "monthly_stability": false, "positive_expectancy": false}`.

CNYRUBF: **INCONCLUSIVE**; conditional diagnosis **INSUFFICIENT_EVIDENCE**.
Exit counts / costs / target details: `{"actual_Take_net_net_R_max": "3", "actual_Take_net_net_R_min": "3", "adverse_Stop_gaps": 0, "cost_R_known_closed": "3.155692140676660800499809788", "cost_price_known_closed": "0.054", "exit_reasons": {"SESSION_FLAT": 4, "STOP": 8, "TAKE": 2, "TIME": 2, "TRADE_DEADLINE": 2}, "gross_R_known_closed": "5.374034462269756387403446227", "gross_price_known_closed": "0.131", "initial_R_denominator": "initial gross price risk; unchanged common metric contract", "known_closures_reaching_full_net_3R": 2, "mean_positive_realized_net_net_R": "1.863909774436090225563909775", "planned_full_net_R_max": "3", "planned_full_net_R_min": "3", "target_hit_closed": 2, "target_hit_fraction_known_closed": "0.1111111111111111111111111111", "target_ratio_denominator": "initial gross risk + round-trip C1", "unresolved_filled_targets": 0}`.
Rejected events: `{"INVALID_RISK": 1, "M5_MISSING_BAR": 1270, "MTF_INCOMPLETE_OR_GAP_RESET": 4865, "MTF_NO_TREND": 12899, "MTF_THREE_PARENTS_NOT_READY": 4864, "NO_CONTINUATION_CONFIRMATION": 223, "NO_TWO_BAR_PULLBACK": 2490, "POSITION_BUSY": 2, "RISK_BELOW_FOUR_TICKS": 2, "SESSION_ENTRY_CUTOFF": 8, "SESSION_LIMIT": 4, "TRADE_DEADLINE": 12}`.
UNKNOWN: `{}`.
Evidence checks: `{"PF_goal_met": false, "complete": false, "concentration_acceptable": false, "enough_sample": false, "monthly_stability": false, "positive_expectancy": true}`.

GLDRUBF: **INCONCLUSIVE**; conditional diagnosis **INSUFFICIENT_EVIDENCE**.
Exit counts / costs / target details: `{"actual_Take_net_net_R_max": "3", "actual_Take_net_net_R_min": "3", "adverse_Stop_gaps": 0, "cost_R_known_closed": "0.7087951519777572318016586556", "cost_price_known_closed": "1.2", "exit_reasons": {"STOP": 4, "TAKE": 2}, "gross_R_known_closed": "2.400560224089635854341736694", "gross_price_known_closed": "34.8", "initial_R_denominator": "initial gross price risk; unchanged common metric contract", "known_closures_reaching_full_net_3R": 2, "mean_positive_realized_net_net_R": "3", "planned_full_net_R_max": "3", "planned_full_net_R_min": "3", "target_hit_closed": 2, "target_hit_fraction_known_closed": "0.3333333333333333333333333333", "target_ratio_denominator": "initial gross risk + round-trip C1", "unresolved_filled_targets": 2}`.
Rejected events: `{"INVALID_RISK": 1, "M5_MISSING_BAR": 932, "MTF_INCOMPLETE_OR_GAP_RESET": 3950, "MTF_NO_TREND": 4271, "MTF_THREE_PARENTS_NOT_READY": 2315, "NO_CONTINUATION_CONFIRMATION": 153, "NO_TWO_BAR_PULLBACK": 1372, "NO_WAITING_BAR": 1, "RISK_BELOW_FOUR_TICKS": 1, "SESSION_ENTRY_CUTOFF": 2, "SESSION_LIMIT": 1, "TRADE_DEADLINE": 13}`.
UNKNOWN: `{"MISSING_EXPOSED_BAR": 2}`.
Evidence checks: `{"PF_goal_met": false, "complete": false, "concentration_acceptable": false, "enough_sample": false, "monthly_stability": false, "positive_expectancy": true}`.

IMOEXF: **INCONCLUSIVE**; conditional diagnosis **NO ECONOMIC BASELINE PASS**.
Exit counts / costs / target details: `{"actual_Take_net_net_R_max": null, "actual_Take_net_net_R_min": null, "adverse_Stop_gaps": 0, "cost_R_known_closed": "0.3650793650793650793650793651", "cost_price_known_closed": "2.0", "exit_reasons": {"STOP": 2}, "gross_R_known_closed": "-2", "gross_price_known_closed": "-11.5", "initial_R_denominator": "initial gross price risk; unchanged common metric contract", "known_closures_reaching_full_net_3R": 0, "mean_positive_realized_net_net_R": null, "planned_full_net_R_max": "3", "planned_full_net_R_min": "3", "target_hit_closed": 0, "target_hit_fraction_known_closed": "0", "target_ratio_denominator": "initial gross risk + round-trip C1", "unresolved_filled_targets": 2}`.
Rejected events: `{"M5_MISSING_BAR": 566, "MTF_INCOMPLETE_OR_GAP_RESET": 1297, "MTF_NO_TREND": 832, "MTF_THREE_PARENTS_NOT_READY": 596, "NO_CONTINUATION_CONFIRMATION": 31, "NO_TWO_BAR_PULLBACK": 242, "SESSION_LIMIT": 1, "TRADE_DEADLINE": 1}`.
UNKNOWN: `{"MISSING_EXPOSED_BAR": 2}`.
Evidence checks: `{"PF_goal_met": false, "complete": false, "concentration_acceptable": false, "enough_sample": false, "monthly_stability": false, "positive_expectancy": false}`.

## LONG / SHORT

| Instrument | Side | Signals | Fills | Closed | UNKNOWN | PF price | PF R | Net R | Expectancy R |
|---|---|---|---|---|---|---|---|---|---|
| USDRUBF | SHORT | 47 | 22 | 22 | 0 | 0.445736 | 0.529302 | -8.412035 | -0.382365 |
| USDRUBF | LONG | 58 | 28 | 28 | 0 | 0.544715 | 0.683937 | -5.667346 | -0.202405 |
| CNYRUBF | SHORT | 19 | 5 | 5 | 0 | 22.000000 | 9.146104 | 6.335859 | 1.267172 |
| CNYRUBF | LONG | 28 | 13 | 13 | 0 | 0.284946 | 0.619573 | -4.117516 | -0.316732 |
| GLDRUBF | SHORT | 11 | 4 | 4 | 0 | 1.258065 | 0.912954 | -0.309875 | -0.077469 |
| GLDRUBF | LONG | 16 | 4 | 2 | 2 | 8.441860 | 2.908540 | 2.001640 | 1.000820 |
| IMOEXF | SHORT | 3 | 2 | 1 | 1 | 0.000000 | 0.000000 | -1.142857 | -1.142857 |
| IMOEXF | LONG | 3 | 2 | 1 | 1 | 0.000000 | 0.000000 | -1.222222 | -1.222222 |

## All twelve calendar months

| Month | Instrument | Signals | Fills | Closed | UNKNOWN | PF price | PF R | Net R | Expectancy R | Coverage |
|---|---|---|---|---|---|---|---|---|---|---|
| 2023-01 | USDRUBF | 9 | 6 | 6 | 0 | 0.087719 | 0.076974 | -4.612051 | -0.768675 | PARTIAL_DATA |
| 2023-01 | CNYRUBF | 1 | 0 | 0 | 0 | — | — | 0.000000 | — | PARTIAL_DATA |
| 2023-01 | GLDRUBF | 0 | 0 | 0 | 0 | — | — | — | — | NO_COVERAGE |
| 2023-01 | IMOEXF | 0 | 0 | 0 | 0 | — | — | — | — | NO_COVERAGE |
| 2023-02 | USDRUBF | 10 | 4 | 4 | 0 | 0.250000 | 0.560227 | -0.356814 | -0.089203 | PARTIAL_DATA |
| 2023-02 | CNYRUBF | 0 | 0 | 0 | 0 | — | — | 0.000000 | — | PARTIAL_DATA |
| 2023-02 | GLDRUBF | 0 | 0 | 0 | 0 | — | — | — | — | NO_COVERAGE |
| 2023-02 | IMOEXF | 0 | 0 | 0 | 0 | — | — | — | — | NO_COVERAGE |
| 2023-03 | USDRUBF | 8 | 1 | 1 | 0 | — | — | 2.363636 | 2.363636 | PARTIAL_DATA |
| 2023-03 | CNYRUBF | 0 | 0 | 0 | 0 | — | — | 0.000000 | — | PARTIAL_DATA |
| 2023-03 | GLDRUBF | 0 | 0 | 0 | 0 | — | — | — | — | NO_COVERAGE |
| 2023-03 | IMOEXF | 0 | 0 | 0 | 0 | — | — | — | — | NO_COVERAGE |
| 2023-04 | USDRUBF | 6 | 4 | 4 | 0 | 1.218750 | 1.392454 | 0.999264 | 0.249816 | PARTIAL_DATA |
| 2023-04 | CNYRUBF | 1 | 0 | 0 | 0 | — | — | 0.000000 | — | PARTIAL_DATA |
| 2023-04 | GLDRUBF | 0 | 0 | 0 | 0 | — | — | — | — | NO_COVERAGE |
| 2023-04 | IMOEXF | 0 | 0 | 0 | 0 | — | — | — | — | NO_COVERAGE |
| 2023-05 | USDRUBF | 5 | 2 | 2 | 0 | 0.500000 | 0.310811 | -0.119859 | -0.059929 | PARTIAL_DATA |
| 2023-05 | CNYRUBF | 0 | 0 | 0 | 0 | — | — | 0.000000 | — | PARTIAL_DATA |
| 2023-05 | GLDRUBF | 0 | 0 | 0 | 0 | — | — | — | — | NO_COVERAGE |
| 2023-05 | IMOEXF | 0 | 0 | 0 | 0 | — | — | — | — | NO_COVERAGE |
| 2023-06 | USDRUBF | 7 | 2 | 2 | 0 | 0.428571 | 0.306122 | -0.971429 | -0.485714 | PARTIAL_DATA |
| 2023-06 | CNYRUBF | 1 | 0 | 0 | 0 | — | — | 0.000000 | — | PARTIAL_DATA |
| 2023-06 | GLDRUBF | 0 | 0 | 0 | 0 | — | — | — | — | NO_COVERAGE |
| 2023-06 | IMOEXF | 0 | 0 | 0 | 0 | — | — | — | — | NO_COVERAGE |
| 2023-07 | USDRUBF | 5 | 1 | 1 | 0 | 0.000000 | 0.000000 | -1.181818 | -1.181818 | PARTIAL_DATA |
| 2023-07 | CNYRUBF | 1 | 1 | 1 | 0 | — | — | 1.250000 | 1.250000 | PARTIAL_DATA |
| 2023-07 | GLDRUBF | 1 | 0 | 0 | 0 | — | — | 0.000000 | — | PARTIAL_DATA |
| 2023-07 | IMOEXF | 0 | 0 | 0 | 0 | — | — | — | — | NO_COVERAGE |
| 2023-08 | USDRUBF | 10 | 5 | 5 | 0 | 0.000000 | 0.000000 | -4.095050 | -0.819010 | PARTIAL_DATA |
| 2023-08 | CNYRUBF | 1 | 0 | 0 | 0 | — | — | 0.000000 | — | PARTIAL_DATA |
| 2023-08 | GLDRUBF | 4 | 2 | 0 | 2 | — | — | 0.000000 | — | UNKNOWN |
| 2023-08 | IMOEXF | 0 | 0 | 0 | 0 | — | — | — | — | NO_COVERAGE |
| 2023-09 | USDRUBF | 12 | 8 | 8 | 0 | 0.407407 | 0.384090 | -5.039747 | -0.629968 | PARTIAL_DATA |
| 2023-09 | CNYRUBF | 4 | 1 | 1 | 0 | 0.000000 | 0.000000 | -1.133333 | -1.133333 | PARTIAL_DATA |
| 2023-09 | GLDRUBF | 1 | 0 | 0 | 0 | — | — | 0.000000 | — | PARTIAL_DATA |
| 2023-09 | IMOEXF | 0 | 0 | 0 | 0 | — | — | — | — | NO_COVERAGE |
| 2023-10 | USDRUBF | 12 | 8 | 8 | 0 | 0.642857 | 0.487044 | -3.554555 | -0.444319 | COMPLETE_MODEL_COHORT |
| 2023-10 | CNYRUBF | 14 | 6 | 6 | 0 | 0.176471 | 0.907982 | -0.456044 | -0.076007 | PARTIAL_DATA |
| 2023-10 | GLDRUBF | 7 | 2 | 2 | 0 | 0.000000 | 0.000000 | -2.159875 | -1.079937 | PARTIAL_DATA |
| 2023-10 | IMOEXF | 0 | 0 | 0 | 0 | — | — | — | — | NO_COVERAGE |
| 2023-11 | USDRUBF | 13 | 8 | 8 | 0 | 1.203390 | 1.646758 | 3.131899 | 0.391487 | PARTIAL_DATA |
| 2023-11 | CNYRUBF | 11 | 5 | 5 | 0 | 2.709677 | 0.968900 | -0.091919 | -0.018384 | PARTIAL_DATA |
| 2023-11 | GLDRUBF | 5 | 0 | 0 | 0 | — | — | 0.000000 | — | PARTIAL_DATA |
| 2023-11 | IMOEXF | 1 | 0 | 0 | 0 | — | — | 0.000000 | — | PARTIAL_DATA |
| 2023-12 | USDRUBF | 8 | 1 | 1 | 0 | 0.000000 | 0.000000 | -0.642857 | -0.642857 | COMPLETE_MODEL_COHORT |
| 2023-12 | CNYRUBF | 13 | 5 | 5 | 0 | 1.543478 | 2.036536 | 2.649639 | 0.529928 | COMPLETE_MODEL_COHORT |
| 2023-12 | GLDRUBF | 9 | 4 | 4 | 0 | 8.820000 | 2.572881 | 3.851640 | 0.962910 | PARTIAL_DATA |
| 2023-12 | IMOEXF | 5 | 4 | 2 | 2 | 0.000000 | 0.000000 | -2.365079 | -1.182540 | UNKNOWN |

## Coverage and UNKNOWN

| Instrument | Rows 2023 | First observation | Complete/incomplete/pre-inception days | Missing/invalid M5 |
|---|---|---|---|---|
| USDRUBF | 42576 | 2023-01-03 09:00:00+03:00 | 224/30/0 | 187/0 |
| CNYRUBF | 39362 | 2023-01-03 09:00:00+03:00 | 82/172/0 | 1270/0 |
| GLDRUBF | 18428 | 2023-07-11 10:00:00+03:00 | 5/119/130 | 932/0 |
| IMOEXF | 4429 | 2023-11-14 10:00:00+03:00 | 2/32/220 | 566/0 |

Coverage uses the entire accepted research windows, including post-17:00 slots, conservatively. No OHLCV filled. Missing waiting rejects before order submission; missing entry Open is UNKNOWN possible fill. Missing exposed/exit path is UNKNOWN with blank P&L. UNKNOWN blocks its day; subsequent independent research days assume FLAT conditionally. Annual equity and Max DD are unconfirmed.

## Validation, isolation and classification

Independent batch M15/signal and forward-path oracle imports no production strategy, core or metrics. It verifies lineage, availability, gaps, signals, ledger, C1 and CSV-only economics. This is independent implementation verification by the task agent, not external human acceptance. See Independent_Audit.md / audit.json.
validation.json records technical tests, two full repeats with byte equality, complete reruns and independent audits of ORB A BASE, R17, R16 and Level Rejection. Old stored results and every existing file remain byte unchanged. Shared execution is unchanged; this adapter owns no orders, positions or P&L. TradingSystemLab and all paths outside IntradayLab are unchanged.
Predeclared evidence policy: complete coverage/outcomes, >=30 closures, >=15 trade days, >=3 active and positive months, >=60% positive active months, positive C1 expectancy, both PF >=1.6, largest winner <=25% and largest positive month <=50%. Incomplete coverage/outcomes gives INCONCLUSIVE; negative known expectancy gives separate NO ECONOMIC BASELINE PASS diagnosis. Controlled annual drawdown cannot be certified without full coverage.
Reproduce: `python3 IntradayLab/tools/run_swing_pullback_baseline.py --data-root /workspace/market-pattern-data --output IntradayLab/work/swing_replay` then the matching `audit_swing_pullback_baseline.py` command.
Pinned source `f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8`; only exact 2023 prefixes. Zero 2024/2025+ price bytes. No selection of profitable instruments/directions/months.
Stops after Draft PR. No Merge, Optimization, Robustness, Walk Forward, TRUE OOS or LIVE.
