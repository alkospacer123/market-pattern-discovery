# TRL Journal — 16.11.2026: R072 TP6 without profit protection versus TP6+Protect3

**Status:** RESEARCH_ONLY / 12_FULL_CASH_REPLAYS / R060_PARITY_PASS / LIVE_UNCHANGED.

**Why:** After approving target V20 60/30/45+EXT2+TP6Protect3, user asked to separate the profitability of TP6-only from TP6 with +3R-triggered stop +1R, and compare against original 45/45/45. No new parameter tuning or alternative entry algorithms.

**Source:** Exact unchanged archival R060 ZIP SHA256 `80291246ba4692485545f58fd28c7563199bf7be28033fc16eb296efee377e31`; 2023–Sep2026 N4 M15 OHLCV, market NEXT_OPEN, old weekend-off, stop 2xATR14, 1.5% per trade and 6% cap per independent account, integer lots, C1, Oct/Nov2026 static GO proxies. All 12 runs reexecuted from same cash engine `engine(...,tp=6, protection=None|3, finance=...)`, three architectures × two exits × two GO models. Five published TP6Protect3 cash (trades/net/PF) controls reconfirmed exactly. M15-close equity DD recomputed per journal using unchanged R060 method.

## Results OCT GO/C1 (45 months)

| Bank / filter | Exit | Trades | Net ₽ | PF | +months/45 | Closed-trade DD ₽ | M15-close DD ₽ |
|---|---|---:|---:|---:|---:|---:|---:|
| V20 45/45/45, no EXT2 | TP6 only | 1437 | +398716.9 | 1.822476 | 38 | 16069.1 | 19943.3 |
| V20 45/45/45, no EXT2 | TP6+Protect3 | 1449 | +381607.6 | 1.844655 | 40 | 11774.5 | 16700.7 |
| V20 60/30/45, no EXT2 | TP6 only | 1461 | +430233.0 | 1.869600 | 38 | 17124.5 | 20464.1 |
| V20 60/30/45, no EXT2 | TP6+Protect3 | 1473 | +422224.1 | 1.914428 | 42 | 12940.9 | 18666.9 |
| **V20 60/30/45 + EXT2** | **TP6 only** | 1426 | **+450254.8** | 1.947106 | 39 | 12674.9 | **16289.6** |
| **V20 60/30/45 + EXT2** | **TP6+Protect3** | 1436 | +443168.2 | **2.002896** | **43** | **12530.9** | 18666.9 |

**Nuance:** For final EXT2 architecture, protection raises PF by0.05579 and positive months by4, but reduces net by7086.6 and **increases max M15 close drawdown by2377.3**; this is contrary to any categorical claim that profit lock always lowers DD.

**NOV GO/C1 final EXT2:** TP6 only n1213 / +293484.6 ₽ / PF1.773679 / 37+ months / M15 DD17089.5; TP6+Protect3 n1224 / +301000.0 ₽ / PF1.858724 / 42+ months / M15 DD15817.8. Under this GO proxy protection also raises net +7515.4 ₽ while lowering DD1271.7 ₽: **capital/GO dependence**.

**OCT final EXT2 by year:** 2023 TP6 +109602.6/PF2.125 versus +protect +107736.6/PF2.196; 2024 TP6 +138955.7/PF1.896 versus +protect +131831.1/PF1.887; 2025 TP6 +67499.5/PF1.492 versus +protect +76244.7/PF1.625; 2026 YTD TP6 +134197/PF2.565 versus +protect +127355.8/PF2.569.

**OCT final EXT2 by robot:** Shallow TP6 +307897.7/PF2.025 vs protected +308311.5/PF2.107; OBV TP6 +96476.8/PF1.823 vs protected +88349.7/PF1.810; Inside TP6 +45880.3/PF1.793 vs protected +46507/PF1.859. The OBV -8127.1 difference warrants caution and **does not** authorize selective parameters during current deployment. **IMOEXF** Shallow +40760→47050 protected, Inside +1980→4200, OBV +1390→670: different exit effect, not evidence to use EXT2 on IMOEXF.

**Decision:** Retain existing selected Research target `V20_603045_EXT2_TP6_PROTECT3_MARKET` for staging: improved monthly regularity/PF and 2025, but acknowledge TP6-only has larger old-history OCT gross net and smaller OCT M15 DD. No new LIVE spec or deployment alteration on the basis of another in-sample comparison, no clean TRUE OOS, real FINAM GO/fees/slippage unavailable. Further mixed exit research only as preregistered separate hypothesis.

**Artifacts** in conversation: `/mnt/data/trl_tp6_compare/TRL-R072-TP6-Only-vs-TP6-Protect3-Comparison.md`, `compare_tp6_only.py` SHA256 cbdc77435a893e95bb60a7598df3b893dff11add474e4e6f64bf1036c07e9837, `tp6_only_vs_protect_summary.csv`, `tp6_only_vs_protect_annual.csv`, `tp6_only_vs_protect_robot.csv`, `tp6_only_vs_protect_robot_symbol.csv`. All outputs read-only. **LIVE mutations = 0**.