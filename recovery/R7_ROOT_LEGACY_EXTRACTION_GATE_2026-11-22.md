# R7 — единое выведение старой Market Pattern Discovery из рабочего корня (22.11.2026)

**АКТУАЛЬНЫЙ ДОКАЗАТЕЛЬНЫЙ СРЕЗ 22.11.2026 — после ранее описанных промежуточных FAIL.** Исторические отчёты ниже сохранены как хронология и не отражают окончательный CI. На PR #586 HEAD `4d9adbd866fc7be2ec68fea219c8932974356319`: [R7 7/7 jobs SUCCESS, попытка 2](https://github.com/alkospacer123/market-pattern-discovery/actions/runs/44953786558), [полный CC03 Windows-native SUCCESS](https://github.com/alkospacer123/market-pattern-discovery/actions/runs/44953786567), [Main Admission SUCCESS](https://github.com/alkospacer123/market-pattern-discovery/actions/runs/44953786551). Исторический оригинальный pytest остается 45 PASS / 1 FAIL, а forensic CI PASS означает только точное сохранение этого FAIL; исходные Git архивы не изменены. Защищённые `archive/pre-r7-cleanup` на `f15d565755b996252081ed49ed5a094ee1e8d820` и `archive/pre-root-legacy-20261122` на `09bca5641cb5bb367e84505ebfc6f8c7f35e2620` подтверждены `protected=true` через GitHub API, Ruleset #27793383 active, запрет deletion/update/non-fast-forward, без bypass. `main=e52dd90ef3e85c6ccc3b075f934df3ea8f5ffa8d` на момент этого среза; #585 и #586 остаются Draft, **Merge ещё не выполнялся**. Новые коммиты в PR требуют повторной проверки актуального точного HEAD; этот срез нельзя автоматически считать их CI.

**ОСТАТОЧНАЯ ГРАНИЦА ПРИЁМКИ.** Предлагается единовременное удаление только устаревшего root legacy (233 файла плюс совместимый указатель), все шесть защищённых деревьев сохраняются. Прямые импорты/Markdown, dynamic AST 80 вызовов, выбранные offline/Windows тесты, 527/530 малых metadata Git blobs, оригинальные архивные индексы и отдельные Kimi/H1/M15 связи проверены в пределах описанных тестов. 302 вхождения старого namespace обнаружены в семи сохранённых метаданных-файлах: три больших historical scope SHA inventories M15, frozen CC baseline, два stage2 manifests и `IntradayLab/optimization_registry/STUDY_CATALOG.json`. Последний содержит 247 записей, 17 ссылок на старый root, все `HISTORICAL_REFERENCE` с `ref=728d23e25d4bd41fdb6d50e134d1f099c206c6b2`; исторические code/config/results доступны по этому Git SHA. `build_registry.py` и `audit_registry.py` получают старые исходники через `git` ref/path, не Python import удалённого ядра. Не переписывать исходные M15 манифесты ради зелёных счётчиков. Три metadata-файла больше 2 МБ исключены из контент-скана и требуют отдельной оценки при полном replay. Проверка не означает достижения полного functional closure неизвестных внешних пользователей, всех данных ZIP/XLSX/CSV или cold restore.

**СЛЕДУЮЩЕЕ РЕШЕНИЕ:** операторский review и отдельное разрешение Merge #585 → #586, с сохранением original historical 1 FAIL и всех датированных рисков. Финальная автономная проверка Recovery — после этапа Kimi; не выдавать существующий Git archive за independent backup.

**СТАТУС ИСТОРИЧЕСКОГО ПЕРВОГО АУДИТА: DRAFT_CANDIDATE / ARCHIVE_GIT_REF_CREATED / MAIN_UNCHANGED / DELETE_GATE_BLOCKED.** Это PR-кандидат, не утверждение, что перенос уже произведён в `main`.

## Источник и архив

- Исходный `main` до этого этапа: `e52dd90ef3e85c6ccc3b075f934df3ea8f5ffa8d` (#583 и #584 уже merged); полный оригинал доступен в [immutable-by-SHA дереве](https://github.com/alkospacer123/market-pattern-discovery/tree/09bca5641cb5bb367e84505ebfc6f8c7f35e2620).
- Создана отдельная ветка-указатель `archive/pre-root-legacy-20261122` на `09bca5641cb5bb367e84505ebfc6f8c7f35e2620` (четыре документационных коммита после `e52dd90ef3e85c6ccc3b075f934df3ea8f5ffa8d`, непосредственный родитель cleanup-кандидата). Поэтому точный Git SHA и mode совпадают для **всех 234** первоначально предназначенных к выведению объектов (233 полностью удалены из кандидатного дерева, `research_domains.md` заменён архивным указателем). Старый `archive/pre-r7-cleanup` остаётся на `f15d565755b996252081ed49ed5a094ee1e8d820` без изменений. **Ветки и Git history не являются автономной резервной копией**; финальный Recovery по дорожной карте — позже.
- В отдельном публичном `market-pattern-archive` ничего не публиковалось; в том числе не переносились приватные внешние артефакты, Windows-файлы, DPAPI, журналы и торговые настройки.

## Единственный согласованный пакет удаления из активного дерева

| Исходный root path | Git blobs до выноса | Классификация |
| --- | ---: | --- |
| `docs/` | 34 | Старые отчёты autonomous/Phase 4–7 |
| `research/` | 4 | Историческая EXP-000001 и гипотезы |
| `schemas/` | 6 | Контракт старого research движка |
| `scripts/` | 7 | Старые CLI запускатели |
| `src/` | 86 | Старое ядро `market_pattern_discovery` |
| `tests/` | 50 | Тесты этого ядра |
| `config/` | 17 | Конфиги и четыре binary .u32 |
| `results/` | 17 | Старые execution/research результаты |
| `evidence/` | 5 | Исторический audit evidence |
| Шесть корневых `ARTIFACT_*`, `CURRENT_ARTIFACT_*`, `*MEMORY*`, `SMOKE_RUN_*` отчётов | 6 | Legacy smoke/handoff, не V20 LIVE |
| `pyproject.toml` | 1 | Packaging старого ядра, полностью удаляется из active tree |
| `research_domains.md` | 1 | Исторический оригинал в archive; в active tree остаётся только ссылка-указатель для неизменного H1 README |
| **Итого оригиналов** | **234** | 233 удаляемых Git paths + 1 заменяемый архивным указателем |

**Не удаляются и не изменяются:** `V20_TradingSystem_M15/`, `ControlCenter/`, `TradingResearchLab/`, `TradingSystemLab/`, `IntradayLab/`, `audit_only/`, исходные четыре CI workflow (добавляется только отдельная **read-only** проверка в `.github/workflows/`); FINAM, Windows Tasks и установленный LIVE не затрагиваются. `recovery/` и root документация дополняются навигацией, без правок runtime-кода.

## Gate перед Merge

1. Автоматически сравнить исходный `main`, архивную ветку на `09bca5641cb5bb367e84505ebfc6f8c7f35e2620` и кандидат: **233 удаления + единственная архивная ссылка `research_domains.md` вместо оригинального исследовательского контракта**, ни одной модификации Git SHA/mode retained исходников, все 234 архивных Git objects доступны.
2. Пройти полную обратную проверку импортов и путей (`src.market_pattern_discovery`, `market_pattern_discovery.*`, `docs/`, `config/`, `schemas/`, scripts/CLI, `pyproject`) в V20/CC/TRL/H1/M15/recovery и GitHub workflow. Исторические ссылки исправить на pinned archive commit, активные зависимости — сохранить или мигрировать. Нельзя ошибочно трактовать 0 совпадений в выборке как closure.
3. Изолированно сравнить offline regression retained V20/CC/H1/M15/TRL и проверить воспроизводимость старого research **из архивного checkout**, включая binary/index, JSON/CSV. Отдельно подтвердить native symlink security и полноту original CC03 scope/native acceptance; отдельный symlink-test не заменяет полный CC03.
4. CI Main Admission должен быть зелёным на **точном финальном head SHA**. Это не LIVE/FINAM/SLTP PASS. По существующему workflow значительная часть R7-защитных jobs привязана к #583 и не запускается автоматически на новом PR.
5. Выполнить операторский review полного diff, GitHub metadata/refs, protected dependencies, возможных внешних данных и только затем явно разрешить **отдельный Merge**. До приёмки старый `main` неизменен.

**Цель:** активная база знаний Kimi содержит только V20/CC/TRL и необходимые общие H1/M15/audit зависимости; восстановление замороженных старых экспериментов — через pinned archive SHA, без объявления их новым LIVE.

## Прямо обнаруженные блокеры и новая автоматическая проверка (22.11.2026)

- `TradingSystemLab/README.md` содержит относительную ссылку `../research_domains.md`. Вместо удаления этого файла без замены оставлен **малый указатель на архивный SHA**, исходный H1 Git tree не изменён.
- `ControlCenter/ci/scope_audit.py` сравнивает **весь** верхний уровень кроме CC с замороженным `ci/protected-main-tree.json`, поэтому уже вступившие в `main` независимые изменения других проектов несовместимы с этим старым контрактом. Не изменять frozen CC baseline и не подавлять native-test failure; требуется согласованный **преемник scope-guard** с отдельной политикой разрешённых изменений.
- В кандидат добавлен `.github/workflows/r7-root-legacy-readonly.yml` и offline-сканер `recovery/tools/r7_root_legacy_readonly_gate.py`: git SHA/mode относительно закреплённого архивного предка, неизменность protected subtree/старых workflow, Markdown-ссылки, AST direct imports. Скан не исполняет код репозитория, пропуски фиксирует и блокирует тест; **не заменяет полную регрессию/CC03 native**.
- Ключевой gate: `DELETE_SCOPE_PARTIAL`, `LIVE_UNTOUCHED`, `MERGE_BLOCKED` до source parity, archive replay, CC native, external dependency verification и отдельного разрешения.

## Реальные дополнительные тесты 22.11.2026 — исходный архив не переписывать

### Статические и аппаратно-независимые проверки

- [Main Admission на HEAD `6a24f38fab8e495e8f0e2a61bd121e4e5117aadc`](https://github.com/alkospacer123/market-pattern-discovery/actions/runs/44951308427) — **SUCCESS**, только selected offline baseline, не полный релиз.
- [R7 Root Legacy Gate на том же HEAD](https://github.com/alkospacer123/market-pattern-discovery/actions/runs/44951308441) — scope/link/AST **PASS**: 233 удаления, 3 добавления на прежнем audited HEAD, 6 документальных замен, 2 045 текстовых файлов, 1 266 внутренних Markdown-ссылок, 0 новых missing, 0 прямых импортов старого root ядра, 0 skipped eligible text. **Весь workflow остаётся FAILURE из-за отдельного исторического теста**; это не следует маскировать.
- Динамические вызовы с точным file/line: **80 всего**, 61 literal и 19 computed: CC=1, IntradayLab=11, V20=7 computed, TradingSystemLab=0 computed. В просмотренных выражениях — локальные CC importlist, IntradayLab tools/audit, V20-owned research AST и временные research modules, **не наблюдаются прямые переходы к удалённому `market_pattern_discovery`**. Это не закрывает внешние вызовы или непрямую runtime reachability.
- Отдельный защищённый [Windows-native CC03 symlink gate](https://github.com/alkospacer123/market-pattern-discovery/actions/runs/44951308441) — **PASS**: file/directory symlinks отказаны, sealed CC Git tree SHA неизменен, только временные synthetic fixtures. Старый **full native CC03** с проверкой entire-root `ControlCenter/ci/scope_audit.py` не принят и не отключён.

### Архивный checkout — точный SHA, настоящий тест, обнаруженный дефект

- В GitHub Actions checkout строго `09bca5641cb5bb367e84505ebfc6f8c7f35e2620` (старый исходный код, не кандидатный runtime). В архивном оригинале: **143/143 Python AST parse PASS**, **30/30 JSON parse PASS**, **4/4 .u32 content SHA-256 + count×4 bytes PASS**. Исторические `pyproject.toml`, `research/experiments/EXP-000001.json` присутствуют.
- Запущены выбранные реальные synthetic тесты `tests/test_backtest_engine.py`, `tests/test_validation_engine.py`, `tests/test_research_cells.py`: **45 PASS / 1 FAIL**. Единственный отказ: `tests/test_validation_engine.py::test_all_deterministic_acceptance_outcomes` ожидает `ValidationStatus.REJECTED`, но исходный `ValidationEngine._decision` при `trade_count < minimum_trades` возвращает `INSUFFICIENT_DATA`. Это фактический исторический дефект/расхождение тестового ожидания, **не регрессия от очистки**, поскольку тест запускался в исходном архивном snapshot.
- Тест **не** подавлен, не исправлен в истории, не xfailed и не исключён. `ARCHIVE_SOURCE_INTEGRITY=PASS_SCOPED`, `ARCHIVED_SELECTED_TESTS=45_PASS_1_FAIL`, `FULL_LEGACY_REPLAY=BLOCKED` до отдельного решения о документированном дефекте либо версионированном исправлении **без изменения замороженного оригинала**.

### Непройденные заключительные gate

- Верификация external data/ZIP/XLSX и indirect consumers, полный парный offline regression V20/CC/H1/M15/TRL; оригинальное исследование из архива не полностью PASS.
- Согласованный successor для устаревшего полного root-scope CC03, без изменения frozen CC origin, отдельные native-тесты.
- После приёмки #585 перенаправить #586 на `main`, выполнить итоговые exact-head CI/checkout/hash/diff/rollback проверки; требуется явное разрешение пользователя для Merge.

**ИТОГ: DRAFT / PARTIAL_ARCHIVE_VALIDATED / HISTORICAL_TEST_FAIL_PRESERVED / NATIVE_SYMLINK_PASS / MAIN_UNCHANGED / NO_MERGE.**

## 22.11 — расширение полного native CC03 без изменения frozen ControlCenter

- В этом же PR (без нового PR) добавлен `.github/workflows/r7-cc03-full-native.yml`, производный от исходного зафиксированного `main:.github/workflows/controlcenter-cc03-windows-native.yml` (исходный Git blob `ebf5b976a9f3857728369b6813512c0e00f2399d`). Реально вызывается **оригинальный** `ControlCenter/ci/windows_acceptance.py` на GitHub-hosted Windows, строго только для PR #586.
- Новая проверка требует полного frozen SHA `ControlCenter`, оригинального frozen `scope_audit.py`, всех 16 исходных тестовых этапов, неповреждённых SHA256/JUnit evidence, полного набора тестов (не менее 700 PASS), и единственного **явно обозначенного** ожидаемого исторического scope failure. Ни оригинальный scope-guard, ни frozen manifest не изменяются и не выключаются.
- Это дополнительный review/CI gate на exact HEAD: до результата workflow **FULL_CC03_NOT_VERIFIED**. Если какой-то иной тест или provenance изменён — FAIL. Отдельная политика разрешённых root изменений уже проверяется в независимом R7-сканере, но не считается заменой оригинального frozen CC03.
- После добавления workflow scope: **233 удалённых**, `research_domains.md` — совместимый archive pointer, изменённые markdown и 4 добавления (root gate + full native CC workflow + scanner + gate doc). Никаких изменений старых workflow или protected project trees.

## Контролируемая классификация исторического тестового FAIL — без изменения архива

Исходная архивная фикстура `tests/test_validation_engine.py::test_all_deterministic_acceptance_outcomes` (archive ref `09bca564...`) создаёт LONG-кандидата и убывающие цены в `market(losing=True)`. В историческом `BacktestEngine._confirmed` для LONG требуется `confirmation.close > signal.close`; при монотонно снижающихся свечах подтверждения не происходит. В `ValidationEngine._decision` первый критерий — `trade_count < minimum_trades`, и тогда ответ `INSUFFICIENT_DATA`. Ожидаемый фикстурой `REJECTED` соответствует другому сценарию: достаточно исполненных, но экономически плохих сделок. **Это несоответствие старой тестовой фикстуры и фактического поведения**, обнаруженное в нетронутом archive checkout; не доказательство регрессии от root-cleanup.

Дополнительная **подготовленная** строгая классификация CI не исправляет и не пропускает старый тест: запускает всю исходную тройку тестовых файлов и требует raw pytest exit 1, ровно 46 testcases, 45 PASS, единственный FAIL с точным ID и текстом `INSUFFICIENT_DATA` vs `REJECTED`, ноль skipped/errors; raw JUnit/log собираются отдельным артефактом. Любое изменение количества, типа ошибки, внезапный успех вместо исторического FAIL или лишний отказ — **gate FAIL**. Если forensic gate зелёный, это означает только `ARCHIVE_KNOWN_PREEXISTING_FAILURE_PRESERVED`, **не** `ARCHIVE_ALL_TESTS_PASS`. До реального запуска и проверки нового workflow не считать его пройденным.

Исходный SHA/режимы всех исторических файлов и оригинальный full CC03 сохранены. Решение, допустимо ли сохранить известную ошибку без восстановления старого ядра в рабочем `main`, принимает оператор после внешней проверки данных, парных регрессий и review. **MERGE BLOCKED** до отдельного разрешения.

## 22.11 — дополнительный обязательный gate: защита archival ref и scan retained config metadata

**Архивный ref — реальный блокер.** GitHub API на момент проверки: `archive/pre-root-legacy-20261122` указывает на `09bca5641cb5bb367e84505ebfc6f8c7f35e2620`, но возвращает `protected=false`; старый `archive/pre-r7-cleanup` и `main` возвращают `protected=true`. Добавлен изолированный `archive-ref-protection` в PR #586: по read-only GitHub API требует и зафиксированный SHA, и `protected=true`; иначе **контролируемый FAIL**, пока оператор не включит защиту от удаления и force-push через Rulesets. Интеграция не наделяется правами записи/администрирования и не перемещает архив. Это не финальный автономный Recovery.

**Новые Git-object/working-checkout данные о ссылках.** Добавлен отдельный `retained-noncode-literals` — источник точный candidate HEAD, Git blob SHA-1 и length сверяются для небольших **неторговых текстовых конфигураций и метаданных** `.json/.txt/.yaml/.yml/.ini/.cfg/.xml/.toml/.js/.ts` в защищённых V20/CC/TRL/H1/M15/audit поддеревьях, исключая явно исторические `results/independent_results/work/archive/data/evidence`. Данные анализируются как UTF-8 текст; никаких исполнений/FINAM. Регистрируются только file/line и имена паттернов `market_pattern_discovery`, `unknown_universe_v1`, legacy CLI, `pyproject.toml`, `research_domains.md`, но не исходные текстовые строки. Непрочитанный Git blob, неверный SHA или отсутствие выбранного малого файла — FAIL. Ожидаемый Git-инвентарь на текущем tree — около **530** файлов этого scope, из которых **3 превышают 2 МБ** и отдельно регистрируются как непроверенные. Это **дополнение**, а не утверждение, что проверены 1,67 ГБ CSV/JSON или все косвенные потребители.

**Состояние до фактического CI:** новые jobs только STAGED; статусы не объявлять PASS до лога на точном HEAD. Архивная ветка ещё нуждается в защите; **MERGE BLOCKED**.
