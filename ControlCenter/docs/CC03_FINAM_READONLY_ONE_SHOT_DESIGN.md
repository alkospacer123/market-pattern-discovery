# CC-03 — FINAM READONLY one-shot, offline candidate (no live authority)

**Status: DRAFT ENGINEERING ONLY. No live FINAM calls, install, tokens, DPAPI, H1 reads, M15 reads, Task changes, broker orders or panel activation.** This is a new candidate subcomponent within existing CC-03, not a new trading phase.

## Boundary

1. Future **separately approved non-Streamlit producer** obtains an authenticated FINAM READONLY observation for one independently verified H1 account. Its operational identity/token and all API traffic remain outside the Control Center panel and outside the existing H1 robot. This PR does not build or run that privileged producer; authorization and exact methods are pending.
2. A future producer must deliver original observed_at, retrieved_at, account identity proof from the authenticated context (not just echoed JSON), and explicit coverage for positions, active orders and fills. Missing/incomplete coverage means UNKNOWN — not flat, zero orders or no fills. H1-owned account mapping must be independently verified; N4 names do not establish ownership.
3. The function broker_readonly.contract.validate_candidate is a **pure offline shape checker** for mocked or already-supplied candidate bytes. It rejects duplicate keys, non-finite values, extra fields, wrong robot/source/account bindings, future/stale timestamps, wrong N4 instruments, bad ID hash format, duplicate or mismatched position/order linkage and invalid price/quantity types. A positive result always says OFFLINE_CANDIDATE_NOT_AUTHENTICATED and broker_authenticated=false. A 64-hex reference is not proof of ownership or cryptographic source authenticity.
4. The function collect_once is intentionally BLOCKED; the candidate cannot open an API or publish a live snapshot. The installed panel still uses accepted Task-only WINDOWS_OS_ONLY. No new Streamlit imports, routes, entrypoints or scheduled jobs.
5. The current CC receiver cannot display live broker positions/stops/fills. Prior to separately authorized activation we require a reviewed authenticated exporter, clean immutable completed CC-only record (close + fsync + unique name), pinned private source and admin-owned receiving policies, strict original timestamp/TTL/coverage semantics, independent Windows-native concurrency + ACL verification and a scoped CC receiver/UI change.

## Authority matrix

| Field | Candidate input | What UI can claim now |
| --- | --- | --- |
| Windows Task | Existing pinned OS scheduler observer | TASK_RUNNING when current; not H1 health |
| Broker positions | Future authenticated complete account snapshot | UNKNOWN (offline candidate is not authenticated) |
| Active stops | Future active orders **and** position/order/account linkage | UNKNOWN, never infer protection from order claim |
| Fills | Future authenticated trade history with completeness watermark | UNKNOWN |
| H1 health, cycles, signals/rejection reasons | Engine-origin evidence missing | UNKNOWN; broker cannot supply it |
| Equity/PnL/cashflows/margin | Separately validated account/ledger history missing | UNKNOWN |
| M15 | Independent absent source | NOT_DEPLOYED |

## Evidence / release gates

Local unit tests cover synthetic positive **shape only**, rejection cases, no cross-source token leak, non-authentication of empty/full lists, and lack of API/process/file capabilities. No hosted Windows-native/FINAM source test is claimed by local tests. Keep Draft until review; do not merge/install/activate on Intel without separate operator instruction. Always preserve H1/M15 strategy/risk/config/robot and both Task identities unchanged.
