"""Offline cash-aware M15 replay, N4 2023-2026 YTD: no LIVE imports.

Research adapter faithfully follows the SHA-verified frozen replay loop for
signals, next-open, 2*ATR stop, stop-first, target, third-observed-session exit
and priority CNY/GLD/IMOEX/USD. Admission gate alone varies with policy.
RUB price multipliers, tick-cost C1, GO are the single historical snapshot
already used by V20-04; they are NOT historical FINAM GO/fees.
Equity = initial deposit + realized closed PnL; NOT broker variation-margin
mark-to-market. Outputs are a research approximation, never LIVE approval.
"""
from __future__ import annotations
import math
import numpy as np
import pandas as pd
from numba import njit

POLICIES = ("current_cash", "half", "reserve_next", "reserve_n4", "one_position_full_go")
BANKS = (45000,60000,75000,100000,150000)
QUOTAS = (2,3)
SYMS = ("CNYRUBF","GLDRUBF","IMOEXF","USDRUBF")
GO = (1139.,1782.,8252.,21204.)
RUB = (1000.,1.,10.,1000.)
FEE = (2.,.2,10.,20.)
TICK = (.001,.1,.5,.01)


def arrays(d, mode):
    chunks=[]
    for s,symbol in enumerate(SYMS):
        f=d[symbol][["Datetime","day","Open","High","Low","Close","atr",
                      mode,mode+"_target",mode+"_tpr"]].copy()
        f["sym"]=s
        f["day_sess"]=pd.factorize(f.day)[0]
        f["tick"]=TICK[s]
        # Known before the next bar: last completed ATR of each symbol.
        f["atr_old"]=f["atr"].shift(1).to_numpy()
        f["weekend"]=(f.Datetime.dt.weekday>=5).astype(np.int64)
        chunks.append(f)
    z=pd.concat(chunks,ignore_index=True).sort_values(
        ["Datetime","sym"],kind="stable").reset_index(drop=True)
    z["day_n"]=pd.factorize(z.day)[0]
    def field(name,dtype):
        return z[name].to_numpy(dtype)
    return (field("Datetime","datetime64[ns]").astype("int64"),
        field("sym",np.int64),field("day_n",np.int64),
        field("day_sess",np.int64),field("Open",np.float64),
        field("High",np.float64),field("Low",np.float64),
        field("atr",np.float64),field("atr_old",np.float64),
        field(mode,np.int64),field(mode+"_target",np.float64),
        field(mode+"_tpr",np.float64),field("weekend",np.int64))


@njit
def replay_cash(ts,sym,day,day_sess,op,hi,lo,atr,atr_old,signal,target,
                tpr,weekend,bank,quota,policy,block_weekend,go_factor=1.0,
                fixed_equity_risk=False):
    pos=np.zeros(4,np.int64)
    pending=np.full(4,-1,np.int64)
    used=np.full(4,-1,np.int64)
    side=np.zeros(4,np.int64)
    entry=np.zeros(4)
    stop=np.zeros(4)
    risk=np.zeros(4)
    tp=np.full(4,np.nan)
    en_idx=np.zeros(4,np.int64)
    en_day=np.zeros(4,np.int64)
    q=np.zeros(4,np.int64)
    committed=np.zeros(4)
    trade_risk=np.zeros(4)
    latest_atr=np.full(4,np.nan)
    prior_atr=np.full(4,np.nan)
    latest_ts=np.full(4,-1,np.int64)
    used_global_day=np.full(4,-1,np.int64)
    equity=bank
    peak=bank
    max_dd=0.
    max_dd_pct=0.
    min_equity=bank
    go_peak=0.
    risk_peak=0.
    gd=-1; nent=0
    accepted=0; rejected_go=0;rejected_risk=0;rejected_weekend=0;rejected_busy=0
    exits=[]  # exit_idx, symbol_idx, enter_idx, contracts, profit, entry_risk_rub
    for i in range(len(ts)):
        s=sym[i]
        if day[i]!=gd:
            gd=day[i]
            nent=0
        if pos[s]:
            x=0.;why=0
            if day_sess[i]-en_day[s]>=2:
                x=op[i];why=3
            elif (side[s]==1 and op[i]<=stop[s]+TICK[s]*1e-7) or (
                  side[s]==-1 and op[i]>=stop[s]-TICK[s]*1e-7):
                x=op[i];why=2
            elif (side[s]==1 and lo[i]<=stop[s]+TICK[s]*1e-7) or (
                  side[s]==-1 and hi[i]>=stop[s]-TICK[s]*1e-7):
                x=stop[s];why=1
            elif np.isfinite(tp[s]):
                if (side[s]==1 and op[i]>=tp[s]-TICK[s]*1e-7) or (
                    side[s]==-1 and op[i]<=tp[s]+TICK[s]*1e-7):
                    x=op[i];why=6
                elif (side[s]==1 and hi[i]>=tp[s]-TICK[s]*1e-7) or (
                      side[s]==-1 and lo[i]<=tp[s]+TICK[s]*1e-7):
                    x=tp[s];why=5
            if why:
                pnl=q[s]*(side[s]*(x-entry[s])*RUB[s]-FEE[s])
                equity+=pnl
                min_equity=min(min_equity,equity)
                peak=max(peak,equity)
                max_dd=max(max_dd,peak-equity)
                max_dd_pct=max(max_dd_pct,(peak-equity)/peak)
                exits.append((i,s,en_idx[s],q[s],pnl,trade_risk[s]))
                pos[s]=0;q[s]=0;committed[s]=0.;trade_risk[s]=0.
        if pending[s]>=0:
            at=pending[s]
            # One-position variant: reject a new NEXT_OPEN entry while
            # another instrument is open; keep frozen signals/exit/order.
            eligible_open=(ts[i]==ts[at]+900000000000 and pos[s]==0
                           and used[s]!=day_sess[i] and nent<quota)
            busy=(policy==4 and np.sum(pos)>0)
            if eligible_open and busy:
                rejected_busy+=1
            if eligible_open and not busy:
                direction=signal[at];price=op[i]
                raw=price-direction*2*atr[at]
                sp=(np.floor(raw/TICK[s]+1e-9) if direction==1 else
                    np.ceil(raw/TICK[s]-1e-9))*TICK[s]
                dist=abs(price-sp)
                targ=target[at]
                if not np.isfinite(targ) and np.isfinite(tpr[at]):
                    targ=price+direction*tpr[at]*dist
                if np.isfinite(targ):
                    targ=(np.floor(targ/TICK[s]+1e-9) if direction==1 else
                          np.ceil(targ/TICK[s]-1e-9))*TICK[s]
                if dist>0 and np.isfinite(dist) and (
                   not np.isfinite(targ) or direction*(targ-price)>0):
                    if block_weekend and weekend[i]:
                        rejected_weekend+=1
                    else:
                        per_lot=dist*RUB[s]+FEE[s]
                        held_go=0.; held_risk=0.
                        for j in range(4):
                            held_go+=committed[j]
                            held_risk+=trade_risk[j]
                        if policy==-1:
                            qty=1
                        else:
                            risk_base=bank if fixed_equity_risk else equity
                            risk_budget=min(.015*risk_base,.06*risk_base-held_risk)
                            qty=int(np.floor((risk_budget+1e-9)/per_lot)) if (
                                equity>0 and risk_budget>0) else 0
                        if qty<1:
                            rejected_risk+=1
                        else:
                            available=equity-held_go
                            reserve=0.
                            if policy==1: # half of equity nominal max per new position
                                available=min(available,equity*.5)
                            elif policy==2 and nent+1<quota and ((ts[i]//60000000000)%1440)<1035:
                                # One next different N4 instrument; never
                                # reserve for the already-open or used symbol.
                                # A next day/session may need rebalancing anew.
                                for j in range(4):
                                    if j==s or pos[j] or used_global_day[j]==day[i]:
                                        continue
                                    old=prior_atr[j] if latest_ts[j]==ts[i] else latest_atr[j]
                                    # If we cannot establish eligibility
                                    # safely, reserve one GO lot anyway.
                                    eligible=not np.isfinite(old) or (
                                        2*old*RUB[j]+FEE[j]<=.015*equity)
                                    if eligible:
                                        reserve=max(reserve,go_factor*GO[j]+FEE[j])
                                available-=reserve
                            elif policy==3:
                                # Strict N4 cash reservation: hold one lot of
                                # margin + model C1 per other FLAT instrument,
                                # even if its next eligible signal is unknown.
                                # Active positions are already charged in
                                # held_go; never double-count their margin.
                                # Carry positions can span future sessions,
                                # so this is intentionally NOT limited to
                                # remaining entries today.
                                for j in range(4):
                                    if j!=s and pos[j]==0:
                                        reserve+=go_factor*GO[j]+FEE[j]
                                available-=reserve
                            if policy!=-1:
                                max_q=int(np.floor((available+1e-7)/(go_factor*GO[s]+FEE[s])))
                                qty=min(qty,max_q)
                            if qty<1:
                                rejected_go+=1
                            else:
                                en_idx[s]=i;side[s]=direction
                                entry[s]=price;stop[s]=sp;risk[s]=dist;tp[s]=targ
                                en_day[s]=day_sess[i];used[s]=day_sess[i]
                                used_global_day[s]=day[i]
                                pos[s]=1;q[s]=qty;nent+=1;accepted+=1
                                committed[s]=qty*(go_factor*GO[s]+FEE[s])
                                trade_risk[s]=qty*per_lot
                                total_go=0.;total_risk=0.
                                for j in range(4):
                                    total_go+=committed[j]
                                    total_risk+=trade_risk[j]
                                go_peak=max(go_peak,total_go)
                                risk_peak=max(risk_peak,total_risk)
                                if policy!=-1:
                                    assert total_go<=equity+1e-6
                                    assert total_risk<=.06*risk_base+1e-6
                                    assert qty*per_lot<=.015*risk_base+1e-6
                                # Frozen stop-first on entry bar.
                                close_now=0.
                                if (direction==1 and lo[i]<=sp+TICK[s]*1e-7) or (
                                    direction==-1 and hi[i]>=sp-TICK[s]*1e-7):
                                    close_now=sp
                                elif np.isfinite(targ) and (
                                    (direction==1 and hi[i]>=targ-TICK[s]*1e-7) or
                                    (direction==-1 and lo[i]<=targ+TICK[s]*1e-7)):
                                    close_now=targ
                                if close_now!=0.:
                                    pnl=qty*(direction*(close_now-price)*RUB[s]-FEE[s])
                                    equity+=pnl
                                    min_equity=min(min_equity,equity)
                                    peak=max(peak,equity)
                                    max_dd=max(max_dd,peak-equity)
                                    max_dd_pct=max(max_dd_pct,(peak-equity)/peak)
                                    exits.append((i,s,i,qty,pnl,trade_risk[s]))
                                    pos[s]=0;q[s]=0;committed[s]=0.;trade_risk[s]=0.
            pending[s]=-1
        # As in frozen replay, a rejected pending entry does not consume
        # per-day/symbol limits. A new valid signal may re-arm after it.
        if signal[i]!=0 and pos[s]==0 and used[s]!=day_sess[i] and (
                np.isfinite(atr[i]) and atr[i]>0):
            pending[s]=i
        if np.isfinite(atr[i]) and atr[i]>0:
            prior_atr[s]=latest_atr[s]
            latest_atr[s]=atr[i]
            latest_ts[s]=ts[i]
    return (exits,accepted,rejected_go,rejected_risk,rejected_weekend,
            go_peak,risk_peak,max_dd,max_dd_pct,min_equity,equity,
            int(np.sum(pos)),rejected_busy)


def metrics(events,arr,bank):
    ts=arr[0]
    ledger=[]
    for i,s,en,q,pnl,risk in events:
        ledger.append((pd.Timestamp(ts[i]),s,q,pnl,risk))
    closed=pd.DataFrame(ledger,columns=["exit","sym","qty","pnl","risk"])
    closed.sort_values(["exit","sym"],kind="stable",inplace=True)
    years={}
    if not closed.empty:
        for year,f in closed.groupby(closed.exit.dt.year):
            w=f.loc[f.pnl>0,"pnl"].sum()
            l=-f.loc[f.pnl<0,"pnl"].sum()
            years[str(year)]={"trades":len(f),"net":round(f.pnl.sum(),2),
                              "pf":round(w/l,4) if l else None}
    # Preserve months with zero trades, not just months with closes.
    months=pd.period_range(pd.Timestamp(ts[0]).to_period("M"),
                           pd.Timestamp(ts[-1]).to_period("M"),freq="M")
    pnl_by_month=(closed.groupby(closed.exit.dt.to_period("M")).pnl.sum()
                   if len(closed) else pd.Series(dtype=float))
    # Comparable monthly trade counts and monetary PF for EVERY policy,
    # including strict N4, from actual accepted cash-aware exits.
    month_stats={}
    if not closed.empty:
        for month,f in closed.groupby(closed.exit.dt.to_period("M")):
            win=float(f.loc[f.pnl>0,"pnl"].sum())
            loss=float(-f.loc[f.pnl<0,"pnl"].sum())
            month_stats[str(month)]={"trades":len(f),
                                    "pf":round(win/loss,4) if loss else None}
    capital=bank
    returns=[]
    for month in months:
        p=float(pnl_by_month.get(month,0.))
        rate=100.*p/capital if capital>0 else float("nan")
        returns.append({"month":str(month),"pnl":round(p,2),
                        "return_pct":round(rate,4),
                        **month_stats.get(str(month),{"trades":0,"pf":None})})
        capital+=p
    valid=[x["return_pct"] for x in returns if math.isfinite(x["return_pct"])]
    # Last quoted month is partial; provide both full and all-month views.
    full=valid[:-1] if len(valid)>1 else valid
    winners=float(closed.loc[closed.pnl>0,"pnl"].sum()) if len(closed) else 0
    losers=float(-closed.loc[closed.pnl<0,"pnl"].sum()) if len(closed) else 0
    return {"trades":len(closed),"end_equity":round(capital,2),
            "net_rub":round(capital-bank,2),
            "total_return_pct":round(100*(capital/bank-1),2),
            "pf":round(winners/losers,4) if losers else None,
            "months":len(valid),"full_months_excluding_last":len(full),
            "mean_month_pct_full":round(float(np.mean(full)),3) if full else None,
            "median_month_pct_full":round(float(np.median(full)),3) if full else None,
            "months_ge10_full":sum(x>=10 for x in full),
            "months_negative_full":sum(x<0 for x in full),
            "min_month_pct_full":round(min(full),3) if full else None,
            "max_month_pct_full":round(max(full),3) if full else None,
            "yearly":years,"monthly":returns}


def run(d,modes,variants):
    results={}
    for mode in modes:
        a=arrays(d,mode)
        scenarios={}
        for q in QUOTAS:
            reference,_=variants[q].merged(d,mode)
            # Validate exact frozen trades, entry timing, return, and count
            # when policy bypasses monetary admission and weekend gate.
            ev,*meta=replay_cash(*a,45000.,q,-1,False)
            check=metrics(ev,a,45000.)
            assert check["trades"]==len(reference),(
                "FROZEN_REPLAY_TRADE_COUNT_PARITY",mode,q,len(reference),
                check["trades"])
            ordered=reference.sort_values(["exit_time","symbol","entry_time"])
            # RUB 1-lot return translated back to frozen net_R.
            got=sorted((str(pd.Timestamp(a[0][i])),SYMS[s],
                        round(pnl/(abs(risk-FEE[s])+1e-20),5))
                       for i,s,en,quantity,pnl,risk in ev)
            expected=sorted((str(pd.Timestamp(t.exit_time)),t.symbol,
                             round(float(t.net_R),5))
                            for t in reference.itertuples(index=False))
            assert len(got)==len(expected)
            for left,right in zip(got,expected):
                assert left[0]==right[0] and left[1]==right[1] and abs(left[2]-right[2])<=1e-3,(
                    "FROZEN_REPLAY_NET_R_PARITY",mode,q,left,right)
            print("CASH_FULL_REPLAY_FROZEN_PARITY",mode,q,len(reference),flush=True)
            for bank in BANKS:
                for policy,name in enumerate(POLICIES):
                    for go_factor in (1.0,0.5):
                        ev,accepted,blocked_go,blocked_risk,weekend_skips,peak_go,peak_risk,dd,ddp,mineq,end_equity,unclosed,busy_skips=(
                            replay_cash(*a,float(bank),q,policy,True,go_factor))
                        z=metrics(ev,a,bank)
                        # Targeted diagnostic: normalize actual cash trades back to R
                        # and compare with a constant 45k sizing risk.
                        if q==2 and bank==45000 and policy==0 and go_factor==0.5:
                            records=[]
                            for i,s,en,quantity,pnl,exposure in ev:
                                if pd.Timestamp(a[0][i]).year!=2025:
                                    continue
                                stop_rub=exposure-quantity*FEE[s]
                                assert stop_rub>0, "INVALID_STOP_EXPOSURE"
                                records.append((pnl,pnl/stop_rub,stop_rub))
                            wR=sum(max(0.,r) for _,r,_ in records)
                            lR=sum(max(0.,-r) for _,r,_ in records)
                            wP=sum(max(0.,p) for p,_,_ in records)
                            lP=sum(max(0.,-p) for p,_,_ in records)
                            avg_win_exposure=(sum(e for p,r,e in records if p>0) /
                                              sum(1 for p,r,e in records if p>0))
                            avg_loss_exposure=(sum(e for p,r,e in records if p<0) /
                                               sum(1 for p,r,e in records if p<0))
                            fixed_ev,*_ = replay_cash(*a,float(bank),q,policy,True,
                                                      go_factor,True)
                            fixed=metrics(fixed_ev,a,bank)
                            audit={
                                "robot":mode,"bank":bank,"go_factor":go_factor,
                                "original_cash_2025":z["yearly"]["2025"],
                                "cash_2025_reconciled":{"n":len(records),
                                   "gross_profit":round(wP,2),"gross_loss":round(lP,2),
                                   "pf":round(wP/lP,6)},
                                "same_fills_normalized_R_2025":{
                                    "n":len(records),"gross_positive_R":round(wR,4),
                                    "gross_negative_R":round(lR,4),
                                    "pf_R":round(wR/lR,6),
                                    "avg_exposure_winning_rub":round(avg_win_exposure,2),
                                    "avg_exposure_losing_rub":round(avg_loss_exposure,2)},
                                "fixed_45000_risk_cash_2025":fixed["yearly"]["2025"],
                                "fixed_risk_all_trades":fixed["trades"]}
                            print("CASH_2025_DIAGNOSTIC",
                                  __import__("json").dumps(audit,separators=(",",":")),
                                  flush=True)
                        z.update(bank=bank,quota=q,policy=name,go_factor=go_factor,accepted=accepted,
                            rejected_go=blocked_go,rejected_risk=blocked_risk,
                            rejected_weekend=weekend_skips,rejected_busy=busy_skips,peak_go=round(peak_go,2),
                            peak_risk=round(peak_risk,2),
                            closed_dd_rub=round(dd,2),
                            closed_dd_pct=round(100*ddp,2),
                            min_realized_equity=round(mineq,2),unclosed=unclosed)
                        scenarios[f"{q}:{bank}:{name}:{go_factor}"]=z
                        print("CASH_FULL_REPLAY_GO_SCALE",mode,
                              __import__("json").dumps(z,ensure_ascii=False,
                              separators=(",",":")),flush=True)
        results[mode]=scenarios
    return results
