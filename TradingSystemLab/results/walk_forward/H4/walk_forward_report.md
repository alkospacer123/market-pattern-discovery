# H4 Walk Forward Validation

**PHASE_H4_WALK_FORWARD_BORDERLINE**

## Previous invalid run

T2 stitched trades = 0; T3 stitched trades = 0. Cause: isolated test-slice indicator warm-up failure.

## Corrected causal-warm-up run

### T2

| Fold | Trades | PF C1 | Expectancy C1 | Net R | DD | Status | Included in pass |
|---|---:|---:|---:|---:|---:|---|---|
| WF01 | 3 | 0.0 | -0.739166658263 | -2.21749997479 | -2.21749997479 | incomplete | False |
| WF02 | 4 | 5.69094467366 | 2.36808041601 | 9.47232166405 | -2.01927806082 | incomplete | False |
| WF03 | 2 | 0.131362182966 | -0.442260348055 | -0.88452069611 | -1.01828481188 | incomplete | False |
| WF04 | 3 | 1.31376268109 | 0.120977704282 | 0.362933112845 | -0.598072807933 | incomplete | False |

Stitched: 12 trades; PF 2.0501357399181908; expectancy 0.5611028421662976; net R 6.733234105995571; DD -4.236778035610387; recovery 1.5892345667869106; win rate 0.3333333333333333.
Verdict: **WALK_FORWARD_BORDERLINE**. Known full-development 2024 robustness activity: 15 trades (comparison diagnostic only).

### T3

| Fold | Trades | PF C1 | Expectancy C1 | Net R | DD | Status | Included in pass |
|---|---:|---:|---:|---:|---:|---|---|
| WF01 | 0 | nan | nan | 0.0 | 0.0 | incomplete | False |
| WF02 | 6 | 0.282473625245 | -0.375063181947 | -2.25037909168 | -3.13630156446 | incomplete | False |
| WF03 | 2 | 0.0 | -0.461596866057 | -0.923193732114 | -0.923193732114 | incomplete | False |
| WF04 | 6 | 5.05506833653 | 2.04471222082 | 12.2682733249 | -2.02458030947 | incomplete | False |

Stitched: 14 trades; PF 2.283671542672255; expectancy 0.6496214643652504; net R 9.094700501113506; DD -5.533176483523269; recovery 1.6436671644571195; win rate 0.2857142857142857.
Verdict: **WALK_FORWARD_BORDERLINE**. Known full-development 2024 robustness activity: 14 trades (comparison diagnostic only).

Every fold starts FLAT while indicators receive only causal development history through its test end. Incomplete folds remain in the stitched diagnostic ledger but are excluded from pass-fold statistics.

C1 only; frozen candidates; 12 source hashes verified; no optimization, ranking, selection, or TRUE OOS read.
