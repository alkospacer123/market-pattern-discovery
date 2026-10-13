Неизменный **A6+S1 / T3 M15 / NEXT_OPEN / TRAIL_375** на полном календарном **2025 WF** даёт **WF_MIXED**. Gross-знак положительный у календарных CLOSED и новых WF входов, но второй квартал отрицательный, GLDRUBF SHORT отрицателен, месячная регулярность и концентрация ограничивают результат. Параметры, фильтры, состав инструментов и исполнение не менялись.

**2025 явно авторизован пользователем 13.10.2026 исключительно для этого WF. 2026 TRUE OOS остаётся закрытым.** Отдельный машинный документ — `USER_AUTHORIZATION.json`; предыдущие ROADMAP/исследования не меняются.

| Период | CLOSED | OPEN на конец | Gross PF | Gross R |
| --- | ---: | ---: | ---: | ---: |
| Полный 2025 | 300 | 1 | 1,581308 | +86,876613R |
| W1 | 71 | 1 | 1,162494 | +6,064142R |
| W2 | 61 | 1 | 0,672386 | −12,842903R |
| W3 | 90 | 1 | 2,171600 | +49,645764R |
| W4 | 78 | 1 | 2,440315 | +44,009610R |

- Новая WF cohort (signal и entry оба в 2025): **299 CLOSED / 1 OPEN, PF 1,563150, +84,163026R, expectancy +0,281482R**. Календарная expectancy +0,289589R. Унаследованный IMOEXF `T3-M15-IMOEXF-000090` закрыт с **+2,713588R** и не считается новым WF входом.
- **7/12** положительных CLOSED месяцев, 5 отрицательных. Худший июнь **−12,111285R**; серия 11 проигрышей и 4 отрицательных месяца. CLOSED-R DD **28,637394R**, восстановление **10.09.2025 15:30 MSK**, 200,729167 дня от первого underwater CLOSED. Исторические критерии PF/20 из 24 не превращаются в автоматический WF PASS.
- LONG **+64,199500R / PF 2,283453**, SHORT **+22,677113R / PF 1,228073**. Все четыре инструмента в целом положительные, но **GLDRUBF SHORT −5,572762R / PF 0,724975**; все instrument×side и отрицательные ячейки сохранены.
- Лучший месяц даёт **42,298813%**, лучшие три **80,509708%** годового R. Без top10 победителей **+4,505390R / PF 1,030146**; без трёх лучших месяцев **+16,932505R / PF 1,145851**. Все четыре full-year leave-one-out положительные. Исключения только диагностические, первичные результаты полные.
- Stress **−0,05R/CLOSED:** **+71,876613R / PF 1,453618 / DD 33,836047R**. **−0,10R/CLOSED:** **+56,876613R / PF 1,339503 / DD 39,432673R**. Это абстрактные R-потери, не реальные FINAM/C1 costs.
- Marked-R отдельно **+83,374338R**, 8/12 положительных месяцев: CLOSED R + U_end − U_start. Terminal OPEN — USDRUBF LONG `T3-M15-Si-000215`, S1 не активирован; mark **+0,029911R** на последнем разрешённом Close **31.12.2025 00:00 MSK**, staleness 24 часа. Нет ликвидации/оценки/закрытия через 2026. Сумма R не доходность капитала.

Проверка:

- Actual GitHub main **fa188b51fbd27df5a51a43a9742bc772a1c17abd**, #510/#511 merged. Правила решения #511 неизменны; **WF_MIXED**, не автоматический PASS и не разрешение TRUE OOS.
- Протокол/разрешение/код/конфигурация/tests опубликованы до raw-read: **cf19f4dc**. Первый DEVELOPMENT-only attempt остановился на сериализации служебного checkpoint numpy.int64, до полного CONTROL и любых данных WF. Свидетельства/первоначальный freeze сохранены; исправлены только serialization cast и force-add ignored outputs, добавлен regression test. Исправленный code freeze **2ba722c6**, опубликован до повторного полного CONTROL и первого чтения 2025. Frozen replay/analysis/spec после этого не менялись; engine/scalar/metrics побайтно #510. Все 43 synthetic tests PASS.
- **Полный CONTROL PASS** в обеих реализациях: trade/Stop/signal/gap/terminal и monthly OPEN, #505–#508, прямые #510 journals и все опубликованные summary/monthly/diagnostics. PF2023 **2,2072776314**, PF2024 **1,7721337045**, **+212,522656R / 480 CLOSED / 1 OPEN / 20 из 24 / DD 12,628056R**. **1 867 799 historical indicator fields PASS**, 0 расхождений.
- CONTROL → W1 → W2 → W3 → W4 с отдельными Git seals до следующего чтения. Expanding replay от канонического начала реконструирует непрерывное состояние без FLAT-reset; старые indicator prefixes exact, settled журналы и Stop/S1/extreme/initial R carry PASS. Quarterly entry cohorts и inherited IDs раскрыты отдельно; плохой квартал не исключён.
- **Свежий независимый stdlib/scalar replay + отдельная arithmetic/selection/recovery/presentation проверка:** **18 772 861 fields**, **556 804 Markdown cells**, 0 расхождений; max delta **1,76215e−12**, tolerance 1e−8. Первичный engine/metrics не импортируются. Независимость вычислительная, автор один; внешнее человеческое ревью PENDING. Supplemental accounting/carry cross-footing **1 109 checks PASS**.
- **Два свежих полных побайтных повтора PASS:** каждый CONTROL + W1–W4 + свежий auditor; все **216 result/audit файлов** каждого запуска direct bytes AND SHA256 совпадают с сохранённым первым запуском. Ещё **8 reporting-disclosure файлов** каждого повтора также идентичны. Sealed квартальные файлы не заменялись.
- Safe readers — отдельные unbuffered FileIO tokenizers, completion **строго < cutoff** до OHLCV suffix. На будущем годе только четырёхбайтовый YEAR sentinel, без декодирования timestamp/цен/объёмов 2026. Runtime raw-open allowlist, byte counters, poisoned suffix/read-spy tests и independent prefix SHA256; full source hash/`hash-object` не выполняются. Системный syscall trace отдельно не выполнялся. Data pin **f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8**. Проверены 48 разрешённых instrument-month; source coverage не выдаётся за независимую сертификацию биржевого календаря.
- **4 091 protected SHA256 files**, весь pre-existing Git tree, ROADMAP, TradingSystemLab/робот, прежние исследования и original checkout неизменны; diff исключительно в `IntradayLab/t3_m15_a6_s1_walk_forward_2025_v1/`. Raw market data read-only, закрытый suffix не хешируется и не исследуется. `git diff --check` PASS.

[Русское итоговое ревью](https://github.com/alkospacer123/market-pattern-discovery/blob/research/t3-m15-a6-s1-walk-forward-2025-v1/IntradayLab/t3_m15_a6_s1_walk_forward_2025_v1/REVIEW_MEMO_RU.md) · [Полный отчёт](https://github.com/alkospacer123/market-pattern-discovery/blob/research/t3-m15-a6-s1-walk-forward-2025-v1/IntradayLab/t3_m15_a6_s1_walk_forward_2025_v1/results/W4/REPORT_RU.md) · [Все таблицы](https://github.com/alkospacer123/market-pattern-discovery/blob/research/t3-m15-a6-s1-walk-forward-2025-v1/IntradayLab/t3_m15_a6_s1_walk_forward_2025_v1/results/W4/DETAILS.md) · [Артефакты и воспроизведение](https://github.com/alkospacer123/market-pattern-discovery/tree/research/t3-m15-a6-s1-walk-forward-2025-v1/IntradayLab/t3_m15_a6_s1_walk_forward_2025_v1)

**Один Draft PR. NO MERGE / NO AUTO-MERGE. STOP для независимого аудита и решения пользователя. TRUE OOS 2026, LIVE и брокерские операции не выполнялись.**

**DEVELOPMENT_2023_2024_EXPOSED / WF_2025_AUTHORIZED / TRUE_OOS_2026_LOCKED / GROSS_ONLY / COSTS_DEFERRED / NOT_LIVE_READY.**
