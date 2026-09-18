# M5 holding-time candidate analysis

Status: `PHASE_M5_HOLDING_TIME_ANALYSIS_COMPLETE`

This is deterministic, read-only evidence collection over completed 2023–2024 trades. It is not a strategy modification, optimization, candidate selection, parameter search, or new backtest.

## Questions and evidence

### 1. Are losing trades failing immediately after entry?

- Portfolio trades below 60 minutes: 963 trades, net_R=-682.322, PF=0.12366773861325413.
- Final outcomes show strong short-duration degradation, but the allowed ledgers cannot establish how soon within each trade the loss developed.

### 2. Do profitable trades require time to develop?

- Portfolio trades of 60 minutes or longer: 998 trades, net_R=820.511, PF=4.201254946115764.
- T2: winner median duration=145 minutes; loser median duration=35 minutes.
- T3: winner median duration=110 minutes; loser median duration=40 minutes.

Winner durations are longer than loser durations in both candidate ledgers. This supports a duration association, while timestamped excursions would be required to prove when profits first developed.

### 3–5. Candidate, instrument, and session differences

| Scope | <60 min trades | <60 min net_R | 60+ min trades | 60+ min net_R |
|---|---:|---:|---:|---:|
| T2 | 442 | -341.045 | 388 | 391.704 |
| T3 | 521 | -341.277 | 610 | 428.807 |
| USDRUBF | 525 | -339.921 | 535 | 516.685 |
| CNYRUBF | 438 | -342.4 | 463 | 303.827 |
| Session_A | 58 | -38.5044 | 17 | 36.8799 |
| Session_B | 713 | -476.406 | 641 | 677.623 |
| Session_C | 192 | -167.411 | 340 | 106.008 |

These are descriptive cells, not proposed filters. Full instrument, session, direction, and holding-bucket metrics are preserved in the CSV reports.

## Intratrade timing limitation

The frozen trade ledgers provide final MAE and MFE values, but not timestamped intratrade excursions. Therefore first-positive-excursion time and time-to-maximum-MAE cannot be calculated causally from the allowed inputs. The corresponding files explicitly report `DATA_UNAVAILABLE`; no candle data was read and no timing was inferred from final outcomes.

The evidence distinguishes duration-associated outcomes, but cannot by itself establish whether MFE appeared early, whether losses failed immediately, or whether an exit-management or entry-quality mechanism caused the association.
