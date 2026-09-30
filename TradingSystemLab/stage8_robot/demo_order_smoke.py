"""Explicit demo infrastructure smoke. Never callable as LIVE."""
import json,os
from pathlib import Path
from .broker import FinamDemoBroker,OrderRequest
from .finam_api import FinamAPI
from .specification import load_frozen_specification

def main():
 gates={"mode":os.getenv("FINAM_MODE")=="DEMO","enabled":os.getenv("DEMO_ORDER_TRANSMISSION_ENABLED")=="true","reconciled":os.getenv("ROBOT_RECONCILIATION")=="RECONCILED"}
 report=json.loads((Path(__file__).parent/"conformance_report.json").read_text()); gates["conformance"]=report.get("production_conformance_pass") is True
 registry=(Path(__file__).parent/"production_instrument_registry.csv").read_text(); gates["registry"]=registry.count("AUTHENTICATED_DEMO_TRADABLE")==4
 load_frozen_specification()
 if not all(gates.values()): raise RuntimeError("DEMO_ORDER_GATE_BLOCKED:"+",".join(k for k,v in gates.items() if not v))
 account=os.environ["FINAM_DEMO_ACCOUNT_ID"]; broker=FinamDemoBroker(FinamAPI(os.environ["FINAM_API_SECRET"]),account,account,True); broker.connect()
 symbol=os.environ["FINAM_SMOKE_SYMBOL"]; quantity=int(os.environ["FINAM_SMOKE_QUANTITY"])
 if quantity<=0: raise ValueError("MINIMUM_VALID_QUANTITY_REQUIRED")
 print(broker.submit_order(OrderRequest("INFRASTRUCTURE_SMOKE_NOT_STRATEGY_SIGNAL",symbol,os.environ["FINAM_SMOKE_SIDE"],quantity)))
if __name__=="__main__": main()
