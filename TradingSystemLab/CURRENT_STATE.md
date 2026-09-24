# Current state — read first

> Persistent handoff snapshot after the independently audited TradingSystemLab
> v2 Phase 3 candidate freeze. Canonical provenance anchors are Phase 1 merge
> `2aae07a3d12907d1869eb603e6ac1a6fb8d851dd`, T2 Phase 2A merge
> `a252f076a09495d3093854c8509b1551701ba2b4`, and T3 Phase 2B merge
> `f8f28834db4bc016a995b55aed1ff7fd53a4a0e8`.

## Governing rule

The original H1 cycle and frozen H1 strategy identities remain the sole
methodological authority: **Baseline → Optimization → Robustness → Walk Forward
→ TRUE OOS**. No stage may be skipped, borrowed from another timeframe, or
replaced by later timeframe/MTF work. Calendar year 2025+ remains locked TRUE
OOS until its preauthorized stage.

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
- The consolidation did not rerun Optimization and makes no claim of a second
  byte-identical Phase 2A/2B execution.

## Identity and scope safeguards

The canonical Baseline retains T2 `max_initial_stop_atr = 3.0` and T3
`ema_period = 100`; historical post-Optimization H1 candidate values 2.5 and 75
must not be confused with Baseline defaults. T3 M30/H1 uses separate causal
context made from complete, non-overlapping four-execution-bar blocks reset at
local trading-day boundaries. T2 remains standalone. The current five-stage
cycle retains `FROZEN_TICK_SIZE = 0.001` for every instrument.

## Next roadmap stage

**Phase 3 Robustness execution** is the next permitted action. It must consume
exactly `results/phase3_candidate_freeze/candidate_registry.json`. No Robustness
has yet been executed, and TRUE OOS 2025+ remains sealed.

## Forbidden next actions

- Do not modify or replace a frozen candidate after observing Robustness. The
  parameters are immutable for Phase 3; any change requires returning to an
  earlier research stage under a new identity.
- Do not execute Walk Forward, TRUE OOS, portfolio selection, or Phase 7 MTF
  research out of sequence.
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
explicit absence of one, scope, costs, TRUE OOS seal, next permitted action,
and forbidden actions.
