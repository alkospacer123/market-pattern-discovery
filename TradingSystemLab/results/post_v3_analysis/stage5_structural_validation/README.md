# Stage 5 — Separate structural validation

Status: **FAIL CLOSED / implementation incomplete**.

The committed normalized ledgers expose final MAE and MFE, but not the ordered
completed bars at which the frozen 1R triggers first became observable.  Using
those final extrema to rewrite outcomes would introduce look-ahead and violate
the repository research contract.  `run_stage5_validation.py` therefore first
authenticates Stage 4, both canonical strategy sources, and the external frozen
market-data repository, then stops until exact lifecycle-aware execution
adapters are implemented.

No Stage 5 result, classification, audit PASS, CLOSED status, or new TRUE OOS
claim is emitted by this checkpoint.  The only permitted evidence label for a
future completed implementation remains `RETROSPECTIVE_CAUSAL_VALIDATION`.
