# IntradayLab — research roadmap

## Master Strategy Registry / Optimization preparation — 2026-10-11

Fixed A_v1, B4/B7/B10 and C_v1 Baselines are complete and their frozen
results remain unchanged. Actual GitHub main is
`f7a1ff5f12779a2b3dfbe5e4dbfe8f265096d3d8`, merge of PR #478.
The [Master Registry](optimization_registry/REGISTRY_REPORT.md) records all
found families, configurations, execution variants and historical references.

The common instrument-specific research admission rule is **100 verified
CLOSED / 40 distinct CLOSED entry days / 6 active CLOSED calendar months**,
with credible signals/execution and pinned reproducible code/config/source.
**Any initial Baseline PF** is admissible. UNKNOWN, SKIP, EXCLUDED, rejected
signals and diagnostic seeds do not count as CLOSED. ELIGIBLE is admission
for research, not economic PASS or proof of annual profitability.

After independent registry audit, review/acceptance and a separate user merge
decision, the next lifecycle step is individually authorized **Optimization**:
[A, B, C, then other eligible families](optimization_registry/OPTIMIZATION_QUEUE.md).
Each instrument/configuration must qualify; sparse cohorts stay excluded.
Use only available 2023 development history; target after-C1 PF >= 2.0,
sufficient closures, positive expectancy, regular positive months, controlled
DD/concentration and stable neighboring parameters. Freeze each family's grid,
budget, exact parameters and candidates before its separate Optimization.
This registry task executes no Optimization and authorizes no following run.

See [machine-readable policy](optimization_registry/OPTIMIZATION_POLICY.json)
and [registry audit](optimization_registry/REGISTRY_AUDIT.json).
This current status supersedes older pending A/B/C and positive-PF-only gate
text below; all historical sections are retained verbatim. The five-step
Baseline → Optimization → Robustness → Walk Forward (2024) → TRUE OOS (2025+)
lifecycle is unchanged. TradingSystemLab, frozen artifacts, source data and
Draft PR #472 remain untouched. **STOP at this registry Draft PR; no merge or auto-merge.**

## Completed fixed C_v1 Baseline — 2026-10-11, Draft PR review only

The separately authorized **RETURN_RETEST_REJECTION_M5 / C_v1 / 2023** Baseline
is complete. **Technical PASS**, 552 pre-P&L tests plus 4 reporting-audit revision
tests; independent raw-M5 audit 570434 fields PASS and two full repeats with
all 15 initial artifacts byte-identical. Base main after merged #477:
`f0e56f5df557ac4eae19af333b6d438524f5f6ff`; trading/config/audit freeze before
first C P&L: `16d07c2c5dc7b3fe5ceb90760e9ce4a7ed17358f`.

Three distinct approaches to one strictly causal local extreme require two
whole-M5 retreats; fixed five-bar lookback, +/-2-tick zone, >=3-tick retreats,
24-bar maximum, third Close >=1 tick toward rejection. Unchanged common engine,
ENTRY_NEXT_OPEN and DATA_GAP_SKIP_V2. Config, source guard and trade logic remain
frozen. A separately versioned **audit 1.1** fixes only pooled Decimal summation
order (-2E-26 R discrepancy); original auditor and all trading/results bytes
retained. [Explicit disclosure](reports/RETURN_RETEST_C_V1_AUDIT_REVISION_1_1.md).

**188 accepted entries = 168 CLOSED + 20 EXCLUDED**, 2 SKIP; ordinary trades are
CLOSED only. Conditional known after-C1 normalized PF **0.545**, Net **-84.183 R**.
USD 102 CLOSED /12 active months and CNY 61 /11 have negative conditional C1
expectancy; GLD 2 /2 is sparse and negative; IMOEX 3 /1 is positive but sparse
with 2 excluded outcomes. Incomplete source/outcomes prevent complete annual
or continuous account-return evidence; skips/exclusions and conditional FLAT
are explicit. No pooled cross-instrument price PF.

Under the latest Roadmap, low/negative initial PF does **not** reject family C
before future Optimization. C is technically reviewable for a separately
versioned 2023 optimization study, subject to common audited CLOSED-count and
calendar-breadth thresholds preregistered before ranking. This task selects no
such thresholds and runs no Optimization. Sparse instrument cohorts do not
supply sufficient evidence. [Full task summary](results/return_retest_rejection_m5_2023_c_v1/Task_Summary.md),
[immutable A/B comparison](results/return_retest_rejection_m5_2023_c_v1/Comparison.md).

Only current status is inserted here; historical decisions remain below.
Common core, frozen A/B and prior results, TradingSystemLab/live robot, pinned
source and independent Draft #472 remain unchanged. **STOP after Baseline C;
separate Draft PR without merge/auto-merge. No Optimization, Robustness,
2024 WF, 2025+ TRUE OOS, LIVE or next strategy.**

## Data Gap Skip / Backtester v2 — technical implementation, 2026-10-11

The separately authorized engineering task implements opt-in `DATA_GAP_SKIP_V2`
for future versioned M5 studies. Default `LEGACY_UNKNOWN`, all frozen strategies,
configs and historical UNKNOWN artifacts remain unchanged. Missing entry Open
means a counted skip with no delayed fill; missing exposure after a modeled fill
means a separate no-P&L exclusion and a same-day entry block. Subsequent independent
days retain explicit conditional FLAT. Six reports disclose accepted = CLOSED +
EXCLUDED, skips, coverage, exclusion share and selection bias. See the
[technical handoff](reports/DATA_GAP_SKIP_V2_TECHNICAL_HANDOFF.md) for API, tests,
independent audit and byte regressions. This supersedes the implementation-PENDING
status below, without activating v2 in any old runner. **STOP: no C Baseline,
Optimization, 2024 WF, 2025+ TRUE OOS, LIVE or merge.**

## Updated USER DECISION — 2026-10-11: optimization after full Baseline queue

**This latest decision supersedes historical positive-Baseline-only Optimization eligibility text below.** Keep exactly the existing **Baseline → Optimization → Robustness → Walk Forward (reserved 2024) → TRUE OOS (locked 2025+)** research lifecycle. Do not alter completed, frozen A_v1 or earlier strategies, configurations, reports or results.

**Execution order:** finish the already-running B4/B7/B10 fixed task under its original preregistered rules; independently audit and review its Draft PR. Then separately authorize and complete the C Baseline and any other explicitly approved signal families. After the Baseline queue, run separate, versioned Optimization on **each eligible** family, including historical IntradayLab strategies. Negative initial PF does **not** bar parameter search. Eligible means a sufficient sample of **fully resolved, independently audited executed trades**, not raw signals, rejected orders or data-gap exclusions; set an objective common minimum for count and active calendar breadth **before any new optimization or ranking**. Do not optimize sparse strategies; report excluded candidates and reasons.

**Deliberate development fitting:** optimize only on **2023**. For each family preregister a bounded parameter grid and run budget covering applicable touches, zone widths, distinct approaches, entry displacement, structural Stop buffers and separately defined fixed-distance Stops, holding limits, and Take ratios **2R through 10R** (including 4R/6R), plus later specifically authorized causal trailing/MTF/filter tests. Evaluate all candidates on after-C1 net PF, executed trade count, positive expectancy, monthly regularity, concentration and drawdown. **Target after-C1 PF >= 2 with enough trades**, not a guarantee or a PF-only maximum on a tiny sample. Publish every tested configuration and its eligibility, not just the winner. Freeze any chosen configuration before Robustness, reserved 2024 WF and locked 2025+ TRUE OOS. Do not select, optimize or respecify using WF/OOS; exposure disqualifies their future claim to untouched independent confirmation. If no sufficient PF 2 candidate exists, report failure; never fabricate a passing result.

**User-directed removal of UNKNOWN from prospective normal trade ledgers: implementation PENDING, not silently activated.** Missing/invalid signal candle or immediately required entry Open: **skip the entry** with a documented DATA_GAP_SKIP reason; never fill at a later Open. A missing candle **after a modeled position has already opened** cannot retroactively make that fill nonexistent. Exclude its unresolvable outcome from PF/Net with a distinct **audited data-quality exclusion record**, retaining the entry/gap evidence and counts, with no invented Stop, Take, close, P&L or continuous equity. The normal ledger for *new versioned studies* should contain only resolved trades; data-quality receipts must disclose every skipped or excluded opportunity and coverage limitations, including potential selection bias in incomplete cohorts. Do not equate skipped/excluded sample with a complete, live-executable strategy. This requires a **separate audited engineering task and Draft PR after the ongoing B task**, with causal/gap fixtures and unchanged legacy regression artifacts. Existing A_v1 and B runs with historical UNKNOWN evidence remain immutable and traceable, and may not be relabeled or overwritten. No automatic code change or optimization is authorized by this documentation decision.

**Isolation:** IntradayLab files only. TradingSystemLab, active trading robot, market-pattern-data, frozen IntradayLab artifacts, unrelated PRs and protected future data are read-only.

## Completed first Round Level family A Baseline — 2026-10-11

The single fixed **EQUAL_HIGH_LOW_M5 A_v1** 2023 Baseline is complete: **INCONCLUSIVE** for coverage/outcomes. Conditional known C1 closures have **NO ECONOMIC BASELINE PASS** for USDRUBF, CNYRUBF and IMOEXF; GLDRUBF is positive on only 9 known closures, **INSUFFICIENT_EVIDENCE**. No Optimization handoff. [Baseline report](results/equal_high_low_m5_2023_a_v1/Baseline_Report.md), [independent algorithm audit](results/equal_high_low_m5_2023_a_v1/Independent_Audit.md), [validation note](reports/EQUAL_HIGH_LOW_M5_2023_A_V1_VALIDATION_NOTE.md).

Base GitHub main `d438c72f9fce5c3bf1d30c9b169d14b97079e768` (merged #473). Pre-P&L code/config/contract freeze `f880b3c4ac0fd2cb6d997d7680a1e427a2537340`, 476 tests PASS, config SHA-256 `cec9b815e1479d7999acf77442840d507eaa5f4e078573e0da4b9d34abc6521a`; no frozen trading dependency changed after returns. Opt-in **ENTRY_NEXT_OPEN** resolves completed M5 → immediate next Open at the same boundary; default waiting M5 remains unchanged, with all six old shared-engine candidates' results byte-identical. **ENTRY_CLOSE_ORACLE** is separate diagnostic only, never economic evidence.

3313 raw directional candidates include 86 ambiguous candidates (both sides rejected/consumed); 3227 qualified signals → 562 model fills +2605 known refusals +60 UNKNOWN possible entries. 491 CLOSED /131 UNKNOWN in the ledger; UNKNOWN comprises 71 filled paths and 60 possible entries, never assigned P&L. Two repeats match all 23 deterministic artifacts; A_v1 independent audit PASS, 212520 fields; six default-mode regressions PASS via the separately hashed reporting verifier. Original frozen validator retains a legacy annotation/CSV-field mismatch; the reporting-only correction is disclosed in validation.json and the note, with no trade/config change.

Only exact 2023 M5 prefixes from pinned read-only `f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8`; 2024+ price bytes unread. All old strategies/config/results, TradingSystemLab/live robot/broker settings and separate Draft #472 (`82ec9ffe61e18a43cd7510e398f6913b25f045e1`) preserved. **STOP after separate Draft PR, no Merge.** Allowed next action is review of this result/audit. B 4/7/10 and future 4–10, C approaches, touch/Stop/Take 2/3/5/7/10R optimization, trailing, MTF/filters and comprehensive historical loss attribution stay documented for separate tasks; none ran automatically.

## Approved Round Level / Touch / Accumulation research plan — 2026-10-11

**USER DECISION: PLAN APPROVED; IMPLEMENTATION / NEW BASELINE NOT YET RUN.**
This is the next research priority. The previously listed 2026-10-10 R16/Level/Swing/Trend/Bollinger queue below is historical, not an instruction to rerun already completed candidates: R16, Level Rejection, Swing Pullback and Trend Pullback were completed and merged through PR #471 (base `a63581a6942974ff7d636387d2ceb23893303096`); separate Bollinger/RSI Draft PR #472 remains unmerged as of this decision. After the bounded Round Level work, perform the user-requested comprehensive loss-attribution review of **all** previously researched strategies, including historical external-branch/CMD work rather than only this roadmap. This is a decision on order, not permission to execute all tasks automatically.

**Research objective.** Test whether repeated candle **High** near a resistance zone (SHORT) or repeated **Low** near a support zone (LONG) produces a fast rejection with a small, bounded structural Stop and favorable after-C1 expectancy. The illustrative sequence `100,101,100,99,100,101,100` means **seven candle High values**, all within a high-cluster zone, **not consecutive prices/Closes** and not necessarily a seven-bar requirement. More touches might strengthen rejection or instead increase breakout likelihood: both are hypotheses, not facts. Round-number proximity is an optional classification, **never a mandatory filter for all hypotheses**.

**Distinct preregistered signal families, each independently versioned, no retrospective PF-driven selection:**

| Family | Definition and initial Baseline focus | Later bounded research questions |
| --- | --- | --- |
| **A EQUAL_HIGH_LOW** | Exact same High (SHORT) / Low (LONG) on **3 consecutive completed M5 bars**, with the final completed candle closing away from that extreme. One cluster/event, not overlapping duplicate fills; mirror LONG/SHORT. | 2–5 touches; one/two-tick tolerance; consecutive vs bounded-window touches. |
| **B HIGH_LOW_CLUSTER** | A compact zone of candle High values (SHORT) or Low values (LONG), **not** a range of consecutive Closes. **Independent fixed Baseline architectures** with 4, 7 and 10 completed M5 bars are planned, each with predefined admissible zone width, boundary-touch count and the same execution contract; they require separate run decisions after A. | **Every duration 4–10**; separate total-bar count, near-boundary touch count, zone width in dated ticks and relative to ATR14; clustered repeated High/Low can be non-round. |
| **C RETURN_RETEST_REJECTION** | Repeated distinct approaches to a local High/Low with a completed-bar pullback between touches; initial **3 distinct approaches**, not merely consecutive bars. Planned as a separate future fixed Baseline. | 2–5 independent approaches; pullback depth and time separation. |

**Level types:** any exact/non-round traded price, a cluster near a prespecified round-price grid, and a cluster away from round prices. Existing historical reference step sizes: USDRUBF 0.10 RUB, CNYRUBF 0.05 RUB. GLDRUBF and IMOEXF round steps and all zone-width rules must be justified and frozen **before evaluating P&L**. Use the actual date-sensitive exchange/research tick grid for each symbol, especially CNY's historical tick change. An arbitrary ordinary price must be a legitimate past candle High/Low, never selected using future bars. All clustered events have deterministic identity, reset/expiry, and duplicate suppression.

**ENTRY CLOCK — EXPLICIT EXCEPTION REQUESTED FOR THIS NEW CANDIDATE:**
- **Primary `ENTRY_NEXT_OPEN`:** after the signal M5 has fully closed, attempt admission and modeled fill at the **immediately following M5 Open**, with no additional waiting/confirmation candle. Reject missing/invalid next Open and illegal windows honestly. This primary clock must be implemented as a **new opt-in, explicitly named mode** in the existing independent IntradayLab Backtester, with tests for boundary ordering and price/availability causality; keep the default completed M5 -> one full waiting M5 -> later Open **unchanged for every existing candidate and frozen artifact**.
- **Secondary `ENTRY_CLOSE_ORACLE`:** idealized fill at the already-known signal M5 Close, **diagnostic upper-bound/latency comparison only**. The same-bar signal Close is not a proven executable causal fill when final High/Low/Close are required for signal formation. Exclude this oracle from economic Baseline PASS, trade-realism claims and candidate selection. Do not sneak a favorable Close into primary next-Open records.
- No E1/E2/E3 confirmation-candle/retest-entry matrix. The three **signal families** A/B/C are different; they do not mandate waiting after a signal.

**Initial trade geometry, preregister before any return evaluation:**
- SHORT Stop = maximum High of the fully observed cluster + outward **1 dated tick**; LONG Stop = minimum cluster Low - 1 dated tick. Stop uses only completed bars; risk and target geometry are recalculated from the **actual next Open**, not signal Close.
- Proposed initial entry admission: risk at least **3 dated ticks**, no more than **12 dated ticks**; entry may not be more than **4 dated ticks** beyond the relevant cluster boundary in the favorable direction (avoid chasing a completed impulsive rejection). Invalid Stop geometry, excessive impulse displacement or too-small risk must be **NONFILL/rejection**, never widened/shifted secretly. Verify that these defaults are executable and instrument-aware on 2023 data **without P&L selection**, then freeze and hash in the candidate config before Baseline.
- Initial fixed exit: **FULL_NET_C1_R = 3** (planned reward divided by planned Stop loss **including C1**), max calendar holding **120 minutes**, subject to existing earlier session-flat/trade deadline. Retain existing engine's Stop-first, gap, one-position, no-entry-bar Take, C1 one dated tick per side and UNKNOWN handling.
- **Optimization only after credible positive Baseline:** bounded touch counts and widths, buffer 1/2/3 ticks, max-Stop and entry-distance caps, fixed **net 2/3/5/7/10R**, and **one** causal trailing-stop alternative (activate after +1R, then trail by extrema of last three **completed** M5, never loosen). Dynamic trailing must use the common engine, not a parallel optimistic simulator. Compare nominal and realized reward/loss after costs.
- **Optional later justified filters:** standalone completed M15/M30 context, or one ADX/EMA/ATR regime filter compared independently to the same unfiltered candidate. No automatic full indicator+MTF grid or new optimization phase.

**Execution sequence and gates.** (1) This roadmap documentation decision; (2) Codex separate **Draft PR without Merge** for causal opt-in next-Open clock, fixed A-v1 strategy/config, preregistration and ONE complete 2023 A-v1 Baseline with independent audit; (3) inspect actual PR files/results and separately authorize B 4/7/10 fixed Baselines and then C, without retrospectively modifying A; (4) Optimization **only on independently audited, credible positive C1 economic evidence**; then Robustness, reserved **2024 Walk Forward**, locked **2025+ TRUE OOS** in existing order. Do not use prior selected 2026 Historical CMD results as untouched OOS confirmation. A/B/C and older CMD rankings cannot be conflated.

**Mandatory results:** USDRUBF, CNYRUBF, GLDRUBF, IMOEXF, available full **2023 M5** from pinned read-only `market-pattern-data`; signals, model orders/NONFILL, CLOSED/UNKNOWN trade ledger, dated C1, price and initial-risk-R PF, gross/cost/net expectancy, each calendar month/no-trade month, instruments/directions, Stop distance, cluster width/touch counts, time/session exits, realized target/trailing distribution, frequency, DD/concentration where knowable. No invented missing bars, no treating known CLOSED-only conditional PF as proven complete-year PF. Goal **PF C1 >= 1.6 (prefer >2), positive expectancy and consistent positive calendar months**, not a guarantee or quota. **Do not advance an economically negative/incomplete Baseline.**

**Safety:** Only `IntradayLab/` files may be added/changed. `TradingSystemLab/`, live robot/account/config/results, other frozen IntradayLab artifacts, source data, and unrelated PR branches stay completely untouched. Every Codex task starts by checking the factual GitHub `main`; work one Draft PR at a time and never auto-merge, auto-authorize LIVE or open protected future data.


## Approved reserve M5 / M15 / MTF strategy sequence — 2026-10-10

**User decision / conditional research queue, not an authorization to execute every candidate.**
The active Codex task is **R16 Compression Breakout M5**. Complete its separate Draft PR,
independent GitHub/code/trade-ledger audit and merge decision first; do not restart,
alter, or parallelize R16. If its Baseline cannot demonstrate credible positive C1
economics, the following order is approved for **future separately authorized
one-at-a-time Baseline tasks**. A profitable candidate does not automatically
trigger another strategy or the next research stage.

| Order | Candidate | Intended trading / context TF | Next action / evidence status |
| --- | --- | --- | --- |
| Current | **R16 Compression Breakout** | M5, intrinsic ATR14; no obligatory MTF | Codex task running; fixed historical parameters, 2023 Baseline pending independent review |
| 1 | **LEVEL_REJECTION_M5** | Standalone M5 | First reserve. Previous [causal opportunity preflight](results/stage2_level_rejection_m5_opportunity_v1/REPORT.md) is `OPPORTUNITY_FEASIBLE` **only**, not a traded/P&L Baseline. Use its preregistered [six-bar rejection grammar](reports/STAGE2_LEVEL_REJECTION_M5_OPPORTUNITY_PREREGISTRATION.md) as provenance; freeze any adaptation to the accepted common M5 execution clock **before P&L** |
| 2 | **SWING_PULLBACK_M5_M15** | M5 entries + strictly completed/available M15 directional context | New, distinct pullback/continuation hypothesis; preregister causal swing, retracement, confirmation, stop/exit, MTF availability and entry clock before looking at outcomes. Do not relabel existing level-breakout/retest as swing pullback |
| 3 | **TREND_PULLBACK_M15_H1** | Independent M15 signal, entry, stop and exit + completed/available H1 context | New separately specified M15 strategy. The current shared Backtester is **M5-only**; any M15 support requires its own approved technical change and tests, not an assumption that the M5 engine already supports M15 |
| 4 | **BOLLINGER_RSI_REENTRY_M15** | Standalone M15; optional higher-TF only if independently justified beforehand | Last reserve: a different re-entry hypothesis, **not** a rerun of rejected VWAP MR with renamed indicators. No automatic MTF addition |

**Execution and evaluation contract:**

- One fixed strategy/parameter set and its causal indicators at a time. Start at
  **Baseline**, not a grid search; advance only by the existing
  **Baseline → Optimization → Robustness → Walk Forward → TRUE OOS** lifecycle.
  No new stage, mandatory four-way indicator/MTF matrix, or retuning after
  inspecting 2023 P&L. A strategy can include MTF intrinsically if causally
  defined before its Baseline. Historical variants are not positive evidence
  until independently audited on the shared contract.
- Use the pinned, read-only `market-pattern-data` **2023** source, four approved
  perpetual instruments where data exist, dated tick sizes, C1 one tick per
  side, proper missing-bar/UNKNOWN accounting, Stop-first execution, monthly
  instrument/direction breakdowns, PF in price units **and R**, expectancy R,
  concentration and independent trade-ledger audit. Positive **calendar months**
  are a central goal, never a guaranteed outcome. Report conditional known
  closures separately from unproven continuous annual/account economics.
- The shared Backtester governs timing. For M5 its currently approved clock is
  completed signal M5 → one complete waiting M5 → next admissible Open. Derived
  M15/H1 must use exact completed children, session-aware boundaries and
  strictly available higher-TF observations; no missing-child fill or stale
  context. Do not alter the entry clock to rescue a negative Baseline; investigate
  delay impact as a **separate predeclared** research decision.
- Preserve prior negative / insufficient-evidence work as actual history:
  ORB A BASE and R17 on the shared M5 core, plus earlier VWAP MR, Session
  Momentum and Squeeze M5/M30 and M15/H1 research. See
  [M15 Squeeze verdict](reports/STAGE2_SQUEEZE_M15_FINAL_REPORT.md) and
  [VWAP/Momentum MTF verdict](reports/STAGE2_CAUSAL_MTF_FINAL_REPORT.md).
  No recycling a failed variant under a new name and no claim of proven edge
  from sparse profitable subsets.
- **2024 remains reserved Walk Forward; 2025+ remains locked TRUE OOS.**
  Any historic 2026 data used to select old R16/R17 candidates cannot later be
  labelled untouched TRUE OOS for those candidates.
- **Isolation:** every new code/config/result/document change must be confined
  to `IntradayLab/`. Do not modify `TradingSystemLab/`, its robot, strategies,
  configurations, results, broker authority/runtime, `market-pattern-data`, or
  already frozen IntradayLab research. Every task independently verifies actual
  GitHub `main`, protected trees and committed result artifacts; Draft PR,
  no automatic merge. This queue itself starts no new experiments.

## Current shared Backtester and first canonical Baseline — 2026-10-10

**Common infrastructure COMPLETE / technical PASS. ORB A BASE Baseline INCONCLUSIVE;
known-closure C1 expectancy: NO ECONOMIC BASELINE PASS. Do not advance ORB to Optimization.**
The [independent core](core/README.md) implements the approved architecture without
ORB rules or TradingSystemLab imports. One [canonical A BASE 2023 run](results/orb_a_base_2023_canonical_v1/Baseline_Report.md)
uses unchanged #463 initial parameters, exact pinned data and the common M5 clock.
266 tests and independent audit PASS; 171 sufficient-day trades match frozen #463,
all 12 months are reported, 246 known closures and 20 UNKNOWN retained, annual
complete metrics null. Two full repeats are byte-identical. Old studies stay frozen.

This task completes only Baseline infrastructure and its first candidate replay.
Incomplete data/outcomes remain concrete diagnostics, not a new methodology stage.
Subsequent candidates should plug into this core and begin with fixed-parameter
Baseline under separate authorized scope. Optimization requires credible positive
C1 economics and sufficient evidence; no tuning, extra experimental modes or
automatic next stage follows this negative/incomplete ORB result. 2024 remains WF,
2025+ remains locked TRUE OOS, TradingSystemLab/live robot remain untouched.

> **Canonical architecture decision — 2026-10-10:** IntradayLab adopts the **methodology and reusable Backtester architecture** of TradingSystemLab, while remaining **100% independent**. One strategy with fixed parameters → shared research Baseline → Optimization only on credible positive C1 economics → Robustness → 2024 Walk Forward → 2025+ TRUE OOS. No obligatory ATR/MTF/grid; no year-long UNKNOWN latch in independent historical-day research. All TradingSystemLab files and live robot are protected read-only. Ongoing Draft PR #463 is separate. **Authoritative for future work:** [ARCHITECTURE_DECISION.md](ARCHITECTURE_DECISION.md). Dated sections below are historical evidence and do not override this decision.

## Completed Stage 2 — standalone M15 / H1→M15, 2026-10-10

**FEASIBILITY PASS / NO ECONOMIC BASELINE PASS** for `SQUEEZE_M15` and `SQUEEZE_H1_M15`. Actual GitHub main verified at `7643513a7ce718b142454fe094186c3e6bbb4605`, merged PR #455 and #456. This separate pair completes the approved four-architecture matrix: 16 new fixed 2023 scenarios, 32 across both pairs; C2 substitutes costs on identical fills. [Final report](reports/STAGE2_SQUEEZE_M15_FINAL_REPORT.md), [pre-returns rules](config/stage2_squeeze_m15_v1.json), [technical feasibility](reports/STAGE2_SQUEEZE_M15_FEASIBILITY.md).

BB/EMA/ATR7 and two M15 squeeze candles were fixed on technical grounds before P&L; maximum same-window segment18 excludes BB20. Exact3/12 completed M5 parents only; M15 available T+20/25, H1 T+65/70. Both delays target the same future M15 Open, and actually produce identical fills. Independent raw-source oracle: **651721 fields PASS, zero discrepancies**. Full annual Net/PF/DD remain null for incomplete coverage.

USD standalone8 trades, C1 closed PF2.333 / Net0.28; H1 five trades, PF5.167 / Net0.25. High PF on tiny cohorts and partially covered positive months does not establish a profitable regular plateau; standalone C2 PF1.414. CNY two wins only in December, GLD one loss, IMOEX no fill after one genuine nonfilled order. H1 does not show a sustainable advantage. **Each of the four tested Squeeze architectures has NO ECONOMIC BASELINE PASS.** Frozen M5/M30 PR #456 code/config/journals/results and its economic verdict remain unchanged. No parameter selection by maximum PF, new phase, Stage3, WF, TRUE OOS or LIVE; separate Draft PR without Merge.

The earlier sections below are retained as historical provenance; their old current/next wording does not reopen completed experiments or override this closeout.

## Current Stage 2 — Volatility Squeeze Breakout, 2026-10-10

GitHub `main` verified at `01e092112efd408f331c0a2b95f04e75187573bd`: **PR #454 MERGED**, including the completed [final independent trading-logic audit](reports/STAGE2_FINAL_INDEPENDENT_TRADING_LOGIC_AUDIT.md). **VWAP Mean Reversion and Session Momentum: TRADING LOGIC PASS / NO ECONOMIC BASELINE PASS / REJECT CANDIDATE.** Their code, configurations, audits and results remain frozen; historical entries below are provenance, not active sequencing gates.

The user explicitly authorized the next roadmap candidate **Volatility Squeeze Breakout**, with exactly `SQUEEZE_M5` and `SQUEEZE_M30_M5`, four instruments, entire available 2023 history, 8 C1 T10 runs and their 8 T15 stresses, plus C2 substitution on identical fills. Rules are [frozen before returns](reports/STAGE2_SQUEEZE_PREREGISTRATION.md) in [versioned configuration](config/stage2_squeeze_v1.json). Research is **COMPLETE: STAGE2_SQUEEZE_NO_ECONOMIC_BASELINE_PASS**; [final report](reports/STAGE2_SQUEEZE_FINAL_REPORT.md), [independent audit](results/stage2_squeeze_v1/independent_audit.json). Both fixed architectures have trading-logic PASS but only 4 USD / 3 CNY T10 entries each, no GLD/IMOEX entries; closed-only C1 PF0.667 /0, no credible regular profitable baseline. Full annual Net/PF/DD remain null. PR #456 received independent user acceptance and was merged to main (`23f25d6ea07e778fa4333fcab3564aeddb763a6a`); Stage 3, WF/OOS/LIVE remain unauthorized.


## Approved two-entry-timeframe Squeeze matrix — user decision, 2026-10-10

**Two separate trading timeframes, not four M5 variants.** For Volatility Squeeze Breakout the user explicitly chose these **four complete research architectures**:

| ID | Signal and execution timeframe | Higher-timeframe context | Research role |
| --- | --- | --- | --- |
| `SQUEEZE_M5` | M5 | none | Standalone M5 control |
| `SQUEEZE_M30_M5` | M5 | completed M30 | Same M5 trading engine, additional M30 entry filter |
| `SQUEEZE_M15` | **M15** | none | Independent M15 indicators, squeeze, signal, execution, Stop/Take and exits |
| `SQUEEZE_H1_M15` | **M15** | completed H1 | Same independent M15 trading engine, additional H1 entry filter |

**Sequencing after Merge #456:** the first Squeeze pair (`SQUEEZE_M5`, `SQUEEZE_M30_M5`) completed independent review with `STAGE2_SQUEEZE_NO_ECONOMIC_BASELINE_PASS` and was merged into `main` at `23f25d6ea07e778fa4333fcab3564aeddb763a6a`; its rules, findings and all artifacts are frozen. The user now authorizes proceeding with the **separate M15/H1→M15 Stage 2 pair**, to be preregistered and audited on a new manifest **before any P&L**. Do not edit M5/M30 artifacts or retroactively revise its verdict. No new roadmap phase or optimization grid. Across both pairs, four instruments × four architectures × T10/T15 = **32 total fixed scenario runs** (16 completed + 16 newly authorized), with C2 an identical-fill cost stress rather than extra architecture.

**M15/H1 feasibility gate BEFORE economic returns:** the present strict same-window reset has morning 10:00–14:00 (16 M15 slots) and afternoon less than five hours; a naive 20-prior-bar/20-period M15 Bollinger/Keltner plus three-squeeze-bar warm-up cannot fit in either window. Independently verify actual usable completed M15 bars, indicator seed and continuous session coverage; predeclare a technically valid **M15-specific** indicator specification justified by bar duration and signal horizon *before* looking at P&L. Do not silently carry warm-up across lunch, overnight or gaps, or shorten periods after seeing PF. If valid causal warm-up cannot be established, classify M15/H1 study **FEASIBILITY BLOCKED / INCONCLUSIVE**, never a proven losing strategy. Do not automatically copy M5 parameters or presume nonzero M15 signals.

**Causal execution / context:** M15 is the trading bar for M15 variants; all indicators/signals/orders/protection/position events respect M15 completed-bar availability, T10 and T15 research delay semantics and intrabar uncertainty. M5 children may support verification or conservative event observation only under an explicitly authorized, non-look-ahead execution contract; do not call an M5 fill an M15 Open without declaring it. For H1 context, use exact completed children from one continuous session with explicitly verified availability; no native-H1 clock assumption, gaps, interpolation or stale fallback. Keep the same four MOEX perpetual instruments, full usable 2023 development windows, C1, month/unknown accounting and protected 2024 WF / 2025+ TRUE OOS.

**Historical distinction:** prior VWAP/Session Momentum Stage 2 tested **M5 execution throughout**: VWAP standalone M5 plus M30→M5 and M15→M5 filters; Momentum standalone M5 plus M30→M5 and H1→M5 filters. They were **not** tested as standalone M15 signal/execution engines. Their accepted `NO ECONOMIC BASELINE PASS / REJECT` remains binding **for tested M5/MTF architectures only**. This decision does not reopen those frozen studies or authorize new VWAP/Momentum experiments.

## Final bounded Stage 2 closeout — 2026-10-09

**VWAP Mean Reversion: NO ECONOMIC BASELINE PASS / REJECT CANDIDATE. Session Momentum: NO ECONOMIC BASELINE PASS / REJECT CANDIDATE.** This final rejection covers the retained M5 architectures and the completed, predeclared derived-M5 M30/M15/H1 tests. See [final causal MTF assessment](reports/STAGE2_CAUSAL_MTF_FINAL_REPORT.md) and [all comparisons](results/stage2_causal_mtf_v1/architecture_comparison.csv). Internal independent-algorithm verification is complete; external acceptance of this Draft remains pending the user's independent audit.

The current user task explicitly authorized this bounded 2023 MTF batch after readiness PASS. **Derived context PASS:** exact completed children only, same window/day, no gaps/reconstruction, M30 availability >= T+35m (T15 stress >= T+40m). Native FINAM higher-TF delivery remains unproved/blocked and is not used. 128 fixed runs include unchanged M5 comparators and their T15 sensitivities; no parameter grid. MTF improves a few known subsets but does not establish adequate trades, stable months, instrument diversity or delay resilience. Full annual Net/PF/DD remain null; the original 82 unknown outcomes and all PR #443/#447/#449/#450 freezes are unchanged.

**Research scope is complete for both candidates; neither advances to Stage 3.** Volatility Squeeze Breakout is the next roadmap recommendation only: **NOT IMPLEMENTED / WAIT FOR A SEPARATE USER DECISION AFTER INDEPENDENT AUDIT.** No merge, LIVE, 2024 WF/2025+ reads or protected-tree changes. The prior decisions below are historical provenance, not the current OPEN status.

## Historical PR #450 M5-only result — 2026-10-09

**Tested M5-only architectures: NO ECONOMIC BASELINE PASS / REJECT THESE M5 VARIANTS. VWAP and Momentum as strategy candidates remain OPEN for their final bounded Stage 2 MTF assessment.** [Frozen economic report](reports/STAGE2_COMPLETE_ARCHITECTURES_REPORT.md) documents 48 primary fixed-rule comparisons and 48 delay checks, the payable-entry follow-up, and exit-only attribution; its original M5-only `NO ECONOMIC BASELINE PASS / REJECT CANDIDATE` conclusion describes **only the tested scope**, not an independently verified MTF rejection. GLD closed subsets lack stable months/trades or delay resilience; annual Net/PF/DD remain null and 82 original unknown paths are untouched. Native M30 OHLCV composition matches on complete 2023 buckets but its delivery/finalization contract is unproved; **native MTF remains BLOCKED**. Stage 3/WF/OOS/LIVE/merge remain unauthorized. **Do not begin Volatility Squeeze Breakout until both VWAP and Momentum have a final independently audited Stage 2 decision, including the MTF comparison or a documented inability to perform it accepted by the user.**

## User decision — complete VWAP and Momentum BEFORE other strategies (2026-10-09)

**Binding research order:** complete the two current strategy candidates **VWAP Mean Reversion** and **Session Momentum** before opening any Volatility Squeeze Breakout or other new strategy work. PR #450 has **rejected the tested M5 architectures only**: neither candidate is finally rejected while its predeclared MTF context has not been tested. Do not conflate inability to establish the *native* M30 delivery timestamp with proof that all causal, locally constructed higher-TF context is impossible.

**Next minimal Stage 2 work (not Stage 3):** (1) Declare and independently validate a conservative **derived-from-completed-M5 M30 context**: six exact consecutive M5 children with all OHLCV known, aligned to a full 30-minute bucket entirely within the same approved research session, never bridge gaps/lunch/day; earliest availability is **no earlier than delivery of the last child under the declared M5 t+10 contract**, with strict future-signal use. This is a **new, explicitly labelled causal derived-context assumption**, NOT evidence of the unproved native M30 feed delivery. Validate against native M30 for 2023 where complete, keep all incomplete buckets ineligible, independently test no look-ahead, stop/exit causality, timing stress and missing paths. Keep native M30 replay blocked pending actual delivery/finalization evidence. (2) After an independent readiness PASS **and explicit MTF experiment authorization**, test a small predeclared set of **M30→M5 strategy architectures for each VWAP/Momentum**, against their unchanged M5 economic comparators. (3) If meaningful and separately justified, do the roadmap's **M15→M5 VWAP** and **H1→M5 Momentum** secondary causal comparisons with the same fully completed-child/delivery contract; no broad mixes or numerical grids.

**Final gate for each strategy:** judge after C1 expectancy, the PF≥1.6 (preferably ≈2.0) research goal, sufficient and diverse trades, calendar-month consistency, drawdown/concentration, T15 delay and cost stress, and missing-path/coverage status. Retain every negative result and refuse full-year PF/PASS if incomplete. If the bounded completed MTF research remains economically negative, record final **REJECT VWAP / REJECT MOMENTUM** and only **then** propose Volatility Squeeze Breakout. If MTF cannot be run honestly, document the precise technical block and request the user's explicit closeout decision before moving on. Never manufacture M5 bars or study gap repair, change C1, shorten 2023, inspect 2024 WF/2025+ TRUE OOS, touch TradingSystemLab or auto-merge PRs.

## Canonical Stage 2 / Stage 3 research method (user decision, 2026-10-09)

**Stage 2 = fully design, test and independently validate complete economically viable Baseline strategies, continuing through reasoned architecture alternatives until a repeatable positive-performance plateau is observed (or the candidate is rejected). Stage 3 = bounded numerical parameter optimization of that independently accepted Baseline architecture and its evidence-backed plateau.** Keep the existing roadmap stages 0–7; this decision changes the research division of work, not their number or the status/authority of existing runs.

- **Stage 2 complete strategy construction:** For each potential strategy, diagnose where money is earned/lost (signal context, causally knowable MFE/MAE, Stop/Take/time exits, failed breakouts, C1, latency and unknown paths), then test a **complete trading system**, not a bare entry pattern. The research toolbox may include justified entry/quality filters, market regimes, ADX with directional DI, ATR, EMA or other evidence-motivated indicators, approved causal MTF context, session/time conditions, volatility bounds, adverse-execution guards, initial/protective Stop, Take, max holding, break-even, trailing, partial exits and other bounded position-management rules. No element is mandatory and no combination is presumed useful. Freeze each complete hypothesis **before** testing and evaluate changes separately where feasible to establish their contribution. Indicative indicator periods (e.g. 14/14/50) are fixed research defaults, **not** authorization for a numeric grid. Diagnose both cut-loss and let-profits-run opportunities; do not add complexity for its own sake.
- **MTF within Stage 2:** M30→M5 is the primary context candidate; M15→M5 for VWAP and H1→M5 for Momentum are secondary comparisons already on this roadmap. M5 is the signal/execution frame; inputs from higher TF must be completed, delivered, session-aligned and causally available. **MTF data/finalization/composition readiness is still blocked and requires a separate audit and explicit authorization before any actual MTF backtest.** Documenting MTF as Baseline architecture does not lift that gate.
- **Baseline architecture comparisons and plateau:** Freeze the full strategy, indicators, MTF assumptions, entry/exit rules, numeric defaults, instruments, C1 and immutable run manifest *before each bounded 2023 development test*. Iterate through **successive individually justified complete architectures** where economically necessary; keep negative trials and frozen v1/v2 as comparators. A Stage 2 *pre-optimization plateau* is repeatable favorable economics across the available months/trades and relevant instruments/regimes, with non-fragile results under a **few predeclared small execution/cost or architectural sanity checks**. A single lucky backtest or narrowly peaked PF is **not** a plateau. This is preliminary viability evidence, **not a parameter-neighborhood optimizer or a substitute for Stage 4 Robustness**. No combinatorial grid, numerical sweep, cherry-picking or forced trade quota.
- **Desired Stage 2 economic acceptance:** target **Net PF >= 1.6 after C1**, preferably approaching **2.0 or higher**, together with **positive Net expectancy**, sufficient independently accounted trades, controlled drawdown, acceptable worst month and losing-month streak, reliable opportunities and a high share of positive **calendar** months. These are research goals, **not guaranteed outcomes**, standalone numeric PASS triggers or permission to select the best-looking configuration by 2023 PF. Assess all available calendar months and instruments with explicit NO_COVERAGE/UNRESOLVED labels; if unknown paths prevent complete Net/PF/DD, leave those metrics null and withhold research PASS. Favor stability and honest completeness over headline PF.
- **If a strategy fails:** diagnose and try a **bounded sequence of independently motivated, separately versioned architecture improvements**, covering entry quality, regimes, justified indicators/MTF and exits when supported by evidence. Do not claim Stage 2 success or move an isolated positive spike to Optimization. If a candidate still lacks a profitable baseline plateau, **reject/pause it and investigate the next strategy** with the same complete Stage 2 process: Volatility Squeeze Breakout is next on this roadmap; Liquidity Sweep / False Breakout remains reserve-only and requires explicit approval; further simple candidates likewise require separately approved scope. Preserve all rejected trials; never force PF by broad retrospective fitting. There is no guarantee a profitable plateau exists.
- **Stage 3, and only then:** after a specific complete Stage 2 architecture **and its preliminary stable-profit plateau** receive independent audit and explicit approval, optimize a **small predeclared set of its numerical parameters**. Do not reinvent signals, add indicators/MTF or repair an unprofitable strategy via a broad search under the name of optimization. Maintain immutable baselines; afterwards follow the existing **Robustness → Walk Forward (reserved 2024) → separately authorized TRUE OOS (2025+)** lifecycle.
- **User's latest Stage 2 priority / missing-data stop rule (2026-10-09):** **Do not commission further missing-M5/M15-gap restoration or forensic tasks as a prerequisite to strategy research.** PR #449 independently reviewed 82 unresolved opened-position outcomes and left them unresolved; that limitation is retained verbatim with `Net=null` for unknown paths, no hypothetical fills, no invented full-year PF or completeness PASS. **Proceed with economic improvement research on the known causal 2023 price paths**, keeping closed-only results visibly diagnostic, same source, C1 and same experiment accounting. A strategy hypothesis may fail or improve without resolving missing bars; unknowns do not become profit or zero. If later economic qualification demands more complete evidence, state that limitation explicitly rather than quietly altering observations or launching another data-gap study.
- **Next Stage 2 strategy research, authorized as a research direction (not completed):** first generate an independent **profit/loss attribution** across available 2023 runs (Net R and C1 by exit reason, hold time, entry delay, time of day, direction, instrument, regime; causally knowable MFE/MAE and subsequent excursion while known). Test the contribution of **initial Stop/Take, cost-adjusted take distance, earlier loss protection, time exit, break-even, trailing or profit-running exits**, maintaining session-flat rules and strict causal execution. Then construct **explicitly versioned fixed-rule VWAP and Momentum Baseline architectures** incorporating justified candidate ADX/+DI/-DI, ATR, reserve EMA and **MTF M30→M5** (secondary M15→M5 VWAP / H1→M5 Momentum), individually or in a small staged, predeclared comparison. Check causal higher-timeframe bar integrity/finalization as part of MTF readiness; this is **not** a renewed missing-position-path recovery project. No parameter grid or strategy-choice feedback from 2024/2025+.
- **Reject-and-replace rule:** if complete VWAP/Momentum variants do not show a credible profitable 2023 Baseline plateau (target after-C1 PF >=1.6, preferably >=2.0, positive expectancy, robust months and realistic costs), record a `REJECT / NO BASELINE PASS` conclusion and move to the next authorized strategy, **Volatility Squeeze Breakout**. Do not send loss-making architectures to Stage 3 or keep adding filters until a single historical PF spike looks good.
- **Current state/permissions:** PR #449's corrective reporting and the original v1/v2 remain historical and unmerged, with 82 unknown paths; indicators/MTF/exits are next **Stage 2** research candidates, not yet tested. Real MTF replay must first satisfy its existing causal source/finalization/approval gate; this user direction does not authorize live orders, 2024 Walk Forward, 2025+ TRUE OOS, mass sweeps or PR merges. PR #444's outdated *Stage 3-only* indicator classification is superseded and must be reconciled before merging either documentation branch.

**Corrective v2 (2026-10-09):** Separate [conditional observed-bar Baseline](reports/STAGE2_M5_CONDITIONAL_V2_REPORT.md), stacked on unmerged PR #443. Frozen v1 parameters/config/results retained; 2,140 model entries (+1,993), 2,058 accounted trades, 82 unknown position paths, 61 NO_BAR_NO_MODEL_FILL, zero missing-entry year latch. Derived B−25 submission / B−20 scenario / B−10 nominal acknowledgement. Execution model PASS with source/arithmetic audit and 100 executed tests; **research completeness NEEDS FIX; both strategy economic verdicts INCONCLUSIVE; all full annual Net/PF/DD null**. NO_COVERAGE preserved; no tuning, protected-tree changes, merge or WF/OOS/LIVE. Historical v1 state below remains separately reproducible.

Decision: **2026-10-08**. Independent intraday research on MOEX perpetual futures. **Only IntradayLab/ may be changed.** This roadmap does not authorize real orders or affect the production TradingSystemLab robot.

**Historical v1 audit gate (2026-10-09):** Independent settings re-audit [STAGE2_M5_STRATEGY_SETTINGS_REAUDIT_20261009](reports/STAGE2_M5_STRATEGY_SETTINGS_REAUDIT_20261009.md) found a failed annual research acceptance despite deterministic code/artifact checks. 93.2% signals blocked after 8 missing-target unknown orders; CNY early-2023 ATR/tick economics and VWAP reward-vs-C1 are poor. Original baseline manifest and result artifacts remain frozen for provenance. Stage 2 needs a bounded 2023-only input/execution audit and separate predeclared candidate variants; **NO PR #443 MERGE, NO Stage 3, NO MTF/WF/OOS/LIVE**. Only IntradayLab may change.

## Approved research outcome targets — user decision, 2026-10-10

**Apply these goals to future IntradayLab strategy candidates; they do not retroactively change any frozen v1/v2/VWAP/Momentum results or mean an existing strategy passed.** The central objective is **consistent positive net CALENDAR months** as a prospective research aspiration, not a guaranteed or mechanically enforced 12/12 promise. Negative days and weeks are acceptable; record the worst month, negative-month counts/streak, months without trades, drawdown and recovery. Do not cherry-pick months or change entries/exits at month-end to force positive outcomes.

- **Profit Factor:** after the IntradayLab **C1** cost model, **Net PF >= 1.6 is the minimum research acceptance target**, with **Net PF > 2.0 preferred**. Require credible sample size and monthly/instrument diversity; a high PF on a handful of trades does NOT qualify.
- **Reward/risk and expectancy:** target **planned net reward-to-initial-risk >= 3:1** for the proposed trade (equivalently risk:reward 1:3 or better), with reasonable Stop/Take geometry and dated C1 considered; separately report **realized** average-win/average-loss ratio and realized Net R after stop, early exit, trailing and costs. **Positive mathematical expectancy after C1 is mandatory**; a projected 1:3 does not imply positive expectancy, and neither a nominal 3R take nor PF on its own constitutes PASS.
- **Frequency:** **2–3 trades per trading day is an indicative opportunity goal, NOT a quota and NOT pre-assigned per instrument versus all four together**. Determine realistic frequency empirically for each instrument and the combined candidate portfolio, showing entries/day, active trade days, monthly frequency, no-trade days and the economics of each. Fewer trades are acceptable when they improve quality; do not raise frequency by lowering signal quality or add arbitrary entry triggers. No hindsight-based cadence tuning.
- **Risk/stability:** controlled drawdown, acceptable recovery, no dependence on one/two very large winning trades, nonfragile execution-delay/cost behavior, and consistency across observable 2023 months and instruments. Avoid forcing a portfolio selection from a 2023 backtest; compare separate instruments and combined exposure only when portfolio accounting is properly defined.
- **Evidence gate:** targets are research criteria, never performance guarantees. Preserve missing outcome/coverage as UNKNOWN/NO_COVERAGE and full annual Net/PF/DD as null where not provable; do not call a closed-only PF, selected months or a small sample a complete Baseline PASS. Preserve Stage 2 → Stage 3 bounded optimization → Robustness → reserved 2024 Walk Forward → separately authorized 2025+ TRUE OOS, with no LIVE permission.

**Current sequencing (2026-10-10):** final VWAP/Momentum audit is complete and accepted through Merge #454. Both candidates are rejected; their artifacts stay frozen. The user authorized the bounded Volatility Squeeze Breakout task above. These targets do not authorize robot/protected-tree changes or Stage 3.

## Research target

Build a moderately aggressive, after-cost intraday system with a high fraction of **positive net calendar months** (12/12 is an aspiration, never a guarantee). Negative days/weeks and some negative months are possible. Evaluate profitability, worst month, consecutive losing months, total and monthly drawdown, time to recovery, sufficient independent opportunities, trading costs, and capacity to fund future withdrawals. Never increase risk or manipulate month-end exits to force a positive month.

**Current cadence decision (2026-10-10):** about 2–3 trades/day is only a flexible research benchmark; **no required quota per instrument or combined portfolio**. The earlier provisional 5–15/week aggregate and 1–3/day per-instrument suggestions are historical, superseded by observed-results-based evaluation. Report actual frequency and its economics without forced entries.

## Frozen initial research scope

**Instruments (perpetual MOEX futures only):**
- USDRUBF
- CNYRUBF
- GLDRUBF
- IMOEXF

**Source:** read-only repository alkospacer123/market-pattern-data, path forever/{INSTRUMENT}/{INSTRUMENT}_{TF}.csv. At inventory inspection, market-pattern-data main = f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8.

**Available files verified by GitHub directory listing (16/16):**

| Perpetual instrument | M5 | M15 | M30 | H1 |
| --- | --- | --- | --- | --- |
| USDRUBF | present | present | present | present |
| CNYRUBF | present | present | present | present |
| GLDRUBF | present | present | present | present |
| IMOEXF | present | present | present | present |

**Current evidence:** the pre-2025 data-content audit has now been performed; see [Stage 1 Data Audit](reports/STAGE1_DATA_AUDIT_20261008.md). M5 data begin 2023-01-03 (USDRUBF/CNYRUBF), 2023-07-11 (GLDRUBF), 2023-11-14 (IMOEXF). Basic OHLC/timestamps/tick tests pass, but the 2024-08-16 IMOEXF M15 evening interval has 20 M15 bars without M5 counterparts. The exporter has now attested FINAM / MSK UTC+3 / start-label; delivery/finalization, bounded historical sessions, funding/margin and intrabar execution remain application-specific gates; **Stage 1 is not complete**.

**Historical status before Stage 2 authorization, 2026-10-09:** Stage 1.2 Historical Sessions & MTF Integrity is **COMPLETE**, [PR #439](https://github.com/alkospacer123/market-pattern-discovery/pull/439) **MERGED**, independent audit PASS. Its historical [report](reports/STAGE1_2_SESSION_MTF_AUDIT.md) and JSON retain their original pending-audit status for reproducibility. Real M15/M30/H1 contexts remain blocked: the new exporter attestation of clock/start-label does not establish delivery/finalization, full session evidence or composition integrity. The [Execution, Costs & Funding Specification](reports/STAGE1_EXECUTION_COSTS_SPEC.md), [PR #440](https://github.com/alkospacer123/market-pattern-discovery/pull/440), is **MERGED**, independent re-audit PASS at `79f974b570e7b8037ef426eba41d4e48793375ee`. Its historical report is retained unchanged. The user approved independent IntradayLab **C1** for the initial Baseline: one instrument-specific tick per executed entry and exit, **2 ticks per closed round trip per contract** at an unchanged tick size. No exchange/broker fees, spread or slippage are charged on top; funding, failed close, gaps and margin remain separate. Higher-cost scenarios are separate sensitivity checks replacing C1, never combined with actual-tariff scenarios. It documents the CNY tick change from 19:00 MSK 2023-09-27: each fill uses its dated tick value, not the modern grid for all history. Current-tick checks alone do not validate the older CNY grid. The actual FINAM tariff will be selected after trade-count/frequency/turnover statistics; its unknown status alone does not block research with C1. Historical margin/funding, delivery/finalization, Volume and execution evidence remain unresolved; CSV source/clock/start-label now have direct user-exporter attestation, not automatically verified FINAM metadata. Historical funding clearing around 18:50 must not be replaced by the 23:50 boundary introduced in 2026. Preserve the existing IMOEXF quarantine; **Stage 1 OPEN**, Stage 2 NOT STARTED. No TradingSystemLab model or code is imported.

**Historical M5 clock confirmation before Stage 2 authorization, 2026-10-09:** [STAGE1_M5_CONDITIONAL_FOR_BASELINE](reports/STAGE1_M5_CLOCK_CONFIRMATION.md), pending independent audit and explicit approval of bounded assumptions. The user personally exported all 16 CSVs through FINAM with identical settings: MSK UTC+3, start-label. Limited M5 controls agree with known MOEX exceptions; independent FINAM re-export unavailable (proxy 403), so no automatic metadata certification. All four instruments are **CONDITIONAL**; currently zero Baseline bars authorized. Preserve the daytime-only scope, USD/CNY 31.08.2023 gap and IMO quarantine. Before Stage 2, confirm/approve finalization at t+10m, selected continuous daytime windows, modelled fills/nonfills and residual risk, and Volume weights/liquidity; margin/limits gate capital and quantity claims, never default q=1. A normalized/conditional-contract study is only a proposal needing separate approval. After independent audit and authorization, propose VWAP Mean Reversion M5-only and Session Momentum M5-only first; all MTF hypotheses remain in this roadmap without automatic authorization. The historical [PR #441 report](reports/STAGE1_M5_READINESS.md) is unchanged; PR #441 MERGED. Stage 1 OPEN, Stage 2 NOT STARTED.

**Current Stage 2 authorization/result, 2026-10-09:** the user explicitly approved the bounded M5-only research model: FINAM / MSK UTC+3 / start-label, availability no earlier than t+10m, the existing daytime windows, PR #440 conditional fills/residuals, C1, relative Volume weights and normalized price analysis without actual GO/equity sizing. **STAGE2_M5_BASELINE_NEEDS_FIX_RESEARCH_AND_SETTINGS**: [report](reports/STAGE2_M5_BASELINE_REPORT.md), immutable [manifest](config/stage2_m5_baseline_v1.json), exactly **2 strategies × 4 instruments = 8 runs**, M5 **2023 only**, using each instrument's entire available 2023 history. 147 conditional model entries; 135 fully accounted trades; 12 trades with unresolved consequences plus 8 unknown-entry orders (20 unresolved cases). 7,279 later signals blocked, including 6,032 otherwise eligible entry attempts; 8 of the original 61 cases remain unknown and 53 are not submitted. Known terminal model units are zero, possible unknown residual units are null and full FLAT is unconfirmed. Full annual Net/PF remain unavailable. 12 known-position plus 8 unknown-order B−10 breaches; 85 synthetic tests PASS and deterministic replay. PR #443 corrected after independent NEEDS_FIX: absent target OHLCV preserves an unknown possible entry and blocks new entries through 2023 end; previous evidence retained in correction_history.json/Git e38e018. Fixed manifest and parameters unchanged; pending independent re-audit. **Stage 1 remains OPEN outside the approved M5 subset; no full 16-file/MTF or real execution readiness.** 2024 reserved WF and 2025+ TRUE OOS physically unread. No optimizer, extra strategies, capital returns, LIVE or next-stage authorization.

**Timeframes:** M5 for signals and price-based execution simulation. M15 / M30 / H1 are candidate *context* timeframes; **M30 -> M5 is the lead hypothesis**, not a preselected winner. Research is strictly intraday. No M1 or M3/M10 data or M1 execution assumptions. No order-book strategy: **Order Flow Imbalance excluded** because historical order-book data is unavailable.

**Initial strategies, in sequence:**
1. **VWAP Mean Reversion** — M5 standalone; M30 -> M5 principal MTF comparison; M15 -> M5 secondary comparison. VWAP is session-anchored. If only OHLCV bars are available, label volume-weighted typical-price VWAP as an approximation, not an observed transaction VWAP. Assess the risk of countertrend entries.
2. **Intraday / Session Momentum** — M5 standalone; M30 -> M5 principal MTF comparison; H1 -> M5 secondary comparison. Measure session- and instrument-dependent continuation without forcing an H1 holding period.
3. **Volatility Squeeze Breakout** — **after** the first two strategies are assessed: M5 standalone versus M30 -> M5. Test whether it adds independent portfolio value beyond Momentum.
4. **Liquidity Sweep / False Breakout** — reserve hypothesis only, not part of initial implementation, subject to a later explicit scope decision.

First-cycle roadmap comparison envelope: **6 strategy/architecture variants x 4 instruments = up to 24 runs**, conditional on their Step 1 quality gates. The current explicitly approved Stage 2 subset is exactly **two M5-only strategies x four instruments = 8 runs**; the four context architectures remain blocked and unstarted. These are predeclared comparisons, not optimizer output. The later Squeeze pair would add up to 8 runs only if explicitly started. Do not multiply variants or optimize timeframe choices using TRUE OOS. Further independently proposed strategies/architecture revisions require separate approved scope and are not silently added to this original matrix.

**MTF causality:** use only the last fully closed higher-timeframe bar available at each completed M5 signal. Check time-zone, session anchoring, resampling agreement, trading halts/gaps, and boundary resets. Source M5 is the finest available bar: same-bar stop/target ordering is ambiguous; model conservatively, stress alternatives or flag unresolved cases. Do not invent M1-level precision. Validate any backtest fills against the actual execution mechanism and available bid/ask information.

## Second-wave Stage 2 candidate queue — revised 2026-10-10

**PLANNED / NO NEW STRATEGY TESTED OR AUTHORIZED.** Three old families VWAP Mean Reversion, Session Momentum and Squeeze (four fixed variants, PR #456/#457 MERGED) failed economic qualification in tested scope. Frozen code, configurations, tests and results remain immutable. This updates the preliminary PR #458 shortlist BEFORE its merge: Range Rotation has a known range-width limit conflicting with 3R in many cases; Opening Drive Pullback is a subset of swing pullback with fewer session opportunities. These are DESIGN exclusions, NOT measured empirical failures. [Independent selection memo](reports/STAGE2_NEXT_STRATEGIES_SELECTION_20261010.md).

| Priority | New M5 architecture | Causal, observable entry hypothesis | Specific falsification |
| --- | --- | --- | --- |
| **1 — first** | **LEVEL_REJECTION_M5 — Failed Level Test / Reclaim** | A previously completed same-window high/low exists before the test. A later completed M5 breaches it but closes **back inside**, allowing an opposite-direction entry on a future admissible delayed M5 Open; Stop outside actual rejection extreme. | Late T10/T15 reclaim, stop too wide, few valid after-C1 3R opportunities. No claims of observed stop orders. |
| **2** | **LEVEL_BREAKOUT_RETEST_M5 — Accepted Break + Retest** | Previous known level breached and subsequent completed M5 closes **outside**; do NOT trade the first breakout. Wait for separately completed retest and renewed direction confirmation, then enter later eligible Open; Stop behind retest. | Multiple waits + delayed execution may consume available movement before session flat. Not rejected Momentum first-breakout entry. |
| **3** | **SWING_PULLBACK_M5 — Structural Intraday Trend Pullback** | Direction from previously completed persistent swing structure; a later corrective retreat and further completed resumption confirmation, WITHOUT a qualifying accepted level breakout/retest; structural correction Stop. | Swing noise, late continuation, excessively broad Stop, redundant retest events. |

These are THREE separately preregistered hypotheses, not parameter variations. A failed breakout closing inside must never equal an accepted breakout closing outside. Accepted-break retests must not also count as generic swing continuation. Declare signal identity, event expiry, overlap/position-busy handling and past-only deterministic level/swing definition BEFORE any counts.

**All ten target criteria preserved:** aspirational combined 2–3 trades/day (not a forced order quota); desired C1 Net PF >=1.6, preferably >2.0; positive net expectancy; planned after-C1 1:3 risk/reward; highest credible positive **calendar-month** share (ideal 12/12, NOT guaranteed); controlled drawdown/recovery; no reliance on top one/two trades; steady monthly opportunity and no-trade-day disclosure; T15 and C2 stress resistance. Neither isolated PF nor setup count creates Stage 2 PASS.

**Cost-exact 3R clarification for NEW candidates only:** with gross initial Stop distance s, one-side historical tick t, directional gross Take distance d, the previously used metric net-win / gross-price-risk = (d−2t)/s, so >=3 means d>=3s+2t. But the more literal requirement net-win / net-Stop-loss AFTER C1 = (d−2t)/(s+2t) gives d>=3s+8t, assuming ideal Stop execution without adverse gap. Report **both**; choose the conservative fully-net 3:1 for these new hypotheses before looking at any P&L. Never retroactively reinterpret frozen old strategies. A target level is theoretical, not proof of future profit.

**First: bounded, separately approved opportunity/geometry preflight WITHIN existing Stage 2, NOT another stage.** For ONE candidate predeclare objective level/swing and Stop/target grammar, expires/dedup, before seeing even event counts. Scan all physically available original 2023 M5 from market-pattern-data/forever for USDRUBF, CNYRUBF, GLDRUBF, IMOEXF; do not shorten dates or read 2024 Walk Forward / locked 2025+ TRUE OOS. Full causal funnel by symbol/session/direction/day/week/**calendar month**: prior-known event, completed signal, T10 and T15 observed readiness, first strictly future executable M5 Open, conditional eligible/nonfill/UNKNOWN, historical tick/Stop and both after-C1 3R target distances, safe time-to-flat, distinct/no-opportunity days and months and source NO_COVERAGE. **DO NOT** inspect any post-entry high/low, later Stop/Take/MFE/MAE, trading P&L/PF or profitable months in this screen; never tune to target trade counts. Target 2–3 DAILY COMBINED opportunities is only a guide and cannot be extrapolated from GLD/IMOEX pre-inception 2023 months. If too sparse/unpayable, report INSUFFICIENT OPPORTUNITY and STOP for user decision. Preflight PASS does NOT mean positive economics.

**Only after separate approval:** ONE complete fixed-rule Stage 2 Baseline with all available 2023, four instruments, T10 primary/T15 stress, C1 one tick/entry plus one tick/exit (two per round trip), C2 identical-fill replacement, conservative conditional future M5 Open, stops, gaps, UNKNOWN and intra-session flat. Independent trade/coverage/monthly audit and objective review of PF, expectancy, realized RR, positive-month frequency, drawdown, concentration and resilience. No optimizer grid, Stage 3, 2024 WF, TRUE OOS, LIVE or auto-next-candidate. No additional broker commissions in C1.

**Protection:** Only IntradayLab documentation changes in this PR; TradingSystemLab (including strategies, configurations, results, active production robot), other project trees and frozen old IntradayLab artifacts are NEVER changed. Historical restricted windows 10:00–14:00 and 14:05–18:50 MSK with dated exceptions, CNY historic tick transition, source gaps and later starts remain unchanged.

## Stages and exit evidence

| Step | Stage | Required deliverable / exit gate | Status |
| --- | --- | --- | --- |
| 0 | Separate project boundary | Research branch + IntradayLab folder, written constraints; protected trees unchanged | **COMPLETE** |
| 1 | Dataset and execution specification | Audited 16 CSVs: date coverage, timezone/bar timestamp meaning, schemas, duplicates, OHLC consistency, missing bars/sessions, volume, cross-TF agreement; venue calendar, actual instrument specs, tick/lot/margin, FINAM + exchange fees, spread/slippage/nonfill model; frozen pre-2025 development scope and TRUE OOS boundary | **OPEN outside approved M5 subset. Stage 1.2 and PR #440 complete/merged; FINAM/MSK/start-label attested by exporter. Limited Stage 2 model explicitly approved; full historical sessions/GO/funding/real fills and MTF remain unresolved** |
| 2 | Baseline | Build, freeze and independently assess complete causal architectures: signal, justified ADX/DI/ATR/EMA where needed, separately authorized MTF contexts, entry/Stop/Take/exit management, all with C1; compare predeclared fixed-rule variants; full trade/monthly/coverage evidence, positive Net expectancy and a preliminary stable after-C1 performance plateau (target PF >=1.6, preferably around 2.0); no numerical parameter grid | **M5-only NEEDS FIX (research coverage and settings audit) — 8 runs, 7,279 blocked signals (93.2%), 12 unresolved trade consequences + 8 unknown entry orders, full annual Net/PF unavailable. Not an accepted annual Baseline; MTF NOT STARTED** |
| 3 | Bounded Optimization | Only after independently accepted viable Stage 2 architecture and explicit authorization: optimize a small prejustified numerical parameter set with immutable manifests; no new signal architecture, mass search or PF-only ranking | **NOT STARTED** |
| 4 | Robustness | Parameter-neighborhood, instruments, session regimes, trading costs, widened slippage, ambiguous fills, adverse months, concentration and drawdown | **NOT STARTED** |
| 5 | Walk Forward | Chronological rolling tests with no future-informed decisions; frozen rules; monthly and portfolio comparisons | **NOT STARTED** |
| 6 | TRUE OOS | Single separately authorized final assessment on **untouched 2025+ data**, frozen finalists and costs, full calendar-month + instrument/portfolio reports | **NOT STARTED / LOCKED** |
| 7 | Forward observation and separate FINAM-account readiness | Read-only/paper monitoring; fully independent credentials, account bindings, sizing, order ledger, reconciliation, kill switch; explicit approval required for real orders | **NOT STARTED / NO LIVE AUTHORIZATION** |

**2025 onward is reserved TRUE OOS**: do not inspect its strategy performance or use it for training, strategy selection, dates, thresholds or parameter decisions before Step 6 authorization. In Step 1 determine the actual earlier shared history and freeze development/WF windows *without* reading protected performance. Never shorten periods ad hoc to improve metrics.

## Evaluation and decision logic

- Report **net** expectancy, PF, trade count, win rate, median holding time, spread/fee/slippage impact, drawdown, return and recovery for each instrument, architecture, year, and month. Initial Baseline results must be labelled **«прибыль после модельных издержек C1»**, not confirmed profit after actual commissions; report C1 as one aggregate cost without inventing its fee/spread/slippage breakdown. Include equity marked to market at calendar month end (with open-position P&L and costs); zero-return months are **not** positive.
- Report positive-month fraction, worst month, count of zero/negative months, longest losing-month streak, rolling 3/6/12-month returns, consistency of opportunities per week/month, and co-loss/correlation of standalone strategies. Compare risk-adjusted results at equal exposure and costs, not on trading frequency alone.
- MTF must add reliable net benefit versus M5 standalone; never assume a slower context always helps. After independent validation, consider an integrated portfolio only if it genuinely improves after-cost monthly stability and drawdowns.
- Intraday positions: specify a causal max holding time, planned flat/session-boundary policy and overnight-risk treatment *before* performance selection. Avoid silently changing holding rules to rescue monthly results.
- Moderate-aggressive study bounds, **not approved LIVE settings**: test 0.25–0.5% of the new account equity risk/trade, a 1–1.5% daily loss guard and 3% weekly guard; include one-contract floor, margin and correlations. No martingale/averaging down. Unaffordable integer positions are skipped.
- Separately stress-test net distributable profit, taxes, external transfers to TradingSystemLab, future living-expense withdrawals and reserves. Do not present this as guaranteed income.

## Isolation / approval rules

- Code, configs, documentation, generated results and logs for this research belong only under IntradayLab/; market-pattern-data/forever is read-only. The primary branch is **main**. IntradayLab changes are submitted through separate task branches and PRs into main with independent audit; research/intraday-lab is the historical setup branch, not the exclusive project location.
- **NEVER change TradingSystemLab/, its active robot/configuration/data authorities, BBW/, other project trees, or repository-root files.** Research ideas may borrow generic engineering discipline only; no imports of TradingSystemLab strategy parameters/results/credentials.
- Do not merge task PRs without separate explicit authorization, independent audit and protected-tree review. Creating a PR does not authorize merge or automatic research-stage advancement.
- After each task independently inspect the actual GitHub main and research branch, changed files and diff, repeatable results, and exact completion status. No advancement to the next stage without audit and approval.
