# STOP/TICK GRID — audit-only artifacts

Read [REPORT_RU.md](REPORT_RU.md). `PRODUCTION_CHANGES=NONE`; no live fix is installed. These files are not imported by the robot.

- `results.json`: authenticated sources, coverage, full and lifecycle counts, instrument/year breakdowns, replay classifications.
- `*_signals.csv` / `*_entries.csv`: derived diagnostic signal evidence, not broker orders or adjusted OOS.
- `*_reconciliation.csv`: two independent raw TRAIL1 comparisons with the unchanged frozen ledger.
- `runtime_matrix.csv`: synthetic risk/margin scenarios, not historical account snapshots.
- `outward_rounding_math_only.csv`: mathematical sizing proposal; no adjusted returns.
- `supplemental_results.json`: causal-prefix real-signal/restart checks and projection edge cases.
- `verification.json`: final GitHub main, diff, source equality and tests.

Reproduction requires Python 3.11+, numpy, pandas, jsonschema, tabulate and pytest. Use isolated clones: code commit `688560ec2e8a71c1085bec255a9660783b51e122`; data commit `50f1fd2178c18b7ab3bd969be82ad01f47a34745`. Do not replace an operator's checkout. Market data must stay outside the code repository. No FINAM credentials are needed.

From the isolated code checkout, run:

```bash
PYTHONDONTWRITEBYTECODE=1 python audit_only/stop_tick_grid_20261012/audit.py \
  --data-root /path/to/frozen-data \
  --out /path/to/new-diagnostic-output \
  --scratch /path/to/new-empty-diagnostic-sqlite-directory
PYTHONDONTWRITEBYTECODE=1 python audit_only/stop_tick_grid_20261012/supplemental.py \
  --data-root /path/to/frozen-data \
  --results-dir /path/to/new-diagnostic-output \
  --scratch /path/to/another-new-empty-diagnostic-sqlite-directory
PYTHONDONTWRITEBYTECODE=1 python audit_only/stop_tick_grid_20261012/run_existing_tests.py
```

`audit.py` never calls an order endpoint; socket connections are explicitly forbidden. It invokes reconciliation with new output paths and never calls existing generators that would overwrite frozen files. It requires byte-exact frozen sources and verifies their Git blobs. Use a fresh scratch directory each time.

Existing-tests runner uses disposable `/workspace/work/stop-tick-results/pytest-temp`; when running in another environment, change only this diagnostic runner's scratch path in an isolated copy. Never use production state. `audit.py` and `supplemental.py` require empty scratch directories to prevent accidental reuse of old diagnostic state.

The 16.09–11.10.2026 twelve-signal claim remains unverified. Frozen data ends with the 15.09.2026 23:00 source candle (16.09 00:00 completed close in Moscow). All adjusted-price evidence is mathematical diagnostics, not replacement OOS.
