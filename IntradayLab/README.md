# IntradayLab — independent MOEX intraday strategy research

Status: **STAGE2_M5_BASELINE_NEEDS_FIX_RESEARCH_AND_SETTINGS**. Exactly 8 fixed M5-only 2023 conditional runs implemented: VWAP and Momentum × four instruments. 147 conditional model entries; 135 fully accounted trades; 12 trades with unresolved consequences plus 8 unknown-entry orders (20 unresolved cases). 7,279 later signals blocked, including 6,032 otherwise eligible entry attempts; 8 of the original 61 cases remain unknown and 53 are not submitted. Known terminal model units are zero, possible unknown residual units are null and full FLAT is unconfirmed. Full annual Net/PF remain unavailable. 12 known-position plus 8 unknown-order B−10 breaches; 85 synthetic tests PASS and deterministic replay. [Report](reports/STAGE2_M5_BASELINE_REPORT.md), [immutable manifest](config/stage2_m5_baseline_v1.json), [structured results](results/stage2_m5/results.json). Stage 1 stays OPEN outside the user-approved limited M5 model. 2024 WF reserved and physically unread; 2025+ TRUE OOS locked/unread. No LIVE authorization.

**Current audit gate (2026-10-09):** Independent settings re-audit [STAGE2_M5_STRATEGY_SETTINGS_REAUDIT_20261009](reports/STAGE2_M5_STRATEGY_SETTINGS_REAUDIT_20261009.md) found a failed annual research acceptance despite deterministic code/artifact checks. 93.2% signals blocked after 8 missing-target unknown orders; CNY early-2023 ATR/tick economics and VWAP reward-vs-C1 are poor. Original baseline manifest and result artifacts remain frozen for provenance. Stage 2 needs a bounded 2023-only input/execution audit and separate predeclared candidate variants; **NO PR #443 MERGE, NO Stage 3, NO MTF/WF/OOS/LIVE**. Only IntradayLab may change.

## Current bounded Baseline

The user explicitly approved FINAM/MSK/start-label, t+10m availability, the existing daytime windows, conditional PR #440 execution, C1 and relative Volume weights for normalized price analysis. The report contains all eight run statuses, entry attempts/conditional trade ledger, direction/month/year diagnostics, gaps, 12 unresolved trade consequences, 8 unknown-entry orders and 20 recorded missed flat targets. Missing target OHLCV keeps the run fail-closed through 2023 end without invented fill/quantity/P&L. Original results and the 61-case disposition are retained in correction_history.json; existing PR #443 failed independent research-completeness re-audit; technical corrections are insufficient for annual strategy acceptance. Model units do not set real q=1 or replace unknown GO; capital sizing, equity returns and roadmap daily/weekly risk limits are not implemented. Volume does not establish contract capacity. The locked manifest never changes by instrument PF; no optimizer or parameter grid. Real MTF and later stages are not started.

Reproduce using the commands in the report: 85 synthetic tests, exact frozen 2023 prefixes, deterministic replay, artifact SHA and protected-tree audit. All changes are under IntradayLab; the source and TradingSystemLab/BBW are unchanged. No merge is authorized in this task.

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

**Markets:** four MOEX perpetuals: USDRUBF, CNYRUBF, GLDRUBF, IMOEXF. New read-only OHLCV datasets live in alkospacer123/market-pattern-data/forever: M5, M15, M30, H1 for each instrument (16 files confirmed by path inventory). The base audit of these 16 CSV files for the period before 2025 is complete: **DATA QA PARTIAL PASS**. Full Stage 1 remains open: the IMOEXF M15 anomaly, bounded historical sessions, delivery/finalization, Volume, funding/margin and the execution model still require the applicable confirmations or explicit limited assumptions. The limited M5-only 2023 Baseline is explicitly authorized and implemented; MTF, TRUE OOS and LIVE remain unauthorized.

**Stage 1.2 COMPLETE:** [PR #439](https://github.com/alkospacer123/market-pattern-discovery/pull/439) merged into main, independent audit PASS. Real M15/M30/H1 contexts remain blocked; the newly attested source clock/start-label does not automatically confirm higher-TF availability, session anchors or full composition integrity. The original [Stage 1.2 report](reports/STAGE1_2_SESSION_MTF_AUDIT.md), JSON, code and tests retain their reproducible historical state. The IMOEXF 16.08.2024 quarantine and known coverage gaps remain in force.

The [Execution, Costs & Funding Specification](reports/STAGE1_EXECUTION_COSTS_SPEC.md), [PR #440](https://github.com/alkospacer123/market-pattern-discovery/pull/440), documents contract units and historical changes, official fees with applicability limits, causal M5 execution, nonfill/partial fills, size constraints and planned flat before the relevant clearing boundary. **PR #440 MERGED, independent re-audit PASS** at `79f974b570e7b8037ef426eba41d4e48793375ee`; its historical report remains unchanged. This does not close Stage 1: historical funding/margin, finalization/delivery, Volume and execution evidence remain UNRESOLVED. CSV source/clock/start-label now have direct user-exporter attestation, not automatically verified FINAM metadata. The user approved **C1** for initial Baseline transaction costs: one instrument-specific tick on each executed entry and exit, **2 ticks per closed round trip per contract** at an unchanged tick size. CNY fills must use the historical tick value applicable before/after 27.09.2023 19:00 MSK. Actual MOEX/FINAM tariffs remain unconfirmed for actual-cost claims; select the FINAM tariff later after trade-count, frequency and turnover statistics. Its unknown status alone does not postpone research with C1. Current 23:50 funding rules must not replace the historical clearing around 18:50. No strategies were run in PR #440; the current limited Stage 2 result is above.

**Historical M5 clock confirmation before Stage 2 approval:** [STAGE1_M5_CONDITIONAL_FOR_BASELINE](reports/STAGE1_M5_CLOCK_CONFIRMATION.md), all four instruments **CONDITIONAL**, pending independent audit and explicit approval of limited assumptions. The user personally exported all 16 FINAM CSVs with identical MSK UTC+3 / start-label settings. M5 controls agree with known MOEX exceptions; independent re-export is unavailable (proxy 403). This removes the previous clock blocker without authorizing Baseline. Remaining gates: bounded finalization t+10m, daytime continuity, modelled fills/nonfills/residual risk and Volume weights/liquidity. Historical margin/limits restrict capital/quantity modelling; no default one-contract size. Normalized/conditional-contract results are only a proposal for separate approval. Preserve gaps/quarantine; Stage 2 NOT STARTED. After audit and authorization, start with VWAP Mean Reversion M5-only and Session Momentum M5-only; MTF stays in the roadmap without automatic permission. The [PR #441 historical report](reports/STAGE1_M5_READINESS.md) remains unchanged; PR #439–441 are MERGED.

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
