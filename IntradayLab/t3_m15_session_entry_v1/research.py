"""Deterministic full-path gross-only session entry research."""
import argparse
from dataclasses import asdict
import json
from pathlib import Path
import platform
import numpy as np
import pandas as pd
from engine import E,FROZEN,HERE,MAIN,RULES,execute,features
LABELS=['GROSS_ONLY','COSTS_DEFERRED','NOT_LIVE_READY']
CALENDAR=[str(x) for x in pd.period_range('2023-01','2024-12',freq='M')]

def js(path,value):path.write_text(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n')
def csv(path,rows,columns=None):
    f = rows if isinstance(rows,pd.DataFrame) else pd.DataFrame(rows,columns=columns)
    f.to_csv(path,index=False,float_format='%.15g',lineterminator='\n')
def ordered(f):return f.sort_values(['exit_time','instrument','trade_id'],kind='mergesort').reset_index(drop=True)

def timestamp_mismatch(actual,reference):
    a=pd.to_datetime(actual,utc=True);r=pd.to_datetime(reference,utc=True)
    return ~((a==r)|(a.isna()&r.isna())).to_numpy()

def metrics(f,calendar,column='gross_R',opened=0):
    f = ordered(f)
    x = f[column].to_numpy(float)
    positive,negative = x[x>0].sum(),-x[x<0].sum()
    equity = np.r_[0.,x.cumsum()]
    monthly = {m:float(f.loc[f.exit_time.dt.strftime('%Y-%m').eq(m),column].sum()) for m in calendar}
    worst = min(monthly,key=monthly.get) if monthly else None
    streak = longest = 0
    for r in x:
        streak = streak+1 if r < 0 else 0
        longest = max(longest,streak)
    result = {'closed_trades':len(f),'open_positions_at_period_end':opened,
        'gross_PF':float(positive/negative) if negative else None,'gross_R':float(x.sum()),
        'expectancy_R':float(x.mean()) if len(x) else None,'positive_R':float(positive),
        'negative_R_volume':float(negative),'max_drawdown_closed_R':float((np.maximum.accumulate(equity)-equity).max()),
        'max_consecutive_losses':longest,'calendar_months':len(calendar),
        'positive_months':sum(v>0 for v in monthly.values()),'negative_months':sum(v<0 for v in monthly.values()),
        'zero_months':sum(v==0 for v in monthly.values()),'no_closed_trade_months':sum(not f.exit_time.dt.strftime('%Y-%m').eq(m).any() for m in calendar),
        'worst_month':worst,'worst_month_R':monthly.get(worst),
        'win_rate':float((x>0).mean()) if len(x) else None}
    for sign in ('positive','negative','zero'):
        result[sign+'_month_share'] = result[sign+'_months']/len(calendar) if calendar else None
    ms = longest_ms = 0
    for value in monthly.values():
        ms = ms+1 if value<0 else 0
        longest_ms = max(longest_ms,ms)
    result['max_losing_month_streak'] = longest_ms
    wins = np.sort(x[x>0])[::-1]
    for n in (5,10):
        top = float(wins[:n].sum())
        result.update({f'top{n}_positive_R':top,f'top{n}_share_positive_R':top/positive if positive else None,
            f'gross_R_without_top{n}':float(x.sum()-top),f'gross_PF_without_top{n}':float((positive-top)/negative) if negative else None})
    return result


def control_gate(trades,opened,output):
    details,diffs = [],[]
    references = [('490',FROZEN/'trades.csv'),('495',HERE.parent/'t3_m15_entry_regime_v1/results/trades_CONTROL.csv')]
    # Historical costs and pseudo-tick units are intentionally not part of this gross experiment.
    excluded = {'C1_R','net_R','c1_price_unit','initial_risk_ticks'}
    for label,path in references:
        ref = pd.read_csv(path)
        fields = [c for c in ref if c not in excluded]
        assert set(fields).issubset(trades.columns),(label,set(fields)-set(trades.columns))
        for version in E.CONFIGS:
            a = ordered(trades.loc[trades.version.eq(version)].copy())
            r = ref.loc[ref.version.eq(version)].copy()
            r.exit_time = pd.to_datetime(r.exit_time,utc=True).dt.tz_convert(E.TZ)
            r = ordered(r)
            assert len(a) == len(r),(label,version,len(a),len(r))
            maxima = {}
            for c in fields:
                av,rv = a[c],r[c]
                if c.endswith('_time') or c in ('H1AvailableAt','H1PreviousAvailableAt'):
                    bad = timestamp_mismatch(av,rv)
                elif pd.api.types.is_numeric_dtype(rv) and not pd.api.types.is_bool_dtype(rv):
                    delta = abs(av.to_numpy(float)-rv.to_numpy(float))
                    bad = (delta>1e-8) | (np.isnan(av.to_numpy(float)) != np.isnan(rv.to_numpy(float)))
                    maxima[c] = float(np.nanmax(delta)) if np.isfinite(delta).any() else 0.
                else:
                    bad = av.fillna('').astype(str).to_numpy() != rv.fillna('').astype(str).to_numpy()
                for i in np.flatnonzero(bad):diffs.append({'reference':label,'version':version,'row':int(i),'field':c,'actual':str(av.iloc[i]),'expected':str(rv.iloc[i])})
            details.append({'reference':label,'version':version,'closed':len(a),'fields_compared':fields,'maximum_deltas':maxima})
    ref_open = json.loads((FROZEN/'OPEN_POSITIONS.json').read_text())
    assert len(opened) == len(ref_open) == 2
    open_fields = 0
    for r in ref_open:
        a = next(o for o in opened if o['version']==r['version'] and o['instrument']==r['instrument'])
        for c,v in r.items():
            if c == 'exit_C1_and_funding':continue
            assert c in a
            assert abs(a[c]-v)<=1e-8 if isinstance(v,float) else a[c]==v,(c,a[c],v)
            open_fields += 1
    second_open=json.loads((HERE.parent/'t3_m15_entry_regime_v1/results/CONTROL_OPEN_POSITIONS.json').read_text())
    for r in second_open:
        a=next(o for o in opened if o['version']==r['version'] and o['instrument']==r['instrument'])
        for c,v in r.items():
            assert abs(a[c]-v)<=1e-8 if isinstance(v,float) else a[c]==v,(c,a[c],v)
            open_fields+=1
    csv(output/'CONTROL_DIFF.csv',diffs,['reference','version','row','field','actual','expected'])
    result = {'status':'PASS' if not diffs else 'FAIL','closed_total':len(trades),'terminal_open':len(opened),
        'numeric_absolute_tolerance':1e-8,'all_common_fields_compared':True,'open_fields_compared':open_fields,
        'excluded_historical_economics':sorted(excluded),'details':details,'differences':len(diffs)}
    js(output/'CONTROL_REPRODUCTION.json',result)
    assert not diffs and len(trades)==1442,'CONTROL_FAILED_VARIANTS_BLOCKED'


def reports(trades,opened,snapshots,frames,output):
    overall,yearly,direction,monthly,november,equity,streaks,top = [],[],[],[],[],[],[],[]
    for v in E.CONFIGS:
        for rule in RULES:
            base=trades.loc[trades.version.eq(v)&trades.rule.eq(rule)]
            for scope in ('ALL_FOUR',*E.SYMBOLS):
                symbols=E.SYMBOLS if scope=='ALL_FOUR' else (scope,)
                f=base.loc[base.instrument.isin(symbols)]
                first=min(frames[s].index[0] for s in symbols).strftime('%Y-%m')
                available=[m for m in CALENDAR if m>=first]
                ids={'version':v,'rule':rule,'scope':scope}
                os=[o for o in opened if o['version']==v and o['rule']==rule and o['instrument'] in symbols]
                ys=[o for o in snapshots if o['version']==v and o['rule']==rule and o['instrument'] in symbols]
                overall.append(ids|{'first_available_month':first,'covered_calendar_months':len(available),
                    'positive_share_covered_months':sum(f.loc[f.exit_time.dt.strftime('%Y-%m').eq(m),'gross_R'].sum()>0 for m in available)/len(available)}|metrics(f,CALENDAR,opened=len(os)))
                for year in (2023,2024):
                    y=f.loc[f.exit_time.dt.year.eq(year)];cal=[m for m in CALENDAR if m.startswith(str(year))]
                    oy=[o for o in ys if o['month']==f'{year}-12']
                    yearly.append(ids|{'year':year}|metrics(y,cal,opened=len(oy)))
                for dr in ('LONG','SHORT'):
                    for year in ('ALL',2023,2024):
                        y=f.loc[f.direction.eq(dr)]
                        if year!='ALL':y=y.loc[y.exit_time.dt.year.eq(year)]
                        cal=CALENDAR if year=='ALL' else [m for m in CALENDAR if m.startswith(str(year))]
                        oy=os if year=='ALL' else [o for o in ys if o['month']==f'{year}-12']
                        direction.append(ids|{'year':year,'direction':dr}|metrics(y,cal,opened=sum(o['direction']==dr for o in oy)))
                for m in CALENDAR:
                    y=f.loc[f.exit_time.dt.strftime('%Y-%m').eq(m)]
                    monthly.append(ids|{'month':m,'coverage':'NO_COVERAGE' if m<first else 'AVAILABLE'}|
                        metrics(y,[m],opened=sum(o['month']==m for o in ys)))
                y=f.loc[f.exit_time.dt.year.eq(2024)];rest=y.loc[y.exit_time.dt.month.ne(11)]
                full=metrics(y,CALENDAR[12:]);rem=metrics(rest,[m for m in CALENDAR[12:] if m!='2024-11'])
                november.append(ids|{'year':2024,'full_PF':full['gross_PF'],'full_R':full['gross_R'],
                    'november_closed':int(y.exit_time.dt.month.eq(11).sum()),
                    'november_R':float(y.loc[y.exit_time.dt.month.eq(11),'gross_R'].sum()),
                    'ex_november_closed':len(rest),'ex_november_PF':rem['gross_PF'],'ex_november_R':rem['gross_R'],
                    'ex_november_drawdown_R':rem['max_drawdown_closed_R']})
                vals={m:float(f.loc[f.exit_time.dt.strftime('%Y-%m').eq(m),'gross_R'].sum()) for m in CALENDAR}
                run=[]
                for m,val in list(vals.items())+[('END',0)]:
                    if val<0:run.append(m)
                    elif run:
                        streaks.append(ids|{'first_month':run[0],'last_month':run[-1],'months':len(run),'gross_R':sum(vals[x] for x in run)});run=[]
                for n in (5,10):
                    winners=f.loc[f.gross_R.gt(0)].sort_values(['gross_R','instrument','trade_id'],ascending=[False,True,True],kind='mergesort').head(n)
                    for rank,r in enumerate(winners.to_dict('records'),1):top.append(ids|{'top_n':n,'rank':rank,'instrument':r['instrument'],'trade_id':r['trade_id'],'entry_time':r['entry_time'],'exit_time':r['exit_time'],'gross_R':r['gross_R']})
                if scope=='ALL_FOUR':
                    total=peak=0.
                    for r in ordered(f).to_dict('records'):
                        total+=r['gross_R'];peak=max(peak,total)
                        equity.append(ids|{'exit_time':r['exit_time'],'instrument':r['instrument'],'trade_id':r['trade_id'],'trade_R':r['gross_R'],'cumulative_closed_R':total,'drawdown_R':peak-total})
    for name,rows in [('overall_report.csv',overall),('yearly_report.csv',yearly),('direction_report.csv',direction),('monthly_report.csv',monthly),('november_dependence.csv',november),('closed_equity.csv',equity),('losing_month_runs.csv',streaks),('top_winners.csv',top),('instrument_report.csv',[r for r in overall if r['scope']!='ALL_FOUR'])]:csv(output/name,rows)


def run(data_root,output,controls_only=False):
    output.mkdir(parents=True,exist_ok=True)
    assert output.resolve().is_relative_to(HERE.resolve())
    assert E.git(data_root,'rev-parse','HEAD')==E.DATA_COMMIT
    specs=json.loads((HERE/'EXPERIMENT_SPECS.json').read_text())
    assert specs['base_main']==MAIN and specs['data_commit']==E.DATA_COMMIT
    assert specs['configurations']=={v:asdict(p) for v,p in E.CONFIGS.items()}
    frames,lows={},{}
    refs=[FROZEN/'engine.py',FROZEN/'trades.csv',FROZEN/'OPEN_POSITIONS.json',
        HERE.parent/'t3_m15_entry_regime_v1/results/trades_CONTROL.csv',
        HERE.parent/'t3_m15_entry_regime_v1/results/CONTROL_OPEN_POSITIONS.json',HERE.parent/'ROADMAP.md']
    manifest={'base_main':MAIN,'data_commit':E.DATA_COMMIT,'labels':LABELS,'future_OHLC_parsed':False,
        'full_file_integrity':'Opaque SHA hashing of full bytes; timestamp-first parser stops before 2025+ OHLC.',
        'sources':[],'runtime':{'python':platform.python_version(),'pandas':pd.__version__,'numpy':np.__version__},
        'freeze_commit':E.git(HERE,'log','-1','--format=%H','--','EXPERIMENT_SPECS.json'),
        'spec_sha256':E.sha_file(HERE/'EXPERIMENT_SPECS.json'),
        'implementation_sha256':{p.name:E.sha_file(p) for p in sorted(HERE.glob('*.py'))},
        'reference_sha256':{str(p.relative_to(HERE.parent)):E.sha_file(p) for p in refs}}
    for s in E.SYMBOLS:
        relative=f'forever/{s}/{s}_M15.csv';src=E.verify_source(data_root,relative)
        raw,prefix_sha=E.read_prefix(data_root/relative);frames[s]=E.close_index(raw)
        lows[s],_=features(frames[s],E.CONFIGS['BASELINE'])
        src.update(instrument=s,historical_prefix_sha256=prefix_sha,used_candles=len(frames[s]),
            first_open=raw.index[0].isoformat(),last_open=raw.index[-1].isoformat(),
            first_close=frames[s].index[0].isoformat(),last_close=frames[s].index[-1].isoformat())
        manifest['sources'].append(src)
    trades,opened,stops,entries,gaps,snapshots=[],[],[],[],[],[]
    def replay(rule):
        for v,p in E.CONFIGS.items():
            for s in E.SYMBOLS:
                t,o,d,e,g,y=execute(lows[s],s,v,p,rule)
                trades.extend(t);stops.extend(d);entries.extend(e);gaps.extend(g);snapshots.extend(y)
                if o:opened.append(o)
    replay('CONTROL');control_gate(pd.DataFrame(trades),opened,output)
    csv(output/'control_gross_trades.csv',trades);js(output/'CONTROL_OPEN_POSITIONS.json',opened.copy())
    js(output/'SOURCE_MANIFEST.json',manifest)
    if controls_only:
        print(json.dumps({'control':'PASS','closed':len(trades),'open':len(opened)}));return
    gate=json.loads((HERE/'PRE_VARIANT_GATE.json').read_text())
    assert gate['control']=='PASS' and gate['tests']=='PASS' and gate['freeze_commit']==manifest['freeze_commit']
    for name,sha in manifest['implementation_sha256'].items():
        committed=__import__('subprocess').check_output(['git','-C',str(HERE),'show',f"{manifest['freeze_commit']}:{(HERE/name).relative_to(HERE.parent.parent)}"])
        assert __import__('hashlib').sha256(committed).hexdigest()==sha,'FROZEN_CODE_CHANGED'
    for rule in RULES[1:]:replay(rule)
    f=pd.DataFrame(trades).sort_values(['version','rule','exit_time','instrument','trade_id'],kind='mergesort').reset_index(drop=True)
    csv(output/'trades.csv',f)
    for rule in RULES:csv(output/f'trades_{rule}.csv',f.loc[f.rule.eq(rule)])
    js(output/'OPEN_POSITIONS.json',opened);js(output/'PERIOD_END_OPEN_POSITIONS.json',snapshots)
    csv(output/'stop_decisions.csv',stops);csv(output/'entry_opportunities.csv',entries);csv(output/'observed_gaps.csv',gaps)
    reports(f,opened,snapshots,frames,output)
    from diagnostics import diagnostics
    diagnostics(f,opened,pd.DataFrame(entries),pd.DataFrame(gaps),frames,output)
    from render_report import render
    render(output)
    js(output/'GENERATED_SHA256.json',{p.name:E.sha_file(p) for p in sorted(output.iterdir()) if p.is_file() and p.name!='GENERATED_SHA256.json'})
    print(json.dumps({'control':'PASS','closed_total':len(f),'terminal_open_total':len(opened),'fixed_replays':6},sort_keys=True))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data-root',type=Path,required=True)
    p.add_argument('--output',type=Path,default=HERE/'results');p.add_argument('--controls-only',action='store_true')
    a=p.parse_args();run(a.data_root,a.output,a.controls_only)
