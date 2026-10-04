# TradingSystemLab project context

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

Stage 8.11 is **IN PROGRESS / CODE READY PENDING PHYSICAL ACCEPTANCE**.
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
