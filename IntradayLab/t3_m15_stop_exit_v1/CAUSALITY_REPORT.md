# Causality and event ordering

GROSS_ONLY / COSTS_DEFERRED / NOT_LIVE_READY. The sole strategy inputs are original T3 features and each live position's immutable initial risk, survived favorable extreme, old Stop and activation state.

For each real M15 candle:

1. An existing position carries the Stop decided at the previous survived Close. If the Open is through/equal to it, execute at the adverse Open. Otherwise, settle any touch of that old Stop at its price. Never consult the favorable extreme to revise this already settled exit.
2. Only if the old Stop was survived, consume this completed candle's extremes and ATR. Compute favorable distance from entry and compare with 1 initial R (S1/S2) or 2 initial R (S3); equality passes. Record the first activation Close.
3. S1 permits original trailing only after activation, using all survived extremes accumulated since entry. S2/S3 always permit original trailing; after activation add BE or +1R as a candidate Stop. Choose the tightest candidate with the existing Stop; ties preserve it. New Stop becomes active at the next observed candle. A crossing of that new Stop earlier inside the just-completed trigger candle cannot execute an exit.
4. At the current Close, process an original T3 signal. Accept it only when flat, including original same-Close re-entry after a protective exit. Initial Stop is exactly entry minus direction ×2×entry ATR. Do not consume entry-candle High/Low as post-entry extrema.

The favorable path and MAE/MFE exclude the exit candle; only executed exit price may enlarge MAE. Signal-Close fills, continuous Stop prices and protective Close labels are the historical control model, not verified physical execution. Both bar endpoints are retained; precise intrabar time is unknown. A newly proposed Stop can be beyond the trigger Close under the original model; next Open execution honors any resulting adverse gap.

Original daily ordinal H1 grouping is preserved: four consecutive observed M15 closes, incomplete/gapped blocks skipped without repacking. ATR, EMA, ADX, Donchian lookbacks and positions explicitly cross calendar days; an unfinished H1 block cannot affect an earlier signal. Positions, initial risk, extrema and activation persist across overnight/weekend/year boundaries, with no forced session flat or synthetic missing candle. There is no terminal liquidation.

2025+ OHLC is never parsed. Prefix readers inspect only Ticker/Datetime before the future boundary; opaque full-file hashes certify pinned byte identity. Source CSVs remain external and read-only. No cost function, C1, commission, spread, slippage, funding or other expense is calculated or deducted from Gross R. Outcome-defined cohorts (original ≥2R, losers, top winners) are reporting only.

`stop_decisions.csv` records every exposure candle, including EXIT rows with no current favorable result/new Stop. `entry_opportunities.csv` records every raw signal and occupied/accepted state. The independent auditor reconstructs both paths from the permitted raw prefix, not from saved trade outcomes.
