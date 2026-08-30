# Cycle 18 — Opening-Range False-Break Fade

Status: **1 STRICT RESEARCH_SURVIVOR / 38 BASE-PROFITABLE CANDIDATES RETAINED**.

## Safety / integrity
- Only CNYRUBF M1 with `2026-01-05 <= t < 2026-05-16` was used.
- Retired `2026-05-16` through `2026-07-01`: NOT USED.
- 2025 TRUE OOS: NOT ACCESSED.
- Top candidate was independently rechecked trade-by-trade against raw permitted M1: 36/36 entries/exits, stops, targets, friction, timestamps and STOP_FIRST path checks passed; no overlap; last used exit `2026-05-15 11:24`.

## Strict survivor
Candidate `C18-d67edca2d39566f5`.

Parameters: `buffer_atr=0.30`, `reclaim_bars=1`, `inside_ticks=2`, `target_r=1.5`, `max_hold=60`.

- N=36; 33 unique trading days; LONG=18 / SHORT=18.
- GROSS PF=3.028912; expectancy=+7.072320 bps; total=+254.603508 bps; DD=36.839009 bps.
- BASE PF=**2.331313**; expectancy=**+5.295450 bps**; total=+190.636188 bps; DD=42.227682 bps; win rate=72.22%; positive months=4; largest-winner share=0.124938.
- STRESS PF=**1.778669**; expectancy=**+3.518578 bps**; total=+126.668815 bps; DD=51.244412 bps; win rate=69.44%; positive months=4.
- Exits: TIME 14, TARGET 12, STOP 10.
- Reclaims: same sweep bar 24, next eligible M5 bar 12.

All strict preregistered gates pass.

## Time diagnostics (post-selection diagnostics only)
- First 18 trades: BASE PF=2.2331, STRESS PF=1.6797.
- Last 18 trades: BASE PF=2.4274, STRESS PF=1.8780.
- Jan-Feb: BASE PF=1.6073, STRESS PF=1.1997.
- Mar-May15: BASE PF=2.7449, STRESS PF=2.1107.
- Monthly BASE totals: Jan -42.23 bps; Feb +73.84; Mar +50.76; Apr +88.01; May1-15 +20.25.

## Neighbor diagnostics
The strict pass is not a broad plateau. One-axis frozen-grid neighbors remain mostly profitable but fall below the strict PF thresholds:
- reclaim_bars=0: N=24, BASE PF=2.4449, STRESS PF=1.8501 (fails N>=30 only);
- reclaim_bars=2: N=47, BASE PF=1.7046, STRESS PF=1.3315;
- inside_ticks=0: N=53, BASE PF=1.7822, STRESS PF=1.3461;
- target_r=2.0: N=36, BASE PF=1.8016, STRESS PF=1.3605;
- max_hold=120: N=36, BASE PF=1.6920, STRESS PF=1.3213;
- buffer_atr=0.15: N=47, BASE PF=1.4618, STRESS PF=1.1069.

Therefore `C18-d67edca2d39566f5` is promoted only to **RESEARCH_SURVIVOR**, not to production or confirmed edge. It now requires genuinely fresh untouched data. No 2025 TRUE OOS or retired May16-Jul1 data is opened for that purpose.