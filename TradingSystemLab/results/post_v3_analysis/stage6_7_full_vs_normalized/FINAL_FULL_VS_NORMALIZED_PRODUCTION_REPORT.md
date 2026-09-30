# Stage 6.7 — Production equity correction and audit close



## Correction

PR #267 production CAGR, final equity, drawdown, quarter, and month conclusions were invalid because lifecycle-reset equity was stitched together. These corrected figures supersede them. The authenticated R-space economics, 55 configurations, 110 load cases, and Stage 6.6 reconciliation are unchanged.



## Method

Production equity is one causal curve from baseline 2023–2024 into historical OOS 2025–2026 YTD. WF24 is independently simulated from 100 and never enters production return, drawdown, quarter, or month statistics. Same-time exits precede entries, and all same-time entries use identical post-exit equity. Recovery is total compounded return divided by absolute realized-equity maximum drawdown.



## Eligibility

- Eligible equity cases: **44**; ineligible: **176**; unique eligible configurations: **11**.

- Best eligible N2: `TRAIL1__N2_03__NORMALIZED__R15`

- Best eligible N3: `STRUCTURAL_STACK_V1__N3_02__FULL__R20`

- Best eligible N4: `NO_PRODUCTION_ELIGIBLE_N4`



## Target counts

- NORMALIZED: all cases CAGR≥70/80 = 0/0, all-years≥70/80 = 0/0; eligible-only CAGR≥70/80 = 0/0, all-years≥70/80 = 0/0.

- FULL: all cases CAGR≥70/80 = 30/20, all-years≥70/80 = 0/0; eligible-only CAGR≥70/80 = 2/1, all-years≥70/80 = 0/0.



## Evidence

Corrected master metrics, separate production/all-case Pareto sets, failure evidence, drawdown bands, execution hashes, and independent audit results are provided beside this report. Partial inception quarters and 2026 Q3/YTD are excluded from complete-quarter ranking.



## Scope stop

Stage 6.8 was **NOT started**. Stage 7 was **NOT executed**.
