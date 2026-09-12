# T3 baseline

Frozen, unoptimized baseline for **Si + CNY**. Source CSV files remain outside the repository.

## Parameters

EMA100; EMA slope 5; ADX(14) > 20; ATR(14) > ATR mean(20); breakout 20;
initial stop 2 ATR; trailing stop 3 ATR; fixed risk 1%; point value 1.
Commission and slippage are configurable and were both set to zero for this baseline.

## Period

2023-01-03T10:00:00+03:00 through 2024-12-31T00:00:00+03:00.
Calendar 2025 was neither selected nor loaded.

## Results

* Trades: 109
* Win rate: 0.4312
* Profit factor: 2.098284631752035
* Average R: 0.4780
* Net profit: 56524.76
* Max drawdown: -17847.64

## Known limitations

H4 candles are consecutive complete four-H1-bar blocks reset at each trading-day
boundary. Intrabar ordering is unknown, so a trailing level calculated from a bar's
extreme becomes active only on the next bar. Open positions at the end of the sample
remain unrealized. Contract multipliers, commissions, and slippage must be configured
to venue-accurate non-zero values before interpreting economic performance.
