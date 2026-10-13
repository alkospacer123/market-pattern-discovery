# IntradayLab — T3/M15 A6+S1 TRAIL_375 Robustness v1 — protocol

**Status:** ARCHIVED-LEDGER ROBUSTNESS IN PROGRESS; full independent raw-OHLC causal replay is **NOT RUN**. 2023–2024 DEVELOPMENT_EXPOSED / GROSS_ONLY / COSTS_DEFERRED / NOT_LIVE_READY.

## Frozen input and scope

- Base GitHub `main`: `9b496d49e3ab8f71a843b24f9ccc288c9c5ff5bd` (PR #508 MERGED).
- Frozen A6+S1 / T3 M15 / NEXT_OPEN / TRAIL_375 from PR #505–#508. **No rule, stop, filter, signal, timeframe, instrument, parameter, or cost changes.**
- Read-only canonical CLOSED ledger: `IntradayLab/t3_m15_early_risk_protection_v1/results/control/trades.csv`, Git blob `72597dbab205be76a1bcb3d26e0e5f39fa4190f2`. It matches the same 480 frozen CONTROL CLOSED trades in PR #507 and reproduces the published #505 trade economy.
- 480 CLOSED, 1 terminal OPEN in the frozen reference. OPEN is excluded from PF, Gross R, monthly and stress calculations, **not** assumed liquidated.
- Four instruments USDRUBF, CNYRUBF, GLDRUBF, IMOEXF, both directions, full 2023 and 2024. GLDRUBF/IMOEXF have partial 2023 coverage. No 2025+ prices are accessed.
- Repo scope: new `IntradayLab/t3_m15_a6_s1_robustness_v1/` only. TradingSystemLab, running robot, roadmap, prior studies, market-pattern-data unchanged.

## Fixed diagnostics, without re-optimization

1. **CONTROL ledger arithmetic:** independently reconstruct annual and full PF = sum(positive CLOSED gross R)/absolute sum(negative CLOSED gross R), gross R, CLOSED counts, 24 monthly results and sequential CLOSED-R peak-to-trough DD; check against published PR #505. Deterministic chronological sort by exit timestamp, instrument, trade_id. Confirm source blob; verify no duplicate closed-trade identity.
2. **Instrument and direction:** all instruments × 2023/2024 and LONG/SHORT × 2023/2024; no removal or selection for primary evaluation.
3. **Four leave-one-instrument-out cases:** remove exactly one instrument at a time *arithmetically from the immutable separate-instrument trajectories* and recompute PF/R, month counts and DD. Confirm no cross-instrument capital constraints in frozen research; these arithmetic slices are **NOT an alternative causal portfolio replay**.
4. **Month concentration:** each year's top1 and top3 months by signed Gross R, month fractions relative to signed annual R (N/A if annual R<=0), diagnostics excluding top1/top3; November 2024 separately. Primary results always use all months. Monthly 24-month denominator explicit.
5. **Large-winner concentration:** top1, top3, top5, top10 positive CLOSED R for 2023, 2024, combined; recompute PF/R after excluding their records for sensitivity. Preserve all trades in CONTROL. Report original >=2R and >=5R winner counts, and fraction of positive R coming from top winners.
6. **Fixed post-trade R haircut:** zero (CONTROL), minus 0.05R, minus 0.10R per originally CLOSED trade, including winners/losers/zeros; recompute signed PF, Gross R, DD, 24 monthly signs. This is arithmetic **NOT causal slippage/fill replay, C1, actual Finam/MOEX fees or funding**. Do not add levels.
7. Comparison to roadmap: annual original Gross PF >=1.70 separately in 2023 and 2024; desired 20–24 positive months and low concentration. Stress/LOO are fragility diagnostics **NOT automatic yearly PF gate criteria**. Assess SUPPORTED/MIXED/FRAGILE by explanations, no tuned composite score or arbitrary extra cutoffs.

## Execution and verification boundary

This isolated run uses the **previously fully audited frozen CLOSED ledger** and independently recalculates its derived metrics. It does not access OHLC or re-run the backtest engine. Accordingly:
- `CONTROL_ARCHIVE_RECALCULATED` is distinct from `CONTROL_FULL_CAUSAL_REPLAY_PASS`.
- Until independently replayed on pinned raw `market-pattern-data/forever/` (SHA `f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8`) and independently audited, mark full replay `NOT_RUN`; **do not** claim a complete Stage Robustness pass or independent OHLC audit.
- New sensitivity output is not independent future evidence: 2023–2024 are already development exposed.
- Store code, human-readable Russian report, machine results, source receipts, and negative findings. No Walk Forward, TRUE OOS, LIVE, broker actions, merge or auto-merge.

One Draft PR only. STOP after the draft for review.
