# CC-03 Intel installation — только план после аудита

> PR #534 audit correction: legacy continuous heartbeat/kill-switch reads are `CC03_LIVE_SOURCE_COMPATIBILITY_BLOCKED` and disabled before file access. Stopped-source evidence does not establish live compatibility. Own export now uses immutable versioned completed JSON files, not replacement of `h1.snapshot.json`. This historical plan does not authorize installation; see [current hosted report](CC03_WINDOWS_HOSTED_ACCEPTANCE.md).

**Не исполнено.** Сначала независимый аудит Draft PR, native Windows security suite и отдельное явное разрешение оператора. Не обновлять production checkout. Только отдельная копия ControlCenter из принятого commit, отдельные identity, app/venv/export/log/private roots. H1 не зависит от панели или exporter. Данный пакет не регистрирует никаких Windows Tasks.

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

В приватном operator transcript определить `$panelSid`, `$exporterSid` двух новых standard accounts. Без robot/admin membership, shared credentials и inherited robot grants. Создание аккаунтов/ACL требует отдельного физического согласования; пакет этого не делает. Подготовить пустые roots и protected ACL по [матрице](CC03_WINDOWS_SECURITY.md). Только SYSTEM/Admin меняют app/venv/policies, exporter пишет только export, panel пишет только logs. Проверить DACL не только roots, но active policy files и всех source ancestors/leaf; проверить effective token/group rights под настоящими SID. Для approved policy WinAPI дополнительно требует owner SYSTEM/Admin и отсутствие write/delete/write-DACL/ownership grants другим SID на policy path/leaf.

Нужны именно отдельные:

```text
C:\TSLControlCenterApp             code + administrator-owned receiver policy
C:\TSLControlCenterVenv            Python venv
C:\TSLControlCenterData\export     immutable completed h1-<time>-<uuid>-<sha256>.json; legacy collection BLOCKED
C:\TSLControlCenterData\logs       только CC logs
C:\TSLControlCenterData\private    private source policy; нет panel grant
```

Существующие H1 checkout/runtime/state/secrets остаются на своих местах. Actual source roots не копировать в docs, брать из независимо проверенного Task binding/операторского evidence. Не предоставлять recursive read H1 runtime или token directory. Если невозможно узкое read двух JSON — STOP exporter, панель DEMO/UNKNOWN.

## 3. Preview и install

Из принятого staging `ControlCenter`, под отдельно разрешённым installer identity:

```powershell
.\deployment\Preflight.ps1
.\deployment\Install.ps1
.\deployment\Start-Panel.ps1
.\deployment\Start-Exporter.ps1
.\deployment\Verify.ps1
.\deployment\Uninstall.ps1
.\deployment\Probe-H1Task.ps1
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

## 5. Подготовить источник отдельно

Только после source/ACL/binding/TTL review локально создать active private `source-policy.json` по неработоспособному example. Передать ожидаемый account **hash**, alias/source/binding references, actual source roots и проверенный installed commit. Политика не создаёт trading authorization. Root IDs получить только metadata API, затем независимо записать в policy (для каждого approved root):

```powershell
# $approvedRoot получен из согласованного приватного evidence; не UI input.
& C:\TSLControlCenterVenv\Scripts\python.exe -c 'import sys; from cc.providers.windows_file import WinAPI; a=WinAPI(); h=a.open(sys.argv[1],True); print(list(a.info(h,sys.argv[1],True)[:3])); a.close(h)' $approvedRoot
```

Команда выполняется из `C:\TSLControlCenterApp`. Ожидается 3 integer NTFS identity, без содержимого файла. Зафиксировать независимо, не угадывать. После записи source policy проверить protected DACL файла: panel нет доступа, exporter Read/Execute, SYSTEM/Admin Full, owner SYSTEM/Admin. `sources_acl_approved`, `installed_commit_verified`, `binding_approved` могут стать true **только после документированных проверок**, не ради прохождения скрипта.

Receiver active policy создать отдельно из `receiver-policy.example.json` в app/deployment: source_id/account_alias/binding_id точно совпадают с private policy. TTL каждого набора пока null; поставить числа только после принятой измеренной cadence; `physical_source_approved` до приёмки false. File owner SYSTEM/Admin, protected DACL, panel/exporter Read/Execute. Активные policies вне manifest, exporter не пишет receiver policy. Политики не делать доступными через браузер.

Под CCExporter (не CCPanel/robot/admin):

```powershell
& C:\TSLControlCenterApp\deployment\Start-Exporter.ps1 -Execute -PanelSid $panelSid -ExporterSid $exporterSid
```

Ожидается один atomic export или `CC03_EXPORT_UNAVAILABLE`; raw path/error/account не выводятся. Запуск one-shot, без daemon/Task/dependency H1. Частота будущих запусков отдельно утверждается; автоматический scheduler не создаётся. Даже успешный export не является PHYSICAL PASS. Если historical heartbeat другого commit, binding не принимается и receiver UNKNOWN; **не запускать H1 ради heartbeat**.

## 6. Логи, сеть и rollback

Панель и exporter foreground, stdout/stderr остаются в своих консольных сеансах. Для локального CC-only transcript после проверки отсутствия секретов можно использовать `Start-Transcript -Path C:\TSLControlCenterData\logs\panel-<UTC>.txt` / `Stop-Transcript` вокруг запуска панели; exporter оставляет stdout в своей консоли, отдельный operator-owned capture требует согласованного sink; ограничить retention вручную. Не transcript private source inspection/credentials. Диагностические application errors — фиксированные sanitized codes. UNKNOWN искать по manifest/ACL/native API/source age/binding, не читать токены или БД ради диагностики.

Удалённый доступ в будущем: согласованный VPN, доступ к loopback через защищённый tunnel либо authenticated restricted HTTPS reverse proxy, отдельная authentication/RBAC policy. VPN не настраивался. Не создавать public firewall rule для 8501, не bind 0.0.0.0, не отключать CORS/XSRF; Windows admin/FINAM credentials не помещать в приложение.

Rollback из принятого staging, после ручного Ctrl+C **только в консолях панели/exporter**:

```powershell
.\deployment\Uninstall.ps1
.\deployment\Uninstall.ps1 -Execute -PanelSid $panelSid -ExporterSid $exporterSid
```

Ожидается `CC03_REMOVED_OWN_FILES_DATA_RETAINED`. Удаляются только существующие matching manifest files приложения и содержимое marker-bound CC venv после path/ACL/reparse checks. Неизвестные/изменённые app files, active policies, export/log/private data, accounts и root ACL сохраняются для разбора. Никакого H1 Task stop/start, checkout rollback, kill switch change, SQLite restore или удаления production файлов. Если hash/ACL/reparse mismatch — автоматическое удаление прекращается; оператор рассматривает **только CC roots** отдельно. Частичный venv без marker автоматически не удаляется.
