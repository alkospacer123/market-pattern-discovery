# Phase 6A — governed strategy and Oracle architecture

## Purpose and relationship to Phase 5B

Phase 6 adds a candidate-to-strategy governance track alongside, and never in
place of, the frozen Phase 5B exhaustive statistical engine. No Phase 5
signature or storage design is changed. Phase 6A contains contracts, registry
metadata, guards, and synthetic tests only: it performs **no profitability
run**, optimization, Oracle calculation, ML fitting, confirmation, or TRUE OOS
access.

## Converging origin tracks

* **KNOWN** records objective human-origin hypotheses.
* **ORACLE** may eventually inspect future path `Y(t)` only as an outcome label
  for causal state `X(t)`. Outcome and predictor namespaces are explicit and a
  hard guard rejects their intersection.
* **ML_DISCOVERY** permits only preregistered interpretable logistic, ensemble
  tree, and gradient-boosting hypothesis generators. Walk-forward fitting,
  deterministic seeds, provenance, importance, path extraction, interaction
  discovery, and simplification are contractual. A fitted model can only emit
  a hypothesis; it cannot become an executable strategy automatically.

All tracks must serialize lineage and converge on the canonical causal strategy
schema. Executability requires causal-validation PASS, including prefix and
future-mutation invariance, session/reference observation times, absence of
Oracle/target fields, deterministic replay, and `m5_close_time <=
m1_close_time`.

## Governed lifecycle

1. Discovery may later use only the preregistered interval
   `[2026-01-05 00:00:00+03:00, 2026-05-16 00:00:00+03:00)` and the DISCOVERY
   role. Parameter count estimation must pass before enumeration.
2. Independent backtests must use explicit commission and slippage references
   and the multi-metric result schema; Profit Factor alone is never a ranker.
3. Robustness reports cost/doubled-cost/slippage stress, entry delay,
   perturbations, plateau breadth, monthly/side/instrument/timeframe stability,
   and walk-forward consistency. Ranking weights, if used later, are transparent
   preregistration inputs—not fitted results.
4. Confirmation accepts only frozen strategies and INTERNAL_CONFIRMATION data.
5. The dormant TRUE OOS final gate accepts only a causal-valid frozen spec with
   frozen discovery and confirmation results. It recomputes SHA-256 and
   hard-fails mutation. Calendar 2025 remains inaccessible outside that final
   mode and is never silently relabelled.

## Anti-overfitting and safety

Domains are intentionally small; deterministic IDs replace UUIDs; ordering and
seeds are explicit; broad parameter plateaus are described rather than an
observed-result score being invented. Source data stays read-only and no real
results belong in architecture files. Future information is a target only,
never an executable predictor. Phase 6B readiness means the architecture is
testable—not permission to bypass preregistration, costs, partitions, or causal
review.
