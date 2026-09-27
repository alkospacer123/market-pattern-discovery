# BE1 Final C1 Accounting Closeout

## Decision

**T3 was double-charged C1.** `Backtester.profit_R` deducted C1, `_normalize_backtester`
renamed that value `gross_R`, and downstream code deducted `cost_R` again. Historical
T3 therefore stored `raw_R - C1 - C1`; the corrected overlay uses `raw_R - C1`.

The affected scope is v2 and v3 T3 Baseline, Optimization, Robustness, Walk Forward,
and historical OOS on M30 and H1. No phase was rerun. T2 economics are unchanged.

## Economic result

Across the 12 lifecycle/timeframe T3 studies, canonical net R increased by
46.4975892771 R and BE1 net R increased by
46.896654986 R. Corrected BE1-minus-canonical net-R
deltas range from -12.1619664046 R to
5.01803721886 R. Relative evidence remains mixed
across generation, lifecycle, strategy, and timeframe, so the retrospective label is
`MIXED_RETROSPECTIVE_EVIDENCE`; the prior report did not assign an allowed frozen
classification, so this is the final accounting-based classification rather than a
silent rewrite of provenance.

## Path and selection safeguards

Trade paths did not change. Existing BE1 trade/event files remain the certified
causal-path evidence.

Corrected C1 economic interpretation is provided by the compact final accounting overlay.

Candidate identifiers were predeclared without metric ranking and remain frozen. However,
historical optimization/robustness eligibility and lifecycle classifications used the
double-charged metrics, so the conservative selection-impact answer is
`POSSIBLE_SELECTION_IMPACT`; no candidate is altered and no optimization is rerun.

## Final status

* `BE1_CAUSAL_PATH_CERTIFICATION = PRESERVED`
* `T3_C1_ACCOUNTING = CORRECTED`
* `BE1_FINAL_ECONOMIC_AUDIT = PASSED`
* `BE1 = CLOSED`
* `Stage5 = OPEN`
* Next research item: `H4_02_PROFIT_PROTECTION_TRAIL1`
