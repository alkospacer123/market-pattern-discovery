# Genuine scientific core integration

## Baseline and audit

The required baseline is `a6b30f85fe779c611a69f4c30e7261183e3ea3bb`
(merged PR #45).  Before this change the production handlers returned two fixed
labels; the runner ignored those labels, calculated `mean(close.diff())`, and
manufactured an evaluation and knowledge record.  That path was not scientific.

The repository audit found the genuine legacy UNKNOWN engine in
`discovery/unknown.py`: deterministic feature inventory/state construction,
`univariate_screen`, `interaction_search`, `subgroup_discovery`, generic
future-behaviour targets, conditional-versus-baseline effects, day-block
bootstrap, walk-forward stability, coverage/sample eligibility, and
multiplicity-family output.  `features/` supplies causal closed-bar features;
`targets/` supplies target-only future paths.  `orchestration/unknown.py`,
`autonomous.py`, and `worker.py` provide bounded/lazy scheduling and persistent
pattern-effect machinery.  These are scientific primitives.  In contrast,
`backtest/phase6b.py` contains useful causal known-event definitions but its
simulation, stops, targets, PF, expectancy, and trade ranking are downstream
trading primitives and are not used here.

## Production scientific path

The new path is `ResearchCell -> native Finam bars -> causal primary/context
features -> KNOWN/UNKNOWN hypothesis -> Evaluation -> Evidence -> PatternEffect
-> KnowledgeConclusion -> KnowledgeRecord -> ResearchMemory`.  A handler must
return the small `ScientificResult` envelope containing a hypothesis ID plus an
actual `Evaluation` and matching `Evidence`.  Label dictionaries are rejected.
The runner never calculates a substitute effect.

Every identity hashes the complete compact hypothesis definition (cell, track,
method, tested state, target, baseline, timeframe, and context).  Memory stores
Evaluation/Evidence/PatternEffect together in `scientific_findings.jsonl`, and
the knowledge record's `evidence_reference` is that evaluation ID.  Append-once
evaluation and knowledge identities make process restarts deterministic.

## KNOWN and UNKNOWN semantics

KNOWN evaluates one pre-existing causal event family (momentum, trailing narrow
range, or prior-20-bar high break) and conditions it on the direction of fully
closed higher-timeframe context.  It measures the next native bar's signed
return against all eligible baseline observations; it does not assume a
strategy or use profitability.

UNKNOWN preserves the three legacy research-method concepts.  Its bounded
per-cell experiment is selected deterministically from univariate, interaction,
or subgroup discovery and tests causal quantile/context states against the same
behavioural baseline.  It imports no Strategy Knowledge Base and uses no PF,
win rate, expectancy, PnL, stop, or target objective.  The production adapter is
deliberately compact rather than duplicating the batch research framework.

## Timeframes, targets, and causal context

Native sources and the generic closed-bar operations are valid for M1, M5,
M15, M30, H1, and D1, for both CNY/CNYRUBF and Si/USDRUBF.  Intraday targets
reset at the Moscow trading-day boundary.  D1 explicitly uses the documented
cross-day `next_native_bar_signed_return_cross_day_D1` target.  No candles are
resampled or synthesized.

SCALPING retains M1/M5 with M15 context; INTRADAY retains M5/M15/M30 with H1/D1;
MEDIUM_TERM retains the canonical H1/D1 primary and H1/D1 context profile.
Context is aligned only after its legal close.  Every tested state consumes the
mean return of the aligned, fully closed context bars.  Thus context is part of
the hypothesis rather than merely loaded metadata.

## Verification and restart smoke

Focused integration result: `17 passed in 0.90s`.  Full suite:
`315 passed in 26.21s`.

Fresh real-data state: `/tmp/marketai_genuine_science_smoke_001/`, budget one
hypothesis/cell/cycle.  Process A ran five cycles and added 5 cells, 5 genuine
hypotheses, and 5 knowledge records.  After complete process termination,
Process B added another 5 cells, hypotheses, effects, and records.  Final:
10 cells/hypotheses, 6 KNOWN, 4 UNKNOWN (2 univariate, 2 interaction, 0 subgroup
in the naturally scheduled first ten), 10 PatternEffects, 10 KnowledgeRecords,
3 positive, 7 negative, 0 unresolved, and zero duplicate evaluation/knowledge
IDs.  Unresolved persistence is separately covered by focused tests; it was not
artificially manufactured in the real smoke.  Source-file hashes were identical
before and after.

Representative findings (statistics are signed returns):

* KNOWN: Si / Scalping / M1 / M15; `known_event_evaluation`; narrow range plus
  non-negative closed M15 context; target next same-day native-bar return;
  n=85,290; baseline 2.9848310761e-7; conditional -2.1212514024e-7; effect
  -5.1060824785e-7; qualified, negative; evaluation
  `2a086254...fed`; effect `fa370eb2...5b9`; knowledge `1d2e4995...e96`.
* UNKNOWN: CNY / Intraday / M30 / H1,D1; `univariate_screen`; mean fully closed
  context return >=0; n=4,025; baseline 1.7590234777e-5; conditional
  1.7790013433e-5; effect 1.9977865669e-7; qualified, positive; evaluation
  `265f992b...2cc`; effect `2df7d231...ce4`; knowledge `61ba7ac0...4bb`.
* The KNOWN example is also a negative, explicitly context-dependent finding;
  it demonstrates that knowledge is not filtered to positive results.

## Limitations

This bounded production adapter evaluates one hypothesis per ResearchCell visit;
the exhaustive legacy engine remains the place for bootstrap, walk-forward, and
multiplicity-finalization campaigns.  The first ten deterministic smoke cells
did not naturally select subgroup discovery, although production scheduling and
focused tests cover it.  Effect qualification is intentionally a transparent
sample/coverage gate, not a claim of statistical significance.  Equal High/Low
remains excluded because no authoritative causal reference primitive exists.
No Strategy Builder or trading optimization was added.
