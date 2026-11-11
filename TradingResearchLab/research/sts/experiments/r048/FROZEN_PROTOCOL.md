# TRL-R-2026-048 — Early Trend Quality / frozen protocol v1.0

Freeze timestamp: 2026-11-11, after studying R047 but **before** calculating R048 candidate outcomes. RESEARCH ONLY. This test is in-sample, hypothesis generating, not TRUE OOS. November 2026 movements and R031 future-labeled trends were already inspected; no outcome-conditional trade selection is allowed.

## Main hypothesis

R047 EARLY_TREND_RESUME had 822 money trades and PF 1.058 (45,000 RUB account, fixed Oct 2026 GO proxy, TP6+PROTECT3) despite reaching 156/366 retrospectively missed trend episodes. Test whether *ex ante observable* smoothness, confirmed bar acceptance, and moderate relative volatility can reduce whipsaws, then judge whether any variant actually adds independent portfolio value. The gate changes a full replay; NEVER delete losing trades from a completed ledger as if blocked trades had no effect on scheduling or margin.

## Immutable input and execution contract

Reuse R047 hash-pinned, frozen N4 M15 OHLCV, R047 `add_signals` as raw EARLY_TREND_RESUME source, frozen R038/R045 money engine and risk/GO account model. Original Classic and V20 TP6 benchmarks must match: Classic BASE 773 net +505.4766203967774 R; Classic TP6+PROTECT3 808 net +499.2860389864027 R; V20 45/45/45 Oct 2026 GO TP6+PROTECT3 +381,607.6 RUB. 3 independent accounts, each 45,000 RUB, no cross-funding, initial stop 2*ATR14, C1 = 1 tick/side, NEXT_OPEN, first fill stop, weekday, session and daily limits unchanged. GO proxies OCT2026 and NOV2026 are static assumptions, not historic time series. Run both frozen exits BASE and TP6+PROTECT3. Report 2023–Sep 2026 YTD by calendar year/symbol, C2/C4, outlier sensitivity, overlap with Classic, and additional coverage of R031 ex-post missed episodes.

## Exactly four candidate rule variations, fixed upfront

All values computed after M15 bar t has CLOSED, using information up to and including t. No future-label information or future candles may be used in signals. Each candidate is a *strict filter* of R047 EARLY_TREND_RESUME raw signal:

1. **EARLY_ER16**: Kaufman price path efficiency ER16 = |Close[t]-Close[t-16]| / sum_{j=t-15..t} |Close[j]-Close[j-1]| >= **0.40**. Reject if denominator <= 0 or missing. Motivation: directional travel vs whipsaw noise over 4 trading hours.
2. **EARLY_ACCEPT**: on signal candle, directional body / (High[t]-Low[t]) >= **0.55**, AND the close lies within the most favorable **25%** of the bar's range (long: (Close-Low)/(High-Low)>=0.75; short <=0.25). Reject zero range. Motivation: closed-bar breakout acceptance, not a spike that closes in the middle.
3. **EARLY_CALM**: ATR14[t] <= **1.25 × median(ATR14[t-64..t-1])** with all 64 prior observations present. Motivation: avoid taking late/volatile shock breakouts with elevated local risk. No current volatility used in reference median; current ATR is observable at bar close.
4. **EARLY_ER_ACCEPT**: conjunction of predeclared 1 and 2; does not include gate 3.

Raw R047 EARLY_TREND_RESUME retained as control (not retuned). No other thresholds, EMA, volumes, symbols, sessions or exits may be modified after viewing results. Do not make a ranked parameter search. All outcomes must be reported regardless of success.

## Acceptance and caveats

Minimum evidence for `FORWARD_CANDIDATE`: PF >=1.3 on C2 stress AND positive R across at least three calendar years AND incremental full-portfolio benefit (e.g. replacing OBV/Inside at equal 45k/account) without worsening worst year, positive months, and M15-equity risk; also independently observable future data after freeze. Current dataset cannot satisfy the last requirement. Others `REJECT_CORE` or `ARCHIVE_FORWARD`. Very few trades => not enough evidence. A better historical PF alone is **not** a reason to replace LIVE.

Check ex-post missed-event coverage only as a diagnostic label, not a causal entry rule. Assess filtered candidates both against original R047 Early and against actual V20 Shallow+OBV+Inside as benchmark. Source facts vs predictions vs assumptions clearly separated. Record decision in TRL journal. DO NOT modify FINAM, LIVE tasks, tokens, production SQLite or brokerage orders.