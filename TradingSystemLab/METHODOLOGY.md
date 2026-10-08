# Canonical research, production, and operational methodology

This file defines durable TradingSystemLab rules. Historical research identities
and verdicts remain immutable. Production operation must preserve the exact Stage 7
identity and fail closed whenever required authority or safety evidence is missing.

## 1. Canonical research lifecycle

**Baseline → Optimization → Robustness → Walk Forward → TRUE OOS**.

Candidate freeze is identity fixation, not an additional research phase.
v1/v2/v3 research verdicts and consumed TRUE OOS evidence remain immutable.

## 2. Causality and deterministic identity

- no look-ahead or future fill;
- completed bars/context only;
- deterministic signal, entry, stop and trailing semantics;
- deterministic event ordering, state transitions and idempotent intent identity;
- strategy/source/parameter/universe/timeframe/risk identity may not drift at runtime.

## 3. Frozen production specification

Production specification:
`PROD_STAGE7_46DB784378797C7FB04636892350AFF21006D71A31F2CED9D4B974EDA2DC36B8`.

Active production identity:
`TRAIL1__N4_01__FULL__R15`.

Frozen semantics:

- v3 perpetual / T3 / H1;
- N4 = `USDRUBF`, `CNYRUBF`, `GLDRUBF`, `IMOEXF`;
- TRAIL1 only;
- FULL load;
- R15 = 1.5% of current realized equity per new instrument position;
- maximum nominal simultaneous initial risk = 6%;
- realized equity only; unrealized PnL excluded;
- one active position per instrument;
- no pyramiding;
- no session-entry filter;
- no automatic canonical fallback.

Stage 8 implements this specification; it does not reopen strategy selection,
portfolio selection, optimization, or research methodology.

## 4. Research-to-robot conformance

Historical authority and production replay reproduce 418/418 trades exactly and
deterministically with zero timestamp/direction/price/state/R mismatch classes.

This establishes implementation fidelity, not permission to trade.

## 5. Stage 8.8 operational hardening

Stage 8.8 operational hardening is complete. Its accepted controls remain active
production safety foundations:

- CurrentUser DPAPI credential protection;
- principal/SID and ACL binding;
- instance locking;
- heartbeat/reconciliation continuity;
- schedule-aware completed-H1 freshness;
- stale-data fail-closed handling and recovery;
- SQLite WAL-safe backup/recovery;
- physical Intel operational acceptance.

These controls remain applicable after LIVE activation.

## 6. Stage 8.9 funding and margin authority

Stage 8.9 is complete under
`STAGE_8_9_REAL_ACCOUNT_FUNDING_MARGIN_VALIDATION_COMPLETE`.

The production account is UNION and uses exactly one authenticated `portfolio_mc`
financial authority. Funding/margin logic is account-type aware and fails closed
on missing, malformed or mismatched financial shapes.

Stage 8.9 proved authenticated equity/margin authority and positive contract
capacity in at least some N4-direction cases. It did not alter Stage 7 R15 risk.

Production quantity is always rounded downward and may only be reduced by margin,
lot and aggregate-risk constraints; those constraints may never increase frozen
risk merely to create a tradable quantity.

## 7. Stage 8.10 credential and safety authority

Stage 8.10 is complete under
`STAGE_8_10_TRADING_TOKEN_LIFECYCLE_COMPLETE`.

Trading Token 1 is stored separately from READ_ONLY credentials in Windows
CurrentUser DPAPI and is bound to the production/account identity.

Credential possession, provisioning or `readonly=false` session evidence alone
does not authorize an order. Order-path construction was first validated only
offline/synthetically; that historical dry validation is not broker acceptance.

The durable kill switch and execution authorization are separate authorities.

## 8. Stage 8.11 controlled real execution acceptance

Stage 8.11 is **COMPLETE / PASS**.

Canonical physical authority:

- attempt: `stage8.11.attempt7`;
- accepted code: `72a910e49b876cda99484a810e6f8a1b16ac0209`;
- evidence SHA-256:
  `704BFCC19B1A63F490192C0D8D0E4715BFECF77664296AFEF47E5B80FBF64B5F`;
- CNYRUBF@RTSX LONG quantity 1;
- one entry POST and one controlled flatten POST;
- entry fill/one-contract position/flatten proven;
- final position = 0;
- final active orders = 0;
- unresolved acceptance intents = 0;
- reconciliation = PASS.

Attempts 1–6 remain immutable failure/recovery provenance and are not reclassified.

### Position-authoritative reconciliation rule

For synchronous Stage 8.11/production risk authority after a physical POST, the
exact `/account` position is authoritative. Normal reconciliation does not require
`/trades`, exact order-detail, executed-quantity, remaining-quantity, or the former
order-status state machine to agree synchronously.

Supplementary broker views may aid diagnostics but may not override exact account
position authority or weaken fail-closed unresolved-intent handling.

## 9. Stage 8.12 production runtime assembly

Stage 8.12.1–8.12.3 are complete/pass and established the production runtime,
end-to-end failure/conformance contracts, and Intel preflight.

Production runtime requirements include:

- exact frozen Stage 7 identity;
- frozen N4 bindings/economics;
- FULL/R15 plus authenticated margin sizing;
- aggregate 6% nominal initial-risk cap;
- durable order intents and restart-idempotent state;
- broker/account reconciliation;
- percentage-of-current-position protective stops;
- TRAIL1 tighter-stop replacement semantics;
- emergency risk-reducing exit;
- missed completed-H1 bars replayed sequentially;
- entry candle excluded from managing its own newly created position;
- realized-equity authority: `equity - unrealized_profit - explained_external_cash_flows`.

## 10. Production H1 data authority

Official FINAM H1 history alone is too shallow for the frozen T3 warm-up.
Production history therefore uses a two-layer authority:

1. immutable Stage 5 `forever` H1 seed from data commit
   `50f1fd2178c18b7ab3bd969be82ad01f47a34745`;
2. append-only validated completed FINAM H1 continuation stored in the production
   state database with integrity digest.

FINAM overlap may omit authority-only historical timestamps, but every FINAM
overlap timestamp must already exist in Stage-5/persisted authority with exact
OHLC and an exact overlap seam.

Fail closed on FINAM-only overlap timestamps, OHLC disagreement, missing seam,
no overlap, continuation corruption, duplicate/order invalidity, or downtime too
long to re-establish validated overlap.

Research source timestamps remain Moscow H1 open-times and are converted to the
frozen +1h close-time index only after exact authority validation.

## 11. Stage 8.12.4 durable production authorization

Stage 8.12.4 is **COMPLETE / LIVE PRODUCTION ACTIVATED**.
Canonical completion status:
`STAGE_8_12_FULL_R15_PRODUCTION_AUTHORIZATION_COMPLETE`.

Activation authority:

- accepted production commit: `883ea1ea6a8268276a8e39ebdc8786c643a21935`;
- Package 5 readiness evidence SHA-256:
  `FE383E9D269F699639D0F256CB15A303E0A5EE9CBC3990F802E10DCE8A41B7CD`;
- activation evidence SHA-256:
  `EA14B73FA1AE1D62C2324A0C76624DA792101FCD945383D70B646BDA1D6F8CB9`;
- durable authorization status: `AUTHORIZED`;
- `execution_authorized = true`;
- production kill switch: `ARMED`;
- production Scheduled Task: `Running`;
- readonly Scheduled Task: `Disabled`.

Authorization is repository-external, create-only and bound to exact production
commit, sanitized account identity, production specification/identity, and
accepted prerequisite evidence. It requires the explicit operator authorization
boundary; code import or credential possession may never create authorization.

## 12. Live entry gate

A new real entry may be submitted only when all required production authorities
are simultaneously valid, including:

- durable production authorization = `AUTHORIZED`;
- exact Stage 7 production identity/account/instrument bindings;
- kill switch = `ARMED`;
- `execution_authorized = true`;
- fresh production heartbeat = `HEALTHY`;
- reconciliation = `PASS`;
- no unresolved conflicting intent/order state;
- current FINAM session/schedule/tradability authority;
- completed/non-stale H1 authority;
- one-position-per-instrument and no-pyramiding constraints;
- R15/margin/lot and aggregate-risk gates.

A failed pre-submit gate blocks the new entry. Ambiguous POST outcomes remain
unresolved and must be reconciled; they must never be blindly retried.

## 13. HALT and risk-reducing operations

`HALTED` blocks new entries. It is not a command to abandon an existing position.

After an authorized position exists, protective-stop installation/replacement and
emergency risk-reducing exit remain available even if the kill switch subsequently
HALTs new entries. Risk-reducing operations must preserve durable intent and
uncertain-submission reconciliation semantics.

## 14. Scheduled-task topology

The production and historical readonly tasks are separate authorities.

Current accepted activation state:

- `TradingSystemLab-Stage8-Production` = `Running`;
- `TradingSystemLab-Stage8-Readonly` = `Disabled`.

The production launcher/task must remain bound to the accepted production commit
and expected Windows principal. Runtime code must not silently follow arbitrary
repository HEAD.

## 15. Post-arm acceptance and current operation

Stage 8.12.4 activation completed without a forced trade.

Accepted post-arm state:

- heartbeat after ARMED transition = true;
- heartbeat = `HEALTHY`;
- reconciliation = `PASS`;
- unresolved intents = 0;
- open positions = 0;
- active protective stops = 0;
- production cycle count = 15.

Current lifecycle state is continuous production operation / monitoring.
A future real order must arise only from a genuine frozen T3/H1 production signal.

## 16. Operational monitoring and recovery

Continuous production must preserve heartbeat/reconciliation freshness, exact H1
continuation integrity, exact account-position authority, durable intent
idempotency, protective-stop coverage for production-owned positions, funding/
margin and aggregate-risk authority, authorization/account/commit binding, and
kill-switch operator control.

Any safety uncertainty must fail closed for new entries. Recovery must reconcile
durable local authority to broker state before normal progression resumes.

## 17. Research and domain separation

Production activation does not reopen research. Do not alter strategy parameters,
portfolio, lifecycle conclusions or consumed OOS evidence because of live results
without a separately authorized research identity/process.

TradingSystemLab remains separate from BBW, Level Touch, Round Level / Touch and
other research domains.

## 18. Evidence standard

Use actual source/config/manifests/replay/audits and external-evidence hashes
according to `AUDIT_PROTOCOL.md`. Runtime secrets, raw account identity, financial
values and DPAPI material remain outside Git.

`CURRENT_STATE.md` and `ROADMAP.md` define the current operational handoff;
`PROJECT_CONTEXT.md` preserves stable project context.
