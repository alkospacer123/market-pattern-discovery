# Evidence-based roadmap

## Governing rule

The original H1 research lifecycle remains the sole methodology for research
identities:

**Baseline → Optimization → Robustness → Walk Forward → TRUE OOS**.

That lifecycle is complete for v3 Perpetual. The current roadmap is therefore
the separate post-v3 evidence-to-production program below. It must not be used
to rewrite v1/v2/v3 identities or add retroactive research phases.

## Historical research generations

### v1 — historical

Broad strategy/timeframe discovery, including T1–T3, R1–R3, multiple
timeframes and later MTF research. v1 remains immutable historical evidence.

### v2 — historical and complete

Quarterly-futures diversification generation using T2/T3 on M30/H1 across
`Si`, `CNY`, `GD`, `BR`, `MIX`, `NG`. Its five-stage cycle is complete and all
four final TRUE OOS study classifications are `BORDERLINE`. Its OOS is consumed.

### v3 Perpetual — historical and complete

Universe: `USDRUBF`, `CNYRUBF`, `GLDRUBF`, `IMOEXF`; strategies T2/T3;
timeframes M30/H1.

v3 completed Baseline, Optimization, Candidate Freeze, Robustness, Walk Forward
and TRUE OOS. Final TRUE OOS outcomes:

- T2/M30 `BORDERLINE`;
- T2/H1 `BORDERLINE`;
- T3/M30 `PASS`;
- T3/H1 `PASS`.

Canonical reproducible v3 lifecycle closeout:
`aab2659cfc91846631bbe22ff3b45e3e4e4af85f`.

## Post-v3 objective

Turn the completed evidence into a defensible production assembly and then a
frozen implementation specification. The process must emphasize not only
profitability but also drawdown, recovery, calendar-month stability,
cross-instrument diversification, direction stability, concentration,
WF/OOS durability, execution practicality and portfolio risk.

Do not select from PF alone.

## Stage 1 — Master v1/v2/v3 evidence consolidation

**Status: CLOSED.**

Deterministic comparison evidence across research generations was built and
independently audited. Generation identity/comparability boundaries are
preserved; unlike samples are not pooled as one population.

Final independent closeout merge:
`05e2cdb30ba8ec341403583d37e02712d179a6a7`.

## Stage 2 — Portfolio/diversification comparison

**Status: CLOSED.**

Calendar/month and instrument contribution evidence, correlations, co-loss
statistics and leave-one-instrument-out diagnostics were built. Historical
availability semantics were subsequently corrected and frozen.

Final correction merge:
`c90e519f2fd4ee6720d9b0da0b1a11ac28cc0c05`.

## Stage 3 — Trade Anatomy / Failure Analysis

**Status: CLOSED.**

v1/v2/v3 trade populations were normalized with provenance, then analyzed by
strategy/timeframe, instrument, direction, entry time, holding profile, exit
reason, MAE/MFE, loss mechanics, giveback and other available dimensions.

Final independent closeout merge:
`244a5adac2baee3bb28d697efa25299b0a1973ef`.

## Stage 4 — Structural hypothesis set

**Status: CLOSED.**

Exactly three hypotheses were admitted for causal structural validation:

- H4_01 / BE1;
- H4_02 / TRAIL1;
- H4_03 / Total Open Risk Cap.

Minimum Hold, Session restriction and Correlated-risk grouping were not
admitted as causal hypotheses.

Freeze merge:
`1378cc2868095823655bab9eebbb8a2d01db9376`.

## Stage 5 — Separate structural validation

**Status: CLOSED.**

Final Stage 5 economic authority: `CORRECTED_SINGLE_C1`.

Final component statuses:

- BE1 — `MIXED_RETROSPECTIVE_EVIDENCE`;
- TRAIL1 — `SUPPORTED_RETROSPECTIVELY`;
- Total Open Risk Cap — `FORMAL_RESEARCH_VERDICT_NOT_ASSIGNED` because of
  terminal right-censoring;
- Minimum Hold — `NOT_ADMITTED / DIAGNOSTIC ONLY`;
- Session / Time of Day — `NOT_ADMITTED / DIAGNOSTIC ONLY`;
- Correlation / Simultaneous Risk — `NOT_ADMITTED / DIAGNOSTIC ONLY`.

The Stage 5 comparator authenticates 9,694 trades. Stage 5 closes the research
work without assigning a fabricated H4_03 verdict and without promoting
diagnostic-only rules.

Final independent closeout merge:
`fdee91b474ccdebcf9d7dc56d8e87a112d37e50e`.

## Stage 6 — Production Assembly Decision

**Status: CLOSED.**

Final decision:

**`PROD_STAGE6_83C7B31BB42C`**

- generation: v3;
- futures type: perpetual;
- strategy: T3;
- timeframe: H1;
- instruments: `CNYRUBF`, `GLDRUBF`, `IMOEXF`;
- structural overlay: TRAIL1;
- economic contract: `CORRECTED_SINGLE_C1`;
- research tick: `0.001`.

Stage 6 was artifact-only. No new backtest, optimizer, parameter search,
exhaustive subset search or new hypothesis was run.

The selected basket's monthly verification uses corrected single-C1 canonical
base exits. TRAIL1 support is parent-level retrospective causal evidence; an
exact three-instrument TRAIL1 basket backtest does not exist. TRAIL1 also does
not dominate the canonical exit on every risk metric.

Final corrected economic-authority merge:
`3687b65d591659f91ae9ecf8c93f775c3b10a44c`.

## Stage 7 — Production Specification Freeze

**Status: NEXT. Not executed.**

Stage 7 must consume the accepted Stage 6 assembly exactly and freeze the
operational identity before implementation.

Required freeze items include:

- exact strategy source/implementation identity;
- exact live-contract mapping;
- roll convention;
- risk allocation;
- position sizing;
- portfolio safeguards;
- production cost model;
- session operating schedule;
- broker/order semantics;
- data-feed conventions;
- operational/reconnect/recovery safeguards.

Stage 7 may specify implementation details, but it must not silently re-open
strategy selection, instrument subset selection, optimization, Stage 4
hypothesis discovery, or historical research verdicts.

## Stage 8 — Trading robot and FINAM API integration

**Status: FUTURE. Do not start before Stage 7 is accepted.**

Implementation must use only the frozen production specification. Required
operational topics include deterministic order/state handling, position/risk
reconciliation, reconnect/recovery behavior, logging/auditability and staged
non-live verification before live deployment.

## Post-v3 constraints

- Follow the ordered stages unless the user explicitly changes the roadmap.
- Do not mix TradingSystemLab with BBW, Level Touch, Round Level / Touch, or
  other projects.
- Do not treat diagnostics as permission to cherry-pick profitable buckets or
  remove losing trades.
- Do not treat post-OOS evidence as fresh OOS.
- Do not alter v1/v2/v3 historical identities or classifications.
- Do not promote Minimum Hold, Session, or correlation diagnostics into rules.
- Do not assign a formal H4_03 Risk Cap verdict while terminal censoring remains.
- Keep `CORRECTED_SINGLE_C1` as the current Stage 5/6 economic authority.
- Production cost and live execution conventions are Stage 7 decisions, not
  implied by the research tick.

## Current handoff

Stages 1–6 are CLOSED.

**Next permitted action: Stage 7 — Production Specification Freeze for
`PROD_STAGE6_83C7B31BB42C`.**
