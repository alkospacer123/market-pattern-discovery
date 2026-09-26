# Evidence-based roadmap

## Governing rule for future work

The original H1 research cycle and frozen H1 strategy identities are the sole
methodological authority. Every newly researched timeframe must independently
pass **Baseline → Optimization → Robustness → Walk Forward → TRUE OOS**. No
stage may be added, skipped, or supplied by another timeframe. Later timeframe
and MTF implementations are historical evidence only, not alternative
templates. The current cycle retains `FROZEN_TICK_SIZE = 0.001` for every
instrument through all five stages; instrument-specific recalculation requires
a separate, explicitly authorized post-cycle audit branch.

## Canonical research history and fixed post-v3 roadmap

This section is the controlling roadmap for work after the v3 Perpetual lifecycle
closeout. It does **not** retroactively add a stage to v1, v2, or v3 and must not
be used to rewrite their frozen evidence.

### Primary objective

The practical objective is to assemble the most stable and profitable production
basket supported by the completed evidence, with particular emphasis on
calendar-month stability and cross-instrument diversification. The expected
production basket is small (approximately 2–3 instruments), but its composition
must be determined from the evidence rather than fixed in advance. A stronger
standalone PF is not sufficient if the instrument worsens portfolio drawdown,
monthly stability, or correlation concentration. Methodology must remain simple:
use the existing evidence, transparent diagnostics, and a small number of
predeclared structural hypotheses only.

### Research lineage

- **v1 — broad strategy/timeframe discovery on perpetual futures.** The first
  generation researched USDRUBF and CNYRUBF with trend strategies T1/T2/T3 and
  range strategies R1/R2/R3 across M1, M5, M15, M30, H1, H4, and D1. The
  purpose was to identify which strategy/timeframe domains were worth deeper
  development. T2/T3 on M30/H1 emerged as the most stable domain for subsequent
  research, so later generations deliberately focus on those combinations.
- **v2 — quarterly-futures diversification test.** The second generation kept
  T2/T3 on M30/H1 and expanded the market universe with quarterly futures
  (Si, CNY, GD, BR, MIX, NG). The explicit research purpose was cross-market
  diversification: gains in one market should be able to offset losses in
  another market in the same calendar period, reducing dependence on a single
  instrument and smoothing portfolio-level P&L.
- **v3 — perpetual-futures stability replication.** Comparison of the prior
  evidence indicated that the perpetual-futures construction used in v1 looked
  more stable than the broader quarterly-futures construction. v3 therefore
  independently tests that proposition on the perpetual universe
  USDRUBF/CNYRUBF/GLDRUBF/IMOEXF using the same M30/H1 T2/T3 research domain and
  the original H1 lifecycle.

### Mandatory work after v3 closeout

After Phase 5 Closeout is independently reproducible and final, work proceeds
in the following order only:

1. **Master v1/v2/v3 evidence consolidation.**
   Build one deterministic comparison dataset/table across the three research
   generations. It must preserve the identity of each generation rather than
   pooling unlike samples. Include, where available: strategy, timeframe,
   instrument universe, data construction, development/WF/OOS periods, trade
   count, PF, expectancy, Net R, max drawdown, recovery, win rate, average
   win/loss, trade frequency, bootstrap evidence, concentration, yearly,
   quarterly, calendar-month, instrument, and direction statistics, plus
   Development/Optimization -> Walk Forward -> TRUE OOS decay.

2. **Portfolio/diversification comparison.**
   Reconstruct calendar P&L matrices by instrument and month for v2 and v3 (and
   v1 where comparable). Measure how simultaneous gains/losses combine at the
   portfolio level: positive-month share, best/worst month, monthly median and
   dispersion, losing-month streaks, instrument contribution to return and
   drawdown, simultaneous losing instruments, concentration, covariance/
   correlation, and the diversification benefit versus standalone instruments.
   This step must answer whether adding markets actually smooths portfolio P&L
   or merely adds weak instruments.

3. **Trade Anatomy / Failure Analysis.**
   Analyse every available trade from v1, v2, and v3 at trade level to determine
   where the systems earn and lose. At minimum segment by generation, strategy,
   timeframe, instrument, LONG/SHORT, year, quarter, calendar month, weekday,
   entry hour/session, exit hour, holding-time bucket, exit reason, MAE, MFE,
   gross/net R, initial-stop geometry, winner giveback, losing streaks, and
   overlapping-position exposure. The analysis must identify repeatable
   structural weaknesses, not simply the worst historical buckets.

4. **Structural-improvement hypothesis set.**
   Only after the trade-level diagnostics, define a small predeclared set of
   structural hypotheses. Candidate examples include:
   - move stop to breakeven only after reaching +1R;
   - activate trailing only after +1R;
   - minimum holding time except for hard protective stops;
   - restrict new entries to a justified session such as 10:00-17:00 or
     10:00-21:00 and trading days only;
   - cap or divide risk across correlated instruments / correlated clusters;
   - cap total simultaneous portfolio risk.
   These examples are **hypotheses, not approved parameter changes**. Exact
   variants must be motivated by the diagnostics and frozen before testing.
   Do not launch a broad grid, optimizer, ranking search, or mass hypothesis
   generation.

5. **Separate validation of structural changes.**
   TRUE OOS from v1/v2/v3 has already been revealed. Any rule discovered from
   those trades is post-OOS knowledge and therefore cannot be inserted back
   into a frozen v1/v2/v3 identity. Each approved structural change creates a
   new research/production identity and must be evaluated in a separately
   defined validation branch with predeclared rules and no retroactive rewriting
   of earlier evidence.

6. **Production assembly decision.**
   Only after the master comparison, diversification analysis, trade anatomy,
   and separate structural validation may a production assembly be selected.
   The decision must use the full evidence set: profitability, drawdown,
   recovery, monthly stability, cross-instrument diversification, direction
   stability, concentration, WF/OOS durability, execution practicality, and
   portfolio risk. Do not select from PF alone.

7. **Production specification freeze.**
   Freeze the chosen strategy/timeframe/instrument set, signal logic, exits,
   risk allocation, session rules, portfolio correlation controls, cost model,
   data conventions, and operational safeguards before implementation.

8. **Trading robot and FINAM API integration.**
   Implement the robot only from the frozen production specification. Then
   integrate FINAM API with deterministic order/state handling, position and
   risk reconciliation, reconnect/recovery logic, logging/auditability, and a
   staged non-live verification path before any live deployment.

### Governing constraints for the post-v3 program

- Work in the order above unless the user explicitly changes this roadmap.
- Do not mix Trading System Lab with BBW, Level Touch, or other projects.
- Do not treat diagnostic slicing as permission to delete losing trades or
  cherry-pick profitable buckets.
- Cross-version comparisons must distinguish unlike universes and data
  constructions; raw PF or Net R is not a valid standalone ranking criterion.
- Calendar-month attribution and instrument-level contribution are mandatory
  because portfolio diversification is an explicit project objective.
- Structural execution/risk overlays must be separated conceptually from
  signal-alpha changes.
- No post-OOS finding may alter the historical v1/v2/v3 verdicts or identities.
- The final objective is a defensible production assembly, followed by a
  frozen robot specification and FINAM API implementation.

## Completed

- **Current v2 single-system cycle:** Phase 1 Baseline, Phase 2 Optimization,
  Phase 3 Candidate Freeze, Phase 3 Robustness, Phase 4 Walk Forward, and Phase
  5 TRUE OOS are complete as procedures. Phase 4 is `PHASE_4_BORDERLINE`
  (canonical merge `0b0027665fdcc0f847b6b9a10cb5928fcfd2d553`); Phase 5
  independently classifies T2/M30, T2/H1, T3/M30, and T3/H1 `BORDERLINE`.
  The Phase 5 canonical merge is `2d7cd61b8d4d399901ebce397d1c2b7111ae427c`.
  The cycle stops at evidence: no portfolio, MTF, cost branch, or replacement.

- **Original H1:** committed unified Baseline (Phase 2), bounded Optimization
  (Phase 3.2), Robustness (Phase 3.3), Walk Forward (Phase 4), diagnostics
  (Phase 4.1), TRUE OOS (Phase 5), and portfolio construction (Phase 6).
  Completion records artifact production; the verdicts below still govern.
- **M5, M15, M30:** committed artifacts record Baseline, Optimization,
  Robustness, Walk Forward, and TRUE OOS. These are historical implementations,
  not templates for future work.
- **H4:** Baseline completed. Optimization separately classified T2 and T3
  `ROBUST_PLATEAU`; Robustness separately classified both `BORDERLINE`; Walk
  Forward separately completed `PHASE_H4_WALK_FORWARD_BORDERLINE`; TRUE OOS
  separately classified both `FAIL`.
- **D1:** Baseline completed and Optimization completed. The Optimization report
  classifies both T2 and T3 `LOCAL_SPIKE` and explicitly says Robustness, Walk
  Forward, and TRUE OOS were not performed. No later D1 lifecycle stage is
  marked complete.
- **M1:** its committed manifest records Baseline completion. No complete
  Optimization → Robustness → Walk Forward → TRUE OOS bundle is inferred.
- Phase 7.1 MTF research, Phase 7.2 artifact-only registry, and Phase 7.3 true-
  MTF research have committed completion manifests. They remain independent
  historical branches.

## Completed but borderline/inconclusive

- Original Phase 4 is `PHASE_4_BORDERLINE`; T3 is
  `WALK_FORWARD_BORDERLINE`, with later `MIXED_EVIDENCE` diagnostics. Phase 4.1
  classifies T2 and T3 `SAMPLE_LIMITED`.
- H4 Robustness is `BORDERLINE` for each strategy and H4 Walk Forward is
  borderline. These do not replace H4 Optimization's separate
  `ROBUST_PLATEAU` classifications. H4 TRUE OOS records T2/T3 `FAIL`.
- Later TRUE OOS outcomes remain candidate-specific: M30 records T2
  `BORDERLINE` / T3 `PASS`; M15 records T2 `FAIL` / T3 `PASS`.
- Historical v2 Phase 1 generated all 24 runs but its audit verdict is **FAIL /
  NOT COMPLETE**. Its instrument-spec and provenance findings remain historical
  evidence, not the controlling roadmap.

## Current v2 single-system cycle

**COMPLETE as a procedure across all five stages.** Phase 1 Baseline, Phase 2
Optimization, Phase 3 Candidate Selection / Freeze, Phase 3 Robustness, Phase
4 Walk Forward, and Phase 5 TRUE OOS are complete.

The final Phase 5 classifications are:

- T2/M30 `BORDERLINE`
- T2/H1 `BORDERLINE`
- T3/M30 `BORDERLINE`
- T3/H1 `BORDERLINE`

The canonical Phase 5 merge is
`2d7cd61b8d4d399901ebce397d1c2b7111ae427c`. The v2 lifecycle itself remains
closed and frozen. The explicit post-v3 program defined above is now authorized;
it analyzes the frozen evidence but does not reopen v2 Optimization, change its
candidates, or rewrite its TRUE OOS verdicts.

## v3 Perpetual independent generation

- Phase 1 Baseline: **COMPLETE**.
- Phase 2A T2: **COMPLETE**; M30/H1 `ROBUST_PLATEAU` counts are 3/4.
- Phase 2B T3: **COMPLETE**; M30/H1 `ROBUST_PLATEAU` counts are 9/9.
- Phase 2 overall: `V3_PERPETUAL_PHASE_2_OPTIMIZATION_COMPLETE`; 82 bounded
  OAT configurations and 25 robust-plateau configurations were independently
  consolidated without rerunning Optimization.
- Candidate Freeze: **COMPLETE**. T2/M30 `T2_M30_candidate_v3`, T2/H1
  `T2_H1_candidate_v3`, T3/M30 `T3_M30_candidate_v3`, and T3/H1
  `T3_H1_candidate_v3` are immutable.
- Phase 3 Robustness: **COMPLETE** (`V3_PERPETUAL_PHASE_3_ROBUSTNESS_COMPLETE`).
  T2/M30, T2/H1, T3/M30, and T3/H1 each classify `ROBUST_READY`; this is not a
  ranking or candidate replacement.
- Phase 4 Walk Forward: **COMPLETE**
  (`V3_PERPETUAL_PHASE_4_WALK_FORWARD_COMPLETE`). All studies have four valid
  folds. T2/M30, T2/H1, and T3/M30 are `WALK_FORWARD_BORDERLINE`; T3/H1 is
  `WALK_FORWARD_PASS`.
- Phase 5 TRUE OOS and reproducible closeout: **COMPLETE**. Canonical closeout
  merge: `aab2659cfc91846631bbe22ff3b45e3e4e4af85f`. The canonical auditor
  independently reconciles semantics, performs an isolated second generation,
  and verifies an exact 50/50 research-artifact SHA-256 match before finalizing.

## v3 perpetual lifecycle — COMPLETE

The prescribed five-stage v3 lifecycle is **complete as a procedure**. Phase 1
Baseline, Phase 2 Optimization, Candidate Freeze, Phase 3 Robustness, Phase 4
Walk Forward, and Phase 5 TRUE OOS are COMPLETE. Fixed-order Phase 5 results are
T2/M30 `BORDERLINE`, T2/H1 `BORDERLINE`, T3/M30 `PASS`, and T3/H1 `PASS`.
No ranking or winner selection was performed, no portfolio phase is created,
and no additional lifecycle phase is authorized by this closeout.
