# M5 candidate robustness validation

Status: `PHASE_M5_ROBUSTNESS_COMPLETE`

This is deterministic, evidence-only robustness analysis. It neither selects a production candidate nor changes strategy or parameters.

## Combined overview

| Slice | Trades | PF | Expectancy R | Net R | Max DD R |
|---|---:|---:|---:|---:|---:|
| Baseline | 1961 | 1.133527094399683 | 0.07046907434064777 | 138.18985478201026 | -46.858478142798795 |
| 10:00–17:00 | 1349 | 1.2997451804824605 | 0.15267973824458642 | 205.96496689194706 | -34.06924628035391 |
| 10:00–17:00 + EMA50 normal | 242 | 1.684634142888469 | 0.3536259961771334 | 85.57749107486629 | -14.788116968467996 |

All results use only the 2023–2024 development period. Calendar 2025 TRUE OOS remained blocked.
