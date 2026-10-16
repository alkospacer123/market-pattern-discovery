# CC-03 independent Windows OS execution evidence

Base `a6e9634bc0a5db378fcff32ea1bc8591baaf1d3c`, after merged #534. One Draft PR; no merge/auto-merge/Intel actions. Changes only ControlCenter; existing workflow unchanged.

Initial Linux engineering run: 351 PASS / 0 FAIL / 35 Windows-native SKIP. This is not Windows acceptance. Native run and exact final counts will be recorded after the existing pull_request Windows workflow executes on this Draft PR. Engineering status while native execution is pending: **NOT_VERIFIED**. No physical PASS is claimed.

Runtime retention is disabled. Legacy live contents remain CC03_LIVE_SOURCE_COMPATIBILITY_BLOCKED. Actual source availability is documented in [OS contract](CC03_WINDOWS_OS_OBSERVER.md); unavailable fields and required producers in [future connection specification](CC03_FUTURE_TELEMETRY_SPEC.md); maintenance in [bounded stop procedure](CC03_EXPORT_MAINTENANCE.md).
