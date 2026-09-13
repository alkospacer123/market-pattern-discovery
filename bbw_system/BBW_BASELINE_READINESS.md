# Frozen baseline parameter readiness

This is a specification inventory, not an optimization result. `FIXED` reflects values already present in the project strategy config; ambiguous or cost-related zero defaults are deliberately not accepted as decisions.

| Parameter | Status | Value / blocker |
|---|---|---|
| BBW period | FIXED | 10 |
| BBW std | FIXED | 2.0 |
| threshold trading days | FIXED | 10 |
| threshold minima | FIXED | 6 |
| EMA | FIXED | 50 |
| EMA slope | FIXED | lag 10, minimum 0.001 |
| ATR | FIXED | 14 |
| range bars | FIXED | 6–30 |
| ATR range bounds | FIXED | 1.0–2.0 |
| max width pct | UNRESOLVED | passport-specific; BR/GOLD missing |
| retest min/max bars | FIXED | 5–30 |
| penetration | UNRESOLVED | 20% fixed, “3 points” unit unresolved |
| stop offset | UNRESOLVED | “4 points” unit unresolved |
| stop min/max | UNRESOLVED | values exist in example config but are not frozen baseline evidence |
| entry extension | UNRESOLVED | not frozen |
| confirmation candle limit | UNRESOLVED | not frozen |
| risk_pct | FIXED | 0.015 |
| margin limit | FIXED | 0.75 |
| commissions | UNRESOLVED | per instrument monetary metadata required |
| slippage | UNRESOLVED | per instrument decision required |
| TP allocations | FIXED | levels 1/2/3 R; 50%/30%/20% |

Preflight is intentionally stricter than the table: every required strategy entry must be supplied as `{ "status": "FIXED", "value": ... }`, and critical passport values must carry `verified: true`. There are no monetary defaults.
