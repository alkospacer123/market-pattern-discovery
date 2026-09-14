# BBW 03B-2B temporal alignment report — CNYRUBF

**Status: UNRESOLVED**

## Confirmed evidence

The completed local Intel comparison resolves Finam intraday timestamp semantics as **START**. M1→M5, M1→M15, M1→M30, and M1→H1 pass under START; all four END hypotheses fail. This conclusion is retained unchanged.

## Remaining gates

The audit now checks effective-dated first/last M1 session boundaries, clearing intervals, bars outside the allowed sessions, weekend sessions, and the three requested schedule regimes. It also requires every H1 dataset edge to contain exactly the observable session minutes; it neither fills missing minutes nor accepts partial edge candles.

TRADING_DATE remains **UNRESOLVED**. The runner now accepts an external `bbw.moex-calendar.v1` artifact containing explicit calendar/trading dates, working-day state, weekend and special/shortened sessions, exchange regimes, session intervals, and provenance. No authoritative artifact was supplied for this rerun. Consequently weekday-evening, weekend, and special-session assignments cannot be used to choose TRADING_DATE versus CALENDAR_DATE without inventing dates or fallback rules.

The extended runner must be executed with both the external, read-only, hash-verified freeze bundle and the authoritative frozen calendar to populate per-date session and H1 evidence, including the 2026-03-23 and 2026-07-14 regime transitions. No raw market data is stored or modified here.

## Decision

**UNRESOLVED.** 03B-2B is not ready for normalization. No normalization, synthetic candles, indicators, BBW processing, baseline, optimization, or backtesting was performed.
