# IntradayLab — project context

Established 2026-10-08. Independent research scope, **not** TradingSystemLab roadmap work.

## User-defined intent

- Moderately aggressive active growth, not maximum leverage.
- A profitable intraday strategy might fund transfers **into** the already-active TradingSystemLab and later planned living expenses.
- Long-run ambition is dependable *financial capacity*, not a false promise that each month will be profitable.
- Instruments: MOEX futures; evaluate timeframe(s) among M1, M3, M5, M10, M15 based on forward-credible evidence, not assumed trade frequency.
- Future LIVE execution on a **new, distinct FINAM brokerage account**, with its own broker authentication, risk ledger, capital authority, state, protection, reconciliation, kill switch, and operator authorization.
- There must be absolutely **no modification to any TradingSystemLab files or production robot**. Any conceptual borrowing from TradingSystemLab is process-level, not evidence-level or strategy inheritance.

## Portfolio and cash-flow discipline (research requirements, not an authorized LIVE sizing spec)

- Start with moderate study limits: candidate risk of 0.25–0.5% of the **new account's** realized equity per trade; research daily loss guard 1–1.5%; weekly guard 3%. Final thresholds require independent validation and explicit approval.
- Model real contract minimums and margin; skip entries when integer sizing would exceed the limit. Do not use martingale or averaging against a stop.
- Record **gross P&L, fees, slippage, taxes as applicable, external transfers, withdrawals, realized trading P&L, and capital separately**. Deposits and transfers are never counted as trading profit.
- Living withdrawals and TradingSystemLab transfers can be made only from distributable realized profits after costs and estimated taxes and after preserving a drawdown/margin reserve, operational liquidity and a predefined high-water-mark rule.
- Do not base fixed recurring expenses on a required winning month. Build an independent living expense reserve before considering full-time trading. Evaluate rolling 3/6/12-month profit, losing-month rate, duration of drawdowns, sequence risk and withdrawal stress.
- Both accounts remain independent even when profits are transferred: an outward transfer from IntradayLab and an inward contribution to TradingSystemLab are **external cash flows**, not strategy performance.
- No promises of a stable monthly salary, guaranteed PF, target return, or target risk-adjusted performance without real evidence.

## Project initial state

- TradingSystemLab main was inspected **read-only** before setup, at commit `eaaef0884fb54eb5c3946f433619b550545a19a8`.
- Branch planned/created: `research/intraday-lab`, based on the above commit.
- All new project content is under `IntradayLab/`. New strategies/backtests/validation/results not executed. No data ingestion. No FINAM trading account integration.
- Initial research priority: VWAP mean reversion and volatility squeeze, then liquidity sweep and momentum/pullback as independent follow-ons.

## Project discipline

After each task: independently verify actual GitHub branch, diffs, changed files, protected TradingSystemLab subtree, reproducibility and stage status. Do not advance research stages automatically without an audit or user approval.
