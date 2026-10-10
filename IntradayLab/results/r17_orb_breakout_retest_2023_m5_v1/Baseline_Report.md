# R17 Opening-Range Breakout Retest — Canonical M5 Baseline 2023

**Baseline: INCONCLUSIVE. No Optimization.**

One frozen candidate, four instruments, all available 2023 development M5. No parameter search.
All reported economics are conditional known closures after C1 (one historical tick per side).
Incomplete source coverage / UNKNOWN mean annual PF, expectancy, Net R, win rate and drawdown remain null. Known-closure drawdown is a diagnostic sequence, not continuous broker equity. Price units from different instruments are never added into a monetary portfolio.

| Instrument | Signals | Orders | Fills | Closed | UNKNOWN | PF C1 price | PF C1 R | Net R | Expectancy R | Win rate | Known-closure DD R |
|---|---|---|---|---|---|---|---|---|---|---|---|
| USDRUBF | 131 | 131 | 129 | 126 | 3 | 1.037194 | 0.735292 | -18.313959 | -0.145349 | 0.436508 | 24.587320 |
| CNYRUBF | 218 | 207 | 200 | 144 | 61 | 0.391561 | 0.322752 | -73.530734 | -0.510630 | 0.298611 | 78.980821 |
| GLDRUBF | 23 | 22 | 21 | 20 | 1 | 1.454545 | 0.858835 | -1.774387 | -0.088719 | 0.400000 | 6.183232 |
| IMOEXF | 10 | 9 | 9 | 7 | 2 | 0.625000 | 0.473974 | -2.386111 | -0.340873 | 0.285714 | 3.202778 |

## Evidence, averages and concentration

| Instrument | Trade days | Positive/negative months | Average winner R | Average loser R | Largest winner share R | Top 3 winners share R | Largest positive month share R | Status / conditional diagnosis |
|---|---|---|---|---|---|---|---|---|
| USDRUBF | 110 | 4/8 | 0.924936 | -1.017433 | 0.028394 | 0.085030 | 0.509380 | INCONCLUSIVE / NO ECONOMIC BASELINE PASS |
| CNYRUBF | 131 | 2/10 | 0.814933 | -1.247964 | 0.041304 | 0.123300 | 0.779571 | INCONCLUSIVE / NO ECONOMIC BASELINE PASS |
| GLDRUBF | 18 | 3/2 | 1.349402 | -1.047467 | 0.138093 | 0.413212 | 0.524231 | INCONCLUSIVE / NO ECONOMIC BASELINE PASS |
| IMOEXF | 7 | 0/1 | 1.075000 | -1.134028 | 0.651163 | 1.000000 | — | INCONCLUSIVE / NO ECONOMIC BASELINE PASS |

USDRUBF: evidence checks `{"PF_goal_met": false, "complete": false, "concentration_acceptable": false, "enough_sample": true, "monthly_stability": false, "positive_expectancy": false}`.
Average winning/losing price-unit trade: 0.177455 / -0.138382.
Rejection/diagnostic reasons: `{"INVALID_STOP_GEOMETRY": 2, "NO_OR": 2, "NO_RETEST_CONDITION": 198, "NO_RETEST_WINDOW": 4}`.
Unknown possible entries: 0; conditional known closures after prior UNKNOWN: 116.

CNYRUBF: evidence checks `{"PF_goal_met": false, "complete": false, "concentration_acceptable": false, "enough_sample": true, "monthly_stability": false, "positive_expectancy": false}`.
Average winning/losing price-unit trade: 0.030860 / -0.038954.
Rejection/diagnostic reasons: `{"INVALID_STOP_GEOMETRY": 2, "MISSING_EXECUTION_BAR": 5, "NO_OR": 6, "NO_RETEST_CONDITION": 93, "NO_RETEST_MISSING_BAR": 5, "NO_WAITING_BAR": 2, "UNKNOWN_POSITION_BLOCK": 9}`.
Unknown possible entries: 5; conditional known closures after prior UNKNOWN: 144.

GLDRUBF: evidence checks `{"PF_goal_met": false, "complete": false, "concentration_acceptable": false, "enough_sample": false, "monthly_stability": true, "positive_expectancy": false}`.
Average winning/losing price-unit trade: 13.200000 / -6.050000.
Rejection/diagnostic reasons: `{"INVALID_STOP_GEOMETRY": 1, "NO_OR": 9, "NO_RETEST_CONDITION": 138, "NO_RETEST_MISSING_BAR": 6, "NO_RETEST_WINDOW": 2, "NO_WAITING_BAR": 1}`.
Unknown possible entries: 0; conditional known closures after prior UNKNOWN: 5.

IMOEXF: evidence checks `{"PF_goal_met": false, "complete": false, "concentration_acceptable": false, "enough_sample": false, "monthly_stability": false, "positive_expectancy": false}`.
Average winning/losing price-unit trade: 10.000000 / -8.000000.
Rejection/diagnostic reasons: `{"NO_OR": 4, "NO_RETEST_CONDITION": 28, "NO_RETEST_MISSING_BAR": 4, "UNKNOWN_POSITION_BLOCK": 1}`.
Unknown possible entries: 0; conditional known closures after prior UNKNOWN: 4.

## LONG / SHORT

| Instrument | Side | Signals | Closed | UNKNOWN | PF C1 price | PF C1 R | Net R | Expectancy R | Win rate |
|---|---|---|---|---|---|---|---|---|---|
| USDRUBF | SHORT | 59 | 58 | 1 | 1.134663 | 0.683318 | -10.223499 | -0.176267 | 0.465517 |
| USDRUBF | LONG | 72 | 68 | 2 | 0.964815 | 0.780760 | -8.090460 | -0.118977 | 0.411765 |
| CNYRUBF | SHORT | 103 | 62 | 36 | 0.464078 | 0.364517 | -27.409730 | -0.442092 | 0.306452 |
| CNYRUBF | LONG | 115 | 82 | 25 | 0.330803 | 0.295225 | -46.121005 | -0.562451 | 0.292683 |
| GLDRUBF | SHORT | 11 | 10 | 1 | 3.514403 | 1.391951 | 2.088464 | 0.208846 | 0.500000 |
| GLDRUBF | LONG | 12 | 10 | 0 | 0.418219 | 0.466547 | -3.862851 | -0.386285 | 0.300000 |
| IMOEXF | SHORT | 4 | 2 | 2 | 0.705882 | 0.794118 | -0.194444 | -0.097222 | 0.500000 |
| IMOEXF | LONG | 6 | 5 | 0 | 0.595745 | 0.389791 | -2.191667 | -0.438333 | 0.200000 |

## Twelve calendar months — conditional known closures

Month attribution uses signal date. Zero closures with observed data have Net R 0 and undefined PF; no source coverage is shown as —, never manufactured as a flat profitable month.

| Month | Instrument | Closed | UNKNOWN | PF C1 price | Net R | Expectancy R | Coverage | Complete/incomplete/pre-inception days |
|---|---|---|---|---|---|---|---|---|
| 2023-01 | USDRUBF | 14 | 2 | 2.272727 | -0.559650 | -0.039975 | UNKNOWN | 16/5/0 |
| 2023-01 | CNYRUBF | 15 | 4 | 0.125000 | -9.679365 | -0.645291 | UNKNOWN | 3/18/0 |
| 2023-01 | GLDRUBF | 0 | 0 | — | — | — | NO_COVERAGE | 0/0/21 |
| 2023-01 | IMOEXF | 0 | 0 | — | — | — | NO_COVERAGE | 0/0/21 |
| 2023-02 | USDRUBF | 14 | 0 | 1.053097 | -0.488386 | -0.034885 | PARTIAL_DATA | 15/4/0 |
| 2023-02 | CNYRUBF | 14 | 5 | 0.518519 | -5.111905 | -0.365136 | UNKNOWN | 1/18/0 |
| 2023-02 | GLDRUBF | 0 | 0 | — | — | — | NO_COVERAGE | 0/0/19 |
| 2023-02 | IMOEXF | 0 | 0 | — | — | — | NO_COVERAGE | 0/0/19 |
| 2023-03 | USDRUBF | 14 | 0 | 1.038462 | -1.906803 | -0.136200 | PARTIAL_DATA | 19/3/0 |
| 2023-03 | CNYRUBF | 7 | 11 | 0.160000 | -8.500000 | -1.214286 | UNKNOWN | 0/22/0 |
| 2023-03 | GLDRUBF | 0 | 0 | — | — | — | NO_COVERAGE | 0/0/22 |
| 2023-03 | IMOEXF | 0 | 0 | — | — | — | NO_COVERAGE | 0/0/22 |
| 2023-04 | USDRUBF | 11 | 0 | 1.596774 | 0.496888 | 0.045172 | PARTIAL_DATA | 15/5/0 |
| 2023-04 | CNYRUBF | 9 | 8 | 4.750000 | 0.897619 | 0.099735 | UNKNOWN | 2/18/0 |
| 2023-04 | GLDRUBF | 0 | 0 | — | — | — | NO_COVERAGE | 0/0/20 |
| 2023-04 | IMOEXF | 0 | 0 | — | — | — | NO_COVERAGE | 0/0/20 |
| 2023-05 | USDRUBF | 8 | 1 | 5.064516 | 2.532392 | 0.316549 | UNKNOWN | 18/3/0 |
| 2023-05 | CNYRUBF | 14 | 9 | 0.117647 | -11.526190 | -0.823299 | UNKNOWN | 0/21/0 |
| 2023-05 | GLDRUBF | 0 | 0 | — | — | — | NO_COVERAGE | 0/0/21 |
| 2023-05 | IMOEXF | 0 | 0 | — | — | — | NO_COVERAGE | 0/0/21 |
| 2023-06 | USDRUBF | 10 | 0 | 3.605263 | 3.300326 | 0.330033 | PARTIAL_DATA | 17/4/0 |
| 2023-06 | CNYRUBF | 13 | 10 | 0.800000 | -4.126190 | -0.317399 | UNKNOWN | 1/20/0 |
| 2023-06 | GLDRUBF | 0 | 0 | — | — | — | NO_COVERAGE | 0/0/21 |
| 2023-06 | IMOEXF | 0 | 0 | — | — | — | NO_COVERAGE | 0/0/21 |
| 2023-07 | USDRUBF | 8 | 0 | 0.702703 | -5.114274 | -0.639284 | PARTIAL_DATA | 20/1/0 |
| 2023-07 | CNYRUBF | 14 | 8 | 0.769231 | -6.986111 | -0.499008 | UNKNOWN | 2/19/0 |
| 2023-07 | GLDRUBF | 0 | 0 | — | 0.000000 | — | PARTIAL_DATA | 0/15/6 |
| 2023-07 | IMOEXF | 0 | 0 | — | — | — | NO_COVERAGE | 0/0/21 |
| 2023-08 | USDRUBF | 7 | 0 | 0.320000 | -4.758797 | -0.679828 | PARTIAL_DATA | 21/2/0 |
| 2023-08 | CNYRUBF | 16 | 4 | 0.327586 | -12.826587 | -0.801662 | UNKNOWN | 9/14/0 |
| 2023-08 | GLDRUBF | 2 | 0 | 5.031250 | 0.458483 | 0.229241 | PARTIAL_DATA | 0/23/0 |
| 2023-08 | IMOEXF | 0 | 0 | — | — | — | NO_COVERAGE | 0/0/23 |
| 2023-09 | USDRUBF | 11 | 0 | 0.512821 | -1.715829 | -0.155984 | PARTIAL_DATA | 19/2/0 |
| 2023-09 | CNYRUBF | 19 | 2 | 0.126667 | -14.848095 | -0.781479 | UNKNOWN | 7/14/0 |
| 2023-09 | GLDRUBF | 6 | 0 | 0.000000 | -6.183232 | -1.030539 | PARTIAL_DATA | 0/21/0 |
| 2023-09 | IMOEXF | 0 | 0 | — | — | — | NO_COVERAGE | 0/0/21 |
| 2023-10 | USDRUBF | 7 | 0 | 0.011364 | -5.831598 | -0.833085 | CONDITIONAL_AFTER_UNKNOWN | 22/0/0 |
| 2023-10 | CNYRUBF | 4 | 0 | 0.000000 | -3.204040 | -0.801010 | PARTIAL_DATA | 20/2/0 |
| 2023-10 | GLDRUBF | 6 | 0 | 3.601695 | 2.930797 | 0.488466 | PARTIAL_DATA | 1/21/0 |
| 2023-10 | IMOEXF | 0 | 0 | — | — | — | NO_COVERAGE | 0/0/22 |
| 2023-11 | USDRUBF | 10 | 0 | 0.700000 | 0.149494 | 0.014949 | PARTIAL_DATA | 21/1/0 |
| 2023-11 | CNYRUBF | 12 | 0 | 1.578313 | 3.174531 | 0.264544 | PARTIAL_DATA | 16/6/0 |
| 2023-11 | GLDRUBF | 5 | 1 | 2.809091 | 2.201383 | 0.440277 | UNKNOWN | 1/21/0 |
| 2023-11 | IMOEXF | 0 | 0 | — | 0.000000 | — | PARTIAL_DATA | 0/13/9 |
| 2023-12 | USDRUBF | 12 | 0 | 0.423729 | -4.417722 | -0.368144 | CONDITIONAL_AFTER_UNKNOWN | 21/0/0 |
| 2023-12 | CNYRUBF | 7 | 0 | 1.111111 | -0.794400 | -0.113486 | CONDITIONAL_AFTER_UNKNOWN | 21/0/0 |
| 2023-12 | GLDRUBF | 1 | 0 | 0.000000 | -1.181818 | -1.181818 | PARTIAL_DATA | 3/18/0 |
| 2023-12 | IMOEXF | 7 | 2 | 0.625000 | -2.386111 | -0.340873 | UNKNOWN | 2/19/0 |

## Source coverage and UNKNOWN

| Instrument | Source M5 rows | First observation | Complete/incomplete/pre-inception days | Missing/invalid slots | Unavailable OR days |
|---|---|---|---|---|---|
| USDRUBF | 42576 | 2023-01-03 09:00:00+03:00 | 224/30/0 | 187/0 | 2 |
| CNYRUBF | 39362 | 2023-01-03 09:00:00+03:00 | 82/172/0 | 1270/0 | 6 |
| GLDRUBF | 18428 | 2023-07-11 10:00:00+03:00 | 5/119/130 | 932/0 | 9 |
| IMOEXF | 4429 | 2023-11-14 10:00:00+03:00 | 2/32/220 | 566/0 | 4 |

Coverage uses the unchanged approved full research-window grid, conservatively including slots outside R17 signal windows. All physical 2023 rows, including morning/evening observations, warm ATR. No bars/days are filled. GLD and IMOEX pre-inception periods stay unavailable.
September 13 halt is diagnosed; other absence causes remain unproven. Missing waiting bars reject without submission. Missing entry Open creates UNKNOWN possible fill; missing exposed bar / mandatory exit retains UNKNOWN with blank net. See coverage_events.csv and unknown_report.csv.
One UNKNOWN blocks only its own day. Following days require an explicit conditional FLAT assumption, not proof of broker FLAT. UNKNOWN economics cannot be used to form a continuous annual result.

## Frozen adaptation and historical provenance

Historical commit `728d23e25d4bd41fdb6d50e134d1f099c206c6b2`, candidate `C17-357ae5a27074861f`; 72 tested parameter sets, 0 strict survivors. Historical 30 trades / BASE PF 1.746113 / STRESS PF 1.406128 are selection provenance only and are not this Baseline.
Historical parameters remain buffer_atr=0.30, retest_bars=1, touch_ticks=2, stop_mode=OR_MID, target_r=1.5.
Config frozen in commit `24f92c68ecc6e4425e4da430de1fb4f73f058399` before any R17 P&L; SHA-256 `9f1da05a6b91f52ab352ebf143d4758487f4385c96e7af5e22d51e69c48191ee`. No subsequent parameter changes.

- **ATR14:** Existing Indicators: arithmetic mean of 14 genuine valid trailing true ranges, includes just-completed breakout bar; continuous across days/sessions, no daily reset. Adjacent previous close only; otherwise H-L. All available 2023 history including outside entry windows warms ATR; no fabricated pre-2023 warmup.
- **M1_non_equivalence:** M5 adaptation, not equivalent to M1 opening/execution; historical max hold was 120 available M1 bars and no observed M1 at/after 17:00. This run uses 120 calendar minutes and an explicit exact-Open 17:00 cutoff.
- **OR:** Exactly valid completed starts 10:00/10:05/10:10, fixed and available at 10:15. No replacement bars.
- **cost:** C1 one dated tick per side, ledger deductions; no synthetic scenario-price alterations.
- **entry:** Retest completes -> one full following M5 completes -> next interval Open, only inside approved calendar and strictly before effective deadline. No future H/L/C/V for admission.
- **exit:** Earliest entry+120 calendar minutes, approved calendar window.end-5 minutes, or exact Open 17:00. At 17:00 use Open scalar only, no 17:00-17:05 OHLC exposure. Stop gap has precedence. No entry at deadline.
- **retest:** Exactly breakout.start+5 minutes in same intersection window; missing/invalid/outside consumes attempt and is diagnosed. Breakout cannot retest itself; first onset consumes one attempt per side/day regardless of execution.
- **signal_windows:** Inclusive M5 START labels; breakout and retest each wholly inside same R17 window intersected with approved calendar. Afternoon first permitted start 14:05 normally and 14:15 on March 13-20. Noon window last start 12:55, afternoon 16:50.
- **stop:** Midpoint=(OR_HIGH+OR_LOW)/2 rounded to nearest historical retest tick with ROUND_HALF_UP (positive half ties upward), then LONG midpoint-1 tick / SHORT midpoint+1 tick. Core validates adverse risk versus actual entry Open. No minimum Stop filter.
- **target:** Core target at 1.5 initial gross risk; outward entry-grid rounding (LONG ceiling / SHORT floor) as canonical execution.
- **unknown:** Unresolved same day blocked; next independent research day conditionally assumes FLAT, never proven broker FLAT; annual continuous economics null on incomplete data/UNKNOWN.

## Classification and validation

The status is computed from actual results, not copied from ORB. Frozen sufficient-evidence criteria: >=30 closures, >=15 trade days, >=3 active and positive months, >=60% positive active months, PF C1 price and R >=1.6, positive expectancy, largest winner <=25% of positive R and largest positive month <=50% of positive monthly R. Complete coverage and resolved outcomes are required for a confirmed pass. Four-instrument overall assessment requires sufficient evidence from every declared instrument.
Independent source/strategy/execution oracle and independent CSV metric reconstruction: audit.json and Independent_Audit.md. Technical tests, two additional deterministic runs and canonical ORB regression: validation.json. Independent implementation audit is not an external reviewer signoff; PR remains Draft for independent review.
Core default execution remains unchanged; only optional daily deadline and additive generic economic assessment helpers are added. Prior canonical ORB artifacts/config/strategy and all frozen studies are protected. TradingSystemLab and market-pattern-data remain unchanged.
Reproduce: `python3 IntradayLab/tools/run_r17_baseline.py --data-root /workspace/market-pattern-data --output IntradayLab/work/r17_replay` then `python3 IntradayLab/tools/audit_r17_baseline.py --data-root /workspace/market-pattern-data --output IntradayLab/work/r17_replay`.
Source commit `f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8`; exact verified 2023 byte prefixes only. No 2024 or 2025+ price bytes read. C1 is a research cost assumption, not verified broker fees or execution capacity.
Baseline → Optimization → Robustness → Walk Forward → TRUE OOS. This task stops at Baseline and Draft PR: no Merge, Optimization, Robustness, Walk Forward, TRUE OOS or LIVE.
