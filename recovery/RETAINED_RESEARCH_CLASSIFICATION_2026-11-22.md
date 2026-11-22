> **FINAL R7 STATUS 22.11.2026:** #587 MERGED `8a1c6618f8d3c9f33de9de6cb3f6efae13fe29f0`, #588 MERGED `bb8c46c1db89ca2b5311f22c755bb4e51ce8f7d6`; #580/#581 CLOSED WITHOUT MERGE, обе исходные ветки сохранены. **[PR #590](https://github.com/alkospacer123/market-pattern-discovery/pull/590) попытался удалить 16 файлов audit_only, однако CI [FAIL](https://github.com/alkospacer123/market-pattern-discovery/actions/runs/44998434881) обнаружил ДВЕ прямые H1 offline research/test зависимости; PR закрыт без Merge.** Каталог оставлен в `main` по доказательной необходимости, [акт этапа I](R7_STAGE_I_FINAL_ACCEPTANCE_20261122.md). Исторические заметки ниже (включая «ещё не merged») относятся к прежнему срезу, а не к фактическому состоянию GitHub.

# R7 — классификация сохранённых исследований и audit_only

**GitHub-срез 22.11.2026:** `market-pattern-discovery/main=4f118ee1cdeced15406136401faabe4fdc3bb847`. Проверены рекурсивные Git trees пяти проектных корней и audit_only: `truncated=false`. Это **не** проверка физической Intel/LIVE установки, не повторный research replay и не право на новое удаление.

## Правило Kimi / GPT

**ACTIVE** — V20 и Control Center; **DEPENDENCY** — нужные им H1/M15 библиотеки; **RESEARCH** — TRL и первичные исторические результаты; **HISTORICAL_PROVENANCE** — датированные исследования и аудиты, а не новые инструкции; **ARCHIVE_PINNED** — исходники доступны в защищённой Git-истории, но это не автономный Recovery; **UNKNOWN** — непроверенные внешние потребители, источники ZIP/XLSX и физический broker state.

| Область | Файлов Git | Неизменный Git tree SHA | Решение |
| --- | ---: | --- | --- |
| `V20_TradingSystem_M15/` | 446 | `08e4b1ff98f8599f662ee8724c2d11cea03d85d3` | **ACTIVE + provenance** V20-02–08, v20_runtime, research_original_v20 |
| `ControlCenter/` | 163 | `8052938c83a27b2367309052d455d74d9341df09` | **ACTIVE**, операторский код, тесты и процедуры |
| `TradingResearchLab/` | 169 | `a5764c5e693f43cbb09469badf26c8dbe3fd3fa9` | **RESEARCH**: research (45), evolution (40), journal (56), reports (23), 5 корневых файлов |
| `TradingSystemLab/` | 3 059 | `08722b448d9b14201284e4dab83693e960a290b2` | **DEPENDENCY + H1 HISTORY**: stage8_robot (252), tests (94), results (2 508) |
| `IntradayLab/` | 2 722 | `d6b686bcdcbd54eca9d1d25c160fecd5bfd82407` | **DEPENDENCY + M15 HISTORY**: core (14), optimization_registry (20), results (490), 22 t3_m15_* комплексов (1 979) |
| `audit_only/` | 16 | `6c7a68b7b51b2d272bd66734835cbece3a25d2b9` | **HISTORICAL_PROVENANCE**: единственный STOP/TICK GRID аудит H1 |

H1 `TradingSystemLab.stage8_robot` и M15 `IntradayLab.core` импортируются действующим V20; из факта их использования **не** следует, что все 2 508/1 979 старых результатов исполняются ежедневно. Однако исследования, замороженные тесты, отрицательные результаты и история независимого replay сохраняют доказательную ценность. Никаких массовых удалений H1/M15 **не разрешено**.

## M15 — что именно даёт 1 979 исторических файлов

Рекурсивный Git tree `d6b686bcdcbd54eca9d1d25c160fecd5bfd82407` содержит **1 681 645 810 байт** Git blobs в `IntradayLab/` — это размер исходных Git файлов, а не размер установленного SSD. Ниже все 22 каталога `t3_m15_*`:

| Исторический каталог под `IntradayLab/` | Файлов |
| --- | ---: |
| `t3_m15_a6_s1_entry_quality_v1/` | 90 |
| `t3_m15_a6_s1_robustness_v1/` | 103 |
| `t3_m15_a6_s1_trail_optimization_v1/` | 100 |
| `t3_m15_a6_s1_trail_plateau_v2/` | 98 |
| `t3_m15_a6_s1_true_oos_2026_readiness_v1/` | 2 |
| `t3_m15_a6_s1_true_oos_2026_ytd_v1/` | 81 |
| `t3_m15_a6_s1_walk_forward_2025_v1/` | 291 |
| `t3_m15_a6_s1_walk_forward_design_v1/` | 6 |
| `t3_m15_build_comparison_2023_2026_v1/` | 403 |
| `t3_m15_combined_v1/` | 76 |
| `t3_m15_early_risk_protection_v1/` | 128 |
| `t3_m15_entry_regime_v1/` | 48 |
| `t3_m15_execution_sensitivity_v1/` | 72 |
| `t3_m15_forever_v1/` | 29 |
| `t3_m15_full_n4_catalog_v1/` | 19 |
| `t3_m15_holding_diagnostics_v1/` | 37 |
| `t3_m15_initial_stop_v1/` | 63 |
| `t3_m15_month_diagnostics_v1/` | 57 |
| `t3_m15_session_entry_v1/` | 60 |
| `t3_m15_stop_exit_v1/` | 64 |
| `t3_m15_t1_entry_retest_v1/` | 57 |
| `t3_m15_t1_s1_v1/` | 95 |
| **Всего** | **1 979** |

Эти каталоги — **HISTORICAL_PROVENANCE / RESEARCH**, а не 22 новых торговых робота. Не загружать весь массив в Kimi как «актуальный проект»; использовать паспорт M15 и выборочную проверку исходного SHA, данных и тестов по исследовательскому запросу. `market-pattern-data` — отдельный репозиторий с исходными данными; полнота локальных оригиналов и ZIP/XLSX здесь не доказана.

## audit_only/stop_tick_grid_20261012 — техническая приёмка

- Источник: [PR #492 (MERGED)](https://github.com/alkospacer123/market-pattern-discovery/pull/492), [исходный отчёт](../audit_only/stop_tick_grid_20261012/REPORT_RU.md), [README](../audit_only/stop_tick_grid_20261012/README.md), [verification.json](../audit_only/stop_tick_grid_20261012/verification.json).
- Ровно **16 файлов**. Git tree `1a184db9d4d856948611442262635573a6699d10`: все **16/16 file path + blob SHA** совпали в текущем `main` и `archive/pre-root-legacy-20261122@09bca5641cb5bb367e84505ebfc6f8c7f35e2620` (защищённый архивный ref).
- Датированный 12.10.2026 результат H1: **1 422/1 422** исторических raw continuous signals с stop off tick-grid; **418/418** frozen TRAIL1 trades research replay PASS; `LIVE_EXECUTION_CONFORMANCE=FAIL` на исследованном старом исполнителе; `PRODUCTION_CHANGES=NONE`. Это **не статус текущей V20 или Intel**.
- После аудита [PR #493 (MERGED)](https://github.com/alkospacer123/market-pattern-discovery/pull/493) добавил код candidate STOP/TICK GRID V2 в H1; GitHub merge **не** доказывает physical LIVE deploy/fills/SLTP.
- Исторический `run_existing_tests.py` ссылается на `tests/test_trail1_authoritative_ledger.py`, **отсутствующий в текущем `main`** после #586, но существующий в защищённом архивном SHA. Для оригинального test replay нужен *архивный изолированный checkout* и frozen data; считать нынешний audit runner полностью запускаемым нельзя.
- Изменение `audit_only` ранее запрещалось immutable scope gate #586 вместе с пятью другими защищёнными поддеревьями. Полная проверка сторонних, динамических и внешних consumers **не проведена**; отсутствие прямого импорта в роботе не является доказательством отсутствия всех dependencies.
- **Финальный вердикт: `KEEP_IN_MAIN_AS_H1_OFFLINE_RESEARCH_DEPENDENCY`.** В обычной работе Kimi не запускает этот код и не принимает старую диагностику за оперативное состояние. Перенос целиком в архив можно рассмотреть позже одним консолидированным cleanup-пакетом, только после доказанного dependency gate, фиксации исходных SHA и явного разрешения владельца.

### Подтверждённые потребители audit_only после gate #590

- `TradingSystemLab/stage8_robot/signal_execution_diagnostic.py` (Git blob `33f20607c828223d426718768ff3f4669dd31956`): `diagnose()` открывает `full_available_raw_signals.csv` из этой папки.
- `TradingSystemLab/stage8_robot/tests/replay_stop_tick_grid.py` (Git blob `23889f765919866357cf034a7c725fab81f4c840`): импортирует архивный `audit.py` и читает `lifecycle_admitted_entries.csv` / `full_available_raw_signals.csv`.
- Подтверждено [CI FAIL #590](https://github.com/alkospacer123/market-pattern-discovery/actions/runs/44998434881); сохранность в Git архиве не обеспечивает работу этих относительных путей в сегодняшнем checkout. **Сохранять 16/16 файлов без правок H1 и audit_only**. Это не утверждение об актуальном V20 LIVE.

## Что уже действительно выведено из рабочего дерева

- Merge [#583](https://github.com/alkospacer123/market-pattern-discovery/pull/583) вывел 11 594 проверенных исторических A/B/C и BBW paths.
- Merge [#586](https://github.com/alkospacer123/market-pattern-discovery/pull/586) вывел 233 файла старой самостоятельной root Market Pattern Discovery. Исходники доступны в `archive/pre-root-legacy-20261122@09bca5641cb5bb367e84505ebfc6f8c7f35e2620`. Исторический тест этой платформы — **45 PASS / 1 known FAIL**, сохранён, не подавлен.
- Старые Draft PR #580/#581 и исследования #557–#564 **не автоматически потеряны**, даже если их содержимого нет в текущем `main`. [Исторический реестр решений](R0_HISTORICAL_RESEARCH_DECISIONS_2026-11-20.md) содержит исходные Git blob SHA/PR и отрицательные результаты. Уникальные материалы из #580/#581 частично перенесены в **ещё не merged** #587/#588; старые ветки не удалять до приёмки.
- `market-pattern-archive` — неполный вспомогательный архив, не главный рабочий репозиторий и **не** доказанный Disaster Recovery.

## Следующая безопасная последовательность

1. Принять документы и исходные инструменты из #587/#588 после exact-HEAD проверки и отдельного разрешения; закончить review старых Draft, не смешивать устаревшие инструкции с действующими.
2. Создать три **логических** Kimi knowledge project V20 / Control Center / TRL из одного `main`; первыми читать `README.md`, `AGENTS.md`, свой паспорт, затем pinned code/tests. H1/M15 — запросные зависимости и исследования, не четвёртый проект.
3. Kimi Chat **и отдельно Kimi Code**: проверить доступ, SHA, воспроизведение кода, безопасность, практический экзамен и GPT↔Kimi handoff. До проверки `NOT_EXAMINED`.
4. **После Kimi** — независимый backup и реальный cold restore без Intel, главного SSD, GitHub и двух ИИ. Не считать Git history или CI заменой этого испытания.

**LIVE:** GitHub-ревизия не трогала FINAM, Windows Tasks, установленные Python, SLTP, позиции, токены или SQLite. Их актуальный статус = UNKNOWN.
