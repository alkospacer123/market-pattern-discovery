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
