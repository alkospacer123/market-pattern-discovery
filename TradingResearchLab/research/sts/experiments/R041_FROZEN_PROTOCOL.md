# TRL-R-2026-041: Two new STS structural correction modules — FROZEN BEFORE BACKTEST

Date fixed: 2026-11-11 | Research-only, no LIVE changes. Data: frozen M15 N4 2023–Sep 2026. This period has extensive previous reuse and is NOT TRUE OOS. No parameter optimization after outcomes.

Architecture: 3 independent accounts, separate starting equity for each strategy; compare current V20 Classic + OBV + Inside to Classic + candidate + Inside, Classic + OBV + candidate, and Classic + candidate A + candidate B. Standalone third-robot placement permitted. No shared capital, no cross-account capital reassignment. Each robot uses original frozen engine: adjacent NEXT_OPEN, 2×ATR14 SL, <=2 entries/day N4 and <=1 symbol/day, 1.5% per account entry, <=6% risk account, integer lots, static GO Oct26 and Nov26, no compounding. Full STOP-FIRST OHLC semantics. Evaluate BASE and TP6_PROTECT3 (+6R TP, after +3R stop +1R next candle), C1=1 tick per side. Record original R039/R040 parity and V20 financial baseline; original V20's actual LIVE exit is BASE, TP6 is experiment.

New hypotheses, both independent raw signals generated solely on completed candles (mirror all inequalities for SHORT). Series indexes t current completed signal M15 bar, t-1 prior bar, t-2 etc; ATR14(t) and M15 EMA50/200 pre-existing from research_extended. Only weekdays, 10:30–16:00 MSK, full bars; same-day constraints as below.

A. `SWEEP_RECLAIM` (failed local break of pullback support)
- Trend LONG: ema50[t] > ema200[t] and ema50[t] > ema50[t-4] (reverse for SHORT); preceding impulse close[t-2] - close[t-10] >= 0.6*ATR[t] (reverse).
- t-1 tests below the *prior* 5-bar low L=min(low[t-6],...,low[t-2]): low[t-1] < L - 0.10*ATR[t-1]; close[t-1] > L; lower wick min(open[t-1],close[t-1])-low[t-1] >=0.20*ATR[t-1]. Mirror using high and upper wick for SHORT.
- t closes above high[t-1] with bullish body close[t]-open[t] >=0.15*ATR[t]. Mirror down for SHORT.
- Bars t and t-1 in same session; t-6 through t-1 are prior complete history but may span sessions. No synthetic future pivot info.
- Economic explanation: failed stop-run against existing trend may exhaust counter-trend liquidity; reclaim may precede trend resumption. This is a hypothesis, NOT a validated institutional stop-flow event; only M15 OHLCV available.

B. `TWO_LEG_RESET` (complex two-legged correction and rebound)
- Same EMA50/200 trend filter and slope as A. Pre-correction impulse close[t-8]-close[t-16] >=0.9*ATR[t] for LONG (reverse for SHORT).
- First trough A=min(low[t-7],low[t-6],low[t-5]); second trough B=min(low[t-3],low[t-2],low[t-1]); intermediate rally top=max(high[t-5],high[t-4],high[t-3]); require B between A-0.15ATR[t] and A+0.60ATR[t]; intermediate top >= A+0.45ATR[t]. For SHORT use maxima (first peak/second peak) and intermediate low.
- Net 7-bar correction: close[t-1] - close[t-7] <=0.25*ATR[t] LONG (reverse SHORT). Signal t closes above max(high[t-2],high[t-1]) and body >=0.15*ATR[t] LONG (mirror SHORT).
- Require t and t-1 share a session, but t-16..t-2 may span sessions. This explicitly detects a multi-wave correction, distinct from 1–2 candle Micro and EMA20 retest.

Test diagnostics: gross/net R, cash PF, ₽ PnL, closed trade DD, 2023/24/25/26 year PF, monthly (+months, weak Shallow months), daily correlation, contemporaneous holding overlaps, marginal difference from replacing OBV/Inside at same bank, 45k/500k/1m, cost stress GLD, independently pass baseline. No tuning or changing formula on 2023–2026 after viewing results; only archive or new hypothesis/version. Not a claim of true OOS, broker-reconstructible GO, commission or MTM.

Research sources motivating different price-structure mechanisms (NOT evidence for N4 specific profitability):
- Adam Grimes, The Art and Science of Technical Analysis (Wiley 2012), Practical Trading Templates, including complex pullbacks and failure tests, DOI https://doi.org/10.1002/9781119202837.ch6
- Al Brooks (2012), Failed Breakouts, Breakout Pullbacks, and Breakout Tests, DOI https://doi.org/10.1002/9781119202608.ch5
- Moskowitz, Ooi, Pedersen (2012), Time Series Momentum, J Financial Economics DOI https://doi.org/10.1016/j.jfineco.2011.11.003