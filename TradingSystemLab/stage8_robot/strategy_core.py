"""Deterministic T3/TRAIL1 decision core; no broker imports are permitted here."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
import hashlib, json, math
from typing import Literal
from zoneinfo import ZoneInfo
from .specification import PRODUCTION_SPECIFICATION_ID
from .trail1_state import Trail1State, tighten

Direction=Literal["LONG","SHORT"]
@dataclass(frozen=True)
class CompletedBar:
    timestamp: datetime; open: float; high: float; low: float; close: float; atr: float
    prior_high: float|None=None; prior_low: float|None=None; completed: bool=True
@dataclass(frozen=True)
class T3Context:
    close: float; ema100: float; ema100_slope: float; adx14: float; atr14: float; atr_mean20: float
    ema50: float|None=None; ema200: float|None=None
@dataclass(frozen=True)
class SignalIntent:
    signal_id: str; trade_id: str; instrument: str; direction: Direction; timestamp: datetime
    entry: float; initial_stop: float; initial_r: float; canonical_stop: float
@dataclass
class PositionState:
    instrument: str; direction: Direction; entry: float; initial_stop: float; current_stop: float
    favorable_extreme: float; trail1: Trail1State

def validate_bar(bar: CompletedBar, now: datetime, previous: datetime|None=None) -> None:
    if bar.timestamp.tzinfo is None or str(bar.timestamp.tzinfo) not in ("Europe/Moscow", "MSK"):
        raise ValueError("MARKET_DATA_TIMEZONE_INVALID")
    if not bar.completed or now.astimezone(ZoneInfo("Europe/Moscow")) < bar.timestamp: raise ValueError("INCOMPLETE_BAR")
    if previous is not None and bar.timestamp <= previous: raise ValueError("DUPLICATE_OR_NON_MONOTONIC_BAR")
    values=(bar.open,bar.high,bar.low,bar.close,bar.atr)
    if not all(math.isfinite(x) and x>0 for x in values) or bar.low>min(bar.open,bar.close) or bar.high<max(bar.open,bar.close):
        raise ValueError("INVALID_OHLC")

class DecisionCore:
    PARAMETERS={"ema_period":100,"slope_lookback":5,"adx_period":14,"adx_threshold":20.0,"atr_period":14,"atr_average_period":20,"breakout_period":20,"stop_atr":2.5,"trail_atr":3.0}
    def signal(self, instrument: str, bar: CompletedBar, context: T3Context, sequence: int) -> SignalIntent|None:
        # EMA50/EMA200 are authenticated context observables, not T3 gates.
        fields=(context.close,context.ema100,context.ema100_slope,context.adx14,context.atr14,context.atr_mean20,bar.atr)
        if any(v is None or not math.isfinite(v) for v in fields): return None
        if context.adx14<=20 or context.atr14<=context.atr_mean20: return None
        direction = "LONG" if context.close>context.ema100 and context.ema100_slope>0 else "SHORT" if context.close<context.ema100 and context.ema100_slope<0 else None
        if direction=="LONG" and (bar.prior_high is None or bar.close<=bar.prior_high): return None
        if direction=="SHORT" and (bar.prior_low is None or bar.close>=bar.prior_low): return None
        if direction is None: return None
        stop=bar.close-2.5*bar.atr if direction=="LONG" else bar.close+2.5*bar.atr
        payload={"production_specification_id":PRODUCTION_SPECIFICATION_ID,"strategy":"T3","configuration":"T3-H1-4e73cdb77246","variant":"TRAIL1","instrument":instrument,"signal_close_timestamp":bar.timestamp.isoformat(),"direction":direction,"signal_sequence":sequence}
        signal_id=hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()
        return SignalIntent(signal_id, hashlib.sha256((signal_id+":trade").encode()).hexdigest(), instrument, direction, bar.timestamp, bar.close, stop, abs(bar.close-stop), stop)
    def manage(self, position: PositionState, bar: CompletedBar) -> dict:
        # Stage 7: activation and stop test precede incorporation of this bar's extremes.
        position.current_stop=position.trail1.activate_before_event(bar.timestamp.isoformat(),position.current_stop)
        hit=bar.low<=position.current_stop if position.direction=="LONG" else bar.high>=position.current_stop
        if hit: return {"event":"EXIT","fill":position.trail1.stop_fill(bar.open,position.current_stop),"stop":position.current_stop}
        position.favorable_extreme=max(position.favorable_extreme,bar.high) if position.direction=="LONG" else min(position.favorable_extreme,bar.low)
        candidate=position.favorable_extreme-3*bar.atr if position.direction=="LONG" else position.favorable_extreme+3*bar.atr
        position.trail1.observe_completed_bar(bar.timestamp.isoformat(),bar.high,bar.low,candidate,position.current_stop)
        position.current_stop=position.trail1.candidate_after_bar(position.current_stop,candidate)
        return {"event":"HOLD","canonical_stop":candidate,"stop":position.current_stop,"triggered":position.trail1.triggered,"activated":position.trail1.activated}

def order_events(events: list[dict]) -> list[dict]:
    return sorted(events,key=lambda e:(e["timestamp"],0 if e["type"]=="EXIT" else 1,e["identity"]))
