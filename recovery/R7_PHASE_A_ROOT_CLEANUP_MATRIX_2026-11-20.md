# R7 / Этап А — матрица решений для корня market-pattern-discovery

**Дата среза:** 20.11.2026. **Истина MAIN:** [`market-pattern-discovery@f15d565755b996252081ed49ed5a094ee1e8d820`](https://github.com/alkospacer123/market-pattern-discovery/tree/f15d565755b996252081ed49ed5a094ee1e8d820). **Статус:** `READONLY_ROOT_CLASSIFICATION_32_OF_32 / DEPENDENCY_CLOSURE_NOT_VERIFIED / NO_DELETIONS`. Сохранение копий в публичном архиве не означает разрешение удалить оригиналы.

## Результат этапа A — без ложного PASS

| Класс | Корневых объектов | Решение |
|---|---:|---|
| KEEP_ACTIVE + KEEP_DEPENDENCY | 6 | Сохраняем все 6 защищённых каталогов |
| KEEP_INFRA + KEEP_UPDATE | 5 | Сохраняем Git infra/CI и точки входа; README и AGENTS нуждаются в уточнении |
| REVIEW_LINKED | 13 | Гипотеза: связанная старая исследовательская платформа, **не** 13 независимых мусорных папок; всего **331 tracked blob** по Git trees |
| ARCHIVE_CANDIDATE | 8 | `audit_only/` (16 файлов) + 7 отдельных исторических корневых отчётов; это **кандидаты**, не доказанная безопасность удаления |
| **Всего** | **32** | **Оценено 32/32 только на уровне корневых объектов** |

### Матрица

| Путь | Предварительное решение | Подтверждённое назначение / ограничения | Следующая проверка |
|---|---|---|---|
| `V20_TradingSystem_M15/` | **KEEP_ACTIVE** | LIVE-intended V20 R088, 9-patch stack, tests. Исторические V20-01…07 внутри сохранять до отдельной оценки. | Не перемещать, не менять релиз |
| `ControlCenter/` | **KEEP_ACTIVE** | V20 UI/CC-07, exporter, Windows; внутри есть исторический CC-03, но каталог целиком защищён. | Не перемещать; ревизия старого CC-03 отдельно |
| `TradingResearchLab/` | **KEEP_ACTIVE** | Current Research/Evolution/Journal, ноябрьский closeout и воспроизводимые свидетельства. | Сохранять; не считать устаревшее по дате автоматически ненужным |
| `recovery/` | **KEEP_ACTIVE** | Текущие знания, R1–R8, Kimi, provenance. | Сохранять; документы срезов не заменяют LIVE |
| `TradingSystemLab/` | **KEEP_DEPENDENCY** | Legacy H1, но `TradingSystemLab.stage8_robot` прямо импортируется V20. | Оставить целиком; перед любым дроблением dependency/offline тесты |
| `IntradayLab/` | **KEEP_DEPENDENCY** | Legacy M15, но `IntradayLab.core` прямо импортируется V20. | Оставить целиком; перед любым дроблением dependency/offline тесты |
| `.github/` | **KEEP_INFRA** | Три workflow; V20 offline CI, CC legacy Windows, V20 research; workflow-история для восстановления. | CI не отключать, не переносить; исторические workflow рассмотреть после тестов |
| `.gitattributes` | **KEEP_INFRA** | Git атрибуты, влияют на интерпретацию содержимого. | Оставить |
| `.gitignore` | **KEEP_INFRA** | Управляет отсутствием секретов, временных файлов и рынка в Git; игнорирует ряд результатов. | Оставить; не менять при архивировании без review |
| `README.md` | **KEEP_UPDATE** | Главная точка входа GitHub, но ниже шапки содержит контракты прежней research платформы. | Сохранить, в будущем сделать краткий актуальный маршрут трёх проектов |
| `AGENTS.md` | **KEEP_UPDATE** | Глобальный контракт старого discovery объявляет 2025 untouched TRUE OOS, что не универсально для текущего TRL. | Сохранить; отдельно уточнить правила по областям применения, не отменяя anti-leakage |
| `BBW/` | **REVIEW_LINKED** | README BBW говорит о независимом research domain и явно ссылается на `bbw_system/` и `results/`. | Проверить как часть общего legacy research bundle |
| `bbw_system/` | **REVIEW_LINKED** | 25 tracked файлов спецификаций и конфигураций BBW, исполняемые пакеты — в `src/bbw_system`. | Сопоставить с `src/`, CLI, test suite и TRL |
| `src/` | **REVIEW_LINKED** | 139 Python/документационных файлов, пакеты `bbw_system` и `market_pattern_discovery`. | Проверить импорты в V20/CC/TRL, package entry points и offline tests |
| `tests/` | **REVIEW_LINKED** | 69 тестов исходной исследовательской платформы; часть может проверять общую H1 методологию. | Не удалять до карты тестового покрытия и зависимостей |
| `pyproject.toml` | **REVIEW_LINKED** | Привязывает `src/`, `tests/` и множество BBW/phase validation CLI; удалить частично означает сломать пакет. | Переоценивать и изменять только вместе с linked research bundle |
| `config/` | **REVIEW_LINKED** | 19 файлов, включая старые research настройки и 4 бинарных rank-index в `unknown_universe_v1`. | Проверить источники, индекс SHA, data/cost privacy; не публиковать слепо |
| `schemas/` | **REVIEW_LINKED** | 6 JSON-схем для legacy research validation. | Проверить связь с `src/` и тестами |
| `scripts/` | **REVIEW_LINKED** | 7 CLI сценариев исследовательской платформы и автономного research. | Проверить вызовы из tests/docs/CI |
| `research/` | **REVIEW_LINKED** | 4 research registry-файла, не совпадает с основным `TradingResearchLab/research/`. | Сохранить историю provenance, выяснить потребность TRL |
| `results/` | **REVIEW_LINKED** | 19 исторических research artifacts, rejected-family и candidate baseline. | Проверить происхождение, уникальность, ссылки и право публичного архива |
| `docs/` | **REVIEW_LINKED** | 34 документа о старой research pipeline, smoke audit и методике. | Часть may be unique evidence; переносить группой после проверки |
| `evidence/` | **REVIEW_LINKED** | 6 BBW/temporal-alignment evidence файлов. | Нельзя оторвать от методики и источников |
| `research_domains.md` | **REVIEW_LINKED** | Старое разделение TSL и BBW, относится к прежней research схеме. | Сохранять вместе с исходными domain docs; не считать текущим TRL паспортом |
| `audit_only/` | **ARCHIVE_CANDIDATE** | 16 файлов STOP/TICK GRID audit; README: PRODUCTION_CHANGES=NONE и код не импортируется роботом; архивный Draft PR #5 готов. | Источник не удалять: отсутствуют полный Git checkpoint, static refs и offline regressions |
| `ARTIFACT_HANDOFF_VERIFICATION_REPORT.md` | **ARCHIVE_CANDIDATE** | Сентябрьский тест сохранения пустых JSONL и общего /workspace — не текущая V20/CC система. | Копия+SHA+проверка links → решение об удалении из root |
| `CURRENT_ARTIFACT_STORAGE_STATUS.md` | **ARCHIVE_CANDIDATE** | Срез состояния старого /workspace от 11.09.2026. | Копия+SHA+links → архив; не текущий статус Recovery |
| `PERMANENT_MEMORY_DIAGNOSTIC_REPORT.md` | **ARCHIVE_CANDIDATE** | Историческая диагностика памяти автономной платформы 11.09. | Копия+SHA+links → архив |
| `PERSISTENT_MEMORY_VERIFICATION_REPORT.md` | **ARCHIVE_CANDIDATE** | Историческая проверка синтетических persistent artifacts. | Копия+SHA+links → архив |
| `SMOKE_RUN_V2_REPORT.md` | **ARCHIVE_CANDIDATE** | Старый 5-cycle smoke исследовательского pipeline 11.09, не V20 R088. | Копия+SHA+links → архив, сохранить отрицательные результаты и metadata |
| `SMOKE_RUN_V3_REPORT.md` | **ARCHIVE_CANDIDATE** | Старый 5-cycle autonomous smoke, не доказательство LIVE. | Копия+SHA+links → архив |
| `ROADMAP.md` | **ARCHIVE_CANDIDATE** | Корневой roadmap старого TradingSystemLab Phase 7.3; текущий Roadmap в recovery. | Копия+SHA+links → архив; ссылки при необходимости редирект |

## Почему нельзя просто удалить 13 старых каталогов

**Проверенная связность:** [`pyproject.toml`](https://github.com/alkospacer123/market-pattern-discovery/blob/f15d565755b996252081ed49ed5a094ee1e8d820/pyproject.toml) объявляет `where=["src"]`, packages `market_pattern_discovery*`, `bbw_system*`, `testpaths=["tests"]` и 23+ CLI entry points. [`BBW/README.md`](https://github.com/alkospacer123/market-pattern-discovery/blob/f15d565755b996252081ed49ed5a094ee1e8d820/BBW/README.md) связывает BBW с `bbw_system/`, `results/`, `research_domains.md`. Исторический `AGENTS.md` глобально ограничивает 2025 TRUE OOS, но [актуальный TRL](https://github.com/alkospacer123/market-pattern-discovery/blob/f15d565755b996252081ed49ed5a094ee1e8d820/TradingResearchLab/README.md) сообщает, что прежние периоды нельзя считать untouched OOS. Значит, старые инструкции должны быть **сфокусированы на прежней платформе**, а не автоматически действовать для TRL.

**Масштаб:** `BBW=1`, `bbw_system=25`, `src=139`, `tests=69`, `config=19`, `schemas=6`, `scripts=7`, `research=4`, `results=19`, `docs=34`, `evidence=6`, плюс `pyproject.toml=1` и `research_domains.md=1`. Это **331 Git blob** в 13 компонентах, а не 331 доказанно ненужный файл. `config/` содержит бинарные исследовательские `.u32` индексы; приватность/переносимость в публичный архив отдельно NOT_VERIFIED.

**Protected dependencies:** [V20 `finam_live.py`](https://github.com/alkospacer123/market-pattern-discovery/blob/f15d565755b996252081ed49ed5a094ee1e8d820/V20_TradingSystem_M15/v20_runtime/finam_live.py) импортирует `TradingSystemLab.stage8_robot`; [V20 `m15_runner.py`](https://github.com/alkospacer123/market-pattern-discovery/blob/f15d565755b996252081ed49ed5a094ee1e8d820/V20_TradingSystem_M15/v20_runtime/m15_runner.py) импортирует `IntradayLab.core` и `TradingSystemLab.stage8_robot`. Даже если 13 связанный legacy research bundle удастся убрать, шесть защищённых каталогов не затрагиваются.

## Имеющиеся архивные свидетельства

[Архивный PR #5](https://github.com/alkospacer123/market-pattern-archive/pull/5) **Draft, not merged**: полный набор из 16 файлов `audit_only/stop_tick_grid_20261012/` скопирован без изменений с `GIT_BLOB_MATCH_16_OF_16`. Исходный [README](https://github.com/alkospacer123/market-pattern-discovery/blob/f15d565755b996252081ed49ed5a094ee1e8d820/audit_only/stop_tick_grid_20261012/README.md) заявляет `PRODUCTION_CHANGES=NONE` и отсутствие импортов роботом, но этот README **не доказывает** отсутствие всех сторонних ссылок и зависимостей TRL. Ничего не удалять до подтверждения тестов и checkpoint.

[Рабочий PR #580](https://github.com/alkospacer123/market-pattern-discovery/pull/580) — отдельно открытый Draft для глубокого Kimi V20, не смешивать с работой по очистке и не считать merged.

## Обязательные gates перед любым удалением

1. **Static dependency closure:** проверить import/file-path ссылки не только Python `import`, но и строки `open/read_csv/Path`, PowerShell, GitHub workflows, `pyproject`, pytest paths, install scripts и отчёты. Для сомнительных случаев `UNKNOWN → KEEP`. Статический анализ ещё **не** выполнен по всему рабочему репозиторию.
2. **Публичный архив:** `copy full logical bundle → verify original Git blob SHA → review секретов/персональных данных/приватных счётов/архивных бинарных файлов → manifest`. Часть исторических исходников может требовать непубличного шифрованного архива.
3. **Pre-delete protective checkpoint:** полный *актуальный* Git mirror всего `discovery` с refs/tags/branches, экспорт PR/Issues/CI metadata, SHA и независимый проверенный носитель. Старый ZIP после #571 не содержит #578/#579 и Git history; checkpoint `NOT_VERIFIED`.
4. **Isolated offline tests:** до и после кандидатного удаления воспроизвести V20/R088 9-patch tests, ControlCenter offline tests, TRL source references + прежнюю platform CLI/pytest suite либо зафиксировать явно согласованный отказ от использования legacy. Не обращаться к FINAM, не запускать H1/M15 LIVE.
5. **Owner decision on exact deletion PR:** конкретный перечень с SHA, бэкапом и откатом; `main` и исходные ветки не переписывать. PR Merge, создание нового GitHub, операции Intel/LIVE запрещены без разрешения.

### Очередь проверки

**Сначала** семь корневых исторических отчётов и `audit_only/` (низкий риск копирования, **не** нулевой риск удаления). **Затем** единой связанной системой исследовать 13 root-компонентов (высокий эффект очистки, высокий риск сломать старую воспроизводимость/TRL). **Потом** исправить корневую навигацию README/AGENTS и проверить три отдельные логические точки входа Kimi. Цель — **удобный рабочий main без потери воспроизводимости**, а не удаление ради числа папок.

**Откат:** пока никаких удалений не выполнено, original `main` сохранился. Это не заменяет проверенный независимый Git backup и не означает R7 PASS.


## R7-А — дополнительная прямaя проверка исходников (20.11.2026)

**Метка:** `DIRECT_SOURCE_SCAN_315 / OLD_PLATFORM_LITERAL_MATCH_0 / STATIC_GATE_PARTIAL`.
**Фиксированный источник:** `market-pattern-discovery/main=f15d565755b996252081ed49ed5a094ee1e8d820`, без анализа установленного Windows/LIVE. Данные получены из `git/trees` и полного содержимого конкретных файлов GitHub через read-only connector, с нулём ошибок чтения в указанных группах.

| Область исходников | Прочитано | Результат |
|---|---:|---|
| `V20_TradingSystem_M15/v20_runtime/*.py` без `tests/` (включая вложенные runtime модули) | 45 | Нет совпадений по указанным ниже именам старой root-платформы |
| Прочие `V20_TradingSystem_M15/**/*.py` (включая runtime tests и исторический код) | 98 | То же |
| `V20_TradingSystem_M15/**/*.ps1` | 55 | То же |
| `ControlCenter/**/*.{py,ps1,yml,yaml,toml}` | 109 | То же |
| `TradingResearchLab/**/*.py` | 5 | То же |
| `.github/workflows/*.yml` | 3 | То же |
| **Всего просмотрено** | **315** | **0 буквальных совпадений с выбранными шаблонами, не 0 зависимостей вообще** |

**Искали без учёта регистра:** `bbw_system`, `market_pattern_discovery`, `unknown_universe_v1`, `research_domains.md`, `audit_only/`, пути `BBW/`, `src/`, `schemas/`, `pyproject.toml` (также Windows `\\`-разделители там, где применимо). Это **выборочный поиск характерных имён внутри полного содержимого перечисленных файлов**, не Python AST, не `importlib` trace, не скан всех расширений и не построенная автоматически transitively-closed карта.

**Положительные факты о связанности исторического комплекса:** [`BBW/README.md`](../BBW/README.md), blob `5dfd38bbd767b5fd3c7d96f4e79d4e018d322402`, явно связывает BBW research с `bbw_system/` и историческим процессом исследовательского pipeline. [`research_domains.md`](../research_domains.md), blob `3b957c8c5c02e09ad2b85643d8c5947b7f4a0fe7`, определяет два прежних научных домена TSL и BBW. [`pyproject.toml`](../pyproject.toml) связывает `src`, `tests`, `bbw_system`, `market_pattern_discovery` и CLI; **331 Git blob из 13 старых root-компонентов — единая кандидатная группа**, а не 331 подтверждённо ненужный файл.

**Границы текущего результата:**
- Не просканированы все Markdown/JSON/CSV, Windows вызовы во всём Git, Git refs и исторические branches; TRL имеет много Markdown-документов, а H1/M15 — тысячи исторических источников. Импорты могут быть динамическими и выраженными через имена/пути вне перечисленных шаблонов.
- Не запускались текущие CI, `pytest`, инсталляция, воспроизведение исследовательского пакета или before/after regressions; не оценена пригодность 4 бинарных index файлов `config/unknown_universe_v1` для публичного архива.
- `AGENTS.md`, корневой `README.md` и правила BBW TRUE OOS необходимо **ограничить историческим исследовательским доменом**, не переносить декларацию о нетронутом 2025 TRUE OOS на современный TRL.
- Даже ноль прямых ссылок во всех 315 прочитанных файлах **не даёт разрешение на удаление root-пакета**: `R7_A_DIRECT_SCAN=PASS_SCOPED`, `R7_A_FULL_DEPENDENCY_CLOSURE=NOT_VERIFIED`, `R7_DELETE_GATE=BLOCKED`.

**Следующий предметный gate (не ещё один отчёт ради отчёта):** закрыть статические ссылки внутри исторических H1/M15 и TRL Markdown/конфигураций, проверить полноту сохранения взаимосвязанной исследовательской платформы и offline тесты на изолированном checkout. До любого удаления — независимый актуальный Git checkpoint, архив **всего согласованного логического комплекса** с SHA/provenance, независимый контроль регрессий и разрешение оператора на конкретный PR. Не менять LIVE.


## R7-А — проверенные документальные связи и offline-инструмент (20.11.2026)

**Метка:** \`R7_A_OFFLINE_SCANNER_STAGED / SYNTHETIC_TESTS_4_OF_4_PASS / REAL_CHECKOUT_SCAN_NOT_RUN\`.

**Новые прямые факты по исходникам основного main \`f15d565755b996252081ed49ed5a094ee1e8d820\`:**
- \`TradingSystemLab/README.md\` blob \`ba02ab218b1307ea0a1224909201fd42a326707c\`, строки 26, 69–81, явно отделяет исследовательский BBW от H1 и ссылается на корневой \`../research_domains.md\`. Это подтверждённая **документальная ссылка**, а не runtime import BBW пакета.
- \`IntradayLab/README.md\` blob \`4a6b3ee47c7f3f6dd9e000dd5995e8b33c7ad3da\`, строка 60, прямо запрещает изменять корневые \`BBW/\`, \`results/\` и старые документы при работе со старой M15. Это историческая граница ответственности; удалить связанную документацию без сохранения provenance нельзя.
- \`TradingSystemLab/strategies/trend/T1_BBW_Donchian.py\` blob \`0005f8639ae7004ace29cfa5625b4e34b1cf3297\` импортирует собственные H1 индикаторы, а \`BBW\` здесь — расчёт Bollinger Band Width. Совпадение трёх букв **не** является зависимостью \`bbw_system\`.
- Корневой \`README.md\` blob \`b3c0ec9e488f4ff9c8745e6ce19cc090f0ff6319\` содержит старые CLI-команды \`python -m bbw_system...\` и \`python -m market_pattern_discovery...\` при наличии современной шапки. После архивирования связанной платформы эти команды необходимо удалить из рабочего *входа* либо явно перевести в историческую область, сохранив воспроизводимые инструкции в архиве.
- Корневой \`AGENTS.md\` blob \`a3aa857b98dca524ea60c24c5171f96517e046c0\` объявляет 2025 «untouched TRUE OOS» для прежнего исследовательского контура; требуется scoped-разделение, чтобы не вводить Kimi в заблуждение о TRL. Нельзя переписать исторический эксперимент как якобы untouched.
- \`.github/workflows/v20-08-live-windows.yml\`, \`v20-cap4-research.yml\`, \`controlcenter-cc03-windows-native.yml\` прочитаны: их области относятся к V20/CC, но **это только текущие 3 workflow**, без полного доказательства отсутствия прямых путей в иных Git refs/Windows/инсталляциях.

**Воспроизводимый offline-инструмент для полного checkout:**
- [\`recovery/tools/r7_dependency_scan.py\`](tools/r7_dependency_scan.py) blob \`aa1c3c44490029efadb46e8d7a259a01dbfe3178\` (stdlib only; read-only: \`git ls-files --stage\`, \`git rev-parse\`, \`git status\`, чтение текстовых файлов). Сохраняет Git HEAD/tree SHA, индекс отслеживаемых старых файлов и их Git blob SHA, классифицирует защищённые/старые ссылки по строкам без включения секретного содержимого строк.
- [\`recovery/tools/tests/test_r7_dependency_scan.py\`](tools/tests/test_r7_dependency_scan.py) blob \`6fdc41b2b8dc886d58b342e0a1ad43e593c7c8ed\`; \`python -m unittest discover -s recovery/tools/tests -p test_r7_dependency_scan.py -v\`: **4/4 PASS на изолированных синтетических Git репозиториях**, Git blob обоих файлов сверены с локально проверенными originals.
- Пример только для **отдельного read-only Git checkout** из его корня: \`python recovery/tools/r7_dependency_scan.py --repo . --output ../r7-dependency-report.json\`. Файл отчёта располагается **вне** checkout, а сам сканер не запускает код репозитория, FINAM, сеть, Windows Tasks или роботов.
- **Не запускался на реальном checkout**: доступа к полной локальной копии репозитория в данном окружении нет, API через отдельные GitHub файлы не заменяет полную Git-копию. Не объявлять \`R7_A_FULL_DEPENDENCY_CLOSURE=PASS\`, \`CHECKPOINT=PASS\` или \`R7_DELETE_GATE=PASS\`.

**Следующее подтверждение перед archive/cleanup:** получить реальный JSON полного checkout, вручную классифицировать защищённые ссылки и skipped/unreadable, проверить ссылки из TRL/H1/M15 на старые исследования и архив, затем защитный Git checkpoint, copy+SHA/privacy, offline before/after regressions и решение владельца о конкретном deletion PR.


## R7-Б — защитный Git-checkpoint и окончательная проверка источников (20.11.2026)

**SCANNER SAFETY FIX:** сканер `recovery/tools/r7_dependency_scan.py` теперь немедленно отказывает при *любом* staged/unstaged изменении tracked Git-файлов: отчёт не может связывать изменённый worktree с SHA исходного Git index. Соответствующий тест `test_dirty_checkout_refused_without_modification` PASS.

**Новый инструмент:** [`recovery/tools/r7_git_checkpoint.py`](tools/r7_git_checkpoint.py) создаёт новый каталог вне исходного checkout, полноценный `git clone --mirror`, проверяет `git fsck --strict`, создаёт Git bundle, сверяет SHA256, клонирует bundle обратно в отдельный bare repo, сверяет список refs, затем выполняет read-only сканирование старой платформы на **изолированном checkout, восстановленном из bundle**. Отчёты: `checkpoint-report.json` и `dependency-report.json`.

[`recovery/tools/tests/test_r7_git_checkpoint.py`](tools/tests/test_r7_git_checkpoint.py) и тесты сканера: **8/8 PASS**, только на синтетических локальных репозиториях. Git blobs инструментов и тестов проверены против локально протестированных объектов. GitHub в рабочем окружении через Git CLI недоступен (DNS), поэтому **настоящий mirror/scan ещё не выполнен**, и тесты не являются proof of restore целевого проекта.

**R7-B PASS требует отдельно:** независимой копии на носителе с проверенным SHA, сохранения полного актуального `Git history/refs/tags`, экспорта GitHub `PR/Issues/CI` (на момент проверки API сообщает 1163 workflow runs), проверки Git LFS/внешних зависимостей при наличии и решения оператора. Созданный скриптом Git-only отчёт намеренно оставляет `r7_checkpoint_status=PARTIAL_GIT_ONLY_NOT_FINAL_RECOVERY`. Он не заменяет финальные R5/R6 после Kimi.

**Действия с source:** `NO_DELETIONS / NO_MERGE / NO_LIVE_CHANGE`. `R7_A_DEPENDENCY_CLOSURE=NOT_VERIFIED`; `R7_B_EXTERNAL_CHECKPOINT=NOT_VERIFIED`; `R7_G_CLEANUP=BLOCKED`.


## R7-Б — доказанное восстановление Git bundle на Intel (operator evidence 20.11.2026)

**Метка:** \`R7_B_INTEL_BUNDLE_COLD_GIT_RESTORE_PASS_20261120\`. Получена оригинальная PowerShell-выгрузка оператора (\`1.txt\`, 1191 строк; не публиковать целиком из-за многословного перечня refs).

- **Исходный mirror:** \`D:\TradingSystemsR7\discovery-checkpoint-20261120\market-pattern-discovery.git\`, ранее \`git fsck --full --strict\` вернул \`exit=0\`, refs=1174, \`main=f15d565755b996252081ed49ed5a094ee1e8d820\`.
- **Независимый от mirror переносной Git bundle:** \`D:\TradingSystemsR7\discovery-checkpoint-20261120\market-pattern-discovery.bundle\`.
- \`bundle_bytes=439668305\`, \`SHA256=09C596CF5E8268256AD4511DE5F28C5E8CA8A823F62867FC9ECF441534D15527\`; \`git bundle verify\` → \`is okay\`, \`complete history\`.
- Bundle сообщает **1175 refs** (включая символический \`HEAD\`), а \`git for-each-ref\` в исходном и восстановленном bare repo сообщает **1174 refs**; это корректно разные виды подсчёта, а не потеря одного ref.
- **Пробное восстановление из bundle:** \`D:\TradingSystemsR7\discovery-checkpoint-20261120\market-pattern-discovery-verify.git\`, отдельный \`git clone --mirror\` из bundle, \`git fsck --full --strict\` закончил успешно. \`original_refs=1174\`, \`restored_refs=1174\`, \`ref_differences=0\`, \`restored_main=f15d565755b996252081ed49ed5a094ee1e8d820\`, \`git_bundle_restore=PASS\`.
- **Что доказано:** соответствие main и всех refs и самостоятельная целостность полного Git-объектного хранилища после восстановления из bundle; ни GitHub, ни рабочий main, ни LIVE не модифицировались.
- **Что ещё НЕ доказано:** физическая независимость диска \`D:\` от Intel/основного SSD, хранение второй копии вне компьютера, экспорт PR/Issues/CI metadata, Git LFS при наличии, воспроизводимость зависимостей и запуск offline регрессий, зависимостный скан полного main. Это предварительный **R7-Б Git-only checkpoint**, НЕ финальное Disaster Recovery и пока НЕ разрешение на удаление.
- **Следующий gate:** создать disposable \`market-pattern-discovery-scan-checkout\` из bundle на отдельном месте и исполнить read-only \`r7_dependency_scan.py --expected-head f15d565...\`, сохранить \`dependency-report.json\`; по результатам классифицировать защищённые ссылки и skipped файлы.


## R7-A — полный локальный checkout: real-scan V1, триаж и коррекция (20.11.2026)

**Метка:** \`R7_A_REAL_CHECKOUT_SCAN_V1_TRIAGED_20261120 / REVISED_SCANNER_V2_SELFTEST_10_OF_10_PASS / CLEANUP_GATE_NOT_YET_PASSED\`.

Оператор скопировал исходный \`main=f15d565755b996252081ed49ed5a094ee1e8d820\` из подтверждённого bundle в отдельный checkout, запустил стандартный offline-сканер. JSON проанализирован напрямую. \`tree_sha=44a5fef98dd8a3b6bc3e6d172f64fafddac5df4b\`, \`tracked_tree_modified=false\`.

| Измерение | Значение |
|---|---:|
| Tracked paths | 18 439 |
| Успешно прочитанные текстовые файлы | 16 828 |
| Точно учтённые старые root blobs | 331 |
| Совпадения V1 всего | 1 721 |
| Из них \`protected_or_entrypoint\` | 1 325 |
| Из них legacy-13 | 361 |
| Из них другие | 35 |
| Пропущено из-за лимита 2MB | 1 012 (= 996 CSV, 14 JSON, 1 TXT, 1 MD) |
| V20 matches | 0 (при V1-дефекте \`bbw_system\` — НЕ доказательство отсутствия зависимости) |
| ControlCenter matches | 2 (snapshot \`ci/protected-main-tree.json\`) |
| TRL matches | 5 (3 исторических отчёта) |
| H1 matches | 7 (включая 2 Python скрипта с \`audit_only/\`) |
| IntradayLab matches | 1 003 (преимущественно исторические hash/scope манифесты) |
| Recovery matches | 300 (292 — один исследовательский blob audit) |

**Критические прямые зависимости/границы:**
1. \`TradingSystemLab/stage8_robot/signal_execution_diagnostic.py:22\` и \`stage8_robot/tests/replay_stop_tick_grid.py:19,64\` имеют *исполняемые ссылки* на \`audit_only/stop_tick_grid_20261012\`. Восьмой root-candidate \`audit_only\` поэтому \`NOT_REMOVABLE_AS_IS\`, пока не изменён и не протестирован H1 диагностический workflow. Кроме того, эти файлы не входят в набор 331 старых blobs.
2. \`TradingResearchLab/reports/TRL-00-TESTER-MAP-2026-10-31.md:16–17\` указывает общие \`src/market_pattern_discovery/backtest\` и \`validation\` как \`SOURCE CONFIRMED\`; \`TRL-00-TESTER-REPRODUCIBILITY-2026-10-31.md:34\` описывает их как переиспользуемый движок и валидаторы. Это доказанная **исследовательская зависимость/наследие**, хотя прямой runtime import TRL этим не подтверждён. Нельзя объявлять \`src/\` целиком ненужным без миграции методик и тестов.
3. \`IntradayLab/optimization_registry/audit_registry.py:16\` и \`build_registry.py:49,318\` упоминают \`src/market_pattern_discovery/backtest/top5_v4/\` как исторический companion/source path. Нужно проверить Git-object-based provenance и условия повтора, а не удалять M15 реестр/протокол.
4. \`ControlCenter/ci/protected-main-tree.json:26,28\` содержит root snapshot \`pyproject.toml\`, \`research_domains.md\`. Снимок — исторический контроль Git дерева, возможно затрагивает CI/acceptance; не переписывать snapshot молча.
5. У 1 325 protected hits большие концентрации: по 157 совпадений в шести M15 исторических JSON списках (в сумме 942); \`recovery/R0_T3_RESEARCH_DRAFT_BLOB_AUDIT_2026-11-20.md\` — 292. Совпадение в manifest ≠ runtime зависимость, но provenance сохранять.

**Точность evidence JSON:** uploaded file \`dependency-report.json\` фактически содержит CRLF и имеет SHA256 \`d947370544f13d317843d879814c7c334094a09e2c37e881f8ba6ed65ed5cfcb\` (убрать пробел перед последним \`b\` при программной проверке); после нормализации CRLF→LF SHA256 \`8e683218f7398d955fb3406193d77d5d6faf08e6f9682203a73cbb122f678d32\`, совпадает с печатью Python. Причина — \`Path.write_text()\` в Windows перевёл LF в CRLF. **Исходный JSON не испорчен**. В сканере исправлено на \`write_bytes(out.encode("utf-8"))\`.
**Дефект V1:** regex \`r"\bbw_system\b"\` фактически ищет \`bw_system\` после word boundary, а не \`bbw_system\`; в отчёте V1 отсутствует \`package:bbw_system\` даже в root \`pyproject.toml\`, где такие ссылки точно есть. Исправлено строгим bounded pattern \`(?<![A-Za-z0-9_])bbw_system(?![A-Za-z0-9_])\`; добавлены два теста на точный match и SHA физического файла. Всего scanner+checkpoint synthetic tests **10/10 PASS**. Поэтому V1 — **не финальная скан-метрика**; нужен \`dependency-report-v2.json\` с исправленным сканером, прежде чем одобрять cleanup.

**Действия:** Не удалять \`audit_only/\`; не переносить в public archive исторические файлы без content/privacy контроля; не изменять TRL/H1/M15/CC snapshots; не делать Merge/LIVE. R7-D grouped-deletion PR разрешать только после triage реального V2 + protected reference rewrite/compat tests и проверки копии на независимом носителе.

## 21.11.2026 — полная очистка main и историческая ветка

Decision ID: R7_FULL_MAIN_REVIEW_ARCHIVE_BRANCH_DECISION_20261121. Аудит расширен с 331 legacy files на все 18 439 tracked paths исходного main; задача — активные и воспроизводимые V20/CC/TRL и необходимые H1/M15 зависимости, методологии, минимальный CI.

**Архитектура:** Один текущий репозиторий, архивная ветка archive/pre-r7-cleanup на SHA f15d565755b996252081ed49ed5a094ee1e8d820, branch status SHA_MATCH; main тот же SHA. GitHub REST protected=false: требуется защита ветки. Ветка не является независимым backup. market-pattern-data не затрагивать. Большой каталог archive/ в main не создавать: только компактный индекс/ссылки при необходимости.

**Gates:**
1. R7-0: доказанная сохранность Git bundle и cold restore (PASS на Intel); подтвердить физический внешний носитель и защиту archive branch; PR/Issues/CI metadata и Git LFS при наличии проверить перед потенциально необратимой очисткой.
2. R7-A-V2: повторный скан isolated checkout исправленным scanner (точный bbw_system, SHA physical bytes), загрузка dependency-report-v2.json; V1 не доказывает закрытие зависимостей.
3. R7-C: whole-repo manifest для каждого tracked пути/sha/mode/размера/назначения; анализ runtime imports, subprocess, PowerShell, workflows, tests, configs, manifests, CLI, frozen research, документации. V1 1012 size-skipped файлов отдельно классифицировать (без исполнения LIVE).
4. R7-D: классифицировать поддеревья KEEP_ACTIVE, KEEP_PROVENANCE, MIGRATE_TEST_FIRST, REMOVE_FROM_MAIN_AFTER_PROOF, HOLD_UNKNOWN; H1/M15/TRL/CC/V20 ссылки на старые пути требуют точной проверки и регрессионных тестов.
5. R7-E: одна согласованная отдельная cleanup branch/PR с физическим удалением доказанно ненужных больших блоков из main; не сотни косметических PR, не rewrite истории Git, не гигантская папка archive/ в main.
6. R7-F: offline тесты, сверка SHA и protected inventory, импортов/путей/исторического provenance в disposable checkout. FAIL = HOLD, устранить сбой до Merge.
7. R7-G: guarded Merge только при всех PASS и отдельном подтверждении оператора; main SHA/tree verify; LIVE/FINAM/Windows Task/реальная торговля вне области уборки.
8. Phase II: три базы знаний Kimi Chat + Kimi Code, проверенный источник, экзамен и GPT↔Kimi handoff. Phase III: независимый Recovery и cold restore строго после Phase II.

Текущий статус: archive branch created SHA_MATCH BUT UNPROTECTED, R7-A-V2 expected, R7-C not started, R7-E delete PR not started, main/LIVE untouched.

## 21.11.2026 — V2 dependency scan: физический отчёт принят и проверен

Evidence: R7_V2_USER_REPORT_VERIFIED_20261121. User ran isolated scanner with head f15d565755b996252081ed49ed5a094ee1e8d820. Actual uploaded file SHA256 = f2bb849da4035042a7209665b9a133fb3652fc20927a0534f0be989aa3f9a16a; stdout SHA MATCH; tracked_tree_modified=false; tree_sha=44a5fef98dd8a3b6bc3e6d172f64fafddac5df4b.

- 18 439 tracked; 16 828 text files scanned; 1 012 skipped >2MB (996 CSV, 14 JSON, 1 TXT, 1 MD). Exactly 331 candidate old-root tracked blobs; no claim they can be deleted.
- 1 979 line-reference hits total: protected_or_entrypoint 1 490, candidate_legacy_bundle 454, other 35. These are **textual lines**, not distinct imports nor proof of runtime use.
- 588 matches for exact package `bbw_system`, of which 491 are from protected_or_entrypoint; 97 from candidate_legacy_bundle. In protected scope 491 hits span only 28 files and are dominated by six historical IntradayLab JSON hash/scope snapshot manifests with 78 lines each. No confirmed live Python import of `bbw_system` identified in this literal report; absence of literal match is NOT dependency closure.
- Specifically 6 protected Python match lines require further inspection: IntradayLab/optimization_registry/audit_registry.py:16, build_registry.py:49,318 refer to historical `market_pattern_discovery` references; TradingSystemLab/stage8_robot/signal_execution_diagnostic.py:22 and tests/replay_stop_tick_grid.py:19,64 refer to audit_only/stop_tick_grid_20261012. TRL reports reference reusable src/market_pattern_discovery/backtest + validation. ControlCenter/ci/protected-main-tree.json contains historical source SHA references.
- **Decision:** V2_SCAN_REPORT=PASS_SHA_AND_READONLY; DEPENDENCY_CLOSURE=NOT_VERIFIED; DELETIONS=BLOCKED. Advance to whole main Git-tree metadata inventory 18 439/18 439, then static owner/runtime/CI/provenance closure and isolated regression tests. Do not publish raw report unless filename/privacy review permits.

## 21.11.2026 — весь main: inventory metadata = PASS

Evidence: R7_WHOLE_MAIN_INVENTORY_VERIFIED_20261121. Operator ran isolated Git-only inventory against f15d565755b996252081ed49ed5a094ee1e8d820. Uploaded JSON SHA256 f3868a4359662bf33804a50847288391a3336753b21e115b985b8f9a63853865 MATCH disk/stdout. 18 439/18 439 tracked blobs classified by path, mode, Git object SHA, byte size, extension and root. `METADATA_ONLY_NOT_DEPENDENCY_CLOSURE_NO_DELETIONS_AUTHORIZED`.

- Total 6,023,678,455 **logical** blob bytes (~6.02 GB); not Git packed size. IntradayLab 14 213 paths (77.08%) / 5,841,504,456 bytes (~96.98%). TradingSystemLab 3 059 paths / 52,334,401 bytes. V20 446 / 53,475,775; ControlCenter 163 / 1,786,283; TradingResearchLab 168 / 1,203,307.
- Major discovery: in IntradayLab/results three historic optimization trees: B high_low_cluster 7 053 paths / ~2,175.74 MB, C return_retest 3 198 / ~1,382.69 MB, A equal_high_low 1 174 / ~597.00 MB. **11 425 paths = 61.96% of main, 4,155.43 MB = 68.98% logical bytes**. They are REQUIRES_REPRODUCIBILITY_AND_EXTERNAL_CALLER_REVIEW, **not** proven redundant.
- Types: CSV 11 954 files, ~5,562 MB; JSON 3 380, ~236 MB; GZ 357, ~118 MB; .u32 4, ~68 MB; Python 1 350, ~13 MB; Markdown 871 ~17 MB. 15 152 distinct Git object SHA vs 18 439 entries: repeated blobs do not prove redundant paths.
- Next step: read-only Git blob grep against exact head to trace references **outside** three candidate result roots, categorize CODE/CONFIG vs RESEARCH/PROVENANCE. Cross-root grep is not full dependency closure (dynamic paths, binary/CSV metadata and external tools can escape). Then preserve reproducibility/test checks and source SHA, only afterward consider grouped deletion PR.
- Status: metadata PASS, dependency closure NOT VERIFIED, physical cleanup PR NOT STARTED, archive branch still UNPROTECTED, main and LIVE UNCHANGED. Do not merge.
