"""Operator-run REAL_READONLY smoke.  This module contains no order call."""
import hashlib,json,os
from datetime import datetime,timedelta,timezone
from decimal import Decimal
from pathlib import Path
from .finam_api import FinamAPI,completed_h1_bars
from .instrument_resolver import MOEX_REFERENCE,N4,discover_finam_asset,evidence_sha256,validate_finam_binding
from .margin import cap_r15_by_margin,directional_initial_margin,forts_funds,parse_rest_decimal_value_object
from .risk import ContractEconomics,size_position

def main():
    if os.getenv("FINAM_MODE") not in ("REAL_READONLY","FINAM_REAL_READONLY"): raise RuntimeError("FINAM_REAL_READONLY_MODE_REQUIRED")
    account=os.environ["FINAM_REAL_ACCOUNT_ID"]; api=FinamAPI(os.environ["FINAM_API_SECRET"])
    api.create_session(); details=api.session_details()
    if account not in {str(x) for x in details.get("account_ids",[])}: raise RuntimeError("CONFIGURED_REAL_ACCOUNT_NOT_ENUMERATED")
    if details.get("readonly") is not True: raise RuntimeError("REAL_TOKEN_NOT_READONLY")
    account_data=api.account(account); orders_data=api.orders(account)
    positions=account_data.get("positions",[]); orders=orders_data.get("orders",orders_data if isinstance(orders_data,list) else [])
    if not isinstance(positions,list) or not isinstance(orders,list): raise RuntimeError("REAL_ACCOUNT_SCHEMA_INVALID")
    free,reserved=forts_funds(account_data)
    try: realized=parse_rest_decimal_value_object(account_data.get("equity"),positive=True)
    except ValueError: raise RuntimeError("REAL_ACCOUNT_EQUITY_INVALID") from None
    assets=api.assets(); available=assets.get("assets",assets if isinstance(assets,list) else [])
    records={}; now=datetime.now(timezone.utc)
    for code in N4:
        asset,blocked=discover_finam_asset(code,available)
        if blocked: raise RuntimeError(f"REAL_BINDING_FAILED:{code}:{blocked}")
        symbol=asset["symbol"]; account_asset=api.asset(symbol,account); params=api.asset_params(symbol,account); schedule=api.schedule(symbol)
        binding=validate_finam_binding(code,asset,params,schedule,account_asset).to_dict()
        if not binding["status"].startswith("AUTHENTICATED_"): raise RuntimeError(f"REAL_BINDING_FAILED:{code}:{binding['status']}")
        binding["status"]="AUTHENTICATED_REAL_READONLY"
        binding["trading_status"]="TRADABLE"
        long_margin=directional_initial_margin(params,"LONG"); short_margin=directional_initial_margin(params,"SHORT")
        raw=api.bars(symbol,(now-timedelta(days=2)).isoformat(),now.isoformat()); bars=completed_h1_bars(raw,now)
        if not bars: raise RuntimeError(f"NO_COMPLETED_H1:{code}")
        step,tick,_=MOEX_REFERENCE[code]; entry=Decimal(str(bars[-1]["close"])); stop=entry-step*10
        lot=int(Decimal(binding["trade_lot_size"])); r15=size_position(realized,entry,stop,ContractEconomics(step,tick,lot,True))
        hypothetical=cap_r15_by_margin(realized_equity=realized,entry=entry,stop=stop,price_step=step,tick_value=tick,
            r15_quantity=r15.quantity,available_cash=free,direction="LONG",initial_margin=long_margin,trade_lot_size=lot)
        binding.update({"initial_margin_long":str(long_margin),"initial_margin_short":str(short_margin),
                        "completed_h1_count":len(bars),"hypothetical_sizing":hypothetical.evidence()})
        records[code]=binding
    if set(records)!=set(N4): raise RuntimeError("REAL_BINDING_REQUIRES_ALL_FOUR")
    clean=not positions and not orders
    from .specification import PRODUCTION_SPECIFICATION_ID
    report={"schema_version":1,"timestamp":now.isoformat(),"binding_status":"AUTHENTICATED_REAL_READONLY",
      "production_specification_id":PRODUCTION_SPECIFICATION_ID,
      "account_identity_sha256":hashlib.sha256(account.encode()).hexdigest(),"account_type":account_data.get("type"),
      "account_status":account_data.get("status"),"token_readonly":True,"account_clean":clean,
      "forts_available_cash":str(free),"forts_money_reserved":str(reserved),"position_count":len(positions),
      "active_order_count":len(orders),"bindings":records}
    report["evidence_sha256"]=evidence_sha256(records)
    Path(os.getenv("FINAM_DIAGNOSTIC_REPORT","finam-real-readonly-diagnostic.json")).write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    if not clean: raise RuntimeError("REAL_ACCOUNT_NOT_CLEAN_FOR_INITIALIZATION")
if __name__=="__main__": main()
