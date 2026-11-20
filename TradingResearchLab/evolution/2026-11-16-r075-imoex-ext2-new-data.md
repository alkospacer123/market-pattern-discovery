# TRL-R075 — direct IMOEX EXT2 on newly uploaded Sep–Nov 2026 M15

**16.11.2026 · READONLY · NEW_DATA_IMOEX_GATE_ZERO_PORTFOLIO_EFFECT · LIVE_UNCHANGED.**

## Scope

Close the unanswered R074 question: R074 found that directly adding EXT2 to Shallow/OBV IMOEXF **worsened** old-history full-cash net by **−6337.70 ₽ Oct GO, −5429.40 ₽ Nov GO**, but did **not** run newest M15 uploads to 16 November. R073 did use those new bars but compared selected EXT2 vs no EXT2 at all, not the direct IMOEX extension.

**Preregistered** R075 protocol SHA256 `740b117f6e7ff6a2b28cb8bd31ac2f50ed96b4f34b35cf0cfbc35f2094667c13`. Immutable source R073 ZIP SHA256 `57af18b1960b986d9d8e1936f36afcb2e43f4796383453be02a859929914c40f`, with original R060 ZIP SHA256 `80291246ba4692485545f58fd28c7563199bf7be28033fc16eb296efee377e31`. Four newest user M15 OHLCV CSV through source-local bar `2026-11-16 08:15`; M15 overlap OHLCV exact and original four-series historical signal parity PASS. No new trade parameter selection.

**Portfolios:** V20 Shallow60k/OBV30k/Inside45k TP6+protect3 (+3R stop+1R from next M15), Market NEXT_OPEN, N4, 1.5% risk/6% cap, same daily/weekend rules. Compare selected EXT2 only Shallow/OBV USD/CNY/GLD against plus direct EXT2 for Shallow/OBV IMOEX; optional add gate on Inside IMOEX only and on all IMOEX. Full multi-year cash replay with exact same Oct/Nov static GO and C1, report *only* newly entered trades `entry_dt >=2026-09-16`, do not claim 2026 full independent OOS.

## Main newly uploaded sample results, 16 Sep–16 Nov 2026

| GO | Direct IMOEX gate | Trades | Net ₽ | PF | +months /3 partial | Max M15-close DD ₽ |
|---|---|---:|---:|---:|---:|---:|
| OCT | Selected (no IMOEX gate) | 62 | +20709.90 | 2.110391 | 3 | 8764.20 |
| OCT | Shallow/OBV add IMOEX | **62** | **+20709.90** | **2.110391** | **3** | **8764.20** |
| NOV | Selected (no IMOEX gate) | 53 | +18608.50 | 2.186971 | 3 | 8191.50 |
| NOV | Shallow/OBV add IMOEX | **53** | **+18608.50** | **2.186971** | **3** | **8191.50** |

Add EXT2 to Inside IMOEX or all three IMOEX: **also exact no change**. Entire newly executed trade ledgers were identical (times, prices, size, exit reason, cash P&L) in both GO conditions, not just same total P&L. Closed-trade DD Oct6502.10 and Nov5864.10, likewise unchanged. No terminal positions; incomplete Nov16 daily coverage.

**Raw candidate filter triggers newly:** Shallow IMOEX 2026-10-10 10:00, OBV IMOEX 2026-10-10 10:00, OBV IMOEX 2026-11-03 13:00. **Oct10 was Saturday** and weekend rules already disallow entries. The third came when the model already held OBV IMOEX SHORT entered 2026-11-03 13:00 until 2026-11-05 09:00 (+500 ₽ in both GO); no additional admitted entry. Inside IMOEX raw qualifying signals **zero**. Thus 3 qualifying raw patterns, **0 deleted actually admitted trades** in the added period.

**Important nuance:** R074 old sample negative IMOEX extension **does not reproduce** on newer short sample; new effect is exactly 0, not newly negative. Zero observed accepted signals does *not* prove positive value or safety in future; latest bars were partially known, no TRUE OOS. No independent reason to add a gate that was negative earlier and inert now.

## Decision

`RETAIN_SELECTED_EXT2_ONLY_SHALLOW_OBV_USD_CNY_GLD / IMOEX_GATE_NOT_APPROVED / INSIDE_GATE_NOT_APPROVED / LIVE_UNCHANGED`. Do not change V20_TradingSystem_M15 deployment task. New monitoring may collect future genuine independent signals with pre-set frozen rules.

**Reproducibility:** detailed Markdown report `TRL-R075-New-IMOEX-EXT2-Direct-Check.md` SHA256 `00701aded2c3a833a406a7324aff68d3f9658527d2e27acc3fc7e4550e2e3da9`; self-contained source archive `TRL-R075-IMOEX-EXT2-New-Data-Reproducible.zip` SHA256 `0bcfa74672a839a0269243e3d111aab2820e18dd167add58f782331fd2a49117` (R073 original source ZIP including all four newest CSV and R060 original, frozen R075 protocol, `run_r075.py`, `reproduce_r075.py`, full new ledgers and raw hits). Clean-scratch independent extraction/re-execution verified: **R075_CLEAN_REPRODUCTION_PASS_ALL_8_VARIANTS_2_GO_FULL_LEDGER**.
