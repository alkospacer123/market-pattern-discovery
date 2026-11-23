# Kimi Chat G2.2A — Control Center V20 training review (2026-11-23)

**State:** `CC_CHAT_TRAINING_SOURCE_AUDIT_ACCEPTED`; **NOT** `CC_EXAM_PASS`, `CODE_PRACTICAL_PASS`, `INSTALLED_VERIFIED`, `LIVE_ACCEPTED`, or `ARMED`.

## Source evidence and evaluation

- Operator submitted Kimi G2.2A source report, ~997 lines, spanning current architecture, readonly exporter, CC-07/08, permissions, failure matrix, V20 interfaces, tests/CI, historical documents and Kimi Code training plan.
- Source baseline: GitHub `main=e05bbd24db88f127a52f0ff1b7282d7c6919cd81`, independently fetched by GPT.
- **28/28 independently selected Git blob SHA matched** the reported values at the fixed `main`: `AGENTS.md`, passport, README, Kimi CC exam, operational Python/PowerShell files, source policy, tests and two CC CI workflows.
- Code spot checks verified: `v20_app.py` manual refresh, 3x5 commands and confirmation behavior; `v20_admin_control.py` one-shot dispatch and `FAILED_UNKNOWN` logic; `v20_contract.py` `age()` and `heartbeat_health()`; frozen CC03 workflow expected historical scope failure; `V20_KIMI_EXAM.md` scope.
- GPT **formative training score: 96/100**. The report is source-based and generally strong; no critical misrepresentations observed in checked parts. This is neither a blinded exam nor an independently executed full code review or CI run. Exact Kimi tool-call history not reconstructed.

## Targeted nuances for G2.2B and independent CC exam

1. **PAUSE vs Protect3:** CC-07 PAUSE means stock HALT new entries while Scheduled Task may continue to run and reconcile old positions, but `V20_TradingSystem_M15/v20_runtime/r070_linked_sltp.py` `stage_r070_protect3_cancel_first_once()` explicitly requires `Switch=ARMED` and fails `R070_PROTECT3_SWITCH_NOT_ARMED` under HALTED. Never claim that every form of SLTP replacement remains enabled on PAUSE. Nor does `Task=Running` prove worker running or broker stop protection.
2. **`age()` for UNKNOWN is intentionally latched in source:** `ControlCenter/cc/v20_contract.py` `age()` returns immediately for `STALE/NOT_CONNECTED/UNKNOWN`, while `heartbeat_health()` can return `STALE` when the observed timestamp exceeds TTL. Report flagged a possible display-contract test; this is **NOT YET A BUG**, test desired invariants with synthetic fixture before any change.
3. **Frozen CI:** `.github/workflows/controlcenter-cc03-windows-native.yml` checks exact CC03 historical tree and historical failure mode even for non-Markdown changes. Any future code change needs reviewed CI/design, not weakening frozen original acceptance. The docs-only workflow has a separate scope.
4. **Alternative gateway:** `v20_command_channel.py` / `cc07_command_worker.py` are not imported by current `v20_app.py`. No evidence the channel is installed on Intel. Do not confuse with current `v20_admin_control.py` → pinned `cc07-v20-operator.ps1`.
5. **Exporter READONLY meaning:** the fixed exporter can publish CC-owned JSON; 'READONLY' applies to trading/broker/Task/ARM controls, **not** a claim that zero local files are written.
6. **Production truth:** no contemporary installed checks or broker FINAM positions, active orders, SLTP, worker state, sid/ACL or `127.0.0.1:8502` listener proof obtained. Historical Intel acceptance is dated, not current. No live commands or tests run by Kimi or GPT in G2.2A.

## Pro quota ledger

- Before G2.2A, 2026-11-23 17:55: cumulative monthly `9.70%`, five-hour Code `0%`.
- After G2.2A, 2026-11-23 18:54: cumulative monthly `11.75%`, five-hour Code `0%`, extra paid usage OFF, next reset 2026-12-23.
- The difference `+2.05 percentage points` is across screenshots, not a certified per-task cost.

## Next gates

`G2.2B`: source-backed unfamiliar/negative CC cases targeting PAUSE/Protect3, UNKNOWN latch, timeout/dispatch, alternate gateway, CC03 CI and operator authority; **GitHub READONLY, no scripts, tasks, FINAM, local access or Git writes**.

`G2.2C`: new-chat independently graded CC theory, with no replay of earlier answers. Then `G2.3` TRL training and exam. Code practical, synthetic CI, GPT-outage, production read-only and final Kimi documentation revision remain later independent gates. Final Recovery is last.
