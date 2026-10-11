# Optimization A Equal High/Low — bounded frozen 2023 grid

**NO QUALIFYING OPTIMIZATION CANDIDATE**

Base main: `ce89458b063f3af2451f8c4c162107207973c53b`. Pre-P&L freeze: `2b6735a3ba459adc59f386620937315d21a060a1`.
72 fixed configurations × USDRUBF/CNYRUBF = 144 evaluations. Complete exhaustive search; no added variants, direction selection, or early stop.
All results below are profit after model C1 costs, not actual broker commissions. Prices are instrument quotation units and never pooled. CLOSED-only economics are conditional on coverage and assumed FLAT after excluded positions. No complete annual PF/return, continuous equity or broker Max DD is established.
Take distance = R × (gross initial risk + planned 2 entry ticks) + planned 2 entry ticks, rounded outward. Net_R uses gross initial risk; planned net/net R and realized net/net R have distinct ledger fields. Actual C1 uses dated entry and exit ticks.
One attempt per maximal equal-extreme sequence; completed candles only; immediate next Open admission, structural Stop unchanged, entry-bar Take disabled, Stop-first, 120-minute/session-flat deadline. CNY tick .01 before 2023-09-27 19:00 MSK, .001 thereafter.
Sample requires 100 CLOSED / 40 entry dates / 6 entry months. Both PF ≥2, expectancy >0, ≥9 positive exit months, conditional DD ≤20R, largest winner ≤25%, largest positive month ≤50%; two adjacent neighbors need 100 CLOSED, positive expectancy, PF R ≥1.5. Local 2023 stability diagnosis is not Robustness.
Monthly zero sign uses the registry 1e-20 R numerical tolerance. PF without losses is NOT_AVAILABLE; zero/no-trade months are not positive. Independent algorithm audit does not replace external Draft PR review.

| Instrument | Evaluated | Sample | Both PF | Months ≥9 | Base criteria | All criteria |
|---|---|---|---|---|---|---|
| USDRUBF | 72 | 36 | 0 | 0 | 0 | 0 |
| CNYRUBF | 72 | 63 | 0 | 0 | 0 | 0 |

Reproduce from a clean checkout with the pinned read-only source:
```bash
python -m IntradayLab.optimization_a_2023_v1.validate --data-root /workspace/market-pattern-data --output IntradayLab/work/fresh_optimization_a_validation
```
The validation command runs canonical + two full repeats and the independent auditor, checks freeze dependencies and every preexisting repository path, and refuses existing outputs. Source OHLC is not copied into this repository.

All candidate criteria and reasons: all_candidates.csv. Complete exact monthly and directional metrics: monthly_results.csv and direction_results.csv. Full events, CLOSED trades, SKIP, EXCLUDED, rejected/nonfill and coverage: evaluations/<ID>/<instrument>/. Selection ranks contain only fully qualified configurations.
Counterfactual legacy replay for T3/SB1/TP3 validates frozen A_v1 paths; comparator_gap_policy.csv explains differences from V2 entry skipping and consequent occupancy. This is an audit of the historical comparator, not an added Optimization variant.

## USDRUBF

NO QUALIFYING OPTIMIZATION CANDIDATE

### A_OPT2023_T2_SB1_TP2

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 1329, entry dates 249, entry months 12; SKIP 6, EXCLUDED 5, exclusion share 0.003748; conditional FLAT CLOSED 1105.
Net -563.200000 R; PF R / price 0.619142 / 0.627287; expectancy -0.423777 R; win rate 0.252822; average winner / loser 2.724901 / -1.502812 R.
Conditional CLOSED-only DD 574.100000 R; largest winner share 0.003641; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 12 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 104 | -44.750000 | 0.613391 | 0.592428 | 5 | 1 | 0 |
| 2023-02 | 110 | -43.500000 | 0.647963 | 0.678879 | 4 | 1 | 0 |
| 2023-03 | 136 | -63.666667 | 0.576544 | 0.594545 | 3 | 0 | 2 |
| 2023-04 | 110 | -7.566667 | 0.930877 | 0.953995 | 5 | 3 | 1 |
| 2023-05 | 91 | -42.850000 | 0.572853 | 0.546599 | 3 | 1 | 0 |
| 2023-06 | 117 | -78.183333 | 0.442278 | 0.418182 | 4 | 0 | 1 |
| 2023-07 | 108 | -62.283333 | 0.505230 | 0.526749 | 1 | 0 | 0 |
| 2023-08 | 81 | -50.866667 | 0.469125 | 0.448819 | 2 | 0 | 0 |
| 2023-09 | 107 | -43.866667 | 0.628511 | 0.680095 | 2 | 0 | 0 |
| 2023-10 | 106 | -47.016667 | 0.614933 | 0.629139 | 0 | 0 | 0 |
| 2023-11 | 146 | -51.650000 | 0.672722 | 0.674457 | 1 | 0 | 1 |
| 2023-12 | 113 | -27.000000 | 0.773932 | 0.815054 | 0 | 0 | 0 |

### A_OPT2023_T2_SB1_TP3

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 1261, entry dates 249, entry months 12; SKIP 6, EXCLUDED 6, exclusion share 0.004736; conditional FLAT CLOSED 1161.
Net -552.783333 R; PF R / price 0.627989 / 0.636075; expectancy -0.438369 R; win rate 0.206979; average winner / loser 3.575287 / -1.499428 R.
Conditional CLOSED-only DD 564.016667 R; largest winner share 0.005358; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 97 | -43.300000 | 0.619786 | 0.590498 | 5 | 1 | 0 |
| 2023-02 | 100 | -22.450000 | 0.797626 | 0.852029 | 4 | 1 | 1 |
| 2023-03 | 132 | -70.466667 | 0.542919 | 0.548845 | 3 | 0 | 2 |
| 2023-04 | 102 | 10.433333 | 1.098119 | 1.196970 | 5 | 3 | 1 |
| 2023-05 | 88 | -48.066667 | 0.533182 | 0.498778 | 3 | 1 | 0 |
| 2023-06 | 110 | -86.216667 | 0.386431 | 0.385036 | 4 | 0 | 1 |
| 2023-07 | 103 | -63.633333 | 0.498753 | 0.501010 | 1 | 0 | 0 |
| 2023-08 | 79 | -51.033333 | 0.483904 | 0.468193 | 2 | 0 | 0 |
| 2023-09 | 104 | -43.100000 | 0.645899 | 0.696552 | 2 | 0 | 0 |
| 2023-10 | 98 | -46.200000 | 0.615000 | 0.625000 | 0 | 0 | 0 |
| 2023-11 | 140 | -60.550000 | 0.633067 | 0.606013 | 1 | 0 | 1 |
| 2023-12 | 108 | -28.200000 | 0.773615 | 0.802469 | 0 | 0 | 0 |

### A_OPT2023_T2_SB1_TP4

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 1216, entry dates 248, entry months 12; SKIP 6, EXCLUDED 7, exclusion share 0.005724; conditional FLAT CLOSED 1119.
Net -546.333333 R; PF R / price 0.626166 / 0.622989; expectancy -0.449287 R; win rate 0.189967; average winner / loser 3.961472 / -1.497370 R.
Conditional CLOSED-only DD 552.350000 R; largest winner share 0.007285; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 94 | -56.716667 | 0.502703 | 0.478458 | 5 | 1 | 0 |
| 2023-02 | 96 | -20.833333 | 0.807396 | 0.834951 | 4 | 1 | 1 |
| 2023-03 | 119 | -67.550000 | 0.520695 | 0.522989 | 3 | 0 | 3 |
| 2023-04 | 100 | 18.733333 | 1.179438 | 1.264631 | 5 | 3 | 1 |
| 2023-05 | 86 | -49.666667 | 0.515605 | 0.463592 | 3 | 1 | 0 |
| 2023-06 | 109 | -77.616667 | 0.447634 | 0.458029 | 4 | 0 | 1 |
| 2023-07 | 101 | -54.333333 | 0.566316 | 0.559184 | 1 | 0 | 0 |
| 2023-08 | 75 | -37.466667 | 0.597205 | 0.577657 | 2 | 0 | 0 |
| 2023-09 | 100 | -40.033333 | 0.666528 | 0.709302 | 2 | 0 | 0 |
| 2023-10 | 95 | -39.733333 | 0.664225 | 0.641084 | 0 | 0 | 0 |
| 2023-11 | 137 | -67.150000 | 0.596737 | 0.548589 | 1 | 0 | 1 |
| 2023-12 | 104 | -53.966667 | 0.577174 | 0.588353 | 0 | 0 | 0 |

### A_OPT2023_T2_SB1_TP5

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 1197, entry dates 248, entry months 12; SKIP 6, EXCLUDED 7, exclusion share 0.005814; conditional FLAT CLOSED 1101.
Net -503.400000 R; PF R / price 0.653007 / 0.646073; expectancy -0.420551 R; win rate 0.182122; average winner / loser 4.345642 / -1.497162 R.
Conditional CLOSED-only DD 503.400000 R; largest winner share 0.008796; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 93 | -84.550000 | 0.287200 | 0.270153 | 5 | 1 | 0 |
| 2023-02 | 93 | -6.933333 | 0.933248 | 0.966837 | 4 | 1 | 1 |
| 2023-03 | 118 | -71.883333 | 0.490550 | 0.491363 | 3 | 0 | 3 |
| 2023-04 | 96 | 25.016667 | 1.242253 | 1.369792 | 5 | 3 | 1 |
| 2023-05 | 86 | -43.933333 | 0.566233 | 0.508600 | 3 | 1 | 0 |
| 2023-06 | 108 | -79.550000 | 0.434680 | 0.448087 | 4 | 0 | 1 |
| 2023-07 | 100 | -47.133333 | 0.622984 | 0.593496 | 1 | 0 | 0 |
| 2023-08 | 75 | -28.916667 | 0.689124 | 0.664850 | 2 | 0 | 0 |
| 2023-09 | 97 | -26.483333 | 0.770143 | 0.806763 | 2 | 0 | 0 |
| 2023-10 | 95 | -25.833333 | 0.781690 | 0.751693 | 0 | 0 | 0 |
| 2023-11 | 136 | -43.766667 | 0.734774 | 0.675633 | 1 | 0 | 1 |
| 2023-12 | 100 | -69.433333 | 0.445863 | 0.445122 | 0 | 0 | 0 |

### A_OPT2023_T2_SB1_TP6

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 1188, entry dates 248, entry months 12; SKIP 6, EXCLUDED 7, exclusion share 0.005858; conditional FLAT CLOSED 1092.
Net -485.600000 R; PF R / price 0.664196 / 0.656188; expectancy -0.408754 R; win rate 0.178451; average winner / loser 4.530582 / -1.496981 R.
Conditional CLOSED-only DD 485.600000 R; largest winner share 0.010411; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 93 | -82.883333 | 0.301251 | 0.281046 | 5 | 1 | 0 |
| 2023-02 | 92 | -0.133333 | 0.998697 | 1.038860 | 4 | 1 | 1 |
| 2023-03 | 118 | -65.550000 | 0.535436 | 0.533589 | 3 | 0 | 3 |
| 2023-04 | 96 | 15.600000 | 1.146939 | 1.231738 | 5 | 3 | 1 |
| 2023-05 | 86 | -44.100000 | 0.564588 | 0.498771 | 3 | 1 | 0 |
| 2023-06 | 107 | -70.300000 | 0.494426 | 0.507353 | 4 | 0 | 1 |
| 2023-07 | 100 | -40.866667 | 0.673110 | 0.642276 | 1 | 0 | 0 |
| 2023-08 | 74 | -18.116667 | 0.802040 | 0.772853 | 2 | 0 | 0 |
| 2023-09 | 96 | -16.750000 | 0.852488 | 0.897311 | 2 | 0 | 0 |
| 2023-10 | 94 | -23.950000 | 0.795182 | 0.779817 | 0 | 0 | 0 |
| 2023-11 | 133 | -53.033333 | 0.675670 | 0.616613 | 1 | 0 | 1 |
| 2023-12 | 99 | -85.516667 | 0.326464 | 0.338028 | 0 | 0 | 0 |

### A_OPT2023_T2_SB1_TP7

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 1179, entry dates 248, entry months 12; SKIP 6, EXCLUDED 7, exclusion share 0.005902; conditional FLAT CLOSED 1083.
Net -455.800000 R; PF R / price 0.682786 / 0.673213; expectancy -0.386599 R; win rate 0.177269; average winner / loser 4.694179 / -1.496753 R.
Conditional CLOSED-only DD 455.800000 R; largest winner share 0.011892; largest positive month share 0.736688. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 93 | -81.216667 | 0.315301 | 0.291939 | 5 | 1 | 0 |
| 2023-02 | 91 | 7.500000 | 1.074282 | 1.121372 | 4 | 1 | 1 |
| 2023-03 | 117 | -63.216667 | 0.546617 | 0.548450 | 3 | 0 | 3 |
| 2023-04 | 96 | 20.983333 | 1.197645 | 1.284635 | 5 | 3 | 1 |
| 2023-05 | 85 | -37.866667 | 0.620891 | 0.547500 | 3 | 1 | 0 |
| 2023-06 | 106 | -64.000000 | 0.534150 | 0.551020 | 4 | 0 | 1 |
| 2023-07 | 98 | -40.533333 | 0.671396 | 0.611910 | 1 | 0 | 0 |
| 2023-08 | 74 | -8.816667 | 0.903661 | 0.869806 | 2 | 0 | 0 |
| 2023-09 | 95 | -17.850000 | 0.842801 | 0.885086 | 2 | 0 | 0 |
| 2023-10 | 94 | -23.800000 | 0.796465 | 0.770642 | 0 | 0 | 0 |
| 2023-11 | 131 | -63.133333 | 0.610569 | 0.567044 | 1 | 0 | 1 |
| 2023-12 | 99 | -83.850000 | 0.339590 | 0.348089 | 0 | 0 | 0 |

### A_OPT2023_T2_SB1_TP8

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 1175, entry dates 248, entry months 12; SKIP 6, EXCLUDED 7, exclusion share 0.005922; conditional FLAT CLOSED 1079.
Net -421.200000 R; PF R / price 0.705931 / 0.694216; expectancy -0.358468 R; win rate 0.177021; average winner / loser 4.861138 / -1.496674 R.
Conditional CLOSED-only DD 421.200000 R; largest winner share 0.013187; largest positive month share 0.711137. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 93 | -79.550000 | 0.329352 | 0.302832 | 5 | 1 | 0 |
| 2023-02 | 91 | 12.233333 | 1.121162 | 1.166227 | 4 | 1 | 1 |
| 2023-03 | 115 | -60.816667 | 0.554021 | 0.563492 | 3 | 0 | 3 |
| 2023-04 | 96 | 30.116667 | 1.283673 | 1.375315 | 5 | 3 | 1 |
| 2023-05 | 85 | -33.033333 | 0.669281 | 0.587500 | 3 | 1 | 0 |
| 2023-06 | 106 | -59.033333 | 0.570302 | 0.591837 | 4 | 0 | 1 |
| 2023-07 | 98 | -39.133333 | 0.682746 | 0.605749 | 1 | 0 | 0 |
| 2023-08 | 74 | -2.250000 | 0.975414 | 0.936288 | 2 | 0 | 0 |
| 2023-09 | 95 | -18.116667 | 0.840452 | 0.877751 | 2 | 0 | 0 |
| 2023-10 | 94 | -25.300000 | 0.783637 | 0.745413 | 0 | 0 | 0 |
| 2023-11 | 129 | -64.133333 | 0.600706 | 0.562806 | 1 | 0 | 1 |
| 2023-12 | 99 | -82.183333 | 0.352717 | 0.358149 | 0 | 0 | 0 |

### A_OPT2023_T2_SB1_TP9

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 1170, entry dates 248, entry months 12; SKIP 6, EXCLUDED 7, exclusion share 0.005947; conditional FLAT CLOSED 1074.
Net -476.066667 R; PF R / price 0.666624 / 0.663615; expectancy -0.406895 R; win rate 0.176068; average winner / loser 4.621117 / -1.496873 R.
Conditional CLOSED-only DD 476.066667 R; largest winner share 0.015757; largest positive month share 0.609213. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 93 | -77.883333 | 0.343403 | 0.313725 | 5 | 1 | 0 |
| 2023-02 | 91 | 16.966667 | 1.168042 | 1.211082 | 4 | 1 | 1 |
| 2023-03 | 115 | -65.816667 | 0.517355 | 0.523810 | 3 | 0 | 3 |
| 2023-04 | 96 | 26.450000 | 1.249137 | 1.345088 | 5 | 3 | 1 |
| 2023-05 | 84 | -56.283333 | 0.427918 | 0.401015 | 3 | 1 | 0 |
| 2023-06 | 106 | -57.233333 | 0.583404 | 0.610390 | 4 | 0 | 1 |
| 2023-07 | 98 | -34.133333 | 0.723281 | 0.636550 | 1 | 0 | 0 |
| 2023-08 | 72 | -9.283333 | 0.896985 | 0.895480 | 2 | 0 | 0 |
| 2023-09 | 95 | -26.800000 | 0.763981 | 0.794621 | 2 | 0 | 0 |
| 2023-10 | 92 | -27.900000 | 0.754977 | 0.726415 | 0 | 0 | 0 |
| 2023-11 | 129 | -83.633333 | 0.484646 | 0.474110 | 1 | 0 | 1 |
| 2023-12 | 99 | -80.516667 | 0.365844 | 0.368209 | 0 | 0 | 0 |

### A_OPT2023_T2_SB1_TP10

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 1169, entry dates 248, entry months 12; SKIP 6, EXCLUDED 7, exclusion share 0.005952; conditional FLAT CLOSED 1073.
Net -463.900000 R; PF R / price 0.674764 / 0.671188; expectancy -0.396835 R; win rate 0.176219; average winner / loser 4.672087 / -1.496695 R.
Conditional CLOSED-only DD 463.900000 R; largest winner share 0.017317; largest positive month share 0.588365. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 93 | -76.216667 | 0.357454 | 0.324619 | 5 | 1 | 0 |
| 2023-02 | 91 | 21.700000 | 1.214922 | 1.255937 | 4 | 1 | 1 |
| 2023-03 | 115 | -65.816667 | 0.517355 | 0.523810 | 3 | 0 | 3 |
| 2023-04 | 96 | 31.016667 | 1.292151 | 1.390428 | 5 | 3 | 1 |
| 2023-05 | 84 | -56.283333 | 0.427918 | 0.401015 | 3 | 1 | 0 |
| 2023-06 | 106 | -54.433333 | 0.603785 | 0.636364 | 4 | 0 | 1 |
| 2023-07 | 98 | -29.133333 | 0.763816 | 0.667351 | 1 | 0 | 0 |
| 2023-08 | 72 | -4.716667 | 0.947660 | 0.946328 | 2 | 0 | 0 |
| 2023-09 | 94 | -44.466667 | 0.602562 | 0.631188 | 2 | 0 | 0 |
| 2023-10 | 92 | -24.566667 | 0.784251 | 0.750000 | 0 | 0 | 0 |
| 2023-11 | 129 | -82.133333 | 0.493889 | 0.483819 | 1 | 0 | 1 |
| 2023-12 | 99 | -78.850000 | 0.378971 | 0.378270 | 0 | 0 | 0 |

### A_OPT2023_T2_SB2_TP2

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 1531, entry dates 250, entry months 12; SKIP 4, EXCLUDED 8, exclusion share 0.005198; conditional FLAT CLOSED 1492.
Net -560.450000 R; PF R / price 0.650312 / 0.658354; expectancy -0.366068 R; win rate 0.261267; average winner / loser 2.605667 / -1.429720 R.
Conditional CLOSED-only DD 566.283333 R; largest winner share 0.003198; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 12 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 113 | -58.100000 | 0.530189 | 0.512334 | 5 | 0 | 2 |
| 2023-02 | 120 | -37.066667 | 0.705625 | 0.752809 | 4 | 0 | 1 |
| 2023-03 | 151 | -66.783333 | 0.578255 | 0.614089 | 3 | 0 | 2 |
| 2023-04 | 135 | -37.400000 | 0.727339 | 0.800705 | 5 | 3 | 1 |
| 2023-05 | 122 | -42.366667 | 0.666404 | 0.599265 | 3 | 1 | 0 |
| 2023-06 | 131 | -65.133333 | 0.548365 | 0.528788 | 4 | 0 | 1 |
| 2023-07 | 125 | -40.933333 | 0.677055 | 0.665517 | 1 | 0 | 0 |
| 2023-08 | 91 | -45.766667 | 0.537399 | 0.505519 | 2 | 0 | 0 |
| 2023-09 | 124 | -51.266667 | 0.611959 | 0.640934 | 2 | 0 | 0 |
| 2023-10 | 120 | -13.133333 | 0.887621 | 0.895257 | 0 | 0 | 0 |
| 2023-11 | 159 | -60.400000 | 0.636510 | 0.622951 | 1 | 0 | 1 |
| 2023-12 | 140 | -42.100000 | 0.710785 | 0.775641 | 0 | 0 | 0 |

### A_OPT2023_T2_SB2_TP3

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 1425, entry dates 250, entry months 12; SKIP 4, EXCLUDED 10, exclusion share 0.006969; conditional FLAT CLOSED 1386.
Net -533.133333 R; PF R / price 0.660511 / 0.664904; expectancy -0.374129 R; win rate 0.222456; average winner / loser 3.272135 / -1.428935 R.
Conditional CLOSED-only DD 540.500000 R; largest winner share 0.004820; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 12 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 108 | -45.650000 | 0.621998 | 0.604288 | 5 | 0 | 2 |
| 2023-02 | 111 | -26.933333 | 0.771493 | 0.843687 | 4 | 0 | 2 |
| 2023-03 | 140 | -66.900000 | 0.567504 | 0.592476 | 3 | 0 | 2 |
| 2023-04 | 124 | -13.433333 | 0.894997 | 0.998117 | 5 | 3 | 1 |
| 2023-05 | 116 | -51.400000 | 0.607434 | 0.546595 | 3 | 1 | 0 |
| 2023-06 | 123 | -52.533333 | 0.622741 | 0.601881 | 4 | 0 | 2 |
| 2023-07 | 113 | -37.183333 | 0.687535 | 0.651625 | 1 | 0 | 0 |
| 2023-08 | 87 | -31.800000 | 0.671827 | 0.632054 | 2 | 0 | 0 |
| 2023-09 | 118 | -50.133333 | 0.618419 | 0.650362 | 2 | 0 | 0 |
| 2023-10 | 107 | -23.583333 | 0.795579 | 0.792415 | 0 | 0 | 0 |
| 2023-11 | 151 | -71.550000 | 0.579859 | 0.558667 | 1 | 0 | 1 |
| 2023-12 | 127 | -62.033333 | 0.575163 | 0.606349 | 0 | 0 | 0 |

### A_OPT2023_T2_SB2_TP4

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 1382, entry dates 249, entry months 12; SKIP 4, EXCLUDED 11, exclusion share 0.007897; conditional FLAT CLOSED 1345.
Net -478.933333 R; PF R / price 0.692351 / 0.684568; expectancy -0.346551 R; win rate 0.204052; average winner / loser 3.822045 / -1.426902 R.
Conditional CLOSED-only DD 484.000000 R; largest winner share 0.006185; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 12 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 106 | -54.350000 | 0.553899 | 0.504780 | 5 | 0 | 2 |
| 2023-02 | 107 | -16.416667 | 0.857391 | 0.890688 | 4 | 0 | 2 |
| 2023-03 | 128 | -54.216667 | 0.619131 | 0.639594 | 3 | 0 | 3 |
| 2023-04 | 121 | -12.983333 | 0.899820 | 1.014953 | 5 | 3 | 1 |
| 2023-05 | 114 | -58.866667 | 0.554603 | 0.485009 | 3 | 1 | 0 |
| 2023-06 | 119 | -67.816667 | 0.518974 | 0.512422 | 4 | 0 | 2 |
| 2023-07 | 111 | -18.450000 | 0.842532 | 0.771325 | 1 | 0 | 0 |
| 2023-08 | 87 | -22.266667 | 0.774095 | 0.745536 | 2 | 0 | 0 |
| 2023-09 | 115 | -38.400000 | 0.704729 | 0.746789 | 2 | 0 | 0 |
| 2023-10 | 105 | -9.950000 | 0.913803 | 0.892000 | 0 | 0 | 0 |
| 2023-11 | 149 | -65.033333 | 0.624519 | 0.590314 | 1 | 0 | 1 |
| 2023-12 | 120 | -60.183333 | 0.570987 | 0.563312 | 0 | 0 | 0 |

### A_OPT2023_T2_SB2_TP5

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 1356, entry dates 249, entry months 12; SKIP 4, EXCLUDED 11, exclusion share 0.008047; conditional FLAT CLOSED 1319.
Net -491.416667 R; PF R / price 0.682400 / 0.683599; expectancy -0.362402 R; win rate 0.194690; average winner / loser 3.999495 / -1.428701 R.
Conditional CLOSED-only DD 503.350000 R; largest winner share 0.007892; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 12 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 104 | -49.866667 | 0.585940 | 0.532946 | 5 | 0 | 2 |
| 2023-02 | 105 | -16.033333 | 0.859418 | 0.917355 | 4 | 0 | 2 |
| 2023-03 | 125 | -61.250000 | 0.565654 | 0.603774 | 3 | 0 | 3 |
| 2023-04 | 120 | -6.816667 | 0.947375 | 1.041045 | 5 | 3 | 1 |
| 2023-05 | 112 | -66.400000 | 0.495057 | 0.434705 | 3 | 1 | 0 |
| 2023-06 | 118 | -51.483333 | 0.630900 | 0.622257 | 4 | 0 | 2 |
| 2023-07 | 110 | -24.050000 | 0.798182 | 0.783002 | 1 | 0 | 0 |
| 2023-08 | 85 | -25.900000 | 0.738648 | 0.765766 | 2 | 0 | 0 |
| 2023-09 | 111 | -36.133333 | 0.712429 | 0.769962 | 2 | 0 | 0 |
| 2023-10 | 103 | -19.466667 | 0.831360 | 0.810000 | 0 | 0 | 0 |
| 2023-11 | 146 | -66.766667 | 0.611972 | 0.577483 | 1 | 0 | 1 |
| 2023-12 | 117 | -67.250000 | 0.519128 | 0.486268 | 0 | 0 | 0 |

### A_OPT2023_T2_SB2_TP6

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 1344, entry dates 249, entry months 12; SKIP 4, EXCLUDED 11, exclusion share 0.008118; conditional FLAT CLOSED 1307.
Net -487.700000 R; PF R / price 0.684136 / 0.687696; expectancy -0.362872 R; win rate 0.189732; average winner / loser 4.142418 / -1.429645 R.
Conditional CLOSED-only DD 499.300000 R; largest winner share 0.009467; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 12 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 104 | -54.366667 | 0.554128 | 0.505747 | 5 | 0 | 2 |
| 2023-02 | 103 | -12.000000 | 0.893538 | 0.972689 | 4 | 0 | 2 |
| 2023-03 | 125 | -60.116667 | 0.573691 | 0.620926 | 3 | 0 | 3 |
| 2023-04 | 120 | -3.950000 | 0.969506 | 1.078358 | 5 | 3 | 1 |
| 2023-05 | 111 | -57.166667 | 0.560819 | 0.491833 | 3 | 1 | 0 |
| 2023-06 | 115 | -58.016667 | 0.579539 | 0.598101 | 4 | 0 | 2 |
| 2023-07 | 108 | -39.483333 | 0.672790 | 0.658318 | 1 | 0 | 0 |
| 2023-08 | 85 | -14.266667 | 0.856038 | 0.885135 | 2 | 0 | 0 |
| 2023-09 | 110 | -33.933333 | 0.729938 | 0.783270 | 2 | 0 | 0 |
| 2023-10 | 101 | -20.166667 | 0.821692 | 0.795082 | 0 | 0 | 0 |
| 2023-11 | 145 | -71.150000 | 0.587057 | 0.537849 | 1 | 0 | 1 |
| 2023-12 | 117 | -63.083333 | 0.548921 | 0.513732 | 0 | 0 | 0 |

### A_OPT2023_T2_SB2_TP7

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 1334, entry dates 249, entry months 12; SKIP 4, EXCLUDED 11, exclusion share 0.008178; conditional FLAT CLOSED 1297.
Net -495.183333 R; PF R / price 0.677884 / 0.685611; expectancy -0.371202 R; win rate 0.187406; average winner / loser 4.168400 / -1.430031 R.
Conditional CLOSED-only DD 510.116667 R; largest winner share 0.011195; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 104 | -69.450000 | 0.444844 | 0.429644 | 5 | 0 | 2 |
| 2023-02 | 103 | -11.083333 | 0.901671 | 0.985294 | 4 | 0 | 2 |
| 2023-03 | 124 | -57.650000 | 0.586788 | 0.632582 | 3 | 0 | 3 |
| 2023-04 | 120 | 6.183333 | 1.047735 | 1.166045 | 5 | 3 | 1 |
| 2023-05 | 110 | -56.116667 | 0.564199 | 0.488971 | 3 | 1 | 0 |
| 2023-06 | 115 | -52.200000 | 0.621693 | 0.645570 | 4 | 0 | 2 |
| 2023-07 | 108 | -47.616667 | 0.609913 | 0.577739 | 1 | 0 | 0 |
| 2023-08 | 83 | -6.800000 | 0.929485 | 0.983645 | 2 | 0 | 0 |
| 2023-09 | 110 | -32.983333 | 0.737498 | 0.785171 | 2 | 0 | 0 |
| 2023-10 | 100 | -38.116667 | 0.662983 | 0.657787 | 0 | 0 | 0 |
| 2023-11 | 140 | -74.100000 | 0.555133 | 0.509642 | 1 | 0 | 1 |
| 2023-12 | 117 | -55.250000 | 0.604934 | 0.558966 | 0 | 0 | 0 |

### A_OPT2023_T2_SB2_TP8

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 1329, entry dates 249, entry months 12; SKIP 4, EXCLUDED 11, exclusion share 0.008209; conditional FLAT CLOSED 1292.
Net -495.050000 R; PF R / price 0.676660 / 0.680597; expectancy -0.372498 R; win rate 0.187359; average winner / loser 4.160643 / -1.429552 R.
Conditional CLOSED-only DD 513.316667 R; largest winner share 0.012870; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 12 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 104 | -66.616667 | 0.467493 | 0.455910 | 5 | 0 | 2 |
| 2023-02 | 103 | -6.750000 | 0.940115 | 1.027311 | 4 | 0 | 2 |
| 2023-03 | 123 | -60.383333 | 0.561963 | 0.599650 | 3 | 0 | 3 |
| 2023-04 | 119 | -1.766667 | 0.986184 | 1.084746 | 5 | 3 | 1 |
| 2023-05 | 110 | -53.516667 | 0.584390 | 0.494485 | 3 | 1 | 0 |
| 2023-06 | 114 | -47.533333 | 0.651728 | 0.678914 | 4 | 0 | 2 |
| 2023-07 | 108 | -43.116667 | 0.646778 | 0.609541 | 1 | 0 | 0 |
| 2023-08 | 82 | -17.916667 | 0.814207 | 0.878505 | 2 | 0 | 0 |
| 2023-09 | 110 | -37.283333 | 0.703276 | 0.737643 | 2 | 0 | 0 |
| 2023-10 | 100 | -35.116667 | 0.689508 | 0.682377 | 0 | 0 | 0 |
| 2023-11 | 140 | -71.033333 | 0.573544 | 0.526171 | 1 | 0 | 1 |
| 2023-12 | 116 | -54.016667 | 0.609847 | 0.558824 | 0 | 0 | 0 |

### A_OPT2023_T2_SB2_TP9

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 1325, entry dates 249, entry months 12; SKIP 4, EXCLUDED 11, exclusion share 0.008234; conditional FLAT CLOSED 1288.
Net -502.083333 R; PF R / price 0.671099 / 0.676804; expectancy -0.378931 R; win rate 0.187170; average winner / loser 4.130914 / -1.429354 R.
Conditional CLOSED-only DD 521.183333 R; largest winner share 0.014642; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 12 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 104 | -78.783333 | 0.377699 | 0.376623 | 5 | 0 | 2 |
| 2023-02 | 103 | -2.416667 | 0.978560 | 1.069328 | 4 | 0 | 2 |
| 2023-03 | 123 | -60.383333 | 0.561963 | 0.599650 | 3 | 0 | 3 |
| 2023-04 | 118 | -8.266667 | 0.934668 | 1.066922 | 5 | 3 | 1 |
| 2023-05 | 110 | -48.516667 | 0.623220 | 0.522059 | 3 | 1 | 0 |
| 2023-06 | 114 | -43.366667 | 0.682257 | 0.714058 | 4 | 0 | 2 |
| 2023-07 | 108 | -38.616667 | 0.683643 | 0.641343 | 1 | 0 | 0 |
| 2023-08 | 82 | -18.683333 | 0.806256 | 0.869159 | 2 | 0 | 0 |
| 2023-09 | 109 | -50.033333 | 0.596993 | 0.613462 | 2 | 0 | 0 |
| 2023-10 | 100 | -34.866667 | 0.691718 | 0.684426 | 0 | 0 | 0 |
| 2023-11 | 140 | -67.966667 | 0.591955 | 0.542700 | 1 | 0 | 1 |
| 2023-12 | 114 | -50.183333 | 0.629050 | 0.577371 | 0 | 0 | 0 |

### A_OPT2023_T2_SB2_TP10

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 1324, entry dates 249, entry months 12; SKIP 4, EXCLUDED 11, exclusion share 0.008240; conditional FLAT CLOSED 1287.
Net -487.950000 R; PF R / price 0.680413 / 0.688664; expectancy -0.368542 R; win rate 0.186556; average winner / loser 4.205938 / -1.429604 R.
Conditional CLOSED-only DD 490.383333 R; largest winner share 0.016043; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 12 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 104 | -77.450000 | 0.388231 | 0.391466 | 5 | 0 | 2 |
| 2023-02 | 103 | -2.916667 | 0.974124 | 1.060924 | 4 | 0 | 2 |
| 2023-03 | 123 | -60.383333 | 0.561963 | 0.599650 | 3 | 0 | 3 |
| 2023-04 | 118 | -5.433333 | 0.957060 | 1.093690 | 5 | 3 | 1 |
| 2023-05 | 110 | -43.516667 | 0.662050 | 0.549632 | 3 | 1 | 0 |
| 2023-06 | 114 | -39.200000 | 0.712785 | 0.749201 | 4 | 0 | 2 |
| 2023-07 | 108 | -34.116667 | 0.720508 | 0.673145 | 1 | 0 | 0 |
| 2023-08 | 82 | -15.850000 | 0.835638 | 0.901869 | 2 | 0 | 0 |
| 2023-09 | 109 | -48.366667 | 0.610418 | 0.623077 | 2 | 0 | 0 |
| 2023-10 | 100 | -33.366667 | 0.704981 | 0.696721 | 0 | 0 | 0 |
| 2023-11 | 139 | -63.500000 | 0.615540 | 0.564673 | 1 | 0 | 1 |
| 2023-12 | 114 | -63.850000 | 0.533771 | 0.518152 | 0 | 0 | 0 |

### A_OPT2023_T3_SB1_TP2

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 237, entry dates 149, entry months 12; SKIP 2, EXCLUDED 2, exclusion share 0.008368; conditional FLAT CLOSED 190.
Net -100.150000 R; PF R / price 0.619443 / 0.625000; expectancy -0.422574 R; win rate 0.244726; average winner / loser 2.810632 / -1.503810 R.
Conditional CLOSED-only DD 107.783333 R; largest winner share 0.020448; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 22 | -10.166667 | 0.598155 | 0.638298 | 5 | 0 | 0 |
| 2023-02 | 23 | -2.466667 | 0.898907 | 0.833333 | 4 | 0 | 0 |
| 2023-03 | 25 | 10.666667 | 1.528053 | 1.613333 | 3 | 0 | 2 |
| 2023-04 | 26 | -20.883333 | 0.361040 | 0.406504 | 5 | 2 | 0 |
| 2023-05 | 16 | -8.016667 | 0.577700 | 0.579710 | 3 | 0 | 0 |
| 2023-06 | 14 | -4.366667 | 0.684337 | 0.566667 | 4 | 0 | 0 |
| 2023-07 | 17 | -18.166667 | 0.180451 | 0.150000 | 1 | 0 | 0 |
| 2023-08 | 12 | -9.033333 | 0.412148 | 0.372881 | 2 | 0 | 0 |
| 2023-09 | 25 | -10.500000 | 0.610630 | 0.557692 | 2 | 0 | 0 |
| 2023-10 | 13 | -4.783333 | 0.659145 | 0.711538 | 0 | 0 | 0 |
| 2023-11 | 26 | -3.466667 | 0.858311 | 0.869565 | 1 | 0 | 0 |
| 2023-12 | 18 | -18.966667 | 0.234186 | 0.295455 | 0 | 0 | 0 |

### A_OPT2023_T3_SB1_TP3

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 235, entry dates 149, entry months 12; SKIP 2, EXCLUDED 2, exclusion share 0.008439; conditional FLAT CLOSED 188.
Net -81.066667 R; PF R / price 0.699345 / 0.708374; expectancy -0.344965 R; win rate 0.212766; average winner / loser 3.771333 / -1.497963 R.
Conditional CLOSED-only DD 92.466667 R; largest winner share 0.026516; largest positive month share 0.857639. Positive / negative / zero months 4 / 8 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 22 | -13.600000 | 0.492537 | 0.520000 | 5 | 0 | 0 |
| 2023-02 | 23 | 1.866667 | 1.076503 | 0.979167 | 4 | 0 | 0 |
| 2023-03 | 25 | 16.466667 | 1.753049 | 1.900000 | 3 | 0 | 2 |
| 2023-04 | 26 | -14.983333 | 0.541560 | 0.609756 | 5 | 2 | 0 |
| 2023-05 | 16 | -3.283333 | 0.827041 | 0.826087 | 3 | 0 | 0 |
| 2023-06 | 14 | 0.366667 | 1.026506 | 0.850000 | 4 | 0 | 0 |
| 2023-07 | 17 | -16.500000 | 0.255639 | 0.212500 | 1 | 0 | 0 |
| 2023-08 | 12 | -9.533333 | 0.379610 | 0.372881 | 2 | 0 | 0 |
| 2023-09 | 24 | -7.766667 | 0.713759 | 0.689320 | 2 | 0 | 0 |
| 2023-10 | 13 | -14.533333 | 0.146771 | 0.156250 | 0 | 0 | 0 |
| 2023-11 | 26 | 0.500000 | 1.020161 | 1.075269 | 1 | 0 | 0 |
| 2023-12 | 17 | -20.066667 | 0.183175 | 0.204545 | 0 | 0 | 0 |

### A_OPT2023_T3_SB1_TP4

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 233, entry dates 149, entry months 12; SKIP 2, EXCLUDED 2, exclusion share 0.008511; conditional FLAT CLOSED 187.
Net -106.200000 R; PF R / price 0.618900 / 0.615019; expectancy -0.455794 R; win rate 0.180258; average winner / loser 4.106349 / -1.498208 R.
Conditional CLOSED-only DD 108.083333 R; largest winner share 0.038655; largest positive month share 0.887417. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 22 | -22.666667 | 0.203747 | 0.238095 | 5 | 0 | 0 |
| 2023-02 | 22 | -4.533333 | 0.814208 | 0.770833 | 4 | 0 | 0 |
| 2023-03 | 25 | 8.933333 | 1.358289 | 1.478261 | 3 | 0 | 2 |
| 2023-04 | 25 | -19.283333 | 0.409995 | 0.447154 | 5 | 2 | 0 |
| 2023-05 | 16 | -2.883333 | 0.848112 | 0.884058 | 3 | 0 | 0 |
| 2023-06 | 14 | -1.900000 | 0.875274 | 0.597015 | 4 | 0 | 0 |
| 2023-07 | 17 | -14.833333 | 0.330827 | 0.275000 | 1 | 0 | 0 |
| 2023-08 | 12 | -8.033333 | 0.477223 | 0.474576 | 2 | 0 | 0 |
| 2023-09 | 24 | -1.533333 | 0.943489 | 0.912621 | 2 | 0 | 0 |
| 2023-10 | 13 | -14.533333 | 0.146771 | 0.156250 | 0 | 0 | 0 |
| 2023-11 | 26 | 1.133333 | 1.043257 | 1.020000 | 1 | 0 | 0 |
| 2023-12 | 17 | -26.066667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### A_OPT2023_T3_SB1_TP5

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 233, entry dates 149, entry months 12; SKIP 2, EXCLUDED 2, exclusion share 0.008511; conditional FLAT CLOSED 187.
Net -116.650000 R; PF R / price 0.586348 / 0.586629; expectancy -0.500644 R; win rate 0.171674; average winner / loser 4.133750 / -1.500000 R.
Conditional CLOSED-only DD 118.533333 R; largest winner share 0.050398; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 22 | -22.666667 | 0.203747 | 0.238095 | 5 | 0 | 0 |
| 2023-02 | 22 | -2.866667 | 0.882514 | 0.822917 | 4 | 0 | 0 |
| 2023-03 | 25 | -4.700000 | 0.823308 | 0.969072 | 3 | 0 | 2 |
| 2023-04 | 25 | -18.783333 | 0.425293 | 0.463415 | 5 | 2 | 0 |
| 2023-05 | 16 | -1.483333 | 0.921861 | 0.985507 | 3 | 0 | 0 |
| 2023-06 | 14 | -0.566667 | 0.962801 | 0.656716 | 4 | 0 | 0 |
| 2023-07 | 17 | -13.166667 | 0.406015 | 0.337500 | 1 | 0 | 0 |
| 2023-08 | 12 | -6.533333 | 0.574837 | 0.576271 | 2 | 0 | 0 |
| 2023-09 | 24 | -10.050000 | 0.651042 | 0.675926 | 2 | 0 | 0 |
| 2023-10 | 13 | -14.533333 | 0.146771 | 0.156250 | 0 | 0 | 0 |
| 2023-11 | 26 | 4.766667 | 1.181934 | 1.120000 | 1 | 0 | 0 |
| 2023-12 | 17 | -26.066667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### A_OPT2023_T3_SB1_TP6

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 231, entry dates 149, entry months 12; SKIP 2, EXCLUDED 2, exclusion share 0.008584; conditional FLAT CLOSED 185.
Net -122.400000 R; PF R / price 0.563636 / 0.558712; expectancy -0.529870 R; win rate 0.168831; average winner / loser 4.053846 / -1.500000 R.
Conditional CLOSED-only DD 124.283333 R; largest winner share 0.063251; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 22 | -22.666667 | 0.203747 | 0.238095 | 5 | 0 | 0 |
| 2023-02 | 22 | -1.200000 | 0.950820 | 0.875000 | 4 | 0 | 0 |
| 2023-03 | 25 | -4.700000 | 0.823308 | 0.969072 | 3 | 0 | 2 |
| 2023-04 | 25 | -17.283333 | 0.471188 | 0.512195 | 5 | 2 | 0 |
| 2023-05 | 16 | -0.083333 | 0.995610 | 1.086957 | 3 | 0 | 0 |
| 2023-06 | 14 | 1.100000 | 1.072210 | 0.731343 | 4 | 0 | 0 |
| 2023-07 | 17 | -11.500000 | 0.481203 | 0.400000 | 1 | 0 | 0 |
| 2023-08 | 12 | -5.033333 | 0.672451 | 0.677966 | 2 | 0 | 0 |
| 2023-09 | 24 | -14.383333 | 0.500579 | 0.444444 | 2 | 0 | 0 |
| 2023-10 | 13 | -14.533333 | 0.146771 | 0.156250 | 0 | 0 | 0 |
| 2023-11 | 24 | -6.050000 | 0.755061 | 0.744681 | 1 | 0 | 0 |
| 2023-12 | 17 | -26.066667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### A_OPT2023_T3_SB1_TP7

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 231, entry dates 149, entry months 12; SKIP 2, EXCLUDED 2, exclusion share 0.008584; conditional FLAT CLOSED 185.
Net -116.666667 R; PF R / price 0.584076 / 0.580492; expectancy -0.505051 R; win rate 0.168831; average winner / loser 4.200855 / -1.500000 R.
Conditional CLOSED-only DD 118.550000 R; largest winner share 0.071211; largest positive month share 0.738318. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 22 | -22.666667 | 0.203747 | 0.238095 | 5 | 0 | 0 |
| 2023-02 | 22 | 0.466667 | 1.019126 | 0.927083 | 4 | 0 | 0 |
| 2023-03 | 25 | -4.700000 | 0.823308 | 0.969072 | 3 | 0 | 2 |
| 2023-04 | 25 | -15.783333 | 0.517083 | 0.560976 | 5 | 2 | 0 |
| 2023-05 | 16 | 1.316667 | 1.069359 | 1.188406 | 3 | 0 | 0 |
| 2023-06 | 14 | -0.233333 | 0.984683 | 0.671642 | 4 | 0 | 0 |
| 2023-07 | 17 | -12.166667 | 0.451128 | 0.375000 | 1 | 0 | 0 |
| 2023-08 | 12 | -3.533333 | 0.770065 | 0.779661 | 2 | 0 | 0 |
| 2023-09 | 24 | -12.716667 | 0.558449 | 0.490741 | 2 | 0 | 0 |
| 2023-10 | 13 | -14.533333 | 0.146771 | 0.156250 | 0 | 0 | 0 |
| 2023-11 | 24 | -6.050000 | 0.755061 | 0.744681 | 1 | 0 | 0 |
| 2023-12 | 17 | -26.066667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### A_OPT2023_T3_SB1_TP8

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 230, entry dates 149, entry months 12; SKIP 2, EXCLUDED 2, exclusion share 0.008621; conditional FLAT CLOSED 184.
Net -112.233333 R; PF R / price 0.597730 / 0.588571; expectancy -0.487971 R; win rate 0.169565; average winner / loser 4.276068 / -1.500000 R.
Conditional CLOSED-only DD 114.116667 R; largest winner share 0.079952; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 22 | -22.666667 | 0.203747 | 0.238095 | 5 | 0 | 0 |
| 2023-02 | 22 | 2.133333 | 1.087432 | 0.979167 | 4 | 0 | 0 |
| 2023-03 | 25 | -4.700000 | 0.823308 | 0.969072 | 3 | 0 | 2 |
| 2023-04 | 25 | -14.283333 | 0.562978 | 0.609756 | 5 | 2 | 0 |
| 2023-05 | 15 | -0.583333 | 0.966635 | 1.031746 | 3 | 0 | 0 |
| 2023-06 | 14 | -0.233333 | 0.984683 | 0.671642 | 4 | 0 | 0 |
| 2023-07 | 17 | -12.166667 | 0.451128 | 0.375000 | 1 | 0 | 0 |
| 2023-08 | 12 | -2.033333 | 0.867679 | 0.881356 | 2 | 0 | 0 |
| 2023-09 | 24 | -11.050000 | 0.616319 | 0.537037 | 2 | 0 | 0 |
| 2023-10 | 13 | -14.533333 | 0.146771 | 0.156250 | 0 | 0 | 0 |
| 2023-11 | 24 | -6.050000 | 0.755061 | 0.744681 | 1 | 0 | 0 |
| 2023-12 | 17 | -26.066667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### A_OPT2023_T3_SB1_TP9

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 230, entry dates 149, entry months 12; SKIP 2, EXCLUDED 2, exclusion share 0.008621; conditional FLAT CLOSED 184.
Net -108.566667 R; PF R / price 0.610872 / 0.601905; expectancy -0.472029 R; win rate 0.169565; average winner / loser 4.370085 / -1.500000 R.
Conditional CLOSED-only DD 110.450000 R; largest winner share 0.088011; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 22 | -22.666667 | 0.203747 | 0.238095 | 5 | 0 | 0 |
| 2023-02 | 22 | 3.800000 | 1.155738 | 1.031250 | 4 | 0 | 0 |
| 2023-03 | 25 | -4.700000 | 0.823308 | 0.969072 | 3 | 0 | 2 |
| 2023-04 | 25 | -12.783333 | 0.608873 | 0.658537 | 5 | 2 | 0 |
| 2023-05 | 15 | -0.583333 | 0.966635 | 1.031746 | 3 | 0 | 0 |
| 2023-06 | 14 | -0.233333 | 0.984683 | 0.671642 | 4 | 0 | 0 |
| 2023-07 | 17 | -12.166667 | 0.451128 | 0.375000 | 1 | 0 | 0 |
| 2023-08 | 12 | -0.533333 | 0.965293 | 0.983051 | 2 | 0 | 0 |
| 2023-09 | 24 | -12.050000 | 0.581597 | 0.509259 | 2 | 0 | 0 |
| 2023-10 | 13 | -14.533333 | 0.146771 | 0.156250 | 0 | 0 | 0 |
| 2023-11 | 24 | -6.050000 | 0.755061 | 0.744681 | 1 | 0 | 0 |
| 2023-12 | 17 | -26.066667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### A_OPT2023_T3_SB1_TP10

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 230, entry dates 149, entry months 12; SKIP 2, EXCLUDED 2, exclusion share 0.008621; conditional FLAT CLOSED 184.
Net -103.900000 R; PF R / price 0.627599 / 0.618095; expectancy -0.451739 R; win rate 0.169565; average winner / loser 4.489744 / -1.500000 R.
Conditional CLOSED-only DD 105.783333 R; largest winner share 0.095184; largest positive month share 0.849741. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 22 | -22.666667 | 0.203747 | 0.238095 | 5 | 0 | 0 |
| 2023-02 | 22 | 5.466667 | 1.224044 | 1.083333 | 4 | 0 | 0 |
| 2023-03 | 25 | -4.700000 | 0.823308 | 0.969072 | 3 | 0 | 2 |
| 2023-04 | 25 | -11.283333 | 0.654768 | 0.707317 | 5 | 2 | 0 |
| 2023-05 | 15 | -0.583333 | 0.966635 | 1.031746 | 3 | 0 | 0 |
| 2023-06 | 14 | -0.233333 | 0.984683 | 0.671642 | 4 | 0 | 0 |
| 2023-07 | 17 | -12.166667 | 0.451128 | 0.375000 | 1 | 0 | 0 |
| 2023-08 | 12 | 0.966667 | 1.062907 | 1.084746 | 2 | 0 | 0 |
| 2023-09 | 24 | -12.050000 | 0.581597 | 0.509259 | 2 | 0 | 0 |
| 2023-10 | 13 | -14.533333 | 0.146771 | 0.156250 | 0 | 0 | 0 |
| 2023-11 | 24 | -6.050000 | 0.755061 | 0.744681 | 1 | 0 | 0 |
| 2023-12 | 17 | -26.066667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### A_OPT2023_T3_SB2_TP2

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 313, entry dates 181, entry months 12; SKIP 2, EXCLUDED 4, exclusion share 0.012618; conditional FLAT CLOSED 292.
Net -111.583333 R; PF R / price 0.661356 / 0.676513; expectancy -0.356496 R; win rate 0.255591; average winner / loser 2.723958 / -1.445175 R.
Conditional CLOSED-only DD 125.116667 R; largest winner share 0.015296; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 12 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 32 | -6.833333 | 0.788877 | 0.781955 | 5 | 0 | 1 |
| 2023-02 | 25 | -0.716667 | 0.970056 | 0.953704 | 4 | 0 | 1 |
| 2023-03 | 35 | -1.750000 | 0.947917 | 1.135338 | 3 | 0 | 2 |
| 2023-04 | 33 | -20.066667 | 0.459605 | 0.521739 | 5 | 2 | 0 |
| 2023-05 | 24 | -0.950000 | 0.960663 | 0.851485 | 3 | 0 | 0 |
| 2023-06 | 18 | -7.266667 | 0.609319 | 0.674699 | 4 | 0 | 0 |
| 2023-07 | 21 | -13.833333 | 0.371212 | 0.282828 | 1 | 0 | 0 |
| 2023-08 | 19 | -14.733333 | 0.382682 | 0.382979 | 2 | 0 | 0 |
| 2023-09 | 25 | -16.466667 | 0.420868 | 0.434109 | 2 | 0 | 0 |
| 2023-10 | 21 | -7.333333 | 0.678363 | 0.663043 | 0 | 0 | 0 |
| 2023-11 | 34 | -1.066667 | 0.964345 | 1.008130 | 1 | 0 | 0 |
| 2023-12 | 26 | -20.566667 | 0.371050 | 0.378788 | 0 | 0 | 0 |

### A_OPT2023_T3_SB2_TP3

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 309, entry dates 181, entry months 12; SKIP 2, EXCLUDED 4, exclusion share 0.012780; conditional FLAT CLOSED 289.
Net -114.466667 R; PF R / price 0.664747 / 0.663421; expectancy -0.370442 R; win rate 0.213592; average winner / loser 3.438889 / -1.446751 R.
Conditional CLOSED-only DD 123.333333 R; largest winner share 0.022030; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 31 | -14.833333 | 0.562008 | 0.489209 | 5 | 0 | 1 |
| 2023-02 | 24 | -3.100000 | 0.870474 | 0.851852 | 4 | 0 | 1 |
| 2023-03 | 35 | -2.366667 | 0.935041 | 1.068027 | 3 | 0 | 2 |
| 2023-04 | 32 | -12.966667 | 0.637127 | 0.707792 | 5 | 2 | 0 |
| 2023-05 | 24 | -2.366667 | 0.908328 | 0.858491 | 3 | 0 | 0 |
| 2023-06 | 18 | -9.766667 | 0.510033 | 0.472527 | 4 | 0 | 0 |
| 2023-07 | 21 | -10.666667 | 0.515152 | 0.393939 | 1 | 0 | 0 |
| 2023-08 | 19 | -13.666667 | 0.427374 | 0.425532 | 2 | 0 | 0 |
| 2023-09 | 25 | -10.733333 | 0.622509 | 0.643411 | 2 | 0 | 0 |
| 2023-10 | 21 | -14.366667 | 0.444588 | 0.413462 | 0 | 0 | 0 |
| 2023-11 | 34 | 4.333333 | 1.137203 | 1.242188 | 1 | 0 | 0 |
| 2023-12 | 25 | -23.966667 | 0.294406 | 0.215827 | 0 | 0 | 0 |

### A_OPT2023_T3_SB2_TP4

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 308, entry dates 180, entry months 12; SKIP 2, EXCLUDED 5, exclusion share 0.015974; conditional FLAT CLOSED 288.
Net -148.716667 R; PF R / price 0.579699 / 0.589226; expectancy -0.482846 R; win rate 0.185065; average winner / loser 3.598538 / -1.450137 R.
Conditional CLOSED-only DD 159.250000 R; largest winner share 0.032502; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 31 | -11.500000 | 0.660433 | 0.561151 | 5 | 0 | 1 |
| 2023-02 | 23 | -7.433333 | 0.689415 | 0.722222 | 4 | 0 | 2 |
| 2023-03 | 35 | -7.600000 | 0.799649 | 0.901961 | 3 | 0 | 2 |
| 2023-04 | 32 | -14.366667 | 0.613106 | 0.664596 | 5 | 2 | 0 |
| 2023-05 | 24 | -13.866667 | 0.524300 | 0.612069 | 3 | 0 | 0 |
| 2023-06 | 18 | -8.016667 | 0.597826 | 0.549451 | 4 | 0 | 0 |
| 2023-07 | 21 | -15.833333 | 0.330986 | 0.288462 | 1 | 0 | 0 |
| 2023-08 | 19 | -10.600000 | 0.555866 | 0.553191 | 2 | 0 | 0 |
| 2023-09 | 25 | -15.900000 | 0.468820 | 0.511111 | 2 | 0 | 0 |
| 2023-10 | 21 | -24.033333 | 0.127119 | 0.146789 | 0 | 0 | 0 |
| 2023-11 | 34 | 6.400000 | 1.194430 | 1.191176 | 1 | 0 | 0 |
| 2023-12 | 25 | -25.966667 | 0.235525 | 0.172662 | 0 | 0 | 0 |

### A_OPT2023_T3_SB2_TP5

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 306, entry dates 180, entry months 12; SKIP 2, EXCLUDED 5, exclusion share 0.016077; conditional FLAT CLOSED 286.
Net -150.083333 R; PF R / price 0.576156 / 0.583951; expectancy -0.490468 R; win rate 0.179739; average winner / loser 3.709394 / -1.451230 R.
Conditional CLOSED-only DD 162.283333 R; largest winner share 0.040846; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 31 | -8.166667 | 0.758858 | 0.633094 | 5 | 0 | 1 |
| 2023-02 | 23 | -5.933333 | 0.752089 | 0.777778 | 4 | 0 | 2 |
| 2023-03 | 35 | -5.433333 | 0.856766 | 0.947712 | 3 | 0 | 2 |
| 2023-04 | 32 | -9.966667 | 0.731598 | 0.788820 | 5 | 2 | 0 |
| 2023-05 | 24 | -12.533333 | 0.570040 | 0.681034 | 3 | 0 | 0 |
| 2023-06 | 18 | -6.516667 | 0.673077 | 0.615385 | 4 | 0 | 0 |
| 2023-07 | 21 | -14.333333 | 0.394366 | 0.346154 | 1 | 0 | 0 |
| 2023-08 | 19 | -17.533333 | 0.313316 | 0.393939 | 2 | 0 | 0 |
| 2023-09 | 25 | -18.900000 | 0.368597 | 0.355556 | 2 | 0 | 0 |
| 2023-10 | 21 | -24.033333 | 0.127119 | 0.146789 | 0 | 0 | 0 |
| 2023-11 | 32 | 2.566667 | 1.081438 | 1.038760 | 1 | 0 | 0 |
| 2023-12 | 25 | -29.300000 | 0.137390 | 0.100719 | 0 | 0 | 0 |

### A_OPT2023_T3_SB2_TP6

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 306, entry dates 180, entry months 12; SKIP 2, EXCLUDED 5, exclusion share 0.016077; conditional FLAT CLOSED 286.
Net -148.783333 R; PF R / price 0.579827 / 0.590695; expectancy -0.486220 R; win rate 0.179739; average winner / loser 3.733030 / -1.451230 R.
Conditional CLOSED-only DD 154.316667 R; largest winner share 0.048705; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 31 | -13.166667 | 0.611220 | 0.525180 | 5 | 0 | 1 |
| 2023-02 | 23 | -4.433333 | 0.814763 | 0.833333 | 4 | 0 | 2 |
| 2023-03 | 35 | -3.766667 | 0.900703 | 0.980392 | 3 | 0 | 2 |
| 2023-04 | 32 | -12.900000 | 0.652603 | 0.720497 | 5 | 2 | 0 |
| 2023-05 | 24 | -11.200000 | 0.615780 | 0.750000 | 3 | 0 | 0 |
| 2023-06 | 18 | -7.516667 | 0.622910 | 0.571429 | 4 | 0 | 0 |
| 2023-07 | 21 | -14.833333 | 0.373239 | 0.326923 | 1 | 0 | 0 |
| 2023-08 | 19 | -16.133333 | 0.368146 | 0.464646 | 2 | 0 | 0 |
| 2023-09 | 25 | -17.400000 | 0.418708 | 0.400000 | 2 | 0 | 0 |
| 2023-10 | 21 | -24.033333 | 0.127119 | 0.146789 | 0 | 0 | 0 |
| 2023-11 | 32 | 5.900000 | 1.187203 | 1.116279 | 1 | 0 | 0 |
| 2023-12 | 25 | -29.300000 | 0.137390 | 0.100719 | 0 | 0 | 0 |

### A_OPT2023_T3_SB2_TP7

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 305, entry dates 180, entry months 12; SKIP 2, EXCLUDED 5, exclusion share 0.016129; conditional FLAT CLOSED 285.
Net -165.500000 R; PF R / price 0.535156 / 0.559219; expectancy -0.542623 R; win rate 0.173770; average winner / loser 3.594969 / -1.453197 R.
Conditional CLOSED-only DD 171.033333 R; largest winner share 0.061232; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 12 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 31 | -24.833333 | 0.301126 | 0.298611 | 5 | 0 | 1 |
| 2023-02 | 23 | -2.933333 | 0.877437 | 0.888889 | 4 | 0 | 2 |
| 2023-03 | 35 | -2.100000 | 0.944640 | 1.013072 | 3 | 0 | 2 |
| 2023-04 | 32 | -11.500000 | 0.690305 | 0.763975 | 5 | 2 | 0 |
| 2023-05 | 23 | -12.466667 | 0.550751 | 0.651376 | 3 | 0 | 0 |
| 2023-06 | 18 | -7.516667 | 0.622910 | 0.571429 | 4 | 0 | 0 |
| 2023-07 | 21 | -14.833333 | 0.373239 | 0.326923 | 1 | 0 | 0 |
| 2023-08 | 19 | -14.733333 | 0.422977 | 0.535354 | 2 | 0 | 0 |
| 2023-09 | 25 | -17.150000 | 0.427060 | 0.407407 | 2 | 0 | 0 |
| 2023-10 | 21 | -24.033333 | 0.127119 | 0.146789 | 0 | 0 | 0 |
| 2023-11 | 32 | -4.100000 | 0.876444 | 0.888060 | 1 | 0 | 0 |
| 2023-12 | 25 | -29.300000 | 0.137390 | 0.100719 | 0 | 0 | 0 |

### A_OPT2023_T3_SB2_TP8

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 305, entry dates 180, entry months 12; SKIP 2, EXCLUDED 5, exclusion share 0.016129; conditional FLAT CLOSED 285.
Net -157.866667 R; PF R / price 0.556596 / 0.579408; expectancy -0.517596 R; win rate 0.173770; average winner / loser 3.738994 / -1.453197 R.
Conditional CLOSED-only DD 163.400000 R; largest winner share 0.067283; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 12 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 31 | -24.833333 | 0.301126 | 0.298611 | 5 | 0 | 1 |
| 2023-02 | 23 | -1.433333 | 0.940111 | 0.944444 | 4 | 0 | 2 |
| 2023-03 | 35 | -0.433333 | 0.988576 | 1.045752 | 3 | 0 | 2 |
| 2023-04 | 32 | -10.100000 | 0.728007 | 0.807453 | 5 | 2 | 0 |
| 2023-05 | 23 | -12.466667 | 0.550751 | 0.651376 | 3 | 0 | 0 |
| 2023-06 | 18 | -7.516667 | 0.622910 | 0.571429 | 4 | 0 | 0 |
| 2023-07 | 21 | -14.833333 | 0.373239 | 0.326923 | 1 | 0 | 0 |
| 2023-08 | 19 | -13.333333 | 0.477807 | 0.606061 | 2 | 0 | 0 |
| 2023-09 | 25 | -17.150000 | 0.427060 | 0.407407 | 2 | 0 | 0 |
| 2023-10 | 21 | -24.033333 | 0.127119 | 0.146789 | 0 | 0 | 0 |
| 2023-11 | 32 | -2.433333 | 0.926670 | 0.925373 | 1 | 0 | 0 |
| 2023-12 | 25 | -29.300000 | 0.137390 | 0.100719 | 0 | 0 | 0 |

### A_OPT2023_T3_SB2_TP9

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 305, entry dates 180, entry months 12; SKIP 2, EXCLUDED 5, exclusion share 0.016129; conditional FLAT CLOSED 285.
Net -150.233333 R; PF R / price 0.578036 / 0.599596; expectancy -0.492568 R; win rate 0.173770; average winner / loser 3.883019 / -1.453197 R.
Conditional CLOSED-only DD 155.766667 R; largest winner share 0.072886; largest positive month share 0.948718. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 31 | -24.833333 | 0.301126 | 0.298611 | 5 | 0 | 1 |
| 2023-02 | 23 | 0.066667 | 1.002786 | 1.000000 | 4 | 0 | 2 |
| 2023-03 | 35 | 1.233333 | 1.032513 | 1.078431 | 3 | 0 | 2 |
| 2023-04 | 32 | -8.700000 | 0.765709 | 0.850932 | 5 | 2 | 0 |
| 2023-05 | 23 | -12.466667 | 0.550751 | 0.651376 | 3 | 0 | 0 |
| 2023-06 | 18 | -7.516667 | 0.622910 | 0.571429 | 4 | 0 | 0 |
| 2023-07 | 21 | -14.833333 | 0.373239 | 0.326923 | 1 | 0 | 0 |
| 2023-08 | 19 | -11.933333 | 0.532637 | 0.676768 | 2 | 0 | 0 |
| 2023-09 | 25 | -17.150000 | 0.427060 | 0.407407 | 2 | 0 | 0 |
| 2023-10 | 21 | -24.033333 | 0.127119 | 0.146789 | 0 | 0 | 0 |
| 2023-11 | 32 | -0.766667 | 0.976896 | 0.962687 | 1 | 0 | 0 |
| 2023-12 | 25 | -29.300000 | 0.137390 | 0.100719 | 0 | 0 | 0 |

### A_OPT2023_T3_SB2_TP10

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 305, entry dates 180, entry months 12; SKIP 2, EXCLUDED 5, exclusion share 0.016129; conditional FLAT CLOSED 285.
Net -142.600000 R; PF R / price 0.599476 / 0.619785; expectancy -0.467541 R; win rate 0.173770; average winner / loser 4.027044 / -1.453197 R.
Conditional CLOSED-only DD 148.133333 R; largest winner share 0.078088; largest positive month share 0.540373. Positive / negative / zero months 3 / 9 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 31 | -24.833333 | 0.301126 | 0.298611 | 5 | 0 | 1 |
| 2023-02 | 23 | 1.566667 | 1.065460 | 1.055556 | 4 | 0 | 2 |
| 2023-03 | 35 | 2.900000 | 1.076450 | 1.111111 | 3 | 0 | 2 |
| 2023-04 | 32 | -7.300000 | 0.803411 | 0.894410 | 5 | 2 | 0 |
| 2023-05 | 23 | -12.466667 | 0.550751 | 0.651376 | 3 | 0 | 0 |
| 2023-06 | 18 | -7.516667 | 0.622910 | 0.571429 | 4 | 0 | 0 |
| 2023-07 | 21 | -14.833333 | 0.373239 | 0.326923 | 1 | 0 | 0 |
| 2023-08 | 19 | -10.533333 | 0.587467 | 0.747475 | 2 | 0 | 0 |
| 2023-09 | 25 | -17.150000 | 0.427060 | 0.407407 | 2 | 0 | 0 |
| 2023-10 | 21 | -24.033333 | 0.127119 | 0.146789 | 0 | 0 | 0 |
| 2023-11 | 32 | 0.900000 | 1.027122 | 1.000000 | 1 | 0 | 0 |
| 2023-12 | 25 | -29.300000 | 0.137390 | 0.100719 | 0 | 0 | 0 |

### A_OPT2023_T4_SB1_TP2

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors.
CLOSED 56, entry dates 53, entry months 12; SKIP 0, EXCLUDED 0, exclusion share 0.000000; conditional FLAT CLOSED 0.
Net -21.700000 R; PF R / price 0.645618 / 0.630435; expectancy -0.387500 R; win rate 0.267857; average winner / loser 2.635556 / -1.530833 R.
Conditional CLOSED-only DD 28.500000 R; largest winner share 0.084317; largest positive month share 0.454810. Positive / negative / zero months 5 / 7 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 8 | -10.733333 | 0.030120 | 0.025641 | 5 | 0 | 0 |
| 2023-02 | 2 | -3.000000 | 0.000000 | 0.000000 | 4 | 0 | 0 |
| 2023-03 | 4 | 0.233333 | 1.080460 | 1.153846 | 3 | 0 | 0 |
| 2023-04 | 3 | -4.666667 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 1 | 3.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 3 | 0 | 0 |
| 2023-06 | 3 | -0.166667 | 0.947368 | 1.090909 | 4 | 0 | 0 |
| 2023-07 | 5 | -2.733333 | 0.549451 | 0.416667 | 1 | 0 | 0 |
| 2023-08 | 6 | -8.766667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 7 | 5.200000 | 2.258065 | 2.428571 | 2 | 0 | 0 |
| 2023-10 | 3 | 0.166667 | 1.052632 | 0.909091 | 0 | 0 | 0 |
| 2023-11 | 9 | 2.833333 | 1.358650 | 1.464286 | 1 | 0 | 0 |
| 2023-12 | 5 | -3.066667 | 0.520833 | 0.454545 | 0 | 0 | 0 |

### A_OPT2023_T4_SB1_TP3

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 56, entry dates 53, entry months 12; SKIP 0, EXCLUDED 0, exclusion share 0.000000; conditional FLAT CLOSED 0.
Net -28.300000 R; PF R / price 0.581154 / 0.583333; expectancy -0.505357 R; win rate 0.196429; average winner / loser 3.569697 / -1.535606 R.
Conditional CLOSED-only DD 32.733333 R; largest winner share 0.127334; largest positive month share 0.523256. Positive / negative / zero months 4 / 8 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 8 | -10.733333 | 0.030120 | 0.025641 | 5 | 0 | 0 |
| 2023-02 | 2 | -3.000000 | 0.000000 | 0.000000 | 4 | 0 | 0 |
| 2023-03 | 4 | 1.633333 | 1.563218 | 1.692308 | 3 | 0 | 0 |
| 2023-04 | 3 | -4.666667 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 1 | -1.500000 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-06 | 3 | 1.333333 | 1.421053 | 1.636364 | 4 | 0 | 0 |
| 2023-07 | 5 | -1.066667 | 0.824176 | 0.625000 | 1 | 0 | 0 |
| 2023-08 | 6 | -8.766667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 7 | 3.866667 | 1.686391 | 1.650000 | 2 | 0 | 0 |
| 2023-10 | 3 | -4.833333 | 0.000000 | 0.000000 | 0 | 0 | 0 |
| 2023-11 | 9 | 7.500000 | 1.949367 | 2.071429 | 1 | 0 | 0 |
| 2023-12 | 5 | -8.066667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### A_OPT2023_T4_SB1_TP4

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 56, entry dates 53, entry months 12; SKIP 0, EXCLUDED 0, exclusion share 0.000000; conditional FLAT CLOSED 0.
Net -34.150000 R; PF R / price 0.515374 / 0.475472; expectancy -0.609821 R; win rate 0.160714; average winner / loser 4.035185 / -1.531884 R.
Conditional CLOSED-only DD 39.500000 R; largest winner share 0.183570; largest positive month share 0.524403. Positive / negative / zero months 3 / 9 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 8 | -10.733333 | 0.030120 | 0.025641 | 5 | 0 | 0 |
| 2023-02 | 2 | -3.000000 | 0.000000 | 0.000000 | 4 | 0 | 0 |
| 2023-03 | 4 | -3.966667 | 0.077519 | 0.050000 | 3 | 0 | 0 |
| 2023-04 | 3 | -4.666667 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 1 | -1.500000 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-06 | 3 | -4.666667 | 0.000000 | 0.000000 | 4 | 0 | 0 |
| 2023-07 | 5 | 0.600000 | 1.098901 | 0.833333 | 1 | 0 | 0 |
| 2023-08 | 6 | -8.766667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 7 | 7.033333 | 2.248521 | 2.200000 | 2 | 0 | 0 |
| 2023-10 | 3 | -4.833333 | 0.000000 | 0.000000 | 0 | 0 | 0 |
| 2023-11 | 9 | 8.416667 | 2.065401 | 2.142857 | 1 | 0 | 0 |
| 2023-12 | 5 | -8.066667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### A_OPT2023_T4_SB1_TP5

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors.
CLOSED 56, entry dates 53, entry months 12; SKIP 0, EXCLUDED 0, exclusion share 0.000000; conditional FLAT CLOSED 0.
Net -29.150000 R; PF R / price 0.586329 / 0.532075; expectancy -0.520536 R; win rate 0.160714; average winner / loser 4.590741 / -1.531884 R.
Conditional CLOSED-only DD 36.700000 R; largest winner share 0.201694; largest positive month share 0.484561. Positive / negative / zero months 3 / 9 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 8 | -10.733333 | 0.030120 | 0.025641 | 5 | 0 | 0 |
| 2023-02 | 2 | -3.000000 | 0.000000 | 0.000000 | 4 | 0 | 0 |
| 2023-03 | 4 | -3.966667 | 0.077519 | 0.050000 | 3 | 0 | 0 |
| 2023-04 | 3 | -4.666667 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 1 | -1.500000 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-06 | 3 | -4.666667 | 0.000000 | 0.000000 | 4 | 0 | 0 |
| 2023-07 | 5 | 2.266667 | 1.373626 | 1.041667 | 1 | 0 | 0 |
| 2023-08 | 6 | -8.766667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 7 | 10.200000 | 2.810651 | 2.750000 | 2 | 0 | 0 |
| 2023-10 | 3 | -4.833333 | 0.000000 | 0.000000 | 0 | 0 | 0 |
| 2023-11 | 9 | 8.583333 | 2.086498 | 2.107143 | 1 | 0 | 0 |
| 2023-12 | 5 | -8.066667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### A_OPT2023_T4_SB1_TP6

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors.
CLOSED 56, entry dates 53, entry months 12; SKIP 0, EXCLUDED 0, exclusion share 0.000000; conditional FLAT CLOSED 0.
Net -22.650000 R; PF R / price 0.678571 / 0.611321; expectancy -0.404464 R; win rate 0.160714; average winner / loser 5.312963 / -1.531884 R.
Conditional CLOSED-only DD 35.033333 R; largest winner share 0.209132; largest positive month share 0.485178. Positive / negative / zero months 3 / 9 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 8 | -10.733333 | 0.030120 | 0.025641 | 5 | 0 | 0 |
| 2023-02 | 2 | -3.000000 | 0.000000 | 0.000000 | 4 | 0 | 0 |
| 2023-03 | 4 | -3.966667 | 0.077519 | 0.050000 | 3 | 0 | 0 |
| 2023-04 | 3 | -4.666667 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 1 | -1.500000 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-06 | 3 | -4.666667 | 0.000000 | 0.000000 | 4 | 0 | 0 |
| 2023-07 | 5 | 3.933333 | 1.648352 | 1.250000 | 1 | 0 | 0 |
| 2023-08 | 6 | -8.766667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 7 | 13.366667 | 3.372781 | 3.300000 | 2 | 0 | 0 |
| 2023-10 | 3 | -4.833333 | 0.000000 | 0.000000 | 0 | 0 | 0 |
| 2023-11 | 9 | 10.250000 | 2.297468 | 2.285714 | 1 | 0 | 0 |
| 2023-12 | 5 | -8.066667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### A_OPT2023_T4_SB1_TP7

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|neighbors.
CLOSED 56, entry dates 53, entry months 12; SKIP 0, EXCLUDED 0, exclusion share 0.000000; conditional FLAT CLOSED 0.
Net -25.150000 R; PF R / price 0.643094 / 0.554717; expectancy -0.449107 R; win rate 0.160714; average winner / loser 5.035185 / -1.531884 R.
Conditional CLOSED-only DD 35.833333 R; largest winner share 0.257448; largest positive month share 0.475715. Positive / negative / zero months 3 / 9 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 8 | -10.733333 | 0.030120 | 0.025641 | 5 | 0 | 0 |
| 2023-02 | 2 | -3.000000 | 0.000000 | 0.000000 | 4 | 0 | 0 |
| 2023-03 | 4 | -3.966667 | 0.077519 | 0.050000 | 3 | 0 | 0 |
| 2023-04 | 3 | -4.666667 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 1 | -1.500000 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-06 | 3 | -4.666667 | 0.000000 | 0.000000 | 4 | 0 | 0 |
| 2023-07 | 5 | 5.600000 | 1.923077 | 1.458333 | 1 | 0 | 0 |
| 2023-08 | 6 | -8.766667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 7 | 7.533333 | 2.337278 | 2.050000 | 2 | 0 | 0 |
| 2023-10 | 3 | -4.833333 | 0.000000 | 0.000000 | 0 | 0 | 0 |
| 2023-11 | 9 | 11.916667 | 2.508439 | 2.464286 | 1 | 0 | 0 |
| 2023-12 | 5 | -8.066667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### A_OPT2023_T4_SB1_TP8

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors.
CLOSED 56, entry dates 53, entry months 12; SKIP 0, EXCLUDED 0, exclusion share 0.000000; conditional FLAT CLOSED 0.
Net -24.816667 R; PF R / price 0.647824 / 0.558491; expectancy -0.443155 R; win rate 0.160714; average winner / loser 5.072222 / -1.531884 R.
Conditional CLOSED-only DD 38.833333 R; largest winner share 0.292077; largest positive month share 0.535128. Positive / negative / zero months 3 / 9 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 8 | -10.733333 | 0.030120 | 0.025641 | 5 | 0 | 0 |
| 2023-02 | 2 | -3.000000 | 0.000000 | 0.000000 | 4 | 0 | 0 |
| 2023-03 | 4 | -3.966667 | 0.077519 | 0.050000 | 3 | 0 | 0 |
| 2023-04 | 3 | -4.666667 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 1 | -1.500000 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-06 | 3 | -4.666667 | 0.000000 | 0.000000 | 4 | 0 | 0 |
| 2023-07 | 5 | 2.600000 | 1.428571 | 1.083333 | 1 | 0 | 0 |
| 2023-08 | 6 | -8.766667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 7 | 9.200000 | 2.633136 | 2.300000 | 2 | 0 | 0 |
| 2023-10 | 3 | -4.833333 | 0.000000 | 0.000000 | 0 | 0 | 0 |
| 2023-11 | 9 | 13.583333 | 2.719409 | 2.642857 | 1 | 0 | 0 |
| 2023-12 | 5 | -8.066667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### A_OPT2023_T4_SB1_TP9

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors.
CLOSED 56, entry dates 53, entry months 12; SKIP 0, EXCLUDED 0, exclusion share 0.000000; conditional FLAT CLOSED 0.
Net -24.150000 R; PF R / price 0.657285 / 0.566038; expectancy -0.431250 R; win rate 0.160714; average winner / loser 5.146296 / -1.531884 R.
Conditional CLOSED-only DD 38.833333 R; largest winner share 0.323858; largest positive month share 0.585413. Positive / negative / zero months 3 / 9 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 8 | -10.733333 | 0.030120 | 0.025641 | 5 | 0 | 0 |
| 2023-02 | 2 | -3.000000 | 0.000000 | 0.000000 | 4 | 0 | 0 |
| 2023-03 | 4 | -3.966667 | 0.077519 | 0.050000 | 3 | 0 | 0 |
| 2023-04 | 3 | -4.666667 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 1 | -1.500000 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-06 | 3 | -4.666667 | 0.000000 | 0.000000 | 4 | 0 | 0 |
| 2023-07 | 5 | 2.600000 | 1.428571 | 1.083333 | 1 | 0 | 0 |
| 2023-08 | 6 | -8.766667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 7 | 8.200000 | 2.455621 | 2.150000 | 2 | 0 | 0 |
| 2023-10 | 3 | -4.833333 | 0.000000 | 0.000000 | 0 | 0 | 0 |
| 2023-11 | 9 | 15.250000 | 2.930380 | 2.821429 | 1 | 0 | 0 |
| 2023-12 | 5 | -8.066667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### A_OPT2023_T4_SB1_TP10

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors.
CLOSED 56, entry dates 53, entry months 12; SKIP 0, EXCLUDED 0, exclusion share 0.000000; conditional FLAT CLOSED 0.
Net -22.483333 R; PF R / price 0.680937 / 0.584906; expectancy -0.401488 R; win rate 0.160714; average winner / loser 5.331481 / -1.531884 R.
Conditional CLOSED-only DD 38.833333 R; largest winner share 0.347343; largest positive month share 0.610343. Positive / negative / zero months 3 / 9 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 8 | -10.733333 | 0.030120 | 0.025641 | 5 | 0 | 0 |
| 2023-02 | 2 | -3.000000 | 0.000000 | 0.000000 | 4 | 0 | 0 |
| 2023-03 | 4 | -3.966667 | 0.077519 | 0.050000 | 3 | 0 | 0 |
| 2023-04 | 3 | -4.666667 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 1 | -1.500000 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-06 | 3 | -4.666667 | 0.000000 | 0.000000 | 4 | 0 | 0 |
| 2023-07 | 5 | 2.600000 | 1.428571 | 1.083333 | 1 | 0 | 0 |
| 2023-08 | 6 | -8.766667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 7 | 8.200000 | 2.455621 | 2.150000 | 2 | 0 | 0 |
| 2023-10 | 3 | -4.833333 | 0.000000 | 0.000000 | 0 | 0 | 0 |
| 2023-11 | 9 | 16.916667 | 3.141350 | 3.000000 | 1 | 0 | 0 |
| 2023-12 | 5 | -8.066667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### A_OPT2023_T4_SB2_TP2

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 80, entry dates 69, entry months 12; SKIP 0, EXCLUDED 0, exclusion share 0.000000; conditional FLAT CLOSED 0.
Net -43.766667 R; PF R / price 0.497512 / 0.509642; expectancy -0.547083 R; win rate 0.212500; average winner / loser 2.549020 / -1.451667 R.
Conditional CLOSED-only DD 43.766667 R; largest winner share 0.076923; largest positive month share 0.979866. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 8 | -5.383333 | 0.376448 | 0.325000 | 5 | 0 | 0 |
| 2023-02 | 4 | -6.133333 | 0.000000 | 0.000000 | 4 | 0 | 0 |
| 2023-03 | 8 | -1.483333 | 0.808190 | 0.900000 | 3 | 0 | 0 |
| 2023-04 | 5 | -0.966667 | 0.775194 | 0.500000 | 5 | 0 | 0 |
| 2023-05 | 3 | -0.533333 | 0.840000 | 1.400000 | 3 | 0 | 0 |
| 2023-06 | 6 | -5.100000 | 0.354430 | 0.500000 | 4 | 0 | 0 |
| 2023-07 | 8 | -5.966667 | 0.334572 | 0.315789 | 1 | 0 | 0 |
| 2023-08 | 8 | -11.566667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 8 | -0.933333 | 0.861386 | 0.928571 | 2 | 0 | 0 |
| 2023-10 | 3 | 0.100000 | 1.034483 | 0.923077 | 0 | 0 | 0 |
| 2023-11 | 12 | 4.866667 | 1.591093 | 1.628571 | 1 | 0 | 0 |
| 2023-12 | 7 | -10.666667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### A_OPT2023_T4_SB2_TP3

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors.
CLOSED 80, entry dates 69, entry months 12; SKIP 0, EXCLUDED 0, exclusion share 0.000000; conditional FLAT CLOSED 0.
Net -49.683333 R; PF R / price 0.465771 / 0.462725; expectancy -0.621042 R; win rate 0.162500; average winner / loser 3.332051 / -1.453125 R.
Conditional CLOSED-only DD 49.683333 R; largest winner share 0.115429; largest positive month share 0.443609. Positive / negative / zero months 3 / 9 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 8 | -4.633333 | 0.463320 | 0.400000 | 5 | 0 | 0 |
| 2023-02 | 4 | -6.133333 | 0.000000 | 0.000000 | 4 | 0 | 0 |
| 2023-03 | 8 | -3.816667 | 0.579044 | 0.421053 | 3 | 0 | 0 |
| 2023-04 | 5 | 0.700000 | 1.162791 | 0.750000 | 5 | 0 | 0 |
| 2023-05 | 3 | -4.733333 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-06 | 6 | -3.700000 | 0.531646 | 0.750000 | 4 | 0 | 0 |
| 2023-07 | 8 | -4.466667 | 0.501859 | 0.473684 | 1 | 0 | 0 |
| 2023-08 | 8 | -11.566667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 8 | 1.966667 | 1.292079 | 1.392857 | 2 | 0 | 0 |
| 2023-10 | 3 | -4.400000 | 0.000000 | 0.000000 | 0 | 0 | 0 |
| 2023-11 | 12 | 1.766667 | 1.178451 | 1.375000 | 1 | 0 | 0 |
| 2023-12 | 7 | -10.666667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### A_OPT2023_T4_SB2_TP4

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors.
CLOSED 80, entry dates 69, entry months 12; SKIP 0, EXCLUDED 0, exclusion share 0.000000; conditional FLAT CLOSED 0.
Net -44.250000 R; PF R / price 0.524194 / 0.503856; expectancy -0.553125 R; win rate 0.162500; average winner / loser 3.750000 / -1.453125 R.
Conditional CLOSED-only DD 44.250000 R; largest winner share 0.136752; largest positive month share 0.491582. Positive / negative / zero months 3 / 9 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 8 | -4.633333 | 0.463320 | 0.400000 | 5 | 0 | 0 |
| 2023-02 | 4 | -6.133333 | 0.000000 | 0.000000 | 4 | 0 | 0 |
| 2023-03 | 8 | -2.150000 | 0.762868 | 0.552632 | 3 | 0 | 0 |
| 2023-04 | 5 | 2.366667 | 1.550388 | 1.000000 | 5 | 0 | 0 |
| 2023-05 | 3 | -4.733333 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-06 | 6 | -6.900000 | 0.126582 | 0.178571 | 4 | 0 | 0 |
| 2023-07 | 8 | -2.966667 | 0.669145 | 0.631579 | 1 | 0 | 0 |
| 2023-08 | 8 | -11.566667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 8 | 4.866667 | 1.722772 | 1.857143 | 2 | 0 | 0 |
| 2023-10 | 3 | -4.400000 | 0.000000 | 0.000000 | 0 | 0 | 0 |
| 2023-11 | 12 | 2.666667 | 1.269360 | 1.450000 | 1 | 0 | 0 |
| 2023-12 | 7 | -10.666667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### A_OPT2023_T4_SB2_TP5

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors.
CLOSED 80, entry dates 69, entry months 12; SKIP 0, EXCLUDED 0, exclusion share 0.000000; conditional FLAT CLOSED 0.
Net -35.016667 R; PF R / price 0.623477 / 0.593830; expectancy -0.437708 R; win rate 0.162500; average winner / loser 4.460256 / -1.453125 R.
Conditional CLOSED-only DD 35.450000 R; largest winner share 0.143719; largest positive month share 0.486430. Positive / negative / zero months 3 / 9 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 8 | -4.633333 | 0.463320 | 0.400000 | 5 | 0 | 0 |
| 2023-02 | 4 | -6.133333 | 0.000000 | 0.000000 | 4 | 0 | 0 |
| 2023-03 | 8 | -0.483333 | 0.946691 | 0.684211 | 3 | 0 | 0 |
| 2023-04 | 5 | 4.033333 | 1.937984 | 1.250000 | 5 | 0 | 0 |
| 2023-05 | 3 | -4.733333 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-06 | 6 | -6.900000 | 0.126582 | 0.178571 | 4 | 0 | 0 |
| 2023-07 | 8 | -1.466667 | 0.836431 | 0.789474 | 1 | 0 | 0 |
| 2023-08 | 8 | -11.566667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 8 | 7.766667 | 2.153465 | 2.321429 | 2 | 0 | 0 |
| 2023-10 | 3 | -4.400000 | 0.000000 | 0.000000 | 0 | 0 | 0 |
| 2023-11 | 12 | 4.166667 | 1.420875 | 1.600000 | 1 | 0 | 0 |
| 2023-12 | 7 | -10.666667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### A_OPT2023_T4_SB2_TP6

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors.
CLOSED 80, entry dates 69, entry months 12; SKIP 0, EXCLUDED 0, exclusion share 0.000000; conditional FLAT CLOSED 0.
Net -37.316667 R; PF R / price 0.598746 / 0.557841; expectancy -0.466458 R; win rate 0.162500; average winner / loser 4.283333 / -1.453125 R.
Conditional CLOSED-only DD 39.250000 R; largest winner share 0.179587; largest positive month share 0.483642. Positive / negative / zero months 5 / 7 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 8 | -4.633333 | 0.463320 | 0.400000 | 5 | 0 | 0 |
| 2023-02 | 4 | -6.133333 | 0.000000 | 0.000000 | 4 | 0 | 0 |
| 2023-03 | 8 | 1.183333 | 1.130515 | 0.815789 | 3 | 0 | 0 |
| 2023-04 | 5 | 1.366667 | 1.317829 | 0.850000 | 5 | 0 | 0 |
| 2023-05 | 3 | -4.733333 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-06 | 6 | -6.900000 | 0.126582 | 0.178571 | 4 | 0 | 0 |
| 2023-07 | 8 | 0.033333 | 1.003717 | 0.947368 | 1 | 0 | 0 |
| 2023-08 | 8 | -11.566667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 8 | 3.466667 | 1.514851 | 1.500000 | 2 | 0 | 0 |
| 2023-10 | 3 | -4.400000 | 0.000000 | 0.000000 | 0 | 0 | 0 |
| 2023-11 | 12 | 5.666667 | 1.572391 | 1.750000 | 1 | 0 | 0 |
| 2023-12 | 7 | -10.666667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### A_OPT2023_T4_SB2_TP7

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors.
CLOSED 80, entry dates 69, entry months 12; SKIP 0, EXCLUDED 0, exclusion share 0.000000; conditional FLAT CLOSED 0.
Net -36.400000 R; PF R / price 0.608602 / 0.562982; expectancy -0.455000 R; win rate 0.162500; average winner / loser 4.353846 / -1.453125 R.
Conditional CLOSED-only DD 39.833333 R; largest winner share 0.206125; largest positive month share 0.474614. Positive / negative / zero months 4 / 8 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 8 | -4.633333 | 0.463320 | 0.400000 | 5 | 0 | 0 |
| 2023-02 | 4 | -6.133333 | 0.000000 | 0.000000 | 4 | 0 | 0 |
| 2023-03 | 8 | 2.850000 | 1.314338 | 0.947368 | 3 | 0 | 0 |
| 2023-04 | 5 | 1.366667 | 1.317829 | 0.850000 | 5 | 0 | 0 |
| 2023-05 | 3 | -4.733333 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-06 | 6 | -6.900000 | 0.126582 | 0.178571 | 4 | 0 | 0 |
| 2023-07 | 8 | -2.466667 | 0.724907 | 0.684211 | 1 | 0 | 0 |
| 2023-08 | 8 | -11.566667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 8 | 3.716667 | 1.551980 | 1.535714 | 2 | 0 | 0 |
| 2023-10 | 3 | -4.400000 | 0.000000 | 0.000000 | 0 | 0 | 0 |
| 2023-11 | 12 | 7.166667 | 1.723906 | 1.900000 | 1 | 0 | 0 |
| 2023-12 | 7 | -10.666667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### A_OPT2023_T4_SB2_TP8

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors.
CLOSED 80, entry dates 69, entry months 12; SKIP 0, EXCLUDED 0, exclusion share 0.000000; conditional FLAT CLOSED 0.
Net -33.233333 R; PF R / price 0.642652 / 0.591260; expectancy -0.415417 R; win rate 0.162500; average winner / loser 4.597436 / -1.453125 R.
Conditional CLOSED-only DD 38.250000 R; largest winner share 0.223090; largest positive month share 0.474453. Positive / negative / zero months 4 / 8 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 8 | -4.633333 | 0.463320 | 0.400000 | 5 | 0 | 0 |
| 2023-02 | 4 | -6.133333 | 0.000000 | 0.000000 | 4 | 0 | 0 |
| 2023-03 | 8 | 4.516667 | 1.498162 | 1.078947 | 3 | 0 | 0 |
| 2023-04 | 5 | 1.366667 | 1.317829 | 0.850000 | 5 | 0 | 0 |
| 2023-05 | 3 | -4.733333 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-06 | 6 | -6.900000 | 0.126582 | 0.178571 | 4 | 0 | 0 |
| 2023-07 | 8 | -2.466667 | 0.724907 | 0.684211 | 1 | 0 | 0 |
| 2023-08 | 8 | -11.566667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 8 | 3.716667 | 1.551980 | 1.535714 | 2 | 0 | 0 |
| 2023-10 | 3 | -4.400000 | 0.000000 | 0.000000 | 0 | 0 | 0 |
| 2023-11 | 12 | 8.666667 | 1.875421 | 2.050000 | 1 | 0 | 0 |
| 2023-12 | 7 | -10.666667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### A_OPT2023_T4_SB2_TP9

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors.
CLOSED 80, entry dates 69, entry months 12; SKIP 0, EXCLUDED 0, exclusion share 0.000000; conditional FLAT CLOSED 0.
Net -30.066667 R; PF R / price 0.676703 / 0.619537; expectancy -0.375833 R; win rate 0.162500; average winner / loser 4.841026 / -1.453125 R.
Conditional CLOSED-only DD 38.250000 R; largest winner share 0.238347; largest positive month share 0.474339. Positive / negative / zero months 4 / 8 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 8 | -4.633333 | 0.463320 | 0.400000 | 5 | 0 | 0 |
| 2023-02 | 4 | -6.133333 | 0.000000 | 0.000000 | 4 | 0 | 0 |
| 2023-03 | 8 | 6.183333 | 1.681985 | 1.210526 | 3 | 0 | 0 |
| 2023-04 | 5 | 1.366667 | 1.317829 | 0.850000 | 5 | 0 | 0 |
| 2023-05 | 3 | -4.733333 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-06 | 6 | -6.900000 | 0.126582 | 0.178571 | 4 | 0 | 0 |
| 2023-07 | 8 | -2.466667 | 0.724907 | 0.684211 | 1 | 0 | 0 |
| 2023-08 | 8 | -11.566667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 8 | 3.716667 | 1.551980 | 1.535714 | 2 | 0 | 0 |
| 2023-10 | 3 | -4.400000 | 0.000000 | 0.000000 | 0 | 0 | 0 |
| 2023-11 | 12 | 10.166667 | 2.026936 | 2.200000 | 1 | 0 | 0 |
| 2023-12 | 7 | -10.666667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### A_OPT2023_T4_SB2_TP10

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|neighbors.
CLOSED 80, entry dates 69, entry months 12; SKIP 0, EXCLUDED 0, exclusion share 0.000000; conditional FLAT CLOSED 0.
Net -26.900000 R; PF R / price 0.710753 / 0.647815; expectancy -0.336250 R; win rate 0.162500; average winner / loser 5.084615 / -1.453125 R.
Conditional CLOSED-only DD 38.250000 R; largest winner share 0.252143; largest positive month share 0.474255. Positive / negative / zero months 4 / 8 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 8 | -4.633333 | 0.463320 | 0.400000 | 5 | 0 | 0 |
| 2023-02 | 4 | -6.133333 | 0.000000 | 0.000000 | 4 | 0 | 0 |
| 2023-03 | 8 | 7.850000 | 1.865809 | 1.342105 | 3 | 0 | 0 |
| 2023-04 | 5 | 1.366667 | 1.317829 | 0.850000 | 5 | 0 | 0 |
| 2023-05 | 3 | -4.733333 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-06 | 6 | -6.900000 | 0.126582 | 0.178571 | 4 | 0 | 0 |
| 2023-07 | 8 | -2.466667 | 0.724907 | 0.684211 | 1 | 0 | 0 |
| 2023-08 | 8 | -11.566667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 8 | 3.716667 | 1.551980 | 1.535714 | 2 | 0 | 0 |
| 2023-10 | 3 | -4.400000 | 0.000000 | 0.000000 | 0 | 0 | 0 |
| 2023-11 | 12 | 11.666667 | 2.178451 | 2.350000 | 1 | 0 | 0 |
| 2023-12 | 7 | -10.666667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### A_OPT2023_T5_SB1_TP2

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|trade_concentration|month_concentration|neighbors.
CLOSED 11, entry dates 10, entry months 7; SKIP 0, EXCLUDED 0, exclusion share 0.000000; conditional FLAT CLOSED 0.
Net -13.266667 R; PF R / price 0.174274 / 0.259259; expectancy -1.206061 R; win rate 0.090909; average winner / loser 2.800000 / -1.606667 R.
Conditional CLOSED-only DD 13.266667 R; largest winner share 1.000000; largest positive month share 1.000000. Positive / negative / zero months 1 / 6 / 5; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 3 | -5.000000 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-02 | 1 | -1.400000 | 0.000000 | 0.000000 | 4 | 0 | 0 |
| 2023-03 | 1 | -1.500000 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-04 | 1 | 2.800000 | NOT_AVAILABLE | NOT_AVAILABLE | 5 | 0 | 0 |
| 2023-05 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 3 | 0 | 0 |
| 2023-06 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 4 | 0 | 0 |
| 2023-07 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 1 | 0 | 0 |
| 2023-08 | 2 | -3.166667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 1 | -1.666667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |
| 2023-11 | 2 | -3.333333 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-12 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### A_OPT2023_T5_SB1_TP3

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|trade_concentration|month_concentration|neighbors.
CLOSED 11, entry dates 10, entry months 7; SKIP 0, EXCLUDED 0, exclusion share 0.000000; conditional FLAT CLOSED 0.
Net -11.866667 R; PF R / price 0.261411 / 0.388889; expectancy -1.078788 R; win rate 0.090909; average winner / loser 4.200000 / -1.606667 R.
Conditional CLOSED-only DD 11.866667 R; largest winner share 1.000000; largest positive month share 1.000000. Positive / negative / zero months 1 / 6 / 5; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 3 | -5.000000 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-02 | 1 | -1.400000 | 0.000000 | 0.000000 | 4 | 0 | 0 |
| 2023-03 | 1 | -1.500000 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-04 | 1 | 4.200000 | NOT_AVAILABLE | NOT_AVAILABLE | 5 | 0 | 0 |
| 2023-05 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 3 | 0 | 0 |
| 2023-06 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 4 | 0 | 0 |
| 2023-07 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 1 | 0 | 0 |
| 2023-08 | 2 | -3.166667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 1 | -1.666667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |
| 2023-11 | 2 | -3.333333 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-12 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### A_OPT2023_T5_SB1_TP4

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|trade_concentration|month_concentration|neighbors.
CLOSED 11, entry dates 10, entry months 7; SKIP 0, EXCLUDED 0, exclusion share 0.000000; conditional FLAT CLOSED 0.
Net -12.466667 R; PF R / price 0.224066 / 0.333333; expectancy -1.133333 R; win rate 0.090909; average winner / loser 3.600000 / -1.606667 R.
Conditional CLOSED-only DD 12.466667 R; largest winner share 1.000000; largest positive month share 1.000000. Positive / negative / zero months 1 / 6 / 5; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 3 | -5.000000 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-02 | 1 | -1.400000 | 0.000000 | 0.000000 | 4 | 0 | 0 |
| 2023-03 | 1 | -1.500000 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-04 | 1 | 3.600000 | NOT_AVAILABLE | NOT_AVAILABLE | 5 | 0 | 0 |
| 2023-05 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 3 | 0 | 0 |
| 2023-06 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 4 | 0 | 0 |
| 2023-07 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 1 | 0 | 0 |
| 2023-08 | 2 | -3.166667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 1 | -1.666667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |
| 2023-11 | 2 | -3.333333 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-12 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### A_OPT2023_T5_SB1_TP5

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|trade_concentration|month_concentration|neighbors.
CLOSED 11, entry dates 10, entry months 7; SKIP 0, EXCLUDED 0, exclusion share 0.000000; conditional FLAT CLOSED 0.
Net -12.466667 R; PF R / price 0.224066 / 0.333333; expectancy -1.133333 R; win rate 0.090909; average winner / loser 3.600000 / -1.606667 R.
Conditional CLOSED-only DD 12.466667 R; largest winner share 1.000000; largest positive month share 1.000000. Positive / negative / zero months 1 / 6 / 5; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 3 | -5.000000 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-02 | 1 | -1.400000 | 0.000000 | 0.000000 | 4 | 0 | 0 |
| 2023-03 | 1 | -1.500000 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-04 | 1 | 3.600000 | NOT_AVAILABLE | NOT_AVAILABLE | 5 | 0 | 0 |
| 2023-05 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 3 | 0 | 0 |
| 2023-06 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 4 | 0 | 0 |
| 2023-07 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 1 | 0 | 0 |
| 2023-08 | 2 | -3.166667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 1 | -1.666667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |
| 2023-11 | 2 | -3.333333 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-12 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### A_OPT2023_T5_SB1_TP6

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|trade_concentration|month_concentration|neighbors.
CLOSED 11, entry dates 10, entry months 7; SKIP 0, EXCLUDED 0, exclusion share 0.000000; conditional FLAT CLOSED 0.
Net -12.466667 R; PF R / price 0.224066 / 0.333333; expectancy -1.133333 R; win rate 0.090909; average winner / loser 3.600000 / -1.606667 R.
Conditional CLOSED-only DD 12.466667 R; largest winner share 1.000000; largest positive month share 1.000000. Positive / negative / zero months 1 / 6 / 5; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 3 | -5.000000 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-02 | 1 | -1.400000 | 0.000000 | 0.000000 | 4 | 0 | 0 |
| 2023-03 | 1 | -1.500000 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-04 | 1 | 3.600000 | NOT_AVAILABLE | NOT_AVAILABLE | 5 | 0 | 0 |
| 2023-05 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 3 | 0 | 0 |
| 2023-06 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 4 | 0 | 0 |
| 2023-07 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 1 | 0 | 0 |
| 2023-08 | 2 | -3.166667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 1 | -1.666667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |
| 2023-11 | 2 | -3.333333 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-12 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### A_OPT2023_T5_SB1_TP7

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|trade_concentration|month_concentration|neighbors.
CLOSED 11, entry dates 10, entry months 7; SKIP 0, EXCLUDED 0, exclusion share 0.000000; conditional FLAT CLOSED 0.
Net -12.466667 R; PF R / price 0.224066 / 0.333333; expectancy -1.133333 R; win rate 0.090909; average winner / loser 3.600000 / -1.606667 R.
Conditional CLOSED-only DD 12.466667 R; largest winner share 1.000000; largest positive month share 1.000000. Positive / negative / zero months 1 / 6 / 5; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 3 | -5.000000 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-02 | 1 | -1.400000 | 0.000000 | 0.000000 | 4 | 0 | 0 |
| 2023-03 | 1 | -1.500000 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-04 | 1 | 3.600000 | NOT_AVAILABLE | NOT_AVAILABLE | 5 | 0 | 0 |
| 2023-05 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 3 | 0 | 0 |
| 2023-06 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 4 | 0 | 0 |
| 2023-07 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 1 | 0 | 0 |
| 2023-08 | 2 | -3.166667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 1 | -1.666667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |
| 2023-11 | 2 | -3.333333 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-12 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### A_OPT2023_T5_SB1_TP8

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|trade_concentration|month_concentration|neighbors.
CLOSED 11, entry dates 10, entry months 7; SKIP 0, EXCLUDED 0, exclusion share 0.000000; conditional FLAT CLOSED 0.
Net -12.466667 R; PF R / price 0.224066 / 0.333333; expectancy -1.133333 R; win rate 0.090909; average winner / loser 3.600000 / -1.606667 R.
Conditional CLOSED-only DD 12.466667 R; largest winner share 1.000000; largest positive month share 1.000000. Positive / negative / zero months 1 / 6 / 5; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 3 | -5.000000 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-02 | 1 | -1.400000 | 0.000000 | 0.000000 | 4 | 0 | 0 |
| 2023-03 | 1 | -1.500000 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-04 | 1 | 3.600000 | NOT_AVAILABLE | NOT_AVAILABLE | 5 | 0 | 0 |
| 2023-05 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 3 | 0 | 0 |
| 2023-06 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 4 | 0 | 0 |
| 2023-07 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 1 | 0 | 0 |
| 2023-08 | 2 | -3.166667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 1 | -1.666667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |
| 2023-11 | 2 | -3.333333 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-12 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### A_OPT2023_T5_SB1_TP9

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|trade_concentration|month_concentration|neighbors.
CLOSED 11, entry dates 10, entry months 7; SKIP 0, EXCLUDED 0, exclusion share 0.000000; conditional FLAT CLOSED 0.
Net -12.466667 R; PF R / price 0.224066 / 0.333333; expectancy -1.133333 R; win rate 0.090909; average winner / loser 3.600000 / -1.606667 R.
Conditional CLOSED-only DD 12.466667 R; largest winner share 1.000000; largest positive month share 1.000000. Positive / negative / zero months 1 / 6 / 5; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 3 | -5.000000 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-02 | 1 | -1.400000 | 0.000000 | 0.000000 | 4 | 0 | 0 |
| 2023-03 | 1 | -1.500000 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-04 | 1 | 3.600000 | NOT_AVAILABLE | NOT_AVAILABLE | 5 | 0 | 0 |
| 2023-05 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 3 | 0 | 0 |
| 2023-06 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 4 | 0 | 0 |
| 2023-07 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 1 | 0 | 0 |
| 2023-08 | 2 | -3.166667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 1 | -1.666667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |
| 2023-11 | 2 | -3.333333 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-12 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### A_OPT2023_T5_SB1_TP10

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|trade_concentration|month_concentration|neighbors.
CLOSED 11, entry dates 10, entry months 7; SKIP 0, EXCLUDED 0, exclusion share 0.000000; conditional FLAT CLOSED 0.
Net -12.466667 R; PF R / price 0.224066 / 0.333333; expectancy -1.133333 R; win rate 0.090909; average winner / loser 3.600000 / -1.606667 R.
Conditional CLOSED-only DD 12.466667 R; largest winner share 1.000000; largest positive month share 1.000000. Positive / negative / zero months 1 / 6 / 5; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 3 | -5.000000 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-02 | 1 | -1.400000 | 0.000000 | 0.000000 | 4 | 0 | 0 |
| 2023-03 | 1 | -1.500000 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-04 | 1 | 3.600000 | NOT_AVAILABLE | NOT_AVAILABLE | 5 | 0 | 0 |
| 2023-05 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 3 | 0 | 0 |
| 2023-06 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 4 | 0 | 0 |
| 2023-07 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 1 | 0 | 0 |
| 2023-08 | 2 | -3.166667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 1 | -1.666667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |
| 2023-11 | 2 | -3.333333 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-12 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### A_OPT2023_T5_SB2_TP2

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|trade_concentration|month_concentration|neighbors.
CLOSED 16, entry dates 15, entry months 9; SKIP 0, EXCLUDED 0, exclusion share 0.000000; conditional FLAT CLOSED 0.
Net -17.966667 R; PF R / price 0.156495 / 0.214286; expectancy -1.122917 R; win rate 0.125000; average winner / loser 1.666667 / -1.521429 R.
Conditional CLOSED-only DD 17.966667 R; largest winner share 0.800000; largest positive month share 1.000000. Positive / negative / zero months 1 / 8 / 3; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 4 | -3.833333 | 0.148148 | 0.111111 | 5 | 0 | 0 |
| 2023-02 | 1 | -1.333333 | 0.000000 | 0.000000 | 4 | 0 | 0 |
| 2023-03 | 2 | -3.066667 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-04 | 1 | 2.666667 | NOT_AVAILABLE | NOT_AVAILABLE | 5 | 0 | 0 |
| 2023-05 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 3 | 0 | 0 |
| 2023-06 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 4 | 0 | 0 |
| 2023-07 | 1 | -1.666667 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-08 | 3 | -4.566667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 1 | -1.500000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |
| 2023-11 | 2 | -3.000000 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-12 | 1 | -1.666667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### A_OPT2023_T5_SB2_TP3

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|trade_concentration|month_concentration|neighbors.
CLOSED 16, entry dates 15, entry months 9; SKIP 0, EXCLUDED 0, exclusion share 0.000000; conditional FLAT CLOSED 0.
Net -16.633333 R; PF R / price 0.219092 / 0.309524; expectancy -1.039583 R; win rate 0.125000; average winner / loser 2.333333 / -1.521429 R.
Conditional CLOSED-only DD 16.633333 R; largest winner share 0.857143; largest positive month share 1.000000. Positive / negative / zero months 1 / 8 / 3; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 4 | -3.833333 | 0.148148 | 0.111111 | 5 | 0 | 0 |
| 2023-02 | 1 | -1.333333 | 0.000000 | 0.000000 | 4 | 0 | 0 |
| 2023-03 | 2 | -3.066667 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-04 | 1 | 4.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 5 | 0 | 0 |
| 2023-05 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 3 | 0 | 0 |
| 2023-06 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 4 | 0 | 0 |
| 2023-07 | 1 | -1.666667 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-08 | 3 | -4.566667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 1 | -1.500000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |
| 2023-11 | 2 | -3.000000 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-12 | 1 | -1.666667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### A_OPT2023_T5_SB2_TP4

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|trade_concentration|month_concentration|neighbors.
CLOSED 16, entry dates 15, entry months 9; SKIP 0, EXCLUDED 0, exclusion share 0.000000; conditional FLAT CLOSED 0.
Net -17.633333 R; PF R / price 0.172144 / 0.238095; expectancy -1.102083 R; win rate 0.125000; average winner / loser 1.833333 / -1.521429 R.
Conditional CLOSED-only DD 17.633333 R; largest winner share 0.818182; largest positive month share 1.000000. Positive / negative / zero months 1 / 8 / 3; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 4 | -3.833333 | 0.148148 | 0.111111 | 5 | 0 | 0 |
| 2023-02 | 1 | -1.333333 | 0.000000 | 0.000000 | 4 | 0 | 0 |
| 2023-03 | 2 | -3.066667 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-04 | 1 | 3.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 5 | 0 | 0 |
| 2023-05 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 3 | 0 | 0 |
| 2023-06 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 4 | 0 | 0 |
| 2023-07 | 1 | -1.666667 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-08 | 3 | -4.566667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 1 | -1.500000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |
| 2023-11 | 2 | -3.000000 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-12 | 1 | -1.666667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### A_OPT2023_T5_SB2_TP5

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|trade_concentration|month_concentration|neighbors.
CLOSED 16, entry dates 15, entry months 9; SKIP 0, EXCLUDED 0, exclusion share 0.000000; conditional FLAT CLOSED 0.
Net -17.633333 R; PF R / price 0.172144 / 0.238095; expectancy -1.102083 R; win rate 0.125000; average winner / loser 1.833333 / -1.521429 R.
Conditional CLOSED-only DD 17.633333 R; largest winner share 0.818182; largest positive month share 1.000000. Positive / negative / zero months 1 / 8 / 3; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 4 | -3.833333 | 0.148148 | 0.111111 | 5 | 0 | 0 |
| 2023-02 | 1 | -1.333333 | 0.000000 | 0.000000 | 4 | 0 | 0 |
| 2023-03 | 2 | -3.066667 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-04 | 1 | 3.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 5 | 0 | 0 |
| 2023-05 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 3 | 0 | 0 |
| 2023-06 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 4 | 0 | 0 |
| 2023-07 | 1 | -1.666667 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-08 | 3 | -4.566667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 1 | -1.500000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |
| 2023-11 | 2 | -3.000000 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-12 | 1 | -1.666667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### A_OPT2023_T5_SB2_TP6

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|trade_concentration|month_concentration|neighbors.
CLOSED 16, entry dates 15, entry months 9; SKIP 0, EXCLUDED 0, exclusion share 0.000000; conditional FLAT CLOSED 0.
Net -17.633333 R; PF R / price 0.172144 / 0.238095; expectancy -1.102083 R; win rate 0.125000; average winner / loser 1.833333 / -1.521429 R.
Conditional CLOSED-only DD 17.633333 R; largest winner share 0.818182; largest positive month share 1.000000. Positive / negative / zero months 1 / 8 / 3; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 4 | -3.833333 | 0.148148 | 0.111111 | 5 | 0 | 0 |
| 2023-02 | 1 | -1.333333 | 0.000000 | 0.000000 | 4 | 0 | 0 |
| 2023-03 | 2 | -3.066667 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-04 | 1 | 3.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 5 | 0 | 0 |
| 2023-05 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 3 | 0 | 0 |
| 2023-06 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 4 | 0 | 0 |
| 2023-07 | 1 | -1.666667 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-08 | 3 | -4.566667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 1 | -1.500000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |
| 2023-11 | 2 | -3.000000 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-12 | 1 | -1.666667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### A_OPT2023_T5_SB2_TP7

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|trade_concentration|month_concentration|neighbors.
CLOSED 16, entry dates 15, entry months 9; SKIP 0, EXCLUDED 0, exclusion share 0.000000; conditional FLAT CLOSED 0.
Net -17.633333 R; PF R / price 0.172144 / 0.238095; expectancy -1.102083 R; win rate 0.125000; average winner / loser 1.833333 / -1.521429 R.
Conditional CLOSED-only DD 17.633333 R; largest winner share 0.818182; largest positive month share 1.000000. Positive / negative / zero months 1 / 8 / 3; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 4 | -3.833333 | 0.148148 | 0.111111 | 5 | 0 | 0 |
| 2023-02 | 1 | -1.333333 | 0.000000 | 0.000000 | 4 | 0 | 0 |
| 2023-03 | 2 | -3.066667 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-04 | 1 | 3.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 5 | 0 | 0 |
| 2023-05 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 3 | 0 | 0 |
| 2023-06 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 4 | 0 | 0 |
| 2023-07 | 1 | -1.666667 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-08 | 3 | -4.566667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 1 | -1.500000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |
| 2023-11 | 2 | -3.000000 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-12 | 1 | -1.666667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### A_OPT2023_T5_SB2_TP8

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|trade_concentration|month_concentration|neighbors.
CLOSED 16, entry dates 15, entry months 9; SKIP 0, EXCLUDED 0, exclusion share 0.000000; conditional FLAT CLOSED 0.
Net -17.633333 R; PF R / price 0.172144 / 0.238095; expectancy -1.102083 R; win rate 0.125000; average winner / loser 1.833333 / -1.521429 R.
Conditional CLOSED-only DD 17.633333 R; largest winner share 0.818182; largest positive month share 1.000000. Positive / negative / zero months 1 / 8 / 3; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 4 | -3.833333 | 0.148148 | 0.111111 | 5 | 0 | 0 |
| 2023-02 | 1 | -1.333333 | 0.000000 | 0.000000 | 4 | 0 | 0 |
| 2023-03 | 2 | -3.066667 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-04 | 1 | 3.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 5 | 0 | 0 |
| 2023-05 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 3 | 0 | 0 |
| 2023-06 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 4 | 0 | 0 |
| 2023-07 | 1 | -1.666667 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-08 | 3 | -4.566667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 1 | -1.500000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |
| 2023-11 | 2 | -3.000000 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-12 | 1 | -1.666667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### A_OPT2023_T5_SB2_TP9

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|trade_concentration|month_concentration|neighbors.
CLOSED 16, entry dates 15, entry months 9; SKIP 0, EXCLUDED 0, exclusion share 0.000000; conditional FLAT CLOSED 0.
Net -17.633333 R; PF R / price 0.172144 / 0.238095; expectancy -1.102083 R; win rate 0.125000; average winner / loser 1.833333 / -1.521429 R.
Conditional CLOSED-only DD 17.633333 R; largest winner share 0.818182; largest positive month share 1.000000. Positive / negative / zero months 1 / 8 / 3; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 4 | -3.833333 | 0.148148 | 0.111111 | 5 | 0 | 0 |
| 2023-02 | 1 | -1.333333 | 0.000000 | 0.000000 | 4 | 0 | 0 |
| 2023-03 | 2 | -3.066667 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-04 | 1 | 3.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 5 | 0 | 0 |
| 2023-05 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 3 | 0 | 0 |
| 2023-06 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 4 | 0 | 0 |
| 2023-07 | 1 | -1.666667 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-08 | 3 | -4.566667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 1 | -1.500000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |
| 2023-11 | 2 | -3.000000 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-12 | 1 | -1.666667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### A_OPT2023_T5_SB2_TP10

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|trade_concentration|month_concentration|neighbors.
CLOSED 16, entry dates 15, entry months 9; SKIP 0, EXCLUDED 0, exclusion share 0.000000; conditional FLAT CLOSED 0.
Net -17.633333 R; PF R / price 0.172144 / 0.238095; expectancy -1.102083 R; win rate 0.125000; average winner / loser 1.833333 / -1.521429 R.
Conditional CLOSED-only DD 17.633333 R; largest winner share 0.818182; largest positive month share 1.000000. Positive / negative / zero months 1 / 8 / 3; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 4 | -3.833333 | 0.148148 | 0.111111 | 5 | 0 | 0 |
| 2023-02 | 1 | -1.333333 | 0.000000 | 0.000000 | 4 | 0 | 0 |
| 2023-03 | 2 | -3.066667 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-04 | 1 | 3.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 5 | 0 | 0 |
| 2023-05 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 3 | 0 | 0 |
| 2023-06 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 4 | 0 | 0 |
| 2023-07 | 1 | -1.666667 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-08 | 3 | -4.566667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 1 | -1.500000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |
| 2023-11 | 2 | -3.000000 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-12 | 1 | -1.666667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

## CNYRUBF

NO QUALIFYING OPTIMIZATION CANDIDATE

### A_OPT2023_T2_SB1_TP2

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 595, entry dates 186, entry months 12; SKIP 72, EXCLUDED 118, exclusion share 0.165498; conditional FLAT CLOSED 594.
Net -348.250000 R; PF R / price 0.454638 / 0.352265; expectancy -0.585294 R; win rate 0.218487; average winner / loser 2.233205 / -1.422197 R.
Conditional CLOSED-only DD 348.250000 R; largest winner share 0.011482; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 12 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 42 | -37.950000 | 0.187366 | 0.188679 | 18 | 9 | 12 |
| 2023-02 | 32 | -26.750000 | 0.205446 | 0.207547 | 18 | 16 | 13 |
| 2023-03 | 16 | -16.416667 | 0.066351 | 0.070175 | 22 | 11 | 13 |
| 2023-04 | 32 | -12.833333 | 0.554913 | 0.582418 | 18 | 12 | 10 |
| 2023-05 | 26 | -13.916667 | 0.456026 | 0.400000 | 21 | 3 | 20 |
| 2023-06 | 22 | -21.250000 | 0.098940 | 0.095890 | 20 | 10 | 16 |
| 2023-07 | 33 | -15.666667 | 0.494624 | 0.561905 | 19 | 5 | 17 |
| 2023-08 | 86 | -51.233333 | 0.422398 | 0.402685 | 14 | 3 | 5 |
| 2023-09 | 59 | -42.350000 | 0.300193 | 0.258469 | 14 | 2 | 9 |
| 2023-10 | 87 | -19.850000 | 0.784004 | 0.805158 | 2 | 0 | 1 |
| 2023-11 | 87 | -41.600000 | 0.582888 | 0.569061 | 6 | 1 | 2 |
| 2023-12 | 73 | -48.433333 | 0.466397 | 0.505952 | 0 | 0 | 0 |

### A_OPT2023_T2_SB1_TP3

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 583, entry dates 186, entry months 12; SKIP 72, EXCLUDED 117, exclusion share 0.167143; conditional FLAT CLOSED 582.
Net -344.800000 R; PF R / price 0.461222 / 0.325664; expectancy -0.591424 R; win rate 0.197256; average winner / loser 2.566667 / -1.422148 R.
Conditional CLOSED-only DD 344.800000 R; largest winner share 0.016940; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 12 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 42 | -36.783333 | 0.212348 | 0.220126 | 18 | 9 | 12 |
| 2023-02 | 32 | -26.750000 | 0.205446 | 0.207547 | 18 | 16 | 13 |
| 2023-03 | 16 | -16.416667 | 0.066351 | 0.070175 | 22 | 11 | 13 |
| 2023-04 | 32 | -17.833333 | 0.415301 | 0.447917 | 18 | 12 | 10 |
| 2023-05 | 28 | -18.583333 | 0.309598 | 0.276596 | 21 | 3 | 19 |
| 2023-06 | 22 | -21.250000 | 0.098940 | 0.095890 | 20 | 10 | 16 |
| 2023-07 | 33 | -19.050000 | 0.385484 | 0.447619 | 19 | 5 | 17 |
| 2023-08 | 82 | -51.566667 | 0.385135 | 0.375887 | 14 | 3 | 5 |
| 2023-09 | 58 | -38.850000 | 0.347242 | 0.257673 | 14 | 2 | 9 |
| 2023-10 | 81 | -17.083333 | 0.812888 | 0.823699 | 2 | 0 | 1 |
| 2023-11 | 85 | -38.233333 | 0.630000 | 0.648649 | 6 | 1 | 2 |
| 2023-12 | 72 | -42.400000 | 0.539130 | 0.558140 | 0 | 0 | 0 |

### A_OPT2023_T2_SB1_TP4

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 576, entry dates 186, entry months 12; SKIP 72, EXCLUDED 117, exclusion share 0.168831; conditional FLAT CLOSED 575.
Net -367.500000 R; PF R / price 0.432199 / 0.320620; expectancy -0.638021 R; win rate 0.178819; average winner / loser 2.715858 / -1.422491 R.
Conditional CLOSED-only DD 367.500000 R; largest winner share 0.025024; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 12 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 42 | -39.033333 | 0.164168 | 0.163522 | 18 | 9 | 12 |
| 2023-02 | 32 | -26.750000 | 0.205446 | 0.207547 | 18 | 16 | 13 |
| 2023-03 | 16 | -16.416667 | 0.066351 | 0.070175 | 22 | 11 | 13 |
| 2023-04 | 32 | -17.833333 | 0.415301 | 0.447917 | 18 | 12 | 10 |
| 2023-05 | 28 | -18.583333 | 0.309598 | 0.276596 | 21 | 3 | 19 |
| 2023-06 | 22 | -21.250000 | 0.098940 | 0.095890 | 20 | 10 | 16 |
| 2023-07 | 33 | -19.050000 | 0.385484 | 0.447619 | 19 | 5 | 17 |
| 2023-08 | 81 | -46.900000 | 0.430595 | 0.423913 | 14 | 3 | 5 |
| 2023-09 | 58 | -35.683333 | 0.400448 | 0.264706 | 14 | 2 | 9 |
| 2023-10 | 80 | -19.916667 | 0.792246 | 0.788462 | 2 | 0 | 1 |
| 2023-11 | 81 | -35.516667 | 0.649391 | 0.627717 | 6 | 1 | 2 |
| 2023-12 | 71 | -70.566667 | 0.281642 | 0.269755 | 0 | 0 | 0 |

### A_OPT2023_T2_SB1_TP5

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 574, entry dates 186, entry months 12; SKIP 72, EXCLUDED 117, exclusion share 0.169320; conditional FLAT CLOSED 573.
Net -380.500000 R; PF R / price 0.413623 / 0.316844; expectancy -0.662892 R; win rate 0.172474; average winner / loser 2.711111 / -1.419912 R.
Conditional CLOSED-only DD 380.500000 R; largest winner share 0.031048; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 12 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 42 | -39.033333 | 0.164168 | 0.163522 | 18 | 9 | 12 |
| 2023-02 | 32 | -26.750000 | 0.205446 | 0.207547 | 18 | 16 | 13 |
| 2023-03 | 16 | -16.416667 | 0.066351 | 0.070175 | 22 | 11 | 13 |
| 2023-04 | 32 | -17.833333 | 0.415301 | 0.447917 | 18 | 12 | 10 |
| 2023-05 | 28 | -18.583333 | 0.309598 | 0.276596 | 21 | 3 | 19 |
| 2023-06 | 22 | -21.250000 | 0.098940 | 0.095890 | 20 | 10 | 16 |
| 2023-07 | 33 | -19.050000 | 0.385484 | 0.447619 | 19 | 5 | 17 |
| 2023-08 | 81 | -46.483333 | 0.435654 | 0.423913 | 14 | 3 | 5 |
| 2023-09 | 58 | -32.516667 | 0.453654 | 0.271739 | 14 | 2 | 9 |
| 2023-10 | 78 | -13.416667 | 0.857573 | 0.857939 | 2 | 0 | 1 |
| 2023-11 | 81 | -55.016667 | 0.474196 | 0.448819 | 6 | 1 | 2 |
| 2023-12 | 71 | -74.150000 | 0.245165 | 0.226158 | 0 | 0 | 0 |

### A_OPT2023_T2_SB1_TP6

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 573, entry dates 186, entry months 12; SKIP 72, EXCLUDED 117, exclusion share 0.169565; conditional FLAT CLOSED 572.
Net -381.350000 R; PF R / price 0.413819 / 0.320768; expectancy -0.665532 R; win rate 0.169284; average winner / loser 2.775430 / -1.420451 R.
Conditional CLOSED-only DD 381.350000 R; largest winner share 0.037145; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 12 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 42 | -39.033333 | 0.164168 | 0.163522 | 18 | 9 | 12 |
| 2023-02 | 32 | -26.750000 | 0.205446 | 0.207547 | 18 | 16 | 13 |
| 2023-03 | 16 | -16.416667 | 0.066351 | 0.070175 | 22 | 11 | 13 |
| 2023-04 | 32 | -17.833333 | 0.415301 | 0.447917 | 18 | 12 | 10 |
| 2023-05 | 28 | -18.583333 | 0.309598 | 0.276596 | 21 | 3 | 19 |
| 2023-06 | 22 | -21.250000 | 0.098940 | 0.095890 | 20 | 10 | 16 |
| 2023-07 | 33 | -19.050000 | 0.385484 | 0.447619 | 19 | 5 | 17 |
| 2023-08 | 81 | -44.816667 | 0.455888 | 0.442029 | 14 | 3 | 5 |
| 2023-09 | 58 | -29.350000 | 0.506861 | 0.278772 | 14 | 2 | 9 |
| 2023-10 | 77 | -15.600000 | 0.834395 | 0.838440 | 2 | 0 | 1 |
| 2023-11 | 81 | -48.516667 | 0.536317 | 0.503937 | 6 | 1 | 2 |
| 2023-12 | 71 | -84.150000 | 0.157658 | 0.155914 | 0 | 0 | 0 |

### A_OPT2023_T2_SB1_TP7

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 573, entry dates 186, entry months 12; SKIP 72, EXCLUDED 117, exclusion share 0.169565; conditional FLAT CLOSED 572.
Net -375.366667 R; PF R / price 0.423016 / 0.326119; expectancy -0.655090 R; win rate 0.169284; average winner / loser 2.837113 / -1.420451 R.
Conditional CLOSED-only DD 375.366667 R; largest winner share 0.042393; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 12 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 42 | -39.033333 | 0.164168 | 0.163522 | 18 | 9 | 12 |
| 2023-02 | 32 | -26.750000 | 0.205446 | 0.207547 | 18 | 16 | 13 |
| 2023-03 | 16 | -16.416667 | 0.066351 | 0.070175 | 22 | 11 | 13 |
| 2023-04 | 32 | -17.833333 | 0.415301 | 0.447917 | 18 | 12 | 10 |
| 2023-05 | 28 | -18.583333 | 0.309598 | 0.276596 | 21 | 3 | 19 |
| 2023-06 | 22 | -21.250000 | 0.098940 | 0.095890 | 20 | 10 | 16 |
| 2023-07 | 33 | -19.050000 | 0.385484 | 0.447619 | 19 | 5 | 17 |
| 2023-08 | 81 | -43.150000 | 0.476123 | 0.460145 | 14 | 3 | 5 |
| 2023-09 | 58 | -31.850000 | 0.464856 | 0.274936 | 14 | 2 | 9 |
| 2023-10 | 77 | -15.283333 | 0.837757 | 0.841226 | 2 | 0 | 1 |
| 2023-11 | 81 | -42.016667 | 0.598439 | 0.559055 | 6 | 1 | 2 |
| 2023-12 | 71 | -84.150000 | 0.157658 | 0.155914 | 0 | 0 | 0 |

### A_OPT2023_T2_SB1_TP8

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 571, entry dates 186, entry months 12; SKIP 72, EXCLUDED 117, exclusion share 0.170058; conditional FLAT CLOSED 570.
Net -372.883333 R; PF R / price 0.423881 / 0.329791; expectancy -0.653036 R; win rate 0.169877; average winner / loser 2.828351 / -1.419371 R.
Conditional CLOSED-only DD 372.883333 R; largest winner share 0.048600; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 12 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 42 | -39.033333 | 0.164168 | 0.163522 | 18 | 9 | 12 |
| 2023-02 | 32 | -26.750000 | 0.205446 | 0.207547 | 18 | 16 | 13 |
| 2023-03 | 16 | -16.416667 | 0.066351 | 0.070175 | 22 | 11 | 13 |
| 2023-04 | 32 | -17.833333 | 0.415301 | 0.447917 | 18 | 12 | 10 |
| 2023-05 | 28 | -18.583333 | 0.309598 | 0.276596 | 21 | 3 | 19 |
| 2023-06 | 22 | -21.250000 | 0.098940 | 0.095890 | 20 | 10 | 16 |
| 2023-07 | 33 | -19.050000 | 0.385484 | 0.447619 | 19 | 5 | 17 |
| 2023-08 | 81 | -41.483333 | 0.496358 | 0.478261 | 14 | 3 | 5 |
| 2023-09 | 58 | -30.350000 | 0.490059 | 0.278772 | 14 | 2 | 9 |
| 2023-10 | 77 | -10.716667 | 0.886235 | 0.891365 | 2 | 0 | 1 |
| 2023-11 | 79 | -47.266667 | 0.533399 | 0.487871 | 6 | 1 | 2 |
| 2023-12 | 71 | -84.150000 | 0.157658 | 0.155914 | 0 | 0 | 0 |

### A_OPT2023_T2_SB1_TP9

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 571, entry dates 186, entry months 12; SKIP 72, EXCLUDED 117, exclusion share 0.170058; conditional FLAT CLOSED 570.
Net -367.650000 R; PF R / price 0.431967 / 0.334983; expectancy -0.643870 R; win rate 0.169877; average winner / loser 2.882302 / -1.419371 R.
Conditional CLOSED-only DD 367.650000 R; largest winner share 0.053651; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 12 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 42 | -39.033333 | 0.164168 | 0.163522 | 18 | 9 | 12 |
| 2023-02 | 32 | -26.750000 | 0.205446 | 0.207547 | 18 | 16 | 13 |
| 2023-03 | 16 | -16.416667 | 0.066351 | 0.070175 | 22 | 11 | 13 |
| 2023-04 | 32 | -17.833333 | 0.415301 | 0.447917 | 18 | 12 | 10 |
| 2023-05 | 28 | -18.583333 | 0.309598 | 0.276596 | 21 | 3 | 19 |
| 2023-06 | 22 | -21.250000 | 0.098940 | 0.095890 | 20 | 10 | 16 |
| 2023-07 | 33 | -19.050000 | 0.385484 | 0.447619 | 19 | 5 | 17 |
| 2023-08 | 81 | -39.816667 | 0.516592 | 0.496377 | 14 | 3 | 5 |
| 2023-09 | 58 | -31.350000 | 0.473257 | 0.276215 | 14 | 2 | 9 |
| 2023-10 | 77 | -6.150000 | 0.934713 | 0.941504 | 2 | 0 | 1 |
| 2023-11 | 79 | -47.266667 | 0.533399 | 0.487871 | 6 | 1 | 2 |
| 2023-12 | 71 | -84.150000 | 0.157658 | 0.155914 | 0 | 0 | 0 |

### A_OPT2023_T2_SB1_TP10

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 571, entry dates 186, entry months 12; SKIP 72, EXCLUDED 117, exclusion share 0.170058; conditional FLAT CLOSED 570.
Net -376.083333 R; PF R / price 0.419535 / 0.324416; expectancy -0.658640 R; win rate 0.169877; average winner / loser 2.802234 / -1.420833 R.
Conditional CLOSED-only DD 376.083333 R; largest winner share 0.055184; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 12 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 42 | -39.033333 | 0.164168 | 0.163522 | 18 | 9 | 12 |
| 2023-02 | 32 | -26.750000 | 0.205446 | 0.207547 | 18 | 16 | 13 |
| 2023-03 | 16 | -16.416667 | 0.066351 | 0.070175 | 22 | 11 | 13 |
| 2023-04 | 32 | -17.833333 | 0.415301 | 0.447917 | 18 | 12 | 10 |
| 2023-05 | 28 | -18.583333 | 0.309598 | 0.276596 | 21 | 3 | 19 |
| 2023-06 | 22 | -21.250000 | 0.098940 | 0.095890 | 20 | 10 | 16 |
| 2023-07 | 33 | -19.050000 | 0.385484 | 0.447619 | 19 | 5 | 17 |
| 2023-08 | 81 | -44.483333 | 0.464271 | 0.451264 | 14 | 3 | 5 |
| 2023-09 | 58 | -31.350000 | 0.473257 | 0.276215 | 14 | 2 | 9 |
| 2023-10 | 77 | -5.916667 | 0.937190 | 0.955432 | 2 | 0 | 1 |
| 2023-11 | 79 | -51.266667 | 0.493912 | 0.455526 | 6 | 1 | 2 |
| 2023-12 | 71 | -84.150000 | 0.157658 | 0.155914 | 0 | 0 | 0 |

### A_OPT2023_T2_SB2_TP2

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 666, entry dates 184, entry months 12; SKIP 23, EXCLUDED 157, exclusion share 0.190765; conditional FLAT CLOSED 665.
Net -280.966667 R; PF R / price 0.554222 / 0.448737; expectancy -0.421872 R; win rate 0.258258; average winner / loser 2.030911 / -1.335346 R.
Conditional CLOSED-only DD 280.966667 R; largest winner share 0.009542; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 12 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 55 | -46.700000 | 0.179021 | 0.168269 | 18 | 5 | 17 |
| 2023-02 | 32 | -27.950000 | 0.140881 | 0.127119 | 18 | 3 | 18 |
| 2023-03 | 15 | -11.583333 | 0.053134 | 0.071429 | 22 | 1 | 21 |
| 2023-04 | 33 | -0.550000 | 0.973451 | 1.000000 | 18 | 4 | 16 |
| 2023-05 | 34 | -16.483333 | 0.483281 | 0.447368 | 21 | 2 | 19 |
| 2023-06 | 24 | -7.633333 | 0.563394 | 0.516667 | 20 | 3 | 20 |
| 2023-07 | 34 | -10.050000 | 0.622180 | 0.715686 | 19 | 3 | 18 |
| 2023-08 | 87 | -35.166667 | 0.537078 | 0.563380 | 14 | 1 | 11 |
| 2023-09 | 63 | -37.166667 | 0.346807 | 0.291040 | 14 | 0 | 13 |
| 2023-10 | 98 | -15.466667 | 0.839057 | 0.863962 | 2 | 0 | 2 |
| 2023-11 | 102 | -37.100000 | 0.651698 | 0.668182 | 6 | 1 | 2 |
| 2023-12 | 89 | -35.116667 | 0.635908 | 0.636580 | 0 | 0 | 0 |

### A_OPT2023_T2_SB2_TP3

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 652, entry dates 184, entry months 12; SKIP 23, EXCLUDED 156, exclusion share 0.193069; conditional FLAT CLOSED 651.
Net -275.333333 R; PF R / price 0.567686 / 0.417226; expectancy -0.422290 R; win rate 0.233129; average winner / loser 2.378618 / -1.340807 R.
Conditional CLOSED-only DD 275.333333 R; largest winner share 0.013829; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 55 | -46.366667 | 0.184881 | 0.173077 | 18 | 5 | 17 |
| 2023-02 | 32 | -27.950000 | 0.140881 | 0.127119 | 18 | 3 | 18 |
| 2023-03 | 15 | -11.583333 | 0.053134 | 0.071429 | 22 | 1 | 21 |
| 2023-04 | 32 | 1.033333 | 1.053773 | 1.090909 | 18 | 4 | 16 |
| 2023-05 | 37 | -18.550000 | 0.464389 | 0.438017 | 21 | 2 | 18 |
| 2023-06 | 24 | -10.966667 | 0.372736 | 0.366667 | 20 | 3 | 20 |
| 2023-07 | 33 | -18.566667 | 0.343160 | 0.373832 | 19 | 3 | 18 |
| 2023-08 | 82 | -33.533333 | 0.526588 | 0.573077 | 14 | 1 | 11 |
| 2023-09 | 62 | -33.766667 | 0.391592 | 0.281401 | 14 | 0 | 13 |
| 2023-10 | 94 | -1.933333 | 0.980082 | 0.971564 | 2 | 0 | 2 |
| 2023-11 | 99 | -30.000000 | 0.725652 | 0.711454 | 6 | 1 | 2 |
| 2023-12 | 87 | -43.150000 | 0.580593 | 0.537445 | 0 | 0 | 0 |

### A_OPT2023_T2_SB2_TP4

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 643, entry dates 184, entry months 12; SKIP 23, EXCLUDED 156, exclusion share 0.195244; conditional FLAT CLOSED 642.
Net -279.800000 R; PF R / price 0.560201 / 0.427099; expectancy -0.435148 R; win rate 0.220840; average winner / loser 2.509859 / -1.336555 R.
Conditional CLOSED-only DD 282.033333 R; largest winner share 0.018706; largest positive month share 0.813814. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 55 | -46.366667 | 0.184881 | 0.173077 | 18 | 5 | 17 |
| 2023-02 | 32 | -27.950000 | 0.140881 | 0.127119 | 18 | 3 | 18 |
| 2023-03 | 15 | -11.583333 | 0.053134 | 0.071429 | 22 | 1 | 21 |
| 2023-04 | 32 | 1.033333 | 1.053773 | 1.090909 | 18 | 4 | 16 |
| 2023-05 | 37 | -18.550000 | 0.464389 | 0.438017 | 21 | 2 | 18 |
| 2023-06 | 24 | -10.966667 | 0.372736 | 0.366667 | 20 | 3 | 20 |
| 2023-07 | 33 | -18.566667 | 0.343160 | 0.373832 | 19 | 3 | 18 |
| 2023-08 | 82 | -29.133333 | 0.588706 | 0.646154 | 14 | 1 | 11 |
| 2023-09 | 62 | -30.766667 | 0.445646 | 0.288647 | 14 | 0 | 13 |
| 2023-10 | 93 | 4.516667 | 1.045137 | 1.039080 | 2 | 0 | 2 |
| 2023-11 | 94 | -44.333333 | 0.588617 | 0.568584 | 6 | 1 | 2 |
| 2023-12 | 84 | -47.133333 | 0.532330 | 0.434389 | 0 | 0 | 0 |

### A_OPT2023_T2_SB2_TP5

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 641, entry dates 184, entry months 12; SKIP 23, EXCLUDED 156, exclusion share 0.195734; conditional FLAT CLOSED 640.
Net -282.366667 R; PF R / price 0.558710 / 0.427836; expectancy -0.440510 R; win rate 0.213729; average winner / loser 2.609489 / -1.335839 R.
Conditional CLOSED-only DD 286.266667 R; largest winner share 0.023310; largest positive month share 0.858770. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 55 | -46.366667 | 0.184881 | 0.173077 | 18 | 5 | 17 |
| 2023-02 | 32 | -27.950000 | 0.140881 | 0.127119 | 18 | 3 | 18 |
| 2023-03 | 15 | -11.583333 | 0.053134 | 0.071429 | 22 | 1 | 21 |
| 2023-04 | 32 | 1.033333 | 1.053773 | 1.090909 | 18 | 4 | 16 |
| 2023-05 | 37 | -18.550000 | 0.464389 | 0.438017 | 21 | 2 | 18 |
| 2023-06 | 24 | -10.966667 | 0.372736 | 0.366667 | 20 | 3 | 20 |
| 2023-07 | 33 | -18.566667 | 0.343160 | 0.373832 | 19 | 3 | 18 |
| 2023-08 | 82 | -27.933333 | 0.605647 | 0.657692 | 14 | 1 | 11 |
| 2023-09 | 62 | -27.766667 | 0.499700 | 0.295894 | 14 | 0 | 13 |
| 2023-10 | 91 | 6.283333 | 1.063361 | 1.044084 | 2 | 0 | 2 |
| 2023-11 | 94 | -53.700000 | 0.515489 | 0.498920 | 6 | 1 | 2 |
| 2023-12 | 84 | -46.300000 | 0.547336 | 0.430804 | 0 | 0 | 0 |

### A_OPT2023_T2_SB2_TP6

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 641, entry dates 184, entry months 12; SKIP 23, EXCLUDED 156, exclusion share 0.195734; conditional FLAT CLOSED 640.
Net -268.666667 R; PF R / price 0.581212 / 0.441550; expectancy -0.419137 R; win rate 0.212168; average winner / loser 2.741667 / -1.336528 R.
Conditional CLOSED-only DD 273.250000 R; largest winner share 0.026819; largest positive month share 0.939036. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 55 | -46.366667 | 0.184881 | 0.173077 | 18 | 5 | 17 |
| 2023-02 | 32 | -27.950000 | 0.140881 | 0.127119 | 18 | 3 | 18 |
| 2023-03 | 15 | -11.583333 | 0.053134 | 0.071429 | 22 | 1 | 21 |
| 2023-04 | 32 | 1.033333 | 1.053773 | 1.090909 | 18 | 4 | 16 |
| 2023-05 | 37 | -18.550000 | 0.464389 | 0.438017 | 21 | 2 | 18 |
| 2023-06 | 24 | -10.966667 | 0.372736 | 0.366667 | 20 | 3 | 20 |
| 2023-07 | 33 | -18.566667 | 0.343160 | 0.373832 | 19 | 3 | 18 |
| 2023-08 | 82 | -24.933333 | 0.648000 | 0.703846 | 14 | 1 | 11 |
| 2023-09 | 62 | -29.266667 | 0.472673 | 0.292271 | 14 | 0 | 13 |
| 2023-10 | 91 | 15.916667 | 1.160504 | 1.146172 | 2 | 0 | 2 |
| 2023-11 | 94 | -46.133333 | 0.583759 | 0.563715 | 6 | 1 | 2 |
| 2023-12 | 84 | -51.300000 | 0.506494 | 0.403974 | 0 | 0 | 0 |

### A_OPT2023_T2_SB2_TP7

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 637, entry dates 184, entry months 12; SKIP 23, EXCLUDED 156, exclusion share 0.196721; conditional FLAT CLOSED 636.
Net -256.033333 R; PF R / price 0.596925 / 0.452855; expectancy -0.401936 R; win rate 0.213501; average winner / loser 2.787990 / -1.334454 R.
Conditional CLOSED-only DD 263.950000 R; largest winner share 0.030769; largest positive month share 0.964265. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 55 | -46.366667 | 0.184881 | 0.173077 | 18 | 5 | 17 |
| 2023-02 | 32 | -27.950000 | 0.140881 | 0.127119 | 18 | 3 | 18 |
| 2023-03 | 15 | -11.583333 | 0.053134 | 0.071429 | 22 | 1 | 21 |
| 2023-04 | 32 | 1.033333 | 1.053773 | 1.090909 | 18 | 4 | 16 |
| 2023-05 | 37 | -18.550000 | 0.464389 | 0.438017 | 21 | 2 | 18 |
| 2023-06 | 24 | -10.966667 | 0.372736 | 0.366667 | 20 | 3 | 20 |
| 2023-07 | 33 | -18.566667 | 0.343160 | 0.373832 | 19 | 3 | 18 |
| 2023-08 | 82 | -21.933333 | 0.690353 | 0.750000 | 14 | 1 | 11 |
| 2023-09 | 62 | -27.766667 | 0.499700 | 0.295894 | 14 | 0 | 13 |
| 2023-10 | 91 | 27.883333 | 1.281176 | 1.264501 | 2 | 0 | 2 |
| 2023-11 | 91 | -46.300000 | 0.563893 | 0.526906 | 6 | 1 | 2 |
| 2023-12 | 83 | -54.966667 | 0.462604 | 0.372768 | 0 | 0 | 0 |

### A_OPT2023_T2_SB2_TP8

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 634, entry dates 184, entry months 12; SKIP 23, EXCLUDED 156, exclusion share 0.197468; conditional FLAT CLOSED 633.
Net -255.200000 R; PF R / price 0.596947 / 0.453432; expectancy -0.402524 R; win rate 0.214511; average winner / loser 2.779167 / -1.335795 R.
Conditional CLOSED-only DD 267.850000 R; largest winner share 0.035276; largest positive month share 0.965324. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 55 | -46.366667 | 0.184881 | 0.173077 | 18 | 5 | 17 |
| 2023-02 | 32 | -27.950000 | 0.140881 | 0.127119 | 18 | 3 | 18 |
| 2023-03 | 15 | -11.583333 | 0.053134 | 0.071429 | 22 | 1 | 21 |
| 2023-04 | 32 | 1.033333 | 1.053773 | 1.090909 | 18 | 4 | 16 |
| 2023-05 | 37 | -18.550000 | 0.464389 | 0.438017 | 21 | 2 | 18 |
| 2023-06 | 24 | -10.966667 | 0.372736 | 0.366667 | 20 | 3 | 20 |
| 2023-07 | 33 | -18.566667 | 0.343160 | 0.373832 | 19 | 3 | 18 |
| 2023-08 | 81 | -22.050000 | 0.685897 | 0.755906 | 14 | 1 | 11 |
| 2023-09 | 62 | -31.516667 | 0.432132 | 0.286836 | 14 | 0 | 13 |
| 2023-10 | 91 | 28.766667 | 1.290084 | 1.299304 | 2 | 0 | 2 |
| 2023-11 | 90 | -47.216667 | 0.555259 | 0.520179 | 6 | 1 | 2 |
| 2023-12 | 82 | -50.233333 | 0.502065 | 0.401361 | 0 | 0 | 0 |

### A_OPT2023_T2_SB2_TP9

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 634, entry dates 184, entry months 12; SKIP 23, EXCLUDED 156, exclusion share 0.197468; conditional FLAT CLOSED 633.
Net -250.650000 R; PF R / price 0.604133 / 0.458379; expectancy -0.395347 R; win rate 0.214511; average winner / loser 2.812623 / -1.335795 R.
Conditional CLOSED-only DD 266.633333 R; largest winner share 0.039214; largest positive month share 0.968938. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 55 | -46.366667 | 0.184881 | 0.173077 | 18 | 5 | 17 |
| 2023-02 | 32 | -27.950000 | 0.140881 | 0.127119 | 18 | 3 | 18 |
| 2023-03 | 15 | -11.583333 | 0.053134 | 0.071429 | 22 | 1 | 21 |
| 2023-04 | 32 | 1.033333 | 1.053773 | 1.090909 | 18 | 4 | 16 |
| 2023-05 | 37 | -18.550000 | 0.464389 | 0.438017 | 21 | 2 | 18 |
| 2023-06 | 24 | -10.966667 | 0.372736 | 0.366667 | 20 | 3 | 20 |
| 2023-07 | 33 | -18.566667 | 0.343160 | 0.373832 | 19 | 3 | 18 |
| 2023-08 | 81 | -20.550000 | 0.707265 | 0.779528 | 14 | 1 | 11 |
| 2023-09 | 62 | -31.516667 | 0.432132 | 0.286836 | 14 | 0 | 13 |
| 2023-10 | 91 | 32.233333 | 1.325042 | 1.317865 | 2 | 0 | 2 |
| 2023-11 | 90 | -50.966667 | 0.519937 | 0.486547 | 6 | 1 | 2 |
| 2023-12 | 82 | -46.900000 | 0.535107 | 0.424036 | 0 | 0 | 0 |

### A_OPT2023_T2_SB2_TP10

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 633, entry dates 184, entry months 12; SKIP 23, EXCLUDED 156, exclusion share 0.197719; conditional FLAT CLOSED 632.
Net -245.600000 R; PF R / price 0.611085 / 0.456359; expectancy -0.387994 R; win rate 0.214850; average winner / loser 2.837500 / -1.335095 R.
Conditional CLOSED-only DD 264.916667 R; largest winner share 0.043189; largest positive month share 0.971082. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 55 | -46.366667 | 0.184881 | 0.173077 | 18 | 5 | 17 |
| 2023-02 | 32 | -27.950000 | 0.140881 | 0.127119 | 18 | 3 | 18 |
| 2023-03 | 15 | -11.583333 | 0.053134 | 0.071429 | 22 | 1 | 21 |
| 2023-04 | 32 | 1.033333 | 1.053773 | 1.090909 | 18 | 4 | 16 |
| 2023-05 | 37 | -18.550000 | 0.464389 | 0.438017 | 21 | 2 | 18 |
| 2023-06 | 24 | -10.966667 | 0.372736 | 0.366667 | 20 | 3 | 20 |
| 2023-07 | 33 | -18.566667 | 0.343160 | 0.373832 | 19 | 3 | 18 |
| 2023-08 | 81 | -21.300000 | 0.696581 | 0.767717 | 14 | 1 | 11 |
| 2023-09 | 62 | -31.516667 | 0.432132 | 0.286836 | 14 | 0 | 13 |
| 2023-10 | 90 | 34.700000 | 1.355897 | 1.314554 | 2 | 0 | 2 |
| 2023-11 | 90 | -50.966667 | 0.519937 | 0.486547 | 6 | 1 | 2 |
| 2023-12 | 82 | -43.566667 | 0.568148 | 0.446712 | 0 | 0 | 0 |

### A_OPT2023_T3_SB1_TP2

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 260, entry dates 142, entry months 12; SKIP 71, EXCLUDED 72, exclusion share 0.216867; conditional FLAT CLOSED 260.
Net -182.300000 R; PF R / price 0.359339 / 0.249179; expectancy -0.701154 R; win rate 0.184615; average winner / loser 2.130208 / -1.408663 R.
Conditional CLOSED-only DD 193.500000 R; largest winner share 0.032600; largest positive month share 0.730392. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 26 | -16.316667 | 0.346898 | 0.353659 | 18 | 7 | 8 |
| 2023-02 | 20 | -20.883333 | 0.000000 | 0.000000 | 18 | 10 | 5 |
| 2023-03 | 11 | -9.833333 | 0.092308 | 0.088235 | 22 | 17 | 6 |
| 2023-04 | 21 | -10.833333 | 0.482072 | 0.484848 | 18 | 10 | 8 |
| 2023-05 | 20 | -17.066667 | 0.290859 | 0.269231 | 21 | 8 | 13 |
| 2023-06 | 18 | -18.166667 | 0.167939 | 0.166667 | 20 | 6 | 10 |
| 2023-07 | 24 | -16.783333 | 0.300694 | 0.307692 | 19 | 3 | 13 |
| 2023-08 | 49 | -49.516667 | 0.213189 | 0.213270 | 14 | 6 | 5 |
| 2023-09 | 30 | -20.000000 | 0.368421 | 0.179704 | 14 | 2 | 4 |
| 2023-10 | 10 | -6.300000 | 0.501319 | 0.488889 | 2 | 1 | 0 |
| 2023-11 | 21 | 0.916667 | 1.044607 | 1.053333 | 6 | 1 | 0 |
| 2023-12 | 10 | 2.483333 | 1.268468 | 1.625000 | 0 | 0 | 0 |

### A_OPT2023_T3_SB1_TP3

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 260, entry dates 142, entry months 12; SKIP 71, EXCLUDED 72, exclusion share 0.216867; conditional FLAT CLOSED 260.
Net -168.433333 R; PF R / price 0.410969 / 0.261199; expectancy -0.647821 R; win rate 0.180769; average winner / loser 2.500355 / -1.408621 R.
Conditional CLOSED-only DD 184.833333 R; largest winner share 0.042547; largest positive month share 0.767327. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 26 | -15.150000 | 0.393596 | 0.414634 | 18 | 7 | 8 |
| 2023-02 | 20 | -20.883333 | 0.000000 | 0.000000 | 18 | 10 | 5 |
| 2023-03 | 11 | -9.833333 | 0.092308 | 0.088235 | 22 | 17 | 6 |
| 2023-04 | 21 | -10.500000 | 0.498008 | 0.500000 | 18 | 10 | 8 |
| 2023-05 | 20 | -18.066667 | 0.249307 | 0.230769 | 21 | 8 | 13 |
| 2023-06 | 18 | -18.166667 | 0.167939 | 0.166667 | 20 | 6 | 10 |
| 2023-07 | 24 | -17.450000 | 0.272917 | 0.282051 | 19 | 3 | 13 |
| 2023-08 | 49 | -48.683333 | 0.226430 | 0.232227 | 14 | 6 | 5 |
| 2023-09 | 30 | -16.666667 | 0.473684 | 0.190275 | 14 | 2 | 4 |
| 2023-10 | 10 | -3.133333 | 0.751979 | 0.733333 | 2 | 1 | 0 |
| 2023-11 | 21 | 7.750000 | 1.377129 | 1.360000 | 6 | 1 | 0 |
| 2023-12 | 10 | 2.350000 | 1.220657 | 1.410256 | 0 | 0 | 0 |

### A_OPT2023_T3_SB1_TP4

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 259, entry dates 142, entry months 12; SKIP 71, EXCLUDED 72, exclusion share 0.217523; conditional FLAT CLOSED 259.
Net -148.616667 R; PF R / price 0.477530 / 0.271625; expectancy -0.573810 R; win rate 0.181467; average winner / loser 2.890071 / -1.408168 R.
Conditional CLOSED-only DD 182.983333 R; largest winner share 0.049080; largest positive month share 0.758136. Positive / negative / zero months 3 / 9 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 26 | -17.400000 | 0.303536 | 0.304878 | 18 | 7 | 8 |
| 2023-02 | 20 | -20.883333 | 0.000000 | 0.000000 | 18 | 10 | 5 |
| 2023-03 | 11 | -9.833333 | 0.092308 | 0.088235 | 22 | 17 | 6 |
| 2023-04 | 21 | -10.500000 | 0.498008 | 0.500000 | 18 | 10 | 8 |
| 2023-05 | 20 | -18.066667 | 0.249307 | 0.230769 | 21 | 8 | 13 |
| 2023-06 | 18 | -18.166667 | 0.167939 | 0.166667 | 20 | 6 | 10 |
| 2023-07 | 24 | -17.450000 | 0.272917 | 0.282051 | 19 | 3 | 13 |
| 2023-08 | 49 | -45.516667 | 0.276748 | 0.284360 | 14 | 6 | 5 |
| 2023-09 | 30 | -13.333333 | 0.578947 | 0.200846 | 14 | 2 | 4 |
| 2023-10 | 10 | 0.033333 | 1.002639 | 0.977778 | 2 | 1 | 0 |
| 2023-11 | 20 | 17.083333 | 1.896763 | 1.884058 | 6 | 1 | 0 |
| 2023-12 | 10 | 5.416667 | 1.508607 | 1.717949 | 0 | 0 | 0 |

### A_OPT2023_T3_SB1_TP5

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 259, entry dates 142, entry months 12; SKIP 71, EXCLUDED 72, exclusion share 0.217523; conditional FLAT CLOSED 259.
Net -143.133333 R; PF R / price 0.499446 / 0.273943; expectancy -0.552638 R; win rate 0.177606; average winner / loser 3.104710 / -1.408621 R.
Conditional CLOSED-only DD 182.566667 R; largest winner share 0.058350; largest positive month share 0.655907. Positive / negative / zero months 3 / 9 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 26 | -17.400000 | 0.303536 | 0.304878 | 18 | 7 | 8 |
| 2023-02 | 20 | -20.883333 | 0.000000 | 0.000000 | 18 | 10 | 5 |
| 2023-03 | 11 | -9.833333 | 0.092308 | 0.088235 | 22 | 17 | 6 |
| 2023-04 | 21 | -10.500000 | 0.498008 | 0.500000 | 18 | 10 | 8 |
| 2023-05 | 20 | -18.066667 | 0.249307 | 0.230769 | 21 | 8 | 13 |
| 2023-06 | 18 | -18.166667 | 0.167939 | 0.166667 | 20 | 6 | 10 |
| 2023-07 | 24 | -17.450000 | 0.272917 | 0.282051 | 19 | 3 | 13 |
| 2023-08 | 49 | -45.100000 | 0.283369 | 0.284360 | 14 | 6 | 5 |
| 2023-09 | 30 | -10.000000 | 0.684211 | 0.211416 | 14 | 2 | 4 |
| 2023-10 | 10 | 2.200000 | 1.174142 | 1.133333 | 2 | 1 | 0 |
| 2023-11 | 20 | 15.916667 | 1.774534 | 1.706667 | 6 | 1 | 0 |
| 2023-12 | 10 | 6.150000 | 1.577465 | 1.846154 | 0 | 0 | 0 |

### A_OPT2023_T3_SB1_TP6

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors.
CLOSED 259, entry dates 142, entry months 12; SKIP 71, EXCLUDED 72, exclusion share 0.217523; conditional FLAT CLOSED 259.
Net -144.650000 R; PF R / price 0.497074 / 0.279697; expectancy -0.558494 R; win rate 0.173745; average winner / loser 3.177037 / -1.409886 R.
Conditional CLOSED-only DD 180.900000 R; largest winner share 0.069946; largest positive month share 0.425352. Positive / negative / zero months 3 / 9 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 26 | -17.400000 | 0.303536 | 0.304878 | 18 | 7 | 8 |
| 2023-02 | 20 | -20.883333 | 0.000000 | 0.000000 | 18 | 10 | 5 |
| 2023-03 | 11 | -9.833333 | 0.092308 | 0.088235 | 22 | 17 | 6 |
| 2023-04 | 21 | -10.500000 | 0.498008 | 0.500000 | 18 | 10 | 8 |
| 2023-05 | 20 | -18.066667 | 0.249307 | 0.230769 | 21 | 8 | 13 |
| 2023-06 | 18 | -18.166667 | 0.167939 | 0.166667 | 20 | 6 | 10 |
| 2023-07 | 24 | -17.450000 | 0.272917 | 0.282051 | 19 | 3 | 13 |
| 2023-08 | 49 | -43.433333 | 0.309852 | 0.308057 | 14 | 6 | 5 |
| 2023-09 | 30 | -6.666667 | 0.789474 | 0.221987 | 14 | 2 | 4 |
| 2023-10 | 10 | 3.866667 | 1.306069 | 1.244444 | 2 | 1 | 0 |
| 2023-11 | 20 | 6.333333 | 1.285071 | 1.287500 | 6 | 1 | 0 |
| 2023-12 | 10 | 7.550000 | 1.708920 | 2.025641 | 0 | 0 | 0 |

### A_OPT2023_T3_SB1_TP7

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 259, entry dates 142, entry months 12; SKIP 71, EXCLUDED 72, exclusion share 0.217523; conditional FLAT CLOSED 259.
Net -144.750000 R; PF R / price 0.496726 / 0.285876; expectancy -0.558880 R; win rate 0.173745; average winner / loser 3.174815 / -1.409886 R.
Conditional CLOSED-only DD 179.233333 R; largest winner share 0.081661; largest positive month share 0.514905. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 26 | -17.400000 | 0.303536 | 0.304878 | 18 | 7 | 8 |
| 2023-02 | 20 | -20.883333 | 0.000000 | 0.000000 | 18 | 10 | 5 |
| 2023-03 | 11 | -9.833333 | 0.092308 | 0.088235 | 22 | 17 | 6 |
| 2023-04 | 21 | -10.500000 | 0.498008 | 0.500000 | 18 | 10 | 8 |
| 2023-05 | 20 | -18.066667 | 0.249307 | 0.230769 | 21 | 8 | 13 |
| 2023-06 | 18 | -18.166667 | 0.167939 | 0.166667 | 20 | 6 | 10 |
| 2023-07 | 24 | -17.450000 | 0.272917 | 0.282051 | 19 | 3 | 13 |
| 2023-08 | 49 | -41.766667 | 0.336335 | 0.331754 | 14 | 6 | 5 |
| 2023-09 | 30 | -9.000000 | 0.715789 | 0.214588 | 14 | 2 | 4 |
| 2023-10 | 10 | -0.133333 | 0.989446 | 0.977778 | 2 | 1 | 0 |
| 2023-11 | 20 | 9.500000 | 1.427607 | 1.425000 | 6 | 1 | 0 |
| 2023-12 | 10 | 8.950000 | 1.840376 | 2.205128 | 0 | 0 | 0 |

### A_OPT2023_T3_SB1_TP8

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 259, entry dates 142, entry months 12; SKIP 71, EXCLUDED 72, exclusion share 0.217523; conditional FLAT CLOSED 259.
Net -144.600000 R; PF R / price 0.497247 / 0.291173; expectancy -0.558301 R; win rate 0.173745; average winner / loser 3.178148 / -1.409886 R.
Conditional CLOSED-only DD 177.566667 R; largest winner share 0.093229; largest positive month share 0.677948. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 26 | -17.400000 | 0.303536 | 0.304878 | 18 | 7 | 8 |
| 2023-02 | 20 | -20.883333 | 0.000000 | 0.000000 | 18 | 10 | 5 |
| 2023-03 | 11 | -9.833333 | 0.092308 | 0.088235 | 22 | 17 | 6 |
| 2023-04 | 21 | -10.500000 | 0.498008 | 0.500000 | 18 | 10 | 8 |
| 2023-05 | 20 | -18.066667 | 0.249307 | 0.230769 | 21 | 8 | 13 |
| 2023-06 | 18 | -18.166667 | 0.167939 | 0.166667 | 20 | 6 | 10 |
| 2023-07 | 24 | -17.450000 | 0.272917 | 0.282051 | 19 | 3 | 13 |
| 2023-08 | 49 | -40.100000 | 0.362818 | 0.355450 | 14 | 6 | 5 |
| 2023-09 | 30 | -7.333333 | 0.768421 | 0.219873 | 14 | 2 | 4 |
| 2023-10 | 10 | -0.133333 | 0.989446 | 0.977778 | 2 | 1 | 0 |
| 2023-11 | 20 | 4.916667 | 1.221305 | 1.175000 | 6 | 1 | 0 |
| 2023-12 | 10 | 10.350000 | 1.971831 | 2.384615 | 0 | 0 | 0 |

### A_OPT2023_T3_SB1_TP9

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 259, entry dates 142, entry months 12; SKIP 71, EXCLUDED 72, exclusion share 0.217523; conditional FLAT CLOSED 259.
Net -138.200000 R; PF R / price 0.519499 / 0.299622; expectancy -0.533591 R; win rate 0.173745; average winner / loser 3.320370 / -1.409886 R.
Conditional CLOSED-only DD 175.900000 R; largest winner share 0.100390; largest positive month share 0.640909. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 26 | -17.400000 | 0.303536 | 0.304878 | 18 | 7 | 8 |
| 2023-02 | 20 | -20.883333 | 0.000000 | 0.000000 | 18 | 10 | 5 |
| 2023-03 | 11 | -9.833333 | 0.092308 | 0.088235 | 22 | 17 | 6 |
| 2023-04 | 21 | -10.500000 | 0.498008 | 0.500000 | 18 | 10 | 8 |
| 2023-05 | 20 | -18.066667 | 0.249307 | 0.230769 | 21 | 8 | 13 |
| 2023-06 | 18 | -18.166667 | 0.167939 | 0.166667 | 20 | 6 | 10 |
| 2023-07 | 24 | -17.450000 | 0.272917 | 0.282051 | 19 | 3 | 13 |
| 2023-08 | 49 | -38.433333 | 0.389301 | 0.379147 | 14 | 6 | 5 |
| 2023-09 | 30 | -5.666667 | 0.821053 | 0.225159 | 14 | 2 | 4 |
| 2023-10 | 10 | -0.133333 | 0.989446 | 0.977778 | 2 | 1 | 0 |
| 2023-11 | 20 | 6.583333 | 1.296324 | 1.237500 | 6 | 1 | 0 |
| 2023-12 | 10 | 11.750000 | 2.103286 | 2.564103 | 0 | 0 | 0 |

### A_OPT2023_T3_SB1_TP10

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 259, entry dates 142, entry months 12; SKIP 71, EXCLUDED 72, exclusion share 0.217523; conditional FLAT CLOSED 259.
Net -142.800000 R; PF R / price 0.503506 / 0.303909; expectancy -0.551351 R; win rate 0.173745; average winner / loser 3.218148 / -1.409886 R.
Conditional CLOSED-only DD 174.233333 R; largest winner share 0.115088; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 26 | -17.400000 | 0.303536 | 0.304878 | 18 | 7 | 8 |
| 2023-02 | 20 | -20.883333 | 0.000000 | 0.000000 | 18 | 10 | 5 |
| 2023-03 | 11 | -9.833333 | 0.092308 | 0.088235 | 22 | 17 | 6 |
| 2023-04 | 21 | -10.500000 | 0.498008 | 0.500000 | 18 | 10 | 8 |
| 2023-05 | 20 | -18.066667 | 0.249307 | 0.230769 | 21 | 8 | 13 |
| 2023-06 | 18 | -18.166667 | 0.167939 | 0.166667 | 20 | 6 | 10 |
| 2023-07 | 24 | -17.450000 | 0.272917 | 0.282051 | 19 | 3 | 13 |
| 2023-08 | 49 | -36.766667 | 0.415784 | 0.402844 | 14 | 6 | 5 |
| 2023-09 | 30 | -4.000000 | 0.873684 | 0.230444 | 14 | 2 | 4 |
| 2023-10 | 10 | -0.133333 | 0.989446 | 0.977778 | 2 | 1 | 0 |
| 2023-11 | 20 | -2.750000 | 0.876219 | 0.887500 | 6 | 1 | 0 |
| 2023-12 | 10 | 13.150000 | 2.234742 | 2.743590 | 0 | 0 | 0 |

### A_OPT2023_T3_SB2_TP2

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 352, entry dates 150, entry months 12; SKIP 18, EXCLUDED 142, exclusion share 0.287449; conditional FLAT CLOSED 352.
Net -178.766667 R; PF R / price 0.447113 / 0.315093; expectancy -0.507860 R; win rate 0.238636; average winner / loser 1.721032 / -1.288181 R.
Conditional CLOSED-only DD 198.350000 R; largest winner share 0.023057; largest positive month share 0.532973. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 35 | -18.950000 | 0.370083 | 0.407407 | 18 | 1 | 15 |
| 2023-02 | 24 | -28.283333 | 0.023028 | 0.020619 | 18 | 0 | 18 |
| 2023-03 | 14 | -8.733333 | 0.322997 | 0.302326 | 22 | 5 | 20 |
| 2023-04 | 25 | -14.733333 | 0.329795 | 0.317073 | 18 | 3 | 17 |
| 2023-05 | 32 | -21.650000 | 0.295553 | 0.287037 | 21 | 3 | 18 |
| 2023-06 | 27 | -14.566667 | 0.398900 | 0.400000 | 20 | 3 | 17 |
| 2023-07 | 30 | -18.283333 | 0.295892 | 0.311111 | 19 | 1 | 17 |
| 2023-08 | 69 | -50.850000 | 0.254217 | 0.246094 | 14 | 1 | 9 |
| 2023-09 | 46 | -14.366667 | 0.608538 | 0.435208 | 14 | 0 | 10 |
| 2023-10 | 12 | -3.766667 | 0.708010 | 0.654545 | 2 | 0 | 1 |
| 2023-11 | 25 | 8.216667 | 1.399514 | 1.420455 | 6 | 1 | 0 |
| 2023-12 | 13 | 7.200000 | 1.710526 | 2.000000 | 0 | 0 | 0 |

### A_OPT2023_T3_SB2_TP3

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 349, entry dates 149, entry months 12; SKIP 18, EXCLUDED 142, exclusion share 0.289206; conditional FLAT CLOSED 349.
Net -168.450000 R; PF R / price 0.480894 / 0.311505; expectancy -0.482665 R; win rate 0.226361; average winner / loser 1.975316 / -1.282609 R.
Conditional CLOSED-only DD 201.050000 R; largest winner share 0.032041; largest positive month share 0.720399. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 35 | -18.283333 | 0.392244 | 0.407407 | 18 | 1 | 15 |
| 2023-02 | 24 | -28.283333 | 0.023028 | 0.020619 | 18 | 0 | 18 |
| 2023-03 | 14 | -7.066667 | 0.452196 | 0.418605 | 22 | 5 | 20 |
| 2023-04 | 24 | -14.566667 | 0.305798 | 0.291139 | 18 | 3 | 17 |
| 2023-05 | 32 | -21.650000 | 0.295553 | 0.287037 | 21 | 3 | 18 |
| 2023-06 | 26 | -17.900000 | 0.261348 | 0.275000 | 20 | 3 | 17 |
| 2023-07 | 30 | -22.283333 | 0.163329 | 0.195652 | 19 | 1 | 17 |
| 2023-08 | 69 | -47.950000 | 0.296749 | 0.296875 | 14 | 1 | 9 |
| 2023-09 | 46 | -13.033333 | 0.644868 | 0.404238 | 14 | 0 | 10 |
| 2023-10 | 12 | -5.866667 | 0.597254 | 0.650000 | 2 | 0 | 1 |
| 2023-11 | 24 | 20.483333 | 2.074301 | 2.048780 | 6 | 1 | 0 |
| 2023-12 | 13 | 7.950000 | 1.693314 | 1.775510 | 0 | 0 | 0 |

### A_OPT2023_T3_SB2_TP4

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 348, entry dates 149, entry months 12; SKIP 18, EXCLUDED 142, exclusion share 0.289796; conditional FLAT CLOSED 348.
Net -153.050000 R; PF R / price 0.528351 / 0.323248; expectancy -0.439799 R; win rate 0.224138; average winner / loser 2.198077 / -1.282609 R.
Conditional CLOSED-only DD 198.633333 R; largest winner share 0.038884; largest positive month share 0.710062. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 35 | -16.616667 | 0.447645 | 0.453704 | 18 | 1 | 15 |
| 2023-02 | 24 | -28.283333 | 0.023028 | 0.020619 | 18 | 0 | 18 |
| 2023-03 | 14 | -11.066667 | 0.142119 | 0.139535 | 22 | 5 | 20 |
| 2023-04 | 24 | -14.566667 | 0.305798 | 0.291139 | 18 | 3 | 17 |
| 2023-05 | 32 | -21.650000 | 0.295553 | 0.287037 | 21 | 3 | 18 |
| 2023-06 | 26 | -17.900000 | 0.261348 | 0.275000 | 20 | 3 | 17 |
| 2023-07 | 30 | -22.283333 | 0.163329 | 0.195652 | 19 | 1 | 17 |
| 2023-08 | 69 | -45.050000 | 0.339281 | 0.347656 | 14 | 1 | 9 |
| 2023-09 | 46 | -10.033333 | 0.726612 | 0.414018 | 14 | 0 | 10 |
| 2023-10 | 12 | -3.366667 | 0.768879 | 0.833333 | 2 | 0 | 1 |
| 2023-11 | 23 | 26.816667 | 2.406469 | 2.317073 | 6 | 1 | 0 |
| 2023-12 | 13 | 10.950000 | 1.954942 | 2.040816 | 0 | 0 | 0 |

### A_OPT2023_T3_SB2_TP5

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 348, entry dates 149, entry months 12; SKIP 18, EXCLUDED 142, exclusion share 0.289796; conditional FLAT CLOSED 348.
Net -148.450000 R; PF R / price 0.544632 / 0.319077; expectancy -0.426580 R; win rate 0.221264; average winner / loser 2.305844 / -1.283465 R.
Conditional CLOSED-only DD 199.683333 R; largest winner share 0.046935; largest positive month share 0.646835. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 35 | -17.950000 | 0.403324 | 0.416667 | 18 | 1 | 15 |
| 2023-02 | 24 | -28.283333 | 0.023028 | 0.020619 | 18 | 0 | 18 |
| 2023-03 | 14 | -11.066667 | 0.142119 | 0.139535 | 22 | 5 | 20 |
| 2023-04 | 24 | -14.566667 | 0.305798 | 0.291139 | 18 | 3 | 17 |
| 2023-05 | 32 | -21.650000 | 0.295553 | 0.287037 | 21 | 3 | 18 |
| 2023-06 | 26 | -17.900000 | 0.261348 | 0.275000 | 20 | 3 | 17 |
| 2023-07 | 30 | -22.283333 | 0.163329 | 0.195652 | 19 | 1 | 17 |
| 2023-08 | 69 | -45.350000 | 0.334881 | 0.335938 | 14 | 1 | 9 |
| 2023-09 | 46 | -7.033333 | 0.808356 | 0.423798 | 14 | 0 | 10 |
| 2023-10 | 12 | -1.866667 | 0.871854 | 0.933333 | 2 | 0 | 1 |
| 2023-11 | 23 | 25.550000 | 2.242301 | 2.147727 | 6 | 1 | 0 |
| 2023-12 | 13 | 13.950000 | 2.216570 | 2.306122 | 0 | 0 | 0 |

### A_OPT2023_T3_SB2_TP6

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 348, entry dates 149, entry months 12; SKIP 18, EXCLUDED 142, exclusion share 0.289796; conditional FLAT CLOSED 348.
Net -145.416667 R; PF R / price 0.553937 / 0.325244; expectancy -0.417864 R; win rate 0.221264; average winner / loser 2.345238 / -1.283465 R.
Conditional CLOSED-only DD 198.183333 R; largest winner share 0.055376; largest positive month share 0.627745. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 35 | -17.950000 | 0.403324 | 0.416667 | 18 | 1 | 15 |
| 2023-02 | 24 | -28.283333 | 0.023028 | 0.020619 | 18 | 0 | 18 |
| 2023-03 | 14 | -11.066667 | 0.142119 | 0.139535 | 22 | 5 | 20 |
| 2023-04 | 24 | -14.566667 | 0.305798 | 0.291139 | 18 | 3 | 17 |
| 2023-05 | 32 | -21.650000 | 0.295553 | 0.287037 | 21 | 3 | 18 |
| 2023-06 | 26 | -17.900000 | 0.261348 | 0.275000 | 20 | 3 | 17 |
| 2023-07 | 30 | -22.283333 | 0.163329 | 0.195652 | 19 | 1 | 17 |
| 2023-08 | 69 | -43.850000 | 0.356881 | 0.359375 | 14 | 1 | 9 |
| 2023-09 | 46 | -8.533333 | 0.767484 | 0.418908 | 14 | 0 | 10 |
| 2023-10 | 12 | -4.866667 | 0.665904 | 0.733333 | 2 | 0 | 1 |
| 2023-11 | 23 | 28.583333 | 2.389789 | 2.227273 | 6 | 1 | 0 |
| 2023-12 | 13 | 16.950000 | 2.478198 | 2.571429 | 0 | 0 | 0 |

### A_OPT2023_T3_SB2_TP7

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 348, entry dates 149, entry months 12; SKIP 18, EXCLUDED 142, exclusion share 0.289796; conditional FLAT CLOSED 348.
Net -139.583333 R; PF R / price 0.571830 / 0.332206; expectancy -0.401102 R; win rate 0.221264; average winner / loser 2.420996 / -1.283465 R.
Conditional CLOSED-only DD 196.683333 R; largest winner share 0.062584; largest positive month share 0.587526. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 35 | -17.950000 | 0.403324 | 0.416667 | 18 | 1 | 15 |
| 2023-02 | 24 | -28.283333 | 0.023028 | 0.020619 | 18 | 0 | 18 |
| 2023-03 | 14 | -11.066667 | 0.142119 | 0.139535 | 22 | 5 | 20 |
| 2023-04 | 24 | -14.566667 | 0.305798 | 0.291139 | 18 | 3 | 17 |
| 2023-05 | 32 | -21.650000 | 0.295553 | 0.287037 | 21 | 3 | 18 |
| 2023-06 | 26 | -17.900000 | 0.261348 | 0.275000 | 20 | 3 | 17 |
| 2023-07 | 30 | -22.283333 | 0.163329 | 0.195652 | 19 | 1 | 17 |
| 2023-08 | 69 | -42.350000 | 0.378880 | 0.382812 | 14 | 1 | 9 |
| 2023-09 | 46 | -7.033333 | 0.808356 | 0.423798 | 14 | 0 | 10 |
| 2023-10 | 12 | -4.866667 | 0.665904 | 0.733333 | 2 | 0 | 1 |
| 2023-11 | 23 | 28.416667 | 2.381686 | 2.125000 | 6 | 1 | 0 |
| 2023-12 | 13 | 19.950000 | 2.739826 | 2.836735 | 0 | 0 | 0 |

### A_OPT2023_T3_SB2_TP8

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 348, entry dates 149, entry months 12; SKIP 18, EXCLUDED 142, exclusion share 0.289796; conditional FLAT CLOSED 348.
Net -138.833333 R; PF R / price 0.574131 / 0.337875; expectancy -0.398946 R; win rate 0.221264; average winner / loser 2.430736 / -1.283465 R.
Conditional CLOSED-only DD 195.183333 R; largest winner share 0.071238; largest positive month share 0.502349. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 35 | -17.950000 | 0.403324 | 0.416667 | 18 | 1 | 15 |
| 2023-02 | 24 | -28.283333 | 0.023028 | 0.020619 | 18 | 0 | 18 |
| 2023-03 | 14 | -11.066667 | 0.142119 | 0.139535 | 22 | 5 | 20 |
| 2023-04 | 24 | -14.566667 | 0.305798 | 0.291139 | 18 | 3 | 17 |
| 2023-05 | 32 | -21.650000 | 0.295553 | 0.287037 | 21 | 3 | 18 |
| 2023-06 | 26 | -17.900000 | 0.261348 | 0.275000 | 20 | 3 | 17 |
| 2023-07 | 30 | -22.283333 | 0.163329 | 0.195652 | 19 | 1 | 17 |
| 2023-08 | 69 | -40.850000 | 0.400880 | 0.406250 | 14 | 1 | 9 |
| 2023-09 | 46 | -5.533333 | 0.849228 | 0.428688 | 14 | 0 | 10 |
| 2023-10 | 12 | -4.866667 | 0.665904 | 0.733333 | 2 | 0 | 1 |
| 2023-11 | 23 | 23.166667 | 2.126418 | 1.875000 | 6 | 1 | 0 |
| 2023-12 | 13 | 22.950000 | 3.001453 | 3.102041 | 0 | 0 | 0 |

### A_OPT2023_T3_SB2_TP9

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 348, entry dates 149, entry months 12; SKIP 18, EXCLUDED 142, exclusion share 0.289796; conditional FLAT CLOSED 348.
Net -131.166667 R; PF R / price 0.597648 / 0.346230; expectancy -0.376916 R; win rate 0.221264; average winner / loser 2.530303 / -1.283465 R.
Conditional CLOSED-only DD 193.683333 R; largest winner share 0.076989; largest positive month share 0.510994. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 35 | -17.950000 | 0.403324 | 0.416667 | 18 | 1 | 15 |
| 2023-02 | 24 | -28.283333 | 0.023028 | 0.020619 | 18 | 0 | 18 |
| 2023-03 | 14 | -11.066667 | 0.142119 | 0.139535 | 22 | 5 | 20 |
| 2023-04 | 24 | -14.566667 | 0.305798 | 0.291139 | 18 | 3 | 17 |
| 2023-05 | 32 | -21.650000 | 0.295553 | 0.287037 | 21 | 3 | 18 |
| 2023-06 | 26 | -17.900000 | 0.261348 | 0.275000 | 20 | 3 | 17 |
| 2023-07 | 30 | -22.283333 | 0.163329 | 0.195652 | 19 | 1 | 17 |
| 2023-08 | 69 | -39.350000 | 0.422879 | 0.429688 | 14 | 1 | 9 |
| 2023-09 | 46 | -4.033333 | 0.890100 | 0.433578 | 14 | 0 | 10 |
| 2023-10 | 12 | -4.866667 | 0.665904 | 0.733333 | 2 | 0 | 1 |
| 2023-11 | 23 | 24.833333 | 2.207455 | 1.931818 | 6 | 1 | 0 |
| 2023-12 | 13 | 25.950000 | 3.263081 | 3.367347 | 0 | 0 | 0 |

### A_OPT2023_T3_SB2_TP10

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 348, entry dates 149, entry months 12; SKIP 18, EXCLUDED 142, exclusion share 0.289796; conditional FLAT CLOSED 348.
Net -125.750000 R; PF R / price 0.614264 / 0.345634; expectancy -0.361351 R; win rate 0.221264; average winner / loser 2.600649 / -1.283465 R.
Conditional CLOSED-only DD 194.433333 R; largest winner share 0.083229; largest positive month share 0.522092. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 35 | -17.950000 | 0.403324 | 0.416667 | 18 | 1 | 15 |
| 2023-02 | 24 | -28.283333 | 0.023028 | 0.020619 | 18 | 0 | 18 |
| 2023-03 | 14 | -11.066667 | 0.142119 | 0.139535 | 22 | 5 | 20 |
| 2023-04 | 24 | -14.566667 | 0.305798 | 0.291139 | 18 | 3 | 17 |
| 2023-05 | 32 | -21.650000 | 0.295553 | 0.287037 | 21 | 3 | 18 |
| 2023-06 | 26 | -17.900000 | 0.261348 | 0.275000 | 20 | 3 | 17 |
| 2023-07 | 30 | -22.283333 | 0.163329 | 0.195652 | 19 | 1 | 17 |
| 2023-08 | 69 | -40.100000 | 0.411880 | 0.417969 | 14 | 1 | 9 |
| 2023-09 | 46 | -2.533333 | 0.930972 | 0.438468 | 14 | 0 | 10 |
| 2023-10 | 12 | -4.866667 | 0.665904 | 0.733333 | 2 | 0 | 1 |
| 2023-11 | 23 | 26.500000 | 2.288493 | 1.988636 | 6 | 1 | 0 |
| 2023-12 | 13 | 28.950000 | 3.524709 | 3.632653 | 0 | 0 | 0 |

### A_OPT2023_T4_SB1_TP2

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 110, entry dates 84, entry months 12; SKIP 29, EXCLUDED 51, exclusion share 0.316770; conditional FLAT CLOSED 110.
Net -84.283333 R; PF R / price 0.281982 / 0.270457; expectancy -0.766212 R; win rate 0.181818; average winner / loser 1.655000 / -1.364922 R.
Conditional CLOSED-only DD 86.050000 R; largest winner share 0.100705; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 12 | -5.000000 | 0.571429 | 0.571429 | 18 | 3 | 4 |
| 2023-02 | 15 | -11.000000 | 0.175000 | 0.170732 | 18 | 6 | 2 |
| 2023-03 | 2 | -2.333333 | 0.000000 | 0.000000 | 22 | 6 | 7 |
| 2023-04 | 9 | -2.750000 | 0.592593 | 0.545455 | 18 | 5 | 8 |
| 2023-05 | 14 | -14.666667 | 0.200000 | 0.189655 | 21 | 1 | 10 |
| 2023-06 | 12 | -13.333333 | 0.090909 | 0.085106 | 20 | 3 | 5 |
| 2023-07 | 9 | -13.400000 | 0.000000 | 0.000000 | 19 | 1 | 8 |
| 2023-08 | 18 | -6.083333 | 0.643902 | 0.711538 | 14 | 2 | 4 |
| 2023-09 | 13 | -13.083333 | 0.036810 | 0.048780 | 14 | 1 | 3 |
| 2023-10 | 1 | -1.666667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-11 | 4 | 0.700000 | 1.241379 | 0.923077 | 6 | 1 | 0 |
| 2023-12 | 1 | -1.666667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### A_OPT2023_T4_SB1_TP3

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 110, entry dates 84, entry months 12; SKIP 29, EXCLUDED 51, exclusion share 0.316770; conditional FLAT CLOSED 110.
Net -79.450000 R; PF R / price 0.323158 / 0.316394; expectancy -0.722273 R; win rate 0.181818; average winner / loser 1.896667 / -1.364922 R.
Conditional CLOSED-only DD 84.550000 R; largest winner share 0.131810; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 12 | -1.666667 | 0.857143 | 0.857143 | 18 | 3 | 4 |
| 2023-02 | 15 | -11.000000 | 0.175000 | 0.170732 | 18 | 6 | 2 |
| 2023-03 | 2 | -2.333333 | 0.000000 | 0.000000 | 22 | 6 | 7 |
| 2023-04 | 9 | -3.416667 | 0.493827 | 0.454545 | 18 | 5 | 8 |
| 2023-05 | 14 | -15.666667 | 0.145455 | 0.137931 | 21 | 1 | 10 |
| 2023-06 | 12 | -13.333333 | 0.090909 | 0.085106 | 20 | 3 | 5 |
| 2023-07 | 9 | -13.400000 | 0.000000 | 0.000000 | 19 | 1 | 8 |
| 2023-08 | 18 | -2.916667 | 0.829268 | 0.923077 | 14 | 2 | 4 |
| 2023-09 | 13 | -13.083333 | 0.036810 | 0.048780 | 14 | 1 | 3 |
| 2023-10 | 1 | -1.666667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-11 | 4 | 0.700000 | 1.241379 | 0.923077 | 6 | 1 | 0 |
| 2023-12 | 1 | -1.666667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### A_OPT2023_T4_SB1_TP4

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 110, entry dates 84, entry months 12; SKIP 29, EXCLUDED 51, exclusion share 0.316770; conditional FLAT CLOSED 110.
Net -81.616667 R; PF R / price 0.304700 / 0.302038; expectancy -0.741970 R; win rate 0.181818; average winner / loser 1.788333 / -1.364922 R.
Conditional CLOSED-only DD 86.050000 R; largest winner share 0.186393; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 12 | -2.333333 | 0.800000 | 0.800000 | 18 | 3 | 4 |
| 2023-02 | 15 | -11.000000 | 0.175000 | 0.170732 | 18 | 6 | 2 |
| 2023-03 | 2 | -2.333333 | 0.000000 | 0.000000 | 22 | 6 | 7 |
| 2023-04 | 9 | -3.416667 | 0.493827 | 0.454545 | 18 | 5 | 8 |
| 2023-05 | 14 | -15.666667 | 0.145455 | 0.137931 | 21 | 1 | 10 |
| 2023-06 | 12 | -13.333333 | 0.090909 | 0.085106 | 20 | 3 | 5 |
| 2023-07 | 9 | -13.400000 | 0.000000 | 0.000000 | 19 | 1 | 8 |
| 2023-08 | 18 | -4.416667 | 0.741463 | 0.865385 | 14 | 2 | 4 |
| 2023-09 | 13 | -13.083333 | 0.036810 | 0.048780 | 14 | 1 | 3 |
| 2023-10 | 1 | -1.666667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-11 | 4 | 0.700000 | 1.241379 | 0.923077 | 6 | 1 | 0 |
| 2023-12 | 1 | -1.666667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### A_OPT2023_T4_SB1_TP5

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 110, entry dates 84, entry months 12; SKIP 29, EXCLUDED 51, exclusion share 0.316770; conditional FLAT CLOSED 110.
Net -85.866667 R; PF R / price 0.268494 / 0.261843; expectancy -0.780606 R; win rate 0.181818; average winner / loser 1.575833 / -1.364922 R.
Conditional CLOSED-only DD 87.300000 R; largest winner share 0.150714; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 12 | -5.333333 | 0.542857 | 0.542857 | 18 | 3 | 4 |
| 2023-02 | 15 | -11.000000 | 0.175000 | 0.170732 | 18 | 6 | 2 |
| 2023-03 | 2 | -2.333333 | 0.000000 | 0.000000 | 22 | 6 | 7 |
| 2023-04 | 9 | -3.416667 | 0.493827 | 0.454545 | 18 | 5 | 8 |
| 2023-05 | 14 | -15.666667 | 0.145455 | 0.137931 | 21 | 1 | 10 |
| 2023-06 | 12 | -13.333333 | 0.090909 | 0.085106 | 20 | 3 | 5 |
| 2023-07 | 9 | -13.400000 | 0.000000 | 0.000000 | 19 | 1 | 8 |
| 2023-08 | 18 | -5.666667 | 0.668293 | 0.769231 | 14 | 2 | 4 |
| 2023-09 | 13 | -13.083333 | 0.036810 | 0.048780 | 14 | 1 | 3 |
| 2023-10 | 1 | -1.666667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-11 | 4 | 0.700000 | 1.241379 | 0.923077 | 6 | 1 | 0 |
| 2023-12 | 1 | -1.666667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### A_OPT2023_T4_SB1_TP6

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 110, entry dates 84, entry months 12; SKIP 29, EXCLUDED 51, exclusion share 0.316770; conditional FLAT CLOSED 110.
Net -85.866667 R; PF R / price 0.268494 / 0.261843; expectancy -0.780606 R; win rate 0.181818; average winner / loser 1.575833 / -1.364922 R.
Conditional CLOSED-only DD 87.300000 R; largest winner share 0.150714; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 12 | -5.333333 | 0.542857 | 0.542857 | 18 | 3 | 4 |
| 2023-02 | 15 | -11.000000 | 0.175000 | 0.170732 | 18 | 6 | 2 |
| 2023-03 | 2 | -2.333333 | 0.000000 | 0.000000 | 22 | 6 | 7 |
| 2023-04 | 9 | -3.416667 | 0.493827 | 0.454545 | 18 | 5 | 8 |
| 2023-05 | 14 | -15.666667 | 0.145455 | 0.137931 | 21 | 1 | 10 |
| 2023-06 | 12 | -13.333333 | 0.090909 | 0.085106 | 20 | 3 | 5 |
| 2023-07 | 9 | -13.400000 | 0.000000 | 0.000000 | 19 | 1 | 8 |
| 2023-08 | 18 | -5.666667 | 0.668293 | 0.769231 | 14 | 2 | 4 |
| 2023-09 | 13 | -13.083333 | 0.036810 | 0.048780 | 14 | 1 | 3 |
| 2023-10 | 1 | -1.666667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-11 | 4 | 0.700000 | 1.241379 | 0.923077 | 6 | 1 | 0 |
| 2023-12 | 1 | -1.666667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### A_OPT2023_T4_SB1_TP7

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 110, entry dates 84, entry months 12; SKIP 29, EXCLUDED 51, exclusion share 0.316770; conditional FLAT CLOSED 110.
Net -85.866667 R; PF R / price 0.268494 / 0.261843; expectancy -0.780606 R; win rate 0.181818; average winner / loser 1.575833 / -1.364922 R.
Conditional CLOSED-only DD 87.300000 R; largest winner share 0.150714; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 12 | -5.333333 | 0.542857 | 0.542857 | 18 | 3 | 4 |
| 2023-02 | 15 | -11.000000 | 0.175000 | 0.170732 | 18 | 6 | 2 |
| 2023-03 | 2 | -2.333333 | 0.000000 | 0.000000 | 22 | 6 | 7 |
| 2023-04 | 9 | -3.416667 | 0.493827 | 0.454545 | 18 | 5 | 8 |
| 2023-05 | 14 | -15.666667 | 0.145455 | 0.137931 | 21 | 1 | 10 |
| 2023-06 | 12 | -13.333333 | 0.090909 | 0.085106 | 20 | 3 | 5 |
| 2023-07 | 9 | -13.400000 | 0.000000 | 0.000000 | 19 | 1 | 8 |
| 2023-08 | 18 | -5.666667 | 0.668293 | 0.769231 | 14 | 2 | 4 |
| 2023-09 | 13 | -13.083333 | 0.036810 | 0.048780 | 14 | 1 | 3 |
| 2023-10 | 1 | -1.666667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-11 | 4 | 0.700000 | 1.241379 | 0.923077 | 6 | 1 | 0 |
| 2023-12 | 1 | -1.666667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### A_OPT2023_T4_SB1_TP8

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 110, entry dates 84, entry months 12; SKIP 29, EXCLUDED 51, exclusion share 0.316770; conditional FLAT CLOSED 110.
Net -85.866667 R; PF R / price 0.268494 / 0.261843; expectancy -0.780606 R; win rate 0.181818; average winner / loser 1.575833 / -1.364922 R.
Conditional CLOSED-only DD 87.300000 R; largest winner share 0.150714; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 12 | -5.333333 | 0.542857 | 0.542857 | 18 | 3 | 4 |
| 2023-02 | 15 | -11.000000 | 0.175000 | 0.170732 | 18 | 6 | 2 |
| 2023-03 | 2 | -2.333333 | 0.000000 | 0.000000 | 22 | 6 | 7 |
| 2023-04 | 9 | -3.416667 | 0.493827 | 0.454545 | 18 | 5 | 8 |
| 2023-05 | 14 | -15.666667 | 0.145455 | 0.137931 | 21 | 1 | 10 |
| 2023-06 | 12 | -13.333333 | 0.090909 | 0.085106 | 20 | 3 | 5 |
| 2023-07 | 9 | -13.400000 | 0.000000 | 0.000000 | 19 | 1 | 8 |
| 2023-08 | 18 | -5.666667 | 0.668293 | 0.769231 | 14 | 2 | 4 |
| 2023-09 | 13 | -13.083333 | 0.036810 | 0.048780 | 14 | 1 | 3 |
| 2023-10 | 1 | -1.666667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-11 | 4 | 0.700000 | 1.241379 | 0.923077 | 6 | 1 | 0 |
| 2023-12 | 1 | -1.666667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### A_OPT2023_T4_SB1_TP9

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 110, entry dates 84, entry months 12; SKIP 29, EXCLUDED 51, exclusion share 0.316770; conditional FLAT CLOSED 110.
Net -85.866667 R; PF R / price 0.268494 / 0.261843; expectancy -0.780606 R; win rate 0.181818; average winner / loser 1.575833 / -1.364922 R.
Conditional CLOSED-only DD 87.300000 R; largest winner share 0.150714; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 12 | -5.333333 | 0.542857 | 0.542857 | 18 | 3 | 4 |
| 2023-02 | 15 | -11.000000 | 0.175000 | 0.170732 | 18 | 6 | 2 |
| 2023-03 | 2 | -2.333333 | 0.000000 | 0.000000 | 22 | 6 | 7 |
| 2023-04 | 9 | -3.416667 | 0.493827 | 0.454545 | 18 | 5 | 8 |
| 2023-05 | 14 | -15.666667 | 0.145455 | 0.137931 | 21 | 1 | 10 |
| 2023-06 | 12 | -13.333333 | 0.090909 | 0.085106 | 20 | 3 | 5 |
| 2023-07 | 9 | -13.400000 | 0.000000 | 0.000000 | 19 | 1 | 8 |
| 2023-08 | 18 | -5.666667 | 0.668293 | 0.769231 | 14 | 2 | 4 |
| 2023-09 | 13 | -13.083333 | 0.036810 | 0.048780 | 14 | 1 | 3 |
| 2023-10 | 1 | -1.666667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-11 | 4 | 0.700000 | 1.241379 | 0.923077 | 6 | 1 | 0 |
| 2023-12 | 1 | -1.666667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### A_OPT2023_T4_SB1_TP10

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 110, entry dates 84, entry months 12; SKIP 29, EXCLUDED 51, exclusion share 0.316770; conditional FLAT CLOSED 110.
Net -85.866667 R; PF R / price 0.268494 / 0.261843; expectancy -0.780606 R; win rate 0.181818; average winner / loser 1.575833 / -1.364922 R.
Conditional CLOSED-only DD 87.300000 R; largest winner share 0.150714; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 12 | -5.333333 | 0.542857 | 0.542857 | 18 | 3 | 4 |
| 2023-02 | 15 | -11.000000 | 0.175000 | 0.170732 | 18 | 6 | 2 |
| 2023-03 | 2 | -2.333333 | 0.000000 | 0.000000 | 22 | 6 | 7 |
| 2023-04 | 9 | -3.416667 | 0.493827 | 0.454545 | 18 | 5 | 8 |
| 2023-05 | 14 | -15.666667 | 0.145455 | 0.137931 | 21 | 1 | 10 |
| 2023-06 | 12 | -13.333333 | 0.090909 | 0.085106 | 20 | 3 | 5 |
| 2023-07 | 9 | -13.400000 | 0.000000 | 0.000000 | 19 | 1 | 8 |
| 2023-08 | 18 | -5.666667 | 0.668293 | 0.769231 | 14 | 2 | 4 |
| 2023-09 | 13 | -13.083333 | 0.036810 | 0.048780 | 14 | 1 | 3 |
| 2023-10 | 1 | -1.666667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-11 | 4 | 0.700000 | 1.241379 | 0.923077 | 6 | 1 | 0 |
| 2023-12 | 1 | -1.666667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### A_OPT2023_T4_SB2_TP2

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 206, entry dates 114, entry months 12; SKIP 13, EXCLUDED 118, exclusion share 0.364198; conditional FLAT CLOSED 206.
Net -112.250000 R; PF R / price 0.402820 / 0.388589; expectancy -0.544903 R; win rate 0.247573; average winner / loser 1.484641 / -1.278685 R.
Conditional CLOSED-only DD 113.833333 R; largest winner share 0.044024; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 19 | -4.416667 | 0.688235 | 0.739130 | 18 | 1 | 11 |
| 2023-02 | 20 | -20.633333 | 0.057121 | 0.057143 | 18 | 3 | 13 |
| 2023-03 | 11 | -8.333333 | 0.285714 | 0.285714 | 22 | 2 | 18 |
| 2023-04 | 18 | -4.183333 | 0.686642 | 0.595745 | 18 | 2 | 15 |
| 2023-05 | 21 | -12.733333 | 0.383374 | 0.356164 | 21 | 1 | 16 |
| 2023-06 | 22 | -9.066667 | 0.498155 | 0.442623 | 20 | 1 | 14 |
| 2023-07 | 21 | -17.666667 | 0.242857 | 0.217949 | 19 | 1 | 15 |
| 2023-08 | 33 | -8.783333 | 0.653289 | 0.717647 | 14 | 1 | 6 |
| 2023-09 | 30 | -20.616667 | 0.253470 | 0.225806 | 14 | 0 | 9 |
| 2023-10 | 2 | -2.666667 | 0.000000 | 0.000000 | 2 | 0 | 1 |
| 2023-11 | 6 | 1.683333 | 1.382576 | 1.100000 | 6 | 1 | 0 |
| 2023-12 | 3 | -4.833333 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### A_OPT2023_T4_SB2_TP3

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 205, entry dates 113, entry months 12; SKIP 13, EXCLUDED 118, exclusion share 0.365325; conditional FLAT CLOSED 205.
Net -110.183333 R; PF R / price 0.411728 / 0.394140; expectancy -0.537480 R; win rate 0.248780; average winner / loser 1.512092 / -1.282877 R.
Conditional CLOSED-only DD 114.600000 R; largest winner share 0.064837; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 19 | -1.250000 | 0.911765 | 0.978261 | 18 | 1 | 11 |
| 2023-02 | 20 | -20.633333 | 0.057121 | 0.057143 | 18 | 3 | 13 |
| 2023-03 | 11 | -6.666667 | 0.428571 | 0.428571 | 22 | 2 | 18 |
| 2023-04 | 18 | -4.850000 | 0.617608 | 0.533333 | 18 | 2 | 15 |
| 2023-05 | 21 | -13.066667 | 0.367232 | 0.342466 | 21 | 1 | 16 |
| 2023-06 | 21 | -12.400000 | 0.313653 | 0.278689 | 20 | 1 | 14 |
| 2023-07 | 21 | -18.000000 | 0.228571 | 0.205128 | 19 | 1 | 15 |
| 2023-08 | 33 | -8.550000 | 0.662500 | 0.741176 | 14 | 1 | 6 |
| 2023-09 | 30 | -20.616667 | 0.253470 | 0.225806 | 14 | 0 | 9 |
| 2023-10 | 2 | -2.666667 | 0.000000 | 0.000000 | 2 | 0 | 1 |
| 2023-11 | 6 | 3.350000 | 1.761364 | 1.350000 | 6 | 1 | 0 |
| 2023-12 | 3 | -4.833333 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### A_OPT2023_T4_SB2_TP4

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 205, entry dates 113, entry months 12; SKIP 13, EXCLUDED 118, exclusion share 0.365325; conditional FLAT CLOSED 205.
Net -112.616667 R; PF R / price 0.398736 / 0.374661; expectancy -0.549350 R; win rate 0.248780; average winner / loser 1.464379 / -1.282877 R.
Conditional CLOSED-only DD 119.050000 R; largest winner share 0.089266; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 19 | -2.083333 | 0.852941 | 0.869565 | 18 | 1 | 11 |
| 2023-02 | 20 | -20.633333 | 0.057121 | 0.057143 | 18 | 3 | 13 |
| 2023-03 | 11 | -11.333333 | 0.028571 | 0.028571 | 22 | 2 | 18 |
| 2023-04 | 18 | -4.850000 | 0.617608 | 0.533333 | 18 | 2 | 15 |
| 2023-05 | 21 | -13.066667 | 0.367232 | 0.342466 | 21 | 1 | 16 |
| 2023-06 | 21 | -12.400000 | 0.313653 | 0.278689 | 20 | 1 | 14 |
| 2023-07 | 21 | -18.000000 | 0.228571 | 0.205128 | 19 | 1 | 15 |
| 2023-08 | 33 | -7.150000 | 0.717763 | 0.823529 | 14 | 1 | 6 |
| 2023-09 | 30 | -20.616667 | 0.253470 | 0.225806 | 14 | 0 | 9 |
| 2023-10 | 2 | -2.666667 | 0.000000 | 0.000000 | 2 | 0 | 1 |
| 2023-11 | 6 | 5.016667 | 2.140152 | 1.600000 | 6 | 1 | 0 |
| 2023-12 | 3 | -4.833333 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### A_OPT2023_T4_SB2_TP5

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 205, entry dates 113, entry months 12; SKIP 13, EXCLUDED 118, exclusion share 0.365325; conditional FLAT CLOSED 205.
Net -114.083333 R; PF R / price 0.390906 / 0.353489; expectancy -0.556504 R; win rate 0.248780; average winner / loser 1.435621 / -1.282877 R.
Conditional CLOSED-only DD 120.850000 R; largest winner share 0.113817; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 19 | -3.416667 | 0.758824 | 0.782609 | 18 | 1 | 11 |
| 2023-02 | 20 | -20.633333 | 0.057121 | 0.057143 | 18 | 3 | 13 |
| 2023-03 | 11 | -11.333333 | 0.028571 | 0.028571 | 22 | 2 | 18 |
| 2023-04 | 18 | -4.850000 | 0.617608 | 0.533333 | 18 | 2 | 15 |
| 2023-05 | 21 | -13.066667 | 0.367232 | 0.342466 | 21 | 1 | 16 |
| 2023-06 | 21 | -12.400000 | 0.313653 | 0.278689 | 20 | 1 | 14 |
| 2023-07 | 21 | -18.000000 | 0.228571 | 0.205128 | 19 | 1 | 15 |
| 2023-08 | 33 | -8.950000 | 0.646711 | 0.717647 | 14 | 1 | 6 |
| 2023-09 | 30 | -20.616667 | 0.253470 | 0.225806 | 14 | 0 | 9 |
| 2023-10 | 2 | -2.666667 | 0.000000 | 0.000000 | 2 | 0 | 1 |
| 2023-11 | 6 | 6.683333 | 2.518939 | 1.850000 | 6 | 1 | 0 |
| 2023-12 | 3 | -4.833333 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### A_OPT2023_T4_SB2_TP6

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 205, entry dates 113, entry months 12; SKIP 13, EXCLUDED 118, exclusion share 0.365325; conditional FLAT CLOSED 205.
Net -112.416667 R; PF R / price 0.399804 / 0.354336; expectancy -0.548374 R; win rate 0.248780; average winner / loser 1.468301 / -1.282877 R.
Conditional CLOSED-only DD 120.850000 R; largest winner share 0.133541; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 19 | -3.416667 | 0.758824 | 0.782609 | 18 | 1 | 11 |
| 2023-02 | 20 | -20.633333 | 0.057121 | 0.057143 | 18 | 3 | 13 |
| 2023-03 | 11 | -11.333333 | 0.028571 | 0.028571 | 22 | 2 | 18 |
| 2023-04 | 18 | -4.850000 | 0.617608 | 0.533333 | 18 | 2 | 15 |
| 2023-05 | 21 | -13.066667 | 0.367232 | 0.342466 | 21 | 1 | 16 |
| 2023-06 | 21 | -12.400000 | 0.313653 | 0.278689 | 20 | 1 | 14 |
| 2023-07 | 21 | -18.000000 | 0.228571 | 0.205128 | 19 | 1 | 15 |
| 2023-08 | 33 | -8.950000 | 0.646711 | 0.717647 | 14 | 1 | 6 |
| 2023-09 | 30 | -20.616667 | 0.253470 | 0.225806 | 14 | 0 | 9 |
| 2023-10 | 2 | -2.666667 | 0.000000 | 0.000000 | 2 | 0 | 1 |
| 2023-11 | 6 | 8.350000 | 2.897727 | 2.100000 | 6 | 1 | 0 |
| 2023-12 | 3 | -4.833333 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### A_OPT2023_T4_SB2_TP7

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 205, entry dates 113, entry months 12; SKIP 13, EXCLUDED 118, exclusion share 0.365325; conditional FLAT CLOSED 205.
Net -110.750000 R; PF R / price 0.408703 / 0.355183; expectancy -0.540244 R; win rate 0.248780; average winner / loser 1.500980 / -1.282877 R.
Conditional CLOSED-only DD 120.850000 R; largest winner share 0.152406; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 19 | -3.416667 | 0.758824 | 0.782609 | 18 | 1 | 11 |
| 2023-02 | 20 | -20.633333 | 0.057121 | 0.057143 | 18 | 3 | 13 |
| 2023-03 | 11 | -11.333333 | 0.028571 | 0.028571 | 22 | 2 | 18 |
| 2023-04 | 18 | -4.850000 | 0.617608 | 0.533333 | 18 | 2 | 15 |
| 2023-05 | 21 | -13.066667 | 0.367232 | 0.342466 | 21 | 1 | 16 |
| 2023-06 | 21 | -12.400000 | 0.313653 | 0.278689 | 20 | 1 | 14 |
| 2023-07 | 21 | -18.000000 | 0.228571 | 0.205128 | 19 | 1 | 15 |
| 2023-08 | 33 | -8.950000 | 0.646711 | 0.717647 | 14 | 1 | 6 |
| 2023-09 | 30 | -20.616667 | 0.253470 | 0.225806 | 14 | 0 | 9 |
| 2023-10 | 2 | -2.666667 | 0.000000 | 0.000000 | 2 | 0 | 1 |
| 2023-11 | 6 | 10.016667 | 3.276515 | 2.350000 | 6 | 1 | 0 |
| 2023-12 | 3 | -4.833333 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### A_OPT2023_T4_SB2_TP8

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 205, entry dates 113, entry months 12; SKIP 13, EXCLUDED 118, exclusion share 0.365325; conditional FLAT CLOSED 205.
Net -111.416667 R; PF R / price 0.405143 / 0.354844; expectancy -0.543496 R; win rate 0.248780; average winner / loser 1.487908 / -1.282877 R.
Conditional CLOSED-only DD 120.850000 R; largest winner share 0.144959; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 19 | -3.416667 | 0.758824 | 0.782609 | 18 | 1 | 11 |
| 2023-02 | 20 | -20.633333 | 0.057121 | 0.057143 | 18 | 3 | 13 |
| 2023-03 | 11 | -11.333333 | 0.028571 | 0.028571 | 22 | 2 | 18 |
| 2023-04 | 18 | -4.850000 | 0.617608 | 0.533333 | 18 | 2 | 15 |
| 2023-05 | 21 | -13.066667 | 0.367232 | 0.342466 | 21 | 1 | 16 |
| 2023-06 | 21 | -12.400000 | 0.313653 | 0.278689 | 20 | 1 | 14 |
| 2023-07 | 21 | -18.000000 | 0.228571 | 0.205128 | 19 | 1 | 15 |
| 2023-08 | 33 | -8.950000 | 0.646711 | 0.717647 | 14 | 1 | 6 |
| 2023-09 | 30 | -20.616667 | 0.253470 | 0.225806 | 14 | 0 | 9 |
| 2023-10 | 2 | -2.666667 | 0.000000 | 0.000000 | 2 | 0 | 1 |
| 2023-11 | 6 | 9.350000 | 3.125000 | 2.250000 | 6 | 1 | 0 |
| 2023-12 | 3 | -4.833333 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### A_OPT2023_T4_SB2_TP9

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 205, entry dates 113, entry months 12; SKIP 13, EXCLUDED 118, exclusion share 0.365325; conditional FLAT CLOSED 205.
Net -111.416667 R; PF R / price 0.405143 / 0.354844; expectancy -0.543496 R; win rate 0.248780; average winner / loser 1.487908 / -1.282877 R.
Conditional CLOSED-only DD 120.850000 R; largest winner share 0.144959; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 19 | -3.416667 | 0.758824 | 0.782609 | 18 | 1 | 11 |
| 2023-02 | 20 | -20.633333 | 0.057121 | 0.057143 | 18 | 3 | 13 |
| 2023-03 | 11 | -11.333333 | 0.028571 | 0.028571 | 22 | 2 | 18 |
| 2023-04 | 18 | -4.850000 | 0.617608 | 0.533333 | 18 | 2 | 15 |
| 2023-05 | 21 | -13.066667 | 0.367232 | 0.342466 | 21 | 1 | 16 |
| 2023-06 | 21 | -12.400000 | 0.313653 | 0.278689 | 20 | 1 | 14 |
| 2023-07 | 21 | -18.000000 | 0.228571 | 0.205128 | 19 | 1 | 15 |
| 2023-08 | 33 | -8.950000 | 0.646711 | 0.717647 | 14 | 1 | 6 |
| 2023-09 | 30 | -20.616667 | 0.253470 | 0.225806 | 14 | 0 | 9 |
| 2023-10 | 2 | -2.666667 | 0.000000 | 0.000000 | 2 | 0 | 1 |
| 2023-11 | 6 | 9.350000 | 3.125000 | 2.250000 | 6 | 1 | 0 |
| 2023-12 | 3 | -4.833333 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### A_OPT2023_T4_SB2_TP10

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 205, entry dates 113, entry months 12; SKIP 13, EXCLUDED 118, exclusion share 0.365325; conditional FLAT CLOSED 205.
Net -111.416667 R; PF R / price 0.405143 / 0.354844; expectancy -0.543496 R; win rate 0.248780; average winner / loser 1.487908 / -1.282877 R.
Conditional CLOSED-only DD 120.850000 R; largest winner share 0.144959; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 19 | -3.416667 | 0.758824 | 0.782609 | 18 | 1 | 11 |
| 2023-02 | 20 | -20.633333 | 0.057121 | 0.057143 | 18 | 3 | 13 |
| 2023-03 | 11 | -11.333333 | 0.028571 | 0.028571 | 22 | 2 | 18 |
| 2023-04 | 18 | -4.850000 | 0.617608 | 0.533333 | 18 | 2 | 15 |
| 2023-05 | 21 | -13.066667 | 0.367232 | 0.342466 | 21 | 1 | 16 |
| 2023-06 | 21 | -12.400000 | 0.313653 | 0.278689 | 20 | 1 | 14 |
| 2023-07 | 21 | -18.000000 | 0.228571 | 0.205128 | 19 | 1 | 15 |
| 2023-08 | 33 | -8.950000 | 0.646711 | 0.717647 | 14 | 1 | 6 |
| 2023-09 | 30 | -20.616667 | 0.253470 | 0.225806 | 14 | 0 | 9 |
| 2023-10 | 2 | -2.666667 | 0.000000 | 0.000000 | 2 | 0 | 1 |
| 2023-11 | 6 | 9.350000 | 3.125000 | 2.250000 | 6 | 1 | 0 |
| 2023-12 | 3 | -4.833333 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### A_OPT2023_T5_SB1_TP2

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 53, entry dates 43, entry months 10; SKIP 22, EXCLUDED 21, exclusion share 0.283784; conditional FLAT CLOSED 46.
Net -29.183333 R; PF R / price 0.416528 / 0.438538; expectancy -0.550629 R; win rate 0.207547; average winner / loser 1.893939 / -1.351802 R.
Conditional CLOSED-only DD 31.850000 R; largest winner share 0.160000; largest positive month share 0.666667. Positive / negative / zero months 2 / 8 / 2; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 6 | 1.000000 | 1.176471 | 1.176471 | 18 | 4 | 0 |
| 2023-02 | 6 | -4.000000 | 0.200000 | 0.200000 | 18 | 3 | 2 |
| 2023-03 | 1 | -1.000000 | 0.000000 | 0.000000 | 22 | 5 | 0 |
| 2023-04 | 7 | -0.916667 | 0.784314 | 1.000000 | 18 | 1 | 3 |
| 2023-05 | 8 | -5.666667 | 0.370370 | 0.370370 | 21 | 3 | 4 |
| 2023-06 | 3 | 0.500000 | 1.333333 | 1.000000 | 20 | 2 | 4 |
| 2023-07 | 7 | -3.733333 | 0.471698 | 0.416667 | 19 | 1 | 5 |
| 2023-08 | 8 | -9.533333 | 0.065359 | 0.064516 | 14 | 2 | 1 |
| 2023-09 | 6 | -4.166667 | 0.107143 | 0.142857 | 14 | 1 | 2 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 2 | 0 | 0 |
| 2023-11 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 6 | 0 | 0 |
| 2023-12 | 1 | -1.666667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### A_OPT2023_T5_SB1_TP3

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 53, entry dates 43, entry months 10; SKIP 22, EXCLUDED 21, exclusion share 0.283784; conditional FLAT CLOSED 46.
Net -27.850000 R; PF R / price 0.443186 / 0.465116; expectancy -0.525472 R; win rate 0.207547; average winner / loser 2.015152 / -1.351802 R.
Conditional CLOSED-only DD 33.850000 R; largest winner share 0.225564; largest positive month share 0.896552. Positive / negative / zero months 2 / 8 / 2; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 6 | 4.333333 | 1.764706 | 1.764706 | 18 | 4 | 0 |
| 2023-02 | 6 | -4.000000 | 0.200000 | 0.200000 | 18 | 3 | 2 |
| 2023-03 | 1 | -1.000000 | 0.000000 | 0.000000 | 22 | 5 | 0 |
| 2023-04 | 7 | -0.916667 | 0.784314 | 1.000000 | 18 | 1 | 3 |
| 2023-05 | 8 | -6.666667 | 0.259259 | 0.259259 | 21 | 3 | 4 |
| 2023-06 | 3 | 0.500000 | 1.333333 | 1.000000 | 20 | 2 | 4 |
| 2023-07 | 7 | -4.733333 | 0.330189 | 0.291667 | 19 | 1 | 5 |
| 2023-08 | 8 | -9.533333 | 0.065359 | 0.064516 | 14 | 2 | 1 |
| 2023-09 | 6 | -4.166667 | 0.107143 | 0.142857 | 14 | 1 | 2 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 2 | 0 | 0 |
| 2023-11 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 6 | 0 | 0 |
| 2023-12 | 1 | -1.666667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### A_OPT2023_T5_SB1_TP4

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors.
CLOSED 53, entry dates 43, entry months 10; SKIP 22, EXCLUDED 21, exclusion share 0.283784; conditional FLAT CLOSED 46.
Net -28.516667 R; PF R / price 0.429857 / 0.451827; expectancy -0.538050 R; win rate 0.207547; average winner / loser 1.954545 / -1.351802 R.
Conditional CLOSED-only DD 34.516667 R; largest winner share 0.310078; largest positive month share 0.880000. Positive / negative / zero months 2 / 8 / 2; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 6 | 3.666667 | 1.647059 | 1.647059 | 18 | 4 | 0 |
| 2023-02 | 6 | -4.000000 | 0.200000 | 0.200000 | 18 | 3 | 2 |
| 2023-03 | 1 | -1.000000 | 0.000000 | 0.000000 | 22 | 5 | 0 |
| 2023-04 | 7 | -0.916667 | 0.784314 | 1.000000 | 18 | 1 | 3 |
| 2023-05 | 8 | -6.666667 | 0.259259 | 0.259259 | 21 | 3 | 4 |
| 2023-06 | 3 | 0.500000 | 1.333333 | 1.000000 | 20 | 2 | 4 |
| 2023-07 | 7 | -4.733333 | 0.330189 | 0.291667 | 19 | 1 | 5 |
| 2023-08 | 8 | -9.533333 | 0.065359 | 0.064516 | 14 | 2 | 1 |
| 2023-09 | 6 | -4.166667 | 0.107143 | 0.142857 | 14 | 1 | 2 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 2 | 0 | 0 |
| 2023-11 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 6 | 0 | 0 |
| 2023-12 | 1 | -1.666667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### A_OPT2023_T5_SB1_TP5

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 53, entry dates 43, entry months 10; SKIP 22, EXCLUDED 21, exclusion share 0.283784; conditional FLAT CLOSED 46.
Net -31.516667 R; PF R / price 0.369877 / 0.392027; expectancy -0.594654 R; win rate 0.207547; average winner / loser 1.681818 / -1.351802 R.
Conditional CLOSED-only DD 34.516667 R; largest winner share 0.198198; largest positive month share 0.571429. Positive / negative / zero months 2 / 8 / 2; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 6 | 0.666667 | 1.117647 | 1.117647 | 18 | 4 | 0 |
| 2023-02 | 6 | -4.000000 | 0.200000 | 0.200000 | 18 | 3 | 2 |
| 2023-03 | 1 | -1.000000 | 0.000000 | 0.000000 | 22 | 5 | 0 |
| 2023-04 | 7 | -0.916667 | 0.784314 | 1.000000 | 18 | 1 | 3 |
| 2023-05 | 8 | -6.666667 | 0.259259 | 0.259259 | 21 | 3 | 4 |
| 2023-06 | 3 | 0.500000 | 1.333333 | 1.000000 | 20 | 2 | 4 |
| 2023-07 | 7 | -4.733333 | 0.330189 | 0.291667 | 19 | 1 | 5 |
| 2023-08 | 8 | -9.533333 | 0.065359 | 0.064516 | 14 | 2 | 1 |
| 2023-09 | 6 | -4.166667 | 0.107143 | 0.142857 | 14 | 1 | 2 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 2 | 0 | 0 |
| 2023-11 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 6 | 0 | 0 |
| 2023-12 | 1 | -1.666667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### A_OPT2023_T5_SB1_TP6

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 53, entry dates 43, entry months 10; SKIP 22, EXCLUDED 21, exclusion share 0.283784; conditional FLAT CLOSED 46.
Net -31.516667 R; PF R / price 0.369877 / 0.392027; expectancy -0.594654 R; win rate 0.207547; average winner / loser 1.681818 / -1.351802 R.
Conditional CLOSED-only DD 34.516667 R; largest winner share 0.198198; largest positive month share 0.571429. Positive / negative / zero months 2 / 8 / 2; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 6 | 0.666667 | 1.117647 | 1.117647 | 18 | 4 | 0 |
| 2023-02 | 6 | -4.000000 | 0.200000 | 0.200000 | 18 | 3 | 2 |
| 2023-03 | 1 | -1.000000 | 0.000000 | 0.000000 | 22 | 5 | 0 |
| 2023-04 | 7 | -0.916667 | 0.784314 | 1.000000 | 18 | 1 | 3 |
| 2023-05 | 8 | -6.666667 | 0.259259 | 0.259259 | 21 | 3 | 4 |
| 2023-06 | 3 | 0.500000 | 1.333333 | 1.000000 | 20 | 2 | 4 |
| 2023-07 | 7 | -4.733333 | 0.330189 | 0.291667 | 19 | 1 | 5 |
| 2023-08 | 8 | -9.533333 | 0.065359 | 0.064516 | 14 | 2 | 1 |
| 2023-09 | 6 | -4.166667 | 0.107143 | 0.142857 | 14 | 1 | 2 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 2 | 0 | 0 |
| 2023-11 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 6 | 0 | 0 |
| 2023-12 | 1 | -1.666667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### A_OPT2023_T5_SB1_TP7

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 53, entry dates 43, entry months 10; SKIP 22, EXCLUDED 21, exclusion share 0.283784; conditional FLAT CLOSED 46.
Net -31.516667 R; PF R / price 0.369877 / 0.392027; expectancy -0.594654 R; win rate 0.207547; average winner / loser 1.681818 / -1.351802 R.
Conditional CLOSED-only DD 34.516667 R; largest winner share 0.198198; largest positive month share 0.571429. Positive / negative / zero months 2 / 8 / 2; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 6 | 0.666667 | 1.117647 | 1.117647 | 18 | 4 | 0 |
| 2023-02 | 6 | -4.000000 | 0.200000 | 0.200000 | 18 | 3 | 2 |
| 2023-03 | 1 | -1.000000 | 0.000000 | 0.000000 | 22 | 5 | 0 |
| 2023-04 | 7 | -0.916667 | 0.784314 | 1.000000 | 18 | 1 | 3 |
| 2023-05 | 8 | -6.666667 | 0.259259 | 0.259259 | 21 | 3 | 4 |
| 2023-06 | 3 | 0.500000 | 1.333333 | 1.000000 | 20 | 2 | 4 |
| 2023-07 | 7 | -4.733333 | 0.330189 | 0.291667 | 19 | 1 | 5 |
| 2023-08 | 8 | -9.533333 | 0.065359 | 0.064516 | 14 | 2 | 1 |
| 2023-09 | 6 | -4.166667 | 0.107143 | 0.142857 | 14 | 1 | 2 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 2 | 0 | 0 |
| 2023-11 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 6 | 0 | 0 |
| 2023-12 | 1 | -1.666667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### A_OPT2023_T5_SB1_TP8

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 53, entry dates 43, entry months 10; SKIP 22, EXCLUDED 21, exclusion share 0.283784; conditional FLAT CLOSED 46.
Net -31.516667 R; PF R / price 0.369877 / 0.392027; expectancy -0.594654 R; win rate 0.207547; average winner / loser 1.681818 / -1.351802 R.
Conditional CLOSED-only DD 34.516667 R; largest winner share 0.198198; largest positive month share 0.571429. Positive / negative / zero months 2 / 8 / 2; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 6 | 0.666667 | 1.117647 | 1.117647 | 18 | 4 | 0 |
| 2023-02 | 6 | -4.000000 | 0.200000 | 0.200000 | 18 | 3 | 2 |
| 2023-03 | 1 | -1.000000 | 0.000000 | 0.000000 | 22 | 5 | 0 |
| 2023-04 | 7 | -0.916667 | 0.784314 | 1.000000 | 18 | 1 | 3 |
| 2023-05 | 8 | -6.666667 | 0.259259 | 0.259259 | 21 | 3 | 4 |
| 2023-06 | 3 | 0.500000 | 1.333333 | 1.000000 | 20 | 2 | 4 |
| 2023-07 | 7 | -4.733333 | 0.330189 | 0.291667 | 19 | 1 | 5 |
| 2023-08 | 8 | -9.533333 | 0.065359 | 0.064516 | 14 | 2 | 1 |
| 2023-09 | 6 | -4.166667 | 0.107143 | 0.142857 | 14 | 1 | 2 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 2 | 0 | 0 |
| 2023-11 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 6 | 0 | 0 |
| 2023-12 | 1 | -1.666667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### A_OPT2023_T5_SB1_TP9

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 53, entry dates 43, entry months 10; SKIP 22, EXCLUDED 21, exclusion share 0.283784; conditional FLAT CLOSED 46.
Net -31.516667 R; PF R / price 0.369877 / 0.392027; expectancy -0.594654 R; win rate 0.207547; average winner / loser 1.681818 / -1.351802 R.
Conditional CLOSED-only DD 34.516667 R; largest winner share 0.198198; largest positive month share 0.571429. Positive / negative / zero months 2 / 8 / 2; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 6 | 0.666667 | 1.117647 | 1.117647 | 18 | 4 | 0 |
| 2023-02 | 6 | -4.000000 | 0.200000 | 0.200000 | 18 | 3 | 2 |
| 2023-03 | 1 | -1.000000 | 0.000000 | 0.000000 | 22 | 5 | 0 |
| 2023-04 | 7 | -0.916667 | 0.784314 | 1.000000 | 18 | 1 | 3 |
| 2023-05 | 8 | -6.666667 | 0.259259 | 0.259259 | 21 | 3 | 4 |
| 2023-06 | 3 | 0.500000 | 1.333333 | 1.000000 | 20 | 2 | 4 |
| 2023-07 | 7 | -4.733333 | 0.330189 | 0.291667 | 19 | 1 | 5 |
| 2023-08 | 8 | -9.533333 | 0.065359 | 0.064516 | 14 | 2 | 1 |
| 2023-09 | 6 | -4.166667 | 0.107143 | 0.142857 | 14 | 1 | 2 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 2 | 0 | 0 |
| 2023-11 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 6 | 0 | 0 |
| 2023-12 | 1 | -1.666667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### A_OPT2023_T5_SB1_TP10

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 53, entry dates 43, entry months 10; SKIP 22, EXCLUDED 21, exclusion share 0.283784; conditional FLAT CLOSED 46.
Net -31.516667 R; PF R / price 0.369877 / 0.392027; expectancy -0.594654 R; win rate 0.207547; average winner / loser 1.681818 / -1.351802 R.
Conditional CLOSED-only DD 34.516667 R; largest winner share 0.198198; largest positive month share 0.571429. Positive / negative / zero months 2 / 8 / 2; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 6 | 0.666667 | 1.117647 | 1.117647 | 18 | 4 | 0 |
| 2023-02 | 6 | -4.000000 | 0.200000 | 0.200000 | 18 | 3 | 2 |
| 2023-03 | 1 | -1.000000 | 0.000000 | 0.000000 | 22 | 5 | 0 |
| 2023-04 | 7 | -0.916667 | 0.784314 | 1.000000 | 18 | 1 | 3 |
| 2023-05 | 8 | -6.666667 | 0.259259 | 0.259259 | 21 | 3 | 4 |
| 2023-06 | 3 | 0.500000 | 1.333333 | 1.000000 | 20 | 2 | 4 |
| 2023-07 | 7 | -4.733333 | 0.330189 | 0.291667 | 19 | 1 | 5 |
| 2023-08 | 8 | -9.533333 | 0.065359 | 0.064516 | 14 | 2 | 1 |
| 2023-09 | 6 | -4.166667 | 0.107143 | 0.142857 | 14 | 1 | 2 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 2 | 0 | 0 |
| 2023-11 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 6 | 0 | 0 |
| 2023-12 | 1 | -1.666667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### A_OPT2023_T5_SB2_TP2

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors.
CLOSED 121, entry dates 77, entry months 11; SKIP 10, EXCLUDED 88, exclusion share 0.421053; conditional FLAT CLOSED 117.
Net -53.866667 R; PF R / price 0.467633 / 0.419180; expectancy -0.445179 R; win rate 0.256198; average winner / loser 1.526344 / -1.249177 R.
Conditional CLOSED-only DD 64.033333 R; largest winner share 0.070447; largest positive month share 0.425926. Positive / negative / zero months 3 / 8 / 1; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 8 | 3.833333 | 1.920000 | 1.687500 | 18 | 1 | 8 |
| 2023-02 | 12 | -6.583333 | 0.307018 | 0.300000 | 18 | 1 | 11 |
| 2023-03 | 8 | -6.333333 | 0.050000 | 0.050000 | 22 | 3 | 13 |
| 2023-04 | 13 | -1.716667 | 0.823024 | 0.878788 | 18 | 1 | 9 |
| 2023-05 | 17 | -10.500000 | 0.402844 | 0.410714 | 21 | 1 | 12 |
| 2023-06 | 15 | -11.233333 | 0.161692 | 0.181818 | 20 | 2 | 12 |
| 2023-07 | 14 | -8.166667 | 0.363636 | 0.369565 | 19 | 0 | 10 |
| 2023-08 | 19 | -11.666667 | 0.292929 | 0.272727 | 14 | 1 | 5 |
| 2023-09 | 12 | -6.666667 | 0.285714 | 0.258065 | 14 | 0 | 8 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 2 | 0 | 0 |
| 2023-11 | 1 | 3.333333 | NOT_AVAILABLE | NOT_AVAILABLE | 6 | 0 | 0 |
| 2023-12 | 2 | 1.833333 | 2.222222 | 1.666667 | 0 | 0 | 0 |

### A_OPT2023_T5_SB2_TP3

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors.
CLOSED 121, entry dates 77, entry months 11; SKIP 10, EXCLUDED 88, exclusion share 0.421053; conditional FLAT CLOSED 117.
Net -51.616667 R; PF R / price 0.489870 / 0.424005; expectancy -0.426584 R; win rate 0.256198; average winner / loser 1.598925 / -1.249177 R.
Conditional CLOSED-only DD 66.950000 R; largest winner share 0.100874; largest positive month share 0.494118. Positive / negative / zero months 3 / 8 / 1; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 8 | 7.000000 | 2.680000 | 2.375000 | 18 | 1 | 8 |
| 2023-02 | 12 | -6.583333 | 0.307018 | 0.300000 | 18 | 1 | 11 |
| 2023-03 | 8 | -6.333333 | 0.050000 | 0.050000 | 22 | 3 | 13 |
| 2023-04 | 13 | -3.383333 | 0.651203 | 0.727273 | 18 | 1 | 9 |
| 2023-05 | 17 | -10.833333 | 0.383886 | 0.392857 | 21 | 1 | 12 |
| 2023-06 | 15 | -11.233333 | 0.161692 | 0.181818 | 20 | 2 | 12 |
| 2023-07 | 14 | -9.416667 | 0.266234 | 0.260870 | 19 | 0 | 10 |
| 2023-08 | 19 | -11.333333 | 0.313131 | 0.290909 | 14 | 1 | 5 |
| 2023-09 | 12 | -6.666667 | 0.285714 | 0.258065 | 14 | 0 | 8 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 2 | 0 | 0 |
| 2023-11 | 1 | 5.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 6 | 0 | 0 |
| 2023-12 | 2 | 2.166667 | 2.444444 | 1.833333 | 0 | 0 | 0 |

### A_OPT2023_T5_SB2_TP4

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors.
CLOSED 121, entry dates 77, entry months 11; SKIP 10, EXCLUDED 88, exclusion share 0.421053; conditional FLAT CLOSED 117.
Net -50.783333 R; PF R / price 0.498106 / 0.410434; expectancy -0.419697 R; win rate 0.256198; average winner / loser 1.625806 / -1.249177 R.
Conditional CLOSED-only DD 66.950000 R; largest winner share 0.132275; largest positive month share 0.444444. Positive / negative / zero months 3 / 8 / 1; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 8 | 6.166667 | 2.480000 | 2.062500 | 18 | 1 | 8 |
| 2023-02 | 12 | -6.583333 | 0.307018 | 0.300000 | 18 | 1 | 11 |
| 2023-03 | 8 | -6.333333 | 0.050000 | 0.050000 | 22 | 3 | 13 |
| 2023-04 | 13 | -3.383333 | 0.651203 | 0.727273 | 18 | 1 | 9 |
| 2023-05 | 17 | -10.833333 | 0.383886 | 0.392857 | 21 | 1 | 12 |
| 2023-06 | 15 | -11.233333 | 0.161692 | 0.181818 | 20 | 2 | 12 |
| 2023-07 | 14 | -9.416667 | 0.266234 | 0.260870 | 19 | 0 | 10 |
| 2023-08 | 19 | -11.333333 | 0.313131 | 0.290909 | 14 | 1 | 5 |
| 2023-09 | 12 | -6.666667 | 0.285714 | 0.258065 | 14 | 0 | 8 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 2 | 0 | 0 |
| 2023-11 | 1 | 6.666667 | NOT_AVAILABLE | NOT_AVAILABLE | 6 | 0 | 0 |
| 2023-12 | 2 | 2.166667 | 2.444444 | 1.833333 | 0 | 0 | 0 |

### A_OPT2023_T5_SB2_TP5

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 121, entry dates 77, entry months 11; SKIP 10, EXCLUDED 88, exclusion share 0.421053; conditional FLAT CLOSED 117.
Net -50.450000 R; PF R / price 0.501400 / 0.399879; expectancy -0.416942 R; win rate 0.256198; average winner / loser 1.636559 / -1.249177 R.
Conditional CLOSED-only DD 66.950000 R; largest winner share 0.164258; largest positive month share 0.543478. Positive / negative / zero months 3 / 8 / 1; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 8 | 4.833333 | 2.160000 | 1.812500 | 18 | 1 | 8 |
| 2023-02 | 12 | -6.583333 | 0.307018 | 0.300000 | 18 | 1 | 11 |
| 2023-03 | 8 | -6.333333 | 0.050000 | 0.050000 | 22 | 3 | 13 |
| 2023-04 | 13 | -3.383333 | 0.651203 | 0.727273 | 18 | 1 | 9 |
| 2023-05 | 17 | -10.833333 | 0.383886 | 0.392857 | 21 | 1 | 12 |
| 2023-06 | 15 | -11.233333 | 0.161692 | 0.181818 | 20 | 2 | 12 |
| 2023-07 | 14 | -9.416667 | 0.266234 | 0.260870 | 19 | 0 | 10 |
| 2023-08 | 19 | -11.333333 | 0.313131 | 0.290909 | 14 | 1 | 5 |
| 2023-09 | 12 | -6.666667 | 0.285714 | 0.258065 | 14 | 0 | 8 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 2 | 0 | 0 |
| 2023-11 | 1 | 8.333333 | NOT_AVAILABLE | NOT_AVAILABLE | 6 | 0 | 0 |
| 2023-12 | 2 | 2.166667 | 2.444444 | 1.833333 | 0 | 0 | 0 |

### A_OPT2023_T5_SB2_TP6

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 121, entry dates 77, entry months 11; SKIP 10, EXCLUDED 88, exclusion share 0.421053; conditional FLAT CLOSED 117.
Net -48.783333 R; PF R / price 0.517872 / 0.401387; expectancy -0.403168 R; win rate 0.256198; average winner / loser 1.690323 / -1.249177 R.
Conditional CLOSED-only DD 66.950000 R; largest winner share 0.190840; largest positive month share 0.588235. Positive / negative / zero months 3 / 8 / 1; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 8 | 4.833333 | 2.160000 | 1.812500 | 18 | 1 | 8 |
| 2023-02 | 12 | -6.583333 | 0.307018 | 0.300000 | 18 | 1 | 11 |
| 2023-03 | 8 | -6.333333 | 0.050000 | 0.050000 | 22 | 3 | 13 |
| 2023-04 | 13 | -3.383333 | 0.651203 | 0.727273 | 18 | 1 | 9 |
| 2023-05 | 17 | -10.833333 | 0.383886 | 0.392857 | 21 | 1 | 12 |
| 2023-06 | 15 | -11.233333 | 0.161692 | 0.181818 | 20 | 2 | 12 |
| 2023-07 | 14 | -9.416667 | 0.266234 | 0.260870 | 19 | 0 | 10 |
| 2023-08 | 19 | -11.333333 | 0.313131 | 0.290909 | 14 | 1 | 5 |
| 2023-09 | 12 | -6.666667 | 0.285714 | 0.258065 | 14 | 0 | 8 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 2 | 0 | 0 |
| 2023-11 | 1 | 10.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 6 | 0 | 0 |
| 2023-12 | 2 | 2.166667 | 2.444444 | 1.833333 | 0 | 0 | 0 |

### A_OPT2023_T5_SB2_TP7

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 121, entry dates 77, entry months 11; SKIP 10, EXCLUDED 88, exclusion share 0.421053; conditional FLAT CLOSED 117.
Net -47.116667 R; PF R / price 0.534344 / 0.402895; expectancy -0.389394 R; win rate 0.256198; average winner / loser 1.744086 / -1.249177 R.
Conditional CLOSED-only DD 66.950000 R; largest winner share 0.215783; largest positive month share 0.625000. Positive / negative / zero months 3 / 8 / 1; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 8 | 4.833333 | 2.160000 | 1.812500 | 18 | 1 | 8 |
| 2023-02 | 12 | -6.583333 | 0.307018 | 0.300000 | 18 | 1 | 11 |
| 2023-03 | 8 | -6.333333 | 0.050000 | 0.050000 | 22 | 3 | 13 |
| 2023-04 | 13 | -3.383333 | 0.651203 | 0.727273 | 18 | 1 | 9 |
| 2023-05 | 17 | -10.833333 | 0.383886 | 0.392857 | 21 | 1 | 12 |
| 2023-06 | 15 | -11.233333 | 0.161692 | 0.181818 | 20 | 2 | 12 |
| 2023-07 | 14 | -9.416667 | 0.266234 | 0.260870 | 19 | 0 | 10 |
| 2023-08 | 19 | -11.333333 | 0.313131 | 0.290909 | 14 | 1 | 5 |
| 2023-09 | 12 | -6.666667 | 0.285714 | 0.258065 | 14 | 0 | 8 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 2 | 0 | 0 |
| 2023-11 | 1 | 11.666667 | NOT_AVAILABLE | NOT_AVAILABLE | 6 | 0 | 0 |
| 2023-12 | 2 | 2.166667 | 2.444444 | 1.833333 | 0 | 0 | 0 |

### A_OPT2023_T5_SB2_TP8

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 121, entry dates 77, entry months 11; SKIP 10, EXCLUDED 88, exclusion share 0.421053; conditional FLAT CLOSED 117.
Net -47.783333 R; PF R / price 0.527755 / 0.402292; expectancy -0.394904 R; win rate 0.256198; average winner / loser 1.722581 / -1.249177 R.
Conditional CLOSED-only DD 66.950000 R; largest winner share 0.205993; largest positive month share 0.611111. Positive / negative / zero months 3 / 8 / 1; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 8 | 4.833333 | 2.160000 | 1.812500 | 18 | 1 | 8 |
| 2023-02 | 12 | -6.583333 | 0.307018 | 0.300000 | 18 | 1 | 11 |
| 2023-03 | 8 | -6.333333 | 0.050000 | 0.050000 | 22 | 3 | 13 |
| 2023-04 | 13 | -3.383333 | 0.651203 | 0.727273 | 18 | 1 | 9 |
| 2023-05 | 17 | -10.833333 | 0.383886 | 0.392857 | 21 | 1 | 12 |
| 2023-06 | 15 | -11.233333 | 0.161692 | 0.181818 | 20 | 2 | 12 |
| 2023-07 | 14 | -9.416667 | 0.266234 | 0.260870 | 19 | 0 | 10 |
| 2023-08 | 19 | -11.333333 | 0.313131 | 0.290909 | 14 | 1 | 5 |
| 2023-09 | 12 | -6.666667 | 0.285714 | 0.258065 | 14 | 0 | 8 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 2 | 0 | 0 |
| 2023-11 | 1 | 11.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 6 | 0 | 0 |
| 2023-12 | 2 | 2.166667 | 2.444444 | 1.833333 | 0 | 0 | 0 |

### A_OPT2023_T5_SB2_TP9

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 121, entry dates 77, entry months 11; SKIP 10, EXCLUDED 88, exclusion share 0.421053; conditional FLAT CLOSED 117.
Net -47.783333 R; PF R / price 0.527755 / 0.402292; expectancy -0.394904 R; win rate 0.256198; average winner / loser 1.722581 / -1.249177 R.
Conditional CLOSED-only DD 66.950000 R; largest winner share 0.205993; largest positive month share 0.611111. Positive / negative / zero months 3 / 8 / 1; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 8 | 4.833333 | 2.160000 | 1.812500 | 18 | 1 | 8 |
| 2023-02 | 12 | -6.583333 | 0.307018 | 0.300000 | 18 | 1 | 11 |
| 2023-03 | 8 | -6.333333 | 0.050000 | 0.050000 | 22 | 3 | 13 |
| 2023-04 | 13 | -3.383333 | 0.651203 | 0.727273 | 18 | 1 | 9 |
| 2023-05 | 17 | -10.833333 | 0.383886 | 0.392857 | 21 | 1 | 12 |
| 2023-06 | 15 | -11.233333 | 0.161692 | 0.181818 | 20 | 2 | 12 |
| 2023-07 | 14 | -9.416667 | 0.266234 | 0.260870 | 19 | 0 | 10 |
| 2023-08 | 19 | -11.333333 | 0.313131 | 0.290909 | 14 | 1 | 5 |
| 2023-09 | 12 | -6.666667 | 0.285714 | 0.258065 | 14 | 0 | 8 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 2 | 0 | 0 |
| 2023-11 | 1 | 11.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 6 | 0 | 0 |
| 2023-12 | 2 | 2.166667 | 2.444444 | 1.833333 | 0 | 0 | 0 |

### A_OPT2023_T5_SB2_TP10

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 121, entry dates 77, entry months 11; SKIP 10, EXCLUDED 88, exclusion share 0.421053; conditional FLAT CLOSED 117.
Net -47.783333 R; PF R / price 0.527755 / 0.402292; expectancy -0.394904 R; win rate 0.256198; average winner / loser 1.722581 / -1.249177 R.
Conditional CLOSED-only DD 66.950000 R; largest winner share 0.205993; largest positive month share 0.611111. Positive / negative / zero months 3 / 8 / 1; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 8 | 4.833333 | 2.160000 | 1.812500 | 18 | 1 | 8 |
| 2023-02 | 12 | -6.583333 | 0.307018 | 0.300000 | 18 | 1 | 11 |
| 2023-03 | 8 | -6.333333 | 0.050000 | 0.050000 | 22 | 3 | 13 |
| 2023-04 | 13 | -3.383333 | 0.651203 | 0.727273 | 18 | 1 | 9 |
| 2023-05 | 17 | -10.833333 | 0.383886 | 0.392857 | 21 | 1 | 12 |
| 2023-06 | 15 | -11.233333 | 0.161692 | 0.181818 | 20 | 2 | 12 |
| 2023-07 | 14 | -9.416667 | 0.266234 | 0.260870 | 19 | 0 | 10 |
| 2023-08 | 19 | -11.333333 | 0.313131 | 0.290909 | 14 | 1 | 5 |
| 2023-09 | 12 | -6.666667 | 0.285714 | 0.258065 | 14 | 0 | 8 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 2 | 0 | 0 |
| 2023-11 | 1 | 11.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 6 | 0 | 0 |
| 2023-12 | 2 | 2.166667 | 2.444444 | 1.833333 | 0 | 0 | 0 |

## Evidence limits

Missing entry Open produces no entry, C1 or P&L; no later substitution. Excluded positions retain known entry evidence and unknown outcomes; same-day entries are blocked. Counts and fractions describe possible selection bias, especially CNY. Incomplete coverage also exists on days without an exclusion. Closed-only DD follows resolved trade order and is conditional.
No GLDRUBF/IMOEXF evaluation, 2024+ reads, Robustness, WF, TRUE OOS, LIVE, portfolio sizing, merge or auto-merge. Frozen Baselines, Master Registry, TradingSystemLab and Draft #472 remain unchanged. STOP after one Draft PR.
