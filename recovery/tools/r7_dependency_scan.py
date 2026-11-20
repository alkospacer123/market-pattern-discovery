#!/usr/bin/env python3
"""Offline, read-only inventory of references to historical root packages.

STDOUT is JSON. Never accesses brokers/networks or executes repository code.
Usage:
  python recovery/tools/r7_dependency_scan.py --repo /path/to/checkout --output /outside/report.json
This is a conservative literal-reference scan, NOT a dependency closure proof.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import subprocess
import sys

PROTECTED_ROOTS = frozenset({
    "V20_TradingSystem_M15", "ControlCenter", "TradingResearchLab",
    "TradingSystemLab", "IntradayLab", "recovery", ".github",
})
LEGACY_ROOTS = frozenset({
    "BBW", "bbw_system", "src", "tests", "config", "schemas",
    "scripts", "research", "results", "docs", "evidence",
    "pyproject.toml", "research_domains.md",
})
TEXT_SUFFIXES = frozenset({
    ".py", ".ps1", ".psm1", ".psd1", ".md", ".txt", ".rst", ".json",
    ".toml", ".ini", ".cfg", ".yaml", ".yml", ".sh", ".cmd",
    ".bat", ".xml", ".js", ".ts", ".csv",
})
# Reference-specific strings: explicit names, not generic 'BBW' indicator or 'results'.
REF_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("package:bbw_system", re.compile(r"\bbw_system\b", re.I)),
    ("package:market_pattern_discovery", re.compile(r"\bmarket_pattern_discovery\b", re.I)),
    ("historical:unknown_universe_v1", re.compile(r"\bunknown_universe_v1\b", re.I)),
    ("historical:research_domains.md", re.compile(r"\bresearch_domains\.md\b", re.I)),
    ("historical:root_pyproject", re.compile(r"\bpyproject\.toml\b", re.I)),
    ("historical:audit_only", re.compile(r"\baudit_only[\\/]", re.I)),
    ("historical:BBW_path", re.compile(r"(?:^|[^\w])BBW[\\/]", re.M)),
    ("historical:legacy_src_import", re.compile(r"\bsrc[\\/](?:bbw_system|market_pattern_discovery)[\\/]?", re.I)),
    ("historical:legacy_script_path", re.compile(r"\bscripts[\\/](?:bbw|research|discovery|run_)", re.I)),
    ("historical:legacy_config_path", re.compile(r"\bconfig[\\/](?:unknown_universe_v1|bbw|research)", re.I)),
)
MAX_TEXT_BYTES = 2_000_000
SCHEMA = "r7-legacy-root-reference-scan/v1"


def git(cwd: pathlib.Path, *args: str) -> bytes:
    proc = subprocess.run(["git", *args], cwd=cwd, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, check=False, timeout=90)
    if proc.returncode:
        raise ValueError(f"git {' '.join(args)} failed: exit {proc.returncode}; "
                         f"error={proc.stderr.decode('utf-8', 'replace')[:250]}")
    return proc.stdout


def tracked_index(root: pathlib.Path) -> list[dict[str, str]]:
    """Uses Git index blob object IDs; never hashes secrets into report."""
    raw = git(root, "ls-files", "--stage", "-z")
    found: list[dict[str, str]] = []
    for item in raw.split(b"\0"):
        if not item:
            continue
        head, sep, path = item.partition(b"\t")
        if not sep:
            raise ValueError("malformed git ls-files --stage output")
        mode, sha, stage = head.decode("ascii").split(" ")
        if stage != "0":
            raise ValueError("unmerged Git index: scan requires a resolved index")
        rel = path.decode("utf-8", "surrogateescape")
        # path traversal is never followed even in an unexpected/malicious index.
        if not rel or rel.startswith("/") or ".." in pathlib.PurePosixPath(rel).parts:
            raise ValueError("unsafe tracked path in index")
        found.append({"path": rel, "blob_sha": sha, "mode": mode})
    return sorted(found, key=lambda x: x["path"])


def scoped_group(path: str) -> str:
    first = path.split("/", 1)[0]
    if first in PROTECTED_ROOTS or first in ("README.md", "AGENTS.md", ".gitignore", ".gitattributes"):
        return "protected_or_entrypoint"
    if first in LEGACY_ROOTS:
        return "candidate_legacy_bundle"
    return "other"


def scan(root: pathlib.Path, *, expected_head: str | None = None,
         max_bytes: int = MAX_TEXT_BYTES) -> dict:
    root = root.resolve(strict=True)
    if (root / ".git").exists() is False and git(root, "rev-parse", "--show-toplevel").decode().strip() != str(root):
        raise ValueError("--repo must be a checkout top-level, not a subfolder")
    top = pathlib.Path(git(root, "rev-parse", "--show-toplevel").decode().strip()).resolve()
    if top != root:
        raise ValueError("--repo must point to Git checkout top-level")
    head = git(root, "rev-parse", "HEAD").decode().strip()
    if expected_head and expected_head.lower() != head.lower():
        raise ValueError(f"HEAD mismatch: expected {expected_head}, found {head}")
    status = git(root, "status", "--porcelain", "--untracked-files=no")
    tree = git(root, "rev-parse", "HEAD^{tree}").decode().strip()
    files = tracked_index(root)
    matches: list[dict] = []
    skipped: list[dict[str, str]] = []
    scanned = 0
    legacy_entries: list[dict[str, str]] = []
    for x in files:
        path = x["path"]
        first = path.split("/", 1)[0]
        if first in LEGACY_ROOTS:
            legacy_entries.append({"path": path, "blob_sha": x["blob_sha"]})
        p = root / path
        if p.is_symlink():
            skipped.append({"path": path, "why": "symlink"})
            continue
        if p.suffix.lower() not in TEXT_SUFFIXES and p.name not in ("Dockerfile", "Makefile"):
            continue
        try:
            if p.stat().st_size > max_bytes:
                skipped.append({"path": path, "why": "oversize_text"})
                continue
            raw = p.read_bytes()
        except OSError:
            skipped.append({"path": path, "why": "unreadable_or_missing"})
            continue
        if b"\x00" in raw[:4096]:
            skipped.append({"path": path, "why": "binary_content"})
            continue
        decoded = raw.decode("utf-8", "replace")
        if "\ufffd" in decoded:
            skipped.append({"path": path, "why": "non_utf8_decoded_replace"})
        scanned += 1
        for line_no, line in enumerate(decoded.splitlines(), 1):
            found = [key for key, pattern in REF_PATTERNS if pattern.search(line)]
            if found:
                # No source content copied to report: paths, line numbers, pattern labels only.
                matches.append({"source_path": path, "source_scope": scoped_group(path),
                                "line": line_no, "patterns": sorted(found)})
    match_groups = {"protected_or_entrypoint": 0, "candidate_legacy_bundle": 0, "other": 0}
    for m in matches:
        match_groups[m["source_scope"]] += 1
    return {
        "schema": SCHEMA,
        "head": head,
        "tree_sha": tree,
        "tracked_tree_modified": bool(status),
        "total_tracked": len(files),
        "legacy_bundle_tracked": len(legacy_entries),
        "legacy_blob_manifest": legacy_entries,
        "text_files_scanned": scanned,
        "pattern_labels": [x[0] for x in REF_PATTERNS],
        "reference_hits_by_scope": match_groups,
        "reference_hits": matches,
        "skipped": skipped,
        "verdict": "LITERAL_SCAN_ONLY_NOT_DEPENDENCY_CLOSURE",
        "safety": "No files changed, no network or broker access; do not delete based on this report",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=pathlib.Path, required=True)
    parser.add_argument("--output", type=pathlib.Path,
                        help="Optional JSON outside checkout; default stdout")
    parser.add_argument("--expected-head", help="Require exact Git commit SHA")
    parser.add_argument("--max-text-bytes", type=int, default=MAX_TEXT_BYTES)
    args = parser.parse_args(argv)
    if args.max_text_bytes < 4096:
        parser.error("--max-text-bytes must be >=4096")
    try:
        data = scan(args.repo, expected_head=args.expected_head,
                    max_bytes=args.max_text_bytes)
        out = json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
        if args.output:
            destination = args.output.expanduser().resolve()
            checkout = args.repo.resolve()
            if destination.is_relative_to(checkout):
                raise ValueError("--output must be outside Git checkout; never change source tree")
            # Only caller-provided path; creates a report outside checkout.
            destination.write_text(out, encoding="utf-8")
            print(json.dumps({"report_path": str(destination),
                              "sha256": hashlib.sha256(out.encode("utf-8")).hexdigest(),
                              "head": data["head"], "tracked": data["total_tracked"],
                              "scanned": data["text_files_scanned"],
                              "legacy_bundle_tracked": data["legacy_bundle_tracked"],
                              "protected_hits": data["reference_hits_by_scope"]["protected_or_entrypoint"],
                              "verdict": data["verdict"]}, ensure_ascii=False))
        else:
            print(out, end="")
        return 0
    except (ValueError, OSError, subprocess.TimeoutExpired) as ex:
        print(f"R7_DEPENDENCY_SCAN_ERROR: {ex}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
