# Audit protocol

## Review levels

These terms are not interchangeable:

1. **Implementation summary review** reads explanatory prose (README, task/PR
   summary, report narrative, or commit message).  It can restate claims but
   cannot verify implementation or numbers.
2. **Code review** opens the relevant source/configuration and checks logic,
   causality, guards, execution assumptions, determinism, and serialization.  It
   does not prove that committed artifacts came from that code or that their
   numbers are correct.
3. **Artifact audit** opens the actual manifests, ledgers, metrics, grouped
   outputs, and verdicts; checks completeness/provenance; and independently
   recomputes declared values where required.  It does not alone prove all code
   paths are causal or correct.
4. **Full research audit** combines code review and artifact audit, binds them to
   an exact repository commit/config/data provenance, checks methodology and
   protected-tree/determinism evidence, and records discrepancies.  A full audit
   MUST NOT be claimed unless the underlying evidence was actually inspected.

**PR descriptions, Codex summaries, task summaries, README summaries, and commit
messages are not evidence of numerical correctness by themselves.**

## Required evidence for result-producing phases

Inspect, where applicable, and list the exact paths in the audit report:

- relevant runner, strategy, indicator, loader, execution, metric, and
  classification source code;
- configuration files and frozen parameter/candidate/provenance manifests;
- run manifests, data-quality/source hashes, repository commit, and cost model;
- `trades.csv` or the equivalent immutable trade ledgers;
- `metrics.json`, statistics, equity/drawdown inputs, and independently
  recomputed key values;
- complete optimization trials or grouped results rather than only the winner;
- monthly, yearly, instrument, direction, fold, concentration, and sample-size
  outputs required by that phase;
- determinism rerun/diff evidence and protected-tree/hash evidence;
- classification rules and final classification/verdict artifacts.

If an item is not applicable, explain why.  If it is required but unavailable,
the audit is incomplete or failed; a summary cannot substitute for it.  Verify
that source data stayed external/read-only and that no prohibited TRUE OOS range
was admitted.  For MTF work, inspect close-time alignment evidence explicitly.

## Claim labels

Every material audit conclusion should carry one of these labels:

- **VERIFIED_FROM_ARTIFACTS** — the named artifact was opened and its relevant
  content inspected; numerical claims state whether and how they were recomputed.
- **VERIFIED_FROM_CODE** — the named source/config was opened and the stated
  behavior was traced in code; this is not a claim about a particular run.
- **REPORTED_BY_SUMMARY_ONLY** — found only in narrative/metadata and not
  independently substantiated.  It must not be upgraded to “verified.”
- **NOT_VERIFIED** — not inspected, unavailable, out of scope, or unable to be
  established.

Never state that a file, result, rerun, data source, or numerical value was
checked unless it was actually opened and inspected.  Record commands and
recomputation method sufficiently for reproduction.  Failed checks remain in
the report; do not silently narrow the audit population.

## Minimum full-audit record

A full audit records the exact commit and dirty state, phase/candidate identity,
files actually inspected, checks and commands, independently recomputed values
and tolerances, causality/OOS/cost/provenance/determinism conclusions,
discrepancies, final status, and unresolved issues.  Store completed reports
under `audits/` using its README convention; do not create retrospective reports
without evidence.

## Persistent AI operating rule

After every Codex/research task, inspect the actual PR/commit and changed files,
then the relevant source, configs, manifests, generated artifacts, trade ledger
(or equivalent), metrics, and grouped reports.  Independently recompute key
values where applicable and verify methodology compliance before accepting the
task or advancing the roadmap.  A Codex Summary alone is never completion
evidence.  Treat the public Git repository as the primary accessible project
source and record exactly what was inspected.
