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

Physical Intel 24/7 restart/network/recovery acceptance remains pending.

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

PR #296 merged.

Latest merge:
`4d8807d5b97f660bd4558e7a35660567829a51f6`.

Status:
`STAGE_8_8_5_STALE_DATA_PROTECTION_CODE_READY_PENDING_INTEL_VALIDATION`.

Freshness uses actual FINAM schedules. Stale completed H1 data raises
`STALE_COMPLETED_H1_DATA`, records `FAULT` / `UNHEALTHY`, does not advance
successful cycle state, and leaves entries disabled. Closed schedules/weekends/
gaps do not create synthetic expectations.

Repository audit: PASS.

## Current operational gate

**NEXT: real Intel Stage 8.8.x operational validation under REAL_READONLY with
entries disabled.**

Required acceptance work includes:

- reboot/restart behavior;
- network failure and recovery;
- stale-data fault injection and recovery;
- heartbeat/state continuity;
- instance locking;
- no-order-call confirmation.

This operational validation must not enable real order transmission.

## Later Stage 8 gates

- Stage 8.9 funding readiness — **BLOCKED** by unavailable authenticated account
  financials (`portfolio_forts`).
- Stage 8.10 trading-token integration — **PENDING / NOT AUTHORIZED**.
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

Stage 7 is frozen. Stage 8 code is ready through 8.8.5.

**Proceed only with real Intel operational validation in REAL_READONLY. LIVE
remains blocked.**
