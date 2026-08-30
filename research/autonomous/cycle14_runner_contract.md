# Cycle 14 — Runner Semantics Freeze

This file resolves implementation details before any Cycle 14 PnL is computed. It does not change the candidate grid or hypothesis.

## Bars and causal features

- Only the already-fenced interval `2026-01-05 <= t < 2026-05-16` may enter memory used by the Cycle 14 runner.
- Session rows are `10:00 <= t < 17:00` Moscow time.
- Exact M5 requires rows at minute offsets 0,1,2,3,4 of the five-minute bin.
- ATR14 is a simple rolling mean of true range over the chronological sequence of exact session M5 bars; it does not reset at the trading-date boundary. The previous exact M5 close is used in true range.
- ER30 is computed over the same chronological exact-M5 sequence and does not reset at the trading-date boundary.
- `NONE` context requires causal VWAP/ATR/deviation availability; `LOW_ER` additionally requires ER30 availability and `ER30 <= 0.45` at excursion onset.

## Excursion state

- State resets at each trading date: both signs start armed and no excursion is active.
- A candidate has at most one active excursion at a time.
- The onset bar itself is not counted as a reclaim bar. `reclaim_bars=1` means the immediately following eligible exact M5 bar is the sole reclaim opportunity.
- Positive reclaim requires `0 <= d_t <= 0.50*k`; negative reclaim requires `-0.50*k <= d_t <= 0`.
- A sign that succeeds or expires remains disarmed. It can re-arm only on a later eligible completed M5 bar satisfying `abs(d_t) < 0.50*k`.
- While one excursion is active, an opposite-side extreme does not create a second simultaneous excursion. The active excursion is evaluated until success or expiry.
- Expiry occurs after the configured number of subsequent eligible M5 reclaim opportunities has been evaluated without success.

## Episode and execution

- Episode raw high/low uses permitted CNY M1 rows from the excursion-onset M5 start through the reclaim M5 decision timestamp, exclusive of the entry row.
- Entry is the exact M1 open whose timestamp equals the M5 decision timestamp.
- The frozen target is the session VWAP value known at the reclaim M5 close.
- Raw risk and reward, before friction, determine `rr_min` eligibility.
- Signals whose exact entry row is absent, whose stop is not adverse to entry, whose target is not favorable to entry, or whose raw reward/risk is below `rr_min` are skipped.
- Trade-path triggers use raw OHLC and frozen raw stop/target. Same-bar stop/target is STOP_FIRST.
- A favorable target gap fills at the frozen target; an adverse stop gap fills at raw open.
- Maximum hold is the first 60 available same-date M1 rows beginning with the entry row. If no stop/target triggers, exit at the close of the last allowed row; no row at or after 17:00 may be used.
- Candidate signals occurring while that candidate already has a position are skipped; a signal at the exact timestamp of the prior exit is also skipped.

## Friction implementation

Raw entry/exit path is invariant across scenarios. Scenario prices are adjusted adversely by whole CNY ticks:

- LONG: adjusted entry = raw entry + f*tick; adjusted exit = raw exit - f*tick.
- SHORT: adjusted entry = raw entry - f*tick; adjusted exit = raw exit + f*tick.

where `f` is 0/1/2 for GROSS/BASE/STRESS and tick=`0.001`. Scenario PnL bps is computed from adjusted prices. This guarantees the intended adverse two-sided friction without changing signal or exit timing.

## Metrics

- Profit factor = sum positive PnL / absolute sum negative PnL; infinite only if losses are zero and gains are positive.
- Expectancy = arithmetic mean trade PnL bps.
- Calendar-month positivity is based on the sum of trade PnL by entry month.
- Largest winner share = largest positive trade / total positive trade PnL.
- Unique trading days are based on entry date.
- Gate and registry tests are applied to executed trades only.