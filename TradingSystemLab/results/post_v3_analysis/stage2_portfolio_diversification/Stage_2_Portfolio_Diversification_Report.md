# Stage 2 — Portfolio / Diversification Analysis

## 1. Scope

Artifact-only descriptive analysis of Stage 1-authenticated committed C1 ledgers. No strategy execution, optimization, ranking, weighting, production selection, or trade modification was performed.

## 2. Research history

v2 is the quarterly-futures diversification experiment (Si, CNY, GD, BR, MIX, NG). v3 is the perpetual-futures stability replication (USDRUBF, CNYRUBF, GLDRUBF, IMOEXF). Cross-generation results are `PARTIALLY_COMPARABLE`.

## 3. Portfolio monthly behavior

The tables preserve generation, lifecycle, strategy, and timeframe. TRUE OOS is presented first below, then Walk Forward; baseline is context only.

### true_oos

| generation | study | months | total R | positive share | std | worst | monthly equity DD |
|---|---:|---:|---:|---:|---:|---:|---:|
| v2 | T2/M30 | 21 | 140.0113 | 0.571 | 20.6822 | -10.4861 | -10.9827 |
| v2 | T2/H1 | 21 | 38.7324 | 0.476 | 6.6220 | -5.3157 | -18.8941 |
| v2 | T3/M30 | 21 | 155.7503 | 0.714 | 12.5231 | -11.7654 | -11.7654 |
| v2 | T3/H1 | 20 | 64.3353 | 0.650 | 7.8022 | -7.7732 | -11.2055 |
| v3 | T2/M30 | 21 | 33.1830 | 0.429 | 8.0765 | -11.1035 | -21.4345 |
| v3 | T2/H1 | 21 | 65.5357 | 0.619 | 7.2026 | -5.8838 | -6.1756 |
| v3 | T3/M30 | 21 | 156.4722 | 0.571 | 13.0670 | -6.1749 | -16.3170 |
| v3 | T3/H1 | 20 | 84.4311 | 0.650 | 9.3479 | -5.0252 | -9.0191 |

### walk_forward

| generation | study | months | total R | positive share | std | worst | monthly equity DD |
|---|---:|---:|---:|---:|---:|---:|---:|
| v2 | T2/M30 | 12 | 14.0842 | 0.583 | 5.4919 | -12.9235 | -12.9235 |
| v2 | T2/H1 | 12 | 33.5255 | 0.750 | 5.8814 | -4.7592 | -4.7592 |
| v2 | T3/M30 | 12 | 29.5075 | 0.583 | 7.4000 | -7.9171 | -10.0636 |
| v2 | T3/H1 | 8 | 29.0910 | 0.500 | 7.9372 | -4.9425 | -4.9425 |
| v3 | T2/M30 | 12 | 61.3976 | 0.667 | 7.1580 | -1.8889 | -2.2783 |
| v3 | T2/H1 | 12 | 48.3066 | 0.750 | 7.9034 | -4.4306 | -4.4306 |
| v3 | T3/M30 | 12 | 46.6659 | 0.833 | 10.4609 | -9.9868 | -15.5872 |
| v3 | T3/H1 | 8 | 38.2931 | 0.750 | 6.4247 | -1.6159 | -1.6159 |

### baseline

| generation | study | months | total R | positive share | std | worst | monthly equity DD |
|---|---:|---:|---:|---:|---:|---:|---:|
| v2 | T2/M30 | 60 | 179.5001 | 0.617 | 8.1604 | -11.9566 | -21.4315 |
| v2 | T2/H1 | 60 | 194.3682 | 0.617 | 7.0191 | -8.8819 | -14.7572 |
| v2 | T3/M30 | 60 | 257.5740 | 0.683 | 8.0974 | -9.5097 | -19.4247 |
| v2 | T3/H1 | 59 | 151.5507 | 0.593 | 6.8345 | -11.1014 | -13.2700 |
| v3 | T2/M30 | 24 | 96.9116 | 0.667 | 6.6933 | -4.4777 | -9.0918 |
| v3 | T2/H1 | 24 | 80.4869 | 0.583 | 7.0275 | -4.4306 | -5.8457 |
| v3 | T3/M30 | 24 | 130.4352 | 0.833 | 7.7990 | -8.9873 | -8.9873 |
| v3 | T3/H1 | 23 | 82.1732 | 0.652 | 6.5140 | -2.9546 | -6.1155 |

## 4. Cross-instrument relationships

Correlation uses only months where both instruments are historically available. A zero is retained for a valid available no-trade month; pre-availability months are excluded. `LOW_SAMPLE` means fewer than six overlaps. Co-loss, opposite-sign, offset, rescue, and reduction fields are descriptive protection evidence, not quality labels.

## 5. Instrument stability

`instrument_stability_summary.csv` keeps profitability (R, PF, expectancy), monthly stability, and diversification contribution separate. `instrument_contribution_summary.csv` identifies positive/negative contribution, drawdown-episode contribution, and offsets. These facts are not DROP/KEEP decisions.

## 6. Quarterly versus perpetual

Does v3 appear more stable? Evidence is mixed and study-specific. Supporting cases are those where v3 has a higher positive-month share, smaller dispersion/worst month/monthly-equity drawdown, shorter losing streak, fewer synchronized losses, or more loss rescue. Complications are visible wherever those signs reverse. v3 also has fewer instruments and different periods and coverage, so higher standalone profitability cannot establish construction superiority. Every comparison remains `PARTIALLY_COMPARABLE`.

## 7. T2 versus T3

T2 and T3 remain separate in every artifact. Their distributions may be compared descriptively, but no strategy rank or winner is produced.

## 8. M30 versus H1

M30 and H1 remain separate in every artifact. Differences in monthly dispersion, synchronized loss, and offset behavior are evidence only, not selection.

## 9. Leave-one-out diagnostics

Each row removes exactly one instrument from the full equal-unit-R universe. Deltas report the factual change in total R, positive-month share, monthly standard deviation, worst month, and monthly-equity drawdown. They do not prescribe elimination.

## 10. Stage 3 implications

Stage 3 should investigate why repeated bad months occur and whether losses cluster by session, direction, holding time, MAE/MFE, or exit reason. None of those trade-anatomy hypotheses is tested here.

## Definitions

* Portfolio monthly R is the unweighted sum of canonical instrument R.
* `AVAILABLE` has trades; `NO_TRADES` is an available month with zero trades; `NOT_YET_AVAILABLE` precedes the first authenticated observation in that study and is excluded from pair calculations.
* Offset: at least one positive and one negative instrument. Rescue: a loss exists but portfolio R is positive. Reduction: portfolio R remains negative while a positive instrument offsets part of losses.
* All-negative/all-positive requires every currently available instrument to have that strict sign. `same_sign_*_count` is the available-instrument count in such a month, otherwise zero.
* `monthly_equity_max_drawdown_R` is peak-to-trough drawdown of cumulative monthly R, not trade-level drawdown.
