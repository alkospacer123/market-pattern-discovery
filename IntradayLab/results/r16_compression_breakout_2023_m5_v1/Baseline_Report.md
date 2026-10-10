# R16 Intraday Compression Breakout — Canonical M5 Baseline 2023

**Baseline: INCONCLUSIVE. No Optimization.**

One frozen candidate, four instruments, all available 2023 development M5. No parameter search.
All reported economics are conditional known closures after C1 (one historical tick per side).
Incomplete source coverage / UNKNOWN mean annual PF, expectancy, Net R, win rate and drawdown remain null. Known-closure drawdown is a diagnostic sequence, not continuous broker equity. Price units from different instruments are never added into a monetary portfolio.

| Instrument | Signals | Orders | Fills | Closed | UNKNOWN | PF C1 price | PF C1 R | Net R | Expectancy R | Win rate | Known-closure DD R |
|---|---|---|---|---|---|---|---|---|---|---|---|
| USDRUBF | 306 | 255 | 253 | 246 | 7 | 0.834288 | 0.689256 | -41.733545 | -0.169649 | 0.402439 | 45.516216 |
| CNYRUBF | 215 | 164 | 162 | 124 | 39 | 0.665745 | 0.596025 | -28.138007 | -0.226919 | 0.370968 | 28.138007 |
| GLDRUBF | 98 | 73 | 70 | 51 | 22 | 1.098169 | 1.428524 | 8.085135 | 0.158532 | 0.529412 | 3.134772 |
| IMOEXF | 18 | 13 | 11 | 9 | 4 | 0.125000 | 0.168259 | -6.814568 | -0.757174 | 0.222222 | 6.814568 |

## Evidence, averages and concentration

| Instrument | Trade days | Positive/negative months | Average winner R | Average loser R | Largest winner share R | Top 3 winners share R | Largest positive month share R | Status / conditional diagnosis |
|---|---|---|---|---|---|---|---|---|
| USDRUBF | 178 | 4/8 | 0.935037 | -0.939176 | 0.015930 | 0.047431 | 0.425110 | INCONCLUSIVE / NO ECONOMIC BASELINE PASS |
| CNYRUBF | 104 | 1/11 | 0.902498 | -0.928706 | 0.035363 | 0.104675 | 1.000000 | INCONCLUSIVE / NO ECONOMIC BASELINE PASS |
| GLDRUBF | 40 | 5/1 | 0.998243 | -0.786142 | 0.055303 | 0.165826 | 0.346043 | INCONCLUSIVE / POSITIVE_EXPECTANCY_BELOW_EVIDENCE_CRITERIA |
| IMOEXF | 7 | 0/1 | 0.689286 | -1.365523 | 0.870466 | 1.000000 | — | INCONCLUSIVE / NO ECONOMIC BASELINE PASS |

USDRUBF: evidence checks `{"PF_goal_met": false, "complete": false, "concentration_acceptable": true, "enough_sample": true, "monthly_stability": false, "positive_expectancy": false}`.
Average winning/losing price-unit trade: 0.176465 / -0.146434.
Rejection/diagnostic reasons: `{"ALREADY_OUTSIDE_RANGE": 23, "COMPRESSION_MISSING_BAR": 136, "COMPRESSION_UNAVAILABLE": 508, "INVALID_STOP_GEOMETRY": 2, "POSITION_BUSY": 49, "TRADE_DEADLINE": 1, "UNKNOWN_POSITION_BLOCK": 1}`.
UNKNOWN reasons: `{"MISSING_EXPOSED_BAR": 7}`.
Unknown possible entries: 0; conditional known closures after prior UNKNOWN: 236.

CNYRUBF: evidence checks `{"PF_goal_met": false, "complete": false, "concentration_acceptable": false, "enough_sample": true, "monthly_stability": false, "positive_expectancy": false}`.
Average winning/losing price-unit trade: 0.031391 / -0.028920.
Rejection/diagnostic reasons: `{"ALREADY_OUTSIDE_RANGE": 25, "COMPRESSION_MISSING_BAR": 782, "COMPRESSION_UNAVAILABLE": 508, "INVALID_STOP_GEOMETRY": 1, "MISSING_EXECUTION_BAR": 1, "NO_WAITING_BAR": 5, "POSITION_BUSY": 36, "TRADE_DEADLINE": 6, "UNKNOWN_POSITION_BLOCK": 4}`.
UNKNOWN reasons: `{"MISSING_EXECUTION_BAR": 1, "MISSING_EXPOSED_BAR": 38}`.
Unknown possible entries: 1; conditional known closures after prior UNKNOWN: 116.

GLDRUBF: evidence checks `{"PF_goal_met": false, "complete": false, "concentration_acceptable": true, "enough_sample": true, "monthly_stability": true, "positive_expectancy": true}`.
Average winning/losing price-unit trade: 10.440741 / -10.695833.
Rejection/diagnostic reasons: `{"ALREADY_OUTSIDE_RANGE": 18, "COMPRESSION_MISSING_BAR": 617, "COMPRESSION_UNAVAILABLE": 248, "MISSING_EXECUTION_BAR": 3, "NO_WAITING_BAR": 2, "POSITION_BUSY": 16, "TRADE_DEADLINE": 1, "UNKNOWN_POSITION_BLOCK": 6}`.
UNKNOWN reasons: `{"MISSING_EXECUTION_BAR": 3, "MISSING_EXPOSED_BAR": 19}`.
Unknown possible entries: 3; conditional known closures after prior UNKNOWN: 50.

IMOEXF: evidence checks `{"PF_goal_met": false, "complete": false, "concentration_acceptable": false, "enough_sample": false, "monthly_stability": false, "positive_expectancy": false}`.
Average winning/losing price-unit trade: 2.750000 / -7.333333.
Rejection/diagnostic reasons: `{"ALREADY_OUTSIDE_RANGE": 6, "COMPRESSION_MISSING_BAR": 353, "COMPRESSION_UNAVAILABLE": 68, "MISSING_EXECUTION_BAR": 2, "NO_WAITING_BAR": 1, "POSITION_BUSY": 4}`.
UNKNOWN reasons: `{"MISSING_EXECUTION_BAR": 2, "MISSING_EXPOSED_BAR": 2}`.
Unknown possible entries: 2; conditional known closures after prior UNKNOWN: 9.

## LONG / SHORT

| Instrument | Side | Signals | Closed | UNKNOWN | PF C1 price | PF C1 R | Net R | Expectancy R | Win rate |
|---|---|---|---|---|---|---|---|---|---|
| USDRUBF | SHORT | 165 | 130 | 4 | 0.887179 | 0.662617 | -24.527043 | -0.188670 | 0.392308 |
| USDRUBF | LONG | 141 | 116 | 3 | 0.767316 | 0.720693 | -17.206502 | -0.148332 | 0.413793 |
| CNYRUBF | SHORT | 121 | 72 | 20 | 0.810526 | 0.649334 | -12.800731 | -0.177788 | 0.388889 |
| CNYRUBF | LONG | 94 | 52 | 19 | 0.505345 | 0.537322 | -15.337276 | -0.294948 | 0.346154 |
| GLDRUBF | SHORT | 47 | 24 | 11 | 0.704686 | 1.122384 | 1.113411 | 0.046392 | 0.416667 |
| GLDRUBF | LONG | 51 | 27 | 11 | 1.408078 | 1.713606 | 6.971724 | 0.258212 | 0.629630 |
| IMOEXF | SHORT | 8 | 5 | 2 | 0.203704 | 0.265645 | -3.810945 | -0.762189 | 0.400000 |
| IMOEXF | LONG | 10 | 4 | 2 | 0.000000 | 0.000000 | -3.003623 | -0.750906 | 0.000000 |

## Twelve calendar months — conditional known closures

Month attribution uses signal date. Zero closures with observed data have Net R 0 and undefined PF; no source coverage is shown as —, never manufactured as a flat profitable month.

| Month | Instrument | Closed | UNKNOWN | PF C1 price | Net R | Expectancy R | Coverage | Complete/incomplete/pre-inception days |
|---|---|---|---|---|---|---|---|---|
| 2023-01 | USDRUBF | 11 | 1 | 0.623932 | -0.168379 | -0.015307 | UNKNOWN | 16/5/0 |
| 2023-01 | CNYRUBF | 8 | 1 | 0.217391 | -3.066667 | -0.383333 | UNKNOWN | 3/18/0 |
| 2023-01 | GLDRUBF | 0 | 0 | — | — | — | NO_COVERAGE | 0/0/21 |
| 2023-01 | IMOEXF | 0 | 0 | — | — | — | NO_COVERAGE | 0/0/21 |
| 2023-02 | USDRUBF | 13 | 2 | 1.510417 | 1.385038 | 0.106541 | UNKNOWN | 15/4/0 |
| 2023-02 | CNYRUBF | 9 | 4 | 0.461538 | -1.266667 | -0.140741 | UNKNOWN | 1/18/0 |
| 2023-02 | GLDRUBF | 0 | 0 | — | — | — | NO_COVERAGE | 0/0/19 |
| 2023-02 | IMOEXF | 0 | 0 | — | — | — | NO_COVERAGE | 0/0/19 |
| 2023-03 | USDRUBF | 23 | 1 | 0.950413 | -4.508139 | -0.196006 | UNKNOWN | 19/3/0 |
| 2023-03 | CNYRUBF | 2 | 4 | 0.333333 | -0.250000 | -0.125000 | UNKNOWN | 0/22/0 |
| 2023-03 | GLDRUBF | 0 | 0 | — | — | — | NO_COVERAGE | 0/0/22 |
| 2023-03 | IMOEXF | 0 | 0 | — | — | — | NO_COVERAGE | 0/0/22 |
| 2023-04 | USDRUBF | 17 | 1 | 1.012987 | -3.886841 | -0.228638 | UNKNOWN | 15/5/0 |
| 2023-04 | CNYRUBF | 7 | 7 | 0.941176 | -1.266667 | -0.180952 | UNKNOWN | 2/18/0 |
| 2023-04 | GLDRUBF | 0 | 0 | — | — | — | NO_COVERAGE | 0/0/20 |
| 2023-04 | IMOEXF | 0 | 0 | — | — | — | NO_COVERAGE | 0/0/20 |
| 2023-05 | USDRUBF | 23 | 0 | 0.519824 | -7.812535 | -0.339675 | PARTIAL_DATA | 18/3/0 |
| 2023-05 | CNYRUBF | 6 | 4 | 0.647059 | -0.785714 | -0.130952 | UNKNOWN | 0/21/0 |
| 2023-05 | GLDRUBF | 0 | 0 | — | — | — | NO_COVERAGE | 0/0/21 |
| 2023-05 | IMOEXF | 0 | 0 | — | — | — | NO_COVERAGE | 0/0/21 |
| 2023-06 | USDRUBF | 21 | 1 | 1.580000 | 2.034830 | 0.096897 | UNKNOWN | 17/4/0 |
| 2023-06 | CNYRUBF | 3 | 8 | 2.666667 | 1.000000 | 0.333333 | UNKNOWN | 1/20/0 |
| 2023-06 | GLDRUBF | 0 | 0 | — | — | — | NO_COVERAGE | 0/0/21 |
| 2023-06 | IMOEXF | 0 | 0 | — | — | — | NO_COVERAGE | 0/0/21 |
| 2023-07 | USDRUBF | 23 | 0 | 0.656489 | -11.433184 | -0.497095 | PARTIAL_DATA | 20/1/0 |
| 2023-07 | CNYRUBF | 11 | 7 | 0.432432 | -6.109341 | -0.555395 | UNKNOWN | 2/19/0 |
| 2023-07 | GLDRUBF | 3 | 4 | 1.049724 | 1.864134 | 0.621378 | UNKNOWN | 0/15/6 |
| 2023-07 | IMOEXF | 0 | 0 | — | — | — | NO_COVERAGE | 0/0/21 |
| 2023-08 | USDRUBF | 23 | 0 | 1.011450 | 0.548307 | 0.023839 | PARTIAL_DATA | 21/2/0 |
| 2023-08 | CNYRUBF | 14 | 2 | 1.269231 | -2.366667 | -0.169048 | UNKNOWN | 9/14/0 |
| 2023-08 | GLDRUBF | 9 | 1 | 1.497951 | 2.456861 | 0.272985 | UNKNOWN | 0/23/0 |
| 2023-08 | IMOEXF | 0 | 0 | — | — | — | NO_COVERAGE | 0/0/23 |
| 2023-09 | USDRUBF | 20 | 0 | 0.375000 | -6.018665 | -0.300933 | PARTIAL_DATA | 19/2/0 |
| 2023-09 | CNYRUBF | 13 | 1 | 0.270833 | -3.586957 | -0.275920 | UNKNOWN | 7/14/0 |
| 2023-09 | GLDRUBF | 3 | 5 | 0.167832 | -0.807386 | -0.269129 | UNKNOWN | 0/21/0 |
| 2023-09 | IMOEXF | 0 | 0 | — | — | — | NO_COVERAGE | 0/0/21 |
| 2023-10 | USDRUBF | 24 | 0 | 0.665323 | -5.548176 | -0.231174 | CONDITIONAL_AFTER_UNKNOWN | 22/0/0 |
| 2023-10 | CNYRUBF | 15 | 0 | 0.952381 | -3.807971 | -0.253865 | PARTIAL_DATA | 20/2/0 |
| 2023-10 | GLDRUBF | 13 | 4 | 1.435065 | 3.077191 | 0.236707 | UNKNOWN | 1/21/0 |
| 2023-10 | IMOEXF | 0 | 0 | — | — | — | NO_COVERAGE | 0/0/22 |
| 2023-11 | USDRUBF | 25 | 1 | 1.057692 | -7.144228 | -0.285769 | UNKNOWN | 21/1/0 |
| 2023-11 | CNYRUBF | 16 | 1 | 0.810651 | -3.305365 | -0.206585 | UNKNOWN | 16/6/0 |
| 2023-11 | GLDRUBF | 9 | 5 | 2.345946 | 0.414556 | 0.046062 | UNKNOWN | 1/21/0 |
| 2023-11 | IMOEXF | 0 | 1 | — | 0.000000 | — | UNKNOWN | 0/13/9 |
| 2023-12 | USDRUBF | 23 | 0 | 0.732673 | 0.818425 | 0.035584 | CONDITIONAL_AFTER_UNKNOWN | 21/0/0 |
| 2023-12 | CNYRUBF | 20 | 0 | 0.603960 | -3.325993 | -0.166300 | CONDITIONAL_AFTER_UNKNOWN | 21/0/0 |
| 2023-12 | GLDRUBF | 14 | 3 | 0.582809 | 1.079779 | 0.077127 | UNKNOWN | 3/18/0 |
| 2023-12 | IMOEXF | 9 | 3 | 0.125000 | -6.814568 | -0.757174 | UNKNOWN | 2/19/0 |

## Source coverage and UNKNOWN

| Instrument | Source M5 rows | First observation | Complete/incomplete/pre-inception days | Missing/invalid slots | Unavailable opening slots (coverage only) |
|---|---|---|---|---|---|
| USDRUBF | 42576 | 2023-01-03 09:00:00+03:00 | 224/30/0 | 187/0 | 2 |
| CNYRUBF | 39362 | 2023-01-03 09:00:00+03:00 | 82/172/0 | 1270/0 | 6 |
| GLDRUBF | 18428 | 2023-07-11 10:00:00+03:00 | 5/119/130 | 932/0 | 9 |
| IMOEXF | 4429 | 2023-11-14 10:00:00+03:00 | 2/32/220 | 566/0 | 4 |

Coverage uses the unchanged approved full research-window grid, conservatively including slots outside R16 signal windows. All physical 2023 rows, including morning/evening observations, warm ATR. No bars/days are filled. GLD and IMOEX pre-inception periods stay unavailable.
September 13 halt is diagnosed; other absence causes remain unproven. Missing waiting bars reject without submission. Missing entry Open creates UNKNOWN possible fill; missing exposed bar / mandatory exit retains UNKNOWN with blank net. See coverage_events.csv and unknown_report.csv.
One UNKNOWN blocks only its own day. Following days require an explicit conditional FLAT assumption, not proof of broker FLAT. UNKNOWN economics cannot be used to form a continuous annual result.

## Frozen adaptation and historical provenance

Historical commit `728d23e25d4bd41fdb6d50e134d1f099c206c6b2`, candidate `C16-eda8af2caeee1259`; 72 tested parameter sets, 0 strict survivors. Historical 126 trades / 81 days / 4 positive months / BASE PF 1.498609 / STRESS PF 1.255979 are selection provenance only and are not this Baseline.
Historical parameters remain W=8, width_atr=2.0, breakout_ticks=1, stop_mode=OPPOSITE, target_r=1.5; ATR14 references the previous completed bar. Previously viewed 2026-01-05 through 2026-05-15 cannot later qualify as independent R16 TRUE OOS.
Config frozen in commit `f0b908d3701c4fc140a4f66f4a689c3e3c2e5aee` before any R16 P&L; SHA-256 `29be35e1a583e279bd2a9a9018117ba6c97a0914a37bed529f9a4062e89f8265`. No subsequent parameter changes.

- **ATR14:** Existing core Indicators arithmetic mean of 14 genuine trailing true ranges, causal and continuous across days/sessions; adjacent previous close only, otherwise H-L. All physically available pinned 2023 observations warm ATR, no pre-2023 fabrication. ATR_ref is the saved snapshot at the last completed compression bar, excluding current breakout. Missing/not-ready/zero ATR_ref rejects with a diagnostic.
- **M1_non_equivalence:** New M5 research, not exact reproduction of the historical 2026 M1 execution. Original hold 120 available M1 rows becomes 120 calendar minutes from model entry or earlier mandatory intraday flat.
- **breakout:** LONG Open<=high and Close>=high+one dated tick; SHORT Open>=low and Close<=low-one dated tick. Both-side ambiguity rejects. No trend, volume, ATR-strength or MTF filter; trustworthy OHLCV validation remains common.
- **compression:** Exactly eight immediately preceding completed valid M5 bars, same date and same continuous approved calendar session, exactly 5-minute spacing. Reset local window on missing/invalid bar, day or session boundary. Current breakout is excluded. Compression may use approved session bars outside the signal windows.
- **cost:** C1 common ledger: one corresponding dated historical tick each side; no scenario-price substitutions or own execution/cost model.
- **entry:** Completed breakout -> one whole next M5 closes -> model next-interval Open. Common one pending/open position, no daily signal quota. Open-only entry admission. Missing waiting rejects; missing execution Open UNKNOWN.
- **exit:** Earliest entry+120 calendar minutes, calendar session end-5 minutes, or exact Open 17:00. Core Stop-first and adverse Stop gap at Open; no Take on entry bar. At 17:00 use only Open, no later OHLC. No entry at effective deadline.
- **scope:** One fixed Baseline only. No Optimization, Robustness, Walk Forward, TRUE OOS, LIVE or automatic advancement.
- **signal_windows:** Inclusive M5 START labels 10:00–12:55 and 14:00–16:50, intersect approved sessions. Afternoon first 14:05 normally / 14:15 March 13–20. Compression never crosses lunch. Execution uses approved calendar session, not a new restriction to signal-start windows.
- **stop:** OPPOSITE: LONG compression_low-one breakout dated tick / SHORT compression_high+one breakout dated tick. Source boundaries must lie on historical breakout grid; consequently Stop is exactly on grid. Core rejects non-adverse Stop versus actual model entry Open, with no minimum-distance filter.
- **target:** Core target at 1.5 initial gross risk, outward historical entry-grid rounding: LONG ceiling / SHORT floor.
- **unknown:** Unresolved day blocked; later independent days conditionally assume FLAT. Incomplete coverage/UNKNOWN leave confirmed annual PF, Net R, DD and other economics null; known closures reported conditionally.

## Classification and validation

The status is computed from actual results, not copied from ORB. Frozen sufficient-evidence criteria: >=30 closures, >=15 trade days, >=3 active and positive months, >=60% positive active months, PF C1 price and R >=1.6, positive expectancy, largest winner <=25% of positive R and largest positive month <=50% of positive monthly R. Complete coverage and resolved outcomes are required for a confirmed pass. Four-instrument overall assessment requires sufficient evidence from every declared instrument.
Independent source/strategy/execution oracle and independent CSV metric reconstruction: audit.json and Independent_Audit.md. Technical tests, two additional deterministic runs and canonical ORB / R17 regressions: validation.json. Independent implementation audit is not an external reviewer signoff; PR remains Draft for independent review.
All common core modules remain byte-unchanged; the existing PR #466 exact daily deadline and generic computed classification are reused. Prior canonical ORB artifacts/config/strategy and all frozen studies are protected. TradingSystemLab and market-pattern-data remain unchanged.
Reproduce: `python3 IntradayLab/tools/run_r16_baseline.py --data-root /workspace/market-pattern-data --output IntradayLab/work/r16_replay` then `python3 IntradayLab/tools/audit_r16_baseline.py --data-root /workspace/market-pattern-data --output IntradayLab/work/r16_replay`.
Source commit `f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8`; exact verified 2023 byte prefixes only. No 2024 or 2025+ price bytes read. C1 is a research cost assumption, not verified broker fees or execution capacity.
Baseline → Optimization → Robustness → Walk Forward → TRUE OOS. This task stops at Baseline and Draft PR: no Merge, Optimization, Robustness, Walk Forward, TRUE OOS or LIVE.
