> Current CC-03 OS-only continuation: [independent Windows observer](CC03_WINDOWS_OS_OBSERVER.md). Legacy content remains blocked; Task/process facts never supply heartbeat/broker authority; metadata is disabled after native interference failure.

# CC-03: source authority и отдельные часы

> PR #534 audit correction: legacy continuous heartbeat/kill-switch reads are `CC03_LIVE_SOURCE_COMPATIBILITY_BLOCKED` and disabled before file access. Stopped-source evidence does not establish live compatibility. Own export now uses immutable versioned completed JSON files, not replacement of `h1.snapshot.json`. This historical plan does not authorize installation; see [current hosted report](CC03_WINDOWS_HOSTED_ACCEPTANCE.md).

Основание: [#524 roadmap v1.0](https://github.com/alkospacer123/market-pattern-discovery/issues/524#issuecomment-6198924792), CC-02 merged [#531](https://github.com/alkospacer123/market-pattern-discovery/pull/531). Это подготовка существующего CC-03; физическая часть не исполнена.

GitHub base `52e167d7b36170f1f639827eb875a57d52175491`. Последний документированный Intel installed commit `3a18c8c24301c866a60f5d725de227288d48f7ec`; источник — начало `TradingSystemLab/CURRENT_STATE.md`, операторский checkpoint #528, дополненный merged #532 во время разработки. Между ним и base в TradingSystemLab ровно пять operational Markdown, 100 добавленных строк; IntradayLab не менялся. Main не установленный робот. Последняя запись #532: durable exact-commit/account-bound authorization CREATED, Task Disabled, HALTED, NOT ARMED / NOT RUNNING; отдельного разрешения start/rearm нет. Старое отсутствие authorization в исходном задании и #528-install checkpoint теперь историческое. Это история, не новое измерение.

Важная сверка: последняя запись CURRENT_STATE сообщает source `FINAM_FILL_AUTHORITY_VERIFIED=True` после #528, тогда как ранние комментарии roadmap говорят False. Ничего не переключать для согласования документов. Этот исходный флаг не предоставляет торговую авторизацию и в данной работе не меняется.

## Разрешённая инженерная схема

Отдельный `python -m exporter.snapshot` внутри ControlCenter, отдельный Windows SID. Ни один import торгового проекта, SQLite, FINAM или сетевой клиент не нужен. Только два существующих JSON, каждый в отдельном явно утверждённом root:

| Набор | Проверенный producer / путь относительно runtime | Что действительно означает | Ограничение |
| --- | --- | --- | --- |
| Heartbeat | `stage8_robot/production_safety_gate.py::write_production_heartbeat`; `diagnostics/stage8-12-4-production-heartbeat.json` | schema `stage8_12_4_production_heartbeat.v1`, Stage7, active identity, installed accepted commit, account hash, timestamp, API contact, health, reconciliation и счётчик unresolved | Старый producer timestamp не освежается exporter-ом; не полный decision trace, не broker fill/finance authority |
| Kill switch | `stage8_robot/trading_safety_gate.py::write_kill_switch`; `safety/stage8-trading-kill-switch.json` | schema `stage8_trading_kill_switch.v1`, Stage7, HALTED/ARMED, generation, updated_utc | Новое независимое чтение получает observed_at; старый updated_utc отдельно. HALTED запрещает новые входы, не доказывает остановку процесса/нулевой портфель |
| Task | `deployment/Probe-H1Task.ps1`, только `Get-ScheduledTask` точного имени | Свежая ручная state/UTC-запись без XML/секретов | Автоматическое ingestion **NEEDS_SOURCE_APPROVAL**; process probe не подключён |
| Reconciliation | Поля production heartbeat | Диагностический PASS/FAULT/unresolved на timestamp heartbeat | Локальная сводка, не новые брокерские данные |
| Завершённые H1 | Нет отдельно принятого JSON + календаря | UNKNOWN | Production history находится в SQLite; не открываем и не реконструируем |
| Intent/request/ACK/position/fill/SLTP | Нет принятого опубликованного event stream | UNKNOWN | Не выводим FILL_CONFIRMED или protected из heartbeat counters/protection rows |
| Финансы | Нет проверенного источника cashflows/fees/equity | UNKNOWN | Не считаем PnL по heartbeat/нулевым отсутствующим полям |

Схема только очищенного частичного наблюдения: `CC03_READONLY_EXPORT_SCHEMA.json`. В ней вообще нет финансов, цен, raw account hash, trade/order/stop IDs, путей, свободных errors/reasons. Неизвестные поля, дубликаты ключей, nonfinite, неверные identity/commit/time и oversized JSON отвергаются. Время каждого набора и source enum независимы.

## Привязка и доверие

`source-policy.example.json` намеренно неработоспособен. Активный private policy существует только вне Git: `C:\Control Center\data\private\source-policy.json`. Настройка требует отдельного физического разрешения после аудита. Она фиксирует source ID, публичный неприватный alias вида `H1-…`, случайный несекретный binding reference (64 hex), ожидаемый **уже хешированный** account hash из проверенного heartbeat, установленный commit, root file IDs `(volume,index_high,index_low)` и явные подтверждения проверки commit/ACL/binding. Raw broker account ID/credentials не хранить даже в этом policy. Подтверждение hash/account mapping делается оператором по ранее санкционированному приватному evidence; новый FINAM polling этим exporter-ом запрещён.

Receiver отдельно сверяет source_id/alias/binding_id по administrator-owned `C:\Control Center\app\deployment\receiver-policy.json`, который exporter не может писать. Только `.example.json` входит в release manifest; active policy — отдельный локальный overlay, не Git. До его отдельного утверждения loader возвращает пустую policy, весь receiving runtime UNKNOWN. JSON-флаг `MATCHED_LOCAL_POLICY` — совпадение с локальной привязкой, **не брокерская подлинность**. SHA-256 — только целостность; producer identity определяется ACL, root pin, release provenance и независимой приёмкой.

`FIXTURE-H1` допустим только OFFLINE_FIXTURE. READONLY_EXPORT не принимает fixture alias и не использует его evidence. `VERIFIED_LIVE_READONLY` остаётся запрещённым. Даже после сопоставления локального alias финансы/позиции/стопы/fill остаются UNKNOWN. Политика не разрешает LIVE, orders или rearm.

## Отдельная freshness policy

| Часы | Timestamp | TTL в поставке | Условие будущего утверждения |
| --- | --- | --- | --- |
| Снимок exporter | generated_at | null / UNKNOWN | Согласовать частоту независимых запусков и допустимую задержку |
| Heartbeat | timestamp producer | null / UNKNOWN | Измерить реальную частоту H1, не брать CC-02 90s |
| Task | probe observed_at | null / UNKNOWN | Утвердить независимый probe, права и частоту |
| Kill switch | observed_at нового чтения; updated_at отдельно | null / UNKNOWN | Согласовать интервал наблюдения и root authority |
| Reconciliation | timestamp heartbeat | null / UNKNOWN | Утвердить локальную диагностическую authority и cadence |
| H1-свечи | отсутствует | null / UNKNOWN | Согласовать биржевой календарь, session/holiday/ожидаемые закрытия и безопасный producer |
| Финансы | отсутствует | null / UNKNOWN | Отдельный проверенный источник, account mapping, cashflows и TTL |

Тестовые числа 60/40/20s в unit tests — только synthetic policy tests. Не production defaults. Пока calendar/ожидаемые close не приняты, закрытый рынок не превращается в DATA_GAP. Новый adapter никогда не синтезирует DATA_GAP по часам; старые DEMO/OFFLINE_FIXTURE сценарии сохранены.

HALTED требует свежего независимого kill-switch observation с принятым TTL и совпавшей локальной source/account policy. Старый heartbeat при этом допустим. STALE скрывает актуальную authority; UNKNOWN не означает нули. UNRESOLVED имеет приоритет над спокойным HALTED, если есть свежая диагностическая неопределённость. HEALTHY требует свежие snapshot, heartbeat+API contact, task Running, kill ARMED, reconciliation PASS/zero unresolved; нынешний exporter Task не поставляет, поэтому HEALTHY от него недостижим. Панель не может перевести switch в ARMED.

Если heartbeat отсутствует, старого commit или не подтверждает binding, новый kill-switch файл сам по себе не подтверждает account-bound runtime: состояние остаётся UNKNOWN. Не обновлять heartbeat вручную и не запускать H1 ради зелёной панели.
