# TRL-R076 — MOM8 on IMOEXF only: conditional test beyond selected EXT2

**16 Nov 2026 · READONLY / 16 CASH REPLAYS / R060&R075 CONTROL PARITY PASS / LIVE_UNCHANGED.**

User asked whether MOM8, unlike EXT2, ought to be used on IMOEXF. R060 originally tested MOM8 on Shallow *all N4*, but not the separate IMOEX effect on an otherwise selected EXT2 portfolio. R076 freezes four variants before running: SELECTED EXT2 only Shallow/OBV USD/CNY/GLD; add MOM8 ≥5 previous 8-M15 ATR with no counter M15 body in preceding 3 bars ONLY on Shallow IMOEX; ONLY OBV IMOEX; both Shallow/OBV IMOEX. Inside unchanged. All use 60/30/45k, TP6R+protect3 (stop +1R after +3R, effective from next M15), Market NEXT_OPEN, unchanged risk/GO/weekends, original unmodified R060 engine (original zip SHA256 80291246ba4692485545f58fd28c7563199bf7be28033fc16eb296efee377e31). Preregistered protocol SHA256 e1e8f01fde22eb362578bd27b89173f5600307a4737348bb3cf598f23fd11228.

**Old 2023–Sep2026, OCT GO C1**:

| Variant | n | Net ₽ | PF | +months /45 | Max M15 DD ₽ | Δ vs selected |
|---|---:|---:|---:|---:|---:|---:|
| SELECTED | 1436 | 443168.2 | 2.002896 | 43 | 18666.9 | — |
| +MOM8 Shallow IMOEX only | 1433 | **450161.7** | **2.023924** | 43 | 18666.9 | **+6993.5** |
| +MOM8 OBV IMOEX only | 1431 | 441787.2 | 2.001457 | 43 | 18666.9 | −1381 |
| +MOM8 both Shallow and OBV IMOEX | 1428 | 448780.7 | 2.022514 | 43 | 18666.9 | +5612.5 |

**NOV GO C1:** selected 301000/PF1.858724/42+ months; Shallow IMOEX MOM8 +308140.8/PF1.886162/43+ months (Δ+7140.8); OBV IMOEX +299734/PF1.857716/42+ (Δ−1266); both +306874.8/PF1.88523/43+ (Δ+5874.8). Old annual Shallow-only deltas: 2023 0; 2024 +4223.8 ₽; 2025 +3677 ₽; 2026 YTD −907.3 ₽. 2025 PF1.6245→1.65997 remains below user's PF≥1.7 target.

**Why it is not a proven IMOEX entry-quality edge:** MOM8 Shallow IMOEX suppressed **15 raw** past signals but removed **only 5** executed selected portfolio trades, which had **NET +1135 ₽** (including two strong winners +800 ₽ on 04Dec2024, +2260 ₽ on 14Aug2026). Two replacement entries contributed +2570 ₽. The majority of cash delta is due to **resizing of existing Shallow trades in other symbols**, +5558.5 ₽ on matched entries (especially GLD +2703.8 ₽ after 10→21 lots and CNY +2442 ₽ after 1→23 lots), which only became possible after freeing GO/slots. Thus old positive delta is GO-dependency/reallocation, not direct removal of losing IMOEX trades. MOM8 OBV IMOEX worsened net by 1381 ₽, including removal of winning signals.

**New user M15 16Sep–16Nov2026, OCT and NOV GO:** all four variants trade **identically**: OCT 62/+20709.9/PF2.110391/3 partial positive months/M15DD8764.2, NOV 53/+18608.5/PF2.186971/3 partial months/M15DD8191.5. New MOM8 raw IMOEX triggers **Shallow Sep20 Sunday, Shallow Oct10 Saturday, OBV Oct10 Saturday**, all already excluded by existing weekend rule, so **0 admissible trades filtered**. Newly available bars to Nov16 08:15 are not full, nor independent TRUE OOS. Selected historical cash controls and R075 new sample controls matched exactly 4/4; 4 variants ×2 GO ×2 periods =16 cash replays.

**Decision:** Research interest in MOM8 solely on Shallow IMOEXF recorded, **not approved for LIVE**: the apparent gain is largely due to secondary changes in GO and size, 2026 YTD decreases, and no informative new accepted signals. OBV IMOEX MOM8 not beneficial. Keep current selected V20 60/30/45+EXT2 on USD/CNY/GLD Shallow/OBV, no filters on IMOEX or Inside. Do not alter V20_TradingSystem_M15 task underway. Full Markdown report `TRL-R076-MOM8-IMOEXF-Direct-Test.md` SHA256 3846e562430e14b023f4928e50c0d35c5435e4a1dfab404a9659f4bf557051eb, full trade CSVs and R076 research script held as TRL conversation artifacts. **LIVE_MUTATIONS=0**.