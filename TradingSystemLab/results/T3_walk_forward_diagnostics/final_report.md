# T3 Walk-Forward Borderline Diagnostics

## Scope and invariants
Frozen T3 and the existing 39 C1 TEST trades were analyzed unchanged. No signal, parameter, schedule, filter, or exit was modified. TRUE OOS 2025+ stayed closed. Common development coverage is 2023-01-03 through 2024-12-31; a 12-month initial train leaves only 2024 forward evidence (3 folds, 39 trades).

## Classification
**MIXED_EVIDENCE** — sample limitation is fundamental, while material fold/direction dependence remains unresolved. Two of three folds and both instruments are positive in aggregate, but removing WF02 leaves -3.698833 R (-0.136994 R/trade). This is descriptive and is not a basis for selecting folds or SHORT-only trading.

WF01 contains few winners and weakness in both instruments; LONG is weak in WF01 but positive in WF03, while SHORT is strong in WF02 and weak in WF01/WF03. Thus the current sample shows temporal/directional dependence, but not a stable defect demonstrated across adequately sized independent subgroups. All fold×symbol×direction cells are explicitly LOW_SAMPLE.

Entry regime summaries describe distributions only and must not be read as threshold proposals. Exit reasons are reconstructed diagnostically: an execution at the initial stop is `INITIAL_STOP`, worse is `GAP_STOP`, otherwise `ATR_TRAILING_STOP`.

The iid interval is [-0.241861, 1.487828] R with P(mean>0)=0.871400; it is **TRADE_IID_BOOTSTRAP_DIAGNOSTIC_ONLY**, ignores temporal dependence, and is not a significance test. Fold-block output has `VERY_LOW_BLOCK_COUNT`. No p-value is reported for 2 positive / 1 negative folds.

## Main reason and roadmap
WALK_FORWARD_BORDERLINE is primarily constrained by only 39 trades, 3 folds, and one forward calendar year, with meaningful but inconclusive dependence on WF02/direction. **NEXT: T3 Intel Extended Pre-OOS Validation**, solely to resolve ambiguity without optimization; TRUE OOS remains locked.
