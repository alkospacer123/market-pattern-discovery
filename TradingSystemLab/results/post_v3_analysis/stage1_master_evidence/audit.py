#!/usr/bin/env python3
"""Independent fail-closed audit of Stage 1 output and determinism."""
import csv, hashlib, json, subprocess, sys
from pathlib import Path

HERE=Path(__file__).resolve().parent

def rows(name):
    with (HERE/name).open(newline="",encoding="utf-8") as f: return list(csv.DictReader(f))

def main():
    source=(HERE/"generate.py").read_text(encoding="utf-8")
    forbidden=("core.data_loader", "core.strategy", "optimization.", "pandas.read_")
    assert not any(x in source for x in forbidden), "market/strategy/optimizer dependency found"
    manifest=json.loads((HERE/"manifest.json").read_text())
    assert manifest["status"]=="POST_V3_STAGE_1_MASTER_EVIDENCE_COMPLETE"
    for item in manifest["source_files_used"]:
        p=HERE.parents[3]/item["path"]; assert p.is_file(); assert hashlib.sha256(p.read_bytes()).hexdigest()==item["sha256"]
    master=rows("master_study_comparison.csv")
    inventory=rows("source_inventory.csv")
    keys=[(r["generation"],r["lifecycle_stage"],r["strategy"],r["timeframe"]) for r in master]
    assert len(keys)==len(set(keys))
    inst=rows("instrument_statistics.csv"); direct=rows("direction_statistics.csv"); monthly=rows("chronological_monthly_statistics.csv")
    for m in master:
        key=(m["generation"],m["lifecycle_stage"],m["strategy"],m["timeframe"]); n=int(m["total_trades"]); net=float(m["net_R"])
        source_trade_rows=0
        for item in inventory:
            item_key=(item["generation"],item["lifecycle_stage"],item["strategy"],item["timeframe"])
            if item_key==key and item["artifact_type"]=="trades" and item["usable"]=="true":
                with (HERE.parents[3]/item["repository_path"]).open(newline="",encoding="utf-8") as fh:
                    source_trade_rows += sum(1 for _ in csv.DictReader(fh))
        assert source_trade_rows==n, f"source trade-count mismatch for {key}"
        ii=[r for r in inst if tuple(r[x] for x in ("generation","lifecycle_stage","strategy","timeframe"))==key]
        dd=[r for r in direct if tuple(r[x] for x in ("generation","lifecycle_stage","strategy","timeframe"))==key]
        mm=[r for r in monthly if tuple(r[x] for x in ("generation","lifecycle_stage","strategy","timeframe"))==key]
        assert sum(int(r["total_trades"]) for r in ii)==n and sum(int(r["trades"]) for r in dd)==n and sum(int(r["trades"]) for r in mm)==n
        assert abs(sum(float(r["net_R"]) for r in ii)-net)<1e-8
        assert abs(sum(float(r["net_R"]) for r in dd)-net)<1e-8
        assert abs(sum(float(r["net_R"]) for r in mm)-net)<1e-8
        periods=[r["YYYY-MM"] for r in mm]; assert periods==sorted(periods)
    before={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in HERE.iterdir() if p.is_file()}
    subprocess.run([sys.executable, str(HERE/"generate.py")], check=True)
    after={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in HERE.iterdir() if p.is_file()}
    assert before==after, "outputs are not byte-deterministic"
    print(f"PASS: {len(master)} studies; instrument/direction/monthly reconciliation; provenance; deterministic rerun")

if __name__=="__main__": main()
