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
