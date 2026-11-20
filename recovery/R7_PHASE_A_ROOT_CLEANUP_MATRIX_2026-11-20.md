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
