# Stage 6.7 — Final stability and risk audit close



## A. Audit correction

Five defects are closed: authenticated availability now distinguishes zero trades from no coverage; quarter completeness uses registry ranges; the production calendar-month spine retains zero-exit months; exposure processes exits before entries on one continuous production timeline; and the independent auditor reconstructs all blocks. Continuous equity and frozen R-space economics remain unchanged.



## B. Eligibility

- Universe: **55 configurations / 110 R cases / 220 equity cases**.

- Eligible: **16**; ineligible: **204**; unique eligible configurations: **4**.

- Eligible N2/N3/N4 equity cases: **16/0/0**.

- Best eligible N2/N3/N4: `CANONICAL__N2_01__NORMALIZED__R15` / `NONE` / `NONE`.



## C. 70–80% target

- NORMALIZED: all cases CAGR≥70/80 = 0/0, all-years≥70/80 = 0/0; eligible-only CAGR≥70/80 = 0/0, all-years≥70/80 = 0/0.

- FULL: all cases CAGR≥70/80 = 30/20, all-years≥70/80 = 0/0; eligible-only CAGR≥70/80 = 0/0, all-years≥70/80 = 0/0.



**Answer:** No production-eligible case reaches 70% historical CAGR. `NO_CURRENT_CONFIGURATION_MEETS_FULL_PRODUCTION_OBJECTIVE`; the strict gate was not relaxed. Highest eligible CAGR is **60.19%**.



## D. Eligible ≥70% table

`eligible_70plus_comparison.csv` is empty by construction because no eligible case reaches 70%.



## E. Stability

Leader `CANONICAL__N2_01__NORMALIZED__R15` has 10/0/4 positive/zero/negative complete quarters (share 71.43%); 1 partial quarters are diagnostic only. It has 24/3/18 positive/zero/negative months (positive 53.33%, zero 6.67%, negative 40.00%, non-positive 46.67%).



## F. Drawdown

`return_by_drawdown_band.csv` reports eligible counts and stability fields for all six frozen DD bands.



## G. Risk

Leader realized DD is **-6.02%**; maximum reserved open risk is **1.50%**, time-weighted reserved risk **0.17%**, and final equity **192.56**. WF24 exposure is isolated in `wf24_open_risk_summary.csv`.



## H. Diagnostic N4

`NO_PRODUCTION_ELIGIBLE_N4`. `BEST_DIAGNOSTIC_N4` is `TRAIL1__N4_01__FULL__R20` at 133.03% CAGR and is **NOT PRODUCTION ELIGIBLE**.



## I. Final Stage 6.7 conclusion

No current configuration simultaneously passes strict instrument-year positivity and reaches the desired 70–80% historical CAGR. Stability and risk diagnostics remain available without reopening research. Independent audit: **PASS**. `STAGE_6_7_AUDIT_CLOSED`.



## Scope stop

Stage 6.8 was **NOT started**. Stage 7 was **NOT executed**.
