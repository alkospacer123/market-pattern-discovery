# FINAM fill price authority — PR #493 follow-up

**Current V2: offline candidate PASS / NOT DEPLOYED; physical acceptance BLOCKED.** Original investigation is retained below; the appended V2 section records current code and user-supplied Intel provenance.

**PROPOSED / NOT DEPLOYED. Source found in official schema; physical acceptance remains BLOCKED. LIVE_CHANGES=NONE. REAL_ORDER_ENDPOINT_CALLS=0.** This work adds one read-only diagnostic and offline tests; it does not enable the proposed execution profile or change FINAM production transport, strategy or state.

## Concrete finding

Official `FinamWeb/finam-trade-api@52c95c8672542c2f89fbee2a4016774e73a0caa4` (commit dated 2026-10-01) describes:

- [`GET /v1/accounts/{account_id}/trades`](https://github.com/FinamWeb/finam-trade-api/blob/52c95c8672542c2f89fbee2a4016774e73a0caa4/proto/grpc/tradeapi/v1/accounts/accounts_service.proto#L107) with `limit`, `interval.start_time`, `interval.end_time`; 400 is explicitly “Неверно передан интервал”. Start is inclusive, end exclusive. Swagger marks individual query fields optional; this does **not** prove that the server accepts the existing completely unbounded request.
- [`AccountTrade`](https://github.com/FinamWeb/finam-trade-api/blob/52c95c8672542c2f89fbee2a4016774e73a0caa4/proto/grpc/tradeapi/v1/trade.proto#L13): `trade_id`, `order_id`, `account_id`, `symbol`, `side`, `size`, `price` (“Цена исполнения”), timestamp and currency. This is the smallest documented source of price-of-this-order using the existing REST API.
- [`Position.average_price`](https://github.com/FinamWeb/finam-trade-api/blob/52c95c8672542c2f89fbee2a4016774e73a0caa4/proto/grpc/tradeapi/v1/accounts/accounts_service.proto#L268): explicitly **not populated for FORTS**. It cannot substitute for fills of N4 futures. `current_price` also is not execution price.
- `OrderState` provides identity, executed/remaining quantity and status, but no executed-price field. Request `limit_price`/`stop_price` are not MARKET fill prices. SubscribeTrades exposes the same trade type through a stream, but would add transport/reconnect requirements and supplies no proven restart history contract here; it is not introduced.

Exact schema extracts, source URLs and four file hashes are in `official_fill_contract.json`. They are documentary authority, not physical broker evidence.

Existing `finam_api.trades()` sends only `/trades`, omitting all interval/limit query parameters. `broker.fills()` reads `account.trades`, although GetAccount is not trade history authority. Both findings are confirmed in code. The omission is a plausible explanation of the historical 400, **not a confirmed explanation of the actual server error**: raw error bodies and Intel responses are unavailable in this environment. Production API/adapter code is not changed on this assumption.

## Attempts 2–7 and retained evidence

The current main, accepted provenance, recovery validators and attempt7 implementation were inspected. Original external Intel evidence/logs/ledger files are not mounted here; their bytes were not fabricated or independently rehashed in this follow-up.

| Attempt | Accepted external evidence SHA-256 | What the retained authority proves about price |
|---|---|---|
| 2 | `0954B5C3D62444BA9AE59519386B0FC454D85C987BE1BAC04B82CA6C671B15A0` | One ACK, +1 CNY position, no proven trade rows at immediate reconciliation; later manual close. No price. |
| 3 | `9206841E4C9E25F126AB6C7032326B4F0778F6CF65D44AF3DA3549D8E677AD65` | Recovery validator binds OIR with ACK/+1 position/zero proven fills; history-detail 404 later allowed by immutable evidence plus flat account. No price/retention proof. |
| 4 | `F0EADA84724509A197BE7F851B2530535DAA7B1A8EC062D8943CCB905C5BA2EF` | Recovery validator binds OIR, +1 position, zero proven fills and manual-close recovery. No price. |
| 5 | `E67127A4727C4B5505F52877A9AFDE29447551DF781E5420DD4F7695CAC92F85` | Same bounded ACK/position/OIR authority; no accepted price rows. |
| 6 | `8921A4A9FC1A44DD0407D405B32B54B03A87F6949AFBCC6DA446F1FDC58BDE3B` | OIR/+1 position and account-only manual-close recovery; no price. |
| 7 | `704BFCC19B1A63F490192C0D8D0E4715BFECF77664296AFEF47E5B80FBF64B5F` | Accepted position-authoritative entry/flatten PASS. `broker_fill_count=2` is calculated from entry/flatten boolean flags in `stage8_11_physical_acceptance.py`, not two authenticated `AccountTrade.price` rows. |

Historical PASS is not reclassified. `_reconcile_position()` changes intent status based on exact quantity; it does not persist trade price rows. Earlier order-detail expiry does not prove `/trades` expiry or retention. The accepted roadmap forbids restoring old synchronous order/trades convergence as normal quantity proof. A separately accepted **price evidence** contract must preserve position-authoritative exposure reconciliation.

## One minimal READONLY scenario for Intel

`finam_fill_price_readonly.py` uses the existing FinamAPI transport under a strict allowlist: POST session/authentication, GET account, GET **bounded** trades. It rejects **all orders URLs, including GET order/detail**, and every trading/cancel operation before transport. The scenario needs no new SDK, stream, token provisioning or production configuration.

Inputs:

1. A stable standalone **copy of an already existing historical Stage8.11 backup** outside RuntimeRoot and the diagnostic checkout, with its known SHA-256. It must include one ACK order ID for an entry from attempts 2–7. An attempt3–6 pre-recovery backup is sufficient; an attempt7 copy is optional. The scenario does not create a backup from the running database. Canonical LIVE database filenames and WAL/shm sidecars are rejected.
2. The exact historical entry intent key and a closed UTC interval covering that order's execution, taken from existing evidence/log timestamps. If the exact sub-interval is unavailable, use an explicitly bounded historical interval covering the known attempt, then inspect completeness. Do not guess a fill from an empty response.
3. The existing READONLY DPAPI credential, retrieved by the existing getter under its existing owner. No trading token, authorization or kill-switch change.
4. A reviewed isolated checkout of this Draft PR, existing Python venv, and a new `.json` output path in an existing audit directory outside RuntimeRoot/checkout.

The wrapper is `run-finam-fill-price-readonly.ps1`. It never calls task/process/kill-switch/state controls and never updates the production checkout. Example with operator-supplied existing paths/times (placeholders must be replaced by actual evidence):

```powershell
& 'C:\TSLAudit\candidate-checkout\TradingSystemLab\stage8_robot\diagnostics\run-finam-fill-price-readonly.ps1' `
  -RuntimeRoot '<existing LIVE runtime root; credentials read only>' `
  -ExpectedDiagnosticCommit '<reviewed 40-character PR head SHA>' `
  -LedgerCopy 'C:\TSLAudit\historical-ack-copy.sqlite3' `
  -LedgerSha256 '<known SHA-256 of that existing standalone copy>' `
  -IntentKey 'stage8.11.attempt6:CNYRUBF:entry' `
  -StartTime '<actual historical interval start RFC3339 UTC>' `
  -EndTime '<actual historical exclusive end RFC3339 UTC>' `
  -Output 'C:\TSLAudit\fill-observation-A.json' `
  -Python '<existing venv python.exe>'
```

Run the **same scenario in a new process** with output `fill-observation-B.json`, plus `-PreviousReport ...A.json -PreviousSha256 <reported hash>`, to observe whether the identical historical fill set is still available. No restart/stop of LIVE is needed. This observes retention across diagnostic process restart and elapsed time, not an indefinite server-retention guarantee.

The report verifies local copied ACK account/client/instrument/side/quantity, matches **only** its exact broker `order_id`, rejects identity/unit/grid errors, deduplicates identical `trade_id` rows, rejects conflicting duplicates/overfills, and reports partial/full/unknown coverage. Weighted price is stored as an **exact rational**, with a Decimal value labelled display-only; no rounded average is passed as authoritative runtime fill. Individual fills must be on the authenticated N4 grid. Current account quantity may be flat after historical exit and is never used as historical price proof.

No documented pagination token/ordering/retention guarantee was found. `row_count >= limit` or a nonempty unknown cursor fails closed: do not invent pagination or claim full history. Empty history, 400, 404, missing identity/currency, partial coverage, or changed fills remain blockers. Reports contain only selected facts/field names and hashed account/order/trade identity, never token/secret or full account payload. SQLite copy is opened `mode=ro&immutable=1`, checked byte-for-byte before/after, without sidecar creation.

**The scenario was prepared and tested offline, not run on Intel.** No actual FINAM response is claimed. A full matching diagnostic observation is evidence to review; it does not automatically enable fill authority, migration, production or ordinary trading.

## Candidate risk audit and separate proposed MARKET contract

| Requirement | Current evidence / limitation |
|---|---|
| Quantity from executable stop | PASS: existing candidate sizing and independent 1422-signal rational oracle remain valid. No raw quantity reuse. |
| Reference is not actual fill | PASS offline: separate fields; real fill remains null; no account average/current price fallback. |
| Actual R/cash calculation | PASS for supplied offline synthetic fill: `R_actual=abs(fill-S_exec)`; cash = R/step × tick_value × filled quantity. Real bridge/price authority not accepted. |
| Partial/unknown and no duplicate entry | Inhibition PASS: unexpected partial quantity leaves the intent unresolved and prevents another entry. Exact matching multi-fill accumulation is tested in the diagnostic only. |
| Preserve protection | Existing fully confirmed exposure with unknown price retains the precommitted backstop and blocks normal management/new entries. **New partial exposure before initial protection is not handled by candidate runtime:** it rejects non-final quantity before creating a stop. This must be fixed and independently accepted before enabling MARKET entry. No protective workaround is deployed. |
| TRAIL1/FULL/R15/N4/frozen T3 | Unchanged; existing offline suite remains control. Proposed profile remains closed and unselected. |

Consequently `STOP_TICK_GRID_CANDIDATE=NEEDS_FIX` for the **complete broker execution acceptance** requested here, while the stop-grid/sizing/TRAIL1 replay components retain offline PASS. This is a newly explicit partial-protection gap, not a failure of the grid rounding formula. No already-open LIVE position is changed by this work.

**Proposed separate execution accounting contract (NOT ACCEPTED / NOT IMPLEMENTED):** keep MARKET and the existing FULL/R15 reference-price 1.5% sizing plus 6% aggregate nominal budget; never promise a strict actual-loss ceiling. Record final matched fill set, exact weighted price, actual initial R/cash and reference budget separately. Partial/unknown exposure must receive verified 100%-of-current-position precommitted protection before normal management; unknown outcome must never resend entry. Freeze TRAIL1 actual entry/R only after complete price/quantity authority, preserving raw/reference evidence. If actual risk exceeds the reference budget or authority is missing/inconsistent, keep protection, block normal trading/new entries and require review; no automatic resize/compensating trade or new parameter is proposed. Gap stop fills, fees and slippage can further exceed initial nominal risk. Accepting this accounting distinction requires separate approval; it does not alter R15 or replace MARKET with LIMIT.

## Remaining acceptance

`FINAM_FILL_PRICE_SOURCE=FOUND_DOCUMENTED_TRADES_HISTORY`; `ORDER_IDENTITY_VERIFIED=BLOCKED`, `PARTIAL_FILL_RECONCILIATION=BLOCKED`, `RESTART_RETENTION=BLOCKED`, `ACTUAL_R15_RISK=BLOCKED`, `LIVE_PRODUCTION_READY=NO`.

Next: inspect the READONLY A/B reports against immutable ACK/physical evidence; prove correct interval request succeeds with real price/unit/identity/coverage. If history is unavailable or clipped, obtain FINAM's exact supported retrieval/retention contract rather than invent it. Real partial/restart price coverage remains unproven by one-contract attempts; existing historical multi-fill evidence is needed if available. Then prepare the narrow price handoff/durable fill retention and partial-protection fix in PR #493, with exact identity/idempotency tests, **before** any separate LIVE acceptance. The diagnostic/profile must not enable itself from observed success.

## Current V2 follow-up — 2026-10-12

The preceding sections record the investigation at PR head `3c45b5c777a5bcd823150c9aebd287d3a8e448f9`. Their “no bridge / partial protection missing” descriptions are historical. The **current candidate** adds the bounded GET price handoff and partial initial protection described in the [V2 amendment](../EXECUTION_AMENDMENT_STOP_TICK_GRID.md#v2-fill-handoff-and-partial-exposure-amendment--2026-10-12). The previous `offline_verification.json` is retained as historical evidence; current results are in [fill_handoff_offline_verification.json](fill_handoff_offline_verification.json).

Physical input supplied by the user: Intel READONLY A/B Attempt 6, CNYRUBF@RTSX LONG, GET trades HTTP 200 with correct interval, matching historical ACK account/order/symbol/side, price 12.748, quantity 1, step 0.001, AccountTrade currency XXX, reported identical two-process results and report hashes. Files `PRICE_AB_SUMMARY.json`, `price-observation-A.json`, `price-observation-B.json` are absent from this workspace. **No independent audit of their bytes or SHA-256 is claimed.** The reported one-contract observation does not prove growing-position SLTP coverage or multi-fill/indefinite history retention.

The unconditional `currency == RUB` filter was wrong for this supplied response shape. The shared validator now stores XXX as a separate feed label; RUB tick valuation comes exclusively from authenticated instrument economics. It rejects unknown monetary specifications/labels, performs no conversion, and never interprets XXX as RUB. A synthetic regression reproduces the stated response shape; that regression is not a copy of Intel evidence.

The production-state handoff strictly matches order/account/symbol/side/trade IDs/time/price/quantity/grid and non-clipped history; multiple fills deduplicate, conflicts roll back, and weighted means/risk remain exact rational values after restart. Production position quantity remains `/account` authority. A fill history read or failure cannot defer the initial partial stop. Missing history, unmatched quantity, incomplete history, price/risk conflict and unproved protection create sticky HALTED/OIR with preserved backstop and no repeated ENTRY.

| Check | Current offline candidate | Separate real FINAM acceptance |
|---|---|---|
| FINAM_FILL_PRICE_SOURCE | FOUND: bounded AccountTrade history; XXX preserved separately | User reports physical success; original A/B bytes/ACK hashes not independently verified |
| ORDER_IDENTITY_VERIFIED | PASS | BLOCKED: independent physical provenance audit |
| PARTIAL_FILL_RECONCILIATION | PASS: record/protect current quantity; inhibit unknown growth, no duplicates | BLOCKED: real multi-fill/races and whole-position percentage-stop growth coverage |
| RESTART_RETENTION | PASS: transactional production-state facts and exact recomputation | BLOCKED: bounded server history completeness/retention under real restart |
| ACTUAL_R15_RISK | PASS: exact actual initial stop-distance accounting, separate nominal reservation | BLOCKED: strict 1.5% actual-loss guarantee under arbitrary MARKET fill/gap/fees |
| STOP_TICK_GRID_CANDIDATE | PASS for applicable offline checks | No LIVE activation/production readiness claim |
| Frozen/OOS | UNCHANGED; both raw replays 418/418, all 1422 signals | Original OOS executability/returns are not reclassified |

Growth before initial protective submission uses a separately persisted fresh quantity with the same 100% payload/key. Growth after established coverage does not invent new broker semantics: it preserves the existing backstop, blocks management/new entries, and requires intervention. No extra replacement is created merely for quantity growth; a pending ordinary TRAIL1 POST is inhibited while halted. Flat exposure with an unresolved entry remainder cannot trigger backstop cancellation.

The proposed MARKET accounting distinction is implemented solely in the inactive candidate: quantity from executable reference stop, nominal FULL/R15 unchanged, exact actual fill risk retained separately, excess/uncertainty halts with protection. It still needs independent acceptance; a strict actual-risk ceiling cannot be asserted. Commission/currency conversion authority is not invented.

Current status: **OFFLINE_FIX_READY_FOR_REVIEW / STOP_TICK_GRID_CANDIDATE=PASS; LIVE_PRODUCTION_READY=NO.** Required physical items remain BLOCKED as listed above. Candidate revision V2 rejects V1/legacy state, remains opt-in and entry-closed, and supplies no migration/deploy/re-arm commands. No Intel connection or physical FINAM request was made in this work: `REAL_ORDER_ENDPOINT_CALLS=0`, `LIVE_CHANGES=NONE`; no merge/auto-merge/deploy/re-arm.

## Intel saved A/B + ACK provenance audit — 2026-10-13 (operator-run, no broker request)

**HISTORICAL_ONE_FILL_AB_ACK_ARTIFACTS_VERIFIED — PASS on Intel.** The operator ran the exact standalone JSON-only Python auditor `stage8-493-finam-ab-ack-offline-audit-v2.py` (locally inspected SHA-256 `c0183eb841c028f2b340d9c4ebd6382ebae7daaf583481b1134f5c7441d6c104`). The auditor contains no network or SQLite imports; it reads only previously saved, local files, verifies pinned hashes and enforces the ACK/account/order/intent/fill/price relationships. A first version of the auditor was blocked by `A_SCHEMA_MISMATCH` because it expected the newer `schema_id/history` shape instead of the actual `finam_fill_price_readonly_xxx_observation.v1` report. The revised V2 checks the original schema/fields; no report was changed to satisfy the checker.

Saved physical evidence, checksummed locally by the Intel auditor (not committed to Git):
- `price-observation-A.json` and `price-observation-B.json`: same pinned SHA-256 **`71be04598e77685e303495794e6e6b8eb3f4f1936b9ac82599f4b74a6424a186`**, **byte-identical**.
- `PRICE_AB_SUMMARY.json`: SHA-256 **`26953268d1d155b716bf04998cf923f551cde1b7f62e5f3777ed4e15eb59190e`**.
- `ACK_CHAIN_READONLY_REPORT.json`: SHA-256 **`282ccbcf2e8ff321de0ae643633bde9aa35698f2bcf5f843d4b5cb8f986eae64`**.
- Immutable historical ACK ledger **binding** (the ledger itself was not reopened by this audit): SHA-256 `68c703c1677dff7ae2f80d916df5032a6001609ae4c2e2ce862b3ab7f914c217`.

Intel V2 output: `report_a_b_original_sha256=pass`, `report_a_b_byte_identical=pass`, `summary_known_sha256=pass`, `ack_chain_known_sha256=pass`, `ack_account_order_intent_provenance=pass`, `historical_fill_set_and_ack_chain=pass`, classification **`historical_one_fill_ab_ack_artifacts_verified`**.

The retained, bounded `GET /trades` observation identified **one** matching CNYRUBF@RTSX LONG MARKET fill, 1 contract at **12.748** on the **0.001** price grid, historical Attempt 6 on **2026-10-06 14:08:33 UTC**. `AccountTrade.currency=XXX` is a feed label only; no conversion to RUB or money/tick valuation is inferred. The chain binds the historical order ACK, account hash, active specification, order hash, fill-set hash and A/B report hashes. The auditor's reported endpoint calls were zero; the live robot, its task/authorization and SQLite were not touched by this offline audit.

**Scope limitation:** This is an independently constructed *local verification program* executed by the operator against previously saved artifacts. The original A/B/ACK JSON bytes were not uploaded into this conversation or independently retrieved from Intel by the auditing agent. The user-provided program output supports the above physical-local PASS; it does not constitute direct remote rehash by the agent, proof of raw FINAM transport for a fresh session, unbounded history retention, or physical **multi-fill / growth / percentage SLTP** acceptance. Production release remains **BLOCKED**, `LIVE_PRODUCTION_READY=NO`.

**Next physical acceptance boundary (separate explicit authorization if an actual trade is needed):** validate position-linked protection for first partial fill, later increase, unknown ACK and rollback/restart on an isolated controlled acceptance path. Before any live cutover, acquire independently validated real FINAM evidence of exact fill quantity/price completeness and effective 100%-current-position SLTP coverage; no new real ENTRY, protective order, cancel, deployment, task change or re-arm is authorized by the A/B PASS.


## Physical percent-SLTP acceptance gate — operator-only, not authorized (2026-10-13)

**Evidence status:** Intel historical GET-only inventory for attempts 2–6 found five single-contract entry fills (12 history rows observed in the bounded read; five matching entries), repeatability across separate requests, but **no active protective SLTP and no observed growing position**. Subsequent local JSON-only A/B/ACK verification independently checks the pinned historical one-fill artifacts. These are useful order/price-history results, **not** physical multi-fill or protection-coverage evidence. Avoid rerunning the same flat historical query as if it could prove growth.

**Official API semantics:** `SLTP_QTY_MEASURE_PERCENT` interprets `quantity_sl` as a percentage **of the position at the moment the SLTP executes** (not a frozen lot quantity). The candidate constructs `quantity_sl.value=100`, `sl_qty_measure=SLTP_QTY_MEASURE_PERCENT`, precommitted on-grid `sl_price`, and `VALID_BEFORE_GOOD_TILL_CANCEL`. Production reconciliation validates the returned active SLTP percentage/price/validity. Source: FINAM `orders_service.proto` `SLTPOrder` fields `sl_qty_measure`, `quantity_sl` and `PlaceSLTPOrder`, and `protective_stop_contract.py`, `production_broker_state.py`, `production_service.py`. This documentary contract is **not** evidence that FINAM actually protects a growing live position throughout races/restart.

### Minimal separate physical acceptance — no automatic execution

1. **Authority gate (before any mutation):** obtain *new, explicit operator permission* naming the real-order experiment, instrument, maximum quantity, acceptable costs/loss, and exact stop/rollback procedure. Operator alone controls the test. Preserve the currently ARMED production bot until separately authorized quiescence. Any actual experiment requires controlled HALTED production/task isolation, verified broker flatness, zero active orders/unresolved intents, exact FINAM account/contract/tick/margin, available funds, binding to approved code and independent emergency flatten capability. No changes to Stage 7 strategy, LIVE configuration or original state/authorization are implicit. If any precondition is false, do not submit.
2. **First observed partial exposure:** an isolated, bounded MARKET acceptance request with quantity above one contract *may* yield partial fills, but **partial execution cannot be induced or guaranteed**. Do not change the frozen strategy to LIMIT, pyramid, repeat an entry, enlarge an order after its submission, or inject a fake fill. On a natural first partial fill, record immutable ACK/order, exact broker `/account` quantity, bounded `AccountTrade` rows/order identity and on-grid execution prices. Candidate must create/persist the precommitted initial stop before price-history completeness; only a verified, single initial protective submission with **100%-of-current-position** percentage payload and unique durable key may count as protection.
3. **Growth / races:** if more of *that same request* fills before initial SLTP submission, the fresh quantity must be persisted at the submission boundary, while the SLTP payload remains `quantity_sl=100` in percentage units. Verify broker ACK and subsequent GET order presence, stop direction/price/percentage/validity and source order linkage, together with fresh account position. If exposure grows *after* established coverage, existing candidate policy is sticky HALTED/OIR with backstop preserved and no new entry/ordinary TRAIL1 replacement; do not assert guaranteed live coverage without broker-observed outcomes. Restart cannot resubmit the same entry or silently cancel protection; absence/contradiction means FAIL_CLOSED/OPERATOR_INTERVENTION_REQUIRED.
4. **Recovery and closeout:** only the authorized operator handles protective-order errors and flat recovery. Record position, protected-stop status, remaining original entry, unique trade fills, active orders and unresolved local intents before/after restart and final closeout. PASS requires broker-confirmed **flat** account, zero active orders/unresolved intents, no unprotected exposure or duplicate submissions, retained authenticated fill-set after fresh process/restart, and a final HALTED state; do not silently rewind state after any real execution. Never treat an ACK alone as a filled or protected position.
5. **Classification:** FULL one-shot fill without partial/growth = **INCONCLUSIVE_FOR_MULTIFILL_GROWTH** (it can still check ordinary SLTP installation if physically observed). Natural partial but missing proof of whole-position protection or complete fill history = **BLOCKED/FAIL_CLOSED**. Only broker-backed partial→growth, active 100%-position SLTP and safe restart/flat closeout can qualify for **PHYSICAL_SLTP_GROWTH_PASS**. Historical detached simulation or documented percent semantics do not qualify. A single successful experiment does not guarantee protection against all latency, market gaps, price limits or broker outages.

**Hard boundary:** This document authorizes **no** entry/exit/SLTP/cancel endpoints, Task/process/kill-switch changes, deployment, merge or re-arm. The inactive V2 still has `FINAM_FILL_AUTHORITY_VERIFIED=False` and will not submit entries; do not toggle it simply to run this test. A separately reviewed, operator-only test implementation and explicit permission are required if physical acceptance is pursued. The currently running LIVE robot and frozen strategy must remain unaffected. `LIVE_PRODUCTION_READY=NO`.
