# HIGH_LOW_CLUSTER_M5 — B4_v1 Baseline 2023

**INCONCLUSIVE**. Экономический диагноз известных закрытий указан отдельно. Optimization не разрешена.

Base `8db73e6338bc5b89eda385e21167e22c74e5a299`; freeze `e969f85f85c59dc03e3c88b35ea7ba5ea1f4f296`; config SHA-256 `fb194b0e0734ac2dc84cf64a5aa33ec4aad3fd00c796108d56ffc5196459fa5f`; source `f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8`. Pre-P&L unittest: **496 PASS**.

Все результаты после модельных издержек C1. UNKNOWN не имеет выдуманного P&L. Ценовые единицы разных инструментов не суммируются. DD известных закрытий условна и не является непрерывной кривой брокерского счёта.

## Замороженные правила

| Parameter | Value |
|---|---|
| cluster_bars | 4 |
| max_hold_calendar_minutes | 120 |
| maximum_rebound_ticks | 4 |
| maximum_risk_ticks | 12 |
| maximum_width_ticks | 3 |
| minimum_boundary_touches | 2 |
| minimum_risk_ticks | 3 |
| minimum_width_ticks | 1 |
| signal_tf | M5 |
| stop_buffer_ticks | 1 |
| target_mode | FULL_NET_C1_R |
| target_net_R | 3 |
| version | B4_v1 |

Первое сформированное окно из N завершённых M5 обрабатывается один раз внутри причинного эпизода с общим диапазоном <=3 исторических тиков. Ширина окна 1–3, >=2 экстремума на внешней границе; нулевая ширина исключена. CLOSE_AT_BOUNDARY также расходует эпизод, сигнал не формирует. При двух допустимых направлениях оба отклонены. ID эпизода одинаков для B4/B7/B10; cluster_id включает модель. Не считать выборки независимыми. Полные сбросы и окончания: episodes.csv; причинные характеристики на момент формирования: signals.csv.

NEXT_OPEN — Open непосредственно следующей M5, совпадает по времени с завершением сигнальной. Stop: граница +/- один тик, без переноса. Риск 3–12 тиков и удаление 0–4 тика проверяются по фактическому Open. Совместно эти правила дают допустимый риск **3–5 тиков**, C1/R **0,40–0,667**. Take gross distance=3s+8t, то есть **17–23 тика** при допустимом риске; полный плановый net/net RR=3. Hold <=120 календарных минут, flat за M5 до конца окна. Stop-first, Stop-gap по Open, Take на входной свече запрещён. Общий Backtester не изменён.

Сессии 10:00–14:00, 14:05–18:50 MSK; 13–20 марта PM с 14:15. Round grid: USD 0,10 RUB и CNY 0,05 RUB из ROADMAP; GLD 10 RUB/грамм, IMOEX 10 индексных пунктов как фиксированные десятичные ориентиры. ROUND_NEAR: внешняя граница <=1 исторического тика от ближайшего узла, остальные ORDINARY_FAR; ближайший при равенстве — больший узел. Это диагностические разрезы без фильтра входа.

## Накопления и входы

| Instrument | Detected | Signals | Fills | Refused | Unknown entry | CLOSED | UNKNOWN | Fills/day |
|---|---|---|---|---|---|---|---|---|
| USDRUBF | 1819 | 1467 | 556 | 909 | 2 | 549 | 9 | 2.188976 |
| CNYRUBF | 2985 | 1967 | 425 | 1522 | 20 | 319 | 126 | 1.673228 |
| GLDRUBF | 125 | 88 | 13 | 70 | 5 | 12 | 6 | 0.104839 |
| IMOEXF | 175 | 115 | 14 | 90 | 11 | 9 | 16 | 0.411765 |

## Условная экономика известных закрытий

| Instrument | Gross R | C1 R | Net R | Net price | PF R | PF price | WR | E[R] | DD R | + / − months |
|---|---|---|---|---|---|---|---|---|---|---|
| USDRUBF | 7.083333 | 288.666667 | -281.583333 | -10.910000 | 0.557641 | 0.559014 | 0.200364 | -0.512902 | 297.116667 | 1/11 |
| CNYRUBF | 2.700000 | 184.000000 | -181.300000 | -4.701000 | 0.419840 | 0.355498 | 0.206897 | -0.568339 | 184.800000 | 1/11 |
| GLDRUBF | 4.466667 | 5.866667 | -1.400000 | -1.700000 | 0.909091 | 0.750000 | 0.250000 | -0.116667 | 8.900000 | 2/3 |
| IMOEXF | -2.083333 | 5.066667 | -7.150000 | -15.000000 | 0.411523 | 0.333333 | 0.111111 | -0.794444 | 10.750000 | 0/1 |

| Instrument | Avg win R | Avg loss R | Stop mean ticks | C1/risk mean | Trade days | Largest winner share | Largest + month share |
|---|---|---|---|---|---|---|---|
| USDRUBF | 3.226970 | -1.466705 | 3.956835 | 0.526019 | 217 | 0.014086 | 1.000000 |
| CNYRUBF | 1.987879 | -1.313025 | 3.505882 | 0.589412 | 162 | 0.038110 | 1.000000 |
| GLDRUBF | 4.666667 | -1.711111 | 4.153846 | 0.489744 | 9 | 0.357143 | 0.548780 |
| IMOEXF | 5.000000 | -1.518750 | 3.714286 | 0.557143 | 8 | 1.000000 | — |

### USDRUBF: INCONCLUSIVE; известные закрытия: NO ECONOMIC BASELINE PASS

Причины всех отказов: `{"AMBIGUOUS_BOTH_SIDES": 100, "CLOSE_AT_BOUNDARY": 252, "ENTRY_MORE_THAN_4_TICKS_FROM_CLUSTER": 387, "MISSING_EXECUTION_BAR": 2, "OPEN_WRONG_SIDE_OF_CLUSTER": 10, "POSITION_BUSY": 183, "SESSION_LIMIT": 62, "STOP_ABOVE_12_TICKS": 47, "STOP_BELOW_3_TICKS": 179, "UNKNOWN_POSITION_BLOCK": 41}`.

UNKNOWN: `{"MISSING_EXECUTION_BAR": 2, "MISSING_EXPOSED_BAR": 7}`.

| Exit | Count | Gross R | C1 R | Net R | Mean hold lower / upper min |
|---|---|---|---|---|---|
| STOP | 408 | -408.000000 | 215.800000 | -623.800000 | 12.51225490196078431372549020 / 17.32843137254901960784313725 |
| TAKE | 65 | 332.733333 | 34.433333 | 298.300000 | 39.76923076923076923076923077 / 44.76923076923076923076923077 |
| TIME | 8 | 10.950000 | 4.233333 | 6.716667 | 120.0 / 120.0 |
| SESSION_FLAT | 68 | 71.400000 | 34.200000 | 37.200000 | 33.08823529411764705882352941 / 33.08823529411764705882352941 |

Риск мал относительно C1; для TAKE требуется пройти значительно больше первоначального Stop. STOP вносит отрицательные исходы; C1 дополнительно вычитается из всех закрытий. TIME/SESSION_FLAT показывают недостижение Take до срока; их P&L приведён отдельно. Поздний Open оценивается только по наблюдаемому смещению и отказам, без контрфактического заявления, что вход по Close был исполним или прибыльнее.

### CNYRUBF: INCONCLUSIVE; известные закрытия: NO ECONOMIC BASELINE PASS

Причины всех отказов: `{"AMBIGUOUS_BOTH_SIDES": 240, "CLOSE_AT_BOUNDARY": 778, "ENTRY_MORE_THAN_4_TICKS_FROM_CLUSTER": 108, "MISSING_EXECUTION_BAR": 20, "OPEN_WRONG_SIDE_OF_CLUSTER": 4, "POSITION_BUSY": 317, "SESSION_LIMIT": 35, "STOP_ABOVE_12_TICKS": 14, "STOP_BELOW_3_TICKS": 397, "UNKNOWN_POSITION_BLOCK": 647}`.

UNKNOWN: `{"MISSING_EXECUTION_BAR": 20, "MISSING_EXPOSED_BAR": 106}`.

| Exit | Count | Gross R | C1 R | Net R | Mean hold lower / upper min |
|---|---|---|---|---|---|
| STOP | 171 | -172.000000 | 99.400000 | -271.400000 | 28.07017543859649122807017544 / 32.74853801169590643274853801 |
| TAKE | 13 | 69.533333 | 7.633333 | 61.900000 | 33.84615384615384615384615385 / 38.84615384615384615384615385 |
| TIME | 70 | 75.233333 | 40.766667 | 34.466667 | 120.0 / 120.0 |
| SESSION_FLAT | 65 | 29.933333 | 36.200000 | -6.266667 | 39.53846153846153846153846154 / 39.53846153846153846153846154 |

Риск мал относительно C1; для TAKE требуется пройти значительно больше первоначального Stop. STOP вносит отрицательные исходы; C1 дополнительно вычитается из всех закрытий. TIME/SESSION_FLAT показывают недостижение Take до срока; их P&L приведён отдельно. Поздний Open оценивается только по наблюдаемому смещению и отказам, без контрфактического заявления, что вход по Close был исполним или прибыльнее.

### GLDRUBF: INCONCLUSIVE; известные закрытия: NO ECONOMIC BASELINE PASS

Причины всех отказов: `{"CLOSE_AT_BOUNDARY": 37, "ENTRY_MORE_THAN_4_TICKS_FROM_CLUSTER": 12, "MISSING_EXECUTION_BAR": 5, "OPEN_WRONG_SIDE_OF_CLUSTER": 5, "SESSION_LIMIT": 2, "STOP_ABOVE_12_TICKS": 33, "STOP_BELOW_3_TICKS": 16, "UNKNOWN_POSITION_BLOCK": 2}`.

UNKNOWN: `{"MISSING_EXECUTION_BAR": 5, "MISSING_EXPOSED_BAR": 1}`.

| Exit | Count | Gross R | C1 R | Net R | Mean hold lower / upper min |
|---|---|---|---|---|---|
| STOP | 9 | -11.200000 | 4.200000 | -15.400000 | 6.111111111111111111111111111 / 10.55555555555555555555555556 |
| TAKE | 3 | 15.666667 | 1.666667 | 14.000000 | 8.333333333333333333333333333 / 13.33333333333333333333333333 |
| TIME | 0 | 0.000000 | 0.000000 | 0.000000 | None / None |
| SESSION_FLAT | 0 | 0.000000 | 0.000000 | 0.000000 | None / None |

Риск мал относительно C1; для TAKE требуется пройти значительно больше первоначального Stop. STOP вносит отрицательные исходы; C1 дополнительно вычитается из всех закрытий. TIME/SESSION_FLAT показывают недостижение Take до срока; их P&L приведён отдельно. Поздний Open оценивается только по наблюдаемому смещению и отказам, без контрфактического заявления, что вход по Close был исполним или прибыльнее.

### IMOEXF: INCONCLUSIVE; известные закрытия: NO ECONOMIC BASELINE PASS

Причины всех отказов: `{"AMBIGUOUS_BOTH_SIDES": 2, "CLOSE_AT_BOUNDARY": 58, "ENTRY_MORE_THAN_4_TICKS_FROM_CLUSTER": 18, "MISSING_EXECUTION_BAR": 11, "OPEN_WRONG_SIDE_OF_CLUSTER": 6, "POSITION_BUSY": 3, "SESSION_LIMIT": 2, "STOP_ABOVE_12_TICKS": 3, "STOP_BELOW_3_TICKS": 16, "UNKNOWN_POSITION_BLOCK": 42}`.

UNKNOWN: `{"MISSING_EXECUTION_BAR": 11, "MISSING_EXPOSED_BAR": 5}`.

| Exit | Count | Gross R | C1 R | Net R | Mean hold lower / upper min |
|---|---|---|---|---|---|
| STOP | 7 | -7.000000 | 3.900000 | -10.900000 | 17.14285714285714285714285714 / 21.42857142857142857142857143 |
| TAKE | 1 | 5.666667 | 0.666667 | 5.000000 | 15.0 / 20.0 |
| TIME | 0 | 0.000000 | 0.000000 | 0.000000 | None / None |
| SESSION_FLAT | 1 | -0.750000 | 0.500000 | -1.250000 | 10.0 / 10.0 |

Риск мал относительно C1; для TAKE требуется пройти значительно больше первоначального Stop. STOP вносит отрицательные исходы; C1 дополнительно вычитается из всех закрытий. TIME/SESSION_FLAT показывают недостижение Take до срока; их P&L приведён отдельно. Поздний Open оценивается только по наблюдаемому смещению и отказам, без контрфактического заявления, что вход по Close был исполним или прибыльнее.

## Календарные месяцы

| Instrument | Month | CLOSED | UNKNOWN | Net R known | Coverage |
|---|---|---|---|---|---|
| USDRUBF | 2023-01 | 46 | 2 | -29.200000 | UNKNOWN |
| USDRUBF | 2023-02 | 44 | 1 | -28.550000 | UNKNOWN |
| USDRUBF | 2023-03 | 62 | 3 | -42.500000 | UNKNOWN |
| USDRUBF | 2023-04 | 52 | 1 | -26.133333 | UNKNOWN |
| USDRUBF | 2023-05 | 37 | 1 | 10.783333 | UNKNOWN |
| USDRUBF | 2023-06 | 43 | 1 | -29.700000 | UNKNOWN |
| USDRUBF | 2023-07 | 39 | 0 | -36.950000 | PARTIAL_DATA |
| USDRUBF | 2023-08 | 25 | 0 | -13.500000 | PARTIAL_DATA |
| USDRUBF | 2023-09 | 43 | 0 | -21.416667 | PARTIAL_DATA |
| USDRUBF | 2023-10 | 41 | 0 | -28.250000 | CONDITIONAL_AFTER_UNKNOWN |
| USDRUBF | 2023-11 | 65 | 0 | -26.366667 | PARTIAL_DATA |
| USDRUBF | 2023-12 | 52 | 0 | -9.800000 | CONDITIONAL_AFTER_UNKNOWN |
| CNYRUBF | 2023-01 | 27 | 13 | -24.783333 | UNKNOWN |
| CNYRUBF | 2023-02 | 19 | 16 | -11.750000 | UNKNOWN |
| CNYRUBF | 2023-03 | 16 | 15 | -18.433333 | UNKNOWN |
| CNYRUBF | 2023-04 | 23 | 14 | 0.416667 | UNKNOWN |
| CNYRUBF | 2023-05 | 23 | 15 | -7.350000 | UNKNOWN |
| CNYRUBF | 2023-06 | 20 | 18 | -20.333333 | UNKNOWN |
| CNYRUBF | 2023-07 | 27 | 15 | -9.583333 | UNKNOWN |
| CNYRUBF | 2023-08 | 49 | 9 | -20.700000 | UNKNOWN |
| CNYRUBF | 2023-09 | 29 | 8 | -17.766667 | UNKNOWN |
| CNYRUBF | 2023-10 | 22 | 1 | -4.333333 | UNKNOWN |
| CNYRUBF | 2023-11 | 39 | 2 | -28.716667 | UNKNOWN |
| CNYRUBF | 2023-12 | 25 | 0 | -17.966667 | CONDITIONAL_AFTER_UNKNOWN |
| GLDRUBF | 2023-01 | 0 | 0 | — | NO_COVERAGE |
| GLDRUBF | 2023-02 | 0 | 0 | — | NO_COVERAGE |
| GLDRUBF | 2023-03 | 0 | 0 | — | NO_COVERAGE |
| GLDRUBF | 2023-04 | 0 | 0 | — | NO_COVERAGE |
| GLDRUBF | 2023-05 | 0 | 0 | — | NO_COVERAGE |
| GLDRUBF | 2023-06 | 0 | 0 | — | NO_COVERAGE |
| GLDRUBF | 2023-07 | 0 | 1 | 0.000000 | UNKNOWN |
| GLDRUBF | 2023-08 | 1 | 1 | -1.500000 | UNKNOWN |
| GLDRUBF | 2023-09 | 1 | 0 | 4.500000 | PARTIAL_DATA |
| GLDRUBF | 2023-10 | 6 | 1 | 3.700000 | UNKNOWN |
| GLDRUBF | 2023-11 | 3 | 1 | -4.500000 | UNKNOWN |
| GLDRUBF | 2023-12 | 1 | 2 | -3.600000 | UNKNOWN |
| IMOEXF | 2023-01 | 0 | 0 | — | NO_COVERAGE |
| IMOEXF | 2023-02 | 0 | 0 | — | NO_COVERAGE |
| IMOEXF | 2023-03 | 0 | 0 | — | NO_COVERAGE |
| IMOEXF | 2023-04 | 0 | 0 | — | NO_COVERAGE |
| IMOEXF | 2023-05 | 0 | 0 | — | NO_COVERAGE |
| IMOEXF | 2023-06 | 0 | 0 | — | NO_COVERAGE |
| IMOEXF | 2023-07 | 0 | 0 | — | NO_COVERAGE |
| IMOEXF | 2023-08 | 0 | 0 | — | NO_COVERAGE |
| IMOEXF | 2023-09 | 0 | 0 | — | NO_COVERAGE |
| IMOEXF | 2023-10 | 0 | 0 | — | NO_COVERAGE |
| IMOEXF | 2023-11 | 0 | 5 | 0.000000 | UNKNOWN |
| IMOEXF | 2023-12 | 9 | 11 | -7.150000 | UNKNOWN |

До появления инструмента NO_COVERAGE — не нулевая доходность. Все 12 календарных месяцев присутствуют; нулевые торговые месяцы с историей отражены отдельно от отсутствующей истории.

## Круглые и обычные уровни

| Instrument | Level | Detected | Fills | CLOSED | UNKNOWN | Net R | PF R | PF price |
|---|---|---|---|---|---|---|---|---|
| USDRUBF | ALL | 1819 | 556 | 549 | 9 | -281.583333 | 0.557641 | 0.559014 |
| USDRUBF | ROUND_NEAR | 590 | 200 | 195 | 6 | -131.033333 | 0.436092 | 0.429530 |
| USDRUBF | ORDINARY_FAR | 1229 | 356 | 354 | 3 | -150.550000 | 0.627521 | 0.632278 |
| CNYRUBF | ALL | 2985 | 425 | 319 | 126 | -181.300000 | 0.419840 | 0.355498 |
| CNYRUBF | ROUND_NEAR | 1588 | 212 | 142 | 82 | -87.383333 | 0.302050 | 0.325058 |
| CNYRUBF | ORDINARY_FAR | 1397 | 213 | 177 | 44 | -93.916667 | 0.498576 | 0.390611 |
| GLDRUBF | ALL | 125 | 13 | 12 | 6 | -1.400000 | 0.909091 | 0.750000 |
| GLDRUBF | ROUND_NEAR | 16 | 4 | 3 | 2 | 1.600000 | 1.551724 | 1.384615 |
| GLDRUBF | ORDINARY_FAR | 109 | 9 | 9 | 4 | -3.000000 | 0.760000 | 0.600000 |
| IMOEXF | ALL | 175 | 14 | 9 | 16 | -7.150000 | 0.411523 | 0.333333 |
| IMOEXF | ROUND_NEAR | 35 | 5 | 4 | 4 | -6.083333 | 0.000000 | 0.000000 |
| IMOEXF | ORDINARY_FAR | 140 | 9 | 5 | 12 | -1.066667 | 0.824176 | 0.625000 |

## Реальные касания внешней границы

| Instrument | Touches | Detected | Fills | CLOSED | UNKNOWN | Net R | PF R |
|---|---|---|---|---|---|---|---|
| USDRUBF | 2 | 1410 | 435 | 431 | 6 | -242.333333 | 0.522794 |
| USDRUBF | 3 | 409 | 121 | 118 | 3 | -39.250000 | 0.695106 |
| CNYRUBF | 2 | 1895 | 271 | 207 | 79 | -116.400000 | 0.421183 |
| CNYRUBF | 3 | 1090 | 154 | 112 | 47 | -64.900000 | 0.417415 |
| GLDRUBF | 2 | 62 | 8 | 7 | 4 | -6.500000 | 0.409091 |
| GLDRUBF | 3 | 63 | 5 | 5 | 2 | 5.100000 | 2.159091 |
| IMOEXF | 2 | 119 | 9 | 5 | 12 | -7.483333 | 0.000000 |
| IMOEXF | 3 | 56 | 5 | 4 | 4 | 0.333333 | 1.071429 |

LONG/SHORT и средние победа/убыток в R и ценах — direction_report.csv и instrument_report.csv. Удаление Close/Open и все исходные экстремумы — signals.csv; holding нижняя/верхняя границы учитывают неизвестное внутрисвечное время выхода.

## Полнота данных

| Instrument | Rows | First | Complete / incomplete / pre-inception | Missing / invalid |
|---|---|---|---|---|
| USDRUBF | 42576 | 2023-01-03 09:00:00+03:00 | 224/30/0 | 187/0 |
| CNYRUBF | 39362 | 2023-01-03 09:00:00+03:00 | 82/172/0 | 1270/0 |
| GLDRUBF | 18428 | 2023-07-11 10:00:00+03:00 | 5/119/130 | 932/0 |
| IMOEXF | 4429 | 2023-11-14 10:00:00+03:00 | 2/32/220 | 566/0 |

Только четыре точных префикса 2023, ноль ценовых байтов 2024+. GLD с 11 июля, IMOEX с 14 ноября; CNY тик 0,01 → 0,001 с 27 сентября 19:00 MSK. UNKNOWN блокирует текущий день; последующие дни используют явное предположение FLAT. Годовые PF/Net/DD остаются null при неполных данных. Независимый алгоритмический аудит не импортирует торговую стратегию или Backtester; это не внешний человеческий signoff. Проверки: audit.json, validation.json, artifact_hashes.json.

STOP после B4/B7/B10. Нет Optimization, Robustness, WF, TRUE OOS, модели C, новых фильтров или автоматического Merge.
