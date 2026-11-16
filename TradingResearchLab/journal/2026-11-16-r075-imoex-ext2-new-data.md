# TRL Journal — 16.11.2026 / R075 direct IMOEX EXT2 on new M15

**Question:** Does extending EXT2 directly to IMOEXF reduce profit on newly uploaded M15 through16Nov2026, as in old-history R074? **Answer: NO — new-sample portfolio effect is ZERO**, not positive.

**Fixed comparison:** R073 source SHA `57af18b1960b986d9d8e1936f36afcb2e43f4796383453be02a859929914c40f`; R075 protocol before test SHA `740b117f6e7ff6a2b28cb8bd31ac2f50ed96b4f34b35cf0cfbc35f2094667c13`. Capital60/30/45, TP6 Protect3, selected gate on Shallow/OBV USD/CNY/GLD vs plus IMOEX. Four user M15 CSVs 2026-09 to Nov16 08:15 (Nov16 incomplete). Exact old/new OHLC overlap and original signal parity.

**OCT GO 16Sep–16Nov:** selected62/+20709.90 ₽/PF2.110391/3+ months/M15DD8764.20; add IMOEX exactly **same figures and identical 62 executed trades**. **NOV GO:** selected53/+18608.50 ₽/PF2.186971/3+/DD8191.50; add IMOEX identical 53 trades. Direct Inside IMOEX gate also zero effect.

**Why:** raw extended-gate triggers count3 (Shallow and OBV IMOEX Saturday 10Oct10:00; OBV IMOEX Tue3Nov13:00). First two already invalid entry day; third already held OBV IMOEX SHORT 3Nov13:00–5Nov09:00 and could not admit second same-instrument trade. So no admitted trades removed. Older-history R074 still shows direct IMOEX loses −6337.70 ₽ OCT and −5429.40 ₽ NOV; newer zero cannot establish benefit, and new period not TRUE independent OOS.

**Decision:** retain chosen V20_603045_EXT2_TP6_PROTECT3_MARKET without direct IMOEX/Inside gating; no updates to live task. **LIVE_MUTATIONS=0**. Detailed [Evolution](../evolution/2026-11-16-r075-imoex-ext2-new-data.md). Repro archive SHA `0bcfa74672a839a0269243e3d111aab2820e18dd167add58f782331fd2a49117`, clean-run verified 8 variants/2 GO and exact ledgers.
