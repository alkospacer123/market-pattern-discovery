# Cycle 16 — Intraday Compression Breakout Continuation

Status: **NO_RESEARCH_SURVIVOR / 27 BASE-PROFITABLE CANDIDATES RETAINED**.

Safety: only CNYRUBF M1 with `2026-01-05 <= t < 2026-05-16` was used. Retired May16–Jul1 was not used. 2025 TRUE OOS was not accessed.

Frozen grid: 72 candidates. Retained by registry rule: 27. Strict gate passes: 0.

Best candidate: `C16-eda8af2caeee1259`.

Parameters: `W=8`, `width_atr=2.0`, `breakout_ticks=1`, `stop_mode=OPPOSITE`, `target_r=1.5`.

Metrics:
- Trades 126; 81 unique trading days.
- GROSS PF 1.792439; expectancy +5.913587 bps; total +745.111900 bps.
- BASE PF **1.498609**; expectancy **+4.130514 bps**; total +520.444770 bps; DD 161.947353 bps; win rate 52.38%; 4 positive months; largest winner share 0.053397.
- STRESS PF **1.255979**; expectancy **+2.347395 bps**; total +295.771757 bps; DD 215.402409 bps; win rate 48.41%; 4 positive months.
- Exit reasons: TARGET 35, STOP 30, DAY_END 30, TIME 30, STOP_GAP 1.
- Sides: SHORT 72, LONG 54.

Strict gate failures: BASE PF < 2.00 and STRESS PF < 1.50. All other listed gate conditions are satisfied by the best candidate.

The neighborhood is not a single isolated point: nearby OPPOSITE-stop configurations at W=8/width=2.0 target 2R and W=6/width=1.5 also remain BASE-positive and STRESS-positive. No post-hoc threshold change is made in Cycle 16. The complete retained candidate set is persisted in the profitable-candidate registry.