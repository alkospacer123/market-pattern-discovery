# TradingSystemLab — аудит STOP / TICK GRID

Дата: 12.10.2026, Europe/Moscow. **Вердикт: NEEDS FIX. PRODUCTION_CHANGES=NONE.**

Это диагностика и проект execution-изменения. Исправление не реализовано в production-коде. Новых исследовательских фаз, оптимизации, переселекции и пересчёта доходности после округления нет.

## Проверенные источники и границы выводов

- GitHub main при начале: `688560ec2e8a71c1085bec255a9660783b51e122`, независимо прочитан через `git ls-remote`.
- Указанный действующий production commit: `184e8c2b8fa092a606249ff293a4f507160bff29`; его исполняемые файлы Stage 8 и frozen Stage 7 совпадают с проверенным main. Между ними существуют ранее внесённые изменения документации/provenance; это не изменения данного аудита.
- Изолированная ветка: `audit/stop-tick-grid-20261012`, от проверенного main. Все новые артефакты только в `audit_only/stop_tick_grid_20261012/`.
- Frozen market data: `alkospacer123/market-pattern-data@50f1fd2178c18b7ab3bd969be82ad01f47a34745`. CSV проверены побайтно по Git blobs и четырём хешам frozen manifest. Локальные основные checkout репозитория и данных не изменялись.
- Параметры: `T3-H1-4e73cdb77246`, EMA100/slope5, ADX14>20, context ATR14>mean20, shifted Donchian20, initial stop 2.5 H1 ATR14, trail 3 ATR, TRAIL1. Stage 7 identity: `TRAIL1__N4_01__FULL__R15`.
- Свечи open-labelled переведены в availability timestamps добавлением 1 часа. Context — только завершённые группы четырёх H1 в одном московском дне; используется последний context с close ≤ signal close. ATR/EWM/Donchian причинные. Для реальных LONG/SHORT всех четырёх инструментов отдельно проверен prefix, физически отсечённый на сигнале.

| Инструмент | H1 строк | Первый доступный close, MSK | Последний доступный close, MSK | step | tick value, RUB |
|---|---:|---|---|---:|---:|
| USDRUBF | 17 116 | 26.04.2022 11:00 | 16.09.2026 00:00 | 0.01 | 10 |
| CNYRUBF | 17 116 | 26.04.2022 11:00 | 16.09.2026 00:00 | 0.001 | 1 |
| GLDRUBF | 13 685 | 11.07.2023 11:00 | 16.09.2026 00:00 | 0.1 | 0.1 |
| IMOEXF | 12 251 | 14.11.2023 11:00 | 16.09.2026 00:00 | 0.5 | 5 |

Всего 60 168 H1. Последний close относится к исходной свече 15.09.2026 23:00. Все Open/High/Low/Close находятся на указанных сетках. Economics взяты из `production_instrument_registry.csv`, с authenticated REAL_READONLY binding и frozen MOEX tick-value reference. Независимый временной архив изменений спецификаций за каждый день отсутствует: выводы о сетке используют эти проверенные N4 economics, а не выдуманную историю спецификаций. Реальные исторические equity, available cash, directional margin, fill prices, брокерские статусы и журналы LIVE недоступны.

Утверждение о 12 сигналах за 16.09–11.10.2026 **не подтверждено данным аудитом**: этот интервал отсутствует в frozen источнике. Более новый checkout данных не подменял frozen-историю.

## ROOT_CAUSE

`DecisionCore.signal()` вычисляет float stop как `bar.close ± 2.5 * bar.atr`; ATR — причинное EWM, оно не обязано быть кратным price step. `ProductionRuntime.plan_entry()` передаёт `Decimal(str(entry))` и `Decimal(str(initial_stop))` в `risk.size_position()`. Последний требует **точного** равенства `distance / step` целому Decimal. Иначе runtime возвращает `SKIP_STOP_NOT_ON_TICK_GRID`, qty=0, без durable order intent и резервирования маржи; pending signal потребляется.

Технически проверяется сетка **расстояния**, а не обе абсолютные цены по отдельности. Для исследованной выборки entry на сетке, поэтому off-grid distance эквивалентен off-grid stop. В общем случае два off-grid price с целым расстоянием могут пройти эту проверку; будущая execution-проекция должна валидировать обе цены.

Это не преимущественно float noise: ни один отказ не лежит в пределах `1e-10` тика от целого. Причина — несовместимость непрерывной ATR-цены с дискретной биржевой ценой, усиленная строгим Decimal boundary. Ослабление сравнения или подавление исключения не задаёт допустимый защитный стоп.

Stage 7 `risk_and_sizing_contract.md` прямо требует блокировать non-integral ticks. `research_to_robot_conformance.md` требует точного initial stop/R и всех TRAIL1 transitions. Runtime реализует этот fail-closed контракт; замороженная исследовательская модель сама не обеспечивает его исполнимость.

## HISTORICAL_SIGNAL_COUNT / OFF_GRID_COUNT / PERCENT

Сигнал, исследовательский вход и реальная заявка — разные объекты.

**Полная доступная непрерывная история**, frozen candidate parameters, причинный warm-up от первого доступного бара каждого инструмента: **1 422 raw T3 срабатывания**, entry on-grid 1 422, stop on-grid 0, distance on-grid 0, **STOP_NOT_ON_TICK_GRID 1 422 / 100%** при изолированном funded-flat вызове текущего planner. Без tick gate исследовательский lifecycle допускает 399 входов: 397 завершённых и 2 открытых на конце. Эти числа не являются новым OOS-результатом и не содержат adjusted PnL.

| Инструмент | 2022 | 2023 | 2024 | 2025 | 2026 YTD | Всего raw / off-grid |
|---|---:|---:|---:|---:|---:|---:|
| USDRUBF | 40 | 125 | 108 | 74 | 89 | 436 / 436 |
| CNYRUBF | 33 | 77 | 79 | 87 | 90 | 366 / 366 |
| GLDRUBF | 0 | 25 | 104 | 90 | 102 | 321 / 321 |
| IMOEXF | 0 | 0 | 112 | 114 | 73 | 299 / 299 |
| Всего | 73 | 227 | 403 | 365 | 354 | 1 422 / 1 422 |

Нули до начала доступности — отсутствие данных/сигналов, не признак длительного наблюдения инструмента.

**Frozen lifecycle windows**, с исходными cold starts, WF01–WF04 и candidate parameters соответствующего Stage 6 authority replay:

| Период | Raw условия T3 | Допускаемые входы, включая terminal open | Завершённые сделки ledger | Off-grid допускаемых входов |
|---|---:|---:|---:|---:|
| Baseline | 605 | 172 | 171 | 172 / 100% |
| WF24 | 226 | 64 | 63 | 64 / 100% |
| Historical TRUE OOS | 665 | 186 | 184 | 186 / 100% |
| Сумма отдельных replay | 1 496 | 422 | 418 | 422 / 100% |

| Период | USDRUBF raw / входы | CNYRUBF raw / входы | GLDRUBF raw / входы | IMOEXF raw / входы |
|---|---:|---:|---:|---:|
| Baseline | 219 / 58 | 145 / 48 | 129 / 40 | 112 / 26 |
| WF24 | 56 / 14 | 57 / 14 | 53 / 21 | 60 / 15 |
| Historical TRUE OOS | 148 / 44 | 158 / 50 | 187 / 41 | 172 / 51 |

| Период / entry year | Raw | Входы | Завершённые |
|---|---:|---:|---:|
| Baseline 2023 | 202 | 59 | 59 |
| Baseline 2024 | 403 | 113 | 112 |
| WF24 2024 | 226 | 64 | 63 |
| TRUE OOS 2025 | 311 | 91 | 91 |
| TRUE OOS 2026 | 354 | 95 | 93 |

Все строки таблиц отказов — 100% off-grid. Полный instrument × year × lifecycle breakdown находится в `results.json`. WF пересекается по календарю с Baseline; **1 496 нельзя называть числом уникальных исторических сигналов**. В lifecycle raw-таблице 1 270 уникальных instrument/timestamp/direction, во входах 362. Даже одинаковый timestamp может иметь разные ATR из-за cold start; эта дедупликация не устанавливает равенство стопов. Непрерывный прогон отличается от cold-start OOS также состоянием и EWM seed; его 1 422 не подменяют 665 OOS срабатываний.

Открытые terminal entries: Baseline IMOEXF 1; WF04 IMOEXF 1; TRUE OOS GLDRUBF 1 и IMOEXF 1. Удаление их из signal count ошибочно. Существующий ledger хранит только 418 завершённых сделок.

Вызов `plan_entry()` проверен отдельно для всех 1 496 lifecycle raw и 1 422 continuous raw: **2 918 изолированных вызовов** с synthetic equity 100 000 RUB, cash 1 000 000 RUB, LONG margin 100 / SHORT 120 RUB. Все вернули именно tick-grid skip. Часть сигналов повторяется между прогонами; 2 918 — число проверок, не уникальных сигналов и не реальных заявок.

## Другие ограничения исполнения

При валидной instrument authority и чистом состоянии tick check происходит до margin cap, zero quantity и aggregate-risk check. Поэтому для этих изолированных вызовов доказан именно tick-grid отказ; никакого order endpoint нет.

В настоящем LIVE раньше могут заблокировать вход: отсутствие authorization/open gate, kill switch, active-session/data readiness, неподтверждённая спецификация, уже открытая позиция по инструменту, unresolved intent или reconciliation fault. После исправления сетки сохраняются zero R15 quantity, directional margin cap, локальный cash budget, лимит nominal risk 6%, доступность торгов и защитного SL/TP. Некоторые дальнейшие raw сигналы в исследовании заблокированы открытой позицией — поэтому raw count больше entry count.

Число исторических отказов по cash/margin/6%/authorization **INCONCLUSIVE**: нет соответствующих исторических account snapshots. Считать все 1 422 реально отвергнутыми заявками FINAM нельзя. Planner до broker transmission не дошёл. Историческая 30-day/live-window подготовка данных и фактические operational gates не воспроизводились как журнал работающего сервиса.

## OOS_IMPACT и классификация

`RESEARCH_SIGNAL_CONFORMANCE = PASS` — заново выполнены два независимых пути: research authority и production decision core. Оба воспроизводят **418/418** frozen TRAIL1 trades: 171 Baseline, 63 WF, 184 historical TRUE OOS; отсутствуют missing/extra, direction/time/price/state/R mismatches в установленном Stage 6 `%.12g` контракте.

`LIVE_EXECUTION_CONFORMANCE = FAIL` — на этих же непрерывных исходных стопах текущий planner не создаёт entry intent. Для исторического TRUE OOS это все 186 допускаемых входов, включая 184 завершённых. Исполняемый код не воспроизводит этот trade stream при текущем tick gate.

`OOS_EXECUTABILITY_VERIFIED = NO` — исходный TRUE OOS и Stage 6.7 не моделировали реальные FINAM price grid, integer contract quantity, margin/account state и реальные fill prices. Original `Backtester` использует `FixedRiskPortfolio.size()` с дробным quantity и `point_value=1`; `FROZEN_TICK_SIZE=0.001` применяется как normalized C1 cost tick, не как биржевая валидация цены. Stage 6.7 `simulate_events()`/four-case `simulate()` используют `risk_cash = realized_equity * 0.015`, `PnL = risk_cash * strategy_R`, без floor-to-contracts и margin.

Следовательно, FULL действительно не делит бюджет на четыре, но проценты Stage 6.7 — математическая R/equity модель. Они не доказывают RUB доходность, количество контрактов или фактический initial loss на FINAM. Нельзя объявлять исторический OOS ошибочным только из-за off-grid цены; **его исполнимость и перенос доходности в LIVE не доказаны и текущим кодом нарушены**.

Отдельно сверён исходный canonical TRUE OOS: **199/199** entry/exit/direction/price paths и C1 costs воспроизведены; все 199 реконструированных initial stops off-grid. Архивная таблица не содержит initial_stop, поэтому стопы восстановлены причинным canonical replay, без вывода из округлённого cost_R. В ней сохраняется известное legacy double-C1: поле gross_R фактически уже вычитает один C1, net_R_C1 вычитает два. Уравнения подтверждены с max delta `4.880362780568248e-11`. Stage 5 closeout и Stage 6 уже используют `CORRECTED_SINGLE_C1`. Исходные файлы и значения не исправлялись. Этот известный accounting вопрос отделён от STOP_GRID; PASS выше относится к принятому corrected Stage 6/TRAIL1 authority.

Никакая доходность с округлёнными стопами не рассчитана и не названа исходным OOS.

## MINIMAL_FIX_PROPOSAL — только проект

Минимальное согласование: новый **append-only execution amendment/profile**, привязанный к frozen Stage 7 ID и отдельному execution revision. Он разрешает только детерминированную price-grid projection и описывает её числовые расхождения. Frozen Stage 7, стратегия и исторический OOS остаются неизменными; без отдельного разрешения внедрение запрещено. Изменить stop и продолжить объявлять exact Stage 7 stop/R conformance PASS нельзя.

1. `DecisionCore.signal()` и все условия T3 сохраняются. Raw `SignalIntent`, raw entry/ATR/stop/R, signal/trade IDs сохраняются как research evidence.
2. В execution boundary до sizing проверить аутентифицированную спецификацию фактического FINAM symbol: конечные положительные step/tick/margin, RUB economics, lot/granularity, binding/status и согласованность текущей спецификации с профилем. Missing/invalid/mismatch — fail closed. Entry должен быть на сетке; его нельзя молча округлять или применять guessed tick.
3. Для LONG `S_exec = floor(S_raw / step) * step`, для SHORT `ceil(S_raw / step) * step`. Использовать Decimal/integer ticks, без float epsilon, ближайшего округления и округления внутрь. Проверить корректную сторону и положительную цену. Стоп уже на сетке не изменяется.
4. `R_exec_ref = abs(E_reference - S_exec)`. При entry на сетке `R_raw <= R_exec_ref < R_raw + step`. Рассчитать `loss_per_contract = R_exec_ref / step * tick_value`, затем `Q_r15 = floor_to_granularity(0.015 * realized_equity / loss_per_contract)`, `Q_margin = floor_to_granularity(available_cash / directional_initial_margin)`, `Q = min(Q_r15, Q_margin)`. Zero quantity — skip. Сохранить существующие FULL, локальное резервирование, exits-before-entries и nominal 6% guard. **Старое quantity до округления повторно не использовать.**
5. Execution position/TRAIL1 создаётся с executable initial stop и явно frozen executable initial R. Raw R хранится отдельно. Initial protective SL/TP устанавливается на `S_exec`, 100% текущей подтверждённой позиции; защита подтверждается до следующего management bar.
6. Сетка нужна также последующим TRAIL1 stops: **260/260 сохранённых trigger candidates off-grid**. После completed-bar candidate calculation проецировать execution stored candidate/current stop наружу по той же сетке до persistence/action; stop-before-current-bar-extreme и активация только на следующем событии сохраняются. LONG `max(previous_exec_stop, projected_candidate)`, SHORT `min(...)`; одинаковый executable stop не создаёт replacement revision. Activation candidate должен быть проецирован до будущего stop test. Добавить более тесную защиту до retirement старой; service/broker reconciliation сравнивают executable stop, raw value остаётся evidence.
7. До submission в durable intent записать raw и executable prices/R, economics fingerprint/revision, quantity и risk/margin calculation. Сохранить ключи, основанные на существующем signal/trade ID, reuse после restart, unresolved-intent block и persisted bar watermark. Не конвертировать активные/неразрешённые старые позиции автоматически и не переигрывать уже consumed исторические сигналы.

Затрагиваемые компоненты будущего изменения: новый execution projection helper/profile; `production_runtime.py` (entry projection, executable position state, stored TRAIL1 candidate/stop projection, durable payload); `risk.py` только при необходимости явной валидации абсолютных цен — strict ticks и floor остаются; `production_service.py` (spec/fill authority и executable reconciliation); protective-stop payload validation; versioned state serialization и offline regression tests. `strategy_core.signal`, T3 source/parameters, Stage 1–7 и старые результаты не требуют изменения. Это список будущих работ, **не выполненный patch**.

## RISKS / 1R / TRAIL1

Первоначальный стоп становится шире менее чем на один тик; потенциальный денежный loss при прежнем qty вырастет. Пересчёт qty доказывает nominal initial stop loss ≤1.5% equity и margin reservation ≤available cash при reference entry. Проверено математически на всех 422 lifecycle-входах; widening находится между 0.004006585851 и 0.999761308072 тика, max рассчитанный initial loss — 1 500 RUB при equity 100 000 RUB.

`Trail1State` сейчас выводит trigger из переданного initial stop. Подмена стопа меняет числовой +1R threshold. На полностью grid OHLC и том же entry trigger predicates совпадают: LONG исходный threshold `2E-S_raw` округляется вверх до `2E-floor_grid(S_raw)`, SHORT симметрично вниз. То же относится к stop-hit predicate на grid lows/highs. Все frozen OHLC проверены как grid-aligned; это ограниченное доказательство дискретной эквивалентности, **не exact numeric conformance и не доказательство неизменной доходности**. Между raw и executable threshold существует off-grid counterexample; fill price/step/spec changes нарушают предпосылки. Исходная stop fill abstraction и executable fill различаются; стоимость 1R, R accounting, диагностические flags и дальнейший реальный position stream могут измениться.

Поэтому amendment должен явно выбрать executable 1R для LIVE TRAIL1 и сохранить raw research 1R как отдельное поле. Если требуется строго trigger на raw 1R, нужен отдельный raw trigger reference и отличное execution-loss R; называть такой threshold «+1 executable R» нельзя. Это альтернативная semantics, которую нельзя молча принять. Рекомендация — единый executable 1R для sizing/protection/TRAIL1 с явным исполнительно числовым отклонением от freeze, без новых параметров/фильтров.

Округление не может гарантировать **фактический** total loss ≤1.5% при произвольном MARKET fill, гэпе, комиссиях и проскальзывании. Действующий transport использует MARKET, а `confirm_entry_position()` получает quantity и сохраняет reference close, не фактическую цену исполнения. `R_exec_actual = abs(E_fill-S_exec)` и cash risk должны быть проверены по аутентифицированному fill, frozen после входа. Утверждение о строгом pre-entry лимите фактического риска требует согласованной границы допустимой цены исполнения/потерь; без неё никакой простой grid fix этот пункт не доказывает. Минимальный проект сохраняет nominal R15 и margin, а fill/slippage guard является обязательным вопросом execution acceptance перед обещанием фактического R15. Это не основание менять исследовательские T3 условия.

## TEST_PLAN и выполненные проверки

Выполнено с запретом socket connections, без FINAM token и запуска production service:

- Существующие runtime, conformance, service, R15/margin, Stage 7, ledger и SQLite recovery проверки: **263 passed, 1 Windows-only skipped, 17 subtests passed**. Именованный off-grid тест прошёл.
- Два независимых frozen replay: **418/418 PASS** каждый; 0 расхождений.
- Все 2 918 funded-flat tick rejection checks — PASS, 0 order intents/orders, unchanged margin budget.
- 40 runtime сценариев: N4 × LONG/SHORT × integer tick, fractional tick, zero R15 quantity, margin cap, zero margin; quantity floor и initial cash risk ≤1.5% — PASS.
- 8 реальных causal-prefix runtime проверок и restart: тот же signal/stop, tick skip, после restart тот же bar не выдаёт новый signal — PASS.
- 32 mathematical outward projection cases, включая уже целый тик и границу чуть меньше следующего тика, 16 invalid authority checks и 82 LONG/SHORT grid-threshold checks — PASS.
- Mathematical outward sizing по 422 historical admitted entries — PASS; **production projection не установлена**.

Перед будущим внедрением достаточно следующего bounded regression/acceptance набора, без оптимизации и нового исследования:

1. На неизменном frozen источнике повторить exact raw signal/TRAIL1 authority; отдельно проверить executable projection и различия initial stop/R/fill. Не подменять raw expectations adjusted values.
2. N4 × LONG/SHORT: decimal grids, exact/on/off tick, near boundaries, invalid/NaN/missing economics, entry off-grid, wrong side/nonpositive stop, lot >1, zero quantity, directional margin, local batch budget, FULL/R15 и aggregate 6%.
3. Initial protective stop и TRAIL1 stored candidate/next-event activation/stop-before-extreme/tighten-only/duplicate rounded candidate; SL/TP absolute prices на сетке, защита before retirement, gap fill и actual fill/R authority.
4. Crash/restart на стадиях projection, intent persistence, send-uncertain, position confirmation и stop replacement; fingerprint/payload mismatch fail closed, revision/client ID reuse, no duplicate orders, no automatic replay of consumed signals.
5. Отдельная проверка согласованного execution amendment и риска при допустимом fill/slippage. Реальный broker acceptance возможен только после отдельной авторизации пользователя. Этот аудит не использует real order endpoint.

Почему тесты ранее не выявили масштаб: runtime/conformance fixtures вручную строят entry=100 и расстояние `step*5`; ATR sizing не связан с настоящей историей. Off-grid тест подтверждает чистый skip, не требует исторического signal pass rate. `production_replay.py` проходит core/manage без `size_position()`/`plan_entry()`/FINAM grid. `test_conformance_reports_two_exact_independent_replays` читает committed PASS JSON, не исполняет historical runtime sizing. Отдельные верные unit checks поэтому не закрыли integration boundary «raw исторический сигнал → sizing → entry/protection».

Дополнительный provenance дефект: нынешний `historical_conformance.authenticate()` нормализует CRLF через `canonical_authority_sha256`, хотя frozen market-data hashes записаны по raw CRLF blobs; вызов fail-closed сообщает четыре h1 mismatch. В диагностике все остальные authentication checks повторены и выполнена более строгая raw-byte проверка CSV == frozen Git blob == manifest hash. Исходная функция и файлы не менялись; независимый byte-exact replay PASS не следует путать с успешным запуском её `generate()`, который также пишет существующие артефакты и здесь не вызывался.

## Неизменность и остановка

`PRODUCTION_CHANGES=NONE`. Действующий LIVE host не подключался; trading credentials, Scheduled Task, authorization, SQLite production и kill switch не читались/не менялись. SQLite использована только в новых disposable diagnostic paths вне репозитория. Из этого аудита не было broker operations, merge, deploy, re-arm или runtime/strategy changes. Frozen Stage 7 и исходный OOS сохранены.

Финальные GitHub main/diff и source equality evidence приведены в `verification.json`. Ветка/PR содержат только новые audit-only файлы; все существующие tracked файлы сохранены. Независимое утверждение о неизменности сервера вследствие действий третьих лиц без доступа к серверу не делается.

**NEEDS FIX:** стратегическая сигнализация и accepted R-модель воспроизводятся, но grid boundary системно блокирует исследованные entry; initial-stop-only patch оставляет off-grid TRAIL1 и не доказывает actual-fill R15. Требуется отдельно согласованный execution amendment и узкая реализация перечисленных проверок. Работа остановлена на аудите и проекте; production fix ждёт отдельного разрешения пользователя.
