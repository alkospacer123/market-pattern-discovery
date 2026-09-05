# Phase 7 Stage 2B: ResearchMemory-driven family finalization

## Frozen legacy oracle

`PatternExperimentRunner.finalize_ready_families` historically grouped the
entire supplied search universe by `(instrument, timeframe, method,
target_family, target_role)`.  Every cell in that frozen group was expected;
the expected size was the number of grouped cells.  Members were sorted by
`pattern_cell_id`, and a family was incomplete if any expected ID lacked an
effective `PatternEffectRecord`.

`INELIGIBLE` records count as present for completeness, but are removed from
the eligible member sequence.  They receive no BH input and no finalization
event.  A family with no eligible members is therefore complete but produces
no events.  Every eligible member must have `raw_p`; consequently
`INFERENCE_PENDING` and any other record without `raw_p` prevent finalization.
Existing `INCOMPLETE_FAMILY` records with raw p-values are eligible.  Eligible
members already in `SCREENED_OUT` or `PATTERN_SURVIVOR` are treated identically
to other eligible records unless every eligible record has
`family_complete=true`; that all-finalized case is an idempotent no-op on
restart.

BH receives eligible raw p-values in ascending `pattern_cell_id` order.  Its
results are zipped back onto that same sequence.  Screening then runs in that
sequence, and one append-only `FAMILY_FINALIZED` event is emitted per eligible
member in sequence.  Families themselves are processed in lexicographic
family-key order.  Partial families, including partially ineligible families,
produce no event.  These rules also define the eager small-universe oracle
retained by the implementation and tests.

## Stage 2B architecture

The production `PatternSearchSpace` now derives exact family cardinalities
directly from its frozen compact condition blocks and ordered target outcomes.
For each block the exact contribution is the number of condition-state
combinations multiplied by the number of outcomes with the family and role.
This is algebraically the same Cartesian product traversed by the legacy
iterator and requires neither a new mutable artifact nor a universe scan.
The inputs remain covered by the existing immutable manifest universe binding.

Finalization starts from effective ResearchMemory records.  Each persisted
scientific definition is reconstructed, its semantic ID is checked, and
`PatternSearchSpace.ordinal_of` proves membership in the active universe.
Malformed, stale, or out-of-universe records fail closed.  Records are grouped
only into touched families.  A touched record count unequal to the exact frozen
cardinality rejects readiness immediately.  Only a genuinely complete family
is sorted and passed through the unchanged eligible filtering, BH, screening,
and append-only persistence logic.

For deliberately small eager sequences, finalization continues to enumerate
the sequence to provide the legacy oracle and compatibility behavior.  Normal
indexed UNKNOWN operation uses the compact path and is proportional to
effective memory records plus touched families, apart from work on a family
that is actually complete.
