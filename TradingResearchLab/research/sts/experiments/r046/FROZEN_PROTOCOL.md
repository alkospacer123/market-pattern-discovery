# TRL-R046 | Signal-coverage diagnostic and STS new hypothesis — 2026-11-11

STATUS: FROZEN BEFORE FIRST R046 CANDIDATE CALCULATION / RESEARCH-ONLY / NO LIVE.

Inputs: user-supplied October 1–November 11 M15 OHLCV N4 (last observed 11 Nov 08:30 in CSV), independent research M15 OHLCV 2023–Aug/Sep 2026. The user-shared screenshot Nov 11 17:55 is not included in candle files. Timezone exported data not independently verified. 9–10 Nov movement already viewed when proposing rules: it is explicitly **discovery sample**, NOT forward OOS.

Reproduce official historic signal reference SHALLOW_PULLBACK, OBV_PRESSURE, INSIDE_DAY_RELEASE using research_extended.py without modifying thresholds. Check on new files whether their RAW signal bars occur, but this is not an audit of actual production order suppression, session permissions or status. There is no LIVE decision journal in uploaded sources.

**New distinct candidate: STS_DRIVE_CONTINUATION_V1**, a trend continuation after short directional movement, *without requiring a pullback*. Price-only breakout, not OBV volume pressure, not Inside Day, not Micro Shallow (opposing candles), not R039 sideways pause.

Signal at completed M15 candle t:
- Weekday Mon–Fri and time 10:30–16:00 in the timestamps of supplied OHLCV; M15 e50/e200 and ATR14 Wilder (same original frozen research loader), positive/negative direction defined as e50>e200 and e50>e50[t-4] (mirror for short).
- LONG: close[t]>max(high[t-8..t-1]); close[t]-open[t]>=0.18*ATR14[t]; high[t]-low[t]>=0.35*ATR14[t]; close[t-1]-close[t-6]>=0.40*ATR14[t]; 0 <= close[t]-session_open_10AM <= prior completed session daily ATR14; close[t]-EMA50[t] <= 3*ATR14[t].
- SHORT: close[t]<min(low[t-8..t-1]); open[t]-close[t]>=0.18*ATR14[t]; high-low>=0.35*ATR; close[t-6]-close[t-1]>=0.40*ATR; 0 <= session_open_10AM-close[t] <= prior daily ATR14; EMA50[t]-close[t]<=3*ATR14[t].
- No volume filter; no counter-trend candle / two-legged correction requirement. All features through t are closed before NEXT_OPEN; prior daily ATR uses only preceding complete eligible sessions. No current-day future high/low to build signal.
- Engine: one independent virtual module/one account, M15 NEXT_OPEN, max 2 trades/day N4, one per symbol/day, 2*ATR14 SL and tick grid, TP6_PROTECT3 and BASE separately; GO Oct/Nov static proxies 45,000 RUB/account; R039 reference frozen Classic and R041 V20 for portfolio comparison.
- Report raw signals on Nov 9–10 and history; net PnL 2023–2026, by-year, cost sensitivity, holding overlap, and equal-bank Classic+candidate+Inside and Classic+OBV+candidate. Reject or research hold after first test; no adjustment of these thresholds based on results. History 2023–2026 heavily reused, not TRUE OOS; Nov9-10 observed before proposing candidate. Any discovered favorable trend event is NOT approval.