# CC-03 Intel installation — только план после аудита

**PLAN ONLY / NOT_EXECUTED.** Текущий документированный H1 checkpoint — ARMED generation 62 / Task RUNNING, installed code `3a18c8c24301c866a60f5d725de227288d48f7ec`; это историческое operator evidence, не новый read Intel. Не требовать Disabled/HALTED и не останавливать H1.

Решения строго разделены: **A** — [ограниченный OS READONLY-preflight](CC03_PHYSICAL_ACCEPTANCE_PLAN.md), без установки; **B** — этот план собственных CC identities/roots/app/venv и панели; **C** — [отдельное утверждение OS source/TTL/ACL](CC03_INTEL_PREFLIGHT_POLICIES.md) и первый real export. A не разрешает B/C, B не разрешает C. В текущей задаче ни одно не исполняется на Intel. Legacy production JSON/content/metadata BLOCKED; отсутствует production file access. H1 checkout, Task, ARM, authorization, SQLite/WAL и FINAM не затрагивать.

## 1. Подготовить release и offline wheelhouse на отдельном Windows x64

Поставляемые scripts рассчитаны на Python **3.12 x64**; сам UI/reader поддерживает 3.11/3.12. Для этого installation package выбран один проверяемый вариант 3.12. ExecutionPolicy не ослаблять. Если политика требует подпись — подписать утверждённым способом вне Git, остановиться до её проверки.

```powershell
# В независимом review checkout принятого PR; НЕ установленный checkout робота.
Set-Location .\ControlCenter
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe deployment\manifest.py --check
.\.venv\Scripts\python.exe -m pip download --only-binary=:all: -r requirements.txt --dest wheelhouse
$wheels = @(Get-ChildItem .\wheelhouse -Filter '*.whl' | Sort-Object Name | ForEach-Object {
    @{ name=$_.Name; sha256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant() }
})
ConvertTo-Json -InputObject $wheels | Set-Content .\wheelhouse\wheels.sha256.json -Encoding UTF8
Get-FileHash .\wheelhouse\wheels.sha256.json -Algorithm SHA256
```

Wheelhouse hash manifest проверить по доверенному transfer record; его checksum сам по себе не аутентифицирует wheels. Зафиксировать полные wheel names/hashes и Python version локально. Не включать `.venv`, wheelhouse, секреты, реальные policies или server reports в GitHub. Офлайн перенести пакет и wheelhouse в новый staging root на Intel **только после разрешения**.

## 2. Сначала проверить изоляцию

Только по отдельному решению B в приватном operator transcript определить `$panelSid`, `$exporterSid` двух новых standard accounts. Без robot/admin membership, shared credentials и inherited robot grants. Создание аккаунтов/ACL требует отдельного физического согласования; пакет этого не делает. Подготовить пустые roots и protected ACL по [матрице](CC03_WINDOWS_SECURITY.md). Только SYSTEM/Admin меняют app/venv/policies, exporter пишет только export, panel пишет только logs. Проверить DACL не только roots, но active policy files и всех source ancestors/leaf; проверить effective token/group rights под настоящими SID. Для approved policy WinAPI дополнительно требует owner SYSTEM/Admin и отсутствие write/delete/write-DACL/ownership grants другим SID на policy path/leaf.

Нужны именно отдельные:

```text
C:\TSLControlCenterApp             code + administrator-owned receiver policy
C:\TSLControlCenterVenv            Python venv
C:\TSLControlCenterData\export     immutable completed h1-<time>-<uuid>-<sha256>.json; legacy collection BLOCKED
C:\TSLControlCenterData\logs       только CC logs
C:\TSLControlCenterData\private    private source policy; нет panel grant
```

Существующие H1 checkout/runtime/state/secrets остаются на своих местах. Не предоставлять доступ к H1 runtime, JSON, SQLite или token directories. Для OS source нужны только существующие Task/process OS read grants. Если их недостаточно, оставить UNKNOWN и exporter выключенным; production ACL не менять.

## 3. Preview и install

Из принятого staging `ControlCenter`, под отдельно разрешённым installer identity:

```powershell
.\deployment\Preflight.ps1
.\deployment\Install.ps1
.\deployment\Start-Panel.ps1
.\deployment\Start-Exporter.ps1
.\deployment\Verify.ps1
.\deployment\Uninstall.ps1
# Всё выше выводит PREVIEW; ничего не устанавливает/запускает/читает в H1.
.\deployment\Preflight.ps1 -Execute -PanelSid $panelSid -ExporterSid $exporterSid
.\deployment\Install.ps1 -Execute -PanelSid $panelSid -ExporterSid $exporterSid -Wheelhouse 'C:\CC03Staging\wheelhouse'
```

Ожидается `CC03_PREFLIGHT_PASS_NO_H1_ACCESS`, затем `CC03_INSTALLED_SOURCE_POLICY_UNAPPROVED`. Package manifest проверяется до/после копии; цели app/venv должны быть пусты, roots уже созданы и защищены. Установка только offline `--no-index` wheels; `pip check` PASS. Инсталлятор не применяет ACL, не запускает H1, панель, exporter или службы. При partial install manifest и ownership marker позволяют rollback из staging. Если состояние отличается или файл уже изменён — STOP без перезаписи.

## 4. Первый запуск панели без источника

Под CCPanel, из отдельной консоли, с локально известными SID (не передавать Windows passwords через параметры):

```powershell
& C:\TSLControlCenterApp\deployment\Start-Panel.ps1 -Execute -PanelSid $panelSid -ExporterSid $exporterSid
```

Открыть `http://127.0.0.1:8501`; default DEMO. В READONLY_EXPORT ожидается UNKNOWN без source, а M15 NOT_DEPLOYED и все 10 controls disabled. Start проверяет actual current SID и отсутствие Administrators group; app/venv/export ACL. CORS/XSRF включены, listener только 127.0.0.1. Отдельная elevated readonly консоль:

```powershell
& C:\TSLControlCenterApp\deployment\Verify.ps1 -Execute -PanelSid $panelSid -ExporterSid $exporterSid
Get-NetTCPConnection -LocalPort 8501 -State Listen | Select-Object LocalAddress,LocalPort,State
```

Ожидается ровно один listener 127.0.0.1, `CC03_H1_STATE=UNKNOWN` и `CC03_INSTALL_VERIFY_PASS_PHYSICAL_H1_NOT_ACCEPTED`. Наличие listener не означает HEALTHY H1.

## 5. OS source — только отдельное решение C

После A evidence и B isolation отдельно утвердить exact Task XML/principal и уже проверенную process epoch binding, реальные права CCExporter, root pin **собственного CC export root**, cadence и TTL. Порядок и неутверждённые private OS/receiver templates: [policies](CC03_INTEL_PREFLIGHT_POLICIES.md). Активный `os-policy.json` запрещён без physical evidence и отдельного C. Не читать legacy heartbeat/kill-switch JSON и не получать production metadata/root pins; `source-policy.json` для live content не активировать.

После отдельного C под CCExporter, без admin, допускается будущий один запуск:

```powershell
& C:\TSLControlCenterApp\deployment\Start-Exporter.ps1 -Execute -OsObserver -PanelSid $panelSid -ExporterSid $exporterSid
```

OS export содержит только Task/process observations, metadata UNKNOWN/DISABLED, account binding UNVERIFIED. Панель H1 health/trading/positions/orders/fills/SLTP/finance/PnL сохраняет UNKNOWN. Нет daemon, Task или автоматического cadence. Успешный export не означает CC03_PHYSICAL_PASS. При PROCESS_UNKNOWN источник не утверждать автоматически и не искать новый PID. Отмена C: завершить только собственную exporter console, не удалять evidence/последний snapshot автоматически; stale/unknown TTL закрывает положительные факты.

## 6. Логи, сеть и rollback

Панель и exporter foreground, stdout/stderr остаются в своих консольных сеансах. Для локального CC-only transcript после проверки отсутствия секретов можно использовать `Start-Transcript -Path C:\TSLControlCenterData\logs\panel-<UTC>.txt` / `Stop-Transcript` вокруг запуска панели; exporter оставляет stdout в своей консоли, отдельный operator-owned capture требует согласованного sink; ограничить retention вручную. Не transcript private source inspection/credentials. Диагностические application errors — фиксированные sanitized codes. UNKNOWN искать по manifest/ACL/native API/source age/binding, не читать токены или БД ради диагностики.

Удалённый доступ в будущем: согласованный VPN, доступ к loopback через защищённый tunnel либо authenticated restricted HTTPS reverse proxy, отдельная authentication/RBAC policy. VPN не настраивался. Не создавать public firewall rule для 8501, не bind 0.0.0.0, не отключать CORS/XSRF; Windows admin/FINAM credentials не помещать в приложение.

Rollback из принятого staging, после ручного Ctrl+C **только в консолях панели/exporter**:

```powershell
.\deployment\Uninstall.ps1
.\deployment\Uninstall.ps1 -Execute -PanelSid $panelSid -ExporterSid $exporterSid
```

Ожидается `CC03_REMOVED_OWN_FILES_DATA_RETAINED`. Удаляются только существующие matching manifest files приложения и содержимое marker-bound CC venv после path/ACL/reparse checks. Неизвестные/изменённые app files, active policies, export/log/private data, accounts и root ACL сохраняются для разбора. Никакого H1 Task stop/start, checkout rollback, kill switch change, SQLite restore или удаления production файлов. Если hash/ACL/reparse mismatch — автоматическое удаление прекращается; оператор рассматривает **только CC roots** отдельно. Частичный venv без marker автоматически не удаляется.
