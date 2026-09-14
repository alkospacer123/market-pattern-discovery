# R2 Liquidity Sweep / False Breakout v1.0

## Hypothesis
A same-bar sweep and reclaim of a pre-existing price-range boundary may revert toward range equilibrium.

## H1 Range Context
ADX(14) <= 25 and absolute 10-bar EMA200 slope / ATR14 <= 0.35.

## Causal Range Boundaries
Highest High and lowest Low of the previous 20 completed H1 bars (`shift(1)`), with their midpoint.

## M15 Sweep
An M15 extreme penetrates the relevant boundary by 0.05 through 1.00 ATR14_M15.

## Same-Bar Reclaim
The signal M15 Close is strictly back inside the frozen H1 range.

## Rejection Requirement
LONG closes at or above its candle midpoint; SHORT closes at or below it.

## Entry
At the closed signal M15 candle, one position maximum.

## Initial Stop
Signal extreme plus a 0.10 ATR outward buffer; initial risk above 1.50 ATR is skipped.

## Frozen Range Midpoint Target
The entry context midpoint is fixed for the trade and must be on the profitable side of entry.

## Range Failure Exit
A newly completed H1 Close beyond the frozen setup boundary exits at the corresponding M15 Close.

## Time Exit
Exit at the Close of the sixteenth executable M15 bar after entry.

## Multi-Timeframe Causality
Entry sees only H1 closes available at or before M15 bar open; no partial H1 candle is visible.

## Development Coverage
Si and CNY source H1 and M15 data, 2023-01-01 through 2024-12-31. No resampling was used.

## Implementation Check Results
IMPLEMENTATION_CHECK_ONLY

Trades: 173 (LONG 72, SHORT 101; Si 94, CNY 79).

## Limitations
No optimization, parameter search, walk-forward, Monte Carlo, comparison, or edge verdict was performed.

## Status
STATUS: IMPLEMENTED — NOT YET OPTIMIZED OR VALIDATED
