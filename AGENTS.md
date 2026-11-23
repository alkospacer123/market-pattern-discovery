# Trading Systems — действующий общий AGENTS для GPT/Codex и Kimi Code

**Проверенный контур этапа I, 22.11.2026, после Merge #589.** [Реестр действующих и исторических документов](recovery/DOCUMENTATION_AUTHORITY_2026-11-22.md) задаёт приоритет, а каждый указанный Git SHA — свидетельство своего датированного среза, не постоянный HEAD. Заменяет старый корневой Research safety contract как универсальную инструкцию. Исходный текст и старый Market Pattern Discovery остаются в Git history и исторических документах. Для проекта сначала прочитать [README](README.md), [срез](recovery/REPOSITORY_CURRENT_STATE.md), [паспорт V20](recovery/PROJECT_PASSPORT_V20.md) / [CC](recovery/PROJECT_PASSPORT_CONTROL_CENTER.md) / [TRL](recovery/PROJECT_PASSPORT_TRL.md).

## Области и приоритет

- `V20_TradingSystem_M15/` = ACTIVE торговое ядро; `ControlCenter/` = ACTIVE операторская панель; `TradingResearchLab/` = RESEARCH. `recovery/` = KNOWLEDGE / continuity.
- `TradingSystemLab/` = LEGACY H1 + **необходимая** библиотека `stage8_robot`; `IntradayLab/` = LEGACY M15 + **необходимая** библиотека `core`. H1/M15 нельзя автоматически запускать. Старая корневая автономная платформа `src/tests/docs/config/results` и её пакеты отсутствуют в данном очищенном дереве; их оригинал закреплён на Git SHA `09bca5641cb5bb367e84505ebfc6f8c7f35e2620` в защищённой ветке `archive/pre-root-legacy-20261122`. Удаление root legacy принято в `main` Merge #586 (`4f118ee1cdeced15406136401faabe4fdc3bb847`); заново проверять будущие изменения GitHub по SHA, а не по старой датированной документации. Отсутствие исполняемых прямых импортов **не означает полного доказательства всех внешних зависимостей**. `audit_only/stop_tick_grid_20261012` обязателен для H1 offline диагностик: `TradingSystemLab/stage8_robot/signal_execution_diagnostic.py` читает committed CSV, `TradingSystemLab/stage8_robot/tests/replay_stop_tick_grid.py` импортирует `audit.py` и CSV. Проверка удаления в [#590](https://github.com/alkospacer123/market-pattern-discovery/pull/590) **FAIL** и PR закрыт без Merge; см. [финальный акт R7](recovery/R7_STAGE_I_FINAL_ACCEPTANCE_20261122.md). Не удалять ради упрощения Kimi и не запускать H1 как LIVE. Проверять [карту](recovery/LEGACY_DEPENDENCIES_AND_RETENTION.md) и [gate](recovery/R7_ROOT_LEGACY_EXTRACTION_GATE_2026-11-22.md).
- При конфликте статуса: свежий проверенный источник и паспорт проекта важнее более раннего датированного среза, но нельзя объявить исторические файлы ложными или незаметно переписать историю. Всегда фиксировать SHA/дату/доказательные границы.

## Методология

- ZERO LOOK-AHEAD, доступность свечи только после полного закрытия, корректный causal MTF, определённые day/session границы, детерминизм, воспроизводимые costs/slippage/GO/ликвидность, запрет подгонки PF и повторной оптимизации на TRUE OOS.
- **НЕТ общего запрета на 2025.** V20 и TRL уже изучали 2018–2026, поэтому это research history, не untouched TRUE OOS. Старые H1/M15/Market Pattern Discovery имеют собственные frozen-сплиты только для воспроизведения соответствующих исторических экспериментов.
- M5-запрет из старого Research safety contract не отменяет M15-first V20. Индикация/сбросы и уровни риска — строго по замороженному проектному контракту, не по устаревшим корневым протоколам.

## Безопасность

- **Только оператор** разрешает Merge, PR-удаления, LIVE-установку, торговые действия, изменения risk/signal/FINAM, кошельков, Scheduled Tasks, HALT/ARM или rearm. Работа ИИ — read-only или offline до отдельного подтверждения.
- MAIN = принятое в Git; INSTALLED = физические файлы Intel; LIVE = свежая фактическая сверка Task/FINAM/SLTP; RESEARCH = история тестов; ARCHIVE = исходные исследования; RECON = восстановленный контекст. Отсутствует проверка — `UNKNOWN`, не PASS.
- Никогда не читать и не публиковать FINAM/DPAPI, идентификаторы счетов, секреты, приватные SQLite, личные журналы; не открывать реальные заявки для тестов. Не повторять broker POST с неизвестным результатом.
- Любая работа с кодом: отдельная ветка и PR, точные SHA/diff, offline tests, review, контроль секретов/приватности, доказательство неизменности LIVE. Не делать `git pull` в работающий каталог Intel.

## Kimi, архив и восстановление

- Три логических проекта Kimi Chat используют один MAIN с разными паспортами. Kimi Code — отдельная реальная code/GitHub интеграция, обязательны экзамен, отдельная ветка, peer review и handoff GPT↔Kimi.
- `market-pattern-archive` — опциональная вспомогательная публичная история, **не** обязательная зависимость V20/CC/TRL и **не** полный backup. Нельзя удалять до проверки полноты будущего Recovery; не делать туда массовую публикацию без privacy-аудита.
- Финальный Recovery вне Intel, основного SSD, GitHub и обеих ИИ с SHA, Git refs, PR/Issues/CI, оригиналами TRL, защищёнными конфигами и реальным cold restore — в конце.

**Количество старых файлов — не критерий мусора.** Для удаления нужны точный список, зависимость, сохранённый первоисточник/провананс, offline-тесты и отдельное разрешение. При UNKNOWN оставить.

## Kimi Code Windows workspace and access gate — 23.11.2026

The single *designated source checkout* for Kimi Code on Intel is `C:\KimiSandbox\market-pattern-discovery`; see [Windows workspace and phased access policy](recovery/kimi/WINDOWS_WORKSPACE_AND_ACCESS.md). This local directory is **not** an OS sandbox: any unreviewed runtime tests/dependency installation require approved separate execution (isolated VM or no-secret CI). The three Kimi projects may share GitHub knowledge but not LIVE permissions. The former external D: checkout is retired. After practical exams the operator may authorize scoped read-only access to non-secret production data, while deploy, FINAM actions, HALT/ARM, code writes in LIVE and unknown-result retries remain independently gated. Preserve `Always Ask` and equivalent approvals in Work; optional Computer Use/Browser Extension must not silently gain LIVE authority.
