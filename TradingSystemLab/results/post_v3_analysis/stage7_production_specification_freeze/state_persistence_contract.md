# State persistence contract

Atomically persist specification ID, open position and contract identity, direction, entry and initial stop, frozen initial risk and risk_cash, favorable extreme, current/canonical stop, TRAIL1 triggered/activated flags and times and stored candidate, last processed completed H1/context bars, last accepted signal/trade ID, pending order/idempotency state, fills, realized equity, and broker reconciliation marker. Restart must reconcile persisted state and broker positions/orders before processing later bars. Any mismatch blocks new entries.
