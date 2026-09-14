"""PowerShell-friendly local inventory, normalization, and audit runner."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from typing import Any
import pandas as pd

from .data_pipeline import (NormalizationConfig, build_manifest, coverage_report,
    file_sha256, infer_identity, liquidity_profile, normalize, read_source)
from .preflight import assert_baseline_ready, load_document
from .data_freeze import run_freeze


def inventory(root: Path) -> list[dict[str, Any]]:
    records = []
    for path in sorted(p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in {".csv", ".txt"}):
        symbol, timeframe = infer_identity(path)
        record: dict[str, Any] = {"source_path": str(path.resolve()), "filename": path.name, "probable_symbol": symbol, "probable_timeframe": timeframe, "format": None, "delimiter": None, "encoding": None, "timestamp_format": None, "first_timestamp": None, "last_timestamp": None, "rows": None, "columns": [], "timezone_status": "unknown", "file_sha256": file_sha256(path), "parse_status": "error"}
        try:
            frame, info = read_source(path)
            record.update(info); record.update({"timestamp_format": "YYYYMMDD HHMMSS" if info["format"] == "finam_csv" else "auto-detected", "first_timestamp": str(frame.timestamp.min()), "last_timestamp": str(frame.timestamp.max()), "rows": len(frame), "columns": list(map(str, frame.columns)), "timezone_status": "embedded" if getattr(frame.timestamp.dt, "tz", None) else "naive", "parse_status": "ok"})
        except Exception as exc:
            record["parse_error"] = str(exc)
        records.append(record)
    return records


def run_audit(data_root: Path, output: Path, passport_root: Path) -> int:
    output.mkdir(parents=True, exist_ok=True)
    records = inventory(data_root)
    (output / "data_inventory.json").write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")
    inventory_lines = ["# Data inventory", "", f"Scanned `{data_root.resolve()}`. Candidate identity is not verified metadata.", "",
        "| Path | File | Symbol | TF | Format | Delimiter | Encoding | First | Last | Rows | TZ | SHA256 | Parse |",
        "|---|---|---|---|---|---|---|---|---|---:|---|---|---|"]
    for item in records:
        inventory_lines.append("| " + " | ".join(str(item.get(k) if item.get(k) is not None else "—") for k in ("source_path","filename","probable_symbol","probable_timeframe","format","delimiter","encoding","first_timestamp","last_timestamp","rows","timezone_status","file_sha256","parse_status")) + " |")
    if not records:
        inventory_lines.append("| — | — | — | — | — | — | — | — | — | 0 | — | — | no files |")
    (output / "DATA_INVENTORY.md").write_text("\n".join(inventory_lines) + "\n", encoding="utf-8")
    quality, manifests, liquid = [], [], []
    for record in records:
        if record["parse_status"] != "ok" or not record["probable_symbol"] or not record["probable_timeframe"]: continue
        passport_path = passport_root / f'{record["probable_symbol"].lower()}.yaml'
        if not passport_path.exists(): continue
        passport = load_document(passport_path)
        def value(key):
            item = passport.get(key, {}); return item.get("value") if isinstance(item, dict) else item
        try:
            raw, _ = read_source(record["source_path"])
            session = value("session") or {}
            cfg = NormalizationConfig(record["probable_symbol"], record["probable_timeframe"], value("source_timezone"), value("exchange_timezone"), session.get("start"), session.get("end"), tuple(tuple(x) for x in value("breaks") or ()))
            normalized, report = normalize(raw, cfg)
        except ValueError as exc:
            quality.append({"instrument": record["probable_symbol"], "timeframe": record["probable_timeframe"], "blocked": str(exc)}); continue
        stem = f'{cfg.symbol}_{cfg.timeframe}'
        normalized.to_csv(output / f"{stem}_normalized.csv", index=False)
        coverage_report(normalized, cfg.timeframe).to_csv(output / f"{stem}_coverage.csv", index=False)
        liquid.append(liquidity_profile(normalized)); quality.append({"instrument": cfg.symbol, "timeframe": cfg.timeframe, **report})
        manifests.append(build_manifest(record["source_path"], normalized, cfg))
    (output / "data_quality.json").write_text(json.dumps(quality, indent=2), encoding="utf-8")
    (output / "manifest.json").write_text(json.dumps(manifests, indent=2), encoding="utf-8")
    if liquid: pd.concat(liquid).to_csv(output / "liquidity_profile.csv", index=False)
    (output / "DATA_QUALITY_REPORT.md").write_text("# Data quality report\n\n```json\n" + json.dumps(quality, indent=2) + "\n```\n", encoding="utf-8")
    available = {(m["instrument"], m["timeframe"]) for m in manifests}
    readiness = ["# Local BBW data readiness", "", "Availability reflects this audit only; metadata verification remains passport-controlled.", "",
        "| Instrument | H1 | M15 | M5 | M1 | Baseline-ready | Blocking reason |", "|---|---|---|---|---|---|---|"]
    for symbol in ("CNYRUBF", "IMOEXF", "GLDRUBF", "BR", "GOLD"):
        flags = ["YES" if (symbol, tf) in available else "NO" for tf in ("H1", "M15", "M5", "M1")]
        readiness.append(f"| {symbol} | {' | '.join(flags)} | NO | run baseline-preflight with verified passport and frozen strategy |")
    (output / "BBW_DATA_READINESS.md").write_text("\n".join(readiness) + "\n", encoding="utf-8")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="python -m bbw_system.data_cli")
    sub = parser.add_subparsers(dest="command", required=True)
    audit = sub.add_parser("audit"); audit.add_argument("--data-root", type=Path, required=True); audit.add_argument("--output", type=Path, required=True); audit.add_argument("--passport-root", type=Path, default=Path("bbw_system/config/instruments"))
    check = sub.add_parser("baseline-preflight"); check.add_argument("--passport", type=Path, required=True); check.add_argument("--strategy", type=Path, required=True)
    freeze = sub.add_parser("freeze"); freeze.add_argument("--data-root", type=Path, required=True); freeze.add_argument("--output-root", type=Path, required=True); freeze.add_argument("--passport-root", type=Path, default=Path("bbw_system/config/instruments")); freeze.add_argument("--symbols", nargs="+", help="optional canonical instrument scope")
    args = parser.parse_args(argv)
    if args.command == "audit": return run_audit(args.data_root, args.output, args.passport_root)
    if args.command == "freeze": return run_freeze(args.data_root, args.output_root, args.passport_root, args.symbols)
    assert_baseline_ready(load_document(args.passport), load_document(args.strategy)); print("Baseline preflight: READY"); return 0


if __name__ == "__main__": raise SystemExit(main())
