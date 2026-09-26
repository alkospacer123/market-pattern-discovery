# Stage 5 — Separate structural validation

Status: **FAIL CLOSED / implementation incomplete**.

The initial fail-closed gate was intentional. The committed normalized ledgers expose final MAE and MFE, but not the ordered
completed bars at which the frozen 1R triggers first became observable.  Using
those final extrema to rewrite outcomes would introduce look-ahead and violate
the repository research contract.  `run_stage5_validation.py` therefore first
authenticates Stage 4, both canonical strategy sources, and the external frozen
market-data repository. The repository is resolved from
`MARKET_PATTERN_DATA_ROOT`, the sibling repository, or the canonical
`/workspace/market-pattern-data` fallback, in that order; its HEAD must still
equal the frozen commit.

The auditor now owns a deliberately duplicated authentication implementation.
It does not import the runner, an execution adapter, or shared Stage 5 metric
generation logic. Exact lifecycle-aware causal adapters have not yet been
implemented, so the runner continues to stop after authentication rather than
emit fabricated evidence. No MFE/MAE outcome rewriting is used.

No Stage 5 result, classification, audit PASS, CLOSED status, or new TRUE OOS
claim is emitted by this checkpoint.  The only permitted evidence label for a
future completed implementation remains `RETROSPECTIVE_CAUSAL_VALIDATION`.
