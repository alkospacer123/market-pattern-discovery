# Current state — read first

## Current handoff

Stage 8.9 is **COMPLETE** under
`STAGE_8_9_REAL_ACCOUNT_FUNDING_MARGIN_VALIDATION_COMPLETE`.

Stage 8.10 is **COMPLETE** under
`STAGE_8_10_TRADING_TOKEN_LIFECYCLE_COMPLETE`.

Stage 8.10.1 through Stage 8.10.8 are **COMPLETE**.

The production kill switch final accepted state is `HALTED`.
`execution_authorized = false`; `real_order_endpoint_called = false`;
`real_order_count = 0`.

Stage 8.11 is **IN PROGRESS / CODE READY PENDING PHYSICAL ACCEPTANCE**.
Stage 8.12 is **NOT STARTED / NOT AUTHORIZED**.

The current lifecycle gate is Stage 8.11 physical acceptance, but it requires separate explicit authorization.
Stage 8.10 completion does not authorize real execution or LIVE trading.

Current accepted GitHub `main`:
`e24638089d9a8ab8ca8dcd2744c8da151b1d8c58`.

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

Stage 8.11 is **IN PROGRESS / CODE READY PENDING PHYSICAL ACCEPTANCE** — Controlled Real Execution Acceptance.
Stage 8.12 is **NOT STARTED / NOT AUTHORIZED** — FULL/R15 Production Authorization.

Stage 8.11 is the first possible real-order gate, but it requires separate explicit authorization.
Nothing in Stage 8.10 authorizes a real order, live execution, or Stage 8.12.

## Domain boundary

Do not mix TradingSystemLab with BBW, Level Touch, Round Level / Touch, or other projects.

## Update rule

Update this file after every accepted lifecycle gate/audit. The top handoff must always state
the current execution authorization, kill-switch state, real-order count, and next authorized boundary.
