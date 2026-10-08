# TradingSystemLab Stage 8.12 Production Runbook

Status: **LIVE PRODUCTION ACTIVATED**

Production specification: `PROD_STAGE7_46DB784378797C7FB04636892350AFF21006D71A31F2CED9D4B974EDA2DC36B8`

Active identity: `TRAIL1__N4_01__FULL__R15`

Production code commit: `883ea1ea6a8268276a8e39ebdc8786c643a21935`

Stage 5 data commit: `50f1fd2178c18b7ab3bd969be82ad01f47a34745`

Stage 8.12.4 activation evidence SHA-256: `EA14B73FA1AE1D62C2324A0C76624DA792101FCD945383D70B646BDA1D6F8CB9`

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
- `accepted_code_commit = 883ea1ea6a8268276a8e39ebdc8786c643a21935`
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

`883ea1ea6a8268276a8e39ebdc8786c643a21935`

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
