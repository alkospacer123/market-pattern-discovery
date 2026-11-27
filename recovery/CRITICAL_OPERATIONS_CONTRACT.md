# Critical Operations Contract

Contract: COC-2026-01
Version: 1.0.0-rc.2
Status: C3_REVIEW_CANDIDATE_NOT_QUALIFIED
Scope: V20 Trading System, Control Center, Trading Research Lab и инженерный HANDOFF.

> Документальная conformance matrix и карта первоисточников. Это не runtime authorization, не разрешение на запись, Merge, deploy, ARM, LIVE или доступ к секретам. Матрица не заменяет кодовые gates, broker reconciliation, независимые испытания и решение владельца.

## 1. Обязательный запуск критической задачи

1. Зафиксируй task ID, владельца, цель, роботов/account aliases, среду, разрешённые источники и запрещённые side effects.
2. Прочитай действующие корневой/проектный `AGENTS.md`, Documentation Authority, паспорт и этот контракт на согласованном snapshot.
3. Применяй общий Git audit в [AGENTS](../AGENTS.md), предметные источники из [навигатора](kimi/README.md) и [HANDOFF](kimi/EXAM_AND_HANDOFF.md) при передаче. До отдельной приёмки C3 также применяй релевантные действующие Skills; не загружай все пять без необходимости.
4. Запиши версии и доступные identities контракта и Skills. Различай фактически загруженный Skill и чтение канонического `SKILL.md` как `SOURCE_FALLBACK`.
5. Если установленный Skill недоступен, найди канонический Markdown по реестру, проверь версию/blob и обозначь fallback. Не выдавай чтение файла за штатную загрузку или установку.
6. При недоступном обязательном источнике используй `SOURCE_UNAVAILABLE`/`BLOCKED`; при просроченном срезе — `STALE_SOURCE`. Недоступность не доказывает отсутствие.
7. При противоречии матрицы проверенному SOURCE зафиксируй `SOURCE_DRIFT`, сохрани оба locator и останови зависимый вывод. Не редактируй факт под матрицу.
8. Для явно ограниченного pinned offline checkout применяй `PINNED_OFFLINE`: не делай сетевой запрос к moving MAIN ради формальности и не заявляй current-MAIN status.

## 2. Доказательства и состояния

Разделяй:

- `MAIN/SOURCE` — авторитетная основная линия и точные исходные bytes на pinned commit;
- `DERIVED` — фактический результат ordered patches/сборки с provenance;
- `INSTALLED` — датированные identities развёрнутых файлов, launcher, dependencies и compatible state;
- `LIVE` — свежие процессы, switches, intents, positions/orders/fills/SLTP и внешние наблюдения;
- `RESEARCH/ARCHIVE/RECON` — исторические, экспериментальные и восстановленные материалы, не текущий допуск.

Для каждого существенного утверждения указывай evidence ID, locator, commit/blob/SHA256 соответствующего типа, время, операцию и предел применимости. Не смешивай commit SHA, Git blob SHA и SHA256 байтов.

Используй `PERFORMED_CHECK`, `HISTORICAL_EVIDENCE`, `INFERRED_RESULT`, `REPORTED_ONLY`; статусы `CONFIRMED`, `CONTRADICTED`, `UNKNOWN`, `BLOCKED`, `NOT_APPLICABLE`. `UNKNOWN` не является `PASS`.

Инварианты:

- вызов родительской функции не авторизует вложенный side effect;
- durable intent не доказывает POST; ACK не доказывает fill/cancel/active SLTP;
- fill не доказывает полную защиту; локальный `EXECUTED` не доказывает broker state;
- `ARMED`, Task `Running`, heartbeat и HTTP 200 не доказывают позицию, FLAT или SLTP;
- switch `HALTED` и durable `execution_halt` — разные состояния;
- отсутствие поля/`None` не превращай в ноль, FLAT или PROTECTED;
- digest/manifest подтверждает identity указанных bytes, не установку, исполнение или безопасность.

## 3. Hazard-first conformance

Для критической операции восстанови цепочку:

`entry point → callers → gates → durable intent/checkpoint → side effect → ACK → independent read-back → terminal state`.

Отметь `STATIC_OBSERVED`, `CONFIG_DEPENDENT`, `RUNTIME_UNVERIFIED`. Докажи первый side effect и достижимость проверяемого predicate. Ранний посторонний refusal не засчитывай как проверку целевого gate.

| ID | Hazard | Обязательная проверка | Запрещённый вывод |
|---|---|---|---|
| COC-GEN-01 | Неверный объект/среда | identity, robot/account alias, source→derived→installed→live | «GitHub совпал, значит LIVE совпал» |
| COC-GEN-02 | Пропущенный gate | фактический call path и каждый предикат | «родитель вызван, значит всё разрешено» |
| COC-GEN-03 | Unknown write | durable phase + независимая сверка | blind retry или очистка intent |
| COC-GEN-04 | Ложный terminal state | broker/read-back witnesses | ACK=fill/cancel/protected |
| COC-GEN-05 | Недоступный источник | точный отказ и coverage | отсутствие файла/события |
| COC-GEN-06 | Старый PASS | SHA/config/event/date/skips | перенос PASS на другой объект |

## 4. V20 — ARMED/HALTED и независимые gates

В таблице `HALTED` означает **только простой kill-switch HALTED**, без автоматического предположения о durable `execution_halt`, FLAT, исправном worker или известном broker state. Собственные gates операции обязательны в обоих столбцах. Таблица не добавляет разрешений и не отменяет временные, market, release, authorization, durable и broker gates.

| Операция | ARMED | Простой HALTED | Независимые условия и предел |
|---|---|---|---|
| ENTRY | Допускается только при всех entry gates | Отказ | completed causal signal, свежий NEXT_OPEN, риск/quota/GO, отсутствие запрещающего durable halt, one-shot intent и broker checks |
| INITIAL_SLTP | Не запрещён самим ARMED | Не запрещён **только из-за** простого HALTED | фактические fills/position, точный VWAP/quantity/stop, ownership, one-shot protection, свежая брокерская проверка и полное coverage |
| Protect3 cancel-first | Требуется ARMED плюс все Protect3 gates | **Запрещён отдельным ARMED-gate до cancel** | release/auth/permit/identity, executable quote, current 100%-stop ownership, durable transition и read-back |
| Фактический HOLD5 exit | Не запрещён самим ARMED | Не запрещён **только из-за** простого HALTED | broker-proven sixth Open, 60-second window по действующему DERIVED, quantity/current SLTP checks, one-shot exit; отдельного ARMED-gate в показанном пути нет |
| cancel-after-flat | Не запрещён самим ARMED | Не запрещён только из-за простого HALTED | свежий broker-FLAT proof, точное владение защитной заявкой и допустимость отмены; unknown cancel не повторять |
| reconciliation | READONLY, ARMED не требуется | READONLY, ARMED не требуется | свежие positions/orders/fills/SLTP; GET-only recognition не выполняет writes |

Формулировка «не запрещён только из-за HALTED» не означает гарантированное исполнение. Любой собственный отказ, unknown state или несвежий witness останавливает операцию. Остановленный Task и сбой до соответствующего кода не компенсируются этой таблицей.

### COC-V20-ENTRY — вход и риск

- Используй действующие frozen-функции и причинно доступные завершённые данные.
- Сохраняй атомарность сигнала, риск-резервации, session quota и intent; повтор границы не создаёт второй вход.
- Не смешивай деньги, резервации, ГО и риск разных роботов/счетов.
- Неизвестный POST запрещает retransmit; `NEVER_POSTED` признавай только полным действующим recovery predicate: точный durable status, отсутствие pre-POST/submission checkpoint, broker ID и конфликтующих durable записей (включая flat cleanup), свежая broker reconciliation без позиции/активной заявки, транзакционная повторная проверка. Не очищай unknown submitted intent; не возвращай автоматически сигнал, риск или quota.
- Account-bound equity, available funds, ГО, tick value/step, lot, costs и snapshot revision обязательны. Отличай pending reservations от уже учтённого broker ГО по точным client IDs; не вычитай средства повторно. После fills пересчитывай по фактическому qty/VWAP/stop и costs, не суммируй повторно бюджет и fees; сохраняй консервативную нижнюю границу (текущая модель max бюджета и известных fees), точную формулу сверяй с DERIVED. Per-trade и account limits обязательны.

### COC-V20-INITIAL-SLTP — первая и текущая защита

- При partial fill защищай фактическую позицию своевременно; не жди полный fill ради TP.
- После каждого изменения позиции пересчитывай суммарное effective stop coverage.
- Не объявляй `PROTECTED` при частичном/unknown coverage и не создавай избыточную вторую защиту.
- Не отменяй проверенный stop только из-за изменения VWAP; ошибка переоценки не разрешает снять защиту.

### COC-V20-PROTECT3 — граница отказа и cancel-first transition

Действующий `stage_r070_protect3_cancel_first_once(...)` имеет ранние scope/transport/release/auth/ARMED/permit/durable/broker checks до cancel-first `try`. До durable `CANCEL_OUTCOME_UNKNOWN` внешний cancel ещё не начат.

- При HALTED/unknown switch ранний ARMED-gate обязан отказать **до отмены старого stop**.
- После начала transition различай `CANCEL_OUTCOME_UNKNOWN` → `CANCEL_ACK_UNVERIFIED` → `CANCEL_PROVED_UNPROTECTED` → `NEW_POST_OUTCOME_UNKNOWN` → `NEW_ACK_UNVERIFIED` → `PROTECTED`.
- `PROTECT3_UNPROTECTED_OR_UNKNOWN` устанавливается исключениями **внутри соответствующего cancel-first `try/except`**. Не приписывай эту запись всем ранним authorization/preflight отказам.
- После исключения в этом переходе допускай возможный незащищённый интервал: stop новые входы предусмотренным fail-closed контуром, эскалируй, не повторяй writes.
- Restart recognition — GET-only. `PROTECTED` принимай только после свежей точной сверки преемника, старого stop и всей позиции.

### COC-V20-HOLD5 — основной R088 LIVE path

Пять наблюдаемых сессий включают вход; выход — на первом подтверждённом Open шестой. Календарные дни не заменяют broker-observed sessions.

Основной DERIVED R088 path по BASE + ordered patches, включая patch №7:

`finam_live.run_cycle → _follow_existing → свежий broker M15 boundary → r088_hold5.hold5_from_broker_boundary → hold5_observed_session_exit → decision EXIT_AT_SIXTH_OBSERVED_SESSION_OPEN → sender.submit_frozen_exit_once → broker read-back/flat cleanup по собственному контракту`.

- В `hold5_from_broker_boundary` и `hold5_observed_session_exit` нет SQLite, FINAM order или ARMED side effects.
- В показанном ветвлении `_follow_existing` до `submit_frozen_exit_once` нет отдельного ARMED-gate. Не добавляй его документационным выводом и не считай остальные gates отключёнными.
- `submit_frozen_exit_once` повторно проверяет boundary, время, broker position/quantity и текущую активную защиту, включая подтверждённый Protect3 replacement.
- ACK выхода не доказывает FLAT; stop сохраняется до доказанного flat и последующей разрешённой cleanup.

Для пропущенной шестой сессии в **основном R088 LIVE path** различай три слоя:

1. return decision: `MISSED_OR_PASSED_SIXTH_SESSION_OPEN_HALT`;
2. durable marker: `FROZEN_EXIT_OPEN_MISSED`;
3. итоговый error code: `V20_LIVE_FROZEN_EXIT_DEADLINE_MISSED`.

Не создавай поздний market exit по прошедшему Open. Не смешивай эту тройку со single-trial path, где patch №7 содержит `R088_SIXTH_SESSION_OPEN_MISSED` и `TRIAL_CYCLE_DEADLINE_MISSED`.

BASE `finam_live.py` содержит TIME3 и не является полным R088. Для source claim используй BASE + девять ordered patches; исторический derived blob не является свежим INSTALLED/LIVE PASS.

### COC-V20-RESTART — восстановление

Восстанавливай entry/fills, session observations, риск/quota, intents и protection transitions из согласованных durable/broker данных. Не удаляй unknown intents и не восстанавливай потреблённые сигнал/риск/quota автоматически. ARM/rearm, deploy, rollback и broker writes требуют отдельных полномочий.

## 5. Control Center — наблюдение и операторские команды

### COC-CC-01 — раздельные контуры

READONLY path:

`explicit operator refresh → manual/cross-process gate → pinned one-shot exporter → check-only inputs → CC-owned snapshot → trusted receiver/policy/ACL → schema/digest/binding/TTL → UI cache/render`.

Operator path:

`UI → admin adapter → pinned privileged controller → stock V20 operator/launcher → Task/switch + audit → bounded READONLY postflight`.

Не объединяй staged inbox/gateway с действующим operator path без доказанного imports/channel policy. Startup, rerun, navigation и dialog не считай READONLY без проверки side effects.

### COC-CC-02 — UI и freshness

- Различай `NOT_CONNECTED`, `UNKNOWN`, `STALE`, `HALTED`, `FAULT`, `HEALTHY`.
- Разделяй attempt time, `observed_at`, heartbeat, event, publication, receipt и render.
- Heartbeat freshness не отменяет FAULT/HALT и не доказывает broker truth.
- После STALE/UNKNOWN не сохраняй прежние положительные текущие метрики как достоверные.
- `positions_local`, `stops_local`, `unresolved_local = None` не превращай в нули/FLAT/PROTECTED.

### COC-CC-03 — команды и unknown outcome

- PAUSE/HALT не доказывает flat, остановку Task или прекращение сопровождения.
- Для STOP проверяй предусмотренный порядок FLAT → HALT → повторный FLAT → Task stop → not Running.
- Для non-PAUSE применяй собственные release/preflight/FLAT gates действующего CC-07; не перенос approval между командами.
- `FAILED_UNKNOWN`, timeout, неполный stdout или неоднозначный postflight запрещают повтор регламентом. Технический interlock ручного повтора с новым ID отдельно не доказан.
- Request ID коррелирует попытку, но не доказывает dispatch/fill/terminal state. Отказ до генерации ID не обязан иметь ID.
- В MAIN `v20_app.py` request ID **не отображается в UI**. Offline-кандидат G5.3.1 исправляет отображение/correlation, но не считается установленным; не описывай его как MAIN/INSTALLED fix.

### COC-CC-04 — RECOVER proof и ответ адаптера

Различай:

1. внутренний stock/controller `proof` refusal и его конкретный code;
2. распознавание wrapper output адаптером;
3. итоговый response class и request ID;
4. независимый postflight/broker state.

Только распознанные адаптером `RECOVER_PREFLIGHT_CODES` отображаются как `REFUSED_PREFLIGHT`. Другой внутренний preflight code или нераспознанный stderr может дать `FAILED_UNKNOWN`. Не приравнивай любой wrapper refusal к итоговому `REFUSED_PREFLIGHT` и не переименовывай unknown child failure в безопасный отказ.

RECOVER принимает только строго разрешённые Task/switch/cycle/code states. Age `-5..90` относится к Running/HALTED, а не универсально ко всем состояниям. Durable `execution_halt` не обходить; V20 ARM сохраняет собственный отказ.

## 6. Trading Research Lab — причинность и воспроизводимость

| ID | Обязательный контроль | Недопустимое расширение вывода |
|---|---|---|
| COC-TRL-01 | raw/normalized/loaded bytes, provenance, coverage, OHLCV quality | manifest без фактических входов = replay |
| COC-TRL-02 | source→available→signal→order→fill timestamps, ZERO LOOK-AHEAD | future/aligned timestamp без as-of logic |
| COC-TRL-03 | frozen protocol, costs/GO/lots/liquidity, event ledger | красивый PF компенсирует неверную модель |
| COC-TRL-04 | Свободный поиск по опыту V20; ZERO LOOK-AHEAD с первого теста; Robustness и WF только перспективным кандидатам (WF при достаточной истории); честный OOS-статус, без обязательной цепочки этапов | повторный запуск/новый год = untouched OOS |
| COC-TRL-05 | clean replay, signals/refusals/orders/fills/ledger/cash/GO/equity witnesses | совпадение Net/PF/N = полная воспроизводимость |

`REPRODUCIBLE_VERIFIED` ограничен фактически воспроизведёнными кодом, входами, конфигурацией и witnesses. Не присваивай идентичность недоступному оригинальному R097 engine по восстановленному коду или output parity; обозначай `SOURCE_BYTE_IDENTITY_NOT_PROVEN` и фактический replay scope.

2018–2026 уже использованы в исследовании и не являются untouched TRUE OOS. Research leader, `CANDIDATE`, `OWNER_SELECTED`, `APPROVED_FOR_IMPLEMENTATION`, `INSTALLED` и `LIVE` разделены. TRL не изменяет V20/FINAM и не выдаёт LIVE-разрешений.

## 7. Skills, документация и HANDOFF

- Канонические Skills находятся в `recovery/kimi/skills/<name>/SKILL.md`; резервные копии — в профильных knowledge folders.
- Копии одной версии должны быть побайтово идентичны указанному source_commit/blob; historical pin не равен current MAIN. Не редактируй backup самостоятельно и не синхронизируй версии молча. Цель C3 (решение владельца 27.11) — канонические документы плюс проверяемый экспорт без зеркал и без пяти собственных активных Skills. До проверенного покрытия/fallback и отдельного разрешения на отключение/удаление прежние копии и Skills сохраняются. Переход не отменяет operation-specific gates, независимую проверку или отдельные разрешения.
- Integration manifest фиксирует подготовленные bytes, но не доказывает фактическую установку Skill, активацию, доступность механизма или qualification.
- Профильные документы ссылаются на IDs этой матрицы и не создают конкурирующие копии правил.
- Исторические отчёты, FAIL/PASS, protocols и Journal не переписывай; исправления оформляй append-only addendum/erratum.
- HANDOFF_ACCEPTED не означает TESTED, MERGED, INSTALLED, LIVE_PASS, QUALIFIED или COLD_RESTORE_PASS.

## 8. Независимая квалификация и STOP

Принятые G0–G6/A/B проверки не повторять. Остаточные обязательные evidence gaps — по [Roadmap](../ROADMAP.md) и [KDR](kimi/KIMI_DEFECTS_AND_REMEDIATION_REGISTER.md), с одной целевой C3 приёмкой изменённых компетенций/fallback. Для критического изменения — закреплённый oracle, positive/negative reachability и controlled mutation там, где требует контракт; critical failure budget = 0. Не создавать параллельную state machine и не заменять независимое доказательство саморевью.

Немедленно останови затронутую часть при unknown write/command outcome, возможной потере stop, критичном `SOURCE_DRIFT`, неустановленной identity, отсутствии полномочий или mandatory independent gate. Безопасную отделимую работу заверши как `PARTIAL`; критичную недостижимую цель — `BLOCKED`.

`KDR-001=CLOSED_OWNER_ACCEPTED_20261126`; G6 принят в проверенном scope. [Акт A](kimi/BLOCK_A_ACCEPTANCE_20261126.md) и [KDR](kimi/KIMI_DEFECTS_AND_REMEDIATION_REGISTER.md) содержат основание и пределы; первоначальный G6.2 CRITICAL FAIL сохранён в Git history, recurrence reopens. Другие KDR и полная автономность/installed/LIVE/cold restore не закрываются автоматически.

## 9. Source authorities для этой редакции

Исторический срез rc.1: MAIN `2de8c212e29b2c589434a789cd81d6b3816ff28a`; Draft #597 head `90916c01bf85c3f9d5ef2ddcb70481845458d4ae`. [Integration manifest](CRITICAL_OPERATIONS_INTEGRATION_MANIFEST.json) — историческая подготовка #599, не manifest rc.2. C3 candidate rc.2 на принятом MAIN `2ac85eb5bcdd8757144898b5a27369329f4d125c`, исходном HEAD #608 `f723a4f172b1df62696a60f5ff66112cac9d5643`; это не новое runtime evidence. Resolve refs заново.

| Область | Первоисточник |
|---|---|
| Приоритет документов | `AGENTS.md`; `recovery/DOCUMENTATION_AUTHORITY_2026-11-22.md` |
| V20 release/DERIVED | `V20_TradingSystem_M15/R088_ARCHITECTURE_AND_SAFETY_20261122.md`; ordered `V20-08/*.patch` |
| ENTRY/exit/flat | `v20_runtime/finam_live.py`; `v20_runtime/finam_execution.py`; R088 patch №7 |
| Protect3 | `v20_runtime/r070_linked_sltp.py`; `v20_runtime/tp6_protect3.py` |
| HOLD5 | `v20_runtime/r088_hold5.py`; R088 patch №7 |
| CC command path | `ControlCenter/v20_admin_control.py`; `ControlCenter/v20_app.py`; `controller/cc07-v20-operator.ps1` |
| CC READONLY path | `deployment/v20_live_export.py`; `cc/v20_receiver.py`; `cc/v20_contract.py` |
| TRL | действующие Start Here, Closeout, Artifact Manifest, Research Methodology, Operating Cycle и primary research records |
| Квалификация | текущий Roadmap, KDR, принятые evidence records и остаточные gates |

Перед применением заново разреши moving refs и проверь актуальные source paths. Эта карта не утверждает INSTALLED/LIVE состояние и не делает датированные evidence свежими.
