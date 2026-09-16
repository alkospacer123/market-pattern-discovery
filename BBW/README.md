# BBW research domain

## Purpose

The BBW domain is the repository's causal market-pattern research system. It
supports ingestion validation, frozen observable feature construction,
research-only future outcomes, unknown-pattern discovery, known-hypothesis
testing, candidate registration, internal confirmation, and the separate BBW
baseline workflow implemented in [`../bbw_system/`](../bbw_system/).

Discovery outputs are scientific evidence, not trading signals or permission
to alter a strategy. The Frozen BBW Baseline and Candidate Baseline v1 retain
their documented identities and are not Trading System Lab systems.

## Data sources

- The locked discovery configuration uses external, read-only Finam candles
  for CNYRUBF and USDRUBF (including documented CNY and Si filename aliases),
  at M1 and M5, from 2026-01-01 through 2026-07-01 in `Europe/Moscow`.
- Finam timestamps denote candle opens. A candle becomes observable only at its
  close; native higher-timeframe context is joined causally.
- Individual BBW baseline and normalization runs may declare additional
  external timeframes or histories under their own frozen data contract. That
  declaration does not expand the approved discovery dataset.
- Source data remains outside the repository and read-only. Hash-verified
  manifests and metadata may be recorded, but source market data may not be
  copied here.
- Calendar year 2025 is locked TRUE OOS and is forbidden during ingestion,
  feature engineering, discovery, optimization, candidate selection, and
  internal confirmation.

## Validation methodology

1. Validate source identity, schema, timestamps, ordering, session boundaries,
   continuity, and hashes without repairing or synthesizing observations.
2. Build causal features only from information observable at the decision
   time. Keep the future-outcome engine physically and conceptually separate;
   outcomes are research labels, never features or signals.
3. Conduct discovery only in the frozen discovery interval. Keep unknown
   machine discovery separate from known hypotheses, register experiment and
   candidate identities, and account for the hypothesis family.
4. Freeze a candidate before the untouched chronological internal-confirmation
   interval. Use expanding temporal folds and dependence-aware inference such
   as day/block resampling; random row splits are forbidden.
5. Judge effect size, stability, replication, uncertainty, and coverage before
   significance or profitability. Strategy construction, if later authorized,
   is a distinct stage with explicit transaction costs and slippage.
6. Freeze an eligible strategy before the single authorized 2025 TRUE OOS
   evaluation. TRUE OOS is pass/fail and cannot be used for retuning.

Processing, tie-breaking, persistence, and restart behavior must remain
deterministic and reproducible.

## Forbidden cross-use

- Do not ingest Trading System Lab trades, metrics, parameters, configurations,
  strategy decisions, portfolio weights, diagnostics, or result artifacts.
- Do not use Trading System Lab performance to label outcomes, rank patterns,
  select hypotheses, define feature thresholds, promote candidates, or claim
  replication.
- Do not present BBW discoveries, future outcomes, or candidates as validation
  of a Trading System Lab strategy.
- Do not copy BBW outputs into `TradingSystemLab/results/` or read that tree as
  a BBW input.
- If a lab observation motivates a BBW hypothesis, register it as a new known
  hypothesis before inspecting BBW data. It receives an independent identity
  and the full BBW validation path; lab evidence is contextual only.

The complete repository-level boundary is defined in
[`../research_domains.md`](../research_domains.md).

## Result locations

Repository-managed BBW research outputs belong under [`../results/`](../results/)
in stage- and candidate-specific directories. BBW core commands may also write
to an explicitly configured external output root; their reports and manifests
must preserve provenance. The implementation's specifications, inventories,
and readiness evidence remain under [`../bbw_system/`](../bbw_system/).

Neither `TradingSystemLab/results/` nor an artifact copied from it is a valid
BBW result location or input source.
