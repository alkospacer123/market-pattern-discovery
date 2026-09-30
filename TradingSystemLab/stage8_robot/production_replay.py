"""Broker-neutral historical execution of the production T3/TRAIL1 core.

This module deliberately has no dependency on a research dispatcher/backtester
or an authoritative output artifact.  The same context, decision and TRAIL1
components used at the DEMO boundary progress solely from completed raw bars.
"""
from __future__ import annotations
import math
import pandas as pd
from .context_builder import T3ContextBuilder
from .strategy_core import CompletedBar, DecisionCore, PositionState, T3Context
from .trail1_state import Trail1State

CONFIGURATION="T3-H1-4e73cdb77246"

def replay_production(frame:pd.DataFrame,symbol:str,meta:dict)->list[dict]:
    low,high=T3ContextBuilder().build(frame,frame.index[-1])
    core=DecisionCore(); cursor=-1; position=None; out=[]; sequence=0
    for timestamp,row in low.iterrows():
        while cursor+1<len(high) and high.index[cursor+1]<=timestamp: cursor+=1
        h=high.iloc[cursor] if cursor>=0 else None
        if position is not None:
            b=CompletedBar(timestamp.to_pydatetime(),float(row.Open),float(row.High),float(row.Low),float(row.Close),float(row.ATR))
            result=core.manage(position["state"],b)
            if result["event"]=="EXIT":
                state=position["state"].trail1; price=float(result["fill"]); sign=1 if position["direction"]=="LONG" else -1
                risk=position["risk"]; gross=sign*(price-position["entry"])/risk; cost=.002/risk
                out.append({**meta,"candidate_config_identity":CONFIGURATION,"trade_id":f"T3-H1-{symbol}-{position['sequence']:06d}",
                    "direction":position["direction"],"entry_time":position["entry_time"],"entry_price":position["entry"],
                    "initial_stop_price":position["initial_stop"],"initial_risk_price":risk,"trigger_price":state.trigger_price,
                    "trail1_triggered":state.triggered,"trigger_bar_time":state.trigger_bar_time,"stored_trail_candidate":state.stored_candidate,
                    "trail1_activation_time":state.activation_time,"trail1_activated":state.activated,
                    "candidate_already_looser":state.candidate_already_looser,"gap_through_activated_trail":state.gap_through_activated_trail,
                    "exit_time":timestamp,"exit_price":price,"exit_reason":"INITIAL_STOP" if result["stop"]==position["initial_stop"] else "ATR_TRAILING_STOP",
                    "gross_R":gross,"cost_R":cost,"net_R_C1":gross-cost,"bars_held":position["bars"]+1})
                position=None
            else: position["bars"]+=1
        if position is None and h is not None and pd.notna(row.ATR):
            ctx=T3Context(float(h.Close),float(h.EMA100),float(h.EMA100Slope),float(h.ADX),float(h.ATR),float(h.ATRMean20),float(h.EMA50),float(h.EMA200))
            b=CompletedBar(timestamp.to_pydatetime(),float(row.Open),float(row.High),float(row.Low),float(row.Close),float(row.ATR),
                           None if pd.isna(row.PriorHigh) else float(row.PriorHigh),None if pd.isna(row.PriorLow) else float(row.PriorLow))
            sequence+=1; intent=core.signal(symbol,b,ctx,sequence)
            if intent is None: sequence-=1
            else:
                trail=Trail1State(intent.direction,intent.entry,intent.initial_stop)
                state=PositionState(symbol,intent.direction,intent.entry,intent.initial_stop,intent.initial_stop,intent.entry,trail)
                position={"state":state,"direction":intent.direction,"entry":intent.entry,"entry_time":timestamp,
                          "initial_stop":intent.initial_stop,"risk":intent.initial_r,"bars":0,"sequence":sequence}
    return out
