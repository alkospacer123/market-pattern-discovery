"""Deterministic, strategy-free evidence freeze for local market data."""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any

import pandas as pd

from .data_pipeline import (FREQUENCIES, NORMALIZATION_VERSION, CalendarConfig,
    NormalizationConfig, build_manifest, coverage_report, file_sha256,
    liquidity_profile, normalize, read_source)
from .preflight import load_document

TARGETS = ("CNYRUBF", "IMOEXF", "GLDRUBF", "BR", "GOLD")
TIMEFRAMES = ("D1", "H1", "M30", "M15", "M5", "M1")
EVIDENCE_FILES = ("FREEZE_MANIFEST.json", "DATA_INVENTORY.md", "DATA_QUALITY.md",
    "DATA_COVERAGE.csv", "LIQUIDITY_SUMMARY.csv", "ROLLOVER_SUMMARY.csv", "DATA_READINESS.md")


def _value(passport: dict[str, Any], key: str) -> Any:
    item = passport.get(key)
    return item.get("value") if isinstance(item, dict) else item


def _token(name: str, value: str) -> bool:
    return bool(re.search(rf"(^|[^A-Z0-9]){re.escape(value.upper())}([^A-Z0-9]|$)", name.upper()))


def portable_identifier(path: Path, root: Path) -> str:
    """Stable, POSIX-form relative source identifier (never a machine prefix)."""
    return path.resolve().relative_to(root.resolve()).as_posix()


def load_passports(root: Path) -> dict[str, dict[str, Any]]:
    result = {}
    for symbol in TARGETS:
        path = root / f"{symbol.lower()}.yaml"
        if path.exists():
            result[symbol] = load_document(path)
    return result


def classify(path: Path, passports: dict[str, dict[str, Any]]) -> tuple[str | None, str | None]:
    name = path.stem.upper()
    symbol = None
    for target in TARGETS:
        aliases = passports.get(target, {}).get("aliases", []) or []
        if _token(name, target) or any(_token(name, str(alias)) for alias in aliases):
            symbol = target
            break
    timeframe = next((tf for tf in TIMEFRAMES if _token(name, tf)), None)
    return symbol, timeframe


def _series_type(frame: pd.DataFrame, passport: dict[str, Any]) -> tuple[str, str]:
    configured = _value(passport, "series_type")
    item = passport.get("series_type", {})
    if configured in {"individual_contract", "continuous_unadjusted", "continuous_adjusted"} and isinstance(item, dict) and item.get("verified"):
        return configured, "verified instrument passport"
    if "contract" in frame and frame.contract.notna().any():
        return "individual_contract", "contract column"
    return "unknown", "no explicit evidence"


def _h4_diagnostic(frame: pd.DataFrame, session_start: str) -> dict[str, int]:
    valid = frame[frame.status.eq("VALID")].copy()
    anchor = int(session_start.split(":")[0])
    valid["bucket"] = valid.timestamp.dt.floor("D") + pd.to_timedelta(
        ((valid.timestamp.dt.hour - anchor) % 24 // 4) * 4 + anchor, unit="h")
    counts = valid.groupby(["trading_date", "bucket"], sort=True).size()
    complete = int(counts.eq(4).sum())
    incomplete = int(counts.ne(4).sum())
    gaps = int(sum(max(0, 4 - int(n)) for n in counts))
    return {"buckets": len(counts), "complete": complete, "incomplete": incomplete,
        "session_end_valid": incomplete, "lost_h1_bars_due_to_gaps": gaps}


def _write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        writer.writeheader(); writer.writerows(rows)


def run_freeze(data_root: Path, output_root: Path, passport_root: Path) -> int:
    """Audit every candidate independently; no strategy code is imported or run."""
    data_root, output_root = data_root.resolve(), output_root.resolve()
    evidence, large = output_root / "evidence", output_root / "large_local_output"
    normalized_dir, diagnostics_dir, cache_dir = large / "normalized", large / "diagnostics", large / "cache"
    for directory in (evidence, normalized_dir, diagnostics_dir, cache_dir): directory.mkdir(parents=True, exist_ok=True)
    passports = load_passports(passport_root)
    inventory, manifests, qualities, coverage, liquids, rollovers = [], [], [], [], [], []
    paths = sorted((p for p in data_root.rglob("*") if p.is_file() and p.suffix.lower() in {".csv", ".txt"}), key=lambda p: portable_identifier(p, data_root).lower())
    for path in paths:
        symbol, timeframe = classify(path, passports)
        record = {"source_path": str(path.resolve()), "portable_id": portable_identifier(path, data_root),
            "filename": path.name, "source_sha256": file_sha256(path), "bytes": path.stat().st_size,
            "detected_symbol": symbol, "detected_timeframe": timeframe, "status": "NOT_TARGET", "reason": None}
        if not symbol or not timeframe:
            record["reason"] = "target symbol/timeframe not identified"
            inventory.append(record); continue
        try:
            raw, info = read_source(path)
            record.update({"detected_format": info["format"], "rows": len(raw), "first_timestamp": str(raw.timestamp.min()), "last_timestamp": str(raw.timestamp.max())})
        except Exception as exc:
            record.update({"status": "PARSE_FAILED", "reason": f"{type(exc).__name__}: {exc}"})
            inventory.append(record); continue
        try:
            passport = passports.get(symbol, {})
            session = _value(passport, "session") or {}
            calendar = passport.get("calendar", {}) or {}
            config = NormalizationConfig(symbol, timeframe, _value(passport, "source_timezone"),
                _value(passport, "exchange_timezone"), session.get("start"), session.get("end"),
                tuple(tuple(x) for x in (_value(passport, "breaks") or ())), CalendarConfig(
                    tuple(calendar.get("holiday_dates", ())), calendar.get("shortened_session_dates", {}),
                    {k: tuple(v) for k, v in calendar.get("special_session_dates", {}).items()}))
            normalized, quality = normalize(raw, config)
            record["status"] = "OK"
        except Exception as exc:
            record.update({"status": "NORMALIZATION_BLOCKED", "reason": f"{type(exc).__name__}: {exc}"})
            inventory.append(record); continue
        inventory.append(record)
        stem = f"{symbol}_{timeframe}_{record['source_sha256'][:12]}"
        normalized.to_csv(normalized_dir / f"{stem}.csv", index=False, lineterminator="\n")
        coverage_report(normalized, timeframe).to_csv(diagnostics_dir / f"{stem}_coverage.csv", index=False, lineterminator="\n")
        series_type, series_evidence = _series_type(normalized, passport)
        manifest = build_manifest(path, normalized, config)
        manifest.update({"portable_id": record["portable_id"], "bytes": record["bytes"], "detected_format": record["detected_format"], "series_type": series_type, "series_type_evidence": series_evidence})
        manifests.append(manifest)
        quality.update({"instrument": symbol, "timeframe": timeframe, "portable_id": record["portable_id"],
            "missing_timestamps": quality["large_gaps"], "suspicious_gaps": quality["large_gaps"],
            "nan_ohlc": quality["missing_ohlc"],
            "weekend_saturday_before": int((normalized.timestamp.dt.weekday.eq(5)).sum()),
            "weekend_sunday_before": int((normalized.timestamp.dt.weekday.eq(6)).sum()),
            "weekend_saturday_after": int((normalized.status.eq("VALID") & normalized.timestamp.dt.weekday.eq(5)).sum()),
            "weekend_sunday_after": int((normalized.status.eq("VALID") & normalized.timestamp.dt.weekday.eq(6)).sum())})
        qualities.append(quality)
        valid = normalized[normalized.status.eq("VALID")]
        dates = pd.to_datetime(valid.trading_date, errors="coerce")
        base = {"instrument": symbol, "timeframe": timeframe, "period": "ALL",
            "first_timestamp": manifest["first_timestamp"], "last_timestamp": manifest["last_timestamp"],
            "calendar_days": int((dates.max()-dates.min()).days + 1) if len(valid) else 0,
            "trading_dates": int(valid.trading_date.nunique()), "number_of_bars": len(valid), "full_year": "N/A"}
        coverage.append(base)
        for year, group in valid.groupby(valid.timestamp.dt.year, sort=True):
            year_dates = pd.to_datetime(group.trading_date)
            coverage.append({"instrument": symbol, "timeframe": timeframe, "period": int(year),
                "first_timestamp": group.timestamp.min().isoformat(), "last_timestamp": group.timestamp.max().isoformat(),
                "calendar_days": int((year_dates.max()-year_dates.min()).days+1), "trading_dates": group.trading_date.nunique(),
                "number_of_bars": len(group), "full_year": "YES" if year_dates.min().month == 1 and year_dates.max().month == 12 else "NO"})
        liquids.extend(liquidity_profile(normalized).to_dict("records"))
        transitions = []
        if "contract" in normalized:
            changed = normalized.contract.ne(normalized.contract.shift()) & normalized.contract.notna()
            transitions = [x.isoformat() for x in normalized.loc[changed, "timestamp"].iloc[1:]]
        rollovers.append({"instrument": symbol, "timeframe": timeframe, "portable_id": record["portable_id"],
            "series_type": series_type, "contract_ids_present": "YES" if "contract" in normalized and normalized.contract.notna().any() else "NO",
            "possible_contract_transitions": len(transitions), "explicit_roll_flags": int(normalized.roll_flag.sum()),
            "suspicious_jumps": quality["suspicious_price_jumps"], "suspected_transition_timestamps": ";".join(transitions),
            "note": "Suspicious jump is not a confirmed rollover."})
        (diagnostics_dir / f"{stem}_quality.json").write_text(json.dumps(quality, indent=2, sort_keys=True), encoding="utf-8")
        if timeframe == "H1" and session.get("start"):
            manifest["synthetic_h4_coverage"] = _h4_diagnostic(normalized, session["start"])

    # Stable ordering and JSON serialization make reruns byte-identical for unchanged inputs/config.
    manifests.sort(key=lambda x: (x["instrument"], x["timeframe"], x["portable_id"]))
    manifest_doc: dict[str, Any] = {"freeze_version": "1.0", "created_at": None,
        "created_at_note": "intentionally null: wall-clock time is excluded from deterministic evidence",
        "normalization_version": NORMALIZATION_VERSION, "instruments": {}}
    for item in manifests:
        manifest_doc["instruments"].setdefault(item["instrument"], {}).setdefault(item["timeframe"], []).append(item)
    (evidence / "FREEZE_MANIFEST.json").write_text(json.dumps(manifest_doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = ["# Data inventory", "", "Paths are local evidence; `portable_id` is stable across machine roots.", "",
        "| Portable ID | Local source path | File | Bytes | SHA256 | Format | Symbol | TF | Rows | First | Last | Status | Reason |",
        "|---|---|---|---:|---|---|---|---|---:|---|---|---|---|"]
    for x in inventory:
        vals = [x.get(k, "") for k in ("portable_id","source_path","filename","bytes","source_sha256","detected_format","detected_symbol","detected_timeframe","rows","first_timestamp","last_timestamp","status","reason")]
        lines.append("| " + " | ".join(str(v) if v is not None else "" for v in vals) + " |")
    (evidence / "DATA_INVENTORY.md").write_text("\n".join(lines)+"\n", encoding="utf-8")
    (evidence / "DATA_QUALITY.md").write_text("# Data quality\n\nNo rows are silently repaired. Counts are before filtering unless an `after` field is named.\n\n```json\n" + json.dumps(sorted(qualities, key=lambda x:(x["instrument"],x["timeframe"],x["portable_id"])), indent=2, sort_keys=True) + "\n```\n", encoding="utf-8")
    _write_csv(evidence/"DATA_COVERAGE.csv", coverage, ["instrument","timeframe","period","first_timestamp","last_timestamp","calendar_days","trading_dates","number_of_bars","full_year"])
    _write_csv(evidence/"LIQUIDITY_SUMMARY.csv", liquids, ["symbol","timeframe","hour","observations","mean_volume","median_volume","zero_volume_pct","median_candle_range","median_true_range"])
    _write_csv(evidence/"ROLLOVER_SUMMARY.csv", rollovers, ["instrument","timeframe","portable_id","series_type","contract_ids_present","possible_contract_transitions","explicit_roll_flags","suspicious_jumps","suspected_transition_timestamps","note"])
    readiness = ["# Data readiness", "", "This is metadata-freeze readiness, not baseline permission.", "",
        "| Instrument | H1_DATA_AVAILABLE | Synthetic H4 check | Status | Reasons |", "|---|---|---|---|---|"]
    for symbol in TARGETS:
        hs = [m for m in manifests if m["instrument"] == symbol and m["timeframe"] == "H1"]
        failed = [x for x in inventory if x.get("detected_symbol") == symbol and x["status"] not in {"OK", "NOT_TARGET"}]
        ready = bool(hs) and not failed and all(m["series_type"] in {"unknown","individual_contract","continuous_unadjusted","continuous_adjusted"} for m in hs)
        reasons = "requirements satisfied; rollover risk recorded" if ready else ("H1 absent or not successfully normalized" if not hs else "parse failure exists")
        h4 = json.dumps(hs[0].get("synthetic_h4_coverage", {}), sort_keys=True) if hs else "N/A"
        readiness.append(f"| {symbol} | {'YES' if hs else 'NO'} | {h4} | {'READY_FOR_METADATA_FREEZE' if ready else 'NOT_READY'} | {reasons} |")
    (evidence/"DATA_READINESS.md").write_text("\n".join(readiness)+"\n", encoding="utf-8")
    return 0
