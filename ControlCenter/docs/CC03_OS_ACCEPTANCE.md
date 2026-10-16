# CC-03 independent Windows OS execution evidence

Base `a6e9634bc0a5db378fcff32ea1bc8591baaf1d3c`, after merged #534. One Draft PR; no merge/auto-merge/Intel actions. Changes only ControlCenter; existing workflow unchanged.

Initial Linux engineering run: 351 PASS / 0 FAIL / 35 Windows-native SKIP. This is not Windows acceptance. Native run and exact final counts will be recorded after the existing pull_request Windows workflow executes on this Draft PR. Engineering status while native execution is pending: **NOT_VERIFIED**. No physical PASS is claimed.

Runtime retention is disabled. Legacy live contents remain CC03_LIVE_SOURCE_COMPATIBILITY_BLOCKED. Actual source availability is documented in [OS contract](CC03_WINDOWS_OS_OBSERVER.md); unavailable fields and required producers in [future connection specification](CC03_FUTURE_TELEMETRY_SPEC.md); maintenance in [bounded stop procedure](CC03_EXPORT_MAINTENANCE.md).

## Initial native engineering run: evidence retained, not a PASS

[38873837179](https://github.com/alkospacer123/market-pattern-discovery/actions/runs/38873837179), job `116884027834`, HEAD `19b05ebfa9964ec1b97f91ec515a5ed521c26329`: full suite **369 PASS / 2 FAIL / 15 POSIX-only SKIP**, OS group **31 PASS / 2 FAIL / 0 SKIP**. Task states, exact process identity, actual separate-SID access denial, immutable transport and installation rehearsal passed. One failure was a Windows cp1252 test-source decode error; fixed with explicit UTF-8. The material failure was **metadata noninterference NOT_PASSED**: the zero-access, all-sharing metadata handle caused `PermissionError(13, Access is denied)` in unchanged `os.replace`. The full job log was reviewed.

Consequent safety decision: remove metadata implementation from observer runtime; accept no production metadata paths, reject `metadata_enabled=true` before any native operation, and require UNKNOWN/DISABLED metadata placeholders in the receiving schema. Retain the failed experiment under CI with an explicit expected-conflict/recovery regression. That regression's PASS never becomes metadata source acceptance. A separate positive test must prove noninterference for the actually enabled Task/process observer.
