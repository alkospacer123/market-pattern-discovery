# Optimization B High/Low Cluster — bounded frozen 2023 grid

**NO QUALIFYING OPTIMIZATION CANDIDATE**

Base main: `0aa3851b754705145b3c64af9781e93f553e4a09`. Pre-P&L freeze: `a7d894ba934ff89f8188e2c3574fdb86b9f2b922`.
315 fixed configurations; 270 USD +315 CNY =585 evaluations. USD N10 excluded before P&L. Complete exhaustive search; no added variants, direction selection, or early stop.
All results below are profit after model C1 costs, not actual broker commissions. Prices are instrument quotation units and never pooled. CLOSED-only economics are conditional on coverage and assumed FLAT after excluded positions. No complete annual PF/return, continuous equity or broker Max DD is established.
Take distance = R × (gross initial risk + planned 2 entry ticks) + planned 2 entry ticks, rounded outward. Net_R uses gross initial risk; planned net/net R and realized net/net R have distinct ledger fields. Actual C1 uses dated entry and exit ticks.
First formed N-bar High/Low window consumes the entire greedy envelope episode, including CLOSE_AT_BOUNDARY; width bounds continuation and termination of the whole episode; completed candles only; immediate next Open admission, structural Stop unchanged, entry-bar Take disabled, Stop-first, 120-minute/session-flat deadline. CNY tick .01 before 2023-09-27 19:00 MSK, .001 thereafter.
Sample requires 100 CLOSED / 40 entry dates / 6 entry months. Both PF ≥2, expectancy >0, ≥9 positive exit months, conditional DD ≤20R, largest winner ≤25%, largest positive month ≤50%; two adjacent neighbors need 100 CLOSED, positive expectancy, PF R ≥1.5. Local 2023 stability diagnosis is not Robustness.
All numerical audit comparisons are exact; no zero-sign tolerance. PF without losses is NOT_AVAILABLE; zero/no-trade months are not positive. Independent algorithm audit does not replace external Draft PR review.

| Instrument | Evaluated | Sample | Both PF | Months ≥9 | Base criteria | All criteria |
|---|---|---|---|---|---|---|
| USDRUBF | 270 | 144 | 0 | 0 | 0 | 0 |
| CNYRUBF | 315 | 315 | 0 | 0 | 0 | 0 |

Reproduce from a clean checkout with the pinned read-only source:
```bash
python -m IntradayLab.optimization_b_high_low_cluster_2023_v1.validate --data-root /workspace/market-pattern-data --output IntradayLab/work/fresh_optimization_b_validation
```
The validation command runs canonical + two full repeats and the independent auditor, checks freeze dependencies and every preexisting repository path, and refuses existing outputs. Source OHLC is not copied into this repository.

All candidate criteria and reasons: all_candidates.csv. Complete exact monthly and directional metrics: monthly_results.csv and direction_results.csv. Full events, CLOSED trades, SKIP, EXCLUDED, rejected/nonfill and coverage: evaluations/<ID>/<instrument>/. Selection ranks contain only fully qualified configurations.
Independent legacy comparator for N4/N7/N10 W3/T2/SB1/TP3 validates frozen B paths; USD N10 is existing-ledger reference only; comparator_gap_policy.csv explains differences from V2 entry skipping and consequent occupancy. This is an audit of the historical comparator, not an added Optimization variant.

## USDRUBF

NO QUALIFYING OPTIMIZATION CANDIDATE

### B_OPT2023_N4_W2_T2_SB1_TP2

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 454, entry dates 199, entry months 12; SKIP 3, EXCLUDED 6, exclusion share 0.013043; conditional FLAT CLOSED 443.
Net -239.550000 R; PF R / price 0.532007 / 0.530695; expectancy -0.527643 R; win rate 0.233480; average winner / loser 2.569025 / -1.483671 R.
Conditional CLOSED-only DD 242.383333 R; largest winner share 0.012241; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 43 | -26.416667 | 0.465970 | 0.455000 | 5 | 0 | 2 |
| 2023-02 | 32 | -20.250000 | 0.445964 | 0.443662 | 4 | 2 | 0 |
| 2023-03 | 52 | -38.683333 | 0.377414 | 0.417391 | 3 | 0 | 2 |
| 2023-04 | 40 | -9.116667 | 0.775359 | 0.771812 | 5 | 1 | 0 |
| 2023-05 | 32 | -11.583333 | 0.642306 | 0.674603 | 3 | 0 | 1 |
| 2023-06 | 32 | 2.066667 | 1.068584 | 1.049180 | 4 | 0 | 1 |
| 2023-07 | 29 | -20.183333 | 0.418348 | 0.392857 | 1 | 0 | 0 |
| 2023-08 | 20 | -13.616667 | 0.444973 | 0.393617 | 2 | 0 | 0 |
| 2023-09 | 41 | -18.666667 | 0.600571 | 0.601124 | 2 | 0 | 0 |
| 2023-10 | 36 | -15.450000 | 0.610831 | 0.529032 | 0 | 0 | 0 |
| 2023-11 | 56 | -31.816667 | 0.496970 | 0.525424 | 1 | 0 | 0 |
| 2023-12 | 41 | -35.833333 | 0.306899 | 0.316583 | 0 | 0 | 0 |

### B_OPT2023_N4_W2_T2_SB1_TP3

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 438, entry dates 197, entry months 12; SKIP 3, EXCLUDED 8, exclusion share 0.017937; conditional FLAT CLOSED 427.
Net -263.716667 R; PF R / price 0.492788 / 0.509834; expectancy -0.602093 R; win rate 0.187215; average winner / loser 3.124593 / -1.481292 R.
Conditional CLOSED-only DD 270.950000 R; largest winner share 0.019515; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 12 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 42 | -31.816667 | 0.363242 | 0.375000 | 5 | 0 | 2 |
| 2023-02 | 32 | -19.633333 | 0.462836 | 0.429577 | 4 | 2 | 0 |
| 2023-03 | 48 | -27.683333 | 0.518271 | 0.553991 | 3 | 0 | 3 |
| 2023-04 | 38 | -7.050000 | 0.813245 | 0.848921 | 5 | 1 | 0 |
| 2023-05 | 32 | -9.216667 | 0.729320 | 0.816794 | 3 | 0 | 1 |
| 2023-06 | 31 | -5.150000 | 0.845345 | 0.827068 | 4 | 0 | 2 |
| 2023-07 | 29 | -26.216667 | 0.305825 | 0.276316 | 1 | 0 | 0 |
| 2023-08 | 20 | -15.450000 | 0.370245 | 0.319149 | 2 | 0 | 0 |
| 2023-09 | 39 | -39.100000 | 0.259937 | 0.294416 | 2 | 0 | 0 |
| 2023-10 | 33 | -20.316667 | 0.495029 | 0.456954 | 0 | 0 | 0 |
| 2023-11 | 55 | -30.016667 | 0.537612 | 0.601660 | 1 | 0 | 0 |
| 2023-12 | 39 | -32.066667 | 0.365854 | 0.410526 | 0 | 0 | 0 |

### B_OPT2023_N4_W2_T2_SB1_TP4

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 435, entry dates 197, entry months 12; SKIP 3, EXCLUDED 8, exclusion share 0.018059; conditional FLAT CLOSED 424.
Net -257.983333 R; PF R / price 0.507227 / 0.513514; expectancy -0.593065 R; win rate 0.172414; average winner / loser 3.540667 / -1.478908 R.
Conditional CLOSED-only DD 267.616667 R; largest winner share 0.025105; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 41 | -29.700000 | 0.405604 | 0.410000 | 5 | 0 | 2 |
| 2023-02 | 32 | -16.466667 | 0.549476 | 0.507042 | 4 | 2 | 0 |
| 2023-03 | 47 | -28.150000 | 0.510151 | 0.530516 | 3 | 0 | 3 |
| 2023-04 | 38 | -15.433333 | 0.606794 | 0.586207 | 5 | 1 | 0 |
| 2023-05 | 32 | -1.850000 | 0.945668 | 1.061069 | 3 | 0 | 1 |
| 2023-06 | 31 | 2.483333 | 1.074575 | 1.052632 | 4 | 0 | 2 |
| 2023-07 | 29 | -30.550000 | 0.221986 | 0.183544 | 1 | 0 | 0 |
| 2023-08 | 20 | -13.783333 | 0.438179 | 0.372340 | 2 | 0 | 0 |
| 2023-09 | 39 | -39.033333 | 0.261199 | 0.279188 | 2 | 0 | 0 |
| 2023-10 | 33 | -23.150000 | 0.445288 | 0.394904 | 0 | 0 | 0 |
| 2023-11 | 54 | -22.383333 | 0.647043 | 0.706383 | 1 | 0 | 0 |
| 2023-12 | 39 | -39.966667 | 0.218893 | 0.248705 | 0 | 0 | 0 |

### B_OPT2023_N4_W2_T2_SB1_TP5

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 431, entry dates 196, entry months 12; SKIP 3, EXCLUDED 8, exclusion share 0.018223; conditional FLAT CLOSED 420.
Net -274.400000 R; PF R / price 0.479449 / 0.485543; expectancy -0.636659 R; win rate 0.160093; average winner / loser 3.662802 / -1.480712 R.
Conditional CLOSED-only DD 287.033333 R; largest winner share 0.032973; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 12 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 41 | -27.866667 | 0.442295 | 0.445000 | 5 | 0 | 2 |
| 2023-02 | 32 | -13.300000 | 0.636115 | 0.584507 | 4 | 2 | 0 |
| 2023-03 | 47 | -27.533333 | 0.520882 | 0.530516 | 3 | 0 | 3 |
| 2023-04 | 38 | -16.016667 | 0.591932 | 0.558621 | 5 | 1 | 0 |
| 2023-05 | 30 | -6.150000 | 0.811639 | 0.879032 | 3 | 0 | 1 |
| 2023-06 | 31 | -2.216667 | 0.936606 | 1.000000 | 4 | 0 | 2 |
| 2023-07 | 29 | -28.883333 | 0.264431 | 0.215190 | 1 | 0 | 0 |
| 2023-08 | 19 | -23.616667 | 0.098601 | 0.090909 | 2 | 0 | 0 |
| 2023-09 | 39 | -45.966667 | 0.156575 | 0.207921 | 2 | 0 | 0 |
| 2023-10 | 32 | -21.333333 | 0.471074 | 0.413333 | 0 | 0 | 0 |
| 2023-11 | 54 | -23.050000 | 0.644382 | 0.661157 | 1 | 0 | 0 |
| 2023-12 | 39 | -38.466667 | 0.248208 | 0.279793 | 0 | 0 | 0 |

### B_OPT2023_N4_W2_T2_SB1_TP6

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 431, entry dates 196, entry months 12; SKIP 3, EXCLUDED 8, exclusion share 0.018223; conditional FLAT CLOSED 420.
Net -268.033333 R; PF R / price 0.491526 / 0.489531; expectancy -0.621887 R; win rate 0.160093; average winner / loser 3.755072 / -1.480712 R.
Conditional CLOSED-only DD 281.916667 R; largest winner share 0.038595; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 12 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 41 | -26.366667 | 0.472315 | 0.475000 | 5 | 0 | 2 |
| 2023-02 | 32 | -12.633333 | 0.654355 | 0.591549 | 4 | 2 | 0 |
| 2023-03 | 47 | -25.866667 | 0.549884 | 0.553991 | 3 | 0 | 3 |
| 2023-04 | 38 | -14.350000 | 0.634395 | 0.593103 | 5 | 1 | 0 |
| 2023-05 | 30 | -10.250000 | 0.686064 | 0.701613 | 3 | 0 | 1 |
| 2023-06 | 31 | -2.316667 | 0.933746 | 0.985507 | 4 | 0 | 2 |
| 2023-07 | 29 | -27.216667 | 0.306876 | 0.246835 | 1 | 0 | 0 |
| 2023-08 | 19 | -23.616667 | 0.098601 | 0.090909 | 2 | 0 | 0 |
| 2023-09 | 39 | -44.566667 | 0.182263 | 0.242574 | 2 | 0 | 0 |
| 2023-10 | 32 | -19.666667 | 0.512397 | 0.446667 | 0 | 0 | 0 |
| 2023-11 | 54 | -22.466667 | 0.653381 | 0.657025 | 1 | 0 | 0 |
| 2023-12 | 39 | -38.716667 | 0.243322 | 0.274611 | 0 | 0 | 0 |

### B_OPT2023_N4_W2_T2_SB1_TP7

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 431, entry dates 196, entry months 12; SKIP 3, EXCLUDED 8, exclusion share 0.018223; conditional FLAT CLOSED 420.
Net -256.216667 R; PF R / price 0.513943 / 0.508475; expectancy -0.594470 R; win rate 0.160093; average winner / loser 3.926329 / -1.480712 R.
Conditional CLOSED-only DD 268.100000 R; largest winner share 0.043064; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 12 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 41 | -28.366667 | 0.432288 | 0.435000 | 5 | 0 | 2 |
| 2023-02 | 32 | -10.966667 | 0.699954 | 0.626761 | 4 | 2 | 0 |
| 2023-03 | 47 | -24.200000 | 0.578886 | 0.577465 | 3 | 0 | 3 |
| 2023-04 | 38 | -12.683333 | 0.676858 | 0.627586 | 5 | 1 | 0 |
| 2023-05 | 30 | -11.500000 | 0.647779 | 0.661290 | 3 | 0 | 1 |
| 2023-06 | 31 | -0.816667 | 0.976644 | 1.028986 | 4 | 0 | 2 |
| 2023-07 | 29 | -26.550000 | 0.323854 | 0.259494 | 1 | 0 | 0 |
| 2023-08 | 19 | -23.616667 | 0.098601 | 0.090909 | 2 | 0 | 0 |
| 2023-09 | 39 | -43.166667 | 0.207951 | 0.277228 | 2 | 0 | 0 |
| 2023-10 | 32 | -18.000000 | 0.553719 | 0.480000 | 0 | 0 | 0 |
| 2023-11 | 54 | -17.633333 | 0.727951 | 0.723140 | 1 | 0 | 0 |
| 2023-12 | 39 | -38.716667 | 0.243322 | 0.274611 | 0 | 0 | 0 |

### B_OPT2023_N4_W2_T2_SB1_TP8

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 431, entry dates 196, entry months 12; SKIP 3, EXCLUDED 8, exclusion share 0.018223; conditional FLAT CLOSED 420.
Net -262.150000 R; PF R / price 0.504255 / 0.503729; expectancy -0.608237 R; win rate 0.157773; average winner / loser 3.921324 / -1.481232 R.
Conditional CLOSED-only DD 274.033333 R; largest winner share 0.050003; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 41 | -28.366667 | 0.432288 | 0.435000 | 5 | 0 | 2 |
| 2023-02 | 32 | -9.300000 | 0.745554 | 0.661972 | 4 | 2 | 0 |
| 2023-03 | 47 | -22.533333 | 0.607889 | 0.600939 | 3 | 0 | 3 |
| 2023-04 | 38 | -16.350000 | 0.583439 | 0.551724 | 5 | 1 | 0 |
| 2023-05 | 30 | -11.500000 | 0.647779 | 0.661290 | 3 | 0 | 1 |
| 2023-06 | 31 | 0.683333 | 1.019542 | 1.072464 | 4 | 0 | 2 |
| 2023-07 | 29 | -26.550000 | 0.323854 | 0.259494 | 1 | 0 | 0 |
| 2023-08 | 19 | -23.616667 | 0.098601 | 0.090909 | 2 | 0 | 0 |
| 2023-09 | 39 | -41.766667 | 0.233639 | 0.311881 | 2 | 0 | 0 |
| 2023-10 | 32 | -31.333333 | 0.253968 | 0.238710 | 0 | 0 | 0 |
| 2023-11 | 54 | -12.800000 | 0.802520 | 0.789256 | 1 | 0 | 0 |
| 2023-12 | 39 | -38.716667 | 0.243322 | 0.274611 | 0 | 0 | 0 |

### B_OPT2023_N4_W2_T2_SB1_TP9

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 431, entry dates 196, entry months 12; SKIP 3, EXCLUDED 8, exclusion share 0.018223; conditional FLAT CLOSED 420.
Net -263.333333 R; PF R / price 0.502017 / 0.501740; expectancy -0.610982 R; win rate 0.157773; average winner / loser 3.903922 / -1.481232 R.
Conditional CLOSED-only DD 275.216667 R; largest winner share 0.056504; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 12 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 41 | -28.366667 | 0.432288 | 0.435000 | 5 | 0 | 2 |
| 2023-02 | 32 | -7.633333 | 0.791154 | 0.697183 | 4 | 2 | 0 |
| 2023-03 | 47 | -20.866667 | 0.636891 | 0.624413 | 3 | 0 | 3 |
| 2023-04 | 38 | -16.350000 | 0.583439 | 0.551724 | 5 | 1 | 0 |
| 2023-05 | 30 | -11.500000 | 0.647779 | 0.661290 | 3 | 0 | 1 |
| 2023-06 | 31 | -4.066667 | 0.883699 | 0.934783 | 4 | 0 | 2 |
| 2023-07 | 29 | -26.550000 | 0.323854 | 0.259494 | 1 | 0 | 0 |
| 2023-08 | 19 | -23.616667 | 0.098601 | 0.090909 | 2 | 0 | 0 |
| 2023-09 | 39 | -40.366667 | 0.259327 | 0.346535 | 2 | 0 | 0 |
| 2023-10 | 32 | -31.333333 | 0.253968 | 0.238710 | 0 | 0 | 0 |
| 2023-11 | 54 | -13.966667 | 0.784520 | 0.780992 | 1 | 0 | 0 |
| 2023-12 | 39 | -38.716667 | 0.243322 | 0.274611 | 0 | 0 | 0 |

### B_OPT2023_N4_W2_T2_SB1_TP10

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 431, entry dates 196, entry months 12; SKIP 3, EXCLUDED 8, exclusion share 0.018223; conditional FLAT CLOSED 420.
Net -263.233333 R; PF R / price 0.502206 / 0.498260; expectancy -0.610750 R; win rate 0.157773; average winner / loser 3.905392 / -1.481232 R.
Conditional CLOSED-only DD 275.116667 R; largest winner share 0.062759; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 12 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 41 | -28.366667 | 0.432288 | 0.435000 | 5 | 0 | 2 |
| 2023-02 | 32 | -5.966667 | 0.836753 | 0.732394 | 4 | 2 | 0 |
| 2023-03 | 47 | -19.200000 | 0.665893 | 0.647887 | 3 | 0 | 3 |
| 2023-04 | 38 | -16.350000 | 0.583439 | 0.551724 | 5 | 1 | 0 |
| 2023-05 | 30 | -11.500000 | 0.647779 | 0.661290 | 3 | 0 | 1 |
| 2023-06 | 31 | -4.066667 | 0.883699 | 0.934783 | 4 | 0 | 2 |
| 2023-07 | 29 | -26.550000 | 0.323854 | 0.259494 | 1 | 0 | 0 |
| 2023-08 | 19 | -23.616667 | 0.098601 | 0.090909 | 2 | 0 | 0 |
| 2023-09 | 39 | -42.766667 | 0.215291 | 0.287129 | 2 | 0 | 0 |
| 2023-10 | 32 | -31.333333 | 0.253968 | 0.238710 | 0 | 0 | 0 |
| 2023-11 | 54 | -14.800000 | 0.771664 | 0.760331 | 1 | 0 | 0 |
| 2023-12 | 39 | -38.716667 | 0.243322 | 0.274611 | 0 | 0 | 0 |

### B_OPT2023_N4_W2_T3_SB1_TP2

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 169, entry dates 118, entry months 12; SKIP 0, EXCLUDED 2, exclusion share 0.011696; conditional FLAT CLOSED 140.
Net -99.433333 R; PF R / price 0.474916 / 0.497914; expectancy -0.588363 R; win rate 0.213018; average winner / loser 2.498148 / -1.456667 R.
Conditional CLOSED-only DD 101.333333 R; largest winner share 0.037064; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 12 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 13 | -6.616667 | 0.469251 | 0.471698 | 5 | 0 | 0 |
| 2023-02 | 13 | -4.700000 | 0.641221 | 0.840000 | 4 | 0 | 0 |
| 2023-03 | 21 | -1.800000 | 0.911765 | 1.000000 | 3 | 0 | 2 |
| 2023-04 | 15 | -19.033333 | 0.010399 | 0.014286 | 5 | 0 | 0 |
| 2023-05 | 13 | -11.066667 | 0.356589 | 0.380952 | 3 | 0 | 0 |
| 2023-06 | 9 | -1.566667 | 0.809717 | 0.812500 | 4 | 0 | 0 |
| 2023-07 | 11 | -10.566667 | 0.239808 | 0.192308 | 1 | 0 | 0 |
| 2023-08 | 7 | -5.466667 | 0.378788 | 0.263158 | 2 | 0 | 0 |
| 2023-09 | 20 | -2.266667 | 0.888525 | 0.913580 | 2 | 0 | 0 |
| 2023-10 | 9 | -7.016667 | 0.338050 | 0.255814 | 0 | 0 | 0 |
| 2023-11 | 22 | -18.933333 | 0.259452 | 0.288889 | 1 | 0 | 0 |
| 2023-12 | 16 | -10.400000 | 0.467577 | 0.486486 | 0 | 0 | 0 |

### B_OPT2023_N4_W2_T3_SB1_TP3

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 169, entry dates 118, entry months 12; SKIP 0, EXCLUDED 2, exclusion share 0.011696; conditional FLAT CLOSED 140.
Net -95.450000 R; PF R / price 0.514085 / 0.532086; expectancy -0.564793 R; win rate 0.183432; average winner / loser 3.257527 / -1.455062 R.
Conditional CLOSED-only DD 95.450000 R; largest winner share 0.049513; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 13 | -11.116667 | 0.204057 | 0.220339 | 5 | 0 | 0 |
| 2023-02 | 13 | -8.700000 | 0.400000 | 0.508772 | 4 | 0 | 0 |
| 2023-03 | 21 | 6.733333 | 1.330065 | 1.452055 | 3 | 0 | 2 |
| 2023-04 | 15 | -19.033333 | 0.010399 | 0.014286 | 5 | 0 | 0 |
| 2023-05 | 13 | -8.000000 | 0.534884 | 0.571429 | 3 | 0 | 0 |
| 2023-06 | 9 | -6.816667 | 0.299658 | 0.289474 | 4 | 0 | 0 |
| 2023-07 | 11 | -8.900000 | 0.359712 | 0.288462 | 1 | 0 | 0 |
| 2023-08 | 7 | -7.466667 | 0.151515 | 0.105263 | 2 | 0 | 0 |
| 2023-09 | 20 | -5.100000 | 0.778261 | 0.824176 | 2 | 0 | 0 |
| 2023-10 | 9 | -5.350000 | 0.495283 | 0.372093 | 0 | 0 | 0 |
| 2023-11 | 22 | -15.866667 | 0.379400 | 0.422222 | 1 | 0 | 0 |
| 2023-12 | 16 | -5.833333 | 0.701365 | 0.729730 | 0 | 0 | 0 |

### B_OPT2023_N4_W2_T3_SB1_TP4

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 167, entry dates 118, entry months 12; SKIP 0, EXCLUDED 2, exclusion share 0.011834; conditional FLAT CLOSED 139.
Net -98.883333 R; PF R / price 0.500421 / 0.518568; expectancy -0.592116 R; win rate 0.167665; average winner / loser 3.537500 / -1.455392 R.
Conditional CLOSED-only DD 98.883333 R; largest winner share 0.067306; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 13 | -11.116667 | 0.204057 | 0.220339 | 5 | 0 | 0 |
| 2023-02 | 13 | -7.300000 | 0.496552 | 0.631579 | 4 | 0 | 0 |
| 2023-03 | 19 | 6.966667 | 1.368607 | 1.522388 | 3 | 0 | 2 |
| 2023-04 | 15 | -19.033333 | 0.010399 | 0.014286 | 5 | 0 | 0 |
| 2023-05 | 13 | -4.933333 | 0.713178 | 0.761905 | 3 | 0 | 0 |
| 2023-06 | 9 | -6.816667 | 0.299658 | 0.289474 | 4 | 0 | 0 |
| 2023-07 | 11 | -7.233333 | 0.479616 | 0.384615 | 1 | 0 | 0 |
| 2023-08 | 7 | -7.466667 | 0.151515 | 0.105263 | 2 | 0 | 0 |
| 2023-09 | 20 | -11.033333 | 0.549660 | 0.556701 | 2 | 0 | 0 |
| 2023-10 | 9 | -3.683333 | 0.652516 | 0.488372 | 0 | 0 | 0 |
| 2023-11 | 22 | -12.800000 | 0.499348 | 0.555556 | 1 | 0 | 0 |
| 2023-12 | 16 | -14.433333 | 0.313788 | 0.387500 | 0 | 0 | 0 |

### B_OPT2023_N4_W2_T3_SB1_TP5

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 165, entry dates 117, entry months 12; SKIP 0, EXCLUDED 3, exclusion share 0.017857; conditional FLAT CLOSED 137.
Net -114.300000 R; PF R / price 0.427355 / 0.425560; expectancy -0.692727 R; win rate 0.151515; average winner / loser 3.412000 / -1.456934 R.
Conditional CLOSED-only DD 114.300000 R; largest winner share 0.097694; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 13 | -11.116667 | 0.204057 | 0.220339 | 5 | 0 | 0 |
| 2023-02 | 13 | -5.900000 | 0.593103 | 0.754386 | 4 | 0 | 0 |
| 2023-03 | 19 | 7.083333 | 1.374780 | 1.492537 | 3 | 0 | 2 |
| 2023-04 | 15 | -19.033333 | 0.010399 | 0.014286 | 5 | 0 | 0 |
| 2023-05 | 11 | -9.133333 | 0.421941 | 0.357143 | 3 | 0 | 1 |
| 2023-06 | 9 | -6.816667 | 0.299658 | 0.289474 | 4 | 0 | 0 |
| 2023-07 | 11 | -5.566667 | 0.599520 | 0.480769 | 1 | 0 | 0 |
| 2023-08 | 7 | -7.466667 | 0.151515 | 0.105263 | 2 | 0 | 0 |
| 2023-09 | 20 | -17.966667 | 0.313376 | 0.401961 | 2 | 0 | 0 |
| 2023-10 | 9 | -2.016667 | 0.809748 | 0.604651 | 0 | 0 | 0 |
| 2023-11 | 22 | -18.133333 | 0.327565 | 0.278351 | 1 | 0 | 0 |
| 2023-12 | 16 | -18.233333 | 0.133122 | 0.150000 | 0 | 0 | 0 |

### B_OPT2023_N4_W2_T3_SB1_TP6

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 165, entry dates 117, entry months 12; SKIP 0, EXCLUDED 3, exclusion share 0.017857; conditional FLAT CLOSED 137.
Net -112.833333 R; PF R / price 0.434703 / 0.438735; expectancy -0.683838 R; win rate 0.151515; average winner / loser 3.470667 / -1.456934 R.
Conditional CLOSED-only DD 112.833333 R; largest winner share 0.115252; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 13 | -11.116667 | 0.204057 | 0.220339 | 5 | 0 | 0 |
| 2023-02 | 13 | -4.500000 | 0.689655 | 0.877193 | 4 | 0 | 0 |
| 2023-03 | 19 | 8.750000 | 1.462963 | 1.567164 | 3 | 0 | 2 |
| 2023-04 | 15 | -19.033333 | 0.010399 | 0.014286 | 5 | 0 | 0 |
| 2023-05 | 11 | -9.133333 | 0.421941 | 0.357143 | 3 | 0 | 1 |
| 2023-06 | 9 | -6.816667 | 0.299658 | 0.289474 | 4 | 0 | 0 |
| 2023-07 | 11 | -3.900000 | 0.719424 | 0.576923 | 1 | 0 | 0 |
| 2023-08 | 7 | -7.466667 | 0.151515 | 0.105263 | 2 | 0 | 0 |
| 2023-09 | 20 | -16.566667 | 0.366879 | 0.470588 | 2 | 0 | 0 |
| 2023-10 | 9 | -0.350000 | 0.966981 | 0.720930 | 0 | 0 | 0 |
| 2023-11 | 22 | -24.466667 | 0.092707 | 0.082474 | 1 | 0 | 0 |
| 2023-12 | 16 | -18.233333 | 0.133122 | 0.150000 | 0 | 0 | 0 |

### B_OPT2023_N4_W2_T3_SB1_TP7

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 165, entry dates 117, entry months 12; SKIP 0, EXCLUDED 3, exclusion share 0.017857; conditional FLAT CLOSED 137.
Net -107.366667 R; PF R / price 0.462091 / 0.467721; expectancy -0.650707 R; win rate 0.151515; average winner / loser 3.689333 / -1.456934 R.
Conditional CLOSED-only DD 109.900000 R; largest winner share 0.126491; largest positive month share 0.887784. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 13 | -11.116667 | 0.204057 | 0.220339 | 5 | 0 | 0 |
| 2023-02 | 13 | -3.100000 | 0.786207 | 1.000000 | 4 | 0 | 0 |
| 2023-03 | 19 | 10.416667 | 1.551146 | 1.641791 | 3 | 0 | 2 |
| 2023-04 | 15 | -19.033333 | 0.010399 | 0.014286 | 5 | 0 | 0 |
| 2023-05 | 11 | -9.133333 | 0.421941 | 0.357143 | 3 | 0 | 1 |
| 2023-06 | 9 | -6.816667 | 0.299658 | 0.289474 | 4 | 0 | 0 |
| 2023-07 | 11 | -4.566667 | 0.671463 | 0.538462 | 1 | 0 | 0 |
| 2023-08 | 7 | -7.466667 | 0.151515 | 0.105263 | 2 | 0 | 0 |
| 2023-09 | 20 | -15.166667 | 0.420382 | 0.539216 | 2 | 0 | 0 |
| 2023-10 | 9 | 1.316667 | 1.124214 | 0.837209 | 0 | 0 | 0 |
| 2023-11 | 22 | -24.466667 | 0.092707 | 0.082474 | 1 | 0 | 0 |
| 2023-12 | 16 | -18.233333 | 0.133122 | 0.150000 | 0 | 0 | 0 |

### B_OPT2023_N4_W2_T3_SB1_TP8

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 165, entry dates 117, entry months 12; SKIP 0, EXCLUDED 3, exclusion share 0.017857; conditional FLAT CLOSED 137.
Net -101.233333 R; PF R / price 0.492819 / 0.499341; expectancy -0.613535 R; win rate 0.151515; average winner / loser 3.934667 / -1.456934 R.
Conditional CLOSED-only DD 106.833333 R; largest winner share 0.135547; largest positive month share 0.801991. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 13 | -11.116667 | 0.204057 | 0.220339 | 5 | 0 | 0 |
| 2023-02 | 13 | -1.700000 | 0.882759 | 1.122807 | 4 | 0 | 0 |
| 2023-03 | 19 | 12.083333 | 1.639330 | 1.716418 | 3 | 0 | 2 |
| 2023-04 | 15 | -19.033333 | 0.010399 | 0.014286 | 5 | 0 | 0 |
| 2023-05 | 11 | -9.133333 | 0.421941 | 0.357143 | 3 | 0 | 1 |
| 2023-06 | 9 | -6.816667 | 0.299658 | 0.289474 | 4 | 0 | 0 |
| 2023-07 | 11 | -4.566667 | 0.671463 | 0.538462 | 1 | 0 | 0 |
| 2023-08 | 7 | -7.466667 | 0.151515 | 0.105263 | 2 | 0 | 0 |
| 2023-09 | 20 | -13.766667 | 0.473885 | 0.607843 | 2 | 0 | 0 |
| 2023-10 | 9 | 2.983333 | 1.281447 | 0.953488 | 0 | 0 | 0 |
| 2023-11 | 22 | -24.466667 | 0.092707 | 0.082474 | 1 | 0 | 0 |
| 2023-12 | 16 | -18.233333 | 0.133122 | 0.150000 | 0 | 0 | 0 |

### B_OPT2023_N4_W2_T3_SB1_TP9

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 165, entry dates 117, entry months 12; SKIP 0, EXCLUDED 3, exclusion share 0.017857; conditional FLAT CLOSED 137.
Net -105.766667 R; PF R / price 0.470107 / 0.488801; expectancy -0.641010 R; win rate 0.151515; average winner / loser 3.753333 / -1.456934 R.
Conditional CLOSED-only DD 114.433333 R; largest winner share 0.159858; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 13 | -11.116667 | 0.204057 | 0.220339 | 5 | 0 | 0 |
| 2023-02 | 13 | -0.300000 | 0.979310 | 1.245614 | 4 | 0 | 0 |
| 2023-03 | 19 | 13.750000 | 1.727513 | 1.791045 | 3 | 0 | 2 |
| 2023-04 | 15 | -19.033333 | 0.010399 | 0.014286 | 5 | 0 | 0 |
| 2023-05 | 11 | -9.133333 | 0.421941 | 0.357143 | 3 | 0 | 1 |
| 2023-06 | 9 | -6.816667 | 0.299658 | 0.289474 | 4 | 0 | 0 |
| 2023-07 | 11 | -4.566667 | 0.671463 | 0.538462 | 1 | 0 | 0 |
| 2023-08 | 7 | -7.466667 | 0.151515 | 0.105263 | 2 | 0 | 0 |
| 2023-09 | 20 | -12.366667 | 0.527389 | 0.676471 | 2 | 0 | 0 |
| 2023-10 | 9 | -6.016667 | 0.432390 | 0.325581 | 0 | 0 | 0 |
| 2023-11 | 22 | -24.466667 | 0.092707 | 0.082474 | 1 | 0 | 0 |
| 2023-12 | 16 | -18.233333 | 0.133122 | 0.150000 | 0 | 0 | 0 |

### B_OPT2023_N4_W2_T3_SB1_TP10

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 165, entry dates 117, entry months 12; SKIP 0, EXCLUDED 3, exclusion share 0.017857; conditional FLAT CLOSED 137.
Net -106.900000 R; PF R / price 0.464429 / 0.476943; expectancy -0.647879 R; win rate 0.151515; average winner / loser 3.708000 / -1.456934 R.
Conditional CLOSED-only DD 116.833333 R; largest winner share 0.179791; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 13 | -11.116667 | 0.204057 | 0.220339 | 5 | 0 | 0 |
| 2023-02 | 13 | -0.700000 | 0.951724 | 1.210526 | 4 | 0 | 0 |
| 2023-03 | 19 | 15.416667 | 1.815697 | 1.865672 | 3 | 0 | 2 |
| 2023-04 | 15 | -19.033333 | 0.010399 | 0.014286 | 5 | 0 | 0 |
| 2023-05 | 11 | -9.133333 | 0.421941 | 0.357143 | 3 | 0 | 1 |
| 2023-06 | 9 | -6.816667 | 0.299658 | 0.289474 | 4 | 0 | 0 |
| 2023-07 | 11 | -4.566667 | 0.671463 | 0.538462 | 1 | 0 | 0 |
| 2023-08 | 7 | -7.466667 | 0.151515 | 0.105263 | 2 | 0 | 0 |
| 2023-09 | 20 | -14.766667 | 0.435669 | 0.558824 | 2 | 0 | 0 |
| 2023-10 | 9 | -6.016667 | 0.432390 | 0.325581 | 0 | 0 | 0 |
| 2023-11 | 22 | -24.466667 | 0.092707 | 0.082474 | 1 | 0 | 0 |
| 2023-12 | 16 | -18.233333 | 0.133122 | 0.150000 | 0 | 0 | 0 |

### B_OPT2023_N4_W3_T2_SB1_TP2

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 566, entry dates 218, entry months 12; SKIP 2, EXCLUDED 6, exclusion share 0.010490; conditional FLAT CLOSED 535.
Net -310.516667 R; PF R / price 0.511984 / 0.506656; expectancy -0.548616 R; win rate 0.227915; average winner / loser 2.525323 / -1.469477 R.
Conditional CLOSED-only DD 318.483333 R; largest winner share 0.010232; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 46 | -34.683333 | 0.367092 | 0.356481 | 5 | 0 | 2 |
| 2023-02 | 45 | -29.416667 | 0.434838 | 0.405941 | 4 | 1 | 1 |
| 2023-03 | 69 | -58.066667 | 0.317665 | 0.330247 | 3 | 0 | 2 |
| 2023-04 | 55 | -30.100000 | 0.508438 | 0.526316 | 5 | 1 | 0 |
| 2023-05 | 37 | 3.933333 | 1.121838 | 1.118110 | 3 | 0 | 1 |
| 2023-06 | 44 | -17.366667 | 0.644611 | 0.705263 | 4 | 0 | 0 |
| 2023-07 | 39 | -31.083333 | 0.330581 | 0.284974 | 1 | 0 | 0 |
| 2023-08 | 26 | -14.733333 | 0.512679 | 0.429752 | 2 | 0 | 0 |
| 2023-09 | 43 | -16.883333 | 0.634164 | 0.629213 | 2 | 0 | 0 |
| 2023-10 | 41 | -23.983333 | 0.491879 | 0.454054 | 0 | 0 | 0 |
| 2023-11 | 67 | -30.333333 | 0.584475 | 0.559859 | 1 | 0 | 0 |
| 2023-12 | 54 | -27.800000 | 0.528281 | 0.571429 | 0 | 0 | 0 |

### B_OPT2023_N4_W3_T2_SB1_TP3

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 551, entry dates 217, entry months 12; SKIP 2, EXCLUDED 8, exclusion share 0.014311; conditional FLAT CLOSED 520.
Net -284.916667 R; PF R / price 0.554737 / 0.556763; expectancy -0.517090 R; win rate 0.199637; average winner / loser 3.226970 / -1.467622 R.
Conditional CLOSED-only DD 300.450000 R; largest winner share 0.014086; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 46 | -29.200000 | 0.467153 | 0.449074 | 5 | 0 | 2 |
| 2023-02 | 45 | -30.216667 | 0.430412 | 0.390244 | 4 | 1 | 1 |
| 2023-03 | 62 | -42.500000 | 0.441769 | 0.442509 | 3 | 0 | 3 |
| 2023-04 | 53 | -27.800000 | 0.535893 | 0.584821 | 5 | 1 | 0 |
| 2023-05 | 37 | 10.783333 | 1.317624 | 1.356061 | 3 | 0 | 1 |
| 2023-06 | 43 | -29.700000 | 0.444167 | 0.480769 | 4 | 0 | 1 |
| 2023-07 | 39 | -36.950000 | 0.253535 | 0.200000 | 1 | 0 | 0 |
| 2023-08 | 25 | -13.500000 | 0.531792 | 0.438596 | 2 | 0 | 0 |
| 2023-09 | 43 | -21.416667 | 0.567194 | 0.611702 | 2 | 0 | 0 |
| 2023-10 | 41 | -28.250000 | 0.439113 | 0.418367 | 0 | 0 | 0 |
| 2023-11 | 65 | -26.366667 | 0.646875 | 0.643599 | 1 | 0 | 0 |
| 2023-12 | 52 | -9.800000 | 0.824268 | 0.886364 | 0 | 0 | 0 |

### B_OPT2023_N4_W3_T2_SB1_TP4

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 545, entry dates 217, entry months 12; SKIP 2, EXCLUDED 8, exclusion share 0.014467; conditional FLAT CLOSED 514.
Net -267.966667 R; PF R / price 0.581269 / 0.576380; expectancy -0.491682 R; win rate 0.190826; average winner / loser 3.576763 / -1.467775 R.
Conditional CLOSED-only DD 284.516667 R; largest winner share 0.017922; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 46 | -27.916667 | 0.490572 | 0.458333 | 5 | 0 | 2 |
| 2023-02 | 44 | -25.683333 | 0.514033 | 0.470588 | 4 | 1 | 1 |
| 2023-03 | 60 | -40.700000 | 0.455397 | 0.457143 | 3 | 0 | 3 |
| 2023-04 | 52 | -39.783333 | 0.345669 | 0.339207 | 5 | 1 | 0 |
| 2023-05 | 37 | 22.983333 | 1.676976 | 1.719697 | 3 | 0 | 1 |
| 2023-06 | 43 | -25.233333 | 0.527760 | 0.572115 | 4 | 0 | 1 |
| 2023-07 | 39 | -33.616667 | 0.320875 | 0.248780 | 1 | 0 | 0 |
| 2023-08 | 25 | -18.500000 | 0.393443 | 0.336134 | 2 | 0 | 0 |
| 2023-09 | 43 | -18.350000 | 0.629168 | 0.659574 | 2 | 0 | 0 |
| 2023-10 | 41 | -32.383333 | 0.375643 | 0.346535 | 0 | 0 | 0 |
| 2023-11 | 63 | -16.550000 | 0.769070 | 0.768953 | 1 | 0 | 0 |
| 2023-12 | 52 | -12.233333 | 0.782969 | 0.834081 | 0 | 0 | 0 |

### B_OPT2023_N4_W3_T2_SB1_TP5

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 542, entry dates 216, entry months 12; SKIP 2, EXCLUDED 8, exclusion share 0.014545; conditional FLAT CLOSED 511.
Net -287.583333 R; PF R / price 0.555066 / 0.547743; expectancy -0.530597 R; win rate 0.178967; average winner / loser 3.698625 / -1.468977 R.
Conditional CLOSED-only DD 308.100000 R; largest winner share 0.023228; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 46 | -29.750000 | 0.457117 | 0.439815 | 5 | 0 | 2 |
| 2023-02 | 43 | -20.616667 | 0.599287 | 0.553299 | 4 | 1 | 1 |
| 2023-03 | 60 | -38.916667 | 0.479260 | 0.467857 | 3 | 0 | 3 |
| 2023-04 | 52 | -40.366667 | 0.336075 | 0.321586 | 5 | 1 | 0 |
| 2023-05 | 36 | 22.116667 | 1.651448 | 1.613636 | 3 | 0 | 1 |
| 2023-06 | 43 | -23.100000 | 0.567686 | 0.629808 | 4 | 0 | 1 |
| 2023-07 | 39 | -40.283333 | 0.212704 | 0.171429 | 1 | 0 | 0 |
| 2023-08 | 25 | -29.733333 | 0.114201 | 0.106870 | 2 | 0 | 0 |
| 2023-09 | 43 | -26.033333 | 0.491039 | 0.559585 | 2 | 0 | 0 |
| 2023-10 | 41 | -30.716667 | 0.407776 | 0.371287 | 0 | 0 | 0 |
| 2023-11 | 63 | -14.216667 | 0.805429 | 0.771127 | 1 | 0 | 0 |
| 2023-12 | 51 | -15.966667 | 0.716736 | 0.748879 | 0 | 0 | 0 |

### B_OPT2023_N4_W3_T2_SB1_TP6

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 540, entry dates 216, entry months 12; SKIP 2, EXCLUDED 8, exclusion share 0.014599; conditional FLAT CLOSED 510.
Net -279.816667 R; PF R / price 0.566142 / 0.552083; expectancy -0.518179 R; win rate 0.177778; average winner / loser 3.803472 / -1.469134 R.
Conditional CLOSED-only DD 296.516667 R; largest winner share 0.027387; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 45 | -33.316667 | 0.392032 | 0.393519 | 5 | 0 | 2 |
| 2023-02 | 43 | -19.950000 | 0.612245 | 0.558376 | 4 | 1 | 1 |
| 2023-03 | 60 | -35.583333 | 0.523863 | 0.503571 | 3 | 0 | 3 |
| 2023-04 | 52 | -38.700000 | 0.363487 | 0.343612 | 5 | 1 | 0 |
| 2023-05 | 36 | 22.850000 | 1.673049 | 1.568182 | 3 | 0 | 1 |
| 2023-06 | 43 | -24.700000 | 0.537742 | 0.591346 | 4 | 0 | 1 |
| 2023-07 | 39 | -38.616667 | 0.245277 | 0.195238 | 1 | 0 | 0 |
| 2023-08 | 25 | -29.733333 | 0.114201 | 0.106870 | 2 | 0 | 0 |
| 2023-09 | 43 | -23.133333 | 0.547735 | 0.626943 | 2 | 0 | 0 |
| 2023-10 | 41 | -29.050000 | 0.439910 | 0.396040 | 0 | 0 | 0 |
| 2023-11 | 63 | -15.133333 | 0.792883 | 0.746479 | 1 | 0 | 0 |
| 2023-12 | 50 | -14.750000 | 0.731656 | 0.768519 | 0 | 0 | 0 |

### B_OPT2023_N4_W3_T2_SB1_TP7

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 540, entry dates 216, entry months 12; SKIP 2, EXCLUDED 8, exclusion share 0.014599; conditional FLAT CLOSED 510.
Net -271.933333 R; PF R / price 0.578365 / 0.562500; expectancy -0.503580 R; win rate 0.177778; average winner / loser 3.885590 / -1.469134 R.
Conditional CLOSED-only DD 286.633333 R; largest winner share 0.031277; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 45 | -35.316667 | 0.355535 | 0.356481 | 5 | 0 | 2 |
| 2023-02 | 43 | -18.283333 | 0.644639 | 0.583756 | 4 | 1 | 1 |
| 2023-03 | 60 | -32.250000 | 0.568466 | 0.539286 | 3 | 0 | 3 |
| 2023-04 | 52 | -37.033333 | 0.390899 | 0.365639 | 5 | 1 | 0 |
| 2023-05 | 36 | 19.766667 | 1.582229 | 1.500000 | 3 | 0 | 1 |
| 2023-06 | 43 | -24.700000 | 0.537742 | 0.591346 | 4 | 0 | 1 |
| 2023-07 | 39 | -37.950000 | 0.258306 | 0.204762 | 1 | 0 | 0 |
| 2023-08 | 25 | -29.733333 | 0.114201 | 0.106870 | 2 | 0 | 0 |
| 2023-09 | 43 | -20.233333 | 0.604431 | 0.694301 | 2 | 0 | 0 |
| 2023-10 | 41 | -27.383333 | 0.472044 | 0.420792 | 0 | 0 | 0 |
| 2023-11 | 63 | -14.800000 | 0.797445 | 0.739437 | 1 | 0 | 0 |
| 2023-12 | 50 | -14.016667 | 0.744997 | 0.791667 | 0 | 0 | 0 |

### B_OPT2023_N4_W3_T2_SB1_TP8

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 540, entry dates 216, entry months 12; SKIP 2, EXCLUDED 8, exclusion share 0.014599; conditional FLAT CLOSED 510.
Net -273.133333 R; PF R / price 0.577596 / 0.565374; expectancy -0.505802 R; win rate 0.175926; average winner / loser 3.931404 / -1.469583 R.
Conditional CLOSED-only DD 287.833333 R; largest winner share 0.035700; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 45 | -35.316667 | 0.355535 | 0.356481 | 5 | 0 | 2 |
| 2023-02 | 43 | -16.616667 | 0.677033 | 0.609137 | 4 | 1 | 1 |
| 2023-03 | 60 | -28.916667 | 0.613069 | 0.575000 | 3 | 0 | 3 |
| 2023-04 | 52 | -40.700000 | 0.330592 | 0.317181 | 5 | 1 | 0 |
| 2023-05 | 36 | 22.933333 | 1.675503 | 1.583333 | 3 | 0 | 1 |
| 2023-06 | 43 | -24.700000 | 0.537742 | 0.591346 | 4 | 0 | 1 |
| 2023-07 | 39 | -37.950000 | 0.258306 | 0.204762 | 1 | 0 | 0 |
| 2023-08 | 25 | -29.733333 | 0.114201 | 0.106870 | 2 | 0 | 0 |
| 2023-09 | 43 | -17.333333 | 0.661127 | 0.761658 | 2 | 0 | 0 |
| 2023-10 | 41 | -40.716667 | 0.239415 | 0.241546 | 0 | 0 | 0 |
| 2023-11 | 63 | -11.466667 | 0.843066 | 0.774648 | 1 | 0 | 0 |
| 2023-12 | 50 | -12.616667 | 0.770467 | 0.824074 | 0 | 0 | 0 |

### B_OPT2023_N4_W3_T2_SB1_TP9

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 540, entry dates 216, entry months 12; SKIP 2, EXCLUDED 8, exclusion share 0.014599; conditional FLAT CLOSED 510.
Net -275.583333 R; PF R / price 0.573807 / 0.560976; expectancy -0.510340 R; win rate 0.175926; average winner / loser 3.905614 / -1.469583 R.
Conditional CLOSED-only DD 290.283333 R; largest winner share 0.040428; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 45 | -35.316667 | 0.355535 | 0.356481 | 5 | 0 | 2 |
| 2023-02 | 43 | -14.950000 | 0.709427 | 0.634518 | 4 | 1 | 1 |
| 2023-03 | 60 | -25.583333 | 0.657672 | 0.610714 | 3 | 0 | 3 |
| 2023-04 | 52 | -40.700000 | 0.330592 | 0.317181 | 5 | 1 | 0 |
| 2023-05 | 36 | 26.100000 | 1.768778 | 1.666667 | 3 | 0 | 1 |
| 2023-06 | 43 | -24.700000 | 0.537742 | 0.591346 | 4 | 0 | 1 |
| 2023-07 | 39 | -37.950000 | 0.258306 | 0.204762 | 1 | 0 | 0 |
| 2023-08 | 25 | -29.733333 | 0.114201 | 0.106870 | 2 | 0 | 0 |
| 2023-09 | 43 | -26.683333 | 0.478332 | 0.575130 | 2 | 0 | 0 |
| 2023-10 | 41 | -40.716667 | 0.239415 | 0.241546 | 0 | 0 | 0 |
| 2023-11 | 63 | -14.133333 | 0.806569 | 0.746479 | 1 | 0 | 0 |
| 2023-12 | 50 | -11.216667 | 0.795937 | 0.856481 | 0 | 0 | 0 |

### B_OPT2023_N4_W3_T2_SB1_TP10

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 540, entry dates 216, entry months 12; SKIP 2, EXCLUDED 8, exclusion share 0.014599; conditional FLAT CLOSED 510.
Net -276.350000 R; PF R / price 0.572622 / 0.552179; expectancy -0.511759 R; win rate 0.175926; average winner / loser 3.897544 / -1.469583 R.
Conditional CLOSED-only DD 291.050000 R; largest winner share 0.045013; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 45 | -35.316667 | 0.355535 | 0.356481 | 5 | 0 | 2 |
| 2023-02 | 43 | -13.283333 | 0.741821 | 0.659898 | 4 | 1 | 1 |
| 2023-03 | 60 | -22.250000 | 0.702275 | 0.646429 | 3 | 0 | 3 |
| 2023-04 | 52 | -40.700000 | 0.330592 | 0.317181 | 5 | 1 | 0 |
| 2023-05 | 36 | 29.266667 | 1.862052 | 1.750000 | 3 | 0 | 1 |
| 2023-06 | 43 | -24.700000 | 0.537742 | 0.591346 | 4 | 0 | 1 |
| 2023-07 | 39 | -37.950000 | 0.258306 | 0.204762 | 1 | 0 | 0 |
| 2023-08 | 25 | -29.733333 | 0.114201 | 0.106870 | 2 | 0 | 0 |
| 2023-09 | 43 | -29.083333 | 0.431411 | 0.512953 | 2 | 0 | 0 |
| 2023-10 | 41 | -40.716667 | 0.239415 | 0.241546 | 0 | 0 | 0 |
| 2023-11 | 63 | -12.466667 | 0.829380 | 0.764085 | 1 | 0 | 0 |
| 2023-12 | 50 | -19.416667 | 0.646756 | 0.666667 | 0 | 0 | 0 |

### B_OPT2023_N4_W3_T3_SB1_TP2

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 202, entry dates 130, entry months 12; SKIP 0, EXCLUDED 3, exclusion share 0.014634; conditional FLAT CLOSED 186.
Net -93.133333 R; PF R / price 0.566284 / 0.568651; expectancy -0.461056 R; win rate 0.252475; average winner / loser 2.384314 / -1.460771 R.
Conditional CLOSED-only DD 98.366667 R; largest winner share 0.027412; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 18 | -4.650000 | 0.723762 | 0.661972 | 5 | 0 | 1 |
| 2023-02 | 12 | -3.400000 | 0.724324 | 0.775510 | 4 | 0 | 0 |
| 2023-03 | 26 | 1.866667 | 1.079772 | 1.164706 | 3 | 0 | 2 |
| 2023-04 | 16 | -22.383333 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 18 | -16.366667 | 0.296057 | 0.300000 | 3 | 0 | 0 |
| 2023-06 | 11 | -5.200000 | 0.535714 | 0.533333 | 4 | 0 | 0 |
| 2023-07 | 14 | -9.300000 | 0.332536 | 0.296296 | 1 | 0 | 0 |
| 2023-08 | 8 | -4.216667 | 0.520833 | 0.394737 | 2 | 0 | 0 |
| 2023-09 | 23 | -0.766667 | 0.962963 | 1.000000 | 2 | 0 | 0 |
| 2023-10 | 10 | -8.516667 | 0.296143 | 0.224490 | 0 | 0 | 0 |
| 2023-11 | 26 | -7.600000 | 0.696809 | 0.698925 | 1 | 0 | 0 |
| 2023-12 | 20 | -12.600000 | 0.490566 | 0.551724 | 0 | 0 | 0 |

### B_OPT2023_N4_W3_T3_SB1_TP3

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 201, entry dates 130, entry months 12; SKIP 0, EXCLUDED 3, exclusion share 0.014706; conditional FLAT CLOSED 185.
Net -88.900000 R; PF R / price 0.602770 / 0.600698; expectancy -0.442289 R; win rate 0.218905; average winner / loser 3.065909 / -1.462745 R.
Conditional CLOSED-only DD 92.800000 R; largest winner share 0.037064; largest positive month share 0.813187. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 18 | -9.733333 | 0.469091 | 0.402597 | 5 | 0 | 1 |
| 2023-02 | 12 | -4.533333 | 0.669903 | 0.642857 | 4 | 0 | 0 |
| 2023-03 | 26 | 7.400000 | 1.297189 | 1.384615 | 3 | 0 | 2 |
| 2023-04 | 16 | -22.383333 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 18 | -13.300000 | 0.427957 | 0.433333 | 3 | 0 | 0 |
| 2023-06 | 11 | -10.450000 | 0.177165 | 0.176471 | 4 | 0 | 0 |
| 2023-07 | 14 | -7.633333 | 0.452153 | 0.388889 | 1 | 0 | 0 |
| 2023-08 | 8 | -6.216667 | 0.293561 | 0.236842 | 2 | 0 | 0 |
| 2023-09 | 23 | 1.700000 | 1.076006 | 1.192771 | 2 | 0 | 0 |
| 2023-10 | 10 | -6.850000 | 0.433884 | 0.326531 | 0 | 0 | 0 |
| 2023-11 | 26 | -5.866667 | 0.779172 | 0.767677 | 1 | 0 | 0 |
| 2023-12 | 19 | -11.033333 | 0.553908 | 0.620690 | 0 | 0 | 0 |

### B_OPT2023_N4_W3_T3_SB1_TP4

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 199, entry dates 130, entry months 12; SKIP 0, EXCLUDED 3, exclusion share 0.014851; conditional FLAT CLOSED 183.
Net -85.750000 R; PF R / price 0.616845 / 0.620489; expectancy -0.430905 R; win rate 0.211055; average winner / loser 3.286905 / -1.462745 R.
Conditional CLOSED-only DD 91.316667 R; largest winner share 0.048292; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 18 | -8.066667 | 0.560000 | 0.467532 | 5 | 0 | 1 |
| 2023-02 | 12 | -5.800000 | 0.577670 | 0.625000 | 4 | 0 | 0 |
| 2023-03 | 24 | 9.133333 | 1.390313 | 1.505882 | 3 | 0 | 2 |
| 2023-04 | 16 | -22.383333 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 18 | -10.233333 | 0.559857 | 0.566667 | 3 | 0 | 0 |
| 2023-06 | 11 | -10.450000 | 0.177165 | 0.176471 | 4 | 0 | 0 |
| 2023-07 | 14 | -5.966667 | 0.571770 | 0.481481 | 1 | 0 | 0 |
| 2023-08 | 8 | -6.216667 | 0.293561 | 0.236842 | 2 | 0 | 0 |
| 2023-09 | 23 | -2.733333 | 0.885475 | 0.943820 | 2 | 0 | 0 |
| 2023-10 | 10 | -5.183333 | 0.571625 | 0.428571 | 0 | 0 | 0 |
| 2023-11 | 26 | -5.716667 | 0.784818 | 0.797980 | 1 | 0 | 0 |
| 2023-12 | 19 | -12.133333 | 0.509434 | 0.632184 | 0 | 0 | 0 |

### B_OPT2023_N4_W3_T3_SB1_TP5

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 197, entry dates 129, entry months 12; SKIP 0, EXCLUDED 4, exclusion share 0.019900; conditional FLAT CLOSED 181.
Net -101.400000 R; PF R / price 0.550067 / 0.534104; expectancy -0.514721 R; win rate 0.197970; average winner / loser 3.178632 / -1.463420 R.
Conditional CLOSED-only DD 108.633333 R; largest winner share 0.067222; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 18 | -6.400000 | 0.650909 | 0.532468 | 5 | 0 | 1 |
| 2023-02 | 12 | -4.400000 | 0.679612 | 0.750000 | 4 | 0 | 0 |
| 2023-03 | 24 | 8.000000 | 1.341880 | 1.423529 | 3 | 0 | 2 |
| 2023-04 | 16 | -22.383333 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 16 | -14.333333 | 0.340996 | 0.273810 | 3 | 0 | 1 |
| 2023-06 | 11 | -10.450000 | 0.177165 | 0.176471 | 4 | 0 | 0 |
| 2023-07 | 14 | -4.300000 | 0.691388 | 0.574074 | 1 | 0 | 0 |
| 2023-08 | 8 | -6.216667 | 0.293561 | 0.236842 | 2 | 0 | 0 |
| 2023-09 | 23 | -11.916667 | 0.533290 | 0.659574 | 2 | 0 | 0 |
| 2023-10 | 10 | -3.516667 | 0.709366 | 0.530612 | 0 | 0 | 0 |
| 2023-11 | 26 | -11.050000 | 0.604887 | 0.528302 | 1 | 0 | 0 |
| 2023-12 | 19 | -14.433333 | 0.416442 | 0.482759 | 0 | 0 | 0 |

### B_OPT2023_N4_W3_T3_SB1_TP6

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 196, entry dates 129, entry months 12; SKIP 0, EXCLUDED 4, exclusion share 0.020000; conditional FLAT CLOSED 181.
Net -108.000000 R; PF R / price 0.520781 / 0.513295; expectancy -0.551020 R; win rate 0.193878; average winner / loser 3.088596 / -1.463420 R.
Conditional CLOSED-only DD 110.166667 R; largest winner share 0.085203; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 17 | -11.466667 | 0.374545 | 0.324675 | 5 | 0 | 1 |
| 2023-02 | 12 | -3.000000 | 0.781553 | 0.875000 | 4 | 0 | 0 |
| 2023-03 | 24 | 9.666667 | 1.413105 | 1.482353 | 3 | 0 | 2 |
| 2023-04 | 16 | -22.383333 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 16 | -14.333333 | 0.340996 | 0.273810 | 3 | 0 | 1 |
| 2023-06 | 11 | -10.450000 | 0.177165 | 0.176471 | 4 | 0 | 0 |
| 2023-07 | 14 | -2.633333 | 0.811005 | 0.666667 | 1 | 0 | 0 |
| 2023-08 | 8 | -6.216667 | 0.293561 | 0.236842 | 2 | 0 | 0 |
| 2023-09 | 23 | -10.516667 | 0.588120 | 0.734043 | 2 | 0 | 0 |
| 2023-10 | 10 | -1.850000 | 0.847107 | 0.632653 | 0 | 0 | 0 |
| 2023-11 | 26 | -17.383333 | 0.378427 | 0.349057 | 1 | 0 | 0 |
| 2023-12 | 19 | -17.433333 | 0.295148 | 0.344828 | 0 | 0 | 0 |

### B_OPT2023_N4_W3_T3_SB1_TP7

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 196, entry dates 129, entry months 12; SKIP 0, EXCLUDED 4, exclusion share 0.020000; conditional FLAT CLOSED 181.
Net -102.533333 R; PF R / price 0.545038 / 0.538728; expectancy -0.523129 R; win rate 0.193878; average winner / loser 3.232456 / -1.463420 R.
Conditional CLOSED-only DD 107.133333 R; largest winner share 0.094980; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 17 | -11.466667 | 0.374545 | 0.324675 | 5 | 0 | 1 |
| 2023-02 | 12 | -1.600000 | 0.883495 | 1.000000 | 4 | 0 | 0 |
| 2023-03 | 24 | 11.333333 | 1.484330 | 1.541176 | 3 | 0 | 2 |
| 2023-04 | 16 | -22.383333 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 16 | -14.333333 | 0.340996 | 0.273810 | 3 | 0 | 1 |
| 2023-06 | 11 | -10.450000 | 0.177165 | 0.176471 | 4 | 0 | 0 |
| 2023-07 | 14 | -3.300000 | 0.763158 | 0.629630 | 1 | 0 | 0 |
| 2023-08 | 8 | -6.216667 | 0.293561 | 0.236842 | 2 | 0 | 0 |
| 2023-09 | 23 | -9.116667 | 0.642950 | 0.808511 | 2 | 0 | 0 |
| 2023-10 | 10 | -0.183333 | 0.984848 | 0.734694 | 0 | 0 | 0 |
| 2023-11 | 26 | -17.383333 | 0.378427 | 0.349057 | 1 | 0 | 0 |
| 2023-12 | 19 | -17.433333 | 0.295148 | 0.344828 | 0 | 0 | 0 |

### B_OPT2023_N4_W3_T3_SB1_TP8

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 196, entry dates 129, entry months 12; SKIP 0, EXCLUDED 4, exclusion share 0.020000; conditional FLAT CLOSED 181.
Net -96.400000 R; PF R / price 0.572253 / 0.566474; expectancy -0.491837 R; win rate 0.193878; average winner / loser 3.393860 / -1.463420 R.
Conditional CLOSED-only DD 104.066667 R; largest winner share 0.103386; largest positive month share 0.897583. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 17 | -11.466667 | 0.374545 | 0.324675 | 5 | 0 | 1 |
| 2023-02 | 12 | -0.200000 | 0.985437 | 1.125000 | 4 | 0 | 0 |
| 2023-03 | 24 | 13.000000 | 1.555556 | 1.600000 | 3 | 0 | 2 |
| 2023-04 | 16 | -22.383333 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 16 | -14.333333 | 0.340996 | 0.273810 | 3 | 0 | 1 |
| 2023-06 | 11 | -10.450000 | 0.177165 | 0.176471 | 4 | 0 | 0 |
| 2023-07 | 14 | -3.300000 | 0.763158 | 0.629630 | 1 | 0 | 0 |
| 2023-08 | 8 | -6.216667 | 0.293561 | 0.236842 | 2 | 0 | 0 |
| 2023-09 | 23 | -7.716667 | 0.697781 | 0.882979 | 2 | 0 | 0 |
| 2023-10 | 10 | 1.483333 | 1.122590 | 0.836735 | 0 | 0 | 0 |
| 2023-11 | 26 | -17.383333 | 0.378427 | 0.349057 | 1 | 0 | 0 |
| 2023-12 | 19 | -17.433333 | 0.295148 | 0.344828 | 0 | 0 | 0 |

### B_OPT2023_N4_W3_T3_SB1_TP9

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 196, entry dates 129, entry months 12; SKIP 0, EXCLUDED 4, exclusion share 0.020000; conditional FLAT CLOSED 181.
Net -100.933333 R; PF R / price 0.552137 / 0.557225; expectancy -0.514966 R; win rate 0.193878; average winner / loser 3.274561 / -1.463420 R.
Conditional CLOSED-only DD 111.666667 R; largest winner share 0.120546; largest positive month share 0.924370. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 17 | -11.466667 | 0.374545 | 0.324675 | 5 | 0 | 1 |
| 2023-02 | 12 | 1.200000 | 1.087379 | 1.250000 | 4 | 0 | 0 |
| 2023-03 | 24 | 14.666667 | 1.626781 | 1.658824 | 3 | 0 | 2 |
| 2023-04 | 16 | -22.383333 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 16 | -14.333333 | 0.340996 | 0.273810 | 3 | 0 | 1 |
| 2023-06 | 11 | -10.450000 | 0.177165 | 0.176471 | 4 | 0 | 0 |
| 2023-07 | 14 | -3.300000 | 0.763158 | 0.629630 | 1 | 0 | 0 |
| 2023-08 | 8 | -6.216667 | 0.293561 | 0.236842 | 2 | 0 | 0 |
| 2023-09 | 23 | -6.316667 | 0.752611 | 0.957447 | 2 | 0 | 0 |
| 2023-10 | 10 | -7.516667 | 0.378788 | 0.285714 | 0 | 0 | 0 |
| 2023-11 | 26 | -17.383333 | 0.378427 | 0.349057 | 1 | 0 | 0 |
| 2023-12 | 19 | -17.433333 | 0.295148 | 0.344828 | 0 | 0 | 0 |

### B_OPT2023_N4_W3_T3_SB1_TP10

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 196, entry dates 129, entry months 12; SKIP 0, EXCLUDED 4, exclusion share 0.020000; conditional FLAT CLOSED 181.
Net -102.066667 R; PF R / price 0.547108 / 0.546821; expectancy -0.520748 R; win rate 0.193878; average winner / loser 3.244737 / -1.463420 R.
Conditional CLOSED-only DD 114.066667 R; largest winner share 0.135172; largest positive month share 0.953307. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 17 | -11.466667 | 0.374545 | 0.324675 | 5 | 0 | 1 |
| 2023-02 | 12 | 0.800000 | 1.058252 | 1.214286 | 4 | 0 | 0 |
| 2023-03 | 24 | 16.333333 | 1.698006 | 1.717647 | 3 | 0 | 2 |
| 2023-04 | 16 | -22.383333 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 16 | -14.333333 | 0.340996 | 0.273810 | 3 | 0 | 1 |
| 2023-06 | 11 | -10.450000 | 0.177165 | 0.176471 | 4 | 0 | 0 |
| 2023-07 | 14 | -3.300000 | 0.763158 | 0.629630 | 1 | 0 | 0 |
| 2023-08 | 8 | -6.216667 | 0.293561 | 0.236842 | 2 | 0 | 0 |
| 2023-09 | 23 | -8.716667 | 0.658616 | 0.829787 | 2 | 0 | 0 |
| 2023-10 | 10 | -7.516667 | 0.378788 | 0.285714 | 0 | 0 | 0 |
| 2023-11 | 26 | -17.383333 | 0.378427 | 0.349057 | 1 | 0 | 0 |
| 2023-12 | 19 | -17.433333 | 0.295148 | 0.344828 | 0 | 0 | 0 |

### B_OPT2023_N5_W2_T2_SB1_TP2

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 261, entry dates 157, entry months 12; SKIP 4, EXCLUDED 3, exclusion share 0.011364; conditional FLAT CLOSED 234.
Net -151.350000 R; PF R / price 0.498924 / 0.512111; expectancy -0.579885 R; win rate 0.210728; average winner / loser 2.740000 / -1.495297 R.
Conditional CLOSED-only DD 154.250000 R; largest winner share 0.022119; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 12 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 25 | -20.800000 | 0.378486 | 0.372881 | 5 | 2 | 0 |
| 2023-02 | 18 | -14.300000 | 0.389758 | 0.418605 | 4 | 0 | 1 |
| 2023-03 | 32 | -13.866667 | 0.612663 | 0.605839 | 3 | 0 | 1 |
| 2023-04 | 21 | -6.766667 | 0.695652 | 0.666667 | 5 | 1 | 1 |
| 2023-05 | 18 | -5.100000 | 0.723327 | 0.647887 | 3 | 1 | 0 |
| 2023-06 | 17 | -11.466667 | 0.443366 | 0.455696 | 4 | 0 | 0 |
| 2023-07 | 17 | -0.333333 | 0.978632 | 0.923077 | 1 | 0 | 0 |
| 2023-08 | 14 | -12.066667 | 0.336996 | 0.333333 | 2 | 0 | 0 |
| 2023-09 | 28 | -31.366667 | 0.165040 | 0.195804 | 2 | 0 | 0 |
| 2023-10 | 16 | -7.100000 | 0.603352 | 0.672131 | 0 | 0 | 0 |
| 2023-11 | 29 | -11.483333 | 0.585689 | 0.625000 | 1 | 0 | 0 |
| 2023-12 | 26 | -16.700000 | 0.463023 | 0.528000 | 0 | 0 | 0 |

### B_OPT2023_N5_W2_T2_SB1_TP3

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 258, entry dates 157, entry months 12; SKIP 4, EXCLUDED 3, exclusion share 0.011494; conditional FLAT CLOSED 231.
Net -133.416667 R; PF R / price 0.567928 / 0.583756; expectancy -0.517119 R; win rate 0.178295; average winner / loser 3.812319 / -1.484535 R.
Conditional CLOSED-only DD 136.216667 R; largest winner share 0.028512; largest positive month share 0.579545. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 25 | -20.466667 | 0.414681 | 0.387097 | 5 | 2 | 0 |
| 2023-02 | 17 | -10.266667 | 0.528331 | 0.530864 | 4 | 0 | 1 |
| 2023-03 | 32 | -7.866667 | 0.783883 | 0.735714 | 3 | 0 | 1 |
| 2023-04 | 20 | -13.700000 | 0.426778 | 0.489130 | 5 | 1 | 1 |
| 2023-05 | 18 | 1.233333 | 1.066908 | 0.957746 | 3 | 1 | 0 |
| 2023-06 | 17 | -8.500000 | 0.587379 | 0.582278 | 4 | 0 | 0 |
| 2023-07 | 17 | 1.700000 | 1.100000 | 0.958333 | 1 | 0 | 0 |
| 2023-08 | 14 | -9.000000 | 0.505495 | 0.500000 | 2 | 0 | 0 |
| 2023-09 | 28 | -28.466667 | 0.242236 | 0.286713 | 2 | 0 | 0 |
| 2023-10 | 15 | -13.800000 | 0.298305 | 0.400000 | 0 | 0 | 0 |
| 2023-11 | 29 | -9.783333 | 0.655314 | 0.763158 | 1 | 0 | 0 |
| 2023-12 | 26 | -14.500000 | 0.545455 | 0.604651 | 0 | 0 | 0 |

### B_OPT2023_N5_W2_T2_SB1_TP4

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 254, entry dates 157, entry months 12; SKIP 4, EXCLUDED 3, exclusion share 0.011673; conditional FLAT CLOSED 228.
Net -132.616667 R; PF R / price 0.570287 / 0.569738; expectancy -0.522113 R; win rate 0.161417; average winner / loser 4.292683 / -1.483734 R.
Conditional CLOSED-only DD 134.816667 R; largest winner share 0.037879; largest positive month share 0.521839. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 24 | -16.050000 | 0.518018 | 0.478992 | 5 | 2 | 0 |
| 2023-02 | 17 | -8.766667 | 0.597243 | 0.604938 | 4 | 0 | 1 |
| 2023-03 | 32 | -9.066667 | 0.750916 | 0.635714 | 3 | 0 | 1 |
| 2023-04 | 20 | -13.400000 | 0.439331 | 0.489130 | 5 | 1 | 1 |
| 2023-05 | 18 | 7.566667 | 1.410488 | 1.267606 | 3 | 1 | 0 |
| 2023-06 | 16 | -11.166667 | 0.453507 | 0.412500 | 4 | 0 | 0 |
| 2023-07 | 17 | 6.933333 | 1.407843 | 1.236111 | 1 | 0 | 0 |
| 2023-08 | 13 | -19.766667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 28 | -37.466667 | 0.040956 | 0.053691 | 2 | 0 | 0 |
| 2023-10 | 15 | -12.400000 | 0.369492 | 0.507692 | 0 | 0 | 0 |
| 2023-11 | 28 | -8.333333 | 0.691167 | 0.813084 | 1 | 0 | 0 |
| 2023-12 | 26 | -10.700000 | 0.664577 | 0.728682 | 0 | 0 | 0 |

### B_OPT2023_N5_W2_T2_SB1_TP5

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 252, entry dates 156, entry months 12; SKIP 4, EXCLUDED 4, exclusion share 0.015625; conditional FLAT CLOSED 226.
Net -144.966667 R; PF R / price 0.530269 / 0.522401; expectancy -0.575265 R; win rate 0.150794; average winner / loser 4.306579 / -1.483734 R.
Conditional CLOSED-only DD 147.166667 R; largest winner share 0.050922; largest positive month share 0.526627. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 24 | -14.383333 | 0.568068 | 0.521008 | 5 | 2 | 0 |
| 2023-02 | 17 | -7.266667 | 0.666156 | 0.679012 | 4 | 0 | 1 |
| 2023-03 | 32 | -3.566667 | 0.902015 | 0.757143 | 3 | 0 | 1 |
| 2023-04 | 20 | -17.650000 | 0.261506 | 0.304348 | 5 | 1 | 1 |
| 2023-05 | 18 | 8.900000 | 1.482821 | 1.366197 | 3 | 1 | 0 |
| 2023-06 | 15 | -17.833333 | 0.127243 | 0.162500 | 4 | 0 | 1 |
| 2023-07 | 17 | 8.000000 | 1.470588 | 1.291667 | 1 | 0 | 0 |
| 2023-08 | 13 | -19.766667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 28 | -37.466667 | 0.040956 | 0.053691 | 2 | 0 | 0 |
| 2023-10 | 15 | -19.400000 | 0.079114 | 0.069444 | 0 | 0 | 0 |
| 2023-11 | 28 | -6.933333 | 0.743051 | 0.878505 | 1 | 0 | 0 |
| 2023-12 | 25 | -17.600000 | 0.422951 | 0.467213 | 0 | 0 | 0 |

### B_OPT2023_N5_W2_T2_SB1_TP6

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 251, entry dates 156, entry months 12; SKIP 4, EXCLUDED 4, exclusion share 0.015686; conditional FLAT CLOSED 225.
Net -143.133333 R; PF R / price 0.538304 / 0.520168; expectancy -0.570252 R; win rate 0.143426; average winner / loser 4.635648 / -1.483333 R.
Conditional CLOSED-only DD 145.333333 R; largest winner share 0.059922; largest positive month share 0.541223. Positive / negative / zero months 3 / 9 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 24 | -16.383333 | 0.508008 | 0.470588 | 5 | 2 | 0 |
| 2023-02 | 17 | -8.266667 | 0.620214 | 0.629630 | 4 | 0 | 1 |
| 2023-03 | 31 | 0.433333 | 1.011905 | 0.835714 | 3 | 0 | 1 |
| 2023-04 | 20 | -17.650000 | 0.261506 | 0.304348 | 5 | 1 | 1 |
| 2023-05 | 18 | 13.566667 | 1.735986 | 1.605634 | 3 | 1 | 0 |
| 2023-06 | 15 | -17.833333 | 0.127243 | 0.162500 | 4 | 0 | 1 |
| 2023-07 | 17 | 11.066667 | 1.650980 | 1.458333 | 1 | 0 | 0 |
| 2023-08 | 13 | -19.766667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 28 | -37.466667 | 0.040956 | 0.053691 | 2 | 0 | 0 |
| 2023-10 | 15 | -19.400000 | 0.079114 | 0.069444 | 0 | 0 | 0 |
| 2023-11 | 28 | -15.333333 | 0.459777 | 0.517544 | 1 | 0 | 0 |
| 2023-12 | 25 | -16.100000 | 0.472131 | 0.516393 | 0 | 0 | 0 |

### B_OPT2023_N5_W2_T2_SB1_TP7

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 251, entry dates 156, entry months 12; SKIP 4, EXCLUDED 4, exclusion share 0.015686; conditional FLAT CLOSED 225.
Net -148.483333 R; PF R / price 0.521047 / 0.503361; expectancy -0.591567 R; win rate 0.143426; average winner / loser 4.487037 / -1.483333 R.
Conditional CLOSED-only DD 150.683333 R; largest winner share 0.072225; largest positive month share 0.628217. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 24 | -16.383333 | 0.508008 | 0.470588 | 5 | 2 | 0 |
| 2023-02 | 17 | -8.266667 | 0.620214 | 0.629630 | 4 | 0 | 1 |
| 2023-03 | 31 | -0.566667 | 0.984432 | 0.814286 | 3 | 0 | 1 |
| 2023-04 | 20 | -17.650000 | 0.261506 | 0.304348 | 5 | 1 | 1 |
| 2023-05 | 18 | 6.983333 | 1.378843 | 1.211268 | 3 | 1 | 0 |
| 2023-06 | 15 | -17.833333 | 0.127243 | 0.162500 | 4 | 0 | 1 |
| 2023-07 | 17 | 11.800000 | 1.694118 | 1.527778 | 1 | 0 | 0 |
| 2023-08 | 13 | -19.766667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 28 | -37.466667 | 0.040956 | 0.053691 | 2 | 0 | 0 |
| 2023-10 | 15 | -19.400000 | 0.079114 | 0.069444 | 0 | 0 | 0 |
| 2023-11 | 28 | -15.333333 | 0.459777 | 0.517544 | 1 | 0 | 0 |
| 2023-12 | 25 | -14.600000 | 0.521311 | 0.565574 | 0 | 0 | 0 |

### B_OPT2023_N5_W2_T2_SB1_TP8

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 251, entry dates 156, entry months 12; SKIP 4, EXCLUDED 4, exclusion share 0.015686; conditional FLAT CLOSED 225.
Net -140.583333 R; PF R / price 0.546530 / 0.526891; expectancy -0.560093 R; win rate 0.143426; average winner / loser 4.706481 / -1.483333 R.
Conditional CLOSED-only DD 142.783333 R; largest winner share 0.078694; largest positive month share 0.536222. Positive / negative / zero months 3 / 9 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 24 | -16.383333 | 0.508008 | 0.470588 | 5 | 2 | 0 |
| 2023-02 | 17 | -8.266667 | 0.620214 | 0.629630 | 4 | 0 | 1 |
| 2023-03 | 31 | 2.766667 | 1.076007 | 0.885714 | 3 | 0 | 1 |
| 2023-04 | 20 | -17.650000 | 0.261506 | 0.304348 | 5 | 1 | 1 |
| 2023-05 | 18 | 8.650000 | 1.469259 | 1.281690 | 3 | 1 | 0 |
| 2023-06 | 15 | -17.833333 | 0.127243 | 0.162500 | 4 | 0 | 1 |
| 2023-07 | 17 | 13.200000 | 1.776471 | 1.625000 | 1 | 0 | 0 |
| 2023-08 | 13 | -19.766667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 28 | -37.466667 | 0.040956 | 0.053691 | 2 | 0 | 0 |
| 2023-10 | 15 | -19.400000 | 0.079114 | 0.069444 | 0 | 0 | 0 |
| 2023-11 | 28 | -15.333333 | 0.459777 | 0.517544 | 1 | 0 | 0 |
| 2023-12 | 25 | -13.100000 | 0.570492 | 0.614754 | 0 | 0 | 0 |

### B_OPT2023_N5_W2_T2_SB1_TP9

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors.
CLOSED 251, entry dates 156, entry months 12; SKIP 4, EXCLUDED 4, exclusion share 0.015686; conditional FLAT CLOSED 225.
Net -134.083333 R; PF R / price 0.567496 / 0.544538; expectancy -0.534197 R; win rate 0.143426; average winner / loser 4.887037 / -1.483333 R.
Conditional CLOSED-only DD 136.283333 R; largest winner share 0.085260; largest positive month share 0.445695. Positive / negative / zero months 3 / 9 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 24 | -16.383333 | 0.508008 | 0.470588 | 5 | 2 | 0 |
| 2023-02 | 17 | -8.266667 | 0.620214 | 0.629630 | 4 | 0 | 1 |
| 2023-03 | 31 | 6.100000 | 1.167582 | 0.957143 | 3 | 0 | 1 |
| 2023-04 | 20 | -17.650000 | 0.261506 | 0.304348 | 5 | 1 | 1 |
| 2023-05 | 18 | 10.316667 | 1.559675 | 1.352113 | 3 | 1 | 0 |
| 2023-06 | 15 | -17.833333 | 0.127243 | 0.162500 | 4 | 0 | 1 |
| 2023-07 | 17 | 13.200000 | 1.776471 | 1.625000 | 1 | 0 | 0 |
| 2023-08 | 13 | -19.766667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 28 | -37.466667 | 0.040956 | 0.053691 | 2 | 0 | 0 |
| 2023-10 | 15 | -19.400000 | 0.079114 | 0.069444 | 0 | 0 | 0 |
| 2023-11 | 28 | -15.333333 | 0.459777 | 0.517544 | 1 | 0 | 0 |
| 2023-12 | 25 | -11.600000 | 0.619672 | 0.663934 | 0 | 0 | 0 |

### B_OPT2023_N5_W2_T2_SB1_TP10

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors.
CLOSED 251, entry dates 156, entry months 12; SKIP 4, EXCLUDED 4, exclusion share 0.015686; conditional FLAT CLOSED 225.
Net -127.583333 R; PF R / price 0.588463 / 0.562185; expectancy -0.508300 R; win rate 0.143426; average winner / loser 5.067593 / -1.483333 R.
Conditional CLOSED-only DD 129.783333 R; largest winner share 0.091358; largest positive month share 0.381319. Positive / negative / zero months 3 / 9 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 24 | -16.383333 | 0.508008 | 0.470588 | 5 | 2 | 0 |
| 2023-02 | 17 | -8.266667 | 0.620214 | 0.629630 | 4 | 0 | 1 |
| 2023-03 | 31 | 9.433333 | 1.259158 | 1.028571 | 3 | 0 | 1 |
| 2023-04 | 20 | -17.650000 | 0.261506 | 0.304348 | 5 | 1 | 1 |
| 2023-05 | 18 | 11.983333 | 1.650090 | 1.422535 | 3 | 1 | 0 |
| 2023-06 | 15 | -17.833333 | 0.127243 | 0.162500 | 4 | 0 | 1 |
| 2023-07 | 17 | 13.200000 | 1.776471 | 1.625000 | 1 | 0 | 0 |
| 2023-08 | 13 | -19.766667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 28 | -37.466667 | 0.040956 | 0.053691 | 2 | 0 | 0 |
| 2023-10 | 15 | -19.400000 | 0.079114 | 0.069444 | 0 | 0 | 0 |
| 2023-11 | 28 | -15.333333 | 0.459777 | 0.517544 | 1 | 0 | 0 |
| 2023-12 | 25 | -10.100000 | 0.668852 | 0.713115 | 0 | 0 | 0 |

### B_OPT2023_N5_W2_T3_SB1_TP2

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 122, entry dates 94, entry months 12; SKIP 0, EXCLUDED 1, exclusion share 0.008130; conditional FLAT CLOSED 80.
Net -53.883333 R; PF R / price 0.590500 / 0.616327; expectancy -0.441667 R; win rate 0.229508; average winner / loser 2.775000 / -1.462037 R.
Conditional CLOSED-only DD 57.816667 R; largest winner share 0.042900; largest positive month share 0.604651. Positive / negative / zero months 3 / 9 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 13 | -9.000000 | 0.425532 | 0.410714 | 5 | 0 | 0 |
| 2023-02 | 11 | -12.666667 | 0.181034 | 0.241379 | 4 | 0 | 0 |
| 2023-03 | 18 | -5.166667 | 0.712430 | 0.758065 | 3 | 0 | 1 |
| 2023-04 | 13 | -8.083333 | 0.431419 | 0.436364 | 5 | 0 | 0 |
| 2023-05 | 8 | -2.633333 | 0.716846 | 0.571429 | 3 | 0 | 0 |
| 2023-06 | 6 | 0.566667 | 1.108280 | 1.300000 | 4 | 0 | 0 |
| 2023-07 | 8 | 3.400000 | 1.560440 | 1.416667 | 1 | 0 | 0 |
| 2023-08 | 6 | -7.866667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 12 | -8.900000 | 0.394558 | 0.481481 | 2 | 0 | 0 |
| 2023-10 | 6 | 6.066667 | 2.978261 | 3.000000 | 0 | 0 | 0 |
| 2023-11 | 10 | -5.800000 | 0.397924 | 0.315789 | 1 | 0 | 0 |
| 2023-12 | 11 | -3.800000 | 0.693548 | 0.869565 | 0 | 0 | 0 |

### B_OPT2023_N5_W2_T3_SB1_TP3

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 121, entry dates 94, entry months 12; SKIP 0, EXCLUDED 1, exclusion share 0.008197; conditional FLAT CLOSED 80.
Net -46.216667 R; PF R / price 0.660130 / 0.666012; expectancy -0.381956 R; win rate 0.190083; average winner / loser 3.902899 / -1.446631 R.
Conditional CLOSED-only DD 47.950000 R; largest winner share 0.055700; largest positive month share 0.530435. Positive / negative / zero months 4 / 8 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 13 | -11.833333 | 0.310680 | 0.258065 | 5 | 0 | 0 |
| 2023-02 | 10 | -11.800000 | 0.144928 | 0.188679 | 4 | 0 | 0 |
| 2023-03 | 18 | -3.733333 | 0.798923 | 0.753846 | 3 | 0 | 1 |
| 2023-04 | 13 | -11.683333 | 0.264428 | 0.350000 | 5 | 0 | 0 |
| 2023-05 | 8 | 0.700000 | 1.075269 | 0.857143 | 3 | 0 | 0 |
| 2023-06 | 6 | 1.866667 | 1.356688 | 1.550000 | 4 | 0 | 0 |
| 2023-07 | 8 | 8.133333 | 2.340659 | 2.125000 | 1 | 0 | 0 |
| 2023-08 | 6 | -7.866667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 12 | -6.000000 | 0.591837 | 0.722222 | 2 | 0 | 0 |
| 2023-10 | 6 | 4.633333 | 2.014599 | 2.000000 | 0 | 0 | 0 |
| 2023-11 | 10 | -4.133333 | 0.570934 | 0.447368 | 1 | 0 | 0 |
| 2023-12 | 11 | -4.500000 | 0.659091 | 0.780000 | 0 | 0 | 0 |

### B_OPT2023_N5_W2_T3_SB1_TP4

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 121, entry dates 94, entry months 12; SKIP 0, EXCLUDED 1, exclusion share 0.008197; conditional FLAT CLOSED 80.
Net -46.216667 R; PF R / price 0.667466 / 0.646833; expectancy -0.381956 R; win rate 0.173554; average winner / loser 4.417460 / -1.447743 R.
Conditional CLOSED-only DD 50.850000 R; largest winner share 0.071865; largest positive month share 0.502825. Positive / negative / zero months 3 / 9 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 13 | -10.166667 | 0.407767 | 0.338710 | 5 | 0 | 0 |
| 2023-02 | 10 | -11.800000 | 0.144928 | 0.188679 | 4 | 0 | 0 |
| 2023-03 | 18 | -3.900000 | 0.789946 | 0.692308 | 3 | 0 | 1 |
| 2023-04 | 13 | -12.883333 | 0.188877 | 0.250000 | 5 | 0 | 0 |
| 2023-05 | 8 | 4.033333 | 1.433692 | 1.142857 | 3 | 0 | 0 |
| 2023-06 | 6 | -4.133333 | 0.386139 | 0.500000 | 4 | 0 | 0 |
| 2023-07 | 8 | 11.866667 | 2.956044 | 2.708333 | 1 | 0 | 0 |
| 2023-08 | 6 | -7.866667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 12 | -15.000000 | 0.074074 | 0.100000 | 2 | 0 | 0 |
| 2023-10 | 6 | 7.700000 | 2.686131 | 2.666667 | 0 | 0 | 0 |
| 2023-11 | 10 | -2.466667 | 0.743945 | 0.578947 | 1 | 0 | 0 |
| 2023-12 | 11 | -1.600000 | 0.878788 | 1.040000 | 0 | 0 | 0 |

### B_OPT2023_N5_W2_T3_SB1_TP5

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 121, entry dates 94, entry months 12; SKIP 0, EXCLUDED 1, exclusion share 0.008197; conditional FLAT CLOSED 80.
Net -40.783333 R; PF R / price 0.709486 / 0.649621; expectancy -0.337052 R; win rate 0.165289; average winner / loser 4.980000 / -1.447251 R.
Conditional CLOSED-only DD 43.116667 R; largest winner share 0.083668; largest positive month share 0.605405. Positive / negative / zero months 3 / 9 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 13 | -8.500000 | 0.504854 | 0.419355 | 5 | 0 | 0 |
| 2023-02 | 10 | -11.800000 | 0.144928 | 0.188679 | 4 | 0 | 0 |
| 2023-03 | 18 | -0.566667 | 0.969479 | 0.846154 | 3 | 0 | 1 |
| 2023-04 | 13 | -12.883333 | 0.188877 | 0.250000 | 5 | 0 | 0 |
| 2023-05 | 8 | 7.366667 | 1.792115 | 1.428571 | 3 | 0 | 0 |
| 2023-06 | 6 | -4.133333 | 0.386139 | 0.500000 | 4 | 0 | 0 |
| 2023-07 | 8 | 14.933333 | 3.461538 | 3.208333 | 1 | 0 | 0 |
| 2023-08 | 6 | -7.866667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 12 | -15.000000 | 0.074074 | 0.100000 | 2 | 0 | 0 |
| 2023-10 | 6 | 2.366667 | 1.396648 | 1.000000 | 0 | 0 | 0 |
| 2023-11 | 10 | -0.800000 | 0.916955 | 0.710526 | 1 | 0 | 0 |
| 2023-12 | 11 | -3.900000 | 0.704545 | 0.780000 | 0 | 0 | 0 |

### B_OPT2023_N5_W2_T3_SB1_TP6

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 120, entry dates 94, entry months 12; SKIP 0, EXCLUDED 1, exclusion share 0.008264; conditional FLAT CLOSED 80.
Net -29.216667 R; PF R / price 0.791879 / 0.721591; expectancy -0.243472 R; win rate 0.158333; average winner / loser 5.850877 / -1.447251 R.
Conditional CLOSED-only DD 36.483333 R; largest winner share 0.089955; largest positive month share 0.508954. Positive / negative / zero months 5 / 7 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 13 | -10.500000 | 0.388350 | 0.322581 | 5 | 0 | 0 |
| 2023-02 | 10 | -11.800000 | 0.144928 | 0.188679 | 4 | 0 | 0 |
| 2023-03 | 17 | 1.766667 | 1.095153 | 0.938462 | 3 | 0 | 1 |
| 2023-04 | 13 | -12.883333 | 0.188877 | 0.250000 | 5 | 0 | 0 |
| 2023-05 | 8 | 10.700000 | 2.150538 | 1.714286 | 3 | 0 | 0 |
| 2023-06 | 6 | -4.133333 | 0.386139 | 0.500000 | 4 | 0 | 0 |
| 2023-07 | 8 | 18.000000 | 3.967033 | 3.708333 | 1 | 0 | 0 |
| 2023-08 | 6 | -7.866667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 12 | -15.000000 | 0.074074 | 0.100000 | 2 | 0 | 0 |
| 2023-10 | 6 | 4.033333 | 1.675978 | 1.200000 | 0 | 0 | 0 |
| 2023-11 | 10 | 0.866667 | 1.089965 | 0.842105 | 1 | 0 | 0 |
| 2023-12 | 11 | -2.400000 | 0.818182 | 0.900000 | 0 | 0 | 0 |

### B_OPT2023_N5_W2_T3_SB1_TP7

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors.
CLOSED 120, entry dates 94, entry months 12; SKIP 0, EXCLUDED 1, exclusion share 0.008264; conditional FLAT CLOSED 80.
Net -26.316667 R; PF R / price 0.812537 / 0.746212; expectancy -0.219306 R; win rate 0.158333; average winner / loser 6.003509 / -1.447251 R.
Conditional CLOSED-only DD 39.150000 R; largest winner share 0.102279; largest positive month share 0.487002. Positive / negative / zero months 3 / 9 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 13 | -10.500000 | 0.388350 | 0.322581 | 5 | 0 | 0 |
| 2023-02 | 10 | -11.800000 | 0.144928 | 0.188679 | 4 | 0 | 0 |
| 2023-03 | 17 | -0.900000 | 0.951526 | 0.815385 | 3 | 0 | 1 |
| 2023-04 | 13 | -12.883333 | 0.188877 | 0.250000 | 5 | 0 | 0 |
| 2023-05 | 8 | 14.033333 | 2.508961 | 2.000000 | 3 | 0 | 0 |
| 2023-06 | 6 | -4.133333 | 0.386139 | 0.500000 | 4 | 0 | 0 |
| 2023-07 | 8 | 18.733333 | 4.087912 | 3.916667 | 1 | 0 | 0 |
| 2023-08 | 6 | -7.866667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 12 | -15.000000 | 0.074074 | 0.100000 | 2 | 0 | 0 |
| 2023-10 | 6 | 5.700000 | 1.955307 | 1.400000 | 0 | 0 | 0 |
| 2023-11 | 10 | -0.800000 | 0.916955 | 0.710526 | 1 | 0 | 0 |
| 2023-12 | 11 | -0.900000 | 0.931818 | 1.020000 | 0 | 0 | 0 |

### B_OPT2023_N5_W2_T3_SB1_TP8

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors.
CLOSED 120, entry dates 94, entry months 12; SKIP 0, EXCLUDED 1, exclusion share 0.008264; conditional FLAT CLOSED 80.
Net -20.416667 R; PF R / price 0.854565 / 0.787879; expectancy -0.170139 R; win rate 0.158333; average winner / loser 6.314035 / -1.447251 R.
Conditional CLOSED-only DD 37.483333 R; largest winner share 0.111142; largest positive month share 0.472984. Positive / negative / zero months 5 / 7 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 13 | -10.500000 | 0.388350 | 0.322581 | 5 | 0 | 0 |
| 2023-02 | 10 | -11.800000 | 0.144928 | 0.188679 | 4 | 0 | 0 |
| 2023-03 | 17 | 0.766667 | 1.041293 | 0.892308 | 3 | 0 | 1 |
| 2023-04 | 13 | -12.883333 | 0.188877 | 0.250000 | 5 | 0 | 0 |
| 2023-05 | 8 | 13.700000 | 2.473118 | 1.971429 | 3 | 0 | 0 |
| 2023-06 | 6 | -4.133333 | 0.386139 | 0.500000 | 4 | 0 | 0 |
| 2023-07 | 8 | 20.133333 | 4.318681 | 4.208333 | 1 | 0 | 0 |
| 2023-08 | 6 | -7.866667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 12 | -15.000000 | 0.074074 | 0.100000 | 2 | 0 | 0 |
| 2023-10 | 6 | 7.366667 | 2.234637 | 1.600000 | 0 | 0 | 0 |
| 2023-11 | 10 | -0.800000 | 0.916955 | 0.710526 | 1 | 0 | 0 |
| 2023-12 | 11 | 0.600000 | 1.045455 | 1.140000 | 0 | 0 | 0 |

### B_OPT2023_N5_W2_T3_SB1_TP9

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 120, entry dates 94, entry months 12; SKIP 0, EXCLUDED 1, exclusion share 0.008264; conditional FLAT CLOSED 80.
Net -24.583333 R; PF R / price 0.824884 / 0.767045; expectancy -0.204861 R; win rate 0.158333; average winner / loser 6.094737 / -1.447251 R.
Conditional CLOSED-only DD 35.816667 R; largest winner share 0.129534; largest positive month share 0.502914. Positive / negative / zero months 4 / 8 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 13 | -10.500000 | 0.388350 | 0.322581 | 5 | 0 | 0 |
| 2023-02 | 10 | -11.800000 | 0.144928 | 0.188679 | 4 | 0 | 0 |
| 2023-03 | 17 | 2.433333 | 1.131059 | 0.969231 | 3 | 0 | 1 |
| 2023-04 | 13 | -12.883333 | 0.188877 | 0.250000 | 5 | 0 | 0 |
| 2023-05 | 8 | 15.366667 | 2.652330 | 2.114286 | 3 | 0 | 0 |
| 2023-06 | 6 | -4.133333 | 0.386139 | 0.500000 | 4 | 0 | 0 |
| 2023-07 | 8 | 20.133333 | 4.318681 | 4.208333 | 1 | 0 | 0 |
| 2023-08 | 6 | -7.866667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 12 | -15.000000 | 0.074074 | 0.100000 | 2 | 0 | 0 |
| 2023-10 | 6 | -1.633333 | 0.726257 | 0.520000 | 0 | 0 | 0 |
| 2023-11 | 10 | -0.800000 | 0.916955 | 0.710526 | 1 | 0 | 0 |
| 2023-12 | 11 | 2.100000 | 1.159091 | 1.260000 | 0 | 0 | 0 |

### B_OPT2023_N5_W2_T3_SB1_TP10

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors.
CLOSED 120, entry dates 94, entry months 12; SKIP 0, EXCLUDED 1, exclusion share 0.008264; conditional FLAT CLOSED 80.
Net -19.750000 R; PF R / price 0.859314 / 0.797348; expectancy -0.164583 R; win rate 0.158333; average winner / loser 6.349123 / -1.447251 R.
Conditional CLOSED-only DD 34.150000 R; largest winner share 0.138160; largest positive month share 0.448737. Positive / negative / zero months 4 / 8 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 13 | -10.500000 | 0.388350 | 0.322581 | 5 | 0 | 0 |
| 2023-02 | 10 | -11.800000 | 0.144928 | 0.188679 | 4 | 0 | 0 |
| 2023-03 | 17 | 4.100000 | 1.220826 | 1.046154 | 3 | 0 | 1 |
| 2023-04 | 13 | -12.883333 | 0.188877 | 0.250000 | 5 | 0 | 0 |
| 2023-05 | 8 | 17.033333 | 2.831541 | 2.257143 | 3 | 0 | 0 |
| 2023-06 | 6 | -4.133333 | 0.386139 | 0.500000 | 4 | 0 | 0 |
| 2023-07 | 8 | 20.133333 | 4.318681 | 4.208333 | 1 | 0 | 0 |
| 2023-08 | 6 | -7.866667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 12 | -15.000000 | 0.074074 | 0.100000 | 2 | 0 | 0 |
| 2023-10 | 6 | -1.633333 | 0.726257 | 0.520000 | 0 | 0 | 0 |
| 2023-11 | 10 | -0.800000 | 0.916955 | 0.710526 | 1 | 0 | 0 |
| 2023-12 | 11 | 3.600000 | 1.272727 | 1.380000 | 0 | 0 | 0 |

### B_OPT2023_N5_W3_T2_SB1_TP2

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 357, entry dates 184, entry months 12; SKIP 2, EXCLUDED 3, exclusion share 0.008333; conditional FLAT CLOSED 252.
Net -210.233333 R; PF R / price 0.486756 / 0.500316; expectancy -0.588889 R; win rate 0.215686; average winner / loser 2.589394 / -1.484118 R.
Conditional CLOSED-only DD 216.433333 R; largest winner share 0.016718; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 12 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 31 | -19.583333 | 0.465423 | 0.435714 | 5 | 0 | 0 |
| 2023-02 | 29 | -29.516667 | 0.225623 | 0.270270 | 4 | 1 | 0 |
| 2023-03 | 45 | -27.500000 | 0.480806 | 0.443902 | 3 | 0 | 1 |
| 2023-04 | 30 | -18.466667 | 0.462136 | 0.441176 | 5 | 0 | 1 |
| 2023-05 | 24 | -3.366667 | 0.861454 | 0.898876 | 3 | 1 | 0 |
| 2023-06 | 27 | -7.150000 | 0.746154 | 0.761468 | 4 | 0 | 1 |
| 2023-07 | 24 | -9.216667 | 0.641839 | 0.631068 | 1 | 0 | 0 |
| 2023-08 | 22 | -24.266667 | 0.201754 | 0.200000 | 2 | 0 | 0 |
| 2023-09 | 30 | -21.700000 | 0.415619 | 0.457143 | 2 | 0 | 0 |
| 2023-10 | 27 | -20.116667 | 0.363061 | 0.391667 | 0 | 0 | 0 |
| 2023-11 | 38 | -21.016667 | 0.480429 | 0.512821 | 1 | 0 | 0 |
| 2023-12 | 30 | -8.333333 | 0.720358 | 0.829060 | 0 | 0 | 0 |

### B_OPT2023_N5_W3_T2_SB1_TP3

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 349, entry dates 184, entry months 12; SKIP 2, EXCLUDED 4, exclusion share 0.011331; conditional FLAT CLOSED 248.
Net -185.800000 R; PF R / price 0.546811 / 0.565657; expectancy -0.532378 R; win rate 0.191977; average winner / loser 3.346020 / -1.474760 R.
Conditional CLOSED-only DD 192.800000 R; largest winner share 0.022303; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 28 | -22.616667 | 0.334151 | 0.317829 | 5 | 0 | 0 |
| 2023-02 | 28 | -28.950000 | 0.205761 | 0.230769 | 4 | 1 | 0 |
| 2023-03 | 45 | -14.933333 | 0.718062 | 0.663415 | 3 | 0 | 1 |
| 2023-04 | 29 | -25.400000 | 0.294444 | 0.333333 | 5 | 0 | 1 |
| 2023-05 | 22 | 3.066667 | 1.134503 | 1.144578 | 3 | 1 | 1 |
| 2023-06 | 27 | -6.283333 | 0.789385 | 0.842105 | 4 | 0 | 1 |
| 2023-07 | 24 | -7.183333 | 0.735258 | 0.672727 | 1 | 0 | 0 |
| 2023-08 | 22 | -21.200000 | 0.302632 | 0.300000 | 2 | 0 | 0 |
| 2023-09 | 30 | -15.633333 | 0.578995 | 0.628571 | 2 | 0 | 0 |
| 2023-10 | 27 | -21.716667 | 0.343577 | 0.380952 | 0 | 0 | 0 |
| 2023-11 | 38 | -23.216667 | 0.435347 | 0.506329 | 1 | 0 | 0 |
| 2023-12 | 29 | -1.733333 | 0.940435 | 1.060870 | 0 | 0 | 0 |

### B_OPT2023_N5_W3_T2_SB1_TP4

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 344, entry dates 184, entry months 12; SKIP 2, EXCLUDED 4, exclusion share 0.011494; conditional FLAT CLOSED 244.
Net -189.283333 R; PF R / price 0.536544 / 0.547529; expectancy -0.550242 R; win rate 0.174419; average winner / loser 3.652222 / -1.474428 R.
Conditional CLOSED-only DD 198.950000 R; largest winner share 0.030423; largest positive month share 0.864553. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 27 | -17.783333 | 0.449432 | 0.419355 | 5 | 0 | 0 |
| 2023-02 | 28 | -27.450000 | 0.246914 | 0.272727 | 4 | 1 | 0 |
| 2023-03 | 45 | -19.633333 | 0.629327 | 0.551220 | 3 | 0 | 1 |
| 2023-04 | 29 | -25.100000 | 0.302778 | 0.333333 | 5 | 0 | 1 |
| 2023-05 | 22 | 10.000000 | 1.438596 | 1.445783 | 3 | 1 | 1 |
| 2023-06 | 26 | -8.250000 | 0.721910 | 0.739130 | 4 | 0 | 1 |
| 2023-07 | 24 | -1.950000 | 0.928133 | 0.854545 | 1 | 0 | 0 |
| 2023-08 | 21 | -31.966667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 30 | -28.133333 | 0.271786 | 0.315068 | 2 | 0 | 0 |
| 2023-10 | 27 | -18.816667 | 0.431234 | 0.484127 | 0 | 0 | 0 |
| 2023-11 | 36 | -21.766667 | 0.431927 | 0.506944 | 1 | 0 | 0 |
| 2023-12 | 29 | 1.566667 | 1.053837 | 1.165217 | 0 | 0 | 0 |

### B_OPT2023_N5_W3_T2_SB1_TP5

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 342, entry dates 183, entry months 12; SKIP 2, EXCLUDED 5, exclusion share 0.014409; conditional FLAT CLOSED 242.
Net -207.816667 R; PF R / price 0.490833 / 0.497468; expectancy -0.607651 R; win rate 0.166667; average winner / loser 3.514620 / -1.473466 R.
Conditional CLOSED-only DD 214.883333 R; largest winner share 0.041597; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 27 | -18.616667 | 0.423633 | 0.379032 | 5 | 0 | 0 |
| 2023-02 | 28 | -25.950000 | 0.288066 | 0.314685 | 4 | 1 | 0 |
| 2023-03 | 45 | -19.133333 | 0.638767 | 0.536585 | 3 | 0 | 1 |
| 2023-04 | 29 | -29.350000 | 0.184722 | 0.212766 | 5 | 0 | 1 |
| 2023-05 | 22 | 11.333333 | 1.497076 | 1.530120 | 3 | 1 | 1 |
| 2023-06 | 25 | -13.416667 | 0.547753 | 0.617391 | 4 | 0 | 2 |
| 2023-07 | 24 | -0.883333 | 0.967445 | 0.890909 | 1 | 0 | 0 |
| 2023-08 | 21 | -31.966667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 29 | -30.966667 | 0.162308 | 0.198582 | 2 | 0 | 0 |
| 2023-10 | 27 | -27.066667 | 0.215080 | 0.210526 | 0 | 0 | 0 |
| 2023-11 | 36 | -21.766667 | 0.431927 | 0.506944 | 1 | 0 | 0 |
| 2023-12 | 29 | -0.033333 | 0.998855 | 1.121739 | 0 | 0 | 0 |

### B_OPT2023_N5_W3_T2_SB1_TP6

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 340, entry dates 183, entry months 12; SKIP 2, EXCLUDED 5, exclusion share 0.014493; conditional FLAT CLOSED 241.
Net -207.016667 R; PF R / price 0.490713 / 0.492063; expectancy -0.608873 R; win rate 0.164706; average winner / loser 3.561905 / -1.472766 R.
Conditional CLOSED-only DD 212.983333 R; largest winner share 0.050134; largest positive month share 0.804769. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 27 | -20.616667 | 0.361713 | 0.330645 | 5 | 0 | 0 |
| 2023-02 | 28 | -26.950000 | 0.260631 | 0.286713 | 4 | 1 | 0 |
| 2023-03 | 44 | -15.133333 | 0.714286 | 0.590244 | 3 | 0 | 1 |
| 2023-04 | 29 | -29.350000 | 0.184722 | 0.212766 | 5 | 0 | 1 |
| 2023-05 | 22 | 9.000000 | 1.394737 | 1.397590 | 3 | 1 | 1 |
| 2023-06 | 25 | -11.916667 | 0.598315 | 0.669565 | 4 | 0 | 2 |
| 2023-07 | 24 | 2.183333 | 1.080467 | 1.000000 | 1 | 0 | 0 |
| 2023-08 | 21 | -31.966667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 29 | -30.966667 | 0.162308 | 0.198582 | 2 | 0 | 0 |
| 2023-10 | 27 | -27.066667 | 0.215080 | 0.210526 | 0 | 0 | 0 |
| 2023-11 | 36 | -21.766667 | 0.431927 | 0.506944 | 1 | 0 | 0 |
| 2023-12 | 28 | -2.466667 | 0.910085 | 1.000000 | 0 | 0 | 0 |

### B_OPT2023_N5_W3_T2_SB1_TP7

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 340, entry dates 183, entry months 12; SKIP 2, EXCLUDED 5, exclusion share 0.014493; conditional FLAT CLOSED 241.
Net -209.616667 R; PF R / price 0.484317 / 0.486349; expectancy -0.616520 R; win rate 0.164706; average winner / loser 3.515476 / -1.472766 R.
Conditional CLOSED-only DD 217.083333 R; largest winner share 0.059262; largest positive month share 0.556962. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 27 | -20.616667 | 0.361713 | 0.330645 | 5 | 0 | 0 |
| 2023-02 | 28 | -26.950000 | 0.260631 | 0.286713 | 4 | 1 | 0 |
| 2023-03 | 44 | -16.133333 | 0.695406 | 0.575610 | 3 | 0 | 1 |
| 2023-04 | 29 | -29.350000 | 0.184722 | 0.212766 | 5 | 0 | 1 |
| 2023-05 | 22 | 3.666667 | 1.160819 | 1.120482 | 3 | 1 | 1 |
| 2023-06 | 25 | -10.416667 | 0.648876 | 0.721739 | 4 | 0 | 2 |
| 2023-07 | 24 | 2.916667 | 1.107494 | 1.045455 | 1 | 0 | 0 |
| 2023-08 | 21 | -31.966667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 29 | -30.966667 | 0.162308 | 0.198582 | 2 | 0 | 0 |
| 2023-10 | 27 | -27.066667 | 0.215080 | 0.210526 | 0 | 0 | 0 |
| 2023-11 | 36 | -21.766667 | 0.431927 | 0.506944 | 1 | 0 | 0 |
| 2023-12 | 28 | -0.966667 | 0.964763 | 1.054545 | 0 | 0 | 0 |

### B_OPT2023_N5_W3_T2_SB1_TP8

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 340, entry dates 183, entry months 12; SKIP 2, EXCLUDED 5, exclusion share 0.014493; conditional FLAT CLOSED 241.
Net -200.216667 R; PF R / price 0.507442 / 0.507937; expectancy -0.588873 R; win rate 0.164706; average winner / loser 3.683333 / -1.472766 R.
Conditional CLOSED-only DD 209.183333 R; largest winner share 0.064641; largest positive month share 0.523732. Positive / negative / zero months 3 / 9 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 27 | -20.616667 | 0.361713 | 0.330645 | 5 | 0 | 0 |
| 2023-02 | 28 | -26.950000 | 0.260631 | 0.286713 | 4 | 1 | 0 |
| 2023-03 | 44 | -12.800000 | 0.758339 | 0.624390 | 3 | 0 | 1 |
| 2023-04 | 29 | -29.350000 | 0.184722 | 0.212766 | 5 | 0 | 1 |
| 2023-05 | 22 | 5.333333 | 1.233918 | 1.180723 | 3 | 1 | 1 |
| 2023-06 | 25 | -8.916667 | 0.699438 | 0.773913 | 4 | 0 | 2 |
| 2023-07 | 24 | 4.316667 | 1.159091 | 1.109091 | 1 | 0 | 0 |
| 2023-08 | 21 | -31.966667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 29 | -30.966667 | 0.162308 | 0.198582 | 2 | 0 | 0 |
| 2023-10 | 27 | -27.066667 | 0.215080 | 0.210526 | 0 | 0 | 0 |
| 2023-11 | 36 | -21.766667 | 0.431927 | 0.506944 | 1 | 0 | 0 |
| 2023-12 | 28 | 0.533333 | 1.019441 | 1.109091 | 0 | 0 | 0 |

### B_OPT2023_N5_W3_T2_SB1_TP9

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 340, entry dates 183, entry months 12; SKIP 2, EXCLUDED 5, exclusion share 0.014493; conditional FLAT CLOSED 241.
Net -198.466667 R; PF R / price 0.511747 / 0.509206; expectancy -0.583725 R; win rate 0.164706; average winner / loser 3.714583 / -1.472766 R.
Conditional CLOSED-only DD 208.933333 R; largest winner share 0.072110; largest positive month share 0.524345. Positive / negative / zero months 3 / 9 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 27 | -20.616667 | 0.361713 | 0.330645 | 5 | 0 | 0 |
| 2023-02 | 28 | -26.950000 | 0.260631 | 0.286713 | 4 | 1 | 0 |
| 2023-03 | 44 | -9.466667 | 0.821271 | 0.673171 | 3 | 0 | 1 |
| 2023-04 | 29 | -29.350000 | 0.184722 | 0.212766 | 5 | 0 | 1 |
| 2023-05 | 22 | 7.000000 | 1.307018 | 1.240964 | 3 | 1 | 1 |
| 2023-06 | 25 | -13.666667 | 0.539326 | 0.608696 | 4 | 0 | 2 |
| 2023-07 | 24 | 4.316667 | 1.159091 | 1.109091 | 1 | 0 | 0 |
| 2023-08 | 21 | -31.966667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 29 | -30.966667 | 0.162308 | 0.198582 | 2 | 0 | 0 |
| 2023-10 | 27 | -27.066667 | 0.215080 | 0.210526 | 0 | 0 | 0 |
| 2023-11 | 36 | -21.766667 | 0.431927 | 0.506944 | 1 | 0 | 0 |
| 2023-12 | 28 | 2.033333 | 1.074119 | 1.163636 | 0 | 0 | 0 |

### B_OPT2023_N5_W3_T2_SB1_TP10

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 340, entry dates 183, entry months 12; SKIP 2, EXCLUDED 5, exclusion share 0.014493; conditional FLAT CLOSED 241.
Net -191.966667 R; PF R / price 0.527738 / 0.522540; expectancy -0.564608 R; win rate 0.164706; average winner / loser 3.830655 / -1.472766 R.
Conditional CLOSED-only DD 203.933333 R; largest winner share 0.077694; largest positive month share 0.524723. Positive / negative / zero months 3 / 9 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 27 | -20.616667 | 0.361713 | 0.330645 | 5 | 0 | 0 |
| 2023-02 | 28 | -26.950000 | 0.260631 | 0.286713 | 4 | 1 | 0 |
| 2023-03 | 44 | -6.133333 | 0.884204 | 0.721951 | 3 | 0 | 1 |
| 2023-04 | 29 | -29.350000 | 0.184722 | 0.212766 | 5 | 0 | 1 |
| 2023-05 | 22 | 8.666667 | 1.380117 | 1.301205 | 3 | 1 | 1 |
| 2023-06 | 25 | -13.666667 | 0.539326 | 0.608696 | 4 | 0 | 2 |
| 2023-07 | 24 | 4.316667 | 1.159091 | 1.109091 | 1 | 0 | 0 |
| 2023-08 | 21 | -31.966667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 29 | -30.966667 | 0.162308 | 0.198582 | 2 | 0 | 0 |
| 2023-10 | 27 | -27.066667 | 0.215080 | 0.210526 | 0 | 0 | 0 |
| 2023-11 | 36 | -21.766667 | 0.431927 | 0.506944 | 1 | 0 | 0 |
| 2023-12 | 28 | 3.533333 | 1.128797 | 1.218182 | 0 | 0 | 0 |

### B_OPT2023_N5_W3_T3_SB1_TP2

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors.
CLOSED 158, entry dates 110, entry months 12; SKIP 0, EXCLUDED 1, exclusion share 0.006289; conditional FLAT CLOSED 102.
Net -66.116667 R; PF R / price 0.611193 / 0.628389; expectancy -0.418460 R; win rate 0.253165; average winner / loser 2.598333 / -1.491667 R.
Conditional CLOSED-only DD 70.616667 R; largest winner share 0.032072; largest positive month share 0.342227. Positive / negative / zero months 3 / 9 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 21 | -4.400000 | 0.784314 | 0.712500 | 5 | 0 | 0 |
| 2023-02 | 12 | -13.733333 | 0.195312 | 0.158730 | 4 | 0 | 0 |
| 2023-03 | 23 | -0.966667 | 0.953895 | 0.932432 | 3 | 0 | 1 |
| 2023-04 | 14 | -9.750000 | 0.386149 | 0.380952 | 5 | 0 | 0 |
| 2023-05 | 14 | -12.733333 | 0.325088 | 0.352941 | 3 | 0 | 0 |
| 2023-06 | 10 | 4.916667 | 1.741206 | 1.814815 | 4 | 0 | 0 |
| 2023-07 | 10 | 4.733333 | 1.612069 | 1.586207 | 1 | 0 | 0 |
| 2023-08 | 6 | -9.066667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 17 | -14.900000 | 0.297170 | 0.373333 | 2 | 0 | 0 |
| 2023-10 | 7 | 4.716667 | 2.010714 | 2.176471 | 0 | 0 | 0 |
| 2023-11 | 11 | -7.566667 | 0.336257 | 0.285714 | 1 | 0 | 0 |
| 2023-12 | 13 | -7.366667 | 0.544330 | 0.716981 | 0 | 0 | 0 |

### B_OPT2023_N5_W3_T3_SB1_TP3

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors.
CLOSED 157, entry dates 110, entry months 12; SKIP 0, EXCLUDED 1, exclusion share 0.006329; conditional FLAT CLOSED 102.
Net -47.416667 R; PF R / price 0.728037 / 0.746501; expectancy -0.302017 R; win rate 0.222930; average winner / loser 3.626667 / -1.477542 R.
Conditional CLOSED-only DD 50.416667 R; largest winner share 0.039391; largest positive month share 0.359563. Positive / negative / zero months 4 / 8 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 20 | -7.900000 | 0.618971 | 0.567901 | 5 | 0 | 0 |
| 2023-02 | 12 | -12.066667 | 0.292969 | 0.238095 | 4 | 0 | 0 |
| 2023-03 | 23 | 8.533333 | 1.406995 | 1.378378 | 3 | 0 | 1 |
| 2023-04 | 14 | -13.350000 | 0.239316 | 0.308824 | 5 | 0 | 0 |
| 2023-05 | 14 | -9.666667 | 0.487633 | 0.529412 | 3 | 0 | 0 |
| 2023-06 | 10 | 7.716667 | 2.163317 | 2.222222 | 4 | 0 | 0 |
| 2023-07 | 10 | 10.966667 | 2.418103 | 2.379310 | 1 | 0 | 0 |
| 2023-08 | 6 | -9.066667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 17 | -12.000000 | 0.433962 | 0.546667 | 2 | 0 | 0 |
| 2023-10 | 7 | 3.283333 | 1.532432 | 1.608696 | 0 | 0 | 0 |
| 2023-11 | 11 | -5.900000 | 0.482456 | 0.404762 | 1 | 0 | 0 |
| 2023-12 | 13 | -7.966667 | 0.530452 | 0.631579 | 0 | 0 | 0 |

### B_OPT2023_N5_W3_T3_SB1_TP4

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 156, entry dates 110, entry months 12; SKIP 0, EXCLUDED 1, exclusion share 0.006369; conditional FLAT CLOSED 102.
Net -46.883333 R; PF R / price 0.733137 / 0.741538; expectancy -0.300534 R; win rate 0.205128; average winner / loser 4.025000 / -1.476331 R.
Conditional CLOSED-only DD 52.916667 R; largest winner share 0.051760; largest positive month share 0.504149. Positive / negative / zero months 4 / 8 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 20 | -4.733333 | 0.771704 | 0.703704 | 5 | 0 | 0 |
| 2023-02 | 11 | -13.066667 | 0.151515 | 0.120690 | 4 | 0 | 0 |
| 2023-03 | 23 | 6.366667 | 1.303657 | 1.283784 | 3 | 0 | 1 |
| 2023-04 | 14 | -14.550000 | 0.170940 | 0.220588 | 5 | 0 | 0 |
| 2023-05 | 14 | -7.400000 | 0.607774 | 0.647059 | 3 | 0 | 0 |
| 2023-06 | 10 | 3.216667 | 1.395492 | 1.454545 | 4 | 0 | 0 |
| 2023-07 | 10 | 16.200000 | 3.094828 | 3.068966 | 1 | 0 | 0 |
| 2023-08 | 6 | -9.066667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 17 | -21.000000 | 0.074890 | 0.098765 | 2 | 0 | 0 |
| 2023-10 | 7 | 6.350000 | 2.029730 | 2.130435 | 0 | 0 | 0 |
| 2023-11 | 11 | -4.233333 | 0.628655 | 0.523810 | 1 | 0 | 0 |
| 2023-12 | 13 | -4.966667 | 0.707269 | 0.842105 | 0 | 0 | 0 |

### B_OPT2023_N5_W3_T3_SB1_TP5

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 156, entry dates 110, entry months 12; SKIP 0, EXCLUDED 1, exclusion share 0.006369; conditional FLAT CLOSED 102.
Net -45.566667 R; PF R / price 0.742682 / 0.726027; expectancy -0.292094 R; win rate 0.198718; average winner / loser 4.242473 / -1.475694 R.
Conditional CLOSED-only DD 52.100000 R; largest winner share 0.063363; largest positive month share 0.608825. Positive / negative / zero months 4 / 8 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 20 | -5.566667 | 0.731511 | 0.641975 | 5 | 0 | 0 |
| 2023-02 | 11 | -13.066667 | 0.151515 | 0.120690 | 4 | 0 | 0 |
| 2023-03 | 23 | 5.200000 | 1.248013 | 1.175676 | 3 | 0 | 1 |
| 2023-04 | 14 | -14.550000 | 0.170940 | 0.220588 | 5 | 0 | 0 |
| 2023-05 | 14 | -5.733333 | 0.696113 | 0.720588 | 3 | 0 | 0 |
| 2023-06 | 10 | 4.716667 | 1.579918 | 1.636364 | 4 | 0 | 0 |
| 2023-07 | 10 | 17.016667 | 3.200431 | 3.172414 | 1 | 0 | 0 |
| 2023-08 | 6 | -9.066667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 17 | -21.000000 | 0.074890 | 0.098765 | 2 | 0 | 0 |
| 2023-10 | 7 | 1.016667 | 1.134361 | 0.866667 | 0 | 0 | 0 |
| 2023-11 | 11 | -2.566667 | 0.774854 | 0.642857 | 1 | 0 | 0 |
| 2023-12 | 13 | -1.966667 | 0.884086 | 1.052632 | 0 | 0 | 0 |

### B_OPT2023_N5_W3_T3_SB1_TP6

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 155, entry dates 110, entry months 12; SKIP 0, EXCLUDED 1, exclusion share 0.006410; conditional FLAT CLOSED 102.
Net -37.166667 R; PF R / price 0.790118 / 0.767123; expectancy -0.239785 R; win rate 0.193548; average winner / loser 4.663889 / -1.475694 R.
Conditional CLOSED-only DD 42.200000 R; largest winner share 0.071471; largest positive month share 0.549977. Positive / negative / zero months 4 / 8 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 20 | -7.566667 | 0.635048 | 0.567901 | 5 | 0 | 0 |
| 2023-02 | 11 | -13.066667 | 0.151515 | 0.120690 | 4 | 0 | 0 |
| 2023-03 | 22 | 7.533333 | 1.359300 | 1.256757 | 3 | 0 | 1 |
| 2023-04 | 14 | -14.550000 | 0.170940 | 0.220588 | 5 | 0 | 0 |
| 2023-05 | 14 | -4.066667 | 0.784452 | 0.794118 | 3 | 0 | 0 |
| 2023-06 | 10 | 6.216667 | 1.764344 | 1.818182 | 4 | 0 | 0 |
| 2023-07 | 10 | 20.083333 | 3.596983 | 3.586207 | 1 | 0 | 0 |
| 2023-08 | 6 | -9.066667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 17 | -21.000000 | 0.074890 | 0.098765 | 2 | 0 | 0 |
| 2023-10 | 7 | 2.683333 | 1.354626 | 1.033333 | 0 | 0 | 0 |
| 2023-11 | 11 | -0.900000 | 0.921053 | 0.761905 | 1 | 0 | 0 |
| 2023-12 | 13 | -3.466667 | 0.795678 | 0.947368 | 0 | 0 | 0 |

### B_OPT2023_N5_W3_T3_SB1_TP7

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 155, entry dates 110, entry months 12; SKIP 0, EXCLUDED 1, exclusion share 0.006410; conditional FLAT CLOSED 102.
Net -34.433333 R; PF R / price 0.805553 / 0.788432; expectancy -0.222151 R; win rate 0.193548; average winner / loser 4.755000 / -1.475694 R.
Conditional CLOSED-only DD 40.966667 R; largest winner share 0.081785; largest positive month share 0.551435. Positive / negative / zero months 4 / 8 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 20 | -7.566667 | 0.635048 | 0.567901 | 5 | 0 | 0 |
| 2023-02 | 11 | -13.066667 | 0.151515 | 0.120690 | 4 | 0 | 0 |
| 2023-03 | 22 | 4.866667 | 1.232114 | 1.148649 | 3 | 0 | 1 |
| 2023-04 | 14 | -14.550000 | 0.170940 | 0.220588 | 5 | 0 | 0 |
| 2023-05 | 14 | -2.400000 | 0.872792 | 0.867647 | 3 | 0 | 0 |
| 2023-06 | 10 | 7.716667 | 1.948770 | 2.000000 | 4 | 0 | 0 |
| 2023-07 | 10 | 20.816667 | 3.691810 | 3.758621 | 1 | 0 | 0 |
| 2023-08 | 6 | -9.066667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 17 | -21.000000 | 0.074890 | 0.098765 | 2 | 0 | 0 |
| 2023-10 | 7 | 4.350000 | 1.574890 | 1.200000 | 0 | 0 | 0 |
| 2023-11 | 11 | -2.566667 | 0.774854 | 0.642857 | 1 | 0 | 0 |
| 2023-12 | 13 | -1.966667 | 0.884086 | 1.052632 | 0 | 0 | 0 |

### B_OPT2023_N5_W3_T3_SB1_TP8

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 155, entry dates 110, entry months 12; SKIP 0, EXCLUDED 1, exclusion share 0.006410; conditional FLAT CLOSED 102.
Net -25.033333 R; PF R / price 0.858635 / 0.840183; expectancy -0.161505 R; win rate 0.193548; average winner / loser 5.068333 / -1.475694 R.
Conditional CLOSED-only DD 36.783333 R; largest winner share 0.087690; largest positive month share 0.505116. Positive / negative / zero months 4 / 8 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 20 | -7.566667 | 0.635048 | 0.567901 | 5 | 0 | 0 |
| 2023-02 | 11 | -13.066667 | 0.151515 | 0.120690 | 4 | 0 | 0 |
| 2023-03 | 22 | 6.533333 | 1.311606 | 1.216216 | 3 | 0 | 1 |
| 2023-04 | 14 | -14.550000 | 0.170940 | 0.220588 | 5 | 0 | 0 |
| 2023-05 | 14 | -0.733333 | 0.961131 | 0.941176 | 3 | 0 | 0 |
| 2023-06 | 10 | 9.216667 | 2.133197 | 2.181818 | 4 | 0 | 0 |
| 2023-07 | 10 | 22.216667 | 3.872845 | 4.000000 | 1 | 0 | 0 |
| 2023-08 | 6 | -9.066667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 17 | -21.000000 | 0.074890 | 0.098765 | 2 | 0 | 0 |
| 2023-10 | 7 | 6.016667 | 1.795154 | 1.366667 | 0 | 0 | 0 |
| 2023-11 | 11 | -2.566667 | 0.774854 | 0.642857 | 1 | 0 | 0 |
| 2023-12 | 13 | -0.466667 | 0.972495 | 1.157895 | 0 | 0 | 0 |

### B_OPT2023_N5_W3_T3_SB1_TP9

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 155, entry dates 110, entry months 12; SKIP 0, EXCLUDED 1, exclusion share 0.006410; conditional FLAT CLOSED 102.
Net -33.950000 R; PF R / price 0.808282 / 0.794521; expectancy -0.219032 R; win rate 0.193548; average winner / loser 4.771111 / -1.475694 R.
Conditional CLOSED-only DD 43.783333 R; largest winner share 0.104797; largest positive month share 0.602895. Positive / negative / zero months 5 / 7 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 20 | -7.566667 | 0.635048 | 0.567901 | 5 | 0 | 0 |
| 2023-02 | 11 | -13.066667 | 0.151515 | 0.120690 | 4 | 0 | 0 |
| 2023-03 | 22 | 8.200000 | 1.391097 | 1.283784 | 3 | 0 | 1 |
| 2023-04 | 14 | -14.550000 | 0.170940 | 0.220588 | 5 | 0 | 0 |
| 2023-05 | 14 | 0.933333 | 1.049470 | 1.014706 | 3 | 0 | 0 |
| 2023-06 | 10 | 4.466667 | 1.549180 | 1.606061 | 4 | 0 | 0 |
| 2023-07 | 10 | 22.216667 | 3.872845 | 4.000000 | 1 | 0 | 0 |
| 2023-08 | 6 | -9.066667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 17 | -21.000000 | 0.074890 | 0.098765 | 2 | 0 | 0 |
| 2023-10 | 7 | -2.983333 | 0.605727 | 0.466667 | 0 | 0 | 0 |
| 2023-11 | 11 | -2.566667 | 0.774854 | 0.642857 | 1 | 0 | 0 |
| 2023-12 | 13 | 1.033333 | 1.060904 | 1.263158 | 0 | 0 | 0 |

### B_OPT2023_N5_W3_T3_SB1_TP10

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 155, entry dates 110, entry months 12; SKIP 0, EXCLUDED 1, exclusion share 0.006410; conditional FLAT CLOSED 102.
Net -29.116667 R; PF R / price 0.835576 / 0.818874; expectancy -0.187849 R; win rate 0.193548; average winner / loser 4.932222 / -1.475694 R.
Conditional CLOSED-only DD 43.783333 R; largest winner share 0.112638; largest positive month share 0.532987. Positive / negative / zero months 5 / 7 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 20 | -7.566667 | 0.635048 | 0.567901 | 5 | 0 | 0 |
| 2023-02 | 11 | -13.066667 | 0.151515 | 0.120690 | 4 | 0 | 0 |
| 2023-03 | 22 | 9.866667 | 1.470588 | 1.351351 | 3 | 0 | 1 |
| 2023-04 | 14 | -14.550000 | 0.170940 | 0.220588 | 5 | 0 | 0 |
| 2023-05 | 14 | 2.600000 | 1.137809 | 1.088235 | 3 | 0 | 0 |
| 2023-06 | 10 | 4.466667 | 1.549180 | 1.606061 | 4 | 0 | 0 |
| 2023-07 | 10 | 22.216667 | 3.872845 | 4.000000 | 1 | 0 | 0 |
| 2023-08 | 6 | -9.066667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 17 | -21.000000 | 0.074890 | 0.098765 | 2 | 0 | 0 |
| 2023-10 | 7 | -2.983333 | 0.605727 | 0.466667 | 0 | 0 | 0 |
| 2023-11 | 11 | -2.566667 | 0.774854 | 0.642857 | 1 | 0 | 0 |
| 2023-12 | 13 | 2.533333 | 1.149312 | 1.368421 | 0 | 0 | 0 |

### B_OPT2023_N6_W2_T2_SB1_TP2

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 124, entry dates 93, entry months 12; SKIP 0, EXCLUDED 2, exclusion share 0.015873; conditional FLAT CLOSED 110.
Net -90.750000 R; PF R / price 0.372117 / 0.364769; expectancy -0.731855 R; win rate 0.161290; average winner / loser 2.689167 / -1.389744 R.
Conditional CLOSED-only DD 90.750000 R; largest winner share 0.061977; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 12 | -13.600000 | 0.170732 | 0.202899 | 5 | 0 | 0 |
| 2023-02 | 11 | -3.000000 | 0.748603 | 0.760000 | 4 | 0 | 1 |
| 2023-03 | 13 | -7.450000 | 0.451534 | 0.500000 | 3 | 0 | 1 |
| 2023-04 | 13 | -7.883333 | 0.458190 | 0.357143 | 5 | 0 | 0 |
| 2023-05 | 7 | 1.283333 | 1.269231 | 1.421053 | 3 | 0 | 0 |
| 2023-06 | 9 | -8.633333 | 0.278552 | 0.238095 | 4 | 0 | 0 |
| 2023-07 | 10 | -8.566667 | 0.280112 | 0.208333 | 1 | 0 | 0 |
| 2023-08 | 4 | -1.666667 | 0.642857 | 0.705882 | 2 | 0 | 0 |
| 2023-09 | 13 | -19.483333 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 5 | -3.000000 | 0.526316 | 0.454545 | 0 | 0 | 0 |
| 2023-11 | 17 | -3.616667 | 0.738239 | 0.666667 | 1 | 0 | 0 |
| 2023-12 | 10 | -15.133333 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N6_W2_T2_SB1_TP3

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 123, entry dates 93, entry months 12; SKIP 0, EXCLUDED 2, exclusion share 0.016000; conditional FLAT CLOSED 109.
Net -101.816667 R; PF R / price 0.321222 / 0.296233; expectancy -0.827778 R; win rate 0.113821; average winner / loser 3.441667 / -1.388889 R.
Conditional CLOSED-only DD 101.816667 R; largest winner share 0.103770; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 12 | -13.600000 | 0.170732 | 0.202899 | 5 | 0 | 0 |
| 2023-02 | 11 | -9.666667 | 0.275000 | 0.192982 | 4 | 0 | 1 |
| 2023-03 | 13 | -6.383333 | 0.530061 | 0.541667 | 3 | 0 | 1 |
| 2023-04 | 13 | -17.216667 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 7 | -1.416667 | 0.770270 | 0.730769 | 3 | 0 | 0 |
| 2023-06 | 9 | -6.966667 | 0.417827 | 0.357143 | 4 | 0 | 0 |
| 2023-07 | 10 | -6.900000 | 0.420168 | 0.312500 | 1 | 0 | 0 |
| 2023-08 | 3 | -4.666667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 13 | -19.483333 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 5 | -1.333333 | 0.789474 | 0.681818 | 0 | 0 | 0 |
| 2023-11 | 17 | 0.950000 | 1.068758 | 0.966667 | 1 | 0 | 0 |
| 2023-12 | 10 | -15.133333 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N6_W2_T2_SB1_TP4

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 123, entry dates 93, entry months 12; SKIP 0, EXCLUDED 2, exclusion share 0.016000; conditional FLAT CLOSED 109.
Net -94.583333 R; PF R / price 0.369444 / 0.333904; expectancy -0.768970 R; win rate 0.113821; average winner / loser 3.958333 / -1.388889 R.
Conditional CLOSED-only DD 94.583333 R; largest winner share 0.120301; largest positive month share 0.913420. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 12 | -13.600000 | 0.170732 | 0.202899 | 5 | 0 | 0 |
| 2023-02 | 11 | -9.666667 | 0.275000 | 0.192982 | 4 | 0 | 1 |
| 2023-03 | 13 | -4.716667 | 0.652761 | 0.645833 | 3 | 0 | 1 |
| 2023-04 | 13 | -17.216667 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 7 | -3.416667 | 0.445946 | 0.423077 | 3 | 0 | 0 |
| 2023-06 | 9 | -5.300000 | 0.557103 | 0.476190 | 4 | 0 | 0 |
| 2023-07 | 10 | -5.233333 | 0.560224 | 0.416667 | 1 | 0 | 0 |
| 2023-08 | 3 | -4.666667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 13 | -19.483333 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 5 | 0.333333 | 1.052632 | 0.909091 | 0 | 0 | 0 |
| 2023-11 | 17 | 3.516667 | 1.254524 | 1.133333 | 1 | 0 | 0 |
| 2023-12 | 10 | -15.133333 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N6_W2_T2_SB1_TP5

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 123, entry dates 93, entry months 12; SKIP 0, EXCLUDED 2, exclusion share 0.016000; conditional FLAT CLOSED 109.
Net -94.850000 R; PF R / price 0.367667 / 0.337329; expectancy -0.771138 R; win rate 0.113821; average winner / loser 3.939286 / -1.388889 R.
Conditional CLOSED-only DD 94.850000 R; largest winner share 0.151103; largest positive month share 0.696203. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 12 | -13.600000 | 0.170732 | 0.202899 | 5 | 0 | 0 |
| 2023-02 | 11 | -9.666667 | 0.275000 | 0.192982 | 4 | 0 | 1 |
| 2023-03 | 13 | -3.050000 | 0.775460 | 0.750000 | 3 | 0 | 1 |
| 2023-04 | 13 | -17.216667 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 7 | -3.416667 | 0.445946 | 0.423077 | 3 | 0 | 0 |
| 2023-06 | 9 | -11.633333 | 0.027855 | 0.023810 | 4 | 0 | 0 |
| 2023-07 | 10 | -3.566667 | 0.700280 | 0.520833 | 1 | 0 | 0 |
| 2023-08 | 3 | -4.666667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 13 | -19.483333 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 5 | 2.000000 | 1.315789 | 1.136364 | 0 | 0 | 0 |
| 2023-11 | 17 | 4.583333 | 1.331725 | 1.233333 | 1 | 0 | 0 |
| 2023-12 | 10 | -15.133333 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N6_W2_T2_SB1_TP6

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 123, entry dates 93, entry months 12; SKIP 0, EXCLUDED 2, exclusion share 0.016000; conditional FLAT CLOSED 109.
Net -92.650000 R; PF R / price 0.382333 / 0.342466; expectancy -0.753252 R; win rate 0.113821; average winner / loser 4.096429 / -1.388889 R.
Conditional CLOSED-only DD 92.650000 R; largest winner share 0.174368; largest positive month share 0.568475. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 12 | -13.600000 | 0.170732 | 0.202899 | 5 | 0 | 0 |
| 2023-02 | 11 | -9.666667 | 0.275000 | 0.192982 | 4 | 0 | 1 |
| 2023-03 | 13 | -2.383333 | 0.824540 | 0.791667 | 3 | 0 | 1 |
| 2023-04 | 13 | -17.216667 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 7 | -3.416667 | 0.445946 | 0.423077 | 3 | 0 | 0 |
| 2023-06 | 9 | -11.633333 | 0.027855 | 0.023810 | 4 | 0 | 0 |
| 2023-07 | 10 | -1.900000 | 0.840336 | 0.625000 | 1 | 0 | 0 |
| 2023-08 | 3 | -4.666667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 13 | -19.483333 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 5 | 3.666667 | 1.578947 | 1.363636 | 0 | 0 | 0 |
| 2023-11 | 17 | 2.783333 | 1.201448 | 1.083333 | 1 | 0 | 0 |
| 2023-12 | 10 | -15.133333 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N6_W2_T2_SB1_TP7

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 123, entry dates 93, entry months 12; SKIP 0, EXCLUDED 2, exclusion share 0.016000; conditional FLAT CLOSED 109.
Net -89.316667 R; PF R / price 0.404556 / 0.359589; expectancy -0.726152 R; win rate 0.113821; average winner / loser 4.334524 / -1.388889 R.
Conditional CLOSED-only DD 89.316667 R; largest winner share 0.192255; largest positive month share 0.657084. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 12 | -13.600000 | 0.170732 | 0.202899 | 5 | 0 | 0 |
| 2023-02 | 11 | -9.666667 | 0.275000 | 0.192982 | 4 | 0 | 1 |
| 2023-03 | 13 | -2.383333 | 0.824540 | 0.791667 | 3 | 0 | 1 |
| 2023-04 | 13 | -17.216667 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 7 | -3.416667 | 0.445946 | 0.423077 | 3 | 0 | 0 |
| 2023-06 | 9 | -11.633333 | 0.027855 | 0.023810 | 4 | 0 | 0 |
| 2023-07 | 10 | -0.233333 | 0.980392 | 0.729167 | 1 | 0 | 0 |
| 2023-08 | 3 | -4.666667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 13 | -19.483333 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 5 | 5.333333 | 1.842105 | 1.590909 | 0 | 0 | 0 |
| 2023-11 | 17 | 2.783333 | 1.201448 | 1.083333 | 1 | 0 | 0 |
| 2023-12 | 10 | -15.133333 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N6_W2_T2_SB1_TP8

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 123, entry dates 93, entry months 12; SKIP 0, EXCLUDED 2, exclusion share 0.016000; conditional FLAT CLOSED 109.
Net -90.650000 R; PF R / price 0.395667 / 0.352740; expectancy -0.736992 R; win rate 0.113821; average winner / loser 4.239286 / -1.388889 R.
Conditional CLOSED-only DD 90.650000 R; largest winner share 0.224656; largest positive month share 0.715503. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 12 | -13.600000 | 0.170732 | 0.202899 | 5 | 0 | 0 |
| 2023-02 | 11 | -9.666667 | 0.275000 | 0.192982 | 4 | 0 | 1 |
| 2023-03 | 13 | -2.383333 | 0.824540 | 0.791667 | 3 | 0 | 1 |
| 2023-04 | 13 | -17.216667 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 7 | -3.416667 | 0.445946 | 0.423077 | 3 | 0 | 0 |
| 2023-06 | 9 | -11.633333 | 0.027855 | 0.023810 | 4 | 0 | 0 |
| 2023-07 | 10 | -3.233333 | 0.728291 | 0.541667 | 1 | 0 | 0 |
| 2023-08 | 3 | -4.666667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 13 | -19.483333 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 5 | 7.000000 | 2.105263 | 1.818182 | 0 | 0 | 0 |
| 2023-11 | 17 | 2.783333 | 1.201448 | 1.083333 | 1 | 0 | 0 |
| 2023-12 | 10 | -15.133333 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N6_W2_T2_SB1_TP9

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 123, entry dates 93, entry months 12; SKIP 0, EXCLUDED 2, exclusion share 0.016000; conditional FLAT CLOSED 109.
Net -99.650000 R; PF R / price 0.335667 / 0.306507; expectancy -0.810163 R; win rate 0.113821; average winner / loser 3.596429 / -1.388889 R.
Conditional CLOSED-only DD 99.650000 R; largest winner share 0.178749; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 12 | -13.600000 | 0.170732 | 0.202899 | 5 | 0 | 0 |
| 2023-02 | 11 | -9.666667 | 0.275000 | 0.192982 | 4 | 0 | 1 |
| 2023-03 | 13 | -2.383333 | 0.824540 | 0.791667 | 3 | 0 | 1 |
| 2023-04 | 13 | -17.216667 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 7 | -3.416667 | 0.445946 | 0.423077 | 3 | 0 | 0 |
| 2023-06 | 9 | -11.633333 | 0.027855 | 0.023810 | 4 | 0 | 0 |
| 2023-07 | 10 | -3.233333 | 0.728291 | 0.541667 | 1 | 0 | 0 |
| 2023-08 | 3 | -4.666667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 13 | -19.483333 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 5 | -2.000000 | 0.684211 | 0.590909 | 0 | 0 | 0 |
| 2023-11 | 17 | 2.783333 | 1.201448 | 1.083333 | 1 | 0 | 0 |
| 2023-12 | 10 | -15.133333 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N6_W2_T2_SB1_TP10

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 123, entry dates 93, entry months 12; SKIP 0, EXCLUDED 2, exclusion share 0.016000; conditional FLAT CLOSED 109.
Net -99.650000 R; PF R / price 0.335667 / 0.306507; expectancy -0.810163 R; win rate 0.113821; average winner / loser 3.596429 / -1.388889 R.
Conditional CLOSED-only DD 99.650000 R; largest winner share 0.178749; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 12 | -13.600000 | 0.170732 | 0.202899 | 5 | 0 | 0 |
| 2023-02 | 11 | -9.666667 | 0.275000 | 0.192982 | 4 | 0 | 1 |
| 2023-03 | 13 | -2.383333 | 0.824540 | 0.791667 | 3 | 0 | 1 |
| 2023-04 | 13 | -17.216667 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 7 | -3.416667 | 0.445946 | 0.423077 | 3 | 0 | 0 |
| 2023-06 | 9 | -11.633333 | 0.027855 | 0.023810 | 4 | 0 | 0 |
| 2023-07 | 10 | -3.233333 | 0.728291 | 0.541667 | 1 | 0 | 0 |
| 2023-08 | 3 | -4.666667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 13 | -19.483333 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 5 | -2.000000 | 0.684211 | 0.590909 | 0 | 0 | 0 |
| 2023-11 | 17 | 2.783333 | 1.201448 | 1.083333 | 1 | 0 | 0 |
| 2023-12 | 10 | -15.133333 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N6_W2_T3_SB1_TP2

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 60, entry dates 46, entry months 12; SKIP 0, EXCLUDED 1, exclusion share 0.016393; conditional FLAT CLOSED 48.
Net -41.383333 R; PF R / price 0.396011 / 0.356863; expectancy -0.689722 R; win rate 0.166667; average winner / loser 2.713333 / -1.370333 R.
Conditional CLOSED-only DD 41.383333 R; largest winner share 0.122850; largest positive month share 0.592593. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 6 | -8.866667 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-02 | 6 | -4.566667 | 0.421941 | 0.357143 | 4 | 0 | 0 |
| 2023-03 | 8 | -2.350000 | 0.586510 | 0.650000 | 3 | 0 | 1 |
| 2023-04 | 8 | -0.416667 | 0.941176 | 0.800000 | 5 | 0 | 0 |
| 2023-05 | 2 | 1.833333 | 2.222222 | 1.666667 | 3 | 0 | 0 |
| 2023-06 | 3 | -3.966667 | 0.000000 | 0.000000 | 4 | 0 | 0 |
| 2023-07 | 7 | -4.900000 | 0.404858 | 0.303030 | 1 | 0 | 0 |
| 2023-08 | 1 | -1.500000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 8 | -11.816667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 3 | 2.666667 | 2.600000 | 2.800000 | 0 | 0 | 0 |
| 2023-11 | 5 | -2.833333 | 0.497041 | 0.700000 | 1 | 0 | 0 |
| 2023-12 | 3 | -4.666667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N6_W2_T3_SB1_TP3

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 59, entry dates 46, entry months 12; SKIP 0, EXCLUDED 1, exclusion share 0.016667; conditional FLAT CLOSED 47.
Net -44.083333 R; PF R / price 0.377207 / 0.352490; expectancy -0.747175 R; win rate 0.135593; average winner / loser 3.337500 / -1.387908 R.
Conditional CLOSED-only DD 44.083333 R; largest winner share 0.187266; largest positive month share 0.553191. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 6 | -8.866667 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-02 | 6 | -4.233333 | 0.464135 | 0.392857 | 4 | 0 | 0 |
| 2023-03 | 7 | -2.450000 | 0.536278 | 0.611111 | 3 | 0 | 1 |
| 2023-04 | 8 | -9.750000 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 2 | 3.500000 | 3.333333 | 2.500000 | 3 | 0 | 0 |
| 2023-06 | 3 | -3.966667 | 0.000000 | 0.000000 | 4 | 0 | 0 |
| 2023-07 | 7 | -3.233333 | 0.607287 | 0.454545 | 1 | 0 | 0 |
| 2023-08 | 1 | -1.500000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 8 | -11.816667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 3 | 4.333333 | 3.600000 | 3.800000 | 0 | 0 | 0 |
| 2023-11 | 5 | -1.433333 | 0.745562 | 1.050000 | 1 | 0 | 0 |
| 2023-12 | 3 | -4.666667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N6_W2_T3_SB1_TP4

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 59, entry dates 46, entry months 12; SKIP 0, EXCLUDED 1, exclusion share 0.016667; conditional FLAT CLOSED 47.
Net -37.683333 R; PF R / price 0.467624 / 0.436782; expectancy -0.638701 R; win rate 0.135593; average winner / loser 4.137500 / -1.387908 R.
Conditional CLOSED-only DD 38.983333 R; largest winner share 0.201410; largest positive month share 0.537313. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 6 | -8.866667 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-02 | 6 | -4.233333 | 0.464135 | 0.392857 | 4 | 0 | 0 |
| 2023-03 | 7 | -2.450000 | 0.536278 | 0.611111 | 3 | 0 | 1 |
| 2023-04 | 8 | -9.750000 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 2 | 5.166667 | 4.444444 | 3.333333 | 3 | 0 | 0 |
| 2023-06 | 3 | -3.966667 | 0.000000 | 0.000000 | 4 | 0 | 0 |
| 2023-07 | 7 | -1.566667 | 0.809717 | 0.606061 | 1 | 0 | 0 |
| 2023-08 | 1 | -1.500000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 8 | -11.816667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 3 | 6.000000 | 4.600000 | 4.800000 | 0 | 0 | 0 |
| 2023-11 | 5 | -0.033333 | 0.994083 | 1.400000 | 1 | 0 | 0 |
| 2023-12 | 3 | -4.666667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N6_W2_T3_SB1_TP5

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 59, entry dates 46, entry months 12; SKIP 0, EXCLUDED 1, exclusion share 0.016667; conditional FLAT CLOSED 47.
Net -33.683333 R; PF R / price 0.524135 / 0.475096; expectancy -0.570904 R; win rate 0.135593; average winner / loser 4.637500 / -1.387908 R.
Conditional CLOSED-only DD 35.650000 R; largest winner share 0.224618; largest positive month share 0.525114. Positive / negative / zero months 3 / 9 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 6 | -8.866667 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-02 | 6 | -4.233333 | 0.464135 | 0.392857 | 4 | 0 | 0 |
| 2023-03 | 7 | -2.450000 | 0.536278 | 0.611111 | 3 | 0 | 1 |
| 2023-04 | 8 | -9.750000 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 2 | 6.833333 | 5.555556 | 4.166667 | 3 | 0 | 0 |
| 2023-06 | 3 | -3.966667 | 0.000000 | 0.000000 | 4 | 0 | 0 |
| 2023-07 | 7 | 0.100000 | 1.012146 | 0.757576 | 1 | 0 | 0 |
| 2023-08 | 1 | -1.500000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 8 | -11.816667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 3 | 7.666667 | 5.600000 | 5.800000 | 0 | 0 | 0 |
| 2023-11 | 5 | -1.033333 | 0.816568 | 1.150000 | 1 | 0 | 0 |
| 2023-12 | 3 | -4.666667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N6_W2_T3_SB1_TP6

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors.
CLOSED 59, entry dates 46, entry months 12; SKIP 0, EXCLUDED 1, exclusion share 0.016667; conditional FLAT CLOSED 47.
Net -28.683333 R; PF R / price 0.594773 / 0.532567; expectancy -0.486158 R; win rate 0.135593; average winner / loser 5.262500 / -1.387908 R.
Conditional CLOSED-only DD 32.316667 R; largest winner share 0.237530; largest positive month share 0.476190. Positive / negative / zero months 3 / 9 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 6 | -8.866667 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-02 | 6 | -4.233333 | 0.464135 | 0.392857 | 4 | 0 | 0 |
| 2023-03 | 7 | -2.450000 | 0.536278 | 0.611111 | 3 | 0 | 1 |
| 2023-04 | 8 | -9.750000 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 2 | 8.500000 | 6.666667 | 5.000000 | 3 | 0 | 0 |
| 2023-06 | 3 | -3.966667 | 0.000000 | 0.000000 | 4 | 0 | 0 |
| 2023-07 | 7 | 1.766667 | 1.214575 | 0.909091 | 1 | 0 | 0 |
| 2023-08 | 1 | -1.500000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 8 | -11.816667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 3 | 9.333333 | 6.600000 | 6.800000 | 0 | 0 | 0 |
| 2023-11 | 5 | -1.033333 | 0.816568 | 1.150000 | 1 | 0 | 0 |
| 2023-12 | 3 | -4.666667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N6_W2_T3_SB1_TP7

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors.
CLOSED 59, entry dates 46, entry months 12; SKIP 0, EXCLUDED 1, exclusion share 0.016667; conditional FLAT CLOSED 47.
Net -23.683333 R; PF R / price 0.665411 / 0.590038; expectancy -0.401412 R; win rate 0.135593; average winner / loser 5.887500 / -1.387908 R.
Conditional CLOSED-only DD 28.983333 R; largest winner share 0.247700; largest positive month share 0.447154. Positive / negative / zero months 3 / 9 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 6 | -8.866667 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-02 | 6 | -4.233333 | 0.464135 | 0.392857 | 4 | 0 | 0 |
| 2023-03 | 7 | -2.450000 | 0.536278 | 0.611111 | 3 | 0 | 1 |
| 2023-04 | 8 | -9.750000 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 2 | 10.166667 | 7.777778 | 5.833333 | 3 | 0 | 0 |
| 2023-06 | 3 | -3.966667 | 0.000000 | 0.000000 | 4 | 0 | 0 |
| 2023-07 | 7 | 3.433333 | 1.417004 | 1.060606 | 1 | 0 | 0 |
| 2023-08 | 1 | -1.500000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 8 | -11.816667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 3 | 11.000000 | 7.600000 | 7.800000 | 0 | 0 | 0 |
| 2023-11 | 5 | -1.033333 | 0.816568 | 1.150000 | 1 | 0 | 0 |
| 2023-12 | 3 | -4.666667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N6_W2_T3_SB1_TP8

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors.
CLOSED 59, entry dates 46, entry months 12; SKIP 0, EXCLUDED 1, exclusion share 0.016667; conditional FLAT CLOSED 47.
Net -27.016667 R; PF R / price 0.618319 / 0.551724; expectancy -0.457910 R; win rate 0.135593; average winner / loser 5.470833 / -1.387908 R.
Conditional CLOSED-only DD 33.983333 R; largest winner share 0.304646; largest positive month share 0.595611. Positive / negative / zero months 3 / 9 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 6 | -8.866667 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-02 | 6 | -4.233333 | 0.464135 | 0.392857 | 4 | 0 | 0 |
| 2023-03 | 7 | -2.450000 | 0.536278 | 0.611111 | 3 | 0 | 1 |
| 2023-04 | 8 | -9.750000 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 2 | 8.166667 | 6.444444 | 4.833333 | 3 | 0 | 0 |
| 2023-06 | 3 | -3.966667 | 0.000000 | 0.000000 | 4 | 0 | 0 |
| 2023-07 | 7 | 0.433333 | 1.052632 | 0.787879 | 1 | 0 | 0 |
| 2023-08 | 1 | -1.500000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 8 | -11.816667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 3 | 12.666667 | 8.600000 | 8.800000 | 0 | 0 | 0 |
| 2023-11 | 5 | -1.033333 | 0.816568 | 1.150000 | 1 | 0 | 0 |
| 2023-12 | 3 | -4.666667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N6_W2_T3_SB1_TP9

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors.
CLOSED 59, entry dates 46, entry months 12; SKIP 0, EXCLUDED 1, exclusion share 0.016667; conditional FLAT CLOSED 47.
Net -36.016667 R; PF R / price 0.491170 / 0.448276; expectancy -0.610452 R; win rate 0.135593; average winner / loser 4.345833 / -1.387908 R.
Conditional CLOSED-only DD 36.016667 R; largest winner share 0.278044; largest positive month share 0.665761. Positive / negative / zero months 3 / 9 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 6 | -8.866667 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-02 | 6 | -4.233333 | 0.464135 | 0.392857 | 4 | 0 | 0 |
| 2023-03 | 7 | -2.450000 | 0.536278 | 0.611111 | 3 | 0 | 1 |
| 2023-04 | 8 | -9.750000 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 2 | 8.166667 | 6.444444 | 4.833333 | 3 | 0 | 0 |
| 2023-06 | 3 | -3.966667 | 0.000000 | 0.000000 | 4 | 0 | 0 |
| 2023-07 | 7 | 0.433333 | 1.052632 | 0.787879 | 1 | 0 | 0 |
| 2023-08 | 1 | -1.500000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 8 | -11.816667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 3 | 3.666667 | 3.200000 | 3.400000 | 0 | 0 | 0 |
| 2023-11 | 5 | -1.033333 | 0.816568 | 1.150000 | 1 | 0 | 0 |
| 2023-12 | 3 | -4.666667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N6_W2_T3_SB1_TP10

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors.
CLOSED 59, entry dates 46, entry months 12; SKIP 0, EXCLUDED 1, exclusion share 0.016667; conditional FLAT CLOSED 47.
Net -36.016667 R; PF R / price 0.491170 / 0.448276; expectancy -0.610452 R; win rate 0.135593; average winner / loser 4.345833 / -1.387908 R.
Conditional CLOSED-only DD 36.016667 R; largest winner share 0.278044; largest positive month share 0.665761. Positive / negative / zero months 3 / 9 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 6 | -8.866667 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-02 | 6 | -4.233333 | 0.464135 | 0.392857 | 4 | 0 | 0 |
| 2023-03 | 7 | -2.450000 | 0.536278 | 0.611111 | 3 | 0 | 1 |
| 2023-04 | 8 | -9.750000 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 2 | 8.166667 | 6.444444 | 4.833333 | 3 | 0 | 0 |
| 2023-06 | 3 | -3.966667 | 0.000000 | 0.000000 | 4 | 0 | 0 |
| 2023-07 | 7 | 0.433333 | 1.052632 | 0.787879 | 1 | 0 | 0 |
| 2023-08 | 1 | -1.500000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 8 | -11.816667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 3 | 3.666667 | 3.200000 | 3.400000 | 0 | 0 | 0 |
| 2023-11 | 5 | -1.033333 | 0.816568 | 1.150000 | 1 | 0 | 0 |
| 2023-12 | 3 | -4.666667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N6_W3_T2_SB1_TP2

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 227, entry dates 144, entry months 12; SKIP 2, EXCLUDED 3, exclusion share 0.013043; conditional FLAT CLOSED 216.
Net -143.516667 R; PF R / price 0.438437 / 0.453981; expectancy -0.632232 R; win rate 0.207048; average winner / loser 2.384043 / -1.435768 R.
Conditional CLOSED-only DD 143.516667 R; largest winner share 0.029749; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 12 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 16 | -15.066667 | 0.289308 | 0.300000 | 5 | 0 | 1 |
| 2023-02 | 28 | -16.416667 | 0.481852 | 0.516393 | 4 | 0 | 0 |
| 2023-03 | 25 | -7.433333 | 0.698445 | 0.816092 | 3 | 1 | 1 |
| 2023-04 | 21 | -7.766667 | 0.673212 | 0.606742 | 5 | 0 | 0 |
| 2023-05 | 13 | -2.416667 | 0.799724 | 1.071429 | 3 | 1 | 0 |
| 2023-06 | 16 | -21.800000 | 0.029674 | 0.024691 | 4 | 0 | 1 |
| 2023-07 | 13 | -6.200000 | 0.527919 | 0.538462 | 1 | 0 | 0 |
| 2023-08 | 10 | -4.533333 | 0.582822 | 0.478261 | 2 | 0 | 0 |
| 2023-09 | 21 | -11.566667 | 0.516039 | 0.489362 | 2 | 0 | 0 |
| 2023-10 | 11 | -9.083333 | 0.310127 | 0.295455 | 0 | 0 | 0 |
| 2023-11 | 30 | -21.666667 | 0.330587 | 0.325581 | 1 | 0 | 0 |
| 2023-12 | 23 | -19.566667 | 0.256020 | 0.287129 | 0 | 0 | 0 |

### B_OPT2023_N6_W3_T2_SB1_TP3

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 225, entry dates 144, entry months 12; SKIP 2, EXCLUDED 3, exclusion share 0.013158; conditional FLAT CLOSED 214.
Net -161.550000 R; PF R / price 0.391067 / 0.401394; expectancy -0.718000 R; win rate 0.168889; average winner / loser 2.730263 / -1.441848 R.
Conditional CLOSED-only DD 161.550000 R; largest winner share 0.048193; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 12 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 16 | -15.800000 | 0.254717 | 0.212500 | 5 | 0 | 1 |
| 2023-02 | 28 | -26.083333 | 0.245783 | 0.222222 | 4 | 0 | 0 |
| 2023-03 | 24 | -8.633333 | 0.643986 | 0.752941 | 3 | 1 | 1 |
| 2023-04 | 21 | -15.766667 | 0.403531 | 0.422680 | 5 | 0 | 0 |
| 2023-05 | 13 | -3.716667 | 0.724010 | 0.897959 | 3 | 1 | 0 |
| 2023-06 | 16 | -21.800000 | 0.029674 | 0.024691 | 4 | 0 | 1 |
| 2023-07 | 13 | -3.133333 | 0.761421 | 0.769231 | 1 | 0 | 0 |
| 2023-08 | 9 | -5.866667 | 0.460123 | 0.326087 | 2 | 0 | 0 |
| 2023-09 | 21 | -18.066667 | 0.332512 | 0.342857 | 2 | 0 | 0 |
| 2023-10 | 11 | -7.416667 | 0.436709 | 0.409091 | 0 | 0 | 0 |
| 2023-11 | 30 | -17.100000 | 0.471679 | 0.465116 | 1 | 0 | 0 |
| 2023-12 | 23 | -18.166667 | 0.309252 | 0.356436 | 0 | 0 | 0 |

### B_OPT2023_N6_W3_T2_SB1_TP4

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 225, entry dates 144, entry months 12; SKIP 2, EXCLUDED 3, exclusion share 0.013158; conditional FLAT CLOSED 214.
Net -151.950000 R; PF R / price 0.427252 / 0.432271; expectancy -0.675333 R; win rate 0.168889; average winner / loser 2.982895 / -1.441848 R.
Conditional CLOSED-only DD 151.950000 R; largest winner share 0.058815; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 12 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 16 | -15.466667 | 0.270440 | 0.225000 | 5 | 0 | 1 |
| 2023-02 | 28 | -24.583333 | 0.289157 | 0.266667 | 4 | 0 | 0 |
| 2023-03 | 24 | -7.133333 | 0.705842 | 0.823529 | 3 | 1 | 1 |
| 2023-04 | 21 | -16.266667 | 0.384615 | 0.402062 | 5 | 0 | 0 |
| 2023-05 | 13 | -4.316667 | 0.679455 | 0.877551 | 3 | 1 | 0 |
| 2023-06 | 16 | -21.800000 | 0.029674 | 0.024691 | 4 | 0 | 1 |
| 2023-07 | 13 | -2.666667 | 0.796954 | 0.750000 | 1 | 0 | 0 |
| 2023-08 | 9 | -4.200000 | 0.613497 | 0.434783 | 2 | 0 | 0 |
| 2023-09 | 21 | -15.066667 | 0.443350 | 0.457143 | 2 | 0 | 0 |
| 2023-10 | 11 | -5.750000 | 0.563291 | 0.522727 | 0 | 0 | 0 |
| 2023-11 | 30 | -14.533333 | 0.550978 | 0.542636 | 1 | 0 | 0 |
| 2023-12 | 23 | -20.166667 | 0.233207 | 0.257426 | 0 | 0 | 0 |

### B_OPT2023_N6_W3_T2_SB1_TP5

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 224, entry dates 144, entry months 12; SKIP 2, EXCLUDED 3, exclusion share 0.013216; conditional FLAT CLOSED 213.
Net -144.233333 R; PF R / price 0.453247 / 0.457916; expectancy -0.643899 R; win rate 0.169643; average winner / loser 3.146491 / -1.441530 R.
Conditional CLOSED-only DD 144.233333 R; largest winner share 0.069696; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 12 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 16 | -15.466667 | 0.270440 | 0.225000 | 5 | 0 | 1 |
| 2023-02 | 28 | -23.083333 | 0.332530 | 0.311111 | 4 | 0 | 0 |
| 2023-03 | 24 | -8.383333 | 0.654296 | 0.764706 | 3 | 1 | 1 |
| 2023-04 | 21 | -14.766667 | 0.441362 | 0.463918 | 5 | 0 | 0 |
| 2023-05 | 13 | -2.916667 | 0.783416 | 1.020408 | 3 | 1 | 0 |
| 2023-06 | 16 | -21.800000 | 0.029674 | 0.024691 | 4 | 0 | 1 |
| 2023-07 | 13 | -1.000000 | 0.923858 | 0.846154 | 1 | 0 | 0 |
| 2023-08 | 9 | -2.533333 | 0.766871 | 0.543478 | 2 | 0 | 0 |
| 2023-09 | 20 | -16.566667 | 0.352021 | 0.363636 | 2 | 0 | 0 |
| 2023-10 | 11 | -4.083333 | 0.689873 | 0.636364 | 0 | 0 | 0 |
| 2023-11 | 30 | -13.466667 | 0.583934 | 0.589147 | 1 | 0 | 0 |
| 2023-12 | 23 | -20.166667 | 0.233207 | 0.257426 | 0 | 0 | 0 |

### B_OPT2023_N6_W3_T2_SB1_TP6

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 224, entry dates 144, entry months 12; SKIP 2, EXCLUDED 3, exclusion share 0.013216; conditional FLAT CLOSED 213.
Net -138.333333 R; PF R / price 0.475613 / 0.472946; expectancy -0.617560 R; win rate 0.169643; average winner / loser 3.301754 / -1.441530 R.
Conditional CLOSED-only DD 138.333333 R; largest winner share 0.079702; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 16 | -15.466667 | 0.270440 | 0.225000 | 5 | 0 | 1 |
| 2023-02 | 28 | -21.583333 | 0.375904 | 0.355556 | 4 | 0 | 0 |
| 2023-03 | 24 | -8.383333 | 0.654296 | 0.764706 | 3 | 1 | 1 |
| 2023-04 | 21 | -13.266667 | 0.498108 | 0.525773 | 5 | 0 | 0 |
| 2023-05 | 13 | -4.716667 | 0.649752 | 0.836735 | 3 | 1 | 0 |
| 2023-06 | 16 | -21.800000 | 0.029674 | 0.024691 | 4 | 0 | 1 |
| 2023-07 | 13 | 0.666667 | 1.050761 | 0.942308 | 1 | 0 | 0 |
| 2023-08 | 9 | -0.866667 | 0.920245 | 0.652174 | 2 | 0 | 0 |
| 2023-09 | 20 | -15.066667 | 0.410691 | 0.424242 | 2 | 0 | 0 |
| 2023-10 | 11 | -2.416667 | 0.816456 | 0.750000 | 0 | 0 | 0 |
| 2023-11 | 30 | -15.266667 | 0.528321 | 0.519380 | 1 | 0 | 0 |
| 2023-12 | 23 | -20.166667 | 0.233207 | 0.257426 | 0 | 0 | 0 |

### B_OPT2023_N6_W3_T2_SB1_TP7

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 224, entry dates 144, entry months 12; SKIP 2, EXCLUDED 3, exclusion share 0.013216; conditional FLAT CLOSED 213.
Net -137.333333 R; PF R / price 0.479404 / 0.471944; expectancy -0.613095 R; win rate 0.169643; average winner / loser 3.328070 / -1.441530 R.
Conditional CLOSED-only DD 137.333333 R; largest winner share 0.092251; largest positive month share 0.744681. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 16 | -15.466667 | 0.270440 | 0.225000 | 5 | 0 | 1 |
| 2023-02 | 28 | -21.333333 | 0.383133 | 0.362963 | 4 | 0 | 0 |
| 2023-03 | 24 | -8.383333 | 0.654296 | 0.764706 | 3 | 1 | 1 |
| 2023-04 | 21 | -13.516667 | 0.488651 | 0.515464 | 5 | 0 | 0 |
| 2023-05 | 13 | -4.716667 | 0.649752 | 0.836735 | 3 | 1 | 0 |
| 2023-06 | 16 | -21.800000 | 0.029674 | 0.024691 | 4 | 0 | 1 |
| 2023-07 | 13 | 2.333333 | 1.177665 | 1.038462 | 1 | 0 | 0 |
| 2023-08 | 9 | 0.800000 | 1.073620 | 0.760870 | 2 | 0 | 0 |
| 2023-09 | 20 | -19.066667 | 0.254237 | 0.262626 | 2 | 0 | 0 |
| 2023-10 | 11 | -0.750000 | 0.943038 | 0.863636 | 0 | 0 | 0 |
| 2023-11 | 30 | -15.266667 | 0.528321 | 0.519380 | 1 | 0 | 0 |
| 2023-12 | 23 | -20.166667 | 0.233207 | 0.257426 | 0 | 0 | 0 |

### B_OPT2023_N6_W3_T2_SB1_TP8

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 224, entry dates 144, entry months 12; SKIP 2, EXCLUDED 3, exclusion share 0.013216; conditional FLAT CLOSED 213.
Net -137.000000 R; PF R / price 0.480667 / 0.472946; expectancy -0.611607 R; win rate 0.169643; average winner / loser 3.336842 / -1.441530 R.
Conditional CLOSED-only DD 137.000000 R; largest winner share 0.105152; largest positive month share 0.729064. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 16 | -15.466667 | 0.270440 | 0.225000 | 5 | 0 | 1 |
| 2023-02 | 28 | -21.333333 | 0.383133 | 0.362963 | 4 | 0 | 0 |
| 2023-03 | 24 | -8.383333 | 0.654296 | 0.764706 | 3 | 1 | 1 |
| 2023-04 | 21 | -13.516667 | 0.488651 | 0.515464 | 5 | 0 | 0 |
| 2023-05 | 13 | -4.716667 | 0.649752 | 0.836735 | 3 | 1 | 0 |
| 2023-06 | 16 | -21.800000 | 0.029674 | 0.024691 | 4 | 0 | 1 |
| 2023-07 | 13 | -0.666667 | 0.949239 | 0.865385 | 1 | 0 | 0 |
| 2023-08 | 9 | 2.466667 | 1.226994 | 0.869565 | 2 | 0 | 0 |
| 2023-09 | 20 | -19.066667 | 0.254237 | 0.262626 | 2 | 0 | 0 |
| 2023-10 | 11 | 0.916667 | 1.069620 | 0.977273 | 0 | 0 | 0 |
| 2023-11 | 30 | -15.266667 | 0.528321 | 0.519380 | 1 | 0 | 0 |
| 2023-12 | 23 | -20.166667 | 0.233207 | 0.257426 | 0 | 0 | 0 |

### B_OPT2023_N6_W3_T2_SB1_TP9

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 224, entry dates 144, entry months 12; SKIP 2, EXCLUDED 3, exclusion share 0.013216; conditional FLAT CLOSED 213.
Net -144.333333 R; PF R / price 0.452868 / 0.450902; expectancy -0.644345 R; win rate 0.169643; average winner / loser 3.143860 / -1.441530 R.
Conditional CLOSED-only DD 144.333333 R; largest winner share 0.125558; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 16 | -15.466667 | 0.270440 | 0.225000 | 5 | 0 | 1 |
| 2023-02 | 28 | -21.333333 | 0.383133 | 0.362963 | 4 | 0 | 0 |
| 2023-03 | 24 | -8.383333 | 0.654296 | 0.764706 | 3 | 1 | 1 |
| 2023-04 | 21 | -13.516667 | 0.488651 | 0.515464 | 5 | 0 | 0 |
| 2023-05 | 13 | -4.716667 | 0.649752 | 0.836735 | 3 | 1 | 0 |
| 2023-06 | 16 | -21.800000 | 0.029674 | 0.024691 | 4 | 0 | 1 |
| 2023-07 | 13 | -0.666667 | 0.949239 | 0.865385 | 1 | 0 | 0 |
| 2023-08 | 9 | 4.133333 | 1.380368 | 0.978261 | 2 | 0 | 0 |
| 2023-09 | 20 | -19.066667 | 0.254237 | 0.262626 | 2 | 0 | 0 |
| 2023-10 | 11 | -8.083333 | 0.386076 | 0.363636 | 0 | 0 | 0 |
| 2023-11 | 30 | -15.266667 | 0.528321 | 0.519380 | 1 | 0 | 0 |
| 2023-12 | 23 | -20.166667 | 0.233207 | 0.257426 | 0 | 0 | 0 |

### B_OPT2023_N6_W3_T2_SB1_TP10

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 224, entry dates 144, entry months 12; SKIP 2, EXCLUDED 3, exclusion share 0.013216; conditional FLAT CLOSED 213.
Net -142.666667 R; PF R / price 0.459186 / 0.455912; expectancy -0.636905 R; win rate 0.169643; average winner / loser 3.187719 / -1.441530 R.
Conditional CLOSED-only DD 142.666667 R; largest winner share 0.137589; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 16 | -15.466667 | 0.270440 | 0.225000 | 5 | 0 | 1 |
| 2023-02 | 28 | -21.333333 | 0.383133 | 0.362963 | 4 | 0 | 0 |
| 2023-03 | 24 | -8.383333 | 0.654296 | 0.764706 | 3 | 1 | 1 |
| 2023-04 | 21 | -13.516667 | 0.488651 | 0.515464 | 5 | 0 | 0 |
| 2023-05 | 13 | -4.716667 | 0.649752 | 0.836735 | 3 | 1 | 0 |
| 2023-06 | 16 | -21.800000 | 0.029674 | 0.024691 | 4 | 0 | 1 |
| 2023-07 | 13 | -0.666667 | 0.949239 | 0.865385 | 1 | 0 | 0 |
| 2023-08 | 9 | 5.800000 | 1.533742 | 1.086957 | 2 | 0 | 0 |
| 2023-09 | 20 | -19.066667 | 0.254237 | 0.262626 | 2 | 0 | 0 |
| 2023-10 | 11 | -8.083333 | 0.386076 | 0.363636 | 0 | 0 | 0 |
| 2023-11 | 30 | -15.266667 | 0.528321 | 0.519380 | 1 | 0 | 0 |
| 2023-12 | 23 | -20.166667 | 0.233207 | 0.257426 | 0 | 0 | 0 |

### B_OPT2023_N6_W3_T3_SB1_TP2

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 104, entry dates 85, entry months 12; SKIP 1, EXCLUDED 1, exclusion share 0.009524; conditional FLAT CLOSED 78.
Net -78.666667 R; PF R / price 0.367801 / 0.363043; expectancy -0.756410 R; win rate 0.173077; average winner / loser 2.542593 / -1.463922 R.
Conditional CLOSED-only DD 78.666667 R; largest winner share 0.072833; largest positive month share 0.613900. Positive / negative / zero months 3 / 9 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 12 | -13.666667 | 0.170040 | 0.222222 | 5 | 0 | 0 |
| 2023-02 | 12 | -9.200000 | 0.407725 | 0.379310 | 4 | 0 | 0 |
| 2023-03 | 15 | 2.650000 | 1.256039 | 1.378378 | 3 | 1 | 1 |
| 2023-04 | 11 | -6.300000 | 0.514139 | 0.416667 | 5 | 0 | 0 |
| 2023-05 | 5 | 1.500000 | 1.310345 | 1.375000 | 3 | 0 | 0 |
| 2023-06 | 5 | -5.566667 | 0.106952 | 0.086957 | 4 | 0 | 0 |
| 2023-07 | 9 | -8.066667 | 0.292398 | 0.227273 | 1 | 0 | 0 |
| 2023-08 | 3 | -4.300000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 10 | -14.616667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 4 | 0.166667 | 1.052632 | 0.909091 | 0 | 0 | 0 |
| 2023-11 | 9 | -6.866667 | 0.324590 | 0.457143 | 1 | 0 | 0 |
| 2023-12 | 9 | -14.400000 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N6_W3_T3_SB1_TP3

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors.
CLOSED 103, entry dates 85, entry months 12; SKIP 1, EXCLUDED 1, exclusion share 0.009615; conditional FLAT CLOSED 77.
Net -79.016667 R; PF R / price 0.376348 / 0.375536; expectancy -0.767152 R; win rate 0.155340; average winner / loser 2.980208 / -1.473256 R.
Conditional CLOSED-only DD 79.016667 R; largest winner share 0.104858; largest positive month share 0.432099. Positive / negative / zero months 3 / 9 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 12 | -16.066667 | 0.024291 | 0.031746 | 5 | 0 | 0 |
| 2023-02 | 12 | -7.366667 | 0.525751 | 0.500000 | 4 | 0 | 0 |
| 2023-03 | 14 | 4.300000 | 1.432161 | 1.600000 | 3 | 1 | 1 |
| 2023-04 | 11 | -15.633333 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 5 | 4.666667 | 1.965517 | 2.062500 | 3 | 0 | 0 |
| 2023-06 | 5 | -5.566667 | 0.106952 | 0.086957 | 4 | 0 | 0 |
| 2023-07 | 9 | -6.400000 | 0.438596 | 0.340909 | 1 | 0 | 0 |
| 2023-08 | 3 | -4.300000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 10 | -14.616667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 4 | 1.833333 | 1.578947 | 1.363636 | 0 | 0 | 0 |
| 2023-11 | 9 | -5.466667 | 0.462295 | 0.657143 | 1 | 0 | 0 |
| 2023-12 | 9 | -14.400000 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N6_W3_T3_SB1_TP4

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 103, entry dates 85, entry months 12; SKIP 1, EXCLUDED 1, exclusion share 0.009615; conditional FLAT CLOSED 77.
Net -71.616667 R; PF R / price 0.434754 / 0.431330; expectancy -0.695307 R; win rate 0.155340; average winner / loser 3.442708 / -1.473256 R.
Conditional CLOSED-only DD 71.616667 R; largest winner share 0.121029; largest positive month share 0.535452. Positive / negative / zero months 3 / 9 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 12 | -16.066667 | 0.024291 | 0.031746 | 5 | 0 | 0 |
| 2023-02 | 12 | -5.866667 | 0.622318 | 0.603448 | 4 | 0 | 0 |
| 2023-03 | 14 | 7.300000 | 1.733668 | 1.942857 | 3 | 1 | 1 |
| 2023-04 | 11 | -15.633333 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 5 | 2.833333 | 1.586207 | 1.500000 | 3 | 0 | 0 |
| 2023-06 | 5 | -5.566667 | 0.106952 | 0.086957 | 4 | 0 | 0 |
| 2023-07 | 9 | -4.733333 | 0.584795 | 0.454545 | 1 | 0 | 0 |
| 2023-08 | 3 | -4.300000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 10 | -14.616667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 4 | 3.500000 | 2.105263 | 1.818182 | 0 | 0 | 0 |
| 2023-11 | 9 | -4.066667 | 0.600000 | 0.857143 | 1 | 0 | 0 |
| 2023-12 | 9 | -14.400000 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N6_W3_T3_SB1_TP5

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors.
CLOSED 103, entry dates 85, entry months 12; SKIP 1, EXCLUDED 1, exclusion share 0.009615; conditional FLAT CLOSED 77.
Net -66.866667 R; PF R / price 0.472244 / 0.459227; expectancy -0.649191 R; win rate 0.155340; average winner / loser 3.739583 / -1.473256 R.
Conditional CLOSED-only DD 66.866667 R; largest winner share 0.139276; largest positive month share 0.403905. Positive / negative / zero months 3 / 9 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 12 | -16.066667 | 0.024291 | 0.031746 | 5 | 0 | 0 |
| 2023-02 | 12 | -4.366667 | 0.718884 | 0.706897 | 4 | 0 | 0 |
| 2023-03 | 14 | 6.550000 | 1.658291 | 1.857143 | 3 | 1 | 1 |
| 2023-04 | 11 | -15.633333 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 5 | 4.500000 | 1.931034 | 1.812500 | 3 | 0 | 0 |
| 2023-06 | 5 | -5.566667 | 0.106952 | 0.086957 | 4 | 0 | 0 |
| 2023-07 | 9 | -3.066667 | 0.730994 | 0.568182 | 1 | 0 | 0 |
| 2023-08 | 3 | -4.300000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 10 | -14.616667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 4 | 5.166667 | 2.631579 | 2.272727 | 0 | 0 | 0 |
| 2023-11 | 9 | -5.066667 | 0.501639 | 0.714286 | 1 | 0 | 0 |
| 2023-12 | 9 | -14.400000 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N6_W3_T3_SB1_TP6

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors.
CLOSED 103, entry dates 85, entry months 12; SKIP 1, EXCLUDED 1, exclusion share 0.009615; conditional FLAT CLOSED 77.
Net -60.366667 R; PF R / price 0.523546 / 0.504292; expectancy -0.586084 R; win rate 0.155340; average winner / loser 4.145833 / -1.473256 R.
Conditional CLOSED-only DD 60.366667 R; largest winner share 0.150754; largest positive month share 0.349531. Positive / negative / zero months 3 / 9 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 12 | -16.066667 | 0.024291 | 0.031746 | 5 | 0 | 0 |
| 2023-02 | 12 | -2.866667 | 0.815451 | 0.810345 | 4 | 0 | 0 |
| 2023-03 | 14 | 6.550000 | 1.658291 | 1.857143 | 3 | 1 | 1 |
| 2023-04 | 11 | -15.633333 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 5 | 6.166667 | 2.275862 | 2.125000 | 3 | 0 | 0 |
| 2023-06 | 5 | -5.566667 | 0.106952 | 0.086957 | 4 | 0 | 0 |
| 2023-07 | 9 | -1.400000 | 0.877193 | 0.681818 | 1 | 0 | 0 |
| 2023-08 | 3 | -4.300000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 10 | -14.616667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 4 | 6.833333 | 3.157895 | 2.727273 | 0 | 0 | 0 |
| 2023-11 | 9 | -5.066667 | 0.501639 | 0.714286 | 1 | 0 | 0 |
| 2023-12 | 9 | -14.400000 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N6_W3_T3_SB1_TP7

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors.
CLOSED 103, entry dates 85, entry months 12; SKIP 1, EXCLUDED 1, exclusion share 0.009615; conditional FLAT CLOSED 77.
Net -55.116667 R; PF R / price 0.564983 / 0.538627; expectancy -0.535113 R; win rate 0.155340; average winner / loser 4.473958 / -1.473256 R.
Conditional CLOSED-only DD 55.116667 R; largest winner share 0.162980; largest positive month share 0.367171. Positive / negative / zero months 4 / 8 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 12 | -16.066667 | 0.024291 | 0.031746 | 5 | 0 | 0 |
| 2023-02 | 12 | -2.616667 | 0.831545 | 0.827586 | 4 | 0 | 0 |
| 2023-03 | 14 | 6.550000 | 1.658291 | 1.857143 | 3 | 1 | 1 |
| 2023-04 | 11 | -15.633333 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 5 | 7.833333 | 2.620690 | 2.437500 | 3 | 0 | 0 |
| 2023-06 | 5 | -5.566667 | 0.106952 | 0.086957 | 4 | 0 | 0 |
| 2023-07 | 9 | 0.266667 | 1.023392 | 0.795455 | 1 | 0 | 0 |
| 2023-08 | 3 | -4.300000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 10 | -14.616667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 4 | 8.500000 | 3.684211 | 3.181818 | 0 | 0 | 0 |
| 2023-11 | 9 | -5.066667 | 0.501639 | 0.714286 | 1 | 0 | 0 |
| 2023-12 | 9 | -14.400000 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N6_W3_T3_SB1_TP8

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors.
CLOSED 103, entry dates 85, entry months 12; SKIP 1, EXCLUDED 1, exclusion share 0.009615; conditional FLAT CLOSED 77.
Net -58.450000 R; PF R / price 0.538674 / 0.517167; expectancy -0.567476 R; win rate 0.155340; average winner / loser 4.265625 / -1.473256 R.
Conditional CLOSED-only DD 58.450000 R; largest winner share 0.195360; largest positive month share 0.450850. Positive / negative / zero months 3 / 9 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 12 | -16.066667 | 0.024291 | 0.031746 | 5 | 0 | 0 |
| 2023-02 | 12 | -2.616667 | 0.831545 | 0.827586 | 4 | 0 | 0 |
| 2023-03 | 14 | 6.550000 | 1.658291 | 1.857143 | 3 | 1 | 1 |
| 2023-04 | 11 | -15.633333 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 5 | 5.833333 | 2.206897 | 2.062500 | 3 | 0 | 0 |
| 2023-06 | 5 | -5.566667 | 0.106952 | 0.086957 | 4 | 0 | 0 |
| 2023-07 | 9 | -2.733333 | 0.760234 | 0.590909 | 1 | 0 | 0 |
| 2023-08 | 3 | -4.300000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 10 | -14.616667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 4 | 10.166667 | 4.210526 | 3.636364 | 0 | 0 | 0 |
| 2023-11 | 9 | -5.066667 | 0.501639 | 0.714286 | 1 | 0 | 0 |
| 2023-12 | 9 | -14.400000 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N6_W3_T3_SB1_TP9

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors.
CLOSED 103, entry dates 85, entry months 12; SKIP 1, EXCLUDED 1, exclusion share 0.009615; conditional FLAT CLOSED 77.
Net -67.450000 R; PF R / price 0.467640 / 0.459227; expectancy -0.654854 R; win rate 0.155340; average winner / loser 3.703125 / -1.473256 R.
Conditional CLOSED-only DD 67.450000 R; largest winner share 0.163150; largest positive month share 0.483395. Positive / negative / zero months 3 / 9 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 12 | -16.066667 | 0.024291 | 0.031746 | 5 | 0 | 0 |
| 2023-02 | 12 | -2.616667 | 0.831545 | 0.827586 | 4 | 0 | 0 |
| 2023-03 | 14 | 6.550000 | 1.658291 | 1.857143 | 3 | 1 | 1 |
| 2023-04 | 11 | -15.633333 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 5 | 5.833333 | 2.206897 | 2.062500 | 3 | 0 | 0 |
| 2023-06 | 5 | -5.566667 | 0.106952 | 0.086957 | 4 | 0 | 0 |
| 2023-07 | 9 | -2.733333 | 0.760234 | 0.590909 | 1 | 0 | 0 |
| 2023-08 | 3 | -4.300000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 10 | -14.616667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 4 | 1.166667 | 1.368421 | 1.181818 | 0 | 0 | 0 |
| 2023-11 | 9 | -5.066667 | 0.501639 | 0.714286 | 1 | 0 | 0 |
| 2023-12 | 9 | -14.400000 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N6_W3_T3_SB1_TP10

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors.
CLOSED 103, entry dates 85, entry months 12; SKIP 1, EXCLUDED 1, exclusion share 0.009615; conditional FLAT CLOSED 77.
Net -67.450000 R; PF R / price 0.467640 / 0.459227; expectancy -0.654854 R; win rate 0.155340; average winner / loser 3.703125 / -1.473256 R.
Conditional CLOSED-only DD 67.450000 R; largest winner share 0.163150; largest positive month share 0.483395. Positive / negative / zero months 3 / 9 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 12 | -16.066667 | 0.024291 | 0.031746 | 5 | 0 | 0 |
| 2023-02 | 12 | -2.616667 | 0.831545 | 0.827586 | 4 | 0 | 0 |
| 2023-03 | 14 | 6.550000 | 1.658291 | 1.857143 | 3 | 1 | 1 |
| 2023-04 | 11 | -15.633333 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 5 | 5.833333 | 2.206897 | 2.062500 | 3 | 0 | 0 |
| 2023-06 | 5 | -5.566667 | 0.106952 | 0.086957 | 4 | 0 | 0 |
| 2023-07 | 9 | -2.733333 | 0.760234 | 0.590909 | 1 | 0 | 0 |
| 2023-08 | 3 | -4.300000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 10 | -14.616667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 4 | 1.166667 | 1.368421 | 1.181818 | 0 | 0 | 0 |
| 2023-11 | 9 | -5.066667 | 0.501639 | 0.714286 | 1 | 0 | 0 |
| 2023-12 | 9 | -14.400000 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N7_W2_T2_SB1_TP2

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 72, entry dates 57, entry months 11; SKIP 1, EXCLUDED 0, exclusion share 0.000000; conditional FLAT CLOSED 0.
Net -47.866667 R; PF R / price 0.420851 / 0.456667; expectancy -0.664815 R; win rate 0.180556; average winner / loser 2.675641 / -1.425000 R.
Conditional CLOSED-only DD 47.866667 R; largest winner share 0.095831; largest positive month share 0.531507. Positive / negative / zero months 3 / 8 / 1; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 8 | -11.700000 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-02 | 5 | 6.466667 | 3.155556 | 2.833333 | 4 | 0 | 0 |
| 2023-03 | 10 | -8.350000 | 0.251121 | 0.341463 | 3 | 1 | 0 |
| 2023-04 | 8 | -10.133333 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 8 | 0.866667 | 1.112069 | 1.379310 | 3 | 0 | 0 |
| 2023-06 | 3 | 4.833333 | 4.222222 | 3.666667 | 4 | 0 | 0 |
| 2023-07 | 6 | -3.766667 | 0.469484 | 0.416667 | 1 | 0 | 0 |
| 2023-08 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 2 | 0 | 0 |
| 2023-09 | 6 | -9.566667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 3 | -2.066667 | 0.326087 | 0.333333 | 0 | 0 | 0 |
| 2023-11 | 10 | -6.716667 | 0.326087 | 0.342105 | 1 | 0 | 0 |
| 2023-12 | 5 | -7.733333 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N7_W2_T2_SB1_TP3

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 72, entry dates 57, entry months 11; SKIP 1, EXCLUDED 0, exclusion share 0.000000; conditional FLAT CLOSED 0.
Net -47.633333 R; PF R / price 0.443211 / 0.453674; expectancy -0.661574 R; win rate 0.152778; average winner / loser 3.446970 / -1.425833 R.
Conditional CLOSED-only DD 47.633333 R; largest winner share 0.131868; largest positive month share 0.508197. Positive / negative / zero months 2 / 9 / 1; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 8 | -11.700000 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-02 | 5 | 8.266667 | 3.755556 | 3.250000 | 4 | 0 | 0 |
| 2023-03 | 10 | -8.950000 | 0.197309 | 0.268293 | 3 | 1 | 0 |
| 2023-04 | 8 | -10.133333 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 8 | -6.433333 | 0.394984 | 0.500000 | 3 | 0 | 0 |
| 2023-06 | 3 | 8.000000 | 6.333333 | 5.500000 | 4 | 0 | 0 |
| 2023-07 | 6 | -2.100000 | 0.704225 | 0.625000 | 1 | 0 | 0 |
| 2023-08 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 2 | 0 | 0 |
| 2023-09 | 6 | -9.566667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 3 | -2.066667 | 0.326087 | 0.333333 | 0 | 0 | 0 |
| 2023-11 | 10 | -5.216667 | 0.476589 | 0.500000 | 1 | 0 | 0 |
| 2023-12 | 5 | -7.733333 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N7_W2_T2_SB1_TP4

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 71, entry dates 56, entry months 11; SKIP 1, EXCLUDED 1, exclusion share 0.013889; conditional FLAT CLOSED 31.
Net -56.566667 R; PF R / price 0.351424 / 0.367925; expectancy -0.796714 R; win rate 0.126761; average winner / loser 3.405556 / -1.429781 R.
Conditional CLOSED-only DD 56.566667 R; largest winner share 0.217510; largest positive month share 0.763547. Positive / negative / zero months 2 / 9 / 1; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 8 | -11.700000 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-02 | 5 | 1.600000 | 1.342857 | 1.411765 | 4 | 0 | 0 |
| 2023-03 | 10 | -8.950000 | 0.197309 | 0.268293 | 3 | 1 | 0 |
| 2023-04 | 8 | -10.133333 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 8 | -5.033333 | 0.526646 | 0.666667 | 3 | 0 | 0 |
| 2023-06 | 2 | 5.166667 | 4.444444 | 3.333333 | 4 | 0 | 1 |
| 2023-07 | 6 | -1.433333 | 0.798122 | 0.708333 | 1 | 0 | 0 |
| 2023-08 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 2 | 0 | 0 |
| 2023-09 | 6 | -9.566667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 3 | -2.066667 | 0.326087 | 0.333333 | 0 | 0 | 0 |
| 2023-11 | 10 | -6.716667 | 0.326087 | 0.342105 | 1 | 0 | 0 |
| 2023-12 | 5 | -7.733333 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N7_W2_T2_SB1_TP5

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors.
CLOSED 71, entry dates 56, entry months 11; SKIP 1, EXCLUDED 1, exclusion share 0.013889; conditional FLAT CLOSED 31.
Net -61.500000 R; PF R / price 0.294860 / 0.330189; expectancy -0.866197 R; win rate 0.126761; average winner / loser 2.857407 / -1.429781 R.
Conditional CLOSED-only DD 61.500000 R; largest winner share 0.272197; largest positive month share 1.000000. Positive / negative / zero months 1 / 10 / 1; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 8 | -11.700000 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-02 | 5 | 1.600000 | 1.342857 | 1.411765 | 4 | 0 | 0 |
| 2023-03 | 10 | -8.950000 | 0.197309 | 0.268293 | 3 | 1 | 0 |
| 2023-04 | 8 | -10.133333 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 8 | -3.633333 | 0.658307 | 0.833333 | 3 | 0 | 0 |
| 2023-06 | 2 | -1.166667 | 0.222222 | 0.166667 | 4 | 0 | 1 |
| 2023-07 | 6 | -1.433333 | 0.798122 | 0.708333 | 1 | 0 | 0 |
| 2023-08 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 2 | 0 | 0 |
| 2023-09 | 6 | -9.566667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 3 | -2.066667 | 0.326087 | 0.333333 | 0 | 0 | 0 |
| 2023-11 | 10 | -6.716667 | 0.326087 | 0.342105 | 1 | 0 | 0 |
| 2023-12 | 5 | -7.733333 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N7_W2_T2_SB1_TP6

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors.
CLOSED 71, entry dates 56, entry months 11; SKIP 1, EXCLUDED 1, exclusion share 0.013889; conditional FLAT CLOSED 31.
Net -60.100000 R; PF R / price 0.310912 / 0.352201; expectancy -0.846479 R; win rate 0.126761; average winner / loser 3.012963 / -1.429781 R.
Conditional CLOSED-only DD 60.100000 R; largest winner share 0.309773; largest positive month share 1.000000. Positive / negative / zero months 1 / 10 / 1; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 8 | -11.700000 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-02 | 5 | 1.600000 | 1.342857 | 1.411765 | 4 | 0 | 0 |
| 2023-03 | 10 | -8.950000 | 0.197309 | 0.268293 | 3 | 1 | 0 |
| 2023-04 | 8 | -10.133333 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 8 | -2.233333 | 0.789969 | 1.000000 | 3 | 0 | 0 |
| 2023-06 | 2 | -1.166667 | 0.222222 | 0.166667 | 4 | 0 | 1 |
| 2023-07 | 6 | -1.433333 | 0.798122 | 0.708333 | 1 | 0 | 0 |
| 2023-08 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 2 | 0 | 0 |
| 2023-09 | 6 | -9.566667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 3 | -2.066667 | 0.326087 | 0.333333 | 0 | 0 | 0 |
| 2023-11 | 10 | -6.716667 | 0.326087 | 0.342105 | 1 | 0 | 0 |
| 2023-12 | 5 | -7.733333 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N7_W2_T2_SB1_TP7

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors.
CLOSED 71, entry dates 56, entry months 11; SKIP 1, EXCLUDED 1, exclusion share 0.013889; conditional FLAT CLOSED 31.
Net -58.700000 R; PF R / price 0.326964 / 0.374214; expectancy -0.826761 R; win rate 0.126761; average winner / loser 3.168519 / -1.429781 R.
Conditional CLOSED-only DD 58.700000 R; largest winner share 0.343659; largest positive month share 1.000000. Positive / negative / zero months 1 / 10 / 1; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 8 | -11.700000 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-02 | 5 | 1.600000 | 1.342857 | 1.411765 | 4 | 0 | 0 |
| 2023-03 | 10 | -8.950000 | 0.197309 | 0.268293 | 3 | 1 | 0 |
| 2023-04 | 8 | -10.133333 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 8 | -0.833333 | 0.921630 | 1.166667 | 3 | 0 | 0 |
| 2023-06 | 2 | -1.166667 | 0.222222 | 0.166667 | 4 | 0 | 1 |
| 2023-07 | 6 | -1.433333 | 0.798122 | 0.708333 | 1 | 0 | 0 |
| 2023-08 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 2 | 0 | 0 |
| 2023-09 | 6 | -9.566667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 3 | -2.066667 | 0.326087 | 0.333333 | 0 | 0 | 0 |
| 2023-11 | 10 | -6.716667 | 0.326087 | 0.342105 | 1 | 0 | 0 |
| 2023-12 | 5 | -7.733333 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N7_W2_T2_SB1_TP8

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors.
CLOSED 71, entry dates 56, entry months 11; SKIP 1, EXCLUDED 1, exclusion share 0.013889; conditional FLAT CLOSED 31.
Net -57.300000 R; PF R / price 0.343015 / 0.396226; expectancy -0.807042 R; win rate 0.126761; average winner / loser 3.324074 / -1.429781 R.
Conditional CLOSED-only DD 57.300000 R; largest winner share 0.374373; largest positive month share 0.738462. Positive / negative / zero months 2 / 9 / 1; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 8 | -11.700000 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-02 | 5 | 1.600000 | 1.342857 | 1.411765 | 4 | 0 | 0 |
| 2023-03 | 10 | -8.950000 | 0.197309 | 0.268293 | 3 | 1 | 0 |
| 2023-04 | 8 | -10.133333 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 8 | 0.566667 | 1.053292 | 1.333333 | 3 | 0 | 0 |
| 2023-06 | 2 | -1.166667 | 0.222222 | 0.166667 | 4 | 0 | 1 |
| 2023-07 | 6 | -1.433333 | 0.798122 | 0.708333 | 1 | 0 | 0 |
| 2023-08 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 2 | 0 | 0 |
| 2023-09 | 6 | -9.566667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 3 | -2.066667 | 0.326087 | 0.333333 | 0 | 0 | 0 |
| 2023-11 | 10 | -6.716667 | 0.326087 | 0.342105 | 1 | 0 | 0 |
| 2023-12 | 5 | -7.733333 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N7_W2_T2_SB1_TP9

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors.
CLOSED 71, entry dates 56, entry months 11; SKIP 1, EXCLUDED 1, exclusion share 0.013889; conditional FLAT CLOSED 31.
Net -55.900000 R; PF R / price 0.359067 / 0.418239; expectancy -0.787324 R; win rate 0.126761; average winner / loser 3.479630 / -1.429781 R.
Conditional CLOSED-only DD 55.900000 R; largest winner share 0.402342; largest positive month share 0.551402. Positive / negative / zero months 2 / 9 / 1; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 8 | -11.700000 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-02 | 5 | 1.600000 | 1.342857 | 1.411765 | 4 | 0 | 0 |
| 2023-03 | 10 | -8.950000 | 0.197309 | 0.268293 | 3 | 1 | 0 |
| 2023-04 | 8 | -10.133333 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 8 | 1.966667 | 1.184953 | 1.500000 | 3 | 0 | 0 |
| 2023-06 | 2 | -1.166667 | 0.222222 | 0.166667 | 4 | 0 | 1 |
| 2023-07 | 6 | -1.433333 | 0.798122 | 0.708333 | 1 | 0 | 0 |
| 2023-08 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 2 | 0 | 0 |
| 2023-09 | 6 | -9.566667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 3 | -2.066667 | 0.326087 | 0.333333 | 0 | 0 | 0 |
| 2023-11 | 10 | -6.716667 | 0.326087 | 0.342105 | 1 | 0 | 0 |
| 2023-12 | 5 | -7.733333 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N7_W2_T2_SB1_TP10

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors.
CLOSED 71, entry dates 56, entry months 11; SKIP 1, EXCLUDED 1, exclusion share 0.013889; conditional FLAT CLOSED 31.
Net -54.500000 R; PF R / price 0.375119 / 0.440252; expectancy -0.767606 R; win rate 0.126761; average winner / loser 3.635185 / -1.429781 R.
Conditional CLOSED-only DD 54.500000 R; largest winner share 0.427916; largest positive month share 0.677852. Positive / negative / zero months 2 / 9 / 1; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 8 | -11.700000 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-02 | 5 | 1.600000 | 1.342857 | 1.411765 | 4 | 0 | 0 |
| 2023-03 | 10 | -8.950000 | 0.197309 | 0.268293 | 3 | 1 | 0 |
| 2023-04 | 8 | -10.133333 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 8 | 3.366667 | 1.316614 | 1.666667 | 3 | 0 | 0 |
| 2023-06 | 2 | -1.166667 | 0.222222 | 0.166667 | 4 | 0 | 1 |
| 2023-07 | 6 | -1.433333 | 0.798122 | 0.708333 | 1 | 0 | 0 |
| 2023-08 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 2 | 0 | 0 |
| 2023-09 | 6 | -9.566667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 3 | -2.066667 | 0.326087 | 0.333333 | 0 | 0 | 0 |
| 2023-11 | 10 | -6.716667 | 0.326087 | 0.342105 | 1 | 0 | 0 |
| 2023-12 | 5 | -7.733333 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N7_W2_T3_SB1_TP2

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 41, entry dates 36, entry months 11; SKIP 1, EXCLUDED 0, exclusion share 0.000000; conditional FLAT CLOSED 0.
Net -34.216667 R; PF R / price 0.290356 / 0.298780; expectancy -0.834553 R; win rate 0.146341; average winner / loser 2.333333 / -1.418137 R.
Conditional CLOSED-only DD 34.216667 R; largest winner share 0.238095; largest positive month share 0.620690. Positive / negative / zero months 2 / 9 / 1; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 7 | -10.033333 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-02 | 2 | 1.833333 | 2.222222 | 1.666667 | 4 | 0 | 0 |
| 2023-03 | 5 | -3.083333 | 0.097561 | 0.083333 | 3 | 1 | 0 |
| 2023-04 | 6 | -7.133333 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 4 | -1.733333 | 0.633803 | 0.705882 | 3 | 0 | 0 |
| 2023-06 | 1 | 3.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 4 | 0 | 0 |
| 2023-07 | 4 | -1.500000 | 0.689655 | 0.625000 | 1 | 0 | 0 |
| 2023-08 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 2 | 0 | 0 |
| 2023-09 | 3 | -5.000000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 2 | -0.666667 | 0.600000 | 0.800000 | 0 | 0 | 0 |
| 2023-11 | 5 | -6.833333 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-12 | 2 | -3.066667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N7_W2_T3_SB1_TP3

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors.
CLOSED 41, entry dates 36, entry months 11; SKIP 1, EXCLUDED 0, exclusion share 0.000000; conditional FLAT CLOSED 0.
Net -35.216667 R; PF R / price 0.291653 / 0.288235; expectancy -0.858943 R; win rate 0.121951; average winner / loser 2.900000 / -1.420476 R.
Conditional CLOSED-only DD 35.216667 R; largest winner share 0.344828; largest positive month share 0.658537. Positive / negative / zero months 3 / 8 / 1; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 7 | -10.033333 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-02 | 2 | 2.166667 | 2.444444 | 1.833333 | 4 | 0 | 0 |
| 2023-03 | 5 | -3.083333 | 0.097561 | 0.083333 | 3 | 1 | 0 |
| 2023-04 | 6 | -7.133333 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 4 | -6.233333 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-06 | 1 | 4.500000 | NOT_AVAILABLE | NOT_AVAILABLE | 4 | 0 | 0 |
| 2023-07 | 4 | 0.166667 | 1.034483 | 0.937500 | 1 | 0 | 0 |
| 2023-08 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 2 | 0 | 0 |
| 2023-09 | 3 | -5.000000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 2 | -0.666667 | 0.600000 | 0.800000 | 0 | 0 | 0 |
| 2023-11 | 5 | -6.833333 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-12 | 2 | -3.066667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N7_W2_T3_SB1_TP4

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors.
CLOSED 40, entry dates 35, entry months 10; SKIP 1, EXCLUDED 1, exclusion share 0.024390; conditional FLAT CLOSED 16.
Net -39.050000 R; PF R / price 0.214549 / 0.194118; expectancy -0.976250 R; win rate 0.100000; average winner / loser 2.666667 / -1.420476 R.
Conditional CLOSED-only DD 39.050000 R; largest winner share 0.531250; largest positive month share 0.722222. Positive / negative / zero months 2 / 8 / 2; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 7 | -10.033333 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-02 | 2 | 2.166667 | 2.444444 | 1.833333 | 4 | 0 | 0 |
| 2023-03 | 5 | -3.083333 | 0.097561 | 0.083333 | 3 | 1 | 0 |
| 2023-04 | 6 | -7.133333 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 4 | -6.233333 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-06 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 4 | 0 | 1 |
| 2023-07 | 4 | 0.833333 | 1.172414 | 1.062500 | 1 | 0 | 0 |
| 2023-08 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 2 | 0 | 0 |
| 2023-09 | 3 | -5.000000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 2 | -0.666667 | 0.600000 | 0.800000 | 0 | 0 | 0 |
| 2023-11 | 5 | -6.833333 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-12 | 2 | -3.066667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N7_W2_T3_SB1_TP5

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors.
CLOSED 40, entry dates 35, entry months 10; SKIP 1, EXCLUDED 1, exclusion share 0.024390; conditional FLAT CLOSED 16.
Net -39.050000 R; PF R / price 0.214549 / 0.194118; expectancy -0.976250 R; win rate 0.100000; average winner / loser 2.666667 / -1.420476 R.
Conditional CLOSED-only DD 39.050000 R; largest winner share 0.531250; largest positive month share 0.722222. Positive / negative / zero months 2 / 8 / 2; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 7 | -10.033333 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-02 | 2 | 2.166667 | 2.444444 | 1.833333 | 4 | 0 | 0 |
| 2023-03 | 5 | -3.083333 | 0.097561 | 0.083333 | 3 | 1 | 0 |
| 2023-04 | 6 | -7.133333 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 4 | -6.233333 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-06 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 4 | 0 | 1 |
| 2023-07 | 4 | 0.833333 | 1.172414 | 1.062500 | 1 | 0 | 0 |
| 2023-08 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 2 | 0 | 0 |
| 2023-09 | 3 | -5.000000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 2 | -0.666667 | 0.600000 | 0.800000 | 0 | 0 | 0 |
| 2023-11 | 5 | -6.833333 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-12 | 2 | -3.066667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N7_W2_T3_SB1_TP6

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors.
CLOSED 40, entry dates 35, entry months 10; SKIP 1, EXCLUDED 1, exclusion share 0.024390; conditional FLAT CLOSED 16.
Net -39.050000 R; PF R / price 0.214549 / 0.194118; expectancy -0.976250 R; win rate 0.100000; average winner / loser 2.666667 / -1.420476 R.
Conditional CLOSED-only DD 39.050000 R; largest winner share 0.531250; largest positive month share 0.722222. Positive / negative / zero months 2 / 8 / 2; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 7 | -10.033333 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-02 | 2 | 2.166667 | 2.444444 | 1.833333 | 4 | 0 | 0 |
| 2023-03 | 5 | -3.083333 | 0.097561 | 0.083333 | 3 | 1 | 0 |
| 2023-04 | 6 | -7.133333 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 4 | -6.233333 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-06 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 4 | 0 | 1 |
| 2023-07 | 4 | 0.833333 | 1.172414 | 1.062500 | 1 | 0 | 0 |
| 2023-08 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 2 | 0 | 0 |
| 2023-09 | 3 | -5.000000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 2 | -0.666667 | 0.600000 | 0.800000 | 0 | 0 | 0 |
| 2023-11 | 5 | -6.833333 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-12 | 2 | -3.066667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N7_W2_T3_SB1_TP7

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors.
CLOSED 40, entry dates 35, entry months 10; SKIP 1, EXCLUDED 1, exclusion share 0.024390; conditional FLAT CLOSED 16.
Net -39.050000 R; PF R / price 0.214549 / 0.194118; expectancy -0.976250 R; win rate 0.100000; average winner / loser 2.666667 / -1.420476 R.
Conditional CLOSED-only DD 39.050000 R; largest winner share 0.531250; largest positive month share 0.722222. Positive / negative / zero months 2 / 8 / 2; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 7 | -10.033333 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-02 | 2 | 2.166667 | 2.444444 | 1.833333 | 4 | 0 | 0 |
| 2023-03 | 5 | -3.083333 | 0.097561 | 0.083333 | 3 | 1 | 0 |
| 2023-04 | 6 | -7.133333 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 4 | -6.233333 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-06 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 4 | 0 | 1 |
| 2023-07 | 4 | 0.833333 | 1.172414 | 1.062500 | 1 | 0 | 0 |
| 2023-08 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 2 | 0 | 0 |
| 2023-09 | 3 | -5.000000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 2 | -0.666667 | 0.600000 | 0.800000 | 0 | 0 | 0 |
| 2023-11 | 5 | -6.833333 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-12 | 2 | -3.066667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N7_W2_T3_SB1_TP8

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors.
CLOSED 40, entry dates 35, entry months 10; SKIP 1, EXCLUDED 1, exclusion share 0.024390; conditional FLAT CLOSED 16.
Net -39.050000 R; PF R / price 0.214549 / 0.194118; expectancy -0.976250 R; win rate 0.100000; average winner / loser 2.666667 / -1.420476 R.
Conditional CLOSED-only DD 39.050000 R; largest winner share 0.531250; largest positive month share 0.722222. Positive / negative / zero months 2 / 8 / 2; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 7 | -10.033333 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-02 | 2 | 2.166667 | 2.444444 | 1.833333 | 4 | 0 | 0 |
| 2023-03 | 5 | -3.083333 | 0.097561 | 0.083333 | 3 | 1 | 0 |
| 2023-04 | 6 | -7.133333 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 4 | -6.233333 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-06 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 4 | 0 | 1 |
| 2023-07 | 4 | 0.833333 | 1.172414 | 1.062500 | 1 | 0 | 0 |
| 2023-08 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 2 | 0 | 0 |
| 2023-09 | 3 | -5.000000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 2 | -0.666667 | 0.600000 | 0.800000 | 0 | 0 | 0 |
| 2023-11 | 5 | -6.833333 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-12 | 2 | -3.066667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N7_W2_T3_SB1_TP9

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors.
CLOSED 40, entry dates 35, entry months 10; SKIP 1, EXCLUDED 1, exclusion share 0.024390; conditional FLAT CLOSED 16.
Net -39.050000 R; PF R / price 0.214549 / 0.194118; expectancy -0.976250 R; win rate 0.100000; average winner / loser 2.666667 / -1.420476 R.
Conditional CLOSED-only DD 39.050000 R; largest winner share 0.531250; largest positive month share 0.722222. Positive / negative / zero months 2 / 8 / 2; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 7 | -10.033333 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-02 | 2 | 2.166667 | 2.444444 | 1.833333 | 4 | 0 | 0 |
| 2023-03 | 5 | -3.083333 | 0.097561 | 0.083333 | 3 | 1 | 0 |
| 2023-04 | 6 | -7.133333 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 4 | -6.233333 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-06 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 4 | 0 | 1 |
| 2023-07 | 4 | 0.833333 | 1.172414 | 1.062500 | 1 | 0 | 0 |
| 2023-08 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 2 | 0 | 0 |
| 2023-09 | 3 | -5.000000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 2 | -0.666667 | 0.600000 | 0.800000 | 0 | 0 | 0 |
| 2023-11 | 5 | -6.833333 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-12 | 2 | -3.066667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N7_W2_T3_SB1_TP10

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors.
CLOSED 40, entry dates 35, entry months 10; SKIP 1, EXCLUDED 1, exclusion share 0.024390; conditional FLAT CLOSED 16.
Net -39.050000 R; PF R / price 0.214549 / 0.194118; expectancy -0.976250 R; win rate 0.100000; average winner / loser 2.666667 / -1.420476 R.
Conditional CLOSED-only DD 39.050000 R; largest winner share 0.531250; largest positive month share 0.722222. Positive / negative / zero months 2 / 8 / 2; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 7 | -10.033333 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-02 | 2 | 2.166667 | 2.444444 | 1.833333 | 4 | 0 | 0 |
| 2023-03 | 5 | -3.083333 | 0.097561 | 0.083333 | 3 | 1 | 0 |
| 2023-04 | 6 | -7.133333 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 4 | -6.233333 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-06 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 4 | 0 | 1 |
| 2023-07 | 4 | 0.833333 | 1.172414 | 1.062500 | 1 | 0 | 0 |
| 2023-08 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 2 | 0 | 0 |
| 2023-09 | 3 | -5.000000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 2 | -0.666667 | 0.600000 | 0.800000 | 0 | 0 | 0 |
| 2023-11 | 5 | -6.833333 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-12 | 2 | -3.066667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N7_W3_T2_SB1_TP2

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 124, entry dates 87, entry months 12; SKIP 1, EXCLUDED 2, exclusion share 0.015873; conditional FLAT CLOSED 119.
Net -85.833333 R; PF R / price 0.407433 / 0.406534; expectancy -0.692204 R; win rate 0.177419; average winner / loser 2.682576 / -1.434158 R.
Conditional CLOSED-only DD 86.000000 R; largest winner share 0.056481; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 9 | -7.566667 | 0.305810 | 0.250000 | 5 | 0 | 1 |
| 2023-02 | 12 | -1.616667 | 0.854135 | 0.772727 | 4 | 0 | 0 |
| 2023-03 | 16 | -17.150000 | 0.140351 | 0.177215 | 3 | 1 | 0 |
| 2023-04 | 12 | -11.666667 | 0.204545 | 0.218182 | 5 | 0 | 0 |
| 2023-05 | 10 | -2.033333 | 0.808777 | 0.952381 | 3 | 0 | 0 |
| 2023-06 | 4 | 3.166667 | 2.000000 | 2.000000 | 4 | 0 | 1 |
| 2023-07 | 7 | -1.400000 | 0.826446 | 0.740741 | 1 | 0 | 0 |
| 2023-08 | 11 | -1.666667 | 0.850299 | 0.772727 | 2 | 0 | 0 |
| 2023-09 | 15 | -12.566667 | 0.323160 | 0.311688 | 2 | 0 | 0 |
| 2023-10 | 6 | -6.883333 | 0.126850 | 0.129032 | 0 | 0 | 0 |
| 2023-11 | 13 | -17.150000 | 0.014368 | 0.015625 | 1 | 0 | 0 |
| 2023-12 | 9 | -9.300000 | 0.184211 | 0.243243 | 0 | 0 | 0 |

### B_OPT2023_N7_W3_T2_SB1_TP3

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 124, entry dates 87, entry months 12; SKIP 1, EXCLUDED 2, exclusion share 0.015873; conditional FLAT CLOSED 119.
Net -76.533333 R; PF R / price 0.482008 / 0.457447; expectancy -0.617204 R; win rate 0.161290; average winner / loser 3.560833 / -1.434466 R.
Conditional CLOSED-only DD 78.366667 R; largest winner share 0.070208; largest positive month share 0.558824. Positive / negative / zero months 3 / 9 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 9 | -5.900000 | 0.458716 | 0.375000 | 5 | 0 | 1 |
| 2023-02 | 12 | -1.816667 | 0.836090 | 0.659091 | 4 | 0 | 0 |
| 2023-03 | 16 | -17.750000 | 0.110276 | 0.139241 | 3 | 1 | 0 |
| 2023-04 | 12 | -10.166667 | 0.306818 | 0.327273 | 5 | 0 | 0 |
| 2023-05 | 10 | -9.333333 | 0.310345 | 0.381818 | 3 | 0 | 0 |
| 2023-06 | 4 | 6.333333 | 3.000000 | 3.000000 | 4 | 0 | 1 |
| 2023-07 | 7 | 1.933333 | 1.239669 | 1.111111 | 1 | 0 | 0 |
| 2023-08 | 11 | 3.066667 | 1.275449 | 1.159091 | 2 | 0 | 0 |
| 2023-09 | 15 | -9.566667 | 0.484740 | 0.467532 | 2 | 0 | 0 |
| 2023-10 | 6 | -6.883333 | 0.126850 | 0.129032 | 0 | 0 | 0 |
| 2023-11 | 13 | -17.150000 | 0.014368 | 0.015625 | 1 | 0 | 0 |
| 2023-12 | 9 | -9.300000 | 0.184211 | 0.243243 | 0 | 0 | 0 |

### B_OPT2023_N7_W3_T2_SB1_TP4

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors.
CLOSED 123, entry dates 86, entry months 12; SKIP 1, EXCLUDED 3, exclusion share 0.023810; conditional FLAT CLOSED 118.
Net -77.233333 R; PF R / price 0.483101 / 0.458699; expectancy -0.627913 R; win rate 0.146341; average winner / loser 4.010185 / -1.436699 R.
Conditional CLOSED-only DD 79.400000 R; largest winner share 0.092357; largest positive month share 0.466819. Positive / negative / zero months 3 / 9 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 9 | -5.566667 | 0.489297 | 0.400000 | 5 | 0 | 1 |
| 2023-02 | 12 | -8.483333 | 0.334641 | 0.285714 | 4 | 0 | 0 |
| 2023-03 | 16 | -17.750000 | 0.110276 | 0.139241 | 3 | 1 | 0 |
| 2023-04 | 12 | -12.166667 | 0.170455 | 0.181818 | 5 | 0 | 0 |
| 2023-05 | 10 | -7.933333 | 0.413793 | 0.509091 | 3 | 0 | 0 |
| 2023-06 | 3 | 3.500000 | 2.105263 | 1.818182 | 4 | 0 | 2 |
| 2023-07 | 7 | 4.266667 | 1.528926 | 1.370370 | 1 | 0 | 0 |
| 2023-08 | 11 | 6.800000 | 1.610778 | 1.431818 | 2 | 0 | 0 |
| 2023-09 | 15 | -6.566667 | 0.646320 | 0.623377 | 2 | 0 | 0 |
| 2023-10 | 6 | -6.883333 | 0.126850 | 0.129032 | 0 | 0 | 0 |
| 2023-11 | 13 | -17.150000 | 0.014368 | 0.015625 | 1 | 0 | 0 |
| 2023-12 | 9 | -9.300000 | 0.184211 | 0.243243 | 0 | 0 | 0 |

### B_OPT2023_N7_W3_T2_SB1_TP5

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 123, entry dates 86, entry months 12; SKIP 1, EXCLUDED 3, exclusion share 0.023810; conditional FLAT CLOSED 118.
Net -82.166667 R; PF R / price 0.456150 / 0.437282; expectancy -0.668022 R; win rate 0.138211; average winner / loser 4.053922 / -1.438889 R.
Conditional CLOSED-only DD 84.333333 R; largest winner share 0.120919; largest positive month share 0.528190. Positive / negative / zero months 3 / 9 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 9 | -5.566667 | 0.489297 | 0.400000 | 5 | 0 | 1 |
| 2023-02 | 12 | -8.483333 | 0.334641 | 0.285714 | 4 | 0 | 0 |
| 2023-03 | 16 | -17.750000 | 0.110276 | 0.139241 | 3 | 1 | 0 |
| 2023-04 | 12 | -12.166667 | 0.170455 | 0.181818 | 5 | 0 | 0 |
| 2023-05 | 10 | -6.533333 | 0.517241 | 0.636364 | 3 | 0 | 0 |
| 2023-06 | 3 | 5.166667 | 2.631579 | 2.272727 | 4 | 0 | 2 |
| 2023-07 | 7 | 5.933333 | 1.735537 | 1.555556 | 1 | 0 | 0 |
| 2023-08 | 11 | 0.133333 | 1.010417 | 0.979592 | 2 | 0 | 0 |
| 2023-09 | 15 | -9.566667 | 0.484740 | 0.467532 | 2 | 0 | 0 |
| 2023-10 | 6 | -6.883333 | 0.126850 | 0.129032 | 0 | 0 | 0 |
| 2023-11 | 13 | -17.150000 | 0.014368 | 0.015625 | 1 | 0 | 0 |
| 2023-12 | 9 | -9.300000 | 0.184211 | 0.243243 | 0 | 0 | 0 |

### B_OPT2023_N7_W3_T2_SB1_TP6

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 123, entry dates 86, entry months 12; SKIP 1, EXCLUDED 3, exclusion share 0.023810; conditional FLAT CLOSED 118.
Net -78.600000 R; PF R / price 0.479757 / 0.463415; expectancy -0.639024 R; win rate 0.138211; average winner / loser 4.263725 / -1.438889 R.
Conditional CLOSED-only DD 80.766667 R; largest winner share 0.137963; largest positive month share 0.574230. Positive / negative / zero months 3 / 9 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 9 | -5.566667 | 0.489297 | 0.400000 | 5 | 0 | 1 |
| 2023-02 | 12 | -8.483333 | 0.334641 | 0.285714 | 4 | 0 | 0 |
| 2023-03 | 16 | -17.750000 | 0.110276 | 0.139241 | 3 | 1 | 0 |
| 2023-04 | 12 | -12.166667 | 0.170455 | 0.181818 | 5 | 0 | 0 |
| 2023-05 | 10 | -5.133333 | 0.620690 | 0.763636 | 3 | 0 | 0 |
| 2023-06 | 3 | 6.833333 | 3.157895 | 2.727273 | 4 | 0 | 2 |
| 2023-07 | 7 | 3.266667 | 1.404959 | 1.259259 | 1 | 0 | 0 |
| 2023-08 | 11 | 1.800000 | 1.140625 | 1.081633 | 2 | 0 | 0 |
| 2023-09 | 15 | -8.066667 | 0.565530 | 0.545455 | 2 | 0 | 0 |
| 2023-10 | 6 | -6.883333 | 0.126850 | 0.129032 | 0 | 0 | 0 |
| 2023-11 | 13 | -17.150000 | 0.014368 | 0.015625 | 1 | 0 | 0 |
| 2023-12 | 9 | -9.300000 | 0.184211 | 0.243243 | 0 | 0 | 0 |

### B_OPT2023_N7_W3_T2_SB1_TP7

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 123, entry dates 86, entry months 12; SKIP 1, EXCLUDED 3, exclusion share 0.023810; conditional FLAT CLOSED 118.
Net -77.866667 R; PF R / price 0.484611 / 0.465157; expectancy -0.633062 R; win rate 0.138211; average winner / loser 4.306863 / -1.438889 R.
Conditional CLOSED-only DD 80.033333 R; largest winner share 0.159344; largest positive month share 0.557987. Positive / negative / zero months 3 / 9 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 9 | -5.566667 | 0.489297 | 0.400000 | 5 | 0 | 1 |
| 2023-02 | 12 | -8.483333 | 0.334641 | 0.285714 | 4 | 0 | 0 |
| 2023-03 | 16 | -17.750000 | 0.110276 | 0.139241 | 3 | 1 | 0 |
| 2023-04 | 12 | -12.166667 | 0.170455 | 0.181818 | 5 | 0 | 0 |
| 2023-05 | 10 | -3.733333 | 0.724138 | 0.890909 | 3 | 0 | 0 |
| 2023-06 | 3 | 8.500000 | 3.684211 | 3.181818 | 4 | 0 | 2 |
| 2023-07 | 7 | 3.266667 | 1.404959 | 1.259259 | 1 | 0 | 0 |
| 2023-08 | 11 | 3.466667 | 1.270833 | 1.183673 | 2 | 0 | 0 |
| 2023-09 | 15 | -12.066667 | 0.350090 | 0.337662 | 2 | 0 | 0 |
| 2023-10 | 6 | -6.883333 | 0.126850 | 0.129032 | 0 | 0 | 0 |
| 2023-11 | 13 | -17.150000 | 0.014368 | 0.015625 | 1 | 0 | 0 |
| 2023-12 | 9 | -9.300000 | 0.184211 | 0.243243 | 0 | 0 | 0 |

### B_OPT2023_N7_W3_T2_SB1_TP8

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 123, entry dates 86, entry months 12; SKIP 1, EXCLUDED 3, exclusion share 0.023810; conditional FLAT CLOSED 118.
Net -73.133333 R; PF R / price 0.515940 / 0.494774; expectancy -0.594580 R; win rate 0.138211; average winner / loser 4.585294 / -1.438889 R.
Conditional CLOSED-only DD 75.300000 R; largest winner share 0.171050; largest positive month share 0.547576. Positive / negative / zero months 3 / 9 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 9 | -5.566667 | 0.489297 | 0.400000 | 5 | 0 | 1 |
| 2023-02 | 12 | -8.483333 | 0.334641 | 0.285714 | 4 | 0 | 0 |
| 2023-03 | 16 | -17.750000 | 0.110276 | 0.139241 | 3 | 1 | 0 |
| 2023-04 | 12 | -12.166667 | 0.170455 | 0.181818 | 5 | 0 | 0 |
| 2023-05 | 10 | -2.333333 | 0.827586 | 1.018182 | 3 | 0 | 0 |
| 2023-06 | 3 | 10.166667 | 4.210526 | 3.636364 | 4 | 0 | 2 |
| 2023-07 | 7 | 3.266667 | 1.404959 | 1.259259 | 1 | 0 | 0 |
| 2023-08 | 11 | 5.133333 | 1.401042 | 1.285714 | 2 | 0 | 0 |
| 2023-09 | 15 | -12.066667 | 0.350090 | 0.337662 | 2 | 0 | 0 |
| 2023-10 | 6 | -6.883333 | 0.126850 | 0.129032 | 0 | 0 | 0 |
| 2023-11 | 13 | -17.150000 | 0.014368 | 0.015625 | 1 | 0 | 0 |
| 2023-12 | 9 | -9.300000 | 0.184211 | 0.243243 | 0 | 0 | 0 |

### B_OPT2023_N7_W3_T2_SB1_TP9

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 123, entry dates 86, entry months 12; SKIP 1, EXCLUDED 3, exclusion share 0.023810; conditional FLAT CLOSED 118.
Net -68.400000 R; PF R / price 0.547270 / 0.524390; expectancy -0.556098 R; win rate 0.138211; average winner / loser 4.863725 / -1.438889 R.
Conditional CLOSED-only DD 70.566667 R; largest winner share 0.181415; largest positive month share 0.540335. Positive / negative / zero months 3 / 9 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 9 | -5.566667 | 0.489297 | 0.400000 | 5 | 0 | 1 |
| 2023-02 | 12 | -8.483333 | 0.334641 | 0.285714 | 4 | 0 | 0 |
| 2023-03 | 16 | -17.750000 | 0.110276 | 0.139241 | 3 | 1 | 0 |
| 2023-04 | 12 | -12.166667 | 0.170455 | 0.181818 | 5 | 0 | 0 |
| 2023-05 | 10 | -0.933333 | 0.931034 | 1.145455 | 3 | 0 | 0 |
| 2023-06 | 3 | 11.833333 | 4.736842 | 4.090909 | 4 | 0 | 2 |
| 2023-07 | 7 | 3.266667 | 1.404959 | 1.259259 | 1 | 0 | 0 |
| 2023-08 | 11 | 6.800000 | 1.531250 | 1.387755 | 2 | 0 | 0 |
| 2023-09 | 15 | -12.066667 | 0.350090 | 0.337662 | 2 | 0 | 0 |
| 2023-10 | 6 | -6.883333 | 0.126850 | 0.129032 | 0 | 0 | 0 |
| 2023-11 | 13 | -17.150000 | 0.014368 | 0.015625 | 1 | 0 | 0 |
| 2023-12 | 9 | -9.300000 | 0.184211 | 0.243243 | 0 | 0 | 0 |

### B_OPT2023_N7_W3_T2_SB1_TP10

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 123, entry dates 86, entry months 12; SKIP 1, EXCLUDED 3, exclusion share 0.023810; conditional FLAT CLOSED 118.
Net -63.666667 R; PF R / price 0.578599 / 0.554007; expectancy -0.517615 R; win rate 0.138211; average winner / loser 5.142157 / -1.438889 R.
Conditional CLOSED-only DD 65.833333 R; largest winner share 0.190658; largest positive month share 0.525292. Positive / negative / zero months 4 / 8 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 9 | -5.566667 | 0.489297 | 0.400000 | 5 | 0 | 1 |
| 2023-02 | 12 | -8.483333 | 0.334641 | 0.285714 | 4 | 0 | 0 |
| 2023-03 | 16 | -17.750000 | 0.110276 | 0.139241 | 3 | 1 | 0 |
| 2023-04 | 12 | -12.166667 | 0.170455 | 0.181818 | 5 | 0 | 0 |
| 2023-05 | 10 | 0.466667 | 1.034483 | 1.272727 | 3 | 0 | 0 |
| 2023-06 | 3 | 13.500000 | 5.263158 | 4.545455 | 4 | 0 | 2 |
| 2023-07 | 7 | 3.266667 | 1.404959 | 1.259259 | 1 | 0 | 0 |
| 2023-08 | 11 | 8.466667 | 1.661458 | 1.489796 | 2 | 0 | 0 |
| 2023-09 | 15 | -12.066667 | 0.350090 | 0.337662 | 2 | 0 | 0 |
| 2023-10 | 6 | -6.883333 | 0.126850 | 0.129032 | 0 | 0 | 0 |
| 2023-11 | 13 | -17.150000 | 0.014368 | 0.015625 | 1 | 0 | 0 |
| 2023-12 | 9 | -9.300000 | 0.184211 | 0.243243 | 0 | 0 | 0 |

### B_OPT2023_N7_W3_T3_SB1_TP2

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 57, entry dates 46, entry months 12; SKIP 1, EXCLUDED 0, exclusion share 0.000000; conditional FLAT CLOSED 0.
Net -38.616667 R; PF R / price 0.411481 / 0.379167; expectancy -0.677485 R; win rate 0.175439; average winner / loser 2.700000 / -1.426449 R.
Conditional CLOSED-only DD 38.616667 R; largest winner share 0.123457; largest positive month share 0.506536. Positive / negative / zero months 5 / 7 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 9 | -12.300000 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-02 | 3 | 5.166667 | 4.444444 | 3.333333 | 4 | 0 | 0 |
| 2023-03 | 8 | -2.750000 | 0.571429 | 0.458333 | 3 | 1 | 0 |
| 2023-04 | 6 | -7.150000 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 5 | 1.433333 | 1.313869 | 1.333333 | 3 | 0 | 0 |
| 2023-06 | 1 | 3.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 4 | 0 | 0 |
| 2023-07 | 3 | 0.166667 | 1.052632 | 0.909091 | 1 | 0 | 0 |
| 2023-08 | 3 | 0.433333 | 1.149425 | 0.769231 | 2 | 0 | 0 |
| 2023-09 | 7 | -10.700000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 2 | -0.750000 | 0.571429 | 0.571429 | 0 | 0 | 0 |
| 2023-11 | 5 | -6.833333 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-12 | 5 | -8.333333 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N7_W3_T3_SB1_TP3

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors.
CLOSED 57, entry dates 46, entry months 12; SKIP 1, EXCLUDED 0, exclusion share 0.000000; conditional FLAT CLOSED 0.
Net -33.116667 R; PF R / price 0.506581 / 0.455285; expectancy -0.580994 R; win rate 0.157895; average winner / loser 3.777778 / -1.428014 R.
Conditional CLOSED-only DD 33.116667 R; largest winner share 0.147059; largest positive month share 0.459402. Positive / negative / zero months 4 / 8 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 9 | -12.300000 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-02 | 3 | 7.166667 | 5.777778 | 4.333333 | 4 | 0 | 0 |
| 2023-03 | 8 | -1.083333 | 0.831169 | 0.666667 | 3 | 1 | 0 |
| 2023-04 | 6 | -7.150000 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 5 | -1.566667 | 0.741758 | 0.750000 | 3 | 0 | 0 |
| 2023-06 | 1 | 4.500000 | NOT_AVAILABLE | NOT_AVAILABLE | 4 | 0 | 0 |
| 2023-07 | 3 | 1.833333 | 1.578947 | 1.363636 | 1 | 0 | 0 |
| 2023-08 | 3 | 2.100000 | 1.724138 | 1.153846 | 2 | 0 | 0 |
| 2023-09 | 7 | -10.700000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 2 | -0.750000 | 0.571429 | 0.571429 | 0 | 0 | 0 |
| 2023-11 | 5 | -6.833333 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-12 | 5 | -8.333333 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N7_W3_T3_SB1_TP4

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors.
CLOSED 56, entry dates 45, entry months 11; SKIP 1, EXCLUDED 1, exclusion share 0.017544; conditional FLAT CLOSED 25.
Net -39.783333 R; PF R / price 0.407251 / 0.341463; expectancy -0.710417 R; win rate 0.142857; average winner / loser 3.416667 / -1.428014 R.
Conditional CLOSED-only DD 39.783333 R; largest winner share 0.243902; largest positive month share 0.396476. Positive / negative / zero months 4 / 7 / 1; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 9 | -12.300000 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-02 | 3 | 4.500000 | 4.000000 | 3.000000 | 4 | 0 | 0 |
| 2023-03 | 8 | 0.583333 | 1.090909 | 0.875000 | 3 | 1 | 0 |
| 2023-04 | 6 | -7.150000 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 5 | -5.066667 | 0.164835 | 0.166667 | 3 | 0 | 0 |
| 2023-06 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 4 | 0 | 1 |
| 2023-07 | 3 | 2.500000 | 1.789474 | 1.545455 | 1 | 0 | 0 |
| 2023-08 | 3 | 3.766667 | 2.298851 | 1.538462 | 2 | 0 | 0 |
| 2023-09 | 7 | -10.700000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 2 | -0.750000 | 0.571429 | 0.571429 | 0 | 0 | 0 |
| 2023-11 | 5 | -6.833333 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-12 | 5 | -8.333333 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N7_W3_T3_SB1_TP5

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|neighbors.
CLOSED 56, entry dates 45, entry months 11; SKIP 1, EXCLUDED 1, exclusion share 0.017544; conditional FLAT CLOSED 25.
Net -46.450000 R; PF R / price 0.324691 / 0.274900; expectancy -0.829464 R; win rate 0.125000; average winner / loser 3.190476 / -1.432986 R.
Conditional CLOSED-only DD 46.450000 R; largest winner share 0.373134; largest positive month share 0.486486. Positive / negative / zero months 3 / 8 / 1; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 9 | -12.300000 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-02 | 3 | 4.500000 | 4.000000 | 3.000000 | 4 | 0 | 0 |
| 2023-03 | 8 | 2.250000 | 1.350649 | 1.083333 | 3 | 1 | 0 |
| 2023-04 | 6 | -7.150000 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 5 | -5.066667 | 0.164835 | 0.166667 | 3 | 0 | 0 |
| 2023-06 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 4 | 0 | 1 |
| 2023-07 | 3 | 2.500000 | 1.789474 | 1.545455 | 1 | 0 | 0 |
| 2023-08 | 3 | -4.566667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 7 | -10.700000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 2 | -0.750000 | 0.571429 | 0.571429 | 0 | 0 | 0 |
| 2023-11 | 5 | -6.833333 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-12 | 5 | -8.333333 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N7_W3_T3_SB1_TP6

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|neighbors.
CLOSED 56, entry dates 45, entry months 11; SKIP 1, EXCLUDED 1, exclusion share 0.017544; conditional FLAT CLOSED 25.
Net -45.783333 R; PF R / price 0.334383 / 0.282869; expectancy -0.817560 R; win rate 0.125000; average winner / loser 3.285714 / -1.432986 R.
Conditional CLOSED-only DD 45.783333 R; largest winner share 0.391304; largest positive month share 0.453782. Positive / negative / zero months 3 / 8 / 1; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 9 | -12.300000 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-02 | 3 | 4.500000 | 4.000000 | 3.000000 | 4 | 0 | 0 |
| 2023-03 | 8 | 2.916667 | 1.454545 | 1.166667 | 3 | 1 | 0 |
| 2023-04 | 6 | -7.150000 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 5 | -5.066667 | 0.164835 | 0.166667 | 3 | 0 | 0 |
| 2023-06 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 4 | 0 | 1 |
| 2023-07 | 3 | 2.500000 | 1.789474 | 1.545455 | 1 | 0 | 0 |
| 2023-08 | 3 | -4.566667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 7 | -10.700000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 2 | -0.750000 | 0.571429 | 0.571429 | 0 | 0 | 0 |
| 2023-11 | 5 | -6.833333 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-12 | 5 | -8.333333 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N7_W3_T3_SB1_TP7

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|neighbors.
CLOSED 56, entry dates 45, entry months 11; SKIP 1, EXCLUDED 1, exclusion share 0.017544; conditional FLAT CLOSED 25.
Net -45.783333 R; PF R / price 0.334383 / 0.282869; expectancy -0.817560 R; win rate 0.125000; average winner / loser 3.285714 / -1.432986 R.
Conditional CLOSED-only DD 45.783333 R; largest winner share 0.391304; largest positive month share 0.453782. Positive / negative / zero months 3 / 8 / 1; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 9 | -12.300000 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-02 | 3 | 4.500000 | 4.000000 | 3.000000 | 4 | 0 | 0 |
| 2023-03 | 8 | 2.916667 | 1.454545 | 1.166667 | 3 | 1 | 0 |
| 2023-04 | 6 | -7.150000 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 5 | -5.066667 | 0.164835 | 0.166667 | 3 | 0 | 0 |
| 2023-06 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 4 | 0 | 1 |
| 2023-07 | 3 | 2.500000 | 1.789474 | 1.545455 | 1 | 0 | 0 |
| 2023-08 | 3 | -4.566667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 7 | -10.700000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 2 | -0.750000 | 0.571429 | 0.571429 | 0 | 0 | 0 |
| 2023-11 | 5 | -6.833333 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-12 | 5 | -8.333333 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N7_W3_T3_SB1_TP8

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|neighbors.
CLOSED 56, entry dates 45, entry months 11; SKIP 1, EXCLUDED 1, exclusion share 0.017544; conditional FLAT CLOSED 25.
Net -45.783333 R; PF R / price 0.334383 / 0.282869; expectancy -0.817560 R; win rate 0.125000; average winner / loser 3.285714 / -1.432986 R.
Conditional CLOSED-only DD 45.783333 R; largest winner share 0.391304; largest positive month share 0.453782. Positive / negative / zero months 3 / 8 / 1; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 9 | -12.300000 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-02 | 3 | 4.500000 | 4.000000 | 3.000000 | 4 | 0 | 0 |
| 2023-03 | 8 | 2.916667 | 1.454545 | 1.166667 | 3 | 1 | 0 |
| 2023-04 | 6 | -7.150000 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 5 | -5.066667 | 0.164835 | 0.166667 | 3 | 0 | 0 |
| 2023-06 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 4 | 0 | 1 |
| 2023-07 | 3 | 2.500000 | 1.789474 | 1.545455 | 1 | 0 | 0 |
| 2023-08 | 3 | -4.566667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 7 | -10.700000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 2 | -0.750000 | 0.571429 | 0.571429 | 0 | 0 | 0 |
| 2023-11 | 5 | -6.833333 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-12 | 5 | -8.333333 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N7_W3_T3_SB1_TP9

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|neighbors.
CLOSED 56, entry dates 45, entry months 11; SKIP 1, EXCLUDED 1, exclusion share 0.017544; conditional FLAT CLOSED 25.
Net -45.783333 R; PF R / price 0.334383 / 0.282869; expectancy -0.817560 R; win rate 0.125000; average winner / loser 3.285714 / -1.432986 R.
Conditional CLOSED-only DD 45.783333 R; largest winner share 0.391304; largest positive month share 0.453782. Positive / negative / zero months 3 / 8 / 1; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 9 | -12.300000 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-02 | 3 | 4.500000 | 4.000000 | 3.000000 | 4 | 0 | 0 |
| 2023-03 | 8 | 2.916667 | 1.454545 | 1.166667 | 3 | 1 | 0 |
| 2023-04 | 6 | -7.150000 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 5 | -5.066667 | 0.164835 | 0.166667 | 3 | 0 | 0 |
| 2023-06 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 4 | 0 | 1 |
| 2023-07 | 3 | 2.500000 | 1.789474 | 1.545455 | 1 | 0 | 0 |
| 2023-08 | 3 | -4.566667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 7 | -10.700000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 2 | -0.750000 | 0.571429 | 0.571429 | 0 | 0 | 0 |
| 2023-11 | 5 | -6.833333 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-12 | 5 | -8.333333 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N7_W3_T3_SB1_TP10

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|neighbors.
CLOSED 56, entry dates 45, entry months 11; SKIP 1, EXCLUDED 1, exclusion share 0.017544; conditional FLAT CLOSED 25.
Net -45.783333 R; PF R / price 0.334383 / 0.282869; expectancy -0.817560 R; win rate 0.125000; average winner / loser 3.285714 / -1.432986 R.
Conditional CLOSED-only DD 45.783333 R; largest winner share 0.391304; largest positive month share 0.453782. Positive / negative / zero months 3 / 8 / 1; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 9 | -12.300000 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-02 | 3 | 4.500000 | 4.000000 | 3.000000 | 4 | 0 | 0 |
| 2023-03 | 8 | 2.916667 | 1.454545 | 1.166667 | 3 | 1 | 0 |
| 2023-04 | 6 | -7.150000 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 5 | -5.066667 | 0.164835 | 0.166667 | 3 | 0 | 0 |
| 2023-06 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 4 | 0 | 1 |
| 2023-07 | 3 | 2.500000 | 1.789474 | 1.545455 | 1 | 0 | 0 |
| 2023-08 | 3 | -4.566667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 7 | -10.700000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 2 | -0.750000 | 0.571429 | 0.571429 | 0 | 0 | 0 |
| 2023-11 | 5 | -6.833333 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-12 | 5 | -8.333333 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N8_W2_T2_SB1_TP2

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|month_concentration|neighbors.
CLOSED 38, entry dates 34, entry months 12; SKIP 0, EXCLUDED 0, exclusion share 0.000000; conditional FLAT CLOSED 0.
Net -16.166667 R; PF R / price 0.592779 / 0.620690; expectancy -0.425439 R; win rate 0.289474; average winner / loser 2.139394 / -1.470370 R.
Conditional CLOSED-only DD 16.333333 R; largest winner share 0.141643; largest positive month share 0.590690. Positive / negative / zero months 4 / 8 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 3 | -3.000000 | 0.100000 | 0.100000 | 5 | 0 | 0 |
| 2023-02 | 6 | 0.100000 | 1.016043 | 0.956522 | 4 | 0 | 0 |
| 2023-03 | 4 | -3.933333 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-04 | 4 | -6.233333 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 2 | 6.133333 | NOT_AVAILABLE | NOT_AVAILABLE | 3 | 0 | 0 |
| 2023-06 | 1 | -1.500000 | 0.000000 | 0.000000 | 4 | 0 | 0 |
| 2023-07 | 2 | 3.550000 | NOT_AVAILABLE | NOT_AVAILABLE | 1 | 0 | 0 |
| 2023-08 | 1 | -1.500000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 4 | -6.500000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 1 | 0.600000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |
| 2023-11 | 6 | -2.583333 | 0.581081 | 0.478261 | 1 | 0 | 0 |
| 2023-12 | 4 | -1.300000 | 0.697674 | 0.600000 | 0 | 0 | 0 |

### B_OPT2023_N8_W2_T2_SB1_TP3

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|neighbors.
CLOSED 38, entry dates 34, entry months 12; SKIP 0, EXCLUDED 0, exclusion share 0.000000; conditional FLAT CLOSED 0.
Net -13.300000 R; PF R / price 0.676399 / 0.671053; expectancy -0.350000 R; win rate 0.263158; average winner / loser 2.780000 / -1.467857 R.
Conditional CLOSED-only DD 14.500000 R; largest winner share 0.179856; largest positive month share 0.481361. Positive / negative / zero months 5 / 7 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 3 | -3.000000 | 0.100000 | 0.100000 | 5 | 0 | 0 |
| 2023-02 | 6 | 0.933333 | 1.149733 | 1.086957 | 4 | 0 | 0 |
| 2023-03 | 4 | -3.933333 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-04 | 4 | -6.233333 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 2 | 3.600000 | 3.571429 | 2.142857 | 3 | 0 | 0 |
| 2023-06 | 1 | -1.500000 | 0.000000 | 0.000000 | 4 | 0 | 0 |
| 2023-07 | 2 | 4.950000 | NOT_AVAILABLE | NOT_AVAILABLE | 1 | 0 | 0 |
| 2023-08 | 1 | -1.500000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 4 | -6.500000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 1 | 0.600000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |
| 2023-11 | 6 | -0.916667 | 0.851351 | 0.695652 | 1 | 0 | 0 |
| 2023-12 | 4 | 0.200000 | 1.046512 | 0.900000 | 0 | 0 | 0 |

### B_OPT2023_N8_W2_T2_SB1_TP4

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|month_concentration|neighbors.
CLOSED 38, entry dates 34, entry months 12; SKIP 0, EXCLUDED 0, exclusion share 0.000000; conditional FLAT CLOSED 0.
Net -15.400000 R; PF R / price 0.639906 / 0.668790; expectancy -0.405263 R; win rate 0.236842; average winner / loser 3.040741 / -1.474713 R.
Conditional CLOSED-only DD 19.450000 R; largest winner share 0.243605; largest positive month share 0.614516. Positive / negative / zero months 5 / 7 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 3 | -3.000000 | 0.100000 | 0.100000 | 5 | 0 | 0 |
| 2023-02 | 6 | 0.933333 | 1.149733 | 1.086957 | 4 | 0 | 0 |
| 2023-03 | 4 | -3.933333 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-04 | 4 | -6.233333 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 2 | -3.066667 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-06 | 1 | -1.500000 | 0.000000 | 0.000000 | 4 | 0 | 0 |
| 2023-07 | 2 | 6.350000 | NOT_AVAILABLE | NOT_AVAILABLE | 1 | 0 | 0 |
| 2023-08 | 1 | -1.500000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 4 | -6.500000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 1 | 0.600000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |
| 2023-11 | 6 | 0.750000 | 1.121622 | 0.913043 | 1 | 0 | 0 |
| 2023-12 | 4 | 1.700000 | 1.395349 | 1.200000 | 0 | 0 | 0 |

### B_OPT2023_N8_W2_T2_SB1_TP5

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|neighbors.
CLOSED 38, entry dates 34, entry months 12; SKIP 0, EXCLUDED 0, exclusion share 0.000000; conditional FLAT CLOSED 0.
Net -18.433333 R; PF R / price 0.568979 / 0.592357; expectancy -0.485088 R; win rate 0.236842; average winner / loser 2.703704 / -1.474713 R.
Conditional CLOSED-only DD 22.633333 R; largest winner share 0.308219; largest positive month share 0.467167. Positive / negative / zero months 4 / 8 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 3 | -3.000000 | 0.100000 | 0.100000 | 5 | 0 | 0 |
| 2023-02 | 6 | 0.933333 | 1.149733 | 1.086957 | 4 | 0 | 0 |
| 2023-03 | 4 | -3.933333 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-04 | 4 | -6.233333 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 2 | -3.066667 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-06 | 1 | -1.500000 | 0.000000 | 0.000000 | 4 | 0 | 0 |
| 2023-07 | 2 | 4.150000 | NOT_AVAILABLE | NOT_AVAILABLE | 1 | 0 | 0 |
| 2023-08 | 1 | -1.500000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 4 | -6.500000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 1 | 0.600000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |
| 2023-11 | 6 | -1.583333 | 0.743243 | 0.608696 | 1 | 0 | 0 |
| 2023-12 | 4 | 3.200000 | 1.744186 | 1.500000 | 0 | 0 | 0 |

### B_OPT2023_N8_W2_T2_SB1_TP6

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|neighbors.
CLOSED 38, entry dates 34, entry months 12; SKIP 0, EXCLUDED 0, exclusion share 0.000000; conditional FLAT CLOSED 0.
Net -16.933333 R; PF R / price 0.604053 / 0.630573; expectancy -0.445614 R; win rate 0.236842; average winner / loser 2.870370 / -1.474713 R.
Conditional CLOSED-only DD 22.633333 R; largest winner share 0.348387; largest positive month share 0.452648. Positive / negative / zero months 4 / 8 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 3 | -3.000000 | 0.100000 | 0.100000 | 5 | 0 | 0 |
| 2023-02 | 6 | 0.933333 | 1.149733 | 1.086957 | 4 | 0 | 0 |
| 2023-03 | 4 | -3.933333 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-04 | 4 | -6.233333 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 2 | -3.066667 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-06 | 1 | -1.500000 | 0.000000 | 0.000000 | 4 | 0 | 0 |
| 2023-07 | 2 | 4.150000 | NOT_AVAILABLE | NOT_AVAILABLE | 1 | 0 | 0 |
| 2023-08 | 1 | -1.500000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 4 | -6.500000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 1 | 0.600000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |
| 2023-11 | 6 | -1.583333 | 0.743243 | 0.608696 | 1 | 0 | 0 |
| 2023-12 | 4 | 4.700000 | 2.093023 | 1.800000 | 0 | 0 | 0 |

### B_OPT2023_N8_W2_T2_SB1_TP7

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors.
CLOSED 38, entry dates 34, entry months 12; SKIP 0, EXCLUDED 0, exclusion share 0.000000; conditional FLAT CLOSED 0.
Net -15.433333 R; PF R / price 0.639127 / 0.668790; expectancy -0.406140 R; win rate 0.236842; average winner / loser 3.037037 / -1.474713 R.
Conditional CLOSED-only DD 22.633333 R; largest winner share 0.384146; largest positive month share 0.521739. Positive / negative / zero months 4 / 8 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 3 | -3.000000 | 0.100000 | 0.100000 | 5 | 0 | 0 |
| 2023-02 | 6 | 0.933333 | 1.149733 | 1.086957 | 4 | 0 | 0 |
| 2023-03 | 4 | -3.933333 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-04 | 4 | -6.233333 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 2 | -3.066667 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-06 | 1 | -1.500000 | 0.000000 | 0.000000 | 4 | 0 | 0 |
| 2023-07 | 2 | 4.150000 | NOT_AVAILABLE | NOT_AVAILABLE | 1 | 0 | 0 |
| 2023-08 | 1 | -1.500000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 4 | -6.500000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 1 | 0.600000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |
| 2023-11 | 6 | -1.583333 | 0.743243 | 0.608696 | 1 | 0 | 0 |
| 2023-12 | 4 | 6.200000 | 2.441860 | 2.100000 | 0 | 0 | 0 |

### B_OPT2023_N8_W2_T2_SB1_TP8

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors.
CLOSED 38, entry dates 34, entry months 12; SKIP 0, EXCLUDED 0, exclusion share 0.000000; conditional FLAT CLOSED 0.
Net -13.933333 R; PF R / price 0.674201 / 0.707006; expectancy -0.366667 R; win rate 0.236842; average winner / loser 3.203704 / -1.474713 R.
Conditional CLOSED-only DD 22.633333 R; largest winner share 0.416185; largest positive month share 0.575342. Positive / negative / zero months 4 / 8 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 3 | -3.000000 | 0.100000 | 0.100000 | 5 | 0 | 0 |
| 2023-02 | 6 | 0.933333 | 1.149733 | 1.086957 | 4 | 0 | 0 |
| 2023-03 | 4 | -3.933333 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-04 | 4 | -6.233333 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 2 | -3.066667 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-06 | 1 | -1.500000 | 0.000000 | 0.000000 | 4 | 0 | 0 |
| 2023-07 | 2 | 4.150000 | NOT_AVAILABLE | NOT_AVAILABLE | 1 | 0 | 0 |
| 2023-08 | 1 | -1.500000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 4 | -6.500000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 1 | 0.600000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |
| 2023-11 | 6 | -1.583333 | 0.743243 | 0.608696 | 1 | 0 | 0 |
| 2023-12 | 4 | 7.700000 | 2.790698 | 2.400000 | 0 | 0 | 0 |

### B_OPT2023_N8_W2_T2_SB1_TP9

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors.
CLOSED 38, entry dates 34, entry months 12; SKIP 0, EXCLUDED 0, exclusion share 0.000000; conditional FLAT CLOSED 0.
Net -12.433333 R; PF R / price 0.709275 / 0.745223; expectancy -0.327193 R; win rate 0.236842; average winner / loser 3.370370 / -1.474713 R.
Conditional CLOSED-only DD 22.633333 R; largest winner share 0.445055; largest positive month share 0.618141. Positive / negative / zero months 4 / 8 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 3 | -3.000000 | 0.100000 | 0.100000 | 5 | 0 | 0 |
| 2023-02 | 6 | 0.933333 | 1.149733 | 1.086957 | 4 | 0 | 0 |
| 2023-03 | 4 | -3.933333 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-04 | 4 | -6.233333 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 2 | -3.066667 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-06 | 1 | -1.500000 | 0.000000 | 0.000000 | 4 | 0 | 0 |
| 2023-07 | 2 | 4.150000 | NOT_AVAILABLE | NOT_AVAILABLE | 1 | 0 | 0 |
| 2023-08 | 1 | -1.500000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 4 | -6.500000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 1 | 0.600000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |
| 2023-11 | 6 | -1.583333 | 0.743243 | 0.608696 | 1 | 0 | 0 |
| 2023-12 | 4 | 9.200000 | 3.139535 | 2.700000 | 0 | 0 | 0 |

### B_OPT2023_N8_W2_T2_SB1_TP10

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors.
CLOSED 38, entry dates 34, entry months 12; SKIP 0, EXCLUDED 0, exclusion share 0.000000; conditional FLAT CLOSED 0.
Net -10.933333 R; PF R / price 0.744349 / 0.783439; expectancy -0.287719 R; win rate 0.236842; average winner / loser 3.537037 / -1.474713 R.
Conditional CLOSED-only DD 22.633333 R; largest winner share 0.471204; largest positive month share 0.653103. Positive / negative / zero months 4 / 8 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 3 | -3.000000 | 0.100000 | 0.100000 | 5 | 0 | 0 |
| 2023-02 | 6 | 0.933333 | 1.149733 | 1.086957 | 4 | 0 | 0 |
| 2023-03 | 4 | -3.933333 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-04 | 4 | -6.233333 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 2 | -3.066667 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-06 | 1 | -1.500000 | 0.000000 | 0.000000 | 4 | 0 | 0 |
| 2023-07 | 2 | 4.150000 | NOT_AVAILABLE | NOT_AVAILABLE | 1 | 0 | 0 |
| 2023-08 | 1 | -1.500000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 4 | -6.500000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 1 | 0.600000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |
| 2023-11 | 6 | -1.583333 | 0.743243 | 0.608696 | 1 | 0 | 0 |
| 2023-12 | 4 | 10.700000 | 3.488372 | 3.000000 | 0 | 0 | 0 |

### B_OPT2023_N8_W2_T3_SB1_TP2

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|neighbors.
CLOSED 24, entry dates 24, entry months 12; SKIP 0, EXCLUDED 0, exclusion share 0.000000; conditional FLAT CLOSED 0.
Net -12.066667 R; PF R / price 0.532300 / 0.566667; expectancy -0.502778 R; win rate 0.291667; average winner / loser 1.961905 / -1.517647 R.
Conditional CLOSED-only DD 15.400000 R; largest winner share 0.242718; largest positive month share 0.285714. Positive / negative / zero months 5 / 7 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 3 | -3.000000 | 0.100000 | 0.100000 | 5 | 0 | 0 |
| 2023-02 | 2 | 1.933333 | 2.380952 | 1.428571 | 4 | 0 | 0 |
| 2023-03 | 3 | -1.566667 | 0.175439 | 0.125000 | 3 | 0 | 0 |
| 2023-04 | 3 | -4.833333 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 1 | 3.333333 | NOT_AVAILABLE | NOT_AVAILABLE | 3 | 0 | 0 |
| 2023-06 | 1 | -1.500000 | 0.000000 | 0.000000 | 4 | 0 | 0 |
| 2023-07 | 1 | 2.800000 | NOT_AVAILABLE | NOT_AVAILABLE | 1 | 0 | 0 |
| 2023-08 | 1 | -1.500000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 3 | -5.000000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 1 | 0.600000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |
| 2023-11 | 4 | -6.333333 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-12 | 1 | 3.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N8_W2_T3_SB1_TP3

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|trade_concentration|neighbors.
CLOSED 24, entry dates 24, entry months 12; SKIP 0, EXCLUDED 0, exclusion share 0.000000; conditional FLAT CLOSED 0.
Net -7.166667 R; PF R / price 0.722222 / 0.777778; expectancy -0.298611 R; win rate 0.291667; average winner / loser 2.661905 / -1.517647 R.
Conditional CLOSED-only DD 12.333333 R; largest winner share 0.268336; largest positive month share 0.301811. Positive / negative / zero months 5 / 7 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 3 | -3.000000 | 0.100000 | 0.100000 | 5 | 0 | 0 |
| 2023-02 | 2 | 2.266667 | 2.619048 | 1.571429 | 4 | 0 | 0 |
| 2023-03 | 3 | -1.566667 | 0.175439 | 0.125000 | 3 | 0 | 0 |
| 2023-04 | 3 | -4.833333 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 1 | 5.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 3 | 0 | 0 |
| 2023-06 | 1 | -1.500000 | 0.000000 | 0.000000 | 4 | 0 | 0 |
| 2023-07 | 1 | 4.200000 | NOT_AVAILABLE | NOT_AVAILABLE | 1 | 0 | 0 |
| 2023-08 | 1 | -1.500000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 3 | -5.000000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 1 | 0.600000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |
| 2023-11 | 4 | -6.333333 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-12 | 1 | 4.500000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N8_W2_T3_SB1_TP4

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|trade_concentration|neighbors.
CLOSED 24, entry dates 24, entry months 12; SKIP 0, EXCLUDED 0, exclusion share 0.000000; conditional FLAT CLOSED 0.
Net -10.933333 R; PF R / price 0.601942 / 0.715789; expectancy -0.455556 R; win rate 0.250000; average winner / loser 2.755556 / -1.525926 R.
Conditional CLOSED-only DD 17.600000 R; largest winner share 0.362903; largest positive month share 0.414747. Positive / negative / zero months 4 / 8 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 3 | -3.000000 | 0.100000 | 0.100000 | 5 | 0 | 0 |
| 2023-02 | 2 | 2.266667 | 2.619048 | 1.571429 | 4 | 0 | 0 |
| 2023-03 | 3 | -1.566667 | 0.175439 | 0.125000 | 3 | 0 | 0 |
| 2023-04 | 3 | -4.833333 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 1 | -1.666667 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-06 | 1 | -1.500000 | 0.000000 | 0.000000 | 4 | 0 | 0 |
| 2023-07 | 1 | 5.600000 | NOT_AVAILABLE | NOT_AVAILABLE | 1 | 0 | 0 |
| 2023-08 | 1 | -1.500000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 3 | -5.000000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 1 | 0.600000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |
| 2023-11 | 4 | -6.333333 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-12 | 1 | 6.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N8_W2_T3_SB1_TP5

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|trade_concentration|month_concentration|neighbors.
CLOSED 24, entry dates 24, entry months 12; SKIP 0, EXCLUDED 0, exclusion share 0.000000; conditional FLAT CLOSED 0.
Net -11.633333 R; PF R / price 0.576456 / 0.663158; expectancy -0.484722 R; win rate 0.250000; average winner / loser 2.638889 / -1.525926 R.
Conditional CLOSED-only DD 19.800000 R; largest winner share 0.473684; largest positive month share 0.544794. Positive / negative / zero months 4 / 8 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 3 | -3.000000 | 0.100000 | 0.100000 | 5 | 0 | 0 |
| 2023-02 | 2 | 2.266667 | 2.619048 | 1.571429 | 4 | 0 | 0 |
| 2023-03 | 3 | -1.566667 | 0.175439 | 0.125000 | 3 | 0 | 0 |
| 2023-04 | 3 | -4.833333 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 1 | -1.666667 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-06 | 1 | -1.500000 | 0.000000 | 0.000000 | 4 | 0 | 0 |
| 2023-07 | 1 | 3.400000 | NOT_AVAILABLE | NOT_AVAILABLE | 1 | 0 | 0 |
| 2023-08 | 1 | -1.500000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 3 | -5.000000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 1 | 0.600000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |
| 2023-11 | 4 | -6.333333 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-12 | 1 | 7.500000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N8_W2_T3_SB1_TP6

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|trade_concentration|month_concentration|neighbors.
CLOSED 24, entry dates 24, entry months 12; SKIP 0, EXCLUDED 0, exclusion share 0.000000; conditional FLAT CLOSED 0.
Net -10.133333 R; PF R / price 0.631068 / 0.726316; expectancy -0.422222 R; win rate 0.250000; average winner / loser 2.888889 / -1.525926 R.
Conditional CLOSED-only DD 19.800000 R; largest winner share 0.519231; largest positive month share 0.589520. Positive / negative / zero months 4 / 8 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 3 | -3.000000 | 0.100000 | 0.100000 | 5 | 0 | 0 |
| 2023-02 | 2 | 2.266667 | 2.619048 | 1.571429 | 4 | 0 | 0 |
| 2023-03 | 3 | -1.566667 | 0.175439 | 0.125000 | 3 | 0 | 0 |
| 2023-04 | 3 | -4.833333 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 1 | -1.666667 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-06 | 1 | -1.500000 | 0.000000 | 0.000000 | 4 | 0 | 0 |
| 2023-07 | 1 | 3.400000 | NOT_AVAILABLE | NOT_AVAILABLE | 1 | 0 | 0 |
| 2023-08 | 1 | -1.500000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 3 | -5.000000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 1 | 0.600000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |
| 2023-11 | 4 | -6.333333 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-12 | 1 | 9.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N8_W2_T3_SB1_TP7

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|trade_concentration|month_concentration|neighbors.
CLOSED 24, entry dates 24, entry months 12; SKIP 0, EXCLUDED 0, exclusion share 0.000000; conditional FLAT CLOSED 0.
Net -8.633333 R; PF R / price 0.685680 / 0.789474; expectancy -0.359722 R; win rate 0.250000; average winner / loser 3.138889 / -1.525926 R.
Conditional CLOSED-only DD 19.800000 R; largest winner share 0.557522; largest positive month share 0.626243. Positive / negative / zero months 4 / 8 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 3 | -3.000000 | 0.100000 | 0.100000 | 5 | 0 | 0 |
| 2023-02 | 2 | 2.266667 | 2.619048 | 1.571429 | 4 | 0 | 0 |
| 2023-03 | 3 | -1.566667 | 0.175439 | 0.125000 | 3 | 0 | 0 |
| 2023-04 | 3 | -4.833333 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 1 | -1.666667 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-06 | 1 | -1.500000 | 0.000000 | 0.000000 | 4 | 0 | 0 |
| 2023-07 | 1 | 3.400000 | NOT_AVAILABLE | NOT_AVAILABLE | 1 | 0 | 0 |
| 2023-08 | 1 | -1.500000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 3 | -5.000000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 1 | 0.600000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |
| 2023-11 | 4 | -6.333333 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-12 | 1 | 10.500000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N8_W2_T3_SB1_TP8

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|trade_concentration|month_concentration|neighbors.
CLOSED 24, entry dates 24, entry months 12; SKIP 0, EXCLUDED 0, exclusion share 0.000000; conditional FLAT CLOSED 0.
Net -7.133333 R; PF R / price 0.740291 / 0.852632; expectancy -0.297222 R; win rate 0.250000; average winner / loser 3.388889 / -1.525926 R.
Conditional CLOSED-only DD 19.800000 R; largest winner share 0.590164; largest positive month share 0.656934. Positive / negative / zero months 4 / 8 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 3 | -3.000000 | 0.100000 | 0.100000 | 5 | 0 | 0 |
| 2023-02 | 2 | 2.266667 | 2.619048 | 1.571429 | 4 | 0 | 0 |
| 2023-03 | 3 | -1.566667 | 0.175439 | 0.125000 | 3 | 0 | 0 |
| 2023-04 | 3 | -4.833333 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 1 | -1.666667 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-06 | 1 | -1.500000 | 0.000000 | 0.000000 | 4 | 0 | 0 |
| 2023-07 | 1 | 3.400000 | NOT_AVAILABLE | NOT_AVAILABLE | 1 | 0 | 0 |
| 2023-08 | 1 | -1.500000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 3 | -5.000000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 1 | 0.600000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |
| 2023-11 | 4 | -6.333333 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-12 | 1 | 12.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N8_W2_T3_SB1_TP9

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|trade_concentration|month_concentration|neighbors.
CLOSED 24, entry dates 24, entry months 12; SKIP 0, EXCLUDED 0, exclusion share 0.000000; conditional FLAT CLOSED 0.
Net -5.633333 R; PF R / price 0.794903 / 0.915789; expectancy -0.234722 R; win rate 0.250000; average winner / loser 3.638889 / -1.525926 R.
Conditional CLOSED-only DD 19.800000 R; largest winner share 0.618321; largest positive month share 0.682968. Positive / negative / zero months 4 / 8 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 3 | -3.000000 | 0.100000 | 0.100000 | 5 | 0 | 0 |
| 2023-02 | 2 | 2.266667 | 2.619048 | 1.571429 | 4 | 0 | 0 |
| 2023-03 | 3 | -1.566667 | 0.175439 | 0.125000 | 3 | 0 | 0 |
| 2023-04 | 3 | -4.833333 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 1 | -1.666667 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-06 | 1 | -1.500000 | 0.000000 | 0.000000 | 4 | 0 | 0 |
| 2023-07 | 1 | 3.400000 | NOT_AVAILABLE | NOT_AVAILABLE | 1 | 0 | 0 |
| 2023-08 | 1 | -1.500000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 3 | -5.000000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 1 | 0.600000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |
| 2023-11 | 4 | -6.333333 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-12 | 1 | 13.500000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N8_W2_T3_SB1_TP10

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|trade_concentration|month_concentration|neighbors.
CLOSED 24, entry dates 24, entry months 12; SKIP 0, EXCLUDED 0, exclusion share 0.000000; conditional FLAT CLOSED 0.
Net -4.133333 R; PF R / price 0.849515 / 0.978947; expectancy -0.172222 R; win rate 0.250000; average winner / loser 3.888889 / -1.525926 R.
Conditional CLOSED-only DD 19.800000 R; largest winner share 0.642857; largest positive month share 0.705329. Positive / negative / zero months 4 / 8 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 3 | -3.000000 | 0.100000 | 0.100000 | 5 | 0 | 0 |
| 2023-02 | 2 | 2.266667 | 2.619048 | 1.571429 | 4 | 0 | 0 |
| 2023-03 | 3 | -1.566667 | 0.175439 | 0.125000 | 3 | 0 | 0 |
| 2023-04 | 3 | -4.833333 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 1 | -1.666667 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-06 | 1 | -1.500000 | 0.000000 | 0.000000 | 4 | 0 | 0 |
| 2023-07 | 1 | 3.400000 | NOT_AVAILABLE | NOT_AVAILABLE | 1 | 0 | 0 |
| 2023-08 | 1 | -1.500000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 3 | -5.000000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 1 | 0.600000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |
| 2023-11 | 4 | -6.333333 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-12 | 1 | 15.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N8_W3_T2_SB1_TP2

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors.
CLOSED 82, entry dates 62, entry months 12; SKIP 0, EXCLUDED 3, exclusion share 0.035294; conditional FLAT CLOSED 77.
Net -34.933333 R; PF R / price 0.610336 / 0.621302; expectancy -0.426016 R; win rate 0.280488; average winner / loser 2.378986 / -1.519492 R.
Conditional CLOSED-only DD 38.616667 R; largest winner share 0.060920; largest positive month share 0.321596. Positive / negative / zero months 5 / 7 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 8 | -5.350000 | 0.369352 | 0.468750 | 5 | 0 | 1 |
| 2023-02 | 11 | -8.100000 | 0.430913 | 0.480000 | 4 | 0 | 1 |
| 2023-03 | 6 | 0.933333 | 1.184211 | 1.263158 | 3 | 0 | 0 |
| 2023-04 | 10 | -10.433333 | 0.242131 | 0.185185 | 5 | 0 | 0 |
| 2023-05 | 8 | 1.666667 | 1.223214 | 1.161290 | 3 | 0 | 0 |
| 2023-06 | 2 | -2.900000 | 0.000000 | 0.000000 | 4 | 0 | 1 |
| 2023-07 | 6 | 1.616667 | 1.341549 | 1.823529 | 1 | 0 | 0 |
| 2023-08 | 6 | 0.600000 | 1.098901 | 0.833333 | 2 | 0 | 0 |
| 2023-09 | 5 | -7.633333 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 2 | -1.400000 | 0.300000 | 0.500000 | 0 | 0 | 0 |
| 2023-11 | 12 | -6.216667 | 0.521795 | 0.571429 | 1 | 0 | 0 |
| 2023-12 | 6 | 2.283333 | 1.531008 | 1.150000 | 0 | 0 | 0 |

### B_OPT2023_N8_W3_T2_SB1_TP3

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors.
CLOSED 82, entry dates 62, entry months 12; SKIP 0, EXCLUDED 3, exclusion share 0.035294; conditional FLAT CLOSED 77.
Net -38.116667 R; PF R / price 0.596507 / 0.585434; expectancy -0.464837 R; win rate 0.231707; average winner / loser 2.965789 / -1.499471 R.
Conditional CLOSED-only DD 44.966667 R; largest winner share 0.088731; largest positive month share 0.377598. Positive / negative / zero months 4 / 8 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 8 | -5.350000 | 0.369352 | 0.468750 | 5 | 0 | 1 |
| 2023-02 | 11 | -9.966667 | 0.299766 | 0.280000 | 4 | 0 | 1 |
| 2023-03 | 6 | -0.816667 | 0.846395 | 0.900000 | 3 | 0 | 0 |
| 2023-04 | 10 | -8.766667 | 0.363196 | 0.277778 | 5 | 0 | 0 |
| 2023-05 | 8 | 0.633333 | 1.071429 | 0.868421 | 3 | 0 | 0 |
| 2023-06 | 2 | -2.900000 | 0.000000 | 0.000000 | 4 | 0 | 1 |
| 2023-07 | 6 | 4.416667 | 1.933099 | 2.647059 | 1 | 0 | 0 |
| 2023-08 | 6 | 3.933333 | 1.648352 | 1.250000 | 2 | 0 | 0 |
| 2023-09 | 5 | -7.633333 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 2 | -1.400000 | 0.300000 | 0.500000 | 0 | 0 | 0 |
| 2023-11 | 12 | -15.716667 | 0.027835 | 0.037736 | 1 | 0 | 0 |
| 2023-12 | 6 | 5.450000 | 2.267442 | 1.700000 | 0 | 0 | 0 |

### B_OPT2023_N8_W3_T2_SB1_TP4

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors.
CLOSED 82, entry dates 62, entry months 12; SKIP 0, EXCLUDED 3, exclusion share 0.035294; conditional FLAT CLOSED 77.
Net -38.416667 R; PF R / price 0.600381 / 0.588398; expectancy -0.468496 R; win rate 0.219512; average winner / loser 3.206481 / -1.502083 R.
Conditional CLOSED-only DD 48.433333 R; largest winner share 0.115507; largest positive month share 0.406766. Positive / negative / zero months 4 / 8 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 8 | -5.350000 | 0.369352 | 0.468750 | 5 | 0 | 1 |
| 2023-02 | 11 | -9.966667 | 0.299766 | 0.280000 | 4 | 0 | 1 |
| 2023-03 | 6 | 0.683333 | 1.128527 | 1.200000 | 3 | 0 | 0 |
| 2023-04 | 10 | -7.100000 | 0.484262 | 0.370370 | 5 | 0 | 0 |
| 2023-05 | 8 | -9.533333 | 0.094937 | 0.093023 | 3 | 0 | 0 |
| 2023-06 | 2 | -2.900000 | 0.000000 | 0.000000 | 4 | 0 | 1 |
| 2023-07 | 6 | 4.616667 | 1.975352 | 2.705882 | 1 | 0 | 0 |
| 2023-08 | 6 | 7.266667 | 2.197802 | 1.666667 | 2 | 0 | 0 |
| 2023-09 | 5 | -7.633333 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 2 | -1.400000 | 0.300000 | 0.500000 | 0 | 0 | 0 |
| 2023-11 | 12 | -15.716667 | 0.027835 | 0.037736 | 1 | 0 | 0 |
| 2023-12 | 6 | 8.616667 | 3.003876 | 2.250000 | 0 | 0 | 0 |

### B_OPT2023_N8_W3_T2_SB1_TP5

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 82, entry dates 62, entry months 12; SKIP 0, EXCLUDED 3, exclusion share 0.035294; conditional FLAT CLOSED 77.
Net -45.616667 R; PF R / price 0.533572 / 0.531335; expectancy -0.556301 R; win rate 0.207317; average winner / loser 3.069608 / -1.504615 R.
Conditional CLOSED-only DD 58.800000 R; largest winner share 0.159693; largest positive month share 0.693817. Positive / negative / zero months 4 / 8 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 8 | -5.350000 | 0.369352 | 0.468750 | 5 | 0 | 1 |
| 2023-02 | 11 | -9.966667 | 0.299766 | 0.280000 | 4 | 0 | 1 |
| 2023-03 | 6 | 2.183333 | 1.410658 | 1.500000 | 3 | 0 | 0 |
| 2023-04 | 10 | -10.100000 | 0.266344 | 0.203704 | 5 | 0 | 0 |
| 2023-05 | 8 | -9.533333 | 0.094937 | 0.093023 | 3 | 0 | 0 |
| 2023-06 | 2 | -2.900000 | 0.000000 | 0.000000 | 4 | 0 | 1 |
| 2023-07 | 6 | 2.416667 | 1.510563 | 2.058824 | 1 | 0 | 0 |
| 2023-08 | 6 | 0.600000 | 1.077586 | 0.862069 | 2 | 0 | 0 |
| 2023-09 | 5 | -7.633333 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 2 | -1.400000 | 0.300000 | 0.500000 | 0 | 0 | 0 |
| 2023-11 | 12 | -15.716667 | 0.027835 | 0.037736 | 1 | 0 | 0 |
| 2023-12 | 6 | 11.783333 | 3.740310 | 2.800000 | 0 | 0 | 0 |

### B_OPT2023_N8_W3_T2_SB1_TP6

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 82, entry dates 62, entry months 12; SKIP 0, EXCLUDED 3, exclusion share 0.035294; conditional FLAT CLOSED 77.
Net -39.283333 R; PF R / price 0.598330 / 0.591281; expectancy -0.479065 R; win rate 0.207317; average winner / loser 3.442157 / -1.504615 R.
Conditional CLOSED-only DD 55.633333 R; largest winner share 0.170891; largest positive month share 0.641172. Positive / negative / zero months 4 / 8 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 8 | -5.350000 | 0.369352 | 0.468750 | 5 | 0 | 1 |
| 2023-02 | 11 | -9.966667 | 0.299766 | 0.280000 | 4 | 0 | 1 |
| 2023-03 | 6 | 3.683333 | 1.692790 | 1.800000 | 3 | 0 | 0 |
| 2023-04 | 10 | -10.100000 | 0.266344 | 0.203704 | 5 | 0 | 0 |
| 2023-05 | 8 | -9.533333 | 0.094937 | 0.093023 | 3 | 0 | 0 |
| 2023-06 | 2 | -2.900000 | 0.000000 | 0.000000 | 4 | 0 | 1 |
| 2023-07 | 6 | 2.416667 | 1.510563 | 2.058824 | 1 | 0 | 0 |
| 2023-08 | 6 | 2.266667 | 1.293103 | 1.034483 | 2 | 0 | 0 |
| 2023-09 | 5 | -7.633333 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 2 | -1.400000 | 0.300000 | 0.500000 | 0 | 0 | 0 |
| 2023-11 | 12 | -15.716667 | 0.027835 | 0.037736 | 1 | 0 | 0 |
| 2023-12 | 6 | 14.950000 | 4.476744 | 3.350000 | 0 | 0 | 0 |

### B_OPT2023_N8_W3_T2_SB1_TP7

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 82, entry dates 62, entry months 12; SKIP 0, EXCLUDED 3, exclusion share 0.035294; conditional FLAT CLOSED 77.
Net -36.950000 R; PF R / price 0.622188 / 0.618529; expectancy -0.450610 R; win rate 0.207317; average winner / loser 3.579412 / -1.504615 R.
Conditional CLOSED-only DD 52.466667 R; largest winner share 0.191728; largest positive month share 0.550357. Positive / negative / zero months 4 / 8 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 8 | -5.350000 | 0.369352 | 0.468750 | 5 | 0 | 1 |
| 2023-02 | 11 | -9.966667 | 0.299766 | 0.280000 | 4 | 0 | 1 |
| 2023-03 | 6 | 5.183333 | 1.974922 | 2.100000 | 3 | 0 | 0 |
| 2023-04 | 10 | -10.100000 | 0.266344 | 0.203704 | 5 | 0 | 0 |
| 2023-05 | 8 | -9.533333 | 0.094937 | 0.093023 | 3 | 0 | 0 |
| 2023-06 | 2 | -2.900000 | 0.000000 | 0.000000 | 4 | 0 | 1 |
| 2023-07 | 6 | 2.416667 | 1.510563 | 2.058824 | 1 | 0 | 0 |
| 2023-08 | 6 | 3.933333 | 1.508621 | 1.206897 | 2 | 0 | 0 |
| 2023-09 | 5 | -7.633333 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 2 | -1.400000 | 0.300000 | 0.500000 | 0 | 0 | 0 |
| 2023-11 | 12 | -15.716667 | 0.027835 | 0.037736 | 1 | 0 | 0 |
| 2023-12 | 6 | 14.116667 | 4.282946 | 3.300000 | 0 | 0 | 0 |

### B_OPT2023_N8_W3_T2_SB1_TP8

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 82, entry dates 62, entry months 12; SKIP 0, EXCLUDED 3, exclusion share 0.035294; conditional FLAT CLOSED 77.
Net -32.283333 R; PF R / price 0.669905 / 0.664850; expectancy -0.393699 R; win rate 0.207317; average winner / loser 3.853922 / -1.504615 R.
Conditional CLOSED-only DD 49.300000 R; largest winner share 0.203511; largest positive month share 0.515118. Positive / negative / zero months 4 / 8 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 8 | -5.350000 | 0.369352 | 0.468750 | 5 | 0 | 1 |
| 2023-02 | 11 | -9.966667 | 0.299766 | 0.280000 | 4 | 0 | 1 |
| 2023-03 | 6 | 6.683333 | 2.257053 | 2.400000 | 3 | 0 | 0 |
| 2023-04 | 10 | -10.100000 | 0.266344 | 0.203704 | 5 | 0 | 0 |
| 2023-05 | 8 | -9.533333 | 0.094937 | 0.093023 | 3 | 0 | 0 |
| 2023-06 | 2 | -2.900000 | 0.000000 | 0.000000 | 4 | 0 | 1 |
| 2023-07 | 6 | 2.416667 | 1.510563 | 2.058824 | 1 | 0 | 0 |
| 2023-08 | 6 | 5.600000 | 1.724138 | 1.379310 | 2 | 0 | 0 |
| 2023-09 | 5 | -7.633333 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 2 | -1.400000 | 0.300000 | 0.500000 | 0 | 0 | 0 |
| 2023-11 | 12 | -15.716667 | 0.027835 | 0.037736 | 1 | 0 | 0 |
| 2023-12 | 6 | 15.616667 | 4.631783 | 3.600000 | 0 | 0 | 0 |

### B_OPT2023_N8_W3_T2_SB1_TP9

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 82, entry dates 62, entry months 12; SKIP 0, EXCLUDED 3, exclusion share 0.035294; conditional FLAT CLOSED 77.
Net -34.866667 R; PF R / price 0.643490 / 0.632153; expectancy -0.425203 R; win rate 0.207317; average winner / loser 3.701961 / -1.504615 R.
Conditional CLOSED-only DD 53.383333 R; largest winner share 0.238347; largest positive month share 0.617188. Positive / negative / zero months 4 / 8 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 8 | -5.350000 | 0.369352 | 0.468750 | 5 | 0 | 1 |
| 2023-02 | 11 | -9.966667 | 0.299766 | 0.280000 | 4 | 0 | 1 |
| 2023-03 | 6 | 0.933333 | 1.175549 | 1.250000 | 3 | 0 | 0 |
| 2023-04 | 10 | -10.100000 | 0.266344 | 0.203704 | 5 | 0 | 0 |
| 2023-05 | 8 | -9.533333 | 0.094937 | 0.093023 | 3 | 0 | 0 |
| 2023-06 | 2 | -2.900000 | 0.000000 | 0.000000 | 4 | 0 | 1 |
| 2023-07 | 6 | 2.416667 | 1.510563 | 2.058824 | 1 | 0 | 0 |
| 2023-08 | 6 | 7.266667 | 1.939655 | 1.551724 | 2 | 0 | 0 |
| 2023-09 | 5 | -7.633333 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 2 | -1.400000 | 0.300000 | 0.500000 | 0 | 0 | 0 |
| 2023-11 | 12 | -15.716667 | 0.027835 | 0.037736 | 1 | 0 | 0 |
| 2023-12 | 6 | 17.116667 | 4.980620 | 3.900000 | 0 | 0 | 0 |

### B_OPT2023_N8_W3_T2_SB1_TP10

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors.
CLOSED 82, entry dates 62, entry months 12; SKIP 0, EXCLUDED 3, exclusion share 0.035294; conditional FLAT CLOSED 77.
Net -31.700000 R; PF R / price 0.675869 / 0.662125; expectancy -0.386585 R; win rate 0.207317; average winner / loser 3.888235 / -1.504615 R.
Conditional CLOSED-only DD 51.716667 R; largest winner share 0.252143; largest positive month share 0.602481. Positive / negative / zero months 4 / 8 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 8 | -5.350000 | 0.369352 | 0.468750 | 5 | 0 | 1 |
| 2023-02 | 11 | -9.966667 | 0.299766 | 0.280000 | 4 | 0 | 1 |
| 2023-03 | 6 | 0.933333 | 1.175549 | 1.250000 | 3 | 0 | 0 |
| 2023-04 | 10 | -10.100000 | 0.266344 | 0.203704 | 5 | 0 | 0 |
| 2023-05 | 8 | -9.533333 | 0.094937 | 0.093023 | 3 | 0 | 0 |
| 2023-06 | 2 | -2.900000 | 0.000000 | 0.000000 | 4 | 0 | 1 |
| 2023-07 | 6 | 2.416667 | 1.510563 | 2.058824 | 1 | 0 | 0 |
| 2023-08 | 6 | 8.933333 | 2.155172 | 1.724138 | 2 | 0 | 0 |
| 2023-09 | 5 | -7.633333 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 2 | -1.400000 | 0.300000 | 0.500000 | 0 | 0 | 0 |
| 2023-11 | 12 | -15.716667 | 0.027835 | 0.037736 | 1 | 0 | 0 |
| 2023-12 | 6 | 18.616667 | 5.329457 | 4.200000 | 0 | 0 | 0 |

### B_OPT2023_N8_W3_T3_SB1_TP2

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors.
CLOSED 49, entry dates 45, entry months 12; SKIP 0, EXCLUDED 0, exclusion share 0.000000; conditional FLAT CLOSED 0.
Net -22.950000 R; PF R / price 0.566026 / 0.527363; expectancy -0.468367 R; win rate 0.265306; average winner / loser 2.302564 / -1.468981 R.
Conditional CLOSED-only DD 24.550000 R; largest winner share 0.111359; largest positive month share 0.297170. Positive / negative / zero months 6 / 6 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 6 | -6.650000 | 0.047733 | 0.038462 | 5 | 0 | 0 |
| 2023-02 | 5 | 2.100000 | 1.459854 | 1.111111 | 4 | 0 | 0 |
| 2023-03 | 4 | 1.433333 | 1.754386 | 1.625000 | 3 | 0 | 0 |
| 2023-04 | 6 | -8.300000 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 5 | 1.766667 | 1.386861 | 1.222222 | 3 | 0 | 0 |
| 2023-06 | 2 | -2.900000 | 0.000000 | 0.000000 | 4 | 0 | 0 |
| 2023-07 | 2 | 1.133333 | 1.680000 | 2.800000 | 1 | 0 | 0 |
| 2023-08 | 3 | 0.433333 | 1.149425 | 0.769231 | 2 | 0 | 0 |
| 2023-09 | 5 | -7.800000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 2 | -1.400000 | 0.300000 | 0.500000 | 0 | 0 | 0 |
| 2023-11 | 6 | -2.966667 | 0.543590 | 0.523810 | 1 | 0 | 0 |
| 2023-12 | 3 | 0.200000 | 1.071429 | 0.857143 | 0 | 0 | 0 |

### B_OPT2023_N8_W3_T3_SB1_TP3

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors.
CLOSED 49, entry dates 45, entry months 12; SKIP 0, EXCLUDED 0, exclusion share 0.000000; conditional FLAT CLOSED 0.
Net -21.466667 R; PF R / price 0.608273 / 0.574879; expectancy -0.438095 R; win rate 0.224490; average winner / loser 3.030303 / -1.442105 R.
Conditional CLOSED-only DD 24.566667 R; largest winner share 0.150000; largest positive month share 0.321041. Positive / negative / zero months 5 / 7 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 6 | -6.650000 | 0.047733 | 0.038462 | 5 | 0 | 0 |
| 2023-02 | 5 | 4.100000 | 1.897810 | 1.444444 | 4 | 0 | 0 |
| 2023-03 | 4 | -1.816667 | 0.155039 | 0.111111 | 3 | 0 | 0 |
| 2023-04 | 6 | -8.300000 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 5 | 4.933333 | 2.080292 | 1.833333 | 3 | 0 | 0 |
| 2023-06 | 2 | -2.900000 | 0.000000 | 0.000000 | 4 | 0 | 0 |
| 2023-07 | 2 | 2.533333 | 2.520000 | 4.200000 | 1 | 0 | 0 |
| 2023-08 | 3 | 2.100000 | 1.724138 | 1.153846 | 2 | 0 | 0 |
| 2023-09 | 5 | -7.800000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 2 | -1.400000 | 0.300000 | 0.500000 | 0 | 0 | 0 |
| 2023-11 | 6 | -7.966667 | 0.024490 | 0.038462 | 1 | 0 | 0 |
| 2023-12 | 3 | 1.700000 | 1.607143 | 1.285714 | 0 | 0 | 0 |

### B_OPT2023_N8_W3_T3_SB1_TP4

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors.
CLOSED 49, entry dates 45, entry months 12; SKIP 0, EXCLUDED 0, exclusion share 0.000000; conditional FLAT CLOSED 0.
Net -29.733333 R; PF R / price 0.473436 / 0.471698; expectancy -0.606803 R; win rate 0.204082; average winner / loser 2.673333 / -1.447863 R.
Conditional CLOSED-only DD 34.333333 R; largest winner share 0.249377; largest positive month share 0.318919. Positive / negative / zero months 4 / 8 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 6 | -6.650000 | 0.047733 | 0.038462 | 5 | 0 | 0 |
| 2023-02 | 5 | 1.433333 | 1.313869 | 1.000000 | 4 | 0 | 0 |
| 2023-03 | 4 | -1.816667 | 0.155039 | 0.111111 | 3 | 0 | 0 |
| 2023-04 | 6 | -8.300000 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 5 | -5.233333 | 0.160428 | 0.173913 | 3 | 0 | 0 |
| 2023-06 | 2 | -2.900000 | 0.000000 | 0.000000 | 4 | 0 | 0 |
| 2023-07 | 2 | 3.933333 | 3.360000 | 5.600000 | 1 | 0 | 0 |
| 2023-08 | 3 | 3.766667 | 2.298851 | 1.538462 | 2 | 0 | 0 |
| 2023-09 | 5 | -7.800000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 2 | -1.400000 | 0.300000 | 0.500000 | 0 | 0 | 0 |
| 2023-11 | 6 | -7.966667 | 0.024490 | 0.038462 | 1 | 0 | 0 |
| 2023-12 | 3 | 3.200000 | 2.142857 | 1.714286 | 0 | 0 | 0 |

### B_OPT2023_N8_W3_T3_SB1_TP5

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors.
CLOSED 49, entry dates 45, entry months 12; SKIP 0, EXCLUDED 0, exclusion share 0.000000; conditional FLAT CLOSED 0.
Net -38.766667 R; PF R / price 0.333142 / 0.345622; expectancy -0.791156 R; win rate 0.183673; average winner / loser 2.151852 / -1.453333 R.
Conditional CLOSED-only DD 44.866667 R; largest winner share 0.387263; largest positive month share 0.597458. Positive / negative / zero months 3 / 9 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 6 | -6.650000 | 0.047733 | 0.038462 | 5 | 0 | 0 |
| 2023-02 | 5 | 1.433333 | 1.313869 | 1.000000 | 4 | 0 | 0 |
| 2023-03 | 4 | -1.816667 | 0.155039 | 0.111111 | 3 | 0 | 0 |
| 2023-04 | 6 | -8.300000 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 5 | -5.233333 | 0.160428 | 0.173913 | 3 | 0 | 0 |
| 2023-06 | 2 | -2.900000 | 0.000000 | 0.000000 | 4 | 0 | 0 |
| 2023-07 | 2 | 1.733333 | 2.040000 | 3.400000 | 1 | 0 | 0 |
| 2023-08 | 3 | -4.566667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 5 | -7.800000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 2 | -1.400000 | 0.300000 | 0.500000 | 0 | 0 | 0 |
| 2023-11 | 6 | -7.966667 | 0.024490 | 0.038462 | 1 | 0 | 0 |
| 2023-12 | 3 | 4.700000 | 2.678571 | 2.142857 | 0 | 0 | 0 |

### B_OPT2023_N8_W3_T3_SB1_TP6

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors.
CLOSED 49, entry dates 45, entry months 12; SKIP 0, EXCLUDED 0, exclusion share 0.000000; conditional FLAT CLOSED 0.
Net -37.266667 R; PF R / price 0.358945 / 0.373272; expectancy -0.760544 R; win rate 0.183673; average winner / loser 2.318519 / -1.453333 R.
Conditional CLOSED-only DD 44.866667 R; largest winner share 0.431310; largest positive month share 0.661922. Positive / negative / zero months 3 / 9 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 6 | -6.650000 | 0.047733 | 0.038462 | 5 | 0 | 0 |
| 2023-02 | 5 | 1.433333 | 1.313869 | 1.000000 | 4 | 0 | 0 |
| 2023-03 | 4 | -1.816667 | 0.155039 | 0.111111 | 3 | 0 | 0 |
| 2023-04 | 6 | -8.300000 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 5 | -5.233333 | 0.160428 | 0.173913 | 3 | 0 | 0 |
| 2023-06 | 2 | -2.900000 | 0.000000 | 0.000000 | 4 | 0 | 0 |
| 2023-07 | 2 | 1.733333 | 2.040000 | 3.400000 | 1 | 0 | 0 |
| 2023-08 | 3 | -4.566667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 5 | -7.800000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 2 | -1.400000 | 0.300000 | 0.500000 | 0 | 0 | 0 |
| 2023-11 | 6 | -7.966667 | 0.024490 | 0.038462 | 1 | 0 | 0 |
| 2023-12 | 3 | 6.200000 | 3.214286 | 2.571429 | 0 | 0 | 0 |

### B_OPT2023_N8_W3_T3_SB1_TP7

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors.
CLOSED 49, entry dates 45, entry months 12; SKIP 0, EXCLUDED 0, exclusion share 0.000000; conditional FLAT CLOSED 0.
Net -35.766667 R; PF R / price 0.384748 / 0.400922; expectancy -0.729932 R; win rate 0.183673; average winner / loser 2.485185 / -1.453333 R.
Conditional CLOSED-only DD 44.866667 R; largest winner share 0.469449; largest positive month share 0.708589. Positive / negative / zero months 3 / 9 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 6 | -6.650000 | 0.047733 | 0.038462 | 5 | 0 | 0 |
| 2023-02 | 5 | 1.433333 | 1.313869 | 1.000000 | 4 | 0 | 0 |
| 2023-03 | 4 | -1.816667 | 0.155039 | 0.111111 | 3 | 0 | 0 |
| 2023-04 | 6 | -8.300000 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 5 | -5.233333 | 0.160428 | 0.173913 | 3 | 0 | 0 |
| 2023-06 | 2 | -2.900000 | 0.000000 | 0.000000 | 4 | 0 | 0 |
| 2023-07 | 2 | 1.733333 | 2.040000 | 3.400000 | 1 | 0 | 0 |
| 2023-08 | 3 | -4.566667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 5 | -7.800000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 2 | -1.400000 | 0.300000 | 0.500000 | 0 | 0 | 0 |
| 2023-11 | 6 | -7.966667 | 0.024490 | 0.038462 | 1 | 0 | 0 |
| 2023-12 | 3 | 7.700000 | 3.750000 | 3.000000 | 0 | 0 | 0 |

### B_OPT2023_N8_W3_T3_SB1_TP8

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors.
CLOSED 49, entry dates 45, entry months 12; SKIP 0, EXCLUDED 0, exclusion share 0.000000; conditional FLAT CLOSED 0.
Net -34.266667 R; PF R / price 0.410550 / 0.428571; expectancy -0.699320 R; win rate 0.183673; average winner / loser 2.651852 / -1.453333 R.
Conditional CLOSED-only DD 44.866667 R; largest winner share 0.502793; largest positive month share 0.743935. Positive / negative / zero months 3 / 9 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 6 | -6.650000 | 0.047733 | 0.038462 | 5 | 0 | 0 |
| 2023-02 | 5 | 1.433333 | 1.313869 | 1.000000 | 4 | 0 | 0 |
| 2023-03 | 4 | -1.816667 | 0.155039 | 0.111111 | 3 | 0 | 0 |
| 2023-04 | 6 | -8.300000 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 5 | -5.233333 | 0.160428 | 0.173913 | 3 | 0 | 0 |
| 2023-06 | 2 | -2.900000 | 0.000000 | 0.000000 | 4 | 0 | 0 |
| 2023-07 | 2 | 1.733333 | 2.040000 | 3.400000 | 1 | 0 | 0 |
| 2023-08 | 3 | -4.566667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 5 | -7.800000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 2 | -1.400000 | 0.300000 | 0.500000 | 0 | 0 | 0 |
| 2023-11 | 6 | -7.966667 | 0.024490 | 0.038462 | 1 | 0 | 0 |
| 2023-12 | 3 | 9.200000 | 4.285714 | 3.428571 | 0 | 0 | 0 |

### B_OPT2023_N8_W3_T3_SB1_TP9

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors.
CLOSED 49, entry dates 45, entry months 12; SKIP 0, EXCLUDED 0, exclusion share 0.000000; conditional FLAT CLOSED 0.
Net -32.766667 R; PF R / price 0.436353 / 0.456221; expectancy -0.668707 R; win rate 0.183673; average winner / loser 2.818519 / -1.453333 R.
Conditional CLOSED-only DD 44.866667 R; largest winner share 0.532194; largest positive month share 0.771635. Positive / negative / zero months 3 / 9 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 6 | -6.650000 | 0.047733 | 0.038462 | 5 | 0 | 0 |
| 2023-02 | 5 | 1.433333 | 1.313869 | 1.000000 | 4 | 0 | 0 |
| 2023-03 | 4 | -1.816667 | 0.155039 | 0.111111 | 3 | 0 | 0 |
| 2023-04 | 6 | -8.300000 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 5 | -5.233333 | 0.160428 | 0.173913 | 3 | 0 | 0 |
| 2023-06 | 2 | -2.900000 | 0.000000 | 0.000000 | 4 | 0 | 0 |
| 2023-07 | 2 | 1.733333 | 2.040000 | 3.400000 | 1 | 0 | 0 |
| 2023-08 | 3 | -4.566667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 5 | -7.800000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 2 | -1.400000 | 0.300000 | 0.500000 | 0 | 0 | 0 |
| 2023-11 | 6 | -7.966667 | 0.024490 | 0.038462 | 1 | 0 | 0 |
| 2023-12 | 3 | 10.700000 | 4.821429 | 3.857143 | 0 | 0 | 0 |

### B_OPT2023_N8_W3_T3_SB1_TP10

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors.
CLOSED 49, entry dates 45, entry months 12; SKIP 0, EXCLUDED 0, exclusion share 0.000000; conditional FLAT CLOSED 0.
Net -31.266667 R; PF R / price 0.462156 / 0.483871; expectancy -0.638095 R; win rate 0.183673; average winner / loser 2.985185 / -1.453333 R.
Conditional CLOSED-only DD 44.866667 R; largest winner share 0.558313; largest positive month share 0.793926. Positive / negative / zero months 3 / 9 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 6 | -6.650000 | 0.047733 | 0.038462 | 5 | 0 | 0 |
| 2023-02 | 5 | 1.433333 | 1.313869 | 1.000000 | 4 | 0 | 0 |
| 2023-03 | 4 | -1.816667 | 0.155039 | 0.111111 | 3 | 0 | 0 |
| 2023-04 | 6 | -8.300000 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 5 | -5.233333 | 0.160428 | 0.173913 | 3 | 0 | 0 |
| 2023-06 | 2 | -2.900000 | 0.000000 | 0.000000 | 4 | 0 | 0 |
| 2023-07 | 2 | 1.733333 | 2.040000 | 3.400000 | 1 | 0 | 0 |
| 2023-08 | 3 | -4.566667 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 5 | -7.800000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 2 | -1.400000 | 0.300000 | 0.500000 | 0 | 0 | 0 |
| 2023-11 | 6 | -7.966667 | 0.024490 | 0.038462 | 1 | 0 | 0 |
| 2023-12 | 3 | 12.200000 | 5.357143 | 4.285714 | 0 | 0 | 0 |

### B_OPT2023_N9_W2_T2_SB1_TP2

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|neighbors.
CLOSED 20, entry dates 19, entry months 10; SKIP 0, EXCLUDED 0, exclusion share 0.000000; conditional FLAT CLOSED 0.
Net -19.733333 R; PF R / price 0.252525 / 0.212766; expectancy -0.986667 R; win rate 0.100000; average winner / loser 3.333333 / -1.466667 R.
Conditional CLOSED-only DD 23.233333 R; largest winner share 0.500000; largest positive month share 0.500000. Positive / negative / zero months 2 / 8 / 2; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 1 | -1.666667 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-02 | 3 | 0.166667 | 1.052632 | 0.909091 | 4 | 0 | 0 |
| 2023-03 | 2 | -2.900000 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-04 | 1 | -1.500000 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 3 | 0 | 0 |
| 2023-06 | 2 | -2.900000 | 0.000000 | 0.000000 | 4 | 0 | 0 |
| 2023-07 | 1 | -0.600000 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-08 | 2 | -3.333333 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 2 | -3.333333 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |
| 2023-11 | 3 | -3.833333 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-12 | 3 | 0.166667 | 1.052632 | 0.909091 | 0 | 0 | 0 |

### B_OPT2023_N9_W2_T2_SB1_TP3

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors.
CLOSED 20, entry dates 19, entry months 10; SKIP 0, EXCLUDED 0, exclusion share 0.000000; conditional FLAT CLOSED 0.
Net -17.733333 R; PF R / price 0.328283 / 0.276596; expectancy -0.886667 R; win rate 0.100000; average winner / loser 4.333333 / -1.466667 R.
Conditional CLOSED-only DD 23.233333 R; largest winner share 0.576923; largest positive month share 0.785714. Positive / negative / zero months 2 / 8 / 2; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 1 | -1.666667 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-02 | 3 | 0.500000 | 1.157895 | 1.000000 | 4 | 0 | 0 |
| 2023-03 | 2 | -2.900000 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-04 | 1 | -1.500000 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 3 | 0 | 0 |
| 2023-06 | 2 | -2.900000 | 0.000000 | 0.000000 | 4 | 0 | 0 |
| 2023-07 | 1 | -0.600000 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-08 | 2 | -3.333333 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 2 | -3.333333 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |
| 2023-11 | 3 | -3.833333 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-12 | 3 | 1.833333 | 1.578947 | 1.363636 | 0 | 0 | 0 |

### B_OPT2023_N9_W2_T2_SB1_TP4

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors.
CLOSED 20, entry dates 19, entry months 10; SKIP 0, EXCLUDED 0, exclusion share 0.000000; conditional FLAT CLOSED 0.
Net -16.066667 R; PF R / price 0.391414 / 0.329787; expectancy -0.803333 R; win rate 0.100000; average winner / loser 5.166667 / -1.466667 R.
Conditional CLOSED-only DD 23.233333 R; largest winner share 0.645161; largest positive month share 0.875000. Positive / negative / zero months 2 / 8 / 2; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 1 | -1.666667 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-02 | 3 | 0.500000 | 1.157895 | 1.000000 | 4 | 0 | 0 |
| 2023-03 | 2 | -2.900000 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-04 | 1 | -1.500000 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 3 | 0 | 0 |
| 2023-06 | 2 | -2.900000 | 0.000000 | 0.000000 | 4 | 0 | 0 |
| 2023-07 | 1 | -0.600000 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-08 | 2 | -3.333333 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 2 | -3.333333 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |
| 2023-11 | 3 | -3.833333 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-12 | 3 | 3.500000 | 2.105263 | 1.818182 | 0 | 0 | 0 |

### B_OPT2023_N9_W2_T2_SB1_TP5

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors.
CLOSED 20, entry dates 19, entry months 10; SKIP 0, EXCLUDED 0, exclusion share 0.000000; conditional FLAT CLOSED 0.
Net -14.400000 R; PF R / price 0.454545 / 0.382979; expectancy -0.720000 R; win rate 0.100000; average winner / loser 6.000000 / -1.466667 R.
Conditional CLOSED-only DD 23.233333 R; largest winner share 0.694444; largest positive month share 0.911765. Positive / negative / zero months 2 / 8 / 2; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 1 | -1.666667 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-02 | 3 | 0.500000 | 1.157895 | 1.000000 | 4 | 0 | 0 |
| 2023-03 | 2 | -2.900000 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-04 | 1 | -1.500000 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 3 | 0 | 0 |
| 2023-06 | 2 | -2.900000 | 0.000000 | 0.000000 | 4 | 0 | 0 |
| 2023-07 | 1 | -0.600000 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-08 | 2 | -3.333333 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 2 | -3.333333 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |
| 2023-11 | 3 | -3.833333 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-12 | 3 | 5.166667 | 2.631579 | 2.272727 | 0 | 0 | 0 |

### B_OPT2023_N9_W2_T2_SB1_TP6

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors.
CLOSED 20, entry dates 19, entry months 10; SKIP 0, EXCLUDED 0, exclusion share 0.000000; conditional FLAT CLOSED 0.
Net -12.733333 R; PF R / price 0.517677 / 0.436170; expectancy -0.636667 R; win rate 0.100000; average winner / loser 6.833333 / -1.466667 R.
Conditional CLOSED-only DD 23.233333 R; largest winner share 0.731707; largest positive month share 0.931818. Positive / negative / zero months 2 / 8 / 2; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 1 | -1.666667 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-02 | 3 | 0.500000 | 1.157895 | 1.000000 | 4 | 0 | 0 |
| 2023-03 | 2 | -2.900000 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-04 | 1 | -1.500000 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 3 | 0 | 0 |
| 2023-06 | 2 | -2.900000 | 0.000000 | 0.000000 | 4 | 0 | 0 |
| 2023-07 | 1 | -0.600000 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-08 | 2 | -3.333333 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 2 | -3.333333 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |
| 2023-11 | 3 | -3.833333 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-12 | 3 | 6.833333 | 3.157895 | 2.727273 | 0 | 0 | 0 |

### B_OPT2023_N9_W2_T2_SB1_TP7

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors.
CLOSED 20, entry dates 19, entry months 10; SKIP 0, EXCLUDED 0, exclusion share 0.000000; conditional FLAT CLOSED 0.
Net -15.066667 R; PF R / price 0.429293 / 0.361702; expectancy -0.753333 R; win rate 0.100000; average winner / loser 5.666667 / -1.466667 R.
Conditional CLOSED-only DD 23.233333 R; largest winner share 0.676471; largest positive month share 0.900000. Positive / negative / zero months 2 / 8 / 2; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 1 | -1.666667 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-02 | 3 | 0.500000 | 1.157895 | 1.000000 | 4 | 0 | 0 |
| 2023-03 | 2 | -2.900000 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-04 | 1 | -1.500000 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 3 | 0 | 0 |
| 2023-06 | 2 | -2.900000 | 0.000000 | 0.000000 | 4 | 0 | 0 |
| 2023-07 | 1 | -0.600000 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-08 | 2 | -3.333333 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 2 | -3.333333 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |
| 2023-11 | 3 | -3.833333 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-12 | 3 | 4.500000 | 2.421053 | 2.090909 | 0 | 0 | 0 |

### B_OPT2023_N9_W2_T2_SB1_TP8

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors.
CLOSED 20, entry dates 19, entry months 10; SKIP 0, EXCLUDED 0, exclusion share 0.000000; conditional FLAT CLOSED 0.
Net -15.066667 R; PF R / price 0.429293 / 0.361702; expectancy -0.753333 R; win rate 0.100000; average winner / loser 5.666667 / -1.466667 R.
Conditional CLOSED-only DD 23.233333 R; largest winner share 0.676471; largest positive month share 0.900000. Positive / negative / zero months 2 / 8 / 2; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 1 | -1.666667 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-02 | 3 | 0.500000 | 1.157895 | 1.000000 | 4 | 0 | 0 |
| 2023-03 | 2 | -2.900000 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-04 | 1 | -1.500000 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 3 | 0 | 0 |
| 2023-06 | 2 | -2.900000 | 0.000000 | 0.000000 | 4 | 0 | 0 |
| 2023-07 | 1 | -0.600000 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-08 | 2 | -3.333333 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 2 | -3.333333 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |
| 2023-11 | 3 | -3.833333 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-12 | 3 | 4.500000 | 2.421053 | 2.090909 | 0 | 0 | 0 |

### B_OPT2023_N9_W2_T2_SB1_TP9

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors.
CLOSED 20, entry dates 19, entry months 10; SKIP 0, EXCLUDED 0, exclusion share 0.000000; conditional FLAT CLOSED 0.
Net -15.066667 R; PF R / price 0.429293 / 0.361702; expectancy -0.753333 R; win rate 0.100000; average winner / loser 5.666667 / -1.466667 R.
Conditional CLOSED-only DD 23.233333 R; largest winner share 0.676471; largest positive month share 0.900000. Positive / negative / zero months 2 / 8 / 2; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 1 | -1.666667 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-02 | 3 | 0.500000 | 1.157895 | 1.000000 | 4 | 0 | 0 |
| 2023-03 | 2 | -2.900000 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-04 | 1 | -1.500000 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 3 | 0 | 0 |
| 2023-06 | 2 | -2.900000 | 0.000000 | 0.000000 | 4 | 0 | 0 |
| 2023-07 | 1 | -0.600000 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-08 | 2 | -3.333333 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 2 | -3.333333 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |
| 2023-11 | 3 | -3.833333 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-12 | 3 | 4.500000 | 2.421053 | 2.090909 | 0 | 0 | 0 |

### B_OPT2023_N9_W2_T2_SB1_TP10

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors.
CLOSED 20, entry dates 19, entry months 10; SKIP 0, EXCLUDED 0, exclusion share 0.000000; conditional FLAT CLOSED 0.
Net -15.066667 R; PF R / price 0.429293 / 0.361702; expectancy -0.753333 R; win rate 0.100000; average winner / loser 5.666667 / -1.466667 R.
Conditional CLOSED-only DD 23.233333 R; largest winner share 0.676471; largest positive month share 0.900000. Positive / negative / zero months 2 / 8 / 2; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 1 | -1.666667 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-02 | 3 | 0.500000 | 1.157895 | 1.000000 | 4 | 0 | 0 |
| 2023-03 | 2 | -2.900000 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-04 | 1 | -1.500000 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 3 | 0 | 0 |
| 2023-06 | 2 | -2.900000 | 0.000000 | 0.000000 | 4 | 0 | 0 |
| 2023-07 | 1 | -0.600000 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-08 | 2 | -3.333333 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 2 | -3.333333 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |
| 2023-11 | 3 | -3.833333 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-12 | 3 | 4.500000 | 2.421053 | 2.090909 | 0 | 0 | 0 |

### B_OPT2023_N9_W2_T3_SB1_TP2

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|trade_concentration|month_concentration|neighbors.
CLOSED 15, entry dates 14, entry months 8; SKIP 0, EXCLUDED 0, exclusion share 0.000000; conditional FLAT CLOSED 0.
Net -15.800000 R; PF R / price 0.188356 / 0.159420; expectancy -1.053333 R; win rate 0.133333; average winner / loser 1.833333 / -1.497436 R.
Conditional CLOSED-only DD 17.466667 R; largest winner share 0.909091; largest positive month share 1.000000. Positive / negative / zero months 1 / 7 / 4; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 1 | -1.666667 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-02 | 1 | 3.333333 | NOT_AVAILABLE | NOT_AVAILABLE | 4 | 0 | 0 |
| 2023-03 | 3 | -2.566667 | 0.114943 | 0.076923 | 3 | 0 | 0 |
| 2023-04 | 1 | -1.500000 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 3 | 0 | 0 |
| 2023-06 | 2 | -2.900000 | 0.000000 | 0.000000 | 4 | 0 | 0 |
| 2023-07 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 1 | 0 | 0 |
| 2023-08 | 2 | -3.333333 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 2 | -3.333333 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |
| 2023-11 | 3 | -3.833333 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-12 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N9_W2_T3_SB1_TP3

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|trade_concentration|month_concentration|neighbors.
CLOSED 15, entry dates 14, entry months 8; SKIP 0, EXCLUDED 0, exclusion share 0.000000; conditional FLAT CLOSED 0.
Net -15.466667 R; PF R / price 0.205479 / 0.173913; expectancy -1.031111 R; win rate 0.133333; average winner / loser 2.000000 / -1.497436 R.
Conditional CLOSED-only DD 17.466667 R; largest winner share 0.916667; largest positive month share 1.000000. Positive / negative / zero months 1 / 7 / 4; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 1 | -1.666667 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-02 | 1 | 3.666667 | NOT_AVAILABLE | NOT_AVAILABLE | 4 | 0 | 0 |
| 2023-03 | 3 | -2.566667 | 0.114943 | 0.076923 | 3 | 0 | 0 |
| 2023-04 | 1 | -1.500000 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 3 | 0 | 0 |
| 2023-06 | 2 | -2.900000 | 0.000000 | 0.000000 | 4 | 0 | 0 |
| 2023-07 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 1 | 0 | 0 |
| 2023-08 | 2 | -3.333333 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 2 | -3.333333 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |
| 2023-11 | 3 | -3.833333 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-12 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N9_W2_T3_SB1_TP4

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|trade_concentration|month_concentration|neighbors.
CLOSED 15, entry dates 14, entry months 8; SKIP 0, EXCLUDED 0, exclusion share 0.000000; conditional FLAT CLOSED 0.
Net -15.466667 R; PF R / price 0.205479 / 0.173913; expectancy -1.031111 R; win rate 0.133333; average winner / loser 2.000000 / -1.497436 R.
Conditional CLOSED-only DD 17.466667 R; largest winner share 0.916667; largest positive month share 1.000000. Positive / negative / zero months 1 / 7 / 4; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 1 | -1.666667 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-02 | 1 | 3.666667 | NOT_AVAILABLE | NOT_AVAILABLE | 4 | 0 | 0 |
| 2023-03 | 3 | -2.566667 | 0.114943 | 0.076923 | 3 | 0 | 0 |
| 2023-04 | 1 | -1.500000 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 3 | 0 | 0 |
| 2023-06 | 2 | -2.900000 | 0.000000 | 0.000000 | 4 | 0 | 0 |
| 2023-07 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 1 | 0 | 0 |
| 2023-08 | 2 | -3.333333 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 2 | -3.333333 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |
| 2023-11 | 3 | -3.833333 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-12 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N9_W2_T3_SB1_TP5

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|trade_concentration|month_concentration|neighbors.
CLOSED 15, entry dates 14, entry months 8; SKIP 0, EXCLUDED 0, exclusion share 0.000000; conditional FLAT CLOSED 0.
Net -15.466667 R; PF R / price 0.205479 / 0.173913; expectancy -1.031111 R; win rate 0.133333; average winner / loser 2.000000 / -1.497436 R.
Conditional CLOSED-only DD 17.466667 R; largest winner share 0.916667; largest positive month share 1.000000. Positive / negative / zero months 1 / 7 / 4; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 1 | -1.666667 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-02 | 1 | 3.666667 | NOT_AVAILABLE | NOT_AVAILABLE | 4 | 0 | 0 |
| 2023-03 | 3 | -2.566667 | 0.114943 | 0.076923 | 3 | 0 | 0 |
| 2023-04 | 1 | -1.500000 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 3 | 0 | 0 |
| 2023-06 | 2 | -2.900000 | 0.000000 | 0.000000 | 4 | 0 | 0 |
| 2023-07 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 1 | 0 | 0 |
| 2023-08 | 2 | -3.333333 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 2 | -3.333333 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |
| 2023-11 | 3 | -3.833333 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-12 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N9_W2_T3_SB1_TP6

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|trade_concentration|month_concentration|neighbors.
CLOSED 15, entry dates 14, entry months 8; SKIP 0, EXCLUDED 0, exclusion share 0.000000; conditional FLAT CLOSED 0.
Net -15.466667 R; PF R / price 0.205479 / 0.173913; expectancy -1.031111 R; win rate 0.133333; average winner / loser 2.000000 / -1.497436 R.
Conditional CLOSED-only DD 17.466667 R; largest winner share 0.916667; largest positive month share 1.000000. Positive / negative / zero months 1 / 7 / 4; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 1 | -1.666667 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-02 | 1 | 3.666667 | NOT_AVAILABLE | NOT_AVAILABLE | 4 | 0 | 0 |
| 2023-03 | 3 | -2.566667 | 0.114943 | 0.076923 | 3 | 0 | 0 |
| 2023-04 | 1 | -1.500000 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 3 | 0 | 0 |
| 2023-06 | 2 | -2.900000 | 0.000000 | 0.000000 | 4 | 0 | 0 |
| 2023-07 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 1 | 0 | 0 |
| 2023-08 | 2 | -3.333333 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 2 | -3.333333 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |
| 2023-11 | 3 | -3.833333 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-12 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N9_W2_T3_SB1_TP7

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|trade_concentration|month_concentration|neighbors.
CLOSED 15, entry dates 14, entry months 8; SKIP 0, EXCLUDED 0, exclusion share 0.000000; conditional FLAT CLOSED 0.
Net -15.466667 R; PF R / price 0.205479 / 0.173913; expectancy -1.031111 R; win rate 0.133333; average winner / loser 2.000000 / -1.497436 R.
Conditional CLOSED-only DD 17.466667 R; largest winner share 0.916667; largest positive month share 1.000000. Positive / negative / zero months 1 / 7 / 4; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 1 | -1.666667 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-02 | 1 | 3.666667 | NOT_AVAILABLE | NOT_AVAILABLE | 4 | 0 | 0 |
| 2023-03 | 3 | -2.566667 | 0.114943 | 0.076923 | 3 | 0 | 0 |
| 2023-04 | 1 | -1.500000 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 3 | 0 | 0 |
| 2023-06 | 2 | -2.900000 | 0.000000 | 0.000000 | 4 | 0 | 0 |
| 2023-07 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 1 | 0 | 0 |
| 2023-08 | 2 | -3.333333 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 2 | -3.333333 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |
| 2023-11 | 3 | -3.833333 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-12 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N9_W2_T3_SB1_TP8

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|trade_concentration|month_concentration|neighbors.
CLOSED 15, entry dates 14, entry months 8; SKIP 0, EXCLUDED 0, exclusion share 0.000000; conditional FLAT CLOSED 0.
Net -15.466667 R; PF R / price 0.205479 / 0.173913; expectancy -1.031111 R; win rate 0.133333; average winner / loser 2.000000 / -1.497436 R.
Conditional CLOSED-only DD 17.466667 R; largest winner share 0.916667; largest positive month share 1.000000. Positive / negative / zero months 1 / 7 / 4; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 1 | -1.666667 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-02 | 1 | 3.666667 | NOT_AVAILABLE | NOT_AVAILABLE | 4 | 0 | 0 |
| 2023-03 | 3 | -2.566667 | 0.114943 | 0.076923 | 3 | 0 | 0 |
| 2023-04 | 1 | -1.500000 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 3 | 0 | 0 |
| 2023-06 | 2 | -2.900000 | 0.000000 | 0.000000 | 4 | 0 | 0 |
| 2023-07 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 1 | 0 | 0 |
| 2023-08 | 2 | -3.333333 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 2 | -3.333333 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |
| 2023-11 | 3 | -3.833333 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-12 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N9_W2_T3_SB1_TP9

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|trade_concentration|month_concentration|neighbors.
CLOSED 15, entry dates 14, entry months 8; SKIP 0, EXCLUDED 0, exclusion share 0.000000; conditional FLAT CLOSED 0.
Net -15.466667 R; PF R / price 0.205479 / 0.173913; expectancy -1.031111 R; win rate 0.133333; average winner / loser 2.000000 / -1.497436 R.
Conditional CLOSED-only DD 17.466667 R; largest winner share 0.916667; largest positive month share 1.000000. Positive / negative / zero months 1 / 7 / 4; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 1 | -1.666667 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-02 | 1 | 3.666667 | NOT_AVAILABLE | NOT_AVAILABLE | 4 | 0 | 0 |
| 2023-03 | 3 | -2.566667 | 0.114943 | 0.076923 | 3 | 0 | 0 |
| 2023-04 | 1 | -1.500000 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 3 | 0 | 0 |
| 2023-06 | 2 | -2.900000 | 0.000000 | 0.000000 | 4 | 0 | 0 |
| 2023-07 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 1 | 0 | 0 |
| 2023-08 | 2 | -3.333333 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 2 | -3.333333 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |
| 2023-11 | 3 | -3.833333 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-12 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N9_W2_T3_SB1_TP10

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|trade_concentration|month_concentration|neighbors.
CLOSED 15, entry dates 14, entry months 8; SKIP 0, EXCLUDED 0, exclusion share 0.000000; conditional FLAT CLOSED 0.
Net -15.466667 R; PF R / price 0.205479 / 0.173913; expectancy -1.031111 R; win rate 0.133333; average winner / loser 2.000000 / -1.497436 R.
Conditional CLOSED-only DD 17.466667 R; largest winner share 0.916667; largest positive month share 1.000000. Positive / negative / zero months 1 / 7 / 4; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 1 | -1.666667 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-02 | 1 | 3.666667 | NOT_AVAILABLE | NOT_AVAILABLE | 4 | 0 | 0 |
| 2023-03 | 3 | -2.566667 | 0.114943 | 0.076923 | 3 | 0 | 0 |
| 2023-04 | 1 | -1.500000 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 3 | 0 | 0 |
| 2023-06 | 2 | -2.900000 | 0.000000 | 0.000000 | 4 | 0 | 0 |
| 2023-07 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 1 | 0 | 0 |
| 2023-08 | 2 | -3.333333 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 2 | -3.333333 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |
| 2023-11 | 3 | -3.833333 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-12 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N9_W3_T2_SB1_TP2

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 52, entry dates 41, entry months 11; SKIP 1, EXCLUDED 1, exclusion share 0.018868; conditional FLAT CLOSED 35.
Net -40.550000 R; PF R / price 0.388386 / 0.358333; expectancy -0.779808 R; win rate 0.173077; average winner / loser 2.861111 / -1.541860 R.
Conditional CLOSED-only DD 42.383333 R; largest winner share 0.129450; largest positive month share 1.000000. Positive / negative / zero months 1 / 10 / 1; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 4 | -6.500000 | 0.000000 | 0.000000 | 5 | 1 | 0 |
| 2023-02 | 8 | -2.733333 | 0.709220 | 0.588235 | 4 | 0 | 0 |
| 2023-03 | 5 | 2.000000 | 1.428571 | 1.176471 | 3 | 0 | 1 |
| 2023-04 | 6 | -7.400000 | 0.043103 | 0.034483 | 5 | 0 | 0 |
| 2023-05 | 3 | -4.833333 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-06 | 3 | -0.150000 | 0.948276 | 0.846154 | 4 | 0 | 0 |
| 2023-07 | 3 | -5.000000 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-08 | 3 | -4.833333 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 4 | -6.233333 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |
| 2023-11 | 7 | -0.900000 | 0.869565 | 1.000000 | 1 | 0 | 0 |
| 2023-12 | 6 | -3.966667 | 0.456621 | 0.312500 | 0 | 0 | 0 |

### B_OPT2023_N9_W3_T2_SB1_TP3

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 52, entry dates 41, entry months 11; SKIP 1, EXCLUDED 1, exclusion share 0.018868; conditional FLAT CLOSED 35.
Net -42.550000 R; PF R / price 0.386003 / 0.329365; expectancy -0.818269 R; win rate 0.134615; average winner / loser 3.821429 / -1.540000 R.
Conditional CLOSED-only DD 46.050000 R; largest winner share 0.186916; largest positive month share 1.000000. Positive / negative / zero months 1 / 10 / 1; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 4 | -6.500000 | 0.000000 | 0.000000 | 5 | 1 | 0 |
| 2023-02 | 8 | -0.733333 | 0.921986 | 0.764706 | 4 | 0 | 0 |
| 2023-03 | 5 | 5.333333 | 2.142857 | 1.764706 | 3 | 0 | 1 |
| 2023-04 | 6 | -7.400000 | 0.043103 | 0.034483 | 5 | 0 | 0 |
| 2023-05 | 3 | -4.833333 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-06 | 3 | -0.150000 | 0.948276 | 0.846154 | 4 | 0 | 0 |
| 2023-07 | 3 | -5.000000 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-08 | 3 | -4.833333 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 4 | -6.233333 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |
| 2023-11 | 7 | -9.900000 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-12 | 6 | -2.300000 | 0.684932 | 0.468750 | 0 | 0 | 0 |

### B_OPT2023_N9_W3_T2_SB1_TP4

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors.
CLOSED 52, entry dates 41, entry months 11; SKIP 1, EXCLUDED 1, exclusion share 0.018868; conditional FLAT CLOSED 35.
Net -46.883333 R; PF R / price 0.323473 / 0.277778; expectancy -0.901603 R; win rate 0.115385; average winner / loser 3.736111 / -1.540000 R.
Conditional CLOSED-only DD 52.050000 R; largest winner share 0.297398; largest positive month share 1.000000. Positive / negative / zero months 1 / 10 / 1; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 4 | -6.500000 | 0.000000 | 0.000000 | 5 | 1 | 0 |
| 2023-02 | 8 | -3.400000 | 0.638298 | 0.529412 | 4 | 0 | 0 |
| 2023-03 | 5 | 2.000000 | 1.428571 | 1.176471 | 3 | 0 | 1 |
| 2023-04 | 6 | -7.400000 | 0.043103 | 0.034483 | 5 | 0 | 0 |
| 2023-05 | 3 | -4.833333 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-06 | 3 | -0.150000 | 0.948276 | 0.846154 | 4 | 0 | 0 |
| 2023-07 | 3 | -5.000000 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-08 | 3 | -4.833333 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 4 | -6.233333 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |
| 2023-11 | 7 | -9.900000 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-12 | 6 | -0.633333 | 0.913242 | 0.625000 | 0 | 0 | 0 |

### B_OPT2023_N9_W3_T2_SB1_TP5

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors.
CLOSED 52, entry dates 41, entry months 11; SKIP 1, EXCLUDED 1, exclusion share 0.018868; conditional FLAT CLOSED 35.
Net -43.550000 R; PF R / price 0.371573 / 0.317460; expectancy -0.837500 R; win rate 0.115385; average winner / loser 4.291667 / -1.540000 R.
Conditional CLOSED-only DD 50.383333 R; largest winner share 0.323625; largest positive month share 0.780142. Positive / negative / zero months 2 / 9 / 1; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 4 | -6.500000 | 0.000000 | 0.000000 | 5 | 1 | 0 |
| 2023-02 | 8 | -3.400000 | 0.638298 | 0.529412 | 4 | 0 | 0 |
| 2023-03 | 5 | 3.666667 | 1.785714 | 1.470588 | 3 | 0 | 1 |
| 2023-04 | 6 | -7.400000 | 0.043103 | 0.034483 | 5 | 0 | 0 |
| 2023-05 | 3 | -4.833333 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-06 | 3 | -0.150000 | 0.948276 | 0.846154 | 4 | 0 | 0 |
| 2023-07 | 3 | -5.000000 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-08 | 3 | -4.833333 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 4 | -6.233333 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |
| 2023-11 | 7 | -9.900000 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-12 | 6 | 1.033333 | 1.141553 | 0.781250 | 0 | 0 | 0 |

### B_OPT2023_N9_W3_T2_SB1_TP6

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors.
CLOSED 52, entry dates 41, entry months 11; SKIP 1, EXCLUDED 1, exclusion share 0.018868; conditional FLAT CLOSED 35.
Net -40.216667 R; PF R / price 0.419673 / 0.357143; expectancy -0.773397 R; win rate 0.115385; average winner / loser 4.847222 / -1.540000 R.
Conditional CLOSED-only DD 48.716667 R; largest winner share 0.343840; largest positive month share 0.663900. Positive / negative / zero months 2 / 9 / 1; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 4 | -6.500000 | 0.000000 | 0.000000 | 5 | 1 | 0 |
| 2023-02 | 8 | -3.400000 | 0.638298 | 0.529412 | 4 | 0 | 0 |
| 2023-03 | 5 | 5.333333 | 2.142857 | 1.764706 | 3 | 0 | 1 |
| 2023-04 | 6 | -7.400000 | 0.043103 | 0.034483 | 5 | 0 | 0 |
| 2023-05 | 3 | -4.833333 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-06 | 3 | -0.150000 | 0.948276 | 0.846154 | 4 | 0 | 0 |
| 2023-07 | 3 | -5.000000 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-08 | 3 | -4.833333 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 4 | -6.233333 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |
| 2023-11 | 7 | -9.900000 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-12 | 6 | 2.700000 | 1.369863 | 0.937500 | 0 | 0 | 0 |

### B_OPT2023_N9_W3_T2_SB1_TP7

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors.
CLOSED 52, entry dates 41, entry months 11; SKIP 1, EXCLUDED 1, exclusion share 0.018868; conditional FLAT CLOSED 35.
Net -40.883333 R; PF R / price 0.410053 / 0.349206; expectancy -0.786218 R; win rate 0.115385; average winner / loser 4.736111 / -1.540000 R.
Conditional CLOSED-only DD 47.050000 R; largest winner share 0.410557; largest positive month share 0.950226. Positive / negative / zero months 2 / 9 / 1; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 4 | -6.500000 | 0.000000 | 0.000000 | 5 | 1 | 0 |
| 2023-02 | 8 | -3.400000 | 0.638298 | 0.529412 | 4 | 0 | 0 |
| 2023-03 | 5 | 7.000000 | 2.500000 | 2.058824 | 3 | 0 | 1 |
| 2023-04 | 6 | -7.400000 | 0.043103 | 0.034483 | 5 | 0 | 0 |
| 2023-05 | 3 | -4.833333 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-06 | 3 | -0.150000 | 0.948276 | 0.846154 | 4 | 0 | 0 |
| 2023-07 | 3 | -5.000000 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-08 | 3 | -4.833333 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 4 | -6.233333 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |
| 2023-11 | 7 | -9.900000 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-12 | 6 | 0.366667 | 1.050228 | 0.718750 | 0 | 0 | 0 |

### B_OPT2023_N9_W3_T2_SB1_TP8

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors.
CLOSED 52, entry dates 41, entry months 11; SKIP 1, EXCLUDED 1, exclusion share 0.018868; conditional FLAT CLOSED 35.
Net -39.216667 R; PF R / price 0.434103 / 0.369048; expectancy -0.754167 R; win rate 0.115385; average winner / loser 5.013889 / -1.540000 R.
Conditional CLOSED-only DD 45.383333 R; largest winner share 0.443213; largest positive month share 0.959410. Positive / negative / zero months 2 / 9 / 1; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 4 | -6.500000 | 0.000000 | 0.000000 | 5 | 1 | 0 |
| 2023-02 | 8 | -3.400000 | 0.638298 | 0.529412 | 4 | 0 | 0 |
| 2023-03 | 5 | 8.666667 | 2.857143 | 2.352941 | 3 | 0 | 1 |
| 2023-04 | 6 | -7.400000 | 0.043103 | 0.034483 | 5 | 0 | 0 |
| 2023-05 | 3 | -4.833333 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-06 | 3 | -0.150000 | 0.948276 | 0.846154 | 4 | 0 | 0 |
| 2023-07 | 3 | -5.000000 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-08 | 3 | -4.833333 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 4 | -6.233333 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |
| 2023-11 | 7 | -9.900000 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-12 | 6 | 0.366667 | 1.050228 | 0.718750 | 0 | 0 | 0 |

### B_OPT2023_N9_W3_T2_SB1_TP9

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors.
CLOSED 52, entry dates 41, entry months 11; SKIP 1, EXCLUDED 1, exclusion share 0.018868; conditional FLAT CLOSED 35.
Net -37.550000 R; PF R / price 0.458153 / 0.388889; expectancy -0.722115 R; win rate 0.115385; average winner / loser 5.291667 / -1.540000 R.
Conditional CLOSED-only DD 44.150000 R; largest winner share 0.472441; largest positive month share 0.965732. Positive / negative / zero months 2 / 9 / 1; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 4 | -6.500000 | 0.000000 | 0.000000 | 5 | 1 | 0 |
| 2023-02 | 8 | -3.400000 | 0.638298 | 0.529412 | 4 | 0 | 0 |
| 2023-03 | 5 | 10.333333 | 3.214286 | 2.647059 | 3 | 0 | 1 |
| 2023-04 | 6 | -7.400000 | 0.043103 | 0.034483 | 5 | 0 | 0 |
| 2023-05 | 3 | -4.833333 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-06 | 3 | -0.150000 | 0.948276 | 0.846154 | 4 | 0 | 0 |
| 2023-07 | 3 | -5.000000 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-08 | 3 | -4.833333 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 4 | -6.233333 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |
| 2023-11 | 7 | -9.900000 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-12 | 6 | 0.366667 | 1.050228 | 0.718750 | 0 | 0 | 0 |

### B_OPT2023_N9_W3_T2_SB1_TP10

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors.
CLOSED 52, entry dates 41, entry months 11; SKIP 1, EXCLUDED 1, exclusion share 0.018868; conditional FLAT CLOSED 35.
Net -35.883333 R; PF R / price 0.482203 / 0.408730; expectancy -0.690064 R; win rate 0.115385; average winner / loser 5.569444 / -1.540000 R.
Conditional CLOSED-only DD 44.150000 R; largest winner share 0.498753; largest positive month share 0.970350. Positive / negative / zero months 2 / 9 / 1; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 4 | -6.500000 | 0.000000 | 0.000000 | 5 | 1 | 0 |
| 2023-02 | 8 | -3.400000 | 0.638298 | 0.529412 | 4 | 0 | 0 |
| 2023-03 | 5 | 12.000000 | 3.571429 | 2.941176 | 3 | 0 | 1 |
| 2023-04 | 6 | -7.400000 | 0.043103 | 0.034483 | 5 | 0 | 0 |
| 2023-05 | 3 | -4.833333 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-06 | 3 | -0.150000 | 0.948276 | 0.846154 | 4 | 0 | 0 |
| 2023-07 | 3 | -5.000000 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-08 | 3 | -4.833333 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 4 | -6.233333 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |
| 2023-11 | 7 | -9.900000 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-12 | 6 | 0.366667 | 1.050228 | 0.718750 | 0 | 0 | 0 |

### B_OPT2023_N9_W3_T3_SB1_TP2

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 35, entry dates 31, entry months 11; SKIP 0, EXCLUDED 1, exclusion share 0.027778; conditional FLAT CLOSED 22.
Net -28.416667 R; PF R / price 0.361423 / 0.337500; expectancy -0.811905 R; win rate 0.171429; average winner / loser 2.680556 / -1.534483 R.
Conditional CLOSED-only DD 28.916667 R; largest winner share 0.207254; largest positive month share 1.000000. Positive / negative / zero months 1 / 10 / 1; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 4 | -6.333333 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-02 | 4 | 3.500000 | 2.105263 | 1.818182 | 4 | 0 | 0 |
| 2023-03 | 5 | -0.900000 | 0.802920 | 0.611111 | 3 | 0 | 1 |
| 2023-04 | 3 | -4.733333 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 1 | -1.666667 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-06 | 3 | -0.150000 | 0.948276 | 0.846154 | 4 | 0 | 0 |
| 2023-07 | 2 | -3.333333 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-08 | 2 | -3.333333 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 4 | -6.233333 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |
| 2023-11 | 4 | -0.833333 | 0.782609 | 1.000000 | 1 | 0 | 0 |
| 2023-12 | 3 | -4.400000 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N9_W3_T3_SB1_TP3

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors.
CLOSED 35, entry dates 31, entry months 11; SKIP 0, EXCLUDED 1, exclusion share 0.027778; conditional FLAT CLOSED 22.
Net -29.250000 R; PF R / price 0.364130 / 0.319277; expectancy -0.835714 R; win rate 0.142857; average winner / loser 3.350000 / -1.533333 R.
Conditional CLOSED-only DD 33.416667 R; largest winner share 0.298507; largest positive month share 0.877660. Positive / negative / zero months 2 / 9 / 1; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 4 | -6.333333 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-02 | 4 | 5.500000 | 2.736842 | 2.363636 | 4 | 0 | 0 |
| 2023-03 | 5 | 0.766667 | 1.167883 | 0.888889 | 3 | 0 | 1 |
| 2023-04 | 3 | -4.733333 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 1 | -1.666667 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-06 | 3 | -0.150000 | 0.948276 | 0.846154 | 4 | 0 | 0 |
| 2023-07 | 2 | -3.333333 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-08 | 2 | -3.333333 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 4 | -6.233333 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |
| 2023-11 | 4 | -5.333333 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-12 | 3 | -4.400000 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N9_W3_T3_SB1_TP4

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors.
CLOSED 35, entry dates 31, entry months 11; SKIP 0, EXCLUDED 1, exclusion share 0.027778; conditional FLAT CLOSED 22.
Net -36.916667 R; PF R / price 0.197464 / 0.180723; expectancy -1.054762 R; win rate 0.114286; average winner / loser 2.270833 / -1.533333 R.
Conditional CLOSED-only DD 36.916667 R; largest winner share 0.403670; largest positive month share 1.000000. Positive / negative / zero months 1 / 10 / 1; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 4 | -6.333333 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-02 | 4 | 2.833333 | 1.894737 | 1.636364 | 4 | 0 | 0 |
| 2023-03 | 5 | -4.233333 | 0.072993 | 0.055556 | 3 | 0 | 1 |
| 2023-04 | 3 | -4.733333 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 1 | -1.666667 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-06 | 3 | -0.150000 | 0.948276 | 0.846154 | 4 | 0 | 0 |
| 2023-07 | 2 | -3.333333 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-08 | 2 | -3.333333 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 4 | -6.233333 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |
| 2023-11 | 4 | -5.333333 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-12 | 3 | -4.400000 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N9_W3_T3_SB1_TP5

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors.
CLOSED 35, entry dates 31, entry months 11; SKIP 0, EXCLUDED 1, exclusion share 0.027778; conditional FLAT CLOSED 22.
Net -36.916667 R; PF R / price 0.197464 / 0.180723; expectancy -1.054762 R; win rate 0.114286; average winner / loser 2.270833 / -1.533333 R.
Conditional CLOSED-only DD 36.916667 R; largest winner share 0.403670; largest positive month share 1.000000. Positive / negative / zero months 1 / 10 / 1; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 4 | -6.333333 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-02 | 4 | 2.833333 | 1.894737 | 1.636364 | 4 | 0 | 0 |
| 2023-03 | 5 | -4.233333 | 0.072993 | 0.055556 | 3 | 0 | 1 |
| 2023-04 | 3 | -4.733333 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 1 | -1.666667 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-06 | 3 | -0.150000 | 0.948276 | 0.846154 | 4 | 0 | 0 |
| 2023-07 | 2 | -3.333333 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-08 | 2 | -3.333333 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 4 | -6.233333 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |
| 2023-11 | 4 | -5.333333 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-12 | 3 | -4.400000 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N9_W3_T3_SB1_TP6

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors.
CLOSED 35, entry dates 31, entry months 11; SKIP 0, EXCLUDED 1, exclusion share 0.027778; conditional FLAT CLOSED 22.
Net -36.916667 R; PF R / price 0.197464 / 0.180723; expectancy -1.054762 R; win rate 0.114286; average winner / loser 2.270833 / -1.533333 R.
Conditional CLOSED-only DD 36.916667 R; largest winner share 0.403670; largest positive month share 1.000000. Positive / negative / zero months 1 / 10 / 1; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 4 | -6.333333 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-02 | 4 | 2.833333 | 1.894737 | 1.636364 | 4 | 0 | 0 |
| 2023-03 | 5 | -4.233333 | 0.072993 | 0.055556 | 3 | 0 | 1 |
| 2023-04 | 3 | -4.733333 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 1 | -1.666667 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-06 | 3 | -0.150000 | 0.948276 | 0.846154 | 4 | 0 | 0 |
| 2023-07 | 2 | -3.333333 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-08 | 2 | -3.333333 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 4 | -6.233333 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |
| 2023-11 | 4 | -5.333333 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-12 | 3 | -4.400000 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N9_W3_T3_SB1_TP7

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors.
CLOSED 35, entry dates 31, entry months 11; SKIP 0, EXCLUDED 1, exclusion share 0.027778; conditional FLAT CLOSED 22.
Net -36.916667 R; PF R / price 0.197464 / 0.180723; expectancy -1.054762 R; win rate 0.114286; average winner / loser 2.270833 / -1.533333 R.
Conditional CLOSED-only DD 36.916667 R; largest winner share 0.403670; largest positive month share 1.000000. Positive / negative / zero months 1 / 10 / 1; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 4 | -6.333333 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-02 | 4 | 2.833333 | 1.894737 | 1.636364 | 4 | 0 | 0 |
| 2023-03 | 5 | -4.233333 | 0.072993 | 0.055556 | 3 | 0 | 1 |
| 2023-04 | 3 | -4.733333 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 1 | -1.666667 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-06 | 3 | -0.150000 | 0.948276 | 0.846154 | 4 | 0 | 0 |
| 2023-07 | 2 | -3.333333 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-08 | 2 | -3.333333 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 4 | -6.233333 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |
| 2023-11 | 4 | -5.333333 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-12 | 3 | -4.400000 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N9_W3_T3_SB1_TP8

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors.
CLOSED 35, entry dates 31, entry months 11; SKIP 0, EXCLUDED 1, exclusion share 0.027778; conditional FLAT CLOSED 22.
Net -36.916667 R; PF R / price 0.197464 / 0.180723; expectancy -1.054762 R; win rate 0.114286; average winner / loser 2.270833 / -1.533333 R.
Conditional CLOSED-only DD 36.916667 R; largest winner share 0.403670; largest positive month share 1.000000. Positive / negative / zero months 1 / 10 / 1; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 4 | -6.333333 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-02 | 4 | 2.833333 | 1.894737 | 1.636364 | 4 | 0 | 0 |
| 2023-03 | 5 | -4.233333 | 0.072993 | 0.055556 | 3 | 0 | 1 |
| 2023-04 | 3 | -4.733333 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 1 | -1.666667 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-06 | 3 | -0.150000 | 0.948276 | 0.846154 | 4 | 0 | 0 |
| 2023-07 | 2 | -3.333333 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-08 | 2 | -3.333333 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 4 | -6.233333 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |
| 2023-11 | 4 | -5.333333 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-12 | 3 | -4.400000 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N9_W3_T3_SB1_TP9

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors.
CLOSED 35, entry dates 31, entry months 11; SKIP 0, EXCLUDED 1, exclusion share 0.027778; conditional FLAT CLOSED 22.
Net -36.916667 R; PF R / price 0.197464 / 0.180723; expectancy -1.054762 R; win rate 0.114286; average winner / loser 2.270833 / -1.533333 R.
Conditional CLOSED-only DD 36.916667 R; largest winner share 0.403670; largest positive month share 1.000000. Positive / negative / zero months 1 / 10 / 1; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 4 | -6.333333 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-02 | 4 | 2.833333 | 1.894737 | 1.636364 | 4 | 0 | 0 |
| 2023-03 | 5 | -4.233333 | 0.072993 | 0.055556 | 3 | 0 | 1 |
| 2023-04 | 3 | -4.733333 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 1 | -1.666667 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-06 | 3 | -0.150000 | 0.948276 | 0.846154 | 4 | 0 | 0 |
| 2023-07 | 2 | -3.333333 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-08 | 2 | -3.333333 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 4 | -6.233333 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |
| 2023-11 | 4 | -5.333333 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-12 | 3 | -4.400000 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N9_W3_T3_SB1_TP10

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors.
CLOSED 35, entry dates 31, entry months 11; SKIP 0, EXCLUDED 1, exclusion share 0.027778; conditional FLAT CLOSED 22.
Net -36.916667 R; PF R / price 0.197464 / 0.180723; expectancy -1.054762 R; win rate 0.114286; average winner / loser 2.270833 / -1.533333 R.
Conditional CLOSED-only DD 36.916667 R; largest winner share 0.403670; largest positive month share 1.000000. Positive / negative / zero months 1 / 10 / 1; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 4 | -6.333333 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-02 | 4 | 2.833333 | 1.894737 | 1.636364 | 4 | 0 | 0 |
| 2023-03 | 5 | -4.233333 | 0.072993 | 0.055556 | 3 | 0 | 1 |
| 2023-04 | 3 | -4.733333 | 0.000000 | 0.000000 | 5 | 0 | 0 |
| 2023-05 | 1 | -1.666667 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-06 | 3 | -0.150000 | 0.948276 | 0.846154 | 4 | 0 | 0 |
| 2023-07 | 2 | -3.333333 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-08 | 2 | -3.333333 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 4 | -6.233333 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |
| 2023-11 | 4 | -5.333333 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-12 | 3 | -4.400000 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N4_W3_T2_SB2_TP2

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 657, entry dates 225, entry months 12; SKIP 2, EXCLUDED 7, exclusion share 0.010542; conditional FLAT CLOSED 620.
Net -299.833333 R; PF R / price 0.560534 / 0.557227; expectancy -0.456367 R; win rate 0.242009; average winner / loser 2.405241 / -1.398087 R.
Conditional CLOSED-only DD 305.533333 R; largest winner share 0.008716; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 12 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 56 | -34.966667 | 0.445267 | 0.435252 | 5 | 0 | 2 |
| 2023-02 | 51 | -32.483333 | 0.393402 | 0.369919 | 4 | 1 | 1 |
| 2023-03 | 78 | -62.316667 | 0.310910 | 0.335859 | 3 | 0 | 2 |
| 2023-04 | 65 | -30.616667 | 0.525078 | 0.510490 | 5 | 1 | 1 |
| 2023-05 | 46 | -4.833333 | 0.883628 | 0.977528 | 3 | 0 | 1 |
| 2023-06 | 51 | -29.933333 | 0.476995 | 0.553785 | 4 | 0 | 0 |
| 2023-07 | 49 | -25.966667 | 0.507274 | 0.432099 | 1 | 0 | 0 |
| 2023-08 | 29 | -8.633333 | 0.703322 | 0.579710 | 2 | 0 | 0 |
| 2023-09 | 47 | -8.866667 | 0.803690 | 0.792271 | 2 | 0 | 0 |
| 2023-10 | 55 | -15.683333 | 0.718937 | 0.677824 | 0 | 0 | 0 |
| 2023-11 | 70 | -30.733333 | 0.576384 | 0.592705 | 1 | 0 | 0 |
| 2023-12 | 60 | -14.800000 | 0.738977 | 0.726592 | 0 | 0 | 0 |

### B_OPT2023_N4_W3_T2_SB2_TP3

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 633, entry dates 223, entry months 12; SKIP 2, EXCLUDED 9, exclusion share 0.014019; conditional FLAT CLOSED 597.
Net -280.800000 R; PF R / price 0.588873 / 0.590954; expectancy -0.443602 R; win rate 0.214850; average winner / loser 2.957353 / -1.402464 R.
Conditional CLOSED-only DD 293.533333 R; largest winner share 0.012432; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 55 | -30.366667 | 0.518244 | 0.503597 | 5 | 0 | 2 |
| 2023-02 | 50 | -24.450000 | 0.541992 | 0.510204 | 4 | 1 | 1 |
| 2023-03 | 69 | -47.733333 | 0.391156 | 0.419075 | 3 | 0 | 3 |
| 2023-04 | 63 | -28.583333 | 0.561605 | 0.508651 | 5 | 1 | 1 |
| 2023-05 | 46 | 5.133333 | 1.119287 | 1.250000 | 3 | 0 | 1 |
| 2023-06 | 50 | -34.900000 | 0.421227 | 0.517110 | 4 | 0 | 1 |
| 2023-07 | 49 | -37.633333 | 0.358887 | 0.287313 | 1 | 0 | 0 |
| 2023-08 | 27 | -15.900000 | 0.462838 | 0.384058 | 2 | 0 | 0 |
| 2023-09 | 47 | -15.633333 | 0.676552 | 0.683486 | 2 | 0 | 0 |
| 2023-10 | 55 | -18.316667 | 0.688845 | 0.637450 | 0 | 0 | 0 |
| 2023-11 | 66 | -15.366667 | 0.774296 | 0.793548 | 1 | 0 | 0 |
| 2023-12 | 56 | -17.050000 | 0.695898 | 0.747126 | 0 | 0 | 0 |

### B_OPT2023_N4_W3_T2_SB2_TP4

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 624, entry dates 222, entry months 12; SKIP 2, EXCLUDED 9, exclusion share 0.014218; conditional FLAT CLOSED 588.
Net -272.500000 R; PF R / price 0.601511 / 0.593187; expectancy -0.436699 R; win rate 0.201923; average winner / loser 3.264550 / -1.401298 R.
Conditional CLOSED-only DD 285.933333 R; largest winner share 0.016207; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 55 | -32.983333 | 0.476732 | 0.449640 | 5 | 0 | 2 |
| 2023-02 | 49 | -16.150000 | 0.689721 | 0.654008 | 4 | 1 | 1 |
| 2023-03 | 68 | -49.000000 | 0.375531 | 0.394203 | 3 | 0 | 3 |
| 2023-04 | 62 | -34.950000 | 0.472054 | 0.406897 | 5 | 1 | 1 |
| 2023-05 | 45 | 3.433333 | 1.079783 | 1.201087 | 3 | 0 | 1 |
| 2023-06 | 50 | -30.000000 | 0.502488 | 0.619772 | 4 | 0 | 1 |
| 2023-07 | 49 | -31.300000 | 0.466780 | 0.369403 | 1 | 0 | 0 |
| 2023-08 | 26 | -19.666667 | 0.341518 | 0.323529 | 2 | 0 | 0 |
| 2023-09 | 47 | -14.333333 | 0.712375 | 0.732143 | 2 | 0 | 0 |
| 2023-10 | 55 | -20.483333 | 0.667478 | 0.567669 | 0 | 0 | 0 |
| 2023-11 | 63 | -8.450000 | 0.869364 | 0.850498 | 1 | 0 | 0 |
| 2023-12 | 55 | -18.616667 | 0.667955 | 0.685824 | 0 | 0 | 0 |

### B_OPT2023_N4_W3_T2_SB2_TP5

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 620, entry dates 222, entry months 12; SKIP 2, EXCLUDED 9, exclusion share 0.014308; conditional FLAT CLOSED 585.
Net -265.450000 R; PF R / price 0.612727 / 0.589256; expectancy -0.428145 R; win rate 0.195161; average winner / loser 3.470937 / -1.401704 R.
Conditional CLOSED-only DD 276.900000 R; largest winner share 0.019842; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 54 | -33.500000 | 0.468535 | 0.438849 | 5 | 0 | 2 |
| 2023-02 | 49 | -11.983333 | 0.769773 | 0.721519 | 4 | 1 | 1 |
| 2023-03 | 68 | -46.000000 | 0.413764 | 0.428986 | 3 | 0 | 3 |
| 2023-04 | 62 | -30.116667 | 0.545065 | 0.462069 | 5 | 1 | 1 |
| 2023-05 | 44 | 3.400000 | 1.081535 | 1.147727 | 3 | 0 | 1 |
| 2023-06 | 50 | -32.000000 | 0.469320 | 0.585551 | 4 | 0 | 1 |
| 2023-07 | 49 | -33.966667 | 0.435770 | 0.332117 | 1 | 0 | 0 |
| 2023-08 | 27 | -31.033333 | 0.088149 | 0.091503 | 2 | 0 | 0 |
| 2023-09 | 47 | -11.033333 | 0.778595 | 0.790179 | 2 | 0 | 0 |
| 2023-10 | 54 | -12.583333 | 0.790975 | 0.664093 | 0 | 0 | 0 |
| 2023-11 | 63 | -5.383333 | 0.916774 | 0.880399 | 1 | 0 | 0 |
| 2023-12 | 53 | -21.250000 | 0.611754 | 0.588933 | 0 | 0 | 0 |

### B_OPT2023_N4_W3_T2_SB2_TP6

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 619, entry dates 222, entry months 12; SKIP 2, EXCLUDED 9, exclusion share 0.014331; conditional FLAT CLOSED 584.
Net -260.633333 R; PF R / price 0.619846 / 0.592593; expectancy -0.421055 R; win rate 0.193861; average winner / loser 3.541389 / -1.402045 R.
Conditional CLOSED-only DD 270.683333 R; largest winner share 0.023531; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 54 | -33.233333 | 0.472766 | 0.431655 | 5 | 0 | 2 |
| 2023-02 | 49 | -11.416667 | 0.780660 | 0.713080 | 4 | 1 | 1 |
| 2023-03 | 68 | -43.000000 | 0.451997 | 0.463768 | 3 | 0 | 3 |
| 2023-04 | 62 | -31.950000 | 0.517372 | 0.448276 | 5 | 1 | 1 |
| 2023-05 | 44 | 1.916667 | 1.045963 | 1.107955 | 3 | 0 | 1 |
| 2023-06 | 50 | -32.000000 | 0.469320 | 0.585551 | 4 | 0 | 1 |
| 2023-07 | 49 | -30.133333 | 0.499446 | 0.375912 | 1 | 0 | 0 |
| 2023-08 | 27 | -31.033333 | 0.088149 | 0.091503 | 2 | 0 | 0 |
| 2023-09 | 47 | -5.133333 | 0.896990 | 0.906250 | 2 | 0 | 0 |
| 2023-10 | 53 | -21.250000 | 0.647985 | 0.540856 | 0 | 0 | 0 |
| 2023-11 | 63 | -3.316667 | 0.948725 | 0.893688 | 1 | 0 | 0 |
| 2023-12 | 53 | -20.083333 | 0.633069 | 0.600791 | 0 | 0 | 0 |

### B_OPT2023_N4_W3_T2_SB2_TP7

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 617, entry dates 222, entry months 12; SKIP 2, EXCLUDED 9, exclusion share 0.014377; conditional FLAT CLOSED 582.
Net -269.150000 R; PF R / price 0.608376 / 0.583115; expectancy -0.436224 R; win rate 0.189627; average winner / loser 3.573647 / -1.402585 R.
Conditional CLOSED-only DD 279.200000 R; largest winner share 0.027903; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 53 | -48.566667 | 0.249356 | 0.240283 | 5 | 0 | 2 |
| 2023-02 | 49 | -8.250000 | 0.841499 | 0.759494 | 4 | 1 | 1 |
| 2023-03 | 68 | -40.000000 | 0.490229 | 0.498551 | 3 | 0 | 3 |
| 2023-04 | 62 | -33.283333 | 0.497231 | 0.424138 | 5 | 1 | 1 |
| 2023-05 | 44 | 4.983333 | 1.119504 | 1.176136 | 3 | 0 | 1 |
| 2023-06 | 50 | -32.000000 | 0.469320 | 0.585551 | 4 | 0 | 1 |
| 2023-07 | 49 | -32.466667 | 0.460687 | 0.350365 | 1 | 0 | 0 |
| 2023-08 | 27 | -31.033333 | 0.088149 | 0.091503 | 2 | 0 | 0 |
| 2023-09 | 46 | -5.133333 | 0.896990 | 0.915179 | 2 | 0 | 0 |
| 2023-10 | 53 | -19.583333 | 0.675594 | 0.560311 | 0 | 0 | 0 |
| 2023-11 | 63 | -5.400000 | 0.916516 | 0.870432 | 1 | 0 | 0 |
| 2023-12 | 53 | -18.416667 | 0.663520 | 0.620553 | 0 | 0 | 0 |

### B_OPT2023_N4_W3_T2_SB2_TP8

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 617, entry dates 222, entry months 12; SKIP 2, EXCLUDED 9, exclusion share 0.014377; conditional FLAT CLOSED 582.
Net -272.550000 R; PF R / price 0.604388 / 0.578896; expectancy -0.441734 R; win rate 0.188006; average winner / loser 3.589511 / -1.403123 R.
Conditional CLOSED-only DD 282.600000 R; largest winner share 0.032022; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 53 | -48.566667 | 0.249356 | 0.240283 | 5 | 0 | 2 |
| 2023-02 | 49 | -20.083333 | 0.626125 | 0.623967 | 4 | 1 | 1 |
| 2023-03 | 68 | -37.000000 | 0.528462 | 0.533333 | 3 | 0 | 3 |
| 2023-04 | 62 | -31.616667 | 0.522407 | 0.441379 | 5 | 1 | 1 |
| 2023-05 | 44 | 8.050000 | 1.193046 | 1.244318 | 3 | 0 | 1 |
| 2023-06 | 50 | -32.000000 | 0.469320 | 0.585551 | 4 | 0 | 1 |
| 2023-07 | 49 | -30.800000 | 0.488372 | 0.368613 | 1 | 0 | 0 |
| 2023-08 | 27 | -31.033333 | 0.088149 | 0.091503 | 2 | 0 | 0 |
| 2023-09 | 46 | -10.933333 | 0.780602 | 0.776786 | 2 | 0 | 0 |
| 2023-10 | 53 | -17.916667 | 0.703203 | 0.579767 | 0 | 0 | 0 |
| 2023-11 | 63 | -3.900000 | 0.939706 | 0.890365 | 1 | 0 | 0 |
| 2023-12 | 53 | -16.750000 | 0.693971 | 0.640316 | 0 | 0 | 0 |

### B_OPT2023_N4_W3_T2_SB2_TP9

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 615, entry dates 222, entry months 12; SKIP 2, EXCLUDED 9, exclusion share 0.014423; conditional FLAT CLOSED 580.
Net -289.400000 R; PF R / price 0.577991 / 0.558689; expectancy -0.470569 R; win rate 0.188618; average winner / loser 3.416954 / -1.402386 R.
Conditional CLOSED-only DD 299.983333 R; largest winner share 0.037844; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 53 | -48.566667 | 0.249356 | 0.240283 | 5 | 0 | 2 |
| 2023-02 | 49 | -18.583333 | 0.654049 | 0.648760 | 4 | 1 | 1 |
| 2023-03 | 67 | -42.583333 | 0.445530 | 0.455882 | 3 | 0 | 3 |
| 2023-04 | 62 | -42.283333 | 0.361279 | 0.331034 | 5 | 1 | 1 |
| 2023-05 | 44 | 11.116667 | 1.266587 | 1.312500 | 3 | 0 | 1 |
| 2023-06 | 50 | -32.000000 | 0.469320 | 0.585551 | 4 | 0 | 1 |
| 2023-07 | 49 | -29.133333 | 0.516058 | 0.386861 | 1 | 0 | 0 |
| 2023-08 | 27 | -31.033333 | 0.088149 | 0.091503 | 2 | 0 | 0 |
| 2023-09 | 46 | -11.433333 | 0.770569 | 0.741071 | 2 | 0 | 0 |
| 2023-10 | 52 | -27.416667 | 0.534258 | 0.462151 | 0 | 0 | 0 |
| 2023-11 | 63 | -2.400000 | 0.962896 | 0.910299 | 1 | 0 | 0 |
| 2023-12 | 53 | -15.083333 | 0.724421 | 0.660079 | 0 | 0 | 0 |

### B_OPT2023_N4_W3_T2_SB2_TP10

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 615, entry dates 222, entry months 12; SKIP 2, EXCLUDED 9, exclusion share 0.014423; conditional FLAT CLOSED 580.
Net -278.333333 R; PF R / price 0.594128 / 0.571475; expectancy -0.452575 R; win rate 0.188618; average winner / loser 3.512356 / -1.402386 R.
Conditional CLOSED-only DD 292.083333 R; largest winner share 0.040906; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 53 | -48.566667 | 0.249356 | 0.240283 | 5 | 0 | 2 |
| 2023-02 | 49 | -17.083333 | 0.681973 | 0.673554 | 4 | 1 | 1 |
| 2023-03 | 67 | -42.583333 | 0.445530 | 0.455882 | 3 | 0 | 3 |
| 2023-04 | 62 | -42.283333 | 0.361279 | 0.331034 | 5 | 1 | 1 |
| 2023-05 | 44 | 14.183333 | 1.340128 | 1.380682 | 3 | 0 | 1 |
| 2023-06 | 50 | -32.000000 | 0.469320 | 0.585551 | 4 | 0 | 1 |
| 2023-07 | 49 | -27.466667 | 0.543743 | 0.405109 | 1 | 0 | 0 |
| 2023-08 | 27 | -31.033333 | 0.088149 | 0.091503 | 2 | 0 | 0 |
| 2023-09 | 46 | -9.766667 | 0.804013 | 0.763393 | 2 | 0 | 0 |
| 2023-10 | 52 | -27.416667 | 0.534258 | 0.462151 | 0 | 0 | 0 |
| 2023-11 | 63 | -0.900000 | 0.986086 | 0.930233 | 1 | 0 | 0 |
| 2023-12 | 53 | -13.416667 | 0.754872 | 0.679842 | 0 | 0 | 0 |

### B_OPT2023_N5_W3_T2_SB2_TP2

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 437, entry dates 197, entry months 12; SKIP 2, EXCLUDED 6, exclusion share 0.013544; conditional FLAT CLOSED 415.
Net -238.833333 R; PF R / price 0.492815 / 0.504636; expectancy -0.546529 R; win rate 0.219680; average winner / loser 2.417361 / -1.418373 R.
Conditional CLOSED-only DD 243.300000 R; largest winner share 0.014364; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 12 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 37 | -22.483333 | 0.459752 | 0.446328 | 5 | 0 | 1 |
| 2023-02 | 36 | -14.383333 | 0.607905 | 0.473373 | 4 | 1 | 1 |
| 2023-03 | 58 | -39.316667 | 0.414640 | 0.397887 | 3 | 0 | 1 |
| 2023-04 | 38 | -28.850000 | 0.316081 | 0.324324 | 5 | 0 | 1 |
| 2023-05 | 26 | -5.616667 | 0.777264 | 0.767857 | 3 | 1 | 1 |
| 2023-06 | 40 | -23.800000 | 0.479971 | 0.548387 | 4 | 0 | 1 |
| 2023-07 | 30 | -20.866667 | 0.367677 | 0.443662 | 1 | 0 | 0 |
| 2023-08 | 26 | -19.133333 | 0.346985 | 0.382812 | 2 | 0 | 0 |
| 2023-09 | 34 | -12.733333 | 0.650183 | 0.630303 | 2 | 0 | 0 |
| 2023-10 | 32 | -11.883333 | 0.627092 | 0.582192 | 0 | 0 | 0 |
| 2023-11 | 43 | -25.133333 | 0.428788 | 0.473684 | 1 | 0 | 0 |
| 2023-12 | 37 | -14.633333 | 0.611848 | 0.745455 | 0 | 0 | 0 |

### B_OPT2023_N5_W3_T2_SB2_TP3

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 426, entry dates 196, entry months 12; SKIP 2, EXCLUDED 6, exclusion share 0.013889; conditional FLAT CLOSED 405.
Net -221.216667 R; PF R / price 0.531337 / 0.545720; expectancy -0.519288 R; win rate 0.194836; average winner / loser 3.021687 / -1.417467 R.
Conditional CLOSED-only DD 229.683333 R; largest winner share 0.019936; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 34 | -18.516667 | 0.521739 | 0.469512 | 5 | 0 | 1 |
| 2023-02 | 35 | -13.783333 | 0.622202 | 0.500000 | 4 | 1 | 1 |
| 2023-03 | 57 | -34.116667 | 0.492060 | 0.503521 | 3 | 0 | 1 |
| 2023-04 | 37 | -27.283333 | 0.350655 | 0.365591 | 5 | 0 | 1 |
| 2023-05 | 25 | 4.583333 | 1.192442 | 1.190476 | 3 | 1 | 1 |
| 2023-06 | 40 | -22.166667 | 0.531030 | 0.604167 | 4 | 0 | 1 |
| 2023-07 | 30 | -20.633333 | 0.399029 | 0.453333 | 1 | 0 | 0 |
| 2023-08 | 24 | -21.650000 | 0.230906 | 0.187500 | 2 | 0 | 0 |
| 2023-09 | 34 | -16.433333 | 0.568301 | 0.570588 | 2 | 0 | 0 |
| 2023-10 | 31 | -9.450000 | 0.703452 | 0.650685 | 0 | 0 | 0 |
| 2023-11 | 43 | -27.900000 | 0.389051 | 0.466667 | 1 | 0 | 0 |
| 2023-12 | 36 | -13.866667 | 0.639515 | 0.797619 | 0 | 0 | 0 |

### B_OPT2023_N5_W3_T2_SB2_TP4

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 421, entry dates 196, entry months 12; SKIP 2, EXCLUDED 7, exclusion share 0.016355; conditional FLAT CLOSED 400.
Net -224.666667 R; PF R / price 0.520541 / 0.526624; expectancy -0.533650 R; win rate 0.185273; average winner / loser 3.127137 / -1.415660 R.
Conditional CLOSED-only DD 232.466667 R; largest winner share 0.027332; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 34 | -15.083333 | 0.610418 | 0.524390 | 5 | 0 | 1 |
| 2023-02 | 34 | -13.050000 | 0.625180 | 0.515337 | 4 | 1 | 1 |
| 2023-03 | 56 | -38.250000 | 0.416031 | 0.408602 | 3 | 0 | 1 |
| 2023-04 | 37 | -29.916667 | 0.287981 | 0.268817 | 5 | 0 | 1 |
| 2023-05 | 24 | 1.883333 | 1.079076 | 1.161905 | 3 | 1 | 1 |
| 2023-06 | 38 | -25.300000 | 0.447196 | 0.505376 | 4 | 0 | 2 |
| 2023-07 | 30 | -16.400000 | 0.522330 | 0.593333 | 1 | 0 | 0 |
| 2023-08 | 24 | -19.983333 | 0.290112 | 0.226562 | 2 | 0 | 0 |
| 2023-09 | 34 | -17.466667 | 0.557432 | 0.531073 | 2 | 0 | 0 |
| 2023-10 | 31 | -5.350000 | 0.832113 | 0.767123 | 0 | 0 | 0 |
| 2023-11 | 43 | -29.650000 | 0.350730 | 0.420513 | 1 | 0 | 0 |
| 2023-12 | 36 | -16.100000 | 0.581456 | 0.726190 | 0 | 0 | 0 |

### B_OPT2023_N5_W3_T2_SB2_TP5

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 419, entry dates 196, entry months 12; SKIP 2, EXCLUDED 7, exclusion share 0.016432; conditional FLAT CLOSED 398.
Net -225.133333 R; PF R / price 0.519545 / 0.510742; expectancy -0.537311 R; win rate 0.181384; average winner / loser 3.203289 / -1.415660 R.
Conditional CLOSED-only DD 234.600000 R; largest winner share 0.034230; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 34 | -13.000000 | 0.664227 | 0.554878 | 5 | 0 | 1 |
| 2023-02 | 34 | -11.783333 | 0.661561 | 0.533742 | 4 | 1 | 1 |
| 2023-03 | 56 | -36.216667 | 0.460794 | 0.450704 | 3 | 0 | 1 |
| 2023-04 | 37 | -32.583333 | 0.224514 | 0.225806 | 5 | 0 | 1 |
| 2023-05 | 24 | 0.783333 | 1.032890 | 1.095238 | 3 | 1 | 1 |
| 2023-06 | 38 | -22.233333 | 0.514202 | 0.569892 | 4 | 0 | 2 |
| 2023-07 | 30 | -15.966667 | 0.534951 | 0.606667 | 1 | 0 | 0 |
| 2023-08 | 24 | -18.316667 | 0.349319 | 0.265625 | 2 | 0 | 0 |
| 2023-09 | 33 | -17.200000 | 0.546971 | 0.485380 | 2 | 0 | 0 |
| 2023-10 | 31 | -12.100000 | 0.635542 | 0.506494 | 0 | 0 | 0 |
| 2023-11 | 43 | -29.650000 | 0.350730 | 0.420513 | 1 | 0 | 0 |
| 2023-12 | 35 | -16.866667 | 0.543733 | 0.672840 | 0 | 0 | 0 |

### B_OPT2023_N5_W3_T2_SB2_TP6

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 419, entry dates 196, entry months 12; SKIP 2, EXCLUDED 7, exclusion share 0.016432; conditional FLAT CLOSED 398.
Net -222.150000 R; PF R / price 0.525911 / 0.515625; expectancy -0.530191 R; win rate 0.181384; average winner / loser 3.242544 / -1.415660 R.
Conditional CLOSED-only DD 224.950000 R; largest winner share 0.040579; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 12 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 34 | -18.000000 | 0.535084 | 0.463415 | 5 | 0 | 1 |
| 2023-02 | 34 | -10.116667 | 0.709430 | 0.564417 | 4 | 1 | 1 |
| 2023-03 | 56 | -36.466667 | 0.457072 | 0.447183 | 3 | 0 | 1 |
| 2023-04 | 37 | -32.583333 | 0.224514 | 0.225806 | 5 | 0 | 1 |
| 2023-05 | 24 | -3.116667 | 0.869139 | 0.895238 | 3 | 1 | 1 |
| 2023-06 | 38 | -19.166667 | 0.581209 | 0.634409 | 4 | 0 | 2 |
| 2023-07 | 30 | -15.133333 | 0.559223 | 0.646667 | 1 | 0 | 0 |
| 2023-08 | 24 | -17.983333 | 0.361160 | 0.273438 | 2 | 0 | 0 |
| 2023-09 | 33 | -14.033333 | 0.630378 | 0.549708 | 2 | 0 | 0 |
| 2023-10 | 31 | -10.433333 | 0.685743 | 0.538961 | 0 | 0 | 0 |
| 2023-11 | 43 | -29.650000 | 0.350730 | 0.420513 | 1 | 0 | 0 |
| 2023-12 | 35 | -15.466667 | 0.581605 | 0.716049 | 0 | 0 | 0 |

### B_OPT2023_N5_W3_T2_SB2_TP7

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 418, entry dates 196, entry months 12; SKIP 2, EXCLUDED 7, exclusion share 0.016471; conditional FLAT CLOSED 397.
Net -222.916667 R; PF R / price 0.525961 / 0.520214; expectancy -0.533293 R; win rate 0.177033; average winner / loser 3.342342 / -1.416416 R.
Conditional CLOSED-only DD 225.716667 R; largest winner share 0.047170; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 12 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 34 | -29.666667 | 0.265374 | 0.272189 | 5 | 0 | 1 |
| 2023-02 | 34 | -8.450000 | 0.757300 | 0.595092 | 4 | 1 | 1 |
| 2023-03 | 56 | -33.466667 | 0.501737 | 0.489437 | 3 | 0 | 1 |
| 2023-04 | 37 | -32.583333 | 0.224514 | 0.225806 | 5 | 0 | 1 |
| 2023-05 | 24 | -1.616667 | 0.932120 | 0.952381 | 3 | 1 | 1 |
| 2023-06 | 38 | -16.100000 | 0.648216 | 0.698925 | 4 | 0 | 2 |
| 2023-07 | 30 | -13.800000 | 0.598058 | 0.700000 | 1 | 0 | 0 |
| 2023-08 | 24 | -17.983333 | 0.361160 | 0.273438 | 2 | 0 | 0 |
| 2023-09 | 32 | -16.766667 | 0.558385 | 0.473684 | 2 | 0 | 0 |
| 2023-10 | 31 | -8.766667 | 0.735944 | 0.571429 | 0 | 0 | 0 |
| 2023-11 | 43 | -29.650000 | 0.350730 | 0.420513 | 1 | 0 | 0 |
| 2023-12 | 35 | -14.066667 | 0.619477 | 0.759259 | 0 | 0 | 0 |

### B_OPT2023_N5_W3_T2_SB2_TP8

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 418, entry dates 196, entry months 12; SKIP 2, EXCLUDED 7, exclusion share 0.016471; conditional FLAT CLOSED 397.
Net -214.350000 R; PF R / price 0.544179 / 0.532392; expectancy -0.512799 R; win rate 0.177033; average winner / loser 3.458108 / -1.416416 R.
Conditional CLOSED-only DD 217.150000 R; largest winner share 0.052104; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 12 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 34 | -29.666667 | 0.265374 | 0.272189 | 5 | 0 | 1 |
| 2023-02 | 34 | -6.783333 | 0.805170 | 0.625767 | 4 | 1 | 1 |
| 2023-03 | 56 | -30.466667 | 0.546402 | 0.531690 | 3 | 0 | 1 |
| 2023-04 | 37 | -32.583333 | 0.224514 | 0.225806 | 5 | 0 | 1 |
| 2023-05 | 24 | -0.116667 | 0.995101 | 1.009524 | 3 | 1 | 1 |
| 2023-06 | 38 | -18.433333 | 0.597232 | 0.618280 | 4 | 0 | 2 |
| 2023-07 | 30 | -13.800000 | 0.598058 | 0.700000 | 1 | 0 | 0 |
| 2023-08 | 24 | -17.983333 | 0.361160 | 0.273438 | 2 | 0 | 0 |
| 2023-09 | 32 | -15.100000 | 0.602283 | 0.502924 | 2 | 0 | 0 |
| 2023-10 | 31 | -7.100000 | 0.786145 | 0.603896 | 0 | 0 | 0 |
| 2023-11 | 43 | -29.650000 | 0.350730 | 0.420513 | 1 | 0 | 0 |
| 2023-12 | 35 | -12.666667 | 0.657349 | 0.802469 | 0 | 0 | 0 |

### B_OPT2023_N5_W3_T2_SB2_TP9

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 418, entry dates 196, entry months 12; SKIP 2, EXCLUDED 7, exclusion share 0.016471; conditional FLAT CLOSED 397.
Net -224.700000 R; PF R / price 0.522169 / 0.515830; expectancy -0.537560 R; win rate 0.177033; average winner / loser 3.318243 / -1.416416 R.
Conditional CLOSED-only DD 227.500000 R; largest winner share 0.061087; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 34 | -29.666667 | 0.265374 | 0.272189 | 5 | 0 | 1 |
| 2023-02 | 34 | -5.116667 | 0.853040 | 0.656442 | 4 | 1 | 1 |
| 2023-03 | 56 | -37.716667 | 0.438462 | 0.429577 | 3 | 0 | 1 |
| 2023-04 | 37 | -32.583333 | 0.224514 | 0.225806 | 5 | 0 | 1 |
| 2023-05 | 24 | 1.383333 | 1.058083 | 1.066667 | 3 | 1 | 1 |
| 2023-06 | 38 | -16.766667 | 0.633649 | 0.645161 | 4 | 0 | 2 |
| 2023-07 | 30 | -13.800000 | 0.598058 | 0.700000 | 1 | 0 | 0 |
| 2023-08 | 24 | -17.983333 | 0.361160 | 0.273438 | 2 | 0 | 0 |
| 2023-09 | 32 | -13.433333 | 0.646181 | 0.532164 | 2 | 0 | 0 |
| 2023-10 | 31 | -18.100000 | 0.454819 | 0.389610 | 0 | 0 | 0 |
| 2023-11 | 43 | -29.650000 | 0.350730 | 0.420513 | 1 | 0 | 0 |
| 2023-12 | 35 | -11.266667 | 0.695221 | 0.845679 | 0 | 0 | 0 |

### B_OPT2023_N5_W3_T2_SB2_TP10

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 418, entry dates 196, entry months 12; SKIP 2, EXCLUDED 7, exclusion share 0.016471; conditional FLAT CLOSED 397.
Net -216.800000 R; PF R / price 0.538969 / 0.529469; expectancy -0.518660 R; win rate 0.177033; average winner / loser 3.425000 / -1.416416 R.
Conditional CLOSED-only DD 219.600000 R; largest winner share 0.065759; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 34 | -29.666667 | 0.265374 | 0.272189 | 5 | 0 | 1 |
| 2023-02 | 34 | -3.450000 | 0.900910 | 0.687117 | 4 | 1 | 1 |
| 2023-03 | 56 | -37.716667 | 0.438462 | 0.429577 | 3 | 0 | 1 |
| 2023-04 | 37 | -32.583333 | 0.224514 | 0.225806 | 5 | 0 | 1 |
| 2023-05 | 24 | 2.883333 | 1.121064 | 1.123810 | 3 | 1 | 1 |
| 2023-06 | 38 | -15.100000 | 0.670066 | 0.672043 | 4 | 0 | 2 |
| 2023-07 | 30 | -13.800000 | 0.598058 | 0.700000 | 1 | 0 | 0 |
| 2023-08 | 24 | -17.983333 | 0.361160 | 0.273438 | 2 | 0 | 0 |
| 2023-09 | 32 | -11.766667 | 0.690079 | 0.561404 | 2 | 0 | 0 |
| 2023-10 | 31 | -18.100000 | 0.454819 | 0.389610 | 0 | 0 | 0 |
| 2023-11 | 43 | -29.650000 | 0.350730 | 0.420513 | 1 | 0 | 0 |
| 2023-12 | 35 | -9.866667 | 0.733093 | 0.888889 | 0 | 0 | 0 |

### B_OPT2023_N6_W3_T2_SB2_TP2

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 272, entry dates 159, entry months 12; SKIP 2, EXCLUDED 4, exclusion share 0.014493; conditional FLAT CLOSED 257.
Net -154.566667 R; PF R / price 0.466060 / 0.446275; expectancy -0.568260 R; win rate 0.216912; average winner / loser 2.286723 / -1.385088 R.
Conditional CLOSED-only DD 154.566667 R; largest winner share 0.024707; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 12 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 24 | -12.100000 | 0.564226 | 0.491525 | 5 | 0 | 1 |
| 2023-02 | 28 | -17.733333 | 0.343210 | 0.311111 | 4 | 0 | 0 |
| 2023-03 | 30 | -5.033333 | 0.816748 | 0.863248 | 3 | 1 | 1 |
| 2023-04 | 27 | -8.733333 | 0.676543 | 0.635593 | 5 | 0 | 1 |
| 2023-05 | 21 | -15.150000 | 0.354862 | 0.455556 | 3 | 1 | 0 |
| 2023-06 | 23 | -16.733333 | 0.385557 | 0.278261 | 4 | 0 | 1 |
| 2023-07 | 13 | -5.466667 | 0.536723 | 0.542373 | 1 | 0 | 0 |
| 2023-08 | 13 | -3.300000 | 0.734584 | 0.610169 | 2 | 0 | 0 |
| 2023-09 | 22 | -17.266667 | 0.332474 | 0.347826 | 2 | 0 | 0 |
| 2023-10 | 13 | -7.933333 | 0.413793 | 0.381818 | 0 | 0 | 0 |
| 2023-11 | 34 | -29.900000 | 0.251252 | 0.265896 | 1 | 0 | 0 |
| 2023-12 | 24 | -15.216667 | 0.413992 | 0.371901 | 0 | 0 | 0 |

### B_OPT2023_N6_W3_T2_SB2_TP3

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 267, entry dates 159, entry months 12; SKIP 2, EXCLUDED 4, exclusion share 0.014760; conditional FLAT CLOSED 253.
Net -168.800000 R; PF R / price 0.430947 / 0.413978; expectancy -0.632210 R; win rate 0.183521; average winner / loser 2.608844 / -1.386137 R.
Conditional CLOSED-only DD 168.800000 R; largest winner share 0.039113; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 12 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 22 | -17.433333 | 0.372149 | 0.271186 | 5 | 0 | 1 |
| 2023-02 | 28 | -20.533333 | 0.276995 | 0.246479 | 4 | 0 | 0 |
| 2023-03 | 29 | -10.666667 | 0.629630 | 0.683333 | 3 | 1 | 1 |
| 2023-04 | 26 | -16.800000 | 0.425641 | 0.401575 | 5 | 0 | 1 |
| 2023-05 | 21 | -14.616667 | 0.377573 | 0.500000 | 3 | 1 | 0 |
| 2023-06 | 23 | -12.400000 | 0.544676 | 0.391304 | 4 | 0 | 1 |
| 2023-07 | 13 | -2.633333 | 0.776836 | 0.779661 | 1 | 0 | 0 |
| 2023-08 | 12 | -2.933333 | 0.764075 | 0.559322 | 2 | 0 | 0 |
| 2023-09 | 22 | -16.466667 | 0.363402 | 0.400000 | 2 | 0 | 0 |
| 2023-10 | 13 | -6.433333 | 0.524631 | 0.490909 | 0 | 0 | 0 |
| 2023-11 | 34 | -25.500000 | 0.361436 | 0.381503 | 1 | 0 | 0 |
| 2023-12 | 24 | -22.383333 | 0.204384 | 0.240310 | 0 | 0 | 0 |

### B_OPT2023_N6_W3_T2_SB2_TP4

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 266, entry dates 159, entry months 12; SKIP 2, EXCLUDED 4, exclusion share 0.014815; conditional FLAT CLOSED 252.
Net -154.600000 R; PF R / price 0.479111 / 0.455035; expectancy -0.581203 R; win rate 0.180451; average winner / loser 2.962500 / -1.386916 R.
Conditional CLOSED-only DD 154.600000 R; largest winner share 0.046882; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 21 | -12.600000 | 0.520305 | 0.375000 | 5 | 0 | 1 |
| 2023-02 | 28 | -19.133333 | 0.326291 | 0.295775 | 4 | 0 | 0 |
| 2023-03 | 29 | -9.400000 | 0.673611 | 0.708333 | 3 | 1 | 1 |
| 2023-04 | 26 | -13.733333 | 0.530484 | 0.496063 | 5 | 0 | 1 |
| 2023-05 | 21 | -13.283333 | 0.434351 | 0.588889 | 3 | 1 | 0 |
| 2023-06 | 23 | -9.066667 | 0.667075 | 0.478261 | 4 | 0 | 1 |
| 2023-07 | 13 | -2.633333 | 0.776836 | 0.728814 | 1 | 0 | 0 |
| 2023-08 | 12 | 0.233333 | 1.018767 | 0.745763 | 2 | 0 | 0 |
| 2023-09 | 22 | -13.666667 | 0.471649 | 0.521739 | 2 | 0 | 0 |
| 2023-10 | 13 | -4.933333 | 0.635468 | 0.600000 | 0 | 0 | 0 |
| 2023-11 | 34 | -31.833333 | 0.234776 | 0.303371 | 1 | 0 | 0 |
| 2023-12 | 24 | -24.550000 | 0.127370 | 0.139535 | 0 | 0 | 0 |

### B_OPT2023_N6_W3_T2_SB2_TP5

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 263, entry dates 158, entry months 12; SKIP 2, EXCLUDED 5, exclusion share 0.018657; conditional FLAT CLOSED 249.
Net -143.900000 R; PF R / price 0.510655 / 0.482893; expectancy -0.547148 R; win rate 0.178707; average winner / loser 3.195035 / -1.387107 R.
Conditional CLOSED-only DD 143.900000 R; largest winner share 0.055494; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 21 | -9.266667 | 0.647208 | 0.464286 | 5 | 0 | 1 |
| 2023-02 | 28 | -17.733333 | 0.375587 | 0.345070 | 4 | 0 | 0 |
| 2023-03 | 29 | -7.733333 | 0.731481 | 0.750000 | 3 | 1 | 1 |
| 2023-04 | 26 | -10.666667 | 0.635328 | 0.590551 | 5 | 0 | 1 |
| 2023-05 | 21 | -11.950000 | 0.491128 | 0.677778 | 3 | 1 | 0 |
| 2023-06 | 21 | -12.733333 | 0.508366 | 0.373832 | 4 | 0 | 2 |
| 2023-07 | 13 | -1.133333 | 0.903955 | 0.830508 | 1 | 0 | 0 |
| 2023-08 | 12 | 3.400000 | 1.273458 | 0.932203 | 2 | 0 | 0 |
| 2023-09 | 21 | -15.266667 | 0.376022 | 0.416667 | 2 | 0 | 0 |
| 2023-10 | 13 | -3.433333 | 0.746305 | 0.709091 | 0 | 0 | 0 |
| 2023-11 | 34 | -32.833333 | 0.210737 | 0.269663 | 1 | 0 | 0 |
| 2023-12 | 24 | -24.550000 | 0.127370 | 0.139535 | 0 | 0 | 0 |

### B_OPT2023_N6_W3_T2_SB2_TP6

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 263, entry dates 158, entry months 12; SKIP 2, EXCLUDED 5, exclusion share 0.018657; conditional FLAT CLOSED 249.
Net -149.000000 R; PF R / price 0.493312 / 0.465008; expectancy -0.566540 R; win rate 0.178707; average winner / loser 3.086525 / -1.387107 R.
Conditional CLOSED-only DD 149.000000 R; largest winner share 0.068934; largest positive month share 0.934524. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 21 | -9.933333 | 0.621827 | 0.446429 | 5 | 0 | 1 |
| 2023-02 | 28 | -17.333333 | 0.389671 | 0.359155 | 4 | 0 | 0 |
| 2023-03 | 29 | -11.733333 | 0.592593 | 0.650000 | 3 | 1 | 1 |
| 2023-04 | 26 | -12.666667 | 0.566952 | 0.543307 | 5 | 0 | 1 |
| 2023-05 | 21 | -14.283333 | 0.391767 | 0.522222 | 3 | 1 | 0 |
| 2023-06 | 21 | -11.066667 | 0.572716 | 0.420561 | 4 | 0 | 2 |
| 2023-07 | 13 | 0.366667 | 1.031073 | 0.932203 | 1 | 0 | 0 |
| 2023-08 | 12 | 5.233333 | 1.420912 | 1.050847 | 2 | 0 | 0 |
| 2023-09 | 21 | -18.266667 | 0.253406 | 0.277778 | 2 | 0 | 0 |
| 2023-10 | 13 | -1.933333 | 0.857143 | 0.818182 | 0 | 0 | 0 |
| 2023-11 | 34 | -32.833333 | 0.210737 | 0.269663 | 1 | 0 | 0 |
| 2023-12 | 24 | -24.550000 | 0.127370 | 0.139535 | 0 | 0 | 0 |

### B_OPT2023_N6_W3_T2_SB2_TP7

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 263, entry dates 158, entry months 12; SKIP 2, EXCLUDED 5, exclusion share 0.018657; conditional FLAT CLOSED 249.
Net -165.750000 R; PF R / price 0.439529 / 0.422928; expectancy -0.630228 R; win rate 0.174905; average winner / loser 2.825725 / -1.388419 R.
Conditional CLOSED-only DD 165.750000 R; largest winner share 0.089755; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 21 | -21.600000 | 0.226730 | 0.170940 | 5 | 0 | 1 |
| 2023-02 | 28 | -17.333333 | 0.389671 | 0.359155 | 4 | 0 | 0 |
| 2023-03 | 29 | -11.733333 | 0.592593 | 0.650000 | 3 | 1 | 1 |
| 2023-04 | 26 | -12.666667 | 0.566952 | 0.543307 | 5 | 0 | 1 |
| 2023-05 | 21 | -14.283333 | 0.391767 | 0.522222 | 3 | 1 | 0 |
| 2023-06 | 21 | -9.400000 | 0.637066 | 0.467290 | 4 | 0 | 2 |
| 2023-07 | 13 | -2.133333 | 0.819209 | 0.762712 | 1 | 0 | 0 |
| 2023-08 | 12 | 6.733333 | 1.541555 | 1.152542 | 2 | 0 | 0 |
| 2023-09 | 21 | -18.266667 | 0.253406 | 0.277778 | 2 | 0 | 0 |
| 2023-10 | 13 | -7.683333 | 0.432266 | 0.400000 | 0 | 0 | 0 |
| 2023-11 | 34 | -32.833333 | 0.210737 | 0.269663 | 1 | 0 | 0 |
| 2023-12 | 24 | -24.550000 | 0.127370 | 0.139535 | 0 | 0 | 0 |

### B_OPT2023_N6_W3_T2_SB2_TP8

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 263, entry dates 158, entry months 12; SKIP 2, EXCLUDED 5, exclusion share 0.018657; conditional FLAT CLOSED 249.
Net -162.583333 R; PF R / price 0.450237 / 0.431448; expectancy -0.618188 R; win rate 0.174905; average winner / loser 2.894565 / -1.388419 R.
Conditional CLOSED-only DD 162.583333 R; largest winner share 0.100138; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 21 | -21.600000 | 0.226730 | 0.170940 | 5 | 0 | 1 |
| 2023-02 | 28 | -17.333333 | 0.389671 | 0.359155 | 4 | 0 | 0 |
| 2023-03 | 29 | -11.733333 | 0.592593 | 0.650000 | 3 | 1 | 1 |
| 2023-04 | 26 | -12.666667 | 0.566952 | 0.543307 | 5 | 0 | 1 |
| 2023-05 | 21 | -14.283333 | 0.391767 | 0.522222 | 3 | 1 | 0 |
| 2023-06 | 21 | -7.733333 | 0.701416 | 0.514019 | 4 | 0 | 2 |
| 2023-07 | 13 | -2.133333 | 0.819209 | 0.762712 | 1 | 0 | 0 |
| 2023-08 | 12 | 8.233333 | 1.662198 | 1.254237 | 2 | 0 | 0 |
| 2023-09 | 21 | -18.266667 | 0.253406 | 0.277778 | 2 | 0 | 0 |
| 2023-10 | 13 | -7.683333 | 0.432266 | 0.400000 | 0 | 0 | 0 |
| 2023-11 | 34 | -32.833333 | 0.210737 | 0.269663 | 1 | 0 | 0 |
| 2023-12 | 24 | -24.550000 | 0.127370 | 0.139535 | 0 | 0 | 0 |

### B_OPT2023_N6_W3_T2_SB2_TP9

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 263, entry dates 158, entry months 12; SKIP 2, EXCLUDED 5, exclusion share 0.018657; conditional FLAT CLOSED 249.
Net -160.666667 R; PF R / price 0.456718 / 0.436096; expectancy -0.610900 R; win rate 0.174905; average winner / loser 2.936232 / -1.388419 R.
Conditional CLOSED-only DD 160.666667 R; largest winner share 0.111056; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 21 | -21.600000 | 0.226730 | 0.170940 | 5 | 0 | 1 |
| 2023-02 | 28 | -17.333333 | 0.389671 | 0.359155 | 4 | 0 | 0 |
| 2023-03 | 29 | -11.733333 | 0.592593 | 0.650000 | 3 | 1 | 1 |
| 2023-04 | 26 | -12.666667 | 0.566952 | 0.543307 | 5 | 0 | 1 |
| 2023-05 | 21 | -14.283333 | 0.391767 | 0.522222 | 3 | 1 | 0 |
| 2023-06 | 21 | -6.066667 | 0.765766 | 0.560748 | 4 | 0 | 2 |
| 2023-07 | 13 | -2.133333 | 0.819209 | 0.762712 | 1 | 0 | 0 |
| 2023-08 | 12 | 8.483333 | 1.682306 | 1.271186 | 2 | 0 | 0 |
| 2023-09 | 21 | -18.266667 | 0.253406 | 0.277778 | 2 | 0 | 0 |
| 2023-10 | 13 | -7.683333 | 0.432266 | 0.400000 | 0 | 0 | 0 |
| 2023-11 | 34 | -32.833333 | 0.210737 | 0.269663 | 1 | 0 | 0 |
| 2023-12 | 24 | -24.550000 | 0.127370 | 0.139535 | 0 | 0 | 0 |

### B_OPT2023_N6_W3_T2_SB2_TP10

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 263, entry dates 158, entry months 12; SKIP 2, EXCLUDED 5, exclusion share 0.018657; conditional FLAT CLOSED 249.
Net -159.000000 R; PF R / price 0.462353 / 0.439969; expectancy -0.604563 R; win rate 0.174905; average winner / loser 2.972464 / -1.388419 R.
Conditional CLOSED-only DD 159.000000 R; largest winner share 0.121892; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 21 | -21.600000 | 0.226730 | 0.170940 | 5 | 0 | 1 |
| 2023-02 | 28 | -17.333333 | 0.389671 | 0.359155 | 4 | 0 | 0 |
| 2023-03 | 29 | -11.733333 | 0.592593 | 0.650000 | 3 | 1 | 1 |
| 2023-04 | 26 | -12.666667 | 0.566952 | 0.543307 | 5 | 0 | 1 |
| 2023-05 | 21 | -14.283333 | 0.391767 | 0.522222 | 3 | 1 | 0 |
| 2023-06 | 21 | -4.400000 | 0.830116 | 0.607477 | 4 | 0 | 2 |
| 2023-07 | 13 | -2.133333 | 0.819209 | 0.762712 | 1 | 0 | 0 |
| 2023-08 | 12 | 8.483333 | 1.682306 | 1.271186 | 2 | 0 | 0 |
| 2023-09 | 21 | -18.266667 | 0.253406 | 0.277778 | 2 | 0 | 0 |
| 2023-10 | 13 | -7.683333 | 0.432266 | 0.400000 | 0 | 0 | 0 |
| 2023-11 | 34 | -32.833333 | 0.210737 | 0.269663 | 1 | 0 | 0 |
| 2023-12 | 24 | -24.550000 | 0.127370 | 0.139535 | 0 | 0 | 0 |

### B_OPT2023_N7_W3_T2_SB2_TP2

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 150, entry dates 103, entry months 12; SKIP 1, EXCLUDED 4, exclusion share 0.025974; conditional FLAT CLOSED 145.
Net -88.566667 R; PF R / price 0.449383 / 0.423680; expectancy -0.590444 R; win rate 0.180000; average winner / loser 2.677160 / -1.351681 R.
Conditional CLOSED-only DD 88.666667 R; largest winner share 0.046115; largest positive month share 0.618557. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 9 | -6.866667 | 0.304054 | 0.260870 | 5 | 0 | 1 |
| 2023-02 | 14 | -2.816667 | 0.766575 | 0.690909 | 4 | 0 | 1 |
| 2023-03 | 20 | -17.366667 | 0.256776 | 0.252427 | 3 | 1 | 0 |
| 2023-04 | 17 | -12.500000 | 0.347826 | 0.263158 | 5 | 0 | 1 |
| 2023-05 | 12 | -4.666667 | 0.635417 | 0.807018 | 3 | 0 | 0 |
| 2023-06 | 6 | 1.233333 | 1.270073 | 1.444444 | 4 | 0 | 1 |
| 2023-07 | 9 | 2.000000 | 1.272727 | 1.062500 | 1 | 0 | 0 |
| 2023-08 | 12 | -0.400000 | 0.958904 | 0.755556 | 2 | 0 | 0 |
| 2023-09 | 17 | -9.100000 | 0.495379 | 0.426966 | 2 | 0 | 0 |
| 2023-10 | 10 | -7.933333 | 0.342541 | 0.280000 | 0 | 0 | 0 |
| 2023-11 | 13 | -18.183333 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-12 | 11 | -11.966667 | 0.124390 | 0.166667 | 0 | 0 | 0 |

### B_OPT2023_N7_W3_T2_SB2_TP3

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 148, entry dates 102, entry months 12; SKIP 1, EXCLUDED 5, exclusion share 0.032680; conditional FLAT CLOSED 143.
Net -84.766667 R; PF R / price 0.481285 / 0.469846; expectancy -0.572748 R; win rate 0.155405; average winner / loser 3.419565 / -1.339481 R.
Conditional CLOSED-only DD 86.650000 R; largest winner share 0.063573; largest positive month share 0.551570. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 9 | -5.366667 | 0.456081 | 0.391304 | 5 | 0 | 1 |
| 2023-02 | 14 | -5.816667 | 0.571253 | 0.524590 | 4 | 0 | 1 |
| 2023-03 | 20 | -16.533333 | 0.292439 | 0.252427 | 3 | 1 | 0 |
| 2023-04 | 17 | -14.833333 | 0.252101 | 0.192308 | 5 | 0 | 1 |
| 2023-05 | 12 | -6.200000 | 0.563380 | 0.750000 | 3 | 0 | 0 |
| 2023-06 | 5 | -0.066667 | 0.985401 | 1.000000 | 4 | 0 | 2 |
| 2023-07 | 8 | 3.333333 | 1.454545 | 1.281250 | 1 | 0 | 0 |
| 2023-08 | 12 | 4.100000 | 1.469466 | 1.404762 | 2 | 0 | 0 |
| 2023-09 | 17 | -4.633333 | 0.743068 | 0.640449 | 2 | 0 | 0 |
| 2023-10 | 10 | -8.600000 | 0.287293 | 0.240000 | 0 | 0 | 0 |
| 2023-11 | 13 | -18.183333 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-12 | 11 | -11.966667 | 0.124390 | 0.166667 | 0 | 0 | 0 |

### B_OPT2023_N7_W3_T2_SB2_TP4

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 147, entry dates 102, entry months 12; SKIP 1, EXCLUDED 5, exclusion share 0.032895; conditional FLAT CLOSED 142.
Net -81.683333 R; PF R / price 0.499540 / 0.497191; expectancy -0.555669 R; win rate 0.156463; average winner / loser 3.544928 / -1.348898 R.
Conditional CLOSED-only DD 84.566667 R; largest winner share 0.081766; largest positive month share 0.541296. Positive / negative / zero months 3 / 9 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 9 | -5.866667 | 0.405405 | 0.347826 | 5 | 0 | 1 |
| 2023-02 | 14 | -4.316667 | 0.681818 | 0.622951 | 4 | 0 | 1 |
| 2023-03 | 20 | -21.200000 | 0.092725 | 0.116505 | 3 | 1 | 0 |
| 2023-04 | 16 | -17.633333 | 0.101868 | 0.077922 | 5 | 0 | 1 |
| 2023-05 | 12 | -6.866667 | 0.516432 | 0.687500 | 3 | 0 | 0 |
| 2023-06 | 5 | 1.433333 | 1.313869 | 1.333333 | 4 | 0 | 2 |
| 2023-07 | 8 | 4.583333 | 1.625000 | 1.437500 | 1 | 0 | 0 |
| 2023-08 | 12 | 7.100000 | 1.812977 | 1.690476 | 2 | 0 | 0 |
| 2023-09 | 17 | -0.166667 | 0.990758 | 0.853933 | 2 | 0 | 0 |
| 2023-10 | 10 | -8.600000 | 0.287293 | 0.240000 | 0 | 0 | 0 |
| 2023-11 | 13 | -18.183333 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-12 | 11 | -11.966667 | 0.124390 | 0.166667 | 0 | 0 | 0 |

### B_OPT2023_N7_W3_T2_SB2_TP5

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors.
CLOSED 147, entry dates 102, entry months 12; SKIP 1, EXCLUDED 5, exclusion share 0.032895; conditional FLAT CLOSED 142.
Net -89.933333 R; PF R / price 0.454012 / 0.452646; expectancy -0.611791 R; win rate 0.149660; average winner / loser 3.399242 / -1.350137 R.
Conditional CLOSED-only DD 91.033333 R; largest winner share 0.111433; largest positive month share 0.427184. Positive / negative / zero months 3 / 9 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 9 | -5.866667 | 0.405405 | 0.347826 | 5 | 0 | 1 |
| 2023-02 | 14 | -6.316667 | 0.534398 | 0.491803 | 4 | 0 | 1 |
| 2023-03 | 20 | -21.200000 | 0.092725 | 0.116505 | 3 | 1 | 0 |
| 2023-04 | 16 | -17.633333 | 0.101868 | 0.077922 | 5 | 0 | 1 |
| 2023-05 | 12 | -5.533333 | 0.610329 | 0.812500 | 3 | 0 | 0 |
| 2023-06 | 5 | 2.933333 | 1.642336 | 1.666667 | 4 | 0 | 2 |
| 2023-07 | 8 | 2.833333 | 1.386364 | 1.218750 | 1 | 0 | 0 |
| 2023-08 | 12 | 1.100000 | 1.107492 | 1.104167 | 2 | 0 | 0 |
| 2023-09 | 17 | -1.500000 | 0.916821 | 0.741573 | 2 | 0 | 0 |
| 2023-10 | 10 | -8.600000 | 0.287293 | 0.240000 | 0 | 0 | 0 |
| 2023-11 | 13 | -18.183333 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-12 | 11 | -11.966667 | 0.124390 | 0.166667 | 0 | 0 | 0 |

### B_OPT2023_N7_W3_T2_SB2_TP6

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors.
CLOSED 147, entry dates 102, entry months 12; SKIP 1, EXCLUDED 5, exclusion share 0.032895; conditional FLAT CLOSED 142.
Net -86.933333 R; PF R / price 0.472225 / 0.466574; expectancy -0.591383 R; win rate 0.149660; average winner / loser 3.535606 / -1.350137 R.
Conditional CLOSED-only DD 88.033333 R; largest winner share 0.128562; largest positive month share 0.449324. Positive / negative / zero months 3 / 9 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 9 | -5.866667 | 0.405405 | 0.347826 | 5 | 0 | 1 |
| 2023-02 | 14 | -6.316667 | 0.534398 | 0.491803 | 4 | 0 | 1 |
| 2023-03 | 20 | -21.200000 | 0.092725 | 0.116505 | 3 | 1 | 0 |
| 2023-04 | 16 | -17.633333 | 0.101868 | 0.077922 | 5 | 0 | 1 |
| 2023-05 | 12 | -4.200000 | 0.704225 | 0.937500 | 3 | 0 | 0 |
| 2023-06 | 5 | 4.433333 | 1.970803 | 2.000000 | 4 | 0 | 2 |
| 2023-07 | 8 | 2.833333 | 1.386364 | 1.218750 | 1 | 0 | 0 |
| 2023-08 | 12 | 2.600000 | 1.254072 | 1.229167 | 2 | 0 | 0 |
| 2023-09 | 17 | -2.833333 | 0.842884 | 0.629213 | 2 | 0 | 0 |
| 2023-10 | 10 | -8.600000 | 0.287293 | 0.240000 | 0 | 0 | 0 |
| 2023-11 | 13 | -18.183333 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-12 | 11 | -11.966667 | 0.124390 | 0.166667 | 0 | 0 | 0 |

### B_OPT2023_N7_W3_T2_SB2_TP7

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors.
CLOSED 147, entry dates 102, entry months 12; SKIP 1, EXCLUDED 5, exclusion share 0.032895; conditional FLAT CLOSED 142.
Net -80.933333 R; PF R / price 0.508651 / 0.501393; expectancy -0.550567 R; win rate 0.149660; average winner / loser 3.808333 / -1.350137 R.
Conditional CLOSED-only DD 82.033333 R; largest winner share 0.139248; largest positive month share 0.461140. Positive / negative / zero months 3 / 9 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 9 | -5.866667 | 0.405405 | 0.347826 | 5 | 0 | 1 |
| 2023-02 | 14 | -6.316667 | 0.534398 | 0.491803 | 4 | 0 | 1 |
| 2023-03 | 20 | -21.200000 | 0.092725 | 0.116505 | 3 | 1 | 0 |
| 2023-04 | 16 | -17.633333 | 0.101868 | 0.077922 | 5 | 0 | 1 |
| 2023-05 | 12 | -2.866667 | 0.798122 | 1.062500 | 3 | 0 | 0 |
| 2023-06 | 5 | 5.933333 | 2.299270 | 2.333333 | 4 | 0 | 2 |
| 2023-07 | 8 | 2.833333 | 1.386364 | 1.218750 | 1 | 0 | 0 |
| 2023-08 | 12 | 4.100000 | 1.400651 | 1.354167 | 2 | 0 | 0 |
| 2023-09 | 17 | -1.166667 | 0.935305 | 0.685393 | 2 | 0 | 0 |
| 2023-10 | 10 | -8.600000 | 0.287293 | 0.240000 | 0 | 0 | 0 |
| 2023-11 | 13 | -18.183333 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-12 | 11 | -11.966667 | 0.124390 | 0.166667 | 0 | 0 | 0 |

### B_OPT2023_N7_W3_T2_SB2_TP8

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors.
CLOSED 147, entry dates 102, entry months 12; SKIP 1, EXCLUDED 5, exclusion share 0.032895; conditional FLAT CLOSED 142.
Net -74.933333 R; PF R / price 0.545077 / 0.536212; expectancy -0.509751 R; win rate 0.149660; average winner / loser 4.081061 / -1.350137 R.
Conditional CLOSED-only DD 76.033333 R; largest winner share 0.148506; largest positive month share 0.454175. Positive / negative / zero months 4 / 8 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 9 | -5.866667 | 0.405405 | 0.347826 | 5 | 0 | 1 |
| 2023-02 | 14 | -6.316667 | 0.534398 | 0.491803 | 4 | 0 | 1 |
| 2023-03 | 20 | -21.200000 | 0.092725 | 0.116505 | 3 | 1 | 0 |
| 2023-04 | 16 | -17.633333 | 0.101868 | 0.077922 | 5 | 0 | 1 |
| 2023-05 | 12 | -1.533333 | 0.892019 | 1.187500 | 3 | 0 | 0 |
| 2023-06 | 5 | 7.433333 | 2.627737 | 2.666667 | 4 | 0 | 2 |
| 2023-07 | 8 | 2.833333 | 1.386364 | 1.218750 | 1 | 0 | 0 |
| 2023-08 | 12 | 5.600000 | 1.547231 | 1.479167 | 2 | 0 | 0 |
| 2023-09 | 17 | 0.500000 | 1.027726 | 0.741573 | 2 | 0 | 0 |
| 2023-10 | 10 | -8.600000 | 0.287293 | 0.240000 | 0 | 0 | 0 |
| 2023-11 | 13 | -18.183333 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-12 | 11 | -11.966667 | 0.124390 | 0.166667 | 0 | 0 | 0 |

### B_OPT2023_N7_W3_T2_SB2_TP9

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors.
CLOSED 147, entry dates 102, entry months 12; SKIP 1, EXCLUDED 5, exclusion share 0.032895; conditional FLAT CLOSED 142.
Net -70.183333 R; PF R / price 0.573915 / 0.564067; expectancy -0.477438 R; win rate 0.149660; average winner / loser 4.296970 / -1.350137 R.
Conditional CLOSED-only DD 71.283333 R; largest winner share 0.158674; largest positive month share 0.451559. Positive / negative / zero months 4 / 8 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 9 | -5.866667 | 0.405405 | 0.347826 | 5 | 0 | 1 |
| 2023-02 | 14 | -6.316667 | 0.534398 | 0.491803 | 4 | 0 | 1 |
| 2023-03 | 20 | -21.200000 | 0.092725 | 0.116505 | 3 | 1 | 0 |
| 2023-04 | 16 | -17.633333 | 0.101868 | 0.077922 | 5 | 0 | 1 |
| 2023-05 | 12 | -0.200000 | 0.985915 | 1.312500 | 3 | 0 | 0 |
| 2023-06 | 5 | 8.933333 | 2.956204 | 3.000000 | 4 | 0 | 2 |
| 2023-07 | 8 | 2.833333 | 1.386364 | 1.218750 | 1 | 0 | 0 |
| 2023-08 | 12 | 5.850000 | 1.571661 | 1.500000 | 2 | 0 | 0 |
| 2023-09 | 17 | 2.166667 | 1.120148 | 0.797753 | 2 | 0 | 0 |
| 2023-10 | 10 | -8.600000 | 0.287293 | 0.240000 | 0 | 0 | 0 |
| 2023-11 | 13 | -18.183333 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-12 | 11 | -11.966667 | 0.124390 | 0.166667 | 0 | 0 | 0 |

### B_OPT2023_N7_W3_T2_SB2_TP10

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors.
CLOSED 147, entry dates 102, entry months 12; SKIP 1, EXCLUDED 5, exclusion share 0.032895; conditional FLAT CLOSED 142.
Net -67.683333 R; PF R / price 0.589092 / 0.582173; expectancy -0.460431 R; win rate 0.149660; average winner / loser 4.410606 / -1.350137 R.
Conditional CLOSED-only DD 68.783333 R; largest winner share 0.154586; largest positive month share 0.472453. Positive / negative / zero months 5 / 7 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 9 | -5.866667 | 0.405405 | 0.347826 | 5 | 0 | 1 |
| 2023-02 | 14 | -6.316667 | 0.534398 | 0.491803 | 4 | 0 | 1 |
| 2023-03 | 20 | -21.200000 | 0.092725 | 0.116505 | 3 | 1 | 0 |
| 2023-04 | 16 | -17.633333 | 0.101868 | 0.077922 | 5 | 0 | 1 |
| 2023-05 | 12 | 1.133333 | 1.079812 | 1.437500 | 3 | 0 | 0 |
| 2023-06 | 5 | 10.433333 | 3.284672 | 3.333333 | 4 | 0 | 2 |
| 2023-07 | 8 | 2.833333 | 1.386364 | 1.218750 | 1 | 0 | 0 |
| 2023-08 | 12 | 5.850000 | 1.571661 | 1.500000 | 2 | 0 | 0 |
| 2023-09 | 17 | 1.833333 | 1.101664 | 0.786517 | 2 | 0 | 0 |
| 2023-10 | 10 | -8.600000 | 0.287293 | 0.240000 | 0 | 0 | 0 |
| 2023-11 | 13 | -18.183333 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-12 | 11 | -11.966667 | 0.124390 | 0.166667 | 0 | 0 | 0 |

### B_OPT2023_N8_W3_T2_SB2_TP2

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors.
CLOSED 93, entry dates 73, entry months 12; SKIP 0, EXCLUDED 4, exclusion share 0.041237; conditional FLAT CLOSED 87.
Net -52.033333 R; PF R / price 0.466507 / 0.479358; expectancy -0.559498 R; win rate 0.225806; average winner / loser 2.166667 / -1.373709 R.
Conditional CLOSED-only DD 55.300000 R; largest winner share 0.073260; largest positive month share 0.429630. Positive / negative / zero months 3 / 9 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 10 | -7.483333 | 0.280449 | 0.377778 | 5 | 0 | 1 |
| 2023-02 | 12 | -6.350000 | 0.496032 | 0.472727 | 4 | 0 | 1 |
| 2023-03 | 7 | -5.166667 | 0.351464 | 0.437500 | 3 | 0 | 1 |
| 2023-04 | 11 | -8.400000 | 0.284091 | 0.175439 | 5 | 0 | 0 |
| 2023-05 | 8 | -2.166667 | 0.728033 | 0.619048 | 3 | 0 | 0 |
| 2023-06 | 2 | -2.733333 | 0.000000 | 0.000000 | 4 | 0 | 1 |
| 2023-07 | 6 | 1.600000 | 1.369231 | 1.750000 | 1 | 0 | 0 |
| 2023-08 | 6 | 0.966667 | 1.192053 | 0.960000 | 2 | 0 | 0 |
| 2023-09 | 8 | -10.733333 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 4 | -4.333333 | 0.103448 | 0.187500 | 0 | 0 | 0 |
| 2023-11 | 13 | -9.166667 | 0.394273 | 0.450000 | 1 | 0 | 0 |
| 2023-12 | 6 | 1.933333 | 1.475410 | 1.173913 | 0 | 0 | 0 |

### B_OPT2023_N8_W3_T2_SB2_TP3

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors.
CLOSED 93, entry dates 73, entry months 12; SKIP 0, EXCLUDED 4, exclusion share 0.041237; conditional FLAT CLOSED 87.
Net -63.166667 R; PF R / price 0.381527 / 0.403509; expectancy -0.679211 R; win rate 0.182796; average winner / loser 2.292157 / -1.361778 R.
Conditional CLOSED-only DD 69.333333 R; largest winner share 0.115483; largest positive month share 0.369898. Positive / negative / zero months 3 / 9 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 10 | -7.816667 | 0.248397 | 0.333333 | 5 | 0 | 1 |
| 2023-02 | 12 | -4.850000 | 0.615079 | 0.581818 | 4 | 0 | 1 |
| 2023-03 | 7 | -8.166667 | 0.000000 | 0.000000 | 3 | 0 | 1 |
| 2023-04 | 11 | -11.066667 | 0.056818 | 0.035088 | 5 | 0 | 0 |
| 2023-05 | 8 | -8.666667 | 0.084507 | 0.083333 | 3 | 0 | 0 |
| 2023-06 | 2 | -2.733333 | 0.000000 | 0.000000 | 4 | 0 | 1 |
| 2023-07 | 6 | 4.266667 | 1.984615 | 2.550000 | 1 | 0 | 0 |
| 2023-08 | 6 | 3.966667 | 1.788079 | 1.440000 | 2 | 0 | 0 |
| 2023-09 | 8 | -10.733333 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 4 | -4.333333 | 0.103448 | 0.187500 | 0 | 0 | 0 |
| 2023-11 | 13 | -17.866667 | 0.009242 | 0.013699 | 1 | 0 | 0 |
| 2023-12 | 6 | 4.833333 | 2.188525 | 1.739130 | 0 | 0 | 0 |

### B_OPT2023_N8_W3_T2_SB2_TP4

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors.
CLOSED 93, entry dates 73, entry months 12; SKIP 0, EXCLUDED 4, exclusion share 0.041237; conditional FLAT CLOSED 87.
Net -55.933333 R; PF R / price 0.452350 / 0.469298; expectancy -0.601434 R; win rate 0.182796; average winner / loser 2.717647 / -1.361778 R.
Conditional CLOSED-only DD 65.000000 R; largest winner share 0.129870; largest positive month share 0.411348. Positive / negative / zero months 3 / 9 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 10 | -7.816667 | 0.248397 | 0.333333 | 5 | 0 | 1 |
| 2023-02 | 12 | -3.350000 | 0.734127 | 0.690909 | 4 | 0 | 1 |
| 2023-03 | 7 | -8.166667 | 0.000000 | 0.000000 | 3 | 0 | 1 |
| 2023-04 | 11 | -11.066667 | 0.056818 | 0.035088 | 5 | 0 | 0 |
| 2023-05 | 8 | -8.666667 | 0.084507 | 0.083333 | 3 | 0 | 0 |
| 2023-06 | 2 | -2.733333 | 0.000000 | 0.000000 | 4 | 0 | 1 |
| 2023-07 | 6 | 4.100000 | 1.946154 | 2.500000 | 1 | 0 | 0 |
| 2023-08 | 6 | 6.966667 | 2.384106 | 1.920000 | 2 | 0 | 0 |
| 2023-09 | 8 | -10.733333 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 4 | -4.333333 | 0.103448 | 0.187500 | 0 | 0 | 0 |
| 2023-11 | 13 | -17.866667 | 0.009242 | 0.013699 | 1 | 0 | 0 |
| 2023-12 | 6 | 7.733333 | 2.901639 | 2.304348 | 0 | 0 | 0 |

### B_OPT2023_N8_W3_T2_SB2_TP5

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 93, entry dates 73, entry months 12; SKIP 0, EXCLUDED 4, exclusion share 0.041237; conditional FLAT CLOSED 87.
Net -63.533333 R; PF R / price 0.386941 / 0.402597; expectancy -0.683154 R; win rate 0.172043; average winner / loser 2.506250 / -1.363596 R.
Conditional CLOSED-only DD 75.500000 R; largest winner share 0.187032; largest positive month share 0.805556. Positive / negative / zero months 3 / 9 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 10 | -7.816667 | 0.248397 | 0.333333 | 5 | 0 | 1 |
| 2023-02 | 12 | -5.350000 | 0.575397 | 0.545455 | 4 | 0 | 1 |
| 2023-03 | 7 | -8.166667 | 0.000000 | 0.000000 | 3 | 0 | 1 |
| 2023-04 | 11 | -11.066667 | 0.056818 | 0.035088 | 5 | 0 | 0 |
| 2023-05 | 8 | -8.666667 | 0.084507 | 0.083333 | 3 | 0 | 0 |
| 2023-06 | 2 | -2.733333 | 0.000000 | 0.000000 | 4 | 0 | 1 |
| 2023-07 | 6 | 1.600000 | 1.369231 | 1.750000 | 1 | 0 | 0 |
| 2023-08 | 6 | 0.966667 | 1.147959 | 0.967742 | 2 | 0 | 0 |
| 2023-09 | 8 | -10.733333 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 4 | -4.333333 | 0.103448 | 0.187500 | 0 | 0 | 0 |
| 2023-11 | 13 | -17.866667 | 0.009242 | 0.013699 | 1 | 0 | 0 |
| 2023-12 | 6 | 10.633333 | 3.614754 | 2.869565 | 0 | 0 | 0 |

### B_OPT2023_N8_W3_T2_SB2_TP6

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 93, entry dates 73, entry months 12; SKIP 0, EXCLUDED 4, exclusion share 0.041237; conditional FLAT CLOSED 87.
Net -62.383333 R; PF R / price 0.398038 / 0.415584; expectancy -0.670789 R; win rate 0.172043; average winner / loser 2.578125 / -1.363596 R.
Conditional CLOSED-only DD 74.000000 R; largest winner share 0.218182; largest positive month share 0.716609. Positive / negative / zero months 3 / 9 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 10 | -7.816667 | 0.248397 | 0.333333 | 5 | 0 | 1 |
| 2023-02 | 12 | -5.350000 | 0.575397 | 0.545455 | 4 | 0 | 1 |
| 2023-03 | 7 | -8.166667 | 0.000000 | 0.000000 | 3 | 0 | 1 |
| 2023-04 | 11 | -11.066667 | 0.056818 | 0.035088 | 5 | 0 | 0 |
| 2023-05 | 8 | -8.666667 | 0.084507 | 0.083333 | 3 | 0 | 0 |
| 2023-06 | 2 | -2.733333 | 0.000000 | 0.000000 | 4 | 0 | 1 |
| 2023-07 | 6 | 1.600000 | 1.369231 | 1.750000 | 1 | 0 | 0 |
| 2023-08 | 6 | 2.466667 | 1.377551 | 1.161290 | 2 | 0 | 0 |
| 2023-09 | 8 | -10.733333 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 4 | -4.333333 | 0.103448 | 0.187500 | 0 | 0 | 0 |
| 2023-11 | 13 | -17.866667 | 0.009242 | 0.013699 | 1 | 0 | 0 |
| 2023-12 | 6 | 10.283333 | 3.528689 | 2.869565 | 0 | 0 | 0 |

### B_OPT2023_N8_W3_T2_SB2_TP7

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 93, entry dates 73, entry months 12; SKIP 0, EXCLUDED 4, exclusion share 0.041237; conditional FLAT CLOSED 87.
Net -59.483333 R; PF R / price 0.426021 / 0.443723; expectancy -0.639606 R; win rate 0.172043; average winner / loser 2.759375 / -1.363596 R.
Conditional CLOSED-only DD 72.500000 R; largest winner share 0.237826; largest positive month share 0.677295. Positive / negative / zero months 3 / 9 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 10 | -7.816667 | 0.248397 | 0.333333 | 5 | 0 | 1 |
| 2023-02 | 12 | -5.350000 | 0.575397 | 0.545455 | 4 | 0 | 1 |
| 2023-03 | 7 | -8.166667 | 0.000000 | 0.000000 | 3 | 0 | 1 |
| 2023-04 | 11 | -11.066667 | 0.056818 | 0.035088 | 5 | 0 | 0 |
| 2023-05 | 8 | -8.666667 | 0.084507 | 0.083333 | 3 | 0 | 0 |
| 2023-06 | 2 | -2.733333 | 0.000000 | 0.000000 | 4 | 0 | 1 |
| 2023-07 | 6 | 1.600000 | 1.369231 | 1.750000 | 1 | 0 | 0 |
| 2023-08 | 6 | 3.966667 | 1.607143 | 1.354839 | 2 | 0 | 0 |
| 2023-09 | 8 | -10.733333 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 4 | -4.333333 | 0.103448 | 0.187500 | 0 | 0 | 0 |
| 2023-11 | 13 | -17.866667 | 0.009242 | 0.013699 | 1 | 0 | 0 |
| 2023-12 | 6 | 11.683333 | 3.872951 | 3.173913 | 0 | 0 | 0 |

### B_OPT2023_N8_W3_T2_SB2_TP8

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors.
CLOSED 93, entry dates 73, entry months 12; SKIP 0, EXCLUDED 4, exclusion share 0.041237; conditional FLAT CLOSED 87.
Net -56.583333 R; PF R / price 0.454005 / 0.471861; expectancy -0.608423 R; win rate 0.172043; average winner / loser 2.940625 / -1.363596 R.
Conditional CLOSED-only DD 71.000000 R; largest winner share 0.255048; largest positive month share 0.649297. Positive / negative / zero months 3 / 9 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 10 | -7.816667 | 0.248397 | 0.333333 | 5 | 0 | 1 |
| 2023-02 | 12 | -5.350000 | 0.575397 | 0.545455 | 4 | 0 | 1 |
| 2023-03 | 7 | -8.166667 | 0.000000 | 0.000000 | 3 | 0 | 1 |
| 2023-04 | 11 | -11.066667 | 0.056818 | 0.035088 | 5 | 0 | 0 |
| 2023-05 | 8 | -8.666667 | 0.084507 | 0.083333 | 3 | 0 | 0 |
| 2023-06 | 2 | -2.733333 | 0.000000 | 0.000000 | 4 | 0 | 1 |
| 2023-07 | 6 | 1.600000 | 1.369231 | 1.750000 | 1 | 0 | 0 |
| 2023-08 | 6 | 5.466667 | 1.836735 | 1.548387 | 2 | 0 | 0 |
| 2023-09 | 8 | -10.733333 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 4 | -4.333333 | 0.103448 | 0.187500 | 0 | 0 | 0 |
| 2023-11 | 13 | -17.866667 | 0.009242 | 0.013699 | 1 | 0 | 0 |
| 2023-12 | 6 | 13.083333 | 4.217213 | 3.478261 | 0 | 0 | 0 |

### B_OPT2023_N8_W3_T2_SB2_TP9

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors.
CLOSED 93, entry dates 73, entry months 12; SKIP 0, EXCLUDED 4, exclusion share 0.041237; conditional FLAT CLOSED 87.
Net -54.933333 R; PF R / price 0.469926 / 0.489177; expectancy -0.590681 R; win rate 0.172043; average winner / loser 3.043750 / -1.363596 R.
Conditional CLOSED-only DD 70.750000 R; largest winner share 0.258727; largest positive month share 0.664373. Positive / negative / zero months 3 / 9 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 10 | -7.816667 | 0.248397 | 0.333333 | 5 | 0 | 1 |
| 2023-02 | 12 | -5.350000 | 0.575397 | 0.545455 | 4 | 0 | 1 |
| 2023-03 | 7 | -8.166667 | 0.000000 | 0.000000 | 3 | 0 | 1 |
| 2023-04 | 11 | -11.066667 | 0.056818 | 0.035088 | 5 | 0 | 0 |
| 2023-05 | 8 | -8.666667 | 0.084507 | 0.083333 | 3 | 0 | 0 |
| 2023-06 | 2 | -2.733333 | 0.000000 | 0.000000 | 4 | 0 | 1 |
| 2023-07 | 6 | 1.600000 | 1.369231 | 1.750000 | 1 | 0 | 0 |
| 2023-08 | 6 | 5.716667 | 1.875000 | 1.580645 | 2 | 0 | 0 |
| 2023-09 | 8 | -10.733333 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 4 | -4.333333 | 0.103448 | 0.187500 | 0 | 0 | 0 |
| 2023-11 | 13 | -17.866667 | 0.009242 | 0.013699 | 1 | 0 | 0 |
| 2023-12 | 6 | 14.483333 | 4.561475 | 3.782609 | 0 | 0 | 0 |

### B_OPT2023_N8_W3_T2_SB2_TP10

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors.
CLOSED 93, entry dates 73, entry months 12; SKIP 0, EXCLUDED 4, exclusion share 0.041237; conditional FLAT CLOSED 87.
Net -53.533333 R; PF R / price 0.483435 / 0.504329; expectancy -0.575627 R; win rate 0.172043; average winner / loser 3.131250 / -1.363596 R.
Conditional CLOSED-only DD 70.750000 R; largest winner share 0.279441; largest positive month share 0.684626. Positive / negative / zero months 3 / 9 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 10 | -7.816667 | 0.248397 | 0.333333 | 5 | 0 | 1 |
| 2023-02 | 12 | -5.350000 | 0.575397 | 0.545455 | 4 | 0 | 1 |
| 2023-03 | 7 | -8.166667 | 0.000000 | 0.000000 | 3 | 0 | 1 |
| 2023-04 | 11 | -11.066667 | 0.056818 | 0.035088 | 5 | 0 | 0 |
| 2023-05 | 8 | -8.666667 | 0.084507 | 0.083333 | 3 | 0 | 0 |
| 2023-06 | 2 | -2.733333 | 0.000000 | 0.000000 | 4 | 0 | 1 |
| 2023-07 | 6 | 1.600000 | 1.369231 | 1.750000 | 1 | 0 | 0 |
| 2023-08 | 6 | 5.716667 | 1.875000 | 1.580645 | 2 | 0 | 0 |
| 2023-09 | 8 | -10.733333 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 4 | -4.333333 | 0.103448 | 0.187500 | 0 | 0 | 0 |
| 2023-11 | 13 | -17.866667 | 0.009242 | 0.013699 | 1 | 0 | 0 |
| 2023-12 | 6 | 15.883333 | 4.905738 | 4.086957 | 0 | 0 | 0 |

### B_OPT2023_N9_W3_T2_SB2_TP2

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 59, entry dates 48, entry months 12; SKIP 1, EXCLUDED 1, exclusion share 0.016667; conditional FLAT CLOSED 40.
Net -45.233333 R; PF R / price 0.355956 / 0.332258; expectancy -0.766667 R; win rate 0.169492; average winner / loser 2.500000 / -1.433333 R.
Conditional CLOSED-only DD 46.833333 R; largest winner share 0.120000; largest positive month share 0.538117. Positive / negative / zero months 3 / 9 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 7 | -11.233333 | 0.000000 | 0.000000 | 5 | 1 | 0 |
| 2023-02 | 8 | 1.616667 | 1.226636 | 1.029412 | 4 | 0 | 0 |
| 2023-03 | 4 | -1.300000 | 0.697674 | 0.600000 | 3 | 0 | 1 |
| 2023-04 | 6 | -6.883333 | 0.035047 | 0.029412 | 5 | 0 | 0 |
| 2023-05 | 4 | -6.066667 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-06 | 3 | -0.533333 | 0.804878 | 0.733333 | 4 | 0 | 0 |
| 2023-07 | 4 | -5.166667 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-08 | 3 | 0.100000 | 1.034483 | 0.923077 | 2 | 0 | 0 |
| 2023-09 | 5 | -7.400000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 1 | 2.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |
| 2023-11 | 8 | -6.500000 | 0.301075 | 0.350000 | 1 | 0 | 0 |
| 2023-12 | 6 | -3.866667 | 0.436893 | 0.324324 | 0 | 0 | 0 |

### B_OPT2023_N9_W3_T2_SB2_TP3

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors.
CLOSED 59, entry dates 48, entry months 12; SKIP 1, EXCLUDED 1, exclusion share 0.016667; conditional FLAT CLOSED 40.
Net -49.933333 R; PF R / price 0.310154 / 0.281250; expectancy -0.846328 R; win rate 0.135593; average winner / loser 2.806250 / -1.419281 R.
Conditional CLOSED-only DD 53.033333 R; largest winner share 0.200445; largest positive month share 0.491803. Positive / negative / zero months 3 / 9 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 7 | -11.233333 | 0.000000 | 0.000000 | 5 | 1 | 0 |
| 2023-02 | 8 | 1.866667 | 1.261682 | 1.058824 | 4 | 0 | 0 |
| 2023-03 | 4 | 0.200000 | 1.046512 | 0.900000 | 3 | 0 | 1 |
| 2023-04 | 6 | -6.883333 | 0.035047 | 0.029412 | 5 | 0 | 0 |
| 2023-05 | 4 | -6.066667 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-06 | 3 | -0.533333 | 0.804878 | 0.733333 | 4 | 0 | 0 |
| 2023-07 | 4 | -5.166667 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-08 | 3 | -3.650000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 5 | -7.400000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 1 | 2.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |
| 2023-11 | 8 | -10.700000 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-12 | 6 | -2.366667 | 0.655340 | 0.486486 | 0 | 0 | 0 |

### B_OPT2023_N9_W3_T2_SB2_TP4

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors.
CLOSED 59, entry dates 48, entry months 12; SKIP 1, EXCLUDED 1, exclusion share 0.016667; conditional FLAT CLOSED 40.
Net -51.433333 R; PF R / price 0.289431 / 0.262500; expectancy -0.871751 R; win rate 0.118644; average winner / loser 2.992857 / -1.419281 R.
Conditional CLOSED-only DD 56.033333 R; largest winner share 0.286396; largest positive month share 0.627329. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 7 | -11.233333 | 0.000000 | 0.000000 | 5 | 1 | 0 |
| 2023-02 | 8 | 3.366667 | 1.471963 | 1.235294 | 4 | 0 | 0 |
| 2023-03 | 4 | -4.300000 | 0.000000 | 0.000000 | 3 | 0 | 1 |
| 2023-04 | 6 | -6.883333 | 0.035047 | 0.029412 | 5 | 0 | 0 |
| 2023-05 | 4 | -6.066667 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-06 | 3 | -0.533333 | 0.804878 | 0.733333 | 4 | 0 | 0 |
| 2023-07 | 4 | -5.166667 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-08 | 3 | -3.650000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 5 | -7.400000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 1 | 2.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |
| 2023-11 | 8 | -10.700000 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-12 | 6 | -0.866667 | 0.873786 | 0.648649 | 0 | 0 | 0 |

### B_OPT2023_N9_W3_T2_SB2_TP5

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|neighbors.
CLOSED 59, entry dates 48, entry months 12; SKIP 1, EXCLUDED 1, exclusion share 0.016667; conditional FLAT CLOSED 40.
Net -51.933333 R; PF R / price 0.282524 / 0.256250; expectancy -0.880226 R; win rate 0.118644; average winner / loser 2.921429 / -1.419281 R.
Conditional CLOSED-only DD 58.033333 R; largest winner share 0.366748; largest positive month share 0.500000. Positive / negative / zero months 3 / 9 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 7 | -11.233333 | 0.000000 | 0.000000 | 5 | 1 | 0 |
| 2023-02 | 8 | 1.366667 | 1.191589 | 1.000000 | 4 | 0 | 0 |
| 2023-03 | 4 | -4.300000 | 0.000000 | 0.000000 | 3 | 0 | 1 |
| 2023-04 | 6 | -6.883333 | 0.035047 | 0.029412 | 5 | 0 | 0 |
| 2023-05 | 4 | -6.066667 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-06 | 3 | -0.533333 | 0.804878 | 0.733333 | 4 | 0 | 0 |
| 2023-07 | 4 | -5.166667 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-08 | 3 | -3.650000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 5 | -7.400000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 1 | 2.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |
| 2023-11 | 8 | -10.700000 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-12 | 6 | 0.633333 | 1.092233 | 0.810811 | 0 | 0 | 0 |

### B_OPT2023_N9_W3_T2_SB2_TP6

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors.
CLOSED 59, entry dates 48, entry months 12; SKIP 1, EXCLUDED 1, exclusion share 0.016667; conditional FLAT CLOSED 40.
Net -53.683333 R; PF R / price 0.258347 / 0.234375; expectancy -0.909887 R; win rate 0.118644; average winner / loser 2.671429 / -1.419281 R.
Conditional CLOSED-only DD 58.033333 R; largest winner share 0.307487; largest positive month share 0.594059. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 7 | -11.233333 | 0.000000 | 0.000000 | 5 | 1 | 0 |
| 2023-02 | 8 | 1.366667 | 1.191589 | 1.000000 | 4 | 0 | 0 |
| 2023-03 | 4 | -4.300000 | 0.000000 | 0.000000 | 3 | 0 | 1 |
| 2023-04 | 6 | -6.883333 | 0.035047 | 0.029412 | 5 | 0 | 0 |
| 2023-05 | 4 | -6.066667 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-06 | 3 | -0.533333 | 0.804878 | 0.733333 | 4 | 0 | 0 |
| 2023-07 | 4 | -5.166667 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-08 | 3 | -3.650000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 5 | -7.400000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 1 | 2.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |
| 2023-11 | 8 | -10.700000 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-12 | 6 | -1.116667 | 0.837379 | 0.621622 | 0 | 0 | 0 |

### B_OPT2023_N9_W3_T2_SB2_TP7

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors.
CLOSED 59, entry dates 48, entry months 12; SKIP 1, EXCLUDED 1, exclusion share 0.016667; conditional FLAT CLOSED 40.
Net -53.683333 R; PF R / price 0.258347 / 0.234375; expectancy -0.909887 R; win rate 0.118644; average winner / loser 2.671429 / -1.419281 R.
Conditional CLOSED-only DD 58.033333 R; largest winner share 0.307487; largest positive month share 0.594059. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 7 | -11.233333 | 0.000000 | 0.000000 | 5 | 1 | 0 |
| 2023-02 | 8 | 1.366667 | 1.191589 | 1.000000 | 4 | 0 | 0 |
| 2023-03 | 4 | -4.300000 | 0.000000 | 0.000000 | 3 | 0 | 1 |
| 2023-04 | 6 | -6.883333 | 0.035047 | 0.029412 | 5 | 0 | 0 |
| 2023-05 | 4 | -6.066667 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-06 | 3 | -0.533333 | 0.804878 | 0.733333 | 4 | 0 | 0 |
| 2023-07 | 4 | -5.166667 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-08 | 3 | -3.650000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 5 | -7.400000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 1 | 2.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |
| 2023-11 | 8 | -10.700000 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-12 | 6 | -1.116667 | 0.837379 | 0.621622 | 0 | 0 | 0 |

### B_OPT2023_N9_W3_T2_SB2_TP8

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors.
CLOSED 59, entry dates 48, entry months 12; SKIP 1, EXCLUDED 1, exclusion share 0.016667; conditional FLAT CLOSED 40.
Net -53.683333 R; PF R / price 0.258347 / 0.234375; expectancy -0.909887 R; win rate 0.118644; average winner / loser 2.671429 / -1.419281 R.
Conditional CLOSED-only DD 58.033333 R; largest winner share 0.307487; largest positive month share 0.594059. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 7 | -11.233333 | 0.000000 | 0.000000 | 5 | 1 | 0 |
| 2023-02 | 8 | 1.366667 | 1.191589 | 1.000000 | 4 | 0 | 0 |
| 2023-03 | 4 | -4.300000 | 0.000000 | 0.000000 | 3 | 0 | 1 |
| 2023-04 | 6 | -6.883333 | 0.035047 | 0.029412 | 5 | 0 | 0 |
| 2023-05 | 4 | -6.066667 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-06 | 3 | -0.533333 | 0.804878 | 0.733333 | 4 | 0 | 0 |
| 2023-07 | 4 | -5.166667 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-08 | 3 | -3.650000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 5 | -7.400000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 1 | 2.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |
| 2023-11 | 8 | -10.700000 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-12 | 6 | -1.116667 | 0.837379 | 0.621622 | 0 | 0 | 0 |

### B_OPT2023_N9_W3_T2_SB2_TP9

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors.
CLOSED 59, entry dates 48, entry months 12; SKIP 1, EXCLUDED 1, exclusion share 0.016667; conditional FLAT CLOSED 40.
Net -53.683333 R; PF R / price 0.258347 / 0.234375; expectancy -0.909887 R; win rate 0.118644; average winner / loser 2.671429 / -1.419281 R.
Conditional CLOSED-only DD 58.033333 R; largest winner share 0.307487; largest positive month share 0.594059. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 7 | -11.233333 | 0.000000 | 0.000000 | 5 | 1 | 0 |
| 2023-02 | 8 | 1.366667 | 1.191589 | 1.000000 | 4 | 0 | 0 |
| 2023-03 | 4 | -4.300000 | 0.000000 | 0.000000 | 3 | 0 | 1 |
| 2023-04 | 6 | -6.883333 | 0.035047 | 0.029412 | 5 | 0 | 0 |
| 2023-05 | 4 | -6.066667 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-06 | 3 | -0.533333 | 0.804878 | 0.733333 | 4 | 0 | 0 |
| 2023-07 | 4 | -5.166667 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-08 | 3 | -3.650000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 5 | -7.400000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 1 | 2.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |
| 2023-11 | 8 | -10.700000 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-12 | 6 | -1.116667 | 0.837379 | 0.621622 | 0 | 0 | 0 |

### B_OPT2023_N9_W3_T2_SB2_TP10

Status: **INSUFFICIENT_SAMPLE**. Failures: sample|PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors.
CLOSED 59, entry dates 48, entry months 12; SKIP 1, EXCLUDED 1, exclusion share 0.016667; conditional FLAT CLOSED 40.
Net -53.683333 R; PF R / price 0.258347 / 0.234375; expectancy -0.909887 R; win rate 0.118644; average winner / loser 2.671429 / -1.419281 R.
Conditional CLOSED-only DD 58.033333 R; largest winner share 0.307487; largest positive month share 0.594059. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 7 | -11.233333 | 0.000000 | 0.000000 | 5 | 1 | 0 |
| 2023-02 | 8 | 1.366667 | 1.191589 | 1.000000 | 4 | 0 | 0 |
| 2023-03 | 4 | -4.300000 | 0.000000 | 0.000000 | 3 | 0 | 1 |
| 2023-04 | 6 | -6.883333 | 0.035047 | 0.029412 | 5 | 0 | 0 |
| 2023-05 | 4 | -6.066667 | 0.000000 | 0.000000 | 3 | 0 | 0 |
| 2023-06 | 3 | -0.533333 | 0.804878 | 0.733333 | 4 | 0 | 0 |
| 2023-07 | 4 | -5.166667 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-08 | 3 | -3.650000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-09 | 5 | -7.400000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-10 | 1 | 2.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |
| 2023-11 | 8 | -10.700000 | 0.000000 | 0.000000 | 1 | 0 | 0 |
| 2023-12 | 6 | -1.116667 | 0.837379 | 0.621622 | 0 | 0 | 0 |

## CNYRUBF

NO QUALIFYING OPTIMIZATION CANDIDATE

### B_OPT2023_N4_W2_T2_SB1_TP2

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 307, entry dates 143, entry months 12; SKIP 26, EXCLUDED 108, exclusion share 0.260241; conditional FLAT CLOSED 307.
Net -182.000000 R; PF R / price 0.389023 / 0.332346; expectancy -0.592834 R; win rate 0.221498; average winner / loser 1.704167 / -1.306506 R.
Conditional CLOSED-only DD 182.000000 R; largest winner share 0.028765; largest positive month share 0.638796. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 33 | -31.050000 | 0.120397 | 0.133858 | 18 | 1 | 12 |
| 2023-02 | 20 | -11.333333 | 0.222857 | 0.244444 | 18 | 5 | 14 |
| 2023-03 | 13 | -12.766667 | 0.094563 | 0.085106 | 22 | 2 | 14 |
| 2023-04 | 18 | 3.183333 | 1.260218 | 1.159091 | 18 | 4 | 12 |
| 2023-05 | 30 | -16.250000 | 0.468665 | 0.484848 | 21 | 3 | 14 |
| 2023-06 | 17 | -19.166667 | 0.012876 | 0.016129 | 20 | 5 | 15 |
| 2023-07 | 35 | -30.316667 | 0.182472 | 0.205128 | 19 | 3 | 11 |
| 2023-08 | 56 | -21.616667 | 0.530583 | 0.515924 | 14 | 2 | 6 |
| 2023-09 | 32 | -28.000000 | 0.168317 | 0.185996 | 14 | 1 | 8 |
| 2023-10 | 14 | 1.800000 | 1.148556 | 0.960784 | 2 | 0 | 1 |
| 2023-11 | 26 | -7.150000 | 0.741098 | 0.750000 | 6 | 0 | 1 |
| 2023-12 | 13 | -9.333333 | 0.383260 | 0.481481 | 0 | 0 | 0 |

### B_OPT2023_N4_W2_T2_SB1_TP3

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 303, entry dates 143, entry months 12; SKIP 26, EXCLUDED 109, exclusion share 0.264563; conditional FLAT CLOSED 303.
Net -197.650000 R; PF R / price 0.347510 / 0.316865; expectancy -0.652310 R; win rate 0.204620; average winner / loser 1.697849 / -1.317029 R.
Conditional CLOSED-only DD 197.650000 R; largest winner share 0.047498; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 12 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 33 | -29.550000 | 0.162890 | 0.181102 | 18 | 1 | 12 |
| 2023-02 | 20 | -11.333333 | 0.222857 | 0.244444 | 18 | 5 | 14 |
| 2023-03 | 13 | -12.766667 | 0.094563 | 0.085106 | 22 | 2 | 14 |
| 2023-04 | 17 | -0.150000 | 0.987738 | 0.931818 | 18 | 4 | 13 |
| 2023-05 | 30 | -17.250000 | 0.435967 | 0.454545 | 21 | 3 | 14 |
| 2023-06 | 17 | -19.166667 | 0.012876 | 0.016129 | 20 | 5 | 15 |
| 2023-07 | 35 | -30.316667 | 0.182472 | 0.205128 | 19 | 3 | 11 |
| 2023-08 | 55 | -20.900000 | 0.538122 | 0.516340 | 14 | 2 | 6 |
| 2023-09 | 31 | -28.333333 | 0.150000 | 0.165929 | 14 | 1 | 8 |
| 2023-10 | 14 | -3.866667 | 0.744212 | 0.555556 | 2 | 0 | 1 |
| 2023-11 | 25 | -11.583333 | 0.604439 | 0.669725 | 6 | 0 | 1 |
| 2023-12 | 13 | -12.433333 | 0.252505 | 0.350000 | 0 | 0 | 0 |

### B_OPT2023_N4_W2_T2_SB1_TP4

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 302, entry dates 143, entry months 12; SKIP 26, EXCLUDED 109, exclusion share 0.265207; conditional FLAT CLOSED 302.
Net -193.350000 R; PF R / price 0.360862 / 0.311741; expectancy -0.640232 R; win rate 0.205298; average winner / loser 1.760753 / -1.321033 R.
Conditional CLOSED-only DD 193.350000 R; largest winner share 0.061069; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 12 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 33 | -32.300000 | 0.084986 | 0.094488 | 18 | 1 | 12 |
| 2023-02 | 20 | -11.333333 | 0.222857 | 0.244444 | 18 | 5 | 14 |
| 2023-03 | 13 | -12.766667 | 0.094563 | 0.085106 | 22 | 2 | 14 |
| 2023-04 | 17 | -0.150000 | 0.987738 | 0.931818 | 18 | 4 | 13 |
| 2023-05 | 30 | -17.250000 | 0.435967 | 0.454545 | 21 | 3 | 14 |
| 2023-06 | 17 | -19.166667 | 0.012876 | 0.016129 | 20 | 5 | 15 |
| 2023-07 | 35 | -30.316667 | 0.182472 | 0.205128 | 19 | 3 | 11 |
| 2023-08 | 55 | -19.233333 | 0.574954 | 0.549020 | 14 | 2 | 6 |
| 2023-09 | 31 | -28.333333 | 0.150000 | 0.165929 | 14 | 1 | 8 |
| 2023-10 | 14 | -0.533333 | 0.964719 | 0.714286 | 2 | 0 | 1 |
| 2023-11 | 24 | -10.933333 | 0.621466 | 0.691589 | 6 | 0 | 1 |
| 2023-12 | 13 | -11.033333 | 0.336673 | 0.466667 | 0 | 0 | 0 |

### B_OPT2023_N4_W2_T2_SB1_TP5

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 302, entry dates 143, entry months 12; SKIP 26, EXCLUDED 109, exclusion share 0.265207; conditional FLAT CLOSED 302.
Net -194.616667 R; PF R / price 0.359849 / 0.316955; expectancy -0.644426 R; win rate 0.201987; average winner / loser 1.793443 / -1.321812 R.
Conditional CLOSED-only DD 194.616667 R; largest winner share 0.076173; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 33 | -32.300000 | 0.084986 | 0.094488 | 18 | 1 | 12 |
| 2023-02 | 20 | -11.333333 | 0.222857 | 0.244444 | 18 | 5 | 14 |
| 2023-03 | 13 | -12.766667 | 0.094563 | 0.085106 | 22 | 2 | 14 |
| 2023-04 | 17 | -0.150000 | 0.987738 | 0.931818 | 18 | 4 | 13 |
| 2023-05 | 30 | -17.250000 | 0.435967 | 0.454545 | 21 | 3 | 14 |
| 2023-06 | 17 | -19.166667 | 0.012876 | 0.016129 | 20 | 5 | 15 |
| 2023-07 | 35 | -30.316667 | 0.182472 | 0.205128 | 19 | 3 | 11 |
| 2023-08 | 55 | -17.566667 | 0.611786 | 0.581699 | 14 | 2 | 6 |
| 2023-09 | 31 | -28.333333 | 0.150000 | 0.165929 | 14 | 1 | 8 |
| 2023-10 | 14 | 1.133333 | 1.074972 | 0.793651 | 2 | 0 | 1 |
| 2023-11 | 24 | -16.933333 | 0.442677 | 0.495575 | 6 | 0 | 1 |
| 2023-12 | 13 | -9.633333 | 0.420842 | 0.583333 | 0 | 0 | 0 |

### B_OPT2023_N4_W2_T2_SB1_TP6

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 302, entry dates 143, entry months 12; SKIP 26, EXCLUDED 109, exclusion share 0.265207; conditional FLAT CLOSED 302.
Net -192.633333 R; PF R / price 0.366372 / 0.323267; expectancy -0.637859 R; win rate 0.201987; average winner / loser 1.825956 / -1.321812 R.
Conditional CLOSED-only DD 192.633333 R; largest winner share 0.089780; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 33 | -32.300000 | 0.084986 | 0.094488 | 18 | 1 | 12 |
| 2023-02 | 20 | -11.333333 | 0.222857 | 0.244444 | 18 | 5 | 14 |
| 2023-03 | 13 | -12.766667 | 0.094563 | 0.085106 | 22 | 2 | 14 |
| 2023-04 | 17 | -0.150000 | 0.987738 | 0.931818 | 18 | 4 | 13 |
| 2023-05 | 30 | -17.250000 | 0.435967 | 0.454545 | 21 | 3 | 14 |
| 2023-06 | 17 | -19.166667 | 0.012876 | 0.016129 | 20 | 5 | 15 |
| 2023-07 | 35 | -30.316667 | 0.182472 | 0.205128 | 19 | 3 | 11 |
| 2023-08 | 55 | -15.900000 | 0.648619 | 0.614379 | 14 | 2 | 6 |
| 2023-09 | 31 | -28.333333 | 0.150000 | 0.165929 | 14 | 1 | 8 |
| 2023-10 | 14 | 2.800000 | 1.185226 | 0.873016 | 2 | 0 | 1 |
| 2023-11 | 24 | -19.683333 | 0.352167 | 0.398230 | 6 | 0 | 1 |
| 2023-12 | 13 | -8.233333 | 0.505010 | 0.700000 | 0 | 0 | 0 |

### B_OPT2023_N4_W2_T2_SB1_TP7

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 302, entry dates 143, entry months 12; SKIP 26, EXCLUDED 109, exclusion share 0.265207; conditional FLAT CLOSED 302.
Net -201.233333 R; PF R / price 0.341693 / 0.326407; expectancy -0.666336 R; win rate 0.198675; average winner / loser 1.740833 / -1.323304 R.
Conditional CLOSED-only DD 202.566667 R; largest winner share 0.111696; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 12 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 33 | -32.300000 | 0.084986 | 0.094488 | 18 | 1 | 12 |
| 2023-02 | 20 | -11.333333 | 0.222857 | 0.244444 | 18 | 5 | 14 |
| 2023-03 | 13 | -12.766667 | 0.094563 | 0.085106 | 22 | 2 | 14 |
| 2023-04 | 17 | -0.150000 | 0.987738 | 0.931818 | 18 | 4 | 13 |
| 2023-05 | 30 | -17.250000 | 0.435967 | 0.454545 | 21 | 3 | 14 |
| 2023-06 | 17 | -19.166667 | 0.012876 | 0.016129 | 20 | 5 | 15 |
| 2023-07 | 35 | -30.316667 | 0.182472 | 0.205128 | 19 | 3 | 11 |
| 2023-08 | 55 | -14.233333 | 0.685451 | 0.647059 | 14 | 2 | 6 |
| 2023-09 | 31 | -28.333333 | 0.150000 | 0.165929 | 14 | 1 | 8 |
| 2023-10 | 14 | -8.866667 | 0.471698 | 0.367647 | 2 | 0 | 1 |
| 2023-11 | 24 | -19.683333 | 0.352167 | 0.398230 | 6 | 0 | 1 |
| 2023-12 | 13 | -6.833333 | 0.589178 | 0.816667 | 0 | 0 | 0 |

### B_OPT2023_N4_W2_T2_SB1_TP8

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 302, entry dates 143, entry months 12; SKIP 26, EXCLUDED 109, exclusion share 0.265207; conditional FLAT CLOSED 302.
Net -198.166667 R; PF R / price 0.351726 / 0.333457; expectancy -0.656181 R; win rate 0.198675; average winner / loser 1.791944 / -1.323304 R.
Conditional CLOSED-only DD 200.900000 R; largest winner share 0.124012; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 12 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 33 | -32.300000 | 0.084986 | 0.094488 | 18 | 1 | 12 |
| 2023-02 | 20 | -11.333333 | 0.222857 | 0.244444 | 18 | 5 | 14 |
| 2023-03 | 13 | -12.766667 | 0.094563 | 0.085106 | 22 | 2 | 14 |
| 2023-04 | 17 | -0.150000 | 0.987738 | 0.931818 | 18 | 4 | 13 |
| 2023-05 | 30 | -17.250000 | 0.435967 | 0.454545 | 21 | 3 | 14 |
| 2023-06 | 17 | -19.166667 | 0.012876 | 0.016129 | 20 | 5 | 15 |
| 2023-07 | 35 | -30.316667 | 0.182472 | 0.205128 | 19 | 3 | 11 |
| 2023-08 | 55 | -12.566667 | 0.722284 | 0.679739 | 14 | 2 | 6 |
| 2023-09 | 31 | -28.333333 | 0.150000 | 0.165929 | 14 | 1 | 8 |
| 2023-10 | 14 | -8.866667 | 0.471698 | 0.367647 | 2 | 0 | 1 |
| 2023-11 | 24 | -19.683333 | 0.352167 | 0.398230 | 6 | 0 | 1 |
| 2023-12 | 13 | -5.433333 | 0.673347 | 0.933333 | 0 | 0 | 0 |

### B_OPT2023_N4_W2_T2_SB1_TP9

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 302, entry dates 143, entry months 12; SKIP 26, EXCLUDED 109, exclusion share 0.265207; conditional FLAT CLOSED 302.
Net -195.100000 R; PF R / price 0.361758 / 0.340507; expectancy -0.646026 R; win rate 0.198675; average winner / loser 1.843056 / -1.323304 R.
Conditional CLOSED-only DD 199.233333 R; largest winner share 0.135644; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 12 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 33 | -32.300000 | 0.084986 | 0.094488 | 18 | 1 | 12 |
| 2023-02 | 20 | -11.333333 | 0.222857 | 0.244444 | 18 | 5 | 14 |
| 2023-03 | 13 | -12.766667 | 0.094563 | 0.085106 | 22 | 2 | 14 |
| 2023-04 | 17 | -0.150000 | 0.987738 | 0.931818 | 18 | 4 | 13 |
| 2023-05 | 30 | -17.250000 | 0.435967 | 0.454545 | 21 | 3 | 14 |
| 2023-06 | 17 | -19.166667 | 0.012876 | 0.016129 | 20 | 5 | 15 |
| 2023-07 | 35 | -30.316667 | 0.182472 | 0.205128 | 19 | 3 | 11 |
| 2023-08 | 55 | -10.900000 | 0.759116 | 0.712418 | 14 | 2 | 6 |
| 2023-09 | 31 | -28.333333 | 0.150000 | 0.165929 | 14 | 1 | 8 |
| 2023-10 | 14 | -8.866667 | 0.471698 | 0.367647 | 2 | 0 | 1 |
| 2023-11 | 24 | -19.683333 | 0.352167 | 0.398230 | 6 | 0 | 1 |
| 2023-12 | 13 | -4.033333 | 0.757515 | 1.050000 | 0 | 0 | 0 |

### B_OPT2023_N4_W2_T2_SB1_TP10

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 302, entry dates 143, entry months 12; SKIP 26, EXCLUDED 109, exclusion share 0.265207; conditional FLAT CLOSED 302.
Net -195.366667 R; PF R / price 0.360885 / 0.335189; expectancy -0.646909 R; win rate 0.198675; average winner / loser 1.838611 / -1.323304 R.
Conditional CLOSED-only DD 200.900000 R; largest winner share 0.126907; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 12 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 33 | -32.300000 | 0.084986 | 0.094488 | 18 | 1 | 12 |
| 2023-02 | 20 | -11.333333 | 0.222857 | 0.244444 | 18 | 5 | 14 |
| 2023-03 | 13 | -12.766667 | 0.094563 | 0.085106 | 22 | 2 | 14 |
| 2023-04 | 17 | -0.150000 | 0.987738 | 0.931818 | 18 | 4 | 13 |
| 2023-05 | 30 | -17.250000 | 0.435967 | 0.454545 | 21 | 3 | 14 |
| 2023-06 | 17 | -19.166667 | 0.012876 | 0.016129 | 20 | 5 | 15 |
| 2023-07 | 35 | -30.316667 | 0.182472 | 0.205128 | 19 | 3 | 11 |
| 2023-08 | 55 | -12.566667 | 0.722284 | 0.679739 | 14 | 2 | 6 |
| 2023-09 | 31 | -28.333333 | 0.150000 | 0.165929 | 14 | 1 | 8 |
| 2023-10 | 14 | -8.866667 | 0.471698 | 0.367647 | 2 | 0 | 1 |
| 2023-11 | 24 | -19.683333 | 0.352167 | 0.398230 | 6 | 0 | 1 |
| 2023-12 | 13 | -2.633333 | 0.841683 | 1.166667 | 0 | 0 | 0 |

### B_OPT2023_N4_W2_T3_SB1_TP2

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 212, entry dates 122, entry months 12; SKIP 28, EXCLUDED 80, exclusion share 0.273973; conditional FLAT CLOSED 212.
Net -137.466667 R; PF R / price 0.326089 / 0.290912; expectancy -0.648428 R; win rate 0.198113; average winner / loser 1.583730 / -1.291034 R.
Conditional CLOSED-only DD 137.466667 R; largest winner share 0.050113; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 23 | -18.750000 | 0.196429 | 0.246575 | 18 | 2 | 10 |
| 2023-02 | 21 | -16.416667 | 0.139738 | 0.145161 | 18 | 5 | 9 |
| 2023-03 | 14 | -16.933333 | 0.019305 | 0.018182 | 22 | 7 | 8 |
| 2023-04 | 11 | -2.566667 | 0.678497 | 0.633333 | 18 | 2 | 10 |
| 2023-05 | 20 | -12.583333 | 0.354701 | 0.354839 | 21 | 0 | 11 |
| 2023-06 | 19 | -19.150000 | 0.080064 | 0.073529 | 20 | 3 | 13 |
| 2023-07 | 21 | -13.483333 | 0.289728 | 0.301587 | 19 | 4 | 8 |
| 2023-08 | 34 | -10.316667 | 0.625756 | 0.619565 | 14 | 2 | 6 |
| 2023-09 | 28 | -21.483333 | 0.208717 | 0.203349 | 14 | 2 | 5 |
| 2023-10 | 2 | -0.250000 | 0.833333 | 0.833333 | 2 | 1 | 0 |
| 2023-11 | 12 | 3.933333 | 1.347059 | 1.621622 | 6 | 0 | 0 |
| 2023-12 | 7 | -9.466667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N4_W2_T3_SB1_TP3

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 211, entry dates 122, entry months 12; SKIP 28, EXCLUDED 80, exclusion share 0.274914; conditional FLAT CLOSED 211.
Net -136.916667 R; PF R / price 0.328785 / 0.295942; expectancy -0.648894 R; win rate 0.194313; average winner / loser 1.635772 / -1.291034 R.
Conditional CLOSED-only DD 136.916667 R; largest winner share 0.074553; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 23 | -17.250000 | 0.260714 | 0.328767 | 18 | 2 | 10 |
| 2023-02 | 21 | -16.416667 | 0.139738 | 0.145161 | 18 | 5 | 9 |
| 2023-03 | 14 | -16.933333 | 0.019305 | 0.018182 | 22 | 7 | 8 |
| 2023-04 | 11 | -2.566667 | 0.678497 | 0.633333 | 18 | 2 | 10 |
| 2023-05 | 20 | -13.583333 | 0.303419 | 0.306452 | 21 | 0 | 11 |
| 2023-06 | 19 | -19.150000 | 0.080064 | 0.073529 | 20 | 3 | 13 |
| 2023-07 | 21 | -13.483333 | 0.289728 | 0.301587 | 19 | 4 | 8 |
| 2023-08 | 34 | -9.900000 | 0.640871 | 0.619565 | 14 | 2 | 6 |
| 2023-09 | 28 | -21.483333 | 0.208717 | 0.203349 | 14 | 2 | 5 |
| 2023-10 | 2 | -0.250000 | 0.833333 | 0.833333 | 2 | 1 | 0 |
| 2023-11 | 11 | 3.566667 | 1.314706 | 1.621622 | 6 | 0 | 0 |
| 2023-12 | 7 | -9.466667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N4_W2_T3_SB1_TP4

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 211, entry dates 122, entry months 12; SKIP 28, EXCLUDED 80, exclusion share 0.274914; conditional FLAT CLOSED 211.
Net -135.233333 R; PF R / price 0.337037 / 0.287391; expectancy -0.640916 R; win rate 0.194313; average winner / loser 1.676829 / -1.291034 R.
Conditional CLOSED-only DD 137.566667 R; largest winner share 0.096970; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 23 | -20.000000 | 0.142857 | 0.178082 | 18 | 2 | 10 |
| 2023-02 | 21 | -16.416667 | 0.139738 | 0.145161 | 18 | 5 | 9 |
| 2023-03 | 14 | -16.933333 | 0.019305 | 0.018182 | 22 | 7 | 8 |
| 2023-04 | 11 | -2.566667 | 0.678497 | 0.633333 | 18 | 2 | 10 |
| 2023-05 | 20 | -13.583333 | 0.303419 | 0.306452 | 21 | 0 | 11 |
| 2023-06 | 19 | -19.150000 | 0.080064 | 0.073529 | 20 | 3 | 13 |
| 2023-07 | 21 | -13.483333 | 0.289728 | 0.301587 | 19 | 4 | 8 |
| 2023-08 | 34 | -8.233333 | 0.701330 | 0.673913 | 14 | 2 | 6 |
| 2023-09 | 28 | -21.483333 | 0.208717 | 0.203349 | 14 | 2 | 5 |
| 2023-10 | 2 | -0.250000 | 0.833333 | 0.833333 | 2 | 1 | 0 |
| 2023-11 | 11 | 6.333333 | 1.558824 | 1.864865 | 6 | 0 | 0 |
| 2023-12 | 7 | -9.466667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N4_W2_T3_SB1_TP5

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 211, entry dates 122, entry months 12; SKIP 28, EXCLUDED 80, exclusion share 0.274914; conditional FLAT CLOSED 211.
Net -139.400000 R; PF R / price 0.321599 / 0.292295; expectancy -0.660664 R; win rate 0.189573; average winner / loser 1.652083 / -1.292348 R.
Conditional CLOSED-only DD 139.400000 R; largest winner share 0.126103; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 23 | -20.000000 | 0.142857 | 0.178082 | 18 | 2 | 10 |
| 2023-02 | 21 | -16.416667 | 0.139738 | 0.145161 | 18 | 5 | 9 |
| 2023-03 | 14 | -16.933333 | 0.019305 | 0.018182 | 22 | 7 | 8 |
| 2023-04 | 11 | -2.566667 | 0.678497 | 0.633333 | 18 | 2 | 10 |
| 2023-05 | 20 | -13.583333 | 0.303419 | 0.306452 | 21 | 0 | 11 |
| 2023-06 | 19 | -19.150000 | 0.080064 | 0.073529 | 20 | 3 | 13 |
| 2023-07 | 21 | -13.483333 | 0.289728 | 0.301587 | 19 | 4 | 8 |
| 2023-08 | 34 | -6.566667 | 0.761790 | 0.728261 | 14 | 2 | 6 |
| 2023-09 | 28 | -21.483333 | 0.208717 | 0.203349 | 14 | 2 | 5 |
| 2023-10 | 2 | -0.250000 | 0.833333 | 0.833333 | 2 | 1 | 0 |
| 2023-11 | 11 | 0.500000 | 1.038961 | 1.162791 | 6 | 0 | 0 |
| 2023-12 | 7 | -9.466667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N4_W2_T3_SB1_TP6

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 211, entry dates 122, entry months 12; SKIP 28, EXCLUDED 80, exclusion share 0.274914; conditional FLAT CLOSED 211.
Net -136.066667 R; PF R / price 0.337821 / 0.301508; expectancy -0.644866 R; win rate 0.189573; average winner / loser 1.735417 / -1.292348 R.
Conditional CLOSED-only DD 136.066667 R; largest winner share 0.144058; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 23 | -20.000000 | 0.142857 | 0.178082 | 18 | 2 | 10 |
| 2023-02 | 21 | -16.416667 | 0.139738 | 0.145161 | 18 | 5 | 9 |
| 2023-03 | 14 | -16.933333 | 0.019305 | 0.018182 | 22 | 7 | 8 |
| 2023-04 | 11 | -2.566667 | 0.678497 | 0.633333 | 18 | 2 | 10 |
| 2023-05 | 20 | -13.583333 | 0.303419 | 0.306452 | 21 | 0 | 11 |
| 2023-06 | 19 | -19.150000 | 0.080064 | 0.073529 | 20 | 3 | 13 |
| 2023-07 | 21 | -13.483333 | 0.289728 | 0.301587 | 19 | 4 | 8 |
| 2023-08 | 34 | -4.900000 | 0.822249 | 0.782609 | 14 | 2 | 6 |
| 2023-09 | 28 | -21.483333 | 0.208717 | 0.203349 | 14 | 2 | 5 |
| 2023-10 | 2 | -0.250000 | 0.833333 | 0.833333 | 2 | 1 | 0 |
| 2023-11 | 11 | 2.166667 | 1.168831 | 1.279070 | 6 | 0 | 0 |
| 2023-12 | 7 | -9.466667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N4_W2_T3_SB1_TP7

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 211, entry dates 122, entry months 12; SKIP 28, EXCLUDED 80, exclusion share 0.274914; conditional FLAT CLOSED 211.
Net -132.733333 R; PF R / price 0.354043 / 0.310720; expectancy -0.629068 R; win rate 0.189573; average winner / loser 1.818750 / -1.292348 R.
Conditional CLOSED-only DD 132.733333 R; largest winner share 0.160367; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 23 | -20.000000 | 0.142857 | 0.178082 | 18 | 2 | 10 |
| 2023-02 | 21 | -16.416667 | 0.139738 | 0.145161 | 18 | 5 | 9 |
| 2023-03 | 14 | -16.933333 | 0.019305 | 0.018182 | 22 | 7 | 8 |
| 2023-04 | 11 | -2.566667 | 0.678497 | 0.633333 | 18 | 2 | 10 |
| 2023-05 | 20 | -13.583333 | 0.303419 | 0.306452 | 21 | 0 | 11 |
| 2023-06 | 19 | -19.150000 | 0.080064 | 0.073529 | 20 | 3 | 13 |
| 2023-07 | 21 | -13.483333 | 0.289728 | 0.301587 | 19 | 4 | 8 |
| 2023-08 | 34 | -3.233333 | 0.882709 | 0.836957 | 14 | 2 | 6 |
| 2023-09 | 28 | -21.483333 | 0.208717 | 0.203349 | 14 | 2 | 5 |
| 2023-10 | 2 | -0.250000 | 0.833333 | 0.833333 | 2 | 1 | 0 |
| 2023-11 | 11 | 3.833333 | 1.298701 | 1.395349 | 6 | 0 | 0 |
| 2023-12 | 7 | -9.466667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N4_W2_T3_SB1_TP8

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 211, entry dates 122, entry months 12; SKIP 28, EXCLUDED 80, exclusion share 0.274914; conditional FLAT CLOSED 211.
Net -129.400000 R; PF R / price 0.370265 / 0.319933; expectancy -0.613270 R; win rate 0.189573; average winner / loser 1.902083 / -1.292348 R.
Conditional CLOSED-only DD 130.900000 R; largest winner share 0.175246; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 23 | -20.000000 | 0.142857 | 0.178082 | 18 | 2 | 10 |
| 2023-02 | 21 | -16.416667 | 0.139738 | 0.145161 | 18 | 5 | 9 |
| 2023-03 | 14 | -16.933333 | 0.019305 | 0.018182 | 22 | 7 | 8 |
| 2023-04 | 11 | -2.566667 | 0.678497 | 0.633333 | 18 | 2 | 10 |
| 2023-05 | 20 | -13.583333 | 0.303419 | 0.306452 | 21 | 0 | 11 |
| 2023-06 | 19 | -19.150000 | 0.080064 | 0.073529 | 20 | 3 | 13 |
| 2023-07 | 21 | -13.483333 | 0.289728 | 0.301587 | 19 | 4 | 8 |
| 2023-08 | 34 | -1.566667 | 0.943168 | 0.891304 | 14 | 2 | 6 |
| 2023-09 | 28 | -21.483333 | 0.208717 | 0.203349 | 14 | 2 | 5 |
| 2023-10 | 2 | -0.250000 | 0.833333 | 0.833333 | 2 | 1 | 0 |
| 2023-11 | 11 | 5.500000 | 1.428571 | 1.511628 | 6 | 0 | 0 |
| 2023-12 | 7 | -9.466667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N4_W2_T3_SB1_TP9

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 211, entry dates 122, entry months 12; SKIP 28, EXCLUDED 80, exclusion share 0.274914; conditional FLAT CLOSED 211.
Net -126.066667 R; PF R / price 0.386487 / 0.329146; expectancy -0.597472 R; win rate 0.189573; average winner / loser 1.985417 / -1.292348 R.
Conditional CLOSED-only DD 129.233333 R; largest winner share 0.188877; largest positive month share 0.986239. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 23 | -20.000000 | 0.142857 | 0.178082 | 18 | 2 | 10 |
| 2023-02 | 21 | -16.416667 | 0.139738 | 0.145161 | 18 | 5 | 9 |
| 2023-03 | 14 | -16.933333 | 0.019305 | 0.018182 | 22 | 7 | 8 |
| 2023-04 | 11 | -2.566667 | 0.678497 | 0.633333 | 18 | 2 | 10 |
| 2023-05 | 20 | -13.583333 | 0.303419 | 0.306452 | 21 | 0 | 11 |
| 2023-06 | 19 | -19.150000 | 0.080064 | 0.073529 | 20 | 3 | 13 |
| 2023-07 | 21 | -13.483333 | 0.289728 | 0.301587 | 19 | 4 | 8 |
| 2023-08 | 34 | 0.100000 | 1.003628 | 0.945652 | 14 | 2 | 6 |
| 2023-09 | 28 | -21.483333 | 0.208717 | 0.203349 | 14 | 2 | 5 |
| 2023-10 | 2 | -0.250000 | 0.833333 | 0.833333 | 2 | 1 | 0 |
| 2023-11 | 11 | 7.166667 | 1.558442 | 1.627907 | 6 | 0 | 0 |
| 2023-12 | 7 | -9.466667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N4_W2_T3_SB1_TP10

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 211, entry dates 122, entry months 12; SKIP 28, EXCLUDED 80, exclusion share 0.274914; conditional FLAT CLOSED 211.
Net -126.066667 R; PF R / price 0.386487 / 0.321608; expectancy -0.597472 R; win rate 0.189573; average winner / loser 1.985417 / -1.292348 R.
Conditional CLOSED-only DD 130.900000 R; largest winner share 0.209864; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 23 | -20.000000 | 0.142857 | 0.178082 | 18 | 2 | 10 |
| 2023-02 | 21 | -16.416667 | 0.139738 | 0.145161 | 18 | 5 | 9 |
| 2023-03 | 14 | -16.933333 | 0.019305 | 0.018182 | 22 | 7 | 8 |
| 2023-04 | 11 | -2.566667 | 0.678497 | 0.633333 | 18 | 2 | 10 |
| 2023-05 | 20 | -13.583333 | 0.303419 | 0.306452 | 21 | 0 | 11 |
| 2023-06 | 19 | -19.150000 | 0.080064 | 0.073529 | 20 | 3 | 13 |
| 2023-07 | 21 | -13.483333 | 0.289728 | 0.301587 | 19 | 4 | 8 |
| 2023-08 | 34 | -1.566667 | 0.943168 | 0.891304 | 14 | 2 | 6 |
| 2023-09 | 28 | -21.483333 | 0.208717 | 0.203349 | 14 | 2 | 5 |
| 2023-10 | 2 | -0.250000 | 0.833333 | 0.833333 | 2 | 1 | 0 |
| 2023-11 | 11 | 8.833333 | 1.688312 | 1.744186 | 6 | 0 | 0 |
| 2023-12 | 7 | -9.466667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N4_W3_T2_SB1_TP2

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 333, entry dates 163, entry months 12; SKIP 23, EXCLUDED 110, exclusion share 0.248307; conditional FLAT CLOSED 332.
Net -188.600000 R; PF R / price 0.405828 / 0.361638; expectancy -0.566366 R; win rate 0.228228; average winner / loser 1.694956 / -1.311639 R.
Conditional CLOSED-only DD 190.433333 R; largest winner share 0.025877; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 27 | -24.783333 | 0.060051 | 0.063158 | 18 | 1 | 13 |
| 2023-02 | 22 | -9.833333 | 0.301775 | 0.280000 | 18 | 4 | 13 |
| 2023-03 | 17 | -20.100000 | 0.062208 | 0.054795 | 22 | 4 | 14 |
| 2023-04 | 26 | 1.583333 | 1.106145 | 1.076923 | 18 | 2 | 11 |
| 2023-05 | 25 | -8.766667 | 0.588097 | 0.585714 | 21 | 2 | 14 |
| 2023-06 | 20 | -20.333333 | 0.054264 | 0.054795 | 20 | 4 | 15 |
| 2023-07 | 31 | -12.416667 | 0.514658 | 0.512195 | 19 | 4 | 12 |
| 2023-08 | 50 | -22.033333 | 0.467150 | 0.453901 | 14 | 1 | 8 |
| 2023-09 | 29 | -18.766667 | 0.362401 | 0.291375 | 14 | 0 | 8 |
| 2023-10 | 22 | -0.066667 | 0.996729 | 1.065789 | 2 | 0 | 1 |
| 2023-11 | 39 | -34.883333 | 0.308099 | 0.317460 | 6 | 1 | 1 |
| 2023-12 | 25 | -18.200000 | 0.406522 | 0.407080 | 0 | 0 | 0 |

### B_OPT2023_N4_W3_T2_SB1_TP3

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 331, entry dates 163, entry months 12; SKIP 23, EXCLUDED 111, exclusion share 0.251131; conditional FLAT CLOSED 330.
Net -184.966667 R; PF R / price 0.422731 / 0.360471; expectancy -0.558812 R; win rate 0.217523; average winner / loser 1.881250 / -1.313183 R.
Conditional CLOSED-only DD 188.466667 R; largest winner share 0.036914; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 12 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 27 | -24.783333 | 0.060051 | 0.063158 | 18 | 1 | 13 |
| 2023-02 | 22 | -9.833333 | 0.301775 | 0.280000 | 18 | 4 | 13 |
| 2023-03 | 17 | -20.100000 | 0.062208 | 0.054795 | 22 | 4 | 14 |
| 2023-04 | 24 | -0.250000 | 0.981366 | 1.000000 | 18 | 2 | 12 |
| 2023-05 | 25 | -9.766667 | 0.541112 | 0.542857 | 21 | 2 | 14 |
| 2023-06 | 20 | -20.333333 | 0.054264 | 0.054795 | 20 | 4 | 15 |
| 2023-07 | 31 | -10.750000 | 0.579805 | 0.573171 | 19 | 4 | 12 |
| 2023-08 | 50 | -20.366667 | 0.507457 | 0.489362 | 14 | 1 | 8 |
| 2023-09 | 29 | -17.766667 | 0.396376 | 0.273893 | 14 | 0 | 8 |
| 2023-10 | 22 | -4.333333 | 0.814683 | 0.840909 | 2 | 0 | 1 |
| 2023-11 | 39 | -28.716667 | 0.430413 | 0.439153 | 6 | 1 | 1 |
| 2023-12 | 25 | -17.966667 | 0.441451 | 0.428571 | 0 | 0 | 0 |

### B_OPT2023_N4_W3_T2_SB1_TP4

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 331, entry dates 163, entry months 12; SKIP 23, EXCLUDED 111, exclusion share 0.251131; conditional FLAT CLOSED 330.
Net -164.333333 R; PF R / price 0.487126 / 0.381917; expectancy -0.496475 R; win rate 0.217523; average winner / loser 2.167824 / -1.313183 R.
Conditional CLOSED-only DD 169.500000 R; largest winner share 0.042712; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 27 | -24.783333 | 0.060051 | 0.063158 | 18 | 1 | 13 |
| 2023-02 | 22 | -9.833333 | 0.301775 | 0.280000 | 18 | 4 | 13 |
| 2023-03 | 17 | -20.100000 | 0.062208 | 0.054795 | 22 | 4 | 14 |
| 2023-04 | 24 | -0.250000 | 0.981366 | 1.000000 | 18 | 2 | 12 |
| 2023-05 | 25 | -9.766667 | 0.541112 | 0.542857 | 21 | 2 | 14 |
| 2023-06 | 20 | -20.333333 | 0.054264 | 0.054795 | 20 | 4 | 15 |
| 2023-07 | 31 | -9.083333 | 0.644951 | 0.634146 | 19 | 4 | 12 |
| 2023-08 | 50 | -18.700000 | 0.547763 | 0.524823 | 14 | 1 | 8 |
| 2023-09 | 29 | -16.100000 | 0.453001 | 0.279720 | 14 | 0 | 8 |
| 2023-10 | 22 | 0.400000 | 1.017106 | 1.034091 | 2 | 0 | 1 |
| 2023-11 | 39 | -22.550000 | 0.552727 | 0.560847 | 6 | 1 | 1 |
| 2023-12 | 25 | -13.233333 | 0.588601 | 0.571429 | 0 | 0 | 0 |

### B_OPT2023_N4_W3_T2_SB1_TP5

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 331, entry dates 163, entry months 12; SKIP 23, EXCLUDED 111, exclusion share 0.251131; conditional FLAT CLOSED 330.
Net -157.566667 R; PF R / price 0.510536 / 0.389683; expectancy -0.476032 R; win rate 0.214502; average winner / loser 2.314789 / -1.313946 R.
Conditional CLOSED-only DD 164.400000 R; largest winner share 0.050705; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 27 | -24.783333 | 0.060051 | 0.063158 | 18 | 1 | 13 |
| 2023-02 | 22 | -9.833333 | 0.301775 | 0.280000 | 18 | 4 | 13 |
| 2023-03 | 17 | -20.100000 | 0.062208 | 0.054795 | 22 | 4 | 14 |
| 2023-04 | 24 | -0.250000 | 0.981366 | 1.000000 | 18 | 2 | 12 |
| 2023-05 | 25 | -9.766667 | 0.541112 | 0.542857 | 21 | 2 | 14 |
| 2023-06 | 20 | -20.333333 | 0.054264 | 0.054795 | 20 | 4 | 15 |
| 2023-07 | 31 | -9.416667 | 0.631922 | 0.621951 | 19 | 4 | 12 |
| 2023-08 | 50 | -17.033333 | 0.588069 | 0.560284 | 14 | 1 | 8 |
| 2023-09 | 29 | -14.433333 | 0.509626 | 0.285548 | 14 | 0 | 8 |
| 2023-10 | 22 | 2.266667 | 1.096935 | 1.102273 | 2 | 0 | 1 |
| 2023-11 | 39 | -25.383333 | 0.511075 | 0.507692 | 6 | 1 | 1 |
| 2023-12 | 25 | -8.500000 | 0.735751 | 0.714286 | 0 | 0 | 0 |

### B_OPT2023_N4_W3_T2_SB1_TP6

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 331, entry dates 163, entry months 12; SKIP 23, EXCLUDED 111, exclusion share 0.251131; conditional FLAT CLOSED 330.
Net -159.083333 R; PF R / price 0.508370 / 0.395638; expectancy -0.480614 R; win rate 0.211480; average winner / loser 2.350000 / -1.315379 R.
Conditional CLOSED-only DD 159.083333 R; largest winner share 0.060790; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 27 | -24.783333 | 0.060051 | 0.063158 | 18 | 1 | 13 |
| 2023-02 | 22 | -9.833333 | 0.301775 | 0.280000 | 18 | 4 | 13 |
| 2023-03 | 17 | -20.100000 | 0.062208 | 0.054795 | 22 | 4 | 14 |
| 2023-04 | 24 | -0.250000 | 0.981366 | 1.000000 | 18 | 2 | 12 |
| 2023-05 | 25 | -9.766667 | 0.541112 | 0.542857 | 21 | 2 | 14 |
| 2023-06 | 20 | -20.333333 | 0.054264 | 0.054795 | 20 | 4 | 15 |
| 2023-07 | 31 | -9.416667 | 0.631922 | 0.621951 | 19 | 4 | 12 |
| 2023-08 | 50 | -15.366667 | 0.628376 | 0.595745 | 14 | 1 | 8 |
| 2023-09 | 29 | -12.766667 | 0.566251 | 0.291375 | 14 | 0 | 8 |
| 2023-10 | 22 | 3.933333 | 1.168211 | 1.159091 | 2 | 0 | 1 |
| 2023-11 | 39 | -24.966667 | 0.519101 | 0.507692 | 6 | 1 | 1 |
| 2023-12 | 25 | -15.433333 | 0.543842 | 0.580645 | 0 | 0 | 0 |

### B_OPT2023_N4_W3_T2_SB1_TP7

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 331, entry dates 163, entry months 12; SKIP 23, EXCLUDED 111, exclusion share 0.251131; conditional FLAT CLOSED 330.
Net -169.850000 R; PF R / price 0.477786 / 0.398283; expectancy -0.513142 R; win rate 0.208459; average winner / loser 2.252174 / -1.316802 R.
Conditional CLOSED-only DD 172.683333 R; largest winner share 0.075075; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 12 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 27 | -24.783333 | 0.060051 | 0.063158 | 18 | 1 | 13 |
| 2023-02 | 22 | -9.833333 | 0.301775 | 0.280000 | 18 | 4 | 13 |
| 2023-03 | 17 | -20.100000 | 0.062208 | 0.054795 | 22 | 4 | 14 |
| 2023-04 | 24 | -0.250000 | 0.981366 | 1.000000 | 18 | 2 | 12 |
| 2023-05 | 25 | -9.766667 | 0.541112 | 0.542857 | 21 | 2 | 14 |
| 2023-06 | 20 | -20.333333 | 0.054264 | 0.054795 | 20 | 4 | 15 |
| 2023-07 | 31 | -9.416667 | 0.631922 | 0.621951 | 19 | 4 | 12 |
| 2023-08 | 50 | -13.700000 | 0.668682 | 0.631206 | 14 | 1 | 8 |
| 2023-09 | 29 | -19.766667 | 0.328426 | 0.266900 | 14 | 0 | 8 |
| 2023-10 | 22 | -7.733333 | 0.691284 | 0.774194 | 2 | 0 | 1 |
| 2023-11 | 39 | -21.800000 | 0.580096 | 0.564103 | 6 | 1 | 1 |
| 2023-12 | 25 | -12.366667 | 0.634483 | 0.677419 | 0 | 0 | 0 |

### B_OPT2023_N4_W3_T2_SB1_TP8

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 331, entry dates 163, entry months 12; SKIP 23, EXCLUDED 111, exclusion share 0.251131; conditional FLAT CLOSED 330.
Net -177.450000 R; PF R / price 0.456924 / 0.400475; expectancy -0.536103 R; win rate 0.205438; average winner / loser 2.195588 / -1.317540 R.
Conditional CLOSED-only DD 183.350000 R; largest winner share 0.089306; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 12 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 27 | -24.783333 | 0.060051 | 0.063158 | 18 | 1 | 13 |
| 2023-02 | 22 | -9.833333 | 0.301775 | 0.280000 | 18 | 4 | 13 |
| 2023-03 | 17 | -20.100000 | 0.062208 | 0.054795 | 22 | 4 | 14 |
| 2023-04 | 24 | -0.250000 | 0.981366 | 1.000000 | 18 | 2 | 12 |
| 2023-05 | 25 | -9.766667 | 0.541112 | 0.542857 | 21 | 2 | 14 |
| 2023-06 | 20 | -20.333333 | 0.054264 | 0.054795 | 20 | 4 | 15 |
| 2023-07 | 31 | -9.416667 | 0.631922 | 0.621951 | 19 | 4 | 12 |
| 2023-08 | 50 | -12.033333 | 0.708988 | 0.666667 | 14 | 1 | 8 |
| 2023-09 | 29 | -19.766667 | 0.328426 | 0.266900 | 14 | 0 | 8 |
| 2023-10 | 22 | -7.733333 | 0.691284 | 0.774194 | 2 | 0 | 1 |
| 2023-11 | 39 | -34.133333 | 0.360998 | 0.333333 | 6 | 1 | 1 |
| 2023-12 | 25 | -9.300000 | 0.725123 | 0.774194 | 0 | 0 | 0 |

### B_OPT2023_N4_W3_T2_SB1_TP9

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 331, entry dates 163, entry months 12; SKIP 23, EXCLUDED 111, exclusion share 0.251131; conditional FLAT CLOSED 330.
Net -172.716667 R; PF R / price 0.471410 / 0.408659; expectancy -0.521803 R; win rate 0.205438; average winner / loser 2.265196 / -1.317540 R.
Conditional CLOSED-only DD 181.683333 R; largest winner share 0.097382; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 12 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 27 | -24.783333 | 0.060051 | 0.063158 | 18 | 1 | 13 |
| 2023-02 | 22 | -9.833333 | 0.301775 | 0.280000 | 18 | 4 | 13 |
| 2023-03 | 17 | -20.100000 | 0.062208 | 0.054795 | 22 | 4 | 14 |
| 2023-04 | 24 | -0.250000 | 0.981366 | 1.000000 | 18 | 2 | 12 |
| 2023-05 | 25 | -9.766667 | 0.541112 | 0.542857 | 21 | 2 | 14 |
| 2023-06 | 20 | -20.333333 | 0.054264 | 0.054795 | 20 | 4 | 15 |
| 2023-07 | 31 | -9.416667 | 0.631922 | 0.621951 | 19 | 4 | 12 |
| 2023-08 | 50 | -10.366667 | 0.749295 | 0.702128 | 14 | 1 | 8 |
| 2023-09 | 29 | -19.766667 | 0.328426 | 0.266900 | 14 | 0 | 8 |
| 2023-10 | 22 | -7.733333 | 0.691284 | 0.774194 | 2 | 0 | 1 |
| 2023-11 | 39 | -34.133333 | 0.360998 | 0.333333 | 6 | 1 | 1 |
| 2023-12 | 25 | -6.233333 | 0.815764 | 0.870968 | 0 | 0 | 0 |

### B_OPT2023_N4_W3_T2_SB1_TP10

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 331, entry dates 163, entry months 12; SKIP 23, EXCLUDED 111, exclusion share 0.251131; conditional FLAT CLOSED 330.
Net -171.316667 R; PF R / price 0.475695 / 0.403643; expectancy -0.517573 R; win rate 0.205438; average winner / loser 2.285784 / -1.317540 R.
Conditional CLOSED-only DD 183.350000 R; largest winner share 0.107227; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 12 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 27 | -24.783333 | 0.060051 | 0.063158 | 18 | 1 | 13 |
| 2023-02 | 22 | -9.833333 | 0.301775 | 0.280000 | 18 | 4 | 13 |
| 2023-03 | 17 | -20.100000 | 0.062208 | 0.054795 | 22 | 4 | 14 |
| 2023-04 | 24 | -0.250000 | 0.981366 | 1.000000 | 18 | 2 | 12 |
| 2023-05 | 25 | -9.766667 | 0.541112 | 0.542857 | 21 | 2 | 14 |
| 2023-06 | 20 | -20.333333 | 0.054264 | 0.054795 | 20 | 4 | 15 |
| 2023-07 | 31 | -9.416667 | 0.631922 | 0.621951 | 19 | 4 | 12 |
| 2023-08 | 50 | -12.033333 | 0.708988 | 0.666667 | 14 | 1 | 8 |
| 2023-09 | 29 | -19.766667 | 0.328426 | 0.266900 | 14 | 0 | 8 |
| 2023-10 | 22 | -7.733333 | 0.691284 | 0.774194 | 2 | 0 | 1 |
| 2023-11 | 39 | -34.133333 | 0.360998 | 0.333333 | 6 | 1 | 1 |
| 2023-12 | 25 | -3.166667 | 0.906404 | 0.967742 | 0 | 0 | 0 |

### B_OPT2023_N4_W3_T3_SB1_TP2

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 230, entry dates 129, entry months 12; SKIP 24, EXCLUDED 80, exclusion share 0.258065; conditional FLAT CLOSED 230.
Net -127.866667 R; PF R / price 0.399875 / 0.328104; expectancy -0.555942 R; win rate 0.213043; average winner / loser 1.738776 / -1.268254 R.
Conditional CLOSED-only DD 129.166667 R; largest winner share 0.039124; largest positive month share 0.590452. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 20 | -13.066667 | 0.286624 | 0.288136 | 18 | 2 | 9 |
| 2023-02 | 24 | -17.750000 | 0.130612 | 0.140625 | 18 | 4 | 8 |
| 2023-03 | 14 | -15.683333 | 0.059940 | 0.053571 | 22 | 5 | 8 |
| 2023-04 | 13 | 3.916667 | 1.635135 | 1.500000 | 18 | 2 | 10 |
| 2023-05 | 22 | -12.666667 | 0.369295 | 0.363636 | 21 | 1 | 11 |
| 2023-06 | 14 | -13.400000 | 0.069444 | 0.063830 | 20 | 3 | 11 |
| 2023-07 | 30 | -16.983333 | 0.378279 | 0.397727 | 19 | 4 | 9 |
| 2023-08 | 37 | -20.866667 | 0.383858 | 0.369369 | 14 | 1 | 6 |
| 2023-09 | 23 | -10.016667 | 0.482343 | 0.283582 | 14 | 1 | 7 |
| 2023-10 | 6 | 2.716667 | 1.582143 | 1.705882 | 2 | 1 | 0 |
| 2023-11 | 18 | -5.900000 | 0.716800 | 0.885714 | 6 | 0 | 1 |
| 2023-12 | 9 | -8.166667 | 0.255319 | 0.341463 | 0 | 0 | 0 |

### B_OPT2023_N4_W3_T3_SB1_TP3

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 229, entry dates 129, entry months 12; SKIP 24, EXCLUDED 80, exclusion share 0.258900; conditional FLAT CLOSED 229.
Net -111.600000 R; PF R / price 0.472091 / 0.355394; expectancy -0.487336 R; win rate 0.213974; average winner / loser 2.036735 / -1.265868 R.
Conditional CLOSED-only DD 117.033333 R; largest winner share 0.050100; largest positive month share 0.582215. Positive / negative / zero months 3 / 9 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 20 | -11.400000 | 0.377616 | 0.372881 | 18 | 2 | 9 |
| 2023-02 | 24 | -17.750000 | 0.130612 | 0.140625 | 18 | 4 | 8 |
| 2023-03 | 14 | -15.683333 | 0.059940 | 0.053571 | 22 | 5 | 8 |
| 2023-04 | 13 | 3.916667 | 1.635135 | 1.500000 | 18 | 2 | 10 |
| 2023-05 | 22 | -13.666667 | 0.319502 | 0.318182 | 21 | 1 | 11 |
| 2023-06 | 14 | -13.400000 | 0.069444 | 0.063830 | 20 | 3 | 11 |
| 2023-07 | 30 | -15.316667 | 0.439292 | 0.454545 | 19 | 4 | 9 |
| 2023-08 | 37 | -19.200000 | 0.433071 | 0.414414 | 14 | 1 | 6 |
| 2023-09 | 23 | -8.350000 | 0.568475 | 0.291045 | 14 | 1 | 7 |
| 2023-10 | 6 | 5.783333 | 2.239286 | 2.411765 | 2 | 1 | 0 |
| 2023-11 | 17 | 0.233333 | 1.012174 | 1.200000 | 6 | 0 | 1 |
| 2023-12 | 9 | -6.766667 | 0.382979 | 0.512195 | 0 | 0 | 0 |

### B_OPT2023_N4_W3_T3_SB1_TP4

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 229, entry dates 129, entry months 12; SKIP 24, EXCLUDED 80, exclusion share 0.258900; conditional FLAT CLOSED 229.
Net -103.200000 R; PF R / price 0.515038 / 0.382125; expectancy -0.450655 R; win rate 0.209607; average winner / loser 2.283333 / -1.266667 R.
Conditional CLOSED-only DD 113.700000 R; largest winner share 0.060827; largest positive month share 0.512548. Positive / negative / zero months 3 / 9 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 20 | -9.733333 | 0.468608 | 0.457627 | 18 | 2 | 9 |
| 2023-02 | 24 | -17.750000 | 0.130612 | 0.140625 | 18 | 4 | 8 |
| 2023-03 | 14 | -15.683333 | 0.059940 | 0.053571 | 22 | 5 | 8 |
| 2023-04 | 13 | 3.916667 | 1.635135 | 1.500000 | 18 | 2 | 10 |
| 2023-05 | 22 | -13.666667 | 0.319502 | 0.318182 | 21 | 1 | 11 |
| 2023-06 | 14 | -13.400000 | 0.069444 | 0.063830 | 20 | 3 | 11 |
| 2023-07 | 30 | -13.650000 | 0.500305 | 0.511364 | 19 | 4 | 9 |
| 2023-08 | 37 | -17.533333 | 0.482283 | 0.459459 | 14 | 1 | 6 |
| 2023-09 | 23 | -6.683333 | 0.654608 | 0.298507 | 14 | 1 | 7 |
| 2023-10 | 6 | 8.850000 | 2.896429 | 3.117647 | 2 | 1 | 0 |
| 2023-11 | 17 | 4.500000 | 1.234783 | 1.430769 | 6 | 0 | 1 |
| 2023-12 | 9 | -12.366667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N4_W3_T3_SB1_TP5

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 229, entry dates 129, entry months 12; SKIP 24, EXCLUDED 80, exclusion share 0.258900; conditional FLAT CLOSED 229.
Net -103.000000 R; PF R / price 0.519365 / 0.386456; expectancy -0.449782 R; win rate 0.205240; average winner / loser 2.368085 / -1.268047 R.
Conditional CLOSED-only DD 112.366667 R; largest winner share 0.074873; largest positive month share 0.724099. Positive / negative / zero months 3 / 9 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 20 | -10.066667 | 0.450409 | 0.440678 | 18 | 2 | 9 |
| 2023-02 | 24 | -17.750000 | 0.130612 | 0.140625 | 18 | 4 | 8 |
| 2023-03 | 14 | -15.683333 | 0.059940 | 0.053571 | 22 | 5 | 8 |
| 2023-04 | 13 | 3.916667 | 1.635135 | 1.500000 | 18 | 2 | 10 |
| 2023-05 | 22 | -13.666667 | 0.319502 | 0.318182 | 21 | 1 | 11 |
| 2023-06 | 14 | -13.400000 | 0.069444 | 0.063830 | 20 | 3 | 11 |
| 2023-07 | 30 | -13.983333 | 0.488103 | 0.500000 | 19 | 4 | 9 |
| 2023-08 | 37 | -15.866667 | 0.531496 | 0.504505 | 14 | 1 | 6 |
| 2023-09 | 23 | -5.016667 | 0.740741 | 0.305970 | 14 | 1 | 7 |
| 2023-10 | 6 | 10.716667 | 3.296429 | 3.470588 | 2 | 1 | 0 |
| 2023-11 | 17 | 0.166667 | 1.008065 | 1.126761 | 6 | 0 | 1 |
| 2023-12 | 9 | -12.366667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N4_W3_T3_SB1_TP6

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 229, entry dates 129, entry months 12; SKIP 24, EXCLUDED 80, exclusion share 0.258900; conditional FLAT CLOSED 229.
Net -96.083333 R; PF R / price 0.551641 / 0.397574; expectancy -0.419578 R; win rate 0.205240; average winner / loser 2.515248 / -1.268047 R.
Conditional CLOSED-only DD 110.700000 R; largest winner share 0.084590; largest positive month share 0.673617. Positive / negative / zero months 3 / 9 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 20 | -10.066667 | 0.450409 | 0.440678 | 18 | 2 | 9 |
| 2023-02 | 24 | -17.750000 | 0.130612 | 0.140625 | 18 | 4 | 8 |
| 2023-03 | 14 | -15.683333 | 0.059940 | 0.053571 | 22 | 5 | 8 |
| 2023-04 | 13 | 3.916667 | 1.635135 | 1.500000 | 18 | 2 | 10 |
| 2023-05 | 22 | -13.666667 | 0.319502 | 0.318182 | 21 | 1 | 11 |
| 2023-06 | 14 | -13.400000 | 0.069444 | 0.063830 | 20 | 3 | 11 |
| 2023-07 | 30 | -13.983333 | 0.488103 | 0.500000 | 19 | 4 | 9 |
| 2023-08 | 37 | -14.200000 | 0.580709 | 0.549550 | 14 | 1 | 6 |
| 2023-09 | 23 | -3.350000 | 0.826873 | 0.313433 | 14 | 1 | 7 |
| 2023-10 | 6 | 12.383333 | 3.653571 | 3.764706 | 2 | 1 | 0 |
| 2023-11 | 17 | 2.083333 | 1.100806 | 1.211268 | 6 | 0 | 1 |
| 2023-12 | 9 | -12.366667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N4_W3_T3_SB1_TP7

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 229, entry dates 129, entry months 12; SKIP 24, EXCLUDED 80, exclusion share 0.258900; conditional FLAT CLOSED 229.
Net -103.750000 R; PF R / price 0.515866 / 0.401280; expectancy -0.453057 R; win rate 0.205240; average winner / loser 2.352128 / -1.268047 R.
Conditional CLOSED-only DD 109.033333 R; largest winner share 0.105533; largest positive month share 0.522326. Positive / negative / zero months 3 / 9 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 20 | -10.066667 | 0.450409 | 0.440678 | 18 | 2 | 9 |
| 2023-02 | 24 | -17.750000 | 0.130612 | 0.140625 | 18 | 4 | 8 |
| 2023-03 | 14 | -15.683333 | 0.059940 | 0.053571 | 22 | 5 | 8 |
| 2023-04 | 13 | 3.916667 | 1.635135 | 1.500000 | 18 | 2 | 10 |
| 2023-05 | 22 | -13.666667 | 0.319502 | 0.318182 | 21 | 1 | 11 |
| 2023-06 | 14 | -13.400000 | 0.069444 | 0.063830 | 20 | 3 | 11 |
| 2023-07 | 30 | -13.983333 | 0.488103 | 0.500000 | 19 | 4 | 9 |
| 2023-08 | 37 | -12.533333 | 0.629921 | 0.594595 | 14 | 1 | 6 |
| 2023-09 | 23 | -10.350000 | 0.465116 | 0.282090 | 14 | 1 | 7 |
| 2023-10 | 6 | 8.383333 | 2.796429 | 3.058824 | 2 | 1 | 0 |
| 2023-11 | 17 | 3.750000 | 1.181452 | 1.281690 | 6 | 0 | 1 |
| 2023-12 | 9 | -12.366667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N4_W3_T3_SB1_TP8

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors.
CLOSED 229, entry dates 129, entry months 12; SKIP 24, EXCLUDED 80, exclusion share 0.258900; conditional FLAT CLOSED 229.
Net -100.416667 R; PF R / price 0.531420 / 0.410546; expectancy -0.438501 R; win rate 0.205240; average winner / loser 2.423050 / -1.268047 R.
Conditional CLOSED-only DD 107.366667 R; largest winner share 0.117079; largest positive month share 0.473189. Positive / negative / zero months 3 / 9 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 20 | -10.066667 | 0.450409 | 0.440678 | 18 | 2 | 9 |
| 2023-02 | 24 | -17.750000 | 0.130612 | 0.140625 | 18 | 4 | 8 |
| 2023-03 | 14 | -15.683333 | 0.059940 | 0.053571 | 22 | 5 | 8 |
| 2023-04 | 13 | 3.916667 | 1.635135 | 1.500000 | 18 | 2 | 10 |
| 2023-05 | 22 | -13.666667 | 0.319502 | 0.318182 | 21 | 1 | 11 |
| 2023-06 | 14 | -13.400000 | 0.069444 | 0.063830 | 20 | 3 | 11 |
| 2023-07 | 30 | -13.983333 | 0.488103 | 0.500000 | 19 | 4 | 9 |
| 2023-08 | 37 | -10.866667 | 0.679134 | 0.639640 | 14 | 1 | 6 |
| 2023-09 | 23 | -10.350000 | 0.465116 | 0.282090 | 14 | 1 | 7 |
| 2023-10 | 6 | 8.383333 | 2.796429 | 3.058824 | 2 | 1 | 0 |
| 2023-11 | 17 | 5.416667 | 1.262097 | 1.352113 | 6 | 0 | 1 |
| 2023-12 | 9 | -12.366667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N4_W3_T3_SB1_TP9

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors.
CLOSED 229, entry dates 129, entry months 12; SKIP 24, EXCLUDED 80, exclusion share 0.258900; conditional FLAT CLOSED 229.
Net -97.083333 R; PF R / price 0.546975 / 0.419811; expectancy -0.423945 R; win rate 0.205240; average winner / loser 2.493972 / -1.268047 R.
Conditional CLOSED-only DD 105.700000 R; largest winner share 0.127968; largest positive month share 0.432502. Positive / negative / zero months 3 / 9 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 20 | -10.066667 | 0.450409 | 0.440678 | 18 | 2 | 9 |
| 2023-02 | 24 | -17.750000 | 0.130612 | 0.140625 | 18 | 4 | 8 |
| 2023-03 | 14 | -15.683333 | 0.059940 | 0.053571 | 22 | 5 | 8 |
| 2023-04 | 13 | 3.916667 | 1.635135 | 1.500000 | 18 | 2 | 10 |
| 2023-05 | 22 | -13.666667 | 0.319502 | 0.318182 | 21 | 1 | 11 |
| 2023-06 | 14 | -13.400000 | 0.069444 | 0.063830 | 20 | 3 | 11 |
| 2023-07 | 30 | -13.983333 | 0.488103 | 0.500000 | 19 | 4 | 9 |
| 2023-08 | 37 | -9.200000 | 0.728346 | 0.684685 | 14 | 1 | 6 |
| 2023-09 | 23 | -10.350000 | 0.465116 | 0.282090 | 14 | 1 | 7 |
| 2023-10 | 6 | 8.383333 | 2.796429 | 3.058824 | 2 | 1 | 0 |
| 2023-11 | 17 | 7.083333 | 1.342742 | 1.422535 | 6 | 0 | 1 |
| 2023-12 | 9 | -12.366667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N4_W3_T3_SB1_TP10

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors.
CLOSED 229, entry dates 129, entry months 12; SKIP 24, EXCLUDED 80, exclusion share 0.258900; conditional FLAT CLOSED 229.
Net -97.083333 R; PF R / price 0.546975 / 0.412230; expectancy -0.423945 R; win rate 0.205240; average winner / loser 2.493972 / -1.268047 R.
Conditional CLOSED-only DD 107.366667 R; largest winner share 0.142187; largest positive month share 0.415677. Positive / negative / zero months 3 / 9 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 20 | -10.066667 | 0.450409 | 0.440678 | 18 | 2 | 9 |
| 2023-02 | 24 | -17.750000 | 0.130612 | 0.140625 | 18 | 4 | 8 |
| 2023-03 | 14 | -15.683333 | 0.059940 | 0.053571 | 22 | 5 | 8 |
| 2023-04 | 13 | 3.916667 | 1.635135 | 1.500000 | 18 | 2 | 10 |
| 2023-05 | 22 | -13.666667 | 0.319502 | 0.318182 | 21 | 1 | 11 |
| 2023-06 | 14 | -13.400000 | 0.069444 | 0.063830 | 20 | 3 | 11 |
| 2023-07 | 30 | -13.983333 | 0.488103 | 0.500000 | 19 | 4 | 9 |
| 2023-08 | 37 | -10.866667 | 0.679134 | 0.639640 | 14 | 1 | 6 |
| 2023-09 | 23 | -10.350000 | 0.465116 | 0.282090 | 14 | 1 | 7 |
| 2023-10 | 6 | 8.383333 | 2.796429 | 3.058824 | 2 | 1 | 0 |
| 2023-11 | 17 | 8.750000 | 1.423387 | 1.492958 | 6 | 0 | 1 |
| 2023-12 | 9 | -12.366667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N5_W2_T2_SB1_TP2

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 251, entry dates 130, entry months 12; SKIP 29, EXCLUDED 100, exclusion share 0.284900; conditional FLAT CLOSED 251.
Net -159.533333 R; PF R / price 0.353898 / 0.329368; expectancy -0.635591 R; win rate 0.235060; average winner / loser 1.481073 / -1.334685 R.
Conditional CLOSED-only DD 159.533333 R; largest winner share 0.038146; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 26 | -20.950000 | 0.192678 | 0.255556 | 18 | 3 | 11 |
| 2023-02 | 19 | -11.816667 | 0.248941 | 0.264151 | 18 | 3 | 14 |
| 2023-03 | 13 | -14.816667 | 0.043057 | 0.038462 | 22 | 7 | 11 |
| 2023-04 | 14 | -3.550000 | 0.667187 | 0.735294 | 18 | 8 | 9 |
| 2023-05 | 24 | -8.300000 | 0.606013 | 0.579710 | 21 | 1 | 14 |
| 2023-06 | 20 | -19.000000 | 0.173913 | 0.173913 | 20 | 1 | 15 |
| 2023-07 | 27 | -20.883333 | 0.193175 | 0.166667 | 19 | 4 | 14 |
| 2023-08 | 47 | -19.433333 | 0.556317 | 0.519737 | 14 | 1 | 4 |
| 2023-09 | 30 | -19.450000 | 0.321117 | 0.207921 | 14 | 0 | 7 |
| 2023-10 | 8 | 0.350000 | 1.054687 | 1.409091 | 2 | 0 | 0 |
| 2023-11 | 12 | -5.800000 | 0.597222 | 0.816327 | 6 | 1 | 1 |
| 2023-12 | 11 | -15.883333 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N5_W2_T2_SB1_TP3

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 251, entry dates 130, entry months 12; SKIP 29, EXCLUDED 100, exclusion share 0.284900; conditional FLAT CLOSED 251.
Net -156.366667 R; PF R / price 0.370293 / 0.341211; expectancy -0.622975 R; win rate 0.231076; average winner / loser 1.585345 / -1.335036 R.
Conditional CLOSED-only DD 156.366667 R; largest winner share 0.054377; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 26 | -19.950000 | 0.231214 | 0.311111 | 18 | 3 | 11 |
| 2023-02 | 19 | -11.816667 | 0.248941 | 0.264151 | 18 | 3 | 14 |
| 2023-03 | 13 | -14.816667 | 0.043057 | 0.038462 | 22 | 7 | 11 |
| 2023-04 | 14 | -3.216667 | 0.698437 | 0.764706 | 18 | 8 | 9 |
| 2023-05 | 24 | -9.300000 | 0.558544 | 0.536232 | 21 | 1 | 14 |
| 2023-06 | 20 | -19.000000 | 0.173913 | 0.173913 | 20 | 1 | 15 |
| 2023-07 | 27 | -20.883333 | 0.193175 | 0.166667 | 19 | 4 | 14 |
| 2023-08 | 47 | -17.766667 | 0.594368 | 0.552632 | 14 | 1 | 4 |
| 2023-09 | 30 | -17.783333 | 0.379290 | 0.212871 | 14 | 0 | 7 |
| 2023-10 | 8 | 1.150000 | 1.179687 | 1.590909 | 2 | 0 | 0 |
| 2023-11 | 12 | -7.100000 | 0.550633 | 0.696429 | 6 | 1 | 1 |
| 2023-12 | 11 | -15.883333 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N5_W2_T2_SB1_TP4

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 251, entry dates 130, entry months 12; SKIP 29, EXCLUDED 100, exclusion share 0.284900; conditional FLAT CLOSED 251.
Net -150.466667 R; PF R / price 0.394053 / 0.349226; expectancy -0.599469 R; win rate 0.231076; average winner / loser 1.687069 / -1.335036 R.
Conditional CLOSED-only DD 150.466667 R; largest winner share 0.068131; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 26 | -19.950000 | 0.231214 | 0.311111 | 18 | 3 | 11 |
| 2023-02 | 19 | -11.816667 | 0.248941 | 0.264151 | 18 | 3 | 14 |
| 2023-03 | 13 | -14.816667 | 0.043057 | 0.038462 | 22 | 7 | 11 |
| 2023-04 | 14 | -3.216667 | 0.698437 | 0.764706 | 18 | 8 | 9 |
| 2023-05 | 24 | -9.300000 | 0.558544 | 0.536232 | 21 | 1 | 14 |
| 2023-06 | 20 | -19.000000 | 0.173913 | 0.173913 | 20 | 1 | 15 |
| 2023-07 | 27 | -20.883333 | 0.193175 | 0.166667 | 19 | 4 | 14 |
| 2023-08 | 47 | -16.433333 | 0.624810 | 0.578947 | 14 | 1 | 4 |
| 2023-09 | 30 | -16.116667 | 0.437464 | 0.217822 | 14 | 0 | 7 |
| 2023-10 | 8 | 1.150000 | 1.179687 | 1.590909 | 2 | 0 | 0 |
| 2023-11 | 12 | -4.200000 | 0.734177 | 0.928571 | 6 | 1 | 1 |
| 2023-12 | 11 | -15.883333 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N5_W2_T2_SB1_TP5

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 251, entry dates 130, entry months 12; SKIP 29, EXCLUDED 100, exclusion share 0.284900; conditional FLAT CLOSED 251.
Net -144.233333 R; PF R / price 0.419156 / 0.358624; expectancy -0.574635 R; win rate 0.231076; average winner / loser 1.794540 / -1.335036 R.
Conditional CLOSED-only DD 144.233333 R; largest winner share 0.080064; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 26 | -19.950000 | 0.231214 | 0.311111 | 18 | 3 | 11 |
| 2023-02 | 19 | -11.816667 | 0.248941 | 0.264151 | 18 | 3 | 14 |
| 2023-03 | 13 | -14.816667 | 0.043057 | 0.038462 | 22 | 7 | 11 |
| 2023-04 | 14 | -3.216667 | 0.698437 | 0.764706 | 18 | 8 | 9 |
| 2023-05 | 24 | -9.300000 | 0.558544 | 0.536232 | 21 | 1 | 14 |
| 2023-06 | 20 | -19.000000 | 0.173913 | 0.173913 | 20 | 1 | 15 |
| 2023-07 | 27 | -20.883333 | 0.193175 | 0.166667 | 19 | 4 | 14 |
| 2023-08 | 47 | -14.766667 | 0.662861 | 0.611842 | 14 | 1 | 4 |
| 2023-09 | 30 | -14.450000 | 0.495637 | 0.222772 | 14 | 0 | 7 |
| 2023-10 | 8 | 1.150000 | 1.179687 | 1.590909 | 2 | 0 | 0 |
| 2023-11 | 12 | -1.300000 | 0.917722 | 1.160714 | 6 | 1 | 1 |
| 2023-12 | 11 | -15.883333 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N5_W2_T2_SB1_TP6

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 251, entry dates 130, entry months 12; SKIP 29, EXCLUDED 100, exclusion share 0.284900; conditional FLAT CLOSED 251.
Net -142.200000 R; PF R / price 0.427344 / 0.365119; expectancy -0.566534 R; win rate 0.231076; average winner / loser 1.829598 / -1.335036 R.
Conditional CLOSED-only DD 142.200000 R; largest winner share 0.094236; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 26 | -19.950000 | 0.231214 | 0.311111 | 18 | 3 | 11 |
| 2023-02 | 19 | -11.816667 | 0.248941 | 0.264151 | 18 | 3 | 14 |
| 2023-03 | 13 | -14.816667 | 0.043057 | 0.038462 | 22 | 7 | 11 |
| 2023-04 | 14 | -3.216667 | 0.698437 | 0.764706 | 18 | 8 | 9 |
| 2023-05 | 24 | -9.300000 | 0.558544 | 0.536232 | 21 | 1 | 14 |
| 2023-06 | 20 | -19.000000 | 0.173913 | 0.173913 | 20 | 1 | 15 |
| 2023-07 | 27 | -20.883333 | 0.193175 | 0.166667 | 19 | 4 | 14 |
| 2023-08 | 47 | -13.100000 | 0.700913 | 0.644737 | 14 | 1 | 4 |
| 2023-09 | 30 | -12.783333 | 0.553810 | 0.227723 | 14 | 0 | 7 |
| 2023-10 | 8 | 1.150000 | 1.179687 | 1.590909 | 2 | 0 | 0 |
| 2023-11 | 12 | -2.600000 | 0.835443 | 1.017857 | 6 | 1 | 1 |
| 2023-12 | 11 | -15.883333 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N5_W2_T2_SB1_TP7

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 251, entry dates 130, entry months 12; SKIP 29, EXCLUDED 100, exclusion share 0.284900; conditional FLAT CLOSED 251.
Net -137.366667 R; PF R / price 0.446809 / 0.373549; expectancy -0.547278 R; win rate 0.231076; average winner / loser 1.912931 / -1.335036 R.
Conditional CLOSED-only DD 137.366667 R; largest winner share 0.105152; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 26 | -19.950000 | 0.231214 | 0.311111 | 18 | 3 | 11 |
| 2023-02 | 19 | -11.816667 | 0.248941 | 0.264151 | 18 | 3 | 14 |
| 2023-03 | 13 | -14.816667 | 0.043057 | 0.038462 | 22 | 7 | 11 |
| 2023-04 | 14 | -3.216667 | 0.698437 | 0.764706 | 18 | 8 | 9 |
| 2023-05 | 24 | -9.300000 | 0.558544 | 0.536232 | 21 | 1 | 14 |
| 2023-06 | 20 | -19.000000 | 0.173913 | 0.173913 | 20 | 1 | 15 |
| 2023-07 | 27 | -20.883333 | 0.193175 | 0.166667 | 19 | 4 | 14 |
| 2023-08 | 47 | -11.433333 | 0.738965 | 0.677632 | 14 | 1 | 4 |
| 2023-09 | 30 | -11.116667 | 0.611984 | 0.232673 | 14 | 0 | 7 |
| 2023-10 | 8 | 1.150000 | 1.179687 | 1.590909 | 2 | 0 | 0 |
| 2023-11 | 12 | -1.100000 | 0.930380 | 1.125000 | 6 | 1 | 1 |
| 2023-12 | 11 | -15.883333 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N5_W2_T2_SB1_TP8

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 251, entry dates 130, entry months 12; SKIP 29, EXCLUDED 100, exclusion share 0.284900; conditional FLAT CLOSED 251.
Net -140.283333 R; PF R / price 0.435063 / 0.377695; expectancy -0.558898 R; win rate 0.231076; average winner / loser 1.862644 / -1.335036 R.
Conditional CLOSED-only DD 140.283333 R; largest winner share 0.123419; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 26 | -19.950000 | 0.231214 | 0.311111 | 18 | 3 | 11 |
| 2023-02 | 19 | -11.816667 | 0.248941 | 0.264151 | 18 | 3 | 14 |
| 2023-03 | 13 | -14.816667 | 0.043057 | 0.038462 | 22 | 7 | 11 |
| 2023-04 | 14 | -3.216667 | 0.698437 | 0.764706 | 18 | 8 | 9 |
| 2023-05 | 24 | -9.300000 | 0.558544 | 0.536232 | 21 | 1 | 14 |
| 2023-06 | 20 | -19.000000 | 0.173913 | 0.173913 | 20 | 1 | 15 |
| 2023-07 | 27 | -20.883333 | 0.193175 | 0.166667 | 19 | 4 | 14 |
| 2023-08 | 47 | -9.766667 | 0.777017 | 0.710526 | 14 | 1 | 4 |
| 2023-09 | 30 | -9.450000 | 0.670157 | 0.237624 | 14 | 0 | 7 |
| 2023-10 | 8 | 1.150000 | 1.179687 | 1.590909 | 2 | 0 | 0 |
| 2023-11 | 12 | -7.350000 | 0.534810 | 0.678571 | 6 | 1 | 1 |
| 2023-12 | 11 | -15.883333 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N5_W2_T2_SB1_TP9

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 251, entry dates 130, entry months 12; SKIP 29, EXCLUDED 100, exclusion share 0.284900; conditional FLAT CLOSED 251.
Net -136.950000 R; PF R / price 0.448486 / 0.385296; expectancy -0.545618 R; win rate 0.231076; average winner / loser 1.920115 / -1.335036 R.
Conditional CLOSED-only DD 136.950000 R; largest winner share 0.134690; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 26 | -19.950000 | 0.231214 | 0.311111 | 18 | 3 | 11 |
| 2023-02 | 19 | -11.816667 | 0.248941 | 0.264151 | 18 | 3 | 14 |
| 2023-03 | 13 | -14.816667 | 0.043057 | 0.038462 | 22 | 7 | 11 |
| 2023-04 | 14 | -3.216667 | 0.698437 | 0.764706 | 18 | 8 | 9 |
| 2023-05 | 24 | -9.300000 | 0.558544 | 0.536232 | 21 | 1 | 14 |
| 2023-06 | 20 | -19.000000 | 0.173913 | 0.173913 | 20 | 1 | 15 |
| 2023-07 | 27 | -20.883333 | 0.193175 | 0.166667 | 19 | 4 | 14 |
| 2023-08 | 47 | -8.100000 | 0.815068 | 0.743421 | 14 | 1 | 4 |
| 2023-09 | 30 | -7.783333 | 0.728330 | 0.242574 | 14 | 0 | 7 |
| 2023-10 | 8 | 1.150000 | 1.179687 | 1.590909 | 2 | 0 | 0 |
| 2023-11 | 12 | -7.350000 | 0.534810 | 0.678571 | 6 | 1 | 1 |
| 2023-12 | 11 | -15.883333 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N5_W2_T2_SB1_TP10

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 251, entry dates 130, entry months 12; SKIP 29, EXCLUDED 100, exclusion share 0.284900; conditional FLAT CLOSED 251.
Net -139.950000 R; PF R / price 0.436405 / 0.366639; expectancy -0.557570 R; win rate 0.231076; average winner / loser 1.868391 / -1.335036 R.
Conditional CLOSED-only DD 139.950000 R; largest winner share 0.153799; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 26 | -19.950000 | 0.231214 | 0.311111 | 18 | 3 | 11 |
| 2023-02 | 19 | -11.816667 | 0.248941 | 0.264151 | 18 | 3 | 14 |
| 2023-03 | 13 | -14.816667 | 0.043057 | 0.038462 | 22 | 7 | 11 |
| 2023-04 | 14 | -3.216667 | 0.698437 | 0.764706 | 18 | 8 | 9 |
| 2023-05 | 24 | -9.300000 | 0.558544 | 0.536232 | 21 | 1 | 14 |
| 2023-06 | 20 | -19.000000 | 0.173913 | 0.173913 | 20 | 1 | 15 |
| 2023-07 | 27 | -20.883333 | 0.193175 | 0.166667 | 19 | 4 | 14 |
| 2023-08 | 47 | -12.766667 | 0.708524 | 0.651316 | 14 | 1 | 4 |
| 2023-09 | 30 | -6.116667 | 0.786504 | 0.247525 | 14 | 0 | 7 |
| 2023-10 | 8 | 1.150000 | 1.179687 | 1.590909 | 2 | 0 | 0 |
| 2023-11 | 12 | -7.350000 | 0.534810 | 0.678571 | 6 | 1 | 1 |
| 2023-12 | 11 | -15.883333 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N5_W2_T3_SB1_TP2

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 185, entry dates 112, entry months 12; SKIP 37, EXCLUDED 79, exclusion share 0.299242; conditional FLAT CLOSED 185.
Net -114.550000 R; PF R / price 0.378515 / 0.365573; expectancy -0.619189 R; win rate 0.232432; average winner / loser 1.622481 / -1.396338 R.
Conditional CLOSED-only DD 114.550000 R; largest winner share 0.047778; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 12 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 21 | -16.083333 | 0.257121 | 0.285714 | 18 | 5 | 11 |
| 2023-02 | 21 | -16.083333 | 0.157205 | 0.174603 | 18 | 4 | 9 |
| 2023-03 | 9 | -11.316667 | 0.021614 | 0.025641 | 22 | 7 | 11 |
| 2023-04 | 11 | -0.416667 | 0.941176 | 0.869565 | 18 | 8 | 7 |
| 2023-05 | 17 | -11.333333 | 0.352381 | 0.339286 | 21 | 4 | 11 |
| 2023-06 | 13 | -8.000000 | 0.314286 | 0.297297 | 20 | 1 | 14 |
| 2023-07 | 18 | -15.833333 | 0.240000 | 0.223881 | 19 | 3 | 9 |
| 2023-08 | 34 | -5.300000 | 0.821248 | 0.810000 | 14 | 2 | 1 |
| 2023-09 | 24 | -14.800000 | 0.357918 | 0.207792 | 14 | 1 | 5 |
| 2023-10 | 2 | -0.416667 | 0.750000 | 1.000000 | 2 | 1 | 0 |
| 2023-11 | 8 | -8.266667 | 0.253012 | 0.358974 | 6 | 1 | 1 |
| 2023-12 | 7 | -6.700000 | 0.294737 | 0.424242 | 0 | 0 | 0 |

### B_OPT2023_N5_W2_T3_SB1_TP3

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 185, entry dates 112, entry months 12; SKIP 37, EXCLUDED 79, exclusion share 0.299242; conditional FLAT CLOSED 185.
Net -110.333333 R; PF R / price 0.401393 / 0.365388; expectancy -0.596396 R; win rate 0.232432; average winner / loser 1.720543 / -1.396338 R.
Conditional CLOSED-only DD 110.333333 R; largest winner share 0.067583; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 12 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 21 | -14.416667 | 0.334103 | 0.357143 | 18 | 5 | 11 |
| 2023-02 | 21 | -16.083333 | 0.157205 | 0.174603 | 18 | 4 | 9 |
| 2023-03 | 9 | -11.316667 | 0.021614 | 0.025641 | 22 | 7 | 11 |
| 2023-04 | 11 | -0.083333 | 0.988235 | 0.913043 | 18 | 8 | 7 |
| 2023-05 | 17 | -12.333333 | 0.295238 | 0.285714 | 21 | 4 | 11 |
| 2023-06 | 13 | -8.000000 | 0.314286 | 0.297297 | 20 | 1 | 14 |
| 2023-07 | 18 | -15.833333 | 0.240000 | 0.223881 | 19 | 3 | 9 |
| 2023-08 | 34 | -6.550000 | 0.779089 | 0.760000 | 14 | 2 | 1 |
| 2023-09 | 24 | -13.133333 | 0.430224 | 0.214286 | 14 | 1 | 5 |
| 2023-10 | 2 | -0.416667 | 0.750000 | 1.000000 | 2 | 1 | 0 |
| 2023-11 | 8 | -6.866667 | 0.379518 | 0.538462 | 6 | 1 | 1 |
| 2023-12 | 7 | -5.300000 | 0.442105 | 0.636364 | 0 | 0 | 0 |

### B_OPT2023_N5_W2_T3_SB1_TP4

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 185, entry dates 112, entry months 12; SKIP 37, EXCLUDED 79, exclusion share 0.299242; conditional FLAT CLOSED 185.
Net -111.333333 R; PF R / price 0.400521 / 0.380089; expectancy -0.601802 R; win rate 0.227027; average winner / loser 1.771032 / -1.396366 R.
Conditional CLOSED-only DD 111.333333 R; largest winner share 0.089626; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 12 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 21 | -12.750000 | 0.411085 | 0.428571 | 18 | 5 | 11 |
| 2023-02 | 21 | -16.083333 | 0.157205 | 0.174603 | 18 | 4 | 9 |
| 2023-03 | 9 | -11.316667 | 0.021614 | 0.025641 | 22 | 7 | 11 |
| 2023-04 | 11 | -0.083333 | 0.988235 | 0.913043 | 18 | 8 | 7 |
| 2023-05 | 17 | -12.333333 | 0.295238 | 0.285714 | 21 | 4 | 11 |
| 2023-06 | 13 | -8.000000 | 0.314286 | 0.297297 | 20 | 1 | 14 |
| 2023-07 | 18 | -15.833333 | 0.240000 | 0.223881 | 19 | 3 | 9 |
| 2023-08 | 34 | -4.883333 | 0.835301 | 0.810000 | 14 | 2 | 1 |
| 2023-09 | 24 | -11.466667 | 0.502531 | 0.220779 | 14 | 1 | 5 |
| 2023-10 | 2 | -0.416667 | 0.750000 | 1.000000 | 2 | 1 | 0 |
| 2023-11 | 8 | -7.266667 | 0.343373 | 0.487179 | 6 | 1 | 1 |
| 2023-12 | 7 | -10.900000 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N5_W2_T3_SB1_TP5

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 185, entry dates 112, entry months 12; SKIP 37, EXCLUDED 79, exclusion share 0.299242; conditional FLAT CLOSED 185.
Net -112.000000 R; PF R / price 0.396931 / 0.368061; expectancy -0.605405 R; win rate 0.227027; average winner / loser 1.755159 / -1.396366 R.
Conditional CLOSED-only DD 112.000000 R; largest winner share 0.113045; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 12 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 21 | -16.750000 | 0.226328 | 0.257143 | 18 | 5 | 11 |
| 2023-02 | 21 | -16.083333 | 0.157205 | 0.174603 | 18 | 4 | 9 |
| 2023-03 | 9 | -11.316667 | 0.021614 | 0.025641 | 22 | 7 | 11 |
| 2023-04 | 11 | -0.083333 | 0.988235 | 0.913043 | 18 | 8 | 7 |
| 2023-05 | 17 | -12.333333 | 0.295238 | 0.285714 | 21 | 4 | 11 |
| 2023-06 | 13 | -8.000000 | 0.314286 | 0.297297 | 20 | 1 | 14 |
| 2023-07 | 18 | -15.833333 | 0.240000 | 0.223881 | 19 | 3 | 9 |
| 2023-08 | 34 | -3.216667 | 0.891512 | 0.860000 | 14 | 2 | 1 |
| 2023-09 | 24 | -9.800000 | 0.574837 | 0.227273 | 14 | 1 | 5 |
| 2023-10 | 2 | -0.416667 | 0.750000 | 1.000000 | 2 | 1 | 0 |
| 2023-11 | 8 | -7.266667 | 0.343373 | 0.487179 | 6 | 1 | 1 |
| 2023-12 | 7 | -10.900000 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N5_W2_T3_SB1_TP6

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 185, entry dates 112, entry months 12; SKIP 37, EXCLUDED 79, exclusion share 0.299242; conditional FLAT CLOSED 185.
Net -108.666667 R; PF R / price 0.414879 / 0.378238; expectancy -0.587387 R; win rate 0.227027; average winner / loser 1.834524 / -1.396366 R.
Conditional CLOSED-only DD 108.666667 R; largest winner share 0.129786; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 12 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 21 | -16.750000 | 0.226328 | 0.257143 | 18 | 5 | 11 |
| 2023-02 | 21 | -16.083333 | 0.157205 | 0.174603 | 18 | 4 | 9 |
| 2023-03 | 9 | -11.316667 | 0.021614 | 0.025641 | 22 | 7 | 11 |
| 2023-04 | 11 | -0.083333 | 0.988235 | 0.913043 | 18 | 8 | 7 |
| 2023-05 | 17 | -12.333333 | 0.295238 | 0.285714 | 21 | 4 | 11 |
| 2023-06 | 13 | -8.000000 | 0.314286 | 0.297297 | 20 | 1 | 14 |
| 2023-07 | 18 | -15.833333 | 0.240000 | 0.223881 | 19 | 3 | 9 |
| 2023-08 | 34 | -1.550000 | 0.947723 | 0.910000 | 14 | 2 | 1 |
| 2023-09 | 24 | -8.133333 | 0.647144 | 0.233766 | 14 | 1 | 5 |
| 2023-10 | 2 | -0.416667 | 0.750000 | 1.000000 | 2 | 1 | 0 |
| 2023-11 | 8 | -7.266667 | 0.343373 | 0.487179 | 6 | 1 | 1 |
| 2023-12 | 7 | -10.900000 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N5_W2_T3_SB1_TP7

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 185, entry dates 112, entry months 12; SKIP 37, EXCLUDED 79, exclusion share 0.299242; conditional FLAT CLOSED 185.
Net -105.333333 R; PF R / price 0.432828 / 0.388416; expectancy -0.569369 R; win rate 0.227027; average winner / loser 1.913889 / -1.396366 R.
Conditional CLOSED-only DD 105.333333 R; largest winner share 0.145138; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 21 | -16.750000 | 0.226328 | 0.257143 | 18 | 5 | 11 |
| 2023-02 | 21 | -16.083333 | 0.157205 | 0.174603 | 18 | 4 | 9 |
| 2023-03 | 9 | -11.316667 | 0.021614 | 0.025641 | 22 | 7 | 11 |
| 2023-04 | 11 | -0.083333 | 0.988235 | 0.913043 | 18 | 8 | 7 |
| 2023-05 | 17 | -12.333333 | 0.295238 | 0.285714 | 21 | 4 | 11 |
| 2023-06 | 13 | -8.000000 | 0.314286 | 0.297297 | 20 | 1 | 14 |
| 2023-07 | 18 | -15.833333 | 0.240000 | 0.223881 | 19 | 3 | 9 |
| 2023-08 | 34 | 0.116667 | 1.003935 | 0.960000 | 14 | 2 | 1 |
| 2023-09 | 24 | -6.466667 | 0.719450 | 0.240260 | 14 | 1 | 5 |
| 2023-10 | 2 | -0.416667 | 0.750000 | 1.000000 | 2 | 1 | 0 |
| 2023-11 | 8 | -7.266667 | 0.343373 | 0.487179 | 6 | 1 | 1 |
| 2023-12 | 7 | -10.900000 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N5_W2_T3_SB1_TP8

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 185, entry dates 112, entry months 12; SKIP 37, EXCLUDED 79, exclusion share 0.299242; conditional FLAT CLOSED 185.
Net -102.000000 R; PF R / price 0.450776 / 0.398594; expectancy -0.551351 R; win rate 0.227027; average winner / loser 1.993254 / -1.396366 R.
Conditional CLOSED-only DD 102.000000 R; largest winner share 0.159267; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 21 | -16.750000 | 0.226328 | 0.257143 | 18 | 5 | 11 |
| 2023-02 | 21 | -16.083333 | 0.157205 | 0.174603 | 18 | 4 | 9 |
| 2023-03 | 9 | -11.316667 | 0.021614 | 0.025641 | 22 | 7 | 11 |
| 2023-04 | 11 | -0.083333 | 0.988235 | 0.913043 | 18 | 8 | 7 |
| 2023-05 | 17 | -12.333333 | 0.295238 | 0.285714 | 21 | 4 | 11 |
| 2023-06 | 13 | -8.000000 | 0.314286 | 0.297297 | 20 | 1 | 14 |
| 2023-07 | 18 | -15.833333 | 0.240000 | 0.223881 | 19 | 3 | 9 |
| 2023-08 | 34 | 1.783333 | 1.060146 | 1.010000 | 14 | 2 | 1 |
| 2023-09 | 24 | -4.800000 | 0.791757 | 0.246753 | 14 | 1 | 5 |
| 2023-10 | 2 | -0.416667 | 0.750000 | 1.000000 | 2 | 1 | 0 |
| 2023-11 | 8 | -7.266667 | 0.343373 | 0.487179 | 6 | 1 | 1 |
| 2023-12 | 7 | -10.900000 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N5_W2_T3_SB1_TP9

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 185, entry dates 112, entry months 12; SKIP 37, EXCLUDED 79, exclusion share 0.299242; conditional FLAT CLOSED 185.
Net -98.666667 R; PF R / price 0.468725 / 0.408771; expectancy -0.533333 R; win rate 0.227027; average winner / loser 2.072619 / -1.396366 R.
Conditional CLOSED-only DD 98.666667 R; largest winner share 0.172315; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 21 | -16.750000 | 0.226328 | 0.257143 | 18 | 5 | 11 |
| 2023-02 | 21 | -16.083333 | 0.157205 | 0.174603 | 18 | 4 | 9 |
| 2023-03 | 9 | -11.316667 | 0.021614 | 0.025641 | 22 | 7 | 11 |
| 2023-04 | 11 | -0.083333 | 0.988235 | 0.913043 | 18 | 8 | 7 |
| 2023-05 | 17 | -12.333333 | 0.295238 | 0.285714 | 21 | 4 | 11 |
| 2023-06 | 13 | -8.000000 | 0.314286 | 0.297297 | 20 | 1 | 14 |
| 2023-07 | 18 | -15.833333 | 0.240000 | 0.223881 | 19 | 3 | 9 |
| 2023-08 | 34 | 3.450000 | 1.116358 | 1.060000 | 14 | 2 | 1 |
| 2023-09 | 24 | -3.133333 | 0.864064 | 0.253247 | 14 | 1 | 5 |
| 2023-10 | 2 | -0.416667 | 0.750000 | 1.000000 | 2 | 1 | 0 |
| 2023-11 | 8 | -7.266667 | 0.343373 | 0.487179 | 6 | 1 | 1 |
| 2023-12 | 7 | -10.900000 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N5_W2_T3_SB1_TP10

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 185, entry dates 112, entry months 12; SKIP 37, EXCLUDED 79, exclusion share 0.299242; conditional FLAT CLOSED 185.
Net -101.666667 R; PF R / price 0.452571 / 0.383790; expectancy -0.549550 R; win rate 0.227027; average winner / loser 2.001190 / -1.396366 R.
Conditional CLOSED-only DD 101.666667 R; largest winner share 0.198295; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 12 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 21 | -16.750000 | 0.226328 | 0.257143 | 18 | 5 | 11 |
| 2023-02 | 21 | -16.083333 | 0.157205 | 0.174603 | 18 | 4 | 9 |
| 2023-03 | 9 | -11.316667 | 0.021614 | 0.025641 | 22 | 7 | 11 |
| 2023-04 | 11 | -0.083333 | 0.988235 | 0.913043 | 18 | 8 | 7 |
| 2023-05 | 17 | -12.333333 | 0.295238 | 0.285714 | 21 | 4 | 11 |
| 2023-06 | 13 | -8.000000 | 0.314286 | 0.297297 | 20 | 1 | 14 |
| 2023-07 | 18 | -15.833333 | 0.240000 | 0.223881 | 19 | 3 | 9 |
| 2023-08 | 34 | -1.216667 | 0.958966 | 0.920000 | 14 | 2 | 1 |
| 2023-09 | 24 | -1.466667 | 0.936370 | 0.259740 | 14 | 1 | 5 |
| 2023-10 | 2 | -0.416667 | 0.750000 | 1.000000 | 2 | 1 | 0 |
| 2023-11 | 8 | -7.266667 | 0.343373 | 0.487179 | 6 | 1 | 1 |
| 2023-12 | 7 | -10.900000 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N5_W3_T2_SB1_TP2

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 275, entry dates 138, entry months 12; SKIP 27, EXCLUDED 100, exclusion share 0.266667; conditional FLAT CLOSED 275.
Net -124.633333 R; PF R / price 0.478849 / 0.374098; expectancy -0.453212 R; win rate 0.254545; average winner / loser 1.635952 / -1.252094 R.
Conditional CLOSED-only DD 125.933333 R; largest winner share 0.029108; largest positive month share 0.865217. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 23 | -13.250000 | 0.360418 | 0.358025 | 18 | 1 | 14 |
| 2023-02 | 20 | -10.183333 | 0.222646 | 0.227273 | 18 | 2 | 12 |
| 2023-03 | 12 | -12.733333 | 0.094787 | 0.083333 | 22 | 5 | 13 |
| 2023-04 | 16 | -4.100000 | 0.580205 | 0.676471 | 18 | 7 | 9 |
| 2023-05 | 26 | -7.100000 | 0.680899 | 0.680556 | 21 | 4 | 12 |
| 2023-06 | 19 | -11.166667 | 0.344423 | 0.321429 | 20 | 4 | 14 |
| 2023-07 | 32 | -23.533333 | 0.248936 | 0.261261 | 19 | 3 | 13 |
| 2023-08 | 49 | -19.683333 | 0.495083 | 0.463768 | 14 | 0 | 6 |
| 2023-09 | 29 | -17.450000 | 0.288239 | 0.164835 | 14 | 1 | 6 |
| 2023-10 | 15 | 0.516667 | 1.041779 | 1.170213 | 2 | 0 | 0 |
| 2023-11 | 21 | 3.316667 | 1.161395 | 1.333333 | 6 | 0 | 1 |
| 2023-12 | 13 | -9.266667 | 0.359447 | 0.481481 | 0 | 0 | 0 |

### B_OPT2023_N5_W3_T2_SB1_TP3

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 275, entry dates 138, entry months 12; SKIP 27, EXCLUDED 100, exclusion share 0.266667; conditional FLAT CLOSED 275.
Net -106.633333 R; PF R / price 0.556710 / 0.416558; expectancy -0.387758 R; win rate 0.250909; average winner / loser 1.940821 / -1.252865 R.
Conditional CLOSED-only DD 115.800000 R; largest winner share 0.037337; largest positive month share 0.635734. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 23 | -10.583333 | 0.489139 | 0.481481 | 18 | 1 | 14 |
| 2023-02 | 20 | -10.183333 | 0.222646 | 0.227273 | 18 | 2 | 12 |
| 2023-03 | 12 | -12.733333 | 0.094787 | 0.083333 | 22 | 5 | 13 |
| 2023-04 | 16 | -4.100000 | 0.580205 | 0.676471 | 18 | 7 | 9 |
| 2023-05 | 26 | -7.766667 | 0.650936 | 0.652778 | 21 | 4 | 12 |
| 2023-06 | 19 | -11.166667 | 0.344423 | 0.321429 | 20 | 4 | 14 |
| 2023-07 | 32 | -22.133333 | 0.293617 | 0.324324 | 19 | 3 | 13 |
| 2023-08 | 49 | -16.350000 | 0.580590 | 0.536232 | 14 | 0 | 6 |
| 2023-09 | 29 | -15.783333 | 0.356220 | 0.170330 | 14 | 1 | 6 |
| 2023-10 | 15 | 4.383333 | 1.354447 | 1.510638 | 2 | 0 | 0 |
| 2023-11 | 21 | 7.650000 | 1.348519 | 1.451220 | 6 | 0 | 1 |
| 2023-12 | 13 | -7.866667 | 0.456221 | 0.611111 | 0 | 0 | 0 |

### B_OPT2023_N5_W3_T2_SB1_TP4

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 274, entry dates 138, entry months 12; SKIP 27, EXCLUDED 100, exclusion share 0.267380; conditional FLAT CLOSED 274.
Net -95.966667 R; PF R / price 0.601053 / 0.428819; expectancy -0.350243 R; win rate 0.248175; average winner / loser 2.126225 / -1.252865 R.
Conditional CLOSED-only DD 114.683333 R; largest winner share 0.046110; largest positive month share 0.634801. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 23 | -8.916667 | 0.569590 | 0.543210 | 18 | 1 | 14 |
| 2023-02 | 20 | -10.183333 | 0.222646 | 0.227273 | 18 | 2 | 12 |
| 2023-03 | 12 | -12.733333 | 0.094787 | 0.083333 | 22 | 5 | 13 |
| 2023-04 | 16 | -4.100000 | 0.580205 | 0.676471 | 18 | 7 | 9 |
| 2023-05 | 26 | -7.766667 | 0.650936 | 0.652778 | 21 | 4 | 12 |
| 2023-06 | 19 | -11.166667 | 0.344423 | 0.321429 | 20 | 4 | 14 |
| 2023-07 | 32 | -22.733333 | 0.274468 | 0.297297 | 19 | 3 | 13 |
| 2023-08 | 49 | -15.016667 | 0.614793 | 0.565217 | 14 | 0 | 6 |
| 2023-09 | 29 | -14.116667 | 0.424201 | 0.175824 | 14 | 1 | 6 |
| 2023-10 | 14 | 8.850000 | 1.806991 | 2.075000 | 2 | 0 | 0 |
| 2023-11 | 21 | 15.383333 | 1.700835 | 1.804878 | 6 | 0 | 1 |
| 2023-12 | 13 | -13.466667 | 0.151261 | 0.196721 | 0 | 0 | 0 |

### B_OPT2023_N5_W3_T2_SB1_TP5

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 274, entry dates 138, entry months 12; SKIP 27, EXCLUDED 100, exclusion share 0.267380; conditional FLAT CLOSED 274.
Net -85.866667 R; PF R / price 0.643040 / 0.438915; expectancy -0.313382 R; win rate 0.248175; average winner / loser 2.274755 / -1.252865 R.
Conditional CLOSED-only DD 113.016667 R; largest winner share 0.053874; largest positive month share 0.657979. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 23 | -9.250000 | 0.553500 | 0.530864 | 18 | 1 | 14 |
| 2023-02 | 20 | -10.183333 | 0.222646 | 0.227273 | 18 | 2 | 12 |
| 2023-03 | 12 | -12.733333 | 0.094787 | 0.083333 | 22 | 5 | 13 |
| 2023-04 | 16 | -4.100000 | 0.580205 | 0.676471 | 18 | 7 | 9 |
| 2023-05 | 26 | -7.766667 | 0.650936 | 0.652778 | 21 | 4 | 12 |
| 2023-06 | 19 | -11.166667 | 0.344423 | 0.321429 | 20 | 4 | 14 |
| 2023-07 | 32 | -22.733333 | 0.274468 | 0.297297 | 19 | 3 | 13 |
| 2023-08 | 49 | -13.350000 | 0.657546 | 0.601449 | 14 | 0 | 6 |
| 2023-09 | 29 | -12.450000 | 0.492182 | 0.181319 | 14 | 1 | 6 |
| 2023-10 | 14 | 10.716667 | 1.977204 | 2.225000 | 2 | 0 | 0 |
| 2023-11 | 21 | 20.616667 | 1.939256 | 2.036585 | 6 | 0 | 1 |
| 2023-12 | 13 | -13.466667 | 0.151261 | 0.196721 | 0 | 0 | 0 |

### B_OPT2023_N5_W3_T2_SB1_TP6

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 274, entry dates 138, entry months 12; SKIP 27, EXCLUDED 100, exclusion share 0.267380; conditional FLAT CLOSED 274.
Net -78.833333 R; PF R / price 0.672279 / 0.447858; expectancy -0.287713 R; win rate 0.248175; average winner / loser 2.378186 / -1.252865 R.
Conditional CLOSED-only DD 111.350000 R; largest winner share 0.061837; largest positive month share 0.646527. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 23 | -9.250000 | 0.553500 | 0.530864 | 18 | 1 | 14 |
| 2023-02 | 20 | -10.183333 | 0.222646 | 0.227273 | 18 | 2 | 12 |
| 2023-03 | 12 | -12.733333 | 0.094787 | 0.083333 | 22 | 5 | 13 |
| 2023-04 | 16 | -4.100000 | 0.580205 | 0.676471 | 18 | 7 | 9 |
| 2023-05 | 26 | -7.766667 | 0.650936 | 0.652778 | 21 | 4 | 12 |
| 2023-06 | 19 | -11.166667 | 0.344423 | 0.321429 | 20 | 4 | 14 |
| 2023-07 | 32 | -22.733333 | 0.274468 | 0.297297 | 19 | 3 | 13 |
| 2023-08 | 49 | -11.683333 | 0.700299 | 0.637681 | 14 | 0 | 6 |
| 2023-09 | 29 | -10.783333 | 0.560163 | 0.186813 | 14 | 1 | 6 |
| 2023-10 | 14 | 12.383333 | 2.129179 | 2.350000 | 2 | 0 | 0 |
| 2023-11 | 21 | 22.650000 | 2.031891 | 2.060976 | 6 | 0 | 1 |
| 2023-12 | 13 | -13.466667 | 0.151261 | 0.196721 | 0 | 0 | 0 |

### B_OPT2023_N5_W3_T2_SB1_TP7

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 274, entry dates 138, entry months 12; SKIP 27, EXCLUDED 100, exclusion share 0.267380; conditional FLAT CLOSED 274.
Net -88.000000 R; PF R / price 0.636689 / 0.450995; expectancy -0.321168 R; win rate 0.244526; average winner / loser 2.301741 / -1.255009 R.
Conditional CLOSED-only DD 109.683333 R; largest winner share 0.075651; largest positive month share 0.627959. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 23 | -9.250000 | 0.553500 | 0.530864 | 18 | 1 | 14 |
| 2023-02 | 20 | -10.183333 | 0.222646 | 0.227273 | 18 | 2 | 12 |
| 2023-03 | 12 | -12.733333 | 0.094787 | 0.083333 | 22 | 5 | 13 |
| 2023-04 | 16 | -4.100000 | 0.580205 | 0.676471 | 18 | 7 | 9 |
| 2023-05 | 26 | -7.766667 | 0.650936 | 0.652778 | 21 | 4 | 12 |
| 2023-06 | 19 | -11.166667 | 0.344423 | 0.321429 | 20 | 4 | 14 |
| 2023-07 | 32 | -22.733333 | 0.274468 | 0.297297 | 19 | 3 | 13 |
| 2023-08 | 49 | -10.016667 | 0.743053 | 0.673913 | 14 | 0 | 6 |
| 2023-09 | 29 | -9.116667 | 0.628144 | 0.192308 | 14 | 1 | 6 |
| 2023-10 | 14 | 8.383333 | 1.764438 | 2.050000 | 2 | 0 | 0 |
| 2023-11 | 21 | 14.150000 | 1.599153 | 1.724138 | 6 | 0 | 1 |
| 2023-12 | 13 | -13.466667 | 0.151261 | 0.196721 | 0 | 0 | 0 |

### B_OPT2023_N5_W3_T2_SB1_TP8

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 274, entry dates 138, entry months 12; SKIP 27, EXCLUDED 100, exclusion share 0.267380; conditional FLAT CLOSED 274.
Net -91.250000 R; PF R / price 0.623271 / 0.455174; expectancy -0.333029 R; win rate 0.244526; average winner / loser 2.253234 / -1.255009 R.
Conditional CLOSED-only DD 108.016667 R; largest winner share 0.088320; largest positive month share 0.525601. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 23 | -9.250000 | 0.553500 | 0.530864 | 18 | 1 | 14 |
| 2023-02 | 20 | -10.183333 | 0.222646 | 0.227273 | 18 | 2 | 12 |
| 2023-03 | 12 | -12.733333 | 0.094787 | 0.083333 | 22 | 5 | 13 |
| 2023-04 | 16 | -4.100000 | 0.580205 | 0.676471 | 18 | 7 | 9 |
| 2023-05 | 26 | -7.766667 | 0.650936 | 0.652778 | 21 | 4 | 12 |
| 2023-06 | 19 | -11.166667 | 0.344423 | 0.321429 | 20 | 4 | 14 |
| 2023-07 | 32 | -22.733333 | 0.274468 | 0.297297 | 19 | 3 | 13 |
| 2023-08 | 49 | -8.350000 | 0.785806 | 0.710145 | 14 | 0 | 6 |
| 2023-09 | 29 | -7.450000 | 0.696125 | 0.197802 | 14 | 1 | 6 |
| 2023-10 | 14 | 8.383333 | 1.764438 | 2.050000 | 2 | 0 | 0 |
| 2023-11 | 21 | 7.566667 | 1.320395 | 1.425287 | 6 | 0 | 1 |
| 2023-12 | 13 | -13.466667 | 0.151261 | 0.196721 | 0 | 0 | 0 |

### B_OPT2023_N5_W3_T2_SB1_TP9

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 274, entry dates 138, entry months 12; SKIP 27, EXCLUDED 100, exclusion share 0.267380; conditional FLAT CLOSED 274.
Net -87.916667 R; PF R / price 0.637033 / 0.463102; expectancy -0.320864 R; win rate 0.244526; average winner / loser 2.302985 / -1.255009 R.
Conditional CLOSED-only DD 106.350000 R; largest winner share 0.097213; largest positive month share 0.525601. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 23 | -9.250000 | 0.553500 | 0.530864 | 18 | 1 | 14 |
| 2023-02 | 20 | -10.183333 | 0.222646 | 0.227273 | 18 | 2 | 12 |
| 2023-03 | 12 | -12.733333 | 0.094787 | 0.083333 | 22 | 5 | 13 |
| 2023-04 | 16 | -4.100000 | 0.580205 | 0.676471 | 18 | 7 | 9 |
| 2023-05 | 26 | -7.766667 | 0.650936 | 0.652778 | 21 | 4 | 12 |
| 2023-06 | 19 | -11.166667 | 0.344423 | 0.321429 | 20 | 4 | 14 |
| 2023-07 | 32 | -22.733333 | 0.274468 | 0.297297 | 19 | 3 | 13 |
| 2023-08 | 49 | -6.683333 | 0.828559 | 0.746377 | 14 | 0 | 6 |
| 2023-09 | 29 | -5.783333 | 0.764106 | 0.203297 | 14 | 1 | 6 |
| 2023-10 | 14 | 8.383333 | 1.764438 | 2.050000 | 2 | 0 | 0 |
| 2023-11 | 21 | 7.566667 | 1.320395 | 1.425287 | 6 | 0 | 1 |
| 2023-12 | 13 | -13.466667 | 0.151261 | 0.196721 | 0 | 0 | 0 |

### B_OPT2023_N5_W3_T2_SB1_TP10

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 274, entry dates 138, entry months 12; SKIP 27, EXCLUDED 100, exclusion share 0.267380; conditional FLAT CLOSED 274.
Net -90.916667 R; PF R / price 0.624647 / 0.443644; expectancy -0.331813 R; win rate 0.244526; average winner / loser 2.258209 / -1.255009 R.
Conditional CLOSED-only DD 111.016667 R; largest winner share 0.110156; largest positive month share 0.525601. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 23 | -9.250000 | 0.553500 | 0.530864 | 18 | 1 | 14 |
| 2023-02 | 20 | -10.183333 | 0.222646 | 0.227273 | 18 | 2 | 12 |
| 2023-03 | 12 | -12.733333 | 0.094787 | 0.083333 | 22 | 5 | 13 |
| 2023-04 | 16 | -4.100000 | 0.580205 | 0.676471 | 18 | 7 | 9 |
| 2023-05 | 26 | -7.766667 | 0.650936 | 0.652778 | 21 | 4 | 12 |
| 2023-06 | 19 | -11.166667 | 0.344423 | 0.321429 | 20 | 4 | 14 |
| 2023-07 | 32 | -22.733333 | 0.274468 | 0.297297 | 19 | 3 | 13 |
| 2023-08 | 49 | -11.350000 | 0.708850 | 0.644928 | 14 | 0 | 6 |
| 2023-09 | 29 | -4.116667 | 0.832087 | 0.208791 | 14 | 1 | 6 |
| 2023-10 | 14 | 8.383333 | 1.764438 | 2.050000 | 2 | 0 | 0 |
| 2023-11 | 21 | 7.566667 | 1.320395 | 1.425287 | 6 | 0 | 1 |
| 2023-12 | 13 | -13.466667 | 0.151261 | 0.196721 | 0 | 0 | 0 |

### B_OPT2023_N5_W3_T3_SB1_TP2

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 209, entry dates 128, entry months 12; SKIP 33, EXCLUDED 81, exclusion share 0.279310; conditional FLAT CLOSED 209.
Net -108.350000 R; PF R / price 0.433019 / 0.341537; expectancy -0.518421 R; win rate 0.220096; average winner / loser 1.798913 / -1.274000 R.
Conditional CLOSED-only DD 109.650000 R; largest winner share 0.040282; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 20 | -10.283333 | 0.376138 | 0.385965 | 18 | 3 | 11 |
| 2023-02 | 22 | -16.533333 | 0.107914 | 0.114754 | 18 | 4 | 9 |
| 2023-03 | 9 | -10.733333 | 0.058480 | 0.050000 | 22 | 3 | 12 |
| 2023-04 | 13 | -0.433333 | 0.935162 | 0.826087 | 18 | 7 | 6 |
| 2023-05 | 21 | -11.900000 | 0.383952 | 0.375000 | 21 | 7 | 10 |
| 2023-06 | 13 | -11.000000 | 0.214286 | 0.200000 | 20 | 2 | 11 |
| 2023-07 | 21 | -10.150000 | 0.457219 | 0.507937 | 19 | 4 | 11 |
| 2023-08 | 37 | -21.066667 | 0.422567 | 0.400000 | 14 | 2 | 4 |
| 2023-09 | 25 | -13.550000 | 0.390098 | 0.220779 | 14 | 0 | 6 |
| 2023-10 | 5 | 4.316667 | 2.407609 | 2.416667 | 2 | 1 | 0 |
| 2023-11 | 16 | -6.200000 | 0.651685 | 0.838710 | 6 | 0 | 1 |
| 2023-12 | 7 | -0.816667 | 0.872727 | 1.166667 | 0 | 0 | 0 |

### B_OPT2023_N5_W3_T3_SB1_TP3

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 209, entry dates 128, entry months 12; SKIP 33, EXCLUDED 81, exclusion share 0.279310; conditional FLAT CLOSED 209.
Net -92.533333 R; PF R / price 0.515786 / 0.367564; expectancy -0.442743 R; win rate 0.220096; average winner / loser 2.142754 / -1.274000 R.
Conditional CLOSED-only DD 106.500000 R; largest winner share 0.050727; largest positive month share 0.788256. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 20 | -8.616667 | 0.477250 | 0.473684 | 18 | 3 | 11 |
| 2023-02 | 22 | -16.533333 | 0.107914 | 0.114754 | 18 | 4 | 9 |
| 2023-03 | 9 | -10.733333 | 0.058480 | 0.050000 | 22 | 3 | 12 |
| 2023-04 | 13 | -0.433333 | 0.935162 | 0.826087 | 18 | 7 | 6 |
| 2023-05 | 21 | -12.900000 | 0.332183 | 0.328125 | 21 | 7 | 10 |
| 2023-06 | 13 | -11.000000 | 0.214286 | 0.200000 | 20 | 2 | 11 |
| 2023-07 | 21 | -8.750000 | 0.532086 | 0.619048 | 19 | 4 | 11 |
| 2023-08 | 37 | -20.650000 | 0.433988 | 0.400000 | 14 | 2 | 4 |
| 2023-09 | 25 | -11.883333 | 0.465116 | 0.227273 | 14 | 0 | 6 |
| 2023-10 | 5 | 7.383333 | 3.407609 | 3.416667 | 2 | 1 | 0 |
| 2023-11 | 16 | -0.400000 | 0.977528 | 1.258065 | 6 | 0 | 1 |
| 2023-12 | 7 | 1.983333 | 1.309091 | 1.750000 | 0 | 0 | 0 |

### B_OPT2023_N5_W3_T3_SB1_TP4

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 209, entry dates 128, entry months 12; SKIP 33, EXCLUDED 81, exclusion share 0.279310; conditional FLAT CLOSED 209.
Net -98.866667 R; PF R / price 0.493770 / 0.372552; expectancy -0.473046 R; win rate 0.205742; average winner / loser 2.242636 / -1.276471 R.
Conditional CLOSED-only DD 104.700000 R; largest winner share 0.069132; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 20 | -6.950000 | 0.578362 | 0.561404 | 18 | 3 | 11 |
| 2023-02 | 22 | -16.533333 | 0.107914 | 0.114754 | 18 | 4 | 9 |
| 2023-03 | 9 | -10.733333 | 0.058480 | 0.050000 | 22 | 3 | 12 |
| 2023-04 | 13 | -0.433333 | 0.935162 | 0.826087 | 18 | 7 | 6 |
| 2023-05 | 21 | -12.900000 | 0.332183 | 0.328125 | 21 | 7 | 10 |
| 2023-06 | 13 | -11.000000 | 0.214286 | 0.200000 | 20 | 2 | 11 |
| 2023-07 | 21 | -9.350000 | 0.500000 | 0.571429 | 19 | 4 | 11 |
| 2023-08 | 37 | -18.983333 | 0.479671 | 0.440000 | 14 | 2 | 4 |
| 2023-09 | 25 | -10.216667 | 0.540135 | 0.233766 | 14 | 0 | 6 |
| 2023-10 | 5 | 10.450000 | 4.407609 | 4.416667 | 2 | 1 | 0 |
| 2023-11 | 16 | -3.000000 | 0.843750 | 1.000000 | 6 | 0 | 1 |
| 2023-12 | 7 | -9.216667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N5_W3_T3_SB1_TP5

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 209, entry dates 128, entry months 12; SKIP 33, EXCLUDED 81, exclusion share 0.279310; conditional FLAT CLOSED 209.
Net -93.500000 R; PF R / price 0.521249 / 0.381902; expectancy -0.447368 R; win rate 0.205742; average winner / loser 2.367442 / -1.276471 R.
Conditional CLOSED-only DD 103.033333 R; largest winner share 0.081860; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 20 | -7.283333 | 0.558140 | 0.543860 | 18 | 3 | 11 |
| 2023-02 | 22 | -16.533333 | 0.107914 | 0.114754 | 18 | 4 | 9 |
| 2023-03 | 9 | -10.733333 | 0.058480 | 0.050000 | 22 | 3 | 12 |
| 2023-04 | 13 | -0.433333 | 0.935162 | 0.826087 | 18 | 7 | 6 |
| 2023-05 | 21 | -12.900000 | 0.332183 | 0.328125 | 21 | 7 | 10 |
| 2023-06 | 13 | -11.000000 | 0.214286 | 0.200000 | 20 | 2 | 11 |
| 2023-07 | 21 | -9.350000 | 0.500000 | 0.571429 | 19 | 4 | 11 |
| 2023-08 | 37 | -17.316667 | 0.525354 | 0.480000 | 14 | 2 | 4 |
| 2023-09 | 25 | -8.550000 | 0.615154 | 0.240260 | 14 | 0 | 6 |
| 2023-10 | 5 | 12.316667 | 5.016304 | 4.916667 | 2 | 1 | 0 |
| 2023-11 | 16 | -2.500000 | 0.869792 | 1.028986 | 6 | 0 | 1 |
| 2023-12 | 7 | -9.216667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N5_W3_T3_SB1_TP6

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 209, entry dates 128, entry months 12; SKIP 33, EXCLUDED 81, exclusion share 0.279310; conditional FLAT CLOSED 209.
Net -88.250000 R; PF R / price 0.548131 / 0.392662; expectancy -0.422249 R; win rate 0.205742; average winner / loser 2.489535 / -1.276471 R.
Conditional CLOSED-only DD 101.366667 R; largest winner share 0.093414; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 20 | -7.283333 | 0.558140 | 0.543860 | 18 | 3 | 11 |
| 2023-02 | 22 | -16.533333 | 0.107914 | 0.114754 | 18 | 4 | 9 |
| 2023-03 | 9 | -10.733333 | 0.058480 | 0.050000 | 22 | 3 | 12 |
| 2023-04 | 13 | -0.433333 | 0.935162 | 0.826087 | 18 | 7 | 6 |
| 2023-05 | 21 | -12.900000 | 0.332183 | 0.328125 | 21 | 7 | 10 |
| 2023-06 | 13 | -11.000000 | 0.214286 | 0.200000 | 20 | 2 | 11 |
| 2023-07 | 21 | -9.350000 | 0.500000 | 0.571429 | 19 | 4 | 11 |
| 2023-08 | 37 | -15.650000 | 0.571037 | 0.520000 | 14 | 2 | 4 |
| 2023-09 | 25 | -6.883333 | 0.690173 | 0.246753 | 14 | 0 | 6 |
| 2023-10 | 5 | 13.983333 | 5.559783 | 5.333333 | 2 | 1 | 0 |
| 2023-11 | 16 | -2.250000 | 0.882812 | 1.043478 | 6 | 0 | 1 |
| 2023-12 | 7 | -9.216667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N5_W3_T3_SB1_TP7

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 209, entry dates 128, entry months 12; SKIP 33, EXCLUDED 81, exclusion share 0.279310; conditional FLAT CLOSED 209.
Net -88.916667 R; PF R / price 0.544718 / 0.400247; expectancy -0.425439 R; win rate 0.205742; average winner / loser 2.474031 / -1.276471 R.
Conditional CLOSED-only DD 99.700000 R; largest winner share 0.109666; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 20 | -7.283333 | 0.558140 | 0.543860 | 18 | 3 | 11 |
| 2023-02 | 22 | -16.533333 | 0.107914 | 0.114754 | 18 | 4 | 9 |
| 2023-03 | 9 | -10.733333 | 0.058480 | 0.050000 | 22 | 3 | 12 |
| 2023-04 | 13 | -0.433333 | 0.935162 | 0.826087 | 18 | 7 | 6 |
| 2023-05 | 21 | -12.900000 | 0.332183 | 0.328125 | 21 | 7 | 10 |
| 2023-06 | 13 | -11.000000 | 0.214286 | 0.200000 | 20 | 2 | 11 |
| 2023-07 | 21 | -9.350000 | 0.500000 | 0.571429 | 19 | 4 | 11 |
| 2023-08 | 37 | -13.983333 | 0.616720 | 0.560000 | 14 | 2 | 4 |
| 2023-09 | 25 | -5.216667 | 0.765191 | 0.253247 | 14 | 0 | 6 |
| 2023-10 | 5 | 9.983333 | 4.255435 | 4.333333 | 2 | 1 | 0 |
| 2023-11 | 16 | -2.250000 | 0.882812 | 1.043478 | 6 | 0 | 1 |
| 2023-12 | 7 | -9.216667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N5_W3_T3_SB1_TP8

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 209, entry dates 128, entry months 12; SKIP 33, EXCLUDED 81, exclusion share 0.279310; conditional FLAT CLOSED 209.
Net -85.583333 R; PF R / price 0.561785 / 0.409949; expectancy -0.409490 R; win rate 0.205742; average winner / loser 2.551550 / -1.276471 R.
Conditional CLOSED-only DD 98.033333 R; largest winner share 0.121525; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 20 | -7.283333 | 0.558140 | 0.543860 | 18 | 3 | 11 |
| 2023-02 | 22 | -16.533333 | 0.107914 | 0.114754 | 18 | 4 | 9 |
| 2023-03 | 9 | -10.733333 | 0.058480 | 0.050000 | 22 | 3 | 12 |
| 2023-04 | 13 | -0.433333 | 0.935162 | 0.826087 | 18 | 7 | 6 |
| 2023-05 | 21 | -12.900000 | 0.332183 | 0.328125 | 21 | 7 | 10 |
| 2023-06 | 13 | -11.000000 | 0.214286 | 0.200000 | 20 | 2 | 11 |
| 2023-07 | 21 | -9.350000 | 0.500000 | 0.571429 | 19 | 4 | 11 |
| 2023-08 | 37 | -12.316667 | 0.662403 | 0.600000 | 14 | 2 | 4 |
| 2023-09 | 25 | -3.550000 | 0.840210 | 0.259740 | 14 | 0 | 6 |
| 2023-10 | 5 | 9.983333 | 4.255435 | 4.333333 | 2 | 1 | 0 |
| 2023-11 | 16 | -2.250000 | 0.882812 | 1.043478 | 6 | 0 | 1 |
| 2023-12 | 7 | -9.216667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N5_W3_T3_SB1_TP9

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 209, entry dates 128, entry months 12; SKIP 33, EXCLUDED 81, exclusion share 0.279310; conditional FLAT CLOSED 209.
Net -82.250000 R; PF R / price 0.578853 / 0.419651; expectancy -0.393541 R; win rate 0.205742; average winner / loser 2.629070 / -1.276471 R.
Conditional CLOSED-only DD 96.366667 R; largest winner share 0.132685; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 20 | -7.283333 | 0.558140 | 0.543860 | 18 | 3 | 11 |
| 2023-02 | 22 | -16.533333 | 0.107914 | 0.114754 | 18 | 4 | 9 |
| 2023-03 | 9 | -10.733333 | 0.058480 | 0.050000 | 22 | 3 | 12 |
| 2023-04 | 13 | -0.433333 | 0.935162 | 0.826087 | 18 | 7 | 6 |
| 2023-05 | 21 | -12.900000 | 0.332183 | 0.328125 | 21 | 7 | 10 |
| 2023-06 | 13 | -11.000000 | 0.214286 | 0.200000 | 20 | 2 | 11 |
| 2023-07 | 21 | -9.350000 | 0.500000 | 0.571429 | 19 | 4 | 11 |
| 2023-08 | 37 | -10.650000 | 0.708086 | 0.640000 | 14 | 2 | 4 |
| 2023-09 | 25 | -1.883333 | 0.915229 | 0.266234 | 14 | 0 | 6 |
| 2023-10 | 5 | 9.983333 | 4.255435 | 4.333333 | 2 | 1 | 0 |
| 2023-11 | 16 | -2.250000 | 0.882812 | 1.043478 | 6 | 0 | 1 |
| 2023-12 | 7 | -9.216667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N5_W3_T3_SB1_TP10

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 209, entry dates 128, entry months 12; SKIP 33, EXCLUDED 81, exclusion share 0.279310; conditional FLAT CLOSED 209.
Net -85.250000 R; PF R / price 0.563492 / 0.395837; expectancy -0.407895 R; win rate 0.205742; average winner / loser 2.559302 / -1.276471 R.
Conditional CLOSED-only DD 101.033333 R; largest winner share 0.151446; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 20 | -7.283333 | 0.558140 | 0.543860 | 18 | 3 | 11 |
| 2023-02 | 22 | -16.533333 | 0.107914 | 0.114754 | 18 | 4 | 9 |
| 2023-03 | 9 | -10.733333 | 0.058480 | 0.050000 | 22 | 3 | 12 |
| 2023-04 | 13 | -0.433333 | 0.935162 | 0.826087 | 18 | 7 | 6 |
| 2023-05 | 21 | -12.900000 | 0.332183 | 0.328125 | 21 | 7 | 10 |
| 2023-06 | 13 | -11.000000 | 0.214286 | 0.200000 | 20 | 2 | 11 |
| 2023-07 | 21 | -9.350000 | 0.500000 | 0.571429 | 19 | 4 | 11 |
| 2023-08 | 37 | -15.316667 | 0.580174 | 0.528000 | 14 | 2 | 4 |
| 2023-09 | 25 | -0.216667 | 0.990248 | 0.272727 | 14 | 0 | 6 |
| 2023-10 | 5 | 9.983333 | 4.255435 | 4.333333 | 2 | 1 | 0 |
| 2023-11 | 16 | -2.250000 | 0.882812 | 1.043478 | 6 | 0 | 1 |
| 2023-12 | 7 | -9.216667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N6_W2_T2_SB1_TP2

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 228, entry dates 119, entry months 12; SKIP 27, EXCLUDED 94, exclusion share 0.291925; conditional FLAT CLOSED 218.
Net -132.850000 R; PF R / price 0.379834 / 0.325188; expectancy -0.582675 R; win rate 0.236842; average winner / loser 1.506790 / -1.306199 R.
Conditional CLOSED-only DD 143.550000 R; largest winner share 0.040967; largest positive month share 0.857143. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 31 | -30.466667 | 0.123261 | 0.123894 | 18 | 4 | 5 |
| 2023-02 | 23 | -20.883333 | 0.097262 | 0.103896 | 18 | 5 | 11 |
| 2023-03 | 11 | -10.566667 | 0.130316 | 0.116279 | 22 | 4 | 13 |
| 2023-04 | 17 | -6.166667 | 0.554217 | 0.555556 | 18 | 5 | 9 |
| 2023-05 | 18 | -10.483333 | 0.435368 | 0.416667 | 21 | 3 | 13 |
| 2023-06 | 18 | -13.483333 | 0.273788 | 0.258065 | 20 | 0 | 16 |
| 2023-07 | 26 | -16.750000 | 0.322776 | 0.373494 | 19 | 3 | 15 |
| 2023-08 | 42 | -9.000000 | 0.737354 | 0.655738 | 14 | 3 | 4 |
| 2023-09 | 33 | -23.900000 | 0.198435 | 0.195876 | 14 | 0 | 7 |
| 2023-10 | 2 | -0.250000 | 0.833333 | 0.833333 | 2 | 0 | 0 |
| 2023-11 | 5 | 7.800000 | 6.571429 | 5.714286 | 6 | 0 | 1 |
| 2023-12 | 2 | 1.300000 | 1.866667 | 2.333333 | 0 | 0 | 0 |

### B_OPT2023_N6_W2_T2_SB1_TP3

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 228, entry dates 119, entry months 12; SKIP 27, EXCLUDED 94, exclusion share 0.291925; conditional FLAT CLOSED 218.
Net -125.083333 R; PF R / price 0.416544 / 0.348556; expectancy -0.548611 R; win rate 0.236842; average winner / loser 1.653704 / -1.307215 R.
Conditional CLOSED-only DD 139.983333 R; largest winner share 0.055991; largest positive month share 0.796992. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 31 | -28.800000 | 0.171223 | 0.168142 | 18 | 4 | 5 |
| 2023-02 | 23 | -20.883333 | 0.097262 | 0.103896 | 18 | 5 | 11 |
| 2023-03 | 11 | -10.566667 | 0.130316 | 0.116279 | 22 | 4 | 13 |
| 2023-04 | 17 | -4.500000 | 0.674699 | 0.666667 | 18 | 5 | 9 |
| 2023-05 | 18 | -11.483333 | 0.381508 | 0.366667 | 21 | 3 | 13 |
| 2023-06 | 18 | -13.483333 | 0.273788 | 0.258065 | 20 | 0 | 16 |
| 2023-07 | 26 | -15.350000 | 0.379380 | 0.457831 | 19 | 3 | 15 |
| 2023-08 | 42 | -9.166667 | 0.733785 | 0.661157 | 14 | 3 | 4 |
| 2023-09 | 33 | -23.900000 | 0.198435 | 0.195876 | 14 | 0 | 7 |
| 2023-10 | 2 | -0.250000 | 0.833333 | 0.833333 | 2 | 0 | 0 |
| 2023-11 | 5 | 10.600000 | 8.571429 | 7.714286 | 6 | 0 | 1 |
| 2023-12 | 2 | 2.700000 | 2.800000 | 3.500000 | 0 | 0 | 0 |

### B_OPT2023_N6_W2_T2_SB1_TP4

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 228, entry dates 119, entry months 12; SKIP 27, EXCLUDED 94, exclusion share 0.291925; conditional FLAT CLOSED 218.
Net -129.150000 R; PF R / price 0.401483 / 0.345935; expectancy -0.566447 R; win rate 0.232456; average winner / loser 1.634591 / -1.307778 R.
Conditional CLOSED-only DD 139.450000 R; largest winner share 0.076953; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 31 | -27.133333 | 0.219185 | 0.212389 | 18 | 4 | 5 |
| 2023-02 | 23 | -20.883333 | 0.097262 | 0.103896 | 18 | 5 | 11 |
| 2023-03 | 11 | -10.566667 | 0.130316 | 0.116279 | 22 | 4 | 13 |
| 2023-04 | 17 | -4.500000 | 0.674699 | 0.666667 | 18 | 5 | 9 |
| 2023-05 | 18 | -11.483333 | 0.381508 | 0.366667 | 21 | 3 | 13 |
| 2023-06 | 18 | -13.483333 | 0.273788 | 0.258065 | 20 | 0 | 16 |
| 2023-07 | 26 | -16.150000 | 0.347035 | 0.409639 | 19 | 3 | 15 |
| 2023-08 | 42 | -9.500000 | 0.724105 | 0.652893 | 14 | 3 | 4 |
| 2023-09 | 33 | -23.900000 | 0.198435 | 0.195876 | 14 | 0 | 7 |
| 2023-10 | 2 | -0.250000 | 0.833333 | 0.833333 | 2 | 0 | 0 |
| 2023-11 | 5 | 11.600000 | 9.285714 | 8.428571 | 6 | 0 | 1 |
| 2023-12 | 2 | -2.900000 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N6_W2_T2_SB1_TP5

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 228, entry dates 119, entry months 12; SKIP 27, EXCLUDED 94, exclusion share 0.291925; conditional FLAT CLOSED 218.
Net -132.750000 R; PF R / price 0.384800 / 0.325611; expectancy -0.582237 R; win rate 0.232456; average winner / loser 1.566667 / -1.307778 R.
Conditional CLOSED-only DD 144.450000 R; largest winner share 0.084303; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 31 | -32.133333 | 0.075300 | 0.079646 | 18 | 4 | 5 |
| 2023-02 | 23 | -20.883333 | 0.097262 | 0.103896 | 18 | 5 | 11 |
| 2023-03 | 11 | -10.566667 | 0.130316 | 0.116279 | 22 | 4 | 13 |
| 2023-04 | 17 | -4.500000 | 0.674699 | 0.666667 | 18 | 5 | 9 |
| 2023-05 | 18 | -11.483333 | 0.381508 | 0.366667 | 21 | 3 | 13 |
| 2023-06 | 18 | -13.483333 | 0.273788 | 0.258065 | 20 | 0 | 16 |
| 2023-07 | 26 | -16.150000 | 0.347035 | 0.409639 | 19 | 3 | 15 |
| 2023-08 | 42 | -9.500000 | 0.724105 | 0.652893 | 14 | 3 | 4 |
| 2023-09 | 33 | -23.900000 | 0.198435 | 0.195876 | 14 | 0 | 7 |
| 2023-10 | 2 | -0.250000 | 0.833333 | 0.833333 | 2 | 0 | 0 |
| 2023-11 | 5 | 13.000000 | 10.285714 | 9.428571 | 6 | 0 | 1 |
| 2023-12 | 2 | -2.900000 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N6_W2_T2_SB1_TP6

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 228, entry dates 119, entry months 12; SKIP 27, EXCLUDED 94, exclusion share 0.291925; conditional FLAT CLOSED 218.
Net -131.350000 R; PF R / price 0.391288 / 0.326606; expectancy -0.576096 R; win rate 0.232456; average winner / loser 1.593082 / -1.307778 R.
Conditional CLOSED-only DD 144.450000 R; largest winner share 0.099487; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 31 | -32.133333 | 0.075300 | 0.079646 | 18 | 4 | 5 |
| 2023-02 | 23 | -20.883333 | 0.097262 | 0.103896 | 18 | 5 | 11 |
| 2023-03 | 11 | -10.566667 | 0.130316 | 0.116279 | 22 | 4 | 13 |
| 2023-04 | 17 | -4.500000 | 0.674699 | 0.666667 | 18 | 5 | 9 |
| 2023-05 | 18 | -11.483333 | 0.381508 | 0.366667 | 21 | 3 | 13 |
| 2023-06 | 18 | -13.483333 | 0.273788 | 0.258065 | 20 | 0 | 16 |
| 2023-07 | 26 | -16.150000 | 0.347035 | 0.409639 | 19 | 3 | 15 |
| 2023-08 | 42 | -9.500000 | 0.724105 | 0.652893 | 14 | 3 | 4 |
| 2023-09 | 33 | -23.900000 | 0.198435 | 0.195876 | 14 | 0 | 7 |
| 2023-10 | 2 | -0.250000 | 0.833333 | 0.833333 | 2 | 0 | 0 |
| 2023-11 | 5 | 14.400000 | 11.285714 | 10.428571 | 6 | 0 | 1 |
| 2023-12 | 2 | -2.900000 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N6_W2_T2_SB1_TP7

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 228, entry dates 119, entry months 12; SKIP 27, EXCLUDED 94, exclusion share 0.291925; conditional FLAT CLOSED 218.
Net -129.950000 R; PF R / price 0.397776 / 0.327601; expectancy -0.569956 R; win rate 0.232456; average winner / loser 1.619497 / -1.307778 R.
Conditional CLOSED-only DD 144.450000 R; largest winner share 0.114175; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 31 | -32.133333 | 0.075300 | 0.079646 | 18 | 4 | 5 |
| 2023-02 | 23 | -20.883333 | 0.097262 | 0.103896 | 18 | 5 | 11 |
| 2023-03 | 11 | -10.566667 | 0.130316 | 0.116279 | 22 | 4 | 13 |
| 2023-04 | 17 | -4.500000 | 0.674699 | 0.666667 | 18 | 5 | 9 |
| 2023-05 | 18 | -11.483333 | 0.381508 | 0.366667 | 21 | 3 | 13 |
| 2023-06 | 18 | -13.483333 | 0.273788 | 0.258065 | 20 | 0 | 16 |
| 2023-07 | 26 | -16.150000 | 0.347035 | 0.409639 | 19 | 3 | 15 |
| 2023-08 | 42 | -9.500000 | 0.724105 | 0.652893 | 14 | 3 | 4 |
| 2023-09 | 33 | -23.900000 | 0.198435 | 0.195876 | 14 | 0 | 7 |
| 2023-10 | 2 | -0.250000 | 0.833333 | 0.833333 | 2 | 0 | 0 |
| 2023-11 | 5 | 15.800000 | 12.285714 | 11.428571 | 6 | 0 | 1 |
| 2023-12 | 2 | -2.900000 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N6_W2_T2_SB1_TP8

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 228, entry dates 119, entry months 12; SKIP 27, EXCLUDED 94, exclusion share 0.291925; conditional FLAT CLOSED 218.
Net -129.150000 R; PF R / price 0.401483 / 0.328169; expectancy -0.566447 R; win rate 0.232456; average winner / loser 1.634591 / -1.307778 R.
Conditional CLOSED-only DD 144.450000 R; largest winner share 0.122355; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 31 | -32.133333 | 0.075300 | 0.079646 | 18 | 4 | 5 |
| 2023-02 | 23 | -20.883333 | 0.097262 | 0.103896 | 18 | 5 | 11 |
| 2023-03 | 11 | -10.566667 | 0.130316 | 0.116279 | 22 | 4 | 13 |
| 2023-04 | 17 | -4.500000 | 0.674699 | 0.666667 | 18 | 5 | 9 |
| 2023-05 | 18 | -11.483333 | 0.381508 | 0.366667 | 21 | 3 | 13 |
| 2023-06 | 18 | -13.483333 | 0.273788 | 0.258065 | 20 | 0 | 16 |
| 2023-07 | 26 | -16.150000 | 0.347035 | 0.409639 | 19 | 3 | 15 |
| 2023-08 | 42 | -9.500000 | 0.724105 | 0.652893 | 14 | 3 | 4 |
| 2023-09 | 33 | -23.900000 | 0.198435 | 0.195876 | 14 | 0 | 7 |
| 2023-10 | 2 | -0.250000 | 0.833333 | 0.833333 | 2 | 0 | 0 |
| 2023-11 | 5 | 16.600000 | 12.857143 | 12.000000 | 6 | 0 | 1 |
| 2023-12 | 2 | -2.900000 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N6_W2_T2_SB1_TP9

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 228, entry dates 119, entry months 12; SKIP 27, EXCLUDED 94, exclusion share 0.291925; conditional FLAT CLOSED 218.
Net -129.150000 R; PF R / price 0.401483 / 0.328169; expectancy -0.566447 R; win rate 0.232456; average winner / loser 1.634591 / -1.307778 R.
Conditional CLOSED-only DD 144.450000 R; largest winner share 0.122355; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 31 | -32.133333 | 0.075300 | 0.079646 | 18 | 4 | 5 |
| 2023-02 | 23 | -20.883333 | 0.097262 | 0.103896 | 18 | 5 | 11 |
| 2023-03 | 11 | -10.566667 | 0.130316 | 0.116279 | 22 | 4 | 13 |
| 2023-04 | 17 | -4.500000 | 0.674699 | 0.666667 | 18 | 5 | 9 |
| 2023-05 | 18 | -11.483333 | 0.381508 | 0.366667 | 21 | 3 | 13 |
| 2023-06 | 18 | -13.483333 | 0.273788 | 0.258065 | 20 | 0 | 16 |
| 2023-07 | 26 | -16.150000 | 0.347035 | 0.409639 | 19 | 3 | 15 |
| 2023-08 | 42 | -9.500000 | 0.724105 | 0.652893 | 14 | 3 | 4 |
| 2023-09 | 33 | -23.900000 | 0.198435 | 0.195876 | 14 | 0 | 7 |
| 2023-10 | 2 | -0.250000 | 0.833333 | 0.833333 | 2 | 0 | 0 |
| 2023-11 | 5 | 16.600000 | 12.857143 | 12.000000 | 6 | 0 | 1 |
| 2023-12 | 2 | -2.900000 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N6_W2_T2_SB1_TP10

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 228, entry dates 119, entry months 12; SKIP 27, EXCLUDED 94, exclusion share 0.291925; conditional FLAT CLOSED 218.
Net -129.150000 R; PF R / price 0.401483 / 0.328169; expectancy -0.566447 R; win rate 0.232456; average winner / loser 1.634591 / -1.307778 R.
Conditional CLOSED-only DD 144.450000 R; largest winner share 0.122355; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 31 | -32.133333 | 0.075300 | 0.079646 | 18 | 4 | 5 |
| 2023-02 | 23 | -20.883333 | 0.097262 | 0.103896 | 18 | 5 | 11 |
| 2023-03 | 11 | -10.566667 | 0.130316 | 0.116279 | 22 | 4 | 13 |
| 2023-04 | 17 | -4.500000 | 0.674699 | 0.666667 | 18 | 5 | 9 |
| 2023-05 | 18 | -11.483333 | 0.381508 | 0.366667 | 21 | 3 | 13 |
| 2023-06 | 18 | -13.483333 | 0.273788 | 0.258065 | 20 | 0 | 16 |
| 2023-07 | 26 | -16.150000 | 0.347035 | 0.409639 | 19 | 3 | 15 |
| 2023-08 | 42 | -9.500000 | 0.724105 | 0.652893 | 14 | 3 | 4 |
| 2023-09 | 33 | -23.900000 | 0.198435 | 0.195876 | 14 | 0 | 7 |
| 2023-10 | 2 | -0.250000 | 0.833333 | 0.833333 | 2 | 0 | 0 |
| 2023-11 | 5 | 16.600000 | 12.857143 | 12.000000 | 6 | 0 | 1 |
| 2023-12 | 2 | -2.900000 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N6_W2_T3_SB1_TP2

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 198, entry dates 118, entry months 12; SKIP 24, EXCLUDED 70, exclusion share 0.261194; conditional FLAT CLOSED 189.
Net -101.700000 R; PF R / price 0.418746 / 0.358838; expectancy -0.513636 R; win rate 0.237374; average winner / loser 1.558865 / -1.267874 R.
Conditional CLOSED-only DD 112.850000 R; largest winner share 0.045496; largest positive month share 0.636771. Positive / negative / zero months 3 / 9 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 22 | -18.916667 | 0.189286 | 0.191781 | 18 | 0 | 7 |
| 2023-02 | 21 | -17.050000 | 0.072529 | 0.064516 | 18 | 5 | 7 |
| 2023-03 | 15 | -16.816667 | 0.014648 | 0.017544 | 22 | 6 | 9 |
| 2023-04 | 18 | -9.000000 | 0.425532 | 0.408163 | 18 | 5 | 7 |
| 2023-05 | 17 | -9.350000 | 0.351445 | 0.333333 | 21 | 4 | 9 |
| 2023-06 | 16 | -6.250000 | 0.519231 | 0.525000 | 20 | 0 | 14 |
| 2023-07 | 19 | -10.733333 | 0.342857 | 0.346154 | 19 | 0 | 9 |
| 2023-08 | 39 | -8.150000 | 0.749359 | 0.761468 | 14 | 1 | 3 |
| 2023-09 | 25 | -16.583333 | 0.271062 | 0.270270 | 14 | 2 | 5 |
| 2023-10 | 1 | 1.250000 | NOT_AVAILABLE | NOT_AVAILABLE | 2 | 1 | 0 |
| 2023-11 | 4 | 7.100000 | 5.733333 | 6.166667 | 6 | 0 | 0 |
| 2023-12 | 1 | 2.800000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N6_W2_T3_SB1_TP3

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 198, entry dates 118, entry months 12; SKIP 24, EXCLUDED 70, exclusion share 0.261194; conditional FLAT CLOSED 189.
Net -95.666667 R; PF R / price 0.453229 / 0.374956; expectancy -0.483165 R; win rate 0.237374; average winner / loser 1.687234 / -1.267874 R.
Conditional CLOSED-only DD 111.016667 R; largest winner share 0.063052; largest positive month share 0.644951. Positive / negative / zero months 3 / 9 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 22 | -17.250000 | 0.260714 | 0.260274 | 18 | 0 | 7 |
| 2023-02 | 21 | -17.050000 | 0.072529 | 0.064516 | 18 | 5 | 7 |
| 2023-03 | 15 | -16.816667 | 0.014648 | 0.017544 | 22 | 6 | 9 |
| 2023-04 | 18 | -8.000000 | 0.489362 | 0.469388 | 18 | 5 | 7 |
| 2023-05 | 17 | -10.350000 | 0.282081 | 0.270833 | 21 | 4 | 9 |
| 2023-06 | 16 | -6.250000 | 0.519231 | 0.525000 | 20 | 0 | 14 |
| 2023-07 | 19 | -10.733333 | 0.342857 | 0.346154 | 19 | 0 | 9 |
| 2023-08 | 39 | -7.983333 | 0.754485 | 0.779817 | 14 | 1 | 3 |
| 2023-09 | 25 | -16.583333 | 0.271062 | 0.270270 | 14 | 2 | 5 |
| 2023-10 | 1 | 1.250000 | NOT_AVAILABLE | NOT_AVAILABLE | 2 | 1 | 0 |
| 2023-11 | 4 | 9.900000 | 7.600000 | 8.500000 | 6 | 0 | 0 |
| 2023-12 | 1 | 4.200000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N6_W2_T3_SB1_TP4

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 198, entry dates 118, entry months 12; SKIP 24, EXCLUDED 70, exclusion share 0.261194; conditional FLAT CLOSED 189.
Net -97.100000 R; PF R / price 0.449442 / 0.391120; expectancy -0.490404 R; win rate 0.232323; average winner / loser 1.723188 / -1.268825 R.
Conditional CLOSED-only DD 107.850000 R; largest winner share 0.084104; largest positive month share 0.897119. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 22 | -15.583333 | 0.332143 | 0.328767 | 18 | 0 | 7 |
| 2023-02 | 21 | -17.050000 | 0.072529 | 0.064516 | 18 | 5 | 7 |
| 2023-03 | 15 | -16.816667 | 0.014648 | 0.017544 | 22 | 6 | 9 |
| 2023-04 | 18 | -8.000000 | 0.489362 | 0.469388 | 18 | 5 | 7 |
| 2023-05 | 17 | -10.350000 | 0.282081 | 0.270833 | 21 | 4 | 9 |
| 2023-06 | 16 | -6.250000 | 0.519231 | 0.525000 | 20 | 0 | 14 |
| 2023-07 | 19 | -10.733333 | 0.342857 | 0.346154 | 19 | 0 | 9 |
| 2023-08 | 39 | -6.483333 | 0.800615 | 0.834862 | 14 | 1 | 3 |
| 2023-09 | 25 | -16.583333 | 0.271062 | 0.270270 | 14 | 2 | 5 |
| 2023-10 | 1 | 1.250000 | NOT_AVAILABLE | NOT_AVAILABLE | 2 | 1 | 0 |
| 2023-11 | 4 | 10.900000 | 8.266667 | 9.333333 | 6 | 0 | 0 |
| 2023-12 | 1 | -1.400000 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N6_W2_T3_SB1_TP5

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 198, entry dates 118, entry months 12; SKIP 24, EXCLUDED 70, exclusion share 0.261194; conditional FLAT CLOSED 189.
Net -99.200000 R; PF R / price 0.437535 / 0.376437; expectancy -0.501010 R; win rate 0.232323; average winner / loser 1.677536 / -1.268825 R.
Conditional CLOSED-only DD 111.350000 R; largest winner share 0.097192; largest positive month share 0.907749. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 22 | -20.583333 | 0.117857 | 0.123288 | 18 | 0 | 7 |
| 2023-02 | 21 | -17.050000 | 0.072529 | 0.064516 | 18 | 5 | 7 |
| 2023-03 | 15 | -16.816667 | 0.014648 | 0.017544 | 22 | 6 | 9 |
| 2023-04 | 18 | -8.000000 | 0.489362 | 0.469388 | 18 | 5 | 7 |
| 2023-05 | 17 | -10.350000 | 0.282081 | 0.270833 | 21 | 4 | 9 |
| 2023-06 | 16 | -6.250000 | 0.519231 | 0.525000 | 20 | 0 | 14 |
| 2023-07 | 19 | -10.733333 | 0.342857 | 0.346154 | 19 | 0 | 9 |
| 2023-08 | 39 | -4.983333 | 0.846745 | 0.889908 | 14 | 1 | 3 |
| 2023-09 | 25 | -16.583333 | 0.271062 | 0.270270 | 14 | 2 | 5 |
| 2023-10 | 1 | 1.250000 | NOT_AVAILABLE | NOT_AVAILABLE | 2 | 1 | 0 |
| 2023-11 | 4 | 12.300000 | 9.200000 | 10.500000 | 6 | 0 | 0 |
| 2023-12 | 1 | -1.400000 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N6_W2_T3_SB1_TP6

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 198, entry dates 118, entry months 12; SKIP 24, EXCLUDED 70, exclusion share 0.261194; conditional FLAT CLOSED 189.
Net -96.300000 R; PF R / price 0.453978 / 0.388289; expectancy -0.486364 R; win rate 0.232323; average winner / loser 1.740580 / -1.268825 R.
Conditional CLOSED-only DD 109.850000 R; largest winner share 0.112406; largest positive month share 0.916388. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 22 | -20.583333 | 0.117857 | 0.123288 | 18 | 0 | 7 |
| 2023-02 | 21 | -17.050000 | 0.072529 | 0.064516 | 18 | 5 | 7 |
| 2023-03 | 15 | -16.816667 | 0.014648 | 0.017544 | 22 | 6 | 9 |
| 2023-04 | 18 | -8.000000 | 0.489362 | 0.469388 | 18 | 5 | 7 |
| 2023-05 | 17 | -10.350000 | 0.282081 | 0.270833 | 21 | 4 | 9 |
| 2023-06 | 16 | -6.250000 | 0.519231 | 0.525000 | 20 | 0 | 14 |
| 2023-07 | 19 | -10.733333 | 0.342857 | 0.346154 | 19 | 0 | 9 |
| 2023-08 | 39 | -3.483333 | 0.892875 | 0.944954 | 14 | 1 | 3 |
| 2023-09 | 25 | -16.583333 | 0.271062 | 0.270270 | 14 | 2 | 5 |
| 2023-10 | 1 | 1.250000 | NOT_AVAILABLE | NOT_AVAILABLE | 2 | 1 | 0 |
| 2023-11 | 4 | 13.700000 | 10.133333 | 11.666667 | 6 | 0 | 0 |
| 2023-12 | 1 | -1.400000 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N6_W2_T3_SB1_TP7

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 198, entry dates 118, entry months 12; SKIP 24, EXCLUDED 70, exclusion share 0.261194; conditional FLAT CLOSED 189.
Net -93.400000 R; PF R / price 0.470421 / 0.400142; expectancy -0.471717 R; win rate 0.232323; average winner / loser 1.803623 / -1.268825 R.
Conditional CLOSED-only DD 108.350000 R; largest winner share 0.126557; largest positive month share 0.923547. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 22 | -20.583333 | 0.117857 | 0.123288 | 18 | 0 | 7 |
| 2023-02 | 21 | -17.050000 | 0.072529 | 0.064516 | 18 | 5 | 7 |
| 2023-03 | 15 | -16.816667 | 0.014648 | 0.017544 | 22 | 6 | 9 |
| 2023-04 | 18 | -8.000000 | 0.489362 | 0.469388 | 18 | 5 | 7 |
| 2023-05 | 17 | -10.350000 | 0.282081 | 0.270833 | 21 | 4 | 9 |
| 2023-06 | 16 | -6.250000 | 0.519231 | 0.525000 | 20 | 0 | 14 |
| 2023-07 | 19 | -10.733333 | 0.342857 | 0.346154 | 19 | 0 | 9 |
| 2023-08 | 39 | -1.983333 | 0.939006 | 1.000000 | 14 | 1 | 3 |
| 2023-09 | 25 | -16.583333 | 0.271062 | 0.270270 | 14 | 2 | 5 |
| 2023-10 | 1 | 1.250000 | NOT_AVAILABLE | NOT_AVAILABLE | 2 | 1 | 0 |
| 2023-11 | 4 | 15.100000 | 11.066667 | 12.833333 | 6 | 0 | 0 |
| 2023-12 | 1 | -1.400000 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N6_W2_T3_SB1_TP8

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 198, entry dates 118, entry months 12; SKIP 24, EXCLUDED 70, exclusion share 0.261194; conditional FLAT CLOSED 189.
Net -91.100000 R; PF R / price 0.483462 / 0.411463; expectancy -0.460101 R; win rate 0.232323; average winner / loser 1.853623 / -1.268825 R.
Conditional CLOSED-only DD 106.850000 R; largest winner share 0.140735; largest positive month share 0.927114. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 22 | -20.583333 | 0.117857 | 0.123288 | 18 | 0 | 7 |
| 2023-02 | 21 | -17.050000 | 0.072529 | 0.064516 | 18 | 5 | 7 |
| 2023-03 | 15 | -16.816667 | 0.014648 | 0.017544 | 22 | 6 | 9 |
| 2023-04 | 18 | -8.000000 | 0.489362 | 0.469388 | 18 | 5 | 7 |
| 2023-05 | 17 | -10.350000 | 0.282081 | 0.270833 | 21 | 4 | 9 |
| 2023-06 | 16 | -6.250000 | 0.519231 | 0.525000 | 20 | 0 | 14 |
| 2023-07 | 19 | -10.733333 | 0.342857 | 0.346154 | 19 | 0 | 9 |
| 2023-08 | 39 | -0.483333 | 0.985136 | 1.055046 | 14 | 1 | 3 |
| 2023-09 | 25 | -16.583333 | 0.271062 | 0.270270 | 14 | 2 | 5 |
| 2023-10 | 1 | 1.250000 | NOT_AVAILABLE | NOT_AVAILABLE | 2 | 1 | 0 |
| 2023-11 | 4 | 15.900000 | 11.600000 | 13.500000 | 6 | 0 | 0 |
| 2023-12 | 1 | -1.400000 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N6_W2_T3_SB1_TP9

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 198, entry dates 118, entry months 12; SKIP 24, EXCLUDED 70, exclusion share 0.261194; conditional FLAT CLOSED 189.
Net -93.350000 R; PF R / price 0.470705 / 0.395542; expectancy -0.471465 R; win rate 0.232323; average winner / loser 1.804710 / -1.268825 R.
Conditional CLOSED-only DD 109.100000 R; largest winner share 0.127685; largest positive month share 0.927114. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 22 | -20.583333 | 0.117857 | 0.123288 | 18 | 0 | 7 |
| 2023-02 | 21 | -17.050000 | 0.072529 | 0.064516 | 18 | 5 | 7 |
| 2023-03 | 15 | -16.816667 | 0.014648 | 0.017544 | 22 | 6 | 9 |
| 2023-04 | 18 | -8.000000 | 0.489362 | 0.469388 | 18 | 5 | 7 |
| 2023-05 | 17 | -10.350000 | 0.282081 | 0.270833 | 21 | 4 | 9 |
| 2023-06 | 16 | -6.250000 | 0.519231 | 0.525000 | 20 | 0 | 14 |
| 2023-07 | 19 | -10.733333 | 0.342857 | 0.346154 | 19 | 0 | 9 |
| 2023-08 | 39 | -2.733333 | 0.915941 | 0.972477 | 14 | 1 | 3 |
| 2023-09 | 25 | -16.583333 | 0.271062 | 0.270270 | 14 | 2 | 5 |
| 2023-10 | 1 | 1.250000 | NOT_AVAILABLE | NOT_AVAILABLE | 2 | 1 | 0 |
| 2023-11 | 4 | 15.900000 | 11.600000 | 13.500000 | 6 | 0 | 0 |
| 2023-12 | 1 | -1.400000 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N6_W2_T3_SB1_TP10

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 198, entry dates 118, entry months 12; SKIP 24, EXCLUDED 70, exclusion share 0.261194; conditional FLAT CLOSED 189.
Net -93.350000 R; PF R / price 0.470705 / 0.395542; expectancy -0.471465 R; win rate 0.232323; average winner / loser 1.804710 / -1.268825 R.
Conditional CLOSED-only DD 109.100000 R; largest winner share 0.127685; largest positive month share 0.927114. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 22 | -20.583333 | 0.117857 | 0.123288 | 18 | 0 | 7 |
| 2023-02 | 21 | -17.050000 | 0.072529 | 0.064516 | 18 | 5 | 7 |
| 2023-03 | 15 | -16.816667 | 0.014648 | 0.017544 | 22 | 6 | 9 |
| 2023-04 | 18 | -8.000000 | 0.489362 | 0.469388 | 18 | 5 | 7 |
| 2023-05 | 17 | -10.350000 | 0.282081 | 0.270833 | 21 | 4 | 9 |
| 2023-06 | 16 | -6.250000 | 0.519231 | 0.525000 | 20 | 0 | 14 |
| 2023-07 | 19 | -10.733333 | 0.342857 | 0.346154 | 19 | 0 | 9 |
| 2023-08 | 39 | -2.733333 | 0.915941 | 0.972477 | 14 | 1 | 3 |
| 2023-09 | 25 | -16.583333 | 0.271062 | 0.270270 | 14 | 2 | 5 |
| 2023-10 | 1 | 1.250000 | NOT_AVAILABLE | NOT_AVAILABLE | 2 | 1 | 0 |
| 2023-11 | 4 | 15.900000 | 11.600000 | 13.500000 | 6 | 0 | 0 |
| 2023-12 | 1 | -1.400000 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N6_W3_T2_SB1_TP2

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 227, entry dates 119, entry months 12; SKIP 21, EXCLUDED 105, exclusion share 0.316265; conditional FLAT CLOSED 216.
Net -86.166667 R; PF R / price 0.537195 / 0.475632; expectancy -0.379589 R; win rate 0.273128; average winner / loser 1.613172 / -1.224890 R.
Conditional CLOSED-only DD 90.900000 R; largest winner share 0.033328; largest positive month share 0.704762. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 26 | -15.433333 | 0.372629 | 0.370787 | 18 | 2 | 7 |
| 2023-02 | 15 | -7.733333 | 0.273865 | 0.263158 | 18 | 3 | 10 |
| 2023-03 | 8 | -8.716667 | 0.132670 | 0.105263 | 22 | 6 | 14 |
| 2023-04 | 15 | 2.466667 | 1.300813 | 1.333333 | 18 | 4 | 11 |
| 2023-05 | 16 | -2.866667 | 0.768817 | 0.690476 | 21 | 1 | 17 |
| 2023-06 | 20 | -14.666667 | 0.241379 | 0.253968 | 20 | 1 | 16 |
| 2023-07 | 27 | -11.200000 | 0.439533 | 0.436620 | 19 | 2 | 15 |
| 2023-08 | 48 | -8.700000 | 0.759890 | 0.638298 | 14 | 1 | 8 |
| 2023-09 | 29 | -15.700000 | 0.294910 | 0.285714 | 14 | 0 | 7 |
| 2023-10 | 5 | -0.450000 | 0.900000 | 1.055556 | 2 | 0 | 0 |
| 2023-11 | 13 | -4.200000 | 0.686567 | 0.955556 | 6 | 1 | 0 |
| 2023-12 | 5 | 1.033333 | 1.226277 | 1.555556 | 0 | 0 | 0 |

### B_OPT2023_N6_W3_T2_SB1_TP3

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 226, entry dates 119, entry months 12; SKIP 21, EXCLUDED 105, exclusion share 0.317221; conditional FLAT CLOSED 215.
Net -69.366667 R; PF R / price 0.625079 / 0.521966; expectancy -0.306932 R; win rate 0.269912; average winner / loser 1.895902 / -1.217215 R.
Conditional CLOSED-only DD 81.200000 R; largest winner share 0.043234; largest positive month share 0.523918. Positive / negative / zero months 4 / 8 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 26 | -12.266667 | 0.501355 | 0.494382 | 18 | 2 | 7 |
| 2023-02 | 15 | -7.733333 | 0.273865 | 0.263158 | 18 | 3 | 10 |
| 2023-03 | 8 | -8.716667 | 0.132670 | 0.105263 | 22 | 6 | 14 |
| 2023-04 | 15 | 2.433333 | 1.279693 | 1.218750 | 18 | 4 | 11 |
| 2023-05 | 16 | -3.200000 | 0.741935 | 0.666667 | 21 | 1 | 17 |
| 2023-06 | 20 | -14.666667 | 0.241379 | 0.253968 | 20 | 1 | 16 |
| 2023-07 | 27 | -11.200000 | 0.439533 | 0.436620 | 19 | 2 | 15 |
| 2023-08 | 47 | -3.200000 | 0.907425 | 0.757353 | 14 | 1 | 8 |
| 2023-09 | 29 | -15.700000 | 0.294910 | 0.285714 | 14 | 0 | 7 |
| 2023-10 | 5 | 0.950000 | 1.211111 | 1.444444 | 2 | 0 | 0 |
| 2023-11 | 13 | 0.100000 | 1.007463 | 1.400000 | 6 | 1 | 0 |
| 2023-12 | 5 | 3.833333 | 1.839416 | 2.333333 | 0 | 0 | 0 |

### B_OPT2023_N6_W3_T2_SB1_TP4

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors.
CLOSED 225, entry dates 119, entry months 12; SKIP 21, EXCLUDED 105, exclusion share 0.318182; conditional FLAT CLOSED 214.
Net -59.950000 R; PF R / price 0.675800 / 0.564538; expectancy -0.266444 R; win rate 0.266667; average winner / loser 2.082778 / -1.216557 R.
Conditional CLOSED-only DD 71.883333 R; largest winner share 0.053348; largest positive month share 0.367177. Positive / negative / zero months 4 / 8 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 26 | -10.350000 | 0.579268 | 0.561798 | 18 | 2 | 7 |
| 2023-02 | 15 | -7.733333 | 0.273865 | 0.263158 | 18 | 3 | 10 |
| 2023-03 | 8 | -8.716667 | 0.132670 | 0.105263 | 22 | 6 | 14 |
| 2023-04 | 15 | 4.100000 | 1.471264 | 1.375000 | 18 | 4 | 11 |
| 2023-05 | 16 | -3.200000 | 0.741935 | 0.666667 | 21 | 1 | 17 |
| 2023-06 | 20 | -14.666667 | 0.241379 | 0.253968 | 20 | 1 | 16 |
| 2023-07 | 27 | -11.200000 | 0.439533 | 0.436620 | 19 | 2 | 15 |
| 2023-08 | 46 | 1.133333 | 1.034274 | 0.869231 | 14 | 1 | 8 |
| 2023-09 | 29 | -15.700000 | 0.294910 | 0.285714 | 14 | 0 | 7 |
| 2023-10 | 5 | 2.350000 | 1.522222 | 1.833333 | 2 | 0 | 0 |
| 2023-11 | 13 | 4.400000 | 1.328358 | 1.844444 | 6 | 1 | 0 |
| 2023-12 | 5 | -0.366667 | 0.938547 | 1.120000 | 0 | 0 | 0 |

### B_OPT2023_N6_W3_T2_SB1_TP5

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors.
CLOSED 225, entry dates 119, entry months 12; SKIP 21, EXCLUDED 105, exclusion share 0.318182; conditional FLAT CLOSED 214.
Net -60.616667 R; PF R / price 0.674658 / 0.574555; expectancy -0.269407 R; win rate 0.262222; average winner / loser 2.130508 / -1.217756 R.
Conditional CLOSED-only DD 69.850000 R; largest winner share 0.066295; largest positive month share 0.381093. Positive / negative / zero months 5 / 7 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 26 | -10.683333 | 0.565718 | 0.550562 | 18 | 2 | 7 |
| 2023-02 | 15 | -7.733333 | 0.273865 | 0.263158 | 18 | 3 | 10 |
| 2023-03 | 8 | -8.716667 | 0.132670 | 0.105263 | 22 | 6 | 14 |
| 2023-04 | 15 | 3.100000 | 1.356322 | 1.281250 | 18 | 4 | 11 |
| 2023-05 | 16 | -3.200000 | 0.741935 | 0.666667 | 21 | 1 | 17 |
| 2023-06 | 20 | -14.666667 | 0.241379 | 0.253968 | 20 | 1 | 16 |
| 2023-07 | 27 | -11.200000 | 0.439533 | 0.436620 | 19 | 2 | 15 |
| 2023-08 | 46 | 4.300000 | 1.130040 | 0.953846 | 14 | 1 | 8 |
| 2023-09 | 29 | -15.700000 | 0.294910 | 0.285714 | 14 | 0 | 7 |
| 2023-10 | 5 | 2.550000 | 1.566667 | 1.888889 | 2 | 0 | 0 |
| 2023-11 | 13 | 0.300000 | 1.020270 | 1.307692 | 6 | 1 | 0 |
| 2023-12 | 5 | 1.033333 | 1.173184 | 1.400000 | 0 | 0 | 0 |

### B_OPT2023_N6_W3_T2_SB1_TP6

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors.
CLOSED 225, entry dates 119, entry months 12; SKIP 21, EXCLUDED 105, exclusion share 0.318182; conditional FLAT CLOSED 214.
Net -54.816667 R; PF R / price 0.705788 / 0.588126; expectancy -0.243630 R; win rate 0.262222; average winner / loser 2.228814 / -1.217756 R.
Conditional CLOSED-only DD 68.350000 R; largest winner share 0.068441; largest positive month share 0.339512. Positive / negative / zero months 5 / 7 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 26 | -10.683333 | 0.565718 | 0.550562 | 18 | 2 | 7 |
| 2023-02 | 15 | -7.733333 | 0.273865 | 0.263158 | 18 | 3 | 10 |
| 2023-03 | 8 | -8.716667 | 0.132670 | 0.105263 | 22 | 6 | 14 |
| 2023-04 | 15 | 3.100000 | 1.356322 | 1.281250 | 18 | 4 | 11 |
| 2023-05 | 16 | -3.200000 | 0.741935 | 0.666667 | 21 | 1 | 17 |
| 2023-06 | 20 | -14.666667 | 0.241379 | 0.253968 | 20 | 1 | 16 |
| 2023-07 | 27 | -11.200000 | 0.439533 | 0.436620 | 19 | 2 | 15 |
| 2023-08 | 46 | 5.800000 | 1.175403 | 1.000000 | 14 | 1 | 8 |
| 2023-09 | 29 | -15.700000 | 0.294910 | 0.285714 | 14 | 0 | 7 |
| 2023-10 | 5 | 2.550000 | 1.566667 | 1.888889 | 2 | 0 | 0 |
| 2023-11 | 13 | 3.200000 | 1.216216 | 1.557692 | 6 | 1 | 0 |
| 2023-12 | 5 | 2.433333 | 1.407821 | 1.680000 | 0 | 0 | 0 |

### B_OPT2023_N6_W3_T2_SB1_TP7

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors.
CLOSED 225, entry dates 119, entry months 12; SKIP 21, EXCLUDED 105, exclusion share 0.318182; conditional FLAT CLOSED 214.
Net -51.266667 R; PF R / price 0.724841 / 0.600170; expectancy -0.227852 R; win rate 0.262222; average winner / loser 2.288983 / -1.217756 R.
Conditional CLOSED-only DD 66.850000 R; largest winner share 0.077749; largest positive month share 0.353796. Positive / negative / zero months 5 / 7 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 26 | -10.683333 | 0.565718 | 0.550562 | 18 | 2 | 7 |
| 2023-02 | 15 | -7.733333 | 0.273865 | 0.263158 | 18 | 3 | 10 |
| 2023-03 | 8 | -8.716667 | 0.132670 | 0.105263 | 22 | 6 | 14 |
| 2023-04 | 15 | 3.100000 | 1.356322 | 1.281250 | 18 | 4 | 11 |
| 2023-05 | 16 | -3.200000 | 0.741935 | 0.666667 | 21 | 1 | 17 |
| 2023-06 | 20 | -14.666667 | 0.241379 | 0.253968 | 20 | 1 | 16 |
| 2023-07 | 27 | -11.200000 | 0.439533 | 0.436620 | 19 | 2 | 15 |
| 2023-08 | 46 | 7.300000 | 1.220766 | 1.046154 | 14 | 1 | 8 |
| 2023-09 | 29 | -15.700000 | 0.294910 | 0.285714 | 14 | 0 | 7 |
| 2023-10 | 5 | 2.550000 | 1.566667 | 1.888889 | 2 | 0 | 0 |
| 2023-11 | 13 | 3.850000 | 1.260135 | 1.634615 | 6 | 1 | 0 |
| 2023-12 | 5 | 3.833333 | 1.642458 | 1.960000 | 0 | 0 | 0 |

### B_OPT2023_N6_W3_T2_SB1_TP8

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors.
CLOSED 225, entry dates 119, entry months 12; SKIP 21, EXCLUDED 105, exclusion share 0.318182; conditional FLAT CLOSED 214.
Net -47.566667 R; PF R / price 0.744700 / 0.612214; expectancy -0.211407 R; win rate 0.262222; average winner / loser 2.351695 / -1.217756 R.
Conditional CLOSED-only DD 65.350000 R; largest winner share 0.086486; largest positive month share 0.361644. Positive / negative / zero months 5 / 7 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 26 | -10.683333 | 0.565718 | 0.550562 | 18 | 2 | 7 |
| 2023-02 | 15 | -7.733333 | 0.273865 | 0.263158 | 18 | 3 | 10 |
| 2023-03 | 8 | -8.716667 | 0.132670 | 0.105263 | 22 | 6 | 14 |
| 2023-04 | 15 | 3.100000 | 1.356322 | 1.281250 | 18 | 4 | 11 |
| 2023-05 | 16 | -3.200000 | 0.741935 | 0.666667 | 21 | 1 | 17 |
| 2023-06 | 20 | -14.666667 | 0.241379 | 0.253968 | 20 | 1 | 16 |
| 2023-07 | 27 | -11.200000 | 0.439533 | 0.436620 | 19 | 2 | 15 |
| 2023-08 | 46 | 8.800000 | 1.266129 | 1.092308 | 14 | 1 | 8 |
| 2023-09 | 29 | -15.700000 | 0.294910 | 0.285714 | 14 | 0 | 7 |
| 2023-10 | 5 | 2.550000 | 1.566667 | 1.888889 | 2 | 0 | 0 |
| 2023-11 | 13 | 4.650000 | 1.314189 | 1.711538 | 6 | 1 | 0 |
| 2023-12 | 5 | 5.233333 | 1.877095 | 2.240000 | 0 | 0 | 0 |

### B_OPT2023_N6_W3_T2_SB1_TP9

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors.
CLOSED 225, entry dates 119, entry months 12; SKIP 21, EXCLUDED 105, exclusion share 0.318182; conditional FLAT CLOSED 214.
Net -52.216667 R; PF R / price 0.719742 / 0.594911; expectancy -0.232074 R; win rate 0.262222; average winner / loser 2.272881 / -1.217756 R.
Conditional CLOSED-only DD 67.600000 R; largest winner share 0.079045; largest positive month share 0.332769. Positive / negative / zero months 5 / 7 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 26 | -10.683333 | 0.565718 | 0.550562 | 18 | 2 | 7 |
| 2023-02 | 15 | -7.733333 | 0.273865 | 0.263158 | 18 | 3 | 10 |
| 2023-03 | 8 | -8.716667 | 0.132670 | 0.105263 | 22 | 6 | 14 |
| 2023-04 | 15 | 3.100000 | 1.356322 | 1.281250 | 18 | 4 | 11 |
| 2023-05 | 16 | -3.200000 | 0.741935 | 0.666667 | 21 | 1 | 17 |
| 2023-06 | 20 | -14.666667 | 0.241379 | 0.253968 | 20 | 1 | 16 |
| 2023-07 | 27 | -11.200000 | 0.439533 | 0.436620 | 19 | 2 | 15 |
| 2023-08 | 46 | 6.550000 | 1.198085 | 1.023077 | 14 | 1 | 8 |
| 2023-09 | 29 | -15.700000 | 0.294910 | 0.285714 | 14 | 0 | 7 |
| 2023-10 | 5 | 2.550000 | 1.566667 | 1.888889 | 2 | 0 | 0 |
| 2023-11 | 13 | 4.650000 | 1.314189 | 1.711538 | 6 | 1 | 0 |
| 2023-12 | 5 | 2.833333 | 1.474860 | 1.760000 | 0 | 0 | 0 |

### B_OPT2023_N6_W3_T2_SB1_TP10

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors.
CLOSED 225, entry dates 119, entry months 12; SKIP 21, EXCLUDED 105, exclusion share 0.318182; conditional FLAT CLOSED 214.
Net -52.216667 R; PF R / price 0.719742 / 0.594911; expectancy -0.232074 R; win rate 0.262222; average winner / loser 2.272881 / -1.217756 R.
Conditional CLOSED-only DD 67.600000 R; largest winner share 0.079045; largest positive month share 0.332769. Positive / negative / zero months 5 / 7 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 26 | -10.683333 | 0.565718 | 0.550562 | 18 | 2 | 7 |
| 2023-02 | 15 | -7.733333 | 0.273865 | 0.263158 | 18 | 3 | 10 |
| 2023-03 | 8 | -8.716667 | 0.132670 | 0.105263 | 22 | 6 | 14 |
| 2023-04 | 15 | 3.100000 | 1.356322 | 1.281250 | 18 | 4 | 11 |
| 2023-05 | 16 | -3.200000 | 0.741935 | 0.666667 | 21 | 1 | 17 |
| 2023-06 | 20 | -14.666667 | 0.241379 | 0.253968 | 20 | 1 | 16 |
| 2023-07 | 27 | -11.200000 | 0.439533 | 0.436620 | 19 | 2 | 15 |
| 2023-08 | 46 | 6.550000 | 1.198085 | 1.023077 | 14 | 1 | 8 |
| 2023-09 | 29 | -15.700000 | 0.294910 | 0.285714 | 14 | 0 | 7 |
| 2023-10 | 5 | 2.550000 | 1.566667 | 1.888889 | 2 | 0 | 0 |
| 2023-11 | 13 | 4.650000 | 1.314189 | 1.711538 | 6 | 1 | 0 |
| 2023-12 | 5 | 2.833333 | 1.474860 | 1.760000 | 0 | 0 | 0 |

### B_OPT2023_N6_W3_T3_SB1_TP2

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 201, entry dates 121, entry months 12; SKIP 24, EXCLUDED 75, exclusion share 0.271739; conditional FLAT CLOSED 192.
Net -94.933333 R; PF R / price 0.461065 / 0.410906; expectancy -0.472305 R; win rate 0.248756; average winner / loser 1.624333 / -1.267266 R.
Conditional CLOSED-only DD 97.933333 R; largest winner share 0.041042; largest positive month share 0.692308. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 20 | -12.216667 | 0.347284 | 0.343750 | 18 | 1 | 9 |
| 2023-02 | 18 | -17.133333 | 0.072202 | 0.095238 | 18 | 3 | 6 |
| 2023-03 | 10 | -10.133333 | 0.061728 | 0.052632 | 22 | 7 | 12 |
| 2023-04 | 18 | -3.466667 | 0.733333 | 0.756098 | 18 | 4 | 6 |
| 2023-05 | 17 | -4.133333 | 0.648227 | 0.625000 | 21 | 5 | 11 |
| 2023-06 | 18 | -8.416667 | 0.419540 | 0.444444 | 20 | 0 | 13 |
| 2023-07 | 23 | -7.700000 | 0.554913 | 0.578947 | 19 | 0 | 9 |
| 2023-08 | 37 | -17.966667 | 0.504140 | 0.460938 | 14 | 0 | 5 |
| 2023-09 | 24 | -14.583333 | 0.297189 | 0.298507 | 14 | 2 | 4 |
| 2023-10 | 3 | 2.550000 | 2.700000 | 3.166667 | 2 | 1 | 0 |
| 2023-11 | 11 | -2.866667 | 0.750000 | 0.952381 | 6 | 1 | 0 |
| 2023-12 | 2 | 1.133333 | 1.680000 | 2.800000 | 0 | 0 | 0 |

### B_OPT2023_N6_W3_T3_SB1_TP3

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors.
CLOSED 201, entry dates 121, entry months 12; SKIP 24, EXCLUDED 75, exclusion share 0.271739; conditional FLAT CLOSED 192.
Net -86.333333 R; PF R / price 0.509887 / 0.428050; expectancy -0.429519 R; win rate 0.248756; average winner / loser 1.796333 / -1.267266 R.
Conditional CLOSED-only DD 95.033333 R; largest winner share 0.055669; largest positive month share 0.498947. Positive / negative / zero months 3 / 9 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 20 | -10.550000 | 0.436331 | 0.421875 | 18 | 1 | 9 |
| 2023-02 | 18 | -17.133333 | 0.072202 | 0.095238 | 18 | 3 | 6 |
| 2023-03 | 10 | -10.133333 | 0.061728 | 0.052632 | 22 | 7 | 12 |
| 2023-04 | 18 | -3.466667 | 0.733333 | 0.756098 | 18 | 4 | 6 |
| 2023-05 | 17 | -5.133333 | 0.563121 | 0.550000 | 21 | 5 | 11 |
| 2023-06 | 18 | -8.416667 | 0.419540 | 0.444444 | 20 | 0 | 13 |
| 2023-07 | 23 | -7.700000 | 0.554913 | 0.578947 | 19 | 0 | 9 |
| 2023-08 | 37 | -17.133333 | 0.527139 | 0.492188 | 14 | 0 | 5 |
| 2023-09 | 24 | -14.583333 | 0.297189 | 0.298507 | 14 | 2 | 4 |
| 2023-10 | 3 | 3.950000 | 3.633333 | 4.333333 | 2 | 1 | 0 |
| 2023-11 | 11 | 1.433333 | 1.125000 | 1.428571 | 6 | 1 | 0 |
| 2023-12 | 2 | 2.533333 | 2.520000 | 4.200000 | 0 | 0 | 0 |

### B_OPT2023_N6_W3_T3_SB1_TP4

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 201, entry dates 121, entry months 12; SKIP 24, EXCLUDED 75, exclusion share 0.271739; conditional FLAT CLOSED 192.
Net -90.066667 R; PF R / price 0.496694 / 0.442969; expectancy -0.448093 R; win rate 0.238806; average winner / loser 1.851736 / -1.269149 R.
Conditional CLOSED-only DD 91.083333 R; largest winner share 0.075005; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 20 | -8.883333 | 0.525378 | 0.500000 | 18 | 1 | 9 |
| 2023-02 | 18 | -17.133333 | 0.072202 | 0.095238 | 18 | 3 | 6 |
| 2023-03 | 10 | -10.133333 | 0.061728 | 0.052632 | 22 | 7 | 12 |
| 2023-04 | 18 | -3.466667 | 0.733333 | 0.756098 | 18 | 4 | 6 |
| 2023-05 | 17 | -5.133333 | 0.563121 | 0.550000 | 21 | 5 | 11 |
| 2023-06 | 18 | -8.416667 | 0.419540 | 0.444444 | 20 | 0 | 13 |
| 2023-07 | 23 | -7.700000 | 0.554913 | 0.578947 | 19 | 0 | 9 |
| 2023-08 | 37 | -15.633333 | 0.568537 | 0.539062 | 14 | 0 | 5 |
| 2023-09 | 24 | -14.583333 | 0.297189 | 0.298507 | 14 | 2 | 4 |
| 2023-10 | 3 | 5.350000 | 4.566667 | 5.500000 | 2 | 1 | 0 |
| 2023-11 | 11 | -1.266667 | 0.901554 | 1.061224 | 6 | 1 | 0 |
| 2023-12 | 2 | -3.066667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N6_W3_T3_SB1_TP5

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 201, entry dates 121, entry months 12; SKIP 24, EXCLUDED 75, exclusion share 0.271739; conditional FLAT CLOSED 192.
Net -85.800000 R; PF R / price 0.520536 / 0.454612; expectancy -0.426866 R; win rate 0.238806; average winner / loser 1.940625 / -1.269149 R.
Conditional CLOSED-only DD 89.916667 R; largest winner share 0.080515; largest positive month share 0.772622. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 20 | -9.216667 | 0.507569 | 0.484375 | 18 | 1 | 9 |
| 2023-02 | 18 | -17.133333 | 0.072202 | 0.095238 | 18 | 3 | 6 |
| 2023-03 | 10 | -10.133333 | 0.061728 | 0.052632 | 22 | 7 | 12 |
| 2023-04 | 18 | -3.466667 | 0.733333 | 0.756098 | 18 | 4 | 6 |
| 2023-05 | 17 | -5.133333 | 0.563121 | 0.550000 | 21 | 5 | 11 |
| 2023-06 | 18 | -8.416667 | 0.419540 | 0.444444 | 20 | 0 | 13 |
| 2023-07 | 23 | -7.700000 | 0.554913 | 0.578947 | 19 | 0 | 9 |
| 2023-08 | 37 | -14.133333 | 0.609936 | 0.585938 | 14 | 0 | 5 |
| 2023-09 | 24 | -14.583333 | 0.297189 | 0.298507 | 14 | 2 | 4 |
| 2023-10 | 3 | 5.550000 | 4.700000 | 5.666667 | 2 | 1 | 0 |
| 2023-11 | 11 | 1.633333 | 1.126943 | 1.326531 | 6 | 1 | 0 |
| 2023-12 | 2 | -3.066667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N6_W3_T3_SB1_TP6

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 201, entry dates 121, entry months 12; SKIP 24, EXCLUDED 75, exclusion share 0.271739; conditional FLAT CLOSED 192.
Net -82.650000 R; PF R / price 0.538139 / 0.466982; expectancy -0.411194 R; win rate 0.238806; average winner / loser 2.006250 / -1.269149 R.
Conditional CLOSED-only DD 88.416667 R; largest winner share 0.093458; largest positive month share 0.628302. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 20 | -9.216667 | 0.507569 | 0.484375 | 18 | 1 | 9 |
| 2023-02 | 18 | -17.133333 | 0.072202 | 0.095238 | 18 | 3 | 6 |
| 2023-03 | 10 | -10.133333 | 0.061728 | 0.052632 | 22 | 7 | 12 |
| 2023-04 | 18 | -3.466667 | 0.733333 | 0.756098 | 18 | 4 | 6 |
| 2023-05 | 17 | -5.133333 | 0.563121 | 0.550000 | 21 | 5 | 11 |
| 2023-06 | 18 | -8.416667 | 0.419540 | 0.444444 | 20 | 0 | 13 |
| 2023-07 | 23 | -7.700000 | 0.554913 | 0.578947 | 19 | 0 | 9 |
| 2023-08 | 37 | -12.633333 | 0.651334 | 0.632812 | 14 | 0 | 5 |
| 2023-09 | 24 | -14.583333 | 0.297189 | 0.298507 | 14 | 2 | 4 |
| 2023-10 | 3 | 5.550000 | 4.700000 | 5.666667 | 2 | 1 | 0 |
| 2023-11 | 11 | 3.283333 | 1.255181 | 1.489796 | 6 | 1 | 0 |
| 2023-12 | 2 | -3.066667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N6_W3_T3_SB1_TP7

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 201, entry dates 121, entry months 12; SKIP 24, EXCLUDED 75, exclusion share 0.271739; conditional FLAT CLOSED 192.
Net -79.750000 R; PF R / price 0.554345 / 0.479170; expectancy -0.396766 R; win rate 0.238806; average winner / loser 2.066667 / -1.269149 R.
Conditional CLOSED-only DD 86.916667 R; largest winner share 0.105847; largest positive month share 0.542345. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 20 | -9.216667 | 0.507569 | 0.484375 | 18 | 1 | 9 |
| 2023-02 | 18 | -17.133333 | 0.072202 | 0.095238 | 18 | 3 | 6 |
| 2023-03 | 10 | -10.133333 | 0.061728 | 0.052632 | 22 | 7 | 12 |
| 2023-04 | 18 | -3.466667 | 0.733333 | 0.756098 | 18 | 4 | 6 |
| 2023-05 | 17 | -5.133333 | 0.563121 | 0.550000 | 21 | 5 | 11 |
| 2023-06 | 18 | -8.416667 | 0.419540 | 0.444444 | 20 | 0 | 13 |
| 2023-07 | 23 | -7.700000 | 0.554913 | 0.578947 | 19 | 0 | 9 |
| 2023-08 | 37 | -11.133333 | 0.692732 | 0.679688 | 14 | 0 | 5 |
| 2023-09 | 24 | -14.583333 | 0.297189 | 0.298507 | 14 | 2 | 4 |
| 2023-10 | 3 | 5.550000 | 4.700000 | 5.666667 | 2 | 1 | 0 |
| 2023-11 | 11 | 4.683333 | 1.363990 | 1.632653 | 6 | 1 | 0 |
| 2023-12 | 2 | -3.066667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N6_W3_T3_SB1_TP8

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 201, entry dates 121, entry months 12; SKIP 24, EXCLUDED 75, exclusion share 0.271739; conditional FLAT CLOSED 192.
Net -77.450000 R; PF R / price 0.567198 / 0.490813; expectancy -0.385323 R; win rate 0.238806; average winner / loser 2.114583 / -1.269149 R.
Conditional CLOSED-only DD 85.416667 R; largest winner share 0.118227; largest positive month share 0.503021. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 20 | -9.216667 | 0.507569 | 0.484375 | 18 | 1 | 9 |
| 2023-02 | 18 | -17.133333 | 0.072202 | 0.095238 | 18 | 3 | 6 |
| 2023-03 | 10 | -10.133333 | 0.061728 | 0.052632 | 22 | 7 | 12 |
| 2023-04 | 18 | -3.466667 | 0.733333 | 0.756098 | 18 | 4 | 6 |
| 2023-05 | 17 | -5.133333 | 0.563121 | 0.550000 | 21 | 5 | 11 |
| 2023-06 | 18 | -8.416667 | 0.419540 | 0.444444 | 20 | 0 | 13 |
| 2023-07 | 23 | -7.700000 | 0.554913 | 0.578947 | 19 | 0 | 9 |
| 2023-08 | 37 | -9.633333 | 0.734131 | 0.726562 | 14 | 0 | 5 |
| 2023-09 | 24 | -14.583333 | 0.297189 | 0.298507 | 14 | 2 | 4 |
| 2023-10 | 3 | 5.550000 | 4.700000 | 5.666667 | 2 | 1 | 0 |
| 2023-11 | 11 | 5.483333 | 1.426166 | 1.714286 | 6 | 1 | 0 |
| 2023-12 | 2 | -3.066667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N6_W3_T3_SB1_TP9

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 201, entry dates 121, entry months 12; SKIP 24, EXCLUDED 75, exclusion share 0.271739; conditional FLAT CLOSED 192.
Net -79.700000 R; PF R / price 0.554624 / 0.474441; expectancy -0.396517 R; win rate 0.238806; average winner / loser 2.067708 / -1.269149 R.
Conditional CLOSED-only DD 87.666667 R; largest winner share 0.106801; largest positive month share 0.503021. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 20 | -9.216667 | 0.507569 | 0.484375 | 18 | 1 | 9 |
| 2023-02 | 18 | -17.133333 | 0.072202 | 0.095238 | 18 | 3 | 6 |
| 2023-03 | 10 | -10.133333 | 0.061728 | 0.052632 | 22 | 7 | 12 |
| 2023-04 | 18 | -3.466667 | 0.733333 | 0.756098 | 18 | 4 | 6 |
| 2023-05 | 17 | -5.133333 | 0.563121 | 0.550000 | 21 | 5 | 11 |
| 2023-06 | 18 | -8.416667 | 0.419540 | 0.444444 | 20 | 0 | 13 |
| 2023-07 | 23 | -7.700000 | 0.554913 | 0.578947 | 19 | 0 | 9 |
| 2023-08 | 37 | -11.883333 | 0.672033 | 0.656250 | 14 | 0 | 5 |
| 2023-09 | 24 | -14.583333 | 0.297189 | 0.298507 | 14 | 2 | 4 |
| 2023-10 | 3 | 5.550000 | 4.700000 | 5.666667 | 2 | 1 | 0 |
| 2023-11 | 11 | 5.483333 | 1.426166 | 1.714286 | 6 | 1 | 0 |
| 2023-12 | 2 | -3.066667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N6_W3_T3_SB1_TP10

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 201, entry dates 121, entry months 12; SKIP 24, EXCLUDED 75, exclusion share 0.271739; conditional FLAT CLOSED 192.
Net -79.700000 R; PF R / price 0.554624 / 0.474441; expectancy -0.396517 R; win rate 0.238806; average winner / loser 2.067708 / -1.269149 R.
Conditional CLOSED-only DD 87.666667 R; largest winner share 0.106801; largest positive month share 0.503021. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 20 | -9.216667 | 0.507569 | 0.484375 | 18 | 1 | 9 |
| 2023-02 | 18 | -17.133333 | 0.072202 | 0.095238 | 18 | 3 | 6 |
| 2023-03 | 10 | -10.133333 | 0.061728 | 0.052632 | 22 | 7 | 12 |
| 2023-04 | 18 | -3.466667 | 0.733333 | 0.756098 | 18 | 4 | 6 |
| 2023-05 | 17 | -5.133333 | 0.563121 | 0.550000 | 21 | 5 | 11 |
| 2023-06 | 18 | -8.416667 | 0.419540 | 0.444444 | 20 | 0 | 13 |
| 2023-07 | 23 | -7.700000 | 0.554913 | 0.578947 | 19 | 0 | 9 |
| 2023-08 | 37 | -11.883333 | 0.672033 | 0.656250 | 14 | 0 | 5 |
| 2023-09 | 24 | -14.583333 | 0.297189 | 0.298507 | 14 | 2 | 4 |
| 2023-10 | 3 | 5.550000 | 4.700000 | 5.666667 | 2 | 1 | 0 |
| 2023-11 | 11 | 5.483333 | 1.426166 | 1.714286 | 6 | 1 | 0 |
| 2023-12 | 2 | -3.066667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N7_W2_T2_SB1_TP2

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 218, entry dates 115, entry months 12; SKIP 26, EXCLUDED 100, exclusion share 0.314465; conditional FLAT CLOSED 218.
Net -156.466667 R; PF R / price 0.255511 / 0.267964; expectancy -0.717737 R; win rate 0.192661; average winner / loser 1.278571 / -1.273737 R.
Conditional CLOSED-only DD 156.466667 R; largest winner share 0.062073; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 12 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 32 | -34.783333 | 0.092214 | 0.089431 | 18 | 3 | 9 |
| 2023-02 | 23 | -10.216667 | 0.436581 | 0.406780 | 18 | 1 | 10 |
| 2023-03 | 11 | -13.583333 | 0.000000 | 0.000000 | 22 | 2 | 15 |
| 2023-04 | 16 | -4.333333 | 0.606061 | 0.600000 | 18 | 8 | 9 |
| 2023-05 | 24 | -20.816667 | 0.218887 | 0.227273 | 21 | 2 | 14 |
| 2023-06 | 17 | -7.350000 | 0.412783 | 0.386364 | 20 | 0 | 15 |
| 2023-07 | 27 | -20.216667 | 0.259463 | 0.288889 | 19 | 7 | 12 |
| 2023-08 | 33 | -21.233333 | 0.315422 | 0.311927 | 14 | 0 | 8 |
| 2023-09 | 29 | -15.950000 | 0.326056 | 0.346667 | 14 | 1 | 8 |
| 2023-10 | 1 | -1.500000 | 0.000000 | 0.000000 | 2 | 1 | 0 |
| 2023-11 | 4 | -5.083333 | 0.000000 | 0.000000 | 6 | 1 | 0 |
| 2023-12 | 1 | -1.400000 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N7_W2_T2_SB1_TP3

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 218, entry dates 115, entry months 12; SKIP 26, EXCLUDED 100, exclusion share 0.314465; conditional FLAT CLOSED 218.
Net -154.633333 R; PF R / price 0.264235 / 0.278443; expectancy -0.709327 R; win rate 0.192661; average winner / loser 1.322222 / -1.273737 R.
Conditional CLOSED-only DD 154.633333 R; largest winner share 0.090036; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 12 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 32 | -33.116667 | 0.135711 | 0.130081 | 18 | 3 | 9 |
| 2023-02 | 23 | -10.550000 | 0.418199 | 0.389831 | 18 | 1 | 10 |
| 2023-03 | 11 | -13.583333 | 0.000000 | 0.000000 | 22 | 2 | 15 |
| 2023-04 | 16 | -4.333333 | 0.606061 | 0.600000 | 18 | 8 | 9 |
| 2023-05 | 24 | -21.816667 | 0.181363 | 0.193182 | 21 | 2 | 14 |
| 2023-06 | 17 | -7.350000 | 0.412783 | 0.386364 | 20 | 0 | 15 |
| 2023-07 | 27 | -18.716667 | 0.314408 | 0.355556 | 19 | 7 | 12 |
| 2023-08 | 33 | -21.233333 | 0.315422 | 0.311927 | 14 | 0 | 8 |
| 2023-09 | 29 | -15.950000 | 0.326056 | 0.346667 | 14 | 1 | 8 |
| 2023-10 | 1 | -1.500000 | 0.000000 | 0.000000 | 2 | 1 | 0 |
| 2023-11 | 4 | -5.083333 | 0.000000 | 0.000000 | 6 | 1 | 0 |
| 2023-12 | 1 | -1.400000 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N7_W2_T2_SB1_TP4

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 218, entry dates 115, entry months 12; SKIP 26, EXCLUDED 100, exclusion share 0.314465; conditional FLAT CLOSED 218.
Net -153.466667 R; PF R / price 0.269786 / 0.282934; expectancy -0.703976 R; win rate 0.192661; average winner / loser 1.350000 / -1.273737 R.
Conditional CLOSED-only DD 153.466667 R; largest winner share 0.117578; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 12 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 32 | -31.450000 | 0.179208 | 0.170732 | 18 | 3 | 9 |
| 2023-02 | 23 | -10.550000 | 0.418199 | 0.389831 | 18 | 1 | 10 |
| 2023-03 | 11 | -13.583333 | 0.000000 | 0.000000 | 22 | 2 | 15 |
| 2023-04 | 16 | -4.333333 | 0.606061 | 0.600000 | 18 | 8 | 9 |
| 2023-05 | 24 | -21.816667 | 0.181363 | 0.193182 | 21 | 2 | 14 |
| 2023-06 | 17 | -7.350000 | 0.412783 | 0.386364 | 20 | 0 | 15 |
| 2023-07 | 27 | -19.216667 | 0.296093 | 0.333333 | 19 | 7 | 12 |
| 2023-08 | 33 | -21.233333 | 0.315422 | 0.311927 | 14 | 0 | 8 |
| 2023-09 | 29 | -15.950000 | 0.326056 | 0.346667 | 14 | 1 | 8 |
| 2023-10 | 1 | -1.500000 | 0.000000 | 0.000000 | 2 | 1 | 0 |
| 2023-11 | 4 | -5.083333 | 0.000000 | 0.000000 | 6 | 1 | 0 |
| 2023-12 | 1 | -1.400000 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N7_W2_T2_SB1_TP5

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 218, entry dates 115, entry months 12; SKIP 26, EXCLUDED 100, exclusion share 0.314465; conditional FLAT CLOSED 218.
Net -158.466667 R; PF R / price 0.245995 / 0.260479; expectancy -0.726911 R; win rate 0.192661; average winner / loser 1.230952 / -1.273737 R.
Conditional CLOSED-only DD 158.466667 R; largest winner share 0.077369; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 12 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 32 | -36.450000 | 0.048717 | 0.048780 | 18 | 3 | 9 |
| 2023-02 | 23 | -10.550000 | 0.418199 | 0.389831 | 18 | 1 | 10 |
| 2023-03 | 11 | -13.583333 | 0.000000 | 0.000000 | 22 | 2 | 15 |
| 2023-04 | 16 | -4.333333 | 0.606061 | 0.600000 | 18 | 8 | 9 |
| 2023-05 | 24 | -21.816667 | 0.181363 | 0.193182 | 21 | 2 | 14 |
| 2023-06 | 17 | -7.350000 | 0.412783 | 0.386364 | 20 | 0 | 15 |
| 2023-07 | 27 | -19.216667 | 0.296093 | 0.333333 | 19 | 7 | 12 |
| 2023-08 | 33 | -21.233333 | 0.315422 | 0.311927 | 14 | 0 | 8 |
| 2023-09 | 29 | -15.950000 | 0.326056 | 0.346667 | 14 | 1 | 8 |
| 2023-10 | 1 | -1.500000 | 0.000000 | 0.000000 | 2 | 1 | 0 |
| 2023-11 | 4 | -5.083333 | 0.000000 | 0.000000 | 6 | 1 | 0 |
| 2023-12 | 1 | -1.400000 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N7_W2_T2_SB1_TP6

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 218, entry dates 115, entry months 12; SKIP 26, EXCLUDED 100, exclusion share 0.314465; conditional FLAT CLOSED 218.
Net -158.466667 R; PF R / price 0.245995 / 0.260479; expectancy -0.726911 R; win rate 0.192661; average winner / loser 1.230952 / -1.273737 R.
Conditional CLOSED-only DD 158.466667 R; largest winner share 0.077369; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 12 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 32 | -36.450000 | 0.048717 | 0.048780 | 18 | 3 | 9 |
| 2023-02 | 23 | -10.550000 | 0.418199 | 0.389831 | 18 | 1 | 10 |
| 2023-03 | 11 | -13.583333 | 0.000000 | 0.000000 | 22 | 2 | 15 |
| 2023-04 | 16 | -4.333333 | 0.606061 | 0.600000 | 18 | 8 | 9 |
| 2023-05 | 24 | -21.816667 | 0.181363 | 0.193182 | 21 | 2 | 14 |
| 2023-06 | 17 | -7.350000 | 0.412783 | 0.386364 | 20 | 0 | 15 |
| 2023-07 | 27 | -19.216667 | 0.296093 | 0.333333 | 19 | 7 | 12 |
| 2023-08 | 33 | -21.233333 | 0.315422 | 0.311927 | 14 | 0 | 8 |
| 2023-09 | 29 | -15.950000 | 0.326056 | 0.346667 | 14 | 1 | 8 |
| 2023-10 | 1 | -1.500000 | 0.000000 | 0.000000 | 2 | 1 | 0 |
| 2023-11 | 4 | -5.083333 | 0.000000 | 0.000000 | 6 | 1 | 0 |
| 2023-12 | 1 | -1.400000 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N7_W2_T2_SB1_TP7

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 218, entry dates 115, entry months 12; SKIP 26, EXCLUDED 100, exclusion share 0.314465; conditional FLAT CLOSED 218.
Net -158.466667 R; PF R / price 0.245995 / 0.260479; expectancy -0.726911 R; win rate 0.192661; average winner / loser 1.230952 / -1.273737 R.
Conditional CLOSED-only DD 158.466667 R; largest winner share 0.077369; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 12 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 32 | -36.450000 | 0.048717 | 0.048780 | 18 | 3 | 9 |
| 2023-02 | 23 | -10.550000 | 0.418199 | 0.389831 | 18 | 1 | 10 |
| 2023-03 | 11 | -13.583333 | 0.000000 | 0.000000 | 22 | 2 | 15 |
| 2023-04 | 16 | -4.333333 | 0.606061 | 0.600000 | 18 | 8 | 9 |
| 2023-05 | 24 | -21.816667 | 0.181363 | 0.193182 | 21 | 2 | 14 |
| 2023-06 | 17 | -7.350000 | 0.412783 | 0.386364 | 20 | 0 | 15 |
| 2023-07 | 27 | -19.216667 | 0.296093 | 0.333333 | 19 | 7 | 12 |
| 2023-08 | 33 | -21.233333 | 0.315422 | 0.311927 | 14 | 0 | 8 |
| 2023-09 | 29 | -15.950000 | 0.326056 | 0.346667 | 14 | 1 | 8 |
| 2023-10 | 1 | -1.500000 | 0.000000 | 0.000000 | 2 | 1 | 0 |
| 2023-11 | 4 | -5.083333 | 0.000000 | 0.000000 | 6 | 1 | 0 |
| 2023-12 | 1 | -1.400000 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N7_W2_T2_SB1_TP8

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 218, entry dates 115, entry months 12; SKIP 26, EXCLUDED 100, exclusion share 0.314465; conditional FLAT CLOSED 218.
Net -158.466667 R; PF R / price 0.245995 / 0.260479; expectancy -0.726911 R; win rate 0.192661; average winner / loser 1.230952 / -1.273737 R.
Conditional CLOSED-only DD 158.466667 R; largest winner share 0.077369; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 12 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 32 | -36.450000 | 0.048717 | 0.048780 | 18 | 3 | 9 |
| 2023-02 | 23 | -10.550000 | 0.418199 | 0.389831 | 18 | 1 | 10 |
| 2023-03 | 11 | -13.583333 | 0.000000 | 0.000000 | 22 | 2 | 15 |
| 2023-04 | 16 | -4.333333 | 0.606061 | 0.600000 | 18 | 8 | 9 |
| 2023-05 | 24 | -21.816667 | 0.181363 | 0.193182 | 21 | 2 | 14 |
| 2023-06 | 17 | -7.350000 | 0.412783 | 0.386364 | 20 | 0 | 15 |
| 2023-07 | 27 | -19.216667 | 0.296093 | 0.333333 | 19 | 7 | 12 |
| 2023-08 | 33 | -21.233333 | 0.315422 | 0.311927 | 14 | 0 | 8 |
| 2023-09 | 29 | -15.950000 | 0.326056 | 0.346667 | 14 | 1 | 8 |
| 2023-10 | 1 | -1.500000 | 0.000000 | 0.000000 | 2 | 1 | 0 |
| 2023-11 | 4 | -5.083333 | 0.000000 | 0.000000 | 6 | 1 | 0 |
| 2023-12 | 1 | -1.400000 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N7_W2_T2_SB1_TP9

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 218, entry dates 115, entry months 12; SKIP 26, EXCLUDED 100, exclusion share 0.314465; conditional FLAT CLOSED 218.
Net -158.466667 R; PF R / price 0.245995 / 0.260479; expectancy -0.726911 R; win rate 0.192661; average winner / loser 1.230952 / -1.273737 R.
Conditional CLOSED-only DD 158.466667 R; largest winner share 0.077369; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 12 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 32 | -36.450000 | 0.048717 | 0.048780 | 18 | 3 | 9 |
| 2023-02 | 23 | -10.550000 | 0.418199 | 0.389831 | 18 | 1 | 10 |
| 2023-03 | 11 | -13.583333 | 0.000000 | 0.000000 | 22 | 2 | 15 |
| 2023-04 | 16 | -4.333333 | 0.606061 | 0.600000 | 18 | 8 | 9 |
| 2023-05 | 24 | -21.816667 | 0.181363 | 0.193182 | 21 | 2 | 14 |
| 2023-06 | 17 | -7.350000 | 0.412783 | 0.386364 | 20 | 0 | 15 |
| 2023-07 | 27 | -19.216667 | 0.296093 | 0.333333 | 19 | 7 | 12 |
| 2023-08 | 33 | -21.233333 | 0.315422 | 0.311927 | 14 | 0 | 8 |
| 2023-09 | 29 | -15.950000 | 0.326056 | 0.346667 | 14 | 1 | 8 |
| 2023-10 | 1 | -1.500000 | 0.000000 | 0.000000 | 2 | 1 | 0 |
| 2023-11 | 4 | -5.083333 | 0.000000 | 0.000000 | 6 | 1 | 0 |
| 2023-12 | 1 | -1.400000 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N7_W2_T2_SB1_TP10

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 218, entry dates 115, entry months 12; SKIP 26, EXCLUDED 100, exclusion share 0.314465; conditional FLAT CLOSED 218.
Net -158.466667 R; PF R / price 0.245995 / 0.260479; expectancy -0.726911 R; win rate 0.192661; average winner / loser 1.230952 / -1.273737 R.
Conditional CLOSED-only DD 158.466667 R; largest winner share 0.077369; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 12 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 32 | -36.450000 | 0.048717 | 0.048780 | 18 | 3 | 9 |
| 2023-02 | 23 | -10.550000 | 0.418199 | 0.389831 | 18 | 1 | 10 |
| 2023-03 | 11 | -13.583333 | 0.000000 | 0.000000 | 22 | 2 | 15 |
| 2023-04 | 16 | -4.333333 | 0.606061 | 0.600000 | 18 | 8 | 9 |
| 2023-05 | 24 | -21.816667 | 0.181363 | 0.193182 | 21 | 2 | 14 |
| 2023-06 | 17 | -7.350000 | 0.412783 | 0.386364 | 20 | 0 | 15 |
| 2023-07 | 27 | -19.216667 | 0.296093 | 0.333333 | 19 | 7 | 12 |
| 2023-08 | 33 | -21.233333 | 0.315422 | 0.311927 | 14 | 0 | 8 |
| 2023-09 | 29 | -15.950000 | 0.326056 | 0.346667 | 14 | 1 | 8 |
| 2023-10 | 1 | -1.500000 | 0.000000 | 0.000000 | 2 | 1 | 0 |
| 2023-11 | 4 | -5.083333 | 0.000000 | 0.000000 | 6 | 1 | 0 |
| 2023-12 | 1 | -1.400000 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N7_W2_T3_SB1_TP2

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 182, entry dates 107, entry months 10; SKIP 23, EXCLUDED 73, exclusion share 0.286275; conditional FLAT CLOSED 182.
Net -120.500000 R; PF R / price 0.284229 / 0.289640; expectancy -0.662088 R; win rate 0.208791; average winner / loser 1.259211 / -1.247037 R.
Conditional CLOSED-only DD 120.500000 R; largest winner share 0.069662; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 10 / 2; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 24 | -20.950000 | 0.155809 | 0.150000 | 18 | 1 | 8 |
| 2023-02 | 17 | -7.800000 | 0.472973 | 0.437500 | 18 | 3 | 7 |
| 2023-03 | 7 | -7.166667 | 0.000000 | 0.000000 | 22 | 0 | 11 |
| 2023-04 | 14 | -2.166667 | 0.754717 | 0.724138 | 18 | 7 | 7 |
| 2023-05 | 19 | -17.816667 | 0.195636 | 0.183099 | 21 | 4 | 9 |
| 2023-06 | 21 | -7.416667 | 0.406667 | 0.386364 | 20 | 0 | 12 |
| 2023-07 | 20 | -19.650000 | 0.157255 | 0.171053 | 19 | 4 | 7 |
| 2023-08 | 30 | -20.250000 | 0.319709 | 0.320388 | 14 | 0 | 7 |
| 2023-09 | 27 | -12.450000 | 0.382645 | 0.406250 | 14 | 3 | 5 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 2 | 1 | 0 |
| 2023-11 | 3 | -4.833333 | 0.000000 | 0.000000 | 6 | 0 | 0 |
| 2023-12 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N7_W2_T3_SB1_TP3

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 182, entry dates 107, entry months 10; SKIP 23, EXCLUDED 73, exclusion share 0.286275; conditional FLAT CLOSED 182.
Net -120.166667 R; PF R / price 0.286209 / 0.291496; expectancy -0.660256 R; win rate 0.208791; average winner / loser 1.267982 / -1.247037 R.
Conditional CLOSED-only DD 120.166667 R; largest winner share 0.103770; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 10 / 2; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 24 | -19.283333 | 0.222968 | 0.212500 | 18 | 1 | 8 |
| 2023-02 | 17 | -8.133333 | 0.450450 | 0.416667 | 18 | 3 | 7 |
| 2023-03 | 7 | -7.166667 | 0.000000 | 0.000000 | 22 | 0 | 11 |
| 2023-04 | 14 | -2.166667 | 0.754717 | 0.724138 | 18 | 7 | 7 |
| 2023-05 | 19 | -18.816667 | 0.150489 | 0.140845 | 21 | 4 | 9 |
| 2023-06 | 21 | -7.416667 | 0.406667 | 0.386364 | 20 | 0 | 12 |
| 2023-07 | 20 | -19.650000 | 0.157255 | 0.171053 | 19 | 4 | 7 |
| 2023-08 | 30 | -20.250000 | 0.319709 | 0.320388 | 14 | 0 | 7 |
| 2023-09 | 27 | -12.450000 | 0.382645 | 0.406250 | 14 | 3 | 5 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 2 | 1 | 0 |
| 2023-11 | 3 | -4.833333 | 0.000000 | 0.000000 | 6 | 0 | 0 |
| 2023-12 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N7_W2_T3_SB1_TP4

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 182, entry dates 107, entry months 10; SKIP 23, EXCLUDED 73, exclusion share 0.286275; conditional FLAT CLOSED 182.
Net -118.500000 R; PF R / price 0.296109 / 0.300780; expectancy -0.651099 R; win rate 0.208791; average winner / loser 1.311842 / -1.247037 R.
Conditional CLOSED-only DD 118.500000 R; largest winner share 0.133735; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 10 / 2; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 24 | -17.616667 | 0.290128 | 0.275000 | 18 | 1 | 8 |
| 2023-02 | 17 | -8.133333 | 0.450450 | 0.416667 | 18 | 3 | 7 |
| 2023-03 | 7 | -7.166667 | 0.000000 | 0.000000 | 22 | 0 | 11 |
| 2023-04 | 14 | -2.166667 | 0.754717 | 0.724138 | 18 | 7 | 7 |
| 2023-05 | 19 | -18.816667 | 0.150489 | 0.140845 | 21 | 4 | 9 |
| 2023-06 | 21 | -7.416667 | 0.406667 | 0.386364 | 20 | 0 | 12 |
| 2023-07 | 20 | -19.650000 | 0.157255 | 0.171053 | 19 | 4 | 7 |
| 2023-08 | 30 | -20.250000 | 0.319709 | 0.320388 | 14 | 0 | 7 |
| 2023-09 | 27 | -12.450000 | 0.382645 | 0.406250 | 14 | 3 | 5 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 2 | 1 | 0 |
| 2023-11 | 3 | -4.833333 | 0.000000 | 0.000000 | 6 | 0 | 0 |
| 2023-12 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N7_W2_T3_SB1_TP5

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 182, entry dates 107, entry months 10; SKIP 23, EXCLUDED 73, exclusion share 0.286275; conditional FLAT CLOSED 182.
Net -123.500000 R; PF R / price 0.266409 / 0.272930; expectancy -0.678571 R; win rate 0.208791; average winner / loser 1.180263 / -1.247037 R.
Conditional CLOSED-only DD 123.500000 R; largest winner share 0.074322; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 10 / 2; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 24 | -22.616667 | 0.088650 | 0.087500 | 18 | 1 | 8 |
| 2023-02 | 17 | -8.133333 | 0.450450 | 0.416667 | 18 | 3 | 7 |
| 2023-03 | 7 | -7.166667 | 0.000000 | 0.000000 | 22 | 0 | 11 |
| 2023-04 | 14 | -2.166667 | 0.754717 | 0.724138 | 18 | 7 | 7 |
| 2023-05 | 19 | -18.816667 | 0.150489 | 0.140845 | 21 | 4 | 9 |
| 2023-06 | 21 | -7.416667 | 0.406667 | 0.386364 | 20 | 0 | 12 |
| 2023-07 | 20 | -19.650000 | 0.157255 | 0.171053 | 19 | 4 | 7 |
| 2023-08 | 30 | -20.250000 | 0.319709 | 0.320388 | 14 | 0 | 7 |
| 2023-09 | 27 | -12.450000 | 0.382645 | 0.406250 | 14 | 3 | 5 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 2 | 1 | 0 |
| 2023-11 | 3 | -4.833333 | 0.000000 | 0.000000 | 6 | 0 | 0 |
| 2023-12 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N7_W2_T3_SB1_TP6

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 182, entry dates 107, entry months 10; SKIP 23, EXCLUDED 73, exclusion share 0.286275; conditional FLAT CLOSED 182.
Net -123.500000 R; PF R / price 0.266409 / 0.272930; expectancy -0.678571 R; win rate 0.208791; average winner / loser 1.180263 / -1.247037 R.
Conditional CLOSED-only DD 123.500000 R; largest winner share 0.074322; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 10 / 2; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 24 | -22.616667 | 0.088650 | 0.087500 | 18 | 1 | 8 |
| 2023-02 | 17 | -8.133333 | 0.450450 | 0.416667 | 18 | 3 | 7 |
| 2023-03 | 7 | -7.166667 | 0.000000 | 0.000000 | 22 | 0 | 11 |
| 2023-04 | 14 | -2.166667 | 0.754717 | 0.724138 | 18 | 7 | 7 |
| 2023-05 | 19 | -18.816667 | 0.150489 | 0.140845 | 21 | 4 | 9 |
| 2023-06 | 21 | -7.416667 | 0.406667 | 0.386364 | 20 | 0 | 12 |
| 2023-07 | 20 | -19.650000 | 0.157255 | 0.171053 | 19 | 4 | 7 |
| 2023-08 | 30 | -20.250000 | 0.319709 | 0.320388 | 14 | 0 | 7 |
| 2023-09 | 27 | -12.450000 | 0.382645 | 0.406250 | 14 | 3 | 5 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 2 | 1 | 0 |
| 2023-11 | 3 | -4.833333 | 0.000000 | 0.000000 | 6 | 0 | 0 |
| 2023-12 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N7_W2_T3_SB1_TP7

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 182, entry dates 107, entry months 10; SKIP 23, EXCLUDED 73, exclusion share 0.286275; conditional FLAT CLOSED 182.
Net -123.500000 R; PF R / price 0.266409 / 0.272930; expectancy -0.678571 R; win rate 0.208791; average winner / loser 1.180263 / -1.247037 R.
Conditional CLOSED-only DD 123.500000 R; largest winner share 0.074322; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 10 / 2; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 24 | -22.616667 | 0.088650 | 0.087500 | 18 | 1 | 8 |
| 2023-02 | 17 | -8.133333 | 0.450450 | 0.416667 | 18 | 3 | 7 |
| 2023-03 | 7 | -7.166667 | 0.000000 | 0.000000 | 22 | 0 | 11 |
| 2023-04 | 14 | -2.166667 | 0.754717 | 0.724138 | 18 | 7 | 7 |
| 2023-05 | 19 | -18.816667 | 0.150489 | 0.140845 | 21 | 4 | 9 |
| 2023-06 | 21 | -7.416667 | 0.406667 | 0.386364 | 20 | 0 | 12 |
| 2023-07 | 20 | -19.650000 | 0.157255 | 0.171053 | 19 | 4 | 7 |
| 2023-08 | 30 | -20.250000 | 0.319709 | 0.320388 | 14 | 0 | 7 |
| 2023-09 | 27 | -12.450000 | 0.382645 | 0.406250 | 14 | 3 | 5 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 2 | 1 | 0 |
| 2023-11 | 3 | -4.833333 | 0.000000 | 0.000000 | 6 | 0 | 0 |
| 2023-12 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N7_W2_T3_SB1_TP8

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 182, entry dates 107, entry months 10; SKIP 23, EXCLUDED 73, exclusion share 0.286275; conditional FLAT CLOSED 182.
Net -123.500000 R; PF R / price 0.266409 / 0.272930; expectancy -0.678571 R; win rate 0.208791; average winner / loser 1.180263 / -1.247037 R.
Conditional CLOSED-only DD 123.500000 R; largest winner share 0.074322; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 10 / 2; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 24 | -22.616667 | 0.088650 | 0.087500 | 18 | 1 | 8 |
| 2023-02 | 17 | -8.133333 | 0.450450 | 0.416667 | 18 | 3 | 7 |
| 2023-03 | 7 | -7.166667 | 0.000000 | 0.000000 | 22 | 0 | 11 |
| 2023-04 | 14 | -2.166667 | 0.754717 | 0.724138 | 18 | 7 | 7 |
| 2023-05 | 19 | -18.816667 | 0.150489 | 0.140845 | 21 | 4 | 9 |
| 2023-06 | 21 | -7.416667 | 0.406667 | 0.386364 | 20 | 0 | 12 |
| 2023-07 | 20 | -19.650000 | 0.157255 | 0.171053 | 19 | 4 | 7 |
| 2023-08 | 30 | -20.250000 | 0.319709 | 0.320388 | 14 | 0 | 7 |
| 2023-09 | 27 | -12.450000 | 0.382645 | 0.406250 | 14 | 3 | 5 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 2 | 1 | 0 |
| 2023-11 | 3 | -4.833333 | 0.000000 | 0.000000 | 6 | 0 | 0 |
| 2023-12 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N7_W2_T3_SB1_TP9

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 182, entry dates 107, entry months 10; SKIP 23, EXCLUDED 73, exclusion share 0.286275; conditional FLAT CLOSED 182.
Net -123.500000 R; PF R / price 0.266409 / 0.272930; expectancy -0.678571 R; win rate 0.208791; average winner / loser 1.180263 / -1.247037 R.
Conditional CLOSED-only DD 123.500000 R; largest winner share 0.074322; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 10 / 2; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 24 | -22.616667 | 0.088650 | 0.087500 | 18 | 1 | 8 |
| 2023-02 | 17 | -8.133333 | 0.450450 | 0.416667 | 18 | 3 | 7 |
| 2023-03 | 7 | -7.166667 | 0.000000 | 0.000000 | 22 | 0 | 11 |
| 2023-04 | 14 | -2.166667 | 0.754717 | 0.724138 | 18 | 7 | 7 |
| 2023-05 | 19 | -18.816667 | 0.150489 | 0.140845 | 21 | 4 | 9 |
| 2023-06 | 21 | -7.416667 | 0.406667 | 0.386364 | 20 | 0 | 12 |
| 2023-07 | 20 | -19.650000 | 0.157255 | 0.171053 | 19 | 4 | 7 |
| 2023-08 | 30 | -20.250000 | 0.319709 | 0.320388 | 14 | 0 | 7 |
| 2023-09 | 27 | -12.450000 | 0.382645 | 0.406250 | 14 | 3 | 5 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 2 | 1 | 0 |
| 2023-11 | 3 | -4.833333 | 0.000000 | 0.000000 | 6 | 0 | 0 |
| 2023-12 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N7_W2_T3_SB1_TP10

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 182, entry dates 107, entry months 10; SKIP 23, EXCLUDED 73, exclusion share 0.286275; conditional FLAT CLOSED 182.
Net -123.500000 R; PF R / price 0.266409 / 0.272930; expectancy -0.678571 R; win rate 0.208791; average winner / loser 1.180263 / -1.247037 R.
Conditional CLOSED-only DD 123.500000 R; largest winner share 0.074322; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 10 / 2; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 24 | -22.616667 | 0.088650 | 0.087500 | 18 | 1 | 8 |
| 2023-02 | 17 | -8.133333 | 0.450450 | 0.416667 | 18 | 3 | 7 |
| 2023-03 | 7 | -7.166667 | 0.000000 | 0.000000 | 22 | 0 | 11 |
| 2023-04 | 14 | -2.166667 | 0.754717 | 0.724138 | 18 | 7 | 7 |
| 2023-05 | 19 | -18.816667 | 0.150489 | 0.140845 | 21 | 4 | 9 |
| 2023-06 | 21 | -7.416667 | 0.406667 | 0.386364 | 20 | 0 | 12 |
| 2023-07 | 20 | -19.650000 | 0.157255 | 0.171053 | 19 | 4 | 7 |
| 2023-08 | 30 | -20.250000 | 0.319709 | 0.320388 | 14 | 0 | 7 |
| 2023-09 | 27 | -12.450000 | 0.382645 | 0.406250 | 14 | 3 | 5 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 2 | 1 | 0 |
| 2023-11 | 3 | -4.833333 | 0.000000 | 0.000000 | 6 | 0 | 0 |
| 2023-12 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N7_W3_T2_SB1_TP2

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 226, entry dates 120, entry months 12; SKIP 21, EXCLUDED 106, exclusion share 0.319277; conditional FLAT CLOSED 226.
Net -101.666667 R; PF R / price 0.440829 / 0.434290; expectancy -0.449853 R; win rate 0.243363; average winner / loser 1.457273 / -1.173011 R.
Conditional CLOSED-only DD 101.666667 R; largest winner share 0.041589; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 26 | -16.816667 | 0.293912 | 0.296296 | 18 | 3 | 11 |
| 2023-02 | 18 | -5.316667 | 0.526706 | 0.450000 | 18 | 1 | 11 |
| 2023-03 | 7 | -6.583333 | 0.102273 | 0.120000 | 22 | 3 | 16 |
| 2023-04 | 19 | 1.166667 | 1.130841 | 1.275862 | 18 | 7 | 11 |
| 2023-05 | 21 | -6.316667 | 0.624381 | 0.603448 | 21 | 0 | 13 |
| 2023-06 | 21 | -7.500000 | 0.430380 | 0.413043 | 20 | 4 | 14 |
| 2023-07 | 25 | -16.000000 | 0.284650 | 0.303797 | 19 | 2 | 14 |
| 2023-08 | 51 | -29.383333 | 0.395405 | 0.375723 | 14 | 0 | 7 |
| 2023-09 | 23 | -6.166667 | 0.535759 | 0.555556 | 14 | 0 | 8 |
| 2023-10 | 5 | -0.033333 | 0.992701 | 0.888889 | 2 | 1 | 1 |
| 2023-11 | 8 | -5.650000 | 0.346821 | 0.387097 | 6 | 0 | 0 |
| 2023-12 | 2 | -3.066667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N7_W3_T2_SB1_TP3

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 225, entry dates 120, entry months 12; SKIP 21, EXCLUDED 106, exclusion share 0.320242; conditional FLAT CLOSED 225.
Net -100.333333 R; PF R / price 0.443571 / 0.439333; expectancy -0.445926 R; win rate 0.244444; average winner / loser 1.454242 / -1.170887 R.
Conditional CLOSED-only DD 100.333333 R; largest winner share 0.062513; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 26 | -17.983333 | 0.244927 | 0.271605 | 18 | 3 | 11 |
| 2023-02 | 18 | -5.650000 | 0.497033 | 0.425000 | 18 | 1 | 11 |
| 2023-03 | 7 | -6.583333 | 0.102273 | 0.120000 | 22 | 3 | 16 |
| 2023-04 | 19 | 3.666667 | 1.411215 | 1.586207 | 18 | 7 | 11 |
| 2023-05 | 21 | -6.983333 | 0.584737 | 0.568966 | 21 | 0 | 13 |
| 2023-06 | 21 | -7.500000 | 0.430380 | 0.413043 | 20 | 4 | 14 |
| 2023-07 | 25 | -18.500000 | 0.172876 | 0.177215 | 19 | 2 | 14 |
| 2023-08 | 50 | -26.383333 | 0.439844 | 0.425150 | 14 | 0 | 7 |
| 2023-09 | 23 | -6.166667 | 0.535759 | 0.555556 | 14 | 0 | 8 |
| 2023-10 | 5 | -1.033333 | 0.773723 | 0.722222 | 2 | 1 | 1 |
| 2023-11 | 8 | -4.150000 | 0.520231 | 0.580645 | 6 | 0 | 0 |
| 2023-12 | 2 | -3.066667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N7_W3_T2_SB1_TP4

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 225, entry dates 120, entry months 12; SKIP 21, EXCLUDED 106, exclusion share 0.320242; conditional FLAT CLOSED 225.
Net -97.916667 R; PF R / price 0.456974 / 0.443847; expectancy -0.435185 R; win rate 0.244444; average winner / loser 1.498182 / -1.170887 R.
Conditional CLOSED-only DD 97.916667 R; largest winner share 0.080906; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 26 | -19.483333 | 0.181945 | 0.197531 | 18 | 3 | 11 |
| 2023-02 | 18 | -5.650000 | 0.497033 | 0.425000 | 18 | 1 | 11 |
| 2023-03 | 7 | -6.583333 | 0.102273 | 0.120000 | 22 | 3 | 16 |
| 2023-04 | 19 | 2.916667 | 1.327103 | 1.482759 | 18 | 7 | 11 |
| 2023-05 | 21 | -6.983333 | 0.584737 | 0.568966 | 21 | 0 | 13 |
| 2023-06 | 21 | -7.500000 | 0.430380 | 0.413043 | 20 | 4 | 14 |
| 2023-07 | 25 | -18.500000 | 0.172876 | 0.177215 | 19 | 2 | 14 |
| 2023-08 | 50 | -23.216667 | 0.507077 | 0.491018 | 14 | 0 | 7 |
| 2023-09 | 23 | -6.166667 | 0.535759 | 0.555556 | 14 | 0 | 8 |
| 2023-10 | 5 | -1.033333 | 0.773723 | 0.722222 | 2 | 1 | 1 |
| 2023-11 | 8 | -2.650000 | 0.693642 | 0.774194 | 6 | 0 | 0 |
| 2023-12 | 2 | -3.066667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N7_W3_T2_SB1_TP5

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 225, entry dates 120, entry months 12; SKIP 21, EXCLUDED 106, exclusion share 0.320242; conditional FLAT CLOSED 225.
Net -93.250000 R; PF R / price 0.482854 / 0.463982; expectancy -0.414444 R; win rate 0.244444; average winner / loser 1.583030 / -1.170887 R.
Conditional CLOSED-only DD 93.250000 R; largest winner share 0.095712; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 26 | -19.483333 | 0.181945 | 0.197531 | 18 | 3 | 11 |
| 2023-02 | 18 | -5.650000 | 0.497033 | 0.425000 | 18 | 1 | 11 |
| 2023-03 | 7 | -6.583333 | 0.102273 | 0.120000 | 22 | 3 | 16 |
| 2023-04 | 19 | 2.916667 | 1.327103 | 1.482759 | 18 | 7 | 11 |
| 2023-05 | 21 | -6.983333 | 0.584737 | 0.568966 | 21 | 0 | 13 |
| 2023-06 | 21 | -7.500000 | 0.430380 | 0.413043 | 20 | 4 | 14 |
| 2023-07 | 25 | -18.500000 | 0.172876 | 0.177215 | 19 | 2 | 14 |
| 2023-08 | 50 | -20.050000 | 0.574310 | 0.556886 | 14 | 0 | 7 |
| 2023-09 | 23 | -6.166667 | 0.535759 | 0.555556 | 14 | 0 | 8 |
| 2023-10 | 5 | -1.033333 | 0.773723 | 0.722222 | 2 | 1 | 1 |
| 2023-11 | 8 | -1.150000 | 0.867052 | 0.967742 | 6 | 0 | 0 |
| 2023-12 | 2 | -3.066667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N7_W3_T2_SB1_TP6

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 225, entry dates 120, entry months 12; SKIP 21, EXCLUDED 106, exclusion share 0.320242; conditional FLAT CLOSED 225.
Net -90.250000 R; PF R / price 0.499492 / 0.475438; expectancy -0.401111 R; win rate 0.244444; average winner / loser 1.637576 / -1.170887 R.
Conditional CLOSED-only DD 90.250000 R; largest winner share 0.099926; largest positive month share 0.892857. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 26 | -19.483333 | 0.181945 | 0.197531 | 18 | 3 | 11 |
| 2023-02 | 18 | -5.650000 | 0.497033 | 0.425000 | 18 | 1 | 11 |
| 2023-03 | 7 | -6.583333 | 0.102273 | 0.120000 | 22 | 3 | 16 |
| 2023-04 | 19 | 2.916667 | 1.327103 | 1.482759 | 18 | 7 | 11 |
| 2023-05 | 21 | -6.983333 | 0.584737 | 0.568966 | 21 | 0 | 13 |
| 2023-06 | 21 | -7.500000 | 0.430380 | 0.413043 | 20 | 4 | 14 |
| 2023-07 | 25 | -18.500000 | 0.172876 | 0.177215 | 19 | 2 | 14 |
| 2023-08 | 50 | -18.550000 | 0.606157 | 0.592814 | 14 | 0 | 7 |
| 2023-09 | 23 | -6.166667 | 0.535759 | 0.555556 | 14 | 0 | 8 |
| 2023-10 | 5 | -1.033333 | 0.773723 | 0.722222 | 2 | 1 | 1 |
| 2023-11 | 8 | 0.350000 | 1.040462 | 1.161290 | 6 | 0 | 0 |
| 2023-12 | 2 | -3.066667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N7_W3_T2_SB1_TP7

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 225, entry dates 120, entry months 12; SKIP 21, EXCLUDED 106, exclusion share 0.320242; conditional FLAT CLOSED 225.
Net -89.500000 R; PF R / price 0.503651 / 0.485332; expectancy -0.397778 R; win rate 0.244444; average winner / loser 1.651212 / -1.170887 R.
Conditional CLOSED-only DD 89.500000 R; largest winner share 0.115618; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 26 | -19.483333 | 0.181945 | 0.197531 | 18 | 3 | 11 |
| 2023-02 | 18 | -5.650000 | 0.497033 | 0.425000 | 18 | 1 | 11 |
| 2023-03 | 7 | -6.583333 | 0.102273 | 0.120000 | 22 | 3 | 16 |
| 2023-04 | 19 | 2.916667 | 1.327103 | 1.482759 | 18 | 7 | 11 |
| 2023-05 | 21 | -6.983333 | 0.584737 | 0.568966 | 21 | 0 | 13 |
| 2023-06 | 21 | -7.500000 | 0.430380 | 0.413043 | 20 | 4 | 14 |
| 2023-07 | 25 | -18.500000 | 0.172876 | 0.177215 | 19 | 2 | 14 |
| 2023-08 | 50 | -17.050000 | 0.638004 | 0.628743 | 14 | 0 | 7 |
| 2023-09 | 23 | -6.166667 | 0.535759 | 0.555556 | 14 | 0 | 8 |
| 2023-10 | 5 | -1.033333 | 0.773723 | 0.722222 | 2 | 1 | 1 |
| 2023-11 | 8 | -0.400000 | 0.953757 | 1.064516 | 6 | 0 | 0 |
| 2023-12 | 2 | -3.066667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N7_W3_T2_SB1_TP8

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 225, entry dates 120, entry months 12; SKIP 21, EXCLUDED 106, exclusion share 0.320242; conditional FLAT CLOSED 225.
Net -88.000000 R; PF R / price 0.511970 / 0.495747; expectancy -0.391111 R; win rate 0.244444; average winner / loser 1.678485 / -1.170887 R.
Conditional CLOSED-only DD 88.000000 R; largest winner share 0.129987; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 26 | -19.483333 | 0.181945 | 0.197531 | 18 | 3 | 11 |
| 2023-02 | 18 | -5.650000 | 0.497033 | 0.425000 | 18 | 1 | 11 |
| 2023-03 | 7 | -6.583333 | 0.102273 | 0.120000 | 22 | 3 | 16 |
| 2023-04 | 19 | 2.916667 | 1.327103 | 1.482759 | 18 | 7 | 11 |
| 2023-05 | 21 | -6.983333 | 0.584737 | 0.568966 | 21 | 0 | 13 |
| 2023-06 | 21 | -7.500000 | 0.430380 | 0.413043 | 20 | 4 | 14 |
| 2023-07 | 25 | -18.500000 | 0.172876 | 0.177215 | 19 | 2 | 14 |
| 2023-08 | 50 | -15.550000 | 0.669851 | 0.664671 | 14 | 0 | 7 |
| 2023-09 | 23 | -6.166667 | 0.535759 | 0.555556 | 14 | 0 | 8 |
| 2023-10 | 5 | -1.033333 | 0.773723 | 0.722222 | 2 | 1 | 1 |
| 2023-11 | 8 | -0.400000 | 0.953757 | 1.064516 | 6 | 0 | 0 |
| 2023-12 | 2 | -3.066667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N7_W3_T2_SB1_TP9

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 225, entry dates 120, entry months 12; SKIP 21, EXCLUDED 106, exclusion share 0.320242; conditional FLAT CLOSED 225.
Net -89.500000 R; PF R / price 0.503651 / 0.485332; expectancy -0.397778 R; win rate 0.244444; average winner / loser 1.651212 / -1.170887 R.
Conditional CLOSED-only DD 89.500000 R; largest winner share 0.115618; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 26 | -19.483333 | 0.181945 | 0.197531 | 18 | 3 | 11 |
| 2023-02 | 18 | -5.650000 | 0.497033 | 0.425000 | 18 | 1 | 11 |
| 2023-03 | 7 | -6.583333 | 0.102273 | 0.120000 | 22 | 3 | 16 |
| 2023-04 | 19 | 2.916667 | 1.327103 | 1.482759 | 18 | 7 | 11 |
| 2023-05 | 21 | -6.983333 | 0.584737 | 0.568966 | 21 | 0 | 13 |
| 2023-06 | 21 | -7.500000 | 0.430380 | 0.413043 | 20 | 4 | 14 |
| 2023-07 | 25 | -18.500000 | 0.172876 | 0.177215 | 19 | 2 | 14 |
| 2023-08 | 50 | -17.050000 | 0.638004 | 0.628743 | 14 | 0 | 7 |
| 2023-09 | 23 | -6.166667 | 0.535759 | 0.555556 | 14 | 0 | 8 |
| 2023-10 | 5 | -1.033333 | 0.773723 | 0.722222 | 2 | 1 | 1 |
| 2023-11 | 8 | -0.400000 | 0.953757 | 1.064516 | 6 | 0 | 0 |
| 2023-12 | 2 | -3.066667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N7_W3_T2_SB1_TP10

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 225, entry dates 120, entry months 12; SKIP 21, EXCLUDED 106, exclusion share 0.320242; conditional FLAT CLOSED 225.
Net -89.500000 R; PF R / price 0.503651 / 0.485332; expectancy -0.397778 R; win rate 0.244444; average winner / loser 1.651212 / -1.170887 R.
Conditional CLOSED-only DD 89.500000 R; largest winner share 0.115618; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 26 | -19.483333 | 0.181945 | 0.197531 | 18 | 3 | 11 |
| 2023-02 | 18 | -5.650000 | 0.497033 | 0.425000 | 18 | 1 | 11 |
| 2023-03 | 7 | -6.583333 | 0.102273 | 0.120000 | 22 | 3 | 16 |
| 2023-04 | 19 | 2.916667 | 1.327103 | 1.482759 | 18 | 7 | 11 |
| 2023-05 | 21 | -6.983333 | 0.584737 | 0.568966 | 21 | 0 | 13 |
| 2023-06 | 21 | -7.500000 | 0.430380 | 0.413043 | 20 | 4 | 14 |
| 2023-07 | 25 | -18.500000 | 0.172876 | 0.177215 | 19 | 2 | 14 |
| 2023-08 | 50 | -17.050000 | 0.638004 | 0.628743 | 14 | 0 | 7 |
| 2023-09 | 23 | -6.166667 | 0.535759 | 0.555556 | 14 | 0 | 8 |
| 2023-10 | 5 | -1.033333 | 0.773723 | 0.722222 | 2 | 1 | 1 |
| 2023-11 | 8 | -0.400000 | 0.953757 | 1.064516 | 6 | 0 | 0 |
| 2023-12 | 2 | -3.066667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N7_W3_T3_SB1_TP2

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 196, entry dates 114, entry months 12; SKIP 24, EXCLUDED 75, exclusion share 0.276753; conditional FLAT CLOSED 196.
Net -114.033333 R; PF R / price 0.343756 / 0.357078; expectancy -0.581803 R; win rate 0.234694; average winner / loser 1.298551 / -1.241190 R.
Conditional CLOSED-only DD 114.033333 R; largest winner share 0.055804; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 12 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 20 | -17.233333 | 0.037244 | 0.032787 | 18 | 1 | 10 |
| 2023-02 | 19 | -12.566667 | 0.307622 | 0.274194 | 18 | 3 | 7 |
| 2023-03 | 9 | -11.333333 | 0.000000 | 0.000000 | 22 | 1 | 11 |
| 2023-04 | 16 | -0.333333 | 0.962264 | 1.000000 | 18 | 7 | 7 |
| 2023-05 | 19 | -6.133333 | 0.613851 | 0.563636 | 21 | 4 | 8 |
| 2023-06 | 25 | -11.483333 | 0.387011 | 0.380952 | 20 | 2 | 11 |
| 2023-07 | 20 | -15.866667 | 0.215815 | 0.220588 | 19 | 3 | 10 |
| 2023-08 | 36 | -19.816667 | 0.437559 | 0.413223 | 14 | 0 | 5 |
| 2023-09 | 23 | -6.400000 | 0.561644 | 0.583333 | 14 | 2 | 5 |
| 2023-10 | 2 | -3.066667 | 0.000000 | 0.000000 | 2 | 1 | 1 |
| 2023-11 | 6 | -8.133333 | 0.000000 | 0.000000 | 6 | 0 | 0 |
| 2023-12 | 1 | -1.666667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N7_W3_T3_SB1_TP3

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 196, entry dates 114, entry months 12; SKIP 24, EXCLUDED 75, exclusion share 0.276753; conditional FLAT CLOSED 196.
Net -114.200000 R; PF R / price 0.342797 / 0.358900; expectancy -0.582653 R; win rate 0.234694; average winner / loser 1.294928 / -1.241190 R.
Conditional CLOSED-only DD 114.200000 R; largest winner share 0.075546; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 20 | -17.233333 | 0.037244 | 0.032787 | 18 | 1 | 10 |
| 2023-02 | 19 | -12.900000 | 0.289256 | 0.258065 | 18 | 3 | 7 |
| 2023-03 | 9 | -11.333333 | 0.000000 | 0.000000 | 22 | 1 | 11 |
| 2023-04 | 16 | 0.666667 | 1.075472 | 1.103448 | 18 | 7 | 7 |
| 2023-05 | 19 | -6.800000 | 0.571878 | 0.527273 | 21 | 4 | 8 |
| 2023-06 | 25 | -11.483333 | 0.387011 | 0.380952 | 20 | 2 | 11 |
| 2023-07 | 20 | -15.866667 | 0.215815 | 0.220588 | 19 | 3 | 10 |
| 2023-08 | 36 | -19.983333 | 0.432829 | 0.421488 | 14 | 0 | 5 |
| 2023-09 | 23 | -6.400000 | 0.561644 | 0.583333 | 14 | 2 | 5 |
| 2023-10 | 2 | -3.066667 | 0.000000 | 0.000000 | 2 | 1 | 1 |
| 2023-11 | 6 | -8.133333 | 0.000000 | 0.000000 | 6 | 0 | 0 |
| 2023-12 | 1 | -1.666667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N7_W3_T3_SB1_TP4

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 196, entry dates 114, entry months 12; SKIP 24, EXCLUDED 75, exclusion share 0.276753; conditional FLAT CLOSED 196.
Net -112.700000 R; PF R / price 0.351429 / 0.369831; expectancy -0.575000 R; win rate 0.234694; average winner / loser 1.327536 / -1.241190 R.
Conditional CLOSED-only DD 112.700000 R; largest winner share 0.098253; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 20 | -17.233333 | 0.037244 | 0.032787 | 18 | 1 | 10 |
| 2023-02 | 19 | -12.900000 | 0.289256 | 0.258065 | 18 | 3 | 7 |
| 2023-03 | 9 | -11.333333 | 0.000000 | 0.000000 | 22 | 1 | 11 |
| 2023-04 | 16 | 0.666667 | 1.075472 | 1.103448 | 18 | 7 | 7 |
| 2023-05 | 19 | -6.800000 | 0.571878 | 0.527273 | 21 | 4 | 8 |
| 2023-06 | 25 | -11.483333 | 0.387011 | 0.380952 | 20 | 2 | 11 |
| 2023-07 | 20 | -15.866667 | 0.215815 | 0.220588 | 19 | 3 | 10 |
| 2023-08 | 36 | -18.483333 | 0.475402 | 0.471074 | 14 | 0 | 5 |
| 2023-09 | 23 | -6.400000 | 0.561644 | 0.583333 | 14 | 2 | 5 |
| 2023-10 | 2 | -3.066667 | 0.000000 | 0.000000 | 2 | 1 | 1 |
| 2023-11 | 6 | -8.133333 | 0.000000 | 0.000000 | 6 | 0 | 0 |
| 2023-12 | 1 | -1.666667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N7_W3_T3_SB1_TP5

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 196, entry dates 114, entry months 12; SKIP 24, EXCLUDED 75, exclusion share 0.276753; conditional FLAT CLOSED 196.
Net -111.200000 R; PF R / price 0.360061 / 0.380762; expectancy -0.567347 R; win rate 0.234694; average winner / loser 1.360145 / -1.241190 R.
Conditional CLOSED-only DD 111.200000 R; largest winner share 0.119872; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 20 | -17.233333 | 0.037244 | 0.032787 | 18 | 1 | 10 |
| 2023-02 | 19 | -12.900000 | 0.289256 | 0.258065 | 18 | 3 | 7 |
| 2023-03 | 9 | -11.333333 | 0.000000 | 0.000000 | 22 | 1 | 11 |
| 2023-04 | 16 | 0.666667 | 1.075472 | 1.103448 | 18 | 7 | 7 |
| 2023-05 | 19 | -6.800000 | 0.571878 | 0.527273 | 21 | 4 | 8 |
| 2023-06 | 25 | -11.483333 | 0.387011 | 0.380952 | 20 | 2 | 11 |
| 2023-07 | 20 | -15.866667 | 0.215815 | 0.220588 | 19 | 3 | 10 |
| 2023-08 | 36 | -16.983333 | 0.517975 | 0.520661 | 14 | 0 | 5 |
| 2023-09 | 23 | -6.400000 | 0.561644 | 0.583333 | 14 | 2 | 5 |
| 2023-10 | 2 | -3.066667 | 0.000000 | 0.000000 | 2 | 1 | 1 |
| 2023-11 | 6 | -8.133333 | 0.000000 | 0.000000 | 6 | 0 | 0 |
| 2023-12 | 1 | -1.666667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N7_W3_T3_SB1_TP6

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 196, entry dates 114, entry months 12; SKIP 24, EXCLUDED 75, exclusion share 0.276753; conditional FLAT CLOSED 196.
Net -109.700000 R; PF R / price 0.368694 / 0.391692; expectancy -0.559694 R; win rate 0.234694; average winner / loser 1.392754 / -1.241190 R.
Conditional CLOSED-only DD 109.700000 R; largest winner share 0.140479; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 20 | -17.233333 | 0.037244 | 0.032787 | 18 | 1 | 10 |
| 2023-02 | 19 | -12.900000 | 0.289256 | 0.258065 | 18 | 3 | 7 |
| 2023-03 | 9 | -11.333333 | 0.000000 | 0.000000 | 22 | 1 | 11 |
| 2023-04 | 16 | 0.666667 | 1.075472 | 1.103448 | 18 | 7 | 7 |
| 2023-05 | 19 | -6.800000 | 0.571878 | 0.527273 | 21 | 4 | 8 |
| 2023-06 | 25 | -11.483333 | 0.387011 | 0.380952 | 20 | 2 | 11 |
| 2023-07 | 20 | -15.866667 | 0.215815 | 0.220588 | 19 | 3 | 10 |
| 2023-08 | 36 | -15.483333 | 0.560549 | 0.570248 | 14 | 0 | 5 |
| 2023-09 | 23 | -6.400000 | 0.561644 | 0.583333 | 14 | 2 | 5 |
| 2023-10 | 2 | -3.066667 | 0.000000 | 0.000000 | 2 | 1 | 1 |
| 2023-11 | 6 | -8.133333 | 0.000000 | 0.000000 | 6 | 0 | 0 |
| 2023-12 | 1 | -1.666667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N7_W3_T3_SB1_TP7

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 196, entry dates 114, entry months 12; SKIP 24, EXCLUDED 75, exclusion share 0.276753; conditional FLAT CLOSED 196.
Net -108.200000 R; PF R / price 0.377326 / 0.402623; expectancy -0.552041 R; win rate 0.234694; average winner / loser 1.425362 / -1.241190 R.
Conditional CLOSED-only DD 108.200000 R; largest winner share 0.160142; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 20 | -17.233333 | 0.037244 | 0.032787 | 18 | 1 | 10 |
| 2023-02 | 19 | -12.900000 | 0.289256 | 0.258065 | 18 | 3 | 7 |
| 2023-03 | 9 | -11.333333 | 0.000000 | 0.000000 | 22 | 1 | 11 |
| 2023-04 | 16 | 0.666667 | 1.075472 | 1.103448 | 18 | 7 | 7 |
| 2023-05 | 19 | -6.800000 | 0.571878 | 0.527273 | 21 | 4 | 8 |
| 2023-06 | 25 | -11.483333 | 0.387011 | 0.380952 | 20 | 2 | 11 |
| 2023-07 | 20 | -15.866667 | 0.215815 | 0.220588 | 19 | 3 | 10 |
| 2023-08 | 36 | -13.983333 | 0.603122 | 0.619835 | 14 | 0 | 5 |
| 2023-09 | 23 | -6.400000 | 0.561644 | 0.583333 | 14 | 2 | 5 |
| 2023-10 | 2 | -3.066667 | 0.000000 | 0.000000 | 2 | 1 | 1 |
| 2023-11 | 6 | -8.133333 | 0.000000 | 0.000000 | 6 | 0 | 0 |
| 2023-12 | 1 | -1.666667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N7_W3_T3_SB1_TP8

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 196, entry dates 114, entry months 12; SKIP 24, EXCLUDED 75, exclusion share 0.276753; conditional FLAT CLOSED 196.
Net -106.700000 R; PF R / price 0.385958 / 0.413554; expectancy -0.544388 R; win rate 0.234694; average winner / loser 1.457971 / -1.241190 R.
Conditional CLOSED-only DD 106.700000 R; largest winner share 0.178926; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 20 | -17.233333 | 0.037244 | 0.032787 | 18 | 1 | 10 |
| 2023-02 | 19 | -12.900000 | 0.289256 | 0.258065 | 18 | 3 | 7 |
| 2023-03 | 9 | -11.333333 | 0.000000 | 0.000000 | 22 | 1 | 11 |
| 2023-04 | 16 | 0.666667 | 1.075472 | 1.103448 | 18 | 7 | 7 |
| 2023-05 | 19 | -6.800000 | 0.571878 | 0.527273 | 21 | 4 | 8 |
| 2023-06 | 25 | -11.483333 | 0.387011 | 0.380952 | 20 | 2 | 11 |
| 2023-07 | 20 | -15.866667 | 0.215815 | 0.220588 | 19 | 3 | 10 |
| 2023-08 | 36 | -12.483333 | 0.645695 | 0.669421 | 14 | 0 | 5 |
| 2023-09 | 23 | -6.400000 | 0.561644 | 0.583333 | 14 | 2 | 5 |
| 2023-10 | 2 | -3.066667 | 0.000000 | 0.000000 | 2 | 1 | 1 |
| 2023-11 | 6 | -8.133333 | 0.000000 | 0.000000 | 6 | 0 | 0 |
| 2023-12 | 1 | -1.666667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N7_W3_T3_SB1_TP9

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 196, entry dates 114, entry months 12; SKIP 24, EXCLUDED 75, exclusion share 0.276753; conditional FLAT CLOSED 196.
Net -108.200000 R; PF R / price 0.377326 / 0.402623; expectancy -0.552041 R; win rate 0.234694; average winner / loser 1.425362 / -1.241190 R.
Conditional CLOSED-only DD 108.200000 R; largest winner share 0.160142; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 20 | -17.233333 | 0.037244 | 0.032787 | 18 | 1 | 10 |
| 2023-02 | 19 | -12.900000 | 0.289256 | 0.258065 | 18 | 3 | 7 |
| 2023-03 | 9 | -11.333333 | 0.000000 | 0.000000 | 22 | 1 | 11 |
| 2023-04 | 16 | 0.666667 | 1.075472 | 1.103448 | 18 | 7 | 7 |
| 2023-05 | 19 | -6.800000 | 0.571878 | 0.527273 | 21 | 4 | 8 |
| 2023-06 | 25 | -11.483333 | 0.387011 | 0.380952 | 20 | 2 | 11 |
| 2023-07 | 20 | -15.866667 | 0.215815 | 0.220588 | 19 | 3 | 10 |
| 2023-08 | 36 | -13.983333 | 0.603122 | 0.619835 | 14 | 0 | 5 |
| 2023-09 | 23 | -6.400000 | 0.561644 | 0.583333 | 14 | 2 | 5 |
| 2023-10 | 2 | -3.066667 | 0.000000 | 0.000000 | 2 | 1 | 1 |
| 2023-11 | 6 | -8.133333 | 0.000000 | 0.000000 | 6 | 0 | 0 |
| 2023-12 | 1 | -1.666667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N7_W3_T3_SB1_TP10

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 196, entry dates 114, entry months 12; SKIP 24, EXCLUDED 75, exclusion share 0.276753; conditional FLAT CLOSED 196.
Net -108.200000 R; PF R / price 0.377326 / 0.402623; expectancy -0.552041 R; win rate 0.234694; average winner / loser 1.425362 / -1.241190 R.
Conditional CLOSED-only DD 108.200000 R; largest winner share 0.160142; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 20 | -17.233333 | 0.037244 | 0.032787 | 18 | 1 | 10 |
| 2023-02 | 19 | -12.900000 | 0.289256 | 0.258065 | 18 | 3 | 7 |
| 2023-03 | 9 | -11.333333 | 0.000000 | 0.000000 | 22 | 1 | 11 |
| 2023-04 | 16 | 0.666667 | 1.075472 | 1.103448 | 18 | 7 | 7 |
| 2023-05 | 19 | -6.800000 | 0.571878 | 0.527273 | 21 | 4 | 8 |
| 2023-06 | 25 | -11.483333 | 0.387011 | 0.380952 | 20 | 2 | 11 |
| 2023-07 | 20 | -15.866667 | 0.215815 | 0.220588 | 19 | 3 | 10 |
| 2023-08 | 36 | -13.983333 | 0.603122 | 0.619835 | 14 | 0 | 5 |
| 2023-09 | 23 | -6.400000 | 0.561644 | 0.583333 | 14 | 2 | 5 |
| 2023-10 | 2 | -3.066667 | 0.000000 | 0.000000 | 2 | 1 | 1 |
| 2023-11 | 6 | -8.133333 | 0.000000 | 0.000000 | 6 | 0 | 0 |
| 2023-12 | 1 | -1.666667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N8_W2_T2_SB1_TP2

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 175, entry dates 101, entry months 11; SKIP 26, EXCLUDED 94, exclusion share 0.349442; conditional FLAT CLOSED 167.
Net -118.450000 R; PF R / price 0.252052 / 0.258438; expectancy -0.676857 R; win rate 0.205714; average winner / loser 1.108796 / -1.237240 R.
Conditional CLOSED-only DD 118.450000 R; largest winner share 0.083507; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 11 / 1; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 24 | -26.833333 | 0.110497 | 0.101010 | 18 | 4 | 11 |
| 2023-02 | 19 | -9.566667 | 0.217984 | 0.214286 | 18 | 1 | 11 |
| 2023-03 | 13 | -12.066667 | 0.020298 | 0.023810 | 22 | 5 | 12 |
| 2023-04 | 16 | -1.416667 | 0.844037 | 0.793103 | 18 | 1 | 8 |
| 2023-05 | 12 | -5.116667 | 0.508013 | 0.562500 | 21 | 3 | 14 |
| 2023-06 | 15 | -10.083333 | 0.266667 | 0.250000 | 20 | 3 | 15 |
| 2023-07 | 25 | -25.250000 | 0.103550 | 0.109890 | 19 | 5 | 11 |
| 2023-08 | 29 | -19.150000 | 0.317696 | 0.326733 | 14 | 1 | 4 |
| 2023-09 | 19 | -5.666667 | 0.479326 | 0.513514 | 14 | 3 | 8 |
| 2023-10 | 1 | -1.500000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-11 | 2 | -1.800000 | 0.000000 | 0.000000 | 6 | 0 | 0 |
| 2023-12 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N8_W2_T2_SB1_TP3

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 175, entry dates 101, entry months 11; SKIP 26, EXCLUDED 94, exclusion share 0.349442; conditional FLAT CLOSED 167.
Net -117.116667 R; PF R / price 0.260471 / 0.266152; expectancy -0.669238 R; win rate 0.205714; average winner / loser 1.145833 / -1.237240 R.
Conditional CLOSED-only DD 117.116667 R; largest winner share 0.121212; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 11 / 1; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 24 | -25.166667 | 0.165746 | 0.151515 | 18 | 4 | 11 |
| 2023-02 | 19 | -9.566667 | 0.217984 | 0.214286 | 18 | 1 | 11 |
| 2023-03 | 13 | -12.066667 | 0.020298 | 0.023810 | 22 | 5 | 12 |
| 2023-04 | 16 | -1.750000 | 0.807339 | 0.758621 | 18 | 1 | 8 |
| 2023-05 | 12 | -5.116667 | 0.508013 | 0.562500 | 21 | 3 | 14 |
| 2023-06 | 15 | -10.083333 | 0.266667 | 0.250000 | 20 | 3 | 15 |
| 2023-07 | 25 | -25.250000 | 0.103550 | 0.109890 | 19 | 5 | 11 |
| 2023-08 | 29 | -19.150000 | 0.317696 | 0.326733 | 14 | 1 | 4 |
| 2023-09 | 19 | -5.666667 | 0.479326 | 0.513514 | 14 | 3 | 8 |
| 2023-10 | 1 | -1.500000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-11 | 2 | -1.800000 | 0.000000 | 0.000000 | 6 | 0 | 0 |
| 2023-12 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N8_W2_T2_SB1_TP4

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 175, entry dates 101, entry months 11; SKIP 26, EXCLUDED 94, exclusion share 0.349442; conditional FLAT CLOSED 167.
Net -115.450000 R; PF R / price 0.270996 / 0.275796; expectancy -0.659714 R; win rate 0.205714; average winner / loser 1.192130 / -1.237240 R.
Conditional CLOSED-only DD 115.450000 R; largest winner share 0.155340; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 11 / 1; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 24 | -23.500000 | 0.220994 | 0.202020 | 18 | 4 | 11 |
| 2023-02 | 19 | -9.566667 | 0.217984 | 0.214286 | 18 | 1 | 11 |
| 2023-03 | 13 | -12.066667 | 0.020298 | 0.023810 | 22 | 5 | 12 |
| 2023-04 | 16 | -1.750000 | 0.807339 | 0.758621 | 18 | 1 | 8 |
| 2023-05 | 12 | -5.116667 | 0.508013 | 0.562500 | 21 | 3 | 14 |
| 2023-06 | 15 | -10.083333 | 0.266667 | 0.250000 | 20 | 3 | 15 |
| 2023-07 | 25 | -25.250000 | 0.103550 | 0.109890 | 19 | 5 | 11 |
| 2023-08 | 29 | -19.150000 | 0.317696 | 0.326733 | 14 | 1 | 4 |
| 2023-09 | 19 | -5.666667 | 0.479326 | 0.513514 | 14 | 3 | 8 |
| 2023-10 | 1 | -1.500000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-11 | 2 | -1.800000 | 0.000000 | 0.000000 | 6 | 0 | 0 |
| 2023-12 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N8_W2_T2_SB1_TP5

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 175, entry dates 101, entry months 11; SKIP 26, EXCLUDED 94, exclusion share 0.349442; conditional FLAT CLOSED 167.
Net -119.450000 R; PF R / price 0.245738 / 0.252652; expectancy -0.682571 R; win rate 0.205714; average winner / loser 1.081019 / -1.237240 R.
Conditional CLOSED-only DD 119.450000 R; largest winner share 0.085653; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 11 / 1; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 24 | -27.500000 | 0.088398 | 0.080808 | 18 | 4 | 11 |
| 2023-02 | 19 | -9.566667 | 0.217984 | 0.214286 | 18 | 1 | 11 |
| 2023-03 | 13 | -12.066667 | 0.020298 | 0.023810 | 22 | 5 | 12 |
| 2023-04 | 16 | -1.750000 | 0.807339 | 0.758621 | 18 | 1 | 8 |
| 2023-05 | 12 | -5.116667 | 0.508013 | 0.562500 | 21 | 3 | 14 |
| 2023-06 | 15 | -10.083333 | 0.266667 | 0.250000 | 20 | 3 | 15 |
| 2023-07 | 25 | -25.250000 | 0.103550 | 0.109890 | 19 | 5 | 11 |
| 2023-08 | 29 | -19.150000 | 0.317696 | 0.326733 | 14 | 1 | 4 |
| 2023-09 | 19 | -5.666667 | 0.479326 | 0.513514 | 14 | 3 | 8 |
| 2023-10 | 1 | -1.500000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-11 | 2 | -1.800000 | 0.000000 | 0.000000 | 6 | 0 | 0 |
| 2023-12 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N8_W2_T2_SB1_TP6

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 175, entry dates 101, entry months 11; SKIP 26, EXCLUDED 94, exclusion share 0.349442; conditional FLAT CLOSED 167.
Net -119.450000 R; PF R / price 0.245738 / 0.252652; expectancy -0.682571 R; win rate 0.205714; average winner / loser 1.081019 / -1.237240 R.
Conditional CLOSED-only DD 119.450000 R; largest winner share 0.085653; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 11 / 1; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 24 | -27.500000 | 0.088398 | 0.080808 | 18 | 4 | 11 |
| 2023-02 | 19 | -9.566667 | 0.217984 | 0.214286 | 18 | 1 | 11 |
| 2023-03 | 13 | -12.066667 | 0.020298 | 0.023810 | 22 | 5 | 12 |
| 2023-04 | 16 | -1.750000 | 0.807339 | 0.758621 | 18 | 1 | 8 |
| 2023-05 | 12 | -5.116667 | 0.508013 | 0.562500 | 21 | 3 | 14 |
| 2023-06 | 15 | -10.083333 | 0.266667 | 0.250000 | 20 | 3 | 15 |
| 2023-07 | 25 | -25.250000 | 0.103550 | 0.109890 | 19 | 5 | 11 |
| 2023-08 | 29 | -19.150000 | 0.317696 | 0.326733 | 14 | 1 | 4 |
| 2023-09 | 19 | -5.666667 | 0.479326 | 0.513514 | 14 | 3 | 8 |
| 2023-10 | 1 | -1.500000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-11 | 2 | -1.800000 | 0.000000 | 0.000000 | 6 | 0 | 0 |
| 2023-12 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N8_W2_T2_SB1_TP7

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 175, entry dates 101, entry months 11; SKIP 26, EXCLUDED 94, exclusion share 0.349442; conditional FLAT CLOSED 167.
Net -119.450000 R; PF R / price 0.245738 / 0.252652; expectancy -0.682571 R; win rate 0.205714; average winner / loser 1.081019 / -1.237240 R.
Conditional CLOSED-only DD 119.450000 R; largest winner share 0.085653; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 11 / 1; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 24 | -27.500000 | 0.088398 | 0.080808 | 18 | 4 | 11 |
| 2023-02 | 19 | -9.566667 | 0.217984 | 0.214286 | 18 | 1 | 11 |
| 2023-03 | 13 | -12.066667 | 0.020298 | 0.023810 | 22 | 5 | 12 |
| 2023-04 | 16 | -1.750000 | 0.807339 | 0.758621 | 18 | 1 | 8 |
| 2023-05 | 12 | -5.116667 | 0.508013 | 0.562500 | 21 | 3 | 14 |
| 2023-06 | 15 | -10.083333 | 0.266667 | 0.250000 | 20 | 3 | 15 |
| 2023-07 | 25 | -25.250000 | 0.103550 | 0.109890 | 19 | 5 | 11 |
| 2023-08 | 29 | -19.150000 | 0.317696 | 0.326733 | 14 | 1 | 4 |
| 2023-09 | 19 | -5.666667 | 0.479326 | 0.513514 | 14 | 3 | 8 |
| 2023-10 | 1 | -1.500000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-11 | 2 | -1.800000 | 0.000000 | 0.000000 | 6 | 0 | 0 |
| 2023-12 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N8_W2_T2_SB1_TP8

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 175, entry dates 101, entry months 11; SKIP 26, EXCLUDED 94, exclusion share 0.349442; conditional FLAT CLOSED 167.
Net -119.450000 R; PF R / price 0.245738 / 0.252652; expectancy -0.682571 R; win rate 0.205714; average winner / loser 1.081019 / -1.237240 R.
Conditional CLOSED-only DD 119.450000 R; largest winner share 0.085653; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 11 / 1; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 24 | -27.500000 | 0.088398 | 0.080808 | 18 | 4 | 11 |
| 2023-02 | 19 | -9.566667 | 0.217984 | 0.214286 | 18 | 1 | 11 |
| 2023-03 | 13 | -12.066667 | 0.020298 | 0.023810 | 22 | 5 | 12 |
| 2023-04 | 16 | -1.750000 | 0.807339 | 0.758621 | 18 | 1 | 8 |
| 2023-05 | 12 | -5.116667 | 0.508013 | 0.562500 | 21 | 3 | 14 |
| 2023-06 | 15 | -10.083333 | 0.266667 | 0.250000 | 20 | 3 | 15 |
| 2023-07 | 25 | -25.250000 | 0.103550 | 0.109890 | 19 | 5 | 11 |
| 2023-08 | 29 | -19.150000 | 0.317696 | 0.326733 | 14 | 1 | 4 |
| 2023-09 | 19 | -5.666667 | 0.479326 | 0.513514 | 14 | 3 | 8 |
| 2023-10 | 1 | -1.500000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-11 | 2 | -1.800000 | 0.000000 | 0.000000 | 6 | 0 | 0 |
| 2023-12 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N8_W2_T2_SB1_TP9

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 175, entry dates 101, entry months 11; SKIP 26, EXCLUDED 94, exclusion share 0.349442; conditional FLAT CLOSED 167.
Net -119.450000 R; PF R / price 0.245738 / 0.252652; expectancy -0.682571 R; win rate 0.205714; average winner / loser 1.081019 / -1.237240 R.
Conditional CLOSED-only DD 119.450000 R; largest winner share 0.085653; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 11 / 1; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 24 | -27.500000 | 0.088398 | 0.080808 | 18 | 4 | 11 |
| 2023-02 | 19 | -9.566667 | 0.217984 | 0.214286 | 18 | 1 | 11 |
| 2023-03 | 13 | -12.066667 | 0.020298 | 0.023810 | 22 | 5 | 12 |
| 2023-04 | 16 | -1.750000 | 0.807339 | 0.758621 | 18 | 1 | 8 |
| 2023-05 | 12 | -5.116667 | 0.508013 | 0.562500 | 21 | 3 | 14 |
| 2023-06 | 15 | -10.083333 | 0.266667 | 0.250000 | 20 | 3 | 15 |
| 2023-07 | 25 | -25.250000 | 0.103550 | 0.109890 | 19 | 5 | 11 |
| 2023-08 | 29 | -19.150000 | 0.317696 | 0.326733 | 14 | 1 | 4 |
| 2023-09 | 19 | -5.666667 | 0.479326 | 0.513514 | 14 | 3 | 8 |
| 2023-10 | 1 | -1.500000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-11 | 2 | -1.800000 | 0.000000 | 0.000000 | 6 | 0 | 0 |
| 2023-12 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N8_W2_T2_SB1_TP10

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 175, entry dates 101, entry months 11; SKIP 26, EXCLUDED 94, exclusion share 0.349442; conditional FLAT CLOSED 167.
Net -119.450000 R; PF R / price 0.245738 / 0.252652; expectancy -0.682571 R; win rate 0.205714; average winner / loser 1.081019 / -1.237240 R.
Conditional CLOSED-only DD 119.450000 R; largest winner share 0.085653; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 11 / 1; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 24 | -27.500000 | 0.088398 | 0.080808 | 18 | 4 | 11 |
| 2023-02 | 19 | -9.566667 | 0.217984 | 0.214286 | 18 | 1 | 11 |
| 2023-03 | 13 | -12.066667 | 0.020298 | 0.023810 | 22 | 5 | 12 |
| 2023-04 | 16 | -1.750000 | 0.807339 | 0.758621 | 18 | 1 | 8 |
| 2023-05 | 12 | -5.116667 | 0.508013 | 0.562500 | 21 | 3 | 14 |
| 2023-06 | 15 | -10.083333 | 0.266667 | 0.250000 | 20 | 3 | 15 |
| 2023-07 | 25 | -25.250000 | 0.103550 | 0.109890 | 19 | 5 | 11 |
| 2023-08 | 29 | -19.150000 | 0.317696 | 0.326733 | 14 | 1 | 4 |
| 2023-09 | 19 | -5.666667 | 0.479326 | 0.513514 | 14 | 3 | 8 |
| 2023-10 | 1 | -1.500000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-11 | 2 | -1.800000 | 0.000000 | 0.000000 | 6 | 0 | 0 |
| 2023-12 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N8_W2_T3_SB1_TP2

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 149, entry dates 97, entry months 10; SKIP 28, EXCLUDED 73, exclusion share 0.328829; conditional FLAT CLOSED 140.
Net -99.283333 R; PF R / price 0.263841 / 0.277214; expectancy -0.666331 R; win rate 0.201342; average winner / loser 1.186111 / -1.193510 R.
Conditional CLOSED-only DD 99.283333 R; largest winner share 0.093677; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 10 / 2; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 25 | -21.833333 | 0.176101 | 0.159091 | 18 | 3 | 8 |
| 2023-02 | 13 | -4.250000 | 0.354430 | 0.333333 | 18 | 5 | 9 |
| 2023-03 | 9 | -10.150000 | 0.000000 | 0.000000 | 22 | 6 | 7 |
| 2023-04 | 14 | -3.083333 | 0.683761 | 0.645161 | 18 | 3 | 7 |
| 2023-05 | 11 | -7.950000 | 0.196970 | 0.258065 | 21 | 1 | 10 |
| 2023-06 | 10 | -5.666667 | 0.370370 | 0.357143 | 20 | 3 | 14 |
| 2023-07 | 16 | -18.500000 | 0.051282 | 0.048387 | 19 | 2 | 10 |
| 2023-08 | 29 | -16.866667 | 0.381796 | 0.431579 | 14 | 2 | 2 |
| 2023-09 | 21 | -9.583333 | 0.352477 | 0.380000 | 14 | 3 | 6 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 2 | 0 | 0 |
| 2023-11 | 1 | -1.400000 | 0.000000 | 0.000000 | 6 | 0 | 0 |
| 2023-12 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N8_W2_T3_SB1_TP3

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 149, entry dates 97, entry months 10; SKIP 28, EXCLUDED 73, exclusion share 0.328829; conditional FLAT CLOSED 140.
Net -97.950000 R; PF R / price 0.273727 / 0.286229; expectancy -0.657383 R; win rate 0.201342; average winner / loser 1.230556 / -1.193510 R.
Conditional CLOSED-only DD 97.950000 R; largest winner share 0.135440; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 10 / 2; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 25 | -20.166667 | 0.238994 | 0.215909 | 18 | 3 | 8 |
| 2023-02 | 13 | -4.250000 | 0.354430 | 0.333333 | 18 | 5 | 9 |
| 2023-03 | 9 | -10.150000 | 0.000000 | 0.000000 | 22 | 6 | 7 |
| 2023-04 | 14 | -3.416667 | 0.649573 | 0.612903 | 18 | 3 | 7 |
| 2023-05 | 11 | -7.950000 | 0.196970 | 0.258065 | 21 | 1 | 10 |
| 2023-06 | 10 | -5.666667 | 0.370370 | 0.357143 | 20 | 3 | 14 |
| 2023-07 | 16 | -18.500000 | 0.051282 | 0.048387 | 19 | 2 | 10 |
| 2023-08 | 29 | -16.866667 | 0.381796 | 0.431579 | 14 | 2 | 2 |
| 2023-09 | 21 | -9.583333 | 0.352477 | 0.380000 | 14 | 3 | 6 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 2 | 0 | 0 |
| 2023-11 | 1 | -1.400000 | 0.000000 | 0.000000 | 6 | 0 | 0 |
| 2023-12 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N8_W2_T3_SB1_TP4

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 149, entry dates 97, entry months 10; SKIP 28, EXCLUDED 73, exclusion share 0.328829; conditional FLAT CLOSED 140.
Net -96.283333 R; PF R / price 0.286085 / 0.297498; expectancy -0.646197 R; win rate 0.201342; average winner / loser 1.286111 / -1.193510 R.
Conditional CLOSED-only DD 96.283333 R; largest winner share 0.172786; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 10 / 2; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 25 | -18.500000 | 0.301887 | 0.272727 | 18 | 3 | 8 |
| 2023-02 | 13 | -4.250000 | 0.354430 | 0.333333 | 18 | 5 | 9 |
| 2023-03 | 9 | -10.150000 | 0.000000 | 0.000000 | 22 | 6 | 7 |
| 2023-04 | 14 | -3.416667 | 0.649573 | 0.612903 | 18 | 3 | 7 |
| 2023-05 | 11 | -7.950000 | 0.196970 | 0.258065 | 21 | 1 | 10 |
| 2023-06 | 10 | -5.666667 | 0.370370 | 0.357143 | 20 | 3 | 14 |
| 2023-07 | 16 | -18.500000 | 0.051282 | 0.048387 | 19 | 2 | 10 |
| 2023-08 | 29 | -16.866667 | 0.381796 | 0.431579 | 14 | 2 | 2 |
| 2023-09 | 21 | -9.583333 | 0.352477 | 0.380000 | 14 | 3 | 6 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 2 | 0 | 0 |
| 2023-11 | 1 | -1.400000 | 0.000000 | 0.000000 | 6 | 0 | 0 |
| 2023-12 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N8_W2_T3_SB1_TP5

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 149, entry dates 97, entry months 10; SKIP 28, EXCLUDED 73, exclusion share 0.328829; conditional FLAT CLOSED 140.
Net -100.283333 R; PF R / price 0.256426 / 0.270453; expectancy -0.673043 R; win rate 0.201342; average winner / loser 1.152778 / -1.193510 R.
Conditional CLOSED-only DD 100.283333 R; largest winner share 0.086747; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 10 / 2; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 25 | -22.500000 | 0.150943 | 0.136364 | 18 | 3 | 8 |
| 2023-02 | 13 | -4.250000 | 0.354430 | 0.333333 | 18 | 5 | 9 |
| 2023-03 | 9 | -10.150000 | 0.000000 | 0.000000 | 22 | 6 | 7 |
| 2023-04 | 14 | -3.416667 | 0.649573 | 0.612903 | 18 | 3 | 7 |
| 2023-05 | 11 | -7.950000 | 0.196970 | 0.258065 | 21 | 1 | 10 |
| 2023-06 | 10 | -5.666667 | 0.370370 | 0.357143 | 20 | 3 | 14 |
| 2023-07 | 16 | -18.500000 | 0.051282 | 0.048387 | 19 | 2 | 10 |
| 2023-08 | 29 | -16.866667 | 0.381796 | 0.431579 | 14 | 2 | 2 |
| 2023-09 | 21 | -9.583333 | 0.352477 | 0.380000 | 14 | 3 | 6 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 2 | 0 | 0 |
| 2023-11 | 1 | -1.400000 | 0.000000 | 0.000000 | 6 | 0 | 0 |
| 2023-12 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N8_W2_T3_SB1_TP6

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 149, entry dates 97, entry months 10; SKIP 28, EXCLUDED 73, exclusion share 0.328829; conditional FLAT CLOSED 140.
Net -100.283333 R; PF R / price 0.256426 / 0.270453; expectancy -0.673043 R; win rate 0.201342; average winner / loser 1.152778 / -1.193510 R.
Conditional CLOSED-only DD 100.283333 R; largest winner share 0.086747; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 10 / 2; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 25 | -22.500000 | 0.150943 | 0.136364 | 18 | 3 | 8 |
| 2023-02 | 13 | -4.250000 | 0.354430 | 0.333333 | 18 | 5 | 9 |
| 2023-03 | 9 | -10.150000 | 0.000000 | 0.000000 | 22 | 6 | 7 |
| 2023-04 | 14 | -3.416667 | 0.649573 | 0.612903 | 18 | 3 | 7 |
| 2023-05 | 11 | -7.950000 | 0.196970 | 0.258065 | 21 | 1 | 10 |
| 2023-06 | 10 | -5.666667 | 0.370370 | 0.357143 | 20 | 3 | 14 |
| 2023-07 | 16 | -18.500000 | 0.051282 | 0.048387 | 19 | 2 | 10 |
| 2023-08 | 29 | -16.866667 | 0.381796 | 0.431579 | 14 | 2 | 2 |
| 2023-09 | 21 | -9.583333 | 0.352477 | 0.380000 | 14 | 3 | 6 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 2 | 0 | 0 |
| 2023-11 | 1 | -1.400000 | 0.000000 | 0.000000 | 6 | 0 | 0 |
| 2023-12 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N8_W2_T3_SB1_TP7

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 149, entry dates 97, entry months 10; SKIP 28, EXCLUDED 73, exclusion share 0.328829; conditional FLAT CLOSED 140.
Net -100.283333 R; PF R / price 0.256426 / 0.270453; expectancy -0.673043 R; win rate 0.201342; average winner / loser 1.152778 / -1.193510 R.
Conditional CLOSED-only DD 100.283333 R; largest winner share 0.086747; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 10 / 2; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 25 | -22.500000 | 0.150943 | 0.136364 | 18 | 3 | 8 |
| 2023-02 | 13 | -4.250000 | 0.354430 | 0.333333 | 18 | 5 | 9 |
| 2023-03 | 9 | -10.150000 | 0.000000 | 0.000000 | 22 | 6 | 7 |
| 2023-04 | 14 | -3.416667 | 0.649573 | 0.612903 | 18 | 3 | 7 |
| 2023-05 | 11 | -7.950000 | 0.196970 | 0.258065 | 21 | 1 | 10 |
| 2023-06 | 10 | -5.666667 | 0.370370 | 0.357143 | 20 | 3 | 14 |
| 2023-07 | 16 | -18.500000 | 0.051282 | 0.048387 | 19 | 2 | 10 |
| 2023-08 | 29 | -16.866667 | 0.381796 | 0.431579 | 14 | 2 | 2 |
| 2023-09 | 21 | -9.583333 | 0.352477 | 0.380000 | 14 | 3 | 6 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 2 | 0 | 0 |
| 2023-11 | 1 | -1.400000 | 0.000000 | 0.000000 | 6 | 0 | 0 |
| 2023-12 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N8_W2_T3_SB1_TP8

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 149, entry dates 97, entry months 10; SKIP 28, EXCLUDED 73, exclusion share 0.328829; conditional FLAT CLOSED 140.
Net -100.283333 R; PF R / price 0.256426 / 0.270453; expectancy -0.673043 R; win rate 0.201342; average winner / loser 1.152778 / -1.193510 R.
Conditional CLOSED-only DD 100.283333 R; largest winner share 0.086747; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 10 / 2; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 25 | -22.500000 | 0.150943 | 0.136364 | 18 | 3 | 8 |
| 2023-02 | 13 | -4.250000 | 0.354430 | 0.333333 | 18 | 5 | 9 |
| 2023-03 | 9 | -10.150000 | 0.000000 | 0.000000 | 22 | 6 | 7 |
| 2023-04 | 14 | -3.416667 | 0.649573 | 0.612903 | 18 | 3 | 7 |
| 2023-05 | 11 | -7.950000 | 0.196970 | 0.258065 | 21 | 1 | 10 |
| 2023-06 | 10 | -5.666667 | 0.370370 | 0.357143 | 20 | 3 | 14 |
| 2023-07 | 16 | -18.500000 | 0.051282 | 0.048387 | 19 | 2 | 10 |
| 2023-08 | 29 | -16.866667 | 0.381796 | 0.431579 | 14 | 2 | 2 |
| 2023-09 | 21 | -9.583333 | 0.352477 | 0.380000 | 14 | 3 | 6 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 2 | 0 | 0 |
| 2023-11 | 1 | -1.400000 | 0.000000 | 0.000000 | 6 | 0 | 0 |
| 2023-12 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N8_W2_T3_SB1_TP9

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 149, entry dates 97, entry months 10; SKIP 28, EXCLUDED 73, exclusion share 0.328829; conditional FLAT CLOSED 140.
Net -100.283333 R; PF R / price 0.256426 / 0.270453; expectancy -0.673043 R; win rate 0.201342; average winner / loser 1.152778 / -1.193510 R.
Conditional CLOSED-only DD 100.283333 R; largest winner share 0.086747; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 10 / 2; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 25 | -22.500000 | 0.150943 | 0.136364 | 18 | 3 | 8 |
| 2023-02 | 13 | -4.250000 | 0.354430 | 0.333333 | 18 | 5 | 9 |
| 2023-03 | 9 | -10.150000 | 0.000000 | 0.000000 | 22 | 6 | 7 |
| 2023-04 | 14 | -3.416667 | 0.649573 | 0.612903 | 18 | 3 | 7 |
| 2023-05 | 11 | -7.950000 | 0.196970 | 0.258065 | 21 | 1 | 10 |
| 2023-06 | 10 | -5.666667 | 0.370370 | 0.357143 | 20 | 3 | 14 |
| 2023-07 | 16 | -18.500000 | 0.051282 | 0.048387 | 19 | 2 | 10 |
| 2023-08 | 29 | -16.866667 | 0.381796 | 0.431579 | 14 | 2 | 2 |
| 2023-09 | 21 | -9.583333 | 0.352477 | 0.380000 | 14 | 3 | 6 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 2 | 0 | 0 |
| 2023-11 | 1 | -1.400000 | 0.000000 | 0.000000 | 6 | 0 | 0 |
| 2023-12 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N8_W2_T3_SB1_TP10

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 149, entry dates 97, entry months 10; SKIP 28, EXCLUDED 73, exclusion share 0.328829; conditional FLAT CLOSED 140.
Net -100.283333 R; PF R / price 0.256426 / 0.270453; expectancy -0.673043 R; win rate 0.201342; average winner / loser 1.152778 / -1.193510 R.
Conditional CLOSED-only DD 100.283333 R; largest winner share 0.086747; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 10 / 2; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 25 | -22.500000 | 0.150943 | 0.136364 | 18 | 3 | 8 |
| 2023-02 | 13 | -4.250000 | 0.354430 | 0.333333 | 18 | 5 | 9 |
| 2023-03 | 9 | -10.150000 | 0.000000 | 0.000000 | 22 | 6 | 7 |
| 2023-04 | 14 | -3.416667 | 0.649573 | 0.612903 | 18 | 3 | 7 |
| 2023-05 | 11 | -7.950000 | 0.196970 | 0.258065 | 21 | 1 | 10 |
| 2023-06 | 10 | -5.666667 | 0.370370 | 0.357143 | 20 | 3 | 14 |
| 2023-07 | 16 | -18.500000 | 0.051282 | 0.048387 | 19 | 2 | 10 |
| 2023-08 | 29 | -16.866667 | 0.381796 | 0.431579 | 14 | 2 | 2 |
| 2023-09 | 21 | -9.583333 | 0.352477 | 0.380000 | 14 | 3 | 6 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 2 | 0 | 0 |
| 2023-11 | 1 | -1.400000 | 0.000000 | 0.000000 | 6 | 0 | 0 |
| 2023-12 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N8_W3_T2_SB1_TP2

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 202, entry dates 116, entry months 12; SKIP 21, EXCLUDED 96, exclusion share 0.322148; conditional FLAT CLOSED 193.
Net -128.000000 R; PF R / price 0.273896 / 0.263248; expectancy -0.633663 R; win rate 0.217822; average winner / loser 1.097348 / -1.207420 R.
Conditional CLOSED-only DD 128.000000 R; largest winner share 0.069037; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 22 | -21.983333 | 0.014937 | 0.012658 | 18 | 3 | 11 |
| 2023-02 | 17 | -11.933333 | 0.097100 | 0.116279 | 18 | 2 | 13 |
| 2023-03 | 11 | -10.250000 | 0.082090 | 0.085714 | 22 | 2 | 12 |
| 2023-04 | 20 | -3.633333 | 0.709333 | 0.804878 | 18 | 2 | 9 |
| 2023-05 | 16 | -8.066667 | 0.358090 | 0.413043 | 21 | 3 | 10 |
| 2023-06 | 17 | -8.433333 | 0.317139 | 0.341463 | 20 | 5 | 12 |
| 2023-07 | 29 | -29.316667 | 0.080982 | 0.081818 | 19 | 2 | 14 |
| 2023-08 | 38 | -24.033333 | 0.344843 | 0.355556 | 14 | 0 | 7 |
| 2023-09 | 21 | -3.816667 | 0.660741 | 0.400000 | 14 | 2 | 7 |
| 2023-10 | 2 | -3.000000 | 0.000000 | 0.000000 | 2 | 0 | 1 |
| 2023-11 | 6 | 0.933333 | 1.191781 | 1.238095 | 6 | 0 | 0 |
| 2023-12 | 3 | -4.466667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N8_W3_T2_SB1_TP3

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 200, entry dates 116, entry months 12; SKIP 21, EXCLUDED 96, exclusion share 0.324324; conditional FLAT CLOSED 191.
Net -121.116667 R; PF R / price 0.306385 / 0.292433; expectancy -0.605583 R; win rate 0.215000; average winner / loser 1.244186 / -1.204253 R.
Conditional CLOSED-only DD 121.116667 R; largest winner share 0.093458; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 22 | -21.983333 | 0.014937 | 0.012658 | 18 | 3 | 11 |
| 2023-02 | 17 | -11.933333 | 0.097100 | 0.116279 | 18 | 2 | 13 |
| 2023-03 | 11 | -10.250000 | 0.082090 | 0.085714 | 22 | 2 | 12 |
| 2023-04 | 20 | -2.383333 | 0.809333 | 0.926829 | 18 | 2 | 9 |
| 2023-05 | 16 | -8.066667 | 0.358090 | 0.413043 | 21 | 3 | 10 |
| 2023-06 | 17 | -8.433333 | 0.317139 | 0.341463 | 20 | 5 | 12 |
| 2023-07 | 29 | -29.316667 | 0.080982 | 0.081818 | 19 | 2 | 14 |
| 2023-08 | 36 | -19.700000 | 0.437411 | 0.446154 | 14 | 0 | 7 |
| 2023-09 | 21 | -2.416667 | 0.785185 | 0.415217 | 14 | 2 | 7 |
| 2023-10 | 2 | -3.000000 | 0.000000 | 0.000000 | 2 | 0 | 1 |
| 2023-11 | 6 | 0.833333 | 1.171233 | 1.142857 | 6 | 0 | 0 |
| 2023-12 | 3 | -4.466667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N8_W3_T2_SB1_TP4

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 200, entry dates 116, entry months 12; SKIP 21, EXCLUDED 96, exclusion share 0.324324; conditional FLAT CLOSED 191.
Net -115.900000 R; PF R / price 0.336260 / 0.310309; expectancy -0.579500 R; win rate 0.215000; average winner / loser 1.365504 / -1.204253 R.
Conditional CLOSED-only DD 116.616667 R; largest winner share 0.113540; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 22 | -21.983333 | 0.014937 | 0.012658 | 18 | 3 | 11 |
| 2023-02 | 17 | -11.933333 | 0.097100 | 0.116279 | 18 | 2 | 13 |
| 2023-03 | 11 | -10.250000 | 0.082090 | 0.085714 | 22 | 2 | 12 |
| 2023-04 | 20 | -3.133333 | 0.749333 | 0.853659 | 18 | 2 | 9 |
| 2023-05 | 16 | -8.066667 | 0.358090 | 0.413043 | 21 | 3 | 10 |
| 2023-06 | 17 | -8.433333 | 0.317139 | 0.341463 | 20 | 5 | 12 |
| 2023-07 | 29 | -29.316667 | 0.080982 | 0.081818 | 19 | 2 | 14 |
| 2023-08 | 36 | -16.633333 | 0.524988 | 0.538462 | 14 | 0 | 7 |
| 2023-09 | 21 | -1.016667 | 0.909630 | 0.430435 | 14 | 2 | 7 |
| 2023-10 | 2 | -3.000000 | 0.000000 | 0.000000 | 2 | 0 | 1 |
| 2023-11 | 6 | 2.333333 | 1.479452 | 1.428571 | 6 | 0 | 0 |
| 2023-12 | 3 | -4.466667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N8_W3_T2_SB1_TP5

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 200, entry dates 116, entry months 12; SKIP 21, EXCLUDED 96, exclusion share 0.324324; conditional FLAT CLOSED 191.
Net -109.933333 R; PF R / price 0.370430 / 0.333391; expectancy -0.549667 R; win rate 0.215000; average winner / loser 1.504264 / -1.204253 R.
Conditional CLOSED-only DD 113.550000 R; largest winner share 0.128833; largest positive month share 0.909091. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 22 | -21.983333 | 0.014937 | 0.012658 | 18 | 3 | 11 |
| 2023-02 | 17 | -11.933333 | 0.097100 | 0.116279 | 18 | 2 | 13 |
| 2023-03 | 11 | -10.250000 | 0.082090 | 0.085714 | 22 | 2 | 12 |
| 2023-04 | 20 | -3.133333 | 0.749333 | 0.853659 | 18 | 2 | 9 |
| 2023-05 | 16 | -8.066667 | 0.358090 | 0.413043 | 21 | 3 | 10 |
| 2023-06 | 17 | -8.433333 | 0.317139 | 0.341463 | 20 | 5 | 12 |
| 2023-07 | 29 | -29.316667 | 0.080982 | 0.081818 | 19 | 2 | 14 |
| 2023-08 | 36 | -13.566667 | 0.612565 | 0.630769 | 14 | 0 | 7 |
| 2023-09 | 21 | 0.383333 | 1.034074 | 0.445652 | 14 | 2 | 7 |
| 2023-10 | 2 | -3.000000 | 0.000000 | 0.000000 | 2 | 0 | 1 |
| 2023-11 | 6 | 3.833333 | 1.787671 | 1.714286 | 6 | 0 | 0 |
| 2023-12 | 3 | -4.466667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N8_W3_T2_SB1_TP6

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 200, entry dates 116, entry months 12; SKIP 21, EXCLUDED 96, exclusion share 0.324324; conditional FLAT CLOSED 191.
Net -105.633333 R; PF R / price 0.395056 / 0.347796; expectancy -0.528167 R; win rate 0.215000; average winner / loser 1.604264 / -1.204253 R.
Conditional CLOSED-only DD 112.150000 R; largest winner share 0.130466; largest positive month share 0.749415. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 22 | -21.983333 | 0.014937 | 0.012658 | 18 | 3 | 11 |
| 2023-02 | 17 | -11.933333 | 0.097100 | 0.116279 | 18 | 2 | 13 |
| 2023-03 | 11 | -10.250000 | 0.082090 | 0.085714 | 22 | 2 | 12 |
| 2023-04 | 20 | -3.133333 | 0.749333 | 0.853659 | 18 | 2 | 9 |
| 2023-05 | 16 | -8.066667 | 0.358090 | 0.413043 | 21 | 3 | 10 |
| 2023-06 | 17 | -8.433333 | 0.317139 | 0.341463 | 20 | 5 | 12 |
| 2023-07 | 29 | -29.316667 | 0.080982 | 0.081818 | 19 | 2 | 14 |
| 2023-08 | 36 | -12.166667 | 0.652546 | 0.684615 | 14 | 0 | 7 |
| 2023-09 | 21 | 1.783333 | 1.158519 | 0.460870 | 14 | 2 | 7 |
| 2023-10 | 2 | -3.000000 | 0.000000 | 0.000000 | 2 | 0 | 1 |
| 2023-11 | 6 | 5.333333 | 2.095890 | 2.000000 | 6 | 0 | 0 |
| 2023-12 | 3 | -4.466667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N8_W3_T2_SB1_TP7

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 200, entry dates 116, entry months 12; SKIP 21, EXCLUDED 96, exclusion share 0.324324; conditional FLAT CLOSED 191.
Net -103.983333 R; PF R / price 0.404505 / 0.357168; expectancy -0.519917 R; win rate 0.215000; average winner / loser 1.642636 / -1.204253 R.
Conditional CLOSED-only DD 111.150000 R; largest winner share 0.138745; largest positive month share 0.590129. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 22 | -21.983333 | 0.014937 | 0.012658 | 18 | 3 | 11 |
| 2023-02 | 17 | -11.933333 | 0.097100 | 0.116279 | 18 | 2 | 13 |
| 2023-03 | 11 | -10.250000 | 0.082090 | 0.085714 | 22 | 2 | 12 |
| 2023-04 | 20 | -3.133333 | 0.749333 | 0.853659 | 18 | 2 | 9 |
| 2023-05 | 16 | -8.066667 | 0.358090 | 0.413043 | 21 | 3 | 10 |
| 2023-06 | 17 | -8.433333 | 0.317139 | 0.341463 | 20 | 5 | 12 |
| 2023-07 | 29 | -29.316667 | 0.080982 | 0.081818 | 19 | 2 | 14 |
| 2023-08 | 36 | -11.166667 | 0.681104 | 0.723077 | 14 | 0 | 7 |
| 2023-09 | 21 | 3.183333 | 1.282963 | 0.476087 | 14 | 2 | 7 |
| 2023-10 | 2 | -3.000000 | 0.000000 | 0.000000 | 2 | 0 | 1 |
| 2023-11 | 6 | 4.583333 | 1.941781 | 1.857143 | 6 | 0 | 0 |
| 2023-12 | 3 | -4.466667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N8_W3_T2_SB1_TP8

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors.
CLOSED 200, entry dates 116, entry months 12; SKIP 21, EXCLUDED 96, exclusion share 0.324324; conditional FLAT CLOSED 191.
Net -102.583333 R; PF R / price 0.412523 / 0.358383; expectancy -0.512917 R; win rate 0.215000; average winner / loser 1.675194 / -1.204253 R.
Conditional CLOSED-only DD 111.150000 R; largest winner share 0.155484; largest positive month share 0.500000. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 22 | -21.983333 | 0.014937 | 0.012658 | 18 | 3 | 11 |
| 2023-02 | 17 | -11.933333 | 0.097100 | 0.116279 | 18 | 2 | 13 |
| 2023-03 | 11 | -10.250000 | 0.082090 | 0.085714 | 22 | 2 | 12 |
| 2023-04 | 20 | -3.133333 | 0.749333 | 0.853659 | 18 | 2 | 9 |
| 2023-05 | 16 | -8.066667 | 0.358090 | 0.413043 | 21 | 3 | 10 |
| 2023-06 | 17 | -8.433333 | 0.317139 | 0.341463 | 20 | 5 | 12 |
| 2023-07 | 29 | -29.316667 | 0.080982 | 0.081818 | 19 | 2 | 14 |
| 2023-08 | 36 | -11.166667 | 0.681104 | 0.723077 | 14 | 0 | 7 |
| 2023-09 | 21 | 4.583333 | 1.407407 | 0.491304 | 14 | 2 | 7 |
| 2023-10 | 2 | -3.000000 | 0.000000 | 0.000000 | 2 | 0 | 1 |
| 2023-11 | 6 | 4.583333 | 1.941781 | 1.857143 | 6 | 0 | 0 |
| 2023-12 | 3 | -4.466667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N8_W3_T2_SB1_TP9

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 200, entry dates 116, entry months 12; SKIP 21, EXCLUDED 96, exclusion share 0.324324; conditional FLAT CLOSED 191.
Net -101.183333 R; PF R / price 0.420540 / 0.359597; expectancy -0.505917 R; win rate 0.215000; average winner / loser 1.707752 / -1.204253 R.
Conditional CLOSED-only DD 111.150000 R; largest winner share 0.171584; largest positive month share 0.566246. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 22 | -21.983333 | 0.014937 | 0.012658 | 18 | 3 | 11 |
| 2023-02 | 17 | -11.933333 | 0.097100 | 0.116279 | 18 | 2 | 13 |
| 2023-03 | 11 | -10.250000 | 0.082090 | 0.085714 | 22 | 2 | 12 |
| 2023-04 | 20 | -3.133333 | 0.749333 | 0.853659 | 18 | 2 | 9 |
| 2023-05 | 16 | -8.066667 | 0.358090 | 0.413043 | 21 | 3 | 10 |
| 2023-06 | 17 | -8.433333 | 0.317139 | 0.341463 | 20 | 5 | 12 |
| 2023-07 | 29 | -29.316667 | 0.080982 | 0.081818 | 19 | 2 | 14 |
| 2023-08 | 36 | -11.166667 | 0.681104 | 0.723077 | 14 | 0 | 7 |
| 2023-09 | 21 | 5.983333 | 1.531852 | 0.506522 | 14 | 2 | 7 |
| 2023-10 | 2 | -3.000000 | 0.000000 | 0.000000 | 2 | 0 | 1 |
| 2023-11 | 6 | 4.583333 | 1.941781 | 1.857143 | 6 | 0 | 0 |
| 2023-12 | 3 | -4.466667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N8_W3_T2_SB1_TP10

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 200, entry dates 116, entry months 12; SKIP 21, EXCLUDED 96, exclusion share 0.324324; conditional FLAT CLOSED 191.
Net -99.783333 R; PF R / price 0.428558 / 0.360812; expectancy -0.498917 R; win rate 0.215000; average winner / loser 1.740310 / -1.204253 R.
Conditional CLOSED-only DD 111.150000 R; largest winner share 0.187082; largest positive month share 0.616992. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 22 | -21.983333 | 0.014937 | 0.012658 | 18 | 3 | 11 |
| 2023-02 | 17 | -11.933333 | 0.097100 | 0.116279 | 18 | 2 | 13 |
| 2023-03 | 11 | -10.250000 | 0.082090 | 0.085714 | 22 | 2 | 12 |
| 2023-04 | 20 | -3.133333 | 0.749333 | 0.853659 | 18 | 2 | 9 |
| 2023-05 | 16 | -8.066667 | 0.358090 | 0.413043 | 21 | 3 | 10 |
| 2023-06 | 17 | -8.433333 | 0.317139 | 0.341463 | 20 | 5 | 12 |
| 2023-07 | 29 | -29.316667 | 0.080982 | 0.081818 | 19 | 2 | 14 |
| 2023-08 | 36 | -11.166667 | 0.681104 | 0.723077 | 14 | 0 | 7 |
| 2023-09 | 21 | 7.383333 | 1.656296 | 0.521739 | 14 | 2 | 7 |
| 2023-10 | 2 | -3.000000 | 0.000000 | 0.000000 | 2 | 0 | 1 |
| 2023-11 | 6 | 4.583333 | 1.941781 | 1.857143 | 6 | 0 | 0 |
| 2023-12 | 3 | -4.466667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N8_W3_T3_SB1_TP2

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 171, entry dates 109, entry months 12; SKIP 22, EXCLUDED 70, exclusion share 0.290456; conditional FLAT CLOSED 161.
Net -107.783333 R; PF R / price 0.268770 / 0.267945; expectancy -0.630312 R; win rate 0.222222; average winner / loser 1.042544 / -1.218182 R.
Conditional CLOSED-only DD 107.783333 R; largest winner share 0.084140; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 12 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 24 | -22.316667 | 0.014717 | 0.012346 | 18 | 1 | 9 |
| 2023-02 | 14 | -7.016667 | 0.224678 | 0.258065 | 18 | 4 | 9 |
| 2023-03 | 10 | -10.333333 | 0.060606 | 0.060606 | 22 | 3 | 8 |
| 2023-04 | 16 | -5.883333 | 0.513103 | 0.500000 | 18 | 4 | 8 |
| 2023-05 | 16 | -8.183333 | 0.311360 | 0.357143 | 21 | 1 | 5 |
| 2023-06 | 13 | -5.250000 | 0.405660 | 0.448276 | 20 | 3 | 11 |
| 2023-07 | 21 | -19.316667 | 0.104328 | 0.109589 | 19 | 1 | 11 |
| 2023-08 | 30 | -17.166667 | 0.370800 | 0.400000 | 14 | 2 | 3 |
| 2023-09 | 20 | -5.816667 | 0.576970 | 0.463636 | 14 | 3 | 5 |
| 2023-10 | 1 | -1.500000 | 0.000000 | 0.000000 | 2 | 0 | 1 |
| 2023-11 | 5 | -3.333333 | 0.456522 | 0.583333 | 6 | 0 | 0 |
| 2023-12 | 1 | -1.666667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N8_W3_T3_SB1_TP3

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 171, entry dates 109, entry months 12; SKIP 22, EXCLUDED 70, exclusion share 0.290456; conditional FLAT CLOSED 161.
Net -107.650000 R; PF R / price 0.269674 / 0.269862; expectancy -0.629532 R; win rate 0.222222; average winner / loser 1.046053 / -1.218182 R.
Conditional CLOSED-only DD 107.650000 R; largest winner share 0.105660; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 12 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 24 | -22.316667 | 0.014717 | 0.012346 | 18 | 1 | 9 |
| 2023-02 | 14 | -7.016667 | 0.224678 | 0.258065 | 18 | 4 | 9 |
| 2023-03 | 10 | -10.333333 | 0.060606 | 0.060606 | 22 | 3 | 8 |
| 2023-04 | 16 | -5.550000 | 0.540690 | 0.526316 | 18 | 4 | 8 |
| 2023-05 | 16 | -8.183333 | 0.311360 | 0.357143 | 21 | 1 | 5 |
| 2023-06 | 13 | -5.250000 | 0.405660 | 0.448276 | 20 | 3 | 11 |
| 2023-07 | 21 | -19.316667 | 0.104328 | 0.109589 | 19 | 1 | 11 |
| 2023-08 | 30 | -17.166667 | 0.370800 | 0.400000 | 14 | 2 | 3 |
| 2023-09 | 20 | -4.416667 | 0.678788 | 0.479545 | 14 | 3 | 5 |
| 2023-10 | 1 | -1.500000 | 0.000000 | 0.000000 | 2 | 0 | 1 |
| 2023-11 | 5 | -4.933333 | 0.195652 | 0.250000 | 6 | 0 | 0 |
| 2023-12 | 1 | -1.666667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N8_W3_T3_SB1_TP4

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 171, entry dates 109, entry months 12; SKIP 22, EXCLUDED 70, exclusion share 0.290456; conditional FLAT CLOSED 161.
Net -106.250000 R; PF R / price 0.279172 / 0.271353; expectancy -0.621345 R; win rate 0.222222; average winner / loser 1.082895 / -1.218182 R.
Conditional CLOSED-only DD 106.250000 R; largest winner share 0.136087; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 12 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 24 | -22.316667 | 0.014717 | 0.012346 | 18 | 1 | 9 |
| 2023-02 | 14 | -7.016667 | 0.224678 | 0.258065 | 18 | 4 | 9 |
| 2023-03 | 10 | -10.333333 | 0.060606 | 0.060606 | 22 | 3 | 8 |
| 2023-04 | 16 | -5.550000 | 0.540690 | 0.526316 | 18 | 4 | 8 |
| 2023-05 | 16 | -8.183333 | 0.311360 | 0.357143 | 21 | 1 | 5 |
| 2023-06 | 13 | -5.250000 | 0.405660 | 0.448276 | 20 | 3 | 11 |
| 2023-07 | 21 | -19.316667 | 0.104328 | 0.109589 | 19 | 1 | 11 |
| 2023-08 | 30 | -17.166667 | 0.370800 | 0.400000 | 14 | 2 | 3 |
| 2023-09 | 20 | -3.016667 | 0.780606 | 0.495455 | 14 | 3 | 5 |
| 2023-10 | 1 | -1.500000 | 0.000000 | 0.000000 | 2 | 0 | 1 |
| 2023-11 | 5 | -4.933333 | 0.195652 | 0.250000 | 6 | 0 | 0 |
| 2023-12 | 1 | -1.666667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N8_W3_T3_SB1_TP5

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 171, entry dates 109, entry months 12; SKIP 22, EXCLUDED 70, exclusion share 0.290456; conditional FLAT CLOSED 161.
Net -104.850000 R; PF R / price 0.288670 / 0.272843; expectancy -0.613158 R; win rate 0.222222; average winner / loser 1.119737 / -1.218182 R.
Conditional CLOSED-only DD 104.850000 R; largest winner share 0.164512; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 12 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 24 | -22.316667 | 0.014717 | 0.012346 | 18 | 1 | 9 |
| 2023-02 | 14 | -7.016667 | 0.224678 | 0.258065 | 18 | 4 | 9 |
| 2023-03 | 10 | -10.333333 | 0.060606 | 0.060606 | 22 | 3 | 8 |
| 2023-04 | 16 | -5.550000 | 0.540690 | 0.526316 | 18 | 4 | 8 |
| 2023-05 | 16 | -8.183333 | 0.311360 | 0.357143 | 21 | 1 | 5 |
| 2023-06 | 13 | -5.250000 | 0.405660 | 0.448276 | 20 | 3 | 11 |
| 2023-07 | 21 | -19.316667 | 0.104328 | 0.109589 | 19 | 1 | 11 |
| 2023-08 | 30 | -17.166667 | 0.370800 | 0.400000 | 14 | 2 | 3 |
| 2023-09 | 20 | -1.616667 | 0.882424 | 0.511364 | 14 | 3 | 5 |
| 2023-10 | 1 | -1.500000 | 0.000000 | 0.000000 | 2 | 0 | 1 |
| 2023-11 | 5 | -4.933333 | 0.195652 | 0.250000 | 6 | 0 | 0 |
| 2023-12 | 1 | -1.666667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N8_W3_T3_SB1_TP6

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 171, entry dates 109, entry months 12; SKIP 22, EXCLUDED 70, exclusion share 0.290456; conditional FLAT CLOSED 161.
Net -103.450000 R; PF R / price 0.298168 / 0.274334; expectancy -0.604971 R; win rate 0.222222; average winner / loser 1.156579 / -1.218182 R.
Conditional CLOSED-only DD 104.000000 R; largest winner share 0.191126; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 12 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 24 | -22.316667 | 0.014717 | 0.012346 | 18 | 1 | 9 |
| 2023-02 | 14 | -7.016667 | 0.224678 | 0.258065 | 18 | 4 | 9 |
| 2023-03 | 10 | -10.333333 | 0.060606 | 0.060606 | 22 | 3 | 8 |
| 2023-04 | 16 | -5.550000 | 0.540690 | 0.526316 | 18 | 4 | 8 |
| 2023-05 | 16 | -8.183333 | 0.311360 | 0.357143 | 21 | 1 | 5 |
| 2023-06 | 13 | -5.250000 | 0.405660 | 0.448276 | 20 | 3 | 11 |
| 2023-07 | 21 | -19.316667 | 0.104328 | 0.109589 | 19 | 1 | 11 |
| 2023-08 | 30 | -17.166667 | 0.370800 | 0.400000 | 14 | 2 | 3 |
| 2023-09 | 20 | -0.216667 | 0.984242 | 0.527273 | 14 | 3 | 5 |
| 2023-10 | 1 | -1.500000 | 0.000000 | 0.000000 | 2 | 0 | 1 |
| 2023-11 | 5 | -4.933333 | 0.195652 | 0.250000 | 6 | 0 | 0 |
| 2023-12 | 1 | -1.666667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N8_W3_T3_SB1_TP7

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 171, entry dates 109, entry months 12; SKIP 22, EXCLUDED 70, exclusion share 0.290456; conditional FLAT CLOSED 161.
Net -102.050000 R; PF R / price 0.307666 / 0.275825; expectancy -0.596784 R; win rate 0.222222; average winner / loser 1.193421 / -1.218182 R.
Conditional CLOSED-only DD 104.000000 R; largest winner share 0.216097; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 24 | -22.316667 | 0.014717 | 0.012346 | 18 | 1 | 9 |
| 2023-02 | 14 | -7.016667 | 0.224678 | 0.258065 | 18 | 4 | 9 |
| 2023-03 | 10 | -10.333333 | 0.060606 | 0.060606 | 22 | 3 | 8 |
| 2023-04 | 16 | -5.550000 | 0.540690 | 0.526316 | 18 | 4 | 8 |
| 2023-05 | 16 | -8.183333 | 0.311360 | 0.357143 | 21 | 1 | 5 |
| 2023-06 | 13 | -5.250000 | 0.405660 | 0.448276 | 20 | 3 | 11 |
| 2023-07 | 21 | -19.316667 | 0.104328 | 0.109589 | 19 | 1 | 11 |
| 2023-08 | 30 | -17.166667 | 0.370800 | 0.400000 | 14 | 2 | 3 |
| 2023-09 | 20 | 1.183333 | 1.086061 | 0.543182 | 14 | 3 | 5 |
| 2023-10 | 1 | -1.500000 | 0.000000 | 0.000000 | 2 | 0 | 1 |
| 2023-11 | 5 | -4.933333 | 0.195652 | 0.250000 | 6 | 0 | 0 |
| 2023-12 | 1 | -1.666667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N8_W3_T3_SB1_TP8

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 171, entry dates 109, entry months 12; SKIP 22, EXCLUDED 70, exclusion share 0.290456; conditional FLAT CLOSED 161.
Net -100.650000 R; PF R / price 0.317164 / 0.277316; expectancy -0.588596 R; win rate 0.222222; average winner / loser 1.230263 / -1.218182 R.
Conditional CLOSED-only DD 104.000000 R; largest winner share 0.239572; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 24 | -22.316667 | 0.014717 | 0.012346 | 18 | 1 | 9 |
| 2023-02 | 14 | -7.016667 | 0.224678 | 0.258065 | 18 | 4 | 9 |
| 2023-03 | 10 | -10.333333 | 0.060606 | 0.060606 | 22 | 3 | 8 |
| 2023-04 | 16 | -5.550000 | 0.540690 | 0.526316 | 18 | 4 | 8 |
| 2023-05 | 16 | -8.183333 | 0.311360 | 0.357143 | 21 | 1 | 5 |
| 2023-06 | 13 | -5.250000 | 0.405660 | 0.448276 | 20 | 3 | 11 |
| 2023-07 | 21 | -19.316667 | 0.104328 | 0.109589 | 19 | 1 | 11 |
| 2023-08 | 30 | -17.166667 | 0.370800 | 0.400000 | 14 | 2 | 3 |
| 2023-09 | 20 | 2.583333 | 1.187879 | 0.559091 | 14 | 3 | 5 |
| 2023-10 | 1 | -1.500000 | 0.000000 | 0.000000 | 2 | 0 | 1 |
| 2023-11 | 5 | -4.933333 | 0.195652 | 0.250000 | 6 | 0 | 0 |
| 2023-12 | 1 | -1.666667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N8_W3_T3_SB1_TP9

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors.
CLOSED 171, entry dates 109, entry months 12; SKIP 22, EXCLUDED 70, exclusion share 0.290456; conditional FLAT CLOSED 161.
Net -99.250000 R; PF R / price 0.326662 / 0.278807; expectancy -0.580409 R; win rate 0.222222; average winner / loser 1.267105 / -1.218182 R.
Conditional CLOSED-only DD 104.000000 R; largest winner share 0.261682; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 24 | -22.316667 | 0.014717 | 0.012346 | 18 | 1 | 9 |
| 2023-02 | 14 | -7.016667 | 0.224678 | 0.258065 | 18 | 4 | 9 |
| 2023-03 | 10 | -10.333333 | 0.060606 | 0.060606 | 22 | 3 | 8 |
| 2023-04 | 16 | -5.550000 | 0.540690 | 0.526316 | 18 | 4 | 8 |
| 2023-05 | 16 | -8.183333 | 0.311360 | 0.357143 | 21 | 1 | 5 |
| 2023-06 | 13 | -5.250000 | 0.405660 | 0.448276 | 20 | 3 | 11 |
| 2023-07 | 21 | -19.316667 | 0.104328 | 0.109589 | 19 | 1 | 11 |
| 2023-08 | 30 | -17.166667 | 0.370800 | 0.400000 | 14 | 2 | 3 |
| 2023-09 | 20 | 3.983333 | 1.289697 | 0.575000 | 14 | 3 | 5 |
| 2023-10 | 1 | -1.500000 | 0.000000 | 0.000000 | 2 | 0 | 1 |
| 2023-11 | 5 | -4.933333 | 0.195652 | 0.250000 | 6 | 0 | 0 |
| 2023-12 | 1 | -1.666667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N8_W3_T3_SB1_TP10

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors.
CLOSED 171, entry dates 109, entry months 12; SKIP 22, EXCLUDED 70, exclusion share 0.290456; conditional FLAT CLOSED 161.
Net -97.850000 R; PF R / price 0.336160 / 0.280298; expectancy -0.572222 R; win rate 0.222222; average winner / loser 1.303947 / -1.218182 R.
Conditional CLOSED-only DD 104.000000 R; largest winner share 0.282543; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 24 | -22.316667 | 0.014717 | 0.012346 | 18 | 1 | 9 |
| 2023-02 | 14 | -7.016667 | 0.224678 | 0.258065 | 18 | 4 | 9 |
| 2023-03 | 10 | -10.333333 | 0.060606 | 0.060606 | 22 | 3 | 8 |
| 2023-04 | 16 | -5.550000 | 0.540690 | 0.526316 | 18 | 4 | 8 |
| 2023-05 | 16 | -8.183333 | 0.311360 | 0.357143 | 21 | 1 | 5 |
| 2023-06 | 13 | -5.250000 | 0.405660 | 0.448276 | 20 | 3 | 11 |
| 2023-07 | 21 | -19.316667 | 0.104328 | 0.109589 | 19 | 1 | 11 |
| 2023-08 | 30 | -17.166667 | 0.370800 | 0.400000 | 14 | 2 | 3 |
| 2023-09 | 20 | 5.383333 | 1.391515 | 0.590909 | 14 | 3 | 5 |
| 2023-10 | 1 | -1.500000 | 0.000000 | 0.000000 | 2 | 0 | 1 |
| 2023-11 | 5 | -4.933333 | 0.195652 | 0.250000 | 6 | 0 | 0 |
| 2023-12 | 1 | -1.666667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N9_W2_T2_SB1_TP2

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 157, entry dates 96, entry months 11; SKIP 25, EXCLUDED 75, exclusion share 0.323276; conditional FLAT CLOSED 157.
Net -96.166667 R; PF R / price 0.309643 / 0.299179; expectancy -0.612527 R; win rate 0.203822; average winner / loser 1.347917 / -1.170588 R.
Conditional CLOSED-only DD 98.966667 R; largest winner share 0.077280; largest positive month share 1.000000. Positive / negative / zero months 1 / 10 / 1; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 15 | -12.566667 | 0.209644 | 0.178571 | 18 | 4 | 10 |
| 2023-02 | 22 | -10.466667 | 0.317391 | 0.416667 | 18 | 0 | 9 |
| 2023-03 | 11 | -10.583333 | 0.059259 | 0.055556 | 22 | 6 | 6 |
| 2023-04 | 19 | -4.716667 | 0.628609 | 0.674419 | 18 | 4 | 5 |
| 2023-05 | 10 | -9.666667 | 0.256410 | 0.238095 | 21 | 1 | 12 |
| 2023-06 | 16 | -12.083333 | 0.161850 | 0.155556 | 20 | 3 | 14 |
| 2023-07 | 17 | -17.366667 | 0.087566 | 0.071429 | 19 | 4 | 8 |
| 2023-08 | 24 | -6.083333 | 0.686426 | 0.641791 | 14 | 0 | 5 |
| 2023-09 | 21 | -13.933333 | 0.168986 | 0.200000 | 14 | 3 | 6 |
| 2023-10 | 1 | -1.500000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-11 | 1 | 2.800000 | NOT_AVAILABLE | NOT_AVAILABLE | 6 | 0 | 0 |
| 2023-12 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N9_W2_T2_SB1_TP3

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 157, entry dates 96, entry months 11; SKIP 25, EXCLUDED 75, exclusion share 0.323276; conditional FLAT CLOSED 157.
Net -97.433333 R; PF R / price 0.300550 / 0.299611; expectancy -0.620594 R; win rate 0.203822; average winner / loser 1.308333 / -1.170588 R.
Conditional CLOSED-only DD 98.633333 R; largest winner share 0.119427; largest positive month share 1.000000. Positive / negative / zero months 1 / 10 / 1; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 15 | -10.900000 | 0.314465 | 0.267857 | 18 | 4 | 10 |
| 2023-02 | 22 | -10.466667 | 0.317391 | 0.416667 | 18 | 0 | 9 |
| 2023-03 | 11 | -10.583333 | 0.059259 | 0.055556 | 22 | 6 | 6 |
| 2023-04 | 19 | -5.383333 | 0.576115 | 0.627907 | 18 | 4 | 5 |
| 2023-05 | 10 | -9.666667 | 0.256410 | 0.238095 | 21 | 1 | 12 |
| 2023-06 | 16 | -12.083333 | 0.161850 | 0.155556 | 20 | 3 | 14 |
| 2023-07 | 17 | -17.366667 | 0.087566 | 0.071429 | 19 | 4 | 8 |
| 2023-08 | 24 | -6.750000 | 0.652062 | 0.611940 | 14 | 0 | 5 |
| 2023-09 | 21 | -13.933333 | 0.168986 | 0.200000 | 14 | 3 | 6 |
| 2023-10 | 1 | -1.500000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-11 | 1 | 1.200000 | NOT_AVAILABLE | NOT_AVAILABLE | 6 | 0 | 0 |
| 2023-12 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N9_W2_T2_SB1_TP4

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 157, entry dates 96, entry months 11; SKIP 25, EXCLUDED 75, exclusion share 0.323276; conditional FLAT CLOSED 157.
Net -95.766667 R; PF R / price 0.312515 / 0.310419; expectancy -0.609979 R; win rate 0.203822; average winner / loser 1.360417 / -1.170588 R.
Conditional CLOSED-only DD 96.966667 R; largest winner share 0.153139; largest positive month share 1.000000. Positive / negative / zero months 1 / 10 / 1; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 15 | -9.233333 | 0.419287 | 0.357143 | 18 | 4 | 10 |
| 2023-02 | 22 | -10.466667 | 0.317391 | 0.416667 | 18 | 0 | 9 |
| 2023-03 | 11 | -10.583333 | 0.059259 | 0.055556 | 22 | 6 | 6 |
| 2023-04 | 19 | -5.383333 | 0.576115 | 0.627907 | 18 | 4 | 5 |
| 2023-05 | 10 | -9.666667 | 0.256410 | 0.238095 | 21 | 1 | 12 |
| 2023-06 | 16 | -12.083333 | 0.161850 | 0.155556 | 20 | 3 | 14 |
| 2023-07 | 17 | -17.366667 | 0.087566 | 0.071429 | 19 | 4 | 8 |
| 2023-08 | 24 | -6.750000 | 0.652062 | 0.611940 | 14 | 0 | 5 |
| 2023-09 | 21 | -13.933333 | 0.168986 | 0.200000 | 14 | 3 | 6 |
| 2023-10 | 1 | -1.500000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-11 | 1 | 1.200000 | NOT_AVAILABLE | NOT_AVAILABLE | 6 | 0 | 0 |
| 2023-12 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N9_W2_T2_SB1_TP5

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 157, entry dates 96, entry months 11; SKIP 25, EXCLUDED 75, exclusion share 0.323276; conditional FLAT CLOSED 157.
Net -100.100000 R; PF R / price 0.281407 / 0.282317; expectancy -0.637580 R; win rate 0.203822; average winner / loser 1.225000 / -1.170588 R.
Conditional CLOSED-only DD 101.300000 R; largest winner share 0.085034; largest positive month share 1.000000. Positive / negative / zero months 1 / 10 / 1; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 15 | -13.566667 | 0.146751 | 0.125000 | 18 | 4 | 10 |
| 2023-02 | 22 | -10.466667 | 0.317391 | 0.416667 | 18 | 0 | 9 |
| 2023-03 | 11 | -10.583333 | 0.059259 | 0.055556 | 22 | 6 | 6 |
| 2023-04 | 19 | -5.383333 | 0.576115 | 0.627907 | 18 | 4 | 5 |
| 2023-05 | 10 | -9.666667 | 0.256410 | 0.238095 | 21 | 1 | 12 |
| 2023-06 | 16 | -12.083333 | 0.161850 | 0.155556 | 20 | 3 | 14 |
| 2023-07 | 17 | -17.366667 | 0.087566 | 0.071429 | 19 | 4 | 8 |
| 2023-08 | 24 | -6.750000 | 0.652062 | 0.611940 | 14 | 0 | 5 |
| 2023-09 | 21 | -13.933333 | 0.168986 | 0.200000 | 14 | 3 | 6 |
| 2023-10 | 1 | -1.500000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-11 | 1 | 1.200000 | NOT_AVAILABLE | NOT_AVAILABLE | 6 | 0 | 0 |
| 2023-12 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N9_W2_T2_SB1_TP6

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 157, entry dates 96, entry months 11; SKIP 25, EXCLUDED 75, exclusion share 0.323276; conditional FLAT CLOSED 157.
Net -100.100000 R; PF R / price 0.281407 / 0.282317; expectancy -0.637580 R; win rate 0.203822; average winner / loser 1.225000 / -1.170588 R.
Conditional CLOSED-only DD 101.300000 R; largest winner share 0.085034; largest positive month share 1.000000. Positive / negative / zero months 1 / 10 / 1; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 15 | -13.566667 | 0.146751 | 0.125000 | 18 | 4 | 10 |
| 2023-02 | 22 | -10.466667 | 0.317391 | 0.416667 | 18 | 0 | 9 |
| 2023-03 | 11 | -10.583333 | 0.059259 | 0.055556 | 22 | 6 | 6 |
| 2023-04 | 19 | -5.383333 | 0.576115 | 0.627907 | 18 | 4 | 5 |
| 2023-05 | 10 | -9.666667 | 0.256410 | 0.238095 | 21 | 1 | 12 |
| 2023-06 | 16 | -12.083333 | 0.161850 | 0.155556 | 20 | 3 | 14 |
| 2023-07 | 17 | -17.366667 | 0.087566 | 0.071429 | 19 | 4 | 8 |
| 2023-08 | 24 | -6.750000 | 0.652062 | 0.611940 | 14 | 0 | 5 |
| 2023-09 | 21 | -13.933333 | 0.168986 | 0.200000 | 14 | 3 | 6 |
| 2023-10 | 1 | -1.500000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-11 | 1 | 1.200000 | NOT_AVAILABLE | NOT_AVAILABLE | 6 | 0 | 0 |
| 2023-12 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N9_W2_T2_SB1_TP7

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 157, entry dates 96, entry months 11; SKIP 25, EXCLUDED 75, exclusion share 0.323276; conditional FLAT CLOSED 157.
Net -100.100000 R; PF R / price 0.281407 / 0.282317; expectancy -0.637580 R; win rate 0.203822; average winner / loser 1.225000 / -1.170588 R.
Conditional CLOSED-only DD 101.300000 R; largest winner share 0.085034; largest positive month share 1.000000. Positive / negative / zero months 1 / 10 / 1; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 15 | -13.566667 | 0.146751 | 0.125000 | 18 | 4 | 10 |
| 2023-02 | 22 | -10.466667 | 0.317391 | 0.416667 | 18 | 0 | 9 |
| 2023-03 | 11 | -10.583333 | 0.059259 | 0.055556 | 22 | 6 | 6 |
| 2023-04 | 19 | -5.383333 | 0.576115 | 0.627907 | 18 | 4 | 5 |
| 2023-05 | 10 | -9.666667 | 0.256410 | 0.238095 | 21 | 1 | 12 |
| 2023-06 | 16 | -12.083333 | 0.161850 | 0.155556 | 20 | 3 | 14 |
| 2023-07 | 17 | -17.366667 | 0.087566 | 0.071429 | 19 | 4 | 8 |
| 2023-08 | 24 | -6.750000 | 0.652062 | 0.611940 | 14 | 0 | 5 |
| 2023-09 | 21 | -13.933333 | 0.168986 | 0.200000 | 14 | 3 | 6 |
| 2023-10 | 1 | -1.500000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-11 | 1 | 1.200000 | NOT_AVAILABLE | NOT_AVAILABLE | 6 | 0 | 0 |
| 2023-12 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N9_W2_T2_SB1_TP8

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 157, entry dates 96, entry months 11; SKIP 25, EXCLUDED 75, exclusion share 0.323276; conditional FLAT CLOSED 157.
Net -100.100000 R; PF R / price 0.281407 / 0.282317; expectancy -0.637580 R; win rate 0.203822; average winner / loser 1.225000 / -1.170588 R.
Conditional CLOSED-only DD 101.300000 R; largest winner share 0.085034; largest positive month share 1.000000. Positive / negative / zero months 1 / 10 / 1; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 15 | -13.566667 | 0.146751 | 0.125000 | 18 | 4 | 10 |
| 2023-02 | 22 | -10.466667 | 0.317391 | 0.416667 | 18 | 0 | 9 |
| 2023-03 | 11 | -10.583333 | 0.059259 | 0.055556 | 22 | 6 | 6 |
| 2023-04 | 19 | -5.383333 | 0.576115 | 0.627907 | 18 | 4 | 5 |
| 2023-05 | 10 | -9.666667 | 0.256410 | 0.238095 | 21 | 1 | 12 |
| 2023-06 | 16 | -12.083333 | 0.161850 | 0.155556 | 20 | 3 | 14 |
| 2023-07 | 17 | -17.366667 | 0.087566 | 0.071429 | 19 | 4 | 8 |
| 2023-08 | 24 | -6.750000 | 0.652062 | 0.611940 | 14 | 0 | 5 |
| 2023-09 | 21 | -13.933333 | 0.168986 | 0.200000 | 14 | 3 | 6 |
| 2023-10 | 1 | -1.500000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-11 | 1 | 1.200000 | NOT_AVAILABLE | NOT_AVAILABLE | 6 | 0 | 0 |
| 2023-12 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N9_W2_T2_SB1_TP9

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 157, entry dates 96, entry months 11; SKIP 25, EXCLUDED 75, exclusion share 0.323276; conditional FLAT CLOSED 157.
Net -100.100000 R; PF R / price 0.281407 / 0.282317; expectancy -0.637580 R; win rate 0.203822; average winner / loser 1.225000 / -1.170588 R.
Conditional CLOSED-only DD 101.300000 R; largest winner share 0.085034; largest positive month share 1.000000. Positive / negative / zero months 1 / 10 / 1; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 15 | -13.566667 | 0.146751 | 0.125000 | 18 | 4 | 10 |
| 2023-02 | 22 | -10.466667 | 0.317391 | 0.416667 | 18 | 0 | 9 |
| 2023-03 | 11 | -10.583333 | 0.059259 | 0.055556 | 22 | 6 | 6 |
| 2023-04 | 19 | -5.383333 | 0.576115 | 0.627907 | 18 | 4 | 5 |
| 2023-05 | 10 | -9.666667 | 0.256410 | 0.238095 | 21 | 1 | 12 |
| 2023-06 | 16 | -12.083333 | 0.161850 | 0.155556 | 20 | 3 | 14 |
| 2023-07 | 17 | -17.366667 | 0.087566 | 0.071429 | 19 | 4 | 8 |
| 2023-08 | 24 | -6.750000 | 0.652062 | 0.611940 | 14 | 0 | 5 |
| 2023-09 | 21 | -13.933333 | 0.168986 | 0.200000 | 14 | 3 | 6 |
| 2023-10 | 1 | -1.500000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-11 | 1 | 1.200000 | NOT_AVAILABLE | NOT_AVAILABLE | 6 | 0 | 0 |
| 2023-12 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N9_W2_T2_SB1_TP10

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 157, entry dates 96, entry months 11; SKIP 25, EXCLUDED 75, exclusion share 0.323276; conditional FLAT CLOSED 157.
Net -100.100000 R; PF R / price 0.281407 / 0.282317; expectancy -0.637580 R; win rate 0.203822; average winner / loser 1.225000 / -1.170588 R.
Conditional CLOSED-only DD 101.300000 R; largest winner share 0.085034; largest positive month share 1.000000. Positive / negative / zero months 1 / 10 / 1; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 15 | -13.566667 | 0.146751 | 0.125000 | 18 | 4 | 10 |
| 2023-02 | 22 | -10.466667 | 0.317391 | 0.416667 | 18 | 0 | 9 |
| 2023-03 | 11 | -10.583333 | 0.059259 | 0.055556 | 22 | 6 | 6 |
| 2023-04 | 19 | -5.383333 | 0.576115 | 0.627907 | 18 | 4 | 5 |
| 2023-05 | 10 | -9.666667 | 0.256410 | 0.238095 | 21 | 1 | 12 |
| 2023-06 | 16 | -12.083333 | 0.161850 | 0.155556 | 20 | 3 | 14 |
| 2023-07 | 17 | -17.366667 | 0.087566 | 0.071429 | 19 | 4 | 8 |
| 2023-08 | 24 | -6.750000 | 0.652062 | 0.611940 | 14 | 0 | 5 |
| 2023-09 | 21 | -13.933333 | 0.168986 | 0.200000 | 14 | 3 | 6 |
| 2023-10 | 1 | -1.500000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-11 | 1 | 1.200000 | NOT_AVAILABLE | NOT_AVAILABLE | 6 | 0 | 0 |
| 2023-12 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N9_W2_T3_SB1_TP2

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 125, entry dates 90, entry months 10; SKIP 18, EXCLUDED 69, exclusion share 0.355670; conditional FLAT CLOSED 125.
Net -80.016667 R; PF R / price 0.305411 / 0.287533; expectancy -0.640133 R; win rate 0.200000; average winner / loser 1.407333 / -1.212632 R.
Conditional CLOSED-only DD 82.816667 R; largest winner share 0.094742; largest positive month share 1.000000. Positive / negative / zero months 1 / 9 / 2; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 16 | -14.233333 | 0.189753 | 0.163934 | 18 | 1 | 9 |
| 2023-02 | 17 | -6.100000 | 0.409677 | 0.515152 | 18 | 1 | 8 |
| 2023-03 | 9 | -10.166667 | 0.061538 | 0.058824 | 22 | 4 | 6 |
| 2023-04 | 16 | -7.250000 | 0.420000 | 0.380952 | 18 | 2 | 5 |
| 2023-05 | 10 | -14.583333 | 0.000000 | 0.000000 | 21 | 1 | 9 |
| 2023-06 | 9 | -4.333333 | 0.350000 | 0.350000 | 20 | 2 | 13 |
| 2023-07 | 12 | -14.733333 | 0.063559 | 0.056604 | 19 | 4 | 9 |
| 2023-08 | 21 | -2.833333 | 0.824561 | 0.781818 | 14 | 0 | 4 |
| 2023-09 | 14 | -8.583333 | 0.207692 | 0.272727 | 14 | 3 | 6 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 2 | 0 | 0 |
| 2023-11 | 1 | 2.800000 | NOT_AVAILABLE | NOT_AVAILABLE | 6 | 0 | 0 |
| 2023-12 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N9_W2_T3_SB1_TP3

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 125, entry dates 90, entry months 10; SKIP 18, EXCLUDED 69, exclusion share 0.355670; conditional FLAT CLOSED 125.
Net -81.283333 R; PF R / price 0.294416 / 0.288064; expectancy -0.650267 R; win rate 0.200000; average winner / loser 1.356667 / -1.212632 R.
Conditional CLOSED-only DD 82.483333 R; largest winner share 0.147420; largest positive month share 1.000000. Positive / negative / zero months 1 / 9 / 2; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 16 | -12.566667 | 0.284630 | 0.245902 | 18 | 1 | 9 |
| 2023-02 | 17 | -6.100000 | 0.409677 | 0.515152 | 18 | 1 | 8 |
| 2023-03 | 9 | -10.166667 | 0.061538 | 0.058824 | 22 | 4 | 6 |
| 2023-04 | 16 | -7.916667 | 0.366667 | 0.333333 | 18 | 2 | 5 |
| 2023-05 | 10 | -14.583333 | 0.000000 | 0.000000 | 21 | 1 | 9 |
| 2023-06 | 9 | -4.333333 | 0.350000 | 0.350000 | 20 | 2 | 13 |
| 2023-07 | 12 | -14.733333 | 0.063559 | 0.056604 | 19 | 4 | 9 |
| 2023-08 | 21 | -3.500000 | 0.783282 | 0.745455 | 14 | 0 | 4 |
| 2023-09 | 14 | -8.583333 | 0.207692 | 0.272727 | 14 | 3 | 6 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 2 | 0 | 0 |
| 2023-11 | 1 | 1.200000 | NOT_AVAILABLE | NOT_AVAILABLE | 6 | 0 | 0 |
| 2023-12 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N9_W2_T3_SB1_TP4

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 125, entry dates 90, entry months 10; SKIP 18, EXCLUDED 69, exclusion share 0.355670; conditional FLAT CLOSED 125.
Net -79.616667 R; PF R / price 0.308883 / 0.301326; expectancy -0.636933 R; win rate 0.200000; average winner / loser 1.423333 / -1.212632 R.
Conditional CLOSED-only DD 80.816667 R; largest winner share 0.187354; largest positive month share 1.000000. Positive / negative / zero months 1 / 9 / 2; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 16 | -10.900000 | 0.379507 | 0.327869 | 18 | 1 | 9 |
| 2023-02 | 17 | -6.100000 | 0.409677 | 0.515152 | 18 | 1 | 8 |
| 2023-03 | 9 | -10.166667 | 0.061538 | 0.058824 | 22 | 4 | 6 |
| 2023-04 | 16 | -7.916667 | 0.366667 | 0.333333 | 18 | 2 | 5 |
| 2023-05 | 10 | -14.583333 | 0.000000 | 0.000000 | 21 | 1 | 9 |
| 2023-06 | 9 | -4.333333 | 0.350000 | 0.350000 | 20 | 2 | 13 |
| 2023-07 | 12 | -14.733333 | 0.063559 | 0.056604 | 19 | 4 | 9 |
| 2023-08 | 21 | -3.500000 | 0.783282 | 0.745455 | 14 | 0 | 4 |
| 2023-09 | 14 | -8.583333 | 0.207692 | 0.272727 | 14 | 3 | 6 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 2 | 0 | 0 |
| 2023-11 | 1 | 1.200000 | NOT_AVAILABLE | NOT_AVAILABLE | 6 | 0 | 0 |
| 2023-12 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N9_W2_T3_SB1_TP5

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 125, entry dates 90, entry months 10; SKIP 18, EXCLUDED 69, exclusion share 0.355670; conditional FLAT CLOSED 125.
Net -83.950000 R; PF R / price 0.271267 / 0.266844; expectancy -0.671600 R; win rate 0.200000; average winner / loser 1.250000 / -1.212632 R.
Conditional CLOSED-only DD 85.150000 R; largest winner share 0.106667; largest positive month share 1.000000. Positive / negative / zero months 1 / 9 / 2; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 16 | -15.233333 | 0.132827 | 0.114754 | 18 | 1 | 9 |
| 2023-02 | 17 | -6.100000 | 0.409677 | 0.515152 | 18 | 1 | 8 |
| 2023-03 | 9 | -10.166667 | 0.061538 | 0.058824 | 22 | 4 | 6 |
| 2023-04 | 16 | -7.916667 | 0.366667 | 0.333333 | 18 | 2 | 5 |
| 2023-05 | 10 | -14.583333 | 0.000000 | 0.000000 | 21 | 1 | 9 |
| 2023-06 | 9 | -4.333333 | 0.350000 | 0.350000 | 20 | 2 | 13 |
| 2023-07 | 12 | -14.733333 | 0.063559 | 0.056604 | 19 | 4 | 9 |
| 2023-08 | 21 | -3.500000 | 0.783282 | 0.745455 | 14 | 0 | 4 |
| 2023-09 | 14 | -8.583333 | 0.207692 | 0.272727 | 14 | 3 | 6 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 2 | 0 | 0 |
| 2023-11 | 1 | 1.200000 | NOT_AVAILABLE | NOT_AVAILABLE | 6 | 0 | 0 |
| 2023-12 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N9_W2_T3_SB1_TP6

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 125, entry dates 90, entry months 10; SKIP 18, EXCLUDED 69, exclusion share 0.355670; conditional FLAT CLOSED 125.
Net -83.950000 R; PF R / price 0.271267 / 0.266844; expectancy -0.671600 R; win rate 0.200000; average winner / loser 1.250000 / -1.212632 R.
Conditional CLOSED-only DD 85.150000 R; largest winner share 0.106667; largest positive month share 1.000000. Positive / negative / zero months 1 / 9 / 2; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 16 | -15.233333 | 0.132827 | 0.114754 | 18 | 1 | 9 |
| 2023-02 | 17 | -6.100000 | 0.409677 | 0.515152 | 18 | 1 | 8 |
| 2023-03 | 9 | -10.166667 | 0.061538 | 0.058824 | 22 | 4 | 6 |
| 2023-04 | 16 | -7.916667 | 0.366667 | 0.333333 | 18 | 2 | 5 |
| 2023-05 | 10 | -14.583333 | 0.000000 | 0.000000 | 21 | 1 | 9 |
| 2023-06 | 9 | -4.333333 | 0.350000 | 0.350000 | 20 | 2 | 13 |
| 2023-07 | 12 | -14.733333 | 0.063559 | 0.056604 | 19 | 4 | 9 |
| 2023-08 | 21 | -3.500000 | 0.783282 | 0.745455 | 14 | 0 | 4 |
| 2023-09 | 14 | -8.583333 | 0.207692 | 0.272727 | 14 | 3 | 6 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 2 | 0 | 0 |
| 2023-11 | 1 | 1.200000 | NOT_AVAILABLE | NOT_AVAILABLE | 6 | 0 | 0 |
| 2023-12 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N9_W2_T3_SB1_TP7

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 125, entry dates 90, entry months 10; SKIP 18, EXCLUDED 69, exclusion share 0.355670; conditional FLAT CLOSED 125.
Net -83.950000 R; PF R / price 0.271267 / 0.266844; expectancy -0.671600 R; win rate 0.200000; average winner / loser 1.250000 / -1.212632 R.
Conditional CLOSED-only DD 85.150000 R; largest winner share 0.106667; largest positive month share 1.000000. Positive / negative / zero months 1 / 9 / 2; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 16 | -15.233333 | 0.132827 | 0.114754 | 18 | 1 | 9 |
| 2023-02 | 17 | -6.100000 | 0.409677 | 0.515152 | 18 | 1 | 8 |
| 2023-03 | 9 | -10.166667 | 0.061538 | 0.058824 | 22 | 4 | 6 |
| 2023-04 | 16 | -7.916667 | 0.366667 | 0.333333 | 18 | 2 | 5 |
| 2023-05 | 10 | -14.583333 | 0.000000 | 0.000000 | 21 | 1 | 9 |
| 2023-06 | 9 | -4.333333 | 0.350000 | 0.350000 | 20 | 2 | 13 |
| 2023-07 | 12 | -14.733333 | 0.063559 | 0.056604 | 19 | 4 | 9 |
| 2023-08 | 21 | -3.500000 | 0.783282 | 0.745455 | 14 | 0 | 4 |
| 2023-09 | 14 | -8.583333 | 0.207692 | 0.272727 | 14 | 3 | 6 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 2 | 0 | 0 |
| 2023-11 | 1 | 1.200000 | NOT_AVAILABLE | NOT_AVAILABLE | 6 | 0 | 0 |
| 2023-12 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N9_W2_T3_SB1_TP8

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 125, entry dates 90, entry months 10; SKIP 18, EXCLUDED 69, exclusion share 0.355670; conditional FLAT CLOSED 125.
Net -83.950000 R; PF R / price 0.271267 / 0.266844; expectancy -0.671600 R; win rate 0.200000; average winner / loser 1.250000 / -1.212632 R.
Conditional CLOSED-only DD 85.150000 R; largest winner share 0.106667; largest positive month share 1.000000. Positive / negative / zero months 1 / 9 / 2; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 16 | -15.233333 | 0.132827 | 0.114754 | 18 | 1 | 9 |
| 2023-02 | 17 | -6.100000 | 0.409677 | 0.515152 | 18 | 1 | 8 |
| 2023-03 | 9 | -10.166667 | 0.061538 | 0.058824 | 22 | 4 | 6 |
| 2023-04 | 16 | -7.916667 | 0.366667 | 0.333333 | 18 | 2 | 5 |
| 2023-05 | 10 | -14.583333 | 0.000000 | 0.000000 | 21 | 1 | 9 |
| 2023-06 | 9 | -4.333333 | 0.350000 | 0.350000 | 20 | 2 | 13 |
| 2023-07 | 12 | -14.733333 | 0.063559 | 0.056604 | 19 | 4 | 9 |
| 2023-08 | 21 | -3.500000 | 0.783282 | 0.745455 | 14 | 0 | 4 |
| 2023-09 | 14 | -8.583333 | 0.207692 | 0.272727 | 14 | 3 | 6 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 2 | 0 | 0 |
| 2023-11 | 1 | 1.200000 | NOT_AVAILABLE | NOT_AVAILABLE | 6 | 0 | 0 |
| 2023-12 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N9_W2_T3_SB1_TP9

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 125, entry dates 90, entry months 10; SKIP 18, EXCLUDED 69, exclusion share 0.355670; conditional FLAT CLOSED 125.
Net -83.950000 R; PF R / price 0.271267 / 0.266844; expectancy -0.671600 R; win rate 0.200000; average winner / loser 1.250000 / -1.212632 R.
Conditional CLOSED-only DD 85.150000 R; largest winner share 0.106667; largest positive month share 1.000000. Positive / negative / zero months 1 / 9 / 2; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 16 | -15.233333 | 0.132827 | 0.114754 | 18 | 1 | 9 |
| 2023-02 | 17 | -6.100000 | 0.409677 | 0.515152 | 18 | 1 | 8 |
| 2023-03 | 9 | -10.166667 | 0.061538 | 0.058824 | 22 | 4 | 6 |
| 2023-04 | 16 | -7.916667 | 0.366667 | 0.333333 | 18 | 2 | 5 |
| 2023-05 | 10 | -14.583333 | 0.000000 | 0.000000 | 21 | 1 | 9 |
| 2023-06 | 9 | -4.333333 | 0.350000 | 0.350000 | 20 | 2 | 13 |
| 2023-07 | 12 | -14.733333 | 0.063559 | 0.056604 | 19 | 4 | 9 |
| 2023-08 | 21 | -3.500000 | 0.783282 | 0.745455 | 14 | 0 | 4 |
| 2023-09 | 14 | -8.583333 | 0.207692 | 0.272727 | 14 | 3 | 6 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 2 | 0 | 0 |
| 2023-11 | 1 | 1.200000 | NOT_AVAILABLE | NOT_AVAILABLE | 6 | 0 | 0 |
| 2023-12 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N9_W2_T3_SB1_TP10

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 125, entry dates 90, entry months 10; SKIP 18, EXCLUDED 69, exclusion share 0.355670; conditional FLAT CLOSED 125.
Net -83.950000 R; PF R / price 0.271267 / 0.266844; expectancy -0.671600 R; win rate 0.200000; average winner / loser 1.250000 / -1.212632 R.
Conditional CLOSED-only DD 85.150000 R; largest winner share 0.106667; largest positive month share 1.000000. Positive / negative / zero months 1 / 9 / 2; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 16 | -15.233333 | 0.132827 | 0.114754 | 18 | 1 | 9 |
| 2023-02 | 17 | -6.100000 | 0.409677 | 0.515152 | 18 | 1 | 8 |
| 2023-03 | 9 | -10.166667 | 0.061538 | 0.058824 | 22 | 4 | 6 |
| 2023-04 | 16 | -7.916667 | 0.366667 | 0.333333 | 18 | 2 | 5 |
| 2023-05 | 10 | -14.583333 | 0.000000 | 0.000000 | 21 | 1 | 9 |
| 2023-06 | 9 | -4.333333 | 0.350000 | 0.350000 | 20 | 2 | 13 |
| 2023-07 | 12 | -14.733333 | 0.063559 | 0.056604 | 19 | 4 | 9 |
| 2023-08 | 21 | -3.500000 | 0.783282 | 0.745455 | 14 | 0 | 4 |
| 2023-09 | 14 | -8.583333 | 0.207692 | 0.272727 | 14 | 3 | 6 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 2 | 0 | 0 |
| 2023-11 | 1 | 1.200000 | NOT_AVAILABLE | NOT_AVAILABLE | 6 | 0 | 0 |
| 2023-12 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N9_W3_T2_SB1_TP2

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 183, entry dates 105, entry months 12; SKIP 24, EXCLUDED 93, exclusion share 0.336957; conditional FLAT CLOSED 183.
Net -102.150000 R; PF R / price 0.331843 / 0.301258; expectancy -0.558197 R; win rate 0.218579; average winner / loser 1.268333 / -1.132469 R.
Conditional CLOSED-only DD 103.233333 R; largest winner share 0.065703; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 22 | -23.550000 | 0.013957 | 0.011905 | 18 | 3 | 12 |
| 2023-02 | 22 | -12.083333 | 0.271357 | 0.358491 | 18 | 2 | 12 |
| 2023-03 | 5 | -5.083333 | 0.089552 | 0.105263 | 22 | 4 | 12 |
| 2023-04 | 18 | -2.033333 | 0.805423 | 0.729730 | 18 | 4 | 7 |
| 2023-05 | 14 | -11.733333 | 0.189873 | 0.254902 | 21 | 1 | 13 |
| 2023-06 | 12 | -2.050000 | 0.711944 | 0.695652 | 20 | 4 | 16 |
| 2023-07 | 30 | -21.933333 | 0.214797 | 0.186275 | 19 | 2 | 9 |
| 2023-08 | 35 | -13.950000 | 0.493341 | 0.464646 | 14 | 2 | 5 |
| 2023-09 | 20 | -7.816667 | 0.457176 | 0.258182 | 14 | 2 | 7 |
| 2023-10 | 1 | -1.500000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-11 | 3 | 1.083333 | 1.565217 | 1.500000 | 6 | 0 | 0 |
| 2023-12 | 1 | -1.500000 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N9_W3_T2_SB1_TP3

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 183, entry dates 105, entry months 12; SKIP 24, EXCLUDED 93, exclusion share 0.336957; conditional FLAT CLOSED 183.
Net -100.316667 R; PF R / price 0.343835 / 0.304306; expectancy -0.548179 R; win rate 0.218579; average winner / loser 1.314167 / -1.132469 R.
Conditional CLOSED-only DD 102.900000 R; largest winner share 0.095117; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 22 | -23.550000 | 0.013957 | 0.011905 | 18 | 3 | 12 |
| 2023-02 | 22 | -12.083333 | 0.271357 | 0.358491 | 18 | 2 | 12 |
| 2023-03 | 5 | -5.083333 | 0.089552 | 0.105263 | 22 | 4 | 12 |
| 2023-04 | 18 | -1.366667 | 0.869219 | 0.783784 | 18 | 4 | 7 |
| 2023-05 | 14 | -11.733333 | 0.189873 | 0.254902 | 21 | 1 | 13 |
| 2023-06 | 12 | -2.050000 | 0.711944 | 0.695652 | 20 | 4 | 16 |
| 2023-07 | 30 | -23.266667 | 0.167064 | 0.147059 | 19 | 2 | 9 |
| 2023-08 | 35 | -12.950000 | 0.529661 | 0.494949 | 14 | 2 | 5 |
| 2023-09 | 20 | -6.316667 | 0.561343 | 0.269091 | 14 | 2 | 7 |
| 2023-10 | 1 | -1.500000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-11 | 3 | 1.083333 | 1.565217 | 1.500000 | 6 | 0 | 0 |
| 2023-12 | 1 | -1.500000 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N9_W3_T2_SB1_TP4

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 183, entry dates 105, entry months 12; SKIP 24, EXCLUDED 93, exclusion share 0.336957; conditional FLAT CLOSED 183.
Net -97.150000 R; PF R / price 0.364548 / 0.314977; expectancy -0.530874 R; win rate 0.218579; average winner / loser 1.393333 / -1.132469 R.
Conditional CLOSED-only DD 101.233333 R; largest winner share 0.119617; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 22 | -23.550000 | 0.013957 | 0.011905 | 18 | 3 | 12 |
| 2023-02 | 22 | -12.083333 | 0.271357 | 0.358491 | 18 | 2 | 12 |
| 2023-03 | 5 | -5.083333 | 0.089552 | 0.105263 | 22 | 4 | 12 |
| 2023-04 | 18 | -1.366667 | 0.869219 | 0.783784 | 18 | 4 | 7 |
| 2023-05 | 14 | -11.733333 | 0.189873 | 0.254902 | 21 | 1 | 13 |
| 2023-06 | 12 | -2.050000 | 0.711944 | 0.695652 | 20 | 4 | 16 |
| 2023-07 | 30 | -23.266667 | 0.167064 | 0.147059 | 19 | 2 | 9 |
| 2023-08 | 35 | -11.283333 | 0.590194 | 0.545455 | 14 | 2 | 5 |
| 2023-09 | 20 | -4.816667 | 0.665509 | 0.280000 | 14 | 2 | 7 |
| 2023-10 | 1 | -1.500000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-11 | 3 | 1.083333 | 1.565217 | 1.500000 | 6 | 0 | 0 |
| 2023-12 | 1 | -1.500000 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N9_W3_T2_SB1_TP5

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 183, entry dates 105, entry months 12; SKIP 24, EXCLUDED 93, exclusion share 0.336957; conditional FLAT CLOSED 183.
Net -93.983333 R; PF R / price 0.385261 / 0.325648; expectancy -0.513570 R; win rate 0.218579; average winner / loser 1.472500 / -1.132469 R.
Conditional CLOSED-only DD 99.566667 R; largest winner share 0.141483; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 22 | -23.550000 | 0.013957 | 0.011905 | 18 | 3 | 12 |
| 2023-02 | 22 | -12.083333 | 0.271357 | 0.358491 | 18 | 2 | 12 |
| 2023-03 | 5 | -5.083333 | 0.089552 | 0.105263 | 22 | 4 | 12 |
| 2023-04 | 18 | -1.366667 | 0.869219 | 0.783784 | 18 | 4 | 7 |
| 2023-05 | 14 | -11.733333 | 0.189873 | 0.254902 | 21 | 1 | 13 |
| 2023-06 | 12 | -2.050000 | 0.711944 | 0.695652 | 20 | 4 | 16 |
| 2023-07 | 30 | -23.266667 | 0.167064 | 0.147059 | 19 | 2 | 9 |
| 2023-08 | 35 | -9.616667 | 0.650726 | 0.595960 | 14 | 2 | 5 |
| 2023-09 | 20 | -3.316667 | 0.769676 | 0.290909 | 14 | 2 | 7 |
| 2023-10 | 1 | -1.500000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-11 | 3 | 1.083333 | 1.565217 | 1.500000 | 6 | 0 | 0 |
| 2023-12 | 1 | -1.500000 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N9_W3_T2_SB1_TP6

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 183, entry dates 105, entry months 12; SKIP 24, EXCLUDED 93, exclusion share 0.336957; conditional FLAT CLOSED 183.
Net -90.816667 R; PF R / price 0.405974 / 0.336319; expectancy -0.496266 R; win rate 0.218579; average winner / loser 1.551667 / -1.132469 R.
Conditional CLOSED-only DD 97.900000 R; largest winner share 0.161117; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 22 | -23.550000 | 0.013957 | 0.011905 | 18 | 3 | 12 |
| 2023-02 | 22 | -12.083333 | 0.271357 | 0.358491 | 18 | 2 | 12 |
| 2023-03 | 5 | -5.083333 | 0.089552 | 0.105263 | 22 | 4 | 12 |
| 2023-04 | 18 | -1.366667 | 0.869219 | 0.783784 | 18 | 4 | 7 |
| 2023-05 | 14 | -11.733333 | 0.189873 | 0.254902 | 21 | 1 | 13 |
| 2023-06 | 12 | -2.050000 | 0.711944 | 0.695652 | 20 | 4 | 16 |
| 2023-07 | 30 | -23.266667 | 0.167064 | 0.147059 | 19 | 2 | 9 |
| 2023-08 | 35 | -7.950000 | 0.711259 | 0.646465 | 14 | 2 | 5 |
| 2023-09 | 20 | -1.816667 | 0.873843 | 0.301818 | 14 | 2 | 7 |
| 2023-10 | 1 | -1.500000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-11 | 3 | 1.083333 | 1.565217 | 1.500000 | 6 | 0 | 0 |
| 2023-12 | 1 | -1.500000 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N9_W3_T2_SB1_TP7

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 183, entry dates 105, entry months 12; SKIP 24, EXCLUDED 93, exclusion share 0.336957; conditional FLAT CLOSED 183.
Net -87.650000 R; PF R / price 0.426687 / 0.346989; expectancy -0.478962 R; win rate 0.218579; average winner / loser 1.630833 / -1.132469 R.
Conditional CLOSED-only DD 96.233333 R; largest winner share 0.178845; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 22 | -23.550000 | 0.013957 | 0.011905 | 18 | 3 | 12 |
| 2023-02 | 22 | -12.083333 | 0.271357 | 0.358491 | 18 | 2 | 12 |
| 2023-03 | 5 | -5.083333 | 0.089552 | 0.105263 | 22 | 4 | 12 |
| 2023-04 | 18 | -1.366667 | 0.869219 | 0.783784 | 18 | 4 | 7 |
| 2023-05 | 14 | -11.733333 | 0.189873 | 0.254902 | 21 | 1 | 13 |
| 2023-06 | 12 | -2.050000 | 0.711944 | 0.695652 | 20 | 4 | 16 |
| 2023-07 | 30 | -23.266667 | 0.167064 | 0.147059 | 19 | 2 | 9 |
| 2023-08 | 35 | -6.283333 | 0.771792 | 0.696970 | 14 | 2 | 5 |
| 2023-09 | 20 | -0.316667 | 0.978009 | 0.312727 | 14 | 2 | 7 |
| 2023-10 | 1 | -1.500000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-11 | 3 | 1.083333 | 1.565217 | 1.500000 | 6 | 0 | 0 |
| 2023-12 | 1 | -1.500000 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N9_W3_T2_SB1_TP8

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 183, entry dates 105, entry months 12; SKIP 24, EXCLUDED 93, exclusion share 0.336957; conditional FLAT CLOSED 183.
Net -84.483333 R; PF R / price 0.447400 / 0.357660; expectancy -0.461658 R; win rate 0.218579; average winner / loser 1.710000 / -1.132469 R.
Conditional CLOSED-only DD 94.566667 R; largest winner share 0.194932; largest positive month share 0.522059. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 22 | -23.550000 | 0.013957 | 0.011905 | 18 | 3 | 12 |
| 2023-02 | 22 | -12.083333 | 0.271357 | 0.358491 | 18 | 2 | 12 |
| 2023-03 | 5 | -5.083333 | 0.089552 | 0.105263 | 22 | 4 | 12 |
| 2023-04 | 18 | -1.366667 | 0.869219 | 0.783784 | 18 | 4 | 7 |
| 2023-05 | 14 | -11.733333 | 0.189873 | 0.254902 | 21 | 1 | 13 |
| 2023-06 | 12 | -2.050000 | 0.711944 | 0.695652 | 20 | 4 | 16 |
| 2023-07 | 30 | -23.266667 | 0.167064 | 0.147059 | 19 | 2 | 9 |
| 2023-08 | 35 | -4.616667 | 0.832324 | 0.747475 | 14 | 2 | 5 |
| 2023-09 | 20 | 1.183333 | 1.082176 | 0.323636 | 14 | 2 | 7 |
| 2023-10 | 1 | -1.500000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-11 | 3 | 1.083333 | 1.565217 | 1.500000 | 6 | 0 | 0 |
| 2023-12 | 1 | -1.500000 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N9_W3_T2_SB1_TP9

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 183, entry dates 105, entry months 12; SKIP 24, EXCLUDED 93, exclusion share 0.336957; conditional FLAT CLOSED 183.
Net -81.316667 R; PF R / price 0.468113 / 0.368331; expectancy -0.444353 R; win rate 0.218579; average winner / loser 1.789167 / -1.132469 R.
Conditional CLOSED-only DD 92.900000 R; largest winner share 0.209595; largest positive month share 0.712389. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 22 | -23.550000 | 0.013957 | 0.011905 | 18 | 3 | 12 |
| 2023-02 | 22 | -12.083333 | 0.271357 | 0.358491 | 18 | 2 | 12 |
| 2023-03 | 5 | -5.083333 | 0.089552 | 0.105263 | 22 | 4 | 12 |
| 2023-04 | 18 | -1.366667 | 0.869219 | 0.783784 | 18 | 4 | 7 |
| 2023-05 | 14 | -11.733333 | 0.189873 | 0.254902 | 21 | 1 | 13 |
| 2023-06 | 12 | -2.050000 | 0.711944 | 0.695652 | 20 | 4 | 16 |
| 2023-07 | 30 | -23.266667 | 0.167064 | 0.147059 | 19 | 2 | 9 |
| 2023-08 | 35 | -2.950000 | 0.892857 | 0.797980 | 14 | 2 | 5 |
| 2023-09 | 20 | 2.683333 | 1.186343 | 0.334545 | 14 | 2 | 7 |
| 2023-10 | 1 | -1.500000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-11 | 3 | 1.083333 | 1.565217 | 1.500000 | 6 | 0 | 0 |
| 2023-12 | 1 | -1.500000 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N9_W3_T2_SB1_TP10

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 183, entry dates 105, entry months 12; SKIP 24, EXCLUDED 93, exclusion share 0.336957; conditional FLAT CLOSED 183.
Net -78.150000 R; PF R / price 0.488826 / 0.379002; expectancy -0.427049 R; win rate 0.218579; average winner / loser 1.868333 / -1.132469 R.
Conditional CLOSED-only DD 91.233333 R; largest winner share 0.223015; largest positive month share 0.794304. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 22 | -23.550000 | 0.013957 | 0.011905 | 18 | 3 | 12 |
| 2023-02 | 22 | -12.083333 | 0.271357 | 0.358491 | 18 | 2 | 12 |
| 2023-03 | 5 | -5.083333 | 0.089552 | 0.105263 | 22 | 4 | 12 |
| 2023-04 | 18 | -1.366667 | 0.869219 | 0.783784 | 18 | 4 | 7 |
| 2023-05 | 14 | -11.733333 | 0.189873 | 0.254902 | 21 | 1 | 13 |
| 2023-06 | 12 | -2.050000 | 0.711944 | 0.695652 | 20 | 4 | 16 |
| 2023-07 | 30 | -23.266667 | 0.167064 | 0.147059 | 19 | 2 | 9 |
| 2023-08 | 35 | -1.283333 | 0.953390 | 0.848485 | 14 | 2 | 5 |
| 2023-09 | 20 | 4.183333 | 1.290509 | 0.345455 | 14 | 2 | 7 |
| 2023-10 | 1 | -1.500000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-11 | 3 | 1.083333 | 1.565217 | 1.500000 | 6 | 0 | 0 |
| 2023-12 | 1 | -1.500000 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N9_W3_T3_SB1_TP2

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 157, entry dates 101, entry months 10; SKIP 23, EXCLUDED 75, exclusion share 0.323276; conditional FLAT CLOSED 157.
Net -95.016667 R; PF R / price 0.314701 / 0.283210; expectancy -0.605202 R; win rate 0.216561; average winner / loser 1.283333 / -1.195259 R.
Conditional CLOSED-only DD 99.350000 R; largest winner share 0.076394; largest positive month share 0.661157. Positive / negative / zero months 2 / 8 / 2; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 21 | -24.716667 | 0.013307 | 0.011236 | 18 | 1 | 11 |
| 2023-02 | 14 | -11.333333 | 0.180723 | 0.232558 | 18 | 3 | 9 |
| 2023-03 | 9 | -10.500000 | 0.059701 | 0.052632 | 22 | 4 | 9 |
| 2023-04 | 17 | -5.483333 | 0.585642 | 0.555556 | 18 | 2 | 6 |
| 2023-05 | 15 | -13.366667 | 0.149523 | 0.189655 | 21 | 2 | 9 |
| 2023-06 | 16 | -8.633333 | 0.217523 | 0.228571 | 20 | 2 | 13 |
| 2023-07 | 19 | -12.300000 | 0.260521 | 0.229508 | 19 | 6 | 8 |
| 2023-08 | 31 | -10.700000 | 0.554167 | 0.567901 | 14 | 1 | 1 |
| 2023-09 | 13 | 0.683333 | 1.108179 | 0.704348 | 14 | 2 | 9 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 2 | 0 | 0 |
| 2023-11 | 2 | 1.333333 | 1.800000 | 1.800000 | 6 | 0 | 0 |
| 2023-12 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N9_W3_T3_SB1_TP3

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 157, entry dates 101, entry months 10; SKIP 23, EXCLUDED 75, exclusion share 0.323276; conditional FLAT CLOSED 157.
Net -94.850000 R; PF R / price 0.315903 / 0.276030; expectancy -0.604140 R; win rate 0.216561; average winner / loser 1.288235 / -1.195259 R.
Conditional CLOSED-only DD 100.683333 R; largest winner share 0.102740; largest positive month share 0.620853. Positive / negative / zero months 2 / 8 / 2; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 21 | -24.716667 | 0.013307 | 0.011236 | 18 | 1 | 11 |
| 2023-02 | 14 | -11.333333 | 0.180723 | 0.232558 | 18 | 3 | 9 |
| 2023-03 | 9 | -10.500000 | 0.059701 | 0.052632 | 22 | 4 | 9 |
| 2023-04 | 17 | -4.816667 | 0.636020 | 0.600000 | 18 | 2 | 6 |
| 2023-05 | 15 | -13.366667 | 0.149523 | 0.189655 | 21 | 2 | 9 |
| 2023-06 | 16 | -8.633333 | 0.217523 | 0.228571 | 20 | 2 | 13 |
| 2023-07 | 19 | -13.633333 | 0.180361 | 0.163934 | 19 | 6 | 8 |
| 2023-08 | 31 | -11.366667 | 0.526389 | 0.543210 | 14 | 1 | 1 |
| 2023-09 | 13 | 2.183333 | 1.345646 | 0.730435 | 14 | 2 | 9 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 2 | 0 | 0 |
| 2023-11 | 2 | 1.333333 | 1.800000 | 1.800000 | 6 | 0 | 0 |
| 2023-12 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N9_W3_T3_SB1_TP4

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 157, entry dates 101, entry months 10; SKIP 23, EXCLUDED 75, exclusion share 0.323276; conditional FLAT CLOSED 157.
Net -93.350000 R; PF R / price 0.326722 / 0.277297; expectancy -0.594586 R; win rate 0.216561; average winner / loser 1.332353 / -1.195259 R.
Conditional CLOSED-only DD 100.683333 R; largest winner share 0.132450; largest positive month share 0.734219. Positive / negative / zero months 2 / 8 / 2; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 21 | -24.716667 | 0.013307 | 0.011236 | 18 | 1 | 11 |
| 2023-02 | 14 | -11.333333 | 0.180723 | 0.232558 | 18 | 3 | 9 |
| 2023-03 | 9 | -10.500000 | 0.059701 | 0.052632 | 22 | 4 | 9 |
| 2023-04 | 17 | -4.816667 | 0.636020 | 0.600000 | 18 | 2 | 6 |
| 2023-05 | 15 | -13.366667 | 0.149523 | 0.189655 | 21 | 2 | 9 |
| 2023-06 | 16 | -8.633333 | 0.217523 | 0.228571 | 20 | 2 | 13 |
| 2023-07 | 19 | -13.633333 | 0.180361 | 0.163934 | 19 | 6 | 8 |
| 2023-08 | 31 | -11.366667 | 0.526389 | 0.543210 | 14 | 1 | 1 |
| 2023-09 | 13 | 3.683333 | 1.583113 | 0.756522 | 14 | 2 | 9 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 2 | 0 | 0 |
| 2023-11 | 2 | 1.333333 | 1.800000 | 1.800000 | 6 | 0 | 0 |
| 2023-12 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N9_W3_T3_SB1_TP5

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 157, entry dates 101, entry months 10; SKIP 23, EXCLUDED 75, exclusion share 0.323276; conditional FLAT CLOSED 157.
Net -91.850000 R; PF R / price 0.337541 / 0.278564; expectancy -0.585032 R; win rate 0.216561; average winner / loser 1.376471 / -1.195259 R.
Conditional CLOSED-only DD 100.683333 R; largest winner share 0.160256; largest positive month share 0.795396. Positive / negative / zero months 2 / 8 / 2; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 21 | -24.716667 | 0.013307 | 0.011236 | 18 | 1 | 11 |
| 2023-02 | 14 | -11.333333 | 0.180723 | 0.232558 | 18 | 3 | 9 |
| 2023-03 | 9 | -10.500000 | 0.059701 | 0.052632 | 22 | 4 | 9 |
| 2023-04 | 17 | -4.816667 | 0.636020 | 0.600000 | 18 | 2 | 6 |
| 2023-05 | 15 | -13.366667 | 0.149523 | 0.189655 | 21 | 2 | 9 |
| 2023-06 | 16 | -8.633333 | 0.217523 | 0.228571 | 20 | 2 | 13 |
| 2023-07 | 19 | -13.633333 | 0.180361 | 0.163934 | 19 | 6 | 8 |
| 2023-08 | 31 | -11.366667 | 0.526389 | 0.543210 | 14 | 1 | 1 |
| 2023-09 | 13 | 5.183333 | 1.820580 | 0.782609 | 14 | 2 | 9 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 2 | 0 | 0 |
| 2023-11 | 2 | 1.333333 | 1.800000 | 1.800000 | 6 | 0 | 0 |
| 2023-12 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N9_W3_T3_SB1_TP6

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 157, entry dates 101, entry months 10; SKIP 23, EXCLUDED 75, exclusion share 0.323276; conditional FLAT CLOSED 157.
Net -90.350000 R; PF R / price 0.348359 / 0.279831; expectancy -0.575478 R; win rate 0.216561; average winner / loser 1.420588 / -1.195259 R.
Conditional CLOSED-only DD 100.683333 R; largest winner share 0.186335; largest positive month share 0.833680. Positive / negative / zero months 2 / 8 / 2; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 21 | -24.716667 | 0.013307 | 0.011236 | 18 | 1 | 11 |
| 2023-02 | 14 | -11.333333 | 0.180723 | 0.232558 | 18 | 3 | 9 |
| 2023-03 | 9 | -10.500000 | 0.059701 | 0.052632 | 22 | 4 | 9 |
| 2023-04 | 17 | -4.816667 | 0.636020 | 0.600000 | 18 | 2 | 6 |
| 2023-05 | 15 | -13.366667 | 0.149523 | 0.189655 | 21 | 2 | 9 |
| 2023-06 | 16 | -8.633333 | 0.217523 | 0.228571 | 20 | 2 | 13 |
| 2023-07 | 19 | -13.633333 | 0.180361 | 0.163934 | 19 | 6 | 8 |
| 2023-08 | 31 | -11.366667 | 0.526389 | 0.543210 | 14 | 1 | 1 |
| 2023-09 | 13 | 6.683333 | 2.058047 | 0.808696 | 14 | 2 | 9 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 2 | 0 | 0 |
| 2023-11 | 2 | 1.333333 | 1.800000 | 1.800000 | 6 | 0 | 0 |
| 2023-12 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N9_W3_T3_SB1_TP7

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 157, entry dates 101, entry months 10; SKIP 23, EXCLUDED 75, exclusion share 0.323276; conditional FLAT CLOSED 157.
Net -88.850000 R; PF R / price 0.359178 / 0.281098; expectancy -0.565924 R; win rate 0.216561; average winner / loser 1.464706 / -1.195259 R.
Conditional CLOSED-only DD 100.683333 R; largest winner share 0.210843; largest positive month share 0.859895. Positive / negative / zero months 2 / 8 / 2; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 21 | -24.716667 | 0.013307 | 0.011236 | 18 | 1 | 11 |
| 2023-02 | 14 | -11.333333 | 0.180723 | 0.232558 | 18 | 3 | 9 |
| 2023-03 | 9 | -10.500000 | 0.059701 | 0.052632 | 22 | 4 | 9 |
| 2023-04 | 17 | -4.816667 | 0.636020 | 0.600000 | 18 | 2 | 6 |
| 2023-05 | 15 | -13.366667 | 0.149523 | 0.189655 | 21 | 2 | 9 |
| 2023-06 | 16 | -8.633333 | 0.217523 | 0.228571 | 20 | 2 | 13 |
| 2023-07 | 19 | -13.633333 | 0.180361 | 0.163934 | 19 | 6 | 8 |
| 2023-08 | 31 | -11.366667 | 0.526389 | 0.543210 | 14 | 1 | 1 |
| 2023-09 | 13 | 8.183333 | 2.295515 | 0.834783 | 14 | 2 | 9 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 2 | 0 | 0 |
| 2023-11 | 2 | 1.333333 | 1.800000 | 1.800000 | 6 | 0 | 0 |
| 2023-12 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N9_W3_T3_SB1_TP8

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 157, entry dates 101, entry months 10; SKIP 23, EXCLUDED 75, exclusion share 0.323276; conditional FLAT CLOSED 157.
Net -87.350000 R; PF R / price 0.369996 / 0.282365; expectancy -0.556369 R; win rate 0.216561; average winner / loser 1.508824 / -1.195259 R.
Conditional CLOSED-only DD 100.683333 R; largest winner share 0.233918; largest positive month share 0.878971. Positive / negative / zero months 2 / 8 / 2; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 21 | -24.716667 | 0.013307 | 0.011236 | 18 | 1 | 11 |
| 2023-02 | 14 | -11.333333 | 0.180723 | 0.232558 | 18 | 3 | 9 |
| 2023-03 | 9 | -10.500000 | 0.059701 | 0.052632 | 22 | 4 | 9 |
| 2023-04 | 17 | -4.816667 | 0.636020 | 0.600000 | 18 | 2 | 6 |
| 2023-05 | 15 | -13.366667 | 0.149523 | 0.189655 | 21 | 2 | 9 |
| 2023-06 | 16 | -8.633333 | 0.217523 | 0.228571 | 20 | 2 | 13 |
| 2023-07 | 19 | -13.633333 | 0.180361 | 0.163934 | 19 | 6 | 8 |
| 2023-08 | 31 | -11.366667 | 0.526389 | 0.543210 | 14 | 1 | 1 |
| 2023-09 | 13 | 9.683333 | 2.532982 | 0.860870 | 14 | 2 | 9 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 2 | 0 | 0 |
| 2023-11 | 2 | 1.333333 | 1.800000 | 1.800000 | 6 | 0 | 0 |
| 2023-12 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N9_W3_T3_SB1_TP9

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors.
CLOSED 157, entry dates 101, entry months 10; SKIP 23, EXCLUDED 75, exclusion share 0.323276; conditional FLAT CLOSED 157.
Net -85.850000 R; PF R / price 0.380815 / 0.283633; expectancy -0.546815 R; win rate 0.216561; average winner / loser 1.552941 / -1.195259 R.
Conditional CLOSED-only DD 100.683333 R; largest winner share 0.255682; largest positive month share 0.893475. Positive / negative / zero months 2 / 8 / 2; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 21 | -24.716667 | 0.013307 | 0.011236 | 18 | 1 | 11 |
| 2023-02 | 14 | -11.333333 | 0.180723 | 0.232558 | 18 | 3 | 9 |
| 2023-03 | 9 | -10.500000 | 0.059701 | 0.052632 | 22 | 4 | 9 |
| 2023-04 | 17 | -4.816667 | 0.636020 | 0.600000 | 18 | 2 | 6 |
| 2023-05 | 15 | -13.366667 | 0.149523 | 0.189655 | 21 | 2 | 9 |
| 2023-06 | 16 | -8.633333 | 0.217523 | 0.228571 | 20 | 2 | 13 |
| 2023-07 | 19 | -13.633333 | 0.180361 | 0.163934 | 19 | 6 | 8 |
| 2023-08 | 31 | -11.366667 | 0.526389 | 0.543210 | 14 | 1 | 1 |
| 2023-09 | 13 | 11.183333 | 2.770449 | 0.886957 | 14 | 2 | 9 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 2 | 0 | 0 |
| 2023-11 | 2 | 1.333333 | 1.800000 | 1.800000 | 6 | 0 | 0 |
| 2023-12 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N9_W3_T3_SB1_TP10

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors.
CLOSED 157, entry dates 101, entry months 10; SKIP 23, EXCLUDED 75, exclusion share 0.323276; conditional FLAT CLOSED 157.
Net -84.350000 R; PF R / price 0.391634 / 0.284900; expectancy -0.537261 R; win rate 0.216561; average winner / loser 1.597059 / -1.195259 R.
Conditional CLOSED-only DD 100.683333 R; largest winner share 0.276243; largest positive month share 0.904875. Positive / negative / zero months 2 / 8 / 2; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 21 | -24.716667 | 0.013307 | 0.011236 | 18 | 1 | 11 |
| 2023-02 | 14 | -11.333333 | 0.180723 | 0.232558 | 18 | 3 | 9 |
| 2023-03 | 9 | -10.500000 | 0.059701 | 0.052632 | 22 | 4 | 9 |
| 2023-04 | 17 | -4.816667 | 0.636020 | 0.600000 | 18 | 2 | 6 |
| 2023-05 | 15 | -13.366667 | 0.149523 | 0.189655 | 21 | 2 | 9 |
| 2023-06 | 16 | -8.633333 | 0.217523 | 0.228571 | 20 | 2 | 13 |
| 2023-07 | 19 | -13.633333 | 0.180361 | 0.163934 | 19 | 6 | 8 |
| 2023-08 | 31 | -11.366667 | 0.526389 | 0.543210 | 14 | 1 | 1 |
| 2023-09 | 13 | 12.683333 | 3.007916 | 0.913043 | 14 | 2 | 9 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 2 | 0 | 0 |
| 2023-11 | 2 | 1.333333 | 1.800000 | 1.800000 | 6 | 0 | 0 |
| 2023-12 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N10_W2_T2_SB1_TP2

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 131, entry dates 89, entry months 10; SKIP 24, EXCLUDED 75, exclusion share 0.364078; conditional FLAT CLOSED 131.
Net -97.583333 R; PF R / price 0.265831 / 0.261293; expectancy -0.744911 R; win rate 0.183206; average winner / loser 1.472222 / -1.303105 R.
Conditional CLOSED-only DD 97.583333 R; largest winner share 0.094340; largest positive month share 1.000000. Positive / negative / zero months 1 / 9 / 2; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 22 | -23.316667 | 0.125078 | 0.116279 | 18 | 5 | 10 |
| 2023-02 | 20 | -21.000000 | 0.027027 | 0.026316 | 18 | 2 | 8 |
| 2023-03 | 8 | -8.233333 | 0.000000 | 0.000000 | 22 | 3 | 9 |
| 2023-04 | 12 | 2.333333 | 1.318182 | 1.333333 | 18 | 4 | 8 |
| 2023-05 | 8 | -2.650000 | 0.606436 | 0.640000 | 21 | 2 | 11 |
| 2023-06 | 10 | -5.416667 | 0.362745 | 0.366667 | 20 | 4 | 12 |
| 2023-07 | 10 | -11.000000 | 0.043478 | 0.048780 | 19 | 1 | 7 |
| 2023-08 | 21 | -11.566667 | 0.435313 | 0.373333 | 14 | 1 | 3 |
| 2023-09 | 19 | -15.233333 | 0.253268 | 0.253731 | 14 | 2 | 7 |
| 2023-10 | 1 | -1.500000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-11 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 6 | 0 | 0 |
| 2023-12 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N10_W2_T2_SB1_TP3

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 131, entry dates 89, entry months 10; SKIP 24, EXCLUDED 75, exclusion share 0.364078; conditional FLAT CLOSED 131.
Net -96.333333 R; PF R / price 0.275235 / 0.270151; expectancy -0.735369 R; win rate 0.183206; average winner / loser 1.524306 / -1.303105 R.
Conditional CLOSED-only DD 96.333333 R; largest winner share 0.136674; largest positive month share 1.000000. Positive / negative / zero months 1 / 9 / 2; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 22 | -21.650000 | 0.187617 | 0.174419 | 18 | 5 | 10 |
| 2023-02 | 20 | -21.000000 | 0.027027 | 0.026316 | 18 | 2 | 8 |
| 2023-03 | 8 | -8.233333 | 0.000000 | 0.000000 | 22 | 3 | 9 |
| 2023-04 | 12 | 1.916667 | 1.261364 | 1.291667 | 18 | 4 | 8 |
| 2023-05 | 8 | -2.650000 | 0.606436 | 0.640000 | 21 | 2 | 11 |
| 2023-06 | 10 | -5.416667 | 0.362745 | 0.366667 | 20 | 4 | 12 |
| 2023-07 | 10 | -11.000000 | 0.043478 | 0.048780 | 19 | 1 | 7 |
| 2023-08 | 21 | -11.566667 | 0.435313 | 0.373333 | 14 | 1 | 3 |
| 2023-09 | 19 | -15.233333 | 0.253268 | 0.253731 | 14 | 2 | 7 |
| 2023-10 | 1 | -1.500000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-11 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 6 | 0 | 0 |
| 2023-12 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N10_W2_T2_SB1_TP4

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 131, entry dates 89, entry months 10; SKIP 24, EXCLUDED 75, exclusion share 0.364078; conditional FLAT CLOSED 131.
Net -94.666667 R; PF R / price 0.287774 / 0.281222; expectancy -0.722646 R; win rate 0.183206; average winner / loser 1.593750 / -1.303105 R.
Conditional CLOSED-only DD 94.666667 R; largest winner share 0.174292; largest positive month share 1.000000. Positive / negative / zero months 1 / 9 / 2; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 22 | -19.983333 | 0.250156 | 0.232558 | 18 | 5 | 10 |
| 2023-02 | 20 | -21.000000 | 0.027027 | 0.026316 | 18 | 2 | 8 |
| 2023-03 | 8 | -8.233333 | 0.000000 | 0.000000 | 22 | 3 | 9 |
| 2023-04 | 12 | 1.916667 | 1.261364 | 1.291667 | 18 | 4 | 8 |
| 2023-05 | 8 | -2.650000 | 0.606436 | 0.640000 | 21 | 2 | 11 |
| 2023-06 | 10 | -5.416667 | 0.362745 | 0.366667 | 20 | 4 | 12 |
| 2023-07 | 10 | -11.000000 | 0.043478 | 0.048780 | 19 | 1 | 7 |
| 2023-08 | 21 | -11.566667 | 0.435313 | 0.373333 | 14 | 1 | 3 |
| 2023-09 | 19 | -15.233333 | 0.253268 | 0.253731 | 14 | 2 | 7 |
| 2023-10 | 1 | -1.500000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-11 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 6 | 0 | 0 |
| 2023-12 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N10_W2_T2_SB1_TP5

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 131, entry dates 89, entry months 10; SKIP 24, EXCLUDED 75, exclusion share 0.364078; conditional FLAT CLOSED 131.
Net -99.000000 R; PF R / price 0.255172 / 0.252436; expectancy -0.755725 R; win rate 0.183206; average winner / loser 1.413194 / -1.303105 R.
Conditional CLOSED-only DD 99.000000 R; largest winner share 0.098280; largest positive month share 1.000000. Positive / negative / zero months 1 / 9 / 2; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 22 | -24.316667 | 0.087555 | 0.081395 | 18 | 5 | 10 |
| 2023-02 | 20 | -21.000000 | 0.027027 | 0.026316 | 18 | 2 | 8 |
| 2023-03 | 8 | -8.233333 | 0.000000 | 0.000000 | 22 | 3 | 9 |
| 2023-04 | 12 | 1.916667 | 1.261364 | 1.291667 | 18 | 4 | 8 |
| 2023-05 | 8 | -2.650000 | 0.606436 | 0.640000 | 21 | 2 | 11 |
| 2023-06 | 10 | -5.416667 | 0.362745 | 0.366667 | 20 | 4 | 12 |
| 2023-07 | 10 | -11.000000 | 0.043478 | 0.048780 | 19 | 1 | 7 |
| 2023-08 | 21 | -11.566667 | 0.435313 | 0.373333 | 14 | 1 | 3 |
| 2023-09 | 19 | -15.233333 | 0.253268 | 0.253731 | 14 | 2 | 7 |
| 2023-10 | 1 | -1.500000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-11 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 6 | 0 | 0 |
| 2023-12 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N10_W2_T2_SB1_TP6

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 131, entry dates 89, entry months 10; SKIP 24, EXCLUDED 75, exclusion share 0.364078; conditional FLAT CLOSED 131.
Net -99.000000 R; PF R / price 0.255172 / 0.252436; expectancy -0.755725 R; win rate 0.183206; average winner / loser 1.413194 / -1.303105 R.
Conditional CLOSED-only DD 99.000000 R; largest winner share 0.098280; largest positive month share 1.000000. Positive / negative / zero months 1 / 9 / 2; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 22 | -24.316667 | 0.087555 | 0.081395 | 18 | 5 | 10 |
| 2023-02 | 20 | -21.000000 | 0.027027 | 0.026316 | 18 | 2 | 8 |
| 2023-03 | 8 | -8.233333 | 0.000000 | 0.000000 | 22 | 3 | 9 |
| 2023-04 | 12 | 1.916667 | 1.261364 | 1.291667 | 18 | 4 | 8 |
| 2023-05 | 8 | -2.650000 | 0.606436 | 0.640000 | 21 | 2 | 11 |
| 2023-06 | 10 | -5.416667 | 0.362745 | 0.366667 | 20 | 4 | 12 |
| 2023-07 | 10 | -11.000000 | 0.043478 | 0.048780 | 19 | 1 | 7 |
| 2023-08 | 21 | -11.566667 | 0.435313 | 0.373333 | 14 | 1 | 3 |
| 2023-09 | 19 | -15.233333 | 0.253268 | 0.253731 | 14 | 2 | 7 |
| 2023-10 | 1 | -1.500000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-11 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 6 | 0 | 0 |
| 2023-12 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N10_W2_T2_SB1_TP7

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 131, entry dates 89, entry months 10; SKIP 24, EXCLUDED 75, exclusion share 0.364078; conditional FLAT CLOSED 131.
Net -99.000000 R; PF R / price 0.255172 / 0.252436; expectancy -0.755725 R; win rate 0.183206; average winner / loser 1.413194 / -1.303105 R.
Conditional CLOSED-only DD 99.000000 R; largest winner share 0.098280; largest positive month share 1.000000. Positive / negative / zero months 1 / 9 / 2; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 22 | -24.316667 | 0.087555 | 0.081395 | 18 | 5 | 10 |
| 2023-02 | 20 | -21.000000 | 0.027027 | 0.026316 | 18 | 2 | 8 |
| 2023-03 | 8 | -8.233333 | 0.000000 | 0.000000 | 22 | 3 | 9 |
| 2023-04 | 12 | 1.916667 | 1.261364 | 1.291667 | 18 | 4 | 8 |
| 2023-05 | 8 | -2.650000 | 0.606436 | 0.640000 | 21 | 2 | 11 |
| 2023-06 | 10 | -5.416667 | 0.362745 | 0.366667 | 20 | 4 | 12 |
| 2023-07 | 10 | -11.000000 | 0.043478 | 0.048780 | 19 | 1 | 7 |
| 2023-08 | 21 | -11.566667 | 0.435313 | 0.373333 | 14 | 1 | 3 |
| 2023-09 | 19 | -15.233333 | 0.253268 | 0.253731 | 14 | 2 | 7 |
| 2023-10 | 1 | -1.500000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-11 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 6 | 0 | 0 |
| 2023-12 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N10_W2_T2_SB1_TP8

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 131, entry dates 89, entry months 10; SKIP 24, EXCLUDED 75, exclusion share 0.364078; conditional FLAT CLOSED 131.
Net -99.000000 R; PF R / price 0.255172 / 0.252436; expectancy -0.755725 R; win rate 0.183206; average winner / loser 1.413194 / -1.303105 R.
Conditional CLOSED-only DD 99.000000 R; largest winner share 0.098280; largest positive month share 1.000000. Positive / negative / zero months 1 / 9 / 2; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 22 | -24.316667 | 0.087555 | 0.081395 | 18 | 5 | 10 |
| 2023-02 | 20 | -21.000000 | 0.027027 | 0.026316 | 18 | 2 | 8 |
| 2023-03 | 8 | -8.233333 | 0.000000 | 0.000000 | 22 | 3 | 9 |
| 2023-04 | 12 | 1.916667 | 1.261364 | 1.291667 | 18 | 4 | 8 |
| 2023-05 | 8 | -2.650000 | 0.606436 | 0.640000 | 21 | 2 | 11 |
| 2023-06 | 10 | -5.416667 | 0.362745 | 0.366667 | 20 | 4 | 12 |
| 2023-07 | 10 | -11.000000 | 0.043478 | 0.048780 | 19 | 1 | 7 |
| 2023-08 | 21 | -11.566667 | 0.435313 | 0.373333 | 14 | 1 | 3 |
| 2023-09 | 19 | -15.233333 | 0.253268 | 0.253731 | 14 | 2 | 7 |
| 2023-10 | 1 | -1.500000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-11 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 6 | 0 | 0 |
| 2023-12 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N10_W2_T2_SB1_TP9

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 131, entry dates 89, entry months 10; SKIP 24, EXCLUDED 75, exclusion share 0.364078; conditional FLAT CLOSED 131.
Net -99.000000 R; PF R / price 0.255172 / 0.252436; expectancy -0.755725 R; win rate 0.183206; average winner / loser 1.413194 / -1.303105 R.
Conditional CLOSED-only DD 99.000000 R; largest winner share 0.098280; largest positive month share 1.000000. Positive / negative / zero months 1 / 9 / 2; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 22 | -24.316667 | 0.087555 | 0.081395 | 18 | 5 | 10 |
| 2023-02 | 20 | -21.000000 | 0.027027 | 0.026316 | 18 | 2 | 8 |
| 2023-03 | 8 | -8.233333 | 0.000000 | 0.000000 | 22 | 3 | 9 |
| 2023-04 | 12 | 1.916667 | 1.261364 | 1.291667 | 18 | 4 | 8 |
| 2023-05 | 8 | -2.650000 | 0.606436 | 0.640000 | 21 | 2 | 11 |
| 2023-06 | 10 | -5.416667 | 0.362745 | 0.366667 | 20 | 4 | 12 |
| 2023-07 | 10 | -11.000000 | 0.043478 | 0.048780 | 19 | 1 | 7 |
| 2023-08 | 21 | -11.566667 | 0.435313 | 0.373333 | 14 | 1 | 3 |
| 2023-09 | 19 | -15.233333 | 0.253268 | 0.253731 | 14 | 2 | 7 |
| 2023-10 | 1 | -1.500000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-11 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 6 | 0 | 0 |
| 2023-12 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N10_W2_T2_SB1_TP10

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 131, entry dates 89, entry months 10; SKIP 24, EXCLUDED 75, exclusion share 0.364078; conditional FLAT CLOSED 131.
Net -99.000000 R; PF R / price 0.255172 / 0.252436; expectancy -0.755725 R; win rate 0.183206; average winner / loser 1.413194 / -1.303105 R.
Conditional CLOSED-only DD 99.000000 R; largest winner share 0.098280; largest positive month share 1.000000. Positive / negative / zero months 1 / 9 / 2; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 22 | -24.316667 | 0.087555 | 0.081395 | 18 | 5 | 10 |
| 2023-02 | 20 | -21.000000 | 0.027027 | 0.026316 | 18 | 2 | 8 |
| 2023-03 | 8 | -8.233333 | 0.000000 | 0.000000 | 22 | 3 | 9 |
| 2023-04 | 12 | 1.916667 | 1.261364 | 1.291667 | 18 | 4 | 8 |
| 2023-05 | 8 | -2.650000 | 0.606436 | 0.640000 | 21 | 2 | 11 |
| 2023-06 | 10 | -5.416667 | 0.362745 | 0.366667 | 20 | 4 | 12 |
| 2023-07 | 10 | -11.000000 | 0.043478 | 0.048780 | 19 | 1 | 7 |
| 2023-08 | 21 | -11.566667 | 0.435313 | 0.373333 | 14 | 1 | 3 |
| 2023-09 | 19 | -15.233333 | 0.253268 | 0.253731 | 14 | 2 | 7 |
| 2023-10 | 1 | -1.500000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-11 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 6 | 0 | 0 |
| 2023-12 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N10_W2_T3_SB1_TP2

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 112, entry dates 79, entry months 9; SKIP 24, EXCLUDED 67, exclusion share 0.374302; conditional FLAT CLOSED 112.
Net -71.400000 R; PF R / price 0.316637 / 0.307910; expectancy -0.637500 R; win rate 0.196429; average winner / loser 1.503788 / -1.243849 R.
Conditional CLOSED-only DD 71.400000 R; largest winner share 0.100756; largest positive month share 1.000000. Positive / negative / zero months 1 / 8 / 3; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 17 | -14.583333 | 0.186047 | 0.178571 | 18 | 4 | 10 |
| 2023-02 | 13 | -14.016667 | 0.017523 | 0.020408 | 18 | 3 | 7 |
| 2023-03 | 8 | -12.166667 | 0.000000 | 0.000000 | 22 | 3 | 6 |
| 2023-04 | 13 | 1.000000 | 1.120000 | 1.148148 | 18 | 4 | 6 |
| 2023-05 | 9 | -4.900000 | 0.337838 | 0.333333 | 21 | 2 | 8 |
| 2023-06 | 7 | -2.083333 | 0.596774 | 0.550000 | 20 | 3 | 13 |
| 2023-07 | 6 | -5.666667 | 0.081081 | 0.086957 | 19 | 2 | 10 |
| 2023-08 | 23 | -9.816667 | 0.475979 | 0.424242 | 14 | 1 | 1 |
| 2023-09 | 16 | -9.166667 | 0.360465 | 0.354167 | 14 | 2 | 6 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 2 | 0 | 0 |
| 2023-11 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 6 | 0 | 0 |
| 2023-12 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N10_W2_T3_SB1_TP3

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 112, entry dates 79, entry months 9; SKIP 24, EXCLUDED 67, exclusion share 0.374302; conditional FLAT CLOSED 112.
Net -70.400000 R; PF R / price 0.326208 / 0.316384; expectancy -0.628571 R; win rate 0.196429; average winner / loser 1.549242 / -1.243849 R.
Conditional CLOSED-only DD 70.400000 R; largest winner share 0.146699; largest positive month share 1.000000. Positive / negative / zero months 1 / 8 / 3; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 17 | -12.916667 | 0.279070 | 0.267857 | 18 | 4 | 10 |
| 2023-02 | 13 | -14.016667 | 0.017523 | 0.020408 | 18 | 3 | 7 |
| 2023-03 | 8 | -12.166667 | 0.000000 | 0.000000 | 22 | 3 | 6 |
| 2023-04 | 13 | 0.333333 | 1.040000 | 1.074074 | 18 | 4 | 6 |
| 2023-05 | 9 | -4.900000 | 0.337838 | 0.333333 | 21 | 2 | 8 |
| 2023-06 | 7 | -2.083333 | 0.596774 | 0.550000 | 20 | 3 | 13 |
| 2023-07 | 6 | -5.666667 | 0.081081 | 0.086957 | 19 | 2 | 10 |
| 2023-08 | 23 | -9.816667 | 0.475979 | 0.424242 | 14 | 1 | 1 |
| 2023-09 | 16 | -9.166667 | 0.360465 | 0.354167 | 14 | 2 | 6 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 2 | 0 | 0 |
| 2023-11 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 6 | 0 | 0 |
| 2023-12 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N10_W2_T3_SB1_TP4

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 112, entry dates 79, entry months 9; SKIP 24, EXCLUDED 67, exclusion share 0.374302; conditional FLAT CLOSED 112.
Net -68.733333 R; PF R / price 0.342160 / 0.330508; expectancy -0.613690 R; win rate 0.196429; average winner / loser 1.625000 / -1.243849 R.
Conditional CLOSED-only DD 68.733333 R; largest winner share 0.186480; largest positive month share 1.000000. Positive / negative / zero months 1 / 8 / 3; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 17 | -11.250000 | 0.372093 | 0.357143 | 18 | 4 | 10 |
| 2023-02 | 13 | -14.016667 | 0.017523 | 0.020408 | 18 | 3 | 7 |
| 2023-03 | 8 | -12.166667 | 0.000000 | 0.000000 | 22 | 3 | 6 |
| 2023-04 | 13 | 0.333333 | 1.040000 | 1.074074 | 18 | 4 | 6 |
| 2023-05 | 9 | -4.900000 | 0.337838 | 0.333333 | 21 | 2 | 8 |
| 2023-06 | 7 | -2.083333 | 0.596774 | 0.550000 | 20 | 3 | 13 |
| 2023-07 | 6 | -5.666667 | 0.081081 | 0.086957 | 19 | 2 | 10 |
| 2023-08 | 23 | -9.816667 | 0.475979 | 0.424242 | 14 | 1 | 1 |
| 2023-09 | 16 | -9.166667 | 0.360465 | 0.354167 | 14 | 2 | 6 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 2 | 0 | 0 |
| 2023-11 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 6 | 0 | 0 |
| 2023-12 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N10_W2_T3_SB1_TP5

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 112, entry dates 79, entry months 9; SKIP 24, EXCLUDED 67, exclusion share 0.374302; conditional FLAT CLOSED 112.
Net -73.066667 R; PF R / price 0.300686 / 0.293785; expectancy -0.652381 R; win rate 0.196429; average winner / loser 1.428030 / -1.243849 R.
Conditional CLOSED-only DD 73.066667 R; largest winner share 0.106101; largest positive month share 1.000000. Positive / negative / zero months 1 / 8 / 3; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 17 | -15.583333 | 0.130233 | 0.125000 | 18 | 4 | 10 |
| 2023-02 | 13 | -14.016667 | 0.017523 | 0.020408 | 18 | 3 | 7 |
| 2023-03 | 8 | -12.166667 | 0.000000 | 0.000000 | 22 | 3 | 6 |
| 2023-04 | 13 | 0.333333 | 1.040000 | 1.074074 | 18 | 4 | 6 |
| 2023-05 | 9 | -4.900000 | 0.337838 | 0.333333 | 21 | 2 | 8 |
| 2023-06 | 7 | -2.083333 | 0.596774 | 0.550000 | 20 | 3 | 13 |
| 2023-07 | 6 | -5.666667 | 0.081081 | 0.086957 | 19 | 2 | 10 |
| 2023-08 | 23 | -9.816667 | 0.475979 | 0.424242 | 14 | 1 | 1 |
| 2023-09 | 16 | -9.166667 | 0.360465 | 0.354167 | 14 | 2 | 6 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 2 | 0 | 0 |
| 2023-11 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 6 | 0 | 0 |
| 2023-12 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N10_W2_T3_SB1_TP6

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 112, entry dates 79, entry months 9; SKIP 24, EXCLUDED 67, exclusion share 0.374302; conditional FLAT CLOSED 112.
Net -73.066667 R; PF R / price 0.300686 / 0.293785; expectancy -0.652381 R; win rate 0.196429; average winner / loser 1.428030 / -1.243849 R.
Conditional CLOSED-only DD 73.066667 R; largest winner share 0.106101; largest positive month share 1.000000. Positive / negative / zero months 1 / 8 / 3; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 17 | -15.583333 | 0.130233 | 0.125000 | 18 | 4 | 10 |
| 2023-02 | 13 | -14.016667 | 0.017523 | 0.020408 | 18 | 3 | 7 |
| 2023-03 | 8 | -12.166667 | 0.000000 | 0.000000 | 22 | 3 | 6 |
| 2023-04 | 13 | 0.333333 | 1.040000 | 1.074074 | 18 | 4 | 6 |
| 2023-05 | 9 | -4.900000 | 0.337838 | 0.333333 | 21 | 2 | 8 |
| 2023-06 | 7 | -2.083333 | 0.596774 | 0.550000 | 20 | 3 | 13 |
| 2023-07 | 6 | -5.666667 | 0.081081 | 0.086957 | 19 | 2 | 10 |
| 2023-08 | 23 | -9.816667 | 0.475979 | 0.424242 | 14 | 1 | 1 |
| 2023-09 | 16 | -9.166667 | 0.360465 | 0.354167 | 14 | 2 | 6 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 2 | 0 | 0 |
| 2023-11 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 6 | 0 | 0 |
| 2023-12 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N10_W2_T3_SB1_TP7

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 112, entry dates 79, entry months 9; SKIP 24, EXCLUDED 67, exclusion share 0.374302; conditional FLAT CLOSED 112.
Net -73.066667 R; PF R / price 0.300686 / 0.293785; expectancy -0.652381 R; win rate 0.196429; average winner / loser 1.428030 / -1.243849 R.
Conditional CLOSED-only DD 73.066667 R; largest winner share 0.106101; largest positive month share 1.000000. Positive / negative / zero months 1 / 8 / 3; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 17 | -15.583333 | 0.130233 | 0.125000 | 18 | 4 | 10 |
| 2023-02 | 13 | -14.016667 | 0.017523 | 0.020408 | 18 | 3 | 7 |
| 2023-03 | 8 | -12.166667 | 0.000000 | 0.000000 | 22 | 3 | 6 |
| 2023-04 | 13 | 0.333333 | 1.040000 | 1.074074 | 18 | 4 | 6 |
| 2023-05 | 9 | -4.900000 | 0.337838 | 0.333333 | 21 | 2 | 8 |
| 2023-06 | 7 | -2.083333 | 0.596774 | 0.550000 | 20 | 3 | 13 |
| 2023-07 | 6 | -5.666667 | 0.081081 | 0.086957 | 19 | 2 | 10 |
| 2023-08 | 23 | -9.816667 | 0.475979 | 0.424242 | 14 | 1 | 1 |
| 2023-09 | 16 | -9.166667 | 0.360465 | 0.354167 | 14 | 2 | 6 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 2 | 0 | 0 |
| 2023-11 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 6 | 0 | 0 |
| 2023-12 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N10_W2_T3_SB1_TP8

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 112, entry dates 79, entry months 9; SKIP 24, EXCLUDED 67, exclusion share 0.374302; conditional FLAT CLOSED 112.
Net -73.066667 R; PF R / price 0.300686 / 0.293785; expectancy -0.652381 R; win rate 0.196429; average winner / loser 1.428030 / -1.243849 R.
Conditional CLOSED-only DD 73.066667 R; largest winner share 0.106101; largest positive month share 1.000000. Positive / negative / zero months 1 / 8 / 3; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 17 | -15.583333 | 0.130233 | 0.125000 | 18 | 4 | 10 |
| 2023-02 | 13 | -14.016667 | 0.017523 | 0.020408 | 18 | 3 | 7 |
| 2023-03 | 8 | -12.166667 | 0.000000 | 0.000000 | 22 | 3 | 6 |
| 2023-04 | 13 | 0.333333 | 1.040000 | 1.074074 | 18 | 4 | 6 |
| 2023-05 | 9 | -4.900000 | 0.337838 | 0.333333 | 21 | 2 | 8 |
| 2023-06 | 7 | -2.083333 | 0.596774 | 0.550000 | 20 | 3 | 13 |
| 2023-07 | 6 | -5.666667 | 0.081081 | 0.086957 | 19 | 2 | 10 |
| 2023-08 | 23 | -9.816667 | 0.475979 | 0.424242 | 14 | 1 | 1 |
| 2023-09 | 16 | -9.166667 | 0.360465 | 0.354167 | 14 | 2 | 6 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 2 | 0 | 0 |
| 2023-11 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 6 | 0 | 0 |
| 2023-12 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N10_W2_T3_SB1_TP9

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 112, entry dates 79, entry months 9; SKIP 24, EXCLUDED 67, exclusion share 0.374302; conditional FLAT CLOSED 112.
Net -73.066667 R; PF R / price 0.300686 / 0.293785; expectancy -0.652381 R; win rate 0.196429; average winner / loser 1.428030 / -1.243849 R.
Conditional CLOSED-only DD 73.066667 R; largest winner share 0.106101; largest positive month share 1.000000. Positive / negative / zero months 1 / 8 / 3; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 17 | -15.583333 | 0.130233 | 0.125000 | 18 | 4 | 10 |
| 2023-02 | 13 | -14.016667 | 0.017523 | 0.020408 | 18 | 3 | 7 |
| 2023-03 | 8 | -12.166667 | 0.000000 | 0.000000 | 22 | 3 | 6 |
| 2023-04 | 13 | 0.333333 | 1.040000 | 1.074074 | 18 | 4 | 6 |
| 2023-05 | 9 | -4.900000 | 0.337838 | 0.333333 | 21 | 2 | 8 |
| 2023-06 | 7 | -2.083333 | 0.596774 | 0.550000 | 20 | 3 | 13 |
| 2023-07 | 6 | -5.666667 | 0.081081 | 0.086957 | 19 | 2 | 10 |
| 2023-08 | 23 | -9.816667 | 0.475979 | 0.424242 | 14 | 1 | 1 |
| 2023-09 | 16 | -9.166667 | 0.360465 | 0.354167 | 14 | 2 | 6 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 2 | 0 | 0 |
| 2023-11 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 6 | 0 | 0 |
| 2023-12 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N10_W2_T3_SB1_TP10

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 112, entry dates 79, entry months 9; SKIP 24, EXCLUDED 67, exclusion share 0.374302; conditional FLAT CLOSED 112.
Net -73.066667 R; PF R / price 0.300686 / 0.293785; expectancy -0.652381 R; win rate 0.196429; average winner / loser 1.428030 / -1.243849 R.
Conditional CLOSED-only DD 73.066667 R; largest winner share 0.106101; largest positive month share 1.000000. Positive / negative / zero months 1 / 8 / 3; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 17 | -15.583333 | 0.130233 | 0.125000 | 18 | 4 | 10 |
| 2023-02 | 13 | -14.016667 | 0.017523 | 0.020408 | 18 | 3 | 7 |
| 2023-03 | 8 | -12.166667 | 0.000000 | 0.000000 | 22 | 3 | 6 |
| 2023-04 | 13 | 0.333333 | 1.040000 | 1.074074 | 18 | 4 | 6 |
| 2023-05 | 9 | -4.900000 | 0.337838 | 0.333333 | 21 | 2 | 8 |
| 2023-06 | 7 | -2.083333 | 0.596774 | 0.550000 | 20 | 3 | 13 |
| 2023-07 | 6 | -5.666667 | 0.081081 | 0.086957 | 19 | 2 | 10 |
| 2023-08 | 23 | -9.816667 | 0.475979 | 0.424242 | 14 | 1 | 1 |
| 2023-09 | 16 | -9.166667 | 0.360465 | 0.354167 | 14 | 2 | 6 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 2 | 0 | 0 |
| 2023-11 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 6 | 0 | 0 |
| 2023-12 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N10_W3_T2_SB1_TP2

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 168, entry dates 95, entry months 12; SKIP 18, EXCLUDED 92, exclusion share 0.353846; conditional FLAT CLOSED 168.
Net -92.300000 R; PF R / price 0.336846 / 0.316027; expectancy -0.549405 R; win rate 0.238095; average winner / loser 1.172083 / -1.179520 R.
Conditional CLOSED-only DD 92.733333 R; largest winner share 0.071098; largest positive month share 1.000000. Positive / negative / zero months 1 / 10 / 1; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 19 | -12.333333 | 0.212766 | 0.232143 | 18 | 3 | 13 |
| 2023-02 | 21 | -16.283333 | 0.142230 | 0.200000 | 18 | 3 | 9 |
| 2023-03 | 7 | -6.900000 | 0.000000 | 0.000000 | 22 | 2 | 11 |
| 2023-04 | 17 | 4.050000 | 1.586957 | 1.440000 | 18 | 5 | 8 |
| 2023-05 | 14 | -11.216667 | 0.156642 | 0.200000 | 21 | 2 | 12 |
| 2023-06 | 14 | -9.266667 | 0.214689 | 0.250000 | 20 | 0 | 16 |
| 2023-07 | 17 | -11.266667 | 0.183575 | 0.169811 | 19 | 2 | 12 |
| 2023-08 | 34 | -16.533333 | 0.470085 | 0.403509 | 14 | 1 | 4 |
| 2023-09 | 22 | -9.650000 | 0.455827 | 0.288136 | 14 | 0 | 7 |
| 2023-10 | 1 | -1.500000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-11 | 1 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 6 | 0 | 0 |
| 2023-12 | 1 | -1.400000 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N10_W3_T2_SB1_TP3

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 168, entry dates 95, entry months 12; SKIP 18, EXCLUDED 92, exclusion share 0.353846; conditional FLAT CLOSED 168.
Net -85.466667 R; PF R / price 0.385942 / 0.351939; expectancy -0.508730 R; win rate 0.238095; average winner / loser 1.342917 / -1.179520 R.
Conditional CLOSED-only DD 87.566667 R; largest winner share 0.093081; largest positive month share 1.000000. Positive / negative / zero months 1 / 10 / 1; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 19 | -10.833333 | 0.308511 | 0.339286 | 18 | 3 | 13 |
| 2023-02 | 21 | -16.283333 | 0.142230 | 0.200000 | 18 | 3 | 9 |
| 2023-03 | 7 | -6.900000 | 0.000000 | 0.000000 | 22 | 2 | 11 |
| 2023-04 | 17 | 5.716667 | 1.828502 | 1.640000 | 18 | 5 | 8 |
| 2023-05 | 14 | -11.216667 | 0.156642 | 0.200000 | 21 | 2 | 12 |
| 2023-06 | 14 | -9.266667 | 0.214689 | 0.250000 | 20 | 0 | 16 |
| 2023-07 | 17 | -11.266667 | 0.183575 | 0.169811 | 19 | 2 | 12 |
| 2023-08 | 34 | -14.533333 | 0.534188 | 0.456140 | 14 | 1 | 4 |
| 2023-09 | 22 | -7.983333 | 0.549812 | 0.296610 | 14 | 0 | 7 |
| 2023-10 | 1 | -1.500000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-11 | 1 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 6 | 0 | 0 |
| 2023-12 | 1 | -1.400000 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N10_W3_T2_SB1_TP4

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 168, entry dates 95, entry months 12; SKIP 18, EXCLUDED 92, exclusion share 0.353846; conditional FLAT CLOSED 168.
Net -84.633333 R; PF R / price 0.391929 / 0.342705; expectancy -0.503770 R; win rate 0.238095; average winner / loser 1.363750 / -1.179520 R.
Conditional CLOSED-only DD 88.400000 R; largest winner share 0.122212; largest positive month share 1.000000. Positive / negative / zero months 1 / 10 / 1; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 19 | -13.333333 | 0.148936 | 0.160714 | 18 | 3 | 13 |
| 2023-02 | 21 | -16.283333 | 0.142230 | 0.200000 | 18 | 3 | 9 |
| 2023-03 | 7 | -6.900000 | 0.000000 | 0.000000 | 22 | 2 | 11 |
| 2023-04 | 17 | 5.716667 | 1.828502 | 1.640000 | 18 | 5 | 8 |
| 2023-05 | 14 | -11.216667 | 0.156642 | 0.200000 | 21 | 2 | 12 |
| 2023-06 | 14 | -9.266667 | 0.214689 | 0.250000 | 20 | 0 | 16 |
| 2023-07 | 17 | -11.266667 | 0.183575 | 0.169811 | 19 | 2 | 12 |
| 2023-08 | 34 | -12.866667 | 0.587607 | 0.500000 | 14 | 1 | 4 |
| 2023-09 | 22 | -6.316667 | 0.643797 | 0.305085 | 14 | 0 | 7 |
| 2023-10 | 1 | -1.500000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-11 | 1 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 6 | 0 | 0 |
| 2023-12 | 1 | -1.400000 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N10_W3_T2_SB1_TP5

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 168, entry dates 95, entry months 12; SKIP 18, EXCLUDED 92, exclusion share 0.353846; conditional FLAT CLOSED 168.
Net -81.300000 R; PF R / price 0.415878 / 0.353991; expectancy -0.483929 R; win rate 0.238095; average winner / loser 1.447083 / -1.179520 R.
Conditional CLOSED-only DD 86.733333 R; largest winner share 0.143968; largest positive month share 1.000000. Positive / negative / zero months 1 / 10 / 1; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 19 | -13.333333 | 0.148936 | 0.160714 | 18 | 3 | 13 |
| 2023-02 | 21 | -16.283333 | 0.142230 | 0.200000 | 18 | 3 | 9 |
| 2023-03 | 7 | -6.900000 | 0.000000 | 0.000000 | 22 | 2 | 11 |
| 2023-04 | 17 | 5.716667 | 1.828502 | 1.640000 | 18 | 5 | 8 |
| 2023-05 | 14 | -11.216667 | 0.156642 | 0.200000 | 21 | 2 | 12 |
| 2023-06 | 14 | -9.266667 | 0.214689 | 0.250000 | 20 | 0 | 16 |
| 2023-07 | 17 | -11.266667 | 0.183575 | 0.169811 | 19 | 2 | 12 |
| 2023-08 | 34 | -11.200000 | 0.641026 | 0.543860 | 14 | 1 | 4 |
| 2023-09 | 22 | -4.650000 | 0.737782 | 0.313559 | 14 | 0 | 7 |
| 2023-10 | 1 | -1.500000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-11 | 1 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 6 | 0 | 0 |
| 2023-12 | 1 | -1.400000 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N10_W3_T2_SB1_TP6

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 168, entry dates 95, entry months 12; SKIP 18, EXCLUDED 92, exclusion share 0.353846; conditional FLAT CLOSED 168.
Net -77.966667 R; PF R / price 0.439828 / 0.365278; expectancy -0.464087 R; win rate 0.238095; average winner / loser 1.530417 / -1.179520 R.
Conditional CLOSED-only DD 85.066667 R; largest winner share 0.163354; largest positive month share 1.000000. Positive / negative / zero months 1 / 10 / 1; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 19 | -13.333333 | 0.148936 | 0.160714 | 18 | 3 | 13 |
| 2023-02 | 21 | -16.283333 | 0.142230 | 0.200000 | 18 | 3 | 9 |
| 2023-03 | 7 | -6.900000 | 0.000000 | 0.000000 | 22 | 2 | 11 |
| 2023-04 | 17 | 5.716667 | 1.828502 | 1.640000 | 18 | 5 | 8 |
| 2023-05 | 14 | -11.216667 | 0.156642 | 0.200000 | 21 | 2 | 12 |
| 2023-06 | 14 | -9.266667 | 0.214689 | 0.250000 | 20 | 0 | 16 |
| 2023-07 | 17 | -11.266667 | 0.183575 | 0.169811 | 19 | 2 | 12 |
| 2023-08 | 34 | -9.533333 | 0.694444 | 0.587719 | 14 | 1 | 4 |
| 2023-09 | 22 | -2.983333 | 0.831767 | 0.322034 | 14 | 0 | 7 |
| 2023-10 | 1 | -1.500000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-11 | 1 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 6 | 0 | 0 |
| 2023-12 | 1 | -1.400000 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N10_W3_T2_SB1_TP7

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 168, entry dates 95, entry months 12; SKIP 18, EXCLUDED 92, exclusion share 0.353846; conditional FLAT CLOSED 168.
Net -74.633333 R; PF R / price 0.463777 / 0.376565; expectancy -0.444246 R; win rate 0.238095; average winner / loser 1.613750 / -1.179520 R.
Conditional CLOSED-only DD 83.400000 R; largest winner share 0.180738; largest positive month share 1.000000. Positive / negative / zero months 1 / 10 / 1; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 19 | -13.333333 | 0.148936 | 0.160714 | 18 | 3 | 13 |
| 2023-02 | 21 | -16.283333 | 0.142230 | 0.200000 | 18 | 3 | 9 |
| 2023-03 | 7 | -6.900000 | 0.000000 | 0.000000 | 22 | 2 | 11 |
| 2023-04 | 17 | 5.716667 | 1.828502 | 1.640000 | 18 | 5 | 8 |
| 2023-05 | 14 | -11.216667 | 0.156642 | 0.200000 | 21 | 2 | 12 |
| 2023-06 | 14 | -9.266667 | 0.214689 | 0.250000 | 20 | 0 | 16 |
| 2023-07 | 17 | -11.266667 | 0.183575 | 0.169811 | 19 | 2 | 12 |
| 2023-08 | 34 | -7.866667 | 0.747863 | 0.631579 | 14 | 1 | 4 |
| 2023-09 | 22 | -1.316667 | 0.925752 | 0.330508 | 14 | 0 | 7 |
| 2023-10 | 1 | -1.500000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-11 | 1 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 6 | 0 | 0 |
| 2023-12 | 1 | -1.400000 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N10_W3_T2_SB1_TP8

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 168, entry dates 95, entry months 12; SKIP 18, EXCLUDED 92, exclusion share 0.353846; conditional FLAT CLOSED 168.
Net -71.300000 R; PF R / price 0.487726 / 0.387851; expectancy -0.424405 R; win rate 0.238095; average winner / loser 1.697083 / -1.179520 R.
Conditional CLOSED-only DD 81.733333 R; largest winner share 0.196415; largest positive month share 0.942308. Positive / negative / zero months 2 / 9 / 1; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 19 | -13.333333 | 0.148936 | 0.160714 | 18 | 3 | 13 |
| 2023-02 | 21 | -16.283333 | 0.142230 | 0.200000 | 18 | 3 | 9 |
| 2023-03 | 7 | -6.900000 | 0.000000 | 0.000000 | 22 | 2 | 11 |
| 2023-04 | 17 | 5.716667 | 1.828502 | 1.640000 | 18 | 5 | 8 |
| 2023-05 | 14 | -11.216667 | 0.156642 | 0.200000 | 21 | 2 | 12 |
| 2023-06 | 14 | -9.266667 | 0.214689 | 0.250000 | 20 | 0 | 16 |
| 2023-07 | 17 | -11.266667 | 0.183575 | 0.169811 | 19 | 2 | 12 |
| 2023-08 | 34 | -6.200000 | 0.801282 | 0.675439 | 14 | 1 | 4 |
| 2023-09 | 22 | 0.350000 | 1.019737 | 0.338983 | 14 | 0 | 7 |
| 2023-10 | 1 | -1.500000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-11 | 1 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 6 | 0 | 0 |
| 2023-12 | 1 | -1.400000 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N10_W3_T2_SB1_TP9

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 168, entry dates 95, entry months 12; SKIP 18, EXCLUDED 92, exclusion share 0.353846; conditional FLAT CLOSED 168.
Net -67.966667 R; PF R / price 0.511675 / 0.399138; expectancy -0.404563 R; win rate 0.238095; average winner / loser 1.780417 / -1.179520 R.
Conditional CLOSED-only DD 80.066667 R; largest winner share 0.210625; largest positive month share 0.739224. Positive / negative / zero months 2 / 9 / 1; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 19 | -13.333333 | 0.148936 | 0.160714 | 18 | 3 | 13 |
| 2023-02 | 21 | -16.283333 | 0.142230 | 0.200000 | 18 | 3 | 9 |
| 2023-03 | 7 | -6.900000 | 0.000000 | 0.000000 | 22 | 2 | 11 |
| 2023-04 | 17 | 5.716667 | 1.828502 | 1.640000 | 18 | 5 | 8 |
| 2023-05 | 14 | -11.216667 | 0.156642 | 0.200000 | 21 | 2 | 12 |
| 2023-06 | 14 | -9.266667 | 0.214689 | 0.250000 | 20 | 0 | 16 |
| 2023-07 | 17 | -11.266667 | 0.183575 | 0.169811 | 19 | 2 | 12 |
| 2023-08 | 34 | -4.533333 | 0.854701 | 0.719298 | 14 | 1 | 4 |
| 2023-09 | 22 | 2.016667 | 1.113722 | 0.347458 | 14 | 0 | 7 |
| 2023-10 | 1 | -1.500000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-11 | 1 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 6 | 0 | 0 |
| 2023-12 | 1 | -1.400000 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N10_W3_T2_SB1_TP10

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 168, entry dates 95, entry months 12; SKIP 18, EXCLUDED 92, exclusion share 0.353846; conditional FLAT CLOSED 168.
Net -64.633333 R; PF R / price 0.535624 / 0.410425; expectancy -0.384722 R; win rate 0.238095; average winner / loser 1.863750 / -1.179520 R.
Conditional CLOSED-only DD 78.400000 R; largest winner share 0.223564; largest positive month share 0.608156. Positive / negative / zero months 2 / 9 / 1; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 19 | -13.333333 | 0.148936 | 0.160714 | 18 | 3 | 13 |
| 2023-02 | 21 | -16.283333 | 0.142230 | 0.200000 | 18 | 3 | 9 |
| 2023-03 | 7 | -6.900000 | 0.000000 | 0.000000 | 22 | 2 | 11 |
| 2023-04 | 17 | 5.716667 | 1.828502 | 1.640000 | 18 | 5 | 8 |
| 2023-05 | 14 | -11.216667 | 0.156642 | 0.200000 | 21 | 2 | 12 |
| 2023-06 | 14 | -9.266667 | 0.214689 | 0.250000 | 20 | 0 | 16 |
| 2023-07 | 17 | -11.266667 | 0.183575 | 0.169811 | 19 | 2 | 12 |
| 2023-08 | 34 | -2.866667 | 0.908120 | 0.763158 | 14 | 1 | 4 |
| 2023-09 | 22 | 3.683333 | 1.207707 | 0.355932 | 14 | 0 | 7 |
| 2023-10 | 1 | -1.500000 | 0.000000 | 0.000000 | 2 | 0 | 0 |
| 2023-11 | 1 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 6 | 0 | 0 |
| 2023-12 | 1 | -1.400000 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N10_W3_T3_SB1_TP2

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 147, entry dates 91, entry months 9; SKIP 18, EXCLUDED 82, exclusion share 0.358079; conditional FLAT CLOSED 147.
Net -67.616667 R; PF R / price 0.386047 / 0.348052; expectancy -0.459977 R; win rate 0.231293; average winner / loser 1.250490 / -1.101333 R.
Conditional CLOSED-only DD 70.950000 R; largest winner share 0.078401; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 9 / 3; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 17 | -14.983333 | 0.021763 | 0.018868 | 18 | 2 | 12 |
| 2023-02 | 15 | -9.550000 | 0.209655 | 0.292683 | 18 | 3 | 11 |
| 2023-03 | 11 | -13.500000 | 0.000000 | 0.000000 | 22 | 3 | 9 |
| 2023-04 | 18 | -0.266667 | 0.976744 | 0.857143 | 18 | 4 | 5 |
| 2023-05 | 16 | -5.900000 | 0.497159 | 0.552632 | 21 | 3 | 8 |
| 2023-06 | 12 | -7.983333 | 0.040080 | 0.031250 | 20 | 2 | 14 |
| 2023-07 | 13 | -5.033333 | 0.304147 | 0.296296 | 19 | 0 | 12 |
| 2023-08 | 29 | -9.900000 | 0.533752 | 0.480000 | 14 | 1 | 3 |
| 2023-09 | 16 | -0.500000 | 0.945946 | 0.633333 | 14 | 0 | 8 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 2 | 0 | 0 |
| 2023-11 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 6 | 0 | 0 |
| 2023-12 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N10_W3_T3_SB1_TP3

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 147, entry dates 91, entry months 9; SKIP 18, EXCLUDED 82, exclusion share 0.358079; conditional FLAT CLOSED 147.
Net -63.950000 R; PF R / price 0.419340 / 0.364935; expectancy -0.435034 R; win rate 0.231293; average winner / loser 1.358333 / -1.101333 R.
Conditional CLOSED-only DD 68.950000 R; largest winner share 0.108264; largest positive month share 0.545455. Positive / negative / zero months 2 / 7 / 3; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 17 | -14.983333 | 0.021763 | 0.018868 | 18 | 2 | 12 |
| 2023-02 | 15 | -9.550000 | 0.209655 | 0.292683 | 18 | 3 | 11 |
| 2023-03 | 11 | -13.500000 | 0.000000 | 0.000000 | 22 | 3 | 9 |
| 2023-04 | 18 | 1.400000 | 1.122093 | 0.976190 | 18 | 4 | 5 |
| 2023-05 | 16 | -5.900000 | 0.497159 | 0.552632 | 21 | 3 | 8 |
| 2023-06 | 12 | -7.983333 | 0.040080 | 0.031250 | 20 | 2 | 14 |
| 2023-07 | 13 | -5.033333 | 0.304147 | 0.296296 | 19 | 0 | 12 |
| 2023-08 | 29 | -9.566667 | 0.549451 | 0.493333 | 14 | 1 | 3 |
| 2023-09 | 16 | 1.166667 | 1.126126 | 0.650000 | 14 | 0 | 8 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 2 | 0 | 0 |
| 2023-11 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 6 | 0 | 0 |
| 2023-12 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N10_W3_T3_SB1_TP4

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 147, entry dates 91, entry months 9; SKIP 18, EXCLUDED 82, exclusion share 0.358079; conditional FLAT CLOSED 147.
Net -62.283333 R; PF R / price 0.434473 / 0.366234; expectancy -0.423696 R; win rate 0.231293; average winner / loser 1.407353 / -1.101333 R.
Conditional CLOSED-only DD 68.950000 R; largest winner share 0.139324; largest positive month share 0.669291. Positive / negative / zero months 2 / 7 / 3; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 17 | -14.983333 | 0.021763 | 0.018868 | 18 | 2 | 12 |
| 2023-02 | 15 | -9.550000 | 0.209655 | 0.292683 | 18 | 3 | 11 |
| 2023-03 | 11 | -13.500000 | 0.000000 | 0.000000 | 22 | 3 | 9 |
| 2023-04 | 18 | 1.400000 | 1.122093 | 0.976190 | 18 | 4 | 5 |
| 2023-05 | 16 | -5.900000 | 0.497159 | 0.552632 | 21 | 3 | 8 |
| 2023-06 | 12 | -7.983333 | 0.040080 | 0.031250 | 20 | 2 | 14 |
| 2023-07 | 13 | -5.033333 | 0.304147 | 0.296296 | 19 | 0 | 12 |
| 2023-08 | 29 | -9.566667 | 0.549451 | 0.493333 | 14 | 1 | 3 |
| 2023-09 | 16 | 2.833333 | 1.306306 | 0.666667 | 14 | 0 | 8 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 2 | 0 | 0 |
| 2023-11 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 6 | 0 | 0 |
| 2023-12 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N10_W3_T3_SB1_TP5

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 147, entry dates 91, entry months 9; SKIP 18, EXCLUDED 82, exclusion share 0.358079; conditional FLAT CLOSED 147.
Net -60.616667 R; PF R / price 0.449607 / 0.367532; expectancy -0.412358 R; win rate 0.231293; average winner / loser 1.456373 / -1.101333 R.
Conditional CLOSED-only DD 68.950000 R; largest winner share 0.168294; largest positive month share 0.762712. Positive / negative / zero months 2 / 7 / 3; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 17 | -14.983333 | 0.021763 | 0.018868 | 18 | 2 | 12 |
| 2023-02 | 15 | -9.550000 | 0.209655 | 0.292683 | 18 | 3 | 11 |
| 2023-03 | 11 | -13.500000 | 0.000000 | 0.000000 | 22 | 3 | 9 |
| 2023-04 | 18 | 1.400000 | 1.122093 | 0.976190 | 18 | 4 | 5 |
| 2023-05 | 16 | -5.900000 | 0.497159 | 0.552632 | 21 | 3 | 8 |
| 2023-06 | 12 | -7.983333 | 0.040080 | 0.031250 | 20 | 2 | 14 |
| 2023-07 | 13 | -5.033333 | 0.304147 | 0.296296 | 19 | 0 | 12 |
| 2023-08 | 29 | -9.566667 | 0.549451 | 0.493333 | 14 | 1 | 3 |
| 2023-09 | 16 | 4.500000 | 1.486486 | 0.683333 | 14 | 0 | 8 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 2 | 0 | 0 |
| 2023-11 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 6 | 0 | 0 |
| 2023-12 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N10_W3_T3_SB1_TP6

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 147, entry dates 91, entry months 9; SKIP 18, EXCLUDED 82, exclusion share 0.358079; conditional FLAT CLOSED 147.
Net -58.950000 R; PF R / price 0.464740 / 0.368831; expectancy -0.401020 R; win rate 0.231293; average winner / loser 1.505392 / -1.101333 R.
Conditional CLOSED-only DD 68.950000 R; largest winner share 0.195376; largest positive month share 0.814978. Positive / negative / zero months 2 / 7 / 3; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 17 | -14.983333 | 0.021763 | 0.018868 | 18 | 2 | 12 |
| 2023-02 | 15 | -9.550000 | 0.209655 | 0.292683 | 18 | 3 | 11 |
| 2023-03 | 11 | -13.500000 | 0.000000 | 0.000000 | 22 | 3 | 9 |
| 2023-04 | 18 | 1.400000 | 1.122093 | 0.976190 | 18 | 4 | 5 |
| 2023-05 | 16 | -5.900000 | 0.497159 | 0.552632 | 21 | 3 | 8 |
| 2023-06 | 12 | -7.983333 | 0.040080 | 0.031250 | 20 | 2 | 14 |
| 2023-07 | 13 | -5.033333 | 0.304147 | 0.296296 | 19 | 0 | 12 |
| 2023-08 | 29 | -9.566667 | 0.549451 | 0.493333 | 14 | 1 | 3 |
| 2023-09 | 16 | 6.166667 | 1.666667 | 0.700000 | 14 | 0 | 8 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 2 | 0 | 0 |
| 2023-11 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 6 | 0 | 0 |
| 2023-12 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N10_W3_T3_SB1_TP7

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 147, entry dates 91, entry months 9; SKIP 18, EXCLUDED 82, exclusion share 0.358079; conditional FLAT CLOSED 147.
Net -57.283333 R; PF R / price 0.479873 / 0.370130; expectancy -0.389683 R; win rate 0.231293; average winner / loser 1.554412 / -1.101333 R.
Conditional CLOSED-only DD 68.950000 R; largest winner share 0.220751; largest positive month share 0.848375. Positive / negative / zero months 2 / 7 / 3; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 17 | -14.983333 | 0.021763 | 0.018868 | 18 | 2 | 12 |
| 2023-02 | 15 | -9.550000 | 0.209655 | 0.292683 | 18 | 3 | 11 |
| 2023-03 | 11 | -13.500000 | 0.000000 | 0.000000 | 22 | 3 | 9 |
| 2023-04 | 18 | 1.400000 | 1.122093 | 0.976190 | 18 | 4 | 5 |
| 2023-05 | 16 | -5.900000 | 0.497159 | 0.552632 | 21 | 3 | 8 |
| 2023-06 | 12 | -7.983333 | 0.040080 | 0.031250 | 20 | 2 | 14 |
| 2023-07 | 13 | -5.033333 | 0.304147 | 0.296296 | 19 | 0 | 12 |
| 2023-08 | 29 | -9.566667 | 0.549451 | 0.493333 | 14 | 1 | 3 |
| 2023-09 | 16 | 7.833333 | 1.846847 | 0.716667 | 14 | 0 | 8 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 2 | 0 | 0 |
| 2023-11 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 6 | 0 | 0 |
| 2023-12 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N10_W3_T3_SB1_TP8

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 147, entry dates 91, entry months 9; SKIP 18, EXCLUDED 82, exclusion share 0.358079; conditional FLAT CLOSED 147.
Net -55.616667 R; PF R / price 0.495006 / 0.371429; expectancy -0.378345 R; win rate 0.231293; average winner / loser 1.603431 / -1.101333 R.
Conditional CLOSED-only DD 68.950000 R; largest winner share 0.244574; largest positive month share 0.871560. Positive / negative / zero months 2 / 7 / 3; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 17 | -14.983333 | 0.021763 | 0.018868 | 18 | 2 | 12 |
| 2023-02 | 15 | -9.550000 | 0.209655 | 0.292683 | 18 | 3 | 11 |
| 2023-03 | 11 | -13.500000 | 0.000000 | 0.000000 | 22 | 3 | 9 |
| 2023-04 | 18 | 1.400000 | 1.122093 | 0.976190 | 18 | 4 | 5 |
| 2023-05 | 16 | -5.900000 | 0.497159 | 0.552632 | 21 | 3 | 8 |
| 2023-06 | 12 | -7.983333 | 0.040080 | 0.031250 | 20 | 2 | 14 |
| 2023-07 | 13 | -5.033333 | 0.304147 | 0.296296 | 19 | 0 | 12 |
| 2023-08 | 29 | -9.566667 | 0.549451 | 0.493333 | 14 | 1 | 3 |
| 2023-09 | 16 | 9.500000 | 2.027027 | 0.733333 | 14 | 0 | 8 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 2 | 0 | 0 |
| 2023-11 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 6 | 0 | 0 |
| 2023-12 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N10_W3_T3_SB1_TP9

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors.
CLOSED 147, entry dates 91, entry months 9; SKIP 18, EXCLUDED 82, exclusion share 0.358079; conditional FLAT CLOSED 147.
Net -53.950000 R; PF R / price 0.510139 / 0.372727; expectancy -0.367007 R; win rate 0.231293; average winner / loser 1.652451 / -1.101333 R.
Conditional CLOSED-only DD 68.950000 R; largest winner share 0.266983; largest positive month share 0.888594. Positive / negative / zero months 2 / 7 / 3; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 17 | -14.983333 | 0.021763 | 0.018868 | 18 | 2 | 12 |
| 2023-02 | 15 | -9.550000 | 0.209655 | 0.292683 | 18 | 3 | 11 |
| 2023-03 | 11 | -13.500000 | 0.000000 | 0.000000 | 22 | 3 | 9 |
| 2023-04 | 18 | 1.400000 | 1.122093 | 0.976190 | 18 | 4 | 5 |
| 2023-05 | 16 | -5.900000 | 0.497159 | 0.552632 | 21 | 3 | 8 |
| 2023-06 | 12 | -7.983333 | 0.040080 | 0.031250 | 20 | 2 | 14 |
| 2023-07 | 13 | -5.033333 | 0.304147 | 0.296296 | 19 | 0 | 12 |
| 2023-08 | 29 | -9.566667 | 0.549451 | 0.493333 | 14 | 1 | 3 |
| 2023-09 | 16 | 11.166667 | 2.207207 | 0.750000 | 14 | 0 | 8 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 2 | 0 | 0 |
| 2023-11 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 6 | 0 | 0 |
| 2023-12 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N10_W3_T3_SB1_TP10

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|trade_concentration|month_concentration|neighbors.
CLOSED 147, entry dates 91, entry months 9; SKIP 18, EXCLUDED 82, exclusion share 0.358079; conditional FLAT CLOSED 147.
Net -52.283333 R; PF R / price 0.525272 / 0.374026; expectancy -0.355669 R; win rate 0.231293; average winner / loser 1.701471 / -1.101333 R.
Conditional CLOSED-only DD 68.950000 R; largest winner share 0.288101; largest positive month share 0.901639. Positive / negative / zero months 2 / 7 / 3; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 17 | -14.983333 | 0.021763 | 0.018868 | 18 | 2 | 12 |
| 2023-02 | 15 | -9.550000 | 0.209655 | 0.292683 | 18 | 3 | 11 |
| 2023-03 | 11 | -13.500000 | 0.000000 | 0.000000 | 22 | 3 | 9 |
| 2023-04 | 18 | 1.400000 | 1.122093 | 0.976190 | 18 | 4 | 5 |
| 2023-05 | 16 | -5.900000 | 0.497159 | 0.552632 | 21 | 3 | 8 |
| 2023-06 | 12 | -7.983333 | 0.040080 | 0.031250 | 20 | 2 | 14 |
| 2023-07 | 13 | -5.033333 | 0.304147 | 0.296296 | 19 | 0 | 12 |
| 2023-08 | 29 | -9.566667 | 0.549451 | 0.493333 | 14 | 1 | 3 |
| 2023-09 | 16 | 12.833333 | 2.387387 | 0.766667 | 14 | 0 | 8 |
| 2023-10 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 2 | 0 | 0 |
| 2023-11 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 6 | 0 | 0 |
| 2023-12 | 0 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 0 | 0 | 0 |

### B_OPT2023_N4_W3_T2_SB2_TP2

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 380, entry dates 159, entry months 12; SKIP 11, EXCLUDED 146, exclusion share 0.277567; conditional FLAT CLOSED 379.
Net -188.700000 R; PF R / price 0.427604 / 0.374811; expectancy -0.496579 R; win rate 0.252632; average winner / loser 1.468403 / -1.239348 R.
Conditional CLOSED-only DD 193.633333 R; largest winner share 0.023646; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 12 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 29 | -19.950000 | 0.200401 | 0.165049 | 18 | 0 | 17 |
| 2023-02 | 23 | -9.266667 | 0.350467 | 0.310345 | 18 | 3 | 16 |
| 2023-03 | 17 | -19.400000 | 0.049020 | 0.051948 | 22 | 2 | 19 |
| 2023-04 | 24 | -13.700000 | 0.316708 | 0.342466 | 18 | 0 | 17 |
| 2023-05 | 30 | -12.100000 | 0.481058 | 0.575000 | 21 | 2 | 18 |
| 2023-06 | 28 | -14.733333 | 0.410274 | 0.351648 | 20 | 1 | 18 |
| 2023-07 | 32 | -7.500000 | 0.596413 | 0.676923 | 19 | 1 | 16 |
| 2023-08 | 58 | -19.600000 | 0.513446 | 0.493671 | 14 | 1 | 10 |
| 2023-09 | 37 | -22.016667 | 0.334844 | 0.303774 | 14 | 0 | 12 |
| 2023-10 | 28 | -10.833333 | 0.610778 | 0.675439 | 2 | 0 | 2 |
| 2023-11 | 44 | -20.866667 | 0.563763 | 0.570048 | 6 | 1 | 1 |
| 2023-12 | 30 | -18.733333 | 0.450098 | 0.394737 | 0 | 0 | 0 |

### B_OPT2023_N4_W3_T2_SB2_TP3

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 377, entry dates 159, entry months 12; SKIP 11, EXCLUDED 146, exclusion share 0.279159; conditional FLAT CLOSED 376.
Net -171.133333 R; PF R / price 0.479732 / 0.382904; expectancy -0.453935 R; win rate 0.251989; average winner / loser 1.661053 / -1.245960 R.
Conditional CLOSED-only DD 179.233333 R; largest winner share 0.031686; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 12 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 29 | -19.616667 | 0.213761 | 0.174757 | 18 | 0 | 17 |
| 2023-02 | 23 | -9.266667 | 0.350467 | 0.310345 | 18 | 3 | 16 |
| 2023-03 | 17 | -19.400000 | 0.049020 | 0.051948 | 22 | 2 | 19 |
| 2023-04 | 24 | -13.700000 | 0.316708 | 0.342466 | 18 | 0 | 17 |
| 2023-05 | 30 | -12.100000 | 0.481058 | 0.575000 | 21 | 2 | 18 |
| 2023-06 | 27 | -13.666667 | 0.413867 | 0.360465 | 20 | 1 | 18 |
| 2023-07 | 32 | -6.000000 | 0.677130 | 0.769231 | 19 | 1 | 16 |
| 2023-08 | 58 | -23.133333 | 0.437829 | 0.433962 | 14 | 1 | 10 |
| 2023-09 | 37 | -20.516667 | 0.380161 | 0.309434 | 14 | 0 | 12 |
| 2023-10 | 27 | -6.966667 | 0.747889 | 0.840708 | 2 | 0 | 2 |
| 2023-11 | 43 | -9.033333 | 0.805456 | 0.810000 | 6 | 1 | 1 |
| 2023-12 | 30 | -17.733333 | 0.503731 | 0.477707 | 0 | 0 | 0 |

### B_OPT2023_N4_W3_T2_SB2_TP4

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 377, entry dates 159, entry months 12; SKIP 11, EXCLUDED 146, exclusion share 0.279159; conditional FLAT CLOSED 376.
Net -158.450000 R; PF R / price 0.520720 / 0.391808; expectancy -0.420292 R; win rate 0.249337; average winner / loser 1.831383 / -1.247547 R.
Conditional CLOSED-only DD 169.716667 R; largest winner share 0.038726; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 12 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 29 | -19.616667 | 0.213761 | 0.174757 | 18 | 0 | 17 |
| 2023-02 | 23 | -9.266667 | 0.350467 | 0.310345 | 18 | 3 | 16 |
| 2023-03 | 17 | -19.400000 | 0.049020 | 0.051948 | 22 | 2 | 19 |
| 2023-04 | 24 | -13.700000 | 0.316708 | 0.342466 | 18 | 0 | 17 |
| 2023-05 | 30 | -12.100000 | 0.481058 | 0.575000 | 21 | 2 | 18 |
| 2023-06 | 27 | -13.666667 | 0.413867 | 0.360465 | 20 | 1 | 18 |
| 2023-07 | 32 | -5.750000 | 0.690583 | 0.784615 | 19 | 1 | 16 |
| 2023-08 | 58 | -23.133333 | 0.437829 | 0.433962 | 14 | 1 | 10 |
| 2023-09 | 37 | -19.016667 | 0.425478 | 0.315094 | 14 | 0 | 12 |
| 2023-10 | 27 | -4.133333 | 0.850422 | 0.955752 | 2 | 0 | 2 |
| 2023-11 | 43 | -6.933333 | 0.855856 | 0.907317 | 6 | 1 | 1 |
| 2023-12 | 30 | -11.733333 | 0.671642 | 0.636943 | 0 | 0 | 0 |

### B_OPT2023_N4_W3_T2_SB2_TP5

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 376, entry dates 159, entry months 12; SKIP 11, EXCLUDED 146, exclusion share 0.279693; conditional FLAT CLOSED 375.
Net -168.616667 R; PF R / price 0.492271 / 0.387557; expectancy -0.448449 R; win rate 0.244681; average winner / loser 1.776993 / -1.248496 R.
Conditional CLOSED-only DD 172.050000 R; largest winner share 0.045876; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 12 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 29 | -19.616667 | 0.213761 | 0.174757 | 18 | 0 | 17 |
| 2023-02 | 23 | -9.266667 | 0.350467 | 0.310345 | 18 | 3 | 16 |
| 2023-03 | 17 | -19.400000 | 0.049020 | 0.051948 | 22 | 2 | 19 |
| 2023-04 | 24 | -13.700000 | 0.316708 | 0.342466 | 18 | 0 | 17 |
| 2023-05 | 30 | -12.100000 | 0.481058 | 0.575000 | 21 | 2 | 18 |
| 2023-06 | 27 | -13.666667 | 0.413867 | 0.360465 | 20 | 1 | 18 |
| 2023-07 | 32 | -5.750000 | 0.690583 | 0.784615 | 19 | 1 | 16 |
| 2023-08 | 58 | -23.133333 | 0.437829 | 0.433962 | 14 | 1 | 10 |
| 2023-09 | 37 | -17.516667 | 0.470796 | 0.320755 | 14 | 0 | 12 |
| 2023-10 | 27 | -2.633333 | 0.904704 | 1.008850 | 2 | 0 | 2 |
| 2023-11 | 42 | -15.100000 | 0.686071 | 0.736585 | 6 | 1 | 1 |
| 2023-12 | 30 | -16.733333 | 0.550582 | 0.546012 | 0 | 0 | 0 |

### B_OPT2023_N4_W3_T2_SB2_TP6

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 376, entry dates 159, entry months 12; SKIP 11, EXCLUDED 146, exclusion share 0.279693; conditional FLAT CLOSED 375.
Net -180.333333 R; PF R / price 0.459432 / 0.382611; expectancy -0.479610 R; win rate 0.242021; average winner / loser 1.684249 / -1.249438 R.
Conditional CLOSED-only DD 183.766667 R; largest winner share 0.058721; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 12 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 29 | -19.616667 | 0.213761 | 0.174757 | 18 | 0 | 17 |
| 2023-02 | 23 | -9.266667 | 0.350467 | 0.310345 | 18 | 3 | 16 |
| 2023-03 | 17 | -19.400000 | 0.049020 | 0.051948 | 22 | 2 | 19 |
| 2023-04 | 24 | -13.700000 | 0.316708 | 0.342466 | 18 | 0 | 17 |
| 2023-05 | 30 | -12.100000 | 0.481058 | 0.575000 | 21 | 2 | 18 |
| 2023-06 | 27 | -13.666667 | 0.413867 | 0.360465 | 20 | 1 | 18 |
| 2023-07 | 32 | -5.750000 | 0.690583 | 0.784615 | 19 | 1 | 16 |
| 2023-08 | 58 | -23.133333 | 0.437829 | 0.433962 | 14 | 1 | 10 |
| 2023-09 | 37 | -22.766667 | 0.312185 | 0.300943 | 14 | 0 | 12 |
| 2023-10 | 27 | -11.633333 | 0.600686 | 0.705882 | 2 | 0 | 2 |
| 2023-11 | 42 | -15.400000 | 0.679834 | 0.721951 | 6 | 1 | 1 |
| 2023-12 | 30 | -13.900000 | 0.626679 | 0.631902 | 0 | 0 | 0 |

### B_OPT2023_N4_W3_T2_SB2_TP7

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 376, entry dates 159, entry months 12; SKIP 11, EXCLUDED 146, exclusion share 0.279693; conditional FLAT CLOSED 375.
Net -187.800000 R; PF R / price 0.439403 / 0.378795; expectancy -0.499468 R; win rate 0.239362; average winner / loser 1.635556 / -1.250000 R.
Conditional CLOSED-only DD 191.233333 R; largest winner share 0.071332; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 12 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 29 | -19.616667 | 0.213761 | 0.174757 | 18 | 0 | 17 |
| 2023-02 | 23 | -9.266667 | 0.350467 | 0.310345 | 18 | 3 | 16 |
| 2023-03 | 17 | -19.400000 | 0.049020 | 0.051948 | 22 | 2 | 19 |
| 2023-04 | 24 | -13.700000 | 0.316708 | 0.342466 | 18 | 0 | 17 |
| 2023-05 | 30 | -12.100000 | 0.481058 | 0.575000 | 21 | 2 | 18 |
| 2023-06 | 27 | -13.666667 | 0.413867 | 0.360465 | 20 | 1 | 18 |
| 2023-07 | 32 | -5.750000 | 0.690583 | 0.784615 | 19 | 1 | 16 |
| 2023-08 | 58 | -23.133333 | 0.437829 | 0.433962 | 14 | 1 | 10 |
| 2023-09 | 37 | -22.766667 | 0.312185 | 0.300943 | 14 | 0 | 12 |
| 2023-10 | 27 | -11.633333 | 0.600686 | 0.705882 | 2 | 0 | 2 |
| 2023-11 | 42 | -25.700000 | 0.480808 | 0.490566 | 6 | 1 | 1 |
| 2023-12 | 30 | -11.066667 | 0.702775 | 0.717791 | 0 | 0 | 0 |

### B_OPT2023_N4_W3_T2_SB2_TP8

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 376, entry dates 159, entry months 12; SKIP 11, EXCLUDED 146, exclusion share 0.279693; conditional FLAT CLOSED 375.
Net -184.966667 R; PF R / price 0.447861 / 0.380430; expectancy -0.491933 R; win rate 0.239362; average winner / loser 1.667037 / -1.250000 R.
Conditional CLOSED-only DD 190.533333 R; largest winner share 0.079982; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 12 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 29 | -19.616667 | 0.213761 | 0.174757 | 18 | 0 | 17 |
| 2023-02 | 23 | -9.266667 | 0.350467 | 0.310345 | 18 | 3 | 16 |
| 2023-03 | 17 | -19.400000 | 0.049020 | 0.051948 | 22 | 2 | 19 |
| 2023-04 | 24 | -13.700000 | 0.316708 | 0.342466 | 18 | 0 | 17 |
| 2023-05 | 30 | -12.100000 | 0.481058 | 0.575000 | 21 | 2 | 18 |
| 2023-06 | 27 | -13.666667 | 0.413867 | 0.360465 | 20 | 1 | 18 |
| 2023-07 | 32 | -5.750000 | 0.690583 | 0.784615 | 19 | 1 | 16 |
| 2023-08 | 58 | -23.133333 | 0.437829 | 0.433962 | 14 | 1 | 10 |
| 2023-09 | 37 | -22.766667 | 0.312185 | 0.300943 | 14 | 0 | 12 |
| 2023-10 | 27 | -11.633333 | 0.600686 | 0.705882 | 2 | 0 | 2 |
| 2023-11 | 42 | -25.700000 | 0.480808 | 0.490566 | 6 | 1 | 1 |
| 2023-12 | 30 | -8.233333 | 0.778872 | 0.803681 | 0 | 0 | 0 |

### B_OPT2023_N4_W3_T2_SB2_TP9

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 376, entry dates 159, entry months 12; SKIP 11, EXCLUDED 146, exclusion share 0.279693; conditional FLAT CLOSED 375.
Net -182.133333 R; PF R / price 0.456318 / 0.382064; expectancy -0.484397 R; win rate 0.239362; average winner / loser 1.698519 / -1.250000 R.
Conditional CLOSED-only DD 190.533333 R; largest winner share 0.088312; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 12 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 29 | -19.616667 | 0.213761 | 0.174757 | 18 | 0 | 17 |
| 2023-02 | 23 | -9.266667 | 0.350467 | 0.310345 | 18 | 3 | 16 |
| 2023-03 | 17 | -19.400000 | 0.049020 | 0.051948 | 22 | 2 | 19 |
| 2023-04 | 24 | -13.700000 | 0.316708 | 0.342466 | 18 | 0 | 17 |
| 2023-05 | 30 | -12.100000 | 0.481058 | 0.575000 | 21 | 2 | 18 |
| 2023-06 | 27 | -13.666667 | 0.413867 | 0.360465 | 20 | 1 | 18 |
| 2023-07 | 32 | -5.750000 | 0.690583 | 0.784615 | 19 | 1 | 16 |
| 2023-08 | 58 | -23.133333 | 0.437829 | 0.433962 | 14 | 1 | 10 |
| 2023-09 | 37 | -22.766667 | 0.312185 | 0.300943 | 14 | 0 | 12 |
| 2023-10 | 27 | -11.633333 | 0.600686 | 0.705882 | 2 | 0 | 2 |
| 2023-11 | 42 | -25.700000 | 0.480808 | 0.490566 | 6 | 1 | 1 |
| 2023-12 | 30 | -5.400000 | 0.854969 | 0.889571 | 0 | 0 | 0 |

### B_OPT2023_N4_W3_T2_SB2_TP10

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 376, entry dates 159, entry months 12; SKIP 11, EXCLUDED 146, exclusion share 0.279693; conditional FLAT CLOSED 375.
Net -179.300000 R; PF R / price 0.464776 / 0.383699; expectancy -0.476862 R; win rate 0.239362; average winner / loser 1.730000 / -1.250000 R.
Conditional CLOSED-only DD 190.533333 R; largest winner share 0.096339; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 12 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 29 | -19.616667 | 0.213761 | 0.174757 | 18 | 0 | 17 |
| 2023-02 | 23 | -9.266667 | 0.350467 | 0.310345 | 18 | 3 | 16 |
| 2023-03 | 17 | -19.400000 | 0.049020 | 0.051948 | 22 | 2 | 19 |
| 2023-04 | 24 | -13.700000 | 0.316708 | 0.342466 | 18 | 0 | 17 |
| 2023-05 | 30 | -12.100000 | 0.481058 | 0.575000 | 21 | 2 | 18 |
| 2023-06 | 27 | -13.666667 | 0.413867 | 0.360465 | 20 | 1 | 18 |
| 2023-07 | 32 | -5.750000 | 0.690583 | 0.784615 | 19 | 1 | 16 |
| 2023-08 | 58 | -23.133333 | 0.437829 | 0.433962 | 14 | 1 | 10 |
| 2023-09 | 37 | -22.766667 | 0.312185 | 0.300943 | 14 | 0 | 12 |
| 2023-10 | 27 | -11.633333 | 0.600686 | 0.705882 | 2 | 0 | 2 |
| 2023-11 | 42 | -25.700000 | 0.480808 | 0.490566 | 6 | 1 | 1 |
| 2023-12 | 30 | -2.566667 | 0.931065 | 0.975460 | 0 | 0 | 0 |

### B_OPT2023_N5_W3_T2_SB2_TP2

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors.
CLOSED 317, entry dates 139, entry months 12; SKIP 5, EXCLUDED 140, exclusion share 0.306346; conditional FLAT CLOSED 317.
Net -82.150000 R; PF R / price 0.633395 / 0.564386; expectancy -0.259148 R; win rate 0.328076; average winner / loser 1.364744 / -1.131734 R.
Conditional CLOSED-only DD 83.666667 R; largest winner share 0.023485; largest positive month share 0.456140. Positive / negative / zero months 4 / 8 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 28 | -14.183333 | 0.344881 | 0.434783 | 18 | 0 | 16 |
| 2023-02 | 25 | -13.316667 | 0.234674 | 0.241935 | 18 | 2 | 15 |
| 2023-03 | 14 | -8.333333 | 0.367089 | 0.326531 | 22 | 1 | 19 |
| 2023-04 | 19 | 3.033333 | 1.444988 | 1.392857 | 18 | 0 | 16 |
| 2023-05 | 24 | 1.916667 | 1.210623 | 1.277778 | 21 | 0 | 18 |
| 2023-06 | 17 | 1.566667 | 1.186139 | 1.206897 | 20 | 0 | 19 |
| 2023-07 | 33 | -13.016667 | 0.405179 | 0.417582 | 19 | 2 | 16 |
| 2023-08 | 58 | -19.633333 | 0.571636 | 0.560694 | 14 | 0 | 10 |
| 2023-09 | 39 | -12.200000 | 0.507734 | 0.366667 | 14 | 0 | 8 |
| 2023-10 | 18 | 0.133333 | 1.009050 | 1.092308 | 2 | 0 | 2 |
| 2023-11 | 26 | -4.916667 | 0.809185 | 1.000000 | 6 | 0 | 1 |
| 2023-12 | 16 | -3.200000 | 0.779817 | 0.727273 | 0 | 0 | 0 |

### B_OPT2023_N5_W3_T2_SB2_TP3

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors.
CLOSED 316, entry dates 139, entry months 12; SKIP 5, EXCLUDED 140, exclusion share 0.307018; conditional FLAT CLOSED 316.
Net -67.883333 R; PF R / price 0.698005 / 0.581263; expectancy -0.214821 R; win rate 0.325949; average winner / loser 1.523301 / -1.135269 R.
Conditional CLOSED-only DD 75.033333 R; largest winner share 0.031867; largest positive month share 0.374723. Positive / negative / zero months 5 / 7 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 28 | -14.850000 | 0.314088 | 0.391304 | 18 | 0 | 16 |
| 2023-02 | 25 | -13.316667 | 0.234674 | 0.241935 | 18 | 2 | 15 |
| 2023-03 | 14 | -6.666667 | 0.493671 | 0.428571 | 22 | 1 | 19 |
| 2023-04 | 19 | 3.700000 | 1.542787 | 1.464286 | 18 | 0 | 16 |
| 2023-05 | 24 | 1.916667 | 1.210623 | 1.277778 | 21 | 0 | 18 |
| 2023-06 | 17 | 1.566667 | 1.186139 | 1.206897 | 20 | 0 | 19 |
| 2023-07 | 33 | -12.683333 | 0.420411 | 0.439560 | 19 | 2 | 16 |
| 2023-08 | 58 | -19.500000 | 0.577922 | 0.561798 | 14 | 0 | 10 |
| 2023-09 | 39 | -10.700000 | 0.568258 | 0.372917 | 14 | 0 | 8 |
| 2023-10 | 17 | 5.633333 | 1.420398 | 1.578947 | 2 | 0 | 2 |
| 2023-11 | 26 | 2.216667 | 1.086028 | 1.326923 | 6 | 0 | 1 |
| 2023-12 | 16 | -5.200000 | 0.679012 | 0.718310 | 0 | 0 | 0 |

### B_OPT2023_N5_W3_T2_SB2_TP4

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors.
CLOSED 316, entry dates 139, entry months 12; SKIP 5, EXCLUDED 140, exclusion share 0.307018; conditional FLAT CLOSED 316.
Net -64.683333 R; PF R / price 0.713938 / 0.575328; expectancy -0.204694 R; win rate 0.322785; average winner / loser 1.582680 / -1.136265 R.
Conditional CLOSED-only DD 77.533333 R; largest winner share 0.041297; largest positive month share 0.347889. Positive / negative / zero months 5 / 7 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 28 | -14.850000 | 0.314088 | 0.391304 | 18 | 0 | 16 |
| 2023-02 | 25 | -13.316667 | 0.234674 | 0.241935 | 18 | 2 | 15 |
| 2023-03 | 14 | -10.666667 | 0.189873 | 0.183673 | 22 | 1 | 19 |
| 2023-04 | 19 | 3.700000 | 1.542787 | 1.464286 | 18 | 0 | 16 |
| 2023-05 | 24 | 1.916667 | 1.210623 | 1.277778 | 21 | 0 | 18 |
| 2023-06 | 17 | 1.566667 | 1.186139 | 1.206897 | 20 | 0 | 19 |
| 2023-07 | 33 | -12.683333 | 0.420411 | 0.439560 | 19 | 2 | 16 |
| 2023-08 | 58 | -18.000000 | 0.610390 | 0.595506 | 14 | 0 | 10 |
| 2023-09 | 39 | -9.200000 | 0.628783 | 0.379167 | 14 | 0 | 8 |
| 2023-10 | 17 | 7.966667 | 1.594527 | 1.771930 | 2 | 0 | 2 |
| 2023-11 | 26 | 7.750000 | 1.300776 | 1.576923 | 6 | 0 | 1 |
| 2023-12 | 16 | -8.866667 | 0.494297 | 0.405063 | 0 | 0 | 0 |

### B_OPT2023_N5_W3_T2_SB2_TP5

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors.
CLOSED 316, entry dates 139, entry months 12; SKIP 5, EXCLUDED 140, exclusion share 0.307018; conditional FLAT CLOSED 316.
Net -55.950000 R; PF R / price 0.752561 / 0.587737; expectancy -0.177057 R; win rate 0.322785; average winner / loser 1.668301 / -1.136265 R.
Conditional CLOSED-only DD 76.033333 R; largest winner share 0.048972; largest positive month share 0.382571. Positive / negative / zero months 5 / 7 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 28 | -14.850000 | 0.314088 | 0.391304 | 18 | 0 | 16 |
| 2023-02 | 25 | -13.316667 | 0.234674 | 0.241935 | 18 | 2 | 15 |
| 2023-03 | 14 | -10.666667 | 0.189873 | 0.183673 | 22 | 1 | 19 |
| 2023-04 | 19 | 3.700000 | 1.542787 | 1.464286 | 18 | 0 | 16 |
| 2023-05 | 24 | 1.916667 | 1.210623 | 1.277778 | 21 | 0 | 18 |
| 2023-06 | 17 | 1.566667 | 1.186139 | 1.206897 | 20 | 0 | 19 |
| 2023-07 | 33 | -12.683333 | 0.420411 | 0.439560 | 19 | 2 | 16 |
| 2023-08 | 58 | -16.500000 | 0.642857 | 0.629213 | 14 | 0 | 10 |
| 2023-09 | 39 | -7.700000 | 0.689307 | 0.385417 | 14 | 0 | 8 |
| 2023-10 | 17 | 9.466667 | 1.706468 | 1.877193 | 2 | 0 | 2 |
| 2023-11 | 26 | 10.316667 | 1.400388 | 1.653846 | 6 | 0 | 1 |
| 2023-12 | 16 | -7.200000 | 0.589354 | 0.468354 | 0 | 0 | 0 |

### B_OPT2023_N5_W3_T2_SB2_TP6

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors.
CLOSED 315, entry dates 139, entry months 12; SKIP 5, EXCLUDED 140, exclusion share 0.307692; conditional FLAT CLOSED 315.
Net -76.383333 R; PF R / price 0.666861 / 0.586649; expectancy -0.242487 R; win rate 0.314286; average winner / loser 1.544444 / -1.140713 R.
Conditional CLOSED-only DD 76.383333 R; largest winner share 0.058862; largest positive month share 0.311576. Positive / negative / zero months 5 / 7 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 28 | -14.850000 | 0.314088 | 0.391304 | 18 | 0 | 16 |
| 2023-02 | 25 | -13.316667 | 0.234674 | 0.241935 | 18 | 2 | 15 |
| 2023-03 | 14 | -10.666667 | 0.189873 | 0.183673 | 22 | 1 | 19 |
| 2023-04 | 19 | 3.700000 | 1.542787 | 1.464286 | 18 | 0 | 16 |
| 2023-05 | 24 | 1.916667 | 1.210623 | 1.277778 | 21 | 0 | 18 |
| 2023-06 | 17 | 1.566667 | 1.186139 | 1.206897 | 20 | 0 | 19 |
| 2023-07 | 33 | -12.683333 | 0.420411 | 0.439560 | 19 | 2 | 16 |
| 2023-08 | 58 | -15.000000 | 0.675325 | 0.662921 | 14 | 0 | 10 |
| 2023-09 | 39 | -6.200000 | 0.749832 | 0.391667 | 14 | 0 | 8 |
| 2023-10 | 16 | 2.133333 | 1.159204 | 1.438596 | 2 | 0 | 2 |
| 2023-11 | 26 | 4.216667 | 1.154645 | 1.409091 | 6 | 0 | 1 |
| 2023-12 | 16 | -17.200000 | 0.104167 | 0.142857 | 0 | 0 | 0 |

### B_OPT2023_N5_W3_T2_SB2_TP7

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors.
CLOSED 315, entry dates 139, entry months 12; SKIP 5, EXCLUDED 140, exclusion share 0.307692; conditional FLAT CLOSED 315.
Net -78.883333 R; PF R / price 0.655957 / 0.592333; expectancy -0.250423 R; win rate 0.314286; average winner / loser 1.519192 / -1.140713 R.
Conditional CLOSED-only DD 78.883333 R; largest winner share 0.069814; largest positive month share 0.397138. Positive / negative / zero months 4 / 8 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 28 | -14.850000 | 0.314088 | 0.391304 | 18 | 0 | 16 |
| 2023-02 | 25 | -13.316667 | 0.234674 | 0.241935 | 18 | 2 | 15 |
| 2023-03 | 14 | -10.666667 | 0.189873 | 0.183673 | 22 | 1 | 19 |
| 2023-04 | 19 | 3.700000 | 1.542787 | 1.464286 | 18 | 0 | 16 |
| 2023-05 | 24 | 1.916667 | 1.210623 | 1.277778 | 21 | 0 | 18 |
| 2023-06 | 17 | 1.566667 | 1.186139 | 1.206897 | 20 | 0 | 19 |
| 2023-07 | 33 | -12.683333 | 0.420411 | 0.439560 | 19 | 2 | 16 |
| 2023-08 | 58 | -13.500000 | 0.707792 | 0.696629 | 14 | 0 | 10 |
| 2023-09 | 39 | -4.700000 | 0.810356 | 0.397917 | 14 | 0 | 8 |
| 2023-10 | 16 | 2.133333 | 1.159204 | 1.438596 | 2 | 0 | 2 |
| 2023-11 | 26 | -1.283333 | 0.952934 | 1.163636 | 6 | 0 | 1 |
| 2023-12 | 16 | -17.200000 | 0.104167 | 0.142857 | 0 | 0 | 0 |

### B_OPT2023_N5_W3_T2_SB2_TP8

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors.
CLOSED 315, entry dates 139, entry months 12; SKIP 5, EXCLUDED 140, exclusion share 0.307692; conditional FLAT CLOSED 315.
Net -75.883333 R; PF R / price 0.669041 / 0.601953; expectancy -0.240899 R; win rate 0.314286; average winner / loser 1.549495 / -1.140713 R.
Conditional CLOSED-only DD 75.883333 R; largest winner share 0.078227; largest positive month share 0.397138. Positive / negative / zero months 4 / 8 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 28 | -14.850000 | 0.314088 | 0.391304 | 18 | 0 | 16 |
| 2023-02 | 25 | -13.316667 | 0.234674 | 0.241935 | 18 | 2 | 15 |
| 2023-03 | 14 | -10.666667 | 0.189873 | 0.183673 | 22 | 1 | 19 |
| 2023-04 | 19 | 3.700000 | 1.542787 | 1.464286 | 18 | 0 | 16 |
| 2023-05 | 24 | 1.916667 | 1.210623 | 1.277778 | 21 | 0 | 18 |
| 2023-06 | 17 | 1.566667 | 1.186139 | 1.206897 | 20 | 0 | 19 |
| 2023-07 | 33 | -12.683333 | 0.420411 | 0.439560 | 19 | 2 | 16 |
| 2023-08 | 58 | -12.000000 | 0.740260 | 0.730337 | 14 | 0 | 10 |
| 2023-09 | 39 | -3.200000 | 0.870881 | 0.404167 | 14 | 0 | 8 |
| 2023-10 | 16 | 2.133333 | 1.159204 | 1.438596 | 2 | 0 | 2 |
| 2023-11 | 26 | -1.283333 | 0.952934 | 1.163636 | 6 | 0 | 1 |
| 2023-12 | 16 | -17.200000 | 0.104167 | 0.142857 | 0 | 0 | 0 |

### B_OPT2023_N5_W3_T2_SB2_TP9

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors.
CLOSED 315, entry dates 139, entry months 12; SKIP 5, EXCLUDED 140, exclusion share 0.307692; conditional FLAT CLOSED 315.
Net -72.883333 R; PF R / price 0.682125 / 0.611573; expectancy -0.231376 R; win rate 0.314286; average winner / loser 1.579798 / -1.140713 R.
Conditional CLOSED-only DD 72.883333 R; largest winner share 0.086317; largest positive month share 0.397138. Positive / negative / zero months 4 / 8 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 28 | -14.850000 | 0.314088 | 0.391304 | 18 | 0 | 16 |
| 2023-02 | 25 | -13.316667 | 0.234674 | 0.241935 | 18 | 2 | 15 |
| 2023-03 | 14 | -10.666667 | 0.189873 | 0.183673 | 22 | 1 | 19 |
| 2023-04 | 19 | 3.700000 | 1.542787 | 1.464286 | 18 | 0 | 16 |
| 2023-05 | 24 | 1.916667 | 1.210623 | 1.277778 | 21 | 0 | 18 |
| 2023-06 | 17 | 1.566667 | 1.186139 | 1.206897 | 20 | 0 | 19 |
| 2023-07 | 33 | -12.683333 | 0.420411 | 0.439560 | 19 | 2 | 16 |
| 2023-08 | 58 | -10.500000 | 0.772727 | 0.764045 | 14 | 0 | 10 |
| 2023-09 | 39 | -1.700000 | 0.931406 | 0.410417 | 14 | 0 | 8 |
| 2023-10 | 16 | 2.133333 | 1.159204 | 1.438596 | 2 | 0 | 2 |
| 2023-11 | 26 | -1.283333 | 0.952934 | 1.163636 | 6 | 0 | 1 |
| 2023-12 | 16 | -17.200000 | 0.104167 | 0.142857 | 0 | 0 | 0 |

### B_OPT2023_N5_W3_T2_SB2_TP10

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors.
CLOSED 315, entry dates 139, entry months 12; SKIP 5, EXCLUDED 140, exclusion share 0.307692; conditional FLAT CLOSED 315.
Net -72.133333 R; PF R / price 0.685397 / 0.608075; expectancy -0.228995 R; win rate 0.314286; average winner / loser 1.587374 / -1.140713 R.
Conditional CLOSED-only DD 72.133333 R; largest winner share 0.095450; largest positive month share 0.397138. Positive / negative / zero months 4 / 8 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 28 | -14.850000 | 0.314088 | 0.391304 | 18 | 0 | 16 |
| 2023-02 | 25 | -13.316667 | 0.234674 | 0.241935 | 18 | 2 | 15 |
| 2023-03 | 14 | -10.666667 | 0.189873 | 0.183673 | 22 | 1 | 19 |
| 2023-04 | 19 | 3.700000 | 1.542787 | 1.464286 | 18 | 0 | 16 |
| 2023-05 | 24 | 1.916667 | 1.210623 | 1.277778 | 21 | 0 | 18 |
| 2023-06 | 17 | 1.566667 | 1.186139 | 1.206897 | 20 | 0 | 19 |
| 2023-07 | 33 | -12.683333 | 0.420411 | 0.439560 | 19 | 2 | 16 |
| 2023-08 | 58 | -11.250000 | 0.756494 | 0.747191 | 14 | 0 | 10 |
| 2023-09 | 39 | -0.200000 | 0.991930 | 0.416667 | 14 | 0 | 8 |
| 2023-10 | 16 | 2.133333 | 1.159204 | 1.438596 | 2 | 0 | 2 |
| 2023-11 | 26 | -1.283333 | 0.952934 | 1.163636 | 6 | 0 | 1 |
| 2023-12 | 16 | -17.200000 | 0.104167 | 0.142857 | 0 | 0 | 0 |

### B_OPT2023_N6_W3_T2_SB2_TP2

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 268, entry dates 127, entry months 12; SKIP 16, EXCLUDED 137, exclusion share 0.338272; conditional FLAT CLOSED 255.
Net -84.083333 R; PF R / price 0.561876 / 0.475420; expectancy -0.313744 R; win rate 0.298507; average winner / loser 1.347917 / -1.115795 R.
Conditional CLOSED-only DD 90.416667 R; largest winner share 0.030912; largest positive month share 0.519784. Positive / negative / zero months 3 / 9 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 33 | -20.233333 | 0.262454 | 0.324324 | 18 | 1 | 15 |
| 2023-02 | 18 | -5.066667 | 0.414258 | 0.400000 | 18 | 2 | 16 |
| 2023-03 | 10 | -7.500000 | 0.181818 | 0.153846 | 22 | 5 | 18 |
| 2023-04 | 19 | 9.633333 | 2.553763 | 2.000000 | 18 | 2 | 16 |
| 2023-05 | 19 | -9.166667 | 0.386845 | 0.436364 | 21 | 1 | 18 |
| 2023-06 | 19 | -10.900000 | 0.343373 | 0.328125 | 20 | 1 | 18 |
| 2023-07 | 28 | -11.533333 | 0.376014 | 0.408451 | 19 | 2 | 16 |
| 2023-08 | 59 | -27.866667 | 0.419243 | 0.417112 | 14 | 1 | 9 |
| 2023-09 | 33 | -7.183333 | 0.602031 | 0.535211 | 14 | 0 | 10 |
| 2023-10 | 6 | 3.800000 | 2.187500 | 1.937500 | 2 | 0 | 1 |
| 2023-11 | 15 | -3.166667 | 0.778555 | 1.000000 | 6 | 1 | 0 |
| 2023-12 | 9 | 5.100000 | 1.739130 | 1.793103 | 0 | 0 | 0 |

### B_OPT2023_N6_W3_T2_SB2_TP3

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 267, entry dates 127, entry months 12; SKIP 16, EXCLUDED 137, exclusion share 0.339109; conditional FLAT CLOSED 254.
Net -72.216667 R; PF R / price 0.624230 / 0.511098; expectancy -0.270474 R; win rate 0.295880; average winner / loser 1.518565 / -1.117345 R.
Conditional CLOSED-only DD 83.850000 R; largest winner share 0.041678; largest positive month share 0.503556. Positive / negative / zero months 4 / 8 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 33 | -20.000000 | 0.270960 | 0.324324 | 18 | 1 | 15 |
| 2023-02 | 18 | -5.066667 | 0.414258 | 0.400000 | 18 | 2 | 16 |
| 2023-03 | 10 | -7.500000 | 0.181818 | 0.153846 | 22 | 5 | 18 |
| 2023-04 | 19 | 11.800000 | 2.903226 | 2.266667 | 18 | 2 | 16 |
| 2023-05 | 19 | -9.166667 | 0.386845 | 0.436364 | 21 | 1 | 18 |
| 2023-06 | 19 | -10.900000 | 0.343373 | 0.328125 | 20 | 1 | 18 |
| 2023-07 | 28 | -12.033333 | 0.348963 | 0.380282 | 19 | 2 | 16 |
| 2023-08 | 58 | -22.800000 | 0.510555 | 0.505556 | 14 | 1 | 9 |
| 2023-09 | 33 | -8.183333 | 0.546630 | 0.492958 | 14 | 0 | 10 |
| 2023-10 | 6 | 4.800000 | 2.500000 | 2.375000 | 2 | 0 | 1 |
| 2023-11 | 15 | 2.400000 | 1.167832 | 1.500000 | 6 | 1 | 0 |
| 2023-12 | 9 | 4.433333 | 1.517510 | 1.852941 | 0 | 0 | 0 |

### B_OPT2023_N6_W3_T2_SB2_TP4

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 267, entry dates 127, entry months 12; SKIP 16, EXCLUDED 137, exclusion share 0.339109; conditional FLAT CLOSED 254.
Net -72.300000 R; PF R / price 0.628945 / 0.520497; expectancy -0.270787 R; win rate 0.288390; average winner / loser 1.591558 / -1.119828 R.
Conditional CLOSED-only DD 81.333333 R; largest winner share 0.054400; largest positive month share 0.561134. Positive / negative / zero months 4 / 8 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 33 | -20.400000 | 0.256379 | 0.306306 | 18 | 1 | 15 |
| 2023-02 | 18 | -5.066667 | 0.414258 | 0.400000 | 18 | 2 | 16 |
| 2023-03 | 10 | -7.500000 | 0.181818 | 0.153846 | 22 | 5 | 18 |
| 2023-04 | 19 | 11.550000 | 2.862903 | 2.233333 | 18 | 2 | 16 |
| 2023-05 | 19 | -9.166667 | 0.386845 | 0.436364 | 21 | 1 | 18 |
| 2023-06 | 19 | -10.900000 | 0.343373 | 0.328125 | 20 | 1 | 18 |
| 2023-07 | 28 | -12.033333 | 0.348963 | 0.380282 | 19 | 2 | 16 |
| 2023-08 | 58 | -19.633333 | 0.578533 | 0.566667 | 14 | 1 | 9 |
| 2023-09 | 33 | -8.183333 | 0.546630 | 0.492958 | 14 | 0 | 10 |
| 2023-10 | 6 | 5.633333 | 2.760417 | 2.687500 | 2 | 0 | 1 |
| 2023-11 | 15 | 1.300000 | 1.083156 | 1.272727 | 6 | 1 | 0 |
| 2023-12 | 9 | 2.100000 | 1.212121 | 1.238095 | 0 | 0 | 0 |

### B_OPT2023_N6_W3_T2_SB2_TP5

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors.
CLOSED 267, entry dates 127, entry months 12; SKIP 16, EXCLUDED 137, exclusion share 0.339109; conditional FLAT CLOSED 254.
Net -63.150000 R; PF R / price 0.675905 / 0.534560; expectancy -0.236517 R; win rate 0.288390; average winner / loser 1.710390 / -1.119828 R.
Conditional CLOSED-only DD 79.416667 R; largest winner share 0.063275; largest positive month share 0.415219. Positive / negative / zero months 4 / 8 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 33 | -20.400000 | 0.256379 | 0.306306 | 18 | 1 | 15 |
| 2023-02 | 18 | -5.066667 | 0.414258 | 0.400000 | 18 | 2 | 16 |
| 2023-03 | 10 | -7.500000 | 0.181818 | 0.153846 | 22 | 5 | 18 |
| 2023-04 | 19 | 11.550000 | 2.862903 | 2.233333 | 18 | 2 | 16 |
| 2023-05 | 19 | -9.166667 | 0.386845 | 0.436364 | 21 | 1 | 18 |
| 2023-06 | 19 | -10.900000 | 0.343373 | 0.328125 | 20 | 1 | 18 |
| 2023-07 | 28 | -12.033333 | 0.348963 | 0.380282 | 19 | 2 | 16 |
| 2023-08 | 58 | -17.716667 | 0.619678 | 0.600000 | 14 | 1 | 9 |
| 2023-09 | 33 | -8.183333 | 0.546630 | 0.492958 | 14 | 0 | 10 |
| 2023-10 | 6 | 5.633333 | 2.760417 | 2.687500 | 2 | 0 | 1 |
| 2023-11 | 15 | 5.533333 | 1.353945 | 1.590909 | 6 | 1 | 0 |
| 2023-12 | 9 | 5.100000 | 1.515152 | 1.547619 | 0 | 0 | 0 |

### B_OPT2023_N6_W3_T2_SB2_TP6

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 267, entry dates 127, entry months 12; SKIP 16, EXCLUDED 137, exclusion share 0.339109; conditional FLAT CLOSED 254.
Net -72.216667 R; PF R / price 0.632516 / 0.538197; expectancy -0.270474 R; win rate 0.284644; average winner / loser 1.635526 / -1.122952 R.
Conditional CLOSED-only DD 77.750000 R; largest winner share 0.080451; largest positive month share 0.559322. Positive / negative / zero months 3 / 9 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 33 | -20.400000 | 0.256379 | 0.306306 | 18 | 1 | 15 |
| 2023-02 | 18 | -5.066667 | 0.414258 | 0.400000 | 18 | 2 | 16 |
| 2023-03 | 10 | -7.500000 | 0.181818 | 0.153846 | 22 | 5 | 18 |
| 2023-04 | 19 | 11.550000 | 2.862903 | 2.233333 | 18 | 2 | 16 |
| 2023-05 | 19 | -9.166667 | 0.386845 | 0.436364 | 21 | 1 | 18 |
| 2023-06 | 19 | -10.900000 | 0.343373 | 0.328125 | 20 | 1 | 18 |
| 2023-07 | 28 | -12.033333 | 0.348963 | 0.380282 | 19 | 2 | 16 |
| 2023-08 | 58 | -16.050000 | 0.655456 | 0.627778 | 14 | 1 | 9 |
| 2023-09 | 33 | -8.183333 | 0.546630 | 0.492958 | 14 | 0 | 10 |
| 2023-10 | 6 | 5.633333 | 2.760417 | 2.687500 | 2 | 0 | 1 |
| 2023-11 | 15 | 3.466667 | 1.221748 | 1.500000 | 6 | 1 | 0 |
| 2023-12 | 9 | -3.566667 | 0.691643 | 1.021277 | 0 | 0 | 0 |

### B_OPT2023_N6_W3_T2_SB2_TP7

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 267, entry dates 127, entry months 12; SKIP 16, EXCLUDED 137, exclusion share 0.339109; conditional FLAT CLOSED 254.
Net -68.383333 R; PF R / price 0.652023 / 0.547615; expectancy -0.256117 R; win rate 0.284644; average winner / loser 1.685965 / -1.122952 R.
Conditional CLOSED-only DD 76.083333 R; largest winner share 0.091051; largest positive month share 0.537626. Positive / negative / zero months 3 / 9 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 33 | -20.400000 | 0.256379 | 0.306306 | 18 | 1 | 15 |
| 2023-02 | 18 | -5.066667 | 0.414258 | 0.400000 | 18 | 2 | 16 |
| 2023-03 | 10 | -7.500000 | 0.181818 | 0.153846 | 22 | 5 | 18 |
| 2023-04 | 19 | 11.550000 | 2.862903 | 2.233333 | 18 | 2 | 16 |
| 2023-05 | 19 | -9.166667 | 0.386845 | 0.436364 | 21 | 1 | 18 |
| 2023-06 | 19 | -10.900000 | 0.343373 | 0.328125 | 20 | 1 | 18 |
| 2023-07 | 28 | -12.033333 | 0.348963 | 0.380282 | 19 | 2 | 16 |
| 2023-08 | 58 | -14.383333 | 0.691234 | 0.655556 | 14 | 1 | 9 |
| 2023-09 | 33 | -8.183333 | 0.546630 | 0.492958 | 14 | 0 | 10 |
| 2023-10 | 6 | 5.633333 | 2.760417 | 2.687500 | 2 | 0 | 1 |
| 2023-11 | 15 | 4.300000 | 1.275053 | 1.575758 | 6 | 1 | 0 |
| 2023-12 | 9 | -2.233333 | 0.806916 | 1.191489 | 0 | 0 | 0 |

### B_OPT2023_N6_W3_T2_SB2_TP8

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 267, entry dates 127, entry months 12; SKIP 16, EXCLUDED 137, exclusion share 0.339109; conditional FLAT CLOSED 254.
Net -68.716667 R; PF R / price 0.650327 / 0.553296; expectancy -0.257366 R; win rate 0.284644; average winner / loser 1.681579 / -1.122952 R.
Conditional CLOSED-only DD 74.416667 R; largest winner share 0.104330; largest positive month share 0.537626. Positive / negative / zero months 3 / 9 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 33 | -20.400000 | 0.256379 | 0.306306 | 18 | 1 | 15 |
| 2023-02 | 18 | -5.066667 | 0.414258 | 0.400000 | 18 | 2 | 16 |
| 2023-03 | 10 | -7.500000 | 0.181818 | 0.153846 | 22 | 5 | 18 |
| 2023-04 | 19 | 11.550000 | 2.862903 | 2.233333 | 18 | 2 | 16 |
| 2023-05 | 19 | -9.166667 | 0.386845 | 0.436364 | 21 | 1 | 18 |
| 2023-06 | 19 | -10.900000 | 0.343373 | 0.328125 | 20 | 1 | 18 |
| 2023-07 | 28 | -12.033333 | 0.348963 | 0.380282 | 19 | 2 | 16 |
| 2023-08 | 58 | -12.716667 | 0.727013 | 0.683333 | 14 | 1 | 9 |
| 2023-09 | 33 | -8.183333 | 0.546630 | 0.492958 | 14 | 0 | 10 |
| 2023-10 | 6 | 5.633333 | 2.760417 | 2.687500 | 2 | 0 | 1 |
| 2023-11 | 15 | 4.300000 | 1.275053 | 1.575758 | 6 | 1 | 0 |
| 2023-12 | 9 | -4.233333 | 0.634006 | 0.936170 | 0 | 0 | 0 |

### B_OPT2023_N6_W3_T2_SB2_TP9

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 267, entry dates 127, entry months 12; SKIP 16, EXCLUDED 137, exclusion share 0.339109; conditional FLAT CLOSED 254.
Net -67.050000 R; PF R / price 0.658808 / 0.560771; expectancy -0.251124 R; win rate 0.284644; average winner / loser 1.703509 / -1.122952 R.
Conditional CLOSED-only DD 72.750000 R; largest winner share 0.115860; largest positive month share 0.537626. Positive / negative / zero months 3 / 9 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 33 | -20.400000 | 0.256379 | 0.306306 | 18 | 1 | 15 |
| 2023-02 | 18 | -5.066667 | 0.414258 | 0.400000 | 18 | 2 | 16 |
| 2023-03 | 10 | -7.500000 | 0.181818 | 0.153846 | 22 | 5 | 18 |
| 2023-04 | 19 | 11.550000 | 2.862903 | 2.233333 | 18 | 2 | 16 |
| 2023-05 | 19 | -9.166667 | 0.386845 | 0.436364 | 21 | 1 | 18 |
| 2023-06 | 19 | -10.900000 | 0.343373 | 0.328125 | 20 | 1 | 18 |
| 2023-07 | 28 | -12.033333 | 0.348963 | 0.380282 | 19 | 2 | 16 |
| 2023-08 | 58 | -11.050000 | 0.762791 | 0.711111 | 14 | 1 | 9 |
| 2023-09 | 33 | -8.183333 | 0.546630 | 0.492958 | 14 | 0 | 10 |
| 2023-10 | 6 | 5.633333 | 2.760417 | 2.687500 | 2 | 0 | 1 |
| 2023-11 | 15 | 4.300000 | 1.275053 | 1.575758 | 6 | 1 | 0 |
| 2023-12 | 9 | -4.233333 | 0.634006 | 0.936170 | 0 | 0 | 0 |

### B_OPT2023_N6_W3_T2_SB2_TP10

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 267, entry dates 127, entry months 12; SKIP 16, EXCLUDED 137, exclusion share 0.339109; conditional FLAT CLOSED 254.
Net -65.383333 R; PF R / price 0.667289 / 0.568246; expectancy -0.244881 R; win rate 0.284644; average winner / loser 1.725439 / -1.122952 R.
Conditional CLOSED-only DD 71.083333 R; largest winner share 0.127097; largest positive month share 0.537626. Positive / negative / zero months 3 / 9 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 33 | -20.400000 | 0.256379 | 0.306306 | 18 | 1 | 15 |
| 2023-02 | 18 | -5.066667 | 0.414258 | 0.400000 | 18 | 2 | 16 |
| 2023-03 | 10 | -7.500000 | 0.181818 | 0.153846 | 22 | 5 | 18 |
| 2023-04 | 19 | 11.550000 | 2.862903 | 2.233333 | 18 | 2 | 16 |
| 2023-05 | 19 | -9.166667 | 0.386845 | 0.436364 | 21 | 1 | 18 |
| 2023-06 | 19 | -10.900000 | 0.343373 | 0.328125 | 20 | 1 | 18 |
| 2023-07 | 28 | -12.033333 | 0.348963 | 0.380282 | 19 | 2 | 16 |
| 2023-08 | 58 | -9.383333 | 0.798569 | 0.738889 | 14 | 1 | 9 |
| 2023-09 | 33 | -8.183333 | 0.546630 | 0.492958 | 14 | 0 | 10 |
| 2023-10 | 6 | 5.633333 | 2.760417 | 2.687500 | 2 | 0 | 1 |
| 2023-11 | 15 | 4.300000 | 1.275053 | 1.575758 | 6 | 1 | 0 |
| 2023-12 | 9 | -4.233333 | 0.634006 | 0.936170 | 0 | 0 | 0 |

### B_OPT2023_N7_W3_T2_SB2_TP2

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 256, entry dates 124, entry months 12; SKIP 13, EXCLUDED 137, exclusion share 0.348601; conditional FLAT CLOSED 256.
Net -125.916667 R; PF R / price 0.366298 / 0.351118; expectancy -0.491862 R; win rate 0.246094; average winner / loser 1.155291 / -1.110056 R.
Conditional CLOSED-only DD 127.916667 R; largest winner share 0.045798; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 29 | -23.383333 | 0.147631 | 0.171429 | 18 | 2 | 17 |
| 2023-02 | 24 | -15.750000 | 0.142468 | 0.149254 | 18 | 1 | 14 |
| 2023-03 | 14 | -11.783333 | 0.048452 | 0.066667 | 22 | 2 | 18 |
| 2023-04 | 23 | 2.566667 | 1.227139 | 1.325000 | 18 | 4 | 14 |
| 2023-05 | 21 | -13.250000 | 0.255618 | 0.318182 | 21 | 0 | 19 |
| 2023-06 | 16 | -8.616667 | 0.291781 | 0.355556 | 20 | 2 | 19 |
| 2023-07 | 25 | -4.683333 | 0.624332 | 0.549020 | 19 | 1 | 16 |
| 2023-08 | 54 | -27.916667 | 0.381462 | 0.351351 | 14 | 0 | 9 |
| 2023-09 | 29 | -15.000000 | 0.253112 | 0.295775 | 14 | 0 | 10 |
| 2023-10 | 6 | -1.900000 | 0.677966 | 0.692308 | 2 | 1 | 1 |
| 2023-11 | 11 | -5.033333 | 0.549254 | 0.521739 | 6 | 0 | 0 |
| 2023-12 | 4 | -1.166667 | 0.740741 | 0.526316 | 0 | 0 | 0 |

### B_OPT2023_N7_W3_T2_SB2_TP3

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 257, entry dates 124, entry months 12; SKIP 13, EXCLUDED 137, exclusion share 0.347716; conditional FLAT CLOSED 257.
Net -127.083333 R; PF R / price 0.374077 / 0.371828; expectancy -0.494488 R; win rate 0.237354; average winner / loser 1.245082 / -1.115568 R.
Conditional CLOSED-only DD 127.083333 R; largest winner share 0.065833; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 29 | -21.983333 | 0.198663 | 0.238095 | 18 | 2 | 17 |
| 2023-02 | 24 | -15.750000 | 0.142468 | 0.149254 | 18 | 1 | 14 |
| 2023-03 | 14 | -11.783333 | 0.048452 | 0.066667 | 22 | 2 | 18 |
| 2023-04 | 23 | 3.433333 | 1.303835 | 1.400000 | 18 | 4 | 14 |
| 2023-05 | 21 | -13.250000 | 0.255618 | 0.318182 | 21 | 0 | 19 |
| 2023-06 | 16 | -8.616667 | 0.291781 | 0.355556 | 20 | 2 | 19 |
| 2023-07 | 25 | -5.016667 | 0.597594 | 0.529412 | 19 | 1 | 16 |
| 2023-08 | 55 | -27.833333 | 0.417713 | 0.381443 | 14 | 0 | 9 |
| 2023-09 | 29 | -15.000000 | 0.253112 | 0.295775 | 14 | 0 | 10 |
| 2023-10 | 6 | -3.150000 | 0.466102 | 0.500000 | 2 | 1 | 1 |
| 2023-11 | 11 | -1.966667 | 0.823881 | 0.782609 | 6 | 0 | 0 |
| 2023-12 | 4 | -6.166667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N7_W3_T2_SB2_TP4

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 257, entry dates 124, entry months 12; SKIP 13, EXCLUDED 137, exclusion share 0.347716; conditional FLAT CLOSED 257.
Net -122.650000 R; PF R / price 0.395912 / 0.376442; expectancy -0.477237 R; win rate 0.237354; average winner / loser 1.317760 / -1.115568 R.
Conditional CLOSED-only DD 122.650000 R; largest winner share 0.082936; largest positive month share 0.757353. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 29 | -23.783333 | 0.133050 | 0.152381 | 18 | 2 | 17 |
| 2023-02 | 24 | -15.750000 | 0.142468 | 0.149254 | 18 | 1 | 14 |
| 2023-03 | 14 | -11.783333 | 0.048452 | 0.066667 | 22 | 2 | 18 |
| 2023-04 | 23 | 3.433333 | 1.303835 | 1.400000 | 18 | 4 | 14 |
| 2023-05 | 21 | -13.250000 | 0.255618 | 0.318182 | 21 | 0 | 19 |
| 2023-06 | 16 | -8.616667 | 0.291781 | 0.355556 | 20 | 2 | 19 |
| 2023-07 | 25 | -5.016667 | 0.597594 | 0.529412 | 19 | 1 | 16 |
| 2023-08 | 55 | -24.666667 | 0.483961 | 0.438144 | 14 | 0 | 9 |
| 2023-09 | 29 | -15.000000 | 0.253112 | 0.295775 | 14 | 0 | 10 |
| 2023-10 | 6 | -3.150000 | 0.466102 | 0.500000 | 2 | 1 | 1 |
| 2023-11 | 11 | 1.100000 | 1.098507 | 1.043478 | 6 | 0 | 0 |
| 2023-12 | 4 | -6.166667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N7_W3_T2_SB2_TP5

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 257, entry dates 124, entry months 12; SKIP 13, EXCLUDED 137, exclusion share 0.347716; conditional FLAT CLOSED 257.
Net -123.000000 R; PF R / price 0.394188 / 0.384516; expectancy -0.478599 R; win rate 0.237354; average winner / loser 1.312022 / -1.115568 R.
Conditional CLOSED-only DD 123.000000 R; largest winner share 0.104123; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 29 | -23.783333 | 0.133050 | 0.152381 | 18 | 2 | 17 |
| 2023-02 | 24 | -15.750000 | 0.142468 | 0.149254 | 18 | 1 | 14 |
| 2023-03 | 14 | -11.783333 | 0.048452 | 0.066667 | 22 | 2 | 18 |
| 2023-04 | 23 | 3.433333 | 1.303835 | 1.400000 | 18 | 4 | 14 |
| 2023-05 | 21 | -13.250000 | 0.255618 | 0.318182 | 21 | 0 | 19 |
| 2023-06 | 16 | -8.616667 | 0.291781 | 0.355556 | 20 | 2 | 19 |
| 2023-07 | 25 | -5.016667 | 0.597594 | 0.529412 | 19 | 1 | 16 |
| 2023-08 | 55 | -22.750000 | 0.524059 | 0.469072 | 14 | 0 | 9 |
| 2023-09 | 29 | -15.000000 | 0.253112 | 0.295775 | 14 | 0 | 10 |
| 2023-10 | 6 | -3.150000 | 0.466102 | 0.500000 | 2 | 1 | 1 |
| 2023-11 | 11 | -1.166667 | 0.895522 | 0.956522 | 6 | 0 | 0 |
| 2023-12 | 4 | -6.166667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N7_W3_T2_SB2_TP6

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 257, entry dates 124, entry months 12; SKIP 13, EXCLUDED 137, exclusion share 0.347716; conditional FLAT CLOSED 257.
Net -121.733333 R; PF R / price 0.400427 / 0.391436; expectancy -0.473671 R; win rate 0.237354; average winner / loser 1.332787 / -1.115568 R.
Conditional CLOSED-only DD 121.733333 R; largest winner share 0.123001; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 29 | -23.783333 | 0.133050 | 0.152381 | 18 | 2 | 17 |
| 2023-02 | 24 | -15.750000 | 0.142468 | 0.149254 | 18 | 1 | 14 |
| 2023-03 | 14 | -11.783333 | 0.048452 | 0.066667 | 22 | 2 | 18 |
| 2023-04 | 23 | 3.433333 | 1.303835 | 1.400000 | 18 | 4 | 14 |
| 2023-05 | 21 | -13.250000 | 0.255618 | 0.318182 | 21 | 0 | 19 |
| 2023-06 | 16 | -8.616667 | 0.291781 | 0.355556 | 20 | 2 | 19 |
| 2023-07 | 25 | -5.016667 | 0.597594 | 0.529412 | 19 | 1 | 16 |
| 2023-08 | 55 | -21.083333 | 0.558926 | 0.494845 | 14 | 0 | 9 |
| 2023-09 | 29 | -15.000000 | 0.253112 | 0.295775 | 14 | 0 | 10 |
| 2023-10 | 6 | -3.150000 | 0.466102 | 0.500000 | 2 | 1 | 1 |
| 2023-11 | 11 | -1.566667 | 0.859701 | 0.913043 | 6 | 0 | 0 |
| 2023-12 | 4 | -6.166667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N7_W3_T2_SB2_TP7

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 257, entry dates 124, entry months 12; SKIP 13, EXCLUDED 137, exclusion share 0.347716; conditional FLAT CLOSED 257.
Net -120.066667 R; PF R / price 0.408636 / 0.398645; expectancy -0.467185 R; win rate 0.237354; average winner / loser 1.360109 / -1.115568 R.
Conditional CLOSED-only DD 120.066667 R; largest winner share 0.140619; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 29 | -23.783333 | 0.133050 | 0.152381 | 18 | 2 | 17 |
| 2023-02 | 24 | -15.750000 | 0.142468 | 0.149254 | 18 | 1 | 14 |
| 2023-03 | 14 | -11.783333 | 0.048452 | 0.066667 | 22 | 2 | 18 |
| 2023-04 | 23 | 3.433333 | 1.303835 | 1.400000 | 18 | 4 | 14 |
| 2023-05 | 21 | -13.250000 | 0.255618 | 0.318182 | 21 | 0 | 19 |
| 2023-06 | 16 | -8.616667 | 0.291781 | 0.355556 | 20 | 2 | 19 |
| 2023-07 | 25 | -5.016667 | 0.597594 | 0.529412 | 19 | 1 | 16 |
| 2023-08 | 55 | -19.416667 | 0.593794 | 0.520619 | 14 | 0 | 9 |
| 2023-09 | 29 | -15.000000 | 0.253112 | 0.295775 | 14 | 0 | 10 |
| 2023-10 | 6 | -3.150000 | 0.466102 | 0.500000 | 2 | 1 | 1 |
| 2023-11 | 11 | -1.566667 | 0.859701 | 0.913043 | 6 | 0 | 0 |
| 2023-12 | 4 | -6.166667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N7_W3_T2_SB2_TP8

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 257, entry dates 124, entry months 12; SKIP 13, EXCLUDED 137, exclusion share 0.347716; conditional FLAT CLOSED 257.
Net -118.400000 R; PF R / price 0.416845 / 0.405854; expectancy -0.460700 R; win rate 0.237354; average winner / loser 1.387432 / -1.115568 R.
Conditional CLOSED-only DD 118.400000 R; largest winner share 0.157542; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 29 | -23.783333 | 0.133050 | 0.152381 | 18 | 2 | 17 |
| 2023-02 | 24 | -15.750000 | 0.142468 | 0.149254 | 18 | 1 | 14 |
| 2023-03 | 14 | -11.783333 | 0.048452 | 0.066667 | 22 | 2 | 18 |
| 2023-04 | 23 | 3.433333 | 1.303835 | 1.400000 | 18 | 4 | 14 |
| 2023-05 | 21 | -13.250000 | 0.255618 | 0.318182 | 21 | 0 | 19 |
| 2023-06 | 16 | -8.616667 | 0.291781 | 0.355556 | 20 | 2 | 19 |
| 2023-07 | 25 | -5.016667 | 0.597594 | 0.529412 | 19 | 1 | 16 |
| 2023-08 | 55 | -17.750000 | 0.628661 | 0.546392 | 14 | 0 | 9 |
| 2023-09 | 29 | -15.000000 | 0.253112 | 0.295775 | 14 | 0 | 10 |
| 2023-10 | 6 | -3.150000 | 0.466102 | 0.500000 | 2 | 1 | 1 |
| 2023-11 | 11 | -1.566667 | 0.859701 | 0.913043 | 6 | 0 | 0 |
| 2023-12 | 4 | -6.166667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N7_W3_T2_SB2_TP9

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 257, entry dates 124, entry months 12; SKIP 13, EXCLUDED 137, exclusion share 0.347716; conditional FLAT CLOSED 257.
Net -116.733333 R; PF R / price 0.425053 / 0.413062; expectancy -0.454215 R; win rate 0.237354; average winner / loser 1.414754 / -1.115568 R.
Conditional CLOSED-only DD 116.733333 R; largest winner share 0.173812; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 29 | -23.783333 | 0.133050 | 0.152381 | 18 | 2 | 17 |
| 2023-02 | 24 | -15.750000 | 0.142468 | 0.149254 | 18 | 1 | 14 |
| 2023-03 | 14 | -11.783333 | 0.048452 | 0.066667 | 22 | 2 | 18 |
| 2023-04 | 23 | 3.433333 | 1.303835 | 1.400000 | 18 | 4 | 14 |
| 2023-05 | 21 | -13.250000 | 0.255618 | 0.318182 | 21 | 0 | 19 |
| 2023-06 | 16 | -8.616667 | 0.291781 | 0.355556 | 20 | 2 | 19 |
| 2023-07 | 25 | -5.016667 | 0.597594 | 0.529412 | 19 | 1 | 16 |
| 2023-08 | 55 | -16.083333 | 0.663529 | 0.572165 | 14 | 0 | 9 |
| 2023-09 | 29 | -15.000000 | 0.253112 | 0.295775 | 14 | 0 | 10 |
| 2023-10 | 6 | -3.150000 | 0.466102 | 0.500000 | 2 | 1 | 1 |
| 2023-11 | 11 | -1.566667 | 0.859701 | 0.913043 | 6 | 0 | 0 |
| 2023-12 | 4 | -6.166667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N7_W3_T2_SB2_TP10

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 257, entry dates 124, entry months 12; SKIP 13, EXCLUDED 137, exclusion share 0.347716; conditional FLAT CLOSED 257.
Net -115.066667 R; PF R / price 0.433262 / 0.420271; expectancy -0.447730 R; win rate 0.237354; average winner / loser 1.442077 / -1.115568 R.
Conditional CLOSED-only DD 115.066667 R; largest winner share 0.189466; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 29 | -23.783333 | 0.133050 | 0.152381 | 18 | 2 | 17 |
| 2023-02 | 24 | -15.750000 | 0.142468 | 0.149254 | 18 | 1 | 14 |
| 2023-03 | 14 | -11.783333 | 0.048452 | 0.066667 | 22 | 2 | 18 |
| 2023-04 | 23 | 3.433333 | 1.303835 | 1.400000 | 18 | 4 | 14 |
| 2023-05 | 21 | -13.250000 | 0.255618 | 0.318182 | 21 | 0 | 19 |
| 2023-06 | 16 | -8.616667 | 0.291781 | 0.355556 | 20 | 2 | 19 |
| 2023-07 | 25 | -5.016667 | 0.597594 | 0.529412 | 19 | 1 | 16 |
| 2023-08 | 55 | -14.416667 | 0.698396 | 0.597938 | 14 | 0 | 9 |
| 2023-09 | 29 | -15.000000 | 0.253112 | 0.295775 | 14 | 0 | 10 |
| 2023-10 | 6 | -3.150000 | 0.466102 | 0.500000 | 2 | 1 | 1 |
| 2023-11 | 11 | -1.566667 | 0.859701 | 0.913043 | 6 | 0 | 0 |
| 2023-12 | 4 | -6.166667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N8_W3_T2_SB2_TP2

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 234, entry dates 112, entry months 12; SKIP 13, EXCLUDED 131, exclusion share 0.358904; conditional FLAT CLOSED 234.
Net -117.666667 R; PF R / price 0.330806 / 0.309961; expectancy -0.502849 R; win rate 0.230769; average winner / loser 1.077160 / -1.059237 R.
Conditional CLOSED-only DD 119.666667 R; largest winner share 0.057307; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 12 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 29 | -23.066667 | 0.137157 | 0.105769 | 18 | 2 | 14 |
| 2023-02 | 20 | -11.166667 | 0.083447 | 0.111111 | 18 | 2 | 16 |
| 2023-03 | 12 | -8.783333 | 0.073814 | 0.085714 | 22 | 1 | 18 |
| 2023-04 | 25 | -3.616667 | 0.761538 | 0.750000 | 18 | 1 | 14 |
| 2023-05 | 19 | -9.216667 | 0.296438 | 0.408163 | 21 | 3 | 16 |
| 2023-06 | 20 | -14.150000 | 0.167647 | 0.213115 | 20 | 3 | 17 |
| 2023-07 | 24 | -6.683333 | 0.524882 | 0.435484 | 19 | 1 | 17 |
| 2023-08 | 45 | -23.500000 | 0.326969 | 0.385714 | 14 | 0 | 8 |
| 2023-09 | 27 | -13.150000 | 0.344140 | 0.235443 | 14 | 0 | 10 |
| 2023-10 | 2 | -2.800000 | 0.000000 | 0.000000 | 2 | 0 | 1 |
| 2023-11 | 7 | -0.700000 | 0.886486 | 1.034483 | 6 | 0 | 0 |
| 2023-12 | 4 | -0.833333 | 0.800000 | 0.454545 | 0 | 0 | 0 |

### B_OPT2023_N8_W3_T2_SB2_TP3

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 233, entry dates 112, entry months 12; SKIP 13, EXCLUDED 131, exclusion share 0.359890; conditional FLAT CLOSED 233.
Net -116.900000 R; PF R / price 0.341408 / 0.338715; expectancy -0.501717 R; win rate 0.223176; average winner / loser 1.165385 / -1.062874 R.
Conditional CLOSED-only DD 116.900000 R; largest winner share 0.082508; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 12 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 29 | -21.400000 | 0.199501 | 0.153846 | 18 | 2 | 14 |
| 2023-02 | 20 | -11.166667 | 0.083447 | 0.111111 | 18 | 2 | 16 |
| 2023-03 | 12 | -8.783333 | 0.073814 | 0.085714 | 22 | 1 | 18 |
| 2023-04 | 25 | -2.750000 | 0.818681 | 0.803571 | 18 | 1 | 14 |
| 2023-05 | 19 | -9.216667 | 0.296438 | 0.408163 | 21 | 3 | 16 |
| 2023-06 | 20 | -14.150000 | 0.167647 | 0.213115 | 20 | 3 | 17 |
| 2023-07 | 24 | -7.016667 | 0.501185 | 0.419355 | 19 | 1 | 17 |
| 2023-08 | 44 | -21.000000 | 0.398568 | 0.471429 | 14 | 0 | 8 |
| 2023-09 | 27 | -11.816667 | 0.410640 | 0.245570 | 14 | 0 | 10 |
| 2023-10 | 2 | -2.800000 | 0.000000 | 0.000000 | 2 | 0 | 1 |
| 2023-11 | 7 | -0.966667 | 0.843243 | 0.931034 | 6 | 0 | 0 |
| 2023-12 | 4 | -5.833333 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N8_W3_T2_SB2_TP4

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 233, entry dates 112, entry months 12; SKIP 13, EXCLUDED 131, exclusion share 0.359890; conditional FLAT CLOSED 233.
Net -109.666667 R; PF R / price 0.382160 / 0.370846; expectancy -0.470672 R; win rate 0.223176; average winner / loser 1.304487 / -1.062874 R.
Conditional CLOSED-only DD 109.666667 R; largest winner share 0.098280; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 29 | -19.733333 | 0.261845 | 0.201923 | 18 | 2 | 14 |
| 2023-02 | 20 | -11.166667 | 0.083447 | 0.111111 | 18 | 2 | 16 |
| 2023-03 | 12 | -8.783333 | 0.073814 | 0.085714 | 22 | 1 | 18 |
| 2023-04 | 25 | -2.750000 | 0.818681 | 0.803571 | 18 | 1 | 14 |
| 2023-05 | 19 | -9.216667 | 0.296438 | 0.408163 | 21 | 3 | 16 |
| 2023-06 | 20 | -14.150000 | 0.167647 | 0.213115 | 20 | 3 | 17 |
| 2023-07 | 24 | -7.016667 | 0.501185 | 0.419355 | 19 | 1 | 17 |
| 2023-08 | 44 | -18.166667 | 0.479714 | 0.571429 | 14 | 0 | 8 |
| 2023-09 | 27 | -10.483333 | 0.477140 | 0.255696 | 14 | 0 | 10 |
| 2023-10 | 2 | -2.800000 | 0.000000 | 0.000000 | 2 | 0 | 1 |
| 2023-11 | 7 | 0.433333 | 1.070270 | 1.172414 | 6 | 0 | 0 |
| 2023-12 | 4 | -5.833333 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N8_W3_T2_SB2_TP5

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 233, entry dates 112, entry months 12; SKIP 13, EXCLUDED 131, exclusion share 0.359890; conditional FLAT CLOSED 233.
Net -108.683333 R; PF R / price 0.387700 / 0.371630; expectancy -0.466452 R; win rate 0.223176; average winner / loser 1.323397 / -1.062874 R.
Conditional CLOSED-only DD 108.750000 R; largest winner share 0.101720; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 29 | -23.066667 | 0.137157 | 0.105769 | 18 | 2 | 14 |
| 2023-02 | 20 | -11.166667 | 0.083447 | 0.111111 | 18 | 2 | 16 |
| 2023-03 | 12 | -8.783333 | 0.073814 | 0.085714 | 22 | 1 | 18 |
| 2023-04 | 25 | -2.750000 | 0.818681 | 0.803571 | 18 | 1 | 14 |
| 2023-05 | 19 | -9.216667 | 0.296438 | 0.408163 | 21 | 3 | 16 |
| 2023-06 | 20 | -14.150000 | 0.167647 | 0.213115 | 20 | 3 | 17 |
| 2023-07 | 24 | -7.016667 | 0.501185 | 0.419355 | 19 | 1 | 17 |
| 2023-08 | 44 | -16.583333 | 0.525060 | 0.635714 | 14 | 0 | 8 |
| 2023-09 | 27 | -9.150000 | 0.543641 | 0.265823 | 14 | 0 | 10 |
| 2023-10 | 2 | -2.800000 | 0.000000 | 0.000000 | 2 | 0 | 1 |
| 2023-11 | 7 | 1.833333 | 1.297297 | 1.413793 | 6 | 0 | 0 |
| 2023-12 | 4 | -5.833333 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N8_W3_T2_SB2_TP6

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 233, entry dates 112, entry months 12; SKIP 13, EXCLUDED 131, exclusion share 0.359890; conditional FLAT CLOSED 233.
Net -106.416667 R; PF R / price 0.400469 / 0.385110; expectancy -0.456724 R; win rate 0.223176; average winner / loser 1.366987 / -1.062874 R.
Conditional CLOSED-only DD 107.416667 R; largest winner share 0.112544; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 29 | -23.066667 | 0.137157 | 0.105769 | 18 | 2 | 14 |
| 2023-02 | 20 | -11.166667 | 0.083447 | 0.111111 | 18 | 2 | 16 |
| 2023-03 | 12 | -8.783333 | 0.073814 | 0.085714 | 22 | 1 | 18 |
| 2023-04 | 25 | -2.750000 | 0.818681 | 0.803571 | 18 | 1 | 14 |
| 2023-05 | 19 | -9.216667 | 0.296438 | 0.408163 | 21 | 3 | 16 |
| 2023-06 | 20 | -14.150000 | 0.167647 | 0.213115 | 20 | 3 | 17 |
| 2023-07 | 24 | -7.016667 | 0.501185 | 0.419355 | 19 | 1 | 17 |
| 2023-08 | 44 | -15.250000 | 0.563246 | 0.692857 | 14 | 0 | 8 |
| 2023-09 | 27 | -7.816667 | 0.610141 | 0.275949 | 14 | 0 | 10 |
| 2023-10 | 2 | -2.800000 | 0.000000 | 0.000000 | 2 | 0 | 1 |
| 2023-11 | 7 | 1.433333 | 1.232432 | 1.344828 | 6 | 0 | 0 |
| 2023-12 | 4 | -5.833333 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N8_W3_T2_SB2_TP7

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 233, entry dates 112, entry months 12; SKIP 13, EXCLUDED 131, exclusion share 0.359890; conditional FLAT CLOSED 233.
Net -105.250000 R; PF R / price 0.407042 / 0.384796; expectancy -0.451717 R; win rate 0.223176; average winner / loser 1.389423 / -1.062874 R.
Conditional CLOSED-only DD 107.583333 R; largest winner share 0.129181; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 29 | -23.066667 | 0.137157 | 0.105769 | 18 | 2 | 14 |
| 2023-02 | 20 | -11.166667 | 0.083447 | 0.111111 | 18 | 2 | 16 |
| 2023-03 | 12 | -8.783333 | 0.073814 | 0.085714 | 22 | 1 | 18 |
| 2023-04 | 25 | -2.750000 | 0.818681 | 0.803571 | 18 | 1 | 14 |
| 2023-05 | 19 | -9.216667 | 0.296438 | 0.408163 | 21 | 3 | 16 |
| 2023-06 | 20 | -14.150000 | 0.167647 | 0.213115 | 20 | 3 | 17 |
| 2023-07 | 24 | -7.016667 | 0.501185 | 0.419355 | 19 | 1 | 17 |
| 2023-08 | 44 | -15.416667 | 0.558473 | 0.685714 | 14 | 0 | 8 |
| 2023-09 | 27 | -6.483333 | 0.676642 | 0.286076 | 14 | 0 | 10 |
| 2023-10 | 2 | -2.800000 | 0.000000 | 0.000000 | 2 | 0 | 1 |
| 2023-11 | 7 | 1.433333 | 1.232432 | 1.344828 | 6 | 0 | 0 |
| 2023-12 | 4 | -5.833333 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N8_W3_T2_SB2_TP8

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 233, entry dates 112, entry months 12; SKIP 13, EXCLUDED 131, exclusion share 0.359890; conditional FLAT CLOSED 233.
Net -103.916667 R; PF R / price 0.414554 / 0.386050; expectancy -0.445994 R; win rate 0.223176; average winner / loser 1.415064 / -1.062874 R.
Conditional CLOSED-only DD 107.583333 R; largest winner share 0.144960; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 29 | -23.066667 | 0.137157 | 0.105769 | 18 | 2 | 14 |
| 2023-02 | 20 | -11.166667 | 0.083447 | 0.111111 | 18 | 2 | 16 |
| 2023-03 | 12 | -8.783333 | 0.073814 | 0.085714 | 22 | 1 | 18 |
| 2023-04 | 25 | -2.750000 | 0.818681 | 0.803571 | 18 | 1 | 14 |
| 2023-05 | 19 | -9.216667 | 0.296438 | 0.408163 | 21 | 3 | 16 |
| 2023-06 | 20 | -14.150000 | 0.167647 | 0.213115 | 20 | 3 | 17 |
| 2023-07 | 24 | -7.016667 | 0.501185 | 0.419355 | 19 | 1 | 17 |
| 2023-08 | 44 | -15.416667 | 0.558473 | 0.685714 | 14 | 0 | 8 |
| 2023-09 | 27 | -5.150000 | 0.743142 | 0.296203 | 14 | 0 | 10 |
| 2023-10 | 2 | -2.800000 | 0.000000 | 0.000000 | 2 | 0 | 1 |
| 2023-11 | 7 | 1.433333 | 1.232432 | 1.344828 | 6 | 0 | 0 |
| 2023-12 | 4 | -5.833333 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N8_W3_T2_SB2_TP9

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 233, entry dates 112, entry months 12; SKIP 13, EXCLUDED 131, exclusion share 0.359890; conditional FLAT CLOSED 233.
Net -102.583333 R; PF R / price 0.422066 / 0.387304; expectancy -0.440272 R; win rate 0.223176; average winner / loser 1.440705 / -1.062874 R.
Conditional CLOSED-only DD 107.583333 R; largest winner share 0.160178; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 29 | -23.066667 | 0.137157 | 0.105769 | 18 | 2 | 14 |
| 2023-02 | 20 | -11.166667 | 0.083447 | 0.111111 | 18 | 2 | 16 |
| 2023-03 | 12 | -8.783333 | 0.073814 | 0.085714 | 22 | 1 | 18 |
| 2023-04 | 25 | -2.750000 | 0.818681 | 0.803571 | 18 | 1 | 14 |
| 2023-05 | 19 | -9.216667 | 0.296438 | 0.408163 | 21 | 3 | 16 |
| 2023-06 | 20 | -14.150000 | 0.167647 | 0.213115 | 20 | 3 | 17 |
| 2023-07 | 24 | -7.016667 | 0.501185 | 0.419355 | 19 | 1 | 17 |
| 2023-08 | 44 | -15.416667 | 0.558473 | 0.685714 | 14 | 0 | 8 |
| 2023-09 | 27 | -3.816667 | 0.809643 | 0.306329 | 14 | 0 | 10 |
| 2023-10 | 2 | -2.800000 | 0.000000 | 0.000000 | 2 | 0 | 1 |
| 2023-11 | 7 | 1.433333 | 1.232432 | 1.344828 | 6 | 0 | 0 |
| 2023-12 | 4 | -5.833333 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N8_W3_T2_SB2_TP10

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 233, entry dates 112, entry months 12; SKIP 13, EXCLUDED 131, exclusion share 0.359890; conditional FLAT CLOSED 233.
Net -101.250000 R; PF R / price 0.429577 / 0.388558; expectancy -0.434549 R; win rate 0.223176; average winner / loser 1.466346 / -1.062874 R.
Conditional CLOSED-only DD 107.583333 R; largest winner share 0.174863; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 29 | -23.066667 | 0.137157 | 0.105769 | 18 | 2 | 14 |
| 2023-02 | 20 | -11.166667 | 0.083447 | 0.111111 | 18 | 2 | 16 |
| 2023-03 | 12 | -8.783333 | 0.073814 | 0.085714 | 22 | 1 | 18 |
| 2023-04 | 25 | -2.750000 | 0.818681 | 0.803571 | 18 | 1 | 14 |
| 2023-05 | 19 | -9.216667 | 0.296438 | 0.408163 | 21 | 3 | 16 |
| 2023-06 | 20 | -14.150000 | 0.167647 | 0.213115 | 20 | 3 | 17 |
| 2023-07 | 24 | -7.016667 | 0.501185 | 0.419355 | 19 | 1 | 17 |
| 2023-08 | 44 | -15.416667 | 0.558473 | 0.685714 | 14 | 0 | 8 |
| 2023-09 | 27 | -2.483333 | 0.876143 | 0.316456 | 14 | 0 | 10 |
| 2023-10 | 2 | -2.800000 | 0.000000 | 0.000000 | 2 | 0 | 1 |
| 2023-11 | 7 | 1.433333 | 1.232432 | 1.344828 | 6 | 0 | 0 |
| 2023-12 | 4 | -5.833333 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N9_W3_T2_SB2_TP2

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 187, entry dates 101, entry months 12; SKIP 13, EXCLUDED 130, exclusion share 0.410095; conditional FLAT CLOSED 187.
Net -96.450000 R; PF R / price 0.307195 / 0.282400; expectancy -0.515775 R; win rate 0.213904; average winner / loser 1.069167 / -1.031235 R.
Conditional CLOSED-only DD 99.783333 R; largest winner share 0.077942; largest positive month share 0.673469. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 22 | -21.500000 | 0.011494 | 0.010989 | 18 | 1 | 18 |
| 2023-02 | 21 | -10.683333 | 0.179257 | 0.220000 | 18 | 1 | 15 |
| 2023-03 | 8 | -8.600000 | 0.044444 | 0.068966 | 22 | 2 | 16 |
| 2023-04 | 21 | -2.933333 | 0.723270 | 0.622222 | 18 | 3 | 13 |
| 2023-05 | 15 | -10.566667 | 0.212422 | 0.306122 | 21 | 0 | 16 |
| 2023-06 | 12 | -5.200000 | 0.424354 | 0.533333 | 20 | 4 | 19 |
| 2023-07 | 18 | -4.566667 | 0.522648 | 0.463415 | 19 | 1 | 14 |
| 2023-08 | 40 | -22.133333 | 0.253093 | 0.285714 | 14 | 0 | 8 |
| 2023-09 | 23 | -9.683333 | 0.431507 | 0.298462 | 14 | 1 | 10 |
| 2023-10 | 1 | -1.400000 | 0.000000 | 0.000000 | 2 | 0 | 1 |
| 2023-11 | 3 | 0.550000 | 1.323529 | 1.285714 | 6 | 0 | 0 |
| 2023-12 | 3 | 0.266667 | 1.086957 | 0.833333 | 0 | 0 | 0 |

### B_OPT2023_N9_W3_T2_SB2_TP3

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 187, entry dates 101, entry months 12; SKIP 13, EXCLUDED 130, exclusion share 0.410095; conditional FLAT CLOSED 187.
Net -100.050000 R; PF R / price 0.289838 / 0.281555; expectancy -0.535027 R; win rate 0.208556; average winner / loser 1.047009 / -1.035907 R.
Conditional CLOSED-only DD 100.050000 R; largest winner share 0.110204; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 22 | -21.500000 | 0.011494 | 0.010989 | 18 | 1 | 18 |
| 2023-02 | 21 | -10.683333 | 0.179257 | 0.220000 | 18 | 1 | 15 |
| 2023-03 | 8 | -8.600000 | 0.044444 | 0.068966 | 22 | 2 | 16 |
| 2023-04 | 21 | -2.933333 | 0.723270 | 0.622222 | 18 | 3 | 13 |
| 2023-05 | 15 | -10.566667 | 0.212422 | 0.306122 | 21 | 0 | 16 |
| 2023-06 | 12 | -5.200000 | 0.424354 | 0.533333 | 20 | 4 | 19 |
| 2023-07 | 18 | -6.066667 | 0.365854 | 0.317073 | 19 | 1 | 14 |
| 2023-08 | 40 | -20.633333 | 0.303712 | 0.336134 | 14 | 0 | 8 |
| 2023-09 | 23 | -8.283333 | 0.513699 | 0.309231 | 14 | 1 | 10 |
| 2023-10 | 1 | -1.400000 | 0.000000 | 0.000000 | 2 | 0 | 1 |
| 2023-11 | 3 | 0.550000 | 1.323529 | 1.285714 | 6 | 0 | 0 |
| 2023-12 | 3 | -4.733333 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N9_W3_T2_SB2_TP4

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 187, entry dates 101, entry months 12; SKIP 13, EXCLUDED 130, exclusion share 0.410095; conditional FLAT CLOSED 187.
Net -97.150000 R; PF R / price 0.310422 / 0.294388; expectancy -0.519519 R; win rate 0.208556; average winner / loser 1.121368 / -1.035907 R.
Conditional CLOSED-only DD 97.166667 R; largest winner share 0.137195; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 22 | -21.500000 | 0.011494 | 0.010989 | 18 | 1 | 18 |
| 2023-02 | 21 | -10.683333 | 0.179257 | 0.220000 | 18 | 1 | 15 |
| 2023-03 | 8 | -8.600000 | 0.044444 | 0.068966 | 22 | 2 | 16 |
| 2023-04 | 21 | -2.933333 | 0.723270 | 0.622222 | 18 | 3 | 13 |
| 2023-05 | 15 | -10.566667 | 0.212422 | 0.306122 | 21 | 0 | 16 |
| 2023-06 | 12 | -5.200000 | 0.424354 | 0.533333 | 20 | 4 | 19 |
| 2023-07 | 18 | -6.066667 | 0.365854 | 0.317073 | 19 | 1 | 14 |
| 2023-08 | 40 | -19.133333 | 0.354331 | 0.386555 | 14 | 0 | 8 |
| 2023-09 | 23 | -6.883333 | 0.595890 | 0.320000 | 14 | 1 | 10 |
| 2023-10 | 1 | -1.400000 | 0.000000 | 0.000000 | 2 | 0 | 1 |
| 2023-11 | 3 | 0.550000 | 1.323529 | 1.285714 | 6 | 0 | 0 |
| 2023-12 | 3 | -4.733333 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N9_W3_T2_SB2_TP5

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 187, entry dates 101, entry months 12; SKIP 13, EXCLUDED 130, exclusion share 0.410095; conditional FLAT CLOSED 187.
Net -94.250000 R; PF R / price 0.331007 / 0.307221; expectancy -0.504011 R; win rate 0.208556; average winner / loser 1.195726 / -1.035907 R.
Conditional CLOSED-only DD 95.666667 R; largest winner share 0.160829; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 22 | -21.500000 | 0.011494 | 0.010989 | 18 | 1 | 18 |
| 2023-02 | 21 | -10.683333 | 0.179257 | 0.220000 | 18 | 1 | 15 |
| 2023-03 | 8 | -8.600000 | 0.044444 | 0.068966 | 22 | 2 | 16 |
| 2023-04 | 21 | -2.933333 | 0.723270 | 0.622222 | 18 | 3 | 13 |
| 2023-05 | 15 | -10.566667 | 0.212422 | 0.306122 | 21 | 0 | 16 |
| 2023-06 | 12 | -5.200000 | 0.424354 | 0.533333 | 20 | 4 | 19 |
| 2023-07 | 18 | -6.066667 | 0.365854 | 0.317073 | 19 | 1 | 14 |
| 2023-08 | 40 | -17.633333 | 0.404949 | 0.436975 | 14 | 0 | 8 |
| 2023-09 | 23 | -5.483333 | 0.678082 | 0.330769 | 14 | 1 | 10 |
| 2023-10 | 1 | -1.400000 | 0.000000 | 0.000000 | 2 | 0 | 1 |
| 2023-11 | 3 | 0.550000 | 1.323529 | 1.285714 | 6 | 0 | 0 |
| 2023-12 | 3 | -4.733333 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N9_W3_T2_SB2_TP6

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 187, entry dates 101, entry months 12; SKIP 13, EXCLUDED 130, exclusion share 0.410095; conditional FLAT CLOSED 187.
Net -91.350000 R; PF R / price 0.351591 / 0.320054; expectancy -0.488503 R; win rate 0.208556; average winner / loser 1.270085 / -1.035907 R.
Conditional CLOSED-only DD 94.166667 R; largest winner share 0.181696; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 22 | -21.500000 | 0.011494 | 0.010989 | 18 | 1 | 18 |
| 2023-02 | 21 | -10.683333 | 0.179257 | 0.220000 | 18 | 1 | 15 |
| 2023-03 | 8 | -8.600000 | 0.044444 | 0.068966 | 22 | 2 | 16 |
| 2023-04 | 21 | -2.933333 | 0.723270 | 0.622222 | 18 | 3 | 13 |
| 2023-05 | 15 | -10.566667 | 0.212422 | 0.306122 | 21 | 0 | 16 |
| 2023-06 | 12 | -5.200000 | 0.424354 | 0.533333 | 20 | 4 | 19 |
| 2023-07 | 18 | -6.066667 | 0.365854 | 0.317073 | 19 | 1 | 14 |
| 2023-08 | 40 | -16.133333 | 0.455568 | 0.487395 | 14 | 0 | 8 |
| 2023-09 | 23 | -4.083333 | 0.760274 | 0.341538 | 14 | 1 | 10 |
| 2023-10 | 1 | -1.400000 | 0.000000 | 0.000000 | 2 | 0 | 1 |
| 2023-11 | 3 | 0.550000 | 1.323529 | 1.285714 | 6 | 0 | 0 |
| 2023-12 | 3 | -4.733333 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N9_W3_T2_SB2_TP7

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 187, entry dates 101, entry months 12; SKIP 13, EXCLUDED 130, exclusion share 0.410095; conditional FLAT CLOSED 187.
Net -88.450000 R; PF R / price 0.372176 / 0.332886; expectancy -0.472995 R; win rate 0.208556; average winner / loser 1.344444 / -1.035907 R.
Conditional CLOSED-only DD 92.666667 R; largest winner share 0.200254; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 22 | -21.500000 | 0.011494 | 0.010989 | 18 | 1 | 18 |
| 2023-02 | 21 | -10.683333 | 0.179257 | 0.220000 | 18 | 1 | 15 |
| 2023-03 | 8 | -8.600000 | 0.044444 | 0.068966 | 22 | 2 | 16 |
| 2023-04 | 21 | -2.933333 | 0.723270 | 0.622222 | 18 | 3 | 13 |
| 2023-05 | 15 | -10.566667 | 0.212422 | 0.306122 | 21 | 0 | 16 |
| 2023-06 | 12 | -5.200000 | 0.424354 | 0.533333 | 20 | 4 | 19 |
| 2023-07 | 18 | -6.066667 | 0.365854 | 0.317073 | 19 | 1 | 14 |
| 2023-08 | 40 | -14.633333 | 0.506187 | 0.537815 | 14 | 0 | 8 |
| 2023-09 | 23 | -2.683333 | 0.842466 | 0.352308 | 14 | 1 | 10 |
| 2023-10 | 1 | -1.400000 | 0.000000 | 0.000000 | 2 | 0 | 1 |
| 2023-11 | 3 | 0.550000 | 1.323529 | 1.285714 | 6 | 0 | 0 |
| 2023-12 | 3 | -4.733333 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N9_W3_T2_SB2_TP8

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 187, entry dates 101, entry months 12; SKIP 13, EXCLUDED 130, exclusion share 0.410095; conditional FLAT CLOSED 187.
Net -85.550000 R; PF R / price 0.392760 / 0.345719; expectancy -0.457487 R; win rate 0.208556; average winner / loser 1.418803 / -1.035907 R.
Conditional CLOSED-only DD 91.166667 R; largest winner share 0.216867; largest positive month share 1.000000. Positive / negative / zero months 1 / 11 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 22 | -21.500000 | 0.011494 | 0.010989 | 18 | 1 | 18 |
| 2023-02 | 21 | -10.683333 | 0.179257 | 0.220000 | 18 | 1 | 15 |
| 2023-03 | 8 | -8.600000 | 0.044444 | 0.068966 | 22 | 2 | 16 |
| 2023-04 | 21 | -2.933333 | 0.723270 | 0.622222 | 18 | 3 | 13 |
| 2023-05 | 15 | -10.566667 | 0.212422 | 0.306122 | 21 | 0 | 16 |
| 2023-06 | 12 | -5.200000 | 0.424354 | 0.533333 | 20 | 4 | 19 |
| 2023-07 | 18 | -6.066667 | 0.365854 | 0.317073 | 19 | 1 | 14 |
| 2023-08 | 40 | -13.133333 | 0.556805 | 0.588235 | 14 | 0 | 8 |
| 2023-09 | 23 | -1.283333 | 0.924658 | 0.363077 | 14 | 1 | 10 |
| 2023-10 | 1 | -1.400000 | 0.000000 | 0.000000 | 2 | 0 | 1 |
| 2023-11 | 3 | 0.550000 | 1.323529 | 1.285714 | 6 | 0 | 0 |
| 2023-12 | 3 | -4.733333 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N9_W3_T2_SB2_TP9

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 187, entry dates 101, entry months 12; SKIP 13, EXCLUDED 130, exclusion share 0.410095; conditional FLAT CLOSED 187.
Net -82.650000 R; PF R / price 0.413344 / 0.358552; expectancy -0.441979 R; win rate 0.208556; average winner / loser 1.493162 / -1.035907 R.
Conditional CLOSED-only DD 89.666667 R; largest winner share 0.231826; largest positive month share 0.825000. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 22 | -21.500000 | 0.011494 | 0.010989 | 18 | 1 | 18 |
| 2023-02 | 21 | -10.683333 | 0.179257 | 0.220000 | 18 | 1 | 15 |
| 2023-03 | 8 | -8.600000 | 0.044444 | 0.068966 | 22 | 2 | 16 |
| 2023-04 | 21 | -2.933333 | 0.723270 | 0.622222 | 18 | 3 | 13 |
| 2023-05 | 15 | -10.566667 | 0.212422 | 0.306122 | 21 | 0 | 16 |
| 2023-06 | 12 | -5.200000 | 0.424354 | 0.533333 | 20 | 4 | 19 |
| 2023-07 | 18 | -6.066667 | 0.365854 | 0.317073 | 19 | 1 | 14 |
| 2023-08 | 40 | -11.633333 | 0.607424 | 0.638655 | 14 | 0 | 8 |
| 2023-09 | 23 | 0.116667 | 1.006849 | 0.373846 | 14 | 1 | 10 |
| 2023-10 | 1 | -1.400000 | 0.000000 | 0.000000 | 2 | 0 | 1 |
| 2023-11 | 3 | 0.550000 | 1.323529 | 1.285714 | 6 | 0 | 0 |
| 2023-12 | 3 | -4.733333 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N9_W3_T2_SB2_TP10

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 187, entry dates 101, entry months 12; SKIP 13, EXCLUDED 130, exclusion share 0.410095; conditional FLAT CLOSED 187.
Net -81.750000 R; PF R / price 0.419733 / 0.356062; expectancy -0.437166 R; win rate 0.208556; average winner / loser 1.516239 / -1.035907 R.
Conditional CLOSED-only DD 90.166667 R; largest winner share 0.236753; largest positive month share 0.733871. Positive / negative / zero months 2 / 10 / 0; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 22 | -21.500000 | 0.011494 | 0.010989 | 18 | 1 | 18 |
| 2023-02 | 21 | -10.683333 | 0.179257 | 0.220000 | 18 | 1 | 15 |
| 2023-03 | 8 | -8.600000 | 0.044444 | 0.068966 | 22 | 2 | 16 |
| 2023-04 | 21 | -2.933333 | 0.723270 | 0.622222 | 18 | 3 | 13 |
| 2023-05 | 15 | -10.566667 | 0.212422 | 0.306122 | 21 | 0 | 16 |
| 2023-06 | 12 | -5.200000 | 0.424354 | 0.533333 | 20 | 4 | 19 |
| 2023-07 | 18 | -6.066667 | 0.365854 | 0.317073 | 19 | 1 | 14 |
| 2023-08 | 40 | -12.133333 | 0.590551 | 0.621849 | 14 | 0 | 8 |
| 2023-09 | 23 | 1.516667 | 1.089041 | 0.384615 | 14 | 1 | 10 |
| 2023-10 | 1 | -1.400000 | 0.000000 | 0.000000 | 2 | 0 | 1 |
| 2023-11 | 3 | 0.550000 | 1.323529 | 1.285714 | 6 | 0 | 0 |
| 2023-12 | 3 | -4.733333 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N10_W3_T2_SB2_TP2

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 179, entry dates 101, entry months 12; SKIP 12, EXCLUDED 123, exclusion share 0.407285; conditional FLAT CLOSED 179.
Net -88.000000 R; PF R / price 0.323770 / 0.295951; expectancy -0.491620 R; win rate 0.240223; average winner / loser 0.979845 / -1.049462 R.
Conditional CLOSED-only DD 91.333333 R; largest winner share 0.079114; largest positive month share 1.000000. Positive / negative / zero months 1 / 10 / 1; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 25 | -22.250000 | 0.011111 | 0.011494 | 18 | 3 | 15 |
| 2023-02 | 21 | -12.766667 | 0.202083 | 0.169231 | 18 | 2 | 12 |
| 2023-03 | 6 | -7.000000 | 0.000000 | 0.000000 | 22 | 1 | 17 |
| 2023-04 | 19 | -2.450000 | 0.718391 | 0.764706 | 18 | 3 | 12 |
| 2023-05 | 16 | -8.950000 | 0.282086 | 0.326087 | 21 | 1 | 15 |
| 2023-06 | 10 | -5.066667 | 0.337691 | 0.366667 | 20 | 0 | 19 |
| 2023-07 | 17 | -6.716667 | 0.294221 | 0.333333 | 19 | 2 | 15 |
| 2023-08 | 37 | -15.616667 | 0.452687 | 0.429752 | 14 | 0 | 7 |
| 2023-09 | 23 | -6.116667 | 0.542394 | 0.343396 | 14 | 0 | 10 |
| 2023-10 | 1 | -1.400000 | 0.000000 | 0.000000 | 2 | 0 | 1 |
| 2023-11 | 1 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 6 | 0 | 0 |
| 2023-12 | 3 | 0.333333 | 1.111111 | 0.769231 | 0 | 0 | 0 |

### B_OPT2023_N10_W3_T2_SB2_TP3

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 179, entry dates 101, entry months 12; SKIP 12, EXCLUDED 123, exclusion share 0.407285; conditional FLAT CLOSED 179.
Net -90.250000 R; PF R / price 0.315250 / 0.304954; expectancy -0.504190 R; win rate 0.234637; average winner / loser 0.989286 / -1.054400 R.
Conditional CLOSED-only DD 90.250000 R; largest winner share 0.108303; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 11 / 1; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 25 | -22.250000 | 0.011111 | 0.011494 | 18 | 3 | 15 |
| 2023-02 | 21 | -12.766667 | 0.202083 | 0.169231 | 18 | 2 | 12 |
| 2023-03 | 6 | -7.000000 | 0.000000 | 0.000000 | 22 | 1 | 17 |
| 2023-04 | 19 | -2.450000 | 0.718391 | 0.764706 | 18 | 3 | 12 |
| 2023-05 | 16 | -8.950000 | 0.282086 | 0.326087 | 21 | 1 | 15 |
| 2023-06 | 10 | -5.066667 | 0.337691 | 0.366667 | 20 | 0 | 19 |
| 2023-07 | 17 | -6.716667 | 0.294221 | 0.333333 | 19 | 2 | 15 |
| 2023-08 | 37 | -14.366667 | 0.496495 | 0.471074 | 14 | 0 | 7 |
| 2023-09 | 23 | -4.616667 | 0.654613 | 0.354717 | 14 | 0 | 10 |
| 2023-10 | 1 | -1.400000 | 0.000000 | 0.000000 | 2 | 0 | 1 |
| 2023-11 | 1 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 6 | 0 | 0 |
| 2023-12 | 3 | -4.666667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N10_W3_T2_SB2_TP4

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 179, entry dates 101, entry months 12; SKIP 12, EXCLUDED 123, exclusion share 0.407285; conditional FLAT CLOSED 179.
Net -87.250000 R; PF R / price 0.338012 / 0.318301; expectancy -0.487430 R; win rate 0.234637; average winner / loser 1.060714 / -1.054400 R.
Conditional CLOSED-only DD 87.250000 R; largest winner share 0.134680; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 11 / 1; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 25 | -22.250000 | 0.011111 | 0.011494 | 18 | 3 | 15 |
| 2023-02 | 21 | -12.766667 | 0.202083 | 0.169231 | 18 | 2 | 12 |
| 2023-03 | 6 | -7.000000 | 0.000000 | 0.000000 | 22 | 1 | 17 |
| 2023-04 | 19 | -2.450000 | 0.718391 | 0.764706 | 18 | 3 | 12 |
| 2023-05 | 16 | -8.950000 | 0.282086 | 0.326087 | 21 | 1 | 15 |
| 2023-06 | 10 | -5.066667 | 0.337691 | 0.366667 | 20 | 0 | 19 |
| 2023-07 | 17 | -6.716667 | 0.294221 | 0.333333 | 19 | 2 | 15 |
| 2023-08 | 37 | -12.866667 | 0.549065 | 0.520661 | 14 | 0 | 7 |
| 2023-09 | 23 | -3.116667 | 0.766833 | 0.366038 | 14 | 0 | 10 |
| 2023-10 | 1 | -1.400000 | 0.000000 | 0.000000 | 2 | 0 | 1 |
| 2023-11 | 1 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 6 | 0 | 0 |
| 2023-12 | 3 | -4.666667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N10_W3_T2_SB2_TP5

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 179, entry dates 101, entry months 12; SKIP 12, EXCLUDED 123, exclusion share 0.407285; conditional FLAT CLOSED 179.
Net -84.250000 R; PF R / price 0.360774 / 0.331648; expectancy -0.470670 R; win rate 0.234637; average winner / loser 1.132143 / -1.054400 R.
Conditional CLOSED-only DD 85.683333 R; largest winner share 0.157729; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 11 / 1; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 25 | -22.250000 | 0.011111 | 0.011494 | 18 | 3 | 15 |
| 2023-02 | 21 | -12.766667 | 0.202083 | 0.169231 | 18 | 2 | 12 |
| 2023-03 | 6 | -7.000000 | 0.000000 | 0.000000 | 22 | 1 | 17 |
| 2023-04 | 19 | -2.450000 | 0.718391 | 0.764706 | 18 | 3 | 12 |
| 2023-05 | 16 | -8.950000 | 0.282086 | 0.326087 | 21 | 1 | 15 |
| 2023-06 | 10 | -5.066667 | 0.337691 | 0.366667 | 20 | 0 | 19 |
| 2023-07 | 17 | -6.716667 | 0.294221 | 0.333333 | 19 | 2 | 15 |
| 2023-08 | 37 | -11.366667 | 0.601636 | 0.570248 | 14 | 0 | 7 |
| 2023-09 | 23 | -1.616667 | 0.879052 | 0.377358 | 14 | 0 | 10 |
| 2023-10 | 1 | -1.400000 | 0.000000 | 0.000000 | 2 | 0 | 1 |
| 2023-11 | 1 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 6 | 0 | 0 |
| 2023-12 | 3 | -4.666667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N10_W3_T2_SB2_TP6

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 179, entry dates 101, entry months 12; SKIP 12, EXCLUDED 123, exclusion share 0.407285; conditional FLAT CLOSED 179.
Net -81.250000 R; PF R / price 0.383536 / 0.344995; expectancy -0.453911 R; win rate 0.234637; average winner / loser 1.203571 / -1.054400 R.
Conditional CLOSED-only DD 84.183333 R; largest winner share 0.178042; largest positive month share NOT_AVAILABLE. Positive / negative / zero months 0 / 11 / 1; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 25 | -22.250000 | 0.011111 | 0.011494 | 18 | 3 | 15 |
| 2023-02 | 21 | -12.766667 | 0.202083 | 0.169231 | 18 | 2 | 12 |
| 2023-03 | 6 | -7.000000 | 0.000000 | 0.000000 | 22 | 1 | 17 |
| 2023-04 | 19 | -2.450000 | 0.718391 | 0.764706 | 18 | 3 | 12 |
| 2023-05 | 16 | -8.950000 | 0.282086 | 0.326087 | 21 | 1 | 15 |
| 2023-06 | 10 | -5.066667 | 0.337691 | 0.366667 | 20 | 0 | 19 |
| 2023-07 | 17 | -6.716667 | 0.294221 | 0.333333 | 19 | 2 | 15 |
| 2023-08 | 37 | -9.866667 | 0.654206 | 0.619835 | 14 | 0 | 7 |
| 2023-09 | 23 | -0.116667 | 0.991272 | 0.388679 | 14 | 0 | 10 |
| 2023-10 | 1 | -1.400000 | 0.000000 | 0.000000 | 2 | 0 | 1 |
| 2023-11 | 1 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 6 | 0 | 0 |
| 2023-12 | 3 | -4.666667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N10_W3_T2_SB2_TP7

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 179, entry dates 101, entry months 12; SKIP 12, EXCLUDED 123, exclusion share 0.407285; conditional FLAT CLOSED 179.
Net -78.250000 R; PF R / price 0.406297 / 0.358342; expectancy -0.437151 R; win rate 0.234637; average winner / loser 1.275000 / -1.054400 R.
Conditional CLOSED-only DD 82.683333 R; largest winner share 0.196078; largest positive month share 1.000000. Positive / negative / zero months 1 / 10 / 1; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 25 | -22.250000 | 0.011111 | 0.011494 | 18 | 3 | 15 |
| 2023-02 | 21 | -12.766667 | 0.202083 | 0.169231 | 18 | 2 | 12 |
| 2023-03 | 6 | -7.000000 | 0.000000 | 0.000000 | 22 | 1 | 17 |
| 2023-04 | 19 | -2.450000 | 0.718391 | 0.764706 | 18 | 3 | 12 |
| 2023-05 | 16 | -8.950000 | 0.282086 | 0.326087 | 21 | 1 | 15 |
| 2023-06 | 10 | -5.066667 | 0.337691 | 0.366667 | 20 | 0 | 19 |
| 2023-07 | 17 | -6.716667 | 0.294221 | 0.333333 | 19 | 2 | 15 |
| 2023-08 | 37 | -8.366667 | 0.706776 | 0.669421 | 14 | 0 | 7 |
| 2023-09 | 23 | 1.383333 | 1.103491 | 0.400000 | 14 | 0 | 10 |
| 2023-10 | 1 | -1.400000 | 0.000000 | 0.000000 | 2 | 0 | 1 |
| 2023-11 | 1 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 6 | 0 | 0 |
| 2023-12 | 3 | -4.666667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N10_W3_T2_SB2_TP8

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 179, entry dates 101, entry months 12; SKIP 12, EXCLUDED 123, exclusion share 0.407285; conditional FLAT CLOSED 179.
Net -75.250000 R; PF R / price 0.429059 / 0.371689; expectancy -0.420391 R; win rate 0.234637; average winner / loser 1.346429 / -1.054400 R.
Conditional CLOSED-only DD 81.183333 R; largest winner share 0.212202; largest positive month share 1.000000. Positive / negative / zero months 1 / 10 / 1; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 25 | -22.250000 | 0.011111 | 0.011494 | 18 | 3 | 15 |
| 2023-02 | 21 | -12.766667 | 0.202083 | 0.169231 | 18 | 2 | 12 |
| 2023-03 | 6 | -7.000000 | 0.000000 | 0.000000 | 22 | 1 | 17 |
| 2023-04 | 19 | -2.450000 | 0.718391 | 0.764706 | 18 | 3 | 12 |
| 2023-05 | 16 | -8.950000 | 0.282086 | 0.326087 | 21 | 1 | 15 |
| 2023-06 | 10 | -5.066667 | 0.337691 | 0.366667 | 20 | 0 | 19 |
| 2023-07 | 17 | -6.716667 | 0.294221 | 0.333333 | 19 | 2 | 15 |
| 2023-08 | 37 | -6.866667 | 0.759346 | 0.719008 | 14 | 0 | 7 |
| 2023-09 | 23 | 2.883333 | 1.215711 | 0.411321 | 14 | 0 | 10 |
| 2023-10 | 1 | -1.400000 | 0.000000 | 0.000000 | 2 | 0 | 1 |
| 2023-11 | 1 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 6 | 0 | 0 |
| 2023-12 | 3 | -4.666667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N10_W3_T2_SB2_TP9

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 179, entry dates 101, entry months 12; SKIP 12, EXCLUDED 123, exclusion share 0.407285; conditional FLAT CLOSED 179.
Net -72.250000 R; PF R / price 0.451821 / 0.385035; expectancy -0.403631 R; win rate 0.234637; average winner / loser 1.417857 / -1.054400 R.
Conditional CLOSED-only DD 79.683333 R; largest winner share 0.226700; largest positive month share 1.000000. Positive / negative / zero months 1 / 10 / 1; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 25 | -22.250000 | 0.011111 | 0.011494 | 18 | 3 | 15 |
| 2023-02 | 21 | -12.766667 | 0.202083 | 0.169231 | 18 | 2 | 12 |
| 2023-03 | 6 | -7.000000 | 0.000000 | 0.000000 | 22 | 1 | 17 |
| 2023-04 | 19 | -2.450000 | 0.718391 | 0.764706 | 18 | 3 | 12 |
| 2023-05 | 16 | -8.950000 | 0.282086 | 0.326087 | 21 | 1 | 15 |
| 2023-06 | 10 | -5.066667 | 0.337691 | 0.366667 | 20 | 0 | 19 |
| 2023-07 | 17 | -6.716667 | 0.294221 | 0.333333 | 19 | 2 | 15 |
| 2023-08 | 37 | -5.366667 | 0.811916 | 0.768595 | 14 | 0 | 7 |
| 2023-09 | 23 | 4.383333 | 1.327930 | 0.422642 | 14 | 0 | 10 |
| 2023-10 | 1 | -1.400000 | 0.000000 | 0.000000 | 2 | 0 | 1 |
| 2023-11 | 1 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 6 | 0 | 0 |
| 2023-12 | 3 | -4.666667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

### B_OPT2023_N10_W3_T2_SB2_TP10

Status: **DOES_NOT_QUALIFY**. Failures: PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors.
CLOSED 179, entry dates 101, entry months 12; SKIP 12, EXCLUDED 123, exclusion share 0.407285; conditional FLAT CLOSED 179.
Net -71.250000 R; PF R / price 0.459408 / 0.382204; expectancy -0.398045 R; win rate 0.234637; average winner / loser 1.441667 / -1.054400 R.
Conditional CLOSED-only DD 80.183333 R; largest winner share 0.247729; largest positive month share 1.000000. Positive / negative / zero months 1 / 10 / 1; ideal 12/12: False. Qualifying adjacent neighbors: 0.

| Exit month | CLOSED | Net R | PF R | PF price | Incomplete days | SKIP | EXCLUDED |
|---|---|---|---|---|---|---|---|
| 2023-01 | 25 | -22.250000 | 0.011111 | 0.011494 | 18 | 3 | 15 |
| 2023-02 | 21 | -12.766667 | 0.202083 | 0.169231 | 18 | 2 | 12 |
| 2023-03 | 6 | -7.000000 | 0.000000 | 0.000000 | 22 | 1 | 17 |
| 2023-04 | 19 | -2.450000 | 0.718391 | 0.764706 | 18 | 3 | 12 |
| 2023-05 | 16 | -8.950000 | 0.282086 | 0.326087 | 21 | 1 | 15 |
| 2023-06 | 10 | -5.066667 | 0.337691 | 0.366667 | 20 | 0 | 19 |
| 2023-07 | 17 | -6.716667 | 0.294221 | 0.333333 | 19 | 2 | 15 |
| 2023-08 | 37 | -5.866667 | 0.794393 | 0.752066 | 14 | 0 | 7 |
| 2023-09 | 23 | 5.883333 | 1.440150 | 0.433962 | 14 | 0 | 10 |
| 2023-10 | 1 | -1.400000 | 0.000000 | 0.000000 | 2 | 0 | 1 |
| 2023-11 | 1 | 0.000000 | NOT_AVAILABLE | NOT_AVAILABLE | 6 | 0 | 0 |
| 2023-12 | 3 | -4.666667 | 0.000000 | 0.000000 | 0 | 0 | 0 |

## Evidence limits

Missing entry Open produces no entry, C1 or P&L; no later substitution. Excluded positions retain known entry evidence and unknown outcomes; same-day entries are blocked. Counts and fractions describe possible selection bias, especially CNY. Incomplete coverage also exists on days without an exclusion. Closed-only DD follows resolved trade order and is conditional.
No USD N10/GLDRUBF/IMOEXF evaluation, 2024+ reads, Robustness, WF, TRUE OOS, LIVE, portfolio sizing, merge or auto-merge. Frozen Baselines, Master Registry, TradingSystemLab and Draft #472 remain unchanged. STOP after one Draft PR.
