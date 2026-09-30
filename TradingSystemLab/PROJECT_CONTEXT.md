# TradingSystemLab project context

## Purpose and authority

TradingSystemLab is the repository's deterministic, fixed-risk systematic
trading research and production-design domain. The repository, not chat history,
is the authoritative project memory. Read `CURRENT_STATE.md` first.

## Canonical research lifecycle

The sole research-methodology authority remains the original H1 lifecycle:

**Baseline → Optimization → Robustness → Walk Forward → TRUE OOS**.

Candidate freeze is procedural identity fixation, not an additional research
phase. Historical v1/v2/v3 identities and verdicts are immutable.

## Research generations

### v1

Broad historical strategy/timeframe discovery, including T1–T3, R1–R3,
multiple timeframes and later MTF work.

### v2

Quarterly-futures T2/T3 diversification generation on M30/H1 across
`Si`, `CNY`, `GD`, `BR`, `MIX`, `NG`. Its five-stage lifecycle is complete;
all four final TRUE OOS study classifications are `BORDERLINE`. OOS is consumed.

### v3 Perpetual

Universe: `USDRUBF`, `CNYRUBF`, `GLDRUBF`, `IMOEXF`; strategies T2/T3;
timeframes M30/H1. v3 completed the full five-stage lifecycle.

Final TRUE OOS:

- T2/M30 `BORDERLINE`;
- T2/H1 `BORDERLINE`;
- T3/M30 `PASS`;
- T3/H1 `PASS`.

v3 TRUE OOS is consumed.

## Frozen v3 upstream identity

The production-design work originates from the accepted v3 T3/H1 identity:

- candidate: `T3_H1_candidate_v3`;
- configuration: `T3-H1-4e73cdb77246`;
- parameter hash:
  `4e73cdb77246cb07b5953160b9fc0ab36bfd4bd6d9a7f7faaae7e6e392ee340a`;
- T3 source hash:
  `840dd3b2cda43fa00259445cd0a22ace6d82e677f4c793028ccc8126f9ad9a8c`.

Historical identities must not be modified by later production diagnostics.

## Post-v3 program

The post-v3 evidence-to-production program is separate from the five-stage
research lifecycle. Stages 1–5 are CLOSED:

1. Master v1/v2/v3 evidence consolidation;
2. Portfolio/diversification comparison;
3. Trade Anatomy / Failure Analysis;
4. Structural hypothesis freeze;
5. Separate structural validation.

Stage 5 final economic authority is `CORRECTED_SINGLE_C1` over the authenticated
9,694-trade comparator.

Final Stage 5 labels:

- BE1 — `MIXED_RETROSPECTIVE_EVIDENCE`;
- TRAIL1 — `SUPPORTED_RETROSPECTIVELY`;
- Total Open Risk Cap — `FORMAL_RESEARCH_VERDICT_NOT_ASSIGNED` because of
  terminal right-censoring;
- Minimum Hold — `NOT_ADMITTED / DIAGNOSTIC ONLY`;
- Session/Time of Day — `NOT_ADMITTED / DIAGNOSTIC ONLY` at Stage 5;
- Correlation/Simultaneous Risk — `NOT_ADMITTED / DIAGNOSTIC ONLY`.

## Original Stage 6 checkpoint

Stage 6 initially selected:

`PROD_STAGE6_83C7B31BB42C` = v3 perpetual / T3 / H1 /
`CNYRUBF + GLDRUBF + IMOEXF` / TRAIL1.

This remains historical evidence, but subsequent pre-Stage-7 work means it is
no longer sufficient by itself as the current handoff to Stage 7.

## Pre-Stage-7 Stage 6 extension

After the original Stage 6 decision, the project explicitly continued with a
retrospective reassessment branch. This did not create fresh OOS and did not
execute Stage 7.

### Audit and fixed-basket reassessment

- IMOEXF contribution/stability/cost semantics were audited in PR #251–#254.
- A fixed A–F basket reassessment in PR #255–#256 preferred basket C
  (`USDRUBF+CNYRUBF+GLDRUBF+IMOEXF`, canonical) under that frozen hierarchy
  and concluded `NEW_PRODUCTION_IDENTITY_REQUIRED_BEFORE_STAGE7`.

### Structural reassessments

- Stage 6.1: `SESSION_10_21_ADMIT_TO_STRUCTURAL_STACK`.
- Stage 6.2: `ONE_BAR_CONFIRMATION_REJECTED_FULL_REMAINS_BENCHMARK`.
- Stage 6.3: `OPPOSITE_REGIME_EXIT_NO_MATERIAL_DIFFERENCE`.
- Stage 6.4: `LOCK1_AFTER_2R_ADMIT_TO_STRUCTURAL_STACK`.
- Stage 6.5: `STRUCTURAL_STACK_V1_ADMITTED`.

`STRUCTURAL_STACK_V1 = SESSION_10_21 + LOCK1_AFTER_2R`.

SESSION_10_21 is entry-only, 10:00 inclusive to 21:00 exclusive
Europe/Moscow. LOCK1_AFTER_2R locks +1R only after a surviving +2R completed
event under its frozen causal rule. ONE_BAR and opposite-regime exit were not
admitted to the stack. TRAIL1 and BE1 are not part of `STRUCTURAL_STACK_V1`.

All Stage 6.1–6.5 evidence is retrospective because 2025–2026 had already been
revealed.

### Stage 6.6 unified comparison

Five authenticated variants were compared across eleven fixed baskets:

- CANONICAL;
- TRAIL1;
- SESSION_10_21;
- LOCK1_AFTER_2R;
- STRUCTURAL_STACK_V1.

Total: **55 configurations**.

Frozen equal-sleeve hierarchy result:

- winner: `STRUCTURAL_STACK_V1__N2_01`;
- runner-up: `SESSION_10_21__N2_01`;
- `N2_01 = USDRUBF + CNYRUBF`.

This was a comparison of existing candidates, not authorization for new basket
search or parameter optimization.

### Stage 6.7 FULL vs NORMALIZED stability/risk closeout

Stage 6.7 converted the frozen Stage 6.6 comparison into explicit R-load/equity
risk cases and independently audited availability, continuous equity, exposure
ordering, month/quarter completeness, eligibility and determinism.

Final authenticated universe:

- 55 configurations;
- 110 R cases;
- 220 equity cases;
- 16 production-eligible equity cases;
- 4 unique eligible configurations;
- eligible N2/N3/N4: **16 / 0 / 0**.

All production-eligible configurations are based on
`N2_01 = USDRUBF + CNYRUBF`.

Stage 6.7 reference leader under its frozen stability/risk ordering:
`CANONICAL__N2_01__NORMALIZED__R15`.

Highest eligible historical CAGR:
**60.19%** for `STRUCTURAL_STACK_V1__N2_01__FULL__R20`.

However, **no production-eligible case reaches the desired 70–80% historical
CAGR**. Final conclusion:

`NO_CURRENT_CONFIGURATION_MEETS_FULL_PRODUCTION_OBJECTIVE`.

The strict gate was not relaxed. `NO_PRODUCTION_ELIGIBLE_N4`.
Stage 6.7 independent audit passed.

## Current project boundary

The prior Stage 7-ready statement is superseded.

Current state:

- no production specification is frozen;
- Stage 7 is not executed;
- Stage 6.8 is not started;
- no current configuration satisfies the full 70–80% production objective
  while retaining strict Stage 6.7 eligibility;
- no gate/target is to be relaxed automatically.

Any continuation requires a new explicit user-authorized task.

## Economic and risk semantics

`FROZEN_TICK_SIZE = 0.001` remains historical research normalization where
applicable. `CORRECTED_SINGLE_C1` remains the authoritative retrospective
economic contract for the post-v3 evidence used in Stage 5–6.x.

Stage 6.7 load/risk scenarios are production-design diagnostics, not a final
live production cost model or broker specification.

## Domain boundaries

Do not mix TradingSystemLab with BBW, Level Touch, Round Level / Touch
Optimization, or other projects.

## Persistent-memory read order

1. `CURRENT_STATE.md`
2. `PROJECT_CONTEXT.md`
3. `METHODOLOGY.md`
4. `ROADMAP.md`
5. `AUDIT_PROTOCOL.md`

Update these files only after accepted repository work and actual artifact audit.
