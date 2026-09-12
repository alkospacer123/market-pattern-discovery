# Baseline Audit

## Strategy
`T1_BBW_Donchian_v1.0`; descriptive audit only. Strategy and parameters were not rerun or changed.

## Sample
2023-02-15 10:00:00+00:00 through 2024-12-30 08:00:00+00:00; 28 closed trades. Calendar year 2025 and later is rejected.

## Overall results
Net profit -2628.786043; PF 0.805455; expectancy -93.885216; average/median R -0.088324/-0.421847; win rate 0.214286; max DD -6283.012046; losing/winning streak 6/2; recovery factor -0.418396.

## Instrument robustness
Si: 13 trades, PF 1.159300, expectancy 64.486317, average R 0.072555, max DD -2948.389317, win rate 0.307692.
CNY: 15 trades, PF 0.579743, expectancy -231.140545, average R -0.227753, max DD -4479.040673, win rate 0.133333.

## LONG/SHORT robustness
LONG: 14 trades, PF 1.071250, expectancy 36.770998, average R 0.047349, win rate 0.142857.
SHORT: 14 trades, PF 0.500011, expectancy -224.541429, average R -0.223997, win rate 0.285714.

## Year robustness
Years present: 2023, 2024. See `yearly_report.csv`. Best/worst month: 2023-07/2024-10; maximum drawdown duration: 416 days.

## Profit concentration
Top-1 share of positive R: 0.370432; top-3/top-5/top-10: 0.819021/0.961936/1.000000.

## Limitations
MAE/MFE unavailable from frozen baseline artifacts.
Intratrade OHLC path is required.
Frozen trades record zero transaction costs; execution robustness therefore remains unverified. This audit does not access source market data or TRUE OOS.

## Verdict
**DESCRIPTIVE_BASELINE** — this is a descriptive frozen-baseline audit. The modest sample,
zero baseline costs, and any cross-instrument or cross-year instability shown above
must be assessed by the separate cost-robustness verdict.
