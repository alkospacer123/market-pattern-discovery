# R1 Bollinger False Breakout Mean Reversion v1.0

## Hypothesis
A failed excursion from a range may revert toward its Bollinger equilibrium.

## Frozen Range Regime
ADX(14) <= 20, current BBW <= the median of the previous 100 BBW observations, and absolute 10-bar EMA200 slope / ATR14 <= 0.25.

## Bollinger Excursion
LONG Low < Lower; SHORT High > Upper on a regime-valid closed H1 bar.

## Reclaim
Exactly the next regime-valid bar must close inside the relevant band and beyond the excursion close.

## Entry
At the reclaim-bar Close, with one position maximum.

## Initial Stop
The two-bar extreme plus a 0.10 ATR outward buffer; risk above 2 ATR is skipped.

## Mean Reversion Target
Intrabar execution uses the prior closed bar's Bollinger middle, never the current bar's close-derived value.

## Range Failure Exit
ADX(14) > 25 exits at Close after intrabar exits are checked.

## Time Exit
Exit at the tenth executable H1 bar Close.

## Causality
Closed H1 data only; prior-only percentile window and target; TRUE OOS 2025+ hard blocked.

## Development Coverage
Si and CNY, 2023-01-01 through 2024-12-31.

## Implementation Check Results
IMPLEMENTATION_CHECK_ONLY

Trades: 60 (LONG 29, SHORT 31).

## Limitations
No optimization, walk-forward analysis, cross-strategy comparison, or trading verdict was performed.

## Status
STATUS: IMPLEMENTED — NOT YET OPTIMIZED OR VALIDATED
