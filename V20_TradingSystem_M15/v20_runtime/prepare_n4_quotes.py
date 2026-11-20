"""Prepare SHA-pinned public N4 M15 CSV fixtures, never trading inputs.

Explicit one-shot offline research source preparation. Only GitHub raw quote
files, no FINAM endpoints, credentials, broker calls or running H1/M15 tasks.
A network connection is needed only while preparing the source fixtures.
"""
from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import tempfile
from urllib.request import urlopen

from .market_reference_descriptive import SOURCE_SHA256

DATA_SHA = "f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8"
DATA_REPO = "alkospacer123/market-pattern-data"
URL_ROOT = f"https://raw.githubusercontent.com/{DATA_REPO}/{DATA_SHA}/forever"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SYMBOLS = ("USDRUBF", "CNYRUBF", "GLDRUBF", "IMOEXF")


def prepare(root: Path) -> dict[str, str]:
    root = root.expanduser().resolve()
    checkout = PROJECT_ROOT.parent
    if root == checkout or checkout in root.parents:
        raise ValueError("SOURCE_FIXTURES_MUST_BE_OUTSIDE_V20_CHECKOUT")
    results: dict[str, str] = {}
    for symbol in SYMBOLS:
        expected = SOURCE_SHA256[symbol]
        filename = symbol + "_M15.csv"
        path = root / symbol / filename
        if path.is_file():
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
            if actual != expected:
                raise RuntimeError(f"EXISTING_SOURCE_HASH_MISMATCH:{symbol}")
            results[symbol] = "REUSED_SHA256_PASS"
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        address = f"{URL_ROOT}/{symbol}/{filename}"
        temp_name = None
        try:
            with tempfile.NamedTemporaryFile(
                    prefix=".v20_m15_", suffix=".part",
                    dir=path.parent, delete=False) as temp:
                temp_name = temp.name
                digest = hashlib.sha256()
                with urlopen(address, timeout=60) as stream:
                    while True:
                        block = stream.read(1024 * 256)
                        if not block:
                            break
                        temp.write(block)
                        digest.update(block)
            if digest.hexdigest() != expected:
                raise RuntimeError(f"DOWNLOADED_SOURCE_HASH_MISMATCH:{symbol}")
            if path.exists():
                raise RuntimeError(f"SOURCE_APPEARED_DURING_DOWNLOAD:{symbol}")
            os.replace(temp_name, path)
            temp_name = None
            results[symbol] = "DOWNLOADED_SHA256_PASS"
        finally:
            if temp_name is not None:
                Path(temp_name).unlink(missing_ok=True)
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True,
                        help="external fixture directory, e.g. /tmp/v20-n4-quotes")
    args = parser.parse_args()
    for symbol, state in prepare(args.output).items():
        print(f"{symbol}={state}")
    print(f"PINNED_PUBLIC_DATA_COMMIT={DATA_SHA}")
    print("NO_FINAM_NO_LIVE_NO_H1_M15_MUTATION=YES")


if __name__ == "__main__":
    main()
