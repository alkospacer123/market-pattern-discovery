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

## Independent audit of retained actual Intel JSON bytes — 2026-10-13

**20 structural/hash cross-checks PASS, zero discrepancies** from the actual attached JSON files, now available in the analysis environment (not new broker calls). The sanitized independent result is committed as [independent_uploaded_finam_evidence_audit_20261013.json](independent_uploaded_finam_evidence_audit_20261013.json). This advances the former *operator-reported-only* A/B and history statements: the auditor directly rehashed the eight original mounted file byte streams and matched their cross-references. The raw reports themselves are **not committed to Git**, and no credentials/individual account data are published.

- Original price A and B files are byte-identical, each SHA-256 `71be04598e77685e303495794e6e6b8eb3f4f1936b9ac82599f4b74a6424a186`. The summary and ACK-chain exact SHA bindings match. The historical Attempt 6 matched order has one on-grid CNYRUBF fill, **12.748**, quantity **1**, feed currency label **XXX**. This does not create a RUB-conversion authority.
- Actual `HISTORY_SLTP_A.json` SHA `10ee8f17c69e7e6cd9378054ee7c165d13eace4028dd2e1fb2a65b94b914e425`, B SHA `67dece1b97530029f7d18a516000d5b097de43a67e15f94a3a3f58f546012aa9`; their summary SHA `2472d493d154e7adb5510ef0da62f6e7e8b2fc39c2499a37575d7f8a309834a5` correctly binds both. Distinct observed-at times explain that the complete JSON files differ; their five normalized entry fill sets match exactly. Attempts **2–6** each have one full-quantity authenticated historical fill. The returned un-clipped bounded history has **12** rows for 2026-10-01 to 2026-10-08, observed with separate FINAM sessions. This does not prove infinite retention or a restart of the actual LIVE runtime.
- Both `HISTORY_SLTP_A/B` snapshots showed **zero broker orders, no nonzero N4 positions and zero active candidate SLTP** when observed on 2026-10-12. Therefore **no physical percentage-SLTP growth or partial/multi-fill coverage** was observed. It would be incorrect to mark `PHYSICAL_SLTP_GROWTH_PASS`.
- The attached `N4_SPECS_READONLY_REPORT.json`, SHA `364438980ae29ab81bc226b6b2c171f87be2ee764ff94e68a799cc2f189ab49e`, records all four FINAM N4 tick grid, lot and positive directional margin observations as PASS. Its `moex_current_tick_value_reverified=false` and per-instrument `FROZEN_MOEX_REFERENCE_NOT_REVERIFIED` mean **current independent MOEX RUB tick monetary authority remains a separate blocker**. No replacement economic coefficient is guessed or written to the registry.

**Scope:** source files were read and rehashed locally for this independent audit; FINAM was **not** queried anew, LIVE was not accessed, and physical evidence dates do not imply broker flatness now. V2 is not deployed, no experiment has been authorized, and `LIVE_PRODUCTION_READY=NO`. The operator-only physical SLTP test remains blocked pending specific permission, controlled isolation and recovery. Do not bypass `FINAM_FILL_AUTHORITY_VERIFIED=False` or alter frozen strategy/risk parameters.

### Official MOEX public tick-price crosscheck, separate from Intel report (2026-10-13)

A fresh independent public-source lookup of the official MOEX perpetual contract pages confirms the N4 original registry values without editing that registry:

| Perpetual contract | Tick (quote units) | RUB per tick per contract | Lot | Official MOEX source |
|---|---:|---:|---:|---|
| USDRUBF | 0.01 | 10 | 1000 | https://www.moex.com/ru/derivatives/perpetual-futures/usdrubf |
| CNYRUBF | 0.001 | 1 | 1000 | https://www.moex.com/ru/derivatives/perpetual-futures/cnyrubf |
| GLDRUBF | 0.1 | 0.1 | 1 | https://www.moex.com/ru/derivatives/perpetual-futures/GLDRUBF |
| IMOEXF | 0.5 | 5 | 10 | https://www.moex.com/ru/derivatives/perpetual-futures/IMOEXF ; also https://www.moex.com/a8803 |

Source/observation scope is separately recorded in [moex_public_tick_crosscheck_20261013.json](moex_public_tick_crosscheck_20261013.json). This **closes the public-documentary N4 tick-value crosscheck**, not the physical trade-time broker risk/margin/fill/SLTP acceptance. The original Intel JSON's `moex_current_tick_value_reverified=false` remains exactly as emitted on October 12; the newer public check does not retroactively change it. Broker cash, instrument/tradability, GO and order safety must be rechecked afresh immediately before any separately authorized real experiment. No currency conversion from AccountTrade `XXX` or frozen specification/risk edit is inferred. `LIVE_PRODUCTION_READY=NO`.

## Controlled physical acceptance readiness, operator permission and hold point (2026-10-13)

The operator authorized **continuing work on the controlled SLTP physical-acceptance task**. This is **not** treated as permission to change an already ARMED/RUNNING production task, disable a real safety gate, force a two-contract position without verified risk capacity, or re-arm any code. Existing LIVE was last observed **ARMED / RUNNING / HEALTHY** on 2026-10-12 and is not known to be isolated or flat now.

A single script was added, [run-stage8-493-sltp-local-readonly-precheck.ps1](run-stage8-493-sltp-local-readonly-precheck.ps1), plus a static no-mutation test. It is **LOCAL / READONLY ONLY**: inspect the exact scheduled-task names, persisted kill switch and the *last* production heartbeat; expose sanitized statuses, do not read production SQLite, authenticate to FINAM, load a DPAPI credential, execute order endpoints, stop/enable tasks, modify state, halt or re-arm. If Task is running or switch ARMED, report `BLOCKED_LIVE_PRODUCTION_NOT_ISOLATED`, never call that ready. Even with a disabled Task and HALTED switch, a prior heartbeat **is not** fresh proof of FINAM flat positions, active orders, margin, account ownership, or runtime process/lock exclusivity.

For a future physical test, the *proposed* maximum is **one candidate entry order with quantity no greater than 2** in frozen N4 membership, **only if** independently current R15/margin nominal risk and an explicit monetary loss/cost limit permit it. Do not choose instrument or direction for performance and do not manufacture a partial fill (no forced order slicing, layering or repeated entries). A single full 2-contract fill is **INCONCLUSIVE for multi-fill**, not PASS; do not repeat merely to obtain partial fill. A controlled test also needs an approved exit/recovery plan for possible 1–2 contracts, strict pre/post broker/account/stop/order/intent observation, unique ledger keys and a safe HALTED final outcome. The existing Stage 8.11 acceptance code has `MAX_ACCEPTANCE_QUANTITY=1`; it **must not** be repurposed by simply changing its constant, nor should proposed V2's `FINAM_FILL_AUTHORITY_VERIFIED=False` be toggled to make the test run.

**Current hold point:** no actual trading-test harness, real brokerage order, stop order, cancel, LIVE task/service/SQLite/authorization change or re-arm is executed or approved by this READONLY preflight. Fresh operator-controlled broker safety evidence and explicit risk/quantity/recovery limits must be reviewed before a separately audited real-order launcher may be used. SLTP physical growth protection remains BLOCKED; `LIVE_PRODUCTION_READY=NO`.

## Actual Intel SLTP local preflight — 2026-10-13 (operator output, no LIVE changes)

The operator executed `run-stage8-493-sltp-local-readonly-precheck.ps1` on Intel. The report is a **local Task/kill-switch/heartbeat observation, not a fresh FINAM GET or brokerage flatness proof**:

| Observed field | Actual output |
|---|---|
| Production Task | `Running` |
| Readonly Task | `Disabled` |
| Kill switch | `ARMED` |
| Heartbeat health / reconciliation | `HEALTHY` / `PASS` |
| Production cycle count | `11247` |
| Local positions / unresolved intents / active protective stops | `0 / 0 / 0` |
| Heartbeat fresh | `True` |
| Classification | **`BLOCKED_LIVE_PRODUCTION_NOT_ISOLATED`** |
| Fresh FINAM position/order/margin authority | **`NOT_COLLECTED`** |
| Real partial-fill and percent-SLTP test | **`NOT_RUN`** |
| Local changes | **NONE** |

This is the **correct safety result**: an active ARMED/Running production robot cannot be used as an isolated physical-acceptance harness. The original Stage8.11 physical acceptance adapter has immutable `MAX_ACCEPTANCE_QUANTITY=1` and does not demonstrate a partial/growing position; it must not be repurposed by editing the constant. The inactive V2 candidate still enforces `FINAM_FILL_AUTHORITY_VERIFIED=False` and therefore rejects new ENTRY before transport. An operator-only bounded two-contract launcher has **not** yet been independently implemented/reviewed/tested.

**Next order of work:** design and independently verify an isolated, exact-commit-bound operator-only SLTP experiment with one request, explicit maximum 2 contracts only if *fresh* R15/margin/account and operator monetary risk/expense limit permit, durable intent-before-POST, allowed session, 100%-current-position protective stop, strict one-shot POST/idempotency, exact matched AccountTrade evidence, fail-closed uncertain outcomes, operator-controlled flatten and final flat/HALTED plus no active stops/intents. No forced multi-fill or claim that 2 contracts guarantee partial fills. First test the harness offline without network or secrets. **Only after that** request a narrow fresh authorization for a controlled production HALTED/task isolation window. Do not halt the healthy ARMED bot merely to discover the test path is incomplete. No LIVE Task/SQLite/credentials/kill switch/order endpoint or Stage7 strategy/risk modification is implied by this report.

`PHYSICAL_SLTP_GROWTH=BLOCKED`; `LIVE_PRODUCTION_READY=NO`; PR #493 remains Draft.


## Intel controlled HALT verified — operator physical READONLY report (2026-10-13 11:00:55 MSK)

Operator supplied the full output from `check-tradingsystemlab-live.ps1`, which now expects the correct pinned production commit `184e8c2b8fa092a606249ff293a4f507160bff29`. Physical local state after the explicitly operator-initiated halt:

- **Kill switch `HALTED`, generation 61**, `updated=2026-10-13T08:00:20.700118+00:00`. Historical health-check field `KILL_SWITCH_ARMED=FAIL` means deliberately no longer ARMED, **not** a malfunction.
- Production Scheduled Task **Running**, Readonly Task **Disabled**; exact task/runtime/code binding, checkout clean, Stage5 `50f1fd2178c18b7ab3bd969be82ad01f47a34745` clean — reported PASS.
- Durable authorization remains `AUTHORIZED`, `execution_authorized=True` for the same pinned LIVE commit; only the kill switch gates off new entries. No authorization replacement, re-arm, Task stop, SQL edit or test order was performed.
- New production heartbeat at `2026-10-13T08:00:28.686890+00:00`, cycle **11282**, `HEALTHY`, reconciliation `PASS`, unresolved intents `0`, open positions `0`, active protective stops `0`. Fresh API contact age **28.4 s** reported by the physical check. These **local heartbeat** values are not a fresh independent FINAM `/accounts` and `/orders` account-flat proof.
- Exact current operational classification: **`HALTED / RUNNING / HEALTHY / PASS` with ENTRY disabled**. The separate V2 physical SLTP/growth acceptance is **NOT RUN**. Do not conflate the status with former ARMED snapshot in `CURRENT_STATE.md`; that historical snapshot is superseded by the operator's above physical report.

**Next**: independently authenticate via the existing DPAPI **READONLY** principal; perform two strict GET-only FINAM `/account` and `/orders` observations, matching the hash to the production heartbeat with still-HALTED gates. A local one-shot synthetic-tested script pair `stage8-493-finam-broker-flat-readonly.ps1` and `.py` is prepared for the operator outside Git (PS SHA-256 `8a5d6110f97c1aa5e390fdc048acf447a0ab1e6fbe852410cd8bc993899017c5`; Python SHA-256 `02dc0b6ada60ce51bfdc9afbb4d54ca3407d0a3cdd94c3ad88e6eb7a78ab8bbe`). Offline synthetic tests: **4 PASS**. Actual Intel FINAM GET outcome is not yet observed. A GET-only PASS does **not** itself authorize disabling/stopping the production task, mutating LIVE or posting a test order; isolation and a separately safety-reviewed, bounded SLTP operator acceptance harness remain pending. No forced trade, no change of frozen T3/H1/TRAIL1/N4/R15. `LIVE_PRODUCTION_READY=NO` for V2.

## Intel FINAM fresh double-broker READONLY flatness gate — 2026-10-13

**Preparation only, physical run pending.** The operator's previous local check showed `HALTED` generation **61**, production Task **Running**, frozen exact checkout `184e8c2b8fa092a606249ff293a4f507160bff29`, heartbeat **HEALTHY / PASS** cycle **11282**, local positions/intents/stops **0/0/0**. This is not yet a fresh independent FINAM flatness observation.

Two independently offline-tested sources are committed only on this inactive Draft PR branch:
- [stage8-493-finam-broker-flat-readonly.py](stage8-493-finam-broker-flat-readonly.py) (SHA-256 `02dc0b6ada60ce51bfdc9afbb4d54ca3407d0a3cdd94c3ad88e6eb7a78ab8bbe`) strictly authenticates existing `REAL_READONLY` token against the exact account, checks local HALTED/healthy/fresh/commit/account hash, then does *two* FINAM `GET /account` and `GET /orders` polls, requiring **zero nonzero positions and zero active orders across the entire account**. HTTP allowlist permits only session authentication and those exact account GETs; no order POST/cancel/other paths. Produces sanitized stdout; does not save account responses or touch production SQLite.
- [stage8-493-finam-broker-flat-readonly.ps1](stage8-493-finam-broker-flat-readonly.ps1) (SHA-256 `8a5d6110f97c1aa5e390fdc048acf447a0ab1e6fbe852410cd8bc993899017c5`) binds the Python SHA and the existing immutable LIVE checkout, requires a clean exact Task/commit/runtime binding, the Task still Running and kill switch HALTED, obtains the existing READONLY CurrentUser DPAPI credential only, runs Python with bytecode writing disabled, and clears credentials.
- [test_stage8_493_broker_readonly.py](../tests/test_stage8_493_broker_readonly.py) **6 PASS** locally: account/token/kill-switch/heartbeat/identity validation, two broker snapshots, positive-position/active-order fail-closed behavior, prohibited endpoint/method rejection, wrapper no-mutation contract. Exact GitHub blobs match the locally tested files.

**Interpretation:** `FRESH_FINAM_READONLY_FLAT_PASS_NOT_ISOLATED` means a fresh temporary **observation**, not continued flatness, physical SLTP acceptance, authority to stop the production Task, or authority to transmit any order. If Intel output says `BLOCKED`, do not stop/disable Task, do not rearm or submit. After success, the separate operator-only isolation step must independently verify process/Task/SQLite ownership and another *fresh* broker-flat check immediately around stopping. No V2 deployment, code/configuration change, or physical test submission has occurred; `LIVE_PRODUCTION_READY=NO`.

## Physical Intel fresh FINAM double-READONLY broker-flat acceptance — 2026-10-13 (operator log)

**`FRESH_FINAM_READONLY_FLAT_PASS_NOT_ISOLATED` / `FINAL_READONLY_BROKER_GATE=PASS`.** The operator ran the pinned, committed `stage8-493-finam-broker-flat-readonly.ps1` with existing readonly Python on Intel; the wrapper and Python emitted the following structured observations:

- `FINAM_SESSION=EXACT_READONLY_ACCOUNT_BOUND`; `ACCOUNT_IDENTITY_SHA_MATCH=PASS`.
- **Snapshot 1:** nonzero positions `0`, active orders `0`, orders scanned `0`.
- **Snapshot 2:** nonzero positions `0`, active orders `0`, orders scanned `0`.
- `FRESH_FINAM_TWO_READONLY_SNAPSHOTS=PASS`; `BROKER_FLAT_AND_ZERO_ACTIVE_ORDERS=PASS`.
- `ORDER_ENDPOINT_CALLS=0`; `NO_TASK_SWITCH_SQLITE_MUTATION=YES`.
- `LOCAL_PRODUCTION_TASK_STILL_RUNNING=YES`; `STOP_TASK_AUTHORIZED_BY_THIS_PROBE=NO`.

The two independent broker reads were collected with the readonly credential under `HALTED` and an exact production account/commit/heartbeat binding. This closes the **fresh broker-flat snapshot read gate at its observation time**; it is not a guarantee of continuing flatness and does not independently prove zero local unresolved intents at any later time. The production Task remains **Running**; LIVE is **HALTED / RUNNING**, not fully isolated.

**Next operator boundary:** separately review and explicitly authorize production Task isolation only after an immediately refreshed whole-account broker-flat and active-order GET; independently recheck process/task ownership, durable unresolved-intent/SQLite integrity, task restart configuration, kill-switch HALTED and emergency recovery/restore. Do **not** merely call `Stop-ScheduledTask` from this evidence: the Scheduled Task may automatically restart a stopped process, and an exposed position must never be left without supervision. The V2 operator-only 1–2 contract SLTP physical acceptance launcher and its fail-closed offline tests remain unfinished; physical real-order SLTP testing is still **NOT RUN**. No new ENTRY/SLTP/flatten/cancel endpoint is permitted by this read-only PASS. Freeze T3/H1/TRAIL1/N4/R15 unchanged, `LIVE_PRODUCTION_READY=NO` for candidate V2.

This result is sourced from the operator-supplied console transcript; independently accessing the Intel broker account from GitHub is not claimed. Raw account IDs, tokens and response bodies were neither printed nor committed.

## 2026-10-13 — operator PRE-isolation READONLY gate and offline SLTP planning launcher

After the operator-reported `FRESH_FINAM_TWO_READONLY_SNAPSHOTS=PASS`, production remains **HALTED / Task Running / not isolated**. The earlier fresh broker observations were temporary. **No Task or process has been stopped** and this append is not a subsequent Intel physical check.

Six candidate-only files added to Draft PR #493:

- `diagnostics/stage8_493_isolation_sqlite_readonly.py`: explicitly read-only SQLite `mode=ro` + `pragma query_only=on`, checks schema/integrity, frozen production identity, absent-or-empty positions, terminal-only intents and no pending signals. Rejects suspicious symlink/reparse/junction paths, requires pre-existing WAL/SHM readiness. Never creates, writes, or migrates production state.
- `diagnostics/stage8-493-pre-isolation-readonly.ps1`: exact pinned live checkout/task binding, Windows production service process candidate, restart policy reporting, readonly SQLite before/after, *new* FINAM two-snapshot readonly probe, unchanged Running Task/HALTED switch checks. It cannot stop/disable Tasks, re-arm, trade, change SQLite, or certify process ownership conclusively; final classification is **operator review required**, never stop authorization.
- `diagnostics/stage8_493_sltp_operator_launcher.py`: separate **OFFLINE / NO LIVE TRANSPORT** two-contract SLTP plan validator. Checks N4 identity, tick grid, LONG/SHORT stop direction, nominal FULL/R15 1.5% per-new-position cap, provided margin/cash, explicit operator cash-cost/loss ceiling, and asserted HALTED/isolation/flat/permission gates. These are operator-provided plan values, **not authenticated fresh FINAM margin, fill, position or risk evidence**. `--execute` refuses. This is a tested planning foundation **not** an executable physical acceptance launcher.
- `tests/test_stage8_493_isolation_sqlite_readonly.py`, `tests/test_stage8_493_pre_isolation_ps.py`, `tests/test_stage8_493_sltp_operator_launcher.py`.

Independent local synthetic pytest suite: **31 PASS** (10 readonly-isolation + 21 offline-launcher). Original local tested file bytes were independently matched to all six committed Git blob IDs. There was **no native Intel/Windows integration test**, no fresh FINAM query from GitHub, no main merge, no deploy, no Task mutation, no SQLite write, no real order. Native Task ownership/auto-restart behavior must be separately confirmed, and the Python process finder must fail closed if the actual deployed command line differs.

Next physical gate: operator transfers the *reviewed exact scripts* to the same Intel diagnostics directory, with existing broker readonly script and pinned Python executable. Run the nonmutating pre-isolation wrapper, inspect complete stdout (including the production process candidate count and task restart policy), and if **any** blocker occurs, make no Task change. Even a wrapper PASS does not authorize stop: next, explicitly approve a bounded isolation procedure with process ownership/auto-restart controls, a fresh broker read immediately around the action, production ledger and lock quiescence proof, safety/recovery and restoration plan. **No direct stop command is included or approved at this stage.**

Only after physical isolation PASS, separately develop and independently test the **real operator-only**, durable intent-before-POST one-request at-most-two-contract, AccountTrade-matched 100%-current-position SLTP protection, uncertain-ACK resolution and broker-flat emergency recovery harness; obtain *new explicit monetary risk/cost and trade authorization* before any real experiment. Existing Stage8.11 `MAX_ACCEPTANCE_QUANTITY=1` and V2 `FINAM_FILL_AUTHORITY_VERIFIED=False` **remain untouched**. Natural partial fill cannot be forced; a single immediate two-contract fill is `INCONCLUSIVE_FOR_MULTIFILL_GROWTH`. Candidate `LIVE_PRODUCTION_READY=NO`.

## 2026-10-13 — PRE-isolation PowerShell parser blocked; candidate-only correction

Operator supplied exact PowerShell SHA256 `e7cf2d794d1bd59568992935c6fe3ac11c5effb27f4310902241138d47a039b0` and Python SHA256 `0f102987ca04a56abd62f6f3fe54e8cb3266ccfbe3c3852ccb9c7cb47d28f51b`. The first Windows PowerShell 5.1 invocation stopped at parser error `UnrecognizedToken` on unquoted `git rev-parse @`; **none of the Python / FINAM / SQLite gates executed and Task isolation did not occur**. No trading/Task/SQLite mutation was performed by the unparsed command.

The candidate-only PowerShell wrapper now quotes Git's `@` revision (`git rev-parse '@'`) and sets/restores a process-local Python bytecode-disable environment variable. Offline synthetic/static regression suite (31 tests) PASS; native PowerShell 5.1 rerun and physical broker/state proof **PENDING**. Updated PS SHA256 `183830e1c7a511dedc9f9cc4419edcb049f5da1c4679db884ecf859ed5035087`, companion Python SHA unchanged. The corrected sources remain only on Draft PR #493; production checkout remains pinned to `184e8c2b8fa092a606249ff293a4f507160bff29` per last Intel evidence. No merge, deployment, re-arm, stop, or order authorization. `LIVE_PRODUCTION_READY=NO`.

## 2026-10-13 — Intel read-only pre-isolation process ambiguity, no action

Physical Intel run of the exact corrected candidate PowerShell wrapper (SHA256 `183830e1c7a511dedc9f9cc4419edcb049f5da1c4679db884ecf859ed5035087`) passed source-hash/operator invocation and reached the process check. It reported `PRODUCTION_SERVICE_PROCESS_CANDIDATES=2`, `TASK_RESTART_COUNT=10`, `TASK_START_WHEN_AVAILABLE=False`, `TASK_MULTIPLE_INSTANCES=IgnoreNew`, `TASK_ENABLED_TRIGGER_COUNT=1`, then **`CLASSIFICATION=BLOCKED:PRODUCTION_PROCESS_NOT_UNIQUELY_IDENTIFIED`**. This is correct fail-closed behavior; the script exited *before* new SQLite or broker checks. `restartcount=10` is the Task's **configured restart ceiling**, **not** evidence of ten real restarts.

Two matching Python PIDs do **not** establish two running robots: a parent/child interpreter chain is possible, but separate service instances are also possible. Never guess, forcibly kill a PID, relax the process uniqueness gate, stop/disable/restart the Scheduled Task or re-arm. The independent read-only `stage8-493-process-lineage-readonly.ps1` was added to report PID/PPID, parent/ancestor names, whether one candidate is the other's parent, safe command identity booleans, and task restart policy without emitting raw process command lines, credentials, account IDs, touching SQLite, loading FINAM or modifying any Task/process. Three static no-mutation tests PASS on its exact Git blob; **native Windows PowerShell 5.1 execution remains pending**.

This diagnostic cannot certify exclusive Scheduled Task ownership or safe Task shutdown. Even if the candidate PIDs form one tree, an operator-controlled isolation procedure must separately establish process identity/ancestry and lock ownership, fresh broker/account/order and production SQLite clean state, Task automatic restart handling, and emergency restoration. No physical isolation, FINAM query, real order, merge, deploy, or production changes occurred in this task. V2 `FINAM_FILL_AUTHORITY_VERIFIED=False` remains unchanged and `LIVE_PRODUCTION_READY=NO`.

## 2026-10-13 — Intel process lineage physically observed; guarded pre-isolation diagnostic revised

The operator physically executed `stage8-493-process-lineage-readonly.ps1` with exact local SHA256 `8a332236c1569726d21044ed343d355e38c152f17e38f605d011bfdb1b9ec09f`. `TASK_STATE=Running`, `HALTED` identity gate, `MATCHING_PYTHON_PROCESSES=2`. PID **6260**, parent PID **8536** (`powershell.exe`), was observed as the direct parent of Python PID **11608**; both Python command lines contained pinned production commit `184e8c2b8fa092a606249ff293a4f507160bff29` and `production_service`. Their process ancestry is one Python root→child under the same PowerShell parent, **not independent root chains**. This alone does not prove exclusive Windows Scheduled Task ownership; no PID was killed or Task stopped/disabled. The Task reports a **configured** restart limit of 10, `MultipleInstances=IgnoreNew` and one enabled trigger; those are not proof of actual ten restarts or non-restart after stopping.

The previous readonly pre-isolation wrapper intentionally rejected both matching Python PIDs by counting `2 != 1`. The proposed candidate-only correction now **accepts only one pinned service Python root, optionally with one direct pinned Python child**, and requires exact `run-production.ps1` parent-PowerShell command identity/commit/runtime/checkout and matching Task action. Any different-commit service process, sibling Python roots, >2 matching service processes, absent/mismatched parent, or a changed PID chain across the SQLite/FINAM prechecks BLOCKS. Subsequent SQLite and fresh two-snapshot FINAM broker checks **have not yet been physically run on the corrected version**. New candidate script SHA256 `2d6e66058b80bef0f5c2dd4c6051c9decbb1032b3531fe05f4d668d836a0def9`; companion `stage8_493_isolation_sqlite_readonly.py` SHA256 remains `0f102987ca04a56abd62f6f3fe54e8cb3266ccfbe3c3852ccb9c7cb47d28f51b`.

This is a READONLY diagnostic refinement only; it never stops Task, re-arms, writes LIVE SQLite, or sends an order. **Task isolation is still NOT AUTHORIZED by a diagnostic PASS**. For controlled isolation, fresh broker flatness and SQLite/lock ownership, Task restart-policy handling and separate explicit operator approval remain hard prerequisites. Stage8.11 one-contract acceptance is not reused; V2 `FINAM_FILL_AUTHORITY_VERIFIED=False` stays in force; `LIVE_PRODUCTION_READY=NO`.

## 2026-10-13 — Intel v3 strict pre-isolation READONLY physical PASS (not Task-stop authority)

Operator executed `powershell.exe -noprofile -executionpolicy bypass -file "c:\tradingsystemlab\stage8-493-pre-isolation-readonly.ps1" -python "c:\tslaudit\fill493\venv\scripts\python.exe"` after installing the reviewed candidate v3 diagnostic (prior pinned SHA-256: `2d6e66058b80bef0f5c2dd4c6051c9decbb1032b3531fe05f4d668d836a0def9`; hash remeasurement was not included in this final operator output). Exact physical stdout:

```text
=== stage8 #493 pre-isolation audit: readonly, no task stop ===
NO_TRADING_TOKEN NO_LIVE_SQLITE_WRITES NO_ORDER_OR_CANCEL NO_TASK_MUTATION NO_REARM
PRODUCTION_SERVICE_PROCESS_CANDIDATES=2
PRODUCTION_CHAIN_ROOT_PID=6260
PRODUCTION_CHAIN_CHILD_PID=11608
PRODUCTION_CHAIN_POWERSHELL_PID=8536
PRODUCTION_PROCESS_SINGLE_BOUND_CHAIN=PASS
TASK_RESTART_LIMIT_CONFIGURED=10
TASK_START_WHEN_AVAILABLE=False
TASK_MULTIPLE_INSTANCES=IgnoreNew
TASK_ENABLED_TRIGGER_COUNT=1
SQLITE_BEFORE_AFTER=PASS
FRESH_BROKER_DOUBLE_SNAPSHOT=PASS
KILL_SWITCH_HALTED=PASS
CLASSIFICATION=PRE_ISOLATION_READONLY_PASS_OPERATOR_REVIEW_REQUIRED
STOP_TASK_AUTHORIZED_BY_THIS_SCRIPT=NO
PRODUCTION_TASK_CHANGED_BY_THIS_SCRIPT=NO
SLTP_REAL_ORDER_AUTHORIZED=NO
```

**Classification:** `STAGE8_493_PHYSICAL_PRE_ISOLATION_READONLY_PASS_OPERATOR_REVIEW_REQUIRED`. This proves exact single *observed* bound Python parent-child production chain, consistent before/after SQLite readonly state, two broker snapshots satisfying independent FINAM real-readonly account/orders zero-position/zero-active-order checks, and continued Task Running with kill switch HALTED at the observation. Credentials were constrained to the existing readonly session probe, no physical order was sent. The wrapper internally consumes rather than prints all nested SQLite and FINAM evidence; the final PASS reflects those nested gates and their zero/clean predicates. Results are a time-bounded observation, **not enduring broker flatness**.

**Still hard-blocked:** the Task has a startup trigger and a configured restart limit of 10; root Python process ancestry and matching command-line are not exclusive proof of Windows Task PID ownership, scheduler stop semantics, or absence of orphaned children after stop. Production's OS lock authority has not been independently proven quiescent; the present Task is running, so no shutdown/quiescence test has occurred. No Task stop/disable/restart, LIVE SQLite or authorization write, rearm, V2 flag change, merge or deployment is authorized by these diagnostics. Prior to any mutation prepare and review an explicit fail-closed operator-only Task-isolation protocol with fresh broker/SQLite checks immediately before and after, proven scheduler action/PID ownership and restart suppression, no orphaned service/lock holder, retained emergency recovery and rollback. Obtain explicit user/operator approval for this production change. AFTER any actual production mutation synchronize CURRENT_STATE/roadmap/runbook/production passport/checklist, then check actual GitHub main against operational authority.

The separate real SLTP 100%-coverage multi-fill acceptance harness (maximum two contracts) is still *offline planning only* and awaits distinct implementation, testing and express risk/order authority; neither `STAGE8_493_PHYSICAL_PRE_ISOLATION_READONLY_PASS_OPERATOR_REVIEW_REQUIRED` nor later Task isolation can authorize orders. `LIVE_PRODUCTION_READY=NO`.

## 2026-10-13 — Controlled Task isolation authorization, candidate package ONLY; LIVE unchanged

Operator approval received to continue *controlled Task isolation only* after the Stage8 #493 physical pre-isolation READONLY PASS. The new package is committed to this **Draft PR** as `stage8-493-controlled-task-isolation.ps1` SHA256 `ca87ea62480c71b81e8c95bb0f9104bcbb103d1dac1673ba71f34317baf4924a`, `stage8-493-post-isolation-readonly.ps1` SHA256 `37df9e1a8f4b0b18ee37d1acc8757ad674160e878264b2746ed0e1bb3e66c201`, `stage8_493_post_isolation_broker_readonly.py` SHA256 `92fc06d2fba9d5d5062d3a3dc14bb74c8c3efd32754a07585dc92d5cb7ea7a13` and `test_stage8_493_controlled_task_isolation.py` (15 independent synthetic/static offline tests PASS). These exact local byte streams were matched to their remote Git blob identifiers. No Windows PowerShell 5.1 native dry-run or physical STOP/disable has yet been completed for these scripts.

The executor defaults to no-mutation **check-only**, which reruns the previous pinned process/SQLite/FINAM/HALTED preflight and records exact Task service PID chain. Explicit `-execute` is physically dangerous and must follow successful Intel check-only review, using the operator's existing Task-isolation approval. It exports the original Task XML into a unique standalone audit file, disables the production Task to suppress startup/restarts, and only then stops the registered Task. It checks process exits, broker account/orders with a separate still-readonly post-stop FINAM session, production SQLite and released state lock. No PID force-stop, rearm, trading token, real order or automatic recovery is included. A failure after a Task mutation attempt is `BLOCKED_OPERATOR_RECOVERY_REQUIRED`, *not* evidence that the previous production runner is restored. A physical PASS would require immediate current-state/roadmap/runbook/passport/checklist synchronization and actual GitHub `main` verification. Until then: **`LIVE_TASK_ISOLATION_NOT_EXECUTED`; `LIVE_PRODUCTION_READY=NO`**.

## 2026-10-13 — Intel controlled Task isolation CHECK-ONLY physical PASS; EXECUTE still not observed

Operator physically invoked without `-execute`:
`powershell.exe -noprofile -executionpolicy bypass -file "c:\tradingsystemlab\stage8-493-controlled-task-isolation.ps1" -python "c:\tslaudit\fill493\venv\scripts\python.exe"`.

Exact reported signals:
```text
=== stage8 #493 controlled production Task isolation ===
NO_REAL_ORDERS NO_REARM NO_TRADING_TOKEN NO_LIVE_SQLITE_MUTATION
FRESH_PROCESS_SQLITE_FINAM_HALTED=PASS
IDENTIFIED_TASK_POWERSHELL_PID=8536
IDENTIFIED_SERVICE_ROOT_PID=6260
IDENTIFIED_SERVICE_CHILD_PID=11608
CLASSIFICATION=CHECK_ONLY_PASS_NO_MUTATION
TASK_MUTATION_ATTEMPTED=False
REAL_ORDER_AUTHORIZED=NO
REARM_PERFORMED=NO
```

This proves the operator's local candidate executor passed **fresh** strict PID chain, Task binding, SQLite before/after, FINAM two READONLY account/orders snapshots and kill switch HALTED before returning at the explicit no-mutation guard. The same PID chain remained `8536 → 6260 → 11608` at that observation. Physical verification of Task backup/disable/stop and post-stop readonly broker/SQLite/lock checks **has not occurred**, and stop semantics/possible orphans remain unproven. The user already gave permission for narrowly scoped controlled isolation, **not** rearm, orders, strategy changes, V2 release or PR merge. Next: execute this exact reviewed isolation file only with `-execute` under the existing explicit permission and fresh preflight; if `BLOCKED_OPERATOR_RECOVERY_REQUIRED`, stop and inspect, never auto-rearm/restart/kill PIDs. If `ISOLATED_HALTED_PENDING_GITHUB_OPERATIONAL_SYNC`, immediately synchronize operational current-state/roadmap/runbook/passport/checklist and verify actual GitHub `main` and Intel physical state. `LIVE_TASK_ISOLATION_NOT_YET_CONFIRMED` and `LIVE_PRODUCTION_READY=NO`.
