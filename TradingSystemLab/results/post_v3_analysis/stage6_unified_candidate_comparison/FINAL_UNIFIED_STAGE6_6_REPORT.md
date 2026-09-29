# Stage 6.6 Unified Existing-Candidate Basket Comparison

## Status: `SOURCE_INCOMPLETE` — ranking not performed

The artifact-only preflight stopped before portfolio construction. The Stage 5
TRAIL1 manifest authenticates an ephemeral runtime ledger SHA-256, but the
repository contains no authoritative instrument-level TRAIL1 trade ledger.
`trail1_trade_digest.csv` is a grouped digest, not a trade ledger: it has no
individual entry, exit, direction, price, or trade-R rows. Using it, replaying
T3, or deriving TRAIL1 from A–F aggregates would violate the requested source
contract.

The other four declared inputs are present. `variant_source_registry.csv`
records all five candidates and explicitly marks TRAIL1 `SOURCE_INCOMPLETE`.
Consequently no 55-row master table, metrics, hierarchy leaders, runner-up, or
A–F appendix was manufactured. The independent audit also fails closed.

No production identity was created. Stage 7 was not executed. Frozen strategy,
parameter, Stage 5, Stage 6.1–6.5, A–F, and production artifacts were not
modified. To unblock Stage 6.6, supply the exact instrument-level Stage 5
TRAIL1 ledger whose SHA-256 is authenticated by its existing manifest; do not
regenerate it as part of this artifact-only stage.
