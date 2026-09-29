# Stage 6 IMOEXF Decision Tests

**Audit status:** PASS

**Decision status:** AUDIT ONLY — `PROD_STAGE6_83C7B31BB42C` remains unchanged.

## TRAIL1_TWO_VS_THREE_EVIDENCE

### Historical TRUE OOS metrics

| basket_or_symbol       | lifecycle           |   trades |   net_R |      PF |   expectancy_R |   max_DD_R |   recovery |   win_rate |   median_R |   positive_month_share |   monthly_median_R |   monthly_std_R |   worst_month_R |   monthly_equity_max_DD_R |   longest_negative_month_streak |   co_loss_months |
|:-----------------------|:--------------------|---------:|--------:|--------:|---------------:|-----------:|-----------:|-----------:|-----------:|-----------------------:|-------------------:|----------------:|----------------:|--------------------------:|--------------------------------:|-----------------:|
| CNYRUBF+GLDRUBF        | historical_true_oos |       90 | 51.8804 | 2.38156 |       0.576448 |   -7.2968  |    7.11002 |   0.544444 |   0.134889 |               0.571429 |          0.8051    |         6.02001 |        -2.75702 |                  -4.08512 |                               2 |                3 |
| CNYRUBF+GLDRUBF+IMOEXF | historical_true_oos |      140 | 65.0673 | 2.07283 |       0.464766 |   -8.57535 |    7.58771 |   0.535714 |   0.183053 |               0.666667 |          0.8051    |         6.25711 |        -3.75706 |                  -5.02091 |                               2 |                4 |
| IMOEXF                 | historical_true_oos |       50 | 13.1869 | 1.5709  |       0.263739 |   -3.83159 |    3.44164 |   0.52     |   0.319696 |               0.52381  |          0.0642367 |         1.63005 |        -2.22641 |                  -3.03164 |                               2 |                0 |

### All lifecycle marginal results

| lifecycle           |   three_instrument_net_R |   two_instrument_net_R |   IMOEXF_marginal_net_R |
|:--------------------|-------------------------:|-----------------------:|------------------------:|
| baseline            |                  57.671  |                44.6405 |                13.0305  |
| walk_forward        |                  32.9683 |                25.6052 |                 7.36307 |
| historical_true_oos |                  65.0673 |                51.8804 |                13.1869  |

The frozen TRAIL1 historical TRUE OOS marginal contribution is **13.186942 R**. This is historical evidence from an already revealed period, not fresh validation of a two-instrument identity.

### Mandatory IMOEXF reconciliation

Canonical/base-exit IMOEXF historical TRUE OOS is **3.323105 R**; frozen TRAIL1 is **13.186942 R**; the exact difference is **9.863837 R**. Numerically, matched trades contribute **4.224545 R**, canonical-only downstream trades remove **-5.639292 R** from the TRAIL1 total (bridge effect **5.639292 R**), and TRAIL1-only downstream trades add **0.000000 R**. These components sum to **9.863837 R**. The reconciliation CSV supplies deterministic entry keys, lifecycle, instrument, direction, both exit timestamps, both R outcomes, and delta R for every changed or unmatched trade. The difference is therefore an overlay-path and downstream entry-sequence effect, not an unexplained accounting anomaly.

## IMOEXF_MARGINAL_COST_SENSITIVITY

### All lifecycle cost points

| lifecycle           |   cost_multiplier |   three_instrument_net_R |   two_instrument_net_R |   IMOEXF_marginal_net_R |
|:--------------------|------------------:|-------------------------:|-----------------------:|------------------------:|
| baseline            |               1   |                  57.671  |                44.6405 |                13.0305  |
| baseline            |               1.5 |                  56.9335 |                43.9042 |                13.0293  |
| baseline            |               2   |                  56.196  |                43.168  |                13.028   |
| walk_forward        |               1   |                  32.9683 |                25.6052 |                 7.36307 |
| walk_forward        |               1.5 |                  32.8088 |                25.4462 |                 7.36262 |
| walk_forward        |               2   |                  32.6493 |                25.2872 |                 7.36216 |
| historical_true_oos |               1   |                  65.0673 |                51.8804 |                13.1869  |
| historical_true_oos |               1.5 |                  64.5045 |                51.3193 |                13.1853  |
| historical_true_oos |               2   |                  63.9418 |                50.7582 |                13.1836  |

Historical TRUE OOS detail:

| lifecycle           |   cost_multiplier |   three_instrument_net_R |   two_instrument_net_R |   IMOEXF_marginal_net_R |
|:--------------------|------------------:|-------------------------:|-----------------------:|------------------------:|
| historical_true_oos |               1   |                  65.0673 |                51.8804 |                 13.1869 |
| historical_true_oos |               1.5 |                  64.5045 |                51.3193 |                 13.1853 |
| historical_true_oos |               2   |                  63.9418 |                50.7582 |                 13.1836 |

The marginal benefit stays clearly positive at all three predeclared points; zero is not bracketed, so no break-even interpolation is reported. This is a **research friction-sensitivity audit**, not the literal Stage 7 commission/slippage model. Every multiplier is a cost-only overlay on immutable frozen TRAIL1 paths; no timestamp or path changes.

## IDENTITY_IMPLICATION

`CURRENT_STAGE6_ASSEMBLY_REMAINS_FROZEN`

No basket is selected here. Removing IMOEXF cannot be an in-place edit: it would require a new identity and prospective or separately justified untouched validation. Stage 7 was not executed.
