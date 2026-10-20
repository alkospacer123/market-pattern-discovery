# T3/M15 — подтверждение растянутого пробоя одной свечой

## Результат

Критерий не выполнен: отрицательных CLOSED и MTM месяцев стало 7 и 7 против 6 и 6 в CONTROL. Худший месяц и DD стали мельче, PF вырос, но число отрицательных месяцев не сократилось. Количество победителей >=2R: 74 → 63; их суммарный вклад 318.180R → 265.344R.

Единственная альтернатива сопоставлена с неизменным CONTROL. Критерий требует сокращения числа и глубины отрицательных месяцев и приемлемой сохранности сильных трендов. Порог неприемлемой потери трендов заранее не задан; ниже приведены абсолютные потери, без подбора такого порога.

| variant | CLOSED | OPEN_at_period_end | gross_PF | expectancy_R | gross_R | CLOSED_R_DD | MTM_R_DD |
| --- | --- | --- | --- | --- | --- | --- | --- |
| CONTROL | 549 | 1 | 1.725663 | 0.336696 | 184.846098 | 16.868904 | 20.913084 |
| CONFIRM | 445 | 1 | 1.843017 | 0.376429 | 167.510962 | 13.602217 | 17.389724 |

| variant | CLOSED_R_negative_months | CLOSED_R_negative_sum | CLOSED_R_worst_month | CLOSED_R_worst_R | MTM_R_negative_months | MTM_R_negative_sum | MTM_R_worst_month | MTM_R_worst_R |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CONTROL | 6 | -22.819622 | 2023-08 | -7.315281 | 6 | -31.473579 | 2024-02 | -9.305471 |
| CONFIRM | 7 | -15.537692 | 2024-06 | -4.904697 | 7 | -23.362793 | 2024-05 | -5.695083 |

Development — только 2023–2024 МСК. Обе системы идут непрерывно от исходного холодного старта, без перезапуска на границе года и без принудительного закрытия на конце. CLOSED-R DD — по frozen порядку exit Close/instrument/trade_id; MTM-R DD — по синхронизированной сетке наблюдённых Close с carry-forward последней отметки. Это суммы нормированных R, а не кривая денежного капитала.

## Отдельно 2023 и 2024

| variant | period | CLOSED | OPEN_at_period_end | gross_PF | expectancy_R | gross_R | CLOSED_R_DD | MTM_R_DD | CLOSED_R_negative_months | MTM_R_negative_months | winner_ge_2R_count | winner_ge_2R_R |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CONTROL | 2023 | 192 | 0 | 2.317459 | 0.540242 | 103.726454 | 10.709148 | 14.021105 | 3 | 3 | 29 | 133.212014 |
| CONTROL | 2024 | 357 | 1 | 1.460921 | 0.227226 | 81.119643 | 16.868904 | 20.913084 | 3 | 3 | 45 | 184.967954 |
| CONFIRM | 2023 | 151 | 0 | 2.400674 | 0.591203 | 89.271626 | 7.680936 | 10.482179 | 4 | 4 | 26 | 114.886089 |
| CONFIRM | 2024 | 294 | 1 | 1.579682 | 0.266120 | 78.239336 | 13.602217 | 17.389724 | 3 | 3 | 37 | 150.458382 |

Год определяется frozen exit-bar Close. Годовые DD считаются внутри года относительно его начального уровня; позиции и их риски не сбрасываются. Поэтому CLOSED и MTM могут относить результат к разным месяцам и годам.

## Конкретные изменения знака

| month | basis | CONTROL_R | CONFIRM_R | transition |
| --- | --- | --- | --- | --- |
| 2023-01 | CLOSED_R | 3.983872 | -1.429855 | 1_TO_-1 |
| 2023-01 | MTM_R | 3.983872 | -1.429855 | 1_TO_-1 |

| month | CONTROL_CLOSED_R | CONFIRM_CLOSED_R | CONTROL_MTM_R | CONFIRM_MTM_R |
| --- | --- | --- | --- | --- |
| 2023-01 | 3.983872 | -1.429855 | 3.983872 | -1.429855 |
| 2023-03 | -4.522581 | -1.473496 | -4.522581 | -1.473496 |
| 2023-05 | -0.563082 | -4.611140 | -0.563082 | -4.611140 |
| 2023-08 | -7.315281 | -2.312557 | -8.141216 | -3.038041 |
| 2024-02 | -6.532981 | -0.166395 | -9.305471 | -2.210480 |
| 2024-05 | -2.116779 | -0.639552 | -7.172310 | -5.695083 |
| 2024-06 | -1.768918 | -4.904697 | -1.768918 | -4.904697 |

Все 48 пар месяц/база, включая месяцы без смены знака: MONTH_SIGN_TRANSITIONS.csv. Полный календарь и покрытие: MONTHLY.csv, COVERAGE.csv.

## Сильные тренды и потери исходных победителей

| variant | winner_ge_2R_count | winner_ge_2R_R | gross_positive_R | gross_negative_R |
| --- | --- | --- | --- | --- |
| CONTROL | 74 | 318.179969 | 439.573150 | -254.727052 |
| CONFIRM | 63 | 265.344471 | 366.215157 | -198.704195 |

| original_ge2R_count | original_ge2R_R | original_ge2R_still_ge2R | original_ge2R_skipped | original_ge2R_to_nonpositive | original_ge2R_OPEN | original_ge2R_CONFIRMED_CLOSED_contribution_R |
| --- | --- | --- | --- | --- | --- | --- |
| 74 | 318.179969 | 57 | 13 | 3 | 0 | 238.749751 |

| missed_profitable | missed_profitable_CONTROL_R | profitable_to_nonpositive | profitable_to_OPEN | profitable_reduced |
| --- | --- | --- | --- | --- |
| 41 | 67.980462 | 13 | 0 | 44 |

| signal_year | original_ge2R_count | CONTROL_R | retained_ge2R | skipped | to_nonpositive | OPEN | CONFIRM_CLOSED_contribution_R |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2023 | 29 | 133.212014 | 22 | 5 | 1 | 0 | 104.162633 |
| 2024 | 45 | 184.967954 | 35 | 8 | 2 | 0 | 134.587119 |
| 2023_2024 | 74 | 318.179969 | 57 | 13 | 3 | 0 | 238.749751 |

Общее количество >=2R уменьшилось на 14.9%, их вклад — на 16.6%. Вклад фиксированной исходной когорты уменьшился на 25.0%. Это раскрытая потеря трендов, а не автоматически приемлемый порог.

Общий набор >=2R победителей альтернативы включает новые сделки. Отдельная исходная когорта удерживает те же instrument/signal Close/side: её вклад включает все CLOSED исходы, в том числе менее 2R и отрицательные; OPEN раскрыт отдельно и не заменён нулевой прибылью. ORIGINAL_GE_2R_WINNERS.csv содержит каждую исходную крупную сделку, LOST_AND_REDUCED_WINNERS.csv — все потерянные/уменьшенные исходные прибыли.

## Входы, занятость и причинный порядок

| common_signals | missed_control_entries | new_confirm_entries | new_entries_R | missed_entries_CONTROL_R |
| --- | --- | --- | --- | --- |
| 400 | 150 | 46 | 19.131946 | -25.480511 |

| signal_year | eligible_attempts | stretched_attempts | executed_confirmed | failed_price | outside_T1 | missing_confirmation | missing_entry | unstretched_executed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2023 | 212 | 109 | 48 | 53 | 7 | 1 | 0 | 103 |
| 2024 | 396 | 172 | 71 | 95 | 6 | 0 | 0 | 224 |
| 2023_2024 | 608 | 281 | 119 | 148 | 13 | 1 | 0 | 327 |

Сделки сопоставлены по instrument/signal Close/side, а не по переиспользуемому frozen счётчику trade_id. TRADE_COMPARISON.csv показывает цену/время входа, исход и причину пропуска. Для общих CLOSED приведены entry penalty, exit delta и альтернативный PNL в CONTROL R0. Разность PNL = exit delta − entry penalty. Ни один готовый CSV сделок не служит входом симуляции.

| variant | reason | count |
| --- | --- | --- |
| CONTROL | EXECUTED_NEXT_OPEN | 550 |
| CONTROL | MISSING_ADJACENT_OPEN | 1 |
| CONTROL | OUTSIDE_T1 | 338 |
| CONTROL | OUTSIDE_T1_AND_OCCUPIED | 283 |
| CONTROL | POSITION_OCCUPIED | 845 |
| CONFIRM | CONFIRMATION_ENTRY_RESERVED | 83 |
| CONFIRM | CONFIRMATION_FAILED | 148 |
| CONFIRM | CONFIRMATION_OUTSIDE_T1 | 13 |
| CONFIRM | EXECUTED_CONFIRMED_OPEN | 119 |
| CONFIRM | EXECUTED_NEXT_OPEN | 327 |
| CONFIRM | MISSING_ADJACENT_CONFIRMATION | 1 |
| CONFIRM | OUTSIDE_T1 | 359 |
| CONFIRM | OUTSIDE_T1_AND_OCCUPIED | 262 |
| CONFIRM | POSITION_OCCUPIED | 705 |

CONTROL/CONFIRM_SIGNALS.csv.gz содержат все исходные сигналы, включая вне T1 и занятый инструмент, стадию ожидания, Close подтверждения и конечную причину. MARKS отражает фактическую позицию и отдельный резерв ожидания на каждой свече. STOPS содержит каждый stop test и обновление; TRADES/OPEN/SNAPSHOTS — конечные исходы и переносы.

Растянутый исходный сигнал >=0.5 ATR ждёт ровно одну смежную M15. Close подтверждения строго дальше исходного Close и исходного Donchian, внутри T1 [10:00,18:00). Вход на следующем смежном Open. Провал, разрыв или выход из T1 завершает исходную попытку. Новый самостоятельный сигнал на Close отказа вправе начать собственную попытку; это не третья свеча старого сигнала. При успехе слот зарезервирован до execution Open. Не добавлены фильтры, повторное ожидание, подбор ATR/порогов или изменения R15.

Initial Stop всегда 2 ATR исходной сигнальной свечи от фактической новой цены входа, trail 3.5 текущего ATR без изменений. High/Low подтверждающей свечи не используются для трейла будущей позиции. Stop-first; adverse Open fill, иначе касание старого stop. Новый trail действует только со следующей свечи. Execution bar уже проверяет Initial Stop.

## CONTROL, независимость и воспроизводимость

Изолированный полный CONTROL воспроизвёл PR518: 1114 CLOSED / 356 INITIAL_STOP, все журналы; дополнительно сверены поля M15 CONTROL PR560. Development CONTROL сверён со всеми исходными полями PR518 и entry/exit/risk полями PR562, включая OPEN на границе. CONTROL mismatch останавливает процесс до сравнения альтернативы.

Отдельный scalar verifier: 321213 строк / 3256082 полей, максимальное абсолютное численное отличие 4.44e-16; 102 fresh CSV/Decimal проверок календаря/PF/R/expectancy. Дополнительный fresh CSV/Decimal verifier проверил 8520 полей всех годовых/месячных метрик, DD и когортных сравнений. Features независимо пересчитаны streaming EWM PR518, исполнения — отдельным алгоритмом agenda. Предел независимости: тот же автор, внешняя человеческая или отдельная агентская экспертиза НЕ выполнена.

Синтетические контракты проверяют обе реализации: порог включительно, LONG/SHORT, строгий Close, обе смежности, 18:00, исходный ATR, отсутствие до-входного trail, первый stop, резерв, новый сигнал после отказа, EOF и gap-fill. Prefix invariance и perturbation будущего OHLC подтверждают причинность признаков и ранее доступных событий. REPEATABILITY.json фиксирует первый и два свежих полных процесса после CODE_FREEZE, с direct bytes и SHA256 каждого generated artifact.

## Ограничения данных и денежная исполнимость

2023 — неполный N4: GLDRUBF начинается 11 июля, IMOEXF 14 ноября; в начале года торгуются только USD/CNY. Фактические gaps не заполняются. H1 — frozen ordinal blocks четырёх M15 по local Close-date, только полные смежные блоки; исторические rolling/EWM явно CROSS_DAY/CROSS_YEAR, H1AvailableAt <= signal Close. Midnight МСК сохранён. Одинаковые исходные данные и прогрев обеих систем не устраняют ограничение короткой истории.

2025–2026 прочитаны только отдельным обязательным CONTROL reconciliation и маркированы RETROSPECTIVE_CONTROL_ONLY; альтернативы на них нет. Это не новый независимый OOS. Сигнальные цены после development endpoint не преобразуются development-парсером в числа. OPEN остаются цензурированными.

Результаты GROSS_ONLY. R15=1.5% и nominal risk cap=6% не менялись. R replay не моделирует фактический капитал, integer qty, исторические ГО, tick-value и расходы. Frozen stops сохраняют исследовательские off-grid значения. Денежный Net, доходность и рублёвая DD — NOT_VALIDATED. CAPITAL_FEASIBILITY.json фиксирует отсутствующие входные данные и формулу qty, без чтения production registry.

Параметры --round-trip-cost-R и --round-trip-slippage-R дают отдельную нормированную чувствительность на CLOSED сделки; по умолчанию 0 для точного Gross CONTROL. Она не заменяет реальные комиссии/проскальзывание FINAM и не доказывает исполнимый Net. Не использована для настройки правила.

## Решение

Правило не выполнило совместный критерий сокращения числа и глубины отрицательных CLOSED/MTM месяцев. Улучшение PF и expectancy не меняет этот вывод; оснований переносить правило в production по этому replay нет.

Только audit-каталог, один Draft PR. Без merge/auto-merge. LIVE H1, M15 robot, FINAM, Tasks, SQLite, Control Center и производственные параметры не читались, не запускались и не менялись.
