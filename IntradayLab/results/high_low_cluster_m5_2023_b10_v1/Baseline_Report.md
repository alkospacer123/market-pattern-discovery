# HIGH_LOW_CLUSTER_M5 — B10_v1 Baseline 2023

**INCONCLUSIVE**. Экономический диагноз известных закрытий указан отдельно. Optimization не разрешена.

Base `8db73e6338bc5b89eda385e21167e22c74e5a299`; freeze `e969f85f85c59dc03e3c88b35ea7ba5ea1f4f296`; config SHA-256 `9e0a9d0649d3530a2a100537979444b4b3ce136c1a87b8a2ff22494b0afcf101`; source `f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8`. Pre-P&L unittest: **496 PASS**.

Все результаты после модельных издержек C1. UNKNOWN не имеет выдуманного P&L. Ценовые единицы разных инструментов не суммируются. DD известных закрытий условна и не является непрерывной кривой брокерского счёта.

## Замороженные правила

| Parameter | Value |
|---|---|
| cluster_bars | 10 |
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
| version | B10_v1 |

Первое сформированное окно из N завершённых M5 обрабатывается один раз внутри причинного эпизода с общим диапазоном <=3 исторических тиков. Ширина окна 1–3, >=2 экстремума на внешней границе; нулевая ширина исключена. CLOSE_AT_BOUNDARY также расходует эпизод, сигнал не формирует. При двух допустимых направлениях оба отклонены. ID эпизода одинаков для B4/B7/B10; cluster_id включает модель. Не считать выборки независимыми. Полные сбросы и окончания: episodes.csv; причинные характеристики на момент формирования: signals.csv.

NEXT_OPEN — Open непосредственно следующей M5, совпадает по времени с завершением сигнальной. Stop: граница +/- один тик, без переноса. Риск 3–12 тиков и удаление 0–4 тика проверяются по фактическому Open. Совместно эти правила дают допустимый риск **3–5 тиков**, C1/R **0,40–0,667**. Take gross distance=3s+8t, то есть **17–23 тика** при допустимом риске; полный плановый net/net RR=3. Hold <=120 календарных минут, flat за M5 до конца окна. Stop-first, Stop-gap по Open, Take на входной свече запрещён. Общий Backtester не изменён.

Сессии 10:00–14:00, 14:05–18:50 MSK; 13–20 марта PM с 14:15. Round grid: USD 0,10 RUB и CNY 0,05 RUB из ROADMAP; GLD 10 RUB/грамм, IMOEX 10 индексных пунктов как фиксированные десятичные ориентиры. ROUND_NEAR: внешняя граница <=1 исторического тика от ближайшего узла, остальные ORDINARY_FAR; ближайший при равенстве — больший узел. Это диагностические разрезы без фильтра входа.

## Накопления и входы

| Instrument | Detected | Signals | Fills | Refused | Unknown entry | CLOSED | UNKNOWN | Fills/day |
|---|---|---|---|---|---|---|---|---|
| USDRUBF | 82 | 65 | 35 | 30 | 0 | 34 | 1 | 0.137795 |
| CNYRUBF | 1285 | 806 | 250 | 539 | 17 | 164 | 103 | 0.984252 |
| GLDRUBF | 5 | 4 | 0 | 4 | 0 | 0 | 0 | 0.000000 |
| IMOEXF | 2 | 2 | 1 | 1 | 0 | 1 | 0 | 0.029412 |

## Условная экономика известных закрытий

| Instrument | Gross R | C1 R | Net R | Net price | PF R | PF price | WR | E[R] | DD R | + / − months |
|---|---|---|---|---|---|---|---|---|---|---|
| USDRUBF | -13.800000 | 18.700000 | -32.500000 | -1.130000 | 0.220000 | 0.261438 | 0.176471 | -0.955882 | 35.333333 | 1/9 |
| CNYRUBF | 11.600000 | 93.500000 | -81.900000 | -3.038000 | 0.396092 | 0.360825 | 0.243902 | -0.499390 | 84.000000 | 1/10 |
| GLDRUBF | 0.000000 | 0.000000 | 0.000000 | 0.000000 | — | — | — | — | — | 0/0 |
| IMOEXF | -1.000000 | 0.666667 | -1.666667 | -2.500000 | 0.000000 | 0.000000 | 0.000000 | -1.666667 | 1.666667 | 0/1 |

| Instrument | Avg win R | Avg loss R | Stop mean ticks | C1/risk mean | Trade days | Largest winner share | Largest + month share |
|---|---|---|---|---|---|---|---|
| USDRUBF | 1.527778 | -1.488095 | 3.828571 | 0.545714 | 30 | 0.490909 | 1.000000 |
| CNYRUBF | 1.342917 | -1.189620 | 3.580000 | 0.579600 | 92 | 0.093081 | 1.000000 |
| GLDRUBF | — | — | — | — | 0 | — | — |
| IMOEXF | — | -1.666667 | 3.000000 | 0.666667 | 1 | — | — |

### USDRUBF: INCONCLUSIVE; известные закрытия: NO ECONOMIC BASELINE PASS

Причины всех отказов: `{"AMBIGUOUS_BOTH_SIDES": 6, "CLOSE_AT_BOUNDARY": 11, "ENTRY_MORE_THAN_4_TICKS_FROM_CLUSTER": 13, "OPEN_WRONG_SIDE_OF_CLUSTER": 2, "POSITION_BUSY": 3, "SESSION_LIMIT": 3, "STOP_BELOW_3_TICKS": 9}`.

UNKNOWN: `{"MISSING_EXPOSED_BAR": 1}`.

| Exit | Count | Gross R | C1 R | Net R | Mean hold lower / upper min |
|---|---|---|---|---|---|
| STOP | 26 | -26.000000 | 14.500000 | -40.500000 | 17.88461538461538461538461538 / 22.69230769230769230769230769 |
| TAKE | 1 | 5.000000 | 0.500000 | 4.500000 | 20.0 / 25.0 |
| TIME | 2 | 2.000000 | 1.066667 | 0.933333 | 120.0 / 120.0 |
| SESSION_FLAT | 5 | 5.200000 | 2.633333 | 2.566667 | 68.0 / 68.0 |

Риск мал относительно C1; для TAKE требуется пройти значительно больше первоначального Stop. STOP вносит отрицательные исходы; C1 дополнительно вычитается из всех закрытий. TIME/SESSION_FLAT показывают недостижение Take до срока; их P&L приведён отдельно. Поздний Open оценивается только по наблюдаемому смещению и отказам, без контрфактического заявления, что вход по Close был исполним или прибыльнее.

### CNYRUBF: INCONCLUSIVE; известные закрытия: NO ECONOMIC BASELINE PASS

Причины всех отказов: `{"AMBIGUOUS_BOTH_SIDES": 212, "CLOSE_AT_BOUNDARY": 267, "ENTRY_MORE_THAN_4_TICKS_FROM_CLUSTER": 12, "MISSING_EXECUTION_BAR": 17, "POSITION_BUSY": 126, "SESSION_LIMIT": 20, "STOP_BELOW_3_TICKS": 179, "UNKNOWN_POSITION_BLOCK": 202}`.

UNKNOWN: `{"MISSING_EXECUTION_BAR": 17, "MISSING_EXPOSED_BAR": 86}`.

| Exit | Count | Gross R | C1 R | Net R | Mean hold lower / upper min |
|---|---|---|---|---|---|
| STOP | 69 | -69.000000 | 39.700000 | -108.700000 | 30.0 / 34.49275362318840579710144928 |
| TAKE | 4 | 22.000000 | 2.500000 | 19.500000 | 37.5 / 42.5 |
| TIME | 41 | 36.816667 | 22.866667 | 13.950000 | 120.0 / 120.0 |
| SESSION_FLAT | 50 | 21.783333 | 28.433333 | -6.650000 | 51.4 / 51.4 |

Риск мал относительно C1; для TAKE требуется пройти значительно больше первоначального Stop. STOP вносит отрицательные исходы; C1 дополнительно вычитается из всех закрытий. TIME/SESSION_FLAT показывают недостижение Take до срока; их P&L приведён отдельно. Поздний Open оценивается только по наблюдаемому смещению и отказам, без контрфактического заявления, что вход по Close был исполним или прибыльнее.

### GLDRUBF: INCONCLUSIVE; известные закрытия: INSUFFICIENT_EVIDENCE

Причины всех отказов: `{"CLOSE_AT_BOUNDARY": 1, "ENTRY_MORE_THAN_4_TICKS_FROM_CLUSTER": 1, "STOP_ABOVE_12_TICKS": 3}`.

UNKNOWN: `{}`.

| Exit | Count | Gross R | C1 R | Net R | Mean hold lower / upper min |
|---|---|---|---|---|---|
| STOP | 0 | 0.000000 | 0.000000 | 0.000000 | None / None |
| TAKE | 0 | 0.000000 | 0.000000 | 0.000000 | None / None |
| TIME | 0 | 0.000000 | 0.000000 | 0.000000 | None / None |
| SESSION_FLAT | 0 | 0.000000 | 0.000000 | 0.000000 | None / None |

Риск мал относительно C1; для TAKE требуется пройти значительно больше первоначального Stop. STOP вносит отрицательные исходы; C1 дополнительно вычитается из всех закрытий. TIME/SESSION_FLAT показывают недостижение Take до срока; их P&L приведён отдельно. Поздний Open оценивается только по наблюдаемому смещению и отказам, без контрфактического заявления, что вход по Close был исполним или прибыльнее.

### IMOEXF: INCONCLUSIVE; известные закрытия: NO ECONOMIC BASELINE PASS

Причины всех отказов: `{"STOP_BELOW_3_TICKS": 1}`.

UNKNOWN: `{}`.

| Exit | Count | Gross R | C1 R | Net R | Mean hold lower / upper min |
|---|---|---|---|---|---|
| STOP | 1 | -1.000000 | 0.666667 | -1.666667 | 100.0 / 105.0 |
| TAKE | 0 | 0.000000 | 0.000000 | 0.000000 | None / None |
| TIME | 0 | 0.000000 | 0.000000 | 0.000000 | None / None |
| SESSION_FLAT | 0 | 0.000000 | 0.000000 | 0.000000 | None / None |

Риск мал относительно C1; для TAKE требуется пройти значительно больше первоначального Stop. STOP вносит отрицательные исходы; C1 дополнительно вычитается из всех закрытий. TIME/SESSION_FLAT показывают недостижение Take до срока; их P&L приведён отдельно. Поздний Open оценивается только по наблюдаемому смещению и отказам, без контрфактического заявления, что вход по Close был исполним или прибыльнее.

## Календарные месяцы

| Instrument | Month | CLOSED | UNKNOWN | Net R known | Coverage |
|---|---|---|---|---|---|
| USDRUBF | 2023-01 | 4 | 0 | -5.066667 | PARTIAL_DATA |
| USDRUBF | 2023-02 | 4 | 0 | -2.866667 | PARTIAL_DATA |
| USDRUBF | 2023-03 | 3 | 1 | -2.833333 | UNKNOWN |
| USDRUBF | 2023-04 | 5 | 0 | -2.433333 | PARTIAL_DATA |
| USDRUBF | 2023-05 | 0 | 0 | 0.000000 | PARTIAL_DATA |
| USDRUBF | 2023-06 | 2 | 0 | -3.166667 | PARTIAL_DATA |
| USDRUBF | 2023-07 | 1 | 0 | -1.666667 | PARTIAL_DATA |
| USDRUBF | 2023-08 | 0 | 0 | 0.000000 | PARTIAL_DATA |
| USDRUBF | 2023-09 | 3 | 0 | -4.666667 | PARTIAL_DATA |
| USDRUBF | 2023-10 | 1 | 0 | 0.600000 | CONDITIONAL_AFTER_UNKNOWN |
| USDRUBF | 2023-11 | 7 | 0 | -9.900000 | PARTIAL_DATA |
| USDRUBF | 2023-12 | 4 | 0 | -0.500000 | CONDITIONAL_AFTER_UNKNOWN |
| CNYRUBF | 2023-01 | 19 | 14 | -10.833333 | UNKNOWN |
| CNYRUBF | 2023-02 | 20 | 10 | -15.783333 | UNKNOWN |
| CNYRUBF | 2023-03 | 6 | 13 | -6.500000 | UNKNOWN |
| CNYRUBF | 2023-04 | 16 | 11 | 7.383333 | UNKNOWN |
| CNYRUBF | 2023-05 | 14 | 14 | -11.216667 | UNKNOWN |
| CNYRUBF | 2023-06 | 14 | 16 | -9.266667 | UNKNOWN |
| CNYRUBF | 2023-07 | 16 | 13 | -10.266667 | UNKNOWN |
| CNYRUBF | 2023-08 | 34 | 5 | -14.533333 | UNKNOWN |
| CNYRUBF | 2023-09 | 22 | 7 | -7.983333 | UNKNOWN |
| CNYRUBF | 2023-10 | 1 | 0 | -1.500000 | PARTIAL_DATA |
| CNYRUBF | 2023-11 | 1 | 0 | 0.000000 | PARTIAL_DATA |
| CNYRUBF | 2023-12 | 1 | 0 | -1.400000 | CONDITIONAL_AFTER_UNKNOWN |
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
| GLDRUBF | 2023-11 | 0 | 0 | 0.000000 | PARTIAL_DATA |
| GLDRUBF | 2023-12 | 0 | 0 | 0.000000 | PARTIAL_DATA |
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
| IMOEXF | 2023-12 | 1 | 0 | -1.666667 | PARTIAL_DATA |

До появления инструмента NO_COVERAGE — не нулевая доходность. Все 12 календарных месяцев присутствуют; нулевые торговые месяцы с историей отражены отдельно от отсутствующей истории.

## Круглые и обычные уровни

| Instrument | Level | Detected | Fills | CLOSED | UNKNOWN | Net R | PF R | PF price |
|---|---|---|---|---|---|---|---|---|
| USDRUBF | ALL | 82 | 35 | 34 | 1 | -32.500000 | 0.220000 | 0.261438 |
| USDRUBF | ROUND_NEAR | 25 | 11 | 11 | 0 | -14.966667 | 0.000000 | 0.000000 |
| USDRUBF | ORDINARY_FAR | 57 | 24 | 23 | 1 | -17.533333 | 0.343321 | 0.416667 |
| CNYRUBF | ALL | 1285 | 250 | 164 | 103 | -81.900000 | 0.396092 | 0.360825 |
| CNYRUBF | ROUND_NEAR | 748 | 143 | 91 | 62 | -50.833333 | 0.282015 | 0.300781 |
| CNYRUBF | ORDINARY_FAR | 537 | 107 | 73 | 41 | -31.066667 | 0.520699 | 0.430917 |
| GLDRUBF | ALL | 5 | 0 | 0 | 0 | 0.000000 | — | — |
| GLDRUBF | ROUND_NEAR | 1 | 0 | 0 | 0 | 0.000000 | — | — |
| GLDRUBF | ORDINARY_FAR | 4 | 0 | 0 | 0 | 0.000000 | — | — |
| IMOEXF | ALL | 2 | 1 | 1 | 0 | -1.666667 | 0.000000 | 0.000000 |
| IMOEXF | ROUND_NEAR | 1 | 1 | 1 | 0 | -1.666667 | 0.000000 | 0.000000 |
| IMOEXF | ORDINARY_FAR | 1 | 0 | 0 | 0 | 0.000000 | — | — |

## Реальные касания внешней границы

| Instrument | Touches | Detected | Fills | CLOSED | UNKNOWN | Net R | PF R |
|---|---|---|---|---|---|---|---|
| USDRUBF | 2 | 24 | 13 | 13 | 0 | -12.733333 | 0.275142 |
| USDRUBF | 3 | 24 | 10 | 10 | 0 | -5.166667 | 0.419476 |
| USDRUBF | 4 | 18 | 7 | 7 | 0 | -8.466667 | 0.066176 |
| USDRUBF | 5 | 9 | 5 | 4 | 1 | -6.133333 | 0.000000 |
| USDRUBF | 6 | 4 | 0 | 0 | 0 | 0.000000 | — |
| USDRUBF | 7 | 1 | 0 | 0 | 0 | 0.000000 | — |
| USDRUBF | 8 | 0 | 0 | 0 | 0 | 0.000000 | — |
| USDRUBF | 9 | 2 | 0 | 0 | 0 | 0.000000 | — |
| CNYRUBF | 2 | 458 | 101 | 69 | 38 | -66.700000 | 0.079788 |
| CNYRUBF | 3 | 229 | 56 | 40 | 18 | -12.500000 | 0.593275 |
| CNYRUBF | 4 | 194 | 43 | 30 | 16 | 1.400000 | 1.078505 |
| CNYRUBF | 5 | 150 | 28 | 16 | 14 | -3.766667 | 0.592058 |
| CNYRUBF | 6 | 99 | 10 | 4 | 9 | -1.333333 | 0.428571 |
| CNYRUBF | 7 | 67 | 7 | 2 | 5 | -2.666667 | 0.000000 |
| CNYRUBF | 8 | 51 | 4 | 2 | 3 | 3.333333 | 11.000000 |
| CNYRUBF | 9 | 37 | 1 | 1 | 0 | 0.333333 | — |
| GLDRUBF | 2 | 1 | 0 | 0 | 0 | 0.000000 | — |
| GLDRUBF | 3 | 0 | 0 | 0 | 0 | 0.000000 | — |
| GLDRUBF | 4 | 1 | 0 | 0 | 0 | 0.000000 | — |
| GLDRUBF | 5 | 0 | 0 | 0 | 0 | 0.000000 | — |
| GLDRUBF | 6 | 1 | 0 | 0 | 0 | 0.000000 | — |
| GLDRUBF | 7 | 0 | 0 | 0 | 0 | 0.000000 | — |
| GLDRUBF | 8 | 0 | 0 | 0 | 0 | 0.000000 | — |
| GLDRUBF | 9 | 2 | 0 | 0 | 0 | 0.000000 | — |
| IMOEXF | 2 | 2 | 1 | 1 | 0 | -1.666667 | 0.000000 |
| IMOEXF | 3 | 0 | 0 | 0 | 0 | 0.000000 | — |
| IMOEXF | 4 | 0 | 0 | 0 | 0 | 0.000000 | — |
| IMOEXF | 5 | 0 | 0 | 0 | 0 | 0.000000 | — |
| IMOEXF | 6 | 0 | 0 | 0 | 0 | 0.000000 | — |
| IMOEXF | 7 | 0 | 0 | 0 | 0 | 0.000000 | — |
| IMOEXF | 8 | 0 | 0 | 0 | 0 | 0.000000 | — |
| IMOEXF | 9 | 0 | 0 | 0 | 0 | 0.000000 | — |

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
