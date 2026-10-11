# HIGH_LOW_CLUSTER_M5 — B7_v1 Baseline 2023

**INCONCLUSIVE**. Экономический диагноз известных закрытий указан отдельно. Optimization не разрешена.

Base `8db73e6338bc5b89eda385e21167e22c74e5a299`; freeze `e969f85f85c59dc03e3c88b35ea7ba5ea1f4f296`; config SHA-256 `2798aed0a7b045a3d71083d7c25ceda25b6b4a877c4d5554a15730fd149f5fe8`; source `f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8`. Pre-P&L unittest: **496 PASS**.

Все результаты после модельных издержек C1. UNKNOWN не имеет выдуманного P&L. Ценовые единицы разных инструментов не суммируются. DD известных закрытий условна и не является непрерывной кривой брокерского счёта.

## Замороженные правила

| Parameter | Value |
|---|---|
| cluster_bars | 7 |
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
| version | B7_v1 |

Первое сформированное окно из N завершённых M5 обрабатывается один раз внутри причинного эпизода с общим диапазоном <=3 исторических тиков. Ширина окна 1–3, >=2 экстремума на внешней границе; нулевая ширина исключена. CLOSE_AT_BOUNDARY также расходует эпизод, сигнал не формирует. При двух допустимых направлениях оба отклонены. ID эпизода одинаков для B4/B7/B10; cluster_id включает модель. Не считать выборки независимыми. Полные сбросы и окончания: episodes.csv; причинные характеристики на момент формирования: signals.csv.

NEXT_OPEN — Open непосредственно следующей M5, совпадает по времени с завершением сигнальной. Stop: граница +/- один тик, без переноса. Риск 3–12 тиков и удаление 0–4 тика проверяются по фактическому Open. Совместно эти правила дают допустимый риск **3–5 тиков**, C1/R **0,40–0,667**. Take gross distance=3s+8t, то есть **17–23 тика** при допустимом риске; полный плановый net/net RR=3. Hold <=120 календарных минут, flat за M5 до конца окна. Stop-first, Stop-gap по Open, Take на входной свече запрещён. Общий Backtester не изменён.

Сессии 10:00–14:00, 14:05–18:50 MSK; 13–20 марта PM с 14:15. Round grid: USD 0,10 RUB и CNY 0,05 RUB из ROADMAP; GLD 10 RUB/грамм, IMOEX 10 индексных пунктов как фиксированные десятичные ориентиры. ROUND_NEAR: внешняя граница <=1 исторического тика от ближайшего узла, остальные ORDINARY_FAR; ближайший при равенстве — больший узел. Это диагностические разрезы без фильтра входа.

## Накопления и входы

| Instrument | Detected | Signals | Fills | Refused | Unknown entry | CLOSED | UNKNOWN | Fills/day |
|---|---|---|---|---|---|---|---|---|
| USDRUBF | 377 | 305 | 125 | 179 | 1 | 123 | 3 | 0.492126 |
| CNYRUBF | 1979 | 1211 | 318 | 876 | 17 | 217 | 118 | 1.251969 |
| GLDRUBF | 10 | 7 | 2 | 5 | 0 | 2 | 0 | 0.016129 |
| IMOEXF | 24 | 15 | 4 | 9 | 2 | 4 | 2 | 0.117647 |

## Условная экономика известных закрытий

| Instrument | Gross R | C1 R | Net R | Net price | PF R | PF price | WR | E[R] | DD R | + / − months |
|---|---|---|---|---|---|---|---|---|---|---|
| USDRUBF | -8.900000 | 66.133333 | -75.033333 | -3.000000 | 0.486952 | 0.462366 | 0.162602 | -0.610027 | 76.866667 | 3/9 |
| CNYRUBF | 33.616667 | 125.700000 | -92.083333 | -2.950000 | 0.464839 | 0.461777 | 0.253456 | -0.424347 | 92.083333 | 1/11 |
| GLDRUBF | -2.000000 | 1.166667 | -3.166667 | -1.100000 | 0.000000 | 0.000000 | 0.000000 | -1.583333 | 3.166667 | 0/2 |
| IMOEXF | 4.250000 | 2.066667 | 2.183333 | 4.500000 | 1.711957 | 1.750000 | 0.500000 | 0.545833 | 2.316667 | 1/0 |

| Instrument | Avg win R | Avg loss R | Stop mean ticks | C1/risk mean | Trade days | Largest winner share | Largest + month share |
|---|---|---|---|---|---|---|---|
| USDRUBF | 3.560833 | -1.433824 | 3.872000 | 0.538400 | 86 | 0.070208 | 0.558824 |
| CNYRUBF | 1.454242 | -1.170522 | 3.531447 | 0.584801 | 115 | 0.062513 | 1.000000 |
| GLDRUBF | — | -1.583333 | 3.500000 | 0.583333 | 2 | — | — |
| IMOEXF | 2.625000 | -1.533333 | 4.000000 | 0.516667 | 4 | 0.857143 | 1.000000 |

### USDRUBF: INCONCLUSIVE; известные закрытия: NO ECONOMIC BASELINE PASS

Причины всех отказов: `{"AMBIGUOUS_BOTH_SIDES": 38, "CLOSE_AT_BOUNDARY": 34, "ENTRY_MORE_THAN_4_TICKS_FROM_CLUSTER": 79, "MISSING_EXECUTION_BAR": 1, "OPEN_WRONG_SIDE_OF_CLUSTER": 3, "POSITION_BUSY": 23, "SESSION_LIMIT": 14, "STOP_ABOVE_12_TICKS": 6, "STOP_BELOW_3_TICKS": 52, "UNKNOWN_POSITION_BLOCK": 2}`.

UNKNOWN: `{"MISSING_EXECUTION_BAR": 1, "MISSING_EXPOSED_BAR": 2}`.

| Exit | Count | Gross R | C1 R | Net R | Mean hold lower / upper min |
|---|---|---|---|---|---|
| STOP | 92 | -92.250000 | 49.700000 | -141.950000 | 18.85869565217391304347826087 / 23.53260869565217391304347826 |
| TAKE | 13 | 68.866667 | 7.466667 | 61.400000 | 34.61538461538461538461538462 / 39.61538461538461538461538462 |
| TIME | 3 | 2.800000 | 1.200000 | 1.600000 | 120.0 / 120.0 |
| SESSION_FLAT | 15 | 11.683333 | 7.766667 | 3.916667 | 32.66666666666666666666666667 / 32.66666666666666666666666667 |

Риск мал относительно C1; для TAKE требуется пройти значительно больше первоначального Stop. STOP вносит отрицательные исходы; C1 дополнительно вычитается из всех закрытий. TIME/SESSION_FLAT показывают недостижение Take до срока; их P&L приведён отдельно. Поздний Open оценивается только по наблюдаемому смещению и отказам, без контрфактического заявления, что вход по Close был исполним или прибыльнее.

### CNYRUBF: INCONCLUSIVE; известные закрытия: NO ECONOMIC BASELINE PASS

Причины всех отказов: `{"AMBIGUOUS_BOTH_SIDES": 264, "CLOSE_AT_BOUNDARY": 504, "ENTRY_MORE_THAN_4_TICKS_FROM_CLUSTER": 27, "MISSING_EXECUTION_BAR": 17, "POSITION_BUSY": 222, "SESSION_LIMIT": 20, "STOP_BELOW_3_TICKS": 251, "UNKNOWN_POSITION_BLOCK": 356}`.

UNKNOWN: `{"MISSING_EXECUTION_BAR": 17, "MISSING_EXPOSED_BAR": 101}`.

| Exit | Count | Gross R | C1 R | Net R | Mean hold lower / upper min |
|---|---|---|---|---|---|
| STOP | 88 | -88.000000 | 51.566667 | -139.566667 | 34.43181818181818181818181818 / 39.26136363636363636363636364 |
| TAKE | 5 | 25.666667 | 2.666667 | 23.000000 | 76.0 / 81.0 |
| TIME | 65 | 68.516667 | 35.966667 | 32.550000 | 120.0 / 120.0 |
| SESSION_FLAT | 59 | 27.433333 | 35.500000 | -8.066667 | 43.05084745762711864406779661 / 43.05084745762711864406779661 |

Риск мал относительно C1; для TAKE требуется пройти значительно больше первоначального Stop. STOP вносит отрицательные исходы; C1 дополнительно вычитается из всех закрытий. TIME/SESSION_FLAT показывают недостижение Take до срока; их P&L приведён отдельно. Поздний Open оценивается только по наблюдаемому смещению и отказам, без контрфактического заявления, что вход по Close был исполним или прибыльнее.

### GLDRUBF: INCONCLUSIVE; известные закрытия: NO ECONOMIC BASELINE PASS

Причины всех отказов: `{"CLOSE_AT_BOUNDARY": 3, "ENTRY_MORE_THAN_4_TICKS_FROM_CLUSTER": 1, "STOP_ABOVE_12_TICKS": 1, "STOP_BELOW_3_TICKS": 3}`.

UNKNOWN: `{}`.

| Exit | Count | Gross R | C1 R | Net R | Mean hold lower / upper min |
|---|---|---|---|---|---|
| STOP | 2 | -2.000000 | 1.166667 | -3.166667 | 12.5 / 17.5 |
| TAKE | 0 | 0.000000 | 0.000000 | 0.000000 | None / None |
| TIME | 0 | 0.000000 | 0.000000 | 0.000000 | None / None |
| SESSION_FLAT | 0 | 0.000000 | 0.000000 | 0.000000 | None / None |

Риск мал относительно C1; для TAKE требуется пройти значительно больше первоначального Stop. STOP вносит отрицательные исходы; C1 дополнительно вычитается из всех закрытий. TIME/SESSION_FLAT показывают недостижение Take до срока; их P&L приведён отдельно. Поздний Open оценивается только по наблюдаемому смещению и отказам, без контрфактического заявления, что вход по Close был исполним или прибыльнее.

### IMOEXF: INCONCLUSIVE; известные закрытия: INSUFFICIENT_EVIDENCE

Причины всех отказов: `{"AMBIGUOUS_BOTH_SIDES": 4, "CLOSE_AT_BOUNDARY": 5, "ENTRY_MORE_THAN_4_TICKS_FROM_CLUSTER": 1, "MISSING_EXECUTION_BAR": 2, "OPEN_WRONG_SIDE_OF_CLUSTER": 1, "SESSION_LIMIT": 3, "STOP_BELOW_3_TICKS": 4}`.

UNKNOWN: `{"MISSING_EXECUTION_BAR": 2}`.

| Exit | Count | Gross R | C1 R | Net R | Mean hold lower / upper min |
|---|---|---|---|---|---|
| STOP | 2 | -2.000000 | 1.066667 | -3.066667 | 5.0 / 10.0 |
| TAKE | 1 | 5.000000 | 0.500000 | 4.500000 | 20.0 / 25.0 |
| TIME | 0 | 0.000000 | 0.000000 | 0.000000 | None / None |
| SESSION_FLAT | 1 | 1.250000 | 0.500000 | 0.750000 | 65.0 / 65.0 |

Риск мал относительно C1; для TAKE требуется пройти значительно больше первоначального Stop. STOP вносит отрицательные исходы; C1 дополнительно вычитается из всех закрытий. TIME/SESSION_FLAT показывают недостижение Take до срока; их P&L приведён отдельно. Поздний Open оценивается только по наблюдаемому смещению и отказам, без контрфактического заявления, что вход по Close был исполним или прибыльнее.

## Календарные месяцы

| Instrument | Month | CLOSED | UNKNOWN | Net R known | Coverage |
|---|---|---|---|---|---|
| USDRUBF | 2023-01 | 9 | 1 | -5.900000 | UNKNOWN |
| USDRUBF | 2023-02 | 12 | 0 | -1.816667 | PARTIAL_DATA |
| USDRUBF | 2023-03 | 15 | 1 | -16.250000 | UNKNOWN |
| USDRUBF | 2023-04 | 12 | 0 | -10.166667 | PARTIAL_DATA |
| USDRUBF | 2023-05 | 10 | 0 | -9.333333 | PARTIAL_DATA |
| USDRUBF | 2023-06 | 4 | 1 | 6.333333 | UNKNOWN |
| USDRUBF | 2023-07 | 7 | 0 | 1.933333 | PARTIAL_DATA |
| USDRUBF | 2023-08 | 11 | 0 | 3.066667 | PARTIAL_DATA |
| USDRUBF | 2023-09 | 15 | 0 | -9.566667 | PARTIAL_DATA |
| USDRUBF | 2023-10 | 6 | 0 | -6.883333 | CONDITIONAL_AFTER_UNKNOWN |
| USDRUBF | 2023-11 | 13 | 0 | -17.150000 | PARTIAL_DATA |
| USDRUBF | 2023-12 | 9 | 0 | -9.300000 | CONDITIONAL_AFTER_UNKNOWN |
| CNYRUBF | 2023-01 | 26 | 12 | -17.983333 | UNKNOWN |
| CNYRUBF | 2023-02 | 18 | 11 | -5.650000 | UNKNOWN |
| CNYRUBF | 2023-03 | 5 | 18 | -3.750000 | UNKNOWN |
| CNYRUBF | 2023-04 | 16 | 14 | 7.333333 | UNKNOWN |
| CNYRUBF | 2023-05 | 21 | 13 | -6.983333 | UNKNOWN |
| CNYRUBF | 2023-06 | 18 | 17 | -5.750000 | UNKNOWN |
| CNYRUBF | 2023-07 | 25 | 16 | -18.500000 | UNKNOWN |
| CNYRUBF | 2023-08 | 50 | 7 | -26.383333 | UNKNOWN |
| CNYRUBF | 2023-09 | 23 | 8 | -6.166667 | UNKNOWN |
| CNYRUBF | 2023-10 | 5 | 2 | -1.033333 | UNKNOWN |
| CNYRUBF | 2023-11 | 8 | 0 | -4.150000 | PARTIAL_DATA |
| CNYRUBF | 2023-12 | 2 | 0 | -3.066667 | CONDITIONAL_AFTER_UNKNOWN |
| GLDRUBF | 2023-01 | 0 | 0 | — | NO_COVERAGE |
| GLDRUBF | 2023-02 | 0 | 0 | — | NO_COVERAGE |
| GLDRUBF | 2023-03 | 0 | 0 | — | NO_COVERAGE |
| GLDRUBF | 2023-04 | 0 | 0 | — | NO_COVERAGE |
| GLDRUBF | 2023-05 | 0 | 0 | — | NO_COVERAGE |
| GLDRUBF | 2023-06 | 0 | 0 | — | NO_COVERAGE |
| GLDRUBF | 2023-07 | 0 | 0 | 0.000000 | PARTIAL_DATA |
| GLDRUBF | 2023-08 | 0 | 0 | 0.000000 | PARTIAL_DATA |
| GLDRUBF | 2023-09 | 0 | 0 | 0.000000 | PARTIAL_DATA |
| GLDRUBF | 2023-10 | 0 | 0 | 0.000000 | PARTIAL_DATA |
| GLDRUBF | 2023-11 | 1 | 0 | -1.500000 | PARTIAL_DATA |
| GLDRUBF | 2023-12 | 1 | 0 | -1.666667 | PARTIAL_DATA |
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
| IMOEXF | 2023-11 | 0 | 0 | 0.000000 | PARTIAL_DATA |
| IMOEXF | 2023-12 | 4 | 2 | 2.183333 | UNKNOWN |

До появления инструмента NO_COVERAGE — не нулевая доходность. Все 12 календарных месяцев присутствуют; нулевые торговые месяцы с историей отражены отдельно от отсутствующей истории.

## Круглые и обычные уровни

| Instrument | Level | Detected | Fills | CLOSED | UNKNOWN | Net R | PF R | PF price |
|---|---|---|---|---|---|---|---|---|
| USDRUBF | ALL | 377 | 125 | 123 | 3 | -75.033333 | 0.486952 | 0.462366 |
| USDRUBF | ROUND_NEAR | 117 | 38 | 36 | 3 | -27.366667 | 0.395434 | 0.436047 |
| USDRUBF | ORDINARY_FAR | 260 | 87 | 87 | 0 | -47.666667 | 0.527975 | 0.474093 |
| CNYRUBF | ALL | 1979 | 318 | 217 | 118 | -92.083333 | 0.464839 | 0.461777 |
| CNYRUBF | ROUND_NEAR | 1134 | 193 | 127 | 77 | -39.216667 | 0.545138 | 0.556667 |
| CNYRUBF | ORDINARY_FAR | 845 | 125 | 90 | 41 | -52.866667 | 0.384197 | 0.347037 |
| GLDRUBF | ALL | 10 | 2 | 2 | 0 | -3.166667 | 0.000000 | 0.000000 |
| GLDRUBF | ROUND_NEAR | 1 | 1 | 1 | 0 | -1.666667 | 0.000000 | 0.000000 |
| GLDRUBF | ORDINARY_FAR | 9 | 1 | 1 | 0 | -1.500000 | 0.000000 | 0.000000 |
| IMOEXF | ALL | 24 | 4 | 4 | 2 | 2.183333 | 1.711957 | 1.750000 |
| IMOEXF | ROUND_NEAR | 6 | 1 | 1 | 2 | -1.400000 | 0.000000 | 0.000000 |
| IMOEXF | ORDINARY_FAR | 18 | 3 | 3 | 0 | 3.583333 | 3.150000 | 4.200000 |

## Реальные касания внешней границы

| Instrument | Touches | Detected | Fills | CLOSED | UNKNOWN | Net R | PF R |
|---|---|---|---|---|---|---|---|
| USDRUBF | 2 | 226 | 87 | 85 | 2 | -42.533333 | 0.572887 |
| USDRUBF | 3 | 88 | 21 | 21 | 0 | -9.666667 | 0.594406 |
| USDRUBF | 4 | 41 | 11 | 11 | 0 | -14.900000 | 0.000000 |
| USDRUBF | 5 | 19 | 5 | 5 | 1 | -6.266667 | 0.000000 |
| USDRUBF | 6 | 3 | 1 | 1 | 0 | -1.666667 | 0.000000 |
| CNYRUBF | 2 | 876 | 156 | 101 | 63 | -45.266667 | 0.451424 |
| CNYRUBF | 3 | 447 | 91 | 71 | 25 | -29.916667 | 0.472679 |
| CNYRUBF | 4 | 279 | 26 | 17 | 12 | -6.733333 | 0.500618 |
| CNYRUBF | 5 | 216 | 20 | 14 | 7 | -3.416667 | 0.438356 |
| CNYRUBF | 6 | 161 | 25 | 14 | 11 | -6.750000 | 0.490566 |
| GLDRUBF | 2 | 4 | 2 | 2 | 0 | -3.166667 | 0.000000 |
| GLDRUBF | 3 | 1 | 0 | 0 | 0 | 0.000000 | — |
| GLDRUBF | 4 | 2 | 0 | 0 | 0 | 0.000000 | — |
| GLDRUBF | 5 | 1 | 0 | 0 | 0 | 0.000000 | — |
| GLDRUBF | 6 | 2 | 0 | 0 | 0 | 0.000000 | — |
| IMOEXF | 2 | 12 | 3 | 3 | 1 | 3.583333 | 3.150000 |
| IMOEXF | 3 | 5 | 0 | 0 | 1 | 0.000000 | — |
| IMOEXF | 4 | 1 | 0 | 0 | 0 | 0.000000 | — |
| IMOEXF | 5 | 2 | 0 | 0 | 0 | 0.000000 | — |
| IMOEXF | 6 | 4 | 1 | 1 | 0 | -1.400000 | 0.000000 |

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
