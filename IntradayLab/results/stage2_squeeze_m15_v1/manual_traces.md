# Manual real M15 execution traces

All eleven unique standalone T10 executions; H1 retained/removed admission is shown separately. T15 has identical execution price/time/protection/exit, with acknowledgement delayed five minutes. Raw source read only through frozen2023 byte budgets. These are normalized conditional executions, not real venue fill evidence. UNKNOWN is absent in the actual cohort; synthetic unknown/boundary tests are separately listed below.

## CNYRUBF SQ_CNYRUBF_000508 LONG

Compression 2023-12-06 11:30:00 through 2023-12-06 12:00:00, 3 M15 candles; range [12.974, 13.009]. Signal 2023-12-06 12:15:00 Close=13.018; signal candle outside range and excluded from its construction. Available=2023-12-06 12:35:00 (T10), 2023-12-06 12:40:00 (T15); strict future M15 Open=2023-12-06 12:45:00 at both delays.

Signal SMA7=12.99028571428571428571428571428571, population variance=0.0002242040816326530612244897959183674, EMA7=12.99612276785714285714285714285714, Wilder ATR7=0.02040233236151603498542274052478134. BB [12.96033882251827684695081379381430,13.02023260605315172447775763475712], KC [12.96551926931486880466472303206997,13.02672626639941690962099125364431], squeeze=False.

Frozen Stop=13.004; cap=13.019; actual Open=13.018; initial risk=0.014; Take=13.062; planned C1=0.002; planned net RR=3.

H1 admission MODELLED/CONDITIONAL_EXACT_OPEN, pair=2023-12-06 10:00:00 → 2023-12-06 11:00:00, available=2023-12-06 12:05:00, direction=0, context reason=.

| M15 start | O | H | L | C | V | Role |
| --- | --- | --- | --- | --- | --- | --- |
| 2023-12-06 11:30:00 | 12.978 | 12.984 | 12.974 | 12.98 | 970 | SQUEEZE |
| 2023-12-06 11:45:00 | 12.976 | 12.983 | 12.974 | 12.982 | 617 | SQUEEZE |
| 2023-12-06 12:00:00 | 12.982 | 13.009 | 12.98 | 13.009 | 4872 | SQUEEZE |
| 2023-12-06 12:15:00 | 13.007 | 13.038 | 13.006 | 13.018 | 5523 | SIGNAL |
| 2023-12-06 12:30:00 | 13.019 | 13.024 | 13.017 | 13.019 | 1649 | PATH |
| 2023-12-06 12:45:00 | 13.018 | 13.03 | 13.018 | 13.027 | 1021 | ENTRY |
| 2023-12-06 13:00:00 | 13.027 | 13.037 | 13.019 | 13.023 | 2994 | PATH |
| 2023-12-06 13:15:00 | 13.025 | 13.034 | 12.99 | 12.99 | 5842 | EXIT |

Exact children for signal, entry and exit (duplicate candles listed once):

| M5 child start | O | H | L | C | V |
| --- | --- | --- | --- | --- | --- |
| 2023-12-06 12:15:00 | 13.007 | 13.02 | 13.006 | 13.02 | 3269 |
| 2023-12-06 12:20:00 | 13.019 | 13.038 | 13.014 | 13.031 | 1093 |
| 2023-12-06 12:25:00 | 13.029 | 13.03 | 13.017 | 13.018 | 1161 |
| 2023-12-06 12:45:00 | 13.018 | 13.025 | 13.018 | 13.025 | 161 |
| 2023-12-06 12:50:00 | 13.025 | 13.028 | 13.021 | 13.026 | 272 |
| 2023-12-06 12:55:00 | 13.027 | 13.03 | 13.024 | 13.027 | 588 |
| 2023-12-06 13:15:00 | 13.025 | 13.034 | 13.021 | 13.028 | 3699 |
| 2023-12-06 13:20:00 | 13.028 | 13.028 | 13.013 | 13.013 | 677 |
| 2023-12-06 13:25:00 | 13.013 | 13.016 | 12.99 | 12.99 | 1466 |

Exit=SESSION_FLAT at 2023-12-06 13:15:00, acknowledgement=2023-12-06 13:35:00, price=13.025, hold=30min, flags=none, flat breach=False. Gross=0.007; C1=0.001+0.001=0.002; Net=0.005; C2 Net=0.003. Net R=0.3571428571428571428571428571428571; conservative MFE R=1.357142857142857142857142857142857. No favorable Stop/market exit-bar extreme used. Expected journal Net=0.005.

## CNYRUBF SQ_CNYRUBF_000539 SHORT

Compression 2023-12-21 15:45:00 through 2023-12-21 16:30:00, 4 M15 candles; range [12.849, 12.907]. Signal 2023-12-21 16:45:00 Close=12.847; signal candle outside range and excluded from its construction. Available=2023-12-21 17:05:00 (T10), 2023-12-21 17:10:00 (T15); strict future M15 Open=2023-12-21 17:15:00 at both delays.

Signal SMA7=12.866, population variance=0.0002794285714285714285714285714285714, EMA7=12.85810435267857142857142857142857, Wilder ATR7=0.02371981912298447075623252216338431. BB [12.83256776576843411570009118274723,12.89943223423156588429990881725277], KC [12.82252462399409472243707978818349,12.89368408136304813470577735467365], squeeze=False.

Frozen Stop=12.854; cap=12.838; actual Open=12.839; initial risk=0.015; Take=12.792; planned C1=0.002; planned net RR=3.

H1 admission MODELLED/CONDITIONAL_EXACT_OPEN, pair=2023-12-21 15:00:00 → 2023-12-21 16:00:00, available=2023-12-21 17:05:00, direction=0, context reason=.

| M15 start | O | H | L | C | V | Role |
| --- | --- | --- | --- | --- | --- | --- |
| 2023-12-21 15:45:00 | 12.904 | 12.907 | 12.863 | 12.873 | 7570 | SQUEEZE |
| 2023-12-21 16:00:00 | 12.873 | 12.877 | 12.86 | 12.861 | 8309 | SQUEEZE |
| 2023-12-21 16:15:00 | 12.861 | 12.866 | 12.86 | 12.862 | 11888 | SQUEEZE |
| 2023-12-21 16:30:00 | 12.862 | 12.865 | 12.849 | 12.856 | 1734 | SQUEEZE |
| 2023-12-21 16:45:00 | 12.856 | 12.863 | 12.844 | 12.847 | 3257 | SIGNAL |
| 2023-12-21 17:00:00 | 12.847 | 12.868 | 12.839 | 12.841 | 3207 | PATH |
| 2023-12-21 17:15:00 | 12.839 | 12.846 | 12.82 | 12.836 | 2743 | ENTRY |
| 2023-12-21 17:30:00 | 12.829 | 12.83 | 12.819 | 12.828 | 1188 | PATH |
| 2023-12-21 17:45:00 | 12.828 | 12.831 | 12.815 | 12.828 | 2024 | PATH |
| 2023-12-21 18:00:00 | 12.829 | 12.844 | 12.829 | 12.833 | 4025 | PATH |
| 2023-12-21 18:15:00 | 12.833 | 12.835 | 12.82 | 12.828 | 23275 | EXIT |

Exact children for signal, entry and exit (duplicate candles listed once):

| M5 child start | O | H | L | C | V |
| --- | --- | --- | --- | --- | --- |
| 2023-12-21 16:45:00 | 12.856 | 12.861 | 12.846 | 12.855 | 1790 |
| 2023-12-21 16:50:00 | 12.855 | 12.863 | 12.854 | 12.855 | 530 |
| 2023-12-21 16:55:00 | 12.855 | 12.858 | 12.844 | 12.847 | 937 |
| 2023-12-21 17:15:00 | 12.839 | 12.846 | 12.839 | 12.841 | 790 |
| 2023-12-21 17:20:00 | 12.841 | 12.843 | 12.829 | 12.829 | 672 |
| 2023-12-21 17:25:00 | 12.828 | 12.837 | 12.82 | 12.836 | 1281 |
| 2023-12-21 18:15:00 | 12.833 | 12.835 | 12.821 | 12.824 | 9954 |
| 2023-12-21 18:20:00 | 12.824 | 12.83 | 12.82 | 12.82 | 12479 |
| 2023-12-21 18:25:00 | 12.821 | 12.829 | 12.82 | 12.828 | 842 |

Exit=SESSION_FLAT at 2023-12-21 18:15:00, acknowledgement=2023-12-21 18:35:00, price=12.833, hold=60min, flags=none, flat breach=False. Gross=0.006; C1=0.001+0.001=0.002; Net=0.004; C2 Net=0.002. Net R=0.2666666666666666666666666666666667; conservative MFE R=1.6. No favorable Stop/market exit-bar extreme used. Expected journal Net=0.004.

## GLDRUBF SQ_GLDRUBF_000092 LONG

Compression 2023-10-18 15:45:00 through 2023-10-18 16:30:00, 4 M15 candles; range [5927.3, 5964.9]. Signal 2023-10-18 16:45:00 Close=5968.6; signal candle outside range and excluded from its construction. Available=2023-10-18 17:05:00 (T10), 2023-10-18 17:10:00 (T15); strict future M15 Open=2023-10-18 17:15:00 at both delays.

Signal SMA7=5949.585714285714285714285714285714, population variance=100.0183673469387755102040816326531, EMA7=5953.103794642857142857142857142857, Wilder ATR7=11.04392217528410781222109835187720. BB [5929.583877635352521947439696834921,5969.587550936076049481131731736507], KC [5936.537911379930981138811209615041,5969.669677905783304575474504670673], squeeze=False.

Frozen Stop=5962.2; cap=5970.4; actual Open=5965.4; initial risk=3.2; Take=5975.2; planned C1=0.2; planned net RR=3.

H1 admission MODELLED/CONDITIONAL_EXACT_OPEN, pair=2023-10-18 15:00:00 → 2023-10-18 16:00:00, available=2023-10-18 17:05:00, direction=1, context reason=.

| M15 start | O | H | L | C | V | Role |
| --- | --- | --- | --- | --- | --- | --- |
| 2023-10-18 15:45:00 | 5943.5 | 5944.4 | 5934.1 | 5943.4 | 2376 | SQUEEZE |
| 2023-10-18 16:00:00 | 5942 | 5944.8 | 5935.8 | 5938.4 | 1128 | SQUEEZE |
| 2023-10-18 16:15:00 | 5938.5 | 5948.9 | 5927.3 | 5948.9 | 509 | SQUEEZE |
| 2023-10-18 16:30:00 | 5949 | 5964.9 | 5947.9 | 5960 | 692 | SQUEEZE |
| 2023-10-18 16:45:00 | 5959.9 | 5969.9 | 5959.9 | 5968.6 | 454 | SIGNAL |
| 2023-10-18 17:00:00 | 5969.4 | 5970 | 5955 | 5965.5 | 495 | PATH |
| 2023-10-18 17:15:00 | 5965.4 | 5974 | 5958.1 | 5958.3 | 217 | ENTRY |

Exact children for signal, entry and exit (duplicate candles listed once):

| M5 child start | O | H | L | C | V |
| --- | --- | --- | --- | --- | --- |
| 2023-10-18 16:45:00 | 5959.9 | 5969.4 | 5959.9 | 5968.3 | 337 |
| 2023-10-18 16:50:00 | 5967.9 | 5969.9 | 5966 | 5969.3 | 73 |
| 2023-10-18 16:55:00 | 5969.4 | 5969.7 | 5966.1 | 5968.6 | 44 |
| 2023-10-18 17:15:00 | 5965.4 | 5966.9 | 5958.1 | 5964.7 | 9 |
| 2023-10-18 17:20:00 | 5963.9 | 5974 | 5960.1 | 5966 | 199 |
| 2023-10-18 17:25:00 | 5965 | 5965 | 5958.3 | 5958.3 | 9 |

Exit=STOP at 2023-10-18 17:15:00, acknowledgement=2023-10-18 17:35:00, price=5962.2, hold=0min, flags=ENTRY_BAR_STOP, flat breach=False. Gross=-3.2; C1=0.1+0.1=0.2; Net=-3.4; C2 Net=-3.6. Net R=-1.0625; conservative MFE R=0. No favorable Stop/market exit-bar extreme used. Expected journal Net=-3.4.

## USDRUBF SQ_USDRUBF_000080 LONG

Compression 2023-02-10 15:45:00 through 2023-02-10 17:00:00, 6 M15 candles; range [72.87, 73.15]. Signal 2023-02-10 17:15:00 Close=73.17; signal candle outside range and excluded from its construction. Available=2023-02-10 17:35:00 (T10), 2023-02-10 17:40:00 (T15); strict future M15 Open=2023-02-10 17:45:00 at both delays.

Signal SMA7=73.04285714285714285714285714285714, population variance=0.005277551020408163265306122448979594, EMA7=73.07386335100446428571428571428571, Wilder ATR7=0.09105807468462484654717482875818264. BB [72.89756363274181577526588908701741,73.18815065297246993901982519869687], KC [72.93727623897752701589352347114844,73.21045046303140155553504795742298], squeeze=False.

Frozen Stop=73.13; cap=73.19; actual Open=73.18; initial risk=0.05; Take=73.35; planned C1=0.02; planned net RR=3.

H1 admission MODELLED/CONDITIONAL_EXACT_OPEN, pair=2023-02-10 15:00:00 → 2023-02-10 16:00:00, available=2023-02-10 17:05:00, direction=0, context reason=.

| M15 start | O | H | L | C | V | Role |
| --- | --- | --- | --- | --- | --- | --- |
| 2023-02-10 15:45:00 | 73.06 | 73.07 | 72.98 | 73.01 | 248 | SQUEEZE |
| 2023-02-10 16:00:00 | 73.03 | 73.07 | 73.01 | 73.01 | 346 | SQUEEZE |
| 2023-02-10 16:15:00 | 73.02 | 73.02 | 72.9 | 72.94 | 1327 | SQUEEZE |
| 2023-02-10 16:30:00 | 72.95 | 72.99 | 72.87 | 72.99 | 335 | SQUEEZE |
| 2023-02-10 16:45:00 | 72.97 | 73.15 | 72.96 | 73.07 | 777 | SQUEEZE |
| 2023-02-10 17:00:00 | 73.08 | 73.13 | 73.07 | 73.11 | 282 | SQUEEZE |
| 2023-02-10 17:15:00 | 73.12 | 73.19 | 73.11 | 73.17 | 644 | SIGNAL |
| 2023-02-10 17:30:00 | 73.17 | 73.18 | 73.13 | 73.18 | 537 | PATH |
| 2023-02-10 17:45:00 | 73.18 | 73.31 | 73.17 | 73.28 | 1644 | ENTRY |
| 2023-02-10 18:00:00 | 73.27 | 73.33 | 73.22 | 73.27 | 1382 | PATH |
| 2023-02-10 18:15:00 | 73.27 | 73.3 | 73.24 | 73.28 | 659 | EXIT |

Exact children for signal, entry and exit (duplicate candles listed once):

| M5 child start | O | H | L | C | V |
| --- | --- | --- | --- | --- | --- |
| 2023-02-10 17:15:00 | 73.12 | 73.14 | 73.11 | 73.14 | 29 |
| 2023-02-10 17:20:00 | 73.14 | 73.15 | 73.14 | 73.14 | 137 |
| 2023-02-10 17:25:00 | 73.15 | 73.19 | 73.14 | 73.17 | 478 |
| 2023-02-10 17:45:00 | 73.18 | 73.25 | 73.17 | 73.24 | 426 |
| 2023-02-10 17:50:00 | 73.25 | 73.3 | 73.24 | 73.3 | 773 |
| 2023-02-10 17:55:00 | 73.3 | 73.31 | 73.28 | 73.28 | 445 |
| 2023-02-10 18:15:00 | 73.27 | 73.3 | 73.24 | 73.3 | 204 |
| 2023-02-10 18:20:00 | 73.29 | 73.3 | 73.25 | 73.28 | 286 |
| 2023-02-10 18:25:00 | 73.28 | 73.28 | 73.25 | 73.28 | 169 |

Exit=SESSION_FLAT at 2023-02-10 18:15:00, acknowledgement=2023-02-10 18:35:00, price=73.27, hold=30min, flags=none, flat breach=False. Gross=0.09; C1=0.01+0.01=0.02; Net=0.07; C2 Net=0.05. Net R=1.4; conservative MFE R=3. No favorable Stop/market exit-bar extreme used. Expected journal Net=0.07.

## USDRUBF SQ_USDRUBF_000140 SHORT

Compression 2023-03-15 15:45:00 through 2023-03-15 16:30:00, 4 M15 candles; range [75.95, 76.2]. Signal 2023-03-15 16:45:00 Close=75.9; signal candle outside range and excluded from its construction. Available=2023-03-15 17:05:00 (T10), 2023-03-15 17:10:00 (T15); strict future M15 Open=2023-03-15 17:15:00 at both delays.

Signal SMA7=76.03571428571428571428571428571429, population variance=0.005110204081632653061224489795918366, EMA7=75.99848772321428571428571428571429, Wilder ATR7=0.1125733325400130897840185636936991. BB [75.89274290282060795908909028913574,76.17868566860796346948233828229284], KC [75.82962772440426607960968644017374,76.16734772202430534896174213125484], squeeze=False.

Frozen Stop=75.97; cap=75.90; actual Open=75.93; initial risk=0.04; Take=75.79; planned C1=0.02; planned net RR=3.

H1 admission MODELLED/CONDITIONAL_EXACT_OPEN, pair=2023-03-15 15:00:00 → 2023-03-15 16:00:00, available=2023-03-15 17:05:00, direction=0, context reason=.

| M15 start | O | H | L | C | V | Role |
| --- | --- | --- | --- | --- | --- | --- |
| 2023-03-15 15:45:00 | 76.02 | 76.15 | 76 | 76.13 | 1419 | SQUEEZE |
| 2023-03-15 16:00:00 | 76.11 | 76.2 | 76.07 | 76.11 | 1128 | SQUEEZE |
| 2023-03-15 16:15:00 | 76.08 | 76.11 | 75.96 | 76.04 | 1185 | SQUEEZE |
| 2023-03-15 16:30:00 | 76.05 | 76.05 | 75.95 | 75.99 | 515 | SQUEEZE |
| 2023-03-15 16:45:00 | 75.97 | 75.99 | 75.89 | 75.9 | 1643 | SIGNAL |
| 2023-03-15 17:00:00 | 75.9 | 76 | 75.9 | 75.93 | 410 | PATH |
| 2023-03-15 17:15:00 | 75.93 | 75.93 | 75.87 | 75.89 | 533 | ENTRY |
| 2023-03-15 17:30:00 | 75.9 | 76.1 | 75.89 | 76.1 | 342 | EXIT |

Exact children for signal, entry and exit (duplicate candles listed once):

| M5 child start | O | H | L | C | V |
| --- | --- | --- | --- | --- | --- |
| 2023-03-15 16:45:00 | 75.97 | 75.99 | 75.95 | 75.95 | 711 |
| 2023-03-15 16:50:00 | 75.95 | 75.95 | 75.91 | 75.91 | 261 |
| 2023-03-15 16:55:00 | 75.91 | 75.92 | 75.89 | 75.9 | 671 |
| 2023-03-15 17:15:00 | 75.93 | 75.93 | 75.91 | 75.91 | 48 |
| 2023-03-15 17:20:00 | 75.9 | 75.9 | 75.87 | 75.9 | 426 |
| 2023-03-15 17:25:00 | 75.9 | 75.91 | 75.89 | 75.89 | 59 |
| 2023-03-15 17:30:00 | 75.9 | 75.95 | 75.89 | 75.9 | 130 |
| 2023-03-15 17:35:00 | 75.95 | 76.03 | 75.95 | 76 | 123 |
| 2023-03-15 17:40:00 | 76 | 76.1 | 76 | 76.1 | 89 |

Exit=STOP at 2023-03-15 17:30:00, acknowledgement=2023-03-15 17:50:00, price=75.97, hold=15min, flags=none, flat breach=False. Gross=-0.04; C1=0.01+0.01=0.02; Net=-0.06; C2 Net=-0.08. Net R=-1.5; conservative MFE R=0. No favorable Stop/market exit-bar extreme used. Expected journal Net=-0.06.

## USDRUBF SQ_USDRUBF_000338 SHORT

Compression 2023-06-21 15:45:00 through 2023-06-21 16:30:00, 4 M15 candles; range [83.91, 84.26]. Signal 2023-06-21 16:45:00 Close=83.89; signal candle outside range and excluded from its construction. Available=2023-06-21 17:05:00 (T10), 2023-06-21 17:10:00 (T15); strict future M15 Open=2023-06-21 17:15:00 at both delays.

Signal SMA7=84.04428571428571428571428571428571, population variance=0.008795918367346938775510204081632649, EMA7=84.00316964285714285714285714285714, Wilder ATR7=0.1318652942226453263521151900993634. BB [83.85671259928948740079523273612006,84.23185882928194117063333869245136], KC [83.80537170152317486761468435770809,84.20096758419111084667102992800619], squeeze=False.

Frozen Stop=83.94; cap=83.85; actual Open=83.9; initial risk=0.04; Take=83.76; planned C1=0.02; planned net RR=3.

H1 admission MODELLED/CONDITIONAL_EXACT_OPEN, pair=2023-06-21 15:00:00 → 2023-06-21 16:00:00, available=2023-06-21 17:05:00, direction=0, context reason=.

| M15 start | O | H | L | C | V | Role |
| --- | --- | --- | --- | --- | --- | --- |
| 2023-06-21 15:45:00 | 84.15 | 84.19 | 84.11 | 84.12 | 679 | SQUEEZE |
| 2023-06-21 16:00:00 | 84.14 | 84.26 | 84.1 | 84.1 | 918 | SQUEEZE |
| 2023-06-21 16:15:00 | 84.11 | 84.17 | 83.96 | 84.05 | 3416 | SQUEEZE |
| 2023-06-21 16:30:00 | 84.03 | 84.03 | 83.91 | 83.93 | 2583 | SQUEEZE |
| 2023-06-21 16:45:00 | 83.92 | 83.94 | 83.84 | 83.89 | 2182 | SIGNAL |
| 2023-06-21 17:00:00 | 83.89 | 83.91 | 83.73 | 83.89 | 2286 | PATH |
| 2023-06-21 17:15:00 | 83.9 | 83.91 | 83.68 | 83.7 | 1124 | ENTRY |
| 2023-06-21 17:30:00 | 83.7 | 83.79 | 83.65 | 83.7 | 1001 | EXIT |

Exact children for signal, entry and exit (duplicate candles listed once):

| M5 child start | O | H | L | C | V |
| --- | --- | --- | --- | --- | --- |
| 2023-06-21 16:45:00 | 83.92 | 83.94 | 83.9 | 83.9 | 571 |
| 2023-06-21 16:50:00 | 83.91 | 83.93 | 83.84 | 83.87 | 990 |
| 2023-06-21 16:55:00 | 83.88 | 83.9 | 83.84 | 83.89 | 621 |
| 2023-06-21 17:15:00 | 83.9 | 83.9 | 83.86 | 83.9 | 289 |
| 2023-06-21 17:20:00 | 83.91 | 83.91 | 83.81 | 83.83 | 215 |
| 2023-06-21 17:25:00 | 83.81 | 83.82 | 83.68 | 83.7 | 620 |
| 2023-06-21 17:30:00 | 83.7 | 83.75 | 83.68 | 83.74 | 132 |
| 2023-06-21 17:35:00 | 83.76 | 83.79 | 83.67 | 83.7 | 130 |
| 2023-06-21 17:40:00 | 83.69 | 83.72 | 83.65 | 83.7 | 739 |

Exit=TAKE at 2023-06-21 17:30:00, acknowledgement=2023-06-21 17:50:00, price=83.76, hold=15min, flags=none, flat breach=False. Gross=0.14; C1=0.01+0.01=0.02; Net=0.12; C2 Net=0.10. Net R=3; conservative MFE R=3.5. No favorable Stop/market exit-bar extreme used. Expected journal Net=0.12.

## USDRUBF SQ_USDRUBF_000346 SHORT

Compression 2023-06-26 11:30:00 through 2023-06-26 12:00:00, 3 M15 candles; range [84.48, 84.77]. Signal 2023-06-26 12:15:00 Close=84.43; signal candle outside range and excluded from its construction. Available=2023-06-26 12:35:00 (T10), 2023-06-26 12:40:00 (T15); strict future M15 Open=2023-06-26 12:45:00 at both delays.

Signal SMA7=84.64142857142857142857142857142857, population variance=0.01615510204081632653061224489795919, EMA7=84.62627232142857142857142857142857, Wilder ATR7=0.178592253227821740941274468971262. BB [84.38722312663388315767247895710112,84.89563401622325969947037818575602], KC [84.35838394158683881715951686797168,84.89416070127030403998334027488546], squeeze=False.

Frozen Stop=84.52; cap=84.40; actual Open=84.45; initial risk=0.07; Take=84.22; planned C1=0.02; planned net RR=3.

H1 admission MODELLED/CONDITIONAL_EXACT_OPEN, pair=2023-06-26 10:00:00 → 2023-06-26 11:00:00, available=2023-06-26 12:05:00, direction=0, context reason=.

| M15 start | O | H | L | C | V | Role |
| --- | --- | --- | --- | --- | --- | --- |
| 2023-06-26 11:30:00 | 84.71 | 84.75 | 84.62 | 84.74 | 1399 | SQUEEZE |
| 2023-06-26 11:45:00 | 84.75 | 84.77 | 84.7 | 84.7 | 207 | SQUEEZE |
| 2023-06-26 12:00:00 | 84.68 | 84.69 | 84.48 | 84.49 | 1468 | SQUEEZE |
| 2023-06-26 12:15:00 | 84.49 | 84.49 | 84.33 | 84.43 | 1251 | SIGNAL |
| 2023-06-26 12:30:00 | 84.44 | 84.5 | 84.41 | 84.45 | 481 | PATH |
| 2023-06-26 12:45:00 | 84.45 | 84.49 | 84.43 | 84.48 | 375 | ENTRY |
| 2023-06-26 13:00:00 | 84.47 | 84.51 | 84.43 | 84.43 | 341 | PATH |
| 2023-06-26 13:15:00 | 84.43 | 84.45 | 84.4 | 84.42 | 296 | EXIT |

Exact children for signal, entry and exit (duplicate candles listed once):

| M5 child start | O | H | L | C | V |
| --- | --- | --- | --- | --- | --- |
| 2023-06-26 12:15:00 | 84.49 | 84.49 | 84.37 | 84.4 | 603 |
| 2023-06-26 12:20:00 | 84.39 | 84.43 | 84.33 | 84.39 | 492 |
| 2023-06-26 12:25:00 | 84.39 | 84.43 | 84.38 | 84.43 | 156 |
| 2023-06-26 12:45:00 | 84.45 | 84.47 | 84.43 | 84.47 | 154 |
| 2023-06-26 12:50:00 | 84.47 | 84.49 | 84.44 | 84.49 | 114 |
| 2023-06-26 12:55:00 | 84.46 | 84.48 | 84.44 | 84.48 | 107 |
| 2023-06-26 13:15:00 | 84.43 | 84.45 | 84.43 | 84.43 | 37 |
| 2023-06-26 13:20:00 | 84.44 | 84.44 | 84.4 | 84.42 | 177 |
| 2023-06-26 13:25:00 | 84.41 | 84.42 | 84.4 | 84.42 | 82 |

Exit=FAILED_BREAKOUT at 2023-06-26 13:15:00, acknowledgement=2023-06-26 13:35:00, price=84.43, hold=30min, flags=none, flat breach=False. Gross=0.02; C1=0.01+0.01=0.02; Net=0.00; C2 Net=-0.02. Net R=0; conservative MFE R=0.2857142857142857142857142857142857. No favorable Stop/market exit-bar extreme used. Expected journal Net=0.00.

## USDRUBF SQ_USDRUBF_000440 SHORT

Compression 2023-08-09 15:45:00 through 2023-08-09 17:00:00, 6 M15 candles; range [97.45, 97.9]. Signal 2023-08-09 17:15:00 Close=97.42; signal candle outside range and excluded from its construction. Available=2023-08-09 17:35:00 (T10), 2023-08-09 17:40:00 (T15); strict future M15 Open=2023-08-09 17:45:00 at both delays.

Signal SMA7=97.65, population variance=0.02042857142857142857142857142857143, EMA7=97.60438511439732142857142857142857, Wilder ATR7=0.1913282973688077003872293250018517. BB [97.36414289283929686719335477494283,97.93585710716070313280664522505717], KC [97.31739266834410987799058458392579,97.89137756045053297915227255893135], squeeze=False.

Frozen Stop=97.49; cap=97.36; actual Open=97.43; initial risk=0.06; Take=97.23; planned C1=0.02; planned net RR=3.

H1 admission FILTERED/MTF_SUSTAINED_ADVERSE_DIRECTION, pair=2023-08-09 15:00:00 → 2023-08-09 16:00:00, available=2023-08-09 17:05:00, direction=1, context reason=MTF_SUSTAINED_ADVERSE_DIRECTION.

| M15 start | O | H | L | C | V | Role |
| --- | --- | --- | --- | --- | --- | --- |
| 2023-08-09 15:45:00 | 97.63 | 97.77 | 97.53 | 97.53 | 2097 | SQUEEZE |
| 2023-08-09 16:00:00 | 97.54 | 97.71 | 97.45 | 97.69 | 1262 | SQUEEZE |
| 2023-08-09 16:15:00 | 97.71 | 97.8 | 97.62 | 97.79 | 674 | SQUEEZE |
| 2023-08-09 16:30:00 | 97.79 | 97.9 | 97.74 | 97.83 | 3582 | SQUEEZE |
| 2023-08-09 16:45:00 | 97.82 | 97.83 | 97.72 | 97.75 | 773 | SQUEEZE |
| 2023-08-09 17:00:00 | 97.75 | 97.75 | 97.52 | 97.54 | 3193 | SQUEEZE |
| 2023-08-09 17:15:00 | 97.54 | 97.55 | 97.37 | 97.42 | 3863 | SIGNAL |
| 2023-08-09 17:30:00 | 97.4 | 97.5 | 97.23 | 97.45 | 2303 | PATH |
| 2023-08-09 17:45:00 | 97.43 | 97.48 | 97.11 | 97.31 | 2707 | ENTRY |
| 2023-08-09 18:00:00 | 97.34 | 97.35 | 96.96 | 97.21 | 4740 | EXIT |

Exact children for signal, entry and exit (duplicate candles listed once):

| M5 child start | O | H | L | C | V |
| --- | --- | --- | --- | --- | --- |
| 2023-08-09 17:15:00 | 97.54 | 97.54 | 97.44 | 97.48 | 1255 |
| 2023-08-09 17:20:00 | 97.47 | 97.55 | 97.37 | 97.55 | 1841 |
| 2023-08-09 17:25:00 | 97.53 | 97.55 | 97.4 | 97.42 | 767 |
| 2023-08-09 17:45:00 | 97.43 | 97.48 | 97.26 | 97.26 | 439 |
| 2023-08-09 17:50:00 | 97.24 | 97.26 | 97.11 | 97.23 | 1625 |
| 2023-08-09 17:55:00 | 97.25 | 97.37 | 97.25 | 97.31 | 643 |
| 2023-08-09 18:00:00 | 97.34 | 97.35 | 97.11 | 97.11 | 1254 |
| 2023-08-09 18:05:00 | 97.11 | 97.18 | 97.01 | 97.02 | 1597 |
| 2023-08-09 18:10:00 | 97.01 | 97.27 | 96.96 | 97.21 | 1889 |

Exit=TAKE at 2023-08-09 18:00:00, acknowledgement=2023-08-09 18:20:00, price=97.23, hold=15min, flags=none, flat breach=False. Gross=0.20; C1=0.01+0.01=0.02; Net=0.18; C2 Net=0.16. Net R=3; conservative MFE R=3.333333333333333333333333333333333. No favorable Stop/market exit-bar extreme used. Expected journal Net=0.18.

## USDRUBF SQ_USDRUBF_000628 SHORT

Compression 2023-11-08 15:45:00 through 2023-11-08 16:15:00, 3 M15 candles; range [92.03, 92.36]. Signal 2023-11-08 16:30:00 Close=92.02; signal candle outside range and excluded from its construction. Available=2023-11-08 16:50:00 (T10), 2023-11-08 16:55:00 (T15); strict future M15 Open=2023-11-08 17:00:00 at both delays.

Signal SMA7=92.18285714285714285714285714285714, population variance=0.008677551020408163265306122448979593, EMA7=92.12654017857142857142857142857143, Wilder ATR7=0.159087880049979175343606830487297. BB [91.99655039557827307476332760743051,92.36916389013601263952238667828377], KC [91.88790835849645980841316118284048,92.36517199864639733444398167430238], squeeze=False.

Frozen Stop=92.06; cap=91.96; actual Open=92.02; initial risk=0.04; Take=91.88; planned C1=0.02; planned net RR=3.

H1 admission FILTERED/MTF_TWO_PARENTS_NOT_READY, pair= → , available=, direction=, context reason=MTF_TWO_PARENTS_NOT_READY.

| M15 start | O | H | L | C | V | Role |
| --- | --- | --- | --- | --- | --- | --- |
| 2023-11-08 15:45:00 | 92.28 | 92.36 | 92.26 | 92.29 | 1906 | SQUEEZE |
| 2023-11-08 16:00:00 | 92.29 | 92.31 | 92.06 | 92.17 | 1264 | SQUEEZE |
| 2023-11-08 16:15:00 | 92.18 | 92.21 | 92.03 | 92.09 | 419 | SQUEEZE |
| 2023-11-08 16:30:00 | 92.09 | 92.1 | 91.91 | 92.02 | 2161 | SIGNAL |
| 2023-11-08 16:45:00 | 92.03 | 92.12 | 92 | 92 | 539 | PATH |
| 2023-11-08 17:00:00 | 92.02 | 92.07 | 91.97 | 92 | 1115 | ENTRY |

Exact children for signal, entry and exit (duplicate candles listed once):

| M5 child start | O | H | L | C | V |
| --- | --- | --- | --- | --- | --- |
| 2023-11-08 16:30:00 | 92.09 | 92.1 | 91.91 | 91.96 | 1244 |
| 2023-11-08 16:35:00 | 91.98 | 91.98 | 91.91 | 91.97 | 626 |
| 2023-11-08 16:40:00 | 91.96 | 92.07 | 91.93 | 92.02 | 291 |
| 2023-11-08 17:00:00 | 92.02 | 92.02 | 91.97 | 92 | 542 |
| 2023-11-08 17:05:00 | 92 | 92.05 | 92 | 92.05 | 458 |
| 2023-11-08 17:10:00 | 92.05 | 92.07 | 92 | 92 | 115 |

Exit=STOP at 2023-11-08 17:00:00, acknowledgement=2023-11-08 17:20:00, price=92.06, hold=0min, flags=ENTRY_BAR_STOP, flat breach=False. Gross=-0.04; C1=0.01+0.01=0.02; Net=-0.06; C2 Net=-0.08. Net R=-1.5; conservative MFE R=0. No favorable Stop/market exit-bar extreme used. Expected journal Net=-0.06.

## USDRUBF SQ_USDRUBF_000649 LONG

Compression 2023-11-17 15:45:00 through 2023-11-17 16:45:00, 5 M15 candles; range [89.35, 89.7]. Signal 2023-11-17 17:00:00 Close=89.72; signal candle outside range and excluded from its construction. Available=2023-11-17 17:20:00 (T10), 2023-11-17 17:25:00 (T15); strict future M15 Open=2023-11-17 17:30:00 at both delays.

Signal SMA7=89.53142857142857142857142857142857, population variance=0.01424081632653061224489795918367347, EMA7=89.56776925223214285714285714285714, Wilder ATR7=0.1570256440768727315999286011780806. BB [89.29275878845191883325933844515349,89.77009835440522402388351869770365], KC [89.33223078611683375974296424109002,89.80330771834745195454275004462426], squeeze=False.

Frozen Stop=89.67; cap=89.77; actual Open=89.71; initial risk=0.04; Take=89.85; planned C1=0.02; planned net RR=3.

H1 admission MODELLED/CONDITIONAL_EXACT_OPEN, pair=2023-11-17 15:00:00 → 2023-11-17 16:00:00, available=2023-11-17 17:05:00, direction=0, context reason=.

| M15 start | O | H | L | C | V | Role |
| --- | --- | --- | --- | --- | --- | --- |
| 2023-11-17 15:45:00 | 89.45 | 89.53 | 89.4 | 89.49 | 470 | SQUEEZE |
| 2023-11-17 16:00:00 | 89.49 | 89.54 | 89.45 | 89.46 | 1059 | SQUEEZE |
| 2023-11-17 16:15:00 | 89.45 | 89.48 | 89.35 | 89.37 | 2267 | SQUEEZE |
| 2023-11-17 16:30:00 | 89.43 | 89.56 | 89.43 | 89.56 | 6294 | SQUEEZE |
| 2023-11-17 16:45:00 | 89.57 | 89.7 | 89.48 | 89.68 | 5035 | SQUEEZE |
| 2023-11-17 17:00:00 | 89.69 | 89.74 | 89.65 | 89.72 | 731 | SIGNAL |
| 2023-11-17 17:15:00 | 89.72 | 89.72 | 89.65 | 89.7 | 550 | PATH |
| 2023-11-17 17:30:00 | 89.71 | 90.23 | 89.69 | 90.23 | 5272 | ENTRY |
| 2023-11-17 17:45:00 | 90.24 | 90.35 | 90.12 | 90.13 | 3242 | EXIT |

Exact children for signal, entry and exit (duplicate candles listed once):

| M5 child start | O | H | L | C | V |
| --- | --- | --- | --- | --- | --- |
| 2023-11-17 17:00:00 | 89.69 | 89.7 | 89.65 | 89.66 | 277 |
| 2023-11-17 17:05:00 | 89.67 | 89.74 | 89.66 | 89.73 | 300 |
| 2023-11-17 17:10:00 | 89.73 | 89.73 | 89.69 | 89.72 | 154 |
| 2023-11-17 17:30:00 | 89.71 | 89.75 | 89.69 | 89.75 | 530 |
| 2023-11-17 17:35:00 | 89.76 | 90.06 | 89.76 | 90.04 | 2200 |
| 2023-11-17 17:40:00 | 90.05 | 90.23 | 90.05 | 90.23 | 2542 |
| 2023-11-17 17:45:00 | 90.24 | 90.35 | 90.24 | 90.26 | 1668 |
| 2023-11-17 17:50:00 | 90.28 | 90.28 | 90.14 | 90.2 | 880 |
| 2023-11-17 17:55:00 | 90.2 | 90.25 | 90.12 | 90.13 | 694 |

Exit=TAKE at 2023-11-17 17:45:00, acknowledgement=2023-11-17 18:05:00, price=89.85, hold=15min, flags=none, flat breach=False. Gross=0.14; C1=0.01+0.01=0.02; Net=0.12; C2 Net=0.10. Net R=3; conservative MFE R=3.5. No favorable Stop/market exit-bar extreme used. Expected journal Net=0.12.

## USDRUBF SQ_USDRUBF_000720 SHORT

Compression 2023-12-21 15:45:00 through 2023-12-21 16:15:00, 3 M15 candles; range [92.08, 92.41]. Signal 2023-12-21 16:30:00 Close=91.99; signal candle outside range and excluded from its construction. Available=2023-12-21 16:50:00 (T10), 2023-12-21 16:55:00 (T15); strict future M15 Open=2023-12-21 17:00:00 at both delays.

Signal SMA7=92.13428571428571428571428571428571, population variance=0.01419591836734693877551020408163265, EMA7=92.09426339285714285714285714285714, Wilder ATR7=0.1836984589754269054560599750104123. BB [91.89599246329150808366367193456131,92.37257896527992048776489949401011], KC [91.81871570439400249895876718034152,92.36981108132028321532694710537276], squeeze=False.

Frozen Stop=92.12; cap=91.99; actual Open=92.05; initial risk=0.07; Take=91.82; planned C1=0.02; planned net RR=3.

H1 admission FILTERED/MTF_TWO_PARENTS_NOT_READY, pair= → , available=, direction=, context reason=MTF_TWO_PARENTS_NOT_READY.

| M15 start | O | H | L | C | V | Role |
| --- | --- | --- | --- | --- | --- | --- |
| 2023-12-21 15:45:00 | 92.39 | 92.41 | 92.11 | 92.17 | 2150 | SQUEEZE |
| 2023-12-21 16:00:00 | 92.17 | 92.22 | 92.11 | 92.14 | 1840 | SQUEEZE |
| 2023-12-21 16:15:00 | 92.14 | 92.17 | 92.08 | 92.08 | 964 | SQUEEZE |
| 2023-12-21 16:30:00 | 92.09 | 92.15 | 91.91 | 91.99 | 1751 | SIGNAL |
| 2023-12-21 16:45:00 | 92 | 92.11 | 91.98 | 92.04 | 1483 | PATH |
| 2023-12-21 17:00:00 | 92.05 | 92.22 | 92.03 | 92.05 | 2570 | ENTRY |

Exact children for signal, entry and exit (duplicate candles listed once):

| M5 child start | O | H | L | C | V |
| --- | --- | --- | --- | --- | --- |
| 2023-12-21 16:30:00 | 92.09 | 92.15 | 92.05 | 92.05 | 388 |
| 2023-12-21 16:35:00 | 92.05 | 92.07 | 92 | 92.02 | 634 |
| 2023-12-21 16:40:00 | 92.01 | 92.01 | 91.91 | 91.99 | 729 |
| 2023-12-21 17:00:00 | 92.05 | 92.17 | 92.03 | 92.15 | 904 |
| 2023-12-21 17:05:00 | 92.14 | 92.22 | 92.12 | 92.17 | 972 |
| 2023-12-21 17:10:00 | 92.17 | 92.21 | 92.03 | 92.05 | 694 |

Exit=STOP at 2023-12-21 17:00:00, acknowledgement=2023-12-21 17:20:00, price=92.12, hold=0min, flags=ENTRY_BAR_STOP, flat breach=False. Gross=-0.07; C1=0.01+0.01=0.02; Net=-0.09; C2 Net=-0.11. Net R=-1.285714285714285714285714285714286; conservative MFE R=0. No favorable Stop/market exit-bar extreme used. Expected journal Net=-0.09.

## Real rejection / nonfill representatives

The full funnel is retained in filter_funnel.csv. Each row below is a real signal, not an invented missing-path example.

| Instrument | Architecture | ID | Signal | Target | Status | Reason |
| --- | --- | --- | --- | --- | --- | --- |
| CNYRUBF | SQUEEZE_M15 | SQ_CNYRUBF_000007 | 2023-01-05 17:00:00 | 2023-01-05 17:30:00 | FILTERED | RISK_BELOW_FOUR_TICKS |
| CNYRUBF | SQUEEZE_M15 | SQ_CNYRUBF_000012 | 2023-01-09 12:00:00 | 2023-01-09 12:30:00 | FILTERED | EXTENSION_OVER_0_5_ATR |
| CNYRUBF | SQUEEZE_M15 | SQ_CNYRUBF_000014 | 2023-01-09 18:00:00 | 2023-01-09 18:30:00 | FILTERED | KNOWN_BOUNDARY_ENTRY_CUTOFF |
| CNYRUBF | SQUEEZE_M15 | SQ_CNYRUBF_000381 | 2023-10-02 12:00:00 | 2023-10-02 12:30:00 | NONFILL | EXTENSION_OVER_0_5_ATR |
| CNYRUBF | SQUEEZE_M15 | SQ_CNYRUBF_000416 | 2023-10-19 17:15:00 | 2023-10-19 17:45:00 | NONFILL | BREAKOUT_NOT_PERSISTENT |
| CNYRUBF | SQUEEZE_H1_M15 | SQ_CNYRUBF_000146 | 2023-04-28 16:30:00 | 2023-04-28 17:00:00 | FILTERED | MTF_TWO_PARENTS_NOT_READY |
| CNYRUBF | SQUEEZE_H1_M15 | SQ_CNYRUBF_000519 | 2023-12-13 12:00:00 | 2023-12-13 12:30:00 | FILTERED | MTF_SUSTAINED_ADVERSE_DIRECTION |
| GLDRUBF | SQUEEZE_M15 | SQ_GLDRUBF_000013 | 2023-07-31 12:30:00 | 2023-07-31 13:00:00 | FILTERED | KNOWN_BOUNDARY_ENTRY_CUTOFF |
| GLDRUBF | SQUEEZE_M15 | SQ_GLDRUBF_000043 | 2023-09-06 12:00:00 | 2023-09-06 12:30:00 | NONFILL | EXTENSION_OVER_0_5_ATR |
| GLDRUBF | SQUEEZE_M15 | SQ_GLDRUBF_000051 | 2023-09-14 12:00:00 | 2023-09-14 12:30:00 | FILTERED | EXTENSION_OVER_0_5_ATR |
| GLDRUBF | SQUEEZE_M15 | SQ_GLDRUBF_000101 | 2023-10-23 16:30:00 | 2023-10-23 17:00:00 | NONFILL | BREAKOUT_NOT_PERSISTENT |
| GLDRUBF | SQUEEZE_H1_M15 | SQ_GLDRUBF_000075 | 2023-10-09 16:15:00 | 2023-10-09 16:45:00 | FILTERED | MTF_TWO_PARENTS_NOT_READY |
| IMOEXF | SQUEEZE_M15 | SQ_IMOEXF_000005 | 2023-12-06 18:30:00 | 2023-12-06 19:00:00 | FILTERED | KNOWN_BOUNDARY_ENTRY_CUTOFF |
| IMOEXF | SQUEEZE_M15 | SQ_IMOEXF_000012 | 2023-12-12 17:00:00 | 2023-12-12 17:30:00 | NONFILL | EXTENSION_OVER_0_5_ATR |
| IMOEXF | SQUEEZE_M15 | SQ_IMOEXF_000034 | 2023-12-29 12:00:00 | 2023-12-29 12:30:00 | FILTERED | EXTENSION_OVER_0_5_ATR |
| USDRUBF | SQUEEZE_M15 | SQ_USDRUBF_000001 | 2023-01-03 12:45:00 | 2023-01-03 13:15:00 | FILTERED | KNOWN_BOUNDARY_ENTRY_CUTOFF |
| USDRUBF | SQUEEZE_M15 | SQ_USDRUBF_000007 | 2023-01-05 16:45:00 | 2023-01-05 17:15:00 | FILTERED | RISK_BELOW_FOUR_TICKS |
| USDRUBF | SQUEEZE_M15 | SQ_USDRUBF_000011 | 2023-01-09 12:15:00 | 2023-01-09 12:45:00 | FILTERED | EXTENSION_OVER_0_5_ATR |
| USDRUBF | SQUEEZE_M15 | SQ_USDRUBF_000022 | 2023-01-13 16:15:00 | 2023-01-13 16:45:00 | NONFILL | BREAKOUT_NOT_PERSISTENT |
| USDRUBF | SQUEEZE_M15 | SQ_USDRUBF_000083 | 2023-02-13 16:45:00 | 2023-02-13 17:15:00 | NONFILL | EXTENSION_OVER_0_5_ATR |
| USDRUBF | SQUEEZE_M15 | SQ_USDRUBF_000171 | 2023-03-30 12:00:00 | 2023-03-30 12:30:00 | NONFILL | RISK_BELOW_FOUR_TICKS |
| USDRUBF | SQUEEZE_H1_M15 | SQ_USDRUBF_000015 | 2023-01-10 16:30:00 | 2023-01-10 17:00:00 | FILTERED | MTF_TWO_PARENTS_NOT_READY |
| USDRUBF | SQUEEZE_H1_M15 | SQ_USDRUBF_000358 | 2023-06-29 17:15:00 | 2023-06-29 17:45:00 | FILTERED | MTF_SUSTAINED_ADVERSE_DIRECTION |

IMOEXF real exact target 2023-12-12 17:30:00: Open=3023.5, cap=3030.5, direction=SHORT, Stop=3035.0, signal ATR=6.424559494768336322450679563787197; EXTENSION_OVER_0_5_ATR explains zero fills despite technical feasibility. No fictitious zero from failed warm-up.

## Separately synthetic adversaries

test_squeeze_m15.py checks hand-calculated LONG/SHORT symmetry, identical strict future M15 Open at both delays, common flat acknowledgement, exact composition/no clearing bridge, seven-bar seed/reset, two-bar range excluding signal, risk/target geometry, adverse gap and dual-touch Stop-first, entry-bar TP nonfill, one-tick penetration, session/max-hold/failed-breakout timers, incomplete target UNKNOWN order, missing exposure UNKNOWN preserved after conditional flat, H1 missing/stale/gap rejection and dated CNY ticks. None is labelled a real2023 UNKNOWN trade.
