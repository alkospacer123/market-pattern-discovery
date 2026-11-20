# TRL-R074 — Extension of EXT2 to IMOEXF / Inside: direct full-cash replay

**16 Nov 2026; PREDECLARED SIX VARIANTS / EXACT R060 CASH PARITY / RESEARCH-ONLY / LIVE_UNCHANGED.**

User asked whether direct EXT2 should be applied to IMOEXF and Inside after R073. R073 did **not** directly gate them: its IMOEX P&L +2495 ₽ was *indirect* capital/entry slot displacement; Inside P&L unchanged. R074 directly measures the additions with unchanged 60k Shallow/30k OBV/45k Inside, original strategies, M15 NEXT_OPEN, stop 2×ATR14, TP6 and +3R-triggered +1R stop from next M15, 1.5%/6% per account, two entries per session, weekend entry ban, C1 one tick per side. Same R060 original unchanged engine and 2023–Sep2026 N4 OHLCV; Oct and Nov static GO proxies, three separate accounts, full reexecution of positions, integer lots and next signals. Original source R060 SHA256 `80291246ba4692485545f58fd28c7563199bf7be28033fc16eb296efee377e31`.

**Frozen before calculation:** `R074_FROZEN_PROTOCOL.md` SHA256 `9fb9c940eda66123675023c3ca84af43d236dd033a9c6354fe8d1e9a0a15370a`. Tested 6 variants against selected EXT2(Shallow, OBV on USD/CNY/GLD): add IMOEX Shallow/OBV; add Inside on 3 syms; add Inside IMOEX; add Inside all4; add IMOEX Shallow/OBV + Inside all4. No parameter optimization.

| Scenario / OCT GO C1 | n | NET ₽ | PF | Months positive /45 | Max M15-close DD ₽ |
|---|---:|---:|---:|---:|---:|
| **SELECTED** | **1436** | **443168.20** | **2.002896** | **43** | 18666.90 |
| Add direct EXT2 Shallow/OBV IMOEXF | 1431 | 436830.50 | 1.990146 | 42 | 18666.90 |
| Add EXT2 Inside USD/CNY/GLD | 1436 | 443168.20 | 2.002896 | 43 | 18666.90 |
| Add EXT2 Inside IMOEXF only | 1436 | 443168.20 | 2.002896 | 43 | 18666.90 |
| Add EXT2 Inside all4 | 1436 | 443168.20 | 2.002896 | 43 | 18666.90 |
| Direct EXT2 every robot/all4 | 1431 | 436830.50 | 1.990146 | 42 | 18666.90 |

**Direct IMOEX extension reduces NET −6337.70 ₽**, PF −0.01275, 1 fewer positive month, closed-trade DD +345.10 ₽, max M15 DD unchanged. Raw signals suppressed: **11 Shallow IMOEXF and 13 OBV IMOEXF**; full cash replay ended with 5 fewer *trades* (not 24), because cash, slots and subsequent trades reflow. Direct Inside EXT2 blocks **zero original Inside raw signals** across all N4, so no effect in this specific period; do not infer perpetual impossibility.

**NOV GO C1:** selected 1224/+301000.00/PF1.858724/42+ months/DD15817.80; plus IMOEX 1218/+295570.60/PF1.844948/42+ months/DD15817.80, **−5429.40 ₽** with worse closed-trade DD by1760 ₽; Inside additions exactly no effect.

**By year OCT GO, delta add IMOEX:** 2023 0; 2024 **+244.60 ₽**; 2025 **−2875.00 ₽**; 2026 YTD **−3707.30 ₽**. By robot add IMOEX: Shallow total −4287.70 ₽, OBV total −2050.00 ₽, Inside 0; Shallow IMOEX 47050→42845, OBV IMOEX +670→−1380. These are full portfolio estimates conditional on other signals and account balances.

**Conclusion:** `REJECT_DIRECT_IMOEX_EXT2 / INSIDE_EXT2_REDUNDANT_IN_THIS_SAMPLE / RETAIN_SELECTED_EXT2_3SYMS_SHALLOW_OBV / NO_LIVE_MUTATIONS`. Old data repeatedly mined / no TRUE independent OOS; these new direct variant tests **do not include separately uploaded 16Sep–16Nov 2026 files**. Model GO/fees and M15 close mark ≠ real FINAM executions or intrabar risk. No changes to current V20_TradingSystem_M15 work order from this evidence.

Self-contained archive `TRL-R074-IMOEX-Inside-EXT2-Reproducible.zip` SHA256 `b7ffb23d9a17f5bb9702be876d649e724ac477791ff1e3376c7d35abc387fe62`: frozen R060 ZIP, R074 preregistration, original runner, full trades, summary/annual/robot/symbol/monthly CSV, `reproduce_r074.py`. Independent clean unpack and re-run: **R074_CLEAN_REPRODUCTION_PASS_12_OF_12**. Full report: `TRL-R074-IMOEX-Inside-EXT2-Expansion.md`.
