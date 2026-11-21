> **Дополнение 22.11.2026 (только Draft-кандидат):** этот файл фиксирует состояние `main` **до** удаления. Полный целостный комплекс, кроме `audit_only/`, предложен к выведению из рабочей ветки: 234 исходных Git blob (233 удаления + 1 архивный указатель `research_domains.md`), сохранённые в `archive/pre-root-legacy-20261122` на `09bca5641cb5bb367e84505ebfc6f8c7f35e2620`. Текущий `main` не изменён этим Draft. Проверки влияния на H1/M15/TRL/CI и независимых исторических воспроизведений не завершены: **MERGE BLOCKED**. См. [текущий gate](R7_ROOT_LEGACY_EXTRACTION_GATE_2026-11-22.md).

# R7 — что делать со старой корневой платформой (21.11.2026)
 
**Объект:** только пути на корне `market-pattern-discovery/main`, а не `TradingResearchLab/research`, `ControlCenter/docs` или `V20_TradingSystem_M15`. Срез исходного main `e52dd90ef3e85c6ccc3b075f934df3ea8f5ffa8d` после #583/#584, GitHub recursive tree `truncated=false`.

**Решение:** эти материалы **не являются текущими операционными исходниками трёх проектов V20/CC/TRL**, но составляют взаимосвязанную старую научно-исследовательскую платформу и уникальные доказательства. `KEEP_AS_HISTORICAL / NOT_ISSUED_FOR_LIVE` до доказательного переноса; возраст файлов сам по себе не разрешает удаление.

## 1. Точная классификация по исходному дереву

| Путь | Файлов | Реальная роль по прочитанным источникам | Решение |
| --- | ---: | --- | --- |
| `docs/` | 34 | Паспорта старых Phase 4/6/7 Market Pattern Discovery, autonomous engine, многогоризонтный research, forensic smoke. Это **не** актуальные операционные `ControlCenter/docs` | HISTORICAL_DOCS, переносить только со ссылками и provenance |
| `research/` | 4 | Предрегистрация `EXP-000001.json` и описание иммутабельных исторических кандидатов/гипотез | HISTORICAL_SOURCE, **не удалять** уникальный EXP |
| `schemas/` | 6 | JSON Schema прежних `discovery_effect_record`, `known_hypothesis`, Phase 6A; контракт старого `src/` | HISTORICAL_RUNTIME_DEP, пока оставить |
| `scripts/` | 7 | Сценарии `run_autonomous_research.py`, `run_cycle37.py`, `run_multihorizon_research.py`, `run_pattern_synthesis.py`, `run_phase6b.py`, `validate_phase1b.py`, `build_unknown_universe_index.py` — используют `market_pattern_discovery.*` | HISTORICAL_CLI_DEP; **не запускать** как V20/TRL, не удалить отдельно от исходников |
| `src/market_pattern_discovery/` | 86 | Реализация прежнего discovery/research/backtest/validation и автономных циклов | HISTORICAL_CORE, пока оставить |
| `tests/` | 50 | Старые тесты Phase 1–7, autonomous/pattern/backtest; не совпадают с V20/CC/TRL tests | HISTORICAL_TESTS, пока оставить |
| `config/` | 17 | Параметры старого pipeline, включая четыре двоичных `.u32` и `unknown_universe_v1/manifest.json` | HISTORICAL_DATA_DEP, нельзя терять проверяемый оригинал |
| `results/` | 17 | Сводки старого `cycle37`, `phase6b` и образцы сделок | HISTORICAL_EVIDENCE, сохранить |
| `evidence/` | 5 | Временные/causal alignment evidence старой системы | HISTORICAL_EVIDENCE |
| `audit_only/` | 16 | Единый `stop_tick_grid_20261012` пакет; сам оригинал всё ещё в main; его 16-файловая копия пока только в **Draft** архивного PR #5 | HISTORICAL_AUDIT, не уничтожать без проверки архива |
| `pyproject.toml` | 1 | `pythonpath=[src,.]`, `testpaths=[tests]`, entrypoints `market_pattern_discovery.validation.*`; принадлежит старой платформе | **KEEP UNTIL PACKAGING/CI MIGRATION**, иначе сломаются старые воспроизводимые команды |

## 2. Старые документы прямо в корне

| Оригинал с Git blob SHA | Что доказывает | Статус |
| --- | --- | --- |
| `ARTIFACT_HANDOFF_VERIFICATION_REPORT.md` — `f26dd57d7b0565c23a4dc932fb0618392f3a5e90` | Синтетическая передача JSONL между процессами `/workspace` от 11.09.2026, **не** Recovery V20 | HISTORICAL_REPORT |
| `CURRENT_ARTIFACT_STORAGE_STATUS.md` — `4ac9d7d33f9508b80cbfc73ca1596dd3957b1490` | Датированная проверка отсутствия старых bundles и затем формат хранения | HISTORICAL_REPORT |
| `PERMANENT_MEMORY_DIAGNOSTIC_REPORT.md` — `22edfaa73b113d1c7599b4c460ddf99ccc782502` | Диагностика старого autonomous-run storage, не память GPT/Kimi | HISTORICAL_REPORT |
| `PERSISTENT_MEMORY_VERIFICATION_REPORT.md` — `69133200da4beedca7612bd6aa54edb3a2049f6b` | Синтетический persistence-test, не backup/restore трёх проектов | HISTORICAL_REPORT |
| `SMOKE_RUN_V2_REPORT.md` — `e3886eb955151d7842669c642333fcfd3a420354` | Пять старых discovery циклов, датированный bundle, старый 2025 OOS; не торговый LIVE V20 | HISTORICAL_REPORT |
| `SMOKE_RUN_V3_REPORT.md` — `9bc70e8af8f6423935a56e71da4d0fe2f42a25a0` | Пять циклов autonomous multi-horizon, старый `/workspace`, не TRL текущий план | HISTORICAL_REPORT |
| `research_domains.md` — baseline blob `3b957c8c5c02e09ad2b85643d8c5947b7f4a0fe7` | Старые две области: H1 и BBW, с historical 2025 locked OOS. После #583 `BBW/` удалён из main; ссылка на исторический README должна указывать на сохранённый Git commit | HISTORICAL_CONTRACT |
| `ROADMAP.md` | Старый H1 Phase 7 Roadmap был ошибочно помещён в корень; замена общей дорожной картой подготовлена в этом PR | CURRENT_NAV_REPLACEMENT |
| `AGENTS.md`, `README.md` | Старые главные инструкции/однофайловая заглушка после #584; замена на общую V20/CC/TRL иерархию подготовлена в этом PR | CURRENT_NAV_REPLACEMENT |

**Важное различие:** проверка в 9 выбранных исходниках V20/CC/TRL и 4 GitHub workflows не выявила явных ссылок на перечисленные legacy scripts/schemas/reports. Это **не исчерпывающий dependency closure**; динамические ссылки, иные исторические модули, `pyproject`, тесты, архивные PR и внешние файлы ещё не проверены полностью.

## 3. Предлагаемое структурное решение (пока НЕ выполнено)

1. **Оставить активными и ясно документированными:** корневой README/AGENTS/Roadmap, три проекта, `recovery`, нужные H1/M15 с сохранением полного дерева, проверенные GitHub workflows.
2. **Единый legacy-комплекс:** после полного reverse-reference scan, настоящего архивного/побайтового checkpoint и offline-parity подготовить **один согласованный move/rename PR** для прежнего `Market Pattern Discovery`, включая `docs/research/schemas/scripts/src/tests/config/results/evidence/audit_only` и шесть отчётов. Возможный адрес `legacy/market-pattern-discovery/` — только проект, не утверждённый путь. Правила packaging, `pyproject`, scripts entrypoints, импорты, ссылки, CI и старая воспроизводимость должны быть адаптированы вместе. Никогда не переносить лишь `src` или `schemas` по отдельности.
3. Если полный перенос не доказан безопасным — **оставить текущие файлы на месте**, но маркировать исторической областью в текущих паспортных документах и для Kimi.
4. **Удаление**, в отличие от переноса, лишь при проверенном отсутствии уникального материала и зависимостей, SHA/приватности, достаточного архива и отдельного разрешения владельца. Не публиковать неизвестные данные в публичный `market-pattern-archive` без privacy review.

**Итог:** `ROOT_LEGACY_TRIAGE=PARTIAL_SOURCE_VERIFIED`, `ROOT_BULK_DELETE_GATE=BLOCKED`, `ACTIVE_V20_CC_TRL_RUNTIME_MODIFIED=NO`. Инструкция для Kimi: не запускать этот код как четвёртую систему и не объявлять его исторические тесты LIVE.
