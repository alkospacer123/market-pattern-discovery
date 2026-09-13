# T3 Causal Walk Forward Validation

## Frozen Strategy
`T3_MTF_Trend_v1.0` used the frozen Sprint 5 JSON unchanged; no fold selected or adapted parameters.

## Data Coverage
Common causal H1 coverage is 2023-01-03T10:00:00+03:00 through 2024-12-31T00:00:00+03:00 (23 month offsets).

## Fold Schedule
Expanding train, 12-month minimum, three-calendar-month test and step; 3 complete folds. Partial windows are discarded.

## Causality Rules
Every fold starts FLAT. Only entries in `[test_start, test_end)` count. A test entry may close after `test_end` and remains solely in its originating fold. H4 rows are complete four-H1-bar blocks labelled at the final close; indicator warm-up is historical and rolling computations are backward-looking.

## Fold Results
- WF01: C1 PF 0.194498, expectancy -0.576535 R, net -7.494950 R.
- WF02: C1 PF 6.145223, expectancy 1.931504 R, net 23.178045 R.
- WF03: C1 PF 1.945839, expectancy 0.271151 R, net 3.796117 R.

## Aggregate Forward Results
C1: 39 trades, PF 2.092928, expectancy 0.499467 R, net 19.479212 R.

## Cost Robustness
C0/C1/C2 expectancy: 0.518078 / 0.499467 / 0.480856 R. C1 alone determines the verdict.

## Instrument Robustness
See `instrument_report.csv`; the pre-declared conditional 20-trade checks are applied without selection.

## Direction Robustness
See `direction_report.csv`; LONG and SHORT are diagnostics, not selection inputs.

## Year Robustness
See `year_report.csv`, grouped by forward entry year only.

## Fold Concentration
Top-one/top-two positive-R shares are 0.7421235368054663 / 0.9514842749146726.

## MAE/MFE
See `mae_mfe_report.csv`; exit efficiency is diagnostic and trailing parameters were not changed.

## Train vs Test Decay
See `train_test_decay.csv`. Train results are diagnostic only and never enter parameter selection or the verdict.

## Limitations
This is a development walk-forward, not TRUE OOS. TRUE OOS 2025+ was not read or used. The parameter robustness map was performed previously; parameters in this Sprint were completely frozen. Results must not be described as TRUE OOS.

## Final Verdict
**WALK_FORWARD_BORDERLINE**
