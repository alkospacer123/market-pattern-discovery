# Evidence-based roadmap

## Governing research rule

The original H1 research lifecycle remains:

**Baseline → Optimization → Robustness → Walk Forward → TRUE OOS**.

v1/v2/v3 are historical and immutable. The active roadmap is the frozen Stage 7
production specification plus Stage 8 operational/broker readiness.

## Historical research generations

- v1 — historical discovery / MTF evidence.
- v2 — complete; all four final TRUE OOS studies `BORDERLINE`.
- v3 Perpetual — complete; T2/M30 `BORDERLINE`, T2/H1 `BORDERLINE`,
  T3/M30 `PASS`, T3/H1 `PASS`.

## Post-v3 Stages 1–6.x

Closed historical evidence:

- Stage 1 master evidence consolidation;
- Stage 2 portfolio/diversification analysis;
- Stage 3 trade anatomy/failure analysis;
- Stage 4 structural hypothesis freeze;
- Stage 5 structural validation under `CORRECTED_SINGLE_C1`;
- Stage 6 / 6.x production-decision and retrospective reassessment evidence;
- focused N4 FULL four-case technical closeout.

The user explicitly selected TRAIL1 N4 FULL R15 from the final fixed N4 evidence.

## Stage 7 — Production Specification Freeze

**COMPLETE.**

Production specification:
`PROD_STAGE7_46DB784378797C7FB04636892350AFF21006D71A31F2CED9D4B974EDA2DC36B8`.

Sole active identity:
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

`CANONICAL__N4_01__FULL__R15` is reference only.

## Stage 8 — Robot / FINAM integration

**ACTIVE. LIVE TRADING NOT AUTHORIZED.**

Historical research-to-robot conformance remains 418/418 exact in both authority
and production replay with deterministic hashes and zero mismatch classes.

All four production instruments remain `AUTHENTICATED_REAL_READONLY`.

## Stage 8.8 — operational hardening

Stage 8.8 operational hardening is COMPLETE.
Stages 8.8.1, 8.8.2, 8.8.3, 8.8.4, 8.8.5, 8.8.6, and 8.8.7 are COMPLETE.

### Stage 8.8.5 — stale H1 protection

Status: `STAGE_8_8_5_STALE_DATA_PROTECTION_COMPLETE`.

Accepted audited source commit:
`1c1c2bb5458827f200bc753e7e64db0272b33a8f`.

External Intel evidence SHA-256:
`C57554AE3AE54018EC1E558108520088C1883718F0406E7B6C6669B4696A9CBC`.

Schedule-aware stale-data fault injection/recovery passed on Intel. Entries
remained disabled and no order-capable call was made.

### Stage 8.8.6 — SQLite backup/recovery

Status: `STAGE_8_8_6_SQLITE_RECOVERY_INTEL_ACCEPTANCE_COMPLETE`.

Accepted code commit:
`dc2b79e74817e71435eee20103ae617e13067d8e`.

External Intel evidence SHA-256:
`1A9B62D4BFC0E7384898C9DF9659E54E50E0E202BD44CE19413864AC2ECA14D6`.

Accepted backup SHA-256:
`00b5e4ca2b389d55389b6b57ac73b5e557c11b72daab8d6e118311613e0aa3b0`.

Accepted manifest SHA-256:
`3d0ef1d7cb11ee592be32550625e8badefc596108f4d0c34eff6c5e12ceba822`.

Accepted baseline logical-state SHA-256:
`13f01f1009768ddce65dce079f70486f2cbc2508cd1ea8ec4787414a78e0d3be`.

### Stage 8.8.7 — Final Operational Audit

Status: `STAGE_8_8_7_FINAL_OPERATIONAL_AUDIT_INTEL_ACCEPTANCE_COMPLETE`.

Accepted code commit:
`bda46f57f0f977e05593c46b55851c40c4ad34fe`.

External Intel acceptance evidence SHA-256:
`181225F29A966179AB513121C3CBACD31401752956EFC9A22253A8EFBF94766E`.

Final physical acceptance passed with REAL_READONLY, entries disabled, healthy
reconciliation/watermarks, zero unresolved orders and no live order transmission.

## Stage 8.9 — Funding / margin readiness

**COMPLETE.** Stage 8.9 is **COMPLETE**.

Canonical status: `STAGE_8_9_REAL_ACCOUNT_FUNDING_MARGIN_VALIDATION_COMPLETE`.

### Stage 8.9.8 — account-authority correction

Status: `STAGE_8_9_8_COMPLETE`.

The production account is `UNION`; the authenticated funding authority is exactly
one `portfolio_mc`. The earlier FORTS-only assumption is historical only.

Portfolio-variant evidence SHA-256:
`60A529DB021B39E1C6117D01CCF3AB5B8B331073D407782E90383E4D124BADC5`.

Account financial-shape evidence SHA-256:
`EED27193E35F46FFCF13CFB4A2F2EAA4AB87A35F967D78139E97BFA885009371`.

The earlier FORTS-only result is historical provenance only:
`BLOCKED_ACCOUNT_FINANCIALS_UNAVAILABLE` / `FORTS_PORTFOLIO_MISSING`, accepted
code `5deedb49f16d9f2525c430383a029017cd9a53ce`, diagnostic SHA-256
`2911D7857B9404E5178FF1A754A9168845E457A9349CEF7B1AFD0E088E06BF46`, and
summary SHA-256
`59A9ADD4BD229C7A7BF3E20337E494F90CF90082208469AD5A694A4B075D852B`.
It is not a current blocker.

### Stage 8.9.9 — physical revalidation

Stage 8.9.9 is **PHYSICAL REVALIDATION COMPLETE**.

The pre-funding zero-capacity result is historical provenance only:
`BLOCKED_INSUFFICIENT_CONTRACT_CAPACITY` / `ZERO_CONTRACT_CAPACITY`, accepted
code `c461911fdceddf54a2a6fe6768574dd93f4844d1`, diagnostic SHA-256
`F307D3F5ADC4525FF304B9582F683B89A097FC9BCFB502E8150FC98D2625860F`, summary
SHA-256 `F36B16565F9E08C38B3264831DCA94A65390275F7A2B78A3C6C90302E4A7C09B`, and
`positive_capacity_case_count = 0`. It is not a current blocker.

### Stage 8.9.10 — post-funding closeout

Stage 8.9.10 is **COMPLETE**.

Accepted physical code commit:
`1013a5a2324e015ab3bc047a7b9af9064552cd10`.

Physical result: `STAGE_8_9_10_POST_FUNDING_REVALIDATION_PASS=1`.
Classification: `STAGE_8_9_FUNDING_MARGIN_VALIDATED`.
Reason: `ALL_AUTHORITIES_VALID`.

External diagnostic report SHA-256:
`C87400F845B73A666B95C83DA2E3B6B710F36F3210AD4AD175BFDABB453864D5`.

External physical summary SHA-256:
`099F85A0DCCF94D404411CFFAC2F5D8C80D606C5C1B5AA2F5B650E8BF5FEB636`.

Accepted counts are `sizing_case_count = 8`,
`positive_capacity_case_count = 4`, `zero_capacity_case_count = 4`, and
`positive_batch_reservation_count = 1`. This establishes account funding and
FINAM margin authority plus at least one executable contract-capacity case.

It does **not** establish positive capacity for every N4 instrument,
simultaneous FULL N4 portfolio capacity, or FULL/R15 production funding
sufficiency. It does not authorize trading, a trading token, or real execution.

## Later gates

- Stage 8.10 — **IN PROGRESS**; Stage 8.10.1 is complete and Stage 8.10.2 is complete and Stage 8.10.3 is complete.
- Stage 8.11 — **NOT STARTED / NOT AUTHORIZED**.
- Stage 8.12 — **NOT STARTED / NOT AUTHORIZED**.

`LIVE_TRADING_NOT_AUTHORIZED` remains in force.
`REAL_ORDER_TRANSMISSION_NOT_AUTHORIZED` remains in force.
`NEW_ENTRIES_DISABLED` remains in force for REAL_READONLY acceptance paths.

## Current handoff

Stage 8.9 is complete. Stage 8.10 is **IN PROGRESS** because Stage 8.10.1 and
Stage 8.10.2 are complete. Stage 8.10.3 is **COMPLETE**. Stage 8.10.4 is **COMPLETE**. Stage 8.10.5 is
the next gate and requires separate explicit authorization.

## Persistent constraints

- no live trading without explicit separate authorization;
- no runtime mutation of Stage 7 identity;
- no canonical fallback;
- no fabricated cash/equity/margin/capacity;
- no reinterpretation of REAL_READONLY success as live authorization;
- no mixing with BBW / Level Touch / Round Level projects;
- no rewrite of historical v1/v2/v3 verdicts.

## Stage 8.10 — trading-token lifecycle

Stage 8.9 is **COMPLETE** under
`STAGE_8_9_REAL_ACCOUNT_FUNDING_MARGIN_VALIDATION_COMPLETE`. Its accepted code,
diagnostic SHA-256, physical-summary SHA-256, capacity counts, classification,
and reason recorded above remain unchanged.

Stage 8.10 is **IN PROGRESS**. This lifecycle state records completion of the
preconditions, secure-provisioning, and identity/account-binding gates; it does
not complete Stage 8.10 or authorize permission validation or execution.

Canonical Stage 8.10 sequence and status:

1. Stage 8.10.1 is **COMPLETE** — Trading Token Preconditions Gate.
   Canonical status: `STAGE_8_10_1_TRADING_TOKEN_PRECONDITIONS_COMPLETE`.
2. Stage 8.10.2 is **COMPLETE** — Secure Provisioning.
3. Stage 8.10.3 is **COMPLETE** — Identity / Account Binding.
4. Stage 8.10.4 is **COMPLETE** — Permission Boundary Validation.
5. Stage 8.10.5 is **COMPLETE** — Order Path Dry Validation.
6. Stage 8.10.6 is **COMPLETE** — Kill Switch / Safety Gates.
7. Stage 8.10.7 is **COMPLETE** — Intel Trading-Token Acceptance.
8. Stage 8.10.8 is **NOT STARTED** — Stage 8.10 Closeout.

Stage 8.11 is **NOT STARTED / NOT AUTHORIZED** — Controlled Real Execution
Acceptance, exactly one-contract test. Stage 8.12 is **NOT STARTED / NOT AUTHORIZED** — FULL/R15 Production Authorization. Stage 8.11 remains the first
possible real-order gate and requires separate explicit authorization.

### Stage 8.10.1 security boundary

The READ_ONLY credential remains the only operational credential. Existing
REAL_READONLY credential handling remains bound to Windows CurrentUser DPAPI,
and the REAL_READONLY broker cannot submit real orders. Trading Token 1 is now provisioned locally in the separate Windows CurrentUser
DPAPI store. Its plaintext, account ID, DPAPI bytes, and runtime metadata remain
outside Git. Possession or storage of Token 1 does not authorize trading.

Plaintext tokens must never be written to Git, logs, command-line arguments,
committed JSON, runtime audit output, or repository metadata. Trading and
read-only credentials must be distinguishable by schema/mode, must never
silently substitute for each other, and token/account/production-ID binding
must fail closed. Acquiring or storing a token cannot authorize order
transmission.

Physical provisioning was performed and Trading Token 1 is provisioned locally
in Windows CurrentUser DPAPI. Token 1 has now been used, and FINAM authentication
has now been performed solely for Stage 8.10.3 identity/session validation.
Stage 8.10 order_count remains exactly 0;
no order-capable operation occurred, no live order was transmitted, and the
Scheduled Task remains Disabled. Possession or storage does not authorize
trading, and real-order capability is not authorized.

`LIVE_TRADING_NOT_AUTHORIZED`, `REAL_ORDER_TRANSMISSION_NOT_AUTHORIZED`, and
`NEW_ENTRIES_DISABLED` remain enforced. The frozen production contract remains
`PROD_STAGE7_46DB784378797C7FB04636892350AFF21006D71A31F2CED9D4B974EDA2DC36B8`
/ `TRAIL1__N4_01__FULL__R15`: T3, H1, exact N4 (`USDRUBF`, `CNYRUBF`,
`GLDRUBF`, `IMOEXF`), TRAIL1, FULL, R15, 1.5% of current realized equity per
new instrument position, 6% maximum nominal simultaneous initial risk, no
pyramiding, no session filter, and no runtime canonical fallback.


### Stage 8.10.2 secure provisioning completed gate

Canonical status: `STAGE_8_10_2_SECURE_PROVISIONING_COMPLETE`. Accepted physical code commit:
`f0c271e428c05ee0ff67b7941e342c06b48a42a0`. External physical evidence SHA-256:
`E5FEA93CE28006BC5ADA19F1AA1C1C365FF7CF4BE48A5A1B8BC8C5589DFD754D`. Physical
result: `STAGE_8_10_2_PHYSICAL_SECURE_PROVISIONING_LOCAL_PASS`. Physical
provisioning was performed and Trading Token 1 is provisioned locally in Windows
CurrentUser DPAPI. Possession/storage of Token 1 does not authorize trading.
`trading_token_used=false`; `finam_authentication_performed=false`; no
order-capable operation occurred; `order_count=0`; and the Scheduled Task remains
Disabled. Stage 8.10 is **IN PROGRESS**; Stage 8.10.4 is **COMPLETE**; Stage 8.10.6 is **COMPLETE**; Stage 8.10.7 is **COMPLETE** and Stage 8.10.8 is
**NOT STARTED**. Stage 8.11 is **NOT STARTED / NOT AUTHORIZED** and Stage 8.12 is
**NOT STARTED / NOT AUTHORIZED**. `LIVE_TRADING_NOT_AUTHORIZED`,
`REAL_ORDER_TRANSMISSION_NOT_AUTHORIZED`, and `NEW_ENTRIES_DISABLED` remain in
force.


## Stage 8.10.3 identity/account binding completed gate

Stage 8.10 is **IN PROGRESS**. Stage 8.10.1 is **COMPLETE** under
`STAGE_8_10_1_TRADING_TOKEN_PRECONDITIONS_COMPLETE`. Stage 8.10.2 is **COMPLETE**
under `STAGE_8_10_2_SECURE_PROVISIONING_COMPLETE`; its historical facts remain
scoped to that earlier gate. Stage 8.10.3 is **COMPLETE** under
`STAGE_8_10_3_IDENTITY_ACCOUNT_BINDING_COMPLETE`.

Accepted physical code commit: `428d285336380726a3ce00487e2c85eb755e2dd9`. External physical evidence SHA-256:
`0DA102E61AB06FFA6A508CC64203FEA3F56BBA3016891A887688A4E300E11BB6`. Physical result: `STAGE_8_10_3_IDENTITY_ACCOUNT_BINDING_PASS`. The external
`stage8_10_3_identity_account_binding.json` remains outside Git; only its digest
and sanitized facts are repository authority.

Before remote authentication, the trading and READ_ONLY credentials resolved
locally to the same production account. Token 1 successfully created a FINAM
session and the expected production account was enumerated exactly once. Token
1 has now been used and FINAM authentication has now been performed, solely for
Stage 8.10.3 session identity/account-binding validation. No permission
validation or order-path validation occurred. No order endpoint was called and
`order_count` remains exactly 0. LIVE trading and real-order transmission remain
unauthorized. The Scheduled Task remains Disabled.

In this historical Stage 8.10.3 snapshot, Stage 8.10.5 was
**NOT STARTED**. In the current lifecycle, Stage 8.10.4 and Stage 8.10.5 are **COMPLETE**. Stage 8.10.6 is **COMPLETE**, Stage 8.10.7 is **COMPLETE**, and Stage 8.10.8 is **NOT STARTED**. Stage 8.11 is **NOT STARTED /
NOT AUTHORIZED**. Stage 8.12 is **NOT STARTED / NOT AUTHORIZED**. That code-ready statement is historical; Stage 8.10.5 is now **COMPLETE**.


## Stage 8.10.4 permission boundary complete

Canonical status: `STAGE_8_10_4_PERMISSION_BOUNDARY_COMPLETE`.
Stage 8.10.4 is **COMPLETE**. Accepted physical code:
`44858bacc2902591e11adc85cfa5f79e2b62dd5b`. External evidence SHA-256:
`E4AEDC153F89E000EC034E5F33A6EF7BECB5DA29BA253BC0B28B2AC3D0C26C5D`. Physical
result: `STAGE_8_10_4_TOKEN_PERMISSION_BOUNDARY_PASS`. The external
`stage8_10_4_permission_boundary.json` remains outside Git.

Before authentication, the READ_ONLY and trading credentials still resolved
locally to the same frozen production account. The READ_ONLY session and trading
Token 1 session were created successfully. The expected production account
appeared exactly once in each session. Session-details returned exact boolean
`readonly=true` for READ_ONLY and exact boolean `readonly=false` for trading
Token 1; the token-level permission boundary therefore passed.

This proves only the FINAM session-details token-level boundary. No order-path
validation occurred, no order endpoint was called, and `order_count=0`. LIVE
trading remains unauthorized, real-order transmission remains unauthorized, and
the Scheduled Task remains Disabled. Stage 8.10.5 is **COMPLETE** after accepted physical offline validation. Stage 8.10.6 is **COMPLETE**. Stage 8.10.7
is **NOT STARTED**. Stage 8.10.8 is **NOT STARTED**. Stage 8.10 remains **IN
PROGRESS**. Stage 8.11 is **NOT STARTED / NOT AUTHORIZED**. Stage 8.12 is **NOT
STARTED / NOT AUTHORIZED**.


## Stage 8.10.5 physical offline order-path dry-validation complete

Canonical status: `STAGE_8_10_5_ORDER_PATH_DRY_VALIDATION_COMPLETE`.
Stage 8.10.5 is **COMPLETE**.

Accepted code commit: `ba284e95954c8473c0e77a95172117bc5cefaf65`.
External evidence SHA-256: `D878309E22FA49BFFA9EE9B37200C3FE207BF77DB5C29D6DE97010F1FFCE904A`.
Physical result: `STAGE_8_10_5_OFFLINE_ORDER_PATH_DRY_VALIDATION_PASS`.
The external `stage8_10_5_order_path_dry_validation.json` remains outside Git;
only its digest and sanitized facts are repository authority.

The physical validation used `OFFLINE_SYNTHETIC_NO_TRANSMISSION` and was fully
offline. No FINAM credential was used, no FINAM authentication occurred, no
external network call occurred, and no real account ID was used. All 16 frozen
N4 broker payload cases passed, including client-order-ID and market-order
serialization validation. One synthetic order POST was intercepted in the
success path and one synthetic order POST was intercepted in the uncertainty
path. The automatic order retry count was zero. The real order endpoint remained
uncalled (`real_order_endpoint_called = false`) and `real_order_count = 0`.
This validates only deterministic local construction and serialization through
an in-process synthetic transport; it does not establish broker acceptance,
execution permission, exchange acceptance, fills, cancellation, margin
sufficiency, LIVE readiness, or production trading authorization.

- Stage 8.10.1 is **COMPLETE**.
- Stage 8.10.2 is **COMPLETE**.
- Stage 8.10.3 is **COMPLETE**.
- Stage 8.10.4 is **COMPLETE**; its historical authority is unchanged.
- Stage 8.10.5 is **COMPLETE**.
- Stage 8.10.6 is **COMPLETE**. Stage 8.10.7 is **COMPLETE**. Stage 8.10.8 is **NOT STARTED**.
- Stage 8.10 is **IN PROGRESS**.
- Stage 8.11 is **NOT STARTED / NOT AUTHORIZED**. Stage 8.12 is **NOT STARTED / NOT AUTHORIZED**.

Stage 8.10.6 — Kill Switch / Safety Gates is **COMPLETE** after accepted physical Intel validation. LIVE trading and
real-order transmission remain unauthorized, and the Scheduled Task remains
Disabled. `LIVE_TRADING_NOT_AUTHORIZED` and
`REAL_ORDER_TRANSMISSION_NOT_AUTHORIZED` remain in force.

## Stage 8.10.6 kill switch / safety gates complete

Canonical status: `STAGE_8_10_6_KILL_SWITCH_SAFETY_GATES_COMPLETE`. Physical validation is complete on accepted code `35ec9007e6302d66e35e1a42a34fc2e77be8a467`; the external evidence SHA-256 is `CF34E54212B3385F154804F440361FE5E213B0AFA63D8DD8AE56E1EBB49D6B30`, and the physical result is `STAGE_8_10_6_PHYSICAL_SAFETY_GATE_VALIDATION_PASS`.

On Intel, pandas 3.0.6 was present and the full Stage 8 suite passed 518 tests with 0 failures. The production kill switch was initialized and remained `HALTED`. The isolated synthetic matrix passed all 25 cases: 1 `OPEN` and 24 `BLOCKED`; emergency HALT passed. `execution_authorized=false`. No credential was used, no FINAM authentication or external network request occurred, no real order endpoint was called, and the real order count was 0. The Scheduled Task remained Disabled. Stage 8.10.7 was not started.

The durable external kill switch defaults fail closed. Its canonical safe production state is `HALTED`; a missing, malformed, mismatched, or unknown state blocks new entries. `ARMED` alone never authorizes trading: a separate exact `execution_authorized=true` input is required, and the current/operator value is `false`. The Stage 8.10.6 wrapper exposes HALT only and cannot arm production. This is only a new-entry inhibit; it neither implements nor authorizes exits, cancels, broker calls, LIVE trading, or order transmission. Existing LIVE and real-order-transmission blocks remain unchanged.

Stage 8.10.7 is **COMPLETE** and Stage 8.10.8 is **NOT STARTED**. Stage 8.10 remains **IN PROGRESS**. Stage 8.11 and Stage 8.12 remain **NOT STARTED / NOT AUTHORIZED**.


## Stage 8.10.7 Intel Trading-Token acceptance complete

Stage 8.10.7 is **COMPLETE** (`STAGE_8_10_7_INTEL_TRADING_TOKEN_ACCEPTANCE_COMPLETE`). Physical Intel validation was accepted against code commit `df4bba6be4f98ba4659e13a01c90bec8e4162ff3`; the external evidence SHA-256 is `A2A6B330A5DC1F15D67A84860223D80786022B634BB8B6CD73E01C815EE7D1B6`, and the physical result is `STAGE_8_10_7_PHYSICAL_INTEL_TRADING_TOKEN_ACCEPTANCE_PASS`. The external report remains outside Git.

The accepted Intel host used pandas 3.0.6. Focused Stage 8.10.7 validation passed 97 tests (91 deselected), and the full Stage 8 suite passed 615 tests with 0 failures. The DPAPI CurrentUser Trading credential was validated, and its production/account identity matched the locally loaded READ_ONLY credential. Trading Token 1 alone was used for remote authentication; the READ_ONLY credential was not used for remote authentication. FINAM authentication created one session, and the expected production account occurred exactly once. Session details returned the exact boolean `readonly=false`, confirming only the token/session write-permission boundary.

The remote method scope was strictly `SESSION_CREATE_AND_DETAILS_ONLY` (`FinamAPI.create_session()` and `FinamAPI.session_details()`). No order permission was tested: `order_endpoint_called=false`, `order_count=0`, `execution_authorized=false`, `live_trading_authorized=false`, and `real_order_transmission_authorized=false`. The valid production kill switch was observed `HALTED` both before and after authentication, remained unmodified, and the Scheduled Task remained Disabled.

Stage 8.10 remains **IN PROGRESS**. Stage 8.10.8 is **NOT STARTED** and is the next separate lifecycle gate; it was not implemented or executed here. Stage 8.11 and Stage 8.12 remain **NOT STARTED / NOT AUTHORIZED**. `LIVE_TRADING_NOT_AUTHORIZED` and `REAL_ORDER_TRANSMISSION_NOT_AUTHORIZED` remain in force.
