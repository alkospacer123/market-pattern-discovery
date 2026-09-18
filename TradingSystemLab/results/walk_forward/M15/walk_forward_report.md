# M15 Causal Walk Forward Validation

Frozen candidates validated independently; this is not a ranking.

| Candidate | Trades | PF | Expectancy R | Net R | Max DD R | Positive folds | Verdict |
|---|---:|---:|---:|---:|---:|---:|---|
| T2_M15_candidate_v1 | 128 | 1.1765602677334752 | 0.08754350492627376 | 11.205568630563041 | -9.808997875599808 | 2/3 | WALK_FORWARD_BORDERLINE |
| T3_M15_candidate_v1 | 160 | 0.9265540842951125 | -0.0423128402859986 | -6.770054445759776 | -31.30136775277552 | 1/3 | WALK_FORWARD_FAIL |

Every fold starts FLAT. Historical data is causal warm-up/context only. H1 C1 is the sole cost model; TRUE OOS remains locked.

PHASE_M15_WALK_FORWARD_COMPLETE
