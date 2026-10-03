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

Stage 8.9 is CURRENT and NOT COMPLETE.

### Corrected account authority

Stage 8.9.8 is `STAGE_8_9_8_COMPLETE`.

Physical evidence confirmed the active production account is `UNION` with
exactly one `portfolio_mc`. The earlier FORTS-only implementation is historical
and no longer the current authority.

Portfolio variant evidence SHA-256:
`60A529DB021B39E1C6117D01CCF3AB5B8B331073D407782E90383E4D124BADC5`.

Financial shape evidence SHA-256:
`EED27193E35F46FFCF13CFB4A2F2EAA4AB87A35F967D78139E97BFA885009371`.

### Physical revalidation

Stage 8.9.9 is PHYSICAL REVALIDATION COMPLETE.

Accepted code commit:
`c461911fdceddf54a2a6fe6768574dd93f4844d1`.

Diagnostic SHA-256:
`F307D3F5ADC4525FF304B9582F683B89A097FC9BCFB502E8150FC98D2625860F`.

Physical summary SHA-256:
`F36B16565F9E08C38B3264831DCA94A65390275F7A2B78A3C6C90302E4A7C09B`.

The corrected run authenticated financial schema, equity, directional margins,
instrument binding, arithmetic and batch-budget behavior, but
`positive_capacity_case_count = 0`.

### Current Stage 8.9.10 blocker

Current status:
`BLOCKED_INSUFFICIENT_CONTRACT_CAPACITY`.

Reason:
`ZERO_CONTRACT_CAPACITY`.

This is the only active Stage 8.9 blocker. Stage 8.9 must not be described as
funding-ready or complete.

## Authorization boundary

- LIVE trading is not authorized.
- REAL order transmission is not authorized.
- Stage 8.10 trading-token integration is not started / not authorized.
- Stage 8.11/8.12 execution is not authorized.

Do not weaken Stage 7 risk to manufacture positive capacity, fabricate financial
values, or reinterpret REAL_READONLY acceptance as live authorization.

## Current handoff

Stop at Stage 8.9.10 while `ZERO_CONTRACT_CAPACITY` remains.

Any resolution path requires an explicit user-authorized task and an independent
audit before advancing.

## Domain boundaries

Do not mix TradingSystemLab with BBW, Level Touch, Round Level / Touch or other
projects.

## Persistent-memory read order

1. `CURRENT_STATE.md`
2. `PROJECT_CONTEXT.md`
3. `METHODOLOGY.md`
4. `ROADMAP.md`
5. `AUDIT_PROTOCOL.md`
