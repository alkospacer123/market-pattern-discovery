> **CC-03 Windows OS continuation:** отдельный `python -m observer.windows_os` (default PREVIEW), штатные Task/process READONLY API ; metadata source отключён после native interference failure; live JSON не читается. Контракт `WINDOWS_OS_ONLY` не даёт HEALTHY, HALTED, broker или trading authority. [Механизм и ограничения](docs/CC03_WINDOWS_OS_OBSERVER.md), [native evidence](docs/CC03_OS_ACCEPTANCE.md), [будущие источники](docs/CC03_FUTURE_TELEMETRY_SPEC.md), [bounded stop / обслуживание](docs/CC03_EXPORT_MAINTENANCE.md). Production binding и Intel physical NOT_EXECUTED. NO INSTALL / NO TRADING.

# TradingSystemLab Control Center — CC-03 preparation

Автономный бесплатный Streamlit-интерфейс на русском для двух независимых контуров: H1 `T3/H1/TRAIL1` и M15 `T3/M15/SESSION`. По умолчанию **SYNTHETIC / DEMO**; сохранён **OFFLINE_FIXTURE**; добавлен **READONLY_EXPORT** для отдельного очищенного источника. Без принятой policy/exporter он показывает **UNKNOWN**, а не нули или HEALTHY.

**CC-03 — только подготовка кода. Intel не подключался, установка не выполнялась. Раздельная single-SID Windows CI #547 PASS; совместная установка+ручной UI сборка требует собственной CI и независимого review. Реальные Intel ACL и источник — NOT_VERIFIED. NO MERGE / NO AUTO-MERGE.**

H1 frozen identity `TRAIL1__N4_01__FULL__R15`, Stage7 `PROD_STAGE7_46DB784378797C7FB04636892350AFF21006D71A31F2CED9D4B974EDA2DC36B8`, N4 USDRUBF/CNYRUBF/GLDRUBF/IMOEXF, справочный риск 1,5% / max 6% не изменены. Последний документированный Intel installed commit `3a18c8c24301c866a60f5d725de227288d48f7ec`. Историческая запись #532 о HALTED/Task Disabled устарела: согласно утверждённому решению #6241614427 действующий H1 LIVE ARMED/RUNNING. Это операционное указание, не новый server read. Панель обязана подтверждать текущее состояние независимым источником, а без него показывать UNKNOWN. GitHub base `52e167d7b36170f1f639827eb875a57d52175491` не установленная версия H1.

M15 всегда NOT_DEPLOYED / NO_RUNTIME_AUTHORITY, отдельные счёт/риск/runtime. Утверждённый кандидат `T3_M15_T1_TRAIL35_N4_R15`, риск 1,5%/позицию, совокупно до 6%; эта спецификация не подтверждает наличие runtime или LIVE-авторизации. DEMO-M15-A/B — искусственные подписи. Счета, позиции, капитал и риск двух контуров не суммируются. Все **10 управляющих кнопок disabled**, без callbacks. T3 не пересчитывается.

## CC-03: single ccpanel — пакетная подготовка, не разрешение на запуск

Текущая ветка установки использует **один** подтверждённый стандартный Windows SID пользователя `ccpanel`. Подготовленные `ccobserver` и `ccexporter` не удаляются и не используются. `app`, `venv`, `data/export` доступны только на чтение; `data/logs` — на запись; `data/private` — только SYSTEM/Administrators. Панель не получает FINAM или H1 токен. `Start-Exporter.ps1 -Execute` принудительно отклоняется до доступа к политике или источнику. До отдельной проверки защищённого производителя снимков реальные H1-поля UNKNOWN. **Код #546 встроен в этот Draft для совместного CI; без отдельного согласования Intel-установки запуск запрещён.** Испытания в GitHub-hosted Windows не являются Intel physical acceptance.

## Локальный запуск DEMO / OFFLINE_FIXTURE

Отдельная копия только `ControlCenter/`, Python 3.11/3.12 x64; никаких торговых SDK, token, SQLite или market CSV:

```powershell
Set-Location .\ControlCenter
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Открыть `http://127.0.0.1:8501`; Ctrl+C завершает только панель. Запускать из этого каталога: `.streamlit/config.toml` фиксирует loopback, CORS/XSRF enabled, telemetry/file watcher off. Не открывать порт 8501 в интернет; будущий remote доступ только отдельно согласованный VPN/tunnel/authenticated HTTPS proxy. Не помещать Windows admin/FINAM credentials в приложение.

Linux: `python -m venv .venv`, `.venv/bin/python -m pip install -r requirements-dev.txt`, `.venv/bin/python -m streamlit run app.py`. Прямые зависимости закреплены, модели используют stdlib. UI не обновляется автоматически: открытие страницы и переходы между вкладками не выполняют READONLY-проверки. Кнопка «Обновить данные» однократно читает только отдельный CC-owned READONLY_EXPORT; без принятой policy статус UNKNOWN. Внутри одного процесса панели параллельные ручные чтения блокируются без retry; при конфликте показывается BLOCKED/UNKNOWN. Этот lock **не межпроцессный**: перед будущей реальной диагностикой требуется отдельная проверка единственного экземпляра панели и безопасного H1-источника. H1/FINAM/Task кнопка не вызывает.

OFFLINE_FIXTURE читает только `fixtures/h1/h1.snapshot.json`, публичный `FIXTURE-H1`; fixture от `2026-10-15T18:20:00Z` не передатируется refresh-ом, позднее STALE. [CC-02 контракт](docs/H1_READONLY_SNAPSHOT_CONTRACT.md) сохранён; его 180/90/300s пороги остаются тестовыми, не production policy. DEMO/fixture FILL evidence никогда не становится реальным broker fill.

## READONLY_EXPORT

Независимый однократный `python -m exporter.snapshot` по умолчанию выполняет PREVIEW. Непрерывное чтение legacy heartbeat/kill-switch **CC03_LIVE_SOURCE_COMPATIBILITY_BLOCKED** и отключено до открытия source-файлов: безопасный reader мешает неизменяемому `os.replace` producer на Windows. H1 producers не изменялись. Собственный transport ControlCenter публикует неизменяемые версионированные JSON через rename закрытого/fsynced temp-файла в уникальное завершённое имя; панель выбирает последний такой файл в закреплённом NTFS root с проверкой digest, размера, reparse/hardlink и provenance. Доверенная receiver policy должна отдельно задать `export_root_id` (volume/file index triple); без него UNKNOWN. Директория ограничена 2048 entries, автоматическая retention не реализована. Native/startup результаты и остаточные gates — в [Windows отчёте](docs/CC03_WINDOWS_HOSTED_ACCEPTANCE.md). Intel установка не разрешена.

Панель читает этот отдельный фиксированный JSON и administrator-owned receiving policy. Реальные source paths/account mapping/ACL/TTL/cadence/calendar **не приняты**; active policies не поставляются. `.example.json` не активирует источник. На Linux source reader не подключает production. На Windows no-safe-API/ACL/type/reparse/identity/timeout failure → UNKNOWN. Secure backend реализован штатными Windows API, но требует native проверки; Linux mocks её не заменяют.

[Source authority](docs/CC03_SOURCE_AUTHORITY.md) разделяет локальное совпадение binding и broker authority. Checksum — целостность, не подлинность. Даже совпавшая private policy не создаёт fills, positions, SLTP protection, H1 bars, finance/PnL или trading permission: их источники NEEDS_SOURCE_APPROVAL. Новое наблюдение HALTED требует свежего независимого KS read и принятого receiving TTL; старый heartbeat сам по себе нормален. Если старый heartbeat не совпадает с installed commit/binding — UNKNOWN; не запускать H1 ради панели.

## Тесты и будущая Windows installation

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe deployment\manifest.py --check
.\deployment\Preflight.ps1     # только PREVIEW
.\deployment\Install.ps1       # только PREVIEW
.\deployment\Uninstall.ps1     # только PREVIEW
```

Native tests запускать только в disposable Windows sandbox; они меняют ACL/создают junction/hardlink **в pytest temp**, никогда в H1. Отсутствующая среда/привилегия → NOT_VERIFIED. Фактические результаты в [CC03 acceptance report](docs/CC03_ACCEPTANCE_REPORT.md).

[Installation plan](docs/CC03_INTEL_INSTALLATION_PLAN.md) содержит отдельный venv/offline wheelhouse, hashes, низкопривилегированные SID, launch/verify/log diagnostics и ограниченный rollback. Все операторские entrypoints по умолчанию PREVIEW. Пакет не изменяет ACL/Windows Tasks/H1 и не запускает приложение при установке. Физически запускать только после отдельного разрешения.

[Windows security/ACL](docs/CC03_WINDOWS_SECURITY.md) · [Physical acceptance — план](docs/CC03_PHYSICAL_ACCEPTANCE_PLAN.md) · [Architecture](docs/ARCHITECTURE.md) · [Security boundary](docs/SECURITY_BOUNDARY.md) · [Source inventory](docs/SOURCE_INVENTORY.md) · [Roadmap](docs/ROADMAP_STATUS.md).
