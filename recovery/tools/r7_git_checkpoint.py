#!/usr/bin/env python3
"""R7-B protective Git-history checkpoint (NOT final disaster recovery).

Creates a NEW destination folder containing:
  <repo>.git/           -- full mirrored refs and Git object store
  <repo>.bundle         -- independently SHA256-verifiable Git bundle
  <repo>-verify.git/    -- isolated restore proof from bundle
  checkpoint-report.json

Never reads FINAM credentials, never executes trading code, never modifies
the source repository. The caller MUST separately copy/verify on independent
media and export GitHub PR/Issue/CI metadata before declaring R7-B PASS.

Example:
python r7_git_checkpoint.py --source https://github.com/OWNER/REPO.git \
    --destination X:/R7-checkpoint-20261120 --expected-main <40-hex>
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

SHA40 = re.compile(r"^[0-9a-fA-F]{40}$")


def run_git(*args: str, cwd: Path | None = None, timeout: int = 900) -> str:
    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"
    env["GIT_CONFIG_NOSYSTEM"] = "1"  # Local/global credential helpers still possible.
    try:
        result = subprocess.run(
            ["git", *args], cwd=cwd, env=env, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True, timeout=timeout, check=False,
        )
    except FileNotFoundError as exc:
        raise ValueError("Git executable not available") from exc
    if result.returncode:
        # Do NOT echo a source URL containing an embedded credential.
        raise ValueError(f"git failed (returncode={result.returncode}), "
                         "see local Git output privately; no token is logged")
    return result.stdout.strip()


def sha256_file(path: Path) -> str:
    d = hashlib.sha256()
    with path.open("rb") as stream:
        while True:
            block = stream.read(1024 * 1024)
            if not block:
                break
            d.update(block)
    return d.hexdigest()


def ensure_outside_local_source(source: str, dst: Path) -> None:
    if "://" in source or source.startswith("git@"):
        return
    src = Path(source).expanduser().resolve(strict=True)
    if dst == src or src in dst.parents or dst in src.parents:
        raise ValueError("destination must be separate from the source repository")


def checkpoint(source: str, destination: Path, expected_main: str,
               repo_basename: str = "market-pattern-discovery") -> dict:
    if not SHA40.fullmatch(expected_main):
        raise ValueError("--expected-main must be a 40-character Git SHA")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{1,100}", repo_basename):
        raise ValueError("--name must be a safe repository basename")
    destination = destination.expanduser().resolve()
    ensure_outside_local_source(source, destination)
    if destination.exists():
        raise ValueError("destination already exists; never overwrite a checkpoint")
    destination.mkdir(parents=True)
    mirror = destination / (repo_basename + ".git")
    bundle = destination / (repo_basename + ".bundle")
    restore = destination / (repo_basename + "-verify.git")
    run_git("clone", "--mirror", "--no-hardlinks", "--quiet", "--",
            source, str(mirror))
    main_sha = run_git("-C", str(mirror), "rev-parse", "refs/heads/main")
    if main_sha.lower() != expected_main.lower():
        raise ValueError(f"cloned main SHA mismatch: {main_sha}; checkpoint INVALID")
    run_git("-C", str(mirror), "fsck", "--full", "--strict", timeout=1800)
    refs = [line.split("\t", 1) for line in run_git(
        "-C", str(mirror), "for-each-ref",
        "--format=%(refname)%09%(objectname)").splitlines()]
    run_git("-C", str(mirror), "bundle", "create", str(bundle), "--all", timeout=1800)
    run_git("-C", str(mirror), "bundle", "verify", str(bundle), timeout=1800)
    run_git("clone", "--mirror", "--quiet", "--", str(bundle), str(restore), timeout=1800)
    run_git("-C", str(restore), "fsck", "--full", "--strict", timeout=1800)
    recovered_sha = run_git("-C", str(restore), "rev-parse", "refs/heads/main")
    if recovered_sha.lower() != expected_main.lower():
        raise ValueError("bundle restored main SHA mismatch; checkpoint INVALID")
    restored_refs = [line.split("\t", 1) for line in run_git(
        "-C", str(restore), "for-each-ref",
        "--format=%(refname)%09%(objectname)").splitlines()]
    if refs != restored_refs:
        raise ValueError("bundle restore ref list differs from mirror; checkpoint INVALID")
    report = {
        "schema": "r7-git-checkpoint/v1",
        "repo_name": repo_basename,
        "main_sha": main_sha,
        "expected_main": expected_main.lower(),
        "mirror_fsck": "PASS",
        "bundle_verify": "PASS",
        "cold_git_bundle_clone_fsck": "PASS",
        "refs_count": len(refs),
        "refs": [{"name": ref, "sha": sha} for ref, sha in refs],
        "bundle_file": bundle.name,
        "bundle_bytes": bundle.stat().st_size,
        "bundle_sha256": sha256_file(bundle),
        "independent_media_copy": "NOT_VERIFIED",
        "github_pr_issues_ci_metadata_export": "NOT_INCLUDED",
        "git_lfs_external_objects": "NOT_VERIFIED",
        "source_installations_and_sqlite": "NOT_INCLUDED",
        "r7_checkpoint_status": "PARTIAL_GIT_ONLY_NOT_FINAL_RECOVERY",
        "safety": "No LIVE / FINAM / source-repo modifications or broker requests",
    }
    out = destination / "checkpoint-report.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                   encoding="utf-8")
    return report


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source", required=True, help="Git remote URL or local Git repository")
    ap.add_argument("--destination", type=Path, required=True, help="NEW external directory")
    ap.add_argument("--expected-main", required=True)
    ap.add_argument("--name", default="market-pattern-discovery")
    args = ap.parse_args(argv)
    try:
        r = checkpoint(args.source, args.destination, args.expected_main, args.name)
        print(json.dumps({
            "main_sha": r["main_sha"], "refs_count": r["refs_count"],
            "bundle_sha256": r["bundle_sha256"],
            "bundle_bytes": r["bundle_bytes"],
            "checkpoint_status": r["r7_checkpoint_status"],
        }, ensure_ascii=False))
        return 0
    except (ValueError, OSError, subprocess.TimeoutExpired) as exc:
        print(f"R7_GIT_CHECKPOINT_FAILED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
