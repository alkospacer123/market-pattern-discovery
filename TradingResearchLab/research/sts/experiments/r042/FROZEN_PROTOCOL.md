# TRL-R-2026-042 — Structural retest and volume-dry correction: frozen protocol

**Frozen 2026-11-11, before examining performance of either new signal.** Scope: TRL/ST​S RESEARCH ONLY, MOEX N4, M15, Jan-2023–Sep-2026 YTD, OOS_COMPROMISED. Do not optimize on this sample. The two rules below are distinct from R041 SWEEP_RECLAIM (immediate entry after sweep confirmation) and TWO_LEG_RESET. Mirror all LONG inequalities for SHORT.

Definitions: t is current fully **completed** M15 signal bar; t-1 etc are preceding rows, including previous sessions where not prohibited; a[t]=Wilder ATR14 M15; EMA50[t], EMA200[t] already causally calculated. All windows are only present and earlier bars. Trend LONG = EMA50>EMA200 and EMA50[t]>EMA50[t-4]. SHORT reversed. Decision time t+15 min, entry at physically adjacent next M15 Open only. Weekday signal hours 10:30–16:00 MSK. No same-bar filling at t Close.

**A — RECLAIM_RETEST (Retest after failed-countertrend-breakout).**

1. A prior R041 SWEEP_RECLAIM LONG raw signal was confirmed at one of t-4, t-3, t-2. This preceding signal (event bar s) followed a failed break below a local pullback support, and is observable then. This module does NOT enter on s.
2. Current t and the event bar s belong to same trading session (d.day). On t-1 the market retests the breakout confirmation threshold `level=High[s-1]` (high of the countertrend sweep candle) without invalidating it: `Low[t-1] <= level+0.35*a[t-1]`, `Low[t-1] >= level-0.45*a[t-1]`, `Close[t-1] >= level-0.15*a[t-1]`. All post-event lows from s+1..t-1 must be above `Low[s-1]` (the swept extreme). For SHORT, reference `level=Low[s-1]`, High[t-1] falls within level±0.35/0.45 ATR mirrors, Close[t-1] <= level+0.15ATR, post-event highs below High[s-1].
3. On t, in current EMA50/200 trend direction, close is beyond t-1 high (for LONG) or low (for SHORT); current directional body at least 0.15 a[t]. If multiple s match, emit one signal. The event is separate in time, not an immediate sweep signal.

**B — VOLUME_DRY_RESET (Volatility/volume exhaustion during mild correction).**

1. EMA50/200 trend as above; predecessor impulse LONG `Close[t-4]-Close[t-12] >=1.0*a[t]` (reverse SHORT).
2. Three fully completed corrective candles t-3..t-1 occur in same exchange session as t. Close[t-1]-Close[t-4] for LONG in `[-1.2*a[t], -0.10*a[t]]`; SHORT `[+0.10*a[t],+1.2*a[t]]`. Thus a measurable mild countertrend drift exists, unlike Sideways Shallow.
3. Correction volume dries up: mean `Volume[t-3:t-1]` <= **0.80** times the median of the 20 bars t-23..t-4 (lagged reference; no current candle). Correction's last bar `High[t-1]-Low[t-1] <= 1.1*(High[t-3]-Low[t-3])`. Require all volumes present, strictly positive reference median. Volume ratio is a *proxy* for lower activity, NOT observed order-book liquidity or absorption.
4. t closes beyond highest of t-3..t-1 for LONG (lowest for SHORT), and current directional body >=0.20 a[t]. This uses no future price data. No forced prior-Shallow loser label is allowed for entry gating.

### Test matrix (unchanged once frozen)

- Full standalone R portfolio: BASE and TP6_PROTECT3; C1 (one tick each side), stressed C2 and C4; loss of top five winners and signal distribution by year and symbol.
- Account cash replay: each of three strategies a *separate* account, starting funds 45k, 500k or 1m ₽ each; C1, 2×ATR14 initial stop, 1.5% entry risk of the corresponding account, 6% concurrent account risk, integer lots, <=2 entries/day per robot N4, 1 symbol entry/session, next-open, OHLC stop-first; GO_OCT26 vs GO_NOV26 static proxies. BASE (LIVE reference exits only) separately from experimental TP6R with +3R→+1R next bar.
- Portfolio alternatives: V20=Classic+OBV+Inside; Classic+OBV+A/B (replace Inside); Classic+A/B+Inside (replace OBV); Classic+A+B (replace both). Also check incremental value against existing R041 Two-Leg with Classic+TwoLeg+A/B, marked as *diagnostic prior-candidate comparison*.
- Examine 2025 PF, each year, positive months, closed-trade drawdown, full monthly series, weak-Classic days/months, same symbol/direction holding overlap with Classic/Micro, missing vs covered post-hoc R031 episodes only as diagnostic. Use no post-hoc filtering to select winners.
- Causal pre-entry gate diagnostic: repeat candidate's *complete* replay excluding entry when a frozen Classic position (same symbol, side) is already open at candidate NEXT_OPEN; don't simply delete completed trades. Later Classic entries may overlap. Mark separately as an exploratory diagnostic, not OOS.
- Distinguish real exchange prices, true FINAM costs, historical GO, true MTM drawdown, orders and partial fills from the model: all absent. 2023–2026 extensively used: NOT TRUE OOS. A promising historical candidate is at most CONTINUE_TO_FORWARD, never a LIVE replacement.

Literature is idea motivation only: Al Brooks (2012) *Failed Breakouts, Breakout Pullbacks and Breakout Tests*, DOI 10.1002/9781119202608.ch5; A. Grimes (2012) *Practical Trading Templates*, DOI 10.1002/9781119202837.ch6. Neither documents profitability of these two precise rules on MOEX.

Governance: frozen original V20 and previously accepted STS chronology; no changes to FINAM, tokens, production SQLite, Windows Tasks, live orders, or existing strategies.