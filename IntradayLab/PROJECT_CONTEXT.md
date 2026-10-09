# IntradayLab — project context

Established 2026-10-08. Independent research scope, **not** TradingSystemLab roadmap work.

## User-defined intent

- Moderately aggressive active growth, not maximum leverage.
- A profitable intraday strategy might fund transfers **into** the already-active TradingSystemLab and later planned living expenses.
- **Primary return-shape objective:** strive for positive **net trading P&L in every calendar month (12/12 as an aspirational target)**. Losing days and weeks are acceptable; losing months should be minimized. This is an evaluation goal, **never a guarantee or a mandate to increase risk near month-end**.
- Long-run ambition is dependable *financial capacity* for living expenses and transfers to TradingSystemLab, not a false promise that each month will be profitable.
- Instruments are exactly four MOEX perpetual futures for the initial research: USDRUBF, CNYRUBF, GLDRUBF, IMOEXF. **M5 is the execution/signal timeframe**. Test context from completed M30 bars first; restricted alternatives are M15 (VWAP) and H1 (Momentum). No M1/M3/M10 research, and do not assume higher trade frequency improves returns.
- Future LIVE execution on a **new, distinct FINAM brokerage account**, with its own broker authentication, risk ledger, capital authority, state, protection, reconciliation, kill switch, and operator authorization.
- There must be absolutely **no modification to any TradingSystemLab files or production robot**. Any conceptual borrowing from TradingSystemLab is process-level, not evidence-level or strategy inheritance.

## Portfolio and cash-flow discipline (research requirements, not an authorized LIVE sizing spec)

- Start with moderate study limits: candidate risk of 0.25–0.5% of the **new account's** realized equity per trade; research daily loss guard 1–1.5%; weekly guard 3%. Final thresholds require independent validation and explicit approval.
- Model real contract minimums and margin; skip entries when integer sizing would exceed the limit. Do not use martingale or averaging against a stop.
- Record **gross P&L, fees, slippage, taxes as applicable, external transfers, withdrawals, realized trading P&L, and capital separately**. Deposits and transfers are never counted as trading profit.
- Living withdrawals and TradingSystemLab transfers can be made only from distributable realized profits after costs and estimated taxes and after preserving a drawdown/margin reserve, operational liquidity and a predefined high-water-mark rule.
- Do not base fixed recurring expenses on a required winning month. Build an independent living expense reserve before considering full-time trading. Evaluate rolling 3/6/12-month profit, losing-month rate, duration of drawdowns, sequence risk and withdrawal stress.
- Both accounts remain independent even when profits are transferred: an outward transfer from IntradayLab and an inward contribution to TradingSystemLab are **external cash flows**, not strategy performance.
- Track positive-month share, worst calendar month, consecutive losing months, and each calendar year's monthly breakdown in Baseline, Walk Forward, TRUE OOS and forward monitoring. Calculate monthly mark-to-market equity including open-position P&L and all execution costs; never hide a loss by deferring realization into the next month.
- No promises of a stable monthly salary, guaranteed PF, target return, or target risk-adjusted performance without real evidence.

## Project initial state

- TradingSystemLab main was inspected **read-only** before setup, at commit `eaaef0884fb54eb5c3946f433619b550545a19a8`.
- Historical setup branch: `research/intraday-lab`, created from the original inspected main commit. The current primary branch is **main**; IntradayLab changes reach it through separate task PRs with independent audit. No task PR merge or next-stage advancement is automatic.
- All project content is under `IntradayLab/`. Stage 0 is COMPLETE; the base pre-2025 audit of 16 CSVs is performed. No strategy/backtest has been executed and there is no FINAM account integration or LIVE authorization. Stage 1 remains OPEN.
- Frozen initial strategy priority (user decision, 2026-10-08): (1) VWAP Mean Reversion; (2) Intraday / Session Momentum; (3) Volatility Squeeze Breakout only after the first two are assessed. Liquidity Sweep remains a reserve idea. **Order Flow Imbalance is excluded** (no historical order-book data). First-cycle Baseline: M5-only / M30->M5 / one alternative context for each of the first two strategies; full matrix and phase gates in ROADMAP.md.

## Verified input inventory (2026-10-08)

- Read-only historical source: alkospacer123/market-pattern-data, forever/{INSTRUMENT}/{INSTRUMENT}_{TF}.csv.
- Inspected market-pattern-data main: f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8.
- GitHub path listing verified **16/16 CSVs**: M5, M15, M30, H1 for each of USDRUBF, CNYRUBF, GLDRUBF and IMOEXF.
- Full pre-2025 CSV audit recorded in [STAGE1_DATA_AUDIT_20261008.md](reports/STAGE1_DATA_AUDIT_20261008.md). M5 history: USDRUBF/CNYRUBF from 2023-01-03, GLDRUBF from 2023-07-11, IMOEXF from 2023-11-14. Across the 16 pre-2025 files, basic parse/ordering/duplicate/OHLC/volume checks passed. Fully populated M5 aggregation buckets agree exactly with available M15/M30/H1 OHLCV. **20 IMOEXF M15 bars on 2024-08-16 19:00-23:45 lack any M5 bucket**; do not fabricate them. Three 2024 trading Saturdays are valid according to MOEX.
- **Stage 1.2 COMPLETE**, [PR #439](https://github.com/alkospacer123/market-pattern-discovery/pull/439) **MERGED** into main at `9e1bc52a5364c6d5979b2743a4b6259d25192f17`, independent audit PASS. Historical [report](reports/STAGE1_2_SESSION_MTF_AUDIT.md), JSON, code and tests remain unchanged; their original pending-audit status records the reproducible run. Zero real MTF contexts are authorized because timestamp/session evidence is unresolved. Preserve the IMOEXF quarantine `[2024-08-16 18:45, 2024-08-17 00:00)` in CSV-clock across all TF and carry intervals. USD/CNY M5/M15 lack 31.08.2023; gaps are not repaired from higher TF.
- **Stage 1 OPEN**, not Baseline-ready. The [Execution, Costs & Funding Specification](reports/STAGE1_EXECUTION_COSTS_SPEC.md) is **STAGE1_EXECUTION_SPEC_PENDING_AUDIT**. It separates current reference specs from historical evidence, records CNY's tick change at 19:00 MSK 27.09.2023, and distinguishes historical funding clearing around 18:50 from current 23:50 after the 2026 unified-session change. It fixes causal M5/Stop-first/nonfill/forced-flat policies and proposes calendar development through 2023 plus future quarterly WF blocks in 2024 without running them. Exact historical fees/margin/funding inputs, account-specific FINAM tariff, export provenance, clock semantics and fill evidence remain UNRESOLVED. No TradingSystemLab C1 model is inherited.
- On source HEAD `f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8`, the five `forever/` README files contain no provenance metadata. OHLCV agreement does not certify timezone, timestamp meaning, exporter or Volume. This documentation task read no market CSV; 2025+ remains closed, and Stage 2 Baseline is NOT STARTED.
- 2025+ TRUE OOS remains locked for strategy research; do not inspect it to choose candidates. Choose and document the valid pre-2025 development window after a data availability audit.

## Project discipline

After each task: independently verify actual GitHub branch, diffs, changed files, protected TradingSystemLab subtree, reproducibility and stage status. Do not advance research stages automatically without an audit or user approval.
