"""Deterministic, read-only local runner for the temporal-alignment audit."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .temporal_alignment import (TemporalAlignmentError, infer_timestamp_semantics,
    load_frozen_datasets, validate_daily, validate_h1, validate_sessions, write_evidence)


def _manifest(root: Path) -> Path:
    direct = root / "FREEZE_MANIFEST.json"
    nested = root / "evidence" / "FREEZE_MANIFEST.json"
    if direct.is_file():
        return direct
    if nested.is_file():
        return nested
    raise TemporalAlignmentError(f"FREEZE_MANIFEST.json not found under: {root}")


def _report(document: dict[str, Any]) -> str:
    scores = document["timestamp_alignment"]["scores"]
    comparisons = document["timestamp_alignment"]["evidence"]
    lines = ["# Temporal alignment report", "", f"**Status:** {document['status']}", "",
        "The audit reads hash-verified frozen source bars without normalization, repair, or synthetic candles.", "",
        "## M1 higher-timeframe comparisons", "",
        "| Comparison | Hypothesis | Checked | Mismatches | Missing aggregate | Missing reference | Match |",
        "|---|---|---:|---:|---:|---:|---|"]
    for semantics in ("START", "END"):
        for row in comparisons[semantics]:
            lines.append(f"| M1->{row['timeframe']} | {semantics} | {row['checked_bars']} | {row['mismatch_count']} | {row['missing_aggregate_count']} | {row['missing_reference_count']} | {'PASS' if row['matches'] else 'FAIL'} |")
    lines += ["", "## Hypothesis scores", "", f"- START hypothesis score: **{scores['START']}**",
        f"- END hypothesis score: **{scores['END']}**",
        f"- Selected timestamp semantics: **{document['timestamp_alignment']['timestamp_semantics']}**", "",
        "## Daily and session boundaries", "",
        f"- TRADING_DATE vs CALENDAR_DATE result: **{document['daily_alignment']['daily_bar_semantics']}** (no trading-date assignment is invented).",
        f"- Session boundary checks: **{document['session_boundary_status']}**.",
        f"- Clearing interval checks: **{document['clearing_interval_status']}**.", "",
        "## H1 and causality safety", "",
        f"- H1 edge completeness: **{document['h1_edge_completeness']}**.",
        f"- Future-fill safety: **{document['future_fill_safety']}** (future-filled bars: {document['future_filled_count']}).", "",
        "Insufficient or contradictory evidence remains `UNRESOLVED`; the runner never guesses START or END."]
    return "\n".join(lines)


def run(freeze_root: Path, output_root: Path, symbol: str) -> int:
    symbol = symbol.upper()
    manifest = _manifest(freeze_root)
    passport = Path("bbw_system/config/instruments") / f"{symbol.lower()}.yaml"
    if not passport.is_file():
        raise TemporalAlignmentError(f"instrument passport not found: {passport}")
    datasets, metadata = load_frozen_datasets(manifest, passport, symbol)
    references = {tf: datasets[tf] for tf in ("M5", "M15", "M30", "H1")}
    alignment = infer_timestamp_semantics(datasets["M1"], references)
    sessions = validate_sessions(datasets["M1"], metadata)
    daily = validate_daily(datasets["M1"], datasets["D1"])
    semantics = alignment["timestamp_semantics"]
    h1_candidates = {name: validate_h1(datasets["M1"], datasets["H1"], name) for name in ("START", "END")}
    h1 = h1_candidates.get(semantics)
    session_status = "PASS" if sessions and all(row["status"] == "PASS" for row in sessions) else "UNRESOLVED"
    clearing_status = "PASS" if sessions and all(row.get("clearing_bar_count") == 0 for row in sessions) else "UNRESOLVED"
    future_count = (h1["future_filled_count"] if h1 else
                    max(candidate["future_filled_count"] for candidate in h1_candidates.values()))
    h1_edges = "PASS" if h1 and not h1["incomplete_h1_bars"] else "UNRESOLVED"
    required = (semantics != "UNRESOLVED", daily["daily_bar_semantics"] != "UNRESOLVED",
                session_status == "PASS", clearing_status == "PASS", h1_edges == "PASS", future_count == 0)
    document = {"schema_version": "bbw.temporal-alignment.v1", "symbol": symbol,
        "status": "READY" if all(required) else "UNRESOLVED", "freeze_manifest": str(manifest.resolve()),
        "timestamp_alignment": alignment, "daily_alignment": daily, "sessions": sessions,
        "session_boundary_status": session_status, "clearing_interval_status": clearing_status,
        "h1_edge_completeness": h1_edges, "h1_candidates": h1_candidates,
        "future_fill_safety": "PASS" if future_count == 0 else "FAIL", "future_filled_count": future_count}
    mtf = [row for name in ("START", "END") for row in alignment["evidence"][name]]
    readiness = "\n".join(["# Temporal alignment readiness", "", f"**Status:** {document['status']}", "",
        "A READY result only reports sufficient alignment evidence; it does not authorize normalization, indicators, strategy selection, or backtesting.",
        "" if document["status"] == "READY" else "No timestamp convention is selected when the evidence is insufficient or contradictory."])
    write_evidence(output_root, document, mtf, sessions, _report(document))
    (output_root / "READINESS.md").write_text(readiness.rstrip() + "\n", encoding="utf-8")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m bbw_system.temporal_alignment_cli",
        description="Audit temporal alignment using a hash-verified 03B-1 freeze bundle.")
    parser.add_argument("--freeze-root", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--symbol", required=True)
    args = parser.parse_args(argv)
    try:
        return run(args.freeze_root, args.output_root, args.symbol)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"temporal alignment failed closed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
