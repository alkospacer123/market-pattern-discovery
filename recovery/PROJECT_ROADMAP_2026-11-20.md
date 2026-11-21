# Trading Systems — Roadmap R7 / Kimi / Recovery, редакция 21.11.2026

**Итоговая последовательность:** Этап I — реальная проверенная очистка `market-pattern-discovery/main` → Этап II — полная адаптация Kimi Chat + Kimi Code с экзаменом и handoff → Этап III — независимый Recovery и реальный cold restore без Intel/GitHub/ИИ. Ранее выполненные R0/R4 и Merge #567/#568/#570/#572–#579 не повторять. Никаких LIVE-изменений без нового отдельного разрешения оператора.

## Архитектурное решение 21.11.2026
- **MAIN:** `alkospacer123/market-pattern-discovery`; сохранение V20, ControlCenter, TradingResearchLab, recovery, необходимых TradingSystemLab/H1 и IntradayLab/M15, .github/CI, методов, исходников и provenance. Устаревший код и десятки тысяч архивных артефактов удалять **из текущего дерева**, но не из Git history.
- **HISTORY:** ветка `archive/pre-r7-cleanup` создана на `f15d565755b996252081ed49ed5a094ee1e8d820` (точное совпадение с main). Защита ветки GitHub пока **OFF**. Эта ветка — снимок до чистки, не независимый backup. Огромный каталог `archive/` в main не создавать.
- **EXISTING SEPARATE ARCHIVE:** `alkospacer123/market-pattern-archive` существует (создан 20.11, основной commit/tree `8d4027c8d53625dfe7780cb7ccfdc354d51b25ba`); в нём есть `historical-prs/`, каталоги и как минимум 19 исторических исходников из закрытых PR. **Не удалять.** Сначала сверить уникальность blobs, refs/PR provenance, privacy и Draft #5. Позже можно выбрать сохранить архив как read-only или объединить уникальное в историю, но только по отдельному решению оператора.
- **DATA:** `market-pattern-data` неизменен; новый GitHub аккаунт, Organization и три кодовых репозитория не создавать.

## Этап I — R7. Полная проверка и реальная очистка

### R7-0. Сохранность и точка отката [PARTIAL PASS]
**Уже выполнено:** исходный main `f15d565755b996252081ed49ed5a094ee1e8d820` совпадал с mirror и с созданной archive branch; Git mirror fsck PASS; Git bundle `439668305 bytes`, SHA256 `09C596CF5E8268256AD4511DE5F28C5E8CA8A823F62867FC9ECF441534D15527`, проверен standalone восстановлением, fsck PASS, **1174/1174 refs, diff=0**. Git history не переписана, main не менялся.
**Осталось до удаления:** включить protection/no force push/no deletion для `archive/pre-r7-cleanup` (текущий protected=false); физическая вторая проверенная копия вне основного Intel/SSD; сохранение metadata GitHub PR/Issues/CI и LFS/артефактов при наличии; отдельная оценка существующего `market-pattern-archive` и его незавершённого PR #5. Это промежуточный checkpoint, не финальные R5/R6.
**Gate:** R7_DESTRUCTIVE=BLOCKED пока любой из перечисленных контрольных пунктов без доказательства. Нет необходимости перекачивать существующий bundle.

### R7-A. Исправленный скан старой root-платформы [V2 PASS; DEPENDENCY CLOSURE OPEN]
- Из isolated checkout получен `dependency-report.json`: `HEAD=f15d565...`, 18 439 tracked, 16 828 scanned, 331 legacy bundle; 1 012 файла >2MB пропущены; 1 325 protected hits, V1 verdict `LITERAL_SCAN_ONLY_NOT_DEPENDENCY_CLOSURE`. Это скан упоминаний, не доказательство отсутствия runtime зависимости.
- Найдены подтверждённые связи: H1 диагностические Python скрипты → `audit_only/stop_tick_grid_20261012`, TRL отчёты → общие `src/market_pattern_discovery/backtest/` + `validation/`, M15 registry → старые paths, CC protected-main-tree.json → исторические root-sha.
- Исправлены regex точного package `bbw_system` и Windows CRLF/SHA256; synthetic tests scanner+checkpoint **10/10 PASS**. Новая версия сканера в #581.
**V2 принят 21.11:** локальный и загруженный JSON SHA256 `f2bb849da4035042a7209665b9a133fb3652fc20927a0534f0be989aa3f9a16a` совпали; HEAD и unchanged-tree PASS; 1 979 total textual references, 1 490 protected, включая 588 `bbw_system` упоминаний (491 в protected). Большая часть BBW protected относится к историческим M15 JSON-манифестам, не к исполняемым импортам. Следующий шаг — R7-B whole-main inventory. Не удалять источники по количеству matches.

### R7-B. Полная инвентаризация всех 18 439 tracked файлов [NOT STARTED]
**Цель:** не ограничиваться 331 файлом. Создать детерминированный `whole-main-inventory.json` / summary на SHA с для каждого файла: path, blob SHA, mode, bytes, owner, purpose, date/provenance/refs, исполняемый или документ/данные, privacy, links/dependencies, предлагаемый класс.
**Техника:** Git ls-files/trees, статический импорт Python/PowerShell/shell/JS, subprocess/importlib, entrypoints, GitHub Actions/workflows, test imports, configs, includes/manifests, dynamic path assembly, symlinks, frozen source paths. Для 1 012 skipped oversized файлов — отдельное безопасное потоковое чтение нужных JSON/MD и регистрация CSV/бинарных доказательств без запуска или доступа к FINAM. Секреты не публиковать, содержимое подозрительных файлов не включать целиком в отчёт.
**Gate:** 18 439/18 439 covered (каждый файл учтён, в том числе skipped/binary с явным reason). Не требовать чтения всех котировок как текста; выборочно проверять воспроизводимость источников.

### R7-C. Карта назначения, зависимостей и архивных решений [PENDING]
Для каждого подсистемного блока: `KEEP_ACTIVE`, `KEEP_PROVENANCE`, `MIGRATE_TEST_FIRST`, `REMOVE_FROM_MAIN_AFTER_PROOF`, `HOLD_UNKNOWN`. UNKNOWN → KEEP до доказательства, историческая ссылка ≠ исполняемая зависимость, но является provenance.
Особый список: V20 три робота и девять патчей R088, старые V20-01–07, CC-03/CC-07, H1/M15 общие исходники, `audit_only` H1 scripts, TRL backtest/validation, отклонённые стратегии, frozen сигналы, текущие тесты, старые большие результаты и источники вне GitHub. Проверить remote CI/Tests и локальные deps отдельно.
**Gate:** таблица `path → callers/imports/runtime/CI/research/provenance/privacy → action → exact SHA → required regression → rollback`, ни одного необоснованного удаления.

### R7-D. Safe cleanup candidate: один согласованный PR [PENDING]
- На отдельной рабочей ветке от заново сверенного main собрать **один связный cleanup PR** с действительным удалением установленных исторических комплексов из main. Не плодить десятки одиночных архивных PR и не создавать огромный archive/ внутри main. Сохранить clean navigation, необходимые исходники и исследовательскую воспроизводимость. Не переписывать историю, branches/tags/PR.
- Действующие целевые деревья защищены: `V20_TradingSystem_M15`, `ControlCenter`, `TradingResearchLab`, `TradingSystemLab` (не весь каталог неприкосновенен, но любое изменение доказано безопасным), `IntradayLab`, `recovery`, `.github`. Файл, который нужен старым офлайн-тестам или воспроизводимому TRL, нельзя удалить без проверенной замены.
- Допустимо исправить документооборот/ссылки/инструкции только при объективной необходимости. Риски live deployment/FINAM/DPAPI исключены. Draft #580/581/582 необходимо согласовать; документационные PR не заменяют cleanup.

### R7-E. Независимые offline регрессии + gate Merge [PENDING]
**До/после:** сохранить и сравнить manifest SHA защищённых исходников, V20 offline tests, CC exporters/operator dry-run только без запусков на рабочих счетах, TRL research reproductions, H1/M15 imports и source provenance, CI/workflow path validity, Python/PowerShell import/test collection. Проверить не только PASS, но и прежние baseline/known FAIL; не требовать незаконного/live network результата.
**PASS:** нет неожиданного изменения сигналов/рисков/FINAM/SLTP/Windows Tasks, защищённые SHA сохраняются либо обоснованный diff+tests, все обязательные тесты PASS, источник восстановим из archive branch/bundle, оператор отдельно разрешил Merge. **FAIL:** НЕ Merge, вернуться к исходному кандидату и выяснить причину.

### R7-F. Merge и верификация чистого main [PENDING]
Merge только после полного R7-0 и R7-E и отдельного явного согласия. Убедиться, что рабочий main реально сократился по files/roles, нет ложных источников для Kimi, история/ref/archived SHA доступны и восстановимы; отдельный отчёт о сокращении `before/after` с исходным `main`. Если cleanup оказался только README — R7_FAIL.

## Этап II — Kimi Chat + Kimi Code [AFTER R7]
Три логических проекта знаний из **одного проверенного рабочего GitHub**, а не три отдельных GitHub: **V20**, **Control Center**, **Trading Research Lab**. Отдельный доступ к архивной ветке только как `ARCHIVE`, не как SOURCE-OF-LIVE. Каждому — START_HERE, frozen/approved rules, branches/SHA, тесты, history/negative results, unknown gaps, no-LIVE contract.
- **R1.1** общая архитектура и первоисточники → **R1.2** V20 + nine-patch R088 → **R1.3** CC/CC-07/read-only boundary → **R1.4** TRL, datasets, TRUE OOS → **R1.5** практический экзамен с проверкой SHA, исходников, offline tests и безопасности → **R1.6** handoff GPT↔Kimi на незавершённой разрешённой задаче.
- **R2** Kimi Code: индивидуальные доступы, branch/PR/CI, audit/review, без FINAM/LIVE; **R3** совместная offline задача, независимая проверка и передача результата. Draft #580 — подготовительные материалы, не доказательство экзамена.
**Gate:** никакого права объявлять систему действующей по одному GitHub; доказать настоящий доступ Kimi Chat отдельно от Kimi Code, тесты и содержательный handoff.

## Этап III — Recovery 10–30 лет [СТРОГО ПОСЛЕ KIMI]
- **R5 Backup:** Git mirrors всех нужных refs, PR/Issues/CI, код V20/CC/TRL/H1/M15 deps, 9 патчей, окружения, воспроизводимые TRL ZIP/XLSX/котировки, принятие/отклонение решений, приватные SQLite/журналы, знания и хронология, инструменты развёртывания. Секреты/DPAPI приватно и с отдельной процедурой перевыпуска. 2 физически независимых защищённых носителя, manifests+SHA.
- **R6 Cold restore:** отдельная машина/ОС без Intel/основного SSD/GitHub/ChatGPT/Kimi, полный запуск офлайн-тестов и восстановление читаемых знаний; без брокерских POST/реальной торговли. FAIL исправить, повторить тест.
- **R8 Приёмка:** отчёты SHA/PASS/FAIL, сценарии отката, долгосрочный lifecycle, права, допущения, обслуживание и письменное решение владельца.

## Контроль рисков и ближайшие действия
1. **Сейчас:** V2 scan SHA PASS, dependency closure ещё OPEN; запустить isolated Git-only whole-main inventory и разобрать JSON; параллельно safe readonly аудит архива.
2. Затем разработать whole-main-inventory 18 439/18 439, выявить крупные исторические комплексы и уже доказанные защищённые зависимости.
3. Подтвердить second copy и archive protection, плюс полноту внешнего metadata до destructive merge.
4. Один cleanup PR, полный offline validation, операторский Merge, затем Kimi и лишь потом итоговый Recovery.
**СТОП:** отсутствие доказанного бэкапа, защищённой исторической ветки, source provenance или регрессий = никакого удаления. Единственный оператор — пользователь. MAIN/INSTALLED/LIVE/RESEARCH/ARCHIVE/RECON не смешивать.
