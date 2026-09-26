# Stage 3A.1 Schema & Provenance Report

## 1. Scope
Compact, aggregate-only schema discovery over the canonical Stage 1 universe. **No normalized trade-level file was committed in this PR.**

## 2. Source families
The 72 authenticated ledgers belong to `multitimeframe_research`, `walk_forward`, `walk_forward_validation`, `true_oos_validation`, `baseline_v2`, `walk_forward_v2`, `true_oos_v2`, `perpetual_v3/baseline`, `perpetual_v3/walk_forward`, and `perpetual_v3/true_oos`.

## 3. Schema IDs
`V1_H1_TRUE_OOS`, `V1_T2_H1_WF_LEGACY`, `V1_T2_M30_TRUE_OOS`, `V1_T2_M30_WF`, `V1_T2_MTF_BASELINE`, `V1_T3_H1_WF_LEGACY_C1_DERIVED`, `V1_T3_M30_TRUE_OOS`, `V1_T3_M30_WF`, `V1_T3_MTF_BASELINE_C1_DERIVED`, `V2_T2_BASELINE`, `V2_T2_WF`, `V2_T3_BASELINE`, `V2_T3_WF`, `V2_TRUE_OOS`, `V3_T2_BASELINE`, `V3_T2_WF`, `V3_T3_BASELINE`, `V3_T3_WF`, `V3_TRUE_OOS`. Distinct physical schemas and C1 contracts are not merged.

## 4. Canonical C1 mappings
Each registry row specifies one exact field or the documented v1 legacy expression `profit_R-2*0.001/initial_risk`; missing and unknown contracts fail closed.

## 5. Field availability
The availability table contains 36 schema/study rows. Totals: MAE 10993, MFE 10993, exit reason 10993, stops 7967, holding 10993, entry prices 10993, exit prices 10993, gross R 10827, and cost R 10827.

## 6. v1 historical C1 protection
T3/H1 walk-forward reproduces 34 trades, PF 3.3803276720178377, expectancy 0.9679913199721701, net R 32.91170487905379, and records DD source reference -5.038562132510952. Legacy C0 PF 3.49197193021 is explicitly rejected.

## 7. Aggregate reconciliation
All 36 independent study identities pass trade count, net R, expectancy, PF, and win-rate reconciliation at 1e-9 tolerance. Maximum observed delta is 4.71e-10.

## 8. Timestamp/direction validation
All entry/exit timestamps parse, all exits are at or after entries, and normalized directions are LONG/SHORT. Source values observed: LONG, SHORT. Invalid timestamps: 0; invalid directions: 0.

## 9. Diff-size control
Only four aggregate CSVs, two scripts, two JSON control records, and this report are permitted. No trade rows, anatomy tables, strategies, market data, optimization, ranking, or rule tests are produced.

## 10. Final status
Generator status: `POST_V3_STAGE_3A1_SCHEMA_PROVENANCE_COMPLETE`. Independent audit status is recorded only in `audit_stage3a1_result.json`.
