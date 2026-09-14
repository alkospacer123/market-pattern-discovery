"""Generate Phase 4.1 reports exclusively from persisted Phase 4 artifacts."""
from pathlib import Path
import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from TradingSystemLab.walk_forward.borderline_diagnostics import run


if __name__ == "__main__":
    result = run()
    print(result["status"])
