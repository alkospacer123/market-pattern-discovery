# IntradayLab M15 robot — isolated offline foundation

**STATUS: CODE FOUNDATION / OFFLINE ONLY / NOT_LIVE_AUTHORIZED.** No order-capable FINAM adapter, order token access, Windows Scheduled Task modification, automatic startup or real brokerage action exists in this package. **Do not deploy to the running H1 checkout.**

## Selected immutable identity

- User-selected: `T3_M15_T1_TRAIL35_N4_R15`.
- Research authority: `T1_NEXT_OPEN_TRAIL_3p5` from merged #518.
- N4: USDRUBF / CNYRUBF / GLDRUBF / IMOEXF; both directions.
- Signal on **completed close-labelled M15**, context from **causally published** H1.
- Session T1 on **signal close**: [10:00,18:00) MSK.
- Historical NEXT_OPEN means price of the immediately adjacent candle Open **at the just-completed signal's timestamp**, not waiting a further 15 minutes.
- Live future adapter must submit as soon as safely possible *after* completed M15 and use **actual FINAM fills**, not pretend guaranteed Open/Close.
- Initial Stop 2 × signal ATR14; trailing 3.5 × ATR (no +1R delay), tighten only after survived M15; no signal-candle extrema.
- One position per instrument, no pyramiding or 18:00 forced close.
- R15 1.5% of authenticated M15 **realized** equity per new position, maximum 6% portfolio nominal initial risk. Margin cap with downward lot rounding, zero remains zero.
- Possible R20 requires a later **separate** user decision, never automatic.

## Exactly what has been built in this PR

1. `feature_adapter.py`: offline causal completed-bar wrapper on **the already audited read-only feature function** of `IntradayLab/t3_m15_t1_entry_retest_v1/primary.py`. **No new signal calculations or tuning.** Includes T1 gate, latest signal ID, H1 publication guard and historical NEXT_OPEN adjacency.
2. `grid_risk.py`: independent M15 port of H1's `execution_grid.py` outward projection, `risk.py` (R15), `margin.py` (minimum of risk and available margin). Initial protective stop uses the actual fill price. Trailing proposals require a **survived** completed bar and are not claimed to be broker fills or acknowledged SLTP updates.
3. `account_boundary.py`: independent account SHA and runtime-root separation; unconditional denial for all real order attempts.
4. `tests/test_foundation.py`: deterministic synthetic checks for selected identity, causal session, risk/margin, stop-grid, trailing and account isolation.

The reference research function is intentionally **imported read-only** for the offline prototype. Before a real runner exists, verify parity of a bounded production-oriented rolling M15 adapter against #518 and the FINAM close-label timing authority, then implement the H1-authorized execution/state/stop/launch sequence as an isolated **copy/adaptation**, without runtime imports from TradingSystemLab. This is **an engineering parity requirement, not new strategy research**.

## What must be reused from H1 rather than redesigned

| Existing audited H1 source (read-only) | Future isolated M15 adaptation |
| --- | --- |
| `TradingSystemLab/stage8_robot/finam_api.py` | FINAM REST transport, session, bars, account/orders, bounded retries |
| `TradingSystemLab/stage8_robot/production_service.py` | Operator/clock/entry cycle, account snapshot, reconciliation before entries, heartbeat |
| `TradingSystemLab/stage8_robot/production_runtime.py` | Durable exactly-once intents, ENTRY/STOP/EXIT transitions |
| `TradingSystemLab/stage8_robot/live_execution.py` | Real order safety and stop implementation **only after explicit authorization** |
| `TradingSystemLab/stage8_robot/execution_grid.py` | Outward stop tick rounding, strict executable price grid |
| `TradingSystemLab/stage8_robot/risk.py`, `margin.py` | Realized-capital R15, authenticated contract step/cost, available GO |
| `TradingSystemLab/stage8_robot/production_safety_gate.py` | Separate kill switch, position/stop ownership, fail-closed heartbeat |
| `TradingSystemLab/stage8_robot/state.py`, `operations.py` | **Separate** SQLite/lock/log file and crash recovery |
| `TradingSystemLab/stage8_robot/deploy/windows/` | Separate Windows Task name, runtime root, service principal and startup script |

**Do not** copy H1's Stage 7 identity, H1 EMA100, 2.5ATR initial stop, TRAIL1, Stage 5 H1 frozen series, SQLite, token, account ID, task, or any LIVE authorization. Do not deploy/call FINAM until **separate M15 operator acceptance**.

## Local offline tests

From the repo root in a Python environment with pandas/numpy:

```bash
python -m unittest discover -s IntradayLab/m15_robot/tests -v
```

These files are designed for offline execution with **no broker credentials or network**. This PR does not establish test PASS unless the tests are run independently in an environment with the repository and their results are retained.

## Recorded constraints and pending integration

- Source of truth: `IntradayLab/SELECTED_T3_M15_SESSION_T1_R15.md`; historical source `IntradayLab/t3_m15_t1_entry_retest_v1/SPEC.json`.
- Need M15-specific FINAM candle timestamp/availability check. H1 label semantics **must not be assumed** to apply to M15.
- Need separately provisioned M15 account, signed/hashed exact account binding, CurrentUser token, isolated persistent state and task.
- Need proven fill-price authority, immediate protected stop coverage, partial-fill growth, broker stop reconciliation and safe restart. No order-capable code in this first PR.
- **Do not silently arm**, schedule, create a real order, merge this PR or touch the H1 robot as a consequence of these docs/tests.
