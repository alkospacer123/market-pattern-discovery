# IntradayLab — new Stage 2 strategy selection memo

2026-10-10. **QUEUE DOCUMENTED, NO NEW STRATEGY TESTED OR VALIDATED.**
GitHub main before this documentation PR: 36316e8dc07c49becaca7be0c3787da65f583245. PR #456 and #457 are MERGED. Project changes remain exclusively inside IntradayLab.

## Why replace the previous set

VWAP Mean Reversion generated many opportunities but its tested architectures failed C1 net expectancy and monthly stability. Session Momentum's completed-bar breakout chasing also failed after delayed Open and minimal C1. Volatility Squeeze Breakout M5/M30 produced only **7** unique 2023 T10 executions with negative USD/CNY closed-subset economics; standalone M15 produced **11** unique conditional trades and H1→M15 retained **8**. USD C1 standalone PF2.333 on just 8 trades and H1 PF5.167 on 5 trades is NOT a reliable monthly or full-year Baseline; C2 standalone USD PF1.414. See [M5 final](STAGE2_SQUEEZE_FINAL_REPORT.md), [M15 final](STAGE2_SQUEEZE_M15_FINAL_REPORT.md).

Two separate failures: many signals with no C1 edge (VWAP/Momentum), and too few executable entries despite attractive micro-sample PF (Squeeze). We must check *completed-bar opportunity*, *actual delayed executable Open*, *risk-adjusted room to planned net 3R*, and *frequency across calendar months* before full economic replay. This isn't a promise of eventual profitability.

## Primary literature (other instruments, NOT verified MOEX trading edges)

- Carol L. Osler, currency stop-loss/take-profit clustering near price levels, Journal of Finance 2003: [DOI](https://doi.org/10.1111/1540-6261.00588), [NY Fed](https://www.newyorkfed.org/research/staff_reports/sr125.html). Justifies studying a *price rejection*, not claiming observed stops or actual liquidity sweeps from OHLCV.
- Fung, Mok & Lam, index futures intraday reversals, 2000: [paper](https://doi.org/10.1016/S0378-4266(99)00072-2). Longer 15-year study cautions reversing effects decline after bid/ask proxy costs: [paper](https://www.sciencedirect.com/science/article/pii/S0378426604000949). No transferability claim to MOEX.
- Gao, Han, Li & Zhou, *Market intraday momentum*, JFE 2018: [study](https://ideas.repec.org/a/eee/jfinec/v129y2018i2p394-414.html); Chinese commodity-futures session momentum: [study](https://www.sciencedirect.com/science/article/pii/S0275531919311328). Motivation to test completed impulse/pullback, not evidence of an after-T10 executable edge.
- Holmberg et al., opening-range breakout, 2013: [study](https://www.sciencedirect.com/science/article/pii/S1544612312000438) notes period sensitivity; an **unreviewed 2026 preprint** finds many pure ORB futures settings unprofitable after costs: [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7428398). Reserve is explicitly drive-pullback-confirmation, NOT naked ORB.
- Another **unreviewed preprint** documents many OHLCV intraday futures families failing friction and stability gates: [arXiv](https://arxiv.org/abs/2605.04004). An external research warning, not evidence for or against MOEX strategies.

No cited paper proves positive 2023 Net PF >=1.6, reliable monthly gains, 3R or 2–3 trades/day on the specified contracts.

## Fixed candidate architecture ideas and how to falsify

**1 — LEVEL_REJECTION_M5 / False Breakout & Level Rejection.** A high/low local boundary is known before the next candle. Later a completed M5 exceeds the known boundary then closes back inside. Trade opposing the failed extension after T10/T15, only at strictly future eligible M5 Open. Stop structurally outside the actually observed rejection extreme; planned <=session time and >=3R NET after C1. Distinct from VWAP mean reversion and chasing Momentum. Failure: too few reclaims, gap/late Open consumes reward, no net-3R space. Must **not** describe OHLCV as observed stop hunt/order-flow.

**2 — IMPULSE_PULLBACK_M5 / Impulse–Pullback Continuation.** A completed directional impulse, separate later completed corrective retrace without destroying structure, then another completed price resumption confirmation; delayed M5 Open with structural pullback Stop. Opposite SHORT mirrored. Distinct from rejected initial breakout Momentum; failure: by third confirmation too little trend or time remains, Stop too broad.

**3 — RANGE_ROTATION_M5 / Range Boundary Rotation.** A completed bounded balanced same-window price range; later completed **non-breaching edge rejection** toward a prior-known interior/opposite bound; structural outside Stop and a target within that range sufficient for >=3R NET after C1. Unlike LEVEL_REJECTION_M5, the known edge is *not* breached; unlike VWAP, no volume-weighted anchor. Failure: range too narrow to pay costs, or range no longer balanced.

**RESERVE — OPENING_DRIVE_PULLBACK_M5.** Fully completed directional drive after an approved session start, followed by separately later pullback and completed resumption signal. Not an immediate opening-range breakout; session anchoring distinguishes from generic impulse. Risk: very few starting drives and little room until flat.

The specific event grammar (range lookback, age, impulse size, pullback depth, rejection, expiry, deduplication, Stop/target and exits) needs **one frozen preregistration before ANY event-count or P&L inspection**, not an optimized grid or hand-picked threshold. These four names do NOT denote proven profitable configurations.

## Existing Stage 2 gate: no-P&L opportunity/geometry check first

A **separate explicit user authorization** is needed for just candidate 1. Scan read-only full accessible 2023 original M5 OHLCV of USDRUBF/CNYRUBF/GLDRUBF/IMOEXF; keep missing slots, later GD/IMOEX history inception, MSK clocks and dated tick. Report raw setups, completed confirmation, T10/T15 readiness, distinct exact next permissible M5 Open, conditional fills vs NONFILL/UNKNOWN, structural initial risk and planned >=3R NET after 2 ticks C1, time until safe flat, per-instrument/day/month/session signal counts, days and months of no opportunity and coverage. The 2–3/day combined trading goal is aspirational, not a forced order quota. No M1 or missing M5 reconstruction.

**DO NOT** look at post-entry future candle High/Low, Take/Stop hit order, future MFE/MAE, P&L, PF, winning months or forward returns to choose/modify preflight strategy rules. If sparse or nonpayable, report **INSUFFICIENT OPPORTUNITY / ECONOMICS NOT TESTED** and request user direction. If sufficiently feasible, obtain *another separate* authorization for fixed complete Stage 2 C1 T10/T15 + C2 stress, conservative execution and exits, monthly/UNKNOWN accounting and independent algorithmic audit. Only after positive expectancy, desired Net PF >=1.6 (prefer >2), planned net>=3R, adequate distinct trades and credible regularity may an accepted Baseline be considered for separately authorized Stage 3.

No additional stage, no new test, no auto-merge, no 2024 WF or 2025+ TRUE OOS reads, no LIVE. No edits to TradingSystemLab or its actual robot.
