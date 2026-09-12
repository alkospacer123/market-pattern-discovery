# BBW Core v1.0

Install the project, then prepare and validate an H1 baseline input without
copying source data into this repository:

```bash
python -m pip install -e '.[test]'
bbw-backtest --config bbw_system/config/base.yaml --h1 /read-only/path/H1.csv --output results/bbw_baseline
pytest -q tests/test_bbw_core.py
```

The command deliberately refuses every dataset containing calendar year 2025.
It writes data diagnostics, complete anchor-aligned synthetic setup bars, four
CSV journals, and the conservative execution-policy record. The core exposes
strategy primitives rather than parameter search; there is no optimizer.
