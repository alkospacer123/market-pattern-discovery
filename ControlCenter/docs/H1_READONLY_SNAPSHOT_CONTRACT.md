# Контракт H1 READONLY snapshot v1 — CC-02

Нормативная полная схема: [H1_READONLY_SNAPSHOT_SCHEMA.json](H1_READONLY_SNAPSHOT_SCHEMA.json).
Её точное равенство runtime `h1_contract.SCHEMA` проверяется тестом.
[Полный допустимый пример](../fixtures/h1/h1.snapshot.json) — искусственный исторический
снимок, не данные Intel. Схема описывает **принимающую сторону**. Санкционированный
экспортёр не найден/не реализован; изменения H1 для публикации не выполнялись.

## 1. Источники и authority

Проверены исходники GitHub `2695cd3fce6f2241608d1d43d2b7c693ecaba32d`, не runtime:

| Набор | Подтверждённый контракт исходников TradingSystemLab/stage8_robot | Ограничение |
| --- | --- | --- |
| Runtime | `production_safety_gate.py::write_production_heartbeat`: timestamp, accepted_code_commit, account_hash, production_specification_id, active_identity, health_status, reconciliation_status, unresolved_intent_count, position_protection | Heartbeat не содержит последнюю H1/полный decision trace; fault writer публикует пустую protection, которая не доказывает flat |
| Частота | `production_service.py`: DEFAULT_POLL_SECONDS=30, FAST_RECONCILIATION_SECONDS=3; poll configurable 5–3600 | Фактическое расписание Intel UNKNOWN |
| H1 | `production_history.py::close_index_for_frozen_t3`: open timestamp + 1h; runtime expected/continuation history | Expected watermark не доказывает полученную/завершённую свечу |
| Сигналы | `production_runtime.py::build_latest_signal`, pending_signal / last_evaluated_h1 | Отсутствие pending signal не доказывает NO_SIGNAL; полного опубликованного rejection trace не найдено |
| Execution | `state.py`: intents/fills; runtime `entry_fill_history`, matched_quantity / weighted_price_exact | Не импортировать StateStore: constructor пишет schema/state |
| Позиции/SLTP | `production_broker_state.py`: position_quantities / active_sltp_for_trade; heartbeat expected/covered quantity | Локальный stop plan и ACK не являются брокерским доказательством |
| Финансы | `production_service.py::Snapshot`; diagnostics capital/PnL и N4 financial classifiers | Полного периодического финансового экспорта не найдено |

Четыре разные сущности:

1. База GitHub main разработки: `2695cd3fce6f2241608d1d43d2b7c693ecaba32d` (#530).
2. Intel pinned code: `3a18c8c24301c866a60f5d725de227288d48f7ec`, **по операторскому checkpoint в CURRENT_STATE**, физически здесь не проверен.
3. Frozen strategy: T3/H1/TRAIL1, `TRAIL1__N4_01__FULL__R15`, Stage7 spec ниже, N4, 1.5%/6%, прежние margin/lot/rounding rules.
4. Наблюдённый runtime сейчас: UNKNOWN. Последний документированный physical checkpoint — HALTED / Task Disabled / LIVE unauthorized, не свежий heartbeat.

В #528 source `FINAM_FILL_AUTHORITY_VERIFIED=True` означает ограниченный fill-контракт,
**не** торговую авторизацию. В CC-02 никаких gates/permissions не меняется.

## 2. Trust configuration и файлы

Текущая конфигурация скомпилирована в принимающий модуль:
`ControlCenter/fixtures/h1/h1.snapshot.json`. Только этот basename и каталог пакета.
Нет root/path/file параметров в UI/constructor, environment selector или query switch.
Нет production paths Intel. Тесты подменяют root только через pytest monkeypatch.

Источник всегда `OFFLINE_FIXTURE/H1`, scope/alias `FIXTURE-H1`,
`SourceKind.OFFLINE_FIXTURE`, `synthetic=True` (совместимое поле модели: реальные данные
не заявляются). Wire `source_kind` обязан быть OFFLINE_FIXTURE; `synthetic` запрещён
как неизвестное поле. VERIFIED_LIVE_READONLY зарезервирован и отвергается в модели.
Ни JSON `synthetic=false`, ни правильный checksum не создают live authority.
Checksum — целостность/согласованность, **не** подпись и не аутентификация брокера.
Доверие к расположению потребует независимых ACL и sanctioned producer в CC-03.

Reader: максимум **131072 bytes** UTF-8, один JSON object, никаких trailing documents,
NaN/Infinity, duplicate keys или дополнительных ключей на любом уровне. Все поля
схемы обязательны; nullable означает UNKNOWN, не отсутствие ключа. Числа конечные,
не bool/строка; quantities — integer 0–1,000,000; monetary values ±1e12, prices >0;
OHLC проверяется отдельно. Лимиты: ровно 4 уникальных N4 bars, до 32 signals
(текущая v1 — не более одного на инструмент), 64 orders с уникальным reference,
до 4 уникальных positions/stops. Только N4 инструменты.

## 3. Полная структура и allowlist

Точные type/enum/range/nullability каждого поля приведены в нормативном JSON Schema.
Ниже исчерпывающий список ключей, включая вложенные объекты.

| Объект | Разрешённые поля |
| --- | --- |
| Envelope | schema_id, source_kind, complete, payload_sha256, generated_at, observed_at, identity, runtime, reconciliation, bars, signals, orders, positions, stops, finances |
| identity | robot_id, strategy_id, active_identity, production_specification_id, accepted_code_commit, account_alias, account_scope, account_binding |
| runtime | observed_at, state, trading_permission, heartbeat_at, last_successful_cycle_at, source_status |
| reconciliation | observed_at, last_success_at, status, unresolved_intents |
| bars[] | instrument, observed_at, open_at, close_at, time_label, time_source, completed, gaps, quality, calendar, ohlc |
| ohlc | open, high, low, close |
| signals / orders / positions / stops | observed_at, complete, items |
| signal item | instrument, bar_close_at, emitted, direction, rejection_reason, risk_result |
| order item | instrument, occurred_at, reference, state, quantity, filled_quantity, fill_price, evidence |
| position item | instrument, side, quantity, entry_price, price_evidence |
| stop item | instrument, side, quantity, expected_quantity, observed_quantity, broker_status, checked_at, planned_price, evidence |
| finances | observed_at, complete, evidence, equity, realized_pnl, unrealized_pnl, commissions, deposits, withdrawals, available_margin, used_risk_pct, contracts |
| evidence / price_evidence | kind, reference, observed_at, complete |

`schema_id=controlcenter.h1.readonly.v1`, envelope `complete=true` означает полную
структуру снимка; group complete=false означает неполноту фактов в группе.
Никаких raw account/broker/order IDs, free-form logs/errors, токенов, путей,
команд или сырых authorization records. `reference` — scoped 64-hex digest;
UI order ref показывает только 12 символов с prefix fixture-, не raw broker ID.
Evidence kinds только FIXTURE_TRADE_HISTORY / FIXTURE_BROKER_SLTP / FIXTURE_ACCOUNT.
Rejection codes только HALTED / RISK_REJECTED / SESSION_CLOSED / CONDITION_FALSE
или null. Непубликованная причина = UNKNOWN / «Причина не опубликована».

## 4. Identity и account validation

До отображения exact equality:

- robot_id H1, strategy_id T3/H1/TRAIL1;
- active_identity `TRAIL1__N4_01__FULL__R15`;
- production_specification_id `PROD_STAGE7_46DB784378797C7FB04636892350AFF21006D71A31F2CED9D4B974EDA2DC36B8`;
- accepted_code_commit `3a18c8c24301c866a60f5d725de227288d48f7ec` — ожидаемый код по checkpoint, не main;
- account_scope/alias FIXTURE-H1; account_binding = 64 символа `f`, **публичная тестовая константа**, не hash настоящего счёта.

Любой mismatch отвергает **весь** снимок. Binding не показывается в UI и не
вычисляется по секрету в web-процессе. Будущий live profile потребует отдельно
утверждённого alias, проверяемого account-bound producer/evidence и current pinned
commit; изменять production checkout ради соответствия панели запрещено.

## 5. Время, labels и свежесть

Все wire timestamps строго UTC RFC3339: `YYYY-MM-DDTHH:MM:SS[.ffffff]Z` или
`+00:00`, длина ≤32. Naive, неверные даты/offsets и неоговорённая зона отвергаются.
UI показывает UTC и MSK. `received_at` задаёт адаптер, файла с таким ключом нет.
`generated_at` — упаковка, root `observed_at` — последнее наблюдение экспортёра;
все дочерние времена ≤ root observed_at ≤ generated_at ≤ received_at (future timestamps запрещены).
Внутри группы event/evidence ≤ её observed_at. Порядок group timestamps не обязан
совпадать: новая сверка не освежает финансовый отчёт или heartbeat.

| Поле / группа | Тестовая policy CC-02 | Основание / реальные ограничения |
| --- | --- | --- |
| Envelope/runtime observation | 180s | Offline contract publication budget: до 60s + два пропущенных периода; **проектная частота экспортёра**, не установленная Intel |
| Heartbeat / успешный цикл | 90s | Три default production цикла по 30s в исходниках; фактический poll должен быть утверждён CC-03 |
| Reconciliation, orders/positions/stops observation, stop check и evidence | 90s | Broker snapshot связан с production cycle; фактический broker-source cadence не подтверждён |
| Finances observation/evidence | 300s | Только offline policy для независимого account export; периодического production publisher не найдено, live TTL **не утверждён** |
| Завершённая H1 | UNKNOWN | Нет утверждённого exchange calendar/delivery budget; calendar=UNAPPROVED, даже свежий файл не делает свечу актуальной |
| Сигналы | UNKNOWN как current state | Историческое emitted событие отображается с close time; не объявляется свежим решением по таймеру |

Эти TTL **не являются live-конфигурацией**. VERIFIED profile в CC-02 вообще
не создаётся. Неопределённый TTL/календарь оставляет поле UNKNOWN; нет предположения,
что ночью/в выходной должна приходить новая H1. До calendar acceptance отсутствие
свечей не определяется wall-clock часом. `gaps=true`/quality GAP — только явный
экспортированный факт. В будущей policy нужны биржевые перерывы, выходные и праздники,
ожидаемые completed closes и delivery latency отдельно от elapsed time.

Completed bar: time_label=CLOSE; open_at присутствует; close_at=open_at+1h;
completed=true; close_at≤bar observed_at. Одна нормализация open→close делается
экспортёром, адаптер проверяет её и не сдвигает повторно. Не завершённая свеча
отвергается, неизвестная свеча — оба времени null/completed=false/ohlc=null.
Никаких расчётов T3, заполнения gaps или market CSV.

HEALTHY означает только опубликованный runtime health: свежие envelope/runtime,
heartbeat, successful cycle, reconciliation PASS и last_success_at, известный ноль
unresolved. Иначе STALE/UNKNOWN/UNHEALTHY/UNRESOLVED. HALTED не требует живого heartbeat:
после остановки он ожидаемо устаревает; само наблюдение HALTED должно быть свежим.
Task status в v1 UNKNOWN: документированный Disabled не превращается в OS probe.

При stale envelope или unavailable source финансовые числа/позиции/заявки/график/
сигналы не переносятся из прежнего результата. Датированные bar metadata и stop
check/ожидаемое количество могут остаться историческим контекстом с quality/evidence
UNKNOWN. Повторный browser refresh меняет только received_at. Последний HEALTHY
не хранится в cache. Порог DEMO 10s применяется исключительно к SYNTHETIC.

## 6. Достоверность торговых фактов

INTENT, REQUESTED, ACK, POSITION_OBSERVED, FILL_CONFIRMED, UNRESOLVED независимы.
ACK/observed position с fill fields отвергаются. FILL_CONFIRMED требует ненулевых
filled quantity, positive price, quantity≤requested (если requested известно),
свежего complete FIXTURE_TRADE_HISTORY evidence и reconciliation PASS. Без authority
уровень понижается до UNRESOLVED, цена/filled quantity скрываются. Это **тестовое**
доказательство, никогда не реальный broker fill.

Позиции известны (включая 0) только при positions.complete=true, свежем наблюдении
и успешной сверке. Иначе positions/open_positions UNKNOWN независимо от пустого
items. Entry price скрыта без отдельного trade-history evidence; observed position
сама по себе точную цену не доказывает. Финансовый PnL по positions/ACK не вычисляется.

Защита требует полного свежего stop export, broker SLTP evidence/check, соответствия
instrument/side/position quantity, ACTIVE и expected=observed=position quantity>0.
Даже в fixture UI пишет FIXTURE_CONFIRMED, не реальное «защищено».
Planned stop price не переносится в действующий stop/график и не является evidence.
Сырые broker stop IDs запрещены. Нет доказательства гарантированной цены/будущего
исполнения стопа или предельного фактического убытка.

Все финансовые числа скрываются, если finances.complete=false, есть null в обязательных
финансовых компонентах, evidence отсутствует/неправильное/старое, account не совпал
или reconciliation не PASS/устарела. Equity, realized/unrealized PnL, комиссии,
вводы/выводы и margin остаются разными величинами. Прибыль не выводится из equity;
PF/DD/monthly actual performance и trade history в receiving v1 UNKNOWN.
Frozen risk 1.5%/6% — справочная спецификация, не наблюдаемая capacity/разрешение.

## 7. Атомарная публикация и безопасное чтение

Будущий экспортёр обязан собрать согласованный bounded/redacted документ вне
runner critical path, записать во временный файл **в том же каталоге**, завершить
flush/fsync и атомарно переименовать в allowlisted basename. Незавершённые .tmp
никогда не читаются. Структурная полнота не заменяет group completeness.

`payload_sha256`: SHA-256 от UTF-8 JSON **всего** документа без этого ключа;
`sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False`.
Checksum вычисляется после заполнения всех identity/time/completeness/evidence полей.

Reader открывает каждый компонент абсолютного каталога через readonly directory
file descriptor с O_NOFOLLOW; файл через O_RDONLY|O_NOFOLLOW|O_NONBLOCK. Только regular
file, nlink=1, допустимый size. Читает не более MAX_BYTES+1; проверяет dev/inode/size/
mtime/ctime до/после, актуальное имя файла и повторное связывание root. FD закрываются
при ошибке и interruption. Symlink, traversal, hardlink, FIFO, directory replacement
и изменения файла во время чтения отвергаются. Write/create/truncate modes отсутствуют.

На платформе без no-follow descriptor primitives (включая текущий стандартный
Windows os backend) — безопасный UNKNOWN, **без fallback на pathlib.read_text**.
CC-03 обязан отдельно принять Windows handle/ACL implementation либо другой
санкционированный безопасный transport; текущая поставка не заявляет Windows
physical reader PASS. Защита от malicious writer с правом менять доверенный каталог
требует OS ACL; checksum её не заменяет. Read size/iterations ограничены; timeout
недоступного сетевого/production FS не симулируется — такие mounts запрещены.

## 8. Ошибки и изоляция

Обычные Exception, включая RuntimeError/DatabaseError (тестовая инъекция, DB не
открывается), приводят к новому пустому H1 UNKNOWN и единственному безопасному коду
`H1_SNAPSHOT_INVALID_OR_UNAVAILABLE`. В UI/логах нет exception payload или file paths.
Stale допустимого снимка — STALE; failed schema/identity/parse/path/integrity — UNKNOWN.
KeyboardInterrupt/SystemExit проходят наружу после cleanup. M15 всегда обрабатывается
отдельным SYNTHETIC provider, NOT_DEPLOYED/NO_RUNTIME_AUTHORITY. Все 10 controls disabled.

## 9. Условия CC-03 — отдельная авторизация и физическая приёмка

- Утвердить независимый exporter, его реальные источники и nonblocking publication,
  подпись/ACL/transport trust, bind каждой account/order/position/evidence, полноту и redaction.
- Проверить actual Intel checkout/commit, HALTED/Disabled, отсутствие authorization;
  не подменять их GitHub main или документацией. Не менять H1 ради панели.
- Утвердить настоящий account alias/binding, источник broker evidence и access identity.
- Принять Windows secure file handles/reparse/race/ACL поведение или иной transport;
  выделить непривилегированную dashboard identity без токенов и production access.
- Согласовать фактический poll, отдельные TTL, биржевой calendar/session и latency.
- Проверить before/after H1 protected code/SQLite consistency/hash/Task/switch/permissions,
  disconnect/crash/restart/load, ноль order/cancel/rearm; dashboard не gate торгового запуска.
- Лишь после отдельной приёмки добавить VERIFIED_LIVE_READONLY trusted profile в новой
  проверенной поставке. Публичный fixture binding и fixture evidence непригодны для LIVE.

CC-02 PASS — готовность принимающего контракта к следующей проверке, не доступная
телеметрия Intel и не разрешение LIVE. После одного Draft PR STOP; CC-03 не начинается.
