# UNKNOWN RESOURCE REPORT

**Profile date:** 2026-09-04 (UTC)
**Profiled commit:** `c6a4cdf5b97b682ed9025fb51d05d2128ac557df`
**Workload:** production-equivalent `mixed --budget 2` (one KNOWN cell followed by
one UNKNOWN discovery cell), using the approved 2026 development inputs at their
external, read-only location. No 2025 TRUE OOS input was read, no source data was
copied, and no application or research logic was changed.

## Executive result

UNKNOWN initialization is dominated by materializing **17,024,040 Python
`PatternSearchCell` objects**, followed by the scheduler recomputing a semantic
SHA-256 identity for every object to check uniqueness. The four matrices do not
remain alive after their corresponding cell tuple is produced, yet the retained
search space alone raised process RSS from 117.1 MiB after KNOWN to 3,688.7 MiB
before scheduler validation. Per-scope search-space construction was the largest
observed allocation source: approximately 859--944 MiB RSS for each 4.24--4.27
million-cell scope.

The full production-sized profile was stopped safely during scheduler duplicate
validation after 13:04 process wall time (about 12:59 in UNKNOWN) at approximately
4,104 MiB RSS. It had not reached planning or discovery. This is not a deadlock:
RSS continued to rise as the temporary list of 64-character cell IDs was built.
A controlled 100,000-cell run completed the remaining stages and demonstrates
that planning is another whole-search-space pass, not a budget-sized operation.

No critical correctness bug was found. The finding is a resource-scaling and
observability problem; changing it would alter implementation logic and was
therefore outside this profiling-only task.

## Environment and method

The run used CPython 3.14.4, pandas 3.0.5, and NumPy 2.5.2 on Linux x86-64. An
external `/tmp` harness called the same repository constructors and methods in
production order and sampled `/proc/self/status` `VmRSS` plus
`resource.getrusage(...).ru_maxrss`. Timing used `time.perf_counter`. Temporary
memory/output roots were outside the repository. Matrix retained size is
pandas' deep logical size for the frame plus state series; it is not additive
to RSS because object/string storage can be shared and allocator release is not
immediate.

To avoid an uncontrolled multi-gigabyte continuation, the full run was stopped
once it had conclusively identified scheduler validation as the current stage.
Planning and discovery were then measured with the identical code paths on the
first 100,000 frozen cells. Values labeled **projected** below are simple linear
capacity estimates, not completion measurements; sorting and allocator behavior
make them lower-confidence than the directly observed figures.

## Stage profile

| Required stage | Direct observation | RSS after stage | Interpretation |
|---|---:|---:|---|
| CLI creation | 0.021 s | 73.7 MiB | `ResearchMemory` plus the 396-cell KNOWN scheduler; UNKNOWN remained lazy. |
| worker creation | 0.001 s | 73.7 MiB | Confirms the lazy factory itself has negligible setup cost. |
| KNOWN execution | 4.972 s | 117.1 MiB | One mixed-budget KNOWN cell completed successfully; peak was 117.0 MiB. |
| UNKNOWN factory initialization | >779 s observed; incomplete | ~4,104 MiB at safe stop | Matrix/cell materialization finished in 327.5 s; tuple finalization finished at 332.6 s; scheduler identity validation was still running. A 100k-cell scheduler initialization took 11.482 s, implying roughly 32.6 min for 17.0m cells if linear, or about **38 min total factory time** including measured construction. |
| matrix loading | 158.2 s total | scope-dependent | Sum of four direct load timings. M1 matrices caused both the longest loads and the highest transient matrix peaks. |
| search-space construction | 155.7 s total, plus 5.084 s final tuple/release work | 3,688.7 MiB retained | Generates all 17,024,040 objects regardless of discovery budget. This is the largest retained allocation. |
| planning | 24.958 s for 100k; full size not run | 218.4 MiB in controlled run | A simple linear projection is ~70.8 min at 17.0m cells. Full planning hashes every unseen cell, buckets all cells, hashes them again for seeded ordering, and sorts each scope; actual full-size time may be worse than linear. |
| discovery | 57.874 s for one selected cell | 224.5 MiB after completion in controlled run | Nearly all of this is the selected cell's matrix reload; one discovery record was created. It is reached only after initialization and global planning. |

The production-sized run's directly completed UNKNOWN work was 327.5 s through
per-scope construction and garbage collection, followed by 5.1 s for final tuple
conversion/release. At the safe stop, duplicate validation alone had consumed
more than 7 minutes and increased RSS by roughly another 0.4 GiB through its
temporary ID list.

## Matrix and search-space detail

| Scope | Rows | Matrix columns | State series | Matrix load | Load RSS delta | Peak RSS during load | Deep retained matrix size | Fragmentation warnings | Generated cells | Cell construction | Cell RSS delta |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| CNYRUBF M1 | 77,789 | 441 | 240 | 66.277 s | +494.5 MiB | 863.2 MiB | 1,245.6 MiB | 88 | 4,268,772 | 40.464 s | +944.2 MiB |
| CNYRUBF M5 | 16,193 | 346 | 219 | 14.543 s | +127.0 MiB | <=1,555.4 MiB process HWM | 230.6 MiB | 16 | 4,243,248 | 39.814 s | +865.2 MiB |
| USDRUBF M1 | 76,567 | 441 | 240 | 62.144 s | +416.3 MiB | 2,613.8 MiB process HWM | 1,226.0 MiB | 88 | 4,268,772 | 38.398 s | +941.9 MiB |
| USDRUBF M5 | 16,170 | 346 | 219 | 15.229 s | +131.3 MiB | <=3,299.1 MiB process HWM | 230.3 MiB | 16 | 4,243,248 | 37.072 s | +858.9 MiB |
| **Total** | **186,719** | — | — | **158.193 s** | — | — | — | **208** | **17,024,040** | **155.748 s** | — |

The repeated cell totals across instruments are expected because cell count is
determined by the frozen feature/state/target contract for each timeframe, not
by the number of market rows.

## Largest allocation and causal path

1. **Largest retained component — search-space objects.** RSS after KNOWN was
   117.1 MiB and settled at 3,688.7 MiB after all four matrices had been released,
   a net retained increase of about **3,571.6 MiB**. Dividing that lower-bound
   process increase by 17,024,040 cells gives about **220 bytes per cell** of
   retained RSS on this interpreter, excluding later identity-validation data.
2. **Largest individual increments — per-scope cell tuples.** M1 scopes added
   about 942--944 MiB each and M5 scopes added about 859--865 MiB each. Cell
   construction time barely depends on source row count, reinforcing that
   hypothesis cardinality is the driver.
3. **Largest matrix — CNYRUBF M1.** Its matrix/state payload had 1,245.6 MiB of
   pandas deep logical size and produced the largest measured load delta
   (+494.5 MiB). Its load also produced 88 fragmentation warnings.
4. **Additional transient allocation — scheduler IDs.** Scheduler construction
   converts the search space to another tuple (cheap when already a tuple), then
   builds a list of every 64-character `pattern_cell_id` and a set of those IDs
   for duplicate detection. The full run was inside this pass when stopped;
   observed RSS rose from 3,688.7 MiB to about 4,104 MiB and was still growing.
5. **Planning repeats global work.** Even with budget one, planning creates an
   `unseen` list over the complete space, four bucket lists, recomputes cell IDs,
   computes seeded hashes for sorting, and sorts all four buckets before choosing
   one cell. The budget caps selected work, not initialization or planning work.

## Fragmentation warning attribution

All 208 captured pandas `PerformanceWarning`s arose during matrix loading. They
are emitted while behavior columns and final timestamp columns are inserted one
at a time into an already wide copied feature frame. They are not emitted by
`PatternSearchCell` construction. This warning site explains matrix-build
transients, but not the dominant 3.57 GiB retained after matrices are released.

## Conclusions

- Lazy initialization behaves correctly: CLI and worker creation remain at
  73.7 MiB and UNKNOWN starts only after KNOWN completes.
- UNKNOWN's frozen space contains **17,024,040 cells**, approximately 43,000
  times the 396-cell KNOWN space.
- Search-space objects are the largest allocation. Scheduler duplicate checking
  adds a second large transient identity collection, and planning performs more
  complete-space identity and sorting work.
- A `budget=2` mixed run selects only one UNKNOWN discovery cell, but its current
  resource cost is governed by the entire 17-million-cell space. The measured
  one-cell discovery itself is roughly one minute; initialization and planning
  dominate elapsed time by orders of magnitude.
- No result from this profile should be treated as scientific discovery output:
  temporary records were solely execution probes and were not added to the
  repository or any durable research memory.
