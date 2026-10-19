# CC-03: ручное WINDOWS_OS_ONLY в Streamlit — Draft PR #558

Основание: последний комментарий [issue #550](https://github.com/alkospacer123/market-pattern-discovery/issues/550#issuecomment-6276578703).
Начальный/current main: `38489db7e69336548a583f968f13aab49c20913b`.
Все изменения ограничены `ControlCenter/`; workflow не изменён.
**NO DEPLOY / NO MERGE.** Установленная Intel-панель и работающий H1 не изменялись.

## Механизм и исправление

Отдельный `manual_os_refresh()`, включая поток, не равнозначен Streamlit:
script-runner подменяет `sys.modules['__main__']` модулем `app.py`.
Windows `multiprocessing.spawn` перед вызовом native-reader заново исполняет
этот файл через `runpy.run_path(..., run_name='__mp_main__')`. Повторная
инициализация UI оказывается внутри двухсекундного policy-read budget.
Прежний общий `except Exception` превращал отказ в одинаковый BLOCKED/UNKNOWN.

Транспорт reader заменён одним фиксированным вызовом
`sys.executable -I -B <protected windows_file.py>`, без shell, caller-selected
command/module, pickle, Streamlit или импортов H1. Один ограниченный JSON
request передаёт только прежние параметры native-read; stdout возвращает
ограниченные bytes либо `N`. Env исключает Python customization и credentials;
stderr не передаётся в UI. `subprocess.run` убивает и ожидает собственного child
при прежнем timeout 2s. OS process creation/scheduling не является hard real-time.

`WinAPI` и `_read_native` не менялись: local NTFS, admin owner/DACL ancestors/leaf,
held handles, no reparse/hardlink/path drift, root pins, размер и digest сохранены.
Применяется один транспорт для существующих CC-owned read paths. Guard запрета
legacy heartbeat/kill-switch остаётся перед любым открытием их источников.

UI выдаёт только фиксированный этап отказа: `POLICY_READ`, `POLICY_VALIDATE`,
`IDENTITY`, `OS_PROBE`, `OS_VALIDATE`, `GATE`, `SOURCE`; contention —
`MANUAL_REFRESH_BUSY`. Исключение, путь, stack и секреты не отображаются.
При отказе старый positive cache заменяется UNKNOWN. Busy/error не повторяется.

## Native evidence и регрессии

Первый baseline attempt, head `536a8a953530ed8aec16acc645fbac880b17f821`,
[run 39320058292](https://github.com/alkospacer123/market-pattern-discovery/actions/runs/39320058292),
завершился `EDGE_START_TIMEOUT` на private fixture desktop до click. Это отказ
harness, **не воспроизведение source bug**; 485 native full-suite PASS не заменяют
отсутствующее нажатие. Исправлен только CI launcher: браузер использует desktop
runner, сервер/native reader/helper остаются под standard ccpanel; bootstrap
явно применяет loopback/port/CORS/XSRF flags. Edge stderr сохраняется.

Повторный baseline head `2b22f985e0bac35c68c9f5d9c7d8341cce3cd131` также
побайтно сохраняет `app.py`, `cc/`, `observer/` из main:
[run 39322283643](https://github.com/alkospacer123/market-pattern-discovery/actions/runs/39322283643).
Он требует один реальный Edge/Streamlit click → BLOCKED, один policy read и
ноль OS probes; standalone защищённый reader проверяется отдельно.
Фактический baseline verdict и безопасная классификация исключения фиксируются
в PR после завершения, а не выводятся из ожидаемого результата теста.

Финальный harness требует обратного результата: стандартный primary SID
`ccpanel`, действительная admin-owned C policy, ровно один реальный DOM click,
один policy read, один unchanged fixed helper, `TASK_RUNNING`,
`WINDOWS_OS_ONLY`, robot/heartbeat/trading UNKNOWN. CI-only adapter заменяет
только policy location и имя Task на вновь созданный UUID fixture; XML/principal
проверяются настоящим helper, identity/native trust/gates не подменены.
Отдельно проверяется full wrapper в потоке под тем же стандартным SID.
Навигация не добавляет reads/probes; десять trading controls disabled.
Browser result, screenshot и append-only fixture JSONL сохраняются в artifact;
их отсутствие или несоответствие отдельно запрещает native acceptance PASS.

Новые/сохранённые регрессии покрывают:

- native poisoned `__main__`, PYTHONHOME/PYTHONPATH/sitecustomize и paths с пробелом;
- реальное завершение/ожидание child после timeout, bounded protocol и redaction;
- native duplicate/missing/writable-parent/junction policy и parent monkeypatch,
  который не может подменить native child read;
- параллельные clicks, cross-process gate, освобождение после failure/owner exit;
- policy/identity/OS validation faults, UI code этапа без сообщения/секрета;
- старые TTL/clock rollback, one-click/no navigation I/O, no legacy opens,
  500+ producer replacements и synthetic before/after canaries.

Точные final head/tree, run/job, JUnit counts, manifest/ZIP SHA256 и независимое
заключение публикуются в [Draft PR #558](https://github.com/alkospacer123/market-pattern-discovery/pull/558)
после фактического прогона. Это позволяет проверить exact bytes без self-reference
хешируемого manifest. Hosted fixtures не являются Intel physical acceptance.

## Поля и authority

| Поле | Источник / authority | После исправления |
| --- | --- | --- |
| Task | Windows Task Scheduler READONLY; exact canonical XML/principal/state bracket | OS fact, например TASK_RUNNING; не ROBOT_HEALTHY |
| Process | Только approved PID + creation/image-path/command/owner pins | WINDOWS_OS_ONLY либо UNKNOWN; discovery нет |
| source/account/binding | Admin-owned manual C policy | Локальные labels; account/broker UNVERIFIED |
| Время | Отдельные observation/receipt + explicit snapshot/OS TTL | Без переписывания timestamps; expiry/clock failure очищает positives |
| Heartbeat, kill-switch, H1 bars, risk, reconciliation, FINAM, positions/fills/stops/orders/finance | Подтверждённого безопасного источника нет | UNKNOWN; legacy content и metadata DISABLED |
| M15 | Прежний независимый UI | NOT_DEPLOYED |

## Независимый аудит и физический checkpoint

Отдельный агент выполнил независимый read-only code/scope audit и локальный
full-suite: 465 PASS / 53 native-only SKIP. Блокирующих code findings нет.
Замеченная гонка fixture evidence с Windows replace устранена append-only JSONL;
она не переносит polling/retry в product. Окончательный verdict зависит от
независимой проверки final native artifacts и manifest и фиксируется в PR.
Это независимый инженерный audit, не human approval на merge/deploy.

Для Intel сначала нужны отдельный review exact package и разрешение оператора
на контролируемый CC-only rollout. Этот PR не выполняет установку, restart
панели, Task/ACL repair или перепривязку policy. После отдельно разрешённого
rollout оператор использует существующий standard ccpanel и принятую policy:
выбирает WINDOWS_OS_ONLY → один раз «Обновить данные» → сохраняет Task/process,
timestamps и authority; navigation не делает новых probes. UNKNOWN полей робота
и брокера остаётся ожидаемым. Если есть BLOCKED, фиксируется только код этапа;
автоматического повтора, ремонта прав или переключения на live H1 reader нет.
