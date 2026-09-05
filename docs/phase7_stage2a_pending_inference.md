# Phase 7 UNKNOWN Stage 2A: pending-inference semantics

## Preserved legacy contract

`UnknownPatternScheduler.pending_inference_cells(limit)` projects the effective
latest state of append-only `ResearchMemory`. A cell qualifies if and only if:

1. its semantic `pattern_cell_id` belongs to the scheduler's frozen logical
   search space;
2. its effective status is exactly `INFERENCE_PENDING`; and
3. its effective evaluation has no `raw_p` key.

No other evaluation field is an eligibility condition. In particular,
`inference_enabled` need not be true. `INELIGIBLE`, `INCOMPLETE_FAMILY`,
`SCREENED_OUT`, and `PATTERN_SURVIVOR` records are excluded. An inference event
adds `raw_p` and changes status, so inferred records are excluded. Finalized
families are excluded by their effective finalized status. Family completeness
is otherwise not consulted: an unusual record still marked
`INFERENCE_PENDING` and lacking `raw_p` remains pending regardless of its
`family_complete` value.

The qualifying cells are ordered by the seeded deterministic hash of
`pattern_cell_id`. The old implementation used Python's stable sort after
visiting cells in frozen-universe order, so hash ties retain logical-universe
order. A negative limit raises `ValueError`; zero returns an empty tuple; a
positive limit returns the first `limit` cells and a limit beyond the pending
population returns all pending cells. Append event order does not affect the
result. Reopening memory reconstructs the same effective state and therefore
returns the same sequence.

## Architecture

Before Stage 2A, the scheduler visited every logical cell, calculated all
semantic IDs, probed effective memory, materialized all matches, sorted them,
and sliced the result. Metrics repeated that operation with the 17,024,040-cell
universe length as the limit.

Stage 2A instead visits effective pattern records, applies the unchanged status
and `raw_p` predicates, reconstructs a candidate from the already-persisted
`scientific_definition`, verifies its unchanged semantic ID, and resolves its
logical ordinal arithmetically against the compact search-space manifest model.
Only qualifying records are sorted. No metadata or identity schema changed, so
existing JSONL records containing the already-required scientific definition
remain readable. Invalid or out-of-universe definitions fail closed, matching
the old scan's exclusion of IDs absent from the active universe.

`pending_inference_count()` uses the same effective-memory predicate and exact
membership validation as a streaming count. Worker and standalone metrics use
this count-only path rather than selecting a universe-sized prefix.

## Controlled smoke evidence

A fresh four-file synthetic execution fixture covered 2026-02-02 through
2026-02-13 only and used the checked-in production manifest/index. It confirmed
17,024,040 logical cells. Initialization took 41.678322 s, manifest validation
18.965355 s, indexed planning 0.002048 s, discovery 5.216677 s (including
0.001042 s persistence), pending selection 0.000599 s, and the no-op inference
call 0.000008 s. Peak RSS through those stages was 841.20 MiB.

The discovered fixture record was `INELIGIBLE`, hence zero pending records were
selected. Execution then remained in the unchanged
`finalize_ready_families()` full-universe pass at one CPU core. The diagnostic
run was stopped after approximately 4 minutes 49 seconds total, with the Python
process using about 2.33 GiB RSS, after this next bottleneck was unambiguously
identified. Consequently validation, state persistence, clean return, and the
MIXED gate were not reached. Stage 2A intentionally does not alter family
finalization.
