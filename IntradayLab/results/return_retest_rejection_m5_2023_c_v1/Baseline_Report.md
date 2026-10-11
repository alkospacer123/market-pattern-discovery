# RETURN_RETEST_REJECTION_M5 / C_v1 / Baseline 2023

Результат после модельных издержек C1; только известные CLOSED. Неполные исходы могут смещать PF.

Base `f0e56f5df557ac4eae19af333b6d438524f5f6ff`; pre-P&L freeze `16d07c2c5dc7b3fe5ceb90760e9ce4a7ed17358f`; config SHA-256 `879801c71ce7d56972c17886ef3f33caf6c6c9d2df81fc3d49f068ec173e27df`.

Торговая логика, исполнение, runner и независимый аудит заморожены до первого исторического P&L. Общий Backtester не изменён.

## Конфигурация

| Параметр | Значение |
| --- | --- |
| approaches | 3 |
| local_extreme_lookback | 5 |
| local_extreme_strict | True |
| max_hold_calendar_minutes | 120 |
| maximum_construction_bars | 24 |
| maximum_rebound_ticks | 4 |
| maximum_risk_ticks | 12 |
| minimum_risk_ticks | 3 |
| rejection_close_ticks | 1 |
| retreat_ticks | 3 |
| signal_tf | M5 |
| stop_buffer_ticks | 1 |
| target_mode | FULL_NET_C1_R |
| target_net_R | 3 |
| tolerance_ticks | 2 |
| version | C_v1 |

Детальные правила и разрешение неоднозначностей: [preregistration](../../reports/RETURN_RETEST_C_V1_PREREGISTRATION.md). NEXT_OPEN, DATA_GAP_SKIP_V2, C1 один датированный тик на сторону; Stop-first/Stop-gap, без Take на входной свече, flat за M5 до конца окна.

## Экономика известных закрытий

| Инструмент | CLOSED | SKIP | EXCLUDED | Gross R | Cost R | Net R | PF R | PF price | WR | E[R] | DD R |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CNYRUBF | 61 | 0 | 16 | -5.799999999999999999999999993 | 32.56666666666666666666666671 | -38.36666666666666666666666671 | 0.3758134490238611713665943598 | 0.05455537370430987452264048009 | 0.09836065573770491803278688525 | -0.6289617486338797814207650280 | 47.46666666666666666666666670 |
| GLDRUBF | 2 | 0 | 0 | -3.25 | 1.166666666666666666666666667 | -4.416666666666666666666666667 | 0E+27 | 0E+1 | 0 | -2.208333333333333333333333334 | 4.416666666666666666666666667 |
| IMOEXF | 3 | 0 | 2 | 3.666666666666666666666666667 | 1.566666666666666666666666667 | 2.1 | 1.724137931034482758620689655 | 1.153846153846153846153846154 | 0.3333333333333333333333333333 | 0.7 | 2.9 |
| USDRUBF | 102 | 2 | 2 | 8.06666666666666666666666667 | 51.56666666666666666666666675 | -43.50000000000000000000000005 | 0.6256454388984509466437177275 | 0.6419491525423728813559322034 | 0.2254901960784313725490196078 | -0.4264705882352941176470588240 | 53.13333333333333333333333338 |

Суммарные результаты — research_metrics.json: только счётчики и нормализованные R; общий ценовой PF отсутствует. DD — максимальная наблюдаемая просадка известных закрытий, не непрерывная equity при EXCLUDED.

## Подходы и сигналы

| Инструмент | Первый | Второй | Третий | LONG | SHORT | Входы | Отказы | Дни сделок | Активные месяцы |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CNYRUBF | 2903 | 535 | 144 | 73 | 59 | 77 | 67 | 52 | 11 |
| GLDRUBF | 2766 | 170 | 23 | 10 | 9 | 2 | 21 | 2 | 2 |
| IMOEXF | 378 | 78 | 17 | 9 | 6 | 5 | 12 | 3 | 1 |
| USDRUBF | 5352 | 1142 | 280 | 113 | 126 | 104 | 174 | 82 | 12 |

## CNYRUBF

Условная экономика: **NEGATIVE_AFTER_C1**. Данные: **INCOMPLETE_SOURCE_OR_OUTCOMES**.

Отказы: `{'DATA_QUALITY_POSITION_BLOCK': 4, 'ENTRY_MORE_THAN_4_TICKS_FROM_CONSTRUCTION': 27, 'POSITION_BUSY': 5, 'SESSION_LIMIT': 9, 'STOP_ABOVE_12_TICKS': 3, 'STOP_BELOW_3_TICKS': 7, 'THIRD_CLOSE_NOT_REJECTED': 12}`.

Средние победа/убыток, концентрация, откаты, интервалы подходов, ширина зоны и Stop: research_metrics.json; полные исходные значения: signals.csv и construction_events.csv.

| Выход | Число | Gross R | Cost R | Net R |
| --- | --- | --- | --- | --- |
| STOP | 33 | -33 | 17.93333333333333333333333335 | -50.93333333333333333333333336 |
| TAKE | 5 | 25.53333333333333333333333334 | 2.633333333333333333333333334 | 22.9 |
| TIME | 4 | -0.9333333333333333333333333333 | 2.066666666666666666666666667 | -3.00 |
| SESSION_FLAT | 19 | 2.600000000000000000000000000 | 9.933333333333333333333333335 | -7.333333333333333333333333334 |

STOP означает движение к структурному Stop, в том числе неблагоприятный gap. TIME/SESSION_FLAT — выход до достижения Take; C1 уменьшает каждый известный результат. Разрез именно убыточных закрытий сохранён в loss_attribution; причинность рыночного режима из этих данных не утверждается.


## GLDRUBF

Условная экономика: **NEGATIVE_AFTER_C1**. Данные: **INCOMPLETE_SOURCE_OR_OUTCOMES**.

Отказы: `{'OPEN_WRONG_SIDE_OF_CONSTRUCTION': 1, 'STOP_ABOVE_12_TICKS': 12, 'STOP_BELOW_3_TICKS': 4, 'THIRD_CLOSE_NOT_REJECTED': 4}`.

Средние победа/убыток, концентрация, откаты, интервалы подходов, ширина зоны и Stop: research_metrics.json; полные исходные значения: signals.csv и construction_events.csv.

| Выход | Число | Gross R | Cost R | Net R |
| --- | --- | --- | --- | --- |
| STOP | 2 | -3.25 | 1.166666666666666666666666667 | -4.416666666666666666666666667 |
| TAKE | 0 | 0 | 0 | 0 |
| TIME | 0 | 0 | 0 | 0 |
| SESSION_FLAT | 0 | 0 | 0 | 0 |

STOP означает движение к структурному Stop, в том числе неблагоприятный gap. TIME/SESSION_FLAT — выход до достижения Take; C1 уменьшает каждый известный результат. Разрез именно убыточных закрытий сохранён в loss_attribution; причинность рыночного режима из этих данных не утверждается.


## IMOEXF

Условная экономика: **POSITIVE_CONDITIONAL**. Данные: **INCOMPLETE_SOURCE_OR_OUTCOMES**.

Отказы: `{'ENTRY_MORE_THAN_4_TICKS_FROM_CONSTRUCTION': 6, 'STOP_ABOVE_12_TICKS': 1, 'STOP_BELOW_3_TICKS': 3, 'THIRD_CLOSE_NOT_REJECTED': 2}`.

Средние победа/убыток, концентрация, откаты, интервалы подходов, ширина зоны и Stop: research_metrics.json; полные исходные значения: signals.csv и construction_events.csv.

| Выход | Число | Gross R | Cost R | Net R |
| --- | --- | --- | --- | --- |
| STOP | 2 | -2 | 0.9 | -2.9 |
| TAKE | 1 | 5.666666666666666666666666667 | 0.6666666666666666666666666667 | 5 |
| TIME | 0 | 0 | 0 | 0 |
| SESSION_FLAT | 0 | 0 | 0 | 0 |

STOP означает движение к структурному Stop, в том числе неблагоприятный gap. TIME/SESSION_FLAT — выход до достижения Take; C1 уменьшает каждый известный результат. Разрез именно убыточных закрытий сохранён в loss_attribution; причинность рыночного режима из этих данных не утверждается.


## USDRUBF

Условная экономика: **NEGATIVE_AFTER_C1**. Данные: **INCOMPLETE_SOURCE_OR_OUTCOMES**.

Отказы: `{'AMBIGUOUS_BOTH_SIDES': 2, 'ENTRY_MORE_THAN_4_TICKS_FROM_CONSTRUCTION': 99, 'MISSING_EXECUTION_BAR': 2, 'POSITION_BUSY': 2, 'SESSION_LIMIT': 13, 'STOP_ABOVE_12_TICKS': 4, 'STOP_BELOW_3_TICKS': 15, 'THIRD_CLOSE_NOT_REJECTED': 39}`.

Средние победа/убыток, концентрация, откаты, интервалы подходов, ширина зоны и Stop: research_metrics.json; полные исходные значения: signals.csv и construction_events.csv.

| Выход | Число | Gross R | Cost R | Net R |
| --- | --- | --- | --- | --- |
| STOP | 75 | -75.2 | 38.20000000000000000000000006 | -113.4000000000000000000000001 |
| TAKE | 13 | 64.60000000000000000000000001 | 6.400000000000000000000000001 | 58.2 |
| TIME | 1 | 2.6 | 0.4 | 2.2 |
| SESSION_FLAT | 13 | 16.06666666666666666666666667 | 6.566666666666666666666666668 | 9.500000000000000000000000000 |

STOP означает движение к структурному Stop, в том числе неблагоприятный gap. TIME/SESSION_FLAT — выход до достижения Take; C1 уменьшает каждый известный результат. Разрез именно убыточных закрытий сохранён в loss_attribution; причинность рыночного режима из этих данных не утверждается.

## Все календарные месяцы

| Инструмент | Месяц | CLOSED | SKIP | EXCLUDED | Net R | Полнота |
| --- | --- | --- | --- | --- | --- | --- |
| USDRUBF | 2023-01 | 4 | 0 | 1 | 9.5 | PARTIAL_DATA |
| USDRUBF | 2023-02 | 14 | 1 | 0 | -11.23333333333333333333333334 | PARTIAL_DATA |
| USDRUBF | 2023-03 | 16 | 0 | 1 | -10.08333333333333333333333334 | PARTIAL_DATA |
| USDRUBF | 2023-04 | 10 | 1 | 0 | -1.100000000000000000000000001 | PARTIAL_DATA |
| USDRUBF | 2023-05 | 9 | 0 | 0 | -1.200000000000000000000000000 | PARTIAL_DATA |
| USDRUBF | 2023-06 | 5 | 0 | 0 | -4.216666666666666666666666667 | PARTIAL_DATA |
| USDRUBF | 2023-07 | 8 | 0 | 0 | -6.133333333333333333333333334 | PARTIAL_DATA |
| USDRUBF | 2023-08 | 3 | 0 | 0 | -4.466666666666666666666666667 | PARTIAL_DATA |
| USDRUBF | 2023-09 | 9 | 0 | 0 | -8.166666666666666666666666668 | PARTIAL_DATA |
| USDRUBF | 2023-10 | 3 | 0 | 0 | 11.0 | COMPLETE |
| USDRUBF | 2023-11 | 10 | 0 | 0 | -8.733333333333333333333333334 | PARTIAL_DATA |
| USDRUBF | 2023-12 | 11 | 0 | 0 | -8.666666666666666666666666667 | COMPLETE |
| CNYRUBF | 2023-01 | 11 | 0 | 3 | -8.350000000000000000000000000 | PARTIAL_DATA |
| CNYRUBF | 2023-02 | 4 | 0 | 2 | -0.966666666666666666666666667 | PARTIAL_DATA |
| CNYRUBF | 2023-03 | 0 | 0 | 1 | 0 | PARTIAL_DATA |
| CNYRUBF | 2023-04 | 1 | 0 | 1 | -0.75 | PARTIAL_DATA |
| CNYRUBF | 2023-05 | 5 | 0 | 0 | -7.000000000000000000000000001 | PARTIAL_DATA |
| CNYRUBF | 2023-06 | 1 | 0 | 1 | -0.6 | PARTIAL_DATA |
| CNYRUBF | 2023-07 | 7 | 0 | 4 | -9.000000000000000000000000001 | PARTIAL_DATA |
| CNYRUBF | 2023-08 | 12 | 0 | 2 | -15.23333333333333333333333333 | PARTIAL_DATA |
| CNYRUBF | 2023-09 | 7 | 0 | 2 | -1.366666666666666666666666667 | PARTIAL_DATA |
| CNYRUBF | 2023-10 | 2 | 0 | 0 | -3.066666666666666666666666667 | PARTIAL_DATA |
| CNYRUBF | 2023-11 | 5 | 0 | 0 | 10.7 | PARTIAL_DATA |
| CNYRUBF | 2023-12 | 6 | 0 | 0 | -2.733333333333333333333333334 | COMPLETE |
| GLDRUBF | 2023-01 | 0 | 0 | 0 | null | NO_COVERAGE |
| GLDRUBF | 2023-02 | 0 | 0 | 0 | null | NO_COVERAGE |
| GLDRUBF | 2023-03 | 0 | 0 | 0 | null | NO_COVERAGE |
| GLDRUBF | 2023-04 | 0 | 0 | 0 | null | NO_COVERAGE |
| GLDRUBF | 2023-05 | 0 | 0 | 0 | null | NO_COVERAGE |
| GLDRUBF | 2023-06 | 0 | 0 | 0 | null | NO_COVERAGE |
| GLDRUBF | 2023-07 | 0 | 0 | 0 | 0 | PARTIAL_DATA |
| GLDRUBF | 2023-08 | 0 | 0 | 0 | 0 | PARTIAL_DATA |
| GLDRUBF | 2023-09 | 1 | 0 | 0 | -1.666666666666666666666666667 | PARTIAL_DATA |
| GLDRUBF | 2023-10 | 0 | 0 | 0 | 0 | PARTIAL_DATA |
| GLDRUBF | 2023-11 | 1 | 0 | 0 | -2.75 | PARTIAL_DATA |
| GLDRUBF | 2023-12 | 0 | 0 | 0 | 0 | PARTIAL_DATA |
| IMOEXF | 2023-01 | 0 | 0 | 0 | null | NO_COVERAGE |
| IMOEXF | 2023-02 | 0 | 0 | 0 | null | NO_COVERAGE |
| IMOEXF | 2023-03 | 0 | 0 | 0 | null | NO_COVERAGE |
| IMOEXF | 2023-04 | 0 | 0 | 0 | null | NO_COVERAGE |
| IMOEXF | 2023-05 | 0 | 0 | 0 | null | NO_COVERAGE |
| IMOEXF | 2023-06 | 0 | 0 | 0 | null | NO_COVERAGE |
| IMOEXF | 2023-07 | 0 | 0 | 0 | null | NO_COVERAGE |
| IMOEXF | 2023-08 | 0 | 0 | 0 | null | NO_COVERAGE |
| IMOEXF | 2023-09 | 0 | 0 | 0 | null | NO_COVERAGE |
| IMOEXF | 2023-10 | 0 | 0 | 0 | null | NO_COVERAGE |
| IMOEXF | 2023-11 | 0 | 0 | 0 | 0 | PARTIAL_DATA |
| IMOEXF | 2023-12 | 3 | 0 | 2 | 2.1 | PARTIAL_DATA |
| ALL_R_DIAGNOSTIC | 2023-01 | 15 | 0 | 4 | 1.150000000000000000000000000 | PARTIAL_DATA |
| ALL_R_DIAGNOSTIC | 2023-02 | 18 | 1 | 2 | -12.20000000000000000000000001 | PARTIAL_DATA |
| ALL_R_DIAGNOSTIC | 2023-03 | 16 | 0 | 2 | -10.08333333333333333333333334 | PARTIAL_DATA |
| ALL_R_DIAGNOSTIC | 2023-04 | 11 | 1 | 1 | -1.850000000000000000000000001 | PARTIAL_DATA |
| ALL_R_DIAGNOSTIC | 2023-05 | 14 | 0 | 0 | -8.20000000000000000000000000 | PARTIAL_DATA |
| ALL_R_DIAGNOSTIC | 2023-06 | 6 | 0 | 1 | -4.816666666666666666666666667 | PARTIAL_DATA |
| ALL_R_DIAGNOSTIC | 2023-07 | 15 | 0 | 4 | -15.13333333333333333333333334 | PARTIAL_DATA |
| ALL_R_DIAGNOSTIC | 2023-08 | 15 | 0 | 2 | -19.70000000000000000000000000 | PARTIAL_DATA |
| ALL_R_DIAGNOSTIC | 2023-09 | 17 | 0 | 2 | -11.20000000000000000000000000 | PARTIAL_DATA |
| ALL_R_DIAGNOSTIC | 2023-10 | 5 | 0 | 0 | 7.933333333333333333333333333 | PARTIAL_DATA |
| ALL_R_DIAGNOSTIC | 2023-11 | 16 | 0 | 0 | -0.783333333333333333333333334 | PARTIAL_DATA |
| ALL_R_DIAGNOSTIC | 2023-12 | 20 | 0 | 2 | -9.300000000000000000000000001 | PARTIAL_DATA |

NO_COVERAGE до начала истории не является нулевой доходностью; месяцы с историей и без сделок имеют нулевую известную сумму. Coverage_report содержит каждый календарный исследовательский день/слот, включая PRE_INCEPTION.

## Оценка и границы

Технический итог и детерминизм — validation.json и audit.json. Число CLOSED, торговые дни и активные месяцы раскрыты отдельно. Пригодность к будущей Optimization технически проверяема после PASS аудита; достаточность выборки требует общих порогов, заданных до будущего ранжирования. Низкий исходный PF не отвергает семейство C. Отрицательная условная экономика не объявляется прибыльной.

A_v1 и B4/B7/B10 — разные конструкции; их неизменные UNKNOWN и результаты сравниваются отдельно в Comparison.md. Совпадения сигналов не складываются в независимые сделки.

Источник pinned 2023 M5, ноль прочитанных ценовых байтов 2024+. USDRUBF/CNYRUBF с 3 января, GLDRUBF с 11 июля, IMOEXF с 14 ноября. После EXCLUDED текущий день блокируется; последующие независимые дни явно условно FLAT. Обычный trades.csv содержит только CLOSED.

STOP после Baseline C. Optimization, Robustness, WF, TRUE OOS и следующие стратегии не выполнялись; Draft PR без merge/auto-merge.
