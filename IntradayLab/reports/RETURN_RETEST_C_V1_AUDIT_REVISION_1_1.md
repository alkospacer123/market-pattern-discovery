# C_v1 independent reporting audit revision 1.1

The first C_v1 Baseline ran only after pre-P&L freeze
16d07c2c5dc7b3fe5ceb90760e9ce4a7ed17358f. The original frozen auditor 1.0
matched every instrument's constructions, execution dispositions, CLOSED and
EXCLUDED paths, economics/distributions, geometry and calendar coverage before
failing the pooled normalized-R Net_R string comparison.

The failure is a reporting-auditor defect, not a trading or parameter defect.
The frozen common closed_metrics sorts closures by (resolved_at, signal_id)
before summing normalized Net R. Auditor 1.0 summed pooled trades in instrument
ledger order. With 28-digit Decimal arithmetic the actual ledger-order sum is
-84.18333333333333333333333343 and the chronological sum is
-84.18333333333333333333333345: difference -2E-26 R.

Separate **C_V1_AUDIT_1.1** supplies the same independent mathematical checks
with the explicit chronological order for closed metrics. The additional
Gross_R/Cost_R retain ledger-order sums, exactly as the frozen C report contract.
No tolerance, rounding, dropped assertion or rewritten historical result is
used. Four additional synthetic tests verify chronological accumulation,
retained Gross/Cost order, exact forged-PF rejection and restoration of the
original auditor function. The 1.1 manifest and code are separately committed
before complete re-audit and two full deterministic verification repeats.

C_v1 strategy, config/hash, common core, runner, original auditor 1.0 and every
first-run trading/report byte remain unchanged. This does not create C_v2,
select parameters or improve PF. Config remains
879801c71ce7d56972c17886ef3f33caf6c6c9d2df81fc3d49f068ec173e27df.
The original validator is preserved; reproduce with the explicitly versioned
adapter:

```bash
python -m IntradayLab.tools.validate_return_retest_baseline_v1_1 \
  --data-root /workspace/market-pattern-data \
  --output IntradayLab/work/fresh_c_v1_validation
```

The final validation receipt records both the trading freeze and audit revision
commit, hashes, full checks and repeat results. This is implementation
independence by the task author, not external human approval.
