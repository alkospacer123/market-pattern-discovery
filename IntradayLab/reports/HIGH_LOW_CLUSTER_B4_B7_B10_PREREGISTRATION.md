# HIGH_LOW_CLUSTER_M5 — B4 / B7 / B10 pre-P&L registration

Authorized fixed Baseline 2023 only, 2026-10-11. Actual origin/main and merged PR #474 verified at `8db73e6338bc5b89eda385e21167e22c74e5a299`; this equals the user-supplied base. Three independent versioned configurations are committed together before the first historical P&L run. No selection by maximum PF, no Oracle run, no Optimization or model C. Existing common Backtester and all prior IntradayLab files remain unchanged.

## Signal and deterministic event identity

For each symbol/day/session/dated tick and direction, start an episode with the first valid completed M5. Maintain the minimum and maximum of **all** High values for SHORT, Low values for LONG since episode start. Envelope can expand while <=3 historical ticks. A new completed extreme making it >3 ends the old episode and starts a new one on that current candle; earlier candles cannot be recycled. Missing/invalid candle, nonadjacency, session/day or tick change ends/reset state. Invalid candle starts no new episode. Events never cross sessions or days.

Within that episode inspect exactly the last N consecutive completed candles, N fixed at 4, 7 or 10. A construction is formed when max-minus-min is 1–3 dated ticks inclusive and at least two extrema equal its external boundary (SHORT max High / LONG min Low). Width zero belongs to A and is excluded. Consume the episode on the **first formed construction**, even if Close is on boundary, entry is refused, position is busy or UNKNOWN. A Close at boundary is recorded as CLOSE_AT_BOUNDARY and gives no signal or later attempt. Otherwise SHORT final Close < boundary / LONG final Close > boundary yields a signal at candle end, with no extra confirmation.

If both directions yield signals at one completed boundary, reject and consume both as AMBIGUOUS_BOTH_SIDES. A non-signalling opposite CLOSE_AT_BOUNDARY does not veto a valid direction. No future return enters this decision.

`episode_id = symbol + day + direction + first candle start + initial extreme in dated ticks`. It is independent of N and admission. `cluster_id = B<N> + episode_id`. Each formed episode has one record, one potential entry and explicit observed end/reset reason in episodes.csv; unformed episodes are internal state and not exported. Signals preserve the exact N extrema and timestamps, window min/max, width, boundary/internal counts, first/last **boundary** touch, episode envelope and prefix length. Episode end metadata is ex-post descriptive only and never passed to signal/admission.

## Common frozen execution

ENTRY_NEXT_OPEN uses the scalar Open of the M5 starting exactly when signal candle closes. Current H/L/C/Volume never enters admission. Stop = SHORT boundary +1 dated tick / LONG boundary -1. Reject wrong side, risk <3 or >12 ticks, favorable distance >4 ticks. Never shift Stop. Combined constraints imply 3–5 tick accepted risk; C1=2 ticks gives 0.40–0.667 raw-risk R. This implication is technical, not a tuned parameter change.

FULL_NET_C1_R=3: with raw Stop risk s and current tick t, gross target distance `3(s+2t)+2t = 3s+8t`, outward grid rounding; planned net winning amount divided by planned net Stop loss is 3. The ledger reports gross/cost/net in raw initial-risk R, so a TAKE is 4.2–5 raw-risk net R for accepted 3–5 tick Stops. Hold <=120 calendar minutes; existing daytime windows 10:00–14:00 and 14:05–18:50 MSK, 13–20 March PM start 14:15, flat one M5 before window end. Stop-first, actual adverse Open gap, no entry-bar Take, one position per instrument, UNKNOWN blocks current day, later independent days explicitly assume FLAT. No new deadline, capital sizing or execution guarantee.

## Round diagnostics fixed without P&L

| Instrument | Round step | Rationale |
|---|---|---|
| USDRUBF | 0.10 RUB | Existing ROADMAP decimal reference; 10 historical ticks |
| CNYRUBF | 0.05 RUB | Existing ROADMAP reference; fixed price step despite 0.01→0.001 tick change |
| GLDRUBF | 10 RUB per gram | Simple decimal quote landmark, 100 ticks at 0.1; no claim of empirical optimum |
| IMOEXF | 10 index points | Simple decimal index landmark, 20 ticks at 0.5; no claim of empirical optimum |

Nearest node is determined from the **external boundary**, ties round upward. ROUND_NEAR means distance <=1 signal-date tick, ORDINARY_FAR otherwise. Preserve nearest node and distance in price and ticks. These diagnostic subsets have identical entry/Stop/Take and are not independently tuned systems.

## Data, audit and classification

Pinned clean read-only data `f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8`, four exact 2023 M5 prefixes inherited from audited A config: 42576 USD, 39362 CNY, 18428 GLD, 4429 IMOEX rows. An unbuffered byte guard rejects every read beyond each approved prefix and all other data paths. No 2024/2025+ prices even for auxiliary calculations. GLD inception 2023-07-11, IMOEX 2023-11-14. CNY tick changes 2023-09-27 19:00 MSK, including causal state reset even though it is outside approved daytime windows.

Before commit run all IntradayLab regression and new synthetic tests, plus full 2023 **signal/admission feasibility only** for all three models without the Backtester, trade paths or P&L. Compare the completed constructions with a separate raw batch envelope partition algorithm. Freeze strategy, runners, independent auditor, validation, reporting, all configs, manifest and source hashes together.

Run B4, B7, B10 sequentially into separate immutable directories. Independent auditor imports no production strategy/engine/loader/metrics: independently reads approved LF-limited raw prefixes, partitions envelopes, reconstructs N-bar windows and episode endings; independent shared A execution oracle verifies NEXT_OPEN, Stop, limits, FULL_NET_C1_R, Stop-first, session exits and UNKNOWN. Recompute metrics and month/direction/round/touch reports from CSV. Two full byte-identical repeats of each result and all old default-mode/A replays are required. Audit is algorithmically independent implementation by the task agent, not external reviewer signoff.

Use A's fixed economic evidence policy for fair reporting: incomplete coverage/outcomes => INCONCLUSIVE with separate known-closure diagnosis; negative known expectation => NO ECONOMIC BASELINE PASS for those closures. PF goals >=1.6 in both R/price, adequate independent events/days, positive regular months and concentration limits never imply PASS by one PF. B models overlap: export paired ID overlap and interval overlap; do not pool them as independent experiments, claim significance or select a winner.

Required ledgers/reports plus episodes, coverage, round and boundary-touch reports; hashes and provenance. Conditional DD only on known closures, full annual/account PF/Net/DD null where coverage incomplete. No-trade months distinguished from PRE_INCEPTION/NO_COVERAGE. Preserve all original A_v1 and protected trees byte-for-byte. Draft PR without Merge. STOP after three fixed Baselines.
