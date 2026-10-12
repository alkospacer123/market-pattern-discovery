# Reproduction audit

Gate A: **PASS**.

Standalone engine; no executable TradingSystemLab imports and no historical runners executed. Both versions were fixed before reading prices.

All historical records compared in canonical exit_time/instrument/trade_id order: count/order, IDs, instrument, direction, timestamps, entry, initial Stop, exit, initial risk, risk ticks, Gross/Net R, MAE/MFE and bars held. Timestamps and categorical fields are exact. Reference CSV has 12 significant digits; comparisons use absolute tolerances with relative tolerance zero:

| field | absolute_tolerance |
|---|---|
| entry_price | 0.0000 |
| initial_stop | 0.0000 |
| exit_price | 0.0000 |
| initial_risk | 0.0000 |
| initial_risk_ticks | 0.0000 |
| gross_R | 0.0000 |
| net_R | 0.0000 |
| MAE_R | 0.0000 |
| MFE_R | 0.0000 |

Scientific tolerances: prices 5e-9; risks and R 5e-10; risk ticks 5e-7. Table formatting is abbreviated; authoritative values are in REPRODUCTION_DETAIL.json.

| version | reference_trades | actual_trades | mismatches |
|---|---|---|---|
| BASELINE | 425 | 425 | 0 |
| OPTIMIZED | 401 | 401 | 0 |

| instrument | candles | timestamps_exact | OHLCV_exact |
|---|---|---|---|
| USDRUBF | 29890 | True | True |
| CNYRUBF | 29633 | True | True |

59,523 OHLCV rows are exactly equal numerically, including Volume, and timestamps/order are identical. REPRODUCTION_DIFF.csv contains only its header when no differences exist. Fieldwise maximum errors are in REPRODUCTION_DETAIL.json.

| version | year | trades | PF | net_R |
|---|---|---|---|---|
| BASELINE | 2023 | 196 | 2.1790 | 88.9809 |
| BASELINE | 2024 | 229 | 1.1067 | 11.7640 |
| OPTIMIZED | 2023 | 185 | 2.1766 | 93.3551 |
| OPTIMIZED | 2024 | 216 | 1.2548 | 28.1346 |

Historical execution: enter at signal-candle close; first check carried Stop, gap execution min(Open,Stop) LONG / max(Open,Stop) SHORT; only survivors update extrema/trailing for later bars; same-close re-entry allowed. Signal/exit bars are excluded from favourable path extrema; adverse travel through exit price contributes to MAE. Open terminal positions are not forcibly liquidated; OPEN_POSITIONS.json explicitly records them.

The close-fill convention is a historical assumption, not proven LIVE execution. H1 grouping resets on the local calendar date of the close timestamp, not a separately inferred exchange session. Complete ordinal blocks of four must be contiguous; incomplete/gapped blocks are skipped without repacking. Indicators and Donchian history explicitly cross days as in the reference; Donchian uses shift(1). No 2025+ OHLC is ingested.
