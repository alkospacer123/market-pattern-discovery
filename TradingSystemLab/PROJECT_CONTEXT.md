# TradingSystemLab project context

## Current handoff

Stage 8.9 is **COMPLETE**. Stage 8.10 is **COMPLETE**. Stage 8.10 is recorded under
`STAGE_8_10_TRADING_TOKEN_LIFECYCLE_COMPLETE`; Stage 8.10.1 through Stage 8.10.8 are **COMPLETE**.

Stage 8.11.0 — Code / Readiness Corrections is **COMPLETE**.
Stage 8.11.1 — Intel Zero-Order PRECHECK is **COMPLETE / PASS** with physical result
`STAGE8_11_PRECHECK_ONLY_PASS` and `real_order_count = 0`.
Stage 8.11.2 — Independent PRECHECK Evidence Audit is **COMPLETE / PASS** under
`STAGE_8_11_2_INDEPENDENT_PRECHECK_EVIDENCE_AUDIT_PASS`.

The current lifecycle gate is **Stage 8.11.3 — Explicit One-Contract Authorization**.
Stage 8.11.3 is **NOT AUTHORIZED / OPERATOR BOUNDARY CODE READY**. Passing Stage 8.11.1 and Stage 8.11.2 does not
authorize a FINAM order; a separate explicit operator authorization is required only
after this repository closeout is merged and independently audited.

The production kill switch final accepted state is `HALTED`.
`execution_authorized = false`; `real_order_endpoint_called = false`;
`real_order_count = 0`; Scheduled Task is `Disabled`.
Stage 8.12 is **NOT STARTED / NOT AUTHORIZED**.

## Purpose and authority

TradingSystemLab is the repository's deterministic systematic-trading research,
production-design, and robot/FINAM integration domain. The Git repository is
the authoritative persistent project memory.

Read `CURRENT_STATE.md` first.

## Canonical research lifecycle

The sole research-methodology authority remains:

**Baseline → Optimization → Robustness → Walk Forward → TRUE OOS**.

Candidate freeze is procedural identity fixation, not an additional research phase.
v1/v2/v3 identities and OOS verdicts remain immutable.

## Historical generations

- v1 — historical discovery and MTF evidence.
- v2 — complete; all four final TRUE OOS studies `BORDERLINE`.
- v3 Perpetual — complete; T2/M30 `BORDERLINE`, T2/H1 `BORDERLINE`,
  T3/M30 `PASS`, T3/H1 `PASS`.

v3 TRUE OOS is consumed.

## Frozen production identity

Stage 7 is COMPLETE.

Production specification:
`PROD_STAGE7_46DB784378797C7FB04636892350AFF21006D71A31F2CED9D4B974EDA2DC36B8`.

Sole active identity:
`TRAIL1__N4_01__FULL__R15`.

Frozen production semantics:

- v3 perpetual / T3 / H1;
- USDRUBF + CNYRUBF + GLDRUBF + IMOEXF;
- TRAIL1;
- FULL;
- R15 = 1.5% current realized equity risk per new instrument position;
- maximum nominal simultaneous initial risk 6%;
- realized equity only;
- one active position per instrument;
- no pyramiding;
- no session filter;
- no canonical fallback.

`CANONICAL__N4_01__FULL__R15` is reference only.

## Stage 8.8 operational hardening

Stage 8.8 operational hardening is COMPLETE.
Stages 8.8.1, 8.8.2, 8.8.3, 8.8.4, 8.8.5, 8.8.6, and 8.8.7 are COMPLETE.

Key accepted provenance:

- Stage 8.8.5: `STAGE_8_8_5_STALE_DATA_PROTECTION_COMPLETE`, code
  `1c1c2bb5458827f200bc753e7e64db0272b33a8f`, external evidence
  `C57554AE3AE54018EC1E558108520088C1883718F0406E7B6C6669B4696A9CBC`;
- Stage 8.8.6: `STAGE_8_8_6_SQLITE_RECOVERY_INTEL_ACCEPTANCE_COMPLETE`, code
  `dc2b79e74817e71435eee20103ae617e13067d8e`, external evidence
  `1A9B62D4BFC0E7384898C9DF9659E54E50E0E202BD44CE19413864AC2ECA14D6`;
- Stage 8.8.7: `STAGE_8_8_7_FINAL_OPERATIONAL_AUDIT_INTEL_ACCEPTANCE_COMPLETE`, code
  `bda46f57f0f977e05593c46b55851c40c4ad34fe`, external evidence
  `181225F29A966179AB513121C3CBACD31401752956EFC9A22253A8EFBF94766E`.

Stage 8.8 did not authorize LIVE trading.

## Stage 8.9 funding and margin validation

Stage 8.9 is **COMPLETE**.
Canonical status:
`STAGE_8_9_REAL_ACCOUNT_FUNDING_MARGIN_VALIDATION_COMPLETE`.

Stage 8.9.8 is `STAGE_8_9_8_COMPLETE`; account authority is UNION / `portfolio_mc`.

Accepted Stage 8.9.10 code commit:
`1013a5a2324e015ab3bc047a7b9af9064552cd10`.

Accepted physical result:
`STAGE_8_9_10_POST_FUNDING_REVALIDATION_PASS=1`.
Funding classification: `STAGE_8_9_FUNDING_MARGIN_VALIDATED`.
Reason: `ALL_AUTHORITIES_VALID`.

Diagnostic SHA-256:
`C87400F845B73A666B95C83DA2E3B6B710F36F3210AD4AD175BFDABB453864D5`.

Physical summary SHA-256:
`099F85A0DCCF94D404411CFFAC2F5D8C80D606C5C1B5AA2F5B650E8BF5FEB636`.

Stage 8.9.8 portfolio-variant SHA-256:
`60A529DB021B39E1C6117D01CCF3AB5B8B331073D407782E90383E4D124BADC5`.

Stage 8.9.8 financial-shape SHA-256:
`EED27193E35F46FFCF13CFB4A2F2EAA4AB87A35F967D78139E97BFA885009371`.

Accepted counts:
`sizing_case_count = 8`; `positive_capacity_case_count = 4`;
`zero_capacity_case_count = 4`; `positive_batch_reservation_count = 1`.

Stage 8.9 completion validates funding/margin authority and some positive contract capacity.
It does not establish positive capacity for every N4 instrument or authorize trading.

## Stage 8.10 trading-token lifecycle

Stage 8.10 is **COMPLETE** under
`STAGE_8_10_TRADING_TOKEN_LIFECYCLE_COMPLETE`.

Gate statuses:

- Stage 8.10.1 is **COMPLETE** — `STAGE_8_10_1_TRADING_TOKEN_PRECONDITIONS_COMPLETE`;
- Stage 8.10.2 is **COMPLETE** — `STAGE_8_10_2_SECURE_PROVISIONING_COMPLETE`;
- Stage 8.10.3 is **COMPLETE** — `STAGE_8_10_3_IDENTITY_ACCOUNT_BINDING_COMPLETE`;
- Stage 8.10.4 is **COMPLETE** — `STAGE_8_10_4_PERMISSION_BOUNDARY_COMPLETE`;
- Stage 8.10.5 is **COMPLETE** — `STAGE_8_10_5_ORDER_PATH_DRY_VALIDATION_COMPLETE`;
- Stage 8.10.6 is **COMPLETE** — `STAGE_8_10_6_KILL_SWITCH_SAFETY_GATES_COMPLETE`;
- Stage 8.10.7 is **COMPLETE** — `STAGE_8_10_7_INTEL_TRADING_TOKEN_ACCEPTANCE_COMPLETE`;
- Stage 8.10.8 is **COMPLETE** — repository-only lifecycle closeout.

Stage 8.10.2 accepted code:
`f0c271e428c05ee0ff67b7941e342c06b48a42a0`.
External evidence:
`E5FEA93CE28006BC5ADA19F1AA1C1C365FF7CF4BE48A5A1B8BC8C5589DFD754D`.
Physical result:
`STAGE_8_10_2_PHYSICAL_SECURE_PROVISIONING_LOCAL_PASS`.

Stage 8.10.3 accepted code:
`428d285336380726a3ce00487e2c85eb755e2dd9`; physical result
`STAGE_8_10_3_IDENTITY_ACCOUNT_BINDING_PASS`.

Stage 8.10.4 accepted code:
`44858bacc2902591e11adc85cfa5f79e2b62dd5b`; physical result
`STAGE_8_10_4_TOKEN_PERMISSION_BOUNDARY_PASS`.

Stage 8.10.5 accepted code:
`ba284e95954c8473c0e77a95172117bc5cefaf65`; physical result
`STAGE_8_10_5_OFFLINE_ORDER_PATH_DRY_VALIDATION_PASS`.

Stage 8.10.6 accepted code:
`35ec9007e6302d66e35e1a42a34fc2e77be8a467`; physical result
`STAGE_8_10_6_PHYSICAL_SAFETY_GATE_VALIDATION_PASS`.

Stage 8.10.7 accepted code:
`df4bba6be4f98ba4659e13a01c90bec8e4162ff3`; physical result
`STAGE_8_10_7_PHYSICAL_INTEL_TRADING_TOKEN_ACCEPTANCE_PASS`.

Trading Token 1 is provisioned separately in Windows CurrentUser DPAPI.
The token/session write-permission boundary was validated, but order permission was not.
The order path was validated only offline/synthetically.

The fail-closed kill switch final accepted state is `HALTED`.
`execution_authorized = false`; no real order endpoint was called;
`real_order_count = 0`.

## Authorization boundary

`LIVE_TRADING_NOT_AUTHORIZED` remains authoritative.
`REAL_ORDER_TRANSMISSION_NOT_AUTHORIZED` remains authoritative.
`NEW_ENTRIES_DISABLED` remains in force for existing REAL_READONLY paths.

Stage 8.11.0 is **COMPLETE**, Stage 8.11.1 and 8.11.2 are **COMPLETE / PASS**, and Stage 8.11.3 is **NOT AUTHORIZED / OPERATOR BOUNDARY CODE READY**.
Stage 8.12 is **NOT STARTED / NOT AUTHORIZED**.

Stage 8.11 is the first possible real-order gate and requires separate explicit authorization.
No Stage 8.10 result authorizes a real order or Stage 8.12.

## Domain boundaries

TradingSystemLab remains separate from BBW, Level Touch, Round Level / Touch, and other projects.

## Persistent-memory read order

1. `CURRENT_STATE.md`
2. `PROJECT_CONTEXT.md`
3. `METHODOLOGY.md`
4. `ROADMAP.md`
5. `AUDIT_PROTOCOL.md`

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

Stage 8.11.3 remains `NOT AUTHORIZED`. Until separate explicit operator authorization
after merge and independent audit: kill switch stays `HALTED`;
`execution_authorized = false`; normal LIVE and real-order transmission remain
unauthorized; existing REAL_READONLY paths remain order-incapable; Scheduled Task
stays `Disabled`; and no physical acceptance broker is invoked. There is no automatic
transition from 8.11.2 to 8.11.3. Stage 8.12 remains FULL/R15 Production Authorization,
`NOT STARTED / NOT AUTHORIZED`. Frozen identity `TRAIL1__N4_01__FULL__R15` and all
T3/H1/TRAIL1, N4, R15, 6% cap, realized-equity sizing, margin cap, no-pyramiding,
no-session-filter, and no-canonical-fallback semantics remain unchanged.
