# Stage 6.7 N4 FULL — final four-case technical closeout

**Status: `STAGE_6_7_N4_FULL_FOUR_CASE_INTERNAL_AUDIT_PASS`** (internal only; external post-merge acceptance remains pending).

## Scope
Exactly four `N4_01` / `FULL` cases are compared: CANONICAL and TRAIL1 at R15 and R20. This is factual analysis, not strategy selection; no composite score or overall winner is produced.

## Data completeness
2023 is retained in the continuous causal path but classified `PARTIAL_N4_DIAGNOSTIC_YEAR`: GLDRUBF begins in July and IMOEXF in November. It is excluded from headline stability and CAGR, with no annual eligibility gate. The authenticated headline endpoint is `2026-09-15T21:00:00+00:00`.

## Annual results and CAGR / DD
| Case | 2024 | 2025 | 2026 YTD | CAGR 2024+ | Max DD | Positive complete quarters | Positive months | Max nominal risk | TW avg risk |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| CANONICAL R15 | 129.88% | 61.02% | 99.12% | 109.13% | -16.34% | 9/10 | 21/33 | 6% | 0.797% |
| TRAIL1 R15 | 165.28% | 74.38% | 88.31% | 122.44% | -19.96% | 10/10 | 23/33 | 6% | 1.024% |
| CANONICAL R20 | 195.58% | 83.99% | 145.50% | 160.44% | -21.27% | 9/10 | 21/33 | 8% | 1.062% |
| TRAIL1 R20 | 256.81% | 104.70% | 127.02% | 182.14% | -25.88% | 10/10 | 23/33 | 8% | 1.364% |

Production sizing remains continuous from baseline through historical TRUE OOS; the 2024 presentation is only a mathematical rebase. CAGR uses actual elapsed time at 365.2425 days/year. Event-level and monthly drawdowns are independently recorded in `headline_comparison.csv`.

## WF24
WF24 is simulated as a separate lifecycle using walk-forward trades only. Its return, drawdown, trade count, and exposure diagnostics are in `wf24_summary.csv` and `wf24_open_risk_summary.csv`.

## Monthly stability
The complete calendar spine has all 33 months from 2024-01 through 2026-09, including zero-exit January 2025. The endpoint month is marked `PARTIAL`. CANONICAL has 21 positive, 1 zero, and 11 negative months; TRAIL1 has 23 positive, 1 zero, and 9 negative months at either risk.

## Quarterly stability
There are 10 complete quarters (2024Q1–2026Q2) and one partial quarter (2026Q3). TRAIL1 has no negative COMPLETE quarter in the 2024 through 2026Q2 headline window; both TRAIL1 risks are 10/10 positive, while both CANONICAL risks are 9/10.

## Exposure
Production exposure is measured only from 2024-01-01 through the authenticated endpoint while preserving pre-2024 equity and open-position state. R15 has a 6% nominal ceiling and R20 an 8% ceiling. Time-weighted values are shown in the headline table; snapshot and threshold diagnostics remain in `open_risk_summary.csv`.

## Instrument diagnostics
Instrument/year signs are diagnostic only and never gate a case. The partial 2023 observations, including TRAIL1 CNYRUBF and GLDRUBF negatives and zero IMOEXF trades, do not reject N4.

## Direction diagnostics
Full-history production LONG/SHORT counts and independently summed net R are reported in `direction_summary.csv`; sizing risk does not alter trade identity.

## R15 vs R20
Within each variant R15 and R20 have identical source trade IDs, timestamps, strategy R, direction, and instrument. R20 increases both CAGR and drawdown/exposure; this is a factual risk-budget trade-off.

## CANONICAL vs TRAIL1
TRAIL1 has higher CAGR at both risk levels and stronger month/complete-quarter sign stability, alongside larger drawdowns and higher time-weighted exposure. CANONICAL R15 has the lowest absolute drawdown.

## Factual leaders
- Highest CAGR: `TRAIL1__N4_01__FULL__R20`.
- Minimum absolute Max DD: `CANONICAL__N4_01__FULL__R15`.
- Quarter stability (tolerance-aware deterministic tie rules): `TRAIL1__N4_01__FULL__R20`.
- Month stability (tolerance-aware deterministic tie rules): `TRAIL1__N4_01__FULL__R15`.
- Highest recovery: `TRAIL1__N4_01__FULL__R20`.
- Highest CAGR / |Max DD|: `CANONICAL__N4_01__FULL__R20`.
- Highest 2025 return: `TRAIL1__N4_01__FULL__R20`.
- Highest 2026 YTD return: `CANONICAL__N4_01__FULL__R20`.
These leaders are metric-specific and are not an automatic production recommendation. The human-retained baseline is `CANONICAL__N4_01__FULL__R15`.

## Reconciliation
The frozen Stage 6.6 trades reconcile to the original Stage 6.7 controls at the separately declared `RECON_TOL=5e-7`; those controls do not establish expected clean-room economics.

## Limitations
2026 is YTD; 2023 has partial N4 availability; this analysis covers only four cases and is historical, with no guarantee of future performance. MAE/MFE are unavailable in the frozen source. Costs are inherited from the authenticated C1 contract. Stage 6.8 was not started and Stage 7 was not executed.
