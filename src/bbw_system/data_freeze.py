"""Deterministic, strategy-free raw audit and optional data normalization."""
from __future__ import annotations

import csv
import itertools
import json
import re
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

from .data_pipeline import (NORMALIZATION_VERSION, NormalizationConfig,
    build_manifest, coverage_report, file_sha256, liquidity_profile, normalize, read_source)
from .preflight import load_document

TARGETS = ("CNYRUBF", "IMOEXF", "GLDRUBF", "BR", "GOLD")
TIMEFRAMES = ("D1", "H1", "M30", "M15", "M5", "M1")
FINAM_TIMEFRAMES = {"1": "M1", "5": "M5", "15": "M15", "30": "M30", "60": "H1", "D": "D1"}
EVIDENCE_FILES = ("FREEZE_MANIFEST.json", "DATA_INVENTORY.md", "DATA_QUALITY.md",
    "DATA_COVERAGE.csv", "LIQUIDITY_SUMMARY.csv", "ROLLOVER_SUMMARY.csv", "DATA_READINESS.md")
SKIP_DIRECTORIES = {".git", ".venv", "venv", "__pycache__", ".cache", "cache", "caches",
    "results", "result", "output", "outputs", "generated", "large_local_output"}


class IdentityError(ValueError):
    """Source identity is internally inconsistent or contradicts its filename."""


def _value(passport: dict[str, Any], key: str) -> Any:
    item = passport.get(key)
    return item.get("value") if isinstance(item, dict) else item


def _token(name: str, value: str) -> bool:
    return bool(re.search(rf"(^|[^A-Z0-9]){re.escape(value.upper())}([^A-Z0-9]|$)", name.upper()))


def portable_identifier(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def load_passports(root: Path) -> dict[str, dict[str, Any]]:
    result = {}
    for symbol in TARGETS:
        path = root / f"{symbol.lower()}.yaml"
        if path.exists():
            result[symbol] = load_document(path)
    return result


def classify(path: Path, passports: dict[str, dict[str, Any]]) -> tuple[str | None, str | None]:
    """Return weak filename/passport identity; source-column evidence is applied later."""
    name = path.stem.upper()
    symbol = None
    for target in TARGETS:
        aliases = passports.get(target, {}).get("aliases", []) or []
        if _token(name, target) or any(_token(name, str(alias)) for alias in aliases):
            symbol = target
            break
    return symbol, next((tf for tf in TIMEFRAMES if _token(name, tf)), None)


def _source_column(frame: pd.DataFrame, name: str) -> pd.Series | None:
    match = next((c for c in frame.columns if str(c).strip().lower().strip("<>") == name), None)
    return frame[match] if match is not None else None


def resolve_identity(path: Path, frame: pd.DataFrame, info: dict[str, Any],
                     passports: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Resolve canonical identity, preferring explicit Finam columns without hiding conflicts."""
    filename_symbol, filename_tf = classify(path, passports)
    symbol, timeframe = filename_symbol, filename_tf
    symbol_evidence = "passport_alias" if filename_symbol and not _token(path.stem, filename_symbol) else "filename_token"
    timeframe_evidence = "filename_token" if filename_tf else None
    if info.get("format") == "finam_csv":
        ticker = _source_column(frame, "ticker")
        per = _source_column(frame, "per")
        if ticker is None or per is None:
            raise IdentityError("FINAM_IDENTITY_COLUMNS_MISSING: <TICKER> and <PER> are required")
        tickers = sorted({str(x).strip().upper() for x in ticker.dropna() if str(x).strip()})
        periods = sorted({str(x).strip().upper() for x in per.dropna() if str(x).strip()})
        if len(tickers) != 1:
            raise IdentityError(f"MULTIPLE_SOURCE_TICKERS: {tickers}")
        if len(periods) != 1:
            raise IdentityError(f"MULTIPLE_SOURCE_PERIODS: {periods}")
        source_symbol = tickers[0] if tickers[0] in TARGETS else None
        source_tf = FINAM_TIMEFRAMES.get(periods[0])
        if filename_symbol and source_symbol != filename_symbol:
            raise IdentityError(f"IDENTITY_MISMATCH: filename symbol {filename_symbol}, Finam ticker {tickers[0]}")
        if filename_tf and source_tf != filename_tf:
            raise IdentityError(f"IDENTITY_MISMATCH: filename timeframe {filename_tf}, Finam PER {periods[0]}")
        symbol, timeframe = source_symbol, source_tf
        symbol_evidence, timeframe_evidence = "finam_ticker_column", "finam_per_column"
        return {"detected_symbol": symbol, "symbol_evidence": symbol_evidence,
            "detected_timeframe": timeframe, "timeframe_evidence": timeframe_evidence,
            "source_tickers": tickers, "source_periods": periods,
            "source_ticker_consistency": "PASS", "source_per_consistency": "PASS"}
    return {"detected_symbol": symbol, "symbol_evidence": symbol_evidence if symbol else None,
        "detected_timeframe": timeframe, "timeframe_evidence": timeframe_evidence,
        "source_tickers": [], "source_periods": [], "source_ticker_consistency": "NOT_APPLICABLE",
        "source_per_consistency": "NOT_APPLICABLE"}


def raw_audit(frame: pd.DataFrame, timeframe: str) -> dict[str, Any]:
    required = ("open", "high", "low", "close", "volume")
    missing = [x for x in required if x not in frame]
    ts = pd.to_datetime(frame.get("timestamp"), errors="coerce")
    numeric = {x: pd.to_numeric(frame[x], errors="coerce") for x in required if x in frame}
    bad_ohlc = int(pd.concat([numeric[x] for x in ("open", "high", "low", "close") if x in numeric], axis=1).isna().any(axis=1).sum()) if not missing else len(frame)
    if not missing:
        bad_ohlc = int((pd.concat([numeric[x] for x in ("open", "high", "low", "close")], axis=1).isna().any(axis=1)
            | (numeric["high"] < pd.concat([numeric["open"], numeric["close"], numeric["low"]], axis=1).max(axis=1))
            | (numeric["low"] > pd.concat([numeric["open"], numeric["close"], numeric["high"]], axis=1).min(axis=1))).sum())
    valid_ts = ts.dropna()
    expected = pd.Timedelta({"M1":"1min","M5":"5min","M15":"15min","M30":"30min","H1":"1h","D1":"1D"}[timeframe])
    deltas = valid_ts.diff().dropna()
    positive = deltas[deltas > pd.Timedelta(0)]
    consistent = bool(len(positive) == 0 or positive.median() == expected)
    return {"row_count": len(frame), "first_raw_timestamp": str(valid_ts.min()) if len(valid_ts) else None,
        "last_raw_timestamp": str(valid_ts.max()) if len(valid_ts) else None,
        "timestamp_parse_failures": int(ts.isna().sum()), "ohlcv_schema_presence": "PASS" if not missing else "FAIL",
        "missing_ohlcv_columns": missing, "invalid_or_missing_ohlc_count": bad_ohlc,
        "negative_volume_count": int((numeric.get("volume", pd.Series(dtype=float)) < 0).sum()),
        "duplicate_raw_timestamps": int(valid_ts.duplicated().sum()),
        "reversed_timestamp_ordering": int((ts.diff() < pd.Timedelta(0)).sum()),
        "timeframe_consistency": "PASS" if consistent else "FAIL",
        "median_positive_interval": str(positive.median()) if len(positive) else None,
        "fatal_corruption": bool(missing or ts.isna().any() or bad_ohlc or not consistent)}


def _metadata(passport: dict[str, Any]) -> tuple[list[str], dict[str, Any]]:
    session = _value(passport, "session") or {}
    values = {"source_timezone": _value(passport, "source_timezone"),
        "exchange_timezone": _value(passport, "exchange_timezone"),
        "session_start": session.get("start"), "session_end": session.get("end")}
    return [k for k, value in values.items() if not value], values


def _series_type(frame: pd.DataFrame, passport: dict[str, Any]) -> tuple[str, str]:
    configured, item = _value(passport, "series_type"), passport.get("series_type", {})
    if configured in {"individual_contract", "continuous_unadjusted", "continuous_adjusted"} and isinstance(item, dict) and item.get("verified"):
        return configured, "verified instrument passport"
    if "contract" in frame and frame.contract.notna().any():
        return "individual_contract", "contract column"
    return "unknown", "no explicit evidence"


def _write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        writer.writeheader(); writer.writerows(rows)


def _source_paths(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if any(part.lower() in SKIP_DIRECTORIES for part in path.relative_to(root).parts[:-1]):
            continue
        if path.is_file() and path.suffix.lower() in {".csv", ".txt"}:
            yield path


def _aggregate_coverage(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    usable = [r for r in records if r.get("raw_parse_status") == "PASS"]
    for (symbol, tf), group_iter in itertools.groupby(sorted(usable, key=lambda r:(r["detected_symbol"],r["detected_timeframe"],r["portable_id"])), key=lambda r:(r["detected_symbol"],r["detected_timeframe"])):
        group = list(group_iter); ranges = sorted((pd.Timestamp(r["first_raw_timestamp"]), pd.Timestamp(r["last_raw_timestamp"]), r["portable_id"]) for r in group)
        overlaps = sum(1 for left, right in zip(ranges, ranges[1:]) if right[0] <= left[1])
        gaps = sum(1 for left, right in zip(ranges, ranges[1:]) if right[0] > left[1])
        years = sorted({str(pd.Timestamp(r[edge]).year) for r in group for edge in ("first_raw_timestamp","last_raw_timestamp")})
        rows.append({"instrument":symbol,"timeframe":tf,"source_files":len(group),"earliest_raw_timestamp":str(min(x[0] for x in ranges)),
            "latest_raw_timestamp":str(max(x[1] for x in ranges)),"total_rows":sum(r["row_count"] for r in group),
            "overlapping_file_ranges":overlaps,"gaps_between_file_ranges":gaps,"yearly_source_period_coverage":";".join(years)})
    return rows


def run_freeze(data_root: Path, output_root: Path, passport_root: Path,
               symbols: Iterable[str] | None = None) -> int:
    """Raw-audit every source independently; normalize only when metadata is explicit."""
    data_root, output_root = data_root.resolve(), output_root.resolve()
    requested = tuple(dict.fromkeys(s.upper() for s in symbols)) if symbols else TARGETS
    unknown = sorted(set(requested) - set(TARGETS))
    if unknown: raise ValueError(f"Unknown --symbols: {unknown}")
    evidence, large = output_root / "evidence", output_root / "large_local_output"
    normalized_dir, diagnostics_dir = large / "normalized", large / "diagnostics"
    for directory in (evidence, normalized_dir, diagnostics_dir, large / "cache"): directory.mkdir(parents=True, exist_ok=True)
    passports = load_passports(passport_root)
    inventory: list[dict[str, Any]] = []; manifests=[]; qualities=[]; liquids=[]; rollovers=[]
    paths = sorted(_source_paths(data_root), key=lambda p: portable_identifier(p, data_root).lower())
    for path in paths:
        weak_symbol, weak_tf = classify(path, passports)
        record = {"source_path":str(path.resolve()),"portable_id":portable_identifier(path,data_root),"filename":path.name,
            "source_sha256":file_sha256(path),"bytes":path.stat().st_size,"detected_symbol":weak_symbol,
            "detected_timeframe":weak_tf,"raw_parse_status":"NOT_TARGET","normalization_status":"NOT_APPLICABLE",
            "normalization_block_reason":None,"status":"NOT_TARGET","reason":None}
        try:
            raw, info = read_source(path); record["detected_format"] = info["format"]
            identity = resolve_identity(path, raw, info, passports); record.update(identity)
        except IdentityError as exc:
            record.update({"raw_parse_status":"FAIL_IDENTITY","status":"IDENTITY_FAILED","reason":str(exc)})
            inventory.append(record); continue
        except Exception as exc:
            record.update({"raw_parse_status":"FAIL_PARSE","status":"PARSE_FAILED","reason":f"{type(exc).__name__}: {exc}"})
            inventory.append(record); continue
        symbol, timeframe = record["detected_symbol"], record["detected_timeframe"]
        if not symbol or not timeframe:
            record["reason"] = "target symbol/timeframe not identified"; inventory.append(record); continue
        if symbol not in requested:
            record.update({"raw_parse_status":"OUT_OF_SCOPE","status":"OUT_OF_SCOPE","reason":"excluded by --symbols"}); inventory.append(record); continue
        audit = raw_audit(raw, timeframe); record.update(audit)
        record.update({"first_timestamp":audit["first_raw_timestamp"],"last_timestamp":audit["last_raw_timestamp"],"rows":audit["row_count"]})
        record["raw_parse_status"] = "FAIL_CORRUPTION" if audit["fatal_corruption"] else "PASS"
        record["status"] = "RAW_INVALID" if audit["fatal_corruption"] else "RAW_VALID_METADATA_PENDING"
        passport = passports.get(symbol, {}); unresolved, metadata = _metadata(passport)
        series_type, series_evidence = _series_type(raw, passport)
        manifest = {"instrument":symbol,"timeframe":timeframe,"source_path":record["source_path"],"portable_id":record["portable_id"],"source_sha256":record["source_sha256"],
            "bytes":record["bytes"],"detected_format":record["detected_format"],"detected_symbol":symbol,
            "symbol_evidence":record["symbol_evidence"],"detected_timeframe":timeframe,"timeframe_evidence":record["timeframe_evidence"],
            "raw_parse_status":record["raw_parse_status"],"normalization_status":"PENDING_METADATA" if unresolved else "NOT_RUN",
            "normalization_block_reason":unresolved,"raw_audit":audit,"series_type":series_type,"series_type_evidence":series_evidence,
            "synthetic_h4_status":"PENDING_METADATA" if timeframe == "H1" and unresolved else "NOT_APPLICABLE"}
        if audit["fatal_corruption"]:
            manifest["normalization_status"]="BLOCKED_RAW_INVALID"; manifest["normalization_block_reason"]=["fatal_raw_corruption"]
        elif unresolved:
            record["normalization_status"]="PENDING_METADATA"; record["normalization_block_reason"]=",".join(unresolved)
        else:
            try:
                config=NormalizationConfig(symbol,timeframe,metadata["source_timezone"],metadata["exchange_timezone"],metadata["session_start"],metadata["session_end"],tuple(tuple(x) for x in (_value(passport,"breaks") or ())))
                normalized, quality=normalize(raw,config); record.update({"status":"OK","normalization_status":"PASS"})
                manifest.update(build_manifest(path,normalized,config)); manifest.update({"portable_id":record["portable_id"],"normalization_status":"PASS","normalization_block_reason":[]})
                stem=f"{symbol}_{timeframe}_{record['source_sha256'][:12]}"; normalized.to_csv(normalized_dir/f"{stem}.csv",index=False,lineterminator="\n")
                coverage_report(normalized,timeframe).to_csv(diagnostics_dir/f"{stem}_coverage.csv",index=False,lineterminator="\n")
                quality.update({"instrument":symbol,"timeframe":timeframe,"portable_id":record["portable_id"]}); qualities.append(quality)
                liquids.extend(liquidity_profile(normalized).to_dict("records"))
            except Exception as exc:
                reason=f"{type(exc).__name__}: {exc}"
                record.update({"status":"NORMALIZATION_BLOCKED","normalization_status":"FAIL","normalization_block_reason":reason})
                manifest.update({"normalization_status":"FAIL","normalization_block_reason":[reason]})
        manifests.append(manifest); inventory.append(record)
        rollovers.append({"instrument":symbol,"timeframe":timeframe,"portable_id":record["portable_id"],"series_type":series_type,
            "contract_ids_present":"YES" if "contract" in raw and raw.contract.notna().any() else "NO","possible_contract_transitions":0,
            "explicit_roll_flags":0,"suspicious_jumps":0,"suspected_transition_timestamps":"","note":"Rollover/series type is not guessed during raw audit."})

    manifests.sort(key=lambda x:(x["instrument"],x["timeframe"],x["portable_id"]))
    aggregate = _aggregate_coverage(inventory)
    manifest_doc={"freeze_version":"1.1","created_at":None,"created_at_note":"intentionally null: wall-clock time is excluded from deterministic evidence",
        "normalization_version":NORMALIZATION_VERSION,"scope":{"symbols":list(requested)},"aggregate_coverage":aggregate,"instruments":{}}
    for item in manifests: manifest_doc["instruments"].setdefault(item["instrument"],{}).setdefault(item["timeframe"],[]).append(item)
    (evidence/"FREEZE_MANIFEST.json").write_text(json.dumps(manifest_doc,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    fields=("portable_id","source_path","filename","bytes","source_sha256","detected_format","detected_symbol","symbol_evidence","detected_timeframe","timeframe_evidence","rows","first_timestamp","last_timestamp","raw_parse_status","normalization_status","normalization_block_reason","status","reason")
    lines=["# Data inventory","","Raw timestamps below are not timezone-converted or session-filtered.","","| "+" | ".join(fields)+" |","|"+"---|"*len(fields)]
    for x in inventory: lines.append("| "+" | ".join(str(x.get(k,"")) if x.get(k) is not None else "" for k in fields)+" |")
    (evidence/"DATA_INVENTORY.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    raw_quality=[{k:r.get(k) for k in ("detected_symbol","detected_timeframe","portable_id","raw_parse_status","ohlcv_schema_presence","invalid_or_missing_ohlc_count","negative_volume_count","duplicate_raw_timestamps","reversed_timestamp_ordering","timeframe_consistency","source_ticker_consistency","source_per_consistency")} for r in inventory if r.get("detected_symbol") in requested]
    (evidence/"DATA_QUALITY.md").write_text("# Data quality\n\nRaw audit is metadata-independent; no rows are repaired or filtered.\n\n```json\n"+json.dumps(raw_quality,indent=2,sort_keys=True)+"\n```\n",encoding="utf-8")
    _write_csv(evidence/"DATA_COVERAGE.csv",aggregate,["instrument","timeframe","source_files","earliest_raw_timestamp","latest_raw_timestamp","total_rows","overlapping_file_ranges","gaps_between_file_ranges","yearly_source_period_coverage"])
    _write_csv(evidence/"LIQUIDITY_SUMMARY.csv",liquids,["symbol","timeframe","hour","observations","mean_volume","median_volume","zero_volume_pct","median_candle_range","median_true_range"])
    _write_csv(evidence/"ROLLOVER_SUMMARY.csv",rollovers,["instrument","timeframe","portable_id","series_type","contract_ids_present","possible_contract_transitions","explicit_roll_flags","suspicious_jumps","suspected_transition_timestamps","note"])
    readiness=["# Data readiness","","Raw readiness does not authorize normalization, H4 validation, or strategy execution.","","| Instrument | H1_SOURCE_AVAILABLE | RAW_PARSE | SYMBOL_IDENTITY | TIMEFRAME | NORMALIZATION | Synthetic H4 | Status | Reasons |","|---|---|---|---|---|---|---|---|---|"]
    for symbol in requested:
        hs=[m for m in manifests if m["instrument"]==symbol and m["timeframe"]=="H1"]
        good=[m for m in hs if m["raw_parse_status"]=="PASS"]
        failed=[r for r in inventory if r.get("detected_symbol")==symbol and r.get("raw_parse_status","").startswith("FAIL")]
        ready=bool(good) and not failed
        norm="PENDING_METADATA" if good and all(m["normalization_status"]=="PENDING_METADATA" for m in good) else ("PASS" if good and all(m["normalization_status"]=="PASS" for m in good) else "N/A")
        h4="PENDING_METADATA" if norm=="PENDING_METADATA" else "NOT_VALIDATED"
        reason="raw H1 requirements satisfied; rollover uncertainty recorded; metadata freeze required" if ready else "H1 absent or raw audit failed"
        readiness.append(f"| {symbol} | {'YES' if hs else 'NO'} | {'PASS' if good else 'FAIL'} | {symbol if good else 'N/A'} | {'H1' if good else 'N/A'} | {norm} | {h4} | {'READY_FOR_METADATA_FREEZE' if ready else 'NOT_READY'} | {reason} |")
    (evidence/"DATA_READINESS.md").write_text("\n".join(readiness)+"\n",encoding="utf-8")
    return 0
