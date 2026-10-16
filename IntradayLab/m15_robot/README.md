# IntradayLab M15 robot — isolated offline foundation

**Инженерный порядок работ, обязательные проверки и условия допуска M15 к LIVE:** [ROADMAP.md](ROADMAP.md). Он описывает внедрение выбранной сборки, не новые исследования, и имеет приоритет как актуальная последовательность реализации.


## H1-style durable intent/fill/stop rehearsal (synthetic only)

`offline_intents.py` ports the **safety lifecycle**, not executable H1 trade authority:
- Separate `m15-offline-intents.sqlite3`, bound to a hash of the **distinct M15** account and selected M15 robot identity. Strict table/column verification, integrity validation and symlink refusal. No H1 SQLite opened.
- `prepare()` durably records the intended order **before** any hypothetical broker POST. Same idempotency key is a no-op, conflicting payloads and second same-instrument entry are rejected.
- `uncertain()` does not retry; a fresh synthetic broker receipt is needed to move out of uncertain state. Synthetic ACK/fill IDs cannot be mistaken for proof from FINAM. Partial fills, overfill, weighted-average price and duplicate fill conflict handled explicitly.
- `synthetic_stop_ack()` tests the audited H1 **100%-of-position** stop policy, valid initial side, and strictly tightening replacements. Acknowledgment only after simulated broker fill. No source module capable of real order transmission exists.
- `tests/test_offline_intents.py` has 20 targeted regression tests; `tests/test_offline_pipeline.py` has 3 cross-component rehearsals of GET-only broker cleanliness, R15/margin sizing, durable intent, partial fill, stop 100%, restart and UNCERTAIN duplicate rejection.

**This is NOT real broker reconciliation or proof of protective SLTP installation.** It is synthetic preparation for porting H1's audited `production_runtime.py` / `live_execution.py`. The next integration must verify authoritative broker order IDs, durable actual fill prices, partial fill expansion and broker-proven SLTP activation before any real account can trade. For the entire Draft PR, the order endpoint remains structurally absent and `execution_authorized=False`.

## M15 candle finalization and frozen-history continuation (offline)

Latest implementation includes:

- `bar_bridge.py`: validated FINAM trading windows (same H1 schedule categories), exact M15 price/volume schema, broker open-labelled timestamp grid and causal translation to *close-labelled MSK* research bars. An intraday M15 bar requires a directly adjacent next bar **open** witness, with the next candle's OHLC never used; a final bar at a verified session end is allowed by H1-equivalent schedule-completion authority. No missing intraday bars are invented. Strict source-label authority defaults **OFF** until operator verification. No trading permission is granted by this boolean.
- `continuation.py`: H1-style immutable-history overlap guard for stitching FINAM's 30-day M15 REST response onto separately authenticated prior M15 history; refuses absent overlap, revised historical OHLCV, duplicate bars and altered clocks. The full research indicator context must be maintained. A short 30-day-only EMA/ADX calculation must **not** be used as a production signal authority.
- `tests/test_bar_bridge.py`, `tests/test_continuation.py`: synthetic schedule-end, gaps, no next bar, float/schema corruption, missing seam and unchanged-prefix cases.

**Pending exact authority:** physical FINAM M15 source open-label/finalization evidence, independent historical series seed SHA, price/volume overlap against FINAM and 2023–2026 research parity. The historical seed may be older than FINAM's supported 30-day window; if a clean seam cannot be proven, the pipeline must halt, not silently concatenate or substitute data.

**Official reference:** [FINAM REST bars](https://api.finam.ru/docs/rest/) documents `TIME_FRAME_M15` and 30-day lookback. `bar_bridge.py` consumes the documented REST `{"value":"..." }` OHLCV format. No live API credentials have been accessed or supplied.

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

## FINAM M15 read-only transport (added, no orders)

The isolated `finam_readonly.py` ports H1's authenticated REST request structure to M15. It exposes `connect_readonly()`, `account()`, `orders()`, `asset_params()`, `schedule()` and `bars_m15()`. It requires a separate single-account `readonly == true` FINAM token and enforces the exact M15 account binding. Only session creation/detail POSTs exist; all other supported requests are **GET only**. There is no submission/cancel/SLTP method. The official FINAM REST `TIME_FRAME_M15` enum and 30-day M15 retention are documented; this does **not** prove timestamp/boundary/finalization behavior of an actual FINAM response. No token is provisioned or used in this PR.

`tests/test_finam_readonly.py` contains 11 synthetic, transport-injected tests for exactly those boundaries, including cross-account denial and blocked order-path methods. It does not contact FINAM.

## Continued H1 reuse: broker read-side and durable shadow

The same PR now also includes **a separate persistent read-only shadow** built from inspected H1 sources:

- `broker_status.py`: byte-equivalent port of H1 `account_cleanliness.py` aside from a source header. Exact documented FINAM order statuses, aliases, terminal/active separation; unknown states fail closed.
- `broker_snapshot.py`: transformed-but-computationally-equivalent port of H1 `production_broker_state.py`, with M15-local imports, error namespace and `m15:` protective-stop comments. It strictly parses position quantity, regular/SLTP order records and stop coverage contract; it has **no** order method.
- `shadow_state.py`: isolated M15 SQLite authority (account-hashed, immutable binding, create-once and integrity-checked), monotonically timestamped sanitized receipts, no positions/intents/credentials/order transmission in storage and permanently `HALTED`.
- `shadow_service.py`: one **GET-side only** injected-broker observation using the ported order/position parser. Foreign/nonzero exposure, active orders, wrong account, unknown status, malformed schema or read failures produce `FAULT_HALTED`. `HEALTHY_READONLY` is **never authorization**.
- `tests/test_shadow.py`: 18 offline synthetic cases covering broker statuses, fake orders and positions, wrong-account denials, SQLite restarts, duplicate cycles and no broker POST/DELETE execution.

Source parity of the two ports has been verified through GitHub with the actual H1 code: **PASS** for both exact specified transformations. The H1 original SHA/blob IDs are recorded in `SOURCE_MAP.md`.

**Limit:** no M15 token or actual FINAM account has yet been connected. The read-side shadow consumes only a fake/injected API interface. Full offline test run and Intel physical read-only acceptance remain pending; no claim of those PASS statuses.

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
