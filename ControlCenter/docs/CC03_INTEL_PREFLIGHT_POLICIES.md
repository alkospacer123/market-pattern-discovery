# CC-03: private policies, existing SID/ACL и утверждение источников

Только подготовка кода: никаких реальных SID/PID/account hash/root pins/TTL в Git. A, B и C из [physical plan](CC03_PHYSICAL_ACCEPTANCE_PLAN.md) независимы. Шаблоны неработоспособны по умолчанию.

## A: policy ограниченного preflight

[preflight-policy.example.json](../deployment/preflight-policy.example.json) содержит false/null и точное имя единственной Task `TradingSystemLab-Stage8-Production`. Runtime читает только `deployment/preflight-policy.json` рядом с проверенной standalone review-копией. Это позволяет A работать без созданных CC accounts/roots. Secure reader проверяет SYSTEM/Admin owner и отсутствие standard-user mutation grants на ancestors/leaf; reparse запрещены. Runtime policy не входит в manifest; оригинал пакета и исходный manifest проверяются независимо. Не выдавать администраторские права observer или ccpanel. Исторический CCExporter в текущем одно-SID плане не используется.

`readonly_preflight_approved` относится исключительно к A. Не создавать `os-policy.json` с `os_policy_approved=true` ради preflight. При отсутствии подходящего existing standard observer token или existing read grants — BLOCKED/UNKNOWN, без изменения Task/H1 ACL.

## Как проверить существующие SID и ACL

1. В отдельном разрешённом operator review сопоставить **существующий** standard observer SID с его токеном; исключить production SID, Administrators (включая deny-only), привилегии/impersonation. Код сам проверяет SID/elevation и Administrators group. Не создавать observer account в A.
2. Для B проверить единственную активируемую стандартную учётную запись `ccpanel`, сопоставить SID с реальным токеном и проверить отсутствие privileged memberships. `ccobserver` и `ccexporter` не использовать и не удалять; этот код не создаёт пользователей. Отсутствующий или Disabled `ccpanel` — BLOCKED до отдельного физического решения. В A `cc_panel_sid=null` честно означает CCPANEL_NOT_PROVISIONED и не мешает независимому Task bracket. Exporter SID в новой policy отсутствует.
3. Для **собственных** existing CC roots (app/venv/data/export/log/private) получить owner/protected DACL и анализ effective rights под настоящими токенами. Не создавать canary и не делать write-test в production. Допустимы только узкие existing-object OS security descriptor/access checks, отдельно перечисленные в решении A; автоматический preflight их не выполняет и оставляет `cc_acl=NOT_VERIFIED`.
4. По [CC03_WINDOWS_SECURITY](CC03_WINDOWS_SECURITY.md) проверить SYSTEM/Admin ownership app/venv/policies; ccpanel Read/Execute app/venv/export, Modify только CC logs, **никакого доступа к private и никакой записи в export**. Exporter не запускается. Проверить ancestors/leaf, наследование, junctions, effective grants. Недостаточные/лишние права блокируют B; исправление только после отдельного одобрения B и только в CC roots.
5. Existing Task Scheduler READONLY grants и exact-PID CIM permissions проверяются фактическим preflight под тем же standard token. Не разрешать Task mutation, SeDebugPrivilege или admin ради зелёного статуса. Никаких H1 filesystem metadata checks: несовместимый observer отключён независимо от ACL.

## Утверждение Task XML/principal

Оператор в рамках отдельно конкретизированного A использует уже проверенное private Task evidence либо независимое разрешённое локальное Scheduler READONLY-наблюдение **ровно одной Task**; без массового GetTasks/process scans. Проверяет action/principal против утверждённого installed checkpoint и сохраняет raw XML только приватно. XML может содержать sensitive arguments — не transcript/raw stdout в общий лог.

Fingerprint = SHA-256 UTF-8 **полной строки** Scheduler `RegisteredTask.Xml`, без XML canonicalization, trim, newline normalization или BOM. Principal `Definition.Principal.UserId` переводится в SID через Windows identity translation. Approved exact digest и SID в policy вносятся независимым оператором после проверки; fingerprint не самоутверждается и не доказывает содержимое executable на диске. Если independent evidence неполно/устарело — не ставить approval true. Before/after должны совпасть; Running допустим, Disabled/HALTED не требуются.

## Process epoch binding

`process_binding=null` — безопасный task-only A. Никакого поиска по имени, дереву, executable basename или автоподхвата нового PID.

Если **раньше независимо подтверждена** связь exact PID с Task worker, оператор вносит объект с ровно такими полями: `process_pid`, `process_creation_sha256`, `process_image_sha256`, `process_command_sha256`, `process_principal_sid`. PID — фактическое число; creation digest — SHA-256 UTF-8 `CreationDate.ToUniversalTime().ToString('o')` от Win32_Process CIM; image — SHA-256 UTF-8 полного `ExecutablePath.ToLowerInvariant()`; command — SHA-256 UTF-8 полной неизменённой `CommandLine`; owner SID — `GetOwnerSid`. Raw command line и пути сохраняются только в private evidence. Никаких environment reads или executable file opens. Один PID не описывает всё дерево wrapper/parent/child и не доказывает worker health.

Идентичность повторно наблюдается existing observer-ом. Новый PID, другой epoch/image/command/SID, завершение, недоступные атрибуты → `PROCESS_UNKNOWN`; новый binding требует отдельного operator review, никакой автоматической перепривязки. Несовпадение Task блокирует preflight до process query. Успешный Task bracket с PROCESS_UNKNOWN возможен, но source C не готов.

## C: private OS policy и receiver policy

[os-policy.example.json](../deployment/os-policy.example.json): false approval, null PID, отсутствующие fingerprints/root IDs. Заполняется **только после** physical A evidence, B isolation и отдельного решения C. В текущей модели одно-SID `Start-Exporter.ps1` отклоняется до обращения к `data/private/os-policy.json`; такой policy не должен активироваться. Для будущего C потребуется новое отдельное решение о безопасном источнике и его ACL, не выдающее ccpanel креденшалы H1/FINAM. Root pin относится только к CC export root; никаких production paths. Metadata false всегда. Пока binding процесса не подтверждён, OS source не утверждать: существующий source-policy validator требует полный pinned process даже при выключенном process source.

[receiver-policy.example.json](../deployment/receiver-policy.example.json): `physical_source_approved=false`, TTL/source/alias/binding null. Source ID/random binding ID/alias выбирает оператор, root pin наблюдает только в **CC-owned** export root после B. Не вставлять account hash: OS source не имеет broker/account authority, `account_binding=UNVERIFIED`. Private OS/receiver policy совпадают по source/alias/binding, обе SYSTEM/Admin-owned и protected; panel видит только receiver.

## TTL: предложения для отдельного рассмотрения C

Конкретных TTL в шаблонах нет. Предложение: сначала измерить длительность one-shot probe, задержку публикации/доставки, допустимый clock skew и отдельно одобрить cadence. Рассмотреть `os_observations TTL = approved cadence + worst observed collection/delivery delay + approved skew budget`; envelope TTL не длиннее самого старого допускаемого OS observation. Оператор может выбрать более строгий срок. Если freshness budget не покрывает измеренный worst case, отказаться от источника/частоты, не повышать права и не нагружать H1. Ни эти формулы, ни test TTL не действующая production policy. Heartbeat/KS/finance TTL остаются null: источников нет.

## Необходимые существующие разрешения A

Read/Execute проверенной standalone копии и Python; READ protected preflight policy и её CC-only ancestors; token QUERY собственного процесса; local Scheduler READ ровно одной Task (XML/principal/state); optional CIM READ exact PID, creation/image/command/GetOwnerSid без privilege enable; exact existing SID translation и directory attributes только фиксированных собственных CC roots. Нет broker/network API, production file READ, Task control, accounts/ACL writes или export writes. Недостающие permissions → UNKNOWN/BLOCKED; нельзя расширять scope автоматически.

## Однозначный контракт A/B после аудита #548

Шаблон A — `cc03.intel-preflight-policy.v2`: ровно прежние поля approval/observer/Task/process и один `cc_panel_sid`; поля `cc_exporter_sid` нет. `observer_sid` обязателен, независимо подтверждается оператором и не выводится из имени ccpanel, его SID или Task. Он может совпасть с отдельно одобренным ccpanel, но не с production principal; это не использование старого ccobserver. Никакая учётная запись не выбирается автоматически.

Совместимый адаптер принимает v1 только при **явно присутствующем** `cc_exporter_sid=null` и всех остальных валидных полях. Он нормализует копию в памяти; ничего не пишет. Ненулевой exporter, неизвестные/недостающие поля или exporter в v2 отклоняются до I/O. Для старой двух-SID policy нужен отдельный operator review и новая protected v2 policy; нельзя автоматически выбрасывать её прежнюю authority. Duplicate JSON keys и нечисловые константы по-прежнему запрещены. Шаблон с false approval/null SID не исполняется.

`Get-CCPanelState` используется A и B одинаково: точное имя **локального ccpanel**, Enabled, совпадение SID, отсутствие прямого членства в привилегированных built-in группах. Перечисление групп/членов недоступно → UNKNOWN, не положительный результат. Исключение имени аккаунта для CI удалено: rehearsal проверяет настоящий одноразовый ccpanel. Это проверка membership, а не полная attestation чужого токена. Фактический primary token A и запуска панели дополнительно отклоняется при elevation/UAC limited token, impersonation или назначенных привилегиях вне узкого списка обычного пользователя (включая disabled powerful privileges). Deny-only Administrators отклоняется отдельно helper-ом; нестандартные группы/права требуют независимого B review, без автоматического исправления.

Отчёт `cc03.intel-preflight-report.v2` разделяет `outcome` A и `cc_installation` B. `CCPANEL_NOT_PROVISIONED`/нет roots → NOT_PROVISIONED; `CCPANEL_DISABLED`, `CCPANEL_SID_MISMATCH`, `CCPANEL_PRIVILEGED` → BLOCKED. `CCPANEL_ENABLED` **не** даёт B PASS: ACL/effective access остаются NOT_VERIFIED до самостоятельной проверки B. A может PASS при заблокированном B; это не C и не источник H1.

Оба фиксированных repository-owned helper (`Read-PreflightReadiness.ps1`, `Read-OsFacts.ps1`) вызываются через Windows PowerShell с `-NoProfile -NonInteractive -ExecutionPolicy Bypass -File` только для дочернего процесса и со scrubbed environment. Это включает точечное решение Draft #545 и распространяет его на второй helper A. Никакого Set-ExecutionPolicy/registry/GPO изменения. MachinePolicy/UserPolicy, AppLocker или WDAC могут по-прежнему запретить выполнение: отказ остаётся BLOCKED/UNKNOWN, такие ограничения не обходятся. Manifest и protected package проверяются перед физическим запуском отдельно; Bypass не удостоверяет код.
