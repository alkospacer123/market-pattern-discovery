# Stage 5 — Separate Validation of Structural Changes

Stage 5 CLOSED. Stage 6 Production Assembly Decision: NEXT.

This directory preserves the artifact-only map of the retrospective Stage 5
program under `CORRECTED_SINGLE_C1`. The canonical comparator authenticated
24/24 studies and 9694/9694 trades with zero trade-level mismatches.

| Step | Evidence | Final status |
|---|---|---|
| Canonical comparator | committed comparator manifest, reconciliation, and independent audit | `STAGE5_CANONICAL_COMPARATOR_INDEPENDENT_AUDIT_PASSED` |
| 5.1 BE1 | `be1/` | CLOSED; `MIXED_RETROSPECTIVE_EVIDENCE` |
| 5.2 TRAIL1 | `trail1/` | CLOSED; `SUPPORTED_RETROSPECTIVELY` |
| 5.3 Risk Cap | `risk_cap/` | `FORMAL_RESEARCH_VERDICT_NOT_ASSIGNED`; terminal censoring preserved |
| 5.4 Minimum Hold | `minimum_hold/` | `DIAGNOSTIC_ONLY_NO_HYPOTHESIS_ADMISSION`; Minimum Hold = NOT_ADMITTED |
| 5.5 Session / Time-of-Day | `session_time/` | `DIAGNOSTIC_ONLY_NO_HYPOTHESIS_ADMISSION`; Session = NOT_ADMITTED |
| 5.6 Correlation / Simultaneous Risk | `correlation_risk/` | `DIAGNOSTIC_ONLY_NO_HYPOTHESIS_ADMISSION`; Correlated-risk grouping = NOT_ADMITTED |
| 5.7 Final Closeout | `stage5_closeout/` | `POST_V3_STAGE_5_FINAL_CLOSEOUT_AUDIT_PASSED` |

The 5.7 closeout authenticates committed artifacts and their declared hashes;
it does not repeat execution or diagnostics. It makes no production assembly,
instrument, timeframe, basket, overlay, session, minimum-hold, threshold, or
group decision and admits no new hypothesis.
