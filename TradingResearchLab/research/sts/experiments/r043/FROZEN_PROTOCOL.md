# TRL-R-2026-043 | STS medium-duration correction modules — FROZEN BEFORE TEST

Frozen at 2026-11-11 (research only). N4 MOEX M15 historical 2023–2026 YTD, OOS_COMPROMISED. No parameter tuning on this sample. Neither candidate is a variation of R041 Two-Leg or R042 Dry Reset, though both retain the economic premise of trend continuation.

All M15 signal indices t refer to FULLY COMPLETED signal bar t. Execute at immediate next physically adjacent M15 Open, with original V20 risk/exit model. For LONG requirements below; SHORT inequalities mirrored. Signal available only on a weekday M15 bar with timestamp 10:30–16:00 Moscow, ATR14 M15>0, directional body >=0.20 current M15 ATR14. Hourly and 4h aggregates are made only from **complete native 4-bar H1 and 16-bar 4h regular-session blocks**, aligned to 10:00 MSK; no partially completed bar used. Both close_time (timestamp of the last M15 bar +15m) <= decision_time (M15 timestamp t+15m) and each aggregate must have full bar count and exactly contiguous native M15 timestamps. They are *session H4* blocks 10:00–14:00 / 14:00–18:00, not exchange-wide clock H4 across evening session. No bar's future high/low is used to form a signal.

## A. H1_H4_LEDGE_RECLAIM (higher-timeframe controlled pullback)

- 4-hour regular-session trend: EMA(close, span=5, adjust=False, min_periods=5) > EMA(close,span=13,min_periods=13) and EMA5(current last completed 4h)>EMA5(2 completed 4h blocks earlier). SHORT reverse.
- H1 regular-session (4 M15) closed bars: EMA8>EMA21 LONG, and most recently COMPLETED H1 close is below H1 EMA8 but not lower than H1 EMA21-0.20*H1 ATR14; H1 ATR14 uses Wilder-style EMA of H1 true ranges, alpha=1/14, min_periods=14.
- H1 controlled ledge: max high of previous three fully closed H1 bars minus latest H1 low lies in [0.40, 2.20] * H1 ATR14. SHORT uses latest H1 high - min low of three recent completed H1 bars, same bounds.
- M15 restart t: close above highest highs of t-1..t-6 for LONG (below lowest lows for SHORT); M15 close direction and body threshold. No explicit M15 EMA50/EMA200 trend filter; MTF trend above defines direction, avoiding mechanically duplicating R026 Deep Pullback rule.

## B. MULTI_SESSION_STAIRCASE (two-day corrective staircase)

- Daily session = M15 10:00–17:45 MSK, at least 24 M15 records, first timestamp 10:00 and final 17:45. Ignore other sessions and invalid session aggregates. Daily close, high, low; daily ATR14 as Wilder EMA over daily true range; EMA8/EMA20 of completed daily closes.
- At signal t, use **only the previous fully completed daily sessions**, p1 yesterday's eligible session, p2 preceding eligible, p3 third preceding, p7 seventh preceding. No future current-session daily summary.
- Daily uptrend: EMA8(p1)>EMA20(p1), EMA8(p1)>EMA8(p3). SHORT reverse.
- Preceding impulse p3 close minus p7 close >=0.70*ATR14(p1), SHORT <=-0.70*ATR14(p1).
- Two-session countertrend correction: close(p2)<close(p3), close(p1)<close(p2), drawdown close(p3)-close(p1) within [0.25,1.60] * ATR14(p1). SHORT reverse.
- Price holds a higher support ledge: low(p1)>=low(p2)-0.25*ATR14(p1), close(p1)>=EMA20(p1)-0.15*ATR14(p1). SHORT mirror using highs and EMA20.
- M15 reacceleration t close above highest high of previous six M15 bars and above close(p1)+0.10*ATR14(p1); directional body >=0.20 M15 ATR14. SHORT symmetric.

## Historical test matrix (immutable)

- Isolated candidates BASE and experimental TP6_PROTECT3 (TP6R, after verified +3R put stop at +1R no earlier than next M15); frozen Classic V20 BASE + TP6 parity.
- 3 **separate** accounts, equal balances 45k / 500k / 1m rub each, frozen position/GO constraints and no transfers, C1 ticks-per-side, stress C2/C4 for standalone R, GO_OCT2026 vs GO_NOV2026 proxy. No compounding. Tests: V20 Classic+OBV+Inside, Classic+OBV+new (replace Inside), Classic+new+Inside (replace OBV), Classic+both new. Includes R041 Two-Leg only as already-studied diagnostic, never claim new OOS.
- Verify each candidate trading signal as of its decision, complete H1/H4/daily source blocks, prefix invariance, costs sensitivity, yearly per-symbol PF and R, top-five winner reliance, overlaps on same side/symbol with Classic/Micro, candidate P&L on historically losing Classic days/months, *causal* pre-entry block when Classic already holds same-symbol same-direction position (full candidate replay).
- Reject as replacement absent positive, credible incremental cash profit, PF, annual robustness, 2025 durability, margins, liquidity/GLD stress and acceptable joint DD. Closed-trade DD != intraday mark-to-market, static GO and C1 != historical FINAM costs. All 2023–2026 repeatedly examined and **NOT TRUE OOS**. Only future time periods after this freeze can supply confirmatory evidence.
- No changes LIVE, FINAM, production SQLite, tokens, orders, schedules, installed strategies. Work only in TRL research copies.
