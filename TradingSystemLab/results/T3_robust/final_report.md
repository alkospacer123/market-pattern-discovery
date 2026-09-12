# T3 Robust Baseline

## Frozen strategy
T3_MTF_Trend_v1.0: H4 EMA100/slope/ADX14/ATR expansion; H1 Donchian 20; SL 2 ATR; trailing 3 ATR. No parameter or signal changes.

## Dataset
Si and CNY, 2023–2024 only. Calendar 2025+ is rejected before indicator calculation.

## Cost stress
C0 PF 2.1050, net R 52.1045; C1 PF 2.0503, expectancy 0.4634 R, net R 50.5153. Break-even 65.5719 round-trip ticks.

## MAE/MFE
See `mae_mfe/mae_mfe_report.md`; path statistics are collected sequentially, excluding entry and stop candles.

## Exit efficiency
See `mae_mfe/exit_efficiency.csv`.

## Instrument robustness
See `reports/instrument_report.csv` (C1).

## Direction robustness
See `reports/direction_report.csv` (C1).

## Year robustness
See `reports/year_report.csv` (C1; 2023 and 2024 only).

## Profit concentration
C1 top-5 share of positive R: 0.3881.

## Final verdict
**ROBUST_CANDIDATE**
