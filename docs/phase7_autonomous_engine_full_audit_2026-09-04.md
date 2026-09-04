# Phase 7 Autonomous Engine Full Audit

**Audit date:** 2026-09-04 (UTC)  
**Audited commit:** `20463a34e4ffd6382e88785c0a0e00ee68ef0c51`  
**Scope:** Static architecture, CLI, persistence, available execution artifacts,
TRUE OOS controls, Git/GitHub state, and the complete test suite. No autonomous
research cycle was started and no application, research, trading, or data logic
was changed.

## Executive conclusion

**Classification: B — additional fixes are required before a manual
`budget=50` mixed cycle.**

The known-track path is connected, deterministic, persisted through research
memory, and isolated per experiment. UNKNOWN_PATTERN discovery is also connected
and persists append-only effect records. Mixed routing always calls known before
unknown and isolates exceptions between those two tracks.

The production Phase 7 entry point does **not**, however, execute the documented
UNKNOWN_PATTERN inference/family-finalization lifecycle. It always invokes
unknown discovery with `infer=False`, exposes no inference budget, and declares
the unknown track exhausted when discovery cells are exhausted even if inference
is pending. In addition, a mixed cycle gives the full requested budget to each
track (up to twice the nominal budget), and integrated worker state lacks the
manifest/count detail required to reconstruct cycle activity. These are readiness
defects, not findings that justify changing governed behavior during this audit.

## 1. Repository and branch state

- The checkout was clean before the report was added. Its local branch was
  `work`, at the same SHA as GitHub `main` (`20463a3`).
- The checkout had **no configured Git remote**, no local `main` branch, and no
  remote-tracking branches. GitHub state therefore had to be queried explicitly
  with `gh -R alkospacer123/market-pattern-discovery` and the GitHub API.
- GitHub's default branch was `main`; its head was `20463a3`, the merge of PR
  #35. The immediately preceding history was PR #35 cleanup, PR #34 workflow
  marker, Phase 7 track routing (#33), Phase 7 CLI selector (#32), and the Phase
  7 autonomous commits (#31 through #27).
- Six pull requests were open: #32, #19, #18, #15, #13, and #12. PR #32 remains
  open even though a later version of that work is already in `main` through
  squash commit `8c4f4a2`.
- GitHub exposed 51 non-main branches. Many are fully behind `main`; multiple
  stale branches remain diverged/ahead, including old Phase 7 and earlier
  research branches. Branch cleanup is therefore incomplete even though `main`
  itself is clean.

## 2. Phase 7 architecture

### Known track

Observed flow:

`AutonomousSearchScheduler.plan` → `CycleRunner.run` → `ExperimentRunner.run`
→ the Phase 6B evaluation pipeline.

- The scheduler selects unseen semantic cells, uses stable hash ordering, and
  returns an explicit exhausted status.
- The cycle runner catches failures independently at each experiment boundary,
  allowing later experiments to run.
- The experiment runner records experiment, candidate, and evaluation history in
  `ResearchMemory`; only successfully recorded experiments count as completed.
- Worker state is atomically written after a bounded invocation.

**Answer:** yes, with “evaluation” comprising the existing ExperimentRunner /
Phase 6B execution and memory-recording path.

### Unknown track

The lower-level UNKNOWN_PATTERN module implements the desired lifecycle:

`UnknownPatternScheduler.plan` → append discovery effects as
`INFERENCE_PENDING` → `pending_inference_cells` → `add_inference` →
`finalize_ready_families`.

The production Phase 7 worker only runs the first two steps. `_run_unknown`
plans a discovery batch and calls `run(..., infer=False)`. It never calls
`pending_inference_cells`, `add_inference`, or `finalize_ready_families`.
Consequently, Phase 7 execution is currently:

`discovery → persisted INFERENCE_PENDING cells → stop`.

**Answer:** no. The complete lifecycle exists in the lower-level standalone
UNKNOWN_PATTERN CLI, but it is not integrated into
`scripts/run_autonomous_research.py`.

### Mixed track

- Ordering is deterministic: known, then unknown.
- An exception from one track does not prevent the other track from receiving a
  turn, and track-qualified failures are persisted in worker state.
- Both tracks receive the entire `budget` argument. Thus `--budget 50 --track
  mixed` can schedule 50 known experiments plus 50 unknown cells, rather than 50
  total units. This conflicts with the worker's “budget-capped cycle” description
  and makes the operator-facing meaning of budget unsafe for a large first run.
- Unknown inference/finalization remains absent in mixed mode.

**Answer:** known then unknown is deterministic, but this is not yet the stated
complete “known + unknown” lifecycle and the aggregate budget is not capped at
the CLI value.

### Restart, persistence, and failure isolation

- Finalized worker cycle numbers cannot be rerun. The CLI selects one plus the
  greatest persisted worker cycle number, so clean restarts advance reliably.
- Memory-based semantic IDs prevent successful known experiments and discovered
  unknown cells from being duplicated after restart.
- JSONL research memory is append-only, uses `O_APPEND`, flushes with `fsync`,
  and reconstructs current pattern state from immutable events.
- Known experiments are failure-isolated individually. Mixed tracks are isolated
  from each other. Unknown-only batch execution is **not** isolated per cell: an
  exception propagates, prevents worker-state persistence for that invocation,
  and leaves only earlier append-complete cells as evidence. A restart should
  avoid those earlier cells and retry remaining cells, but the failure itself is
  not captured in autonomous state.
- Atomic worker-state replacement protects finalized state-file writes. There is
  no equivalent integrated autonomous manifest capturing the planned cells,
  counts, and partial progress.

## 3. CLI audit

The production help output exposes:

- required `--data-root`, `--memory-root`, `--output-root`, and `--budget`;
- `--mode {once,continuous}`;
- `--track {known,unknown,mixed}`;
- `--sleep-seconds`.

It does **not** expose `--inference-budget`.

Parameter wiring findings:

- `--track` constructs UNKNOWN_PATTERN components when required and reaches the
  worker router.
- `--budget` reaches scheduler planning. In mixed mode it is applied separately
  to both tracks rather than shared.
- `--mode once` returns after one invocation. `continuous` increments the cycle,
  sleeps for the configured interval, and stops on worker status
  `SEARCH_SPACE_EXHAUSTED`.
- Because the worker never services inference, continuous unknown mode stops
  when discovery is exhausted regardless of persisted inference-pending work.
- Positive-budget and non-negative-sleep validation are enforced.

The standalone `market_pattern_discovery.orchestration.unknown` CLI does expose
`--mode {discovery,inference,both}` and `--inference-budget`, but that is not the
requested production Phase 7 script.

## 4. UNKNOWN_PATTERN lifecycle and memory

### What discovery creates

For each selected frozen search cell, discovery evaluates descriptive effect
information without inferential p-values, appends a `PatternEffectRecord`, and
marks eligible records `INFERENCE_PENDING` (or `INELIGIBLE`). The record contains
cell/batch/experiment identities, cycle number, feature/target definition,
provenance, contract signatures, effect evidence, and incomplete-family fields.

### What remains pending

`pending_inference_cells` deterministically selects persisted records whose
effective status is `INFERENCE_PENDING` and which lack `raw_p`. The full test
suite verifies deterministic selection and continuation after reopening memory.
Because the production worker never calls this method, every eligible discovery
record created through that worker remains pending indefinitely.

### What can be finalized

`add_inference` appends `INFERENCE_ADDED` evidence with uncertainty and raw
p-values. `finalize_ready_families` waits until every cell in a frozen family is
present; it excludes ineligible members, requires inference for every eligible
member, performs BH adjustment, screens effects, and appends
`FAMILY_FINALIZED`. It is idempotent for already finalized families. Tests cover
cross-restart inference/finalization and no-op repeated finalization.

### Append-only behavior

`pattern_effect_history.jsonl` is the authoritative event stream. Creation,
inference enrichment, and family finalization append separate events; current
state is a projection. Duplicate creation, duplicate inference, and repeated
family-finalization events are rejected/no-op as appropriate. The related known
track streams are `experiments.jsonl`, `candidate_history.jsonl`, and
`evaluation_history.jsonl`.

### Available live memory

No `pattern_effect_history.jsonl` or related autonomous memory stream existed in
the repository, elsewhere under `/workspace`, or in the recursive GitHub `main`
tree at audit time. Therefore there is no live UNKNOWN_PATTERN population from
which to report numeric created, pending, or finalized counts. Available counts
are: **created 0 observable, pending 0 observable, finalized 0 observable**;
these mean “no persisted evidence available,” not proof that no external run was
ever performed.

## 5. Current cycles and results

No `autonomous-state` directory, Phase 7 cycle manifest, Phase 7 report,
autonomous result directory, or autonomous JSONL memory was present in the
checkout or elsewhere under `/workspace`. None was present in GitHub `main`.
Folder modification times were not used.

Accordingly, **zero Phase 7 cycles are verifiable from persisted manifests/state
available to this audit**. There is no defensible per-cycle track, budget, status,
experiment count, candidate count, evaluation count, or failure count to report.

The tracked `results/phase6b/run_manifest.json` is an earlier Phase 6B result,
not an autonomous Phase 7 cycle. Its own content reports `PARTIAL`, the discovery
window, 11 strategies, and its row counts; it must not be misclassified as an
autonomous cycle.

This absence also exposes an observability gap: integrated worker state stores
only cycle number, overall status, combined ID, failures, and validation. It
does not store track, requested/effective per-track budget, planned/finished
experiment counts, candidate/evaluation counts, pending inference, or finalized
families. Although `CycleReport.audit` can produce richer known-track data, the
worker never persists or invokes it. The integrated unknown worker likewise does
not write the standalone unknown manifest.

## 6. TRUE OOS safety

**Result: controls remain intact; no bypass was identified in Phase 7 routing.**

- Source discovery is structurally rooted at `<data-root>/2026/<instrument>` and
  accepts only the expected 2026 filenames.
- Ingestion validates every source timestamp against the approved development
  interval.
- UNKNOWN_PATTERN loading requests signed DISCOVERY access before reading,
  rejects any discovered source path containing `2025`, then filters and checks
  the discovery window.
- Known Phase 6B loading uses the same enumerated source discovery and separately
  rejects empty, non-2026, or out-of-bound data.
- The research protocol seals calendar 2025 for non-TRUE-OOS access and requires
  a `frozen_for_true_oos` candidate for explicit TRUE OOS mode.
- Phase 7 accepts an operator-provided root, but its actual loaders do not glob
  arbitrary years beneath that root. No new track-routing code directly opens
  source files or bypasses the guarded loaders.
- Tests explicitly cover development boundaries, forbidden 2025 ingestion,
  protocol refusal, Phase 6D metadata detection, and architecture-level TRUE OOS
  rejection.

Residual note: Phase 6D validation checks recorded metadata, so it is a detection
layer rather than the primary access boundary. Safety rests correctly on the
enumerated 2026 loader, timestamp validation, and access protocol.

## 7. Test coverage

`pytest -q` completed with **276 passed, 0 failed, 0 warnings** in 26.67 seconds.

Coverage is strong for deterministic known scheduling, memory immutability,
restart projections, UNKNOWN_PATTERN inference/finalization primitives, routing
order, and mixed-track exception isolation. Important missing integration tests
mirror the defects above:

- no production-worker test requiring pending inference to progress;
- no production-worker test requiring family finalization;
- no exhaustion test with discovery exhausted but inference pending;
- no assertion that mixed work is capped by one aggregate budget;
- no state-schema/count audit test;
- no unknown-only per-cell failure persistence/recovery integration test.

## 8. Readiness assessment

### Classification B — additional fixes required

Do **not** run the requested manual `budget=50` mixed cycle yet.

Blocking reasons:

1. Phase 7 production routing strands UNKNOWN_PATTERN records before inference
   and family finalization.
2. Discovery exhaustion can terminate a continuous run while inferential work is
   pending.
3. Mixed budget semantics can execute twice the operator's nominal cap.
4. Persisted autonomous state cannot support the requested per-cycle audit and
   cannot distinguish track-level counts/progress.
5. Unknown-only failures are not persisted/isolate-at-cell in the same manner as
   known experiments.

The clean test suite establishes that currently asserted behavior is stable; it
does not make the missing production lifecycle ready.

## 9. Recommended sequence

1. Obtain separate approval for a narrowly scoped Phase 7 remediation PR; do not
   alter scientific definitions, trading logic, costs, data boundaries, or TRUE
   OOS rules.
2. Integrate explicit inference budgeting and family finalization into the
   production worker, including progress after discovery exhaustion.
3. Define and enforce aggregate mixed-cycle budget semantics (recommended: split
   one total cap deterministically, or rename/document separate per-track caps).
4. Persist an atomic, schema-stable per-cycle manifest containing track,
   requested/effective budgets, planned/completed/failed counts, candidates,
   evaluations, inference pending/completed, family finalization, and per-track
   status. Preserve append-only research memory.
5. Add integration tests for restart, discovery exhaustion with pending
   inference, mixed aggregate caps, per-cell failure recovery, and manifest
   reconstruction.
6. Run the full suite.
7. Run `unknown --budget 3` with a small explicit inference budget; audit memory
   and manifest.
8. Run `known --budget 3`; audit experiment/candidate/evaluation persistence.
9. Run `mixed --budget 3`; verify deterministic ordering, the aggregate cap,
   failure isolation, and restart behavior.
10. Repeat the full audit from manifests/state, not directory timestamps.
11. Only then run one manual `mixed --budget 50` cycle and audit it.
12. Enable long-running research mode only after the budget-50 audit passes.

