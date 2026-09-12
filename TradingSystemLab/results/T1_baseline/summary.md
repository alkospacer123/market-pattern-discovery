# T1 frozen baseline

`T1_BBW_Donchian_v1.0`, Si and CNY, H1, 2023–2024. Parameters are frozen in
`configs/T1_BBW_Donchian.yaml`; no optimization was performed. C0 uses zero cost,
while costs and slippage remain configurable in the shared backtester.

* Trades: 28
* LONG / SHORT: 14 / 14
* PF: 0.805455
* Expectancy: -93.885216
* Average R: -0.088324
* Max DD: -6283.012046
* Net profit: -2628.786043

Calendar 2025+ was neither selected nor read. Open positions at sample end remain
unrealized. Signal-candle entries use the close; trailing updates become active on
the next bar because OHLC cannot reveal intrabar ordering.
