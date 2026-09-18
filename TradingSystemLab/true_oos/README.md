# M15 TRUE OOS validation

This module is the only M15 path permitted to open locked TRUE OOS data. It is
an execution and audit stage, not research or candidate selection.

## Locked boundaries

| Partition | Boundary | Permitted use |
|---|---|---|
| Development | 2023-01-01 — 2024-12-31 | completed research and walk-forward only |
| TRUE OOS | >= 2025-01-01 | this one-shot validation only |

An M15 candle becomes available at its close. Every loaded close and every
trade entry/exit is independently checked against the TRUE OOS boundary.
Development candles are not used for warm-up. H1 context is formed causally
from four completed M15 candles and resets at each trading-day boundary.

## Frozen contract

- Allowed identities: `T2_candidate_v1`, `T3_candidate_v1` only.
- Parameters are read only from the frozen M15 candidate registries.
- Candidate ID, configuration ID, parameter hash, registry file hash,
  walk-forward provenance, and frozen strategy source hash are checked before
  market data is opened.
- Execution is one continuous period, starts `FLAT`, and has no internal reset.
- Costs are the frozen H1 C1 model: one tick per side; slippage is configurable
  in the shared engine but frozen to zero for candidate parity.

```text
optimization = false
ranking = false
parameters_frozen = true
```

The runner has no strategy, candidate, parameter, optimizer, ranking, or
retraining argument. It also audits its own call graph and fails if an
optimization or ranking call is introduced.

## Run

Preparation tests (do not execute TRUE OOS):

```bash
pytest -q TradingSystemLab/tests/test_m15_true_oos.py
```

After merge, the authorized results audit may be run once against read-only
source data:

```bash
python -m TradingSystemLab.run_m15_true_oos \
  --data-root /workspace/market-pattern-data \
  --output TradingSystemLab/results/true_oos_validation/M15
```

The per-candidate audit contains `metrics.json`, `trades.csv`,
`period_summary.csv`, instrument/direction/year reports, concentration and
MAE/MFE reports, deterministic SVG charts, and `summary.md`. `manifest.json`
records SHA256 for every generated artifact.
