# IntradayLab — LEVEL_REJECTION_M5 v1 preregistration BEFORE frequency / economic results

**2026-10-10. Status: STAGE2_LEVEL_REJECTION_RULES_PREDECLARED; empirical 2023 frequency, trades, economic performance: NOT RUN.**

GitHub base authority: `832739dfb9c9ec8f4f2fc1768d7fc07fbc69521c` (merged PR #458). This standalone IntradayLab-only freeze is the first step of the user's explicitly authorized **Stage 2 opportunity/geometry preflight**, not a new stage or full economic Baseline. [Immutable machine manifest](../config/stage2_level_rejection_m5_opportunity_v1.json) is the only numeric/settings authority.

### Market premise

A previously completed six-M5 range defines known high and low for the current continuous research window. The next completed M5 tests/breaches that level by at least one valid instrument tick and its CLOSE returns at least one tick INSIDE. This is a **price-only failed-level test**; no historical STOP orders, bid/ask or hidden liquidity can be inferred from OHLCV. LONG is rejected lower bound; SHORT rejected upper bound. If one candle sweeps both, label AMBIGUOUS_BOTH_SIDES, no signal. It is not VWAP mean reversion, breakout chasing or Squeeze.

### Full rules frozen *before counts*

- Use exactly **six contiguous earlier completed, positive-volume M5 within the SAME allowed continuous session window**, with no missing bars/lunch/night bridging. Earlier-six HIGH/LOW exclude the test candle. Test candle must be complete and available at **start+5+T**; T10 & T15 are independent.
- One failed level test per direction per instrument per **30 clock minutes** from previous confirmed test start, whether its order fills or fails. Print both raw and deduplicated counts; no results-driven cooldown editing. No position/exits simulated, so unique conditional entry count is only **an upper bound on real tradable frequency**.
- Freeze Stop beyond the test extreme by one dated tick: below low for LONG / above high for SHORT. Require at the scheduled entry Open both preservation of reclaim (strict 1 tick inside known level) and correct Stop-side geometry, **at least four ticks** initial raw risk.
- Enter at first exact future M5 Open strictly AFTER signal delivery: `test_start+20min` for T10 and `test_start+25min` for T15. The future target is a **schedule**, not information available when the signal is placed. A missing actual scheduled M5 must remain UNKNOWN_POSSIBLE_FILL (never invent an Open); a complete observed target failing geometry is NONFILL.
- Keep the same historically accepted daytime windows, valid-date and CNY historical tick grids. New entry requires its M5 complete bar inside the same window and `entry_start+35min <= window_end` for flat-risk reserve; not evidence that the eventual exit can be guaranteed.
- Model **C1 = 1 dated tick per side** only. At conditional Open let `s=abs(Open-Stop)`, `t=tick`; legacy gross-target `d=3s+2t`, and the fully after-C1 win/stop-loss **net-net** target `d=3s+8t`. Both outward grid-aligned target prices and initial net ratios must be in result rows. Primary target uses the latter; an arithmetic target **is not proof it will be reached**. Whether target is within the already known opposite bound is explanatory only, not an extra hidden entry filter.
- No price path after the entry Open is examined (no entry bar High/Low, later Stop/Take, actual wins, PnL, PF, MFE/MAE or selected profitable months) in this task. Future price mutations cannot change earlier admission. Deduplication and raw-vs-distinct counts must remain auditable.

### Research output and gating

Read only frozen **2023** source prefixes with SHA-256, byte budget and row budget directly inherited from already-audited Stage 2 Squeeze inputs (2024/2025+ bytes read = 0). Four instruments: USDRUBF, CNYRUBF, GLDRUBF, IMOEXF. Report funnel and rejection reasons, real M5 observation coverage and same-window valid slots, gaps, admissible risk and 3R geometry, both delays, instruments, LONG/SHORT, day/week/**all 12 calendar months**, no-opportunity days and missed months, combined distinct actionable opportunities with cross-instrument overlaps disclosed. Do not claim 2–3 *executed* trades/day from signals alone.

**PASS only for causal opportunity research and independently audited counts.** It cannot receive economic Baseline PASS at this step. If even opportunity count is tiny or full-net 3R geometry unpayable, record `INSUFFICIENT_OPPORTUNITY` and stop without unfreezing settings. Stage 3, 2024 WF, locked 2025+ TRUE OOS, LIVE, new candidates and full financial Baseline remain unauthorized.

**Protected trees:** no files outside `IntradayLab/`; no changes to previous IntradayLab strategy engines, configs and results. TradingSystemLab (including real robot) completely untouched.

