"""Operator-run REAL_READONLY smoke.  This module contains no order call."""
import hashlib,json,os
from datetime import datetime,timedelta,timezone
from decimal import Decimal
from pathlib import Path
from .finam_api import FinamAPI,completed_h1_bars
from .readonly_supervisor import trading_h1_windows
from .instrument_resolver import MOEX_REFERENCE,N4,discover_finam_asset,evidence_sha256,validate_finam_binding
from .margin import cap_r15_by_margin,directional_initial_margin,forts_funds,parse_rest_decimal_value_object
from .risk import ContractEconomics,size_position

def run_diagnostic(api,account,report_path):
    api.create_session(); details=api.session_details()
    if account not in {str(x) for x in details.get("account_ids",[])}: raise RuntimeError("CONFIGURED_REAL_ACCOUNT_NOT_ENUMERATED")
    if details.get("readonly") is not True: raise RuntimeError("REAL_TOKEN_NOT_READONLY")
    account_data=api.account(account); orders_data=api.orders(account)
    positions=account_data.get("positions",[]); orders=orders_data.get("orders",orders_data if isinstance(orders_data,list) else [])
    if not isinstance(positions,list) or not isinstance(orders,list): raise RuntimeError("REAL_ACCOUNT_SCHEMA_INVALID")
    clean=not positions and not orders
    if not clean: raise RuntimeError("REAL_ACCOUNT_NOT_CLEAN_FOR_INITIALIZATION")
    # Binding deliberately precedes account-financial parsing.  An empty UNION
    # account can authenticate instruments without manufacturing FORTS funds.
    available=api.assets_all_active()
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
        binding.update({"initial_margin_long":str(long_margin),"initial_margin_short":str(short_margin),
                        })
        records[code]=binding
    if set(records)!=set(N4): raise RuntimeError("REAL_BINDING_REQUIRES_ALL_FOUR")
    funding_status="READY"; funding_error=None; financials={}
    try:
        free,reserved=forts_funds(account_data)
        realized=parse_rest_decimal_value_object(account_data.get("equity"),positive=True)
        financials={"forts_available_cash":str(free),"forts_money_reserved":str(reserved)}
        for code,binding in records.items():
            symbol=binding["finam_symbol"]
            schedule=api.schedule(symbol)
            raw=api.bars(symbol,(now-timedelta(days=2)).isoformat(),now.isoformat()); bars=completed_h1_bars(raw,now,trading_h1_windows(schedule))
            if not bars: raise RuntimeError(f"NO_COMPLETED_H1:{code}")
            step,tick,_=MOEX_REFERENCE[code]; entry=Decimal(str(bars[-1]["close"])); stop=entry-step*10
            lot=int(Decimal(binding["trade_lot_size"])); r15=size_position(realized,entry,stop,ContractEconomics(step,tick,lot,True))
            hypothetical=cap_r15_by_margin(realized_equity=realized,entry=entry,stop=stop,price_step=step,tick_value=tick,
                r15_quantity=r15.quantity,available_cash=free,direction="LONG",
                initial_margin=Decimal(binding["initial_margin_long"]),trade_lot_size=lot)
            binding.update({"completed_h1_count":len(bars),"hypothetical_sizing":hypothetical.evidence()})
    except ValueError as exc:
        funding_status="BLOCKED_ACCOUNT_FINANCIALS_UNAVAILABLE"; funding_error=str(exc)
    from .specification import PRODUCTION_SPECIFICATION_ID
    report={"schema_version":1,"timestamp":now.isoformat(),"binding_status":"AUTHENTICATED_REAL_READONLY",
      "production_specification_id":PRODUCTION_SPECIFICATION_ID,
      "account_identity_sha256":hashlib.sha256(account.encode()).hexdigest(),"account_type":account_data.get("type"),
      "account_status":account_data.get("status"),"token_readonly":True,"account_clean":clean,
      "funding_status":funding_status,"position_count":len(positions),
      "active_order_count":len(orders),"bindings":records}
    report.update(financials)
    report["evidence_sha256"]=evidence_sha256(records)
    Path(report_path).write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    if funding_error is not None: raise RuntimeError(f"{funding_status}:{funding_error}")

def main():
    if os.getenv("FINAM_MODE") not in ("REAL_READONLY","FINAM_REAL_READONLY"): raise RuntimeError("FINAM_REAL_READONLY_MODE_REQUIRED")
    account=os.environ["FINAM_REAL_ACCOUNT_ID"]; api=FinamAPI(os.environ["FINAM_API_SECRET"])
    run_diagnostic(api,account,os.getenv("FINAM_DIAGNOSTIC_REPORT","finam-real-readonly-diagnostic.json"))
if __name__=="__main__": main()
