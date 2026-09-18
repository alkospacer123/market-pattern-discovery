# M5 Walk-Forward Validation

This is sequential validation of frozen hypotheses, not optimization or ranking.

| Candidate | Positive folds | Negative folds | Average expectancy R | Median expectancy R | Development expectancy R | Walk-forward expectancy R |
|---|---:|---:|---:|---:|---:|---:|
| M5_BASELINE | 3 | 0 | 0.07888224137099563 | 0.09073602403638358 | 0.07046907434064777 | 0.07914493903723253 |
| M5_SESSION_CANDIDATE | 3 | 0 | 0.13845142789621775 | 0.1335318749191134 | 0.15267973824458642 | 0.13720199726689516 |
| M5_SESSION_EMA50_NORMAL | 3 | 0 | 0.36157220275161217 | 0.373542664913757 | 0.3536259961771334 | 0.3647007580803406 |

## Diagnostics

Per-fold files report top-1/top-5 positive-R concentration, maximum drawdown, recovery factor, and the longest recovery period. These expose dependence on isolated trades and unrecovered folds.

All results retain the baseline cost-adjusted T2/T3 outcomes. Calendar 2025 TRUE OOS was rejected before output generation.

PHASE_M5_WALK_FORWARD_COMPLETE
