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
