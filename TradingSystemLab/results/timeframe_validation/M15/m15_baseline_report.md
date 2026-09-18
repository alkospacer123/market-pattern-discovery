# M15 Baseline Research

Frozen `T2_candidate_v1` and `T3_candidate_v1` were evaluated on M15 using the unchanged H1 methodology and full 2023–2024 development period.

TRUE OOS is blocked. No optimization, ranking, selection, parameter changes, or strategy changes were performed.

| Strategy | Trades | PF | Expectancy R | Net R | Max DD R |
|---|---:|---:|---:|---:|---:|
| T2 | 384 | 1.5236 | 0.246957 | 94.8313 | -18.0698 |
| T3 | 425 | 1.54244 | 0.237047 | 100.745 | -33.0753 |

T3 H1 context uses exactly four consecutive completed M15 candles, resets daily, and is timestamped at the fourth close.

optimization=false; ranking=false; selection=false; walk_forward=false; true_oos_blocked=true; parameter_change=false; strategy_change=false.

PHASE_M15_BASELINE_COMPLETE
