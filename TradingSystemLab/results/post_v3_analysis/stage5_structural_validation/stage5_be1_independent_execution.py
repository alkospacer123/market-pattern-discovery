"""Independent raw-data BE1 executor; shares no producer execution code at runtime."""
from __future__ import annotations
import csv, hashlib, json, os, shutil, tempfile
from dataclasses import replace
from pathlib import Path
from typing import Any
import pandas as pd
from concurrent.futures import ProcessPoolExecutor
from TradingSystemLab.core.data_loader import DataLoader
from TradingSystemLab.core.portfolio import FixedRiskPortfolio
from TradingSystemLab.strategies.trend.T2_Trend_Pullback import T2Parameters, T2TrendPullback, PullbackSetup
from TradingSystemLab.strategies.trend.T3_MTF_Trend import T3Parameters, T3MTFTrend
from dataclasses import dataclass

@dataclass
class IndependentBE1State:
    direction: str
    entry_price: float
    initial_stop_price: float
    enabled: bool = True
    triggered: bool = False
    activated: bool = False
    trigger_bar_time: Any = None
    trigger_bar_high: float | None = None
    trigger_bar_low: float | None = None
    activation_time: Any = None
    stop_before_activation: float | None = None
    stop_after_activation: float | None = None
    canonical_stop_already_tighter: bool = False
    be_level_touched: bool = False
    protective_stop_touched_after_be: bool = False
    gap_through_be_level: bool = False
    current_protective_stop_at_exit: float | None = None
    exit_protection_source: str = "CANONICAL"
    def __post_init__(self):
        self.initial_risk_price=(self.entry_price-self.initial_stop_price if self.direction=="LONG" else self.initial_stop_price-self.entry_price)
        if self.initial_risk_price<=0: raise ValueError("BE1_INITIAL_RISK_NOT_POSITIVE")
        self.trigger_price=self.entry_price+self.initial_risk_price if self.direction=="LONG" else self.entry_price-self.initial_risk_price
    def activate_before_event(self,t,stop):
        if not self.enabled or not self.triggered or self.activated or t==self.trigger_bar_time:return stop
        self.activation_time=t;self.stop_before_activation=float(stop);self.canonical_stop_already_tighter=(stop>=self.entry_price if self.direction=="LONG" else stop<=self.entry_price)
        self.stop_after_activation=max(stop,self.entry_price) if self.direction=="LONG" else min(stop,self.entry_price);self.activated=True;return self.stop_after_activation
    def observe_completed_bar(self,t,high,low):
        reached=self.enabled and not self.triggered and (high>=self.trigger_price if self.direction=="LONG" else low<=self.trigger_price)
        if reached:self.triggered=True;self.trigger_bar_time=t;self.trigger_bar_high=float(high);self.trigger_bar_low=float(low)
        return reached
    def stop_fill(self,open_,stop,bar_low=None,bar_high=None):
        fill=min(float(open_),stop) if self.direction=="LONG" else max(float(open_),stop);self.current_protective_stop_at_exit=float(stop)
        if self.activated:
            self.protective_stop_touched_after_be=True;at_be=abs(stop-self.entry_price)<=1e-12
            self.be_level_touched=(bar_low<=self.entry_price if self.direction=="LONG" and bar_low is not None else bar_high>=self.entry_price if self.direction=="SHORT" and bar_high is not None else at_be)
            self.gap_through_be_level=fill<self.entry_price if self.direction=="LONG" else fill>self.entry_price
            self.exit_protection_source="BE_LEVEL" if at_be else ("CANONICAL_TRAIL_AFTER_BE" if (stop>self.entry_price if self.direction=="LONG" else stop<self.entry_price) else "OTHER_CANONICAL_PROTECTIVE_EXIT")
        return fill
    def event_fields(self):
        return {"initial_stop_price":self.initial_stop_price,"initial_risk_price":self.initial_risk_price,"trigger_price":self.trigger_price,"be_triggered":self.triggered,"trigger_bar_time":self.trigger_bar_time,"trigger_bar_high":self.trigger_bar_high,"trigger_bar_low":self.trigger_bar_low,"be_activation_time":self.activation_time,"protective_stop_before_activation":self.stop_before_activation,"protective_stop_after_activation":self.stop_after_activation,"canonical_stop_already_tighter":self.canonical_stop_already_tighter,"be_level":self.entry_price,"be_level_touched":self.be_level_touched,"protective_stop_touched_after_be":self.protective_stop_touched_after_be,"current_protective_stop_at_exit":self.current_protective_stop_at_exit,"exit_protection_source":self.exit_protection_source,"gap_through_be_level":self.gap_through_be_level}

def independent_canonical_trail(direction,stop,candidate):return max(stop,candidate) if direction=="LONG" else min(stop,candidate)

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
TICK=.001
EVENT_COLUMNS=['generation','lifecycle','fold_id','strategy','timeframe','instrument','candidate_config_identity','be1_strategy_identity','trade_id','direction','entry_time','entry_price','initial_stop_price','initial_risk_price','trigger_price','be_triggered','trigger_bar_time','trigger_bar_high','trigger_bar_low','be_activation_time','protective_stop_before_activation','protective_stop_after_activation','canonical_stop_already_tighter','be_level','be_level_touched','protective_stop_touched_after_be','current_protective_stop_at_exit','exit_protection_source','gap_through_be_level','exit_time','exit_price','exit_reason','gross_R','cost_R','net_R_C1','bars_held']

def _sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def _csv(path:Path, rows:Any, columns=None):
    f=rows if isinstance(rows,pd.DataFrame) else pd.DataFrame(rows)
    if columns is not None:f=f.reindex(columns=columns)
    f.to_csv(path,index=False,lineterminator='\n',float_format='%.12g',na_rep='')
def _json(path:Path,x:Any):path.write_text(json.dumps(x,indent=2,sort_keys=True,allow_nan=False)+'\n')
def _params(gen,s,life):
    if life=='baseline': return T2Parameters() if s=='T2' else T3Parameters()
    p=ROOT/'TradingSystemLab/results'/('phase3_candidate_freeze/candidate_registry.json' if gen=='v2_quarterly' else 'perpetual_v3/phase3_candidate_freeze/candidate_registry.json')
    x=next(x for x in json.loads(p.read_text())['candidates'] if x['strategy']==s and x['timeframe']==_params.tf)
    return replace(T2Parameters() if s=='T2' else T3Parameters(),**x['parameters'])

def _record(meta,pos,state,t,price,reason):
    sign=1 if pos['direction']=='LONG' else -1; gross=sign*(price-pos['entry'])/pos['risk']; cost=2*TICK/pos['risk']
    if meta['strategy']=='T3':gross-=cost
    d={**meta,'trade_id':f"{meta['strategy']}-{meta['timeframe']}-{meta['instrument']}-{pos['seq']:06d}",'direction':pos['direction'],'entry_time':pos['entry_time'],'entry_price':pos['entry'],'exit_time':t,'exit_price':price,'exit_reason':reason,'gross_R':gross,'cost_R':cost,'net_R_C1':gross-cost,'bars_held':pos['bars']+1,**state.event_fields()}
    d['be1_strategy_identity']='H4_01_PROFIT_PROTECTION_BE1'; return d

def run_t2(frame,symbol,p,meta,be_enabled=True):
    st=T2TrendPullback(p); st._validate=lambda x:None; data=st.calculate_indicators(frame); setup=pos=None; out=[]; equity=100000.
    for i,(t,b) in enumerate(data.iterrows()):
      regime=st.regime(b)
      if pos is not None:
        bs=pos['be']; old=bs.activate_before_event(t,pos['stop']); pos['stop']=old
        hit=b.Low<=old if pos['direction']=='LONG' else b.High>=old
        if hit:
          price=bs.stop_fill(float(b.Open),old,bar_low=float(b.Low),bar_high=float(b.High)); out.append(_record(meta,pos,bs,t,price,'INITIAL_STOP' if old==pos['initial'] else 'ATR_TRAILING_STOP')); pos=None; continue
        loss=b.Close<b.EMA50 if pos['direction']=='LONG' else b.Close>b.EMA50
        if loss: out.append(_record(meta,pos,bs,t,float(b.Close),'EMA50_TREND_LOSS')); pos=None; continue
        pos['bars']+=1; pos['lo']=min(pos['lo'],float(b.Low));pos['hi']=max(pos['hi'],float(b.High))
        candidate=pos['hi']-p.trailing_atr*b.ATR if pos['direction']=='LONG' else pos['lo']+p.trailing_atr*b.ATR
        pos['stop']=independent_canonical_trail(pos['direction'],old,float(candidate));bs.observe_completed_bar(t,float(b.High),float(b.Low));continue
      if setup is not None:
        if i>setup.expiry_index or regime!=setup.direction:setup=None
        elif i>setup.pullback_start_index:
          setup.pullback_extreme=min(setup.pullback_extreme,float(b.Low)) if setup.direction=='LONG' else max(setup.pullback_extreme,float(b.High))
          if st.is_confirmation(b,data.iloc[i-1],setup.direction):
            entry=float(b.Close); stop=setup.pullback_extreme-p.stop_buffer_atr*b.ATR if setup.direction=='LONG' else setup.pullback_extreme+p.stop_buffer_atr*b.ATR; risk=entry-stop if setup.direction=='LONG' else stop-entry
            if risk>0 and risk<=p.max_initial_stop_atr*b.ATR:
              bs=IndependentBE1State(setup.direction,entry,float(stop),enabled=be_enabled); pos={'direction':setup.direction,'entry':entry,'entry_time':t,'initial':float(stop),'risk':float(risk),'stop':float(stop),'bars':0,'lo':entry,'hi':entry,'seq':len(out)+1,'be':bs}
            setup=None
        continue
      if regime and i:
        ref=st.impulse_reference(data,i,regime)
        if ref is not None and st.is_pullback(b,regime):setup=PullbackSetup(regime,t,i,i+p.confirmation_window,float(b.Low if regime=='LONG' else b.High),ref)
    return out

def run_t3(frame,symbol,p,meta,be_enabled=True):
    strategy=T3MTFTrend(p); high=DataLoader.h4_from_h1(frame); low,high=strategy.calculate_indicators(frame,high); cursor=-1;pos=None;out=[]
    for t,b in low.iterrows():
      while cursor+1<len(high) and high.index[cursor+1]<=t:cursor+=1
      regime=strategy.regime(high.iloc[cursor]) if cursor>=0 else None
      if pos is not None:
        bs=pos['be'];old=bs.activate_before_event(t,pos['stop']);pos['stop']=old
        if strategy.exit_signal(pos['direction'],b,old):
          price=bs.stop_fill(float(b.Open),old,bar_low=float(b.Low),bar_high=float(b.High));out.append(_record(meta,pos,bs,t,price,'ATR_TRAILING_STOP'));pos=None
        else:
          pos['bars']+=1;pos['lo']=min(pos['lo'],float(b.Low));pos['hi']=max(pos['hi'],float(b.High));pos['extreme']=max(pos['extreme'],b.High) if pos['direction']=='LONG' else min(pos['extreme'],b.Low)
          pos['stop']=independent_canonical_trail(pos['direction'],old,float(strategy.manage_position(pos['direction'],pos['extreme'],b.ATR)));bs.observe_completed_bar(t,float(b.High),float(b.Low))
      if pos is None and pd.notna(b.ATR):
        signal=strategy.generate_signal(b,regime)
        if signal:
          entry=float(b.Close);stop=float(strategy.calculate_stop_loss(signal,entry,float(b.ATR)));pos={'direction':signal,'entry':entry,'entry_time':t,'initial':stop,'risk':abs(entry-stop),'stop':stop,'extreme':entry,'bars':0,'lo':entry,'hi':entry,'seq':len(out)+1,'be':IndependentBE1State(signal,entry,stop,enabled=be_enabled)}
    return out

def _execute_row(item):
    r,root,be_enabled=item
    universe='futures_quarterly' if r['generation']=='v2_quarterly' else 'forever'
    path=Path(root)/universe/r['instrument']/f"{r['instrument']}_{r['timeframe']}.csv"
    raw=DataLoader(forbid_true_oos=False).load_csv(path)
    frame=DataLoader.close_index(raw,'30min' if r['timeframe']=='M30' else '1h').loc[r['start_timestamp']:r['end_timestamp']].copy()
    _params.tf=r['timeframe'];p=_params(r['generation'],r['strategy'],r['lifecycle'])
    meta={k:r[k] for k in ('generation','lifecycle','fold_id','strategy','timeframe','instrument','candidate_config_identity')}
    return (run_t2 if r['strategy']=='T2' else run_t3)(frame,r['instrument'],p,meta,be_enabled)

def _dispatch(registry,data_root,be_enabled):
    events=[]
    with ProcessPoolExecutor(max_workers=min(8,os.cpu_count() or 1)) as pool:
        for rows in pool.map(_execute_row,[(r,str(data_root),be_enabled) for r in registry],chunksize=1):events.extend(rows)
    return pd.DataFrame(events).reindex(columns=EVENT_COLUMNS)


def execute_independent(data_root:Path, registry_path:Path, output:Path)->pd.DataFrame:
    registry=list(csv.DictReader(Path(registry_path).open()))
    frame=_dispatch(registry,Path(data_root),True)
    frame=frame.sort_values(["generation","lifecycle","strategy","timeframe","fold_id","exit_time","instrument","trade_id"],kind="mergesort").reset_index(drop=True)
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    _csv(output/"independent_be1_trade_events.csv",frame,EVENT_COLUMNS)
    return frame
