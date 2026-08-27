# Pattern Discovery Protocol v1.0

Phase 5A freezes **how** causal market effects may be discovered; it performs no
real-data search. Every run requires a preregistered experiment, `DISCOVERY`
access, exact frozen input signatures, the research seed, a target family and a
multiplicity family. Unknown discovery and registered known-hypothesis testing
are independent tracks; known concepts never filter unknown search by default.

The canonical baseline is every target-valid row of the same instrument,
timeframe and discovery period. Initial ranking reports effect magnitude,
uncertainty, coverage, fold stability, replication and adjusted evidence as
separate dimensions. It never ranks by strategy results. Generated effect tables
belong in ignored `results/discovery/`; tracked candidates contain full lineage.

Continuous states use target-independent discovery-fit p10/p25/p75/p90 bins and
an explicit `MISSING` state. Natural classes are retained for categorical data.
Pairwise states reuse these bins and stop at 500 feature pairs. Rules have at
most three fixed state conditions. Exact row masks are automatically deduplicated;
overlap and feature/target-family diversity remain descriptive review metadata.

Clustering uses causal features only. Its scaling/imputation parameters are fit
on discovery features, features above 20% missingness are excluded, and its
predeclared k grid is 4/8/12/16. Cluster identity is frozen before outcomes are
evaluated and k cannot be chosen from outcome quality. Motif candidates record
past-to-present state sequences, support, days and overlap policy; uncontrolled
subsequence mining is deferred.

Uncertainty uses 1,000 deterministic whole-Moscow-trading-day bootstrap draws.
Benjamini–Hochberg applies only within the preregistered family. Walk-forward
reports reuse one frozen condition without per-fold retuning. Raw instrument-
scale thresholds are not remapped for replication.

Promotion requires preregistered coverage and day minima, finite uncertainty,
complete multiplicity metadata, at least two same-direction folds, no invalidity,
and a target-family practical effect threshold expressed in behavior units.
Every notable test remains an effect record even when not promoted. A candidate
frozen for confirmation is immutable; a definition change requires a new ID.

Complexity is controlled: univariate work is batched by target family
`O(rows × selected features × selected targets)`, pairwise work is capped,
fixed-depth rules are bounded by preregistration, and each k clustering fit is
`O(rows × selected features × k × iterations)`. No full feature-target-pair
Cartesian product is materialized.
