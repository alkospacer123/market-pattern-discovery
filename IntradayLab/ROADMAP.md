# IntradayLab — research roadmap

Decision: **2026-10-08**. Independent intraday research on MOEX perpetual futures. **Only IntradayLab/ may be changed.** This roadmap does not authorize real orders or affect the production TradingSystemLab robot.

**Current audit gate (2026-10-09):** Independent settings re-audit [STAGE2_M5_STRATEGY_SETTINGS_REAUDIT_20261009](reports/STAGE2_M5_STRATEGY_SETTINGS_REAUDIT_20261009.md) found a failed annual research acceptance despite deterministic code/artifact checks. 93.2% signals blocked after 8 missing-target unknown orders; CNY early-2023 ATR/tick economics and VWAP reward-vs-C1 are poor. Original baseline manifest and result artifacts remain frozen for provenance. Stage 2 needs a bounded 2023-only input/execution audit and separate predeclared candidate variants; **NO PR #443 MERGE, NO Stage 3, NO MTF/WF/OOS/LIVE**. Only IntradayLab may change.

## Research target

Build a moderately aggressive, after-cost intraday system with a high fraction of **positive net calendar months** (12/12 is an aspiration, never a guarantee). Negative days/weeks and some negative months are possible. Evaluate profitability, worst month, consecutive losing months, total and monthly drawdown, time to recovery, sufficient independent opportunities, trading costs, and capacity to fund future withdrawals. Never increase risk or manipulate month-end exits to force a positive month.

**Trading cadence is an observed outcome, not a trading quota.** The original provisional aggregate planning range across all four instruments is roughly 5–15 trades/week (20–60/month). On 2026-10-09 the user additionally requested investigating a higher target of 1–3 trades/day **per instrument**; it is a new research objective pending explicit baseline specification, NOT an execution quota. Neither target justifies negative after-C1 expectancy or overtrading; no requirement to trade every day. Reject overtrading that erases net expectancy.

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

**Current evidence:** the pre-2025 data-content audit has now been performed; see [Stage 1 Data Audit](reports/STAGE1_DATA_AUDIT_20261008.md). M5 data begin 2023-01-03 (USDRUBF/CNYRUBF), 2023-07-11 (GLDRUBF), 2023-11-14 (IMOEXF). Basic OHLC/timestamps/tick tests pass, but the 2024-08-16 IMOEXF M15 evening interval has 20 M15 bars without M5 counterparts. The exporter has now attested FINAM / MSK UTC+3 / start-label; delivery/finalization, bounded historical sessions, funding/margin and intrabar execution remain application-specific gates; **Stage 1 is not complete**.

**Historical status before Stage 2 authorization, 2026-10-09:** Stage 1.2 Historical Sessions & MTF Integrity is **COMPLETE**, [PR #439](https://github.com/alkospacer123/market-pattern-discovery/pull/439) **MERGED**, independent audit PASS. Its historical [report](reports/STAGE1_2_SESSION_MTF_AUDIT.md) and JSON retain their original pending-audit status for reproducibility. Real M15/M30/H1 contexts remain blocked: the new exporter attestation of clock/start-label does not establish delivery/finalization, full session evidence or composition integrity. The [Execution, Costs & Funding Specification](reports/STAGE1_EXECUTION_COSTS_SPEC.md), [PR #440](https://github.com/alkospacer123/market-pattern-discovery/pull/440), is **MERGED**, independent re-audit PASS at `79f974b570e7b8037ef426eba41d4e48793375ee`. Its historical report is retained unchanged. The user approved independent IntradayLab **C1** for the initial Baseline: one instrument-specific tick per executed entry and exit, **2 ticks per closed round trip per contract** at an unchanged tick size. No exchange/broker fees, spread or slippage are charged on top; funding, failed close, gaps and margin remain separate. Higher-cost scenarios are separate sensitivity checks replacing C1, never combined with actual-tariff scenarios. It documents the CNY tick change from 19:00 MSK 2023-09-27: each fill uses its dated tick value, not the modern grid for all history. Current-tick checks alone do not validate the older CNY grid. The actual FINAM tariff will be selected after trade-count/frequency/turnover statistics; its unknown status alone does not block research with C1. Historical margin/funding, delivery/finalization, Volume and execution evidence remain unresolved; CSV source/clock/start-label now have direct user-exporter attestation, not automatically verified FINAM metadata. Historical funding clearing around 18:50 must not be replaced by the 23:50 boundary introduced in 2026. Preserve the existing IMOEXF quarantine; **Stage 1 OPEN**, Stage 2 NOT STARTED. No TradingSystemLab model or code is imported.

**Historical M5 clock confirmation before Stage 2 authorization, 2026-10-09:** [STAGE1_M5_CONDITIONAL_FOR_BASELINE](reports/STAGE1_M5_CLOCK_CONFIRMATION.md), pending independent audit and explicit approval of bounded assumptions. The user personally exported all 16 CSVs through FINAM with identical settings: MSK UTC+3, start-label. Limited M5 controls agree with known MOEX exceptions; independent FINAM re-export unavailable (proxy 403), so no automatic metadata certification. All four instruments are **CONDITIONAL**; currently zero Baseline bars authorized. Preserve the daytime-only scope, USD/CNY 31.08.2023 gap and IMO quarantine. Before Stage 2, confirm/approve finalization at t+10m, selected continuous daytime windows, modelled fills/nonfills and residual risk, and Volume weights/liquidity; margin/limits gate capital and quantity claims, never default q=1. A normalized/conditional-contract study is only a proposal needing separate approval. After independent audit and authorization, propose VWAP Mean Reversion M5-only and Session Momentum M5-only first; all MTF hypotheses remain in this roadmap without automatic authorization. The historical [PR #441 report](reports/STAGE1_M5_READINESS.md) is unchanged; PR #441 MERGED. Stage 1 OPEN, Stage 2 NOT STARTED.

**Current Stage 2 authorization/result, 2026-10-09:** the user explicitly approved the bounded M5-only research model: FINAM / MSK UTC+3 / start-label, availability no earlier than t+10m, the existing daytime windows, PR #440 conditional fills/residuals, C1, relative Volume weights and normalized price analysis without actual GO/equity sizing. **STAGE2_M5_BASELINE_NEEDS_FIX_RESEARCH_AND_SETTINGS**: [report](reports/STAGE2_M5_BASELINE_REPORT.md), immutable [manifest](config/stage2_m5_baseline_v1.json), exactly **2 strategies × 4 instruments = 8 runs**, M5 **2023 only**, using each instrument's entire available 2023 history. 147 conditional model entries; 135 fully accounted trades; 12 trades with unresolved consequences plus 8 unknown-entry orders (20 unresolved cases). 7,279 later signals blocked, including 6,032 otherwise eligible entry attempts; 8 of the original 61 cases remain unknown and 53 are not submitted. Known terminal model units are zero, possible unknown residual units are null and full FLAT is unconfirmed. Full annual Net/PF remain unavailable. 12 known-position plus 8 unknown-order B−10 breaches; 85 synthetic tests PASS and deterministic replay. PR #443 corrected after independent NEEDS_FIX: absent target OHLCV preserves an unknown possible entry and blocks new entries through 2023 end; previous evidence retained in correction_history.json/Git e38e018. Fixed manifest and parameters unchanged; pending independent re-audit. **Stage 1 remains OPEN outside the approved M5 subset; no full 16-file/MTF or real execution readiness.** 2024 reserved WF and 2025+ TRUE OOS physically unread. No optimizer, extra strategies, capital returns, LIVE or next-stage authorization.

**Timeframes:** M5 for signals and price-based execution simulation. M15 / M30 / H1 are candidate *context* timeframes; **M30 -> M5 is the lead hypothesis**, not a preselected winner. Research is strictly intraday. No M1 or M3/M10 data or M1 execution assumptions. No order-book strategy: **Order Flow Imbalance excluded** because historical order-book data is unavailable.

**Initial strategies, in sequence:**
1. **VWAP Mean Reversion** — M5 standalone; M30 -> M5 principal MTF comparison; M15 -> M5 secondary comparison. VWAP is session-anchored. If only OHLCV bars are available, label volume-weighted typical-price VWAP as an approximation, not an observed transaction VWAP. Assess the risk of countertrend entries.
2. **Intraday / Session Momentum** — M5 standalone; M30 -> M5 principal MTF comparison; H1 -> M5 secondary comparison. Measure session- and instrument-dependent continuation without forcing an H1 holding period.
3. **Volatility Squeeze Breakout** — **after** the first two strategies are assessed: M5 standalone versus M30 -> M5. Test whether it adds independent portfolio value beyond Momentum.
4. **Liquidity Sweep / False Breakout** — reserve hypothesis only, not part of initial implementation, subject to a later explicit scope decision.

Roadmap comparison envelope: **6 strategy/architecture variants x 4 instruments = up to 24 runs**, conditional on their Step 1 quality gates. The current explicitly approved Stage 2 subset is exactly **two M5-only strategies x four instruments = 8 runs**; the four context architectures remain blocked and unstarted. These are predeclared comparisons, not optimizer output. The later Squeeze pair would add up to 8 runs only if explicitly started. Do not multiply variants or optimize timeframe choices using TRUE OOS.

**MTF causality:** use only the last fully closed higher-timeframe bar available at each completed M5 signal. Check time-zone, session anchoring, resampling agreement, trading halts/gaps, and boundary resets. Source M5 is the finest available bar: same-bar stop/target ordering is ambiguous; model conservatively, stress alternatives or flag unresolved cases. Do not invent M1-level precision. Validate any backtest fills against the actual execution mechanism and available bid/ask information.

## Stages and exit evidence

| Step | Stage | Required deliverable / exit gate | Status |
| --- | --- | --- | --- |
| 0 | Separate project boundary | Research branch + IntradayLab folder, written constraints; protected trees unchanged | **COMPLETE** |
| 1 | Dataset and execution specification | Audited 16 CSVs: date coverage, timezone/bar timestamp meaning, schemas, duplicates, OHLC consistency, missing bars/sessions, volume, cross-TF agreement; venue calendar, actual instrument specs, tick/lot/margin, FINAM + exchange fees, spread/slippage/nonfill model; frozen pre-2025 development scope and TRUE OOS boundary | **OPEN outside approved M5 subset. Stage 1.2 and PR #440 complete/merged; FINAM/MSK/start-label attested by exporter. Limited Stage 2 model explicitly approved; full historical sessions/GO/funding/real fills and MTF remain unresolved** |
| 2 | Baseline | Causal fixed-rule VWAP and Momentum implementations; predeclared six architectures; per-run trade ledgers, after-cost metrics, direction/instrument/monthly reports, no parameters fitted to TRUE OOS | **M5-only NEEDS FIX (research coverage and settings audit) — 8 runs, 7,279 blocked signals (93.2%), 12 unresolved trade consequences + 8 unknown entry orders, full annual Net/PF unavailable. Not an accepted annual Baseline; MTF NOT STARTED** |
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
- Do not merge task PRs without separate explicit authorization, independent audit and protected-tree review. Creating a PR does not authorize merge or automatic research-stage advancement.
- After each task independently inspect the actual GitHub main and research branch, changed files and diff, repeatable results, and exact completion status. No advancement to the next stage without audit and approval.
