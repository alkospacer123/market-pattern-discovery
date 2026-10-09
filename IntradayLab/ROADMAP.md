# IntradayLab — research roadmap

Decision: **2026-10-08**. Independent intraday research on MOEX perpetual futures. **Only IntradayLab/ may be changed.** This roadmap does not authorize real orders or affect the production TradingSystemLab robot.

## Research target

Build a moderately aggressive, after-cost intraday system with a high fraction of **positive net calendar months** (12/12 is an aspiration, never a guarantee). Negative days/weeks and some negative months are possible. Evaluate profitability, worst month, consecutive losing months, total and monthly drawdown, time to recovery, sufficient independent opportunities, trading costs, and capacity to fund future withdrawals. Never increase risk or manipulate month-end exits to force a positive month.

**Trading cadence is an observed outcome, not a trading quota.** The provisional aggregate planning range across all four instruments is roughly 5–15 trades/week (20–60/month), with no requirement to trade on every day. Reject overtrading that erases net expectancy.

## Frozen initial research scope

**Instruments (perpetual MOEX futures only):**
- USDRUBF
- CNYRUBF
- GLDRUBF
- IMOEXF

**Source:** read-only repository alkospacer123/market-pattern-data, path forever/{INSTRUMENT}/{INSTRUMENT}_{TF}.csv. At inventory inspection, market-pattern-data main = f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8.

**Available files verified by GitHub directory listing (16/16):**

| Perpetual instrument | M5 | M15 | M30 | H1 |
| --- | --- | --- | --- | --- |
| USDRUBF | present | present | present | present |
| CNYRUBF | present | present | present | present |
| GLDRUBF | present | present | present | present |
| IMOEXF | present | present | present | present |

**Current evidence:** the pre-2025 data-content audit has now been performed; see [Stage 1 Data Audit](reports/STAGE1_DATA_AUDIT_20261008.md). M5 data begin 2023-01-03 (USDRUBF/CNYRUBF), 2023-07-11 (GLDRUBF), 2023-11-14 (IMOEXF). Basic OHLC/timestamps/tick tests pass, but the 2024-08-16 IMOEXF M15 evening interval has 20 M15 bars without M5 counterparts. Timezone, actual historical sessions, financing/commission assumptions and intrabar execution remain validation gates; **Stage 1 is not complete**.

**Timeframes:** M5 for signals and price-based execution simulation. M15 / M30 / H1 are candidate *context* timeframes; **M30 -> M5 is the lead hypothesis**, not a preselected winner. Research is strictly intraday. No M1 or M3/M10 data or M1 execution assumptions. No order-book strategy: **Order Flow Imbalance excluded** because historical order-book data is unavailable.

**Initial strategies, in sequence:**
1. **VWAP Mean Reversion** — M5 standalone; M30 -> M5 principal MTF comparison; M15 -> M5 secondary comparison. VWAP is session-anchored. If only OHLCV bars are available, label volume-weighted typical-price VWAP as an approximation, not an observed transaction VWAP. Assess the risk of countertrend entries.
2. **Intraday / Session Momentum** — M5 standalone; M30 -> M5 principal MTF comparison; H1 -> M5 secondary comparison. Measure session- and instrument-dependent continuation without forcing an H1 holding period.
3. **Volatility Squeeze Breakout** — **after** the first two strategies are assessed: M5 standalone versus M30 -> M5. Test whether it adds independent portfolio value beyond Momentum.
4. **Liquidity Sweep / False Breakout** — reserve hypothesis only, not part of initial implementation, subject to a later explicit scope decision.

Initial Baseline design: **6 strategy/architecture variants x 4 instruments = up to 24 runs**, conditional on Step 1 quality gates. These are predeclared comparisons, not optimizer output. The later Squeeze pair would add up to 8 runs only if explicitly started. Do not multiply variants or optimize timeframe choices using TRUE OOS.

**MTF causality:** use only the last fully closed higher-timeframe bar available at each completed M5 signal. Check time-zone, session anchoring, resampling agreement, trading halts/gaps, and boundary resets. Source M5 is the finest available bar: same-bar stop/target ordering is ambiguous; model conservatively, stress alternatives or flag unresolved cases. Do not invent M1-level precision. Validate any backtest fills against the actual execution mechanism and available bid/ask information.

## Stages and exit evidence

| Step | Stage | Required deliverable / exit gate | Status |
| --- | --- | --- | --- |
| 0 | Separate project boundary | Research branch + IntradayLab folder, written constraints; protected trees unchanged | **COMPLETE** |
| 1 | Dataset and execution specification | Audited 16 CSVs: date coverage, timezone/bar timestamp meaning, schemas, duplicates, OHLC consistency, missing bars/sessions, volume, cross-TF agreement; venue calendar, actual instrument specs, tick/lot/margin, FINAM + exchange fees, spread/slippage/nonfill model; frozen pre-2025 development scope and TRUE OOS boundary | **IN PROGRESS — 16/16 pre-2025 CSV content audit performed; basic OHLC/timestamp PASS; IMOEXF M15 anomaly, timezone, historical calendar, fees and fill model remain open** |
| 2 | Baseline | Causal fixed-rule VWAP and Momentum implementations; predeclared six architectures; per-run trade ledgers, after-cost metrics, direction/instrument/monthly reports, no parameters fitted to TRUE OOS | **NOT STARTED** |
| 3 | Bounded Optimization | Only a small prejustified parameter set where Baseline supports it; immutable run manifests, no mass search, no PF-only ranking | **NOT STARTED** |
| 4 | Robustness | Parameter-neighborhood, instruments, session regimes, trading costs, widened slippage, ambiguous fills, adverse months, concentration and drawdown | **NOT STARTED** |
| 5 | Walk Forward | Chronological rolling tests with no future-informed decisions; frozen rules; monthly and portfolio comparisons | **NOT STARTED** |
| 6 | TRUE OOS | Single separately authorized final assessment on **untouched 2025+ data**, frozen finalists and costs, full calendar-month + instrument/portfolio reports | **NOT STARTED / LOCKED** |
| 7 | Forward observation and separate FINAM-account readiness | Read-only/paper monitoring; fully independent credentials, account bindings, sizing, order ledger, reconciliation, kill switch; explicit approval required for real orders | **NOT STARTED / NO LIVE AUTHORIZATION** |

**2025 onward is reserved TRUE OOS**: do not inspect its strategy performance or use it for training, strategy selection, dates, thresholds or parameter decisions before Step 6 authorization. In Step 1 determine the actual earlier shared history and freeze development/WF windows *without* reading protected performance. Never shorten periods ad hoc to improve metrics.

## Evaluation and decision logic

- Report **net** expectancy, PF, trade count, win rate, median holding time, spread/fee/slippage impact, drawdown, return and recovery for each instrument, architecture, year, and month. Include equity marked to market at calendar month end (with open-position P&L and costs); zero-return months are **not** positive.
- Report positive-month fraction, worst month, count of zero/negative months, longest losing-month streak, rolling 3/6/12-month returns, consistency of opportunities per week/month, and co-loss/correlation of standalone strategies. Compare risk-adjusted results at equal exposure and costs, not on trading frequency alone.
- MTF must add reliable net benefit versus M5 standalone; never assume a slower context always helps. After independent validation, consider an integrated portfolio only if it genuinely improves after-cost monthly stability and drawdowns.
- Intraday positions: specify a causal max holding time, planned flat/session-boundary policy and overnight-risk treatment *before* performance selection. Avoid silently changing holding rules to rescue monthly results.
- Moderate-aggressive study bounds, **not approved LIVE settings**: test 0.25–0.5% of the new account equity risk/trade, a 1–1.5% daily loss guard and 3% weekly guard; include one-contract floor, margin and correlations. No martingale/averaging down. Unaffordable integer positions are skipped.
- Separately stress-test net distributable profit, taxes, external transfers to TradingSystemLab, future living-expense withdrawals and reserves. Do not present this as guaranteed income.

## Isolation / approval rules

- Code, configs, documentation, generated results and logs for this research belong only under IntradayLab/ on research/intraday-lab; market-pattern-data/forever is read-only.
- **NEVER change TradingSystemLab/, its active robot/configuration/data authorities, BBW/, other project trees, or repository-root files.** Research ideas may borrow generic engineering discipline only; no imports of TradingSystemLab strategy parameters/results/credentials.
- Do not merge the research branch into production main without separate explicit authorization and protected-tree review.
- After each task independently inspect the actual GitHub main and research branch, changed files and diff, repeatable results, and exact completion status. No advancement to the next stage without audit and approval.
