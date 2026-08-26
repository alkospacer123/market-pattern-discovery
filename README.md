# Market Pattern Discovery

A research-first, causality-safe Python foundation for strict Finam candle
validation. The dependency and research direction is one way only:

`raw data → ingestion → features → discovery → hypothesis → backtest → robustness validation → TRUE OOS`

Only ingestion and validation contracts exist today. There is deliberately no
feature builder, target calculation, pattern discovery, strategy search, or
backtest implementation.

## Locked research configuration

Development uses `CNYRUBF` and `USDRUBF` (including documented `CNY`/`Si`
filename aliases), M1 and M5, from 2026-01-01 through the inclusive end of
2026-07-01 in `Europe/Moscow`. Finam timestamps are candle **open** times.
Calendar year 2025 is locked TRUE OOS and forbidden in development workflows.

Run `pytest -vv` for contract tests. Run `python scripts/validate_phase1b.py`
only against the eight explicitly enumerated 2026 source files; it hashes them
before and after and writes its ignored report under `results/`.
