# Execution units and transaction-cost formula

## Audit scope and finding

The frozen T1/T3 signal, entry, exit, ATR, stop and trailing rules were not changed. The old implementation used the dimensionally correct algebra, but configured `Si` as `tick_size = 1.0` while OHLC is stored in RUB per USD. The Si exchange quote point (one RUB per USD 1,000) is **0.001** in that price representation. This configuration/unit conversion bug charged 1,000 real Si ticks per requested stress tick. CNY was already configured as 0.001.

## Units

| Value | Unit |
| --- | --- |
| OHLC price | source price points: RUB per currency unit |
| ATR | source price points |
| `initial_stop` | source price |
| `initial_risk` / `initial_risk_points` | source price points, `abs(entry_price - initial_stop)` |
| `tick_size` | source price points per exchange tick |
| `gross_profit` | money (`profit_points * quantity * point_value`) |
| `gross_R` | dimensionless initial-risk units (`profit_points / initial_risk_points`) |
| tick transaction cost | ticks per side, converted to price points and then R |
| commission | money per contract per side |

## Previous implementation

`costs_money = 2 * (commission_per_unit + cost_ticks_per_side * tick_size * point_value) * quantity`

`net_R = gross_R - costs_money / (quantity * point_value * initial_risk_points)`

For tick-only stress this algebra simplifies to the confirmed formula below. The defect was the Si input (`tick_size = 1.0`), not double application or the equation itself. Slippage, when configured separately, adjusts execution prices and is not included in these C0/C0.5/C1/C2 tick-only runs.

## Confirmed/corrected model

```
price_cost_per_side = cost_ticks_per_side * tick_size
round_trip_cost_points = 2 * price_cost_per_side
initial_risk_points = abs(entry_price - initial_stop)
initial_risk_ticks = initial_risk_points / tick_size
cost_R = round_trip_cost_points / initial_risk_points
net_R = gross_R - cost_R
```

`initial_risk_points > 0` and `tick_size > 0` are enforced. Quantity and point value cancel exactly in R normalization. Cost stress is subtracted once; it does not alter entry/exit or gross P&L. `PF_R` explicitly denotes profit factor calculated from per-trade net R.

## Data safety

Only explicitly selected 2023–2024 files are read. Observed increments are diagnostics of stored OHLC granularity, not substitutes for configured instrument metadata. No 2025+ TRUE OOS data is read.
