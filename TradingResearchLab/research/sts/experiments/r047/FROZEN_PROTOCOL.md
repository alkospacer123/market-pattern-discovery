# TRL-R-2026-047 — Missed Trend Opportunities / frozen protocol v1

Date: 2026-11-11. STATUS: RESEARCH_ONLY / FROZEN BEFORE FIRST R047 CANDIDATE PNL CALCULATION.

## Goal and controls

Study the 779 retrospective R031 trend episodes, especially 366 with no accepted frozen Classic Shallow entry. Separate (a) no signal (b) raw signal rejected by historical execution restrictions (c) seemingly eligible event with uncertain financial quality. The episode catalog uses future price movement to label a trend and is a **retrospective descriptive diagnostic only**; it must NOT enter candidate signal rules, trading filters, or parameter selection. Events may overlap. 2023–2026 already mined and NOT independent OOS. The new Nov 9–11 screenshots were seen before the rules, so Nov is also NOT independent OOS.

Data/engine: SHA-verified R039 historic N4 M15 OHLCV and frozen `research_extended.py`, R038 `trl_fixed_engine_sts.py` (research-only finance-parameter fork, no LIVE). Preserve exact Classic signal and baseline/parity, account sizing 1.5% per trade, 6% per account, 1 entry/symbol/session, max 2 entries/day/account, weekday-only, NEXT_OPEN, initial stop 2*ATR14, frozen price ticks, C1 one tick per side. Comparison separate BASE and experimental TP6_PROTECT3 (+3R activation, stop to +1R next candle). At 45k RUB per account and Oct/Nov static GO proxy; three standalone independent accounts, no capital transfers. Only if standalone shows useful effect, compare extra banks. Historical costs are not live commissions/slippage/funding and mark-to-market DD is not available for all alternatives here.

### Predefined candidate A: `EARLY_TREND_RESUME` (early directional momentum before EMA alignment)

All signal conditions at fully closed bar t, no future values. Base weekday Mon–Fri, 10:30–16:00 local file candle labels; ATR14>0, EMA50 and EMA200 valid, prior session daily ATR14 valid and session-open 10:00 valid.

LONG: EMA50[t] > EMA50[t-4] (upward slope), EMA50[t] <= EMA200[t] (long regime not yet aligned); Close[t] > EMA50[t]; Close[t]-Close[t-12] >= 1.0*ATR14[t]; Close[t-1]-Close[t-7] >= 0.45*ATR14[t]; Close[t] > max(High[t-1..t-6]); Close[t]-Open[t] >= 0.2*ATR14[t]; 0 <= Close[t]-session_open <= prior_daily_ATR14. SHORT mirror: EMA50 falling but EMA50>=EMA200, close below EMA50, negative 12/6-bar price movements and breakout below prior 6 lows; 0 <= session_open-Close <= prior_daily ATR14. These tests explicitly target episodes before the Classic EMA50/EMA200 full trend confirmation. Initial historical test not licensed for trading or parameter search.

### Predefined candidate B: `TIGHT_DRIFT_BREAK` (directional tight drift, not opposing-candle pullback)

Same weekday/time/valid-data base. All of [t-4..t-1] are within the same instrument session, and reference ATR14[t] positive. Trend LONG EMA50>EMA200 and EMA50[t]>EMA50[t-4], SHORT inverse. Prior four completed bars' max high − min low <= 0.9*ATR14[t]. For LONG Close[t-1]-Close[t-4] in [0.15,0.80]*ATR14[t], for SHORT mirror. Prior close[t-1]-close[t-9] >=0.9ATR14[t] (SHORT mirror). Current Close[t]>max(High[t-1..t-4]) (SHORT below min Low), current directional body >=0.20 ATR14[t], and 0<= directional distance between Close[t] and session_open <= prior_daily ATR14. No volume, no opposite candle prerequisite, no ex-post episode filter. This aims at a narrow **directional** pause rather than R039 mixed sideways or Micro opposite candles.

## Predefined reporting, no retune

1. Raw signals, accepted money trades, rejection reasons, net R, PF R, net RUB, PF RUB, close-only DD, net/year/instrument/month; C1/C2/C4 costs, remove top5 wins, positive months. Test both predefined exits, both GO proxies; 45k account.
2. Coverage of R031 missed episodes: number of distinct ex-post missed events with ≥1 accepted new entry within [start,end] in matching direction, number with ≥1 positive trade and net full-life R, without claiming independent tradable opportunities.
3. Daily P&L correlation vs Classic; overlap as candidate trades with Classic same symbol and direction, including Classic active at candidate entry; on losing Classic days/months; historical portfolio replacement `Classic+candidate+Inside`, `Classic+OBV+candidate`, and all-Shallow `Classic+candidate_A+candidate_B` with separate 45k accounts. Report historical dates 2023–2026 YTD and GO proxy.
4. Causal prefix test of both signal functions on the R039 history; exact baseline Classic 773 BASE and 808 TP6_PROTECT3, and R045 V20 45/45/45 Oct historical +381607.6 RUB TP6 control.
5. Decision REJECT / ARCHIVE_FORWARD / CONTINUE based on marginal portfolio value and concentration, not on percentage of labeled ex-post trends.

No use of broker tokens, production SQLite, real orders, Windows Tasks or LIVE state.