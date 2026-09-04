# Market Pattern Discovery

A research-first, causality-safe Python foundation for strict Finam candle
validation. The dependency and research direction is one way only:

`raw data → ingestion → features → discovery → hypothesis → backtest → robustness validation → TRUE OOS`

The frozen causal Feature Set v1.0 and the separate research-only Future
Outcome Engine v1.0 now exist. Outcomes intentionally inspect future candles;
features never import or consume them. No outcome is a target label, signal,
trade, profitability measure, or optimization result.

## Phase 3A future-path contract

Finam timestamps are candle opens. `decision_time` is the fully closed current
candle's `close_time`; future candle 1 is strictly the next row (`t+1`). The
fixed grids are M1 `[1, 3, 5, 10, 15, 30, 60]` and M5 `[1, 3, 6, 12]`.
Complete paths may not cross a Moscow calendar date or jump over a missing
one-/five-minute candle. Incomplete, end-of-data, cross-date, and gap horizons
are invalid rather than shortened or padded.

All price changes use the current close as `target_reference_close`. Excursion
values are signed and not clipped: long MFE / short MAE are `future_high -
reference_close`; long MAE / short MFE are `reference_close - future_low`.
Normalized values divide the corresponding prices by the reference close.
Equal extrema use their deterministic first occurrence. When the first high
and first low are in one candle, order is `NaN`; no intrabar ordering is
invented. These directional views imply no strategy. Calendar year 2025
remains locked TRUE OOS and is not accessed by the engine or validator.

## Locked research configuration

Development uses `CNYRUBF` and `USDRUBF` (including documented `CNY`/`Si`
filename aliases), M1 and M5, from 2026-01-01 through the inclusive end of
2026-07-01 in `Europe/Moscow`. Finam timestamps are candle **open** times.
Calendar year 2025 is locked TRUE OOS and forbidden in development workflows.

## Fresh-checkout setup and commands

From the repository root, create an isolated environment and install the project
(including its test dependency):

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[test]'
```

The single standard Phase 1B validator command is:

```bash
phase1b-validate
```

The installed entry point imports the package using normal src-layout packaging;
no local `PYTHONPATH` is required. It reads only the eight explicitly enumerated
2026 source files, verifies their hashes before and after, and writes its ignored
report under `results/`. Run the contract suite with `pytest -vv`.

Validate the Phase 3A outcome matrix on the four approved 2026 datasets with
`phase3a-validate`.

## Research Protocol v1.0

Phase 4A freezes a one-way, chronological research process. The approved 2026
coverage is described without predictive selection; discovery is limited to
2026-01-05 through 2026-05-15 (Europe/Moscow calendar dates), and the untouched
internal-confirmation interval begins 2026-05-16 and runs through 2026-07-01.
The split is a simple mid-month boundary at roughly three quarters of the actual
calendar coverage and was selected without examining target behavior. Random
row splitting is forbidden. Expanding monthly folds validate February, March,
April, and the first half of May using only earlier training blocks.

The four explicit access modes are `DESCRIPTIVE_DEVELOPMENT`, `DISCOVERY`,
`INTERNAL_CONFIRMATION`, and `TRUE_OOS`. Descriptive development may summarize
all approved 2026 data only in aggregate and must not rank or select predictive
feature-to-outcome relationships. Confirmation requires a frozen candidate;
TRUE OOS requires a strategy candidate frozen for that one access. Attempts at
either protected interval are audited without logging market contents.

The two parallel tracks, `unknown_discovery` and `known_hypothesis`, are kept
separate. An unknown machine-derived definition is recorded before any later
human interpretation. CNY and Si can be studied independently or as replication
instruments. M1 with causally available native M5 context is primary, while
standalone M5 is separate; their overlapping observations are not independent.
Future inference must address serial dependence with block/day resampling,
valid temporal permutations, day-clustered uncertainty, and effective sample
considerations. Every experiment accounts for its hypothesis family, and
effect size, stability, replication, uncertainty, and coverage precede mere
significance. No universal minimum event count or single winning metric applies.

The governance flow is:

```text
2026 descriptive research
        ↓
2026 discovery period
        ↓
candidate definition frozen
        ↓
2026 internal confirmation
        ↓
strategy construction / robustness
        ↓
strategy frozen
        ↓
2025 TRUE OOS exactly once
        ↓
pass/fail
        ↓
no OOS retuning
```

Candidate states are one way: `discovered → screened →
frozen_for_confirmation → internally_confirmed|internally_rejected`; confirmed
candidates may continue through `strategy_candidate → frozen_for_true_oos →
true_oos_pass|true_oos_fail`. If a definition changes after confirmation or OOS
was seen, it receives a new candidate identity and that previously seen period
is not untouched for the new version. The immutable experiment, candidate, and
known-hypothesis registries live under `research/`. Stochastic work uses seed
`20260401` unless a different seed was preregistered; seed shopping is forbidden.
Validate this contract without running discovery using `phase4a-validate`.
# Local UNKNOWN_PATTERN execution

The Phase 4B track is a deterministic, single-process Python workflow suitable
for an Intel Windows or Linux workstation. Paths are operational inputs and do
not enter scientific identities. A cycle first discovers unseen frozen cells;
`--inference-budget` then enriches existing `INFERENCE_PENDING` cells using the
canonical 1,000-replication inference contract. ResearchMemory is authoritative
on restart, while an auditable cycle manifest is written beneath `output-root`.

```text
python -m market_pattern_discovery.orchestration.unknown \
  --data-root D:\market-data --memory-root D:\research-memory \
  --output-root D:\pattern-output --cycle 1 --budget 20 \
  --methods univariate_screen --inference-budget 2
```

Repeat with an incremented `--cycle` and the same memory root to resume. Use
`--mode discovery --inference-budget 0` for fast discovery-only cycles, or
`--mode inference --inference-budget 1` for an inference-only resume. The CLI never accesses
trading profitability and does not create strategies or trading candidates.

The Phase 7 production entry point accepts the same `--inference-budget` and
runs pending-cell inference and ready-family finalization after UNKNOWN_PATTERN
discovery. Its `--budget` controls discovery only. In `mixed` mode that total is
split deterministically: KNOWN receives `ceil(N / 2)` and UNKNOWN_PATTERN
receives `floor(N / 2)` (so a budget of 50 is 25 + 25); a zero share is skipped.
Inference has its own explicit cap and does not cause either discovery track to
receive the full mixed budget.
When discovery is exhausted but inference remains and its configured budget
cannot make progress, the cycle reports `INFERENCE_PENDING` rather than
incorrectly declaring the research space exhausted or continuously writing
empty cycle state.
