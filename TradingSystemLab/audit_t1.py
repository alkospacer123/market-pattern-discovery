"""Audit the frozen T1 artifacts through the shared audit framework."""
from pathlib import Path

from .audit_t3 import run_audit

BASELINE_DIR = Path(__file__).parent / "results" / "T1_baseline"


def run(source: Path = BASELINE_DIR, output: Path | None = None) -> dict:
    return run_audit(source, output, strategy_name="T1_BBW_Donchian_v1.0",
                     audit_verdict="DESCRIPTIVE_BASELINE")


if __name__ == "__main__":
    run()
