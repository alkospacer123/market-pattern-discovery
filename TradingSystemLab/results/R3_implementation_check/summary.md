# R3 Round Level Rejection v1.0

## Hypothesis
Penetration and same-bar reclaim of a psychological price level may move away from that level.

## Round Level Construction
Decimal floor/ceiling of signal Open; an exact level is both its lower and upper candidate.

## Instrument Level Spacing
Si 0.10 RUB; CNY 0.05 RUB. Execution tick size remains separately configured at 0.001.

## Rejection Definition
LONG opens at/above, penetrates below, and closes above its candidate; SHORT is the mirror.

## Penetration Rules
Inclusive 0.05--0.75 M15 ATR14, without reaching the next full level interval.

## Entry
Signal M15 Close. Exits first become executable on the next bar; one position maximum.

## Initial Stop
Signal extreme plus an outward 0.10 ATR buffer; risk over 1.25 ATR is skipped.

## Structural Target
Frozen midpoint between the rejected level and next level in trade direction.

## Level Failure
A post-entry M15 Close through the rejected level exits at that Close.

## Time Exit
Close of the twelfth executable M15 bar.

## Causality
Only closed M15 bars are signals. Optional H1 values are causally aligned diagnostics and never filters.

## Development Coverage
Si and CNY native M15, 2023-01-01 through 2024-12-31. TRUE OOS 2025+ is hard blocked.

## Implementation Check Results
IMPLEMENTATION_CHECK_ONLY

Trades: 3708 (LONG 1853, SHORT 1855; Si 2493, CNY 1215).

## Limitations
No optimization, parameter search, walk-forward, Monte Carlo, comparison, or trading verdict.

## Status
STATUS: IMPLEMENTED — NOT YET OPTIMIZED OR VALIDATED
