# Замороженные правила кандидата

**A6+S1 / T3 M15 / NEXT_OPEN / TRAIL_375. GROSS_ONLY / COSTS_DEFERRED / NOT_LIVE_READY.**

Канон — merged #510 на main `fbfb0650ac2af6c6b374d10b67dd62801cd0fcc4`: [SPEC](../t3_m15_a6_s1_robustness_v1/SPEC.json), [engine](../t3_m15_a6_s1_robustness_v1/engine.py), [scalar](../t3_m15_a6_s1_robustness_v1/scalar.py), [common](../t3_m15_a6_s1_robustness_v1/common.py). Исходники и их численная семантика сохраняются; будущий адаптер периодов требует отдельного CONTROL, а не изменения стратегии.

| Объект | Неизменное правило |
| --- | --- |
| Состав | USDRUBF, CNYRUBF, GLDRUBF, IMOEXF; LONG и SHORT на каждом |
| Источник сигналов | M15; MSK / Europe/Moscow; исходный CSV start-label, расчётное время — Close = Open + 15 минут |
| H1 | Дневные ordinal-блоки по четыре наблюдаемых M15; учитываются только полные последовательные блоки с расстоянием first/last Close 45 минут; доступны на четвёртом Close |
| Направление LONG | Последний доступный завершённый H1 Close > EMA75 и slope5 > 0 |
| Направление SHORT | H1 Close < EMA75 и slope5 < 0 |
| EMA / slope | EMA75 (`adjust=False`, `min_periods=75`), slope = EMA − EMA.shift(5) |
| ADX | H1 ADX14 > 20, строгое сравнение; прежняя рекурсия и инициализация |
| ATRRatio | H1 ATR14 / rolling mean20 H1 ATR > 1 |
| A6 | Текущий доступный H1 ATRRatio > предыдущий опубликованный H1 ATRRatio |
| Donchian | M15 high/low за 20 предыдущих баров, `shift(1)`; LONG Close > prior high, SHORT Close < prior low |
| NEXT_OPEN | Только строго соседний M15: execution Open = signal Close, execution Close = signal Close + 15 минут. Пропуск соседа = skip, без ожидания более позднего Open |
| Первоначальный Stop | actual_entry − side × 2 × M15 ATR14 завершённого signal bar |
| Initial R | abs(actual_entry − initial_stop), неизменный знаменатель на весь срок сделки |
| S1 | После пережитого завершённого post-entry бара с favorable extreme ≥ +1 initial R; execution bar тоже участвует |
| Trailing | favorable extreme − side × 3,75 × ATR14 текущего завершённого M15; только ужесточение после S1; действует на следующем наблюдаемом баре |
| Stop-first | Проверить старый Stop до extrema и S1/Trailing; при adverse Open за Stop — fill по Open, иначе при касании по Stop |
| Занятость | Одна позиция на инструмент; прежние busy decisions, pending, same-close exit/re-entry и deterministic IDs/order |
| Границы дня/окна | H1 grouping сбрасывает дневной блок; рекурсивные индикаторы и Donchian пересекают дни, как в каноне. Состояние не сбрасывается на границе отчётного блока |
| Удержание | Прежние overnight/weekend и gap правила; без нового session flat, time Stop, Take или ограничения времени T1 |
| Агрегация | Нет общих межинструментальных лимитов; сумма initial R условная, без capital/sizing |
| OPEN | Без принудительного закрытия; отдельный снимок состояния; исключён из CLOSED PF/Gross R |

В каноническом коде внутренний `rule="C1"` означает A6+S1, а **не** модель издержек C1 из раннего M5 roadmap. `version="TRAIL_375"`, `mode="NEXT_OPEN"`. Не переносить в этот кандидат настройки старых M5 исследований.

Запрещены смена EMA/slope/ADX/ATR/ATRRatio/Donchian, A6/S1, trailing, entry/fill/Stop/gap/occupancy, состава и направлений; фильтрация часов/месяцев/инструментов/SHORT; добавление EARLY_PROTECT_05; возврат к сетке trailing; подбор параметров по очередному блоку. Не заменять H1 ordinal-модель обычным часовым resample.

Исторический CONTROL (только published reference, не результат WF): PF2023 **2,207278**, PF2024 **1,772134**, PF_ALL **1,911934**, Gross R **+212,522656R**, **480 CLOSED / 1 terminal OPEN**, **20/24** положительных календарных месяцев, CLOSED-R DD **12,628056R**. Точные значения хранятся в WF_SPEC.json. OPEN — IMOEXF LONG `T3-M15-IMOEXF-000090`, вход 30.12.2024 11:15 MSK, последний известный Close 31.12.2024 00:00 MSK. Дальнейшая судьба не проверялась.

Контроль новых адаптеров в будущем обязан сверять весь разрешённый published 2023–2024 CONTROL: trade/Stop/signal/gap, terminal и period-end OPEN, summary/monthly; только совпадения двух PF недостаточно. Параметры и хеши исходников приведены в SOURCE_REVIEW.json. Нового движка или runner в этом дизайне нет.
