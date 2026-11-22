# Trading Systems — матрица действующей и исторической документации

**Аудит 22.11.2026, GitHub контрольный commit:** `41d0b48c1d33db29bc1b19497d558748b3db8fb4`. Это зафиксированный срез *до* документационного PR. При изменении `main` заново сверять `git rev-parse HEAD` и нужные Git blob SHA. **Аудит проверяет GitHub Markdown, а не Intel/LIVE и не full cold restore**.

## 1. Правило приоритета (GPT, Kimi Chat, Kimi Code)

1. [Корневой AGENTS](../AGENTS.md): общие методы, полномочия, LIVE-безопасность, ZERO LOOK-AHEAD.
2. [Корневой README](../README.md) → [Roadmap](../ROADMAP.md) → [текущий GitHub snapshot](REPOSITORY_CURRENT_STATE.md): цели и фактически завершённые PR.
3. **Выбранный один из трёх паспортов:** [V20](PROJECT_PASSPORT_V20.md), [Control Center](PROJECT_PASSPORT_CONTROL_CENTER.md), [TRL](PROJECT_PASSPORT_TRL.md), затем соответствующие инструкции проекта.
4. [Kimi Phase II](kimi/README.md) и независимый [экзамен Kimi Code](kimi/EXAM_AND_HANDOFF.md). **Kimi Chat не является Kimi Code**.
5. **Исторические snapshots, отрицательные исследования, старые PR, CI:** использовать только как датированные свидетельства со своим commit/blob SHA, не как инструкции для нынешней торговли.

**MAIN** — исходники в GitHub; **INSTALLED** — физический файл на Intel; **LIVE** — свежая независимая сверка Task/FINAM/positions/orders/SLTP; **RESEARCH** — исторический тест; **ARCHIVE** — pinned Git/source/binary. Нет новой проверки — `UNKNOWN`.

## 2. Паспорт → действующий первоисточник

| Проект / статус | Канонический документ | Приоритетная оперативная/исследовательская ссылка | Защита от неправильного чтения |
| --- | --- | --- | --- |
| **V20 ACTIVE source** | [V20 паспорт](PROJECT_PASSPORT_V20.md) | [V20 R088 release](../V20_TradingSystem_M15/V20-08/LIVE_RELEASE_R088_20261120_RU.md), [V20 AGENTS](../V20_TradingSystem_M15/AGENTS.md) | Утверждено 60/30/45, TP6, Protect3, HOLD5, EXT2 OFF, **MAIN ≠ INSTALLED ≠ LIVE** |
| **Control Center ACTIVE source** | [CC паспорт](PROJECT_PASSPORT_CONTROL_CENTER.md) | [CC-08 Operations](../ControlCenter/docs/V20_CC08_OPERATIONS.md), [CC README](../ControlCenter/README.md) | Старое CC-03/H1, 8501, disabled controls и Draft #568 из датированного текста не являются нынешней V20-панелью |
| **TRL RESEARCH** | [TRL паспорт](PROJECT_PASSPORT_TRL.md) | [TRL November Closeout](../TradingResearchLab/reports/TRL-NOV-2026-FINAL-CLOSEOUT.md), [Start Here](../TradingResearchLab/reports/TRL-NOV-2026-KIMI-START-HERE.md) | 75/30/30 — исторический Net/PF лидер, но выбор владельца 60/30/45; 2025 не untouched TRUE OOS |
| **H1 historical + dependency** | [retained-source map](RETAINED_RESEARCH_CLASSIFICATION_2026-11-22.md) | [TradingSystemLab README](../TradingSystemLab/README.md), [датированный CURRENT_STATE](../TradingSystemLab/CURRENT_STATE.md) | H1 ARMED / Task snapshot от октября **не** нынешнее разрешение; V20 нужны H1 `stage8_robot` модули |
| **M15 historical + dependency** | [retained-source map](RETAINED_RESEARCH_CLASSIFICATION_2026-11-22.md) | [IntradayLab README](../IntradayLab/README.md), [датированный ROADMAP](../IntradayLab/ROADMAP.md) | T3/M15 standalone candidate не V20, не новый LIVE; V20 нужен `IntradayLab.core` |
| **H1 audit original** | [R7 final acceptance](R7_STAGE_I_FINAL_ACCEPTANCE_20261122.md) | [STOP/TICK GRID original](../audit_only/stop_tick_grid_20261012/README.md) | 16 файлов оставлены из-за двух доказанных H1 research/replay imports; не четвёртый проект |
| **Final Recovery (future)** | [Recovery guide](RECOVERY_GUIDE.md) | [Maintenance](MAINTENANCE.md) | ZIP/SSD hash или Git mirror ≠ COLD_RESTORE_PASS; только в самом конце |

## 3. Датированные документы — не исправлять исходную историю

- `V20_TradingSystem_M15/docs/PROJECT_SPEC_RU.md` — **ранняя проектная спецификация**: планы 3×500 тысяч, ранний TIME3 / отдельный repo и `C:\V20Lab` как будущий путь **не отражают актуальное решение R088**. Проверять установленное по отдельным свидетельствам, не исправлять замороженный документ задним числом.
- `ControlCenter/README.md` — главный верхний блок датирован **20.11**, содержит устаревшую строку `#568 Draft`; GitHub API проверен: [#568 MERGED](https://github.com/alkospacer123/market-pattern-discovery/pull/568) (merge `66093575312010ea2ecd92b5cddef063f1340488`). Сейчас читать CC-08/паспорт, не исторический статус PR.
- `ControlCenter/docs/ROADMAP_STATUS.md` — отдельный historical CC-03/H1, не Roadmap панели V20/8502.
- `TradingSystemLab/CURRENT_STATE.md` — последний описанный в начале физический H1 checkpoint относится к **16.10** и не разрешает ARM, Task restart или real orders сегодня; H1 сохранён как legacy + shared dependency.
- `IntradayLab/ROADMAP.md` — историческая исследовательская хронология самостоятельного T3/M15, а не действующая дорожная карта трёх проектов.
- `recovery/PROJECT_INSTRUCTIONS_CURRENT_2026-11-20.md`, `recovery/PROJECT_ROADMAP_2026-11-20.md`, `recovery/HISTORICAL_DRAFT_REGISTER_2026-11-20.md`, `recovery/KIMI_R1_1_VERIFIED_SOURCE_INDEX_2026-11-20.md`, `recovery/KIMI_R1_2_V20_DEEP_DIVE_AND_EXAM_2026-11-20.md` и `recovery/R7_ROOT_LEGACY_EXTRACTION_GATE_2026-11-22.md` — **датированные R7/provenance источники**, даже когда написано CURRENT/DRAFT/NOT MERGED. Пользоваться первым делом этим индексом и текущим snapshot, не заменять исходные свидетельства.
- Более 900 остальных документов — преимущественно historical research, run results и замороженные stage notes. **Не заявлено**, что все они актуализированы вручную или что все их внешние и относительные ссылки были replay-tested.

## 4. Проверенный перечень и пределы аудита

- GitHub `main` содержит **956 Markdown/RST/TXT файлов** по Git tree (каталоги `recovery/`, исторические результаты H1/M15, V20/CC/TRL и старые исследования). Рекурсивный Git tree не усечён.
- **64 приоритетных Markdown-документа** из корневого слоя, паспортов, Kimi, recovery, project READMEs/Roadmaps: **336 относительных ссылок** сверены с Git tree, **0 отсутствующих целей**. Изолированные Markdown anchors, внешние URL и бинарный replay этой проверкой **не доказаны**.
- **11/11 точных Git blob SHA** для трёх паспортов, R088 release, V20 базового `finam_live.py`, workflow, CC README/CC-08, TRL Start Here/Closeout/manifest совпали с проверенным принятым HEAD. Это SOURCE parity, не installed или LIVE parity.
- Обнаружено и разъяснено устаревание `README` (`4f118...`), `ROADMAP` (#589 ещё не MERGED), `recovery/REPOSITORY_CURRENT_STATE` (`bb8c...` как latest), `ControlCenter/README` (исторический Draft #568). Никаких нетронутых исторических выводов задним числом не редактировать.
- Автономный backup и cold restore оставлены на этапе III. Исходные ZIP/XLSX и полнота OHLCV физически ещё не проверены для Kimi/Recovery. Без FINAM токенов, DPAPI, SQLite и приватных журналов в GitHub.

**Результат:** действующая точка входа, паспорта, SHA и безопасность могут быть согласованы на уровне GitHub; физическая среда и старая полная research history **не объявлены** проверенными.
