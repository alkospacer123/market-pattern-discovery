# IntradayLab — independent MOEX intraday strategy research

Status: **STAGE 1 OPEN — STAGE1_M5_CONDITIONAL_FOR_BASELINE, PENDING INDEPENDENT AUDIT AND EXPLICIT ASSUMPTION APPROVAL**. Stage 0 and Stage 1.2 are complete; Stage 2 Baseline has not started. No strategy has been validated, and no LIVE trading is authorized.

## Mission

Develop and independently validate one or more **moderately aggressive** systematic intraday strategies on MOEX futures, using M5 as the execution/signal timeframe and M15/M30/H1 as possible completed-bar context. A prospective second FINAM brokerage account will isolate capital, order authority, runtime, reconciliation, risk, and evidence from the existing TradingSystemLab production robot.

Two long-term uses of *realized net* profit:
1. Reinvest part into the separate TradingSystemLab account.
2. Eventually support irregular-but-planned living withdrawals, **only after** a sufficiently long record of net profitability, operating reserves, and withdrawal-safe capitalization.

There is **no guarantee of positive returns in every calendar month**, stable salary-like income, or fast deposit growth. The project must measure time-to-recovery, drawdown, losing months, and the effect of withdrawals.

## Hard isolation boundary

- **NEVER MODIFY any files under `TradingSystemLab/`**, or its Stage 7 / Stage 8 production identity, research results, robot, data authorities, configuration, or operational state.
- New research files and reports belong only to `IntradayLab/`. The primary branch is **main**, with separate task branches and PRs subject to independent audit. `research/intraday-lab` was the historical setup branch. Do not merge task PRs without separate authorization and a protected-tree diff audit.
- Do not modify other domains (`BBW/`, `results/`, root project documentation) for this study.
- No imports of TradingSystemLab strategies, their parameter sets, candidate decisions, results, or execution authority. General research methods and engineering practices may be learned from read-only examination, but **all new hypotheses and evidence must be independent**.
- No market data or credentials committed to Git. Historical source data is external and read-only.
- A future independent FINAM account is **not currently connected or authorized**. No order-capable integration is part of research setup.
- Changes restricted to this folder; independently inspect actual GitHub `main`, branch and changed-file diff after any research task.

## Agreed strategy scope (not proven profitable)

**Markets:** four MOEX perpetuals: USDRUBF, CNYRUBF, GLDRUBF, IMOEXF. New read-only OHLCV datasets live in alkospacer123/market-pattern-data/forever: M5, M15, M30, H1 for each instrument (16 files confirmed by path inventory). The base audit of these 16 CSV files for the period before 2025 is complete: **DATA QA PARTIAL PASS**. Full Stage 1 remains open: the IMOEXF M15 anomaly, bounded historical sessions, delivery/finalization, Volume, funding/margin and the execution model still require the applicable confirmations or explicit limited assumptions. Baseline, TRUE OOS and LIVE are not authorized.

**Stage 1.2 COMPLETE:** [PR #439](https://github.com/alkospacer123/market-pattern-discovery/pull/439) merged into main, independent audit PASS. Real M15/M30/H1 contexts remain blocked; the newly attested source clock/start-label does not automatically confirm higher-TF availability, session anchors or full composition integrity. The original [Stage 1.2 report](reports/STAGE1_2_SESSION_MTF_AUDIT.md), JSON, code and tests retain their reproducible historical state. The IMOEXF 16.08.2024 quarantine and known coverage gaps remain in force.

The [Execution, Costs & Funding Specification](reports/STAGE1_EXECUTION_COSTS_SPEC.md), [PR #440](https://github.com/alkospacer123/market-pattern-discovery/pull/440), documents contract units and historical changes, official fees with applicability limits, causal M5 execution, nonfill/partial fills, size constraints and planned flat before the relevant clearing boundary. **PR #440 MERGED, independent re-audit PASS** at `79f974b570e7b8037ef426eba41d4e48793375ee`; its historical report remains unchanged. This does not close Stage 1: historical funding/margin, finalization/delivery, Volume and execution evidence remain UNRESOLVED. CSV source/clock/start-label now have direct user-exporter attestation, not automatically verified FINAM metadata. The user approved **C1** for initial Baseline transaction costs: one instrument-specific tick on each executed entry and exit, **2 ticks per closed round trip per contract** at an unchanged tick size. CNY fills must use the historical tick value applicable before/after 27.09.2023 19:00 MSK. Actual MOEX/FINAM tariffs remain unconfirmed for actual-cost claims; select the FINAM tariff later after trade-count, frequency and turnover statistics. Its unknown status alone does not postpone research with C1. Current 23:50 funding rules must not replace the historical clearing around 18:50. No strategies or later research stages were run.

**M5 clock confirmation:** [STAGE1_M5_CONDITIONAL_FOR_BASELINE](reports/STAGE1_M5_CLOCK_CONFIRMATION.md), all four instruments **CONDITIONAL**, pending independent audit and explicit approval of limited assumptions. The user personally exported all 16 FINAM CSVs with identical MSK UTC+3 / start-label settings. M5 controls agree with known MOEX exceptions; independent re-export is unavailable (proxy 403). This removes the previous clock blocker without authorizing Baseline. Remaining gates: bounded finalization t+10m, daytime continuity, modelled fills/nonfills/residual risk and Volume weights/liquidity. Historical margin/limits restrict capital/quantity modelling; no default one-contract size. Normalized/conditional-contract results are only a proposal for separate approval. Preserve gaps/quarantine; Stage 2 NOT STARTED. After audit and authorization, start with VWAP Mean Reversion M5-only and Session Momentum M5-only; MTF stays in the roadmap without automatic permission. The [PR #441 historical report](reports/STAGE1_M5_READINESS.md) remains unchanged; PR #439–441 are MERGED.

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
- Initial Baseline uses **independent IntradayLab C1** as aggregate modelled transaction costs: no additional exchange/broker commissions, spread or slippage on top, and no double charge if C1 is embedded in cost-adjusted prices. Higher-cost scenarios are separate sensitivity checks replacing C1, not mixed with actual tariffs. Funding, failed close, gaps, margin and lot constraints remain separate. Label results **«прибыль после модельных издержек C1»**, not confirmed profit after actual commissions. No TradingSystemLab model, code or parameters are imported.
- Repository-wide 2025 TRUE OOS lock applies: **do not read, tune on, rank using, or inspect 2025 data during development**. Define development/validation/untouched holdout dates before research; treat all post-development data as protected until an explicit OOS release.
- Development stages: Baseline -> bounded Optimization -> Robustness -> Walk Forward -> TRUE OOS -> operational forward observation. Do not introduce ML or large-scale parameter mining by default.
- Record profit and loss after costs, drawdown, losing months, stability, sample size, execution sensitivity, and joint portfolio exposure before any LIVE recommendation.
- Never average down or use martingale. If one-contract minimum risk breaches limits, **skip** the trade.

See [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md) and [ROADMAP.md](ROADMAP.md).
