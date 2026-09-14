# BBW 03B-2B temporal alignment report — CNYRUBF

## Scope

The audit implementation covers raw M1 comparison with Finam M5, M15, M30
and H1, effective-dated weekday/weekend session diagnostics, D1 convention
comparison, and H1 completeness/future-fill checks. It performs no
normalization, price correction, synthetic H4 construction, indicator,
strategy, trade, backtest, optimization, or performance operation.

## Inputs found

The instrument metadata registry is present at
`bbw_system/config/instruments/cnyrubf.yaml`. No hash-verified frozen raw
CNYRUBF dataset bundle or `FREEZE_MANIFEST.json` is present in this checkout.
Source market data was not downloaded or copied into the repository.

## Empirical results

* Checked source candles: **0**.
* Timestamp semantics: **UNRESOLVED** (no empirical comparisons).
* M1 → M5/M15/M30/H1: **UNRESOLVED**, not passed.
* Session regimes A–E and weekend sessions: **UNRESOLVED**.
* D1 semantics: **UNRESOLVED**.
* H1 alignment: **FAIL** (cannot establish completeness or absence of future fill).
* Found data mismatches: **0 observed**, which is not evidence of a match.

## Verdict

**NOT READY FOR NORMALIZATION.** The audit fails closed until an external,
read-only, hash-verified freeze manifest provides all six requested raw
timeframes. Re-running the audit must not mutate those sources and must retain
the resulting complete evidence bundle.
