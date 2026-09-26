# Stage 3C Failure Mechanics Report

## 1. Scope
Diagnostic-only aggregate analysis of 10,993 authenticated normalized trades; no strategy execution, rule simulation, optimization, ranking, or Stage 4 work.

## 2. Prerequisites
Stage 3A is closed and Stage 3B audit passed. All seven normalized hashes and all Stage 3B output hashes were authenticated.

## 3. MAE/MFE semantic verification
Source implementations define MAE and MFE as non-negative adverse/favorable maximum price excursions divided by initial risk. Threshold inference is supported. **MAE_MFE_ORDER_UNAVAILABLE**: excursion ordering and timing are not available.

## 4. MFE threshold outcome diagnostics
Across all separately retained studies, 7337 trades recorded MFE >= 0.5R and 3077 ultimately closed nonpositive; at 1R the counts were 5322 and 1135; at 2R they were 2954 and 54. These facts establish no ordering relative to MAE.

## 5. Winner giveback
Among 4264 positive trades with valid MFE, mean descriptive giveback was 1.5804R and median was 1.4428R. Giveback is not realizable missed profit.

## 6. Losing-trade excursion anatomy
The tables preserve each of 36 parent studies; 6729 trades closed negative.

## 7. Initial-stop mechanics
INITIAL_STOP occurred 1255 times (11.42%); mean final R was -1.0416, mean MAE 0.5899, mean MFE 0.2939, and 5.02% recorded MFE >= 1R.

## 8. Trailing-exit mechanics
Raw exit labels are unchanged. ATR trailing-stop observations are reported separately in `stop_exit_profile.csv`; no counterfactual is calculated.

## 9. Exit efficiency
For 10398 trades with MFE > 0, median uncapped final-R/MFE retention was -0.3012; negative values are retained.

## 10. Holding-time failure mechanics
The exact Stage 3B fixed buckets are used. Outcomes, excursion, giveback, and MFE>=1R/final<=0 shares are descriptive only.

## 11. Loss streaks
The longest parent-bounded loss streak was 16 trades; the worst parent-bounded streak totaled -13.3573R. Ordering is exit time, entry time, then canonical key.

## 12. Loss concentration
Across parent studies, the maximum worst-single-loss share was 9.26%, and maximum worst-ten share was 76.34%.

## 13. Instrument/direction recurrence
Stage 3B instrument and direction aggregates remain the compact reference. Stage 3C does not mine additional dimensions.

## 14. Repeated diagnostic patterns
`FM_MFE1_FINAL_NONPOSITIVE` is recorded as a **REPEATED_DIAGNOSTIC_PATTERN** where parent rows show nonzero MFE>=1R/final<=0 counts across generations including TRUE OOS. Magnitudes and samples are in the threshold table; the limitation is unavailable path order.

## 15. Cross-lifecycle recurrence
Baseline, walk-forward, and TRUE OOS remain separate rows; no lifecycle pooling or robustness score occurs.

## 16. Cross-generation recurrence
v1 perpetual, v2 quarterly, and v3 perpetual remain separate. Their universes and samples differ.

## 17. Limitations
MAE/MFE lack event order and timing. Diagnostics are observational, not causal, and do not establish realizable alternative exits. Negative is a subset of nonpositive, not an additive partition.

## 18. Handoff to Stage 3D
Stage 3C provides audit-ready facts only. No Stage 3D or Stage 4 work is performed.
