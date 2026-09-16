# Trading System Lab research domain

## Purpose

Trading System Lab evaluates the independently specified T1–T3 trend systems
and R1–R3 range-reversal systems. Its scope includes deterministic baseline
reproduction, bounded optimization where explicitly authorized, robustness and
walk-forward analysis, execution and cost audits, multi-timeframe research,
TRUE OOS validation after the required freeze, and portfolio construction.

It is not the BBW pattern-discovery domain. A similarly named indicator or
strategy does not make artifacts interchangeable between the domains.

## Data sources

- Market data is supplied through an explicit `--data-root`; source files stay
  outside the repository and are read-only.
- The established development datasets are the documented Si and CNY futures
  inputs (including their configured aliases), primarily native H1 and M15
  candles. A workflow may use only the symbols, timeframes, and date interval
  declared by its frozen configuration or report.
- Development and validation workflows must enforce their declared temporal
  splits. Calendar year 2025 is locked TRUE OOS and cannot be read before a
  strategy has been frozen for its single authorized validation.
- Higher-timeframe values, including derived H4 or other context, must use only
  fully closed source candles and must be aligned without future fill.

No file under `results/`, the BBW domain, or another generated-artifact tree is
a substitute for the declared source dataset.

## Validation methodology

1. Freeze the strategy identity, parameters, signal timing, execution model,
   cost and slippage assumptions, instruments, timeframes, and date bounds.
2. Reproduce the baseline deterministically and audit causal candle-close and
   higher-timeframe alignment.
3. Where authorized, perform bounded development-only optimization without
   chasing profit factor, followed by parameter, cost, and execution
   robustness checks.
4. Use chronological walk-forward validation; do not use random row splits.
   Report fold, instrument, direction, year, concentration, and sample-size
   limitations rather than selecting favorable subsets.
5. Freeze the resulting candidate before any TRUE OOS access. Calendar year
   2025 is a one-time pass/fail evaluation and cannot trigger retuning.
6. Construct portfolios only from eligible frozen system evidence, preserving
   each component's provenance and cost assumptions.

All ordering and tie-breaking must be deterministic. Future backtests must
include configurable transaction costs and slippage, and reports must not omit
them when drawing conclusions.

## Forbidden cross-use

- Do not ingest BBW features, future-outcome labels, candidate registries,
  thresholds, optimization findings, diagnostics, or result artifacts.
- Do not use BBW discoveries to filter trades, choose systems, set parameters,
  define regimes, or justify a Trading System Lab promotion.
- Do not publish Trading System Lab trades or metrics as replication,
  confirmation, or OOS evidence for BBW.
- Do not copy Trading System Lab outputs into `results/` or any BBW output root.
- If a BBW observation motivates a new lab idea, preregister a new lab identity
  and validate it from the beginning on lab-approved data. Prior BBW evidence
  remains contextual only.

The complete repository-level boundary is defined in
[`../research_domains.md`](../research_domains.md).

## Result locations

All canonical outputs for this domain belong under
[`TradingSystemLab/results/`](results/). Stage-specific subdirectories hold
baseline, implementation-check, optimization, robustness, walk-forward,
multi-timeframe, TRUE OOS, audit, and portfolio artifacts. An invocation may
use another explicit output directory for a temporary run, but such a run is
not canonical until its provenance and intended status are documented; it must
never target the BBW `results/` tree.
