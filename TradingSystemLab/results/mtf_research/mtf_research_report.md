# Phase 7.3 TRUE MTF Research

## Methodology

Frozen T2_candidate_v1 and T3_candidate_v1 parameters were evaluated on development data only. Higher-timeframe trend context filters lower-timeframe execution; no indicator, optimization, or ranking was added.

## Tested timeframe pairs

- H4 → H1
- H1 → M30
- H1 → M15

## Causal MTF rules

Candles are close-labelled. A higher-timeframe candle is aligned only to an execution candle whose open is at or after that higher-timeframe close. Incomplete or non-consecutive aggregation blocks are dropped, and aggregation resets at each Moscow trading-day boundary.

## Result summary

| Pair | Strategy | Status | Trades | PF | Expectancy R | Net R | Max DD R |
|---|---|---|---:|---:|---:|---:|---:|
| H4_H1 | T2 | AVAILABLE | 64 | 2.23415 | 0.634745 | 40.6237 | -12.8673 |
| H4_H1 | T3 | AVAILABLE | 101 | 1.93983 | 0.411465 | 41.5579 | -10.1016 |
| H1_M30 | T2 | AVAILABLE | 174 | 1.94452 | 0.446844 | 77.7509 | -10.6139 |
| H1_M30 | T3 | AVAILABLE | 246 | 1.83594 | 0.372837 | 91.7179 | -15.4567 |
| H1_M15 | T2 | AVAILABLE | 329 | 1.59553 | 0.293002 | 96.3976 | -26.2192 |
| H1_M15 | T3 | AVAILABLE | 379 | 1.6707 | 0.287166 | 108.836 | -29.4324 |

## Limitations

Results cover only Si and CNY development observations from 2023–2024. Missing source resolutions return DATA_UNAVAILABLE; candles are never fabricated. Results are descriptive and are not a production promotion decision.

## Safety

optimization=false; ranking=false; true_oos_blocked=true. Phase 5 and Phase 6 artifact hashes were checked before and after execution.
