# TradingSystemLab project context

## Purpose and authority

TradingSystemLab is the deterministic, fixed-risk research and production-design
domain for the repository's systematic trading work. It preserves complete
research provenance from v1, v2, and v3 and now carries the accepted post-v3
production program through Production Specification Freeze and later robot/API
implementation.

The repository, not chat history, is the authoritative persistent memory.
`CURRENT_STATE.md` is the first handoff file to read.

## Canonical research methodology

The sole methodological authority for new research identities remains the
original H1 lifecycle:

**Baseline → Optimization → Robustness → Walk Forward → TRUE OOS**.

Candidate freeze is procedural identity fixation between Optimization and
Robustness, not an additional research phase. Later timeframe or MTF work is
historical evidence, not a substitute methodology.

Signals must remain causal, deterministic, provenance-bound and separated from
TRUE OOS. A logic/parameter change after OOS creates a new identity; historical
verdicts may not be rewritten.

## Research generations

### v1

Broad strategy/timeframe discovery on perpetual futures. It includes T1–T3 and
R1–R3 work across multiple timeframes and later MTF research. v1 is historical
evidence only.

### v2

Quarterly-futures diversification generation using T2/T3 on M30/H1 across
`Si`, `CNY`, `GD`, `BR`, `MIX`, `NG`. Its five-stage cycle is complete. Final
TRUE OOS classifications for T2/M30, T2/H1, T3/M30, and T3/H1 are all
`BORDERLINE`. Its TRUE OOS is consumed and cannot be reused as untouched OOS.

### v3 Perpetual

Independent stability replication on perpetual futures:

- instruments: `USDRUBF`, `CNYRUBF`, `GLDRUBF`, `IMOEXF`;
- strategies: T2/T3;
- timeframes: M30/H1;
- development: 2023-01-01 through 2024-12-31, with natural later starts where
  applicable;
- research tick: `0.001`;
- cost accounting: C1 under the frozen research contract.

v3 completed the full five-stage lifecycle. Final TRUE OOS outcomes are:

- T2/M30 `BORDERLINE`;
- T2/H1 `BORDERLINE`;
- T3/M30 `PASS`;
- T3/H1 `PASS`.

The reproducible v3 Phase 5 closeout merge is
`aab2659cfc91846631bbe22ff3b45e3e4e4af85f`. v3 TRUE OOS is consumed.

## Frozen v3 candidate identities

The accepted v3 Candidate Freeze preserved one immutable identity per study:

- T2/M30 — `T2_M30_candidate_v3`, configuration `T2-M30-608dc87d09f1`;
- T2/H1 — `T2_H1_candidate_v3`, configuration `T2-H1-608dc87d09f1`;
- T3/M30 — `T3_M30_candidate_v3`, configuration `T3-M30-d6feb972db57`;
- T3/H1 — `T3_H1_candidate_v3`, configuration `T3-H1-4e73cdb77246`.

Frozen strategy source hashes:

- T2: `376df085cfda85eefccb31343aad40ed4fbb1078f1314496472a3a4ac9507774`;
- T3: `840dd3b2cda43fa00259445cd0a22ace6d82e677f4c793028ccc8126f9ad9a8c`.

## Post-v3 production program

Completion of v3 did not retroactively add stages to the research lifecycle.
Instead, the project entered a separate evidence-to-production program defined
in `ROADMAP.md`.

Accepted status:

- Stage 1 Master v1/v2/v3 evidence consolidation — CLOSED;
- Stage 2 Portfolio/diversification comparison — CLOSED;
- Stage 3 Trade Anatomy / Failure Analysis — CLOSED;
- Stage 4 Structural hypothesis set — CLOSED;
- Stage 5 Separate structural validation — CLOSED;
- Stage 6 Production Assembly Decision — CLOSED;
- Stage 7 Production Specification Freeze — NEXT;
- Stage 8 Trading robot / FINAM API integration — FUTURE.

Stages 1–6 are evidence/production-design work and do not alter historical
v1/v2/v3 research identities.

## Stage 5 structural-validation authority

Stage 5 uses the corrected economic authority `CORRECTED_SINGLE_C1` over a
9,694-trade canonical comparator. The final closeout states:

- BE1: `MIXED_RETROSPECTIVE_EVIDENCE`;
- TRAIL1: `SUPPORTED_RETROSPECTIVELY`;
- Total Open Risk Cap: `FORMAL_RESEARCH_VERDICT_NOT_ASSIGNED` because terminal
  right-censoring prevents complete final economic certification;
- Minimum Hold: `NOT_ADMITTED / DIAGNOSTIC ONLY`;
- Session/Time of Day: `NOT_ADMITTED / DIAGNOSTIC ONLY`;
- Correlation/Simultaneous Risk grouping: `NOT_ADMITTED / DIAGNOSTIC ONLY`.

These labels must not be silently converted into stronger production claims.

## Stage 6 production assembly

Stage 6 independently certified the production-assembly decision:

**`PROD_STAGE6_83C7B31BB42C`**

- generation: v3;
- futures type: perpetual;
- strategy/timeframe: T3/H1;
- instruments: `CNYRUBF`, `GLDRUBF`, `IMOEXF`;
- structural overlay: TRAIL1;
- economic contract: `CORRECTED_SINGLE_C1`;
- research tick: `0.001`.

Final Stage 6 corrected-authority merge:
`3687b65d591659f91ae9ecf8c93f775c3b10a44c`.

Stage 6 did not run a new backtest, optimizer, parameter search, subset search,
or new hypothesis. It selected an assembly from accepted evidence. TRAIL1
support is parent-level retrospective causal evidence; there is no exact
three-instrument TRAIL1 basket backtest.

## Current boundary

The Stage 6 assembly is selected but is **not yet a frozen production
specification**. Stage 7 must freeze implementation identity, live-contract
mapping/roll, risk allocation, position sizing, safeguards, production costs,
session operating schedule, broker/order semantics, data-feed conventions, and
operational recovery rules before implementation.

Robot or FINAM API implementation must not start from an unfrozen specification.

## Evaluation and evidence contract

- R-based metrics, costs and lifecycle labels must be tied to their exact
  generation and economic authority.
- PF is evidence, not a standalone ranking objective.
- Reports do not substitute for ledgers/manifests/source provenance.
- Post-OOS diagnostics are retrospective unless separately validated.
- Production decisions must use profitability, drawdown, recovery, calendar-month
  stability, diversification, direction stability, concentration, WF/OOS
  durability, execution practicality and risk together.
- Cross-generation comparisons must preserve unlike universes/data constructions
  rather than pooling them as one sample.

## Domain boundaries

TradingSystemLab must not be mixed with BBW, Level Touch, Round Level / Touch
Optimization, or other research domains. Their artifacts, hypotheses and
methodology are not interchangeable.

## Persistent-memory files

Read in this order:

1. `CURRENT_STATE.md` — exact active handoff;
2. `PROJECT_CONTEXT.md` — stable project architecture and accepted history;
3. `METHODOLOGY.md` — research/evidence rules;
4. `ROADMAP.md` — ordered next work;
5. `AUDIT_PROTOCOL.md` — evidence standard.

Update stable context only after accepted work and actual repository audit.
