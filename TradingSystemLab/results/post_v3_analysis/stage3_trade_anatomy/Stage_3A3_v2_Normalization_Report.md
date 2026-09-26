# Stage 3A.3 — v2 Normalization Report

## 1. Scope
This stage normalized only v2 quarterly T2/T3 M30/H1 trades. No v1 or v3 rows were included, and Stage 3A.4 was not started.

## 2. Stage 3A.1/3A.2 prerequisites
Both prerequisite manifests and audit results were verified in final PASS state, including their manifest/output hashes. The Stage 3A.1 inventory, registry, and every selected v2 source hash were authenticated before source rows were read.

## 3. Source schemas
The closed schema set is `V2_T2_BASELINE`, `V2_T2_WF`, `V2_T3_BASELINE`, `V2_T3_WF`, and `V2_TRUE_OOS` from the three authorized v2 source families.

## 4. Partition layout
The logical dataset is the union of baseline, walk-forward, and TRUE OOS CSV partitions. No duplicate combined ledger is produced.

## 5. v2 trade counts
There are 6,954 rows: baseline 4,449, walk_forward 746, and true_oos 1,759. T2 has 3,206 rows and T3 has 3,748; H1 has 2,284 and M30 has 4,670.

## 6. C1 contract
Baseline uses `net_R`, walk-forward uses `net_R_C1`, and TRUE OOS uses `R_result`. There is no generic fallback and no price-based C1 reconstruction.

## 7. Row provenance
Each output row retains its authenticated source path, source row number, source trade ID, schema, and deterministic key. All 6,954 rows reconcile independently to one source row.

## 8. Reconciliation
All 12 lifecycle × strategy × timeframe studies reconcile for trade count, net R, expectancy, PF, and win rate.

## 9. Integrity checks
Keys are globally unique, no unexpected economic duplicates or partition leakage exist, timestamps and directions are valid, and instruments remain exactly Si/CNY/GD/BR/MIX/NG. Raw anatomy fields are copied only through registry mappings; unavailable stop values remain empty. MAE/MFE sign convention remains UNKNOWN.

## 10. Determinism
Every partition has an explicit stable ordering. The independent auditor performs isolated regeneration, equivalent pending-state byte comparison, a second semantic audit, and mutation tests before closeout.

## 11. Final status
The generator leaves `PENDING_INDEPENDENT_AUDIT`; the auditor owns closeout to `POST_V3_STAGE_3A3_V2_NORMALIZATION_AUDIT_PASSED`.

No anatomy analysis performed. No optimization, ranking, or rule testing was performed.
