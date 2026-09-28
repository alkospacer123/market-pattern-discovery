"""CLI for the artifact-only Stage 5.7 closeout."""
from __future__ import annotations
import argparse
import tempfile
from pathlib import Path
from .stage5_closeout import DEFAULT_OUTPUT, build, sha256

def certify(output: Path = DEFAULT_OUTPUT) -> dict:
    with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
        # Preliminary builds are marked verified only for serialization; the
        # byte comparison below is the authority for the final build.
        build(Path(a), deterministic=True); build(Path(b), deterministic=True)
        names=sorted(p.name for p in Path(a).iterdir())
        if any(sha256(Path(a)/n)!=sha256(Path(b)/n) for n in names):
            raise RuntimeError("STAGE5_CLOSEOUT_DETERMINISM_FAILED")
    return build(output, deterministic=True)

def main() -> int:
    parser=argparse.ArgumentParser(); parser.add_argument("--certify",action="store_true"); parser.add_argument("--output",type=Path,default=DEFAULT_OUTPUT); args=parser.parse_args()
    audit=certify(args.output) if args.certify else build(args.output)
    print(audit["status"]); return 0

if __name__ == "__main__": raise SystemExit(main())
