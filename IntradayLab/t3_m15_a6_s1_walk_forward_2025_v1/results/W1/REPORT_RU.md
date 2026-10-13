# TRAIL_375 — Walk Forward 2025

Блок **W1**. GROSS_ONLY / COSTS_DEFERRED / NOT_LIVE_READY

Только условная сумма первоначальных R; без общего sizing/capital и реальных издержек. Gross PF и R не являются доходностью капитала.

Полный причинный replay от исходного начала 2023 года. Кандидат, четыре инструмента, LONG/SHORT, H1 ordinal aggregation, NEXT_OPEN, Stop-first, gaps, A6/S1, trailing 3,75 ATR неизменны. На квартальных границах FLAT-reset отсутствует. Каждый блок запечатан до чтения следующего.

CONTROL полностью сверяется с #510, включая журналы, индикаторы и опубликованные таблицы; две реализации и фиксированные арифметические сценарии проверяются отдельно.

## Календарные CLOSED: год, кварталы, месяцы

<!-- dataset view_calendar -->
| period | closed | period_end_OPEN | gross_PF | gross_R | expectancy_R | win_fraction | mean_WIN_R | mean_LOSS_R | positive_months | negative_months | zero_months | worst_month_R | closed_R_drawdown | max_losing_trade_run |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| FULL_WF | 71 | 1 | 1.162494 | 6.064142 | 0.085410 | 0.323944 | 1.886231 | -0.777483 | 1 | 2 | 0 | -4.824484 | 12.493541 | 10 |
| W1 | 71 | 1 | 1.162494 | 6.064142 | 0.085410 | 0.323944 | 1.886231 | -0.777483 | 1 | 2 | 0 | -4.824484 | 12.493541 | 10 |
| 2025-01 | 26 | 0 | 0.704678 | -4.824484 | -0.185557 | 0.307692 | 1.438981 | -0.907574 | 0 | 1 | 0 | -4.824484 | 10.091263 | 10 |
| 2025-02 | 27 | 0 | 2.072858 | 14.123854 | 0.523106 | 0.370370 | 2.728856 | -0.774394 | 1 | 0 | 0 | 14.123854 | 7.049000 | 8 |
| 2025-03 | 18 | 1 | 0.586189 | -3.235228 | -0.179735 | 0.277778 | 0.916579 | -0.601394 | 0 | 1 | 0 | -3.235228 | 6.555221 | 9 |


## Новые и унаследованные сделки

Календарный CLOSED учитывается один раз по каноническому exit Close. NEW_WF_COHORT: signal и фактический entry оба в 2025; на квартальных таблицах эта годовая cohort распределена по выходу. INHERITED_DEVELOPMENT раскрывается отдельно. OPEN не входит в CLOSED PF/R.
<!-- dataset view_cohorts -->
| cohort | closed | period_end_OPEN | gross_PF | gross_R | expectancy_R | win_fraction | mean_WIN_R | mean_LOSS_R | positive_months | negative_months | zero_months | worst_month_R | closed_R_drawdown | max_losing_trade_run |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CALENDAR_CLOSED | 71 | 1 | 1.162494 | 6.064142 | 0.085410 | 0.323944 | 1.886231 | -0.777483 | 1 | 2 | 0 | -4.824484 | 12.493541 | 10 |
| NEW_WF_COHORT | 70 | 1 | 1.089781 | 3.350554 | 0.047865 | 0.314286 | 1.848623 | -0.777483 | 1 | 2 | 0 | -7.538072 | 12.493541 | 10 |
| INHERITED_DEVELOPMENT | 1 | 0 | N/A | 2.713588 | 2.713588 | 1.000000 | 2.713588 | N/A | 1 | 0 | 2 | 0 | 0.000000 | 0 |


## Инструменты

<!-- dataset view_instruments -->
| scope | closed | period_end_OPEN | gross_PF | gross_R | expectancy_R | win_fraction | mean_WIN_R | mean_LOSS_R | positive_months | negative_months | zero_months | worst_month_R | closed_R_drawdown | max_losing_trade_run | share_portfolio_R |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| USDRUBF | 18 | 0 | 1.377739 | 3.439927 | 0.191107 | 0.333333 | 2.091092 | -0.758885 | 2 | 1 | 0 | -2.068785 | 4.068785 | 6 | 0.567257 |
| CNYRUBF | 18 | 0 | 1.839948 | 7.537482 | 0.418749 | 0.444444 | 2.063903 | -0.897374 | 1 | 2 | 0 | -0.948855 | 2.477254 | 3 | 1.242959 |
| GLDRUBF | 16 | 1 | 0.142314 | -9.280100 | -0.580006 | 0.062500 | 1.539824 | -0.721328 | 0 | 3 | 0 | -4.732223 | 9.280100 | 8 | -1.530324 |
| IMOEXF | 19 | 0 | 1.518696 | 4.366834 | 0.229833 | 0.421053 | 1.598213 | -0.765352 | 2 | 1 | 0 | -0.532381 | 5.289792 | 4 | 0.720107 |


## LONG / SHORT

<!-- dataset view_directions -->
| direction | closed | period_end_OPEN | gross_PF | gross_R | expectancy_R | win_fraction | mean_WIN_R | mean_LOSS_R | positive_months | negative_months | zero_months | worst_month_R | closed_R_drawdown | max_losing_trade_run | share_portfolio_R |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| LONG | 17 | 1 | 1.224142 | 1.969897 | 0.115876 | 0.294118 | 2.151702 | -0.732385 | 2 | 1 | 0 | -3.651039 | 8.408451 | 6 | 0.324844 |
| SHORT | 54 | 0 | 1.143504 | 4.094245 | 0.075819 | 0.333333 | 1.812488 | -0.792515 | 1 | 2 | 0 | -3.744024 | 12.493541 | 9 | 0.675156 |


## Фиксированные диагностические сценарии

−0,05R и −0,10R на каждый CLOSED — абстрактные потери R, без изменения траекторий, не комиссия FINAM/C1. Leave-one-out и исключения победителей/месяцев — диагностика; первичные результаты сохраняют все сделки.
<!-- dataset view_stress -->
| cohort | scenario | closed | gross_PF | gross_R | expectancy_R | closed_R_drawdown | positive_months | negative_months | zero_months |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CALENDAR_CLOSED | LEAVE_OUT_USDRUBF | 53 | 1.093016 | 2.624215 | 0.049513 | 12.496254 | 1 | 2 | 0 |
| CALENDAR_CLOSED | LEAVE_OUT_CNYRUBF | 53 | 0.948022 | -1.473340 | -0.027799 | 10.655495 | 1 | 2 | 0 |
| CALENDAR_CLOSED | LEAVE_OUT_GLDRUBF | 55 | 1.579045 | 15.344242 | 0.278986 | 8.471791 | 1 | 2 | 0 |
| CALENDAR_CLOSED | LEAVE_OUT_IMOEXF | 52 | 1.058730 | 1.697308 | 0.032641 | 10.580098 | 1 | 2 | 0 |
| CALENDAR_CLOSED | EX_BEST1_MONTHS | 44 | 0.666326 | -8.059712 | -0.183175 | 12.982612 | 0 | 2 | 1 |
| CALENDAR_CLOSED | EX_BEST3_MONTHS | 0 | N/A | 0.000000 | N/A | 0.000000 | 0 | 0 | 3 |
| CALENDAR_CLOSED | EX_TOP1_WINNERS | 70 | 1.029121 | 1.086764 | 0.015525 | 12.493541 | 1 | 2 | 0 |
| CALENDAR_CLOSED | EX_TOP3_WINNERS | 68 | 0.784418 | -8.045338 | -0.118314 | 16.693362 | 1 | 2 | 0 |
| CALENDAR_CLOSED | EX_TOP5_WINNERS | 66 | 0.581891 | -15.603469 | -0.236416 | 20.526369 | 0 | 3 | 0 |
| CALENDAR_CLOSED | EX_TOP10_WINNERS | 61 | 0.242761 | -28.259508 | -0.463271 | 30.468821 | 0 | 3 | 0 |
| CALENDAR_CLOSED | R_STRESS_0.05 | 71 | 1.063298 | 2.514142 | 0.035410 | 13.729735 | 1 | 2 | 0 |
| CALENDAR_CLOSED | R_STRESS_0.1 | 71 | 0.975406 | -1.035858 | -0.014590 | 15.329735 | 1 | 2 | 0 |
| NEW_WF_COHORT | LEAVE_OUT_USDRUBF | 52 | 0.996832 | -0.089373 | -0.001719 | 12.496254 | 1 | 2 | 0 |
| NEW_WF_COHORT | LEAVE_OUT_CNYRUBF | 52 | 0.852289 | -4.186928 | -0.080518 | 10.655495 | 1 | 2 | 0 |
| NEW_WF_COHORT | LEAVE_OUT_GLDRUBF | 54 | 1.476642 | 12.630654 | 0.233901 | 8.471791 | 1 | 2 | 0 |
| NEW_WF_COHORT | LEAVE_OUT_IMOEXF | 52 | 1.058730 | 1.697308 | 0.032641 | 10.580098 | 1 | 2 | 0 |
| NEW_WF_COHORT | EX_BEST1_MONTHS | 43 | 0.553983 | -10.773300 | -0.250542 | 12.982612 | 0 | 2 | 1 |
| NEW_WF_COHORT | EX_BEST3_MONTHS | 0 | N/A | 0.000000 | N/A | 0.000000 | 0 | 0 | 3 |
| NEW_WF_COHORT | EX_TOP1_WINNERS | 69 | 0.956408 | -1.626824 | -0.023577 | 12.493541 | 1 | 2 | 0 |
| NEW_WF_COHORT | EX_TOP3_WINNERS | 67 | 0.711705 | -10.758926 | -0.160581 | 16.693362 | 1 | 2 | 0 |
| NEW_WF_COHORT | EX_TOP5_WINNERS | 65 | 0.509178 | -18.317057 | -0.281801 | 20.526369 | 0 | 3 | 0 |
| NEW_WF_COHORT | EX_TOP10_WINNERS | 60 | 0.188981 | -30.266543 | -0.504442 | 32.475856 | 0 | 3 | 0 |
| NEW_WF_COHORT | R_STRESS_0.05 | 70 | 0.996237 | -0.149446 | -0.002135 | 13.729735 | 1 | 2 | 0 |
| NEW_WF_COHORT | R_STRESS_0.1 | 70 | 0.913354 | -3.649446 | -0.052135 | 15.329735 | 1 | 2 | 0 |


## Marked-R отдельно от CLOSED

Marked-R = CLOSED R + U_end − U_start. Снимок — последний разрешённый завершённый Close перед границей; время и цена отметки в open_monthly/ CHECKPOINT, без оценок 2026.
<!-- dataset view_marked -->
| month | CLOSED_R | U_start_R | U_end_R | marked_R | OPEN_start | OPEN_end | carried_in_IDs | carried_out_IDs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2025-01 | -4.824484 | 3.532186 | 0 | -8.356670 | 1 | 0 | T3-M15-IMOEXF-000090 |  |
| 2025-02 | 14.123854 | 0 | 0 | 14.123854 | 0 | 0 |  |  |
| 2025-03 | -3.235228 | 0 | 0.128152 | -3.107076 | 0 | 1 |  | T3-M15-GLDRUBF-000129 |


## Аудит и ограничения

Внешнее человеческое ревью PENDING. Независимость вычислительная: два канонических алгоритма, один автор. Покрытие проверяется только в разрешённом prefix: все 48 instrument-month, фактические наблюдаемые бары/дни/gaps; независимого биржевого календаря и доказательства отсутствия всех vendor-пропусков нет. Будущая часть не исследуется. Нет оптимизации, TRUE OOS, LIVE, брокерских действий, допуска к реальной торговле.

Полные показатели, top-1/3/5/10 ID, recovery episodes, серии убытков, состояния OPEN, coverage и сценарии: DETAILS.md, CSV и TABLES.json. Полные журналы: primary/ и scalar/.
