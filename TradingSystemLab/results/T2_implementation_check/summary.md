# T2 Trend Pullback Continuation v1.0

## Hypothesis
An established trend may offer better entry price and initial risk after a controlled pullback.

## Frozen Rules
H1 only; one position; fixed-risk sizing; parameters are frozen in the manifest.

## Trend Regime
LONG/SHORT requires EMA50 above/below EMA200, ADX(14) > 20, and ATR(14) >= its 20-bar SMA.

## Impulse Definition
At least one of the 10 bars strictly before the pullback is at least 0.5 ATR beyond EMA20 in trend direction.

## Pullback Definition
LONG: Low <= EMA20 and Close >= EMA50. SHORT is exactly mirrored.

## Confirmation
Within the next three bars, Close crosses the already-known previous High/Low and EMA20 in trend direction.

## Initial Stop
Pullback-to-confirmation extreme plus a 0.10 ATR outward buffer; risks over 3 ATR are skipped.

## Exit Logic
Three-ATR causal trailing stop or EMA50 close trend loss; an executable intrabar stop has priority.

## Causality
All inputs are current/past closed H1 bars. Entry is confirmation Close. Calendar 2025+ is hard-blocked.

## Development Coverage
Si and CNY, 2023-01-01 through 2024-12-31 only.

## Implementation Check Results
IMPLEMENTATION_CHECK_ONLY

NO STRATEGY VERDICT
Trades: 95 (LONG 68, SHORT 27).

## Limitations
This is neither optimization nor validation; open positions at sample end are not force-closed.

## Status
STATUS: IMPLEMENTED — NOT YET OPTIMIZED OR VALIDATED
