# STOP/TICK GRID execution amendment

**Current V2: PROPOSED / NOT DEPLOYED; offline candidate PASS, LIVE acceptance BLOCKED.** The V1 sections below are retained historical proposal/evidence; the appended V2 section defines the current candidate.

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
## V2 fill handoff and partial exposure amendment — 2026-10-12

**Current proposed revision: `STOP_TICK_GRID_V2_FILL_PROPOSED`; schema `stage8_12_production_runtime.stop_tick_grid.v2`. PROPOSED / NOT DEPLOYED. Offline candidate PASS; LIVE acceptance BLOCKED.** This section supersedes the V1 implementation limitations above, while preserving the original proposal and its evidence. It creates no new roadmap phase. Stage 7 ID, strategy identity, parameters, research signals/results and TRUE OOS remain unchanged.

### Distinct price and monetary authorities

The user reports physical Intel READONLY A/B for historical Stage 8.11 Attempt 6: bounded GET `/trades` HTTP 200, ACK order/account/instrument/side match, CNYRUBF@RTSX LONG, price 12.748, quantity 1, step 0.001, `AccountTrade.currency=XXX`; two processes reportedly returned equal results/report hashes. `PRICE_AB_SUMMARY.json`, `price-observation-A.json`, `price-observation-B.json` were **not available in this workspace**. Their bytes, reported SHA-256 values and account/order bindings have **not been independently audited here**. This is user-supplied physical provenance, not a fixture promoted to broker evidence.

`AccountTrade.price` is authority for the price of its exact order. `/account` remains authority for the current open contract quantity. Neither account average/current price nor reference entry substitutes for a fill. The parser accepts the documented RUB feed label and the physically reported XXX label, stores each label exactly and rejects missing/other labels. **XXX is not RUB. No currency conversion is performed.** Price differences are valued solely in instrument ticks using the separately authenticated N4 registry's price_step and RUB tick_value/MOEX reference, bound into the existing specification fingerprint. Unknown instrument monetary authority fails closed. Commission/accrued-interest currencies are not used to infer money or promise an all-in loss ceiling. Physical price-unit/tick economics for current N4, and fees if required, remain separate acceptance requirements.

Bounded history must match exact durable broker order ID, account, FINAM symbol, side, nonempty unique trade IDs, RFC3339 time (including nanoseconds), positive on-grid prices and positive integer contract quantities. The interval covers the durable pre-POST submission time through the snapshot observation, inclusive start/exclusive end; it cannot begin after submission, use a different observation end, regress observation time or accept pre-submission fills. Total matched quantity cannot exceed the committed ENTRY quantity. Identical fills deduplicate; changes to identity/price/quantity/time/currency conflict and roll back. History saturation (`rows >= limit`), unknown pagination cursor, missing previously retained fills or quantity/history mismatch block authority. No pagination or indefinite broker retention guarantee is invented.

### Durable atomic handoff

Before any candidate ENTRY POST, production state commits exact account binding, submission timestamp and SUBMITTED status together. Existing guards keep all candidate ENTRY POST unavailable in this work. SUBMITTED/UNCERTAIN/ACK never retry ENTRY; a uniquely matching broker order can reconcile its ACK ID, but cannot change an existing ID.

The existing **production** `fills` table retains real order/trade identity, frozen strategy signal/trade identity, quantity, exact Decimal execution price, nanosecond timestamp, account binding, feed currency label, separate RUB risk currency, specification fingerprint and execution revision. No historical Stage 8.11 ledger is adopted or modified. The account-scoped broker trade ID is the idempotency key; conflicting duplicates, including cross-order reuse, fail closed. SQL columns must agree with the canonical stored payload.

Fill insertions, complete bounded-history fingerprint, exact weighted mean, actual R/cash, position state and entry reconciliation share one SQLite transaction. A failure rolls back all facts/state, then commits a sticky HALTED/OIR fault. Weighted mean `sum(price_i * qty_i)/sum(qty_i)` is authoritative as an exact rational numerator/denominator, including repeating decimals. Serialized rational strings are exact; the diagnostic Decimal mean is display-only. Restart recomputes mean/risk from durable fills, checks identity/time/grid/history fingerprint and protective coverage, and rejects inconsistent state. Local durable retention is proven offline; availability/retention of broker history after a real restart remains a separate acceptance item.

Reference entry, raw stop/raw R and executable reference stop/R remain immutable research/planning evidence. `verified_fill_entry`, exact actual initial R and cash are separate. For matched open quantity Q:

```
R_actual = abs(weighted_fill_entry - precommitted_executable_stop)
initial_cash_actual = R_actual / authenticated_price_step * authenticated_tick_value_RUB * Q
```

Quantity is never recomputed/reused from the raw stop or silently resized after a fill. FULL/R15 remains 1.5% realized equity reference sizing with floor, directional margin/local reservation and 6% aggregate nominal initial budget. The full committed nominal risk/margin reservation remains conservative for a partial position until its lifecycle resolves. Actual fill accounting is distinct from that nominal budget.

Ordinary executable TRAIL1 uses the exact verified entry and corresponding actual executable initial R after complete price/position/completion authority. Fraction arithmetic handles a repeating weighted mean; outward projection returns exact Decimal grid stop prices. Raw research R stays separate. Frozen core event ordering, +1R trigger, next-event activation, stop-before-extremes, tighten-only, no retroactive exits, EXIT before ENTRY and duplicate projected-stop suppression remain unchanged.

### Partial exposure and protection uncertainty

Any broker-confirmed positive signed partial quantity within the committed request immediately creates the initial protective intent for that actual quantity at the **precommitted executable stop**, before requesting fill history. Lack of fill price does not postpone protection. The existing payload remains absolute grid stop + 100% `SLTP_QTY_MEASURE_PERCENT`, GTC. Its scope is not converted into an invented fixed-contract or MARKET-fill protection scheme.

If quantity grows before the initial protective POST, the candidate separately persists the latest snapshot quantity at the submission boundary and submits the same 100% stop under the same key. The immutable original protective intent and ENTRY quantity remain intact. Broker active SLTP proof, exact price/identity and the committed submission quantity establish the recorded coverage for that observation. ACK alone does not establish active protection.

If quantity subsequently grows beyond established coverage, the candidate records the current exposure, preserves the existing backstop and sets **HALTED / OPERATOR_INTERVENTION_REQUIRED**. It does **not** assert that an old percentage stop automatically expands, create duplicate percentage stops, cancel the backstop, resend ENTRY, resize the position or make a compensating trade. Whole-position dynamic coverage after growth is **BLOCKED for real FINAM** until independently proven. Shrinking/fluctuating exposure while ENTRY is open, inconsistent history, unknown protection, actual reference-budget excess or fill at/across the committed stop likewise inhibit ordinary management/new entries. Existing protection can still reconcile; unsubmitted ordinary TRAIL1 replacements are not posted while halted. A confirmed cancelled/expired partial remainder can resolve price/completion authority for the remaining matched position, without cancelling anything in this implementation.

Flat position while an ENTRY remainder is unresolved does not permit automatic backstop cancellation or normal lifecycle completion: the remainder can reopen exposure. Restart retains the same intent/submission/stop keys, continues protection reconciliation, never repeats unknown POSTs and never implicitly clears HALTED. Operator recovery/migration is not implemented or authorized by this amendment.

### Separate MARKET accounting contract and LIVE criteria

The candidate implements **proposed** accounting of reference nominal budget versus actual matched-fill initial stop distance. It does not guarantee `actual risk <= 1.5%` for arbitrary MARKET fill, a gap, stop execution slippage or fees. Budget excess is recorded and halts ordinary trading while retaining protection. This contract requires separate acceptance; it changes no R15 parameter and does not replace MARKET with LIMIT. Strict actual-loss ceiling remains BLOCKED under an unrestricted MARKET contract.

V2 rejects legacy, unidentified, V1 and mixed revision databases before adopting positions or unresolved intents. No silent migration, re-arm of old signals or rewrite of legacy positions is provided. The opt-in constructor and the existing closed candidate entry guard remain; CLI/LIVE defaults and deployment/authorization/kill-switch files are unchanged.

Offline PASS covers parser/identity/rational risk, full/partial/multi-fill, duplicate/conflict, missing/stale/clipped history, durable crash rollback/restart, partial initial protection, changing exposure with safe inhibition, grid/TRAIL1 and unchanged raw replay. It does **not** certify actual broker SLTP dynamic coverage, history completeness beyond the documented bounded response, broker retention, fee semantics or unbounded MARKET risk. Before any separately authorized LIVE acceptance: audit the A/B bytes/known hashes and ACK provenance; authenticate current N4 tick/price-unit/margin economics; establish real partial/multi-fill history and restart retention; prove percentage SLTP coverage/races/backstop behavior; independently accept state lifecycle and the proposed MARKET accounting distinction. No real orders are authorized here.

Reproducible V2 results/provenance: [fill handoff verification](diagnostics/fill_handoff_offline_verification.json), [appended replay results](tests/stop_tick_grid_evidence/fill_v2_results.json), [diagnostic follow-up](diagnostics/FINAM_FILL_PRICE_AUTHORITY.md). Original replay evidence remains unchanged.

## V2 pre-POST recovery correction — 2026-10-12

**PROPOSED / NOT DEPLOYED. `PRE_POST_RECOVERY_OFFLINE=PASS`; `OFFLINE_FIX_READY_FOR_REVIEW`; `LIVE_PRODUCTION_READY=NO`.** This corrects durable ENTRY recovery in the same candidate/roadmap phase. It changes no price, quantity, risk, strategy or protective-stop semantics; the V2 revision/schema and closed profile remain.

Independent review identified a real defect at candidate `69cf0b2122687d6462d512252e5b75bb828ee344`: a `LiveExecutionError` restored `INTENT_PERSISTED` but retained active `entry_submission`. A subsequent attempt with a new timestamp failed with `ENTRY_SUBMISSION_ALREADY_COMMITTED`; reuse of the old timestamp also needed a fail-closed status check. The new regression fails against that original code before the correction.

The existing transport now emits the narrow subtype `EntryPrePostRefused` only from its ENTRY preflight block, **before invoking `api.place_order`**. The endpoint call is outside that block. Even a marker raised from the endpoint is downgraded to an unclassified error; it cannot become no-POST proof. Generic errors without this explicit contract do not permit a retry, even when an offline observer happens to know that no simulated POST occurred. Authorization/session/gate checks and default profile selection remain unchanged.

For the exact matching SUBMITTED attempt, with no ACK/fill/open-position authority, an existing SQLite transaction atomically:

1. Appends the original account/revision/timestamp and explicit `ENTRY_POST_NOT_CALLED` outcome/reason to `entry_pre_post_refusals:<entry_key>`.
2. Releases only the active `entry_submission:<entry_key>` reference to JSON null.
3. Restores the same immutable intent/key to `INTENT_PERSISTED`.

The refused attempt evidence is retained. Repeated recovery of the same proof is a no-op. Repeated reconcile/restart at the same timestamp is also a no-op. A later attempt must pass the existing gates and use a strictly newer timestamp; stale proof cannot release its authority. Clock regression/reused time, conflicting authority or an existing broker ACK cannot silently reset state.

If POST may have occurred, timeout/unclassified endpoint error/invalid ACK retains the original active submission record, marks `UNCERTAIN` and HALTED/OIR, and prohibits automatic ENTRY retry. A crash after durable SUBMITTED but before durable refusal proof likewise keeps SUBMITTED/evidence and requires reconciliation. Recovery transaction failures roll back proof/release/status together and halt. The previous inconsistent `INTENT_PERSISTED + active submission` state is not guessed to be pre-POST: it is inhibited as uncertain with preserved evidence. Healthy existing V2 state is compatible; legacy/V1/mixed adoption and implicit migration/re-arm remain forbidden. No recovery subsystem, table or StateStore/schema change is added.

Protection/multi-fill/stop-grid/R15/TRAIL1 regressions remain controls. The three transport protection/emergency/cancel method bodies and six runtime position/fill/protection/management method bodies are identical to the original candidate; no backstop contract is changed. Test-only guard patches and a network-incapable API spy exercise the otherwise closed candidate path; they do not activate a deployed profile or prove physical FINAM acceptance.

Final connection-forbidden regression runner: **444 PASS, 1 Windows-only skipped, 17 subtests PASS** (426 previous cases plus 18 pre-POST cases). Both independent raw replays remain **418/418**, all **1,422** signals pass the projection/sizing oracle, and the original executable comparison CSV is byte-identical. Original replay evidence and frozen artifacts remain untouched. Current hashes/results and archived previous verification are recorded in [candidate verification](diagnostics/fill_handoff_offline_verification.json).

Physical fill provenance, broker history retention, growing-position percentage-SLTP coverage and unrestricted MARKET risk limitations remain BLOCKED as described above. This correction authorizes no real request, Intel/LIVE change, merge, deploy, re-arm or profile activation. Stop after the Draft PR and summary for independent audit.

## Append-only: isolated release preparation (2026-10-12)

Status remains **PROPOSED / NOT DEPLOYED**. The same PR now includes external immutable legacy-snapshot dry-run, exact causal state preservation, byte-exact ledger archive/rollback, and a manifest/exact-commit-bound V2 selection through the actual ProductionService CLI. The selection is isolated, HALTED, one-shot and GET-only; no authorization or execution transport exists in that path. Legacy remains default; `FINAM_FILL_AUTHORITY_VERIFIED=False` remains unchanged. No trading profile is activated.

The protocol, state inventory, readonly preview interface, fixed frozen-interval signal diagnosis and separate future operator boundary are specified in [RELEASE_PREPARATION_STOP_TICK_GRID_V2.md](RELEASE_PREPARATION_STOP_TICK_GRID_V2.md). Actual test counts, hashes, old-suite baseline failures and protected artifacts are recorded in `diagnostics/release_preparation_verification.json`. Original frozen replay and executable comparison evidence remain unchanged. Preparation PASS does not remove physical fill/percent-SLTP growth or production cutover acceptance blockers and does not imply `LIVE_PRODUCTION_READY=YES`.


## Roadmap 3.6 — FINAM percentage-SLTP contractual acceptance proposal (2026-10-15, DRAFT ONLY)

**SOURCE ONLY, NOT LIVE AUTHORIZATION.** The operator supplied a written response attributed to FINAM's specialized support department: when a 100%-of-position SLTP condition activates at its stop price, FINAM calculates the amount from the position then and creates an exchange order for that quantity. The department also points to `GetOrder(s)` for the `sl_qty_measure` and `quantity_sl` fields. The verbatim report is in operator correspondence, not an independently authenticated GitHub/FINAM evidence artifact. Separately, the official FINAM `orders_service.proto` defines `SLTP_QTY_MEASURE_PERCENT` as percentage of position "at execution", `triggered_order_id` as the created exchange order and `VALID_BEFORE_GOOD_TILL_CANCEL` as the standing duration: https://github.com/FinamWeb/finam-trade-api/blob/main/proto/grpc/tradeapi/v1/orders/orders_service.proto .

**Narrow runtime decision, subject to independent acceptance:** no automatic HALT solely for a detected increase in the position of the *same* unresolved ENTRY when the same account/orders snapshot proves the exact original ACTIVE SLTP (same broker order ID, persisted reconciled intent, instrument, side, 100% measure and quantity, GTC, unchanged on-grid stop, client/order identity) and position is within the already planned quantity. The existing recorded backstop remains; no repost, replace, stop-price or FULL/R15 strategy change. The durable cumulative original-submission-to-current-quantity evidence remains separately auditable through restart. The `real_finam_dynamic_coverage_proven=False` fact stays unchanged: contractual activation-quantity semantics are NOT physical stop triggering, successful exchange fill, indefinite history retention or protection against gaps, post-trigger partial executions, broker outages and clearing. Exact broker `AccountTrade` matching and actual risk acceptance remain independent gates.

**Fail closed** for absent/mismatched/terminal stop, changed ID/price/side/percent, invalid durable evidence, decreasing/reversing quantity, missing history or contradictory fills, nonzero unresolved/unknown intents, prior sticky operator hold, actual protective order after trigger not confirmed or ordinary loss of protection. Never clear an existing HALT automatically, never retry a potentially transmitted ENTRY, never manufacture a partial fill. Tests are synthetic and do not prove physical multi-fill/growth in FINAM. The observed operator CNYRUBF two-contract 0->2 and WATCHING stop remain the only already conducted two-contract trade and are not reclassified as a natural 1->2.

This candidate changes only the scoped V2 growth decision and its offline regressions. The frozen T3/H1/TRAIL1, Stage7 N4 FULL/R15, Stage5, research/results, real FINAM adapters, SQLite schema, Task/DPAPI and the production activation gate are unchanged. `FINAM_FILL_AUTHORITY_VERIFIED=False` continues to block V2 real ENTRY and startup. Separate code review, physical Intel offline tests, subsequent approval of release fill authority and a new V2 code/account-bound authorization would still be required; **NO-GO for live trading** until separately approved.
