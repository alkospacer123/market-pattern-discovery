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

**Phase 1 Baseline: COMPLETE. Phase 2 Optimization: COMPLETE. Phase 3 Candidate
Selection / Freeze: COMPLETE. Phase 3 Robustness: COMPLETE.** The accepted
Phase 2 universe contains four independent Development studies and 82 bounded
Baseline + OAT configurations. T2/M30, T2/H1, T3/M30, and T3/H1 each classify
as `ROBUST_PLATEAU`; the stable-region inventory is descriptive and unranked.
TRUE OOS 2025+ remains sealed. Frozen candidates are T2/M30
`T2_M30_candidate_v2`, T2/H1 `T2_H1_candidate_v2`, T3/M30
`T3_M30_candidate_v2`, and T3/H1 `T3_H1_candidate_v2`. Their parameters are
immutable for Phase 3. Robustness classified T2/M30 `ROBUST_READY`, T2/H1
`BORDERLINE`, T3/M30 `ROBUST_READY`, and T3/H1 `ROBUST_READY`; the T2/H1
candidate remains frozen and records `INSTRUMENT_DEPENDENT`. The candidate
freeze is anchored at `ff0db54b35544086f4265c303b1018d57d3849e7`. TRUE OOS
2025+ remains sealed.

## Planned

1. Execute **Phase 4 Walk Forward** for the same four frozen identities. The
   Phase 3 classifications are evidence, not authorization for post-hoc pruning
   or replacement.
2. Only after Walk Forward is accepted may the single preauthorized TRUE OOS
   stage proceed.

Per-instrument tick-size work remains deferred. If later authorized, it is a
separate audit/recalculation branch and cannot silently modify this cycle or
historical results.
