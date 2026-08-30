# Cycle 15 — Prior-Day High/Low Sweep and Reclaim

Preregistered before any Cycle 15 PnL is computed. This is a separate structural/liquidity hypothesis class, not a parameter rescue of Cycle 14.

## Safety fences

- Research-only.
- Use only CNYRUBF M1 rows with Moscow timestamp `2026-01-05 <= t < 2026-05-16`.
- Retired `2026-05-16` through `2026-07-01` MUST NOT be read or scored.
- 2025 TRUE OOS remains SEALED.
- Any survivor requires genuinely new untouched data before promotion.

## Causal references

- Current trading date uses the immediately preceding available trading date in the permitted dataset.
- Previous-day high (PDH) and low (PDL) are computed from that prior date's CNYRUBF M1 rows with `10:00 <= t < 17:00`.
- PDH/PDL are therefore fully known before the current date starts.
- Signal bars are exact M5 bars made from exactly five expected M1 rows.
- Signal windows: M5 starts `10:00–12:55` and `14:00–16:50` Moscow.
- ATR14 is the same causal exact-session-M5 rolling true-range mean frozen in Cycle 14 runner semantics.

## Sweep/reclaim event

Each current trading date has two independent one-attempt references: PDH for SHORT and PDL for LONG. Each reference can create at most one sweep episode and at most one signal that day.

A sweep starts on the first eligible exact M5 bar satisfying:

- PDH/SHORT: `high >= PDH + sweep_atr * ATR14`.
- PDL/LONG: `low <= PDL - sweep_atr * ATR14`.

The sweep bar is reclaim opportunity zero. A reclaim is valid when a completed exact M5 close returns inside the prior-day boundary by at least `inside_ticks` CNY ticks:

- PDH/SHORT: `close <= PDH - inside_ticks*tick`.
- PDL/LONG: `close >= PDL + inside_ticks*tick`.

If the sweep bar itself reclaims, signal immediately. Otherwise the episode remains pending for at most `reclaim_bars` subsequent eligible exact M5 bars. If no reclaim occurs, the reference is finished for that date; no second attempt is allowed.

## Entry / stop / target

- Signal time = reclaim M5 close.
- Entry = exact next M1 open at signal time; missing row => skip.
- SHORT stop = maximum raw M1 high from sweep onset through reclaim close + `stop_pad_ticks*tick`.
- LONG stop = minimum raw M1 low over the same episode - `stop_pad_ticks*tick`.
- Raw risk must be positive.
- Target is a fixed R-multiple from the exact raw entry and frozen stop: `target_r * risk` in the trade direction.
- STOP_FIRST for same-bar stop/target.
- Adverse stop gap fills raw open; favorable target gap fills frozen target.
- Maximum hold = 120 available same-date M1 rows from entry, force-close before 17:00.
- One open position per candidate; signals while open, including exact prior-exit timestamp, are skipped.

## Frozen grid — exactly 72 candidates

Cartesian product:

- `sweep_atr`: 0.00, 0.25, 0.50
- `reclaim_bars`: 0, 1, 2
- `inside_ticks`: 0, 1
- `stop_pad_ticks`: 1, 2
- `target_r`: 1.5, 2.0

No grid value may be changed after results are seen.

## Friction

CNY tick = 0.001. Raw trade path is invariant.

- GROSS: 0 adverse ticks per side
- BASE: 1 adverse tick per side
- STRESS: 2 adverse ticks per side
- Commission excluded.

Scenario-price adjustment follows the Cycle 14 runner contract.

## Persistent registry rule

Every candidate with BASE PF > 1.0, positive BASE expectancy, and at least 10 executed trades is retained in the persistent profitable-candidate registry even if it fails the strict gate. It is never silently discarded. Gate failures are recorded explicitly.

## Strict research-survivor gate

All required:

- BASE PF >= 2.00
- STRESS PF >= 1.50
- BASE and STRESS expectancy > 0
- >= 30 BASE trades
- >= 15 unique trading days
- >= 3 positive BASE calendar months
- >= 2 positive STRESS calendar months
- largest BASE winning-trade share <= 0.25
- GROSS total bps >= BASE >= STRESS

Rank gate-pass candidates by BASE PF, STRESS PF, BASE expectancy, then trades, then deterministic lexical parameter tie-break.

## Integrity

No future/current-day complete high/low is used. No parameter is selected from Cycle 15 outcomes before the full frozen grid is evaluated. Retired May16–Jul1 and 2025 TRUE OOS remain outside the research process.