# Trading Candidate Engine

## Purpose

The trading-candidate layer translates a statistically qualified market effect
into a **trade hypothesis**. It is deliberately not a strategy builder: it
contains no entry, exit, stop, target, sizing, execution, or profitability
selection rules.

## Architecture and lineage

The scientific architecture remains:

`ResearchCell → Hypothesis → Evaluation → Evidence → PatternEffect → KnowledgeRecord`

The new downstream branch is strictly:

`Hypothesis → Evaluation → Evidence → PatternEffect → TradingCandidate`

The generator accepts the complete scientific finding and verifies every ID
link. It rejects a `ResearchCell`, metadata, unqualified evidence, insufficient
samples, missing evaluation lineage, mismatched effects, invalid targets, and
missing causal context. Thus a candidate cannot bypass `PatternEffect`.

## Candidate fields

`candidate_id` is a deterministic hash of the schema, source effect, hypothesis,
market scope, direction, and family. `source_pattern_effect_id` preserves direct
lineage. Market scope includes symbol, research horizon, execution timeframe,
and context timeframes. The scientific basis includes the hypothesis
description, state and target definitions, observed behavior, effect, sample
size, and confidence metadata.

Direction is `LONG` for a positive effect, `SHORT` for a negative effect, and
`UNKNOWN` when a direction cannot yet be assigned. Families are `KNOWN`,
`UNKNOWN_UNIVARIATE`, `UNKNOWN_INTERACTION`, and `UNKNOWN_SUBGROUP`. Lifecycle
values are `CREATED`, `READY_FOR_STRATEGY_SEARCH`, and `REJECTED`; a fully gated
generated candidate is ready for later strategy research. The schema identifier
is `trading-candidate-v1`.

## Memory and restart behavior

`ResearchMemory` appends candidates to `trading_candidates.jsonl`. It reconstructs
the registry on startup and indexes it by deterministic candidate ID. Recreating
an existing scientific effect returns the same ID, and persistence reports a
skip instead of appending a duplicate. Existing events are never rewritten.

## Example

A qualified negative conditional future signed return for Si on M1, evaluated
with causally available M15 context, becomes a `SHORT` trade hypothesis for Si
M1. The candidate explains the observed conditional behavior and retains its
state, target, confidence, and PatternEffect ID. It does not say when to enter,
where to exit, or how much capital to allocate.
