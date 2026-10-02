# Evidence-based roadmap

## Governing research rule

The original H1 lifecycle remains the sole research methodology:

**Baseline → Optimization → Robustness → Walk Forward → TRUE OOS**.

v1/v2/v3 are historical and immutable. The active roadmap is production
specification + robot/FINAM integration.

## Historical research generations

- v1 — historical discovery/MTF evidence.
- v2 — complete; four final TRUE OOS study classifications `BORDERLINE`.
- v3 Perpetual — complete; T2/M30 `BORDERLINE`, T2/H1 `BORDERLINE`,
  T3/M30 `PASS`, T3/H1 `PASS`.

## Post-v3 Stages 1–5

All CLOSED:

1. Master evidence consolidation.
2. Portfolio/diversification comparison.
3. Trade Anatomy / Failure Analysis.
4. Structural hypothesis freeze.
5. Structural validation.

Stage 5 economic authority: `CORRECTED_SINGLE_C1`.

## Stage 6 / 6.x — production decision history

**CLOSED as historical evidence.**

Important checkpoints:

- original Stage 6 assembly: `PROD_STAGE6_83C7B31BB42C`;
- Stage 6.1 SESSION_10_21 admitted to Structural Stack;
- Stage 6.2 ONE_BAR rejected;
- Stage 6.3 opposite-regime exit not admitted;
- Stage 6.4 LOCK1_AFTER_2R admitted;
- Stage 6.5 `STRUCTURAL_STACK_V1` admitted;
- Stage 6.6 fixed 55-configuration comparison;
- Stage 6.7 broad FULL/NORMALIZED stability/risk audit;
- focused Stage 6.7 N4 FULL four-case clean-room audit.

The broad Stage 6.7 gate conclusion remains historical:
`NO_CURRENT_CONFIGURATION_MEETS_FULL_PRODUCTION_OBJECTIVE`.

The later focused N4 comparison did not auto-select a winner. It provided the
fixed evidence set from which the user explicitly chose TRAIL1 N4 FULL R15.

## Stage 7 — Production Specification Freeze

**COMPLETE.**

Merge: `32cf5d530e77a673d9f5eafd0b17bea7996c820b`.

Frozen production specification:

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

`CANONICAL__N4_01__FULL__R15` is stable reference only.

## Stage 8 — Robot / FINAM integration

**ACTIVE. LIVE TRADING NOT AUTHORIZED.**

### Stage 8 foundation

Completed / merged:

- PR #274 — fail-closed Stage 8 robot foundation;
- PR #275 — FINAM demo-safe perpetual integration foundation;
- PR #276 — FINAM REST schema correction + frozen H1 replay;
- PR #277 — exact research-to-robot conformance restoration;
- PR #278 — strict FINAM demo instrument binding;
- PR #279 — FINAM REST binding schema correction.

Historical conformance now passes exactly:

- authority replay 418/418;
- production robot replay 418/418;
- deterministic hashes;
- zero recorded reconciliation mismatches.

### REAL_READONLY / margin / deployment preparation

Completed / merged:

- PR #280 — real read-only + margin-aware FULL/R15 + Intel deployment prep;
- PR #281 — FINAM real-account schema and registry activation support;
- PR #282–#283 — Windows compatibility and fixture normalization;
- PR #284 — session-details REST authentication fix;
- PR #285–#288 — catalog binding diagnostics, cursor recovery, terminal cursor
  parsing, and futures lot-size semantics;
- PR #289 — activate REAL_READONLY N4 registry;
- PR #290 — operational runbook correction.

Current registry: **4/4 N4 instruments `AUTHENTICATED_REAL_READONLY`**.

No real order was transmitted.

Funding readiness remains fail-closed because the validated clean UNION account
did not expose required `portfolio_forts` financials.

### Stage 8.8.1 — operational supervisor

PR #291 merged.

Status:
`STAGE_8_8_1_REAL_READONLY_SUPERVISOR_CODE_READY`.

Supervisor is read-only, entries disabled, single-instance, heartbeat/reconcile
aware, and cannot transmit real orders.

Physical Intel operational acceptance is complete. It covered supervisor
startup and `--once`, continuous operation, restart, second-instance exclusion,
reboot, and network/API failure through `UNHEALTHY` / `FAULT` and recovery to
`HEALTHY` / `PASS`. Recovery reset the consecutive-failure counter, and no
order-capable call was made.

### Stage 8.8.4 — Windows DPAPI credential bootstrap

Completed / hardened through PR #292–#295.

Implemented:

- CurrentUser DPAPI credential store;
- production-ID binding;
- matched scheduled-task principal;
- real Windows DPAPI execution tests;
- explicit System.Security loading;
- SID/ACL hardening.

Secrets remain outside Git and output.

### Stage 8.8.5 — schedule-aware stale H1 protection

Status:
`STAGE_8_8_5_STALE_DATA_PROTECTION_COMPLETE`.

Freshness uses instrument-specific FINAM schedules, whole-hour UTC raw opens,
merged touching trading windows, a partial final-bar completion boundary, and
the persisted exact expected watermark. Stale completed H1 data raises
`STALE_COMPLETED_H1_DATA`, records `FAULT` / `UNHEALTHY`, does not advance
successful cycle state, and leaves entries disabled. Closed schedules/weekends/
gaps do not create synthetic expectations.

Repository audit: PASS. Real Intel stale-data fault injection and deterministic
recovery: PASS. The real Intel stale-data acceptance was executed against
audited source Git head `1c1c2bb5458827f200bc753e7e64db0272b33a8f`.
PR #302 subsequently performed the Stage 8.8.5 repository closeout; its
GitHub-visible head was `635bea24710cc41f0cb65eef9c6ed576494f5396`, and its
merge commit was `b19a3625698f4701b7c531cade5a27a497269b73`. PR #302 did
not modify `stage8_robot/readonly_supervisor.py`, `stage8_robot/finam_api.py`,
or `stage8_robot/tests/test_readonly_supervisor.py`, so the accepted H1
implementation remained byte-identical. The external artifact SHA-256 is
`C57554AE3AE54018EC1E558108520088C1883718F0406E7B6C6669B4696A9CBC`.
The clean and recovered states were `HEALTHY` / `PASS`; the controlled
`STALE_COMPLETED_H1_DATA` state was `UNHEALTHY` / `FAULT` and did not advance
cycle, H1, or expected-H1 state. Recovery reset consecutive failures to 0.
Order-capable calls were 0, entries stayed disabled, and the Scheduled Task
stayed Disabled. Runtime JSON and real market responses remain outside Git.

## Current operational gate

Stage 8.8.6 repository status:
`STAGE_8_8_6_SQLITE_RECOVERY_INTEL_ACCEPTANCE_COMPLETE`.

The canonical REAL_READONLY database now has fail-closed online backup,
production-ID/checksum manifests, paired retention, strict schema validation,
lifetime-lock exclusion, and atomic recovery with stale WAL/SHM removal.

Physical Intel backup, exact restore, and normal REAL_READONLY reconciliation
acceptance completed against audited commit
`dc2b79e74817e71435eee20103ae617e13067d8e`. The external evidence remains
outside Git and is identified by SHA-256
`1A9B62D4BFC0E7384898C9DF9659E54E50E0E202BD44CE19413864AC2ECA14D6`.
This completion does not enable real order transmission.

The accepted backup SHA-256 is
`00b5e4ca2b389d55389b6b57ac73b5e557c11b72daab8d6e118311613e0aa3b0`, its
manifest SHA-256 is
`3d0ef1d7cb11ee592be32550625e8badefc596108f4d0c34eff6c5e12ceba822`, and the
baseline logical-state SHA-256 is
`13f01f1009768ddce65dce079f70486f2cbc2508cd1ea8ec4787414a78e0d3be`.

### Stage 8.8.7 — Final Operational Audit

Status: `STAGE_8_8_7_FINAL_OPERATIONAL_AUDIT_INTEL_ACCEPTANCE_COMPLETE`.

Stage 8.8 operational hardening is COMPLETE. Stages 8.8.1, 8.8.2, 8.8.3,
8.8.4, 8.8.5, 8.8.6, and 8.8.7 are COMPLETE.

Physical Intel acceptance executed against exact GitHub merge
`bda46f57f0f977e05593c46b55851c40c4ad34fe`. The external acceptance artifact
remains outside Git and is referenced only by SHA-256
`181225F29A966179AB513121C3CBACD31401752956EFC9A22253A8EFBF94766E`.
The accepted Windows gate passed 267 Stage 8 tests, 43 final operational checks,
132 Stage 8 checks, and 22 Stage 7 checks plus 19 mutation tests. One
`REAL_READONLY --once` cycle advanced cycle count 20 to 21 and all N4 H1
watermarks monotonically from 12:00 to 13:00 UTC with expected-H1 equality.
Final state was `HEALTHY` / `PASS`, entries disabled, zero unresolved orders,
and zero failures. The Scheduled Task remained Disabled, process and recovery
internal file counts were zero, and secret/account environment variables were
absent. No live order was transmitted and no authorization changed. Repository
tooling validates the provenance and hash; it did not generate the evidence.

Stage 8.9 is CURRENT. Repository status is
`BLOCKED_ACCOUNT_FINANCIALS_UNAVAILABLE`.
Physical REAL_READONLY validation was performed on accepted Intel code commit
`5deedb49f16d9f2525c430383a029017cd9a53ce`. Its classification is
`BLOCKED_ACCOUNT_FINANCIALS_UNAVAILABLE`, reason `FORTS_PORTFOLIO_MISSING`.
The external diagnostic report SHA-256 is
`2911D7857B9404E5178FF1A754A9168845E457A9349CEF7B1AFD0E088E06BF46`; the
external physical summary SHA-256 is
`59A9ADD4BD229C7A7BF3E20337E494F90CF90082208469AD5A694A4B075D852B`.
Both external JSON files remain outside Git. `stage8_9_physical_validation_performed = true`;
Stage 8.9 is CURRENT / BLOCKED / NOT COMPLETE.

## Later Stage 8 gates

- Stage 8.9 — **CURRENT / BLOCKED / NOT COMPLETE**. Physical validation was performed and returned `BLOCKED_ACCOUNT_FINANCIALS_UNAVAILABLE` because `portfolio_forts` was absent; this is not reinterpreted as zero and is not claimed resolved.
- Stage 8.10 trading-token integration — **NOT STARTED / NOT AUTHORIZED**.
- Stage 8.11/8.12 execution — **NOT AUTHORIZED**.

Do not bypass these gates.

## Persistent constraints

- no live trading without explicit separate authorization;
- no runtime change to frozen Stage 7 identity;
- no canonical fallback;
- no fabricated funding/margin/equity;
- no reinterpretation of REAL_READONLY success as trading authorization;
- no mixing with BBW / Level Touch / Round Level projects;
- no rewrite of historical v1/v2/v3 verdicts.

## Current handoff

Stage 7 is frozen. Stage 8.8 operational hardening is COMPLETE. Stages 8.8.1, 8.8.2, 8.8.3,
8.8.4, 8.8.5, 8.8.6, and 8.8.7 are COMPLETE.
Status: `STAGE_8_8_7_FINAL_OPERATIONAL_AUDIT_INTEL_ACCEPTANCE_COMPLETE`.

**CURRENT: Stage 8.9 — Real Account Funding & Margin Validation.** Physical
validation was performed. `BLOCKED_ACCOUNT_FINANCIALS_UNAVAILABLE` remains in force because
`portfolio_forts` was unavailable. LIVE and real-order transmission remain not
authorized.
## Stage 8.9 physical validation closeout

Repository diagnostic readiness is retained. Physical REAL_READONLY validation was performed on accepted Intel code commit `5deedb49f16d9f2525c430383a029017cd9a53ce`. `stage8_9_physical_validation_performed = true`. The result is `BLOCKED_ACCOUNT_FINANCIALS_UNAVAILABLE`, reason `FORTS_PORTFOLIO_MISSING`. Diagnostic report SHA-256: `2911D7857B9404E5178FF1A754A9168845E457A9349CEF7B1AFD0E088E06BF46`. Physical validation summary SHA-256: `59A9ADD4BD229C7A7BF3E20337E494F90CF90082208469AD5A694A4B075D852B`. The external JSON evidence remains outside Git. The authenticated account was a clean, active `UNION` account using a read-only token, and its exact frozen N4 binding was valid. `portfolio_forts` was absent, so funding/margin feasibility remained `BLOCKED`; absence is not zero and no other field is a fallback. The no-order-call assertion was true. The Scheduled Task stayed Disabled; supervisor process and recovery internal file counts stayed zero; FINAM secret and account ID were removed from the process environment. The accepted physical run recorded Stage 8 repository audit PASS / 141 checks, Final Operational Audit PASS / 45 checks, Stage 7 production audit PASS / 22 checks / 19 mutation tests, and server preflight PASS. No physical order-capable operation occurred. Stage 8.9 is **CURRENT / BLOCKED / NOT COMPLETE**. Stage 8.10 is **NOT STARTED / NOT AUTHORIZED**. LIVE trading and real-order transmission remain unauthorized.


## Stage 8.9.8 UNION/MC authority resolution

Status: `STAGE_8_9_UNION_MC_AUTHORITY_CODE_READY_PENDING_PHYSICAL_REVALIDATION`.
Stage 8.9.8 account-authority resolution is complete: the production account is
`UNION`, and funded physical evidence confirmed exactly one `portfolio_mc`. The
FORTS-only implementation was incorrect for this account. The post-funding MC
portfolio-variant evidence SHA-256 is
`60A529DB021B39E1C6117D01CCF3AB5B8B331073D407782E90383E4D124BADC5`; the
post-funding account financial-shape evidence SHA-256 is
`EED27193E35F46FFCF13CFB4A2F2EAA4AB87A35F967D78139E97BFA885009371`.
Only these sanitized hashes are committed; the external JSON, account identity,
and financial values remain outside Git. Corrective code is ready only after
this PR passes. **Stage 8.9.9 physical revalidation is still required.** Stage
8.9 remains **NOT COMPLETE**. Stage 8.10 remains **NOT STARTED / NOT
AUTHORIZED**. `LIVE_TRADING_NOT_AUTHORIZED`,
`REAL_ORDER_TRANSMISSION_NOT_AUTHORIZED`, and `NEW_ENTRIES_DISABLED` remain
unchanged. No live order was transmitted and no live trading was authorized.

The earlier physical result `BLOCKED_ACCOUNT_FINANCIALS_UNAVAILABLE` /
`FORTS_PORTFOLIO_MISSING`, accepted Intel commit
`5deedb49f16d9f2525c430383a029017cd9a53ce`, diagnostic SHA-256
`2911D7857B9404E5178FF1A754A9168845E457A9349CEF7B1AFD0E088E06BF46`, and
physical-summary SHA-256
`59A9ADD4BD229C7A7BF3E20337E494F90CF90082208469AD5A694A4B075D852B` remain
historical evidence of the old implementation and are not reinterpreted.
