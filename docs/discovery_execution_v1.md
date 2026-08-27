# Discovery Execution Contract v1.0

The normative machine-readable contract is `config/discovery_execution_v1.json`. Its canonical JSON serialization, excluding `signature_sha256`, is signed with SHA-256. It consumes the unchanged Phase 1–5A.1 signatures and no market outcomes.

## Feature typing

The inventory preserves the exact frozen Feature Set order. `trading_date` is **excluded** from discovery because it is an identifier/nontransferable calendar-date key; it remains available only for grouping, complete-day inference, lineage, and temporal analysis. It can never enter univariate, interaction, subgroup, or candidate conditions. `local_hour`, `local_minute`, and `weekday` are natural low-cardinality cyclic/nominal integer states. High-cardinality ordinal descriptors—including `minute_of_day`, minutes since open, consecutive counts, touch/cross counts, and bars-since counts—use `continuous_quantile`; no singleton-like raw integer states are searched. Direction variables are categorical and declared flags are binary. Outcomes are never consulted.

Continuous state order is `LE_P10`, `P10_P25`, `P25_P75`, `P75_P90`, `GE_P90`, `MISSING`; ties enter the lower interval. Binary order is `0`, `1`, `MISSING`; other categories use canonical scalar ordering with explicit missingness. Full discovery cutpoints fit only the applicable DISCOVERY instrument/timeframe; walk-forward cutpoints fit TRAIN and apply unchanged to VALIDATE.

## Coverage-balanced search

Every eligible unordered `i < j` pair receives SHA-256 priority from execution seed 20260401, timeframe, frozen indices, and canonical feature identities. Sorting by this priority and taking 500 removes feature-order prefix bias without using targets. Same- and cross-family pairs are allowed.

Subgroups retain depths 2 and 3 with a fixed 50%/50% rule-budget allocation. A seeded SHA-256 feature order and cyclic gap schedule supplies broad combination coverage; canonical state products receive a second SHA-256 priority within each depth allocation. The total cap is 100,000. There is no target input, adaptive beam, profitability input, or prefix truncation.

## Inference and operations

The baseline is all target-valid rows for the same instrument, timeframe, and DISCOVERY interval. Complete Moscow days are never exchanged across unequal arrays. Under the null, each complete day's candidate-membership sequence is independently circularly phase-shifted against that same day's fixed outcomes. This preserves row identity, day length, candidate count, mask serial structure, and boundaries; exchangeability assumes within-day phase stationarity. Continuous statistics use signed median difference; binary/multiclass contrasts use signed probability difference. With 1,000 replicates and seed 20260401, `p=(1+count(|T_null|>=|T_observed|))/(B+1)`. No truncation or IID bootstrap is used.

Screening statuses are a schema/runtime enum with explicit transitions. Only `promoted` effects enter `research.registry.create_candidate`; default creation persists in the canonical candidate registry, starts at `discovered`, and carries complete signed effect, target, fold, replication, signature, and code lineage. Tests use an explicit temporary directory.

Replication, ranking, shortlist, preregistration, finalization, deterministic batches/checkpoints, artifact schemas, and completeness reconciliation remain frozen. No partial run passes. This phase analyzes no feature/outcome relationships, creates no market-data candidates, accesses neither confirmation nor 2025, calculates no profitability, and runs no backtest.
