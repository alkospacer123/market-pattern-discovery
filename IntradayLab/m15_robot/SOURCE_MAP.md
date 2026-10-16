# Audited-source map — M15 offline foundation

Snapshot inspected before this task on actual GitHub main:
`2f0c9592bbca012471da9cbb15fdfaa764d8e17f`.

## M15 research authority
- `IntradayLab/SELECTED_T3_M15_SESSION_T1_R15.md` — user-selected identity and R15.
- `IntradayLab/t3_m15_t1_entry_retest_v1/primary.py` — original causal `features()` and selected `NEXT_OPEN` replay, reviewed without modifying it.
- `IntradayLab/t3_m15_t1_entry_retest_v1/SPEC.json` and `results/comparison_summary.csv` — 2 ATR initial, 3.5 ATR trailing, T1 and N4 evidence.

## H1 engineering sources (read-only, NEVER modify/import into M15 LIVE)
- `TradingSystemLab/stage8_robot/risk.py` — `risk=equity*0.015`, integer tick loss and downward rounding.
- `TradingSystemLab/stage8_robot/margin.py` — available cash / directional GO and min(risk quantity, margin quantity).
- `TradingSystemLab/stage8_robot/execution_grid.py` — outward stop projection and exact on-grid validation.
- `TradingSystemLab/stage8_robot/production_service.py` — strict broker/account binding, snapshot, reconciliation, time gates, actual broker fill authority and guarded transport.
- `TradingSystemLab/stage8_robot/production_runtime.py` — broker-neutral decisions and durable storage.
- `TradingSystemLab/stage8_robot/production_safety_gate.py` — position protection and reconciliation health before entries.

The copied concepts are **not permission to adopt H1 strategy settings**. The M15 second account's fresh authority and successful Intel dry-run/physical tests are required. Research snapshot does not prove live/Net economic performance; historical 2024 PF=1.460921 below 1.70 gate. No filter or optimization added.
