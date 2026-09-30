"""Deterministic, fail-closed perpetual-to-contract resolution."""
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
import csv
from pathlib import Path

@dataclass(frozen=True)
class Contract:
    research_symbol:str; security_id:str; contract_code:str; expiry:date; price_step:Decimal
    tick_value:Decimal; multiplier:Decimal; quantity_granularity:int; currency:str; trading_status:str
class ContractResolver:
    def __init__(self, contracts:list[Contract]): self.contracts=contracts
    def resolve(self,symbol:str,on_date:date)->Contract:
        valid=sorted((c for c in self.contracts if c.research_symbol==symbol and c.expiry>on_date and c.trading_status=="ACTIVE"),key=lambda c:(c.expiry,c.security_id))
        if not valid: raise RuntimeError(f"CONTRACT_BINDING_UNAVAILABLE:{symbol}")
        return valid[0]
    @staticmethod
    def open_position_roll(_:Contract,next_contract:Contract|None=None): raise RuntimeError("OPERATOR_ACTION_REQUIRED_NO_FROZEN_ROLL_POLICY")

def load_registry(path:Path)->list[Contract]:
    rows=[]
    with path.open(newline="",encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["binding_status"]!="AUTHENTICATED_ACTIVE": continue
            rows.append(Contract(r["research_symbol"],r["security_id"],r["contract_code"],date.fromisoformat(r["expiry"]),Decimal(r["price_step"]),Decimal(r["tick_value"]),Decimal(r["contract_multiplier"]),int(r["quantity_granularity"]),r["currency"],r["trading_status"]))
    return rows
