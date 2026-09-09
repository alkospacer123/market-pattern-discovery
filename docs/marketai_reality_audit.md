# MarketAI physical reality audit

## Scope and repository gate

- Starting HEAD: `d649eaa965c2b995ce1e7d39e4e1470f24acc95c`.
- `git merge-base --is-ancestor d649eaa965c2b995ce1e7d39e4e1470f24acc95c HEAD`
  exited 0, and the initial working tree was clean (`## work`).
- All ten required rebuild files exist, and `MarketDataLoader`, `ResearchCell`,
  `PatternEffect`, `ResearchIntelligence`, `KnowledgeRecord`, and
  `MultiHorizonResearchRunner` imported from the checkout.

## Capability matrix

| Capability | Expected | Physical file/symbol | Actual production wiring | Status | Evidence / notes |
|---|---|---|---|---|---|
| Baseline | PR #44 ancestor | Git history | HEAD is the required merge | PASS | Merge-base command exited 0. |
| Market aliases | CNY/CNYRUBF and Si/USDRUBF | `data/finam.py:ALIASES` | Loader canonicalizes both | PASS | Real files for both tickers loaded during validation. |
| Finam ingestion | Read-only normalized OHLCV | `MarketDataLoader` | Runner calls `load`; loader only opens sources for reading | PASS | Canonical eight-column output; no resampling or writes. |
| Development fence | Row-time fence through 2026-08-31; 2025 locked | `_read`, `DEV_START`, `DEV_END` | Every production load requests `development_rows_only=True` | PASS | Audit corrected the prior 2026-07-01 end; regression tests retain 2025 and 2026-09-01 exclusion. |
| Timeframes | M1/M5/M15/M30/H1/D1 | `TIMEFRAMES` | Loader and scheduler use registry entries | PASS | Durations are 1/5/15/30/60/1440 minutes; Finam PER is 1/5/15/30/60/`D`. |
| Horizons | Scalping/Intraday/Medium-term | `ResearchHorizon`, `PROFILES` | Scheduler builds all profiles | PASS | Scalping M1/M5 + M15; Intraday M5/M15/M30 + H1/D1; Medium-term H1/D1 + H1/D1. |
| Research tracks | Real KNOWN and autonomous UNKNOWN paths | `ResearchTrack`, `UnifiedResearchExecutor`, `_known`, `_unknown` | Dispatcher reaches two different functions | FAIL | Both production handlers ignore the prepared contracts and return only fixed labels. UNKNOWN is not a whitelist, but it also performs no autonomous discovery; KNOWN performs no family evaluation. |
| Cell scheduling | Deterministic unseen cells and restart awareness | `ResearchCell.identity`, `MultiHorizonScheduler.plan` | Runner rebuilds completed cell IDs from memory each cycle | PASS | 20 attempts had 20 cell IDs and restart continued at the next deterministic cell. |
| Causal context | Closed M15/H1/D1 only | `CausalContextEngine` | `_prepare` aligns every profile context | PASS | Backward as-of uses close times and asserts `context_close_time <= observation_close_time`; D1 closes at open + 24 hours, not midnight-open availability. |
| Evidence/effects | Evidence-derived `PatternEffect` and conclusion | `Evaluation`, `Evidence`, `create_pattern_effect`, `ResearchIntelligence` | Runner computes mean close change after dispatch | PARTIAL | Evidence is calculated from real bars, but it is disconnected from the fixed-label track handler result; effects are transient and not separately persisted. |
| Research intelligence | positive/negative/unresolved, not rules | `ResearchIntelligence.conclude` | Runner uses the conclusion in knowledge records | PASS | The type exposes no signal/order/position behavior. |
| Research memory | Append-only attempts/knowledge, deterministic IDs, restart dedupe | `ResearchMemory` | Runner records attempts then knowledge | PASS | JSONL uses append writes plus fsync; duplicate IDs return false; restart retained all process-A rows. |
| Production CLI | Finite production multi-horizon entry point | `scripts/run_multihorizon_research.py` | Instantiates and calls `MultiHorizonResearchRunner.run` | PASS | Positive cycles and budget are mandatory; zero/unlimited cycles are rejected. |
| Legacy autonomous architecture | Existing pre-PR-44 system remains | `orchestration/autonomous.py`, `orchestration/worker.py` | Separate legacy CLI/worker path | PASS | The finite strategy search scheduler, mixed known/unknown worker, cycle manifests, and legacy memory APIs remain physically present; the rebuilt CLI does not call them. |

## Actual production call chain

The rebuilt CLI calls `MultiHorizonResearchRunner.run`. Each cycle reads
persisted attempts, asks `MultiHorizonScheduler` for unseen `ResearchCell`s,
and calls `_prepare`. `_prepare` loads the primary and each context timeframe
with `MarketDataLoader`, aligns contexts with `CausalContextEngine`, and creates
a one-column close-change feature frame. `UnifiedResearchExecutor` dispatches
to `_known` or `_unknown`, but those functions only return constant method and
state strings and do not inspect their arguments. The runner then independently
constructs an `Evaluation` from the mean primary close change, qualifies
`Evidence` on row count, creates an in-memory `PatternEffect`, classifies it
with `ResearchIntelligence`, and appends one `KnowledgeRecord` per context
timeframe to `ResearchMemory` after appending the attempt.

This differs materially from the architectural report's implication that the
KNOWN/UNKNOWN stage performs discovery that produces the evaluated evidence.
Connecting a real discovery implementation would be architectural work, so it
was not improvised in this audit.

## Causality evidence

Context timestamps are candle opens. `close_times` adds the canonical duration,
including 24 hours for D1. `merge_asof(... direction="backward")` joins only a
context close at or before the observation close and a runtime assertion checks
the invariant. A post-run replay of all 20 persisted cells checked 699,212
available aligned rows and found zero violations.

## Persistence and restart evidence

`ResearchMemory` stores attempts and knowledge as canonical JSONL append events.
Semantic hashes provide attempt, cell, and knowledge IDs. Before appending, the
memory checks the on-disk history, so a new process sees prior records and the
scheduler excludes their cell IDs. Process A produced 10 unique attempts and 16
unique knowledge records. Process B used the same directory and grew those
counts to 20 and 34 without duplicates or overwritten rows.

## Tests

- Focused architecture gate: `53 passed in 12.88s` (wall 14.710 seconds).
- Full repository gate: `309 passed in 27.43s` (wall 29.344 seconds).
- An earlier post-change run exposed a stale July boundary assertion
  (`1 failed, 308 passed`); the assertion was updated to the required August
  boundary and both final gates above passed.

## Missing/partial components and reality verdict

The production track functions are placeholders rather than genuine KNOWN and
UNKNOWN research implementations, and the later evaluation is independent of
their returned result. Therefore the physical code and persistence machinery
are operational, but the requested production research path is not scientifically
complete.

**Reality audit: FAIL.**
