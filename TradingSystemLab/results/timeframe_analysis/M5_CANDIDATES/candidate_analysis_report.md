# M5 candidate hypothesis analysis

Status: `PHASE_M5_CANDIDATE_ANALYSIS_COMPLETE`

This is deterministic, read-only descriptive analysis of already-completed development trades. It is not a backtest, optimization, ranking, candidate selection, or strategy change. Hour subsets are in-sample descriptions and require independent future development before any promotion decision.

## Questions

### 1. Is Session_B the main source of profitability?

Portfolio Session_B has net_R 201.217, PF 1.29083, and 1354 trades, versus total net_R 138.19. This is the largest positive session contribution when compared with the complete session rows; it is evidence of concentration, not a filter decision.

### 2. How much performance comes from Session_C losses?

Session_C contributes net_R -61.4029 across 532 trades. The hypothetical portfolio without Session_C has net_R 199.593; the arithmetic net_R difference is 61.4029 R.

### 3. Are short-duration trades the main degradation source?

Trades below 60 minutes contribute net_R -682.322 across 963 trades (PF 0.123668); 60+ minute trades contribute net_R 820.511 across 998 trades (PF 4.20125). Bucket-level results are retained in comparison.csv.

### 4. Is the effect different between USDRUBF and CNYRUBF?

In Session_C, USDRUBF net_R is -2.04763 (284 trades) and CNYRUBF net_R is -59.3552 (248 trades). The six instrument/session cells show whether the session effect is shared or instrument-specific.

### 5. Which hypotheses deserve promotion to future candidates?

No candidate is promoted or selected in this phase. The session, duration, instrument/session, and time-window hypotheses are documented as evidence-bearing hypotheses for a separately governed future development phase. Session concentration and sub-60-minute degradation merit prospective validation; instrument/session interactions merit validation as a possible moderator. Data-derived profitable-hour sets are explicitly exploratory and carry the highest in-sample overfitting risk.

## Holding bucket reference

- 0-15 min: trades=216, net_R=-207.163, PF=0.0104817
- 15-30 min: trades=304, net_R=-259.548, PF=0.0531509
- 30-60 min: trades=443, net_R=-215.61, PF=0.269453
- 60-120 min: trades=500, net_R=95.2139, PF=1.5456
- 120+ min: trades=498, net_R=725.298, PF=9.86697

No strategy rules, entries, exits, stops, trailing logic, parameters, or research frameworks were modified.
