# V20-07 — Изолированная установка на Intel, LIVE=OFF

**Roadmap:** V20-07.1–07.4 (не добавлять этапы и подэтапы). Фактический V20-06 READONLY на Intel 24.10.2026 = PASS 3/3; все три новых счёта проверены на `MONEY=PASS`, `POSITIONS=0`, `ACTIVE_ORDERS=0`. Отчёты `C:\V20Lab\readonly-06\ACCOUNT_STATE_REPORT_FUNDED.json` и `BROKER_READONLY_REPORT_FUNDED.json` хранятся только на Intel.

## 07.1: минимальная установка — FIRST INTEL ATTEMPT FAILED (IMPORT OUTPUT QUOTING), FIX PREPARED

`Install-StagingOnly.ps1` — отдельный offline-staging инсталлятор для Intel **URIU-PC, Windows 10 Pro build 19045**, закреплённый source commit `610109b736c53a5cc1025657291e272b1136b254`. Инсталлятор:
- Проверяет наличие локального PASS отчёта 06.4 funded, а также уже установленных H1/M15 исходников для Offline Acceptance в `C:\V20Lab\source-raw` и Python `C:\V20Lab\.venv-raw\scripts\python.exe`. H1 и IntradayLab не обновляет и не перезапускает.
- Использует **sparse** git-fetch exact SHA в новом `C:\V20Lab\staging-07\checkout`: извлекает только `V20_TradingSystem_M15` и не скачивает тяжёлые архивы IntradayLab. Проверяет HEAD и blob `v20_runtime/m15_runner.py`; выполняет безопасный Python import без запуска роботизированного цикла.
- Создаёт `C:\V20Lab\robots\shallow`, `obv`, `inside` с независимыми `config/state/logs/secrets`. Конфиги `config\staging.json` без account_id и токенов; только SHA256 подтверждённой привязки, N4 и `live_enabled=false`.
- Не обращается к FINAM, не размещает заявки, не меняет Windows Task, не запускает стратегию и не трогает H1/M15. Действующий Offline/FakeBroker runner НЕ объявляется LIVE-исполнителем.
- При фактическом PASS пишет локальный `C:\V20Lab\staging-07\INSTALL_07_1_REPORT.json` с перечнем трёх инсталляций. Старые `readonly-06`, `source-raw`, `acceptance-raw` не меняются. Повторно используется уже скачанный **чистый pinned checkout** при точном совпадении remote, sparse scope, HEAD и SHA runner; чужой checkout не переписывается, существующий отчёт не перезаписывается.
- Требуется физический запуск на Intel. Создание скрипта/PR не означает PASS 07.1.

## Дальше ровно по roadmap

- **07.2:** отдельные Windows Tasks `v20-shallow`, `v20-obv`, `v20-inside`, **Disabled**, без торгового исполнения до разрешения.
- **07.3:** H1-подобные `check/start/stop/restart` каждого робота, при этом `start` не снимает ограничение LIVE.
- **07.4:** проверка изоляции, остановленных Tasks, прав, журналов и recovery; итоговый `INTEL_STAGING_REPORT.json`, только после физического подтверждения.

Запрещены запись реальных торговых токенов в PR, LIVE, пробные сделки, изменение H1/M15, сторонние Control Center работы, новые фазы roadmap.

## Факт Intel, 24.10.2026: первый запуск 07.1 — FAIL, минимальный фикс

Операторский stdout: оба git-fetch в `C:\V20Lab\staging-07\checkout` выполнились успешно, checkout `610109b736c53a5cc1025657291e272b1136b254` создан, Python import **фактически прошёл до** попытки `print`, но Windows PowerShell неправильно передал вложенные кавычки в `python -c`: `NameError: name 'PASS_OFFLINE_ONLY' is not defined`. Скрипт остановился по `OFFLINE_IMPORT_FAILED` до создания конфигураций трёх роботов и итогового отчёта. **07.1 НЕ PASS**.

Исправление ограничено `Install-StagingOnly.ps1`: Python делает только import, строка PASS выводится штатным `Write-Output` PowerShell после exitcode=0; существующий чистый checkout переиспользуется, без повторного fetch. Полный импорт не является включением LIVE или запуском торгового процесса. Требуется повторное фактическое выполнение.

**Вторая попытка Intel 24.10.2026:** `V20_07_1_EXISTING_PINNED_CHECKOUT=REUSE`, `V20_07_1_IMPORT_CHECK=PASS_OFFLINE_ONLY`, затем `VariableNotWritable` при присваивании `$home`: Windows PowerShell не различает `$home` и встроенную read-only `$HOME`. До создания `config\staging.json` для первого робота исполнение не дошло, `INSTALL_07_1_REPORT.json` не создан. Адресный фикс: заменить 5 употреблений `$home` на `$instanceDir` только в `Install-StagingOnly.ps1`. Git checkout не скачивать снова, состояние H1/M15 не трогать. Статус **07.1 NOT PASS; SECOND FIX READY / INTEL NOT YET RE-RUN**.

## Факт Intel 24.10.2026 — V20-07.1 PASS 3/3

Повторный запуск на `URIU-PC` подтвердил `V20_07_1_EXISTING_PINNED_CHECKOUT=REUSE`, `V20_07_1_IMPORT_CHECK=PASS_OFFLINE_ONLY`, `V20_07_1_v20-shallow/obv/inside=INSTALLED_LIVE_OFF`, `V20_07_1_RESULT=PASS_STAGING_ONLY_3_OF_3`. Закреплённый checkout SHA `610109b736c53a5cc1025657291e272b1136b254` и локальный отчёт `C:\V20Lab\staging-07\INSTALL_07_1_REPORT.json` подтверждены выводом оператора. FINAM, H1/M15 и Windows Tasks не затронуты. **07.1 CLOSED / PASS**.

## V20-07.2 — три Windows Tasks в Disabled, СКРИПТ ГОТОВ / INTEL NOT RUN

Создан `Install-DisabledTasks.ps1` по штатной H1-схеме `New-ScheduledTask` / `Register-ScheduledTask` / `Disable-ScheduledTask` — **только три новых имени**: `v20-shallow`, `v20-obv`, `v20-inside`. Устанавливаются от текущей учётной записи Windows (локальная `Interactive`-привязка, `RunLevel Limited`, без запроса пароля и без всплывающих окон). Этот тип входа **не означает автономную работу при разлогиненном пользователе**: полноценную независимую учётную запись/хранение секретов/разрешённый LIVE-лаунчер конфигурируем позднее по отдельному разрешению, не подменяя стадийный факт.

Task имеет триггер `AtStartup`, но **действие намеренно только** `C:\V20Lab\staging-07\v20-task-live-blocked.ps1`, которое печатает `V20_TASK_LIVE_NOT_AUTHORIZED` и завершается с кодом 87. Никаких торговых библиотек, токенов, FINAM, заявок. Запуск отключённых Tasks не выполняется; при установке каждый Task сразу переводится в `Disabled`, затем проверяется. При повторной установке уже существующие задачи могут быть только переиспользованы при строгом совпадении Disabled / SID / действия / рабочего каталога; конфликтная задача не перезаписывается.

До установки проверяется локальный PASS `INSTALL_07_1_REPORT.json`, funded 06.4 PASS, pinned Git SHA и три staging-конфига `LIVE=OFF` / `NOT_CONFIGURED`. Фактический отчёт после установки — `C:\V20Lab\staging-07\TASKS_07_2_REPORT.json` (SID, Task principal, action, hash/commit, задачи). Скрипт не затрагивает H1/M15. **07.2 пока НЕ PASS**, пока три `Get-ScheduledTask` реально не покажут Disabled.

## 24.10.2026 — 07.2 первая попытка Intel PARTIAL

Оператор выполнил инсталлятор 07.2 из pinned GitHub. Физический stdout: `V20_07_2_v20-shallow=REGISTERED_DISABLED`, после чего `V20_07_2_TASK_NOT_SAFE_DISABLED` и оболочка `v20_07_2_failed`. Из этого выводится, что установка первых Task-команд дошла до `Disable-ScheduledTask`, но **строгая обратная проверка не пройдена** (не установлено, какое из свойств: State, Action.Args или Principal.UserId). `v20-obv` и `v20-inside` не были обработаны в этом запуске. Итоговый `TASKS_07_2_REPORT.json` не создан. До получения READONLY-диагностики конкретного свойства повторять установку, включать или запускать задачу нельзя. **07.2 НЕ PASS**.

## Диагноз 07.2 по фактической READONLY-проверке Intel 24.10.2026

Оператор подтвердил: Task `v20-shallow` существует, **state=Disabled**, `actions=1`, `exec_match=True`, `args_match=True`, `workdir_match=True`; задачи `v20-obv` и `v20-inside` отсутствуют. Единственное расхождение: сравнение текстового имени Task principal с текущим Windows identity: `principal_match=False`. Текстовое представление principal в Task Scheduler может отличаться от имени текущего пользователя; ослаблять проверку владельца нельзя. Исправлен только validation predicate: преобразовать Task `Principal.UserId` в настоящий Windows SID через `NTAccount.Translate(SecurityIdentifier)` либо проверить готовый SID, затем сравнить с SID текущего пользователя. Если SID другой или не разрешился, установщик останавливается. Совпадающий существующий `v20-shallow` переиспользуется без перерегистрации; затем создаются только отсутствующие Disabled Tasks. Новый фактический запуск ещё не подтверждён. **07.2 PARTIAL / NOT PASS**.

## 24.10.2026 — ФАКТИЧЕСКИЙ V20-07.2 PASS INTEL 3/3

Оператор подтвердил stdout: `V20_07_2_v20-shallow=REUSED_DISABLED`, `V20_07_2_v20-obv=REGISTERED_DISABLED`, `V20_07_2_v20-inside=REGISTERED_DISABLED`, `V20_07_2_RESULT=PASS_3_OF_3_DISABLED`, закреплённый V20 source SHA `610109b736c53a5cc1025657291e272b1136b254`, файл `C:\V20Lab\staging-07\TASKS_07_2_REPORT.json` создан. `V20_07_2_NO_FINAM_NO_ORDERS_NO_LIVE_NO_H1_M15_TASK_MUTATION=YES`. Три Task зарегистрированы в Disabled с блокирующим вместо торгового действия. **V20-07.2 PASS.** Следующий неизменённый подэтап — V20-07.3 операторские check/start/stop/restart, без включения LIVE.
