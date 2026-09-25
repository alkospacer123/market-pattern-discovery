# Current state — read first

## v3 Perpetual current handoff

The independent `v3_perpetual` generation has completed Phase 1 Baseline
(`V3_PERPETUAL_PHASE_1_BASELINE_COMPLETE`) and Phase 2 Optimization
(`V3_PERPETUAL_PHASE_2_OPTIMIZATION_COMPLETE`). Phase 2 classified T2/M30 as
`ROBUST_PLATEAU` (3 configurations), T2/H1 as `ROBUST_PLATEAU` (4), T3/M30 as
`ROBUST_PLATEAU` (9), and T3/H1 as `ROBUST_PLATEAU` (9): 25 robust-plateau
configurations across 82 total bounded OAT configurations. Consolidation did
not rerun Optimization, rank the configurations, declare a winner, or select a
candidate.

The canonical Phase 1 merge is `f8ee11841eedb11cb6ec98debc74ad8bc8c0c8a9`,
and its independently hardened audit closeout is
`a9c9815a9865a2c20fa555292de2c9924aadca96`. That audit passes all 16 ledgers
(1,124 trades), eight source data files, report reconciliations, and
causal-context checks. The Phase 2A T2 and Phase 2B T3 provenance anchors are
`7559953fd3dda8582af17f747ee38d94a93c42ad` and
`3b3cb3046f3f68c602d6d65f715d23090ab4a17c`; the canonical Phase 2
consolidation merge is `272eabd5a4261a18a763356964b82b4b5b5673ea`.

The artifact-only v3 Candidate Freeze is **COMPLETE**. Frozen identities are
T2/M30 `T2_M30_candidate_v3` / `T2-M30-608dc87d09f1`, T2/H1
`T2_H1_candidate_v3` / `T2-H1-608dc87d09f1`, T3/M30
`T3_M30_candidate_v3` / `T3-M30-d6feb972db57`, and T3/H1
`T3_H1_candidate_v3` / `T3-H1-4e73cdb77246`. Phase 3 Robustness is **COMPLETE**
(`V3_PERPETUAL_PHASE_3_ROBUSTNESS_COMPLETE`): all four frozen studies classify
`ROBUST_READY`. Phase 4 Walk Forward is **COMPLETE** as a procedure
(`V3_PERPETUAL_PHASE_4_WALK_FORWARD_COMPLETE`): T2/M30, T2/H1, and T3/M30
classify `WALK_FORWARD_BORDERLINE`; T3/H1 classifies `WALK_FORWARD_PASS`. Each
study has four valid expanding-window quarterly folds. TRUE OOS >= 2025-01-01
remains `BLOCKED_NOT_READ_NOT_EXECUTED`; Phase 5 had not yet been executed at that checkpoint. The next
permitted action is Phase 5 TRUE OOS only after a separate explicit task.

> Persistent handoff snapshot after the independently audited TradingSystemLab
> v2 Phase 5 TRUE OOS execution. Canonical provenance anchors are Phase 1 merge
> `2aae07a3d12907d1869eb603e6ac1a6fb8d851dd`, T2 Phase 2A merge
> `a252f076a09495d3093854c8509b1551701ba2b4`, and T3 Phase 2B merge
> `f8f28834db4bc016a995b55aed1ff7fd53a4a0e8`. The canonical Phase 5 merge is
> `2d7cd61b8d4d399901ebce397d1c2b7111ae427c`.

## Governing rule

The original H1 cycle and frozen H1 strategy identities remain the sole
methodological authority: **Baseline → Optimization → Robustness → Walk Forward
→ TRUE OOS**. No stage may be skipped, borrowed from another timeframe, or
replaced by later timeframe/MTF work. Calendar year 2025+ was opened only at
its preauthorized Phase 5 stage.

## Accepted current cycle

- **Phase 1 Baseline: COMPLETE.** The accepted Development matrix is T2/T3 ×
  Si/CNY/GD/BR/MIX/NG × M30/H1, with 24 runs over the declared 2020-01-01
  through 2024-12-31 interval, C1 only, and normalized research tick `0.001`.
- **Phase 2 Optimization: COMPLETE.** The artifact-only consolidation audit
  independently verified the complete 82-configuration bounded Baseline + OAT
  design, exact parameter spaces and hashes, Phase 1 Baseline reconciliation,
  C1-only calculations, six-instrument diagnostics, causal T3 context, TRUE OOS
  exclusion, immediate neighbors, and all plateau classifications.
- Scoped Phase 2 results are T2/M30 `ROBUST_PLATEAU` (3 configurations), T2/H1
  `ROBUST_PLATEAU` (4), T3/M30 `ROBUST_PLATEAU` (9), and T3/H1
  `ROBUST_PLATEAU` (9). These counts are a descriptive stable-region inventory,
  not a ranking.
- **Phase 3 Candidate Selection / Freeze: COMPLETE.** Exactly one predeclared
  candidate is immutable for each study: T2/M30 → `T2_M30_candidate_v2`, T2/H1
  → `T2_H1_candidate_v2`, T3/M30 → `T3_M30_candidate_v2`, and T3/H1 →
  `T3_H1_candidate_v2`. Historical H1 candidates were provenance only.
- **Phase 3 Robustness: COMPLETE.** The original H1 Phase 3.3 methodology,
  adapted only to the frozen v2 C1-only contract, classified T2/M30
  `ROBUST_READY`, T2/H1 `BORDERLINE`, T3/M30 `ROBUST_READY`, and T3/H1
  `ROBUST_READY`. T2/H1 retained its frozen identity and records
  `INSTRUMENT_DEPENDENT`; it was not replaced.
- The canonical candidate-freeze merge anchor is
  `ff0db54b35544086f4265c303b1018d57d3849e7`.
- The canonical Phase 3 Robustness merge anchor is
  `d89d0f1f7ba3259e0f08e43a0832bd16f4d15f6b`.
- **Phase 4 Walk Forward: COMPLETE as a procedure.** All four immutable
  candidates were executed independently on four expanding-window quarterly
  tests in 2024, C1 only. T2/M30, T2/H1, T3/M30, and T3/H1 each received
  `WALK_FORWARD_BORDERLINE`; no candidate was pruned or replaced.
- The canonical Phase 4 merge anchor is
  `0b0027665fdcc0f847b6b9a10cb5928fcfd2d553`.
- **Phase 5 TRUE OOS: COMPLETE as a procedure.** All four frozen identities
  started cold and FLAT on admitted 2025+ observations. T2/M30, T2/H1,
  T3/M30, and T3/H1 each classified `BORDERLINE`. No candidate was replaced,
  optimized, or ranked after TRUE OOS was opened.
- The canonical Phase 5 procedural status is
  `PHASE_5_TRUE_OOS_VALIDATION_COMPLETE`.
- The consolidation did not rerun Optimization and makes no claim of a second
  byte-identical Phase 2A/2B execution.

## Identity and scope safeguards

The canonical Baseline retains T2 `max_initial_stop_atr = 3.0` and T3
`ema_period = 100`; historical post-Optimization H1 candidate values 2.5 and 75
must not be confused with Baseline defaults. T3 M30/H1 uses separate causal
context made from complete, non-overlapping four-execution-bar blocks reset at
local trading-day boundaries. T2 remains standalone. The current five-stage
cycle retains `FROZEN_TICK_SIZE = 0.001` for every instrument.

## Completed current cycle

- Phase 1 Baseline — **COMPLETE**
- Phase 2 Optimization — **COMPLETE**
- Phase 3 Candidate Selection / Freeze — **COMPLETE**
- Phase 3 Robustness — **COMPLETE**
- Phase 4 Walk Forward — **COMPLETE as a procedure** / root `PHASE_4_BORDERLINE`
- Phase 5 TRUE OOS — **COMPLETE as a procedure**

The Phase 5 classifications are T2/M30 → `BORDERLINE`, T2/H1 → `BORDERLINE`,
T3/M30 → `BORDERLINE`, and T3/H1 → `BORDERLINE`.

TRUE OOS 2025+ was opened once in the authorized Phase 5 cold-start evaluation
and must not be reused to retune or reselect these same frozen identities. The
five-stage single-system cycle is complete. No next phase is automatically
authorized.

## Forbidden next actions

- Do not modify or replace a frozen candidate after observing Robustness. The
  parameters are immutable for Phase 3; any change requires returning to an
  earlier research stage under a new identity.
- Do not reuse consumed TRUE OOS, select a portfolio, or begin MTF research
  without a new user decision.
- Do not access 2025+ data during candidate selection, optimize or rank by PF,
  change the frozen strategies, replace the normalized research tick, or rewrite
  the accepted Phase 1/2 artifact trees.

## Historical evidence

Older failed, borderline, TRUE OOS, MTF, and alternative-timeframe artifacts
remain immutable evidence of their own generations. They do not control or
substitute for this accepted v2 lifecycle.

## Update rule

Update this file after every accepted research phase or major audit. Record the
canonical commits, current and last-completed stages, candidate identity or the
explicit absence of one, scope, costs, TRUE OOS consumption state, next
permitted action, and forbidden actions.

## v3 Perpetual independent generation

v1 and v2 remain immutable historical evidence. For `v3_perpetual`, Phase 1,
Phase 2A T2, Phase 2B T3, Phase 2 Optimization overall, and the procedural
Candidate Freeze are **COMPLETE**.
The artifact-only independent consolidation status is
`V3_PERPETUAL_PHASE_2_OPTIMIZATION_COMPLETE`: T2/M30 is `ROBUST_PLATEAU`
(3 configurations), T2/H1 is `ROBUST_PLATEAU` (4), T3/M30 is
`ROBUST_PLATEAU` (9), and T3/H1 is `ROBUST_PLATEAU` (9), for 25 total.
No Optimization was rerun and this inventory is not a ranking.

Frozen candidates are T2/M30 `T2_M30_candidate_v3`, T2/H1
`T2_H1_candidate_v3`, T3/M30 `T3_M30_candidate_v3`, and T3/H1
`T3_H1_candidate_v3`. At that historical checkpoint, TRUE OOS >= 2025-01-01 was
`BLOCKED_NOT_READ_NOT_EXECUTED`. Robustness is **NOT EXECUTED**; the next
permitted action is v3 Phase 3 Robustness. Candidate replacement or a second
selection is forbidden.

## v3 perpetual lifecycle closeout — Phase 5 TRUE OOS

The v3 perpetual five-stage lifecycle is **complete as a procedure**: Phase 1
Baseline, Phase 2 Optimization, Candidate Freeze, Phase 3 Robustness, Phase 4
Walk Forward, and Phase 5 TRUE OOS are COMPLETE. The audited one-shot outcomes
in fixed lifecycle order are T2/M30 `BORDERLINE`, T2/H1 `BORDERLINE`, T3/M30
`PASS`, and T3/H1 `PASS`. Every evaluation began cold and `FLAT`, admitted zero
Development rows, and used frozen candidates, parameters, strategy code, and C1.
No optimization, ranking, replacement, recommendation, or portfolio phase was
performed. Status: `V3_PERPETUAL_PHASE_5_TRUE_OOS_COMPLETE`.
