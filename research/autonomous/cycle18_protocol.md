# Cycle 18 — Opening-Range False-Break Fade

Preregistered before any Cycle 18 PnL. This is the mean-reversion mirror of Cycle 17, with a distinct false-break mechanism.

## Safety
- Research-only CNYRUBF M1, Moscow `2026-01-05 <= t < 2026-05-16`.
- Retired `2026-05-16` through `2026-07-01` MUST NOT be read/scored.
- 2025 TRUE OOS remains SEALED.

## Opening range and bars
- OR requires exactly the 15 M1 rows 10:00–10:14; OR high/low then freeze.
- Exact M5 requires all five expected M1 rows.
- Eligible M5 starts: `10:15–12:55` and `14:00–16:50`.
- ATR14 is the previously frozen causal exact-session-M5 measure.

## Sweep and false-break reclaim
Each date has one high-side attempt and one low-side attempt.

High-side sweep starts on first eligible M5 with `high >= OR_high + buffer_atr*ATR14`; intended trade after reclaim is SHORT.
Low-side sweep starts on first eligible M5 with `low <= OR_low - buffer_atr*ATR14`; intended trade after reclaim is LONG.

If the same M5 simultaneously satisfies both high- and low-side sweep conditions, both events are treated as ambiguous and both sides are finished for that date without a signal.

The sweep bar is reclaim opportunity zero. A reclaim is valid on the sweep bar or within the next `reclaim_bars` eligible exact M5 bars:

- high-side/SHORT: close <= OR_high - `inside_ticks*tick` and close >= OR_low;
- low-side/LONG: close >= OR_low + `inside_ticks*tick` and close <= OR_high.

If no reclaim occurs by the fixed deadline, that side is finished for the date. At most one signal per side/date.

## Entry / stop / target
- Signal time = reclaim M5 close.
- Entry = exact next M1 open at signal time.
- SHORT stop = maximum raw M1 high from sweep onset through reclaim close + one tick.
- LONG stop = minimum raw M1 low over the episode - one tick.
- Stop must be adverse to exact raw entry.
- Target = fixed `target_r * raw risk` from exact raw entry in fade direction.
- STOP_FIRST; adverse stop gaps at raw open; favorable target gaps at frozen target.
- Max hold = `max_hold` available same-date M1 rows, no row at/after 17:00.
- One open position per candidate; signals while open, including exact prior-exit timestamp, are skipped.

## Frozen grid — exactly 72 candidates
- `buffer_atr`: 0.00, 0.15, 0.30
- `reclaim_bars`: 0, 1, 2
- `inside_ticks`: 0, 2
- `target_r`: 1.5, 2.0
- `max_hold`: 60, 120

No grid modification after outcomes.

## Friction / registry / gate
CNY tick=0.001; GROSS/BASE/STRESS = 0/1/2 adverse ticks per side with frozen scenario-price adjustment.

Retain every candidate with >=10 executed trades, BASE PF>1.0 and positive BASE expectancy. Strict research-survivor gate unchanged: BASE PF>=2.00; STRESS PF>=1.50; positive BASE/STRESS expectancy; >=30 trades; >=15 days; >=3 positive BASE months; >=2 positive STRESS months; largest BASE winner share<=0.25; GROSS total>=BASE>=STRESS.

Any pass is research-only and needs genuinely fresh untouched data.