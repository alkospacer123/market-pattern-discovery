"""Explicit all-four, integrity-checked, atomic demo registry activation."""
import csv,json,os,sys,tempfile
from pathlib import Path
from .instrument_resolver import AUTHENTICATED,N4,evidence_sha256,load_registry
from .specification import PRODUCTION_SPECIFICATION_ID,load_frozen_specification

def update(report_path:Path,registry_path:Path)->None:
    report=json.loads(report_path.read_text()); bindings=report.get("bindings",{})
    if load_frozen_specification().production_id!=PRODUCTION_SPECIFICATION_ID: raise RuntimeError("PRODUCTION_ID_MISMATCH")
    conformance=json.loads((Path(__file__).parent/"conformance_report.json").read_text())
    if any(conformance.get(x,{}).get("exact_matches")!=418 or conformance[x].get("status")!="PASS" for x in ("authority_replay","production_robot_replay")):
        raise RuntimeError("CONFORMANCE_418_REQUIRED")
    if not report.get("account_verified") or tuple(sorted(bindings))!=tuple(sorted(N4)): raise RuntimeError("ALL_FOUR_AUTHENTICATION_REQUIRED")
    if report.get("evidence_sha256")!=evidence_sha256(bindings): raise RuntimeError("EVIDENCE_INTEGRITY_FAILURE")
    if any(bindings[x].get("status")!=AUTHENTICATED for x in N4): raise RuntimeError("ALL_FOUR_AUTHENTICATION_REQUIRED")
    with registry_path.open(newline="") as source: rows=list(csv.DictReader(source)); fields=source.seek(0) or next(csv.reader(source),None)
    fields=list(rows[0]); original={x["research_symbol"]:x for x in rows}
    if set(original)!=set(N4): raise RuntimeError("REGISTRY_UNIVERSE_MISMATCH")
    for code in N4:
        row=original[code]; x=bindings[code]
        if row["instrument_type"]!="PERPETUAL_FUTURE" or row["research_symbol"]!=code: raise RuntimeError("FROZEN_IDENTITY_MISMATCH")
        row.update(finam_symbol=x["finam_symbol"],mic=x["mic"],security_id=x["security_id"],price_step=x["derived_price_step"],
          contract_size=x["futures_contract_size"],quantity_granularity=x["trade_lot_size"],currency=x["quote_currency"],
          trading_status="DEMO_TRADABLE",binding_status=AUTHENTICATED,
          authority="FINAM credential-backed evidence sha256="+report["evidence_sha256"]+"; MOEX tick-value reference")
    temp=None
    try:
        with tempfile.NamedTemporaryFile("w",dir=registry_path.parent,delete=False,newline="",encoding="utf-8") as f:
            temp=Path(f.name); writer=csv.DictWriter(f,fieldnames=fields,lineterminator="\n"); writer.writeheader(); writer.writerows(rows); f.flush(); os.fsync(f.fileno())
        validated=load_registry(temp)
        if len(validated)!=4 or any(x.binding_status!=AUTHENTICATED for x in validated): raise RuntimeError("TEMP_REGISTRY_VALIDATION_FAILED")
        validated_by_code={x.research_symbol:x for x in validated}
        for code in N4:
            row=validated_by_code[code]; evidence=bindings[code]
            expected=(evidence["finam_symbol"],evidence["mic"],evidence["security_id"],
              evidence["derived_price_step"],evidence["futures_contract_size"],evidence["trade_lot_size"],
              evidence["quote_currency"],evidence["status"])
            actual=(row.finam_symbol,row.mic,row.security_id,str(row.price_step),str(row.contract_size),
              str(row.quantity_granularity),row.currency,row.binding_status)
            if actual!=expected: raise RuntimeError(f"TEMP_REGISTRY_EVIDENCE_MISMATCH:{code}")
        os.replace(temp,registry_path); temp=None
    finally:
        if temp is not None: temp.unlink(missing_ok=True)
if __name__=="__main__": update(Path(sys.argv[1]),Path(sys.argv[2]))
