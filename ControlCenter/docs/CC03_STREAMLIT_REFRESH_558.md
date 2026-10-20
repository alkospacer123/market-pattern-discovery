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
Прежний общий `except Exception` превращал любой отказ в одинаковый BLOCKED/UNKNOWN.
Это свойство spawn само по себе не доказывает конкретную причину физического
сбоя: оба baseline — обычный и с production flags — успешно прошли, как указано ниже.
Причина физического Intel BLOCKED остаётся неподтверждённой.

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
Он действительно выполнил один DOM click, но исходный reader вернул
`TASK_RUNNING`: accepted=true, reads=probes=clicks=1, read_seconds=1.171.
CI завершился FAIL из-за отрицательного ожидания теста; это **опровержение
универсального сбоя spawn в Streamlit**, а не воспроизведение BLOCKED.

Следующий baseline использует те же `-I -B`, что production Start-Panel:
head `a06d6a84eeec085ea0bc580c415dd76aa638d6fa`,
[run 39323941657](https://github.com/alkospacer123/market-pattern-discovery/actions/runs/39323941657).
Его runtime также побайтно main; фиксированный CI bootstrap лишь подготавливает
synthetic policy/UUID Task и запускает настоящий app.py с этими flags.
Фактический click также accepted=true / TASK_RUNNING; reads=probes=clicks=1,
read_seconds=1.703, server_isolated=server_no_bytecode=true. CI FAIL вновь вызван
отрицательным ожиданием теста, а не отказом reader.

Candidate без нагрузки успешно прошёл native acceptance:
[run 39322603937](https://github.com/alkospacer123/market-pattern-discovery/actions/runs/39322603937)
и с точными `-I -B` flags
[run 39324054902](https://github.com/alkospacer123/market-pattern-discovery/actions/runs/39324054902).
Первый: 503 full-suite PASS / 15 platform SKIP, read_seconds=0.266; все
existing native gates и 500 producer replacements / zero errors / zero legacy opens PASS.
Последняя пара проверяет дополнительную timing-гипотезу при неизменном timeout 2s:
в disposable runner запускаются ограниченные CPU-only children (не более 45s),
а исходный full wrapper напрямую и в потоке под тем же standard SID должен
сначала вернуть TASK_RUNNING под той же нагрузкой. После этого выполняется один
реальный Streamlit click. Искусственных задержек внутри reader и уменьшения
timeout нет; children завершаются/ожидаются в finally. Если control не проходит,
это не считается воспроизведением source-specific failure. Даже возможный
READ_TIMEOUT в таком тесте не доказывает причину физического Intel отказа.

Финальный harness использует тот же isolated launcher и требует: стандартный primary SID
`ccpanel`, действительная admin-owned C policy, ровно один реальный DOM click,
один policy read, один unchanged fixed helper, `TASK_RUNNING`,
`WINDOWS_OS_ONLY`, robot/heartbeat/trading UNKNOWN. CI-only adapter заменяет
только policy location и имя Task на вновь созданный UUID fixture; XML/principal
проверяются настоящим helper, identity/native trust/gates не подменены.
Отдельно проверяется full wrapper в потоке под тем же стандартным SID.
Навигация не добавляет reads/probes; десять trading controls disabled.
Проверяется конкретная rendered строка Windows Task: TASK_RUNNING,
которая прокручивается в screenshot; статический caption не считается доказательством.
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
