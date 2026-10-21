# New trend structures M15 — protocol fixed before calculation, 2026-10-20

**Goal**: 1–2 fresh entries/day in N4 portfolio with hard cap 2; local swing/trend held until stop or beginning of third observed session. Desired PF >=1.7 separately in DEV 2023–24 and retrospective LATE 2025–26; not authorized for trading.

Time: original recorded timestamps treated as Moscow by convention, timezone provenance uncertain. Session 09:00 anchor for day indexing, signal M15 opens [10:00,17:00); NEXT adjacent M15 Open only. Stop 2x Wilder ATR14 from executed Open, rounded outward to source tick. Stop-first, adverse Open fills, exit on entry candle, one position/instrument, max one fresh entry/instrument/session; 2 across portfolio. NO TP/trailing. Exit at first observed opening M15 candle on third observed session. C1 proxy: 1 quote tick per side. All four instruments eligible, no results-based omission. 2026 partial.

Eight fixed entry models, no parameter grids:
1. PREVDAY_BREAK — price crosses complete preceding-session high/low in direction of previous session candle and EMA50/EMA200 direction.
2. INSIDE_DAY_RELEASE — preceding completed session is inside preceding-before-it session; release beyond previous high/low aligned EMA50/200.
3. GAP_FOLLOW_30 — 10:30 M15 (open 10:15), positive/negative opening gap >=0.35 ATR at the 10:00 bar versus previous observed session Close, continuation close in same direction, EMA50/200 aligned.
4. FX_PAIR_CONTINUATION — only CNY/USD; both USD and CNY completed M15 EMA50/200 states aligned; both 12-M15 returns same sign, target close crosses 8-M15 prior extreme.
5. BREADTH_RECLAIM — >=3 of observed four instruments agree on completed 16-M15 normalized momentum direction (not guessing missing); target M15 Close crosses EMA20 in breadth direction, EMA50/200 aligned.
6. RELATIVE_LEADER — among contemporaneously observed instruments, target has highest positive 16-M15 momentum/ATR (LONG) or lowest negative (SHORT) with >=2 eligible members; M15 crosses EMA20 in target EMA50/200 direction.
7. H1_RETEST — H1 higher-high/higher-low structure (or bearish converse), price M15 trades through previous completed H1 high/low but closes back in trend direction, EMA50/200 aligned, entry next Open.
8. DAY_COMPRESSION_EXPANSION — previous completed session has total high-low range <0.8 of preceding session range; today close crosses prior session midrange toward yesterday close direction, with EMA50/200 aligned.

No tuning/mutation after results. One test per model, both periods reported regardless of appearance. Historical 2025+ repeatedly seen prior: retrospective, not independent OOS. All charts R are trade-local risk-normalized, not RUB equity/GO. Explicit daily data gaps not filled, completeness tests. Audit by independently reslicing trades along OHLC and signal indexes.
