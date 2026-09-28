# Session / Time-of-Day Diagnostics Report

## 1. Scope
Stage 5.5 describes entry-time associations in existing canonical trades. **NO SESSION SELECTION. NO BEST-HOUR SELECTION. NO CAUSAL SESSION-RESTRICTION CONCLUSION.**

## 2. Prerequisite provenance
The authenticated Stage 3 metadata, Stage 5 comparator (24/24 studies; 9,694/9,694 trades; zero trade mismatches), frozen strategies, and Stage 4 evidence are prerequisites.

## 3. Canonical 9694 reconciliation
All **9,694 / 9,694** T2/T3 M30/H1 rows reconcile under `CORRECTED_SINGLE_C1`.

## 4. Time basis / timezone contract
Time basis is `SOURCE_LOCAL_OFFSET_AWARE_ENTRY_TIME`; observed offset is `+03:00`; timezone conversion is `NONE`. Wall clocks were parsed directly.

## 5. Entry-hour distribution
The report retains all fixed hours 0..23; no outcome-driven binning occurred.

## 6. Hour economics by lifecycle
- Hour 0: 0 negative and 0 positive expectancy cells among 0 sufficiently populated cells.
- Hour 1: 0 negative and 0 positive expectancy cells among 0 sufficiently populated cells.
- Hour 2: 0 negative and 0 positive expectancy cells among 0 sufficiently populated cells.
- Hour 3: 0 negative and 0 positive expectancy cells among 0 sufficiently populated cells.
- Hour 4: 0 negative and 0 positive expectancy cells among 0 sufficiently populated cells.
- Hour 5: 0 negative and 0 positive expectancy cells among 0 sufficiently populated cells.
- Hour 6: 0 negative and 0 positive expectancy cells among 0 sufficiently populated cells.
- Hour 7: 0 negative and 0 positive expectancy cells among 0 sufficiently populated cells.
- Hour 8: 0 negative and 0 positive expectancy cells among 0 sufficiently populated cells.
- Hour 9: 2 negative and 0 positive expectancy cells among 2 sufficiently populated cells.
- Hour 10: 1 negative and 5 positive expectancy cells among 6 sufficiently populated cells.
- Hour 11: 1 negative and 10 positive expectancy cells among 11 sufficiently populated cells.
- Hour 12: 0 negative and 11 positive expectancy cells among 11 sufficiently populated cells.
- Hour 13: 2 negative and 7 positive expectancy cells among 9 sufficiently populated cells.
- Hour 14: 1 negative and 9 positive expectancy cells among 10 sufficiently populated cells.
- Hour 15: 3 negative and 5 positive expectancy cells among 8 sufficiently populated cells.
- Hour 16: 1 negative and 7 positive expectancy cells among 8 sufficiently populated cells.
- Hour 17: 1 negative and 11 positive expectancy cells among 12 sufficiently populated cells.
- Hour 18: 1 negative and 10 positive expectancy cells among 11 sufficiently populated cells.
- Hour 19: 1 negative and 7 positive expectancy cells among 8 sufficiently populated cells.
- Hour 20: 1 negative and 6 positive expectancy cells among 7 sufficiently populated cells.
- Hour 21: 2 negative and 2 positive expectancy cells among 4 sufficiently populated cells.
- Hour 22: 0 negative and 4 positive expectancy cells among 4 sufficiently populated cells.
- Hour 23: 0 negative and 1 positive expectancy cells among 1 sufficiently populated cells.

## 7. T2/T3 and M30/H1
The strategy/timeframe report keeps T2 M30, T2 H1, T3 M30, and T3 H1 separate within each lifecycle.

## 8. FULL / 10–17 / 10–21 descriptive cohorts
Observed-trade counts are FULL=9694, SESSION_10_17=4957, SESSION_10_21=8358. These are fixed descriptive cohorts, not candidates.

## 9. Walk Forward fold diagnostics
WF reconciles to v2=746 and v3=515 across eight generation/fold portfolios; folds remain separate.

## 10. Direction diagnostics
LONG/SHORT composition is published descriptively without selection.

## 11. Instrument diagnostics
Instrument composition is published descriptively without exclusion or a rule.

## 12. Recurrence across generations/lifecycles
Recurrence is a count across 24 fixed parent cells and is neither a score nor leaderboard.

## 13. Small-sample limitations
Every cell below 30 trades is flagged. Sparse hourly results are not stable evidence of a rule.

## 14. No-counterfactual statement
No filtered equity, avoided-trade P&L, portfolio path, or causal re-execution was produced. Existing trades cannot identify the state changes caused by suppressing an entry.

## 15. Stage 4 preservation
`Stage4 Session restriction = NOT_ADMITTED / UNCHANGED`. No H4_04 or hypothesis was created.

## 16. Independent audit status
`STAGE5_5_5_SESSION_TIME_DIAGNOSTICS_COMPLETE`. Every certification check passed independently.

## 17. Conclusion / next roadmap step
Observed entry-time effects are heterogeneous and descriptive only. Stage 5.5 is CLOSED with `DIAGNOSTIC_ONLY_NO_HYPOTHESIS_ADMISSION`; Stage 5 remains OPEN. Next is **5.6 Correlation / simultaneous-risk diagnostics**.
