# CC-03 Intel: ограниченный физический READONLY-preflight

**PLAN ONLY / NOT_EXECUTED.** Продолжение [#524](https://github.com/alkospacer123/market-pattern-discovery/issues/524). Следующий шаг — только отдельное решение оператора A. Это не CC03_PHYSICAL_PASS и не переход к CC-04.

## Текущий документированный checkpoint

Прочитан верхний handoff `TradingSystemLab/CURRENT_STATE.md` на main `c9dea4e1fb728c97c3c14e70ae75adab6e6cfc94`: установленный executable `3a18c8c24301c866a60f5d725de227288d48f7ec`, T3/H1/TRAIL1, frozen identity `TRAIL1__N4_01__FULL__R15`, Task RUNNING, kill switch ARMED generation 62; торговая авторизация выдана отдельным решением. Последняя независимая операторская физическая READONLY-проверка документирована PASS. Это историческое наблюдение, не гарантия состояния сейчас.

**Не требовать Disabled/HALTED и не останавливать H1.** Условия старого плана о stopped robot, чтении kill-switch/heartbeat JSON, checkout/state/SQLite hashes и token-parent canaries отменены. Их нельзя исполнять как часть этого preflight. Никаких production file opens, metadata handles, git/status/hash в production checkout, SQL/WAL, FINAM или токенов.

## Три отдельных решения

| Решение | Разрешаемый scope | Что не входит |
| --- | --- | --- |
| A — физический READONLY-preflight | Уже подготовленный проверенный standalone CC package, существующий standard observer token, точная Task через локальный Scheduler, необязательный заранее pinned PID, существующие CC SID/roots | Установка, provisioning, изменение сервера/ACL, запуск панели/exporter, OS source approval |
| B — установка Control Center | После отдельного решения: собственные CC accounts/roots/ACL, app/venv, DEMO/UNKNOWN панель | H1 ACL/Task/ARM, source approval, real export |
| C — OS source и первый real export | После отдельного решения: Task/process binding, собственные root pins/ACL, измеренная cadence/TTL, private OS policy и receiver policy, один export | Торговое здоровье, broker authority, production metadata/content, автоматическое расписание |

Разрешения не объединяются. A может наблюдать `CC_IDENTITIES_NOT_PROVISIONED` / `NOT_PROVISIONED`; ничего не создавать. Если standalone package/защищённая конфигурация ещё не доступны в разрешённой операторской зоне, A остаётся NOT_VERIFIED до отдельного решения о подготовке этой зоны; не использовать checkout робота и не запускать installer. Создание CC app/data identities относится только к B.

## Порядок A после отдельного разрешения

1. Независимо проверить принятую revision пакета, SHA-256 manifest и scripts; использовать существующий Python 3.12 x64 в отдельной review-копии. Не обновлять H1 и не устанавливать зависимости на Intel этой процедурой. PREVIEW: `python -m observer.intel_preflight` из корня `ControlCenter`. Он не читает policy, Task, процессы, CC roots или broker.
2. Проверить приватное разрешение A: кто наблюдает, какой exact Task XML/principal, существует ли ранее проверенная process binding, временное окно и запреты. [Порядок утверждения и ACL](CC03_INTEL_PREFLIGHT_POLICIES.md). Нет независимого Task fingerprint → BLOCKED, не угадывать и не включать auto-discovery.
3. В уже согласованной защищённой review-копии оператор готовит `deployment/preflight-policy.json` из шаблона. Это отдельная policy A, не `os-policy.json`. `readonly_preflight_approved=true` допускается только после решения A и проверки provenance Task. Owner SYSTEM/Administrators, весь путь и leaf не writable стандартным пользователям, observer Read/Execute. Не менять права H1. Нет подходящей конфигурации/прав → NOT_VERIFIED/BLOCKED.
4. Под существующим утверждённым standard SID, отличным от production principal, выполнить **только** `python -m observer.intel_preflight --execute`. Elevated или filtered administrator token отклоняется. Код проверяет SID, локальный exact Task XML SHA-256/principal/state, затем опциональный PID, затем повторно тот же Task. Один запуск, максимум три OS subprocess по 6 секунд, readiness 6 секунд, policy read 2 секунды плюс короткое завершение worker. Нет цикла ожидания или нового process binding.
5. Зафиксировать sanitized JSON/stdout и exit code в уже разрешённом private evidence sink; сам preflight не создаёт файлов и ничего не публикует. UTC timestamp в отчёте, операторская запись также UTC+MSK. Raw XML/command line/SID/path не отправлять в GitHub. Не делать вывод о current installed code по совпадению XML: executable attestation не выполнялась.
6. Сохранность определяется только agreement XML fingerprint/principal и Task state между дискретными наблюдениями. Естественный переход state → BLOCKED/UNKNOWN, без вмешательства. Это не непрерывная гарантия отсутствия изменений. Restart/PID reuse/wrong epoch → PROCESS_UNKNOWN, без поиска нового PID. Отсутствующие права → UNKNOWN/ACCESS_DENIED, без исправления production ACL.
7. Existing CC SIDs и собственные фиксированные app/venv/data/export/log/private roots наблюдаются только на существование, roots обходятся без reparse. `EXISTING_*_OBSERVED` не доказывает effective ACL или готовность к установке: `cc_acl=NOT_VERIFIED`; независимый review нужен для B/C.

## Результаты A

`TASK_IDENTITY_MATCHED`, `TASK_RUNNING_OBSERVED`, `PROCESS_IDENTITY_MATCHED` — независимые OS observations. `PROCESS_UNKNOWN`, `ACCESS_DENIED`, `CC_IDENTITIES_NOT_PROVISIONED`, `OS_SOURCE_APPROVAL_REQUIRED`, `UNKNOWN` остаются отдельными результатами.

- **PASS** — только matched standard observer и неизменная identity/state exact Task в bracket. Допускаются Running, Ready, Disabled; менять state не требуется. Process остаётся UNKNOWN, если не привязан/не подтверждён; identities/roots могут быть NOT_PROVISIONED. PASS A не утверждает process source C.
- **BLOCKED** — неправильная identity/token, Task mismatch, Task access denied, изменённая identity/state или непроверяемый standard token. Доступные независимые факты сохраняются; неизвестное не подменяется успехом.
- **NOT_VERIFIED** — PREVIEW, не-Windows, отсутствующая/неутверждённая/недоступная protected policy либо непредвиденная ошибка наблюдения. Никакой физический PASS не заявляется.

`TASK_RUNNING_OBSERVED` никогда не означает ROBOT_HEALTHY, BROKER_CONNECTED, TRADING_AUTHORIZED, POSITION_FLAT или STOP_PROTECTED. Positions/orders/fills/SLTP/capital/PnL/health остаются UNKNOWN без отдельного источника. Kill switch не читается, даже чтобы подтвердить историческую generation 62.

## Остановка и отмена

При отказе прав, drift, timeout или секретах прекратить **только CC preflight** (Ctrl+C его собственной консоли). Не Stop-Process по именам и не Stop Task. A не создаёт accounts/dirs/ACL, не запускает панель/exporter и не требует uninstall. Сохранить sanitized evidence и сообщить оператору blocker; не чинить H1. Отмена B/C описана отдельно в [installation plan](CC03_INTEL_INSTALLATION_PLAN.md). После отчёта A — STOP и новое решение; никакого автоматического B/C.
