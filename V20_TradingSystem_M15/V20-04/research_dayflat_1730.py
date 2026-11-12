"""Research-only: compare frozen carry trades with 17:30 MSK day-flat exits.

Frozen N4 replay is copied in scratch by research_cap4.py and modified ONLY
to exit at the observed 17:30 M15 Open. No LIVE/FINAM operations.

C1 costs, 2 ATR stops, NEXT_OPEN, stop-first, signal priority, 3rd session
exit and session quotas all retain frozen behavior.
"""
import json
import math
import pandas as pd
import numpy as np


def metric(ledger):
    r=ledger.net_R.to_numpy(float) if len(ledger) else np.empty(0)
    winners=float(r[r>0].sum())
    losers=float(-r[r<0].sum())
    ordered=ledger.sort_values(["exit_time","symbol","entry_time"],kind="stable") if len(ledger) else ledger
    seq=ordered.net_R.to_numpy(float) if len(ledger) else np.empty(0)
    curve=np.r_[0.,np.cumsum(seq)]
    return {"trades":int(len(ledger)),
            "pf":round(winners/losers,5) if losers>0 else None,
            "net_R":round(float(r.sum()),5),
            "dd_closed_R":round(float((np.maximum.accumulate(curve)-curve).max()),5),
            "exit_1730":int((ledger.exit_reason==8).sum()) if len(ledger) else 0,
            "carry_trades":int((ledger.session_count>=2).sum()) if len(ledger) else 0}


def analyze(d,modes,base_variants,flat_variants):
    report={}
    total_open_late=0
    for m in modes:
        report[m]={}
        for k in (2,3):
            orig,orig_open=base_variants[k].merged(d,m)
            flat,flat_open=flat_variants[k].merged(d,m)
            # No overnight positions may remain in a strict daily-flat replay,
            # provided all source sessions have a valid 17:30 M15 Open.
            lingering=flat.loc[flat.session_count>=2]
            assert not len(lingering),("DAYFLAT_OVERNIGHT_CARRY",m,k,len(lingering))
            assert not len(flat_open),("DAYFLAT_UNCLOSED_POSITIONS",m,k,len(flat_open))
            # No entry after cutoff should occur; the 17:15 signal is
            # not eligible in frozen V20, so the last entry is at 17:15.
            entered=pd.to_datetime(flat.entry_time)
            assert not len(flat) or ((entered.dt.hour*60+entered.dt.minute)<1050).all(),(
                "DAYFLAT_LATE_ENTRY",m,k)
            forced=flat.loc[flat.exit_reason==8]
            hours=pd.to_datetime(forced.exit_time)
            late_mask=hours.dt.hour*60+hours.dt.minute>1050
            late=forced.loc[late_mask]
            y={}
            for year in (2023,2024,2025,2026):
                old=orig.loc[orig.exit_year==year]
                new=flat.loc[flat.exit_year==year]
                y[str(year)]={"frozen":metric(old),"dayflat_1730":metric(new)}
            # Exits on the entry session are kept as-is, while holding trades
            # may close early or be replaced by next-session opportunities.
            o={"frozen":metric(orig),"dayflat_1730":metric(flat),
               "by_exit_year":y, "terminal_open_flat":len(flat_open),
               "late_open_fallback_count":len(late),
               "late_open_fallback_examples":late[["symbol","entry_time","exit_time","net_R"]].head(5).to_dict("records"),
               "not_live":True,"source_quote_scope":"2023-2026 YTD"}
            print("DAYFLAT_1730 "+m+" "+json.dumps({"quota":k,**o},
                   separators=(",",":"),ensure_ascii=False),flush=True)
            report[m][str(k)]=o
    print("DAYFLAT_1730_INVARIANTS=PASS",flush=True)
    return report
