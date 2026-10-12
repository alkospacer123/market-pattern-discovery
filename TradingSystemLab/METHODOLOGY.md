# Canonical research, production, and operational methodology

## 2026-10-12 re-arm operation — current LIVE authority (methodology unchanged)

Operator-approved re-arm `STAGE8_12_H1_REARM=PASS`, switch `ARMED` gen 60, entry gate `OPEN`, exact accepted fixed code `184e8c2b8fa092a606249ff293a4f507160bff29`. Subsequent read-only check 11:38:23 MSK confirmed LIVE production task Running, heartbeat `HEALTHY`, reconciliation `PASS`, cycle 9258, no local open positions/unresolved intents. Earlier H1 splice faults are historical; two commit mismatch warnings arose from an obsolete expected SHA in a separate read-only diagnostic. No change to frozen methodology, candidate, T3/H1/TRAIL1, N4, FULL/R15 or broker execution model.


## 2026-10-12 operational H1 backfill fix — LIVE restored HALTED (no methodology change)

Operator evidence: corrected production code exactly `184e8c2b8fa092a606249ff293a4f507160bff29` (PR #484), 114 regression tests PASS, N4 immutable H1 PASS; real LIVE production cycles 9213 and **9214** `HEALTHY/PASS`. Existing Windows Scheduled Task action was recovered with principal unchanged and now `RUNNING` at exact commit; commit-bound authorization migrated. Kill switch `HALTED` generation 59, entries closed, re-arm not done. Evidence SHA-256 `95d724dce03cedefd444de742d6f73fa3b6a0dbdecf0f8c6418e2149c8a0da43`. Previous incident and stopped task snapshots below are historical. Frozen research phases, T3/H1/TRAIL1/N4/FULL/R15 strategy and 6% initial risk limit remain immutable.


## 2026-10-12 production-readiness evidence (no methodological change)

Intel operator reports `READINESS_BACKUP=PASS` after corrected H1 shadow `HEALTHY/PASS`. Real broker positions/orders/unresolved intents `0/0/0`; kill switch `HALTED` generation 59; exact Stage5 and frozen T3/H1/TRAIL1/N4/R15 unchanged. Read-only online SQLite backup integrity PASS, external backup SHA-256 `6a8c2c7d1ef589ff0190b28624397962abb9583eccfa90bc4099a6f1681486fe`, external report SHA-256 `812ab73de05b896db7d4938b040d20bda49f8fc924a0e852a8c20de45516b644`. LIVE rollout/authorization migration/re-arm not done; LIVE heartbeat recovery unverified. This is an operational hold, not a new research phase or strategy change.


## 2026-10-12 H1 operational validation note — research methodology unchanged

On Intel, PR #484 H1 immutable splice passed 60/60 targeted code tests, 4/4 N4 real FINAM GET-only precheck (SHA-256 `2fe51ccd6ab57682579f222158b12413eaae6020abe21aec7afa188d3afddb43`) and isolated one-cycle production shadow preactivation on a SQLite backup copy (immutable H1 prefixes 4/4 PASS, shadow `HEALTHY/PASS`, SHA-256 `4799a0b426cd62d143a0b3fdba6035ef44f11dde6654676568b1a28e3a8fbded`). These are operator-reported; **LIVE heartbeat recovery, authorization rollover, re-arm and full test suite are not done**. LIVE remains `HALTED` generation 59 and pinned to historical commit. Research methodology, production strategy, Stage 7 portfolio, risk and broker execution semantics remain frozen.


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

FINAM overlap may omit authority-only historical timestamps. Once a completed
H1 bar has been accepted into Stage-5/persisted production authority, that
accepted OHLC is immutable production history. A later FINAM historical OHLC
revision for the same already-accepted timestamp must not rewrite authority and
must not by itself permanently block production liveness.

Fail closed on FINAM-only/unknown overlap timestamps, missing exact splice seam,
no overlap, continuation corruption, duplicate/order invalidity, stale current
H1, or downtime too long to re-establish validated overlap.

Research source timestamps remain Moscow H1 open-times and are converted to the
frozen +1h close-time index only after exact authority validation.

## 11. Stage 8.12.4 durable production authorization

Stage 8.12.4 is **COMPLETE / LIVE PRODUCTION ACTIVATED**.
Canonical completion status:
`STAGE_8_12_FULL_R15_PRODUCTION_AUTHORIZATION_COMPLETE`.

Activation authority:

- current accepted production commit: `4c7cd7cbbde5fbffb63ed6984cf89b90dc50d129`;
- original live-activation commit (historical provenance): `883ea1ea6a8268276a8e39ebdc8786c643a21935`;
- Package 5 readiness evidence SHA-256:
  `FE383E9D269F699639D0F256CB15A303E0A5EE9CBC3990F802E10DCE8A41B7CD`;
- activation evidence SHA-256:
  `EA14B73FA1AE1D62C2324A0C76624DA792101FCD945383D70B646BDA1D6F8CB9`;
- durable authorization status: `AUTHORIZED`;
- `execution_authorized = true`;
- production kill switch: `ARMED`;
- production Scheduled Task: `Running`;
- readonly Scheduled Task: `Disabled`.

Operational authority was rolled forward on 2026-10-08 by H1 hotfix PR #435.
Intel validation passed 15/15 targeted tests; re-authorization and explicit
re-arm completed on exact commit `4c7cd7cbbde5fbffb63ed6984cf89b90dc50d129`
with `HEALTHY / PASS`, zero unresolved intents, kill switch `ARMED`, production
task `Running`, and production entry gate `OPEN`. This changed only the
production H1 history boundary; frozen T3/TRAIL1/N4/FULL-R15/risk semantics did
not change.

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

## 19. Production H1 history liveness (operational safety clarification, 2026-10-12)

Stage5 seed and persisted completed-H1 continuation form immutable accepted production authority. A later FINAM response is an observation, not retrospective permission to insert bars or revise accepted OHLC. Ignore FINAM-only historical timestamps `<= authority.max()`; append only `> authority.max()` with the **exact latest authority seam present** in the validated FINAM response. Missing seam, no overlap, duplicates or invalid order, corrupted continuation, and stale current completed H1 fail closed. This operational data-integrity clarification does not alter canonical research methodology, frozen T3 signal calculation, risk sizing or execution. PR #484 (code merge `184e8c2b8fa092a606249ff293a4f507160bff29`) remains unaccepted physically on Intel; kill switch HALTED after the 2026-10-12 incident and separate re-arm permission required.
