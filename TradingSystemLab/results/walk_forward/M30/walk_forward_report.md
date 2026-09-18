# M30 Causal Walk Forward Validation

Frozen candidates validated independently; this is not a ranking.

| Candidate | Trades | PF | Expectancy R | Net R | Max DD R | Positive folds | Verdict |
|---|---:|---:|---:|---:|---:|---:|---|
| T2_M30_candidate_v1 | 67 | 1.2457337798708468 | 0.11482500641099182 | 7.693275429536452 | -9.206776207327863 | 1/3 | WALK_FORWARD_BORDERLINE |
| T3_M30_candidate_v1 | 60 | 1.8642790304708174 | 0.35876975558775787 | 21.52618533526547 | -8.949224596662896 | 2/3 | WALK_FORWARD_PASS |

Every fold starts FLAT. Historical data is causal warm-up/context only. H1 C1 is the sole cost model; TRUE OOS remains locked.

PHASE_M30_WALK_FORWARD_COMPLETE
