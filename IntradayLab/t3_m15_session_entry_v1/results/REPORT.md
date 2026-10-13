# T3/M15 Session Entry v1 — 2023–2024

**GROSS_ONLY / COSTS_DEFERRED / NOT_LIVE_READY**. 2023–2024 development-exposed; это не новый независимый Walk Forward.

Цель полного pooled Gross PF ≥2,0: не достигнута (0/4 вариантов T1/T2).
Число положительных календарных месяцев увеличилось: BASELINE/T1, OPTIMIZED/T1.

## Все шесть полных replay

| version | rule | closed_trades | open_positions_at_period_end | gross_PF | gross_R | expectancy_R | max_drawdown_closed_R | max_consecutive_losses | positive_months | negative_months | zero_months | positive_month_share | worst_month | worst_month_R | max_losing_month_streak |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BASELINE | CONTROL | 741 | 1 | 1.4542 | 144.4112 | 0.1949 | 23.6765 | 14 | 15 | 9 | 0 | 0.6250 | 2023-08 | -8.4431 | 5 |
| BASELINE | T1 | 568 | 1 | 1.5475 | 135.5203 | 0.2386 | 18.6022 | 10 | 17 | 7 | 0 | 0.7083 | 2023-08 | -10.3887 | 2 |
| BASELINE | T2 | 729 | 1 | 1.4480 | 141.1740 | 0.1937 | 25.0437 | 13 | 15 | 9 | 0 | 0.6250 | 2023-08 | -10.6967 | 5 |
| OPTIMIZED | CONTROL | 701 | 1 | 1.5462 | 178.7198 | 0.2549 | 26.1261 | 13 | 17 | 7 | 0 | 0.7083 | 2023-08 | -9.4074 | 2 |
| OPTIMIZED | T1 | 549 | 1 | 1.6784 | 175.7446 | 0.3201 | 17.5995 | 10 | 18 | 6 | 0 | 0.7500 | 2023-08 | -10.7929 | 2 |
| OPTIMIZED | T2 | 694 | 1 | 1.5299 | 172.8698 | 0.2491 | 25.6853 | 12 | 17 | 7 | 0 | 0.7083 | 2023-08 | -12.1141 | 2 |

## По годам

CLOSED относятся к году московского exit-bar Close, как в исходной модели. OPEN — снимок на последнем наблюдаемом закрытии перед годовой границей; позиция продолжает жить в полном replay. На конце периода terminal OPEN исключены из CLOSED PF/R.

| version | rule | year | closed_trades | open_positions_at_period_end | gross_PF | gross_R | expectancy_R | positive_months | negative_months | max_drawdown_closed_R |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BASELINE | CONTROL | 2023 | 256 | 0 | 1.9482 | 94.2049 | 0.3680 | 9 | 3 | 13.2041 |
| BASELINE | CONTROL | 2024 | 485 | 1 | 1.2296 | 50.2063 | 0.1035 | 6 | 6 | 23.6765 |
| BASELINE | T1 | 2023 | 197 | 0 | 1.9768 | 77.9175 | 0.3955 | 9 | 3 | 13.5948 |
| BASELINE | T1 | 2024 | 371 | 1 | 1.3434 | 57.6028 | 0.1553 | 8 | 4 | 18.6022 |
| BASELINE | T2 | 2023 | 251 | 0 | 1.9206 | 91.7261 | 0.3654 | 9 | 3 | 15.4577 |
| BASELINE | T2 | 2024 | 478 | 1 | 1.2295 | 49.4480 | 0.1034 | 6 | 6 | 25.0437 |
| OPTIMIZED | CONTROL | 2023 | 243 | 0 | 1.9252 | 98.6178 | 0.4058 | 9 | 3 | 14.6437 |
| OPTIMIZED | CONTROL | 2024 | 458 | 1 | 1.3631 | 80.1020 | 0.1749 | 8 | 4 | 26.1261 |
| OPTIMIZED | T1 | 2023 | 192 | 0 | 2.1086 | 93.7488 | 0.4883 | 9 | 3 | 14.2289 |
| OPTIMIZED | T1 | 2024 | 357 | 1 | 1.4699 | 81.9958 | 0.2297 | 9 | 3 | 17.5995 |
| OPTIMIZED | T2 | 2023 | 240 | 0 | 1.8960 | 95.5274 | 0.3980 | 9 | 3 | 17.3503 |
| OPTIMIZED | T2 | 2024 | 454 | 1 | 1.3521 | 77.3424 | 0.1704 | 8 | 4 | 25.6853 |

## Концентрация и 2024 без ноября — только диагностика

| version | rule | top5_positive_R | top5_share_positive_R | top10_positive_R | top10_share_positive_R | gross_R_without_top5 | gross_R_without_top10 | gross_PF_without_top5 | gross_PF_without_top10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BASELINE | CONTROL | 37.3086 | 0.0807 | 66.2192 | 0.1432 | 107.1027 | 78.1920 | 1.3368 | 1.2459 |
| BASELINE | T1 | 37.3086 | 0.0974 | 66.0929 | 0.1725 | 98.2117 | 69.4273 | 1.3968 | 1.2805 |
| BASELINE | T2 | 37.3086 | 0.0818 | 66.2192 | 0.1451 | 103.8655 | 74.9548 | 1.3296 | 1.2378 |
| OPTIMIZED | CONTROL | 48.7357 | 0.0963 | 81.6315 | 0.1613 | 129.9841 | 97.0883 | 1.3972 | 1.2967 |
| OPTIMIZED | T1 | 48.7357 | 0.1121 | 81.6315 | 0.1877 | 127.0089 | 94.1132 | 1.4903 | 1.3633 |
| OPTIMIZED | T2 | 48.7357 | 0.0976 | 81.6315 | 0.1635 | 124.1341 | 91.2383 | 1.3805 | 1.2797 |

| version | rule | november_closed | november_R | full_PF | ex_november_closed | ex_november_PF | ex_november_R | ex_november_drawdown_R |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BASELINE | CONTROL | 44 | 50.5287 | 1.2296 | 441 | 0.9984 | -0.3224 | 23.6765 |
| BASELINE | T1 | 33 | 44.1940 | 1.3434 | 338 | 1.0839 | 13.4088 | 18.6022 |
| BASELINE | T2 | 43 | 50.6987 | 1.2295 | 435 | 0.9938 | -1.2507 | 25.0437 |
| OPTIMIZED | CONTROL | 39 | 54.1860 | 1.3631 | 419 | 1.1232 | 25.9160 | 26.1261 |
| OPTIMIZED | T1 | 31 | 46.1908 | 1.4699 | 326 | 1.2168 | 35.8050 | 17.5995 |
| OPTIMIZED | T2 | 38 | 54.8657 | 1.3521 | 416 | 1.1070 | 22.4767 | 25.6853 |

Drawdown — сумма CLOSED R в порядке exit_time/instrument/trade_id с начальным нулём. Это не денежная и не mark-to-market просадка. Ни ноябрь, ни крупные победители не удаляются из основной экономики. top_winners.csv сохраняет идентификаторы top5/top10. losing_month_runs.csv содержит все серии отрицательных месяцев.

## Исходные сигналы, запреты и занятость

original_signals = accepted_entries + rule_forbidden_signals + allowed_skipped_position_busy. Запрет правила и занятость могут пересекаться: forbidden_and_busy показан отдельно. Каждый вариант заново обрабатывает все исходные сигналы, включая сигналы, занятые в CONTROL.

| version | rule | year | original_signals | rule_forbidden_signals | rule_forbidden_when_flat | rule_forbidden_and_busy | accepted_entries | allowed_skipped_position_busy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BASELINE | CONTROL | ALL | 2017 | 0 | 0 | 0 | 742 | 1275 |
| BASELINE | CONTROL | 2023 | 698 | 0 | 0 | 0 | 256 | 442 |
| BASELINE | CONTROL | 2024 | 1319 | 0 | 0 | 0 | 486 | 833 |
| BASELINE | T1 | ALL | 2017 | 621 | 377 | 244 | 569 | 827 |
| BASELINE | T1 | 2023 | 698 | 202 | 128 | 74 | 197 | 299 |
| BASELINE | T1 | 2024 | 1319 | 419 | 249 | 170 | 372 | 528 |
| BASELINE | T2 | ALL | 2017 | 54 | 30 | 24 | 730 | 1233 |
| BASELINE | T2 | 2023 | 698 | 26 | 13 | 13 | 251 | 421 |
| BASELINE | T2 | 2024 | 1319 | 28 | 17 | 11 | 479 | 812 |
| OPTIMIZED | CONTROL | ALL | 2017 | 0 | 0 | 0 | 702 | 1315 |
| OPTIMIZED | CONTROL | 2023 | 698 | 0 | 0 | 0 | 243 | 455 |
| OPTIMIZED | CONTROL | 2024 | 1319 | 0 | 0 | 0 | 459 | 860 |
| OPTIMIZED | T1 | ALL | 2017 | 621 | 337 | 284 | 550 | 846 |
| OPTIMIZED | T1 | 2023 | 698 | 202 | 110 | 92 | 192 | 304 |
| OPTIMIZED | T1 | 2024 | 1319 | 419 | 227 | 192 | 358 | 542 |
| OPTIMIZED | T2 | ALL | 2017 | 54 | 25 | 29 | 695 | 1268 |
| OPTIMIZED | T2 | 2023 | 698 | 26 | 11 | 15 | 240 | 432 |
| OPTIMIZED | T2 | 2024 | 1319 | 28 | 14 | 14 | 455 | 836 |

## Длительность, частота и наблюдаемые ночные разрывы

Годовая длительность — CLOSED exit-year cohort; частота — entry-year cohort, включая terminal OPEN. Знаменатели частоты — реально наблюдаемые московские даты Close, отдельно общий календарь портфеля и сумма инструмент-дней. Ночной gap для диагностики: >15 минут между закрытиями, даты соответствующих исходных Open различаются. Никаких искусственных свечей и официальной классификации перерыва.

| version | rule | year | holding_minutes_mean | holding_minutes_median | holding_minutes_p90 | accepted_entries | entries_per_observed_portfolio_day | closed_with_observed_overnight_gap | closed_with_observed_overnight_gap_share | total_observed_overnight_gap_exposures |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BASELINE | CONTROL | ALL | 557.4696 | 240.0000 | 1170.0000 | 742 | 1.1948 | 206 | 0.2780 | 206 |
| BASELINE | CONTROL | 2023 | 568.9453 | 255.0000 | 1162.5000 | 256 | 0.8285 | 72 | 0.2812 | 72 |
| BASELINE | CONTROL | 2024 | 551.4124 | 210.0000 | 1164.0000 | 486 | 1.5577 | 134 | 0.2763 | 134 |
| BASELINE | T1 | ALL | 433.7588 | 195.0000 | 1114.5000 | 569 | 0.9163 | 97 | 0.1708 | 97 |
| BASELINE | T1 | 2023 | 464.9239 | 210.0000 | 1158.0000 | 197 | 0.6375 | 34 | 0.1726 | 34 |
| BASELINE | T1 | 2024 | 417.2102 | 180.0000 | 1080.0000 | 372 | 1.1923 | 63 | 0.1698 | 63 |
| BASELINE | T2 | ALL | 563.4362 | 240.0000 | 1170.0000 | 730 | 1.1755 | 205 | 0.2812 | 205 |
| BASELINE | T2 | 2023 | 574.7809 | 255.0000 | 1185.0000 | 251 | 0.8123 | 71 | 0.2829 | 71 |
| BASELINE | T2 | 2024 | 557.4791 | 225.0000 | 1170.0000 | 479 | 1.5353 | 134 | 0.2803 | 134 |
| OPTIMIZED | CONTROL | ALL | 677.0114 | 300.0000 | 1365.0000 | 702 | 1.1304 | 236 | 0.3367 | 242 |
| OPTIMIZED | CONTROL | 2023 | 680.8025 | 315.0000 | 1380.0000 | 243 | 0.7864 | 82 | 0.3374 | 84 |
| OPTIMIZED | CONTROL | 2024 | 675.0000 | 300.0000 | 1324.5000 | 459 | 1.4712 | 154 | 0.3362 | 158 |
| OPTIMIZED | T1 | ALL | 560.6011 | 240.0000 | 1308.0000 | 550 | 0.8857 | 127 | 0.2313 | 131 |
| OPTIMIZED | T1 | 2023 | 598.9062 | 277.5000 | 1365.0000 | 192 | 0.6214 | 48 | 0.2500 | 48 |
| OPTIMIZED | T1 | 2024 | 540.0000 | 210.0000 | 1206.0000 | 358 | 1.1474 | 79 | 0.2213 | 83 |
| OPTIMIZED | T2 | ALL | 680.4899 | 300.0000 | 1365.0000 | 695 | 1.1192 | 235 | 0.3386 | 241 |
| OPTIMIZED | T2 | 2023 | 683.5000 | 315.0000 | 1380.0000 | 240 | 0.7767 | 81 | 0.3375 | 83 |
| OPTIMIZED | T2 | 2024 | 678.8987 | 292.5000 | 1330.5000 | 455 | 1.4583 | 154 | 0.3392 | 158 |

## Победители ≥2R и изменение последующих входов

Сопоставление — инструмент/направление/время исходного входа, а не последовательный trade_id. При совпавшем входе весь исходный Stop/выход/P&L обязан совпадать. trade_lineage.csv объясняет каждый пропавший вход; chronology_changes.csv показывает каждое изменение допуска/занятости; new_entries.csv содержит новые CLOSED и их убытки.

| version | rule | control_exit_year | control_large_winners_ge_2R | large_winners_preserved | large_winners_lost | lost_large_winner_R | lost_positive_R | removed_negative_R_volume | lost_entry_rule_blocked | lost_entry_busy_only | new_closed_entries | new_closed_losses | new_closed_gross_R | new_losses_R_volume |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BASELINE | T1 | ALL | 81 | 64 | 17 | 51.4249 | 85.8494 | 89.2934 | 203 | 0 | 30 | 22 | -12.3350 | 18.8446 |
| BASELINE | T1 | 2023 | 34 | 26 | 8 | 23.8409 | 37.4252 | 30.0203 | 74 | 0 | 15 | 12 | -8.8825 | 10.4322 |
| BASELINE | T1 | 2024 | 47 | 38 | 9 | 27.5840 | 48.4241 | 59.2731 | 129 | 0 | 15 | 10 | -3.4525 | 8.4124 |
| BASELINE | T2 | ALL | 81 | 80 | 1 | 3.3834 | 11.3599 | 13.5713 | 30 | 0 | 18 | 12 | -5.4486 | 10.7331 |
| BASELINE | T2 | 2023 | 34 | 34 | 0 | 0.0000 | 3.7310 | 4.6032 | 13 | 0 | 8 | 6 | -3.3511 | 4.8859 |
| BASELINE | T2 | 2024 | 47 | 46 | 1 | 3.3834 | 7.6289 | 8.9681 | 17 | 0 | 10 | 6 | -2.0975 | 5.8472 |
| OPTIMIZED | T1 | ALL | 90 | 73 | 17 | 50.3758 | 81.1991 | 87.4709 | 184 | 0 | 32 | 24 | -9.2469 | 19.2995 |
| OPTIMIZED | T1 | 2023 | 34 | 28 | 6 | 20.0113 | 33.0560 | 32.0062 | 66 | 0 | 15 | 11 | -3.8192 | 9.9738 |
| OPTIMIZED | T1 | 2024 | 56 | 45 | 11 | 30.3645 | 48.1431 | 55.4647 | 118 | 0 | 17 | 13 | -5.4278 | 9.3257 |
| OPTIMIZED | T2 | ALL | 90 | 88 | 2 | 8.3899 | 14.7083 | 11.9153 | 25 | 0 | 18 | 13 | -3.0570 | 10.9434 |
| OPTIMIZED | T2 | 2023 | 34 | 33 | 1 | 5.3059 | 8.1478 | 4.7909 | 11 | 0 | 8 | 6 | 0.2664 | 4.8087 |
| OPTIMIZED | T2 | 2024 | 56 | 55 | 1 | 3.0839 | 6.5605 | 7.1244 | 14 | 0 | 10 | 7 | -3.3234 | 6.1347 |

Сохранение победителей и ночные переносы — только ретроспективная диагностика. Прибыльный будущий перенос через полночь нельзя распознать при входе; он не используется как фильтр. Сравнивается полная экономика replay с новыми и потерянными сделками.

## T1: запрещённые сигналы по московским часам

Фиксированное окно 10:00 ≤ signal Close <18:00. Это исследовательское окно, а не официальная сессия MOEX.

| version | moscow_hour | original_signals | forbidden | forbidden_flat | forbidden_busy |
| --- | --- | --- | --- | --- | --- |
| BASELINE | 0 | 5 | 5 | 4 | 1 |
| BASELINE | 1 | 0 | 0 | 0 | 0 |
| BASELINE | 2 | 0 | 0 | 0 | 0 |
| BASELINE | 3 | 0 | 0 | 0 | 0 |
| BASELINE | 4 | 0 | 0 | 0 | 0 |
| BASELINE | 5 | 0 | 0 | 0 | 0 |
| BASELINE | 6 | 0 | 0 | 0 | 0 |
| BASELINE | 7 | 0 | 0 | 0 | 0 |
| BASELINE | 8 | 0 | 0 | 0 | 0 |
| BASELINE | 9 | 53 | 53 | 46 | 7 |
| BASELINE | 10 | 175 | 0 | 0 | 0 |
| BASELINE | 11 | 205 | 0 | 0 | 0 |
| BASELINE | 12 | 175 | 0 | 0 | 0 |
| BASELINE | 13 | 178 | 0 | 0 | 0 |
| BASELINE | 14 | 162 | 0 | 0 | 0 |
| BASELINE | 15 | 147 | 0 | 0 | 0 |
| BASELINE | 16 | 185 | 0 | 0 | 0 |
| BASELINE | 17 | 169 | 0 | 0 | 0 |
| BASELINE | 18 | 235 | 235 | 107 | 128 |
| BASELINE | 19 | 158 | 158 | 93 | 65 |
| BASELINE | 20 | 56 | 56 | 40 | 16 |
| BASELINE | 21 | 40 | 40 | 29 | 11 |
| BASELINE | 22 | 46 | 46 | 34 | 12 |
| BASELINE | 23 | 28 | 28 | 24 | 4 |
| OPTIMIZED | 0 | 5 | 5 | 2 | 3 |
| OPTIMIZED | 1 | 0 | 0 | 0 | 0 |
| OPTIMIZED | 2 | 0 | 0 | 0 | 0 |
| OPTIMIZED | 3 | 0 | 0 | 0 | 0 |
| OPTIMIZED | 4 | 0 | 0 | 0 | 0 |
| OPTIMIZED | 5 | 0 | 0 | 0 | 0 |
| OPTIMIZED | 6 | 0 | 0 | 0 | 0 |
| OPTIMIZED | 7 | 0 | 0 | 0 | 0 |
| OPTIMIZED | 8 | 0 | 0 | 0 | 0 |
| OPTIMIZED | 9 | 53 | 53 | 43 | 10 |
| OPTIMIZED | 10 | 175 | 0 | 0 | 0 |
| OPTIMIZED | 11 | 205 | 0 | 0 | 0 |
| OPTIMIZED | 12 | 175 | 0 | 0 | 0 |
| OPTIMIZED | 13 | 178 | 0 | 0 | 0 |
| OPTIMIZED | 14 | 162 | 0 | 0 | 0 |
| OPTIMIZED | 15 | 147 | 0 | 0 | 0 |
| OPTIMIZED | 16 | 185 | 0 | 0 | 0 |
| OPTIMIZED | 17 | 169 | 0 | 0 | 0 |
| OPTIMIZED | 18 | 235 | 235 | 91 | 144 |
| OPTIMIZED | 19 | 158 | 158 | 84 | 74 |
| OPTIMIZED | 20 | 56 | 56 | 38 | 18 |
| OPTIMIZED | 21 | 40 | 40 | 27 | 13 |
| OPTIMIZED | 22 | 46 | 46 | 30 | 16 |
| OPTIMIZED | 23 | 28 | 28 | 22 | 6 |

## T2: первая завершённая свеча после наблюдаемого gap

Только текущий и предыдущий фактически наблюдаемые завершённые Close. При отсутствии предыдущего — отдельная причина NO_PREVIOUS_OBSERVED_CLOSE. Следующая непрерывная свеча снова разрешена. observed_gaps.csv фиксирует все gaps, даже без исходного сигнала.

| version | year | observed_gaps_gt_15min | no_previous_bars | signals_on_first_bar_after_gap | signals_without_previous | blocked_gap_signals | blocked_no_previous_signals |
| --- | --- | --- | --- | --- | --- | --- | --- |
| BASELINE | ALL | 2366 | 4 | 54 | 0 | 54 | 0 |
| BASELINE | 2023 | 1181 | 4 | 26 | 0 | 26 | 0 |
| BASELINE | 2024 | 1185 | 0 | 28 | 0 | 28 | 0 |
| OPTIMIZED | ALL | 2366 | 4 | 54 | 0 | 54 | 0 |
| OPTIMIZED | 2023 | 1181 | 4 | 26 | 0 | 26 | 0 |
| OPTIMIZED | 2024 | 1185 | 0 | 28 | 0 | 28 | 0 |

## Данные и воспроизведение

База удалённого main `4b415f95576e00480e344a1da498c35660eef931` совпала с ожидаемым Merge #498. Данные `f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8`; freeze commit `e8feb7ac351c9548d61abee0e06462485e852fc1`.

| instrument | used_candles | first_open | last_open | first_close | last_close |
| --- | --- | --- | --- | --- | --- |
| USDRUBF | 29890 | 2023-01-03T09:00:00+03:00 | 2024-12-30T23:45:00+03:00 | 2023-01-03T09:15:00+03:00 | 2024-12-31T00:00:00+03:00 |
| CNYRUBF | 29633 | 2023-01-03T09:00:00+03:00 | 2024-12-30T23:45:00+03:00 | 2023-01-03T09:15:00+03:00 | 2024-12-31T00:00:00+03:00 |
| GLDRUBF | 22189 | 2023-07-11T10:00:00+03:00 | 2024-12-30T23:45:00+03:00 | 2023-07-11T10:15:00+03:00 | 2024-12-31T00:00:00+03:00 |
| IMOEXF | 16593 | 2023-11-14T10:00:00+03:00 | 2024-12-30T23:45:00+03:00 | 2023-11-14T10:15:00+03:00 | 2024-12-31T00:00:00+03:00 |

CONTROL: 1 442 CLOSED +2 terminal OPEN, все общие торговые поля #490/#495 и OPEN сверены; допуск чисел 1e−8, даты/строки/флаги точно. Исторические C1/net и искусственные C1-единицы исключены. Исходные OHLC не копируются.
Парсеры останавливаются по timestamp перед OHLC 2025+. Полнофайловые SHA используют будущий суффикс только как непрозрачные байты целостности. H1 — исходные дневные порядковые блоки четырёх последовательных M15; только закрытые H1 доступны текущему Close. Индикаторы пересекают дни, как в исходной модели.
Stop-first, неблагоприятный Open gap, trailing после завершённой пережитой свечи, same-Close re-entry при разрешении нового входа, занятость, перенос через дни/выходные/годы сохранены. Вход по Close — историческое предположение; исполнимость реального Close-fill не заявляется.

## Каждый инструмент

| version | rule | scope | closed_trades | open_positions_at_period_end | gross_PF | gross_R | expectancy_R | positive_months | negative_months | zero_months | positive_share_covered_months | max_drawdown_closed_R |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BASELINE | CONTROL | USDRUBF | 226 | 0 | 1.7440 | 68.7570 | 0.3042 | 16 | 8 | 0 | 0.6667 | 14.9600 |
| BASELINE | CONTROL | CNYRUBF | 199 | 0 | 1.5279 | 45.0322 | 0.2263 | 14 | 10 | 0 | 0.5833 | 17.6552 |
| BASELINE | CONTROL | GLDRUBF | 178 | 0 | 1.1386 | 11.1684 | 0.0627 | 9 | 9 | 6 | 0.5000 | 10.3931 |
| BASELINE | CONTROL | IMOEXF | 138 | 1 | 1.3259 | 19.4536 | 0.1410 | 9 | 5 | 10 | 0.6429 | 9.4402 |
| BASELINE | T1 | USDRUBF | 173 | 0 | 1.7723 | 57.5693 | 0.3328 | 13 | 11 | 0 | 0.5417 | 8.9868 |
| BASELINE | T1 | CNYRUBF | 155 | 0 | 1.6671 | 44.4419 | 0.2867 | 14 | 9 | 1 | 0.5833 | 15.6410 |
| BASELINE | T1 | GLDRUBF | 127 | 0 | 1.4690 | 25.2605 | 0.1989 | 9 | 9 | 6 | 0.5000 | 8.5412 |
| BASELINE | T1 | IMOEXF | 113 | 1 | 1.1571 | 8.2485 | 0.0730 | 7 | 7 | 10 | 0.5000 | 10.3459 |
| BASELINE | T2 | USDRUBF | 220 | 0 | 1.7394 | 66.7380 | 0.3034 | 14 | 10 | 0 | 0.5833 | 15.9427 |
| BASELINE | T2 | CNYRUBF | 194 | 0 | 1.5786 | 47.6019 | 0.2454 | 14 | 10 | 0 | 0.5833 | 17.6552 |
| BASELINE | T2 | GLDRUBF | 177 | 0 | 1.1088 | 8.9139 | 0.0504 | 8 | 10 | 6 | 0.4444 | 11.7330 |
| BASELINE | T2 | IMOEXF | 138 | 1 | 1.2955 | 17.9202 | 0.1299 | 8 | 6 | 10 | 0.5714 | 9.4086 |
| OPTIMIZED | CONTROL | USDRUBF | 213 | 0 | 1.7939 | 75.8196 | 0.3560 | 14 | 10 | 0 | 0.5833 | 17.5358 |
| OPTIMIZED | CONTROL | CNYRUBF | 188 | 0 | 1.6694 | 58.1002 | 0.3090 | 15 | 9 | 0 | 0.6250 | 14.1599 |
| OPTIMIZED | CONTROL | GLDRUBF | 166 | 0 | 1.2587 | 21.3159 | 0.1284 | 9 | 9 | 6 | 0.5000 | 11.1124 |
| OPTIMIZED | CONTROL | IMOEXF | 134 | 1 | 1.3756 | 23.4842 | 0.1753 | 8 | 6 | 10 | 0.5714 | 9.4715 |
| OPTIMIZED | T1 | USDRUBF | 167 | 0 | 1.9832 | 74.1198 | 0.4438 | 13 | 11 | 0 | 0.5417 | 12.3087 |
| OPTIMIZED | T1 | CNYRUBF | 148 | 0 | 1.8279 | 56.7595 | 0.3835 | 16 | 7 | 1 | 0.6667 | 9.3956 |
| OPTIMIZED | T1 | GLDRUBF | 123 | 0 | 1.5360 | 32.1086 | 0.2610 | 11 | 7 | 6 | 0.6111 | 9.6186 |
| OPTIMIZED | T1 | IMOEXF | 111 | 1 | 1.2310 | 12.7567 | 0.1149 | 8 | 6 | 10 | 0.5714 | 6.5298 |
| OPTIMIZED | T2 | USDRUBF | 208 | 0 | 1.7880 | 73.3010 | 0.3524 | 14 | 10 | 0 | 0.5833 | 18.6095 |
| OPTIMIZED | T2 | CNYRUBF | 186 | 0 | 1.6844 | 58.6919 | 0.3155 | 15 | 9 | 0 | 0.6250 | 14.1599 |
| OPTIMIZED | T2 | GLDRUBF | 166 | 0 | 1.2208 | 18.6191 | 0.1122 | 9 | 9 | 6 | 0.5000 | 12.0818 |
| OPTIMIZED | T2 | IMOEXF | 134 | 1 | 1.3525 | 22.2578 | 0.1661 | 8 | 6 | 10 | 0.5714 | 9.4715 |

## LONG/SHORT, полный период и оба года

| version | rule | scope | year | direction | closed_trades | open_positions_at_period_end | gross_PF | gross_R | expectancy_R |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BASELINE | CONTROL | ALL_FOUR | ALL | LONG | 416 | 1 | 1.5349 | 93.0651 | 0.2237 |
| BASELINE | CONTROL | ALL_FOUR | 2023 | LONG | 161 | 0 | 1.7729 | 49.3497 | 0.3065 |
| BASELINE | CONTROL | ALL_FOUR | 2024 | LONG | 255 | 1 | 1.3969 | 43.7154 | 0.1714 |
| BASELINE | CONTROL | ALL_FOUR | ALL | SHORT | 325 | 0 | 1.3566 | 51.3461 | 0.1580 |
| BASELINE | CONTROL | ALL_FOUR | 2023 | SHORT | 95 | 0 | 2.2633 | 44.8552 | 0.4722 |
| BASELINE | CONTROL | ALL_FOUR | 2024 | SHORT | 230 | 0 | 1.0598 | 6.4909 | 0.0282 |
| BASELINE | CONTROL | USDRUBF | ALL | LONG | 133 | 0 | 1.8852 | 46.8216 | 0.3520 |
| BASELINE | CONTROL | USDRUBF | 2023 | LONG | 71 | 0 | 2.7092 | 42.4775 | 0.5983 |
| BASELINE | CONTROL | USDRUBF | 2024 | LONG | 62 | 0 | 1.1549 | 4.3441 | 0.0701 |
| BASELINE | CONTROL | USDRUBF | ALL | SHORT | 93 | 0 | 1.5550 | 21.9355 | 0.2359 |
| BASELINE | CONTROL | USDRUBF | 2023 | SHORT | 40 | 0 | 2.6766 | 22.3813 | 0.5595 |
| BASELINE | CONTROL | USDRUBF | 2024 | SHORT | 53 | 0 | 0.9830 | -0.4458 | -0.0084 |
| BASELINE | CONTROL | CNYRUBF | ALL | LONG | 113 | 0 | 1.6045 | 28.7720 | 0.2546 |
| BASELINE | CONTROL | CNYRUBF | 2023 | LONG | 55 | 0 | 1.5088 | 11.6494 | 0.2118 |
| BASELINE | CONTROL | CNYRUBF | 2024 | LONG | 58 | 0 | 1.6934 | 17.1226 | 0.2952 |
| BASELINE | CONTROL | CNYRUBF | ALL | SHORT | 86 | 0 | 1.4312 | 16.2602 | 0.1891 |
| BASELINE | CONTROL | CNYRUBF | 2023 | SHORT | 30 | 0 | 2.5135 | 17.5196 | 0.5840 |
| BASELINE | CONTROL | CNYRUBF | 2024 | SHORT | 56 | 0 | 0.9518 | -1.2594 | -0.0225 |
| BASELINE | CONTROL | GLDRUBF | ALL | LONG | 119 | 0 | 1.0221 | 1.2411 | 0.0104 |
| BASELINE | CONTROL | GLDRUBF | 2023 | LONG | 33 | 0 | 0.6802 | -5.1432 | -0.1559 |
| BASELINE | CONTROL | GLDRUBF | 2024 | LONG | 86 | 0 | 1.1596 | 6.3844 | 0.0742 |
| BASELINE | CONTROL | GLDRUBF | ALL | SHORT | 59 | 0 | 1.4053 | 9.9273 | 0.1683 |
| BASELINE | CONTROL | GLDRUBF | 2023 | SHORT | 18 | 0 | 1.7075 | 5.0407 | 0.2800 |
| BASELINE | CONTROL | GLDRUBF | 2024 | SHORT | 41 | 0 | 1.2813 | 4.8866 | 0.1192 |
| BASELINE | CONTROL | IMOEXF | ALL | LONG | 51 | 1 | 1.9319 | 16.2304 | 0.3182 |
| BASELINE | CONTROL | IMOEXF | 2023 | LONG | 2 | 0 | 28.1271 | 0.3660 | 0.1830 |
| BASELINE | CONTROL | IMOEXF | 2024 | LONG | 49 | 1 | 1.9116 | 15.8644 | 0.3238 |
| BASELINE | CONTROL | IMOEXF | ALL | SHORT | 87 | 0 | 1.0763 | 3.2232 | 0.0370 |
| BASELINE | CONTROL | IMOEXF | 2023 | SHORT | 7 | 0 | 0.9750 | -0.0864 | -0.0123 |
| BASELINE | CONTROL | IMOEXF | 2024 | SHORT | 80 | 0 | 1.0853 | 3.3095 | 0.0414 |
| BASELINE | T1 | ALL_FOUR | ALL | LONG | 307 | 1 | 1.6973 | 87.4925 | 0.2850 |
| BASELINE | T1 | ALL_FOUR | 2023 | LONG | 122 | 0 | 1.6279 | 32.3800 | 0.2654 |
| BASELINE | T1 | ALL_FOUR | 2024 | LONG | 185 | 1 | 1.7458 | 55.1125 | 0.2979 |
| BASELINE | T1 | ALL_FOUR | ALL | SHORT | 261 | 0 | 1.3935 | 48.0278 | 0.1840 |
| BASELINE | T1 | ALL_FOUR | 2023 | SHORT | 75 | 0 | 2.6152 | 45.5375 | 0.6072 |
| BASELINE | T1 | ALL_FOUR | 2024 | SHORT | 186 | 0 | 1.0265 | 2.4903 | 0.0134 |
| BASELINE | T1 | USDRUBF | ALL | LONG | 100 | 0 | 1.7634 | 33.4091 | 0.3341 |
| BASELINE | T1 | USDRUBF | 2023 | LONG | 55 | 0 | 2.1176 | 24.9411 | 0.4535 |
| BASELINE | T1 | USDRUBF | 2024 | LONG | 45 | 0 | 1.3948 | 8.4681 | 0.1882 |
| BASELINE | T1 | USDRUBF | ALL | SHORT | 73 | 0 | 1.7850 | 24.1602 | 0.3310 |
| BASELINE | T1 | USDRUBF | 2023 | SHORT | 31 | 0 | 3.1555 | 22.3493 | 0.7209 |
| BASELINE | T1 | USDRUBF | 2024 | SHORT | 42 | 0 | 1.0887 | 1.8109 | 0.0431 |
| BASELINE | T1 | CNYRUBF | ALL | LONG | 83 | 0 | 1.9370 | 31.1916 | 0.3758 |
| BASELINE | T1 | CNYRUBF | 2023 | LONG | 38 | 0 | 1.8709 | 13.1965 | 0.3473 |
| BASELINE | T1 | CNYRUBF | 2024 | LONG | 45 | 0 | 1.9922 | 17.9951 | 0.3999 |
| BASELINE | T1 | CNYRUBF | ALL | SHORT | 72 | 0 | 1.3976 | 13.2504 | 0.1840 |
| BASELINE | T1 | CNYRUBF | 2023 | SHORT | 24 | 0 | 2.9924 | 17.4554 | 0.7273 |
| BASELINE | T1 | CNYRUBF | 2024 | SHORT | 48 | 0 | 0.8288 | -4.2050 | -0.0876 |
| BASELINE | T1 | GLDRUBF | ALL | LONG | 82 | 0 | 1.3230 | 11.2381 | 0.1371 |
| BASELINE | T1 | GLDRUBF | 2023 | LONG | 27 | 0 | 0.5653 | -6.1235 | -0.2268 |
| BASELINE | T1 | GLDRUBF | 2024 | LONG | 55 | 0 | 1.8383 | 17.3617 | 0.3157 |
| BASELINE | T1 | GLDRUBF | ALL | SHORT | 45 | 0 | 1.7355 | 14.0224 | 0.3116 |
| BASELINE | T1 | GLDRUBF | 2023 | SHORT | 14 | 0 | 2.1579 | 6.4942 | 0.4639 |
| BASELINE | T1 | GLDRUBF | 2024 | SHORT | 31 | 0 | 1.5594 | 7.5282 | 0.2428 |
| BASELINE | T1 | IMOEXF | ALL | LONG | 42 | 1 | 1.8557 | 11.6537 | 0.2775 |
| BASELINE | T1 | IMOEXF | 2023 | LONG | 2 | 0 | 28.1271 | 0.3660 | 0.1830 |
| BASELINE | T1 | IMOEXF | 2024 | LONG | 40 | 1 | 1.8296 | 11.2877 | 0.2822 |
| BASELINE | T1 | IMOEXF | ALL | SHORT | 71 | 0 | 0.9124 | -3.4052 | -0.0480 |
| BASELINE | T1 | IMOEXF | 2023 | SHORT | 6 | 0 | 0.7797 | -0.7614 | -0.1269 |
| BASELINE | T1 | IMOEXF | 2024 | SHORT | 65 | 0 | 0.9254 | -2.6438 | -0.0407 |
| BASELINE | T2 | ALL_FOUR | ALL | LONG | 412 | 1 | 1.5011 | 88.3211 | 0.2144 |
| BASELINE | T2 | ALL_FOUR | 2023 | LONG | 159 | 0 | 1.7310 | 47.1289 | 0.2964 |
| BASELINE | T2 | ALL_FOUR | 2024 | LONG | 253 | 1 | 1.3685 | 41.1922 | 0.1628 |
| BASELINE | T2 | ALL_FOUR | ALL | SHORT | 317 | 0 | 1.3806 | 52.8529 | 0.1667 |
| BASELINE | T2 | ALL_FOUR | 2023 | SHORT | 92 | 0 | 2.2684 | 44.5971 | 0.4848 |
| BASELINE | T2 | ALL_FOUR | 2024 | SHORT | 225 | 0 | 1.0796 | 8.2558 | 0.0367 |
| BASELINE | T2 | USDRUBF | ALL | LONG | 130 | 0 | 1.8683 | 45.6008 | 0.3508 |
| BASELINE | T2 | USDRUBF | 2023 | LONG | 69 | 0 | 2.5799 | 40.2567 | 0.5834 |
| BASELINE | T2 | USDRUBF | 2024 | LONG | 61 | 0 | 1.1976 | 5.3441 | 0.0876 |
| BASELINE | T2 | USDRUBF | ALL | SHORT | 90 | 0 | 1.5601 | 21.1372 | 0.2349 |
| BASELINE | T2 | USDRUBF | 2023 | SHORT | 39 | 0 | 2.6240 | 22.0196 | 0.5646 |
| BASELINE | T2 | USDRUBF | 2024 | SHORT | 51 | 0 | 0.9635 | -0.8824 | -0.0173 |
| BASELINE | T2 | CNYRUBF | ALL | LONG | 112 | 0 | 1.6103 | 28.9420 | 0.2584 |
| BASELINE | T2 | CNYRUBF | 2023 | LONG | 55 | 0 | 1.5088 | 11.6494 | 0.2118 |
| BASELINE | T2 | CNYRUBF | 2024 | LONG | 57 | 0 | 1.7051 | 17.2926 | 0.3034 |
| BASELINE | T2 | CNYRUBF | ALL | SHORT | 82 | 0 | 1.5354 | 18.6599 | 0.2276 |
| BASELINE | T2 | CNYRUBF | 2023 | SHORT | 29 | 0 | 2.4927 | 17.1528 | 0.5915 |
| BASELINE | T2 | CNYRUBF | 2024 | SHORT | 53 | 0 | 1.0645 | 1.5070 | 0.0284 |
| BASELINE | T2 | GLDRUBF | ALL | LONG | 119 | 0 | 0.9744 | -1.4837 | -0.0125 |
| BASELINE | T2 | GLDRUBF | 2023 | LONG | 33 | 0 | 0.6802 | -5.1432 | -0.1559 |
| BASELINE | T2 | GLDRUBF | 2024 | LONG | 86 | 0 | 1.0875 | 3.6595 | 0.0426 |
| BASELINE | T2 | GLDRUBF | ALL | SHORT | 58 | 0 | 1.4328 | 10.3977 | 0.1793 |
| BASELINE | T2 | GLDRUBF | 2023 | SHORT | 17 | 0 | 1.8282 | 5.5110 | 0.3242 |
| BASELINE | T2 | GLDRUBF | 2024 | SHORT | 41 | 0 | 1.2813 | 4.8866 | 0.1192 |
| BASELINE | T2 | IMOEXF | ALL | LONG | 51 | 1 | 1.8302 | 15.2620 | 0.2993 |
| BASELINE | T2 | IMOEXF | 2023 | LONG | 2 | 0 | 28.1271 | 0.3660 | 0.1830 |
| BASELINE | T2 | IMOEXF | 2024 | LONG | 49 | 1 | 1.8108 | 14.8960 | 0.3040 |
| BASELINE | T2 | IMOEXF | ALL | SHORT | 87 | 0 | 1.0629 | 2.6581 | 0.0306 |
| BASELINE | T2 | IMOEXF | 2023 | SHORT | 7 | 0 | 0.9750 | -0.0864 | -0.0123 |
| BASELINE | T2 | IMOEXF | 2024 | SHORT | 80 | 0 | 1.0707 | 2.7445 | 0.0343 |
| OPTIMIZED | CONTROL | ALL_FOUR | ALL | LONG | 396 | 1 | 1.5650 | 103.1002 | 0.2604 |
| OPTIMIZED | CONTROL | ALL_FOUR | 2023 | LONG | 152 | 0 | 1.7874 | 53.6639 | 0.3531 |
| OPTIMIZED | CONTROL | ALL_FOUR | 2024 | LONG | 244 | 1 | 1.4324 | 49.4363 | 0.2026 |
| OPTIMIZED | CONTROL | ALL_FOUR | ALL | SHORT | 305 | 0 | 1.5225 | 75.6197 | 0.2479 |
| OPTIMIZED | CONTROL | ALL_FOUR | 2023 | SHORT | 91 | 0 | 2.1695 | 44.9539 | 0.4940 |
| OPTIMIZED | CONTROL | ALL_FOUR | 2024 | SHORT | 214 | 0 | 1.2885 | 30.6658 | 0.1433 |
| OPTIMIZED | CONTROL | USDRUBF | ALL | LONG | 125 | 0 | 1.9153 | 50.8503 | 0.4068 |
| OPTIMIZED | CONTROL | USDRUBF | 2023 | LONG | 65 | 0 | 2.8525 | 47.4704 | 0.7303 |
| OPTIMIZED | CONTROL | USDRUBF | 2024 | LONG | 60 | 0 | 1.1129 | 3.3800 | 0.0563 |
| OPTIMIZED | CONTROL | USDRUBF | ALL | SHORT | 88 | 0 | 1.6249 | 24.9693 | 0.2837 |
| OPTIMIZED | CONTROL | USDRUBF | 2023 | SHORT | 38 | 0 | 2.5415 | 23.1865 | 0.6102 |
| OPTIMIZED | CONTROL | USDRUBF | 2024 | SHORT | 50 | 0 | 1.0716 | 1.7828 | 0.0357 |
| OPTIMIZED | CONTROL | CNYRUBF | ALL | LONG | 111 | 0 | 1.4236 | 22.0799 | 0.1989 |
| OPTIMIZED | CONTROL | CNYRUBF | 2023 | LONG | 53 | 0 | 1.4426 | 10.8178 | 0.2041 |
| OPTIMIZED | CONTROL | CNYRUBF | 2024 | LONG | 58 | 0 | 1.4069 | 11.2621 | 0.1942 |
| OPTIMIZED | CONTROL | CNYRUBF | ALL | SHORT | 77 | 0 | 2.0388 | 36.0203 | 0.4678 |
| OPTIMIZED | CONTROL | CNYRUBF | 2023 | SHORT | 29 | 0 | 2.4478 | 16.7282 | 0.5768 |
| OPTIMIZED | CONTROL | CNYRUBF | 2024 | SHORT | 48 | 0 | 1.8344 | 19.2921 | 0.4019 |
| OPTIMIZED | CONTROL | GLDRUBF | ALL | LONG | 110 | 0 | 1.1576 | 8.7470 | 0.0795 |
| OPTIMIZED | CONTROL | GLDRUBF | 2023 | LONG | 32 | 0 | 0.7074 | -5.2933 | -0.1654 |
| OPTIMIZED | CONTROL | GLDRUBF | 2024 | LONG | 78 | 0 | 1.3754 | 14.0403 | 0.1800 |
| OPTIMIZED | CONTROL | GLDRUBF | ALL | SHORT | 56 | 0 | 1.4670 | 12.5688 | 0.2244 |
| OPTIMIZED | CONTROL | GLDRUBF | 2023 | SHORT | 17 | 0 | 1.7563 | 6.0522 | 0.3560 |
| OPTIMIZED | CONTROL | GLDRUBF | 2024 | SHORT | 39 | 0 | 1.3446 | 6.5166 | 0.1671 |
| OPTIMIZED | CONTROL | IMOEXF | ALL | LONG | 50 | 1 | 2.1085 | 21.4229 | 0.4285 |
| OPTIMIZED | CONTROL | IMOEXF | 2023 | LONG | 2 | 0 | — | 0.6690 | 0.3345 |
| OPTIMIZED | CONTROL | IMOEXF | 2024 | LONG | 48 | 1 | 2.0739 | 20.7539 | 0.4324 |
| OPTIMIZED | CONTROL | IMOEXF | ALL | SHORT | 84 | 0 | 1.0477 | 2.0613 | 0.0245 |
| OPTIMIZED | CONTROL | IMOEXF | 2023 | SHORT | 7 | 0 | 0.7363 | -1.0130 | -0.1447 |
| OPTIMIZED | CONTROL | IMOEXF | 2024 | SHORT | 77 | 0 | 1.0781 | 3.0743 | 0.0399 |
| OPTIMIZED | T1 | ALL_FOUR | ALL | LONG | 298 | 1 | 1.7856 | 105.6347 | 0.3545 |
| OPTIMIZED | T1 | ALL_FOUR | 2023 | LONG | 118 | 0 | 1.8818 | 47.1710 | 0.3998 |
| OPTIMIZED | T1 | ALL_FOUR | 2024 | LONG | 180 | 1 | 1.7221 | 58.4638 | 0.3248 |
| OPTIMIZED | T1 | ALL_FOUR | ALL | SHORT | 251 | 0 | 1.5627 | 70.1099 | 0.2793 |
| OPTIMIZED | T1 | ALL_FOUR | 2023 | SHORT | 74 | 0 | 2.4991 | 46.5778 | 0.6294 |
| OPTIMIZED | T1 | ALL_FOUR | 2024 | SHORT | 177 | 0 | 1.2516 | 23.5321 | 0.1329 |
| OPTIMIZED | T1 | USDRUBF | ALL | LONG | 96 | 0 | 2.0788 | 47.7548 | 0.4974 |
| OPTIMIZED | T1 | USDRUBF | 2023 | LONG | 52 | 0 | 2.8836 | 40.0635 | 0.7705 |
| OPTIMIZED | T1 | USDRUBF | 2024 | LONG | 44 | 0 | 1.3345 | 7.6913 | 0.1748 |
| OPTIMIZED | T1 | USDRUBF | ALL | SHORT | 71 | 0 | 1.8472 | 26.3650 | 0.3713 |
| OPTIMIZED | T1 | USDRUBF | 2023 | SHORT | 30 | 0 | 3.1491 | 24.3727 | 0.8124 |
| OPTIMIZED | T1 | USDRUBF | 2024 | SHORT | 41 | 0 | 1.1007 | 1.9924 | 0.0486 |
| OPTIMIZED | T1 | CNYRUBF | ALL | LONG | 82 | 0 | 1.6471 | 23.8112 | 0.2904 |
| OPTIMIZED | T1 | CNYRUBF | 2023 | LONG | 37 | 0 | 1.6121 | 10.0762 | 0.2723 |
| OPTIMIZED | T1 | CNYRUBF | 2024 | LONG | 45 | 0 | 1.6754 | 13.7351 | 0.3052 |
| OPTIMIZED | T1 | CNYRUBF | ALL | SHORT | 66 | 0 | 2.0375 | 32.9483 | 0.4992 |
| OPTIMIZED | T1 | CNYRUBF | 2023 | SHORT | 24 | 0 | 2.7191 | 16.1030 | 0.6710 |
| OPTIMIZED | T1 | CNYRUBF | 2024 | SHORT | 42 | 0 | 1.7523 | 16.8453 | 0.4011 |
| OPTIMIZED | T1 | GLDRUBF | ALL | LONG | 79 | 0 | 1.4712 | 18.0340 | 0.2283 |
| OPTIMIZED | T1 | GLDRUBF | 2023 | LONG | 27 | 0 | 0.7692 | -3.6377 | -0.1347 |
| OPTIMIZED | T1 | GLDRUBF | 2024 | LONG | 52 | 0 | 1.9628 | 21.6716 | 0.4168 |
| OPTIMIZED | T1 | GLDRUBF | ALL | SHORT | 44 | 0 | 1.6507 | 14.0746 | 0.3199 |
| OPTIMIZED | T1 | GLDRUBF | 2023 | SHORT | 14 | 0 | 2.1554 | 7.5341 | 0.5382 |
| OPTIMIZED | T1 | GLDRUBF | 2024 | SHORT | 30 | 0 | 1.4329 | 6.5405 | 0.2180 |
| OPTIMIZED | T1 | IMOEXF | ALL | LONG | 41 | 1 | 2.0600 | 16.0348 | 0.3911 |
| OPTIMIZED | T1 | IMOEXF | 2023 | LONG | 2 | 0 | — | 0.6690 | 0.3345 |
| OPTIMIZED | T1 | IMOEXF | 2024 | LONG | 39 | 1 | 2.0158 | 15.3658 | 0.3940 |
| OPTIMIZED | T1 | IMOEXF | ALL | SHORT | 70 | 0 | 0.9182 | -3.2780 | -0.0468 |
| OPTIMIZED | T1 | IMOEXF | 2023 | SHORT | 6 | 0 | 0.6272 | -1.4320 | -0.2387 |
| OPTIMIZED | T1 | IMOEXF | 2024 | SHORT | 64 | 0 | 0.9491 | -1.8460 | -0.0288 |
| OPTIMIZED | T2 | ALL_FOUR | ALL | LONG | 392 | 1 | 1.5438 | 99.4059 | 0.2536 |
| OPTIMIZED | T2 | ALL_FOUR | 2023 | LONG | 150 | 0 | 1.7639 | 51.6189 | 0.3441 |
| OPTIMIZED | T2 | ALL_FOUR | 2024 | LONG | 242 | 1 | 1.4148 | 47.7870 | 0.1975 |
| OPTIMIZED | T2 | ALL_FOUR | ALL | SHORT | 302 | 0 | 1.5120 | 73.4639 | 0.2433 |
| OPTIMIZED | T2 | ALL_FOUR | 2023 | SHORT | 90 | 0 | 2.1247 | 43.9084 | 0.4879 |
| OPTIMIZED | T2 | ALL_FOUR | 2024 | SHORT | 212 | 0 | 1.2830 | 29.5554 | 0.1394 |
| OPTIMIZED | T2 | USDRUBF | ALL | LONG | 122 | 0 | 1.9228 | 49.8054 | 0.4082 |
| OPTIMIZED | T2 | USDRUBF | 2023 | LONG | 63 | 0 | 2.8140 | 45.4254 | 0.7210 |
| OPTIMIZED | T2 | USDRUBF | 2024 | LONG | 59 | 0 | 1.1514 | 4.3800 | 0.0742 |
| OPTIMIZED | T2 | USDRUBF | ALL | SHORT | 86 | 0 | 1.6017 | 23.4956 | 0.2732 |
| OPTIMIZED | T2 | USDRUBF | 2023 | SHORT | 37 | 0 | 2.5487 | 23.2290 | 0.6278 |
| OPTIMIZED | T2 | USDRUBF | 2024 | SHORT | 49 | 0 | 1.0111 | 0.2666 | 0.0054 |
| OPTIMIZED | T2 | CNYRUBF | ALL | LONG | 110 | 0 | 1.4424 | 22.7596 | 0.2069 |
| OPTIMIZED | T2 | CNYRUBF | 2023 | LONG | 53 | 0 | 1.4426 | 10.8178 | 0.2041 |
| OPTIMIZED | T2 | CNYRUBF | 2024 | LONG | 57 | 0 | 1.4423 | 11.9418 | 0.2095 |
| OPTIMIZED | T2 | CNYRUBF | ALL | SHORT | 76 | 0 | 2.0470 | 35.9323 | 0.4728 |
| OPTIMIZED | T2 | CNYRUBF | 2023 | SHORT | 29 | 0 | 2.2823 | 15.6402 | 0.5393 |
| OPTIMIZED | T2 | CNYRUBF | 2024 | SHORT | 47 | 0 | 1.9174 | 20.2921 | 0.4317 |
| OPTIMIZED | T2 | GLDRUBF | ALL | LONG | 110 | 0 | 1.1054 | 6.0503 | 0.0550 |
| OPTIMIZED | T2 | GLDRUBF | 2023 | LONG | 32 | 0 | 0.7074 | -5.2933 | -0.1654 |
| OPTIMIZED | T2 | GLDRUBF | 2024 | LONG | 78 | 0 | 1.2885 | 11.3436 | 0.1454 |
| OPTIMIZED | T2 | GLDRUBF | ALL | SHORT | 56 | 0 | 1.4670 | 12.5688 | 0.2244 |
| OPTIMIZED | T2 | GLDRUBF | 2023 | SHORT | 17 | 0 | 1.7563 | 6.0522 | 0.3560 |
| OPTIMIZED | T2 | GLDRUBF | 2024 | SHORT | 39 | 0 | 1.3446 | 6.5166 | 0.1671 |
| OPTIMIZED | T2 | IMOEXF | ALL | LONG | 50 | 1 | 2.0417 | 20.7906 | 0.4158 |
| OPTIMIZED | T2 | IMOEXF | 2023 | LONG | 2 | 0 | — | 0.6690 | 0.3345 |
| OPTIMIZED | T2 | IMOEXF | 2024 | LONG | 48 | 1 | 2.0082 | 20.1217 | 0.4192 |
| OPTIMIZED | T2 | IMOEXF | ALL | SHORT | 84 | 0 | 1.0340 | 1.4671 | 0.0175 |
| OPTIMIZED | T2 | IMOEXF | 2023 | SHORT | 7 | 0 | 0.7363 | -1.0130 | -0.1447 |
| OPTIMIZED | T2 | IMOEXF | 2024 | SHORT | 77 | 0 | 1.0630 | 2.4801 | 0.0322 |

## Все календарные месяцы

Полный календарный знаменатель — 24 месяца, включая NO_COVERAGE до старта инструмента. Доля среди покрытых месяцев отдельно в overall_report.csv. Нулевые и NO_COVERAGE не считаются положительными. OPEN на каждом месячном конце сохранены отдельно; месячная CLOSED сумма не отражает текущий P&L открытых позиций.

### ALL_FOUR

| version | rule | month | coverage | closed_trades | open_positions_at_period_end | gross_PF | gross_R |
| --- | --- | --- | --- | --- | --- | --- | --- |
| BASELINE | CONTROL | 2023-01 | AVAILABLE | 7 | 0 | 2.3802 | 3.8099 |
| BASELINE | CONTROL | 2023-02 | AVAILABLE | 15 | 0 | 1.7799 | 4.1951 |
| BASELINE | CONTROL | 2023-03 | AVAILABLE | 13 | 0 | 0.2443 | -6.2022 |
| BASELINE | CONTROL | 2023-04 | AVAILABLE | 14 | 0 | 9.6212 | 29.3412 |
| BASELINE | CONTROL | 2023-05 | AVAILABLE | 20 | 0 | 0.6320 | -3.3071 |
| BASELINE | CONTROL | 2023-06 | AVAILABLE | 15 | 2 | 1.2821 | 2.0233 |
| BASELINE | CONTROL | 2023-07 | AVAILABLE | 18 | 1 | 3.9954 | 17.3426 |
| BASELINE | CONTROL | 2023-08 | AVAILABLE | 36 | 0 | 0.5059 | -8.4431 |
| BASELINE | CONTROL | 2023-09 | AVAILABLE | 19 | 1 | 1.6277 | 5.8414 |
| BASELINE | CONTROL | 2023-10 | AVAILABLE | 33 | 0 | 4.3118 | 21.5526 |
| BASELINE | CONTROL | 2023-11 | AVAILABLE | 28 | 0 | 1.7153 | 8.1545 |
| BASELINE | CONTROL | 2023-12 | AVAILABLE | 38 | 0 | 2.4903 | 19.8967 |
| BASELINE | CONTROL | 2024-01 | AVAILABLE | 32 | 3 | 1.3380 | 4.2609 |
| BASELINE | CONTROL | 2024-02 | AVAILABLE | 39 | 0 | 0.8221 | -3.2939 |
| BASELINE | CONTROL | 2024-03 | AVAILABLE | 38 | 0 | 0.9495 | -0.9280 |
| BASELINE | CONTROL | 2024-04 | AVAILABLE | 49 | 1 | 0.9695 | -0.6988 |
| BASELINE | CONTROL | 2024-05 | AVAILABLE | 42 | 1 | 0.9038 | -1.6710 |
| BASELINE | CONTROL | 2024-06 | AVAILABLE | 43 | 0 | 0.8411 | -3.4411 |
| BASELINE | CONTROL | 2024-07 | AVAILABLE | 36 | 2 | 1.1961 | 3.4609 |
| BASELINE | CONTROL | 2024-08 | AVAILABLE | 43 | 1 | 1.0295 | 0.6238 |
| BASELINE | CONTROL | 2024-09 | AVAILABLE | 36 | 0 | 1.2716 | 3.8486 |
| BASELINE | CONTROL | 2024-10 | AVAILABLE | 42 | 0 | 0.7956 | -4.2789 |
| BASELINE | CONTROL | 2024-11 | AVAILABLE | 44 | 0 | 5.0903 | 50.5287 |
| BASELINE | CONTROL | 2024-12 | AVAILABLE | 41 | 1 | 1.0858 | 1.7951 |
| BASELINE | T1 | 2023-01 | AVAILABLE | 5 | 0 | 3.0896 | 4.1792 |
| BASELINE | T1 | 2023-02 | AVAILABLE | 12 | 0 | 2.2983 | 5.4085 |
| BASELINE | T1 | 2023-03 | AVAILABLE | 9 | 0 | 0.3596 | -3.5706 |
| BASELINE | T1 | 2023-04 | AVAILABLE | 10 | 0 | 10.8276 | 23.6194 |
| BASELINE | T1 | 2023-05 | AVAILABLE | 18 | 0 | 0.4607 | -4.7060 |
| BASELINE | T1 | 2023-06 | AVAILABLE | 7 | 2 | 1.1095 | 0.3085 |
| BASELINE | T1 | 2023-07 | AVAILABLE | 15 | 1 | 3.8316 | 14.0313 |
| BASELINE | T1 | 2023-08 | AVAILABLE | 30 | 0 | 0.3384 | -10.3887 |
| BASELINE | T1 | 2023-09 | AVAILABLE | 14 | 0 | 2.0187 | 7.6442 |
| BASELINE | T1 | 2023-10 | AVAILABLE | 25 | 0 | 3.8557 | 15.0024 |
| BASELINE | T1 | 2023-11 | AVAILABLE | 21 | 0 | 1.8395 | 7.9766 |
| BASELINE | T1 | 2023-12 | AVAILABLE | 31 | 0 | 2.6500 | 18.4125 |
| BASELINE | T1 | 2024-01 | AVAILABLE | 25 | 3 | 1.4562 | 4.6422 |
| BASELINE | T1 | 2024-02 | AVAILABLE | 30 | 0 | 0.5127 | -6.7864 |
| BASELINE | T1 | 2024-03 | AVAILABLE | 28 | 0 | 1.2329 | 3.0769 |
| BASELINE | T1 | 2024-04 | AVAILABLE | 38 | 1 | 1.0467 | 0.8317 |
| BASELINE | T1 | 2024-05 | AVAILABLE | 34 | 0 | 0.7825 | -3.6261 |
| BASELINE | T1 | 2024-06 | AVAILABLE | 31 | 0 | 0.5732 | -7.3059 |
| BASELINE | T1 | 2024-07 | AVAILABLE | 25 | 0 | 1.3817 | 4.4847 |
| BASELINE | T1 | 2024-08 | AVAILABLE | 33 | 1 | 1.3614 | 5.6031 |
| BASELINE | T1 | 2024-09 | AVAILABLE | 26 | 0 | 1.8661 | 8.1820 |
| BASELINE | T1 | 2024-10 | AVAILABLE | 34 | 0 | 0.8906 | -1.9361 |
| BASELINE | T1 | 2024-11 | AVAILABLE | 33 | 0 | 6.5190 | 44.1940 |
| BASELINE | T1 | 2024-12 | AVAILABLE | 34 | 1 | 1.3791 | 6.2426 |
| BASELINE | T2 | 2023-01 | AVAILABLE | 7 | 0 | 2.3802 | 3.8099 |
| BASELINE | T2 | 2023-02 | AVAILABLE | 14 | 0 | 1.8218 | 4.3188 |
| BASELINE | T2 | 2023-03 | AVAILABLE | 12 | 0 | 0.2658 | -5.5388 |
| BASELINE | T2 | 2023-04 | AVAILABLE | 14 | 0 | 9.2415 | 28.0488 |
| BASELINE | T2 | 2023-05 | AVAILABLE | 19 | 0 | 0.5376 | -4.4974 |
| BASELINE | T2 | 2023-06 | AVAILABLE | 15 | 2 | 1.2821 | 2.0233 |
| BASELINE | T2 | 2023-07 | AVAILABLE | 17 | 1 | 4.8296 | 18.3426 |
| BASELINE | T2 | 2023-08 | AVAILABLE | 36 | 0 | 0.4337 | -10.6967 |
| BASELINE | T2 | 2023-09 | AVAILABLE | 18 | 1 | 1.7143 | 6.3117 |
| BASELINE | T2 | 2023-10 | AVAILABLE | 33 | 0 | 4.3118 | 21.5526 |
| BASELINE | T2 | 2023-11 | AVAILABLE | 28 | 0 | 1.7153 | 8.1545 |
| BASELINE | T2 | 2023-12 | AVAILABLE | 38 | 0 | 2.4903 | 19.8967 |
| BASELINE | T2 | 2024-01 | AVAILABLE | 32 | 3 | 1.3020 | 3.8069 |
| BASELINE | T2 | 2024-02 | AVAILABLE | 39 | 0 | 0.7403 | -5.0676 |
| BASELINE | T2 | 2024-03 | AVAILABLE | 38 | 0 | 0.9495 | -0.9280 |
| BASELINE | T2 | 2024-04 | AVAILABLE | 49 | 1 | 0.9695 | -0.6988 |
| BASELINE | T2 | 2024-05 | AVAILABLE | 42 | 1 | 0.8697 | -2.2646 |
| BASELINE | T2 | 2024-06 | AVAILABLE | 41 | 0 | 0.8067 | -4.0321 |
| BASELINE | T2 | 2024-07 | AVAILABLE | 35 | 2 | 1.2679 | 4.4609 |
| BASELINE | T2 | 2024-08 | AVAILABLE | 43 | 1 | 1.0295 | 0.6238 |
| BASELINE | T2 | 2024-09 | AVAILABLE | 36 | 0 | 1.2716 | 3.8486 |
| BASELINE | T2 | 2024-10 | AVAILABLE | 40 | 0 | 0.8367 | -3.2301 |
| BASELINE | T2 | 2024-11 | AVAILABLE | 43 | 0 | 5.1614 | 50.6987 |
| BASELINE | T2 | 2024-12 | AVAILABLE | 40 | 1 | 1.1120 | 2.2301 |
| OPTIMIZED | CONTROL | 2023-01 | AVAILABLE | 7 | 0 | 2.0647 | 3.2090 |
| OPTIMIZED | CONTROL | 2023-02 | AVAILABLE | 13 | 0 | 2.3478 | 6.6877 |
| OPTIMIZED | CONTROL | 2023-03 | AVAILABLE | 13 | 0 | 0.1473 | -7.6677 |
| OPTIMIZED | CONTROL | 2023-04 | AVAILABLE | 13 | 0 | 11.1980 | 31.0016 |
| OPTIMIZED | CONTROL | 2023-05 | AVAILABLE | 20 | 0 | 0.4820 | -5.2475 |
| OPTIMIZED | CONTROL | 2023-06 | AVAILABLE | 13 | 2 | 1.7579 | 4.2143 |
| OPTIMIZED | CONTROL | 2023-07 | AVAILABLE | 16 | 2 | 3.4495 | 16.7258 |
| OPTIMIZED | CONTROL | 2023-08 | AVAILABLE | 36 | 0 | 0.5382 | -9.4074 |
| OPTIMIZED | CONTROL | 2023-09 | AVAILABLE | 18 | 1 | 1.7789 | 7.3847 |
| OPTIMIZED | CONTROL | 2023-10 | AVAILABLE | 30 | 0 | 5.2308 | 27.7491 |
| OPTIMIZED | CONTROL | 2023-11 | AVAILABLE | 28 | 0 | 1.3138 | 4.0809 |
| OPTIMIZED | CONTROL | 2023-12 | AVAILABLE | 36 | 0 | 2.3574 | 19.8874 |
| OPTIMIZED | CONTROL | 2024-01 | AVAILABLE | 32 | 3 | 1.2532 | 3.4461 |
| OPTIMIZED | CONTROL | 2024-02 | AVAILABLE | 36 | 0 | 0.9175 | -1.4773 |
| OPTIMIZED | CONTROL | 2024-03 | AVAILABLE | 36 | 0 | 1.1589 | 3.0465 |
| OPTIMIZED | CONTROL | 2024-04 | AVAILABLE | 48 | 1 | 0.9221 | -1.9484 |
| OPTIMIZED | CONTROL | 2024-05 | AVAILABLE | 41 | 1 | 0.9247 | -1.4023 |
| OPTIMIZED | CONTROL | 2024-06 | AVAILABLE | 41 | 0 | 1.2442 | 5.4406 |
| OPTIMIZED | CONTROL | 2024-07 | AVAILABLE | 35 | 2 | 1.1519 | 2.6465 |
| OPTIMIZED | CONTROL | 2024-08 | AVAILABLE | 40 | 1 | 1.1669 | 3.3666 |
| OPTIMIZED | CONTROL | 2024-09 | AVAILABLE | 34 | 0 | 1.4099 | 6.0285 |
| OPTIMIZED | CONTROL | 2024-10 | AVAILABLE | 40 | 0 | 0.8862 | -2.4057 |
| OPTIMIZED | CONTROL | 2024-11 | AVAILABLE | 39 | 0 | 6.2974 | 54.1860 |
| OPTIMIZED | CONTROL | 2024-12 | AVAILABLE | 36 | 1 | 1.4506 | 9.1748 |
| OPTIMIZED | T1 | 2023-01 | AVAILABLE | 5 | 0 | 2.9481 | 3.9826 |
| OPTIMIZED | T1 | 2023-02 | AVAILABLE | 11 | 0 | 2.9784 | 7.7384 |
| OPTIMIZED | T1 | 2023-03 | AVAILABLE | 9 | 0 | 0.2265 | -4.5230 |
| OPTIMIZED | T1 | 2023-04 | AVAILABLE | 10 | 0 | 7.7567 | 21.1635 |
| OPTIMIZED | T1 | 2023-05 | AVAILABLE | 18 | 0 | 0.3601 | -5.7798 |
| OPTIMIZED | T1 | 2023-06 | AVAILABLE | 7 | 2 | 4.0417 | 6.0833 |
| OPTIMIZED | T1 | 2023-07 | AVAILABLE | 13 | 2 | 5.0492 | 18.8890 |
| OPTIMIZED | T1 | 2023-08 | AVAILABLE | 30 | 0 | 0.3927 | -10.7929 |
| OPTIMIZED | T1 | 2023-09 | AVAILABLE | 14 | 0 | 2.2113 | 9.2387 |
| OPTIMIZED | T1 | 2023-10 | AVAILABLE | 24 | 0 | 5.2684 | 22.1996 |
| OPTIMIZED | T1 | 2023-11 | AVAILABLE | 21 | 0 | 1.4468 | 4.7657 |
| OPTIMIZED | T1 | 2023-12 | AVAILABLE | 30 | 0 | 2.6412 | 20.7836 |
| OPTIMIZED | T1 | 2024-01 | AVAILABLE | 25 | 3 | 1.1793 | 2.0744 |
| OPTIMIZED | T1 | 2024-02 | AVAILABLE | 29 | 0 | 0.5981 | -6.1374 |
| OPTIMIZED | T1 | 2024-03 | AVAILABLE | 27 | 0 | 1.4520 | 6.2412 |
| OPTIMIZED | T1 | 2024-04 | AVAILABLE | 37 | 1 | 1.0505 | 0.9543 |
| OPTIMIZED | T1 | 2024-05 | AVAILABLE | 33 | 0 | 0.8776 | -2.1390 |
| OPTIMIZED | T1 | 2024-06 | AVAILABLE | 29 | 0 | 0.9920 | -0.1428 |
| OPTIMIZED | T1 | 2024-07 | AVAILABLE | 25 | 0 | 1.3153 | 3.7598 |
| OPTIMIZED | T1 | 2024-08 | AVAILABLE | 32 | 1 | 1.5601 | 8.4216 |
| OPTIMIZED | T1 | 2024-09 | AVAILABLE | 26 | 0 | 1.8923 | 9.1641 |
| OPTIMIZED | T1 | 2024-10 | AVAILABLE | 33 | 0 | 1.0230 | 0.4076 |
| OPTIMIZED | T1 | 2024-11 | AVAILABLE | 31 | 0 | 5.9650 | 46.1908 |
| OPTIMIZED | T1 | 2024-12 | AVAILABLE | 30 | 1 | 1.8544 | 13.2012 |
| OPTIMIZED | T2 | 2023-01 | AVAILABLE | 7 | 0 | 2.0647 | 3.2090 |
| OPTIMIZED | T2 | 2023-02 | AVAILABLE | 13 | 0 | 2.1035 | 6.1115 |
| OPTIMIZED | T2 | 2023-03 | AVAILABLE | 12 | 0 | 0.1613 | -6.8870 |
| OPTIMIZED | T2 | 2023-04 | AVAILABLE | 13 | 0 | 10.5012 | 29.7597 |
| OPTIMIZED | T2 | 2023-05 | AVAILABLE | 19 | 0 | 0.4424 | -5.5938 |
| OPTIMIZED | T2 | 2023-06 | AVAILABLE | 13 | 2 | 1.7579 | 4.2143 |
| OPTIMIZED | T2 | 2023-07 | AVAILABLE | 15 | 2 | 4.0414 | 17.7258 |
| OPTIMIZED | T2 | 2023-08 | AVAILABLE | 36 | 0 | 0.4392 | -12.1141 |
| OPTIMIZED | T2 | 2023-09 | AVAILABLE | 18 | 1 | 1.7789 | 7.3847 |
| OPTIMIZED | T2 | 2023-10 | AVAILABLE | 30 | 0 | 5.2308 | 27.7491 |
| OPTIMIZED | T2 | 2023-11 | AVAILABLE | 28 | 0 | 1.3138 | 4.0809 |
| OPTIMIZED | T2 | 2023-12 | AVAILABLE | 36 | 0 | 2.3574 | 19.8874 |
| OPTIMIZED | T2 | 2024-01 | AVAILABLE | 32 | 3 | 1.2186 | 3.0037 |
| OPTIMIZED | T2 | 2024-02 | AVAILABLE | 36 | 0 | 0.8280 | -3.2509 |
| OPTIMIZED | T2 | 2024-03 | AVAILABLE | 36 | 0 | 1.1589 | 3.0465 |
| OPTIMIZED | T2 | 2024-04 | AVAILABLE | 48 | 1 | 0.9221 | -1.9484 |
| OPTIMIZED | T2 | 2024-05 | AVAILABLE | 41 | 1 | 0.8947 | -1.9615 |
| OPTIMIZED | T2 | 2024-06 | AVAILABLE | 40 | 0 | 1.1959 | 4.2939 |
| OPTIMIZED | T2 | 2024-07 | AVAILABLE | 34 | 2 | 1.2220 | 3.6465 |
| OPTIMIZED | T2 | 2024-08 | AVAILABLE | 40 | 1 | 1.1669 | 3.3666 |
| OPTIMIZED | T2 | 2024-09 | AVAILABLE | 34 | 0 | 1.4099 | 6.0285 |
| OPTIMIZED | T2 | 2024-10 | AVAILABLE | 38 | 0 | 0.9337 | -1.3288 |
| OPTIMIZED | T2 | 2024-11 | AVAILABLE | 38 | 0 | 6.7457 | 54.8657 |
| OPTIMIZED | T2 | 2024-12 | AVAILABLE | 37 | 1 | 1.3549 | 7.5806 |

### USDRUBF

| version | rule | month | coverage | closed_trades | open_positions_at_period_end | gross_PF | gross_R |
| --- | --- | --- | --- | --- | --- | --- | --- |
| BASELINE | CONTROL | 2023-01 | AVAILABLE | 5 | 0 | 3.0896 | 4.1792 |
| BASELINE | CONTROL | 2023-02 | AVAILABLE | 8 | 0 | 2.2022 | 3.2765 |
| BASELINE | CONTROL | 2023-03 | AVAILABLE | 6 | 0 | 0.5459 | -1.0795 |
| BASELINE | CONTROL | 2023-04 | AVAILABLE | 6 | 0 | 16.7081 | 18.8632 |
| BASELINE | CONTROL | 2023-05 | AVAILABLE | 11 | 0 | 0.4611 | -2.1692 |
| BASELINE | CONTROL | 2023-06 | AVAILABLE | 10 | 1 | 1.5545 | 2.6715 |
| BASELINE | CONTROL | 2023-07 | AVAILABLE | 10 | 0 | 3.3093 | 8.8295 |
| BASELINE | CONTROL | 2023-08 | AVAILABLE | 14 | 0 | 1.0131 | 0.0854 |
| BASELINE | CONTROL | 2023-09 | AVAILABLE | 6 | 1 | 2.2010 | 3.4413 |
| BASELINE | CONTROL | 2023-10 | AVAILABLE | 14 | 0 | 8.3878 | 13.2261 |
| BASELINE | CONTROL | 2023-11 | AVAILABLE | 12 | 0 | 1.5949 | 2.4438 |
| BASELINE | CONTROL | 2023-12 | AVAILABLE | 9 | 0 | 6.6791 | 11.0910 |
| BASELINE | CONTROL | 2024-01 | AVAILABLE | 6 | 1 | 7.5247 | 4.4943 |
| BASELINE | CONTROL | 2024-02 | AVAILABLE | 7 | 0 | 0.5576 | -1.4710 |
| BASELINE | CONTROL | 2024-03 | AVAILABLE | 7 | 0 | 0.4109 | -2.1409 |
| BASELINE | CONTROL | 2024-04 | AVAILABLE | 11 | 0 | 0.3101 | -4.4527 |
| BASELINE | CONTROL | 2024-05 | AVAILABLE | 11 | 0 | 1.1444 | 0.6573 |
| BASELINE | CONTROL | 2024-06 | AVAILABLE | 10 | 0 | 1.0737 | 0.3641 |
| BASELINE | CONTROL | 2024-07 | AVAILABLE | 8 | 1 | 0.2584 | -4.0019 |
| BASELINE | CONTROL | 2024-08 | AVAILABLE | 10 | 0 | 1.9425 | 4.3981 |
| BASELINE | CONTROL | 2024-09 | AVAILABLE | 10 | 0 | 1.4762 | 2.0413 |
| BASELINE | CONTROL | 2024-10 | AVAILABLE | 13 | 0 | 0.3147 | -5.6307 |
| BASELINE | CONTROL | 2024-11 | AVAILABLE | 12 | 0 | 9.5997 | 11.6354 |
| BASELINE | CONTROL | 2024-12 | AVAILABLE | 10 | 0 | 0.7023 | -1.9950 |
| BASELINE | T1 | 2023-01 | AVAILABLE | 5 | 0 | 3.0896 | 4.1792 |
| BASELINE | T1 | 2023-02 | AVAILABLE | 7 | 0 | 2.1723 | 3.2389 |
| BASELINE | T1 | 2023-03 | AVAILABLE | 4 | 0 | 0.8226 | -0.2800 |
| BASELINE | T1 | 2023-04 | AVAILABLE | 5 | 0 | 12.8250 | 14.2001 |
| BASELINE | T1 | 2023-05 | AVAILABLE | 9 | 0 | 0.4930 | -1.9081 |
| BASELINE | T1 | 2023-06 | AVAILABLE | 6 | 1 | 0.8799 | -0.3385 |
| BASELINE | T1 | 2023-07 | AVAILABLE | 8 | 0 | 2.6491 | 5.2958 |
| BASELINE | T1 | 2023-08 | AVAILABLE | 12 | 0 | 0.5121 | -3.1734 |
| BASELINE | T1 | 2023-09 | AVAILABLE | 5 | 0 | 2.3685 | 3.6439 |
| BASELINE | T1 | 2023-10 | AVAILABLE | 9 | 0 | 8.0013 | 8.8625 |
| BASELINE | T1 | 2023-11 | AVAILABLE | 9 | 0 | 1.7182 | 2.3386 |
| BASELINE | T1 | 2023-12 | AVAILABLE | 7 | 0 | 7.7570 | 11.2313 |
| BASELINE | T1 | 2024-01 | AVAILABLE | 5 | 1 | 6.6707 | 3.9060 |
| BASELINE | T1 | 2024-02 | AVAILABLE | 7 | 0 | 0.5576 | -1.4710 |
| BASELINE | T1 | 2024-03 | AVAILABLE | 5 | 0 | 0.5514 | -1.2151 |
| BASELINE | T1 | 2024-04 | AVAILABLE | 9 | 0 | 0.3998 | -3.0049 |
| BASELINE | T1 | 2024-05 | AVAILABLE | 8 | 0 | 0.8547 | -0.6522 |
| BASELINE | T1 | 2024-06 | AVAILABLE | 6 | 0 | 1.1002 | 0.2694 |
| BASELINE | T1 | 2024-07 | AVAILABLE | 4 | 0 | 0.6630 | -0.6740 |
| BASELINE | T1 | 2024-08 | AVAILABLE | 8 | 0 | 3.0310 | 6.0740 |
| BASELINE | T1 | 2024-09 | AVAILABLE | 7 | 0 | 2.5579 | 3.8540 |
| BASELINE | T1 | 2024-10 | AVAILABLE | 11 | 0 | 0.3225 | -5.2629 |
| BASELINE | T1 | 2024-11 | AVAILABLE | 8 | 0 | 6.0469 | 9.5710 |
| BASELINE | T1 | 2024-12 | AVAILABLE | 9 | 0 | 0.8084 | -1.1153 |
| BASELINE | T2 | 2023-01 | AVAILABLE | 5 | 0 | 3.0896 | 4.1792 |
| BASELINE | T2 | 2023-02 | AVAILABLE | 8 | 0 | 1.6664 | 2.4002 |
| BASELINE | T2 | 2023-03 | AVAILABLE | 5 | 0 | 0.7573 | -0.4161 |
| BASELINE | T2 | 2023-04 | AVAILABLE | 6 | 0 | 15.6318 | 17.5708 |
| BASELINE | T2 | 2023-05 | AVAILABLE | 10 | 0 | 0.3895 | -2.9081 |
| BASELINE | T2 | 2023-06 | AVAILABLE | 10 | 1 | 1.5545 | 2.6715 |
| BASELINE | T2 | 2023-07 | AVAILABLE | 9 | 0 | 4.4814 | 9.8295 |
| BASELINE | T2 | 2023-08 | AVAILABLE | 14 | 0 | 0.8307 | -1.2529 |
| BASELINE | T2 | 2023-09 | AVAILABLE | 6 | 1 | 2.2010 | 3.4413 |
| BASELINE | T2 | 2023-10 | AVAILABLE | 14 | 0 | 8.3878 | 13.2261 |
| BASELINE | T2 | 2023-11 | AVAILABLE | 12 | 0 | 1.5949 | 2.4438 |
| BASELINE | T2 | 2023-12 | AVAILABLE | 9 | 0 | 6.6791 | 11.0910 |
| BASELINE | T2 | 2024-01 | AVAILABLE | 6 | 1 | 6.8657 | 4.0404 |
| BASELINE | T2 | 2024-02 | AVAILABLE | 7 | 0 | 0.5576 | -1.4710 |
| BASELINE | T2 | 2024-03 | AVAILABLE | 7 | 0 | 0.4109 | -2.1409 |
| BASELINE | T2 | 2024-04 | AVAILABLE | 11 | 0 | 0.3101 | -4.4527 |
| BASELINE | T2 | 2024-05 | AVAILABLE | 11 | 0 | 1.0140 | 0.0638 |
| BASELINE | T2 | 2024-06 | AVAILABLE | 9 | 0 | 0.9936 | -0.0250 |
| BASELINE | T2 | 2024-07 | AVAILABLE | 8 | 1 | 0.2584 | -4.0019 |
| BASELINE | T2 | 2024-08 | AVAILABLE | 10 | 0 | 1.9425 | 4.3981 |
| BASELINE | T2 | 2024-09 | AVAILABLE | 10 | 0 | 1.4762 | 2.0413 |
| BASELINE | T2 | 2024-10 | AVAILABLE | 12 | 0 | 0.3584 | -4.6307 |
| BASELINE | T2 | 2024-11 | AVAILABLE | 12 | 0 | 9.5997 | 11.6354 |
| BASELINE | T2 | 2024-12 | AVAILABLE | 9 | 0 | 0.8254 | -0.9950 |
| OPTIMIZED | CONTROL | 2023-01 | AVAILABLE | 5 | 0 | 2.9481 | 3.9826 |
| OPTIMIZED | CONTROL | 2023-02 | AVAILABLE | 7 | 0 | 2.6533 | 4.5087 |
| OPTIMIZED | CONTROL | 2023-03 | AVAILABLE | 6 | 0 | 0.2847 | -2.1402 |
| OPTIMIZED | CONTROL | 2023-04 | AVAILABLE | 6 | 0 | 11.8693 | 17.3654 |
| OPTIMIZED | CONTROL | 2023-05 | AVAILABLE | 11 | 0 | 0.3432 | -3.1868 |
| OPTIMIZED | CONTROL | 2023-06 | AVAILABLE | 8 | 1 | 2.8680 | 5.6041 |
| OPTIMIZED | CONTROL | 2023-07 | AVAILABLE | 9 | 0 | 3.1807 | 9.7958 |
| OPTIMIZED | CONTROL | 2023-08 | AVAILABLE | 13 | 0 | 1.1664 | 1.2642 |
| OPTIMIZED | CONTROL | 2023-09 | AVAILABLE | 6 | 1 | 1.9444 | 2.8701 |
| OPTIMIZED | CONTROL | 2023-10 | AVAILABLE | 11 | 0 | 22.9895 | 21.1407 |
| OPTIMIZED | CONTROL | 2023-11 | AVAILABLE | 12 | 0 | 1.0115 | 0.0593 |
| OPTIMIZED | CONTROL | 2023-12 | AVAILABLE | 9 | 0 | 5.2273 | 9.3931 |
| OPTIMIZED | CONTROL | 2024-01 | AVAILABLE | 6 | 1 | 4.7602 | 3.4129 |
| OPTIMIZED | CONTROL | 2024-02 | AVAILABLE | 7 | 0 | 0.3781 | -2.2770 |
| OPTIMIZED | CONTROL | 2024-03 | AVAILABLE | 6 | 0 | 0.6190 | -1.3987 |
| OPTIMIZED | CONTROL | 2024-04 | AVAILABLE | 11 | 0 | 0.2478 | -5.1868 |
| OPTIMIZED | CONTROL | 2024-05 | AVAILABLE | 11 | 0 | 0.9752 | -0.1200 |
| OPTIMIZED | CONTROL | 2024-06 | AVAILABLE | 10 | 0 | 0.9972 | -0.0159 |
| OPTIMIZED | CONTROL | 2024-07 | AVAILABLE | 8 | 1 | 0.2067 | -4.5106 |
| OPTIMIZED | CONTROL | 2024-08 | AVAILABLE | 10 | 0 | 1.7036 | 3.5368 |
| OPTIMIZED | CONTROL | 2024-09 | AVAILABLE | 10 | 0 | 1.9221 | 3.8513 |
| OPTIMIZED | CONTROL | 2024-10 | AVAILABLE | 11 | 0 | 0.8661 | -0.9562 |
| OPTIMIZED | CONTROL | 2024-11 | AVAILABLE | 11 | 0 | 8.3488 | 9.8895 |
| OPTIMIZED | CONTROL | 2024-12 | AVAILABLE | 9 | 0 | 0.8184 | -1.0626 |
| OPTIMIZED | T1 | 2023-01 | AVAILABLE | 5 | 0 | 2.9481 | 3.9826 |
| OPTIMIZED | T1 | 2023-02 | AVAILABLE | 6 | 0 | 3.1414 | 4.9325 |
| OPTIMIZED | T1 | 2023-03 | AVAILABLE | 4 | 0 | 0.4611 | -0.9955 |
| OPTIMIZED | T1 | 2023-04 | AVAILABLE | 5 | 0 | 8.6035 | 12.8491 |
| OPTIMIZED | T1 | 2023-05 | AVAILABLE | 9 | 0 | 0.4437 | -2.0883 |
| OPTIMIZED | T1 | 2023-06 | AVAILABLE | 6 | 1 | 3.8678 | 5.7357 |
| OPTIMIZED | T1 | 2023-07 | AVAILABLE | 7 | 0 | 5.1755 | 11.5271 |
| OPTIMIZED | T1 | 2023-08 | AVAILABLE | 11 | 0 | 0.6839 | -2.2542 |
| OPTIMIZED | T1 | 2023-09 | AVAILABLE | 5 | 0 | 2.2495 | 3.2823 |
| OPTIMIZED | T1 | 2023-10 | AVAILABLE | 8 | 0 | 39.9543 | 17.2340 |
| OPTIMIZED | T1 | 2023-11 | AVAILABLE | 9 | 0 | 1.1223 | 0.5042 |
| OPTIMIZED | T1 | 2023-12 | AVAILABLE | 7 | 0 | 6.1509 | 9.7267 |
| OPTIMIZED | T1 | 2024-01 | AVAILABLE | 5 | 1 | 3.7776 | 2.8953 |
| OPTIMIZED | T1 | 2024-02 | AVAILABLE | 7 | 0 | 0.3781 | -2.2770 |
| OPTIMIZED | T1 | 2024-03 | AVAILABLE | 5 | 0 | 0.3851 | -1.8512 |
| OPTIMIZED | T1 | 2024-04 | AVAILABLE | 9 | 0 | 0.3216 | -3.6041 |
| OPTIMIZED | T1 | 2024-05 | AVAILABLE | 8 | 0 | 0.8039 | -0.9083 |
| OPTIMIZED | T1 | 2024-06 | AVAILABLE | 6 | 0 | 0.8423 | -0.5161 |
| OPTIMIZED | T1 | 2024-07 | AVAILABLE | 4 | 0 | 0.5523 | -0.8955 |
| OPTIMIZED | T1 | 2024-08 | AVAILABLE | 8 | 0 | 2.6296 | 5.3070 |
| OPTIMIZED | T1 | 2024-09 | AVAILABLE | 7 | 0 | 2.4602 | 4.0524 |
| OPTIMIZED | T1 | 2024-10 | AVAILABLE | 10 | 0 | 0.8839 | -0.8130 |
| OPTIMIZED | T1 | 2024-11 | AVAILABLE | 8 | 0 | 5.2600 | 8.3567 |
| OPTIMIZED | T1 | 2024-12 | AVAILABLE | 8 | 0 | 0.9871 | -0.0626 |
| OPTIMIZED | T2 | 2023-01 | AVAILABLE | 5 | 0 | 2.9481 | 3.9826 |
| OPTIMIZED | T2 | 2023-02 | AVAILABLE | 7 | 0 | 2.1904 | 3.9325 |
| OPTIMIZED | T2 | 2023-03 | AVAILABLE | 5 | 0 | 0.3852 | -1.3595 |
| OPTIMIZED | T2 | 2023-04 | AVAILABLE | 6 | 0 | 10.5411 | 16.1235 |
| OPTIMIZED | T2 | 2023-05 | AVAILABLE | 10 | 0 | 0.3504 | -3.0883 |
| OPTIMIZED | T2 | 2023-06 | AVAILABLE | 8 | 1 | 2.8680 | 5.6041 |
| OPTIMIZED | T2 | 2023-07 | AVAILABLE | 8 | 0 | 4.0916 | 10.7958 |
| OPTIMIZED | T2 | 2023-08 | AVAILABLE | 13 | 0 | 0.9023 | -0.7994 |
| OPTIMIZED | T2 | 2023-09 | AVAILABLE | 6 | 1 | 1.9444 | 2.8701 |
| OPTIMIZED | T2 | 2023-10 | AVAILABLE | 11 | 0 | 22.9895 | 21.1407 |
| OPTIMIZED | T2 | 2023-11 | AVAILABLE | 12 | 0 | 1.0115 | 0.0593 |
| OPTIMIZED | T2 | 2023-12 | AVAILABLE | 9 | 0 | 5.2273 | 9.3931 |
| OPTIMIZED | T2 | 2024-01 | AVAILABLE | 6 | 1 | 3.8498 | 2.9705 |
| OPTIMIZED | T2 | 2024-02 | AVAILABLE | 7 | 0 | 0.3781 | -2.2770 |
| OPTIMIZED | T2 | 2024-03 | AVAILABLE | 6 | 0 | 0.6190 | -1.3987 |
| OPTIMIZED | T2 | 2024-04 | AVAILABLE | 11 | 0 | 0.2478 | -5.1868 |
| OPTIMIZED | T2 | 2024-05 | AVAILABLE | 11 | 0 | 0.8594 | -0.6793 |
| OPTIMIZED | T2 | 2024-06 | AVAILABLE | 9 | 0 | 0.8858 | -0.5304 |
| OPTIMIZED | T2 | 2024-07 | AVAILABLE | 8 | 1 | 0.2067 | -4.5106 |
| OPTIMIZED | T2 | 2024-08 | AVAILABLE | 10 | 0 | 1.7036 | 3.5368 |
| OPTIMIZED | T2 | 2024-09 | AVAILABLE | 10 | 0 | 1.9221 | 3.8513 |
| OPTIMIZED | T2 | 2024-10 | AVAILABLE | 10 | 0 | 1.0071 | 0.0438 |
| OPTIMIZED | T2 | 2024-11 | AVAILABLE | 11 | 0 | 8.3488 | 9.8895 |
| OPTIMIZED | T2 | 2024-12 | AVAILABLE | 9 | 0 | 0.8184 | -1.0626 |

### CNYRUBF

| version | rule | month | coverage | closed_trades | open_positions_at_period_end | gross_PF | gross_R |
| --- | --- | --- | --- | --- | --- | --- | --- |
| BASELINE | CONTROL | 2023-01 | AVAILABLE | 2 | 0 | 0.5143 | -0.3694 |
| BASELINE | CONTROL | 2023-02 | AVAILABLE | 7 | 0 | 1.3462 | 0.9187 |
| BASELINE | CONTROL | 2023-03 | AVAILABLE | 7 | 0 | 0.1213 | -5.1227 |
| BASELINE | CONTROL | 2023-04 | AVAILABLE | 8 | 0 | 5.7573 | 10.4780 |
| BASELINE | CONTROL | 2023-05 | AVAILABLE | 9 | 0 | 0.7707 | -1.1379 |
| BASELINE | CONTROL | 2023-06 | AVAILABLE | 5 | 1 | 0.7247 | -0.6483 |
| BASELINE | CONTROL | 2023-07 | AVAILABLE | 4 | 1 | — | 10.3612 |
| BASELINE | CONTROL | 2023-08 | AVAILABLE | 9 | 0 | 0.0723 | -4.1957 |
| BASELINE | CONTROL | 2023-09 | AVAILABLE | 6 | 0 | 4.0780 | 4.5425 |
| BASELINE | CONTROL | 2023-10 | AVAILABLE | 11 | 0 | 4.1398 | 9.1544 |
| BASELINE | CONTROL | 2023-11 | AVAILABLE | 8 | 0 | 2.3373 | 4.0686 |
| BASELINE | CONTROL | 2023-12 | AVAILABLE | 9 | 0 | 1.2983 | 1.1197 |
| BASELINE | CONTROL | 2024-01 | AVAILABLE | 10 | 1 | 2.7342 | 4.2383 |
| BASELINE | CONTROL | 2024-02 | AVAILABLE | 12 | 0 | 0.3884 | -4.1524 |
| BASELINE | CONTROL | 2024-03 | AVAILABLE | 10 | 0 | 0.1870 | -4.7080 |
| BASELINE | CONTROL | 2024-04 | AVAILABLE | 9 | 0 | 1.7044 | 2.4827 |
| BASELINE | CONTROL | 2024-05 | AVAILABLE | 12 | 0 | 0.4171 | -3.9747 |
| BASELINE | CONTROL | 2024-06 | AVAILABLE | 10 | 0 | 1.3262 | 1.7962 |
| BASELINE | CONTROL | 2024-07 | AVAILABLE | 7 | 0 | 0.9518 | -0.1788 |
| BASELINE | CONTROL | 2024-08 | AVAILABLE | 8 | 0 | 0.2477 | -2.9852 |
| BASELINE | CONTROL | 2024-09 | AVAILABLE | 8 | 0 | 3.1857 | 3.8197 |
| BASELINE | CONTROL | 2024-10 | AVAILABLE | 8 | 0 | 1.3834 | 1.3057 |
| BASELINE | CONTROL | 2024-11 | AVAILABLE | 10 | 0 | 6.4841 | 14.0619 |
| BASELINE | CONTROL | 2024-12 | AVAILABLE | 10 | 0 | 1.9131 | 4.1577 |
| BASELINE | T1 | 2023-01 | AVAILABLE | 0 | 0 | — | 0.0000 |
| BASELINE | T1 | 2023-02 | AVAILABLE | 5 | 0 | 2.5466 | 2.1696 |
| BASELINE | T1 | 2023-03 | AVAILABLE | 5 | 0 | 0.1769 | -3.2906 |
| BASELINE | T1 | 2023-04 | AVAILABLE | 5 | 0 | 8.8330 | 9.4193 |
| BASELINE | T1 | 2023-05 | AVAILABLE | 9 | 0 | 0.4362 | -2.7979 |
| BASELINE | T1 | 2023-06 | AVAILABLE | 1 | 1 | — | 0.6470 |
| BASELINE | T1 | 2023-07 | AVAILABLE | 4 | 1 | — | 10.3612 |
| BASELINE | T1 | 2023-08 | AVAILABLE | 7 | 0 | 0.0813 | -3.6939 |
| BASELINE | T1 | 2023-09 | AVAILABLE | 4 | 0 | 6.0183 | 5.0183 |
| BASELINE | T1 | 2023-10 | AVAILABLE | 9 | 0 | 4.2461 | 7.0957 |
| BASELINE | T1 | 2023-11 | AVAILABLE | 6 | 0 | 1.9696 | 2.9498 |
| BASELINE | T1 | 2023-12 | AVAILABLE | 7 | 0 | 2.3212 | 2.7734 |
| BASELINE | T1 | 2024-01 | AVAILABLE | 7 | 1 | 2.6408 | 3.3066 |
| BASELINE | T1 | 2024-02 | AVAILABLE | 9 | 0 | 0.2194 | -3.7504 |
| BASELINE | T1 | 2024-03 | AVAILABLE | 8 | 0 | 0.2322 | -3.5797 |
| BASELINE | T1 | 2024-04 | AVAILABLE | 7 | 0 | 2.8965 | 3.9334 |
| BASELINE | T1 | 2024-05 | AVAILABLE | 11 | 0 | 0.4271 | -3.8159 |
| BASELINE | T1 | 2024-06 | AVAILABLE | 8 | 0 | 0.9891 | -0.0490 |
| BASELINE | T1 | 2024-07 | AVAILABLE | 5 | 0 | 0.0860 | -3.6561 |
| BASELINE | T1 | 2024-08 | AVAILABLE | 6 | 0 | 0.1898 | -2.7186 |
| BASELINE | T1 | 2024-09 | AVAILABLE | 8 | 0 | 3.1857 | 3.8197 |
| BASELINE | T1 | 2024-10 | AVAILABLE | 7 | 0 | 1.5703 | 1.7110 |
| BASELINE | T1 | 2024-11 | AVAILABLE | 8 | 0 | 7.2592 | 13.5825 |
| BASELINE | T1 | 2024-12 | AVAILABLE | 9 | 0 | 2.3514 | 5.0065 |
| BASELINE | T2 | 2023-01 | AVAILABLE | 2 | 0 | 0.5143 | -0.3694 |
| BASELINE | T2 | 2023-02 | AVAILABLE | 6 | 0 | 2.1602 | 1.9187 |
| BASELINE | T2 | 2023-03 | AVAILABLE | 7 | 0 | 0.1213 | -5.1227 |
| BASELINE | T2 | 2023-04 | AVAILABLE | 8 | 0 | 5.7573 | 10.4780 |
| BASELINE | T2 | 2023-05 | AVAILABLE | 9 | 0 | 0.6798 | -1.5892 |
| BASELINE | T2 | 2023-06 | AVAILABLE | 5 | 1 | 0.7247 | -0.6483 |
| BASELINE | T2 | 2023-07 | AVAILABLE | 4 | 1 | — | 10.3612 |
| BASELINE | T2 | 2023-08 | AVAILABLE | 9 | 0 | 0.0601 | -5.1111 |
| BASELINE | T2 | 2023-09 | AVAILABLE | 6 | 0 | 4.0780 | 4.5425 |
| BASELINE | T2 | 2023-10 | AVAILABLE | 11 | 0 | 4.1398 | 9.1544 |
| BASELINE | T2 | 2023-11 | AVAILABLE | 8 | 0 | 2.3373 | 4.0686 |
| BASELINE | T2 | 2023-12 | AVAILABLE | 9 | 0 | 1.2983 | 1.1197 |
| BASELINE | T2 | 2024-01 | AVAILABLE | 10 | 1 | 2.7342 | 4.2383 |
| BASELINE | T2 | 2024-02 | AVAILABLE | 12 | 0 | 0.3884 | -4.1524 |
| BASELINE | T2 | 2024-03 | AVAILABLE | 10 | 0 | 0.1870 | -4.7080 |
| BASELINE | T2 | 2024-04 | AVAILABLE | 9 | 0 | 1.7044 | 2.4827 |
| BASELINE | T2 | 2024-05 | AVAILABLE | 12 | 0 | 0.4171 | -3.9747 |
| BASELINE | T2 | 2024-06 | AVAILABLE | 9 | 0 | 1.5406 | 2.5627 |
| BASELINE | T2 | 2024-07 | AVAILABLE | 7 | 0 | 0.9518 | -0.1788 |
| BASELINE | T2 | 2024-08 | AVAILABLE | 8 | 0 | 0.2477 | -2.9852 |
| BASELINE | T2 | 2024-09 | AVAILABLE | 8 | 0 | 3.1857 | 3.8197 |
| BASELINE | T2 | 2024-10 | AVAILABLE | 7 | 0 | 1.9586 | 2.3057 |
| BASELINE | T2 | 2024-11 | AVAILABLE | 9 | 0 | 6.9446 | 14.2320 |
| BASELINE | T2 | 2024-12 | AVAILABLE | 9 | 0 | 2.4514 | 5.1577 |
| OPTIMIZED | CONTROL | 2023-01 | AVAILABLE | 2 | 0 | 0.2019 | -0.7737 |
| OPTIMIZED | CONTROL | 2023-02 | AVAILABLE | 6 | 0 | 1.9750 | 2.1791 |
| OPTIMIZED | CONTROL | 2023-03 | AVAILABLE | 7 | 0 | 0.0787 | -5.5275 |
| OPTIMIZED | CONTROL | 2023-04 | AVAILABLE | 7 | 0 | 10.4543 | 13.6362 |
| OPTIMIZED | CONTROL | 2023-05 | AVAILABLE | 9 | 0 | 0.6096 | -2.0606 |
| OPTIMIZED | CONTROL | 2023-06 | AVAILABLE | 5 | 1 | 0.4571 | -1.3898 |
| OPTIMIZED | CONTROL | 2023-07 | AVAILABLE | 4 | 1 | — | 9.2663 |
| OPTIMIZED | CONTROL | 2023-08 | AVAILABLE | 9 | 0 | 0.0120 | -5.4652 |
| OPTIMIZED | CONTROL | 2023-09 | AVAILABLE | 6 | 0 | 3.4995 | 4.0366 |
| OPTIMIZED | CONTROL | 2023-10 | AVAILABLE | 11 | 0 | 3.8162 | 8.6859 |
| OPTIMIZED | CONTROL | 2023-11 | AVAILABLE | 8 | 0 | 2.0714 | 3.3172 |
| OPTIMIZED | CONTROL | 2023-12 | AVAILABLE | 8 | 0 | 1.3923 | 1.6416 |
| OPTIMIZED | CONTROL | 2024-01 | AVAILABLE | 10 | 1 | 2.0376 | 2.6991 |
| OPTIMIZED | CONTROL | 2024-02 | AVAILABLE | 10 | 0 | 0.7798 | -1.2581 |
| OPTIMIZED | CONTROL | 2024-03 | AVAILABLE | 10 | 0 | 0.1218 | -5.3427 |
| OPTIMIZED | CONTROL | 2024-04 | AVAILABLE | 8 | 0 | 2.1161 | 4.5349 |
| OPTIMIZED | CONTROL | 2024-05 | AVAILABLE | 12 | 0 | 0.2954 | -5.1227 |
| OPTIMIZED | CONTROL | 2024-06 | AVAILABLE | 8 | 0 | 3.3222 | 10.9638 |
| OPTIMIZED | CONTROL | 2024-07 | AVAILABLE | 7 | 0 | 0.7759 | -0.8587 |
| OPTIMIZED | CONTROL | 2024-08 | AVAILABLE | 7 | 0 | 1.1819 | 0.7126 |
| OPTIMIZED | CONTROL | 2024-09 | AVAILABLE | 8 | 0 | 2.0889 | 2.5291 |
| OPTIMIZED | CONTROL | 2024-10 | AVAILABLE | 8 | 0 | 1.2489 | 0.8784 |
| OPTIMIZED | CONTROL | 2024-11 | AVAILABLE | 10 | 0 | 4.5384 | 11.8515 |
| OPTIMIZED | CONTROL | 2024-12 | AVAILABLE | 8 | 0 | 3.6412 | 8.9668 |
| OPTIMIZED | T1 | 2023-01 | AVAILABLE | 0 | 0 | — | 0.0000 |
| OPTIMIZED | T1 | 2023-02 | AVAILABLE | 5 | 0 | 2.7450 | 2.8060 |
| OPTIMIZED | T1 | 2023-03 | AVAILABLE | 5 | 0 | 0.1181 | -3.5275 |
| OPTIMIZED | T1 | 2023-04 | AVAILABLE | 5 | 0 | 6.7646 | 8.3144 |
| OPTIMIZED | T1 | 2023-05 | AVAILABLE | 9 | 0 | 0.3006 | -3.6914 |
| OPTIMIZED | T1 | 2023-06 | AVAILABLE | 1 | 1 | — | 0.3476 |
| OPTIMIZED | T1 | 2023-07 | AVAILABLE | 4 | 1 | — | 9.2663 |
| OPTIMIZED | T1 | 2023-08 | AVAILABLE | 7 | 0 | 0.0144 | -4.5531 |
| OPTIMIZED | T1 | 2023-09 | AVAILABLE | 4 | 0 | 5.6516 | 4.6516 |
| OPTIMIZED | T1 | 2023-10 | AVAILABLE | 9 | 0 | 4.0135 | 6.9740 |
| OPTIMIZED | T1 | 2023-11 | AVAILABLE | 6 | 0 | 1.7563 | 2.2960 |
| OPTIMIZED | T1 | 2023-12 | AVAILABLE | 6 | 0 | 2.3022 | 3.2953 |
| OPTIMIZED | T1 | 2024-01 | AVAILABLE | 7 | 1 | 1.8654 | 2.1031 |
| OPTIMIZED | T1 | 2024-02 | AVAILABLE | 8 | 0 | 0.6470 | -1.6634 |
| OPTIMIZED | T1 | 2024-03 | AVAILABLE | 8 | 0 | 0.1545 | -4.0557 |
| OPTIMIZED | T1 | 2024-04 | AVAILABLE | 6 | 0 | 3.5358 | 6.1664 |
| OPTIMIZED | T1 | 2024-05 | AVAILABLE | 11 | 0 | 0.3068 | -4.8523 |
| OPTIMIZED | T1 | 2024-06 | AVAILABLE | 6 | 0 | 3.5230 | 9.3891 |
| OPTIMIZED | T1 | 2024-07 | AVAILABLE | 5 | 0 | 0.0667 | -3.7330 |
| OPTIMIZED | T1 | 2024-08 | AVAILABLE | 6 | 0 | 1.4792 | 1.4997 |
| OPTIMIZED | T1 | 2024-09 | AVAILABLE | 8 | 0 | 2.0889 | 2.5291 |
| OPTIMIZED | T1 | 2024-10 | AVAILABLE | 7 | 0 | 1.4695 | 1.4084 |
| OPTIMIZED | T1 | 2024-11 | AVAILABLE | 8 | 0 | 5.2424 | 11.8221 |
| OPTIMIZED | T1 | 2024-12 | AVAILABLE | 7 | 0 | 5.1616 | 9.9668 |
| OPTIMIZED | T2 | 2023-01 | AVAILABLE | 2 | 0 | 0.2019 | -0.7737 |
| OPTIMIZED | T2 | 2023-02 | AVAILABLE | 6 | 0 | 1.9750 | 2.1791 |
| OPTIMIZED | T2 | 2023-03 | AVAILABLE | 7 | 0 | 0.0787 | -5.5275 |
| OPTIMIZED | T2 | 2023-04 | AVAILABLE | 7 | 0 | 10.4543 | 13.6362 |
| OPTIMIZED | T2 | 2023-05 | AVAILABLE | 9 | 0 | 0.5253 | -2.5055 |
| OPTIMIZED | T2 | 2023-06 | AVAILABLE | 5 | 1 | 0.4571 | -1.3898 |
| OPTIMIZED | T2 | 2023-07 | AVAILABLE | 4 | 1 | — | 9.2663 |
| OPTIMIZED | T2 | 2023-08 | AVAILABLE | 9 | 0 | 0.0108 | -6.1082 |
| OPTIMIZED | T2 | 2023-09 | AVAILABLE | 6 | 0 | 3.4995 | 4.0366 |
| OPTIMIZED | T2 | 2023-10 | AVAILABLE | 11 | 0 | 3.8162 | 8.6859 |
| OPTIMIZED | T2 | 2023-11 | AVAILABLE | 8 | 0 | 2.0714 | 3.3172 |
| OPTIMIZED | T2 | 2023-12 | AVAILABLE | 8 | 0 | 1.3923 | 1.6416 |
| OPTIMIZED | T2 | 2024-01 | AVAILABLE | 10 | 1 | 2.0376 | 2.6991 |
| OPTIMIZED | T2 | 2024-02 | AVAILABLE | 10 | 0 | 0.7798 | -1.2581 |
| OPTIMIZED | T2 | 2024-03 | AVAILABLE | 10 | 0 | 0.1218 | -5.3427 |
| OPTIMIZED | T2 | 2024-04 | AVAILABLE | 8 | 0 | 2.1161 | 4.5349 |
| OPTIMIZED | T2 | 2024-05 | AVAILABLE | 12 | 0 | 0.2954 | -5.1227 |
| OPTIMIZED | T2 | 2024-06 | AVAILABLE | 8 | 0 | 3.3222 | 10.9638 |
| OPTIMIZED | T2 | 2024-07 | AVAILABLE | 7 | 0 | 0.7759 | -0.8587 |
| OPTIMIZED | T2 | 2024-08 | AVAILABLE | 7 | 0 | 1.1819 | 0.7126 |
| OPTIMIZED | T2 | 2024-09 | AVAILABLE | 8 | 0 | 2.0889 | 2.5291 |
| OPTIMIZED | T2 | 2024-10 | AVAILABLE | 7 | 0 | 1.7425 | 1.8784 |
| OPTIMIZED | T2 | 2024-11 | AVAILABLE | 9 | 0 | 5.6940 | 12.5312 |
| OPTIMIZED | T2 | 2024-12 | AVAILABLE | 8 | 0 | 3.6412 | 8.9668 |

### GLDRUBF

| version | rule | month | coverage | closed_trades | open_positions_at_period_end | gross_PF | gross_R |
| --- | --- | --- | --- | --- | --- | --- | --- |
| BASELINE | CONTROL | 2023-01 | NO_COVERAGE | 0 | 0 | — | 0.0000 |
| BASELINE | CONTROL | 2023-02 | NO_COVERAGE | 0 | 0 | — | 0.0000 |
| BASELINE | CONTROL | 2023-03 | NO_COVERAGE | 0 | 0 | — | 0.0000 |
| BASELINE | CONTROL | 2023-04 | NO_COVERAGE | 0 | 0 | — | 0.0000 |
| BASELINE | CONTROL | 2023-05 | NO_COVERAGE | 0 | 0 | — | 0.0000 |
| BASELINE | CONTROL | 2023-06 | NO_COVERAGE | 0 | 0 | — | 0.0000 |
| BASELINE | CONTROL | 2023-07 | AVAILABLE | 4 | 0 | 0.0601 | -1.8481 |
| BASELINE | CONTROL | 2023-08 | AVAILABLE | 13 | 0 | 0.2840 | -4.3327 |
| BASELINE | CONTROL | 2023-09 | AVAILABLE | 7 | 0 | 0.5685 | -2.1424 |
| BASELINE | CONTROL | 2023-10 | AVAILABLE | 8 | 0 | 0.5405 | -0.8279 |
| BASELINE | CONTROL | 2023-11 | AVAILABLE | 7 | 0 | 1.8131 | 2.6422 |
| BASELINE | CONTROL | 2023-12 | AVAILABLE | 12 | 0 | 2.2378 | 6.4063 |
| BASELINE | CONTROL | 2024-01 | AVAILABLE | 6 | 0 | 0.5475 | -1.2940 |
| BASELINE | CONTROL | 2024-02 | AVAILABLE | 11 | 0 | 0.4072 | -3.5200 |
| BASELINE | CONTROL | 2024-03 | AVAILABLE | 13 | 0 | 2.0035 | 5.5150 |
| BASELINE | CONTROL | 2024-04 | AVAILABLE | 12 | 1 | 2.3743 | 6.4031 |
| BASELINE | CONTROL | 2024-05 | AVAILABLE | 7 | 0 | 1.5261 | 1.2444 |
| BASELINE | CONTROL | 2024-06 | AVAILABLE | 12 | 0 | 0.0999 | -6.4588 |
| BASELINE | CONTROL | 2024-07 | AVAILABLE | 10 | 1 | 2.0945 | 3.4535 |
| BASELINE | CONTROL | 2024-08 | AVAILABLE | 13 | 0 | 1.1819 | 1.1723 |
| BASELINE | CONTROL | 2024-09 | AVAILABLE | 7 | 0 | 0.0000 | -3.9822 |
| BASELINE | CONTROL | 2024-10 | AVAILABLE | 12 | 0 | 1.1558 | 0.7828 |
| BASELINE | CONTROL | 2024-11 | AVAILABLE | 11 | 0 | 4.7138 | 13.1694 |
| BASELINE | CONTROL | 2024-12 | AVAILABLE | 13 | 0 | 0.2242 | -5.2146 |
| BASELINE | T1 | 2023-01 | NO_COVERAGE | 0 | 0 | — | 0.0000 |
| BASELINE | T1 | 2023-02 | NO_COVERAGE | 0 | 0 | — | 0.0000 |
| BASELINE | T1 | 2023-03 | NO_COVERAGE | 0 | 0 | — | 0.0000 |
| BASELINE | T1 | 2023-04 | NO_COVERAGE | 0 | 0 | — | 0.0000 |
| BASELINE | T1 | 2023-05 | NO_COVERAGE | 0 | 0 | — | 0.0000 |
| BASELINE | T1 | 2023-06 | NO_COVERAGE | 0 | 0 | — | 0.0000 |
| BASELINE | T1 | 2023-07 | AVAILABLE | 3 | 0 | 0.0678 | -1.6256 |
| BASELINE | T1 | 2023-08 | AVAILABLE | 11 | 0 | 0.3198 | -3.5215 |
| BASELINE | T1 | 2023-09 | AVAILABLE | 5 | 0 | 0.7350 | -1.0180 |
| BASELINE | T1 | 2023-10 | AVAILABLE | 7 | 0 | 0.4696 | -0.9557 |
| BASELINE | T1 | 2023-11 | AVAILABLE | 5 | 0 | 2.6740 | 3.6882 |
| BASELINE | T1 | 2023-12 | AVAILABLE | 10 | 0 | 1.7717 | 3.8033 |
| BASELINE | T1 | 2024-01 | AVAILABLE | 5 | 0 | 0.8419 | -0.2940 |
| BASELINE | T1 | 2024-02 | AVAILABLE | 6 | 0 | 0.0000 | -3.3343 |
| BASELINE | T1 | 2024-03 | AVAILABLE | 8 | 0 | 3.2806 | 6.8419 |
| BASELINE | T1 | 2024-04 | AVAILABLE | 9 | 1 | 1.6736 | 2.9963 |
| BASELINE | T1 | 2024-05 | AVAILABLE | 5 | 0 | 2.0344 | 1.5144 |
| BASELINE | T1 | 2024-06 | AVAILABLE | 9 | 0 | 0.0768 | -5.7027 |
| BASELINE | T1 | 2024-07 | AVAILABLE | 7 | 0 | 3.6669 | 4.6680 |
| BASELINE | T1 | 2024-08 | AVAILABLE | 9 | 0 | 2.1839 | 4.0771 |
| BASELINE | T1 | 2024-09 | AVAILABLE | 3 | 0 | 0.0000 | -1.1105 |
| BASELINE | T1 | 2024-10 | AVAILABLE | 8 | 0 | 1.6737 | 2.0079 |
| BASELINE | T1 | 2024-11 | AVAILABLE | 8 | 0 | 545.6981 | 16.2869 |
| BASELINE | T1 | 2024-12 | AVAILABLE | 9 | 0 | 0.3299 | -3.0612 |
| BASELINE | T2 | 2023-01 | NO_COVERAGE | 0 | 0 | — | 0.0000 |
| BASELINE | T2 | 2023-02 | NO_COVERAGE | 0 | 0 | — | 0.0000 |
| BASELINE | T2 | 2023-03 | NO_COVERAGE | 0 | 0 | — | 0.0000 |
| BASELINE | T2 | 2023-04 | NO_COVERAGE | 0 | 0 | — | 0.0000 |
| BASELINE | T2 | 2023-05 | NO_COVERAGE | 0 | 0 | — | 0.0000 |
| BASELINE | T2 | 2023-06 | NO_COVERAGE | 0 | 0 | — | 0.0000 |
| BASELINE | T2 | 2023-07 | AVAILABLE | 4 | 0 | 0.0601 | -1.8481 |
| BASELINE | T2 | 2023-08 | AVAILABLE | 13 | 0 | 0.2840 | -4.3327 |
| BASELINE | T2 | 2023-09 | AVAILABLE | 6 | 0 | 0.6280 | -1.6720 |
| BASELINE | T2 | 2023-10 | AVAILABLE | 8 | 0 | 0.5405 | -0.8279 |
| BASELINE | T2 | 2023-11 | AVAILABLE | 7 | 0 | 1.8131 | 2.6422 |
| BASELINE | T2 | 2023-12 | AVAILABLE | 12 | 0 | 2.2378 | 6.4063 |
| BASELINE | T2 | 2024-01 | AVAILABLE | 6 | 0 | 0.5475 | -1.2940 |
| BASELINE | T2 | 2024-02 | AVAILABLE | 11 | 0 | 0.2370 | -5.2937 |
| BASELINE | T2 | 2024-03 | AVAILABLE | 13 | 0 | 2.0035 | 5.5150 |
| BASELINE | T2 | 2024-04 | AVAILABLE | 12 | 1 | 2.3743 | 6.4031 |
| BASELINE | T2 | 2024-05 | AVAILABLE | 7 | 0 | 1.5261 | 1.2444 |
| BASELINE | T2 | 2024-06 | AVAILABLE | 12 | 0 | 0.0999 | -6.4588 |
| BASELINE | T2 | 2024-07 | AVAILABLE | 10 | 1 | 2.0945 | 3.4535 |
| BASELINE | T2 | 2024-08 | AVAILABLE | 13 | 0 | 1.1819 | 1.1723 |
| BASELINE | T2 | 2024-09 | AVAILABLE | 7 | 0 | 0.0000 | -3.9822 |
| BASELINE | T2 | 2024-10 | AVAILABLE | 12 | 0 | 0.9713 | -0.1684 |
| BASELINE | T2 | 2024-11 | AVAILABLE | 11 | 0 | 4.7138 | 13.1694 |
| BASELINE | T2 | 2024-12 | AVAILABLE | 13 | 0 | 0.2242 | -5.2146 |
| OPTIMIZED | CONTROL | 2023-01 | NO_COVERAGE | 0 | 0 | — | 0.0000 |
| OPTIMIZED | CONTROL | 2023-02 | NO_COVERAGE | 0 | 0 | — | 0.0000 |
| OPTIMIZED | CONTROL | 2023-03 | NO_COVERAGE | 0 | 0 | — | 0.0000 |
| OPTIMIZED | CONTROL | 2023-04 | NO_COVERAGE | 0 | 0 | — | 0.0000 |
| OPTIMIZED | CONTROL | 2023-05 | NO_COVERAGE | 0 | 0 | — | 0.0000 |
| OPTIMIZED | CONTROL | 2023-06 | NO_COVERAGE | 0 | 0 | — | 0.0000 |
| OPTIMIZED | CONTROL | 2023-07 | AVAILABLE | 3 | 1 | 0.0000 | -2.3362 |
| OPTIMIZED | CONTROL | 2023-08 | AVAILABLE | 14 | 0 | 0.2813 | -5.2065 |
| OPTIMIZED | CONTROL | 2023-09 | AVAILABLE | 6 | 0 | 1.0990 | 0.4781 |
| OPTIMIZED | CONTROL | 2023-10 | AVAILABLE | 8 | 0 | 0.1734 | -2.0774 |
| OPTIMIZED | CONTROL | 2023-11 | AVAILABLE | 7 | 0 | 1.4524 | 1.7044 |
| OPTIMIZED | CONTROL | 2023-12 | AVAILABLE | 11 | 0 | 2.5168 | 8.1967 |
| OPTIMIZED | CONTROL | 2024-01 | AVAILABLE | 6 | 0 | 0.5654 | -1.4163 |
| OPTIMIZED | CONTROL | 2024-02 | AVAILABLE | 10 | 0 | 0.3876 | -3.4272 |
| OPTIMIZED | CONTROL | 2024-03 | AVAILABLE | 13 | 0 | 1.9345 | 5.2989 |
| OPTIMIZED | CONTROL | 2024-04 | AVAILABLE | 12 | 1 | 1.8007 | 4.4069 |
| OPTIMIZED | CONTROL | 2024-05 | AVAILABLE | 7 | 0 | 1.1614 | 0.4489 |
| OPTIMIZED | CONTROL | 2024-06 | AVAILABLE | 12 | 0 | 0.3308 | -4.9243 |
| OPTIMIZED | CONTROL | 2024-07 | AVAILABLE | 10 | 1 | 1.7385 | 2.5091 |
| OPTIMIZED | CONTROL | 2024-08 | AVAILABLE | 11 | 0 | 1.3796 | 1.8695 |
| OPTIMIZED | CONTROL | 2024-09 | AVAILABLE | 6 | 0 | 0.1937 | -2.8897 |
| OPTIMIZED | CONTROL | 2024-10 | AVAILABLE | 12 | 0 | 0.8216 | -1.0763 |
| OPTIMIZED | CONTROL | 2024-11 | AVAILABLE | 7 | 0 | 42.2009 | 22.4126 |
| OPTIMIZED | CONTROL | 2024-12 | AVAILABLE | 11 | 0 | 0.6533 | -2.6554 |
| OPTIMIZED | T1 | 2023-01 | NO_COVERAGE | 0 | 0 | — | 0.0000 |
| OPTIMIZED | T1 | 2023-02 | NO_COVERAGE | 0 | 0 | — | 0.0000 |
| OPTIMIZED | T1 | 2023-03 | NO_COVERAGE | 0 | 0 | — | 0.0000 |
| OPTIMIZED | T1 | 2023-04 | NO_COVERAGE | 0 | 0 | — | 0.0000 |
| OPTIMIZED | T1 | 2023-05 | NO_COVERAGE | 0 | 0 | — | 0.0000 |
| OPTIMIZED | T1 | 2023-06 | NO_COVERAGE | 0 | 0 | — | 0.0000 |
| OPTIMIZED | T1 | 2023-07 | AVAILABLE | 2 | 1 | 0.0000 | -1.9043 |
| OPTIMIZED | T1 | 2023-08 | AVAILABLE | 12 | 0 | 0.3383 | -3.9857 |
| OPTIMIZED | T1 | 2023-09 | AVAILABLE | 5 | 0 | 1.3262 | 1.3048 |
| OPTIMIZED | T1 | 2023-10 | AVAILABLE | 7 | 0 | 0.1783 | -2.0084 |
| OPTIMIZED | T1 | 2023-11 | AVAILABLE | 5 | 0 | 2.1833 | 2.9655 |
| OPTIMIZED | T1 | 2023-12 | AVAILABLE | 10 | 0 | 2.3924 | 7.5246 |
| OPTIMIZED | T1 | 2024-01 | AVAILABLE | 5 | 0 | 0.8157 | -0.4163 |
| OPTIMIZED | T1 | 2024-02 | AVAILABLE | 6 | 0 | 0.0000 | -3.9699 |
| OPTIMIZED | T1 | 2024-03 | AVAILABLE | 8 | 0 | 3.3025 | 6.9076 |
| OPTIMIZED | T1 | 2024-04 | AVAILABLE | 9 | 1 | 1.3355 | 1.6799 |
| OPTIMIZED | T1 | 2024-05 | AVAILABLE | 5 | 0 | 1.4710 | 0.8854 |
| OPTIMIZED | T1 | 2024-06 | AVAILABLE | 9 | 0 | 0.0300 | -6.2199 |
| OPTIMIZED | T1 | 2024-07 | AVAILABLE | 7 | 0 | 2.9705 | 3.7917 |
| OPTIMIZED | T1 | 2024-08 | AVAILABLE | 8 | 0 | 2.4299 | 3.9986 |
| OPTIMIZED | T1 | 2024-09 | AVAILABLE | 3 | 0 | 1.1501 | 0.0906 |
| OPTIMIZED | T1 | 2024-10 | AVAILABLE | 8 | 0 | 1.1864 | 0.6819 |
| OPTIMIZED | T1 | 2024-11 | AVAILABLE | 6 | 0 | 41.8594 | 22.2268 |
| OPTIMIZED | T1 | 2024-12 | AVAILABLE | 8 | 0 | 0.7403 | -1.4442 |
| OPTIMIZED | T2 | 2023-01 | NO_COVERAGE | 0 | 0 | — | 0.0000 |
| OPTIMIZED | T2 | 2023-02 | NO_COVERAGE | 0 | 0 | — | 0.0000 |
| OPTIMIZED | T2 | 2023-03 | NO_COVERAGE | 0 | 0 | — | 0.0000 |
| OPTIMIZED | T2 | 2023-04 | NO_COVERAGE | 0 | 0 | — | 0.0000 |
| OPTIMIZED | T2 | 2023-05 | NO_COVERAGE | 0 | 0 | — | 0.0000 |
| OPTIMIZED | T2 | 2023-06 | NO_COVERAGE | 0 | 0 | — | 0.0000 |
| OPTIMIZED | T2 | 2023-07 | AVAILABLE | 3 | 1 | 0.0000 | -2.3362 |
| OPTIMIZED | T2 | 2023-08 | AVAILABLE | 14 | 0 | 0.2813 | -5.2065 |
| OPTIMIZED | T2 | 2023-09 | AVAILABLE | 6 | 0 | 1.0990 | 0.4781 |
| OPTIMIZED | T2 | 2023-10 | AVAILABLE | 8 | 0 | 0.1734 | -2.0774 |
| OPTIMIZED | T2 | 2023-11 | AVAILABLE | 7 | 0 | 1.4524 | 1.7044 |
| OPTIMIZED | T2 | 2023-12 | AVAILABLE | 11 | 0 | 2.5168 | 8.1967 |
| OPTIMIZED | T2 | 2024-01 | AVAILABLE | 6 | 0 | 0.5654 | -1.4163 |
| OPTIMIZED | T2 | 2024-02 | AVAILABLE | 10 | 0 | 0.2115 | -5.2008 |
| OPTIMIZED | T2 | 2024-03 | AVAILABLE | 13 | 0 | 1.9345 | 5.2989 |
| OPTIMIZED | T2 | 2024-04 | AVAILABLE | 12 | 1 | 1.8007 | 4.4069 |
| OPTIMIZED | T2 | 2024-05 | AVAILABLE | 7 | 0 | 1.1614 | 0.4489 |
| OPTIMIZED | T2 | 2024-06 | AVAILABLE | 12 | 0 | 0.3308 | -4.9243 |
| OPTIMIZED | T2 | 2024-07 | AVAILABLE | 10 | 1 | 1.7385 | 2.5091 |
| OPTIMIZED | T2 | 2024-08 | AVAILABLE | 11 | 0 | 1.3796 | 1.8695 |
| OPTIMIZED | T2 | 2024-09 | AVAILABLE | 6 | 0 | 0.1937 | -2.8897 |
| OPTIMIZED | T2 | 2024-10 | AVAILABLE | 12 | 0 | 0.7126 | -1.9994 |
| OPTIMIZED | T2 | 2024-11 | AVAILABLE | 7 | 0 | 42.2009 | 22.4126 |
| OPTIMIZED | T2 | 2024-12 | AVAILABLE | 11 | 0 | 0.6533 | -2.6554 |

### IMOEXF

| version | rule | month | coverage | closed_trades | open_positions_at_period_end | gross_PF | gross_R |
| --- | --- | --- | --- | --- | --- | --- | --- |
| BASELINE | CONTROL | 2023-01 | NO_COVERAGE | 0 | 0 | — | 0.0000 |
| BASELINE | CONTROL | 2023-02 | NO_COVERAGE | 0 | 0 | — | 0.0000 |
| BASELINE | CONTROL | 2023-03 | NO_COVERAGE | 0 | 0 | — | 0.0000 |
| BASELINE | CONTROL | 2023-04 | NO_COVERAGE | 0 | 0 | — | 0.0000 |
| BASELINE | CONTROL | 2023-05 | NO_COVERAGE | 0 | 0 | — | 0.0000 |
| BASELINE | CONTROL | 2023-06 | NO_COVERAGE | 0 | 0 | — | 0.0000 |
| BASELINE | CONTROL | 2023-07 | NO_COVERAGE | 0 | 0 | — | 0.0000 |
| BASELINE | CONTROL | 2023-08 | NO_COVERAGE | 0 | 0 | — | 0.0000 |
| BASELINE | CONTROL | 2023-09 | NO_COVERAGE | 0 | 0 | — | 0.0000 |
| BASELINE | CONTROL | 2023-10 | NO_COVERAGE | 0 | 0 | — | 0.0000 |
| BASELINE | CONTROL | 2023-11 | AVAILABLE | 1 | 0 | 0.0000 | -1.0000 |
| BASELINE | CONTROL | 2023-12 | AVAILABLE | 8 | 0 | 1.5182 | 1.2796 |
| BASELINE | CONTROL | 2024-01 | AVAILABLE | 10 | 1 | 0.5194 | -3.1777 |
| BASELINE | CONTROL | 2024-02 | AVAILABLE | 9 | 0 | 3.3744 | 5.8495 |
| BASELINE | CONTROL | 2024-03 | AVAILABLE | 8 | 0 | 1.1172 | 0.4058 |
| BASELINE | CONTROL | 2024-04 | AVAILABLE | 17 | 0 | 0.3819 | -5.1320 |
| BASELINE | CONTROL | 2024-05 | AVAILABLE | 12 | 1 | 1.1105 | 0.4020 |
| BASELINE | CONTROL | 2024-06 | AVAILABLE | 11 | 0 | 1.2127 | 0.8574 |
| BASELINE | CONTROL | 2024-07 | AVAILABLE | 11 | 0 | 1.7772 | 4.1880 |
| BASELINE | CONTROL | 2024-08 | AVAILABLE | 12 | 1 | 0.6756 | -1.9614 |
| BASELINE | CONTROL | 2024-09 | AVAILABLE | 11 | 0 | 1.4746 | 1.9699 |
| BASELINE | CONTROL | 2024-10 | AVAILABLE | 9 | 0 | 0.8283 | -0.7367 |
| BASELINE | CONTROL | 2024-11 | AVAILABLE | 11 | 0 | 3.3848 | 11.6619 |
| BASELINE | CONTROL | 2024-12 | AVAILABLE | 8 | 1 | 2.6485 | 4.8470 |
| BASELINE | T1 | 2023-01 | NO_COVERAGE | 0 | 0 | — | 0.0000 |
| BASELINE | T1 | 2023-02 | NO_COVERAGE | 0 | 0 | — | 0.0000 |
| BASELINE | T1 | 2023-03 | NO_COVERAGE | 0 | 0 | — | 0.0000 |
| BASELINE | T1 | 2023-04 | NO_COVERAGE | 0 | 0 | — | 0.0000 |
| BASELINE | T1 | 2023-05 | NO_COVERAGE | 0 | 0 | — | 0.0000 |
| BASELINE | T1 | 2023-06 | NO_COVERAGE | 0 | 0 | — | 0.0000 |
| BASELINE | T1 | 2023-07 | NO_COVERAGE | 0 | 0 | — | 0.0000 |
| BASELINE | T1 | 2023-08 | NO_COVERAGE | 0 | 0 | — | 0.0000 |
| BASELINE | T1 | 2023-09 | NO_COVERAGE | 0 | 0 | — | 0.0000 |
| BASELINE | T1 | 2023-10 | NO_COVERAGE | 0 | 0 | — | 0.0000 |
| BASELINE | T1 | 2023-11 | AVAILABLE | 1 | 0 | 0.0000 | -1.0000 |
| BASELINE | T1 | 2023-12 | AVAILABLE | 7 | 0 | 1.2448 | 0.6046 |
| BASELINE | T1 | 2024-01 | AVAILABLE | 8 | 1 | 0.5944 | -2.2765 |
| BASELINE | T1 | 2024-02 | AVAILABLE | 8 | 0 | 1.7182 | 1.7693 |
| BASELINE | T1 | 2024-03 | AVAILABLE | 7 | 0 | 1.3629 | 1.0297 |
| BASELINE | T1 | 2024-04 | AVAILABLE | 13 | 0 | 0.5061 | -3.0931 |
| BASELINE | T1 | 2024-05 | AVAILABLE | 10 | 0 | 0.8343 | -0.6723 |
| BASELINE | T1 | 2024-06 | AVAILABLE | 8 | 0 | 0.5133 | -1.8236 |
| BASELINE | T1 | 2024-07 | AVAILABLE | 9 | 0 | 2.0367 | 4.1468 |
| BASELINE | T1 | 2024-08 | AVAILABLE | 10 | 1 | 0.6798 | -1.8295 |
| BASELINE | T1 | 2024-09 | AVAILABLE | 8 | 0 | 1.3934 | 1.6188 |
| BASELINE | T1 | 2024-10 | AVAILABLE | 8 | 0 | 0.9006 | -0.3921 |
| BASELINE | T1 | 2024-11 | AVAILABLE | 9 | 0 | 2.2154 | 4.7536 |
| BASELINE | T1 | 2024-12 | AVAILABLE | 7 | 1 | 3.2795 | 5.4127 |
| BASELINE | T2 | 2023-01 | NO_COVERAGE | 0 | 0 | — | 0.0000 |
| BASELINE | T2 | 2023-02 | NO_COVERAGE | 0 | 0 | — | 0.0000 |
| BASELINE | T2 | 2023-03 | NO_COVERAGE | 0 | 0 | — | 0.0000 |
| BASELINE | T2 | 2023-04 | NO_COVERAGE | 0 | 0 | — | 0.0000 |
| BASELINE | T2 | 2023-05 | NO_COVERAGE | 0 | 0 | — | 0.0000 |
| BASELINE | T2 | 2023-06 | NO_COVERAGE | 0 | 0 | — | 0.0000 |
| BASELINE | T2 | 2023-07 | NO_COVERAGE | 0 | 0 | — | 0.0000 |
| BASELINE | T2 | 2023-08 | NO_COVERAGE | 0 | 0 | — | 0.0000 |
| BASELINE | T2 | 2023-09 | NO_COVERAGE | 0 | 0 | — | 0.0000 |
| BASELINE | T2 | 2023-10 | NO_COVERAGE | 0 | 0 | — | 0.0000 |
| BASELINE | T2 | 2023-11 | AVAILABLE | 1 | 0 | 0.0000 | -1.0000 |
| BASELINE | T2 | 2023-12 | AVAILABLE | 8 | 0 | 1.5182 | 1.2796 |
| BASELINE | T2 | 2024-01 | AVAILABLE | 10 | 1 | 0.5194 | -3.1777 |
| BASELINE | T2 | 2024-02 | AVAILABLE | 9 | 0 | 3.3744 | 5.8495 |
| BASELINE | T2 | 2024-03 | AVAILABLE | 8 | 0 | 1.1172 | 0.4058 |
| BASELINE | T2 | 2024-04 | AVAILABLE | 17 | 0 | 0.3819 | -5.1320 |
| BASELINE | T2 | 2024-05 | AVAILABLE | 12 | 1 | 1.1105 | 0.4020 |
| BASELINE | T2 | 2024-06 | AVAILABLE | 11 | 0 | 0.9778 | -0.1109 |
| BASELINE | T2 | 2024-07 | AVAILABLE | 10 | 0 | 2.1822 | 5.1880 |
| BASELINE | T2 | 2024-08 | AVAILABLE | 12 | 1 | 0.6756 | -1.9614 |
| BASELINE | T2 | 2024-09 | AVAILABLE | 11 | 0 | 1.4746 | 1.9699 |
| BASELINE | T2 | 2024-10 | AVAILABLE | 9 | 0 | 0.8283 | -0.7367 |
| BASELINE | T2 | 2024-11 | AVAILABLE | 11 | 0 | 3.3848 | 11.6619 |
| BASELINE | T2 | 2024-12 | AVAILABLE | 9 | 1 | 1.8329 | 3.2819 |
| OPTIMIZED | CONTROL | 2023-01 | NO_COVERAGE | 0 | 0 | — | 0.0000 |
| OPTIMIZED | CONTROL | 2023-02 | NO_COVERAGE | 0 | 0 | — | 0.0000 |
| OPTIMIZED | CONTROL | 2023-03 | NO_COVERAGE | 0 | 0 | — | 0.0000 |
| OPTIMIZED | CONTROL | 2023-04 | NO_COVERAGE | 0 | 0 | — | 0.0000 |
| OPTIMIZED | CONTROL | 2023-05 | NO_COVERAGE | 0 | 0 | — | 0.0000 |
| OPTIMIZED | CONTROL | 2023-06 | NO_COVERAGE | 0 | 0 | — | 0.0000 |
| OPTIMIZED | CONTROL | 2023-07 | NO_COVERAGE | 0 | 0 | — | 0.0000 |
| OPTIMIZED | CONTROL | 2023-08 | NO_COVERAGE | 0 | 0 | — | 0.0000 |
| OPTIMIZED | CONTROL | 2023-09 | NO_COVERAGE | 0 | 0 | — | 0.0000 |
| OPTIMIZED | CONTROL | 2023-10 | NO_COVERAGE | 0 | 0 | — | 0.0000 |
| OPTIMIZED | CONTROL | 2023-11 | AVAILABLE | 1 | 0 | 0.0000 | -1.0000 |
| OPTIMIZED | CONTROL | 2023-12 | AVAILABLE | 8 | 0 | 1.2309 | 0.6560 |
| OPTIMIZED | CONTROL | 2024-01 | AVAILABLE | 10 | 1 | 0.8173 | -1.2496 |
| OPTIMIZED | CONTROL | 2024-02 | AVAILABLE | 9 | 0 | 2.8741 | 5.4850 |
| OPTIMIZED | CONTROL | 2024-03 | AVAILABLE | 7 | 0 | 2.1966 | 4.4889 |
| OPTIMIZED | CONTROL | 2024-04 | AVAILABLE | 17 | 0 | 0.3330 | -5.7034 |
| OPTIMIZED | CONTROL | 2024-05 | AVAILABLE | 11 | 1 | 1.9051 | 3.3915 |
| OPTIMIZED | CONTROL | 2024-06 | AVAILABLE | 11 | 0 | 0.8721 | -0.5830 |
| OPTIMIZED | CONTROL | 2024-07 | AVAILABLE | 10 | 0 | 2.2218 | 5.5067 |
| OPTIMIZED | CONTROL | 2024-08 | AVAILABLE | 12 | 1 | 0.5630 | -2.7524 |
| OPTIMIZED | CONTROL | 2024-09 | AVAILABLE | 10 | 0 | 1.5487 | 2.5377 |
| OPTIMIZED | CONTROL | 2024-10 | AVAILABLE | 9 | 0 | 0.7172 | -1.2517 |
| OPTIMIZED | CONTROL | 2024-11 | AVAILABLE | 11 | 0 | 3.0106 | 10.0324 |
| OPTIMIZED | CONTROL | 2024-12 | AVAILABLE | 8 | 1 | 2.1354 | 3.9261 |
| OPTIMIZED | T1 | 2023-01 | NO_COVERAGE | 0 | 0 | — | 0.0000 |
| OPTIMIZED | T1 | 2023-02 | NO_COVERAGE | 0 | 0 | — | 0.0000 |
| OPTIMIZED | T1 | 2023-03 | NO_COVERAGE | 0 | 0 | — | 0.0000 |
| OPTIMIZED | T1 | 2023-04 | NO_COVERAGE | 0 | 0 | — | 0.0000 |
| OPTIMIZED | T1 | 2023-05 | NO_COVERAGE | 0 | 0 | — | 0.0000 |
| OPTIMIZED | T1 | 2023-06 | NO_COVERAGE | 0 | 0 | — | 0.0000 |
| OPTIMIZED | T1 | 2023-07 | NO_COVERAGE | 0 | 0 | — | 0.0000 |
| OPTIMIZED | T1 | 2023-08 | NO_COVERAGE | 0 | 0 | — | 0.0000 |
| OPTIMIZED | T1 | 2023-09 | NO_COVERAGE | 0 | 0 | — | 0.0000 |
| OPTIMIZED | T1 | 2023-10 | NO_COVERAGE | 0 | 0 | — | 0.0000 |
| OPTIMIZED | T1 | 2023-11 | AVAILABLE | 1 | 0 | 0.0000 | -1.0000 |
| OPTIMIZED | T1 | 2023-12 | AVAILABLE | 7 | 0 | 1.0834 | 0.2370 |
| OPTIMIZED | T1 | 2024-01 | AVAILABLE | 8 | 1 | 0.5706 | -2.5077 |
| OPTIMIZED | T1 | 2024-02 | AVAILABLE | 8 | 0 | 1.6057 | 1.7729 |
| OPTIMIZED | T1 | 2024-03 | AVAILABLE | 6 | 0 | 2.7468 | 5.2404 |
| OPTIMIZED | T1 | 2024-04 | AVAILABLE | 13 | 0 | 0.4642 | -3.2879 |
| OPTIMIZED | T1 | 2024-05 | AVAILABLE | 9 | 0 | 1.6891 | 2.7362 |
| OPTIMIZED | T1 | 2024-06 | AVAILABLE | 8 | 0 | 0.3614 | -2.7959 |
| OPTIMIZED | T1 | 2024-07 | AVAILABLE | 9 | 0 | 2.1492 | 4.5967 |
| OPTIMIZED | T1 | 2024-08 | AVAILABLE | 10 | 1 | 0.5928 | -2.3836 |
| OPTIMIZED | T1 | 2024-09 | AVAILABLE | 8 | 0 | 1.5455 | 2.4920 |
| OPTIMIZED | T1 | 2024-10 | AVAILABLE | 8 | 0 | 0.7849 | -0.8697 |
| OPTIMIZED | T1 | 2024-11 | AVAILABLE | 9 | 0 | 1.9437 | 3.7851 |
| OPTIMIZED | T1 | 2024-12 | AVAILABLE | 7 | 1 | 2.7942 | 4.7413 |
| OPTIMIZED | T2 | 2023-01 | NO_COVERAGE | 0 | 0 | — | 0.0000 |
| OPTIMIZED | T2 | 2023-02 | NO_COVERAGE | 0 | 0 | — | 0.0000 |
| OPTIMIZED | T2 | 2023-03 | NO_COVERAGE | 0 | 0 | — | 0.0000 |
| OPTIMIZED | T2 | 2023-04 | NO_COVERAGE | 0 | 0 | — | 0.0000 |
| OPTIMIZED | T2 | 2023-05 | NO_COVERAGE | 0 | 0 | — | 0.0000 |
| OPTIMIZED | T2 | 2023-06 | NO_COVERAGE | 0 | 0 | — | 0.0000 |
| OPTIMIZED | T2 | 2023-07 | NO_COVERAGE | 0 | 0 | — | 0.0000 |
| OPTIMIZED | T2 | 2023-08 | NO_COVERAGE | 0 | 0 | — | 0.0000 |
| OPTIMIZED | T2 | 2023-09 | NO_COVERAGE | 0 | 0 | — | 0.0000 |
| OPTIMIZED | T2 | 2023-10 | NO_COVERAGE | 0 | 0 | — | 0.0000 |
| OPTIMIZED | T2 | 2023-11 | AVAILABLE | 1 | 0 | 0.0000 | -1.0000 |
| OPTIMIZED | T2 | 2023-12 | AVAILABLE | 8 | 0 | 1.2309 | 0.6560 |
| OPTIMIZED | T2 | 2024-01 | AVAILABLE | 10 | 1 | 0.8173 | -1.2496 |
| OPTIMIZED | T2 | 2024-02 | AVAILABLE | 9 | 0 | 2.8741 | 5.4850 |
| OPTIMIZED | T2 | 2024-03 | AVAILABLE | 7 | 0 | 2.1966 | 4.4889 |
| OPTIMIZED | T2 | 2024-04 | AVAILABLE | 17 | 0 | 0.3330 | -5.7034 |
| OPTIMIZED | T2 | 2024-05 | AVAILABLE | 11 | 1 | 1.9051 | 3.3915 |
| OPTIMIZED | T2 | 2024-06 | AVAILABLE | 11 | 0 | 0.7658 | -1.2152 |
| OPTIMIZED | T2 | 2024-07 | AVAILABLE | 9 | 0 | 2.8554 | 6.5067 |
| OPTIMIZED | T2 | 2024-08 | AVAILABLE | 12 | 1 | 0.5630 | -2.7524 |
| OPTIMIZED | T2 | 2024-09 | AVAILABLE | 10 | 0 | 1.5487 | 2.5377 |
| OPTIMIZED | T2 | 2024-10 | AVAILABLE | 9 | 0 | 0.7172 | -1.2517 |
| OPTIMIZED | T2 | 2024-11 | AVAILABLE | 11 | 0 | 3.0106 | 10.0324 |
| OPTIMIZED | T2 | 2024-12 | AVAILABLE | 9 | 1 | 1.5231 | 2.3319 |

## Аудит и STOP

AUDIT_RESULTS.json — отдельная stdlib реализация парсера, рекурсивных индикаторов, допуска входов, replay и отчётных расчётов. Алгоритмическая независимость; автор тот же, внешний аудит PENDING. Два свежих полных повтора проверяют каждый сгенерированный файл побайтно; SHA артефактов проверяется отдельно.
Один Draft PR, без Merge/Auto-Merge. STOP для внешнего аудита и решения пользователя. Numerical Optimization, Robustness, Walk Forward, TRUE OOS, LIVE и новые комбинации не выполнялись.

