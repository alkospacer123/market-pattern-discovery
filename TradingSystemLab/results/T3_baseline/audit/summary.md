# T3 Baseline Audit

## Strategy
`T3_MTF_Trend_v1.0`; descriptive audit only. Strategy and parameters were not rerun or changed.

## Sample
2023-02-20 20:00:00+00:00 through 2024-12-12 10:00:00+00:00; 109 closed trades. Calendar year 2025 and later is rejected.

## Overall results
Net profit 56524.755166; PF 2.098285; expectancy 518.575735; average/median R 0.478023/-0.333890; win rate 0.431193; max DD -17847.639642; losing/winning streak 10/6; recovery factor 3.167072.

## Instrument robustness
Si: 61 trades, PF 1.753398, expectancy 357.180680, average R 0.339967, max DD -12312.537109, win rate 0.442623.
CNY: 48 trades, PF 2.540655, expectancy 723.681952, average R 0.653469, max DD -5848.680391, win rate 0.416667.

## LONG/SHORT robustness
LONG: 74 trades, PF 1.915359, expectancy 416.898881, average R 0.367236, win rate 0.432432.
SHORT: 35 trades, PF 2.445361, expectancy 733.549657, average R 0.712258, win rate 0.428571.

## Year robustness
Years present: 2023, 2024. See `yearly_report.csv`. Best/worst month: 2024-06/2023-10; maximum drawdown duration: 303 days.

## Profit concentration
Top-1 share of positive R: 0.140988; top-3/top-5/top-10: 0.288249/0.386471/0.570525.

## Limitations
MAE/MFE unavailable from frozen baseline artifacts.
Intratrade OHLC path is required.
Frozen trades record zero transaction costs; execution robustness therefore remains unverified. This audit does not access source market data or TRUE OOS.

## Verdict
**NEEDS_RESEARCH** — positive expectancy appears across both instruments and both years, but the modest sample, absent intratrade path, and zero recorded costs are material limitations.
