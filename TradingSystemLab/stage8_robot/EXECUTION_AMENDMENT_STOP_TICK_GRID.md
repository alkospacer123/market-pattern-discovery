# STOP/TICK GRID execution amendment

**PROPOSED / NOT DEPLOYED. Итог: BLOCKED (ACTUAL_FILL_AUTHORITY). LIVE_PRODUCTION_READY=NO.**

Это append-only execution amendment `STOP_TICK_GRID_V1_PROPOSED`, а не изменение frozen Stage 7 или заявление о прежнем exact Stage 7 execution conformance. Разрешённая область — кандидатный код, offline tests/replay и Draft PR. Merge, deploy, re-arm и реальные заявки не разрешены.

Frozen specification: `PROD_STAGE7_46DB784378797C7FB04636892350AFF21006D71A31F2CED9D4B974EDA2DC36B8`.
Identity: `TRAIL1__N4_01__FULL__R15`, T3/H1 `T3-H1-4e73cdb77246`, N4 USDRUBF/CNYRUBF/GLDRUBF/IMOEXF.
Основание: принятый PR #492, main `5c78d15c5b05e881904b644e1b7aa3b67ee63821`. До разработки Python execution sources main побайтно совпали с указанным LIVE code SHA `184e8c2b8fa092a606249ff293a4f507160bff29`. Сервер для этого сравнения не подключался.

## Raw и executable semantics

`DecisionCore.signal`, параметры, индикаторы, context construction, frozen TRAIL1 core, signal ID и trade ID остаются прежними. Raw signal остаётся `Entry ± 2.5 × ATR14`. `raw_initial_stop` и `raw_initial_r` сохраняются ровно как frozen evidence, включая исходное представление чисел.

В явно выбранном proposed execution profile до sizing:

- LONG: `S_exec = floor(S_raw / price_step) × price_step`;
- SHORT: `S_exec = ceil(S_raw / price_step) × price_step`;
- on-grid stop численно не изменяется;
- reference entry проверяется на собственной абсолютной сетке, без молчаливого округления;
- положительные finite цены, правильная сторона initial stop, N4 binding, step/tick/lot и положительные directional margins обязательны; иначе fail closed.

Проекция использует integer ratios Decimal и точный integer coefficient/exponent product. Нет float/epsilon проверки сетки. Decimal arithmetic применяется к executable state и свечам в execution adapter. Frozen float core/raw replay остаётся отдельным неизменным контрольным путём.

`price_step`, tick value и lot должны совпадать с authenticated REAL_READONLY production registry. Margin передаётся существующей authority конкретной стороны. Durable fingerprint включает instrument authority и hash всей authenticated registry row; он не является доказательством исторической или будущей актуальности FINAM metadata. Перед LIVE требуется отдельная повторная проверка реальной спецификации.

`reference_entry = signal.entry`; `executable_initial_stop = S_exec`; `executable_initial_r = abs(reference_entry − S_exec)` сохраняется как **reference-price** execution 1R. Raw и executable 1R различаются; initial stop расширяется менее чем на один тик.

## FULL/R15 и margin

Старое raw quantity не используется. После проекции существующий строгий FULL/R15 sizing заново получает executable stop:

`stop_ticks = abs(reference_entry − S_exec) / price_step` (целое),
`loss_per_contract = stop_ticks × tick_value`,
`risk_cash = realized_equity × 0.015`,
`r15_quantity = floor(risk_cash / loss_per_contract / trade_lot_size) × trade_lot_size`,
`margin_quantity = floor(available_cash / directional_initial_margin / trade_lot_size) × trade_lot_size`,
`final_quantity = floor_to_lot(min(r15_quantity, margin_quantity))`.

FULL не делит риск на четыре. Ноль остаётся нулём. Нет pyramiding. Локальное резервирование `final_quantity × initial_margin` происходит после успешной записи intent. Aggregate проверяет сумму nominal risk budgets (`risk_cash` каждой открытой позиции) плюс новый budget против `0.06 × realized_equity`, как в прежнем контракте. Отдельная проверка подтверждает `reference_initial_loss_cash ≤ 0.015 × realized_equity`. Это nominal/reference bound, не гарантия фактического убытка.

## TRAIL1 и защитные заявки

Execution adapter вызывает прежний `DecisionCore.manage` и прежние события TRAIL1. Decimal state не меняет формулу candidate `favorable_extreme ± 3 × ATR`. Candidate проецируется тем же outward LONG/SHORT правилом до persistence/будущей activation; активируемая цена проецирована до stop test. Subsequent current stop также проецируется наружу и ограничивается tighten-only: LONG max(previous executable stop, projected stop), SHORT min(...).

Сохраняются stop-before-current-extremes, +1R trigger, запрет активации на trigger-свече, activation только на следующем событии, отсутствие retroactive exits и EXIT before ENTRY. При синтетически verified fill используется `actual_initial_r = abs(verified_fill_entry − S_exec)` и соответствующий executable trigger. Он согласован с фактическим entry и неизменным committed initial stop; reference execution R и raw R остаются отдельными evidence. Для reference-price offline fills это тот же `executable_initial_r`.

Разные raw candidates с одним projected stop не создают новую replacement revision. Initial и replacement payload проходят независимую absolute-grid проверку по registry. Сохраняется прежний 100%-of-current-position SL/TP contract: новая tighter protection добавляется при сохранённом старом backstop; retirement разрешён прежним transport только после подтверждённого flat. При stop divergence остаётся прежний emergency action; новой компенсирующей MARKET схемы нет.

## Fill authority — blocking item

Existing `FinamAPI` имеет account, orders, order detail и trades endpoints. Принятая schema authority описывает `/trades`: trade_id, order_id, account_id, symbol, side, size, price, timestamp. Но accepted real-account evidence фиксирует HTTP 400 этого endpoint, а действующий roadmap запрещает возвращать `/trades`/order-detail/executed-quantity как synchronous fill proof. Наличие поля `average_price` в синтетическом account fixture не доказывает authoritative цену данного entry (особенно при клиринге/частичных fills). Position quantity доказывает exposure, а не price. `broker.fills()` читает неаутентифицированное account.trades и не используется как price authority.

Поэтому **ACTUAL_FILL_AUTHORITY=BLOCKED**. Candidate service/transport запрещают новый ENTRY до POST; нет нового FINAM parser, guesses, endpoint calls или MARKET-fill workaround. Guard не включается environment flag. Proposed profile выбирается только явным constructor argument `execution_revision=EXECUTION_REVISION`; CLI/LIVE defaults не меняются. Legacy profile сохранён для исходных regression controls и не получает grid fix автоматически.

`verified_fill_entry` изначально null; `actual_initial_loss_cash` null, никогда не выдаётся за reference risk. Для order-incapable offline проверки runtime принимает только явный `OFFLINE_SYNTHETIC_VERIFIED` handoff; это **не аутентификация FINAM**. Weighted average fill может быть off-grid и не округляется. Actual initial R/cash пересчитывается по этому отдельному fill. Тест показывает actual nominal risk >1.5% при неблагоприятном fill, хотя reference sizing ≤1.5%. Gap/stop slippage, комиссии и произвольный MARKET fill также не ограничены R15 sizing.

Если уже возникшая exposure подтверждена количеством, прежний precommitted initial stop можно восстановить под тем же durable key; fill остаётся MISSING. Management, новые entry и автоматическое повышение неизвестного fill до verified блокируются. Backstop не отменяется; нет повторного entry или произвольной компенсирующей сделки. Fill за initial stop либо изменение fill authority требуют review. Late price authority не применяется молча к уже созданному management state. Это bounded fail-closed recovery, не доказательство безопасности нового LIVE MARKET entry.

До отдельной LIVE acceptance необходим принятый и физически проверенный источник цены именно этой заявки: account/symbol/side/order identity, полный quantity coverage, partial fills/weighted average, время доступности и restart retention, без догадок и чужих fills. Требуется также согласованный MARKET slippage/risk contract; произвольный MARKET fill не позволяет обещать actual risk ≤1.5%.

## Persistence и migration

Новый runtime schema `stage8_12_production_runtime.stop_tick_grid.v1` имеет отдельную database identity с revision при том же frozen specification ID. Legacy/unidentified/mixed revision state отвергается; legacy identity проверяется read-only до открытия writable StateStore. Автоматической migration старых позиций, unresolved intents или сигналов нет. Fresh candidate database в этой работе существует только в disposable offline paths.

До любой submission intent хранит signal/trade identity, raw/executable prices/R, reference/fill distinction, revision, full authority/fingerprint, заново рассчитанные ticks/loss/R15/margin/final quantity, margin reservation и H1 timestamp. Position/stop intents сохраняют те же authority/evidence и protective state/revision. Restart проверяет fingerprint, projection, sizing, absolute grids и entry authority; несовместимость fail closed.

SQLite transaction объединяет signal sequence + pending signal, entry intent + consumption/watermark, position + entry reconciliation + initial-stop intent, replacement intent + position + management watermark, stop reconciliation + position state и flat/equity update. Прерывание внутри этих переходов откатывает весь переход. Persisted/Submitted/Uncertain/ACK intents сохраняют прежние keys; uncertain POST не повторяется. Отсутствие позиции при ACK не принимается за fill. Старый pending signal не активируется автоматически. После persist и до reconciliation state либо полностью записан, либо полностью откатан.

Новая LIVE database/migration procedure требует отдельного одобрения, clean-account проверки и плана сохранения legacy authority. Текущий patch не предоставляет production migration/deploy/re-arm команд.

## Offline доказательства и границы OOS

В `tests/stop_tick_grid_evidence/` сохраняются results и отдельный executable comparison; исходные audit/frozen artifacts не переписываются. Два независимых raw replay обязаны воспроизвести 418/418 frozen completed TRAIL1 trades с нулевыми price/time/state/R mismatches. Frozen data worktree: `market-pattern-data@50f1fd2178c18b7ab3bd969be82ad01f47a34745`, побайтно проверенный по accepted manifest/Git blobs. Известный CRLF mismatch прежнего authenticate() явно остаётся в results; byte-exact verification строже и проходит, функция не исправляется этим amendment.

Candidate replay проверяет 1 422 accepted full-history signals через настоящий plan_entry и 422 frozen entry paths через amended runtime, включая restart. Equity 100000, cash 1000000, LONG margin 100/SHORT 120 и fill=reference **синтетические**, не historical broker authority. 418 completed/4 terminal-open paths; 10 763 management bars; 2 948 initial/replacement prices; 2 526 replacements; 0 отличий exit timestamps при этих предпосылках. Нет adjusted PnL, optimization, parameter selection или adjusted OOS результата. Сопоставление числовых execution stop/R/fill с research хранится отдельно; исходный OOS остаётся неизменным. Совпадение event timestamps на grid OHLC не означает exact numeric execution/OOS conformance.

Offline PASS требует отдельные RAW_RESEARCH_CONFORMANCE, EXECUTABLE_STOP_CONFORMANCE, R15_MARGIN_CONFORMANCE, PROTECTIVE_STOP/TRAIL1_PROTECTION_CONFORMANCE, RESTART_RECOVERY_CONFORMANCE и ACTUAL_FILL_AUTHORITY. Synthetic PASS остальных категорий не превращает последнюю в PASS и не даёт PRODUCTION_READY=YES.

Воспроизведение из корня репозитория (вывод и SQLite только в новых scratch paths):

```sh
python TradingSystemLab/stage8_robot/tests/run_stop_tick_grid_tests.py --basetemp /path/to/new/scratch/pytest
python TradingSystemLab/stage8_robot/tests/replay_stop_tick_grid.py --data-root /path/to/frozen/data/worktree --out /path/to/new/scratch/replay
```

Отдельная LIVE acceptance после явного разрешения должна проверить fill contract, authenticated current N4 specifications/margins, broker SL/TP acceptance and replacement/backstop races, partial/unknown outcomes, cold restart/reconciliation и state lifecycle. Эта работа заканчивается Draft PR и Summary.

## Fill authority follow-up (append-only; still PROPOSED)

The [READONLY investigation](diagnostics/FINAM_FILL_PRICE_AUTHORITY.md) pins the official FINAM REST contract: bounded `/trades` query parameters and order-linked `AccountTrade.price` exist; FORTS `average_price` is explicitly unpopulated. The current adapter omits the documented interval/limit parameters. Whether that explains the actual historical HTTP 400 remains physically unconfirmed. One diagnostic and offline tests are prepared, with no production bridge or profile activation.

The follow-up also makes a missing acceptance requirement explicit: unexpected partial entry quantity is inhibited/idempotent, but candidate runtime does not yet install protection for a newly arisen partial exposure. Thus the complete broker candidate is `NEEDS_FIX` until partial protection and actual price/retention authority are implemented and accepted; existing grid/replay PASS results remain separate. `ACTUAL_FILL_AUTHORITY=BLOCKED`, `LIVE_PRODUCTION_READY=NO`. Original Stage7 and OOS are unchanged.
