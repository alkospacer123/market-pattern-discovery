# Cycle 17 — Opening-Range Breakout Retest Continuation

Preregistered before any Cycle 17 PnL is computed. This tests a breakout-plus-retest mechanism, not the direct ORB formulation from earlier work.

## Safety
- Research-only CNYRUBF M1, Moscow `2026-01-05 <= t < 2026-05-16`.
- Retired `2026-05-16` through `2026-07-01` MUST NOT be read or scored.
- 2025 TRUE OOS remains SEALED.

## Opening range
- Opening range (OR) uses exactly the 15 expected M1 rows from 10:00 through 10:14 on each trading date. Missing any row invalidates that date for Cycle 17.
- OR high/low are fixed after 10:14 and available from 10:15 onward.
- Exact M5 signal bars require all five expected M1 rows.
- Eligible M5 starts: `10:15–12:55` and `14:00–16:50`.
- ATR14 is the causal exact-session-M5 measure frozen previously.

## Breakout and retest state
Each date has independent one-attempt LONG and SHORT sides.

Breakout onset:
- LONG: completed M5 close >= OR_high + `buffer_atr * ATR14`.
- SHORT: completed M5 close <= OR_low - `buffer_atr * ATR14`.

The breakout bar is not a retest bar. Retest must occur within the next `retest_bars` eligible exact M5 bars.

LONG retest requires:
- bar low <= OR_high + `touch_ticks*tick`;
- bar low >= OR_low;
- bar close >= OR_high.

SHORT retest requires:
- bar high >= OR_low - `touch_ticks*tick`;
- bar high <= OR_high;
- bar close <= OR_low.

If no valid retest occurs inside the fixed window, that side is finished for the date. At most one signal per side per date.

## Entry, stop, target
- Signal time = retest M5 close.
- Entry = exact next M1 open at signal time; missing row => skip.
- `RETEST_EXTREME`: LONG stop = minimum raw M1 low from breakout onset through retest close minus one tick; SHORT = maximum high plus one tick.
- `OR_MID`: LONG stop = OR midpoint minus one tick; SHORT = OR midpoint plus one tick.
- Stop must be adverse to exact raw entry.
- Target = fixed `target_r * raw risk` from exact raw entry.
- STOP_FIRST; adverse stop gap at raw open; favorable target gap at frozen target.
- Max hold 120 available same-date M1 rows; no row at/after 17:00.
- One open position per candidate; signals while open, including exact prior-exit timestamp, are skipped.

## Frozen grid — exactly 72 candidates
- `buffer_atr`: 0.00, 0.15, 0.30
- `retest_bars`: 1, 2, 3
- `touch_ticks`: 0, 2
- `stop_mode`: `RETEST_EXTREME`, `OR_MID`
- `target_r`: 1.5, 2.0

No grid modification after outcomes.

## Friction / registry / gate
CNY tick=0.001. GROSS/BASE/STRESS = 0/1/2 adverse ticks per side with frozen scenario-price adjustment.

Retain every candidate with >=10 executed trades, BASE PF>1.0 and positive BASE expectancy. Strict research-survivor gate unchanged: BASE PF>=2.00; STRESS PF>=1.50; positive BASE/STRESS expectancy; >=30 trades; >=15 days; >=3 positive BASE months; >=2 positive STRESS months; largest BASE winner share<=0.25; GROSS total>=BASE>=STRESS.

Any pass remains research-only pending genuinely fresh untouched data.