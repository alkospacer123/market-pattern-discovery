"""Atomically activate the registry from a successful sanitized smoke report."""
import csv,json,sys,tempfile
from pathlib import Path
from .specification import INSTRUMENTS

def update(report_path:Path,registry_path:Path)->None:
    report=json.loads(report_path.read_text()); assets=report.get("assets",{})
    if not report.get("account_verified") or set(assets)!=set(INSTRUMENTS): raise RuntimeError("ALL_FOUR_AUTHENTICATION_REQUIRED")
    for code in INSTRUMENTS:
        x=assets[code]; p=x.get("params",{}); a=x.get("asset",{})
        if not x.get("symbol") or not a.get("is_tradable") or not p.get("trade_lot_size"): raise RuntimeError(f"INSTRUMENT_NOT_AUTHENTICATED:{code}")
    rows=list(csv.DictReader(registry_path.open())); fields=list(rows[0])
    for row in rows:
        row["finam_symbol"]=assets[row["research_symbol"]]["symbol"]
        row["binding_status"]="AUTHENTICATED_DEMO_TRADABLE"
    with tempfile.NamedTemporaryFile("w",dir=registry_path.parent,delete=False,newline="") as f:
        writer=csv.DictWriter(f,fieldnames=fields,lineterminator="\n");writer.writeheader();writer.writerows(rows); temp=Path(f.name)
    temp.replace(registry_path)
if __name__=="__main__": update(Path(sys.argv[1]),Path(sys.argv[2]))
