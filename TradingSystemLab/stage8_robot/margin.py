"""Fail-closed FINAM FORTS margin parsing and execution-feasibility sizing.

FINAM names ``portfolio_forts.available_cash`` as the available (free) cash.
It is therefore the capacity authority and ``money_reserved`` is recorded as
evidence, not subtracted a second time.  Unknown response shapes are rejected.
"""
from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation, ROUND_FLOOR

NANO=Decimal(1_000_000_000)
AVAILABLE_CASH_SEMANTICS="FINAM_FORTS_AVAILABLE_CASH_ALREADY_AVAILABLE_DO_NOT_SUBTRACT_RESERVED"

def parse_money(value:dict, *, currency:str="RUB", positive:bool=False)->Decimal:
    if not isinstance(value,dict) or set(value)!={"currency_code","units","nanos"}:
        raise ValueError("MALFORMED_MONEY")
    if value["currency_code"] != currency: raise ValueError("MARGIN_CURRENCY_MISMATCH")
    if isinstance(value["units"],bool) or not isinstance(value["units"],str): raise ValueError("MALFORMED_MONEY_UNITS")
    if isinstance(value["nanos"],bool) or not isinstance(value["nanos"],int): raise ValueError("MALFORMED_MONEY_NANOS")
    try: units=Decimal(value["units"])
    except InvalidOperation: raise ValueError("MALFORMED_MONEY_UNITS") from None
    if units != units.to_integral_value() or abs(value["nanos"])>=1_000_000_000:
        raise ValueError("MALFORMED_MONEY")
    if (units>0 and value["nanos"]<0) or (units<0 and value["nanos"]>0):
        raise ValueError("MALFORMED_MONEY_SIGN")
    result=units+Decimal(value["nanos"])/NANO
    if positive and result<=0: raise ValueError("NON_POSITIVE_MARGIN")
    return result

def _money_value(container:dict,name:str,*,positive:bool=False)->Decimal:
    field=container.get(name)
    if not isinstance(field,dict) or set(field)!={"value"}: raise ValueError("MISSING_MONEY_VALUE")
    return parse_money(field["value"],positive=positive)

def forts_funds(account:dict)->tuple[Decimal,Decimal]:
    forts=account.get("portfolio_forts")
    if not isinstance(forts,dict): raise ValueError("FORTS_PORTFOLIO_MISSING")
    free=_money_value(forts,"available_cash")
    reserved=_money_value(forts,"money_reserved")
    if free<0 or reserved<0: raise ValueError("NEGATIVE_FORTS_FUNDS")
    return free,reserved

def directional_initial_margin(params:dict,direction:str)->Decimal:
    key={"LONG":"long_initial_margin","SHORT":"short_initial_margin"}.get(direction)
    if key is None: raise ValueError("DIRECTION_INVALID")
    return parse_money(params.get(key),positive=True)

def floor_to_trade_lot(quantity:int,trade_lot_size:int)->int:
    if type(quantity) is not int or type(trade_lot_size) is not int or quantity<0 or trade_lot_size<=0:
        raise ValueError("QUANTITY_GRANULARITY_INVALID")
    return quantity//trade_lot_size*trade_lot_size

def margin_capacity(available_cash:Decimal,initial_margin:Decimal,trade_lot_size:int)->int:
    if available_cash<0 or initial_margin<=0: raise ValueError("MARGIN_INPUT_INVALID")
    raw=int((available_cash/initial_margin).to_integral_value(rounding=ROUND_FLOOR))
    return floor_to_trade_lot(raw,trade_lot_size)

@dataclass(frozen=True)
class MarginAwareSize:
    current_realized_equity:Decimal; risk_cash:Decimal; entry:Decimal; initial_stop:Decimal
    stop_distance:Decimal; price_step:Decimal; tick_value:Decimal; loss_per_contract:Decimal
    r15_quantity:int; available_cash:Decimal; direction:str; initial_margin:Decimal
    margin_quantity:int; trade_lot_size:int; final_quantity:int
    reason:str|None=None
    def evidence(self): return {k:str(v) if isinstance(v,Decimal) else v for k,v in asdict(self).items()}

def cap_r15_by_margin(*,realized_equity:Decimal,entry:Decimal,stop:Decimal,price_step:Decimal,
                      tick_value:Decimal,r15_quantity:int,available_cash:Decimal,direction:str,
                      initial_margin:Decimal,trade_lot_size:int)->MarginAwareSize:
    if r15_quantity<0: raise ValueError("R15_QUANTITY_INVALID")
    margin_qty=margin_capacity(available_cash,initial_margin,trade_lot_size)
    final=floor_to_trade_lot(min(r15_quantity,margin_qty),trade_lot_size)
    distance=abs(entry-stop); ticks=distance/price_step; loss=ticks*tick_value
    result=MarginAwareSize(realized_equity,realized_equity*Decimal("0.015"),entry,stop,distance,
                           price_step,tick_value,loss,r15_quantity,available_cash,direction,
                           initial_margin,margin_qty,trade_lot_size,final,
                           None if final>0 else "INSUFFICIENT_R15_OR_MARGIN_CAPACITY")
    if result.final_quantity>result.r15_quantity: raise AssertionError("MARGIN_CAP_INCREASED_R15")
    return result

class MarginBatchBudget:
    """Local reservation prevents a stale account snapshot funding every intent."""
    def __init__(self,available_cash:Decimal):
        if available_cash<0: raise ValueError("MARGIN_INPUT_INVALID")
        self.initial_available_cash=available_cash; self.remaining=available_cash
    def size_and_reserve(self,**kwargs)->MarginAwareSize:
        result=cap_r15_by_margin(available_cash=self.remaining,**kwargs)
        reservation=result.initial_margin*result.final_quantity
        if reservation>self.remaining: raise AssertionError("LOCAL_MARGIN_OVERALLOCATION")
        self.remaining-=reservation
        return result
