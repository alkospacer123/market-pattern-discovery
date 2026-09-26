# Stage 1 Master Evidence Report

## Scope and lineage

Stage 1 is an artifact-only consolidation. It executes no strategy, optimizer, or market-data loader; it makes no ranking, candidate replacement, trade change, or production choice.

* **v1** tested T1/T2/T3 and R1/R2/R3 on USDRUBF/CNYRUBF over M1, M5, M15, M30, H1, H4, and D1. Existing evidence advanced T2/T3 on M30/H1 as the more stable research domain; this report preserves that decision rather than re-selecting it.
* **v2** tested T2/T3 M30/H1 on quarterly Si, CNY, GD, BR, MIX, and NG to evaluate transfer and cross-market diversification.
* **v3** tested T2/T3 M30/H1 on perpetual USDRUBF, CNYRUBF, GLDRUBF, and IMOEXF through baseline, optimization, freeze, robustness, walk-forward, and TRUE OOS. The final TRUE OOS labels are T2/M30 BORDERLINE, T2/H1 BORDERLINE, T3/M30 PASS, and T3/H1 PASS.

## Exact coverage

The source inventory contains **96 artifacts** and the consolidation contains **36 study rows**, **144 instrument rows**, **72 direction rows**, and **789 chronological month rows**. Canonical trade-ledger trees used are `multitimeframe_research`, `walk_forward`, and `true_oos_validation` (v1); `baseline_v2`, `walk_forward_v2`, and `true_oos_v2` (v2); and `perpetual_v3/baseline`, `perpetual_v3/walk_forward`, and `perpetual_v3/true_oos` (v3). The v3 closeout provenance supplied by the brief is `aab2659cfc91846631bbe22ff3b45e3e4e4af85f`.

Robustness reports are not promoted to trade-level study rows because the canonical trees do not contain complete robustness trade ledgers. Their absence is explicit rather than inferred.

## Unavailable historical fields

Bootstrap and gate fields for older/development stages; historical candidate ids and verdicts where source metrics omit them; top-1/top-3 source concentration reports (derived descriptive shares are supplied); robustness-stage trade ledgers for all generations. `NA` means unavailable/not applicable, never zero.

## Factual observations (not rankings)

The generations differ in contract type, universe, development window, sample size, and lifecycle maturity. Therefore cross-generation PF and expectancy values must not be interpreted as an ordering. The calendar, instrument, and direction tables retain generation and lifecycle labels and retain negative contributors. Monthly and period values are descriptive aggregations of immutable source trade outcomes.

## Scope protection

This stage does **not** decide a production basket or winner, change sessions, add breakeven/trailing rules, test correlated-risk limits, or construct a portfolio. Those questions remain for later stages.
