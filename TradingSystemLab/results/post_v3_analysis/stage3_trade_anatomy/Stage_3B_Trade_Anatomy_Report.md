# Stage 3B Trade Anatomy Report

## 1. Scope
Aggregate-only descriptive diagnostics for T2/T3, M30/H1, and separately labelled baseline, walk-forward, and TRUE OOS lifecycles. No strategy execution or selection was performed.

## 2. Canonical normalized dataset
The authenticated Stage 3A closed population contains 10,993 uniquely keyed trades across 36 studies. All seven normalized partitions are inputs; no raw market data is read.

## 3. T2 vs T3
The strategy/timeframe table exposes descriptive return, holding, and excursion differences while retaining generation and lifecycle labels. It defines no selection score.

## 4. M30 vs H1
Timeframe comparisons remain stratified by generation, lifecycle, and strategy. Different sample sizes must be kept visible.

## 5. Instrument anatomy
Instrument rows are not merged. In particular, quarterly v2 Si/CNY constructions remain distinct from perpetual USDRUBF/CNYRUBF constructions.

## 6. Direction anatomy
LONG and SHORT anatomy is reported without filtering or prescriptive interpretation.

## 7. Exit-reason anatomy
Source values are preserved verbatim; missing values, if any, are the explicit `UNAVAILABLE` category. Shares are calculated within each study.

## 8. Holding-time anatomy
Fixed, predeclared buckets are `<1h`, `1–3h`, `3–6h`, `6–12h`, `12–24h`, `24–48h`, `48–96h`, and `>96h`; missing values use `UNAVAILABLE`. Boundaries were not fitted to outcomes.

## 9. Entry weekday
Normalized weekday values (0=Monday through 6=Sunday) are retained without causal claims.

## 10. Entry hour
Normalized hours are retained without timezone conversion, session construction, or rule testing.

## 11. MAE/MFE anatomy
Coverage and quartiles are reported without imputation or alteration of the Stage 3A sign convention, which remains UNKNOWN. **MAE_MFE_ORDER_UNAVAILABLE**: the normalized records do not establish intratrade event ordering.

## 12. Repeated patterns across lifecycle
The tables permit side-by-side inspection only. Lifecycle stages are never pooled, and recurrence is not a selection criterion.

## 13. Cross-generation observations
v1 and v3 perpetual results and v2 quarterly results are presented descriptively. Periods, universes, constructions, and sample sizes differ, so no causal superiority claim is supported.

## 14. Limitations
This is descriptive evidence organization: no significance tests, path reconstruction, threshold-event inference, recommendations, ranking, optimization, or small-sample suppression. Aggregate MAE/MFE does not reveal which excursion occurred first.

## 15. Handoff to Stage 3C
No Stage 3C work is performed. Any later threshold-event analysis requires separately declared exact inference rules and ordered-path evidence.
