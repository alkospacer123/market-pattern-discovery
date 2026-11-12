# Frozen R055 rules

Original protocol frozen before any R055 historical PnL computation; original file SHA256 8479a8280bdb107015f033c9e0d3791acb0b2e273d3b69077f6ae1497e9d7f63 (exact original bytes supplied in conversation archive).

Original Classic fixed signal and trade state machine. Physical LONG correction: at least n previous bars with specified opposite-body count, pre-window eight-bar peak to window low ATR14 depth within fixed range; SHORT mirrored; Classic trend EMA50/200 and EMA50 slope, previous impulse drive >1.8 ATR except NO_DRIVE, current bar >previous n highs for LONG/<lows for SHORT, direction body >0.2 ATR and range >0.5 ATR. NEXT_OPEN.

Variants: PB_ONE3 (3 window, 1 contra, depth .25–1.5); PB_TWO3 (3, 2 contra, .35–1.5); PB_CONSEC2 (last two consecutive contra, .35–1.5); PB_DEEP3 (3, 1 contra, .75–2.25); PB_LONG5 (5, 2 contra, .5–2.0); PB_TWO_ADX (PB_TWO3 plus Wilder ADX14 previous close >=20 and rising); PB_TWO_NO_DRIVE (PB_TWO3 without prior impulse); PB_FIRST_30 (PB_ONE3 + directional EMA50/200 crossover in last 30 bars). N4 2023–2026 partial, independent 45k account, Oct GO proxy, TP6+protect3, C1, fixed 1.5% risk and 6% cap; no OOS. Post hoc contiguity recalculation separately marked exploratory. LIMIT review DAY/GTC/IOC/FOK, original 100% position protection unchanged.
