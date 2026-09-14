# BBW 03B-2B temporal alignment report — CNYRUBF

**Status: UNRESOLVED**

## Confirmed evidence

The completed local Intel comparison resolves Finam intraday timestamp semantics as **START**. M1→M5, M1→M15, M1→M30, and M1→H1 pass under START; all four END hypotheses fail. This conclusion is retained unchanged.

## Remaining gates

The audit now checks effective-dated first/last M1 session boundaries, clearing intervals, bars outside the allowed sessions, weekend sessions, and the three requested schedule regimes. It also requires every H1 dataset edge to contain exactly the observable session minutes; it neither fills missing minutes nor accepts partial edge candles.

TRADING_DATE remains **UNRESOLVED**. Frozen metadata explicitly requires a versioned MOEX annual/special-day calendar, but that calendar is absent. Consequently weekday-evening and weekend assignments cannot be used to choose TRADING_DATE versus CALENDAR_DATE without inventing a fallback.

The extended runner must be executed on the external, read-only, hash-verified freeze bundle to populate per-date session and H1 evidence. No raw market data is stored or modified here.

## Decision

**UNRESOLVED.** 03B-2B is not ready for normalization. No normalization, synthetic candles, indicators, BBW processing, baseline, optimization, or backtesting was performed.
