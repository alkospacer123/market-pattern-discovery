# Current state — read first

## Authoritative handoff

The active TradingSystemLab work is now the **post-v3 production program**. The
v3 Perpetual five-stage research lifecycle is complete and immutable as historical
evidence. Post-v3 Stages 1–6 are also CLOSED. The next permitted action is
**Stage 7 — Production Specification Freeze**.

Latest accepted repository state used for this handoff:

- current `main`: `3687b65d591659f91ae9ecf8c93f775c3b10a44c`;
- v3 Phase 5 reproducible lifecycle closeout: `aab2659cfc91846631bbe22ff3b45e3e4e4af85f`;
- Stage 1 final independent closeout: `05e2cdb30ba8ec341403583d37e02712d179a6a7`;
- Stage 2 final availability-semantics correction: `c90e519f2fd4ee6720d9b0da0b1a11ac28cc0c05`;
- Stage 3 final independent closeout: `244a5adac2baee3bb28d697efa25299b0a1973ef`;
- Stage 4 structural hypothesis freeze: `1378cc2868095823655bab9eebbb8a2d01db9376`;
- Stage 5 final independently certified closeout: `fdee91b474ccdebcf9d7dc56d8e87a112d37e50e`;
- Stage 6 final corrected economic-authority merge: `3687b65d591659f91ae9ecf8c93f775c3b10a44c`.

## v3 Perpetual lifecycle — CLOSED

Universe: `USDRUBF`, `CNYRUBF`, `GLDRUBF`, `IMOEXF`; strategies T2/T3;
timeframes M30/H1. The original H1 lifecycle remained the governing template:

**Baseline → Optimization → Robustness → Walk Forward → TRUE OOS**.

Final v3 TRUE OOS classifications, in fixed study order:

- T2/M30 — `BORDERLINE`;
- T2/H1 — `BORDERLINE`;
- T3/M30 — `PASS`;
- T3/H1 — `PASS`.

TRUE OOS was consumed by the authorized v3 Phase 5 evaluation and is no longer
untouched evidence for those identities. No post-hoc parameter change may rewrite
the v3 lifecycle.

The frozen upstream T3/H1 candidate used by the selected post-v3 parent is
`T3_H1_candidate_v3` / `T3-H1-4e73cdb77246` with parameter hash
`4e73cdb77246cb07b5953160b9fc0ab36bfd4bd6d9a7f7faaae7e6e392ee340a`.

## Post-v3 program status

- **Stage 1 — Master v1/v2/v3 evidence consolidation: CLOSED.** Independent
  audit passed; deterministic cross-generation evidence tables are frozen.
- **Stage 2 — Portfolio/diversification comparison: CLOSED.** Portfolio and
  instrument/month evidence are frozen with corrected availability semantics.
- **Stage 3 — Trade Anatomy / Failure Analysis: CLOSED.** v1/v2/v3 normalized
  trade evidence, anatomy tables, failure mechanics, and independent closeout
  are frozen.
- **Stage 4 — Structural hypothesis set: CLOSED.** Exactly three hypotheses
  were admitted for causal validation: BE1, TRAIL1, and total-open-risk cap.
- **Stage 5 — Structural validation: CLOSED.** Final economic authority is
  `CORRECTED_SINGLE_C1`; 9,694 canonical comparator trades authenticate.
- **Stage 6 — Production Assembly Decision: CLOSED.** Final status
  `POST_V3_STAGE_6_PRODUCTION_ASSEMBLY_DECISION_COMPLETE`; independent audit
  `POST_V3_STAGE_6_PRODUCTION_ASSEMBLY_DECISION_AUDIT_PASSED`.
- **Stage 7 — Production Specification Freeze: NEXT.** Not executed yet.
- **Stage 8 — Trading robot / FINAM API integration: FUTURE.**

## Stage 5 final authority

The six-row Stage 5 closeout matrix is authoritative:

- BE1 / H4_01: `MIXED_RETROSPECTIVE_EVIDENCE`;
- TRAIL1 / H4_02: `SUPPORTED_RETROSPECTIVELY`;
- Total Open Risk Cap / H4_03: `FORMAL_RESEARCH_VERDICT_NOT_ASSIGNED` because
  final economic certification is right-censored by terminal open positions;
- Minimum Hold: `NOT_ADMITTED / DIAGNOSTIC ONLY`;
- Session / Time of Day: `NOT_ADMITTED / DIAGNOSTIC ONLY`;
- Correlation / Simultaneous Risk grouping: `NOT_ADMITTED / DIAGNOSTIC ONLY`.

No session rule, minimum-hold rule, correlation threshold, correlated-risk group,
or risk-cap production rule was admitted. TRAIL1 support is retrospective causal
evidence, not fresh untouched OOS.

## Stage 6 selected assembly

Production assembly ID: **`PROD_STAGE6_83C7B31BB42C`**.

Stage 6 selected:

- generation: `v3`;
- futures construction: perpetual;
- strategy: `T3`;
- timeframe: `H1`;
- instruments: `CNYRUBF`, `GLDRUBF`, `IMOEXF`;
- structural overlay: `TRAIL1`;
- economic contract: `CORRECTED_SINGLE_C1`;
- research tick: `0.001`.

Stage 6 was artifact-only: no new backtest, optimizer, parameter search, subset
search, or hypothesis generation. The selected basket was verified against the
Stage 5 corrected single-C1 authority. TRAIL1 was selected from its Stage 5
parent-level retrospective evidence; there is no separate three-instrument
TRAIL1 basket backtest.

## What Stage 6 did not freeze

The assembly decision is **not yet a frozen production specification**. Stage 7
must freeze at least:

- exact strategy implementation/source identity;
- live-contract mapping and roll convention;
- risk allocation and position sizing;
- portfolio safeguards;
- production cost model;
- session operating schedule;
- broker/order semantics;
- data-feed conventions;
- operational safeguards.

## Historical generations

v1 and v2 remain immutable historical evidence. v2 completed its own five-stage
cycle and finished with all four TRUE OOS study classifications `BORDERLINE`.
Historical v1/v2/v3 evidence must not be rewritten by post-v3 findings.

## Governing constraints

- Do not mix TradingSystemLab with BBW, Round Level / Touch, or other projects.
- Do not alter frozen v1/v2/v3 identities or historical verdicts.
- Do not treat revealed TRUE OOS as fresh OOS for a modified identity.
- Do not promote diagnostic-only Minimum Hold, Session, or correlation findings
  into production rules.
- Do not assign a formal H4_03 risk-cap verdict while terminal censoring remains.
- Do not reinterpret TRAIL1 as universally superior: its historical OOS
  drawdown/recovery include explicit counter-evidence.
- Do not begin robot/FINAM implementation before Stage 7 freezes the production
  specification.

## Next permitted action

**Stage 7 — Production Specification Freeze** for `PROD_STAGE6_83C7B31BB42C`.

Stage 7 must consume the exact accepted Stage 6 assembly and Stage 1–6 evidence.
It may freeze implementation and operational details, but it must not silently
re-open selection, optimization, structural hypothesis discovery, or historical
research verdicts.

## Update rule

Update this file after every accepted stage or major audit. The first sections
must always describe the active handoff; older generation checkpoints belong in
clearly labelled historical sections rather than being presented as current.
