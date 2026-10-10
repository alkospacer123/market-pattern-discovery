# IntradayLab — Stage 2 LEVEL_REJECTION_M5 economic Baseline preregistration

2026-10-10. STATUS: PRE-RETURNS FREEZE / NOT RUN / NO ECONOMIC PASS.

Authority: merged PR #459; actual main `9914ebbc97e3ba1fded1b6f06fb4bd66a82c2811`. Frozen opportunity manifest, preregistration, scanner and existing results unchanged. Exact machine rules: [frozen economic config](../config/stage2_level_rejection_m5_economic_v1.json).

## Trading contract fixed before economic inspection

1. Four perpetuals USDRUBF, CNYRUBF, GLDRUBF, IMOEXF; complete physically available 2023 M5 from pinned source commit and identical input SHA/prefix-byte budgets. Same MSK/start-label and historical session exceptions, T10 and T15 separately. All 2024 Walk Forward and 2025+ TRUE OOS locked unread.
2. Use the complete PR #459 signal, admission and risk rules unchanged: past six completed M5, breached/reclaimed level, one-tick Stop beyond wick, delayed strictly future M5 Open, 30-minute directional dedup, 4-tick minimum initial risk, B-35 safety. No extra indicator or signal filter and no requirement that Take stays inside the old six-bar range. A future Open is a conditional model fill only.
3. One model exposure per symbol; EXIT-before-ENTRY for equal timestamps; record all BUSY signals explicitly. Unknown possible entry blocks any more entries on that symbol through year-end unless proven reconciled.
4. Resident protective Stop even on entry candle; adverse gap exits at worse Open; if both Stop and Take become eligible in one bar, STOP wins. On entry candle do not credit a Take because intrabar order is unknown. After entry bar, require at least one tick penetration beyond TP, not mere level touch.
5. Target frozen on entry as full-net-to-net 3R AFTER C1: gross distance d=3*s+8*t, where s is gross entry-to-initial-Stop distance and t is dated single-side tick. C1 is one tick per executed side; C2 substitutes two ticks per side on identical modeled entries, exits and unchanged Take/Stop. No extra broker fees.
6. Failed reclaim after entry: later completed M5 Close at least one dated tick beyond original rejected level in adverse direction requests market flatten no sooner than the candle's completed delivery + T10/T15, filled conditionally on a STRICTLY later Open. Never use the hindsight Close as fill. Resident Stop remains active until exit.
7. Maximum intended hold 120 minutes, begin time-close request at entry+115 minutes; fill at later Open. Session safety request at B−(15+delay) minutes (B−25 for T10, B−30 for T15), modeled flat acknowledgment no later than B−10. Missing close, boundary exposure or emergency data gap is unresolved and must not be converted into a favorable outcome.
8. A missing or zero-volume scheduled entry bar means UNKNOWN_POSSIBLE_ENTRY, not NONFILL or FLAT. A missing/zero-volume M5 while position may exist means UNKNOWN trade outcome, emergency exit at earliest subsequently observed allowable Open only if possible. Maintain all uncertainty, full annual Net/PF/DD null when not provable, with closed-only diagnostics clearly distinguished.
9. Independently report modeled trades, exit attribution, hold time, direction, C1/C2 net, PF, expectancy, top trade concentration, drawdown, worst month and 12 calendar months including pre-inception NO_COVERAGE and UNKNOWN. Price-unit quote results for different contracts cannot be naïvely summed as actual account RUB returns; normalized R is an analytical comparison, not leverage sizing.

## Research acceptance

Requirements jointly assessed: aspiration 2–3 executed model trades/day aggregated; after-C1 positive expectancy, Net PF >=1.6 preferably >2, planned full-net 3R, high fraction of positive calendar months (12/12 ideal but not guaranteed), controlled DD/losing streak/recovery, no top-two-trade reliance, T15 and C2 resilience. The prior 1754/1648 upper-bound opportunities prove none of these economic metrics.

An independently checked full-year Baseline can be ACCEPTED or REJECTED; no selected profitable-month optimization. If gaps cause incomplete annual results, report INCONCLUSIVE / no Baseline PASS, retaining null headline metrics. Source integrity, same-fills C2, older strategy hashes and untouched TradingSystemLab protected roots required.

Work strictly inside IntradayLab/. Stage3, 2024 Walk Forward, TRUE OOS 2025+, FINAM LIVE and Merge are NOT authorized by this freeze.
