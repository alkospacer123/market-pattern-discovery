# Kimi knowledge project — Trading Research Lab

**Решение владельца 26.11.2026:** новые расчёты TRL — только C1 (1 тик на каждую сторону); C2/C4 и иные повышенные модельные расходы не рассчитывать. Frozen исторические протоколы сохранять и воспроизводить без изменения; Evolution учитывает реальные комиссии/исполнения по факту. Отдельная программа: по одному исследованию стратегии каждого направления TREND, MOMENTUM, VOLATILITY, по опыту V20, со свободным выбором идей, методов и порядка тестирования, без обязательной цепочки этапов, TRAIN-разделения или TRUE OOS для каждого исследования; критерий каждой стратегии — (net PF ≥ 1,7 и средняя частота 1–2 закрытые сделки в торговый день по всей вселенной, включая нулевые дни) либо чистая годовая доходность ≥ 80% на весь выделенный капитал при приемлемом риске. Это цели отбора, не гарантии; при недостижении REJECT/CONTINUE/HOLD_DATA, без подгонки. M15 и N4 основные, другие TF/инструменты по обоснованию; сопоставимый исследовательский банк 45 000 ₽ на стратегию, риск 1,5% на сделку, cap 6% на счёт, учёт ГО, целых лотов, капитала и DD. ZERO LOOK-AHEAD с первого теста, Robustness только перспективным кандидатам, Walk-Forward перспективным кандидатам при достаточной истории. Изученная история не TRUE OOS. Независимая проверка GPT↔Kimi перед принятием кандидата. Не квота ежемесячного обзора и не экзамен; запуск исследования отдельно, без LIVE.

Ниже датированные сведения и старые blob references, не текущие pins. Актуальные документы разрешать по MAIN. G0–G6 и A приняты в документированном объёме; старые экзамены не повторять; очередь — ROADMAP.md.

**SOURCE SHA REFRESH 23.11.2026:** TRL Start Here и binary manifest Git blobs ниже сверены по `main@1413273a1a312802a0ced7a06a4eb73f050d2ec3`. Исторический pinned base остаётся свидетельством старого среза; исходные бинарные ZIP/XLSX/OHLCV через GitHub не доказаны.


> **SOURCE AUTHORITY CHECK 22.11.2026:** последние принятые GitHub-документы после [Merge #589](https://github.com/alkospacer123/market-pattern-discovery/pull/589) зафиксированы на контрольном `main=41d0b48c1d33db29bc1b19497d558748b3db8fb4`. Указанный ниже `bb8c46c1...` — **воспроизводимый исходный base до #589**, а не всегда актуальный HEAD. Перед чтением и практическим экзаменом перепроверять `main`, Git blobs и [иерархию документов](../DOCUMENTATION_AUTHORITY_2026-11-22.md). Никаких Kimi Chat/Code access, установленного LIVE, FINAM или cold restore не подтверждено.

**PINNED SOURCE:** GitHub main `bb8c46c1db89ca2b5311f22c755bb4e51ce8f7d6`. Research only; original ZIP/XLSX/OHLCV bytes not fully verified in this GitHub.

Читать: [AGENTS](../../TradingResearchLab/AGENTS.md) blob `65c585b1e34015882b66aef393947e4541844c13` → [паспорт TRL](../PROJECT_PASSPORT_TRL.md) blob `0420ec83a8328ce625c2d699062ef9ec75018e43` → [TRL Start Here](../../TradingResearchLab/reports/TRL-NOV-2026-KIMI-START-HERE.md) blob `20de0d0f5e8ad56323321de931265e4e57e61278` → [November Closeout](../../TradingResearchLab/reports/TRL-NOV-2026-FINAL-CLOSEOUT.md) blob `ec06839fd233f9909eead53e82b9b7d1d7868fb8` → [binary manifest](../../TradingResearchLab/reports/TRL-NOV-2026-ARTIFACT-MANIFEST.md) blob `725da79a35484a7385a8f9b98c3d7c59bc4e19e3`.

Research → Evolution → Journal. Итоговое решение владельца 60/30/45 + TP6 + Protect3 + HOLD5, EXT2 OFF; исторический лидер 75/30/30 по Net/PF в R097/R098 **не стал автоматически выбранной сборкой**. История 2018–2026 многократно исследована, 2025 не untouched TRUE OOS, но ретроспективный анализ 2025 разрешён.

Исходные R060/R097 ZIP, XLSX, калькуляторы и OHLCV могут отсутствовать в GitHub; SHA256 в манифесте — не подтверждение наличия исходных байтов. Не имитировать replay. Сохранять отрицательные результаты и ограничения GO/ликвидности, избегать подгонки и lookahead.

Экзамен: самостоятельно объяснить R086→R089→R097→R098→closeout, сослаться на исходники и проверить SHA; перечислить все недоступные бинарные оригиналы; предложить одну ограниченную offline гипотезу на декабрь с preregistered criteria, costs и без LIVE. [Исторические H1/M15](../RETAINED_RESEARCH_CLASSIFICATION_2026-11-22.md) — reference only.

## Critical Operations Contract

Перед критической TRL-задачей прочитай [контракт](../CRITICAL_OPERATIONS_CONTRACT.md), затем применяй `trl-repro-review` и `github-source-audit`; при передаче добавь `ai-engineering-handoff`. По `COC-TRL-*` проверяй frozen protocol, причинность, фактические bytes, contamination и ledger/witness parity. `REPRODUCIBLE_VERIFIED` не расширяй на недоступный оригинальный R097 engine, INSTALLED или LIVE. Canonical Markdown fallback не называть установленным Skill.
