# Research domain isolation

This repository contains two independent research domains. Their coexistence in
one repository is an operational convenience, not permission to combine their
data, hypotheses, parameters, validation evidence, or conclusions.

| Domain | Purpose | Canonical documentation | Result location |
| --- | --- | --- | --- |
| Trading System Lab | Evaluate the separately defined T1–T3 and R1–R3 trading systems and their portfolio behavior. | [`TradingSystemLab/README.md`](TradingSystemLab/README.md) | `TradingSystemLab/results/` |
| BBW | Discover and validate causal market patterns and maintain the independent BBW baseline workflow. | [`BBW/README.md`](BBW/README.md) | `results/` and explicitly configured external output roots |

## Repository-wide invariants

Both domains obey the repository research safety contract:

- **ZERO LOOK-AHEAD:** a value is usable only after it is observable; higher
  timeframes are aligned causally and a candle is unavailable until it closes.
- Day and session boundaries are explicit. Rolling state resets at the trading
  day boundary unless a feature is explicitly documented as cross-day.
- Processing order and tie-breaking are deterministic and reproducible.
- Source market data remains external and read-only; it is never copied into
  this repository.
- Calendar year 2025 is locked TRUE OOS. It may not be read during ingestion,
  feature engineering, discovery, optimization, or strategy selection, and it
  is never used for retuning.
- Any backtest must declare configurable transaction costs and slippage.
  Profit factor is evidence, not an optimization target.

## Isolation boundary

### Permitted sharing

The domains may share repository infrastructure and general engineering
principles: causal timestamp conventions, deterministic serialization, audit
patterns, schema-validation techniques, and generic test utilities. Sharing
such infrastructure does not transfer research evidence.

### Forbidden cross-use

The following uses are prohibited in both directions:

- using one domain's results, labels, future outcomes, discovered patterns, or
  diagnostics to create, filter, rank, tune, or select candidates in the other;
- treating a strategy, parameter set, threshold, feature definition, cost
  assumption, rejection, or promotion decision as validated because it worked
  in the other domain;
- pooling observations, trades, metrics, folds, uncertainty estimates, or OOS
  evidence across domains;
- importing one domain's generated artifacts as the other domain's inputs,
  baselines, checkpoints, or validation evidence;
- moving or duplicating result artifacts between result trees in a way that
  obscures provenance; and
- using access granted to one domain as authorization to inspect locked data in
  the other domain.

An idea inspired by the other domain must be registered as a new hypothesis in
the receiving domain before its data is inspected. It receives a new identity,
uses only that domain's approved inputs and validation protocol, and makes no
claim to untouched confirmation or TRUE OOS evidence already consumed
elsewhere.

## Provenance and result handling

Every result must identify its domain, configuration or candidate identity,
input period, source hashes where the workflow provides them, validation stage,
cost and slippage assumptions when applicable, and code version when available.
The producing domain's result tree is authoritative. Reports may link to an
artifact in the other tree for human context, but the link is not an input and
does not confer validation status.
