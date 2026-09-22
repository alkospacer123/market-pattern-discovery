# Current state — read first

> Persistent handoff snapshot.  Research-state base HEAD: `f336303` (full SHA
> `f3363033db376ee654e7abb62aff1f77c5d19612`, branch `work`).  This documentation-only descendant does not change
> research state or artifacts.

## Repository state

- Project/version: **TradingSystemLab v2**.
- Latest research action: audit of v2 Phase 1 baseline.
- Authority: committed code, manifests, ledgers, metrics, and audit verdicts;
  conversation summaries are not project state.

## Current phase

- **Name:** Phase 1.1 — v2 baseline instrument-spec/provenance remediation.
- **Status:** `BLOCKED / NOT COMPLETE`; the generated matrix says complete, but
  `results/baseline_v2/Baseline_Audit_Report.md` is an explicit audit `FAIL`.
- **Type:** current task is infrastructure; underlying phase is baseline
  validation/audit remediation, not new research.
- **Provenance:** `baseline_v2.py`, `results/baseline_v2/manifest.json`, and the
  subsequent audit report.  This v2 line is separate from completed original H1
  and Phase 7 MTF generations.

## Frozen identities

| Strategy | Candidate/config ID | Parameter hash | Provenance |
|---|---|---|---|
| T2 | `T2_Trend_Pullback_Continuation_v1.0` / v2 Phase 1 | `2b0494cdd24bfbfa8ce7d657d6f83d1408f07b9f565d38d093dec5b4856e3c00` | `baseline_v2.py`; each `results/baseline_v2/T2/*/*/manifest.json`; strategy SHA-256 `376df085…9507774` |
| T3 | `T3_MTF_Trend_v1.0` / v2 Phase 1 single-timeframe mode | `938b6b3b78f680010115a204b9a49e7eef962db119f4ea121e388c00741920ba` | `baseline_v2.py`; each `results/baseline_v2/T3/*/*/manifest.json`; strategy SHA-256 `840dd3b2…ad9a8c` |

Do not substitute class/YAML defaults for these manifest-frozen v2 parameters.

## Data scope

- Instruments: `Si`, `CNY`, `GD`, `BR`, `MIX`, `NG`; timeframes: M30 and H1.
- Declared development range: 2020-01-01 through 2024-12-31.  Audited actual
  starts: most 2020-01-03, CNY 2022-04-21, NG 2020-02-03; all end 2024-12-31.
- TRUE OOS boundary: **2025-01-01** (`Europe/Moscow`); 2025+ is locked and must
  not be read during this remediation or any development phase.

## Costs

- Active v2 model: C1, 1 tick per side / 2 round-trip ticks, zero additional
  slippage.
- Current implementation incorrectly applies global `tick_size = 0.001` to all
  six instruments.  The audit states NG requires `0.01`; verified specs for
  GD/BR/MIX/NG are absent.  Do not guess them.

## Completed immediately before current phase

- v2 Phase 0 smoke: `PASS`.
- v2 Phase 1: all 24 runs generated; deterministic rerun and ledger/metrics
  consistency `PASS`, but overall audit verdict **PHASE 1 BASELINE — NOT
  COMPLETE** because instrument-spec/provenance requirements fail.
- Independent older line: Phase 7.3 manifest says
  `PHASE_7_3_TRUE_MTF_RESEARCH_COMPLETE`.

## Known blockers / unresolved issues

1. Verified contract specs are unavailable in the registry for GD, BR, MIX, NG;
   the v2 runner does not use per-instrument specs (including existing Si/CNY).
2. All 24 v2 run manifests lack `instrument_spec` and `source_hash`.
3. The extra-slippage key differs from the frozen contract wording.
4. `tests/test_execution_spec_audit.py` has two protected-tree hash failures.
5. Root `ROADMAP.md` still calls Phase 7.3 current although its own result
   manifest says complete; this handoff follows the later v2 audit evidence.

## Next permitted action

Verify authoritative contract specifications for the six v2 instruments, then
perform the audit-prescribed Phase 1.1 integration/provenance fix and tests.  Do
not change frozen T2/T3 strategy logic or parameters.  After those prerequisites,
rerun exactly the frozen 24-run development-only C1 matrix and fully re-audit its
artifacts.

## Forbidden next actions

- No optimization, PF chasing, ranking, selection, or new research.
- No TRUE OOS/2025 read, retuning, or repeated OOS probing.
- No guessed instrument specs, silent strategy/parameter changes, or acceptance
  of generated `COMPLETE` status over the audit verdict.
- No cross-use of BBW, Round Level, or Touch Optimization evidence/artifacts.
- No modification or copying of source market data.
