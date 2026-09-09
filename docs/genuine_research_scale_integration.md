# Genuine research-scale integration

## Architecture

Before this change, a `ResearchCell` was scheduled once and its handler chose
one experiment from the cell identity.  Cell completion therefore exhausted a
market scope.  The production path is now:

```
ResearchCell -> lazy bounded hypothesis universe -> HypothesisScheduler
 -> Evaluation -> Evidence -> PatternEffect (only when qualified)
 -> KnowledgeRecord
```

A cell is only a scope (`symbol × horizon × primary timeframe × causal context
× track`).  It is not an experiment and cannot directly create knowledge.

## Hypothesis lifecycle and scheduler

`Hypothesis` captures the cell ID, symbol, horizon, primary and context
timeframes, KNOWN/UNKNOWN track, method, state, behavioural target, baseline,
and contract version.  Its ID is the canonical deterministic hash of those
fields.  It deliberately contains no observed threshold or result, so rerunning
the same scientific question on changed observations cannot change its ID.

Generators yield one object at a time.  UNKNOWN is finite (quantile-state
univariates, cross-feature interactions, and causal-context subgroups) but has
more than one thousand questions per cell.  The scheduler walks cells and
ordinal hypotheses deterministically, accepts a finite budget, and filters the
completed hypothesis IDs loaded from memory.  It neither constructs a Cartesian
universe in RAM nor randomly samples it.

## KNOWN registry

KNOWN is a registry of supported causal primitives rather than strategies:
closed-bar momentum, narrow range, and a prior-20-bar-high interaction, each
conditioned on positive or negative fully closed higher-timeframe context.
There are no entries, exits, stops, profit factor, win rate, expectancy, or
risk/reward objectives.

## UNKNOWN expansion

UNKNOWN lazily combines the existing prepared feature inventory (`return_1`,
native-bar `range`, prior high, and causally aligned context direction) using
the existing method names `univariate_screen`, `interaction_search`, and
`subgroup_discovery`.  Every method asks whether a market state changes a
future native-bar behavioural statistic relative to the unconditional
observable baseline.  Quantile cutoffs are computed only while evaluating the
predeclared state; they do not become identity inputs.

Targets remain next-native-bar returns.  Intraday targets are cleared at the
Moscow trading-day boundary. D1 is explicitly documented as cross-day. Context
alignment continues to enforce `context_close_time <= observation_close_time`.
No candle is synthesized.

## Three-level memory and restart

1. Research attempts retain the cells that have been visited.
2. Each attempt now persists its `hypothesis_id`; `completed_hypothesis_ids()`
   is the restart cursor and deduplication set.
3. Scientific findings persist the complete Hypothesis-reference → Evaluation
   → Evidence → optional PatternEffect lineage, while knowledge references the
   evaluation. An unqualified evaluation has no manufactured effect.

All histories remain append-only. On restart, the same deterministic universe
is regenerated lazily and completed IDs are skipped. Evaluation, effect, and
knowledge identities are deterministic, and memory rejects duplicate writes.

## Real-data smoke test

The smoke used fresh `/tmp/marketai_hypothesis_scale_smoke_001` and the
read-only `/workspace/market-pattern-data` development loader. Process A ran 10
cycles; after it exited, Process B ran 10 more cycles against the same memory.

| Measure | Result |
|---|---:|
| ResearchCells visited | 20 |
| Hypotheses generated/evaluated | 20 / 20 |
| KNOWN / UNKNOWN | 10 / 10 |
| univariate / interaction / subgroup | 10 / 0 / 0 |
| PatternEffects | 20 |
| KnowledgeRecords | 20 |
| positive / negative / unresolved | 6 / 14 / 0 |
| duplicate hypothesis IDs | 0 |
| restart growth | 10 → 20 |

The bounded 20-cycle ordering reached the first ordinal of twenty distinct
cells. Interaction and subgroup execution are therefore demonstrated by the
focused method tests and examples below, not falsely claimed as smoke output.
Bytewise SHA-256 manifests of every source CSV matched before and after.

## Scientific examples (real development data)

All examples are CNY, Scalping, M5 with fully closed M15 context; target is
same-day next-native-bar signed return, baseline sample 31,066, and evidence is
qualified by the shared minimum baseline/conditional sample gate.

* **KNOWN momentum + nonnegative context:** sample 15,409; baseline
  `3.2352994e-06`; conditional `-6.2678910e-06`; effect `-9.5031904e-06`;
  negative conclusion. Hypothesis `4c41618b...c268b92`, evaluation
  `8e444784...ac4ed9`, effect `160fd5ab...eef6e6c`.
* **UNKNOWN univariate** (`return_1 >= P05`): sample 29,505; conditional
  `2.3369530e-06`; effect `-8.9834638e-07`; negative conclusion. Hypothesis
  `71bd6c8d...c4290c8`, evaluation `62ff0bc7...2b86d4d`, effect
  `309b7389...c9ac3`.
* **UNKNOWN interaction** (`return_1 >= P05` + `range >= P05`): sample
  28,319; conditional `1.1665997e-06`; effect `-2.0686997e-06`; negative
  conclusion. Hypothesis `5812ba9c...039a1`, evaluation
  `8eb32232...aa3be`, effect `1ddb096b...64ad6`.
* **UNKNOWN subgroup** (`return_1 >= P05` in nonnegative context): sample
  24,977; conditional `2.8990741e-06`; effect `-3.3622527e-07`; negative
  conclusion. Hypothesis `59a6a616...c4506`, evaluation
  `24b7d03d...86f2c2`, effect `bae851ef...ba60e`.

These are behavioural associations, not trading claims.

## Tests and limitations

Focused tests prove multiple deterministic and distinct hypotheses per cell,
restart continuation, KNOWN multiplicity, all three UNKNOWN methods, forbidden
objective absence, and full lineage. The full suite also covers CNY and Si, all
six native timeframes, causal context, locked TRUE OOS, and source-data loading.

This layer intentionally does not search strategy parameters, establish
causality, or imply economic action. The current production qualification gate
is the existing minimum-sample evidence rule; richer bootstrap, stability, and
multiplicity workflows remain in the separate UNKNOWN discovery pipeline and
are not represented as having run here. Results remain hypothesis-specific
associations requiring replication.
