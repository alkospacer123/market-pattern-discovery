# Stage 6.7 N4 FULL — focused four-case test

**Status: `STAGE_6_7_N4_FULL_FOUR_CASE_TEST_COMPLETE`**

## Contract
- Frozen equality tolerance: `1e-09`.
- Exactly N4_01 / FULL / CANONICAL+TRAIL1 / R15+R20; no optimizer or annual sign gate.
- 2023 is retained as `PARTIAL_N4_DIAGNOSTIC_YEAR`; headline window is 2024 through 2026-09-15T21:00:00+00:00.
- Production is continuous baseline → historical TRUE OOS and merely rebased at 2024; WF24 is isolated.
- Same-time events use EXIT before ENTRY. Stage 6.8 is NOT STARTED; Stage 7 is NOT EXECUTED.

## Headline metrics
| case_id                     |   return_2024_pct |   WF24_return_pct |   return_2025_pct |   return_2026_YTD_pct |   CAGR_2024_plus_pct |   compounded_return_2024_plus_pct |   max_realized_equity_DD_2024_plus_pct |   recovery_factor |   positive_quarter_share |   positive_month_share |
|:----------------------------|------------------:|------------------:|------------------:|----------------------:|---------------------:|----------------------------------:|---------------------------------------:|------------------:|-------------------------:|-----------------------:|
| CANONICAL__N4_01__FULL__R15 |        129.878788 |         70.187220 |         61.018882 |             99.123575 |           109.127845 |                        637.052436 |                             -16.344766 |         38.975929 |                 0.900000 |               0.636364 |
| TRAIL1__N4_01__FULL__R15    |        165.280420 |         91.523729 |         74.383151 |             88.310619 |           122.444496 |                        771.133120 |                             -19.959839 |         38.634236 |                 1.000000 |               0.696970 |
| CANONICAL__N4_01__FULL__R20 |        195.581862 |         99.456611 |         83.989336 |            145.495487 |           160.441570 |                       1235.100459 |                             -21.271098 |         58.064725 |                 0.900000 |               0.636364 |
| TRAIL1__N4_01__FULL__R20    |        256.814209 |        133.146179 |        104.697503 |            127.018253 |           182.141418 |                       1558.118109 |                             -25.877394 |         60.211553 |                 1.000000 |               0.696970 |

## Direct answers
1. **R15:** TRAIL1 has the higher CAGR (122.444% vs 109.128%), with a larger drawdown.
2. **R20:** TRAIL1 has the higher CAGR (182.141% vs 160.442%), with a larger drawdown.
3–4. **CANONICAL R20 vs R15:** compounded return +598.048 pp, CAGR +51.314 pp, absolute DD +4.926 pp, max nominal exposure +2.000 pp.
3–4. **TRAIL1 R20 vs R15:** compounded return +786.985 pp, CAGR +59.697 pp, absolute DD +5.918 pp, max nominal exposure +2.000 pp.

5. **Leaders:** return: `TRAIL1__N4_01__FULL__R20`; drawdown: `CANONICAL__N4_01__FULL__R15`; quarter_stability: `TRAIL1__N4_01__FULL__R20`; month_stability: `TRAIL1__N4_01__FULL__R15`; recovery: `TRAIL1__N4_01__FULL__R20`; risk_efficiency: `CANONICAL__N4_01__FULL__R20`; oos_2025: `TRAIL1__N4_01__FULL__R20`; ytd_2026: `CANONICAL__N4_01__FULL__R20`.
6. TRAIL1 provides economically material extra return/CAGR at both risks, but not for free: drawdown rises; this is a trade-off rather than dominance.
7. R20 adds substantial return and also drawdown/exposure. Incremental CAGR/DD is reported explicitly; whether it compensates is a risk-budget decision, not an optimizer verdict.
8. Removing the partial-2023 sign gate keeps all four cases visible and moves the headline to comparable 2024+ history; it does not alter any frozen trade.
9. **Transparent production-consideration view:** TRAIL1 R15 is the more balanced growth/risk profile when return and risk efficiency are considered together; CANONICAL R15 remains the minimum-DD choice, while both R20 profiles require accepting the documented 8% nominal ceiling. No composite score was used.

## Provenance and limitations
MAE/MFE are unavailable in the frozen registry. Trade statistics are variant-level because risk changes sizing, not the trade path. Instrument-year signs are diagnostic only. Transaction costs are inherited from frozen Stage 6.6 strategy-R evidence and the lifecycle `C1` contract; no trades or strategy parameters were changed.
