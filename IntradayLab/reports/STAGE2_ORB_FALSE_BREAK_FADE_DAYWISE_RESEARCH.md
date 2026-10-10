# IntradayLab — отдельная диагностика UNKNOWN для ORB False-Break Fade

**STATUS: CODE ADDED / PHYSICAL 2023 REPLAY NOT YET VERIFIED.**

Problem: the original strict Stage 2 ORB v1 correctly latches fail-closed after an
unresolved position and therefore cannot assess later independent research days.
The original strict results and configuration are frozen and are not edited.

This diagnostic performs **four architecture × four instrument = 16** scenarios
using the **same frozen signals, filters, entries, stops, take, C1/C2 and MTF**.
It replays each trading date independently, with the original fail-closed
behavior **within** that date. If one day ends with UNKNOWN, the next day is a
**counterfactual experiment starting from assumed FLAT**; this is explicitly
flagged on every subsequent signal/trade. It does **not** verify a flat
brokerage position or resolve the missing execution path.

### Run (Codex Cloud workspace with pinned data repo)

Run the same base/synthetic tests and then:

\`\`\`powershell
python -m unittest discover -s IntradayLab/tests -v
python IntradayLab/tools/run_orb_false_break_fade_daywise.py --data-root /workspace/market-pattern-data
\`\`\`

Use the actual workspace path to the clean, pinned data repository. The program
verifies source commit, blob IDs, input prefix hashes, independent raw source,
independent signal oracle and per-day independent trade oracle. Commit the
generated new files under
\`IntradayLab/results/stage2_orb_false_break_fade_m5_daywise_v1/\` only after
real execution and verification.

Required review: strict versus daywise by each symbol/architecture, UNKNOWN
counts and dates, number of recovered conditional closed trades, C1/C2 PF and
Net R (diagnostic only), all 12 months, ATR rejection funnel and MTF rejection
funnel. Do not replace strict annual Net/PF/DD nulls, interpret daywise figures
as account P&L or modify ATR/MTF parameters based on the replay.

**No M1. No 2024+ replay. No TradingSystemLab changes. No Merge or Stage 3.**
