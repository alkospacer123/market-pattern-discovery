# BBW Core v1.0

Install the project, then prepare and validate an H1 baseline input without
copying source data into this repository:

```bash
python -m pip install -e '.[test]'
bbw-backtest --config bbw_system/config/base.yaml --h1 /read-only/path/H1.csv --output results/bbw_baseline
pytest -q tests/test_bbw_core.py
```

The baseline accepts arbitrary configured history; train/OOS partitioning is a
separate research workflow concern and no calendar year is special-cased here.
It writes data diagnostics, policy-complete anchor-aligned synthetic setup bars, four
CSV journals, and the conservative execution-policy record. The core exposes
strategy primitives rather than parameter search; there is no optimizer.


Session exclusions are explicit through `excluded_weekdays`, `excluded_dates`,
intraday `excluded_intervals`, and date-specific `session_end_overrides`.
`setup_bar_completion_policy` is either
`strict_source_count` or `session_end_valid`; the latter accepts a shortened
final bucket only when all session-expected H1 slots are present. Range anchoring
is explicit and deterministic; no candidate is selected using a later breakout.
