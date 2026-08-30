# Cycle 18 runner tie semantics

Frozen before Cycle 18 PnL.

- `reclaim_bars=0` means sweep bar only; 1 means sweep bar plus the next eligible exact M5 bar; 2 means sweep bar plus the next two.
- High-side and low-side state machines are otherwise independent.
- If both new sweep conditions first occur on the same M5, both attempts are marked ambiguous/done with no signal.
- If independent state machines later produce opposite trade signals at the exact same signal timestamp, both signals are skipped as `AMBIGUOUS_OPPOSITE_SIGNAL` before the one-position rule.
- Episode high/low includes permitted raw M1 from sweep M5 start through reclaim decision time, excluding the entry row.
- Same candidate trade-path/friction semantics remain those frozen in prior runner contracts.