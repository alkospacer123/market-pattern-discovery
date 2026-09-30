# Risk and sizing contract

`current_equity` is the required starting equity plus realized PnL booked by completed exits; unrealized PnL is excluded. At one timestamp all exits are booked before entries. Each entry freezes `risk_cash = current_equity * 0.015` and its initial stop/1R. FULL never divides this budget by four; four positions imply 6% nominal initial risk.

For authenticated contract values: `stop_ticks = abs(entry - initial_stop) / price_step`; `loss_per_contract = stop_ticks * tick_value` (equivalently use an authenticated multiplier mapping); `quantity = floor_to_quantity_granularity(risk_cash / loss_per_contract)`. Non-integral ticks, nonpositive values, zero quantity, or unavailable specifications block entry. Exact FINAM/MOEX fields remain `BROKER_ADAPTER_BINDING_REQUIRED_STAGE8`; research R is not represented as live RUB PnL.
