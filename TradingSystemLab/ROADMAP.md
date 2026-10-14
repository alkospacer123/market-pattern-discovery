# Evidence-based roadmap

## ЗАФИКСИРОВАННЫЙ ROADMAP ЗАПУСКА — PR #493 → REAL FINAM LIVE (14.10.2026)

**ЕДИНСТВЕННЫЙ АКТИВНЫЙ ПЛАН ДО ЗАПУСКА. РОВНО 3 ЗАДАЧИ: 1 → 2 → 3. НИКАКИХ НОВЫХ ЭТАПОВ, PR, МЕТОДОЛОГИЙ, ОПТИМИЗАЦИЙ И НЕЗАПРОШЕННЫХ ИСПРАВЛЕНИЙ.** Все следующие ниже старые roadmap-разделы сохранены как история; они не вводят дополнительных текущих задач. План закреплён по прямому указанию оператора 14.10.2026. Работа строго по подпунктам; не повторять успешно завершённые offline/READONLY-проверки без фактического основания. Ускорять выполнение, но не обходить необходимые физические safety-gates и отдельные разрешения.

**Цель:** реальный автоматический запуск T3/H1/TRAIL1 на FINAM максимально быстро (целевая дата 14.10.2026, не гарантия). Замороженная производственная спецификация `PROD_STAGE7_46DB784378797C7FB04636892350AFF21006D71A31F2CED9D4B974EDA2DC36B8`, identity `TRAIL1__N4_01__FULL__R15`, N4 USDRUBF/CNYRUBF/GLDRUBF/IMOEXF, R15=1.5% риска на новую позицию/6% суммарно, текущие ГО/лот/округление, без MICRO-лимита и без изменения стратегии. Основной кандидат — **PR #493**. PR #515 — не действующий путь к запуску, не merge/deploy. Блокировка `FINAM_FILL_AUTHORITY_VERIFIED=False` не снимается без доказательств и отдельного разрешения.

### Задача 1. Закончить подключение FINAM и безопасного закрытия — В РАБОТЕ

| Пункт | Что делаем | Статус |
| --- | --- | --- |
| **1.1** | Используем готовый `diagnostics/stage8_493_operator_harness.py` с отдельным журналом приёмки, не связанным с LIVE SQLite и Windows Task. | **Основа готова** |
| **1.2** | В существующем PR #493 подключён операторский инструмент к `FinamAPI` (позиции, заявки, исполнения, ENTRY, SLTP 100%, ограниченные cancel/exit) через `stage8_493_finam_operator_port.py` с внешним write-gate, закрытым по умолчанию. Реальные заявки не отправлялись. | **PASS — 14.10.2026 Intel: 53 теста за 2,73 с; точный commit `dabb90a9f794b703353e2530a519aa2210347e71`, Task Disabled/HALTED до и после.** |
| **1.3** | Проверка реальной исторической FINAM `GET /trades`: подтверждены order-linked AccountTrade по попыткам 2–6, идентичные результаты между отдельными сессиями, точные идентификаторы/сторона/инструмент/объём/цена. Независимый аудит `diagnostics/independent_uploaded_finam_evidence_audit_20261013.json` — 20 PASS / 0 FAIL, попытка 6: CNYRUBF, 1 контракт по 12.748. Не доказывает реальные 1→2 и SLTP. | **PASS в границах исторической READONLY-приёмки (доказательства 12–13.10.2026); свежие сделки проверяются только в задаче 2.** |
| **1.4** | На Intel проверены исходный частный N4-отчёт по SHA-256, расчёт неизменного FULL/R15 и ГО для всех четырёх инструментов LONG/SHORT в `stage8_493_two_contract_plan_offline.py`. Номинальный риск R15 по **историческому** снимку 749.54340 RUB; естественное количество 2 возможно в определённых диапазонах стопа на всех четырёх N4. Пополнение — капитал, не PnL; LIVE SQLite не трогали. | **INTEL OFFLINE REFERENCE PASS 14.10.2026: 17 тестов, проверенный частный отчёт, Task Disabled/HALTED. Для реальной сделки остаются актуальные entry/stop, комиссии, slippage и денежный бюджет; это не LIVE authority.** |
| **1.5** | Сохраняем прежние Intel PASS: 53 FINAM-адаптер, 158 V2, 2 recovery. В кандидате #493 после брокерской позиции SLTP устанавливается/сверяется **до** `GET /trades`; одноразовый `stage8_493_operator_write_gate.py` требует отдельно проверяемого согласия на конкретную сделку, host/FINAM/R15 и durable-intent перед каждой записью. | **INTEL OFFLINE PASS — 14.10.2026: exact commit `b71268aa174749f2775feae81380cffb32eed8be`; `54 passed in 4.88s`, Task Disabled/HALTED до/после, реальных заявок 0. Ограничение: отдельный операторский физический runner, текущая торговая авторизация/тариф/риск/восстановление в брокере не доказаны; gate не является исполняемым торговым launcher.** |

**Ответственные:** агент разрабатывает/аудирует только эту часть PR #493; оператор Intel запускает отдельно проверенные команды, сообщает фактический вывод. **Готовность задачи 1:** проверенный операторский FINAM-адаптер и подтверждённый бюджет/риск/восстановление для конкретной приёмки. Ни одного реального приказа не отправлено.

### Задача 2. Одна отдельно разрешённая реальная приёмка FINAM — НЕ НАЧАТА

| Пункт | Что делаем | Статус |
| --- | --- | --- |
| **2.1** | Intel 14.10.2026: по существующему hash-pinned READONLY N4-скрипту проверены Task Disabled/HALTED, послеизоляционная broker-flatness, два снимка счёта/ордеров, текущие FINAM asset/params и финансовые значения N4. Частный отчёт остался на Intel `c:\\tslaudit\\fill493\\stage8-493-n4-financial-readonly-task2-20261014.json` с SHA-256 `687DD4EA0D7FAF03F3245A73F974047F30992E816E34C8E1F16E5440148A89EA`. Непосредственно перед любой будущей ENTRY **повторяем только свежий брокерский/Task/сессионный precheck**, старые pytest не повторяем. | **READONLY SNAPSHOT PASS 14.10.2026: `EXACT_READONLY_SOURCE_HASHES`, `FRESH_POST_ISOLATION_READONLY_GATE`, `FINAM_N4_FINANCIAL_GET_READONLY` = PASS; real orders 0. Не является разрешением сделки или подтверждением тарифа/точного R15=2; точный before-POST gate PENDING.** |
| **2.2** | **РЕШЕНИЕ ОПЕРАТОРА 14.10.2026: для ОДНОЙ изолированной контролируемой приёмки FINAM разрешён ровно 2-контрактный CNYRUBF LONG, при сценарном бюджете 1000 RUB; это ИСКЛЮЧЕНИЕ ТОЛЬКО ИЗ ПРАВИЛА КОЛИЧЕСТВА ТЕСТОВОЙ ПРИЁМКИ, НЕ ИЗ FULL/R15 РОБОТА.** Действующий замороженный T3/H1/TRAIL1 и FULL/R15 (1.5%/позицию, 6% совокупно, текущая margin authority, без MICRO cap) НЕ МЕНЯЮТСЯ. Приёмка выполняется только отдельным операторским контуром, НЕ сигналом/размером production runner; произвольный стоп ради двух контрактов не устанавливать. Intel 14.10.2026 CNY H1 v3 READONLY PASS: session bound, Task Disabled/HALTED, zero order POST; H1 close reference 12.541, ATR14 0.02578879582314137, reference LONG SL 12.476, 65 тиков; справочный риск 65 RUB/контракт, 130 RUB на 2 и reference FULL/R15 quantity **11** (margin capacity **42**) — реальная стратегия именно так и должна рассчитываться при тех же *справочных* входе/стопе, НИКАКОГО изменения на quantity 2 в production. Эти цифры НЕ подтверждают текущий bid/ask, verified Stage5 H1 authority/signal, RUB tick authority FINAM, SQLite realized basis, клиентские fees/степень проскальзывания, реальное покрытие SLTP и безопасный EXIT; остаток 870 RUB до бюджета — арифметическая оценка, а не гарантированный предел потерь. **Следующий путь без новых фаз:** закрыть недостающий физический CNY plan/risk и ограниченный operator-only live runner/terminal recovery в рамках #493 → отдельная конкретная авторизация ENTRY/SLTP/CANCEL/EXIT пункта 2.3 → одна наблюдаемая приёмка 2.4–2.6 → задача 3 после отдельного разрешения. | **TEST-ONLY EXACT 2 CONTRACTS APPROVED / PHYSICAL TRADE NOT AUTHORIZED**. Отказ 2.2 **только из-за natural FULL/R15=11 снят**; physical entry/stop/fees, cash-loss stress и безопасное закрытие всё ещё PENDING. Пользователь разрешил изменить лишь правило теста, НЕ размер ордеров робота/его стратегию/результаты/производственную конфигурацию; production Task Disabled, switch HALTED. |
| **2.3** | Получаем **отдельное конкретное согласие пользователя** на реальные ENTRY, SLTP, возможный cancel/flatten с известными инструментом, направлением, объёмом, временем и денежным бюджетом. Согласие на roadmap/offline не разрешает сделки. | **Ожидает** |
| **2.4** | Под наблюдением выполняем **одну** ENTRY, подтверждаем реальные связанные с ней fills и позицию, устанавливаем и проверяем защитный SLTP 100% текущей позиции. ACK не равен fill. | **Ожидает** |
| **2.5** | Если брокер естественно исполнит 1→2, проверяем покрытие той же реальной SLTP-заявкой второго контракта. Немедленные 0→2 или только 100%-echo — **INCONCLUSIVE**, а не PASS. Не создаём дополнительную сделку ради частичного fill. | **Ожидает** |
| **2.6** | По заранее разрешённой процедуре закрываем позицию, сверяем fills, получаем две независимые проверки **positions=0, active orders=0, unresolved intents=0**; оставляем HALTED и Task Disabled. При неопределённости — безопасная остановка и ручное восстановление, без повторных слепых POST. | **Ожидает** |

**Ответственные:** агент — подготовка/проверка исполнения; оператор Intel — отдельное разрешение на риск и исполнение физического теста. **Готовность задачи 2:** фактические критерии приёмки подтверждены, счёт flat, заявок/неразрешённых намерений нет. Неподтверждённый реальный 1→2 остаётся блокером, не автоматической новой задачей.

### Задача 3. Выпустить PR #493, установить на Intel и запустить робота — НЕ НАЧАТА

| Пункт | Что делаем | Статус |
| --- | --- | --- |
| **3.1** | Финальный независимый аудит точного PR #493: статус задач 1–2, фактические тесты/исполнение, frozen стратегия, портфель N4, FULL/R15, риск и отсутствие незакрытых блокеров. | **Ожидает** |
| **3.2** | После **явного разрешения на выпуск**: merge PR #493, проверка фактического GitHub `main`, точного commit и разрешённого diff. PR #515 не используется. | **Ожидает** |
| **3.3** | После отдельного согласия на production cutover: неизменяемые резервные копии SQLite/WAL, предыдущего Task/авторизации/commit; точная проверенная версия, безопасная миграция/новая схема только в согласованных рамках PR #493, контролируемое переключение на Intel при HALTED и flat. | **Ожидает** |
| **3.4** | Проверяем фактические checkout/data SHA, счёт/позиции/заявки FINAM, новую authority/schema, отсутствие неразрешённых intents, N4 и безопасное состояние после переключения. | **Ожидает** |
| **3.5** | **Сразу после разрешённого production fix:** обновляем `CURRENT_STATE.md`, `ROADMAP.md`, `stage8_robot/PRODUCTION_RUNBOOK.md`, `stage8_robot/PRODUCTION_STRATEGY_PASSPORT.md`, `stage8_robot/PRODUCTION_OPERATOR_CHECKLIST.md` и `PROJECT_CONTEXT.md` если применимо. Независимо сверяем фактический GitHub `main` с реально развёрнутыми Intel checkout/Task/kill switch/authorization; не путать docs-only main SHA с production SHA. | **Ожидает** |
| **3.6** | После **отдельного разрешения на торговый запуск:** Task Running, kill switch ARMED, HEALTHY, reconciliation PASS, entry gate OPEN и реальная возможность автоматических входов **только по сигналам** замороженного T3/H1. Никаких принудительных сделок для статуса запуска. | **Ожидает** |

**Ответственные:** агент — проверка PR, GitHub/документов и безопасные операторские сценарии; оператор Intel — явное разрешение и выполнение production-команд. **Готовность задачи 3:** включённый, здоровый и сверенный автоматический робот с разрешённой реальной торговлей FINAM. Не требуется искусственно получать сигнал/сделку в тот же день.

### Границы и фактический checkpoint (14.10.2026)

- **Чекпоинт 14.10.2026: 1.2 Intel 53 PASS, 1.3 исторический FINAM аудит 20/20 PASS, 1.4 Intel 17 PASS, 1.5 новый SLTP-first/one-shot gate Intel 54 PASS (до этого 158 + recovery 2 PASS). Задача 2.1 — новый FINAM N4 READONLY SNAPSHOT PASS, отчёт SHA-256 проверен. Следующий шаг строго 2.2: локально использовать свежий частный отчёт, выбрать реальную entry/stop, установить клиентский тариф/стресс-риск и отдельно согласовать риск; затем 2.3.** Перед реальным POST обязателен ещё один свежий precheck; прежние тесты и GET истории не повторять без причины. Реальных заявок, merge, rollout и rearm не разрешено. Не добавлять новые задачи/фазы/исследования или параллельные PR без нового согласия пользователя.
- Сохранены результаты операторских offline-проверок 737 PASS и FINAM READONLY PASS, но ни они, ни текущие средства не доказывают реальное покрытие SLTP на 1→2.
- Последняя физическая информация Intel: production commit `184e8c2b8fa092a606249ff293a4f507160bff29`, Task **Disabled/stopped**, switch **HALTED**, broker flat на момент двух READONLY снимков. Постоянное полномочие не было автоматически отозвано; без нового специального разрешения Task не запускать, HALTED не снимать, заявки не отправлять.
- Этот документ — **фиксация порядка работ**, а не отдельное разрешение на кодовые изменения вне пунктов, реальные заявки, merge, миграцию, Scheduled Task или re-arm.
- Более ранние разделы ниже — исторические сведения. Приоритет у этих ровно **трёх** задач и неизменных уже принятых производственных ограничений.

---

## CURRENT roadmap checkpoint — 2026-10-13 isolation PASS; real SLTP acceptance HOLD

**CURRENT LIVE: STAGE8_493_PRODUCTION_TASK_ISOLATED_HALTED — 2026-10-13 Intel operator evidence.** The authorized `stage8-493-controlled-task-isolation.ps1 -execute` physically returned `ISOLATED_HALTED_PENDING_GITHUB_OPERATIONAL_SYNC`. Fresh before-stop `FINAM + SQLite + HALTED=PASS`; Task `TradingSystemLab-Stage8-Production` was **disabled before stop** with startup/auto-restart suppressed; PowerShell PID **8536**, Python root **6260**, Python child **11608** exited. Post-stop `POST_STOP_FINAM_SQLITE_LOCK_GATE=PASS`: two fresh broker READONLY account/orders flat snapshots, clean production SQLite and lock quiescent. Existing kill switch **HALTED**. No orders or rearm by this operation.

**Evidence:** original Task XML backup saved outside Git in `c:\tslaudit\fill493`, operator-reported SHA-256 `2714BB09FF571EFAE748509F5D3C3BC8DD5F38460173E1A13EF5AEE752DF906E` (backup bytes and exact timestamped filename not independently fetched). Result is a time-bounded *operator-console* observation; heartbeat stops refreshing by design after isolation. The durable commit-bound production authorization record **was not revoked or rewritten**. Disabling Task and keeping HALTED do not erase existing authorization; do not start/rearm without fresh separately approved recovery.

**Frozen identity unaffected:** accepted Intel code `184e8c2b8fa092a606249ff293a4f507160bff29` (PR #484), Stage5 data `50f1fd2178c18b7ab3bd969be82ad01f47a34745`, production spec `PROD_STAGE7_46DB784378797C7FB04636892350AFF21006D71A31F2CED9D4B974EDA2DC36B8`, `TRAIL1__N4_01__FULL__R15`, T3/H1/TRAIL1, N4 USDRUBF/CNYRUBF/GLDRUBF/IMOEXF, risk 1.5% new position / 6% nominal aggregate and frozen margin sizing. No source, strategy, risk, research, execution adapter, authorization file or production SQLite modification was made.

**HARD HOLD:** Draft PR #493 (candidate STOP/TICK GRID and SLTP acceptance) is not merged/deployed. No real orders, SLTP test, V2 rearm, Task restore/restart, forced PID kills, change to `FINAM_FILL_AUTHORITY_VERIFIED=False` or stage8.11 one-contract policy without new, separate explicit authorization. Post-stop FINAM validation is **readonly** and does not grant fill-price or live-entry authority. The prior `ARMED / Running / HEALTHY` sections below are **historical**, not instructions for current LIVE. Never `git pull` the pinned Intel checkout to follow docs-only GitHub commits.

**Roadmap:** The already-approved Task isolation is complete. Next remains a separately reviewed operator-only multi-fill/SLTP acceptance design (up to two contracts) and independent safety/recovery tests, not an automatically authorized trade. No new phase, optimization, parameter changes or production V2 release.


## 2026-10-12 CURRENT operational authority — LIVE ARMED, confirmed after re-arm

**LIVE: ARMED, kill switch generation 60; Scheduled Task Running; fresh HEALTHY / reconciliation PASS; entry gate OPEN.** Production code remains exact fix `184e8c2b8fa092a606249ff293a4f507160bff29` (PR #484); Stage5 data authority `50f1fd2178c18b7ab3bd969be82ad01f47a34745`. Explicit operator-authorized `stage8_12_h1_rearm_once.ps1` returned `STAGE8_12_H1_REARM=PASS`, `REARM_COMPLETED=YES`. Re-arm did not change source, Scheduled Task, authorization or SQLite schema, and did not itself force an order.

**Physical read-only check, 2026-10-12 11:38:23 MSK:** production `Running`, readonly `Disabled`; auth `AUTHORIZED`, `execution_authorized=True`, accepted commit exact `184e8c2...`; `ARMED` gen 60; heartbeat `HEALTHY`, reconciliation `PASS`, **cycle 9258**, heartbeat/API `2026-10-12T08:37:59.022453+00:00`, positions 0, active protective stops 0, unresolved intents 0. Successful production cycles 9213–9258 follow earlier historical H1 timestamp mismatch faults. There is no evidence of a new real trade in this snapshot; trading is eligible only if frozen safety and signal gates pass.

The operator check script `check-tradingsystemlab-live.ps1` still compares authorization and heartbeat to **obsolete** SHA `4c7cd7cbbde5fbffb63ed6984cf89b90dc50d129`, producing two **false MISMATCH** warnings. Actual authorization and heartbeat both match fixed SHA `184e8c2...`. Updating that read-only diagnostic is a separate small task; do not change live production to accommodate old expectations.

The earlier HALTED and shadow/backup/recovery sections below remain historical and are **superseded as current operational status**. T3/H1/TRAIL1, frozen N4 FULL/R15 (1.5% per new position, 6% nominal aggregate initial risk), margin sizing and all research/strategy/exec semantics are unchanged. **Never `git pull` the active production checkout just because docs-only GitHub main advanced.**


## Current operational authority — 2026-10-12, H1 timestamp-backfill fix LIVE restored under HALTED

**AUTHORITATIVE LATEST STATE: HALTED / RUNNING / HEALTHY / RECONCILIATION PASS / NOT REARMED.** This supersedes earlier dated incident, shadow, readiness, and partially failed task-rollout snapshots below; those remain historical provenance, **not** current operational instructions.

Intel operator executed approved fix rollout plus narrow Scheduled Task recovery. The exact active production checkout is **`184e8c2b8fa092a606249ff293a4f507160bff29`**, PR #484, **not latest docs-only GitHub main**. Frozen Stage5 data remains pinned `50f1fd2178c18b7ab3bd969be82ad01f47a34745`; old production source checkout `4c7cd7cbbde5fbffb63ed6984cf89b90dc50d129` retained as previous/rollback provenance, not active LIVE code.

- Cutover regression tests **114 passed**; FINAM broker/SQLite safety precheck PASS; separate SQLite cutover backup SHA-256 `759ef278967b9781a79bd916e47bfe5823908b027dc98b48b05b198fa4482bd7`; exact new commit-bound production authorization successfully rolled over once; N4 immutable H1 prefix PASS.
- First corrected production real-runtime guarded cycle **9213**: `HEALTHY`, reconciliation `PASS`. The initial Scheduled Task update failed due to Windows username/password validation; this is **resolved**, not a current blocker.
- Subsequent narrow recovery script `stage8_12_h1_resume_task_binding_halted.ps1` operator result: `STAGE8_12_H1_TASK_RECOVERY=PASS`; exact Windows task action rebound with principal unchanged; task started successfully; new actual LIVE cycle **9214**, heartbeat `HEALTHY`, reconciliation `PASS`.
- Latest recovery broker/SQLite precheck PASS, open positions `0`, unresolved intents `0` (and prior cutover active broker orders `0`); exact-commit task **`RUNNING`**; entry gate **`CLOSED_HALTED`**; kill switch **`HALTED`**, generation **`59`**; **`REARM=NOT_DONE`** and no new trade authorization implied by task recovery.
- External Intel task-recovery evidence: `c:\tradingsystemlab\verification\h1-live-rollout-184e8c2-20261012\halted-task-recovery-pass.json`, SHA-256 `95d724dce03cedefd444de742d6f73fa3b6a0dbdecf0f8c6418e2149c8a0da43`. These physical facts come from the operator's PowerShell log; external report bytes and runtime are **not** stored in GitHub.

**Next:** preserve running HALTED monitoring; do not repeat rollout, reissue authorization, change task bindings, edit SQLite, or `git pull` the production checkout. Re-arm to enable entries requires **separate explicit operator authorization** after an up-to-date safety check. No Stage7 strategy, T3/H1/TRAIL1, N4, R15/6% limits, risk sizing, research artifacts, or broker execution semantics changed.


## 2026-10-12 HALTED LIVE rollout readiness + backup — PASS (operator evidence)

Operator-ran Intel backup-only gate after the 60/60 isolated H1 tests, 4/4 FINAM GET-only H1 checks, and 4/4 shadow production HEALTHY/PASS:
- `READINESS_BACKUP=PASS`, source LIVE SQLite backed up using read-only SQLite online backup; `SQLITE_BACKUP_INTEGRITY=PASS`; exactly four durable N4 H1 continuation keys.
- Latest broker positions `0`, active broker orders `0`, local unresolved intents `0`; kill switch `HALTED`, generation `59`.
- External SQLite backup SHA-256: `6a8c2c7d1ef589ff0190b28624397962abb9583eccfa90bc4099a6f1681486fe`.
- External readiness report: `C:\TradingSystemLab\verification\h1-live-rollout-readiness-backup-20261012\readiness-backup-report.json`; SHA-256: `812ab73de05b896db7d4938b040d20bda49f8fc924a0e852a8c20de45516b644`.
- The backup also preserved existing authorization and Scheduled Task definition externally. Existing production checkout `4c7cd7cbbde5fbffb63ed6984cf89b90dc50d129`, authorization, production task `Running`, Stage5 source and LIVE SQLite remain unchanged. `ROLLOUT=NOT_STARTED`; `REARM=NOT_DONE`; LIVE `HEALTHY/PASS` has **not** been proven.
- **Next operator boundary:** exact-commit controlled HALTED task/code/authorization migration, with old authorization kept immutable as evidence and no automatic re-arm. Requires separate explicit operator permission before altering the active task/authorization. Never `git pull` into active production checkout.

The validation and backup evidence hashes are operator reported; actual external backup bytes remain on Intel. No frozen T3/H1/TRAIL1, N4, R15/6%, sizing, research or execution changes.


## 2026-10-12 validation update — shadow PASS; LIVE still HALTED

Intel operator evidence for code fix PR #484 (commit `184e8c2b8fa092a606249ff293a4f507160bff29`), **not** a production deployment:

- Isolated worktree targeted tests **60/60 PASS**. Full Stage 8 suite not yet run.
- FINAM GET-only immutable H1 physical splice **4/4 N4 PASS**; accepted seam `2026-10-11T18:00:00+03:00`; 2 backfilled historical timestamps ignored and 2 newer append-ready bars **per N4 at probe time**. Broker positions, active orders and unresolved intents: `0/0/0`. External evidence SHA-256: `2fe51ccd6ab57682579f222158b12413eaae6020abe21aec7afa188d3afddb43`.
- One-cycle corrected production service **on an isolated SQLite online-backup copy**, FINAM restricted to session/GET calls: immutable-prefix checks `4/4 PASS`, **3 newer bars per N4 appended to shadow only**. Shadow heartbeat `HEALTHY`, reconciliation `PASS`. External evidence SHA-256: `4799a0b426cd62d143a0b3fdba6035ef44f11dde6654676568b1a28e3a8fbded`.
- LIVE checkout remains at old code commit `4c7cd7cbbde5fbffb63ed6984cf89b90dc50d129`; old-commit-bound authorization and LIVE SQLite/tasks unchanged. Production task `Running`, kill switch `HALTED` generation 59. **LIVE production heartbeat recovery NOT TESTED/NOT PROVEN.** No real order endpoint call or re-arm in these checks.
- Next gate: operator-controlled HALTED LIVE deployment with validated rollback/backups and exact commit/task/authorization rollover, full applicable tests/audits, fresh real-runtime `HEALTHY/PASS`; re-arm requires a separate explicit operator decision. Do not run historical foundation/package3 scripts against an already authorized, Running LIVE environment; never `git pull` active LIVE checkout.

External report bytes remain on Intel, not committed in Git. No strategy, T3/H1/TRAIL1/N4/FULL-R15, frozen risk/portfolio/execution, Stage5 or research changes.


## Current operational HOLD — 2026-10-12 (supersedes older operational snapshots)

**HALTED / NOT REARMED.** Operator-provided physical snapshot at `2026-10-12T05:55:33.966970+00:00`: kill switch `HALTED`, generation `59`, production service `Running`, positions `0`, unresolved intents `0`; heartbeat `UNHEALTHY`, reconciliation `FAULT`, cycle_count `9212`, repeated `STAGE8_12_4_H1_SPLICE_TIMESTAMP_MISMATCH`. These are **reported observations**, not a new physical verification.

Observed GET-only diagnosis across all four N4: FINAM later added H1 `2026-10-10 09:00 MSK` inside immutable historical overlap; exact authority seam `2026-10-11 18:00 MSK` remained present and a later live H1 `2026-10-12 07:00 MSK` existed. The first LIVE week independently examined 58 H1 per N4 (232 checks), with 0 complete T3 signals, 0 intents, 0 fills and signal_sequence=0.

Code-only H1-history fix: [PR #484](https://github.com/alkospacer123/market-pattern-discovery/pull/484), merged as `184e8c2b8fa092a606249ff293a4f507160bff29`. This is **repository code**, **not** a physically accepted or deployed LIVE commit. The Intel production checkout remains historically pinned to `4c7cd7cbbde5fbffb63ed6984cf89b90dc50d129`; Stage5 data is `50f1fd2178c18b7ab3bd969be82ad01f47a34745`. Documentation-only commits may advance `main` without changing that checkout.

Stage5 plus persisted H1 remains immutable; later FINAM-only timestamps `<= authority.max()` are ignored, and only bars `> authority.max()` append after the **exact latest seam** is observed. Missing seam/no overlap, duplicated or unordered timestamps, persisted corruption and stale current H1 continue to fail closed. Frozen T3/H1/TRAIL1/N4/FULL-R15/6%, sizing and execution semantics are unchanged.

**Gates outstanding:** full repository test execution; Intel preactivation under `HALTED` with fresh `HEALTHY/PASS`, positions=0 and unresolved=0; new commit-bound authorization rollover if necessary; **separate explicit re-arm permission**. No `git pull` or automatic checkout movement on Intel; no re-arm, forced entries or retroactive persisted continuation edit. See `stage8_robot/PRODUCTION_OPERATOR_CHECKLIST.md` and `stage8_robot/PRODUCTION_STRATEGY_PASSPORT.md`.


## Operational checkpoint — 2026-10-08

Current LIVE production code authority is pinned to:
`4c7cd7cbbde5fbffb63ed6984cf89b90dc50d129`.

Repository `main` may advance after documentation-only synchronization; that does **not** move the Intel production checkout. The production checkout remains pinned to the exact accepted production commit until a separately controlled code migration.

Current operational authority:

- Stage 8.9 — COMPLETE;
- Stage 8.10 — COMPLETE;
- Stage 8.11 Controlled Real Execution Acceptance — **COMPLETE / PASS**;
- Stage 8.12 FULL/R15 Production Authorization — **COMPLETE / PASS**;
- Stage 8.12.4 — **COMPLETE / LIVE PRODUCTION ACTIVATED**;
- canonical completion status: `STAGE_8_12_FULL_R15_PRODUCTION_AUTHORIZATION_COMPLETE`.

Stage 8.11 PASS authority is immutable attempt `stage8.11.attempt7`, accepted code
`72a910e49b876cda99484a810e6f8a1b16ac0209`, evidence SHA-256
`704BFCC19B1A63F490192C0D8D0E4715BFECF77664296AFEF47E5B80FBF64B5F`.
It proved one-contract entry, observed position, controlled flatten, final flat
account, zero active orders, zero unresolved intents, and reconciliation PASS.
Attempts 1–6 remain historical failure/recovery provenance and are not rewritten.

Current Stage 8.12.4 activation authority:

- accepted production commit: `4c7cd7cbbde5fbffb63ed6984cf89b90dc50d129`;
- original 2026-10-07 live-activation commit (historical provenance): `883ea1ea6a8268276a8e39ebdc8786c643a21935`;
- Stage 5 data authority: `50f1fd2178c18b7ab3bd969be82ad01f47a34745`;
- Package 5 readiness evidence SHA-256:
  `FE383E9D269F699639D0F256CB15A303E0A5EE9CBC3990F802E10DCE8A41B7CD`;
- live-activation evidence SHA-256:
  `EA14B73FA1AE1D62C2324A0C76624DA792101FCD945383D70B646BDA1D6F8CB9`;
- durable production authorization: `AUTHORIZED`;
- `execution_authorized = true`;
- production kill switch: `ARMED`;
- production Scheduled Task: `Running`;
- readonly Scheduled Task: `Disabled`;
- post-arm heartbeat / reconciliation: `HEALTHY / PASS`;
- post-arm unresolved intents / open positions / protective stops: `0 / 0 / 0`;
- post-arm production cycle count: `15`.

### 2026-10-08 H1 hotfix operational rollover — CURRENT

- incident: repeated `STAGE8_12_4_H1_SPLICE_OHLC_MISMATCH` while FINAM connectivity remained available;
- root cause: production append-only authority was correct, but liveness still depended on exact equality with mutable historical FINAM OHLC;
- corrective PR: #435;
- accepted production commit: `4c7cd7cbbde5fbffb63ed6984cf89b90dc50d129`;
- Stage 5 data commit remained unchanged and clean: `50f1fd2178c18b7ab3bd969be82ad01f47a34745`;
- accepted H1 rule: once a completed H1 bar is accepted into Stage-5/persisted production authority, its OHLC is immutable; a later FINAM OHLC revision for the same timestamp does not rewrite accepted history and does not permanently fault production;
- timestamp safety remains fail-closed: duplicate timestamps, unknown overlap timestamps, missing exact splice seam, no overlap, continuation corruption, stale current H1 and other safety faults remain blocking;
- Intel preactivation: `15/15 PASS`, `HEALTHY / PASS`, open positions `0`, unresolved intents `0`;
- new durable authorization created for exact commit `4c7cd7c...`;
- final re-arm: kill switch `ARMED` generation `58`, production task `Running`, entry gate `OPEN`, post-arm cycle count observed `1772`;
- no strategy, parameter, N4, TRAIL1, FULL/R15, 6% risk-cap or execution-model change.

The original Package 5 activation commit/evidence remain immutable historical provenance and are not rewritten by this operational hotfix.

The frozen production identity is unchanged:
`TRAIL1__N4_01__FULL__R15` — T3/H1/TRAIL1, N4
(`USDRUBF`, `CNYRUBF`, `GLDRUBF`, `IMOEXF`), FULL/R15, 1.5% of current
realized equity per new instrument position, maximum 6% nominal simultaneous
initial risk.

No forced trade was required to complete activation. Real orders are now permitted
only for genuine frozen-strategy signals while durable authorization, exact
identity/account bindings, `ARMED`, fresh `HEALTHY / PASS` production gate,
risk/margin gates, and all other runtime safety checks remain valid.

Current lifecycle state is **continuous production operation / monitoring**.
Historical pre-activation and failed-attempt sections below remain provenance only
and must not be read as current authorization state.

## Historical archive — Stage 8.11 early physical attempts (superseded for current status)

> **Historical only.** This archive preserves evidence from the failed/partial Stage 8.11 attempts. It does not define current project status. Current authority is the later Current handoff section, `authority_provenance.json`, and the active Stage 8.12 roadmap below.

`STAGE8_11_FIRST_PHYSICAL_ATTEMPT_FAILED_HTTP_400` is the canonical historical result. The accepted code commit was `069806355fc6931470d7f68d5ca6db20b06358fa`; the fixed request was `CNYRUBF` / `CNYRUBF@RTSX`, `LONG`, quantity `1`. Exactly one order-endpoint call returned HTTP 400. Physical evidence with SHA-256 `9FEFC5469F2C97F1EB36A5B5C99D323FA37BB948CF53C8A8745A27A06AB3B324` proves zero broker fills, `OPERATOR_INTERVENTION_REQUIRED`, and final kill switch `HALTED`. No retry and no controlled flatten occurred. The original physical evidence remains immutable and **did not PASS**.

`STAGE8_11_PRIOR_ONE_CONTRACT_AUTHORIZATION_CONSUMED`: the independently observed, structurally order-incapable `REAL_READONLY` recovery completed with schema `stage8_11_failed_attempt_recovery.v1` and `recovery_status = COMMITTED`. It terminalized only the historical `stage8.11:CNYRUBF:entry` ledger row as `REJECTED`, with `broker_order_id = NULL` and canonical unresolved intent count `0`. Fresh account-wide reconciliation passed, all positions were zero, and active broker order count was zero. This repository closeout does not retroactively change the failed physical result, constitute successful physical acceptance, or make the consumed authorization reusable.

Canonical lifecycle status:

- Stage 8.11.0 — **COMPLETE**.
- Stage 8.11.1 — **COMPLETE / PASS**.
- Stage 8.11.2 — **COMPLETE / PASS**.
- Stage 8.11.3 — prior explicit authorization **CONSUMED** by the first physical attempt; any broker-side retry requires a new explicit authorization after merge and independent audit.
- Stage 8.11.4 — **ATTEMPTED / FAILED HTTP 400 / NO ACCEPTED ENTRY PROVEN**.
- Stage 8.11.5 — **NO POSITION / BROKER CLEAN PROVED**.
- Stage 8.11.6 — **FLATTEN NOT SUBMITTED** because entry fill/position was not proved.
- Stage 8.11.7 — **COMPLETE / PASS / HISTORICAL INTENT RECOVERED**.
- Stage 8.11.8 — **COMPLETE / STAGE 8.11 CLOSEOUT**.
- Stage 8.12 — **NOT STARTED / NOT AUTHORIZED**.

Corrective code distinguishes acknowledged, definitive rejection, and uncertain submission outcomes; a definite HTTP 400 terminalizes its durable intent as `REJECTED` and can be `NOT_ACCEPTED_NO_EXECUTION` only after a fresh account-wide clean proof. POST-side 5xx and transport ambiguity remain `UNCERTAIN`, require reconciliation, and are never blindly retried. The current official PlaceOrder schema exposes `time_in_force`; the bounded market entry and flatten payloads now explicitly use the official `TIME_IN_FORCE_DAY` enum. A fresh exact-symbol FINAM schedule must prove that the timestamp is within `EARLY_TRADING`, `CORE_TRADING`, or `LATE_TRADING` immediately before every possible POST. Missing, malformed, stale/non-current, auction, clearing, closed, or outside-session evidence blocks before a new intent and with zero POSTs.

The recovery was repository-external `REAL_READONLY` evidence work only: it submitted no order, performed no cancellation, and did not retry physical acceptance. Stage 8.11 is closed while its aggregate result remains `STAGE_8_11_CONTROLLED_REAL_EXECUTION_ACCEPTANCE_NOT_YET_PASSED`. The kill switch remains `HALTED`, the Scheduled Task remains `Disabled`, and Stage 8.12 was neither started nor authorized. Any future physical retry requires a new explicit operator authorization.

`stage8.11.attempt2` was physically executed on 2026-10-05. Exactly one CNYRUBF@RTSX LONG quantity-1 entry POST was acknowledged by FINAM. Immutable `stage8_11_physical_acceptance_attempt2.json` evidence SHA-256 `0954B5C3D62444BA9AE59519386B0FC454D85C987BE1BAC04B82CA6C671B15A0` records `broker_order_present = true`, `final_position_quantity = 1`, zero active broker orders, zero proven fills at the instant of reconciliation, one unresolved `stage8.11.attempt2:CNYRUBF:entry` ACK intent, no controlled flatten, final `HALTED`, and `OPERATOR_INTERVENTION_REQUIRED`. The operator subsequently reported manually closing that one-contract broker position; that external manual close is not retroactive Stage 8.11 PASS. The observed defect is FINAM read-side eventual consistency: the immediate reconciliation required order/account/trade views to converge in one observation and stopped when the account position became visible before matching trade proof. The corrective attempt-3 code adds bounded GET-only convergence, reconciles the durable attempt-2 ACK without resubmitting entry, requires a broker-flat account, then uses fixed `stage8.11.attempt3` keys and create-only `stage8_11_physical_acceptance_attempt3.json` evidence for a clean repeat. Attempt 3 has not been physically executed by this code change. Stage 8.12 remains not started and not authorized.


## Current handoff

Stage 8.9 is **COMPLETE**. Stage 8.10 is **COMPLETE**. Stage 8.11 — Controlled Real Execution Acceptance — remains **COMPLETE / PASS**. Stage 8.12 — FULL/R15 Production Authorization — is **COMPLETE / PASS**. Stage 8.12.4 live activation is **COMPLETE / LIVE PRODUCTION ACTIVATED**.

Stage 8.11 remains the historical physical broker-acceptance authority: accepted commit `72a910e49b876cda99484a810e6f8a1b16ac0209`, immutable attempt `stage8.11.attempt7`, evidence SHA-256 `704BFCC19B1A63F490192C0D8D0E4715BFECF77664296AFEF47E5B80FBF64B5F`. At the Stage 8.11 closeout, `execution_authorized = false`, the production kill switch was `HALTED`, and the Scheduled Task was `Disabled`. That historical state is superseded by the Stage 8.12.4 activation below.

Canonical Stage 8.12.4 production activation authority:

- accepted production commit: `4c7cd7cbbde5fbffb63ed6984cf89b90dc50d129`;
- original live-activation commit (historical provenance): `883ea1ea6a8268276a8e39ebdc8786c643a21935`;
- Stage 5 data commit: `50f1fd2178c18b7ab3bd969be82ad01f47a34745`;
- Package 5 readiness evidence SHA-256: `FE383E9D269F699639D0F256CB15A303E0A5EE9CBC3990F802E10DCE8A41B7CD`;
- external activation evidence: `runtime/diagnostics/package5-live-activation/stage8_12_4_live_activation.json`;
- activation evidence SHA-256: `EA14B73FA1AE1D62C2324A0C76624DA792101FCD945383D70B646BDA1D6F8CB9`;
- durable production authorization: `AUTHORIZED`;
- `execution_authorized = true`;
- pre-arm heartbeat / reconciliation: `HEALTHY / PASS`;
- pre-arm unresolved intents / open positions / active protective stops: `0 / 0 / 0`;
- final production kill switch: `ARMED`;
- production Scheduled Task: `Running`;
- readonly Scheduled Task: `Disabled`;
- post-arm heartbeat occurred after the ARMED transition: `true`;
- post-arm heartbeat: `HEALTHY`;
- post-arm reconciliation: `PASS`;
- post-arm unresolved intents: `0`;
- post-arm open positions: `0`;
- post-arm active protective stops: `0`;
- post-arm production cycle count: `15`;
- no forced trade was required or submitted to complete Stage 8.12.

Canonical completion status: `STAGE_8_12_FULL_R15_PRODUCTION_AUTHORIZATION_COMPLETE`.

The frozen production identity remains `TRAIL1__N4_01__FULL__R15` with T3 / H1 / TRAIL1, N4, FULL/R15, 1.5% realized-equity risk per new instrument position and the existing 6% nominal initial-risk cap. No strategy, portfolio, parameter, research-methodology, sizing, or broker-runtime change is introduced by this repository closeout. The production service may submit real orders only for genuine frozen-strategy signals while the durable authorization, exact bindings, `ARMED` kill switch, fresh `HEALTHY / PASS` production gate, and all other runtime safety checks remain valid.

### Pre-activation package history — historical

Stage 8.9 is **COMPLETE**. Stage 8.10 is **COMPLETE**. Stage 8.11 — Controlled Real Execution Acceptance — is now **COMPLETE / PASS**.

Canonical Stage 8.11 physical acceptance authority:

- accepted code commit: `72a910e49b876cda99484a810e6f8a1b16ac0209`;
- immutable attempt: `stage8.11.attempt7`;
- external evidence: `runtime/diagnostics/stage8_11_physical_acceptance_attempt7.json`;
- evidence SHA-256: `704BFCC19B1A63F490192C0D8D0E4715BFECF77664296AFEF47E5B80FBF64B5F`;
- fixed physical case: `CNYRUBF@RTSX`, LONG, quantity `1`;
- exactly two real order-endpoint calls: one entry POST and one controlled flatten POST;
- broker fills proven: `2`;
- entry fill proven: `true`;
- one-contract position observed: `true`;
- controlled flatten proven: `true`;
- final position quantity: `0`;
- final active broker orders: `0`;
- unresolved Stage 8.11 intents: `0`;
- reconciliation result: `PASS`;
- physical result classification: `PASS`;
- final production kill switch: `HALTED`;
- Scheduled Task: `Disabled`.

The accepted normal reconciliation model is position-authoritative: after each physical POST, synchronous fill/risk authority is the exact `/account` position. Normal fill detection does not depend on `/trades`, exact `/orders/{id}`, `executed_quantity`, `remaining_quantity`, or the former order-status state machine. The physical authorization used for attempt7 is consumed. Current `execution_authorized = false`; real-order transmission remains unauthorized after the Stage 8.11 PASS.

Attempts 1–6, their failures/OIR classifications, manual closes, and recovery evidence remain immutable historical provenance and are not reclassified by the attempt7 PASS.

Stage 8.12 — **STARTED / STAGES 8.12.1–8.12.3 COMPLETE / STAGE 8.12.4 IMPLEMENTATION IN PROGRESS / NOT AUTHORIZED**. Stage 8.12.1 — Production runtime assembly — is **COMPLETE / PASS**. Stage 8.12.2 — Production path conformance and failure audit — is **COMPLETE / PASS**. Stage 8.12.3 — Intel production preflight — is **COMPLETE / PASS**.

Canonical Stage 8.12.1 authority:

- accepted merged code commit: `3f2d68ca0c327271fb543a0b63c0e8f842c855bd`;
- external test-only verifier evidence SHA-256: `F11FD6620A21F48499600392F49D3FC8A2340765B2B7B1C3C190822D8316513C`;
- structural zero-order boundary: `PASS`;
- Stage 8.12.1 runtime + N4 capacity tests: `25/25 PASS`;
- frozen Stage 7 / risk / margin regression: `166/166 PASS`;
- Stage 8.11 position-authority regression: `113/113 PASS`;
- independent Stage 8 audit: `PASS`;
- final operational audit: `PASS`;
- test-only real-order count: `0`;
- current `execution_authorized = false`;
- production kill switch: `HALTED`;
- production Scheduled Task: `Disabled`.

Canonical Stage 8.12.2 authority:

- accepted tested main commit: `2a15f4331afc1433dfbfd0464108e39e59d236f8`;
- external test-only verifier evidence SHA-256: `4F58595E2F62F2A377E5525972B9E88A136B2F9BC51760268D012AF94A70AE9F`;
- Stage 8.12.2 end-to-end + protective-stop conformance: `19/19 PASS`;
- Stage 8.12.1 runtime regression: `25/25 PASS`;
- R15 / margin / same-batch financial regressions: `144/144 PASS`;
- readonly account / H1 freshness / kill-switch regressions: `48/48 PASS`;
- Stage 8.11 bounded position-authority / timeout regressions: `113/113 PASS`;
- frozen research-to-robot / Stage 7 core conformance: `111/111 PASS`;
- independent Stage 8 audit: `PASS` (`262` checks);
- final operational audit: `PASS` (`149` checks);
- test-only real-order count: `0`;
- real order endpoint called: `false`;
- current `execution_authorized = false`;
- production kill switch: `HALTED`;
- production Scheduled Task: `Disabled`.

Stage 8.12.1 assembled the production runtime without adding FINAM order transport. Stage 8.12.2 completed the required TEST/AUDIT-only conformance with zero real orders. Stage 8.12.3 Intel production preflight is **COMPLETE / PASS** on accepted commit `0a40e3bf7a97f0c011d3a6f5216d9f61dd52ef30` with external evidence SHA-256 `9584F45186DE38ABAE9209E1F326255C783AF762CD736EA45718D19C93BC61B1`. Stage 8.12.4 Package 3 Intel exact-commit zero-order validation is **COMPLETE / PASS** on accepted commit `242c0a4bee0200da171d1a7451472b256241e170` with evidence SHA-256 `AB1D22A2BE4A748B5F25C21C56FEAC922CAE03499F6F41DF04A47F192A3E7D30` and focused rolling/service tests `33/33 PASS`. Package 4 initial funding recalculation is **COMPLETE / PASS** on accepted commit `a31080781e6c51de405d840d5cf30abd91c70ead` with external evidence SHA-256 `60D9C3EFEC7D54C50BF188B003DCE06D31647A9D6B6F0ED33BB46FF08475621B`. Post-funding revalidation is **COMPLETE / PASS / CAPITAL SUFFICIENT** on accepted commit `636b6a9abcec459173247f2c52b0d19470dfe738` with external evidence SHA-256 `54205165758FF6FC200290E61070D7082DFC13494048AABE7A5A61CDDE3C7F11`, HEALTHY production heartbeat, reconciliation PASS, zero unresolved intents, zero open positions, Stage 8.12.4 real order count `0`, and additional funding required: `0` in external evidence. Package 5 readiness is now **COMPLETE / PASS / LIVE ACTIVATION NOT PERFORMED** on accepted commit `883ea1ea6a8268276a8e39ebdc8786c643a21935` with external readiness evidence SHA-256 `FE383E9D269F699639D0F256CB15A303E0A5EE9CBC3990F802E10DCE8A41B7CD`, exact disabled production-task binding PASS, fresh GET-only financial authority PASS, additional funding required: `0`, and Stage 8.12.4 real order count `0`. Account financial values remain external to Git. durable production authorization: absent; `execution_authorized = false`; kill switch `HALTED`; production task `Disabled`; live activation performed: `false`. **Historical pre-activation snapshot:** at that time Package 5 live activation had not yet been performed. It subsequently completed, and current LIVE authority is the 2026-10-08 H1 hotfix rollover at accepted production commit `4c7cd7cbbde5fbffb63ed6984cf89b90dc50d129` recorded at the top of this roadmap.

## Governing research rule

The original H1 research lifecycle remains:

**Baseline → Optimization → Robustness → Walk Forward → TRUE OOS**.

v1/v2/v3 are immutable historical research generations. The active roadmap is
production specification + operational/broker readiness.

## Historical research generations

- v1 — historical discovery / MTF evidence.
- v2 — complete; all four final TRUE OOS studies `BORDERLINE`.
- v3 Perpetual — complete; T2/M30 `BORDERLINE`, T2/H1 `BORDERLINE`,
  T3/M30 `PASS`, T3/H1 `PASS`.

## Post-v3 Stages 1–6.x

Closed historical evidence:

- Stage 1 master consolidation;
- Stage 2 portfolio/diversification analysis;
- Stage 3 trade anatomy / failure analysis;
- Stage 4 structural hypothesis freeze;
- Stage 5 structural validation under `CORRECTED_SINGLE_C1`;
- Stage 6 / 6.x production-design and retrospective reassessment;
- focused N4 FULL four-case closeout.

The user explicitly selected TRAIL1 N4 FULL R15 from the final focused evidence.

## Stage 7 — Production Specification Freeze

**COMPLETE.**

Production specification:
`PROD_STAGE7_46DB784378797C7FB04636892350AFF21006D71A31F2CED9D4B974EDA2DC36B8`.

Active identity:
`TRAIL1__N4_01__FULL__R15`.

Frozen:

- v3 perpetual T3/H1;
- USDRUBF + CNYRUBF + GLDRUBF + IMOEXF;
- TRAIL1;
- FULL;
- R15 = 1.5% realized-equity risk per new position;
- max nominal initial risk 6%;
- no session filter;
- no pyramiding;
- no canonical fallback.

## Stage 8 — Robot / FINAM integration

**ACTIVE. LIVE TRADING NOT AUTHORIZED.**

Historical conformance:

- authority replay 418/418 exact;
- production replay 418/418 exact;
- deterministic hashes;
- zero mismatch classes.

All four production instruments remain `AUTHENTICATED_REAL_READONLY`.

## Stage 8.8 — operational hardening

Stage 8.8 operational hardening is COMPLETE.
Stages 8.8.1, 8.8.2, 8.8.3, 8.8.4, 8.8.5, 8.8.6, and 8.8.7 are COMPLETE.

### Stage 8.8.5

Status: `STAGE_8_8_5_STALE_DATA_PROTECTION_COMPLETE`.
Accepted source: `1c1c2bb5458827f200bc753e7e64db0272b33a8f`.
External evidence:
`C57554AE3AE54018EC1E558108520088C1883718F0406E7B6C6669B4696A9CBC`.

### Stage 8.8.6

Status: `STAGE_8_8_6_SQLITE_RECOVERY_INTEL_ACCEPTANCE_COMPLETE`.
Accepted code: `dc2b79e74817e71435eee20103ae617e13067d8e`.
External evidence:
`1A9B62D4BFC0E7384898C9DF9659E54E50E0E202BD44CE19413864AC2ECA14D6`.

Recovery hashes:

- backup `00b5e4ca2b389d55389b6b57ac73b5e557c11b72daab8d6e118311613e0aa3b0`;
- manifest `3d0ef1d7cb11ee592be32550625e8badefc596108f4d0c34eff6c5e12ceba822`;
- baseline logical state `13f01f1009768ddce65dce079f70486f2cbc2508cd1ea8ec4787414a78e0d3be`.

### Stage 8.8.7

Status: `STAGE_8_8_7_FINAL_OPERATIONAL_AUDIT_INTEL_ACCEPTANCE_COMPLETE`.
Accepted code: `bda46f57f0f977e05593c46b55851c40c4ad34fe`.
External evidence:
`181225F29A966179AB513121C3CBACD31401752956EFC9A22253A8EFBF94766E`.

Stage 8.8 is closed. It did not authorize execution.

## Stage 8.9 — funding / margin validation

**COMPLETE.**

Status:
`STAGE_8_9_REAL_ACCOUNT_FUNDING_MARGIN_VALIDATION_COMPLETE`.

Stage 8.9.8: `STAGE_8_9_8_COMPLETE`.

Accepted Stage 8.9.10 code:
`1013a5a2324e015ab3bc047a7b9af9064552cd10`.

Physical result:
`STAGE_8_9_10_POST_FUNDING_REVALIDATION_PASS=1`.
Classification: `STAGE_8_9_FUNDING_MARGIN_VALIDATED`.
Reason: `ALL_AUTHORITIES_VALID`.

Diagnostic SHA-256:
`C87400F845B73A666B95C83DA2E3B6B710F36F3210AD4AD175BFDABB453864D5`.

Physical summary SHA-256:
`099F85A0DCCF94D404411CFFAC2F5D8C80D606C5C1B5AA2F5B650E8BF5FEB636`.

Stage 8.9.8 portfolio variant SHA-256:
`60A529DB021B39E1C6117D01CCF3AB5B8B331073D407782E90383E4D124BADC5`.

Stage 8.9.8 financial shape SHA-256:
`EED27193E35F46FFCF13CFB4A2F2EAA4AB87A35F967D78139E97BFA885009371`.

Accepted counts:
`sizing_case_count = 8`; `positive_capacity_case_count = 4`;
`zero_capacity_case_count = 4`; `positive_batch_reservation_count = 1`.

Stage 8.9 proves financial/margin authority and some positive capacity only.
It does not establish positive capacity for all N4 instruments or authorize execution.

## Stage 8.10 — trading-token lifecycle

**COMPLETE.**

Overall status:
`STAGE_8_10_TRADING_TOKEN_LIFECYCLE_COMPLETE`.

### Stage 8.10.1 — Preconditions

Stage 8.10.1 is **COMPLETE**.
Status: `STAGE_8_10_1_TRADING_TOKEN_PRECONDITIONS_COMPLETE`.

### Stage 8.10.2 — Secure Provisioning

Stage 8.10.2 is **COMPLETE**.
Status: `STAGE_8_10_2_SECURE_PROVISIONING_COMPLETE`.
Accepted code: `f0c271e428c05ee0ff67b7941e342c06b48a42a0`.
External evidence:
`E5FEA93CE28006BC5ADA19F1AA1C1C365FF7CF4BE48A5A1B8BC8C5589DFD754D`.
Physical result: `STAGE_8_10_2_PHYSICAL_SECURE_PROVISIONING_LOCAL_PASS`.

### Stage 8.10.3 — Identity / Account Binding

Stage 8.10.3 is **COMPLETE**.
Status: `STAGE_8_10_3_IDENTITY_ACCOUNT_BINDING_COMPLETE`.
Accepted code: `428d285336380726a3ce00487e2c85eb755e2dd9`.
Physical result: `STAGE_8_10_3_IDENTITY_ACCOUNT_BINDING_PASS`.

### Stage 8.10.4 — Permission Boundary

Stage 8.10.4 is **COMPLETE**.
Status: `STAGE_8_10_4_PERMISSION_BOUNDARY_COMPLETE`.
Accepted code: `44858bacc2902591e11adc85cfa5f79e2b62dd5b`.
Physical result: `STAGE_8_10_4_TOKEN_PERMISSION_BOUNDARY_PASS`.

### Stage 8.10.5 — Offline Order Path

Stage 8.10.5 is **COMPLETE**.
Status: `STAGE_8_10_5_ORDER_PATH_DRY_VALIDATION_COMPLETE`.
Accepted code: `ba284e95954c8473c0e77a95172117bc5cefaf65`.
Physical result: `STAGE_8_10_5_OFFLINE_ORDER_PATH_DRY_VALIDATION_PASS`.

Validation was offline synthetic only. No real order endpoint was called.

### Stage 8.10.6 — Kill Switch / Safety Gates

Stage 8.10.6 is **COMPLETE**.
Status: `STAGE_8_10_6_KILL_SWITCH_SAFETY_GATES_COMPLETE`.
Accepted code: `35ec9007e6302d66e35e1a42a34fc2e77be8a467`.
Physical result: `STAGE_8_10_6_PHYSICAL_SAFETY_GATE_VALIDATION_PASS`.

Final kill-switch state: `HALTED`.
`execution_authorized = false`.

### Stage 8.10.7 — Intel Trading-Token Acceptance

Stage 8.10.7 is **COMPLETE**.
Status: `STAGE_8_10_7_INTEL_TRADING_TOKEN_ACCEPTANCE_COMPLETE`.
Accepted code: `df4bba6be4f98ba4659e13a01c90bec8e4162ff3`.
External evidence:
`A2A6B330A5DC1F15D67A84860223D80786022B634BB8B6CD73E01C815EE7D1B6`.
Physical result: `STAGE_8_10_7_PHYSICAL_INTEL_TRADING_TOKEN_ACCEPTANCE_PASS`.

Remote scope was session creation/details only. No order permission was tested.

### Stage 8.10.8 — Lifecycle Closeout

Stage 8.10.8 is **COMPLETE**.

Repository-only closeout established aggregate Stage 8.10 state:

- kill switch `HALTED`;
- `execution_authorized = false`;
- `real_order_endpoint_called = false`;
- `real_order_count = 0`;
- Scheduled Task Disabled;
- no LIVE authorization.

## Historical Stage 8.11 lifecycle snapshot — superseded

The detailed Stage 8.11 sub-gate text that previously occupied this location described the pre-attempt7 state and is no longer current roadmap authority. The immutable history of attempts 1–6 remains preserved in Git and in `TradingSystemLab/stage8_robot/authority_provenance.json`.

Current Stage 8.11 authority is only the Current handoff section above plus the machine-readable provenance:

- Stage 8.11 = `STAGE_8_11_CONTROLLED_REAL_EXECUTION_ACCEPTANCE_COMPLETE_PASS`;
- physical authority = `stage8.11.attempt7`;
- accepted code commit = `72a910e49b876cda99484a810e6f8a1b16ac0209`;
- evidence SHA-256 = `704BFCC19B1A63F490192C0D8D0E4715BFECF77664296AFEF47E5B80FBF64B5F`;
- entry and controlled flatten were physically proven;
- final broker position = `0`;
- final active orders = `0`;
- final unresolved intents = `0`;
- production kill switch = `HALTED`;
- current `execution_authorized = false`.

Do not derive current status from older Stage 8.11 attempt narratives.

## Stage 8.12 — FULL/R15 Production Authorization

**COMPLETE / PASS / FULL/R15 LIVE PRODUCTION ACTIVATED.**

Purpose: move the already frozen and physically accepted Stage 7 production system from controlled acceptance into unattended FULL/R15 production operation on the real FINAM account.

Stage 8.12 is an operational authorization/deployment stage. It is **not** a new research phase and must not change the strategy, portfolio, parameters, risk model, or research methodology.

Frozen authority carried into Stage 8.12:

- production specification: `PROD_STAGE7_46DB784378797C7FB04636892350AFF21006D71A31F2CED9D4B974EDA2DC36B8`;
- active identity: `TRAIL1__N4_01__FULL__R15`;
- strategy: T3 / H1 / TRAIL1;
- instruments: USDRUBF, CNYRUBF, GLDRUBF, IMOEXF;
- risk: 1.5% of current realized equity per new instrument position;
- maximum nominal simultaneous initial risk: 6%;
- quantity: automatic `min(R15 quantity, margin quantity)`, rounded down to trade lot;
- `final_quantity = 0` is a valid skip, not an error and not a reason to alter the frozen risk model;
- normal real fill/risk reconciliation remains position-authoritative using the exact broker account position;
- the Stage 8.11 one-contract quantity was acceptance-only and is not a production quantity cap.

### Stage 8.12.1 — Production runtime assembly

**COMPLETE / PASS / CODE-ONLY / NO REAL-ORDER AUTHORIZATION.**

Build the smallest production runtime by wiring together existing authenticated components rather than creating a parallel strategy implementation:

- `strategy_core.py` + `context_builder.py` + `trail1_state.py`;
- frozen Stage 7 specification and N4 registry;
- existing completed-H1 / freshness authority;
- existing R15 sizing and margin cap with same-batch local margin reservation;
- durable intent/state persistence and restart reconciliation;
- Stage 8.10 safety gate / kill switch;
- Stage 8.11 position-authoritative entry/exit reconciliation;
- trading-capable FINAM credential boundary already physically accepted in Stages 8.10–8.11.

Requirements:

- dedicated production runtime; do not weaken or convert the existing `REAL_READONLY` observer into an order-capable process;
- no strategy parameter changes, no new filters, no new session rule, no pyramiding, no fallback strategy;
- no implicit LIVE mode and no environment-only bypass;
- no order retry after an uncertain POST;
- normal fill proof must not reintroduce `/trades`, exact `/orders/{id}`, or the removed order-status state machine as synchronous authority;
- exits follow the frozen Stage 7 execution semantics; do not introduce new broker-native stop logic unless it is already part of the frozen authority.

Exit criterion: production code path exists but remains structurally incapable of real transmission without a separate Stage 8.12 authorization authority.

### Stage 8.12.2 — Production path conformance and failure audit

**COMPLETE / PASS / TEST-AUDIT ONLY / ZERO REAL ORDERS.**

Validate the assembled production path end-to-end without contacting the real order endpoint.

Minimum evidence:

- frozen research-to-robot conformance remains unchanged;
- genuine T3 signal -> FULL/R15 size -> durable intent -> synthetic order -> position-authoritative reconciliation -> TRAIL1 management/exit is deterministic;
- LONG and SHORT behavior;
- all four N4 bindings;
- zero-capacity signal cleanly skips with quantity `0`;
- R15 quantity can never be increased by margin logic;
- same-batch local margin reservation cannot over-allocate cash;
- aggregate nominal initial risk cannot exceed the frozen 6% authority;
- duplicate signal/restart cannot create a duplicate order;
- stale/malformed H1, account mismatch, unexpected position, active order, unresolved intent, reconciliation timeout, or invalid kill-switch state fail closed;
- restart/recovery preserves durable state and cannot silently reopen authorization;
- protective-stop adapter semantics are proven offline: initial server-side stop, TRAIL1 tighten-only updates, no stale/looser replacement, and no interval in which an accepted open position is considered safely protected without a broker-confirmed protective stop;
- the Stage 8.12.2 stop contract uses FINAM's documented 100%-of-current-position SL quantity semantics: a tighter protective stop is confirmed before it becomes the effective stop, older looser stops remain backstops during the open position, cancel-first replacement is forbidden, and local exit closeout requires aggregate terminal/inactive proof for all protective stops;
- real FINAM protective-stop acceptance is not inferred from the offline contract and is not authorized by Stage 8.12.2;
- both independent Stage 8 audits PASS.

Canonical closeout evidence:

- accepted tested main commit: `2a15f4331afc1433dfbfd0464108e39e59d236f8`;
- external TEST/AUDIT verifier evidence SHA-256: `4F58595E2F62F2A377E5525972B9E88A136B2F9BC51760268D012AF94A70AE9F`;
- end-to-end + protective-stop conformance: `19/19 PASS`;
- Stage 8.12.1 runtime regression: `25/25 PASS`;
- R15 / margin / same-batch regressions: `144/144 PASS`;
- readonly account / H1 freshness / kill-switch regressions: `48/48 PASS`;
- Stage 8.11 bounded position-authority / timeout regressions: `113/113 PASS`;
- frozen research-to-robot / Stage 7 core conformance: `111/111 PASS`;
- independent Stage 8 audit: `PASS` with `262` checks;
- final operational audit: `PASS` with `149` checks;
- real order endpoint calls: `0`;
- real order count: `0`;
- `execution_authorized = false`;
- production kill switch: `HALTED`;
- production Scheduled Task: `Disabled`.

Exit criterion: **PASS**. Exact tested production commit remained independently auditable with zero real-order transmission authorization. At the Stage 8.12.2 closeout, Stage 8.12.3 was the next gate; it subsequently completed under the Stage 8.12.3 authority recorded below.

### Stage 8.12.3 — Intel production preflight

**COMPLETE / PASS / REAL ACCOUNT / ZERO ORDERS / STILL NOT AUTHORIZED.**

Run one external Intel-host preflight on the exact accepted production commit.

Require:

- exact Stage 7 production ID and active identity;
- exact real account binding and trading-capable DPAPI credential;
- current broker account schema valid;
- no unexplained broker position or active order at the authorization boundary;
- no unresolved production intents;
- healthy reconciliation and fresh FINAM/H1 contact;
- frozen N4 registry valid and tradable;
- current realized-equity state and margin authority valid;
- sanitized N4 simultaneous positive-capacity report for one trade lot of each USDRUBF, CNYRUBF, GLDRUBF, and IMOEXF, using current directional initial margins plus strategy-consistent loss-per-contract;
- report fields: R15 equity floor, all-LONG margin floor, all-SHORT margin floor, worst-direction margin floor, base required capital, current available cash, and additional funding required;
- reserve scenarios reported separately at 0%, 10%, 20%, and 30%; the reserve is an operational funding buffer and does not alter the frozen 1.5% R15 risk model;
- kill switch `HALTED`;
- production Scheduled Task disabled/not running;
- `execution_authorized = false`;
- zero calls to the real order endpoint.

This preflight does **not** require every N4 instrument to have positive quantity. Each real signal is sized independently under R15 + available margin; quantity `0` means skip that entry.

Exit criterion: **PASS**. External sanitized evidence proves the exact production build is ready to proceed to the separate authorization gate while the account remains non-trading.

Canonical Stage 8.12.3 closeout evidence:

- accepted Intel preflight commit: `0a40e3bf7a97f0c011d3a6f5216d9f61dd52ef30`;
- external sanitized evidence: `runtime/diagnostics/stage8_12_3_intel_preflight.json`;
- external evidence SHA-256: `9584F45186DE38ABAE9209E1F326255C783AF762CD736EA45718D19C93BC61B1`;
- focused Stage 8.12 zero-order regression: `205/205 PASS`;
- independent Stage 8 audit: `PASS` with `262` checks;
- final operational audit: `PASS` with `149` checks;
- physical result: `STAGE_8_12_3_INTEL_PRODUCTION_PREFLIGHT_PASS`;
- exact Stage 7 production identity, real-account binding, trading-capable DPAPI credential, clean broker account, current reconciliation/H1 authority, frozen N4 binding/tradability, and production-state continuity: `PASS`;
- external evidence includes the required N4 simultaneous-capacity report and 0/10/20/30% reserve scenarios; exact account financial values remain external and are not reproduced in the public repository;
- real order endpoint calls: `0`;
- real order count: `0`;
- `execution_authorized = false`;
- production kill switch: `HALTED`;
- production Scheduled Task: `DisabledOrAbsent`;
- Stage 8.12.4 remains `NOT_STARTED_NOT_AUTHORIZED`.

### Stage 8.12.4 — Explicit FULL/R15 production authorization and activation

**COMPLETE / PASS / LIVE PRODUCTION ACTIVATED.**

**THIS GATE IS THE AUTHORITY FOR CONTINUOUS REAL PRODUCTION TRADING.**

Implementation started without activating execution. Current code boundary:

- durable authorization is repository-external, create-only, and exact-bound to production commit, sanitized account hash, frozen Stage 7 production ID/identity, and the accepted Stage 8.12.2 / Stage 8.12.3 evidence hashes;
- creating authorization requires a separate exact operator authorization phrase;
- production entry uses a production-aware heartbeat/reconciliation gate so legitimate frozen N4 positions do not become false safety faults;
- FINAM order transport includes market entry, dedicated SL/TP submission through `POST /v1/accounts/{account_id}/sltp-orders`, and emergency market exit;
- entry requires durable authorization plus `ARMED` and a fresh healthy production gate;
- protective-stop and emergency-exit transmission remain risk-reducing operations after authorization even if the kill switch later HALTs new entries;
- durable production authorization is present; `execution_authorized = true`; post-arm heartbeat/reconciliation is `HEALTHY / PASS`; the kill switch is `ARMED`; the production task is `Running`; the readonly task is `Disabled`; no forced trade is required for completion.

Stage 8.12.4 production-service prerequisites are **CODE READY / NOT AUTHORIZED**. Official FINAM H1 history is limited to 30 days, which is insufficient for the frozen T3 four-H1 context validity warm-up. Production history therefore seeds only from the exact Stage 5 TRAIL1 data authority (`market-pattern-data` commit `50f1fd2178c18b7ab3bd969be82ad01f47a34745`, exact frozen N4 H1 source SHA-256 values) and then appends completed FINAM H1 bars. The overlapping seed/FINAM interval must have an identical timestamp set and exact OHLC; any gap or conflict fails closed. Research CSV timestamps remain Moscow H1 open-times and are converted to the frozen `+1h` close-time index only after the exact splice. This prerequisite layer adds no order transmission and does not create production authorization.

Stage 8.12.4 Package 2 — production service + dedicated production Scheduled Task — is **IMPLEMENTED / NOT AUTHORIZED**. The continuous service uses the existing `ProductionRuntime`, exact frozen Stage 5 bootstrap + durable validated FINAM completed-H1 continuation, frozen T3/H1 context, TRAIL1, FULL/R15+margin sizing, durable intents, exact account-position/order reconciliation, percentage-of-current-position protective stops, TRAIL1 tighter-stop backstops, emergency exit, the adjusted realized-equity authority `equity - unrealized_profit - explained_external_cash_flows`, `InstanceLock`, and the production heartbeat. The separate `TradingSystemLab-Stage8-Production` installer registers the production task and immediately leaves it `Disabled`; the historical readonly task remains separate and must already be disabled. Package 2 creates no durable authorization, never changes the kill switch, never enables/starts the production task, and transmits no real order by itself. New-entry signal evaluation is not consumed while authorization is absent or the production entry gate is closed. The next fixed boundary is Package 3 exact-commit Intel zero-order validation; Package 3 is now started in validation-only code preparation and remains not physically accepted.


Post-Package-2 rolling-H1 corrective is **IMPLEMENTED IN CODE / NOT AUTHORIZED / PENDING PACKAGE 3 VALIDATION**. The exact Stage-5 H1 seed remains immutable. After the first exact seed↔FINAM overlap, only newly validated FINAM completed H1 bars are persisted under the existing `stage8-12-production.sqlite3` production state as a per-instrument append-only continuation with an integrity digest. On restart, the current 30-day FINAM window must overlap exactly with the combined Stage-5 + persisted continuation authority by timestamp and OHLC before any new bars are appended. This preserves the frozen T3/H1 warm-up after the original Stage-5 tail rolls out of FINAM's 30-day window. Missing overlap, timestamp/OHLC disagreement, continuation corruption, duplicate/order invalidity, or a downtime longer than the available overlap fails closed. No strategy/risk parameter, authorization, kill-switch state, task state, or order boundary changes in this corrective.

Package 3 — Intel exact-commit zero-order validation — is **STARTED / CODE READY / PHYSICAL INTEL EXECUTION NOT YET PERFORMED**. The validation wrapper is `TradingSystemLab/stage8_robot/deploy/windows/run-stage8-12-4-package3-zero-order-validation.ps1`. It requires a clean exact code commit, exact clean Stage-5 data commit, absent durable production authorization, kill switch `HALTED`, the dedicated production Scheduled Task installed and still `Disabled` with exact commit/current-principal binding, and the readonly task disabled or absent. It runs the existing foundation validator and independent audits, the focused rolling-H1/service tests, then exactly one unauthorized production-service cycle with `--once`. That cycle may perform FINAM authentication and GET/read reconciliation/H1 calls, but because authorization is absent the order transport is never constructed and no signal is consumed for entry. PASS additionally requires a healthy production heartbeat, zero unresolved intents, zero local/broker positions, all four durable rolling-H1 continuations, production task still `Disabled`, authorization still absent, kill switch still `HALTED`, and real-order count `0`. Evidence is written only outside the repository and SHA-256 hashed. Package 4 funding recalculation must not start until this physical Intel validation returns PASS.

The implementation must pass exact-commit zero-order validation before the separate final operator authorization and activation action.

Requires a new explicit operator authorization bound to:

- exact accepted production commit;
- exact Stage 7 production specification ID;
- exact account identity hash;
- exact active identity `TRAIL1__N4_01__FULL__R15`;
- passing Stage 8.12.2 audit evidence;
- passing Stage 8.12.3 Intel preflight evidence.

Activation semantics:

1. persist the production authorization outside the repository;
2. arm the production kill switch only after all gates pass;
3. enable/start the dedicated production Scheduled Task;
4. production runtime may submit orders only for genuine frozen-strategy signals;
5. **do not force a trade merely to complete Stage 8.12** — Stage 8.11 already proved the physical broker entry/flatten path;
6. the first production cycle must prove healthy account binding, data freshness, reconciliation, state continuity, and safety-gate state;
7. any startup/reconciliation/safety fault fails closed and returns the system to `HALTED`;
8. after authorization, normal restart may resume production only when the same durable authorization, production commit, specification ID, account identity, and ARMED kill-switch authority all still match exactly.

Stage 8.12 completion criterion — **MET**:

- canonical status = `STAGE_8_12_FULL_R15_PRODUCTION_AUTHORIZATION_COMPLETE`;
- dedicated production task installed/enabled for the frozen identity;
- first authorized production cycle healthy;
- no safety blocker or unresolved intent;
- no forced acceptance trade required;
- continuous production trading authorized only for the frozen Stage 7 identity and only while all runtime gates remain valid.

## Persistent constraints for Stage 8.12

Until Stage 8.12.4 is explicitly authorized:

- `LIVE_TRADING_NOT_AUTHORIZED` remains in force;
- `REAL_ORDER_TRANSMISSION_NOT_AUTHORIZED` remains in force outside the already consumed Stage 8.11 physical acceptance;
- production kill switch remains `HALTED`;
- production Scheduled Task remains disabled;
- `execution_authorized = false`.

Do not:

- change Stage 7 strategy, T3/H1 parameters, TRAIL1 semantics, N4 basket, FULL load, or R15 risk;
- add optimization, candidate selection, filters, ML, or a new research phase;
- require positive capacity for every N4 instrument;
- add a MICRO_LIVE cap;
- reuse Stage 8.11 one-contract acceptance as a production sizing rule;
- reintroduce complex order/trade reconciliation where exact account position is sufficient;
- mix TradingSystemLab with BBW / Level Touch / Round Level projects.

## Current roadmap boundary

**CURRENT GATE: Stage 8.12.4 — Explicit FULL/R15 production authorization and activation.**

Stage 8.12 is **STARTED / NOT YET AUTHORIZED**. Stage 8.12.1 is COMPLETE / PASS. Stage 8.12.2 is COMPLETE / PASS / TEST-AUDIT ONLY / ZERO REAL ORDERS. Stage 8.12.3 is COMPLETE / PASS / REAL ACCOUNT / ZERO ORDERS / STILL NOT AUTHORIZED. Stage 8.12.4 is **STARTED / IMPLEMENTATION IN PROGRESS / NOT AUTHORIZED**. The durable production authorization has not been created, the production kill switch remains `HALTED`, the production Scheduled Task remains disabled, and `execution_authorized = false`. Only a later explicit Stage 8.12.4 operator authorization bound to the exact accepted implementation commit may authorize continuous real production trading.
