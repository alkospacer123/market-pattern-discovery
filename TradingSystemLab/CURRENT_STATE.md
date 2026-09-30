# Current state — read first

## Active handoff — Stage 7 complete

- Stage 6 is **CLOSED**.
- Stage 7 Production Specification Freeze is **COMPLETE**:
  `TRAIL1__N4_01__FULL__R15` is the sole `ACTIVE_PRODUCTION_SPECIFICATION`.
- Immutable ID: `PROD_STAGE7_46DB784378797C7FB04636892350AFF21006D71A31F2CED9D4B974EDA2DC36B8`.
- `CANONICAL__N4_01__FULL__R15` is
  `STABLE_REFERENCE_NOT_ACTIVE_PRODUCTION`, never an automatic fallback.
- Stage 8 Robot / FINAM API is next but **NOT STARTED**; no implementation has begun.

Older statements below that Stage 7 is unexecuted are retained as historical
evidence and superseded by this explicit user-authorized freeze.

## Authoritative handoff

The active TradingSystemLab work remains the **post-v3 production program**.
The v3 five-stage research lifecycle is complete and immutable historical
evidence. Post-v3 Stages 1–5 are CLOSED. Stage 6 Production Assembly was
completed, but its direct Stage 7 handoff was subsequently subjected to a
pre-Stage-7 reassessment branch, now complete through **Stage 6.7**.

Current repository state:

- `main`: `8c57fc740aacd784b3cf82b02e2614d463330199`;
- Stage 6.7 final audit-close merge: `8c57fc740aacd784b3cf82b02e2614d463330199`;
- Stage 7 has **NOT** been executed;
- Stage 6.8 has **NOT** been started.

## v3 Perpetual lifecycle — CLOSED

Universe: `USDRUBF`, `CNYRUBF`, `GLDRUBF`, `IMOEXF`; strategies T2/T3;
timeframes M30/H1. Governing lifecycle:

**Baseline → Optimization → Robustness → Walk Forward → TRUE OOS**.

Final v3 TRUE OOS classifications:

- T2/M30 — `BORDERLINE`;
- T2/H1 — `BORDERLINE`;
- T3/M30 — `PASS`;
- T3/H1 — `PASS`.

v3 TRUE OOS is consumed and cannot be reused as untouched OOS for a modified
identity.

## Post-v3 Stages 1–5 — CLOSED

- Stage 1 — Master v1/v2/v3 evidence consolidation: CLOSED.
- Stage 2 — Portfolio/diversification comparison: CLOSED.
- Stage 3 — Trade Anatomy / Failure Analysis: CLOSED.
- Stage 4 — Structural hypothesis set: CLOSED.
- Stage 5 — Structural validation: CLOSED under `CORRECTED_SINGLE_C1`.

Stage 5 final component states remain:

- BE1 — `MIXED_RETROSPECTIVE_EVIDENCE`;
- TRAIL1 — `SUPPORTED_RETROSPECTIVELY`;
- Total Open Risk Cap — `FORMAL_RESEARCH_VERDICT_NOT_ASSIGNED` because of
  terminal right-censoring;
- Minimum Hold — `NOT_ADMITTED / DIAGNOSTIC ONLY`;
- Session / Time of Day — `NOT_ADMITTED / DIAGNOSTIC ONLY` at Stage 5;
- Correlation / Simultaneous Risk — `NOT_ADMITTED / DIAGNOSTIC ONLY`.

## Stage 6 original production decision — historical checkpoint

Stage 6 initially selected production assembly:

**`PROD_STAGE6_83C7B31BB42C`** = v3 perpetual / T3 / H1 /
`CNYRUBF + GLDRUBF + IMOEXF` / TRAIL1 / `CORRECTED_SINGLE_C1`.

That decision remains immutable historical evidence, but it is **not** a
frozen production specification and must no longer be treated as the current
direct Stage 7 handoff without the later Stage 6.1–6.7 reassessment evidence.

## Pre-Stage-7 reassessment branch — COMPLETE through Stage 6.7

### Stage 6 audit extension / fixed-basket reassessment

- PR #251–#254 audited IMOEXF marginal contribution, decision semantics,
  cost/stability evidence, and the original TRAIL1 assembly.
- PR #255–#256 compared a frozen six-basket A–F set. Basket C
  (`USDRUBF+CNYRUBF+GLDRUBF+IMOEXF`, canonical) was preferred under that
  frozen hierarchy; final status was `NEW_PRODUCTION_IDENTITY_REQUIRED_BEFORE_STAGE7`.

### Stage 6.1 — Session 10:00–21:00 causal reassessment

- Merge: `65d79271806a434c13973c274dad11c27eb3a973`.
- Decision: `SESSION_10_21_ADMIT_TO_STRUCTURAL_STACK`.
- Rule applies to **new entries only**, 10:00 inclusive to 21:00 exclusive
  Europe/Moscow; exits/stops/context remain unrestricted.
- Evidence is retrospective; no fresh OOS validation was created.

### Stage 6.2 — ONE_BAR_BREAKOUT_CONFIRMATION

- Merge: `df69c016b3f3e46deb31f57a797d640ea5c850c0`.
- Decision: `ONE_BAR_CONFIRMATION_REJECTED_FULL_REMAINS_BENCHMARK`.
- Not admitted to the later structural stack.

### Stage 6.3 — EXIT_ON_OPPOSITE_REGIME

- Merge: `a7745798f65cc9a514eb01aad3ae6804017e699e`.
- Decision: `OPPOSITE_REGIME_EXIT_NO_MATERIAL_DIFFERENCE`.
- Not admitted.

### Stage 6.4 — LOCK1_AFTER_2R

- Merge: `59a3bd6869fde3d14d15c2fd1f0bf521cbe2ab18`.
- Decision: `LOCK1_AFTER_2R_ADMIT_TO_STRUCTURAL_STACK`.
- Retrospective evidence only; Stage 7 remained unexecuted.

### Stage 6.5 — STRUCTURAL_STACK_V1

- Main implementation merge: `7f616d366e206c3aa04fe52719b8e4641ceceb18`;
  hardened reproducibility close: `27b31703054574682c38384ddf1e33a2a7097652`.
- Definition: `SESSION_10_21 + LOCK1_AFTER_2R`.
- Decision: `STRUCTURAL_STACK_V1_ADMITTED`.
- ONE_BAR, opposite-regime exit, TRAIL1 and BE1 are not part of this stack.

### Stage 6.6 — Unified existing-candidate comparison

- Authoritative TRAIL1 ledger materialized: `1bf22b559c12f6244dd4087de176d5f684a1025e`.
- Comparison close: `47a63c34d1288a076ff5e7e3f803bc77aff5302b`.
- Population: 5 authenticated variants × 11 fixed baskets = **55 configurations**.
- Variants: CANONICAL, TRAIL1, SESSION_10_21, LOCK1_AFTER_2R,
  STRUCTURAL_STACK_V1.
- Winner under the frozen equal-sleeve hierarchy:
  `STRUCTURAL_STACK_V1__N2_01`.
- Runner-up: `SESSION_10_21__N2_01`.
- `N2_01` = `USDRUBF + CNYRUBF`.
- Stage 7 was not executed.

### Stage 6.7 — FULL vs NORMALIZED stability/risk audit

- Initial implementation merge: `890097ee0e92687356a1ce3d3292abf0c26795eb`;
  continuous-equity correction: `a2f02a01323babf4d18cdcbc623b92c016390d64`;
  final audit close: `8c57fc740aacd784b3cf82b02e2614d463330199`.
- Universe: **55 configurations / 110 R cases / 220 equity cases**.
- Production-eligible equity cases: **16**; unique eligible configurations: **4**.
- Eligible N2/N3/N4 cases: **16 / 0 / 0**.
- All eligible configurations are on basket `N2_01 = USDRUBF + CNYRUBF`.
- Frozen stability/risk reference leader:
  `CANONICAL__N2_01__NORMALIZED__R15`.
- Highest eligible historical CAGR: **60.19%**
  (`STRUCTURAL_STACK_V1__N2_01__FULL__R20`).
- No production-eligible case reaches the desired **70–80% historical CAGR**.
- Final conclusion:
  `NO_CURRENT_CONFIGURATION_MEETS_FULL_PRODUCTION_OBJECTIVE`.
- Strict eligibility/return gate was **not relaxed**.
- `NO_PRODUCTION_ELIGIBLE_N4`.
- Stage 6.7 final status: `STAGE_6_7_AUDIT_CLOSED`; independent audit PASS.

## Current boundary

The previous statement “Stage 7 is NEXT for `PROD_STAGE6_83C7B31BB42C`” is
superseded by the completed Stage 6.1–6.7 reassessment evidence.

Current facts:

- there is **no frozen production specification**;
- there is **no current configuration meeting the full 70–80% production
  objective under the strict Stage 6.7 gates**;
- Stage 7 is **NOT EXECUTED**;
- Stage 6.8 is **NOT STARTED**;
- no gate, target, or eligibility rule may be relaxed automatically.

Any continuation beyond Stage 6.7 requires a new explicit user-authorized task.
Until then, do not create Stage 7, Stage 6.8, robot implementation, FINAM API
integration, or a new production identity automatically.

## Governing constraints

- Do not mix TradingSystemLab with BBW, Level Touch, Round Level / Touch, or
  other projects.
- Do not rewrite v1/v2/v3 historical identities or OOS classifications.
- Treat all Stage 6.1–6.7 2025–2026 evidence as revealed/retrospective, not
  fresh OOS.
- Do not infer that an admitted structural variant is production-approved.
- Do not reinterpret Stage 6.6 or Stage 6.7 ranking tables as permission to
  search new baskets or tune rules.
- Do not promote N3/N4 configurations: Stage 6.7 found no production-eligible
  N3 or N4 equity cases.
- Do not relax the 70–80% objective or strict production-eligibility gates
  without explicit user authorization.

## Update rule

Update this file after every accepted task or major audit. The first sections
must describe the latest active handoff; older Stage 6 checkpoints must remain
clearly historical.
