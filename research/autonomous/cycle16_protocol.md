# Cycle 16 — Intraday Compression Breakout Continuation

Preregistered before any Cycle 16 PnL is computed. Separate hypothesis class from Cycles 14–15.

## Safety

- Research-only CNYRUBF M1, Moscow `2026-01-05 <= t < 2026-05-16`.
- Retired `2026-05-16` through `2026-07-01` MUST NOT be read/scored.
- 2025 TRUE OOS remains SEALED.

## Bars and causal compression

- Session rows: `10:00 <= t < 17:00`.
- Exact M5 requires all five expected M1 rows.
- Signal M5 starts: `10:00–12:55` and `14:00–16:50`.
- ATR14 is the causal exact-session-M5 rolling true-range mean already frozen in Cycle 14 runner semantics.
- For a candidate with lookback `W`, the compression window is the immediately preceding W exact M5 bars on the same trading date. They must be contiguous at five-minute spacing; no window crosses the lunch gap or a missing M5 bar.
- Compression high/low are max high/min low of those W bars. `ATR_ref` is ATR14 on the last bar of the compression window.
- Compression qualifies when `(compression_high-compression_low)/ATR_ref <= width_atr`.

## Breakout signal

Current exact M5 is not part of the compression window.

LONG requires:
- current open <= compression_high;
- current close >= compression_high + `breakout_ticks*tick`.

SHORT requires:
- current open >= compression_low;
- current close <= compression_low - `breakout_ticks*tick`.

If both sides could be true on malformed/degenerate data, skip the bar. Signal time is current M5 close. This open-inside/close-outside condition defines a fresh breakout and prevents persistent outside closes from being treated as the same event.

## Entry / risk / exit

- Entry = exact next M1 open at signal time; missing entry => skip.
- `MIDPOINT` stop: midpoint of compression range, shifted one adverse tick beyond the midpoint (`midpoint-tick` LONG, `midpoint+tick` SHORT).
- `OPPOSITE` stop: opposite compression boundary plus one adverse tick (`low-tick` LONG, `high+tick` SHORT).
- Stop must be adverse to exact raw entry or signal is skipped.
- Target = fixed `target_r * raw_risk` from raw entry.
- STOP_FIRST; adverse stop gaps fill raw open; favorable target gaps fill frozen target.
- Max hold 120 available same-date M1 rows from entry; no row at/after 17:00.
- One open position per candidate; signals while open, including exact exit timestamp, are skipped.

## Frozen grid — exactly 72 candidates

- `W`: 4, 6, 8
- `width_atr`: 1.5, 2.0, 2.5
- `breakout_ticks`: 0, 1
- `stop_mode`: `MIDPOINT`, `OPPOSITE`
- `target_r`: 1.5, 2.0

No grid modification after outcomes.

## Friction and registry

CNY tick=0.001; GROSS/BASE/STRESS = 0/1/2 adverse ticks per side using the frozen scenario-price adjustment.

Retain every candidate with >=10 executed trades, BASE PF>1.0 and positive BASE expectancy. Strict research-survivor gate is unchanged: BASE PF>=2.00; STRESS PF>=1.50; positive BASE/STRESS expectancy; >=30 trades; >=15 days; >=3 positive BASE months; >=2 positive STRESS months; largest BASE winner share<=0.25; GROSS total>=BASE>=STRESS.

Any pass is research-only and requires fresh untouched data.