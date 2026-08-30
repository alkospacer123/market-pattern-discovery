# Cycle 14 — CNY Session-VWAP Exhaustion/Reclaim — Result

Status: **NO_EXECUTABLE_CANDIDATE**

The Cycle 14 hypothesis, candidate grid, and runner semantics were committed before any Cycle 14 PnL was computed.

## Safety

- Research data actually used: CNYRUBF M1 with `2026-01-05 <= t < 2026-05-16` only.
- Retired `2026-05-16` through `2026-07-01`: **NOT USED**.
- 2025 TRUE OOS: **NOT ACCESSED**.

## Frozen search space

- 48 candidates.
- `k`: 1.25, 1.50, 1.75, 2.00.
- `reclaim_bars`: 1, 2, 3.
- `rr_min`: 1.00, 1.25.
- context: `NONE`, `LOW_ER`.

## Result

Across the full candidate grid the state machines produced 1,282 reclaim events before execution eligibility:

- 1,250 were rejected by the preregistered minimum reward/risk test.
- 32 were rejected because the frozen signal-time VWAP was not favorable to the intended trade direction at the exact next-M1 entry.
- Executed trades: **0**.
- BASE-profitable registry candidates: **0**.
- Strict research survivors: **0**.

Raw reward/risk across all 1,282 reclaim events:

- median: 0.270854
- P90: 0.665941
- P95: 0.732424
- P99: 0.862021
- maximum: **0.917499**

Thus no event reached even the lowest frozen `rr_min=1.00`. This is a structural falsification of this exact entry/stop/target formulation, not a profitability failure after execution.

## Scientific disposition

The Cycle 14 parameters are not relaxed after seeing this result. In particular, `rr_min`, the episode stop, and the frozen-VWAP target are not changed and the candidate set is not re-run. Cycle 14 remains a completed negative benchmark.

Any subsequent cycle must be a separately preregistered hypothesis class. No information from retired May16–Jul1 or from 2025 TRUE OOS may be used.