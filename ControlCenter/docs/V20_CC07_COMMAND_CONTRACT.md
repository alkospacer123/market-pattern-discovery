# CC-07 — действующий контракт команд (SOURCE, 22.11.2026)

**CODE AUTHORITY:** `v20_app.py` → `v20_admin_control.py` → `controller/cc07-v20-operator.ps1`. Срез MAIN: `0e569be6cb3c7cce1f7224e7f1fef6be38f6ba52`. Документ НЕ разрешает живое управление. Историческая физическая приёмка — [CC-08](V20_CC08_OPERATIONS.md).

## Команда → подтверждение → эффект по коду

| Команда | UI | Требуемая логика stock/PS |
|---|---|---|
| PAUSE | Одно нажатие (адаптер генерирует точную фразу) | Штатный V20 `stop`: HALT новых входов, worker не отключается |
| START | Второе «Подтвердить» | V20 `start`, проверка итогового ARMED |
| STOP | Второе подтверждение | V20 `stop` (HALT) → **повторный FINAM FLAT** → `Stop-ScheduledTask` → Task не Running |
| RESTART | Второе подтверждение | Stock V20 `restart`, FLAT-gate и итоговый ARMED |
| RECOVER / ВОССТАНОВИТЬ | Второе подтверждение | Только проверенный HALTED/FAIL; stock `start`, без очистки V20 durable HALT/журнала |

Панель не вызывает operator при загрузке, переключении вкладок или одном лишь открытии диалога подтверждения. Admin adapter запускает фиксированный PowerShell в `-mode execute` с exact confirmation `cc07 <action> <robot> <request_id>` через STDIN. Для четырёх действий, кроме PAUSE, создаёт однократный private `cc.v20.release.v1` с identity, SID и временем до 90 секунд; PowerShell независимо проверяет фразу и release.

## Защита до выполнения
1. Admin adapter: Windows `URIU-PC`, административный контекст, pinned operator blob `10de325be0335733a248c412943f39d45bd93c62`, установленная private gateway-policy с `approved=false` (одновременный второй channel не допущен). `admin_ready` — только read-only readiness.
2. PowerShell: PIN собственного и stock operator, allowlist **точных** Git blobs V20 launcher (включая установленный ранее `e1de4aad7a98cdc84768c1811131c3ad079d7d90`), отсутствие reparse, trusted ownership/ACL; actor SID должен совпасть с principal SID Windows Task. Mismatch → отказ, не отключать SHA/pins.
3. Stock `-mode check`: строгое READONLY banner, согласованные Task/switch/cycle/age/code. Для Running обычный предел свежести 90 c, для `MOEX_CLOSED_PROTECTED_MONITOR` — 180 c. Есть строго описанные исключения для HALTED/Ready; неизвестное состояние не заменять «готово».
4. Для всех действий **кроме PAUSE** stock launcher `-mode readonly` должен подтвердить `positions=0` и `active_orders=0`. Это preflight внутри V20, а не независимая внешняя проверка брокера. Для STOP повторить FINAM FLAT **после HALT и до остановки Task**. При отсутствии proof отказ.
5. Один global mutex; проверка уникального request ID относительно audit, лимит размера журнала, защищённое append-only `C:\Control Center\data\control-audit\v20-control.jsonl` (`cc.v20.audit.v1`). Phases `began` / `finished` и при инциденте `unknown_outcome_reconcile_manually`.
6. После stock action — ограниченное наблюдение `-mode check` с максимум 12 попытками (оно **не повторяет** команду). Отсутствие однозначного postflight → неизвестный результат.

## Когда RECOVER обязан отказать

`recover` принимает только Running/Ready с HALTED switch, ожидаемым частичным stock health (`HEALTH_PARTIAL`, exit 1), типизированным cycle HALTED/FAIL и проверенным кодом. Для HALTED допустим ожидаемый `HALTED_NO_NEW_ENTRIES`; для FAIL — строгий `HALT_/FAULT_/FINAM_…`. Для Running/HALTED нужен свежий cycle не старше 90 с. Дополнительно: FINAM FLAT, PIN/SID/ACL/release, а сам V20 **не должен отвергнуть** re-ARM из-за durable execution_halt. Если switch уже ARMED, неверный/старый код или нет FLAT — `REFUSED`. Исторический `cc07_recovery_switch_not_halted` означает корректный защитный отказ, НЕ успешный RECOVER в настоящем инциденте.

## Результат и ручная реакция

| Исход UI/адаптера | Интерпретация |
|---|---|
| `EXECUTED` / `ALREADY_HALTED` | Подтверждён локальный результат, брокерские SLTP/позиции по нему не подтверждены |
| `REFUSED_PREFLIGHT` | Отказ до подтверждённого исполнения; устранять источник, не обходить защиту |
| `FAILED_UNKNOWN` / «Результат не подтверждён» | **НЕ ПОВТОРЯТЬ.** Отдельно проверить Task/switch, `v20-control.jsonl`, FINAM positions/orders/SLTP доступной разрешённой READONLY-процедурой |

После dispatch неполный stdout, timeout или ошибка дают `FAILED_UNKNOWN`, а не PASS. Не тестировать START/PAUSE/STOP/RESTART/RECOVER на реальных роботах ради документации.

**Не путать** с альтернативным `v20_command_channel.py`/`cc07_command_worker.py` (другой PIN, transport, нет RECOVER): текущий `v20_app.py` этот channel не импортирует. Реальная установка gateway **NOT_VERIFIED**; переключение на него требует отдельного проекта/приёмки.
