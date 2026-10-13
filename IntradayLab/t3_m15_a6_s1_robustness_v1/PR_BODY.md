Фиксированная Robustness неизменного **A6+S1 / T3 M15 / NEXT_OPEN / TRAIL_375** даёт **MIXED**: историческое преимущество сохраняется в портфельных сценариях, но регулярность и устойчивость слабых частей неоднородны. Новая оптимизация и sensitivity replay с изменёнными торговыми правилами не выполнялись.

**2023–2024 DEVELOPMENT_EXPOSED. GROSS_ONLY / COSTS_DEFERRED / NOT_LIVE_READY.**

- USDRUBF даёт **73,608559% R2023**; без него PF2023 **1,524816**, +23,855401R, **6/12** положительных месяцев против9/12. Все четыре leave-one-out сценария по обоим годам и полному периоду остаются положительными. Межинструментальных лимитов в эталонном исполнении нет; это условная сумма R без общего sizing/capital.
- Ноябрь2024 даёт **44,005603% R2024**; без него PF2024 **1,452043**, +68,387068R. Три лучших месяца дают около73–74% годового net R. Все месяцы сохраняются в первичных результатах.
- Без top10 ALL PF **1,565589**, +131,808371R, **17/24** положительных месяцев. Но **SHORT2024 без его top5**: PF **0,988208**, −0,954381R. Слабая сторона не исключается.
- **0,05R/CLOSED:** годовые PF **2,033245 / 1,636882**, полный R+188,522656R, **18/24**, DD14,936730R. **0,10R/CLOSED:** **1,876833 / 1,514730**, R+164,522656R, **16/24**, DD19,686730R. Оба уровня сохраняют положительный годовой/полный портфельный знак. Это абстрактные R-потери, **не FINAM, не C1, не реальные комиссии/slippage**.

Рекомендация — после ревью **отдельно решить вопрос о предусмотренном roadmap Walk Forward неизменного кандидата**. Текущее исследование не поддерживает новый архитектурный фильтр; исторический PF≥1,70 и20/24 не дают автоматический Robustness PASS. Exposed2024 нельзя назвать clean WF/OOS.

Верификация:

- Actual main после подтверждённого merge#508: **9b496d49e3ab8f71a843b24f9ccc288c9c5ff5bd**; PR#505–#508 merged. Прочитаны roadmap и замороженные источники, их четыре inventories PASS.
- Протокол/код/SPEC/tests/renderer/auditor/repeat заморожены и опубликованы **до исторических расчётов**: **eb4397a8256cd1164ac687c030cfbbf6e59540b3**. Frozen code после результатов неизменен. Engines/scalar/metrics — побайтные копии#506; все параметры и четыре инструмента сохранены.
- **Полный CONTROL PASS в обеих реализациях:** по **2 324 206 полей**,0 расхождений, все trade/Stop/signal/gap/terminal OPEN/period-end OPEN #505–#508 и published summary/monthly #505. PF2023/2024/ALL, +212,522656R,480 CLOSED/1 OPEN,20/24 и DD12,628056R воспроизведены.
- Все **98 305 M15 / 1 867 799 feature fields** совпали. **38 synthetic tests PASS**,12 959 causal rows PASS.
- Свежий независимый stdlib/dict/scalar replay и отдельный arithmetic accounting: **1 509 772 поля**,0 расхождений, max delta9,663e−13 при tolerance1e−8. Не импортирует primary engine/analysis/metrics. Автор один; внешнее человеческое ревью PENDING.
- **699 rows / 8046 cells** основных Markdown таблиц PASS. Заключение, evidence, DECISION и README дополнительно сверены: **3952 fields**,0 расхождений.
- **Два свежих полных побайтных повтора PASS:** все **60 result/audit файлов** каждого запуска совпали direct bytes AND SHA256;120+120 проверок. Первые bytes сохранены.
- Все новые CSV/JSON/MD, полные журналы и негативные ячейки — исключительно `IntradayLab/t3_m15_a6_s1_robustness_v1/`.420 protected files, ROADMAP, TradingSystemLab/робот, прежние исследования, original checkout и market data неизменны. Data pin **f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8**; timestamp-first без OHLC2025+, full hashes opaque bytes. Raw quotes не копируются.

[Русское заключение и четыре ответа](https://github.com/alkospacer123/market-pattern-discovery/blob/research/t3-m15-a6-s1-robustness-v1/IntradayLab/t3_m15_a6_s1_robustness_v1/CONCLUSIONS.md) · [Отчёт](https://github.com/alkospacer123/market-pattern-discovery/blob/research/t3-m15-a6-s1-robustness-v1/IntradayLab/t3_m15_a6_s1_robustness_v1/results/REPORT.md) · [Артефакты и воспроизведение](https://github.com/alkospacer123/market-pattern-discovery/tree/research/t3-m15-a6-s1-robustness-v1/IntradayLab/t3_m15_a6_s1_robustness_v1)

**Один Draft PR. NO MERGE / NO AUTO-MERGE. STOP для проверки.** Walk Forward, TRUE OOS, LIVE и дальнейшие архитектурные исследования не выполнялись.
