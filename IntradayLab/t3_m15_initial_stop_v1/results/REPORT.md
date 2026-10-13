# T3/M15 Initial Stop v1 — полный 2023–2024

**GROSS_ONLY / COSTS_DEFERRED / NOT_LIVE_READY**. Все 2023–2024 development-exposed.

## Вывод по заданной цели

Численно достигли pooled Gross PF ≥2,0: 0 из 6 самостоятельных вариантов I1/I2/I3 на двух trailing. Цель полного периода не достигнута ни одним вариантом.

Экономическое преимущество и исполнимость не доказаны; автоматического PASS и выбора победителя нет. Узкие Stop порядка одного–двух тиков нельзя считать доказательством экономического преимущества. Снижение знаменателя R влияет на вес сделок в PF: ниже отдельно приведена нормализация на исходные 2×ATR.

## Полный период, четыре инструмента

### ACTUAL_INITIAL_RISK

Основная Gross R: прибыль в цене / фактический фиксированный первоначальный риск.

| version | rule | closed_trades | open_positions_at_period_end | gross_PF | gross_R | expectancy_R | max_drawdown_closed_R | max_consecutive_losses | positive_months | negative_months | zero_months | worst_month | worst_month_R |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BASELINE | CONTROL | 741 | 1 | 1.4542 | 144.4112 | 0.1949 | 23.6765 | 14 | 15 | 9 | 0 | 2023-08 | -8.4431 |
| BASELINE | I1 | 848 | 1 | 1.2386 | 130.7181 | 0.1541 | 88.6450 | 25 | 15 | 9 | 0 | 2024-02 | -27.0620 |
| BASELINE | I2 | 1100 | 1 | 1.3209 | 335.3870 | 0.3049 | 129.5899 | 39 | 13 | 11 | 0 | 2023-08 | -42.0262 |
| BASELINE | I3 | 853 | 1 | 1.2366 | 133.1402 | 0.1561 | 90.8033 | 25 | 14 | 10 | 0 | 2024-02 | -27.4249 |
| OPTIMIZED | CONTROL | 701 | 1 | 1.5462 | 178.7198 | 0.2549 | 26.1261 | 13 | 17 | 7 | 0 | 2023-08 | -9.4074 |
| OPTIMIZED | I1 | 819 | 1 | 1.3598 | 199.6470 | 0.2438 | 90.5950 | 23 | 14 | 10 | 0 | 2024-02 | -27.9261 |
| OPTIMIZED | I2 | 1074 | 1 | 1.2877 | 294.1281 | 0.2739 | 146.3975 | 39 | 13 | 11 | 0 | 2024-04 | -54.4655 |
| OPTIMIZED | I3 | 824 | 1 | 1.3566 | 202.5164 | 0.2458 | 92.7048 | 23 | 14 | 10 | 0 | 2024-02 | -28.3463 |

### REFERENCE_2ATR

Диагностика: та же прибыль в цене / (2×ATR при входе). Это отдельная метрика, не подмена основной Gross R.

| version | rule | closed_trades | open_positions_at_period_end | gross_PF | gross_R | expectancy_R | max_drawdown_closed_R | max_consecutive_losses | positive_months | negative_months | zero_months | worst_month | worst_month_R |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BASELINE | CONTROL | 741 | 1 | 1.4542 | 144.4112 | 0.1949 | 23.6765 | 14 | 15 | 9 | 0 | 2023-08 | -8.4431 |
| BASELINE | I1 | 848 | 1 | 1.2692 | 85.1526 | 0.1004 | 50.6420 | 25 | 15 | 9 | 0 | 2024-02 | -15.7384 |
| BASELINE | I2 | 1100 | 1 | 1.3039 | 72.7731 | 0.0662 | 36.5489 | 39 | 13 | 11 | 0 | 2023-08 | -9.5582 |
| BASELINE | I3 | 853 | 1 | 1.2670 | 84.2358 | 0.0988 | 51.3453 | 25 | 15 | 9 | 0 | 2024-02 | -15.1954 |
| OPTIMIZED | CONTROL | 701 | 1 | 1.5462 | 178.7198 | 0.2549 | 26.1261 | 13 | 17 | 7 | 0 | 2023-08 | -9.4074 |
| OPTIMIZED | I1 | 819 | 1 | 1.3409 | 109.6671 | 0.1339 | 51.7218 | 23 | 15 | 9 | 0 | 2024-02 | -16.5099 |
| OPTIMIZED | I2 | 1074 | 1 | 1.3760 | 89.7839 | 0.0836 | 38.4262 | 39 | 14 | 10 | 0 | 2023-08 | -9.7897 |
| OPTIMIZED | I3 | 824 | 1 | 1.3494 | 111.2746 | 0.1350 | 50.6541 | 23 | 15 | 9 | 0 | 2024-02 | -15.7031 |

## По годам, четыре инструмента

CLOSED отнесены к году исторической метки exit-bar Close в МСК. OPEN — фактические позиции на последней доступной свече перед границей года, без ликвидации. Количество OPEN в 2023 не означает терминальную позицию в полном replay.

| version | rule | normalization | year | closed_trades | open_positions_at_period_end | gross_PF | gross_R | expectancy_R | max_drawdown_closed_R | positive_months | negative_months | zero_months | worst_month | worst_month_R |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BASELINE | CONTROL | ACTUAL_INITIAL_RISK | 2023 | 256 | 0 | 1.9482 | 94.2049 | 0.3680 | 13.2041 | 9 | 3 | 0 | 2023-08 | -8.4431 |
| BASELINE | CONTROL | ACTUAL_INITIAL_RISK | 2024 | 485 | 1 | 1.2296 | 50.2063 | 0.1035 | 23.6765 | 6 | 6 | 0 | 2024-10 | -4.2789 |
| BASELINE | CONTROL | REFERENCE_2ATR | 2023 | 256 | 0 | 1.9482 | 94.2049 | 0.3680 | 13.2041 | 9 | 3 | 0 | 2023-08 | -8.4431 |
| BASELINE | CONTROL | REFERENCE_2ATR | 2024 | 485 | 1 | 1.2296 | 50.2063 | 0.1035 | 23.6765 | 6 | 6 | 0 | 2024-10 | -4.2789 |
| BASELINE | I1 | ACTUAL_INITIAL_RISK | 2023 | 289 | 0 | 1.6629 | 111.0092 | 0.3841 | 28.0722 | 9 | 3 | 0 | 2023-08 | -16.8970 |
| BASELINE | I1 | ACTUAL_INITIAL_RISK | 2024 | 559 | 1 | 1.0518 | 19.7088 | 0.0353 | 88.6450 | 6 | 6 | 0 | 2024-02 | -27.0620 |
| BASELINE | I1 | REFERENCE_2ATR | 2023 | 289 | 0 | 1.7586 | 75.6377 | 0.2617 | 16.5085 | 9 | 3 | 0 | 2023-08 | -10.1880 |
| BASELINE | I1 | REFERENCE_2ATR | 2024 | 559 | 1 | 1.0439 | 9.5150 | 0.0170 | 50.6420 | 6 | 6 | 0 | 2024-02 | -15.7384 |
| BASELINE | I2 | ACTUAL_INITIAL_RISK | 2023 | 381 | 0 | 1.2332 | 83.8025 | 0.2200 | 70.5018 | 7 | 5 | 0 | 2023-08 | -42.0262 |
| BASELINE | I2 | ACTUAL_INITIAL_RISK | 2024 | 719 | 1 | 1.3668 | 251.5844 | 0.3499 | 129.5899 | 6 | 6 | 0 | 2024-03 | -41.2601 |
| BASELINE | I2 | REFERENCE_2ATR | 2023 | 381 | 0 | 1.5481 | 47.0272 | 0.1234 | 16.3288 | 8 | 4 | 0 | 2023-08 | -9.5582 |
| BASELINE | I2 | REFERENCE_2ATR | 2024 | 719 | 1 | 1.1675 | 25.7459 | 0.0358 | 36.5489 | 5 | 7 | 0 | 2024-02 | -8.2877 |
| BASELINE | I3 | ACTUAL_INITIAL_RISK | 2023 | 291 | 0 | 1.6534 | 112.8082 | 0.3877 | 27.9372 | 9 | 3 | 0 | 2023-08 | -17.1220 |
| BASELINE | I3 | ACTUAL_INITIAL_RISK | 2024 | 562 | 1 | 1.0521 | 20.3320 | 0.0362 | 90.8033 | 5 | 7 | 0 | 2024-02 | -27.4249 |
| BASELINE | I3 | REFERENCE_2ATR | 2023 | 291 | 0 | 1.7465 | 74.3273 | 0.2554 | 16.1293 | 9 | 3 | 0 | 2023-08 | -10.1880 |
| BASELINE | I3 | REFERENCE_2ATR | 2024 | 562 | 1 | 1.0459 | 9.9085 | 0.0176 | 51.3453 | 6 | 6 | 0 | 2024-02 | -15.1954 |
| OPTIMIZED | CONTROL | ACTUAL_INITIAL_RISK | 2023 | 243 | 0 | 1.9252 | 98.6178 | 0.4058 | 14.6437 | 9 | 3 | 0 | 2023-08 | -9.4074 |
| OPTIMIZED | CONTROL | ACTUAL_INITIAL_RISK | 2024 | 458 | 1 | 1.3631 | 80.1020 | 0.1749 | 26.1261 | 8 | 4 | 0 | 2024-10 | -2.4057 |
| OPTIMIZED | CONTROL | REFERENCE_2ATR | 2023 | 243 | 0 | 1.9252 | 98.6178 | 0.4058 | 14.6437 | 9 | 3 | 0 | 2023-08 | -9.4074 |
| OPTIMIZED | CONTROL | REFERENCE_2ATR | 2024 | 458 | 1 | 1.3631 | 80.1020 | 0.1749 | 26.1261 | 8 | 4 | 0 | 2024-10 | -2.4057 |
| OPTIMIZED | I1 | ACTUAL_INITIAL_RISK | 2023 | 280 | 0 | 1.7490 | 131.2061 | 0.4686 | 32.0725 | 8 | 4 | 0 | 2023-08 | -18.8515 |
| OPTIMIZED | I1 | ACTUAL_INITIAL_RISK | 2024 | 539 | 1 | 1.1802 | 68.4409 | 0.1270 | 90.5950 | 6 | 6 | 0 | 2024-02 | -27.9261 |
| OPTIMIZED | I1 | REFERENCE_2ATR | 2023 | 280 | 0 | 1.7261 | 77.5453 | 0.2769 | 16.3819 | 8 | 4 | 0 | 2023-08 | -9.6465 |
| OPTIMIZED | I1 | REFERENCE_2ATR | 2024 | 539 | 1 | 1.1495 | 32.1218 | 0.0596 | 50.1912 | 7 | 5 | 0 | 2024-02 | -16.5099 |
| OPTIMIZED | I2 | ACTUAL_INITIAL_RISK | 2023 | 372 | 0 | 1.1800 | 64.2518 | 0.1727 | 71.6076 | 7 | 5 | 0 | 2023-08 | -42.1812 |
| OPTIMIZED | I2 | ACTUAL_INITIAL_RISK | 2024 | 702 | 1 | 1.3455 | 229.8762 | 0.3275 | 146.3975 | 6 | 6 | 0 | 2024-04 | -54.4655 |
| OPTIMIZED | I2 | REFERENCE_2ATR | 2023 | 372 | 0 | 1.5518 | 48.4398 | 0.1302 | 16.7227 | 8 | 4 | 0 | 2023-08 | -9.7897 |
| OPTIMIZED | I2 | REFERENCE_2ATR | 2024 | 702 | 1 | 1.2739 | 41.3441 | 0.0589 | 38.1984 | 6 | 6 | 0 | 2024-02 | -9.6369 |
| OPTIMIZED | I3 | ACTUAL_INITIAL_RISK | 2023 | 282 | 0 | 1.7359 | 132.6568 | 0.4704 | 30.6209 | 8 | 4 | 0 | 2023-08 | -19.1674 |
| OPTIMIZED | I3 | ACTUAL_INITIAL_RISK | 2024 | 542 | 1 | 1.1802 | 69.8596 | 0.1289 | 92.7048 | 6 | 6 | 0 | 2024-02 | -28.3463 |
| OPTIMIZED | I3 | REFERENCE_2ATR | 2023 | 282 | 0 | 1.7313 | 77.2177 | 0.2738 | 15.8160 | 8 | 4 | 0 | 2023-08 | -9.6465 |
| OPTIMIZED | I3 | REFERENCE_2ATR | 2024 | 542 | 1 | 1.1600 | 34.0569 | 0.0628 | 50.1669 | 7 | 5 | 0 | 2024-02 | -15.7031 |

## Концентрация и ноябрь 2024

| version | rule | normalization | top5_share_positive_R | top10_share_positive_R | gross_PF_without_top5 | gross_PF_without_top10 | gross_R_without_top10 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| BASELINE | CONTROL | ACTUAL_INITIAL_RISK | 0.0807 | 0.1432 | 1.3368 | 1.2459 | 78.1920 |
| BASELINE | CONTROL | REFERENCE_2ATR | 0.0807 | 0.1432 | 1.3368 | 1.2459 | 78.1920 |
| BASELINE | I1 | ACTUAL_INITIAL_RISK | 0.1187 | 0.1938 | 1.0915 | 0.9985 | -0.8170 |
| BASELINE | I1 | REFERENCE_2ATR | 0.0929 | 0.1629 | 1.1512 | 1.0625 | 19.7627 |
| BASELINE | I2 | ACTUAL_INITIAL_RISK | 0.2321 | 0.3540 | 1.0143 | 0.8533 | -153.3629 |
| BASELINE | I2 | REFERENCE_2ATR | 0.1112 | 0.1938 | 1.1588 | 1.0512 | 12.2528 |
| BASELINE | I3 | ACTUAL_INITIAL_RISK | 0.1158 | 0.1890 | 1.0934 | 1.0029 | 1.6051 |
| BASELINE | I3 | REFERENCE_2ATR | 0.0933 | 0.1636 | 1.1487 | 1.0597 | 18.8459 |
| OPTIMIZED | CONTROL | ACTUAL_INITIAL_RISK | 0.0963 | 0.1613 | 1.3972 | 1.2967 | 97.0883 |
| OPTIMIZED | CONTROL | REFERENCE_2ATR | 0.0963 | 0.1613 | 1.3972 | 1.2967 | 97.0883 |
| OPTIMIZED | I1 | ACTUAL_INITIAL_RISK | 0.1438 | 0.2354 | 1.1643 | 1.0397 | 22.0299 |
| OPTIMIZED | I1 | REFERENCE_2ATR | 0.1130 | 0.1891 | 1.1894 | 1.0873 | 28.0804 |
| OPTIMIZED | I2 | ACTUAL_INITIAL_RISK | 0.2295 | 0.3517 | 0.9923 | 0.8348 | -168.8464 |
| OPTIMIZED | I2 | REFERENCE_2ATR | 0.1234 | 0.2133 | 1.2063 | 1.0825 | 19.6899 |
| OPTIMIZED | I3 | ACTUAL_INITIAL_RISK | 0.1408 | 0.2305 | 1.1656 | 1.0438 | 24.8993 |
| OPTIMIZED | I3 | REFERENCE_2ATR | 0.1134 | 0.1899 | 1.1964 | 1.0932 | 29.6879 |

| version | rule | normalization | year | november_closed | november_R | full_PF | ex_november_PF | ex_november_R | ex_november_drawdown_R |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BASELINE | CONTROL | ACTUAL_INITIAL_RISK | ALL | 44 | 50.5287 | 1.4542 | 1.3072 | 93.8825 | 23.6765 |
| BASELINE | CONTROL | ACTUAL_INITIAL_RISK | 2024 | 44 | 50.5287 | 1.2296 | 0.9984 | -0.3224 | 23.6765 |
| BASELINE | CONTROL | REFERENCE_2ATR | ALL | 44 | 50.5287 | 1.4542 | 1.3072 | 93.8825 | 23.6765 |
| BASELINE | CONTROL | REFERENCE_2ATR | 2024 | 44 | 50.5287 | 1.2296 | 0.9984 | -0.3224 | 23.6765 |
| BASELINE | I1 | ACTUAL_INITIAL_RISK | ALL | 50 | 58.2090 | 1.2386 | 1.1396 | 72.5090 | 88.6450 |
| BASELINE | I1 | ACTUAL_INITIAL_RISK | 2024 | 50 | 58.2090 | 1.0518 | 0.8907 | -38.5002 | 88.6450 |
| BASELINE | I1 | REFERENCE_2ATR | ALL | 50 | 36.7401 | 1.2692 | 1.1616 | 48.4125 | 50.6420 |
| BASELINE | I1 | REFERENCE_2ATR | 2024 | 50 | 36.7401 | 1.0439 | 0.8638 | -27.2252 | 50.6420 |
| BASELINE | I2 | ACTUAL_INITIAL_RISK | ALL | 69 | 163.1010 | 1.3209 | 1.1751 | 172.2860 | 129.5899 |
| BASELINE | I2 | ACTUAL_INITIAL_RISK | 2024 | 69 | 163.1010 | 1.3668 | 1.1416 | 88.4834 | 129.5899 |
| BASELINE | I2 | REFERENCE_2ATR | ALL | 69 | 33.0361 | 1.3039 | 1.1772 | 39.7370 | 36.5489 |
| BASELINE | I2 | REFERENCE_2ATR | 2024 | 69 | 33.0361 | 1.1675 | 0.9474 | -7.2902 | 36.5489 |
| BASELINE | I3 | ACTUAL_INITIAL_RISK | ALL | 50 | 59.4134 | 1.2366 | 1.1380 | 73.7268 | 90.8033 |
| BASELINE | I3 | ACTUAL_INITIAL_RISK | 2024 | 50 | 59.4134 | 1.0521 | 0.8919 | -39.0814 | 90.8033 |
| BASELINE | I3 | REFERENCE_2ATR | ALL | 50 | 36.7401 | 1.2670 | 1.1589 | 47.4957 | 51.3453 |
| BASELINE | I3 | REFERENCE_2ATR | 2024 | 50 | 36.7401 | 1.0459 | 0.8654 | -26.8316 | 51.3453 |
| OPTIMIZED | CONTROL | ACTUAL_INITIAL_RISK | ALL | 39 | 54.1860 | 1.5462 | 1.3929 | 124.5338 | 26.1261 |
| OPTIMIZED | CONTROL | ACTUAL_INITIAL_RISK | 2024 | 39 | 54.1860 | 1.3631 | 1.1232 | 25.9160 | 26.1261 |
| OPTIMIZED | CONTROL | REFERENCE_2ATR | ALL | 39 | 54.1860 | 1.5462 | 1.3929 | 124.5338 | 26.1261 |
| OPTIMIZED | CONTROL | REFERENCE_2ATR | 2024 | 39 | 54.1860 | 1.3631 | 1.1232 | 25.9160 | 26.1261 |
| OPTIMIZED | I1 | ACTUAL_INITIAL_RISK | ALL | 46 | 71.9713 | 1.3598 | 1.2413 | 127.6758 | 90.5950 |
| OPTIMIZED | I1 | ACTUAL_INITIAL_RISK | 2024 | 46 | 71.9713 | 1.1802 | 0.9900 | -3.5303 | 90.5950 |
| OPTIMIZED | I1 | REFERENCE_2ATR | ALL | 46 | 42.1039 | 1.3409 | 1.2198 | 67.5632 | 51.7218 |
| OPTIMIZED | I1 | REFERENCE_2ATR | 2024 | 46 | 42.1039 | 1.1495 | 0.9502 | -9.9821 | 50.1912 |
| OPTIMIZED | I2 | ACTUAL_INITIAL_RISK | ALL | 64 | 136.2377 | 1.2877 | 1.1625 | 157.8904 | 146.3975 |
| OPTIMIZED | I2 | ACTUAL_INITIAL_RISK | 2024 | 64 | 136.2377 | 1.3455 | 1.1523 | 93.6386 | 146.3975 |
| OPTIMIZED | I2 | REFERENCE_2ATR | ALL | 64 | 38.6445 | 1.3760 | 1.2261 | 51.1394 | 38.4262 |
| OPTIMIZED | I2 | REFERENCE_2ATR | 2024 | 64 | 38.6445 | 1.2739 | 1.0195 | 2.6995 | 38.1984 |
| OPTIMIZED | I3 | ACTUAL_INITIAL_RISK | ALL | 46 | 72.8947 | 1.3566 | 1.2393 | 129.6217 | 92.7048 |
| OPTIMIZED | I3 | ACTUAL_INITIAL_RISK | 2024 | 46 | 72.8947 | 1.1802 | 0.9916 | -3.0351 | 92.7048 |
| OPTIMIZED | I3 | REFERENCE_2ATR | ALL | 46 | 42.1039 | 1.3494 | 1.2274 | 69.1707 | 50.6541 |
| OPTIMIZED | I3 | REFERENCE_2ATR | 2024 | 46 | 42.1039 | 1.1600 | 0.9595 | -8.0470 | 50.1669 |

Удаление ноября и top5/top10 — только описательная чувствительность; сделки не исключаются из основной оценки. Drawdown — сумма CLOSED R в порядке exit_time/instrument/trade_id; это не денежная или mark-to-market просадка.

## Первоначальный риск и пропуски

Распределения включают все принятые входы, включая терминальные OPEN. Тики биржевые: USD 0,01; CNY 0,01 до 27.09.2023 19:00 МСК и 0,001 после; GLD 0,1; IMOEX 0,5. Источники — сохранённая спецификация IntradayLab, раздел 2 и датированные ссылки MOEX. Полные исторические редакции не аттестованы. Исходные искусственные единицы C1 0,001 USD/CNY не используются как биржевые тики. Уровни Stop не округлены; геометрия тиков — диагностика, не гарантия допустимости заявки.

| version | rule | instrument | accepted_entries_including_terminal_open | risk_price_min | risk_price_median | risk_ATR_median | risk_exchange_ticks_min | risk_exchange_ticks_median | risk_le_1_tick | risk_le_2_ticks | risk_le_2_ticks_share |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BASELINE | CONTROL | USDRUBF | 226 | 0.1358 | 0.2620 | 2.0000 | 13.5823 | 26.2038 | 0 | 0 | 0.0000 |
| BASELINE | CONTROL | CNYRUBF | 199 | 0.0157 | 0.0376 | 2.0000 | 2.5702 | 28.1034 | 0 | 0 | 0.0000 |
| BASELINE | CONTROL | GLDRUBF | 178 | 10.4703 | 24.1403 | 2.0000 | 104.7027 | 241.4032 | 0 | 0 | 0.0000 |
| BASELINE | CONTROL | IMOEXF | 139 | 4.9179 | 14.0749 | 2.0000 | 9.8358 | 28.1498 | 0 | 0 | 0.0000 |
| BASELINE | I1 | USDRUBF | 248 | 0.0200 | 0.1500 | 1.2081 | 2.0000 | 15.0000 | 0 | 2 | 0.0081 |
| BASELINE | I1 | CNYRUBF | 228 | 0.0020 | 0.0225 | 1.1719 | 1.0000 | 15.0000 | 6 | 30 | 0.1316 |
| BASELINE | I1 | GLDRUBF | 201 | 0.9000 | 14.1000 | 1.1059 | 9.0000 | 141.0000 | 0 | 0 | 0.0000 |
| BASELINE | I1 | IMOEXF | 172 | 0.5000 | 7.5000 | 1.0800 | 1.0000 | 15.0000 | 1 | 5 | 0.0291 |
| BASELINE | I2 | USDRUBF | 326 | 0.0100 | 0.0600 | 0.4298 | 1.0000 | 6.0000 | 32 | 71 | 0.2178 |
| BASELINE | I2 | CNYRUBF | 291 | 0.0010 | 0.0100 | 0.4758 | 1.0000 | 5.0000 | 73 | 111 | 0.3814 |
| BASELINE | I2 | GLDRUBF | 265 | 0.1000 | 4.8000 | 0.3765 | 1.0000 | 48.0000 | 4 | 8 | 0.0302 |
| BASELINE | I2 | IMOEXF | 219 | 0.5000 | 2.5000 | 0.4117 | 1.0000 | 5.0000 | 27 | 58 | 0.2648 |
| BASELINE | I3 | USDRUBF | 248 | 0.0200 | 0.1500 | 1.2081 | 2.0000 | 15.0000 | 0 | 2 | 0.0081 |
| BASELINE | I3 | CNYRUBF | 230 | 0.0020 | 0.0215 | 1.1719 | 1.0000 | 15.0000 | 6 | 30 | 0.1304 |
| BASELINE | I3 | GLDRUBF | 203 | 0.9000 | 13.1000 | 1.0938 | 9.0000 | 131.0000 | 0 | 0 | 0.0000 |
| BASELINE | I3 | IMOEXF | 173 | 0.5000 | 7.2576 | 1.0960 | 1.0000 | 14.5151 | 1 | 5 | 0.0289 |
| OPTIMIZED | CONTROL | USDRUBF | 213 | 0.1358 | 0.2552 | 2.0000 | 13.5823 | 25.5154 | 0 | 0 | 0.0000 |
| OPTIMIZED | CONTROL | CNYRUBF | 188 | 0.0157 | 0.0368 | 2.0000 | 2.5702 | 27.9615 | 0 | 0 | 0.0000 |
| OPTIMIZED | CONTROL | GLDRUBF | 166 | 10.4703 | 23.9357 | 2.0000 | 104.7027 | 239.3565 | 0 | 0 | 0.0000 |
| OPTIMIZED | CONTROL | IMOEXF | 135 | 4.9179 | 14.0749 | 2.0000 | 9.8358 | 28.1498 | 0 | 0 | 0.0000 |
| OPTIMIZED | I1 | USDRUBF | 239 | 0.0200 | 0.1500 | 1.1931 | 2.0000 | 15.0000 | 0 | 2 | 0.0084 |
| OPTIMIZED | I1 | CNYRUBF | 223 | 0.0020 | 0.0220 | 1.1649 | 1.0000 | 14.0000 | 6 | 30 | 0.1345 |
| OPTIMIZED | I1 | GLDRUBF | 190 | 0.9000 | 12.8500 | 1.0804 | 9.0000 | 128.5000 | 0 | 0 | 0.0000 |
| OPTIMIZED | I1 | IMOEXF | 168 | 0.5000 | 7.5000 | 1.0800 | 1.0000 | 15.0000 | 1 | 5 | 0.0298 |
| OPTIMIZED | I2 | USDRUBF | 321 | 0.0100 | 0.0600 | 0.4293 | 1.0000 | 6.0000 | 31 | 70 | 0.2181 |
| OPTIMIZED | I2 | CNYRUBF | 289 | 0.0010 | 0.0100 | 0.4752 | 1.0000 | 5.0000 | 73 | 111 | 0.3841 |
| OPTIMIZED | I2 | GLDRUBF | 252 | 0.1000 | 4.7000 | 0.3741 | 1.0000 | 47.0000 | 4 | 8 | 0.0317 |
| OPTIMIZED | I2 | IMOEXF | 213 | 0.5000 | 2.5000 | 0.4122 | 1.0000 | 5.0000 | 25 | 55 | 0.2582 |
| OPTIMIZED | I3 | USDRUBF | 239 | 0.0200 | 0.1500 | 1.1931 | 2.0000 | 15.0000 | 0 | 2 | 0.0084 |
| OPTIMIZED | I3 | CNYRUBF | 225 | 0.0020 | 0.0210 | 1.1649 | 1.0000 | 15.0000 | 6 | 30 | 0.1333 |
| OPTIMIZED | I3 | GLDRUBF | 192 | 0.9000 | 12.7614 | 1.0644 | 9.0000 | 127.6141 | 0 | 0 | 0.0000 |
| OPTIMIZED | I3 | IMOEXF | 169 | 0.5000 | 7.5000 | 1.0960 | 1.0000 | 15.0000 | 1 | 5 | 0.0296 |

| version | rule | instrument | signal_opportunities | accepted | busy | invalid_candidate_count | invalid_unoccupied_skipped | nonpositive_risk | nonfinite_risk | fallbacks |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BASELINE | CONTROL | USDRUBF | 615 | 226 | 389 | 0 | 0 | 0 | 0 | 0 |
| BASELINE | CONTROL | CNYRUBF | 500 | 199 | 301 | 0 | 0 | 0 | 0 | 0 |
| BASELINE | CONTROL | GLDRUBF | 516 | 178 | 338 | 0 | 0 | 0 | 0 | 0 |
| BASELINE | CONTROL | IMOEXF | 386 | 139 | 247 | 0 | 0 | 0 | 0 | 0 |
| BASELINE | I1 | USDRUBF | 615 | 248 | 367 | 0 | 0 | 0 | 0 | 0 |
| BASELINE | I1 | CNYRUBF | 500 | 228 | 272 | 0 | 0 | 0 | 0 | 0 |
| BASELINE | I1 | GLDRUBF | 516 | 201 | 311 | 7 | 4 | 7 | 0 | 0 |
| BASELINE | I1 | IMOEXF | 386 | 172 | 213 | 2 | 1 | 2 | 0 | 0 |
| BASELINE | I2 | USDRUBF | 615 | 326 | 289 | 0 | 0 | 0 | 0 | 0 |
| BASELINE | I2 | CNYRUBF | 500 | 291 | 209 | 0 | 0 | 0 | 0 | 0 |
| BASELINE | I2 | GLDRUBF | 516 | 265 | 251 | 0 | 0 | 0 | 0 | 0 |
| BASELINE | I2 | IMOEXF | 386 | 219 | 167 | 0 | 0 | 0 | 0 | 0 |
| BASELINE | I3 | USDRUBF | 615 | 248 | 367 | 0 | 0 | 0 | 0 | 0 |
| BASELINE | I3 | CNYRUBF | 500 | 230 | 270 | 0 | 0 | 0 | 0 | 0 |
| BASELINE | I3 | GLDRUBF | 516 | 203 | 309 | 7 | 4 | 7 | 0 | 0 |
| BASELINE | I3 | IMOEXF | 386 | 173 | 212 | 2 | 1 | 2 | 0 | 0 |
| OPTIMIZED | CONTROL | USDRUBF | 615 | 213 | 402 | 0 | 0 | 0 | 0 | 0 |
| OPTIMIZED | CONTROL | CNYRUBF | 500 | 188 | 312 | 0 | 0 | 0 | 0 | 0 |
| OPTIMIZED | CONTROL | GLDRUBF | 516 | 166 | 350 | 0 | 0 | 0 | 0 | 0 |
| OPTIMIZED | CONTROL | IMOEXF | 386 | 135 | 251 | 0 | 0 | 0 | 0 | 0 |
| OPTIMIZED | I1 | USDRUBF | 615 | 239 | 376 | 0 | 0 | 0 | 0 | 0 |
| OPTIMIZED | I1 | CNYRUBF | 500 | 223 | 277 | 0 | 0 | 0 | 0 | 0 |
| OPTIMIZED | I1 | GLDRUBF | 516 | 190 | 323 | 7 | 3 | 7 | 0 | 0 |
| OPTIMIZED | I1 | IMOEXF | 386 | 168 | 217 | 2 | 1 | 2 | 0 | 0 |
| OPTIMIZED | I2 | USDRUBF | 615 | 321 | 294 | 0 | 0 | 0 | 0 | 0 |
| OPTIMIZED | I2 | CNYRUBF | 500 | 289 | 211 | 0 | 0 | 0 | 0 | 0 |
| OPTIMIZED | I2 | GLDRUBF | 516 | 252 | 264 | 0 | 0 | 0 | 0 | 0 |
| OPTIMIZED | I2 | IMOEXF | 386 | 213 | 173 | 0 | 0 | 0 | 0 | 0 |
| OPTIMIZED | I3 | USDRUBF | 615 | 239 | 376 | 0 | 0 | 0 | 0 | 0 |
| OPTIMIZED | I3 | CNYRUBF | 500 | 225 | 275 | 0 | 0 | 0 | 0 | 0 |
| OPTIMIZED | I3 | GLDRUBF | 516 | 192 | 321 | 7 | 3 | 7 | 0 | 0 |
| OPTIMIZED | I3 | IMOEXF | 386 | 169 | 216 | 2 | 1 | 2 | 0 | 0 |

Всего записей чрезвычайно узких принятых Stop ≤2 тиков: 640; гэпов с потерей >1R: 197. Полные строки сохранены в отдельных журналах; никакого нового фильтра по ним нет.

## Исходные крупные победители и занятость

| version | rule | control_large_winners_ge_2R | large_winner_entry_busy | large_winner_entry_invalid | large_winner_price_pnl_preserved | large_winner_reference_R_preserved | large_winner_actual_R_preserved | large_winners_turned_losses | missed_busy_entries | new_closed_entries | new_closed_losses |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BASELINE | I1 | 81 | 0 | 0 | 66 | 66 | 52 | 15 | 4 | 115 | 87 |
| BASELINE | I2 | 81 | 0 | 0 | 35 | 35 | 32 | 46 | 2 | 360 | 295 |
| BASELINE | I3 | 81 | 0 | 0 | 66 | 66 | 66 | 15 | 0 | 116 | 88 |
| OPTIMIZED | I1 | 90 | 0 | 0 | 67 | 67 | 58 | 23 | 4 | 125 | 94 |
| OPTIMIZED | I2 | 90 | 0 | 0 | 33 | 33 | 31 | 57 | 2 | 374 | 311 |
| OPTIMIZED | I3 | 90 | 0 | 0 | 67 | 67 | 67 | 23 | 0 | 126 | 94 |

Сохранение победителя показано в цене, R на исходных 2×ATR и R на новом риске отдельно. Рост actual R при сокращении цены выигрыша не считается сохранением экономического результата. trade_lineage.csv содержит каждый исходный CLOSED, причину пропуска и идентификатор занятой позиции; new_entries.csv содержит новые CLOSED.

## Данные и сопоставимость

Удалённый main проверен: `8513203e6e6d9f6995d9464ecd29bb75775400d3` (#497); данные `f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8`. Freeze commit `82662ac1db6280c9b788a76edc87f525b135f084`.

| instrument | used_candles | first_open | last_open | first_close | last_close |
| --- | --- | --- | --- | --- | --- |
| USDRUBF | 29890 | 2023-01-03T09:00:00+03:00 | 2024-12-30T23:45:00+03:00 | 2023-01-03T09:15:00+03:00 | 2024-12-31T00:00:00+03:00 |
| CNYRUBF | 29633 | 2023-01-03T09:00:00+03:00 | 2024-12-30T23:45:00+03:00 | 2023-01-03T09:15:00+03:00 | 2024-12-31T00:00:00+03:00 |
| GLDRUBF | 22189 | 2023-07-11T10:00:00+03:00 | 2024-12-30T23:45:00+03:00 | 2023-07-11T10:15:00+03:00 | 2024-12-31T00:00:00+03:00 |
| IMOEXF | 16593 | 2023-11-14T10:00:00+03:00 | 2024-12-30T23:45:00+03:00 | 2023-11-14T10:15:00+03:00 | 2024-12-31T00:00:00+03:00 |

Использованы все исходные доступные M15 2023–2024 с реальными поздними стартами. OHLC 2025+ не парсятся: оба timestamp-first парсера останавливаются перед ними; полнофайловый SHA — только непрозрачная проверка байтов. Raw OHLC не копируются в research-репозиторий.

Исторический вход по Close завершённой сигнальной свечи — **непроверенное предположение об исполнении**, сохранённое для сопоставимости. H1 использует исходные дневные порядковые блоки по четыре последовательных M15, только завершённые. EMA/ATR/ADX/Donchian пересекают дни, как в замороженном T3. Stop проверяется первым; неблагоприятный gap исполняется по Open; trailing после пережитой свечи действует со следующей. Одинаковая хронология LONG/SHORT, фиксированный первоначальный риск, повторные входы после выхода и перенос через день/год сохранены.

CONTROL проходит совпадение всех общих полей #490/#495: 1 442 CLOSED + 2 терминальных OPEN, численный допуск 1e−8. Исторические C1/net и искусственные C1 tick units исключены из сопоставления и расчётов.

## Все календарные месяцы

Для каждого инструмента показаны все 24 месяца. До старта — NO_COVERAGE, нулевой CLOSED R; такие месяцы не являются положительными. В overall_report.csv дополнительно указан знаменатель и положительная доля только среди месяцев покрытия. Закрытая месячная сумма может не отражать накопленный PnL удерживаемой позиции.

### ALL_FOUR / ACTUAL_INITIAL_RISK

| version | rule | month | coverage | closed_trades | gross_PF | gross_R |
| --- | --- | --- | --- | --- | --- | --- |
| BASELINE | CONTROL | 2023-01 | AVAILABLE | 7 | 2.3802 | 3.8099 |
| BASELINE | CONTROL | 2023-02 | AVAILABLE | 15 | 1.7799 | 4.1951 |
| BASELINE | CONTROL | 2023-03 | AVAILABLE | 13 | 0.2443 | -6.2022 |
| BASELINE | CONTROL | 2023-04 | AVAILABLE | 14 | 9.6212 | 29.3412 |
| BASELINE | CONTROL | 2023-05 | AVAILABLE | 20 | 0.6320 | -3.3071 |
| BASELINE | CONTROL | 2023-06 | AVAILABLE | 15 | 1.2821 | 2.0233 |
| BASELINE | CONTROL | 2023-07 | AVAILABLE | 18 | 3.9954 | 17.3426 |
| BASELINE | CONTROL | 2023-08 | AVAILABLE | 36 | 0.5059 | -8.4431 |
| BASELINE | CONTROL | 2023-09 | AVAILABLE | 19 | 1.6277 | 5.8414 |
| BASELINE | CONTROL | 2023-10 | AVAILABLE | 33 | 4.3118 | 21.5526 |
| BASELINE | CONTROL | 2023-11 | AVAILABLE | 28 | 1.7153 | 8.1545 |
| BASELINE | CONTROL | 2023-12 | AVAILABLE | 38 | 2.4903 | 19.8967 |
| BASELINE | CONTROL | 2024-01 | AVAILABLE | 32 | 1.3380 | 4.2609 |
| BASELINE | CONTROL | 2024-02 | AVAILABLE | 39 | 0.8221 | -3.2939 |
| BASELINE | CONTROL | 2024-03 | AVAILABLE | 38 | 0.9495 | -0.9280 |
| BASELINE | CONTROL | 2024-04 | AVAILABLE | 49 | 0.9695 | -0.6988 |
| BASELINE | CONTROL | 2024-05 | AVAILABLE | 42 | 0.9038 | -1.6710 |
| BASELINE | CONTROL | 2024-06 | AVAILABLE | 43 | 0.8411 | -3.4411 |
| BASELINE | CONTROL | 2024-07 | AVAILABLE | 36 | 1.1961 | 3.4609 |
| BASELINE | CONTROL | 2024-08 | AVAILABLE | 43 | 1.0295 | 0.6238 |
| BASELINE | CONTROL | 2024-09 | AVAILABLE | 36 | 1.2716 | 3.8486 |
| BASELINE | CONTROL | 2024-10 | AVAILABLE | 42 | 0.7956 | -4.2789 |
| BASELINE | CONTROL | 2024-11 | AVAILABLE | 44 | 5.0903 | 50.5287 |
| BASELINE | CONTROL | 2024-12 | AVAILABLE | 41 | 1.0858 | 1.7951 |
| BASELINE | I1 | 2023-01 | AVAILABLE | 8 | 1.4713 | 2.1761 |
| BASELINE | I1 | 2023-02 | AVAILABLE | 18 | 1.2154 | 2.5070 |
| BASELINE | I1 | 2023-03 | AVAILABLE | 13 | 0.3559 | -5.6780 |
| BASELINE | I1 | 2023-04 | AVAILABLE | 18 | 5.7382 | 44.4282 |
| BASELINE | I1 | 2023-05 | AVAILABLE | 21 | 0.7150 | -3.1974 |
| BASELINE | I1 | 2023-06 | AVAILABLE | 17 | 1.1515 | 1.7507 |
| BASELINE | I1 | 2023-07 | AVAILABLE | 22 | 2.2240 | 14.8124 |
| BASELINE | I1 | 2023-08 | AVAILABLE | 41 | 0.4583 | -16.8970 |
| BASELINE | I1 | 2023-09 | AVAILABLE | 20 | 1.4944 | 5.7929 |
| BASELINE | I1 | 2023-10 | AVAILABLE | 36 | 2.7031 | 26.1139 |
| BASELINE | I1 | 2023-11 | AVAILABLE | 30 | 2.5308 | 21.7506 |
| BASELINE | I1 | 2023-12 | AVAILABLE | 45 | 1.6795 | 17.4500 |
| BASELINE | I1 | 2024-01 | AVAILABLE | 33 | 1.8935 | 16.4099 |
| BASELINE | I1 | 2024-02 | AVAILABLE | 50 | 0.3823 | -27.0620 |
| BASELINE | I1 | 2024-03 | AVAILABLE | 47 | 0.5004 | -16.3790 |
| BASELINE | I1 | 2024-04 | AVAILABLE | 56 | 0.8244 | -6.7898 |
| BASELINE | I1 | 2024-05 | AVAILABLE | 54 | 0.6812 | -11.8896 |
| BASELINE | I1 | 2024-06 | AVAILABLE | 48 | 0.6215 | -12.6912 |
| BASELINE | I1 | 2024-07 | AVAILABLE | 41 | 1.0198 | 0.5199 |
| BASELINE | I1 | 2024-08 | AVAILABLE | 49 | 1.2431 | 7.9114 |
| BASELINE | I1 | 2024-09 | AVAILABLE | 40 | 1.1200 | 2.8708 |
| BASELINE | I1 | 2024-10 | AVAILABLE | 44 | 0.9516 | -1.4423 |
| BASELINE | I1 | 2024-11 | AVAILABLE | 50 | 3.0525 | 58.2090 |
| BASELINE | I1 | 2024-12 | AVAILABLE | 47 | 1.2860 | 10.0417 |
| BASELINE | I2 | 2023-01 | AVAILABLE | 9 | 1.3355 | 2.2752 |
| BASELINE | I2 | 2023-02 | AVAILABLE | 25 | 1.1699 | 3.8101 |
| BASELINE | I2 | 2023-03 | AVAILABLE | 14 | 0.3142 | -8.2296 |
| BASELINE | I2 | 2023-04 | AVAILABLE | 27 | 3.9598 | 65.0171 |
| BASELINE | I2 | 2023-05 | AVAILABLE | 27 | 0.5586 | -9.5226 |
| BASELINE | I2 | 2023-06 | AVAILABLE | 25 | 0.7834 | -4.7270 |
| BASELINE | I2 | 2023-07 | AVAILABLE | 29 | 1.2306 | 7.0863 |
| BASELINE | I2 | 2023-08 | AVAILABLE | 52 | 0.2660 | -42.0262 |
| BASELINE | I2 | 2023-09 | AVAILABLE | 23 | 1.4609 | 8.2327 |
| BASELINE | I2 | 2023-10 | AVAILABLE | 57 | 0.9043 | -6.9151 |
| BASELINE | I2 | 2023-11 | AVAILABLE | 32 | 4.1176 | 65.2815 |
| BASELINE | I2 | 2023-12 | AVAILABLE | 61 | 1.0656 | 3.5201 |
| BASELINE | I2 | 2024-01 | AVAILABLE | 43 | 1.1153 | 4.0599 |
| BASELINE | I2 | 2024-02 | AVAILABLE | 59 | 0.4205 | -37.4585 |
| BASELINE | I2 | 2024-03 | AVAILABLE | 60 | 0.2250 | -41.2601 |
| BASELINE | I2 | 2024-04 | AVAILABLE | 79 | 0.6146 | -34.7330 |
| BASELINE | I2 | 2024-05 | AVAILABLE | 66 | 2.4559 | 86.6757 |
| BASELINE | I2 | 2024-06 | AVAILABLE | 54 | 0.7482 | -12.3824 |
| BASELINE | I2 | 2024-07 | AVAILABLE | 56 | 0.5473 | -23.0924 |
| BASELINE | I2 | 2024-08 | AVAILABLE | 62 | 1.4456 | 28.4167 |
| BASELINE | I2 | 2024-09 | AVAILABLE | 49 | 1.0860 | 4.4710 |
| BASELINE | I2 | 2024-10 | AVAILABLE | 61 | 0.9625 | -2.0205 |
| BASELINE | I2 | 2024-11 | AVAILABLE | 69 | 3.6651 | 163.1010 |
| BASELINE | I2 | 2024-12 | AVAILABLE | 61 | 3.2198 | 115.8070 |
| BASELINE | I3 | 2023-01 | AVAILABLE | 8 | 1.3586 | 1.7931 |
| BASELINE | I3 | 2023-02 | AVAILABLE | 18 | 1.2136 | 2.4897 |
| BASELINE | I3 | 2023-03 | AVAILABLE | 13 | 0.3556 | -5.6848 |
| BASELINE | I3 | 2023-04 | AVAILABLE | 18 | 5.7382 | 44.4282 |
| BASELINE | I3 | 2023-05 | AVAILABLE | 21 | 0.7177 | -3.2889 |
| BASELINE | I3 | 2023-06 | AVAILABLE | 17 | 1.1392 | 1.6523 |
| BASELINE | I3 | 2023-07 | AVAILABLE | 22 | 2.3671 | 16.7754 |
| BASELINE | I3 | 2023-08 | AVAILABLE | 41 | 0.4550 | -17.1220 |
| BASELINE | I3 | 2023-09 | AVAILABLE | 22 | 1.2492 | 3.5720 |
| BASELINE | I3 | 2023-10 | AVAILABLE | 36 | 2.8621 | 28.5516 |
| BASELINE | I3 | 2023-11 | AVAILABLE | 30 | 2.4220 | 21.5527 |
| BASELINE | I3 | 2023-12 | AVAILABLE | 45 | 1.7018 | 18.0890 |
| BASELINE | I3 | 2024-01 | AVAILABLE | 33 | 1.8884 | 16.4552 |
| BASELINE | I3 | 2024-02 | AVAILABLE | 50 | 0.3812 | -27.4249 |
| BASELINE | I3 | 2024-03 | AVAILABLE | 49 | 0.4480 | -20.1122 |
| BASELINE | I3 | 2024-04 | AVAILABLE | 56 | 0.8602 | -5.4148 |
| BASELINE | I3 | 2024-05 | AVAILABLE | 54 | 0.7158 | -10.6268 |
| BASELINE | I3 | 2024-06 | AVAILABLE | 48 | 0.6650 | -11.7846 |
| BASELINE | I3 | 2024-07 | AVAILABLE | 42 | 0.9649 | -0.9860 |
| BASELINE | I3 | 2024-08 | AVAILABLE | 49 | 1.2434 | 7.9212 |
| BASELINE | I3 | 2024-09 | AVAILABLE | 40 | 1.1416 | 3.3875 |
| BASELINE | I3 | 2024-10 | AVAILABLE | 44 | 0.9311 | -2.1013 |
| BASELINE | I3 | 2024-11 | AVAILABLE | 50 | 3.0802 | 59.4134 |
| BASELINE | I3 | 2024-12 | AVAILABLE | 47 | 1.3235 | 11.6054 |
| OPTIMIZED | CONTROL | 2023-01 | AVAILABLE | 7 | 2.0647 | 3.2090 |
| OPTIMIZED | CONTROL | 2023-02 | AVAILABLE | 13 | 2.3478 | 6.6877 |
| OPTIMIZED | CONTROL | 2023-03 | AVAILABLE | 13 | 0.1473 | -7.6677 |
| OPTIMIZED | CONTROL | 2023-04 | AVAILABLE | 13 | 11.1980 | 31.0016 |
| OPTIMIZED | CONTROL | 2023-05 | AVAILABLE | 20 | 0.4820 | -5.2475 |
| OPTIMIZED | CONTROL | 2023-06 | AVAILABLE | 13 | 1.7579 | 4.2143 |
| OPTIMIZED | CONTROL | 2023-07 | AVAILABLE | 16 | 3.4495 | 16.7258 |
| OPTIMIZED | CONTROL | 2023-08 | AVAILABLE | 36 | 0.5382 | -9.4074 |
| OPTIMIZED | CONTROL | 2023-09 | AVAILABLE | 18 | 1.7789 | 7.3847 |
| OPTIMIZED | CONTROL | 2023-10 | AVAILABLE | 30 | 5.2308 | 27.7491 |
| OPTIMIZED | CONTROL | 2023-11 | AVAILABLE | 28 | 1.3138 | 4.0809 |
| OPTIMIZED | CONTROL | 2023-12 | AVAILABLE | 36 | 2.3574 | 19.8874 |
| OPTIMIZED | CONTROL | 2024-01 | AVAILABLE | 32 | 1.2532 | 3.4461 |
| OPTIMIZED | CONTROL | 2024-02 | AVAILABLE | 36 | 0.9175 | -1.4773 |
| OPTIMIZED | CONTROL | 2024-03 | AVAILABLE | 36 | 1.1589 | 3.0465 |
| OPTIMIZED | CONTROL | 2024-04 | AVAILABLE | 48 | 0.9221 | -1.9484 |
| OPTIMIZED | CONTROL | 2024-05 | AVAILABLE | 41 | 0.9247 | -1.4023 |
| OPTIMIZED | CONTROL | 2024-06 | AVAILABLE | 41 | 1.2442 | 5.4406 |
| OPTIMIZED | CONTROL | 2024-07 | AVAILABLE | 35 | 1.1519 | 2.6465 |
| OPTIMIZED | CONTROL | 2024-08 | AVAILABLE | 40 | 1.1669 | 3.3666 |
| OPTIMIZED | CONTROL | 2024-09 | AVAILABLE | 34 | 1.4099 | 6.0285 |
| OPTIMIZED | CONTROL | 2024-10 | AVAILABLE | 40 | 0.8862 | -2.4057 |
| OPTIMIZED | CONTROL | 2024-11 | AVAILABLE | 39 | 6.2974 | 54.1860 |
| OPTIMIZED | CONTROL | 2024-12 | AVAILABLE | 36 | 1.4506 | 9.1748 |
| OPTIMIZED | I1 | 2023-01 | AVAILABLE | 8 | 1.3599 | 1.6981 |
| OPTIMIZED | I1 | 2023-02 | AVAILABLE | 17 | 1.8750 | 9.9440 |
| OPTIMIZED | I1 | 2023-03 | AVAILABLE | 13 | 0.2182 | -7.3973 |
| OPTIMIZED | I1 | 2023-04 | AVAILABLE | 18 | 4.9811 | 39.8609 |
| OPTIMIZED | I1 | 2023-05 | AVAILABLE | 21 | 0.5193 | -6.2739 |
| OPTIMIZED | I1 | 2023-06 | AVAILABLE | 17 | 0.9173 | -0.9821 |
| OPTIMIZED | I1 | 2023-07 | AVAILABLE | 19 | 3.7097 | 29.1047 |
| OPTIMIZED | I1 | 2023-08 | AVAILABLE | 41 | 0.4405 | -18.8515 |
| OPTIMIZED | I1 | 2023-09 | AVAILABLE | 20 | 1.5217 | 6.8656 |
| OPTIMIZED | I1 | 2023-10 | AVAILABLE | 33 | 3.4072 | 37.0051 |
| OPTIMIZED | I1 | 2023-11 | AVAILABLE | 30 | 1.9508 | 15.5881 |
| OPTIMIZED | I1 | 2023-12 | AVAILABLE | 43 | 1.9726 | 24.6442 |
| OPTIMIZED | I1 | 2024-01 | AVAILABLE | 33 | 1.6877 | 13.1492 |
| OPTIMIZED | I1 | 2024-02 | AVAILABLE | 49 | 0.3649 | -27.9261 |
| OPTIMIZED | I1 | 2024-03 | AVAILABLE | 46 | 0.6816 | -10.4888 |
| OPTIMIZED | I1 | 2024-04 | AVAILABLE | 55 | 0.8293 | -6.7905 |
| OPTIMIZED | I1 | 2024-05 | AVAILABLE | 54 | 0.5822 | -16.3232 |
| OPTIMIZED | I1 | 2024-06 | AVAILABLE | 46 | 0.9729 | -0.9018 |
| OPTIMIZED | I1 | 2024-07 | AVAILABLE | 40 | 0.9687 | -0.8321 |
| OPTIMIZED | I1 | 2024-08 | AVAILABLE | 47 | 1.2311 | 7.4525 |
| OPTIMIZED | I1 | 2024-09 | AVAILABLE | 37 | 1.3472 | 7.5950 |
| OPTIMIZED | I1 | 2024-10 | AVAILABLE | 43 | 1.0937 | 2.9173 |
| OPTIMIZED | I1 | 2024-11 | AVAILABLE | 46 | 3.7830 | 71.9713 |
| OPTIMIZED | I1 | 2024-12 | AVAILABLE | 43 | 1.8430 | 28.6181 |
| OPTIMIZED | I2 | 2023-01 | AVAILABLE | 9 | 1.2357 | 1.6321 |
| OPTIMIZED | I2 | 2023-02 | AVAILABLE | 25 | 1.0762 | 1.7531 |
| OPTIMIZED | I2 | 2023-03 | AVAILABLE | 14 | 0.2230 | -9.3235 |
| OPTIMIZED | I2 | 2023-04 | AVAILABLE | 27 | 3.5615 | 57.6231 |
| OPTIMIZED | I2 | 2023-05 | AVAILABLE | 27 | 0.4305 | -13.0874 |
| OPTIMIZED | I2 | 2023-06 | AVAILABLE | 25 | 0.5074 | -10.8378 |
| OPTIMIZED | I2 | 2023-07 | AVAILABLE | 27 | 1.4632 | 13.5350 |
| OPTIMIZED | I2 | 2023-08 | AVAILABLE | 52 | 0.2706 | -42.1812 |
| OPTIMIZED | I2 | 2023-09 | AVAILABLE | 22 | 1.5667 | 10.3496 |
| OPTIMIZED | I2 | 2023-10 | AVAILABLE | 55 | 0.8134 | -13.2271 |
| OPTIMIZED | I2 | 2023-11 | AVAILABLE | 32 | 3.3597 | 53.5481 |
| OPTIMIZED | I2 | 2023-12 | AVAILABLE | 57 | 1.2973 | 14.4677 |
| OPTIMIZED | I2 | 2024-01 | AVAILABLE | 43 | 1.0307 | 1.0911 |
| OPTIMIZED | I2 | 2024-02 | AVAILABLE | 59 | 0.3829 | -40.3943 |
| OPTIMIZED | I2 | 2024-03 | AVAILABLE | 57 | 0.3641 | -32.7423 |
| OPTIMIZED | I2 | 2024-04 | AVAILABLE | 79 | 0.3991 | -54.4655 |
| OPTIMIZED | I2 | 2024-05 | AVAILABLE | 66 | 2.3298 | 80.0810 |
| OPTIMIZED | I2 | 2024-06 | AVAILABLE | 53 | 0.8846 | -5.6474 |
| OPTIMIZED | I2 | 2024-07 | AVAILABLE | 55 | 0.5868 | -20.4744 |
| OPTIMIZED | I2 | 2024-08 | AVAILABLE | 60 | 1.4361 | 27.5449 |
| OPTIMIZED | I2 | 2024-09 | AVAILABLE | 47 | 1.5308 | 23.1972 |
| OPTIMIZED | I2 | 2024-10 | AVAILABLE | 61 | 0.7859 | -11.7745 |
| OPTIMIZED | I2 | 2024-11 | AVAILABLE | 64 | 3.6932 | 136.2377 |
| OPTIMIZED | I2 | 2024-12 | AVAILABLE | 58 | 3.4941 | 127.2228 |
| OPTIMIZED | I3 | 2023-01 | AVAILABLE | 8 | 1.2373 | 1.2308 |
| OPTIMIZED | I3 | 2023-02 | AVAILABLE | 17 | 1.8653 | 9.8846 |
| OPTIMIZED | I3 | 2023-03 | AVAILABLE | 13 | 0.2182 | -7.3973 |
| OPTIMIZED | I3 | 2023-04 | AVAILABLE | 18 | 4.9811 | 39.8609 |
| OPTIMIZED | I3 | 2023-05 | AVAILABLE | 21 | 0.5171 | -6.6099 |
| OPTIMIZED | I3 | 2023-06 | AVAILABLE | 17 | 0.9220 | -0.9365 |
| OPTIMIZED | I3 | 2023-07 | AVAILABLE | 19 | 3.8191 | 30.8724 |
| OPTIMIZED | I3 | 2023-08 | AVAILABLE | 41 | 0.4366 | -19.1674 |
| OPTIMIZED | I3 | 2023-09 | AVAILABLE | 22 | 1.3154 | 4.8682 |
| OPTIMIZED | I3 | 2023-10 | AVAILABLE | 33 | 3.5778 | 39.6280 |
| OPTIMIZED | I3 | 2023-11 | AVAILABLE | 30 | 1.8899 | 15.3636 |
| OPTIMIZED | I3 | 2023-12 | AVAILABLE | 43 | 1.9851 | 25.0596 |
| OPTIMIZED | I3 | 2024-01 | AVAILABLE | 33 | 1.7032 | 13.4461 |
| OPTIMIZED | I3 | 2024-02 | AVAILABLE | 49 | 0.3619 | -28.3463 |
| OPTIMIZED | I3 | 2024-03 | AVAILABLE | 48 | 0.6126 | -14.2146 |
| OPTIMIZED | I3 | 2024-04 | AVAILABLE | 55 | 0.8661 | -5.3418 |
| OPTIMIZED | I3 | 2024-05 | AVAILABLE | 54 | 0.6137 | -15.1042 |
| OPTIMIZED | I3 | 2024-06 | AVAILABLE | 46 | 0.9972 | -0.0958 |
| OPTIMIZED | I3 | 2024-07 | AVAILABLE | 41 | 0.9206 | -2.2326 |
| OPTIMIZED | I3 | 2024-08 | AVAILABLE | 47 | 1.2306 | 7.4392 |
| OPTIMIZED | I3 | 2024-09 | AVAILABLE | 37 | 1.3689 | 8.0702 |
| OPTIMIZED | I3 | 2024-10 | AVAILABLE | 43 | 1.0778 | 2.4624 |
| OPTIMIZED | I3 | 2024-11 | AVAILABLE | 46 | 3.7792 | 72.8947 |
| OPTIMIZED | I3 | 2024-12 | AVAILABLE | 43 | 1.9097 | 30.8824 |

### USDRUBF / ACTUAL_INITIAL_RISK

| version | rule | month | coverage | closed_trades | gross_PF | gross_R |
| --- | --- | --- | --- | --- | --- | --- |
| BASELINE | CONTROL | 2023-01 | AVAILABLE | 5 | 3.0896 | 4.1792 |
| BASELINE | CONTROL | 2023-02 | AVAILABLE | 8 | 2.2022 | 3.2765 |
| BASELINE | CONTROL | 2023-03 | AVAILABLE | 6 | 0.5459 | -1.0795 |
| BASELINE | CONTROL | 2023-04 | AVAILABLE | 6 | 16.7081 | 18.8632 |
| BASELINE | CONTROL | 2023-05 | AVAILABLE | 11 | 0.4611 | -2.1692 |
| BASELINE | CONTROL | 2023-06 | AVAILABLE | 10 | 1.5545 | 2.6715 |
| BASELINE | CONTROL | 2023-07 | AVAILABLE | 10 | 3.3093 | 8.8295 |
| BASELINE | CONTROL | 2023-08 | AVAILABLE | 14 | 1.0131 | 0.0854 |
| BASELINE | CONTROL | 2023-09 | AVAILABLE | 6 | 2.2010 | 3.4413 |
| BASELINE | CONTROL | 2023-10 | AVAILABLE | 14 | 8.3878 | 13.2261 |
| BASELINE | CONTROL | 2023-11 | AVAILABLE | 12 | 1.5949 | 2.4438 |
| BASELINE | CONTROL | 2023-12 | AVAILABLE | 9 | 6.6791 | 11.0910 |
| BASELINE | CONTROL | 2024-01 | AVAILABLE | 6 | 7.5247 | 4.4943 |
| BASELINE | CONTROL | 2024-02 | AVAILABLE | 7 | 0.5576 | -1.4710 |
| BASELINE | CONTROL | 2024-03 | AVAILABLE | 7 | 0.4109 | -2.1409 |
| BASELINE | CONTROL | 2024-04 | AVAILABLE | 11 | 0.3101 | -4.4527 |
| BASELINE | CONTROL | 2024-05 | AVAILABLE | 11 | 1.1444 | 0.6573 |
| BASELINE | CONTROL | 2024-06 | AVAILABLE | 10 | 1.0737 | 0.3641 |
| BASELINE | CONTROL | 2024-07 | AVAILABLE | 8 | 0.2584 | -4.0019 |
| BASELINE | CONTROL | 2024-08 | AVAILABLE | 10 | 1.9425 | 4.3981 |
| BASELINE | CONTROL | 2024-09 | AVAILABLE | 10 | 1.4762 | 2.0413 |
| BASELINE | CONTROL | 2024-10 | AVAILABLE | 13 | 0.3147 | -5.6307 |
| BASELINE | CONTROL | 2024-11 | AVAILABLE | 12 | 9.5997 | 11.6354 |
| BASELINE | CONTROL | 2024-12 | AVAILABLE | 10 | 0.7023 | -1.9950 |
| BASELINE | I1 | 2023-01 | AVAILABLE | 5 | 2.5001 | 3.9256 |
| BASELINE | I1 | 2023-02 | AVAILABLE | 9 | 2.1574 | 5.5501 |
| BASELINE | I1 | 2023-03 | AVAILABLE | 6 | 0.7511 | -0.7442 |
| BASELINE | I1 | 2023-04 | AVAILABLE | 7 | 12.6993 | 27.8042 |
| BASELINE | I1 | 2023-05 | AVAILABLE | 11 | 1.0148 | 0.0610 |
| BASELINE | I1 | 2023-06 | AVAILABLE | 11 | 1.5840 | 4.0275 |
| BASELINE | I1 | 2023-07 | AVAILABLE | 11 | 1.8968 | 5.9283 |
| BASELINE | I1 | 2023-08 | AVAILABLE | 17 | 0.9940 | -0.0672 |
| BASELINE | I1 | 2023-09 | AVAILABLE | 8 | 0.8095 | -1.0179 |
| BASELINE | I1 | 2023-10 | AVAILABLE | 14 | 4.8333 | 16.2802 |
| BASELINE | I1 | 2023-11 | AVAILABLE | 12 | 1.1124 | 0.5826 |
| BASELINE | I1 | 2023-12 | AVAILABLE | 11 | 3.1899 | 11.8117 |
| BASELINE | I1 | 2024-01 | AVAILABLE | 6 | 2.6281 | 3.2562 |
| BASELINE | I1 | 2024-02 | AVAILABLE | 9 | 0.0487 | -6.0301 |
| BASELINE | I1 | 2024-03 | AVAILABLE | 9 | 0.1913 | -5.7280 |
| BASELINE | I1 | 2024-04 | AVAILABLE | 14 | 0.0428 | -12.0532 |
| BASELINE | I1 | 2024-05 | AVAILABLE | 12 | 1.0745 | 0.4624 |
| BASELINE | I1 | 2024-06 | AVAILABLE | 10 | 0.4843 | -3.9982 |
| BASELINE | I1 | 2024-07 | AVAILABLE | 9 | 0.2493 | -6.0054 |
| BASELINE | I1 | 2024-08 | AVAILABLE | 9 | 3.7737 | 14.0170 |
| BASELINE | I1 | 2024-09 | AVAILABLE | 11 | 1.5015 | 3.7666 |
| BASELINE | I1 | 2024-10 | AVAILABLE | 13 | 0.6993 | -3.1120 |
| BASELINE | I1 | 2024-11 | AVAILABLE | 13 | 2.9616 | 11.9714 |
| BASELINE | I1 | 2024-12 | AVAILABLE | 11 | 1.1287 | 1.0848 |
| BASELINE | I2 | 2023-01 | AVAILABLE | 6 | 1.7893 | 3.7741 |
| BASELINE | I2 | 2023-02 | AVAILABLE | 15 | 1.5805 | 7.2131 |
| BASELINE | I2 | 2023-03 | AVAILABLE | 6 | 0.9426 | -0.2296 |
| BASELINE | I2 | 2023-04 | AVAILABLE | 14 | 5.5683 | 54.6688 |
| BASELINE | I2 | 2023-05 | AVAILABLE | 12 | 0.9751 | -0.2134 |
| BASELINE | I2 | 2023-06 | AVAILABLE | 15 | 1.2262 | 2.7149 |
| BASELINE | I2 | 2023-07 | AVAILABLE | 12 | 2.3300 | 11.3283 |
| BASELINE | I2 | 2023-08 | AVAILABLE | 25 | 0.5653 | -9.9988 |
| BASELINE | I2 | 2023-09 | AVAILABLE | 10 | 0.9268 | -0.6265 |
| BASELINE | I2 | 2023-10 | AVAILABLE | 22 | 1.6980 | 11.1696 |
| BASELINE | I2 | 2023-11 | AVAILABLE | 12 | 2.3003 | 7.8201 |
| BASELINE | I2 | 2023-12 | AVAILABLE | 17 | 1.1262 | 1.5148 |
| BASELINE | I2 | 2024-01 | AVAILABLE | 9 | 1.3681 | 2.5765 |
| BASELINE | I2 | 2024-02 | AVAILABLE | 14 | 0.0160 | -12.7925 |
| BASELINE | I2 | 2024-03 | AVAILABLE | 10 | 0.1649 | -7.2229 |
| BASELINE | I2 | 2024-04 | AVAILABLE | 18 | 0.0000 | -18.5000 |
| BASELINE | I2 | 2024-05 | AVAILABLE | 17 | 3.4087 | 40.1776 |
| BASELINE | I2 | 2024-06 | AVAILABLE | 11 | 0.7262 | -2.4807 |
| BASELINE | I2 | 2024-07 | AVAILABLE | 11 | 0.0799 | -9.2014 |
| BASELINE | I2 | 2024-08 | AVAILABLE | 13 | 3.1706 | 26.0473 |
| BASELINE | I2 | 2024-09 | AVAILABLE | 11 | 2.4722 | 16.1942 |
| BASELINE | I2 | 2024-10 | AVAILABLE | 16 | 0.0000 | -15.9003 |
| BASELINE | I2 | 2024-11 | AVAILABLE | 18 | 3.0087 | 24.1041 |
| BASELINE | I2 | 2024-12 | AVAILABLE | 12 | 2.2194 | 12.1938 |
| BASELINE | I3 | 2023-01 | AVAILABLE | 5 | 2.1808 | 3.5425 |
| BASELINE | I3 | 2023-02 | AVAILABLE | 9 | 2.1496 | 5.5328 |
| BASELINE | I3 | 2023-03 | AVAILABLE | 6 | 0.7511 | -0.7442 |
| BASELINE | I3 | 2023-04 | AVAILABLE | 7 | 12.6993 | 27.8042 |
| BASELINE | I3 | 2023-05 | AVAILABLE | 11 | 0.9191 | -0.3681 |
| BASELINE | I3 | 2023-06 | AVAILABLE | 11 | 1.6023 | 4.1857 |
| BASELINE | I3 | 2023-07 | AVAILABLE | 11 | 2.2123 | 8.0139 |
| BASELINE | I3 | 2023-08 | AVAILABLE | 17 | 0.9804 | -0.2207 |
| BASELINE | I3 | 2023-09 | AVAILABLE | 8 | 1.0248 | 0.1360 |
| BASELINE | I3 | 2023-10 | AVAILABLE | 14 | 5.2424 | 18.0176 |
| BASELINE | I3 | 2023-11 | AVAILABLE | 12 | 1.1626 | 0.9098 |
| BASELINE | I3 | 2023-12 | AVAILABLE | 11 | 3.2194 | 11.9709 |
| BASELINE | I3 | 2024-01 | AVAILABLE | 6 | 2.6448 | 3.2895 |
| BASELINE | I3 | 2024-02 | AVAILABLE | 9 | 0.0534 | -6.0001 |
| BASELINE | I3 | 2024-03 | AVAILABLE | 9 | 0.1873 | -5.8797 |
| BASELINE | I3 | 2024-04 | AVAILABLE | 14 | 0.0537 | -11.9159 |
| BASELINE | I3 | 2024-05 | AVAILABLE | 12 | 1.2137 | 1.3428 |
| BASELINE | I3 | 2024-06 | AVAILABLE | 10 | 0.6122 | -3.1434 |
| BASELINE | I3 | 2024-07 | AVAILABLE | 9 | 0.2493 | -6.0054 |
| BASELINE | I3 | 2024-08 | AVAILABLE | 9 | 3.7737 | 14.0170 |
| BASELINE | I3 | 2024-09 | AVAILABLE | 11 | 1.5015 | 3.7666 |
| BASELINE | I3 | 2024-10 | AVAILABLE | 13 | 0.6768 | -3.4559 |
| BASELINE | I3 | 2024-11 | AVAILABLE | 13 | 3.0670 | 12.6143 |
| BASELINE | I3 | 2024-12 | AVAILABLE | 11 | 1.0908 | 0.7923 |
| OPTIMIZED | CONTROL | 2023-01 | AVAILABLE | 5 | 2.9481 | 3.9826 |
| OPTIMIZED | CONTROL | 2023-02 | AVAILABLE | 7 | 2.6533 | 4.5087 |
| OPTIMIZED | CONTROL | 2023-03 | AVAILABLE | 6 | 0.2847 | -2.1402 |
| OPTIMIZED | CONTROL | 2023-04 | AVAILABLE | 6 | 11.8693 | 17.3654 |
| OPTIMIZED | CONTROL | 2023-05 | AVAILABLE | 11 | 0.3432 | -3.1868 |
| OPTIMIZED | CONTROL | 2023-06 | AVAILABLE | 8 | 2.8680 | 5.6041 |
| OPTIMIZED | CONTROL | 2023-07 | AVAILABLE | 9 | 3.1807 | 9.7958 |
| OPTIMIZED | CONTROL | 2023-08 | AVAILABLE | 13 | 1.1664 | 1.2642 |
| OPTIMIZED | CONTROL | 2023-09 | AVAILABLE | 6 | 1.9444 | 2.8701 |
| OPTIMIZED | CONTROL | 2023-10 | AVAILABLE | 11 | 22.9895 | 21.1407 |
| OPTIMIZED | CONTROL | 2023-11 | AVAILABLE | 12 | 1.0115 | 0.0593 |
| OPTIMIZED | CONTROL | 2023-12 | AVAILABLE | 9 | 5.2273 | 9.3931 |
| OPTIMIZED | CONTROL | 2024-01 | AVAILABLE | 6 | 4.7602 | 3.4129 |
| OPTIMIZED | CONTROL | 2024-02 | AVAILABLE | 7 | 0.3781 | -2.2770 |
| OPTIMIZED | CONTROL | 2024-03 | AVAILABLE | 6 | 0.6190 | -1.3987 |
| OPTIMIZED | CONTROL | 2024-04 | AVAILABLE | 11 | 0.2478 | -5.1868 |
| OPTIMIZED | CONTROL | 2024-05 | AVAILABLE | 11 | 0.9752 | -0.1200 |
| OPTIMIZED | CONTROL | 2024-06 | AVAILABLE | 10 | 0.9972 | -0.0159 |
| OPTIMIZED | CONTROL | 2024-07 | AVAILABLE | 8 | 0.2067 | -4.5106 |
| OPTIMIZED | CONTROL | 2024-08 | AVAILABLE | 10 | 1.7036 | 3.5368 |
| OPTIMIZED | CONTROL | 2024-09 | AVAILABLE | 10 | 1.9221 | 3.8513 |
| OPTIMIZED | CONTROL | 2024-10 | AVAILABLE | 11 | 0.8661 | -0.9562 |
| OPTIMIZED | CONTROL | 2024-11 | AVAILABLE | 11 | 8.3488 | 9.8895 |
| OPTIMIZED | CONTROL | 2024-12 | AVAILABLE | 9 | 0.8184 | -1.0626 |
| OPTIMIZED | I1 | 2023-01 | AVAILABLE | 5 | 2.4735 | 3.8225 |
| OPTIMIZED | I1 | 2023-02 | AVAILABLE | 8 | 4.1157 | 13.5981 |
| OPTIMIZED | I1 | 2023-03 | AVAILABLE | 6 | 0.4243 | -1.9930 |
| OPTIMIZED | I1 | 2023-04 | AVAILABLE | 7 | 9.7636 | 25.6339 |
| OPTIMIZED | I1 | 2023-05 | AVAILABLE | 11 | 0.6065 | -2.2044 |
| OPTIMIZED | I1 | 2023-06 | AVAILABLE | 11 | 1.3725 | 2.6076 |
| OPTIMIZED | I1 | 2023-07 | AVAILABLE | 9 | 5.3452 | 22.2936 |
| OPTIMIZED | I1 | 2023-08 | AVAILABLE | 16 | 0.9180 | -0.9467 |
| OPTIMIZED | I1 | 2023-09 | AVAILABLE | 8 | 0.6385 | -2.3249 |
| OPTIMIZED | I1 | 2023-10 | AVAILABLE | 11 | 14.0469 | 32.4431 |
| OPTIMIZED | I1 | 2023-11 | AVAILABLE | 12 | 0.6583 | -2.2787 |
| OPTIMIZED | I1 | 2023-12 | AVAILABLE | 11 | 2.6818 | 9.7174 |
| OPTIMIZED | I1 | 2024-01 | AVAILABLE | 6 | 2.1329 | 2.2657 |
| OPTIMIZED | I1 | 2024-02 | AVAILABLE | 9 | 0.0000 | -6.9256 |
| OPTIMIZED | I1 | 2024-03 | AVAILABLE | 9 | 0.1613 | -6.2700 |
| OPTIMIZED | I1 | 2024-04 | AVAILABLE | 14 | 0.0390 | -12.3278 |
| OPTIMIZED | I1 | 2024-05 | AVAILABLE | 12 | 0.7971 | -1.3606 |
| OPTIMIZED | I1 | 2024-06 | AVAILABLE | 10 | 0.5517 | -3.5333 |
| OPTIMIZED | I1 | 2024-07 | AVAILABLE | 9 | 0.1798 | -6.5619 |
| OPTIMIZED | I1 | 2024-08 | AVAILABLE | 9 | 3.2455 | 12.4417 |
| OPTIMIZED | I1 | 2024-09 | AVAILABLE | 11 | 1.4882 | 3.8685 |
| OPTIMIZED | I1 | 2024-10 | AVAILABLE | 12 | 1.3462 | 3.7475 |
| OPTIMIZED | I1 | 2024-11 | AVAILABLE | 13 | 2.5205 | 9.6498 |
| OPTIMIZED | I1 | 2024-12 | AVAILABLE | 10 | 1.3202 | 2.4338 |
| OPTIMIZED | I2 | 2023-01 | AVAILABLE | 6 | 1.8302 | 3.8808 |
| OPTIMIZED | I2 | 2023-02 | AVAILABLE | 15 | 1.4403 | 5.7233 |
| OPTIMIZED | I2 | 2023-03 | AVAILABLE | 6 | 0.6691 | -1.3235 |
| OPTIMIZED | I2 | 2023-04 | AVAILABLE | 14 | 5.0389 | 49.9399 |
| OPTIMIZED | I2 | 2023-05 | AVAILABLE | 12 | 0.6856 | -3.1385 |
| OPTIMIZED | I2 | 2023-06 | AVAILABLE | 15 | 0.8235 | -2.1184 |
| OPTIMIZED | I2 | 2023-07 | AVAILABLE | 10 | 3.6949 | 18.8643 |
| OPTIMIZED | I2 | 2023-08 | AVAILABLE | 25 | 0.5083 | -11.4162 |
| OPTIMIZED | I2 | 2023-09 | AVAILABLE | 10 | 0.8231 | -1.5918 |
| OPTIMIZED | I2 | 2023-10 | AVAILABLE | 20 | 1.8919 | 12.8732 |
| OPTIMIZED | I2 | 2023-11 | AVAILABLE | 12 | 1.4689 | 3.4958 |
| OPTIMIZED | I2 | 2023-12 | AVAILABLE | 17 | 0.8474 | -1.8574 |
| OPTIMIZED | I2 | 2024-01 | AVAILABLE | 9 | 1.2386 | 1.6704 |
| OPTIMIZED | I2 | 2024-02 | AVAILABLE | 14 | 0.0000 | -13.0913 |
| OPTIMIZED | I2 | 2024-03 | AVAILABLE | 10 | 0.1416 | -7.6968 |
| OPTIMIZED | I2 | 2024-04 | AVAILABLE | 18 | 0.0000 | -18.5000 |
| OPTIMIZED | I2 | 2024-05 | AVAILABLE | 17 | 3.0859 | 34.4177 |
| OPTIMIZED | I2 | 2024-06 | AVAILABLE | 11 | 0.8339 | -1.5272 |
| OPTIMIZED | I2 | 2024-07 | AVAILABLE | 11 | 0.0552 | -9.4479 |
| OPTIMIZED | I2 | 2024-08 | AVAILABLE | 13 | 2.9775 | 23.7297 |
| OPTIMIZED | I2 | 2024-09 | AVAILABLE | 11 | 2.6598 | 18.2573 |
| OPTIMIZED | I2 | 2024-10 | AVAILABLE | 16 | 0.0000 | -16.0000 |
| OPTIMIZED | I2 | 2024-11 | AVAILABLE | 18 | 2.5635 | 18.7626 |
| OPTIMIZED | I2 | 2024-12 | AVAILABLE | 11 | 2.5367 | 13.8303 |
| OPTIMIZED | I3 | 2023-01 | AVAILABLE | 5 | 2.0959 | 3.3552 |
| OPTIMIZED | I3 | 2023-02 | AVAILABLE | 8 | 4.0604 | 13.5386 |
| OPTIMIZED | I3 | 2023-03 | AVAILABLE | 6 | 0.4243 | -1.9930 |
| OPTIMIZED | I3 | 2023-04 | AVAILABLE | 7 | 9.7636 | 25.6339 |
| OPTIMIZED | I3 | 2023-05 | AVAILABLE | 11 | 0.5447 | -2.8406 |
| OPTIMIZED | I3 | 2023-06 | AVAILABLE | 11 | 1.3976 | 2.7829 |
| OPTIMIZED | I3 | 2023-07 | AVAILABLE | 9 | 5.7238 | 24.2361 |
| OPTIMIZED | I3 | 2023-08 | AVAILABLE | 16 | 0.9016 | -1.1588 |
| OPTIMIZED | I3 | 2023-09 | AVAILABLE | 8 | 0.8312 | -1.0856 |
| OPTIMIZED | I3 | 2023-10 | AVAILABLE | 11 | 14.8629 | 34.4721 |
| OPTIMIZED | I3 | 2023-11 | AVAILABLE | 12 | 0.7173 | -1.9796 |
| OPTIMIZED | I3 | 2023-12 | AVAILABLE | 11 | 2.7034 | 9.8425 |
| OPTIMIZED | I3 | 2024-01 | AVAILABLE | 6 | 2.1444 | 2.2889 |
| OPTIMIZED | I3 | 2024-02 | AVAILABLE | 9 | 0.0000 | -6.9380 |
| OPTIMIZED | I3 | 2024-03 | AVAILABLE | 9 | 0.1569 | -6.4802 |
| OPTIMIZED | I3 | 2024-04 | AVAILABLE | 14 | 0.0489 | -12.2005 |
| OPTIMIZED | I3 | 2024-05 | AVAILABLE | 12 | 0.9383 | -0.4138 |
| OPTIMIZED | I3 | 2024-06 | AVAILABLE | 10 | 0.6456 | -2.9823 |
| OPTIMIZED | I3 | 2024-07 | AVAILABLE | 9 | 0.1798 | -6.5619 |
| OPTIMIZED | I3 | 2024-08 | AVAILABLE | 9 | 3.2455 | 12.4417 |
| OPTIMIZED | I3 | 2024-09 | AVAILABLE | 11 | 1.4882 | 3.8685 |
| OPTIMIZED | I3 | 2024-10 | AVAILABLE | 12 | 1.3247 | 3.5714 |
| OPTIMIZED | I3 | 2024-11 | AVAILABLE | 13 | 2.6104 | 10.2207 |
| OPTIMIZED | I3 | 2024-12 | AVAILABLE | 10 | 1.3202 | 2.4338 |

### CNYRUBF / ACTUAL_INITIAL_RISK

| version | rule | month | coverage | closed_trades | gross_PF | gross_R |
| --- | --- | --- | --- | --- | --- | --- |
| BASELINE | CONTROL | 2023-01 | AVAILABLE | 2 | 0.5143 | -0.3694 |
| BASELINE | CONTROL | 2023-02 | AVAILABLE | 7 | 1.3462 | 0.9187 |
| BASELINE | CONTROL | 2023-03 | AVAILABLE | 7 | 0.1213 | -5.1227 |
| BASELINE | CONTROL | 2023-04 | AVAILABLE | 8 | 5.7573 | 10.4780 |
| BASELINE | CONTROL | 2023-05 | AVAILABLE | 9 | 0.7707 | -1.1379 |
| BASELINE | CONTROL | 2023-06 | AVAILABLE | 5 | 0.7247 | -0.6483 |
| BASELINE | CONTROL | 2023-07 | AVAILABLE | 4 | — | 10.3612 |
| BASELINE | CONTROL | 2023-08 | AVAILABLE | 9 | 0.0723 | -4.1957 |
| BASELINE | CONTROL | 2023-09 | AVAILABLE | 6 | 4.0780 | 4.5425 |
| BASELINE | CONTROL | 2023-10 | AVAILABLE | 11 | 4.1398 | 9.1544 |
| BASELINE | CONTROL | 2023-11 | AVAILABLE | 8 | 2.3373 | 4.0686 |
| BASELINE | CONTROL | 2023-12 | AVAILABLE | 9 | 1.2983 | 1.1197 |
| BASELINE | CONTROL | 2024-01 | AVAILABLE | 10 | 2.7342 | 4.2383 |
| BASELINE | CONTROL | 2024-02 | AVAILABLE | 12 | 0.3884 | -4.1524 |
| BASELINE | CONTROL | 2024-03 | AVAILABLE | 10 | 0.1870 | -4.7080 |
| BASELINE | CONTROL | 2024-04 | AVAILABLE | 9 | 1.7044 | 2.4827 |
| BASELINE | CONTROL | 2024-05 | AVAILABLE | 12 | 0.4171 | -3.9747 |
| BASELINE | CONTROL | 2024-06 | AVAILABLE | 10 | 1.3262 | 1.7962 |
| BASELINE | CONTROL | 2024-07 | AVAILABLE | 7 | 0.9518 | -0.1788 |
| BASELINE | CONTROL | 2024-08 | AVAILABLE | 8 | 0.2477 | -2.9852 |
| BASELINE | CONTROL | 2024-09 | AVAILABLE | 8 | 3.1857 | 3.8197 |
| BASELINE | CONTROL | 2024-10 | AVAILABLE | 8 | 1.3834 | 1.3057 |
| BASELINE | CONTROL | 2024-11 | AVAILABLE | 10 | 6.4841 | 14.0619 |
| BASELINE | CONTROL | 2024-12 | AVAILABLE | 10 | 1.9131 | 4.1577 |
| BASELINE | I1 | 2023-01 | AVAILABLE | 3 | 0.1253 | -1.7494 |
| BASELINE | I1 | 2023-02 | AVAILABLE | 9 | 0.5552 | -3.0431 |
| BASELINE | I1 | 2023-03 | AVAILABLE | 7 | 0.1530 | -4.9338 |
| BASELINE | I1 | 2023-04 | AVAILABLE | 11 | 3.3748 | 16.6239 |
| BASELINE | I1 | 2023-05 | AVAILABLE | 10 | 0.5410 | -3.2584 |
| BASELINE | I1 | 2023-06 | AVAILABLE | 6 | 0.5114 | -2.2768 |
| BASELINE | I1 | 2023-07 | AVAILABLE | 6 | 7.0795 | 12.1589 |
| BASELINE | I1 | 2023-08 | AVAILABLE | 11 | 0.0000 | -11.9077 |
| BASELINE | I1 | 2023-09 | AVAILABLE | 6 | 5.5422 | 7.5703 |
| BASELINE | I1 | 2023-10 | AVAILABLE | 11 | 5.0530 | 15.6884 |
| BASELINE | I1 | 2023-11 | AVAILABLE | 10 | 3.1840 | 10.9790 |
| BASELINE | I1 | 2023-12 | AVAILABLE | 10 | 1.5452 | 3.1893 |
| BASELINE | I1 | 2024-01 | AVAILABLE | 10 | 1.8279 | 3.3115 |
| BASELINE | I1 | 2024-02 | AVAILABLE | 14 | 0.1782 | -9.2113 |
| BASELINE | I1 | 2024-03 | AVAILABLE | 12 | 0.1339 | -8.8921 |
| BASELINE | I1 | 2024-04 | AVAILABLE | 10 | 1.4635 | 2.7953 |
| BASELINE | I1 | 2024-05 | AVAILABLE | 15 | 0.3512 | -7.5353 |
| BASELINE | I1 | 2024-06 | AVAILABLE | 11 | 1.4722 | 3.3675 |
| BASELINE | I1 | 2024-07 | AVAILABLE | 8 | 1.2399 | 1.4393 |
| BASELINE | I1 | 2024-08 | AVAILABLE | 9 | 0.1328 | -6.0281 |
| BASELINE | I1 | 2024-09 | AVAILABLE | 8 | 3.0362 | 4.0559 |
| BASELINE | I1 | 2024-10 | AVAILABLE | 8 | 2.6318 | 4.9967 |
| BASELINE | I1 | 2024-11 | AVAILABLE | 12 | 3.6298 | 17.9083 |
| BASELINE | I1 | 2024-12 | AVAILABLE | 11 | 0.9267 | -0.6009 |
| BASELINE | I2 | 2023-01 | AVAILABLE | 3 | 0.2506 | -1.4989 |
| BASELINE | I2 | 2023-02 | AVAILABLE | 10 | 0.6597 | -3.4030 |
| BASELINE | I2 | 2023-03 | AVAILABLE | 8 | 0.0000 | -8.0000 |
| BASELINE | I2 | 2023-04 | AVAILABLE | 13 | 2.0348 | 10.3483 |
| BASELINE | I2 | 2023-05 | AVAILABLE | 15 | 0.2839 | -9.3092 |
| BASELINE | I2 | 2023-06 | AVAILABLE | 10 | 0.2426 | -7.4419 |
| BASELINE | I2 | 2023-07 | AVAILABLE | 8 | 2.5681 | 10.9765 |
| BASELINE | I2 | 2023-08 | AVAILABLE | 11 | 0.0000 | -15.1092 |
| BASELINE | I2 | 2023-09 | AVAILABLE | 6 | 6.7395 | 11.4791 |
| BASELINE | I2 | 2023-10 | AVAILABLE | 16 | 3.3150 | 25.4260 |
| BASELINE | I2 | 2023-11 | AVAILABLE | 11 | 7.7205 | 53.1945 |
| BASELINE | I2 | 2023-12 | AVAILABLE | 14 | 0.5948 | -4.8618 |
| BASELINE | I2 | 2024-01 | AVAILABLE | 16 | 0.5559 | -5.7733 |
| BASELINE | I2 | 2024-02 | AVAILABLE | 16 | 0.0439 | -13.3855 |
| BASELINE | I2 | 2024-03 | AVAILABLE | 15 | 0.0461 | -12.7596 |
| BASELINE | I2 | 2024-04 | AVAILABLE | 20 | 0.0711 | -17.6607 |
| BASELINE | I2 | 2024-05 | AVAILABLE | 16 | 0.4961 | -7.0471 |
| BASELINE | I2 | 2024-06 | AVAILABLE | 13 | 1.3287 | 3.1216 |
| BASELINE | I2 | 2024-07 | AVAILABLE | 9 | 0.0000 | -9.0000 |
| BASELINE | I2 | 2024-08 | AVAILABLE | 11 | 0.0994 | -9.0059 |
| BASELINE | I2 | 2024-09 | AVAILABLE | 12 | 0.1571 | -8.4163 |
| BASELINE | I2 | 2024-10 | AVAILABLE | 9 | 4.1900 | 15.7857 |
| BASELINE | I2 | 2024-11 | AVAILABLE | 17 | 2.6513 | 24.5720 |
| BASELINE | I2 | 2024-12 | AVAILABLE | 12 | 1.0676 | 0.7276 |
| BASELINE | I3 | 2023-01 | AVAILABLE | 3 | 0.1253 | -1.7494 |
| BASELINE | I3 | 2023-02 | AVAILABLE | 9 | 0.5552 | -3.0431 |
| BASELINE | I3 | 2023-03 | AVAILABLE | 7 | 0.1529 | -4.9406 |
| BASELINE | I3 | 2023-04 | AVAILABLE | 11 | 3.3748 | 16.6239 |
| BASELINE | I3 | 2023-05 | AVAILABLE | 10 | 0.5886 | -2.9207 |
| BASELINE | I3 | 2023-06 | AVAILABLE | 6 | 0.4847 | -2.5334 |
| BASELINE | I3 | 2023-07 | AVAILABLE | 6 | 7.1026 | 12.2052 |
| BASELINE | I3 | 2023-08 | AVAILABLE | 11 | 0.0000 | -11.9077 |
| BASELINE | I3 | 2023-09 | AVAILABLE | 8 | 2.1937 | 4.5316 |
| BASELINE | I3 | 2023-10 | AVAILABLE | 11 | 5.2339 | 16.3887 |
| BASELINE | I3 | 2023-11 | AVAILABLE | 10 | 3.0469 | 10.7529 |
| BASELINE | I3 | 2023-12 | AVAILABLE | 10 | 1.5699 | 3.3445 |
| BASELINE | I3 | 2024-01 | AVAILABLE | 10 | 1.8699 | 3.4797 |
| BASELINE | I3 | 2024-02 | AVAILABLE | 14 | 0.1788 | -9.2475 |
| BASELINE | I3 | 2024-03 | AVAILABLE | 12 | 0.1339 | -8.8921 |
| BASELINE | I3 | 2024-04 | AVAILABLE | 10 | 1.5215 | 3.1846 |
| BASELINE | I3 | 2024-05 | AVAILABLE | 15 | 0.3687 | -7.3448 |
| BASELINE | I3 | 2024-06 | AVAILABLE | 11 | 1.4859 | 3.7809 |
| BASELINE | I3 | 2024-07 | AVAILABLE | 8 | 1.2399 | 1.4393 |
| BASELINE | I3 | 2024-08 | AVAILABLE | 9 | 0.1328 | -6.0281 |
| BASELINE | I3 | 2024-09 | AVAILABLE | 8 | 3.2956 | 4.5726 |
| BASELINE | I3 | 2024-10 | AVAILABLE | 8 | 2.3381 | 4.6226 |
| BASELINE | I3 | 2024-11 | AVAILABLE | 12 | 3.5256 | 17.7070 |
| BASELINE | I3 | 2024-12 | AVAILABLE | 11 | 0.8809 | -1.0277 |
| OPTIMIZED | CONTROL | 2023-01 | AVAILABLE | 2 | 0.2019 | -0.7737 |
| OPTIMIZED | CONTROL | 2023-02 | AVAILABLE | 6 | 1.9750 | 2.1791 |
| OPTIMIZED | CONTROL | 2023-03 | AVAILABLE | 7 | 0.0787 | -5.5275 |
| OPTIMIZED | CONTROL | 2023-04 | AVAILABLE | 7 | 10.4543 | 13.6362 |
| OPTIMIZED | CONTROL | 2023-05 | AVAILABLE | 9 | 0.6096 | -2.0606 |
| OPTIMIZED | CONTROL | 2023-06 | AVAILABLE | 5 | 0.4571 | -1.3898 |
| OPTIMIZED | CONTROL | 2023-07 | AVAILABLE | 4 | — | 9.2663 |
| OPTIMIZED | CONTROL | 2023-08 | AVAILABLE | 9 | 0.0120 | -5.4652 |
| OPTIMIZED | CONTROL | 2023-09 | AVAILABLE | 6 | 3.4995 | 4.0366 |
| OPTIMIZED | CONTROL | 2023-10 | AVAILABLE | 11 | 3.8162 | 8.6859 |
| OPTIMIZED | CONTROL | 2023-11 | AVAILABLE | 8 | 2.0714 | 3.3172 |
| OPTIMIZED | CONTROL | 2023-12 | AVAILABLE | 8 | 1.3923 | 1.6416 |
| OPTIMIZED | CONTROL | 2024-01 | AVAILABLE | 10 | 2.0376 | 2.6991 |
| OPTIMIZED | CONTROL | 2024-02 | AVAILABLE | 10 | 0.7798 | -1.2581 |
| OPTIMIZED | CONTROL | 2024-03 | AVAILABLE | 10 | 0.1218 | -5.3427 |
| OPTIMIZED | CONTROL | 2024-04 | AVAILABLE | 8 | 2.1161 | 4.5349 |
| OPTIMIZED | CONTROL | 2024-05 | AVAILABLE | 12 | 0.2954 | -5.1227 |
| OPTIMIZED | CONTROL | 2024-06 | AVAILABLE | 8 | 3.3222 | 10.9638 |
| OPTIMIZED | CONTROL | 2024-07 | AVAILABLE | 7 | 0.7759 | -0.8587 |
| OPTIMIZED | CONTROL | 2024-08 | AVAILABLE | 7 | 1.1819 | 0.7126 |
| OPTIMIZED | CONTROL | 2024-09 | AVAILABLE | 8 | 2.0889 | 2.5291 |
| OPTIMIZED | CONTROL | 2024-10 | AVAILABLE | 8 | 1.2489 | 0.8784 |
| OPTIMIZED | CONTROL | 2024-11 | AVAILABLE | 10 | 4.5384 | 11.8515 |
| OPTIMIZED | CONTROL | 2024-12 | AVAILABLE | 8 | 3.6412 | 8.9668 |
| OPTIMIZED | I1 | 2023-01 | AVAILABLE | 3 | 0.0000 | -2.1243 |
| OPTIMIZED | I1 | 2023-02 | AVAILABLE | 9 | 0.4780 | -3.6540 |
| OPTIMIZED | I1 | 2023-03 | AVAILABLE | 7 | 0.0993 | -5.4043 |
| OPTIMIZED | I1 | 2023-04 | AVAILABLE | 11 | 3.0073 | 14.2270 |
| OPTIMIZED | I1 | 2023-05 | AVAILABLE | 10 | 0.4537 | -4.0695 |
| OPTIMIZED | I1 | 2023-06 | AVAILABLE | 6 | 0.2629 | -3.5896 |
| OPTIMIZED | I1 | 2023-07 | AVAILABLE | 6 | 6.2108 | 10.4215 |
| OPTIMIZED | I1 | 2023-08 | AVAILABLE | 11 | 0.0000 | -12.9422 |
| OPTIMIZED | I1 | 2023-09 | AVAILABLE | 6 | 4.5636 | 6.6385 |
| OPTIMIZED | I1 | 2023-10 | AVAILABLE | 11 | 3.5664 | 12.3629 |
| OPTIMIZED | I1 | 2023-11 | AVAILABLE | 10 | 2.6274 | 8.8408 |
| OPTIMIZED | I1 | 2023-12 | AVAILABLE | 9 | 2.0918 | 5.9279 |
| OPTIMIZED | I1 | 2024-01 | AVAILABLE | 10 | 1.3208 | 1.3822 |
| OPTIMIZED | I1 | 2024-02 | AVAILABLE | 14 | 0.1451 | -9.8502 |
| OPTIMIZED | I1 | 2024-03 | AVAILABLE | 12 | 0.0915 | -9.3269 |
| OPTIMIZED | I1 | 2024-04 | AVAILABLE | 9 | 2.3150 | 7.2674 |
| OPTIMIZED | I1 | 2024-05 | AVAILABLE | 15 | 0.2880 | -8.3560 |
| OPTIMIZED | I1 | 2024-06 | AVAILABLE | 9 | 3.4825 | 15.2152 |
| OPTIMIZED | I1 | 2024-07 | AVAILABLE | 8 | 1.0494 | 0.2966 |
| OPTIMIZED | I1 | 2024-08 | AVAILABLE | 9 | 0.6348 | -2.6208 |
| OPTIMIZED | I1 | 2024-09 | AVAILABLE | 8 | 1.8456 | 2.4335 |
| OPTIMIZED | I1 | 2024-10 | AVAILABLE | 8 | 2.3801 | 4.5066 |
| OPTIMIZED | I1 | 2024-11 | AVAILABLE | 12 | 3.0210 | 15.1923 |
| OPTIMIZED | I1 | 2024-12 | AVAILABLE | 10 | 1.1114 | 0.8820 |
| OPTIMIZED | I2 | 2023-01 | AVAILABLE | 3 | 0.0000 | -2.2487 |
| OPTIMIZED | I2 | 2023-02 | AVAILABLE | 10 | 0.6030 | -3.9702 |
| OPTIMIZED | I2 | 2023-03 | AVAILABLE | 8 | 0.0000 | -8.0000 |
| OPTIMIZED | I2 | 2023-04 | AVAILABLE | 13 | 1.7584 | 7.6833 |
| OPTIMIZED | I2 | 2023-05 | AVAILABLE | 15 | 0.2347 | -9.9489 |
| OPTIMIZED | I2 | 2023-06 | AVAILABLE | 10 | 0.1281 | -8.7194 |
| OPTIMIZED | I2 | 2023-07 | AVAILABLE | 8 | 2.4128 | 9.8893 |
| OPTIMIZED | I2 | 2023-08 | AVAILABLE | 11 | 0.0000 | -15.4607 |
| OPTIMIZED | I2 | 2023-09 | AVAILABLE | 6 | 5.9711 | 10.3213 |
| OPTIMIZED | I2 | 2023-10 | AVAILABLE | 16 | 2.6750 | 18.7040 |
| OPTIMIZED | I2 | 2023-11 | AVAILABLE | 11 | 6.8296 | 46.8697 |
| OPTIMIZED | I2 | 2023-12 | AVAILABLE | 14 | 0.4684 | -6.3793 |
| OPTIMIZED | I2 | 2024-01 | AVAILABLE | 16 | 0.4111 | -7.6561 |
| OPTIMIZED | I2 | 2024-02 | AVAILABLE | 16 | 0.0224 | -13.7927 |
| OPTIMIZED | I2 | 2024-03 | AVAILABLE | 15 | 0.0326 | -13.2035 |
| OPTIMIZED | I2 | 2024-04 | AVAILABLE | 20 | 0.0751 | -18.0719 |
| OPTIMIZED | I2 | 2024-05 | AVAILABLE | 16 | 0.3839 | -8.6257 |
| OPTIMIZED | I2 | 2024-06 | AVAILABLE | 12 | 1.9877 | 9.0254 |
| OPTIMIZED | I2 | 2024-07 | AVAILABLE | 9 | 0.0000 | -9.0000 |
| OPTIMIZED | I2 | 2024-08 | AVAILABLE | 11 | 0.6263 | -3.7373 |
| OPTIMIZED | I2 | 2024-09 | AVAILABLE | 12 | 0.1347 | -9.2626 |
| OPTIMIZED | I2 | 2024-10 | AVAILABLE | 9 | 3.6116 | 13.0578 |
| OPTIMIZED | I2 | 2024-11 | AVAILABLE | 17 | 2.1806 | 19.4028 |
| OPTIMIZED | I2 | 2024-12 | AVAILABLE | 11 | 1.4280 | 3.9943 |
| OPTIMIZED | I3 | 2023-01 | AVAILABLE | 3 | 0.0000 | -2.1243 |
| OPTIMIZED | I3 | 2023-02 | AVAILABLE | 9 | 0.4780 | -3.6540 |
| OPTIMIZED | I3 | 2023-03 | AVAILABLE | 7 | 0.0993 | -5.4043 |
| OPTIMIZED | I3 | 2023-04 | AVAILABLE | 11 | 3.0073 | 14.2270 |
| OPTIMIZED | I3 | 2023-05 | AVAILABLE | 10 | 0.4940 | -3.7692 |
| OPTIMIZED | I3 | 2023-06 | AVAILABLE | 6 | 0.2561 | -3.7194 |
| OPTIMIZED | I3 | 2023-07 | AVAILABLE | 6 | 6.2283 | 10.4566 |
| OPTIMIZED | I3 | 2023-08 | AVAILABLE | 11 | 0.0000 | -12.9422 |
| OPTIMIZED | I3 | 2023-09 | AVAILABLE | 8 | 1.9519 | 3.6769 |
| OPTIMIZED | I3 | 2023-10 | AVAILABLE | 11 | 3.6897 | 12.9568 |
| OPTIMIZED | I3 | 2023-11 | AVAILABLE | 10 | 2.5979 | 8.7790 |
| OPTIMIZED | I3 | 2023-12 | AVAILABLE | 9 | 2.1089 | 6.0420 |
| OPTIMIZED | I3 | 2024-01 | AVAILABLE | 10 | 1.3493 | 1.5051 |
| OPTIMIZED | I3 | 2024-02 | AVAILABLE | 14 | 0.1434 | -9.9850 |
| OPTIMIZED | I3 | 2024-03 | AVAILABLE | 12 | 0.0915 | -9.3269 |
| OPTIMIZED | I3 | 2024-04 | AVAILABLE | 9 | 2.3834 | 7.7973 |
| OPTIMIZED | I3 | 2024-05 | AVAILABLE | 15 | 0.3025 | -8.2098 |
| OPTIMIZED | I3 | 2024-06 | AVAILABLE | 9 | 3.4090 | 15.0831 |
| OPTIMIZED | I3 | 2024-07 | AVAILABLE | 8 | 1.0494 | 0.2966 |
| OPTIMIZED | I3 | 2024-08 | AVAILABLE | 9 | 0.6348 | -2.6208 |
| OPTIMIZED | I3 | 2024-09 | AVAILABLE | 8 | 2.0107 | 2.9087 |
| OPTIMIZED | I3 | 2024-10 | AVAILABLE | 8 | 2.1641 | 4.1846 |
| OPTIMIZED | I3 | 2024-11 | AVAILABLE | 12 | 2.8814 | 14.8282 |
| OPTIMIZED | I3 | 2024-12 | AVAILABLE | 10 | 1.1114 | 0.8820 |

### GLDRUBF / ACTUAL_INITIAL_RISK

| version | rule | month | coverage | closed_trades | gross_PF | gross_R |
| --- | --- | --- | --- | --- | --- | --- |
| BASELINE | CONTROL | 2023-01 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | CONTROL | 2023-02 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | CONTROL | 2023-03 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | CONTROL | 2023-04 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | CONTROL | 2023-05 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | CONTROL | 2023-06 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | CONTROL | 2023-07 | AVAILABLE | 4 | 0.0601 | -1.8481 |
| BASELINE | CONTROL | 2023-08 | AVAILABLE | 13 | 0.2840 | -4.3327 |
| BASELINE | CONTROL | 2023-09 | AVAILABLE | 7 | 0.5685 | -2.1424 |
| BASELINE | CONTROL | 2023-10 | AVAILABLE | 8 | 0.5405 | -0.8279 |
| BASELINE | CONTROL | 2023-11 | AVAILABLE | 7 | 1.8131 | 2.6422 |
| BASELINE | CONTROL | 2023-12 | AVAILABLE | 12 | 2.2378 | 6.4063 |
| BASELINE | CONTROL | 2024-01 | AVAILABLE | 6 | 0.5475 | -1.2940 |
| BASELINE | CONTROL | 2024-02 | AVAILABLE | 11 | 0.4072 | -3.5200 |
| BASELINE | CONTROL | 2024-03 | AVAILABLE | 13 | 2.0035 | 5.5150 |
| BASELINE | CONTROL | 2024-04 | AVAILABLE | 12 | 2.3743 | 6.4031 |
| BASELINE | CONTROL | 2024-05 | AVAILABLE | 7 | 1.5261 | 1.2444 |
| BASELINE | CONTROL | 2024-06 | AVAILABLE | 12 | 0.0999 | -6.4588 |
| BASELINE | CONTROL | 2024-07 | AVAILABLE | 10 | 2.0945 | 3.4535 |
| BASELINE | CONTROL | 2024-08 | AVAILABLE | 13 | 1.1819 | 1.1723 |
| BASELINE | CONTROL | 2024-09 | AVAILABLE | 7 | 0.0000 | -3.9822 |
| BASELINE | CONTROL | 2024-10 | AVAILABLE | 12 | 1.1558 | 0.7828 |
| BASELINE | CONTROL | 2024-11 | AVAILABLE | 11 | 4.7138 | 13.1694 |
| BASELINE | CONTROL | 2024-12 | AVAILABLE | 13 | 0.2242 | -5.2146 |
| BASELINE | I1 | 2023-01 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | I1 | 2023-02 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | I1 | 2023-03 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | I1 | 2023-04 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | I1 | 2023-05 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | I1 | 2023-06 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | I1 | 2023-07 | AVAILABLE | 5 | 0.0619 | -3.2749 |
| BASELINE | I1 | 2023-08 | AVAILABLE | 13 | 0.3966 | -4.9220 |
| BASELINE | I1 | 2023-09 | AVAILABLE | 6 | 0.8387 | -0.7596 |
| BASELINE | I1 | 2023-10 | AVAILABLE | 11 | 0.1886 | -5.8547 |
| BASELINE | I1 | 2023-11 | AVAILABLE | 7 | 4.7315 | 11.1890 |
| BASELINE | I1 | 2023-12 | AVAILABLE | 14 | 1.4844 | 4.2145 |
| BASELINE | I1 | 2024-01 | AVAILABLE | 6 | 0.5854 | -1.4534 |
| BASELINE | I1 | 2024-02 | AVAILABLE | 15 | 0.0131 | -17.9506 |
| BASELINE | I1 | 2024-03 | AVAILABLE | 15 | 1.0541 | 0.4082 |
| BASELINE | I1 | 2024-04 | AVAILABLE | 14 | 1.2870 | 2.1988 |
| BASELINE | I1 | 2024-05 | AVAILABLE | 7 | 2.1810 | 6.1049 |
| BASELINE | I1 | 2024-06 | AVAILABLE | 12 | 0.0558 | -7.3855 |
| BASELINE | I1 | 2024-07 | AVAILABLE | 13 | 0.8083 | -1.4303 |
| BASELINE | I1 | 2024-08 | AVAILABLE | 13 | 2.3195 | 8.5569 |
| BASELINE | I1 | 2024-09 | AVAILABLE | 9 | 0.0000 | -7.8594 |
| BASELINE | I1 | 2024-10 | AVAILABLE | 13 | 0.7619 | -2.2278 |
| BASELINE | I1 | 2024-11 | AVAILABLE | 12 | 4.0240 | 20.3212 |
| BASELINE | I1 | 2024-12 | AVAILABLE | 16 | 0.2837 | -9.5957 |
| BASELINE | I2 | 2023-01 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | I2 | 2023-02 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | I2 | 2023-03 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | I2 | 2023-04 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | I2 | 2023-05 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | I2 | 2023-06 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | I2 | 2023-07 | AVAILABLE | 9 | 0.0000 | -15.2185 |
| BASELINE | I2 | 2023-08 | AVAILABLE | 16 | 0.1165 | -16.9182 |
| BASELINE | I2 | 2023-09 | AVAILABLE | 7 | 0.6415 | -2.6198 |
| BASELINE | I2 | 2023-10 | AVAILABLE | 19 | 0.0389 | -43.5107 |
| BASELINE | I2 | 2023-11 | AVAILABLE | 8 | 1.8763 | 5.2669 |
| BASELINE | I2 | 2023-12 | AVAILABLE | 19 | 1.3506 | 7.5871 |
| BASELINE | I2 | 2024-01 | AVAILABLE | 6 | 0.6322 | -1.5453 |
| BASELINE | I2 | 2024-02 | AVAILABLE | 15 | 0.1507 | -22.6234 |
| BASELINE | I2 | 2024-03 | AVAILABLE | 21 | 0.4223 | -8.5005 |
| BASELINE | I2 | 2024-04 | AVAILABLE | 21 | 1.0516 | 1.8611 |
| BASELINE | I2 | 2024-05 | AVAILABLE | 9 | 9.8194 | 56.3389 |
| BASELINE | I2 | 2024-06 | AVAILABLE | 12 | 0.1735 | -7.1179 |
| BASELINE | I2 | 2024-07 | AVAILABLE | 19 | 0.6877 | -5.3113 |
| BASELINE | I2 | 2024-08 | AVAILABLE | 15 | 2.7688 | 17.8355 |
| BASELINE | I2 | 2024-09 | AVAILABLE | 9 | 0.0000 | -9.0000 |
| BASELINE | I2 | 2024-10 | AVAILABLE | 21 | 1.3167 | 6.0166 |
| BASELINE | I2 | 2024-11 | AVAILABLE | 19 | 5.4852 | 99.9464 |
| BASELINE | I2 | 2024-12 | AVAILABLE | 20 | 1.2223 | 3.7967 |
| BASELINE | I3 | 2023-01 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | I3 | 2023-02 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | I3 | 2023-03 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | I3 | 2023-04 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | I3 | 2023-05 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | I3 | 2023-06 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | I3 | 2023-07 | AVAILABLE | 5 | 0.0591 | -3.4438 |
| BASELINE | I3 | 2023-08 | AVAILABLE | 13 | 0.3932 | -4.9936 |
| BASELINE | I3 | 2023-09 | AVAILABLE | 6 | 0.7828 | -1.0956 |
| BASELINE | I3 | 2023-10 | AVAILABLE | 11 | 0.1886 | -5.8547 |
| BASELINE | I3 | 2023-11 | AVAILABLE | 7 | 4.2904 | 10.8900 |
| BASELINE | I3 | 2023-12 | AVAILABLE | 14 | 1.5174 | 4.5392 |
| BASELINE | I3 | 2024-01 | AVAILABLE | 6 | 0.5827 | -1.4699 |
| BASELINE | I3 | 2024-02 | AVAILABLE | 15 | 0.0180 | -18.3073 |
| BASELINE | I3 | 2024-03 | AVAILABLE | 17 | 0.7126 | -3.1733 |
| BASELINE | I3 | 2024-04 | AVAILABLE | 14 | 1.3977 | 3.0471 |
| BASELINE | I3 | 2024-05 | AVAILABLE | 7 | 2.1810 | 6.1049 |
| BASELINE | I3 | 2024-06 | AVAILABLE | 12 | 0.0888 | -7.3591 |
| BASELINE | I3 | 2024-07 | AVAILABLE | 13 | 0.8066 | -1.4458 |
| BASELINE | I3 | 2024-08 | AVAILABLE | 13 | 2.3211 | 8.5668 |
| BASELINE | I3 | 2024-09 | AVAILABLE | 9 | 0.0000 | -7.8594 |
| BASELINE | I3 | 2024-10 | AVAILABLE | 13 | 0.7684 | -2.1674 |
| BASELINE | I3 | 2024-11 | AVAILABLE | 12 | 4.1376 | 21.0840 |
| BASELINE | I3 | 2024-12 | AVAILABLE | 16 | 0.2826 | -9.6479 |
| OPTIMIZED | CONTROL | 2023-01 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | CONTROL | 2023-02 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | CONTROL | 2023-03 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | CONTROL | 2023-04 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | CONTROL | 2023-05 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | CONTROL | 2023-06 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | CONTROL | 2023-07 | AVAILABLE | 3 | 0.0000 | -2.3362 |
| OPTIMIZED | CONTROL | 2023-08 | AVAILABLE | 14 | 0.2813 | -5.2065 |
| OPTIMIZED | CONTROL | 2023-09 | AVAILABLE | 6 | 1.0990 | 0.4781 |
| OPTIMIZED | CONTROL | 2023-10 | AVAILABLE | 8 | 0.1734 | -2.0774 |
| OPTIMIZED | CONTROL | 2023-11 | AVAILABLE | 7 | 1.4524 | 1.7044 |
| OPTIMIZED | CONTROL | 2023-12 | AVAILABLE | 11 | 2.5168 | 8.1967 |
| OPTIMIZED | CONTROL | 2024-01 | AVAILABLE | 6 | 0.5654 | -1.4163 |
| OPTIMIZED | CONTROL | 2024-02 | AVAILABLE | 10 | 0.3876 | -3.4272 |
| OPTIMIZED | CONTROL | 2024-03 | AVAILABLE | 13 | 1.9345 | 5.2989 |
| OPTIMIZED | CONTROL | 2024-04 | AVAILABLE | 12 | 1.8007 | 4.4069 |
| OPTIMIZED | CONTROL | 2024-05 | AVAILABLE | 7 | 1.1614 | 0.4489 |
| OPTIMIZED | CONTROL | 2024-06 | AVAILABLE | 12 | 0.3308 | -4.9243 |
| OPTIMIZED | CONTROL | 2024-07 | AVAILABLE | 10 | 1.7385 | 2.5091 |
| OPTIMIZED | CONTROL | 2024-08 | AVAILABLE | 11 | 1.3796 | 1.8695 |
| OPTIMIZED | CONTROL | 2024-09 | AVAILABLE | 6 | 0.1937 | -2.8897 |
| OPTIMIZED | CONTROL | 2024-10 | AVAILABLE | 12 | 0.8216 | -1.0763 |
| OPTIMIZED | CONTROL | 2024-11 | AVAILABLE | 7 | 42.2009 | 22.4126 |
| OPTIMIZED | CONTROL | 2024-12 | AVAILABLE | 11 | 0.6533 | -2.6554 |
| OPTIMIZED | I1 | 2023-01 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | I1 | 2023-02 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | I1 | 2023-03 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | I1 | 2023-04 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | I1 | 2023-05 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | I1 | 2023-06 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | I1 | 2023-07 | AVAILABLE | 4 | 0.0000 | -3.6104 |
| OPTIMIZED | I1 | 2023-08 | AVAILABLE | 14 | 0.4607 | -4.9626 |
| OPTIMIZED | I1 | 2023-09 | AVAILABLE | 6 | 1.5243 | 2.5520 |
| OPTIMIZED | I1 | 2023-10 | AVAILABLE | 11 | 0.0332 | -7.8009 |
| OPTIMIZED | I1 | 2023-11 | AVAILABLE | 7 | 4.0432 | 10.0260 |
| OPTIMIZED | I1 | 2023-12 | AVAILABLE | 13 | 2.3908 | 11.3676 |
| OPTIMIZED | I1 | 2024-01 | AVAILABLE | 6 | 0.5528 | -1.7049 |
| OPTIMIZED | I1 | 2024-02 | AVAILABLE | 14 | 0.0046 | -17.1431 |
| OPTIMIZED | I1 | 2024-03 | AVAILABLE | 15 | 0.9283 | -0.5693 |
| OPTIMIZED | I1 | 2024-04 | AVAILABLE | 14 | 0.8664 | -1.2028 |
| OPTIMIZED | I1 | 2024-05 | AVAILABLE | 7 | 1.7224 | 4.1773 |
| OPTIMIZED | I1 | 2024-06 | AVAILABLE | 12 | 0.1937 | -6.5493 |
| OPTIMIZED | I1 | 2024-07 | AVAILABLE | 13 | 0.6514 | -2.8937 |
| OPTIMIZED | I1 | 2024-08 | AVAILABLE | 11 | 2.6226 | 8.0816 |
| OPTIMIZED | I1 | 2024-09 | AVAILABLE | 8 | 0.1203 | -5.4593 |
| OPTIMIZED | I1 | 2024-10 | AVAILABLE | 13 | 0.6187 | -3.8127 |
| OPTIMIZED | I1 | 2024-11 | AVAILABLE | 8 | 13.5777 | 40.9583 |
| OPTIMIZED | I1 | 2024-12 | AVAILABLE | 14 | 1.5926 | 7.7349 |
| OPTIMIZED | I2 | 2023-01 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | I2 | 2023-02 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | I2 | 2023-03 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | I2 | 2023-04 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | I2 | 2023-05 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | I2 | 2023-06 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | I2 | 2023-07 | AVAILABLE | 9 | 0.0000 | -15.2185 |
| OPTIMIZED | I2 | 2023-08 | AVAILABLE | 16 | 0.2007 | -15.3043 |
| OPTIMIZED | I2 | 2023-09 | AVAILABLE | 6 | 1.2254 | 1.6200 |
| OPTIMIZED | I2 | 2023-10 | AVAILABLE | 19 | 0.0103 | -44.8043 |
| OPTIMIZED | I2 | 2023-11 | AVAILABLE | 8 | 1.6749 | 4.1826 |
| OPTIMIZED | I2 | 2023-12 | AVAILABLE | 15 | 2.5196 | 25.0735 |
| OPTIMIZED | I2 | 2024-01 | AVAILABLE | 6 | 0.5979 | -1.8096 |
| OPTIMIZED | I2 | 2024-02 | AVAILABLE | 15 | 0.1423 | -22.8648 |
| OPTIMIZED | I2 | 2024-03 | AVAILABLE | 21 | 0.3895 | -9.3857 |
| OPTIMIZED | I2 | 2024-04 | AVAILABLE | 21 | 0.5981 | -14.5062 |
| OPTIMIZED | I2 | 2024-05 | AVAILABLE | 9 | 8.6580 | 52.3263 |
| OPTIMIZED | I2 | 2024-06 | AVAILABLE | 12 | 0.4378 | -4.8363 |
| OPTIMIZED | I2 | 2024-07 | AVAILABLE | 19 | 0.6268 | -6.5512 |
| OPTIMIZED | I2 | 2024-08 | AVAILABLE | 13 | 2.9128 | 16.9378 |
| OPTIMIZED | I2 | 2024-09 | AVAILABLE | 9 | 0.0000 | -9.0000 |
| OPTIMIZED | I2 | 2024-10 | AVAILABLE | 21 | 0.9836 | -0.3276 |
| OPTIMIZED | I2 | 2024-11 | AVAILABLE | 14 | 9.6785 | 86.7854 |
| OPTIMIZED | I2 | 2024-12 | AVAILABLE | 19 | 1.9439 | 16.6853 |
| OPTIMIZED | I3 | 2023-01 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | I3 | 2023-02 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | I3 | 2023-03 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | I3 | 2023-04 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | I3 | 2023-05 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | I3 | 2023-06 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | I3 | 2023-07 | AVAILABLE | 4 | 0.0000 | -3.8204 |
| OPTIMIZED | I3 | 2023-08 | AVAILABLE | 14 | 0.4555 | -5.0665 |
| OPTIMIZED | I3 | 2023-09 | AVAILABLE | 6 | 1.4427 | 2.2768 |
| OPTIMIZED | I3 | 2023-10 | AVAILABLE | 11 | 0.0332 | -7.8009 |
| OPTIMIZED | I3 | 2023-11 | AVAILABLE | 7 | 3.5388 | 9.5642 |
| OPTIMIZED | I3 | 2023-12 | AVAILABLE | 13 | 2.3982 | 11.5388 |
| OPTIMIZED | I3 | 2024-01 | AVAILABLE | 6 | 0.5924 | -1.5540 |
| OPTIMIZED | I3 | 2024-02 | AVAILABLE | 14 | 0.0064 | -17.4161 |
| OPTIMIZED | I3 | 2024-03 | AVAILABLE | 17 | 0.6442 | -4.0849 |
| OPTIMIZED | I3 | 2024-04 | AVAILABLE | 14 | 0.9543 | -0.4114 |
| OPTIMIZED | I3 | 2024-05 | AVAILABLE | 7 | 1.7224 | 4.1773 |
| OPTIMIZED | I3 | 2024-06 | AVAILABLE | 12 | 0.2927 | -5.8839 |
| OPTIMIZED | I3 | 2024-07 | AVAILABLE | 13 | 0.6482 | -2.9344 |
| OPTIMIZED | I3 | 2024-08 | AVAILABLE | 11 | 2.6156 | 8.0683 |
| OPTIMIZED | I3 | 2024-09 | AVAILABLE | 8 | 0.1203 | -5.4593 |
| OPTIMIZED | I3 | 2024-10 | AVAILABLE | 13 | 0.6236 | -3.7645 |
| OPTIMIZED | I3 | 2024-11 | AVAILABLE | 8 | 13.7871 | 41.6749 |
| OPTIMIZED | I3 | 2024-12 | AVAILABLE | 14 | 1.5926 | 7.7349 |

### IMOEXF / ACTUAL_INITIAL_RISK

| version | rule | month | coverage | closed_trades | gross_PF | gross_R |
| --- | --- | --- | --- | --- | --- | --- |
| BASELINE | CONTROL | 2023-01 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | CONTROL | 2023-02 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | CONTROL | 2023-03 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | CONTROL | 2023-04 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | CONTROL | 2023-05 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | CONTROL | 2023-06 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | CONTROL | 2023-07 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | CONTROL | 2023-08 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | CONTROL | 2023-09 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | CONTROL | 2023-10 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | CONTROL | 2023-11 | AVAILABLE | 1 | 0.0000 | -1.0000 |
| BASELINE | CONTROL | 2023-12 | AVAILABLE | 8 | 1.5182 | 1.2796 |
| BASELINE | CONTROL | 2024-01 | AVAILABLE | 10 | 0.5194 | -3.1777 |
| BASELINE | CONTROL | 2024-02 | AVAILABLE | 9 | 3.3744 | 5.8495 |
| BASELINE | CONTROL | 2024-03 | AVAILABLE | 8 | 1.1172 | 0.4058 |
| BASELINE | CONTROL | 2024-04 | AVAILABLE | 17 | 0.3819 | -5.1320 |
| BASELINE | CONTROL | 2024-05 | AVAILABLE | 12 | 1.1105 | 0.4020 |
| BASELINE | CONTROL | 2024-06 | AVAILABLE | 11 | 1.2127 | 0.8574 |
| BASELINE | CONTROL | 2024-07 | AVAILABLE | 11 | 1.7772 | 4.1880 |
| BASELINE | CONTROL | 2024-08 | AVAILABLE | 12 | 0.6756 | -1.9614 |
| BASELINE | CONTROL | 2024-09 | AVAILABLE | 11 | 1.4746 | 1.9699 |
| BASELINE | CONTROL | 2024-10 | AVAILABLE | 9 | 0.8283 | -0.7367 |
| BASELINE | CONTROL | 2024-11 | AVAILABLE | 11 | 3.3848 | 11.6619 |
| BASELINE | CONTROL | 2024-12 | AVAILABLE | 8 | 2.6485 | 4.8470 |
| BASELINE | I1 | 2023-01 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | I1 | 2023-02 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | I1 | 2023-03 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | I1 | 2023-04 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | I1 | 2023-05 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | I1 | 2023-06 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | I1 | 2023-07 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | I1 | 2023-08 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | I1 | 2023-09 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | I1 | 2023-10 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | I1 | 2023-11 | AVAILABLE | 1 | 0.0000 | -1.0000 |
| BASELINE | I1 | 2023-12 | AVAILABLE | 10 | 0.6923 | -1.7655 |
| BASELINE | I1 | 2024-01 | AVAILABLE | 11 | 2.2749 | 11.2957 |
| BASELINE | I1 | 2024-02 | AVAILABLE | 12 | 1.7590 | 6.1300 |
| BASELINE | I1 | 2024-03 | AVAILABLE | 11 | 0.7255 | -2.1672 |
| BASELINE | I1 | 2024-04 | AVAILABLE | 18 | 1.0217 | 0.2693 |
| BASELINE | I1 | 2024-05 | AVAILABLE | 20 | 0.2365 | -10.9216 |
| BASELINE | I1 | 2024-06 | AVAILABLE | 15 | 0.5682 | -4.6750 |
| BASELINE | I1 | 2024-07 | AVAILABLE | 11 | 2.3422 | 6.5164 |
| BASELINE | I1 | 2024-08 | AVAILABLE | 18 | 0.3855 | -8.6345 |
| BASELINE | I1 | 2024-09 | AVAILABLE | 12 | 1.4432 | 2.9077 |
| BASELINE | I1 | 2024-10 | AVAILABLE | 10 | 0.8432 | -1.0991 |
| BASELINE | I1 | 2024-11 | AVAILABLE | 13 | 1.9176 | 8.0082 |
| BASELINE | I1 | 2024-12 | AVAILABLE | 9 | 4.7711 | 19.1535 |
| BASELINE | I2 | 2023-01 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | I2 | 2023-02 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | I2 | 2023-03 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | I2 | 2023-04 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | I2 | 2023-05 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | I2 | 2023-06 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | I2 | 2023-07 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | I2 | 2023-08 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | I2 | 2023-09 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | I2 | 2023-10 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | I2 | 2023-11 | AVAILABLE | 1 | 0.0000 | -1.0000 |
| BASELINE | I2 | 2023-12 | AVAILABLE | 11 | 0.9102 | -0.7200 |
| BASELINE | I2 | 2024-01 | AVAILABLE | 12 | 1.8002 | 8.8021 |
| BASELINE | I2 | 2024-02 | AVAILABLE | 14 | 2.0312 | 11.3430 |
| BASELINE | I2 | 2024-03 | AVAILABLE | 14 | 0.2256 | -12.7771 |
| BASELINE | I2 | 2024-04 | AVAILABLE | 20 | 0.9737 | -0.4333 |
| BASELINE | I2 | 2024-05 | AVAILABLE | 24 | 0.8757 | -2.7936 |
| BASELINE | I2 | 2024-06 | AVAILABLE | 18 | 0.7315 | -5.9055 |
| BASELINE | I2 | 2024-07 | AVAILABLE | 17 | 1.0280 | 0.4203 |
| BASELINE | I2 | 2024-08 | AVAILABLE | 23 | 0.7961 | -6.4601 |
| BASELINE | I2 | 2024-09 | AVAILABLE | 17 | 1.2588 | 5.6931 |
| BASELINE | I2 | 2024-10 | AVAILABLE | 15 | 0.4341 | -7.9225 |
| BASELINE | I2 | 2024-11 | AVAILABLE | 15 | 2.2031 | 14.4785 |
| BASELINE | I2 | 2024-12 | AVAILABLE | 17 | 7.9187 | 99.0889 |
| BASELINE | I3 | 2023-01 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | I3 | 2023-02 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | I3 | 2023-03 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | I3 | 2023-04 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | I3 | 2023-05 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | I3 | 2023-06 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | I3 | 2023-07 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | I3 | 2023-08 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | I3 | 2023-09 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | I3 | 2023-10 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | I3 | 2023-11 | AVAILABLE | 1 | 0.0000 | -1.0000 |
| BASELINE | I3 | 2023-12 | AVAILABLE | 10 | 0.6923 | -1.7657 |
| BASELINE | I3 | 2024-01 | AVAILABLE | 11 | 2.2395 | 11.1559 |
| BASELINE | I3 | 2024-02 | AVAILABLE | 12 | 1.7590 | 6.1300 |
| BASELINE | I3 | 2024-03 | AVAILABLE | 11 | 0.7255 | -2.1672 |
| BASELINE | I3 | 2024-04 | AVAILABLE | 18 | 1.0217 | 0.2693 |
| BASELINE | I3 | 2024-05 | AVAILABLE | 20 | 0.2499 | -10.7297 |
| BASELINE | I3 | 2024-06 | AVAILABLE | 15 | 0.5486 | -5.0630 |
| BASELINE | I3 | 2024-07 | AVAILABLE | 12 | 1.7612 | 5.0259 |
| BASELINE | I3 | 2024-08 | AVAILABLE | 18 | 0.3855 | -8.6345 |
| BASELINE | I3 | 2024-09 | AVAILABLE | 12 | 1.4432 | 2.9077 |
| BASELINE | I3 | 2024-10 | AVAILABLE | 10 | 0.8431 | -1.1007 |
| BASELINE | I3 | 2024-11 | AVAILABLE | 13 | 1.9176 | 8.0082 |
| BASELINE | I3 | 2024-12 | AVAILABLE | 9 | 5.2309 | 21.4887 |
| OPTIMIZED | CONTROL | 2023-01 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | CONTROL | 2023-02 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | CONTROL | 2023-03 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | CONTROL | 2023-04 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | CONTROL | 2023-05 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | CONTROL | 2023-06 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | CONTROL | 2023-07 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | CONTROL | 2023-08 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | CONTROL | 2023-09 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | CONTROL | 2023-10 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | CONTROL | 2023-11 | AVAILABLE | 1 | 0.0000 | -1.0000 |
| OPTIMIZED | CONTROL | 2023-12 | AVAILABLE | 8 | 1.2309 | 0.6560 |
| OPTIMIZED | CONTROL | 2024-01 | AVAILABLE | 10 | 0.8173 | -1.2496 |
| OPTIMIZED | CONTROL | 2024-02 | AVAILABLE | 9 | 2.8741 | 5.4850 |
| OPTIMIZED | CONTROL | 2024-03 | AVAILABLE | 7 | 2.1966 | 4.4889 |
| OPTIMIZED | CONTROL | 2024-04 | AVAILABLE | 17 | 0.3330 | -5.7034 |
| OPTIMIZED | CONTROL | 2024-05 | AVAILABLE | 11 | 1.9051 | 3.3915 |
| OPTIMIZED | CONTROL | 2024-06 | AVAILABLE | 11 | 0.8721 | -0.5830 |
| OPTIMIZED | CONTROL | 2024-07 | AVAILABLE | 10 | 2.2218 | 5.5067 |
| OPTIMIZED | CONTROL | 2024-08 | AVAILABLE | 12 | 0.5630 | -2.7524 |
| OPTIMIZED | CONTROL | 2024-09 | AVAILABLE | 10 | 1.5487 | 2.5377 |
| OPTIMIZED | CONTROL | 2024-10 | AVAILABLE | 9 | 0.7172 | -1.2517 |
| OPTIMIZED | CONTROL | 2024-11 | AVAILABLE | 11 | 3.0106 | 10.0324 |
| OPTIMIZED | CONTROL | 2024-12 | AVAILABLE | 8 | 2.1354 | 3.9261 |
| OPTIMIZED | I1 | 2023-01 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | I1 | 2023-02 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | I1 | 2023-03 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | I1 | 2023-04 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | I1 | 2023-05 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | I1 | 2023-06 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | I1 | 2023-07 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | I1 | 2023-08 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | I1 | 2023-09 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | I1 | 2023-10 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | I1 | 2023-11 | AVAILABLE | 1 | 0.0000 | -1.0000 |
| OPTIMIZED | I1 | 2023-12 | AVAILABLE | 10 | 0.6025 | -2.3687 |
| OPTIMIZED | I1 | 2024-01 | AVAILABLE | 11 | 2.2451 | 11.2062 |
| OPTIMIZED | I1 | 2024-02 | AVAILABLE | 12 | 1.7219 | 5.9928 |
| OPTIMIZED | I1 | 2024-03 | AVAILABLE | 10 | 1.7825 | 5.6774 |
| OPTIMIZED | I1 | 2024-04 | AVAILABLE | 18 | 0.9576 | -0.5272 |
| OPTIMIZED | I1 | 2024-05 | AVAILABLE | 20 | 0.2733 | -10.7840 |
| OPTIMIZED | I1 | 2024-06 | AVAILABLE | 15 | 0.4570 | -6.0345 |
| OPTIMIZED | I1 | 2024-07 | AVAILABLE | 10 | 2.9624 | 8.3269 |
| OPTIMIZED | I1 | 2024-08 | AVAILABLE | 18 | 0.2815 | -10.4499 |
| OPTIMIZED | I1 | 2024-09 | AVAILABLE | 10 | 2.3876 | 6.7523 |
| OPTIMIZED | I1 | 2024-10 | AVAILABLE | 10 | 0.7835 | -1.5241 |
| OPTIMIZED | I1 | 2024-11 | AVAILABLE | 13 | 1.7060 | 6.1708 |
| OPTIMIZED | I1 | 2024-12 | AVAILABLE | 9 | 4.2664 | 17.5675 |
| OPTIMIZED | I2 | 2023-01 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | I2 | 2023-02 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | I2 | 2023-03 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | I2 | 2023-04 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | I2 | 2023-05 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | I2 | 2023-06 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | I2 | 2023-07 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | I2 | 2023-08 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | I2 | 2023-09 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | I2 | 2023-10 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | I2 | 2023-11 | AVAILABLE | 1 | 0.0000 | -1.0000 |
| OPTIMIZED | I2 | 2023-12 | AVAILABLE | 11 | 0.7039 | -2.3691 |
| OPTIMIZED | I2 | 2024-01 | AVAILABLE | 12 | 1.8079 | 8.8865 |
| OPTIMIZED | I2 | 2024-02 | AVAILABLE | 14 | 1.8063 | 9.3545 |
| OPTIMIZED | I2 | 2024-03 | AVAILABLE | 11 | 0.8181 | -2.4562 |
| OPTIMIZED | I2 | 2024-04 | AVAILABLE | 20 | 0.7947 | -3.3874 |
| OPTIMIZED | I2 | 2024-05 | AVAILABLE | 24 | 1.0858 | 1.9627 |
| OPTIMIZED | I2 | 2024-06 | AVAILABLE | 18 | 0.6223 | -8.3094 |
| OPTIMIZED | I2 | 2024-07 | AVAILABLE | 16 | 1.3481 | 4.5247 |
| OPTIMIZED | I2 | 2024-08 | AVAILABLE | 23 | 0.7095 | -9.3853 |
| OPTIMIZED | I2 | 2024-09 | AVAILABLE | 15 | 2.7848 | 23.2025 |
| OPTIMIZED | I2 | 2024-10 | AVAILABLE | 15 | 0.3925 | -8.5048 |
| OPTIMIZED | I2 | 2024-11 | AVAILABLE | 15 | 1.9289 | 11.2869 |
| OPTIMIZED | I2 | 2024-12 | AVAILABLE | 17 | 7.1809 | 92.7129 |
| OPTIMIZED | I3 | 2023-01 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | I3 | 2023-02 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | I3 | 2023-03 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | I3 | 2023-04 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | I3 | 2023-05 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | I3 | 2023-06 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | I3 | 2023-07 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | I3 | 2023-08 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | I3 | 2023-09 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | I3 | 2023-10 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | I3 | 2023-11 | AVAILABLE | 1 | 0.0000 | -1.0000 |
| OPTIMIZED | I3 | 2023-12 | AVAILABLE | 10 | 0.6033 | -2.3638 |
| OPTIMIZED | I3 | 2024-01 | AVAILABLE | 11 | 2.2451 | 11.2062 |
| OPTIMIZED | I3 | 2024-02 | AVAILABLE | 12 | 1.7219 | 5.9928 |
| OPTIMIZED | I3 | 2024-03 | AVAILABLE | 10 | 1.7825 | 5.6774 |
| OPTIMIZED | I3 | 2024-04 | AVAILABLE | 18 | 0.9576 | -0.5272 |
| OPTIMIZED | I3 | 2024-05 | AVAILABLE | 20 | 0.2818 | -10.6578 |
| OPTIMIZED | I3 | 2024-06 | AVAILABLE | 15 | 0.4458 | -6.3128 |
| OPTIMIZED | I3 | 2024-07 | AVAILABLE | 11 | 2.2040 | 6.9670 |
| OPTIMIZED | I3 | 2024-08 | AVAILABLE | 18 | 0.2815 | -10.4499 |
| OPTIMIZED | I3 | 2024-09 | AVAILABLE | 10 | 2.3876 | 6.7523 |
| OPTIMIZED | I3 | 2024-10 | AVAILABLE | 10 | 0.7829 | -1.5292 |
| OPTIMIZED | I3 | 2024-11 | AVAILABLE | 13 | 1.7060 | 6.1708 |
| OPTIMIZED | I3 | 2024-12 | AVAILABLE | 9 | 4.6874 | 19.8318 |

### ALL_FOUR / REFERENCE_2ATR

| version | rule | month | coverage | closed_trades | gross_PF | gross_R |
| --- | --- | --- | --- | --- | --- | --- |
| BASELINE | CONTROL | 2023-01 | AVAILABLE | 7 | 2.3802 | 3.8099 |
| BASELINE | CONTROL | 2023-02 | AVAILABLE | 15 | 1.7799 | 4.1951 |
| BASELINE | CONTROL | 2023-03 | AVAILABLE | 13 | 0.2443 | -6.2022 |
| BASELINE | CONTROL | 2023-04 | AVAILABLE | 14 | 9.6212 | 29.3412 |
| BASELINE | CONTROL | 2023-05 | AVAILABLE | 20 | 0.6320 | -3.3071 |
| BASELINE | CONTROL | 2023-06 | AVAILABLE | 15 | 1.2821 | 2.0233 |
| BASELINE | CONTROL | 2023-07 | AVAILABLE | 18 | 3.9954 | 17.3426 |
| BASELINE | CONTROL | 2023-08 | AVAILABLE | 36 | 0.5059 | -8.4431 |
| BASELINE | CONTROL | 2023-09 | AVAILABLE | 19 | 1.6277 | 5.8414 |
| BASELINE | CONTROL | 2023-10 | AVAILABLE | 33 | 4.3118 | 21.5526 |
| BASELINE | CONTROL | 2023-11 | AVAILABLE | 28 | 1.7153 | 8.1545 |
| BASELINE | CONTROL | 2023-12 | AVAILABLE | 38 | 2.4903 | 19.8967 |
| BASELINE | CONTROL | 2024-01 | AVAILABLE | 32 | 1.3380 | 4.2609 |
| BASELINE | CONTROL | 2024-02 | AVAILABLE | 39 | 0.8221 | -3.2939 |
| BASELINE | CONTROL | 2024-03 | AVAILABLE | 38 | 0.9495 | -0.9280 |
| BASELINE | CONTROL | 2024-04 | AVAILABLE | 49 | 0.9695 | -0.6988 |
| BASELINE | CONTROL | 2024-05 | AVAILABLE | 42 | 0.9038 | -1.6710 |
| BASELINE | CONTROL | 2024-06 | AVAILABLE | 43 | 0.8411 | -3.4411 |
| BASELINE | CONTROL | 2024-07 | AVAILABLE | 36 | 1.1961 | 3.4609 |
| BASELINE | CONTROL | 2024-08 | AVAILABLE | 43 | 1.0295 | 0.6238 |
| BASELINE | CONTROL | 2024-09 | AVAILABLE | 36 | 1.2716 | 3.8486 |
| BASELINE | CONTROL | 2024-10 | AVAILABLE | 42 | 0.7956 | -4.2789 |
| BASELINE | CONTROL | 2024-11 | AVAILABLE | 44 | 5.0903 | 50.5287 |
| BASELINE | CONTROL | 2024-12 | AVAILABLE | 41 | 1.0858 | 1.7951 |
| BASELINE | I1 | 2023-01 | AVAILABLE | 8 | 1.8975 | 2.7464 |
| BASELINE | I1 | 2023-02 | AVAILABLE | 18 | 1.2884 | 2.1151 |
| BASELINE | I1 | 2023-03 | AVAILABLE | 13 | 0.3400 | -3.8923 |
| BASELINE | I1 | 2023-04 | AVAILABLE | 18 | 6.5942 | 26.3518 |
| BASELINE | I1 | 2023-05 | AVAILABLE | 21 | 0.7384 | -1.8046 |
| BASELINE | I1 | 2023-06 | AVAILABLE | 17 | 1.0008 | 0.0058 |
| BASELINE | I1 | 2023-07 | AVAILABLE | 22 | 2.4870 | 10.3529 |
| BASELINE | I1 | 2023-08 | AVAILABLE | 41 | 0.4166 | -10.1880 |
| BASELINE | I1 | 2023-09 | AVAILABLE | 20 | 2.1307 | 8.0148 |
| BASELINE | I1 | 2023-10 | AVAILABLE | 36 | 3.3001 | 18.6922 |
| BASELINE | I1 | 2023-11 | AVAILABLE | 30 | 1.7364 | 7.7411 |
| BASELINE | I1 | 2023-12 | AVAILABLE | 45 | 2.1146 | 15.5025 |
| BASELINE | I1 | 2024-01 | AVAILABLE | 33 | 1.3894 | 4.3080 |
| BASELINE | I1 | 2024-02 | AVAILABLE | 50 | 0.3496 | -15.7384 |
| BASELINE | I1 | 2024-03 | AVAILABLE | 47 | 0.6313 | -7.0425 |
| BASELINE | I1 | 2024-04 | AVAILABLE | 56 | 0.8113 | -4.2882 |
| BASELINE | I1 | 2024-05 | AVAILABLE | 54 | 0.6459 | -7.1465 |
| BASELINE | I1 | 2024-06 | AVAILABLE | 48 | 0.7085 | -6.3578 |
| BASELINE | I1 | 2024-07 | AVAILABLE | 41 | 1.3234 | 4.2549 |
| BASELINE | I1 | 2024-08 | AVAILABLE | 49 | 1.2293 | 3.6416 |
| BASELINE | I1 | 2024-09 | AVAILABLE | 40 | 1.4199 | 4.9885 |
| BASELINE | I1 | 2024-10 | AVAILABLE | 44 | 0.7991 | -3.9094 |
| BASELINE | I1 | 2024-11 | AVAILABLE | 50 | 3.2015 | 36.7401 |
| BASELINE | I1 | 2024-12 | AVAILABLE | 47 | 1.0031 | 0.0645 |
| BASELINE | I2 | 2023-01 | AVAILABLE | 9 | 2.0345 | 2.9061 |
| BASELINE | I2 | 2023-02 | AVAILABLE | 25 | 1.3041 | 1.8287 |
| BASELINE | I2 | 2023-03 | AVAILABLE | 14 | 0.3168 | -2.7987 |
| BASELINE | I2 | 2023-04 | AVAILABLE | 27 | 5.2373 | 20.8522 |
| BASELINE | I2 | 2023-05 | AVAILABLE | 27 | 0.4959 | -2.9863 |
| BASELINE | I2 | 2023-06 | AVAILABLE | 25 | 0.4281 | -4.8487 |
| BASELINE | I2 | 2023-07 | AVAILABLE | 29 | 1.6601 | 4.9363 |
| BASELINE | I2 | 2023-08 | AVAILABLE | 52 | 0.3390 | -9.5582 |
| BASELINE | I2 | 2023-09 | AVAILABLE | 23 | 2.5451 | 8.2672 |
| BASELINE | I2 | 2023-10 | AVAILABLE | 57 | 1.9927 | 8.7175 |
| BASELINE | I2 | 2023-11 | AVAILABLE | 32 | 2.4076 | 10.0492 |
| BASELINE | I2 | 2023-12 | AVAILABLE | 61 | 1.9338 | 9.6618 |
| BASELINE | I2 | 2024-01 | AVAILABLE | 43 | 1.3618 | 3.1872 |
| BASELINE | I2 | 2024-02 | AVAILABLE | 59 | 0.5023 | -8.2877 |
| BASELINE | I2 | 2024-03 | AVAILABLE | 60 | 0.4991 | -6.7395 |
| BASELINE | I2 | 2024-04 | AVAILABLE | 79 | 0.6038 | -7.4455 |
| BASELINE | I2 | 2024-05 | AVAILABLE | 66 | 0.6519 | -5.5784 |
| BASELINE | I2 | 2024-06 | AVAILABLE | 54 | 0.9512 | -0.6951 |
| BASELINE | I2 | 2024-07 | AVAILABLE | 56 | 0.9638 | -0.3811 |
| BASELINE | I2 | 2024-08 | AVAILABLE | 62 | 1.5532 | 5.8061 |
| BASELINE | I2 | 2024-09 | AVAILABLE | 49 | 1.6862 | 5.2600 |
| BASELINE | I2 | 2024-10 | AVAILABLE | 61 | 0.7935 | -2.5290 |
| BASELINE | I2 | 2024-11 | AVAILABLE | 69 | 3.1744 | 33.0361 |
| BASELINE | I2 | 2024-12 | AVAILABLE | 61 | 2.0527 | 10.1127 |
| BASELINE | I3 | 2023-01 | AVAILABLE | 8 | 1.9009 | 2.7517 |
| BASELINE | I3 | 2023-02 | AVAILABLE | 18 | 1.3000 | 2.1806 |
| BASELINE | I3 | 2023-03 | AVAILABLE | 13 | 0.3519 | -3.6935 |
| BASELINE | I3 | 2023-04 | AVAILABLE | 18 | 6.5942 | 26.3518 |
| BASELINE | I3 | 2023-05 | AVAILABLE | 21 | 0.7384 | -1.8046 |
| BASELINE | I3 | 2023-06 | AVAILABLE | 17 | 1.0225 | 0.1704 |
| BASELINE | I3 | 2023-07 | AVAILABLE | 22 | 2.5320 | 10.4768 |
| BASELINE | I3 | 2023-08 | AVAILABLE | 41 | 0.4166 | -10.1880 |
| BASELINE | I3 | 2023-09 | AVAILABLE | 22 | 1.6123 | 5.1858 |
| BASELINE | I3 | 2023-10 | AVAILABLE | 36 | 3.3001 | 18.6922 |
| BASELINE | I3 | 2023-11 | AVAILABLE | 30 | 1.8186 | 8.2164 |
| BASELINE | I3 | 2023-12 | AVAILABLE | 45 | 2.1911 | 15.9878 |
| BASELINE | I3 | 2024-01 | AVAILABLE | 33 | 1.4732 | 4.9374 |
| BASELINE | I3 | 2024-02 | AVAILABLE | 50 | 0.3576 | -15.1954 |
| BASELINE | I3 | 2024-03 | AVAILABLE | 49 | 0.5510 | -9.6028 |
| BASELINE | I3 | 2024-04 | AVAILABLE | 56 | 0.8217 | -4.0025 |
| BASELINE | I3 | 2024-05 | AVAILABLE | 54 | 0.6459 | -7.1465 |
| BASELINE | I3 | 2024-06 | AVAILABLE | 48 | 0.7594 | -4.8963 |
| BASELINE | I3 | 2024-07 | AVAILABLE | 42 | 1.1846 | 2.7135 |
| BASELINE | I3 | 2024-08 | AVAILABLE | 49 | 1.2380 | 3.7534 |
| BASELINE | I3 | 2024-09 | AVAILABLE | 40 | 1.4199 | 4.9885 |
| BASELINE | I3 | 2024-10 | AVAILABLE | 44 | 0.8471 | -2.8078 |
| BASELINE | I3 | 2024-11 | AVAILABLE | 50 | 3.2015 | 36.7401 |
| BASELINE | I3 | 2024-12 | AVAILABLE | 47 | 1.0212 | 0.4269 |
| OPTIMIZED | CONTROL | 2023-01 | AVAILABLE | 7 | 2.0647 | 3.2090 |
| OPTIMIZED | CONTROL | 2023-02 | AVAILABLE | 13 | 2.3478 | 6.6877 |
| OPTIMIZED | CONTROL | 2023-03 | AVAILABLE | 13 | 0.1473 | -7.6677 |
| OPTIMIZED | CONTROL | 2023-04 | AVAILABLE | 13 | 11.1980 | 31.0016 |
| OPTIMIZED | CONTROL | 2023-05 | AVAILABLE | 20 | 0.4820 | -5.2475 |
| OPTIMIZED | CONTROL | 2023-06 | AVAILABLE | 13 | 1.7579 | 4.2143 |
| OPTIMIZED | CONTROL | 2023-07 | AVAILABLE | 16 | 3.4495 | 16.7258 |
| OPTIMIZED | CONTROL | 2023-08 | AVAILABLE | 36 | 0.5382 | -9.4074 |
| OPTIMIZED | CONTROL | 2023-09 | AVAILABLE | 18 | 1.7789 | 7.3847 |
| OPTIMIZED | CONTROL | 2023-10 | AVAILABLE | 30 | 5.2308 | 27.7491 |
| OPTIMIZED | CONTROL | 2023-11 | AVAILABLE | 28 | 1.3138 | 4.0809 |
| OPTIMIZED | CONTROL | 2023-12 | AVAILABLE | 36 | 2.3574 | 19.8874 |
| OPTIMIZED | CONTROL | 2024-01 | AVAILABLE | 32 | 1.2532 | 3.4461 |
| OPTIMIZED | CONTROL | 2024-02 | AVAILABLE | 36 | 0.9175 | -1.4773 |
| OPTIMIZED | CONTROL | 2024-03 | AVAILABLE | 36 | 1.1589 | 3.0465 |
| OPTIMIZED | CONTROL | 2024-04 | AVAILABLE | 48 | 0.9221 | -1.9484 |
| OPTIMIZED | CONTROL | 2024-05 | AVAILABLE | 41 | 0.9247 | -1.4023 |
| OPTIMIZED | CONTROL | 2024-06 | AVAILABLE | 41 | 1.2442 | 5.4406 |
| OPTIMIZED | CONTROL | 2024-07 | AVAILABLE | 35 | 1.1519 | 2.6465 |
| OPTIMIZED | CONTROL | 2024-08 | AVAILABLE | 40 | 1.1669 | 3.3666 |
| OPTIMIZED | CONTROL | 2024-09 | AVAILABLE | 34 | 1.4099 | 6.0285 |
| OPTIMIZED | CONTROL | 2024-10 | AVAILABLE | 40 | 0.8862 | -2.4057 |
| OPTIMIZED | CONTROL | 2024-11 | AVAILABLE | 39 | 6.2974 | 54.1860 |
| OPTIMIZED | CONTROL | 2024-12 | AVAILABLE | 36 | 1.4506 | 9.1748 |
| OPTIMIZED | I1 | 2023-01 | AVAILABLE | 8 | 1.8346 | 2.5353 |
| OPTIMIZED | I1 | 2023-02 | AVAILABLE | 17 | 1.3831 | 2.8562 |
| OPTIMIZED | I1 | 2023-03 | AVAILABLE | 13 | 0.2059 | -5.1066 |
| OPTIMIZED | I1 | 2023-04 | AVAILABLE | 18 | 5.6383 | 23.7782 |
| OPTIMIZED | I1 | 2023-05 | AVAILABLE | 21 | 0.5394 | -3.8622 |
| OPTIMIZED | I1 | 2023-06 | AVAILABLE | 17 | 0.8199 | -1.4634 |
| OPTIMIZED | I1 | 2023-07 | AVAILABLE | 19 | 3.3985 | 15.4611 |
| OPTIMIZED | I1 | 2023-08 | AVAILABLE | 41 | 0.4844 | -9.6465 |
| OPTIMIZED | I1 | 2023-09 | AVAILABLE | 20 | 2.1076 | 8.8802 |
| OPTIMIZED | I1 | 2023-10 | AVAILABLE | 33 | 3.9717 | 24.0268 |
| OPTIMIZED | I1 | 2023-11 | AVAILABLE | 30 | 1.2739 | 3.4546 |
| OPTIMIZED | I1 | 2023-12 | AVAILABLE | 43 | 2.1572 | 16.6316 |
| OPTIMIZED | I1 | 2024-01 | AVAILABLE | 33 | 1.1853 | 2.1445 |
| OPTIMIZED | I1 | 2024-02 | AVAILABLE | 49 | 0.3251 | -16.5099 |
| OPTIMIZED | I1 | 2024-03 | AVAILABLE | 46 | 0.7912 | -4.0452 |
| OPTIMIZED | I1 | 2024-04 | AVAILABLE | 55 | 0.8381 | -3.7341 |
| OPTIMIZED | I1 | 2024-05 | AVAILABLE | 54 | 0.5594 | -9.4243 |
| OPTIMIZED | I1 | 2024-06 | AVAILABLE | 46 | 1.1938 | 4.1010 |
| OPTIMIZED | I1 | 2024-07 | AVAILABLE | 40 | 1.2560 | 3.3977 |
| OPTIMIZED | I1 | 2024-08 | AVAILABLE | 47 | 1.2559 | 3.9760 |
| OPTIMIZED | I1 | 2024-09 | AVAILABLE | 37 | 1.5837 | 6.8146 |
| OPTIMIZED | I1 | 2024-10 | AVAILABLE | 43 | 0.8559 | -2.9699 |
| OPTIMIZED | I1 | 2024-11 | AVAILABLE | 46 | 3.9499 | 42.1039 |
| OPTIMIZED | I1 | 2024-12 | AVAILABLE | 43 | 1.3383 | 6.2675 |
| OPTIMIZED | I2 | 2023-01 | AVAILABLE | 9 | 2.0320 | 2.8304 |
| OPTIMIZED | I2 | 2023-02 | AVAILABLE | 25 | 1.1903 | 1.1760 |
| OPTIMIZED | I2 | 2023-03 | AVAILABLE | 14 | 0.2079 | -3.2449 |
| OPTIMIZED | I2 | 2023-04 | AVAILABLE | 27 | 4.5232 | 18.4786 |
| OPTIMIZED | I2 | 2023-05 | AVAILABLE | 27 | 0.3503 | -4.2859 |
| OPTIMIZED | I2 | 2023-06 | AVAILABLE | 25 | 0.2938 | -6.1244 |
| OPTIMIZED | I2 | 2023-07 | AVAILABLE | 27 | 2.3598 | 9.9072 |
| OPTIMIZED | I2 | 2023-08 | AVAILABLE | 52 | 0.3414 | -9.7897 |
| OPTIMIZED | I2 | 2023-09 | AVAILABLE | 22 | 2.8828 | 10.0750 |
| OPTIMIZED | I2 | 2023-10 | AVAILABLE | 55 | 2.2272 | 10.6588 |
| OPTIMIZED | I2 | 2023-11 | AVAILABLE | 32 | 1.8049 | 6.6979 |
| OPTIMIZED | I2 | 2023-12 | AVAILABLE | 57 | 2.2377 | 12.0608 |
| OPTIMIZED | I2 | 2024-01 | AVAILABLE | 43 | 1.2490 | 2.2165 |
| OPTIMIZED | I2 | 2024-02 | AVAILABLE | 59 | 0.4327 | -9.6369 |
| OPTIMIZED | I2 | 2024-03 | AVAILABLE | 57 | 0.7769 | -3.0152 |
| OPTIMIZED | I2 | 2024-04 | AVAILABLE | 79 | 0.5258 | -9.1693 |
| OPTIMIZED | I2 | 2024-05 | AVAILABLE | 66 | 0.6014 | -6.4668 |
| OPTIMIZED | I2 | 2024-06 | AVAILABLE | 53 | 1.3617 | 4.9608 |
| OPTIMIZED | I2 | 2024-07 | AVAILABLE | 55 | 0.9495 | -0.5326 |
| OPTIMIZED | I2 | 2024-08 | AVAILABLE | 60 | 1.5912 | 6.2002 |
| OPTIMIZED | I2 | 2024-09 | AVAILABLE | 47 | 1.9031 | 6.9704 |
| OPTIMIZED | I2 | 2024-10 | AVAILABLE | 61 | 0.7139 | -3.5637 |
| OPTIMIZED | I2 | 2024-11 | AVAILABLE | 64 | 4.0816 | 38.6445 |
| OPTIMIZED | I2 | 2024-12 | AVAILABLE | 58 | 2.7250 | 14.7362 |
| OPTIMIZED | I3 | 2023-01 | AVAILABLE | 8 | 1.7583 | 2.4034 |
| OPTIMIZED | I3 | 2023-02 | AVAILABLE | 17 | 1.3953 | 2.9217 |
| OPTIMIZED | I3 | 2023-03 | AVAILABLE | 13 | 0.2128 | -4.8995 |
| OPTIMIZED | I3 | 2023-04 | AVAILABLE | 18 | 5.6383 | 23.7782 |
| OPTIMIZED | I3 | 2023-05 | AVAILABLE | 21 | 0.5394 | -3.8622 |
| OPTIMIZED | I3 | 2023-06 | AVAILABLE | 17 | 0.8659 | -1.0316 |
| OPTIMIZED | I3 | 2023-07 | AVAILABLE | 19 | 3.4651 | 15.5850 |
| OPTIMIZED | I3 | 2023-08 | AVAILABLE | 41 | 0.4844 | -9.6465 |
| OPTIMIZED | I3 | 2023-09 | AVAILABLE | 22 | 1.7112 | 6.3863 |
| OPTIMIZED | I3 | 2023-10 | AVAILABLE | 33 | 3.9717 | 24.0268 |
| OPTIMIZED | I3 | 2023-11 | AVAILABLE | 30 | 1.3818 | 4.4386 |
| OPTIMIZED | I3 | 2023-12 | AVAILABLE | 43 | 2.2327 | 17.1175 |
| OPTIMIZED | I3 | 2024-01 | AVAILABLE | 33 | 1.2775 | 2.9803 |
| OPTIMIZED | I3 | 2024-02 | AVAILABLE | 49 | 0.3362 | -15.7031 |
| OPTIMIZED | I3 | 2024-03 | AVAILABLE | 48 | 0.7057 | -6.3354 |
| OPTIMIZED | I3 | 2024-04 | AVAILABLE | 55 | 0.8492 | -3.4318 |
| OPTIMIZED | I3 | 2024-05 | AVAILABLE | 54 | 0.5595 | -9.4234 |
| OPTIMIZED | I3 | 2024-06 | AVAILABLE | 46 | 1.3006 | 5.8374 |
| OPTIMIZED | I3 | 2024-07 | AVAILABLE | 41 | 1.1518 | 2.1964 |
| OPTIMIZED | I3 | 2024-08 | AVAILABLE | 47 | 1.2559 | 3.9760 |
| OPTIMIZED | I3 | 2024-09 | AVAILABLE | 37 | 1.5837 | 6.8146 |
| OPTIMIZED | I3 | 2024-10 | AVAILABLE | 43 | 0.9268 | -1.3931 |
| OPTIMIZED | I3 | 2024-11 | AVAILABLE | 46 | 3.9499 | 42.1039 |
| OPTIMIZED | I3 | 2024-12 | AVAILABLE | 43 | 1.3505 | 6.4350 |

### USDRUBF / REFERENCE_2ATR

| version | rule | month | coverage | closed_trades | gross_PF | gross_R |
| --- | --- | --- | --- | --- | --- | --- |
| BASELINE | CONTROL | 2023-01 | AVAILABLE | 5 | 3.0896 | 4.1792 |
| BASELINE | CONTROL | 2023-02 | AVAILABLE | 8 | 2.2022 | 3.2765 |
| BASELINE | CONTROL | 2023-03 | AVAILABLE | 6 | 0.5459 | -1.0795 |
| BASELINE | CONTROL | 2023-04 | AVAILABLE | 6 | 16.7081 | 18.8632 |
| BASELINE | CONTROL | 2023-05 | AVAILABLE | 11 | 0.4611 | -2.1692 |
| BASELINE | CONTROL | 2023-06 | AVAILABLE | 10 | 1.5545 | 2.6715 |
| BASELINE | CONTROL | 2023-07 | AVAILABLE | 10 | 3.3093 | 8.8295 |
| BASELINE | CONTROL | 2023-08 | AVAILABLE | 14 | 1.0131 | 0.0854 |
| BASELINE | CONTROL | 2023-09 | AVAILABLE | 6 | 2.2010 | 3.4413 |
| BASELINE | CONTROL | 2023-10 | AVAILABLE | 14 | 8.3878 | 13.2261 |
| BASELINE | CONTROL | 2023-11 | AVAILABLE | 12 | 1.5949 | 2.4438 |
| BASELINE | CONTROL | 2023-12 | AVAILABLE | 9 | 6.6791 | 11.0910 |
| BASELINE | CONTROL | 2024-01 | AVAILABLE | 6 | 7.5247 | 4.4943 |
| BASELINE | CONTROL | 2024-02 | AVAILABLE | 7 | 0.5576 | -1.4710 |
| BASELINE | CONTROL | 2024-03 | AVAILABLE | 7 | 0.4109 | -2.1409 |
| BASELINE | CONTROL | 2024-04 | AVAILABLE | 11 | 0.3101 | -4.4527 |
| BASELINE | CONTROL | 2024-05 | AVAILABLE | 11 | 1.1444 | 0.6573 |
| BASELINE | CONTROL | 2024-06 | AVAILABLE | 10 | 1.0737 | 0.3641 |
| BASELINE | CONTROL | 2024-07 | AVAILABLE | 8 | 0.2584 | -4.0019 |
| BASELINE | CONTROL | 2024-08 | AVAILABLE | 10 | 1.9425 | 4.3981 |
| BASELINE | CONTROL | 2024-09 | AVAILABLE | 10 | 1.4762 | 2.0413 |
| BASELINE | CONTROL | 2024-10 | AVAILABLE | 13 | 0.3147 | -5.6307 |
| BASELINE | CONTROL | 2024-11 | AVAILABLE | 12 | 9.5997 | 11.6354 |
| BASELINE | CONTROL | 2024-12 | AVAILABLE | 10 | 0.7023 | -1.9950 |
| BASELINE | I1 | 2023-01 | AVAILABLE | 5 | 2.4563 | 3.3580 |
| BASELINE | I1 | 2023-02 | AVAILABLE | 9 | 2.2771 | 3.3660 |
| BASELINE | I1 | 2023-03 | AVAILABLE | 6 | 0.7819 | -0.3621 |
| BASELINE | I1 | 2023-04 | AVAILABLE | 7 | 14.1043 | 17.4407 |
| BASELINE | I1 | 2023-05 | AVAILABLE | 11 | 0.6953 | -0.8134 |
| BASELINE | I1 | 2023-06 | AVAILABLE | 11 | 1.4998 | 2.3689 |
| BASELINE | I1 | 2023-07 | AVAILABLE | 11 | 2.9848 | 5.6570 |
| BASELINE | I1 | 2023-08 | AVAILABLE | 17 | 0.9174 | -0.5297 |
| BASELINE | I1 | 2023-09 | AVAILABLE | 8 | 1.7901 | 2.4855 |
| BASELINE | I1 | 2023-10 | AVAILABLE | 14 | 5.4962 | 11.6372 |
| BASELINE | I1 | 2023-11 | AVAILABLE | 12 | 1.3890 | 1.6111 |
| BASELINE | I1 | 2023-12 | AVAILABLE | 11 | 4.2584 | 8.0590 |
| BASELINE | I1 | 2024-01 | AVAILABLE | 6 | 7.1031 | 3.7310 |
| BASELINE | I1 | 2024-02 | AVAILABLE | 9 | 0.0588 | -4.5518 |
| BASELINE | I1 | 2024-03 | AVAILABLE | 9 | 0.3143 | -2.8420 |
| BASELINE | I1 | 2024-04 | AVAILABLE | 14 | 0.0893 | -6.9051 |
| BASELINE | I1 | 2024-05 | AVAILABLE | 12 | 1.2974 | 1.1830 |
| BASELINE | I1 | 2024-06 | AVAILABLE | 10 | 1.0532 | 0.2178 |
| BASELINE | I1 | 2024-07 | AVAILABLE | 9 | 0.2194 | -2.7969 |
| BASELINE | I1 | 2024-08 | AVAILABLE | 9 | 3.2534 | 6.2785 |
| BASELINE | I1 | 2024-09 | AVAILABLE | 11 | 1.7260 | 2.5374 |
| BASELINE | I1 | 2024-10 | AVAILABLE | 13 | 0.3394 | -4.8762 |
| BASELINE | I1 | 2024-11 | AVAILABLE | 13 | 3.9050 | 9.2849 |
| BASELINE | I1 | 2024-12 | AVAILABLE | 11 | 0.7229 | -1.6219 |
| BASELINE | I2 | 2023-01 | AVAILABLE | 6 | 2.5107 | 3.3532 |
| BASELINE | I2 | 2023-02 | AVAILABLE | 15 | 1.8163 | 2.1087 |
| BASELINE | I2 | 2023-03 | AVAILABLE | 6 | 1.1854 | 0.2030 |
| BASELINE | I2 | 2023-04 | AVAILABLE | 14 | 6.7937 | 13.5882 |
| BASELINE | I2 | 2023-05 | AVAILABLE | 12 | 0.6628 | -0.6916 |
| BASELINE | I2 | 2023-06 | AVAILABLE | 15 | 0.6578 | -1.5517 |
| BASELINE | I2 | 2023-07 | AVAILABLE | 12 | 6.8652 | 5.9618 |
| BASELINE | I2 | 2023-08 | AVAILABLE | 25 | 0.7800 | -1.1356 |
| BASELINE | I2 | 2023-09 | AVAILABLE | 10 | 1.5735 | 1.5110 |
| BASELINE | I2 | 2023-10 | AVAILABLE | 22 | 2.7947 | 5.3199 |
| BASELINE | I2 | 2023-11 | AVAILABLE | 12 | 1.8003 | 2.5571 |
| BASELINE | I2 | 2023-12 | AVAILABLE | 17 | 2.9991 | 4.5765 |
| BASELINE | I2 | 2024-01 | AVAILABLE | 9 | 1.9342 | 1.7532 |
| BASELINE | I2 | 2024-02 | AVAILABLE | 14 | 0.0276 | -3.4476 |
| BASELINE | I2 | 2024-03 | AVAILABLE | 10 | 0.4586 | -1.5383 |
| BASELINE | I2 | 2024-04 | AVAILABLE | 18 | 0.0000 | -5.3944 |
| BASELINE | I2 | 2024-05 | AVAILABLE | 17 | 0.6705 | -1.7295 |
| BASELINE | I2 | 2024-06 | AVAILABLE | 11 | 2.3749 | 2.4959 |
| BASELINE | I2 | 2024-07 | AVAILABLE | 11 | 0.3599 | -1.2762 |
| BASELINE | I2 | 2024-08 | AVAILABLE | 13 | 2.7023 | 4.0911 |
| BASELINE | I2 | 2024-09 | AVAILABLE | 11 | 5.8325 | 4.9983 |
| BASELINE | I2 | 2024-10 | AVAILABLE | 16 | 0.0000 | -4.0617 |
| BASELINE | I2 | 2024-11 | AVAILABLE | 18 | 4.5336 | 8.0487 |
| BASELINE | I2 | 2024-12 | AVAILABLE | 12 | 1.5995 | 1.5857 |
| BASELINE | I3 | 2023-01 | AVAILABLE | 5 | 2.4620 | 3.3633 |
| BASELINE | I3 | 2023-02 | AVAILABLE | 9 | 2.2771 | 3.3660 |
| BASELINE | I3 | 2023-03 | AVAILABLE | 6 | 0.7819 | -0.3621 |
| BASELINE | I3 | 2023-04 | AVAILABLE | 7 | 14.1043 | 17.4407 |
| BASELINE | I3 | 2023-05 | AVAILABLE | 11 | 0.6953 | -0.8134 |
| BASELINE | I3 | 2023-06 | AVAILABLE | 11 | 1.5537 | 2.5335 |
| BASELINE | I3 | 2023-07 | AVAILABLE | 11 | 2.9848 | 5.6570 |
| BASELINE | I3 | 2023-08 | AVAILABLE | 17 | 0.9174 | -0.5297 |
| BASELINE | I3 | 2023-09 | AVAILABLE | 8 | 1.8153 | 2.5291 |
| BASELINE | I3 | 2023-10 | AVAILABLE | 14 | 5.4962 | 11.6372 |
| BASELINE | I3 | 2023-11 | AVAILABLE | 12 | 1.4451 | 1.7719 |
| BASELINE | I3 | 2023-12 | AVAILABLE | 11 | 4.2584 | 8.0590 |
| BASELINE | I3 | 2024-01 | AVAILABLE | 6 | 7.1031 | 3.7310 |
| BASELINE | I3 | 2024-02 | AVAILABLE | 9 | 0.0588 | -4.5518 |
| BASELINE | I3 | 2024-03 | AVAILABLE | 9 | 0.3143 | -2.8420 |
| BASELINE | I3 | 2024-04 | AVAILABLE | 14 | 0.0893 | -6.9051 |
| BASELINE | I3 | 2024-05 | AVAILABLE | 12 | 1.2974 | 1.1830 |
| BASELINE | I3 | 2024-06 | AVAILABLE | 10 | 1.1131 | 0.4381 |
| BASELINE | I3 | 2024-07 | AVAILABLE | 9 | 0.2210 | -2.7718 |
| BASELINE | I3 | 2024-08 | AVAILABLE | 9 | 3.2534 | 6.2785 |
| BASELINE | I3 | 2024-09 | AVAILABLE | 11 | 1.7260 | 2.5374 |
| BASELINE | I3 | 2024-10 | AVAILABLE | 13 | 0.3676 | -4.3098 |
| BASELINE | I3 | 2024-11 | AVAILABLE | 13 | 3.9050 | 9.2849 |
| BASELINE | I3 | 2024-12 | AVAILABLE | 11 | 0.7494 | -1.4150 |
| OPTIMIZED | CONTROL | 2023-01 | AVAILABLE | 5 | 2.9481 | 3.9826 |
| OPTIMIZED | CONTROL | 2023-02 | AVAILABLE | 7 | 2.6533 | 4.5087 |
| OPTIMIZED | CONTROL | 2023-03 | AVAILABLE | 6 | 0.2847 | -2.1402 |
| OPTIMIZED | CONTROL | 2023-04 | AVAILABLE | 6 | 11.8693 | 17.3654 |
| OPTIMIZED | CONTROL | 2023-05 | AVAILABLE | 11 | 0.3432 | -3.1868 |
| OPTIMIZED | CONTROL | 2023-06 | AVAILABLE | 8 | 2.8680 | 5.6041 |
| OPTIMIZED | CONTROL | 2023-07 | AVAILABLE | 9 | 3.1807 | 9.7958 |
| OPTIMIZED | CONTROL | 2023-08 | AVAILABLE | 13 | 1.1664 | 1.2642 |
| OPTIMIZED | CONTROL | 2023-09 | AVAILABLE | 6 | 1.9444 | 2.8701 |
| OPTIMIZED | CONTROL | 2023-10 | AVAILABLE | 11 | 22.9895 | 21.1407 |
| OPTIMIZED | CONTROL | 2023-11 | AVAILABLE | 12 | 1.0115 | 0.0593 |
| OPTIMIZED | CONTROL | 2023-12 | AVAILABLE | 9 | 5.2273 | 9.3931 |
| OPTIMIZED | CONTROL | 2024-01 | AVAILABLE | 6 | 4.7602 | 3.4129 |
| OPTIMIZED | CONTROL | 2024-02 | AVAILABLE | 7 | 0.3781 | -2.2770 |
| OPTIMIZED | CONTROL | 2024-03 | AVAILABLE | 6 | 0.6190 | -1.3987 |
| OPTIMIZED | CONTROL | 2024-04 | AVAILABLE | 11 | 0.2478 | -5.1868 |
| OPTIMIZED | CONTROL | 2024-05 | AVAILABLE | 11 | 0.9752 | -0.1200 |
| OPTIMIZED | CONTROL | 2024-06 | AVAILABLE | 10 | 0.9972 | -0.0159 |
| OPTIMIZED | CONTROL | 2024-07 | AVAILABLE | 8 | 0.2067 | -4.5106 |
| OPTIMIZED | CONTROL | 2024-08 | AVAILABLE | 10 | 1.7036 | 3.5368 |
| OPTIMIZED | CONTROL | 2024-09 | AVAILABLE | 10 | 1.9221 | 3.8513 |
| OPTIMIZED | CONTROL | 2024-10 | AVAILABLE | 11 | 0.8661 | -0.9562 |
| OPTIMIZED | CONTROL | 2024-11 | AVAILABLE | 11 | 8.3488 | 9.8895 |
| OPTIMIZED | CONTROL | 2024-12 | AVAILABLE | 9 | 0.8184 | -1.0626 |
| OPTIMIZED | I1 | 2023-01 | AVAILABLE | 5 | 2.5182 | 3.3599 |
| OPTIMIZED | I1 | 2023-02 | AVAILABLE | 8 | 2.7397 | 4.5947 |
| OPTIMIZED | I1 | 2023-03 | AVAILABLE | 6 | 0.4222 | -1.1656 |
| OPTIMIZED | I1 | 2023-04 | AVAILABLE | 7 | 10.4902 | 16.1153 |
| OPTIMIZED | I1 | 2023-05 | AVAILABLE | 11 | 0.4249 | -2.2542 |
| OPTIMIZED | I1 | 2023-06 | AVAILABLE | 11 | 1.3090 | 1.4907 |
| OPTIMIZED | I1 | 2023-07 | AVAILABLE | 9 | 6.5738 | 12.1143 |
| OPTIMIZED | I1 | 2023-08 | AVAILABLE | 16 | 1.0931 | 0.6121 |
| OPTIMIZED | I1 | 2023-09 | AVAILABLE | 8 | 1.4523 | 1.6646 |
| OPTIMIZED | I1 | 2023-10 | AVAILABLE | 11 | 14.0796 | 19.9157 |
| OPTIMIZED | I1 | 2023-11 | AVAILABLE | 12 | 0.8671 | -0.7095 |
| OPTIMIZED | I1 | 2023-12 | AVAILABLE | 11 | 3.3925 | 6.6000 |
| OPTIMIZED | I1 | 2024-01 | AVAILABLE | 6 | 5.8148 | 2.9435 |
| OPTIMIZED | I1 | 2024-02 | AVAILABLE | 9 | 0.0000 | -5.2640 |
| OPTIMIZED | I1 | 2024-03 | AVAILABLE | 9 | 0.2523 | -3.4367 |
| OPTIMIZED | I1 | 2024-04 | AVAILABLE | 14 | 0.0811 | -7.1128 |
| OPTIMIZED | I1 | 2024-05 | AVAILABLE | 12 | 1.1356 | 0.5626 |
| OPTIMIZED | I1 | 2024-06 | AVAILABLE | 10 | 1.0530 | 0.2333 |
| OPTIMIZED | I1 | 2024-07 | AVAILABLE | 9 | 0.1582 | -3.0163 |
| OPTIMIZED | I1 | 2024-08 | AVAILABLE | 9 | 2.7934 | 5.4979 |
| OPTIMIZED | I1 | 2024-09 | AVAILABLE | 11 | 1.7248 | 2.7463 |
| OPTIMIZED | I1 | 2024-10 | AVAILABLE | 12 | 0.7283 | -2.1522 |
| OPTIMIZED | I1 | 2024-11 | AVAILABLE | 13 | 3.3032 | 7.6771 |
| OPTIMIZED | I1 | 2024-12 | AVAILABLE | 10 | 0.9367 | -0.2901 |
| OPTIMIZED | I2 | 2023-01 | AVAILABLE | 6 | 2.6762 | 3.4905 |
| OPTIMIZED | I2 | 2023-02 | AVAILABLE | 15 | 1.6278 | 1.7268 |
| OPTIMIZED | I2 | 2023-03 | AVAILABLE | 6 | 0.7778 | -0.2433 |
| OPTIMIZED | I2 | 2023-04 | AVAILABLE | 14 | 5.7384 | 12.4159 |
| OPTIMIZED | I2 | 2023-05 | AVAILABLE | 12 | 0.3978 | -1.6407 |
| OPTIMIZED | I2 | 2023-06 | AVAILABLE | 15 | 0.4853 | -2.3339 |
| OPTIMIZED | I2 | 2023-07 | AVAILABLE | 10 | 14.6750 | 11.2616 |
| OPTIMIZED | I2 | 2023-08 | AVAILABLE | 25 | 0.6733 | -1.7291 |
| OPTIMIZED | I2 | 2023-09 | AVAILABLE | 10 | 1.3849 | 1.0765 |
| OPTIMIZED | I2 | 2023-10 | AVAILABLE | 20 | 4.2444 | 9.0271 |
| OPTIMIZED | I2 | 2023-11 | AVAILABLE | 12 | 1.1922 | 0.7462 |
| OPTIMIZED | I2 | 2023-12 | AVAILABLE | 17 | 2.4613 | 3.4086 |
| OPTIMIZED | I2 | 2024-01 | AVAILABLE | 9 | 1.6901 | 1.2952 |
| OPTIMIZED | I2 | 2024-02 | AVAILABLE | 14 | 0.0000 | -3.5884 |
| OPTIMIZED | I2 | 2024-03 | AVAILABLE | 10 | 0.3725 | -1.9535 |
| OPTIMIZED | I2 | 2024-04 | AVAILABLE | 18 | 0.0000 | -5.3944 |
| OPTIMIZED | I2 | 2024-05 | AVAILABLE | 17 | 0.6599 | -1.6899 |
| OPTIMIZED | I2 | 2024-06 | AVAILABLE | 11 | 2.1824 | 2.5114 |
| OPTIMIZED | I2 | 2024-07 | AVAILABLE | 11 | 0.2488 | -1.4977 |
| OPTIMIZED | I2 | 2024-08 | AVAILABLE | 13 | 2.5312 | 3.6799 |
| OPTIMIZED | I2 | 2024-09 | AVAILABLE | 11 | 6.3187 | 5.5012 |
| OPTIMIZED | I2 | 2024-10 | AVAILABLE | 16 | 0.0000 | -4.1627 |
| OPTIMIZED | I2 | 2024-11 | AVAILABLE | 18 | 3.8968 | 6.5983 |
| OPTIMIZED | I2 | 2024-12 | AVAILABLE | 11 | 2.0107 | 2.1590 |
| OPTIMIZED | I3 | 2023-01 | AVAILABLE | 5 | 2.3766 | 3.2280 |
| OPTIMIZED | I3 | 2023-02 | AVAILABLE | 8 | 2.7397 | 4.5947 |
| OPTIMIZED | I3 | 2023-03 | AVAILABLE | 6 | 0.4222 | -1.1656 |
| OPTIMIZED | I3 | 2023-04 | AVAILABLE | 7 | 10.4902 | 16.1153 |
| OPTIMIZED | I3 | 2023-05 | AVAILABLE | 11 | 0.4249 | -2.2542 |
| OPTIMIZED | I3 | 2023-06 | AVAILABLE | 11 | 1.3726 | 1.7140 |
| OPTIMIZED | I3 | 2023-07 | AVAILABLE | 9 | 6.5738 | 12.1143 |
| OPTIMIZED | I3 | 2023-08 | AVAILABLE | 16 | 1.0931 | 0.6121 |
| OPTIMIZED | I3 | 2023-09 | AVAILABLE | 8 | 1.5492 | 1.8949 |
| OPTIMIZED | I3 | 2023-10 | AVAILABLE | 11 | 14.0796 | 19.9157 |
| OPTIMIZED | I3 | 2023-11 | AVAILABLE | 12 | 0.9370 | -0.3113 |
| OPTIMIZED | I3 | 2023-12 | AVAILABLE | 11 | 3.3925 | 6.6000 |
| OPTIMIZED | I3 | 2024-01 | AVAILABLE | 6 | 5.8148 | 2.9435 |
| OPTIMIZED | I3 | 2024-02 | AVAILABLE | 9 | 0.0000 | -5.2640 |
| OPTIMIZED | I3 | 2024-03 | AVAILABLE | 9 | 0.2523 | -3.4367 |
| OPTIMIZED | I3 | 2024-04 | AVAILABLE | 14 | 0.0811 | -7.1128 |
| OPTIMIZED | I3 | 2024-05 | AVAILABLE | 12 | 1.1358 | 0.5635 |
| OPTIMIZED | I3 | 2024-06 | AVAILABLE | 10 | 1.1084 | 0.4535 |
| OPTIMIZED | I3 | 2024-07 | AVAILABLE | 9 | 0.1593 | -2.9912 |
| OPTIMIZED | I3 | 2024-08 | AVAILABLE | 9 | 2.7934 | 5.4979 |
| OPTIMIZED | I3 | 2024-09 | AVAILABLE | 11 | 1.7248 | 2.7463 |
| OPTIMIZED | I3 | 2024-10 | AVAILABLE | 12 | 0.8208 | -1.2597 |
| OPTIMIZED | I3 | 2024-11 | AVAILABLE | 13 | 3.3032 | 7.6771 |
| OPTIMIZED | I3 | 2024-12 | AVAILABLE | 10 | 0.9367 | -0.2901 |

### CNYRUBF / REFERENCE_2ATR

| version | rule | month | coverage | closed_trades | gross_PF | gross_R |
| --- | --- | --- | --- | --- | --- | --- |
| BASELINE | CONTROL | 2023-01 | AVAILABLE | 2 | 0.5143 | -0.3694 |
| BASELINE | CONTROL | 2023-02 | AVAILABLE | 7 | 1.3462 | 0.9187 |
| BASELINE | CONTROL | 2023-03 | AVAILABLE | 7 | 0.1213 | -5.1227 |
| BASELINE | CONTROL | 2023-04 | AVAILABLE | 8 | 5.7573 | 10.4780 |
| BASELINE | CONTROL | 2023-05 | AVAILABLE | 9 | 0.7707 | -1.1379 |
| BASELINE | CONTROL | 2023-06 | AVAILABLE | 5 | 0.7247 | -0.6483 |
| BASELINE | CONTROL | 2023-07 | AVAILABLE | 4 | — | 10.3612 |
| BASELINE | CONTROL | 2023-08 | AVAILABLE | 9 | 0.0723 | -4.1957 |
| BASELINE | CONTROL | 2023-09 | AVAILABLE | 6 | 4.0780 | 4.5425 |
| BASELINE | CONTROL | 2023-10 | AVAILABLE | 11 | 4.1398 | 9.1544 |
| BASELINE | CONTROL | 2023-11 | AVAILABLE | 8 | 2.3373 | 4.0686 |
| BASELINE | CONTROL | 2023-12 | AVAILABLE | 9 | 1.2983 | 1.1197 |
| BASELINE | CONTROL | 2024-01 | AVAILABLE | 10 | 2.7342 | 4.2383 |
| BASELINE | CONTROL | 2024-02 | AVAILABLE | 12 | 0.3884 | -4.1524 |
| BASELINE | CONTROL | 2024-03 | AVAILABLE | 10 | 0.1870 | -4.7080 |
| BASELINE | CONTROL | 2024-04 | AVAILABLE | 9 | 1.7044 | 2.4827 |
| BASELINE | CONTROL | 2024-05 | AVAILABLE | 12 | 0.4171 | -3.9747 |
| BASELINE | CONTROL | 2024-06 | AVAILABLE | 10 | 1.3262 | 1.7962 |
| BASELINE | CONTROL | 2024-07 | AVAILABLE | 7 | 0.9518 | -0.1788 |
| BASELINE | CONTROL | 2024-08 | AVAILABLE | 8 | 0.2477 | -2.9852 |
| BASELINE | CONTROL | 2024-09 | AVAILABLE | 8 | 3.1857 | 3.8197 |
| BASELINE | CONTROL | 2024-10 | AVAILABLE | 8 | 1.3834 | 1.3057 |
| BASELINE | CONTROL | 2024-11 | AVAILABLE | 10 | 6.4841 | 14.0619 |
| BASELINE | CONTROL | 2024-12 | AVAILABLE | 10 | 1.9131 | 4.1577 |
| BASELINE | I1 | 2023-01 | AVAILABLE | 3 | 0.1888 | -0.6116 |
| BASELINE | I1 | 2023-02 | AVAILABLE | 9 | 0.7338 | -1.2509 |
| BASELINE | I1 | 2023-03 | AVAILABLE | 7 | 0.1669 | -3.5303 |
| BASELINE | I1 | 2023-04 | AVAILABLE | 11 | 3.6367 | 8.9111 |
| BASELINE | I1 | 2023-05 | AVAILABLE | 10 | 0.7656 | -0.9912 |
| BASELINE | I1 | 2023-06 | AVAILABLE | 6 | 0.2149 | -2.3631 |
| BASELINE | I1 | 2023-07 | AVAILABLE | 6 | 10.2029 | 7.8382 |
| BASELINE | I1 | 2023-08 | AVAILABLE | 11 | 0.0000 | -6.5409 |
| BASELINE | I1 | 2023-09 | AVAILABLE | 6 | 6.4854 | 5.6241 |
| BASELINE | I1 | 2023-10 | AVAILABLE | 11 | 5.2765 | 9.7826 |
| BASELINE | I1 | 2023-11 | AVAILABLE | 10 | 1.8981 | 3.1272 |
| BASELINE | I1 | 2023-12 | AVAILABLE | 10 | 1.0892 | 0.3788 |
| BASELINE | I1 | 2024-01 | AVAILABLE | 10 | 3.3639 | 4.3052 |
| BASELINE | I1 | 2024-02 | AVAILABLE | 14 | 0.1761 | -4.9329 |
| BASELINE | I1 | 2024-03 | AVAILABLE | 12 | 0.1853 | -4.7593 |
| BASELINE | I1 | 2024-04 | AVAILABLE | 10 | 1.6295 | 2.3209 |
| BASELINE | I1 | 2024-05 | AVAILABLE | 15 | 0.3632 | -4.0931 |
| BASELINE | I1 | 2024-06 | AVAILABLE | 11 | 1.3543 | 1.9106 |
| BASELINE | I1 | 2024-07 | AVAILABLE | 8 | 0.8832 | -0.3969 |
| BASELINE | I1 | 2024-08 | AVAILABLE | 9 | 0.1395 | -3.0469 |
| BASELINE | I1 | 2024-09 | AVAILABLE | 8 | 3.8263 | 4.1123 |
| BASELINE | I1 | 2024-10 | AVAILABLE | 8 | 1.5231 | 1.6179 |
| BASELINE | I1 | 2024-11 | AVAILABLE | 12 | 3.8910 | 11.6115 |
| BASELINE | I1 | 2024-12 | AVAILABLE | 11 | 1.2526 | 1.4154 |
| BASELINE | I2 | 2023-01 | AVAILABLE | 3 | 0.2415 | -0.4471 |
| BASELINE | I2 | 2023-02 | AVAILABLE | 10 | 0.9184 | -0.2800 |
| BASELINE | I2 | 2023-03 | AVAILABLE | 8 | 0.0000 | -3.0016 |
| BASELINE | I2 | 2023-04 | AVAILABLE | 13 | 3.8202 | 7.2640 |
| BASELINE | I2 | 2023-05 | AVAILABLE | 15 | 0.4074 | -2.2947 |
| BASELINE | I2 | 2023-06 | AVAILABLE | 10 | 0.1640 | -3.2970 |
| BASELINE | I2 | 2023-07 | AVAILABLE | 8 | 1.5748 | 1.9843 |
| BASELINE | I2 | 2023-08 | AVAILABLE | 11 | 0.0000 | -4.0165 |
| BASELINE | I2 | 2023-09 | AVAILABLE | 6 | 15.7920 | 6.2283 |
| BASELINE | I2 | 2023-10 | AVAILABLE | 16 | 3.1502 | 6.0616 |
| BASELINE | I2 | 2023-11 | AVAILABLE | 11 | 3.2178 | 4.5554 |
| BASELINE | I2 | 2023-12 | AVAILABLE | 14 | 0.8538 | -0.3970 |
| BASELINE | I2 | 2024-01 | AVAILABLE | 16 | 1.8458 | 1.6682 |
| BASELINE | I2 | 2024-02 | AVAILABLE | 16 | 0.1055 | -3.1536 |
| BASELINE | I2 | 2024-03 | AVAILABLE | 15 | 0.1251 | -3.3314 |
| BASELINE | I2 | 2024-04 | AVAILABLE | 20 | 0.2812 | -4.0595 |
| BASELINE | I2 | 2024-05 | AVAILABLE | 16 | 0.5135 | -1.9123 |
| BASELINE | I2 | 2024-06 | AVAILABLE | 13 | 1.6331 | 2.1855 |
| BASELINE | I2 | 2024-07 | AVAILABLE | 9 | 0.0000 | -2.7383 |
| BASELINE | I2 | 2024-08 | AVAILABLE | 11 | 0.1435 | -2.0649 |
| BASELINE | I2 | 2024-09 | AVAILABLE | 12 | 0.9270 | -0.1583 |
| BASELINE | I2 | 2024-10 | AVAILABLE | 9 | 1.7666 | 1.8949 |
| BASELINE | I2 | 2024-11 | AVAILABLE | 17 | 4.2372 | 11.3394 |
| BASELINE | I2 | 2024-12 | AVAILABLE | 12 | 2.9412 | 4.6330 |
| BASELINE | I3 | 2023-01 | AVAILABLE | 3 | 0.1888 | -0.6116 |
| BASELINE | I3 | 2023-02 | AVAILABLE | 9 | 0.7441 | -1.1855 |
| BASELINE | I3 | 2023-03 | AVAILABLE | 7 | 0.1751 | -3.3314 |
| BASELINE | I3 | 2023-04 | AVAILABLE | 11 | 3.6367 | 8.9111 |
| BASELINE | I3 | 2023-05 | AVAILABLE | 10 | 0.7656 | -0.9912 |
| BASELINE | I3 | 2023-06 | AVAILABLE | 6 | 0.2149 | -2.3631 |
| BASELINE | I3 | 2023-07 | AVAILABLE | 6 | 10.2029 | 7.8382 |
| BASELINE | I3 | 2023-08 | AVAILABLE | 11 | 0.0000 | -6.5409 |
| BASELINE | I3 | 2023-09 | AVAILABLE | 8 | 1.9545 | 2.5398 |
| BASELINE | I3 | 2023-10 | AVAILABLE | 11 | 5.2765 | 9.7826 |
| BASELINE | I3 | 2023-11 | AVAILABLE | 10 | 2.0866 | 3.4418 |
| BASELINE | I3 | 2023-12 | AVAILABLE | 10 | 1.0892 | 0.3788 |
| BASELINE | I3 | 2024-01 | AVAILABLE | 10 | 3.3639 | 4.3052 |
| BASELINE | I3 | 2024-02 | AVAILABLE | 14 | 0.1761 | -4.9329 |
| BASELINE | I3 | 2024-03 | AVAILABLE | 12 | 0.1856 | -4.7519 |
| BASELINE | I3 | 2024-04 | AVAILABLE | 10 | 1.6609 | 2.3905 |
| BASELINE | I3 | 2024-05 | AVAILABLE | 15 | 0.3632 | -4.0931 |
| BASELINE | I3 | 2024-06 | AVAILABLE | 11 | 1.5582 | 2.6164 |
| BASELINE | I3 | 2024-07 | AVAILABLE | 8 | 0.8868 | -0.3833 |
| BASELINE | I3 | 2024-08 | AVAILABLE | 9 | 0.1395 | -3.0469 |
| BASELINE | I3 | 2024-09 | AVAILABLE | 8 | 3.8263 | 4.1123 |
| BASELINE | I3 | 2024-10 | AVAILABLE | 8 | 1.7692 | 2.0481 |
| BASELINE | I3 | 2024-11 | AVAILABLE | 12 | 3.8910 | 11.6115 |
| BASELINE | I3 | 2024-12 | AVAILABLE | 11 | 1.2610 | 1.4528 |
| OPTIMIZED | CONTROL | 2023-01 | AVAILABLE | 2 | 0.2019 | -0.7737 |
| OPTIMIZED | CONTROL | 2023-02 | AVAILABLE | 6 | 1.9750 | 2.1791 |
| OPTIMIZED | CONTROL | 2023-03 | AVAILABLE | 7 | 0.0787 | -5.5275 |
| OPTIMIZED | CONTROL | 2023-04 | AVAILABLE | 7 | 10.4543 | 13.6362 |
| OPTIMIZED | CONTROL | 2023-05 | AVAILABLE | 9 | 0.6096 | -2.0606 |
| OPTIMIZED | CONTROL | 2023-06 | AVAILABLE | 5 | 0.4571 | -1.3898 |
| OPTIMIZED | CONTROL | 2023-07 | AVAILABLE | 4 | — | 9.2663 |
| OPTIMIZED | CONTROL | 2023-08 | AVAILABLE | 9 | 0.0120 | -5.4652 |
| OPTIMIZED | CONTROL | 2023-09 | AVAILABLE | 6 | 3.4995 | 4.0366 |
| OPTIMIZED | CONTROL | 2023-10 | AVAILABLE | 11 | 3.8162 | 8.6859 |
| OPTIMIZED | CONTROL | 2023-11 | AVAILABLE | 8 | 2.0714 | 3.3172 |
| OPTIMIZED | CONTROL | 2023-12 | AVAILABLE | 8 | 1.3923 | 1.6416 |
| OPTIMIZED | CONTROL | 2024-01 | AVAILABLE | 10 | 2.0376 | 2.6991 |
| OPTIMIZED | CONTROL | 2024-02 | AVAILABLE | 10 | 0.7798 | -1.2581 |
| OPTIMIZED | CONTROL | 2024-03 | AVAILABLE | 10 | 0.1218 | -5.3427 |
| OPTIMIZED | CONTROL | 2024-04 | AVAILABLE | 8 | 2.1161 | 4.5349 |
| OPTIMIZED | CONTROL | 2024-05 | AVAILABLE | 12 | 0.2954 | -5.1227 |
| OPTIMIZED | CONTROL | 2024-06 | AVAILABLE | 8 | 3.3222 | 10.9638 |
| OPTIMIZED | CONTROL | 2024-07 | AVAILABLE | 7 | 0.7759 | -0.8587 |
| OPTIMIZED | CONTROL | 2024-08 | AVAILABLE | 7 | 1.1819 | 0.7126 |
| OPTIMIZED | CONTROL | 2024-09 | AVAILABLE | 8 | 2.0889 | 2.5291 |
| OPTIMIZED | CONTROL | 2024-10 | AVAILABLE | 8 | 1.2489 | 0.8784 |
| OPTIMIZED | CONTROL | 2024-11 | AVAILABLE | 10 | 4.5384 | 11.8515 |
| OPTIMIZED | CONTROL | 2024-12 | AVAILABLE | 8 | 3.6412 | 8.9668 |
| OPTIMIZED | I1 | 2023-01 | AVAILABLE | 3 | 0.0000 | -0.8246 |
| OPTIMIZED | I1 | 2023-02 | AVAILABLE | 9 | 0.6389 | -1.7384 |
| OPTIMIZED | I1 | 2023-03 | AVAILABLE | 7 | 0.1071 | -3.9410 |
| OPTIMIZED | I1 | 2023-04 | AVAILABLE | 11 | 3.2351 | 7.6629 |
| OPTIMIZED | I1 | 2023-05 | AVAILABLE | 10 | 0.6400 | -1.6079 |
| OPTIMIZED | I1 | 2023-06 | AVAILABLE | 6 | 0.1053 | -2.9541 |
| OPTIMIZED | I1 | 2023-07 | AVAILABLE | 6 | 8.9462 | 6.7679 |
| OPTIMIZED | I1 | 2023-08 | AVAILABLE | 11 | 0.0000 | -7.0305 |
| OPTIMIZED | I1 | 2023-09 | AVAILABLE | 6 | 5.3652 | 5.0831 |
| OPTIMIZED | I1 | 2023-10 | AVAILABLE | 11 | 3.6623 | 7.6857 |
| OPTIMIZED | I1 | 2023-11 | AVAILABLE | 10 | 1.5192 | 2.0389 |
| OPTIMIZED | I1 | 2023-12 | AVAILABLE | 9 | 1.2575 | 1.1413 |
| OPTIMIZED | I1 | 2024-01 | AVAILABLE | 10 | 2.5225 | 3.0123 |
| OPTIMIZED | I1 | 2024-02 | AVAILABLE | 14 | 0.1323 | -5.5384 |
| OPTIMIZED | I1 | 2024-03 | AVAILABLE | 12 | 0.1269 | -5.1008 |
| OPTIMIZED | I1 | 2024-04 | AVAILABLE | 9 | 2.3656 | 4.9196 |
| OPTIMIZED | I1 | 2024-05 | AVAILABLE | 15 | 0.2968 | -4.6312 |
| OPTIMIZED | I1 | 2024-06 | AVAILABLE | 9 | 3.9564 | 11.7207 |
| OPTIMIZED | I1 | 2024-07 | AVAILABLE | 8 | 0.7394 | -0.8858 |
| OPTIMIZED | I1 | 2024-08 | AVAILABLE | 9 | 0.5892 | -1.5201 |
| OPTIMIZED | I1 | 2024-09 | AVAILABLE | 8 | 2.4539 | 2.8746 |
| OPTIMIZED | I1 | 2024-10 | AVAILABLE | 8 | 1.3093 | 1.0415 |
| OPTIMIZED | I1 | 2024-11 | AVAILABLE | 12 | 3.1754 | 9.9977 |
| OPTIMIZED | I1 | 2024-12 | AVAILABLE | 10 | 1.7215 | 3.4010 |
| OPTIMIZED | I2 | 2023-01 | AVAILABLE | 3 | 0.0000 | -0.6602 |
| OPTIMIZED | I2 | 2023-02 | AVAILABLE | 10 | 0.8394 | -0.5507 |
| OPTIMIZED | I2 | 2023-03 | AVAILABLE | 8 | 0.0000 | -3.0016 |
| OPTIMIZED | I2 | 2023-04 | AVAILABLE | 13 | 3.3100 | 6.0627 |
| OPTIMIZED | I2 | 2023-05 | AVAILABLE | 15 | 0.3169 | -2.6452 |
| OPTIMIZED | I2 | 2023-06 | AVAILABLE | 10 | 0.0840 | -3.7905 |
| OPTIMIZED | I2 | 2023-07 | AVAILABLE | 8 | 1.4795 | 1.6555 |
| OPTIMIZED | I2 | 2023-08 | AVAILABLE | 11 | 0.0000 | -4.2888 |
| OPTIMIZED | I2 | 2023-09 | AVAILABLE | 6 | 13.1622 | 5.7729 |
| OPTIMIZED | I2 | 2023-10 | AVAILABLE | 16 | 2.5637 | 4.5418 |
| OPTIMIZED | I2 | 2023-11 | AVAILABLE | 11 | 2.6547 | 3.7185 |
| OPTIMIZED | I2 | 2023-12 | AVAILABLE | 14 | 0.6865 | -0.8511 |
| OPTIMIZED | I2 | 2024-01 | AVAILABLE | 16 | 1.4846 | 0.9559 |
| OPTIMIZED | I2 | 2024-02 | AVAILABLE | 16 | 0.0470 | -3.4736 |
| OPTIMIZED | I2 | 2024-03 | AVAILABLE | 15 | 0.0853 | -3.6793 |
| OPTIMIZED | I2 | 2024-04 | AVAILABLE | 20 | 0.2783 | -4.4681 |
| OPTIMIZED | I2 | 2024-05 | AVAILABLE | 16 | 0.4160 | -2.3035 |
| OPTIMIZED | I2 | 2024-06 | AVAILABLE | 12 | 3.4350 | 6.5392 |
| OPTIMIZED | I2 | 2024-07 | AVAILABLE | 9 | 0.0000 | -2.7383 |
| OPTIMIZED | I2 | 2024-08 | AVAILABLE | 11 | 0.9042 | -0.2310 |
| OPTIMIZED | I2 | 2024-09 | AVAILABLE | 12 | 0.7529 | -0.6068 |
| OPTIMIZED | I2 | 2024-10 | AVAILABLE | 9 | 1.5950 | 1.5170 |
| OPTIMIZED | I2 | 2024-11 | AVAILABLE | 17 | 3.2884 | 9.5857 |
| OPTIMIZED | I2 | 2024-12 | AVAILABLE | 11 | 5.5439 | 6.6508 |
| OPTIMIZED | I3 | 2023-01 | AVAILABLE | 3 | 0.0000 | -0.8246 |
| OPTIMIZED | I3 | 2023-02 | AVAILABLE | 9 | 0.6477 | -1.6730 |
| OPTIMIZED | I3 | 2023-03 | AVAILABLE | 7 | 0.1123 | -3.7339 |
| OPTIMIZED | I3 | 2023-04 | AVAILABLE | 11 | 3.2351 | 7.6629 |
| OPTIMIZED | I3 | 2023-05 | AVAILABLE | 10 | 0.6400 | -1.6079 |
| OPTIMIZED | I3 | 2023-06 | AVAILABLE | 6 | 0.1124 | -2.7457 |
| OPTIMIZED | I3 | 2023-07 | AVAILABLE | 6 | 8.9462 | 6.7679 |
| OPTIMIZED | I3 | 2023-08 | AVAILABLE | 11 | 0.0000 | -7.0305 |
| OPTIMIZED | I3 | 2023-09 | AVAILABLE | 8 | 1.7311 | 1.9915 |
| OPTIMIZED | I3 | 2023-10 | AVAILABLE | 11 | 3.6623 | 7.6857 |
| OPTIMIZED | I3 | 2023-11 | AVAILABLE | 10 | 1.7856 | 2.6247 |
| OPTIMIZED | I3 | 2023-12 | AVAILABLE | 9 | 1.2575 | 1.1413 |
| OPTIMIZED | I3 | 2024-01 | AVAILABLE | 10 | 2.5225 | 3.0123 |
| OPTIMIZED | I3 | 2024-02 | AVAILABLE | 14 | 0.1323 | -5.5384 |
| OPTIMIZED | I3 | 2024-03 | AVAILABLE | 12 | 0.1270 | -5.0934 |
| OPTIMIZED | I3 | 2024-04 | AVAILABLE | 9 | 2.4236 | 5.0059 |
| OPTIMIZED | I3 | 2024-05 | AVAILABLE | 15 | 0.2968 | -4.6312 |
| OPTIMIZED | I3 | 2024-06 | AVAILABLE | 9 | 4.8133 | 12.4265 |
| OPTIMIZED | I3 | 2024-07 | AVAILABLE | 8 | 0.7423 | -0.8722 |
| OPTIMIZED | I3 | 2024-08 | AVAILABLE | 9 | 0.5892 | -1.5201 |
| OPTIMIZED | I3 | 2024-09 | AVAILABLE | 8 | 2.4539 | 2.8746 |
| OPTIMIZED | I3 | 2024-10 | AVAILABLE | 8 | 1.5815 | 1.6209 |
| OPTIMIZED | I3 | 2024-11 | AVAILABLE | 12 | 3.1754 | 9.9977 |
| OPTIMIZED | I3 | 2024-12 | AVAILABLE | 10 | 1.7215 | 3.4010 |

### GLDRUBF / REFERENCE_2ATR

| version | rule | month | coverage | closed_trades | gross_PF | gross_R |
| --- | --- | --- | --- | --- | --- | --- |
| BASELINE | CONTROL | 2023-01 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | CONTROL | 2023-02 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | CONTROL | 2023-03 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | CONTROL | 2023-04 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | CONTROL | 2023-05 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | CONTROL | 2023-06 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | CONTROL | 2023-07 | AVAILABLE | 4 | 0.0601 | -1.8481 |
| BASELINE | CONTROL | 2023-08 | AVAILABLE | 13 | 0.2840 | -4.3327 |
| BASELINE | CONTROL | 2023-09 | AVAILABLE | 7 | 0.5685 | -2.1424 |
| BASELINE | CONTROL | 2023-10 | AVAILABLE | 8 | 0.5405 | -0.8279 |
| BASELINE | CONTROL | 2023-11 | AVAILABLE | 7 | 1.8131 | 2.6422 |
| BASELINE | CONTROL | 2023-12 | AVAILABLE | 12 | 2.2378 | 6.4063 |
| BASELINE | CONTROL | 2024-01 | AVAILABLE | 6 | 0.5475 | -1.2940 |
| BASELINE | CONTROL | 2024-02 | AVAILABLE | 11 | 0.4072 | -3.5200 |
| BASELINE | CONTROL | 2024-03 | AVAILABLE | 13 | 2.0035 | 5.5150 |
| BASELINE | CONTROL | 2024-04 | AVAILABLE | 12 | 2.3743 | 6.4031 |
| BASELINE | CONTROL | 2024-05 | AVAILABLE | 7 | 1.5261 | 1.2444 |
| BASELINE | CONTROL | 2024-06 | AVAILABLE | 12 | 0.0999 | -6.4588 |
| BASELINE | CONTROL | 2024-07 | AVAILABLE | 10 | 2.0945 | 3.4535 |
| BASELINE | CONTROL | 2024-08 | AVAILABLE | 13 | 1.1819 | 1.1723 |
| BASELINE | CONTROL | 2024-09 | AVAILABLE | 7 | 0.0000 | -3.9822 |
| BASELINE | CONTROL | 2024-10 | AVAILABLE | 12 | 1.1558 | 0.7828 |
| BASELINE | CONTROL | 2024-11 | AVAILABLE | 11 | 4.7138 | 13.1694 |
| BASELINE | CONTROL | 2024-12 | AVAILABLE | 13 | 0.2242 | -5.2146 |
| BASELINE | I1 | 2023-01 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | I1 | 2023-02 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | I1 | 2023-03 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | I1 | 2023-04 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | I1 | 2023-05 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | I1 | 2023-06 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | I1 | 2023-07 | AVAILABLE | 5 | 0.0363 | -3.1424 |
| BASELINE | I1 | 2023-08 | AVAILABLE | 13 | 0.3084 | -3.1174 |
| BASELINE | I1 | 2023-09 | AVAILABLE | 6 | 0.9675 | -0.0947 |
| BASELINE | I1 | 2023-10 | AVAILABLE | 11 | 0.1610 | -2.7276 |
| BASELINE | I1 | 2023-11 | AVAILABLE | 7 | 2.4786 | 3.5146 |
| BASELINE | I1 | 2023-12 | AVAILABLE | 14 | 2.2263 | 6.0403 |
| BASELINE | I1 | 2024-01 | AVAILABLE | 6 | 0.7464 | -0.5321 |
| BASELINE | I1 | 2024-02 | AVAILABLE | 15 | 0.0373 | -8.6716 |
| BASELINE | I1 | 2024-03 | AVAILABLE | 15 | 1.3176 | 1.4911 |
| BASELINE | I1 | 2024-04 | AVAILABLE | 14 | 2.1935 | 4.6729 |
| BASELINE | I1 | 2024-05 | AVAILABLE | 7 | 2.1444 | 1.9264 |
| BASELINE | I1 | 2024-06 | AVAILABLE | 12 | 0.1459 | -4.1970 |
| BASELINE | I1 | 2024-07 | AVAILABLE | 13 | 1.5233 | 1.8813 |
| BASELINE | I1 | 2024-08 | AVAILABLE | 13 | 2.0972 | 3.9845 |
| BASELINE | I1 | 2024-09 | AVAILABLE | 9 | 0.0000 | -3.4802 |
| BASELINE | I1 | 2024-10 | AVAILABLE | 13 | 1.1558 | 0.7624 |
| BASELINE | I1 | 2024-11 | AVAILABLE | 12 | 3.6225 | 11.8125 |
| BASELINE | I1 | 2024-12 | AVAILABLE | 16 | 0.2383 | -4.8178 |
| BASELINE | I2 | 2023-01 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | I2 | 2023-02 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | I2 | 2023-03 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | I2 | 2023-04 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | I2 | 2023-05 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | I2 | 2023-06 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | I2 | 2023-07 | AVAILABLE | 9 | 0.0000 | -3.0098 |
| BASELINE | I2 | 2023-08 | AVAILABLE | 16 | 0.1659 | -4.4062 |
| BASELINE | I2 | 2023-09 | AVAILABLE | 7 | 1.2300 | 0.5279 |
| BASELINE | I2 | 2023-10 | AVAILABLE | 19 | 0.1116 | -2.6640 |
| BASELINE | I2 | 2023-11 | AVAILABLE | 8 | 3.2260 | 3.3304 |
| BASELINE | I2 | 2023-12 | AVAILABLE | 19 | 1.9163 | 3.7865 |
| BASELINE | I2 | 2024-01 | AVAILABLE | 6 | 2.2726 | 0.8768 |
| BASELINE | I2 | 2024-02 | AVAILABLE | 15 | 0.1645 | -5.6376 |
| BASELINE | I2 | 2024-03 | AVAILABLE | 21 | 0.8692 | -0.4358 |
| BASELINE | I2 | 2024-04 | AVAILABLE | 21 | 2.1295 | 4.0461 |
| BASELINE | I2 | 2024-05 | AVAILABLE | 9 | 2.4134 | 1.7443 |
| BASELINE | I2 | 2024-06 | AVAILABLE | 12 | 0.1998 | -2.8718 |
| BASELINE | I2 | 2024-07 | AVAILABLE | 19 | 1.2795 | 0.8309 |
| BASELINE | I2 | 2024-08 | AVAILABLE | 15 | 3.8364 | 5.6308 |
| BASELINE | I2 | 2024-09 | AVAILABLE | 9 | 0.0000 | -1.6632 |
| BASELINE | I2 | 2024-10 | AVAILABLE | 21 | 1.1898 | 0.6207 |
| BASELINE | I2 | 2024-11 | AVAILABLE | 19 | 2.4940 | 8.8541 |
| BASELINE | I2 | 2024-12 | AVAILABLE | 20 | 0.8102 | -0.3530 |
| BASELINE | I3 | 2023-01 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | I3 | 2023-02 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | I3 | 2023-03 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | I3 | 2023-04 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | I3 | 2023-05 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | I3 | 2023-06 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | I3 | 2023-07 | AVAILABLE | 5 | 0.0377 | -3.0184 |
| BASELINE | I3 | 2023-08 | AVAILABLE | 13 | 0.3084 | -3.1174 |
| BASELINE | I3 | 2023-09 | AVAILABLE | 6 | 1.0432 | 0.1169 |
| BASELINE | I3 | 2023-10 | AVAILABLE | 11 | 0.1610 | -2.7276 |
| BASELINE | I3 | 2023-11 | AVAILABLE | 7 | 2.4786 | 3.5146 |
| BASELINE | I3 | 2023-12 | AVAILABLE | 14 | 2.4696 | 6.5255 |
| BASELINE | I3 | 2024-01 | AVAILABLE | 6 | 0.7464 | -0.5321 |
| BASELINE | I3 | 2024-02 | AVAILABLE | 15 | 0.0382 | -8.4661 |
| BASELINE | I3 | 2024-03 | AVAILABLE | 17 | 0.8459 | -1.0767 |
| BASELINE | I3 | 2024-04 | AVAILABLE | 14 | 2.2068 | 4.6963 |
| BASELINE | I3 | 2024-05 | AVAILABLE | 7 | 2.1444 | 1.9264 |
| BASELINE | I3 | 2024-06 | AVAILABLE | 12 | 0.1459 | -4.1970 |
| BASELINE | I3 | 2024-07 | AVAILABLE | 13 | 1.5233 | 1.8813 |
| BASELINE | I3 | 2024-08 | AVAILABLE | 13 | 2.1638 | 4.0963 |
| BASELINE | I3 | 2024-09 | AVAILABLE | 9 | 0.0000 | -3.4802 |
| BASELINE | I3 | 2024-10 | AVAILABLE | 13 | 1.1598 | 0.7796 |
| BASELINE | I3 | 2024-11 | AVAILABLE | 12 | 3.6225 | 11.8125 |
| BASELINE | I3 | 2024-12 | AVAILABLE | 16 | 0.2428 | -4.6997 |
| OPTIMIZED | CONTROL | 2023-01 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | CONTROL | 2023-02 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | CONTROL | 2023-03 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | CONTROL | 2023-04 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | CONTROL | 2023-05 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | CONTROL | 2023-06 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | CONTROL | 2023-07 | AVAILABLE | 3 | 0.0000 | -2.3362 |
| OPTIMIZED | CONTROL | 2023-08 | AVAILABLE | 14 | 0.2813 | -5.2065 |
| OPTIMIZED | CONTROL | 2023-09 | AVAILABLE | 6 | 1.0990 | 0.4781 |
| OPTIMIZED | CONTROL | 2023-10 | AVAILABLE | 8 | 0.1734 | -2.0774 |
| OPTIMIZED | CONTROL | 2023-11 | AVAILABLE | 7 | 1.4524 | 1.7044 |
| OPTIMIZED | CONTROL | 2023-12 | AVAILABLE | 11 | 2.5168 | 8.1967 |
| OPTIMIZED | CONTROL | 2024-01 | AVAILABLE | 6 | 0.5654 | -1.4163 |
| OPTIMIZED | CONTROL | 2024-02 | AVAILABLE | 10 | 0.3876 | -3.4272 |
| OPTIMIZED | CONTROL | 2024-03 | AVAILABLE | 13 | 1.9345 | 5.2989 |
| OPTIMIZED | CONTROL | 2024-04 | AVAILABLE | 12 | 1.8007 | 4.4069 |
| OPTIMIZED | CONTROL | 2024-05 | AVAILABLE | 7 | 1.1614 | 0.4489 |
| OPTIMIZED | CONTROL | 2024-06 | AVAILABLE | 12 | 0.3308 | -4.9243 |
| OPTIMIZED | CONTROL | 2024-07 | AVAILABLE | 10 | 1.7385 | 2.5091 |
| OPTIMIZED | CONTROL | 2024-08 | AVAILABLE | 11 | 1.3796 | 1.8695 |
| OPTIMIZED | CONTROL | 2024-09 | AVAILABLE | 6 | 0.1937 | -2.8897 |
| OPTIMIZED | CONTROL | 2024-10 | AVAILABLE | 12 | 0.8216 | -1.0763 |
| OPTIMIZED | CONTROL | 2024-11 | AVAILABLE | 7 | 42.2009 | 22.4126 |
| OPTIMIZED | CONTROL | 2024-12 | AVAILABLE | 11 | 0.6533 | -2.6554 |
| OPTIMIZED | I1 | 2023-01 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | I1 | 2023-02 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | I1 | 2023-03 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | I1 | 2023-04 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | I1 | 2023-05 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | I1 | 2023-06 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | I1 | 2023-07 | AVAILABLE | 4 | 0.0000 | -3.4211 |
| OPTIMIZED | I1 | 2023-08 | AVAILABLE | 14 | 0.3674 | -3.2281 |
| OPTIMIZED | I1 | 2023-09 | AVAILABLE | 6 | 1.6722 | 2.1325 |
| OPTIMIZED | I1 | 2023-10 | AVAILABLE | 11 | 0.0275 | -3.5745 |
| OPTIMIZED | I1 | 2023-11 | AVAILABLE | 7 | 1.9303 | 2.6371 |
| OPTIMIZED | I1 | 2023-12 | AVAILABLE | 13 | 2.7444 | 8.2497 |
| OPTIMIZED | I1 | 2024-01 | AVAILABLE | 6 | 0.8197 | -0.4053 |
| OPTIMIZED | I1 | 2024-02 | AVAILABLE | 14 | 0.0134 | -8.2479 |
| OPTIMIZED | I1 | 2024-03 | AVAILABLE | 15 | 1.2088 | 1.0362 |
| OPTIMIZED | I1 | 2024-04 | AVAILABLE | 14 | 1.8125 | 3.3607 |
| OPTIMIZED | I1 | 2024-05 | AVAILABLE | 7 | 1.5507 | 1.1471 |
| OPTIMIZED | I1 | 2024-06 | AVAILABLE | 12 | 0.4939 | -2.4945 |
| OPTIMIZED | I1 | 2024-07 | AVAILABLE | 13 | 1.2472 | 0.9898 |
| OPTIMIZED | I1 | 2024-08 | AVAILABLE | 11 | 2.6421 | 4.2232 |
| OPTIMIZED | I1 | 2024-09 | AVAILABLE | 8 | 0.2685 | -1.8911 |
| OPTIMIZED | I1 | 2024-10 | AVAILABLE | 13 | 0.9545 | -0.2363 |
| OPTIMIZED | I1 | 2024-11 | AVAILABLE | 8 | 16.7289 | 21.4097 |
| OPTIMIZED | I1 | 2024-12 | AVAILABLE | 14 | 0.8019 | -1.2361 |
| OPTIMIZED | I2 | 2023-01 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | I2 | 2023-02 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | I2 | 2023-03 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | I2 | 2023-04 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | I2 | 2023-05 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | I2 | 2023-06 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | I2 | 2023-07 | AVAILABLE | 9 | 0.0000 | -3.0098 |
| OPTIMIZED | I2 | 2023-08 | AVAILABLE | 16 | 0.2860 | -3.7718 |
| OPTIMIZED | I2 | 2023-09 | AVAILABLE | 6 | 2.5512 | 3.2255 |
| OPTIMIZED | I2 | 2023-10 | AVAILABLE | 19 | 0.0295 | -2.9101 |
| OPTIMIZED | I2 | 2023-11 | AVAILABLE | 8 | 2.4603 | 2.6269 |
| OPTIMIZED | I2 | 2023-12 | AVAILABLE | 15 | 3.2574 | 7.9024 |
| OPTIMIZED | I2 | 2024-01 | AVAILABLE | 6 | 2.3632 | 1.0630 |
| OPTIMIZED | I2 | 2024-02 | AVAILABLE | 15 | 0.1308 | -5.8853 |
| OPTIMIZED | I2 | 2024-03 | AVAILABLE | 21 | 0.8010 | -0.7322 |
| OPTIMIZED | I2 | 2024-04 | AVAILABLE | 21 | 1.9000 | 3.2241 |
| OPTIMIZED | I2 | 2024-05 | AVAILABLE | 9 | 1.9582 | 1.3531 |
| OPTIMIZED | I2 | 2024-06 | AVAILABLE | 12 | 0.6915 | -1.0863 |
| OPTIMIZED | I2 | 2024-07 | AVAILABLE | 19 | 1.1127 | 0.3630 |
| OPTIMIZED | I2 | 2024-08 | AVAILABLE | 13 | 3.7233 | 4.9700 |
| OPTIMIZED | I2 | 2024-09 | AVAILABLE | 9 | 0.0000 | -1.6632 |
| OPTIMIZED | I2 | 2024-10 | AVAILABLE | 21 | 1.0621 | 0.2049 |
| OPTIMIZED | I2 | 2024-11 | AVAILABLE | 14 | 9.1803 | 18.9286 |
| OPTIMIZED | I2 | 2024-12 | AVAILABLE | 19 | 1.9931 | 2.0517 |
| OPTIMIZED | I3 | 2023-01 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | I3 | 2023-02 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | I3 | 2023-03 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | I3 | 2023-04 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | I3 | 2023-05 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | I3 | 2023-06 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | I3 | 2023-07 | AVAILABLE | 4 | 0.0000 | -3.2971 |
| OPTIMIZED | I3 | 2023-08 | AVAILABLE | 14 | 0.3674 | -3.2281 |
| OPTIMIZED | I3 | 2023-09 | AVAILABLE | 6 | 1.8912 | 2.4999 |
| OPTIMIZED | I3 | 2023-10 | AVAILABLE | 11 | 0.0275 | -3.5745 |
| OPTIMIZED | I3 | 2023-11 | AVAILABLE | 7 | 1.9303 | 2.6371 |
| OPTIMIZED | I3 | 2023-12 | AVAILABLE | 13 | 3.0587 | 8.7357 |
| OPTIMIZED | I3 | 2024-01 | AVAILABLE | 6 | 0.8197 | -0.4053 |
| OPTIMIZED | I3 | 2024-02 | AVAILABLE | 14 | 0.0142 | -7.7786 |
| OPTIMIZED | I3 | 2024-03 | AVAILABLE | 17 | 0.8231 | -1.2613 |
| OPTIMIZED | I3 | 2024-04 | AVAILABLE | 14 | 1.8229 | 3.3842 |
| OPTIMIZED | I3 | 2024-05 | AVAILABLE | 7 | 1.5507 | 1.1471 |
| OPTIMIZED | I3 | 2024-06 | AVAILABLE | 12 | 0.4939 | -2.4945 |
| OPTIMIZED | I3 | 2024-07 | AVAILABLE | 13 | 1.2472 | 0.9898 |
| OPTIMIZED | I3 | 2024-08 | AVAILABLE | 11 | 2.6421 | 4.2232 |
| OPTIMIZED | I3 | 2024-09 | AVAILABLE | 8 | 0.2685 | -1.8911 |
| OPTIMIZED | I3 | 2024-10 | AVAILABLE | 13 | 0.9577 | -0.2191 |
| OPTIMIZED | I3 | 2024-11 | AVAILABLE | 8 | 16.7289 | 21.4097 |
| OPTIMIZED | I3 | 2024-12 | AVAILABLE | 14 | 0.8240 | -1.0687 |

### IMOEXF / REFERENCE_2ATR

| version | rule | month | coverage | closed_trades | gross_PF | gross_R |
| --- | --- | --- | --- | --- | --- | --- |
| BASELINE | CONTROL | 2023-01 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | CONTROL | 2023-02 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | CONTROL | 2023-03 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | CONTROL | 2023-04 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | CONTROL | 2023-05 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | CONTROL | 2023-06 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | CONTROL | 2023-07 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | CONTROL | 2023-08 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | CONTROL | 2023-09 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | CONTROL | 2023-10 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | CONTROL | 2023-11 | AVAILABLE | 1 | 0.0000 | -1.0000 |
| BASELINE | CONTROL | 2023-12 | AVAILABLE | 8 | 1.5182 | 1.2796 |
| BASELINE | CONTROL | 2024-01 | AVAILABLE | 10 | 0.5194 | -3.1777 |
| BASELINE | CONTROL | 2024-02 | AVAILABLE | 9 | 3.3744 | 5.8495 |
| BASELINE | CONTROL | 2024-03 | AVAILABLE | 8 | 1.1172 | 0.4058 |
| BASELINE | CONTROL | 2024-04 | AVAILABLE | 17 | 0.3819 | -5.1320 |
| BASELINE | CONTROL | 2024-05 | AVAILABLE | 12 | 1.1105 | 0.4020 |
| BASELINE | CONTROL | 2024-06 | AVAILABLE | 11 | 1.2127 | 0.8574 |
| BASELINE | CONTROL | 2024-07 | AVAILABLE | 11 | 1.7772 | 4.1880 |
| BASELINE | CONTROL | 2024-08 | AVAILABLE | 12 | 0.6756 | -1.9614 |
| BASELINE | CONTROL | 2024-09 | AVAILABLE | 11 | 1.4746 | 1.9699 |
| BASELINE | CONTROL | 2024-10 | AVAILABLE | 9 | 0.8283 | -0.7367 |
| BASELINE | CONTROL | 2024-11 | AVAILABLE | 11 | 3.3848 | 11.6619 |
| BASELINE | CONTROL | 2024-12 | AVAILABLE | 8 | 2.6485 | 4.8470 |
| BASELINE | I1 | 2023-01 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | I1 | 2023-02 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | I1 | 2023-03 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | I1 | 2023-04 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | I1 | 2023-05 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | I1 | 2023-06 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | I1 | 2023-07 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | I1 | 2023-08 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | I1 | 2023-09 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | I1 | 2023-10 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | I1 | 2023-11 | AVAILABLE | 1 | 0.0000 | -0.5118 |
| BASELINE | I1 | 2023-12 | AVAILABLE | 10 | 1.4531 | 1.0245 |
| BASELINE | I1 | 2024-01 | AVAILABLE | 11 | 0.5107 | -3.1961 |
| BASELINE | I1 | 2024-02 | AVAILABLE | 12 | 1.5537 | 2.4180 |
| BASELINE | I1 | 2024-03 | AVAILABLE | 11 | 0.7891 | -0.9322 |
| BASELINE | I1 | 2024-04 | AVAILABLE | 18 | 0.4201 | -4.3768 |
| BASELINE | I1 | 2024-05 | AVAILABLE | 20 | 0.2387 | -6.1628 |
| BASELINE | I1 | 2024-06 | AVAILABLE | 15 | 0.4212 | -4.2892 |
| BASELINE | I1 | 2024-07 | AVAILABLE | 11 | 3.1584 | 5.5674 |
| BASELINE | I1 | 2024-08 | AVAILABLE | 18 | 0.3966 | -3.5745 |
| BASELINE | I1 | 2024-09 | AVAILABLE | 12 | 1.5271 | 1.8190 |
| BASELINE | I1 | 2024-10 | AVAILABLE | 10 | 0.6547 | -1.4135 |
| BASELINE | I1 | 2024-11 | AVAILABLE | 13 | 1.8108 | 4.0313 |
| BASELINE | I1 | 2024-12 | AVAILABLE | 9 | 2.8859 | 5.0888 |
| BASELINE | I2 | 2023-01 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | I2 | 2023-02 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | I2 | 2023-03 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | I2 | 2023-04 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | I2 | 2023-05 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | I2 | 2023-06 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | I2 | 2023-07 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | I2 | 2023-08 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | I2 | 2023-09 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | I2 | 2023-10 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | I2 | 2023-11 | AVAILABLE | 1 | 0.0000 | -0.3937 |
| BASELINE | I2 | 2023-12 | AVAILABLE | 11 | 2.4016 | 1.6958 |
| BASELINE | I2 | 2024-01 | AVAILABLE | 12 | 0.7399 | -1.1110 |
| BASELINE | I2 | 2024-02 | AVAILABLE | 14 | 2.3944 | 3.9511 |
| BASELINE | I2 | 2024-03 | AVAILABLE | 14 | 0.5872 | -1.4340 |
| BASELINE | I2 | 2024-04 | AVAILABLE | 20 | 0.5112 | -2.0377 |
| BASELINE | I2 | 2024-05 | AVAILABLE | 24 | 0.3442 | -3.6808 |
| BASELINE | I2 | 2024-06 | AVAILABLE | 18 | 0.5344 | -2.5047 |
| BASELINE | I2 | 2024-07 | AVAILABLE | 17 | 1.9967 | 2.8025 |
| BASELINE | I2 | 2024-08 | AVAILABLE | 23 | 0.4993 | -1.8510 |
| BASELINE | I2 | 2024-09 | AVAILABLE | 17 | 1.7442 | 2.0832 |
| BASELINE | I2 | 2024-10 | AVAILABLE | 15 | 0.5979 | -0.9829 |
| BASELINE | I2 | 2024-11 | AVAILABLE | 15 | 2.3752 | 4.7939 |
| BASELINE | I2 | 2024-12 | AVAILABLE | 17 | 2.5646 | 4.2471 |
| BASELINE | I3 | 2023-01 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | I3 | 2023-02 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | I3 | 2023-03 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | I3 | 2023-04 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | I3 | 2023-05 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | I3 | 2023-06 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | I3 | 2023-07 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | I3 | 2023-08 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | I3 | 2023-09 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | I3 | 2023-10 | NO_COVERAGE | 0 | — | 0.0000 |
| BASELINE | I3 | 2023-11 | AVAILABLE | 1 | 0.0000 | -0.5118 |
| BASELINE | I3 | 2023-12 | AVAILABLE | 10 | 1.4531 | 1.0245 |
| BASELINE | I3 | 2024-01 | AVAILABLE | 11 | 0.5651 | -2.5668 |
| BASELINE | I3 | 2024-02 | AVAILABLE | 12 | 1.6839 | 2.7555 |
| BASELINE | I3 | 2024-03 | AVAILABLE | 11 | 0.7891 | -0.9322 |
| BASELINE | I3 | 2024-04 | AVAILABLE | 18 | 0.4311 | -4.1842 |
| BASELINE | I3 | 2024-05 | AVAILABLE | 20 | 0.2387 | -6.1628 |
| BASELINE | I3 | 2024-06 | AVAILABLE | 15 | 0.4540 | -3.7538 |
| BASELINE | I3 | 2024-07 | AVAILABLE | 12 | 1.9586 | 3.9873 |
| BASELINE | I3 | 2024-08 | AVAILABLE | 18 | 0.3966 | -3.5745 |
| BASELINE | I3 | 2024-09 | AVAILABLE | 12 | 1.5271 | 1.8190 |
| BASELINE | I3 | 2024-10 | AVAILABLE | 10 | 0.6690 | -1.3257 |
| BASELINE | I3 | 2024-11 | AVAILABLE | 13 | 1.8108 | 4.0313 |
| BASELINE | I3 | 2024-12 | AVAILABLE | 9 | 2.8859 | 5.0888 |
| OPTIMIZED | CONTROL | 2023-01 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | CONTROL | 2023-02 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | CONTROL | 2023-03 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | CONTROL | 2023-04 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | CONTROL | 2023-05 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | CONTROL | 2023-06 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | CONTROL | 2023-07 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | CONTROL | 2023-08 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | CONTROL | 2023-09 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | CONTROL | 2023-10 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | CONTROL | 2023-11 | AVAILABLE | 1 | 0.0000 | -1.0000 |
| OPTIMIZED | CONTROL | 2023-12 | AVAILABLE | 8 | 1.2309 | 0.6560 |
| OPTIMIZED | CONTROL | 2024-01 | AVAILABLE | 10 | 0.8173 | -1.2496 |
| OPTIMIZED | CONTROL | 2024-02 | AVAILABLE | 9 | 2.8741 | 5.4850 |
| OPTIMIZED | CONTROL | 2024-03 | AVAILABLE | 7 | 2.1966 | 4.4889 |
| OPTIMIZED | CONTROL | 2024-04 | AVAILABLE | 17 | 0.3330 | -5.7034 |
| OPTIMIZED | CONTROL | 2024-05 | AVAILABLE | 11 | 1.9051 | 3.3915 |
| OPTIMIZED | CONTROL | 2024-06 | AVAILABLE | 11 | 0.8721 | -0.5830 |
| OPTIMIZED | CONTROL | 2024-07 | AVAILABLE | 10 | 2.2218 | 5.5067 |
| OPTIMIZED | CONTROL | 2024-08 | AVAILABLE | 12 | 0.5630 | -2.7524 |
| OPTIMIZED | CONTROL | 2024-09 | AVAILABLE | 10 | 1.5487 | 2.5377 |
| OPTIMIZED | CONTROL | 2024-10 | AVAILABLE | 9 | 0.7172 | -1.2517 |
| OPTIMIZED | CONTROL | 2024-11 | AVAILABLE | 11 | 3.0106 | 10.0324 |
| OPTIMIZED | CONTROL | 2024-12 | AVAILABLE | 8 | 2.1354 | 3.9261 |
| OPTIMIZED | I1 | 2023-01 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | I1 | 2023-02 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | I1 | 2023-03 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | I1 | 2023-04 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | I1 | 2023-05 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | I1 | 2023-06 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | I1 | 2023-07 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | I1 | 2023-08 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | I1 | 2023-09 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | I1 | 2023-10 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | I1 | 2023-11 | AVAILABLE | 1 | 0.0000 | -0.5118 |
| OPTIMIZED | I1 | 2023-12 | AVAILABLE | 10 | 1.2612 | 0.6405 |
| OPTIMIZED | I1 | 2024-01 | AVAILABLE | 11 | 0.4945 | -3.4061 |
| OPTIMIZED | I1 | 2024-02 | AVAILABLE | 12 | 1.5699 | 2.5405 |
| OPTIMIZED | I1 | 2024-03 | AVAILABLE | 10 | 1.8709 | 3.4561 |
| OPTIMIZED | I1 | 2024-04 | AVAILABLE | 18 | 0.3532 | -4.9017 |
| OPTIMIZED | I1 | 2024-05 | AVAILABLE | 20 | 0.2415 | -6.5028 |
| OPTIMIZED | I1 | 2024-06 | AVAILABLE | 15 | 0.3183 | -5.3584 |
| OPTIMIZED | I1 | 2024-07 | AVAILABLE | 10 | 3.7595 | 6.3100 |
| OPTIMIZED | I1 | 2024-08 | AVAILABLE | 18 | 0.3185 | -4.2250 |
| OPTIMIZED | I1 | 2024-09 | AVAILABLE | 10 | 1.9285 | 3.0848 |
| OPTIMIZED | I1 | 2024-10 | AVAILABLE | 10 | 0.6065 | -1.6229 |
| OPTIMIZED | I1 | 2024-11 | AVAILABLE | 13 | 1.6059 | 3.0194 |
| OPTIMIZED | I1 | 2024-12 | AVAILABLE | 9 | 2.4686 | 4.3927 |
| OPTIMIZED | I2 | 2023-01 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | I2 | 2023-02 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | I2 | 2023-03 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | I2 | 2023-04 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | I2 | 2023-05 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | I2 | 2023-06 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | I2 | 2023-07 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | I2 | 2023-08 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | I2 | 2023-09 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | I2 | 2023-10 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | I2 | 2023-11 | AVAILABLE | 1 | 0.0000 | -0.3937 |
| OPTIMIZED | I2 | 2023-12 | AVAILABLE | 11 | 2.3381 | 1.6010 |
| OPTIMIZED | I2 | 2024-01 | AVAILABLE | 12 | 0.7431 | -1.0975 |
| OPTIMIZED | I2 | 2024-02 | AVAILABLE | 14 | 2.1100 | 3.3104 |
| OPTIMIZED | I2 | 2024-03 | AVAILABLE | 11 | 2.2397 | 3.3499 |
| OPTIMIZED | I2 | 2024-04 | AVAILABLE | 20 | 0.3929 | -2.5309 |
| OPTIMIZED | I2 | 2024-05 | AVAILABLE | 24 | 0.3511 | -3.8266 |
| OPTIMIZED | I2 | 2024-06 | AVAILABLE | 18 | 0.4421 | -3.0034 |
| OPTIMIZED | I2 | 2024-07 | AVAILABLE | 16 | 2.2862 | 3.3404 |
| OPTIMIZED | I2 | 2024-08 | AVAILABLE | 23 | 0.4234 | -2.2188 |
| OPTIMIZED | I2 | 2024-09 | AVAILABLE | 15 | 2.4572 | 3.7392 |
| OPTIMIZED | I2 | 2024-10 | AVAILABLE | 15 | 0.5406 | -1.1229 |
| OPTIMIZED | I2 | 2024-11 | AVAILABLE | 15 | 1.9394 | 3.5319 |
| OPTIMIZED | I2 | 2024-12 | AVAILABLE | 17 | 2.3467 | 3.8746 |
| OPTIMIZED | I3 | 2023-01 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | I3 | 2023-02 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | I3 | 2023-03 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | I3 | 2023-04 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | I3 | 2023-05 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | I3 | 2023-06 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | I3 | 2023-07 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | I3 | 2023-08 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | I3 | 2023-09 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | I3 | 2023-10 | NO_COVERAGE | 0 | — | 0.0000 |
| OPTIMIZED | I3 | 2023-11 | AVAILABLE | 1 | 0.0000 | -0.5118 |
| OPTIMIZED | I3 | 2023-12 | AVAILABLE | 10 | 1.2612 | 0.6405 |
| OPTIMIZED | I3 | 2024-01 | AVAILABLE | 11 | 0.5645 | -2.5703 |
| OPTIMIZED | I3 | 2024-02 | AVAILABLE | 12 | 1.6985 | 2.8780 |
| OPTIMIZED | I3 | 2024-03 | AVAILABLE | 10 | 1.8709 | 3.4561 |
| OPTIMIZED | I3 | 2024-04 | AVAILABLE | 18 | 0.3624 | -4.7091 |
| OPTIMIZED | I3 | 2024-05 | AVAILABLE | 20 | 0.2415 | -6.5028 |
| OPTIMIZED | I3 | 2024-06 | AVAILABLE | 15 | 0.3549 | -4.5481 |
| OPTIMIZED | I3 | 2024-07 | AVAILABLE | 11 | 2.4376 | 5.0700 |
| OPTIMIZED | I3 | 2024-08 | AVAILABLE | 18 | 0.3185 | -4.2250 |
| OPTIMIZED | I3 | 2024-09 | AVAILABLE | 10 | 1.9285 | 3.0848 |
| OPTIMIZED | I3 | 2024-10 | AVAILABLE | 10 | 0.6196 | -1.5351 |
| OPTIMIZED | I3 | 2024-11 | AVAILABLE | 13 | 1.6059 | 3.0194 |
| OPTIMIZED | I3 | 2024-12 | AVAILABLE | 9 | 2.4686 | 4.3927 |

## Каждый инструмент и LONG/SHORT

| version | rule | scope | normalization | closed_trades | open_positions_at_period_end | gross_PF | gross_R | expectancy_R | max_drawdown_closed_R | positive_months | negative_months | zero_months |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BASELINE | CONTROL | USDRUBF | ACTUAL_INITIAL_RISK | 226 | 0 | 1.7440 | 68.7570 | 0.3042 | 14.9600 | 16 | 8 | 0 |
| BASELINE | CONTROL | USDRUBF | REFERENCE_2ATR | 226 | 0 | 1.7440 | 68.7570 | 0.3042 | 14.9600 | 16 | 8 | 0 |
| BASELINE | CONTROL | CNYRUBF | ACTUAL_INITIAL_RISK | 199 | 0 | 1.5279 | 45.0322 | 0.2263 | 17.6552 | 14 | 10 | 0 |
| BASELINE | CONTROL | CNYRUBF | REFERENCE_2ATR | 199 | 0 | 1.5279 | 45.0322 | 0.2263 | 17.6552 | 14 | 10 | 0 |
| BASELINE | CONTROL | GLDRUBF | ACTUAL_INITIAL_RISK | 178 | 0 | 1.1386 | 11.1684 | 0.0627 | 10.3931 | 9 | 9 | 6 |
| BASELINE | CONTROL | GLDRUBF | REFERENCE_2ATR | 178 | 0 | 1.1386 | 11.1684 | 0.0627 | 10.3931 | 9 | 9 | 6 |
| BASELINE | CONTROL | IMOEXF | ACTUAL_INITIAL_RISK | 138 | 1 | 1.3259 | 19.4536 | 0.1410 | 9.4402 | 9 | 5 | 10 |
| BASELINE | CONTROL | IMOEXF | REFERENCE_2ATR | 138 | 1 | 1.3259 | 19.4536 | 0.1410 | 9.4402 | 9 | 5 | 10 |
| BASELINE | I1 | USDRUBF | ACTUAL_INITIAL_RISK | 248 | 0 | 1.4813 | 71.7733 | 0.2894 | 38.3585 | 15 | 9 | 0 |
| BASELINE | I1 | USDRUBF | REFERENCE_2ATR | 248 | 0 | 1.6093 | 53.9168 | 0.2174 | 17.7715 | 15 | 9 | 0 |
| BASELINE | I1 | CNYRUBF | ACTUAL_INITIAL_RISK | 228 | 0 | 1.3037 | 44.6473 | 0.1958 | 31.6638 | 13 | 11 | 0 |
| BASELINE | I1 | CNYRUBF | REFERENCE_2ATR | 228 | 0 | 1.3420 | 30.4388 | 0.1335 | 17.0703 | 13 | 11 | 0 |
| BASELINE | I1 | GLDRUBF | ACTUAL_INITIAL_RISK | 201 | 0 | 0.9288 | -9.7203 | -0.0484 | 28.8991 | 7 | 11 | 6 |
| BASELINE | I1 | GLDRUBF | REFERENCE_2ATR | 201 | 0 | 1.0717 | 5.3051 | 0.0264 | 14.3457 | 9 | 9 | 6 |
| BASELINE | I1 | IMOEXF | ACTUAL_INITIAL_RISK | 171 | 1 | 1.2082 | 24.0178 | 0.1405 | 30.2045 | 7 | 7 | 10 |
| BASELINE | I1 | IMOEXF | REFERENCE_2ATR | 171 | 1 | 0.9305 | -4.5081 | -0.0264 | 20.3787 | 6 | 8 | 10 |
| BASELINE | I2 | USDRUBF | ACTUAL_INITIAL_RISK | 326 | 0 | 1.5314 | 144.3309 | 0.4427 | 51.6954 | 14 | 10 | 0 |
| BASELINE | I2 | USDRUBF | REFERENCE_2ATR | 326 | 0 | 1.6147 | 41.3258 | 0.1268 | 14.6654 | 15 | 9 | 0 |
| BASELINE | I2 | CNYRUBF | ACTUAL_INITIAL_RISK | 291 | 0 | 1.0917 | 22.9586 | 0.0789 | 88.8361 | 9 | 15 | 0 |
| BASELINE | I2 | CNYRUBF | REFERENCE_2ATR | 291 | 0 | 1.2350 | 16.6625 | 0.0573 | 16.8056 | 10 | 14 | 0 |
| BASELINE | I2 | GLDRUBF | ACTUAL_INITIAL_RISK | 265 | 0 | 1.2168 | 66.2836 | 0.2501 | 127.1803 | 8 | 10 | 6 |
| BASELINE | I2 | GLDRUBF | REFERENCE_2ATR | 265 | 0 | 1.1642 | 9.2071 | 0.0347 | 10.7447 | 10 | 8 | 6 |
| BASELINE | I2 | IMOEXF | ACTUAL_INITIAL_RISK | 218 | 1 | 1.4680 | 101.8139 | 0.4670 | 45.7121 | 6 | 8 | 10 |
| BASELINE | I2 | IMOEXF | REFERENCE_2ATR | 218 | 1 | 1.1231 | 5.5777 | 0.0256 | 12.9462 | 6 | 8 | 10 |
| BASELINE | I3 | USDRUBF | ACTUAL_INITIAL_RISK | 248 | 0 | 1.5147 | 78.2026 | 0.3153 | 36.6076 | 15 | 9 | 0 |
| BASELINE | I3 | USDRUBF | REFERENCE_2ATR | 248 | 0 | 1.6350 | 55.3098 | 0.2230 | 17.5261 | 15 | 9 | 0 |
| BASELINE | I3 | CNYRUBF | ACTUAL_INITIAL_RISK | 230 | 0 | 1.2839 | 42.9982 | 0.1869 | 31.2524 | 13 | 11 | 0 |
| BASELINE | I3 | CNYRUBF | REFERENCE_2ATR | 230 | 0 | 1.3288 | 29.1973 | 0.1269 | 16.2874 | 13 | 11 | 0 |
| BASELINE | I3 | GLDRUBF | ACTUAL_INITIAL_RISK | 203 | 0 | 0.9112 | -12.5856 | -0.0620 | 31.8810 | 6 | 12 | 6 |
| BASELINE | I3 | GLDRUBF | REFERENCE_2ATR | 203 | 0 | 1.0538 | 4.0343 | 0.0199 | 16.1002 | 9 | 9 | 6 |
| BASELINE | I3 | IMOEXF | ACTUAL_INITIAL_RISK | 172 | 1 | 1.2085 | 24.5250 | 0.1426 | 31.8926 | 7 | 7 | 10 |
| BASELINE | I3 | IMOEXF | REFERENCE_2ATR | 172 | 1 | 0.9334 | -4.3056 | -0.0250 | 20.2640 | 6 | 8 | 10 |
| OPTIMIZED | CONTROL | USDRUBF | ACTUAL_INITIAL_RISK | 213 | 0 | 1.7939 | 75.8196 | 0.3560 | 17.5358 | 14 | 10 | 0 |
| OPTIMIZED | CONTROL | USDRUBF | REFERENCE_2ATR | 213 | 0 | 1.7939 | 75.8196 | 0.3560 | 17.5358 | 14 | 10 | 0 |
| OPTIMIZED | CONTROL | CNYRUBF | ACTUAL_INITIAL_RISK | 188 | 0 | 1.6694 | 58.1002 | 0.3090 | 14.1599 | 15 | 9 | 0 |
| OPTIMIZED | CONTROL | CNYRUBF | REFERENCE_2ATR | 188 | 0 | 1.6694 | 58.1002 | 0.3090 | 14.1599 | 15 | 9 | 0 |
| OPTIMIZED | CONTROL | GLDRUBF | ACTUAL_INITIAL_RISK | 166 | 0 | 1.2587 | 21.3159 | 0.1284 | 11.1124 | 9 | 9 | 6 |
| OPTIMIZED | CONTROL | GLDRUBF | REFERENCE_2ATR | 166 | 0 | 1.2587 | 21.3159 | 0.1284 | 11.1124 | 9 | 9 | 6 |
| OPTIMIZED | CONTROL | IMOEXF | ACTUAL_INITIAL_RISK | 134 | 1 | 1.3756 | 23.4842 | 0.1753 | 9.4715 | 8 | 6 | 10 |
| OPTIMIZED | CONTROL | IMOEXF | REFERENCE_2ATR | 134 | 1 | 1.3756 | 23.4842 | 0.1753 | 9.4715 | 8 | 6 | 10 |
| OPTIMIZED | I1 | USDRUBF | ACTUAL_INITIAL_RISK | 239 | 0 | 1.6349 | 97.7961 | 0.4092 | 42.5199 | 13 | 11 | 0 |
| OPTIMIZED | I1 | USDRUBF | REFERENCE_2ATR | 239 | 0 | 1.6572 | 60.7263 | 0.2541 | 20.3963 | 15 | 9 | 0 |
| OPTIMIZED | I1 | CNYRUBF | ACTUAL_INITIAL_RISK | 223 | 0 | 1.2886 | 43.6565 | 0.1958 | 28.5720 | 14 | 10 | 0 |
| OPTIMIZED | I1 | CNYRUBF | REFERENCE_2ATR | 223 | 0 | 1.3445 | 31.5743 | 0.1416 | 15.1599 | 13 | 11 | 0 |
| OPTIMIZED | I1 | GLDRUBF | ACTUAL_INITIAL_RISK | 190 | 0 | 1.2164 | 29.1888 | 0.1536 | 34.2029 | 7 | 11 | 6 |
| OPTIMIZED | I1 | GLDRUBF | REFERENCE_2ATR | 190 | 0 | 1.2856 | 20.4510 | 0.1076 | 14.4571 | 9 | 9 | 6 |
| OPTIMIZED | I1 | IMOEXF | ACTUAL_INITIAL_RISK | 167 | 1 | 1.2529 | 29.0055 | 0.1737 | 28.3621 | 7 | 7 | 10 |
| OPTIMIZED | I1 | IMOEXF | REFERENCE_2ATR | 167 | 1 | 0.9533 | -3.0846 | -0.0185 | 19.7842 | 7 | 7 | 10 |
| OPTIMIZED | I2 | USDRUBF | ACTUAL_INITIAL_RISK | 321 | 0 | 1.4320 | 117.7364 | 0.3668 | 55.1082 | 12 | 12 | 0 |
| OPTIMIZED | I2 | USDRUBF | REFERENCE_2ATR | 321 | 0 | 1.5911 | 40.6646 | 0.1267 | 14.7039 | 14 | 10 | 0 |
| OPTIMIZED | I2 | CNYRUBF | ACTUAL_INITIAL_RISK | 289 | 0 | 1.0034 | 0.8708 | 0.0030 | 84.7438 | 9 | 15 | 0 |
| OPTIMIZED | I2 | CNYRUBF | REFERENCE_2ATR | 289 | 0 | 1.1902 | 13.7111 | 0.0474 | 16.7135 | 10 | 14 | 0 |
| OPTIMIZED | I2 | GLDRUBF | ACTUAL_INITIAL_RISK | 252 | 0 | 1.2030 | 59.0023 | 0.2341 | 107.6090 | 7 | 11 | 6 |
| OPTIMIZED | I2 | GLDRUBF | REFERENCE_2ATR | 252 | 0 | 1.5086 | 26.8546 | 0.1066 | 11.1027 | 11 | 7 | 6 |
| OPTIMIZED | I2 | IMOEXF | ACTUAL_INITIAL_RISK | 212 | 1 | 1.5658 | 116.5185 | 0.5496 | 39.2094 | 7 | 7 | 10 |
| OPTIMIZED | I2 | IMOEXF | REFERENCE_2ATR | 212 | 1 | 1.1897 | 8.5536 | 0.0403 | 12.3355 | 7 | 7 | 10 |
| OPTIMIZED | I3 | USDRUBF | ACTUAL_INITIAL_RISK | 239 | 0 | 1.6640 | 104.0519 | 0.4354 | 41.1173 | 13 | 11 | 0 |
| OPTIMIZED | I3 | USDRUBF | REFERENCE_2ATR | 239 | 0 | 1.6912 | 62.5851 | 0.2619 | 20.1500 | 15 | 9 | 0 |
| OPTIMIZED | I3 | CNYRUBF | ACTUAL_INITIAL_RISK | 225 | 0 | 1.2709 | 41.8678 | 0.1861 | 27.9259 | 14 | 10 | 0 |
| OPTIMIZED | I3 | CNYRUBF | REFERENCE_2ATR | 225 | 0 | 1.3410 | 30.9419 | 0.1375 | 14.3605 | 13 | 11 | 0 |
| OPTIMIZED | I3 | GLDRUBF | ACTUAL_INITIAL_RISK | 192 | 0 | 1.1915 | 26.8391 | 0.1398 | 36.2184 | 7 | 11 | 6 |
| OPTIMIZED | I3 | GLDRUBF | REFERENCE_2ATR | 192 | 0 | 1.2746 | 19.8081 | 0.1032 | 15.7993 | 8 | 10 | 6 |
| OPTIMIZED | I3 | IMOEXF | ACTUAL_INITIAL_RISK | 168 | 1 | 1.2554 | 29.7575 | 0.1771 | 29.8742 | 7 | 7 | 10 |
| OPTIMIZED | I3 | IMOEXF | REFERENCE_2ATR | 168 | 1 | 0.9683 | -2.0606 | -0.0123 | 18.9636 | 7 | 7 | 10 |

| version | rule | scope | normalization | year | direction | closed_trades | open_positions_at_period_end | gross_PF | gross_R | expectancy_R |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BASELINE | CONTROL | ALL_FOUR | ACTUAL_INITIAL_RISK | ALL | LONG | 416 | 1 | 1.5349 | 93.0651 | 0.2237 |
| BASELINE | CONTROL | ALL_FOUR | ACTUAL_INITIAL_RISK | 2023 | LONG | 161 | 0 | 1.7729 | 49.3497 | 0.3065 |
| BASELINE | CONTROL | ALL_FOUR | ACTUAL_INITIAL_RISK | 2024 | LONG | 255 | 1 | 1.3969 | 43.7154 | 0.1714 |
| BASELINE | CONTROL | ALL_FOUR | ACTUAL_INITIAL_RISK | ALL | SHORT | 325 | 0 | 1.3566 | 51.3461 | 0.1580 |
| BASELINE | CONTROL | ALL_FOUR | ACTUAL_INITIAL_RISK | 2023 | SHORT | 95 | 0 | 2.2633 | 44.8552 | 0.4722 |
| BASELINE | CONTROL | ALL_FOUR | ACTUAL_INITIAL_RISK | 2024 | SHORT | 230 | 0 | 1.0598 | 6.4909 | 0.0282 |
| BASELINE | CONTROL | ALL_FOUR | REFERENCE_2ATR | ALL | LONG | 416 | 1 | 1.5349 | 93.0651 | 0.2237 |
| BASELINE | CONTROL | ALL_FOUR | REFERENCE_2ATR | 2023 | LONG | 161 | 0 | 1.7729 | 49.3497 | 0.3065 |
| BASELINE | CONTROL | ALL_FOUR | REFERENCE_2ATR | 2024 | LONG | 255 | 1 | 1.3969 | 43.7154 | 0.1714 |
| BASELINE | CONTROL | ALL_FOUR | REFERENCE_2ATR | ALL | SHORT | 325 | 0 | 1.3566 | 51.3461 | 0.1580 |
| BASELINE | CONTROL | ALL_FOUR | REFERENCE_2ATR | 2023 | SHORT | 95 | 0 | 2.2633 | 44.8552 | 0.4722 |
| BASELINE | CONTROL | ALL_FOUR | REFERENCE_2ATR | 2024 | SHORT | 230 | 0 | 1.0598 | 6.4909 | 0.0282 |
| BASELINE | CONTROL | USDRUBF | ACTUAL_INITIAL_RISK | ALL | LONG | 133 | 0 | 1.8852 | 46.8216 | 0.3520 |
| BASELINE | CONTROL | USDRUBF | ACTUAL_INITIAL_RISK | 2023 | LONG | 71 | 0 | 2.7092 | 42.4775 | 0.5983 |
| BASELINE | CONTROL | USDRUBF | ACTUAL_INITIAL_RISK | 2024 | LONG | 62 | 0 | 1.1549 | 4.3441 | 0.0701 |
| BASELINE | CONTROL | USDRUBF | ACTUAL_INITIAL_RISK | ALL | SHORT | 93 | 0 | 1.5550 | 21.9355 | 0.2359 |
| BASELINE | CONTROL | USDRUBF | ACTUAL_INITIAL_RISK | 2023 | SHORT | 40 | 0 | 2.6766 | 22.3813 | 0.5595 |
| BASELINE | CONTROL | USDRUBF | ACTUAL_INITIAL_RISK | 2024 | SHORT | 53 | 0 | 0.9830 | -0.4458 | -0.0084 |
| BASELINE | CONTROL | USDRUBF | REFERENCE_2ATR | ALL | LONG | 133 | 0 | 1.8852 | 46.8216 | 0.3520 |
| BASELINE | CONTROL | USDRUBF | REFERENCE_2ATR | 2023 | LONG | 71 | 0 | 2.7092 | 42.4775 | 0.5983 |
| BASELINE | CONTROL | USDRUBF | REFERENCE_2ATR | 2024 | LONG | 62 | 0 | 1.1549 | 4.3441 | 0.0701 |
| BASELINE | CONTROL | USDRUBF | REFERENCE_2ATR | ALL | SHORT | 93 | 0 | 1.5550 | 21.9355 | 0.2359 |
| BASELINE | CONTROL | USDRUBF | REFERENCE_2ATR | 2023 | SHORT | 40 | 0 | 2.6766 | 22.3813 | 0.5595 |
| BASELINE | CONTROL | USDRUBF | REFERENCE_2ATR | 2024 | SHORT | 53 | 0 | 0.9830 | -0.4458 | -0.0084 |
| BASELINE | CONTROL | CNYRUBF | ACTUAL_INITIAL_RISK | ALL | LONG | 113 | 0 | 1.6045 | 28.7720 | 0.2546 |
| BASELINE | CONTROL | CNYRUBF | ACTUAL_INITIAL_RISK | 2023 | LONG | 55 | 0 | 1.5088 | 11.6494 | 0.2118 |
| BASELINE | CONTROL | CNYRUBF | ACTUAL_INITIAL_RISK | 2024 | LONG | 58 | 0 | 1.6934 | 17.1226 | 0.2952 |
| BASELINE | CONTROL | CNYRUBF | ACTUAL_INITIAL_RISK | ALL | SHORT | 86 | 0 | 1.4312 | 16.2602 | 0.1891 |
| BASELINE | CONTROL | CNYRUBF | ACTUAL_INITIAL_RISK | 2023 | SHORT | 30 | 0 | 2.5135 | 17.5196 | 0.5840 |
| BASELINE | CONTROL | CNYRUBF | ACTUAL_INITIAL_RISK | 2024 | SHORT | 56 | 0 | 0.9518 | -1.2594 | -0.0225 |
| BASELINE | CONTROL | CNYRUBF | REFERENCE_2ATR | ALL | LONG | 113 | 0 | 1.6045 | 28.7720 | 0.2546 |
| BASELINE | CONTROL | CNYRUBF | REFERENCE_2ATR | 2023 | LONG | 55 | 0 | 1.5088 | 11.6494 | 0.2118 |
| BASELINE | CONTROL | CNYRUBF | REFERENCE_2ATR | 2024 | LONG | 58 | 0 | 1.6934 | 17.1226 | 0.2952 |
| BASELINE | CONTROL | CNYRUBF | REFERENCE_2ATR | ALL | SHORT | 86 | 0 | 1.4312 | 16.2602 | 0.1891 |
| BASELINE | CONTROL | CNYRUBF | REFERENCE_2ATR | 2023 | SHORT | 30 | 0 | 2.5135 | 17.5196 | 0.5840 |
| BASELINE | CONTROL | CNYRUBF | REFERENCE_2ATR | 2024 | SHORT | 56 | 0 | 0.9518 | -1.2594 | -0.0225 |
| BASELINE | CONTROL | GLDRUBF | ACTUAL_INITIAL_RISK | ALL | LONG | 119 | 0 | 1.0221 | 1.2411 | 0.0104 |
| BASELINE | CONTROL | GLDRUBF | ACTUAL_INITIAL_RISK | 2023 | LONG | 33 | 0 | 0.6802 | -5.1432 | -0.1559 |
| BASELINE | CONTROL | GLDRUBF | ACTUAL_INITIAL_RISK | 2024 | LONG | 86 | 0 | 1.1596 | 6.3844 | 0.0742 |
| BASELINE | CONTROL | GLDRUBF | ACTUAL_INITIAL_RISK | ALL | SHORT | 59 | 0 | 1.4053 | 9.9273 | 0.1683 |
| BASELINE | CONTROL | GLDRUBF | ACTUAL_INITIAL_RISK | 2023 | SHORT | 18 | 0 | 1.7075 | 5.0407 | 0.2800 |
| BASELINE | CONTROL | GLDRUBF | ACTUAL_INITIAL_RISK | 2024 | SHORT | 41 | 0 | 1.2813 | 4.8866 | 0.1192 |
| BASELINE | CONTROL | GLDRUBF | REFERENCE_2ATR | ALL | LONG | 119 | 0 | 1.0221 | 1.2411 | 0.0104 |
| BASELINE | CONTROL | GLDRUBF | REFERENCE_2ATR | 2023 | LONG | 33 | 0 | 0.6802 | -5.1432 | -0.1559 |
| BASELINE | CONTROL | GLDRUBF | REFERENCE_2ATR | 2024 | LONG | 86 | 0 | 1.1596 | 6.3844 | 0.0742 |
| BASELINE | CONTROL | GLDRUBF | REFERENCE_2ATR | ALL | SHORT | 59 | 0 | 1.4053 | 9.9273 | 0.1683 |
| BASELINE | CONTROL | GLDRUBF | REFERENCE_2ATR | 2023 | SHORT | 18 | 0 | 1.7075 | 5.0407 | 0.2800 |
| BASELINE | CONTROL | GLDRUBF | REFERENCE_2ATR | 2024 | SHORT | 41 | 0 | 1.2813 | 4.8866 | 0.1192 |
| BASELINE | CONTROL | IMOEXF | ACTUAL_INITIAL_RISK | ALL | LONG | 51 | 1 | 1.9319 | 16.2304 | 0.3182 |
| BASELINE | CONTROL | IMOEXF | ACTUAL_INITIAL_RISK | 2023 | LONG | 2 | 0 | 28.1271 | 0.3660 | 0.1830 |
| BASELINE | CONTROL | IMOEXF | ACTUAL_INITIAL_RISK | 2024 | LONG | 49 | 1 | 1.9116 | 15.8644 | 0.3238 |
| BASELINE | CONTROL | IMOEXF | ACTUAL_INITIAL_RISK | ALL | SHORT | 87 | 0 | 1.0763 | 3.2232 | 0.0370 |
| BASELINE | CONTROL | IMOEXF | ACTUAL_INITIAL_RISK | 2023 | SHORT | 7 | 0 | 0.9750 | -0.0864 | -0.0123 |
| BASELINE | CONTROL | IMOEXF | ACTUAL_INITIAL_RISK | 2024 | SHORT | 80 | 0 | 1.0853 | 3.3095 | 0.0414 |
| BASELINE | CONTROL | IMOEXF | REFERENCE_2ATR | ALL | LONG | 51 | 1 | 1.9319 | 16.2304 | 0.3182 |
| BASELINE | CONTROL | IMOEXF | REFERENCE_2ATR | 2023 | LONG | 2 | 0 | 28.1271 | 0.3660 | 0.1830 |
| BASELINE | CONTROL | IMOEXF | REFERENCE_2ATR | 2024 | LONG | 49 | 1 | 1.9116 | 15.8644 | 0.3238 |
| BASELINE | CONTROL | IMOEXF | REFERENCE_2ATR | ALL | SHORT | 87 | 0 | 1.0763 | 3.2232 | 0.0370 |
| BASELINE | CONTROL | IMOEXF | REFERENCE_2ATR | 2023 | SHORT | 7 | 0 | 0.9750 | -0.0864 | -0.0123 |
| BASELINE | CONTROL | IMOEXF | REFERENCE_2ATR | 2024 | SHORT | 80 | 0 | 1.0853 | 3.3095 | 0.0414 |
| BASELINE | I1 | ALL_FOUR | ACTUAL_INITIAL_RISK | ALL | LONG | 475 | 1 | 1.2793 | 87.3529 | 0.1839 |
| BASELINE | I1 | ALL_FOUR | ACTUAL_INITIAL_RISK | 2023 | LONG | 185 | 0 | 1.5059 | 57.3548 | 0.3100 |
| BASELINE | I1 | ALL_FOUR | ACTUAL_INITIAL_RISK | 2024 | LONG | 290 | 1 | 1.1504 | 29.9981 | 0.1034 |
| BASELINE | I1 | ALL_FOUR | ACTUAL_INITIAL_RISK | ALL | SHORT | 373 | 0 | 1.1844 | 43.3651 | 0.1163 |
| BASELINE | I1 | ALL_FOUR | ACTUAL_INITIAL_RISK | 2023 | SHORT | 104 | 0 | 1.9920 | 53.6544 | 0.5159 |
| BASELINE | I1 | ALL_FOUR | ACTUAL_INITIAL_RISK | 2024 | SHORT | 269 | 0 | 0.9432 | -10.2892 | -0.0382 |
| BASELINE | I1 | ALL_FOUR | REFERENCE_2ATR | ALL | LONG | 475 | 1 | 1.3013 | 52.6822 | 0.1109 |
| BASELINE | I1 | ALL_FOUR | REFERENCE_2ATR | 2023 | LONG | 185 | 0 | 1.4649 | 31.4675 | 0.1701 |
| BASELINE | I1 | ALL_FOUR | REFERENCE_2ATR | 2024 | LONG | 290 | 1 | 1.1979 | 21.2148 | 0.0732 |
| BASELINE | I1 | ALL_FOUR | REFERENCE_2ATR | ALL | SHORT | 373 | 0 | 1.2295 | 32.4704 | 0.0871 |
| BASELINE | I1 | ALL_FOUR | REFERENCE_2ATR | 2023 | SHORT | 104 | 0 | 2.3790 | 44.1702 | 0.4247 |
| BASELINE | I1 | ALL_FOUR | REFERENCE_2ATR | 2024 | SHORT | 269 | 0 | 0.8931 | -11.6998 | -0.0435 |
| BASELINE | I1 | USDRUBF | ACTUAL_INITIAL_RISK | ALL | LONG | 146 | 0 | 1.6586 | 58.2577 | 0.3990 |
| BASELINE | I1 | USDRUBF | ACTUAL_INITIAL_RISK | 2023 | LONG | 81 | 0 | 2.0251 | 46.3900 | 0.5727 |
| BASELINE | I1 | USDRUBF | ACTUAL_INITIAL_RISK | 2024 | LONG | 65 | 0 | 1.2747 | 11.8677 | 0.1826 |
| BASELINE | I1 | USDRUBF | ACTUAL_INITIAL_RISK | ALL | SHORT | 102 | 0 | 1.2228 | 13.5156 | 0.1325 |
| BASELINE | I1 | USDRUBF | ACTUAL_INITIAL_RISK | 2023 | SHORT | 41 | 0 | 2.6872 | 27.7519 | 0.6769 |
| BASELINE | I1 | USDRUBF | ACTUAL_INITIAL_RISK | 2024 | SHORT | 61 | 0 | 0.6780 | -14.2363 | -0.2334 |
| BASELINE | I1 | USDRUBF | REFERENCE_2ATR | ALL | LONG | 146 | 0 | 1.7437 | 37.3063 | 0.2555 |
| BASELINE | I1 | USDRUBF | REFERENCE_2ATR | 2023 | LONG | 81 | 0 | 2.1988 | 31.1892 | 0.3851 |
| BASELINE | I1 | USDRUBF | REFERENCE_2ATR | 2024 | LONG | 65 | 0 | 1.2533 | 6.1171 | 0.0941 |
| BASELINE | I1 | USDRUBF | REFERENCE_2ATR | ALL | SHORT | 102 | 0 | 1.4334 | 16.6105 | 0.1628 |
| BASELINE | I1 | USDRUBF | REFERENCE_2ATR | 2023 | SHORT | 41 | 0 | 3.1111 | 23.0890 | 0.5631 |
| BASELINE | I1 | USDRUBF | REFERENCE_2ATR | 2024 | SHORT | 61 | 0 | 0.7635 | -6.4785 | -0.1062 |
| BASELINE | I1 | CNYRUBF | ACTUAL_INITIAL_RISK | ALL | LONG | 128 | 0 | 1.4108 | 32.9372 | 0.2573 |
| BASELINE | I1 | CNYRUBF | ACTUAL_INITIAL_RISK | 2023 | LONG | 65 | 0 | 1.3402 | 14.3654 | 0.2210 |
| BASELINE | I1 | CNYRUBF | ACTUAL_INITIAL_RISK | 2024 | LONG | 63 | 0 | 1.4893 | 18.5718 | 0.2948 |
| BASELINE | I1 | CNYRUBF | ACTUAL_INITIAL_RISK | ALL | SHORT | 100 | 0 | 1.1752 | 11.7101 | 0.1171 |
| BASELINE | I1 | CNYRUBF | ACTUAL_INITIAL_RISK | 2023 | SHORT | 35 | 0 | 2.1466 | 24.6752 | 0.7050 |
| BASELINE | I1 | CNYRUBF | ACTUAL_INITIAL_RISK | 2024 | SHORT | 65 | 0 | 0.7139 | -12.9650 | -0.1995 |
| BASELINE | I1 | CNYRUBF | REFERENCE_2ATR | ALL | LONG | 128 | 0 | 1.4471 | 21.2996 | 0.1664 |
| BASELINE | I1 | CNYRUBF | REFERENCE_2ATR | 2023 | LONG | 65 | 0 | 1.2199 | 5.6592 | 0.0871 |
| BASELINE | I1 | CNYRUBF | REFERENCE_2ATR | 2024 | LONG | 63 | 0 | 1.7140 | 15.6403 | 0.2483 |
| BASELINE | I1 | CNYRUBF | REFERENCE_2ATR | ALL | SHORT | 100 | 0 | 1.2209 | 9.1392 | 0.0914 |
| BASELINE | I1 | CNYRUBF | REFERENCE_2ATR | 2023 | SHORT | 35 | 0 | 2.1315 | 14.7149 | 0.4204 |
| BASELINE | I1 | CNYRUBF | REFERENCE_2ATR | 2024 | SHORT | 65 | 0 | 0.8034 | -5.5757 | -0.0858 |
| BASELINE | I1 | GLDRUBF | ACTUAL_INITIAL_RISK | ALL | LONG | 138 | 0 | 0.7733 | -23.2014 | -0.1681 |
| BASELINE | I1 | GLDRUBF | ACTUAL_INITIAL_RISK | 2023 | LONG | 37 | 0 | 0.8536 | -3.7888 | -0.1024 |
| BASELINE | I1 | GLDRUBF | ACTUAL_INITIAL_RISK | 2024 | LONG | 101 | 0 | 0.7461 | -19.4126 | -0.1922 |
| BASELINE | I1 | GLDRUBF | ACTUAL_INITIAL_RISK | ALL | SHORT | 63 | 0 | 1.3953 | 13.4811 | 0.2140 |
| BASELINE | I1 | GLDRUBF | ACTUAL_INITIAL_RISK | 2023 | SHORT | 19 | 0 | 1.4665 | 4.3811 | 0.2306 |
| BASELINE | I1 | GLDRUBF | ACTUAL_INITIAL_RISK | 2024 | SHORT | 44 | 0 | 1.3683 | 9.0999 | 0.2068 |
| BASELINE | I1 | GLDRUBF | REFERENCE_2ATR | ALL | LONG | 138 | 0 | 0.8698 | -7.1963 | -0.0521 |
| BASELINE | I1 | GLDRUBF | REFERENCE_2ATR | 2023 | LONG | 37 | 0 | 0.6388 | -5.7469 | -0.1553 |
| BASELINE | I1 | GLDRUBF | REFERENCE_2ATR | 2024 | LONG | 101 | 0 | 0.9632 | -1.4493 | -0.0143 |
| BASELINE | I1 | GLDRUBF | REFERENCE_2ATR | ALL | SHORT | 63 | 0 | 1.6685 | 12.5014 | 0.1984 |
| BASELINE | I1 | GLDRUBF | REFERENCE_2ATR | 2023 | SHORT | 19 | 0 | 2.1669 | 6.2196 | 0.3273 |
| BASELINE | I1 | GLDRUBF | REFERENCE_2ATR | 2024 | SHORT | 44 | 0 | 1.4698 | 6.2817 | 0.1428 |
| BASELINE | I1 | IMOEXF | ACTUAL_INITIAL_RISK | ALL | LONG | 63 | 1 | 1.4631 | 19.3594 | 0.3073 |
| BASELINE | I1 | IMOEXF | ACTUAL_INITIAL_RISK | 2023 | LONG | 2 | 0 | 30.1590 | 0.3883 | 0.1941 |
| BASELINE | I1 | IMOEXF | ACTUAL_INITIAL_RISK | 2024 | LONG | 61 | 1 | 1.4539 | 18.9712 | 0.3110 |
| BASELINE | I1 | IMOEXF | ACTUAL_INITIAL_RISK | ALL | SHORT | 108 | 0 | 1.0633 | 4.6584 | 0.0431 |
| BASELINE | I1 | IMOEXF | ACTUAL_INITIAL_RISK | 2023 | SHORT | 9 | 0 | 0.5310 | -3.1538 | -0.3504 |
| BASELINE | I1 | IMOEXF | ACTUAL_INITIAL_RISK | 2024 | SHORT | 99 | 0 | 1.1169 | 7.8121 | 0.0789 |
| BASELINE | I1 | IMOEXF | REFERENCE_2ATR | ALL | LONG | 63 | 1 | 1.0584 | 1.2726 | 0.0202 |
| BASELINE | I1 | IMOEXF | REFERENCE_2ATR | 2023 | LONG | 2 | 0 | 28.1271 | 0.3660 | 0.1830 |
| BASELINE | I1 | IMOEXF | REFERENCE_2ATR | 2024 | LONG | 61 | 1 | 1.0417 | 0.9066 | 0.0149 |
| BASELINE | I1 | IMOEXF | REFERENCE_2ATR | ALL | SHORT | 108 | 0 | 0.8658 | -5.7807 | -0.0535 |
| BASELINE | I1 | IMOEXF | REFERENCE_2ATR | 2023 | SHORT | 9 | 0 | 1.0531 | 0.1466 | 0.0163 |
| BASELINE | I1 | IMOEXF | REFERENCE_2ATR | 2024 | SHORT | 99 | 0 | 0.8530 | -5.9273 | -0.0599 |
| BASELINE | I2 | ALL_FOUR | ACTUAL_INITIAL_RISK | ALL | LONG | 627 | 1 | 1.0275 | 16.2085 | 0.0259 |
| BASELINE | I2 | ALL_FOUR | ACTUAL_INITIAL_RISK | 2023 | LONG | 246 | 0 | 0.8906 | -24.6268 | -0.1001 |
| BASELINE | I2 | ALL_FOUR | ACTUAL_INITIAL_RISK | 2024 | LONG | 381 | 1 | 1.1119 | 40.8353 | 0.1072 |
| BASELINE | I2 | ALL_FOUR | ACTUAL_INITIAL_RISK | ALL | SHORT | 473 | 0 | 1.7015 | 319.1785 | 0.6748 |
| BASELINE | I2 | ALL_FOUR | ACTUAL_INITIAL_RISK | 2023 | SHORT | 135 | 0 | 1.8078 | 108.4294 | 0.8032 |
| BASELINE | I2 | ALL_FOUR | ACTUAL_INITIAL_RISK | 2024 | SHORT | 338 | 0 | 1.6570 | 210.7491 | 0.6235 |
| BASELINE | I2 | ALL_FOUR | REFERENCE_2ATR | ALL | LONG | 627 | 1 | 1.2228 | 30.7261 | 0.0490 |
| BASELINE | I2 | ALL_FOUR | REFERENCE_2ATR | 2023 | LONG | 246 | 0 | 1.2220 | 12.9100 | 0.0525 |
| BASELINE | I2 | ALL_FOUR | REFERENCE_2ATR | 2024 | LONG | 381 | 1 | 1.2235 | 17.8161 | 0.0468 |
| BASELINE | I2 | ALL_FOUR | REFERENCE_2ATR | ALL | SHORT | 473 | 0 | 1.4138 | 42.0471 | 0.0889 |
| BASELINE | I2 | ALL_FOUR | REFERENCE_2ATR | 2023 | SHORT | 135 | 0 | 2.2340 | 34.1173 | 0.2527 |
| BASELINE | I2 | ALL_FOUR | REFERENCE_2ATR | 2024 | SHORT | 338 | 0 | 1.1072 | 7.9298 | 0.0235 |
| BASELINE | I2 | USDRUBF | ACTUAL_INITIAL_RISK | ALL | LONG | 195 | 0 | 1.3183 | 50.9637 | 0.2614 |
| BASELINE | I2 | USDRUBF | ACTUAL_INITIAL_RISK | 2023 | LONG | 114 | 0 | 1.2770 | 25.8875 | 0.2271 |
| BASELINE | I2 | USDRUBF | ACTUAL_INITIAL_RISK | 2024 | LONG | 81 | 0 | 1.3763 | 25.0762 | 0.3096 |
| BASELINE | I2 | USDRUBF | ACTUAL_INITIAL_RISK | ALL | SHORT | 131 | 0 | 1.8371 | 93.3672 | 0.7127 |
| BASELINE | I2 | USDRUBF | ACTUAL_INITIAL_RISK | 2023 | SHORT | 52 | 0 | 2.8394 | 63.2478 | 1.2163 |
| BASELINE | I2 | USDRUBF | ACTUAL_INITIAL_RISK | 2024 | SHORT | 79 | 0 | 1.3904 | 30.1195 | 0.3813 |
| BASELINE | I2 | USDRUBF | REFERENCE_2ATR | ALL | LONG | 195 | 0 | 1.7393 | 27.5734 | 0.1414 |
| BASELINE | I2 | USDRUBF | REFERENCE_2ATR | 2023 | LONG | 114 | 0 | 1.8791 | 19.7211 | 0.1730 |
| BASELINE | I2 | USDRUBF | REFERENCE_2ATR | 2024 | LONG | 81 | 0 | 1.5284 | 7.8523 | 0.0969 |
| BASELINE | I2 | USDRUBF | REFERENCE_2ATR | ALL | SHORT | 131 | 0 | 1.4594 | 13.7524 | 0.1050 |
| BASELINE | I2 | USDRUBF | REFERENCE_2ATR | 2023 | SHORT | 52 | 0 | 2.6651 | 16.0797 | 0.3092 |
| BASELINE | I2 | USDRUBF | REFERENCE_2ATR | 2024 | SHORT | 79 | 0 | 0.8852 | -2.3272 | -0.0295 |
| BASELINE | I2 | CNYRUBF | ACTUAL_INITIAL_RISK | ALL | LONG | 167 | 0 | 0.9032 | -13.9282 | -0.0834 |
| BASELINE | I2 | CNYRUBF | ACTUAL_INITIAL_RISK | 2023 | LONG | 80 | 0 | 0.8636 | -9.5108 | -0.1189 |
| BASELINE | I2 | CNYRUBF | ACTUAL_INITIAL_RISK | 2024 | LONG | 87 | 0 | 0.9405 | -4.4174 | -0.0508 |
| BASELINE | I2 | CNYRUBF | ACTUAL_INITIAL_RISK | ALL | SHORT | 124 | 0 | 1.3468 | 36.8868 | 0.2975 |
| BASELINE | I2 | CNYRUBF | ACTUAL_INITIAL_RISK | 2023 | SHORT | 45 | 0 | 2.8704 | 71.3112 | 1.5847 |
| BASELINE | I2 | CNYRUBF | ACTUAL_INITIAL_RISK | 2024 | SHORT | 79 | 0 | 0.4955 | -34.4244 | -0.4358 |
| BASELINE | I2 | CNYRUBF | REFERENCE_2ATR | ALL | LONG | 167 | 0 | 1.1804 | 7.4529 | 0.0446 |
| BASELINE | I2 | CNYRUBF | REFERENCE_2ATR | 2023 | LONG | 80 | 0 | 0.9931 | -0.1562 | -0.0020 |
| BASELINE | I2 | CNYRUBF | REFERENCE_2ATR | 2024 | LONG | 87 | 0 | 1.4097 | 7.6091 | 0.0875 |
| BASELINE | I2 | CNYRUBF | REFERENCE_2ATR | ALL | SHORT | 124 | 0 | 1.3112 | 9.2096 | 0.0743 |
| BASELINE | I2 | CNYRUBF | REFERENCE_2ATR | 2023 | SHORT | 45 | 0 | 2.2329 | 12.5159 | 0.2781 |
| BASELINE | I2 | CNYRUBF | REFERENCE_2ATR | 2024 | SHORT | 79 | 0 | 0.8299 | -3.3063 | -0.0419 |
| BASELINE | I2 | GLDRUBF | ACTUAL_INITIAL_RISK | ALL | LONG | 187 | 0 | 0.8920 | -23.3205 | -0.1247 |
| BASELINE | I2 | GLDRUBF | ACTUAL_INITIAL_RISK | 2023 | LONG | 50 | 0 | 0.3432 | -39.9840 | -0.7997 |
| BASELINE | I2 | GLDRUBF | ACTUAL_INITIAL_RISK | 2024 | LONG | 137 | 0 | 1.1074 | 16.6634 | 0.1216 |
| BASELINE | I2 | GLDRUBF | ACTUAL_INITIAL_RISK | ALL | SHORT | 78 | 0 | 1.9990 | 89.6042 | 1.1488 |
| BASELINE | I2 | GLDRUBF | ACTUAL_INITIAL_RISK | 2023 | SHORT | 28 | 0 | 0.5266 | -25.4292 | -0.9082 |
| BASELINE | I2 | GLDRUBF | ACTUAL_INITIAL_RISK | 2024 | SHORT | 50 | 0 | 4.1975 | 115.0333 | 2.3007 |
| BASELINE | I2 | GLDRUBF | REFERENCE_2ATR | ALL | LONG | 187 | 0 | 0.8638 | -5.6883 | -0.0304 |
| BASELINE | I2 | GLDRUBF | REFERENCE_2ATR | 2023 | LONG | 50 | 0 | 0.4996 | -6.3365 | -0.1267 |
| BASELINE | I2 | GLDRUBF | REFERENCE_2ATR | 2024 | LONG | 137 | 0 | 1.0223 | 0.6482 | 0.0047 |
| BASELINE | I2 | GLDRUBF | REFERENCE_2ATR | ALL | SHORT | 78 | 0 | 2.0418 | 14.8954 | 0.1910 |
| BASELINE | I2 | GLDRUBF | REFERENCE_2ATR | 2023 | SHORT | 28 | 0 | 1.5953 | 3.9013 | 0.1393 |
| BASELINE | I2 | GLDRUBF | REFERENCE_2ATR | 2024 | SHORT | 50 | 0 | 2.4195 | 10.9941 | 0.2199 |
| BASELINE | I2 | IMOEXF | ACTUAL_INITIAL_RISK | ALL | LONG | 78 | 1 | 1.0356 | 2.4936 | 0.0320 |
| BASELINE | I2 | IMOEXF | ACTUAL_INITIAL_RISK | 2023 | LONG | 2 | 0 | 0.0000 | -1.0195 | -0.5098 |
| BASELINE | I2 | IMOEXF | ACTUAL_INITIAL_RISK | 2024 | LONG | 76 | 1 | 1.0508 | 3.5131 | 0.0462 |
| BASELINE | I2 | IMOEXF | ACTUAL_INITIAL_RISK | ALL | SHORT | 140 | 0 | 1.6737 | 99.3203 | 0.7094 |
| BASELINE | I2 | IMOEXF | ACTUAL_INITIAL_RISK | 2023 | SHORT | 10 | 0 | 0.9124 | -0.7004 | -0.0700 |
| BASELINE | I2 | IMOEXF | ACTUAL_INITIAL_RISK | 2024 | SHORT | 130 | 0 | 1.7174 | 100.0207 | 0.7694 |
| BASELINE | I2 | IMOEXF | REFERENCE_2ATR | ALL | LONG | 78 | 1 | 1.0793 | 1.3881 | 0.0178 |
| BASELINE | I2 | IMOEXF | REFERENCE_2ATR | 2023 | LONG | 2 | 0 | 0.0000 | -0.3183 | -0.1592 |
| BASELINE | I2 | IMOEXF | REFERENCE_2ATR | 2024 | LONG | 76 | 1 | 1.0993 | 1.7064 | 0.0225 |
| BASELINE | I2 | IMOEXF | REFERENCE_2ATR | ALL | SHORT | 140 | 0 | 1.1508 | 4.1896 | 0.0299 |
| BASELINE | I2 | IMOEXF | REFERENCE_2ATR | 2023 | SHORT | 10 | 0 | 2.2607 | 1.6204 | 0.1620 |
| BASELINE | I2 | IMOEXF | REFERENCE_2ATR | 2024 | SHORT | 130 | 0 | 1.0969 | 2.5692 | 0.0198 |
| BASELINE | I3 | ALL_FOUR | ACTUAL_INITIAL_RISK | ALL | LONG | 479 | 1 | 1.2644 | 84.7826 | 0.1770 |
| BASELINE | I3 | ALL_FOUR | ACTUAL_INITIAL_RISK | 2023 | LONG | 187 | 0 | 1.4734 | 55.3469 | 0.2960 |
| BASELINE | I3 | ALL_FOUR | ACTUAL_INITIAL_RISK | 2024 | LONG | 292 | 1 | 1.1444 | 29.4357 | 0.1008 |
| BASELINE | I3 | ALL_FOUR | ACTUAL_INITIAL_RISK | ALL | SHORT | 374 | 0 | 1.1998 | 48.3576 | 0.1293 |
| BASELINE | I3 | ALL_FOUR | ACTUAL_INITIAL_RISK | 2023 | SHORT | 104 | 0 | 2.0307 | 57.4613 | 0.5525 |
| BASELINE | I3 | ALL_FOUR | ACTUAL_INITIAL_RISK | 2024 | SHORT | 270 | 0 | 0.9511 | -9.1036 | -0.0337 |
| BASELINE | I3 | ALL_FOUR | REFERENCE_2ATR | ALL | LONG | 479 | 1 | 1.2765 | 48.9196 | 0.1021 |
| BASELINE | I3 | ALL_FOUR | REFERENCE_2ATR | 2023 | LONG | 187 | 0 | 1.4349 | 29.6110 | 0.1583 |
| BASELINE | I3 | ALL_FOUR | REFERENCE_2ATR | 2024 | LONG | 292 | 1 | 1.1774 | 19.3087 | 0.0661 |
| BASELINE | I3 | ALL_FOUR | REFERENCE_2ATR | ALL | SHORT | 374 | 0 | 1.2547 | 35.3162 | 0.0944 |
| BASELINE | I3 | ALL_FOUR | REFERENCE_2ATR | 2023 | SHORT | 104 | 0 | 2.4202 | 44.7163 | 0.4300 |
| BASELINE | I3 | ALL_FOUR | REFERENCE_2ATR | 2024 | SHORT | 270 | 0 | 0.9123 | -9.4001 | -0.0348 |
| BASELINE | I3 | USDRUBF | ACTUAL_INITIAL_RISK | ALL | LONG | 146 | 0 | 1.6751 | 60.3211 | 0.4132 |
| BASELINE | I3 | USDRUBF | ACTUAL_INITIAL_RISK | 2023 | LONG | 81 | 0 | 2.0400 | 47.8902 | 0.5912 |
| BASELINE | I3 | USDRUBF | ACTUAL_INITIAL_RISK | 2024 | LONG | 65 | 0 | 1.2870 | 12.4309 | 0.1912 |
| BASELINE | I3 | USDRUBF | ACTUAL_INITIAL_RISK | ALL | SHORT | 102 | 0 | 1.2857 | 17.8815 | 0.1753 |
| BASELINE | I3 | USDRUBF | ACTUAL_INITIAL_RISK | 2023 | SHORT | 41 | 0 | 2.7907 | 30.8903 | 0.7534 |
| BASELINE | I3 | USDRUBF | ACTUAL_INITIAL_RISK | 2024 | SHORT | 61 | 0 | 0.7130 | -13.0088 | -0.2133 |
| BASELINE | I3 | USDRUBF | REFERENCE_2ATR | ALL | LONG | 146 | 0 | 1.7510 | 37.5145 | 0.2569 |
| BASELINE | I3 | USDRUBF | REFERENCE_2ATR | 2023 | LONG | 81 | 0 | 2.2165 | 31.3974 | 0.3876 |
| BASELINE | I3 | USDRUBF | REFERENCE_2ATR | 2024 | LONG | 65 | 0 | 1.2533 | 6.1171 | 0.0941 |
| BASELINE | I3 | USDRUBF | REFERENCE_2ATR | ALL | SHORT | 102 | 0 | 1.4791 | 17.7953 | 0.1745 |
| BASELINE | I3 | USDRUBF | REFERENCE_2ATR | 2023 | SHORT | 41 | 0 | 3.1591 | 23.2552 | 0.5672 |
| BASELINE | I3 | USDRUBF | REFERENCE_2ATR | 2024 | SHORT | 61 | 0 | 0.7930 | -5.4598 | -0.0895 |
| BASELINE | I3 | CNYRUBF | ACTUAL_INITIAL_RISK | ALL | LONG | 130 | 0 | 1.3663 | 30.3607 | 0.2335 |
| BASELINE | I3 | CNYRUBF | ACTUAL_INITIAL_RISK | 2023 | LONG | 67 | 0 | 1.2481 | 11.0771 | 0.1653 |
| BASELINE | I3 | CNYRUBF | ACTUAL_INITIAL_RISK | 2024 | LONG | 63 | 0 | 1.5045 | 19.2836 | 0.3061 |
| BASELINE | I3 | CNYRUBF | ACTUAL_INITIAL_RISK | ALL | SHORT | 100 | 0 | 1.1842 | 12.6375 | 0.1264 |
| BASELINE | I3 | CNYRUBF | ACTUAL_INITIAL_RISK | 2023 | SHORT | 35 | 0 | 2.1813 | 25.6747 | 0.7336 |
| BASELINE | I3 | CNYRUBF | ACTUAL_INITIAL_RISK | 2024 | SHORT | 65 | 0 | 0.7218 | -13.0372 | -0.2006 |
| BASELINE | I3 | CNYRUBF | REFERENCE_2ATR | ALL | LONG | 130 | 0 | 1.3775 | 18.4973 | 0.1423 |
| BASELINE | I3 | CNYRUBF | REFERENCE_2ATR | 2023 | LONG | 67 | 0 | 1.1021 | 2.7737 | 0.0414 |
| BASELINE | I3 | CNYRUBF | REFERENCE_2ATR | 2024 | LONG | 63 | 0 | 1.7206 | 15.7236 | 0.2496 |
| BASELINE | I3 | CNYRUBF | REFERENCE_2ATR | ALL | SHORT | 100 | 0 | 1.2688 | 10.7000 | 0.1070 |
| BASELINE | I3 | CNYRUBF | REFERENCE_2ATR | 2023 | SHORT | 35 | 0 | 2.1956 | 15.0949 | 0.4313 |
| BASELINE | I3 | CNYRUBF | REFERENCE_2ATR | 2024 | SHORT | 65 | 0 | 0.8383 | -4.3949 | -0.0676 |
| BASELINE | I3 | GLDRUBF | ACTUAL_INITIAL_RISK | ALL | LONG | 140 | 0 | 0.7435 | -27.3632 | -0.1955 |
| BASELINE | I3 | GLDRUBF | ACTUAL_INITIAL_RISK | 2023 | LONG | 37 | 0 | 0.8470 | -4.0085 | -0.1083 |
| BASELINE | I3 | GLDRUBF | ACTUAL_INITIAL_RISK | 2024 | LONG | 103 | 0 | 0.7098 | -23.3547 | -0.2267 |
| BASELINE | I3 | GLDRUBF | ACTUAL_INITIAL_RISK | ALL | SHORT | 63 | 0 | 1.4221 | 14.7776 | 0.2346 |
| BASELINE | I3 | GLDRUBF | ACTUAL_INITIAL_RISK | 2023 | SHORT | 19 | 0 | 1.4034 | 4.0501 | 0.2132 |
| BASELINE | I3 | GLDRUBF | ACTUAL_INITIAL_RISK | 2024 | SHORT | 44 | 0 | 1.4296 | 10.7275 | 0.2438 |
| BASELINE | I3 | GLDRUBF | REFERENCE_2ATR | ALL | LONG | 140 | 0 | 0.8495 | -8.4671 | -0.0605 |
| BASELINE | I3 | GLDRUBF | REFERENCE_2ATR | 2023 | LONG | 37 | 0 | 0.6735 | -4.9261 | -0.1331 |
| BASELINE | I3 | GLDRUBF | REFERENCE_2ATR | 2024 | LONG | 103 | 0 | 0.9140 | -3.5410 | -0.0344 |
| BASELINE | I3 | GLDRUBF | REFERENCE_2ATR | ALL | SHORT | 63 | 0 | 1.6685 | 12.5014 | 0.1984 |
| BASELINE | I3 | GLDRUBF | REFERENCE_2ATR | 2023 | SHORT | 19 | 0 | 2.1669 | 6.2196 | 0.3273 |
| BASELINE | I3 | GLDRUBF | REFERENCE_2ATR | 2024 | SHORT | 44 | 0 | 1.4698 | 6.2817 | 0.1428 |
| BASELINE | I3 | IMOEXF | ACTUAL_INITIAL_RISK | ALL | LONG | 63 | 1 | 1.5134 | 21.4639 | 0.3407 |
| BASELINE | I3 | IMOEXF | ACTUAL_INITIAL_RISK | 2023 | LONG | 2 | 0 | 29.7632 | 0.3881 | 0.1940 |
| BASELINE | I3 | IMOEXF | ACTUAL_INITIAL_RISK | 2024 | LONG | 61 | 1 | 1.5043 | 21.0758 | 0.3455 |
| BASELINE | I3 | IMOEXF | ACTUAL_INITIAL_RISK | ALL | SHORT | 109 | 0 | 1.0404 | 3.0611 | 0.0281 |
| BASELINE | I3 | IMOEXF | ACTUAL_INITIAL_RISK | 2023 | SHORT | 9 | 0 | 0.5310 | -3.1538 | -0.3504 |
| BASELINE | I3 | IMOEXF | ACTUAL_INITIAL_RISK | 2024 | SHORT | 100 | 0 | 1.0899 | 6.2149 | 0.0621 |
| BASELINE | I3 | IMOEXF | REFERENCE_2ATR | ALL | LONG | 63 | 1 | 1.0634 | 1.3749 | 0.0218 |
| BASELINE | I3 | IMOEXF | REFERENCE_2ATR | 2023 | LONG | 2 | 0 | 28.1271 | 0.3660 | 0.1830 |
| BASELINE | I3 | IMOEXF | REFERENCE_2ATR | 2024 | LONG | 61 | 1 | 1.0466 | 1.0089 | 0.0165 |
| BASELINE | I3 | IMOEXF | REFERENCE_2ATR | ALL | SHORT | 109 | 0 | 0.8678 | -5.6806 | -0.0521 |
| BASELINE | I3 | IMOEXF | REFERENCE_2ATR | 2023 | SHORT | 9 | 0 | 1.0531 | 0.1466 | 0.0163 |
| BASELINE | I3 | IMOEXF | REFERENCE_2ATR | 2024 | SHORT | 100 | 0 | 0.8551 | -5.8272 | -0.0583 |
| OPTIMIZED | CONTROL | ALL_FOUR | ACTUAL_INITIAL_RISK | ALL | LONG | 396 | 1 | 1.5650 | 103.1002 | 0.2604 |
| OPTIMIZED | CONTROL | ALL_FOUR | ACTUAL_INITIAL_RISK | 2023 | LONG | 152 | 0 | 1.7874 | 53.6639 | 0.3531 |
| OPTIMIZED | CONTROL | ALL_FOUR | ACTUAL_INITIAL_RISK | 2024 | LONG | 244 | 1 | 1.4324 | 49.4363 | 0.2026 |
| OPTIMIZED | CONTROL | ALL_FOUR | ACTUAL_INITIAL_RISK | ALL | SHORT | 305 | 0 | 1.5225 | 75.6197 | 0.2479 |
| OPTIMIZED | CONTROL | ALL_FOUR | ACTUAL_INITIAL_RISK | 2023 | SHORT | 91 | 0 | 2.1695 | 44.9539 | 0.4940 |
| OPTIMIZED | CONTROL | ALL_FOUR | ACTUAL_INITIAL_RISK | 2024 | SHORT | 214 | 0 | 1.2885 | 30.6658 | 0.1433 |
| OPTIMIZED | CONTROL | ALL_FOUR | REFERENCE_2ATR | ALL | LONG | 396 | 1 | 1.5650 | 103.1002 | 0.2604 |
| OPTIMIZED | CONTROL | ALL_FOUR | REFERENCE_2ATR | 2023 | LONG | 152 | 0 | 1.7874 | 53.6639 | 0.3531 |
| OPTIMIZED | CONTROL | ALL_FOUR | REFERENCE_2ATR | 2024 | LONG | 244 | 1 | 1.4324 | 49.4363 | 0.2026 |
| OPTIMIZED | CONTROL | ALL_FOUR | REFERENCE_2ATR | ALL | SHORT | 305 | 0 | 1.5225 | 75.6197 | 0.2479 |
| OPTIMIZED | CONTROL | ALL_FOUR | REFERENCE_2ATR | 2023 | SHORT | 91 | 0 | 2.1695 | 44.9539 | 0.4940 |
| OPTIMIZED | CONTROL | ALL_FOUR | REFERENCE_2ATR | 2024 | SHORT | 214 | 0 | 1.2885 | 30.6658 | 0.1433 |
| OPTIMIZED | CONTROL | USDRUBF | ACTUAL_INITIAL_RISK | ALL | LONG | 125 | 0 | 1.9153 | 50.8503 | 0.4068 |
| OPTIMIZED | CONTROL | USDRUBF | ACTUAL_INITIAL_RISK | 2023 | LONG | 65 | 0 | 2.8525 | 47.4704 | 0.7303 |
| OPTIMIZED | CONTROL | USDRUBF | ACTUAL_INITIAL_RISK | 2024 | LONG | 60 | 0 | 1.1129 | 3.3800 | 0.0563 |
| OPTIMIZED | CONTROL | USDRUBF | ACTUAL_INITIAL_RISK | ALL | SHORT | 88 | 0 | 1.6249 | 24.9693 | 0.2837 |
| OPTIMIZED | CONTROL | USDRUBF | ACTUAL_INITIAL_RISK | 2023 | SHORT | 38 | 0 | 2.5415 | 23.1865 | 0.6102 |
| OPTIMIZED | CONTROL | USDRUBF | ACTUAL_INITIAL_RISK | 2024 | SHORT | 50 | 0 | 1.0716 | 1.7828 | 0.0357 |
| OPTIMIZED | CONTROL | USDRUBF | REFERENCE_2ATR | ALL | LONG | 125 | 0 | 1.9153 | 50.8503 | 0.4068 |
| OPTIMIZED | CONTROL | USDRUBF | REFERENCE_2ATR | 2023 | LONG | 65 | 0 | 2.8525 | 47.4704 | 0.7303 |
| OPTIMIZED | CONTROL | USDRUBF | REFERENCE_2ATR | 2024 | LONG | 60 | 0 | 1.1129 | 3.3800 | 0.0563 |
| OPTIMIZED | CONTROL | USDRUBF | REFERENCE_2ATR | ALL | SHORT | 88 | 0 | 1.6249 | 24.9693 | 0.2837 |
| OPTIMIZED | CONTROL | USDRUBF | REFERENCE_2ATR | 2023 | SHORT | 38 | 0 | 2.5415 | 23.1865 | 0.6102 |
| OPTIMIZED | CONTROL | USDRUBF | REFERENCE_2ATR | 2024 | SHORT | 50 | 0 | 1.0716 | 1.7828 | 0.0357 |
| OPTIMIZED | CONTROL | CNYRUBF | ACTUAL_INITIAL_RISK | ALL | LONG | 111 | 0 | 1.4236 | 22.0799 | 0.1989 |
| OPTIMIZED | CONTROL | CNYRUBF | ACTUAL_INITIAL_RISK | 2023 | LONG | 53 | 0 | 1.4426 | 10.8178 | 0.2041 |
| OPTIMIZED | CONTROL | CNYRUBF | ACTUAL_INITIAL_RISK | 2024 | LONG | 58 | 0 | 1.4069 | 11.2621 | 0.1942 |
| OPTIMIZED | CONTROL | CNYRUBF | ACTUAL_INITIAL_RISK | ALL | SHORT | 77 | 0 | 2.0388 | 36.0203 | 0.4678 |
| OPTIMIZED | CONTROL | CNYRUBF | ACTUAL_INITIAL_RISK | 2023 | SHORT | 29 | 0 | 2.4478 | 16.7282 | 0.5768 |
| OPTIMIZED | CONTROL | CNYRUBF | ACTUAL_INITIAL_RISK | 2024 | SHORT | 48 | 0 | 1.8344 | 19.2921 | 0.4019 |
| OPTIMIZED | CONTROL | CNYRUBF | REFERENCE_2ATR | ALL | LONG | 111 | 0 | 1.4236 | 22.0799 | 0.1989 |
| OPTIMIZED | CONTROL | CNYRUBF | REFERENCE_2ATR | 2023 | LONG | 53 | 0 | 1.4426 | 10.8178 | 0.2041 |
| OPTIMIZED | CONTROL | CNYRUBF | REFERENCE_2ATR | 2024 | LONG | 58 | 0 | 1.4069 | 11.2621 | 0.1942 |
| OPTIMIZED | CONTROL | CNYRUBF | REFERENCE_2ATR | ALL | SHORT | 77 | 0 | 2.0388 | 36.0203 | 0.4678 |
| OPTIMIZED | CONTROL | CNYRUBF | REFERENCE_2ATR | 2023 | SHORT | 29 | 0 | 2.4478 | 16.7282 | 0.5768 |
| OPTIMIZED | CONTROL | CNYRUBF | REFERENCE_2ATR | 2024 | SHORT | 48 | 0 | 1.8344 | 19.2921 | 0.4019 |
| OPTIMIZED | CONTROL | GLDRUBF | ACTUAL_INITIAL_RISK | ALL | LONG | 110 | 0 | 1.1576 | 8.7470 | 0.0795 |
| OPTIMIZED | CONTROL | GLDRUBF | ACTUAL_INITIAL_RISK | 2023 | LONG | 32 | 0 | 0.7074 | -5.2933 | -0.1654 |
| OPTIMIZED | CONTROL | GLDRUBF | ACTUAL_INITIAL_RISK | 2024 | LONG | 78 | 0 | 1.3754 | 14.0403 | 0.1800 |
| OPTIMIZED | CONTROL | GLDRUBF | ACTUAL_INITIAL_RISK | ALL | SHORT | 56 | 0 | 1.4670 | 12.5688 | 0.2244 |
| OPTIMIZED | CONTROL | GLDRUBF | ACTUAL_INITIAL_RISK | 2023 | SHORT | 17 | 0 | 1.7563 | 6.0522 | 0.3560 |
| OPTIMIZED | CONTROL | GLDRUBF | ACTUAL_INITIAL_RISK | 2024 | SHORT | 39 | 0 | 1.3446 | 6.5166 | 0.1671 |
| OPTIMIZED | CONTROL | GLDRUBF | REFERENCE_2ATR | ALL | LONG | 110 | 0 | 1.1576 | 8.7470 | 0.0795 |
| OPTIMIZED | CONTROL | GLDRUBF | REFERENCE_2ATR | 2023 | LONG | 32 | 0 | 0.7074 | -5.2933 | -0.1654 |
| OPTIMIZED | CONTROL | GLDRUBF | REFERENCE_2ATR | 2024 | LONG | 78 | 0 | 1.3754 | 14.0403 | 0.1800 |
| OPTIMIZED | CONTROL | GLDRUBF | REFERENCE_2ATR | ALL | SHORT | 56 | 0 | 1.4670 | 12.5688 | 0.2244 |
| OPTIMIZED | CONTROL | GLDRUBF | REFERENCE_2ATR | 2023 | SHORT | 17 | 0 | 1.7563 | 6.0522 | 0.3560 |
| OPTIMIZED | CONTROL | GLDRUBF | REFERENCE_2ATR | 2024 | SHORT | 39 | 0 | 1.3446 | 6.5166 | 0.1671 |
| OPTIMIZED | CONTROL | IMOEXF | ACTUAL_INITIAL_RISK | ALL | LONG | 50 | 1 | 2.1085 | 21.4229 | 0.4285 |
| OPTIMIZED | CONTROL | IMOEXF | ACTUAL_INITIAL_RISK | 2023 | LONG | 2 | 0 | — | 0.6690 | 0.3345 |
| OPTIMIZED | CONTROL | IMOEXF | ACTUAL_INITIAL_RISK | 2024 | LONG | 48 | 1 | 2.0739 | 20.7539 | 0.4324 |
| OPTIMIZED | CONTROL | IMOEXF | ACTUAL_INITIAL_RISK | ALL | SHORT | 84 | 0 | 1.0477 | 2.0613 | 0.0245 |
| OPTIMIZED | CONTROL | IMOEXF | ACTUAL_INITIAL_RISK | 2023 | SHORT | 7 | 0 | 0.7363 | -1.0130 | -0.1447 |
| OPTIMIZED | CONTROL | IMOEXF | ACTUAL_INITIAL_RISK | 2024 | SHORT | 77 | 0 | 1.0781 | 3.0743 | 0.0399 |
| OPTIMIZED | CONTROL | IMOEXF | REFERENCE_2ATR | ALL | LONG | 50 | 1 | 2.1085 | 21.4229 | 0.4285 |
| OPTIMIZED | CONTROL | IMOEXF | REFERENCE_2ATR | 2023 | LONG | 2 | 0 | — | 0.6690 | 0.3345 |
| OPTIMIZED | CONTROL | IMOEXF | REFERENCE_2ATR | 2024 | LONG | 48 | 1 | 2.0739 | 20.7539 | 0.4324 |
| OPTIMIZED | CONTROL | IMOEXF | REFERENCE_2ATR | ALL | SHORT | 84 | 0 | 1.0477 | 2.0613 | 0.0245 |
| OPTIMIZED | CONTROL | IMOEXF | REFERENCE_2ATR | 2023 | SHORT | 7 | 0 | 0.7363 | -1.0130 | -0.1447 |
| OPTIMIZED | CONTROL | IMOEXF | REFERENCE_2ATR | 2024 | SHORT | 77 | 0 | 1.0781 | 3.0743 | 0.0399 |
| OPTIMIZED | I1 | ALL_FOUR | ACTUAL_INITIAL_RISK | ALL | LONG | 458 | 1 | 1.4113 | 128.3173 | 0.2802 |
| OPTIMIZED | I1 | ALL_FOUR | ACTUAL_INITIAL_RISK | 2023 | LONG | 178 | 0 | 1.6833 | 78.5616 | 0.4414 |
| OPTIMIZED | I1 | ALL_FOUR | ACTUAL_INITIAL_RISK | 2024 | LONG | 280 | 1 | 1.2525 | 49.7557 | 0.1777 |
| OPTIMIZED | I1 | ALL_FOUR | ACTUAL_INITIAL_RISK | ALL | SHORT | 361 | 0 | 1.2937 | 71.3298 | 0.1976 |
| OPTIMIZED | I1 | ALL_FOUR | ACTUAL_INITIAL_RISK | 2023 | SHORT | 102 | 0 | 1.8743 | 52.6445 | 0.5161 |
| OPTIMIZED | I1 | ALL_FOUR | ACTUAL_INITIAL_RISK | 2024 | SHORT | 259 | 0 | 1.1023 | 18.6852 | 0.0721 |
| OPTIMIZED | I1 | ALL_FOUR | REFERENCE_2ATR | ALL | LONG | 458 | 1 | 1.3755 | 65.9882 | 0.1441 |
| OPTIMIZED | I1 | ALL_FOUR | REFERENCE_2ATR | 2023 | LONG | 178 | 0 | 1.5155 | 36.3848 | 0.2044 |
| OPTIMIZED | I1 | ALL_FOUR | REFERENCE_2ATR | 2024 | LONG | 280 | 1 | 1.2815 | 29.6034 | 0.1057 |
| OPTIMIZED | I1 | ALL_FOUR | REFERENCE_2ATR | ALL | SHORT | 361 | 0 | 1.2993 | 43.6788 | 0.1210 |
| OPTIMIZED | I1 | ALL_FOUR | REFERENCE_2ATR | 2023 | SHORT | 102 | 0 | 2.1363 | 41.1605 | 0.4035 |
| OPTIMIZED | I1 | ALL_FOUR | REFERENCE_2ATR | 2024 | SHORT | 259 | 0 | 1.0229 | 2.5183 | 0.0097 |
| OPTIMIZED | I1 | USDRUBF | ACTUAL_INITIAL_RISK | ALL | LONG | 140 | 0 | 1.8662 | 78.5698 | 0.5612 |
| OPTIMIZED | I1 | USDRUBF | ACTUAL_INITIAL_RISK | 2023 | LONG | 76 | 0 | 2.4477 | 66.2578 | 0.8718 |
| OPTIMIZED | I1 | USDRUBF | ACTUAL_INITIAL_RISK | 2024 | LONG | 64 | 0 | 1.2740 | 12.3121 | 0.1924 |
| OPTIMIZED | I1 | USDRUBF | ACTUAL_INITIAL_RISK | ALL | SHORT | 99 | 0 | 1.3035 | 19.2263 | 0.1942 |
| OPTIMIZED | I1 | USDRUBF | ACTUAL_INITIAL_RISK | 2023 | SHORT | 39 | 0 | 2.8716 | 34.1106 | 0.8746 |
| OPTIMIZED | I1 | USDRUBF | ACTUAL_INITIAL_RISK | 2024 | SHORT | 60 | 0 | 0.6701 | -14.8843 | -0.2481 |
| OPTIMIZED | I1 | USDRUBF | REFERENCE_2ATR | ALL | LONG | 140 | 0 | 1.8128 | 42.8144 | 0.3058 |
| OPTIMIZED | I1 | USDRUBF | REFERENCE_2ATR | 2023 | LONG | 76 | 0 | 2.3870 | 37.7182 | 0.4963 |
| OPTIMIZED | I1 | USDRUBF | REFERENCE_2ATR | 2024 | LONG | 64 | 0 | 1.2000 | 5.0962 | 0.0796 |
| OPTIMIZED | I1 | USDRUBF | REFERENCE_2ATR | ALL | SHORT | 99 | 0 | 1.4509 | 17.9119 | 0.1809 |
| OPTIMIZED | I1 | USDRUBF | REFERENCE_2ATR | 2023 | SHORT | 39 | 0 | 3.0237 | 24.6196 | 0.6313 |
| OPTIMIZED | I1 | USDRUBF | REFERENCE_2ATR | 2024 | SHORT | 60 | 0 | 0.7566 | -6.7077 | -0.1118 |
| OPTIMIZED | I1 | CNYRUBF | ACTUAL_INITIAL_RISK | ALL | LONG | 127 | 0 | 1.2621 | 21.7286 | 0.1711 |
| OPTIMIZED | I1 | CNYRUBF | ACTUAL_INITIAL_RISK | 2023 | LONG | 64 | 0 | 1.2163 | 9.3112 | 0.1455 |
| OPTIMIZED | I1 | CNYRUBF | ACTUAL_INITIAL_RISK | 2024 | LONG | 63 | 0 | 1.3115 | 12.4175 | 0.1971 |
| OPTIMIZED | I1 | CNYRUBF | ACTUAL_INITIAL_RISK | ALL | SHORT | 96 | 0 | 1.3209 | 21.9279 | 0.2284 |
| OPTIMIZED | I1 | CNYRUBF | ACTUAL_INITIAL_RISK | 2023 | SHORT | 35 | 0 | 1.7231 | 17.3235 | 0.4950 |
| OPTIMIZED | I1 | CNYRUBF | ACTUAL_INITIAL_RISK | 2024 | SHORT | 61 | 0 | 1.1037 | 4.6044 | 0.0755 |
| OPTIMIZED | I1 | CNYRUBF | REFERENCE_2ATR | ALL | LONG | 127 | 0 | 1.2811 | 14.1468 | 0.1114 |
| OPTIMIZED | I1 | CNYRUBF | REFERENCE_2ATR | 2023 | LONG | 64 | 0 | 1.0788 | 2.1240 | 0.0332 |
| OPTIMIZED | I1 | CNYRUBF | REFERENCE_2ATR | 2024 | LONG | 63 | 0 | 1.5146 | 12.0229 | 0.1908 |
| OPTIMIZED | I1 | CNYRUBF | REFERENCE_2ATR | ALL | SHORT | 96 | 0 | 1.4217 | 17.4274 | 0.1815 |
| OPTIMIZED | I1 | CNYRUBF | REFERENCE_2ATR | 2023 | SHORT | 35 | 0 | 1.6968 | 10.1593 | 0.2903 |
| OPTIMIZED | I1 | CNYRUBF | REFERENCE_2ATR | 2024 | SHORT | 61 | 0 | 1.2718 | 7.2682 | 0.1192 |
| OPTIMIZED | I1 | GLDRUBF | ACTUAL_INITIAL_RISK | ALL | LONG | 129 | 0 | 1.0295 | 2.8540 | 0.0221 |
| OPTIMIZED | I1 | GLDRUBF | ACTUAL_INITIAL_RISK | 2023 | LONG | 36 | 0 | 1.0884 | 2.3114 | 0.0642 |
| OPTIMIZED | I1 | GLDRUBF | ACTUAL_INITIAL_RISK | 2024 | LONG | 93 | 0 | 1.0077 | 0.5426 | 0.0058 |
| OPTIMIZED | I1 | GLDRUBF | ACTUAL_INITIAL_RISK | ALL | SHORT | 61 | 0 | 1.6885 | 26.3348 | 0.4317 |
| OPTIMIZED | I1 | GLDRUBF | ACTUAL_INITIAL_RISK | 2023 | SHORT | 19 | 0 | 1.4751 | 5.2603 | 0.2769 |
| OPTIMIZED | I1 | GLDRUBF | ACTUAL_INITIAL_RISK | 2024 | SHORT | 42 | 0 | 1.7755 | 21.0745 | 0.5018 |
| OPTIMIZED | I1 | GLDRUBF | REFERENCE_2ATR | ALL | LONG | 129 | 0 | 1.0849 | 4.3312 | 0.0336 |
| OPTIMIZED | I1 | GLDRUBF | REFERENCE_2ATR | 2023 | LONG | 36 | 0 | 0.7488 | -4.1263 | -0.1146 |
| OPTIMIZED | I1 | GLDRUBF | REFERENCE_2ATR | 2024 | LONG | 93 | 0 | 1.2445 | 8.4575 | 0.0909 |
| OPTIMIZED | I1 | GLDRUBF | REFERENCE_2ATR | ALL | SHORT | 61 | 0 | 1.7827 | 16.1198 | 0.2643 |
| OPTIMIZED | I1 | GLDRUBF | REFERENCE_2ATR | 2023 | SHORT | 19 | 0 | 2.0631 | 6.9219 | 0.3643 |
| OPTIMIZED | I1 | GLDRUBF | REFERENCE_2ATR | 2024 | SHORT | 42 | 0 | 1.6531 | 9.1979 | 0.2190 |
| OPTIMIZED | I1 | IMOEXF | ACTUAL_INITIAL_RISK | ALL | LONG | 62 | 1 | 1.6028 | 25.1648 | 0.4059 |
| OPTIMIZED | I1 | IMOEXF | ACTUAL_INITIAL_RISK | 2023 | LONG | 2 | 0 | — | 0.6812 | 0.3406 |
| OPTIMIZED | I1 | IMOEXF | ACTUAL_INITIAL_RISK | 2024 | LONG | 60 | 1 | 1.5865 | 24.4836 | 0.4081 |
| OPTIMIZED | I1 | IMOEXF | ACTUAL_INITIAL_RISK | ALL | SHORT | 105 | 0 | 1.0526 | 3.8407 | 0.0366 |
| OPTIMIZED | I1 | IMOEXF | ACTUAL_INITIAL_RISK | 2023 | SHORT | 9 | 0 | 0.4180 | -4.0499 | -0.4500 |
| OPTIMIZED | I1 | IMOEXF | ACTUAL_INITIAL_RISK | 2024 | SHORT | 96 | 0 | 1.1196 | 7.8906 | 0.0822 |
| OPTIMIZED | I1 | IMOEXF | REFERENCE_2ATR | ALL | LONG | 62 | 1 | 1.2160 | 4.6958 | 0.0757 |
| OPTIMIZED | I1 | IMOEXF | REFERENCE_2ATR | 2023 | LONG | 2 | 0 | — | 0.6690 | 0.3345 |
| OPTIMIZED | I1 | IMOEXF | REFERENCE_2ATR | 2024 | LONG | 60 | 1 | 1.1852 | 4.0268 | 0.0671 |
| OPTIMIZED | I1 | IMOEXF | REFERENCE_2ATR | ALL | SHORT | 105 | 0 | 0.8244 | -7.7803 | -0.0741 |
| OPTIMIZED | I1 | IMOEXF | REFERENCE_2ATR | 2023 | SHORT | 9 | 0 | 0.8177 | -0.5403 | -0.0600 |
| OPTIMIZED | I1 | IMOEXF | REFERENCE_2ATR | 2024 | SHORT | 96 | 0 | 0.8249 | -7.2400 | -0.0754 |
| OPTIMIZED | I2 | ALL_FOUR | ACTUAL_INITIAL_RISK | ALL | LONG | 611 | 1 | 0.9471 | -30.4592 | -0.0499 |
| OPTIMIZED | I2 | ALL_FOUR | ACTUAL_INITIAL_RISK | 2023 | LONG | 240 | 0 | 0.8994 | -22.2799 | -0.0928 |
| OPTIMIZED | I2 | ALL_FOUR | ACTUAL_INITIAL_RISK | 2024 | LONG | 371 | 1 | 0.9769 | -8.1793 | -0.0220 |
| OPTIMIZED | I2 | ALL_FOUR | ACTUAL_INITIAL_RISK | ALL | SHORT | 463 | 0 | 1.7274 | 324.5872 | 0.7011 |
| OPTIMIZED | I2 | ALL_FOUR | ACTUAL_INITIAL_RISK | 2023 | SHORT | 132 | 0 | 1.6386 | 86.5317 | 0.6555 |
| OPTIMIZED | I2 | ALL_FOUR | ACTUAL_INITIAL_RISK | 2024 | SHORT | 331 | 0 | 1.7661 | 238.0555 | 0.7192 |
| OPTIMIZED | I2 | ALL_FOUR | REFERENCE_2ATR | ALL | LONG | 611 | 1 | 1.2821 | 38.6318 | 0.0632 |
| OPTIMIZED | I2 | ALL_FOUR | REFERENCE_2ATR | 2023 | LONG | 240 | 0 | 1.2627 | 15.5074 | 0.0646 |
| OPTIMIZED | I2 | ALL_FOUR | REFERENCE_2ATR | 2024 | LONG | 371 | 1 | 1.2967 | 23.1244 | 0.0623 |
| OPTIMIZED | I2 | ALL_FOUR | REFERENCE_2ATR | ALL | SHORT | 463 | 0 | 1.5025 | 51.1521 | 0.1105 |
| OPTIMIZED | I2 | ALL_FOUR | REFERENCE_2ATR | 2023 | SHORT | 132 | 0 | 2.1450 | 32.9324 | 0.2495 |
| OPTIMIZED | I2 | ALL_FOUR | REFERENCE_2ATR | 2024 | SHORT | 331 | 0 | 1.2495 | 18.2197 | 0.0550 |
| OPTIMIZED | I2 | USDRUBF | ACTUAL_INITIAL_RISK | ALL | LONG | 193 | 0 | 1.2135 | 34.4261 | 0.1784 |
| OPTIMIZED | I2 | USDRUBF | ACTUAL_INITIAL_RISK | 2023 | LONG | 112 | 0 | 1.2073 | 19.5330 | 0.1744 |
| OPTIMIZED | I2 | USDRUBF | ACTUAL_INITIAL_RISK | 2024 | LONG | 81 | 0 | 1.2221 | 14.8931 | 0.1839 |
| OPTIMIZED | I2 | USDRUBF | ACTUAL_INITIAL_RISK | ALL | SHORT | 128 | 0 | 1.7486 | 83.3104 | 0.6509 |
| OPTIMIZED | I2 | USDRUBF | ACTUAL_INITIAL_RISK | 2023 | SHORT | 50 | 0 | 2.5331 | 53.7986 | 1.0760 |
| OPTIMIZED | I2 | USDRUBF | ACTUAL_INITIAL_RISK | 2024 | SHORT | 78 | 0 | 1.3873 | 29.5118 | 0.3784 |
| OPTIMIZED | I2 | USDRUBF | REFERENCE_2ATR | ALL | LONG | 193 | 0 | 1.6606 | 25.5891 | 0.1326 |
| OPTIMIZED | I2 | USDRUBF | REFERENCE_2ATR | 2023 | LONG | 112 | 0 | 1.8804 | 20.6984 | 0.1848 |
| OPTIMIZED | I2 | USDRUBF | REFERENCE_2ATR | 2024 | LONG | 81 | 0 | 1.3212 | 4.8907 | 0.0604 |
| OPTIMIZED | I2 | USDRUBF | REFERENCE_2ATR | ALL | SHORT | 128 | 0 | 1.5016 | 15.0755 | 0.1178 |
| OPTIMIZED | I2 | USDRUBF | REFERENCE_2ATR | 2023 | SHORT | 50 | 0 | 2.6174 | 16.5079 | 0.3302 |
| OPTIMIZED | I2 | USDRUBF | REFERENCE_2ATR | 2024 | SHORT | 78 | 0 | 0.9278 | -1.4324 | -0.0184 |
| OPTIMIZED | I2 | CNYRUBF | ACTUAL_INITIAL_RISK | ALL | LONG | 167 | 0 | 0.7910 | -30.7108 | -0.1839 |
| OPTIMIZED | I2 | CNYRUBF | ACTUAL_INITIAL_RISK | 2023 | LONG | 80 | 0 | 0.7353 | -18.6615 | -0.2333 |
| OPTIMIZED | I2 | CNYRUBF | ACTUAL_INITIAL_RISK | 2024 | LONG | 87 | 0 | 0.8424 | -12.0494 | -0.1385 |
| OPTIMIZED | I2 | CNYRUBF | ACTUAL_INITIAL_RISK | ALL | SHORT | 122 | 0 | 1.2977 | 31.5816 | 0.2589 |
| OPTIMIZED | I2 | CNYRUBF | ACTUAL_INITIAL_RISK | 2023 | SHORT | 45 | 0 | 2.4860 | 57.4017 | 1.2756 |
| OPTIMIZED | I2 | CNYRUBF | ACTUAL_INITIAL_RISK | 2024 | SHORT | 77 | 0 | 0.6172 | -25.8201 | -0.3353 |
| OPTIMIZED | I2 | CNYRUBF | REFERENCE_2ATR | ALL | LONG | 167 | 0 | 1.0236 | 1.0170 | 0.0061 |
| OPTIMIZED | I2 | CNYRUBF | REFERENCE_2ATR | 2023 | LONG | 80 | 0 | 0.8603 | -3.2371 | -0.0405 |
| OPTIMIZED | I2 | CNYRUBF | REFERENCE_2ATR | 2024 | LONG | 87 | 0 | 1.2146 | 4.2542 | 0.0489 |
| OPTIMIZED | I2 | CNYRUBF | REFERENCE_2ATR | ALL | SHORT | 122 | 0 | 1.4367 | 12.6941 | 0.1040 |
| OPTIMIZED | I2 | CNYRUBF | REFERENCE_2ATR | 2023 | SHORT | 45 | 0 | 1.8655 | 9.2003 | 0.2045 |
| OPTIMIZED | I2 | CNYRUBF | REFERENCE_2ATR | 2024 | SHORT | 77 | 0 | 1.1894 | 3.4938 | 0.0454 |
| OPTIMIZED | I2 | GLDRUBF | ACTUAL_INITIAL_RISK | ALL | LONG | 176 | 0 | 0.7957 | -40.7109 | -0.2313 |
| OPTIMIZED | I2 | GLDRUBF | ACTUAL_INITIAL_RISK | 2023 | LONG | 46 | 0 | 0.5929 | -22.6921 | -0.4933 |
| OPTIMIZED | I2 | GLDRUBF | ACTUAL_INITIAL_RISK | 2024 | LONG | 130 | 0 | 0.8745 | -18.0188 | -0.1386 |
| OPTIMIZED | I2 | GLDRUBF | ACTUAL_INITIAL_RISK | ALL | SHORT | 76 | 0 | 2.0910 | 99.7132 | 1.3120 |
| OPTIMIZED | I2 | GLDRUBF | ACTUAL_INITIAL_RISK | 2023 | SHORT | 27 | 0 | 0.5954 | -21.7589 | -0.8059 |
| OPTIMIZED | I2 | GLDRUBF | ACTUAL_INITIAL_RISK | 2024 | SHORT | 49 | 0 | 4.2296 | 121.4721 | 2.4790 |
| OPTIMIZED | I2 | GLDRUBF | REFERENCE_2ATR | ALL | LONG | 176 | 0 | 1.1917 | 7.2702 | 0.0413 |
| OPTIMIZED | I2 | GLDRUBF | REFERENCE_2ATR | 2023 | LONG | 46 | 0 | 0.8319 | -2.0226 | -0.0440 |
| OPTIMIZED | I2 | GLDRUBF | REFERENCE_2ATR | 2024 | LONG | 130 | 0 | 1.3589 | 9.2928 | 0.0715 |
| OPTIMIZED | I2 | GLDRUBF | REFERENCE_2ATR | ALL | SHORT | 76 | 0 | 2.3159 | 19.5844 | 0.2577 |
| OPTIMIZED | I2 | GLDRUBF | REFERENCE_2ATR | 2023 | SHORT | 27 | 0 | 1.9165 | 6.0857 | 0.2254 |
| OPTIMIZED | I2 | GLDRUBF | REFERENCE_2ATR | 2024 | SHORT | 49 | 0 | 2.6375 | 13.4987 | 0.2755 |
| OPTIMIZED | I2 | IMOEXF | ACTUAL_INITIAL_RISK | ALL | LONG | 75 | 1 | 1.0955 | 6.5365 | 0.0872 |
| OPTIMIZED | I2 | IMOEXF | ACTUAL_INITIAL_RISK | 2023 | LONG | 2 | 0 | 0.5407 | -0.4593 | -0.2297 |
| OPTIMIZED | I2 | IMOEXF | ACTUAL_INITIAL_RISK | 2024 | LONG | 73 | 1 | 1.1037 | 6.9958 | 0.0958 |
| OPTIMIZED | I2 | IMOEXF | ACTUAL_INITIAL_RISK | ALL | SHORT | 137 | 0 | 1.8000 | 109.9821 | 0.8028 |
| OPTIMIZED | I2 | IMOEXF | ACTUAL_INITIAL_RISK | 2023 | SHORT | 10 | 0 | 0.6363 | -2.9098 | -0.2910 |
| OPTIMIZED | I2 | IMOEXF | ACTUAL_INITIAL_RISK | 2024 | SHORT | 127 | 0 | 1.8720 | 112.8918 | 0.8889 |
| OPTIMIZED | I2 | IMOEXF | REFERENCE_2ATR | ALL | LONG | 75 | 1 | 1.2749 | 4.7554 | 0.0634 |
| OPTIMIZED | I2 | IMOEXF | REFERENCE_2ATR | 2023 | LONG | 2 | 0 | 1.2254 | 0.0687 | 0.0344 |
| OPTIMIZED | I2 | IMOEXF | REFERENCE_2ATR | 2024 | LONG | 73 | 1 | 1.2758 | 4.6867 | 0.0642 |
| OPTIMIZED | I2 | IMOEXF | REFERENCE_2ATR | ALL | SHORT | 137 | 0 | 1.1367 | 3.7982 | 0.0277 |
| OPTIMIZED | I2 | IMOEXF | REFERENCE_2ATR | 2023 | SHORT | 10 | 0 | 1.8858 | 1.1385 | 0.1139 |
| OPTIMIZED | I2 | IMOEXF | REFERENCE_2ATR | 2024 | SHORT | 127 | 0 | 1.1003 | 2.6596 | 0.0209 |
| OPTIMIZED | I3 | ALL_FOUR | ACTUAL_INITIAL_RISK | ALL | LONG | 462 | 1 | 1.3926 | 125.6025 | 0.2719 |
| OPTIMIZED | I3 | ALL_FOUR | ACTUAL_INITIAL_RISK | 2023 | LONG | 180 | 0 | 1.6441 | 76.2895 | 0.4238 |
| OPTIMIZED | I3 | ALL_FOUR | ACTUAL_INITIAL_RISK | 2024 | LONG | 282 | 1 | 1.2447 | 49.3131 | 0.1749 |
| OPTIMIZED | I3 | ALL_FOUR | ACTUAL_INITIAL_RISK | ALL | SHORT | 362 | 0 | 1.3102 | 76.9138 | 0.2125 |
| OPTIMIZED | I3 | ALL_FOUR | ACTUAL_INITIAL_RISK | 2023 | SHORT | 102 | 0 | 1.9120 | 56.3673 | 0.5526 |
| OPTIMIZED | I3 | ALL_FOUR | ACTUAL_INITIAL_RISK | 2024 | SHORT | 260 | 0 | 1.1104 | 20.5465 | 0.0790 |
| OPTIMIZED | I3 | ALL_FOUR | REFERENCE_2ATR | ALL | LONG | 462 | 1 | 1.3575 | 63.2213 | 0.1368 |
| OPTIMIZED | I3 | ALL_FOUR | REFERENCE_2ATR | 2023 | LONG | 180 | 0 | 1.4966 | 34.9839 | 0.1944 |
| OPTIMIZED | I3 | ALL_FOUR | REFERENCE_2ATR | 2024 | LONG | 282 | 1 | 1.2654 | 28.2373 | 0.1001 |
| OPTIMIZED | I3 | ALL_FOUR | REFERENCE_2ATR | ALL | SHORT | 362 | 0 | 1.3394 | 48.0533 | 0.1327 |
| OPTIMIZED | I3 | ALL_FOUR | REFERENCE_2ATR | 2023 | SHORT | 102 | 0 | 2.2016 | 42.2338 | 0.4141 |
| OPTIMIZED | I3 | ALL_FOUR | REFERENCE_2ATR | 2024 | SHORT | 260 | 0 | 1.0547 | 5.8195 | 0.0224 |
| OPTIMIZED | I3 | USDRUBF | ACTUAL_INITIAL_RISK | ALL | LONG | 140 | 0 | 1.8748 | 80.2461 | 0.5732 |
| OPTIMIZED | I3 | USDRUBF | ACTUAL_INITIAL_RISK | 2023 | LONG | 76 | 0 | 2.4448 | 67.4603 | 0.8876 |
| OPTIMIZED | I3 | USDRUBF | ACTUAL_INITIAL_RISK | 2024 | LONG | 64 | 0 | 1.2839 | 12.7858 | 0.1998 |
| OPTIMIZED | I3 | USDRUBF | ACTUAL_INITIAL_RISK | ALL | SHORT | 99 | 0 | 1.3664 | 23.8057 | 0.2405 |
| OPTIMIZED | I3 | USDRUBF | ACTUAL_INITIAL_RISK | 2023 | SHORT | 39 | 0 | 2.9634 | 37.3433 | 0.9575 |
| OPTIMIZED | I3 | USDRUBF | ACTUAL_INITIAL_RISK | 2024 | SHORT | 60 | 0 | 0.7054 | -13.5376 | -0.2256 |
| OPTIMIZED | I3 | USDRUBF | REFERENCE_2ATR | ALL | LONG | 140 | 0 | 1.8304 | 43.3201 | 0.3094 |
| OPTIMIZED | I3 | USDRUBF | REFERENCE_2ATR | 2023 | LONG | 76 | 0 | 2.4275 | 38.1719 | 0.5023 |
| OPTIMIZED | I3 | USDRUBF | REFERENCE_2ATR | 2024 | LONG | 64 | 0 | 1.2025 | 5.1482 | 0.0804 |
| OPTIMIZED | I3 | USDRUBF | REFERENCE_2ATR | ALL | SHORT | 99 | 0 | 1.5021 | 19.2650 | 0.1946 |
| OPTIMIZED | I3 | USDRUBF | REFERENCE_2ATR | 2023 | SHORT | 39 | 0 | 3.0914 | 24.8859 | 0.6381 |
| OPTIMIZED | I3 | USDRUBF | REFERENCE_2ATR | 2024 | SHORT | 60 | 0 | 0.7877 | -5.6209 | -0.0937 |
| OPTIMIZED | I3 | CNYRUBF | ACTUAL_INITIAL_RISK | ALL | LONG | 129 | 0 | 1.2254 | 19.2842 | 0.1495 |
| OPTIMIZED | I3 | CNYRUBF | ACTUAL_INITIAL_RISK | 2023 | LONG | 66 | 0 | 1.1377 | 6.2245 | 0.0943 |
| OPTIMIZED | I3 | CNYRUBF | ACTUAL_INITIAL_RISK | 2024 | LONG | 63 | 0 | 1.3238 | 13.0596 | 0.2073 |
| OPTIMIZED | I3 | CNYRUBF | ACTUAL_INITIAL_RISK | ALL | SHORT | 96 | 0 | 1.3272 | 22.5837 | 0.2352 |
| OPTIMIZED | I3 | CNYRUBF | ACTUAL_INITIAL_RISK | 2023 | SHORT | 35 | 0 | 1.7622 | 18.3003 | 0.5229 |
| OPTIMIZED | I3 | CNYRUBF | ACTUAL_INITIAL_RISK | 2024 | SHORT | 61 | 0 | 1.0952 | 4.2833 | 0.0702 |
| OPTIMIZED | I3 | CNYRUBF | REFERENCE_2ATR | ALL | LONG | 129 | 0 | 1.2252 | 11.5705 | 0.0897 |
| OPTIMIZED | I3 | CNYRUBF | REFERENCE_2ATR | 2023 | LONG | 66 | 0 | 0.9804 | -0.5521 | -0.0084 |
| OPTIMIZED | I3 | CNYRUBF | REFERENCE_2ATR | 2024 | LONG | 63 | 0 | 1.5211 | 12.1227 | 0.1924 |
| OPTIMIZED | I3 | CNYRUBF | REFERENCE_2ATR | ALL | SHORT | 96 | 0 | 1.4919 | 19.3714 | 0.2018 |
| OPTIMIZED | I3 | CNYRUBF | REFERENCE_2ATR | 2023 | SHORT | 35 | 0 | 1.7761 | 10.8105 | 0.3089 |
| OPTIMIZED | I3 | CNYRUBF | REFERENCE_2ATR | 2024 | SHORT | 61 | 0 | 1.3364 | 8.5608 | 0.1403 |
| OPTIMIZED | I3 | GLDRUBF | ACTUAL_INITIAL_RISK | ALL | LONG | 131 | 0 | 0.9883 | -1.1852 | -0.0090 |
| OPTIMIZED | I3 | GLDRUBF | ACTUAL_INITIAL_RISK | 2023 | LONG | 36 | 0 | 1.0723 | 1.9185 | 0.0533 |
| OPTIMIZED | I3 | GLDRUBF | ACTUAL_INITIAL_RISK | 2024 | LONG | 95 | 0 | 0.9583 | -3.1037 | -0.0327 |
| OPTIMIZED | I3 | GLDRUBF | ACTUAL_INITIAL_RISK | ALL | SHORT | 61 | 0 | 1.7151 | 28.0243 | 0.4594 |
| OPTIMIZED | I3 | GLDRUBF | ACTUAL_INITIAL_RISK | 2023 | SHORT | 19 | 0 | 1.4039 | 4.7736 | 0.2512 |
| OPTIMIZED | I3 | GLDRUBF | ACTUAL_INITIAL_RISK | 2024 | SHORT | 42 | 0 | 1.8494 | 23.2507 | 0.5536 |
| OPTIMIZED | I3 | GLDRUBF | REFERENCE_2ATR | ALL | LONG | 131 | 0 | 1.0684 | 3.5326 | 0.0270 |
| OPTIMIZED | I3 | GLDRUBF | REFERENCE_2ATR | 2023 | LONG | 36 | 0 | 0.7882 | -3.3048 | -0.0918 |
| OPTIMIZED | I3 | GLDRUBF | REFERENCE_2ATR | 2024 | LONG | 95 | 0 | 1.1895 | 6.8374 | 0.0720 |
| OPTIMIZED | I3 | GLDRUBF | REFERENCE_2ATR | ALL | SHORT | 61 | 0 | 1.7963 | 16.2755 | 0.2668 |
| OPTIMIZED | I3 | GLDRUBF | REFERENCE_2ATR | 2023 | SHORT | 19 | 0 | 2.1136 | 7.0776 | 0.3725 |
| OPTIMIZED | I3 | GLDRUBF | REFERENCE_2ATR | 2024 | SHORT | 42 | 0 | 1.6531 | 9.1979 | 0.2190 |
| OPTIMIZED | I3 | IMOEXF | ACTUAL_INITIAL_RISK | ALL | LONG | 62 | 1 | 1.6529 | 27.2574 | 0.4396 |
| OPTIMIZED | I3 | IMOEXF | ACTUAL_INITIAL_RISK | 2023 | LONG | 2 | 0 | — | 0.6861 | 0.3431 |
| OPTIMIZED | I3 | IMOEXF | ACTUAL_INITIAL_RISK | 2024 | LONG | 60 | 1 | 1.6365 | 26.5713 | 0.4429 |
| OPTIMIZED | I3 | IMOEXF | ACTUAL_INITIAL_RISK | ALL | SHORT | 106 | 0 | 1.0334 | 2.5001 | 0.0236 |
| OPTIMIZED | I3 | IMOEXF | ACTUAL_INITIAL_RISK | 2023 | SHORT | 9 | 0 | 0.4180 | -4.0499 | -0.4500 |
| OPTIMIZED | I3 | IMOEXF | ACTUAL_INITIAL_RISK | 2024 | SHORT | 97 | 0 | 1.0966 | 6.5500 | 0.0675 |
| OPTIMIZED | I3 | IMOEXF | REFERENCE_2ATR | ALL | LONG | 62 | 1 | 1.2217 | 4.7981 | 0.0774 |
| OPTIMIZED | I3 | IMOEXF | REFERENCE_2ATR | 2023 | LONG | 2 | 0 | — | 0.6690 | 0.3345 |
| OPTIMIZED | I3 | IMOEXF | REFERENCE_2ATR | 2024 | LONG | 60 | 1 | 1.1908 | 4.1291 | 0.0688 |
| OPTIMIZED | I3 | IMOEXF | REFERENCE_2ATR | ALL | SHORT | 106 | 0 | 0.8419 | -6.8587 | -0.0647 |
| OPTIMIZED | I3 | IMOEXF | REFERENCE_2ATR | 2023 | SHORT | 9 | 0 | 0.8177 | -0.5403 | -0.0600 |
| OPTIMIZED | I3 | IMOEXF | REFERENCE_2ATR | 2024 | SHORT | 97 | 0 | 0.8437 | -6.3183 | -0.0651 |

## Проверки и остановка

Полные trade/entry/Stop журналы, риск, крупные победители, годовые OPEN и отрицательные результаты сохранены. AUDIT_RESULTS.json содержит отдельный stdlib replay и проверку всех полей журналов и диагностики; независимость алгоритмическая, автор тот же. Внешний аудит остаётся PENDING. REPEATABILITY.json подтверждает два полных побайтных повтора, ARTIFACT_SHA256.json — состав и SHA артефактов. Optimization, Robustness, Walk Forward, TRUE OOS и LIVE не выполнялись. Один Draft PR, без Merge и Auto-Merge; STOP для внешнего аудита и решения пользователя.

