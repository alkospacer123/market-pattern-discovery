"""Read-only operator smoke; writes only sanitized diagnostics."""
import json,os
from datetime import datetime,timezone,timedelta
from pathlib import Path
from .finam_api import FinamAPI
from .specification import INSTRUMENTS
def main():
 secret=os.environ["FINAM_API_SECRET"]; account=os.environ["FINAM_DEMO_ACCOUNT_ID"]
 if os.getenv("FINAM_ACCOUNT_ID",account)!=account: raise RuntimeError("DEMO_ACCOUNT_EXPLICIT_BINDING_REQUIRED")
 api=FinamAPI(secret); session=api.create_session(); ids={str(x.get("id",x.get("accountId",x))) for x in session.get("accounts",[])}
 if account not in ids: raise RuntimeError("CONFIGURED_DEMO_ACCOUNT_NOT_ENUMERATED")
 report={"timestamp":datetime.now(timezone.utc).isoformat(),"account_identity":"configured-demo-account","account_verified":bool(api.account(account)),"assets":{}}
 available=api.assets(True); rows=available.get("assets",available if isinstance(available,list) else [])
 for code in INSTRUMENTS:
  matches=[x for x in rows if x.get("ticker")==code or x.get("code")==code or x.get("shortCode")==code]
  if len(matches)!=1: report["assets"][code]={"status":"BLOCKED_NOT_FOUND"}; continue
  symbol=matches[0].get("symbol"); report["assets"][code]={"symbol":symbol,"asset":matches[0],"params":api.asset_params(symbol),"schedule":api.schedule(symbol),"h1":api.candles(symbol,{"timeFrame":"H1","from":(datetime.now(timezone.utc)-timedelta(days=2)).isoformat()})}
 Path(os.getenv("FINAM_DIAGNOSTIC_REPORT","finam-demo-diagnostic.json")).write_text(json.dumps(report,indent=2,sort_keys=True,default=str)+"\n")
if __name__=="__main__": main()
