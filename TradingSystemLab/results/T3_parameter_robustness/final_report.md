# T3 Parameter Robustness

Descriptive sensitivity research only; no parameter selection or ranking. TRUE OOS 2025+ remained blocked.

## Frozen parity and scope
C0/C1 trade-field parity: **PASS** (tolerance `1e-10`). Unique configurations: 47; C0/C1 cost-scenario runs: 94. EMA slope remains the frozen configurable five-H4-bar difference.

## OAT sensitivity
Every tested Donchian, ADX, EMA, ATR-regime, initial-stop, and trailing-stop configuration retained positive C1 expectancy and both LONG and SHORT trades. Stable tested ranges: donchian 10..55; adx 15..30; ema 50..200; atr_regime 10..50; stop_atr 1.5..3.0; trail_atr 2.0..4.0. There is no sign cliff in the declared ranges.

## Local interactions
Entry/risk positive share: 1.000000 (27/27). Regime positive share: 1.000000 (9/9). The frozen baseline is not an isolated local PF/expectancy peak: positive observations exist on both sides of every baseline parameter.

## Consistency
The instrument, year, and direction tables report every unique configuration separately. At the frozen baseline, Si/CNY, 2023/2024, and LONG/SHORT expectancy are all positive; the OAT tables expose the same diagnostics for each sensitivity point.

## Cost robustness
C1 is the primary map. `cost_robustness.csv` additionally reports C0/C1/C2 for the frozen baseline and both declared extremes of every OAT range.

## Final verdict
**ROBUST_PLATEAU**

The edge persists across the complete pre-declared local map rather than only at the frozen point. The next permitted research step is causal walk-forward validation while TRUE OOS 2025+ remains sealed.
