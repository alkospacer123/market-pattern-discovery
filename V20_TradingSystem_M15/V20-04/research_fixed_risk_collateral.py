"""Research-only: separate fixed trading-risk base from GO cash collateral.

Replays the accepted historical frozen CAP2/CAP3 trade LEDGER unchanged.
No extra signal generation after unfillable risk-sized entries. No LIVE imports,
no broker requests, no prospective equity reinvestment. Static GO snapshot.
"""
from collections import defaultdict
import math
import pandas as pd

def simulate(df, risk_base, margin, point_rub, tick_rub):
    """Fixed risk base -> full risk-sized lots -> minimum required collateral.

    Cash floor uses entry-by-entry margin + C1 costs and realized strategy PnL.
    Both GO and trading-ruble PnL use historical constant per-contract values.
    Calculates theoretical full-lot positions WITHOUT GO censorship; this is
    valid only when a user-funded collateral deposit meets the floor.
    """
    assert risk_base > 0
    entries=[]
    positions={}
    risklimit=0.015*risk_base
    rejected=0
    theoretical=[]
    for i,t in enumerate(df.itertuples(index=False)):
        symbol=t.symbol
        price_risk=abs(float(t.risk))*point_rub[symbol]
        fee=2*tick_rub[symbol]
        one_lot_loss=price_risk+fee
        q=math.floor(risklimit/one_lot_loss + 1e-10) if one_lot_loss>0 else 0
        if q<1:
            rejected+=1
            continue
        assert q*one_lot_loss <= risklimit + 1e-7
        margin_cost=q*(margin[symbol]+fee)
        t0=pd.Timestamp(t.entry_time)
        t1=pd.Timestamp(t.exit_time)
        assert t1>=t0
        # Normal prior exit -> entry at same M15 timestamp;
        # entry-bar stop: entry then exit, not free GO before admission.
        entries.append((t0,1,symbol,i,True))
        entries.append((t1,2 if t0==t1 else 0,symbol,i,False))
        theoretical.append((i,q,one_lot_loss,margin_cost,price_risk,fee))
    entries.sort()
    info={t[0]:t[1:] for t in theoretical}
    used=0.
    peak_margin=0.
    peak_time=None
    worst_collateral_1=0.
    worst_collateral_15=0.
    worst_time_15=None
    realized=0.
    wins=0.
    losses=0.
    years=defaultdict(lambda:[0.,0.,0])
    dd=0.
    high=0.
    max_concurrent=0
    sum_budget_util=0.
    n=0
    minutil=1.
    max_risk_exposure=0.
    for at,_,symbol,i,isentry in entries:
        t=df.iloc[i]
        q,one_lot_loss,margin_cost,price_risk,fee=info[i]
        if isentry:
            assert i not in positions
            assert symbol not in positions.values(), "FROZEN_LEDGER_SAME_SYMBOL"
            positions[i]=symbol
            used+=margin_cost
            max_concurrent=max(max_concurrent,len(positions))
            peak_margin=max(peak_margin,used)
            if used>=peak_margin:
                peak_time=str(at)
            loss=q*one_lot_loss
            sum_budget_util+=loss/risklimit
            minutil=min(minutil,loss/risklimit)
            max_risk_exposure=max(max_risk_exposure,len(positions)*risklimit)
            n+=1
        else:
            assert i in positions
            used-=margin_cost
            del positions[i]
            pnl=float(t.net_R)*price_risk*q
            realized+=pnl
            if pnl>0:
                wins+=pnl
                years[str(at.year)][0]+=pnl
            elif pnl<0:
                losses-=pnl
                years[str(at.year)][1]-=pnl
            years[str(at.year)][2]+=1
            high=max(high,realized)
            dd=max(dd,high-realized)
        # Minimal starting CASH to maintain non-negative free equity after
        # realized PnL and a 50% spare margin buffer.
        worst_collateral_1=max(worst_collateral_1,used-realized,-realized)
        if 1.5*used-realized > worst_collateral_15:
            worst_collateral_15=1.5*used-realized
            worst_time_15=str(at)
        worst_collateral_15=max(worst_collateral_15,-realized)
        assert used >= -1e-4
    assert len(positions)==0 and abs(used)<1e-4
    return {
        "risk_base_rub":risk_base, "risk_per_entry_limit_rub":round(risklimit,2),
        "source_trades":len(df), "filled_full_qty":n, "risk_one_lot_skips":rejected,
        "max_active_symbols":max_concurrent,
        "peak_go_plus_c1_rub":round(peak_margin,2), "peak_go_time":peak_time,
        "peak_go_to_risk_base":round(peak_margin/risk_base,3),
        "conservative_cash_for_go_plus_50pct_rub":round(1.5*peak_margin,2),
        "cash_floor_go_only_after_realized_pnl_rub":round(max(0.,worst_collateral_1),2),
        "cash_floor_go50_after_realized_pnl_rub":round(max(0.,worst_collateral_15),2),
        "peak_go50_path_time":worst_time_15,
        "avg_filled_risk_fraction_of_1p5":round(sum_budget_util/n,4) if n else None,
        "min_filled_risk_fraction_of_1p5":round(minutil,4) if n else None,
        "max_aggregate_stop_risk_rub_upper_bound":round(max_risk_exposure,2),
        "net_rub":round(realized,2), "pf_rub":round(wins/losses,5) if losses else None,
        "dd_closed_rub":round(dd,2),
        "annual":{year:{"trades":vals[2], "net_rub":round(vals[0]-vals[1],2),
                        "pf_rub":round(vals[0]/vals[1],5) if vals[1] else None}
                  for year,vals in sorted(years.items())},
        "not_live":True, "one_static_go_snapshot":True,
    }
