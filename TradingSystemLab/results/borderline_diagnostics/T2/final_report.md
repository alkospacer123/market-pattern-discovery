# T2_candidate_v1 — Phase 4.1 Borderline Diagnostics

## Classification

**SAMPLE_LIMITED**

The observed aggregate edge is positive and survives every leave-one-fold-out case, but **does not survive removal of the five best trades**. Both instruments and both directions have positive expectancy. It is not declared TRUE-OOS-ready because only 33 forward trades exist (below the predeclared 50-trade minimum) and every fold is marked incomplete in the Phase 4 artifact. This is a sample/coverage limitation, not a strategy rejection.

## Findings

- Strongest fold: **WF04** (17.482 net R); weakest: **WF01** (-3.499 net R).
- Single-fold dependency: **false** (strongest-fold share 64.9%).
- Instrument stability: **instrument independent**. Direction stability: **both directions contribute**.
- Temporal pattern: **one regime-dependent quarter**; the negative WF01 result followed positive quarters, indicating a possible **regime mismatch** rather than monotonic decay.
- Bootstrap P(mean R > 0): **97.1%** (10,000 deterministic resamples; diagnostic only, not a significance test).
- The 2023 training trade count and net R cannot be reconstructed from the allowed Phase 4 artifacts; only its persisted expectancy is reported. No market data, strategy code, Phase 3 artifacts, or TRUE OOS data were read.

No strategy change, parameter optimization, candidate selection, or ranking was performed.
