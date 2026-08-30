# Cycle 14 — CNY Session-VWAP Exhaustion/Reclaim

Preregistered before any Cycle 14 PnL is computed.

## Safety fences

- Research-only.
- The runner may read **only** CNYRUBF M1 rows with Moscow timestamp `2026-01-05 <= t < 2026-05-16`.
- `2026-05-16` through `2026-07-01` is retired and MUST NOT be read or scored.
- 2025 TRUE OOS remains SEALED and MUST NOT be opened.
- Any Cycle 14 survivor remains research-only and requires genuinely new untouched data before promotion.

## Why this is a new hypothesis class

Cycles 11–13 concentrated on normalized-state / executable-PnL machine learning and cross-instrument lead-lag. Cycle 14 instead tests a sparse, directly executable intraday microstructure hypothesis: a sufficiently large displacement away from a causal session VWAP followed by a fast reclaim may represent temporary exhaustion rather than continuation.

CNYRUBF is the Cycle 14 target because exact M1 execution data are present for the whole permitted research interval. Instrument choice is fixed before Cycle 14 outcomes are computed.

## Causal data construction

1. Parse only the permitted CNYRUBF M1 interval before any feature is calculated.
2. Decision windows are `10:00–12:55` and `14:00–16:50` Moscow time.
3. Build an M5 signal bar only when all five exact expected M1 rows exist in its five-minute bin.
4. Session VWAP resets at 10:00 each trading date and is cumulative from permitted M1 rows using typical price `(H+L+C)/3` weighted by volume. The 13:00–13:59 rows do not create signals but, when present, remain part of the same causal session VWAP prefix.
5. M5 ATR14 uses only completed M5 bars through the decision bar.
6. M5 efficiency ratio ER30 is `abs(close_t-close_{t-30}) / sum(abs(diff(close)), 30 bars)` and is available only after the current M5 bar closes.
7. No forward-looking feature is allowed.

## Event state machine

For each fixed candidate configuration define signed deviation

`d_t = (M5_close_t - session_VWAP_t) / ATR14_t`.

An excursion begins on the first completed eligible M5 bar for which `abs(d_t) >= k` while that side is armed.

- Positive excursion (`d_t >= k`) seeks a SHORT reclaim.
- Negative excursion (`d_t <= -k`) seeks a LONG reclaim.
- The excursion may last at most `reclaim_bars` valid M5 signal bars.
- A reclaim occurs when a completed M5 close returns to `abs(d_t) <= 0.50 * k` on the same side-to-center path (positive excursion must fall back toward zero; negative excursion must rise back toward zero).
- If no reclaim occurs within the fixed window, that excursion expires and the same side remains disarmed until a completed M5 bar returns to `abs(d_t) < 0.50*k`.
- A successful reclaim also disarms that side until the same reset condition occurs after the trade signal.

Optional preregistered context mode `LOW_ER` requires `ER30 <= 0.45` on the excursion-onset bar. `NONE` applies no ER filter.

## Entry, stop, target, execution

- Signal time is the close of the reclaim M5 bar.
- Entry is the exact next M1 open. If that timestamp is missing, skip the signal.
- LONG stop = minimum raw M1 low from excursion onset through reclaim close minus one CNY tick (`0.001`).
- SHORT stop = maximum raw M1 high over the same episode plus one tick.
- Target is the **frozen signal-time session VWAP**.
- Candidate `rr_min` requires frozen target reward / raw entry risk >= the configured minimum; otherwise skip.
- Stop/target same-M1 tie is `STOP_FIRST`.
- Adverse stop gap fills at raw M1 open; favorable target gap fills at the frozen target.
- Maximum hold is 60 M1 bars; otherwise TIME exit at the available bar close, with force-close no later than 17:00.
- One open position per candidate at a time.

## Frozen candidate grid

Cartesian product, exactly 48 candidates:

- `k`: 1.25, 1.50, 1.75, 2.00
- `reclaim_bars`: 1, 2, 3
- `rr_min`: 1.00, 1.25
- `context`: `NONE`, `LOW_ER`

No values may be added, removed, or changed after Cycle 14 results are seen.

## Friction

CNY tick = `0.001`.

- GROSS: 0 adverse ticks per side
- BASE: 1 adverse tick per side
- STRESS: 2 adverse ticks per side
- commission excluded

PnL is reported in bps relative to raw entry price and also in R where useful.

## Registry policy

Cycle 14 is not allowed to discard profitable but non-passing configurations. Every configuration with `BASE PF > 1.0`, positive BASE expectancy and at least 10 executed trades is written to the persistent profitable-candidate registry with its exact parameters and failure reasons. A strict gate-pass is separately marked `RESEARCH_SURVIVOR`.

## Strict research-survivor gate

A candidate passes only if all are true:

- BASE PF >= 2.00
- STRESS PF >= 1.50
- BASE and STRESS expectancy > 0
- >= 30 BASE trades
- >= 15 unique trading days
- >= 3 positive BASE calendar months
- >= 2 positive STRESS calendar months
- largest BASE winning-trade share <= 0.25
- GROSS total bps >= BASE total bps >= STRESS total bps

Ranking among gate-pass candidates: BASE PF, then STRESS PF, then BASE expectancy, then trades, with deterministic lexical parameter tie-break.

## Research integrity

The Cycle 14 protocol is frozen by this commit before market outcomes for this hypothesis are calculated. No information from retired May16–Jul1 or from 2025 TRUE OOS may influence features, candidate selection, thresholds, ranking, or reporting.