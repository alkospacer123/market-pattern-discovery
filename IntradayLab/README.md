# IntradayLab — independent MOEX intraday strategy research

Status: **RESEARCH SETUP ONLY**. No strategy has been validated, and no LIVE trading is authorized.

## Mission

Develop and independently validate one or more **moderately aggressive** systematic intraday strategies on MOEX futures, using M5 as the execution/signal timeframe and M15/M30/H1 as possible completed-bar context. A prospective second FINAM brokerage account will isolate capital, order authority, runtime, reconciliation, risk, and evidence from the existing TradingSystemLab production robot.

Two long-term uses of *realized net* profit:
1. Reinvest part into the separate TradingSystemLab account.
2. Eventually support irregular-but-planned living withdrawals, **only after** a sufficiently long record of net profitability, operating reserves, and withdrawal-safe capitalization.

There is **no guarantee of positive returns in every calendar month**, stable salary-like income, or fast deposit growth. The project must measure time-to-recovery, drawdown, losing months, and the effect of withdrawals.

## Hard isolation boundary

- **NEVER MODIFY any files under `TradingSystemLab/`**, or its Stage 7 / Stage 8 production identity, research results, robot, data authorities, configuration, or operational state.
- New research files and reports belong only to `IntradayLab/` on `research/intraday-lab` until an explicit future decision about repository arrangement. Do not merge this branch into the production `main` without separate user approval and a protected-tree diff audit.
- Do not modify other domains (`BBW/`, `results/`, root project documentation) for this study.
- No imports of TradingSystemLab strategies, their parameter sets, candidate decisions, results, or execution authority. General research methods and engineering practices may be learned from read-only examination, but **all new hypotheses and evidence must be independent**.
- No market data or credentials committed to Git. Historical source data is external and read-only.
- A future independent FINAM account is **not currently connected or authorized**. No order-capable integration is part of research setup.
- Changes restricted to this folder; independently inspect actual GitHub `main`, branch and changed-file diff after any research task.

## Agreed strategy scope (not proven profitable)

**Markets:** four MOEX perpetuals: USDRUBF, CNYRUBF, GLDRUBF, IMOEXF. New read-only OHLCV datasets live in alkospacer123/market-pattern-data/forever: M5, M15, M30, H1 for each instrument (16 files confirmed by path inventory). Data integrity, spans, fees and execution have not yet been audited.

**Trading timeframe:** M5. **MTF contexts:** M30 -> M5 is primary, with M15 -> M5 for VWAP and H1 -> M5 for Momentum as restricted comparisons. No M1, M3 or M10 research in this agreed scope; M5 is the finest available bar and cannot prove tick-level fill ordering.

**Initial strategy hypotheses:**
1. **VWAP mean reversion** — compare standalone M5, M30 -> M5 and M15 -> M5. Use a documented session anchor and appropriate trend-regime discipline.
2. **Intraday / session momentum** — compare standalone M5, M30 -> M5 and H1 -> M5.
3. **Volatility squeeze breakout** — evaluate subsequently, standalone M5 versus M30 -> M5, after the first two are assessed.
4. **Liquidity sweep / false breakout** — reserve only, not approved for initial implementation.

**Order Flow Imbalance is excluded** because no historical order-book data is available. Do not add it or invent order-book signals.

These are bounded research priorities, **not** performance claims or a mandate to trade daily. No guaranteed positive month. See ROADMAP.md for gates and 2025+ TRUE OOS restrictions.

## Non-negotiable research rules

- ZERO LOOK-AHEAD. Completed bars only, timestamps causal, trading-day/session boundaries explicit, deterministic handling of simultaneous events.
- Intraday friction must include commissions, bid/ask effects, slippage, nonfill risk, funding/margin constraints and lot size where applicable. Report assumptions and stress tests. Do **not** carry over TradingSystemLab's C1 model as if it were validated for intraday M5 execution.
- Repository-wide 2025 TRUE OOS lock applies: **do not read, tune on, rank using, or inspect 2025 data during development**. Define development/validation/untouched holdout dates before research; treat all post-development data as protected until an explicit OOS release.
- Development stages: Baseline -> bounded Optimization -> Robustness -> Walk Forward -> TRUE OOS -> operational forward observation. Do not introduce ML or large-scale parameter mining by default.
- Record profit and loss after costs, drawdown, losing months, stability, sample size, execution sensitivity, and joint portfolio exposure before any LIVE recommendation.
- Never average down or use martingale. If one-contract minimum risk breaches limits, **skip** the trade.

See [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md) and [ROADMAP.md](ROADMAP.md).
