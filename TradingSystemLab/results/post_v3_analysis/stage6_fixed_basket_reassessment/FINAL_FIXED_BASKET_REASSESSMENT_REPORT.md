# Final Fixed-Basket Production Reassessment

## Provenance

- Source main used for the original evidence: `c0dfcc9397f0fb825b3937cfc06fcb7a8fde12e8`.
- PR #255 head: `fd7c4e6659278953bc57295d0b62a70b630a3c80`.
- PR #255 merge and fix base: `664e63ff6f598dd594523c19690ac3f1b938c16c`.
- Existing production identity `PROD_STAGE6_83C7B31BB42C` is unchanged. No Stage 7 action occurred.

## Exact frozen six-basket registry

| basket   | members                        | path      | strategy_identity   | configuration      | parameter_hash                                                   | cost_contract       |   research_tick | current_stage6   |
|:---------|:-------------------------------|:----------|:--------------------|:-------------------|:-----------------------------------------------------------------|:--------------------|----------------:|:-----------------|
| A        | CNYRUBF+GLDRUBF+IMOEXF         | canonical | T3_H1_candidate_v3  | T3-H1-4e73cdb77246 | 4e73cdb77246cb07b5953160b9fc0ab36bfd4bd6d9a7f7faaae7e6e392ee340a | CORRECTED_SINGLE_C1 |        0.001000 | False            |
| B        | CNYRUBF+GLDRUBF+IMOEXF         | TRAIL1    | T3_H1_candidate_v3  | T3-H1-4e73cdb77246 | 4e73cdb77246cb07b5953160b9fc0ab36bfd4bd6d9a7f7faaae7e6e392ee340a | CORRECTED_SINGLE_C1 |        0.001000 | True             |
| C        | USDRUBF+CNYRUBF+GLDRUBF+IMOEXF | canonical | T3_H1_candidate_v3  | T3-H1-4e73cdb77246 | 4e73cdb77246cb07b5953160b9fc0ab36bfd4bd6d9a7f7faaae7e6e392ee340a | CORRECTED_SINGLE_C1 |        0.001000 | False            |
| D        | USDRUBF+CNYRUBF+GLDRUBF+IMOEXF | TRAIL1    | T3_H1_candidate_v3  | T3-H1-4e73cdb77246 | 4e73cdb77246cb07b5953160b9fc0ab36bfd4bd6d9a7f7faaae7e6e392ee340a | CORRECTED_SINGLE_C1 |        0.001000 | False            |
| E        | USDRUBF+GLDRUBF+IMOEXF         | canonical | T3_H1_candidate_v3  | T3-H1-4e73cdb77246 | 4e73cdb77246cb07b5953160b9fc0ab36bfd4bd6d9a7f7faaae7e6e392ee340a | CORRECTED_SINGLE_C1 |        0.001000 | False            |
| F        | USDRUBF+GLDRUBF+IMOEXF         | TRAIL1    | T3_H1_candidate_v3  | T3-H1-4e73cdb77246 | 4e73cdb77246cb07b5953160b9fc0ab36bfd4bd6d9a7f7faaae7e6e392ee340a | CORRECTED_SINGLE_C1 |        0.001000 | False            |

## Annual hard-gate table

| basket   | path      | lifecycle           |   year |     net_R |   positive_months |   available_months |   positive_month_share |   median_monthly_R |   monthly_std_R |   worst_month_R |   best_month_R |   longest_negative_month_streak | annual_gate   |
|:---------|:----------|:--------------------|-------:|----------:|------------------:|-------------------:|-----------------------:|-------------------:|----------------:|----------------:|---------------:|--------------------------------:|:--------------|
| A        | canonical | baseline            |   2023 |  0.549982 |                 4 |                 12 |               0.333333 |          -0.510278 |        1.773720 |       -2.569743 |       3.724184 |                               4 | True          |
| A        | canonical | baseline            |   2024 | 50.750000 |                 9 |                 12 |               0.750000 |           3.531451 |        4.662420 |       -0.804197 |      15.471134 |                               1 | True          |
| A        | canonical | walk_forward        |   2024 | 26.643396 |                 5 |                 12 |               0.416667 |           0.000000 |        4.404272 |       -0.758132 |      15.471134 |                               1 | True          |
| A        | canonical | historical_true_oos |   2025 | 29.217577 |                 7 |                 12 |               0.583333 |           0.054258 |        5.882750 |       -3.419461 |      19.356999 |                               2 | True          |
| A        | canonical | historical_true_oos |   2026 | 33.071561 |                 5 |                  9 |               0.555556 |           0.505255 |        6.559688 |       -3.643717 |      17.912033 |                               1 | True          |
| B        | TRAIL1    | baseline            |   2023 | -3.450404 |                 4 |                 12 |               0.333333 |          -0.045215 |        1.984705 |       -3.664494 |       3.329894 |                               4 | False         |
| B        | TRAIL1    | baseline            |   2024 | 58.873709 |                10 |                 12 |               0.833333 |           4.070125 |        4.864498 |       -0.709256 |      14.281930 |                               1 | True          |
| B        | TRAIL1    | walk_forward        |   2024 | 32.968262 |                 5 |                 12 |               0.416667 |           0.000000 |        4.425221 |       -1.070970 |      14.281930 |                               1 | True          |
| B        | TRAIL1    | historical_true_oos |   2025 | 32.158460 |                 8 |                 12 |               0.666667 |           1.011366 |        5.826034 |       -3.757058 |      19.722782 |                               2 | True          |
| B        | TRAIL1    | historical_true_oos |   2026 | 32.908838 |                 6 |                  9 |               0.666667 |           0.411104 |        6.418823 |       -3.025172 |      19.484130 |                               1 | True          |
| C        | canonical | baseline            |   2023 | 13.698604 |                 6 |                 12 |               0.500000 |           0.235903 |        3.566141 |       -2.632438 |       8.039008 |                               2 | True          |
| C        | canonical | baseline            |   2024 | 60.011015 |                 8 |                 12 |               0.666667 |           4.159130 |        6.335595 |       -1.623390 |      20.945378 |                               1 | True          |
| C        | canonical | walk_forward        |   2024 | 38.729866 |                 6 |                 12 |               0.500000 |           0.107824 |        6.152716 |       -1.577325 |      20.945378 |                               1 | True          |
| C        | canonical | historical_true_oos |   2025 | 36.347441 |                 7 |                 12 |               0.583333 |           0.054258 |        8.422828 |       -4.967293 |      27.534141 |                               2 | True          |
| C        | canonical | historical_true_oos |   2026 | 49.388980 |                 6 |                  9 |               0.666667 |           0.844706 |        9.459820 |       -4.069529 |      25.875841 |                               1 | True          |
| D        | TRAIL1    | baseline            |   2023 | 11.927668 |                 5 |                 12 |               0.416667 |          -0.157602 |        3.634584 |       -3.354836 |       7.113136 |                               2 | True          |
| D        | TRAIL1    | baseline            |   2024 | 69.995783 |                 9 |                 12 |               0.750000 |           4.746291 |        6.246166 |       -1.464951 |      19.756173 |                               2 | True          |
| D        | TRAIL1    | walk_forward        |   2024 | 46.825228 |                 6 |                 12 |               0.500000 |           0.578297 |        6.116407 |       -2.073796 |      19.756173 |                               1 | True          |
| D        | TRAIL1    | historical_true_oos |   2025 | 41.617436 |                 8 |                 12 |               0.666667 |           0.837784 |        8.361818 |       -4.330600 |      28.660396 |                               2 | True          |
| D        | TRAIL1    | historical_true_oos |   2026 | 46.287029 |                 6 |                  9 |               0.666667 |           1.417292 |        9.342324 |       -4.028533 |      26.815524 |                               1 | True          |
| E        | canonical | baseline            |   2023 | 12.764529 |                 7 |                 12 |               0.583333 |           1.022707 |        2.236959 |       -1.894809 |       5.350569 |                               2 | True          |
| E        | canonical | baseline            |   2024 | 38.162621 |                 9 |                 12 |               0.750000 |           2.875363 |        3.683414 |       -2.056420 |      10.192494 |                               2 | True          |
| E        | canonical | walk_forward        |   2024 | 20.663151 |                 6 |                 12 |               0.500000 |           0.340823 |        2.786264 |       -0.802509 |       8.790892 |                               1 | True          |
| E        | canonical | historical_true_oos |   2025 | 26.332705 |                 6 |                 12 |               0.500000 |           0.229299 |        6.288684 |       -4.425901 |      19.709203 |                               2 | True          |
| E        | canonical | historical_true_oos |   2026 | 36.638134 |                 4 |                  9 |               0.444444 |          -0.004945 |        7.247604 |       -3.682062 |      20.123788 |                               2 | True          |
| F        | TRAIL1    | baseline            |   2023 | 12.815822 |                 7 |                 12 |               0.583333 |           0.580422 |        2.326391 |       -2.048367 |       5.768639 |                               2 | True          |
| F        | TRAIL1    | baseline            |   2024 | 47.014161 |                10 |                 12 |               0.833333 |           3.877497 |        3.764698 |       -2.579792 |       9.742219 |                               2 | True          |
| F        | TRAIL1    | walk_forward        |   2024 | 26.139516 |                 7 |                 12 |               0.583333 |           0.905280 |        2.902217 |       -1.038231 |       8.299584 |                               1 | True          |
| F        | TRAIL1    | historical_true_oos |   2025 | 30.503246 |                 7 |                 12 |               0.583333 |           0.799169 |        6.910547 |       -5.002539 |      22.540752 |                               2 | True          |
| F        | TRAIL1    | historical_true_oos |   2026 | 37.248516 |                 4 |                  9 |               0.444444 |          -0.219873 |        7.430014 |       -3.003456 |      21.721323 |                               2 | True          |

## Lifecycle risk/recovery table

| basket   | path      | lifecycle           |   trades |     net_R |   trade_level_max_DD_R |   monthly_equity_max_DD_R |   recovery_factor |
|:---------|:----------|:--------------------|---------:|----------:|-----------------------:|--------------------------:|------------------:|
| A        | canonical | baseline            |      118 | 51.299982 |              -6.490863 |                 -6.224979 |          7.903414 |
| A        | canonical | walk_forward        |       52 | 26.643396 |              -2.281748 |                 -0.758132 |         11.676747 |
| A        | canonical | historical_true_oos |      150 | 62.289138 |              -7.153150 |                 -5.434723 |          8.707931 |
| B        | TRAIL1    | baseline            |      113 | 55.423305 |             -12.108415 |                -10.069951 |          4.577255 |
| B        | TRAIL1    | walk_forward        |       49 | 32.968262 |              -3.076781 |                 -1.070970 |         10.715181 |
| B        | TRAIL1    | historical_true_oos |      140 | 65.067298 |              -8.575350 |                 -5.020915 |          7.587713 |
| C        | canonical | baseline            |      181 | 73.709619 |              -5.589595 |                 -4.563846 |         13.186934 |
| C        | canonical | walk_forward        |       66 | 38.729866 |              -2.300388 |                 -1.577325 |         16.836232 |
| C        | canonical | historical_true_oos |      199 | 85.736421 |             -11.719118 |                 -8.843879 |          7.315945 |
| D        | TRAIL1    | baseline            |      171 | 81.923451 |             -10.688186 |                 -9.260095 |          7.664860 |
| D        | TRAIL1    | walk_forward        |       63 | 46.825228 |              -2.438416 |                 -2.073796 |         19.203137 |
| D        | TRAIL1    | historical_true_oos |      184 | 87.904465 |             -14.451470 |                 -7.857077 |          6.082735 |
| E        | canonical | baseline            |      130 | 50.927150 |              -3.525443 |                 -2.898422 |         14.445603 |
| E        | canonical | walk_forward        |       50 | 20.663151 |              -2.075429 |                 -0.802509 |          9.956085 |
| E        | canonical | historical_true_oos |      148 | 62.970839 |             -10.225463 |                 -7.387814 |          6.158239 |
| F        | TRAIL1    | baseline            |      123 | 59.829983 |              -5.669188 |                 -5.153166 |         10.553536 |
| F        | TRAIL1    | walk_forward        |       49 | 26.139516 |              -2.004171 |                 -1.038231 |         13.042561 |
| F        | TRAIL1    | historical_true_oos |      134 | 67.751762 |             -11.866656 |                 -7.604138 |          5.709423 |

## Full monthly Baseline 2023 A–F

| Basket   |      Jan |       Feb |       Mar |      Apr |      May |      Jun |       Jul |      Aug |       Sep |       Oct |       Nov |       Dec |     Total |
|:---------|---------:|----------:|----------:|---------:|---------:|---------:|----------:|---------:|----------:|----------:|----------:|----------:|----------:|
| A        | 0.000000 | -0.594015 | -0.426541 | 3.724184 | 2.437394 | 1.633938 | -2.569743 | 1.284662 | -1.200308 | -1.000713 | -0.971689 | -1.767188 |  0.549982 |
| B        | 0.000000 | -0.042215 | -0.048216 | 3.329894 | 2.437394 | 0.663620 | -3.035069 | 1.200489 | -2.013649 | -1.306469 | -0.971689 | -3.664494 | -3.450404 |
| C        | 0.000000 | -2.488824 | -1.430154 | 8.039008 | 4.636650 | 3.809423 | -2.021883 | 6.635231 | -1.931409 | -2.632438 |  0.471806 |  0.611194 | 13.698604 |
| D        | 0.000000 | -0.315204 | -1.051829 | 7.113136 | 4.636650 | 4.396888 | -2.636329 | 6.969128 | -3.015629 | -3.354836 |  0.471806 | -1.286113 | 11.927668 |
| E        | 0.000000 | -1.894809 | -1.003613 | 4.314824 | 2.199256 | 2.175485 |  0.547860 | 5.350569 | -1.166867 | -1.631725 |  1.497555 |  2.375995 | 12.764529 |
| F        | 0.000000 | -0.272990 | -1.003613 | 3.783243 | 2.199256 | 3.733269 |  0.398740 | 5.768639 | -2.002012 | -2.048367 |  1.497555 |  0.762103 | 12.815822 |

 Zero-trade available months are numeric `0.000000` (`NO_TRADES`); unavailable future months are absent (`NOT_YET_AVAILABLE`).

## Full monthly Baseline 2024 A–F

| Basket   |       Jan |       Feb |      Mar |      Apr |       May |       Jun |      Jul |       Aug |      Sep |      Oct |       Nov |       Dec |     Total |
|:---------|----------:|----------:|---------:|---------:|----------:|----------:|---------:|----------:|---------:|---------:|----------:|----------:|----------:|
| A        |  2.405642 | -0.804197 | 4.434861 | 6.456562 |  1.266643 | 15.471134 | 3.796154 | -0.170873 | 3.471587 | 3.591314 | 11.276140 | -0.444967 | 50.750000 |
| B        | -0.279070 |  0.392454 | 8.609751 | 8.182880 |  2.535336 | 14.281930 | 3.944499 |  0.295132 | 4.497563 | 4.195751 | 12.926740 | -0.709256 | 58.873709 |
| C        |  1.609407 | -1.623390 | 5.567329 | 5.307423 | -0.102864 | 20.945378 | 3.796154 | -0.196445 | 4.522106 | 5.721999 | 14.527019 | -0.063101 | 60.011015 |
| D        | -1.464951 | -0.610372 | 9.742219 | 6.092617 |  2.762398 | 19.756173 | 3.944499 |  2.352620 | 5.548082 | 6.326436 | 15.873452 | -0.327390 | 69.995783 |
| E        | -0.774772 | -2.056420 | 5.567329 | 3.025300 | -0.610293 |  8.790892 | 3.796154 |  0.956086 | 2.725425 | 5.868780 | 10.192494 |  0.681646 | 38.162621 |
| F        | -2.579792 | -0.782653 | 9.742219 | 3.810495 |  1.609338 |  8.299584 | 3.944499 |  4.404034 | 2.725425 | 5.536689 |  9.622677 |  0.681646 | 47.014161 |

 Zero-trade available months are numeric `0.000000` (`NO_TRADES`); unavailable future months are absent (`NOT_YET_AVAILABLE`).

## Full monthly Walk Forward 2024 A–F

| Basket   |      Jan |       Feb |      Mar |      Apr |       May |       Jun |      Jul |       Aug |      Sep |      Oct |       Nov |       Dec |     Total |
|:---------|---------:|----------:|---------:|---------:|----------:|----------:|---------:|----------:|---------:|---------:|----------:|----------:|----------:|
| A        | 0.000000 | -0.758132 | 1.045283 | 0.000000 |  2.948478 | 15.471134 | 0.000000 | -0.537171 | 3.471587 | 0.000000 |  5.447184 | -0.444967 | 26.643396 |
| B        | 0.000000 | -1.070970 | 5.220173 | 0.000000 |  4.602308 | 14.281930 | 0.000000 | -0.951270 | 4.497563 | 0.000000 |  7.097785 | -0.709256 | 32.968262 |
| C        | 0.000000 | -1.577325 | 2.177751 | 0.000000 |  2.096031 | 20.945378 | 0.000000 |  0.215648 | 4.522106 | 0.000000 | 10.413379 | -0.063101 | 38.729866 |
| D        | 0.000000 | -2.073796 | 6.352641 | 0.000000 |  4.348944 | 19.756173 | 0.000000 |  1.156593 | 5.548082 | 0.000000 | 12.063980 | -0.327390 | 46.825228 |
| E        | 0.000000 | -0.802509 | 2.177751 | 0.000000 | -0.093233 |  8.790892 | 0.000000 |  1.104326 | 2.725425 | 0.000000 |  6.078854 |  0.681646 | 20.663151 |
| F        | 0.000000 | -1.038231 | 6.352641 | 0.000000 |  1.128913 |  8.299584 | 0.000000 |  2.176334 | 2.725425 | 0.000000 |  5.813205 |  0.681646 | 26.139516 |

 Zero-trade available months are numeric `0.000000` (`NO_TRADES`); unavailable future months are absent (`NOT_YET_AVAILABLE`).

## Full monthly Historical TRUE OOS 2025 A–F

| Basket   |      Jan |       Feb |      Mar |       Apr |      May |       Jun |      Jul |      Aug |       Sep |       Oct |       Nov |       Dec |     Total |
|:---------|---------:|----------:|---------:|----------:|---------:|----------:|---------:|---------:|----------:|----------:|----------:|----------:|----------:|
| A        | 0.000000 |  0.019513 | 1.549312 | -0.370630 | 1.729743 | -0.822340 | 5.146070 | 0.089003 | 19.356999 |  7.954630 | -3.419461 | -2.015262 | 29.217577 |
| B        | 0.000000 | -0.797897 | 0.759777 |  1.594727 | 1.729743 |  0.805100 | 4.322920 | 1.217632 | 19.722782 |  7.824590 | -3.757058 | -1.263857 | 32.158460 |
| C        | 0.000000 |  0.019513 | 2.218406 | -2.493074 | 1.557878 | -0.822340 | 7.250135 | 0.089003 | 27.534141 |  9.837657 | -4.967293 | -3.876586 | 36.347441 |
| D        | 0.000000 | -0.797897 | 2.630702 |  0.870468 | 0.727444 |  0.805100 | 5.509389 | 1.217632 | 28.660396 |  9.560526 | -3.235725 | -4.330600 | 41.617436 |
| E        | 0.000000 | -1.182644 | 0.458598 | -0.415353 | 1.557878 |  0.000000 | 2.567921 | 0.823987 | 19.709203 | 10.200929 | -4.425901 | -2.961913 | 26.332705 |
| F        | 0.000000 | -2.000055 | 0.870894 |  2.908615 | 0.727444 |  0.000000 | 2.154918 | 1.217632 | 22.540752 |  9.564314 | -2.478731 | -5.002539 | 30.503246 |

 Zero-trade available months are numeric `0.000000` (`NO_TRADES`); unavailable future months are absent (`NOT_YET_AVAILABLE`).

## Full monthly Historical TRUE OOS 2026 YTD A–F

| Basket   |      Jan |       Feb |       Mar |       Apr |       May |       Jun |       Jul |       Aug |       Sep |     Total |
|:---------|---------:|----------:|----------:|----------:|----------:|----------:|----------:|----------:|----------:|----------:|
| A        | 6.466511 | -1.518095 |  6.479408 |  0.505255 | -0.545146 |  9.208760 | -3.643717 | 17.912033 | -1.793449 | 33.071561 |
| B        | 5.744688 | -3.025172 |  5.467930 |  0.411104 |  0.272600 |  6.126952 | -1.256067 | 19.484130 | -0.317327 | 32.908838 |
| C        | 6.118757 | -2.230329 | 14.339700 |  0.844706 |  0.379841 | 11.425598 | -4.069529 | 25.875841 | -3.295605 | 49.388980 |
| D        | 3.737781 | -4.028533 | 13.328223 |  0.436119 |  1.417292 |  9.162603 | -2.258080 | 26.815524 | -2.323899 | 46.287029 |
| E        | 5.261564 | -1.205252 |  9.999774 | -0.004945 | -0.810919 |  8.447586 | -3.682062 | 20.123788 | -1.491401 | 36.638134 |
| F        | 2.880588 | -3.003456 |  9.769030 | -0.413533 | -0.219873 |  8.037077 | -1.243871 | 21.721323 | -0.278769 | 37.248516 |

 Zero-trade available months are numeric `0.000000` (`NO_TRADES`); unavailable future months are absent (`NOT_YET_AVAILABLE`).

## Rolling 3M/6M/12M comparison

Only complete consecutive windows are included.

| basket   | path      | lifecycle           |   complete_3M_windows |   worst_3M_R |   final_3M_R |   complete_6M_windows |   worst_6M_R |   final_6M_R |   median_6M_R |   complete_12M_windows |   worst_12M_R |   final_12M_R |
|:---------|:----------|:--------------------|----------------------:|-------------:|-------------:|----------------------:|-------------:|-------------:|--------------:|-----------------------:|--------------:|--------------:|
| A        | canonical | baseline            |                    22 |    -3.739589 |    14.422487 |                    19 |    -6.224979 |    21.519355 |      6.774961 |                     13 |      0.549982 |     50.750000 |
| A        | canonical | historical_true_oos |                    19 |     0.536774 |    12.474868 |                    16 |     2.105598 |    21.643737 |     21.120215 |                     10 |     29.217577 |     35.591468 |
| A        | canonical | walk_forward        |                    10 |     0.287151 |     5.002217 |                     7 |     7.936633 |     7.936633 |     18.927724 |                      1 |     26.643396 |     26.643396 |
| B        | TRAIL1    | baseline            |                    22 |    -5.942652 |    16.413236 |                    19 |    -9.790881 |    25.150430 |      6.340477 |                     13 |     -3.729475 |     58.873709 |
| B        | TRAIL1    | historical_true_oos |                    19 |    -0.038120 |    17.910736 |                    16 |     3.577635 |    24.721392 |     19.859747 |                     10 |     32.158460 |     35.712513 |
| B        | TRAIL1    | walk_forward        |                    10 |     3.546293 |     6.388529 |                     7 |     9.934822 |     9.934822 |     23.033441 |                      1 |     32.968262 |     32.968262 |
| C        | canonical | baseline            |                    22 |    -4.092040 |    20.185917 |                    19 |    -3.494830 |    28.307732 |     12.566103 |                     13 |     13.698604 |     60.011015 |
| C        | canonical | historical_true_oos |                    19 |    -2.725122 |    18.510708 |                    16 |     0.480383 |    31.160853 |     31.019563 |                     10 |     36.347441 |     50.382759 |
| C        | canonical | walk_forward        |                    10 |     0.600426 |    10.350278 |                     7 |    15.088032 |    15.088032 |     25.434807 |                      1 |     38.729866 |     38.729866 |
| D        | TRAIL1    | baseline            |                    22 |    -5.898659 |    21.872498 |                    19 |    -9.260095 |    33.717699 |     15.235799 |                     13 |     10.167549 |     69.995783 |
| D        | TRAIL1    | historical_true_oos |                    19 |    -4.621352 |    22.233545 |                    16 |     4.235817 |    33.249558 |     27.208664 |                     10 |     41.617436 |     48.281230 |
| D        | TRAIL1    | walk_forward        |                    10 |     4.278845 |    11.736590 |                     7 |    18.441265 |    18.441265 |     30.809793 |                      1 |     46.825228 |     46.825228 |
| E        | canonical | baseline            |                    22 |    -2.898422 |    16.742920 |                    19 |    -1.756235 |    24.220585 |      9.634987 |                     13 |     11.828146 |     38.162621 |
| E        | canonical | historical_true_oos |                    19 |    -2.126250 |    14.950325 |                    16 |     0.418479 |    22.582048 |     22.134928 |                     10 |     26.332705 |     39.451249 |
| E        | canonical | walk_forward        |                    10 |     1.375242 |     6.760500 |                     7 |    10.072901 |    10.590250 |     11.979736 |                      1 |     20.663151 |     20.663151 |
| F        | TRAIL1    | baseline            |                    22 |    -2.600342 |    15.841012 |                    19 |    -5.153166 |    26.914970 |     12.561711 |                     13 |      9.726366 |     47.014161 |
| F        | TRAIL1    | historical_true_oos |                    19 |    -5.125407 |    20.198683 |                    16 |     1.751360 |    27.602354 |     20.775381 |                     10 |     30.503246 |     39.331560 |
| F        | TRAIL1    | walk_forward        |                    10 |     4.901758 |     6.494851 |                     7 |    11.396609 |    11.396609 |     14.742907 |                      1 |     26.139516 |     26.139516 |

## Monthly concentration comparison

Descriptive only; no threshold or selection rank uses this table.

| basket   | path      | lifecycle           |   total_net_R |   best_month_R |   best_month_share_of_positive_monthly_R |   top_3_positive_months_R |   top_3_share_of_positive_monthly_R |   worst_month_R |   bottom_3_months_R |
|:---------|:----------|:--------------------|--------------:|---------------:|-----------------------------------------:|--------------------------:|------------------------------------:|----------------:|--------------------:|
| A        | canonical | baseline            |     51.299982 |      15.471134 |                                 0.252589 |                 33.203836 |                            0.542102 |       -2.569743 |           -5.537238 |
| A        | canonical | historical_true_oos |     62.289138 |      19.356999 |                                 0.253307 |                 46.477792 |                            0.608211 |       -3.643717 |           -9.078440 |
| A        | canonical | walk_forward        |     26.643396 |      15.471134 |                                 0.545072 |                 24.389906 |                            0.859294 |       -0.758132 |           -1.740270 |
| B        | TRAIL1    | baseline            |     55.423305 |      14.281930 |                                 0.211605 |                 35.818421 |                            0.530695 |       -3.664494 |           -8.713212 |
| B        | TRAIL1    | historical_true_oos |     65.067298 |      19.722782 |                                 0.261282 |                 47.031502 |                            0.623060 |       -3.757058 |           -8.046087 |
| B        | TRAIL1    | walk_forward        |     32.968262 |      14.281930 |                                 0.400057 |                 26.599887 |                            0.745100 |       -1.070970 |           -2.731496 |
| C        | canonical | baseline            |     73.709619 |      20.945378 |                                 0.242985 |                 43.511404 |                            0.504772 |       -2.632438 |           -7.143145 |
| C        | canonical | historical_true_oos |     85.736421 |      27.534141 |                                 0.256153 |                 67.749683 |                            0.630281 |       -4.967293 |          -12.913407 |
| C        | canonical | walk_forward        |     38.729866 |      20.945378 |                                 0.518831 |                 35.880863 |                            0.888794 |       -1.577325 |           -1.640426 |
| D        | TRAIL1    | baseline            |     81.923451 |      19.756173 |                                 0.205823 |                 45.371844 |                            0.472692 |       -3.354836 |           -9.006794 |
| D        | TRAIL1    | historical_true_oos |     87.904465 |      28.660396 |                                 0.273271 |                 68.804142 |                            0.656032 |       -4.330600 |          -11.594858 |
| D        | TRAIL1    | walk_forward        |     46.825228 |      19.756173 |                                 0.401333 |                 38.172794 |                            0.775453 |       -2.073796 |           -2.401186 |
| E        | canonical | baseline            |     50.927150 |      10.192494 |                                 0.169689 |                 24.852167 |                            0.413750 |       -2.056420 |           -5.582954 |
| E        | canonical | historical_true_oos |     62.970839 |      20.123788 |                                 0.254245 |                 50.033920 |                            0.632131 |       -4.425901 |          -11.069875 |
| E        | canonical | walk_forward        |     20.663151 |       8.790892 |                                 0.407762 |                 17.595171 |                            0.816144 |       -0.802509 |           -0.895742 |
| F        | TRAIL1    | baseline            |     59.829983 |       9.742219 |                                 0.142182 |                 27.664480 |                            0.403747 |       -2.579792 |           -6.630171 |
| F        | TRAIL1    | historical_true_oos |     67.751762 |      22.540752 |                                 0.273577 |                 54.031106 |                            0.655776 |       -5.002539 |          -10.484725 |
| F        | TRAIL1    | walk_forward        |     26.139516 |       8.299584 |                                 0.305382 |                 20.465430 |                            0.753022 |       -1.038231 |           -1.038231 |

## Instrument contribution

| basket   | path      | lifecycle           |   year | instrument   |   instrument_net_R |   share_of_positive_instrument_R | largest_positive_contributor   | largest_negative_contributor   |   leave_one_out_net_R | sign_changes_when_removed   |
|:---------|:----------|:--------------------|-------:|:-------------|-------------------:|---------------------------------:|:-------------------------------|:-------------------------------|----------------------:|:----------------------------|
| A        | canonical | baseline            |   2023 | CNYRUBF      |           0.934075 |                         1.000000 | CNYRUBF                        | GLDRUBF                        |             -0.384093 | True                        |
| A        | canonical | baseline            |   2023 | GLDRUBF      |          -0.384093 |                         0.000000 | CNYRUBF                        | GLDRUBF                        |              0.934075 | False                       |
| A        | canonical | baseline            |   2023 | IMOEXF       |           0.000000 |                         0.000000 | CNYRUBF                        | GLDRUBF                        |              0.549982 | False                       |
| A        | canonical | baseline            |   2024 | CNYRUBF      |          21.848394 |                         0.430510 | CNYRUBF                        | GLDRUBF                        |             28.901606 | False                       |
| A        | canonical | baseline            |   2024 | GLDRUBF      |          10.826715 |                         0.213334 | CNYRUBF                        | GLDRUBF                        |             39.923285 | False                       |
| A        | canonical | baseline            |   2024 | IMOEXF       |          18.074892 |                         0.356155 | CNYRUBF                        | GLDRUBF                        |             32.675109 | False                       |
| A        | canonical | walk_forward        |   2024 | CNYRUBF      |          18.066715 |                         0.678094 | CNYRUBF                        | GLDRUBF                        |              8.576681 | False                       |
| A        | canonical | walk_forward        |   2024 | GLDRUBF      |           0.224714 |                         0.008434 | CNYRUBF                        | GLDRUBF                        |             26.418682 | False                       |
| A        | canonical | walk_forward        |   2024 | IMOEXF       |           8.351967 |                         0.313472 | CNYRUBF                        | GLDRUBF                        |             18.291429 | False                       |
| A        | canonical | historical_true_oos |   2025 | CNYRUBF      |          10.014736 |                         0.342764 | GLDRUBF                        | IMOEXF                         |             19.202841 | False                       |
| A        | canonical | historical_true_oos |   2025 | GLDRUBF      |          15.377694 |                         0.526317 | GLDRUBF                        | IMOEXF                         |             13.839883 | False                       |
| A        | canonical | historical_true_oos |   2025 | IMOEXF       |           3.825147 |                         0.130919 | GLDRUBF                        | IMOEXF                         |             25.392430 | False                       |
| A        | canonical | historical_true_oos |   2026 | CNYRUBF      |          12.750847 |                         0.379788 | GLDRUBF                        | IMOEXF                         |             20.320714 | False                       |
| A        | canonical | historical_true_oos |   2026 | GLDRUBF      |          20.822756 |                         0.620212 | GLDRUBF                        | IMOEXF                         |             12.248805 | False                       |
| A        | canonical | historical_true_oos |   2026 | IMOEXF       |          -0.502042 |                         0.000000 | GLDRUBF                        | IMOEXF                         |             33.573603 | False                       |
| B        | TRAIL1    | baseline            |   2023 | CNYRUBF      |          -0.888154 |                       nan        | IMOEXF                         | GLDRUBF                        |             -2.562251 | False                       |
| B        | TRAIL1    | baseline            |   2023 | GLDRUBF      |          -2.562251 |                       nan        | IMOEXF                         | GLDRUBF                        |             -0.888154 | False                       |
| B        | TRAIL1    | baseline            |   2023 | IMOEXF       |           0.000000 |                       nan        | IMOEXF                         | GLDRUBF                        |             -3.450404 | False                       |
| B        | TRAIL1    | baseline            |   2024 | CNYRUBF      |          22.981622 |                         0.390355 | CNYRUBF                        | GLDRUBF                        |             35.892087 | False                       |
| B        | TRAIL1    | baseline            |   2024 | GLDRUBF      |          13.348402 |                         0.226729 | CNYRUBF                        | GLDRUBF                        |             45.525307 | False                       |
| B        | TRAIL1    | baseline            |   2024 | IMOEXF       |          22.543685 |                         0.382916 | CNYRUBF                        | GLDRUBF                        |             36.330024 | False                       |
| B        | TRAIL1    | walk_forward        |   2024 | CNYRUBF      |          20.685711 |                         0.627443 | CNYRUBF                        | GLDRUBF                        |             12.282551 | False                       |
| B        | TRAIL1    | walk_forward        |   2024 | GLDRUBF      |           4.919482 |                         0.149219 | CNYRUBF                        | GLDRUBF                        |             28.048780 | False                       |
| B        | TRAIL1    | walk_forward        |   2024 | IMOEXF       |           7.363069 |                         0.223338 | CNYRUBF                        | GLDRUBF                        |             25.605193 | False                       |
| B        | TRAIL1    | historical_true_oos |   2025 | CNYRUBF      |          11.114190 |                         0.345607 | GLDRUBF                        | IMOEXF                         |             21.044270 | False                       |
| B        | TRAIL1    | historical_true_oos |   2025 | GLDRUBF      |          12.104852 |                         0.376413 | GLDRUBF                        | IMOEXF                         |             20.053608 | False                       |
| B        | TRAIL1    | historical_true_oos |   2025 | IMOEXF       |           8.939418 |                         0.277980 | GLDRUBF                        | IMOEXF                         |             23.219042 | False                       |
| B        | TRAIL1    | historical_true_oos |   2026 | CNYRUBF      |           9.038513 |                         0.274653 | GLDRUBF                        | IMOEXF                         |             23.870325 | False                       |
| B        | TRAIL1    | historical_true_oos |   2026 | GLDRUBF      |          19.622801 |                         0.596278 | GLDRUBF                        | IMOEXF                         |             13.286037 | False                       |
| B        | TRAIL1    | historical_true_oos |   2026 | IMOEXF       |           4.247524 |                         0.129069 | GLDRUBF                        | IMOEXF                         |             28.661314 | False                       |
| C        | canonical | baseline            |   2023 | USDRUBF      |          13.148622 |                         0.933672 | USDRUBF                        | GLDRUBF                        |              0.549982 | False                       |
| C        | canonical | baseline            |   2023 | CNYRUBF      |           0.934075 |                         0.066328 | USDRUBF                        | GLDRUBF                        |             12.764529 | False                       |
| C        | canonical | baseline            |   2023 | GLDRUBF      |          -0.384093 |                         0.000000 | USDRUBF                        | GLDRUBF                        |             14.082697 | False                       |
| C        | canonical | baseline            |   2023 | IMOEXF       |           0.000000 |                         0.000000 | USDRUBF                        | GLDRUBF                        |             13.698604 | False                       |
| C        | canonical | baseline            |   2024 | USDRUBF      |           9.261015 |                         0.154322 | CNYRUBF                        | USDRUBF                        |             50.750000 | False                       |
| C        | canonical | baseline            |   2024 | CNYRUBF      |          21.848394 |                         0.364073 | CNYRUBF                        | USDRUBF                        |             38.162621 | False                       |
| C        | canonical | baseline            |   2024 | GLDRUBF      |          10.826715 |                         0.180412 | CNYRUBF                        | USDRUBF                        |             49.184300 | False                       |
| C        | canonical | baseline            |   2024 | IMOEXF       |          18.074892 |                         0.301193 | CNYRUBF                        | USDRUBF                        |             41.936123 | False                       |
| C        | canonical | walk_forward        |   2024 | USDRUBF      |          12.086470 |                         0.312071 | CNYRUBF                        | GLDRUBF                        |             26.643396 | False                       |
| C        | canonical | walk_forward        |   2024 | CNYRUBF      |          18.066715 |                         0.466480 | CNYRUBF                        | GLDRUBF                        |             20.663151 | False                       |
| C        | canonical | walk_forward        |   2024 | GLDRUBF      |           0.224714 |                         0.005802 | CNYRUBF                        | GLDRUBF                        |             38.505152 | False                       |
| C        | canonical | walk_forward        |   2024 | IMOEXF       |           8.351967 |                         0.215647 | CNYRUBF                        | GLDRUBF                        |             30.377899 | False                       |
| C        | canonical | historical_true_oos |   2025 | USDRUBF      |           7.129864 |                         0.196159 | GLDRUBF                        | IMOEXF                         |             29.217577 | False                       |
| C        | canonical | historical_true_oos |   2025 | CNYRUBF      |          10.014736 |                         0.275528 | GLDRUBF                        | IMOEXF                         |             26.332705 | False                       |
| C        | canonical | historical_true_oos |   2025 | GLDRUBF      |          15.377694 |                         0.423075 | GLDRUBF                        | IMOEXF                         |             20.969747 | False                       |
| C        | canonical | historical_true_oos |   2025 | IMOEXF       |           3.825147 |                         0.105238 | GLDRUBF                        | IMOEXF                         |             32.522294 | False                       |
| C        | canonical | historical_true_oos |   2026 | USDRUBF      |          16.317420 |                         0.327061 | GLDRUBF                        | IMOEXF                         |             33.071561 | False                       |
| C        | canonical | historical_true_oos |   2026 | CNYRUBF      |          12.750847 |                         0.255574 | GLDRUBF                        | IMOEXF                         |             36.638134 | False                       |
| C        | canonical | historical_true_oos |   2026 | GLDRUBF      |          20.822756 |                         0.417365 | GLDRUBF                        | IMOEXF                         |             28.566225 | False                       |
| C        | canonical | historical_true_oos |   2026 | IMOEXF       |          -0.502042 |                         0.000000 | GLDRUBF                        | IMOEXF                         |             49.891022 | False                       |
| D        | TRAIL1    | baseline            |   2023 | USDRUBF      |          15.378072 |                         1.000000 | USDRUBF                        | GLDRUBF                        |             -3.450404 | True                        |
| D        | TRAIL1    | baseline            |   2023 | CNYRUBF      |          -0.888154 |                         0.000000 | USDRUBF                        | GLDRUBF                        |             12.815822 | False                       |
| D        | TRAIL1    | baseline            |   2023 | GLDRUBF      |          -2.562251 |                         0.000000 | USDRUBF                        | GLDRUBF                        |             14.489919 | False                       |
| D        | TRAIL1    | baseline            |   2023 | IMOEXF       |           0.000000 |                         0.000000 | USDRUBF                        | GLDRUBF                        |             11.927668 | False                       |
| D        | TRAIL1    | baseline            |   2024 | USDRUBF      |          11.122074 |                         0.158896 | CNYRUBF                        | USDRUBF                        |             58.873709 | False                       |
| D        | TRAIL1    | baseline            |   2024 | CNYRUBF      |          22.981622 |                         0.328329 | CNYRUBF                        | USDRUBF                        |             47.014161 | False                       |
| D        | TRAIL1    | baseline            |   2024 | GLDRUBF      |          13.348402 |                         0.190703 | CNYRUBF                        | USDRUBF                        |             56.647381 | False                       |
| D        | TRAIL1    | baseline            |   2024 | IMOEXF       |          22.543685 |                         0.322072 | CNYRUBF                        | USDRUBF                        |             47.452098 | False                       |
| D        | TRAIL1    | walk_forward        |   2024 | USDRUBF      |          13.856965 |                         0.295929 | CNYRUBF                        | GLDRUBF                        |             32.968262 | False                       |
| D        | TRAIL1    | walk_forward        |   2024 | CNYRUBF      |          20.685711 |                         0.441764 | CNYRUBF                        | GLDRUBF                        |             26.139516 | False                       |
| D        | TRAIL1    | walk_forward        |   2024 | GLDRUBF      |           4.919482 |                         0.105061 | CNYRUBF                        | GLDRUBF                        |             41.905745 | False                       |
| D        | TRAIL1    | walk_forward        |   2024 | IMOEXF       |           7.363069 |                         0.157246 | CNYRUBF                        | GLDRUBF                        |             39.462159 | False                       |
| D        | TRAIL1    | historical_true_oos |   2025 | USDRUBF      |           9.458976 |                         0.227284 | GLDRUBF                        | IMOEXF                         |             32.158460 | False                       |
| D        | TRAIL1    | historical_true_oos |   2025 | CNYRUBF      |          11.114190 |                         0.267056 | GLDRUBF                        | IMOEXF                         |             30.503246 | False                       |
| D        | TRAIL1    | historical_true_oos |   2025 | GLDRUBF      |          12.104852 |                         0.290860 | GLDRUBF                        | IMOEXF                         |             29.512584 | False                       |
| D        | TRAIL1    | historical_true_oos |   2025 | IMOEXF       |           8.939418 |                         0.214800 | GLDRUBF                        | IMOEXF                         |             32.678018 | False                       |
| D        | TRAIL1    | historical_true_oos |   2026 | USDRUBF      |          13.378191 |                         0.289027 | GLDRUBF                        | IMOEXF                         |             32.908838 | False                       |
| D        | TRAIL1    | historical_true_oos |   2026 | CNYRUBF      |           9.038513 |                         0.195271 | GLDRUBF                        | IMOEXF                         |             37.248516 | False                       |
| D        | TRAIL1    | historical_true_oos |   2026 | GLDRUBF      |          19.622801 |                         0.423937 | GLDRUBF                        | IMOEXF                         |             26.664228 | False                       |
| D        | TRAIL1    | historical_true_oos |   2026 | IMOEXF       |           4.247524 |                         0.091765 | GLDRUBF                        | IMOEXF                         |             42.039505 | False                       |
| E        | canonical | baseline            |   2023 | USDRUBF      |          13.148622 |                         1.000000 | USDRUBF                        | GLDRUBF                        |             -0.384093 | True                        |
| E        | canonical | baseline            |   2023 | GLDRUBF      |          -0.384093 |                         0.000000 | USDRUBF                        | GLDRUBF                        |             13.148622 | False                       |
| E        | canonical | baseline            |   2023 | IMOEXF       |           0.000000 |                         0.000000 | USDRUBF                        | GLDRUBF                        |             12.764529 | False                       |
| E        | canonical | baseline            |   2024 | USDRUBF      |           9.261015 |                         0.242672 | IMOEXF                         | USDRUBF                        |             28.901606 | False                       |
| E        | canonical | baseline            |   2024 | GLDRUBF      |          10.826715 |                         0.283699 | IMOEXF                         | USDRUBF                        |             27.335907 | False                       |
| E        | canonical | baseline            |   2024 | IMOEXF       |          18.074892 |                         0.473628 | IMOEXF                         | USDRUBF                        |             20.087730 | False                       |
| E        | canonical | walk_forward        |   2024 | USDRUBF      |          12.086470 |                         0.584929 | USDRUBF                        | GLDRUBF                        |              8.576681 | False                       |
| E        | canonical | walk_forward        |   2024 | GLDRUBF      |           0.224714 |                         0.010875 | USDRUBF                        | GLDRUBF                        |             20.438437 | False                       |
| E        | canonical | walk_forward        |   2024 | IMOEXF       |           8.351967 |                         0.404196 | USDRUBF                        | GLDRUBF                        |             12.311184 | False                       |
| E        | canonical | historical_true_oos |   2025 | USDRUBF      |           7.129864 |                         0.270761 | GLDRUBF                        | IMOEXF                         |             19.202841 | False                       |
| E        | canonical | historical_true_oos |   2025 | GLDRUBF      |          15.377694 |                         0.583977 | GLDRUBF                        | IMOEXF                         |             10.955011 | False                       |
| E        | canonical | historical_true_oos |   2025 | IMOEXF       |           3.825147 |                         0.145262 | GLDRUBF                        | IMOEXF                         |             22.507558 | False                       |
| E        | canonical | historical_true_oos |   2026 | USDRUBF      |          16.317420 |                         0.439347 | GLDRUBF                        | IMOEXF                         |             20.320714 | False                       |
| E        | canonical | historical_true_oos |   2026 | GLDRUBF      |          20.822756 |                         0.560653 | GLDRUBF                        | IMOEXF                         |             15.815378 | False                       |
| E        | canonical | historical_true_oos |   2026 | IMOEXF       |          -0.502042 |                         0.000000 | GLDRUBF                        | IMOEXF                         |             37.140175 | False                       |
| F        | TRAIL1    | baseline            |   2023 | USDRUBF      |          15.378072 |                         1.000000 | USDRUBF                        | GLDRUBF                        |             -2.562251 | True                        |
| F        | TRAIL1    | baseline            |   2023 | GLDRUBF      |          -2.562251 |                         0.000000 | USDRUBF                        | GLDRUBF                        |             15.378072 | False                       |
| F        | TRAIL1    | baseline            |   2023 | IMOEXF       |           0.000000 |                         0.000000 | USDRUBF                        | GLDRUBF                        |             12.815822 | False                       |
| F        | TRAIL1    | baseline            |   2024 | USDRUBF      |          11.122074 |                         0.236569 | IMOEXF                         | USDRUBF                        |             35.892087 | False                       |
| F        | TRAIL1    | baseline            |   2024 | GLDRUBF      |          13.348402 |                         0.283923 | IMOEXF                         | USDRUBF                        |             33.665759 | False                       |
| F        | TRAIL1    | baseline            |   2024 | IMOEXF       |          22.543685 |                         0.479508 | IMOEXF                         | USDRUBF                        |             24.470476 | False                       |
| F        | TRAIL1    | walk_forward        |   2024 | USDRUBF      |          13.856965 |                         0.530116 | USDRUBF                        | GLDRUBF                        |             12.282551 | False                       |
| F        | TRAIL1    | walk_forward        |   2024 | GLDRUBF      |           4.919482 |                         0.188201 | USDRUBF                        | GLDRUBF                        |             21.220034 | False                       |
| F        | TRAIL1    | walk_forward        |   2024 | IMOEXF       |           7.363069 |                         0.281683 | USDRUBF                        | GLDRUBF                        |             18.776448 | False                       |
| F        | TRAIL1    | historical_true_oos |   2025 | USDRUBF      |           9.458976 |                         0.310097 | GLDRUBF                        | IMOEXF                         |             21.044270 | False                       |
| F        | TRAIL1    | historical_true_oos |   2025 | GLDRUBF      |          12.104852 |                         0.396838 | GLDRUBF                        | IMOEXF                         |             18.398394 | False                       |
| F        | TRAIL1    | historical_true_oos |   2025 | IMOEXF       |           8.939418 |                         0.293064 | GLDRUBF                        | IMOEXF                         |             21.563828 | False                       |
| F        | TRAIL1    | historical_true_oos |   2026 | USDRUBF      |          13.378191 |                         0.359160 | GLDRUBF                        | IMOEXF                         |             23.870325 | False                       |
| F        | TRAIL1    | historical_true_oos |   2026 | GLDRUBF      |          19.622801 |                         0.526808 | GLDRUBF                        | IMOEXF                         |             17.625715 | False                       |
| F        | TRAIL1    | historical_true_oos |   2026 | IMOEXF       |           4.247524 |                         0.114032 | GLDRUBF                        | IMOEXF                         |             33.000992 | False                       |

## Canonical vs TRAIL1 comparison

| instrument_set                              | canonical_basket   | trail1_basket   | trail1_improves_profitability   | trail1_improves_annual_floor   | trail1_reduces_DD   | trail1_improves_recovery   | trail1_improves_positive_month_share   | trail1_introduces_negative_calendar_year   |   chronological_delta_R |   annual_floor_delta_R |
|:--------------------------------------------|:-------------------|:----------------|:--------------------------------|:-------------------------------|:--------------------|:---------------------------|:---------------------------------------|:-------------------------------------------|------------------------:|-----------------------:|
| ('CNYRUBF', 'GLDRUBF', 'IMOEXF')            | A                  | B               | True                            | False                          | False               | False                      | True                                   | True                                       |                6.901483 |              -4.000386 |
| ('USDRUBF', 'CNYRUBF', 'GLDRUBF', 'IMOEXF') | C                  | D               | True                            | False                          | False               | False                      | True                                   | False                                      |               10.381876 |              -1.770936 |
| ('USDRUBF', 'GLDRUBF', 'IMOEXF')            | E                  | F               | True                            | True                           | False               | False                      | True                                   | False                                      |               13.683756 |               0.051293 |

## v1/v3 bar reconciliation

The v1 USD/CNY sources are continuous/perpetual lineages. Common OHLC bars are identical, while timestamp coverage differs; both streams therefore remain `SOURCE_STREAM_SEMANTICALLY_COMPARABLE_BUT_NOT_IDENTICAL`.

| instrument   | v1_first_timestamp        | v1_last_timestamp         |   v1_bars | v3_first_timestamp        | v3_last_timestamp         |   v3_bars |   timestamp_overlap |   timestamps_missing_from_v1 |   timestamps_missing_from_v3 | OHLC_equal_common   |   OHLC_difference_count | context_bar_construction   | timezone_treatment                    | day_reset_semantics          | completed_context_publication   | incomplete_context_exclusion   | donchian_shift_convention   | C1_cost_convention   |   normalized_tick | v3_strategy_source_hash                                          | v3_parameter_hash                                                | determination                                           | lineage_correction                                                               |
|:-------------|:--------------------------|:--------------------------|----------:|:--------------------------|:--------------------------|----------:|--------------------:|-----------------------------:|-----------------------------:|:--------------------|------------------------:|:---------------------------|:--------------------------------------|:-----------------------------|:--------------------------------|:-------------------------------|:----------------------------|:---------------------|------------------:|:-----------------------------------------------------------------|:-----------------------------------------------------------------|:--------------------------------------------------------|:---------------------------------------------------------------------------------|
| USDRUBF      | 2023-01-03 09:00:00+03:00 | 2024-12-30 23:00:00+03:00 |      7487 | 2023-01-03 09:00:00+03:00 | 2024-12-30 23:00:00+03:00 |      7813 |                7482 |                          331 |                            5 | True                |                       0 | H1_TO_COMPLETED_H4_CAUSAL  | OFFSET_AWARE_MOSCOW_TO_UTC_COMPARISON | EXPLICIT_SOURCE_SESSION_DAYS | True                            | True                           | SHIFT_1                     | CORRECTED_SINGLE_C1  |          0.001000 | 840dd3b2cda43fa00259445cd0a22ace6d82e677f4c793028ccc8126f9ad9a8c | 4e73cdb77246cb07b5953160b9fc0ab36bfd4bd6d9a7f7faaae7e6e392ee340a | SOURCE_STREAM_SEMANTICALLY_COMPARABLE_BUT_NOT_IDENTICAL | v1 is perpetual/continuous; Q filenames are file pieces, not quarterly contracts |
| CNYRUBF      | 2023-01-03 09:00:00+03:00 | 2024-12-30 23:00:00+03:00 |      7486 | 2023-01-03 09:00:00+03:00 | 2024-12-30 23:00:00+03:00 |      7816 |                7481 |                          335 |                            5 | True                |                       0 | H1_TO_COMPLETED_H4_CAUSAL  | OFFSET_AWARE_MOSCOW_TO_UTC_COMPARISON | EXPLICIT_SOURCE_SESSION_DAYS | True                            | True                           | SHIFT_1                     | CORRECTED_SINGLE_C1  |          0.001000 | 840dd3b2cda43fa00259445cd0a22ace6d82e677f4c793028ccc8126f9ad9a8c | 4e73cdb77246cb07b5953160b9fc0ab36bfd4bd6d9a7f7faaae7e6e392ee340a | SOURCE_STREAM_SEMANTICALLY_COMPARABLE_BUT_NOT_IDENTICAL | v1 is perpetual/continuous; Q filenames are file pieces, not quarterly contracts |

## v1/v3 exact P&L bridge

The deterministic composite trade key is instrument, direction, normalized UTC entry timestamp, and entry price. Each delta closes as matched delta minus v1-only R plus v3-only R.

| instrument   |   year | trade_key                                                       |   v1_duplicate_key_count |   v3_duplicate_key_count |   matched_trades |   v1_only_trades |   v3_only_trades |   matched_trades_identical_exit |   matched_trades_changed_exit |   v1_net_R |   v3_net_R |   total_delta_v3_minus_v1 |   matched_exit_delta_R |   v1_only_R |   removed_trade_bridge_R |   v3_only_R |   added_trade_bridge_R |   total_reconciliation_error_R |
|:-------------|-------:|:----------------------------------------------------------------|-------------------------:|-------------------------:|-----------------:|-----------------:|-----------------:|--------------------------------:|------------------------------:|-----------:|-----------:|--------------------------:|-----------------------:|------------:|-------------------------:|------------:|-----------------------:|-------------------------------:|
| USDRUBF      |   2023 | instrument+direction+normalized_UTC_entry_timestamp+entry_price |                        0 |                        0 |               26 |                8 |                5 |                               1 |                            25 |  14.343735 |  13.148622 |                 -1.195113 |              -1.934656 |    4.964687 |                -4.964687 |    5.704230 |               5.704230 |                       0.000000 |
| USDRUBF      |   2024 | instrument+direction+normalized_UTC_entry_timestamp+entry_price |                       16 |                        0 |               16 |               28 |               16 |                               0 |                            16 |  28.974036 |   9.261015 |                -19.713021 |              -0.138435 |   23.013595 |               -23.013595 |    3.439010 |               3.439010 |                      -0.000000 |
| CNYRUBF      |   2023 | instrument+direction+normalized_UTC_entry_timestamp+entry_price |                        0 |                        0 |               19 |                8 |                5 |                               1 |                            18 |   4.666636 |   0.934075 |                 -3.732560 |              -0.934611 |    3.247464 |                -3.247464 |    0.449514 |               0.449514 |                      -0.000000 |
| CNYRUBF      |   2024 | instrument+direction+normalized_UTC_entry_timestamp+entry_price |                       17 |                        0 |               13 |               30 |               14 |                               0 |                            13 |  40.472892 |  21.848394 |                -18.624498 |              -2.175605 |   19.649014 |               -19.649014 |    3.200121 |               3.200121 |                      -0.000000 |

- **USDRUBF 2023:** `+14.343735 R` to `+13.148622 R` (`-1.195113 R`): matched trades `-1.934656 R`, v1-only removal `-4.964687 R`, v3-only addition `+5.704230 R`.
- **USDRUBF 2024:** `+28.974036 R` to `+9.261015 R` (`-19.713021 R`): matched trades `-0.138435 R`, v1-only removal `-23.013595 R`, v3-only addition `+3.439010 R`.
- **CNYRUBF 2023:** `+4.666636 R` to `+0.934075 R` (`-3.732560 R`): matched trades `-0.934611 R`, v1-only removal `-3.247464 R`, v3-only addition `+0.449514 R`.
- **CNYRUBF 2024:** `+40.472892 R` to `+21.848394 R` (`-18.624498 R`): matched trades `-2.175605 R`, v1-only removal `-19.649014 R`, v3-only addition `+3.200121 R`.

## Independently recomputed candidate-selection result

| basket   | path      | baseline_2023_positive   | baseline_2024_positive   | wf_2024_positive   | oos_2025_positive   | oos_2026_partial_positive   | all_annual_gates_pass   |   minimum_calendar_period_net_R |   worst_trade_level_DD_R |   minimum_recovery_factor |   chronological_net_R |   positive_month_share |   median_monthly_R |   worst_6M_R |   worst_12M_R |   longest_negative_month_streak |
|:---------|:----------|:-------------------------|:-------------------------|:-------------------|:--------------------|:----------------------------|:------------------------|--------------------------------:|-------------------------:|--------------------------:|----------------------:|-----------------------:|-------------------:|-------------:|--------------:|--------------------------------:|
| A        | canonical | True                     | True                     | True               | True                | True                        | True                    |                        0.549982 |                -7.153150 |                  7.903414 |            113.589120 |               0.526316 |           0.089003 |    -6.224979 |      0.549982 |                               4 |
| B        | TRAIL1    | False                    | True                     | True               | True                | True                        | False                   |                       -3.450404 |               -12.108415 |                  4.577255 |            120.490603 |               0.578947 |           0.663620 |    -9.790881 |     -3.729475 |                               5 |
| C        | canonical | True                     | True                     | True               | True                | True                        | True                    |                       13.698604 |               -11.719118 |                  7.315945 |            159.446041 |               0.578947 |           0.471806 |    -3.494830 |     13.698604 |                               2 |
| D        | TRAIL1    | True                     | True                     | True               | True                | True                        | True                    |                       11.927668 |               -14.451470 |                  6.082735 |            169.827916 |               0.596491 |           1.156593 |    -9.260095 |     10.167549 |                               3 |
| E        | canonical | True                     | True                     | True               | True                | True                        | True                    |                       12.764529 |               -10.225463 |                  6.158239 |            113.897989 |               0.561404 |           0.681646 |    -1.756235 |     11.828146 |                               2 |
| F        | TRAIL1    | True                     | True                     | True               | True                | True                        | True                    |                       12.815822 |               -11.866656 |                  5.709423 |            127.581745 |               0.614035 |           1.128913 |    -5.153166 |      9.726366 |                               2 |

Annual hard-gate failures: **B**. Eligible baskets: **A, C, D, E, F**. Preferred basket under the unchanged hierarchy: **C**. The auditor independently reconstructs and compares this result.

## Limitations

Historical 2025–2026 results are revealed evidence, not fresh OOS; 2026 is partial through September. No historical screen guarantees future results. Costs are the frozen corrected C1 contract; later production risk allocation, slippage scenarios, and a new identity are outside this fix.

## Final computed status

`NEW_PRODUCTION_IDENTITY_REQUIRED_BEFORE_STAGE7`
