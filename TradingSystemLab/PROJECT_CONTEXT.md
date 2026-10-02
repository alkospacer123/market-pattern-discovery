# TradingSystemLab project context

## Purpose and authority

TradingSystemLab is the repository's deterministic systematic-trading research,
production-design, and robot-integration domain. The Git repository is the
authoritative persistent memory; conversation history is not.

Read `CURRENT_STATE.md` first.

## Canonical research lifecycle

The sole research-methodology authority remains:

**Baseline → Optimization → Robustness → Walk Forward → TRUE OOS**.

Candidate freeze is procedural identity fixation, not a sixth research phase.
Historical v1/v2/v3 identities and verdicts are immutable.

## Research generations

### v1

Historical broad strategy/timeframe discovery including multiple strategies,
timeframes and later MTF work.

### v2

Historical quarterly-futures T2/T3 diversification on M30/H1 across
`Si`, `CNY`, `GD`, `BR`, `MIX`, `NG`. Its full lifecycle is complete; all four
final TRUE OOS study classifications are `BORDERLINE`.

### v3 Perpetual

Universe: `USDRUBF`, `CNYRUBF`, `GLDRUBF`, `IMOEXF`; T2/T3; M30/H1.

Final TRUE OOS:

- T2/M30 `BORDERLINE`;
- T2/H1 `BORDERLINE`;
- T3/M30 `PASS`;
- T3/H1 `PASS`.

v3 TRUE OOS is consumed.

## Frozen upstream strategy identity

Production work originates from the accepted v3 T3/H1 candidate:

- candidate `T3_H1_candidate_v3`;
- configuration `T3-H1-4e73cdb77246`;
- parameter hash
  `4e73cdb77246cb07b5953160b9fc0ab36bfd4bd6d9a7f7faaae7e6e392ee340a`;
- T3 source hash
  `840dd3b2cda43fa00259445cd0a22ace6d82e677f4c793028ccc8126f9ad9a8c`.

## Post-v3 evidence program

Stages 1–5 are complete historical evidence:

1. master v1/v2/v3 consolidation;
2. portfolio/diversification analysis;
3. trade anatomy/failure analysis;
4. structural hypothesis freeze;
5. separate structural validation.

Stage 5 authoritative economic contract is `CORRECTED_SINGLE_C1`.

Final Stage 5 labels:

- BE1 `MIXED_RETROSPECTIVE_EVIDENCE`;
- TRAIL1 `SUPPORTED_RETROSPECTIVELY`;
- Total Open Risk Cap `FORMAL_RESEARCH_VERDICT_NOT_ASSIGNED`;
- Minimum Hold `NOT_ADMITTED / DIAGNOSTIC ONLY`;
- Session `NOT_ADMITTED / DIAGNOSTIC ONLY` at Stage 5;
- Correlation/Simultaneous Risk `NOT_ADMITTED / DIAGNOSTIC ONLY`.

## Stage 6 historical checkpoints

Original Stage 6 selected
`PROD_STAGE6_83C7B31BB42C` = v3/T3/H1/CNYRUBF+GLDRUBF+IMOEXF/TRAIL1.

Later Stage 6.1–6.7 work performed retrospective pre-Stage-7 reassessment.
Important results include:

- SESSION_10_21 admitted to Structural Stack;
- ONE_BAR confirmation rejected;
- opposite-regime exit not admitted;
- LOCK1_AFTER_2R admitted;
- `STRUCTURAL_STACK_V1 = SESSION_10_21 + LOCK1_AFTER_2R` admitted;
- Stage 6.6 compared 55 fixed configurations;
- Stage 6.7 broad eligibility audit found no broadly eligible case meeting the
  70–80% target under its strict gates.

These are historical production-design diagnostics, not fresh OOS.

## Final N4 production-decision evidence

A user-authorized focused Stage 6.7 N4 FULL four-case comparison then evaluated
only:

- CANONICAL R15;
- TRAIL1 R15;
- CANONICAL R20;
- TRAIL1 R20.

The independent audit passed. It intentionally produced metric-specific leaders
rather than an automatic overall winner.

Historical 2024+ headline evidence:

- CANONICAL R15: CAGR 109.13%, Max DD -16.34%;
- TRAIL1 R15: CAGR 122.44%, Max DD -19.96%;
- CANONICAL R20: CAGR 160.44%, Max DD -21.27%;
- TRAIL1 R20: CAGR 182.14%, Max DD -25.88%.

The user explicitly selected **TRAIL1 N4 FULL R15**. That human decision, not an
automatic ranking rule, is the authority for Stage 7.

## Stage 7 Production Specification Freeze

Stage 7 is COMPLETE.

Production specification ID:

`PROD_STAGE7_46DB784378797C7FB04636892350AFF21006D71A31F2CED9D4B974EDA2DC36B8`

Sole active production identity:

`TRAIL1__N4_01__FULL__R15`

Frozen content:

- T3/H1;
- `USDRUBF + CNYRUBF + GLDRUBF + IMOEXF`;
- TRAIL1 only;
- FULL loading;
- R15 = 1.5% of current realized equity per new instrument position;
- maximum nominal simultaneous initial risk 6%;
- no session filter;
- one active position per instrument;
- no pyramiding;
- realized equity only for sizing.

`CANONICAL__N4_01__FULL__R15` is a stable historical reference only, never a
runtime fallback.

Forbidden runtime overlays:

- BE1;
- LOCK1_AFTER_2R;
- SESSION_10_21;
- ONE_BAR;
- EXIT_ON_OPPOSITE_REGIME;
- STRUCTURAL_STACK.

Stage 7 independent audit passed.

## Stage 8 robot / FINAM integration

Stage 8 is ACTIVE. It is implementation and operational validation of the exact
Stage 7 specification, not a new strategy-selection stage.

Current package: `TradingSystemLab/stage8_robot/`.

Accepted properties:

- fail-closed architecture;
- DRY_RUN, DEMO and REAL_READONLY modes;
- LIVE always rejected;
- frozen Stage 7 strategy parameters are not runtime-tunable;
- canonical reference cannot become a fallback;
- transactional SQLite/WAL state with idempotency;
- deterministic exit-before-entry same-timestamp ordering;
- separate broker, risk, market-data, reconciliation, state, logging and
  strategy components.

## Research-to-robot conformance

Historical replay is exact and deterministic:

- research-authority replay: 418/418 exact;
- independent production robot replay: 418/418 exact;
- zero timestamp, direction, price, state or R mismatches;
- repeated replay hashes match.

This proves historical conformance to the frozen Stage 7 identity; it does not
authorize live trading.

## FINAM REAL_READONLY binding

All four Stage 7 instruments are currently
`AUTHENTICATED_REAL_READONLY` in the committed production registry:

- USDRUBF → `USDRUBF@RTSX`, security ID 3447194;
- CNYRUBF → `CNYRUBF@RTSX`, security ID 3447192;
- GLDRUBF → `GLDRUBF@RTSX`, security ID 4454911;
- IMOEXF → `IMOEXF@RTSX`, security ID 4631091.

Bindings are account-specific read-only evidence. No real order was transmitted.

Perpetual-futures semantics:

- automatic prolongation;
- quarterly exercise operator-only;
- quantity granularity one contract;
- FINAM REST representation is authoritative for runtime binding.

## Funding and margin boundary

FULL/R15 sizing code is margin-aware and uses FORTS available cash plus
directional initial margin. It fails closed on unknown/missing funding shapes.

The clean UNION account used during read-only validation did not expose
`portfolio_forts`; funding readiness is therefore currently
`BLOCKED_ACCOUNT_FINANCIALS_UNAVAILABLE`.

Do not invent cash, margin, equity or position capacity.

## Windows Intel deployment

Deployment support is prepared for Windows/Intel:

- instance lock;
- external state paths;
- bounded logs and heartbeat;
- online SQLite backup;
- restart reconciliation;
- CurrentUser DPAPI secret store;
- matched non-SYSTEM scheduled-task principal;
- ACL hardening;
- real Windows DPAPI execution tests.

Secrets remain outside Git.

## Stage 8.8 operational supervision

Stage 8.8.1 REAL_READONLY supervisor code is ready. It forces read-only mode,
entries disabled, account/data observation, instance locking and sanitized
heartbeat persistence.

Stage 8.8.4 added the Windows DPAPI credential bootstrap and real Windows
CurrentUser execution tests; later fixes hardened System.Security loading and
SID/ACL handling.

Stage 8.8.5 added schedule-aware stale H1 protection:

- external real timing evidence (kept outside Git) established whole-hour UTC opens;
- touching trading sessions form one instrument-specific contiguous grid;
- completion is `min(open + 1 hour, trading-window end)`;
- auction/clearing/closed preserve the transactional expected-H1 watermark;
- exact expected raw-open membership is required and cold start fails closed;
- malformed schedule fails closed;
- stale newest H1 candle raises `STALE_COMPLETED_H1_DATA`;
- heartbeat becomes `FAULT` / `UNHEALTHY`;
- cycle/watermark do not advance;
- no order-capable call is introduced.

Current Stage 8 status:

`STAGE_8_8_6_SQLITE_RECOVERY_CODE_READY_PENDING_INTEL_ACCEPTANCE`.

Real Intel stale-data acceptance passed against audited Git head
`1c1c2bb5458827f200bc753e7e64db0272b33a8f`; the external artifact SHA-256 is
`C57554AE3AE54018EC1E558108520088C1883718F0406E7B6C6669B4696A9CBC`.
The clean cycle was `HEALTHY` / `PASS`. The controlled
`STALE_COMPLETED_H1_DATA` fault was `UNHEALTHY` / `FAULT` and advanced neither
successful cycle count nor H1/expected-H1 state. Recovery returned `HEALTHY` /
`PASS` and reset consecutive failures to 0. Order-capable calls were 0, entries
remained disabled, and the production Scheduled Task remained Disabled. The
runtime artifact and real FINAM responses remain outside Git.

## Live-trading boundary

LIVE trading is not authorized and is not implemented as an enabled path.

`FinamRealReadOnlyBroker.submit_order` rejects transmission with
`REAL_ORDER_TRANSMISSION_NOT_AUTHORIZED`.

Current operational blockers / pending gates:

- Stage 8.8.6 physical Intel backup / recovery / reconciliation acceptance
  (repository code ready; acceptance pending);
- Stage 8.9 funding readiness blocked by unavailable account financials;
- Stage 8.10 trading-token integration pending;
- Stage 8.11/8.12 execution unauthorized.

Any live-order capability requires explicit separate authorization and audit.

## Domain boundaries

Do not mix TradingSystemLab with BBW, Level Touch, Round Level / Touch or other
research domains.

## Persistent-memory read order

1. `CURRENT_STATE.md`
2. `PROJECT_CONTEXT.md`
3. `METHODOLOGY.md`
4. `ROADMAP.md`
5. `AUDIT_PROTOCOL.md`

Update persistent memory only after accepted repository work and actual artifact
audit.
