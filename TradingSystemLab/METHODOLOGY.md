# Canonical research and evidence methodology

This file defines the methodological rules that must survive across chats and
future implementation work. It does not redefine accepted historical results.

## 1. Canonical research lifecycle

The sole research template remains the original H1 cycle:

**Baseline → Optimization → Robustness → Walk Forward → TRUE OOS**.

Every new research identity must pass the applicable stages independently.
Candidate freeze is procedural identity fixation between Optimization and
Robustness; it is not a sixth research phase.

Do not add, skip, borrow, or silently substitute lifecycle stages. Later
timeframe/MTF implementations are historical evidence, not alternative
methodological authorities.

## 2. Research identity and immutability

A research identity binds at minimum:

- strategy source/hash;
- full parameters/hash;
- instrument universe;
- timeframe/context alignment;
- development/OOS bounds;
- execution/cost assumptions;
- classification rules.

After candidate freeze, the identity is immutable through Robustness, Walk
Forward, and TRUE OOS. A later parameter or logic change creates a new identity
and cannot inherit untouched-OOS status from the old one.

v1, v2 and v3 are separate historical generations and must not be conflated.

## 3. Baseline

Purpose: establish an auditable causal reference for a frozen strategy/config.

Permitted:
- causal strategy execution on declared Development data;
- descriptive metrics and grouped reports;
- deterministic provenance/hashing.

Prohibited:
- parameter search;
- ranking/selection;
- Walk Forward inference;
- TRUE OOS access;
- silent strategy mutation.

The corrected historical v2 Baseline and the independent v3 Baseline are both
accepted historical evidence. Earlier failed/superseded v2 attempts remain
provenance only and must not be described as the current state.

## 4. Optimization

Purpose: test only a predeclared bounded parameter space on Development data and
describe stable regions.

Optimization is not PF chasing. Complete trial populations must be preserved.
The original H1 classification concepts such as `ROBUST_PLATEAU`, `LOCAL_SPIKE`
and `NO_EDGE` remain the methodological reference where applicable.

TRUE OOS remains prohibited during Optimization.

## 5. Candidate freeze

After Development evaluation and before validation/OOS, select/fix the exact
candidate identity using the predeclared contract. The registry is a provenance
record, not a ranking table.

Once frozen, a weak later result does not permit return to the inventory for a
replacement candidate under the same research identity.

## 6. Robustness

Purpose: challenge the frozen candidate against the predeclared neighborhood,
costs, instruments, directions, years, concentration, and execution assumptions.

Robustness may diagnose weakness but may not retune or replace the candidate.

## 7. Walk Forward

Purpose: measure chronological forward behavior using predeclared folds and a
frozen candidate.

Forward-fold outcomes may not be used to alter parameters, choose favorable
folds, or access TRUE OOS early.

## 8. TRUE OOS

Purpose: one preauthorized evaluation of the frozen identity on the locked OOS
period.

TRUE OOS cannot be used for discovery, optimization, ranking, replacement or
post-hoc retuning. Once revealed, it is consumed for that identity.

For v3 Perpetual the lifecycle is complete. Final TRUE OOS classifications are
T2/M30 `BORDERLINE`, T2/H1 `BORDERLINE`, T3/M30 `PASS`, T3/H1 `PASS`.

## 9. Causality and deterministic execution

- Candle information is unavailable before close.
- Higher-timeframe/context data must use fully closed source bars only.
- No future-fill or look-ahead is allowed.
- T3 context construction must respect the declared completed-bar/day-boundary
  semantics of its generation.
- Ordering, trade IDs, serialization and reruns must be deterministic.
- Market data remains external/read-only unless an explicit task says otherwise.

## 10. Research costs and economic authority

`FROZEN_TICK_SIZE = 0.001` is the normalized research tick used by the accepted
v2/v3 research contracts where specified. It is not automatically the final
live production cost model.

Post-v3 Stage 5 and Stage 6 use the corrected economic authority
`CORRECTED_SINGLE_C1` for R-derived production-decision evidence. Historical
lifecycle classifications are preserved; corrected accounting does not
retroactively reclassify v1/v2/v3.

The final production cost model remains **NOT YET FROZEN** and belongs to
Stage 7 Production Specification Freeze.

## 11. Post-v3 program is not a new research lifecycle

After the v3 five-stage lifecycle closed, the project entered a separate
evidence-to-production program:

1. Master v1/v2/v3 evidence consolidation;
2. Portfolio/diversification comparison;
3. Trade Anatomy / Failure Analysis;
4. Structural hypothesis freeze;
5. Separate structural validation;
6. Production Assembly Decision;
7. Production Specification Freeze;
8. Trading robot / FINAM API integration.

These stages do not retroactively add phases to v1/v2/v3 and cannot rewrite
their research identities or OOS verdicts.

## 12. Structural hypothesis discipline

Structural execution/risk overlays are separate from signal-alpha changes.
Hypotheses must be small, explicit and predeclared before causal validation.
No broad grid, optimizer, ranking search, mass hypothesis generation, or
favorable-bucket filtering is allowed.

Stage 4 admitted exactly three causal structural hypotheses:

- BE1 profit protection;
- TRAIL1 delayed/conditional trailing structure;
- Total Open Risk Cap.

Minimum Hold, Session restriction and Correlation/Simultaneous-Risk grouping
were not admitted as causal hypotheses; later diagnostics did not convert them
into production rules.

## 13. Stage 5 evidence semantics

Final Stage 5 authority:

- BE1 — `MIXED_RETROSPECTIVE_EVIDENCE`;
- TRAIL1 — `SUPPORTED_RETROSPECTIVELY`;
- Total Open Risk Cap — `FORMAL_RESEARCH_VERDICT_NOT_ASSIGNED` because terminal
  right-censoring prevents complete economic certification;
- Minimum Hold — `NOT_ADMITTED / DIAGNOSTIC ONLY`;
- Session/Time of Day — `NOT_ADMITTED / DIAGNOSTIC ONLY`;
- Correlation/Simultaneous Risk — `NOT_ADMITTED / DIAGNOSTIC ONLY`.

Retrospective support is not fresh untouched OOS. Diagnostic slicing is not
permission to delete losses, cherry-pick hours, or manufacture a causal rule.

## 14. Stage 6 production-decision semantics

Stage 6 is an artifact-only decision over accepted evidence. It must not run a
new backtest, optimizer, parameter search, subset search or new hypothesis.

The accepted assembly is `PROD_STAGE6_83C7B31BB42C`: v3 perpetual / T3 / H1 /
`CNYRUBF`, `GLDRUBF`, `IMOEXF` / TRAIL1.

Selection must be understood under the full evidence set, including
profitability, drawdown, recovery, calendar-month stability, diversification,
direction stability, concentration, WF/OOS durability and execution practicality.
PF alone is never sufficient.

TRAIL1 does not dominate the canonical exit on every risk metric; explicit
historical OOS counter-evidence must remain visible.

## 15. Stage 7 boundary

Stage 6 selected an assembly, not a complete production specification.

Stage 7 must freeze:

- exact implementation/source identity;
- live-contract mapping and roll;
- risk allocation and sizing;
- portfolio safeguards;
- production costs;
- operating session/schedule;
- broker/order semantics;
- data-feed conventions;
- operational/recovery safeguards.

Do not implement the robot or FINAM integration before this freeze.

## 16. Domain separation

TradingSystemLab is separate from BBW, Level Touch, Round Level / Touch
Optimization, and other research domains. Do not copy their artifacts,
hypotheses or methodology into this project.

## 17. Evidence and audit standard

Reports summarize evidence; they do not replace it. Accepted claims must be
grounded in actual code/config/manifests/ledgers/metrics or other applicable
artifacts according to `AUDIT_PROTOCOL.md`.

After every accepted task or major audit, update `CURRENT_STATE.md` and
`ROADMAP.md`; update this methodology file only when the governing process or a
stale methodological statement itself needs correction.
