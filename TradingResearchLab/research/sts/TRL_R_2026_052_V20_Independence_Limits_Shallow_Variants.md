# TRL-R052 — независимость V20, лимитные входы и версии Shallow

**12.11.2026 — research only; LIVE unchanged.** Frozen M15 N4 2023–2026 YTD, cash engine R051 and R045 ledger with 1449 V20 accepted trades, GO Oct static proxy. Source data are overused, NOT TRUE OOS. Full report, Excel and reproducible ZIP delivered in TRL conversation.

## Architecture

All V20 are technical trend following with EMA50/EMA200, ATR, M15 NEXT_OPEN, same broker and shared risk/execution code. Shallow: 8-bar impulse and shallow 3-bar pullback breakout; OBV Pressure: normalized 12-bar signed volume pressure, 10-bar breakout and EMA trend; Inside: previous day's inside structure breakout and EMA trend. Separate FINAM accounts, tokens, processes and logs provide partial operational fault isolation but common API/network/host/market risk remains.

Cash PnL correlation across 3x45k accounts Oct GO TP6: daily Shallow–OBV 0.3435, Shallow–Inside 0.0975; monthly 0.3834 and 0.3268. Daily close correlations do not measure simultaneous open risk. In 7 losing Shallow months OBV and Inside each earned positive monthly PnL in 4; neither guarantees a hedge.

## Frozen Shallow sensitivity

Frozen protocol SHA256 aebf7b16394aada378ce7fba30ee45b4ceb8ab3e7aee1eac4630750e8ff0b385 (before new cash results). Only pullback window or depth modified; all other entry/exit/risk settings unchanged; standalone 45k account TP6+protect3 GO Oct.

| Version | Trades | Net RUB | PF RUB | Closed DD RUB | Daily corr with Classic |
|---|---:|---:|---:|---:|---:|
| Classic 3 bars / 0.85 ATR | 736 | 208507 | 1.961 | 8729 | 1.00 |
| FAST2 2 bars / 0.85 ATR | 851 | 204191 | 1.814 | 7219 | 0.667 |
| LONG5 5 bars / 0.85 ATR | 542 | 139376 | 1.829 | 7427 | 0.486 |
| DEEP3 3 bars / 1.35 ATR | 894 | 225490 | 1.850 | 10411 | 0.843 |
| TIGHT3 3 bars / 0.50 ATR | 486 | 134604 | 1.848 | 7942 | 0.791 |

Three-account portfolio Classic+DEEP3+Inside: +480503 RUB PF1.896 closed DD19408 vs frozen V20 +381608 PF1.845 DD11775 (higher profits but much higher DD, correlated same-direction positions). No candidate dominates by risk; past 2023–2026 selection cannot approve new core. R031 catalogue coverage of previously missed trends is posthoc only.

## Limits: OHLC TOUCH is not fill

Frozen MARKET/NEXT_OPEN baseline 1449 trades. For a passive limit 1 price tick better than next M15 Open: touched within same M15 candle 89.1% N4 / 90.5% GLD (optimistic, unknown latency/order of trades); touched within 4 *subsequent* consecutive M15 bars and before baseline exit, excluding entry candle: 71.5% N4 / 73.1% GLD. This is neither actual fill probability, full fill, nor profit. Marketable cap one tick worse than Open trivially gives 100% touched on opening candle because Open already printed before order arrival; no evidence about execution. Without actual bid/ask, L2 queue, timestamps, per-trade prints, broker partial fills, fees, GO, no trustworthy savings/PnL can be calculated.

Proposed research priorities: best-ask/bid anchored capped marketable LIMIT IOC, passive LIMIT with TTL and cancel, split execution and partial-fill protective SLTP reconciliation, GLD depth cap and skip-if-unfillable logic. Finam docs: https://api.finam.ru/docs/rest/ and https://github.com/FinamWeb/finam-trade-api/blob/main/proto/grpc/tradeapi/v1/orders/orders_service.proto

**Decision:** TP6+protect3 future LIVE implementation is user's decision, but TRL changes nothing. Inside remains the more distinct signal complement to Shallow, but not an operational hedge. Shallow FAST2/DEEP3 archived for prospective validation only. Limit entry claims pending L2/order/fill evidence. Isolated replay 19 CSV byte-for-byte PASS.
