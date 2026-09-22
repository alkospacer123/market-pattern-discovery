# Evidence-based roadmap

This roadmap follows committed artifacts, not the mere presence of runners.
It also records the conflict between the older repository-root `ROADMAP.md` and
the newer v2 audit rather than guessing that one provenance line replaced the
other.

## Completed

- Original lifecycle artifacts: unified baseline (Phase 2), bounded optimization
  (Phase 3.2), robustness validation (Phase 3.3), Phase 4 walk-forward execution,
  Phase 4.1 diagnostics, Phase 5 TRUE OOS, and Phase 6 portfolio construction.
  “Completed” here means the phase produced a committed completion artifact; its
  individual classifications still apply.
- Phase 7.1 multi-timeframe research and Phase 7.2 artifact-only candidate
  analysis/registry.  The registry retains all combinations and performs no
  ranking or selection.
- Phase 7.3 true-MTF research: its `results/mtf_research/manifest.json` records
  `PHASE_7_3_TRUE_MTF_RESEARCH_COMPLETE`.
- Committed later-timeframe baseline/optimization/robustness/walk-forward/TRUE
  OOS bundles exist for the timeframes identified by their manifests, including
  M1, M5, M15, M30, H4, and D1 branches.  Completion does not imply a pass.
- TradingSystemLab v2 Phase 0 smoke test passed, and the v2 Phase 1 24-run matrix
  was generated reproducibly.  Its audit acceptance is listed below.

## Completed but borderline/inconclusive

- Original Phase 4 is recorded as `PHASE_4_BORDERLINE`; T3's dedicated
  walk-forward verdict is `WALK_FORWARD_BORDERLINE`, with diagnostic
  classification `MIXED_EVIDENCE`.
- Phase 4.1 diagnostics classify both T2 and T3 as `SAMPLE_LIMITED`.
- H4 robustness classifies both T2 and T3 `BORDERLINE`; H4 walk-forward also has
  a borderline completion status.
- Timeframe TRUE OOS results are mixed and must remain candidate-specific: M30
  records T2 `BORDERLINE` and T3 `PASS`; M15 records T2 `FAIL` and T3 `PASS`.
- **v2 Phase 1 baseline is audit-failed / not complete.** Although its generator
  and manifests say `PHASE_1_BASELINE_COMPLETE`, `Baseline_Audit_Report.md`
  finds missing per-instrument specification integration, missing `source_hash`
  and `instrument_spec` fields, and failing protected-tree tests.  Numerical
  consistency of the generated ledgers does not override that verdict.

## Current

**TradingSystemLab v2 Phase 1.1 baseline remediation, blocked pending verified
instrument specifications; this change itself is infrastructure/documentation.**
The source-state commit is `f336303` on branch `work`.  No research operation is
authorized by this documentation task.

The root roadmap says “Current: Phase 7.3,” but the Phase 7.3 manifest already
records completion.  Later commits introduced and audited the v2 Phase 1 matrix;
the audit's explicit `NOT COMPLETE` verdict is the newest research-state evidence
at HEAD and therefore controls this handoff.

## Planned

Only the remediation prescribed by the committed v2 audit is currently
supported:

1. Obtain verified contract specifications for all six v2 instruments.
2. Add missing GD/BR/MIX/NG specifications and matrix-level integration tests;
   remove the v2 baseline's global tick-size assumption in favor of each run's
   verified spec.
3. Record `instrument_spec` and `source_hash` in every run manifest (and resolve
   the documented slippage-field naming issue).
4. Resolve the pre-existing protected-tree hash failure, rerun exactly the frozen
   24-run C1 development-only matrix without changing T2/T3 parameters or logic,
   then repeat the full artifact audit.

Optimization, ranking, selection, strategy modification, or TRUE OOS access is
not the next planned work.
