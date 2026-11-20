# R7 — актуальный архив и первичная карта корневых зависимостей (read-only)

**Срез проверки:** 20.11.2026. **Контур:** MAIN + ARCHIVE, только GitHub read-only; **не** INSTALLED, LIVE, CI PASS или R6 restore. Этот документ фиксирует последующий факт, не переписывая исторические протоколы.

## 1. Точные состояния Git

| Репозиторий | Проверенный main | Доказательство |
|---|---|---|
| [market-pattern-discovery](https://github.com/alkospacer123/market-pattern-discovery) | `f15d565755b996252081ed49ed5a094ee1e8d820` | [docs-only PR #579](https://github.com/alkospacer123/market-pattern-discovery/pull/579), parent `aea99cd322085c6c9e87f74248a9eb7026447911` |
| [market-pattern-archive](https://github.com/alkospacer123/market-pattern-archive) | `8d4027c8d53625dfe7780cb7ccfdc354d51b25ba` | [архивный PR #4](https://github.com/alkospacer123/market-pattern-archive/pull/4), parent `1fd5f0b2118396651e42b3e591cb4a039a012b88` |

Архивные PR [#1](https://github.com/alkospacer123/market-pattern-archive/pull/1), [#2](https://github.com/alkospacer123/market-pattern-archive/pull/2), [#3](https://github.com/alkospacer123/market-pattern-archive/pull/3), [#4](https://github.com/alkospacer123/market-pattern-archive/pull/4) имеют `merged=true`. После #3 перенесены исходные файлы из #544/#561; после #4 — восемь исходных методов, manifest, correction и offline-test файлов из #557/#564.

**Результат собственной read-only проверки Git дерева:** `historical-prs/` архива содержит **19 blob-файлов** из 10 закрытых исторических PR, при этом из каждого PR есть минимум один исходный файл. Их SHA и происхождение перечислены в [манифестах архива](https://github.com/alkospacer123/market-pattern-archive/tree/main/catalog). В [реестре покрытия](https://github.com/alkospacer123/market-pattern-archive/blob/main/catalog/PR_SOURCE_COVERAGE_2026-11-20.md) — **425 записей изменённых файлов** в сумме по PR; **19** скопированных, **406** иных записей. **406 — не число уникальных недостающих файлов**; часть уже есть в MAIN, некоторые записи дублируют изменения. Полные 10 PR, их discussion/CI, бинарные данные, оригинальные ZIP/XLSX и независимый restore не архивированы полностью.

**Предупреждение об устаревших срезах:** README, `catalog/FOURTH_ARCHIVED_METHODS_PR557_PR564_2026-11-20.md` и `PR_SOURCE_COVERAGE_2026-11-20.md` архива были написаны до Merge #4 и внутри могут всё ещё говорить `STAGED_DRAFT`/`NOT_MERGED` или «после возможного Merge». Для определения фактического статуса приоритет имеют свежий main SHA и [merged PR #4](https://github.com/alkospacer123/market-pattern-archive/pull/4). Эти фразы в исторических манифестах не доказывают, что Merge не было.

## 2. Защищённые шесть каталогов

`V20_TradingSystem_M15/` ACTIVE, `ControlCenter/` ACTIVE, `TradingResearchLab/` RESEARCH, `recovery/` KNOWLEDGE; `TradingSystemLab/` и `IntradayLab/` — LEGACY **и одновременно необходимые V20 зависимости**. Правила: [Kimi repository boundaries](KIMI_REPOSITORY_BOUNDARIES_2026-11-20.md).

Прямые подтверждения в `main=f15d565...`:
- [V20 live base `finam_live.py`](../V20_TradingSystem_M15/v20_runtime/finam_live.py), blob `b80fb9eb135f7cdcb4c78337e2b808c4d7135195`: импортирует `TradingSystemLab.stage8_robot` (broker, safety, FINAM и т. д.). Это **Git base**, не установленный R088 + 9 патчей.
- [V20 offline `m15_runner.py`](../V20_TradingSystem_M15/v20_runtime/m15_runner.py), blob `41c17be3469fd371d0288db78914ecc492197464`: импортирует `IntradayLab.core` и `TradingSystemLab.stage8_robot`. OFFLINE runner не подтверждает LIVE.
- [V20 Windows workflow](../.github/workflows/v20-08-live-windows.yml), blob `889db248b943105dd598fbbe248d277a5e1b7e67`: выполняет офлайн-проверки по событиям и путям V20; это не проверка локальной установки и не брокерский PASS.

## 3. Другие корневые пути: никаких массовых удалений

| Корневой путь | Текущее наблюдение | Решение до глубокого dependency/offline gate |
|---|---|---|
| `src/`, `tests/` | [`pyproject.toml`](../pyproject.toml), blob `d1874cd67bece45bfdd0e060876a4f2cbcdeb187`, задаёт `pythonpath=["src","."]`, `testpaths=["tests"]`, package discovery `src` | **KEEP / LINKED_BY_PACKAGE_AND_TEST_CONFIG**, не считать мусором |
| `bbw_system/`, `BBW/`, `config/` | `pyproject.toml` определяет множество команд `bbw_system.*`; BBW-конфиги и исследовательские контракты остались в Git | **KEEP / RESEARCH_OR_LEGACY / DEPENDENCY_NOT_CLEARED** |
| `.github/` | В дереве три workflow: V20-08, V20-CAP4 research, CC-03 Windows. [CC-03 workflow](../.github/workflows/controlcenter-cc03-windows-native.yml), blob `0f43c02b955a089f11ffe2ad9b1c8ea78858e050`, слушает `ControlCenter/**`; старый статус CC-03 не делает workflow «безопасным для удаления» | **KEEP / CI_REFERENCE** |
| `audit_only/` | В текущем main — 16 файлов исторического `stop_tick_grid_20261012/`; закрытые PR содержат иные исторические деревья `audit_only` | **KEEP / RESEARCH_EVIDENCE / UNIQUENESS_NOT_VERIFIED** |
| `scripts/`, `docs/`, `research/`, `results/`, `schemas/`, `evidence/` | Историческая исследовательская инфраструктура, возможные входы/ссылки, часть материалов и негативных результатов | **KEEP / IMPORT_AND_PROVENANCE_NOT_VERIFIED** |

**Особый риск для Kimi:** корневой [`AGENTS.md`](../AGENTS.md), blob `a3aa857b98dca524ea60c24c5171f96517e046c0`, и старые разделы [`README.md`](../README.md) содержат исторический контракт «2025 locked TRUE OOS». Это требование **в рамках старого research pipeline**, не свидетельство, что 2025 остаётся untouched TRUE OOS для ретроспективных TRL-исследований 2026 года. Для TRL актуальную границу OOS проверять по первоисточникам и [инструкции проекта](PROJECT_INSTRUCTIONS_CURRENT_2026-11-20.md). Нельзя переобозначать уже использованные интервалы как новый untouched OOS.

## 4. Gate перед дальнейшей R7-очисткой

1. На **конкретный путь**, не целую папку: установить использование через Python imports, CLI, `pyproject`, Windows scripts, GitHub workflows, ссылки отчётов и ветки с сохранёнными первоисточниками.
2. Для уникальных исторических материалов: **copy → SHA и публичная privacy-проверка → manifest/provenance → offline regression**. Не переносить FINAM/DPAPI, счета, токены, необезличенные журналы, SQLite и частные чаты в публичный архив.
3. До необратимой очистки: **новый независимый полный Git mirror текущего MAIN/refs + PR/Issues/CI экспорт + SHA/наличие второго носителя**. Существующий ZIP после #571 не включает #578/#579 и Git history.
4. **Отдельное разрешение владельца на конкретное удаление/Merge**, даже если всё выше PASS. При UNKNOWN — не удалять. R5/R6 окончательный backup/restore — в конце после Kimi.

**Что реально проверено сейчас:** Git SHA, дерево архива, основные исходники/конфигурация/CI по указанным blob SHA. **Что не проверено:** полный reverse-import анализ всего Git, исполнение offline suites, Windows installed, FINAM/SLTP/ARMED, независимый архив всех 10 PR, полноценный privacy audit, текущий Git mirror, cold restore. Следовательно, `R7_DEPENDENCY_GATE=PARTIAL_READONLY`, `R7_DELETE_GATE=BLOCKED`, `R1_KIMI_ACCESS=NOT_TESTED`.

**Следующий безопасный шаг:** довести точную карту candidate-path → imports/CI/data → archive provenance; параллельно готовить три Kimi-проекта по [R1.1 index](KIMI_R1_1_VERIFIED_SOURCE_INDEX_2026-11-20.md), без притворного PASS и без LIVE.
