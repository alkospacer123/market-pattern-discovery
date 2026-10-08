# IntradayLab — compact research roadmap

This is an independent plan. It creates **no changes** to TradingSystemLab and **no LIVE authorization**.

| Step | Name | Exit evidence | Status |
| --- | --- | --- | --- |
| 0 | Independent project boundary | Dedicated research branch/folder, context, unchanged protected trees | COMPLETE — documentation-only setup, isolated diff audited |
| 1 | Dataset & execution specification | Confirm available M1 sources/timezones/sessions, instruments, dates, bid/ask or execution proxy, costs, exchange lot/margin, development and locked TRUE OOS | NOT STARTED |
| 2 | Baseline | Fixed, causal rules for VWAP mean reversion and volatility squeeze; baseline trade ledgers and cost-inclusive reports across predeclared TFs/instruments | NOT STARTED |
| 3 | Bounded Optimization | Small justified parameter set; no tuning against holdout and no PF chasing | NOT STARTED |
| 4 | Robustness | Execution costs/slippage stress, parameter neighborhoods, instrument/session variation, concentrated-trade and drawdown tests | NOT STARTED |
| 5 | Walk Forward | Chronological out-of-sample rolling validation, frozen protocol | NOT STARTED |
| 6 | TRUE OOS | One final assessment of frozen finalists on locked data, including 2025 only after formal unlock for TRUE OOS | NOT STARTED |
| 7 | Forward observation & separate-account readiness | Paper/read-only observation, broker-specific execution acceptance and audited protections; requires explicit authorization before any REAL orders | NOT STARTED |

## Baseline strategy scope

- Initial hypotheses: VWAP mean reversion (M3/M5/M15) and volatility squeeze breakout (M5/M15).
- Secondary hypotheses, **only after first pair is assessed**: liquidity sweep/false breakout (M1/M3/M5), intraday momentum/pullback (M5/M15).
- Instruments initially considered: USDRUBF, CNYRUBF, GLDRUBF, IMOEXF. Confirm continuous contract data availability and execution economics before committing research universe.
- M1 input bars may be used for causal higher-timeframe aggregation and fill modeling. No future bar in signal calculations.

## Acceptance logic

Choose only candidates with credible **after-cost** expectancy and robustness, sufficient independent trades, controlled tail risk, and repeatable chronological performance. An in-sample top performer is **not automatically a candidate**.

**Primary research objective:** maximize the share of positive **net calendar months**, aspiring to 12/12, while allowing negative days and weeks. Report positive-month ratio, worst month, longest run of losing months, year-by-year monthly results and open-position mark-to-market at month-end through Baseline, Walk Forward and TRUE OOS. Do not assume 12/12 is achievable, promise monthly profits, manipulate month-end exits, or raise risk to rescue a losing month. Monthly stability is a primary evaluation dimension alongside return and drawdown, not a hard in-sample fit target.

Cash-flow suitability is a separate gate from strategy profitability: simulate fees, taxes, losing months, drawdown-recovery time, minimum viable capital and realistic withdrawal schedules, including reserve protection and external transfers.

Do not advance a stage without an explicit audit of its real outputs. Do not create new research phases just to get a desired PASS.

## Hard safety guard

All commits in this branch must change files **only** below `IntradayLab/`; preserve `TradingSystemLab/`, `BBW/`, root files and other results unchanged. Future separate-account broker integration must never reuse TradingSystemLab account bindings, live credentials, SQLite state, operational tasks, or its risk authorities.
