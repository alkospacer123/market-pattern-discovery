# TradingSystemLab Stage 8.12 Production Runbook

## CURRENT LIVE operations: 2026-10-15 Stage8 #528 RUNNING HEALTHY under external HALTED

Intel reported `ROADMAP36_PR528_V2_RUNNING_HEALTHY_HALTED_NOT_ARMED`, `FRESH_V2_HEALTHY_RECONCILIATION_PASS=YES`, cycle_count `11609`, `FRESH_FINAM_API_CONTACT=PASS`, `NO_OPEN_POSITIONS_NO_UNRESOLVED_INTENTS_NO_ACTIVE_STOPS=PASS`, `ENTRY_GATE_EXCLUSIVELY_BLOCKED_EXTERNAL_HALTED=PASS`, and `FROZEN_H1_FRESHNESS_PATH_COMPLETED_IN_HEALTHY_PRODUCTION_CYCLE=PASS`. Evidence at `c:\tslaudit\fill493\stage8-528-halted-start-only-20261015-205529-ed0b4a76`. Installed release remains pinned `3a18c8c24301c866a60f5d725de227288d48f7ec`; Task running, external kill switch HALTED, no live entry permission and no orders authorized by this checkpoint. Earlier exact one-key `execution_halt` release-preparation recovery independently verified on SQLite+WAL+SHM; do not repeat recovery.

RUNBOOK HOLD: maintain external HALTED and exact installed commit until operator separately permits rearm and live entries. No user consent to ARMED at this checkpoint. If any reconciliation, heartbeat, account, position or protective-stop check fails, remain fail-closed. Do not delete WAL/SHM; do not rerun prior SQLite recovery.


## CURRENT authority — 2026-10-15 #528 authorized durable record, robot still HALTED / Disabled

**LATEST OPERATOR-REPORTED INTEL PHYSICAL AUTHORIZATION — 2026-10-15:** operator explicitly approved **only** new V2 durable authorization at installed source `3a18c8c24301c866a60f5d725de227288d48f7ec`, checkout `c:\tradingsystemlab\production\h1-3a18c8c-roadmap36-20261015-190703-0580155`. `stage8-528-authorize-halted-v1.ps1 -mode execute` returned `DURABLE_EXACT_COMMIT_ACCOUNT_AUTHORIZATION_CREATED=PASS` and `CLASSIFICATION=ROADMAP36_PR528_V2_AUTHORIZATION_CREATED_HALTED_NOT_ARMED`; exact durable `runtime\safety\stage8-12-4-production-authorization.json` record SHA-256 **`62DCFC8EBBD0552D0C7869E0407CEF4725554E57F1C83B720D240F7135DEAE09`**. Binding to the exact installed commit, sanitized FINAM account identity, frozen Stage7 identity, prior accepted evidence and operator phrase passed in operator's precheck; **DO NOT recreate/overwrite** this create-once record. Precheck `PINNED_RELEASE_STAGE5_TASK_DISABLED_HALTED_NO_AUTHORIZATION=PASS`, `FROZEN_SQLITE_EXACT_SHA_NO_SIDECARS_PRIVATE_EVIDENCE_SHA=PASS`, `PRIVATE_R15_ACCOUNT_AND_NATIVE_AUTHORIZE_PRECHECK=PASS`, after-create `PRODUCTION_SQLITE_TASK_KILL_SWITCH_BEFORE_AFTER_UNCHANGED=PASS`, `TASK_DISABLED_KILL_SWITCH_HALTED_AFTER_AUTH=PASS`. Original precheck with mistyped `-ode` did not authorize; subsequent explicit `-mode execute` did.

**Financial reconciliation before authorization (same operator, 2026-10-15):** fresh FINAM GET-only READONLY account / positions / orders / frozen N4 asset and margin precheck `ROADMAP36_PR528_FRESH_FINAM_READONLY_PRECHECK_PASS_NO_LIVE`, private broker report SHA-256 `295FE0B68495390C57DCEB1A05D18A6F9FD43323B2D22354C6A49DA5E766D2B0`. Independently controlled copied-SQLite capital check `ROADMAP36_PR528_SQLITE_R15_BROKER_BASIS_PASS_NO_TRADING_AUTHORITY`, sanitized private audit SHA-256 `8D83292404676C11DFE3D88E38A690CDDB378F9FEFEDBE988DFABA8944C85646`: production persisted realized equity **49 931.44 RUB** = FINAM-derived realized equity **49 931.44 RUB**; starting realized 2 469.56 RUB; production explained-cash-flow **subtraction field 0** (do not mislabel as externally audited aggregate funding); production local positions **0**, unresolved intents **0**, execution_halt **HALTED**, clean SQLite identity / integrity. Auditor reported SQLite and Task/kill switch byte-identical before/after. No broker order, stop trigger or V2 production cycle occurred in these two reports.

**CURRENT SAFE STATE / HARD BOUNDARY:** durable `execution_authorized=True` record exists but **NOT ARMED / NOT RUNNING / LIVE_PRODUCTION_READY=NO**: Windows Task `TradingSystemLab-Stage8-Production` **Disabled**, kill switch **HALTED**, no real order/cancel, no trading token used during authorization, no LIVE SQLite write/rearm, no robot process start. Release fill-authority source `FINAM_FILL_AUTHORITY_VERIFIED=True` is not a full exchange stop-fill guarantee; broker 100%-at-activation SLTP semantics leaves gap/slippage/partial-order-execution risk. Strategy remains frozen `PROD_STAGE7_46DB784378797C7FB04636892350AFF21006D71A31F2CED9D4B974EDA2DC36B8` / `TRAIL1__N4_01__FULL__R15` / T3/H1/TRAIL1, N4 USDRUBF/CNYRUBF/GLDRUBF/IMOEXF, 1.5% nominal risk per new position / 6% maximum simultaneous nominal initial risk and margin-limited downward lot rounding, unchanged; Stage5 pinned `50f1fd2178c18b7ab3bd969be82ad01f47a34745`.

**NEXT EXISTING ROADMAP 3.6 ONLY:** independently verify this five-document GitHub-main sync (docs changes must not force any Intel repin); request **separate explicit operator permission** for a controlled **HALTED** Task enable/start under exact same installed checkout and existing created authorization, followed by fresh observed real runtime HEALTHY + reconciliation PASS, empty intents, FINAM/account/N4/exposure, fresh H1, new exact-commit heartbeat, no entry-gate bypass. **Separate later explicit operator permission** is required to switch kill switch from HALTED to ARMED and authorize normal real entries. No new phase, no optimization, no strategy/risk adjustments, no repeat of 309 synthetic offline tests without a relevant code change.


## CURRENT operational authority — 2026-10-15 PR #528 HALTED, no trading

**LATEST INTEL OPERATOR CONSOLE, 2026-10-15 — `ROADMAP36_PR528_HALTED_FILL_RELEASE_TASK_REBIND_PASS_NO_TRADING`.** Source-only PR #528 was merged as release commit `3a18c8c24301c866a60f5d725de227288d48f7ec` after exact-head 309 focused offline PASS. The expressly approved `stage8-528-halted-fill-release-rebind-v1.ps1 -mode execute` returned PASS for exact source/release-diff, six PR #528 Git blobs, frozen Stage5, new versioned checkout and safely re-bound **Disabled** Windows Scheduled Task `TradingSystemLab-Stage8-Production` with V2 selector `STOP_TICK_GRID_V2_FILL_PROPOSED`. **Current Intel installed code SHA** `3a18c8c24301c866a60f5d725de227288d48f7ec`, **checkout** `c:\tradingsystemlab\production\h1-3a18c8c-roadmap36-20261015-190703-0580155`. Exact external Task/rollback evidence `c:\tslaudit\fill493\stage8-528-halted-fill-release-20261015-190703-0580155`. Previous installed checkout `c:\tradingsystemlab\production\h1-5bf1fe0-roadmap36-20261015-180944-9922708` and rollback preserved. Earlier source commit and current main may differ by documentation/other-project changes: **Intel must stay pinned to its installed commit**.

**NO TRADING AUTHORITY:** Source `FINAM_FILL_AUTHORITY_VERIFIED=True` refers **only to bounded contractual fill acceptance** and does not grant authorization. Current Task is **Disabled**, kill switch **HALTED**, there is **NO active exact-commit/account-bound V2 production authorization**, production SQLite hash verified unchanged without SQLite mutation, no Task start/rearm, no token, FINAM request, actual order/cancel or live production cycle occurred in this operation. **LIVE_PRODUCTION_READY=NO, V2 orders prohibited** pending distinct explicit operator approvals. Frozen Stage5 data `50f1fd2178c18b7ab3bd969be82ad01f47a34745`, Stage7 spec `PROD_STAGE7_46DB784378797C7FB04636892350AFF21006D71A31F2CED9D4B974EDA2DC36B8`, `TRAIL1__N4_01__FULL__R15`, T3/H1/TRAIL1, N4 USDRUBF/CNYRUBF/GLDRUBF/IMOEXF, nominal R15 1.5% per new position/max 6% aggregate/margin rounding **unchanged**. Broker 100%-at-activation stop semantics does not prove natural partial 1→2 stop triggering, full exchange execution, infinite trade history or guaranteed realized-loss cap; failures must remain fail-closed.

**NEXT ROADMAP 3.6 (no new phases or repeated offline tests):** Complete this five-document operational synchronization and independently check actual GitHub main vs pinned Intel; execute **fresh FINAM READONLY** account/positions/orders, N4 instrument finances, equity vs explained funding, H1/session, state/heartbeat, unresolved intents and safe HALTED/Disabled precheck without trading token/production state writes; review precise blockers. Separate new exact code-commit/account-bound V2 authorization requires new express operator consent, followed by separate Task start/rearm permission and observed HEALTHY, reconciliation PASS, entry gate OPEN. Do not infer these permissions from PR merge or HALTED installation.


## CURRENT LIVE operational authority — 2026-10-15 #525 halted code-only rebind PASS

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

## CURRENT RUNBOOK — 2026-10-13 production Task disabled/stopped, HALTED

**CURRENT LIVE: STAGE8_493_PRODUCTION_TASK_ISOLATED_HALTED — 2026-10-13 Intel operator evidence.** The authorized `stage8-493-controlled-task-isolation.ps1 -execute` physically returned `ISOLATED_HALTED_PENDING_GITHUB_OPERATIONAL_SYNC`. Fresh before-stop `FINAM + SQLite + HALTED=PASS`; Task `TradingSystemLab-Stage8-Production` was **disabled before stop** with startup/auto-restart suppressed; PowerShell PID **8536**, Python root **6260**, Python child **11608** exited. Post-stop `POST_STOP_FINAM_SQLITE_LOCK_GATE=PASS`: two fresh broker READONLY account/orders flat snapshots, clean production SQLite and lock quiescent. Existing kill switch **HALTED**. No orders or rearm by this operation.

**Evidence:** original Task XML backup saved outside Git in `c:\tslaudit\fill493`, operator-reported SHA-256 `2714BB09FF571EFAE748509F5D3C3BC8DD5F38460173E1A13EF5AEE752DF906E` (backup bytes and exact timestamped filename not independently fetched). Result is a time-bounded *operator-console* observation; heartbeat stops refreshing by design after isolation. The durable commit-bound production authorization record **was not revoked or rewritten**. Disabling Task and keeping HALTED do not erase existing authorization; do not start/rearm without fresh separately approved recovery.

**Frozen identity unaffected:** accepted Intel code `184e8c2b8fa092a606249ff293a4f507160bff29` (PR #484), Stage5 data `50f1fd2178c18b7ab3bd969be82ad01f47a34745`, production spec `PROD_STAGE7_46DB784378797C7FB04636892350AFF21006D71A31F2CED9D4B974EDA2DC36B8`, `TRAIL1__N4_01__FULL__R15`, T3/H1/TRAIL1, N4 USDRUBF/CNYRUBF/GLDRUBF/IMOEXF, risk 1.5% new position / 6% nominal aggregate and frozen margin sizing. No source, strategy, risk, research, execution adapter, authorization file or production SQLite modification was made.

**HARD HOLD:** Draft PR #493 (candidate STOP/TICK GRID and SLTP acceptance) is not merged/deployed. No real orders, SLTP test, V2 rearm, Task restore/restart, forced PID kills, change to `FINAM_FILL_AUTHORITY_VERIFIED=False` or stage8.11 one-contract policy without new, separate explicit authorization. Post-stop FINAM validation is **readonly** and does not grant fill-price or live-entry authority. The prior `ARMED / Running / HEALTHY` sections below are **historical**, not instructions for current LIVE. Never `git pull` the pinned Intel checkout to follow docs-only GitHub commits.

**Recovery boundary:** The pre-isolation FINAM wrapper requires Task Running and is invalid after stop; use only explicitly approved post-stop READONLY checks. If processes reappear, lock is held, broker exposure/orders are not flat, or kill switch changes, classify `OPERATOR_INTERVENTION_REQUIRED`, preserve evidence and follow an independently approved recovery; do not repeat `-execute`, kill PIDs, restore Task or rearm. Original Task XML exists outside Git but must be verified before any future separately approved restoration. Previous daily Running-heartbeat instructions are suspended.


## 2026-10-12 CURRENT operational authority — LIVE ARMED, confirmed after re-arm

**LIVE: ARMED, kill switch generation 60; Scheduled Task Running; fresh HEALTHY / reconciliation PASS; entry gate OPEN.** Production code remains exact fix `184e8c2b8fa092a606249ff293a4f507160bff29` (PR #484); Stage5 data authority `50f1fd2178c18b7ab3bd969be82ad01f47a34745`. Explicit operator-authorized `stage8_12_h1_rearm_once.ps1` returned `STAGE8_12_H1_REARM=PASS`, `REARM_COMPLETED=YES`. Re-arm did not change source, Scheduled Task, authorization or SQLite schema, and did not itself force an order.

**Physical read-only check, 2026-10-12 11:38:23 MSK:** production `Running`, readonly `Disabled`; auth `AUTHORIZED`, `execution_authorized=True`, accepted commit exact `184e8c2...`; `ARMED` gen 60; heartbeat `HEALTHY`, reconciliation `PASS`, **cycle 9258**, heartbeat/API `2026-10-12T08:37:59.022453+00:00`, positions 0, active protective stops 0, unresolved intents 0. Successful production cycles 9213–9258 follow earlier historical H1 timestamp mismatch faults. There is no evidence of a new real trade in this snapshot; trading is eligible only if frozen safety and signal gates pass.

The operator check script `check-tradingsystemlab-live.ps1` still compares authorization and heartbeat to **obsolete** SHA `4c7cd7cbbde5fbffb63ed6984cf89b90dc50d129`, producing two **false MISMATCH** warnings. Actual authorization and heartbeat both match fixed SHA `184e8c2...`. Updating that read-only diagnostic is a separate small task; do not change live production to accommodate old expectations.

The earlier HALTED and shadow/backup/recovery sections below remain historical and are **superseded as current operational status**. T3/H1/TRAIL1, frozen N4 FULL/R15 (1.5% per new position, 6% nominal aggregate initial risk), margin sizing and all research/strategy/exec semantics are unchanged. **Never `git pull` the active production checkout just because docs-only GitHub main advanced.**


## Current operational authority — 2026-10-12, H1 timestamp-backfill fix LIVE restored under HALTED

**AUTHORITATIVE LATEST STATE: HALTED / RUNNING / HEALTHY / RECONCILIATION PASS / NOT REARMED.** This supersedes earlier dated incident, shadow, readiness, and partially failed task-rollout snapshots below; those remain historical provenance, **not** current operational instructions.

Intel operator executed approved fix rollout plus narrow Scheduled Task recovery. The exact active production checkout is **`184e8c2b8fa092a606249ff293a4f507160bff29`**, PR #484, **not latest docs-only GitHub main**. Frozen Stage5 data remains pinned `50f1fd2178c18b7ab3bd969be82ad01f47a34745`; old production source checkout `4c7cd7cbbde5fbffb63ed6984cf89b90dc50d129` retained as previous/rollback provenance, not active LIVE code.

- Cutover regression tests **114 passed**; FINAM broker/SQLite safety precheck PASS; separate SQLite cutover backup SHA-256 `759ef278967b9781a79bd916e47bfe5823908b027dc98b48b05b198fa4482bd7`; exact new commit-bound production authorization successfully rolled over once; N4 immutable H1 prefix PASS.
- First corrected production real-runtime guarded cycle **9213**: `HEALTHY`, reconciliation `PASS`. The initial Scheduled Task update failed due to Windows username/password validation; this is **resolved**, not a current blocker.
- Subsequent narrow recovery script `stage8_12_h1_resume_task_binding_halted.ps1` operator result: `STAGE8_12_H1_TASK_RECOVERY=PASS`; exact Windows task action rebound with principal unchanged; task started successfully; new actual LIVE cycle **9214**, heartbeat `HEALTHY`, reconciliation `PASS`.
- Latest recovery broker/SQLite precheck PASS, open positions `0`, unresolved intents `0` (and prior cutover active broker orders `0`); exact-commit task **`RUNNING`**; entry gate **`CLOSED_HALTED`**; kill switch **`HALTED`**, generation **`59`**; **`REARM=NOT_DONE`** and no new trade authorization implied by task recovery.
- External Intel task-recovery evidence: `c:\tradingsystemlab\verification\h1-live-rollout-184e8c2-20261012\halted-task-recovery-pass.json`, SHA-256 `95d724dce03cedefd444de742d6f73fa3b6a0dbdecf0f8c6418e2149c8a0da43`. These physical facts come from the operator's PowerShell log; external report bytes and runtime are **not** stored in GitHub.

**Next:** preserve running HALTED monitoring; do not repeat rollout, reissue authorization, change task bindings, edit SQLite, or `git pull` the production checkout. Re-arm to enable entries requires **separate explicit operator authorization** after an up-to-date safety check. No Stage7 strategy, T3/H1/TRAIL1, N4, R15/6% limits, risk sizing, research artifacts, or broker execution semantics changed.


## 2026-10-12 HALTED LIVE rollout readiness + backup — PASS (operator evidence)

Operator-ran Intel backup-only gate after the 60/60 isolated H1 tests, 4/4 FINAM GET-only H1 checks, and 4/4 shadow production HEALTHY/PASS:
- `READINESS_BACKUP=PASS`, source LIVE SQLite backed up using read-only SQLite online backup; `SQLITE_BACKUP_INTEGRITY=PASS`; exactly four durable N4 H1 continuation keys.
- Latest broker positions `0`, active broker orders `0`, local unresolved intents `0`; kill switch `HALTED`, generation `59`.
- External SQLite backup SHA-256: `6a8c2c7d1ef589ff0190b28624397962abb9583eccfa90bc4099a6f1681486fe`.
- External readiness report: `C:\TradingSystemLab\verification\h1-live-rollout-readiness-backup-20261012\readiness-backup-report.json`; SHA-256: `812ab73de05b896db7d4938b040d20bda49f8fc924a0e852a8c20de45516b644`.
- The backup also preserved existing authorization and Scheduled Task definition externally. Existing production checkout `4c7cd7cbbde5fbffb63ed6984cf89b90dc50d129`, authorization, production task `Running`, Stage5 source and LIVE SQLite remain unchanged. `ROLLOUT=NOT_STARTED`; `REARM=NOT_DONE`; LIVE `HEALTHY/PASS` has **not** been proven.
- **Next operator boundary:** exact-commit controlled HALTED task/code/authorization migration, with old authorization kept immutable as evidence and no automatic re-arm. Requires separate explicit operator permission before altering the active task/authorization. Never `git pull` into active production checkout.

The validation and backup evidence hashes are operator reported; actual external backup bytes remain on Intel. No frozen T3/H1/TRAIL1, N4, R15/6%, sizing, research or execution changes.


## 2026-10-12 validation update — shadow PASS; LIVE still HALTED

Intel operator evidence for code fix PR #484 (commit `184e8c2b8fa092a606249ff293a4f507160bff29`), **not** a production deployment:

- Isolated worktree targeted tests **60/60 PASS**. Full Stage 8 suite not yet run.
- FINAM GET-only immutable H1 physical splice **4/4 N4 PASS**; accepted seam `2026-10-11T18:00:00+03:00`; 2 backfilled historical timestamps ignored and 2 newer append-ready bars **per N4 at probe time**. Broker positions, active orders and unresolved intents: `0/0/0`. External evidence SHA-256: `2fe51ccd6ab57682579f222158b12413eaae6020abe21aec7afa188d3afddb43`.
- One-cycle corrected production service **on an isolated SQLite online-backup copy**, FINAM restricted to session/GET calls: immutable-prefix checks `4/4 PASS`, **3 newer bars per N4 appended to shadow only**. Shadow heartbeat `HEALTHY`, reconciliation `PASS`. External evidence SHA-256: `4799a0b426cd62d143a0b3fdba6035ef44f11dde6654676568b1a28e3a8fbded`.
- LIVE checkout remains at old code commit `4c7cd7cbbde5fbffb63ed6984cf89b90dc50d129`; old-commit-bound authorization and LIVE SQLite/tasks unchanged. Production task `Running`, kill switch `HALTED` generation 59. **LIVE production heartbeat recovery NOT TESTED/NOT PROVEN.** No real order endpoint call or re-arm in these checks.
- Next gate: operator-controlled HALTED LIVE deployment with validated rollback/backups and exact commit/task/authorization rollover, full applicable tests/audits, fresh real-runtime `HEALTHY/PASS`; re-arm requires a separate explicit operator decision. Do not run historical foundation/package3 scripts against an already authorized, Running LIVE environment; never `git pull` active LIVE checkout.

External report bytes remain on Intel, not committed in Git. No strategy, T3/H1/TRAIL1/N4/FULL-R15, frozen risk/portfolio/execution, Stage5 or research changes.


## Current operational HOLD — 2026-10-12 (supersedes older operational snapshots)

**HALTED / NOT REARMED.** Operator-provided physical snapshot at `2026-10-12T05:55:33.966970+00:00`: kill switch `HALTED`, generation `59`, production service `Running`, positions `0`, unresolved intents `0`; heartbeat `UNHEALTHY`, reconciliation `FAULT`, cycle_count `9212`, repeated `STAGE8_12_4_H1_SPLICE_TIMESTAMP_MISMATCH`. These are **reported observations**, not a new physical verification.

Observed GET-only diagnosis across all four N4: FINAM later added H1 `2026-10-10 09:00 MSK` inside immutable historical overlap; exact authority seam `2026-10-11 18:00 MSK` remained present and a later live H1 `2026-10-12 07:00 MSK` existed. The first LIVE week independently examined 58 H1 per N4 (232 checks), with 0 complete T3 signals, 0 intents, 0 fills and signal_sequence=0.

Code-only H1-history fix: [PR #484](https://github.com/alkospacer123/market-pattern-discovery/pull/484), merged as `184e8c2b8fa092a606249ff293a4f507160bff29`. This is **repository code**, **not** a physically accepted or deployed LIVE commit. The Intel production checkout remains historically pinned to `4c7cd7cbbde5fbffb63ed6984cf89b90dc50d129`; Stage5 data is `50f1fd2178c18b7ab3bd969be82ad01f47a34745`. Documentation-only commits may advance `main` without changing that checkout.

Stage5 plus persisted H1 remains immutable; later FINAM-only timestamps `<= authority.max()` are ignored, and only bars `> authority.max()` append after the **exact latest seam** is observed. Missing seam/no overlap, duplicated or unordered timestamps, persisted corruption and stale current H1 continue to fail closed. Frozen T3/H1/TRAIL1/N4/FULL-R15/6%, sizing and execution semantics are unchanged.

**Gates outstanding:** full repository test execution; Intel preactivation under `HALTED` with fresh `HEALTHY/PASS`, positions=0 and unresolved=0; new commit-bound authorization rollover if necessary; **separate explicit re-arm permission**. No `git pull` or automatic checkout movement on Intel; no re-arm, forced entries or retroactive persisted continuation edit. See `stage8_robot/PRODUCTION_OPERATOR_CHECKLIST.md` and `stage8_robot/PRODUCTION_STRATEGY_PASSPORT.md`.


Historical runbook content below records past activation and MUST NOT be read as current re-arm authority.


Status: **HISTORICALLY ACTIVATED; NOW HALTED (2026-10-12 fault) — RE-ARM NOT AUTHORIZED**

Production specification: `PROD_STAGE7_46DB784378797C7FB04636892350AFF21006D71A31F2CED9D4B974EDA2DC36B8`

Active identity: `TRAIL1__N4_01__FULL__R15`

Production code commit: `4c7cd7cbbde5fbffb63ed6984cf89b90dc50d129`

Stage 5 data commit: `50f1fd2178c18b7ab3bd969be82ad01f47a34745`

Stage 8.12.4 activation evidence SHA-256: `EA14B73FA1AE1D62C2324A0C76624DA792101FCD945383D70B646BDA1D6F8CB9`

Current operational authority after the 2026-10-08 H1 hotfix:

- original live-activation commit `883ea1ea6a8268276a8e39ebdc8786c643a21935` remains historical activation provenance;
- PR #435 merged as `4c7cd7cbbde5fbffb63ed6984cf89b90dc50d129`;
- Intel preactivation validation: `15/15 PASS`, heartbeat `HEALTHY / PASS`, positions `0`, unresolved intents `0`;
- durable authorization was rolled over to the new exact commit;
- final re-arm: kill switch `ARMED`, production task `Running`, entry gate `OPEN`, post-arm cycle count observed `1772`;
- frozen T3/TRAIL1/N4/FULL-R15/risk/execution semantics were not changed.

This runbook documents the current production implementation. It does **not** modify strategy logic, N4 membership, TRAIL1, FULL/R15 sizing, Stage 5 data authority, or research methodology.

## 0. Operating principles

1. Broker/account state is the external truth for positions and orders. The production service reconciles that truth against durable local state before publishing a healthy heartbeat.
2. New entries require all gates simultaneously: exact durable authorization, exact production/account binding, kill switch `ARMED`, fresh `HEALTHY / PASS` production heartbeat, zero unresolved intents, current H1 data, valid session, frozen signal, R15 capacity, margin capacity, and risk cap.
3. `HALTED` blocks new entries. It does not by itself flatten positions, cancel stops, stop the service, or revoke authorization.
4. Risk-reducing protection and emergency-exit paths remain available after HALT.
5. Never manually edit the authorization, kill-switch, heartbeat, or SQLite files.
6. Never run `git pull` in the production checkout while the Scheduled Task is bound to the accepted commit.
7. Do not change Stage 5 data checkout from the exact pinned commit.
8. Do not deposit or withdraw cash during live production without a controlled procedure for `explained_external_cash_flows`; otherwise the realized-equity sizing basis can be distorted.
9. After every accepted production fix, immediately synchronize current operational authority in `CURRENT_STATE.md`, `PROJECT_CONTEXT.md`, `ROADMAP.md`, `METHODOLOGY.md`, this runbook, the Stage 8 README, authority provenance, and operator-facing passport/checklists. Preserve superseded commits as historical provenance, then independently verify factual GitHub `main` and the production checkout binding.

## 1. Critical runtime files

Runtime root:

`C:\TradingSystemLab\runtime`

Production state:

`C:\TradingSystemLab\runtime\state\stage8-12-production.sqlite3`

Production heartbeat:

`C:\TradingSystemLab\runtime\diagnostics\stage8-12-4-production-heartbeat.json`

Kill switch:

`C:\TradingSystemLab\runtime\safety\stage8-trading-kill-switch.json`

Durable authorization:

`C:\TradingSystemLab\runtime\safety\stage8-12-4-production-authorization.json`

Operational log:

`C:\TradingSystemLab\runtime\logs\stage8-12-production.log`

The operational log rotates at 5 MB with 5 retained backups.

Production Scheduled Task:

`TradingSystemLab-Stage8-Production`

Historical readonly task:

`TradingSystemLab-Stage8-Readonly`

The readonly task must remain disabled during production.

## 2. Daily monitoring

### 2.1 Production heartbeat

Read:

```powershell
$r="c:\tradingsystemlab\runtime"; get-content "$r\diagnostics\stage8-12-4-production-heartbeat.json" -raw | convertfrom-json | format-list *
```

Critical fields:

- `health_status = HEALTHY`
- `reconciliation_status = PASS`
- `unresolved_intent_count = 0`
- `cycle_count >= 1` and should keep increasing
- `accepted_code_commit = 4c7cd7cbbde5fbffb63ed6984cf89b90dc50d129`
- `timestamp` fresh
- `last_successful_finam_api_contact` fresh
- `open_position_count` consistent with `position_protection`
- every open position must have exact covered quantity and at least one active protective-stop order id

Hard entry-gate freshness threshold:

- heartbeat age: maximum 900 seconds
- FINAM API contact age: maximum 900 seconds
- future clock skew tolerance: maximum 60 seconds

Normal operation uses a 30-second poll, so an operator should normally see a much fresher heartbeat than the 900-second hard limit. Treat a heartbeat older than roughly 2 minutes as a warning worth checking, even though the hard gate is 15 minutes.

`open_position_count = 0` is not required. Zero means flat. A nonzero value is valid if broker/local reconciliation and protection are exact.

### 2.2 Kill switch

Read:

```powershell
$r="c:\tradingsystemlab\runtime"; get-content "$r\safety\stage8-trading-kill-switch.json" -raw | convertfrom-json | select-object state,generation,updated_utc
```

Normal live state:

`state = ARMED`

`generation` is an integer revision counter. Every atomic rewrite of the kill switch increments it. It is not a trade count and not an authorization generation.

### 2.3 Durable authorization

Read only the non-secret fields:

```powershell
$r="c:\tradingsystemlab\runtime"; get-content "$r\safety\stage8-12-4-production-authorization.json" -raw | convertfrom-json | select-object status,execution_authorized,accepted_code_commit,authorized_utc
```

Normal live state:

- `status = AUTHORIZED`
- `execution_authorized = True`
- accepted commit equals the pinned production commit

There is no time-to-live or expiry field. Authorization does not expire simply because time passes. It fails closed if the file is absent/corrupt or its exact commit/account/evidence bindings do not match.

### 2.4 Scheduled Tasks

```powershell
get-scheduledtask -taskname "tradingsystemlab-stage8-production" | select-object taskname,state
get-scheduledtask -taskname "tradingsystemlab-stage8-readonly" | select-object taskname,state
get-scheduledtaskinfo -taskname "tradingsystemlab-stage8-production"
```

Normal live state:

- production: `Running`
- readonly: `Disabled`

The production task is configured with an AtStartup trigger and restart policy: up to 10 restarts at 2-minute intervals if the process exits.

### 2.5 Operational log

Latest entries:

```powershell
$r="c:\tradingsystemlab\runtime"; get-content "$r\logs\stage8-12-production.log" -tail 100
```

Follow live:

```powershell
$r="c:\tradingsystemlab\runtime"; get-content "$r\logs\stage8-12-production.log" -tail 50 -wait
```

Search faults:

```powershell
$r="c:\tradingsystemlab\runtime"; select-string -path "$r\logs\stage8-12-production.log*" -pattern "PRODUCTION_CYCLE_FAULT|STAGE8_12_4_|FINAM_"
```

Healthy cycles contain `PRODUCTION_CYCLE_PASS`.

Any `PRODUCTION_CYCLE_FAULT` deserves review. A transient fault may recover automatically, but repeated faults or a persistent `UNHEALTHY / FAULT` heartbeat require operator attention.

## 3. Weekly monitoring

Reconciliation itself is not weekly: it runs every production cycle before a healthy heartbeat is published.

Weekly operator review should confirm:

- heartbeat remains `HEALTHY / PASS`
- no unresolved intents remain
- broker positions match production positions
- every open position is protected
- production log has no recurring fault pattern
- Scheduled Task restart/last-result history is normal
- production checkout and Stage 5 data checkout remain at their exact pinned commits and clean

Read local production position state without modifying SQLite:

```powershell
$py="c:\tradingsystemlab\runtime\venv\scripts\python.exe"; $db="c:\tradingsystemlab\runtime\state\stage8-12-production.sqlite3"; & $py -c "import sqlite3,json; c=sqlite3.connect(r'$db'); r=c.execute('select value from state where key=?',('production_positions',)).fetchone(); print(json.dumps(json.loads(r[0]) if r else {},indent=2)); c.close()"
```

Read unresolved intents:

```powershell
$py="c:\tradingsystemlab\runtime\venv\scripts\python.exe"; $db="c:\tradingsystemlab\runtime\state\stage8-12-production.sqlite3"; & $py -c "import sqlite3; c=sqlite3.connect(r'$db'); rows=c.execute(\"select idempotency_key,status,broker_order_id,updated_at from intents where status not in ('CANCELLED','REJECTED','CLOSED','RECONCILED') order by updated_at\").fetchall(); print(*rows,sep='\n'); c.close()"
```

Expected result during steady state: no rows.

## 4. Monthly monitoring

### 4.1 Margin

Margin is checked automatically at every candidate entry.

The production service obtains fresh directional initial margin from FINAM asset parameters:

- LONG -> `long_initial_margin`
- SHORT -> `short_initial_margin`

Final quantity is:

`floor_to_lot(min(R15 quantity, margin quantity))`

If margin/R15 capacity is zero, the entry becomes `SKIP_ZERO_CAPACITY`. The robot does not increase quantity above R15.

A monthly review should compare current broker margin conditions with recent sizing behavior, but no manual monthly margin refresh is required for normal operation because entry sizing requests current margin parameters.

### 4.2 Realized equity

Production sizing basis:

`realized_equity = broker equity - broker unrealized_profit - explained_external_cash_flows`

The current value is stored in SQLite under `realized_equity`. The initial bootstrap is stored under `starting_realized_equity`.

Read:

```powershell
$py="c:\tradingsystemlab\runtime\venv\scripts\python.exe"; $db="c:\tradingsystemlab\runtime\state\stage8-12-production.sqlite3"; & $py -c "import sqlite3,json; c=sqlite3.connect(r'$db'); keys=('starting_realized_equity','realized_equity','explained_external_cash_flows','production_service_cycle_count'); [print(k,'=',(c.execute('select value from state where key=?',(k,)).fetchone() or [None])[0]) for k in keys]; c.close()"
```

Do not treat raw broker equity as R15 realized equity while a position is open.

### 4.3 External funding / deposits / withdrawals

The current production service does not contain an automatic cash-flow classification engine. It has the state key `explained_external_cash_flows`, initialized to zero.

Therefore: **do not make a new deposit or withdrawal during live production and assume the robot will distinguish it from trading PnL automatically.**

A new external cash flow requires a controlled operator procedure before allowing new sizing from that changed account balance.

### 4.4 Drawdown

The current Stage 8.12 runtime does not maintain a canonical production drawdown time series or DD metric.

DD must therefore be reconstructed from broker/account history or a separate read-only production analytics process. Do not infer DD from the single current `realized_equity` value.

No new production DD kill threshold is defined in the current frozen specification. Do not invent one inside the live runtime.

## 5. PnL

The production runtime's `realized_equity` is a **sizing authority**, not a complete PnL report.

Operational realized change can be compared against `starting_realized_equity`, subject to correctly accounted external cash flows.

The current Stage 8.12 production path does not maintain a separate canonical ledger for:

- commissions
- broker fees
- separate funding/financing components
- a full production PnL report by day/month/instrument

The generic SQLite schema has a `fills` table with a fee field, but the current production service/runtime does not use `persist_fill` to build a complete production fee/PnL ledger.

For accounting-grade PnL, commissions, and broker charges, use the broker statement/account reporting. Do not manufacture missing attribution from runtime state.

## 6. How the robot decides

### 6.1 Frozen T3/H1 signal

Decision core parameters:

- EMA100
- EMA100 slope
- ADX14 threshold 20
- ATR14 vs ATR mean20
- prior 20-bar breakout high/low
- initial stop 2.5 ATR
- TRAIL1 candidate 3 ATR

LONG requires:

- context close > EMA100
- EMA100 slope > 0
- ADX14 > 20
- ATR14 > ATR mean20
- completed H1 bar close > prior high

SHORT is symmetric:

- context close < EMA100
- EMA100 slope < 0
- ADX14 > 20
- ATR14 > ATR mean20
- completed H1 bar close < prior low

EMA50/EMA200 are observables, not entry gates.

Only completed bars are processed. The entry candle is excluded from later position management by a persisted H1 watermark.

### 6.2 R15 sizing

Base risk cash for one new instrument position:

`realized_equity * 0.015`

Loss per contract:

`abs(entry - stop) / price_step * tick_value`

R15 quantity is rounded down to the contract quantity granularity.

Then current directional margin capacity is applied.

Final quantity:

`floor_to_lot(min(r15_quantity, margin_quantity))`

Maximum nominal simultaneous initial-risk authority remains 6% of realized equity. Pyramiding is not authorized.

### 6.3 Protective stop

After an entry position is proven by exact broker/account position, the runtime creates a durable `PROTECTIVE_STOP_INSTALL` intent.

The broker SL/TP order is reconciled and then the local position becomes `protective_stop_state = ACTIVE`.

An open local position without an active exact protective stop is a production fault.

### 6.4 TRAIL1

At +1R, TRAIL1 is triggered from a completed H1 bar. Activation cannot occur on the same trigger bar.

On the next eligible event it activates the stored trailing candidate. Thereafter the stop only tightens.

TRAIL1 candidate:

- LONG: favorable extreme - 3 * ATR
- SHORT: favorable extreme + 3 * ATR

When the canonical stop tightens, the runtime creates a `PROTECTIVE_STOP_REPLACE` intent.

### 6.5 Exit and emergency exit

The broker protective stop is the primary external protection.

If the completed-bar strategy logic says the stop should already have been hit but the broker account still shows the position open, the runtime creates `EMERGENCY_EXIT_REQUIRED` and submits a market exit for the exact observed position.

There is no generic operator `flatten all` command in the current production runtime.

## 7. Error handling and recovery

### 7.1 Normal cycle error

On a production-cycle exception:

- heartbeat is written as `UNHEALTHY / FAULT`
- fault code is written to `stage8-12-production.log`
- service does not normally exit
- it retries after 3 seconds

Healthy steady-state polling is 30 seconds.

If unresolved intents exist, the loop also uses the 3-second fast reconciliation interval.

### 7.2 Uncertain order submission

If FINAM submission outcome is uncertain, the durable intent becomes `UNCERTAIN`.

The system does not blindly retry the POST. It requires broker proof through reconciliation.

While an unresolved intent exists:

- new signal evaluation/new entries are blocked
- heartbeat becomes fault/unhealthy around the action
- service reconciles at the fast interval

This production behavior is not the old Stage 8.11 `OIR + automatic HALT` acceptance workflow. Do not assume every timeout automatically flips the production kill switch to HALTED.

### 7.3 Position mismatch / unexpected position / unexpected order

Examples include:

- `STAGE8_12_4_UNEXPECTED_BROKER_POSITION`
- `STAGE8_12_4_UNEXPECTED_ACTIVE_BROKER_ORDER`
- `STAGE8_12_4_POSITION_RECONCILIATION_MISMATCH`
- `POSITION_AUTHORITY_UNEXPECTED_QUANTITY`

These are fail-closed production faults. New entry eligibility is lost because heartbeat/reconciliation is no longer healthy.

Do not "fix" SQLite to match the broker. Broker truth and durable intents must be investigated first.

### 7.4 Stale H1

If the expected completed H1 close is not present in current FINAM completed-bar data, the service raises:

`STAGE8_12_4_STALE_COMPLETED_H1_DATA`

The cycle faults; new entries do not proceed.

### 7.4.1 Revised historical H1 OHLC

Once a completed H1 bar has been accepted into the Stage-5/persisted production authority, that accepted OHLC is immutable. If a later FINAM historical response revises OHLC for the same already-accepted timestamp, production keeps the accepted authority row and does not rewrite prior history.

Timestamp continuity remains fail-closed: duplicate timestamps, an unknown timestamp inside the overlap, a missing exact splice seam, no overlap, or stale current H1 data still fault the cycle.

### 7.5 Network/API failure

Network/API errors produce a fault cycle and fast retry.

Existing broker-side protective orders remain at the broker if they were already accepted and active. However local TRAIL1 updates and any new emergency-exit submission cannot occur until connectivity returns.

Persistent network failure therefore requires operator attention even if a server-side protective stop exists.

## 8. Emergency halt — first operator action

### 8.1 Halt new entries

Use the production implementation; do not manually edit JSON:

```powershell
set-location "c:\tradingsystemlab\market-pattern-discovery"; $r="c:\tradingsystemlab\runtime"; $py="c:\tradingsystemlab\runtime\venv\scripts\python.exe"; & $py -c "from pathlib import Path; from TradingSystemLab.stage8_robot.trading_safety_gate import emergency_halt; print(emergency_halt(Path(r'$r')))"
```

Verify:

```powershell
$r="c:\tradingsystemlab\runtime"; get-content "$r\safety\stage8-trading-kill-switch.json" -raw | convertfrom-json | select-object state,generation,updated_utc
```

Expected: `HALTED`.

**HALT does not close existing positions.**

If positions are open, normally keep the production service running so it can continue risk-reducing protection/reconciliation. Do not immediately kill the process just because new entries were halted.

### 8.2 Full service stop

If the account is flat, or a deliberate operator intervention requires a full stop:

```powershell
stop-scheduledtask -taskname "tradingsystemlab-stage8-production" -erroraction silentlycontinue
disable-scheduledtask -taskname "tradingsystemlab-stage8-production"
```

Do not use full service stop as the first response to an ordinary open-position issue unless broker protection and manual recovery responsibility are understood.

## 9. Resume / re-arm

There is no separate canonical `resume.ps1` in the current production repository.

Re-arm is an explicit operator action and should happen only after:

- exact production commit is still pinned and clean
- Stage 5 data commit is still pinned and clean
- authorization loads successfully
- production task is running
- heartbeat is fresh `HEALTHY / PASS`
- unresolved intents = 0
- broker/local positions and protection are reconciled

If the task was disabled, first enable and start it while kill switch remains HALTED:

```powershell
enable-scheduledtask -taskname "tradingsystemlab-stage8-production"
start-scheduledtask -taskname "tradingsystemlab-stage8-production"
```

Wait for a fresh healthy heartbeat.

Then, only after explicit operator decision, re-arm through the implementation rather than editing the file:

```powershell
set-location "c:\tradingsystemlab\market-pattern-discovery"; $r="c:\tradingsystemlab\runtime"; $py="c:\tradingsystemlab\runtime\venv\scripts\python.exe"; & $py -c "from pathlib import Path; from TradingSystemLab.stage8_robot.trading_safety_gate import write_kill_switch; print(write_kill_switch(Path(r'$r'),'armed'.upper(),allow_arm=True))"
```

Verify fresh post-arm heartbeat before considering recovery complete.

## 10. Restart and reboot

### 10.1 Controlled service restart

Recommended sequence:

1. HALT new entries.
2. Confirm broker/local reconciliation and, if positions are open, confirm active protective stops.
3. Stop the production Scheduled Task.
4. Start it again.
5. Wait for a new `HEALTHY / PASS` heartbeat while still HALTED.
6. Re-arm only after explicit operator decision.

If the task is already enabled:

```powershell
stop-scheduledtask -taskname "tradingsystemlab-stage8-production" -erroraction silentlycontinue
start-scheduledtask -taskname "tradingsystemlab-stage8-production"
```

### 10.2 Reboot

The production task has an AtStartup trigger. If it remains enabled, the machine can restart the service after Windows reboot.

Durable authorization and kill-switch state persist on disk.

Therefore, if a planned reboot must **not** resume live entry eligibility automatically, HALT before reboot.

## 11. Broker truth and reconciliation

The production service uses:

- `GET /account` position quantities as synchronous position/fill authority
- broker order list for active regular and SL/TP order reconciliation
- exact client-order/idempotency bindings

The service rejects unexpected broker positions/orders that cannot be explained by durable production state/intents.

Operational comparison order:

1. FINAM broker account/terminal: actual positions and active orders.
2. Production heartbeat: reconciled position/protection summary.
3. SQLite: durable production positions and intents.
4. Production log: fault/recovery chronology.

Never make SQLite "match" an unexpected broker state by hand.

## 12. Unexpected order

If an order appears that cannot be explained by production intents:

1. HALT new entries immediately.
2. Check broker position and all active regular/SLTP orders.
3. Check heartbeat and production log.
4. Query unresolved intents.
5. Do not create a compensating robot order by guess.
6. If immediate risk reduction is required, broker-side manual intervention is an operator decision; afterward all resulting positions/orders must be reconciled before re-arm.

## 13. Manual closing of positions

The current production runtime has no generic operator `close all positions` command.

Manual broker closing can make local state temporarily disagree with broker state. The service can recognize a flat broker position, but a still-active protective stop must also become terminal/cancelled before local exit cleanup is complete.

Therefore manual flattening is an **operator-intervention procedure**, not a normal command.

Minimum safe principle:

- HALT new entries first
- use broker truth
- account for linked protective SL/TP orders
- verify flat broker position
- verify no orphan active protective order
- wait for production reconciliation to return `HEALTHY / PASS`
- only then consider re-arm

## 14. Code update

Do **not** run `git pull` in the active production checkout.

The production launcher requires exact HEAD:

`4c7cd7cbbde5fbffb63ed6984cf89b90dc50d129`

and a clean checkout.

A new code version is not an in-place update. It requires a controlled deployment lifecycle:

1. HALT.
2. Resolve/close or explicitly protect all live positions.
3. Back up durable state.
4. Validate new code separately.
5. Establish a new accepted production commit.
6. Rebind Scheduled Task to that exact commit.
7. Perform explicit authorization rollover because authorization is bound to the accepted commit.
8. Start HALTED, obtain `HEALTHY / PASS`, then explicitly re-arm.

The current durable authorization is create-once and cannot simply be overwritten for a new commit.

## 15. Stage 5 data update

Current production launcher hard-pins Stage 5 data to:

`50f1fd2178c18b7ab3bd969be82ad01f47a34745`

A different Stage 5 checkout fails closed.

Therefore Stage 5 data is not a routine updateable input in the live system. Any change requires a separately accepted authority/migration. Do not replace files or advance the Stage 5 repository in place.

## 16. Authorization rollover

Current authorization contains:

- schema id
- `AUTHORIZED` status
- production specification id
- active identity
- accepted production commit
- sanitized account hash
- Stage 8.12.2 evidence SHA
- Stage 8.12.3 evidence SHA
- `execution_authorized = true`
- authorization UTC timestamp

It has no expiry timer.

If the exact commit/account/evidence binding changes, the current file becomes invalid for the new authority.

Do not delete or edit it merely to get the service running. A re-authorization/migration must be a deliberate operator procedure.

## 17. Rollback / deactivate live production

Operational rollback is:

1. emergency HALT
2. keep service running while open positions require protection/reconciliation
3. after flat and clean, stop and disable the production task if full deactivation is desired

Authorization remains on disk. HALT does not erase it.

Do not delete authorization as a casual rollback mechanism.

## 18. What not to do

Forbidden or unsafe routine actions:

- do not `git pull` the production checkout
- do not advance the Stage 5 data checkout
- do not manually edit kill-switch JSON
- do not manually edit authorization JSON
- do not manually edit heartbeat JSON
- do not edit SQLite state/intents/positions to "repair" a mismatch
- do not run Stage 8.11 physical acceptance scripts as production controls
- do not start the historical readonly Scheduled Task
- do not retry uncertain order POSTs manually
- do not force a trade to test that the robot works
- do not alter T3/H1/TRAIL1/N4/R15/6% risk authority inside production
- do not deposit/withdraw cash without a controlled external-cash-flow procedure
- do not re-arm after a fault until broker/local reconciliation is healthy

## 19. Automatic alerting

No external automatic notification/alerting channel is implemented in the current Stage 8.12 production path.

Current automatic mechanisms are:

- heartbeat file
- operational rotating log
- fail-closed entry gate
- 3-second fast recovery/reconciliation loop after faults/unresolved intents
- Windows Scheduled Task restart policy if the process exits

Therefore daily operator monitoring remains required unless a separate read-only alerting layer is later added.

## 20. What to watch if no positions open for a long time

Do not change the strategy merely because no trades occur.

Check in this order:

1. production heartbeat is healthy/fresh
2. kill switch is ARMED
3. authorization is exact
4. no unresolved intents
5. H1 data is current
6. trading session is open with required safety margin
7. margin/R15 capacity is nonzero
8. logs contain no repeated faults
9. only then conclude that the frozen T3 signal simply has not occurred

Absence of trades is not itself evidence of strategy decay.

## 21. When to reconsider the strategy

The live runtime contains no automatic strategy-decay detector and no production DD threshold that authorizes parameter changes.

Do not change strategy, N4, TRAIL1, R15, or the research methodology from production observations ad hoc.

If a separate research review is eventually required, it must be isolated from live production and follow the established research methodology. Production remains frozen until an explicit later decision replaces its authority.

## 22. Current roadmap position

Stage 8.12.4 is complete:

`STAGE_8_12_FULL_R15_PRODUCTION_AUTHORIZATION_COMPLETE`

There is no currently authorized `Package 6`, `Stage 8.12.5`, or `Stage 9` implied by completion.

The current next activity is continuous production operation and monitoring under the frozen production authority.

## 23. Five-minute operator checklist

Daily:

1. production task = Running
2. readonly task = Disabled
3. kill switch = ARMED
4. authorization = AUTHORIZED
5. heartbeat = HEALTHY
6. reconciliation = PASS
7. unresolved intents = 0
8. heartbeat/API timestamps fresh
9. cycle_count increased since prior check
10. if positions > 0: every position has exact protective coverage
11. no recurring `PRODUCTION_CYCLE_FAULT` in logs

If any critical item fails: **do not force a trade or edit state. Investigate. If risk is uncertain, HALT new entries first.**
