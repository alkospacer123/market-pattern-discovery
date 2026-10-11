# Optimization C Return/Retest/Rejection — USDRUBF 2023

**NO QUALIFYING OPTIMIZATION CANDIDATE**

Base `297137fe17f0de851976ea26180fac441f2ada6e`; pre-P&L freeze `daeba033cd985bd678193df9622bae686ef83782`. 288/288 configurations. No added parameter values or adaptive trials.
Only pinned USDRUBF 2023 development M5. 2024 is reserved for Walk Forward; 2025+ TRUE OOS was unread. No next lifecycle stage was run.
CLOSED-only economics after model C1 are conditional on incomplete source/outcomes and assumed FLAT after exclusions. They do not establish complete annual profit, continuous account equity, or future profitability.
One fixed first strict local level per direction; 2/3 distinct approaches separated by whole-M5 retreats. Final first-touch Close alone confirms rejection; failed Close consumes until structural reset. Structural Stop uses all observed construction extrema plus the frozen buffer. Completed M5 only, immediate next Open, no delayed entry, unchanged Backtester/V2, Stop-first, adverse Open gaps, no entry-bar Take, 120-minute/session-flat limit.
Gross Take distance = target_net_R × (initial_gross_risk + planned_C1) + planned_C1, outward price-grid rounding. net_R_c1 uses initial gross risk, planned_net_to_net_R uses risk + planned C1, realized_net_to_net_R uses risk + actual C1. Denominators never depend on trade profitability.
Selection: 100 CLOSED, 40 distinct entry dates, 6 active entry months; PF R/price both ≥2, expectancy >0, ≥9 positive exit months, conditional DD ≤20R, winner concentration ≤25%, positive-month concentration ≤50%. Two adjacent list-index neighbors require 100 CLOSED, PF R ≥1.5, expectancy >0. Only full passes are ranked by positive months DESC, min(PF R,price) DESC, DD ASC, CLOSED DESC, ID ASC.
Detailed CSVs are sharded by evaluation in evaluations/<configuration_id>/USDRUBF/: signals.csv, construction_events.csv, trades.csv, data_gap_skips.csv, data_quality_exclusions.csv, rejected_nonfill.csv, coverage_report.csv, days.csv, construction_diagnostics.csv. detailed_artifact_index.csv lists all 288 directories and counts. This preserves full construction receipts within GitHub file-size limits. No source candles are copied.
No missing month is treated as a positive zero. All 12 exit months are published for each configuration; entry-date counts remain separate. No PF-only winner is selected.

| Evaluated | Sample pass | Both PF pass | Monthly pass | Neighbor pass | Full pass |
|---|---|---|---|---|---|
| 288 | 216 | 0 | 0 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK3_TOL1_MAXBARS24_SB1_TP2

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 324; dates/months 188/12; PF R/price 0.428795/0.435125; Net -231.100000 R; expectancy -0.713272 R; positive months 1/12; conditional DD 234.366667 R.
Accepted 327 = CLOSED 324 + EXCLUDED 3; SKIP 0; exclusion share 0.009174; conditional FLAT closures 220; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 14 | -3.700000 | 0.763326 | 0.877193 | 7 | 0 |
| 2023-02 | 34 | -23.000000 | 0.436275 | 0.423077 | 5 | 0 |
| 2023-03 | 32 | -23.533333 | 0.392427 | 0.429530 | 4 | 0 |
| 2023-04 | 31 | -21.000000 | 0.455017 | 0.537931 | 6 | 2 |
| 2023-05 | 32 | -23.250000 | 0.410895 | 0.386076 | 7 | 1 |
| 2023-06 | 33 | -25.266667 | 0.402208 | 0.379085 | 4 | 0 |
| 2023-07 | 29 | -39.033333 | 0.078678 | 0.063291 | 1 | 0 |
| 2023-08 | 18 | -4.700000 | 0.786039 | 0.835443 | 109 | 0 |
| 2023-09 | 27 | 2.300000 | 1.086792 | 1.112245 | 43 | 0 |
| 2023-10 | 21 | -16.883333 | 0.359266 | 0.336634 | 0 | 0 |
| 2023-11 | 25 | -23.833333 | 0.295567 | 0.243902 | 1 | 0 |
| 2023-12 | 28 | -29.200000 | 0.234266 | 0.255034 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK3_TOL1_MAXBARS24_SB1_TP3

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 319; dates/months 188/12; PF R/price 0.473019/0.474026; Net -214.683333 R; expectancy -0.672989 R; positive months 1/12; conditional DD 218.483333 R.
Accepted 322 = CLOSED 319 + EXCLUDED 3; SKIP 0; exclusion share 0.009317; conditional FLAT closures 217; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 14 | -1.400000 | 0.910448 | 1.122807 | 7 | 0 |
| 2023-02 | 34 | -19.250000 | 0.528186 | 0.512821 | 5 | 0 |
| 2023-03 | 31 | -20.883333 | 0.439123 | 0.461538 | 4 | 0 |
| 2023-04 | 30 | -21.733333 | 0.434519 | 0.472603 | 6 | 2 |
| 2023-05 | 32 | -16.766667 | 0.575169 | 0.537975 | 7 | 1 |
| 2023-06 | 32 | -25.600000 | 0.391924 | 0.331169 | 4 | 0 |
| 2023-07 | 29 | -44.033333 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 17 | -4.333333 | 0.800307 | 0.802469 | 109 | 0 |
| 2023-09 | 26 | 4.700000 | 1.167857 | 1.163462 | 43 | 0 |
| 2023-10 | 21 | -12.150000 | 0.538899 | 0.504950 | 0 | 0 |
| 2023-11 | 25 | -28.500000 | 0.197183 | 0.164062 | 1 | 0 |
| 2023-12 | 28 | -24.733333 | 0.351399 | 0.382550 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK3_TOL1_MAXBARS24_SB1_TP4

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 316; dates/months 188/12; PF R/price 0.440640/0.441801; Net -230.633333 R; expectancy -0.729852 R; positive months 0/12; conditional DD 235.433333 R.
Accepted 320 = CLOSED 316 + EXCLUDED 4; SKIP 0; exclusion share 0.012500; conditional FLAT closures 267; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 14 | -1.300000 | 0.916844 | 1.105263 | 7 | 0 |
| 2023-02 | 34 | -18.833333 | 0.538399 | 0.512821 | 5 | 0 |
| 2023-03 | 29 | -28.483333 | 0.237054 | 0.253521 | 4 | 1 |
| 2023-04 | 30 | -17.166667 | 0.553339 | 0.595890 | 6 | 2 |
| 2023-05 | 32 | -11.933333 | 0.697635 | 0.639241 | 7 | 1 |
| 2023-06 | 32 | -30.266667 | 0.281077 | 0.240260 | 4 | 0 |
| 2023-07 | 29 | -44.033333 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 17 | -4.183333 | 0.807220 | 0.827160 | 109 | 0 |
| 2023-09 | 26 | -5.983333 | 0.808021 | 0.817391 | 43 | 0 |
| 2023-10 | 20 | -21.350000 | 0.237954 | 0.188679 | 0 | 0 |
| 2023-11 | 25 | -26.833333 | 0.244131 | 0.203125 | 1 | 0 |
| 2023-12 | 28 | -20.266667 | 0.468531 | 0.510067 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK3_TOL1_MAXBARS24_SB1_TP5

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 316; dates/months 188/12; PF R/price 0.419183/0.426198; Net -241.416667 R; expectancy -0.763977 R; positive months 1/12; conditional DD 247.250000 R.
Accepted 320 = CLOSED 316 + EXCLUDED 4; SKIP 0; exclusion share 0.012500; conditional FLAT closures 267; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 14 | 1.600000 | 1.102345 | 1.333333 | 7 | 0 |
| 2023-02 | 34 | -27.166667 | 0.360283 | 0.372671 | 5 | 0 |
| 2023-03 | 29 | -27.983333 | 0.250446 | 0.267606 | 4 | 1 |
| 2023-04 | 30 | -18.650000 | 0.514744 | 0.541096 | 6 | 2 |
| 2023-05 | 32 | -12.100000 | 0.693412 | 0.645570 | 7 | 1 |
| 2023-06 | 32 | -28.600000 | 0.320665 | 0.272727 | 4 | 0 |
| 2023-07 | 29 | -44.033333 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 17 | -2.783333 | 0.871736 | 0.913580 | 109 | 0 |
| 2023-09 | 26 | -15.250000 | 0.535533 | 0.616667 | 43 | 0 |
| 2023-10 | 20 | -19.683333 | 0.297442 | 0.235849 | 0 | 0 |
| 2023-11 | 25 | -25.166667 | 0.291080 | 0.242188 | 1 | 0 |
| 2023-12 | 28 | -21.600000 | 0.433566 | 0.442953 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK3_TOL1_MAXBARS24_SB1_TP6

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 316; dates/months 188/12; PF R/price 0.448053/0.454952; Net -229.416667 R; expectancy -0.726002 R; positive months 1/12; conditional DD 236.750000 R.
Accepted 320 = CLOSED 316 + EXCLUDED 4; SKIP 0; exclusion share 0.012500; conditional FLAT closures 267; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 14 | 3.300000 | 1.211087 | 1.456140 | 7 | 0 |
| 2023-02 | 34 | -27.166667 | 0.360283 | 0.372671 | 5 | 0 |
| 2023-03 | 29 | -27.983333 | 0.250446 | 0.267606 | 4 | 1 |
| 2023-04 | 30 | -16.983333 | 0.558109 | 0.575342 | 6 | 2 |
| 2023-05 | 32 | -8.933333 | 0.773649 | 0.715190 | 7 | 1 |
| 2023-06 | 32 | -30.933333 | 0.265241 | 0.227273 | 4 | 0 |
| 2023-07 | 29 | -44.033333 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 17 | -1.383333 | 0.936252 | 1.000000 | 109 | 0 |
| 2023-09 | 26 | -13.850000 | 0.578173 | 0.675000 | 43 | 0 |
| 2023-10 | 20 | -18.016667 | 0.356930 | 0.283019 | 0 | 0 |
| 2023-11 | 25 | -23.500000 | 0.338028 | 0.281250 | 1 | 0 |
| 2023-12 | 28 | -19.933333 | 0.477273 | 0.476510 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK3_TOL1_MAXBARS24_SB1_TP7

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 316; dates/months 188/12; PF R/price 0.435401/0.450318; Net -235.616667 R; expectancy -0.745622 R; positive months 2/12; conditional DD 244.450000 R.
Accepted 320 = CLOSED 316 + EXCLUDED 4; SKIP 0; exclusion share 0.012500; conditional FLAT closures 267; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 14 | 4.800000 | 1.307036 | 1.561404 | 7 | 0 |
| 2023-02 | 34 | -27.166667 | 0.360283 | 0.372671 | 5 | 0 |
| 2023-03 | 29 | -27.983333 | 0.250446 | 0.267606 | 4 | 1 |
| 2023-04 | 30 | -15.316667 | 0.601474 | 0.609589 | 6 | 2 |
| 2023-05 | 32 | -12.766667 | 0.676520 | 0.651899 | 7 | 1 |
| 2023-06 | 32 | -30.933333 | 0.265241 | 0.227273 | 4 | 0 |
| 2023-07 | 29 | -44.033333 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 17 | 0.016667 | 1.000768 | 1.086420 | 109 | 0 |
| 2023-09 | 26 | -12.450000 | 0.620812 | 0.733333 | 43 | 0 |
| 2023-10 | 20 | -16.350000 | 0.416419 | 0.330189 | 0 | 0 |
| 2023-11 | 25 | -21.833333 | 0.384977 | 0.320312 | 1 | 0 |
| 2023-12 | 28 | -31.600000 | 0.206030 | 0.266234 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK3_TOL1_MAXBARS24_SB1_TP8

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 316; dates/months 188/12; PF R/price 0.425029/0.432467; Net -240.750000 R; expectancy -0.761867 R; positive months 1/12; conditional DD 251.083333 R.
Accepted 320 = CLOSED 316 + EXCLUDED 4; SKIP 0; exclusion share 0.012500; conditional FLAT closures 267; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 14 | 6.300000 | 1.402985 | 1.666667 | 7 | 0 |
| 2023-02 | 34 | -27.166667 | 0.360283 | 0.372671 | 5 | 0 |
| 2023-03 | 29 | -27.983333 | 0.250446 | 0.267606 | 4 | 1 |
| 2023-04 | 30 | -13.650000 | 0.644840 | 0.643836 | 6 | 2 |
| 2023-05 | 32 | -11.266667 | 0.714527 | 0.689873 | 7 | 1 |
| 2023-06 | 32 | -30.933333 | 0.265241 | 0.227273 | 4 | 0 |
| 2023-07 | 29 | -44.033333 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 17 | -11.183333 | 0.515873 | 0.443182 | 109 | 0 |
| 2023-09 | 26 | -11.050000 | 0.663452 | 0.791667 | 43 | 0 |
| 2023-10 | 20 | -14.683333 | 0.475907 | 0.377358 | 0 | 0 |
| 2023-11 | 25 | -23.500000 | 0.338028 | 0.281250 | 1 | 0 |
| 2023-12 | 28 | -31.600000 | 0.206030 | 0.266234 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK3_TOL1_MAXBARS24_SB1_TP9

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 316; dates/months 188/12; PF R/price 0.416153/0.417882; Net -244.466667 R; expectancy -0.773629 R; positive months 1/12; conditional DD 256.300000 R.
Accepted 320 = CLOSED 316 + EXCLUDED 4; SKIP 0; exclusion share 0.012500; conditional FLAT closures 267; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 14 | 7.800000 | 1.498934 | 1.771930 | 7 | 0 |
| 2023-02 | 34 | -27.166667 | 0.360283 | 0.372671 | 5 | 0 |
| 2023-03 | 29 | -27.983333 | 0.250446 | 0.267606 | 4 | 1 |
| 2023-04 | 30 | -11.983333 | 0.688205 | 0.678082 | 6 | 2 |
| 2023-05 | 32 | -15.016667 | 0.619510 | 0.594937 | 7 | 1 |
| 2023-06 | 32 | -30.933333 | 0.265241 | 0.227273 | 4 | 0 |
| 2023-07 | 29 | -44.033333 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 17 | -11.183333 | 0.515873 | 0.443182 | 109 | 0 |
| 2023-09 | 26 | -15.850000 | 0.517259 | 0.591667 | 43 | 0 |
| 2023-10 | 20 | -13.016667 | 0.535396 | 0.424528 | 0 | 0 |
| 2023-11 | 25 | -23.500000 | 0.338028 | 0.281250 | 1 | 0 |
| 2023-12 | 28 | -31.600000 | 0.206030 | 0.266234 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK3_TOL1_MAXBARS24_SB1_TP10

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 316; dates/months 188/12; PF R/price 0.405405/0.410273; Net -248.966667 R; expectancy -0.787869 R; positive months 1/12; conditional DD 262.300000 R.
Accepted 320 = CLOSED 316 + EXCLUDED 4; SKIP 0; exclusion share 0.012500; conditional FLAT closures 267; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 14 | 9.300000 | 1.594883 | 1.877193 | 7 | 0 |
| 2023-02 | 34 | -27.166667 | 0.360283 | 0.372671 | 5 | 0 |
| 2023-03 | 29 | -27.983333 | 0.250446 | 0.267606 | 4 | 1 |
| 2023-04 | 30 | -10.316667 | 0.731570 | 0.712329 | 6 | 2 |
| 2023-05 | 32 | -15.016667 | 0.619510 | 0.594937 | 7 | 1 |
| 2023-06 | 32 | -30.933333 | 0.265241 | 0.227273 | 4 | 0 |
| 2023-07 | 29 | -44.033333 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 17 | -11.183333 | 0.515873 | 0.443182 | 109 | 0 |
| 2023-09 | 26 | -15.850000 | 0.517259 | 0.591667 | 43 | 0 |
| 2023-10 | 20 | -20.683333 | 0.261749 | 0.207547 | 0 | 0 |
| 2023-11 | 25 | -23.500000 | 0.338028 | 0.281250 | 1 | 0 |
| 2023-12 | 28 | -31.600000 | 0.206030 | 0.266234 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK3_TOL1_MAXBARS24_SB2_TP2

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 430; dates/months 214/12; PF R/price 0.491511/0.506462; Net -248.583333 R; expectancy -0.578101 R; positive months 0/12; conditional DD 248.583333 R.
Accepted 434 = CLOSED 430 + EXCLUDED 4; SKIP 0; exclusion share 0.009217; conditional FLAT closures 319; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 21 | -16.233333 | 0.360053 | 0.500000 | 7 | 0 |
| 2023-02 | 44 | -18.383333 | 0.603807 | 0.583333 | 5 | 0 |
| 2023-03 | 47 | -26.700000 | 0.478855 | 0.500000 | 4 | 1 |
| 2023-04 | 35 | -10.866667 | 0.690702 | 0.814103 | 6 | 2 |
| 2023-05 | 39 | -23.533333 | 0.462709 | 0.492462 | 7 | 1 |
| 2023-06 | 45 | -20.600000 | 0.593421 | 0.537383 | 4 | 0 |
| 2023-07 | 34 | -37.466667 | 0.154251 | 0.126904 | 1 | 0 |
| 2023-08 | 24 | -4.216667 | 0.835286 | 0.798165 | 109 | 0 |
| 2023-09 | 37 | -18.200000 | 0.571092 | 0.633721 | 43 | 0 |
| 2023-10 | 34 | -19.133333 | 0.520868 | 0.569620 | 0 | 0 |
| 2023-11 | 31 | -19.666667 | 0.451163 | 0.375796 | 1 | 0 |
| 2023-12 | 39 | -33.583333 | 0.302768 | 0.342995 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK3_TOL1_MAXBARS24_SB2_TP3

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 415; dates/months 213/12; PF R/price 0.463177/0.477889; Net -264.966667 R; expectancy -0.638474 R; positive months 1/12; conditional DD 266.000000 R.
Accepted 421 = CLOSED 415 + EXCLUDED 6; SKIP 0; exclusion share 0.014252; conditional FLAT closures 373; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 21 | -15.000000 | 0.408673 | 0.560000 | 7 | 0 |
| 2023-02 | 40 | -14.800000 | 0.660291 | 0.647368 | 5 | 1 |
| 2023-03 | 44 | -36.566667 | 0.290886 | 0.295775 | 4 | 2 |
| 2023-04 | 34 | -8.416667 | 0.750494 | 0.865772 | 6 | 2 |
| 2023-05 | 39 | -20.500000 | 0.540359 | 0.566502 | 7 | 1 |
| 2023-06 | 41 | -18.283333 | 0.618965 | 0.504808 | 4 | 0 |
| 2023-07 | 34 | -46.966667 | 0.010534 | 0.014423 | 1 | 0 |
| 2023-08 | 22 | 0.416667 | 1.017532 | 0.970588 | 109 | 0 |
| 2023-09 | 37 | -16.700000 | 0.619879 | 0.685393 | 43 | 0 |
| 2023-10 | 33 | -30.733333 | 0.308327 | 0.305085 | 0 | 0 |
| 2023-11 | 31 | -22.833333 | 0.388393 | 0.331288 | 1 | 0 |
| 2023-12 | 39 | -34.583333 | 0.306020 | 0.386792 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK3_TOL1_MAXBARS24_SB2_TP4

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 415; dates/months 213/12; PF R/price 0.448801/0.465073; Net -276.233333 R; expectancy -0.665622 R; positive months 1/12; conditional DD 278.666667 R.
Accepted 421 = CLOSED 415 + EXCLUDED 6; SKIP 0; exclusion share 0.014252; conditional FLAT closures 373; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 21 | -12.266667 | 0.516426 | 0.710000 | 7 | 0 |
| 2023-02 | 40 | -27.333333 | 0.413028 | 0.400990 | 5 | 1 |
| 2023-03 | 44 | -34.066667 | 0.339367 | 0.347418 | 4 | 2 |
| 2023-04 | 34 | -8.983333 | 0.733696 | 0.838926 | 6 | 2 |
| 2023-05 | 39 | -18.200000 | 0.591928 | 0.625616 | 7 | 1 |
| 2023-06 | 41 | -26.366667 | 0.468949 | 0.380282 | 4 | 0 |
| 2023-07 | 34 | -46.966667 | 0.010534 | 0.014423 | 1 | 0 |
| 2023-08 | 22 | 3.416667 | 1.143759 | 1.098039 | 109 | 0 |
| 2023-09 | 37 | -26.550000 | 0.433096 | 0.476440 | 43 | 0 |
| 2023-10 | 33 | -26.166667 | 0.411103 | 0.406780 | 0 | 0 |
| 2023-11 | 31 | -19.833333 | 0.468750 | 0.404908 | 1 | 0 |
| 2023-12 | 39 | -32.916667 | 0.339465 | 0.419811 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK3_TOL1_MAXBARS24_SB2_TP5

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 414; dates/months 213/12; PF R/price 0.461918/0.474988; Net -270.466667 R; expectancy -0.653301 R; positive months 1/12; conditional DD 274.300000 R.
Accepted 420 = CLOSED 414 + EXCLUDED 6; SKIP 0; exclusion share 0.014286; conditional FLAT closures 372; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 21 | -9.533333 | 0.624179 | 0.860000 | 7 | 0 |
| 2023-02 | 40 | -25.666667 | 0.448819 | 0.425743 | 5 | 1 |
| 2023-03 | 44 | -32.566667 | 0.368455 | 0.375587 | 4 | 2 |
| 2023-04 | 34 | -7.483333 | 0.778162 | 0.879195 | 6 | 2 |
| 2023-05 | 38 | -21.400000 | 0.520179 | 0.522167 | 7 | 1 |
| 2023-06 | 41 | -24.533333 | 0.505874 | 0.399061 | 4 | 0 |
| 2023-07 | 34 | -46.966667 | 0.010534 | 0.014423 | 1 | 0 |
| 2023-08 | 22 | 1.416667 | 1.059607 | 1.078431 | 109 | 0 |
| 2023-09 | 37 | -23.550000 | 0.497153 | 0.544503 | 43 | 0 |
| 2023-10 | 33 | -21.600000 | 0.513878 | 0.508475 | 0 | 0 |
| 2023-11 | 31 | -25.833333 | 0.334764 | 0.284024 | 1 | 0 |
| 2023-12 | 39 | -32.750000 | 0.342809 | 0.410377 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK3_TOL1_MAXBARS24_SB2_TP6

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 414; dates/months 213/12; PF R/price 0.440775/0.462005; Net -281.933333 R; expectancy -0.680998 R; positive months 1/12; conditional DD 287.166667 R.
Accepted 420 = CLOSED 414 + EXCLUDED 6; SKIP 0; exclusion share 0.014286; conditional FLAT closures 372; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 21 | -8.800000 | 0.653088 | 0.890000 | 7 | 0 |
| 2023-02 | 40 | -24.000000 | 0.484610 | 0.450495 | 5 | 1 |
| 2023-03 | 44 | -31.066667 | 0.397544 | 0.403756 | 4 | 2 |
| 2023-04 | 34 | -5.983333 | 0.822628 | 0.919463 | 6 | 2 |
| 2023-05 | 38 | -24.000000 | 0.461883 | 0.477833 | 7 | 1 |
| 2023-06 | 41 | -31.200000 | 0.371601 | 0.305164 | 4 | 0 |
| 2023-07 | 34 | -46.966667 | 0.010534 | 0.014423 | 1 | 0 |
| 2023-08 | 22 | 2.750000 | 1.115708 | 1.156863 | 109 | 0 |
| 2023-09 | 37 | -21.883333 | 0.532740 | 0.591623 | 43 | 0 |
| 2023-10 | 33 | -24.700000 | 0.444111 | 0.457627 | 0 | 0 |
| 2023-11 | 31 | -24.333333 | 0.373391 | 0.319527 | 1 | 0 |
| 2023-12 | 39 | -41.750000 | 0.186688 | 0.261468 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK3_TOL1_MAXBARS24_SB2_TP7

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 413; dates/months 213/12; PF R/price 0.445962/0.459497; Net -279.133333 R; expectancy -0.675868 R; positive months 0/12; conditional DD 285.766667 R.
Accepted 419 = CLOSED 413 + EXCLUDED 6; SKIP 0; exclusion share 0.014320; conditional FLAT closures 371; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 21 | -7.400000 | 0.708279 | 0.960000 | 7 | 0 |
| 2023-02 | 40 | -22.333333 | 0.520401 | 0.475248 | 5 | 1 |
| 2023-03 | 44 | -29.566667 | 0.426632 | 0.431925 | 4 | 2 |
| 2023-04 | 34 | -4.483333 | 0.867095 | 0.959732 | 6 | 2 |
| 2023-05 | 38 | -22.600000 | 0.493274 | 0.512315 | 7 | 1 |
| 2023-06 | 40 | -27.866667 | 0.419243 | 0.336538 | 4 | 0 |
| 2023-07 | 34 | -46.966667 | 0.010534 | 0.014423 | 1 | 0 |
| 2023-08 | 22 | -6.583333 | 0.737716 | 0.636364 | 109 | 0 |
| 2023-09 | 37 | -20.550000 | 0.561210 | 0.633508 | 43 | 0 |
| 2023-10 | 33 | -23.200000 | 0.477869 | 0.491525 | 0 | 0 |
| 2023-11 | 31 | -25.833333 | 0.334764 | 0.284024 | 1 | 0 |
| 2023-12 | 39 | -41.750000 | 0.186688 | 0.261468 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK3_TOL1_MAXBARS24_SB2_TP8

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 413; dates/months 213/12; PF R/price 0.437097/0.445065; Net -283.600000 R; expectancy -0.686683 R; positive months 0/12; conditional DD 291.633333 R.
Accepted 419 = CLOSED 413 + EXCLUDED 6; SKIP 0; exclusion share 0.014320; conditional FLAT closures 371; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 21 | -6.000000 | 0.763469 | 1.030000 | 7 | 0 |
| 2023-02 | 40 | -20.666667 | 0.556192 | 0.500000 | 5 | 1 |
| 2023-03 | 44 | -28.066667 | 0.455721 | 0.460094 | 4 | 2 |
| 2023-04 | 34 | -2.983333 | 0.911561 | 1.000000 | 6 | 2 |
| 2023-05 | 38 | -25.800000 | 0.421525 | 0.433498 | 7 | 1 |
| 2023-06 | 40 | -26.200000 | 0.453977 | 0.360577 | 4 | 0 |
| 2023-07 | 34 | -46.966667 | 0.010534 | 0.014423 | 1 | 0 |
| 2023-08 | 22 | -6.583333 | 0.737716 | 0.636364 | 109 | 0 |
| 2023-09 | 37 | -24.550000 | 0.475801 | 0.507853 | 43 | 0 |
| 2023-10 | 33 | -28.200000 | 0.365341 | 0.378531 | 0 | 0 |
| 2023-11 | 31 | -25.833333 | 0.334764 | 0.284024 | 1 | 0 |
| 2023-12 | 39 | -41.750000 | 0.186688 | 0.261468 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK3_TOL1_MAXBARS24_SB2_TP9

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 413; dates/months 213/12; PF R/price 0.441860/0.451117; Net -281.200000 R; expectancy -0.680872 R; positive months 0/12; conditional DD 290.633333 R.
Accepted 419 = CLOSED 413 + EXCLUDED 6; SKIP 0; exclusion share 0.014320; conditional FLAT closures 371; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 21 | -4.600000 | 0.818660 | 1.100000 | 7 | 0 |
| 2023-02 | 40 | -19.000000 | 0.591983 | 0.524752 | 5 | 1 |
| 2023-03 | 44 | -26.566667 | 0.484809 | 0.488263 | 4 | 2 |
| 2023-04 | 34 | -1.483333 | 0.956028 | 1.040268 | 6 | 2 |
| 2023-05 | 38 | -25.800000 | 0.421525 | 0.433498 | 7 | 1 |
| 2023-06 | 40 | -29.866667 | 0.377562 | 0.307692 | 4 | 0 |
| 2023-07 | 34 | -46.966667 | 0.010534 | 0.014423 | 1 | 0 |
| 2023-08 | 22 | -6.583333 | 0.737716 | 0.636364 | 109 | 0 |
| 2023-09 | 37 | -24.550000 | 0.475801 | 0.507853 | 43 | 0 |
| 2023-10 | 33 | -28.200000 | 0.365341 | 0.378531 | 0 | 0 |
| 2023-11 | 31 | -25.833333 | 0.334764 | 0.284024 | 1 | 0 |
| 2023-12 | 39 | -41.750000 | 0.186688 | 0.261468 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK3_TOL1_MAXBARS24_SB2_TP10

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 412; dates/months 213/12; PF R/price 0.436988/0.446104; Net -282.716667 R; expectancy -0.686206 R; positive months 0/12; conditional DD 293.550000 R.
Accepted 418 = CLOSED 412 + EXCLUDED 6; SKIP 0; exclusion share 0.014354; conditional FLAT closures 370; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 21 | -3.200000 | 0.873850 | 1.170000 | 7 | 0 |
| 2023-02 | 40 | -17.333333 | 0.627774 | 0.549505 | 5 | 1 |
| 2023-03 | 44 | -25.066667 | 0.513898 | 0.516432 | 4 | 2 |
| 2023-04 | 33 | -7.566667 | 0.764033 | 0.861111 | 6 | 2 |
| 2023-05 | 38 | -25.800000 | 0.421525 | 0.433498 | 7 | 1 |
| 2023-06 | 40 | -29.866667 | 0.377562 | 0.307692 | 4 | 0 |
| 2023-07 | 34 | -46.966667 | 0.010534 | 0.014423 | 1 | 0 |
| 2023-08 | 22 | -6.583333 | 0.737716 | 0.636364 | 109 | 0 |
| 2023-09 | 37 | -24.550000 | 0.475801 | 0.507853 | 43 | 0 |
| 2023-10 | 33 | -28.200000 | 0.365341 | 0.378531 | 0 | 0 |
| 2023-11 | 31 | -25.833333 | 0.334764 | 0.284024 | 1 | 0 |
| 2023-12 | 39 | -41.750000 | 0.186688 | 0.261468 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK3_TOL1_MAXBARS36_SB1_TP2

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 303; dates/months 177/12; PF R/price 0.400106/0.414909; Net -225.550000 R; expectancy -0.744389 R; positive months 0/12; conditional DD 225.550000 R.
Accepted 306 = CLOSED 303 + EXCLUDED 3; SKIP 0; exclusion share 0.009804; conditional FLAT closures 202; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 15 | -10.100000 | 0.459893 | 0.579710 | 7 | 0 |
| 2023-02 | 30 | -18.933333 | 0.479853 | 0.474453 | 5 | 0 |
| 2023-03 | 33 | -23.450000 | 0.397172 | 0.439189 | 4 | 0 |
| 2023-04 | 29 | -18.000000 | 0.493433 | 0.586466 | 6 | 2 |
| 2023-05 | 22 | -12.383333 | 0.516276 | 0.466667 | 7 | 1 |
| 2023-06 | 33 | -27.333333 | 0.354331 | 0.320261 | 4 | 0 |
| 2023-07 | 27 | -36.966667 | 0.082713 | 0.066225 | 1 | 0 |
| 2023-08 | 16 | -11.600000 | 0.425743 | 0.533333 | 109 | 0 |
| 2023-09 | 29 | -0.766667 | 0.974070 | 0.990909 | 43 | 0 |
| 2023-10 | 22 | -18.216667 | 0.341963 | 0.314815 | 0 | 0 |
| 2023-11 | 23 | -26.750000 | 0.123908 | 0.107143 | 1 | 0 |
| 2023-12 | 24 | -21.050000 | 0.303749 | 0.322314 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK3_TOL1_MAXBARS36_SB1_TP3

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 297; dates/months 177/12; PF R/price 0.472842/0.477987; Net -198.800000 R; expectancy -0.669360 R; positive months 1/12; conditional DD 201.316667 R.
Accepted 300 = CLOSED 297 + EXCLUDED 3; SKIP 0; exclusion share 0.010000; conditional FLAT closures 199; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 15 | -5.800000 | 0.689840 | 0.869565 | 7 | 0 |
| 2023-02 | 30 | -15.183333 | 0.582875 | 0.576642 | 5 | 0 |
| 2023-03 | 31 | -21.050000 | 0.437166 | 0.464789 | 4 | 0 |
| 2023-04 | 28 | -18.733333 | 0.471308 | 0.514925 | 6 | 2 |
| 2023-05 | 22 | -6.150000 | 0.759766 | 0.685714 | 7 | 1 |
| 2023-06 | 32 | -25.166667 | 0.403162 | 0.337662 | 4 | 0 |
| 2023-07 | 27 | -41.966667 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 15 | -11.233333 | 0.436455 | 0.506494 | 109 | 0 |
| 2023-09 | 28 | 1.633333 | 1.052575 | 1.043103 | 43 | 0 |
| 2023-10 | 22 | -13.483333 | 0.512944 | 0.472222 | 0 | 0 |
| 2023-11 | 23 | -25.083333 | 0.178493 | 0.151786 | 1 | 0 |
| 2023-12 | 24 | -16.583333 | 0.451488 | 0.479339 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK3_TOL1_MAXBARS36_SB1_TP4

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 293; dates/months 177/12; PF R/price 0.439627/0.445139; Net -213.250000 R; expectancy -0.727816 R; positive months 0/12; conditional DD 220.066667 R.
Accepted 297 = CLOSED 293 + EXCLUDED 4; SKIP 0; exclusion share 0.013468; conditional FLAT closures 247; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 15 | -5.700000 | 0.695187 | 0.855072 | 7 | 0 |
| 2023-02 | 30 | -14.766667 | 0.594322 | 0.576642 | 5 | 0 |
| 2023-03 | 29 | -28.650000 | 0.236000 | 0.255319 | 4 | 1 |
| 2023-04 | 28 | -14.166667 | 0.600188 | 0.649254 | 6 | 2 |
| 2023-05 | 22 | -1.316667 | 0.948568 | 0.838095 | 7 | 1 |
| 2023-06 | 32 | -29.833333 | 0.292490 | 0.246753 | 4 | 0 |
| 2023-07 | 27 | -41.966667 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 15 | -11.083333 | 0.443980 | 0.532468 | 109 | 0 |
| 2023-09 | 28 | -9.050000 | 0.735638 | 0.740157 | 43 | 0 |
| 2023-10 | 20 | -21.183333 | 0.239378 | 0.186916 | 0 | 0 |
| 2023-11 | 23 | -23.416667 | 0.233079 | 0.196429 | 1 | 0 |
| 2023-12 | 24 | -12.116667 | 0.599228 | 0.636364 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK3_TOL1_MAXBARS36_SB1_TP5

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 293; dates/months 177/12; PF R/price 0.416403/0.428276; Net -224.033333 R; expectancy -0.764619 R; positive months 0/12; conditional DD 229.350000 R.
Accepted 297 = CLOSED 293 + EXCLUDED 4; SKIP 0; exclusion share 0.013468; conditional FLAT closures 247; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 15 | -2.800000 | 0.850267 | 1.043478 | 7 | 0 |
| 2023-02 | 30 | -23.100000 | 0.393170 | 0.415493 | 5 | 0 |
| 2023-03 | 29 | -28.150000 | 0.249333 | 0.269504 | 4 | 1 |
| 2023-04 | 28 | -15.650000 | 0.558325 | 0.589552 | 6 | 2 |
| 2023-05 | 22 | -1.483333 | 0.942057 | 0.847619 | 7 | 1 |
| 2023-06 | 32 | -28.166667 | 0.332016 | 0.279221 | 4 | 0 |
| 2023-07 | 27 | -41.966667 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 15 | -9.683333 | 0.514214 | 0.623377 | 109 | 0 |
| 2023-09 | 28 | -18.316667 | 0.489786 | 0.560606 | 43 | 0 |
| 2023-10 | 20 | -19.516667 | 0.299222 | 0.233645 | 0 | 0 |
| 2023-11 | 23 | -21.750000 | 0.287664 | 0.241071 | 1 | 0 |
| 2023-12 | 24 | -13.450000 | 0.555127 | 0.553719 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK3_TOL1_MAXBARS36_SB1_TP6

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 293; dates/months 177/12; PF R/price 0.447662/0.459310; Net -212.033333 R; expectancy -0.723663 R; positive months 1/12; conditional DD 218.850000 R.
Accepted 297 = CLOSED 293 + EXCLUDED 4; SKIP 0; exclusion share 0.013468; conditional FLAT closures 247; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 15 | -1.100000 | 0.941176 | 1.144928 | 7 | 0 |
| 2023-02 | 30 | -23.100000 | 0.393170 | 0.415493 | 5 | 0 |
| 2023-03 | 29 | -28.150000 | 0.249333 | 0.269504 | 4 | 1 |
| 2023-04 | 28 | -13.983333 | 0.605362 | 0.626866 | 6 | 2 |
| 2023-05 | 22 | 1.683333 | 1.065755 | 0.952381 | 7 | 1 |
| 2023-06 | 32 | -30.500000 | 0.276680 | 0.233766 | 4 | 0 |
| 2023-07 | 27 | -41.966667 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 15 | -8.283333 | 0.584448 | 0.714286 | 109 | 0 |
| 2023-09 | 28 | -16.916667 | 0.528784 | 0.613636 | 43 | 0 |
| 2023-10 | 20 | -17.850000 | 0.359066 | 0.280374 | 0 | 0 |
| 2023-11 | 23 | -20.083333 | 0.342249 | 0.285714 | 1 | 0 |
| 2023-12 | 24 | -11.783333 | 0.610254 | 0.595041 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK3_TOL1_MAXBARS36_SB1_TP7

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 293; dates/months 177/12; PF R/price 0.433969/0.454296; Net -218.233333 R; expectancy -0.744824 R; positive months 1/12; conditional DD 226.550000 R.
Accepted 297 = CLOSED 293 + EXCLUDED 4; SKIP 0; exclusion share 0.013468; conditional FLAT closures 247; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 15 | 0.400000 | 1.021390 | 1.231884 | 7 | 0 |
| 2023-02 | 30 | -23.100000 | 0.393170 | 0.415493 | 5 | 0 |
| 2023-03 | 29 | -28.150000 | 0.249333 | 0.269504 | 4 | 1 |
| 2023-04 | 28 | -12.316667 | 0.652399 | 0.664179 | 6 | 2 |
| 2023-05 | 22 | -2.150000 | 0.916016 | 0.857143 | 7 | 1 |
| 2023-06 | 32 | -30.500000 | 0.276680 | 0.233766 | 4 | 0 |
| 2023-07 | 27 | -41.966667 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 15 | -6.883333 | 0.654682 | 0.805195 | 109 | 0 |
| 2023-09 | 28 | -15.516667 | 0.567781 | 0.666667 | 43 | 0 |
| 2023-10 | 20 | -16.183333 | 0.418911 | 0.327103 | 0 | 0 |
| 2023-11 | 23 | -18.416667 | 0.396834 | 0.330357 | 1 | 0 |
| 2023-12 | 24 | -23.450000 | 0.264890 | 0.333333 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK3_TOL1_MAXBARS36_SB1_TP8

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 293; dates/months 177/12; PF R/price 0.422751/0.435021; Net -223.366667 R; expectancy -0.762344 R; positive months 1/12; conditional DD 233.183333 R.
Accepted 297 = CLOSED 293 + EXCLUDED 4; SKIP 0; exclusion share 0.013468; conditional FLAT closures 247; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 15 | 1.900000 | 1.101604 | 1.318841 | 7 | 0 |
| 2023-02 | 30 | -23.100000 | 0.393170 | 0.415493 | 5 | 0 |
| 2023-03 | 29 | -28.150000 | 0.249333 | 0.269504 | 4 | 1 |
| 2023-04 | 28 | -10.650000 | 0.699436 | 0.701493 | 6 | 2 |
| 2023-05 | 22 | -0.650000 | 0.974609 | 0.914286 | 7 | 1 |
| 2023-06 | 32 | -30.500000 | 0.276680 | 0.233766 | 4 | 0 |
| 2023-07 | 27 | -41.966667 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 15 | -18.083333 | 0.152344 | 0.154762 | 109 | 0 |
| 2023-09 | 28 | -14.116667 | 0.606778 | 0.719697 | 43 | 0 |
| 2023-10 | 20 | -14.516667 | 0.478755 | 0.373832 | 0 | 0 |
| 2023-11 | 23 | -20.083333 | 0.342249 | 0.285714 | 1 | 0 |
| 2023-12 | 24 | -23.450000 | 0.264890 | 0.333333 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK3_TOL1_MAXBARS36_SB1_TP9

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 293; dates/months 177/12; PF R/price 0.413146/0.419289; Net -227.083333 R; expectancy -0.775028 R; positive months 1/12; conditional DD 238.400000 R.
Accepted 297 = CLOSED 293 + EXCLUDED 4; SKIP 0; exclusion share 0.013468; conditional FLAT closures 247; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 15 | 3.400000 | 1.181818 | 1.405797 | 7 | 0 |
| 2023-02 | 30 | -23.100000 | 0.393170 | 0.415493 | 5 | 0 |
| 2023-03 | 29 | -28.150000 | 0.249333 | 0.269504 | 4 | 1 |
| 2023-04 | 28 | -8.983333 | 0.746472 | 0.738806 | 6 | 2 |
| 2023-05 | 22 | -4.400000 | 0.828125 | 0.771429 | 7 | 1 |
| 2023-06 | 32 | -30.500000 | 0.276680 | 0.233766 | 4 | 0 |
| 2023-07 | 27 | -41.966667 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 15 | -18.083333 | 0.152344 | 0.154762 | 109 | 0 |
| 2023-09 | 28 | -18.916667 | 0.473073 | 0.537879 | 43 | 0 |
| 2023-10 | 20 | -12.850000 | 0.538600 | 0.420561 | 0 | 0 |
| 2023-11 | 23 | -20.083333 | 0.342249 | 0.285714 | 1 | 0 |
| 2023-12 | 24 | -23.450000 | 0.264890 | 0.333333 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK3_TOL1_MAXBARS36_SB1_TP10

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 293; dates/months 177/12; PF R/price 0.401516/0.411081; Net -231.583333 R; expectancy -0.790387 R; positive months 1/12; conditional DD 244.400000 R.
Accepted 297 = CLOSED 293 + EXCLUDED 4; SKIP 0; exclusion share 0.013468; conditional FLAT closures 247; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 15 | 4.900000 | 1.262032 | 1.492754 | 7 | 0 |
| 2023-02 | 30 | -23.100000 | 0.393170 | 0.415493 | 5 | 0 |
| 2023-03 | 29 | -28.150000 | 0.249333 | 0.269504 | 4 | 1 |
| 2023-04 | 28 | -7.316667 | 0.793509 | 0.776119 | 6 | 2 |
| 2023-05 | 22 | -4.400000 | 0.828125 | 0.771429 | 7 | 1 |
| 2023-06 | 32 | -30.500000 | 0.276680 | 0.233766 | 4 | 0 |
| 2023-07 | 27 | -41.966667 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 15 | -18.083333 | 0.152344 | 0.154762 | 109 | 0 |
| 2023-09 | 28 | -18.916667 | 0.473073 | 0.537879 | 43 | 0 |
| 2023-10 | 20 | -20.516667 | 0.263315 | 0.205607 | 0 | 0 |
| 2023-11 | 23 | -20.083333 | 0.342249 | 0.285714 | 1 | 0 |
| 2023-12 | 24 | -23.450000 | 0.264890 | 0.333333 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK3_TOL1_MAXBARS36_SB2_TP2

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 403; dates/months 205/12; PF R/price 0.483402/0.504874; Net -235.500000 R; expectancy -0.584367 R; positive months 0/12; conditional DD 235.500000 R.
Accepted 407 = CLOSED 403 + EXCLUDED 4; SKIP 0; exclusion share 0.009828; conditional FLAT closures 295; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 21 | -16.566667 | 0.355383 | 0.476190 | 7 | 0 |
| 2023-02 | 40 | -14.500000 | 0.656940 | 0.648352 | 5 | 0 |
| 2023-03 | 48 | -28.933333 | 0.454088 | 0.486364 | 4 | 1 |
| 2023-04 | 34 | -9.466667 | 0.719368 | 0.852349 | 6 | 2 |
| 2023-05 | 29 | -13.333333 | 0.569892 | 0.620438 | 7 | 1 |
| 2023-06 | 42 | -22.683333 | 0.521112 | 0.460784 | 4 | 0 |
| 2023-07 | 30 | -31.550000 | 0.178029 | 0.142045 | 1 | 0 |
| 2023-08 | 22 | -8.883333 | 0.626227 | 0.575472 | 109 | 0 |
| 2023-09 | 39 | -21.033333 | 0.535346 | 0.586022 | 43 | 0 |
| 2023-10 | 35 | -20.433333 | 0.504446 | 0.542169 | 0 | 0 |
| 2023-11 | 28 | -20.216667 | 0.362585 | 0.340580 | 1 | 0 |
| 2023-12 | 35 | -27.900000 | 0.342498 | 0.394444 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK3_TOL1_MAXBARS36_SB2_TP3

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 389; dates/months 204/12; PF R/price 0.462950/0.483461; Net -247.266667 R; expectancy -0.635647 R; positive months 0/12; conditional DD 247.266667 R.
Accepted 395 = CLOSED 389 + EXCLUDED 6; SKIP 0; exclusion share 0.015190; conditional FLAT closures 347; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 21 | -15.333333 | 0.403372 | 0.533333 | 7 | 0 |
| 2023-02 | 38 | -12.000000 | 0.705642 | 0.698864 | 5 | 1 |
| 2023-03 | 44 | -39.000000 | 0.268750 | 0.281106 | 4 | 2 |
| 2023-04 | 33 | -7.016667 | 0.782990 | 0.908451 | 6 | 2 |
| 2023-05 | 29 | -10.300000 | 0.676101 | 0.723404 | 7 | 1 |
| 2023-06 | 38 | -19.633333 | 0.560612 | 0.459596 | 4 | 0 |
| 2023-07 | 30 | -41.050000 | 0.012034 | 0.016043 | 1 | 0 |
| 2023-08 | 20 | -4.250000 | 0.806231 | 0.737374 | 109 | 0 |
| 2023-09 | 39 | -19.533333 | 0.582324 | 0.635417 | 43 | 0 |
| 2023-10 | 34 | -32.033333 | 0.299563 | 0.291892 | 0 | 0 |
| 2023-11 | 28 | -18.216667 | 0.425644 | 0.391304 | 1 | 0 |
| 2023-12 | 35 | -28.900000 | 0.344671 | 0.443243 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK3_TOL1_MAXBARS36_SB2_TP4

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 388; dates/months 204/12; PF R/price 0.461265/0.480081; Net -250.466667 R; expectancy -0.645533 R; positive months 0/12; conditional DD 251.566667 R.
Accepted 394 = CLOSED 388 + EXCLUDED 6; SKIP 0; exclusion share 0.015228; conditional FLAT closures 346; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 21 | -12.600000 | 0.509728 | 0.676190 | 7 | 0 |
| 2023-02 | 38 | -24.533333 | 0.439452 | 0.430851 | 5 | 1 |
| 2023-03 | 44 | -36.500000 | 0.315625 | 0.331797 | 4 | 2 |
| 2023-04 | 33 | -7.583333 | 0.765464 | 0.880282 | 6 | 2 |
| 2023-05 | 29 | -8.000000 | 0.748428 | 0.808511 | 7 | 1 |
| 2023-06 | 38 | -21.050000 | 0.528907 | 0.414141 | 4 | 0 |
| 2023-07 | 30 | -41.050000 | 0.012034 | 0.016043 | 1 | 0 |
| 2023-08 | 20 | -1.250000 | 0.943009 | 0.868687 | 109 | 0 |
| 2023-09 | 39 | -29.383333 | 0.408389 | 0.443902 | 43 | 0 |
| 2023-10 | 33 | -26.066667 | 0.412030 | 0.404494 | 0 | 0 |
| 2023-11 | 28 | -15.216667 | 0.520231 | 0.478261 | 1 | 0 |
| 2023-12 | 35 | -27.233333 | 0.382464 | 0.481081 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK3_TOL1_MAXBARS36_SB2_TP5

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 387; dates/months 204/12; PF R/price 0.475362/0.490699; Net -244.700000 R; expectancy -0.632300 R; positive months 0/12; conditional DD 247.200000 R.
Accepted 393 = CLOSED 387 + EXCLUDED 6; SKIP 0; exclusion share 0.015267; conditional FLAT closures 345; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 21 | -9.866667 | 0.616083 | 0.819048 | 7 | 0 |
| 2023-02 | 38 | -22.866667 | 0.477532 | 0.457447 | 5 | 1 |
| 2023-03 | 44 | -35.000000 | 0.343750 | 0.359447 | 4 | 2 |
| 2023-04 | 33 | -6.083333 | 0.811856 | 0.922535 | 6 | 2 |
| 2023-05 | 28 | -11.200000 | 0.647799 | 0.659574 | 7 | 1 |
| 2023-06 | 38 | -19.216667 | 0.569937 | 0.434343 | 4 | 0 |
| 2023-07 | 30 | -41.050000 | 0.012034 | 0.016043 | 1 | 0 |
| 2023-08 | 20 | -3.250000 | 0.851824 | 0.848485 | 109 | 0 |
| 2023-09 | 39 | -26.383333 | 0.468792 | 0.507317 | 43 | 0 |
| 2023-10 | 33 | -21.500000 | 0.515038 | 0.505618 | 0 | 0 |
| 2023-11 | 28 | -21.216667 | 0.361264 | 0.333333 | 1 | 0 |
| 2023-12 | 35 | -27.066667 | 0.386243 | 0.470270 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK3_TOL1_MAXBARS36_SB2_TP6

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 386; dates/months 204/12; PF R/price 0.454155/0.477889; Net -254.500000 R; expectancy -0.659326 R; positive months 0/12; conditional DD 258.400000 R.
Accepted 392 = CLOSED 386 + EXCLUDED 6; SKIP 0; exclusion share 0.015306; conditional FLAT closures 344; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 21 | -9.133333 | 0.644617 | 0.847619 | 7 | 0 |
| 2023-02 | 38 | -21.200000 | 0.515613 | 0.484043 | 5 | 1 |
| 2023-03 | 44 | -33.500000 | 0.371875 | 0.387097 | 4 | 2 |
| 2023-04 | 33 | -4.583333 | 0.858247 | 0.964789 | 6 | 2 |
| 2023-05 | 28 | -13.800000 | 0.566038 | 0.595745 | 7 | 1 |
| 2023-06 | 38 | -25.883333 | 0.420739 | 0.333333 | 4 | 0 |
| 2023-07 | 30 | -41.050000 | 0.012034 | 0.016043 | 1 | 0 |
| 2023-08 | 20 | -1.916667 | 0.912614 | 0.929293 | 109 | 0 |
| 2023-09 | 39 | -24.716667 | 0.502349 | 0.551220 | 43 | 0 |
| 2023-10 | 32 | -22.933333 | 0.462500 | 0.468208 | 0 | 0 |
| 2023-11 | 28 | -19.716667 | 0.406422 | 0.375000 | 1 | 0 |
| 2023-12 | 35 | -36.066667 | 0.209064 | 0.298429 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK3_TOL1_MAXBARS36_SB2_TP7

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 386; dates/months 204/12; PF R/price 0.458136/0.473974; Net -253.366667 R; expectancy -0.656390 R; positive months 0/12; conditional DD 258.666667 R.
Accepted 392 = CLOSED 386 + EXCLUDED 6; SKIP 0; exclusion share 0.015306; conditional FLAT closures 344; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 21 | -7.733333 | 0.699092 | 0.914286 | 7 | 0 |
| 2023-02 | 38 | -19.533333 | 0.553694 | 0.510638 | 5 | 1 |
| 2023-03 | 44 | -32.000000 | 0.400000 | 0.414747 | 4 | 2 |
| 2023-04 | 33 | -3.083333 | 0.904639 | 1.007042 | 6 | 2 |
| 2023-05 | 28 | -12.400000 | 0.610063 | 0.645390 | 7 | 1 |
| 2023-06 | 38 | -24.216667 | 0.458038 | 0.358586 | 4 | 0 |
| 2023-07 | 30 | -41.050000 | 0.012034 | 0.016043 | 1 | 0 |
| 2023-08 | 20 | -11.250000 | 0.516476 | 0.411215 | 109 | 0 |
| 2023-09 | 39 | -23.383333 | 0.529195 | 0.590244 | 43 | 0 |
| 2023-10 | 32 | -21.433333 | 0.497656 | 0.502890 | 0 | 0 |
| 2023-11 | 28 | -21.216667 | 0.361264 | 0.333333 | 1 | 0 |
| 2023-12 | 35 | -36.066667 | 0.209064 | 0.298429 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK3_TOL1_MAXBARS36_SB2_TP8

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 386; dates/months 204/12; PF R/price 0.448583/0.458458; Net -257.833333 R; expectancy -0.667962 R; positive months 0/12; conditional DD 264.533333 R.
Accepted 392 = CLOSED 386 + EXCLUDED 6; SKIP 0; exclusion share 0.015306; conditional FLAT closures 344; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 21 | -6.333333 | 0.753567 | 0.980952 | 7 | 0 |
| 2023-02 | 38 | -17.866667 | 0.591775 | 0.537234 | 5 | 1 |
| 2023-03 | 44 | -30.500000 | 0.428125 | 0.442396 | 4 | 2 |
| 2023-04 | 33 | -1.583333 | 0.951031 | 1.049296 | 6 | 2 |
| 2023-05 | 28 | -15.600000 | 0.509434 | 0.531915 | 7 | 1 |
| 2023-06 | 38 | -22.550000 | 0.495338 | 0.383838 | 4 | 0 |
| 2023-07 | 30 | -41.050000 | 0.012034 | 0.016043 | 1 | 0 |
| 2023-08 | 20 | -11.250000 | 0.516476 | 0.411215 | 109 | 0 |
| 2023-09 | 39 | -27.383333 | 0.448658 | 0.473171 | 43 | 0 |
| 2023-10 | 32 | -26.433333 | 0.380469 | 0.387283 | 0 | 0 |
| 2023-11 | 28 | -21.216667 | 0.361264 | 0.333333 | 1 | 0 |
| 2023-12 | 35 | -36.066667 | 0.209064 | 0.298429 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK3_TOL1_MAXBARS36_SB2_TP9

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 386; dates/months 204/12; PF R/price 0.453716/0.464965; Net -255.433333 R; expectancy -0.661744 R; positive months 0/12; conditional DD 263.533333 R.
Accepted 392 = CLOSED 386 + EXCLUDED 6; SKIP 0; exclusion share 0.015306; conditional FLAT closures 344; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 21 | -4.933333 | 0.808042 | 1.047619 | 7 | 0 |
| 2023-02 | 38 | -16.200000 | 0.629855 | 0.563830 | 5 | 1 |
| 2023-03 | 44 | -29.000000 | 0.456250 | 0.470046 | 4 | 2 |
| 2023-04 | 33 | -0.083333 | 0.997423 | 1.091549 | 6 | 2 |
| 2023-05 | 28 | -15.600000 | 0.509434 | 0.531915 | 7 | 1 |
| 2023-06 | 38 | -26.216667 | 0.413279 | 0.328283 | 4 | 0 |
| 2023-07 | 30 | -41.050000 | 0.012034 | 0.016043 | 1 | 0 |
| 2023-08 | 20 | -11.250000 | 0.516476 | 0.411215 | 109 | 0 |
| 2023-09 | 39 | -27.383333 | 0.448658 | 0.473171 | 43 | 0 |
| 2023-10 | 32 | -26.433333 | 0.380469 | 0.387283 | 0 | 0 |
| 2023-11 | 28 | -21.216667 | 0.361264 | 0.333333 | 1 | 0 |
| 2023-12 | 35 | -36.066667 | 0.209064 | 0.298429 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK3_TOL1_MAXBARS36_SB2_TP10

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 385; dates/months 204/12; PF R/price 0.448507/0.459609; Net -256.950000 R; expectancy -0.667403 R; positive months 0/12; conditional DD 266.450000 R.
Accepted 391 = CLOSED 385 + EXCLUDED 6; SKIP 0; exclusion share 0.015345; conditional FLAT closures 343; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 21 | -3.533333 | 0.862516 | 1.114286 | 7 | 0 |
| 2023-02 | 38 | -14.533333 | 0.667936 | 0.590426 | 5 | 1 |
| 2023-03 | 44 | -27.500000 | 0.484375 | 0.497696 | 4 | 2 |
| 2023-04 | 32 | -6.166667 | 0.798913 | 0.905109 | 6 | 2 |
| 2023-05 | 28 | -15.600000 | 0.509434 | 0.531915 | 7 | 1 |
| 2023-06 | 38 | -26.216667 | 0.413279 | 0.328283 | 4 | 0 |
| 2023-07 | 30 | -41.050000 | 0.012034 | 0.016043 | 1 | 0 |
| 2023-08 | 20 | -11.250000 | 0.516476 | 0.411215 | 109 | 0 |
| 2023-09 | 39 | -27.383333 | 0.448658 | 0.473171 | 43 | 0 |
| 2023-10 | 32 | -26.433333 | 0.380469 | 0.387283 | 0 | 0 |
| 2023-11 | 28 | -21.216667 | 0.361264 | 0.333333 | 1 | 0 |
| 2023-12 | 35 | -36.066667 | 0.209064 | 0.298429 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK3_TOL2_MAXBARS24_SB1_TP2

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 452; dates/months 209/12; PF R/price 0.482166/0.499273; Net -272.700000 R; expectancy -0.603319 R; positive months 1/12; conditional DD 280.300000 R.
Accepted 458 = CLOSED 452 + EXCLUDED 6; SKIP 1; exclusion share 0.013100; conditional FLAT closures 432; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 29 | -1.300000 | 0.953846 | 1.018182 | 7 | 1 |
| 2023-02 | 41 | -31.316667 | 0.349151 | 0.362162 | 5 | 1 |
| 2023-03 | 41 | -22.916667 | 0.488467 | 0.516129 | 4 | 1 |
| 2023-04 | 43 | -32.133333 | 0.393329 | 0.458537 | 6 | 2 |
| 2023-05 | 40 | -35.600000 | 0.301276 | 0.331683 | 7 | 1 |
| 2023-06 | 51 | -19.000000 | 0.652439 | 0.611111 | 4 | 0 |
| 2023-07 | 39 | -34.133333 | 0.304348 | 0.314721 | 1 | 0 |
| 2023-08 | 26 | -15.200000 | 0.531828 | 0.507692 | 109 | 0 |
| 2023-09 | 33 | 1.300000 | 1.039275 | 1.161017 | 43 | 0 |
| 2023-10 | 31 | -21.550000 | 0.414667 | 0.416667 | 0 | 0 |
| 2023-11 | 41 | -32.516667 | 0.343981 | 0.314433 | 1 | 0 |
| 2023-12 | 37 | -28.333333 | 0.383164 | 0.431818 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK3_TOL2_MAXBARS24_SB1_TP3

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 441; dates/months 209/12; PF R/price 0.516117/0.532661; Net -256.950000 R; expectancy -0.582653 R; positive months 2/12; conditional DD 273.300000 R.
Accepted 448 = CLOSED 441 + EXCLUDED 7; SKIP 1; exclusion share 0.015625; conditional FLAT closures 421; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 28 | 6.066667 | 1.226650 | 1.339806 | 7 | 1 |
| 2023-02 | 41 | -27.833333 | 0.421545 | 0.448649 | 5 | 1 |
| 2023-03 | 39 | -20.616667 | 0.523865 | 0.538889 | 4 | 1 |
| 2023-04 | 42 | -31.466667 | 0.404792 | 0.446602 | 6 | 2 |
| 2023-05 | 39 | -28.150000 | 0.431887 | 0.482051 | 7 | 1 |
| 2023-06 | 49 | -14.700000 | 0.730275 | 0.658986 | 4 | 0 |
| 2023-07 | 39 | -44.933333 | 0.162213 | 0.181395 | 1 | 0 |
| 2023-08 | 25 | -14.833333 | 0.539337 | 0.492424 | 109 | 0 |
| 2023-09 | 32 | 1.500000 | 1.041551 | 1.146154 | 43 | 0 |
| 2023-10 | 31 | -16.916667 | 0.540516 | 0.520833 | 0 | 0 |
| 2023-11 | 39 | -40.033333 | 0.218608 | 0.211055 | 1 | 1 |
| 2023-12 | 37 | -25.033333 | 0.455007 | 0.522727 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK3_TOL2_MAXBARS24_SB1_TP4

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 434; dates/months 209/12; PF R/price 0.496000/0.516827; Net -267.733333 R; expectancy -0.616897 R; positive months 1/12; conditional DD 285.750000 R.
Accepted 442 = CLOSED 434 + EXCLUDED 8; SKIP 1; exclusion share 0.018100; conditional FLAT closures 414; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 28 | 3.333333 | 1.124533 | 1.203883 | 7 | 1 |
| 2023-02 | 40 | -26.016667 | 0.439900 | 0.472222 | 5 | 1 |
| 2023-03 | 37 | -28.216667 | 0.349846 | 0.374302 | 4 | 2 |
| 2023-04 | 42 | -25.500000 | 0.517654 | 0.567961 | 6 | 2 |
| 2023-05 | 38 | -22.350000 | 0.535826 | 0.601064 | 7 | 1 |
| 2023-06 | 47 | -18.933333 | 0.643440 | 0.580952 | 4 | 0 |
| 2023-07 | 39 | -42.033333 | 0.216283 | 0.241860 | 1 | 0 |
| 2023-08 | 25 | -14.683333 | 0.543996 | 0.507576 | 109 | 0 |
| 2023-09 | 31 | -11.716667 | 0.699573 | 0.755245 | 43 | 0 |
| 2023-10 | 31 | -21.016667 | 0.453876 | 0.469799 | 0 | 0 |
| 2023-11 | 39 | -41.366667 | 0.192583 | 0.160804 | 1 | 1 |
| 2023-12 | 37 | -19.233333 | 0.581277 | 0.670455 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK3_TOL2_MAXBARS24_SB1_TP5

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 434; dates/months 209/12; PF R/price 0.475744/0.495714; Net -281.150000 R; expectancy -0.647811 R; positive months 1/12; conditional DD 300.133333 R.
Accepted 442 = CLOSED 434 + EXCLUDED 8; SKIP 1; exclusion share 0.018100; conditional FLAT closures 414; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 28 | 7.900000 | 1.295143 | 1.378641 | 7 | 1 |
| 2023-02 | 40 | -24.616667 | 0.470039 | 0.511111 | 5 | 1 |
| 2023-03 | 37 | -27.716667 | 0.361367 | 0.385475 | 4 | 2 |
| 2023-04 | 42 | -28.783333 | 0.455549 | 0.485437 | 6 | 2 |
| 2023-05 | 38 | -29.950000 | 0.396777 | 0.463918 | 7 | 1 |
| 2023-06 | 47 | -12.700000 | 0.760829 | 0.690476 | 4 | 0 |
| 2023-07 | 39 | -47.533333 | 0.136281 | 0.135135 | 1 | 0 |
| 2023-08 | 25 | -13.283333 | 0.587474 | 0.560606 | 109 | 0 |
| 2023-09 | 31 | -19.583333 | 0.518443 | 0.641892 | 43 | 0 |
| 2023-10 | 31 | -17.950000 | 0.533564 | 0.550336 | 0 | 0 |
| 2023-11 | 39 | -39.700000 | 0.225114 | 0.185930 | 1 | 1 |
| 2023-12 | 37 | -27.233333 | 0.413496 | 0.477528 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK3_TOL2_MAXBARS24_SB1_TP6

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 433; dates/months 209/12; PF R/price 0.455078/0.479107; Net -293.050000 R; expectancy -0.676790 R; positive months 1/12; conditional DD 318.300000 R.
Accepted 441 = CLOSED 433 + EXCLUDED 8; SKIP 1; exclusion share 0.018141; conditional FLAT closures 413; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 28 | 11.266667 | 1.420922 | 1.495146 | 7 | 1 |
| 2023-02 | 40 | -23.216667 | 0.500179 | 0.550000 | 5 | 1 |
| 2023-03 | 37 | -27.716667 | 0.361367 | 0.385475 | 4 | 2 |
| 2023-04 | 42 | -37.116667 | 0.297919 | 0.364078 | 6 | 2 |
| 2023-05 | 38 | -28.550000 | 0.424975 | 0.500000 | 7 | 1 |
| 2023-06 | 46 | -23.866667 | 0.550534 | 0.466667 | 4 | 0 |
| 2023-07 | 39 | -56.533333 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 25 | -11.883333 | 0.630952 | 0.613636 | 109 | 0 |
| 2023-09 | 31 | -16.783333 | 0.587295 | 0.736486 | 43 | 0 |
| 2023-10 | 31 | -14.883333 | 0.613252 | 0.630872 | 0 | 0 |
| 2023-11 | 39 | -38.033333 | 0.257645 | 0.211055 | 1 | 1 |
| 2023-12 | 37 | -25.733333 | 0.445800 | 0.511236 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK3_TOL2_MAXBARS24_SB1_TP7

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 433; dates/months 209/12; PF R/price 0.461617/0.482431; Net -289.533333 R; expectancy -0.668668 R; positive months 1/12; conditional DD 312.100000 R.
Accepted 441 = CLOSED 433 + EXCLUDED 8; SKIP 1; exclusion share 0.018141; conditional FLAT closures 413; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 28 | 14.433333 | 1.539228 | 1.601942 | 7 | 1 |
| 2023-02 | 40 | -24.816667 | 0.465734 | 0.505556 | 5 | 1 |
| 2023-03 | 37 | -27.716667 | 0.361367 | 0.385475 | 4 | 2 |
| 2023-04 | 42 | -37.116667 | 0.297919 | 0.364078 | 6 | 2 |
| 2023-05 | 38 | -27.150000 | 0.453172 | 0.536082 | 7 | 1 |
| 2023-06 | 46 | -22.200000 | 0.581921 | 0.490476 | 4 | 0 |
| 2023-07 | 39 | -56.533333 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 25 | -10.483333 | 0.674431 | 0.666667 | 109 | 0 |
| 2023-09 | 31 | -13.983333 | 0.656148 | 0.831081 | 43 | 0 |
| 2023-10 | 31 | -17.616667 | 0.542226 | 0.516779 | 0 | 0 |
| 2023-11 | 39 | -36.366667 | 0.290176 | 0.236181 | 1 | 1 |
| 2023-12 | 37 | -29.983333 | 0.354271 | 0.415730 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK3_TOL2_MAXBARS24_SB1_TP8

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 433; dates/months 209/12; PF R/price 0.449723/0.463322; Net -296.700000 R; expectancy -0.685219 R; positive months 1/12; conditional DD 322.433333 R.
Accepted 441 = CLOSED 433 + EXCLUDED 8; SKIP 1; exclusion share 0.018141; conditional FLAT closures 413; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 28 | 17.600000 | 1.657534 | 1.708738 | 7 | 1 |
| 2023-02 | 40 | -24.816667 | 0.465734 | 0.505556 | 5 | 1 |
| 2023-03 | 37 | -27.716667 | 0.361367 | 0.385475 | 4 | 2 |
| 2023-04 | 42 | -37.116667 | 0.297919 | 0.364078 | 6 | 2 |
| 2023-05 | 38 | -30.750000 | 0.380665 | 0.443299 | 7 | 1 |
| 2023-06 | 46 | -20.533333 | 0.613308 | 0.514286 | 4 | 0 |
| 2023-07 | 39 | -56.533333 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 25 | -21.683333 | 0.354663 | 0.280576 | 109 | 0 |
| 2023-09 | 31 | -11.183333 | 0.725000 | 0.925676 | 43 | 0 |
| 2023-10 | 31 | -15.950000 | 0.585535 | 0.550336 | 0 | 0 |
| 2023-11 | 39 | -38.033333 | 0.257645 | 0.211055 | 1 | 1 |
| 2023-12 | 37 | -29.983333 | 0.354271 | 0.415730 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK3_TOL2_MAXBARS24_SB1_TP9

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 433; dates/months 209/12; PF R/price 0.458317/0.473261; Net -292.066667 R; expectancy -0.674519 R; positive months 1/12; conditional DD 316.300000 R.
Accepted 441 = CLOSED 433 + EXCLUDED 8; SKIP 1; exclusion share 0.018141; conditional FLAT closures 413; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 28 | 16.100000 | 1.601494 | 1.679612 | 7 | 1 |
| 2023-02 | 40 | -24.816667 | 0.465734 | 0.505556 | 5 | 1 |
| 2023-03 | 37 | -27.716667 | 0.361367 | 0.385475 | 4 | 2 |
| 2023-04 | 42 | -37.116667 | 0.297919 | 0.364078 | 6 | 2 |
| 2023-05 | 38 | -30.750000 | 0.380665 | 0.443299 | 7 | 1 |
| 2023-06 | 46 | -18.866667 | 0.644696 | 0.538095 | 4 | 0 |
| 2023-07 | 39 | -56.533333 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 25 | -21.683333 | 0.354663 | 0.280576 | 109 | 0 |
| 2023-09 | 31 | -8.383333 | 0.793852 | 1.020270 | 43 | 0 |
| 2023-10 | 31 | -14.283333 | 0.628844 | 0.583893 | 0 | 0 |
| 2023-11 | 39 | -38.033333 | 0.257645 | 0.211055 | 1 | 1 |
| 2023-12 | 37 | -29.983333 | 0.354271 | 0.415730 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK3_TOL2_MAXBARS24_SB1_TP10

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 433; dates/months 209/12; PF R/price 0.450218/0.470421; Net -296.433333 R; expectancy -0.684604 R; positive months 1/12; conditional DD 322.166667 R.
Accepted 441 = CLOSED 433 + EXCLUDED 8; SKIP 1; exclusion share 0.018141; conditional FLAT closures 413; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 28 | 17.600000 | 1.657534 | 1.737864 | 7 | 1 |
| 2023-02 | 40 | -24.816667 | 0.465734 | 0.505556 | 5 | 1 |
| 2023-03 | 37 | -27.716667 | 0.361367 | 0.385475 | 4 | 2 |
| 2023-04 | 42 | -37.116667 | 0.297919 | 0.364078 | 6 | 2 |
| 2023-05 | 38 | -30.750000 | 0.380665 | 0.443299 | 7 | 1 |
| 2023-06 | 46 | -19.866667 | 0.625863 | 0.523810 | 4 | 0 |
| 2023-07 | 39 | -56.533333 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 25 | -21.683333 | 0.354663 | 0.280576 | 109 | 0 |
| 2023-09 | 31 | -5.583333 | 0.862705 | 1.114865 | 43 | 0 |
| 2023-10 | 31 | -21.950000 | 0.429623 | 0.429530 | 0 | 0 |
| 2023-11 | 39 | -38.033333 | 0.257645 | 0.211055 | 1 | 1 |
| 2023-12 | 37 | -29.983333 | 0.354271 | 0.415730 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK3_TOL2_MAXBARS24_SB2_TP2

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 528; dates/months 228/12; PF R/price 0.542930/0.561308; Net -258.100000 R; expectancy -0.488826 R; positive months 0/12; conditional DD 262.033333 R.
Accepted 535 = CLOSED 528 + EXCLUDED 7; SKIP 1; exclusion share 0.013084; conditional FLAT closures 504; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 34 | -10.600000 | 0.685149 | 0.807947 | 7 | 1 |
| 2023-02 | 50 | -21.266667 | 0.587322 | 0.571429 | 5 | 1 |
| 2023-03 | 52 | -29.750000 | 0.460399 | 0.503937 | 4 | 1 |
| 2023-04 | 46 | -22.700000 | 0.521434 | 0.623256 | 6 | 2 |
| 2023-05 | 46 | -29.300000 | 0.442613 | 0.462810 | 7 | 1 |
| 2023-06 | 55 | -5.866667 | 0.885714 | 0.801619 | 4 | 0 |
| 2023-07 | 44 | -37.066667 | 0.280259 | 0.309917 | 1 | 0 |
| 2023-08 | 29 | -6.583333 | 0.786024 | 0.691781 | 109 | 0 |
| 2023-09 | 42 | -17.166667 | 0.632668 | 0.738220 | 43 | 0 |
| 2023-10 | 39 | -16.766667 | 0.594682 | 0.601093 | 0 | 0 |
| 2023-11 | 45 | -30.683333 | 0.392610 | 0.327731 | 1 | 1 |
| 2023-12 | 46 | -30.350000 | 0.417839 | 0.484716 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK3_TOL2_MAXBARS24_SB2_TP3

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 509; dates/months 227/12; PF R/price 0.583851/0.597021; Net -233.550000 R; expectancy -0.458841 R; positive months 0/12; conditional DD 241.316667 R.
Accepted 518 = CLOSED 509 + EXCLUDED 9; SKIP 1; exclusion share 0.017375; conditional FLAT closures 485; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 33 | -5.233333 | 0.838144 | 0.972028 | 7 | 1 |
| 2023-02 | 46 | -10.366667 | 0.780832 | 0.752381 | 5 | 2 |
| 2023-03 | 48 | -35.550000 | 0.339219 | 0.357724 | 4 | 2 |
| 2023-04 | 45 | -17.166667 | 0.627082 | 0.735577 | 6 | 2 |
| 2023-05 | 44 | -21.600000 | 0.567134 | 0.615044 | 7 | 1 |
| 2023-06 | 51 | -0.883333 | 0.982462 | 0.829960 | 4 | 0 |
| 2023-07 | 44 | -47.033333 | 0.156100 | 0.182510 | 1 | 0 |
| 2023-08 | 28 | -0.883333 | 0.969818 | 0.857143 | 109 | 0 |
| 2023-09 | 41 | -15.700000 | 0.673823 | 0.787879 | 43 | 0 |
| 2023-10 | 39 | -22.966667 | 0.499273 | 0.519802 | 0 | 0 |
| 2023-11 | 44 | -32.183333 | 0.360808 | 0.284519 | 1 | 1 |
| 2023-12 | 46 | -23.983333 | 0.539962 | 0.628821 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK3_TOL2_MAXBARS24_SB2_TP4

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 505; dates/months 227/12; PF R/price 0.579365/0.589084; Net -237.483333 R; expectancy -0.470264 R; positive months 1/12; conditional DD 245.116667 R.
Accepted 514 = CLOSED 505 + EXCLUDED 9; SKIP 1; exclusion share 0.017510; conditional FLAT closures 481; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 33 | -5.800000 | 0.820619 | 0.951049 | 7 | 1 |
| 2023-02 | 45 | -10.900000 | 0.769556 | 0.728571 | 5 | 2 |
| 2023-03 | 48 | -33.050000 | 0.385688 | 0.402439 | 4 | 2 |
| 2023-04 | 45 | -16.400000 | 0.643736 | 0.754808 | 6 | 2 |
| 2023-05 | 43 | -22.066667 | 0.558372 | 0.600000 | 7 | 1 |
| 2023-06 | 50 | -7.400000 | 0.854043 | 0.729508 | 4 | 0 |
| 2023-07 | 44 | -50.966667 | 0.106893 | 0.114391 | 1 | 0 |
| 2023-08 | 28 | 3.516667 | 1.120159 | 1.000000 | 109 | 0 |
| 2023-09 | 41 | -22.883333 | 0.551600 | 0.668246 | 43 | 0 |
| 2023-10 | 39 | -18.066667 | 0.606105 | 0.623762 | 0 | 0 |
| 2023-11 | 44 | -27.516667 | 0.453492 | 0.355649 | 1 | 1 |
| 2023-12 | 45 | -25.950000 | 0.489843 | 0.575221 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK3_TOL2_MAXBARS24_SB2_TP5

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 503; dates/months 227/12; PF R/price 0.536850/0.551351; Net -264.250000 R; expectancy -0.525348 R; positive months 1/12; conditional DD 274.683333 R.
Accepted 512 = CLOSED 503 + EXCLUDED 9; SKIP 1; exclusion share 0.017578; conditional FLAT closures 479; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 33 | -1.566667 | 0.951546 | 1.097902 | 7 | 1 |
| 2023-02 | 44 | -16.900000 | 0.645206 | 0.666667 | 5 | 2 |
| 2023-03 | 48 | -31.550000 | 0.413569 | 0.426829 | 4 | 2 |
| 2023-04 | 45 | -24.566667 | 0.466329 | 0.576923 | 6 | 2 |
| 2023-05 | 43 | -32.166667 | 0.372969 | 0.416309 | 7 | 1 |
| 2023-06 | 49 | -8.333333 | 0.835634 | 0.688525 | 4 | 0 |
| 2023-07 | 44 | -57.966667 | 0.008552 | 0.010791 | 1 | 0 |
| 2023-08 | 28 | 2.916667 | 1.099658 | 1.035714 | 109 | 0 |
| 2023-09 | 41 | -17.216667 | 0.662639 | 0.805687 | 43 | 0 |
| 2023-10 | 39 | -12.166667 | 0.734738 | 0.752475 | 0 | 0 |
| 2023-11 | 44 | -31.850000 | 0.385728 | 0.293878 | 1 | 1 |
| 2023-12 | 45 | -32.883333 | 0.370855 | 0.433476 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK3_TOL2_MAXBARS24_SB2_TP6

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 503; dates/months 227/12; PF R/price 0.530599/0.546332; Net -267.816667 R; expectancy -0.532439 R; positive months 2/12; conditional DD 276.450000 R.
Accepted 512 = CLOSED 503 + EXCLUDED 9; SKIP 1; exclusion share 0.017578; conditional FLAT closures 479; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 33 | 0.666667 | 1.020619 | 1.160839 | 7 | 1 |
| 2023-02 | 44 | -16.233333 | 0.659202 | 0.661836 | 5 | 2 |
| 2023-03 | 48 | -30.050000 | 0.441450 | 0.451220 | 4 | 2 |
| 2023-04 | 45 | -24.566667 | 0.466329 | 0.576923 | 6 | 2 |
| 2023-05 | 43 | -30.833333 | 0.398960 | 0.450644 | 7 | 1 |
| 2023-06 | 49 | -16.833333 | 0.667982 | 0.549180 | 4 | 0 |
| 2023-07 | 44 | -57.966667 | 0.008552 | 0.010791 | 1 | 0 |
| 2023-08 | 28 | 4.250000 | 1.145216 | 1.092857 | 109 | 0 |
| 2023-09 | 41 | -12.883333 | 0.747551 | 0.924171 | 43 | 0 |
| 2023-10 | 39 | -18.600000 | 0.594477 | 0.608911 | 0 | 0 |
| 2023-11 | 44 | -28.683333 | 0.446802 | 0.338776 | 1 | 1 |
| 2023-12 | 45 | -36.083333 | 0.309630 | 0.364807 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK3_TOL2_MAXBARS24_SB2_TP7

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 503; dates/months 227/12; PF R/price 0.529479/0.539646; Net -269.083333 R; expectancy -0.534957 R; positive months 1/12; conditional DD 279.116667 R.
Accepted 512 = CLOSED 503 + EXCLUDED 9; SKIP 1; exclusion share 0.017578; conditional FLAT closures 479; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 33 | 3.566667 | 1.110309 | 1.251748 | 7 | 1 |
| 2023-02 | 44 | -14.566667 | 0.694192 | 0.685990 | 5 | 2 |
| 2023-03 | 48 | -28.550000 | 0.469331 | 0.475610 | 4 | 2 |
| 2023-04 | 45 | -24.566667 | 0.466329 | 0.576923 | 6 | 2 |
| 2023-05 | 43 | -33.666667 | 0.343730 | 0.377682 | 7 | 1 |
| 2023-06 | 49 | -13.666667 | 0.730440 | 0.594262 | 4 | 0 |
| 2023-07 | 44 | -57.966667 | 0.008552 | 0.010791 | 1 | 0 |
| 2023-08 | 28 | -5.083333 | 0.833878 | 0.709459 | 109 | 0 |
| 2023-09 | 41 | -8.883333 | 0.825931 | 1.037915 | 43 | 0 |
| 2023-10 | 39 | -17.100000 | 0.627180 | 0.638614 | 0 | 0 |
| 2023-11 | 44 | -32.516667 | 0.372870 | 0.285714 | 1 | 1 |
| 2023-12 | 45 | -36.083333 | 0.309630 | 0.364807 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK3_TOL2_MAXBARS24_SB2_TP8

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 503; dates/months 227/12; PF R/price 0.528284/0.538491; Net -269.766667 R; expectancy -0.536315 R; positive months 1/12; conditional DD 281.200000 R.
Accepted 512 = CLOSED 503 + EXCLUDED 9; SKIP 1; exclusion share 0.017578; conditional FLAT closures 479; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 33 | 2.216667 | 1.068557 | 1.223776 | 7 | 1 |
| 2023-02 | 44 | -12.900000 | 0.729181 | 0.710145 | 5 | 2 |
| 2023-03 | 48 | -27.050000 | 0.497212 | 0.500000 | 4 | 2 |
| 2023-04 | 45 | -24.566667 | 0.466329 | 0.576923 | 6 | 2 |
| 2023-05 | 43 | -33.666667 | 0.343730 | 0.377682 | 7 | 1 |
| 2023-06 | 49 | -12.000000 | 0.763314 | 0.614754 | 4 | 0 |
| 2023-07 | 44 | -57.966667 | 0.008552 | 0.010791 | 1 | 0 |
| 2023-08 | 28 | -5.083333 | 0.833878 | 0.709459 | 109 | 0 |
| 2023-09 | 41 | -8.050000 | 0.842260 | 1.061611 | 43 | 0 |
| 2023-10 | 39 | -22.100000 | 0.518169 | 0.539604 | 0 | 0 |
| 2023-11 | 44 | -32.516667 | 0.372870 | 0.285714 | 1 | 1 |
| 2023-12 | 45 | -36.083333 | 0.309630 | 0.364807 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK3_TOL2_MAXBARS24_SB2_TP9

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 503; dates/months 227/12; PF R/price 0.534520/0.547344; Net -266.200000 R; expectancy -0.529225 R; positive months 1/12; conditional DD 279.183333 R.
Accepted 512 = CLOSED 503 + EXCLUDED 9; SKIP 1; exclusion share 0.017578; conditional FLAT closures 479; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 33 | 3.616667 | 1.111856 | 1.272727 | 7 | 1 |
| 2023-02 | 44 | -11.233333 | 0.764171 | 0.734300 | 5 | 2 |
| 2023-03 | 48 | -25.550000 | 0.525093 | 0.524390 | 4 | 2 |
| 2023-04 | 45 | -24.566667 | 0.466329 | 0.576923 | 6 | 2 |
| 2023-05 | 43 | -33.666667 | 0.343730 | 0.377682 | 7 | 1 |
| 2023-06 | 49 | -15.666667 | 0.690993 | 0.569672 | 4 | 0 |
| 2023-07 | 44 | -57.966667 | 0.008552 | 0.010791 | 1 | 0 |
| 2023-08 | 28 | -5.083333 | 0.833878 | 0.709459 | 109 | 0 |
| 2023-09 | 41 | -5.383333 | 0.894513 | 1.137441 | 43 | 0 |
| 2023-10 | 39 | -22.100000 | 0.518169 | 0.539604 | 0 | 0 |
| 2023-11 | 44 | -32.516667 | 0.372870 | 0.285714 | 1 | 1 |
| 2023-12 | 45 | -36.083333 | 0.309630 | 0.364807 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK3_TOL2_MAXBARS24_SB2_TP10

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 503; dates/months 227/12; PF R/price 0.521522/0.526559; Net -273.633333 R; expectancy -0.544003 R; positive months 1/12; conditional DD 289.683333 R.
Accepted 512 = CLOSED 503 + EXCLUDED 9; SKIP 1; exclusion share 0.017578; conditional FLAT closures 479; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 33 | 5.016667 | 1.155155 | 1.321678 | 7 | 1 |
| 2023-02 | 44 | -9.566667 | 0.799160 | 0.758454 | 5 | 2 |
| 2023-03 | 48 | -24.050000 | 0.552974 | 0.548780 | 4 | 2 |
| 2023-04 | 45 | -24.566667 | 0.466329 | 0.576923 | 6 | 2 |
| 2023-05 | 43 | -33.666667 | 0.343730 | 0.377682 | 7 | 1 |
| 2023-06 | 49 | -15.666667 | 0.690993 | 0.569672 | 4 | 0 |
| 2023-07 | 44 | -57.966667 | 0.008552 | 0.010791 | 1 | 0 |
| 2023-08 | 28 | -5.083333 | 0.833878 | 0.709459 | 109 | 0 |
| 2023-09 | 41 | -17.383333 | 0.659373 | 0.796209 | 43 | 0 |
| 2023-10 | 39 | -22.100000 | 0.518169 | 0.539604 | 0 | 0 |
| 2023-11 | 44 | -32.516667 | 0.372870 | 0.285714 | 1 | 1 |
| 2023-12 | 45 | -36.083333 | 0.309630 | 0.364807 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK3_TOL2_MAXBARS36_SB1_TP2

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 404; dates/months 203/12; PF R/price 0.471418/0.498121; Net -251.816667 R; expectancy -0.623309 R; positive months 0/12; conditional DD 253.316667 R.
Accepted 411 = CLOSED 404 + EXCLUDED 7; SKIP 1; exclusion share 0.017032; conditional FLAT closures 394; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 26 | -0.616667 | 0.976190 | 1.068627 | 7 | 2 |
| 2023-02 | 32 | -22.266667 | 0.415061 | 0.421769 | 5 | 1 |
| 2023-03 | 39 | -23.450000 | 0.452529 | 0.491228 | 4 | 1 |
| 2023-04 | 39 | -27.966667 | 0.420980 | 0.489362 | 6 | 2 |
| 2023-05 | 29 | -23.333333 | 0.346100 | 0.387324 | 7 | 1 |
| 2023-06 | 47 | -20.333333 | 0.616352 | 0.568720 | 4 | 0 |
| 2023-07 | 39 | -29.316667 | 0.383888 | 0.380952 | 1 | 0 |
| 2023-08 | 22 | -15.800000 | 0.419118 | 0.490909 | 109 | 0 |
| 2023-09 | 34 | -0.100000 | 0.997101 | 1.096000 | 43 | 0 |
| 2023-10 | 30 | -26.050000 | 0.320139 | 0.320000 | 0 | 0 |
| 2023-11 | 36 | -34.566667 | 0.234404 | 0.238636 | 1 | 0 |
| 2023-12 | 31 | -28.016667 | 0.297241 | 0.348684 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK3_TOL2_MAXBARS36_SB1_TP3

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 394; dates/months 203/12; PF R/price 0.516210/0.540498; Net -233.283333 R; expectancy -0.592090 R; positive months 2/12; conditional DD 246.100000 R.
Accepted 402 = CLOSED 394 + EXCLUDED 8; SKIP 1; exclusion share 0.019900; conditional FLAT closures 384; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 25 | 8.750000 | 1.357143 | 1.484211 | 7 | 2 |
| 2023-02 | 32 | -18.783333 | 0.506567 | 0.530612 | 5 | 1 |
| 2023-03 | 37 | -21.450000 | 0.481048 | 0.503030 | 4 | 1 |
| 2023-04 | 38 | -27.300000 | 0.433610 | 0.476190 | 6 | 2 |
| 2023-05 | 29 | -17.533333 | 0.508641 | 0.570423 | 7 | 1 |
| 2023-06 | 45 | -13.533333 | 0.743849 | 0.665094 | 4 | 0 |
| 2023-07 | 39 | -45.116667 | 0.161660 | 0.183962 | 1 | 0 |
| 2023-08 | 21 | -14.033333 | 0.478960 | 0.535714 | 109 | 0 |
| 2023-09 | 33 | 0.100000 | 1.002667 | 1.087591 | 43 | 0 |
| 2023-10 | 30 | -22.916667 | 0.401914 | 0.380000 | 0 | 0 |
| 2023-11 | 34 | -35.750000 | 0.208195 | 0.210227 | 1 | 1 |
| 2023-12 | 31 | -25.716667 | 0.354933 | 0.427632 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK3_TOL2_MAXBARS36_SB1_TP4

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 390; dates/months 203/12; PF R/price 0.490214/0.518947; Net -247.433333 R; expectancy -0.634444 R; positive months 1/12; conditional DD 261.250000 R.
Accepted 399 = CLOSED 390 + EXCLUDED 9; SKIP 1; exclusion share 0.022556; conditional FLAT closures 380; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 25 | 6.016667 | 1.245578 | 1.336842 | 7 | 2 |
| 2023-02 | 31 | -16.966667 | 0.533883 | 0.563380 | 5 | 1 |
| 2023-03 | 35 | -29.050000 | 0.298874 | 0.323171 | 4 | 2 |
| 2023-04 | 38 | -21.333333 | 0.557400 | 0.608466 | 6 | 2 |
| 2023-05 | 29 | -13.133333 | 0.631948 | 0.704225 | 7 | 1 |
| 2023-06 | 45 | -19.166667 | 0.637224 | 0.566038 | 4 | 0 |
| 2023-07 | 39 | -42.216667 | 0.215547 | 0.245283 | 1 | 0 |
| 2023-08 | 21 | -13.283333 | 0.506807 | 0.580357 | 109 | 0 |
| 2023-09 | 33 | -14.783333 | 0.648574 | 0.696774 | 43 | 0 |
| 2023-10 | 29 | -25.016667 | 0.349935 | 0.362416 | 0 | 0 |
| 2023-11 | 34 | -37.083333 | 0.178664 | 0.153409 | 1 | 1 |
| 2023-12 | 31 | -21.416667 | 0.462793 | 0.559211 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK3_TOL2_MAXBARS36_SB1_TP5

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 390; dates/months 203/12; PF R/price 0.480848/0.508863; Net -254.350000 R; expectancy -0.652179 R; positive months 1/12; conditional DD 274.016667 R.
Accepted 399 = CLOSED 390 + EXCLUDED 9; SKIP 1; exclusion share 0.022556; conditional FLAT closures 380; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 25 | 10.583333 | 1.431973 | 1.526316 | 7 | 2 |
| 2023-02 | 31 | -15.566667 | 0.572344 | 0.612676 | 5 | 1 |
| 2023-03 | 35 | -28.550000 | 0.310941 | 0.335366 | 4 | 2 |
| 2023-04 | 38 | -24.616667 | 0.489281 | 0.518519 | 6 | 2 |
| 2023-05 | 29 | -20.733333 | 0.442403 | 0.520270 | 7 | 1 |
| 2023-06 | 45 | -12.933333 | 0.755205 | 0.674528 | 4 | 0 |
| 2023-07 | 39 | -47.716667 | 0.135829 | 0.136986 | 1 | 0 |
| 2023-08 | 21 | -11.883333 | 0.558787 | 0.642857 | 109 | 0 |
| 2023-09 | 33 | -22.650000 | 0.482088 | 0.593750 | 43 | 0 |
| 2023-10 | 29 | -21.950000 | 0.429623 | 0.442953 | 0 | 0 |
| 2023-11 | 34 | -35.416667 | 0.215578 | 0.181818 | 1 | 1 |
| 2023-12 | 31 | -22.916667 | 0.425167 | 0.500000 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK3_TOL2_MAXBARS36_SB1_TP6

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 389; dates/months 203/12; PF R/price 0.458217/0.490644; Net -266.250000 R; expectancy -0.684447 R; positive months 1/12; conditional DD 292.183333 R.
Accepted 398 = CLOSED 389 + EXCLUDED 9; SKIP 1; exclusion share 0.022613; conditional FLAT closures 379; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 25 | 13.950000 | 1.569388 | 1.652632 | 7 | 2 |
| 2023-02 | 31 | -14.166667 | 0.610806 | 0.661972 | 5 | 1 |
| 2023-03 | 35 | -28.550000 | 0.310941 | 0.335366 | 4 | 2 |
| 2023-04 | 38 | -32.950000 | 0.316390 | 0.386243 | 6 | 2 |
| 2023-05 | 29 | -19.333333 | 0.480054 | 0.567568 | 7 | 1 |
| 2023-06 | 44 | -24.100000 | 0.543849 | 0.452830 | 4 | 0 |
| 2023-07 | 39 | -56.716667 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 21 | -10.483333 | 0.610767 | 0.705357 | 109 | 0 |
| 2023-09 | 33 | -19.850000 | 0.546113 | 0.681250 | 43 | 0 |
| 2023-10 | 29 | -18.883333 | 0.509311 | 0.523490 | 0 | 0 |
| 2023-11 | 34 | -33.750000 | 0.252492 | 0.210227 | 1 | 1 |
| 2023-12 | 31 | -21.416667 | 0.462793 | 0.539474 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK3_TOL2_MAXBARS36_SB1_TP7

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 389; dates/months 203/12; PF R/price 0.465373/0.494283; Net -262.733333 R; expectancy -0.675407 R; positive months 1/12; conditional DD 285.983333 R.
Accepted 398 = CLOSED 389 + EXCLUDED 9; SKIP 1; exclusion share 0.022613; conditional FLAT closures 379; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 25 | 17.116667 | 1.698639 | 1.768421 | 7 | 2 |
| 2023-02 | 31 | -15.766667 | 0.566850 | 0.605634 | 5 | 1 |
| 2023-03 | 35 | -28.550000 | 0.310941 | 0.335366 | 4 | 2 |
| 2023-04 | 38 | -32.950000 | 0.316390 | 0.386243 | 6 | 2 |
| 2023-05 | 29 | -17.933333 | 0.517705 | 0.614865 | 7 | 1 |
| 2023-06 | 44 | -22.433333 | 0.575394 | 0.476415 | 4 | 0 |
| 2023-07 | 39 | -56.716667 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 21 | -9.083333 | 0.662748 | 0.767857 | 109 | 0 |
| 2023-09 | 33 | -17.050000 | 0.610137 | 0.768750 | 43 | 0 |
| 2023-10 | 29 | -21.616667 | 0.438285 | 0.409396 | 0 | 0 |
| 2023-11 | 34 | -32.083333 | 0.289406 | 0.238636 | 1 | 1 |
| 2023-12 | 31 | -25.666667 | 0.356187 | 0.427632 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK3_TOL2_MAXBARS36_SB1_TP8

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 389; dates/months 203/12; PF R/price 0.452350/0.473330; Net -269.900000 R; expectancy -0.693830 R; positive months 1/12; conditional DD 296.316667 R.
Accepted 398 = CLOSED 389 + EXCLUDED 9; SKIP 1; exclusion share 0.022613; conditional FLAT closures 379; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 25 | 20.283333 | 1.827891 | 1.884211 | 7 | 2 |
| 2023-02 | 31 | -15.766667 | 0.566850 | 0.605634 | 5 | 1 |
| 2023-03 | 35 | -28.550000 | 0.310941 | 0.335366 | 4 | 2 |
| 2023-04 | 38 | -32.950000 | 0.316390 | 0.386243 | 6 | 2 |
| 2023-05 | 29 | -21.533333 | 0.420887 | 0.493243 | 7 | 1 |
| 2023-06 | 44 | -20.766667 | 0.606940 | 0.500000 | 4 | 0 |
| 2023-07 | 39 | -56.716667 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 21 | -20.283333 | 0.284118 | 0.310924 | 109 | 0 |
| 2023-09 | 33 | -14.250000 | 0.674162 | 0.856250 | 43 | 0 |
| 2023-10 | 29 | -19.950000 | 0.481594 | 0.442953 | 0 | 0 |
| 2023-11 | 34 | -33.750000 | 0.252492 | 0.210227 | 1 | 1 |
| 2023-12 | 31 | -25.666667 | 0.356187 | 0.427632 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK3_TOL2_MAXBARS36_SB1_TP9

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 389; dates/months 203/12; PF R/price 0.461752/0.484205; Net -265.266667 R; expectancy -0.681919 R; positive months 1/12; conditional DD 290.183333 R.
Accepted 398 = CLOSED 389 + EXCLUDED 9; SKIP 1; exclusion share 0.022613; conditional FLAT closures 379; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 25 | 18.783333 | 1.766667 | 1.852632 | 7 | 2 |
| 2023-02 | 31 | -15.766667 | 0.566850 | 0.605634 | 5 | 1 |
| 2023-03 | 35 | -28.550000 | 0.310941 | 0.335366 | 4 | 2 |
| 2023-04 | 38 | -32.950000 | 0.316390 | 0.386243 | 6 | 2 |
| 2023-05 | 29 | -21.533333 | 0.420887 | 0.493243 | 7 | 1 |
| 2023-06 | 44 | -19.100000 | 0.638486 | 0.523585 | 4 | 0 |
| 2023-07 | 39 | -56.716667 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 21 | -20.283333 | 0.284118 | 0.310924 | 109 | 0 |
| 2023-09 | 33 | -11.450000 | 0.738186 | 0.943750 | 43 | 0 |
| 2023-10 | 29 | -18.283333 | 0.524903 | 0.476510 | 0 | 0 |
| 2023-11 | 34 | -33.750000 | 0.252492 | 0.210227 | 1 | 1 |
| 2023-12 | 31 | -25.666667 | 0.356187 | 0.427632 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK3_TOL2_MAXBARS36_SB1_TP10

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 389; dates/months 203/12; PF R/price 0.452891/0.481098; Net -269.633333 R; expectancy -0.693145 R; positive months 1/12; conditional DD 296.050000 R.
Accepted 398 = CLOSED 389 + EXCLUDED 9; SKIP 1; exclusion share 0.022613; conditional FLAT closures 379; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 25 | 20.283333 | 1.827891 | 1.915789 | 7 | 2 |
| 2023-02 | 31 | -15.766667 | 0.566850 | 0.605634 | 5 | 1 |
| 2023-03 | 35 | -28.550000 | 0.310941 | 0.335366 | 4 | 2 |
| 2023-04 | 38 | -32.950000 | 0.316390 | 0.386243 | 6 | 2 |
| 2023-05 | 29 | -21.533333 | 0.420887 | 0.493243 | 7 | 1 |
| 2023-06 | 44 | -20.100000 | 0.619558 | 0.509434 | 4 | 0 |
| 2023-07 | 39 | -56.716667 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 21 | -20.283333 | 0.284118 | 0.310924 | 109 | 0 |
| 2023-09 | 33 | -8.650000 | 0.802210 | 1.031250 | 43 | 0 |
| 2023-10 | 29 | -25.950000 | 0.325682 | 0.322148 | 0 | 0 |
| 2023-11 | 34 | -33.750000 | 0.252492 | 0.210227 | 1 | 1 |
| 2023-12 | 31 | -25.666667 | 0.356187 | 0.427632 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK3_TOL2_MAXBARS36_SB2_TP2

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 475; dates/months 222/12; PF R/price 0.534179/0.560360; Net -239.983333 R; expectancy -0.505228 R; positive months 0/12; conditional DD 239.983333 R.
Accepted 483 = CLOSED 475 + EXCLUDED 8; SKIP 1; exclusion share 0.016563; conditional FLAT closures 463; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 30 | -7.200000 | 0.765217 | 0.899281 | 7 | 2 |
| 2023-02 | 39 | -9.866667 | 0.748940 | 0.725714 | 5 | 1 |
| 2023-03 | 49 | -30.916667 | 0.419224 | 0.470588 | 4 | 1 |
| 2023-04 | 45 | -23.066667 | 0.515406 | 0.621495 | 6 | 2 |
| 2023-05 | 35 | -17.766667 | 0.537728 | 0.575581 | 7 | 1 |
| 2023-06 | 51 | -11.366667 | 0.775805 | 0.719008 | 4 | 0 |
| 2023-07 | 42 | -28.550000 | 0.379123 | 0.395455 | 1 | 0 |
| 2023-08 | 26 | -9.883333 | 0.639733 | 0.578947 | 109 | 0 |
| 2023-09 | 42 | -16.583333 | 0.640664 | 0.730570 | 43 | 0 |
| 2023-10 | 39 | -22.633333 | 0.490623 | 0.492308 | 0 | 0 |
| 2023-11 | 38 | -32.750000 | 0.270872 | 0.239437 | 1 | 1 |
| 2023-12 | 39 | -29.400000 | 0.365468 | 0.430693 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK3_TOL2_MAXBARS36_SB2_TP3

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 461; dates/months 221/12; PF R/price 0.570781/0.590310; Net -222.500000 R; expectancy -0.482646 R; positive months 0/12; conditional DD 224.666667 R.
Accepted 471 = CLOSED 461 + EXCLUDED 10; SKIP 1; exclusion share 0.021231; conditional FLAT closures 449; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 29 | -1.833333 | 0.937500 | 1.083969 | 7 | 2 |
| 2023-02 | 37 | -1.800000 | 0.952507 | 0.910714 | 5 | 2 |
| 2023-03 | 45 | -36.650000 | 0.293834 | 0.313043 | 4 | 2 |
| 2023-04 | 44 | -17.533333 | 0.620491 | 0.734300 | 6 | 2 |
| 2023-05 | 35 | -12.733333 | 0.668690 | 0.732558 | 7 | 1 |
| 2023-06 | 48 | -5.650000 | 0.886394 | 0.776860 | 4 | 0 |
| 2023-07 | 42 | -43.016667 | 0.168224 | 0.194332 | 1 | 0 |
| 2023-08 | 24 | -3.916667 | 0.847005 | 0.769841 | 109 | 0 |
| 2023-09 | 42 | -16.616667 | 0.661230 | 0.757282 | 43 | 0 |
| 2023-10 | 39 | -30.233333 | 0.382153 | 0.392523 | 0 | 0 |
| 2023-11 | 37 | -28.083333 | 0.350674 | 0.278846 | 1 | 1 |
| 2023-12 | 39 | -24.433333 | 0.472662 | 0.559406 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK3_TOL2_MAXBARS36_SB2_TP4

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 458; dates/months 221/12; PF R/price 0.583400/0.596365; Net -217.166667 R; expectancy -0.474163 R; positive months 0/12; conditional DD 220.800000 R.
Accepted 468 = CLOSED 458 + EXCLUDED 10; SKIP 1; exclusion share 0.021368; conditional FLAT closures 446; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 29 | -2.400000 | 0.918182 | 1.061069 | 7 | 2 |
| 2023-02 | 36 | -2.333333 | 0.938434 | 0.880952 | 5 | 2 |
| 2023-03 | 45 | -34.150000 | 0.342004 | 0.360870 | 4 | 2 |
| 2023-04 | 44 | -16.766667 | 0.637085 | 0.753623 | 6 | 2 |
| 2023-05 | 34 | -13.200000 | 0.657143 | 0.713450 | 7 | 1 |
| 2023-06 | 48 | -6.833333 | 0.862601 | 0.727273 | 4 | 0 |
| 2023-07 | 42 | -46.950000 | 0.114986 | 0.121569 | 1 | 0 |
| 2023-08 | 24 | -0.916667 | 0.964193 | 0.873016 | 109 | 0 |
| 2023-09 | 42 | -23.800000 | 0.541867 | 0.643836 | 43 | 0 |
| 2023-10 | 38 | -22.933333 | 0.517532 | 0.531401 | 0 | 0 |
| 2023-11 | 37 | -23.416667 | 0.458574 | 0.360577 | 1 | 1 |
| 2023-12 | 39 | -23.466667 | 0.493525 | 0.594059 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK3_TOL2_MAXBARS36_SB2_TP5

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 456; dates/months 221/12; PF R/price 0.534693/0.552488; Net -245.333333 R; expectancy -0.538012 R; positive months 1/12; conditional DD 252.266667 R.
Accepted 466 = CLOSED 456 + EXCLUDED 10; SKIP 1; exclusion share 0.021459; conditional FLAT closures 444; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 29 | 1.833333 | 1.062500 | 1.221374 | 7 | 2 |
| 2023-02 | 36 | -9.666667 | 0.755687 | 0.768786 | 5 | 2 |
| 2023-03 | 45 | -32.650000 | 0.370906 | 0.386957 | 4 | 2 |
| 2023-04 | 44 | -24.933333 | 0.460317 | 0.574879 | 6 | 2 |
| 2023-05 | 33 | -21.966667 | 0.429437 | 0.491228 | 7 | 1 |
| 2023-06 | 47 | -7.766667 | 0.843834 | 0.685950 | 4 | 0 |
| 2023-07 | 42 | -53.950000 | 0.009183 | 0.011450 | 1 | 0 |
| 2023-08 | 24 | -2.916667 | 0.886068 | 0.857143 | 109 | 0 |
| 2023-09 | 42 | -18.133333 | 0.650946 | 0.776256 | 43 | 0 |
| 2023-10 | 38 | -17.033333 | 0.641655 | 0.657005 | 0 | 0 |
| 2023-11 | 37 | -27.750000 | 0.379888 | 0.289720 | 1 | 1 |
| 2023-12 | 39 | -30.400000 | 0.363128 | 0.435407 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK3_TOL2_MAXBARS36_SB2_TP6

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 455; dates/months 221/12; PF R/price 0.529602/0.548198; Net -247.233333 R; expectancy -0.543370 R; positive months 1/12; conditional DD 253.200000 R.
Accepted 465 = CLOSED 455 + EXCLUDED 10; SKIP 1; exclusion share 0.021505; conditional FLAT closures 443; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 29 | 4.066667 | 1.138636 | 1.290076 | 7 | 2 |
| 2023-02 | 36 | -9.000000 | 0.772536 | 0.763006 | 5 | 2 |
| 2023-03 | 45 | -31.150000 | 0.399807 | 0.413043 | 4 | 2 |
| 2023-04 | 44 | -24.933333 | 0.460317 | 0.574879 | 6 | 2 |
| 2023-05 | 33 | -20.633333 | 0.464069 | 0.538012 | 7 | 1 |
| 2023-06 | 47 | -16.266667 | 0.672922 | 0.545455 | 4 | 0 |
| 2023-07 | 42 | -53.950000 | 0.009183 | 0.011450 | 1 | 0 |
| 2023-08 | 24 | -1.583333 | 0.938151 | 0.920635 | 109 | 0 |
| 2023-09 | 42 | -13.800000 | 0.734360 | 0.890411 | 43 | 0 |
| 2023-10 | 37 | -21.800000 | 0.524709 | 0.529703 | 0 | 0 |
| 2023-11 | 37 | -24.583333 | 0.450652 | 0.341121 | 1 | 1 |
| 2023-12 | 39 | -33.600000 | 0.296089 | 0.358852 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK3_TOL2_MAXBARS36_SB2_TP7

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 455; dates/months 221/12; PF R/price 0.528388/0.540936; Net -248.500000 R; expectancy -0.546154 R; positive months 1/12; conditional DD 258.000000 R.
Accepted 465 = CLOSED 455 + EXCLUDED 10; SKIP 1; exclusion share 0.021505; conditional FLAT closures 443; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 29 | 6.966667 | 1.237500 | 1.389313 | 7 | 2 |
| 2023-02 | 36 | -7.333333 | 0.814659 | 0.791908 | 5 | 2 |
| 2023-03 | 45 | -29.650000 | 0.428709 | 0.439130 | 4 | 2 |
| 2023-04 | 44 | -24.933333 | 0.460317 | 0.574879 | 6 | 2 |
| 2023-05 | 33 | -23.466667 | 0.390476 | 0.438596 | 7 | 1 |
| 2023-06 | 47 | -13.100000 | 0.736595 | 0.590909 | 4 | 0 |
| 2023-07 | 42 | -53.950000 | 0.009183 | 0.011450 | 1 | 0 |
| 2023-08 | 24 | -10.916667 | 0.594678 | 0.507463 | 109 | 0 |
| 2023-09 | 42 | -9.800000 | 0.811357 | 1.000000 | 43 | 0 |
| 2023-10 | 37 | -20.300000 | 0.557413 | 0.559406 | 0 | 0 |
| 2023-11 | 37 | -28.416667 | 0.364991 | 0.280374 | 1 | 1 |
| 2023-12 | 39 | -33.600000 | 0.296089 | 0.358852 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK3_TOL2_MAXBARS36_SB2_TP8

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 455; dates/months 221/12; PF R/price 0.527092/0.539683; Net -249.183333 R; expectancy -0.547656 R; positive months 1/12; conditional DD 259.000000 R.
Accepted 465 = CLOSED 455 + EXCLUDED 10; SKIP 1; exclusion share 0.021505; conditional FLAT closures 443; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 29 | 5.616667 | 1.191477 | 1.358779 | 7 | 2 |
| 2023-02 | 36 | -5.666667 | 0.856782 | 0.820809 | 5 | 2 |
| 2023-03 | 45 | -28.150000 | 0.457611 | 0.465217 | 4 | 2 |
| 2023-04 | 44 | -24.933333 | 0.460317 | 0.574879 | 6 | 2 |
| 2023-05 | 33 | -23.466667 | 0.390476 | 0.438596 | 7 | 1 |
| 2023-06 | 47 | -11.433333 | 0.770107 | 0.611570 | 4 | 0 |
| 2023-07 | 42 | -53.950000 | 0.009183 | 0.011450 | 1 | 0 |
| 2023-08 | 24 | -10.916667 | 0.594678 | 0.507463 | 109 | 0 |
| 2023-09 | 42 | -8.966667 | 0.827398 | 1.022831 | 43 | 0 |
| 2023-10 | 37 | -25.300000 | 0.448401 | 0.460396 | 0 | 0 |
| 2023-11 | 37 | -28.416667 | 0.364991 | 0.280374 | 1 | 1 |
| 2023-12 | 39 | -33.600000 | 0.296089 | 0.358852 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK3_TOL2_MAXBARS36_SB2_TP9

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 455; dates/months 221/12; PF R/price 0.533861/0.549290; Net -245.616667 R; expectancy -0.539817 R; positive months 1/12; conditional DD 258.500000 R.
Accepted 465 = CLOSED 455 + EXCLUDED 10; SKIP 1; exclusion share 0.021505; conditional FLAT closures 443; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 29 | 7.016667 | 1.239205 | 1.412214 | 7 | 2 |
| 2023-02 | 36 | -4.000000 | 0.898905 | 0.849711 | 5 | 2 |
| 2023-03 | 45 | -26.650000 | 0.486513 | 0.491304 | 4 | 2 |
| 2023-04 | 44 | -24.933333 | 0.460317 | 0.574879 | 6 | 2 |
| 2023-05 | 33 | -23.466667 | 0.390476 | 0.438596 | 7 | 1 |
| 2023-06 | 47 | -15.100000 | 0.696381 | 0.566116 | 4 | 0 |
| 2023-07 | 42 | -53.950000 | 0.009183 | 0.011450 | 1 | 0 |
| 2023-08 | 24 | -10.916667 | 0.594678 | 0.507463 | 109 | 0 |
| 2023-09 | 42 | -6.300000 | 0.878730 | 1.095890 | 43 | 0 |
| 2023-10 | 37 | -25.300000 | 0.448401 | 0.460396 | 0 | 0 |
| 2023-11 | 37 | -28.416667 | 0.364991 | 0.280374 | 1 | 1 |
| 2023-12 | 39 | -33.600000 | 0.296089 | 0.358852 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK3_TOL2_MAXBARS36_SB2_TP10

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 455; dates/months 221/12; PF R/price 0.519753/0.526734; Net -253.050000 R; expectancy -0.556154 R; positive months 1/12; conditional DD 269.000000 R.
Accepted 465 = CLOSED 455 + EXCLUDED 10; SKIP 1; exclusion share 0.021505; conditional FLAT closures 443; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 29 | 8.416667 | 1.286932 | 1.465649 | 7 | 2 |
| 2023-02 | 36 | -2.333333 | 0.941028 | 0.878613 | 5 | 2 |
| 2023-03 | 45 | -25.150000 | 0.515414 | 0.517391 | 4 | 2 |
| 2023-04 | 44 | -24.933333 | 0.460317 | 0.574879 | 6 | 2 |
| 2023-05 | 33 | -23.466667 | 0.390476 | 0.438596 | 7 | 1 |
| 2023-06 | 47 | -15.100000 | 0.696381 | 0.566116 | 4 | 0 |
| 2023-07 | 42 | -53.950000 | 0.009183 | 0.011450 | 1 | 0 |
| 2023-08 | 24 | -10.916667 | 0.594678 | 0.507463 | 109 | 0 |
| 2023-09 | 42 | -18.300000 | 0.647738 | 0.767123 | 43 | 0 |
| 2023-10 | 37 | -25.300000 | 0.448401 | 0.460396 | 0 | 0 |
| 2023-11 | 37 | -28.416667 | 0.364991 | 0.280374 | 1 | 1 |
| 2023-12 | 39 | -33.600000 | 0.296089 | 0.358852 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK5_TOL1_MAXBARS24_SB1_TP2

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 283; dates/months 177/12; PF R/price 0.425298/0.425898; Net -200.666667 R; expectancy -0.709069 R; positive months 2/12; conditional DD 205.766667 R.
Accepted 284 = CLOSED 283 + EXCLUDED 1; SKIP 0; exclusion share 0.003521; conditional FLAT closures 157; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 13 | 3.333333 | 1.267380 | 1.217391 | 7 | 0 |
| 2023-02 | 30 | -26.400000 | 0.302817 | 0.305556 | 5 | 0 |
| 2023-03 | 30 | -24.666667 | 0.334532 | 0.347222 | 4 | 0 |
| 2023-04 | 31 | -19.283333 | 0.475521 | 0.531915 | 6 | 0 |
| 2023-05 | 24 | -11.383333 | 0.582518 | 0.572727 | 7 | 1 |
| 2023-06 | 25 | -22.200000 | 0.324544 | 0.302521 | 4 | 0 |
| 2023-07 | 27 | -40.700000 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 20 | -7.766667 | 0.689747 | 0.725275 | 109 | 0 |
| 2023-09 | 23 | 8.600000 | 1.430000 | 1.441558 | 43 | 0 |
| 2023-10 | 18 | -12.250000 | 0.435917 | 0.409639 | 0 | 0 |
| 2023-11 | 19 | -24.066667 | 0.121655 | 0.098039 | 1 | 0 |
| 2023-12 | 23 | -23.883333 | 0.204331 | 0.190476 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK5_TOL1_MAXBARS24_SB1_TP3

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 277; dates/months 176/12; PF R/price 0.474821/0.473094; Net -183.200000 R; expectancy -0.661372 R; positive months 1/12; conditional DD 186.033333 R.
Accepted 279 = CLOSED 277 + EXCLUDED 2; SKIP 0; exclusion share 0.007168; conditional FLAT closures 270; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 11 | -2.433333 | 0.804813 | 0.934783 | 7 | 1 |
| 2023-02 | 30 | -21.733333 | 0.426056 | 0.423611 | 5 | 0 |
| 2023-03 | 29 | -25.416667 | 0.314299 | 0.326389 | 4 | 0 |
| 2023-04 | 31 | -17.316667 | 0.529012 | 0.567376 | 6 | 0 |
| 2023-05 | 23 | -6.166667 | 0.761598 | 0.757282 | 7 | 1 |
| 2023-06 | 25 | -23.366667 | 0.320078 | 0.272000 | 4 | 0 |
| 2023-07 | 27 | -40.700000 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 19 | -7.400000 | 0.701211 | 0.698925 | 109 | 0 |
| 2023-09 | 22 | 15.066667 | 1.759664 | 1.692308 | 43 | 0 |
| 2023-10 | 18 | -7.516667 | 0.653876 | 0.614458 | 0 | 0 |
| 2023-11 | 19 | -25.400000 | 0.072993 | 0.058824 | 1 | 0 |
| 2023-12 | 23 | -20.816667 | 0.306496 | 0.285714 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK5_TOL1_MAXBARS24_SB1_TP4

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 276; dates/months 176/12; PF R/price 0.437870/0.441176; Net -199.650000 R; expectancy -0.723370 R; positive months 2/12; conditional DD 203.983333 R.
Accepted 278 = CLOSED 276 + EXCLUDED 2; SKIP 0; exclusion share 0.007194; conditional FLAT closures 269; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 11 | 0.466667 | 1.037433 | 1.217391 | 7 | 1 |
| 2023-02 | 30 | -21.316667 | 0.437060 | 0.423611 | 5 | 0 |
| 2023-03 | 29 | -29.916667 | 0.224287 | 0.233333 | 4 | 0 |
| 2023-04 | 31 | -12.750000 | 0.653218 | 0.695035 | 6 | 0 |
| 2023-05 | 23 | -3.000000 | 0.884021 | 0.864078 | 7 | 1 |
| 2023-06 | 25 | -29.700000 | 0.135790 | 0.120000 | 4 | 0 |
| 2023-07 | 27 | -40.700000 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 19 | -7.250000 | 0.707268 | 0.720430 | 109 | 0 |
| 2023-09 | 22 | 4.383333 | 1.190580 | 1.179775 | 43 | 0 |
| 2023-10 | 17 | -16.716667 | 0.285103 | 0.227273 | 0 | 0 |
| 2023-11 | 19 | -25.400000 | 0.072993 | 0.058824 | 1 | 0 |
| 2023-12 | 23 | -17.750000 | 0.408662 | 0.380952 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK5_TOL1_MAXBARS24_SB1_TP5

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 276; dates/months 176/12; PF R/price 0.415249/0.426277; Net -209.633333 R; expectancy -0.759541 R; positive months 2/12; conditional DD 215.466667 R.
Accepted 278 = CLOSED 276 + EXCLUDED 2; SKIP 0; exclusion share 0.007194; conditional FLAT closures 269; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 11 | 3.366667 | 1.270053 | 1.500000 | 7 | 1 |
| 2023-02 | 30 | -29.650000 | 0.250000 | 0.275168 | 5 | 0 |
| 2023-03 | 29 | -29.416667 | 0.237252 | 0.246667 | 4 | 0 |
| 2023-04 | 31 | -14.233333 | 0.612874 | 0.638298 | 6 | 0 |
| 2023-05 | 23 | 0.166667 | 1.006443 | 0.970874 | 7 | 1 |
| 2023-06 | 25 | -29.700000 | 0.135790 | 0.120000 | 4 | 0 |
| 2023-07 | 27 | -40.700000 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 19 | -5.850000 | 0.763795 | 0.795699 | 109 | 0 |
| 2023-09 | 22 | -4.883333 | 0.802027 | 0.904255 | 43 | 0 |
| 2023-10 | 17 | -15.050000 | 0.356379 | 0.284091 | 0 | 0 |
| 2023-11 | 19 | -25.400000 | 0.072993 | 0.058824 | 1 | 0 |
| 2023-12 | 23 | -18.283333 | 0.390894 | 0.333333 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK5_TOL1_MAXBARS24_SB1_TP6

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 276; dates/months 176/12; PF R/price 0.450581/0.460584; Net -196.966667 R; expectancy -0.713647 R; positive months 2/12; conditional DD 204.300000 R.
Accepted 278 = CLOSED 276 + EXCLUDED 2; SKIP 0; exclusion share 0.007194; conditional FLAT closures 269; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 11 | 5.066667 | 1.406417 | 1.652174 | 7 | 1 |
| 2023-02 | 30 | -29.650000 | 0.250000 | 0.275168 | 5 | 0 |
| 2023-03 | 29 | -29.416667 | 0.237252 | 0.246667 | 4 | 0 |
| 2023-04 | 31 | -12.566667 | 0.658205 | 0.673759 | 6 | 0 |
| 2023-05 | 23 | 3.333333 | 1.128866 | 1.077670 | 7 | 1 |
| 2023-06 | 25 | -29.700000 | 0.135790 | 0.120000 | 4 | 0 |
| 2023-07 | 27 | -40.700000 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 19 | -4.450000 | 0.820323 | 0.870968 | 109 | 0 |
| 2023-09 | 22 | -3.483333 | 0.858784 | 0.978723 | 43 | 0 |
| 2023-10 | 17 | -13.383333 | 0.427655 | 0.340909 | 0 | 0 |
| 2023-11 | 19 | -25.400000 | 0.072993 | 0.058824 | 1 | 0 |
| 2023-12 | 23 | -16.616667 | 0.446419 | 0.373016 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK5_TOL1_MAXBARS24_SB1_TP7

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 276; dates/months 176/12; PF R/price 0.431282/0.451636; Net -204.833333 R; expectancy -0.742150 R; positive months 1/12; conditional DD 213.666667 R.
Accepted 278 = CLOSED 276 + EXCLUDED 2; SKIP 0; exclusion share 0.007194; conditional FLAT closures 269; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 11 | 6.566667 | 1.526738 | 1.782609 | 7 | 1 |
| 2023-02 | 30 | -29.650000 | 0.250000 | 0.275168 | 5 | 0 |
| 2023-03 | 29 | -29.416667 | 0.237252 | 0.246667 | 4 | 0 |
| 2023-04 | 31 | -10.900000 | 0.703536 | 0.709220 | 6 | 0 |
| 2023-05 | 23 | -0.500000 | 0.980670 | 0.980583 | 7 | 1 |
| 2023-06 | 25 | -29.700000 | 0.135790 | 0.120000 | 4 | 0 |
| 2023-07 | 27 | -40.700000 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 19 | -3.050000 | 0.876851 | 0.946237 | 109 | 0 |
| 2023-09 | 22 | -2.083333 | 0.915541 | 1.053191 | 43 | 0 |
| 2023-10 | 17 | -11.716667 | 0.498931 | 0.397727 | 0 | 0 |
| 2023-11 | 19 | -25.400000 | 0.072993 | 0.058824 | 1 | 0 |
| 2023-12 | 23 | -28.283333 | 0.107312 | 0.129771 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK5_TOL1_MAXBARS24_SB1_TP8

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 276; dates/months 176/12; PF R/price 0.423896/0.434877; Net -208.300000 R; expectancy -0.754710 R; positive months 2/12; conditional DD 218.633333 R.
Accepted 278 = CLOSED 276 + EXCLUDED 2; SKIP 0; exclusion share 0.007194; conditional FLAT closures 269; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 11 | 8.066667 | 1.647059 | 1.913043 | 7 | 1 |
| 2023-02 | 30 | -29.650000 | 0.250000 | 0.275168 | 5 | 0 |
| 2023-03 | 29 | -29.416667 | 0.237252 | 0.246667 | 4 | 0 |
| 2023-04 | 31 | -9.233333 | 0.748867 | 0.744681 | 6 | 0 |
| 2023-05 | 23 | 1.000000 | 1.038660 | 1.038835 | 7 | 1 |
| 2023-06 | 25 | -29.700000 | 0.135790 | 0.120000 | 4 | 0 |
| 2023-07 | 27 | -40.700000 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 19 | -14.250000 | 0.455414 | 0.390000 | 109 | 0 |
| 2023-09 | 22 | -0.683333 | 0.972297 | 1.127660 | 43 | 0 |
| 2023-10 | 17 | -10.050000 | 0.570207 | 0.454545 | 0 | 0 |
| 2023-11 | 19 | -25.400000 | 0.072993 | 0.058824 | 1 | 0 |
| 2023-12 | 23 | -28.283333 | 0.107312 | 0.129771 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK5_TOL1_MAXBARS24_SB1_TP9

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 276; dates/months 176/12; PF R/price 0.413617/0.418234; Net -212.016667 R; expectancy -0.768176 R; positive months 1/12; conditional DD 223.850000 R.
Accepted 278 = CLOSED 276 + EXCLUDED 2; SKIP 0; exclusion share 0.007194; conditional FLAT closures 269; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 11 | 9.566667 | 1.767380 | 2.043478 | 7 | 1 |
| 2023-02 | 30 | -29.650000 | 0.250000 | 0.275168 | 5 | 0 |
| 2023-03 | 29 | -29.416667 | 0.237252 | 0.246667 | 4 | 0 |
| 2023-04 | 31 | -7.566667 | 0.794198 | 0.780142 | 6 | 0 |
| 2023-05 | 23 | -2.750000 | 0.893686 | 0.893204 | 7 | 1 |
| 2023-06 | 25 | -29.700000 | 0.135790 | 0.120000 | 4 | 0 |
| 2023-07 | 27 | -40.700000 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 19 | -14.250000 | 0.455414 | 0.390000 | 109 | 0 |
| 2023-09 | 22 | -5.483333 | 0.777703 | 0.872340 | 43 | 0 |
| 2023-10 | 17 | -8.383333 | 0.641483 | 0.511364 | 0 | 0 |
| 2023-11 | 19 | -25.400000 | 0.072993 | 0.058824 | 1 | 0 |
| 2023-12 | 23 | -28.283333 | 0.107312 | 0.129771 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK5_TOL1_MAXBARS24_SB1_TP10

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 276; dates/months 176/12; PF R/price 0.401171/0.409551; Net -216.516667 R; expectancy -0.784481 R; positive months 1/12; conditional DD 229.850000 R.
Accepted 278 = CLOSED 276 + EXCLUDED 2; SKIP 0; exclusion share 0.007194; conditional FLAT closures 269; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 11 | 11.066667 | 1.887701 | 2.173913 | 7 | 1 |
| 2023-02 | 30 | -29.650000 | 0.250000 | 0.275168 | 5 | 0 |
| 2023-03 | 29 | -29.416667 | 0.237252 | 0.246667 | 4 | 0 |
| 2023-04 | 31 | -5.900000 | 0.839529 | 0.815603 | 6 | 0 |
| 2023-05 | 23 | -2.750000 | 0.893686 | 0.893204 | 7 | 1 |
| 2023-06 | 25 | -29.700000 | 0.135790 | 0.120000 | 4 | 0 |
| 2023-07 | 27 | -40.700000 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 19 | -14.250000 | 0.455414 | 0.390000 | 109 | 0 |
| 2023-09 | 22 | -5.483333 | 0.777703 | 0.872340 | 43 | 0 |
| 2023-10 | 17 | -16.050000 | 0.313614 | 0.250000 | 0 | 0 |
| 2023-11 | 19 | -25.400000 | 0.072993 | 0.058824 | 1 | 0 |
| 2023-12 | 23 | -28.283333 | 0.107312 | 0.129771 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK5_TOL1_MAXBARS24_SB2_TP2

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 375; dates/months 203/12; PF R/price 0.478237/0.485574; Net -221.766667 R; expectancy -0.591378 R; positive months 0/12; conditional DD 221.766667 R.
Accepted 377 = CLOSED 375 + EXCLUDED 2; SKIP 0; exclusion share 0.005305; conditional FLAT closures 275; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 18 | -6.666667 | 0.651568 | 0.753247 | 7 | 0 |
| 2023-02 | 40 | -20.816667 | 0.522918 | 0.505263 | 5 | 0 |
| 2023-03 | 43 | -31.066667 | 0.371968 | 0.358491 | 4 | 1 |
| 2023-04 | 32 | -0.766667 | 0.971848 | 1.078125 | 6 | 0 |
| 2023-05 | 29 | -13.300000 | 0.564885 | 0.614286 | 7 | 1 |
| 2023-06 | 37 | -17.766667 | 0.577320 | 0.511494 | 4 | 0 |
| 2023-07 | 34 | -42.300000 | 0.083092 | 0.064677 | 1 | 0 |
| 2023-08 | 24 | -9.783333 | 0.648503 | 0.620968 | 109 | 0 |
| 2023-09 | 33 | -8.800000 | 0.747610 | 0.845070 | 43 | 0 |
| 2023-10 | 27 | -12.200000 | 0.597802 | 0.592000 | 0 | 0 |
| 2023-11 | 24 | -18.633333 | 0.345433 | 0.293651 | 1 | 0 |
| 2023-12 | 34 | -39.666667 | 0.125000 | 0.141414 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK5_TOL1_MAXBARS24_SB2_TP3

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 361; dates/months 201/12; PF R/price 0.459924/0.471770; Net -230.783333 R; expectancy -0.639289 R; positive months 1/12; conditional DD 231.816667 R.
Accepted 365 = CLOSED 361 + EXCLUDED 4; SKIP 0; exclusion share 0.010959; conditional FLAT closures 352; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 16 | -9.933333 | 0.480836 | 0.636364 | 7 | 1 |
| 2023-02 | 36 | -16.233333 | 0.602124 | 0.590909 | 5 | 1 |
| 2023-03 | 42 | -36.966667 | 0.277053 | 0.276498 | 4 | 1 |
| 2023-04 | 32 | 0.283333 | 1.010404 | 1.093750 | 6 | 0 |
| 2023-05 | 28 | -13.366667 | 0.559824 | 0.608696 | 7 | 1 |
| 2023-06 | 34 | -16.050000 | 0.607099 | 0.488506 | 4 | 0 |
| 2023-07 | 34 | -47.300000 | 0.010460 | 0.014563 | 1 | 0 |
| 2023-08 | 23 | -7.150000 | 0.728481 | 0.711864 | 109 | 0 |
| 2023-09 | 32 | -5.800000 | 0.833652 | 0.936620 | 43 | 0 |
| 2023-10 | 26 | -19.800000 | 0.408955 | 0.397059 | 0 | 0 |
| 2023-11 | 24 | -21.633333 | 0.278087 | 0.234848 | 1 | 0 |
| 2023-12 | 34 | -36.833333 | 0.187500 | 0.212121 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK5_TOL1_MAXBARS24_SB2_TP4

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 361; dates/months 201/12; PF R/price 0.430997/0.444444; Net -247.450000 R; expectancy -0.685457 R; positive months 0/12; conditional DD 249.883333 R.
Accepted 365 = CLOSED 361 + EXCLUDED 4; SKIP 0; exclusion share 0.010959; conditional FLAT closures 352; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 16 | -7.200000 | 0.623693 | 0.831169 | 7 | 1 |
| 2023-02 | 36 | -28.766667 | 0.343227 | 0.329787 | 5 | 1 |
| 2023-03 | 42 | -34.466667 | 0.325945 | 0.327189 | 4 | 1 |
| 2023-04 | 32 | -0.283333 | 0.989596 | 1.062500 | 6 | 0 |
| 2023-05 | 28 | -10.466667 | 0.655324 | 0.702899 | 7 | 1 |
| 2023-06 | 34 | -25.633333 | 0.397099 | 0.307263 | 4 | 0 |
| 2023-07 | 34 | -47.300000 | 0.010460 | 0.014563 | 1 | 0 |
| 2023-08 | 23 | -5.816667 | 0.779114 | 0.779661 | 109 | 0 |
| 2023-09 | 32 | -15.650000 | 0.585613 | 0.658065 | 43 | 0 |
| 2023-10 | 26 | -15.233333 | 0.545274 | 0.529412 | 0 | 0 |
| 2023-11 | 24 | -20.133333 | 0.328142 | 0.280303 | 1 | 0 |
| 2023-12 | 34 | -36.500000 | 0.194853 | 0.207071 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK5_TOL1_MAXBARS24_SB2_TP5

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 361; dates/months 201/12; PF R/price 0.470840/0.483493; Net -230.916667 R; expectancy -0.639658 R; positive months 1/12; conditional DD 234.750000 R.
Accepted 365 = CLOSED 361 + EXCLUDED 4; SKIP 0; exclusion share 0.010959; conditional FLAT closures 352; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 16 | -4.466667 | 0.766551 | 1.025974 | 7 | 1 |
| 2023-02 | 36 | -27.100000 | 0.381279 | 0.356383 | 5 | 1 |
| 2023-03 | 42 | -32.966667 | 0.355280 | 0.354839 | 4 | 1 |
| 2023-04 | 32 | 1.216667 | 1.044676 | 1.109375 | 6 | 0 |
| 2023-05 | 28 | -7.566667 | 0.750823 | 0.797101 | 7 | 1 |
| 2023-06 | 34 | -22.300000 | 0.475500 | 0.363128 | 4 | 0 |
| 2023-07 | 34 | -47.300000 | 0.010460 | 0.014563 | 1 | 0 |
| 2023-08 | 23 | -4.483333 | 0.829747 | 0.847458 | 109 | 0 |
| 2023-09 | 32 | -12.650000 | 0.665049 | 0.741935 | 43 | 0 |
| 2023-10 | 26 | -10.666667 | 0.681592 | 0.661765 | 0 | 0 |
| 2023-11 | 24 | -27.633333 | 0.121822 | 0.094203 | 1 | 0 |
| 2023-12 | 34 | -35.000000 | 0.227941 | 0.237374 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK5_TOL1_MAXBARS24_SB2_TP6

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 361; dates/months 201/12; PF R/price 0.443040/0.465499; Net -243.883333 R; expectancy -0.675577 R; positive months 1/12; conditional DD 249.116667 R.
Accepted 365 = CLOSED 361 + EXCLUDED 4; SKIP 0; exclusion share 0.010959; conditional FLAT closures 352; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 16 | -3.733333 | 0.804878 | 1.064935 | 7 | 1 |
| 2023-02 | 36 | -25.433333 | 0.419330 | 0.382979 | 5 | 1 |
| 2023-03 | 42 | -31.466667 | 0.384615 | 0.382488 | 4 | 1 |
| 2023-04 | 32 | 2.716667 | 1.099755 | 1.156250 | 6 | 0 |
| 2023-05 | 28 | -10.166667 | 0.665203 | 0.731884 | 7 | 1 |
| 2023-06 | 34 | -28.966667 | 0.318699 | 0.251397 | 4 | 0 |
| 2023-07 | 34 | -47.300000 | 0.010460 | 0.014563 | 1 | 0 |
| 2023-08 | 23 | -3.150000 | 0.880380 | 0.915254 | 109 | 0 |
| 2023-09 | 32 | -10.983333 | 0.709179 | 0.800000 | 43 | 0 |
| 2023-10 | 26 | -13.766667 | 0.589055 | 0.595588 | 0 | 0 |
| 2023-11 | 24 | -27.633333 | 0.121822 | 0.094203 | 1 | 0 |
| 2023-12 | 34 | -44.000000 | 0.060498 | 0.083333 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK5_TOL1_MAXBARS24_SB2_TP7

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 360; dates/months 201/12; PF R/price 0.452444/0.465819; Net -239.583333 R; expectancy -0.665509 R; positive months 1/12; conditional DD 246.216667 R.
Accepted 364 = CLOSED 360 + EXCLUDED 4; SKIP 0; exclusion share 0.010989; conditional FLAT closures 351; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 16 | -2.333333 | 0.878049 | 1.155844 | 7 | 1 |
| 2023-02 | 36 | -23.766667 | 0.457382 | 0.409574 | 5 | 1 |
| 2023-03 | 42 | -29.966667 | 0.413950 | 0.410138 | 4 | 1 |
| 2023-04 | 32 | 4.216667 | 1.154835 | 1.203125 | 6 | 0 |
| 2023-05 | 28 | -8.766667 | 0.711306 | 0.782609 | 7 | 1 |
| 2023-06 | 33 | -25.633333 | 0.372501 | 0.287356 | 4 | 0 |
| 2023-07 | 34 | -47.300000 | 0.010460 | 0.014563 | 1 | 0 |
| 2023-08 | 23 | -12.483333 | 0.548795 | 0.476190 | 109 | 0 |
| 2023-09 | 32 | -9.650000 | 0.744484 | 0.851613 | 43 | 0 |
| 2023-10 | 26 | -12.266667 | 0.633831 | 0.639706 | 0 | 0 |
| 2023-11 | 24 | -27.633333 | 0.121822 | 0.094203 | 1 | 0 |
| 2023-12 | 34 | -44.000000 | 0.060498 | 0.083333 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK5_TOL1_MAXBARS24_SB2_TP8

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 360; dates/months 201/12; PF R/price 0.442235/0.449391; Net -244.050000 R; expectancy -0.677917 R; positive months 1/12; conditional DD 252.083333 R.
Accepted 364 = CLOSED 360 + EXCLUDED 4; SKIP 0; exclusion share 0.010989; conditional FLAT closures 351; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 16 | -0.933333 | 0.951220 | 1.246753 | 7 | 1 |
| 2023-02 | 36 | -22.100000 | 0.495434 | 0.436170 | 5 | 1 |
| 2023-03 | 42 | -28.466667 | 0.443286 | 0.437788 | 4 | 1 |
| 2023-04 | 32 | 5.716667 | 1.209914 | 1.250000 | 6 | 0 |
| 2023-05 | 28 | -11.966667 | 0.605928 | 0.666667 | 7 | 1 |
| 2023-06 | 33 | -23.966667 | 0.413301 | 0.316092 | 4 | 0 |
| 2023-07 | 34 | -47.300000 | 0.010460 | 0.014563 | 1 | 0 |
| 2023-08 | 23 | -12.483333 | 0.548795 | 0.476190 | 109 | 0 |
| 2023-09 | 32 | -13.650000 | 0.638570 | 0.696774 | 43 | 0 |
| 2023-10 | 26 | -17.266667 | 0.484577 | 0.492647 | 0 | 0 |
| 2023-11 | 24 | -27.633333 | 0.121822 | 0.094203 | 1 | 0 |
| 2023-12 | 34 | -44.000000 | 0.060498 | 0.083333 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK5_TOL1_MAXBARS24_SB2_TP9

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 360; dates/months 201/12; PF R/price 0.447720/0.456280; Net -241.650000 R; expectancy -0.671250 R; positive months 2/12; conditional DD 251.083333 R.
Accepted 364 = CLOSED 360 + EXCLUDED 4; SKIP 0; exclusion share 0.010989; conditional FLAT closures 351; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 16 | 0.466667 | 1.024390 | 1.337662 | 7 | 1 |
| 2023-02 | 36 | -20.433333 | 0.533486 | 0.462766 | 5 | 1 |
| 2023-03 | 42 | -26.966667 | 0.472621 | 0.465438 | 4 | 1 |
| 2023-04 | 32 | 7.216667 | 1.264994 | 1.296875 | 6 | 0 |
| 2023-05 | 28 | -11.966667 | 0.605928 | 0.666667 | 7 | 1 |
| 2023-06 | 33 | -27.633333 | 0.323541 | 0.252874 | 4 | 0 |
| 2023-07 | 34 | -47.300000 | 0.010460 | 0.014563 | 1 | 0 |
| 2023-08 | 23 | -12.483333 | 0.548795 | 0.476190 | 109 | 0 |
| 2023-09 | 32 | -13.650000 | 0.638570 | 0.696774 | 43 | 0 |
| 2023-10 | 26 | -17.266667 | 0.484577 | 0.492647 | 0 | 0 |
| 2023-11 | 24 | -27.633333 | 0.121822 | 0.094203 | 1 | 0 |
| 2023-12 | 34 | -44.000000 | 0.060498 | 0.083333 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK5_TOL1_MAXBARS24_SB2_TP10

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 360; dates/months 201/12; PF R/price 0.440445/0.449391; Net -244.833333 R; expectancy -0.680093 R; positive months 1/12; conditional DD 255.666667 R.
Accepted 364 = CLOSED 360 + EXCLUDED 4; SKIP 0; exclusion share 0.010989; conditional FLAT closures 351; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 16 | 1.866667 | 1.097561 | 1.428571 | 7 | 1 |
| 2023-02 | 36 | -18.766667 | 0.571537 | 0.489362 | 5 | 1 |
| 2023-03 | 42 | -25.466667 | 0.501956 | 0.493088 | 4 | 1 |
| 2023-04 | 32 | -0.533333 | 0.980416 | 1.054688 | 6 | 0 |
| 2023-05 | 28 | -11.966667 | 0.605928 | 0.666667 | 7 | 1 |
| 2023-06 | 33 | -27.633333 | 0.323541 | 0.252874 | 4 | 0 |
| 2023-07 | 34 | -47.300000 | 0.010460 | 0.014563 | 1 | 0 |
| 2023-08 | 23 | -12.483333 | 0.548795 | 0.476190 | 109 | 0 |
| 2023-09 | 32 | -13.650000 | 0.638570 | 0.696774 | 43 | 0 |
| 2023-10 | 26 | -17.266667 | 0.484577 | 0.492647 | 0 | 0 |
| 2023-11 | 24 | -27.633333 | 0.121822 | 0.094203 | 1 | 0 |
| 2023-12 | 34 | -44.000000 | 0.060498 | 0.083333 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK5_TOL1_MAXBARS36_SB1_TP2

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 270; dates/months 178/12; PF R/price 0.389101/0.398601; Net -205.333333 R; expectancy -0.760494 R; positive months 1/12; conditional DD 205.700000 R.
Accepted 271 = CLOSED 270 + EXCLUDED 1; SKIP 0; exclusion share 0.003690; conditional FLAT closures 154; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 14 | -3.066667 | 0.802575 | 0.793103 | 7 | 0 |
| 2023-02 | 27 | -23.833333 | 0.318398 | 0.328244 | 5 | 0 |
| 2023-03 | 31 | -26.333333 | 0.320138 | 0.335570 | 4 | 0 |
| 2023-04 | 28 | -16.783333 | 0.502962 | 0.565891 | 6 | 0 |
| 2023-05 | 18 | -6.750000 | 0.656197 | 0.637500 | 7 | 1 |
| 2023-06 | 25 | -19.600000 | 0.373134 | 0.342105 | 4 | 0 |
| 2023-07 | 25 | -38.633333 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 19 | -16.166667 | 0.347241 | 0.430108 | 109 | 0 |
| 2023-09 | 24 | 6.933333 | 1.320000 | 1.353659 | 43 | 0 |
| 2023-10 | 18 | -12.083333 | 0.439288 | 0.404762 | 0 | 0 |
| 2023-11 | 18 | -23.883333 | 0.018493 | 0.022222 | 1 | 0 |
| 2023-12 | 23 | -25.133333 | 0.196162 | 0.183206 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK5_TOL1_MAXBARS36_SB1_TP3

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 264; dates/months 177/12; PF R/price 0.449695/0.454616; Net -184.783333 R; expectancy -0.699937 R; positive months 1/12; conditional DD 186.216667 R.
Accepted 266 = CLOSED 264 + EXCLUDED 2; SKIP 0; exclusion share 0.007519; conditional FLAT closures 257; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 12 | -6.833333 | 0.560086 | 0.672414 | 7 | 1 |
| 2023-02 | 27 | -19.166667 | 0.451859 | 0.458015 | 5 | 0 |
| 2023-03 | 30 | -27.083333 | 0.300775 | 0.315436 | 4 | 0 |
| 2023-04 | 28 | -14.816667 | 0.561204 | 0.604651 | 6 | 0 |
| 2023-05 | 17 | -1.783333 | 0.902194 | 0.890411 | 7 | 1 |
| 2023-06 | 25 | -20.766667 | 0.366226 | 0.308333 | 4 | 0 |
| 2023-07 | 25 | -38.633333 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 18 | -15.800000 | 0.355102 | 0.410526 | 109 | 0 |
| 2023-09 | 23 | 13.400000 | 1.623256 | 1.590361 | 43 | 0 |
| 2023-10 | 18 | -7.350000 | 0.658933 | 0.607143 | 0 | 0 |
| 2023-11 | 18 | -23.883333 | 0.018493 | 0.022222 | 1 | 0 |
| 2023-12 | 23 | -22.066667 | 0.294243 | 0.274809 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK5_TOL1_MAXBARS36_SB1_TP4

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 263; dates/months 177/12; PF R/price 0.411799/0.421815; Net -201.233333 R; expectancy -0.765146 R; positive months 2/12; conditional DD 204.166667 R.
Accepted 265 = CLOSED 263 + EXCLUDED 2; SKIP 0; exclusion share 0.007547; conditional FLAT closures 256; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 12 | -3.933333 | 0.746781 | 0.896552 | 7 | 1 |
| 2023-02 | 27 | -18.750000 | 0.463775 | 0.458015 | 5 | 0 |
| 2023-03 | 30 | -31.583333 | 0.214996 | 0.225806 | 4 | 0 |
| 2023-04 | 28 | -10.250000 | 0.696446 | 0.744186 | 6 | 0 |
| 2023-05 | 17 | 1.383333 | 1.075868 | 1.041096 | 7 | 1 |
| 2023-06 | 25 | -27.100000 | 0.172940 | 0.150000 | 4 | 0 |
| 2023-07 | 25 | -38.633333 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 18 | -15.650000 | 0.361224 | 0.431579 | 109 | 0 |
| 2023-09 | 23 | 2.716667 | 1.110135 | 1.117021 | 43 | 0 |
| 2023-10 | 17 | -16.550000 | 0.287150 | 0.224719 | 0 | 0 |
| 2023-11 | 18 | -23.883333 | 0.018493 | 0.022222 | 1 | 0 |
| 2023-12 | 23 | -19.000000 | 0.392324 | 0.366412 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK5_TOL1_MAXBARS36_SB1_TP5

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 263; dates/months 177/12; PF R/price 0.388575/0.406510; Net -211.216667 R; expectancy -0.803105 R; positive months 1/12; conditional DD 215.650000 R.
Accepted 265 = CLOSED 263 + EXCLUDED 2; SKIP 0; exclusion share 0.007547; conditional FLAT closures 256; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 12 | -1.033333 | 0.933476 | 1.120690 | 7 | 1 |
| 2023-02 | 27 | -27.083333 | 0.260692 | 0.294118 | 5 | 0 |
| 2023-03 | 30 | -31.083333 | 0.227423 | 0.238710 | 4 | 0 |
| 2023-04 | 28 | -11.733333 | 0.652517 | 0.682171 | 6 | 0 |
| 2023-05 | 17 | 4.550000 | 1.249543 | 1.191781 | 7 | 1 |
| 2023-06 | 25 | -27.100000 | 0.172940 | 0.150000 | 4 | 0 |
| 2023-07 | 25 | -38.633333 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 18 | -14.250000 | 0.418367 | 0.505263 | 109 | 0 |
| 2023-09 | 23 | -6.550000 | 0.751266 | 0.858586 | 43 | 0 |
| 2023-10 | 17 | -14.883333 | 0.358938 | 0.280899 | 0 | 0 |
| 2023-11 | 18 | -23.883333 | 0.018493 | 0.022222 | 1 | 0 |
| 2023-12 | 23 | -19.533333 | 0.375267 | 0.320611 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK5_TOL1_MAXBARS36_SB1_TP6

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 263; dates/months 177/12; PF R/price 0.425242/0.442089; Net -198.550000 R; expectancy -0.754943 R; positive months 2/12; conditional DD 204.483333 R.
Accepted 265 = CLOSED 263 + EXCLUDED 2; SKIP 0; exclusion share 0.007547; conditional FLAT closures 256; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 12 | 0.666667 | 1.042918 | 1.241379 | 7 | 1 |
| 2023-02 | 27 | -27.083333 | 0.260692 | 0.294118 | 5 | 0 |
| 2023-03 | 30 | -31.083333 | 0.227423 | 0.238710 | 4 | 0 |
| 2023-04 | 28 | -10.066667 | 0.701876 | 0.720930 | 6 | 0 |
| 2023-05 | 17 | 7.716667 | 1.423218 | 1.342466 | 7 | 1 |
| 2023-06 | 25 | -27.100000 | 0.172940 | 0.150000 | 4 | 0 |
| 2023-07 | 25 | -38.633333 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 18 | -12.850000 | 0.475510 | 0.578947 | 109 | 0 |
| 2023-09 | 23 | -5.150000 | 0.804430 | 0.929293 | 43 | 0 |
| 2023-10 | 17 | -13.216667 | 0.430725 | 0.337079 | 0 | 0 |
| 2023-11 | 18 | -23.883333 | 0.018493 | 0.022222 | 1 | 0 |
| 2023-12 | 23 | -17.866667 | 0.428571 | 0.358779 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK5_TOL1_MAXBARS36_SB1_TP7

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 263; dates/months 177/12; PF R/price 0.405339/0.432881; Net -206.416667 R; expectancy -0.784854 R; positive months 2/12; conditional DD 213.850000 R.
Accepted 265 = CLOSED 263 + EXCLUDED 2; SKIP 0; exclusion share 0.007547; conditional FLAT closures 256; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 12 | 2.166667 | 1.139485 | 1.344828 | 7 | 1 |
| 2023-02 | 27 | -27.083333 | 0.260692 | 0.294118 | 5 | 0 |
| 2023-03 | 30 | -31.083333 | 0.227423 | 0.238710 | 4 | 0 |
| 2023-04 | 28 | -8.400000 | 0.751234 | 0.759690 | 6 | 0 |
| 2023-05 | 17 | 3.883333 | 1.212980 | 1.205479 | 7 | 1 |
| 2023-06 | 25 | -27.100000 | 0.172940 | 0.150000 | 4 | 0 |
| 2023-07 | 25 | -38.633333 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 18 | -11.450000 | 0.532653 | 0.652632 | 109 | 0 |
| 2023-09 | 23 | -3.750000 | 0.857595 | 1.000000 | 43 | 0 |
| 2023-10 | 17 | -11.550000 | 0.502513 | 0.393258 | 0 | 0 |
| 2023-11 | 18 | -23.883333 | 0.018493 | 0.022222 | 1 | 0 |
| 2023-12 | 23 | -29.533333 | 0.103239 | 0.125000 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK5_TOL1_MAXBARS36_SB1_TP8

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 263; dates/months 177/12; PF R/price 0.397781/0.415604; Net -209.883333 R; expectancy -0.798035 R; positive months 2/12; conditional DD 218.816667 R.
Accepted 265 = CLOSED 263 + EXCLUDED 2; SKIP 0; exclusion share 0.007547; conditional FLAT closures 256; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 12 | 3.666667 | 1.236052 | 1.448276 | 7 | 1 |
| 2023-02 | 27 | -27.083333 | 0.260692 | 0.294118 | 5 | 0 |
| 2023-03 | 30 | -31.083333 | 0.227423 | 0.238710 | 4 | 0 |
| 2023-04 | 28 | -6.733333 | 0.800592 | 0.798450 | 6 | 0 |
| 2023-05 | 17 | 5.383333 | 1.295247 | 1.287671 | 7 | 1 |
| 2023-06 | 25 | -27.100000 | 0.172940 | 0.150000 | 4 | 0 |
| 2023-07 | 25 | -38.633333 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 18 | -22.650000 | 0.125483 | 0.127451 | 109 | 0 |
| 2023-09 | 23 | -2.350000 | 0.910759 | 1.070707 | 43 | 0 |
| 2023-10 | 17 | -9.883333 | 0.574300 | 0.449438 | 0 | 0 |
| 2023-11 | 18 | -23.883333 | 0.018493 | 0.022222 | 1 | 0 |
| 2023-12 | 23 | -29.533333 | 0.103239 | 0.125000 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK5_TOL1_MAXBARS36_SB1_TP9

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 263; dates/months 177/12; PF R/price 0.387117/0.398350; Net -213.600000 R; expectancy -0.812167 R; positive months 2/12; conditional DD 224.033333 R.
Accepted 265 = CLOSED 263 + EXCLUDED 2; SKIP 0; exclusion share 0.007547; conditional FLAT closures 256; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 12 | 5.166667 | 1.332618 | 1.551724 | 7 | 1 |
| 2023-02 | 27 | -27.083333 | 0.260692 | 0.294118 | 5 | 0 |
| 2023-03 | 30 | -31.083333 | 0.227423 | 0.238710 | 4 | 0 |
| 2023-04 | 28 | -5.066667 | 0.849951 | 0.837209 | 6 | 0 |
| 2023-05 | 17 | 1.633333 | 1.089580 | 1.082192 | 7 | 1 |
| 2023-06 | 25 | -27.100000 | 0.172940 | 0.150000 | 4 | 0 |
| 2023-07 | 25 | -38.633333 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 18 | -22.650000 | 0.125483 | 0.127451 | 109 | 0 |
| 2023-09 | 23 | -7.150000 | 0.728481 | 0.828283 | 43 | 0 |
| 2023-10 | 17 | -8.216667 | 0.646088 | 0.505618 | 0 | 0 |
| 2023-11 | 18 | -23.883333 | 0.018493 | 0.022222 | 1 | 0 |
| 2023-12 | 23 | -29.533333 | 0.103239 | 0.125000 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK5_TOL1_MAXBARS36_SB1_TP10

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 263; dates/months 177/12; PF R/price 0.374205/0.389347; Net -218.100000 R; expectancy -0.829278 R; positive months 2/12; conditional DD 230.033333 R.
Accepted 265 = CLOSED 263 + EXCLUDED 2; SKIP 0; exclusion share 0.007547; conditional FLAT closures 256; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 12 | 6.666667 | 1.429185 | 1.655172 | 7 | 1 |
| 2023-02 | 27 | -27.083333 | 0.260692 | 0.294118 | 5 | 0 |
| 2023-03 | 30 | -31.083333 | 0.227423 | 0.238710 | 4 | 0 |
| 2023-04 | 28 | -3.400000 | 0.899309 | 0.875969 | 6 | 0 |
| 2023-05 | 17 | 1.633333 | 1.089580 | 1.082192 | 7 | 1 |
| 2023-06 | 25 | -27.100000 | 0.172940 | 0.150000 | 4 | 0 |
| 2023-07 | 25 | -38.633333 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 18 | -22.650000 | 0.125483 | 0.127451 | 109 | 0 |
| 2023-09 | 23 | -7.150000 | 0.728481 | 0.828283 | 43 | 0 |
| 2023-10 | 17 | -15.883333 | 0.315865 | 0.247191 | 0 | 0 |
| 2023-11 | 18 | -23.883333 | 0.018493 | 0.022222 | 1 | 0 |
| 2023-12 | 23 | -29.533333 | 0.103239 | 0.125000 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK5_TOL1_MAXBARS36_SB2_TP2

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 360; dates/months 204/12; PF R/price 0.464665/0.474816; Net -218.666667 R; expectancy -0.607407 R; positive months 1/12; conditional DD 218.666667 R.
Accepted 362 = CLOSED 360 + EXCLUDED 2; SKIP 0; exclusion share 0.005525; conditional FLAT closures 262; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 18 | -7.000000 | 0.640411 | 0.707317 | 7 | 0 |
| 2023-02 | 37 | -18.333333 | 0.551752 | 0.542857 | 5 | 0 |
| 2023-03 | 44 | -32.566667 | 0.361020 | 0.348624 | 4 | 1 |
| 2023-04 | 30 | 0.233333 | 1.009032 | 1.123967 | 6 | 0 |
| 2023-05 | 23 | -8.833333 | 0.624113 | 0.695238 | 7 | 1 |
| 2023-06 | 35 | -17.216667 | 0.557412 | 0.503067 | 4 | 0 |
| 2023-07 | 31 | -38.050000 | 0.091524 | 0.070270 | 1 | 0 |
| 2023-08 | 24 | -16.450000 | 0.412500 | 0.401575 | 109 | 0 |
| 2023-09 | 34 | -10.300000 | 0.716774 | 0.810811 | 43 | 0 |
| 2023-10 | 27 | -12.100000 | 0.599779 | 0.587302 | 0 | 0 |
| 2023-11 | 24 | -18.850000 | 0.315789 | 0.279661 | 1 | 0 |
| 2023-12 | 33 | -39.200000 | 0.126300 | 0.140704 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK5_TOL1_MAXBARS36_SB2_TP3

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 347; dates/months 202/12; PF R/price 0.441166/0.456436; Net -230.100000 R; expectancy -0.663112 R; positive months 1/12; conditional DD 230.100000 R.
Accepted 351 = CLOSED 347 + EXCLUDED 4; SKIP 0; exclusion share 0.011396; conditional FLAT closures 339; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 16 | -10.266667 | 0.472603 | 0.597561 | 7 | 1 |
| 2023-02 | 35 | -14.833333 | 0.623519 | 0.615385 | 5 | 1 |
| 2023-03 | 43 | -38.466667 | 0.269158 | 0.269058 | 4 | 1 |
| 2023-04 | 30 | 1.283333 | 1.049677 | 1.140496 | 6 | 0 |
| 2023-05 | 22 | -8.900000 | 0.618026 | 0.689320 | 7 | 1 |
| 2023-06 | 32 | -17.166667 | 0.544852 | 0.447853 | 4 | 0 |
| 2023-07 | 31 | -43.050000 | 0.011481 | 0.015789 | 1 | 0 |
| 2023-08 | 22 | -13.483333 | 0.484713 | 0.483333 | 109 | 0 |
| 2023-09 | 33 | -7.300000 | 0.799267 | 0.898649 | 43 | 0 |
| 2023-10 | 26 | -19.700000 | 0.410180 | 0.394161 | 0 | 0 |
| 2023-11 | 24 | -21.850000 | 0.247849 | 0.217742 | 1 | 0 |
| 2023-12 | 33 | -36.366667 | 0.189450 | 0.211055 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK5_TOL1_MAXBARS36_SB2_TP4

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 347; dates/months 202/12; PF R/price 0.425117/0.437916; Net -240.100000 R; expectancy -0.691931 R; positive months 1/12; conditional DD 241.200000 R.
Accepted 351 = CLOSED 347 + EXCLUDED 4; SKIP 0; exclusion share 0.011396; conditional FLAT closures 339; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 16 | -7.533333 | 0.613014 | 0.780488 | 7 | 1 |
| 2023-02 | 35 | -27.366667 | 0.354560 | 0.342541 | 5 | 1 |
| 2023-03 | 43 | -35.966667 | 0.316656 | 0.318386 | 4 | 1 |
| 2023-04 | 30 | 0.716667 | 1.027742 | 1.107438 | 6 | 0 |
| 2023-05 | 22 | -6.000000 | 0.742489 | 0.815534 | 7 | 1 |
| 2023-06 | 32 | -20.083333 | 0.467521 | 0.355828 | 4 | 0 |
| 2023-07 | 31 | -43.050000 | 0.011481 | 0.015789 | 1 | 0 |
| 2023-08 | 22 | -12.150000 | 0.535669 | 0.550000 | 109 | 0 |
| 2023-09 | 33 | -17.150000 | 0.563243 | 0.633540 | 43 | 0 |
| 2023-10 | 26 | -15.133333 | 0.546906 | 0.525547 | 0 | 0 |
| 2023-11 | 24 | -20.350000 | 0.299484 | 0.266129 | 1 | 0 |
| 2023-12 | 33 | -36.033333 | 0.196880 | 0.206030 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK5_TOL1_MAXBARS36_SB2_TP5

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 347; dates/months 202/12; PF R/price 0.466619/0.478453; Net -223.566667 R; expectancy -0.644284 R; positive months 1/12; conditional DD 226.066667 R.
Accepted 351 = CLOSED 347 + EXCLUDED 4; SKIP 0; exclusion share 0.011396; conditional FLAT closures 339; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 16 | -4.800000 | 0.753425 | 0.963415 | 7 | 1 |
| 2023-02 | 35 | -25.700000 | 0.393868 | 0.370166 | 5 | 1 |
| 2023-03 | 43 | -34.466667 | 0.345155 | 0.345291 | 4 | 1 |
| 2023-04 | 30 | 2.216667 | 1.085806 | 1.157025 | 6 | 0 |
| 2023-05 | 22 | -3.100000 | 0.866953 | 0.941748 | 7 | 1 |
| 2023-06 | 32 | -16.750000 | 0.555899 | 0.417178 | 4 | 0 |
| 2023-07 | 31 | -43.050000 | 0.011481 | 0.015789 | 1 | 0 |
| 2023-08 | 22 | -10.816667 | 0.586624 | 0.616667 | 109 | 0 |
| 2023-09 | 33 | -14.150000 | 0.639643 | 0.714286 | 43 | 0 |
| 2023-10 | 26 | -10.566667 | 0.683633 | 0.656934 | 0 | 0 |
| 2023-11 | 24 | -27.850000 | 0.088380 | 0.069231 | 1 | 0 |
| 2023-12 | 33 | -34.533333 | 0.230312 | 0.236181 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK5_TOL1_MAXBARS36_SB2_TP6

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 346; dates/months 202/12; PF R/price 0.439437/0.461071; Net -234.866667 R; expectancy -0.678805 R; positive months 1/12; conditional DD 238.766667 R.
Accepted 350 = CLOSED 346 + EXCLUDED 4; SKIP 0; exclusion share 0.011429; conditional FLAT closures 338; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 16 | -4.066667 | 0.791096 | 1.000000 | 7 | 1 |
| 2023-02 | 35 | -24.033333 | 0.433176 | 0.397790 | 5 | 1 |
| 2023-03 | 43 | -32.966667 | 0.373654 | 0.372197 | 4 | 1 |
| 2023-04 | 30 | 3.716667 | 1.143871 | 1.206612 | 6 | 0 |
| 2023-05 | 22 | -5.700000 | 0.755365 | 0.854369 | 7 | 1 |
| 2023-06 | 32 | -23.416667 | 0.379143 | 0.294479 | 4 | 0 |
| 2023-07 | 31 | -43.050000 | 0.011481 | 0.015789 | 1 | 0 |
| 2023-08 | 22 | -9.483333 | 0.637580 | 0.683333 | 109 | 0 |
| 2023-09 | 33 | -12.483333 | 0.682088 | 0.770186 | 43 | 0 |
| 2023-10 | 25 | -12.000000 | 0.621849 | 0.613636 | 0 | 0 |
| 2023-11 | 24 | -27.850000 | 0.088380 | 0.069231 | 1 | 0 |
| 2023-12 | 33 | -43.533333 | 0.061107 | 0.082927 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK5_TOL1_MAXBARS36_SB2_TP7

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 346; dates/months 202/12; PF R/price 0.447480/0.460143; Net -232.233333 R; expectancy -0.671195 R; positive months 1/12; conditional DD 237.533333 R.
Accepted 350 = CLOSED 346 + EXCLUDED 4; SKIP 0; exclusion share 0.011429; conditional FLAT closures 338; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 16 | -2.666667 | 0.863014 | 1.085366 | 7 | 1 |
| 2023-02 | 35 | -22.366667 | 0.472484 | 0.425414 | 5 | 1 |
| 2023-03 | 43 | -31.466667 | 0.402153 | 0.399103 | 4 | 1 |
| 2023-04 | 30 | 5.216667 | 1.201935 | 1.256198 | 6 | 0 |
| 2023-05 | 22 | -4.300000 | 0.815451 | 0.922330 | 7 | 1 |
| 2023-06 | 32 | -21.750000 | 0.423332 | 0.325153 | 4 | 0 |
| 2023-07 | 31 | -43.050000 | 0.011481 | 0.015789 | 1 | 0 |
| 2023-08 | 22 | -18.816667 | 0.315758 | 0.265625 | 109 | 0 |
| 2023-09 | 33 | -11.150000 | 0.716044 | 0.819876 | 43 | 0 |
| 2023-10 | 25 | -10.500000 | 0.669118 | 0.659091 | 0 | 0 |
| 2023-11 | 24 | -27.850000 | 0.088380 | 0.069231 | 1 | 0 |
| 2023-12 | 33 | -43.533333 | 0.061107 | 0.082927 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK5_TOL1_MAXBARS36_SB2_TP8

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 346; dates/months 202/12; PF R/price 0.436853/0.443101; Net -236.700000 R; expectancy -0.684104 R; positive months 1/12; conditional DD 243.400000 R.
Accepted 350 = CLOSED 346 + EXCLUDED 4; SKIP 0; exclusion share 0.011429; conditional FLAT closures 338; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 16 | -1.266667 | 0.934932 | 1.170732 | 7 | 1 |
| 2023-02 | 35 | -20.700000 | 0.511792 | 0.453039 | 5 | 1 |
| 2023-03 | 43 | -29.966667 | 0.430652 | 0.426009 | 4 | 1 |
| 2023-04 | 30 | 6.716667 | 1.260000 | 1.305785 | 6 | 0 |
| 2023-05 | 22 | -7.500000 | 0.678112 | 0.766990 | 7 | 1 |
| 2023-06 | 32 | -20.083333 | 0.467521 | 0.355828 | 4 | 0 |
| 2023-07 | 31 | -43.050000 | 0.011481 | 0.015789 | 1 | 0 |
| 2023-08 | 22 | -18.816667 | 0.315758 | 0.265625 | 109 | 0 |
| 2023-09 | 33 | -15.150000 | 0.614177 | 0.670807 | 43 | 0 |
| 2023-10 | 25 | -15.500000 | 0.511555 | 0.507576 | 0 | 0 |
| 2023-11 | 24 | -27.850000 | 0.088380 | 0.069231 | 1 | 0 |
| 2023-12 | 33 | -43.533333 | 0.061107 | 0.082927 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK5_TOL1_MAXBARS36_SB2_TP9

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 346; dates/months 202/12; PF R/price 0.442563/0.450247; Net -234.300000 R; expectancy -0.677168 R; positive months 2/12; conditional DD 242.400000 R.
Accepted 350 = CLOSED 346 + EXCLUDED 4; SKIP 0; exclusion share 0.011429; conditional FLAT closures 338; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 16 | 0.133333 | 1.006849 | 1.256098 | 7 | 1 |
| 2023-02 | 35 | -19.033333 | 0.551101 | 0.480663 | 5 | 1 |
| 2023-03 | 43 | -28.466667 | 0.459151 | 0.452915 | 4 | 1 |
| 2023-04 | 30 | 8.216667 | 1.318065 | 1.355372 | 6 | 0 |
| 2023-05 | 22 | -7.500000 | 0.678112 | 0.766990 | 7 | 1 |
| 2023-06 | 32 | -23.750000 | 0.370305 | 0.288344 | 4 | 0 |
| 2023-07 | 31 | -43.050000 | 0.011481 | 0.015789 | 1 | 0 |
| 2023-08 | 22 | -18.816667 | 0.315758 | 0.265625 | 109 | 0 |
| 2023-09 | 33 | -15.150000 | 0.614177 | 0.670807 | 43 | 0 |
| 2023-10 | 25 | -15.500000 | 0.511555 | 0.507576 | 0 | 0 |
| 2023-11 | 24 | -27.850000 | 0.088380 | 0.069231 | 1 | 0 |
| 2023-12 | 33 | -43.533333 | 0.061107 | 0.082927 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK5_TOL1_MAXBARS36_SB2_TP10

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 346; dates/months 202/12; PF R/price 0.434989/0.443101; Net -237.483333 R; expectancy -0.686368 R; positive months 2/12; conditional DD 246.983333 R.
Accepted 350 = CLOSED 346 + EXCLUDED 4; SKIP 0; exclusion share 0.011429; conditional FLAT closures 338; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 16 | 1.533333 | 1.078767 | 1.341463 | 7 | 1 |
| 2023-02 | 35 | -17.366667 | 0.590409 | 0.508287 | 5 | 1 |
| 2023-03 | 43 | -26.966667 | 0.487650 | 0.479821 | 4 | 1 |
| 2023-04 | 30 | 0.466667 | 1.018065 | 1.099174 | 6 | 0 |
| 2023-05 | 22 | -7.500000 | 0.678112 | 0.766990 | 7 | 1 |
| 2023-06 | 32 | -23.750000 | 0.370305 | 0.288344 | 4 | 0 |
| 2023-07 | 31 | -43.050000 | 0.011481 | 0.015789 | 1 | 0 |
| 2023-08 | 22 | -18.816667 | 0.315758 | 0.265625 | 109 | 0 |
| 2023-09 | 33 | -15.150000 | 0.614177 | 0.670807 | 43 | 0 |
| 2023-10 | 25 | -15.500000 | 0.511555 | 0.507576 | 0 | 0 |
| 2023-11 | 24 | -27.850000 | 0.088380 | 0.069231 | 1 | 0 |
| 2023-12 | 33 | -43.533333 | 0.061107 | 0.082927 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK5_TOL2_MAXBARS24_SB1_TP2

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 389; dates/months 204/12; PF R/price 0.495885/0.511111; Net -224.600000 R; expectancy -0.577378 R; positive months 2/12; conditional DD 232.933333 R.
Accepted 392 = CLOSED 389 + EXCLUDED 3; SKIP 0; exclusion share 0.007653; conditional FLAT closures 360; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 26 | 3.600000 | 1.152542 | 1.195652 | 7 | 0 |
| 2023-02 | 35 | -28.650000 | 0.319747 | 0.354037 | 5 | 1 |
| 2023-03 | 41 | -29.883333 | 0.358268 | 0.384211 | 4 | 1 |
| 2023-04 | 41 | -28.416667 | 0.416496 | 0.465969 | 6 | 0 |
| 2023-05 | 31 | -17.333333 | 0.514246 | 0.556338 | 7 | 1 |
| 2023-06 | 38 | -13.333333 | 0.665552 | 0.607595 | 4 | 0 |
| 2023-07 | 34 | -36.100000 | 0.192394 | 0.225989 | 1 | 0 |
| 2023-08 | 26 | -16.266667 | 0.514911 | 0.500000 | 109 | 0 |
| 2023-09 | 28 | 5.733333 | 1.219108 | 1.260000 | 43 | 0 |
| 2023-10 | 31 | -8.350000 | 0.743996 | 0.780488 | 0 | 0 |
| 2023-11 | 31 | -31.183333 | 0.195615 | 0.176471 | 1 | 0 |
| 2023-12 | 27 | -24.416667 | 0.264927 | 0.279412 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK5_TOL2_MAXBARS24_SB1_TP3

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 380; dates/months 203/12; PF R/price 0.553615/0.563244; Net -199.400000 R; expectancy -0.524737 R; positive months 3/12; conditional DD 216.516667 R.
Accepted 384 = CLOSED 380 + EXCLUDED 4; SKIP 0; exclusion share 0.010417; conditional FLAT closures 352; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 25 | 9.733333 | 1.438438 | 1.505882 | 7 | 0 |
| 2023-02 | 35 | -24.500000 | 0.418283 | 0.465839 | 5 | 1 |
| 2023-03 | 39 | -26.483333 | 0.412352 | 0.440217 | 4 | 1 |
| 2023-04 | 41 | -25.050000 | 0.485626 | 0.528796 | 6 | 0 |
| 2023-05 | 30 | -10.883333 | 0.682547 | 0.755556 | 7 | 1 |
| 2023-06 | 37 | -11.266667 | 0.727639 | 0.640244 | 4 | 0 |
| 2023-07 | 34 | -43.400000 | 0.088235 | 0.110526 | 1 | 0 |
| 2023-08 | 25 | -15.900000 | 0.522044 | 0.485075 | 109 | 0 |
| 2023-09 | 27 | 8.600000 | 1.312727 | 1.308411 | 43 | 0 |
| 2023-10 | 31 | 0.033333 | 1.001022 | 1.024390 | 0 | 0 |
| 2023-11 | 29 | -36.766667 | 0.051591 | 0.039216 | 1 | 1 |
| 2023-12 | 27 | -23.516667 | 0.292022 | 0.316176 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK5_TOL2_MAXBARS24_SB1_TP4

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 377; dates/months 203/12; PF R/price 0.510337/0.529511; Net -221.066667 R; expectancy -0.586384 R; positive months 1/12; conditional DD 238.066667 R.
Accepted 381 = CLOSED 377 + EXCLUDED 4; SKIP 0; exclusion share 0.010499; conditional FLAT closures 349; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 25 | 6.716667 | 1.302553 | 1.400000 | 7 | 0 |
| 2023-02 | 34 | -22.683333 | 0.439225 | 0.493590 | 5 | 1 |
| 2023-03 | 39 | -30.983333 | 0.334646 | 0.363158 | 4 | 1 |
| 2023-04 | 41 | -19.083333 | 0.608145 | 0.659686 | 6 | 0 |
| 2023-05 | 29 | -5.083333 | 0.845413 | 0.945312 | 7 | 1 |
| 2023-06 | 36 | -18.566667 | 0.535446 | 0.458599 | 4 | 0 |
| 2023-07 | 34 | -42.000000 | 0.117647 | 0.147368 | 1 | 0 |
| 2023-08 | 25 | -15.750000 | 0.526553 | 0.500000 | 109 | 0 |
| 2023-09 | 27 | -7.683333 | 0.760395 | 0.736000 | 43 | 0 |
| 2023-10 | 31 | -8.566667 | 0.760596 | 0.813433 | 0 | 0 |
| 2023-11 | 29 | -36.766667 | 0.051591 | 0.039216 | 1 | 1 |
| 2023-12 | 27 | -20.616667 | 0.379328 | 0.411765 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK5_TOL2_MAXBARS24_SB1_TP5

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 377; dates/months 203/12; PF R/price 0.488378/0.507513; Net -233.316667 R; expectancy -0.618877 R; positive months 1/12; conditional DD 257.783333 R.
Accepted 381 = CLOSED 377 + EXCLUDED 4; SKIP 0; exclusion share 0.010499; conditional FLAT closures 349; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 25 | 11.283333 | 1.508258 | 1.611765 | 7 | 0 |
| 2023-02 | 34 | -21.283333 | 0.473836 | 0.538462 | 5 | 1 |
| 2023-03 | 39 | -30.483333 | 0.345383 | 0.373684 | 4 | 1 |
| 2023-04 | 41 | -22.366667 | 0.540726 | 0.570681 | 6 | 0 |
| 2023-05 | 29 | -12.683333 | 0.631120 | 0.731343 | 7 | 1 |
| 2023-06 | 36 | -15.400000 | 0.614679 | 0.528662 | 4 | 0 |
| 2023-07 | 34 | -49.000000 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 25 | -14.350000 | 0.568637 | 0.552239 | 109 | 0 |
| 2023-09 | 27 | -16.950000 | 0.497530 | 0.553846 | 43 | 0 |
| 2023-10 | 31 | -4.000000 | 0.888216 | 0.947761 | 0 | 0 |
| 2023-11 | 29 | -36.766667 | 0.051591 | 0.039216 | 1 | 1 |
| 2023-12 | 27 | -21.316667 | 0.358254 | 0.375000 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK5_TOL2_MAXBARS24_SB1_TP6

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 377; dates/months 203/12; PF R/price 0.488671/0.513588; Net -233.950000 R; expectancy -0.620557 R; positive months 2/12; conditional DD 264.683333 R.
Accepted 381 = CLOSED 377 + EXCLUDED 4; SKIP 0; exclusion share 0.010499; conditional FLAT closures 349; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 25 | 14.650000 | 1.659910 | 1.752941 | 7 | 0 |
| 2023-02 | 34 | -19.883333 | 0.508447 | 0.583333 | 5 | 1 |
| 2023-03 | 39 | -30.483333 | 0.345383 | 0.373684 | 4 | 1 |
| 2023-04 | 41 | -30.700000 | 0.369610 | 0.439791 | 6 | 0 |
| 2023-05 | 29 | -11.283333 | 0.671837 | 0.783582 | 7 | 1 |
| 2023-06 | 36 | -22.733333 | 0.451768 | 0.355828 | 4 | 0 |
| 2023-07 | 34 | -49.000000 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 25 | -12.950000 | 0.610721 | 0.604478 | 109 | 0 |
| 2023-09 | 27 | -15.550000 | 0.539032 | 0.607692 | 43 | 0 |
| 2023-10 | 31 | 0.566667 | 1.015836 | 1.082090 | 0 | 0 |
| 2023-11 | 29 | -36.766667 | 0.051591 | 0.039216 | 1 | 1 |
| 2023-12 | 27 | -19.816667 | 0.403412 | 0.419118 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK5_TOL2_MAXBARS24_SB1_TP7

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 377; dates/months 203/12; PF R/price 0.468448/0.489221; Net -244.000000 R; expectancy -0.647215 R; positive months 1/12; conditional DD 272.050000 R.
Accepted 381 = CLOSED 377 + EXCLUDED 4; SKIP 0; exclusion share 0.010499; conditional FLAT closures 349; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 25 | 17.816667 | 1.802553 | 1.882353 | 7 | 0 |
| 2023-02 | 34 | -21.483333 | 0.468892 | 0.532051 | 5 | 1 |
| 2023-03 | 39 | -30.483333 | 0.345383 | 0.373684 | 4 | 1 |
| 2023-04 | 41 | -30.700000 | 0.369610 | 0.439791 | 6 | 0 |
| 2023-05 | 29 | -9.883333 | 0.712555 | 0.835821 | 7 | 1 |
| 2023-06 | 36 | -21.066667 | 0.491961 | 0.386503 | 4 | 0 |
| 2023-07 | 34 | -49.000000 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 25 | -11.550000 | 0.652806 | 0.656716 | 109 | 0 |
| 2023-09 | 27 | -14.150000 | 0.580534 | 0.661538 | 43 | 0 |
| 2023-10 | 31 | -12.666667 | 0.660259 | 0.657143 | 0 | 0 |
| 2023-11 | 29 | -36.766667 | 0.051591 | 0.039216 | 1 | 1 |
| 2023-12 | 27 | -24.066667 | 0.275464 | 0.294118 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK5_TOL2_MAXBARS24_SB1_TP8

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 377; dates/months 203/12; PF R/price 0.455079/0.465859; Net -250.900000 R; expectancy -0.665517 R; positive months 1/12; conditional DD 282.116667 R.
Accepted 381 = CLOSED 377 + EXCLUDED 4; SKIP 0; exclusion share 0.010499; conditional FLAT closures 349; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 25 | 20.983333 | 1.945195 | 2.011765 | 7 | 0 |
| 2023-02 | 34 | -21.483333 | 0.468892 | 0.532051 | 5 | 1 |
| 2023-03 | 39 | -30.483333 | 0.345383 | 0.373684 | 4 | 1 |
| 2023-04 | 41 | -30.700000 | 0.369610 | 0.439791 | 6 | 0 |
| 2023-05 | 29 | -13.483333 | 0.607853 | 0.701493 | 7 | 1 |
| 2023-06 | 36 | -19.400000 | 0.532154 | 0.417178 | 4 | 0 |
| 2023-07 | 34 | -49.000000 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 25 | -22.750000 | 0.343750 | 0.276596 | 109 | 0 |
| 2023-09 | 27 | -12.750000 | 0.622036 | 0.715385 | 43 | 0 |
| 2023-10 | 31 | -11.000000 | 0.704962 | 0.692857 | 0 | 0 |
| 2023-11 | 29 | -36.766667 | 0.051591 | 0.039216 | 1 | 1 |
| 2023-12 | 27 | -24.066667 | 0.275464 | 0.294118 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK5_TOL2_MAXBARS24_SB1_TP9

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 377; dates/months 203/12; PF R/price 0.462101/0.473568; Net -247.666667 R; expectancy -0.656941 R; positive months 1/12; conditional DD 277.383333 R.
Accepted 381 = CLOSED 377 + EXCLUDED 4; SKIP 0; exclusion share 0.010499; conditional FLAT closures 349; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 25 | 19.483333 | 1.877628 | 1.976471 | 7 | 0 |
| 2023-02 | 34 | -21.483333 | 0.468892 | 0.532051 | 5 | 1 |
| 2023-03 | 39 | -30.483333 | 0.345383 | 0.373684 | 4 | 1 |
| 2023-04 | 41 | -30.700000 | 0.369610 | 0.439791 | 6 | 0 |
| 2023-05 | 29 | -13.483333 | 0.607853 | 0.701493 | 7 | 1 |
| 2023-06 | 36 | -17.733333 | 0.572347 | 0.447853 | 4 | 0 |
| 2023-07 | 34 | -49.000000 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 25 | -22.750000 | 0.343750 | 0.276596 | 109 | 0 |
| 2023-09 | 27 | -11.350000 | 0.663538 | 0.769231 | 43 | 0 |
| 2023-10 | 31 | -9.333333 | 0.749665 | 0.728571 | 0 | 0 |
| 2023-11 | 29 | -36.766667 | 0.051591 | 0.039216 | 1 | 1 |
| 2023-12 | 27 | -24.066667 | 0.275464 | 0.294118 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK5_TOL2_MAXBARS24_SB1_TP10

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 377; dates/months 203/12; PF R/price 0.449576/0.466410; Net -253.433333 R; expectancy -0.672237 R; positive months 1/12; conditional DD 284.650000 R.
Accepted 381 = CLOSED 377 + EXCLUDED 4; SKIP 0; exclusion share 0.010499; conditional FLAT closures 349; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 25 | 20.983333 | 1.945195 | 2.047059 | 7 | 0 |
| 2023-02 | 34 | -21.483333 | 0.468892 | 0.532051 | 5 | 1 |
| 2023-03 | 39 | -30.483333 | 0.345383 | 0.373684 | 4 | 1 |
| 2023-04 | 41 | -30.700000 | 0.369610 | 0.439791 | 6 | 0 |
| 2023-05 | 29 | -13.483333 | 0.607853 | 0.701493 | 7 | 1 |
| 2023-06 | 36 | -18.733333 | 0.548232 | 0.429448 | 4 | 0 |
| 2023-07 | 34 | -49.000000 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 25 | -22.750000 | 0.343750 | 0.276596 | 109 | 0 |
| 2023-09 | 27 | -9.950000 | 0.705040 | 0.823077 | 43 | 0 |
| 2023-10 | 31 | -17.000000 | 0.544032 | 0.564286 | 0 | 0 |
| 2023-11 | 29 | -36.766667 | 0.051591 | 0.039216 | 1 | 1 |
| 2023-12 | 27 | -24.066667 | 0.275464 | 0.294118 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK5_TOL2_MAXBARS24_SB2_TP2

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 457; dates/months 222/12; PF R/price 0.556474/0.573376; Net -213.683333 R; expectancy -0.467578 R; positive months 0/12; conditional DD 214.816667 R.
Accepted 461 = CLOSED 457 + EXCLUDED 4; SKIP 0; exclusion share 0.008677; conditional FLAT closures 423; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 30 | -4.500000 | 0.837935 | 0.960000 | 7 | 0 |
| 2023-02 | 44 | -18.666667 | 0.593614 | 0.591133 | 5 | 1 |
| 2023-03 | 51 | -32.116667 | 0.418176 | 0.430830 | 4 | 1 |
| 2023-04 | 42 | -12.000000 | 0.690189 | 0.786885 | 6 | 0 |
| 2023-05 | 34 | -16.566667 | 0.546119 | 0.603550 | 7 | 1 |
| 2023-06 | 44 | -3.566667 | 0.912079 | 0.812500 | 4 | 0 |
| 2023-07 | 39 | -38.766667 | 0.182138 | 0.223744 | 1 | 0 |
| 2023-08 | 29 | -16.183333 | 0.527264 | 0.463855 | 109 | 0 |
| 2023-09 | 36 | -3.933333 | 0.890233 | 0.993421 | 43 | 0 |
| 2023-10 | 37 | -5.033333 | 0.857681 | 0.866242 | 0 | 0 |
| 2023-11 | 34 | -28.216667 | 0.277422 | 0.217391 | 1 | 1 |
| 2023-12 | 37 | -34.133333 | 0.244838 | 0.292929 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK5_TOL2_MAXBARS24_SB2_TP3

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 442; dates/months 221/12; PF R/price 0.600674/0.612301; Net -191.550000 R; expectancy -0.433371 R; positive months 1/12; conditional DD 195.116667 R.
Accepted 447 = CLOSED 442 + EXCLUDED 5; SKIP 0; exclusion share 0.011186; conditional FLAT closures 409; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 29 | -1.116667 | 0.957755 | 1.111111 | 7 | 0 |
| 2023-02 | 40 | -6.666667 | 0.839744 | 0.819672 | 5 | 2 |
| 2023-03 | 49 | -32.283333 | 0.415157 | 0.407115 | 4 | 1 |
| 2023-04 | 42 | -7.866667 | 0.796902 | 0.890710 | 6 | 0 |
| 2023-05 | 32 | -13.466667 | 0.605854 | 0.716129 | 7 | 1 |
| 2023-06 | 41 | 1.150000 | 1.029163 | 0.834197 | 4 | 0 |
| 2023-07 | 39 | -45.633333 | 0.089761 | 0.115385 | 1 | 0 |
| 2023-08 | 28 | -13.550000 | 0.586049 | 0.525000 | 109 | 0 |
| 2023-09 | 35 | -2.400000 | 0.935542 | 1.037736 | 43 | 0 |
| 2023-10 | 37 | -9.833333 | 0.753756 | 0.805714 | 0 | 0 |
| 2023-11 | 33 | -27.883333 | 0.282898 | 0.210811 | 1 | 1 |
| 2023-12 | 37 | -32.000000 | 0.292035 | 0.353535 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK5_TOL2_MAXBARS24_SB2_TP4

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 440; dates/months 221/12; PF R/price 0.573458/0.585135; Net -207.150000 R; expectancy -0.470795 R; positive months 0/12; conditional DD 213.516667 R.
Accepted 445 = CLOSED 440 + EXCLUDED 5; SKIP 0; exclusion share 0.011236; conditional FLAT closures 407; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 29 | -0.883333 | 0.966583 | 1.119658 | 7 | 0 |
| 2023-02 | 39 | -7.200000 | 0.826923 | 0.792350 | 5 | 2 |
| 2023-03 | 49 | -34.116667 | 0.381944 | 0.399209 | 4 | 1 |
| 2023-04 | 42 | -7.100000 | 0.816695 | 0.912568 | 6 | 0 |
| 2023-05 | 32 | -18.333333 | 0.484536 | 0.586420 | 7 | 1 |
| 2023-06 | 40 | -8.200000 | 0.793797 | 0.631579 | 4 | 0 |
| 2023-07 | 39 | -50.966667 | 0.009715 | 0.012397 | 1 | 0 |
| 2023-08 | 28 | -12.216667 | 0.626782 | 0.575000 | 109 | 0 |
| 2023-09 | 35 | -9.516667 | 0.762874 | 0.866279 | 43 | 0 |
| 2023-10 | 37 | -3.533333 | 0.911519 | 0.965714 | 0 | 0 |
| 2023-11 | 33 | -24.716667 | 0.364338 | 0.270270 | 1 | 1 |
| 2023-12 | 37 | -30.366667 | 0.328171 | 0.388889 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK5_TOL2_MAXBARS24_SB2_TP5

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 440; dates/months 221/12; PF R/price 0.552870/0.567483; Net -219.816667 R; expectancy -0.499583 R; positive months 2/12; conditional DD 230.266667 R.
Accepted 445 = CLOSED 440 + EXCLUDED 5; SKIP 0; exclusion share 0.011236; conditional FLAT closures 407; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 29 | 3.350000 | 1.126734 | 1.299145 | 7 | 0 |
| 2023-02 | 39 | -14.533333 | 0.664099 | 0.691489 | 5 | 2 |
| 2023-03 | 49 | -32.616667 | 0.409118 | 0.422925 | 4 | 1 |
| 2023-04 | 42 | -15.266667 | 0.605852 | 0.710383 | 6 | 0 |
| 2023-05 | 32 | -17.000000 | 0.522024 | 0.635802 | 7 | 1 |
| 2023-06 | 40 | -10.366667 | 0.748178 | 0.548223 | 4 | 0 |
| 2023-07 | 39 | -50.966667 | 0.009715 | 0.012397 | 1 | 0 |
| 2023-08 | 28 | -10.883333 | 0.667515 | 0.625000 | 109 | 0 |
| 2023-09 | 35 | -8.783333 | 0.781146 | 0.883721 | 43 | 0 |
| 2023-10 | 37 | 3.766667 | 1.094324 | 1.154286 | 0 | 0 |
| 2023-11 | 33 | -30.550000 | 0.243500 | 0.162304 | 1 | 1 |
| 2023-12 | 37 | -35.966667 | 0.228183 | 0.273171 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK5_TOL2_MAXBARS24_SB2_TP6

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 440; dates/months 221/12; PF R/price 0.530881/0.547069; Net -231.283333 R; expectancy -0.525644 R; positive months 1/12; conditional DD 241.433333 R.
Accepted 445 = CLOSED 440 + EXCLUDED 5; SKIP 0; exclusion share 0.011236; conditional FLAT closures 407; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 29 | 5.583333 | 1.211223 | 1.376068 | 7 | 0 |
| 2023-02 | 39 | -13.866667 | 0.679507 | 0.686170 | 5 | 2 |
| 2023-03 | 49 | -31.116667 | 0.436292 | 0.446640 | 4 | 1 |
| 2023-04 | 42 | -15.266667 | 0.605852 | 0.710383 | 6 | 0 |
| 2023-05 | 32 | -15.666667 | 0.559513 | 0.685185 | 7 | 1 |
| 2023-06 | 40 | -15.533333 | 0.622672 | 0.477157 | 4 | 0 |
| 2023-07 | 39 | -50.966667 | 0.009715 | 0.012397 | 1 | 0 |
| 2023-08 | 28 | -9.550000 | 0.708248 | 0.675000 | 109 | 0 |
| 2023-09 | 35 | -5.783333 | 0.855897 | 0.982558 | 43 | 0 |
| 2023-10 | 37 | -11.066667 | 0.732258 | 0.758242 | 0 | 0 |
| 2023-11 | 33 | -28.883333 | 0.284771 | 0.188482 | 1 | 1 |
| 2023-12 | 37 | -39.166667 | 0.159514 | 0.195122 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK5_TOL2_MAXBARS24_SB2_TP7

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 440; dates/months 221/12; PF R/price 0.529921/0.538496; Net -232.383333 R; expectancy -0.528144 R; positive months 1/12; conditional DD 247.100000 R.
Accepted 445 = CLOSED 440 + EXCLUDED 5; SKIP 0; exclusion share 0.011236; conditional FLAT closures 407; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 29 | 8.483333 | 1.320933 | 1.487179 | 7 | 0 |
| 2023-02 | 39 | -12.200000 | 0.718028 | 0.712766 | 5 | 2 |
| 2023-03 | 49 | -29.616667 | 0.463466 | 0.470356 | 4 | 1 |
| 2023-04 | 42 | -15.266667 | 0.605852 | 0.710383 | 6 | 0 |
| 2023-05 | 32 | -18.500000 | 0.479850 | 0.580247 | 7 | 1 |
| 2023-06 | 40 | -12.366667 | 0.699595 | 0.532995 | 4 | 0 |
| 2023-07 | 39 | -50.966667 | 0.009715 | 0.012397 | 1 | 0 |
| 2023-08 | 28 | -18.883333 | 0.445695 | 0.357143 | 109 | 0 |
| 2023-09 | 35 | -3.116667 | 0.922342 | 1.075581 | 43 | 0 |
| 2023-10 | 37 | -9.566667 | 0.768548 | 0.791209 | 0 | 0 |
| 2023-11 | 33 | -31.216667 | 0.226991 | 0.151832 | 1 | 1 |
| 2023-12 | 37 | -39.166667 | 0.159514 | 0.195122 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK5_TOL2_MAXBARS24_SB2_TP8

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 440; dates/months 221/12; PF R/price 0.525842/0.533628; Net -234.400000 R; expectancy -0.532727 R; positive months 1/12; conditional DD 249.433333 R.
Accepted 445 = CLOSED 440 + EXCLUDED 5; SKIP 0; exclusion share 0.011236; conditional FLAT closures 407; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 29 | 7.133333 | 1.269861 | 1.452991 | 7 | 0 |
| 2023-02 | 39 | -10.533333 | 0.756549 | 0.739362 | 5 | 2 |
| 2023-03 | 49 | -28.116667 | 0.490640 | 0.494071 | 4 | 1 |
| 2023-04 | 42 | -15.266667 | 0.605852 | 0.710383 | 6 | 0 |
| 2023-05 | 32 | -18.500000 | 0.479850 | 0.580247 | 7 | 1 |
| 2023-06 | 40 | -10.700000 | 0.740081 | 0.558376 | 4 | 0 |
| 2023-07 | 39 | -50.966667 | 0.009715 | 0.012397 | 1 | 0 |
| 2023-08 | 28 | -18.883333 | 0.445695 | 0.357143 | 109 | 0 |
| 2023-09 | 35 | -3.616667 | 0.909884 | 1.058140 | 43 | 0 |
| 2023-10 | 37 | -14.566667 | 0.647581 | 0.681319 | 0 | 0 |
| 2023-11 | 33 | -31.216667 | 0.226991 | 0.151832 | 1 | 1 |
| 2023-12 | 37 | -39.166667 | 0.159514 | 0.195122 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK5_TOL2_MAXBARS24_SB2_TP9

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 440; dates/months 221/12; PF R/price 0.530360/0.540265; Net -232.166667 R; expectancy -0.527652 R; positive months 1/12; conditional DD 250.266667 R.
Accepted 445 = CLOSED 440 + EXCLUDED 5; SKIP 0; exclusion share 0.011236; conditional FLAT closures 407; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 29 | 8.533333 | 1.322825 | 1.512821 | 7 | 0 |
| 2023-02 | 39 | -8.866667 | 0.795069 | 0.765957 | 5 | 2 |
| 2023-03 | 49 | -26.616667 | 0.517814 | 0.517787 | 4 | 1 |
| 2023-04 | 42 | -15.266667 | 0.605852 | 0.710383 | 6 | 0 |
| 2023-05 | 32 | -18.500000 | 0.479850 | 0.580247 | 7 | 1 |
| 2023-06 | 40 | -14.366667 | 0.651012 | 0.502538 | 4 | 0 |
| 2023-07 | 39 | -50.966667 | 0.009715 | 0.012397 | 1 | 0 |
| 2023-08 | 28 | -18.883333 | 0.445695 | 0.357143 | 109 | 0 |
| 2023-09 | 35 | -2.283333 | 0.943106 | 1.104651 | 43 | 0 |
| 2023-10 | 37 | -14.566667 | 0.647581 | 0.681319 | 0 | 0 |
| 2023-11 | 33 | -31.216667 | 0.226991 | 0.151832 | 1 | 1 |
| 2023-12 | 37 | -39.166667 | 0.159514 | 0.195122 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK5_TOL2_MAXBARS24_SB2_TP10

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 440; dates/months 221/12; PF R/price 0.526449/0.530973; Net -234.100000 R; expectancy -0.532045 R; positive months 1/12; conditional DD 255.266667 R.
Accepted 445 = CLOSED 440 + EXCLUDED 5; SKIP 0; exclusion share 0.011236; conditional FLAT closures 407; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 29 | 9.933333 | 1.375788 | 1.572650 | 7 | 0 |
| 2023-02 | 39 | -7.200000 | 0.833590 | 0.792553 | 5 | 2 |
| 2023-03 | 49 | -25.116667 | 0.544988 | 0.541502 | 4 | 1 |
| 2023-04 | 42 | -15.266667 | 0.605852 | 0.710383 | 6 | 0 |
| 2023-05 | 32 | -18.500000 | 0.479850 | 0.580247 | 7 | 1 |
| 2023-06 | 40 | -14.366667 | 0.651012 | 0.502538 | 4 | 0 |
| 2023-07 | 39 | -50.966667 | 0.009715 | 0.012397 | 1 | 0 |
| 2023-08 | 28 | -18.883333 | 0.445695 | 0.357143 | 109 | 0 |
| 2023-09 | 35 | -8.783333 | 0.781146 | 0.877907 | 43 | 0 |
| 2023-10 | 37 | -14.566667 | 0.647581 | 0.681319 | 0 | 0 |
| 2023-11 | 33 | -31.216667 | 0.226991 | 0.151832 | 1 | 1 |
| 2023-12 | 37 | -39.166667 | 0.159514 | 0.195122 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK5_TOL2_MAXBARS36_SB1_TP2

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 362; dates/months 201/12; PF R/price 0.458901/0.481459; Net -229.633333 R; expectancy -0.634346 R; positive months 1/12; conditional DD 232.633333 R.
Accepted 366 = CLOSED 362 + EXCLUDED 4; SKIP 0; exclusion share 0.010929; conditional FLAT closures 351; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 23 | -3.866667 | 0.841530 | 0.937500 | 7 | 1 |
| 2023-02 | 28 | -21.166667 | 0.370664 | 0.403101 | 5 | 1 |
| 2023-03 | 40 | -30.433333 | 0.332114 | 0.356757 | 4 | 1 |
| 2023-04 | 37 | -25.750000 | 0.434480 | 0.483333 | 6 | 0 |
| 2023-05 | 23 | -9.533333 | 0.616879 | 0.663366 | 7 | 1 |
| 2023-06 | 36 | -11.833333 | 0.691573 | 0.631579 | 4 | 0 |
| 2023-07 | 35 | -32.683333 | 0.267464 | 0.284091 | 1 | 0 |
| 2023-08 | 24 | -23.266667 | 0.269874 | 0.314961 | 109 | 0 |
| 2023-09 | 31 | 1.000000 | 1.032362 | 1.076923 | 43 | 0 |
| 2023-10 | 30 | -15.850000 | 0.535418 | 0.558140 | 0 | 0 |
| 2023-11 | 30 | -32.083333 | 0.145204 | 0.144828 | 1 | 0 |
| 2023-12 | 25 | -24.166667 | 0.266936 | 0.281481 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK5_TOL2_MAXBARS36_SB1_TP3

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 354; dates/months 200/12; PF R/price 0.507705/0.525223; Net -210.316667 R; expectancy -0.594115 R; positive months 2/12; conditional DD 219.300000 R.
Accepted 359 = CLOSED 354 + EXCLUDED 5; SKIP 0; exclusion share 0.013928; conditional FLAT closures 343; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 22 | 2.600000 | 1.113043 | 1.224719 | 7 | 1 |
| 2023-02 | 28 | -17.016667 | 0.494054 | 0.542636 | 5 | 1 |
| 2023-03 | 39 | -27.083333 | 0.385401 | 0.407821 | 4 | 1 |
| 2023-04 | 37 | -22.383333 | 0.508419 | 0.550000 | 6 | 0 |
| 2023-05 | 22 | -3.333333 | 0.858055 | 0.946809 | 7 | 1 |
| 2023-06 | 35 | -9.766667 | 0.755017 | 0.664557 | 4 | 0 |
| 2023-07 | 35 | -44.983333 | 0.085395 | 0.108247 | 1 | 0 |
| 2023-08 | 23 | -22.900000 | 0.275316 | 0.302326 | 109 | 0 |
| 2023-09 | 30 | 3.866667 | 1.119959 | 1.129032 | 43 | 0 |
| 2023-10 | 30 | -9.716667 | 0.715193 | 0.720930 | 0 | 0 |
| 2023-11 | 28 | -36.333333 | 0.031972 | 0.027586 | 1 | 1 |
| 2023-12 | 25 | -23.266667 | 0.294237 | 0.318519 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK5_TOL2_MAXBARS36_SB1_TP4

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 352; dates/months 200/12; PF R/price 0.470439/0.495026; Net -229.450000 R; expectancy -0.651847 R; positive months 2/12; conditional DD 241.650000 R.
Accepted 357 = CLOSED 352 + EXCLUDED 5; SKIP 0; exclusion share 0.014006; conditional FLAT closures 341; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 22 | 2.916667 | 1.126812 | 1.235955 | 7 | 1 |
| 2023-02 | 27 | -15.200000 | 0.524505 | 0.580645 | 5 | 1 |
| 2023-03 | 39 | -31.583333 | 0.306876 | 0.329730 | 4 | 1 |
| 2023-04 | 37 | -16.416667 | 0.639458 | 0.688889 | 6 | 0 |
| 2023-05 | 22 | 1.066667 | 1.045422 | 1.148936 | 7 | 1 |
| 2023-06 | 35 | -18.466667 | 0.536789 | 0.455696 | 4 | 0 |
| 2023-07 | 35 | -43.583333 | 0.113860 | 0.144330 | 1 | 0 |
| 2023-08 | 23 | -22.750000 | 0.280063 | 0.317829 | 109 | 0 |
| 2023-09 | 30 | -12.416667 | 0.662591 | 0.647887 | 43 | 0 |
| 2023-10 | 29 | -16.316667 | 0.544015 | 0.582090 | 0 | 0 |
| 2023-11 | 28 | -36.333333 | 0.031972 | 0.027586 | 1 | 1 |
| 2023-12 | 25 | -20.366667 | 0.382204 | 0.414815 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK5_TOL2_MAXBARS36_SB1_TP5

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 352; dates/months 200/12; PF R/price 0.447984/0.472496; Net -241.700000 R; expectancy -0.686648 R; positive months 1/12; conditional DD 261.366667 R.
Accepted 357 = CLOSED 352 + EXCLUDED 5; SKIP 0; exclusion share 0.014006; conditional FLAT closures 341; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 22 | 7.483333 | 1.325362 | 1.438202 | 7 | 1 |
| 2023-02 | 27 | -13.800000 | 0.568300 | 0.637097 | 5 | 1 |
| 2023-03 | 39 | -31.083333 | 0.317849 | 0.340541 | 4 | 1 |
| 2023-04 | 37 | -19.700000 | 0.567350 | 0.594444 | 6 | 0 |
| 2023-05 | 22 | -6.533333 | 0.738492 | 0.850000 | 7 | 1 |
| 2023-06 | 35 | -15.300000 | 0.616221 | 0.525316 | 4 | 0 |
| 2023-07 | 35 | -50.583333 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 23 | -21.350000 | 0.324367 | 0.372093 | 109 | 0 |
| 2023-09 | 30 | -21.683333 | 0.436308 | 0.489796 | 43 | 0 |
| 2023-10 | 29 | -11.750000 | 0.671635 | 0.716418 | 0 | 0 |
| 2023-11 | 28 | -36.333333 | 0.031972 | 0.027586 | 1 | 1 |
| 2023-12 | 25 | -21.066667 | 0.360971 | 0.377778 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK5_TOL2_MAXBARS36_SB1_TP6

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 352; dates/months 200/12; PF R/price 0.448428/0.478938; Net -242.333333 R; expectancy -0.688447 R; positive months 1/12; conditional DD 268.266667 R.
Accepted 357 = CLOSED 352 + EXCLUDED 5; SKIP 0; exclusion share 0.014006; conditional FLAT closures 341; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 22 | 10.850000 | 1.471739 | 1.573034 | 7 | 1 |
| 2023-02 | 27 | -12.400000 | 0.612096 | 0.693548 | 5 | 1 |
| 2023-03 | 39 | -31.083333 | 0.317849 | 0.340541 | 4 | 1 |
| 2023-04 | 37 | -28.033333 | 0.384334 | 0.455556 | 6 | 0 |
| 2023-05 | 22 | -5.133333 | 0.794530 | 0.920000 | 7 | 1 |
| 2023-06 | 35 | -22.633333 | 0.452861 | 0.353659 | 4 | 0 |
| 2023-07 | 35 | -50.583333 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 23 | -19.950000 | 0.368671 | 0.426357 | 109 | 0 |
| 2023-09 | 30 | -20.283333 | 0.472704 | 0.537415 | 43 | 0 |
| 2023-10 | 29 | -7.183333 | 0.799255 | 0.850746 | 0 | 0 |
| 2023-11 | 28 | -36.333333 | 0.031972 | 0.027586 | 1 | 1 |
| 2023-12 | 25 | -19.566667 | 0.406471 | 0.422222 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK5_TOL2_MAXBARS36_SB1_TP7

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 352; dates/months 200/12; PF R/price 0.427507/0.453709; Net -252.383333 R; expectancy -0.716998 R; positive months 1/12; conditional DD 275.633333 R.
Accepted 357 = CLOSED 352 + EXCLUDED 5; SKIP 0; exclusion share 0.014006; conditional FLAT closures 341; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 22 | 14.016667 | 1.609420 | 1.696629 | 7 | 1 |
| 2023-02 | 27 | -14.000000 | 0.562044 | 0.629032 | 5 | 1 |
| 2023-03 | 39 | -31.083333 | 0.317849 | 0.340541 | 4 | 1 |
| 2023-04 | 37 | -28.033333 | 0.384334 | 0.455556 | 6 | 0 |
| 2023-05 | 22 | -3.733333 | 0.850567 | 0.990000 | 7 | 1 |
| 2023-06 | 35 | -20.966667 | 0.493151 | 0.384146 | 4 | 0 |
| 2023-07 | 35 | -50.583333 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 23 | -18.550000 | 0.412975 | 0.480620 | 109 | 0 |
| 2023-09 | 30 | -18.883333 | 0.509099 | 0.585034 | 43 | 0 |
| 2023-10 | 29 | -20.416667 | 0.452392 | 0.435714 | 0 | 0 |
| 2023-11 | 28 | -36.333333 | 0.031972 | 0.027586 | 1 | 1 |
| 2023-12 | 25 | -23.816667 | 0.277553 | 0.296296 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK5_TOL2_MAXBARS36_SB1_TP8

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 352; dates/months 200/12; PF R/price 0.413718/0.429553; Net -259.283333 R; expectancy -0.736600 R; positive months 1/12; conditional DD 285.700000 R.
Accepted 357 = CLOSED 352 + EXCLUDED 5; SKIP 0; exclusion share 0.014006; conditional FLAT closures 341; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 22 | 17.183333 | 1.747101 | 1.820225 | 7 | 1 |
| 2023-02 | 27 | -14.000000 | 0.562044 | 0.629032 | 5 | 1 |
| 2023-03 | 39 | -31.083333 | 0.317849 | 0.340541 | 4 | 1 |
| 2023-04 | 37 | -28.033333 | 0.384334 | 0.455556 | 6 | 0 |
| 2023-05 | 22 | -7.333333 | 0.706471 | 0.810000 | 7 | 1 |
| 2023-06 | 35 | -19.300000 | 0.533441 | 0.414634 | 4 | 0 |
| 2023-07 | 35 | -50.583333 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 23 | -29.750000 | 0.098485 | 0.095588 | 109 | 0 |
| 2023-09 | 30 | -17.483333 | 0.545494 | 0.632653 | 43 | 0 |
| 2023-10 | 29 | -18.750000 | 0.497094 | 0.471429 | 0 | 0 |
| 2023-11 | 28 | -36.333333 | 0.031972 | 0.027586 | 1 | 1 |
| 2023-12 | 25 | -23.816667 | 0.277553 | 0.296296 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK5_TOL2_MAXBARS36_SB1_TP9

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 352; dates/months 200/12; PF R/price 0.421029/0.437572; Net -256.050000 R; expectancy -0.727415 R; positive months 1/12; conditional DD 280.966667 R.
Accepted 357 = CLOSED 352 + EXCLUDED 5; SKIP 0; exclusion share 0.014006; conditional FLAT closures 341; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 22 | 15.683333 | 1.681884 | 1.786517 | 7 | 1 |
| 2023-02 | 27 | -14.000000 | 0.562044 | 0.629032 | 5 | 1 |
| 2023-03 | 39 | -31.083333 | 0.317849 | 0.340541 | 4 | 1 |
| 2023-04 | 37 | -28.033333 | 0.384334 | 0.455556 | 6 | 0 |
| 2023-05 | 22 | -7.333333 | 0.706471 | 0.810000 | 7 | 1 |
| 2023-06 | 35 | -17.633333 | 0.573731 | 0.445122 | 4 | 0 |
| 2023-07 | 35 | -50.583333 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 23 | -29.750000 | 0.098485 | 0.095588 | 109 | 0 |
| 2023-09 | 30 | -16.083333 | 0.581889 | 0.680272 | 43 | 0 |
| 2023-10 | 29 | -17.083333 | 0.541797 | 0.507143 | 0 | 0 |
| 2023-11 | 28 | -36.333333 | 0.031972 | 0.027586 | 1 | 1 |
| 2023-12 | 25 | -23.816667 | 0.277553 | 0.296296 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK5_TOL2_MAXBARS36_SB1_TP10

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 352; dates/months 200/12; PF R/price 0.407989/0.430126; Net -261.816667 R; expectancy -0.743797 R; positive months 1/12; conditional DD 288.233333 R.
Accepted 357 = CLOSED 352 + EXCLUDED 5; SKIP 0; exclusion share 0.014006; conditional FLAT closures 341; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 22 | 17.183333 | 1.747101 | 1.853933 | 7 | 1 |
| 2023-02 | 27 | -14.000000 | 0.562044 | 0.629032 | 5 | 1 |
| 2023-03 | 39 | -31.083333 | 0.317849 | 0.340541 | 4 | 1 |
| 2023-04 | 37 | -28.033333 | 0.384334 | 0.455556 | 6 | 0 |
| 2023-05 | 22 | -7.333333 | 0.706471 | 0.810000 | 7 | 1 |
| 2023-06 | 35 | -18.633333 | 0.549557 | 0.426829 | 4 | 0 |
| 2023-07 | 35 | -50.583333 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 23 | -29.750000 | 0.098485 | 0.095588 | 109 | 0 |
| 2023-09 | 30 | -14.683333 | 0.618284 | 0.727891 | 43 | 0 |
| 2023-10 | 29 | -24.750000 | 0.336165 | 0.342857 | 0 | 0 |
| 2023-11 | 28 | -36.333333 | 0.031972 | 0.027586 | 1 | 1 |
| 2023-12 | 25 | -23.816667 | 0.277553 | 0.296296 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK5_TOL2_MAXBARS36_SB2_TP2

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 428; dates/months 219/12; PF R/price 0.536022/0.555396; Net -212.633333 R; expectancy -0.496807 R; positive months 0/12; conditional DD 213.766667 R.
Accepted 433 = CLOSED 428 + EXCLUDED 5; SKIP 0; exclusion share 0.011547; conditional FLAT closures 415; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 26 | -8.333333 | 0.698068 | 0.818898 | 7 | 1 |
| 2023-02 | 36 | -10.100000 | 0.723540 | 0.714286 | 5 | 1 |
| 2023-03 | 50 | -32.883333 | 0.395156 | 0.403226 | 4 | 1 |
| 2023-04 | 39 | -10.900000 | 0.707252 | 0.802260 | 6 | 0 |
| 2023-05 | 26 | -9.200000 | 0.653266 | 0.735537 | 7 | 1 |
| 2023-06 | 42 | -6.366667 | 0.840966 | 0.784946 | 4 | 0 |
| 2023-07 | 39 | -33.250000 | 0.259190 | 0.290476 | 1 | 0 |
| 2023-08 | 28 | -21.516667 | 0.349294 | 0.316770 | 109 | 0 |
| 2023-09 | 39 | -8.016667 | 0.799165 | 0.883041 | 43 | 0 |
| 2023-10 | 37 | -13.700000 | 0.643539 | 0.639053 | 0 | 0 |
| 2023-11 | 33 | -27.766667 | 0.269619 | 0.215909 | 1 | 1 |
| 2023-12 | 33 | -30.600000 | 0.265600 | 0.310160 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK5_TOL2_MAXBARS36_SB2_TP3

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 416; dates/months 218/12; PF R/price 0.566466/0.580615; Net -200.083333 R; expectancy -0.480970 R; positive months 0/12; conditional DD 203.150000 R.
Accepted 422 = CLOSED 416 + EXCLUDED 6; SKIP 0; exclusion share 0.014218; conditional FLAT closures 403; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 25 | -3.200000 | 0.878173 | 1.016807 | 7 | 1 |
| 2023-02 | 34 | -0.933333 | 0.973359 | 0.935484 | 5 | 2 |
| 2023-03 | 49 | -32.783333 | 0.396996 | 0.383065 | 4 | 1 |
| 2023-04 | 39 | -6.766667 | 0.818263 | 0.909605 | 6 | 0 |
| 2023-05 | 25 | -7.433333 | 0.708877 | 0.852174 | 7 | 1 |
| 2023-06 | 39 | -3.316667 | 0.914739 | 0.780749 | 4 | 0 |
| 2023-07 | 39 | -44.616667 | 0.091619 | 0.116883 | 1 | 0 |
| 2023-08 | 26 | -18.550000 | 0.406083 | 0.376623 | 109 | 0 |
| 2023-09 | 38 | -6.483333 | 0.843082 | 0.926966 | 43 | 0 |
| 2023-10 | 37 | -20.100000 | 0.532558 | 0.561497 | 0 | 0 |
| 2023-11 | 32 | -27.433333 | 0.275209 | 0.209040 | 1 | 1 |
| 2023-12 | 33 | -28.466667 | 0.316800 | 0.374332 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK5_TOL2_MAXBARS36_SB2_TP4

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 414; dates/months 218/12; PF R/price 0.553516/0.563202; Net -207.950000 R; expectancy -0.502295 R; positive months 0/12; conditional DD 212.983333 R.
Accepted 420 = CLOSED 414 + EXCLUDED 6; SKIP 0; exclusion share 0.014286; conditional FLAT closures 401; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 25 | -2.966667 | 0.887056 | 1.025210 | 7 | 1 |
| 2023-02 | 33 | -1.466667 | 0.958135 | 0.903226 | 5 | 2 |
| 2023-03 | 49 | -34.616667 | 0.363274 | 0.375000 | 4 | 1 |
| 2023-04 | 39 | -6.000000 | 0.838854 | 0.932203 | 6 | 0 |
| 2023-05 | 25 | -12.300000 | 0.543317 | 0.672131 | 7 | 1 |
| 2023-06 | 39 | -7.333333 | 0.811482 | 0.641711 | 4 | 0 |
| 2023-07 | 39 | -49.950000 | 0.009911 | 0.012552 | 1 | 0 |
| 2023-08 | 26 | -17.216667 | 0.448773 | 0.428571 | 109 | 0 |
| 2023-09 | 38 | -13.600000 | 0.692424 | 0.780105 | 43 | 0 |
| 2023-10 | 36 | -11.400000 | 0.725962 | 0.766667 | 0 | 0 |
| 2023-11 | 32 | -24.266667 | 0.358873 | 0.271186 | 1 | 1 |
| 2023-12 | 33 | -26.833333 | 0.356000 | 0.411765 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK5_TOL2_MAXBARS36_SB2_TP5

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 414; dates/months 218/12; PF R/price 0.532311/0.545118; Net -220.616667 R; expectancy -0.532890 R; positive months 1/12; conditional DD 228.450000 R.
Accepted 420 = CLOSED 414 + EXCLUDED 6; SKIP 0; exclusion share 0.014286; conditional FLAT closures 401; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 25 | 1.266667 | 1.048223 | 1.201681 | 7 | 1 |
| 2023-02 | 33 | -8.800000 | 0.760218 | 0.781250 | 5 | 2 |
| 2023-03 | 49 | -33.116667 | 0.390865 | 0.399194 | 4 | 1 |
| 2023-04 | 39 | -14.166667 | 0.619517 | 0.723164 | 6 | 0 |
| 2023-05 | 25 | -10.966667 | 0.592822 | 0.737705 | 7 | 1 |
| 2023-06 | 39 | -9.500000 | 0.764268 | 0.556701 | 4 | 0 |
| 2023-07 | 39 | -49.950000 | 0.009911 | 0.012552 | 1 | 0 |
| 2023-08 | 26 | -15.883333 | 0.491462 | 0.480519 | 109 | 0 |
| 2023-09 | 38 | -12.866667 | 0.709009 | 0.795812 | 43 | 0 |
| 2023-10 | 36 | -4.100000 | 0.901442 | 0.950000 | 0 | 0 |
| 2023-11 | 32 | -30.100000 | 0.235070 | 0.158470 | 1 | 1 |
| 2023-12 | 33 | -32.433333 | 0.246904 | 0.288660 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK5_TOL2_MAXBARS36_SB2_TP6

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 413; dates/months 218/12; PF R/price 0.511260/0.525196; Net -230.416667 R; expectancy -0.557910 R; positive months 1/12; conditional DD 237.650000 R.
Accepted 419 = CLOSED 413 + EXCLUDED 6; SKIP 0; exclusion share 0.014320; conditional FLAT closures 400; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 25 | 3.500000 | 1.133249 | 1.277311 | 7 | 1 |
| 2023-02 | 33 | -8.133333 | 0.778383 | 0.775000 | 5 | 2 |
| 2023-03 | 49 | -31.616667 | 0.418455 | 0.423387 | 4 | 1 |
| 2023-04 | 39 | -14.166667 | 0.619517 | 0.723164 | 6 | 0 |
| 2023-05 | 25 | -9.633333 | 0.642327 | 0.803279 | 7 | 1 |
| 2023-06 | 39 | -14.666667 | 0.636063 | 0.484536 | 4 | 0 |
| 2023-07 | 39 | -49.950000 | 0.009911 | 0.012552 | 1 | 0 |
| 2023-08 | 26 | -14.550000 | 0.534152 | 0.532468 | 109 | 0 |
| 2023-09 | 38 | -9.866667 | 0.776856 | 0.884817 | 43 | 0 |
| 2023-10 | 35 | -17.266667 | 0.582258 | 0.587912 | 0 | 0 |
| 2023-11 | 32 | -28.433333 | 0.277425 | 0.185792 | 1 | 1 |
| 2023-12 | 33 | -35.633333 | 0.172601 | 0.206186 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK5_TOL2_MAXBARS36_SB2_TP7

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 413; dates/months 218/12; PF R/price 0.510311/0.516352; Net -231.516667 R; expectancy -0.560573 R; positive months 1/12; conditional DD 243.316667 R.
Accepted 419 = CLOSED 413 + EXCLUDED 6; SKIP 0; exclusion share 0.014320; conditional FLAT closures 400; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 25 | 6.400000 | 1.243655 | 1.386555 | 7 | 1 |
| 2023-02 | 33 | -6.466667 | 0.823797 | 0.806250 | 5 | 2 |
| 2023-03 | 49 | -30.116667 | 0.446045 | 0.447581 | 4 | 1 |
| 2023-04 | 39 | -14.166667 | 0.619517 | 0.723164 | 6 | 0 |
| 2023-05 | 25 | -12.466667 | 0.537129 | 0.663934 | 7 | 1 |
| 2023-06 | 39 | -11.500000 | 0.714640 | 0.541237 | 4 | 0 |
| 2023-07 | 39 | -49.950000 | 0.009911 | 0.012552 | 1 | 0 |
| 2023-08 | 26 | -23.883333 | 0.266633 | 0.209877 | 109 | 0 |
| 2023-09 | 38 | -7.200000 | 0.837165 | 0.968586 | 43 | 0 |
| 2023-10 | 35 | -15.766667 | 0.618548 | 0.620879 | 0 | 0 |
| 2023-11 | 32 | -30.766667 | 0.218128 | 0.147541 | 1 | 1 |
| 2023-12 | 33 | -35.633333 | 0.172601 | 0.206186 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK5_TOL2_MAXBARS36_SB2_TP8

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 413; dates/months 218/12; PF R/price 0.506046/0.511285; Net -233.533333 R; expectancy -0.565456 R; positive months 1/12; conditional DD 245.650000 R.
Accepted 419 = CLOSED 413 + EXCLUDED 6; SKIP 0; exclusion share 0.014320; conditional FLAT closures 400; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 25 | 5.050000 | 1.192259 | 1.352941 | 7 | 1 |
| 2023-02 | 33 | -4.800000 | 0.869210 | 0.837500 | 5 | 2 |
| 2023-03 | 49 | -28.616667 | 0.473636 | 0.471774 | 4 | 1 |
| 2023-04 | 39 | -14.166667 | 0.619517 | 0.723164 | 6 | 0 |
| 2023-05 | 25 | -12.466667 | 0.537129 | 0.663934 | 7 | 1 |
| 2023-06 | 39 | -9.833333 | 0.755997 | 0.567010 | 4 | 0 |
| 2023-07 | 39 | -49.950000 | 0.009911 | 0.012552 | 1 | 0 |
| 2023-08 | 26 | -23.883333 | 0.266633 | 0.209877 | 109 | 0 |
| 2023-09 | 38 | -7.700000 | 0.825858 | 0.952880 | 43 | 0 |
| 2023-10 | 35 | -20.766667 | 0.497581 | 0.510989 | 0 | 0 |
| 2023-11 | 32 | -30.766667 | 0.218128 | 0.147541 | 1 | 1 |
| 2023-12 | 33 | -35.633333 | 0.172601 | 0.206186 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK5_TOL2_MAXBARS36_SB2_TP9

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 413; dates/months 218/12; PF R/price 0.510770/0.518194; Net -231.300000 R; expectancy -0.560048 R; positive months 1/12; conditional DD 246.483333 R.
Accepted 419 = CLOSED 413 + EXCLUDED 6; SKIP 0; exclusion share 0.014320; conditional FLAT closures 400; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 25 | 6.450000 | 1.245558 | 1.411765 | 7 | 1 |
| 2023-02 | 33 | -3.133333 | 0.914623 | 0.868750 | 5 | 2 |
| 2023-03 | 49 | -27.116667 | 0.501226 | 0.495968 | 4 | 1 |
| 2023-04 | 39 | -14.166667 | 0.619517 | 0.723164 | 6 | 0 |
| 2023-05 | 25 | -12.466667 | 0.537129 | 0.663934 | 7 | 1 |
| 2023-06 | 39 | -13.500000 | 0.665012 | 0.510309 | 4 | 0 |
| 2023-07 | 39 | -49.950000 | 0.009911 | 0.012552 | 1 | 0 |
| 2023-08 | 26 | -23.883333 | 0.266633 | 0.209877 | 109 | 0 |
| 2023-09 | 38 | -6.366667 | 0.856012 | 0.994764 | 43 | 0 |
| 2023-10 | 35 | -20.766667 | 0.497581 | 0.510989 | 0 | 0 |
| 2023-11 | 32 | -30.766667 | 0.218128 | 0.147541 | 1 | 1 |
| 2023-12 | 33 | -35.633333 | 0.172601 | 0.206186 | 0 | 0 |

## C_OPT2023_APP2_LOOKBACK5_TOL2_MAXBARS36_SB2_TP10

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 413; dates/months 218/12; PF R/price 0.506680/0.508521; Net -233.233333 R; expectancy -0.564730 R; positive months 1/12; conditional DD 251.483333 R.
Accepted 419 = CLOSED 413 + EXCLUDED 6; SKIP 0; exclusion share 0.014320; conditional FLAT closures 400; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 25 | 7.850000 | 1.298858 | 1.470588 | 7 | 1 |
| 2023-02 | 33 | -1.466667 | 0.960036 | 0.900000 | 5 | 2 |
| 2023-03 | 49 | -25.616667 | 0.528817 | 0.520161 | 4 | 1 |
| 2023-04 | 39 | -14.166667 | 0.619517 | 0.723164 | 6 | 0 |
| 2023-05 | 25 | -12.466667 | 0.537129 | 0.663934 | 7 | 1 |
| 2023-06 | 39 | -13.500000 | 0.665012 | 0.510309 | 4 | 0 |
| 2023-07 | 39 | -49.950000 | 0.009911 | 0.012552 | 1 | 0 |
| 2023-08 | 26 | -23.883333 | 0.266633 | 0.209877 | 109 | 0 |
| 2023-09 | 38 | -12.866667 | 0.709009 | 0.790576 | 43 | 0 |
| 2023-10 | 35 | -20.766667 | 0.497581 | 0.510989 | 0 | 0 |
| 2023-11 | 32 | -30.766667 | 0.218128 | 0.147541 | 1 | 1 |
| 2023-12 | 33 | -35.633333 | 0.172601 | 0.206186 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK3_TOL1_MAXBARS24_SB1_TP2

**INSUFFICIENT_SAMPLE**; failed gates: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors; sample reasons: CLOSED_BELOW_100.
CLOSED 43; dates/months 42/12; PF R/price 0.139113/0.131915; Net -49.816667 R; expectancy -1.158527 R; positive months 0/12; conditional DD 49.816667 R.
Accepted 44 = CLOSED 43 + EXCLUDED 1; SKIP 0; exclusion share 0.022727; conditional FLAT closures 30; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 1 | -1.666667 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-02 | 5 | -4.966667 | 0.118343 | 0.100000 | 5 | 0 |
| 2023-03 | 7 | -5.533333 | 0.375940 | 0.263158 | 4 | 1 |
| 2023-04 | 7 | -6.066667 | 0.315789 | 0.368421 | 6 | 0 |
| 2023-05 | 6 | -8.666667 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-06 | 3 | -1.816667 | 0.407609 | 0.416667 | 4 | 0 |
| 2023-07 | 1 | -1.500000 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 3 | -4.466667 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 3 | -4.833333 | 0.000000 | 0.000000 | 43 | 0 |
| 2023-10 | 2 | -2.833333 | 0.000000 | 0.000000 | 0 | 0 |
| 2023-11 | 4 | -5.966667 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-12 | 1 | -1.500000 | 0.000000 | 0.000000 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK3_TOL1_MAXBARS24_SB1_TP3

**INSUFFICIENT_SAMPLE**; failed gates: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors; sample reasons: CLOSED_BELOW_100.
CLOSED 43; dates/months 42/12; PF R/price 0.151786/0.153191; Net -49.083333 R; expectancy -1.141473 R; positive months 0/12; conditional DD 49.083333 R.
Accepted 44 = CLOSED 43 + EXCLUDED 1; SKIP 0; exclusion share 0.022727; conditional FLAT closures 30; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 1 | -1.666667 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-02 | 5 | -4.966667 | 0.118343 | 0.100000 | 5 | 0 |
| 2023-03 | 7 | -6.200000 | 0.300752 | 0.210526 | 4 | 1 |
| 2023-04 | 7 | -4.666667 | 0.473684 | 0.552632 | 6 | 0 |
| 2023-05 | 6 | -8.666667 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-06 | 3 | -1.816667 | 0.407609 | 0.416667 | 4 | 0 |
| 2023-07 | 1 | -1.500000 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 3 | -4.466667 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 3 | -4.833333 | 0.000000 | 0.000000 | 43 | 0 |
| 2023-10 | 2 | -2.833333 | 0.000000 | 0.000000 | 0 | 0 |
| 2023-11 | 4 | -5.966667 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-12 | 1 | -1.500000 | 0.000000 | 0.000000 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK3_TOL1_MAXBARS24_SB1_TP4

**INSUFFICIENT_SAMPLE**; failed gates: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors; sample reasons: CLOSED_BELOW_100.
CLOSED 43; dates/months 42/12; PF R/price 0.175979/0.182979; Net -47.683333 R; expectancy -1.108915 R; positive months 0/12; conditional DD 47.683333 R.
Accepted 44 = CLOSED 43 + EXCLUDED 1; SKIP 0; exclusion share 0.022727; conditional FLAT closures 30; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 1 | -1.666667 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-02 | 5 | -4.966667 | 0.118343 | 0.100000 | 5 | 0 |
| 2023-03 | 7 | -6.200000 | 0.300752 | 0.210526 | 4 | 1 |
| 2023-04 | 7 | -3.266667 | 0.631579 | 0.736842 | 6 | 0 |
| 2023-05 | 6 | -8.666667 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-06 | 3 | -1.816667 | 0.407609 | 0.416667 | 4 | 0 |
| 2023-07 | 1 | -1.500000 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 3 | -4.466667 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 3 | -4.833333 | 0.000000 | 0.000000 | 43 | 0 |
| 2023-10 | 2 | -2.833333 | 0.000000 | 0.000000 | 0 | 0 |
| 2023-11 | 4 | -5.966667 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-12 | 1 | -1.500000 | 0.000000 | 0.000000 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK3_TOL1_MAXBARS24_SB1_TP5

**INSUFFICIENT_SAMPLE**; failed gates: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors; sample reasons: CLOSED_BELOW_100.
CLOSED 43; dates/months 42/12; PF R/price 0.200173/0.212766; Net -46.283333 R; expectancy -1.076357 R; positive months 0/12; conditional DD 46.283333 R.
Accepted 44 = CLOSED 43 + EXCLUDED 1; SKIP 0; exclusion share 0.022727; conditional FLAT closures 30; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 1 | -1.666667 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-02 | 5 | -4.966667 | 0.118343 | 0.100000 | 5 | 0 |
| 2023-03 | 7 | -6.200000 | 0.300752 | 0.210526 | 4 | 1 |
| 2023-04 | 7 | -1.866667 | 0.789474 | 0.921053 | 6 | 0 |
| 2023-05 | 6 | -8.666667 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-06 | 3 | -1.816667 | 0.407609 | 0.416667 | 4 | 0 |
| 2023-07 | 1 | -1.500000 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 3 | -4.466667 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 3 | -4.833333 | 0.000000 | 0.000000 | 43 | 0 |
| 2023-10 | 2 | -2.833333 | 0.000000 | 0.000000 | 0 | 0 |
| 2023-11 | 4 | -5.966667 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-12 | 1 | -1.500000 | 0.000000 | 0.000000 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK3_TOL1_MAXBARS24_SB1_TP6

**INSUFFICIENT_SAMPLE**; failed gates: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors; sample reasons: CLOSED_BELOW_100.
CLOSED 43; dates/months 42/12; PF R/price 0.186348/0.195745; Net -47.083333 R; expectancy -1.094961 R; positive months 0/12; conditional DD 47.083333 R.
Accepted 44 = CLOSED 43 + EXCLUDED 1; SKIP 0; exclusion share 0.022727; conditional FLAT closures 30; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 1 | -1.666667 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-02 | 5 | -4.966667 | 0.118343 | 0.100000 | 5 | 0 |
| 2023-03 | 7 | -6.200000 | 0.300752 | 0.210526 | 4 | 1 |
| 2023-04 | 7 | -2.666667 | 0.699248 | 0.815789 | 6 | 0 |
| 2023-05 | 6 | -8.666667 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-06 | 3 | -1.816667 | 0.407609 | 0.416667 | 4 | 0 |
| 2023-07 | 1 | -1.500000 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 3 | -4.466667 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 3 | -4.833333 | 0.000000 | 0.000000 | 43 | 0 |
| 2023-10 | 2 | -2.833333 | 0.000000 | 0.000000 | 0 | 0 |
| 2023-11 | 4 | -5.966667 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-12 | 1 | -1.500000 | 0.000000 | 0.000000 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK3_TOL1_MAXBARS24_SB1_TP7

**INSUFFICIENT_SAMPLE**; failed gates: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors; sample reasons: CLOSED_BELOW_100.
CLOSED 43; dates/months 42/12; PF R/price 0.186348/0.195745; Net -47.083333 R; expectancy -1.094961 R; positive months 0/12; conditional DD 47.083333 R.
Accepted 44 = CLOSED 43 + EXCLUDED 1; SKIP 0; exclusion share 0.022727; conditional FLAT closures 30; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 1 | -1.666667 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-02 | 5 | -4.966667 | 0.118343 | 0.100000 | 5 | 0 |
| 2023-03 | 7 | -6.200000 | 0.300752 | 0.210526 | 4 | 1 |
| 2023-04 | 7 | -2.666667 | 0.699248 | 0.815789 | 6 | 0 |
| 2023-05 | 6 | -8.666667 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-06 | 3 | -1.816667 | 0.407609 | 0.416667 | 4 | 0 |
| 2023-07 | 1 | -1.500000 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 3 | -4.466667 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 3 | -4.833333 | 0.000000 | 0.000000 | 43 | 0 |
| 2023-10 | 2 | -2.833333 | 0.000000 | 0.000000 | 0 | 0 |
| 2023-11 | 4 | -5.966667 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-12 | 1 | -1.500000 | 0.000000 | 0.000000 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK3_TOL1_MAXBARS24_SB1_TP8

**INSUFFICIENT_SAMPLE**; failed gates: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors; sample reasons: CLOSED_BELOW_100.
CLOSED 43; dates/months 42/12; PF R/price 0.186348/0.195745; Net -47.083333 R; expectancy -1.094961 R; positive months 0/12; conditional DD 47.083333 R.
Accepted 44 = CLOSED 43 + EXCLUDED 1; SKIP 0; exclusion share 0.022727; conditional FLAT closures 30; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 1 | -1.666667 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-02 | 5 | -4.966667 | 0.118343 | 0.100000 | 5 | 0 |
| 2023-03 | 7 | -6.200000 | 0.300752 | 0.210526 | 4 | 1 |
| 2023-04 | 7 | -2.666667 | 0.699248 | 0.815789 | 6 | 0 |
| 2023-05 | 6 | -8.666667 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-06 | 3 | -1.816667 | 0.407609 | 0.416667 | 4 | 0 |
| 2023-07 | 1 | -1.500000 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 3 | -4.466667 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 3 | -4.833333 | 0.000000 | 0.000000 | 43 | 0 |
| 2023-10 | 2 | -2.833333 | 0.000000 | 0.000000 | 0 | 0 |
| 2023-11 | 4 | -5.966667 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-12 | 1 | -1.500000 | 0.000000 | 0.000000 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK3_TOL1_MAXBARS24_SB1_TP9

**INSUFFICIENT_SAMPLE**; failed gates: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors; sample reasons: CLOSED_BELOW_100.
CLOSED 43; dates/months 42/12; PF R/price 0.186348/0.195745; Net -47.083333 R; expectancy -1.094961 R; positive months 0/12; conditional DD 47.083333 R.
Accepted 44 = CLOSED 43 + EXCLUDED 1; SKIP 0; exclusion share 0.022727; conditional FLAT closures 30; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 1 | -1.666667 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-02 | 5 | -4.966667 | 0.118343 | 0.100000 | 5 | 0 |
| 2023-03 | 7 | -6.200000 | 0.300752 | 0.210526 | 4 | 1 |
| 2023-04 | 7 | -2.666667 | 0.699248 | 0.815789 | 6 | 0 |
| 2023-05 | 6 | -8.666667 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-06 | 3 | -1.816667 | 0.407609 | 0.416667 | 4 | 0 |
| 2023-07 | 1 | -1.500000 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 3 | -4.466667 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 3 | -4.833333 | 0.000000 | 0.000000 | 43 | 0 |
| 2023-10 | 2 | -2.833333 | 0.000000 | 0.000000 | 0 | 0 |
| 2023-11 | 4 | -5.966667 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-12 | 1 | -1.500000 | 0.000000 | 0.000000 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK3_TOL1_MAXBARS24_SB1_TP10

**INSUFFICIENT_SAMPLE**; failed gates: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors; sample reasons: CLOSED_BELOW_100.
CLOSED 43; dates/months 42/12; PF R/price 0.186348/0.195745; Net -47.083333 R; expectancy -1.094961 R; positive months 0/12; conditional DD 47.083333 R.
Accepted 44 = CLOSED 43 + EXCLUDED 1; SKIP 0; exclusion share 0.022727; conditional FLAT closures 30; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 1 | -1.666667 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-02 | 5 | -4.966667 | 0.118343 | 0.100000 | 5 | 0 |
| 2023-03 | 7 | -6.200000 | 0.300752 | 0.210526 | 4 | 1 |
| 2023-04 | 7 | -2.666667 | 0.699248 | 0.815789 | 6 | 0 |
| 2023-05 | 6 | -8.666667 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-06 | 3 | -1.816667 | 0.407609 | 0.416667 | 4 | 0 |
| 2023-07 | 1 | -1.500000 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 3 | -4.466667 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 3 | -4.833333 | 0.000000 | 0.000000 | 43 | 0 |
| 2023-10 | 2 | -2.833333 | 0.000000 | 0.000000 | 0 | 0 |
| 2023-11 | 4 | -5.966667 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-12 | 1 | -1.500000 | 0.000000 | 0.000000 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK3_TOL1_MAXBARS24_SB2_TP2

**INSUFFICIENT_SAMPLE**; failed gates: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: CLOSED_BELOW_100.
CLOSED 53; dates/months 49/12; PF R/price 0.268711/0.300000; Net -46.900000 R; expectancy -0.884906 R; positive months 1/12; conditional DD 46.900000 R.
Accepted 54 = CLOSED 53 + EXCLUDED 1; SKIP 0; exclusion share 0.018519; conditional FLAT closures 35; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 2 | -3.166667 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-02 | 7 | -3.700000 | 0.471429 | 0.615385 | 5 | 0 |
| 2023-03 | 9 | -4.433333 | 0.566775 | 0.553191 | 4 | 1 |
| 2023-04 | 7 | 1.566667 | 1.281437 | 1.379310 | 6 | 0 |
| 2023-05 | 6 | -7.833333 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-06 | 4 | -3.500000 | 0.222222 | 0.263158 | 4 | 0 |
| 2023-07 | 4 | -6.400000 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 3 | -4.000000 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 3 | -4.400000 | 0.000000 | 0.000000 | 43 | 0 |
| 2023-10 | 3 | -4.066667 | 0.000000 | 0.000000 | 0 | 0 |
| 2023-11 | 4 | -5.566667 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-12 | 1 | -1.400000 | 0.000000 | 0.000000 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK3_TOL1_MAXBARS24_SB2_TP3

**INSUFFICIENT_SAMPLE**; failed gates: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors; sample reasons: CLOSED_BELOW_100.
CLOSED 52; dates/months 48/12; PF R/price 0.178131/0.207483; Net -53.366667 R; expectancy -1.026282 R; positive months 0/12; conditional DD 53.366667 R.
Accepted 54 = CLOSED 52 + EXCLUDED 2; SKIP 0; exclusion share 0.037037; conditional FLAT closures 47; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 2 | -3.166667 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-02 | 6 | -6.500000 | 0.071429 | 0.076923 | 5 | 1 |
| 2023-03 | 9 | -5.833333 | 0.429967 | 0.425532 | 4 | 1 |
| 2023-04 | 7 | -0.700000 | 0.890052 | 1.030303 | 6 | 0 |
| 2023-05 | 6 | -7.833333 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-06 | 4 | -3.500000 | 0.222222 | 0.263158 | 4 | 0 |
| 2023-07 | 4 | -6.400000 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 3 | -4.000000 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 3 | -4.400000 | 0.000000 | 0.000000 | 43 | 0 |
| 2023-10 | 3 | -4.066667 | 0.000000 | 0.000000 | 0 | 0 |
| 2023-11 | 4 | -5.566667 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-12 | 1 | -1.400000 | 0.000000 | 0.000000 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK3_TOL1_MAXBARS24_SB2_TP4

**INSUFFICIENT_SAMPLE**; failed gates: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors; sample reasons: CLOSED_BELOW_100.
CLOSED 52; dates/months 48/12; PF R/price 0.198665/0.234694; Net -52.033333 R; expectancy -1.000641 R; positive months 1/12; conditional DD 52.033333 R.
Accepted 54 = CLOSED 52 + EXCLUDED 2; SKIP 0; exclusion share 0.037037; conditional FLAT closures 47; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 2 | -3.166667 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-02 | 6 | -6.500000 | 0.071429 | 0.076923 | 5 | 1 |
| 2023-03 | 9 | -5.833333 | 0.429967 | 0.425532 | 4 | 1 |
| 2023-04 | 7 | 0.633333 | 1.099476 | 1.272727 | 6 | 0 |
| 2023-05 | 6 | -7.833333 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-06 | 4 | -3.500000 | 0.222222 | 0.263158 | 4 | 0 |
| 2023-07 | 4 | -6.400000 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 3 | -4.000000 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 3 | -4.400000 | 0.000000 | 0.000000 | 43 | 0 |
| 2023-10 | 3 | -4.066667 | 0.000000 | 0.000000 | 0 | 0 |
| 2023-11 | 4 | -5.566667 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-12 | 1 | -1.400000 | 0.000000 | 0.000000 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK3_TOL1_MAXBARS24_SB2_TP5

**INSUFFICIENT_SAMPLE**; failed gates: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors; sample reasons: CLOSED_BELOW_100.
CLOSED 52; dates/months 48/12; PF R/price 0.196099/0.231293; Net -52.200000 R; expectancy -1.003846 R; positive months 1/12; conditional DD 52.200000 R.
Accepted 54 = CLOSED 52 + EXCLUDED 2; SKIP 0; exclusion share 0.037037; conditional FLAT closures 47; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 2 | -3.166667 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-02 | 6 | -6.500000 | 0.071429 | 0.076923 | 5 | 1 |
| 2023-03 | 9 | -5.833333 | 0.429967 | 0.425532 | 4 | 1 |
| 2023-04 | 7 | 0.466667 | 1.073298 | 1.242424 | 6 | 0 |
| 2023-05 | 6 | -7.833333 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-06 | 4 | -3.500000 | 0.222222 | 0.263158 | 4 | 0 |
| 2023-07 | 4 | -6.400000 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 3 | -4.000000 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 3 | -4.400000 | 0.000000 | 0.000000 | 43 | 0 |
| 2023-10 | 3 | -4.066667 | 0.000000 | 0.000000 | 0 | 0 |
| 2023-11 | 4 | -5.566667 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-12 | 1 | -1.400000 | 0.000000 | 0.000000 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK3_TOL1_MAXBARS24_SB2_TP6

**INSUFFICIENT_SAMPLE**; failed gates: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors; sample reasons: CLOSED_BELOW_100.
CLOSED 52; dates/months 48/12; PF R/price 0.196099/0.231293; Net -52.200000 R; expectancy -1.003846 R; positive months 1/12; conditional DD 52.200000 R.
Accepted 54 = CLOSED 52 + EXCLUDED 2; SKIP 0; exclusion share 0.037037; conditional FLAT closures 47; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 2 | -3.166667 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-02 | 6 | -6.500000 | 0.071429 | 0.076923 | 5 | 1 |
| 2023-03 | 9 | -5.833333 | 0.429967 | 0.425532 | 4 | 1 |
| 2023-04 | 7 | 0.466667 | 1.073298 | 1.242424 | 6 | 0 |
| 2023-05 | 6 | -7.833333 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-06 | 4 | -3.500000 | 0.222222 | 0.263158 | 4 | 0 |
| 2023-07 | 4 | -6.400000 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 3 | -4.000000 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 3 | -4.400000 | 0.000000 | 0.000000 | 43 | 0 |
| 2023-10 | 3 | -4.066667 | 0.000000 | 0.000000 | 0 | 0 |
| 2023-11 | 4 | -5.566667 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-12 | 1 | -1.400000 | 0.000000 | 0.000000 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK3_TOL1_MAXBARS24_SB2_TP7

**INSUFFICIENT_SAMPLE**; failed gates: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors; sample reasons: CLOSED_BELOW_100.
CLOSED 52; dates/months 48/12; PF R/price 0.196099/0.231293; Net -52.200000 R; expectancy -1.003846 R; positive months 1/12; conditional DD 52.200000 R.
Accepted 54 = CLOSED 52 + EXCLUDED 2; SKIP 0; exclusion share 0.037037; conditional FLAT closures 47; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 2 | -3.166667 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-02 | 6 | -6.500000 | 0.071429 | 0.076923 | 5 | 1 |
| 2023-03 | 9 | -5.833333 | 0.429967 | 0.425532 | 4 | 1 |
| 2023-04 | 7 | 0.466667 | 1.073298 | 1.242424 | 6 | 0 |
| 2023-05 | 6 | -7.833333 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-06 | 4 | -3.500000 | 0.222222 | 0.263158 | 4 | 0 |
| 2023-07 | 4 | -6.400000 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 3 | -4.000000 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 3 | -4.400000 | 0.000000 | 0.000000 | 43 | 0 |
| 2023-10 | 3 | -4.066667 | 0.000000 | 0.000000 | 0 | 0 |
| 2023-11 | 4 | -5.566667 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-12 | 1 | -1.400000 | 0.000000 | 0.000000 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK3_TOL1_MAXBARS24_SB2_TP8

**INSUFFICIENT_SAMPLE**; failed gates: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors; sample reasons: CLOSED_BELOW_100.
CLOSED 52; dates/months 48/12; PF R/price 0.196099/0.231293; Net -52.200000 R; expectancy -1.003846 R; positive months 1/12; conditional DD 52.200000 R.
Accepted 54 = CLOSED 52 + EXCLUDED 2; SKIP 0; exclusion share 0.037037; conditional FLAT closures 47; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 2 | -3.166667 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-02 | 6 | -6.500000 | 0.071429 | 0.076923 | 5 | 1 |
| 2023-03 | 9 | -5.833333 | 0.429967 | 0.425532 | 4 | 1 |
| 2023-04 | 7 | 0.466667 | 1.073298 | 1.242424 | 6 | 0 |
| 2023-05 | 6 | -7.833333 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-06 | 4 | -3.500000 | 0.222222 | 0.263158 | 4 | 0 |
| 2023-07 | 4 | -6.400000 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 3 | -4.000000 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 3 | -4.400000 | 0.000000 | 0.000000 | 43 | 0 |
| 2023-10 | 3 | -4.066667 | 0.000000 | 0.000000 | 0 | 0 |
| 2023-11 | 4 | -5.566667 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-12 | 1 | -1.400000 | 0.000000 | 0.000000 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK3_TOL1_MAXBARS24_SB2_TP9

**INSUFFICIENT_SAMPLE**; failed gates: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors; sample reasons: CLOSED_BELOW_100.
CLOSED 52; dates/months 48/12; PF R/price 0.196099/0.231293; Net -52.200000 R; expectancy -1.003846 R; positive months 1/12; conditional DD 52.200000 R.
Accepted 54 = CLOSED 52 + EXCLUDED 2; SKIP 0; exclusion share 0.037037; conditional FLAT closures 47; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 2 | -3.166667 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-02 | 6 | -6.500000 | 0.071429 | 0.076923 | 5 | 1 |
| 2023-03 | 9 | -5.833333 | 0.429967 | 0.425532 | 4 | 1 |
| 2023-04 | 7 | 0.466667 | 1.073298 | 1.242424 | 6 | 0 |
| 2023-05 | 6 | -7.833333 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-06 | 4 | -3.500000 | 0.222222 | 0.263158 | 4 | 0 |
| 2023-07 | 4 | -6.400000 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 3 | -4.000000 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 3 | -4.400000 | 0.000000 | 0.000000 | 43 | 0 |
| 2023-10 | 3 | -4.066667 | 0.000000 | 0.000000 | 0 | 0 |
| 2023-11 | 4 | -5.566667 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-12 | 1 | -1.400000 | 0.000000 | 0.000000 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK3_TOL1_MAXBARS24_SB2_TP10

**INSUFFICIENT_SAMPLE**; failed gates: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors; sample reasons: CLOSED_BELOW_100.
CLOSED 52; dates/months 48/12; PF R/price 0.196099/0.231293; Net -52.200000 R; expectancy -1.003846 R; positive months 1/12; conditional DD 52.200000 R.
Accepted 54 = CLOSED 52 + EXCLUDED 2; SKIP 0; exclusion share 0.037037; conditional FLAT closures 47; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 2 | -3.166667 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-02 | 6 | -6.500000 | 0.071429 | 0.076923 | 5 | 1 |
| 2023-03 | 9 | -5.833333 | 0.429967 | 0.425532 | 4 | 1 |
| 2023-04 | 7 | 0.466667 | 1.073298 | 1.242424 | 6 | 0 |
| 2023-05 | 6 | -7.833333 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-06 | 4 | -3.500000 | 0.222222 | 0.263158 | 4 | 0 |
| 2023-07 | 4 | -6.400000 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 3 | -4.000000 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 3 | -4.400000 | 0.000000 | 0.000000 | 43 | 0 |
| 2023-10 | 3 | -4.066667 | 0.000000 | 0.000000 | 0 | 0 |
| 2023-11 | 4 | -5.566667 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-12 | 1 | -1.400000 | 0.000000 | 0.000000 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK3_TOL1_MAXBARS36_SB1_TP2

**INSUFFICIENT_SAMPLE**; failed gates: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors; sample reasons: CLOSED_BELOW_100.
CLOSED 46; dates/months 44/12; PF R/price 0.097870/0.084677; Net -55.766667 R; expectancy -1.212319 R; positive months 0/12; conditional DD 55.766667 R.
Accepted 47 = CLOSED 46 + EXCLUDED 1; SKIP 0; exclusion share 0.021277; conditional FLAT closures 32; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 1 | -1.666667 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-02 | 5 | -4.966667 | 0.118343 | 0.100000 | 5 | 0 |
| 2023-03 | 8 | -7.033333 | 0.321543 | 0.227273 | 4 | 1 |
| 2023-04 | 7 | -7.900000 | 0.091954 | 0.102564 | 6 | 0 |
| 2023-05 | 6 | -8.016667 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-06 | 4 | -3.316667 | 0.273723 | 0.277778 | 4 | 0 |
| 2023-07 | 1 | -1.500000 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 3 | -4.733333 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 4 | -6.333333 | 0.000000 | 0.000000 | 43 | 0 |
| 2023-10 | 2 | -2.833333 | 0.000000 | 0.000000 | 0 | 0 |
| 2023-11 | 4 | -5.966667 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-12 | 1 | -1.500000 | 0.000000 | 0.000000 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK3_TOL1_MAXBARS36_SB1_TP3

**INSUFFICIENT_SAMPLE**; failed gates: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors; sample reasons: CLOSED_BELOW_100.
CLOSED 46; dates/months 44/12; PF R/price 0.087085/0.076613; Net -56.433333 R; expectancy -1.226812 R; positive months 0/12; conditional DD 56.433333 R.
Accepted 47 = CLOSED 46 + EXCLUDED 1; SKIP 0; exclusion share 0.021277; conditional FLAT closures 32; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 1 | -1.666667 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-02 | 5 | -4.966667 | 0.118343 | 0.100000 | 5 | 0 |
| 2023-03 | 8 | -7.700000 | 0.257235 | 0.181818 | 4 | 1 |
| 2023-04 | 7 | -7.900000 | 0.091954 | 0.102564 | 6 | 0 |
| 2023-05 | 6 | -8.016667 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-06 | 4 | -3.316667 | 0.273723 | 0.277778 | 4 | 0 |
| 2023-07 | 1 | -1.500000 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 3 | -4.733333 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 4 | -6.333333 | 0.000000 | 0.000000 | 43 | 0 |
| 2023-10 | 2 | -2.833333 | 0.000000 | 0.000000 | 0 | 0 |
| 2023-11 | 4 | -5.966667 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-12 | 1 | -1.500000 | 0.000000 | 0.000000 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK3_TOL1_MAXBARS36_SB1_TP4

**INSUFFICIENT_SAMPLE**; failed gates: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors; sample reasons: CLOSED_BELOW_100.
CLOSED 46; dates/months 44/12; PF R/price 0.087085/0.076613; Net -56.433333 R; expectancy -1.226812 R; positive months 0/12; conditional DD 56.433333 R.
Accepted 47 = CLOSED 46 + EXCLUDED 1; SKIP 0; exclusion share 0.021277; conditional FLAT closures 32; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 1 | -1.666667 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-02 | 5 | -4.966667 | 0.118343 | 0.100000 | 5 | 0 |
| 2023-03 | 8 | -7.700000 | 0.257235 | 0.181818 | 4 | 1 |
| 2023-04 | 7 | -7.900000 | 0.091954 | 0.102564 | 6 | 0 |
| 2023-05 | 6 | -8.016667 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-06 | 4 | -3.316667 | 0.273723 | 0.277778 | 4 | 0 |
| 2023-07 | 1 | -1.500000 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 3 | -4.733333 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 4 | -6.333333 | 0.000000 | 0.000000 | 43 | 0 |
| 2023-10 | 2 | -2.833333 | 0.000000 | 0.000000 | 0 | 0 |
| 2023-11 | 4 | -5.966667 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-12 | 1 | -1.500000 | 0.000000 | 0.000000 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK3_TOL1_MAXBARS36_SB1_TP5

**INSUFFICIENT_SAMPLE**; failed gates: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors; sample reasons: CLOSED_BELOW_100.
CLOSED 46; dates/months 44/12; PF R/price 0.087085/0.076613; Net -56.433333 R; expectancy -1.226812 R; positive months 0/12; conditional DD 56.433333 R.
Accepted 47 = CLOSED 46 + EXCLUDED 1; SKIP 0; exclusion share 0.021277; conditional FLAT closures 32; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 1 | -1.666667 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-02 | 5 | -4.966667 | 0.118343 | 0.100000 | 5 | 0 |
| 2023-03 | 8 | -7.700000 | 0.257235 | 0.181818 | 4 | 1 |
| 2023-04 | 7 | -7.900000 | 0.091954 | 0.102564 | 6 | 0 |
| 2023-05 | 6 | -8.016667 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-06 | 4 | -3.316667 | 0.273723 | 0.277778 | 4 | 0 |
| 2023-07 | 1 | -1.500000 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 3 | -4.733333 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 4 | -6.333333 | 0.000000 | 0.000000 | 43 | 0 |
| 2023-10 | 2 | -2.833333 | 0.000000 | 0.000000 | 0 | 0 |
| 2023-11 | 4 | -5.966667 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-12 | 1 | -1.500000 | 0.000000 | 0.000000 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK3_TOL1_MAXBARS36_SB1_TP6

**INSUFFICIENT_SAMPLE**; failed gates: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors; sample reasons: CLOSED_BELOW_100.
CLOSED 46; dates/months 44/12; PF R/price 0.087085/0.076613; Net -56.433333 R; expectancy -1.226812 R; positive months 0/12; conditional DD 56.433333 R.
Accepted 47 = CLOSED 46 + EXCLUDED 1; SKIP 0; exclusion share 0.021277; conditional FLAT closures 32; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 1 | -1.666667 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-02 | 5 | -4.966667 | 0.118343 | 0.100000 | 5 | 0 |
| 2023-03 | 8 | -7.700000 | 0.257235 | 0.181818 | 4 | 1 |
| 2023-04 | 7 | -7.900000 | 0.091954 | 0.102564 | 6 | 0 |
| 2023-05 | 6 | -8.016667 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-06 | 4 | -3.316667 | 0.273723 | 0.277778 | 4 | 0 |
| 2023-07 | 1 | -1.500000 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 3 | -4.733333 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 4 | -6.333333 | 0.000000 | 0.000000 | 43 | 0 |
| 2023-10 | 2 | -2.833333 | 0.000000 | 0.000000 | 0 | 0 |
| 2023-11 | 4 | -5.966667 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-12 | 1 | -1.500000 | 0.000000 | 0.000000 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK3_TOL1_MAXBARS36_SB1_TP7

**INSUFFICIENT_SAMPLE**; failed gates: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors; sample reasons: CLOSED_BELOW_100.
CLOSED 46; dates/months 44/12; PF R/price 0.087085/0.076613; Net -56.433333 R; expectancy -1.226812 R; positive months 0/12; conditional DD 56.433333 R.
Accepted 47 = CLOSED 46 + EXCLUDED 1; SKIP 0; exclusion share 0.021277; conditional FLAT closures 32; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 1 | -1.666667 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-02 | 5 | -4.966667 | 0.118343 | 0.100000 | 5 | 0 |
| 2023-03 | 8 | -7.700000 | 0.257235 | 0.181818 | 4 | 1 |
| 2023-04 | 7 | -7.900000 | 0.091954 | 0.102564 | 6 | 0 |
| 2023-05 | 6 | -8.016667 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-06 | 4 | -3.316667 | 0.273723 | 0.277778 | 4 | 0 |
| 2023-07 | 1 | -1.500000 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 3 | -4.733333 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 4 | -6.333333 | 0.000000 | 0.000000 | 43 | 0 |
| 2023-10 | 2 | -2.833333 | 0.000000 | 0.000000 | 0 | 0 |
| 2023-11 | 4 | -5.966667 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-12 | 1 | -1.500000 | 0.000000 | 0.000000 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK3_TOL1_MAXBARS36_SB1_TP8

**INSUFFICIENT_SAMPLE**; failed gates: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors; sample reasons: CLOSED_BELOW_100.
CLOSED 46; dates/months 44/12; PF R/price 0.087085/0.076613; Net -56.433333 R; expectancy -1.226812 R; positive months 0/12; conditional DD 56.433333 R.
Accepted 47 = CLOSED 46 + EXCLUDED 1; SKIP 0; exclusion share 0.021277; conditional FLAT closures 32; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 1 | -1.666667 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-02 | 5 | -4.966667 | 0.118343 | 0.100000 | 5 | 0 |
| 2023-03 | 8 | -7.700000 | 0.257235 | 0.181818 | 4 | 1 |
| 2023-04 | 7 | -7.900000 | 0.091954 | 0.102564 | 6 | 0 |
| 2023-05 | 6 | -8.016667 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-06 | 4 | -3.316667 | 0.273723 | 0.277778 | 4 | 0 |
| 2023-07 | 1 | -1.500000 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 3 | -4.733333 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 4 | -6.333333 | 0.000000 | 0.000000 | 43 | 0 |
| 2023-10 | 2 | -2.833333 | 0.000000 | 0.000000 | 0 | 0 |
| 2023-11 | 4 | -5.966667 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-12 | 1 | -1.500000 | 0.000000 | 0.000000 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK3_TOL1_MAXBARS36_SB1_TP9

**INSUFFICIENT_SAMPLE**; failed gates: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors; sample reasons: CLOSED_BELOW_100.
CLOSED 46; dates/months 44/12; PF R/price 0.087085/0.076613; Net -56.433333 R; expectancy -1.226812 R; positive months 0/12; conditional DD 56.433333 R.
Accepted 47 = CLOSED 46 + EXCLUDED 1; SKIP 0; exclusion share 0.021277; conditional FLAT closures 32; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 1 | -1.666667 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-02 | 5 | -4.966667 | 0.118343 | 0.100000 | 5 | 0 |
| 2023-03 | 8 | -7.700000 | 0.257235 | 0.181818 | 4 | 1 |
| 2023-04 | 7 | -7.900000 | 0.091954 | 0.102564 | 6 | 0 |
| 2023-05 | 6 | -8.016667 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-06 | 4 | -3.316667 | 0.273723 | 0.277778 | 4 | 0 |
| 2023-07 | 1 | -1.500000 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 3 | -4.733333 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 4 | -6.333333 | 0.000000 | 0.000000 | 43 | 0 |
| 2023-10 | 2 | -2.833333 | 0.000000 | 0.000000 | 0 | 0 |
| 2023-11 | 4 | -5.966667 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-12 | 1 | -1.500000 | 0.000000 | 0.000000 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK3_TOL1_MAXBARS36_SB1_TP10

**INSUFFICIENT_SAMPLE**; failed gates: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors; sample reasons: CLOSED_BELOW_100.
CLOSED 46; dates/months 44/12; PF R/price 0.087085/0.076613; Net -56.433333 R; expectancy -1.226812 R; positive months 0/12; conditional DD 56.433333 R.
Accepted 47 = CLOSED 46 + EXCLUDED 1; SKIP 0; exclusion share 0.021277; conditional FLAT closures 32; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 1 | -1.666667 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-02 | 5 | -4.966667 | 0.118343 | 0.100000 | 5 | 0 |
| 2023-03 | 8 | -7.700000 | 0.257235 | 0.181818 | 4 | 1 |
| 2023-04 | 7 | -7.900000 | 0.091954 | 0.102564 | 6 | 0 |
| 2023-05 | 6 | -8.016667 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-06 | 4 | -3.316667 | 0.273723 | 0.277778 | 4 | 0 |
| 2023-07 | 1 | -1.500000 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 3 | -4.733333 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 4 | -6.333333 | 0.000000 | 0.000000 | 43 | 0 |
| 2023-10 | 2 | -2.833333 | 0.000000 | 0.000000 | 0 | 0 |
| 2023-11 | 4 | -5.966667 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-12 | 1 | -1.500000 | 0.000000 | 0.000000 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK3_TOL1_MAXBARS36_SB2_TP2

**INSUFFICIENT_SAMPLE**; failed gates: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: CLOSED_BELOW_100.
CLOSED 55; dates/months 51/12; PF R/price 0.235203/0.255102; Net -49.533333 R; expectancy -0.900606 R; positive months 1/12; conditional DD 49.533333 R.
Accepted 56 = CLOSED 55 + EXCLUDED 1; SKIP 0; exclusion share 0.017857; conditional FLAT closures 36; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 3 | -4.833333 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-02 | 6 | -2.033333 | 0.618750 | 0.761905 | 5 | 0 |
| 2023-03 | 10 | -5.833333 | 0.498567 | 0.481481 | 4 | 1 |
| 2023-04 | 6 | 1.066667 | 1.262295 | 1.217391 | 6 | 0 |
| 2023-05 | 6 | -7.100000 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-06 | 6 | -4.900000 | 0.169492 | 0.192308 | 4 | 0 |
| 2023-07 | 3 | -4.733333 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 3 | -4.333333 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 4 | -5.800000 | 0.000000 | 0.000000 | 43 | 0 |
| 2023-10 | 3 | -4.066667 | 0.000000 | 0.000000 | 0 | 0 |
| 2023-11 | 4 | -5.566667 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-12 | 1 | -1.400000 | 0.000000 | 0.000000 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK3_TOL1_MAXBARS36_SB2_TP3

**INSUFFICIENT_SAMPLE**; failed gates: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors; sample reasons: CLOSED_BELOW_100.
CLOSED 54; dates/months 50/12; PF R/price 0.125572/0.137584; Net -57.333333 R; expectancy -1.061728 R; positive months 0/12; conditional DD 57.333333 R.
Accepted 56 = CLOSED 54 + EXCLUDED 2; SKIP 0; exclusion share 0.035714; conditional FLAT closures 48; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 3 | -4.833333 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-02 | 5 | -4.833333 | 0.093750 | 0.095238 | 5 | 1 |
| 2023-03 | 10 | -7.233333 | 0.378223 | 0.370370 | 4 | 1 |
| 2023-04 | 6 | -2.533333 | 0.479452 | 0.518519 | 6 | 0 |
| 2023-05 | 6 | -7.100000 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-06 | 6 | -4.900000 | 0.169492 | 0.192308 | 4 | 0 |
| 2023-07 | 3 | -4.733333 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 3 | -4.333333 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 4 | -5.800000 | 0.000000 | 0.000000 | 43 | 0 |
| 2023-10 | 3 | -4.066667 | 0.000000 | 0.000000 | 0 | 0 |
| 2023-11 | 4 | -5.566667 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-12 | 1 | -1.400000 | 0.000000 | 0.000000 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK3_TOL1_MAXBARS36_SB2_TP4

**INSUFFICIENT_SAMPLE**; failed gates: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors; sample reasons: CLOSED_BELOW_100.
CLOSED 54; dates/months 50/12; PF R/price 0.125572/0.137584; Net -57.333333 R; expectancy -1.061728 R; positive months 0/12; conditional DD 57.333333 R.
Accepted 56 = CLOSED 54 + EXCLUDED 2; SKIP 0; exclusion share 0.035714; conditional FLAT closures 48; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 3 | -4.833333 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-02 | 5 | -4.833333 | 0.093750 | 0.095238 | 5 | 1 |
| 2023-03 | 10 | -7.233333 | 0.378223 | 0.370370 | 4 | 1 |
| 2023-04 | 6 | -2.533333 | 0.479452 | 0.518519 | 6 | 0 |
| 2023-05 | 6 | -7.100000 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-06 | 6 | -4.900000 | 0.169492 | 0.192308 | 4 | 0 |
| 2023-07 | 3 | -4.733333 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 3 | -4.333333 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 4 | -5.800000 | 0.000000 | 0.000000 | 43 | 0 |
| 2023-10 | 3 | -4.066667 | 0.000000 | 0.000000 | 0 | 0 |
| 2023-11 | 4 | -5.566667 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-12 | 1 | -1.400000 | 0.000000 | 0.000000 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK3_TOL1_MAXBARS36_SB2_TP5

**INSUFFICIENT_SAMPLE**; failed gates: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors; sample reasons: CLOSED_BELOW_100.
CLOSED 54; dates/months 50/12; PF R/price 0.125572/0.137584; Net -57.333333 R; expectancy -1.061728 R; positive months 0/12; conditional DD 57.333333 R.
Accepted 56 = CLOSED 54 + EXCLUDED 2; SKIP 0; exclusion share 0.035714; conditional FLAT closures 48; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 3 | -4.833333 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-02 | 5 | -4.833333 | 0.093750 | 0.095238 | 5 | 1 |
| 2023-03 | 10 | -7.233333 | 0.378223 | 0.370370 | 4 | 1 |
| 2023-04 | 6 | -2.533333 | 0.479452 | 0.518519 | 6 | 0 |
| 2023-05 | 6 | -7.100000 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-06 | 6 | -4.900000 | 0.169492 | 0.192308 | 4 | 0 |
| 2023-07 | 3 | -4.733333 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 3 | -4.333333 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 4 | -5.800000 | 0.000000 | 0.000000 | 43 | 0 |
| 2023-10 | 3 | -4.066667 | 0.000000 | 0.000000 | 0 | 0 |
| 2023-11 | 4 | -5.566667 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-12 | 1 | -1.400000 | 0.000000 | 0.000000 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK3_TOL1_MAXBARS36_SB2_TP6

**INSUFFICIENT_SAMPLE**; failed gates: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors; sample reasons: CLOSED_BELOW_100.
CLOSED 54; dates/months 50/12; PF R/price 0.125572/0.137584; Net -57.333333 R; expectancy -1.061728 R; positive months 0/12; conditional DD 57.333333 R.
Accepted 56 = CLOSED 54 + EXCLUDED 2; SKIP 0; exclusion share 0.035714; conditional FLAT closures 48; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 3 | -4.833333 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-02 | 5 | -4.833333 | 0.093750 | 0.095238 | 5 | 1 |
| 2023-03 | 10 | -7.233333 | 0.378223 | 0.370370 | 4 | 1 |
| 2023-04 | 6 | -2.533333 | 0.479452 | 0.518519 | 6 | 0 |
| 2023-05 | 6 | -7.100000 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-06 | 6 | -4.900000 | 0.169492 | 0.192308 | 4 | 0 |
| 2023-07 | 3 | -4.733333 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 3 | -4.333333 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 4 | -5.800000 | 0.000000 | 0.000000 | 43 | 0 |
| 2023-10 | 3 | -4.066667 | 0.000000 | 0.000000 | 0 | 0 |
| 2023-11 | 4 | -5.566667 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-12 | 1 | -1.400000 | 0.000000 | 0.000000 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK3_TOL1_MAXBARS36_SB2_TP7

**INSUFFICIENT_SAMPLE**; failed gates: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors; sample reasons: CLOSED_BELOW_100.
CLOSED 54; dates/months 50/12; PF R/price 0.125572/0.137584; Net -57.333333 R; expectancy -1.061728 R; positive months 0/12; conditional DD 57.333333 R.
Accepted 56 = CLOSED 54 + EXCLUDED 2; SKIP 0; exclusion share 0.035714; conditional FLAT closures 48; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 3 | -4.833333 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-02 | 5 | -4.833333 | 0.093750 | 0.095238 | 5 | 1 |
| 2023-03 | 10 | -7.233333 | 0.378223 | 0.370370 | 4 | 1 |
| 2023-04 | 6 | -2.533333 | 0.479452 | 0.518519 | 6 | 0 |
| 2023-05 | 6 | -7.100000 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-06 | 6 | -4.900000 | 0.169492 | 0.192308 | 4 | 0 |
| 2023-07 | 3 | -4.733333 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 3 | -4.333333 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 4 | -5.800000 | 0.000000 | 0.000000 | 43 | 0 |
| 2023-10 | 3 | -4.066667 | 0.000000 | 0.000000 | 0 | 0 |
| 2023-11 | 4 | -5.566667 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-12 | 1 | -1.400000 | 0.000000 | 0.000000 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK3_TOL1_MAXBARS36_SB2_TP8

**INSUFFICIENT_SAMPLE**; failed gates: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors; sample reasons: CLOSED_BELOW_100.
CLOSED 54; dates/months 50/12; PF R/price 0.125572/0.137584; Net -57.333333 R; expectancy -1.061728 R; positive months 0/12; conditional DD 57.333333 R.
Accepted 56 = CLOSED 54 + EXCLUDED 2; SKIP 0; exclusion share 0.035714; conditional FLAT closures 48; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 3 | -4.833333 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-02 | 5 | -4.833333 | 0.093750 | 0.095238 | 5 | 1 |
| 2023-03 | 10 | -7.233333 | 0.378223 | 0.370370 | 4 | 1 |
| 2023-04 | 6 | -2.533333 | 0.479452 | 0.518519 | 6 | 0 |
| 2023-05 | 6 | -7.100000 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-06 | 6 | -4.900000 | 0.169492 | 0.192308 | 4 | 0 |
| 2023-07 | 3 | -4.733333 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 3 | -4.333333 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 4 | -5.800000 | 0.000000 | 0.000000 | 43 | 0 |
| 2023-10 | 3 | -4.066667 | 0.000000 | 0.000000 | 0 | 0 |
| 2023-11 | 4 | -5.566667 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-12 | 1 | -1.400000 | 0.000000 | 0.000000 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK3_TOL1_MAXBARS36_SB2_TP9

**INSUFFICIENT_SAMPLE**; failed gates: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors; sample reasons: CLOSED_BELOW_100.
CLOSED 54; dates/months 50/12; PF R/price 0.125572/0.137584; Net -57.333333 R; expectancy -1.061728 R; positive months 0/12; conditional DD 57.333333 R.
Accepted 56 = CLOSED 54 + EXCLUDED 2; SKIP 0; exclusion share 0.035714; conditional FLAT closures 48; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 3 | -4.833333 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-02 | 5 | -4.833333 | 0.093750 | 0.095238 | 5 | 1 |
| 2023-03 | 10 | -7.233333 | 0.378223 | 0.370370 | 4 | 1 |
| 2023-04 | 6 | -2.533333 | 0.479452 | 0.518519 | 6 | 0 |
| 2023-05 | 6 | -7.100000 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-06 | 6 | -4.900000 | 0.169492 | 0.192308 | 4 | 0 |
| 2023-07 | 3 | -4.733333 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 3 | -4.333333 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 4 | -5.800000 | 0.000000 | 0.000000 | 43 | 0 |
| 2023-10 | 3 | -4.066667 | 0.000000 | 0.000000 | 0 | 0 |
| 2023-11 | 4 | -5.566667 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-12 | 1 | -1.400000 | 0.000000 | 0.000000 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK3_TOL1_MAXBARS36_SB2_TP10

**INSUFFICIENT_SAMPLE**; failed gates: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors; sample reasons: CLOSED_BELOW_100.
CLOSED 54; dates/months 50/12; PF R/price 0.125572/0.137584; Net -57.333333 R; expectancy -1.061728 R; positive months 0/12; conditional DD 57.333333 R.
Accepted 56 = CLOSED 54 + EXCLUDED 2; SKIP 0; exclusion share 0.035714; conditional FLAT closures 48; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 3 | -4.833333 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-02 | 5 | -4.833333 | 0.093750 | 0.095238 | 5 | 1 |
| 2023-03 | 10 | -7.233333 | 0.378223 | 0.370370 | 4 | 1 |
| 2023-04 | 6 | -2.533333 | 0.479452 | 0.518519 | 6 | 0 |
| 2023-05 | 6 | -7.100000 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-06 | 6 | -4.900000 | 0.169492 | 0.192308 | 4 | 0 |
| 2023-07 | 3 | -4.733333 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 3 | -4.333333 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 4 | -5.800000 | 0.000000 | 0.000000 | 43 | 0 |
| 2023-10 | 3 | -4.066667 | 0.000000 | 0.000000 | 0 | 0 |
| 2023-11 | 4 | -5.566667 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-12 | 1 | -1.400000 | 0.000000 | 0.000000 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK3_TOL2_MAXBARS24_SB1_TP2

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 110; dates/months 85/12; PF R/price 0.505076/0.548000; Net -61.750000 R; expectancy -0.561364 R; positive months 2/12; conditional DD 65.816667 R.
Accepted 112 = CLOSED 110 + EXCLUDED 2; SKIP 2; exclusion share 0.017857; conditional FLAT closures 104; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 7 | 2.266667 | 1.369565 | 1.750000 | 7 | 1 |
| 2023-02 | 15 | -14.133333 | 0.266436 | 0.246753 | 5 | 0 |
| 2023-03 | 15 | -12.066667 | 0.255144 | 0.269841 | 4 | 1 |
| 2023-04 | 13 | -8.566667 | 0.436404 | 0.433333 | 6 | 0 |
| 2023-05 | 8 | -2.533333 | 0.707692 | 0.600000 | 7 | 0 |
| 2023-06 | 4 | -3.483333 | 0.264085 | 0.294118 | 4 | 0 |
| 2023-07 | 7 | -6.133333 | 0.328467 | 0.333333 | 1 | 0 |
| 2023-08 | 3 | -4.466667 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 7 | -6.500000 | 0.301075 | 0.400000 | 43 | 0 |
| 2023-10 | 6 | 12.066667 | 8.240000 | 11.800000 | 0 | 0 |
| 2023-11 | 12 | -13.566667 | 0.181087 | 0.176471 | 1 | 0 |
| 2023-12 | 13 | -4.633333 | 0.655087 | 0.785714 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK3_TOL2_MAXBARS24_SB1_TP3

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 105; dates/months 84/12; PF R/price 0.698348/0.752643; Net -35.916667 R; expectancy -0.342063 R; positive months 4/12; conditional DD 47.816667 R.
Accepted 108 = CLOSED 105 + EXCLUDED 3; SKIP 2; exclusion share 0.027778; conditional FLAT closures 102; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 4 | 1.666667 | 1.500000 | 2.500000 | 7 | 2 |
| 2023-02 | 15 | -12.466667 | 0.352941 | 0.311688 | 5 | 0 |
| 2023-03 | 15 | -10.566667 | 0.347737 | 0.365079 | 4 | 1 |
| 2023-04 | 13 | -5.500000 | 0.638158 | 0.633333 | 6 | 0 |
| 2023-05 | 8 | 0.200000 | 1.023077 | 0.875000 | 7 | 0 |
| 2023-06 | 4 | -3.483333 | 0.264085 | 0.294118 | 4 | 0 |
| 2023-07 | 7 | -4.633333 | 0.492701 | 0.500000 | 1 | 0 |
| 2023-08 | 3 | -4.466667 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 7 | -5.100000 | 0.451613 | 0.600000 | 43 | 0 |
| 2023-10 | 6 | 18.033333 | 11.820000 | 16.800000 | 0 | 0 |
| 2023-11 | 12 | -12.066667 | 0.271630 | 0.264706 | 1 | 0 |
| 2023-12 | 11 | 2.466667 | 1.234177 | 1.511628 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK3_TOL2_MAXBARS24_SB1_TP4

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors; sample reasons: none.
CLOSED 105; dates/months 84/12; PF R/price 0.743157/0.810021; Net -30.966667 R; expectancy -0.294921 R; positive months 4/12; conditional DD 41.100000 R.
Accepted 108 = CLOSED 105 + EXCLUDED 3; SKIP 2; exclusion share 0.027778; conditional FLAT closures 102; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 4 | 1.666667 | 1.500000 | 2.500000 | 7 | 2 |
| 2023-02 | 15 | -10.800000 | 0.439446 | 0.376623 | 5 | 0 |
| 2023-03 | 15 | -9.066667 | 0.440329 | 0.460317 | 4 | 1 |
| 2023-04 | 13 | -2.433333 | 0.839912 | 0.833333 | 6 | 0 |
| 2023-05 | 8 | 1.600000 | 1.184615 | 1.050000 | 7 | 0 |
| 2023-06 | 4 | -3.483333 | 0.264085 | 0.294118 | 4 | 0 |
| 2023-07 | 7 | -3.133333 | 0.656934 | 0.666667 | 1 | 0 |
| 2023-08 | 3 | -4.466667 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 7 | -3.700000 | 0.602151 | 0.800000 | 43 | 0 |
| 2023-10 | 6 | 8.500000 | 3.684211 | 4.818182 | 0 | 0 |
| 2023-11 | 12 | -12.316667 | 0.256539 | 0.250000 | 1 | 0 |
| 2023-12 | 11 | 6.666667 | 1.632911 | 2.000000 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK3_TOL2_MAXBARS24_SB1_TP5

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors; sample reasons: none.
CLOSED 105; dates/months 84/12; PF R/price 0.768706/0.841237; Net -28.233333 R; expectancy -0.268889 R; positive months 5/12; conditional DD 39.166667 R.
Accepted 108 = CLOSED 105 + EXCLUDED 3; SKIP 2; exclusion share 0.027778; conditional FLAT closures 102; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 4 | 1.666667 | 1.500000 | 2.500000 | 7 | 2 |
| 2023-02 | 15 | -9.133333 | 0.525952 | 0.441558 | 5 | 0 |
| 2023-03 | 15 | -8.566667 | 0.471193 | 0.492063 | 4 | 1 |
| 2023-04 | 13 | 0.633333 | 1.041667 | 1.033333 | 6 | 0 |
| 2023-05 | 8 | 3.000000 | 1.346154 | 1.225000 | 7 | 0 |
| 2023-06 | 4 | -3.483333 | 0.264085 | 0.294118 | 4 | 0 |
| 2023-07 | 7 | -10.633333 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 3 | -4.466667 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 7 | -2.300000 | 0.752688 | 1.000000 | 43 | 0 |
| 2023-10 | 6 | 9.900000 | 4.126316 | 5.454545 | 0 | 0 |
| 2023-11 | 12 | -12.316667 | 0.256539 | 0.250000 | 1 | 0 |
| 2023-12 | 11 | 7.466667 | 1.708861 | 2.093023 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK3_TOL2_MAXBARS24_SB1_TP6

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors; sample reasons: none.
CLOSED 105; dates/months 84/12; PF R/price 0.835336/0.911340; Net -20.100000 R; expectancy -0.191429 R; positive months 5/12; conditional DD 32.433333 R.
Accepted 108 = CLOSED 105 + EXCLUDED 3; SKIP 2; exclusion share 0.027778; conditional FLAT closures 102; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 4 | 1.666667 | 1.500000 | 2.500000 | 7 | 2 |
| 2023-02 | 15 | -7.466667 | 0.612457 | 0.506494 | 5 | 0 |
| 2023-03 | 15 | -8.566667 | 0.471193 | 0.492063 | 4 | 1 |
| 2023-04 | 13 | 1.500000 | 1.098684 | 1.050000 | 6 | 0 |
| 2023-05 | 8 | 4.400000 | 1.507692 | 1.400000 | 7 | 0 |
| 2023-06 | 4 | -3.483333 | 0.264085 | 0.294118 | 4 | 0 |
| 2023-07 | 7 | -10.633333 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 3 | -4.466667 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 7 | -0.900000 | 0.903226 | 1.200000 | 43 | 0 |
| 2023-10 | 6 | 11.300000 | 4.568421 | 6.090909 | 0 | 0 |
| 2023-11 | 12 | -12.316667 | 0.256539 | 0.250000 | 1 | 0 |
| 2023-12 | 11 | 8.866667 | 1.841772 | 2.255814 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK3_TOL2_MAXBARS24_SB1_TP7

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors; sample reasons: none.
CLOSED 105; dates/months 84/12; PF R/price 0.875751/0.948454; Net -15.166667 R; expectancy -0.144444 R; positive months 6/12; conditional DD 25.783333 R.
Accepted 108 = CLOSED 105 + EXCLUDED 3; SKIP 2; exclusion share 0.027778; conditional FLAT closures 102; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 4 | 1.666667 | 1.500000 | 2.500000 | 7 | 2 |
| 2023-02 | 15 | -5.800000 | 0.698962 | 0.571429 | 5 | 0 |
| 2023-03 | 15 | -8.566667 | 0.471193 | 0.492063 | 4 | 1 |
| 2023-04 | 13 | 3.166667 | 1.208333 | 1.133333 | 6 | 0 |
| 2023-05 | 8 | 5.800000 | 1.669231 | 1.575000 | 7 | 0 |
| 2023-06 | 4 | -3.483333 | 0.264085 | 0.294118 | 4 | 0 |
| 2023-07 | 7 | -10.633333 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 3 | -4.466667 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 7 | 0.500000 | 1.053763 | 1.400000 | 43 | 0 |
| 2023-10 | 6 | 12.700000 | 5.010526 | 6.727273 | 0 | 0 |
| 2023-11 | 12 | -12.316667 | 0.256539 | 0.250000 | 1 | 0 |
| 2023-12 | 11 | 6.266667 | 1.594937 | 1.953488 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK3_TOL2_MAXBARS24_SB1_TP8

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors; sample reasons: none.
CLOSED 105; dates/months 84/12; PF R/price 0.911251/0.979381; Net -10.833333 R; expectancy -0.103175 R; positive months 6/12; conditional DD 23.250000 R.
Accepted 108 = CLOSED 105 + EXCLUDED 3; SKIP 2; exclusion share 0.027778; conditional FLAT closures 102; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 4 | 1.666667 | 1.500000 | 2.500000 | 7 | 2 |
| 2023-02 | 15 | -4.133333 | 0.785467 | 0.636364 | 5 | 0 |
| 2023-03 | 15 | -8.566667 | 0.471193 | 0.492063 | 4 | 1 |
| 2023-04 | 13 | 4.833333 | 1.317982 | 1.216667 | 6 | 0 |
| 2023-05 | 8 | 7.200000 | 1.830769 | 1.750000 | 7 | 0 |
| 2023-06 | 4 | -3.483333 | 0.264085 | 0.294118 | 4 | 0 |
| 2023-07 | 7 | -10.633333 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 3 | -4.466667 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 7 | 1.900000 | 1.204301 | 1.600000 | 43 | 0 |
| 2023-10 | 6 | 10.900000 | 4.442105 | 5.909091 | 0 | 0 |
| 2023-11 | 12 | -12.316667 | 0.256539 | 0.250000 | 1 | 0 |
| 2023-12 | 11 | 6.266667 | 1.594937 | 1.953488 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK3_TOL2_MAXBARS24_SB1_TP9

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors; sample reasons: none.
CLOSED 105; dates/months 84/12; PF R/price 0.910705/0.964948; Net -10.900000 R; expectancy -0.103810 R; positive months 5/12; conditional DD 26.166667 R.
Accepted 108 = CLOSED 105 + EXCLUDED 3; SKIP 2; exclusion share 0.027778; conditional FLAT closures 102; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 4 | 1.666667 | 1.500000 | 2.500000 | 7 | 2 |
| 2023-02 | 15 | -2.466667 | 0.871972 | 0.701299 | 5 | 0 |
| 2023-03 | 15 | -8.566667 | 0.471193 | 0.492063 | 4 | 1 |
| 2023-04 | 13 | 6.500000 | 1.427632 | 1.300000 | 6 | 0 |
| 2023-05 | 8 | 8.600000 | 1.992308 | 1.925000 | 7 | 0 |
| 2023-06 | 4 | -3.483333 | 0.264085 | 0.294118 | 4 | 0 |
| 2023-07 | 7 | -10.633333 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 3 | -4.466667 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 7 | -2.900000 | 0.688172 | 0.914286 | 43 | 0 |
| 2023-10 | 6 | 10.900000 | 4.442105 | 5.909091 | 0 | 0 |
| 2023-11 | 12 | -12.316667 | 0.256539 | 0.250000 | 1 | 0 |
| 2023-12 | 11 | 6.266667 | 1.594937 | 1.953488 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK3_TOL2_MAXBARS24_SB1_TP10

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors; sample reasons: none.
CLOSED 104; dates/months 84/12; PF R/price 0.962625/1.010417; Net -4.500000 R; expectancy -0.043269 R; positive months 6/12; conditional DD 24.766667 R.
Accepted 107 = CLOSED 104 + EXCLUDED 3; SKIP 2; exclusion share 0.028037; conditional FLAT closures 101; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 4 | 1.666667 | 1.500000 | 2.500000 | 7 | 2 |
| 2023-02 | 14 | 0.866667 | 1.049242 | 0.819444 | 5 | 0 |
| 2023-03 | 15 | -8.566667 | 0.471193 | 0.492063 | 4 | 1 |
| 2023-04 | 13 | 8.166667 | 1.537281 | 1.383333 | 6 | 0 |
| 2023-05 | 8 | 10.000000 | 2.153846 | 2.100000 | 7 | 0 |
| 2023-06 | 4 | -3.483333 | 0.264085 | 0.294118 | 4 | 0 |
| 2023-07 | 7 | -10.633333 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 3 | -4.466667 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 7 | -2.900000 | 0.688172 | 0.914286 | 43 | 0 |
| 2023-10 | 6 | 10.900000 | 4.442105 | 5.909091 | 0 | 0 |
| 2023-11 | 12 | -12.316667 | 0.256539 | 0.250000 | 1 | 0 |
| 2023-12 | 11 | 6.266667 | 1.594937 | 1.953488 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK3_TOL2_MAXBARS24_SB2_TP2

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 124; dates/months 96/12; PF R/price 0.583823/0.650927; Net -53.166667 R; expectancy -0.428763 R; positive months 3/12; conditional DD 55.500000 R.
Accepted 126 = CLOSED 124 + EXCLUDED 2; SKIP 2; exclusion share 0.015873; conditional FLAT closures 118; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 8 | 0.666667 | 1.090909 | 1.454545 | 7 | 1 |
| 2023-02 | 18 | -13.900000 | 0.344340 | 0.364583 | 5 | 0 |
| 2023-03 | 16 | -7.600000 | 0.461629 | 0.500000 | 4 | 1 |
| 2023-04 | 13 | 3.400000 | 1.335526 | 1.404255 | 6 | 0 |
| 2023-05 | 11 | -0.833333 | 0.915254 | 0.760000 | 7 | 0 |
| 2023-06 | 6 | -6.666667 | 0.130435 | 0.166667 | 4 | 0 |
| 2023-07 | 9 | -9.000000 | 0.237288 | 0.269231 | 1 | 0 |
| 2023-08 | 4 | -5.666667 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 7 | -5.900000 | 0.311284 | 0.390244 | 43 | 0 |
| 2023-10 | 7 | 9.466667 | 3.989474 | 6.090909 | 0 | 0 |
| 2023-11 | 13 | -14.266667 | 0.164063 | 0.166667 | 1 | 0 |
| 2023-12 | 12 | -2.866667 | 0.744048 | 0.877193 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK3_TOL2_MAXBARS24_SB2_TP3

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors; sample reasons: none.
CLOSED 119; dates/months 95/12; PF R/price 0.623318/0.696707; Net -47.116667 R; expectancy -0.395938 R; positive months 4/12; conditional DD 52.050000 R.
Accepted 123 = CLOSED 119 + EXCLUDED 4; SKIP 2; exclusion share 0.032520; conditional FLAT closures 116; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 5 | -0.500000 | 0.892857 | 1.470588 | 7 | 2 |
| 2023-02 | 17 | -15.200000 | 0.283019 | 0.281250 | 5 | 1 |
| 2023-03 | 16 | -6.600000 | 0.532468 | 0.575758 | 4 | 1 |
| 2023-04 | 13 | 3.083333 | 1.304276 | 1.382979 | 6 | 0 |
| 2023-05 | 11 | 2.666667 | 1.271186 | 1.060000 | 7 | 0 |
| 2023-06 | 6 | -6.666667 | 0.130435 | 0.166667 | 4 | 0 |
| 2023-07 | 9 | -7.600000 | 0.355932 | 0.403846 | 1 | 0 |
| 2023-08 | 4 | -5.666667 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 7 | -4.566667 | 0.466926 | 0.585366 | 43 | 0 |
| 2023-10 | 7 | 4.266667 | 1.934307 | 2.722222 | 0 | 0 |
| 2023-11 | 13 | -12.866667 | 0.246094 | 0.250000 | 1 | 0 |
| 2023-12 | 11 | 2.533333 | 1.258503 | 1.480000 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK3_TOL2_MAXBARS24_SB2_TP4

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors; sample reasons: none.
CLOSED 119; dates/months 95/12; PF R/price 0.748035/0.837088; Net -31.516667 R; expectancy -0.264846 R; positive months 4/12; conditional DD 39.216667 R.
Accepted 123 = CLOSED 119 + EXCLUDED 4; SKIP 2; exclusion share 0.032520; conditional FLAT closures 116; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 5 | -0.500000 | 0.892857 | 1.470588 | 7 | 2 |
| 2023-02 | 17 | -13.700000 | 0.353774 | 0.343750 | 5 | 1 |
| 2023-03 | 16 | -5.600000 | 0.603306 | 0.651515 | 4 | 1 |
| 2023-04 | 13 | 5.916667 | 1.583882 | 1.680851 | 6 | 0 |
| 2023-05 | 11 | 5.666667 | 1.576271 | 1.320000 | 7 | 0 |
| 2023-06 | 6 | -6.666667 | 0.130435 | 0.166667 | 4 | 0 |
| 2023-07 | 9 | -6.200000 | 0.474576 | 0.538462 | 1 | 0 |
| 2023-08 | 4 | -5.666667 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 7 | -3.233333 | 0.622568 | 0.780488 | 43 | 0 |
| 2023-10 | 7 | 5.600000 | 2.226277 | 3.166667 | 0 | 0 |
| 2023-11 | 13 | -13.666667 | 0.199219 | 0.202381 | 1 | 0 |
| 2023-12 | 11 | 6.533333 | 1.666667 | 1.960000 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK3_TOL2_MAXBARS24_SB2_TP5

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors; sample reasons: none.
CLOSED 119; dates/months 95/12; PF R/price 0.758730/0.842466; Net -30.516667 R; expectancy -0.256443 R; positive months 4/12; conditional DD 37.716667 R.
Accepted 123 = CLOSED 119 + EXCLUDED 4; SKIP 2; exclusion share 0.032520; conditional FLAT closures 116; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 5 | -0.500000 | 0.892857 | 1.470588 | 7 | 2 |
| 2023-02 | 17 | -12.200000 | 0.424528 | 0.406250 | 5 | 1 |
| 2023-03 | 16 | -5.600000 | 0.603306 | 0.651515 | 4 | 1 |
| 2023-04 | 13 | 7.250000 | 1.715461 | 1.787234 | 6 | 0 |
| 2023-05 | 11 | 8.666667 | 1.881356 | 1.580000 | 7 | 0 |
| 2023-06 | 6 | -6.666667 | 0.130435 | 0.166667 | 4 | 0 |
| 2023-07 | 9 | -13.200000 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 4 | -5.666667 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 7 | -1.900000 | 0.778210 | 0.975610 | 43 | 0 |
| 2023-10 | 7 | 6.933333 | 2.518248 | 3.611111 | 0 | 0 |
| 2023-11 | 13 | -13.666667 | 0.199219 | 0.202381 | 1 | 0 |
| 2023-12 | 11 | 6.033333 | 1.615646 | 1.900000 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK3_TOL2_MAXBARS24_SB2_TP6

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors; sample reasons: none.
CLOSED 119; dates/months 95/12; PF R/price 0.812755/0.893836; Net -23.683333 R; expectancy -0.199020 R; positive months 4/12; conditional DD 33.233333 R.
Accepted 123 = CLOSED 119 + EXCLUDED 4; SKIP 2; exclusion share 0.032520; conditional FLAT closures 116; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 5 | -0.500000 | 0.892857 | 1.470588 | 7 | 2 |
| 2023-02 | 17 | -10.700000 | 0.495283 | 0.468750 | 5 | 1 |
| 2023-03 | 16 | -5.600000 | 0.603306 | 0.651515 | 4 | 1 |
| 2023-04 | 13 | 8.750000 | 1.863487 | 1.914894 | 6 | 0 |
| 2023-05 | 11 | 11.666667 | 2.186441 | 1.840000 | 7 | 0 |
| 2023-06 | 6 | -6.666667 | 0.130435 | 0.166667 | 4 | 0 |
| 2023-07 | 9 | -13.200000 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 4 | -5.666667 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 7 | -0.566667 | 0.933852 | 1.170732 | 43 | 0 |
| 2023-10 | 7 | 8.266667 | 2.810219 | 4.055556 | 0 | 0 |
| 2023-11 | 13 | -13.666667 | 0.199219 | 0.202381 | 1 | 0 |
| 2023-12 | 11 | 4.200000 | 1.428571 | 1.680000 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK3_TOL2_MAXBARS24_SB2_TP7

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors; sample reasons: none.
CLOSED 119; dates/months 95/12; PF R/price 0.860192/0.936644; Net -17.683333 R; expectancy -0.148599 R; positive months 5/12; conditional DD 33.233333 R.
Accepted 123 = CLOSED 119 + EXCLUDED 4; SKIP 2; exclusion share 0.032520; conditional FLAT closures 116; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 5 | -0.500000 | 0.892857 | 1.470588 | 7 | 2 |
| 2023-02 | 17 | -9.200000 | 0.566038 | 0.531250 | 5 | 1 |
| 2023-03 | 16 | -5.600000 | 0.603306 | 0.651515 | 4 | 1 |
| 2023-04 | 13 | 10.250000 | 2.011513 | 2.042553 | 6 | 0 |
| 2023-05 | 11 | 14.666667 | 2.491525 | 2.100000 | 7 | 0 |
| 2023-06 | 6 | -6.666667 | 0.130435 | 0.166667 | 4 | 0 |
| 2023-07 | 9 | -13.200000 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 4 | -5.666667 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 7 | 0.766667 | 1.089494 | 1.365854 | 43 | 0 |
| 2023-10 | 7 | 6.933333 | 2.518248 | 3.611111 | 0 | 0 |
| 2023-11 | 13 | -13.666667 | 0.199219 | 0.202381 | 1 | 0 |
| 2023-12 | 11 | 4.200000 | 1.428571 | 1.680000 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK3_TOL2_MAXBARS24_SB2_TP8

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors; sample reasons: none.
CLOSED 119; dates/months 95/12; PF R/price 0.876005/0.938356; Net -15.683333 R; expectancy -0.131793 R; positive months 4/12; conditional DD 37.233333 R.
Accepted 123 = CLOSED 119 + EXCLUDED 4; SKIP 2; exclusion share 0.032520; conditional FLAT closures 116; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 5 | -0.500000 | 0.892857 | 1.470588 | 7 | 2 |
| 2023-02 | 17 | -7.700000 | 0.636792 | 0.593750 | 5 | 1 |
| 2023-03 | 16 | -5.600000 | 0.603306 | 0.651515 | 4 | 1 |
| 2023-04 | 13 | 11.750000 | 2.159539 | 2.170213 | 6 | 0 |
| 2023-05 | 11 | 17.666667 | 2.796610 | 2.360000 | 7 | 0 |
| 2023-06 | 6 | -6.666667 | 0.130435 | 0.166667 | 4 | 0 |
| 2023-07 | 9 | -13.200000 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 4 | -5.666667 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 7 | -3.233333 | 0.622568 | 0.780488 | 43 | 0 |
| 2023-10 | 7 | 6.933333 | 2.518248 | 3.611111 | 0 | 0 |
| 2023-11 | 13 | -13.666667 | 0.199219 | 0.202381 | 1 | 0 |
| 2023-12 | 11 | 4.200000 | 1.428571 | 1.680000 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK3_TOL2_MAXBARS24_SB2_TP9

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors; sample reasons: none.
CLOSED 118; dates/months 95/12; PF R/price 0.924523/0.982699; Net -9.433333 R; expectancy -0.079944 R; positive months 4/12; conditional DD 37.233333 R.
Accepted 122 = CLOSED 118 + EXCLUDED 4; SKIP 2; exclusion share 0.032787; conditional FLAT closures 115; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 5 | -0.500000 | 0.892857 | 1.470588 | 7 | 2 |
| 2023-02 | 16 | -5.950000 | 0.697970 | 0.644444 | 5 | 1 |
| 2023-03 | 16 | -5.600000 | 0.603306 | 0.651515 | 4 | 1 |
| 2023-04 | 13 | 13.250000 | 2.307566 | 2.297872 | 6 | 0 |
| 2023-05 | 11 | 20.666667 | 3.101695 | 2.620000 | 7 | 0 |
| 2023-06 | 6 | -6.666667 | 0.130435 | 0.166667 | 4 | 0 |
| 2023-07 | 9 | -13.200000 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 4 | -5.666667 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 7 | -3.233333 | 0.622568 | 0.780488 | 43 | 0 |
| 2023-10 | 7 | 6.933333 | 2.518248 | 3.611111 | 0 | 0 |
| 2023-11 | 13 | -13.666667 | 0.199219 | 0.202381 | 1 | 0 |
| 2023-12 | 11 | 4.200000 | 1.428571 | 1.680000 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK3_TOL2_MAXBARS24_SB2_TP10

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 118; dates/months 95/12; PF R/price 0.886518/0.951557; Net -14.183333 R; expectancy -0.120198 R; positive months 4/12; conditional DD 37.233333 R.
Accepted 122 = CLOSED 118 + EXCLUDED 4; SKIP 2; exclusion share 0.032787; conditional FLAT closures 115; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 5 | -0.500000 | 0.892857 | 1.470588 | 7 | 2 |
| 2023-02 | 16 | -5.950000 | 0.697970 | 0.644444 | 5 | 1 |
| 2023-03 | 16 | -5.600000 | 0.603306 | 0.651515 | 4 | 1 |
| 2023-04 | 13 | 5.500000 | 1.542763 | 1.638298 | 6 | 0 |
| 2023-05 | 11 | 23.666667 | 3.406780 | 2.880000 | 7 | 0 |
| 2023-06 | 6 | -6.666667 | 0.130435 | 0.166667 | 4 | 0 |
| 2023-07 | 9 | -13.200000 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 4 | -5.666667 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 7 | -3.233333 | 0.622568 | 0.780488 | 43 | 0 |
| 2023-10 | 7 | 6.933333 | 2.518248 | 3.611111 | 0 | 0 |
| 2023-11 | 13 | -13.666667 | 0.199219 | 0.202381 | 1 | 0 |
| 2023-12 | 11 | 4.200000 | 1.428571 | 1.680000 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK3_TOL2_MAXBARS36_SB1_TP2

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 110; dates/months 85/12; PF R/price 0.413731/0.453307; Net -76.566667 R; expectancy -0.696061 R; positive months 2/12; conditional DD 80.366667 R.
Accepted 112 = CLOSED 110 + EXCLUDED 2; SKIP 2; exclusion share 0.017857; conditional FLAT closures 104; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 7 | 2.000000 | 1.312500 | 1.909091 | 7 | 1 |
| 2023-02 | 16 | -15.733333 | 0.246006 | 0.231707 | 5 | 0 |
| 2023-03 | 12 | -11.966667 | 0.217865 | 0.220339 | 4 | 1 |
| 2023-04 | 14 | -8.650000 | 0.424612 | 0.377049 | 6 | 0 |
| 2023-05 | 7 | -5.866667 | 0.323077 | 0.350000 | 7 | 0 |
| 2023-06 | 4 | -3.483333 | 0.264085 | 0.294118 | 4 | 0 |
| 2023-07 | 9 | -9.133333 | 0.247253 | 0.250000 | 1 | 0 |
| 2023-08 | 2 | -3.066667 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 7 | -6.500000 | 0.301075 | 0.400000 | 43 | 0 |
| 2023-10 | 7 | 6.100000 | 2.262069 | 2.812500 | 0 | 0 |
| 2023-11 | 12 | -11.166667 | 0.263736 | 0.262295 | 1 | 0 |
| 2023-12 | 13 | -9.100000 | 0.397351 | 0.491803 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK3_TOL2_MAXBARS36_SB1_TP3

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 107; dates/months 84/12; PF R/price 0.537458/0.578842; Net -59.066667 R; expectancy -0.552025 R; positive months 1/12; conditional DD 60.866667 R.
Accepted 110 = CLOSED 107 + EXCLUDED 3; SKIP 2; exclusion share 0.027273; conditional FLAT closures 103; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 5 | -0.000000 | 1.000000 | 1.666667 | 7 | 2 |
| 2023-02 | 16 | -14.066667 | 0.325879 | 0.292683 | 5 | 0 |
| 2023-03 | 12 | -10.466667 | 0.315904 | 0.322034 | 4 | 1 |
| 2023-04 | 14 | -6.983333 | 0.535477 | 0.459016 | 6 | 0 |
| 2023-05 | 7 | -4.466667 | 0.484615 | 0.525000 | 7 | 0 |
| 2023-06 | 4 | -3.483333 | 0.264085 | 0.294118 | 4 | 0 |
| 2023-07 | 9 | -7.633333 | 0.370879 | 0.375000 | 1 | 0 |
| 2023-08 | 2 | -3.066667 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 7 | -5.100000 | 0.451613 | 0.600000 | 43 | 0 |
| 2023-10 | 7 | 10.666667 | 3.206897 | 3.937500 | 0 | 0 |
| 2023-11 | 12 | -9.666667 | 0.362637 | 0.360656 | 1 | 0 |
| 2023-12 | 12 | -4.800000 | 0.647059 | 0.800000 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK3_TOL2_MAXBARS36_SB1_TP4

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 107; dates/months 84/12; PF R/price 0.579592/0.633136; Net -54.316667 R; expectancy -0.507632 R; positive months 1/12; conditional DD 56.116667 R.
Accepted 110 = CLOSED 107 + EXCLUDED 3; SKIP 2; exclusion share 0.027273; conditional FLAT closures 103; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 5 | -0.000000 | 1.000000 | 1.666667 | 7 | 2 |
| 2023-02 | 16 | -12.400000 | 0.405751 | 0.353659 | 5 | 0 |
| 2023-03 | 12 | -8.966667 | 0.413943 | 0.423729 | 4 | 1 |
| 2023-04 | 14 | -5.316667 | 0.646341 | 0.540984 | 6 | 0 |
| 2023-05 | 7 | -3.066667 | 0.646154 | 0.700000 | 7 | 0 |
| 2023-06 | 4 | -3.483333 | 0.264085 | 0.294118 | 4 | 0 |
| 2023-07 | 9 | -6.133333 | 0.494505 | 0.500000 | 1 | 0 |
| 2023-08 | 2 | -3.066667 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 7 | -3.700000 | 0.602151 | 0.800000 | 43 | 0 |
| 2023-10 | 7 | 3.733333 | 1.589474 | 2.045455 | 0 | 0 |
| 2023-11 | 12 | -9.916667 | 0.346154 | 0.344262 | 1 | 0 |
| 2023-12 | 12 | -2.000000 | 0.852941 | 1.054545 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK3_TOL2_MAXBARS36_SB1_TP5

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 107; dates/months 84/12; PF R/price 0.591558/0.647173; Net -53.383333 R; expectancy -0.498910 R; positive months 1/12; conditional DD 55.250000 R.
Accepted 110 = CLOSED 107 + EXCLUDED 3; SKIP 2; exclusion share 0.027273; conditional FLAT closures 103; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 5 | -0.000000 | 1.000000 | 1.666667 | 7 | 2 |
| 2023-02 | 16 | -10.733333 | 0.485623 | 0.414634 | 5 | 0 |
| 2023-03 | 12 | -8.466667 | 0.446623 | 0.457627 | 4 | 1 |
| 2023-04 | 14 | -3.650000 | 0.757206 | 0.622951 | 6 | 0 |
| 2023-05 | 7 | -1.666667 | 0.807692 | 0.875000 | 7 | 0 |
| 2023-06 | 4 | -3.483333 | 0.264085 | 0.294118 | 4 | 0 |
| 2023-07 | 9 | -13.633333 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 2 | -3.066667 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 7 | -2.300000 | 0.752688 | 1.000000 | 43 | 0 |
| 2023-10 | 7 | 5.133333 | 1.810526 | 2.363636 | 0 | 0 |
| 2023-11 | 12 | -9.916667 | 0.346154 | 0.344262 | 1 | 0 |
| 2023-12 | 12 | -1.600000 | 0.882353 | 1.090909 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK3_TOL2_MAXBARS36_SB1_TP6

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 107; dates/months 84/12; PF R/price 0.659908/0.721248; Net -44.450000 R; expectancy -0.415421 R; positive months 1/12; conditional DD 47.716667 R.
Accepted 110 = CLOSED 107 + EXCLUDED 3; SKIP 2; exclusion share 0.027273; conditional FLAT closures 103; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 5 | -0.000000 | 1.000000 | 1.666667 | 7 | 2 |
| 2023-02 | 16 | -9.066667 | 0.565495 | 0.475610 | 5 | 0 |
| 2023-03 | 12 | -8.466667 | 0.446623 | 0.457627 | 4 | 1 |
| 2023-04 | 14 | -1.983333 | 0.868071 | 0.704918 | 6 | 0 |
| 2023-05 | 7 | -0.266667 | 0.969231 | 1.050000 | 7 | 0 |
| 2023-06 | 4 | -3.483333 | 0.264085 | 0.294118 | 4 | 0 |
| 2023-07 | 9 | -13.633333 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 2 | -3.066667 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 7 | -0.900000 | 0.903226 | 1.200000 | 43 | 0 |
| 2023-10 | 7 | 6.533333 | 2.031579 | 2.681818 | 0 | 0 |
| 2023-11 | 12 | -9.916667 | 0.346154 | 0.344262 | 1 | 0 |
| 2023-12 | 12 | -0.200000 | 0.985294 | 1.218182 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK3_TOL2_MAXBARS36_SB1_TP7

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 107; dates/months 84/12; PF R/price 0.697654/0.756335; Net -39.516667 R; expectancy -0.369315 R; positive months 3/12; conditional DD 41.316667 R.
Accepted 110 = CLOSED 107 + EXCLUDED 3; SKIP 2; exclusion share 0.027273; conditional FLAT closures 103; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 5 | -0.000000 | 1.000000 | 1.666667 | 7 | 2 |
| 2023-02 | 16 | -7.400000 | 0.645367 | 0.536585 | 5 | 0 |
| 2023-03 | 12 | -8.466667 | 0.446623 | 0.457627 | 4 | 1 |
| 2023-04 | 14 | -0.316667 | 0.978936 | 0.786885 | 6 | 0 |
| 2023-05 | 7 | 1.133333 | 1.130769 | 1.225000 | 7 | 0 |
| 2023-06 | 4 | -3.483333 | 0.264085 | 0.294118 | 4 | 0 |
| 2023-07 | 9 | -13.633333 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 2 | -3.066667 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 7 | 0.500000 | 1.053763 | 1.400000 | 43 | 0 |
| 2023-10 | 7 | 7.933333 | 2.252632 | 3.000000 | 0 | 0 |
| 2023-11 | 12 | -9.916667 | 0.346154 | 0.344262 | 1 | 0 |
| 2023-12 | 12 | -2.800000 | 0.794118 | 0.981818 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK3_TOL2_MAXBARS36_SB1_TP8

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 107; dates/months 84/12; PF R/price 0.730808/0.785575; Net -35.183333 R; expectancy -0.328816 R; positive months 4/12; conditional DD 36.983333 R.
Accepted 110 = CLOSED 107 + EXCLUDED 3; SKIP 2; exclusion share 0.027273; conditional FLAT closures 103; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 5 | -0.000000 | 1.000000 | 1.666667 | 7 | 2 |
| 2023-02 | 16 | -5.733333 | 0.725240 | 0.597561 | 5 | 0 |
| 2023-03 | 12 | -8.466667 | 0.446623 | 0.457627 | 4 | 1 |
| 2023-04 | 14 | 1.350000 | 1.089800 | 0.868852 | 6 | 0 |
| 2023-05 | 7 | 2.533333 | 1.292308 | 1.400000 | 7 | 0 |
| 2023-06 | 4 | -3.483333 | 0.264085 | 0.294118 | 4 | 0 |
| 2023-07 | 9 | -13.633333 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 2 | -3.066667 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 7 | 1.900000 | 1.204301 | 1.600000 | 43 | 0 |
| 2023-10 | 7 | 6.133333 | 1.968421 | 2.590909 | 0 | 0 |
| 2023-11 | 12 | -9.916667 | 0.346154 | 0.344262 | 1 | 0 |
| 2023-12 | 12 | -2.800000 | 0.794118 | 0.981818 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK3_TOL2_MAXBARS36_SB1_TP9

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors; sample reasons: none.
CLOSED 107; dates/months 84/12; PF R/price 0.730298/0.771930; Net -35.250000 R; expectancy -0.329439 R; positive months 3/12; conditional DD 37.050000 R.
Accepted 110 = CLOSED 107 + EXCLUDED 3; SKIP 2; exclusion share 0.027273; conditional FLAT closures 103; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 5 | -0.000000 | 1.000000 | 1.666667 | 7 | 2 |
| 2023-02 | 16 | -4.066667 | 0.805112 | 0.658537 | 5 | 0 |
| 2023-03 | 12 | -8.466667 | 0.446623 | 0.457627 | 4 | 1 |
| 2023-04 | 14 | 3.016667 | 1.200665 | 0.950820 | 6 | 0 |
| 2023-05 | 7 | 3.933333 | 1.453846 | 1.575000 | 7 | 0 |
| 2023-06 | 4 | -3.483333 | 0.264085 | 0.294118 | 4 | 0 |
| 2023-07 | 9 | -13.633333 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 2 | -3.066667 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 7 | -2.900000 | 0.688172 | 0.914286 | 43 | 0 |
| 2023-10 | 7 | 6.133333 | 1.968421 | 2.590909 | 0 | 0 |
| 2023-11 | 12 | -9.916667 | 0.346154 | 0.344262 | 1 | 0 |
| 2023-12 | 12 | -2.800000 | 0.794118 | 0.981818 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK3_TOL2_MAXBARS36_SB1_TP10

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors; sample reasons: none.
CLOSED 106; dates/months 84/12; PF R/price 0.776414/0.812992; Net -28.850000 R; expectancy -0.272170 R; positive months 3/12; conditional DD 32.983333 R.
Accepted 109 = CLOSED 106 + EXCLUDED 3; SKIP 2; exclusion share 0.027523; conditional FLAT closures 102; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 5 | -0.000000 | 1.000000 | 1.666667 | 7 | 2 |
| 2023-02 | 15 | -0.733333 | 0.961806 | 0.766234 | 5 | 0 |
| 2023-03 | 12 | -8.466667 | 0.446623 | 0.457627 | 4 | 1 |
| 2023-04 | 14 | 4.683333 | 1.311530 | 1.032787 | 6 | 0 |
| 2023-05 | 7 | 5.333333 | 1.615385 | 1.750000 | 7 | 0 |
| 2023-06 | 4 | -3.483333 | 0.264085 | 0.294118 | 4 | 0 |
| 2023-07 | 9 | -13.633333 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 2 | -3.066667 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 7 | -2.900000 | 0.688172 | 0.914286 | 43 | 0 |
| 2023-10 | 7 | 6.133333 | 1.968421 | 2.590909 | 0 | 0 |
| 2023-11 | 12 | -9.916667 | 0.346154 | 0.344262 | 1 | 0 |
| 2023-12 | 12 | -2.800000 | 0.794118 | 0.981818 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK3_TOL2_MAXBARS36_SB2_TP2

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors; sample reasons: none.
CLOSED 124; dates/months 97/12; PF R/price 0.546080/0.587940; Net -58.283333 R; expectancy -0.470027 R; positive months 3/12; conditional DD 62.950000 R.
Accepted 126 = CLOSED 124 + EXCLUDED 2; SKIP 2; exclusion share 0.015873; conditional FLAT closures 118; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 8 | 3.000000 | 1.500000 | 2.080000 | 7 | 1 |
| 2023-02 | 20 | -12.033333 | 0.469118 | 0.441176 | 5 | 0 |
| 2023-03 | 14 | -9.250000 | 0.387417 | 0.432836 | 4 | 1 |
| 2023-04 | 13 | 4.300000 | 1.498069 | 1.487805 | 6 | 0 |
| 2023-05 | 9 | -2.166667 | 0.734694 | 0.577778 | 7 | 0 |
| 2023-06 | 7 | -6.666667 | 0.130435 | 0.166667 | 4 | 0 |
| 2023-07 | 10 | -10.133333 | 0.216495 | 0.229508 | 1 | 0 |
| 2023-08 | 3 | -4.500000 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 7 | -5.900000 | 0.311284 | 0.390244 | 43 | 0 |
| 2023-10 | 8 | 3.900000 | 1.642857 | 2.125000 | 0 | 0 |
| 2023-11 | 12 | -10.466667 | 0.255924 | 0.253521 | 1 | 0 |
| 2023-12 | 13 | -8.366667 | 0.403800 | 0.478873 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK3_TOL2_MAXBARS36_SB2_TP3

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 120; dates/months 96/12; PF R/price 0.543022/0.592530; Net -58.066667 R; expectancy -0.483889 R; positive months 4/12; conditional DD 60.233333 R.
Accepted 124 = CLOSED 120 + EXCLUDED 4; SKIP 2; exclusion share 0.032258; conditional FLAT closures 116; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 6 | 0.500000 | 1.107143 | 1.705882 | 7 | 2 |
| 2023-02 | 19 | -16.000000 | 0.294118 | 0.284314 | 5 | 1 |
| 2023-03 | 14 | -8.250000 | 0.453642 | 0.507463 | 4 | 1 |
| 2023-04 | 13 | 2.650000 | 1.306950 | 1.268293 | 6 | 0 |
| 2023-05 | 9 | 0.833333 | 1.102041 | 0.866667 | 7 | 0 |
| 2023-06 | 7 | -6.666667 | 0.130435 | 0.166667 | 4 | 0 |
| 2023-07 | 10 | -8.733333 | 0.324742 | 0.344262 | 1 | 0 |
| 2023-08 | 3 | -4.500000 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 7 | -4.566667 | 0.466926 | 0.585366 | 43 | 0 |
| 2023-10 | 8 | 0.033333 | 1.004464 | 1.322581 | 0 | 0 |
| 2023-11 | 12 | -9.066667 | 0.355450 | 0.352113 | 1 | 0 |
| 2023-12 | 12 | -4.300000 | 0.659631 | 0.781250 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK3_TOL2_MAXBARS36_SB2_TP4

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors; sample reasons: none.
CLOSED 120; dates/months 96/12; PF R/price 0.644806/0.702886; Net -45.133333 R; expectancy -0.376111 R; positive months 4/12; conditional DD 47.300000 R.
Accepted 124 = CLOSED 120 + EXCLUDED 4; SKIP 2; exclusion share 0.032258; conditional FLAT closures 116; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 6 | 0.500000 | 1.107143 | 1.705882 | 7 | 2 |
| 2023-02 | 19 | -14.500000 | 0.360294 | 0.343137 | 5 | 1 |
| 2023-03 | 14 | -7.250000 | 0.519868 | 0.582090 | 4 | 1 |
| 2023-04 | 13 | 4.150000 | 1.480695 | 1.414634 | 6 | 0 |
| 2023-05 | 9 | 3.833333 | 1.469388 | 1.155556 | 7 | 0 |
| 2023-06 | 7 | -6.666667 | 0.130435 | 0.166667 | 4 | 0 |
| 2023-07 | 10 | -7.333333 | 0.432990 | 0.459016 | 1 | 0 |
| 2023-08 | 3 | -4.500000 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 7 | -3.233333 | 0.622568 | 0.780488 | 43 | 0 |
| 2023-10 | 8 | 1.366667 | 1.183036 | 1.580645 | 0 | 0 |
| 2023-11 | 12 | -9.866667 | 0.298578 | 0.295775 | 1 | 0 |
| 2023-12 | 12 | -1.633333 | 0.870712 | 1.031250 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK3_TOL2_MAXBARS36_SB2_TP5

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors; sample reasons: none.
CLOSED 120; dates/months 96/12; PF R/price 0.660353/0.714765; Net -43.633333 R; expectancy -0.363611 R; positive months 4/12; conditional DD 45.800000 R.
Accepted 124 = CLOSED 120 + EXCLUDED 4; SKIP 2; exclusion share 0.032258; conditional FLAT closures 116; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 6 | 0.500000 | 1.107143 | 1.705882 | 7 | 2 |
| 2023-02 | 19 | -13.000000 | 0.426471 | 0.401961 | 5 | 1 |
| 2023-03 | 14 | -7.250000 | 0.519868 | 0.582090 | 4 | 1 |
| 2023-04 | 13 | 5.650000 | 1.654440 | 1.560976 | 6 | 0 |
| 2023-05 | 9 | 6.833333 | 1.836735 | 1.444444 | 7 | 0 |
| 2023-06 | 7 | -6.666667 | 0.130435 | 0.166667 | 4 | 0 |
| 2023-07 | 10 | -14.333333 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 3 | -4.500000 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 7 | -1.900000 | 0.778210 | 0.975610 | 43 | 0 |
| 2023-10 | 8 | 2.700000 | 1.361607 | 1.838710 | 0 | 0 |
| 2023-11 | 12 | -9.866667 | 0.298578 | 0.295775 | 1 | 0 |
| 2023-12 | 12 | -1.800000 | 0.857520 | 1.015625 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK3_TOL2_MAXBARS36_SB2_TP6

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors; sample reasons: none.
CLOSED 120; dates/months 96/12; PF R/price 0.713544/0.765101; Net -36.800000 R; expectancy -0.306667 R; positive months 4/12; conditional DD 38.966667 R.
Accepted 124 = CLOSED 120 + EXCLUDED 4; SKIP 2; exclusion share 0.032258; conditional FLAT closures 116; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 6 | 0.500000 | 1.107143 | 1.705882 | 7 | 2 |
| 2023-02 | 19 | -11.500000 | 0.492647 | 0.460784 | 5 | 1 |
| 2023-03 | 14 | -7.250000 | 0.519868 | 0.582090 | 4 | 1 |
| 2023-04 | 13 | 7.150000 | 1.828185 | 1.707317 | 6 | 0 |
| 2023-05 | 9 | 9.833333 | 2.204082 | 1.733333 | 7 | 0 |
| 2023-06 | 7 | -6.666667 | 0.130435 | 0.166667 | 4 | 0 |
| 2023-07 | 10 | -14.333333 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 3 | -4.500000 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 7 | -0.566667 | 0.933852 | 1.170732 | 43 | 0 |
| 2023-10 | 8 | 4.033333 | 1.540179 | 2.096774 | 0 | 0 |
| 2023-11 | 12 | -9.866667 | 0.298578 | 0.295775 | 1 | 0 |
| 2023-12 | 12 | -3.633333 | 0.712401 | 0.843750 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK3_TOL2_MAXBARS36_SB2_TP7

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 120; dates/months 96/12; PF R/price 0.760249/0.807047; Net -30.800000 R; expectancy -0.256667 R; positive months 5/12; conditional DD 36.866667 R.
Accepted 124 = CLOSED 120 + EXCLUDED 4; SKIP 2; exclusion share 0.032258; conditional FLAT closures 116; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 6 | 0.500000 | 1.107143 | 1.705882 | 7 | 2 |
| 2023-02 | 19 | -10.000000 | 0.558824 | 0.519608 | 5 | 1 |
| 2023-03 | 14 | -7.250000 | 0.519868 | 0.582090 | 4 | 1 |
| 2023-04 | 13 | 8.650000 | 2.001931 | 1.853659 | 6 | 0 |
| 2023-05 | 9 | 12.833333 | 2.571429 | 2.022222 | 7 | 0 |
| 2023-06 | 7 | -6.666667 | 0.130435 | 0.166667 | 4 | 0 |
| 2023-07 | 10 | -14.333333 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 3 | -4.500000 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 7 | 0.766667 | 1.089494 | 1.365854 | 43 | 0 |
| 2023-10 | 8 | 2.700000 | 1.361607 | 1.838710 | 0 | 0 |
| 2023-11 | 12 | -9.866667 | 0.298578 | 0.295775 | 1 | 0 |
| 2023-12 | 12 | -3.633333 | 0.712401 | 0.843750 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK3_TOL2_MAXBARS36_SB2_TP8

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 120; dates/months 96/12; PF R/price 0.775817/0.808725; Net -28.800000 R; expectancy -0.240000 R; positive months 4/12; conditional DD 40.866667 R.
Accepted 124 = CLOSED 120 + EXCLUDED 4; SKIP 2; exclusion share 0.032258; conditional FLAT closures 116; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 6 | 0.500000 | 1.107143 | 1.705882 | 7 | 2 |
| 2023-02 | 19 | -8.500000 | 0.625000 | 0.578431 | 5 | 1 |
| 2023-03 | 14 | -7.250000 | 0.519868 | 0.582090 | 4 | 1 |
| 2023-04 | 13 | 10.150000 | 2.175676 | 2.000000 | 6 | 0 |
| 2023-05 | 9 | 15.833333 | 2.938776 | 2.311111 | 7 | 0 |
| 2023-06 | 7 | -6.666667 | 0.130435 | 0.166667 | 4 | 0 |
| 2023-07 | 10 | -14.333333 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 3 | -4.500000 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 7 | -3.233333 | 0.622568 | 0.780488 | 43 | 0 |
| 2023-10 | 8 | 2.700000 | 1.361607 | 1.838710 | 0 | 0 |
| 2023-11 | 12 | -9.866667 | 0.298578 | 0.295775 | 1 | 0 |
| 2023-12 | 12 | -3.633333 | 0.712401 | 0.843750 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK3_TOL2_MAXBARS36_SB2_TP9

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 119; dates/months 96/12; PF R/price 0.822394/0.850847; Net -22.550000 R; expectancy -0.189496 R; positive months 4/12; conditional DD 40.866667 R.
Accepted 123 = CLOSED 119 + EXCLUDED 4; SKIP 2; exclusion share 0.032520; conditional FLAT closures 115; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 6 | 0.500000 | 1.107143 | 1.705882 | 7 | 2 |
| 2023-02 | 18 | -6.750000 | 0.681102 | 0.625000 | 5 | 1 |
| 2023-03 | 14 | -7.250000 | 0.519868 | 0.582090 | 4 | 1 |
| 2023-04 | 13 | 11.650000 | 2.349421 | 2.146341 | 6 | 0 |
| 2023-05 | 9 | 18.833333 | 3.306122 | 2.600000 | 7 | 0 |
| 2023-06 | 7 | -6.666667 | 0.130435 | 0.166667 | 4 | 0 |
| 2023-07 | 10 | -14.333333 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 3 | -4.500000 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 7 | -3.233333 | 0.622568 | 0.780488 | 43 | 0 |
| 2023-10 | 8 | 2.700000 | 1.361607 | 1.838710 | 0 | 0 |
| 2023-11 | 12 | -9.866667 | 0.298578 | 0.295775 | 1 | 0 |
| 2023-12 | 12 | -3.633333 | 0.712401 | 0.843750 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK3_TOL2_MAXBARS36_SB2_TP10

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 119; dates/months 96/12; PF R/price 0.784983/0.820339; Net -27.300000 R; expectancy -0.229412 R; positive months 4/12; conditional DD 40.866667 R.
Accepted 123 = CLOSED 119 + EXCLUDED 4; SKIP 2; exclusion share 0.032520; conditional FLAT closures 115; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 6 | 0.500000 | 1.107143 | 1.705882 | 7 | 2 |
| 2023-02 | 18 | -6.750000 | 0.681102 | 0.625000 | 5 | 1 |
| 2023-03 | 14 | -7.250000 | 0.519868 | 0.582090 | 4 | 1 |
| 2023-04 | 13 | 3.900000 | 1.451737 | 1.390244 | 6 | 0 |
| 2023-05 | 9 | 21.833333 | 3.673469 | 2.888889 | 7 | 0 |
| 2023-06 | 7 | -6.666667 | 0.130435 | 0.166667 | 4 | 0 |
| 2023-07 | 10 | -14.333333 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 3 | -4.500000 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 7 | -3.233333 | 0.622568 | 0.780488 | 43 | 0 |
| 2023-10 | 8 | 2.700000 | 1.361607 | 1.838710 | 0 | 0 |
| 2023-11 | 12 | -9.866667 | 0.298578 | 0.295775 | 1 | 0 |
| 2023-12 | 12 | -3.633333 | 0.712401 | 0.843750 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK5_TOL1_MAXBARS24_SB1_TP2

**INSUFFICIENT_SAMPLE**; failed gates: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors; sample reasons: CLOSED_BELOW_100.
CLOSED 43; dates/months 40/12; PF R/price 0.175371/0.177778; Net -46.316667 R; expectancy -1.077132 R; positive months 0/12; conditional DD 46.316667 R.
Accepted 44 = CLOSED 43 + EXCLUDED 1; SKIP 0; exclusion share 0.022727; conditional FLAT closures 29; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 1 | -1.500000 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-02 | 6 | -6.633333 | 0.091324 | 0.080000 | 5 | 0 |
| 2023-03 | 7 | -5.800000 | 0.364964 | 0.277778 | 4 | 1 |
| 2023-04 | 8 | -4.266667 | 0.518797 | 0.605263 | 6 | 0 |
| 2023-05 | 5 | -7.266667 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-06 | 4 | -2.816667 | 0.307377 | 0.294118 | 4 | 0 |
| 2023-07 | 2 | -3.000000 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 2 | -3.066667 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 3 | -4.833333 | 0.000000 | 0.000000 | 43 | 0 |
| 2023-10 | 1 | -1.333333 | 0.000000 | 0.000000 | 0 | 0 |
| 2023-11 | 3 | -4.300000 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-12 | 1 | -1.500000 | 0.000000 | 0.000000 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK5_TOL1_MAXBARS24_SB1_TP3

**INSUFFICIENT_SAMPLE**; failed gates: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors; sample reasons: CLOSED_BELOW_100.
CLOSED 43; dates/months 40/12; PF R/price 0.188427/0.200000; Net -45.583333 R; expectancy -1.060078 R; positive months 0/12; conditional DD 45.583333 R.
Accepted 44 = CLOSED 43 + EXCLUDED 1; SKIP 0; exclusion share 0.022727; conditional FLAT closures 29; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 1 | -1.500000 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-02 | 6 | -6.633333 | 0.091324 | 0.080000 | 5 | 0 |
| 2023-03 | 7 | -6.466667 | 0.291971 | 0.222222 | 4 | 1 |
| 2023-04 | 8 | -2.866667 | 0.676692 | 0.789474 | 6 | 0 |
| 2023-05 | 5 | -7.266667 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-06 | 4 | -2.816667 | 0.307377 | 0.294118 | 4 | 0 |
| 2023-07 | 2 | -3.000000 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 2 | -3.066667 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 3 | -4.833333 | 0.000000 | 0.000000 | 43 | 0 |
| 2023-10 | 1 | -1.333333 | 0.000000 | 0.000000 | 0 | 0 |
| 2023-11 | 3 | -4.300000 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-12 | 1 | -1.500000 | 0.000000 | 0.000000 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK5_TOL1_MAXBARS24_SB1_TP4

**INSUFFICIENT_SAMPLE**; failed gates: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors; sample reasons: CLOSED_BELOW_100.
CLOSED 43; dates/months 40/12; PF R/price 0.213353/0.231111; Net -44.183333 R; expectancy -1.027519 R; positive months 0/12; conditional DD 44.183333 R.
Accepted 44 = CLOSED 43 + EXCLUDED 1; SKIP 0; exclusion share 0.022727; conditional FLAT closures 29; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 1 | -1.500000 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-02 | 6 | -6.633333 | 0.091324 | 0.080000 | 5 | 0 |
| 2023-03 | 7 | -6.466667 | 0.291971 | 0.222222 | 4 | 1 |
| 2023-04 | 8 | -1.466667 | 0.834586 | 0.973684 | 6 | 0 |
| 2023-05 | 5 | -7.266667 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-06 | 4 | -2.816667 | 0.307377 | 0.294118 | 4 | 0 |
| 2023-07 | 2 | -3.000000 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 2 | -3.066667 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 3 | -4.833333 | 0.000000 | 0.000000 | 43 | 0 |
| 2023-10 | 1 | -1.333333 | 0.000000 | 0.000000 | 0 | 0 |
| 2023-11 | 3 | -4.300000 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-12 | 1 | -1.500000 | 0.000000 | 0.000000 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK5_TOL1_MAXBARS24_SB1_TP5

**INSUFFICIENT_SAMPLE**; failed gates: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors; sample reasons: CLOSED_BELOW_100.
CLOSED 43; dates/months 40/12; PF R/price 0.238279/0.262222; Net -42.783333 R; expectancy -0.994961 R; positive months 0/12; conditional DD 42.783333 R.
Accepted 44 = CLOSED 43 + EXCLUDED 1; SKIP 0; exclusion share 0.022727; conditional FLAT closures 29; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 1 | -1.500000 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-02 | 6 | -6.633333 | 0.091324 | 0.080000 | 5 | 0 |
| 2023-03 | 7 | -6.466667 | 0.291971 | 0.222222 | 4 | 1 |
| 2023-04 | 8 | -0.066667 | 0.992481 | 1.157895 | 6 | 0 |
| 2023-05 | 5 | -7.266667 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-06 | 4 | -2.816667 | 0.307377 | 0.294118 | 4 | 0 |
| 2023-07 | 2 | -3.000000 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 2 | -3.066667 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 3 | -4.833333 | 0.000000 | 0.000000 | 43 | 0 |
| 2023-10 | 1 | -1.333333 | 0.000000 | 0.000000 | 0 | 0 |
| 2023-11 | 3 | -4.300000 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-12 | 1 | -1.500000 | 0.000000 | 0.000000 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK5_TOL1_MAXBARS24_SB1_TP6

**INSUFFICIENT_SAMPLE**; failed gates: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors; sample reasons: CLOSED_BELOW_100.
CLOSED 43; dates/months 40/12; PF R/price 0.224036/0.244444; Net -43.583333 R; expectancy -1.013566 R; positive months 0/12; conditional DD 43.583333 R.
Accepted 44 = CLOSED 43 + EXCLUDED 1; SKIP 0; exclusion share 0.022727; conditional FLAT closures 29; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 1 | -1.500000 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-02 | 6 | -6.633333 | 0.091324 | 0.080000 | 5 | 0 |
| 2023-03 | 7 | -6.466667 | 0.291971 | 0.222222 | 4 | 1 |
| 2023-04 | 8 | -0.866667 | 0.902256 | 1.052632 | 6 | 0 |
| 2023-05 | 5 | -7.266667 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-06 | 4 | -2.816667 | 0.307377 | 0.294118 | 4 | 0 |
| 2023-07 | 2 | -3.000000 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 2 | -3.066667 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 3 | -4.833333 | 0.000000 | 0.000000 | 43 | 0 |
| 2023-10 | 1 | -1.333333 | 0.000000 | 0.000000 | 0 | 0 |
| 2023-11 | 3 | -4.300000 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-12 | 1 | -1.500000 | 0.000000 | 0.000000 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK5_TOL1_MAXBARS24_SB1_TP7

**INSUFFICIENT_SAMPLE**; failed gates: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors; sample reasons: CLOSED_BELOW_100.
CLOSED 43; dates/months 40/12; PF R/price 0.224036/0.244444; Net -43.583333 R; expectancy -1.013566 R; positive months 0/12; conditional DD 43.583333 R.
Accepted 44 = CLOSED 43 + EXCLUDED 1; SKIP 0; exclusion share 0.022727; conditional FLAT closures 29; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 1 | -1.500000 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-02 | 6 | -6.633333 | 0.091324 | 0.080000 | 5 | 0 |
| 2023-03 | 7 | -6.466667 | 0.291971 | 0.222222 | 4 | 1 |
| 2023-04 | 8 | -0.866667 | 0.902256 | 1.052632 | 6 | 0 |
| 2023-05 | 5 | -7.266667 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-06 | 4 | -2.816667 | 0.307377 | 0.294118 | 4 | 0 |
| 2023-07 | 2 | -3.000000 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 2 | -3.066667 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 3 | -4.833333 | 0.000000 | 0.000000 | 43 | 0 |
| 2023-10 | 1 | -1.333333 | 0.000000 | 0.000000 | 0 | 0 |
| 2023-11 | 3 | -4.300000 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-12 | 1 | -1.500000 | 0.000000 | 0.000000 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK5_TOL1_MAXBARS24_SB1_TP8

**INSUFFICIENT_SAMPLE**; failed gates: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors; sample reasons: CLOSED_BELOW_100.
CLOSED 43; dates/months 40/12; PF R/price 0.224036/0.244444; Net -43.583333 R; expectancy -1.013566 R; positive months 0/12; conditional DD 43.583333 R.
Accepted 44 = CLOSED 43 + EXCLUDED 1; SKIP 0; exclusion share 0.022727; conditional FLAT closures 29; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 1 | -1.500000 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-02 | 6 | -6.633333 | 0.091324 | 0.080000 | 5 | 0 |
| 2023-03 | 7 | -6.466667 | 0.291971 | 0.222222 | 4 | 1 |
| 2023-04 | 8 | -0.866667 | 0.902256 | 1.052632 | 6 | 0 |
| 2023-05 | 5 | -7.266667 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-06 | 4 | -2.816667 | 0.307377 | 0.294118 | 4 | 0 |
| 2023-07 | 2 | -3.000000 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 2 | -3.066667 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 3 | -4.833333 | 0.000000 | 0.000000 | 43 | 0 |
| 2023-10 | 1 | -1.333333 | 0.000000 | 0.000000 | 0 | 0 |
| 2023-11 | 3 | -4.300000 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-12 | 1 | -1.500000 | 0.000000 | 0.000000 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK5_TOL1_MAXBARS24_SB1_TP9

**INSUFFICIENT_SAMPLE**; failed gates: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors; sample reasons: CLOSED_BELOW_100.
CLOSED 43; dates/months 40/12; PF R/price 0.224036/0.244444; Net -43.583333 R; expectancy -1.013566 R; positive months 0/12; conditional DD 43.583333 R.
Accepted 44 = CLOSED 43 + EXCLUDED 1; SKIP 0; exclusion share 0.022727; conditional FLAT closures 29; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 1 | -1.500000 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-02 | 6 | -6.633333 | 0.091324 | 0.080000 | 5 | 0 |
| 2023-03 | 7 | -6.466667 | 0.291971 | 0.222222 | 4 | 1 |
| 2023-04 | 8 | -0.866667 | 0.902256 | 1.052632 | 6 | 0 |
| 2023-05 | 5 | -7.266667 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-06 | 4 | -2.816667 | 0.307377 | 0.294118 | 4 | 0 |
| 2023-07 | 2 | -3.000000 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 2 | -3.066667 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 3 | -4.833333 | 0.000000 | 0.000000 | 43 | 0 |
| 2023-10 | 1 | -1.333333 | 0.000000 | 0.000000 | 0 | 0 |
| 2023-11 | 3 | -4.300000 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-12 | 1 | -1.500000 | 0.000000 | 0.000000 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK5_TOL1_MAXBARS24_SB1_TP10

**INSUFFICIENT_SAMPLE**; failed gates: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors; sample reasons: CLOSED_BELOW_100.
CLOSED 43; dates/months 40/12; PF R/price 0.224036/0.244444; Net -43.583333 R; expectancy -1.013566 R; positive months 0/12; conditional DD 43.583333 R.
Accepted 44 = CLOSED 43 + EXCLUDED 1; SKIP 0; exclusion share 0.022727; conditional FLAT closures 29; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 1 | -1.500000 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-02 | 6 | -6.633333 | 0.091324 | 0.080000 | 5 | 0 |
| 2023-03 | 7 | -6.466667 | 0.291971 | 0.222222 | 4 | 1 |
| 2023-04 | 8 | -0.866667 | 0.902256 | 1.052632 | 6 | 0 |
| 2023-05 | 5 | -7.266667 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-06 | 4 | -2.816667 | 0.307377 | 0.294118 | 4 | 0 |
| 2023-07 | 2 | -3.000000 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 2 | -3.066667 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 3 | -4.833333 | 0.000000 | 0.000000 | 43 | 0 |
| 2023-10 | 1 | -1.333333 | 0.000000 | 0.000000 | 0 | 0 |
| 2023-11 | 3 | -4.300000 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-12 | 1 | -1.500000 | 0.000000 | 0.000000 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK5_TOL1_MAXBARS24_SB2_TP2

**INSUFFICIENT_SAMPLE**; failed gates: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: CLOSED_BELOW_100.
CLOSED 51; dates/months 45/12; PF R/price 0.376661/0.410646; Net -35.966667 R; expectancy -0.705229 R; positive months 1/12; conditional DD 35.966667 R.
Accepted 52 = CLOSED 51 + EXCLUDED 1; SKIP 0; exclusion share 0.019231; conditional FLAT closures 34; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 1 | -1.400000 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-02 | 7 | -3.533333 | 0.482927 | 0.592593 | 5 | 0 |
| 2023-03 | 9 | -0.100000 | 0.988764 | 0.974359 | 4 | 1 |
| 2023-04 | 8 | 3.066667 | 1.550898 | 1.689655 | 6 | 0 |
| 2023-05 | 5 | -6.500000 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-06 | 5 | -4.333333 | 0.187500 | 0.208333 | 4 | 0 |
| 2023-07 | 5 | -7.800000 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 2 | -2.833333 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 3 | -4.400000 | 0.000000 | 0.000000 | 43 | 0 |
| 2023-10 | 2 | -2.666667 | 0.000000 | 0.000000 | 0 | 0 |
| 2023-11 | 3 | -4.066667 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-12 | 1 | -1.400000 | 0.000000 | 0.000000 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK5_TOL1_MAXBARS24_SB2_TP3

**INSUFFICIENT_SAMPLE**; failed gates: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors; sample reasons: CLOSED_BELOW_100.
CLOSED 50; dates/months 44/12; PF R/price 0.219239/0.257353; Net -46.533333 R; expectancy -0.930667 R; positive months 1/12; conditional DD 46.533333 R.
Accepted 52 = CLOSED 50 + EXCLUDED 2; SKIP 0; exclusion share 0.038462; conditional FLAT closures 45; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 1 | -1.400000 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-02 | 6 | -6.333333 | 0.073171 | 0.074074 | 5 | 1 |
| 2023-03 | 9 | -5.000000 | 0.468085 | 0.487805 | 4 | 1 |
| 2023-04 | 8 | 0.200000 | 1.028708 | 1.194444 | 6 | 0 |
| 2023-05 | 5 | -6.500000 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-06 | 5 | -4.333333 | 0.187500 | 0.208333 | 4 | 0 |
| 2023-07 | 5 | -7.800000 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 2 | -2.833333 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 3 | -4.400000 | 0.000000 | 0.000000 | 43 | 0 |
| 2023-10 | 2 | -2.666667 | 0.000000 | 0.000000 | 0 | 0 |
| 2023-11 | 3 | -4.066667 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-12 | 1 | -1.400000 | 0.000000 | 0.000000 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK5_TOL1_MAXBARS24_SB2_TP4

**INSUFFICIENT_SAMPLE**; failed gates: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors; sample reasons: CLOSED_BELOW_100.
CLOSED 50; dates/months 44/12; PF R/price 0.241611/0.286765; Net -45.200000 R; expectancy -0.904000 R; positive months 1/12; conditional DD 45.200000 R.
Accepted 52 = CLOSED 50 + EXCLUDED 2; SKIP 0; exclusion share 0.038462; conditional FLAT closures 45; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 1 | -1.400000 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-02 | 6 | -6.333333 | 0.073171 | 0.074074 | 5 | 1 |
| 2023-03 | 9 | -5.000000 | 0.468085 | 0.487805 | 4 | 1 |
| 2023-04 | 8 | 1.533333 | 1.220096 | 1.416667 | 6 | 0 |
| 2023-05 | 5 | -6.500000 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-06 | 5 | -4.333333 | 0.187500 | 0.208333 | 4 | 0 |
| 2023-07 | 5 | -7.800000 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 2 | -2.833333 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 3 | -4.400000 | 0.000000 | 0.000000 | 43 | 0 |
| 2023-10 | 2 | -2.666667 | 0.000000 | 0.000000 | 0 | 0 |
| 2023-11 | 3 | -4.066667 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-12 | 1 | -1.400000 | 0.000000 | 0.000000 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK5_TOL1_MAXBARS24_SB2_TP5

**INSUFFICIENT_SAMPLE**; failed gates: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors; sample reasons: CLOSED_BELOW_100.
CLOSED 50; dates/months 44/12; PF R/price 0.238814/0.283088; Net -45.366667 R; expectancy -0.907333 R; positive months 1/12; conditional DD 45.366667 R.
Accepted 52 = CLOSED 50 + EXCLUDED 2; SKIP 0; exclusion share 0.038462; conditional FLAT closures 45; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 1 | -1.400000 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-02 | 6 | -6.333333 | 0.073171 | 0.074074 | 5 | 1 |
| 2023-03 | 9 | -5.000000 | 0.468085 | 0.487805 | 4 | 1 |
| 2023-04 | 8 | 1.366667 | 1.196172 | 1.388889 | 6 | 0 |
| 2023-05 | 5 | -6.500000 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-06 | 5 | -4.333333 | 0.187500 | 0.208333 | 4 | 0 |
| 2023-07 | 5 | -7.800000 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 2 | -2.833333 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 3 | -4.400000 | 0.000000 | 0.000000 | 43 | 0 |
| 2023-10 | 2 | -2.666667 | 0.000000 | 0.000000 | 0 | 0 |
| 2023-11 | 3 | -4.066667 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-12 | 1 | -1.400000 | 0.000000 | 0.000000 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK5_TOL1_MAXBARS24_SB2_TP6

**INSUFFICIENT_SAMPLE**; failed gates: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors; sample reasons: CLOSED_BELOW_100.
CLOSED 50; dates/months 44/12; PF R/price 0.238814/0.283088; Net -45.366667 R; expectancy -0.907333 R; positive months 1/12; conditional DD 45.366667 R.
Accepted 52 = CLOSED 50 + EXCLUDED 2; SKIP 0; exclusion share 0.038462; conditional FLAT closures 45; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 1 | -1.400000 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-02 | 6 | -6.333333 | 0.073171 | 0.074074 | 5 | 1 |
| 2023-03 | 9 | -5.000000 | 0.468085 | 0.487805 | 4 | 1 |
| 2023-04 | 8 | 1.366667 | 1.196172 | 1.388889 | 6 | 0 |
| 2023-05 | 5 | -6.500000 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-06 | 5 | -4.333333 | 0.187500 | 0.208333 | 4 | 0 |
| 2023-07 | 5 | -7.800000 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 2 | -2.833333 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 3 | -4.400000 | 0.000000 | 0.000000 | 43 | 0 |
| 2023-10 | 2 | -2.666667 | 0.000000 | 0.000000 | 0 | 0 |
| 2023-11 | 3 | -4.066667 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-12 | 1 | -1.400000 | 0.000000 | 0.000000 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK5_TOL1_MAXBARS24_SB2_TP7

**INSUFFICIENT_SAMPLE**; failed gates: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors; sample reasons: CLOSED_BELOW_100.
CLOSED 50; dates/months 44/12; PF R/price 0.238814/0.283088; Net -45.366667 R; expectancy -0.907333 R; positive months 1/12; conditional DD 45.366667 R.
Accepted 52 = CLOSED 50 + EXCLUDED 2; SKIP 0; exclusion share 0.038462; conditional FLAT closures 45; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 1 | -1.400000 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-02 | 6 | -6.333333 | 0.073171 | 0.074074 | 5 | 1 |
| 2023-03 | 9 | -5.000000 | 0.468085 | 0.487805 | 4 | 1 |
| 2023-04 | 8 | 1.366667 | 1.196172 | 1.388889 | 6 | 0 |
| 2023-05 | 5 | -6.500000 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-06 | 5 | -4.333333 | 0.187500 | 0.208333 | 4 | 0 |
| 2023-07 | 5 | -7.800000 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 2 | -2.833333 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 3 | -4.400000 | 0.000000 | 0.000000 | 43 | 0 |
| 2023-10 | 2 | -2.666667 | 0.000000 | 0.000000 | 0 | 0 |
| 2023-11 | 3 | -4.066667 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-12 | 1 | -1.400000 | 0.000000 | 0.000000 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK5_TOL1_MAXBARS24_SB2_TP8

**INSUFFICIENT_SAMPLE**; failed gates: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors; sample reasons: CLOSED_BELOW_100.
CLOSED 50; dates/months 44/12; PF R/price 0.238814/0.283088; Net -45.366667 R; expectancy -0.907333 R; positive months 1/12; conditional DD 45.366667 R.
Accepted 52 = CLOSED 50 + EXCLUDED 2; SKIP 0; exclusion share 0.038462; conditional FLAT closures 45; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 1 | -1.400000 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-02 | 6 | -6.333333 | 0.073171 | 0.074074 | 5 | 1 |
| 2023-03 | 9 | -5.000000 | 0.468085 | 0.487805 | 4 | 1 |
| 2023-04 | 8 | 1.366667 | 1.196172 | 1.388889 | 6 | 0 |
| 2023-05 | 5 | -6.500000 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-06 | 5 | -4.333333 | 0.187500 | 0.208333 | 4 | 0 |
| 2023-07 | 5 | -7.800000 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 2 | -2.833333 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 3 | -4.400000 | 0.000000 | 0.000000 | 43 | 0 |
| 2023-10 | 2 | -2.666667 | 0.000000 | 0.000000 | 0 | 0 |
| 2023-11 | 3 | -4.066667 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-12 | 1 | -1.400000 | 0.000000 | 0.000000 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK5_TOL1_MAXBARS24_SB2_TP9

**INSUFFICIENT_SAMPLE**; failed gates: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors; sample reasons: CLOSED_BELOW_100.
CLOSED 50; dates/months 44/12; PF R/price 0.238814/0.283088; Net -45.366667 R; expectancy -0.907333 R; positive months 1/12; conditional DD 45.366667 R.
Accepted 52 = CLOSED 50 + EXCLUDED 2; SKIP 0; exclusion share 0.038462; conditional FLAT closures 45; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 1 | -1.400000 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-02 | 6 | -6.333333 | 0.073171 | 0.074074 | 5 | 1 |
| 2023-03 | 9 | -5.000000 | 0.468085 | 0.487805 | 4 | 1 |
| 2023-04 | 8 | 1.366667 | 1.196172 | 1.388889 | 6 | 0 |
| 2023-05 | 5 | -6.500000 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-06 | 5 | -4.333333 | 0.187500 | 0.208333 | 4 | 0 |
| 2023-07 | 5 | -7.800000 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 2 | -2.833333 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 3 | -4.400000 | 0.000000 | 0.000000 | 43 | 0 |
| 2023-10 | 2 | -2.666667 | 0.000000 | 0.000000 | 0 | 0 |
| 2023-11 | 3 | -4.066667 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-12 | 1 | -1.400000 | 0.000000 | 0.000000 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK5_TOL1_MAXBARS24_SB2_TP10

**INSUFFICIENT_SAMPLE**; failed gates: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors; sample reasons: CLOSED_BELOW_100.
CLOSED 50; dates/months 44/12; PF R/price 0.238814/0.283088; Net -45.366667 R; expectancy -0.907333 R; positive months 1/12; conditional DD 45.366667 R.
Accepted 52 = CLOSED 50 + EXCLUDED 2; SKIP 0; exclusion share 0.038462; conditional FLAT closures 45; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 1 | -1.400000 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-02 | 6 | -6.333333 | 0.073171 | 0.074074 | 5 | 1 |
| 2023-03 | 9 | -5.000000 | 0.468085 | 0.487805 | 4 | 1 |
| 2023-04 | 8 | 1.366667 | 1.196172 | 1.388889 | 6 | 0 |
| 2023-05 | 5 | -6.500000 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-06 | 5 | -4.333333 | 0.187500 | 0.208333 | 4 | 0 |
| 2023-07 | 5 | -7.800000 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 2 | -2.833333 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 3 | -4.400000 | 0.000000 | 0.000000 | 43 | 0 |
| 2023-10 | 2 | -2.666667 | 0.000000 | 0.000000 | 0 | 0 |
| 2023-11 | 3 | -4.066667 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-12 | 1 | -1.400000 | 0.000000 | 0.000000 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK5_TOL1_MAXBARS36_SB1_TP2

**INSUFFICIENT_SAMPLE**; failed gates: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors; sample reasons: CLOSED_BELOW_100.
CLOSED 48; dates/months 45/12; PF R/price 0.173406/0.178862; Net -50.766667 R; expectancy -1.057639 R; positive months 0/12; conditional DD 50.766667 R.
Accepted 49 = CLOSED 48 + EXCLUDED 1; SKIP 0; exclusion share 0.020408; conditional FLAT closures 34; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 1 | -1.500000 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-02 | 6 | -6.633333 | 0.091324 | 0.080000 | 5 | 0 |
| 2023-03 | 7 | -5.800000 | 0.364964 | 0.277778 | 4 | 1 |
| 2023-04 | 9 | -3.300000 | 0.620690 | 0.692308 | 6 | 0 |
| 2023-05 | 6 | -8.016667 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-06 | 5 | -4.316667 | 0.224551 | 0.217391 | 4 | 0 |
| 2023-07 | 2 | -3.000000 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 2 | -3.066667 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 5 | -8.000000 | 0.000000 | 0.000000 | 43 | 0 |
| 2023-10 | 1 | -1.333333 | 0.000000 | 0.000000 | 0 | 0 |
| 2023-11 | 3 | -4.300000 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-12 | 1 | -1.500000 | 0.000000 | 0.000000 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK5_TOL1_MAXBARS36_SB1_TP3

**INSUFFICIENT_SAMPLE**; failed gates: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors; sample reasons: CLOSED_BELOW_100.
CLOSED 48; dates/months 45/12; PF R/price 0.185346/0.199187; Net -50.033333 R; expectancy -1.042361 R; positive months 0/12; conditional DD 50.033333 R.
Accepted 49 = CLOSED 48 + EXCLUDED 1; SKIP 0; exclusion share 0.020408; conditional FLAT closures 34; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 1 | -1.500000 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-02 | 6 | -6.633333 | 0.091324 | 0.080000 | 5 | 0 |
| 2023-03 | 7 | -6.466667 | 0.291971 | 0.222222 | 4 | 1 |
| 2023-04 | 9 | -1.900000 | 0.781609 | 0.871795 | 6 | 0 |
| 2023-05 | 6 | -8.016667 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-06 | 5 | -4.316667 | 0.224551 | 0.217391 | 4 | 0 |
| 2023-07 | 2 | -3.000000 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 2 | -3.066667 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 5 | -8.000000 | 0.000000 | 0.000000 | 43 | 0 |
| 2023-10 | 1 | -1.333333 | 0.000000 | 0.000000 | 0 | 0 |
| 2023-11 | 3 | -4.300000 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-12 | 1 | -1.500000 | 0.000000 | 0.000000 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK5_TOL1_MAXBARS36_SB1_TP4

**INSUFFICIENT_SAMPLE**; failed gates: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors; sample reasons: CLOSED_BELOW_100.
CLOSED 48; dates/months 45/12; PF R/price 0.208141/0.227642; Net -48.633333 R; expectancy -1.013194 R; positive months 0/12; conditional DD 48.633333 R.
Accepted 49 = CLOSED 48 + EXCLUDED 1; SKIP 0; exclusion share 0.020408; conditional FLAT closures 34; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 1 | -1.500000 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-02 | 6 | -6.633333 | 0.091324 | 0.080000 | 5 | 0 |
| 2023-03 | 7 | -6.466667 | 0.291971 | 0.222222 | 4 | 1 |
| 2023-04 | 9 | -0.500000 | 0.942529 | 1.051282 | 6 | 0 |
| 2023-05 | 6 | -8.016667 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-06 | 5 | -4.316667 | 0.224551 | 0.217391 | 4 | 0 |
| 2023-07 | 2 | -3.000000 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 2 | -3.066667 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 5 | -8.000000 | 0.000000 | 0.000000 | 43 | 0 |
| 2023-10 | 1 | -1.333333 | 0.000000 | 0.000000 | 0 | 0 |
| 2023-11 | 3 | -4.300000 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-12 | 1 | -1.500000 | 0.000000 | 0.000000 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK5_TOL1_MAXBARS36_SB1_TP5

**INSUFFICIENT_SAMPLE**; failed gates: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors; sample reasons: CLOSED_BELOW_100.
CLOSED 48; dates/months 45/12; PF R/price 0.230936/0.256098; Net -47.233333 R; expectancy -0.984028 R; positive months 1/12; conditional DD 47.233333 R.
Accepted 49 = CLOSED 48 + EXCLUDED 1; SKIP 0; exclusion share 0.020408; conditional FLAT closures 34; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 1 | -1.500000 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-02 | 6 | -6.633333 | 0.091324 | 0.080000 | 5 | 0 |
| 2023-03 | 7 | -6.466667 | 0.291971 | 0.222222 | 4 | 1 |
| 2023-04 | 9 | 0.900000 | 1.103448 | 1.230769 | 6 | 0 |
| 2023-05 | 6 | -8.016667 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-06 | 5 | -4.316667 | 0.224551 | 0.217391 | 4 | 0 |
| 2023-07 | 2 | -3.000000 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 2 | -3.066667 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 5 | -8.000000 | 0.000000 | 0.000000 | 43 | 0 |
| 2023-10 | 1 | -1.333333 | 0.000000 | 0.000000 | 0 | 0 |
| 2023-11 | 3 | -4.300000 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-12 | 1 | -1.500000 | 0.000000 | 0.000000 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK5_TOL1_MAXBARS36_SB1_TP6

**INSUFFICIENT_SAMPLE**; failed gates: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors; sample reasons: CLOSED_BELOW_100.
CLOSED 48; dates/months 45/12; PF R/price 0.217910/0.239837; Net -48.033333 R; expectancy -1.000694 R; positive months 1/12; conditional DD 48.033333 R.
Accepted 49 = CLOSED 48 + EXCLUDED 1; SKIP 0; exclusion share 0.020408; conditional FLAT closures 34; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 1 | -1.500000 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-02 | 6 | -6.633333 | 0.091324 | 0.080000 | 5 | 0 |
| 2023-03 | 7 | -6.466667 | 0.291971 | 0.222222 | 4 | 1 |
| 2023-04 | 9 | 0.100000 | 1.011494 | 1.128205 | 6 | 0 |
| 2023-05 | 6 | -8.016667 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-06 | 5 | -4.316667 | 0.224551 | 0.217391 | 4 | 0 |
| 2023-07 | 2 | -3.000000 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 2 | -3.066667 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 5 | -8.000000 | 0.000000 | 0.000000 | 43 | 0 |
| 2023-10 | 1 | -1.333333 | 0.000000 | 0.000000 | 0 | 0 |
| 2023-11 | 3 | -4.300000 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-12 | 1 | -1.500000 | 0.000000 | 0.000000 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK5_TOL1_MAXBARS36_SB1_TP7

**INSUFFICIENT_SAMPLE**; failed gates: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors; sample reasons: CLOSED_BELOW_100.
CLOSED 48; dates/months 45/12; PF R/price 0.217910/0.239837; Net -48.033333 R; expectancy -1.000694 R; positive months 1/12; conditional DD 48.033333 R.
Accepted 49 = CLOSED 48 + EXCLUDED 1; SKIP 0; exclusion share 0.020408; conditional FLAT closures 34; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 1 | -1.500000 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-02 | 6 | -6.633333 | 0.091324 | 0.080000 | 5 | 0 |
| 2023-03 | 7 | -6.466667 | 0.291971 | 0.222222 | 4 | 1 |
| 2023-04 | 9 | 0.100000 | 1.011494 | 1.128205 | 6 | 0 |
| 2023-05 | 6 | -8.016667 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-06 | 5 | -4.316667 | 0.224551 | 0.217391 | 4 | 0 |
| 2023-07 | 2 | -3.000000 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 2 | -3.066667 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 5 | -8.000000 | 0.000000 | 0.000000 | 43 | 0 |
| 2023-10 | 1 | -1.333333 | 0.000000 | 0.000000 | 0 | 0 |
| 2023-11 | 3 | -4.300000 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-12 | 1 | -1.500000 | 0.000000 | 0.000000 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK5_TOL1_MAXBARS36_SB1_TP8

**INSUFFICIENT_SAMPLE**; failed gates: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors; sample reasons: CLOSED_BELOW_100.
CLOSED 48; dates/months 45/12; PF R/price 0.217910/0.239837; Net -48.033333 R; expectancy -1.000694 R; positive months 1/12; conditional DD 48.033333 R.
Accepted 49 = CLOSED 48 + EXCLUDED 1; SKIP 0; exclusion share 0.020408; conditional FLAT closures 34; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 1 | -1.500000 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-02 | 6 | -6.633333 | 0.091324 | 0.080000 | 5 | 0 |
| 2023-03 | 7 | -6.466667 | 0.291971 | 0.222222 | 4 | 1 |
| 2023-04 | 9 | 0.100000 | 1.011494 | 1.128205 | 6 | 0 |
| 2023-05 | 6 | -8.016667 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-06 | 5 | -4.316667 | 0.224551 | 0.217391 | 4 | 0 |
| 2023-07 | 2 | -3.000000 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 2 | -3.066667 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 5 | -8.000000 | 0.000000 | 0.000000 | 43 | 0 |
| 2023-10 | 1 | -1.333333 | 0.000000 | 0.000000 | 0 | 0 |
| 2023-11 | 3 | -4.300000 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-12 | 1 | -1.500000 | 0.000000 | 0.000000 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK5_TOL1_MAXBARS36_SB1_TP9

**INSUFFICIENT_SAMPLE**; failed gates: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors; sample reasons: CLOSED_BELOW_100.
CLOSED 48; dates/months 45/12; PF R/price 0.217910/0.239837; Net -48.033333 R; expectancy -1.000694 R; positive months 1/12; conditional DD 48.033333 R.
Accepted 49 = CLOSED 48 + EXCLUDED 1; SKIP 0; exclusion share 0.020408; conditional FLAT closures 34; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 1 | -1.500000 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-02 | 6 | -6.633333 | 0.091324 | 0.080000 | 5 | 0 |
| 2023-03 | 7 | -6.466667 | 0.291971 | 0.222222 | 4 | 1 |
| 2023-04 | 9 | 0.100000 | 1.011494 | 1.128205 | 6 | 0 |
| 2023-05 | 6 | -8.016667 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-06 | 5 | -4.316667 | 0.224551 | 0.217391 | 4 | 0 |
| 2023-07 | 2 | -3.000000 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 2 | -3.066667 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 5 | -8.000000 | 0.000000 | 0.000000 | 43 | 0 |
| 2023-10 | 1 | -1.333333 | 0.000000 | 0.000000 | 0 | 0 |
| 2023-11 | 3 | -4.300000 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-12 | 1 | -1.500000 | 0.000000 | 0.000000 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK5_TOL1_MAXBARS36_SB1_TP10

**INSUFFICIENT_SAMPLE**; failed gates: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors; sample reasons: CLOSED_BELOW_100.
CLOSED 48; dates/months 45/12; PF R/price 0.217910/0.239837; Net -48.033333 R; expectancy -1.000694 R; positive months 1/12; conditional DD 48.033333 R.
Accepted 49 = CLOSED 48 + EXCLUDED 1; SKIP 0; exclusion share 0.020408; conditional FLAT closures 34; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 1 | -1.500000 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-02 | 6 | -6.633333 | 0.091324 | 0.080000 | 5 | 0 |
| 2023-03 | 7 | -6.466667 | 0.291971 | 0.222222 | 4 | 1 |
| 2023-04 | 9 | 0.100000 | 1.011494 | 1.128205 | 6 | 0 |
| 2023-05 | 6 | -8.016667 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-06 | 5 | -4.316667 | 0.224551 | 0.217391 | 4 | 0 |
| 2023-07 | 2 | -3.000000 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 2 | -3.066667 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 5 | -8.000000 | 0.000000 | 0.000000 | 43 | 0 |
| 2023-10 | 1 | -1.333333 | 0.000000 | 0.000000 | 0 | 0 |
| 2023-11 | 3 | -4.300000 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-12 | 1 | -1.500000 | 0.000000 | 0.000000 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK5_TOL1_MAXBARS36_SB2_TP2

**INSUFFICIENT_SAMPLE**; failed gates: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: CLOSED_BELOW_100.
CLOSED 55; dates/months 50/12; PF R/price 0.376893/0.407273; Net -37.033333 R; expectancy -0.673333 R; positive months 1/12; conditional DD 37.233333 R.
Accepted 56 = CLOSED 55 + EXCLUDED 1; SKIP 0; exclusion share 0.017857; conditional FLAT closures 38; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 1 | -1.400000 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-02 | 7 | -3.533333 | 0.482927 | 0.592593 | 5 | 0 |
| 2023-03 | 9 | -0.100000 | 0.988764 | 0.974359 | 4 | 1 |
| 2023-04 | 8 | 5.233333 | 2.286885 | 2.304348 | 6 | 0 |
| 2023-05 | 6 | -7.100000 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-06 | 7 | -5.733333 | 0.148515 | 0.161290 | 4 | 0 |
| 2023-07 | 4 | -6.133333 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 2 | -2.833333 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 5 | -7.300000 | 0.000000 | 0.000000 | 43 | 0 |
| 2023-10 | 2 | -2.666667 | 0.000000 | 0.000000 | 0 | 0 |
| 2023-11 | 3 | -4.066667 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-12 | 1 | -1.400000 | 0.000000 | 0.000000 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK5_TOL1_MAXBARS36_SB2_TP3

**INSUFFICIENT_SAMPLE**; failed gates: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors; sample reasons: CLOSED_BELOW_100.
CLOSED 54; dates/months 49/12; PF R/price 0.223913/0.260563; Net -47.600000 R; expectancy -0.881481 R; positive months 1/12; conditional DD 47.600000 R.
Accepted 56 = CLOSED 54 + EXCLUDED 2; SKIP 0; exclusion share 0.035714; conditional FLAT closures 49; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 1 | -1.400000 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-02 | 6 | -6.333333 | 0.073171 | 0.074074 | 5 | 1 |
| 2023-03 | 9 | -5.000000 | 0.468085 | 0.487805 | 4 | 1 |
| 2023-04 | 8 | 2.366667 | 1.432927 | 1.566667 | 6 | 0 |
| 2023-05 | 6 | -7.100000 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-06 | 7 | -5.733333 | 0.148515 | 0.161290 | 4 | 0 |
| 2023-07 | 4 | -6.133333 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 2 | -2.833333 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 5 | -7.300000 | 0.000000 | 0.000000 | 43 | 0 |
| 2023-10 | 2 | -2.666667 | 0.000000 | 0.000000 | 0 | 0 |
| 2023-11 | 3 | -4.066667 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-12 | 1 | -1.400000 | 0.000000 | 0.000000 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK5_TOL1_MAXBARS36_SB2_TP4

**INSUFFICIENT_SAMPLE**; failed gates: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors; sample reasons: CLOSED_BELOW_100.
CLOSED 54; dates/months 49/12; PF R/price 0.245652/0.288732; Net -46.266667 R; expectancy -0.856790 R; positive months 1/12; conditional DD 46.266667 R.
Accepted 56 = CLOSED 54 + EXCLUDED 2; SKIP 0; exclusion share 0.035714; conditional FLAT closures 49; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 1 | -1.400000 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-02 | 6 | -6.333333 | 0.073171 | 0.074074 | 5 | 1 |
| 2023-03 | 9 | -5.000000 | 0.468085 | 0.487805 | 4 | 1 |
| 2023-04 | 8 | 3.700000 | 1.676829 | 1.833333 | 6 | 0 |
| 2023-05 | 6 | -7.100000 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-06 | 7 | -5.733333 | 0.148515 | 0.161290 | 4 | 0 |
| 2023-07 | 4 | -6.133333 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 2 | -2.833333 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 5 | -7.300000 | 0.000000 | 0.000000 | 43 | 0 |
| 2023-10 | 2 | -2.666667 | 0.000000 | 0.000000 | 0 | 0 |
| 2023-11 | 3 | -4.066667 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-12 | 1 | -1.400000 | 0.000000 | 0.000000 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK5_TOL1_MAXBARS36_SB2_TP5

**INSUFFICIENT_SAMPLE**; failed gates: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors; sample reasons: CLOSED_BELOW_100.
CLOSED 54; dates/months 49/12; PF R/price 0.242935/0.285211; Net -46.433333 R; expectancy -0.859877 R; positive months 1/12; conditional DD 46.433333 R.
Accepted 56 = CLOSED 54 + EXCLUDED 2; SKIP 0; exclusion share 0.035714; conditional FLAT closures 49; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 1 | -1.400000 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-02 | 6 | -6.333333 | 0.073171 | 0.074074 | 5 | 1 |
| 2023-03 | 9 | -5.000000 | 0.468085 | 0.487805 | 4 | 1 |
| 2023-04 | 8 | 3.533333 | 1.646341 | 1.800000 | 6 | 0 |
| 2023-05 | 6 | -7.100000 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-06 | 7 | -5.733333 | 0.148515 | 0.161290 | 4 | 0 |
| 2023-07 | 4 | -6.133333 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 2 | -2.833333 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 5 | -7.300000 | 0.000000 | 0.000000 | 43 | 0 |
| 2023-10 | 2 | -2.666667 | 0.000000 | 0.000000 | 0 | 0 |
| 2023-11 | 3 | -4.066667 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-12 | 1 | -1.400000 | 0.000000 | 0.000000 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK5_TOL1_MAXBARS36_SB2_TP6

**INSUFFICIENT_SAMPLE**; failed gates: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors; sample reasons: CLOSED_BELOW_100.
CLOSED 54; dates/months 49/12; PF R/price 0.242935/0.285211; Net -46.433333 R; expectancy -0.859877 R; positive months 1/12; conditional DD 46.433333 R.
Accepted 56 = CLOSED 54 + EXCLUDED 2; SKIP 0; exclusion share 0.035714; conditional FLAT closures 49; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 1 | -1.400000 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-02 | 6 | -6.333333 | 0.073171 | 0.074074 | 5 | 1 |
| 2023-03 | 9 | -5.000000 | 0.468085 | 0.487805 | 4 | 1 |
| 2023-04 | 8 | 3.533333 | 1.646341 | 1.800000 | 6 | 0 |
| 2023-05 | 6 | -7.100000 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-06 | 7 | -5.733333 | 0.148515 | 0.161290 | 4 | 0 |
| 2023-07 | 4 | -6.133333 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 2 | -2.833333 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 5 | -7.300000 | 0.000000 | 0.000000 | 43 | 0 |
| 2023-10 | 2 | -2.666667 | 0.000000 | 0.000000 | 0 | 0 |
| 2023-11 | 3 | -4.066667 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-12 | 1 | -1.400000 | 0.000000 | 0.000000 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK5_TOL1_MAXBARS36_SB2_TP7

**INSUFFICIENT_SAMPLE**; failed gates: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors; sample reasons: CLOSED_BELOW_100.
CLOSED 54; dates/months 49/12; PF R/price 0.242935/0.285211; Net -46.433333 R; expectancy -0.859877 R; positive months 1/12; conditional DD 46.433333 R.
Accepted 56 = CLOSED 54 + EXCLUDED 2; SKIP 0; exclusion share 0.035714; conditional FLAT closures 49; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 1 | -1.400000 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-02 | 6 | -6.333333 | 0.073171 | 0.074074 | 5 | 1 |
| 2023-03 | 9 | -5.000000 | 0.468085 | 0.487805 | 4 | 1 |
| 2023-04 | 8 | 3.533333 | 1.646341 | 1.800000 | 6 | 0 |
| 2023-05 | 6 | -7.100000 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-06 | 7 | -5.733333 | 0.148515 | 0.161290 | 4 | 0 |
| 2023-07 | 4 | -6.133333 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 2 | -2.833333 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 5 | -7.300000 | 0.000000 | 0.000000 | 43 | 0 |
| 2023-10 | 2 | -2.666667 | 0.000000 | 0.000000 | 0 | 0 |
| 2023-11 | 3 | -4.066667 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-12 | 1 | -1.400000 | 0.000000 | 0.000000 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK5_TOL1_MAXBARS36_SB2_TP8

**INSUFFICIENT_SAMPLE**; failed gates: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors; sample reasons: CLOSED_BELOW_100.
CLOSED 54; dates/months 49/12; PF R/price 0.242935/0.285211; Net -46.433333 R; expectancy -0.859877 R; positive months 1/12; conditional DD 46.433333 R.
Accepted 56 = CLOSED 54 + EXCLUDED 2; SKIP 0; exclusion share 0.035714; conditional FLAT closures 49; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 1 | -1.400000 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-02 | 6 | -6.333333 | 0.073171 | 0.074074 | 5 | 1 |
| 2023-03 | 9 | -5.000000 | 0.468085 | 0.487805 | 4 | 1 |
| 2023-04 | 8 | 3.533333 | 1.646341 | 1.800000 | 6 | 0 |
| 2023-05 | 6 | -7.100000 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-06 | 7 | -5.733333 | 0.148515 | 0.161290 | 4 | 0 |
| 2023-07 | 4 | -6.133333 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 2 | -2.833333 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 5 | -7.300000 | 0.000000 | 0.000000 | 43 | 0 |
| 2023-10 | 2 | -2.666667 | 0.000000 | 0.000000 | 0 | 0 |
| 2023-11 | 3 | -4.066667 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-12 | 1 | -1.400000 | 0.000000 | 0.000000 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK5_TOL1_MAXBARS36_SB2_TP9

**INSUFFICIENT_SAMPLE**; failed gates: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors; sample reasons: CLOSED_BELOW_100.
CLOSED 54; dates/months 49/12; PF R/price 0.242935/0.285211; Net -46.433333 R; expectancy -0.859877 R; positive months 1/12; conditional DD 46.433333 R.
Accepted 56 = CLOSED 54 + EXCLUDED 2; SKIP 0; exclusion share 0.035714; conditional FLAT closures 49; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 1 | -1.400000 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-02 | 6 | -6.333333 | 0.073171 | 0.074074 | 5 | 1 |
| 2023-03 | 9 | -5.000000 | 0.468085 | 0.487805 | 4 | 1 |
| 2023-04 | 8 | 3.533333 | 1.646341 | 1.800000 | 6 | 0 |
| 2023-05 | 6 | -7.100000 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-06 | 7 | -5.733333 | 0.148515 | 0.161290 | 4 | 0 |
| 2023-07 | 4 | -6.133333 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 2 | -2.833333 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 5 | -7.300000 | 0.000000 | 0.000000 | 43 | 0 |
| 2023-10 | 2 | -2.666667 | 0.000000 | 0.000000 | 0 | 0 |
| 2023-11 | 3 | -4.066667 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-12 | 1 | -1.400000 | 0.000000 | 0.000000 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK5_TOL1_MAXBARS36_SB2_TP10

**INSUFFICIENT_SAMPLE**; failed gates: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors; sample reasons: CLOSED_BELOW_100.
CLOSED 54; dates/months 49/12; PF R/price 0.242935/0.285211; Net -46.433333 R; expectancy -0.859877 R; positive months 1/12; conditional DD 46.433333 R.
Accepted 56 = CLOSED 54 + EXCLUDED 2; SKIP 0; exclusion share 0.035714; conditional FLAT closures 49; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 1 | -1.400000 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-02 | 6 | -6.333333 | 0.073171 | 0.074074 | 5 | 1 |
| 2023-03 | 9 | -5.000000 | 0.468085 | 0.487805 | 4 | 1 |
| 2023-04 | 8 | 3.533333 | 1.646341 | 1.800000 | 6 | 0 |
| 2023-05 | 6 | -7.100000 | 0.000000 | 0.000000 | 7 | 0 |
| 2023-06 | 7 | -5.733333 | 0.148515 | 0.161290 | 4 | 0 |
| 2023-07 | 4 | -6.133333 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 2 | -2.833333 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 5 | -7.300000 | 0.000000 | 0.000000 | 43 | 0 |
| 2023-10 | 2 | -2.666667 | 0.000000 | 0.000000 | 0 | 0 |
| 2023-11 | 3 | -4.066667 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-12 | 1 | -1.400000 | 0.000000 | 0.000000 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK5_TOL2_MAXBARS24_SB1_TP2

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 103; dates/months 83/12; PF R/price 0.513514/0.521459; Net -55.800000 R; expectancy -0.541748 R; positive months 2/12; conditional DD 66.466667 R.
Accepted 104 = CLOSED 103 + EXCLUDED 1; SKIP 2; exclusion share 0.009615; conditional FLAT closures 68; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 5 | 10.533333 | 8.523810 | 7.142857 | 7 | 0 |
| 2023-02 | 14 | -12.900000 | 0.284658 | 0.275362 | 5 | 0 |
| 2023-03 | 16 | -7.083333 | 0.526726 | 0.581818 | 4 | 1 |
| 2023-04 | 10 | -4.166667 | 0.614198 | 0.634146 | 6 | 0 |
| 2023-05 | 9 | -3.933333 | 0.609272 | 0.510638 | 7 | 0 |
| 2023-06 | 5 | -4.216667 | 0.228659 | 0.208333 | 4 | 0 |
| 2023-07 | 8 | -7.633333 | 0.282132 | 0.285714 | 1 | 0 |
| 2023-08 | 3 | -4.466667 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 9 | -9.566667 | 0.226415 | 0.297872 | 43 | 0 |
| 2023-10 | 3 | 7.933333 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 |
| 2023-11 | 10 | -10.233333 | 0.226700 | 0.206897 | 1 | 0 |
| 2023-12 | 11 | -10.066667 | 0.241206 | 0.280702 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK5_TOL2_MAXBARS24_SB1_TP3

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 102; dates/months 82/12; PF R/price 0.625645/0.641949; Net -43.500000 R; expectancy -0.426471 R; positive months 2/12; conditional DD 53.133333 R.
Accepted 104 = CLOSED 102 + EXCLUDED 2; SKIP 2; exclusion share 0.019231; conditional FLAT closures 102; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 4 | 9.500000 | 7.785714 | 7.142857 | 7 | 1 |
| 2023-02 | 14 | -11.233333 | 0.377079 | 0.347826 | 5 | 0 |
| 2023-03 | 16 | -10.083333 | 0.387652 | 0.426230 | 4 | 1 |
| 2023-04 | 10 | -1.100000 | 0.898148 | 0.926829 | 6 | 0 |
| 2023-05 | 9 | -1.200000 | 0.880795 | 0.744681 | 7 | 0 |
| 2023-06 | 5 | -4.216667 | 0.228659 | 0.208333 | 4 | 0 |
| 2023-07 | 8 | -6.133333 | 0.423197 | 0.428571 | 1 | 0 |
| 2023-08 | 3 | -4.466667 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 9 | -8.166667 | 0.339623 | 0.446809 | 43 | 0 |
| 2023-10 | 3 | 11.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 |
| 2023-11 | 10 | -8.733333 | 0.340050 | 0.310345 | 1 | 0 |
| 2023-12 | 11 | -8.666667 | 0.346734 | 0.403509 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK5_TOL2_MAXBARS24_SB1_TP4

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors; sample reasons: none.
CLOSED 102; dates/months 82/12; PF R/price 0.706971/0.733051; Net -34.050000 R; expectancy -0.333824 R; positive months 4/12; conditional DD 42.383333 R.
Accepted 104 = CLOSED 102 + EXCLUDED 2; SKIP 2; exclusion share 0.019231; conditional FLAT closures 102; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 4 | 8.200000 | 6.857143 | 6.285714 | 7 | 1 |
| 2023-02 | 14 | -9.566667 | 0.469501 | 0.420290 | 5 | 0 |
| 2023-03 | 16 | -8.583333 | 0.478745 | 0.524590 | 4 | 1 |
| 2023-04 | 10 | 1.966667 | 1.182099 | 1.219512 | 6 | 0 |
| 2023-05 | 9 | 0.200000 | 1.019868 | 0.893617 | 7 | 0 |
| 2023-06 | 5 | -4.216667 | 0.228659 | 0.208333 | 4 | 0 |
| 2023-07 | 8 | -4.633333 | 0.564263 | 0.571429 | 1 | 0 |
| 2023-08 | 3 | -4.466667 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 9 | -6.766667 | 0.452830 | 0.595745 | 43 | 0 |
| 2023-10 | 3 | 10.066667 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 |
| 2023-11 | 10 | -8.983333 | 0.321159 | 0.293103 | 1 | 0 |
| 2023-12 | 11 | -7.266667 | 0.452261 | 0.526316 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK5_TOL2_MAXBARS24_SB1_TP5

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors; sample reasons: none.
CLOSED 102; dates/months 82/12; PF R/price 0.739026/0.771967; Net -30.716667 R; expectancy -0.301144 R; positive months 4/12; conditional DD 39.050000 R.
Accepted 104 = CLOSED 102 + EXCLUDED 2; SKIP 2; exclusion share 0.019231; conditional FLAT closures 102; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 4 | 8.200000 | 6.857143 | 6.285714 | 7 | 1 |
| 2023-02 | 14 | -7.900000 | 0.561922 | 0.492754 | 5 | 0 |
| 2023-03 | 16 | -8.083333 | 0.509109 | 0.557377 | 4 | 1 |
| 2023-04 | 10 | 5.033333 | 1.466049 | 1.512195 | 6 | 0 |
| 2023-05 | 9 | 1.600000 | 1.158940 | 1.042553 | 7 | 0 |
| 2023-06 | 5 | -4.216667 | 0.228659 | 0.208333 | 4 | 0 |
| 2023-07 | 8 | -12.133333 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 3 | -4.466667 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 9 | -5.366667 | 0.566038 | 0.744681 | 43 | 0 |
| 2023-10 | 3 | 11.466667 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 |
| 2023-11 | 10 | -8.983333 | 0.321159 | 0.293103 | 1 | 0 |
| 2023-12 | 11 | -5.866667 | 0.557789 | 0.649123 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK5_TOL2_MAXBARS24_SB1_TP6

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors; sample reasons: none.
CLOSED 102; dates/months 82/12; PF R/price 0.808128/0.843096; Net -22.583333 R; expectancy -0.221405 R; positive months 4/12; conditional DD 30.916667 R.
Accepted 104 = CLOSED 102 + EXCLUDED 2; SKIP 2; exclusion share 0.019231; conditional FLAT closures 102; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 4 | 8.200000 | 6.857143 | 6.285714 | 7 | 1 |
| 2023-02 | 14 | -6.233333 | 0.654344 | 0.565217 | 5 | 0 |
| 2023-03 | 16 | -8.083333 | 0.509109 | 0.557377 | 4 | 1 |
| 2023-04 | 10 | 5.900000 | 1.546296 | 1.536585 | 6 | 0 |
| 2023-05 | 9 | 3.000000 | 1.298013 | 1.191489 | 7 | 0 |
| 2023-06 | 5 | -4.216667 | 0.228659 | 0.208333 | 4 | 0 |
| 2023-07 | 8 | -12.133333 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 3 | -4.466667 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 9 | -3.966667 | 0.679245 | 0.893617 | 43 | 0 |
| 2023-10 | 3 | 12.866667 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 |
| 2023-11 | 10 | -8.983333 | 0.321159 | 0.293103 | 1 | 0 |
| 2023-12 | 11 | -4.466667 | 0.663317 | 0.771930 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK5_TOL2_MAXBARS24_SB1_TP7

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors; sample reasons: none.
CLOSED 102; dates/months 82/12; PF R/price 0.850042/0.880753; Net -17.650000 R; expectancy -0.173039 R; positive months 4/12; conditional DD 28.233333 R.
Accepted 104 = CLOSED 102 + EXCLUDED 2; SKIP 2; exclusion share 0.019231; conditional FLAT closures 102; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 4 | 8.200000 | 6.857143 | 6.285714 | 7 | 1 |
| 2023-02 | 14 | -4.566667 | 0.746765 | 0.637681 | 5 | 0 |
| 2023-03 | 16 | -8.083333 | 0.509109 | 0.557377 | 4 | 1 |
| 2023-04 | 10 | 7.566667 | 1.700617 | 1.658537 | 6 | 0 |
| 2023-05 | 9 | 4.400000 | 1.437086 | 1.340426 | 7 | 0 |
| 2023-06 | 5 | -4.216667 | 0.228659 | 0.208333 | 4 | 0 |
| 2023-07 | 8 | -12.133333 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 3 | -4.466667 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 9 | -2.566667 | 0.792453 | 1.042553 | 43 | 0 |
| 2023-10 | 3 | 14.266667 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 |
| 2023-11 | 10 | -8.983333 | 0.321159 | 0.293103 | 1 | 0 |
| 2023-12 | 11 | -7.066667 | 0.467337 | 0.543860 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK5_TOL2_MAXBARS24_SB1_TP8

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors; sample reasons: none.
CLOSED 102; dates/months 82/12; PF R/price 0.886859/0.912134; Net -13.316667 R; expectancy -0.130556 R; positive months 4/12; conditional DD 27.233333 R.
Accepted 104 = CLOSED 102 + EXCLUDED 2; SKIP 2; exclusion share 0.019231; conditional FLAT closures 102; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 4 | 8.200000 | 6.857143 | 6.285714 | 7 | 1 |
| 2023-02 | 14 | -2.900000 | 0.839187 | 0.710145 | 5 | 0 |
| 2023-03 | 16 | -8.083333 | 0.509109 | 0.557377 | 4 | 1 |
| 2023-04 | 10 | 9.233333 | 1.854938 | 1.780488 | 6 | 0 |
| 2023-05 | 9 | 5.800000 | 1.576159 | 1.489362 | 7 | 0 |
| 2023-06 | 5 | -4.216667 | 0.228659 | 0.208333 | 4 | 0 |
| 2023-07 | 8 | -12.133333 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 3 | -4.466667 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 9 | -1.166667 | 0.905660 | 1.191489 | 43 | 0 |
| 2023-10 | 3 | 12.466667 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 |
| 2023-11 | 10 | -8.983333 | 0.321159 | 0.293103 | 1 | 0 |
| 2023-12 | 11 | -7.066667 | 0.467337 | 0.543860 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK5_TOL2_MAXBARS24_SB1_TP9

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors; sample reasons: none.
CLOSED 102; dates/months 82/12; PF R/price 0.886293/0.897490; Net -13.383333 R; expectancy -0.131209 R; positive months 4/12; conditional DD 31.766667 R.
Accepted 104 = CLOSED 102 + EXCLUDED 2; SKIP 2; exclusion share 0.019231; conditional FLAT closures 102; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 4 | 8.200000 | 6.857143 | 6.285714 | 7 | 1 |
| 2023-02 | 14 | -1.233333 | 0.931608 | 0.782609 | 5 | 0 |
| 2023-03 | 16 | -8.083333 | 0.509109 | 0.557377 | 4 | 1 |
| 2023-04 | 10 | 10.900000 | 2.009259 | 1.902439 | 6 | 0 |
| 2023-05 | 9 | 7.200000 | 1.715232 | 1.638298 | 7 | 0 |
| 2023-06 | 5 | -4.216667 | 0.228659 | 0.208333 | 4 | 0 |
| 2023-07 | 8 | -12.133333 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 3 | -4.466667 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 9 | -5.966667 | 0.517520 | 0.680851 | 43 | 0 |
| 2023-10 | 3 | 12.466667 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 |
| 2023-11 | 10 | -8.983333 | 0.321159 | 0.293103 | 1 | 0 |
| 2023-12 | 11 | -7.066667 | 0.467337 | 0.543860 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK5_TOL2_MAXBARS24_SB1_TP10

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors; sample reasons: none.
CLOSED 101; dates/months 82/12; PF R/price 0.939816/0.942918; Net -6.983333 R; expectancy -0.069142 R; positive months 5/12; conditional DD 31.766667 R.
Accepted 103 = CLOSED 101 + EXCLUDED 2; SKIP 2; exclusion share 0.019417; conditional FLAT closures 101; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 4 | 8.200000 | 6.857143 | 6.285714 | 7 | 1 |
| 2023-02 | 13 | 2.100000 | 1.128310 | 0.921875 | 5 | 0 |
| 2023-03 | 16 | -8.083333 | 0.509109 | 0.557377 | 4 | 1 |
| 2023-04 | 10 | 12.566667 | 2.163580 | 2.024390 | 6 | 0 |
| 2023-05 | 9 | 8.600000 | 1.854305 | 1.787234 | 7 | 0 |
| 2023-06 | 5 | -4.216667 | 0.228659 | 0.208333 | 4 | 0 |
| 2023-07 | 8 | -12.133333 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 3 | -4.466667 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 9 | -5.966667 | 0.517520 | 0.680851 | 43 | 0 |
| 2023-10 | 3 | 12.466667 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 |
| 2023-11 | 10 | -8.983333 | 0.321159 | 0.293103 | 1 | 0 |
| 2023-12 | 11 | -7.066667 | 0.467337 | 0.543860 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK5_TOL2_MAXBARS24_SB2_TP2

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 115; dates/months 90/12; PF R/price 0.533644/0.553004; Net -55.100000 R; expectancy -0.479130 R; positive months 3/12; conditional DD 64.900000 R.
Accepted 116 = CLOSED 115 + EXCLUDED 1; SKIP 2; exclusion share 0.008621; conditional FLAT closures 75; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 5 | 9.800000 | 8.350000 | 7.250000 | 7 | 0 |
| 2023-02 | 18 | -14.333333 | 0.337442 | 0.380435 | 5 | 0 |
| 2023-03 | 17 | -6.500000 | 0.522644 | 0.600000 | 4 | 1 |
| 2023-04 | 10 | 0.600000 | 1.070866 | 1.000000 | 6 | 0 |
| 2023-05 | 11 | -0.500000 | 0.947368 | 0.716981 | 7 | 0 |
| 2023-06 | 7 | -7.333333 | 0.120000 | 0.135135 | 4 | 0 |
| 2023-07 | 10 | -10.400000 | 0.212121 | 0.237288 | 1 | 0 |
| 2023-08 | 4 | -5.833333 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 9 | -8.733333 | 0.233918 | 0.290909 | 43 | 0 |
| 2023-10 | 3 | 7.166667 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 |
| 2023-11 | 10 | -9.600000 | 0.225806 | 0.208955 | 1 | 0 |
| 2023-12 | 11 | -9.433333 | 0.241287 | 0.272727 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK5_TOL2_MAXBARS24_SB2_TP3

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors; sample reasons: none.
CLOSED 113; dates/months 89/12; PF R/price 0.618141/0.650177; Net -45.116667 R; expectancy -0.399263 R; positive months 4/12; conditional DD 53.816667 R.
Accepted 116 = CLOSED 113 + EXCLUDED 3; SKIP 2; exclusion share 0.025862; conditional FLAT closures 113; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 4 | 8.700000 | 7.525000 | 7.000000 | 7 | 1 |
| 2023-02 | 17 | -15.633333 | 0.277350 | 0.293478 | 5 | 1 |
| 2023-03 | 17 | -5.500000 | 0.596083 | 0.683333 | 4 | 1 |
| 2023-04 | 10 | 2.683333 | 1.316929 | 1.261905 | 6 | 0 |
| 2023-05 | 11 | 3.000000 | 1.315789 | 1.000000 | 7 | 0 |
| 2023-06 | 7 | -7.333333 | 0.120000 | 0.135135 | 4 | 0 |
| 2023-07 | 10 | -9.000000 | 0.318182 | 0.355932 | 1 | 0 |
| 2023-08 | 4 | -5.833333 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 9 | -7.400000 | 0.350877 | 0.436364 | 43 | 0 |
| 2023-10 | 3 | 7.500000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 |
| 2023-11 | 10 | -8.200000 | 0.338710 | 0.313433 | 1 | 0 |
| 2023-12 | 11 | -8.100000 | 0.348525 | 0.393939 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK5_TOL2_MAXBARS24_SB2_TP4

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors; sample reasons: none.
CLOSED 113; dates/months 89/12; PF R/price 0.709268/0.743816; Net -34.350000 R; expectancy -0.303982 R; positive months 4/12; conditional DD 40.883333 R.
Accepted 116 = CLOSED 113 + EXCLUDED 3; SKIP 2; exclusion share 0.025862; conditional FLAT closures 113; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 4 | 6.533333 | 5.900000 | 5.500000 | 7 | 1 |
| 2023-02 | 17 | -14.133333 | 0.346687 | 0.358696 | 5 | 1 |
| 2023-03 | 17 | -4.500000 | 0.669523 | 0.766667 | 4 | 1 |
| 2023-04 | 10 | 5.516667 | 1.651575 | 1.595238 | 6 | 0 |
| 2023-05 | 11 | 6.000000 | 1.631579 | 1.245283 | 7 | 0 |
| 2023-06 | 7 | -7.333333 | 0.120000 | 0.135135 | 4 | 0 |
| 2023-07 | 10 | -7.600000 | 0.424242 | 0.474576 | 1 | 0 |
| 2023-08 | 4 | -5.833333 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 9 | -6.066667 | 0.467836 | 0.581818 | 43 | 0 |
| 2023-10 | 3 | 8.833333 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 |
| 2023-11 | 10 | -9.000000 | 0.274194 | 0.253731 | 1 | 0 |
| 2023-12 | 11 | -6.766667 | 0.455764 | 0.515152 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK5_TOL2_MAXBARS24_SB2_TP5

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors; sample reasons: none.
CLOSED 113; dates/months 89/12; PF R/price 0.736373/0.769634; Net -31.516667 R; expectancy -0.278909 R; positive months 4/12; conditional DD 38.100000 R.
Accepted 116 = CLOSED 113 + EXCLUDED 3; SKIP 2; exclusion share 0.025862; conditional FLAT closures 113; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 4 | 6.533333 | 5.900000 | 5.500000 | 7 | 1 |
| 2023-02 | 17 | -12.633333 | 0.416025 | 0.423913 | 5 | 1 |
| 2023-03 | 17 | -4.500000 | 0.669523 | 0.766667 | 4 | 1 |
| 2023-04 | 10 | 6.850000 | 1.809055 | 1.714286 | 6 | 0 |
| 2023-05 | 11 | 9.000000 | 1.947368 | 1.490566 | 7 | 0 |
| 2023-06 | 7 | -7.333333 | 0.120000 | 0.135135 | 4 | 0 |
| 2023-07 | 10 | -14.600000 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 4 | -5.833333 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 9 | -4.733333 | 0.584795 | 0.727273 | 43 | 0 |
| 2023-10 | 3 | 10.166667 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 |
| 2023-11 | 10 | -9.000000 | 0.274194 | 0.253731 | 1 | 0 |
| 2023-12 | 11 | -5.433333 | 0.563003 | 0.636364 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK5_TOL2_MAXBARS24_SB2_TP6

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors; sample reasons: none.
CLOSED 113; dates/months 89/12; PF R/price 0.793531/0.821990; Net -24.683333 R; expectancy -0.218437 R; positive months 4/12; conditional DD 37.266667 R.
Accepted 116 = CLOSED 113 + EXCLUDED 3; SKIP 2; exclusion share 0.025862; conditional FLAT closures 113; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 4 | 6.533333 | 5.900000 | 5.500000 | 7 | 1 |
| 2023-02 | 17 | -11.133333 | 0.485362 | 0.489130 | 5 | 1 |
| 2023-03 | 17 | -4.500000 | 0.669523 | 0.766667 | 4 | 1 |
| 2023-04 | 10 | 8.350000 | 1.986220 | 1.857143 | 6 | 0 |
| 2023-05 | 11 | 12.000000 | 2.263158 | 1.735849 | 7 | 0 |
| 2023-06 | 7 | -7.333333 | 0.120000 | 0.135135 | 4 | 0 |
| 2023-07 | 10 | -14.600000 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 4 | -5.833333 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 9 | -3.400000 | 0.701754 | 0.872727 | 43 | 0 |
| 2023-10 | 3 | 11.500000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 |
| 2023-11 | 10 | -9.000000 | 0.274194 | 0.253731 | 1 | 0 |
| 2023-12 | 11 | -7.266667 | 0.415550 | 0.469697 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK5_TOL2_MAXBARS24_SB2_TP7

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors; sample reasons: none.
CLOSED 113; dates/months 89/12; PF R/price 0.843720/0.865620; Net -18.683333 R; expectancy -0.165339 R; positive months 4/12; conditional DD 37.266667 R.
Accepted 116 = CLOSED 113 + EXCLUDED 3; SKIP 2; exclusion share 0.025862; conditional FLAT closures 113; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 4 | 6.533333 | 5.900000 | 5.500000 | 7 | 1 |
| 2023-02 | 17 | -9.633333 | 0.554700 | 0.554348 | 5 | 1 |
| 2023-03 | 17 | -4.500000 | 0.669523 | 0.766667 | 4 | 1 |
| 2023-04 | 10 | 9.850000 | 2.163386 | 2.000000 | 6 | 0 |
| 2023-05 | 11 | 15.000000 | 2.578947 | 1.981132 | 7 | 0 |
| 2023-06 | 7 | -7.333333 | 0.120000 | 0.135135 | 4 | 0 |
| 2023-07 | 10 | -14.600000 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 4 | -5.833333 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 9 | -2.066667 | 0.818713 | 1.018182 | 43 | 0 |
| 2023-10 | 3 | 10.166667 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 |
| 2023-11 | 10 | -9.000000 | 0.274194 | 0.253731 | 1 | 0 |
| 2023-12 | 11 | -7.266667 | 0.415550 | 0.469697 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK5_TOL2_MAXBARS24_SB2_TP8

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors; sample reasons: none.
CLOSED 113; dates/months 89/12; PF R/price 0.860449/0.867365; Net -16.683333 R; expectancy -0.147640 R; positive months 4/12; conditional DD 41.266667 R.
Accepted 116 = CLOSED 113 + EXCLUDED 3; SKIP 2; exclusion share 0.025862; conditional FLAT closures 113; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 4 | 6.533333 | 5.900000 | 5.500000 | 7 | 1 |
| 2023-02 | 17 | -8.133333 | 0.624037 | 0.619565 | 5 | 1 |
| 2023-03 | 17 | -4.500000 | 0.669523 | 0.766667 | 4 | 1 |
| 2023-04 | 10 | 11.350000 | 2.340551 | 2.142857 | 6 | 0 |
| 2023-05 | 11 | 18.000000 | 2.894737 | 2.226415 | 7 | 0 |
| 2023-06 | 7 | -7.333333 | 0.120000 | 0.135135 | 4 | 0 |
| 2023-07 | 10 | -14.600000 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 4 | -5.833333 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 9 | -6.066667 | 0.467836 | 0.581818 | 43 | 0 |
| 2023-10 | 3 | 10.166667 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 |
| 2023-11 | 10 | -9.000000 | 0.274194 | 0.253731 | 1 | 0 |
| 2023-12 | 11 | -7.266667 | 0.415550 | 0.469697 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK5_TOL2_MAXBARS24_SB2_TP9

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors; sample reasons: none.
CLOSED 112; dates/months 89/12; PF R/price 0.911619/0.911817; Net -10.433333 R; expectancy -0.093155 R; positive months 4/12; conditional DD 41.266667 R.
Accepted 115 = CLOSED 112 + EXCLUDED 3; SKIP 2; exclusion share 0.026087; conditional FLAT closures 112; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 4 | 6.533333 | 5.900000 | 5.500000 | 7 | 1 |
| 2023-02 | 16 | -6.383333 | 0.682947 | 0.674419 | 5 | 1 |
| 2023-03 | 17 | -4.500000 | 0.669523 | 0.766667 | 4 | 1 |
| 2023-04 | 10 | 12.850000 | 2.517717 | 2.285714 | 6 | 0 |
| 2023-05 | 11 | 21.000000 | 3.210526 | 2.471698 | 7 | 0 |
| 2023-06 | 7 | -7.333333 | 0.120000 | 0.135135 | 4 | 0 |
| 2023-07 | 10 | -14.600000 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 4 | -5.833333 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 9 | -6.066667 | 0.467836 | 0.581818 | 43 | 0 |
| 2023-10 | 3 | 10.166667 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 |
| 2023-11 | 10 | -9.000000 | 0.274194 | 0.253731 | 1 | 0 |
| 2023-12 | 11 | -7.266667 | 0.415550 | 0.469697 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK5_TOL2_MAXBARS24_SB2_TP10

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 112; dates/months 89/12; PF R/price 0.871382/0.880071; Net -15.183333 R; expectancy -0.135565 R; positive months 4/12; conditional DD 41.266667 R.
Accepted 115 = CLOSED 112 + EXCLUDED 3; SKIP 2; exclusion share 0.026087; conditional FLAT closures 112; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 4 | 6.533333 | 5.900000 | 5.500000 | 7 | 1 |
| 2023-02 | 16 | -6.383333 | 0.682947 | 0.674419 | 5 | 1 |
| 2023-03 | 17 | -4.500000 | 0.669523 | 0.766667 | 4 | 1 |
| 2023-04 | 10 | 5.100000 | 1.602362 | 1.547619 | 6 | 0 |
| 2023-05 | 11 | 24.000000 | 3.526316 | 2.716981 | 7 | 0 |
| 2023-06 | 7 | -7.333333 | 0.120000 | 0.135135 | 4 | 0 |
| 2023-07 | 10 | -14.600000 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 4 | -5.833333 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 9 | -6.066667 | 0.467836 | 0.581818 | 43 | 0 |
| 2023-10 | 3 | 10.166667 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 |
| 2023-11 | 10 | -9.000000 | 0.274194 | 0.253731 | 1 | 0 |
| 2023-12 | 11 | -7.266667 | 0.415550 | 0.469697 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK5_TOL2_MAXBARS36_SB1_TP2

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 106; dates/months 86/12; PF R/price 0.479856/0.496907; Net -62.400000 R; expectancy -0.588679 R; positive months 2/12; conditional DD 71.400000 R.
Accepted 107 = CLOSED 106 + EXCLUDED 1; SKIP 2; exclusion share 0.009346; conditional FLAT closures 72; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 6 | 8.866667 | 3.891304 | 4.166667 | 7 | 0 |
| 2023-02 | 15 | -14.400000 | 0.262799 | 0.253333 | 5 | 0 |
| 2023-03 | 13 | -6.883333 | 0.507160 | 0.538462 | 4 | 1 |
| 2023-04 | 11 | -3.700000 | 0.652038 | 0.666667 | 6 | 0 |
| 2023-05 | 8 | -7.266667 | 0.278146 | 0.297872 | 7 | 0 |
| 2023-06 | 5 | -4.216667 | 0.228659 | 0.208333 | 4 | 0 |
| 2023-07 | 9 | -9.133333 | 0.247253 | 0.250000 | 1 | 0 |
| 2023-08 | 3 | -4.466667 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 10 | -8.066667 | 0.347709 | 0.425532 | 43 | 0 |
| 2023-10 | 5 | 4.766667 | 2.505263 | 3.000000 | 0 | 0 |
| 2023-11 | 10 | -7.833333 | 0.338028 | 0.313725 | 1 | 0 |
| 2023-12 | 11 | -10.066667 | 0.241206 | 0.280702 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK5_TOL2_MAXBARS36_SB1_TP3

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors; sample reasons: none.
CLOSED 105; dates/months 85/12; PF R/price 0.576564/0.604888; Net -51.433333 R; expectancy -0.489841 R; positive months 2/12; conditional DD 59.400000 R.
Accepted 107 = CLOSED 105 + EXCLUDED 2; SKIP 2; exclusion share 0.018692; conditional FLAT closures 105; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 5 | 7.833333 | 3.554348 | 4.166667 | 7 | 1 |
| 2023-02 | 15 | -12.733333 | 0.348123 | 0.320000 | 5 | 0 |
| 2023-03 | 13 | -9.883333 | 0.360991 | 0.379310 | 4 | 1 |
| 2023-04 | 11 | -0.633333 | 0.940439 | 0.952381 | 6 | 0 |
| 2023-05 | 8 | -5.866667 | 0.417219 | 0.446809 | 7 | 0 |
| 2023-06 | 5 | -4.216667 | 0.228659 | 0.208333 | 4 | 0 |
| 2023-07 | 9 | -7.633333 | 0.370879 | 0.375000 | 1 | 0 |
| 2023-08 | 3 | -4.466667 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 10 | -6.666667 | 0.460916 | 0.574468 | 43 | 0 |
| 2023-10 | 5 | 7.833333 | 3.473684 | 4.090909 | 0 | 0 |
| 2023-11 | 10 | -6.333333 | 0.464789 | 0.431373 | 1 | 0 |
| 2023-12 | 11 | -8.666667 | 0.346734 | 0.403509 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK5_TOL2_MAXBARS36_SB1_TP4

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors; sample reasons: none.
CLOSED 105; dates/months 85/12; PF R/price 0.654363/0.692464; Net -41.983333 R; expectancy -0.399841 R; positive months 3/12; conditional DD 48.650000 R.
Accepted 107 = CLOSED 105 + EXCLUDED 2; SKIP 2; exclusion share 0.018692; conditional FLAT closures 105; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 5 | 6.533333 | 3.130435 | 3.666667 | 7 | 1 |
| 2023-02 | 15 | -11.066667 | 0.433447 | 0.386667 | 5 | 0 |
| 2023-03 | 13 | -8.383333 | 0.457974 | 0.482759 | 4 | 1 |
| 2023-04 | 11 | 2.433333 | 1.228840 | 1.238095 | 6 | 0 |
| 2023-05 | 8 | -4.466667 | 0.556291 | 0.595745 | 7 | 0 |
| 2023-06 | 5 | -4.216667 | 0.228659 | 0.208333 | 4 | 0 |
| 2023-07 | 9 | -6.133333 | 0.494505 | 0.500000 | 1 | 0 |
| 2023-08 | 3 | -4.466667 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 10 | -5.266667 | 0.574124 | 0.723404 | 43 | 0 |
| 2023-10 | 5 | 6.900000 | 3.178947 | 4.090909 | 0 | 0 |
| 2023-11 | 10 | -6.583333 | 0.443662 | 0.411765 | 1 | 0 |
| 2023-12 | 11 | -7.266667 | 0.452261 | 0.526316 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK5_TOL2_MAXBARS36_SB1_TP5

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors; sample reasons: none.
CLOSED 105; dates/months 85/12; PF R/price 0.685687/0.730382; Net -38.650000 R; expectancy -0.368095 R; positive months 3/12; conditional DD 45.316667 R.
Accepted 107 = CLOSED 105 + EXCLUDED 2; SKIP 2; exclusion share 0.018692; conditional FLAT closures 105; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 5 | 6.533333 | 3.130435 | 3.666667 | 7 | 1 |
| 2023-02 | 15 | -9.400000 | 0.518771 | 0.453333 | 5 | 0 |
| 2023-03 | 13 | -7.883333 | 0.490302 | 0.517241 | 4 | 1 |
| 2023-04 | 11 | 5.500000 | 1.517241 | 1.523810 | 6 | 0 |
| 2023-05 | 8 | -3.066667 | 0.695364 | 0.744681 | 7 | 0 |
| 2023-06 | 5 | -4.216667 | 0.228659 | 0.208333 | 4 | 0 |
| 2023-07 | 9 | -13.633333 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 3 | -4.466667 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 10 | -3.866667 | 0.687332 | 0.872340 | 43 | 0 |
| 2023-10 | 5 | 8.300000 | 3.621053 | 4.727273 | 0 | 0 |
| 2023-11 | 10 | -6.583333 | 0.443662 | 0.411765 | 1 | 0 |
| 2023-12 | 11 | -5.866667 | 0.557789 | 0.649123 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK5_TOL2_MAXBARS36_SB1_TP6

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors; sample reasons: none.
CLOSED 105; dates/months 85/12; PF R/price 0.751830/0.798793; Net -30.516667 R; expectancy -0.290635 R; positive months 3/12; conditional DD 37.183333 R.
Accepted 107 = CLOSED 105 + EXCLUDED 2; SKIP 2; exclusion share 0.018692; conditional FLAT closures 105; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 5 | 6.533333 | 3.130435 | 3.666667 | 7 | 1 |
| 2023-02 | 15 | -7.733333 | 0.604096 | 0.520000 | 5 | 0 |
| 2023-03 | 13 | -7.883333 | 0.490302 | 0.517241 | 4 | 1 |
| 2023-04 | 11 | 6.366667 | 1.598746 | 1.547619 | 6 | 0 |
| 2023-05 | 8 | -1.666667 | 0.834437 | 0.893617 | 7 | 0 |
| 2023-06 | 5 | -4.216667 | 0.228659 | 0.208333 | 4 | 0 |
| 2023-07 | 9 | -13.633333 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 3 | -4.466667 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 10 | -2.466667 | 0.800539 | 1.021277 | 43 | 0 |
| 2023-10 | 5 | 9.700000 | 4.063158 | 5.363636 | 0 | 0 |
| 2023-11 | 10 | -6.583333 | 0.443662 | 0.411765 | 1 | 0 |
| 2023-12 | 11 | -4.466667 | 0.663317 | 0.771930 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK5_TOL2_MAXBARS36_SB1_TP7

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors; sample reasons: none.
CLOSED 105; dates/months 85/12; PF R/price 0.791949/0.835010; Net -25.583333 R; expectancy -0.243651 R; positive months 3/12; conditional DD 32.700000 R.
Accepted 107 = CLOSED 105 + EXCLUDED 2; SKIP 2; exclusion share 0.018692; conditional FLAT closures 105; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 5 | 6.533333 | 3.130435 | 3.666667 | 7 | 1 |
| 2023-02 | 15 | -6.066667 | 0.689420 | 0.586667 | 5 | 0 |
| 2023-03 | 13 | -7.883333 | 0.490302 | 0.517241 | 4 | 1 |
| 2023-04 | 11 | 8.033333 | 1.755486 | 1.666667 | 6 | 0 |
| 2023-05 | 8 | -0.266667 | 0.973510 | 1.042553 | 7 | 0 |
| 2023-06 | 5 | -4.216667 | 0.228659 | 0.208333 | 4 | 0 |
| 2023-07 | 9 | -13.633333 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 3 | -4.466667 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 10 | -1.066667 | 0.913747 | 1.170213 | 43 | 0 |
| 2023-10 | 5 | 11.100000 | 4.505263 | 6.000000 | 0 | 0 |
| 2023-11 | 10 | -6.583333 | 0.443662 | 0.411765 | 1 | 0 |
| 2023-12 | 11 | -7.066667 | 0.467337 | 0.543860 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK5_TOL2_MAXBARS36_SB1_TP8

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors; sample reasons: none.
CLOSED 105; dates/months 85/12; PF R/price 0.827189/0.865191; Net -21.250000 R; expectancy -0.202381 R; positive months 5/12; conditional DD 31.700000 R.
Accepted 107 = CLOSED 105 + EXCLUDED 2; SKIP 2; exclusion share 0.018692; conditional FLAT closures 105; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 5 | 6.533333 | 3.130435 | 3.666667 | 7 | 1 |
| 2023-02 | 15 | -4.400000 | 0.774744 | 0.653333 | 5 | 0 |
| 2023-03 | 13 | -7.883333 | 0.490302 | 0.517241 | 4 | 1 |
| 2023-04 | 11 | 9.700000 | 1.912226 | 1.785714 | 6 | 0 |
| 2023-05 | 8 | 1.133333 | 1.112583 | 1.191489 | 7 | 0 |
| 2023-06 | 5 | -4.216667 | 0.228659 | 0.208333 | 4 | 0 |
| 2023-07 | 9 | -13.633333 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 3 | -4.466667 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 10 | 0.333333 | 1.026954 | 1.319149 | 43 | 0 |
| 2023-10 | 5 | 9.300000 | 3.936842 | 5.181818 | 0 | 0 |
| 2023-11 | 10 | -6.583333 | 0.443662 | 0.411765 | 1 | 0 |
| 2023-12 | 11 | -7.066667 | 0.467337 | 0.543860 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK5_TOL2_MAXBARS36_SB1_TP9

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors; sample reasons: none.
CLOSED 105; dates/months 85/12; PF R/price 0.826647/0.851107; Net -21.316667 R; expectancy -0.203016 R; positive months 4/12; conditional DD 35.100000 R.
Accepted 107 = CLOSED 105 + EXCLUDED 2; SKIP 2; exclusion share 0.018692; conditional FLAT closures 105; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 5 | 6.533333 | 3.130435 | 3.666667 | 7 | 1 |
| 2023-02 | 15 | -2.733333 | 0.860068 | 0.720000 | 5 | 0 |
| 2023-03 | 13 | -7.883333 | 0.490302 | 0.517241 | 4 | 1 |
| 2023-04 | 11 | 11.366667 | 2.068966 | 1.904762 | 6 | 0 |
| 2023-05 | 8 | 2.533333 | 1.251656 | 1.340426 | 7 | 0 |
| 2023-06 | 5 | -4.216667 | 0.228659 | 0.208333 | 4 | 0 |
| 2023-07 | 9 | -13.633333 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 3 | -4.466667 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 10 | -4.466667 | 0.638814 | 0.808511 | 43 | 0 |
| 2023-10 | 5 | 9.300000 | 3.936842 | 5.181818 | 0 | 0 |
| 2023-11 | 10 | -6.583333 | 0.443662 | 0.411765 | 1 | 0 |
| 2023-12 | 11 | -7.066667 | 0.467337 | 0.543860 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK5_TOL2_MAXBARS36_SB1_TP10

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors; sample reasons: none.
CLOSED 104; dates/months 85/12; PF R/price 0.877027/0.894309; Net -14.916667 R; expectancy -0.143429 R; positive months 5/12; conditional DD 33.700000 R.
Accepted 106 = CLOSED 104 + EXCLUDED 2; SKIP 2; exclusion share 0.018868; conditional FLAT closures 104; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 5 | 6.533333 | 3.130435 | 3.666667 | 7 | 1 |
| 2023-02 | 14 | 0.600000 | 1.033582 | 0.842857 | 5 | 0 |
| 2023-03 | 13 | -7.883333 | 0.490302 | 0.517241 | 4 | 1 |
| 2023-04 | 11 | 13.033333 | 2.225705 | 2.023810 | 6 | 0 |
| 2023-05 | 8 | 3.933333 | 1.390728 | 1.489362 | 7 | 0 |
| 2023-06 | 5 | -4.216667 | 0.228659 | 0.208333 | 4 | 0 |
| 2023-07 | 9 | -13.633333 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 3 | -4.466667 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 10 | -4.466667 | 0.638814 | 0.808511 | 43 | 0 |
| 2023-10 | 5 | 9.300000 | 3.936842 | 5.181818 | 0 | 0 |
| 2023-11 | 10 | -6.583333 | 0.443662 | 0.411765 | 1 | 0 |
| 2023-12 | 11 | -7.066667 | 0.467337 | 0.543860 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK5_TOL2_MAXBARS36_SB2_TP2

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 119; dates/months 94/12; PF R/price 0.550779/0.559792; Net -53.816667 R; expectancy -0.452241 R; positive months 3/12; conditional DD 64.616667 R.
Accepted 120 = CLOSED 119 + EXCLUDED 1; SKIP 2; exclusion share 0.008333; conditional FLAT closures 79; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 6 | 10.800000 | 9.100000 | 7.750000 | 7 | 0 |
| 2023-02 | 20 | -12.400000 | 0.461650 | 0.454545 | 5 | 0 |
| 2023-03 | 14 | -6.416667 | 0.501295 | 0.561404 | 4 | 1 |
| 2023-04 | 11 | 1.166667 | 1.142857 | 1.047619 | 6 | 0 |
| 2023-05 | 10 | -3.500000 | 0.631579 | 0.490566 | 7 | 0 |
| 2023-06 | 8 | -7.333333 | 0.120000 | 0.135135 | 4 | 0 |
| 2023-07 | 10 | -10.133333 | 0.216495 | 0.229508 | 1 | 0 |
| 2023-08 | 4 | -5.833333 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 10 | -7.533333 | 0.339181 | 0.400000 | 43 | 0 |
| 2023-10 | 5 | 4.266667 | 2.471264 | 2.846154 | 0 | 0 |
| 2023-11 | 10 | -7.466667 | 0.325301 | 0.305085 | 1 | 0 |
| 2023-12 | 11 | -9.433333 | 0.241287 | 0.272727 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK5_TOL2_MAXBARS36_SB2_TP3

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 117; dates/months 93/12; PF R/price 0.607679/0.637782; Net -47.000000 R; expectancy -0.401709 R; positive months 3/12; conditional DD 56.700000 R.
Accepted 120 = CLOSED 117 + EXCLUDED 3; SKIP 2; exclusion share 0.025000; conditional FLAT closures 117; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 5 | 9.700000 | 8.275000 | 7.500000 | 7 | 1 |
| 2023-02 | 19 | -16.366667 | 0.289436 | 0.292929 | 5 | 1 |
| 2023-03 | 14 | -5.416667 | 0.579016 | 0.649123 | 4 | 1 |
| 2023-04 | 11 | 3.250000 | 1.397959 | 1.309524 | 6 | 0 |
| 2023-05 | 10 | -0.500000 | 0.947368 | 0.735849 | 7 | 0 |
| 2023-06 | 8 | -7.333333 | 0.120000 | 0.135135 | 4 | 0 |
| 2023-07 | 10 | -8.733333 | 0.324742 | 0.344262 | 1 | 0 |
| 2023-08 | 4 | -5.833333 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 10 | -6.200000 | 0.456140 | 0.545455 | 43 | 0 |
| 2023-10 | 5 | 4.600000 | 2.586207 | 3.153846 | 0 | 0 |
| 2023-11 | 10 | -6.066667 | 0.451807 | 0.423729 | 1 | 0 |
| 2023-12 | 11 | -8.100000 | 0.348525 | 0.393939 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK5_TOL2_MAXBARS36_SB2_TP4

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors; sample reasons: none.
CLOSED 117; dates/months 93/12; PF R/price 0.697551/0.729636; Net -36.233333 R; expectancy -0.309687 R; positive months 4/12; conditional DD 43.766667 R.
Accepted 120 = CLOSED 117 + EXCLUDED 3; SKIP 2; exclusion share 0.025000; conditional FLAT closures 117; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 5 | 7.533333 | 6.650000 | 6.000000 | 7 | 1 |
| 2023-02 | 19 | -14.866667 | 0.354559 | 0.353535 | 5 | 1 |
| 2023-03 | 14 | -4.416667 | 0.656736 | 0.736842 | 4 | 1 |
| 2023-04 | 11 | 6.083333 | 1.744898 | 1.642857 | 6 | 0 |
| 2023-05 | 10 | 2.500000 | 1.263158 | 0.981132 | 7 | 0 |
| 2023-06 | 8 | -7.333333 | 0.120000 | 0.135135 | 4 | 0 |
| 2023-07 | 10 | -7.333333 | 0.432990 | 0.459016 | 1 | 0 |
| 2023-08 | 4 | -5.833333 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 10 | -4.866667 | 0.573099 | 0.690909 | 43 | 0 |
| 2023-10 | 5 | 5.933333 | 3.045977 | 3.769231 | 0 | 0 |
| 2023-11 | 10 | -6.866667 | 0.379518 | 0.355932 | 1 | 0 |
| 2023-12 | 11 | -6.766667 | 0.455764 | 0.515152 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK5_TOL2_MAXBARS36_SB2_TP5

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors; sample reasons: none.
CLOSED 117; dates/months 93/12; PF R/price 0.724422/0.755137; Net -33.400000 R; expectancy -0.285470 R; positive months 4/12; conditional DD 40.933333 R.
Accepted 120 = CLOSED 117 + EXCLUDED 3; SKIP 2; exclusion share 0.025000; conditional FLAT closures 117; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 5 | 7.533333 | 6.650000 | 6.000000 | 7 | 1 |
| 2023-02 | 19 | -13.366667 | 0.419682 | 0.414141 | 5 | 1 |
| 2023-03 | 14 | -4.416667 | 0.656736 | 0.736842 | 4 | 1 |
| 2023-04 | 11 | 7.416667 | 1.908163 | 1.761905 | 6 | 0 |
| 2023-05 | 10 | 5.500000 | 1.578947 | 1.226415 | 7 | 0 |
| 2023-06 | 8 | -7.333333 | 0.120000 | 0.135135 | 4 | 0 |
| 2023-07 | 10 | -14.333333 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 4 | -5.833333 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 10 | -3.533333 | 0.690058 | 0.836364 | 43 | 0 |
| 2023-10 | 5 | 7.266667 | 3.505747 | 4.384615 | 0 | 0 |
| 2023-11 | 10 | -6.866667 | 0.379518 | 0.355932 | 1 | 0 |
| 2023-12 | 11 | -5.433333 | 0.563003 | 0.636364 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK5_TOL2_MAXBARS36_SB2_TP6

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors; sample reasons: none.
CLOSED 117; dates/months 93/12; PF R/price 0.780803/0.806507; Net -26.566667 R; expectancy -0.227066 R; positive months 4/12; conditional DD 36.566667 R.
Accepted 120 = CLOSED 117 + EXCLUDED 3; SKIP 2; exclusion share 0.025000; conditional FLAT closures 117; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 5 | 7.533333 | 6.650000 | 6.000000 | 7 | 1 |
| 2023-02 | 19 | -11.866667 | 0.484805 | 0.474747 | 5 | 1 |
| 2023-03 | 14 | -4.416667 | 0.656736 | 0.736842 | 4 | 1 |
| 2023-04 | 11 | 8.916667 | 2.091837 | 1.904762 | 6 | 0 |
| 2023-05 | 10 | 8.500000 | 1.894737 | 1.471698 | 7 | 0 |
| 2023-06 | 8 | -7.333333 | 0.120000 | 0.135135 | 4 | 0 |
| 2023-07 | 10 | -14.333333 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 4 | -5.833333 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 10 | -2.200000 | 0.807018 | 0.981818 | 43 | 0 |
| 2023-10 | 5 | 8.600000 | 3.965517 | 5.000000 | 0 | 0 |
| 2023-11 | 10 | -6.866667 | 0.379518 | 0.355932 | 1 | 0 |
| 2023-12 | 11 | -7.266667 | 0.415550 | 0.469697 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK5_TOL2_MAXBARS36_SB2_TP7

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors; sample reasons: none.
CLOSED 117; dates/months 93/12; PF R/price 0.830308/0.849315; Net -20.566667 R; expectancy -0.175783 R; positive months 4/12; conditional DD 36.566667 R.
Accepted 120 = CLOSED 117 + EXCLUDED 3; SKIP 2; exclusion share 0.025000; conditional FLAT closures 117; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 5 | 7.533333 | 6.650000 | 6.000000 | 7 | 1 |
| 2023-02 | 19 | -10.366667 | 0.549928 | 0.535354 | 5 | 1 |
| 2023-03 | 14 | -4.416667 | 0.656736 | 0.736842 | 4 | 1 |
| 2023-04 | 11 | 10.416667 | 2.275510 | 2.047619 | 6 | 0 |
| 2023-05 | 10 | 11.500000 | 2.210526 | 1.716981 | 7 | 0 |
| 2023-06 | 8 | -7.333333 | 0.120000 | 0.135135 | 4 | 0 |
| 2023-07 | 10 | -14.333333 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 4 | -5.833333 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 10 | -0.866667 | 0.923977 | 1.127273 | 43 | 0 |
| 2023-10 | 5 | 7.266667 | 3.505747 | 4.384615 | 0 | 0 |
| 2023-11 | 10 | -6.866667 | 0.379518 | 0.355932 | 1 | 0 |
| 2023-12 | 11 | -7.266667 | 0.415550 | 0.469697 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK5_TOL2_MAXBARS36_SB2_TP8

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors; sample reasons: none.
CLOSED 117; dates/months 93/12; PF R/price 0.846810/0.851027; Net -18.566667 R; expectancy -0.158689 R; positive months 4/12; conditional DD 40.566667 R.
Accepted 120 = CLOSED 117 + EXCLUDED 3; SKIP 2; exclusion share 0.025000; conditional FLAT closures 117; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 5 | 7.533333 | 6.650000 | 6.000000 | 7 | 1 |
| 2023-02 | 19 | -8.866667 | 0.615051 | 0.595960 | 5 | 1 |
| 2023-03 | 14 | -4.416667 | 0.656736 | 0.736842 | 4 | 1 |
| 2023-04 | 11 | 11.916667 | 2.459184 | 2.190476 | 6 | 0 |
| 2023-05 | 10 | 14.500000 | 2.526316 | 1.962264 | 7 | 0 |
| 2023-06 | 8 | -7.333333 | 0.120000 | 0.135135 | 4 | 0 |
| 2023-07 | 10 | -14.333333 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 4 | -5.833333 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 10 | -4.866667 | 0.573099 | 0.690909 | 43 | 0 |
| 2023-10 | 5 | 7.266667 | 3.505747 | 4.384615 | 0 | 0 |
| 2023-11 | 10 | -6.866667 | 0.379518 | 0.355932 | 1 | 0 |
| 2023-12 | 11 | -7.266667 | 0.415550 | 0.469697 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK5_TOL2_MAXBARS36_SB2_TP9

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors; sample reasons: none.
CLOSED 116; dates/months 93/12; PF R/price 0.897104/0.894464; Net -12.316667 R; expectancy -0.106178 R; positive months 4/12; conditional DD 40.566667 R.
Accepted 119 = CLOSED 116 + EXCLUDED 3; SKIP 2; exclusion share 0.025210; conditional FLAT closures 116; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 5 | 7.533333 | 6.650000 | 6.000000 | 7 | 1 |
| 2023-02 | 18 | -7.116667 | 0.669505 | 0.645161 | 5 | 1 |
| 2023-03 | 14 | -4.416667 | 0.656736 | 0.736842 | 4 | 1 |
| 2023-04 | 11 | 13.416667 | 2.642857 | 2.333333 | 6 | 0 |
| 2023-05 | 10 | 17.500000 | 2.842105 | 2.207547 | 7 | 0 |
| 2023-06 | 8 | -7.333333 | 0.120000 | 0.135135 | 4 | 0 |
| 2023-07 | 10 | -14.333333 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 4 | -5.833333 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 10 | -4.866667 | 0.573099 | 0.690909 | 43 | 0 |
| 2023-10 | 5 | 7.266667 | 3.505747 | 4.384615 | 0 | 0 |
| 2023-11 | 10 | -6.866667 | 0.379518 | 0.355932 | 1 | 0 |
| 2023-12 | 11 | -7.266667 | 0.415550 | 0.469697 | 0 | 0 |

## C_OPT2023_APP3_LOOKBACK5_TOL2_MAXBARS36_SB2_TP10

**DOES_NOT_QUALIFY**; failed gates: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors; sample reasons: none.
CLOSED 116; dates/months 93/12; PF R/price 0.857421/0.863322; Net -17.066667 R; expectancy -0.147126 R; positive months 4/12; conditional DD 40.566667 R.
Accepted 119 = CLOSED 116 + EXCLUDED 3; SKIP 2; exclusion share 0.025210; conditional FLAT closures 116; qualifying neighbors 0.

| Exit month | CLOSED | Net R | PF R | PF price | Missing bars | EXCLUDED |
|---|---|---|---|---|---|---|
| 2023-01 | 5 | 7.533333 | 6.650000 | 6.000000 | 7 | 1 |
| 2023-02 | 18 | -7.116667 | 0.669505 | 0.645161 | 5 | 1 |
| 2023-03 | 14 | -4.416667 | 0.656736 | 0.736842 | 4 | 1 |
| 2023-04 | 11 | 5.666667 | 1.693878 | 1.595238 | 6 | 0 |
| 2023-05 | 10 | 20.500000 | 3.157895 | 2.452830 | 7 | 0 |
| 2023-06 | 8 | -7.333333 | 0.120000 | 0.135135 | 4 | 0 |
| 2023-07 | 10 | -14.333333 | 0.000000 | 0.000000 | 1 | 0 |
| 2023-08 | 4 | -5.833333 | 0.000000 | 0.000000 | 109 | 0 |
| 2023-09 | 10 | -4.866667 | 0.573099 | 0.690909 | 43 | 0 |
| 2023-10 | 5 | 7.266667 | 3.505747 | 4.384615 | 0 | 0 |
| 2023-11 | 10 | -6.866667 | 0.379518 | 0.355932 | 1 | 0 |
| 2023-12 | 11 | -7.266667 | 0.415550 | 0.469697 | 0 | 0 |

