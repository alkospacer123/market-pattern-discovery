# Canonical research and evidence methodology

This file defines durable rules for TradingSystemLab. It records accepted
methodological boundaries and must not be used to rewrite historical evidence.

## 1. Canonical research lifecycle

The sole research-methodology authority remains:

**Baseline → Optimization → Robustness → Walk Forward → TRUE OOS**.

Candidate freeze is identity fixation between Optimization and Robustness, not a
sixth phase. v1, v2 and v3 are separate historical research generations.

## 2. Research identity and OOS discipline

A research identity binds strategy source/hash, parameters/hash, universe,
timeframe/context alignment, date bounds, execution/cost assumptions and
classification rules.

After candidate freeze, identity is immutable through Robustness, Walk Forward
and TRUE OOS. Once TRUE OOS is revealed, it is consumed for that identity.
Post-OOS rule discovery is retrospective and cannot be relabeled as fresh OOS.

## 3. Causality and determinism

- Candle information is unavailable before close.
- Context/higher-timeframe data must use fully completed source bars.
- No future fill or look-ahead.
- Ordering, trade IDs, serialization and reruns must be deterministic.
- Market data remains external/read-only unless explicitly authorized otherwise.

## 4. Historical v3 completion

v3 Perpetual completed the full five-stage lifecycle. Final TRUE OOS:

- T2/M30 `BORDERLINE`;
- T2/H1 `BORDERLINE`;
- T3/M30 `PASS`;
- T3/H1 `PASS`.

These classifications remain immutable.

## 5. Post-v3 evidence-to-production program

Post-v3 work is separate from the five-stage research lifecycle. It may analyze
revealed evidence and build production-design candidates, but it may not
retroactively rewrite v1/v2/v3.

Stages 1–5 established consolidated evidence, diversification diagnostics, trade
anatomy, a frozen structural-hypothesis set, and separate structural validation.

Stage 5 final economic authority is `CORRECTED_SINGLE_C1`.

## 6. Stage 5 structural-validation semantics

Final Stage 5 labels:

- BE1 — `MIXED_RETROSPECTIVE_EVIDENCE`;
- TRAIL1 — `SUPPORTED_RETROSPECTIVELY`;
- Total Open Risk Cap — `FORMAL_RESEARCH_VERDICT_NOT_ASSIGNED` because terminal
  right-censoring prevents complete final economic certification;
- Minimum Hold — `NOT_ADMITTED / DIAGNOSTIC ONLY`;
- Session/Time of Day — `NOT_ADMITTED / DIAGNOSTIC ONLY` at Stage 5;
- Correlation/Simultaneous Risk — `NOT_ADMITTED / DIAGNOSTIC ONLY`.

Stage 5 diagnostics are not permission to cherry-pick historical buckets.

## 7. Original Stage 6 decision semantics

Stage 6 initially selected `PROD_STAGE6_83C7B31BB42C`: v3 perpetual / T3 / H1
/ CNYRUBF + GLDRUBF + IMOEXF / TRAIL1.

This is an accepted historical production-decision checkpoint, not a final
production specification. Subsequent Stage 6.x reassessments supersede its
direct Stage 7 handoff.

## 8. Pre-Stage-7 reassessment methodology

After Stage 6, additional work was explicitly run as **retrospective
pre-Stage-7 reassessment**, not as a new OOS lifecycle.

Rules:

- revealed 2025–2026 evidence remains retrospective;
- no result may be described as fresh OOS;
- no broad optimizer or unrestricted parameter search;
- each tested rule must have an explicit causal state machine;
- rejected rules remain rejected; admitted rules do not automatically become
  production-approved;
- basket comparisons must use a frozen basket registry;
- later equity/risk loading analysis must not alter underlying R-space trade
  evidence.

## 9. Stage 6.1–6.5 structural rule results

Accepted retrospective decisions:

- `SESSION_10_21_ADMIT_TO_STRUCTURAL_STACK`;
- `ONE_BAR_CONFIRMATION_REJECTED_FULL_REMAINS_BENCHMARK`;
- `OPPOSITE_REGIME_EXIT_NO_MATERIAL_DIFFERENCE`;
- `LOCK1_AFTER_2R_ADMIT_TO_STRUCTURAL_STACK`;
- `STRUCTURAL_STACK_V1_ADMITTED`.

`STRUCTURAL_STACK_V1 = SESSION_10_21 + LOCK1_AFTER_2R`.

SESSION_10_21 restricts new entries only to 10:00 inclusive–21:00 exclusive
Europe/Moscow. LOCK1_AFTER_2R is the frozen causal +2R trigger / +1R lock rule.

ONE_BAR confirmation and opposite-regime exit are not part of the structural
stack. TRAIL1 and BE1 are separate historical overlays and are not components
of `STRUCTURAL_STACK_V1`.

## 10. Stage 6.6 comparison discipline

Stage 6.6 compared only five authenticated variants across eleven fixed baskets
(55 configurations): CANONICAL, TRAIL1, SESSION_10_21, LOCK1_AFTER_2R and
STRUCTURAL_STACK_V1.

The frozen equal-sleeve hierarchy placed:

- `STRUCTURAL_STACK_V1__N2_01` first;
- `SESSION_10_21__N2_01` second;
- `N2_01 = USDRUBF + CNYRUBF`.

This ranking is evidence within the frozen candidate set. It is not permission
to launch a new subset search or optimizer.

## 11. Stage 6.7 loading, equity and eligibility discipline

Stage 6.7 evaluated the frozen 55 configurations under FULL/NORMALIZED loading
and frozen risk scenarios, producing 110 R cases and 220 equity cases.

Production eligibility requires the frozen portfolio/instrument-year gates. It
must fail closed; eligibility may not be relaxed merely to reach a return target.

Final Stage 6.7 facts:

- 16 production-eligible equity cases;
- 4 unique eligible configurations;
- eligible N2/N3/N4 = 16/0/0;
- all eligible configurations use `N2_01 = USDRUBF + CNYRUBF`;
- no eligible case reaches 70% historical CAGR;
- highest eligible historical CAGR = 60.19%;
- final classification:
  `NO_CURRENT_CONFIGURATION_MEETS_FULL_PRODUCTION_OBJECTIVE`.

Reference stability/risk ordering and maximum CAGR are different concepts:

- frozen reference leader: `CANONICAL__N2_01__NORMALIZED__R15`;
- highest eligible CAGR case:
  `STRUCTURAL_STACK_V1__N2_01__FULL__R20`.

Do not collapse these into a single invented 'winner'.

## 12. Current production boundary

Stage 7 is not executed and no production specification is frozen.

Stage 6.8 is not started. Because the strict 70–80% objective is unmet, no
automatic next-stage transition is permitted.

Do not:

- relax eligibility gates or return targets automatically;
- promote N3/N4 configurations when Stage 6.7 found none production-eligible;
- treat Stage 6.6 hierarchy output as a final live specification;
- start robot/FINAM integration;
- create a new production identity without explicit authorization.

Any continuation after Stage 6.7 requires a new explicit user-authorized task.

## 13. Cost and risk semantics

`FROZEN_TICK_SIZE = 0.001` remains historical research normalization where
applicable. `CORRECTED_SINGLE_C1` remains the authoritative retrospective
economic contract for Stage 5–6.x evidence.

Stage 6.7 risk/load scenarios are production-design diagnostics, not the final
broker cost model or live sizing specification.

## 14. Domain separation

TradingSystemLab is separate from BBW, Level Touch, Round Level / Touch and
other research domains.

## 15. Evidence standard

Reports summarize evidence; they do not replace manifests, ledgers, metrics,
source provenance, deterministic reruns or independent audits. Follow
`AUDIT_PROTOCOL.md`.

Update this file only when the governing process changes or stale methodological
language needs correction. Routine progress belongs primarily in
`CURRENT_STATE.md` and `ROADMAP.md`.
