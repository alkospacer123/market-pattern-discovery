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
