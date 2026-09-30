"""Strict FINAM REST v1 binding for the frozen N4 perpetual futures.

REST transport shapes are intentionally parsed separately: scalar decimal
strings, ``{"value": "..."}`` quantity objects, and primitive booleans.  The
protobuf/gRPC ``{num, scale}`` representation is not REST binding evidence.
"""
from __future__ import annotations
from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation
import csv, hashlib, json
from pathlib import Path
from typing import Any

PERPETUAL_FUTURE = "PERPETUAL_FUTURE"
OPERATOR_ACTION_ONLY = "OPERATOR_ACTION_ONLY"
AUTHENTICATED = "AUTHENTICATED_DEMO_TRADABLE"
N4 = ("USDRUBF", "CNYRUBF", "GLDRUBF", "IMOEXF")

@dataclass(frozen=True)
class Instrument:
    research_symbol: str; finam_symbol: str | None; moex_short_code: str; mic: str
    security_id: str | None; instrument_type: str; perpetual: bool
    automatic_prolongation: bool; price_step: Decimal; tick_value: Decimal
    contract_size: Decimal; quantity_granularity: Decimal; currency: str
    trading_status: str; trading_schedule: dict[str, Any] | None
    quarterly_exercise: str = OPERATOR_ACTION_ONLY; expiry: None = None
    binding_status: str = "BLOCKED_UNAUTHENTICATED"
    def __post_init__(self):
        if self.instrument_type != PERPETUAL_FUTURE or not self.perpetual or self.expiry is not None:
            raise ValueError("PRODUCTION_INSTRUMENT_MUST_BE_NONEXPIRING_PERPETUAL")

class ContractResolver:
    def __init__(self, instruments): self.instruments=instruments
    def resolve(self,symbol,on_date=None):
        found=[x for x in self.instruments if x.research_symbol==symbol and x.binding_status==AUTHENTICATED]
        if len(found)!=1: raise RuntimeError(f"PERPETUAL_BINDING_UNAVAILABLE:{symbol}")
        return found[0]
    @staticmethod
    def open_position_roll(*_): raise RuntimeError("OPERATOR_ACTION_ONLY_NO_AUTOMATIC_ROLL")

MOEX_REFERENCE = {
 "USDRUBF": (Decimal("0.01"),Decimal("10"),Decimal("1000")),
 "CNYRUBF": (Decimal("0.001"),Decimal("1"),Decimal("1000")),
 "GLDRUBF": (Decimal("0.1"),Decimal("0.1"),Decimal("1")),
 "IMOEXF": (Decimal("0.5"),Decimal("5"),Decimal("10")),
}

def _checked_decimal(value: str, *, positive: bool) -> Decimal:
    try:
        result=Decimal(value)
    except (InvalidOperation, ValueError) as exc: raise ValueError("REST_DECIMAL_INVALID") from exc
    if not result.is_finite() or (positive and result <= 0): raise ValueError("REST_DECIMAL_RANGE_INVALID")
    return result

def parse_rest_decimal_scalar(value: Any, *, positive: bool = False) -> Decimal:
    """Parse an exact REST decimal string; numbers and protobuf objects fail."""
    if not isinstance(value,str) or not value: raise ValueError("REST_DECIMAL_SCALAR_INVALID")
    return _checked_decimal(value,positive=positive)

def parse_rest_value_object(value: Any, *, positive: bool = False) -> Decimal:
    """Parse the REST quantity shape ``{"value": "decimal"}`` exactly."""
    if not isinstance(value,dict) or set(value)!={"value"}: raise ValueError("REST_VALUE_OBJECT_INVALID")
    return parse_rest_decimal_scalar(value["value"],positive=positive)

def parse_rest_bool(value: Any) -> bool:
    """Parse an unwrapped REST JSON boolean exactly."""
    if type(value) is not bool: raise ValueError("REST_BOOL_INVALID")
    return value

def schedule_summary(schedule: Any) -> dict[str, Any] | None:
    if not isinstance(schedule,dict) or not schedule: return None
    sessions=schedule.get("sessions")
    if not isinstance(sessions,list) or not sessions: return None
    normalized=json.dumps(schedule,sort_keys=True,separators=(",",":"),ensure_ascii=True)
    return {"session_count":len(sessions),"sha256":hashlib.sha256(normalized.encode()).hexdigest()}

@dataclass(frozen=True)
class FinamBindingEvidence:
    research_symbol: str; finam_symbol: str | None; ticker: str | None; mic: str | None
    security_id: str | None; asset_type: str | None; quote_currency: str | None
    decimals: int | None; min_step: str | None; derived_price_step: str | None
    lot_size: str | None; futures_contract_size: str | None
    is_tradable: bool | None; trade_lot_size: str | None
    quantity_semantics: str; schedule: dict[str,Any] | None
    moex_price_step: str; moex_tick_value: str; moex_contract_size: str
    tick_value_source: str; status: str; validation_errors: tuple[str,...]
    rest_schema: dict[str,str]
    def to_dict(self):
        value=asdict(self); value["validation_errors"]=list(self.validation_errors); return value

def discover_finam_asset(research_symbol: str, assets: list[dict]) -> tuple[dict|None,str|None]:
    matches=[x for x in assets if x.get("ticker")==research_symbol and x.get("is_archived") is False]
    if not matches: return None,"BLOCKED_NOT_FOUND"
    # Futures identity and exact ticker@MIC can resolve irrelevant same-ticker rows.
    viable=[x for x in matches if x.get("type")=="ASSET_TYPE_FUTURE" and x.get("symbol")==f"{research_symbol}@{x.get('mic')}" and x.get("id")]
    if len(viable)!=1: return None,"BLOCKED_AMBIGUOUS_FINAM_ASSET" if len(matches)>1 else "BLOCKED_INSTRUMENT_TYPE_MISMATCH"
    return viable[0],None

def validate_finam_binding(symbol: str, asset: dict, params: dict, schedule: dict|None,
                           account_asset: dict|None=None) -> FinamBindingEvidence:
    """Cross-check exact FINAM fields against frozen MOEX reference; fail closed."""
    step,tick,size=MOEX_REFERENCE[symbol]; errors=[]; status=AUTHENTICATED
    authority=account_asset if isinstance(account_asset,dict) and account_asset else asset
    ticker=asset.get("ticker"); finam_symbol=asset.get("symbol"); mic=asset.get("mic"); security_id=asset.get("id")
    asset_type=asset.get("type"); currency=authority.get("quote_currency"); decimals=authority.get("decimals")
    def block(code,msg):
        nonlocal status
        if status==AUTHENTICATED: status=code
        errors.append(msg)
    if ticker!=symbol or not finam_symbol or finam_symbol!=f"{ticker}@{mic}" or not mic or not security_id:
        block("BLOCKED_IDENTITY_MISMATCH","exact ticker, ticker@MIC symbol, MIC, and security ID are required")
    if asset_type!="ASSET_TYPE_FUTURE": block("BLOCKED_INSTRUMENT_TYPE_MISMATCH","type must be ASSET_TYPE_FUTURE")
    if asset.get("is_archived") is not False: block("BLOCKED_INSTRUMENT_DISABLED","asset must explicitly be non-archived")
    if currency!="RUB": block("BLOCKED_CURRENCY_MISMATCH","quote_currency must be RUB")
    min_step=lot_size=contract_size=derived=trade_lot=None
    try:
        if isinstance(decimals,bool) or not isinstance(decimals,int) or decimals<0: raise ValueError
        min_step=parse_rest_decimal_scalar(authority.get("min_step"),positive=True); derived=min_step/(Decimal(10)**decimals)
        if derived!=step: block("BLOCKED_PRICE_STEP_MISMATCH",f"derived price step {derived} != {step}")
    except ValueError: block("BLOCKED_PRICE_STEP_MISMATCH","decimals/min_step invalid")
    future=authority.get("future_details")
    try:
        lot_size=parse_rest_value_object(authority.get("lot_size"),positive=True)
        contract_size=parse_rest_value_object(future.get("contract_size") if isinstance(future,dict) else None,positive=True)
        if lot_size!=1 or contract_size!=size: block("BLOCKED_CONTRACT_ECONOMICS_MISMATCH","lot_size or futures contract_size mismatch")
        # Perpetual identities must not acquire an expiry/automatic-roll meaning.
        if isinstance(future,dict) and future.get("expiration_date") not in (None,""):
            block("BLOCKED_CONTRACT_ECONOMICS_MISMATCH","perpetual future unexpectedly has expiration_date")
    except ValueError: block("BLOCKED_CONTRACT_ECONOMICS_MISMATCH","lot_size/future_details.contract_size invalid")
    try: tradable=parse_rest_bool(params.get("is_tradable") if isinstance(params,dict) else None)
    except ValueError: tradable=None
    try: trade_lot=parse_rest_decimal_scalar(params.get("trade_lot_size"),positive=True)
    except (ValueError,AttributeError): block("BLOCKED_PARAMS_INVALID","trade_lot_size missing or non-positive")
    if tradable is not True: block("BLOCKED_NOT_TRADABLE","account params is_tradable is false or unset")
    if trade_lot is not None and trade_lot!=1: block("BLOCKED_PARAMS_INVALID","futures trade_lot_size must be one contract")
    summary=schedule_summary(schedule)
    if summary is None: block("BLOCKED_SCHEDULE_INVALID","non-empty schedule.sessions required")
    return FinamBindingEvidence(symbol,finam_symbol,ticker,mic,security_id,asset_type,currency,
      decimals if isinstance(decimals,int) and not isinstance(decimals,bool) else None,
      str(min_step) if min_step is not None else None,str(derived) if derived is not None else None,
      str(lot_size) if lot_size is not None else None,str(contract_size) if contract_size is not None else None,
      tradable,str(trade_lot) if trade_lot is not None else None,
      "quantity.value is a number of futures contracts; must be a multiple of trade_lot_size",
      summary,str(step),str(tick),str(size),"MOEX",status,tuple(errors),
      {"quote_currency":type(authority.get("quote_currency")).__name__,
       "min_step":type(authority.get("min_step")).__name__,"lot_size":type(authority.get("lot_size")).__name__,
       "future_details.contract_size":type(future.get("contract_size") if isinstance(future,dict) else None).__name__,
       "is_tradable":type(params.get("is_tradable") if isinstance(params,dict) else None).__name__,
       "trade_lot_size":type(params.get("trade_lot_size") if isinstance(params,dict) else None).__name__})

def evidence_sha256(records: dict[str,dict]) -> str:
    return hashlib.sha256(json.dumps(records,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode()).hexdigest()

def load_registry(path:Path)->list[Instrument]:
    with path.open(newline="",encoding="utf-8") as f:
        return [Instrument(r["research_symbol"],r["finam_symbol"] or None,r["moex_short_code"],r["mic"],r["security_id"] or None,r["instrument_type"],r["perpetual"].lower()=="true",r["automatic_prolongation"].lower()=="true",Decimal(r["price_step"]),Decimal(r["tick_value"]),Decimal(r["contract_size"]),Decimal(r["quantity_granularity"]),r["currency"],r["trading_status"],None,r["quarterly_exercise"],None,r["binding_status"]) for r in csv.DictReader(f)]
