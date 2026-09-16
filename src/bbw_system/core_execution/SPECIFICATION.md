# BBW CORE v1 execution contract

This package is an isolated research replay. It does not call or modify the
Baseline, Candidate optimization, Robustness, or `bbw_engine` implementations.

## State machine

`Range -> Breakout -> Retest -> Entry -> Structural Stop -> Management -> Exit`

1. **Range:** begins at an H1 squeeze and uses wick highs/lows of preceding,
   same-calendar-day bars. It records high, low, width, bar count, breakout-bar
   ATR, width/ATR, width/price, and squeeze state. Both Candidate ATR limits and
   the optional `max_range_width_atr` / `max_range_width_pct` limits are
   inclusive; the strictest configured ATR maximum wins.
2. **Breakout:** the H1 close must cross the range in its causal trend direction.
   Excess extension (in ATR or range units) and oversized breakout candles are
   rejected. The H1 bar is available only at its close.
3. **Retest:** same-day M15 bars must touch the broken boundary, not close back
   inside it, and respect the Candidate penetration and bar-window limits.
4. **Entry:** confirmation creates an order for the **next M15 open**, never the
   confirmation close. Entry extension is checked again and adverse slippage is
   applied.
5. **Structural stop:** the initial stop is the opposite range boundary plus the
   configured outward offset. A non-positive risk setup is rejected.
6. **Management:** targets are partial exits in initial-R units. After TP1 the
   stop moves to breakeven; after TP2 it locks +1R by default. Optional ATR
   trailing uses an ATR known before the managed candle. Same-bar ambiguity is
   always stop-first.
7. **Exit:** only one position may be reserved at a time. Positions exit at a
   stop, final target, same-day/time limit, or are omitted when the input ends
   before a valid exit. No multi-year `END_OF_DATA` mark is produced. Commission
   and slippage are explicit and included in `result_R`.

All inputs must be strictly increasing START-labelled TRAIN observations before
2025-01-01. Source frames and files are copied/read only, deterministic stable
ordering is used, and output diagnostics identify every terminal rejection.
