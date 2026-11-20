# TRL-R-2026-050 — Frozen protocol / causal trend-start attempts

**2026-11-11, before first R050 result.** RESEARCH ONLY, no LIVE access or changes.

## Objective

Understand why initial directional breakouts fail, by sampling *all rule-defined attempts*, **not ex-post winners** in R031. Test whether pre-signal market-state variables have useful descriptive association with later outcomes. The output is a diagnostic universe, not a new approved trading system.

## Data and baseline

N4 15-minute historical OHLCV 2023–2026 YTD from existing SHA-pinned R039/R049 local dependency bundle. Frozen Classic 773 BASE +505.4766203967774R / 808 TP6_PROTECT3 +499.2860389864027R, V20 TP6 October proxy 1449 trades +381607.6 ₽. No 2023–2026 TRUE OOS; all old windows repeatedly researched. Nov9–11 2026 seen by researcher, not validation/OOS and excluded from R050 quantitative historical sample. No broker tokens, production DB or LIVE actions.

## Causal attempt universe

For each instrument, closed M15 candle with finite ATR14, historical preceding 16 completed M15 candles, legal Mon–Fri and 10:30–16:00 (Moscow), a valid daily ATR14 and current session opening price, and next adjacent 15min execution candle exists: define bullish attempt when close exceeds the maximum high of **prior 16 bars** by >= 0.05 current ATR14; bearish analog below prior 16 lows. For unambiguous direction, choose only one side per candle; a candle cannot simultaneously satisfy both. To avoid counting the same impulse on every bar, retain **the first qualifying attempt per symbol and session** (both directions compete) independent of any future performance. This universe does NOT include all imaginable trend starts; it is *all events satisfying these explicit rules*, including failed moves. No ex-post R031 trend labels may enter detection or filtering.

Entry at next contiguous M15 open (not candle close); stop 2x ATR14 tick-outward, exit BASE or TP6_PROTECT3 6R TP and +3R to +1R stop executable next bar. One symbol/session; max 2 N4 entries/day per account; C1 1 tick per side; one separate 45k account for the candidate, GO static Oct26 and Nov26 proxies. Report cost C2/C4 on executed trades; no true FINAM fees or actual historical GO. For portfolio compare 3 separate accounts Classic + OBV + candidate vs Classic + candidate + Inside vs frozen Classic+OBV+Inside. No shared funding and no post-hoc risk budget shift.

## Fixed preregistered pre-entry features (evaluated at signal candle close)

1. **PRE_ALIGNMENT:** EMA50 is in signal direction relative to EMA200, and EMA50 direction vs its value 4 candles before is aligned. (No future H1/H4.)
2. **BAR_ACCEPT:** candle close falls in top 25% of candle high-low range in direction of signal (long >=0.75, short <=0.25).
3. **PRE_EFFICIENCY:** abs(previous close - close 12 bars before) / sum(abs(close-to-close changes)) across the 11 intervals ending previous candle; high if >=0.40. All values end at *previous* bar.
4. **DAILY_EXTENSION:** directional distance at signal close from session open / prior completed daily ATR14; stretched if >=0.75, otherwise fresh. Invalid prior ATR excludes event.
5. **VOLUME_SURGE:** current volume >=1.5x median prior 32 bar volumes; descriptive only.

No performance-selected thresholds. Exploratory group contrasts with independent instrument/year and contiguous-month summaries. Avoid claiming significance from many comparisons; do not treat 2025 as a clean OOS. Never filter on future trend labels.

## Strictly frozen two diagnostic entry variants

- `START_ALL`: every initial eligible trend-start attempt (one per symbol/day).
- `START_ACCEPT`: same attempts with `BAR_ACCEPT` and not `DAILY_EXTENSION` (fresh start). This is **predeclared filter**, not tuned, and is not an approved trading model.

Economic replay same engine/risk for both. Both variants have no externally established advantage; if neither beats V20 and stress tests, REJECT_CORE. If metrics are promising, only FORWARD_CANDIDATE, no rollout.

## Outcome labels (analysis ONLY, never features)

Starting at next adjacent M15 candle, look 8 future *contiguous* 15-minute bars **in the same Moscow session/date**; if any gap or date change: outcome=NOT_OBSERVED, exclude from valid outcome denominators. For valid episodes, use signed close change of bar8 relative to entry open / ATR14 at signal (forward8_RATR). Label positive if >=+0.5 ATR, negative if <=-0.5 ATR; otherwise neutral. Separately record `close_reenters_channel` if any of the 8 future completed closes is on the wrong side of prior16-channel breakout line. This does not establish stop-first execution or P&L.

For post-event diagnostics compare where candidate trade happened to overlap an R031 ex-post successful trend separately; never use that catalog for event selection. Also check same-side overlap with executed Classic trades and cumulative candidate returns on days/months when Classic loses. Bootstrap monthly **paired** portfolio delta using 3-month circular blocks 3000 resamples, fixed seed 5049; descriptive only.

## Decision gates

Potential module must (a) have standalone robust net profit after C2/C4, (b) earn profits outside Classic-held positions, (c) improve or justify replacing OBV/Inside in 3-account cash replay, (d) not depend on a few extreme wins, (e) be vetted on future untouched data. Until then `NOT_APPROVED`. KEEP current LIVE V20 as frozen baseline, not claim optimum. All substantial results go to TRL Journal.