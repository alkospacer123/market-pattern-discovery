# Canonical research, production, and operational methodology

This file defines durable TradingSystemLab rules. It must preserve historical
research identities while governing production specification and robot
implementation.

## 1. Canonical research lifecycle

The sole research lifecycle remains:

**Baseline → Optimization → Robustness → Walk Forward → TRUE OOS**.

Candidate freeze is procedural identity fixation, not a sixth phase.

## 2. Historical identity and OOS discipline

A research identity binds strategy source/hash, parameters/hash, universe,
timeframe/context alignment, date bounds, execution/cost assumptions and
classification rules.

After candidate freeze the identity is immutable through Robustness, Walk
Forward and TRUE OOS. Once TRUE OOS is revealed it is consumed. Post-OOS
diagnostics are retrospective and cannot become fresh OOS by renaming.

v1/v2/v3 verdicts remain immutable.

## 3. Causality and determinism

- no look-ahead or future fill;
- context uses completed bars only;
- signal/entry/stop/trailing semantics are deterministic;
- ordering, trade IDs, serialization and reruns are deterministic;
- source data remain external/read-only unless explicitly authorized otherwise.

## 4. Post-v3 evidence program

Stages 1–5 are historical evidence-to-production analysis and do not rewrite
the v3 lifecycle. Stage 5 authoritative retrospective economic contract is
`CORRECTED_SINGLE_C1`.

Stage 5 final labels remain:

- BE1 `MIXED_RETROSPECTIVE_EVIDENCE`;
- TRAIL1 `SUPPORTED_RETROSPECTIVELY`;
- Risk Cap `FORMAL_RESEARCH_VERDICT_NOT_ASSIGNED`;
- Minimum Hold / Session / Correlation diagnostic-only at Stage 5.

## 5. Stage 6.x retrospective reassessment

Stage 6.1–6.7 used revealed historical evidence. It was not a second OOS
lifecycle.

Structural results:

- SESSION_10_21 admitted to structural stack;
- ONE_BAR confirmation rejected;
- opposite-regime exit not admitted;
- LOCK1_AFTER_2R admitted;
- `STRUCTURAL_STACK_V1 = SESSION_10_21 + LOCK1_AFTER_2R` admitted.

Stage 6.6 compared a frozen set of five authenticated variants across eleven
fixed baskets; it did not authorize open-ended subset search.

Stage 6.7 broad loading/equity analysis used frozen eligibility rules. Its
`NO_CURRENT_CONFIGURATION_MEETS_FULL_PRODUCTION_OBJECTIVE` conclusion remains
historical evidence and must not be rewritten.

## 6. Focused N4 four-case decision evidence

After Stage 6.7 broad closeout, a separately authorized fixed four-case N4 FULL
comparison examined only CANONICAL/TRAIL1 × R15/R20.

Rules:

- no new parameter search;
- no automatic overall winner;
- 2025–2026 remain revealed historical evidence;
- metric-specific leaders remain separate;
- human production selection is allowed only as an explicit decision over the
  frozen four-case evidence.

The user explicitly selected `TRAIL1__N4_01__FULL__R15`.

That explicit decision is the Stage 7 authority. It must not be reinterpreted
as proof that the earlier broad Stage 6.7 gate was automatically satisfied.

## 7. Stage 7 Production Specification Freeze

Stage 7 freezes one production identity:

`PROD_STAGE7_46DB784378797C7FB04636892350AFF21006D71A31F2CED9D4B974EDA2DC36B8`

Active identity:

`TRAIL1__N4_01__FULL__R15`.

Frozen production semantics:

- v3 perpetual / T3 / H1;
- N4: USDRUBF, CNYRUBF, GLDRUBF, IMOEXF;
- TRAIL1 only;
- FULL load;
- 1.5% current realized-equity risk per new instrument position;
- 6% maximum nominal simultaneous initial risk;
- one active position per instrument;
- no pyramiding;
- no session entry filter;
- no automatic canonical fallback;
- realized equity excludes unrealized PnL.

`CANONICAL__N4_01__FULL__R15` is reference evidence only.

Forbidden production overlays unless a new explicitly authorized specification
is created:

- BE1;
- LOCK1_AFTER_2R;
- SESSION_10_21;
- ONE_BAR;
- EXIT_ON_OPPOSITE_REGIME;
- STRUCTURAL_STACK.

## 8. Research-to-robot conformance

Stage 8 implementation must reproduce the frozen Stage 7 identity before any
broker activation.

Required conformance evidence:

- exact trade count;
- timestamp/direction/price/state/R reconciliation;
- deterministic repeated replay;
- no runtime parameter override;
- no alternative production identity/fallback.

Current accepted evidence reproduces **418/418 trades exactly** in both
research-authority replay and independent production robot replay.

## 9. Fail-closed Stage 8 architecture

Production code must default to safety:

- LIVE is disabled and cannot be enabled by a casual environment toggle;
- REAL_READONLY cannot transmit orders;
- unresolved instrument binding blocks progression;
- reconciliation failures block entries;
- stale/invalid market data blocks entries;
- missing funding/margin evidence blocks sizing;
- unknown REST schemas fail closed;
- duplicate intents/orders are prevented by persisted idempotency.

Order intent is persisted before submission. Exit/fee realization precedes
later same-timestamp entry sizing.

## 10. Cost and sizing separation

`FROZEN_TICK_SIZE = 0.001` and C1 are historical research-normalization/evidence
contracts. They are not automatically the live fee/slippage model.

Stage 7 FULL/R15 sizing uses 1.5% of current realized equity per new position.
Stage 8 may cap quantity by authenticated available cash and directional initial
margin, but may not increase frozen risk.

Unknown funding values never permit fabricated sizing.

## 11. FINAM binding semantics

Runtime FINAM binding uses authenticated REST evidence.

Current N4 registry is 4/4 `AUTHENTICATED_REAL_READONLY`.

Important rules:

- REST wire shapes are authoritative for the REST client;
- protobuf/gRPC shapes are not accepted as REST evidence;
- futures order quantity is contracts and must respect `trade_lot_size`;
- contract size is underlying-per-contract, not order-lot count;
- price step is derived exactly from FINAM decimals/min_step semantics;
- account-specific binding and generic catalog discovery remain distinct.

Binding authentication does not equal funding readiness or live-trading
authorization.

## 12. Credential and deployment methodology

Secrets never enter Git, process arguments or logs.

Windows production-readonly credentials use DPAPI `CurrentUser`, bound to the
frozen production ID and the matched non-SYSTEM scheduled-task principal.

Credential storage must fail closed on:

- tampering;
- wrong production ID;
- wrong SID/principal;
- invalid ACL/security setup;
- unavailable DPAPI support.

Real Windows execution tests are required in addition to static code checks.

## 13. Operational supervisor methodology

REAL_READONLY supervisor:

- forces REAL_READONLY mode;
- keeps entries disabled;
- holds a lifetime instance lock;
- reconciles state/account/data;
- writes sanitized heartbeat/continuity only;
- never transmits real orders.

Repository tests are not substitutes for physical Intel 24/7/restart/network
acceptance.

## 14. Schedule-aware stale H1 protection

Freshness must be derived from the broker-reported instrument schedule rather
than wall-clock assumptions.

Only a completed one-hour interval wholly contained inside an authenticated
trading session creates an expected H1 close.

Do not synthesize expected bars across:

- closed weekends;
- empty schedules;
- future sessions;
- sub-hour intervals;
- schedule gaps.

Malformed schedule evidence fails closed.

If newest completed H1 data is older than the expected close:

- raise `STALE_COMPLETED_H1_DATA`;
- mark heartbeat `FAULT` / `UNHEALTHY`;
- do not increment successful cycle count;
- do not advance watermark/state as a successful cycle;
- keep entries disabled;
- do not call order-capable paths.

Recovery must clear the fault only after fresh authenticated data are observed.

## 15. Current operational gate

Stage 8.8.5 code/repository audit readiness does **not** equal operational
acceptance.

Before any further authorization, real Intel validation must exercise at least
restart, network failure/recovery, stale-data fault injection and recovery under
REAL_READONLY with entries disabled.

Funding readiness remains separately blocked while required account financials
are unavailable.

## 16. Live authorization boundary

LIVE trading is currently unauthorized.

Any future order-capable real mode requires:

- explicit user authorization;
- authenticated funding/account semantics;
- a separately audited trading credential/token path;
- completed operational acceptance;
- documented rollback/kill/reconciliation behavior.

Do not infer live authorization from code readiness, demo readiness, registry
binding, or REAL_READONLY success.

## 17. Domain separation

TradingSystemLab remains separate from BBW, Level Touch, Round Level / Touch and
other projects.

## 18. Evidence standard

Use actual source/config/manifests/ledgers/metrics/replay/audit evidence according
to `AUDIT_PROTOCOL.md`. Summary prose alone is not evidence.

Routine progress updates belong primarily in `CURRENT_STATE.md` and
`ROADMAP.md`.
