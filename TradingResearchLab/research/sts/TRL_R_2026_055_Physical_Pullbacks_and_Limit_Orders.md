# TRL-R055 — Physical Pullbacks and Finam LIMIT (12.11.2026)

Research-only / no LIVE changes. Frozen protocol SHA256: 8479a8280bdb107015f033c9e0d3791acb0b2e273d3b69077f6ae1497e9d7f63.

Model: SHA-pinned R038/R052 historical N4 M15 engine, 45,000 RUB per independent account, Oct 2026 fixed GO proxy, 1.5% position risk, max 6% account, TP6R + protect at +3R to +1R effective next M15, C1 tick per side, no compounding, 2023–2026 YTD (NOT TRUE OOS).

| Variant | Trades | Net RUB | PF | Closed DD RUB | Non-overlap with Classic Net RUB |
|---|---:|---:|---:|---:|---:|
| Classic |736|208507|1.9614|8729|—|
| PB_ONE3 physical 1 bar, depth .25–1.5 ATR |590|159640|1.8952|15021|−8737|
| PB_TWO3 two contrary bars |187|41551|1.6552|9197|−7843|
| PB_CONSEC2 two consecutive bars |91|17397|1.5691|6745|−6953|
| PB_DEEP3 depth .75–2.25ATR |647|187211|1.9326|13319|+662|
| PB_LONG5 two of five bars, .5–2ATR |445|129317|1.9366|10463|+5211|
| PB_TWO_ADX ADX14>=20 and rising |117|23219|1.6080|8805|−5410|
| PB_TWO_NO_DRIVE |444|73680|1.4920|13810|−4818|
| PB_FIRST_30 after fresh EMA cross |114|18955|1.5417|6308|−3554|

Additional exploratory contiguity test (previous n bars in same day, 15-min adjacent) PB_DEEP3_CONTIG 644/+189284/PF1.953; PB_LONG5_CONTIG 430/+128006/PF1.970 but PF2025 ~1.174 and +5556 RUB net only from positions not overlapping Classic. Older 8-bar swing can cross day boundaries. Do not optimize further on old history.

3 separate 45k accounts, TP6+protect, Oct GO and closed-trade DD: V20 Classic+OBV+Inside +381608 PF1.845 DD11775; Classic+PB_ONE3+Inside +414654 PF1.923 DD15795; Classic+PB_DEEP3+Inside +442224 PF1.937 DD17942; Classic+PB_LONG5+Inside +384331 PF1.939 DD16738. Higher profit from Deep costs ~52% more closed DD and worse PF2025. M15 MTM DD for these new portfolios was NOT calculated.

Nov9–10 user N4 CSV raw signals: no physical candidate USD/CNY/IMOEX; GLD PB_ONE3 three signal bars, PB_DEEP3 two. Prices available only until Nov11 08:30, not the 17:55 screenshot. Physical pullback doesn't capture trends lacking correction.

Official Finam Trade API: https://api.finam.ru/docs/rest/ and https://github.com/FinamWeb/finam-trade-api/blob/main/proto/grpc/tradeapi/v1/orders/orders_service.proto. ORDER_TYPE_LIMIT with TIF DAY/GTC/IOC/FOK, PARTIALLY_FILLED and executed/remaining quantities exposed in proto; instrument-specific support unverified. R055 candidate is ordinary LIMIT DAY with capped BUY price initially at ASK+1 tick or SELL at BID−1 tick, no arbitrary 60-sec expiry; do not carry pending entry after stop/position closed, signal invalidation or session. Existing user 100% position stop NOT modified. Proto explicitly has quantity_sl; actual dynamic fill coverage requires separate READONLY LIVE verification.

M15 post-entry hypothetical LIMIT one tick better than NEXT_OPEN: 1449 historical market trades, later price touch after 1h 71.4%, by session end/before original exit 77.9% (+95 new first touches after 1h). GLD 72.9%→79.9% (+31). These are OHLC TOUCHES, NOT exchange fills or profit estimates. No L2/tick history, FINAM fees or real GO.

Decision: NO_NEW_CORE_APPROVAL / LIMIT_DAY_FORWARD_CANDIDATE / LIVE_UNCHANGED. Full Excel, Markdown, autonomous reproducible ZIP and Journal supplied separately in conversation artifacts; 9 CSV independently repeated byte-identical.
