# TradingSystemLab — Frozen Stage 7 Production Strategy Passport

## Identity (unchanged)
- Production specification: `PROD_STAGE7_46DB784378797C7FB04636892350AFF21006D71A31F2CED9D4B974EDA2DC36B8`
- Active identity: `TRAIL1__N4_01__FULL__R15`
- Frozen strategy: T3 / H1 / TRAIL1, candidate `T3_H1_candidate_v3`
- N4 instruments: USDRUBF, CNYRUBF, GLDRUBF, IMOEXF
- FULL/R15: initial new-position risk 1.5% of current realized equity; nominal simultaneous initial risk ceiling 6%
- Quantity: round down to contract lots after applying both R15 risk limit and margin limit; zero remains zero
- No pyramiding, no session-entry filter, no automatic canonical fallback, no MICRO_LIVE cap
- Research outcomes and Stage 7 strategy identity are historical authority, never reoptimized by this incident

## Production data and code provenance
- Stage5 data commit: `50f1fd2178c18b7ab3bd969be82ad01f47a34745`
- Historical accepted/Intel code commit: `4c7cd7cbbde5fbffb63ed6984cf89b90dc50d129` (not silently replaced)
- Corrective GitHub code merge: `184e8c2b8fa092a606249ff293a4f507160bff29` (PR #484; not physically accepted or activated yet)
- Earlier 2026-10-08 OHLC correction: PR #435; preserved as historical provenance
- Stage5 and persisted completed H1 are immutable. Later FINAM-only historical timestamps at or before the latest accepted H1 timestamp are ignored; no historical insertion or rewrite. The latest exact seam must be present; only strictly newer completed bars may append.

## Operational state — 2026-10-12 incident
Operator evidence: emergency kill switch `HALTED`, generation 59 at `2026-10-12T05:55:33.966970+00:00`; service Running; positions=0 and unresolved intents=0. The earlier ARMED status (generation 58) predates HALT. Fault: `STAGE8_12_4_H1_SPLICE_TIMESTAMP_MISMATCH`; FINAM introduced `2026-10-10 09:00 MSK` retroactively across all N4. Accepted seam `2026-10-11 18:00 MSK` was present, later bar `2026-10-12 07:00 MSK` observed.

Earlier week: 58 evaluated H1 per N4 / 232 total / zero full T3 entry signals, intents, fills and signal sequence.

**Code merge is not LIVE approval.** Full repository tests and Intel HALTED preactivation remain pending, followed by separately controlled commit-bound authorization rollover and explicit operator re-arm permission. No automatic production checkout update; no historical continuation edits.

See `PRODUCTION_RUNBOOK.md`, `PRODUCTION_OPERATOR_CHECKLIST.md` and `authority_provenance.json`.
