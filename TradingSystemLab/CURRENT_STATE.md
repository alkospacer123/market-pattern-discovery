# Current state — read first

> Persistent handoff snapshot. Accepted repository evidence commit: `f336303`
> (full SHA `f3363033db376ee654e7abb62aff1f77c5d19612`, branch `work`). The
> documentation descendants do not change research code or artifacts.

## Governing rule

The original H1 cycle and frozen H1 strategy identities are the sole authority
for every new timeframe: **Baseline → Optimization → Robustness → Walk Forward
→ TRUE OOS**. No stage may be added, skipped, borrowed from another timeframe,
or replaced by a later timeframe/MTF implementation.

## A. Repository evidence

- Project/version: TradingSystemLab; current accepted research artifacts include
  the original H1 lifecycle and the later historical v2 Phase 1 attempt.
- Original Baseline strategy identity: T2
  `T2_Trend_Pullback_Continuation_v1.0`, source default
  `max_initial_stop_atr = 3.0`; T3 `T3_MTF_Trend_v1.0`, source default
  `ema_period = 100`. The original unified H1 baseline covers Si/CNY, H1,
  2023-01-01 through 2024-12-31, with C1 primary and C0/C0.5/C1/C2 reporting.
- Original post-Optimization frozen candidates: `T2_candidate_v1`, configuration
  `T2-0007-608dc87d09f1`; and `T3_candidate_v1`, configuration
  `T3-0014-0050d828c1a8`. The Phase 3.3 registry records candidate values 2.5
  and 75 while separately recording baseline defaults 3.0 and 100. This
  distinction must be preserved.
- Historical v2 Phase 1 used T2 parameter hash
  `2b0494cdd24bfbfa8ce7d657d6f83d1408f07b9f565d38d093dec5b4856e3c00`
  (2.5) and T3 parameter hash
  `938b6b3b78f680010115a204b9a49e7eef962db119f4ea121e388c00741920ba`
  (75). Those hashes identify only that historical attempt, not the corrected
  Baseline.
- Calendar year 2025 is locked TRUE OOS and may not be read before its
  preauthorized final stage.

## B. Historical unresolved findings

- `results/baseline_v2/Baseline_Audit_Report.md` records **FAIL / PHASE 1
  BASELINE — NOT COMPLETE**: absent per-instrument-spec integration, absent
  `source_hash` and `instrument_spec` in 24 run manifests, a slippage-field
  naming discrepancy, and two protected-tree hash failures.
- That audit is preserved as evidence about v2 Phase 1. Its instrument-spec
  recommendation does **not** control the current roadmap and is not a blocker
  for the canonical cycle.
- Root `ROADMAP.md` calls Phase 7.3 current although its result manifest records
  completion. This conflict remains historical provenance.

## C. Current approved research direction

- **Current phase:** corrected **Baseline**, specified from the original H1
  Baseline methodology and frozen T2/T3 strategy identities; status **approved
  to execute, not yet executed or audited**. This is research, not Phase 1.1
  instrument-spec remediation.
- **Current corrected Baseline identity:** T2 source default 3.0 and T3 source
  default 100. The historical v2 hashes do not apply. Exact run manifests must
  bind the complete parameter sets and computed hashes when the rerun occurs.
- **Data scope:** reproduce the original H1 Baseline scope: Si and CNY, native
  H1, development-only 2023-01-01 through 2024-12-31. No 2025 read.
- **Costs/execution:** reproduce original H1 cost scenarios with C1 primary;
  retain `FROZEN_TICK_SIZE = 0.001` for **all instruments**, with no
  instrument-specific substitution, throughout the entire current five-stage
  cycle.
- **Last accepted historical phase:** original H1 lifecycle artifacts remain
  committed; the later v2 Phase 1 attempt was generated but audit-failed and is
  not an accepted replacement Baseline.

## Next permitted action

Execute the corrected Baseline under the original H1 methodology with the
identity, scope, costs, and frozen tick size above; then perform an artifact
audit under `AUDIT_PROTOCOL.md`. Proceed to Optimization only after that
Baseline is accepted by audit.

## Forbidden next actions

- Do not proceed to Optimization, Robustness, Walk Forward, or TRUE OOS before
  the preceding canonical stage is executed and accepted.
- Do not access 2025/TRUE OOS, optimize, rank, select, chase PF, or silently
  alter strategy logic or parameters during Baseline.
- Do not replace `FROZEN_TICK_SIZE = 0.001`, make instrument-spec remediation a
  prerequisite, or route this cycle through a Phase 1.1 remediation branch.
- Do not treat the v2 2.5/75 overrides as original Baseline defaults or rewrite
  historical artifacts. Do not mix BBW, Round Level, or Touch Optimization work.

## Update rule

Update this file after every **accepted** research phase or major audit—not
merely when Codex generates output. Record the exact accepted commit, current
and last-completed phases, frozen candidate identity, methodological authority,
data scope, costs, `FROZEN_TICK_SIZE`, unresolved historical findings, next
permitted action, and forbidden actions.
