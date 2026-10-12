# STOP/TICK GRID V2: isolated release preparation

**PROPOSED / NOT DEPLOYED.** This extends the existing PR #493 candidate within Stage 8; it creates no new roadmap phase and grants no trading authorization. `LIVE_PRODUCTION_READY=NO`. `FINAM_FILL_AUTHORITY_VERIFIED=False` remains in force.

## Authority and scope

Preparation baseline: PR #493 `e59fd8d4676e94d84df0b585f40ec67401ac6ba0`. Initially observed GitHub main: `758a0ac1deda8bfa7aa1bc99d8a97a33a9357f02`; its advance from `5c78d15…` changes only `IntradayLab/ROADMAP.md`. Last **documented**, not re-observed here, Intel checkout: `184e8c2b8fa092a606249ff293a4f507160bff29`. Main subsequently advanced to `bc4f95f48b332f43d79ed10f26fc03c5ad01cd97` via #495, solely adding IntradayLab artifacts; TradingSystemLab remained unchanged. No Intel connection, credentials, LIVE database, Task, authorization or kill switch is used by this work.

Frozen production specification: `PROD_STAGE7_46DB784378797C7FB04636892350AFF21006D71A31F2CED9D4B974EDA2DC36B8`; strategy `T3-H1-4e73cdb77246`; active identity `TRAIL1__N4_01__FULL__R15`. N4, FULL/R15, raw signals, original TRAIL1 core and Stage 7/OOS evidence remain unchanged. Legacy is the default service profile. V2 schema is `stage8_12_production_runtime.stop_tick_grid.v2`, revision `STOP_TICK_GRID_V2_FILL_PROPOSED`.

## A. External snapshot dry-run

`release_preparation` accepts a separately supplied, standalone external SQLite snapshot and its SHA-256, exact source/candidate commits, authenticated account hash, fixed Stage5 data root, and a hashed broker observation file. It never obtains a LIVE snapshot itself. The observation is caller-supplied evidence, not a fresh physical acceptance claim. The exercised fixture is explicitly synthetic legacy service state with the real immutable Stage5 seeds; a real Intel snapshot was not provided.

Before creating output, it rejects canonical LIVE/runtime/state paths, repository paths, symbolic links, hard-linked snapshots, WAL/SHM/journal companions, changed hashes, noncanonical SQLite schemas, unidentified identities, unknown state keys, incompatible ledgers, pending signals, non-flat local/broker positions, active broker orders and unresolved intents. Broker account/status/time and realized-equity consistency are checked; unexplained financial discrepancies do not create a new equity authority. Contradictions, duplicate broker position rows and missing history authority fail closed.

The causal inventory preserved as original SQLite JSON text is:

- `production_service_identity` (specification, active identity, account hash, Stage5 commit);
- `realized_equity`, `starting_realized_equity`, `explained_external_cash_flows`, empty `production_positions`, `production_service_cycle_count`;
- all N4 `production_h1_continuation:*`, `production_expected_h1:*`, `last_evaluated_h1:*`, `last_managed_h1:*`, `signal_sequence:*`, `pending_signal:*` keys actually present.

Each symbol requires validated continuation authority and a last-evaluated watermark belonging to the exact immutable H1 history. Sequence counters are preserved; pending signals must be null/absent. Watermarks cannot exceed that history or the broker observation. Unknown keys require explicit review rather than silent omission.

`database_identity` is explicitly replaced with V2 identity only in a newly created isolated database. **Every legacy intent/fill remains in the byte-exact whole-database archive**; terminal ledger rows are validated but are never rewritten into V2 executable rows. V2 starts with empty intent/fill tables, preserved causal state, archive metadata and a sticky `HALTED / OPERATOR_INTERVENTION_REQUIRED` state. No old signal is processed and no entry is planned/submitted. Restart validates the actual V2 runtime identity; rollback restores the complete original database and verifies its hash and all state/ledger rows. Source bytes do not change.

The dry-run CLI operates only on already supplied external files:

```text
python -m TradingSystemLab.stage8_robot.release_preparation \
  --snapshot <external-standalone-snapshot> --snapshot-sha256 <sha256> \
  --out <new-isolated-output> --stage5-data-root <exact-Stage5-checkout> \
  --broker-snapshot <external-observation.json> --broker-snapshot-sha256 <sha256> \
  --account-hash <sha256-account-id> --source-commit <40-hex> --candidate-commit <40-hex>
```

This is not automatic LIVE migration. Source commit provenance is supplied by the operator; a synthetic fixture or a valid hash does not prove which Intel checkout created a real snapshot.

## B. Explicit, closed service selection

`release_candidate_runner` dispatches through the actual `production_service.run_from_environment()` and selects `ProductionService(execution_revision=V2)` only with a manifest, its SHA-256, `--once`, exact current checkout commit, frozen identity/schema, matching account/data paths and committed source-file hashes. Mutated state/archive/code, wrong commit/revision/account, symlink/hardlink/WAL aliases and an existing production authorization file are rejected before service construction. An environment flag alone has no effect on legacy profile selection.

The clone remains HALTED. No production authorization is loaded or created, no kill switch is touched, and no execution transport is attached. The IO adapter independently allows only session authentication/details and exact-account `GET account` / `GET orders`, after verification of a readonly session. Write-capable sessions, order submission, SLTP submission/cancellation, foreign accounts and other HTTP methods/paths fail closed. Authentication POSTs are not trading POSTs. All exercised IO is fake, under socket connection denial; no real endpoint is contacted in this task.

```text
python -m TradingSystemLab.stage8_robot.release_candidate_runner \
  --runtime-root <manifest-bound-isolated-candidate-root> \
  --stage5-data-root <exact-Stage5-checkout> --accepted-commit <exact-current-commit> \
  --release-manifest <external-release-manifest.json> --release-manifest-sha256 <sha256>
```

This path requires an existing readonly credential if separately authorized for physical diagnostics; none is supplied or changed here. It is a one-shot preview, not a trading runner. Snapshot accounting may update **only the isolated clone**; afterwards its original manifest hash binding becomes stale. Prepare a new output for another preview. Future automatic trading still requires a separately reviewed activation path and physical acceptance; this command cannot unlock it.

## C. Fixed-interval signal diagnosis

`signal_execution_diagnostic` uses exact Stage5 commit `50f1fd2178c18b7ab3bd969be82ad01f47a34745`, immutable seed hashes, unchanged T3 context/core and the accepted full-history raw-signal CSV oracle. It checks timestamp, signal/trade IDs and raw entry/stop/R for each found signal, then compares legacy and V2 independent planners on the same signal. Synthetic capacity assumptions are explicitly labelled: equity 100000, cash 1000000, directional GO 100/120, zero open aggregate risk. These numbers do not establish physical margin or actual entry eligibility. Output records sizing, grid/capacity/aggregate reasons, guard closure and missing historical session authority.

For `[2026-09-01 00:00, 2026-09-16 00:00)` Moscow time: 13 raw signals, all 13 legacy grid skips, all 13 V2 plannable, all 13 blocked by the execution guard. Counts: USDRUBF 3, CNYRUBF 2, GLDRUBF 5, IMOEXF 3. Three actual examples are recorded with raw/executable stops and quantities in the diagnostic JSON/CSV; they are counterfactual planning observations, not broker trades.

For `[2026-09-15 13:00, 2026-09-16 00:00)`: zero raw T3 signals in all four instruments. **The stop-grid fix cannot create an absent signal.** Frozen data ends at H1 close 2026-09-16 00:00 Moscow. The October LIVE week cannot be diagnosed from these data: an external validated LIVE H1 snapshot would be required. Session authority is also BLOCKED rather than inferred from candle availability.

## D. Tests and provenance

See `diagnostics/release_preparation_verification.json` and its hashed stdout artifacts. The final default regression runner reports **501 PASS, 1 Windows-only skipped, 17 subtests PASS** (444 existing plus 57 release cases). A separate final release-module rerun reports **57 PASS**. The default runner includes all earlier tests plus release-preparation checks; the expanded Stage8 run also checks older components, frozen specification and authoritative TRAIL1 ledger. Socket connect/connect_ex/create_connection are denied.

The unfiltered expanded run has historical repository-authority failures. All 35 failed nodes reproduce on unchanged `e59fd8d…`; 33 also fail on actual main. Historical implementation hashes, literal wiring predicates and Stage8.11 assumptions do not describe the later code. Those tests/documents were not rewritten to claim old conformance. Their exact nodes and baseline results remain recorded separately from applicable execution checks; an unfiltered suite PASS is not claimed. The applicable expanded run reports 1352 PASS, one uncovered-interval fixture failure, 10 skipped and 35 exact baseline exclusions. That fixture patched the loader in the wrong module; the corrected case and later release cases pass in the final 57-case module/501-case runner. Results are reported per actual invocation; counts are not summed into a fictional single run.

Both independent raw replays remain 418/418, with 1422 raw signals and exact N4 grid checks. The original executable comparison CSV is byte-identical. Prior pre-POST recovery, partial protection, multi-fill/duplicate/conflict, SLTP growth halt, reference/actual risk, restart, R15, stop grid and TRAIL1 regressions are retained.

## Proposed HALTED cutover procedure — requires separate permission

No step below has been executed on Intel. The next operator boundary is independent audit and a separate decision on physical acceptance/cutover. A preparation PASS is neither merge permission nor production acceptance.

1. Verify the actual deployed commit, frozen specification/account/source bindings and approved candidate commit. Separately approve stopping the production service/Task, preserve safe Task status and acquire exclusive production lock; prevent a second process or new order submission. Legacy HALTED means an operator-controlled quiescent boundary, not an invented legacy database flag.
2. Preserve the existing authorization separately with its exact hash and binding; do not repurpose it for V2. Keep configuration/kill switch/credentials unchanged. Obtain fresh account/order GET evidence while quiescent: zero positions, zero active orders, zero unresolved local intents, no uncovered exposure or pending signal. Stop on contradictions or missing authority.
3. Use SQLite online backup of the quiescent database, verify WAL consistency, close the backup, record schema/integrity/hash and source commit. Retain immutable original archive and causal-key/ledger inventory. Supply this external snapshot to the isolated dry-run; unknown state/revision or incompatible ledgers require review, never guessed migration.
4. Stage a versioned directory with the exact reviewed commit and V2 clone. Validate all state/history/sequence/watermarks, restart and byte-exact rollback on copies. Run the manifest-bound readonly preview against separately authorized fresh broker evidence, with entries closed. No Task/service is pointed at this staging directory yet.
5. Only after a separate reviewed cutover authorization, replace the versioned service/state binding atomically under lock while still quiescent. Recheck identity/account/data/broker flatness. Create a new explicit authorization bound to the approved V2 commit/schema/revision only after the transition is accepted; old authorization is not reused. A trading activation path must itself be reviewed; the preparation runner remains order-incapable.
6. Before any V2 execution/state advancement, rollback may restore the exact old checkout, full original database and preserved old bindings under the same exclusive lock, remaining quiescent. **After any V2 order, fill, position or causal advancement, restoring an old snapshot is unsafe:** stop for fresh reconciliation/operator review; do not rewind watermarks, duplicate entries or cancel a backstop automatically.
7. Physical order-linked fill completeness/retention and percent-SLTP partial/growth coverage must be independently accepted. Re-arm is a separate authorization. Only after a separately approved actual production change, synchronize CURRENT_STATE/ROADMAP/RUNBOOK/PASSPORT/CHECKLIST and recheck actual main/LIVE identity together. No operational document is updated here as though deployment occurred.

## Remaining boundaries

Historical Intel five one-contract CNYRUBF entries are reported readonly A/B PASS by the supplied task; their original report bytes have not been supplied/hash-audited here. They do not prove real partial/multi-fill retention or percent-SLTP growth. Those properties, fresh flat cutover evidence, a real external legacy snapshot and trading activation/authorization remain BLOCKED. `XXX` is not RUB; authenticated tick monetary authority is separate. Reference-entry R15 sizing does not guarantee actual MARKET risk <=1.5% under arbitrary slippage/gaps. No fees/tariffs are calculated or introduced as preparation blockers.

`RELEASE_PREPARATION_OFFLINE_PASS` concerns the isolated dry-run and closed opt-in path only. `LIVE_PRODUCTION_READY=NO`; merge, deploy, re-arm and automatic V2 trading remain unperformed.
