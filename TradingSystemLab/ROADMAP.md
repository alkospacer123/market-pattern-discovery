# Evidence-based roadmap

## Historical archive — Stage 8.11 early physical attempts (superseded for current status)

> **Historical only.** This archive preserves evidence from the failed/partial Stage 8.11 attempts. It does not define current project status. Current authority is the later `## Current handoff`, `authority_provenance.json`, and the active Stage 8.12 roadmap below.

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

Current Stage 8.11 authority is only the `## Current handoff` above plus the machine-readable provenance:

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

**ROADMAP DEFINED / NOT STARTED / NOT AUTHORIZED.**

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

**CODE-ONLY / NO REAL-ORDER AUTHORIZATION.**

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

**TEST/AUDIT ONLY / ZERO REAL ORDERS.**

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
- both independent Stage 8 audits PASS.

Exit criterion: exact production commit is independently auditable and still has zero real-order transmission authorization.

### Stage 8.12.3 — Intel production preflight

**REAL ACCOUNT / ZERO ORDERS / STILL NOT AUTHORIZED.**

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
- kill switch `HALTED`;
- production Scheduled Task disabled/not running;
- `execution_authorized = false`;
- zero calls to the real order endpoint.

This preflight does **not** require every N4 instrument to have positive quantity. Each real signal is sized independently under R15 + available margin; quantity `0` means skip that entry.

Exit criterion: external sanitized evidence proves the exact production build is ready to be authorized, while the account remains non-trading.

### Stage 8.12.4 — Explicit FULL/R15 production authorization and activation

**ONLY THIS GATE MAY AUTHORIZE CONTINUOUS REAL PRODUCTION TRADING.**

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

Stage 8.12 completion criterion:

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

**NEXT GATE: Stage 8.12.1 — Production runtime assembly.**

Stage 8.12 has a defined roadmap but is still **NOT STARTED / NOT AUTHORIZED**. Defining this roadmap does not authorize any real-order transmission. Stage 8.12.1 must begin as code-only work with the production kill switch `HALTED`, production Scheduled Task disabled, and `execution_authorized = false`.
