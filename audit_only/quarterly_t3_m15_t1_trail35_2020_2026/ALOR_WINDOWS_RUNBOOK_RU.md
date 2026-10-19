# АЛОР M15: запуск на отдельном Windows-компьютере

**Из Codex получен только CONNECT 403. Ни одного ответа АЛОР не получено. Загрузчик проверен автономными синтетическими тестами на Python 3.12, но ещё не проверен на реальном API и на Windows.** Успех на вашем компьютере заранее не предполагается.

Используется только `https://api.alor.ru` и два публичных GET: `/md/v2/Securities` и `/md/v2/history`. Нет токенов, входа в счёт, FINAM, торговых команд или фоновых задач. Запускать на обычном отдельном ПК; **не на торговом Intel-сервере**. Не менять настройки роботов и не создавать Scheduled Tasks.

## 1. Проверить Python 3.12 и получить файлы

Открыть обычный PowerShell. Python 3.12 должен быть установлен с Python Launcher (`py`); установка библиотек не требуется.

```powershell
py -0p
py -3.12 --version
if ($LASTEXITCODE -ne 0) { throw 'Установите Python 3.12 с python.org и Python Launcher, затем повторите.' }

$ScriptDir = Join-Path $env:USERPROFILE 'Documents\AlorM15Tools'
$DataDir = Join-Path $env:USERPROFILE 'Documents\AlorM15Data'
New-Item -ItemType Directory -Force -Path $ScriptDir, $DataDir | Out-Null

$Source = 'https://raw.githubusercontent.com/alkospacer123/market-pattern-discovery/codex/audit-quarterly-m15-t1-trail35-2020-2026/audit_only/quarterly_t3_m15_t1_trail35_2020_2026'
$Files = @('download_quarterly_m15_alor.py', 'test_alor_downloader.py')
foreach ($Name in $Files) {
    $Destination = Join-Path $ScriptDir $Name
    if (Test-Path -LiteralPath $Destination) { throw "Файл уже существует: $Destination. Сохраните прежний комплект или выберите новую папку." }
    Invoke-WebRequest -Uri "$Source/$Name" -OutFile $Destination
}
$Expected = @{
    'download_quarterly_m15_alor.py' = 'c5479798f2347f553ad71fd55920e7fc3638010cd42683305f98a6b806824164'
    'test_alor_downloader.py' = 'c22fc7279d88c1c780cdf4d247de70be1a8c296b2ade3ed86a0ca5c759f106f0'
}
foreach ($Name in $Files) {
    $Actual = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $ScriptDir $Name)).Hash.ToLowerInvariant()
    if ($Actual -ne $Expected[$Name]) { throw "SHA256 не совпал: $Name. Ничего не запускайте; получите актуальный комплект из PR #556." }
}
Set-Location -LiteralPath $ScriptDir
py -3.12 -m unittest -v test_alor_downloader
if ($LASTEXITCODE -ne 0) { throw 'Автономные тесты не прошли.' }
```

Оба исходных файла также доступны для отдельного скачивания из Draft PR #556. После сохранения выполнить проверку SHA256/тесты из команд выше. Данные всегда хранить отдельно от Git checkout. `$DataDir` не должен быть внутри research/data-репозитория.

## 2. Запустить только пилот

```powershell
$Downloader = Join-Path $ScriptDir 'download_quarterly_m15_alor.py'
py -3.12 $Downloader --mode probe --output-dir $DataDir 2>&1 |
    Tee-Object -FilePath (Join-Path $DataDir 'probe-console.log')
$ProbeExit = $LASTEXITCODE
Write-Host "Код завершения пилота: $ProbeExit"
```

Пилот ищет метаданные Si/GD/CNY через публичный `/md/v2/Securities`: канонический датированный символ, MOEX/FORTS, RFUD, futures type и CFI. Строки вроде `Si-3.20` используются только как **поисковые кандидаты**; история запрашивается лишь после ответа с подходящими метаданными. Вечные, мини-контракты и похожие активы не принимаются. Приватные карточки инструментов не вызываются.

Затем проверяются Si/GD 9–10 января 2020, 2–3 апреля 2024 и 1–2 сентября 2026; CNY 2024/2026 и первое найденное реальное окно самого раннего подтверждённого в поиске контракта. Это не доказательство истинной даты запуска CNY или самой ранней хранимой истории. Если старый контракт не найден публичным поиском, его символ не подставляется по догадке.

Каждая положительная выборка должна содержать смежные M15. Один дополнительный запрос каждой такой выборки нужен для сравнения неизменности OHLCV; он помечен `replica=true`. При возобновлении сохраняются обе исходные копии, новые повторы не выполняются.

## 3. Посмотреть результат

```powershell
$ProbePath = Join-Path $DataDir 'probe_result.json'
if (Test-Path -LiteralPath $ProbePath) {
    $Probe = Get-Content -Raw -Encoding UTF8 -LiteralPath $ProbePath | ConvertFrom-Json
    $Probe | Select-Object status, calendar_completeness, retention_limit | Format-List
    $Probe.samples | Select-Object label, status, contract, rows | Format-Table -AutoSize
}
$ErrorPath = Join-Path $DataDir 'last_error.json'
if (Test-Path -LiteralPath $ErrorPath) {
    Get-Content -Raw -Encoding UTF8 -LiteralPath $ErrorPath
}
```

- `PASS`: все девять выборок проверены; это ещё не подтверждение полного архива.
- `PASS_AVAILABLE_PARTIAL`: свежие Si/GD/CNY и первое найденное окно CNY прошли, но Si/GD 2020 не подтверждены. Допускается скачивание реальной доступной части с явной неполнотой.
- Любой другой статус: массовая загрузка заблокирована. Сохранить каталог и передать результат Codex. Не редактировать JSON ради получения PASS.

`HTTP200_EMPTY_NOT_PROOF_OF_DELETION` означает пустой ответ, а не доказательство удаления архива. `METADATA_NOT_FOUND` означает отсутствие подтверждения в публичном поиске, а не отсутствие контракта на бирже. Токены запрашивать не нужно. Если API требует авторизацию, этот путь останавливается.

## 4. Запустить загрузку после успешного пилота

```powershell
$Probe = Get-Content -Raw -Encoding UTF8 -LiteralPath (Join-Path $DataDir 'probe_result.json') | ConvertFrom-Json
if ($Probe.status -notin @('PASS', 'PASS_AVAILABLE_PARTIAL')) { throw 'Сначала нужен успешный пилот.' }
py -3.12 $Downloader --mode download --output-dir $DataDir 2>&1 |
    Tee-Object -FilePath (Join-Path $DataDir 'download-console.log') -Append
Write-Host "Код завершения загрузки: $LASTEXITCODE"
```

Даты по умолчанию: 01.01.2020–19.10.2026 включительно по Москве, с ограничением по завершённым свечам и 15-минутной задержке анонимного API. Последняя граница фиксируется в `settings.json` при первом запуске. Смещение UTC+03 корректно для Москвы во всём этом периоде; отдельный пакет tzdata на Windows не нужен.

Загрузка последовательная, не чаще одного нового запроса в секунду, история порциями до семи дней. BR/NG проверяются по всем месяцам. Публичный поиск может не выдавать истёкшие инструменты: `includeOld` относится к приватному endpoint и здесь не применяется. Отсутствующие контракты остаются пробелами. Даты первых торгов/экспирации не выводятся из имени. `cancellation` хранится отдельно как дата завершения по АЛОР.

Если дата первых торгов неизвестна, запрашивается часть общего периода до provider completion + одного дня; поэтому много пустых интервалов и длительная загрузка возможны. Лимит — 20 000 **новых** GET за один запуск. При исчерпании бюджета повторить ту же команду: успешные URL берутся из кэша без сети. Изменение дат/шага порций требует нового выходного каталога и пилота.

После сетевого сбоя/HTTP-ошибки автоматического retry нет. Исправив доступ, разрешить новую попытку явно:

```powershell
# Выбрать тот режим, на котором произошла ошибка:
py -3.12 $Downloader --mode probe --output-dir $DataDir --retry-failed
# После нового успешного пилота, если сбой был в загрузке:
py -3.12 $Downloader --mode download --output-dir $DataDir --retry-failed
```

Старые попытки сохраняются, успешные не повторяются. Для 429 соблюдается Retry-After; при неистёкшем сроке команда остановится. Не повторять 401/403 поставщика ради обхода доступа. Статусы прокси и поставщика различаются в receipt.

Обычный Ctrl+C сохраняет доступные receipts. При аварийном завершении может остаться `.downloader.lock` или незавершённый `attempt-*`: скрипт остановится. Убедиться, что Python-процесс завершён; сохранить копию каталога. Lock можно удалить только после этой проверки. Незавершённую попытку не исправлять вручную — передать её Codex для проверки; подтверждённые исходные ответы не перезаписывать.

## 5. Проверить manifest и сырые файлы без сети

```powershell
py -3.12 $Downloader --mode verify --output-dir $DataDir
if ($LASTEXITCODE -ne 0) { throw 'Проверка SHA256/схемы не прошла. Сохраните файлы и передайте Codex ошибку.' }
$Manifest = Get-Content -Raw -Encoding UTF8 -LiteralPath (Join-Path $DataDir 'manifest.json') | ConvertFrom-Json
$Manifest | Select-Object status, calendar_completeness, actual_retention_limit, strategy_replay | Format-List
$Manifest.coverage_by_market_year | Format-Table market, year, distinct_contract_bars, state -AutoSize
$Manifest.contracts | Select-Object market, alor_symbol, board, provider_cancellation_utc, first_trade_utc, expiry_utc | Format-Table -AutoSize
```

`verify` проверяет исходные байты и схему, не доказывает биржевую полноту. Годовые counts — свечи **отдельных контрактов**, а не склеенная серия или число сделок стратегии. Для отсутствующей истории стоит NO_DATA/null. Наблюдаемые разрывы могут быть торговыми перерывами. Маркировка времени свечи как Open требует последующей независимой сверки. Автоматическая сверка с continuous H1/M30 некорректна без правил их склейки; она оставлена для аудита после передачи данных.

Структура каталога:

- `requests/<hash>/attempt-*/response.json` — неизменённый ответ, включая HTTP-error body, если он получен;
- `request.json`/`receipt.json` — URL, UTC-время, код ответа, размер, SHA256 и тип ошибки;
- `settings.json` — неизменные границы и параметры; `contracts.json` — подтверждённые метаданные;
- `probe_result.json`, `manifest.json`, `last_error.json` — последние производные отчёты; все прежние версии сохраняются в `reports/`;
- `chunks/` — checkpoints; raw данные никогда не перезаписываются.

## 6. Подготовить архив для возврата в эту задачу

```powershell
if (Test-Path -LiteralPath (Join-Path $DataDir '.downloader.lock')) { throw 'Сначала дождитесь окончания загрузчика.' }
$Archive = Join-Path (Split-Path -Parent $DataDir) 'alor_m15_for_codex.zip'
if (Test-Path -LiteralPath $Archive) { throw 'Архив уже существует. Сохраните его или выберите новое имя.' }
Add-Type -AssemblyName System.IO.Compression.FileSystem
[System.IO.Compression.ZipFile]::CreateFromDirectory($DataDir, $Archive)
Get-Item -LiteralPath $Archive | Select-Object FullName, Length
Get-FileHash -Algorithm SHA256 -LiteralPath $Archive
```

Передать архив и его SHA256 **в этот чат**, сообщив статус пилота и загрузки. Даже заблокированный/частичный результат полезен: нужны исходные ответы и receipts. Если архив превышает лимит вложения, сначала передать `manifest.json`, `probe_result.json`, `contracts.json`, `last_error.json` и размер полного архива; затем согласовать передачу оставшихся байтов. Не публиковать котировки в GitHub PR #556, другом публичном репозитории или GitHub Actions.

После приёма Codex продолжит аудит данных и только при достаточном подтверждённом покрытии — frozen replication/replay. Сам загрузчик не исполняет стратегию, не строит склейку и не рассчитывает доходность. Обновляется существующий Draft PR #556; merge и auto-merge запрещены.
