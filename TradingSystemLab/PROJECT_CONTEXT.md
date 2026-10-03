# TradingSystemLab project context

## Purpose and authority

TradingSystemLab is the repository's deterministic systematic-trading research,
production-design, and robot/FINAM integration domain. The Git repository is
the authoritative persistent memory.

Read `CURRENT_STATE.md` first.

## Canonical research lifecycle

The sole research-methodology authority remains:

**Baseline → Optimization → Robustness → Walk Forward → TRUE OOS**.

Candidate freeze is identity fixation, not a sixth phase. Historical v1/v2/v3
identities and OOS verdicts are immutable.

## Historical generations

- v1 — broad historical discovery and MTF evidence.
- v2 — complete quarterly-futures T2/T3 generation; all four final TRUE OOS
  studies `BORDERLINE`.
- v3 Perpetual — complete; T2/M30 `BORDERLINE`, T2/H1 `BORDERLINE`,
  T3/M30 `PASS`, T3/H1 `PASS`.

v3 TRUE OOS is consumed.

## Frozen upstream production identity

Production work originates from accepted v3 T3/H1:

- candidate `T3_H1_candidate_v3`;
- configuration `T3-H1-4e73cdb77246`;
- parameter hash
  `4e73cdb77246cb07b5953160b9fc0ab36bfd4bd6d9a7f7faaae7e6e392ee340a`;
- T3 source hash
  `840dd3b2cda43fa00259445cd0a22ace6d82e677f4c793028ccc8126f9ad9a8c`.

## Post-v3 historical evidence

Stages 1–5 are closed historical evidence. Stage 5 authoritative retrospective
economic contract remains `CORRECTED_SINGLE_C1`.

Stage 6 / 6.x produced production-design evidence, including structural
reassessments, fixed basket comparisons, broad FULL/NORMALIZED risk analysis,
and the final focused N4 four-case analysis.

The user explicitly selected TRAIL1 N4 FULL R15 from the focused N4 evidence;
that explicit human decision is the authority for Stage 7.

## Stage 7 Production Specification Freeze

Stage 7 is COMPLETE.

Production specification:
`PROD_STAGE7_46DB784378797C7FB04636892350AFF21006D71A31F2CED9D4B974EDA2DC36B8`.

Sole active production identity:
`TRAIL1__N4_01__FULL__R15`.

Frozen:

- v3 perpetual / T3 / H1;
- USDRUBF + CNYRUBF + GLDRUBF + IMOEXF;
- TRAIL1;
- FULL;
- R15 = 1.5% current realized equity risk per new position;
- maximum nominal simultaneous initial risk 6%;
- realized equity only;
- no session filter;
- one active position per instrument;
- no pyramiding;
- no canonical fallback.

`CANONICAL__N4_01__FULL__R15` remains reference only.

## Stage 8 architecture

Stage 8 is implementation/operational validation of the exact Stage 7 identity,
not a new strategy-selection phase.

Accepted foundation:

- fail-closed robot architecture;
- exact historical research-to-robot replay;
- transactional SQLite/WAL state;
- deterministic event ordering;
- immutable runtime production identity;
- DRY_RUN / DEMO / REAL_READONLY separation;
- LIVE and real order transmission explicitly blocked.

Historical conformance is 418/418 exact in both authority and production replay,
with zero recorded mismatch classes.

## FINAM production binding

All four N4 instruments are `AUTHENTICATED_REAL_READONLY`.

Binding authentication is distinct from funding capacity and live authorization.

Production-account financial authority is account-type aware:

- the active account is `UNION`;
- UNION funding authority uses `portfolio_mc`;
- FORTS accounts use `portfolio_forts` where applicable;
- unknown or mismatched shapes fail closed.

## Stage 8.8 operational hardening

Stage 8.8 operational hardening is COMPLETE.
Stages 8.8.1, 8.8.2, 8.8.3, 8.8.4, 8.8.5, 8.8.6, and 8.8.7 are COMPLETE.

Accepted capabilities include:

- REAL_READONLY supervisor and heartbeat;
- Windows CurrentUser DPAPI credential store;
- scheduled-task principal/ACL hardening;
- schedule-aware stale H1 protection;
- real Intel stale-data fault injection/recovery;
- fail-closed SQLite online backup/recovery;
- Windows WAL/handle recovery correctness;
- final physical Intel operational audit.

Final Stage 8.8.7 status:
`STAGE_8_8_7_FINAL_OPERATIONAL_AUDIT_INTEL_ACCEPTANCE_COMPLETE`.

Accepted Stage 8.8.7 code commit:
`bda46f57f0f977e05593c46b55851c40c4ad34fe`.

External Stage 8.8.7 evidence SHA-256:
`181225F29A966179AB513121C3CBACD31401752956EFC9A22253A8EFBF94766E`.

Stage 8.8 completion did not authorize live trading.

## Stage 8.9 funding / margin validation

Stage 8.9 is **COMPLETE** under canonical status
`STAGE_8_9_REAL_ACCOUNT_FUNDING_MARGIN_VALIDATION_COMPLETE`.

### Corrected account authority

Stage 8.9.8 is **COMPLETE** with status `STAGE_8_9_8_COMPLETE`.
Physical evidence confirmed the active production account is `UNION` with
exactly one `portfolio_mc`.

Portfolio variant evidence SHA-256:
`60A529DB021B39E1C6117D01CCF3AB5B8B331073D407782E90383E4D124BADC5`.

Financial shape evidence SHA-256:
`EED27193E35F46FFCF13CFB4A2F2EAA4AB87A35F967D78139E97BFA885009371`.

The earlier FORTS-only result is strictly historical provenance:
`BLOCKED_ACCOUNT_FINANCIALS_UNAVAILABLE` / `FORTS_PORTFOLIO_MISSING`, accepted
code `5deedb49f16d9f2525c430383a029017cd9a53ce`, diagnostic SHA-256
`2911D7857B9404E5178FF1A754A9168845E457A9349CEF7B1AFD0E088E06BF46`, and
summary SHA-256
`59A9ADD4BD229C7A7BF3E20337E494F90CF90082208469AD5A694A4B075D852B`.
It is not a current blocker.

### Physical revalidation

Stage 8.9.9 is **PHYSICAL REVALIDATION COMPLETE**.
Its pre-funding zero-capacity result remains strictly historical provenance:
`BLOCKED_INSUFFICIENT_CONTRACT_CAPACITY` / `ZERO_CONTRACT_CAPACITY`, accepted
code `c461911fdceddf54a2a6fe6768574dd93f4844d1`, diagnostic SHA-256
`F307D3F5ADC4525FF304B9582F683B89A097FC9BCFB502E8150FC98D2625860F`, summary
SHA-256 `F36B16565F9E08C38B3264831DCA94A65390275F7A2B78A3C6C90302E4A7C09B`, and
`positive_capacity_case_count = 0`. It is not a current blocker.

### Stage 8.9.10 post-funding closeout

Stage 8.9.10 is **COMPLETE**. The accepted physical REAL_READONLY run used code
`1013a5a2324e015ab3bc047a7b9af9064552cd10` and returned
`STAGE_8_9_10_POST_FUNDING_REVALIDATION_PASS=1`, classification
`STAGE_8_9_FUNDING_MARGIN_VALIDATED`, reason `ALL_AUTHORITIES_VALID`.

Diagnostic SHA-256:
`C87400F845B73A666B95C83DA2E3B6B710F36F3210AD4AD175BFDABB453864D5`.

Physical summary SHA-256:
`099F85A0DCCF94D404411CFFAC2F5D8C80D606C5C1B5AA2F5B650E8BF5FEB636`.

The accepted counts are `sizing_case_count = 8`,
`positive_capacity_case_count = 4`, `zero_capacity_case_count = 4`, and
`positive_batch_reservation_count = 1`. This validates funding and margin
authority and at least one executable contract-capacity case.

Completion does **not** establish positive capacity for every N4 instrument,
all-N4 or simultaneous FULL N4 portfolio capacity, or FULL/R15 production
funding sufficiency. It does not authorize trading or real execution.

## Authorization boundary

- `LIVE_TRADING_NOT_AUTHORIZED` remains in force.
- `REAL_ORDER_TRANSMISSION_NOT_AUTHORIZED` remains in force.
- `NEW_ENTRIES_DISABLED` remains in force.
- Stage 8.10 is **IN PROGRESS**; Stage 8.10.1 is complete and Stage 8.10.2 is complete and Stage 8.10.3 is the next not-started gate.
- Stage 8.11 is **NOT STARTED / NOT AUTHORIZED**.
- Stage 8.12 is **NOT STARTED / NOT AUTHORIZED**.

## Current handoff

Stage 8.9 is complete. Stage 8.10 is **IN PROGRESS** because Stage 8.10.1 and
Stage 8.10.2 are complete. Stage 8.10.3 is the next **NOT STARTED** gate and
requires separate explicit authorization.

## Domain boundaries

Do not mix TradingSystemLab with BBW, Level Touch, Round Level / Touch or other
projects.

## Persistent-memory read order

1. `CURRENT_STATE.md`
2. `PROJECT_CONTEXT.md`
3. `METHODOLOGY.md`
4. `ROADMAP.md`
5. `AUDIT_PROTOCOL.md`

## Stage 8.10 — trading-token lifecycle

Stage 8.9 is **COMPLETE** under
`STAGE_8_9_REAL_ACCOUNT_FUNDING_MARGIN_VALIDATION_COMPLETE`. Its accepted code,
diagnostic SHA-256, physical-summary SHA-256, capacity counts, classification,
and reason recorded above remain unchanged.

Stage 8.10 is **IN PROGRESS**. This lifecycle state records completion of the
preconditions and secure-provisioning gates; it does not complete Stage 8.10 and
does not authorize Token 1 use, FINAM authentication, or execution.

Canonical Stage 8.10 sequence and status:

1. Stage 8.10.1 is **COMPLETE** — Trading Token Preconditions Gate.
   Canonical status: `STAGE_8_10_1_TRADING_TOKEN_PRECONDITIONS_COMPLETE`.
2. Stage 8.10.2 is **COMPLETE** — Secure Provisioning.
3. Stage 8.10.3 is **NOT STARTED** — Identity / Account Binding.
4. Stage 8.10.4 is **NOT STARTED** — Permission Boundary Validation.
5. Stage 8.10.5 is **NOT STARTED** — Order Path Dry Validation.
6. Stage 8.10.6 is **NOT STARTED** — Kill Switch / Safety Gates.
7. Stage 8.10.7 is **NOT STARTED** — Intel Trading-Token Acceptance.
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
in Windows CurrentUser DPAPI. Token 1 has not been used and FINAM trading
authentication has not been performed. Stage 8.10 order_count remains exactly 0;
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
Disabled. Stage 8.10 is **IN PROGRESS**; Stage 8.10.3 through Stage 8.10.8 are
**NOT STARTED**. Stage 8.11 is **NOT STARTED / NOT AUTHORIZED** and Stage 8.12 is
**NOT STARTED / NOT AUTHORIZED**. `LIVE_TRADING_NOT_AUTHORIZED`,
`REAL_ORDER_TRANSMISSION_NOT_AUTHORIZED`, and `NEW_ENTRIES_DISABLED` remain in
force.
