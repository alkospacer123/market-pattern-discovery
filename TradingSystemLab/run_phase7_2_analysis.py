"""Command-line entry point for Phase 7.2 artifact-only analysis."""
from __future__ import annotations

import json

from .multitimeframe.phase72 import run


def main() -> None:
    print(json.dumps(run(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
