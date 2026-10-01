"""Atomic registry promotion from externally validated REAL_READONLY evidence."""
import csv,json,os,tempfile
from decimal import Decimal,InvalidOperation
from pathlib import Path
from .instrument_resolver import N4,evidence_sha256
from .specification import PRODUCTION_SPECIFICATION_ID

AUTHENTICATED_REAL_READONLY="AUTHENTICATED_REAL_READONLY"
HERE=Path(__file__).resolve().parent
FROZEN_FIELDS=("research_symbol","moex_short_code","instrument_type","perpetual",
               "automatic_prolongation","tick_value","quarterly_exercise")
COPIED_FIELDS=("finam_symbol","mic","security_id","price_step","contract_size",
               "quantity_granularity","currency","binding_status")

def _decimal(value,name):
    if not isinstance(value,str) or not value: raise RuntimeError(f"REAL_BINDING_{name}_INVALID")
    try: result=Decimal(value)
    except InvalidOperation: raise RuntimeError(f"REAL_BINDING_{name}_INVALID") from None
    if not result.is_finite() or result<=0: raise RuntimeError(f"REAL_BINDING_{name}_INVALID")
    return result

def _binding_values(code,binding,evidence_hash):
    values={
      "finam_symbol":binding.get("finam_symbol"),"mic":binding.get("mic"),
      "security_id":binding.get("security_id"),"price_step":binding.get("derived_price_step"),
      "contract_size":binding.get("futures_contract_size"),
      "quantity_granularity":binding.get("trade_lot_size"),"currency":binding.get("quote_currency"),
      "trading_status":binding.get("trading_status"),"binding_status":binding.get("status")}
    if not all(isinstance(values[k],str) and values[k] for k in ("finam_symbol","mic","security_id")):
        raise RuntimeError(f"REAL_BINDING_IDENTITY_INVALID:{code}")
    if values["currency"]!="RUB" or values["trading_status"]!="TRADABLE" or values["binding_status"]!=AUTHENTICATED_REAL_READONLY:
        raise RuntimeError(f"REAL_BINDING_STATUS_INVALID:{code}")
    for key in ("price_step","contract_size","quantity_granularity"): _decimal(values[key],key.upper())
    values["authority"]=(f"FINAM REAL_READONLY evidence sha256:{evidence_hash}; "
      f"MOEX frozen tick-value reference; account-specific binding authenticated")
    return values

def _validate_gates(report,bindings):
    conformance=json.loads((HERE/"conformance_report.json").read_text())
    exact=all(conformance.get(layer,{}).get("status")=="PASS"
      and conformance[layer].get("exact_matches")==418
      and conformance[layer].get("expected_trade_count")==418
      and conformance[layer].get("reproduced_trade_count")==418
      for layer in ("authority_replay","production_robot_replay"))
    valid_hash=isinstance(report.get("evidence_sha256"),str) and len(report["evidence_sha256"])==64 \
      and report["evidence_sha256"]==evidence_sha256(bindings)
    if (report.get("production_specification_id")!=PRODUCTION_SPECIFICATION_ID or not exact
        or report.get("binding_status")!=AUTHENTICATED_REAL_READONLY
        or report.get("token_readonly") is not True or report.get("account_clean") is not True
        or set(bindings)!=set(N4) or not valid_hash
        or any(not isinstance(x,dict) or x.get("status")!=AUTHENTICATED_REAL_READONLY for x in bindings.values())):
        raise RuntimeError("REAL_READONLY_ACTIVATION_REQUIRES_VALIDATED_ALL_FOUR")

def update(evidence_path:Path,registry_path:Path):
    report=json.loads(evidence_path.read_text()); bindings=report.get("bindings",{})
    if not isinstance(bindings,dict): raise RuntimeError("REAL_READONLY_ACTIVATION_REQUIRES_VALIDATED_ALL_FOUR")
    _validate_gates(report,bindings)
    evidence_hash=report["evidence_sha256"]
    with registry_path.open(newline="",encoding="utf-8") as source:
        reader=csv.DictReader(source); fields=list(reader.fieldnames or ()); rows=list(reader)
    if [row.get("research_symbol") for row in rows]!=list(N4):
        raise RuntimeError("REAL_REGISTRY_REQUIRES_EXACT_N4")
    frozen={row["research_symbol"]:{key:row[key] for key in FROZEN_FIELDS} for row in rows}
    expected={code:_binding_values(code,bindings[code],evidence_hash) for code in N4}
    for row in rows:
        values=expected[row["research_symbol"]]
        if (Decimal(values["price_step"])!=Decimal(row["price_step"])
            or Decimal(values["contract_size"])!=Decimal(row["contract_size"])
            or Decimal(values["quantity_granularity"])!=Decimal(row["quantity_granularity"])):
            raise RuntimeError("REAL_BINDING_FROZEN_ECONOMICS_MISMATCH")
        row.update(values)
    fd,name=tempfile.mkstemp(dir=registry_path.parent,prefix="registry-",suffix=".tmp"); temp=Path(name)
    try:
        with os.fdopen(fd,"w",newline="",encoding="utf-8") as out:
            writer=csv.DictWriter(out,fieldnames=fields); writer.writeheader(); writer.writerows(rows)
            out.flush(); os.fsync(out.fileno())
        # Independently reload and compare the complete promoted binding before replacement.
        with temp.open(newline="",encoding="utf-8") as check_file:
            checked=list(csv.DictReader(check_file))
        if [row.get("research_symbol") for row in checked]!=list(N4): raise RuntimeError("TEMP_REGISTRY_VALIDATION_FAILED")
        for row in checked:
            code=row["research_symbol"]
            if any(row.get(k)!=v for k,v in frozen[code].items()): raise RuntimeError("TEMP_REGISTRY_FROZEN_FIELD_CHANGED")
            if any(row.get(k)!=expected[code][k] for k in COPIED_FIELDS): raise RuntimeError("TEMP_REGISTRY_VALIDATION_FAILED")
        os.replace(temp,registry_path)
        directory_fd=os.open(registry_path.parent,os.O_RDONLY)
        try: os.fsync(directory_fd)
        finally: os.close(directory_fd)
    finally: temp.unlink(missing_ok=True)
