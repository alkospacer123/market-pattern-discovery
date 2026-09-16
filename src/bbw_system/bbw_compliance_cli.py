"""CLI for BBW Strategy Compliance Audit v1."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .compliance import ComplianceAuditError, run_compliance_audit


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run read-only BBW Strategy Compliance Audit v1")
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--feature-root", required=True, type=Path)
    parser.add_argument("--normalized-root", required=True, type=Path)
    parser.add_argument("--baseline-root", required=True, type=Path)
    parser.add_argument("--candidate-root", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        result = run_compliance_audit(args.feature_root, args.normalized_root, args.baseline_root,
                                      args.candidate_root, args.output_root, args.symbol.upper())
        print(json.dumps(result, sort_keys=True))
        return 0
    except (ComplianceAuditError, OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"Compliance audit failed closed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
