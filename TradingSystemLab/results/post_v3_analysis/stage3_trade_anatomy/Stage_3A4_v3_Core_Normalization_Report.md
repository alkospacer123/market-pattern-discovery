# Stage 3A.4 — v3 Core Normalization Report

## 1. Scope
Normalization and integrity only for v3 perpetual T2/T3 M30/H1 trades; no anatomy analysis.
## 2. Prerequisites
Stage 3A.1, 3A.2, and 3A.3 manifests, audits, artifacts, and hashes are authenticated.
## 3. v3 source schemas
Only V3_T2_BASELINE, V3_T2_WF, V3_T3_BASELINE, V3_T3_WF, and V3_TRUE_OOS are accepted.
## 4. v3 partition layout
Baseline, walk-forward, and TRUE OOS are separate canonical partitions; no combined ledger exists.
## 5. v3 trade counts
2,740 total: baseline 1,124, walk_forward 515, true_oos 1,101.
## 6. C1 contracts
Baseline uses `net_R`; walk-forward uses `net_R_C1`; TRUE OOS uses `R_result`, without fallback or reconstruction.
## 7. v3 reconciliation
All 12/12 studies reconcile on count, net R, expectancy, PF, and win rate.
## 8. row-level integrity
All 2,740 source rows reconcile; keys, timestamps, directions, instruments, partitions, and provenance are validated.
## 9. core v1/v2/v3 normalization summary
The aggregate summary contains nine generation × lifecycle rows: v1 1,299; v2 6,954; v3 2,740.
## 10. 10,993 trade global integrity
All 10,993 rows and keys are unique and reconciled across 36/36 studies.
## 11. determinism
The independent auditor performs isolated regeneration and byte comparison.
## 12. final Stage 3A core status
`STAGE_3A_CORE_NORMALIZATION_CLOSED` after independent audit PASS. This closes only the normalization foundation, not Stage 3.
## 13. next permitted step
`Stage 3B — Trade Anatomy Tables` (not executed).

No analysis, optimization, ranking, rule testing, Stage 3B, or Stage 4 work was performed.
