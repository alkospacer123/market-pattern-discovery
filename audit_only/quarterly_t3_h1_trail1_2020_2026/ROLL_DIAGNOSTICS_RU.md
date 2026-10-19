# Неизвестная склейка: отдельная диагностика чувствительности

Статус: ROLL_PROVENANCE=UNVERIFIED; TRADABLE_QUARTERLY_PERFORMANCE=NOT_VALIDATED.
Это постфактум-диагностика исходного replay, не фильтр и не оптимизация. Все сделки сохранены в PRIMARY.

## Заранее заданные определения

- Потенциальные квартальные окна: третий четверг марта/июня/сентября/декабря ±3 и ±7 календарных дней. Крайние дни включены целиком; локальное время Europe/Moscow. Это условные календарные anchors, не расписание MOEX и не найденные даты переходов.
- Дополнительное monthly_3d окно — третий четверг каждого месяца ±3 дня для всех шести рынков. Оно не подтверждает monthly cadence. Квартальные окна могут пропускать большую часть реальных energy rolls.
- Открытая сделка пересекает окно, если [entry,exit] пересекает [window_start,window_end]; anchor crossing отдельно означает entry≤anchor≤exit.
- Крупный гэп: absolute fractional gap≥3% ИЛИ absolute gap≥2.5 предыдущих ATR. Первые бары без ATR могут попасть по процентному критерию. Никаких quantiles, выбора лучших порогов или удаления свечей нет.
- Сигнал — eligible breakout/regime на закрытии независимо от занятой позиции. Вход — действительно принятый сигнал при отсутствии позиции. Stop test — каждое событие управления уже открытой позицией. Trigger, activation и tighten учитываются отдельно.
- Прибыль для концентрации относится к exit timestamp; прибыль пересекающих окно сделок дополнительно раскрывается через полный список флагов. Доля positive R имеет знаменатель сумму положительных Net R. Для корректной базы сравнения показаны наблюдаемые H1 и сигналы на 1000 баров рядом/вне окон.

## Концентрация всех шести

| Условные окна | Доля исходных H1 | Доля сигналов | Входов рядом | Выходов рядом | Stop tests рядом | Доля positive R выходов |
|---|---|---|---|---|---|---|
| quarter_3d | 7.137% | 7.927% | 76 | 74 | 1881 | 11.428% |
| quarter_7d | 16.134% | 17.953% | 168 | 176 | 4348 | 23.456% |
| monthly_3d | 23.265% | 20.941% | 208 | 221 | 5577 | 24.151% |

| Ряд | Сделок | Пересекают ±3d окно | Пересекают anchor | Крупный gap при позиции | Gap stop penalty R |
|---|---|---|---|---|---|
| Si | 188 | 21 | 6 | 2 | 0.594 |
| CNY | 113 | 14 | 2 | 2 | 1.789 |
| GD | 171 | 16 | 7 | 15 | 3.895 |
| MIX | 178 | 18 | 4 | 3 | 4.738 |
| BR | 180 | 16 | 5 | 16 | 5.209 |
| NG | 172 | 12 | 2 | 20 | 3.276 |

## Чувствительность уже наблюдаемых сделок

| Корзина | Диагностика | Осталось n | Убрано n | Net PF | Net R | Avg R |
|---|---|---|---|---|---|---|
| PRIMARY4 | ORIGINAL_CONTINUOUS_SERIES | 650 | 0 | 1.636 | 185.818 | 0.286 |
| PRIMARY4 | ATTRIBUTION_OMIT_TOUCH_QUARTER_3D | 581 | 69 | 1.533 | 139.038 | 0.239 |
| PRIMARY4 | ATTRIBUTION_OMIT_TOUCH_QUARTER_7D | 509 | 141 | 1.495 | 113.686 | 0.223 |
| PRIMARY4 | ATTRIBUTION_OMIT_LARGE_GAP_WHILE_OPEN | 628 | 22 | 1.561 | 160.518 | 0.256 |
| PRIMARY4 | ATTRIBUTION_OMIT_ENTRY_OR_HOLDING_LARGE_GAP | 625 | 25 | 1.567 | 161.041 | 0.258 |
| PRIMARY4 | STOP_LEVEL_FILL_ARITHMETIC_CREDIT_ONLY | 650 | 0 | 1.677 | 196.833 | 0.303 |
| ADDITIONAL2 | ORIGINAL_CONTINUOUS_SERIES | 352 | 0 | 1.198 | 34.472 | 0.098 |
| ADDITIONAL2 | ATTRIBUTION_OMIT_TOUCH_QUARTER_3D | 324 | 28 | 1.109 | 18.116 | 0.056 |
| ADDITIONAL2 | ATTRIBUTION_OMIT_TOUCH_QUARTER_7D | 293 | 59 | 1.041 | 6.015 | 0.021 |
| ADDITIONAL2 | ATTRIBUTION_OMIT_LARGE_GAP_WHILE_OPEN | 316 | 36 | 1.082 | 13.021 | 0.041 |
| ADDITIONAL2 | ATTRIBUTION_OMIT_ENTRY_OR_HOLDING_LARGE_GAP | 308 | 44 | 1.085 | 13.261 | 0.043 |
| ADDITIONAL2 | STOP_LEVEL_FILL_ARITHMETIC_CREDIT_ONLY | 352 | 0 | 1.252 | 42.957 | 0.122 |
| ALL6 | ORIGINAL_CONTINUOUS_SERIES | 1002 | 0 | 1.472 | 220.290 | 0.220 |
| ALL6 | ATTRIBUTION_OMIT_TOUCH_QUARTER_3D | 905 | 97 | 1.368 | 157.154 | 0.174 |
| ALL6 | ATTRIBUTION_OMIT_TOUCH_QUARTER_7D | 802 | 200 | 1.317 | 119.701 | 0.149 |
| ALL6 | ATTRIBUTION_OMIT_LARGE_GAP_WHILE_OPEN | 944 | 58 | 1.390 | 173.539 | 0.184 |
| ALL6 | ATTRIBUTION_OMIT_ENTRY_OR_HOLDING_LARGE_GAP | 933 | 69 | 1.396 | 174.302 | 0.187 |
| ALL6 | STOP_LEVEL_FILL_ARITHMETIC_CREDIT_ONLY | 1002 | 0 | 1.520 | 239.791 | 0.239 |

Остальные инструменты и сценарии находятся в roll_sensitivity.csv. Удаление закрытых сделок — условное разложение результата, а не новый исполнимый replay: после удаления не моделируются освобождение позиции, новые входы, изменившиеся индикаторы или новый путь стопов. Исходные показатели находятся в ORIGINAL_CONTINUOUS_SERIES.

STOP_LEVEL_FILL_ARITHMETIC_CREDIT_ONLY прибавляет сумму sign*(stop−actual_gap_fill)/initialR к исходным Gross/Net R. Издержки, моменты выхода и последовательность сделок не меняются. Эта величина показывает прямую adverse gap-stop penalty, но не оценивает полный эффект discontinuity на ATR/EMA/Donchian, входы и будущие стопы. Нельзя считать stop-level fill физически доступным при гэпе.

## Файлы и ограничения

- potential_expiry_windows.csv: все proxy windows с actual_roll_date_confirmed=False.
- trade_roll_flags.csv: каждая закрытая сделка, пересечения/anchors, entry/exit proximity, large-gap exposures и gap-stop penalty.
- roll_concentration.csv: инструменты и три корзины, каждый год и общий период; сигналы/входы/выходы/stop tests/triggers/activation/profit и базовая экспозиция.
- potential_window_metrics.csv: детализация по каждому инструменту и условному окну.
- gap_events.csv: все наблюдаемые разрывы по заранее заданному критерию, без публикации исходных OHLC.
- roll_sensitivity.csv: исходный результат и явно отделённые диагностические разложения.

Связь результатов с календарными окнами или гэпами не идентифицирует причинный эффект ролловера: окна занимают часть торговой истории, сделки могут быть длинными, а кризисные рыночные гэпы не являются доказанными склейками. Отсутствие концентрации в выбранных окнах тоже не подтверждает корректность ряда. Для точной проверки нужны паспорт поставщика и составляющие контракты. Параметры и основной журнал не меняются.
