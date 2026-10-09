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

**Current evidence:** the pre-2025 data-content audit has now been performed; see [Stage 1 Data Audit](reports/STAGE1_DATA_AUDIT_20261008.md). M5 data begin 2023-01-03 (USDRUBF/CNYRUBF), 2023-07-11 (GLDRUBF), 2023-11-14 (IMOEXF). Basic OHLC/timestamps/tick tests pass, but the 2024-08-16 IMOEXF M15 evening interval has 20 M15 bars without M5 counterparts. Timezone, actual historical sessions, funding/margin and intrabar execution remain validation gates; **Stage 1 is not complete**.

**Status update, 2026-10-09:** Stage 1.2 Historical Sessions & MTF Integrity is **COMPLETE**, [PR #439](https://github.com/alkospacer123/market-pattern-discovery/pull/439) **MERGED**, independent audit PASS. Its historical [report](reports/STAGE1_2_SESSION_MTF_AUDIT.md) and JSON retain their original pending-audit status for reproducibility. Real M15/M30/H1 contexts remain blocked: timezone, timestamp meaning and full session evidence are unresolved. The [Execution, Costs & Funding Specification](reports/STAGE1_EXECUTION_COSTS_SPEC.md), [PR #440](https://github.com/alkospacer123/market-pattern-discovery/pull/440), is **STAGE1_EXECUTION_SPEC_PENDING_AUDIT**. The user approved independent IntradayLab **C1** for the initial Baseline: one instrument-specific tick per executed entry and exit, **2 ticks per closed round trip per contract** at an unchanged tick size. No exchange/broker fees, spread or slippage are charged on top; funding, failed close, gaps and margin remain separate. Higher-cost scenarios are separate sensitivity checks replacing C1, never combined with actual-tariff scenarios. It documents the CNY tick change from 19:00 MSK 2023-09-27: each fill uses its dated tick value, not the modern grid for all history. Current-tick checks alone do not validate the older CNY grid. The actual FINAM tariff will be selected after trade-count/frequency/turnover statistics; its unknown status alone does not block research with C1. Historical margin/funding, CSV provenance and execution evidence remain unresolved. Historical funding clearing around 18:50 must not be replaced by the 23:50 boundary introduced in 2026. Preserve the existing IMOEXF quarantine; **Stage 1 OPEN**, Stage 2 NOT STARTED. No TradingSystemLab model or code is imported.

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
| 1 | Dataset and execution specification | Audited 16 CSVs: date coverage, timezone/bar timestamp meaning, schemas, duplicates, OHLC consistency, missing bars/sessions, volume, cross-TF agreement; venue calendar, actual instrument specs, tick/lot/margin, FINAM + exchange fees, spread/slippage/nonfill model; frozen pre-2025 development scope and TRUE OOS boundary | **OPEN — 16/16 base audit performed; Stage 1.2 COMPLETE, PR #439 MERGED, independent audit PASS; execution specification PENDING AUDIT. Initial C1 aggregate costs approved; actual FINAM tariff deferred until trading statistics, not an independent research blocker. Provenance/timezone, full historical sessions/specs/margin/funding and real fill evidence unresolved; quarantine retained; no real MTF or Baseline readiness** |
| 2 | Baseline | Causal fixed-rule VWAP and Momentum implementations; predeclared six architectures; per-run trade ledgers, after-cost metrics, direction/instrument/monthly reports, no parameters fitted to TRUE OOS | **NOT STARTED** |
| 3 | Bounded Optimization | Only a small prejustified parameter set where Baseline supports it; immutable run manifests, no mass search, no PF-only ranking | **NOT STARTED** |
| 4 | Robustness | Parameter-neighborhood, instruments, session regimes, trading costs, widened slippage, ambiguous fills, adverse months, concentration and drawdown | **NOT STARTED** |
| 5 | Walk Forward | Chronological rolling tests with no future-informed decisions; frozen rules; monthly and portfolio comparisons | **NOT STARTED** |
| 6 | TRUE OOS | Single separately authorized final assessment on **untouched 2025+ data**, frozen finalists and costs, full calendar-month + instrument/portfolio reports | **NOT STARTED / LOCKED** |
| 7 | Forward observation and separate FINAM-account readiness | Read-only/paper monitoring; fully independent credentials, account bindings, sizing, order ledger, reconciliation, kill switch; explicit approval required for real orders | **NOT STARTED / NO LIVE AUTHORIZATION** |

**2025 onward is reserved TRUE OOS**: do not inspect its strategy performance or use it for training, strategy selection, dates, thresholds or parameter decisions before Step 6 authorization. In Step 1 determine the actual earlier shared history and freeze development/WF windows *without* reading protected performance. Never shorten periods ad hoc to improve metrics.

## Evaluation and decision logic

- Report **net** expectancy, PF, trade count, win rate, median holding time, spread/fee/slippage impact, drawdown, return and recovery for each instrument, architecture, year, and month. Initial Baseline results must be labelled **«прибыль после модельных издержек C1»**, not confirmed profit after actual commissions; report C1 as one aggregate cost without inventing its fee/spread/slippage breakdown. Include equity marked to market at calendar month end (with open-position P&L and costs); zero-return months are **not** positive.
- Report positive-month fraction, worst month, count of zero/negative months, longest losing-month streak, rolling 3/6/12-month returns, consistency of opportunities per week/month, and co-loss/correlation of standalone strategies. Compare risk-adjusted results at equal exposure and costs, not on trading frequency alone.
- MTF must add reliable net benefit versus M5 standalone; never assume a slower context always helps. After independent validation, consider an integrated portfolio only if it genuinely improves after-cost monthly stability and drawdowns.
- Intraday positions: specify a causal max holding time, planned flat/session-boundary policy and overnight-risk treatment *before* performance selection. Avoid silently changing holding rules to rescue monthly results.
- Moderate-aggressive study bounds, **not approved LIVE settings**: test 0.25–0.5% of the new account equity risk/trade, a 1–1.5% daily loss guard and 3% weekly guard; include one-contract floor, margin and correlations. No martingale/averaging down. Unaffordable integer positions are skipped.
- Separately stress-test net distributable profit, taxes, external transfers to TradingSystemLab, future living-expense withdrawals and reserves. Do not present this as guaranteed income.

## Isolation / approval rules

- Code, configs, documentation, generated results and logs for this research belong only under IntradayLab/; market-pattern-data/forever is read-only. The primary branch is **main**. IntradayLab changes are submitted through separate task branches and PRs into main with independent audit; research/intraday-lab is the historical setup branch, not the exclusive project location.
- **NEVER change TradingSystemLab/, its active robot/configuration/data authorities, BBW/, other project trees, or repository-root files.** Research ideas may borrow generic engineering discipline only; no imports of TradingSystemLab strategy parameters/results/credentials.
- Do not merge task PRs without separate explicit authorization, independent audit and protected-tree review. Creating a PR does not authorize merge or advancement to Stage 2.
- After each task independently inspect the actual GitHub main and research branch, changed files and diff, repeatable results, and exact completion status. No advancement to the next stage without audit and approval.
