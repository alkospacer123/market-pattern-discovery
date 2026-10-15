# Stage 8.12.4 — H1 timestamp backfill production operator checklist

## CURRENT operator gate — 2026-10-15 #528 Disabled/HALTED

**LATEST INTEL OPERATOR CONSOLE, 2026-10-15 — `ROADMAP36_PR528_HALTED_FILL_RELEASE_TASK_REBIND_PASS_NO_TRADING`.** Source-only PR #528 was merged as release commit `3a18c8c24301c866a60f5d725de227288d48f7ec` after exact-head 309 focused offline PASS. The expressly approved `stage8-528-halted-fill-release-rebind-v1.ps1 -mode execute` returned PASS for exact source/release-diff, six PR #528 Git blobs, frozen Stage5, new versioned checkout and safely re-bound **Disabled** Windows Scheduled Task `TradingSystemLab-Stage8-Production` with V2 selector `STOP_TICK_GRID_V2_FILL_PROPOSED`. **Current Intel installed code SHA** `3a18c8c24301c866a60f5d725de227288d48f7ec`, **checkout** `c:\tradingsystemlab\production\h1-3a18c8c-roadmap36-20261015-190703-0580155`. Exact external Task/rollback evidence `c:\tslaudit\fill493\stage8-528-halted-fill-release-20261015-190703-0580155`. Previous installed checkout `c:\tradingsystemlab\production\h1-5bf1fe0-roadmap36-20261015-180944-9922708` and rollback preserved. Earlier source commit and current main may differ by documentation/other-project changes: **Intel must stay pinned to its installed commit**.

**NO TRADING AUTHORITY:** Source `FINAM_FILL_AUTHORITY_VERIFIED=True` refers **only to bounded contractual fill acceptance** and does not grant authorization. Current Task is **Disabled**, kill switch **HALTED**, there is **NO active exact-commit/account-bound V2 production authorization**, production SQLite hash verified unchanged without SQLite mutation, no Task start/rearm, no token, FINAM request, actual order/cancel or live production cycle occurred in this operation. **LIVE_PRODUCTION_READY=NO, V2 orders prohibited** pending distinct explicit operator approvals. Frozen Stage5 data `50f1fd2178c18b7ab3bd969be82ad01f47a34745`, Stage7 spec `PROD_STAGE7_46DB784378797C7FB04636892350AFF21006D71A31F2CED9D4B974EDA2DC36B8`, `TRAIL1__N4_01__FULL__R15`, T3/H1/TRAIL1, N4 USDRUBF/CNYRUBF/GLDRUBF/IMOEXF, nominal R15 1.5% per new position/max 6% aggregate/margin rounding **unchanged**. Broker 100%-at-activation stop semantics does not prove natural partial 1→2 stop triggering, full exchange execution, infinite trade history or guaranteed realized-loss cap; failures must remain fail-closed.

**NEXT ROADMAP 3.6 (no new phases or repeated offline tests):** Complete this five-document operational synchronization and independently check actual GitHub main vs pinned Intel; execute **fresh FINAM READONLY** account/positions/orders, N4 instrument finances, equity vs explained funding, H1/session, state/heartbeat, unresolved intents and safe HALTED/Disabled precheck without trading token/production state writes; review precise blockers. Separate new exact code-commit/account-bound V2 authorization requires new express operator consent, followed by separate Task start/rearm permission and observed HEALTHY, reconciliation PASS, entry gate OPEN. Do not infer these permissions from PR merge or HALTED installation.


## CURRENT LIVE operational authority — 2026-10-15 #525 Intel Task Disabled HALTED rebind PASS

**LATEST PHYSICAL CHECKPOINT — Intel operator output, 2026-10-15: `ROADMAP36_PR525_HALTED_CODE_ONLY_TASK_REBIND_PASS_NO_TRADING`.** After independent source-only approval of PR #525 (91 focused synthetic tests PASS, AST PASS, exact 4/4 source blobs PASS on Intel), PR #525 was merged into GitHub main at **`5bf1fe02023dd48f4fceb4b288a48ee3f76aebeb`**. The operator then ran approved `stage8-525-halted-code-rebind-v1.ps1 -mode execute` and reported **PASS**, not a trading start. Exact preflight checked the old disabled V2 Task/old archives, clean frozen Stage5 source and release diff **five previously advanced operational Markdown docs plus four PR #525 files**. Native source hashes matched exactly; source `FINAM_FILL_AUTHORITY_VERIFIED=False` remains.

**CURRENT INTEL PRODUCTION CODE (operator-reported, pinned versioned checkout):** `c:\tradingsystemlab\production\h1-5bf1fe0-roadmap36-20261015-180944-9922708`; installed code commit **`5bf1fe02023dd48f4fceb4b288a48ee3f76aebeb`**, explicitly selected revision `STOP_TICK_GRID_V2_FILL_PROPOSED`, Scheduled Task `TradingSystemLab-Stage8-Production` **Disabled**, kill switch **HALTED**. Versioned previous checkout **`c:\tradingsystemlab\production\h1-575001a-roadmap36-20261015-121950-9556285`**, its rollback and original production archives retained. New private Task action/rollback evidence `c:\tslaudit\fill493\stage8-525-halted-code-rebind-20261015-180944-9922708`. Previous retained SQLite SHA-256 **`7368817a82576db8ed301838b1b2de3104c4da508b3edb18f8969dcb4cb2216c`**; latest script reports the LIVE SQLite hash unchanged before/after without writing/opening SQLite. Source/frozen Stage5 root is still pinned to **`50f1fd2178c18b7ab3bd969be82ad01f47a34745`**. No active production trade authorization file. No Task start, process rearm, FINAM/token, real ORDER/CANCEL, SQLite mutation, live production service cycle or migration during this operation.

**STRICT TRADING HOLD:** Frozen Stage7 specification `PROD_STAGE7_46DB784378797C7FB04636892350AFF21006D71A31F2CED9D4B974EDA2DC36B8`, active `TRAIL1__N4_01__FULL__R15`, T3/H1/TRAIL1, N4 (USDRUBF/CNYRUBF/GLDRUBF/IMOEXF), nominal 1.5% new-position and 6% aggregate risk/margin sizing unchanged. FINAM specialist written reply supports `SLTP_QTY_MEASURE_PERCENT=100` determined against the position at stop activation; PR #525's bounded code now accepts growing position **only when the exact same ACTIVE 100% broker stop and durable identity match**, and fails closed otherwise. The previous CNY 2-contract test verified broker WATCHING/100% SLTP after immediate 0→2, not natural 1→2, exchange stop-trigger, full fill, infinite history retention, clearing or client-disconnect behavior. Durable `real_finam_dynamic_coverage_proven=False` does not claim physical proof. **`FINAM_FILL_AUTHORITY_VERIFIED=False`; LIVE_PRODUCTION_READY=NO; no V2 trading authorization and no ARMED permission.** Stage 8 roadmap **3.3/3.4 HALTED install/verification PASS; 3.5 operational synchronization completed by this documents-only merge; 3.6 source update PASS, production trading activation NOT AUTHORIZED**. Before any future real trading, obtain separately reviewed fill/reconciliation/stop post-trigger safety acceptance, fresh broker position/order/account/equity/risk authority, explicit commit+account-bound V2 authorization, separately approved Task start/rearm and observed healthy reconciliation/entry gate. Do not interpret merge as authority to flip fill-gate. No new phases or repeated unrelated tests.

**GitHub/Intel SHA distinction:** at the time of installation, public GitHub main matched installed code **`5bf1fe02023dd48f4fceb4b288a48ee3f76aebeb`**. The later docs-only operational sync merge advances GitHub main commit while the installed Intel checkout stays pinned to `5bf1fe0…`; this is intentional, not code drift. Do not `git pull` the versioned production checkout or re-run #522/#525 rebind.


## CURRENT LIVE operational authority — 2026-10-15 #522 launcher HALTED rebind PASS

**LATEST PHYSICAL CHECKPOINT (Intel operator console, 2026-10-15): roadmap 3.6 source-only PR #522 MERGED, then separately approved HALTED launcher-only Task rebind v1 PASS; NO TRADING.** Exact classification: `ROADMAP36_HALTED_LAUNCHER_ONLY_TASK_REBIND_PASS_NO_TRADING`. PRECHECK installed V2/Task Disabled/HALTED/no active authorization PASS; Stage5/frozen former checkout PASS; public GitHub main pinned to **575001a04bbf127c4a62be83f7855d6b2ce6391e** PASS; allowed delta since installed **7cf7a2d932e217a64bfcb52639abe0d986d1cbeb** is exactly 5 operational docs + 3 launcher/test files; 3 new launcher Git blobs verified and V2 fill gate still CLOSED. Operator reports Windows Task action now explicitly selects V2 revision `STOP_TICK_GRID_V2_FILL_PROPOSED` in a new versioned checkout, while still **Disabled**. Source-only PR #522 Intel offline tests previously **14/14 PASS**, checked 3 exact blobs and production unchanged; those tests do not prove real trading acceptance.

**CURRENT INSTALLED CODE AND TASK BINDING (operator-reported):** `c:\tradingsystemlab\production\h1-575001a-roadmap36-20261015-121950-9556285` at commit **575001a04bbf127c4a62be83f7855d6b2ce6391e**. Frozen Stage5 authority **50f1fd2178c18b7ab3bd969be82ad01f47a34745**. New external private Task rebind evidence `c:\tslaudit\fill493\stage8-522-halted-launcher-20261015-121950-9556285`. Installed V2 SQLite persisted from #47/#48, known SHA-256 **7368817a82576db8ed301838b1b2de3104c4da508b3edb18f8969dcb4cb2216c**; #522 operator rebind reports SQL file hash **UNCHANGED**, without opening or writing SQLite. Original 7cf7 checkout, old database rollback/archives and old authentication archives remain preserved. Production kill switch **HALTED**; Task **Disabled**, processes remain stopped at last precheck. **No** Finam, trading token, Task start, rearm, SQLite migration, order submission or real trading during #522. Last separately checked FINAM readonly capital from #47 **49,931.44 RUB**: do not re-label as a new #522 broker observation.

**STRICT HOLD / ROADMAP:** Stage 8 existing roadmap **3.3 HALTED cutover COMPLETE**, **3.4 physical verification #48 PASS for HALTED installed authority**, **3.5 operational doc sync completed for #47 and now for #522 after this merge**; **3.6 trading activation NOT AUTHORIZED**. Launcher selector wiring is physically installed, but `FINAM_FILL_AUTHORITY_VERIFIED=False`; no new commit/account-bound production trading authorization was created and no service cycle, independent live order-linked multi-fill/SLTP growth, HEALTHY heartbeat, or active entry gate is established. No fill gate relaxation by implication, no Scheduled Task start, no authorization/rearm/orders without separate explicit operator approval and safety-gate acceptance. Frozen Stage7 `PROD_STAGE7_46DB784378797C7FB04636892350AFF21006D71A31F2CED9D4B974EDA2DC36B8`, `TRAIL1__N4_01__FULL__R15`, T3/H1/TRAIL1, N4, 1.5%/new position, 6% nominal concurrent risk and margin sizing unchanged. The GitHub docs-only merge **after** this checkpoint advances the GitHub main hash but does **not** advance the pinned Intel production checkout. Do not `git pull` the pinned release or rerun #47/#48/#522 cutover.


## CURRENT LIVE operational authority — 2026-10-15 #47 HALTED cutover PASS

**LATEST PHYSICAL CHECKPOINT (Intel operator output, 2026-10-15): Stage 8 roadmap 3.3 HALTED production cutover #47 PASS, NO TRADING.** `CLASSIFICATION=ROADMAP33_HALTED_PRODUCTION_CUTOVER_PASS_NO_TRADING`. The operator's #47 report states exact reviewed code blobs 22/22, fresh legacy SQLite online backup, readonly FINAM flat check/equity **49,931.44 RUB**, pristine V2 manifest, exact new production V2 SQLite hash, preserved causal/history ledger, and verification of disabled Windows Task rebinding to the versioned checkout. Old code-bound authorization was archived and **not reused**; Task **Disabled**, kill switch **HALTED**, no Task start/rearm/order. These are operator-reported physical results, not direct access to Intel host files.

**Current installed production authority:** versioned Intel checkout `c:\tradingsystemlab\production\h1-7cf7a2d-roadmap33-20261015-090830-1372736` pinned to release code **7cf7a2d932e217a64bfcb52639abe0d986d1cbeb** (GitHub main may contain later docs-only commits). Stage5 data **50f1fd2178c18b7ab3bd969be82ad01f47a34745**. Installed pristine V2 SQLite SHA-256 **7368817a82576db8ed301838b1b2de3104c4da508b3edb18f8969dcb4cb2216c**. External private cutover evidence `c:\tslaudit\fill493\stage8-519-39-halted-cutover-20261015-090830-1372736`, preparation plan SHA-256 **0b08b63be99ca925a78bb916152ae1b8237d389db4ea3f14088dbb0b2fcd613c**. Old checkout/database (with original WAL/SHM)/authorization retained for controlled recovery. V2 equity capital basis **49,931.44 RUB**; prior historical starting capital and causal/trading history preserved.

**Strict HOLD:** isolated #38 V2 rehearsal was PASS; #41 interrupted cutover was exactly rolled back by #43; subsequent #47 is the first accepted HALTED production cutover. **No production runtime cycle, V2 trading task start, live signal execution, broker fill/slippage/multi-fill authority, or automatic trading authorization is proven by #47.** `FINAM_FILL_AUTHORITY_VERIFIED=False` remains. Existing Windows Task launcher/legacy-default vs explicitly gated V2 runner must be independently checked before even a HALTED Task start; do not assume that replacing the Task checkout activates V2. Trade/rearm/new durable authorization requires separate explicit permission and approved safety gates. No source, frozen T3/H1/TRAIL1 strategy, N4 portfolio, FULL/R15 initial risk (1.5% per new instrument, max 6% nominal aggregate), margin sizing, frozen Stage7 identity or research artifact changes. Do not run #41-#47 again or `git pull` the pinned production checkout. Prior dated sections below are retained historical evidence and are superseded by this checkpoint.



## CURRENT operational authority — 2026-10-15 #43 restored HALTED

**LATEST PHYSICAL CHECKPOINT (Intel operator console, 2026-10-15): Stage 8 roadmap 3.3 #43 exact recovery PASS, NOT V2 LIVE.** The approved #41 HALTED cutover prepared a fresh SQLite backup and a pristine V2 candidate at broker equity **49,931.44 RUB**, but failed during the atomic swap / Scheduled Task update. #42 READONLY established a partial cutover: new V2 SQLite in the live path, old exact Task binding, old SQLite+WAL/SHM retained in rollback, old authorization archived; Task Disabled, kill switch HALTED, production processes 0. The operator then ran #43; output OLD_SQLITE_MAIN_WAL_SHM_RESTORED_EXACT=PASS, OLD_AUTHORIZATION_RESTORED_EXACT=PASS, OLD_TASK_BINDING_DISABLED_UNCHANGED=PASS, INTERRUPTED_NEW_V2_ARCHIVED_EXACT=PASS, KILL_SWITCH_HALTED_UNCHANGED=PASS, ROADMAP33_INTERRUPTED_CUTOVER_EXACT_ROLLBACK_RESTORED_HALTED. No Task start, rearm, real orders or FINAM call during #43. These are operator-reported host observations; the original confidential bytes are not available in GitHub.

**Current production authority:** legacy Intel checkout **184e8c2b8fa092a606249ff293a4f507160bff29**; legacy production SQLite and WAL/SHM restored byte-for-byte; original commit-bound authorization file restored and must **not** be reused for V2; Scheduled Task still **Disabled**, still bound to the old checkout; switch **HALTED**; no service processes in last observed diagnostic. Broker equity **49,931.44 RUB** was observed READONLY before #41 swap; old legacy SQLite was restored as-is, so the **49,931.44 RUB rebasing exists only in separately archived V2 preparations**, not as an accepted live equity-state change. Frozen T3/H1/TRAIL1, N4, FULL/R15 (1.5% / 6%), and Stage5 authority **50f1fd2178c18b7ab3bd969be82ad01f47a34745** remain unchanged.

**Operational decision:** roadmap 3.3 isolated rehearsal #38 **PASS** (22/22 code blobs, clean V2 dry-run, exact rollback, HALTED readonly preview). HALTED **production cutover remains NOT COMPLETE**, despite the successful exact rollback. Do **not** rerun #41 or #43, start Task, rearm, send orders, edit the live SQLite, or unlock FINAM_FILL_AUTHORITY_VERIFIED=False by implication. First correct/verify the Windows Task action-update mechanism (prior 2026-10-12 Windows account/password-validation issue is relevant, but #41's exact native exception was not captured), then execute only a separately gated HALTED cutover under the operator's existing bounded approval. V2 preview is not a production trading authorization. PRs **#493 and #519 are merged**; older "Draft #493 unmerged" statements below are dated historical records and are superseded here. Immediately synchronize the operational docs after any subsequent accepted production change and independently compare actual GitHub main with Intel bindings.

**Private incident evidence (not for Git):** c:\tslaudit\fill493\stage8-519-39-halted-cutover-20261015-081546-2400714, plan SHA-256 fc93b100bf0854b68ca3187f68012bf073aa78299729f7c025fef22473ce1bb9, pristine V2 SHA-256 b7954b8a1507447a65c865652686af33e9026aa824dd6f2c20affe75c7ff2f30. Previous observations below are historical unless explicitly reconfirmed.

## CURRENT OPERATOR CHECKLIST — 2026-10-13 Task isolation PASS / HALTED

- [x] Explicit authorization obtained for Task isolation **only**.
- [x] Fresh FINAM account/orders double READONLY flatness, SQLite and HALTED precheck PASS.
- [x] Original production Task XML saved outside Git; SHA-256 `2714BB09FF571EFAE748509F5D3C3BC8DD5F38460173E1A13EF5AEE752DF906E` reported by Intel (actual XML not downloaded).
- [x] `TradingSystemLab-Stage8-Production` disabled before stop; automatic restart suppressed.
- [x] PowerShell PID 8536, Python PIDs 6260 / 11608 all exited; no service processes at post-stop gate.
- [x] Post-stop FINAM double READONLY broker flatness, production SQLite before/after and exclusive lock test PASS.
- [x] Kill switch HALTED; no order submission, Task rearm, source/strategy/margin/SQLite edits.
- [ ] Keep Task Disabled; do not apply historical ARMED / Running daily checklist below.
- [ ] New operator approval required to restore/start Task, rearm or send any real order; no SLTP physical acceptance authorization.
- [ ] Future post-stop READONLY observations should independently check broker flatness and no service processes; stopped heartbeat stale by design.

**NO TRADING.** Existing durable code-bound authorization is still stored, not revoked. Draft PR #493 remains isolated/unmerged; do not deploy candidate or change frozen Stage7 identity. For emergency broker exposure or orphan process, halt and escalate rather than improvising Task/PID commands.


## Current daily closeout — 2026-10-12 post-rearm read-only verification

- [x] Explicit operator re-arm `STAGE8_12_H1_REARM=PASS`; kill switch `ARMED` generation **60**, entry gate `OPEN`.
- [x] Actual production code `184e8c2b8fa092a606249ff293a4f507160bff29`; Stage5 `50f1fd2178c18b7ab3bd969be82ad01f47a34745`; frozen production identity unchanged.
- [x] At 11:38:23 MSK: Production Scheduled Task `Running`, Readonly `Disabled`, authorization `AUTHORIZED`/`True`, auth and heartbeat both match fix commit.
- [x] Heartbeat `HEALTHY`, reconciliation `PASS`, cycle **9258**, fresh FINAM contact; open positions **0**, unresolved intents **0**, active protective stops **0** at observation time.
- [x] Earlier `STAGE8_12_4_H1_SPLICE_TIMESTAMP_MISMATCH` records pre-date fix; cycles **9213–9258** are PASS.
- [ ] Update separately `check-tradingsystemlab-live.ps1` expected commit: obsolete `4c7cd7c...` causes two false `MISMATCH` warnings; do not modify production robot.
- [ ] Continue regular LIVE monitoring and broker-side order/position/protection reconciliation on every real position. No new trade/fill observed in the provided log.


## Current operator closeout — 2026-10-12 (supersedes older unchecked items)

- [x] Regression tests **114 PASS**; exact PR #484 fix staged at `184e8c2b8fa092a606249ff293a4f507160bff29`; frozen Stage5 and N4 H1 immutable history preserved.
- [x] FINAM + SQLite precheck PASS, initial broker positions/active orders/local unresolved `0/0/0`; cutover backup SHA-256 `759ef278967b9781a79bd916e47bfe5823908b027dc98b48b05b198fa4482bd7`.
- [x] Authorization rolled over exactly once and bound to fix SHA; guarded real production cycle **9213** `HEALTHY/PASS`.
- [x] Windows Scheduled Task principal-preserving exact-commit recovery `PASS`, `RUNNING`; next real LIVE cycle **9214** `HEALTHY/PASS`.
- [x] Recovery broker/SQLite check PASS, 0 positions, 0 unresolved; entry gate `CLOSED_HALTED`; kill switch `HALTED` generation 59.
- [x] Evidence stored outside Git: `h1-live-rollout-184e8c2-20261012/halted-task-recovery-pass.json`, SHA-256 `95d724dce03cedefd444de742d6f73fa3b6a0dbdecf0f8c6418e2149c8a0da43`.
- [ ] Separate explicit operator **re-arm** decision after fresh safety checks. Until then **do not change kill switch or enable entries**.
- [ ] Continue normal HALTED production observation; no repeat code/authorization/task rollout.


## Completed Intel backup gate — 2026-10-12

- [x] `READINESS_BACKUP=PASS`, broker positions/orders/local unresolved intents `0/0/0`, N4 continuation keys `4`.
- [x] SQLite read-only online backup integrity PASS; backup SHA-256 `6a8c2c7d1ef589ff0190b28624397962abb9583eccfa90bc4099a6f1681486fe`.
- [x] External readiness report SHA-256 `812ab73de05b896db7d4938b040d20bda49f8fc924a0e852a8c20de45516b644`; old auth/task backups retained externally.
- [x] Kill switch `HALTED` generation 59; active LIVE checkout, production SQLite, auth and task untouched.
- [ ] Exact-commit HALTED LIVE deployment, authorized migration procedure, real-runtime `HEALTHY/PASS`, separate explicit re-arm permission.


## Newly accepted physical evidence — 2026-10-12

- [x] Fix PR #484 isolated exact-code targeted tests: 60/60 PASS (full Stage 8 suite pending).
- [x] FINAM GET-only immutable H1 N4: 4/4 PASS; 2 ignored historical backfills + 2 append-ready bars per N4 at probe; broker positions/orders/unresolved intents 0/0/0. External SHA-256 `2fe51ccd6ab57682579f222158b12413eaae6020abe21aec7afa188d3afddb43`.
- [x] Isolated one-cycle production shadow with SQLite copy: unchanged prefix 4/4 PASS, 3 bars appended per N4 to shadow only, shadow heartbeat `HEALTHY`, reconciliation `PASS`. External SHA-256 `4799a0b426cd62d143a0b3fdba6035ef44f11dde6654676568b1a28e3a8fbded`.
- [x] Confirmed old LIVE checkout/authorization/SQLite/Tasks not modified by shadow; kill switch `HALTED` generation 59.
- [ ] Controlled LIVE exact-code rollout after backups, full applicable audit and commit-bound authorization migration.
- [ ] Fresh LIVE-runtime `HEALTHY/PASS`, verified flat account/zero unresolved intents and separate explicit re-arm approval.


## Current gate: HALTED / NOT REARMED (2026-10-12)

This checklist supersedes the historical **ARMED** daily-operations checklist until a new explicit operator decision. Existing production authorization remains bound to the previously accepted code commit; its existence is not approval to re-arm after this incident.

### A. Physical safety baseline (reported, recheck on Intel)

- [ ] Verify kill switch remains `HALTED`, generation at least 59. Do not change it.
- [ ] Confirm production task state and actual pinned production checkout; production service may remain Running in HALTED state.
- [ ] Verify positions=0, unresolved intents=0, active orders and protective coverage consistent with exact FINAM account authority.
- [ ] Record a fresh heartbeat, reconciliation result, cycle_count, last completed H1, and recent fault codes.
- [ ] Confirm REAL account, N4 bindings, Stage7 identity and persisted authority hashes unchanged.
- [ ] Preserve existing external runtime state and SQLite continuation; **no deletion, manual insertion, rewriting, or reseeding**.
- [ ] No `git pull`, automatic update or unattended activation of production checkout.

### B. Code and regression verification

- [ ] Check actual GitHub `main`; PR #484 code merge: `184e8c2b8fa092a606249ff293a4f507160bff29`.
- [ ] Independently run full project tests and targeted H1 splice/continuation/safety regressions against that exact source.
- [ ] Existing-timestamp FINAM OHLC revision leaves accepted OHLC unchanged.
- [ ] Late FINAM-only backfilled H1 at/before immutable authority.max() is ignored, not inserted.
- [ ] Persisted continuation prefix and already accepted history unchanged.
- [ ] Exact latest authority seam present: only strictly newer completed bars append.
- [ ] Missing exact latest seam / no overlap => fail closed.
- [ ] Duplicate or out-of-order FINAM timestamps => fail closed.
- [ ] Persisted continuation corruption => fail closed.
- [ ] Missing/stale current completed H1 => fail closed.
- [ ] Confirm frozen T3/H1/TRAIL1/N4/FULL-R15, 6% ceiling, sizing, execution semantics and research results unchanged.

### C. Intel preactivation: HALTED, GET-only/zero-order

- [ ] Separately stage and verify the **exact tested code commit** on Intel without moving the active LIVE checkout automatically.
- [ ] Ensure kill switch remains HALTED throughout the preactivation.
- [ ] Run operator-controlled zero-order preactivation, with physical N4 data and persisted H1 continuation validated without modification of historical prefix.
- [ ] Require fresh `health_status=HEALTHY`, `reconciliation_status=PASS`, positions=0 and unresolved intents=0.
- [ ] Confirm fresh H1 and heartbeat; no repeated splice fault; exact account, Stage5 commit and accepted code hash proven.
- [ ] Capture sanitized external evidence, timestamps, code and data commit hashes, test counts and preactivation result.
- [ ] If any criterion fails, remain HALTED and do not proceed.

### D. Commit-bound authorization and re-arm — separate permission required

- [ ] Determine whether new accepted code commit requires authorization rollover. Never copy/modify an existing authorization by hand or reuse an incompatible commit-bound record.
- [ ] Revalidate accepted authority, operational checks, and safe operator-controlled rollover, **only with separately explicit operator permission**.
- [ ] Re-arm **only after new explicit user/operator authorization**. The permission to implement the H1 fix is not permission to re-arm.
- [ ] Following any separately approved re-arm, verify first fresh heartbeat, PASS reconciliation, zero unexpected intents/orders, correct position protection and active code hash.
- [ ] Update `CURRENT_STATE.md`, `PROJECT_CONTEXT.md`, `ROADMAP.md`, `METHODOLOGY.md`, runbook, README, provenance, strategy passport and checklist after the physical decision; verify actual GitHub `main` again.

**Fail-closed rule:** no forced entries, no changed sizing or strategy, no manual persisted history edit, no automatic `git pull` on LIVE.
