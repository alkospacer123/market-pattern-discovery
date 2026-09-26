# Stage 3A.2 — v1 Normalization Report

## 1. Scope
This stage normalized only v1 perpetual T2/T3 M30/H1 trades. No v2 or v3 rows were included.

## 2. Stage 3A.1 prerequisite
The final Stage 3A.1 manifest/audit PASS states, registry hash, inventory hash, and every v1 source hash were verified before reading source rows.

## 3. Source schemas used
V1_H1_TRUE_OOS, V1_T2_H1_WF_LEGACY, V1_T2_M30_TRUE_OOS, V1_T2_M30_WF, V1_T2_MTF_BASELINE, V1_T3_H1_WF_LEGACY_C1_DERIVED, V1_T3_M30_TRUE_OOS, V1_T3_M30_WF, V1_T3_MTF_BASELINE_C1_DERIVED.

## 4. C1 normalization
Canonical C1 follows the registry exactly. `V1_T3_H1_WF_LEGACY_C1_DERIVED` and `V1_T3_MTF_BASELINE_C1_DERIVED` use `profit_R - 2*0.001/initial_risk`; no fallback mapping exists.

## 5. v1 trade counts
1,299 rows: baseline 606, walk_forward 194, true_oos 499; T2 597, T3 702; H1 426, M30 873.

## 6. Field availability in normalized output
Raw anatomy values are copied only through registry mappings. Missing source fields remain empty and `UNAVAILABLE`; holding duration is `DERIVED`. MAE/MFE sign convention remains UNKNOWN.

## 7. Reconciliation
All 12 lifecycle × strategy × timeframe studies reconcile for count, net R, expectancy, PF, and win rate.

## 8. Duplicate, timestamp, and direction checks
Canonical keys are unique; no unproven economic duplicates, invalid timestamps, or invalid directions exist. Instruments are only USDRUBF/CNYRUBF.

## 9. Determinism
Rows use an explicit lifecycle-first stable ordering. The independent auditor performs isolated regeneration and byte comparison.

## 10. Final audit status
The generator leaves `PENDING_INDEPENDENT_AUDIT`; the independent auditor owns closeout to `POST_V3_STAGE_3A2_V1_NORMALIZATION_AUDIT_PASSED`. The accompanying final manifest and audit result confirm that closeout.

No trade anatomy analysis was performed. No optimization, ranking, or rule testing was performed.
