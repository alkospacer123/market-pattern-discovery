# Инвентаризация потенциальных источников — CC-00

CC-02: повторно проверено наличие и содержание исходников на фактическом GitHub main
`2695cd3fce6f2241608d1d43d2b7c693ecaba32d` (#530). PR #529 MERGED,
merge commit `5d1eb30ec0b525e6da34963287cecf5fa23edf76`.
Intel pinned code по последнему операторскому документу — `3a18c8c24301c866a60f5d725de227288d48f7ec`,
не этот GitHub main. Frozen identity отдельна от обоих code SHAs; текущий
наблюдённый runtime UNKNOWN. Последний документированный checkpoint HALTED / Task
Disabled / LIVE unauthorized не является свежей телеметрией. Source fill gate #528
True не означает разрешение LIVE; исторические False ниже не текущая code authority.

[Roadmap / authority](https://github.com/alkospacer123/market-pattern-discovery/issues/524#issuecomment-6198924792).

**Доступа к Intel, Windows Tasks, production SQLite, runtime JSON/logs или FINAM не было.**
Ни один runtime-файл фактически не прочитан и ни один live-источник не подтверждён.
Указание «код есть» не означает «источник сейчас существует/обновляется на Intel».
CURRENT_STATE.md — датированный операторский отчёт, не live-телеметрия.
Последний checkpoint: H1 HALTED / Task Disabled / trading unauthorized.
M15 OOS PASS принят как сообщение оператора; production spec из research не выводится. Новый документ
`IntradayLab/SELECTED_T3_M15_SESSION_T1_R20.md` (#527) прочитан отдельно: выбранный план
`T3_M15_T1_TRAIL35_N4_R20`, SESSION T1 / NEXT_OPEN / TRAIL 3.5 / FULL N4, R20 2% / 8%.
Статус самого документа USER_SELECTED_FOR_FUTURE_ROBOT / DOCUMENTATION_ONLY /
NOT_LIVE_AUTHORIZED. Это проверенная документационная authority плана, не работающий runtime.
План не подменяет фактический RiskSnapshot или production identity.

Обозначения: **C** — контракт проверен в коде, runtime authority не проверена;
**D** — историческое документационное свидетельство; **P** — предложение будущего контракта.
Таблицы ниже сохраняют инвентаризацию контрактов и предварительные предложения,
**не** фактическую конфигурацию Intel. Текущая принимающая реализация/TTL/allowlist
определяются [контрактом CC-02](H1_READONLY_SNAPSHOT_CONTRACT.md); прежний proposal
Task TTL 60s не реализован. Raw heartbeat/runtime paths из таблицы не читаются.
Все actual live TTL до CC-03 не утверждены; неизвестный calendar/current signal UNKNOWN.

## H1 — TradingSystemLab / отдельный account scope

Базовый код: `TradingSystemLab/stage8_robot/`. Полные проверяемые пути приведены ниже таблицы.

| Показатель | Предполагаемый источник / поле | Фактическое существование | Достоверность | Обновление / время источника | Критерий устаревания | Безопасное чтение в будущем | При отсутствии |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Heartbeat production | `production_safety_gate.py::write_production_heartbeat`; `<runtime>/diagnostics/stage8-12-4-production-heartbeat.json`, schema `stage8_12_4_production_heartbeat.v1`; timestamp, health_status, cycle_count | Код/schema есть; JSON Intel не проверен | C: только producer-отчёт после reconciliation; не broker truth | `ProductionService`: default poll 30s, fast 3s при unresolved/ошибках; фактический poll UNKNOWN | Предложение: >2–3 фактических циклов + запас; future/naive timestamp invalid; HALTED с остановленным процессом не требует свежего heartbeat | Ограниченный атомарный redacted JSON export, allowlist identity/account/commit/schema, без запуска producer | UNKNOWN / STALE; не оставлять HEALTHY |
| Исторический readonly heartbeat | `operations.py::write_heartbeat`, `readonly_supervisor.py`; `diagnostics/stage8-heartbeat.json`, last_completed_h1_timestamp, entries_enabled, failure_code | Код есть; runtime-файл не проверен | C; другой режим и другая authority, не подмена production heartbeat | Supervisor default 300s, диапазон 30–3600s в коде; timestamp | TTL по фактическому readonly poll; неверный mode/identity → UNKNOWN | Отдельный allowlisted snapshot и отдельная маркировка режима | UNKNOWN; не смешивать с production |
| Windows Task / процесс | `diagnostics/stage8-493-process-lineage-readonly.ps1`; Task name `TradingSystemLab-Stage8-Production`, CIM lineage; CURRENT_STATE.md checkpoint Disabled | Диагностический скрипт есть, Windows не опрашивался | C + D; старый скрипт имеет устаревшие commit/Running-предусловия и не готовый адаптер текущего HALTED | Только момент отдельной диагностики; периодического экспорта не найдено | Предложение TTL 60s от probe observed_at; process ≠ trading permission | Отдельный санкционированный read-only OS probe публикует ограниченный снимок; UI не запускает PowerShell | UNKNOWN; Task Disabled только как датированный отчёт |
| HALTED / торговое разрешение | `trading_safety_gate.py::load_kill_switch`; `safety/stage8-trading-kill-switch.json`, state/generation/updated_utc; production_safety_gate.py entry gate | Код/schema есть; switch/authorization Intel не читались | C + D; HALTED документирован. ARMED сам по себе не даёт authorization | updated_utc при смене switch; observed_at безопасного probe нужен отдельно | Не считать старый updated_utc ошибкой неизменного HALTED; устаревает время повторного наблюдения | Allowlisted sanitized gate snapshot, exact spec/commit/account; не импортировать loader и не читать raw authorization в UI | UNKNOWN; входы в UI всегда запрещены |
| Последняя завершённая H1 на каждый N4 | `production_service.py::_history`; state keys `production_expected_h1:{instrument}`, `production_h1_continuation:{instrument}`; `production_history.py::close_index_for_frozen_t3` | Ключи и close conversion есть; SQLite не открыт | C; watermark/expected не равен полученной свече; production heartbeat последнюю H1 не содержит | После обработки истории; continuation bars имеют timestamp open-label; перевод в close обязателен | По ожидаемому **закрытию** H1 и торговому календарю; неполная свеча/ожидаемая отсутствующая → DATA_GAP | Готовый per-instrument export с label/timezone/calendar/observed_at; не перечитывать market CSV из UI | UNKNOWN / DATA_GAP; не выдумывать свечу |
| Сигнал / отсутствие сигнала / индикаторы / условия | `production_runtime.py::build_latest_signal`; `pending_signal:{instrument}`, `last_evaluated_h1:{instrument}`; DecisionCore вызывается внутри runtime | Код есть; полного устойчивого decision trace со всеми NO SIGNAL причинами не найдено | C частично; `return None` не устанавливает причину; UI не может её восстановить достоверно | При новой завершённой H1; signal timestamp и source observation отдельно | Signal должен соответствовать bar/identity; старый сигнал помечается временем; отсутствие trace не равно NO SIGNAL | Только реально emitted поля в sanctioned snapshot; не запускать core заново | UNKNOWN, «причина не опубликована» |
| Риск / число контрактов / margin | `risk.py::size_position`; `production_runtime.py::plan_entry`, sizing payload, risk_cash, actual_initial_loss_cash, margin_reservation; frozen specification.py | Код/контракты есть; фактический sizing не проверен | C; frozen 1,5% / 6% — справочная спецификация, не текущая capacity | При sizing intent; equity/economics/account timestamp обязательны | Если любой исходный account/economics stale, capacity UNKNOWN; исторический размер остаётся историческим | Redacted per-intent export вместе с ценой/валютой/округлением и gate reason | UNKNOWN для фактических quantity/risk; frozen лимиты отдельно |
| Намерения и ACK | `state.py::_SCHEMA`: `intents(idempotency_key,payload,status,broker_order_id,updated_at)`; submission/protective state keys | SQLite schema и transitions есть; БД Intel не прочитана | C; ACK/request не подтверждают fill | updated_at и source observation; SQLite CURRENT_TIMESTAMP требует явной UTC трактовки | Возраст pending/request + отсутствие reconciliation → UNRESOLVED, без авторазрешения | Разрешённый consistent read-only export; не создавать StateStore (его constructor пишет schema) | UNKNOWN / UNRESOLVED, fill_price UNKNOWN |
| Наблюдаемые позиции | `production_runtime.py::open_positions`, state `production_positions`; `production_broker_state.py::position_quantities`; heartbeat open_position_count | Код есть; ни local ledger, ни broker не опрошены | C: ledger ≠ брокер; POSITION_OBSERVED ≠ FILL_CONFIRMED; fault heartbeat может содержать пустую protection | На reconciliation/snapshot; timestamp heartbeat/account отдельно | Старый account observation → STALE; fault heartbeat с нулями не доказательство flat | Account-scoped redacted reconciled snapshot с явной completeness/authority; не интерпретировать пустую fault protection как 0 позиций | UNKNOWN, не 0 |
| Подтверждённое исполнение | `state.py` fills; `production_runtime.py::_handoff_entry_history`, `entry_fill_history:{entry_key}`, matched_quantity/weighted_price_exact; readonly observation helper | Код есть; broker trade history не проверена | C; только authenticated account+order-linked trade evidence даёт FILL_CONFIRMED; fill-gate False по docs не меняется | Timestamp факта сделки + timestamp получения истории, окно/limit/completeness | Неполная/обрезанная история или неустановленный account/order → UNRESOLVED | Экспорт проверенных фактов с evidence hash и completeness, без сырых broker IDs | UNKNOWN для цены/количества, UNRESOLVED |
| Защитные стопы | `production_broker_state.py::active_sltp_for_trade`; heartbeat position_protection expected/covered qty/active_stop_order_ids; runtime protective_stop_state/price | Код есть; текущих SLTP не наблюдали | C; local stop plan не подтверждает broker protection. 100% SLTP не является доказательством будущего исполнения | При broker reconciliation и heartbeat, observed_at | Старые broker facts/несовпадение позиции/qty/identity → UNKNOWN protection | Только reconciled per-position evidence; редактировать ID; не обращаться к FINAM из UI | Стоп UNKNOWN; не «позиция защищена» |
| Финансы / equity / realized / unrealized / комиссии | `production_service.py::Snapshot`, runtime realized_equity; `diagnostics/stage8_493_capital_pnl_readonly.py::classify`, `stage8_493_n4_financial_readonly.py` | Код/helper есть; готовый периодический финансовый экспорт не подтверждён | C; ledger basis ≠ broker equity; deposits/withdrawals ≠ PnL; месячный PF/DD authority не подтверждена | Account snapshot observed_at, fills timestamps, separate cashflow statement times | По свежести account и полноте fill/cashflow ledger; нельзя освежать исторический капитал docs | Готовый отдельный account-scoped финансовый снимок с reconciled cashflows/fees; без новых FINAM запросов | Каждый неизвестный показатель UNKNOWN, не 0; PF/DD только по полной подтверждённой истории |
| Ошибки / FINAM диагностика / события | `production_service.py` logs `logs/stage8-12-production.log`, PRODUCTION_CYCLE_PASS/FAULT; heartbeat reconciliation_status/last_successful_finam_api_contact; readonly observation helper | Logging и helper есть; файлы/актуальность/полнота Intel не проверены | C; цикл PASS не доказывает сделку; helper сам API не вызывает и freshness не гарантирует | На цикл/ошибку; heartbeat timestamp/API-contact timestamp; не у каждого log record есть typed event timestamp | Возраст последнего producer/API success; log rotation и пропуски не заменять тишиной «всё хорошо» | Bounded redacted structured event export, whitelist типов и лимит истории; raw log/exception не отдавать UI | UNKNOWN / API_ERROR, отдельно последняя успешная API-связь |

## M15 — IntradayLab / отдельный будущий FINAM-счёт

Просмотрены новый документ выбора #527, README/архитектурная граница IntradayLab, список файлов и
`IntradayLab/t3_m15_session_entry_v1/README.md`, `engine.py`.
Это research replay с историческими предположениями об исполнении, не production runtime.
Результаты OOS, исходные рыночные CSV и торговые токены не читались. Список файлов
не выявил отдельного runtime/production/heartbeat модуля. Это ограниченное обследование
данного commit, не доказательство отсутствия внешнего M15 проекта.

| Показатель | Ожидаемый источник | Фактическое существование | Достоверность | Обновление / время | Критерий устаревания | Безопасное чтение в будущем | При отсутствии |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Approved production identity / параметры / инструменты | `SELECTED_T3_M15_SESSION_T1_R20.md` (#527), будущий runtime spec | План существует и прочитан: T3_M15_T1_TRAIL35_N4_R20, FULL N4, SESSION T1 / NEXT_OPEN / TRAIL 3.5; final deployed identity не существует в проверенных источниках | D для выбранного плана, P для production authority | Документ решения 15.10.2026; будущий schema/commit export | Документ плана не устаревает как heartbeat, но не подтверждает runtime; exact deployed spec ещё нужен | Показывать план отдельно от production identity; будущий allowlisted spec export | NOT_DEPLOYED / production identity UNKNOWN |
| Последняя завершённая M15 | Будущий runtime completed-bar snapshot с close timestamp/timezone/label/calendar | Production export не найден; research engine работает с историческими close-index frames | P, runtime UNKNOWN | На каждое ожидаемое закрытие M15; producer observed_at | По M15 календарю/сессии и delivery latency; missing expected bar → DATA_GAP | Независимый M15 snapshot, без H1/market-file импорта в UI | UNKNOWN |
| Торговая сессия | Approved M15 session policy и runtime session gate | `session_entry_v1/engine.py::permits` существует для research CONTROL/T1/T2; в #527 выбран план T1 (10:00≤close<18:00 MSK); runtime gate не подтверждён | C только research; P production | При смене session и на bar; MSK/calendar/observed_at | Отсутствует утверждённый calendar/timezone или старый observation → UNKNOWN | Только emitted session fields собственного M15 exporter | UNKNOWN / NO_RUNTIME_AUTHORITY |
| SESSION сигналы / условия / отказы | Будущий per-bar decision trace M15 | Research entries/stops/gaps lists есть; runtime emitted trace не найден | C research ≠ live, P runtime | На завершённую M15, signal/bar/source timestamps | Нет matching bar/spec либо missing reason → UNKNOWN | Отдельный scoped M15 trace; не пересчитывать research strategy из UI | UNKNOWN, не выдуманный NO SIGNAL |
| Сделки / заявки / позиции / стопы | Собственный M15 execution/reconciliation ledger | Research replay lists есть; production ledger и broker evidence не подтверждены | P; historical assumed fill не broker fill | При каждом подтверждённом событии, fact time + observed_at | Pending/ACK без фактов → UNRESOLVED; неполная история UNKNOWN | Экспорт собственного account-scoped runtime; те же уровни фактов, своя stop authority | UNKNOWN |
| Риск / капитал / комиссии / PF / DD | Собственная approved risk spec + отдельный account ledger | План #527: R20 2% / 8%, отдельный счёт; production source/capacity не установлен, R15 H1 не применяется | P | При sizing/account/fill/cashflow, отдельные времена | Нет полной account/financial authority → UNKNOWN | Независимый redacted snapshot, никакого объединения с H1 | UNKNOWN, не 0, не H1 R15 |
| Состояние отдельного FINAM-счёта | Санкционированный M15 account reconciliation exporter | Не подключён; идентификатор/баланс неизвестны | P | По правилам будущего M15 runtime; observed_at | Время producer/API success, exact account match | UI только читает готовый export, без FINAM/token/polling | UNKNOWN / NOT_DEPLOYED |
| Heartbeat / Task / процесс | Собственный будущий M15 runtime heartbeat и независимый OS probe | В проверенном дереве runtime/heartbeat не найден, внешние источники не проверены | P | На цикл будущего runtime; poll ещё не определён | TTL после согласования, не заимствовать H1; missing runtime сохраняет NOT_DEPLOYED | Отдельные directory/identity/account, read-only snapshot | NOT_DEPLOYED / NO_RUNTIME_AUTHORITY; heartbeat UNKNOWN |

## Проверяемые ссылки на исходники (зафиксированный commit)

Все пути относительно корня репозитория, чтение исходников не запускало их код.

- [production heartbeat schema/writer](../../TradingSystemLab/stage8_robot/production_safety_gate.py)
- [production service / snapshots / history / cadence / logs](../../TradingSystemLab/stage8_robot/production_service.py)
- [readonly supervisor / отдельная OperationalState](../../TradingSystemLab/stage8_robot/readonly_supervisor.py)
- [operations / historical heartbeat writer](../../TradingSystemLab/stage8_robot/operations.py)
- [kill switch loader/schema](../../TradingSystemLab/stage8_robot/trading_safety_gate.py)
- [StateStore / intents / fills schema](../../TradingSystemLab/stage8_robot/state.py)
- [production runtime / signals / sizing / positions / fill evidence](../../TradingSystemLab/stage8_robot/production_runtime.py)
- [H1 labels / continuation / close conversion](../../TradingSystemLab/stage8_robot/production_history.py)
- [broker position / order / SLTP views](../../TradingSystemLab/stage8_robot/production_broker_state.py)
- [FINAM readonly evidence normalizer](../../TradingSystemLab/stage8_robot/diagnostics/stage8_493_finam_readonly_observation.py)
- [capital / cashflow / PnL classifier](../../TradingSystemLab/stage8_robot/diagnostics/stage8_493_capital_pnl_readonly.py)
- [N4 financial diagnostics](../../TradingSystemLab/stage8_robot/diagnostics/stage8_493_n4_financial_readonly.py)
- [process lineage read-only diagnostic (не запускался)](../../TradingSystemLab/stage8_robot/diagnostics/stage8-493-process-lineage-readonly.ps1)
- [документационное состояние H1](../../TradingSystemLab/CURRENT_STATE.md)
- [проверенный документ выбора будущего M15, не runtime authority](../../IntradayLab/SELECTED_T3_M15_SESSION_T1_R20.md)
- [IntradayLab isolation / research context](../../IntradayLab/README.md)
- [M15 research SESSION, не production spec](../../IntradayLab/t3_m15_session_entry_v1/README.md)
- [research permits и replay lists](../../IntradayLab/t3_m15_session_entry_v1/engine.py)

## Конфиденциальность и схема подключения

Только псевдоним счёта и scoped reference/evidence hashes; не raw account ID/order ID,
command line, Windows credential paths, token, полный auth record или exception payload.
Publisher должен редактировать поля **до** их попадания в UI. Account hash не раскрывать
целиком без необходимости. Реальная identity и provenance проверяются до отображения.
Для будущего адаптера согласовать разрешённый producer/path, атомарную публикацию,
max bytes/history, TTL/completeness, чтение без блокировки runtime, поведение при
partial writes/отказе/WAL busy. Никакие существующие utility constructors не импортируются
в Streamlit, так как часть из них создаёт БД, пишет state или обращается к API.

В CC-02 используются два доверенных локальных **тестовых** источника: SYNTHETIC provider
в памяти и фиксированный OFFLINE_FIXTURE JSON, проверяемый H1ReadonlyProvider.
Новый sanctioned periodic exporter остаётся зависимостью CC-03. Ни один источник
Intel физически не прочитан. Financial classifier и N4 diagnostics подтверждают
различие equity/realized/cashflow/margin; commissions/tariff и полная финансовая
authority не появляются автоматически из GET account. Неполные числа скрываются.

## Карта фактически реализованных receiving полей

| Набор | Wire -> display | Достоверность | Обновление/TTL | Fallback | Источник/чтение | Конфиденциальность |
| --- | --- | --- | --- | --- | --- | --- |
| Identity/account | identity exact constants -> provenance/status/details | Только публичный fixture binding; не настоящий account | На каждый read, до отображения | Весь снимок UNKNOWN | Fixed package JSON, schema/hash | Нет raw account ID; binding не выводится |
| Runtime | state, heartbeat_at, last_successful_cycle_at, source_status | OFFLINE_FIXTURE, HALTED учитывается | 180s envelope / 90s heartbeat+cycle | STALE/UNKNOWN | Ограниченный readonly snapshot | Только safe enums |
| Reconciliation | status, last_success_at, unresolved_intents | Не broker truth; тестовое свидетельство | 90s | UNKNOWN; numeric authority отсутствует | Та же проверенная упаковка, независимый observed_at | Без API payload |
| Bars N4 | open_at/close_at/completed/label, gaps, quality, OHLC | Завершённость проверяется, актуальность calendar UNKNOWN | TTL не утверждён; metadata с временем | UNKNOWN/DATA_GAP; stale chart скрыт | Только опубликованные поля; no T3/CSV | N4 только |
| Signals | emitted/bar_close/direction/reason/risk_result | Только опубликованное событие | Historical event; current UNKNOWN | Причина не опубликована; отсутствие != NO_SIGNAL | Нет пересчёта DecisionCore | Enum причины, no free text |
| Orders/positions/stops | 6 execution levels, qty/side, отдельное fill/SLTP evidence | Fixture evidence; не live ACK/fill/protection | 90s + complete/reconciled | UNKNOWN/UNRESOLVED, no inferred zero/price/protection | Никаких DB/FINAM | Scoped reference hashes, no raw broker IDs |
| Finance/risk | equity, separate PnL/fees/cashflows/margin/contracts | Полный fixture account export с evidence | Offline 300s + fresh reconciliation | Все actual numbers UNKNOWN | Полнота/привязка до отображения | Нет account details/secret strings |

Полная схема, доверенные ограничения и будущие physical acceptance requirements:
[H1_READONLY_SNAPSHOT_CONTRACT.md](H1_READONLY_SNAPSHOT_CONTRACT.md).
