"""Credential-backed, read-only FINAM discovery and binding diagnostic."""
import hashlib,json,os
from datetime import datetime,timezone,timedelta
from pathlib import Path
from .finam_api import FinamAPI,completed_h1_bars
from .instrument_resolver import N4,discover_finam_asset,evidence_sha256,validate_finam_binding

def main():
    if os.getenv("FINAM_MODE")!="DEMO": raise RuntimeError("FINAM_DEMO_MODE_REQUIRED")
    secret=os.environ["FINAM_API_SECRET"]; account=os.environ["FINAM_DEMO_ACCOUNT_ID"]
    if os.getenv("FINAM_ACCOUNT_ID",account)!=account: raise RuntimeError("DEMO_ACCOUNT_EXPLICIT_BINDING_REQUIRED")
    api=FinamAPI(secret); api.create_session(); details=api.session_details()
    if account not in {str(x) for x in details.get("account_ids",[])}: raise RuntimeError("CONFIGURED_DEMO_ACCOUNT_NOT_ENUMERATED")
    account_verified=bool(api.account(account)); available=api.assets()
    rows=available.get("assets",available if isinstance(available,list) else [])
    records={}
    for code in N4:
        asset,blocked=discover_finam_asset(code,rows)
        if blocked:
            records[code]={"research_symbol":code,"status":blocked,"validation_errors":[blocked]}; continue
        symbol=asset["symbol"]; account_asset=api.asset(symbol,account); params=api.asset_params(symbol,account); schedule=api.schedule(symbol)
        evidence=validate_finam_binding(code,asset,params,schedule,account_asset).to_dict()
        now=datetime.now(timezone.utc); raw=api.bars(symbol,(now-timedelta(days=2)).isoformat(),now.isoformat())
        evidence["recent_h1"]={"completed_count":len(completed_h1_bars(raw,now))}
        records[code]=evidence
    report={"schema_version":1,"timestamp":datetime.now(timezone.utc).isoformat(),
      "account_identity_sha256":hashlib.sha256(account.encode()).hexdigest(),"account_verified":account_verified,"bindings":records}
    report["evidence_sha256"]=evidence_sha256(records)
    Path(os.getenv("FINAM_DIAGNOSTIC_REPORT","finam-demo-diagnostic.json")).write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
if __name__=="__main__": main()
