# T3/M15 Stop & Exit v1 — gross-only research

**Goal not reached: no full-period all-four Gross PF ≥2.** S1 increases 2024 R with small 2023 R changes but increases closed-trade DD; S2/S3 do not improve both controls consistently. **COSTS_DEFERRED / GROSS_ONLY / NOT_LIVE_READY.** Draft PR; STOP for external review/user decision, no merge/auto-merge.

Exactly CONTROL, S1 TRAIL_AFTER_1R, S2 BREAK_EVEN_1R and S3 LOCK_1R_AFTER_2R on both fixed controls (ATR trailing 3.0 / 3.5, initial Stop 2 ATR). Original T3/EMA75/H1/ADX14/Donchian20 and all other parameters preserved. No combinations, numeric search or new thresholds.

Starting GitHub main `bc4f95f48b332f43d79ed10f26fc03c5ad01cd97` matched expected main; no changes after it. Read-only data `f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8`. Specifications and source SHAs were committed **before all package replay results** in `d6728adac580070a69c7ea9b33b1f7f9fe59cd73`. Full available 2023–2024 four-instrument prefixes include GLD/IMOEX late starts. Future OHLC is not parsed; 2024 is not independent WF.

Read [EXPERIMENT_REPORT.md](EXPERIMENT_REPORT.md), [INSTRUMENT_DIRECTION_DETAIL.md](INSTRUMENT_DIRECTION_DETAIL.md) and [MONTHLY_DETAIL.md](MONTHLY_DETAIL.md). Machine-readable results are under `results/`; common CLOSED journal, separate CONTROL/S1/S2/S3 journals, terminal OPEN, complete Stop and occupancy paths, metrics, winner/loss lineage, attribution and November sensitivity are included. A6/A7 are immutable copied #495 benchmarks only.

Controls reconcile all **1,442 CLOSED plus two terminal OPEN** against both #490 and #495. Twenty causal tests precede variant outcomes. Separate standard-library raw-prefix replay verifies **5,789 CLOSED, eight OPEN, 109,941 Stop decisions, 16,136 entry decisions and 2,888 central metric rows**, with additional lineage/sensitivity/attribution checks. Direct bytes and SHA comparison of two complete fresh-process repeats is required. [INDEPENDENT_AUDIT.md](INDEPENDENT_AUDIT.md) distinguishes independent implementation from external reviewer independence (PENDING).

Reproduce from repository root, Python 3.12.14 with [requirements.txt](requirements.txt):

```bash
PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s IntradayLab/t3_m15_stop_exit_v1 -p 'test_*.py' -v
PYTHONDONTWRITEBYTECODE=1 python IntradayLab/t3_m15_stop_exit_v1/research.py --data-root /workspace/market-pattern-data --output IntradayLab/t3_m15_stop_exit_v1/work/control --controls-only
PYTHONDONTWRITEBYTECODE=1 python IntradayLab/t3_m15_stop_exit_v1/research.py --data-root /workspace/market-pattern-data
PYTHONDONTWRITEBYTECODE=1 python IntradayLab/t3_m15_stop_exit_v1/audit.py --data-root /workspace/market-pattern-data
MPLCONFIGDIR=IntradayLab/t3_m15_stop_exit_v1/work/mplconfig PYTHONDONTWRITEBYTECODE=1 python IntradayLab/t3_m15_stop_exit_v1/render_report.py
PYTHONDONTWRITEBYTECODE=1 python IntradayLab/t3_m15_stop_exit_v1/verify_repeatability.py --data-root /workspace/market-pattern-data
```

The data root must be pinned and clean. Do not put raw market CSVs in discovery. The runner creates its destination; custom outputs must stay inside this new directory. Repeats require fresh `work/repeat1` and `work/repeat2` directories. `work/` and bytecode are excluded from the PR. Checksums describe this package's source snapshot; after changing source code rerun the primary runner and auditor before comparisons. Presentation changes do not alter strategy rules.

Gross R = direction ×(exit−entry)/abs(entry−initial Stop). Expenses are neither computed nor deducted. Original Close fills and continuous Stop pricing remain unverified execution assumptions. Annual/monthly OPEN counts refer to terminal positions by entry year/month, not historical snapshots. R sums and CLOSED DD are not capital/portfolio returns. [CAUSALITY_REPORT.md](CAUSALITY_REPORT.md).

Only the new `IntradayLab/t3_m15_stop_exit_v1/` changes; all previous research, ROADMAP, TradingSystemLab, source data, production robot, broker configs and real accounts remain unchanged. No Optimization, Robustness, Walk Forward, TRUE OOS, LIVE, merge or auto-merge. External review and the user's decision are the final boundary.
