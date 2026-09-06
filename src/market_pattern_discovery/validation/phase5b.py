"""Phase 5B artifact validator command."""
from __future__ import annotations
import json
from pathlib import Path
from market_pattern_discovery.discovery.execution_contract import load_execution_contract
from market_pattern_discovery.discovery.phase5b import validate_artifacts

def main() -> int:
    load_execution_contract()
    result = validate_artifacts(Path("results/phase5b"))
    print(json.dumps({"phase": "5B", **result}, indent=2, sort_keys=True))
    if result["status"] == "PASS": print("PHASE 5B: PASS")
    elif result["status"] == "INCOMPLETE / RESUMABLE": print("PHASE 5B: INCOMPLETE / RESUMABLE")
    else: print("PHASE 5B: FAIL")
    return 0 if result["status"] == "PASS" else 2

if __name__ == "__main__": raise SystemExit(main())
