# Phase 6.1 MOEX execution specification audit

**Status:** `PHASE_6_1_EXECUTION_SPEC_AUDIT_COMPLETE`

## Current execution model and compatibility

Frozen Phase 1--6 runners use a legacy `tick_size=0.001` argument for both
cost arithmetic and risk-unit reporting. It represented the historical source
price unit, not a newly verified exchange execution grid. Those runners,
parameters, and results remain byte-for-byte unchanged; the new specification
is an additive compatibility layer for future simulation and Finam integration.

## Explicit units

| Instrument | Exchange | Exchange tick | Contract lot | OHLC precision | R3 round level step |
|---|---|---:|---:|---:|---:|
| USDRUBF (Si) | MOEX | 0.01 | 1,000 USD | 0.001 | 0.10 |
| CNYRUBF (CNY) | MOEX | 0.01 | 1,000 CNY | 0.001 | 0.05 |

- **`tick_size` (A):** real exchange minimum price movement. Future commission,
  slippage, fill simulation, order rounding, and Finam API code must use it.
- **`price_precision` (B):** historical OHLC storage precision. Data loading,
  indicators, and mathematical calculations use it without order rounding.
- **`round_level_step` (C):** strategy-specific R3 logical spacing. It is not an
  exchange tick and remains 0.10 for Si and 0.05 for CNY.

## `tick_size` usage audit

- **A -- execution:** `core/execution.py` and `core/backtester.py` convert costs
  expressed in ticks; future calls must supply the exchange tick.
- **A/B legacy compatibility:** strategy runners and frozen optimization,
  walk-forward, and TRUE OOS modules pass 0.001 into cost/risk calculations.
  They are intentionally untouched so historical artifacts are not recalculated.
- **B -- historical precision:** `configs/Si.yaml` and `configs/CNY.yaml` label
  0.001 as `tick_size`; frozen readers retain that behavior. New consumers use
  `price_precision` from the specification layer.
- **C -- strategy levels:** R3 receives `round_level_step` separately and its
  level calculations already use that value. No replacement was required.
- Test-only synthetic tick values exercise unit formulas and are not instrument
  specifications.

## Frozen artifact integrity

Tree hashes cover relative filenames and bytes in deterministic lexical order.
No Phase 5 or Phase 6 code is executed by this audit.

| Artifact tree | SHA256 | Status |
|---|---|---|
| R1_implementation_check | `0cd7becc41ca35cc77432fafd34163df7b7ee9fcfc9feaf1c0f728bc55484864` | PASS |
| R2_implementation_check | `fcf8681a46d1a78a8396a58599f33fe0569019ebd1f5450824be16f547e0acdc` | PASS |
| R3_implementation_check | `3624d26ebe9f72259476697c4d4c9805ea6c1fe182d776d87f19f077d77da200` | PASS |
| T1_baseline | `3cf927fb18c08cc6bdbc7f38631ad56ab383bfdfe7f7e109550163db5590bb3d` | PASS |
| T2_implementation_check | `7046279447feda8170ab9c1050aa9945185becfe612f33fb015f9ca243162a63` | PASS |
| T3_baseline | `813ff85b4efbf99754737f0fc826c8d86c4bab038156e8d87d7d3766f91332f9` | PASS |
| portfolio_construction | `637e3910e1e39eb317e9d4c168ba8ebb3ee313865a422c02fd0254a435565efc` | PASS |
| true_oos_validation | `2c50a0365899bba0fa908ac0b1d163b2a97656f85bdb712ab1d4f7cabe6bbb67` | PASS |

The generator contains no runtime timestamp, sorts JSON keys, fixes CSV row and
newline ordering, and fails closed before reporting completion on any mismatch.
