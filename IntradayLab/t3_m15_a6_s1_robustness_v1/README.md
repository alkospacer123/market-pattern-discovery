# A6+S1 / TRAIL_375 — Robustness archived ledger diagnostics

This directory contains **read-only sensitivity arithmetic** on the unchanged, previously published and audited TRAIL_375 CONTROL CLOSED ledger. No strategy or robot change is authorized.

## Reproduce locally

From repo root, with Python 3:

```bash
python IntradayLab/t3_m15_a6_s1_robustness_v1/robustness.py
```

The standard-library-only script reads `IntradayLab/t3_m15_early_risk_protection_v1/results/control/trades.csv`, asserts original 480 CLOSED control statistics, then overwrites the diagnostic CSV/JSON files under this directory's `results/`. If byte-for-byte verification is required, normalize serialization and rerun on a pinned Python interpreter. Execution of this script was **not** independently recorded in this conversation runtime.

Review `PROTOCOL.md`, `REPORT.md`, and `results/AUDIT_STATUS.json` before interpreting any result.

**Missing for complete Robustness:** independent full causal replay from pinned OHLC, audit of that replay, two fresh full repeats. Current scope explicitly labels these `NOT_RUN` (no fabricated PASS). This is not a complete system-level Robustness acceptance. No Walk Forward, TRUE OOS or LIVE approval.

**2023–2024 DEVELOPMENT_EXPOSED / GROSS_ONLY / COSTS_DEFERRED / NOT_LIVE_READY**.
