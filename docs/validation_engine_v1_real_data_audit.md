# Validation Engine v1 real-data restart audit

## Scope and safety

The isolated audit memory was freshly created at
`/tmp/marketai_validation_engine_validation_001`. It used read-only CNYRUBF Q1 M5 and M15
source observations from 2023, 2024, and locked 2025. Source timestamps were converted from
bar-open time to explicit close/availability time (five and fifteen minutes respectively).
Signals were a fixed periodic sampling rule, not an outcome label, and all runs applied fixed
commission `0.001` and per-fill slippage `0.0005`. This exercise validates mechanics; its
deliberately artificial audit strategy is not evidence of a tradable market effect.

The real-data split was TRAIN 2023, VALIDATION 2024, and TRUE_OOS 2025. Two fixed walk-forward
windows within 2023 were executed. The validation engine alone unlocked TRUE_OOS, after the
strategy and development backtest existed. No source file was written or copied.

## Two-process result

Process A executed 20 validation cycles and persisted 20 strategy candidates, 20 backtests,
and 20 validation reports. Process B terminated Process A, reopened the same memory, and
replayed the same 20 cycles. All append operations became idempotent skips: final counts
remained 20/20/20 and there were zero duplicate validation IDs.

| Metric | Process A | Process B after restart |
|---|---:|---:|
| StrategyCandidates | 20 | 20 |
| Backtests | 20 | 20 |
| ValidationReports | 20 | 20 |
| ACCEPTED | 0 | 0 |
| REJECTED | 20 | 20 |
| INSUFFICIENT_DATA | 0 | 0 |
| Walk-forward windows | 40 | 40 |
| Average stability | 0.9995835069 | 0.9995835069 |
| Average drawdown | 0.2360000000 | 0.2360000000 |
| Duplicate IDs | 0 | 0 |

The rejection distribution is reported without parameter search or attempts to improve it.
The restart check passed, as did deterministic identities and StrategyCandidate immutability.
It does not override the repository's prohibition on using 2025 for discovery, optimization,
or strategy selection.
