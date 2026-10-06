# Current state — read first

## Stage 8.11 first physical attempt corrective record (2026-10-04)

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

Stage 8.12 — **NOT STARTED / NOT AUTHORIZED**. Stage 8.12 remains not started and not authorized. Stage 8.11 completion does not automatically authorize FULL/R15 production execution, continuous LIVE trading, Scheduled Task activation, or any new order transmission. The production kill switch remains `HALTED` until a separate Stage 8.12 decision and explicit authorization.

## Frozen Stage 7 production specification

Production specification:
`PROD_STAGE7_46DB784378797C7FB04636892350AFF21006D71A31F2CED9D4B974EDA2DC36B8`.

Sole active production identity:
`TRAIL1__N4_01__FULL__R15`.

Frozen production semantics:

- v3 perpetual / T3 / H1;
- basket N4: `USDRUBF + CNYRUBF + GLDRUBF + IMOEXF`;
- TRAIL1 only;
- FULL load;
- R15 = 1.5% current realized equity risk per new instrument position;
- maximum nominal simultaneous initial risk = 6%;
- realized equity only; unrealized PnL excluded;
- one active position per instrument;
- no pyramiding;
- no session filter;
- no automatic canonical fallback.

`CANONICAL__N4_01__FULL__R15` remains
`STABLE_REFERENCE_NOT_ACTIVE_PRODUCTION` only.

## Historical research authority

- v1/v2/v3 research identities and TRUE OOS verdicts remain immutable.
- v3 TRUE OOS: T2/M30 `BORDERLINE`, T2/H1 `BORDERLINE`, T3/M30 `PASS`, T3/H1 `PASS`.
- Stage 5 retrospective economic authority remains `CORRECTED_SINGLE_C1`.
- Stage 6.x and focused N4 decision evidence are revealed historical evidence, not fresh OOS.
- The user explicitly selected `TRAIL1__N4_01__FULL__R15`; Stage 7 froze that exact identity.

## Research-to-robot conformance

Historical conformance remains exact and deterministic:

- research-authority replay: 418 / 418 exact;
- production-robot replay: 418 / 418 exact;
- zero timestamp, direction, price, state or R mismatches;
- repeated replay hashes match.

This establishes implementation conformance only. It does not authorize execution.

## Stage 8.8 operational hardening

Stage 8.8 operational hardening is COMPLETE.
Stages 8.8.1, 8.8.2, 8.8.3, 8.8.4, 8.8.5, 8.8.6, and 8.8.7 are COMPLETE.

Stage 8.8.5 status:
`STAGE_8_8_5_STALE_DATA_PROTECTION_COMPLETE`.
Accepted source commit:
`1c1c2bb5458827f200bc753e7e64db0272b33a8f`.
External Intel evidence SHA-256:
`C57554AE3AE54018EC1E558108520088C1883718F0406E7B6C6669B4696A9CBC`.

Stage 8.8.6 status:
`STAGE_8_8_6_SQLITE_RECOVERY_INTEL_ACCEPTANCE_COMPLETE`.
Accepted code commit:
`dc2b79e74817e71435eee20103ae617e13067d8e`.
External Intel evidence SHA-256:
`1A9B62D4BFC0E7384898C9DF9659E54E50E0E202BD44CE19413864AC2ECA14D6`.

Accepted Stage 8.8.6 recovery hashes:

- backup SHA-256: `00b5e4ca2b389d55389b6b57ac73b5e557c11b72daab8d6e118311613e0aa3b0`;
- manifest SHA-256: `3d0ef1d7cb11ee592be32550625e8badefc596108f4d0c34eff6c5e12ceba822`;
- baseline logical-state SHA-256: `13f01f1009768ddce65dce079f70486f2cbc2508cd1ea8ec4787414a78e0d3be`.

Stage 8.8.7 status:
`STAGE_8_8_7_FINAL_OPERATIONAL_AUDIT_INTEL_ACCEPTANCE_COMPLETE`.
Accepted code commit:
`bda46f57f0f977e05593c46b55851c40c4ad34fe`.
External Intel evidence SHA-256:
`181225F29A966179AB513121C3CBACD31401752956EFC9A22253A8EFBF94766E`.

Stage 8.8 physical acceptance completed with REAL_READONLY, entries disabled,
healthy reconciliation/state recovery, and no live-order authorization.

## Stage 8.9 funding and margin validation

Stage 8.9 is **COMPLETE**.
Canonical status:
`STAGE_8_9_REAL_ACCOUNT_FUNDING_MARGIN_VALIDATION_COMPLETE`.

Stage 8.9.8 status:
`STAGE_8_9_8_COMPLETE`.

The production account authority is `UNION` with exactly one `portfolio_mc`.
The earlier FORTS-only implementation is historical provenance only.

Stage 8.9.10 accepted code commit:
`1013a5a2324e015ab3bc047a7b9af9064552cd10`.

Accepted physical result:
`STAGE_8_9_10_POST_FUNDING_REVALIDATION_PASS=1`.
Funding classification: `STAGE_8_9_FUNDING_MARGIN_VALIDATED`.
Reason: `ALL_AUTHORITIES_VALID`.

External diagnostic report SHA-256:
`C87400F845B73A666B95C83DA2E3B6B710F36F3210AD4AD175BFDABB453864D5`.

External physical summary SHA-256:
`099F85A0DCCF94D404411CFFAC2F5D8C80D606C5C1B5AA2F5B650E8BF5FEB636`.

Stage 8.9.8 portfolio-variant evidence SHA-256:
`60A529DB021B39E1C6117D01CCF3AB5B8B331073D407782E90383E4D124BADC5`.

Stage 8.9.8 financial-shape evidence SHA-256:
`EED27193E35F46FFCF13CFB4A2F2EAA4AB87A35F967D78139E97BFA885009371`.

Accepted Stage 8.9 counts:

- `sizing_case_count = 8`;
- `positive_capacity_case_count = 4`;
- `zero_capacity_case_count = 4`;
- `positive_batch_reservation_count = 1`.

Positive-capacity cases included CNYRUBF LONG/SHORT and GLDRUBF LONG/SHORT.
This proves funding/margin authority and at least one executable contract-capacity case.
It does not prove positive capacity for every N4 instrument, simultaneous all-N4 capacity,
or production execution authorization.

## Stage 8.10 trading-token lifecycle

Stage 8.10 is **COMPLETE**.
Canonical overall status:
`STAGE_8_10_TRADING_TOKEN_LIFECYCLE_COMPLETE`.

Canonical gate sequence:

1. Stage 8.10.1 is **COMPLETE** — `STAGE_8_10_1_TRADING_TOKEN_PRECONDITIONS_COMPLETE`.
2. Stage 8.10.2 is **COMPLETE** — `STAGE_8_10_2_SECURE_PROVISIONING_COMPLETE`.
3. Stage 8.10.3 is **COMPLETE** — `STAGE_8_10_3_IDENTITY_ACCOUNT_BINDING_COMPLETE`.
4. Stage 8.10.4 is **COMPLETE** — `STAGE_8_10_4_PERMISSION_BOUNDARY_COMPLETE`.
5. Stage 8.10.5 is **COMPLETE** — `STAGE_8_10_5_ORDER_PATH_DRY_VALIDATION_COMPLETE`.
6. Stage 8.10.6 is **COMPLETE** — `STAGE_8_10_6_KILL_SWITCH_SAFETY_GATES_COMPLETE`.
7. Stage 8.10.7 is **COMPLETE** — `STAGE_8_10_7_INTEL_TRADING_TOKEN_ACCEPTANCE_COMPLETE`.
8. Stage 8.10.8 is **COMPLETE** — repository-only Stage 8.10 closeout.

### Stage 8.10.2 secure provisioning

Accepted code commit:
`f0c271e428c05ee0ff67b7941e342c06b48a42a0`.
External evidence SHA-256:
`E5FEA93CE28006BC5ADA19F1AA1C1C365FF7CF4BE48A5A1B8BC8C5589DFD754D`.
Physical result:
`STAGE_8_10_2_PHYSICAL_SECURE_PROVISIONING_LOCAL_PASS`.

Trading Token 1 is provisioned in a separate Windows CurrentUser DPAPI store.
Plaintext token/account/DPAPI material remains outside Git.

### Stage 8.10.3 identity/account binding

Accepted code commit:
`428d285336380726a3ce00487e2c85eb755e2dd9`.
External evidence SHA-256:
`0DA102E61AB06FFA6A508CC64203FEA3F56BBA3016891A887688A4E300E11BB6`.
Physical result:
`STAGE_8_10_3_IDENTITY_ACCOUNT_BINDING_PASS`.

Trading and READ_ONLY credentials were validated against the same frozen production account.
No order endpoint was called and order count remained zero.

### Stage 8.10.4 permission boundary

Accepted code commit:
`44858bacc2902591e11adc85cfa5f79e2b62dd5b`.
External evidence SHA-256:
`E4AEDC153F89E000EC034E5F33A6EF7BECB5DA29BA253BC0B28B2AC3D0C26C5D`.
Physical result:
`STAGE_8_10_4_TOKEN_PERMISSION_BOUNDARY_PASS`.

Session-details confirmed READ_ONLY `readonly=true` and Trading Token 1 `readonly=false`.
This proves the token/session permission boundary only, not order acceptance.

### Stage 8.10.5 offline order-path dry validation

Accepted code commit:
`ba284e95954c8473c0e77a95172117bc5cefaf65`.
External evidence SHA-256:
`D878309E22FA49BFFA9EE9B37200C3FE207BF77DB5C29D6DE97010F1FFCE904A`.
Physical result:
`STAGE_8_10_5_OFFLINE_ORDER_PATH_DRY_VALIDATION_PASS`.

The validation was `OFFLINE_SYNTHETIC_NO_TRANSMISSION`.
All frozen N4 payload cases passed local construction/serialization checks.
`real_order_endpoint_called = false`; `real_order_count = 0`.

### Stage 8.10.6 kill switch and safety gates

Accepted code commit:
`35ec9007e6302d66e35e1a42a34fc2e77be8a467`.
External evidence SHA-256:
`CF34E54212B3385F154804F440361FE5E213B0AFA63D8DD8AE56E1EBB49D6B30`.
Physical result:
`STAGE_8_10_6_PHYSICAL_SAFETY_GATE_VALIDATION_PASS`.

The production kill switch is fail-closed. Final accepted state: `HALTED`.
`ARMED` alone never authorizes execution; exact separate `execution_authorized=true` would still be required.
Current accepted value remains `execution_authorized = false`.

### Stage 8.10.7 Intel Trading-Token acceptance

Accepted code commit:
`df4bba6be4f98ba4659e13a01c90bec8e4162ff3`.
External evidence SHA-256:
`A2A6B330A5DC1F15D67A84860223D80786022B634BB8B6CD73E01C815EE7D1B6`.
Physical result:
`STAGE_8_10_7_PHYSICAL_INTEL_TRADING_TOKEN_ACCEPTANCE_PASS`.

Remote scope was strictly `SESSION_CREATE_AND_DETAILS_ONLY`.
Trading Token 1 authenticated and exposed `readonly=false`; the kill switch was `HALTED` before and after.
No order permission was tested; `order_endpoint_called=false`, `order_count=0`,
`execution_authorized=false`, `live_trading_authorized=false`,
`real_order_transmission_authorized=false`.

### Stage 8.10.8 lifecycle closeout

Stage 8.10.8 is **COMPLETE**.
It is repository-only and created no new physical evidence.

Aggregate Stage 8.10 safety facts:

- Trading Token 1 is securely provisioned and identity-bound;
- token permission boundary was validated;
- order path was validated only offline/synthetically;
- kill-switch/safety gates passed;
- Intel token/session acceptance passed;
- production kill switch final accepted state remains `HALTED`;
- `execution_authorized = false`;
- `real_order_endpoint_called = false`;
- `real_order_count = 0`;
- Scheduled Task remains Disabled.

## Authorization boundary

`LIVE_TRADING_NOT_AUTHORIZED` remains in force.
`REAL_ORDER_TRANSMISSION_NOT_AUTHORIZED` remains in force.
`NEW_ENTRIES_DISABLED` remains in force for existing REAL_READONLY paths.

Stage 8.11.0 is **COMPLETE**, Stage 8.11.1 and 8.11.2 are **COMPLETE / PASS**, and Stage 8.11.3 prior authorization is **CONSUMED**; Stage 8.11.4 failed HTTP 400 and Stage 8.11.7 historical intent recovery is COMPLETE / PASS — Controlled Real Execution Acceptance.
Stage 8.12 is **NOT STARTED / NOT AUTHORIZED** — FULL/R15 Production Authorization.

Stage 8.11 is the first possible real-order gate, but it requires separate explicit authorization.
Nothing in Stage 8.10 authorizes a real order, live execution, or Stage 8.12.

## Domain boundary

Do not mix TradingSystemLab with BBW, Level Touch, Round Level / Touch, or other projects.

## Update rule

Update this file after every accepted lifecycle gate/audit. The top handoff must always state
the current execution authorization, kill-switch state, real-order count, and next authorized boundary.

## Stage 8.11.0–8.11.2 canonical lifecycle closeout (2026-10-04)

The accepted physical PRECHECK authority is commit
`9be31f1723877a9c542f89027052570425f7e976`, production specification
`PROD_STAGE7_46DB784378797C7FB04636892350AFF21006D71A31F2CED9D4B974EDA2DC36B8`,
`schema_id = stage8_11_intel_precheck.v1`, and
`mode = STAGE8_11_PRECHECK_ONLY`. The external report remains outside Git at
`runtime/diagnostics/stage8_11_intel_precheck.json`; its SHA-256 is
`7171B7CD0098FF51159DC05C46C0326BF7F412A2D9EA0CBB3F9BDAFBE7745455`.
The external canonical acceptance ledger remains outside Git at
`runtime/state/stage8-11-acceptance.sqlite3`; its physically observed SHA-256 is
`A83C93733321C696225F606A5DBE584413915DA3C46C2B4A261091EC85B7C354`.

The sanitized PRECHECK facts are: Stage 8.10 authority `PASS`; DPAPI authority
`PASS`; trading-session write-capable boundary `PASS`; account binding `PASS`;
reconciliation `PASS`; active orders `0`; canonical unresolved acceptance intents
`0`; unresolved broker intents/orders `0`; instrument binding `PASS`; tradable
`PASS`; recovery readiness `PASS`; R15 permits at least one contract `true`; margin
permits at least one contract `true`; acceptance quantity `1`; execution authorization
observed `false`; order endpoint call count `0`; real order count `0`; and kill switch
observed `HALTED`. The exact and only safety-gate reasons were
`KILL_SWITCH_HALTED` and `EXECUTION_NOT_AUTHORIZED`. Stage 8.12 was
`NOT_STARTED_NOT_AUTHORIZED`.

Immediately before PRECHECK, one structurally order-incapable REAL_READONLY supervisor
cycle completed with: `cycle_count = 23`, `health_status = HEALTHY`,
`reconciliation_status = PASS`, `consecutive_failures = 0`, `entries_enabled = false`,
`unresolved_order_count = 0`, last completed H1
`2026-10-04T10:00:00+00:00`, last successful FINAM contact
`2026-10-04T11:58:57.828648+00:00`, and heartbeat
`2026-10-04T11:59:01.549910+00:00`. Only the sanitized account SHA is retained:
`a113cd66fb2aff5583ddebb480bacf71876cf4f7c10e7209ac6330ccec456826`.

The operational physical-acceptance candidate was research symbol `CNYRUBF`, FINAM
symbol `CNYRUBF@RTSX`, prospective direction `LONG`, quantity `1`. This was **not a
trading signal and not performance selection**. The PRECHECK applies frozen N4
feasibility order `USDRUBF → CNYRUBF → GLDRUBF → IMOEXF` and selects the first member
for which frozen R15 capacity and current directional FINAM margin permit one contract.
It is not a T3 entry signal, PF ranking, optimizer result, portfolio preference, or
production allocation change.

The independent audit result is
`STAGE_8_11_2_INDEPENDENT_PRECHECK_EVIDENCE_AUDIT_PASS`. It confirmed accepted-code
HEAD, fresh healthy heartbeat, account and reconciliation authority, separate
acceptance-ledger and supervisor authorities, zero unresolved acceptance intents,
zero active broker orders, exact frozen registry binding, feasibility-order selection,
`execution_authorized = false`, `HALTED`, zero endpoint calls, zero real orders, and
Scheduled Task `Disabled`. It independently reconstructed the report SHA from the
displayed canonical JSON serialization. The ledger SHA was physically observed; the
external SQLite binary was **not** claimed to have been independently byte-for-byte
rehashed outside the Intel host.

Historical provenance is retained. The first result, `STAGE8_11_SAFETY_GATE_BLOCKED`,
was caused by stale heartbeat/contact after the supervisor was intentionally stopped;
a fresh order-incapable REAL_READONLY cycle removed those transient blockers. The
second, `STAGE8_11_CANONICAL_INTENTS_INVALID`, is classified
`BLOCKED_CANONICAL_INTENT_LEDGER_AUTHORITY_MISMATCH`: PR #356 incorrectly treated
`readonly-supervisor.sqlite3` (production `OperationalState`) as a `StateStore` intent
ledger. The dedicated `stage8-11-acceptance.sqlite3` authority corrected that defect.
The successful PRECHECK supersedes both as the current result without erasing them.

Persistence correction PR #357 has base
`ea090d99266d5dae808c03024f327c41fb8b9170`, head
`60e3f72dae3a08eeb3ba8c756861efbb4c4f28e7`, and merge
`f29053e2c4b5f687115f0a5b12f582e822b60ea1`. Later exact-ledger-schema hardening PR
#358 has base `f29053e2c4b5f687115f0a5b12f582e822b60ea1`, head
`40fcf6f5c165e8bd64b128949358aa7475521f1b`, and merge
`9be31f1723877a9c542f89027052570425f7e976`. PR #358 does not replace PR #357's
historical persistence authority.

Stage 8.11.3 prior authorization is `CONSUMED`. After historical recovery and closeout, and until a new separate explicit operator authorization
after merge and independent audit: kill switch stays `HALTED`;
`execution_authorized = false`; normal LIVE and real-order transmission remain
unauthorized; existing REAL_READONLY paths remain order-incapable; Scheduled Task
stays `Disabled`; and no physical acceptance broker is invoked. There is no automatic
transition from 8.11.2 to 8.11.3. Stage 8.12 remains FULL/R15 Production Authorization,
`NOT STARTED / NOT AUTHORIZED`. Frozen identity `TRAIL1__N4_01__FULL__R15` and all
T3/H1/TRAIL1, N4, R15, 6% cap, realized-equity sizing, margin cap, no-pyramiding,
no-session-filter, and no-canonical-fallback semantics remain unchanged.
