# Canonical research methodology

This is a reconstruction of the lifecycle encoded by the runners and committed
phase artifacts.  It does not redesign that lifecycle.  Every phase is causal,
development/OOS separated, cost-aware, deterministic, and provenance-bound.

## Canonical methodology authority

> **All future TradingSystemLab timeframe research uses only the original H1
> cycle and frozen H1 strategy identities as its methodological template.**

The mandatory sequence is **Baseline → Optimization → Robustness → Walk Forward
→ TRUE OOS**.  Each new timeframe must reproduce each corresponding original
H1 stage as closely as applicable and pass it independently.  No extra
qualification stage may be inserted, and another timeframe cannot supply or
waive a stage.  Later timeframe and MTF implementations are historical
provenance only: they may be audited, but may not redesign the cycle.  New
optimization, ranking, candidate-generation logic, or methodological gates
require explicit authorization as a separate future research project.

The current cycle also freezes `FROZEN_TICK_SIZE = 0.001` for all instruments
through all five stages.  Per-instrument tick-size investigation is deferred to
a separately authorized post-cycle audit/recalculation branch and cannot
silently revise this cycle or historical artifacts.

## Lifecycle: Baseline → Optimization → Robustness → Walk Forward → TRUE OOS

### 1. Baseline

**Purpose.** Reproduce a declared strategy/configuration on declared instruments,
timeframes, development dates, and costs, and establish an auditable reference.

**Inputs.** Frozen strategy source and parameters, external read-only candle
files, instrument/timeframe/date declarations, and a cost model.  **Permitted:**
causal indicator/signal execution and descriptive metrics.  **Prohibited:**
parameter search, ranking, selection, walk-forward inference, MTF substitution,
and all TRUE OOS reads.  **Outputs:** manifest, data-quality/provenance record,
trade ledger, metrics, and report.  Stable ordering, candle-close semantics,
repeatable identifiers, strategy/parameter hashes, source identity, and costs
are required.

The historical v2 Phase 1 implementation is a 24-run C1-only matrix.  Its generated
manifests say complete, but the subsequent audit verdict is **NOT COMPLETE**
because per-instrument execution specs and required manifest provenance are
missing.  Generated status is therefore not the same as audit acceptance.
Its T2 2.5 / T3 75 overrides are not the original baseline defaults (3.0 / 100)
and do not define the corrected Baseline identity.

### 2. Optimization

**Purpose.** Test a predeclared, bounded parameter space on development data and
describe stable regions.  **Inputs:** an accepted baseline, frozen search space,
constraints, deterministic experiment definition, and development-only data.
**Permitted:** only the encoded bounded grid/experiments and development metrics.
**Prohibited:** TRUE OOS access, unrecorded expansion, favorable-subset selection,
and ad-hoc PF chasing.  **Outputs:** experiment/manifest, complete parameter
table, best-region/plateau reports, and validation report.

The original H1 Phase 3.2 classifies the recorded surfaces as
`ROBUST_PLATEAU`, `LOCAL_SPIKE`, or `NO_EDGE`; classification is not permission
to hide other trials.  Later timeframe modules have their own manifests and
spaces.  Their provenance must remain separate rather than being harmonized
after the fact.

### 3. Robustness

**Purpose.** Challenge a frozen baseline/candidate against the predeclared
parameter neighborhood, costs, instruments, directions, years, concentration,
and relevant execution assumptions.  **Inputs:** immutable upstream artifacts
and ledgers plus declared gates.  **Permitted:** diagnostic grouping, prescribed
sensitivity tests, and classification.  **Prohibited:** tuning from robustness
results or discarding unfavorable slices.  **Outputs:** cost and sensitivity
tables, grouped reports, ledgers where reruns occur, manifest, and a verdict.

Implemented labels differ by phase: original validation records include
`ROBUST_READY`; timeframe work uses classifications such as `ROBUST`,
`BORDERLINE`, and failure flags.  The exact rules in that phase's code and
manifest govern; labels must not be translated silently between generations.

### 4. Walk Forward

**Purpose.** Measure chronological forward behavior without random splitting.
**Inputs:** a robustness-eligible frozen candidate, predeclared folds, costs,
and development-era data only.  **Permitted:** train diagnostics and evaluation
on each subsequent forward fold.  **Prohibited:** changing parameters from a
forward fold, selecting favorable folds, or accessing TRUE OOS.  **Outputs:**
fold definition, fold ledgers/metrics, stitched forward ledger, grouped results,
concentration/decay diagnostics, manifest, and verdict.

The original Phase 4 summary is `PHASE_4_BORDERLINE`; T3's dedicated artifact is
`WALK_FORWARD_BORDERLINE`, and subsequent diagnostics classify its evidence as
`MIXED_EVIDENCE`.  Later timeframe workflows use their own predeclared gates and
can emit pass, borderline, or fail independently.  A diagnostic does not alter
the frozen strategy or retroactively select it.

### Candidate freeze point

The candidate identity—strategy code/hash, parameters/hash, instruments,
timeframe/alignment, data bounds, execution assumptions, cost model, and
classification rules—must be frozen **after development evaluation and before
any TRUE OOS access**.  Candidate manifests/registries are provenance records,
not rankings.  A TRUE OOS outcome cannot trigger retuning under the same identity.

### 5. TRUE OOS

**Purpose.** Perform the single preauthorized pass/fail (or predeclared
classification) evaluation on locked calendar year 2025.  **Inputs:** a frozen,
eligible candidate and its complete provenance.  **Permitted:** execution and
the predeclared reports/classification.  **Prohibited:** discovery, optimization,
ranking, selection, parameter/logic changes, repeated probing, and feedback into
the candidate.  **Outputs:** run manifest, immutable ledger, metrics, grouped
reports, and classification.

Original Phase 5 artifacts record T2 and T3 `PASS`; timeframe-specific later
branches record their own mixed outcomes (for example M30 T2 `BORDERLINE` and T3
`PASS`, and M15 T2 `FAIL` and T3 `PASS`).  These are different provenance lines,
not contradictory votes on one harmonized candidate.

## Independent later branches

### Multi-timeframe research

Phase 7.1 executes declared timeframe combinations; Phase 7.2 analyzes its
immutable artifacts without market-data access, trade recalculation,
optimization, ranking, or selection and labels every combination either
`ROBUST_TIMEFRAME_CANDIDATE` or `RESEARCH_ONLY` using fixed gates.  Phase 7.3 is
the separate true-MTF H1→M15, H1→M30, and H4→H1 research bundle.  These phases do
not silently replace the original H1 lifecycle or the newer v2 baseline.

### Additional timeframe generations

M1, M5, M15, M30, H4, and D1 runners encode later baseline/optimization/
robustness/walk-forward/TRUE-OOS variants.  Their own manifests, candidate IDs,
coverage, gates, and verdicts are authoritative.  Code existing for a later
stage is not evidence that its run completed; only committed artifacts and
verdicts establish completion.

Historical differences are preserved, not retroactively harmonized.  In
particular, their existence never promotes their phase logic into a second
methodological template.

## Universal evidence requirements

Each phase must preserve the exact upstream identity, code/config hashes, data
scope and source provenance, costs/slippage, deterministic ordering, full trial
or trade population, and the phase's classification rules.  Reports summarize
artifacts; they do not replace them.  Audit claims use `AUDIT_PROTOCOL.md`.
