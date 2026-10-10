# Squeeze v1 — independent manual traces

All times MSK UTC+3. Source `f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8`; source row1 is header. Oracle uses raw source, weighted closed-form EMA/ATR, its own cycles/execution; published CSV is only the comparison target. Trace selection covers rules and does not select architectures. Real trades and synthetic boundary tests are labelled separately.

## Real LONG / 3R Take: USDRUBF / SQUEEZE_M5 / T10 / SQ_USDRUBF_000050

Signal=2023-02-20 12:00:00; delivered/decision=2023-02-20 12:10:00; strictly future scheduled Open=2023-02-20 12:15:00. Outcome=MODELLED / CONDITIONAL_EXACT_OPEN.

Frozen range [73.57, 73.85] from 2023-02-20 11:35:00 through 2023-02-20 11:55:00 (5 true candles). Signal Close=73.88, direction=LONG. Signal candle is excluded: range end < signal start.

Published `signals.csv.gz` decompressed CSV line: 509.
Published `trade_ledger.csv.gz` decompressed CSV line: 10.

| Feature | Independently reconstructed value |
| --- | --- |
| warmup | 25 |
| sma20 | 73.679 |
| variance20 | 0.004489 |
| std20 | 0.067 |
| ema20 | 73.702911360052065313761829102659312294186652093078 |
| tr | 0.13 |
| atr20 | 0.08665523765625 |
| bb_upper | 73.813 |
| bb_lower | 73.545 |
| kc_upper | 73.832894216536440313761829102659312294186652093078 |
| kc_lower | 73.572928503567690313761829102659312294186652093078 |
| squeeze | False |
| stop | 73.83 |
| cap | 73.89 |

Last20 completed source candles (population mean/variance window); TR includes previous Close in the same contiguous segment:

| Source row | Start | Open | High | Low | Close | TR |
| --- | --- | --- | --- | --- | --- | --- |
| 5715 | 2023-02-20 10:25:00 | 73.62 | 73.68 | 73.59 | 73.67 | 0.09 |
| 5716 | 2023-02-20 10:30:00 | 73.65 | 73.66 | 73.63 | 73.66 | 0.04 |
| 5717 | 2023-02-20 10:35:00 | 73.66 | 73.67 | 73.65 | 73.66 | 0.02 |
| 5718 | 2023-02-20 10:40:00 | 73.65 | 73.68 | 73.62 | 73.62 | 0.06 |
| 5719 | 2023-02-20 10:45:00 | 73.63 | 73.69 | 73.61 | 73.65 | 0.08 |
| 5720 | 2023-02-20 10:50:00 | 73.66 | 73.7 | 73.62 | 73.69 | 0.08 |
| 5721 | 2023-02-20 10:55:00 | 73.69 | 73.69 | 73.63 | 73.63 | 0.06 |
| 5722 | 2023-02-20 11:00:00 | 73.65 | 73.68 | 73.65 | 73.66 | 0.05 |
| 5723 | 2023-02-20 11:05:00 | 73.66 | 73.67 | 73.63 | 73.65 | 0.04 |
| 5724 | 2023-02-20 11:10:00 | 73.66 | 73.7 | 73.63 | 73.67 | 0.07 |
| 5725 | 2023-02-20 11:15:00 | 73.68 | 73.72 | 73.65 | 73.69 | 0.07 |
| 5726 | 2023-02-20 11:20:00 | 73.68 | 73.7 | 73.61 | 73.61 | 0.09 |
| 5727 | 2023-02-20 11:25:00 | 73.63 | 73.66 | 73.61 | 73.62 | 0.05 |
| 5728 | 2023-02-20 11:30:00 | 73.62 | 73.67 | 73.61 | 73.67 | 0.06 |
| 5729 | 2023-02-20 11:35:00 | 73.65 | 73.67 | 73.65 | 73.66 | 0.02 |
| 5730 | 2023-02-20 11:40:00 | 73.65 | 73.66 | 73.57 | 73.66 | 0.09 |
| 5731 | 2023-02-20 11:45:00 | 73.67 | 73.71 | 73.61 | 73.66 | 0.10 |
| 5732 | 2023-02-20 11:50:00 | 73.67 | 73.76 | 73.66 | 73.72 | 0.10 |
| 5733 | 2023-02-20 11:55:00 | 73.75 | 73.85 | 73.75 | 73.85 | 0.13 |
| 5734 | 2023-02-20 12:00:00 | 73.85 | 73.98 | 73.85 | 73.88 | 0.13 |

All squeeze-range source children (off/signal candles absent):

| Source row | Start | High | Low |
| --- | --- | --- | --- |
| 5729 | 2023-02-20 11:35:00 | 73.67 | 73.65 |
| 5730 | 2023-02-20 11:40:00 | 73.66 | 73.57 |
| 5731 | 2023-02-20 11:45:00 | 73.71 | 73.61 |
| 5732 | 2023-02-20 11:50:00 | 73.76 | 73.66 |
| 5733 | 2023-02-20 11:55:00 | 73.85 | 73.75 |

Signal source row 5734 at 2023-02-20 12:00:00: OHLCV=(Decimal('73.85'), Decimal('73.98'), Decimal('73.85'), Decimal('73.88'), Decimal('1011')).

Exact scheduled entry source row 5737 at 2023-02-20 12:15:00: OHLCV=(Decimal('73.87'), Decimal('73.93'), Decimal('73.87'), Decimal('73.91'), Decimal('147')).

Exit source row 5751 at 2023-02-20 13:25:00: OHLCV=(Decimal('74.01'), Decimal('74.02'), Decimal('73.99'), Decimal('74.01'), Decimal('218')).

Independent payoff and protection:

| Item | Value |
| --- | --- |
| entry | 73.87 |
| entry_at | 2023-02-20 12:15:00 |
| entry_ack | 2023-02-20 12:25:00 |
| stop | 73.83 |
| initial_risk | 0.04 |
| planned_c1 | 0.02 |
| planned_gross_reward | 0.14 |
| planned_net_reward | 0.12 |
| planned_net_RR | 3 |
| take | 74.01 |
| target_atr | 1.6155976694145332433481493917416319762596000467881 |
| exit | 74.01 |
| exit_at | 2023-02-20 13:25:00 |
| exit_ack | 2023-02-20 13:35:00 |
| exit_reason | TAKE |
| gross | 0.14 |
| c1_entry | 0.01 |
| c1_exit | 0.01 |
| c1 | 0.02 |
| net | 0.12 |
| gross_R | 3.5 |
| net_R | 3 |
| mfe_R | 3.5 |
| hold_minutes | 70 |
| flags |  |

| Event clock / modeled start | Kind | Reason | Price | Acknowledgement | Flags |
| --- | --- | --- | --- | --- | --- |
| 2023-02-20 12:10:00 | ENTRY_ORDER | FIXED_SQUEEZE_BREAKOUT | None | None |  |
| 2023-02-20 12:15:00 | ENTRY | CONDITIONAL_EXACT_OPEN | 73.87 | 2023-02-20 12:25:00 |  |
| 2023-02-20 13:20:00 | TP_NONFILL | TOUCH_WITHOUT_TICK_PENETRATION | None | 2023-02-20 13:30:00 |  |
| 2023-02-20 13:25:00 | EXIT | TAKE | 74.01 | 2023-02-20 13:35:00 |  |

## Real SHORT / entry-bar Stop: USDRUBF / SQUEEZE_M5 / T10 / SQ_USDRUBF_000168

Signal=2023-07-07 12:45:00; delivered/decision=2023-07-07 12:55:00; strictly future scheduled Open=2023-07-07 13:00:00. Outcome=MODELLED / CONDITIONAL_EXACT_OPEN.

Frozen range [91.46, 91.87] from 2023-07-07 11:55:00 through 2023-07-07 12:40:00 (10 true candles). Signal Close=91.45, direction=SHORT. Signal candle is excluded: range end < signal start.

Published `signals.csv.gz` decompressed CSV line: 552.
Published `trade_ledger.csv.gz` decompressed CSV line: 12.

| Feature | Independently reconstructed value |
| --- | --- |
| warmup | 34 |
| sma20 | 91.694 |
| variance20 | 0.009234 |
| std20 | 0.096093704268281800897303715690361395636540589925145 |
| ema20 | 91.660787332126493861776734895376023932093086186611 |
| tr | 0.13 |
| atr20 | 0.13546801996296338498992919921875 |
| bb_upper | 91.886187408536563601794607431380722791273081179850 |
| bb_lower | 91.501812591463436398205392568619277208726918820150 |
| kc_upper | 91.863989362070938939261628694204148932093086186611 |
| kc_lower | 91.457585302182048784291841096547898932093086186611 |
| squeeze | False |
| stop | 91.49 |
| cap | 91.40 |

Last20 completed source candles (population mean/variance window); TR includes previous Close in the same contiguous segment:

| Source row | Start | Open | High | Low | Close | TR |
| --- | --- | --- | --- | --- | --- | --- |
| 21264 | 2023-07-07 11:10:00 | 91.49 | 91.61 | 91.48 | 91.6 | 0.13 |
| 21265 | 2023-07-07 11:15:00 | 91.61 | 91.63 | 91.58 | 91.62 | 0.05 |
| 21266 | 2023-07-07 11:20:00 | 91.61 | 91.63 | 91.57 | 91.62 | 0.06 |
| 21267 | 2023-07-07 11:25:00 | 91.63 | 91.72 | 91.58 | 91.69 | 0.14 |
| 21268 | 2023-07-07 11:30:00 | 91.68 | 91.73 | 91.61 | 91.66 | 0.12 |
| 21269 | 2023-07-07 11:35:00 | 91.67 | 91.72 | 91.65 | 91.72 | 0.07 |
| 21270 | 2023-07-07 11:40:00 | 91.72 | 91.74 | 91.64 | 91.71 | 0.10 |
| 21271 | 2023-07-07 11:45:00 | 91.7 | 91.74 | 91.65 | 91.73 | 0.09 |
| 21272 | 2023-07-07 11:50:00 | 91.73 | 91.79 | 91.7 | 91.79 | 0.09 |
| 21273 | 2023-07-07 11:55:00 | 91.79 | 91.83 | 91.75 | 91.79 | 0.08 |
| 21274 | 2023-07-07 12:00:00 | 91.8 | 91.87 | 91.75 | 91.79 | 0.12 |
| 21275 | 2023-07-07 12:05:00 | 91.79 | 91.79 | 91.71 | 91.73 | 0.08 |
| 21276 | 2023-07-07 12:10:00 | 91.73 | 91.77 | 91.71 | 91.76 | 0.06 |
| 21277 | 2023-07-07 12:15:00 | 91.76 | 91.76 | 91.72 | 91.76 | 0.04 |
| 21278 | 2023-07-07 12:20:00 | 91.76 | 91.76 | 91.68 | 91.76 | 0.08 |
| 21279 | 2023-07-07 12:25:00 | 91.74 | 91.74 | 91.69 | 91.71 | 0.07 |
| 21280 | 2023-07-07 12:30:00 | 91.71 | 91.76 | 91.69 | 91.74 | 0.07 |
| 21281 | 2023-07-07 12:35:00 | 91.74 | 91.78 | 91.72 | 91.78 | 0.06 |
| 21282 | 2023-07-07 12:40:00 | 91.78 | 91.79 | 91.46 | 91.47 | 0.33 |
| 21283 | 2023-07-07 12:45:00 | 91.47 | 91.55 | 91.42 | 91.45 | 0.13 |

All squeeze-range source children (off/signal candles absent):

| Source row | Start | High | Low |
| --- | --- | --- | --- |
| 21273 | 2023-07-07 11:55:00 | 91.83 | 91.75 |
| 21274 | 2023-07-07 12:00:00 | 91.87 | 91.75 |
| 21275 | 2023-07-07 12:05:00 | 91.79 | 91.71 |
| 21276 | 2023-07-07 12:10:00 | 91.77 | 91.71 |
| 21277 | 2023-07-07 12:15:00 | 91.76 | 91.72 |
| 21278 | 2023-07-07 12:20:00 | 91.76 | 91.68 |
| 21279 | 2023-07-07 12:25:00 | 91.74 | 91.69 |
| 21280 | 2023-07-07 12:30:00 | 91.76 | 91.69 |
| 21281 | 2023-07-07 12:35:00 | 91.78 | 91.72 |
| 21282 | 2023-07-07 12:40:00 | 91.79 | 91.46 |

Signal source row 21283 at 2023-07-07 12:45:00: OHLCV=(Decimal('91.47'), Decimal('91.55'), Decimal('91.42'), Decimal('91.45'), Decimal('1265')).

Exact scheduled entry source row 21286 at 2023-07-07 13:00:00: OHLCV=(Decimal('91.41'), Decimal('91.54'), Decimal('91.4'), Decimal('91.54'), Decimal('650')).

Exit source row 21286 at 2023-07-07 13:00:00: OHLCV=(Decimal('91.41'), Decimal('91.54'), Decimal('91.4'), Decimal('91.54'), Decimal('650')).

Independent payoff and protection:

| Item | Value |
| --- | --- |
| entry | 91.41 |
| entry_at | 2023-07-07 13:00:00 |
| entry_ack | 2023-07-07 13:10:00 |
| stop | 91.49 |
| initial_risk | 0.08 |
| planned_c1 | 0.02 |
| planned_gross_reward | 0.26 |
| planned_net_reward | 0.24 |
| planned_net_RR | 3 |
| take | 91.15 |
| target_atr | 1.9192721652762278823066922241186775056383376843350 |
| exit | 91.49 |
| exit_at | 2023-07-07 13:00:00 |
| exit_ack | 2023-07-07 13:10:00 |
| exit_reason | STOP |
| gross | -0.08 |
| c1_entry | 0.01 |
| c1_exit | 0.01 |
| c1 | 0.02 |
| net | -0.10 |
| gross_R | -1 |
| net_R | -1.25 |
| mfe_R | 0 |
| hold_minutes | 0 |
| flags | ENTRY_BAR_STOP |

| Event clock / modeled start | Kind | Reason | Price | Acknowledgement | Flags |
| --- | --- | --- | --- | --- | --- |
| 2023-07-07 12:55:00 | ENTRY_ORDER | FIXED_SQUEEZE_BREAKOUT | None | None |  |
| 2023-07-07 13:00:00 | ENTRY | CONDITIONAL_EXACT_OPEN | 91.41 | 2023-07-07 13:10:00 |  |
| 2023-07-07 13:00:00 | EXIT | STOP | 91.49 | 2023-07-07 13:10:00 | ENTRY_BAR_STOP |

## Real session-flat / previous +1R excursion: USDRUBF / SQUEEZE_M5 / T10 / SQ_USDRUBF_000133

Signal=2023-05-15 13:05:00; delivered/decision=2023-05-15 13:15:00; strictly future scheduled Open=2023-05-15 13:20:00. Outcome=MODELLED / CONDITIONAL_EXACT_OPEN.

Frozen range [79.26, 79.39] from 2023-05-15 12:50:00 through 2023-05-15 13:00:00 (3 true candles). Signal Close=79.42, direction=LONG. Signal candle is excluded: range end < signal start.

Published `signals.csv.gz` decompressed CSV line: 539.
Published `trade_ledger.csv.gz` decompressed CSV line: 11.

| Feature | Independently reconstructed value |
| --- | --- |
| warmup | 38 |
| sma20 | 79.2005 |
| variance20 | 0.00804475 |
| std20 | 0.089692530346735117627826744343242136745765105520045 |
| ema20 | 79.200542748424288888866928196184017614952494824141 |
| tr | 0.08 |
| atr20 | 0.1159505793721566801186236782073974609375 |
| bb_upper | 79.379885060693470235255653488686484273491530211040 |
| bb_lower | 79.021114939306529764744346511313515726508469788960 |
| kc_upper | 79.374468617482523909044863713495113806358744824141 |
| kc_lower | 79.026616879366053868688992678872921423546244824141 |
| squeeze | False |
| stop | 79.37 |
| cap | 79.44 |

Last20 completed source candles (population mean/variance window); TR includes previous Close in the same contiguous segment:

| Source row | Start | Open | High | Low | Close | TR |
| --- | --- | --- | --- | --- | --- | --- |
| 14987 | 2023-05-15 11:30:00 | 79.07 | 79.09 | 79.03 | 79.06 | 0.06 |
| 14988 | 2023-05-15 11:35:00 | 79.07 | 79.18 | 79.06 | 79.18 | 0.12 |
| 14989 | 2023-05-15 11:40:00 | 79.18 | 79.2 | 79.1 | 79.16 | 0.1 |
| 14990 | 2023-05-15 11:45:00 | 79.15 | 79.16 | 79.09 | 79.15 | 0.07 |
| 14991 | 2023-05-15 11:50:00 | 79.13 | 79.14 | 79.11 | 79.14 | 0.04 |
| 14992 | 2023-05-15 11:55:00 | 79.13 | 79.15 | 79.1 | 79.13 | 0.05 |
| 14993 | 2023-05-15 12:00:00 | 79.13 | 79.2 | 79.13 | 79.17 | 0.07 |
| 14994 | 2023-05-15 12:05:00 | 79.2 | 79.24 | 79.19 | 79.24 | 0.07 |
| 14995 | 2023-05-15 12:10:00 | 79.24 | 79.24 | 79.01 | 79.06 | 0.23 |
| 14996 | 2023-05-15 12:15:00 | 79.07 | 79.18 | 78.99 | 79.16 | 0.19 |
| 14997 | 2023-05-15 12:20:00 | 79.13 | 79.18 | 79.07 | 79.18 | 0.11 |
| 14998 | 2023-05-15 12:25:00 | 79.18 | 79.18 | 79.14 | 79.14 | 0.04 |
| 14999 | 2023-05-15 12:30:00 | 79.17 | 79.2 | 79.15 | 79.18 | 0.06 |
| 15000 | 2023-05-15 12:35:00 | 79.2 | 79.21 | 79.17 | 79.17 | 0.04 |
| 15001 | 2023-05-15 12:40:00 | 79.19 | 79.24 | 79.16 | 79.24 | 0.08 |
| 15002 | 2023-05-15 12:45:00 | 79.24 | 79.3 | 79.17 | 79.28 | 0.13 |
| 15003 | 2023-05-15 12:50:00 | 79.28 | 79.29 | 79.26 | 79.28 | 0.03 |
| 15004 | 2023-05-15 12:55:00 | 79.27 | 79.33 | 79.26 | 79.33 | 0.07 |
| 15005 | 2023-05-15 13:00:00 | 79.32 | 79.39 | 79.32 | 79.34 | 0.07 |
| 15006 | 2023-05-15 13:05:00 | 79.34 | 79.42 | 79.34 | 79.42 | 0.08 |

All squeeze-range source children (off/signal candles absent):

| Source row | Start | High | Low |
| --- | --- | --- | --- |
| 15003 | 2023-05-15 12:50:00 | 79.29 | 79.26 |
| 15004 | 2023-05-15 12:55:00 | 79.33 | 79.26 |
| 15005 | 2023-05-15 13:00:00 | 79.39 | 79.32 |

Signal source row 15006 at 2023-05-15 13:05:00: OHLCV=(Decimal('79.34'), Decimal('79.42'), Decimal('79.34'), Decimal('79.42'), Decimal('227')).

Exact scheduled entry source row 15009 at 2023-05-15 13:20:00: OHLCV=(Decimal('79.43'), Decimal('79.49'), Decimal('79.42'), Decimal('79.47'), Decimal('134')).

Exit source row 15013 at 2023-05-15 13:40:00: OHLCV=(Decimal('79.43'), Decimal('79.51'), Decimal('79.43'), Decimal('79.51'), Decimal('153')).

Independent payoff and protection:

| Item | Value |
| --- | --- |
| entry | 79.43 |
| entry_at | 2023-05-15 13:20:00 |
| entry_ack | 2023-05-15 13:30:00 |
| stop | 79.37 |
| initial_risk | 0.06 |
| planned_c1 | 0.02 |
| planned_gross_reward | 0.20 |
| planned_net_reward | 0.18 |
| planned_net_RR | 3 |
| take | 79.63 |
| target_atr | 1.7248727956595806799757445668905912664871777491612 |
| exit | 79.43 |
| exit_at | 2023-05-15 13:40:00 |
| exit_ack | 2023-05-15 13:50:00 |
| exit_reason | SESSION_FLAT |
| gross | 0.00 |
| c1_entry | 0.01 |
| c1_exit | 0.01 |
| c1 | 0.02 |
| net | -0.02 |
| gross_R | 0 |
| net_R | -0.33333333333333333333333333333333333333333333333333 |
| mfe_R | 1.1666666666666666666666666666666666666666666666667 |
| hold_minutes | 20 |
| flags |  |

| Event clock / modeled start | Kind | Reason | Price | Acknowledgement | Flags |
| --- | --- | --- | --- | --- | --- |
| 2023-05-15 13:15:00 | ENTRY_ORDER | FIXED_SQUEEZE_BREAKOUT | None | None |  |
| 2023-05-15 13:20:00 | ENTRY | CONDITIONAL_EXACT_OPEN | 79.43 | 2023-05-15 13:30:00 |  |
| 2023-05-15 13:35:00 | EXIT_ORDER | SESSION_FLAT | None | None |  |
| 2023-05-15 13:40:00 | EXIT | SESSION_FLAT | 79.43 | 2023-05-15 13:50:00 |  |

## Real later Stop: USDRUBF / SQUEEZE_M5 / T10 / SQ_USDRUBF_000199

Signal=2023-08-09 17:25:00; delivered/decision=2023-08-09 17:35:00; strictly future scheduled Open=2023-08-09 17:40:00. Outcome=MODELLED / CONDITIONAL_EXACT_OPEN.

Frozen range [97.45, 97.9] from 2023-08-09 15:55:00 through 2023-08-09 16:45:00 (11 true candles). Signal Close=97.42, direction=SHORT. Signal candle is excluded: range end < signal start.

Published `signals.csv.gz` decompressed CSV line: 568.
Published `trade_ledger.csv.gz` decompressed CSV line: 13.

| Feature | Independently reconstructed value |
| --- | --- |
| warmup | 41 |
| sma20 | 97.6645 |
| variance20 | 0.01483475 |
| std20 | 0.12179798848913720873921493279022671039411175462742 |
| ema20 | 97.621093070653015579631515052479413309493563144469 |
| tr | 0.15 |
| atr20 | 0.1170972539383587267275998908722400665283203125 |
| bb_upper | 97.908095976978274417478429865580453420788223509255 |
| bb_lower | 97.420904023021725582521570134419546579211776490745 |
| kc_upper | 97.796738951560553669722914888787773409286043613219 |
| kc_lower | 97.445447189745477489540115216171053209701082675719 |
| squeeze | False |
| stop | 97.47 |
| cap | 97.40 |

Last20 completed source candles (population mean/variance window); TR includes previous Close in the same contiguous segment:

| Source row | Start | Open | High | Low | Close | TR |
| --- | --- | --- | --- | --- | --- | --- |
| 25246 | 2023-08-09 15:50:00 | 97.72 | 97.75 | 97.69 | 97.75 | 0.06 |
| 25247 | 2023-08-09 15:55:00 | 97.75 | 97.77 | 97.53 | 97.53 | 0.24 |
| 25248 | 2023-08-09 16:00:00 | 97.54 | 97.62 | 97.45 | 97.57 | 0.17 |
| 25249 | 2023-08-09 16:05:00 | 97.58 | 97.63 | 97.54 | 97.61 | 0.09 |
| 25250 | 2023-08-09 16:10:00 | 97.61 | 97.71 | 97.6 | 97.69 | 0.11 |
| 25251 | 2023-08-09 16:15:00 | 97.71 | 97.72 | 97.62 | 97.67 | 0.10 |
| 25252 | 2023-08-09 16:20:00 | 97.68 | 97.74 | 97.68 | 97.73 | 0.07 |
| 25253 | 2023-08-09 16:25:00 | 97.73 | 97.8 | 97.71 | 97.79 | 0.09 |
| 25254 | 2023-08-09 16:30:00 | 97.79 | 97.9 | 97.74 | 97.76 | 0.16 |
| 25255 | 2023-08-09 16:35:00 | 97.79 | 97.89 | 97.78 | 97.85 | 0.13 |
| 25256 | 2023-08-09 16:40:00 | 97.84 | 97.85 | 97.78 | 97.83 | 0.07 |
| 25257 | 2023-08-09 16:45:00 | 97.82 | 97.82 | 97.72 | 97.77 | 0.11 |
| 25258 | 2023-08-09 16:50:00 | 97.78 | 97.83 | 97.77 | 97.79 | 0.06 |
| 25259 | 2023-08-09 16:55:00 | 97.81 | 97.82 | 97.75 | 97.75 | 0.07 |
| 25260 | 2023-08-09 17:00:00 | 97.75 | 97.75 | 97.65 | 97.65 | 0.10 |
| 25261 | 2023-08-09 17:05:00 | 97.65 | 97.65 | 97.54 | 97.56 | 0.11 |
| 25262 | 2023-08-09 17:10:00 | 97.56 | 97.59 | 97.52 | 97.54 | 0.07 |
| 25263 | 2023-08-09 17:15:00 | 97.54 | 97.54 | 97.44 | 97.48 | 0.10 |
| 25264 | 2023-08-09 17:20:00 | 97.47 | 97.55 | 97.37 | 97.55 | 0.18 |
| 25265 | 2023-08-09 17:25:00 | 97.53 | 97.55 | 97.4 | 97.42 | 0.15 |

All squeeze-range source children (off/signal candles absent):

| Source row | Start | High | Low |
| --- | --- | --- | --- |
| 25247 | 2023-08-09 15:55:00 | 97.77 | 97.53 |
| 25248 | 2023-08-09 16:00:00 | 97.62 | 97.45 |
| 25249 | 2023-08-09 16:05:00 | 97.63 | 97.54 |
| 25250 | 2023-08-09 16:10:00 | 97.71 | 97.6 |
| 25251 | 2023-08-09 16:15:00 | 97.72 | 97.62 |
| 25252 | 2023-08-09 16:20:00 | 97.74 | 97.68 |
| 25253 | 2023-08-09 16:25:00 | 97.8 | 97.71 |
| 25254 | 2023-08-09 16:30:00 | 97.9 | 97.74 |
| 25255 | 2023-08-09 16:35:00 | 97.89 | 97.78 |
| 25256 | 2023-08-09 16:40:00 | 97.85 | 97.78 |
| 25257 | 2023-08-09 16:45:00 | 97.82 | 97.72 |

Signal source row 25265 at 2023-08-09 17:25:00: OHLCV=(Decimal('97.53'), Decimal('97.55'), Decimal('97.4'), Decimal('97.42'), Decimal('767')).

Exact scheduled entry source row 25268 at 2023-08-09 17:40:00: OHLCV=(Decimal('97.43'), Decimal('97.46'), Decimal('97.38'), Decimal('97.45'), Decimal('173')).

Exit source row 25269 at 2023-08-09 17:45:00: OHLCV=(Decimal('97.43'), Decimal('97.48'), Decimal('97.26'), Decimal('97.26'), Decimal('439')).

Independent payoff and protection:

| Item | Value |
| --- | --- |
| entry | 97.43 |
| entry_at | 2023-08-09 17:40:00 |
| entry_ack | 2023-08-09 17:50:00 |
| stop | 97.47 |
| initial_risk | 0.04 |
| planned_c1 | 0.02 |
| planned_gross_reward | 0.14 |
| planned_net_reward | 0.12 |
| planned_net_RR | 3 |
| take | 97.29 |
| target_atr | 1.1955873881867249330736058216133250643182414519785 |
| exit | 97.47 |
| exit_at | 2023-08-09 17:45:00 |
| exit_ack | 2023-08-09 17:55:00 |
| exit_reason | STOP |
| gross | -0.04 |
| c1_entry | 0.01 |
| c1_exit | 0.01 |
| c1 | 0.02 |
| net | -0.06 |
| gross_R | -1 |
| net_R | -1.5 |
| mfe_R | 0 |
| hold_minutes | 5 |
| flags | STOP_FIRST_BOTH_LEVELS |

| Event clock / modeled start | Kind | Reason | Price | Acknowledgement | Flags |
| --- | --- | --- | --- | --- | --- |
| 2023-08-09 17:35:00 | ENTRY_ORDER | FIXED_SQUEEZE_BREAKOUT | None | None |  |
| 2023-08-09 17:40:00 | ENTRY | CONDITIONAL_EXACT_OPEN | 97.43 | 2023-08-09 17:50:00 |  |
| 2023-08-09 17:50:00 | EXIT_ORDER | FAILED_BREAKOUT | None | None |  |
| 2023-08-09 17:45:00 | EXIT | STOP | 97.47 | 2023-08-09 17:55:00 | STOP_FIRST_BOTH_LEVELS |

## Real CNY LONG after historical tick switch: CNYRUBF / SQUEEZE_M5 / T10 / SQ_CNYRUBF_000271

Signal=2023-10-10 17:15:00; delivered/decision=2023-10-10 17:25:00; strictly future scheduled Open=2023-10-10 17:30:00. Outcome=MODELLED / CONDITIONAL_EXACT_OPEN.

Frozen range [13.672, 13.731] from 2023-10-10 16:35:00 through 2023-10-10 17:00:00 (6 true candles). Signal Close=13.738, direction=LONG. Signal candle is excluded: range end < signal start.

Published `signals.csv.gz` decompressed CSV line: 68.
Published `trade_ledger.csv.gz` decompressed CSV line: 2.

| Feature | Independently reconstructed value |
| --- | --- |
| warmup | 39 |
| sma20 | 13.68925 |
| variance20 | 0.0003152875 |
| std20 | 0.017756336897006657099163282328744574118724509480394 |
| ema20 | 13.693045047493076343971348163952730649908127185952 |
| tr | 0.033 |
| atr20 | 0.016099985780081985615712248497009277343750 |
| bb_upper | 13.724762673794013314198326564657489148237449018961 |
| bb_lower | 13.653737326205986685801673435342510851762550981039 |
| kc_upper | 13.717195026163199322394916536698244565923752185952 |
| kc_lower | 13.668895068822953365547779791207216733892502185952 |
| squeeze | False |
| stop | 13.727 |
| cap | 13.739 |

Last20 completed source candles (population mean/variance window); TR includes previous Close in the same contiguous segment:

| Source row | Start | Open | High | Low | Close | TR |
| --- | --- | --- | --- | --- | --- | --- |
| 29476 | 2023-10-10 15:40:00 | 13.666 | 13.669 | 13.654 | 13.669 | 0.019 |
| 29477 | 2023-10-10 15:45:00 | 13.666 | 13.685 | 13.666 | 13.684 | 0.019 |
| 29478 | 2023-10-10 15:50:00 | 13.684 | 13.687 | 13.674 | 13.682 | 0.013 |
| 29479 | 2023-10-10 15:55:00 | 13.674 | 13.692 | 13.674 | 13.686 | 0.018 |
| 29480 | 2023-10-10 16:00:00 | 13.688 | 13.688 | 13.674 | 13.675 | 0.014 |
| 29481 | 2023-10-10 16:05:00 | 13.675 | 13.676 | 13.675 | 13.676 | 0.001 |
| 29482 | 2023-10-10 16:10:00 | 13.675 | 13.675 | 13.667 | 13.673 | 0.009 |
| 29483 | 2023-10-10 16:15:00 | 13.669 | 13.688 | 13.668 | 13.688 | 0.020 |
| 29484 | 2023-10-10 16:20:00 | 13.685 | 13.686 | 13.672 | 13.683 | 0.016 |
| 29485 | 2023-10-10 16:25:00 | 13.684 | 13.691 | 13.671 | 13.676 | 0.020 |
| 29486 | 2023-10-10 16:30:00 | 13.676 | 13.688 | 13.676 | 13.684 | 0.012 |
| 29487 | 2023-10-10 16:35:00 | 13.684 | 13.692 | 13.677 | 13.679 | 0.015 |
| 29488 | 2023-10-10 16:40:00 | 13.681 | 13.686 | 13.679 | 13.681 | 0.007 |
| 29489 | 2023-10-10 16:45:00 | 13.682 | 13.686 | 13.672 | 13.672 | 0.014 |
| 29490 | 2023-10-10 16:50:00 | 13.678 | 13.694 | 13.677 | 13.692 | 0.022 |
| 29491 | 2023-10-10 16:55:00 | 13.692 | 13.716 | 13.689 | 13.71 | 0.027 |
| 29492 | 2023-10-10 17:00:00 | 13.71 | 13.731 | 13.705 | 13.711 | 0.026 |
| 29493 | 2023-10-10 17:05:00 | 13.71 | 13.711 | 13.7 | 13.709 | 0.011 |
| 29494 | 2023-10-10 17:10:00 | 13.709 | 13.717 | 13.698 | 13.717 | 0.019 |
| 29495 | 2023-10-10 17:15:00 | 13.717 | 13.75 | 13.717 | 13.738 | 0.033 |

All squeeze-range source children (off/signal candles absent):

| Source row | Start | High | Low |
| --- | --- | --- | --- |
| 29487 | 2023-10-10 16:35:00 | 13.692 | 13.677 |
| 29488 | 2023-10-10 16:40:00 | 13.686 | 13.679 |
| 29489 | 2023-10-10 16:45:00 | 13.686 | 13.672 |
| 29490 | 2023-10-10 16:50:00 | 13.694 | 13.677 |
| 29491 | 2023-10-10 16:55:00 | 13.716 | 13.689 |
| 29492 | 2023-10-10 17:00:00 | 13.731 | 13.705 |

Signal source row 29495 at 2023-10-10 17:15:00: OHLCV=(Decimal('13.717'), Decimal('13.75'), Decimal('13.717'), Decimal('13.738'), Decimal('1411')).

Exact scheduled entry source row 29498 at 2023-10-10 17:30:00: OHLCV=(Decimal('13.736'), Decimal('13.74'), Decimal('13.722'), Decimal('13.731'), Decimal('899')).

Exit source row 29498 at 2023-10-10 17:30:00: OHLCV=(Decimal('13.736'), Decimal('13.74'), Decimal('13.722'), Decimal('13.731'), Decimal('899')).

Independent payoff and protection:

| Item | Value |
| --- | --- |
| entry | 13.736 |
| entry_at | 2023-10-10 17:30:00 |
| entry_ack | 2023-10-10 17:40:00 |
| stop | 13.727 |
| initial_risk | 0.009 |
| planned_c1 | 0.002 |
| planned_gross_reward | 0.029 |
| planned_net_reward | 0.027 |
| planned_net_RR | 3 |
| take | 13.765 |
| target_atr | 1.8012438269279219149596930608378090502122543348932 |
| exit | 13.727 |
| exit_at | 2023-10-10 17:30:00 |
| exit_ack | 2023-10-10 17:40:00 |
| exit_reason | STOP |
| gross | -0.009 |
| c1_entry | 0.001 |
| c1_exit | 0.001 |
| c1 | 0.002 |
| net | -0.011 |
| gross_R | -1 |
| net_R | -1.2222222222222222222222222222222222222222222222222 |
| mfe_R | 0 |
| hold_minutes | 0 |
| flags | ENTRY_BAR_STOP |

| Event clock / modeled start | Kind | Reason | Price | Acknowledgement | Flags |
| --- | --- | --- | --- | --- | --- |
| 2023-10-10 17:25:00 | ENTRY_ORDER | FIXED_SQUEEZE_BREAKOUT | None | None |  |
| 2023-10-10 17:30:00 | ENTRY | CONDITIONAL_EXACT_OPEN | 13.736 | 2023-10-10 17:40:00 |  |
| 2023-10-10 17:30:00 | EXIT | STOP | 13.727 | 2023-10-10 17:40:00 | ENTRY_BAR_STOP |

## Real CNY SHORT / risk and C1: CNYRUBF / SQUEEZE_M5 / T10 / SQ_CNYRUBF_000276

Signal=2023-10-12 12:35:00; delivered/decision=2023-10-12 12:45:00; strictly future scheduled Open=2023-10-12 12:50:00. Outcome=MODELLED / CONDITIONAL_EXACT_OPEN.

Frozen range [13.28, 13.314] from 2023-10-12 12:15:00 through 2023-10-12 12:30:00 (4 true candles). Signal Close=13.277, direction=SHORT. Signal candle is excluded: range end < signal start.

Published `signals.csv.gz` decompressed CSV line: 70.
Published `trade_ledger.csv.gz` decompressed CSV line: 3.

| Feature | Independently reconstructed value |
| --- | --- |
| warmup | 32 |
| sma20 | 13.29785 |
| variance20 | 0.0001150275 |
| std20 | 0.010725087412231193558870107861566442120225969767364 |
| ema20 | 13.295823001561207617345579315830953810921655281809 |
| tr | 0.014 |
| atr20 | 0.01528856106785905362548828125 |
| bb_upper | 13.319300174824462387117740215723132884240451939535 |
| bb_lower | 13.276399825175537612882259784276867115759548060465 |
| kc_upper | 13.318755843162996197783811737705953810921655281809 |
| kc_lower | 13.272890159959419036907346893955953810921655281809 |
| squeeze | False |
| stop | 13.283 |
| cap | 13.273 |

Last20 completed source candles (population mean/variance window); TR includes previous Close in the same contiguous segment:

| Source row | Start | Open | High | Low | Close | TR |
| --- | --- | --- | --- | --- | --- | --- |
| 29755 | 2023-10-12 11:00:00 | 13.295 | 13.3 | 13.285 | 13.295 | 0.015 |
| 29756 | 2023-10-12 11:05:00 | 13.296 | 13.296 | 13.279 | 13.289 | 0.017 |
| 29757 | 2023-10-12 11:10:00 | 13.289 | 13.294 | 13.285 | 13.288 | 0.009 |
| 29758 | 2023-10-12 11:15:00 | 13.288 | 13.29 | 13.282 | 13.282 | 0.008 |
| 29759 | 2023-10-12 11:20:00 | 13.286 | 13.295 | 13.286 | 13.293 | 0.013 |
| 29760 | 2023-10-12 11:25:00 | 13.293 | 13.303 | 13.293 | 13.303 | 0.010 |
| 29761 | 2023-10-12 11:30:00 | 13.3 | 13.303 | 13.298 | 13.302 | 0.005 |
| 29762 | 2023-10-12 11:35:00 | 13.301 | 13.315 | 13.301 | 13.308 | 0.014 |
| 29763 | 2023-10-12 11:40:00 | 13.31 | 13.31 | 13.292 | 13.295 | 0.018 |
| 29764 | 2023-10-12 11:45:00 | 13.296 | 13.305 | 13.296 | 13.302 | 0.010 |
| 29765 | 2023-10-12 11:50:00 | 13.297 | 13.312 | 13.294 | 13.312 | 0.018 |
| 29766 | 2023-10-12 11:55:00 | 13.306 | 13.312 | 13.305 | 13.312 | 0.007 |
| 29767 | 2023-10-12 12:00:00 | 13.31 | 13.31 | 13.307 | 13.308 | 0.005 |
| 29768 | 2023-10-12 12:05:00 | 13.308 | 13.308 | 13.297 | 13.3 | 0.011 |
| 29769 | 2023-10-12 12:10:00 | 13.3 | 13.309 | 13.3 | 13.309 | 0.009 |
| 29770 | 2023-10-12 12:15:00 | 13.305 | 13.314 | 13.305 | 13.312 | 0.009 |
| 29771 | 2023-10-12 12:20:00 | 13.314 | 13.314 | 13.295 | 13.302 | 0.019 |
| 29772 | 2023-10-12 12:25:00 | 13.302 | 13.303 | 13.284 | 13.285 | 0.019 |
| 29773 | 2023-10-12 12:30:00 | 13.285 | 13.29 | 13.28 | 13.283 | 0.01 |
| 29774 | 2023-10-12 12:35:00 | 13.28 | 13.285 | 13.271 | 13.277 | 0.014 |

All squeeze-range source children (off/signal candles absent):

| Source row | Start | High | Low |
| --- | --- | --- | --- |
| 29770 | 2023-10-12 12:15:00 | 13.314 | 13.305 |
| 29771 | 2023-10-12 12:20:00 | 13.314 | 13.295 |
| 29772 | 2023-10-12 12:25:00 | 13.303 | 13.284 |
| 29773 | 2023-10-12 12:30:00 | 13.29 | 13.28 |

Signal source row 29774 at 2023-10-12 12:35:00: OHLCV=(Decimal('13.28'), Decimal('13.285'), Decimal('13.271'), Decimal('13.277'), Decimal('1376')).

Exact scheduled entry source row 29777 at 2023-10-12 12:50:00: OHLCV=(Decimal('13.279'), Decimal('13.287'), Decimal('13.279'), Decimal('13.285'), Decimal('643')).

Exit source row 29777 at 2023-10-12 12:50:00: OHLCV=(Decimal('13.279'), Decimal('13.287'), Decimal('13.279'), Decimal('13.285'), Decimal('643')).

Independent payoff and protection:

| Item | Value |
| --- | --- |
| entry | 13.279 |
| entry_at | 2023-10-12 12:50:00 |
| entry_ack | 2023-10-12 13:00:00 |
| stop | 13.283 |
| initial_risk | 0.004 |
| planned_c1 | 0.002 |
| planned_gross_reward | 0.014 |
| planned_net_reward | 0.012 |
| planned_net_RR | 3 |
| take | 13.265 |
| target_atr | 0.91571730902995318007682886764996433764980583761624 |
| exit | 13.283 |
| exit_at | 2023-10-12 12:50:00 |
| exit_ack | 2023-10-12 13:00:00 |
| exit_reason | STOP |
| gross | -0.004 |
| c1_entry | 0.001 |
| c1_exit | 0.001 |
| c1 | 0.002 |
| net | -0.006 |
| gross_R | -1 |
| net_R | -1.5 |
| mfe_R | 0 |
| hold_minutes | 0 |
| flags | ENTRY_BAR_STOP |

| Event clock / modeled start | Kind | Reason | Price | Acknowledgement | Flags |
| --- | --- | --- | --- | --- | --- |
| 2023-10-12 12:45:00 | ENTRY_ORDER | FIXED_SQUEEZE_BREAKOUT | None | None |  |
| 2023-10-12 12:50:00 | ENTRY | CONDITIONAL_EXACT_OPEN | 13.279 | 2023-10-12 13:00:00 |  |
| 2023-10-12 12:50:00 | EXIT | STOP | 13.283 | 2023-10-12 13:00:00 | ENTRY_BAR_STOP |

## Real CNY December Stop: CNYRUBF / SQUEEZE_M5 / T10 / SQ_CNYRUBF_000368

Signal=2023-12-28 12:10:00; delivered/decision=2023-12-28 12:20:00; strictly future scheduled Open=2023-12-28 12:25:00. Outcome=MODELLED / CONDITIONAL_EXACT_OPEN.

Frozen range [12.686, 12.704] from 2023-12-28 11:40:00 through 2023-12-28 12:05:00 (6 true candles). Signal Close=12.706, direction=LONG. Signal candle is excluded: range end < signal start.

Published `signals.csv.gz` decompressed CSV line: 103.
Published `trade_ledger.csv.gz` decompressed CSV line: 4.

| Feature | Independently reconstructed value |
| --- | --- |
| warmup | 27 |
| sma20 | 12.69225 |
| variance20 | 0.0000701875 |
| std20 | 0.0083777980400580199233351675357703049428995710814496 |
| ema20 | 12.697800026226750614810557500515461888111585070597 |
| tr | 0.014 |
| atr20 | 0.0143286753630859375 |
| bb_upper | 12.709005596080116039846670335071540609885799142163 |
| bb_lower | 12.675494403919883960153329664928459390114200857837 |
| kc_upper | 12.719293039271379521060557500515461888111585070597 |
| kc_lower | 12.676307013182121708560557500515461888111585070597 |
| squeeze | False |
| stop | 12.701 |
| cap | 12.711 |

Last20 completed source candles (population mean/variance window); TR includes previous Close in the same contiguous segment:

| Source row | Start | Open | High | Low | Close | TR |
| --- | --- | --- | --- | --- | --- | --- |
| 39036 | 2023-12-28 10:35:00 | 12.69 | 12.69 | 12.684 | 12.689 | 0.007 |
| 39037 | 2023-12-28 10:40:00 | 12.689 | 12.689 | 12.677 | 12.678 | 0.012 |
| 39038 | 2023-12-28 10:45:00 | 12.678 | 12.696 | 12.675 | 12.69 | 0.021 |
| 39039 | 2023-12-28 10:50:00 | 12.693 | 12.704 | 12.689 | 12.704 | 0.015 |
| 39040 | 2023-12-28 10:55:00 | 12.702 | 12.707 | 12.695 | 12.697 | 0.012 |
| 39041 | 2023-12-28 11:00:00 | 12.697 | 12.697 | 12.682 | 12.687 | 0.015 |
| 39042 | 2023-12-28 11:05:00 | 12.686 | 12.687 | 12.675 | 12.677 | 0.012 |
| 39043 | 2023-12-28 11:10:00 | 12.679 | 12.698 | 12.677 | 12.697 | 0.021 |
| 39044 | 2023-12-28 11:15:00 | 12.693 | 12.694 | 12.686 | 12.692 | 0.011 |
| 39045 | 2023-12-28 11:20:00 | 12.689 | 12.692 | 12.684 | 12.686 | 0.008 |
| 39046 | 2023-12-28 11:25:00 | 12.686 | 12.688 | 12.68 | 12.682 | 0.008 |
| 39047 | 2023-12-28 11:30:00 | 12.68 | 12.689 | 12.68 | 12.684 | 0.009 |
| 39048 | 2023-12-28 11:35:00 | 12.685 | 12.689 | 12.637 | 12.688 | 0.052 |
| 39049 | 2023-12-28 11:40:00 | 12.688 | 12.692 | 12.686 | 12.692 | 0.006 |
| 39050 | 2023-12-28 11:45:00 | 12.692 | 12.699 | 12.69 | 12.697 | 0.009 |
| 39051 | 2023-12-28 11:50:00 | 12.695 | 12.696 | 12.688 | 12.693 | 0.009 |
| 39052 | 2023-12-28 11:55:00 | 12.691 | 12.701 | 12.691 | 12.699 | 0.010 |
| 39053 | 2023-12-28 12:00:00 | 12.696 | 12.704 | 12.69 | 12.704 | 0.014 |
| 39054 | 2023-12-28 12:05:00 | 12.7 | 12.704 | 12.698 | 12.703 | 0.006 |
| 39055 | 2023-12-28 12:10:00 | 12.701 | 12.709 | 12.695 | 12.706 | 0.014 |

All squeeze-range source children (off/signal candles absent):

| Source row | Start | High | Low |
| --- | --- | --- | --- |
| 39049 | 2023-12-28 11:40:00 | 12.692 | 12.686 |
| 39050 | 2023-12-28 11:45:00 | 12.699 | 12.69 |
| 39051 | 2023-12-28 11:50:00 | 12.696 | 12.688 |
| 39052 | 2023-12-28 11:55:00 | 12.701 | 12.691 |
| 39053 | 2023-12-28 12:00:00 | 12.704 | 12.69 |
| 39054 | 2023-12-28 12:05:00 | 12.704 | 12.698 |

Signal source row 39055 at 2023-12-28 12:10:00: OHLCV=(Decimal('12.701'), Decimal('12.709'), Decimal('12.695'), Decimal('12.706'), Decimal('3401')).

Exact scheduled entry source row 39058 at 2023-12-28 12:25:00: OHLCV=(Decimal('12.705'), Decimal('12.707'), Decimal('12.699'), Decimal('12.699'), Decimal('653')).

Exit source row 39058 at 2023-12-28 12:25:00: OHLCV=(Decimal('12.705'), Decimal('12.707'), Decimal('12.699'), Decimal('12.699'), Decimal('653')).

Independent payoff and protection:

| Item | Value |
| --- | --- |
| entry | 12.705 |
| entry_at | 2023-12-28 12:25:00 |
| entry_ack | 2023-12-28 12:35:00 |
| stop | 12.701 |
| initial_risk | 0.004 |
| planned_c1 | 0.002 |
| planned_gross_reward | 0.014 |
| planned_net_reward | 0.012 |
| planned_net_RR | 3 |
| take | 12.719 |
| target_atr | 0.97706170635056167819820111907296633274485520603945 |
| exit | 12.701 |
| exit_at | 2023-12-28 12:25:00 |
| exit_ack | 2023-12-28 12:35:00 |
| exit_reason | STOP |
| gross | -0.004 |
| c1_entry | 0.001 |
| c1_exit | 0.001 |
| c1 | 0.002 |
| net | -0.006 |
| gross_R | -1 |
| net_R | -1.5 |
| mfe_R | 0 |
| hold_minutes | 0 |
| flags | ENTRY_BAR_STOP |

| Event clock / modeled start | Kind | Reason | Price | Acknowledgement | Flags |
| --- | --- | --- | --- | --- | --- |
| 2023-12-28 12:20:00 | ENTRY_ORDER | FIXED_SQUEEZE_BREAKOUT | None | None |  |
| 2023-12-28 12:25:00 | ENTRY | CONDITIONAL_EXACT_OPEN | 12.705 | 2023-12-28 12:35:00 |  |
| 2023-12-28 12:25:00 | EXIT | STOP | 12.701 | 2023-12-28 12:35:00 | ENTRY_BAR_STOP |

## Real T15 failed-breakout exit: USDRUBF / SQUEEZE_M5 / T15 / SQ_USDRUBF_000233

Signal=2023-09-07 17:30:00; delivered/decision=2023-09-07 17:45:00; strictly future scheduled Open=2023-09-07 17:50:00. Outcome=MODELLED / CONDITIONAL_EXACT_OPEN.

Frozen range [97.54, 98.27] from 2023-09-07 15:40:00 through 2023-09-07 17:00:00 (17 true candles). Signal Close=98.28, direction=LONG. Signal candle is excluded: range end < signal start.

Published `signals.csv.gz` decompressed CSV line: 739.
Published `trade_ledger.csv.gz` decompressed CSV line: 15.

| Feature | Independently reconstructed value |
| --- | --- |
| warmup | 42 |
| sma20 | 98.056 |
| variance20 | 0.021764 |
| std20 | 0.14752626884728021209794394781024054055529928114893 |
| ema20 | 98.103472479608769984443716478254999216624685221346 |
| tr | 0.10 |
| atr20 | 0.14810144495254455292563033848350048065185546875 |
| bb_upper | 98.351052537694560424195887895620481081110598562298 |
| bb_lower | 97.760947462305439575804112104379518918889401437702 |
| kc_upper | 98.325624647037586813832161985980249937602468424471 |
| kc_lower | 97.881320312179953155055270970529748495646902018221 |
| squeeze | False |
| stop | 98.24 |
| cap | 98.34 |

Last20 completed source candles (population mean/variance window); TR includes previous Close in the same contiguous segment:

| Source row | Start | Open | High | Low | Close | TR |
| --- | --- | --- | --- | --- | --- | --- |
| 28657 | 2023-09-07 15:55:00 | 97.86 | 97.88 | 97.76 | 97.78 | 0.12 |
| 28658 | 2023-09-07 16:00:00 | 97.77 | 97.92 | 97.54 | 97.89 | 0.38 |
| 28659 | 2023-09-07 16:05:00 | 97.88 | 97.99 | 97.8 | 97.89 | 0.19 |
| 28660 | 2023-09-07 16:10:00 | 97.88 | 98.05 | 97.83 | 98 | 0.22 |
| 28661 | 2023-09-07 16:15:00 | 98.01 | 98.09 | 97.93 | 98 | 0.16 |
| 28662 | 2023-09-07 16:20:00 | 98 | 98.03 | 97.83 | 97.87 | 0.20 |
| 28663 | 2023-09-07 16:25:00 | 97.87 | 97.95 | 97.85 | 97.91 | 0.10 |
| 28664 | 2023-09-07 16:30:00 | 97.92 | 98.04 | 97.92 | 98 | 0.13 |
| 28665 | 2023-09-07 16:35:00 | 98 | 98.02 | 97.95 | 97.97 | 0.07 |
| 28666 | 2023-09-07 16:40:00 | 97.98 | 97.98 | 97.91 | 97.94 | 0.07 |
| 28667 | 2023-09-07 16:45:00 | 97.93 | 98.08 | 97.93 | 98.08 | 0.15 |
| 28668 | 2023-09-07 16:50:00 | 98.08 | 98.23 | 98.02 | 98.06 | 0.21 |
| 28669 | 2023-09-07 16:55:00 | 98.07 | 98.17 | 98.07 | 98.15 | 0.11 |
| 28670 | 2023-09-07 17:00:00 | 98.15 | 98.27 | 98.15 | 98.24 | 0.12 |
| 28671 | 2023-09-07 17:05:00 | 98.24 | 98.27 | 98.18 | 98.24 | 0.09 |
| 28672 | 2023-09-07 17:10:00 | 98.23 | 98.24 | 98.18 | 98.18 | 0.06 |
| 28673 | 2023-09-07 17:15:00 | 98.2 | 98.25 | 98.18 | 98.22 | 0.07 |
| 28674 | 2023-09-07 17:20:00 | 98.21 | 98.21 | 98.16 | 98.19 | 0.06 |
| 28675 | 2023-09-07 17:25:00 | 98.22 | 98.26 | 98.19 | 98.23 | 0.07 |
| 28676 | 2023-09-07 17:30:00 | 98.23 | 98.31 | 98.21 | 98.28 | 0.10 |

All squeeze-range source children (off/signal candles absent):

| Source row | Start | High | Low |
| --- | --- | --- | --- |
| 28654 | 2023-09-07 15:40:00 | 98.04 | 97.95 |
| 28655 | 2023-09-07 15:45:00 | 98.06 | 97.77 |
| 28656 | 2023-09-07 15:50:00 | 97.88 | 97.76 |
| 28657 | 2023-09-07 15:55:00 | 97.88 | 97.76 |
| 28658 | 2023-09-07 16:00:00 | 97.92 | 97.54 |
| 28659 | 2023-09-07 16:05:00 | 97.99 | 97.8 |
| 28660 | 2023-09-07 16:10:00 | 98.05 | 97.83 |
| 28661 | 2023-09-07 16:15:00 | 98.09 | 97.93 |
| 28662 | 2023-09-07 16:20:00 | 98.03 | 97.83 |
| 28663 | 2023-09-07 16:25:00 | 97.95 | 97.85 |
| 28664 | 2023-09-07 16:30:00 | 98.04 | 97.92 |
| 28665 | 2023-09-07 16:35:00 | 98.02 | 97.95 |
| 28666 | 2023-09-07 16:40:00 | 97.98 | 97.91 |
| 28667 | 2023-09-07 16:45:00 | 98.08 | 97.93 |
| 28668 | 2023-09-07 16:50:00 | 98.23 | 98.02 |
| 28669 | 2023-09-07 16:55:00 | 98.17 | 98.07 |
| 28670 | 2023-09-07 17:00:00 | 98.27 | 98.15 |

Signal source row 28676 at 2023-09-07 17:30:00: OHLCV=(Decimal('98.23'), Decimal('98.31'), Decimal('98.21'), Decimal('98.28'), Decimal('351')).

Exact scheduled entry source row 28680 at 2023-09-07 17:50:00: OHLCV=(Decimal('98.31'), Decimal('98.33'), Decimal('98.31'), Decimal('98.31'), Decimal('291')).

Exit source row 28685 at 2023-09-07 18:15:00: OHLCV=(Decimal('98.45'), Decimal('98.46'), Decimal('98.41'), Decimal('98.41'), Decimal('657')).

Independent payoff and protection:

| Item | Value |
| --- | --- |
| entry | 98.31 |
| entry_at | 2023-09-07 17:50:00 |
| entry_ack | 2023-09-07 18:05:00 |
| stop | 98.24 |
| initial_risk | 0.07 |
| planned_c1 | 0.02 |
| planned_gross_reward | 0.23 |
| planned_net_reward | 0.21 |
| planned_net_RR | 3 |
| take | 98.54 |
| target_atr | 1.5529895746371537061386625966879294492447503403853 |
| exit | 98.45 |
| exit_at | 2023-09-07 18:15:00 |
| exit_ack | 2023-09-07 18:30:00 |
| exit_reason | FAILED_BREAKOUT |
| gross | 0.14 |
| c1_entry | 0.01 |
| c1_exit | 0.01 |
| c1 | 0.02 |
| net | 0.12 |
| gross_R | 2 |
| net_R | 1.7142857142857142857142857142857142857142857142857 |
| mfe_R | 2.1428571428571428571428571428571428571428571428571 |
| hold_minutes | 25 |
| flags |  |

| Event clock / modeled start | Kind | Reason | Price | Acknowledgement | Flags |
| --- | --- | --- | --- | --- | --- |
| 2023-09-07 17:45:00 | ENTRY_ORDER | FIXED_SQUEEZE_BREAKOUT | None | None |  |
| 2023-09-07 17:50:00 | ENTRY | CONDITIONAL_EXACT_OPEN | 98.31 | 2023-09-07 18:05:00 |  |
| 2023-09-07 18:10:00 | EXIT_ORDER | FAILED_BREAKOUT | None | None |  |
| 2023-09-07 18:15:00 | EXIT | FAILED_BREAKOUT | 98.45 | 2023-09-07 18:30:00 |  |

## Real T15 counterpart of T10 winner / NONFILL: USDRUBF / SQUEEZE_M5 / T15 / SQ_USDRUBF_000050

Signal=2023-02-20 12:00:00; delivered/decision=2023-02-20 12:15:00; strictly future scheduled Open=2023-02-20 12:20:00. Outcome=NONFILL / EXTENSION_OVER_0_5_ATR.

Frozen range [73.57, 73.85] from 2023-02-20 11:35:00 through 2023-02-20 11:55:00 (5 true candles). Signal Close=73.88, direction=LONG. Signal candle is excluded: range end < signal start.

Published `signals.csv.gz` decompressed CSV line: 665.
Published `trade_ledger.csv.gz` decompressed CSV line: no ledger row / no fill.

| Feature | Independently reconstructed value |
| --- | --- |
| warmup | 25 |
| sma20 | 73.679 |
| variance20 | 0.004489 |
| std20 | 0.067 |
| ema20 | 73.702911360052065313761829102659312294186652093078 |
| tr | 0.13 |
| atr20 | 0.08665523765625 |
| bb_upper | 73.813 |
| bb_lower | 73.545 |
| kc_upper | 73.832894216536440313761829102659312294186652093078 |
| kc_lower | 73.572928503567690313761829102659312294186652093078 |
| squeeze | False |
| stop | 73.83 |
| cap | 73.89 |

Last20 completed source candles (population mean/variance window); TR includes previous Close in the same contiguous segment:

| Source row | Start | Open | High | Low | Close | TR |
| --- | --- | --- | --- | --- | --- | --- |
| 5715 | 2023-02-20 10:25:00 | 73.62 | 73.68 | 73.59 | 73.67 | 0.09 |
| 5716 | 2023-02-20 10:30:00 | 73.65 | 73.66 | 73.63 | 73.66 | 0.04 |
| 5717 | 2023-02-20 10:35:00 | 73.66 | 73.67 | 73.65 | 73.66 | 0.02 |
| 5718 | 2023-02-20 10:40:00 | 73.65 | 73.68 | 73.62 | 73.62 | 0.06 |
| 5719 | 2023-02-20 10:45:00 | 73.63 | 73.69 | 73.61 | 73.65 | 0.08 |
| 5720 | 2023-02-20 10:50:00 | 73.66 | 73.7 | 73.62 | 73.69 | 0.08 |
| 5721 | 2023-02-20 10:55:00 | 73.69 | 73.69 | 73.63 | 73.63 | 0.06 |
| 5722 | 2023-02-20 11:00:00 | 73.65 | 73.68 | 73.65 | 73.66 | 0.05 |
| 5723 | 2023-02-20 11:05:00 | 73.66 | 73.67 | 73.63 | 73.65 | 0.04 |
| 5724 | 2023-02-20 11:10:00 | 73.66 | 73.7 | 73.63 | 73.67 | 0.07 |
| 5725 | 2023-02-20 11:15:00 | 73.68 | 73.72 | 73.65 | 73.69 | 0.07 |
| 5726 | 2023-02-20 11:20:00 | 73.68 | 73.7 | 73.61 | 73.61 | 0.09 |
| 5727 | 2023-02-20 11:25:00 | 73.63 | 73.66 | 73.61 | 73.62 | 0.05 |
| 5728 | 2023-02-20 11:30:00 | 73.62 | 73.67 | 73.61 | 73.67 | 0.06 |
| 5729 | 2023-02-20 11:35:00 | 73.65 | 73.67 | 73.65 | 73.66 | 0.02 |
| 5730 | 2023-02-20 11:40:00 | 73.65 | 73.66 | 73.57 | 73.66 | 0.09 |
| 5731 | 2023-02-20 11:45:00 | 73.67 | 73.71 | 73.61 | 73.66 | 0.10 |
| 5732 | 2023-02-20 11:50:00 | 73.67 | 73.76 | 73.66 | 73.72 | 0.10 |
| 5733 | 2023-02-20 11:55:00 | 73.75 | 73.85 | 73.75 | 73.85 | 0.13 |
| 5734 | 2023-02-20 12:00:00 | 73.85 | 73.98 | 73.85 | 73.88 | 0.13 |

All squeeze-range source children (off/signal candles absent):

| Source row | Start | High | Low |
| --- | --- | --- | --- |
| 5729 | 2023-02-20 11:35:00 | 73.67 | 73.65 |
| 5730 | 2023-02-20 11:40:00 | 73.66 | 73.57 |
| 5731 | 2023-02-20 11:45:00 | 73.71 | 73.61 |
| 5732 | 2023-02-20 11:50:00 | 73.76 | 73.66 |
| 5733 | 2023-02-20 11:55:00 | 73.85 | 73.75 |

Signal source row 5734 at 2023-02-20 12:00:00: OHLCV=(Decimal('73.85'), Decimal('73.98'), Decimal('73.85'), Decimal('73.88'), Decimal('1011')).

Exact scheduled entry source row 5738 at 2023-02-20 12:20:00: OHLCV=(Decimal('73.91'), Decimal('73.93'), Decimal('73.9'), Decimal('73.93'), Decimal('40')).

No model fill, no ledger price, no C1. The exact-slot rejection is not retried on a later favorable candle.

| Event clock / modeled start | Kind | Reason | Price | Acknowledgement | Flags |
| --- | --- | --- | --- | --- | --- |
| 2023-02-20 12:15:00 | ENTRY_ORDER | FIXED_SQUEEZE_BREAKOUT | None | None |  |
| 2023-02-20 12:20:00 | ENTRY_NONFILL | EXTENSION_OVER_0_5_ATR | None | 2023-02-20 12:35:00 |  |

## Real M30 adverse-context rejection: USDRUBF / SQUEEZE_M30_M5 / T10 / SQ_USDRUBF_000013

Signal=2023-01-12 16:45:00; delivered/decision=2023-01-12 16:55:00; strictly future scheduled Open=2023-01-12 17:00:00. Outcome=FILTERED / MTF_SUSTAINED_ADVERSE_DIRECTION.

Frozen range [67.73, 67.9] from 2023-01-12 16:30:00 through 2023-01-12 16:40:00 (3 true candles). Signal Close=67.69, direction=SHORT. Signal candle is excluded: range end < signal start.

Published `signals.csv.gz` decompressed CSV line: 809.
Published `trade_ledger.csv.gz` decompressed CSV line: no ledger row / no fill.

| Feature | Independently reconstructed value |
| --- | --- |
| warmup | 33 |
| sma20 | 67.7985 |
| variance20 | 0.00239275 |
| std20 | 0.048915743886810103380907865812684307230043499080746 |
| ema20 | 67.792316607267985031477428621288937139660559868712 |
| tr | 0.12 |
| atr20 | 0.06320749801346591981201171875 |
| bb_upper | 67.896331487773620206761815731625368614460086998161 |
| bb_lower | 67.700668512226379793238184268374631385539913001839 |
| kc_upper | 67.887127854288183911195446199413937139660559868712 |
| kc_lower | 67.697505360247786151759411043163937139660559868712 |
| squeeze | False |
| stop | 67.74 |
| cap | 67.70 |

Last20 completed source candles (population mean/variance window); TR includes previous Close in the same contiguous segment:

| Source row | Start | Open | High | Low | Close | TR |
| --- | --- | --- | --- | --- | --- | --- |
| 1249 | 2023-01-12 15:10:00 | 67.77 | 67.79 | 67.76 | 67.76 | 0.03 |
| 1250 | 2023-01-12 15:15:00 | 67.77 | 67.77 | 67.74 | 67.74 | 0.03 |
| 1251 | 2023-01-12 15:20:00 | 67.74 | 67.77 | 67.73 | 67.75 | 0.04 |
| 1252 | 2023-01-12 15:25:00 | 67.76 | 67.78 | 67.76 | 67.78 | 0.03 |
| 1253 | 2023-01-12 15:30:00 | 67.78 | 67.78 | 67.71 | 67.75 | 0.07 |
| 1254 | 2023-01-12 15:35:00 | 67.74 | 67.87 | 67.74 | 67.87 | 0.13 |
| 1255 | 2023-01-12 15:40:00 | 67.85 | 67.87 | 67.8 | 67.85 | 0.07 |
| 1256 | 2023-01-12 15:45:00 | 67.86 | 67.87 | 67.8 | 67.86 | 0.07 |
| 1257 | 2023-01-12 15:50:00 | 67.82 | 67.82 | 67.78 | 67.79 | 0.08 |
| 1258 | 2023-01-12 15:55:00 | 67.77 | 67.82 | 67.77 | 67.82 | 0.05 |
| 1259 | 2023-01-12 16:00:00 | 67.82 | 67.82 | 67.79 | 67.79 | 0.03 |
| 1260 | 2023-01-12 16:05:00 | 67.79 | 67.81 | 67.79 | 67.8 | 0.02 |
| 1261 | 2023-01-12 16:10:00 | 67.82 | 67.83 | 67.8 | 67.83 | 0.03 |
| 1262 | 2023-01-12 16:15:00 | 67.84 | 67.86 | 67.83 | 67.86 | 0.03 |
| 1263 | 2023-01-12 16:20:00 | 67.84 | 67.87 | 67.79 | 67.84 | 0.08 |
| 1264 | 2023-01-12 16:25:00 | 67.84 | 67.85 | 67.81 | 67.85 | 0.04 |
| 1265 | 2023-01-12 16:30:00 | 67.83 | 67.9 | 67.73 | 67.73 | 0.17 |
| 1266 | 2023-01-12 16:35:00 | 67.74 | 67.82 | 67.74 | 67.8 | 0.09 |
| 1267 | 2023-01-12 16:40:00 | 67.78 | 67.81 | 67.78 | 67.81 | 0.03 |
| 1268 | 2023-01-12 16:45:00 | 67.8 | 67.8 | 67.69 | 67.69 | 0.12 |

All squeeze-range source children (off/signal candles absent):

| Source row | Start | High | Low |
| --- | --- | --- | --- |
| 1265 | 2023-01-12 16:30:00 | 67.9 | 67.73 |
| 1266 | 2023-01-12 16:35:00 | 67.82 | 67.74 |
| 1267 | 2023-01-12 16:40:00 | 67.81 | 67.78 |

Signal source row 1268 at 2023-01-12 16:45:00: OHLCV=(Decimal('67.8'), Decimal('67.8'), Decimal('67.69'), Decimal('67.69'), Decimal('116')).

Exact scheduled entry source row 1271 at 2023-01-12 17:00:00: OHLCV=(Decimal('67.69'), Decimal('67.71'), Decimal('67.62'), Decimal('67.68'), Decimal('151')).

No model fill, no ledger price, no C1. The exact-slot rejection is not retried on a later favorable candle.

M30 pair=2023-01-12 15:30:00 / 2023-01-12 16:00:00; available=2023-01-12 16:35:00; direction=1; gate reason=MTF_SUSTAINED_ADVERSE_DIRECTION.

| M30 child start | Source row | OHLCV |
| --- | --- | --- |
| 2023-01-12 15:30:00 | 1253 | (Decimal('67.78'), Decimal('67.78'), Decimal('67.71'), Decimal('67.75'), Decimal('92')) |
| 2023-01-12 15:35:00 | 1254 | (Decimal('67.74'), Decimal('67.87'), Decimal('67.74'), Decimal('67.87'), Decimal('446')) |
| 2023-01-12 15:40:00 | 1255 | (Decimal('67.85'), Decimal('67.87'), Decimal('67.8'), Decimal('67.85'), Decimal('430')) |
| 2023-01-12 15:45:00 | 1256 | (Decimal('67.86'), Decimal('67.87'), Decimal('67.8'), Decimal('67.86'), Decimal('691')) |
| 2023-01-12 15:50:00 | 1257 | (Decimal('67.82'), Decimal('67.82'), Decimal('67.78'), Decimal('67.79'), Decimal('140')) |
| 2023-01-12 15:55:00 | 1258 | (Decimal('67.77'), Decimal('67.82'), Decimal('67.77'), Decimal('67.82'), Decimal('116')) |
| 2023-01-12 16:00:00 | 1259 | (Decimal('67.82'), Decimal('67.82'), Decimal('67.79'), Decimal('67.79'), Decimal('11')) |
| 2023-01-12 16:05:00 | 1260 | (Decimal('67.79'), Decimal('67.81'), Decimal('67.79'), Decimal('67.8'), Decimal('18')) |
| 2023-01-12 16:10:00 | 1261 | (Decimal('67.82'), Decimal('67.83'), Decimal('67.8'), Decimal('67.83'), Decimal('96')) |
| 2023-01-12 16:15:00 | 1262 | (Decimal('67.84'), Decimal('67.86'), Decimal('67.83'), Decimal('67.86'), Decimal('4')) |
| 2023-01-12 16:20:00 | 1263 | (Decimal('67.84'), Decimal('67.87'), Decimal('67.79'), Decimal('67.84'), Decimal('45')) |
| 2023-01-12 16:25:00 | 1264 | (Decimal('67.84'), Decimal('67.85'), Decimal('67.81'), Decimal('67.85'), Decimal('14')) |

| Event clock / modeled start | Kind | Reason | Price | Acknowledgement | Flags |
| --- | --- | --- | --- | --- | --- |

## Real M30 accepted counterpart / same M5 exit: USDRUBF / SQUEEZE_M30_M5 / T10 / SQ_USDRUBF_000050

Signal=2023-02-20 12:00:00; delivered/decision=2023-02-20 12:10:00; strictly future scheduled Open=2023-02-20 12:15:00. Outcome=MODELLED / CONDITIONAL_EXACT_OPEN.

Frozen range [73.57, 73.85] from 2023-02-20 11:35:00 through 2023-02-20 11:55:00 (5 true candles). Signal Close=73.88, direction=LONG. Signal candle is excluded: range end < signal start.

Published `signals.csv.gz` decompressed CSV line: 821.
Published `trade_ledger.csv.gz` decompressed CSV line: 16.

| Feature | Independently reconstructed value |
| --- | --- |
| warmup | 25 |
| sma20 | 73.679 |
| variance20 | 0.004489 |
| std20 | 0.067 |
| ema20 | 73.702911360052065313761829102659312294186652093078 |
| tr | 0.13 |
| atr20 | 0.08665523765625 |
| bb_upper | 73.813 |
| bb_lower | 73.545 |
| kc_upper | 73.832894216536440313761829102659312294186652093078 |
| kc_lower | 73.572928503567690313761829102659312294186652093078 |
| squeeze | False |
| stop | 73.83 |
| cap | 73.89 |

Last20 completed source candles (population mean/variance window); TR includes previous Close in the same contiguous segment:

| Source row | Start | Open | High | Low | Close | TR |
| --- | --- | --- | --- | --- | --- | --- |
| 5715 | 2023-02-20 10:25:00 | 73.62 | 73.68 | 73.59 | 73.67 | 0.09 |
| 5716 | 2023-02-20 10:30:00 | 73.65 | 73.66 | 73.63 | 73.66 | 0.04 |
| 5717 | 2023-02-20 10:35:00 | 73.66 | 73.67 | 73.65 | 73.66 | 0.02 |
| 5718 | 2023-02-20 10:40:00 | 73.65 | 73.68 | 73.62 | 73.62 | 0.06 |
| 5719 | 2023-02-20 10:45:00 | 73.63 | 73.69 | 73.61 | 73.65 | 0.08 |
| 5720 | 2023-02-20 10:50:00 | 73.66 | 73.7 | 73.62 | 73.69 | 0.08 |
| 5721 | 2023-02-20 10:55:00 | 73.69 | 73.69 | 73.63 | 73.63 | 0.06 |
| 5722 | 2023-02-20 11:00:00 | 73.65 | 73.68 | 73.65 | 73.66 | 0.05 |
| 5723 | 2023-02-20 11:05:00 | 73.66 | 73.67 | 73.63 | 73.65 | 0.04 |
| 5724 | 2023-02-20 11:10:00 | 73.66 | 73.7 | 73.63 | 73.67 | 0.07 |
| 5725 | 2023-02-20 11:15:00 | 73.68 | 73.72 | 73.65 | 73.69 | 0.07 |
| 5726 | 2023-02-20 11:20:00 | 73.68 | 73.7 | 73.61 | 73.61 | 0.09 |
| 5727 | 2023-02-20 11:25:00 | 73.63 | 73.66 | 73.61 | 73.62 | 0.05 |
| 5728 | 2023-02-20 11:30:00 | 73.62 | 73.67 | 73.61 | 73.67 | 0.06 |
| 5729 | 2023-02-20 11:35:00 | 73.65 | 73.67 | 73.65 | 73.66 | 0.02 |
| 5730 | 2023-02-20 11:40:00 | 73.65 | 73.66 | 73.57 | 73.66 | 0.09 |
| 5731 | 2023-02-20 11:45:00 | 73.67 | 73.71 | 73.61 | 73.66 | 0.10 |
| 5732 | 2023-02-20 11:50:00 | 73.67 | 73.76 | 73.66 | 73.72 | 0.10 |
| 5733 | 2023-02-20 11:55:00 | 73.75 | 73.85 | 73.75 | 73.85 | 0.13 |
| 5734 | 2023-02-20 12:00:00 | 73.85 | 73.98 | 73.85 | 73.88 | 0.13 |

All squeeze-range source children (off/signal candles absent):

| Source row | Start | High | Low |
| --- | --- | --- | --- |
| 5729 | 2023-02-20 11:35:00 | 73.67 | 73.65 |
| 5730 | 2023-02-20 11:40:00 | 73.66 | 73.57 |
| 5731 | 2023-02-20 11:45:00 | 73.71 | 73.61 |
| 5732 | 2023-02-20 11:50:00 | 73.76 | 73.66 |
| 5733 | 2023-02-20 11:55:00 | 73.85 | 73.75 |

Signal source row 5734 at 2023-02-20 12:00:00: OHLCV=(Decimal('73.85'), Decimal('73.98'), Decimal('73.85'), Decimal('73.88'), Decimal('1011')).

Exact scheduled entry source row 5737 at 2023-02-20 12:15:00: OHLCV=(Decimal('73.87'), Decimal('73.93'), Decimal('73.87'), Decimal('73.91'), Decimal('147')).

Exit source row 5751 at 2023-02-20 13:25:00: OHLCV=(Decimal('74.01'), Decimal('74.02'), Decimal('73.99'), Decimal('74.01'), Decimal('218')).

Independent payoff and protection:

| Item | Value |
| --- | --- |
| entry | 73.87 |
| entry_at | 2023-02-20 12:15:00 |
| entry_ack | 2023-02-20 12:25:00 |
| stop | 73.83 |
| initial_risk | 0.04 |
| planned_c1 | 0.02 |
| planned_gross_reward | 0.14 |
| planned_net_reward | 0.12 |
| planned_net_RR | 3 |
| take | 74.01 |
| target_atr | 1.6155976694145332433481493917416319762596000467881 |
| exit | 74.01 |
| exit_at | 2023-02-20 13:25:00 |
| exit_ack | 2023-02-20 13:35:00 |
| exit_reason | TAKE |
| gross | 0.14 |
| c1_entry | 0.01 |
| c1_exit | 0.01 |
| c1 | 0.02 |
| net | 0.12 |
| gross_R | 3.5 |
| net_R | 3 |
| mfe_R | 3.5 |
| hold_minutes | 70 |
| flags |  |

M30 pair=2023-02-20 11:00:00 / 2023-02-20 11:30:00; available=2023-02-20 12:05:00; direction=0; gate reason=None.

| M30 child start | Source row | OHLCV |
| --- | --- | --- |
| 2023-02-20 11:00:00 | 5722 | (Decimal('73.65'), Decimal('73.68'), Decimal('73.65'), Decimal('73.66'), Decimal('92')) |
| 2023-02-20 11:05:00 | 5723 | (Decimal('73.66'), Decimal('73.67'), Decimal('73.63'), Decimal('73.65'), Decimal('203')) |
| 2023-02-20 11:10:00 | 5724 | (Decimal('73.66'), Decimal('73.7'), Decimal('73.63'), Decimal('73.67'), Decimal('347')) |
| 2023-02-20 11:15:00 | 5725 | (Decimal('73.68'), Decimal('73.72'), Decimal('73.65'), Decimal('73.69'), Decimal('277')) |
| 2023-02-20 11:20:00 | 5726 | (Decimal('73.68'), Decimal('73.7'), Decimal('73.61'), Decimal('73.61'), Decimal('383')) |
| 2023-02-20 11:25:00 | 5727 | (Decimal('73.63'), Decimal('73.66'), Decimal('73.61'), Decimal('73.62'), Decimal('191')) |
| 2023-02-20 11:30:00 | 5728 | (Decimal('73.62'), Decimal('73.67'), Decimal('73.61'), Decimal('73.67'), Decimal('112')) |
| 2023-02-20 11:35:00 | 5729 | (Decimal('73.65'), Decimal('73.67'), Decimal('73.65'), Decimal('73.66'), Decimal('56')) |
| 2023-02-20 11:40:00 | 5730 | (Decimal('73.65'), Decimal('73.66'), Decimal('73.57'), Decimal('73.66'), Decimal('607')) |
| 2023-02-20 11:45:00 | 5731 | (Decimal('73.67'), Decimal('73.71'), Decimal('73.61'), Decimal('73.66'), Decimal('732')) |
| 2023-02-20 11:50:00 | 5732 | (Decimal('73.67'), Decimal('73.76'), Decimal('73.66'), Decimal('73.72'), Decimal('230')) |
| 2023-02-20 11:55:00 | 5733 | (Decimal('73.75'), Decimal('73.85'), Decimal('73.75'), Decimal('73.85'), Decimal('339')) |

| Event clock / modeled start | Kind | Reason | Price | Acknowledgement | Flags |
| --- | --- | --- | --- | --- | --- |
| 2023-02-20 12:10:00 | ENTRY_ORDER | FIXED_SQUEEZE_BREAKOUT | None | None |  |
| 2023-02-20 12:15:00 | ENTRY | CONDITIONAL_EXACT_OPEN | 73.87 | 2023-02-20 12:25:00 |  |
| 2023-02-20 13:20:00 | TP_NONFILL | TOUCH_WITHOUT_TICK_PENETRATION | None | 2023-02-20 13:30:00 |  |
| 2023-02-20 13:25:00 | EXIT | TAKE | 74.01 | 2023-02-20 13:35:00 |  |

## Real compression without a signal

{
  "bars": 7,
  "confirmed_at": "2023-01-03 18:35:00",
  "cycle_id": "SQ_USDRUBF_000002",
  "direction": null,
  "end": "2023-01-03 18:45:00",
  "range_high": "71.43",
  "range_low": "71.14",
  "released_at": null,
  "signal_at": null,
  "start": "2023-01-03 18:15:00",
  "terminal_at": "2023-01-03 19:00:00",
  "terminal_reason": "NO_EXPANSION_SESSION"
}

Confirmed squeeze alone does not create an order. The range expired without a directional expansion; it cannot be reused after reset.

## Real missing M30 child / no stale fallback

GLDRUBF decision clock=2023-07-11 11:05:00; independent gate={'mtf_first': None, 'mtf_last': None, 'mtf_available_at': None, 'mtf_direction': None, 'mtf_reason': 'MTF_INCOMPLETE_CHILD_BUCKET'}.

| Expected child | Physically exists | OHLCV |
| --- | --- | --- |
| 2023-07-11 10:30:00 | False | None |
| 2023-07-11 10:35:00 | True | (Decimal('5483.6'), Decimal('5483.6'), Decimal('5483.6'), Decimal('5483.6'), Decimal('1')) |
| 2023-07-11 10:40:00 | True | (Decimal('5483.5'), Decimal('5483.5'), Decimal('5483.5'), Decimal('5483.5'), Decimal('3')) |
| 2023-07-11 10:45:00 | True | (Decimal('5493.1'), Decimal('5502.9'), Decimal('5493.1'), Decimal('5502.9'), Decimal('154')) |
| 2023-07-11 10:50:00 | True | (Decimal('5506'), Decimal('5506'), Decimal('5506'), Decimal('5506'), Decimal('3')) |
| 2023-07-11 10:55:00 | True | (Decimal('5504.2'), Decimal('5504.2'), Decimal('5504.2'), Decimal('5504.2'), Decimal('1')) |

A prior complete M30 pair is not substituted. Missing child remains physically missing.

## Real entire missing date / reset

USDRUBF 2023-08-31: all 105 approved M5 slots absent; no source row, no reconstructed candle, no indicator carry through the date. No Squeeze position was open across this gap; actual UNKNOWN count is0.
CNYRUBF 2023-08-31: all 105 approved M5 slots absent; no source row, no reconstructed candle, no indicator carry through the date. No Squeeze position was open across this gap; actual UNKNOWN count is0.

## Synthetic boundary cases — these are NOT 2023 trades

The actual 2023 candidate has no adverse Stop gap, missing-entry order, opened UNKNOWN, Stop/Take ambiguity or MAX_HOLD exit. Those paths are verified by deterministic unit fixtures, not invented historical transactions.

- Adverse gap + both levels: LONG entry100.05, stop99.97, risk0.08, take100.31; following Open99.95/High100.40/Low99.90. Stop-first gives exit99.95, Gross−0.10, C1=0.02, Net−0.12, NetR=−1.5. High100.40 does not prove prior3R. `test_stop_first_and_adverse_gap`.
- Missing entry: prescribed signal15:55, T10 ready16:05, target16:10 absent; acknowledgement16:20 gives NO_BAR_NO_MODEL_FILL, no entry price/cost. No later candle retries that entry. `test_session_reserve_t10_t15_and_missing_exact_entry`.
- UNKNOWN path: entry11:15 acknowledged11:25; gap observation11:30 requests future11:35 reduce-all, acknowledged11:45. All past Gross/C1_total/Net/R stay null even if next Open is200. `test_unknown_never_reconciles_payoff`.
- MAX_HOLD: PM prescribed signal15:55, model entry16:10; request18:05, future Open18:10, acknowledgement18:20; actual model holding120min. `test_max_hold_120_and_future_failed_breakout_exit`.
- Failed breakout: entry16:10; completed candle16:20 closes100.08 inside [99.90,100.10], delivered16:30; request16:30 and exit16:35 Open100.11, never the earlier Close100.08.
- Session: B18:50; T10 request18:25 → Open18:30 → acknowledgement18:40. T15 request18:20 → Open18:25 → acknowledgement18:40. Both reserve B−10; boundary has priority over120min.
- M30: delete each of the six children of latest expected parent; all six deletions block, even if previous pair exists. Late child delivery at decision+5 also blocks. `test_each_m30_child_missing_and_no_stale_fallback`.

Reproduction: run `audit_squeeze.py` into a fresh audit folder, then this tool against its `reconstructed.json.gz`. Every source read uses exact attested2023 byte budget; no native TF or later-year row is opened.
