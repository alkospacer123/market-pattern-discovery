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

- **Current v2 single-system cycle:** Phase 1 Baseline, Phase 2 Optimization,
  Phase 3 Candidate Freeze, Phase 3 Robustness, Phase 4 Walk Forward, and Phase
  5 TRUE OOS are complete as procedures. Phase 4 is `PHASE_4_BORDERLINE`
  (canonical merge `0b0027665fdcc0f847b6b9a10cb5928fcfd2d553`); Phase 5
  independently classifies T2/M30, T2/H1, T3/M30, and T3/H1 `BORDERLINE`.
  The Phase 5 canonical merge is `2d7cd61b8d4d399901ebce397d1c2b7111ae427c`.
  The cycle stops at evidence: no portfolio, MTF, cost branch, or replacement.

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

## Current v2 single-system cycle

**COMPLETE as a procedure across all five stages.** Phase 1 Baseline, Phase 2
Optimization, Phase 3 Candidate Selection / Freeze, Phase 3 Robustness, Phase
4 Walk Forward, and Phase 5 TRUE OOS are complete.

The final Phase 5 classifications are:

- T2/M30 `BORDERLINE`
- T2/H1 `BORDERLINE`
- T3/M30 `BORDERLINE`
- T3/H1 `BORDERLINE`

The canonical Phase 5 merge is
`2d7cd61b8d4d399901ebce397d1c2b7111ae427c`. No automatic next research phase
is authorized. The lifecycle must **STOP** here until a new user decision is
made. Do not automatically add a portfolio phase, MTF, cost recalculation, new
optimization, or session research.

## v3 Perpetual independent generation

- Phase 1 Baseline: **COMPLETE**.
- Phase 2A T2: **COMPLETE**; M30/H1 `ROBUST_PLATEAU` counts are 3/4.
- Phase 2B T3: **COMPLETE**; M30/H1 `ROBUST_PLATEAU` counts are 9/9.
- Phase 2 overall: `V3_PERPETUAL_PHASE_2_OPTIMIZATION_COMPLETE`; 82 bounded
  OAT configurations and 25 robust-plateau configurations were independently
  consolidated without rerunning Optimization.
- Candidate Freeze: **COMPLETE**. T2/M30 `T2_M30_candidate_v3`, T2/H1
  `T2_H1_candidate_v3`, T3/M30 `T3_M30_candidate_v3`, and T3/H1
  `T3_H1_candidate_v3` are immutable.
- Phase 3 Robustness: **COMPLETE** (`V3_PERPETUAL_PHASE_3_ROBUSTNESS_COMPLETE`).
  T2/M30, T2/H1, T3/M30, and T3/H1 each classify `ROBUST_READY`; this is not a
  ranking or candidate replacement.
- Phase 4 Walk Forward: **COMPLETE**
  (`V3_PERPETUAL_PHASE_4_WALK_FORWARD_COMPLETE`). All studies have four valid
  folds. T2/M30, T2/H1, and T3/M30 are `WALK_FORWARD_BORDERLINE`; T3/H1 is
  `WALK_FORWARD_PASS`.
- Historical pre-Phase-5 checkpoint — TRUE OOS >= 2025-01-01: `BLOCKED_NOT_READ_NOT_EXECUTED`; Phase 5 was not
  executed.
- Next permitted action: Phase 5 TRUE OOS only after a separate explicit task.

## v3 perpetual lifecycle — COMPLETE

The prescribed five-stage v3 lifecycle is **complete as a procedure**. Phase 1
Baseline, Phase 2 Optimization, Candidate Freeze, Phase 3 Robustness, Phase 4
Walk Forward, and Phase 5 TRUE OOS are COMPLETE. Fixed-order Phase 5 results are
T2/M30 `BORDERLINE`, T2/H1 `BORDERLINE`, T3/M30 `PASS`, and T3/H1 `PASS`.
No ranking or winner selection was performed, no portfolio phase is created,
and no additional lifecycle phase is authorized by this closeout.
