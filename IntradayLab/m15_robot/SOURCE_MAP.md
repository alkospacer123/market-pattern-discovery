# Audited-source map — M15 offline foundation

## Durable execution & protection — audited H1 architectural sources

- `TradingSystemLab/stage8_robot/state.py` — durable SQLite intent and fill IDs, account-bound identity and recovery. `offline_intents.py` is a **new M15-isolated synthetic-only adaptation** of these invariants; no shared SQLite and no real ACK transport.
- `TradingSystemLab/stage8_robot/live_execution.py` — authorized order transmission requires distinct exact account, authorized commit, kill-switch and reconciled safety gate. M15 deliberately **does not yet include this adapter**.
- `TradingSystemLab/stage8_robot/protective_stop_contract.py` — H1 close-only SLTP `SLTP_QTY_MEASURE_PERCENT`, `100` percent and strictly tightening stop; the M15 rehearsal validates synthetic receipts but never claims broker-covered risk.

`tests/test_offline_intents.py` and `tests/test_offline_pipeline.py` are fully synthetic and may safely run without credentials. They do **not** establish actual FINAM order-price authority or LIVE approval.

## M15 candle source semantics and H1 continuation contract

- `TradingSystemLab/stage8_robot/finam_api.py` → M15 REST bar transport and official decimal `value` schema (READ-ONLY).
- `TradingSystemLab/stage8_robot/readonly_supervisor.py` → validated session windows EARLY/CORE/LATE, intraday clearing exclusions and schedule-end completion; M15 adds explicitly required 15-minute alignment. (READ-ONLY)
- `TradingSystemLab/stage8_robot/production_history.py` → immutable pinned historical-prefix seam and fail-closed overlap contract. `IntradayLab/m15_robot/continuation.py` is an isolated non-mutating M15 adaptation; historical data stays outside this repo.

M15 research source `IntradayLab/t3_m15_t1_entry_retest_v1/primary.py` requires the full warmup from past candles; missing old history cannot be replaced with a rolling 30-day-only indicator.

Source-label authority still unverified on a physical M15 FINAM payload, so the bridge refuses it by default. No FINAM tokens, live actions or H1 paths are touched.

Snapshot inspected before this task on actual GitHub main:
`2f0c9592bbca012471da9cbb15fdfaa764d8e17f`.

## M15 research authority
- `IntradayLab/SELECTED_T3_M15_SESSION_T1_R15.md` — user-selected identity and R15.
- `IntradayLab/t3_m15_t1_entry_retest_v1/primary.py` — original causal `features()` and selected `NEXT_OPEN` replay, reviewed without modifying it.
- `IntradayLab/t3_m15_t1_entry_retest_v1/SPEC.json` and `results/comparison_summary.csv` — 2 ATR initial, 3.5 ATR trailing, T1 and N4 evidence.

## FINAM read-only network adaptation

`IntradayLab/m15_robot/finam_readonly.py` adapts only the **GET-side and authentication** from `TradingSystemLab/stage8_robot/finam_api.py`, replaces the H1 hardcoded timeframe with the officially documented `TIME_FRAME_M15` and requires a dedicated exact one-account read-only scope. Order functions are **not** copied. Official reference: https://api.finam.ru/docs/rest/ ; H1 source has no edits.

Actual M15 timestamp semantics, schedule and completeness need verified independent FINAM read-only evidence before feeding a trading signal. Official M15 REST lookback is 30 days, not an alternative to immutable history.

## Latest read-only H1 source parity (repository GitHub verification)

The live H1 modules were fetched and compared to isolated M15 copies in this PR. Direct exact transformation check: **PASS / PASS**.

| H1 audited source file SHA (Git blob) | M15 local counterpart and transformation |
| --- | --- |
| `TradingSystemLab/stage8_robot/account_cleanliness.py` — `e3ad17c6f4330431b173658800489722a5731037` | `broker_status.py` — same executable code with a new module header |
| `TradingSystemLab/stage8_robot/production_broker_state.py` — `894321fc0d3101e75eea48f45ff3a26c0c0f58eb` | `broker_snapshot.py` — imports remapped to local broker_status, constants localized, error prefixes and active-stop comment owner renamed; no algorithm changes |

The new `shadow_state.py` / `shadow_service.py` are **offline shadow integration**, not an H1 release copy. They intentionally have **no REAL order transport or LIVE authorization**. The H1 live identity, token, task and SQLite are never accessed.

## H1 engineering sources (read-only, NEVER modify/import into M15 LIVE)
- `TradingSystemLab/stage8_robot/risk.py` — `risk=equity*0.015`, integer tick loss and downward rounding.
- `TradingSystemLab/stage8_robot/margin.py` — available cash / directional GO and min(risk quantity, margin quantity).
- `TradingSystemLab/stage8_robot/execution_grid.py` — outward stop projection and exact on-grid validation.
- `TradingSystemLab/stage8_robot/production_service.py` — strict broker/account binding, snapshot, reconciliation, time gates, actual broker fill authority and guarded transport.
- `TradingSystemLab/stage8_robot/production_runtime.py` — broker-neutral decisions and durable storage.
- `TradingSystemLab/stage8_robot/production_safety_gate.py` — position protection and reconciliation health before entries.

The copied concepts are **not permission to adopt H1 strategy settings**. The M15 second account's fresh authority and successful Intel dry-run/physical tests are required. Research snapshot does not prove live/Net economic performance; historical 2024 PF=1.460921 below 1.70 gate. No filter or optimization added.
