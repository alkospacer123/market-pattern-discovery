# Stage 8 / PR #493 — operator SLTP multi-fill acceptance rehearsal

**Status (2026-10-13): OFFLINE_SIMULATION_PASS, PHYSICAL_FINAM_ACCEPTANCE_NOT_RUN, REAL_ORDER_AUTHORITY=NO.**
Only candidate files in **Draft PR #493**; never merge/deploy/rearm from this report.
The production Scheduled Task remains isolated/Disabled and kill switch HALTED after the operator's physical Intel #493 isolation. Frozen T3/H1/TRAIL1 N4 FULL/R15 strategy, accepted LIVE checkout `184e8c2b8fa092a606249ff293a4f507160bff29`, Stage5 data and risk are unchanged.

## Delivered order-incapable candidate

- `stage8_493_multifill_offline_acceptance.py` runs a strict **synthetic event replay** using a fresh, clearly named SQLite journal **only under the supplied scratch directory**. It has no FINAM client/network, DPAPI, LIVE state integration, Task calls or production order endpoints. `--execute` always fails `BLOCKED_NO_REAL_ORDER_TRANSPORT`.
- `tests/test_stage8_493_multifill_offline_acceptance.py`: **52 independent local pytest tests PASS** (including 28 parametrized malformed brokerage scenarios, restart/rollback and uncertain ACK). Local file bytes equal both GitHub Git blobs: replay script `b6a0e538c6e069e70cf5168cc884d3d7fc635859` and tests `2d8c16bc9ab2544387dcd4a2a74151513d3a82e4`. Native Intel and live broker not involved.
- Two full fresh synthetic replays byte-for-byte identical JSON output, SHA-256 `c09cf35325abf2c65e1c2bc112eae083e3df3a224d267185fa8f16c27c92ff39`. Source synthetic input SHA-256 `b9a21b95e7c615a828d1f27482b56b6c3af40ad82cd6a30ad43d03828aa8f229` in the isolated test workspace, not authentic FINAM evidence.

## Validated synthetic sequence

1. Persist one ENTRY intent for **exactly 2 total contracts** before a single synthetic entry POST/ACK identity. Observed nonzero exposure starts at **1**; instantaneous 2-contract fill does **not** prove separate partial growth.
2. Associate one synthetic order-linked fill (account, order ID, N4 symbol, direction, 1 contract and on-grid price) with the observed 1-contract position. Reject duplicate/conflicting/disappearing fills, price off-grid, invalid quantity/account/side/order.
3. Persist protective stop intent before one synthetic protective POST/ACK; require externally asserted **ACTIVE** `SLTP_QTY_MEASURE_PERCENT`, `quantity_sl=100`, correct N4 symbol, side and exact initial stop, `covered_current_quantity=1`. ACK alone is not coverage.
4. Accept **new** fill associated with the original entry and observed position rising from **1→2** only after active protection at 1. Demand a **fresh** synthetic broker stop observation with the *same protective order ID*, active 100% measure and `covered_current_quantity=2`.
5. End only after synthetic position is **0**, active orders **0**, entry and stop terminal, unresolved intents **0**; otherwise `INCOMPLETE` or fail closed.
6. Test uncertain entry/stop ACK, missing history, unverified fill price, conflicting journal replay, restart/crash before atomic event commit and forbidden duplicate submission. Any uncertain sequence yields operator intervention rather than retrying a broker POST.

Expected exact classification:
`OFFLINE_MULTIFILL_GROWTH_SIMULATION_PASS_NOT_REAL_AUTHORITY`.
Report fields explicitly mark `broker_percent_coverage_real=NOT_VERIFIED`, `real_account_fill_history=NOT_VERIFIED`, `broker_flat_physical=NOT_VERIFIED`, `real_order_endpoint_calls=0`, `live_production_ready=false`.

## Actual V2 gap: NEEDS FIX before physical growth test

**Important source-code observation:** `TradingSystemLab/stage8_robot/production_runtime.py` (candidate V2) creates initial protection on first observed partial quantity, but `_confirm_candidate_entry` currently treats subsequent quantity growth while `protective_stop_state == 'ACTIVE'` as a **HALT** (`POSITION_CHANGED_WHILE_ENTRY_UNRESOLVED`), and requires `protective_covered_quantity == current.quantity`. That is a correct conservative safety stop, **not proven 100% dynamic protection as quantity increases**. The offline acceptance model only states what a later broker trace must show; it is not a fix or a demonstration that present V2 can safely support the 1→2 event.

The existing `protective_stop_contract.py` synthetic 100%-current-position semantics are *not* physical FINAM behavior proof. `ACTUAL_FILL_AUTHORITY` remains blocked until durable AccountTrade history for the exact order/account/side/symbol/quantity can be proven across restart, with fresh current N4 instrument cash/tick and fees authority and operator-defined gap/slippage/loss bounds. OFFLINE synthetic fill prices are **never** promoted to real execution/risk evidence. Candidate `FINAM_FILL_AUTHORITY_VERIFIED=False` stays untouched.

## Next existing-roadmap acceptance gate (separate approval required)

- Independently review exact operator-only **physical** adapter behavior: durable intent before POST, at most one 2-contract entry, at most one initial SLTP, no blind retry after uncertain ACK, 1→2 position observation, 100% SLTP coverage at each quantity, stop/backstop and no double close, exact order-linked partial fills and irreversible flat state.
- First fix or explicitly reconcile the candidate growth HALT contract **in isolated candidate code**, not in the frozen LIVE service, and add restart/persistence and adversarial tests; no force-fill simulation accepted as real evidence. If the actual FINAM two-contract entry fills atomically with no observable 1-contract stage, classify `INCONCLUSIVE_FOR_MULTIFILL_GROWTH` rather than PASS.
- Require **new explicit operator permission for real order transmission**, exact selected N4 symbol/direction/current margin/realized equity/cost cap and a post-failure manual emergency recovery protocol. This current authorization is for **offline engineering only**.
- Preserve `Task Disabled`, `HALTED`, existing frozen 1-contract Stage8.11 acceptance, no changes to live SQLite/config/strategy, no PR merge/deploy.

**Next action:** review the V2 candidate partial-growth transition and safe stop-coverage reconciliation offline. Do not run this tool against a real account or treat synthetic PASS as go-live readiness.

## 2026-10-13 — Candidate-only partial-growth bridge (supersedes earlier V2 source blocker; PHYSICAL HOLD remains)

Following explicit permission to **continue candidate engineering/offline tests only**, the V2 candidate source was narrowly updated in `production_runtime.py` and `production_service.py` without changing the frozen strategy, defaults, running robot, production checkout or state. The earlier unconditional `HALT` upon growth *while local stop ACTIVE* is superseded **only when a fresh parsed broker SLTP observation is provided** from the same account/orders snapshot that observed the larger quantity.

The source enforces:
- Observed current-position direction and total quantity bound by the precommitted entry; **no quantity cap, R15 sizing, signal/strategy or broker adapter changes**.
- The exact *same* reconciled SLTP broker order ID, persisted stop intent, client order ID and comment, N4 FINAM symbol, exit side, on-grid stop price equal to current active stop, normalized ACTIVE order status and literal `SLTP_QTY_MEASURE_PERCENT` **100%**, GTC. Broker view/request fields must agree. A plain ACK or asserted `ACTIVE=True` boolean does not suffice.
- An atomic local 1→2 state transition updates covered count to observed current exposure and persists a separate `entry_growth_stop_observed:...` record explicitly marking `real_finam_dynamic_coverage_proven=false` (because real physical dynamic-stop behavior is not proven by a parsed GET response alone).
- If any evidence is missing, stale or mismatched, durable `execution_halt` and `entry_growth_hold:...` record the larger *broker-observed* quantity and reason, **without changing the old protected local quantity, submitting another SLTP, cancelling the backstop or automatically clearing the hold**. Once held, later observations cannot silently rearm/reconcile; a separate operator-controlled recovery decision is mandatory.
- Only the V2 branch accepts an `observed_protective_stop` input; the existing legacy/frozen branch rejects a non-null observation. The candidate service passes a parsed `BrokerOrderView` only from `active_sltp_for_trade` and refuses to proceed to fills after a hold.

A new adversarial, candidate-runtime integration pytest module `tests/test_stage8_493_partial_growth_candidate.py` exercises LONG/SHORT signed 1→2 growth, forged/mismatched broker IDs and request fields, fixed-quantity/terminal/not-active stop, missing proof, sticky hold on restart, exactly one existing stop intent, before-stop-ACK pending exposure and continued `FINAM_FILL_AUTHORITY_VERIFIED=False`. **The new full-repository pytest is not yet physically executed** (no repo worktree or authenticated FINAM runtime in the current offline container); do not call it PASS until a pinned isolated candidate checkout reports real test output. Earlier independent **52 PASS** refers solely to the *separate* synthetic event-journal rehearsal, not this runtime integration.

**Outstanding hard gate:** This code verifies a broker **order description** of 100%-current-position coverage, not whether FINAM actually changes stop coverage from one to two filled contracts before a stop trigger, nor whether an account and orders GET were atomic, nor a gap or market loss bound. The V2 fill authority, actual current N4 tick/margin/fee authority, and real-order/Task permissions are unchanged. `LIVE_PRODUCTION_READY=NO`, `REAL_ORDER_AUTHORIZED=NO`, operator isolation remains `HALTED / Task Disabled`.

**Next:** run pinned, isolated Python/pytest (no production data or secrets), independently audit the candidate runtime integration and negative fixtures, then resolve any regression only in Draft PR #493. After independent offline PASS, submit a distinct broker acceptance protocol for explicit monetary-loss and real-order approval; do **not** merge/deploy/rearm automatically.
