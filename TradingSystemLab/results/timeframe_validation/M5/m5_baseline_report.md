# M5 Baseline Research

Frozen `T2_candidate_v1` and `T3_candidate_v1` were evaluated with the unchanged H1 methodology on M5 development data only.

| Strategy | Status | Trades | PF | Expectancy R | Net R | Max DD R |
|---|---|---:|---:|---:|---:|---:|
| T2 | AVAILABLE | 830 | 1.10573 | 0.0610357 | 50.6596 | -56.4226 |
| T3 | AVAILABLE | 1131 | 1.15749 | 0.0773919 | 87.5303 | -42.8122 |

M5 inputs only. Four-bar T3 context resets daily and uses complete, consecutive closed candles.

optimization=false; ranking=false; walk_forward=false; true_oos_blocked=true.

PHASE_M5_BASELINE_COMPLETE
