# Evidence-based roadmap

## Governing rule for future work

The original H1 research cycle and frozen H1 strategy identities are the sole
methodological authority. Every newly researched timeframe must independently
pass **Baseline → Optimization → Robustness → Walk Forward → TRUE OOS**. No
stage may be added, skipped, or supplied by another timeframe. Later timeframe
and MTF implementations are historical evidence only, not alternative
templates. The current cycle retains `FROZEN_TICK_SIZE = 0.001` for every
instrument through all five stages; instrument-specific recalculation requires
a separate, explicitly authorized post-cycle audit branch.

## Completed

- **Original H1:** committed unified Baseline (Phase 2), bounded Optimization
  (Phase 3.2), Robustness (Phase 3.3), Walk Forward (Phase 4), diagnostics
  (Phase 4.1), TRUE OOS (Phase 5), and portfolio construction (Phase 6).
  Completion records artifact production; the verdicts below still govern.
- **M5, M15, M30:** committed artifacts record Baseline, Optimization,
  Robustness, Walk Forward, and TRUE OOS. These are historical implementations,
  not templates for future work.
- **H4:** Baseline completed. Optimization separately classified T2 and T3
  `ROBUST_PLATEAU`; Robustness separately classified both `BORDERLINE`; Walk
  Forward separately completed `PHASE_H4_WALK_FORWARD_BORDERLINE`; TRUE OOS
  separately classified both `FAIL`.
- **D1:** Baseline completed and Optimization completed. The Optimization report
  classifies both T2 and T3 `LOCAL_SPIKE` and explicitly says Robustness, Walk
  Forward, and TRUE OOS were not performed. No later D1 lifecycle stage is
  marked complete.
- **M1:** its committed manifest records Baseline completion. No complete
  Optimization → Robustness → Walk Forward → TRUE OOS bundle is inferred.
- Phase 7.1 MTF research, Phase 7.2 artifact-only registry, and Phase 7.3 true-
  MTF research have committed completion manifests. They remain independent
  historical branches.

## Completed but borderline/inconclusive

- Original Phase 4 is `PHASE_4_BORDERLINE`; T3 is
  `WALK_FORWARD_BORDERLINE`, with later `MIXED_EVIDENCE` diagnostics. Phase 4.1
  classifies T2 and T3 `SAMPLE_LIMITED`.
- H4 Robustness is `BORDERLINE` for each strategy and H4 Walk Forward is
  borderline. These do not replace H4 Optimization's separate
  `ROBUST_PLATEAU` classifications. H4 TRUE OOS records T2/T3 `FAIL`.
- Later TRUE OOS outcomes remain candidate-specific: M30 records T2
  `BORDERLINE` / T3 `PASS`; M15 records T2 `FAIL` / T3 `PASS`.
- Historical v2 Phase 1 generated all 24 runs but its audit verdict is **FAIL /
  NOT COMPLETE**. Its instrument-spec and provenance findings remain historical
  evidence, not the controlling roadmap.

## Current

**Corrected Baseline: approved to execute, not yet executed or audited.** It
returns to the original H1 Baseline methodology and frozen T2/T3 strategy
identities (T2 baseline default 3.0; T3 baseline default 100), rather than the
historical v2 2.5/75 override identity. This documentation correction is not a
research phase.

## Planned

1. Execute the corrected Baseline with `FROZEN_TICK_SIZE = 0.001` and audit its
   actual code, manifests, ledgers, metrics, grouped outputs, determinism, and
   verdict evidence.
2. Only after Baseline audit acceptance, perform the original-H1-template
   Optimization; then independently audit it.
3. Only after each predecessor is accepted, continue in order through
   Robustness, Walk Forward, and the single preauthorized TRUE OOS stage.

Per-instrument tick-size work is deferred. If later authorized, it is a separate
audit/recalculation branch and cannot silently modify this cycle or historical
results.
