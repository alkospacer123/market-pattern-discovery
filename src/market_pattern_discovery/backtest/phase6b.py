"""Causal Phase 6B known-strategy benchmark.

Signals consume a closed candle, executions consume only the following candle,
and outcome code is deliberately separate from signal generation.  All rolling
state resets on ``trading_date`` except explicitly previous-day levels.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import math

import numpy as np
import pandas as pd

from market_pattern_discovery.data.finam import stitch_finam

START = pd.Timestamp("2026-01-05", tz="Europe/Moscow")
END = pd.Timestamp("2026-05-16", tz="Europe/Moscow")
SPECS = {"CNYRUBF": (0.001, 0.05, "CNY"), "USDRUBF": (0.01, 0.10, "Si")}
STRATEGIES = ("RL-01", "RL-02", "RL-03", "RL-04", "MOM-01", "MOM-02",
              "NR-01", "RH-01", "RH-02", "PD-01", "PD-02")
SKIPPED = {
    "EH-01": "No existing causal Equal High/Equal Low reference-price primitive is exposed by the frozen feature builder.",
    "EH-02": "No existing causal Equal High/Equal Low reference-price primitive is exposed by the frozen feature builder.",
}


def load_discovery(data_root: str | Path, instrument: str) -> tuple[pd.DataFrame, list[dict]]:
    """Read only named 2026 M1 sources, then apply the immutable discovery fence."""
    tick, _, folder = SPECS[instrument]
    paths = sorted((Path(data_root) / "2026" / folder).glob("*_2026_Q[12]_M1.csv"))
    result = stitch_finam(paths, instrument, "M1")
    f = result.frame.loc[(result.frame.open_time >= START) & (result.frame.close_time < END)].copy()
    if f.empty or f.open_time.dt.year.ne(2026).any() or f.close_time.max() >= END:
        raise ValueError("discovery boundary violation")
    f["trading_date"] = f.open_time.dt.tz_convert("Europe/Moscow").dt.date
    # Wilder ATR(14), seeded by the first 14 closed true ranges of each day.
    tr = pd.concat([f.high-f.low, (f.high-f.close.shift()).abs(), (f.low-f.close.shift()).abs()], axis=1).max(axis=1)
    f["atr14"] = np.nan
    for _, d in f.groupby("trading_date", sort=False):
        vals = tr.loc[d.index].to_numpy(float); out = np.full(len(vals), np.nan)
        if len(vals) >= 14:
            out[13] = vals[:14].mean()
            for i in range(14, len(vals)): out[i] = (out[i-1] * 13 + vals[i]) / 14
        f.loc[d.index, "atr14"] = out
    f["tick"] = tick
    return f.reset_index(drop=True), result.provenance


def _event(strategy: str, i: int, side: int, atr: float, ref: float | None = None, **audit) -> dict:
    return {"strategy_id": strategy, "bar_index": i, "side": "LONG" if side == 1 else "SHORT",
            "direction": side, "ATR_at_signal": atr, "reference_level": ref, **audit}


def generate_signals(frame: pd.DataFrame, instrument: str) -> pd.DataFrame:
    """Generate preregistered events using row ``i`` and its closed prefix only."""
    tick, step, _ = SPECS[instrument]; events: list[dict] = []
    # Fully completed previous trading day levels.
    daily = frame.groupby("trading_date").agg(day_high=("high", "max"), day_low=("low", "min"))
    prev = daily.shift(1); ph = frame.trading_date.map(prev.day_high); pl = frame.trading_date.map(prev.day_low)
    # Stateful definitions are day-local.
    for _, day in frame.groupby("trading_date", sort=False):
        idx = list(day.index); nr = None; retests: list[dict] = []
        for pos, i in enumerate(idx):
            r = frame.loc[i]; atr = r.atr14
            if not np.isfinite(atr) or pos == 0: continue
            p = frame.loc[idx[pos-1]]
            # Frozen round-level semantics select one nearest reference from the
            # decision close; exact half-step ties deterministically select up.
            levels = [math.floor(r.close / step + .5)]
            for k in levels:
                L = round(k*step, 10)
                if r.low <= L+tick and r.close > L and p.close >= L: events.append(_event("RL-01",i,1,atr,L))
                if r.high >= L-tick and r.close < L and p.close <= L: events.append(_event("RL-01",i,-1,atr,L))
                if p.close <= L and r.close > L+tick: events.append(_event("RL-02",i,1,atr,L))
                if p.close >= L and r.close < L-tick: events.append(_event("RL-02",i,-1,atr,L))
                # Current penetration; or previous penetration whose pre-break close was on the proper side.
                pp = frame.loc[idx[pos-2]] if pos >= 2 else None
                long_pen = (r.low <= L-tick and p.close >= L) or (p.low <= L-tick and pp is not None and pp.close >= L)
                short_pen = (r.high >= L+tick and p.close <= L) or (p.high >= L+tick and pp is not None and pp.close <= L)
                if long_pen and r.close > L: events.append(_event("RL-03",i,1,atr,L,return_window=2))
                if short_pen and r.close < L: events.append(_event("RL-03",i,-1,atr,L,return_window=2))
                if p.close <= L and r.close > L+tick: retests.append({"side":1,"level":L,"break_pos":pos})
                if p.close >= L and r.close < L-tick: retests.append({"side":-1,"level":L,"break_pos":pos})
            # A retest may start only after the breakout candle; expire after five closed bars.
            keep=[]
            for s in retests:
                age=pos-s["break_pos"]
                if 1 <= age <= 5 and r.low <= s["level"]+tick and r.high >= s["level"]-tick and ((s["side"]==1 and r.close>s["level"]) or (s["side"]==-1 and r.close<s["level"])):
                    events.append(_event("RL-04",i,s["side"],atr,s["level"],retest_age=age))
                elif age <= 5: keep.append(s)
            retests=keep
            if pos >= 5:
                m5=(r.close-frame.loc[idx[pos-5],"close"])/atr
                if abs(m5)>=.5: events.append(_event("MOM-01",i,1 if m5>0 else -1,atr,momentum=m5))
            if pos >= 10:
                m10=(r.close-frame.loc[idx[pos-10],"close"])/atr
                if abs(m10)>=.75: events.append(_event("MOM-02",i,1 if m10>0 else -1,atr,momentum=m10))
            # First breakout of the latest NR7; a newer NR7 replaces old state.
            if nr is not None:
                age=pos-nr["pos"]
                if 1 <= age <= 10 and r.close>nr["high"]: events.append(_event("NR-01",i,1,atr,nr["high"],nr_age=age)); nr=None
                elif 1 <= age <= 10 and r.close<nr["low"]: events.append(_event("NR-01",i,-1,atr,nr["low"],nr_age=age)); nr=None
                elif age>10: nr=None
            if pos >= 6:
                seven=frame.loc[idx[pos-6:pos],"high"].to_numpy()-frame.loc[idx[pos-6:pos],"low"].to_numpy()
                if (r.high-r.low) <= seven.min(): nr={"pos":pos,"high":r.high,"low":r.low}
            if pos >= 20:
                hist=frame.loc[idx[pos-20:pos-1]]; hi=hist.high.max(); lo=hist.low.min()
                if r.close>hi: events.append(_event("RH-01",i,1,atr,hi))
                if r.close<lo: events.append(_event("RH-01",i,-1,atr,lo))
                if r.low<lo and r.close>lo: events.append(_event("RH-02",i,1,atr,lo))
                if r.high>hi and r.close<hi: events.append(_event("RH-02",i,-1,atr,hi))
            if np.isfinite(ph.iloc[i]):
                if p.close<=ph.iloc[i] and r.close>ph.iloc[i]: events.append(_event("PD-01",i,1,atr,ph.iloc[i]))
                if p.close>=pl.iloc[i] and r.close<pl.iloc[i]: events.append(_event("PD-01",i,-1,atr,pl.iloc[i]))
                if r.low<pl.iloc[i] and r.close>pl.iloc[i]: events.append(_event("PD-02",i,1,atr,pl.iloc[i]))
                if r.high>ph.iloc[i] and r.close<ph.iloc[i]: events.append(_event("PD-02",i,-1,atr,ph.iloc[i]))
    if not events: return pd.DataFrame()
    e=pd.DataFrame(events).drop_duplicates(["strategy_id","bar_index","side","reference_level"], keep="first")
    e["signal_time"]=e.bar_index.map(frame.close_time); e["instrument"]=instrument
    return e.sort_values(["strategy_id","bar_index","side"],kind="mergesort").reset_index(drop=True)


def event_outcomes(frame: pd.DataFrame, events: pd.DataFrame) -> pd.DataFrame:
    rows=[]
    for e in events.itertuples():
        for h in (5,15,30,60):
            end=min(e.bar_index+h,len(frame)-1); future=frame.iloc[e.bar_index+1:end+1]
            if len(future)<h: continue
            side=e.direction; base=frame.close.iloc[e.bar_index]; atr=e.ATR_at_signal
            rows.append({"strategy_id":e.strategy_id,"instrument":e.instrument,"signal_time":e.signal_time,"horizon":h,
                         "signed_move_atr":side*(frame.close.iloc[end]-base)/atr,
                         "mfe_atr":((future.high.max()-base) if side==1 else (base-future.low.min()))/atr,
                         "mae_atr":((base-future.low.min()) if side==1 else (future.high.max()-base))/atr})
    return pd.DataFrame(rows)


def simulate(frame: pd.DataFrame, events: pd.DataFrame, tick: float) -> pd.DataFrame:
    """Simulate grid with next-open entry and per-cell position exclusivity."""
    configs=[(f"STOP_{s}_TARGET_{t}",s,t,60) for s in (.5,1.) for t in (1.,1.5,2.)]+[(f"TIME_{h}",None,None,h) for h in (15,30,60)]
    raw=[]
    for strategy, es in events.groupby("strategy_id",sort=False):
      for name,stop_r,target_r,maxhold in configs:
        available=-1
        for e in es.sort_values("bar_index").itertuples():
            entry_i=e.bar_index+1
            if entry_i>=len(frame) or entry_i<=available or frame.trading_date.iloc[entry_i]!=frame.trading_date.iloc[e.bar_index]: continue
            entry=float(frame.open.iloc[entry_i]); risk=(stop_r or 1.)*e.ATR_at_signal; side=e.direction
            stop=entry-side*risk if stop_r else np.nan; target=entry+side*risk*target_r if target_r else np.nan
            exit_i=min(entry_i+maxhold-1,len(frame)-1); reason="TIME"; price=float(frame.close.iloc[exit_i])
            mfe=mae=0.
            for j in range(entry_i,exit_i+1):
                b=frame.iloc[j]; mfe=max(mfe,(b.high-entry) if side==1 else (entry-b.low)); mae=max(mae,(entry-b.low) if side==1 else (b.high-entry))
                hit_s=stop_r is not None and (b.low<=stop if side==1 else b.high>=stop)
                hit_t=target_r is not None and (b.high>=target if side==1 else b.low<=target)
                if hit_s: exit_i=j; price=stop; reason="STOP_FIRST_TIE" if hit_t else "STOP"; break
                if hit_t: exit_i=j; price=target; reason="TARGET"; break
            available=exit_i
            for friction,ticks in (("GROSS",0),("BASE",1),("STRESS",2)):
                ae=entry+side*ticks*tick; ax=price-side*ticks*tick; gross=side*(price-entry); net=side*(ax-ae)
                raw.append({"strategy_id":strategy,"instrument":e.instrument,"exit_configuration":name,"friction_scenario":friction,
                    "signal_time":e.signal_time,"entry_time":frame.open_time.iloc[entry_i],"entry_price_raw":entry,"entry_price_adjusted":ae,
                    "side":e.side,"ATR_at_entry":e.ATR_at_signal,"reference_level":e.reference_level,"stop_price":stop,"target_price":target,
                    "exit_time":frame.close_time.iloc[exit_i],"exit_price_raw":price,"exit_price_adjusted":ax,"exit_reason":reason,
                    "bars_held":exit_i-entry_i+1,"gross_pnl_price":gross,"net_pnl_price":net,"pnl_R":net/risk,"MFE":mfe,"MAE":mae})
    return pd.DataFrame(raw)


def metrics(ledger: pd.DataFrame) -> pd.DataFrame:
    rows=[]
    keys=["strategy_id","instrument","exit_configuration","friction_scenario"]
    for key,g in ledger.groupby(keys,sort=False):
        x=g.pnl_R.to_numpy(); wins=x[x>0]; losses=x[x<0]; equity=x.cumsum(); dd=equity-np.maximum.accumulate(np.r_[0,equity])[1:]; mdd=-dd.min(initial=0); n=len(x)
        pf=wins.sum()/-losses.sum() if losses.size else np.inf; sd=x.std(ddof=1) if n>1 else np.nan; downside=x[x<0].std(ddof=1) if (x<0).sum()>1 else np.nan
        streak=cur=0
        for v in x: cur=cur+1 if v<0 else 0; streak=max(streak,cur)
        rows.append(dict(zip(keys,key))|{"trades":n,"wins":len(wins),"losses":len(losses),"win_rate":len(wins)/n,"gross_pnl_price":g.gross_pnl_price.sum(),
          "net_pnl_price":g.net_pnl_price.sum(),"average_trade_R":x.mean(),"median_trade_R":np.median(x),"profit_factor":pf,"average_win_R":wins.mean() if len(wins) else np.nan,
          "average_loss_R":losses.mean() if len(losses) else np.nan,"payoff_ratio":wins.mean()/-losses.mean() if len(wins) and len(losses) else np.nan,"expectancy_R":x.mean(),
          "max_drawdown_R":mdd,"recovery_factor":x.sum()/mdd if mdd else np.nan,"sharpe":x.mean()/sd*np.sqrt(n) if n>=30 and sd else np.nan,
          "sortino":x.mean()/downside*np.sqrt(n) if n>=30 and downside else np.nan,"max_consecutive_losses":streak,"average_holding_bars":g.bars_held.mean(),
          "median_holding_bars":g.bars_held.median(),"net_result_R":x.sum(),"sample_flag":"VERY_LOW_SAMPLE" if n<20 else "LOW_SAMPLE" if n<50 else "MODERATE_SAMPLE" if n<100 else "BETTER_SAMPLE"})
    return pd.DataFrame(rows)


def run(data_root: str | Path, output: str | Path) -> dict:
    output=Path(output); output.mkdir(parents=True,exist_ok=True); frames={}; evs=[]; ledgers=[]; provenance=[]
    for inst in SPECS:
        f,p=load_discovery(data_root,inst); frames[inst]=f; provenance+=p; e=generate_signals(f,inst); evs.append(e); ledgers.append(simulate(f,e,SPECS[inst][0]))
    events=pd.concat(evs,ignore_index=True); ledger=pd.concat(ledgers,ignore_index=True); summary=metrics(ledger)
    outcomes=pd.concat([event_outcomes(frames[i],events[events.instrument==i]) for i in frames],ignore_index=True)
    monthly=(ledger.assign(month=ledger.entry_time.dt.strftime("%Y-%m")).groupby(["strategy_id","instrument","exit_configuration","friction_scenario","month"]).pnl_R.agg([("trades","size"),("net_result_R","sum"),("expectancy_R","mean")]).reset_index())
    surface=summary[summary.exit_configuration.str.startswith("STOP")].copy()
    for df,name in ((summary,"strategy_summary.csv"),(surface,"strategy_parameter_surface.csv"),(monthly,"monthly_summary.csv"),(outcomes,"event_outcomes.csv"),(ledger,"trade_ledger.csv")): df.to_csv(output/name,index=False)
    manifest={"status":"PARTIAL" if SKIPPED else "PASS","window":{"start":START.isoformat(),"end_exclusive":END.isoformat()},"rows":{i:len(f) for i,f in frames.items()},
      "dates":{i:[f.open_time.min().isoformat(),f.close_time.max().isoformat()] for i,f in frames.items()},"strategies_executed":list(STRATEGIES),"skipped":SKIPPED,
      "raw_signals":len(events),"trade_simulations":len(ledger),"provenance":provenance,"tie_policy":"stop first","source_modified":False}
    (output/"run_manifest.json").write_text(json.dumps(manifest,indent=2,default=str)+"\n")
    top=summary.sort_values(["expectancy_R","profit_factor","max_drawdown_R"],ascending=[False,False,True]).head(15)
    # Avoid an optional ``tabulate`` runtime dependency in the research runner.
    report="# Phase 6B real known-strategy backtest\n\n```json\n"+json.dumps(manifest,indent=2,default=str)+"\n```\n\n## Top 15\n\n```csv\n"+top.to_csv(index=False)+"```\n"
    (output/"phase6b_report.md").write_text(report)
    return manifest
