# Scientific depth and balanced discovery integration

## Previous limitation and retained architecture

Production research previously enumerated only return, range, close/high and
context direction states, measured only next-bar signed return, and allowed the
large univariate prefix to delay interactions and subgroups. This integration
extends—not replaces—the existing causal lineage:

`ResearchCell → Hypothesis → Evaluation → Evidence → PatternEffect → KnowledgeRecord`.

The executor rejects metadata-only handler output. An effect can exist only
after qualified evidence for an evaluation that names its hypothesis. An
unqualified evaluation remains useful negative/unresolved scientific memory,
but cannot manufacture a `PatternEffect`.

## Feature inventory

The production inventory is versioned as `scientific-inventory-v1` and spans:

* price behaviour: one-bar return, body/range and close position;
* range: native range and causal within-day range percentile;
* volatility: lagged five-bar return volatility;
* momentum: five-bar close momentum;
* structure: position in the prior 20-bar range and prior-high events;
* context: direction from closed higher-timeframe candles; and
* interactions/subgroups: canonical feature pairs and feature states
  conditioned on context direction.

Rolling range and volatility inputs are shifted before rolling and reset by
Moscow trading date. Higher-timeframe context retains the invariant
`context_close_time <= observation_close_time`. Targets are never admitted as
features.

## Behavioural target families

The versioned `behavioural-targets-v1` family contains future signed return,
future absolute movement (volatility), future range expansion, future
direction, and direction-state transition. Intraday targets require an
observable next bar on the same Moscow trading day; D1 definitions explicitly
permit the next D1 bar. These answer what follows a state and contain no profit
factor, win rate, expectancy, entry, stop, target, or risk/reward objective.

## Statistical qualification

Each evaluation stores sample size, unconditional and conditional statistics,
effect, exact target/state/context/baseline definitions, and four validation
views. It reuses the existing Moscow-date block bootstrap and
Benjamini–Hochberg implementation, adds an explicit zero-effect null
comparison, and evaluates sign stability across three ordered validation
blocks. Evidence qualifies only when sample, practical effect, bootstrap/null
reliability, multiplicity and stability gates all pass. Qualification—not
metadata—is the sole route to a `PatternEffect`.

## Deterministic balanced scheduling and restart

The scheduler has four bounded lanes in fixed order: KNOWN, UNKNOWN univariate,
UNKNOWN interaction, UNKNOWN subgroup. It emits one from each lane before the
next round. Lane and cell order are deterministic; IDs hash full versioned
definitions. On restart the scheduler reconstructs the same streams and skips
hypothesis IDs already in append-only `ResearchMemory`. Evaluation, effect and
knowledge writes are independently idempotent, so the continuation neither
repeats nor bypasses scientific work.

## Multi-horizon preservation

SCALPING uses M1/M5 execution and M15 context. INTRADAY uses M5/M15/M30
execution and H1/D1 context. MEDIUM_TERM uses H1/D1. Thus M1, M5, M15, M30, H1
and D1 remain represented without changing the causal context engine.

## Tests and real-data validation

Automated tests cover inventory depth/versioning, behavioural-only targets,
all four scheduler lanes in the first four positions, restart de-duplication,
bootstrap, ordered stability, BH multiplicity, evidence lineage and the
metadata/direct-knowledge rejection boundary.

The requested fresh-memory validation uses
`/tmp/marketai_scientific_depth_validation_001`, Process A (20 cycles), then a
new runner Process B (20 cycles). Detailed counts and four real examples are
recorded below after the validation run. Source CSV hashes are computed before
and after; market data remains outside and read-only from this repository.

## Validation results and examples

Process A generated/evaluated/recorded 20 hypotheses in 20 bounded cycles.
Process B restarted from the same memory and generated/evaluated/recorded 20
new hypotheses. Final memory contains 3 distinct research cells, 40 hypotheses,
40 evaluations, 20 qualified pattern effects and 40 knowledge records. The
track split is KNOWN 10 / UNKNOWN 30; discovery methods are exactly 10 each for
KNOWN event evaluation, univariate, interaction and subgroup. Conclusions are
5 positive, 15 negative and 20 unresolved. There are zero duplicate hypothesis
IDs, evaluation IDs or knowledge IDs.

All five target families were exercised (signed return 11, volatility 10,
range expansion 7, direction 6, state transition 6). Used features were
return, range, body/range, close position, five-bar volatility, causal range
percentile, five-bar momentum, prior-range position, close/prior-high and
closed context direction. The complete before/after SHA256 manifests of every
source CSV compared byte-for-byte equal.

Representative real descriptive results:

* **KNOWN:** Si, Scalping, M1 with closed M15 context; momentum plus
  nonnegative context; signed-return target; sample 89,367; baseline
  `2.9848310761e-07`; effect `-1.4729177578e-05`; evidence qualified.
* **UNKNOWN univariate:** CNY, Intraday, M30 with closed H1/D1 context;
  return ≥ P05; signed-return target; sample 4,964; baseline
  `1.7590234777e-05`; effect `2.0544936956e-06`; evidence unresolved after
  reliability qualification.
* **UNKNOWN interaction:** CNY, Intraday, M30 with closed H1/D1 context;
  return ≥ P05 plus range ≥ P05; signed-return target; sample 4,746; the same
  baseline; effect `-6.6350963637e-06`; evidence unresolved after reliability
  qualification.
* **UNKNOWN subgroup:** CNY, Intraday, M30 with closed H1/D1 context; return ≥
  P05 conditioned on nonnegative context; signed-return target; sample 3,860;
  the same baseline; effect `-3.6188517254e-06`; evidence unresolved after
  reliability qualification.

These are behavioural measurements, not trading claims or selected strategy
parameters.
