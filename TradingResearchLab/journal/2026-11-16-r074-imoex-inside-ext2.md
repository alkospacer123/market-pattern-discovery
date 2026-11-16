# TRL Journal — 16.11.2026 / R074: IMOEXF and Inside direct EXT2

**Question:** whether extend EXT2 beyond USD/CNY/GLD Shallow and OBV. R073 direct implementation applied neither IMOEX nor Inside; R074 preregistered six alternative gate placements before simulation. No changes to parameters or original 60/30/45, TP6, +3R→+1R stop, market NEXT_OPEN, GO/risk/weekend constraints.

**Exact cash parity R060:** SELECTED OCT GO/C1 1436 trades / +443168.20 ₽ / PF2.002896 / 43 positive months / M15 DD18666.90. **Add IMOEX Shallow and OBV:** 1431 trades / +436830.50 ₽ / PF1.990146 / 42 months / same M15 DD. Delta **−6337.70 ₽**. NOV GO selected 1224/+301000/PF1.858724 vs IMOEX extra 1218/+295570.60/PF1.844948, delta **−5429.40 ₽**. Historical blocked raw Shallow IMOEX=11 and OBV IMOEX=13; negative effects especially 2025 (−2875 ₽) and 2026 YTD (−3707.30 ₽).

**Add EXT2 to Inside:** exactly 0 blocked raw signals on all four N4 in historical R060 input, hence **0 changes** to trades, PF, profit, months and DD. Not proof it cannot trigger in future.

**Decision:** `RETAIN_3SYMS_SHALLOW_OBV / REJECT_EXTRA_IMOEX / INSIDE_NO_USEFUL_ADDITION / NO_LIVE_CHANGE`. Do not alter the already-started V20 deployment work; no independent OOS, source history repeated, no live fills/actual GO. Same user-provided 16Sep–16Nov CSV not separately run for direct IMOEX/Inside variants. PR remains Draft, changes strictly research-only.

R074 protocol SHA256 `9fb9c940eda66123675023c3ca84af43d236dd033a9c6354fe8d1e9a0a15370a` **fixed before result**; R060 unchanged SHA256 `80291246ba4692485545f58fd28c7563199bf7be28033fc16eb296efee377e31`; reproducible ZIP SHA256 `b7ffb23d9a17f5bb9702be876d649e724ac477791ff1e3376c7d35abc387fe62`. Clean replay **R074_CLEAN_REPRODUCTION_PASS_12_OF_12**. [Evolution report](../evolution/2026-11-16-r074-ext2-imoex-inside-direct-replay.md). **LIVE mutations=0**.