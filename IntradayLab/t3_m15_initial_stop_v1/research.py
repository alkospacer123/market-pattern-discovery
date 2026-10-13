"""CONTROL gates precede variants; deterministic journals and dual-normalization reports."""
import argparse
from dataclasses import asdict
import json
from pathlib import Path
import platform
import numpy as np
import pandas as pd
from engine import E,FROZEN,HERE,MAIN,RULES,execute,features

LABELS = ['GROSS_ONLY','COSTS_DEFERRED','NOT_LIVE_READY']
CALENDAR = [str(x) for x in pd.period_range('2023-01','2024-12',freq='M')]
NORMALIZATIONS = {'ACTUAL_INITIAL_RISK':'gross_R','REFERENCE_2ATR':'reference_2ATR_R'}

def js(path,value):path.write_text(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n')
def csv(path,rows,columns=None):
    f = rows if isinstance(rows,pd.DataFrame) else pd.DataFrame(rows,columns=columns)
    f.to_csv(path,index=False,float_format='%.15g',lineterminator='\n')
def ordered(f):return f.sort_values(['exit_time','instrument','trade_id'],kind='mergesort').reset_index(drop=True)

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
                    bad = pd.to_datetime(av,utc=True).to_numpy() != pd.to_datetime(rv,utc=True).to_numpy()
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
    csv(output/'CONTROL_DIFF.csv',diffs,['reference','version','row','field','actual','expected'])
    result = {'status':'PASS' if not diffs else 'FAIL','closed_total':len(trades),'terminal_open':len(opened),
        'numeric_absolute_tolerance':1e-8,'all_common_fields_compared':True,'open_fields_compared':open_fields,
        'excluded_historical_economics':sorted(excluded),'details':details,'differences':len(diffs)}
    js(output/'CONTROL_REPRODUCTION.json',result)
    assert not diffs and len(trades)==1442,'CONTROL_FAILED_VARIANTS_BLOCKED'


def reports(trades,opened,snapshots,frames,output):
    overall,yearly,direction,monthly,november,equity = [],[],[],[],[],[]
    for version in E.CONFIGS:
        for rule in RULES:
            base = trades.loc[trades.version.eq(version)&trades.rule.eq(rule)]
            for scope in ('ALL_FOUR',*E.SYMBOLS):
                symbols = E.SYMBOLS if scope=='ALL_FOUR' else (scope,)
                f = base.loc[base.instrument.isin(symbols)]
                first = min(frames[s].index[0] for s in symbols).strftime('%Y-%m')
                available = [m for m in CALENDAR if m>=first]
                ids = {'version':version,'rule':rule,'scope':scope}
                os = [o for o in opened if o['version']==version and o['rule']==rule and o['instrument'] in symbols]
                for norm,col in NORMALIZATIONS.items():
                    idn = ids | {'normalization':norm}
                    overall.append(idn | {'first_available_month':first,'covered_calendar_months':len(available),
                        'positive_share_covered_months':sum(f.loc[f.exit_time.dt.strftime('%Y-%m').eq(m),col].sum()>0 for m in available)/len(available)} |
                        metrics(f,CALENDAR,col,len(os)))
                    for year in (2023,2024):
                        y = f.loc[f.exit_time.dt.year.eq(year)]
                        cal = [m for m in CALENDAR if m.startswith(str(year))]
                        oy = [o for o in snapshots if o['version']==version and o['rule']==rule and o['instrument'] in symbols and o['year']==year]
                        yearly.append(idn | {'year':year} | metrics(y,cal,col,len(oy)))
                    for dr in ('LONG','SHORT'):
                        for year in ('ALL',2023,2024):
                            y = f.loc[f.direction.eq(dr)]
                            if year!='ALL':y = y.loc[y.exit_time.dt.year.eq(year)]
                            cal = CALENDAR if year=='ALL' else [m for m in CALENDAR if m.startswith(str(year))]
                            oy = os if year=='ALL' else [o for o in snapshots if o['version']==version and o['rule']==rule and o['instrument'] in symbols and o['year']==year]
                            direction.append(idn | {'year':year,'direction':dr} | metrics(y,cal,col,sum(o['direction']==dr for o in oy)))
                    for m in CALENDAR:
                        y = f.loc[f.exit_time.dt.strftime('%Y-%m').eq(m)]
                        monthly.append(idn | {'month':m,'coverage':'NO_COVERAGE' if m<first else 'AVAILABLE'} | metrics(y,[m],col))
                    for year in ('ALL',2024):
                        y = f if year=='ALL' else f.loc[f.exit_time.dt.year.eq(2024)]
                        n = y.loc[y.exit_time.dt.strftime('%Y-%m').eq('2024-11')]
                        rest = y.loc[~y.exit_time.dt.strftime('%Y-%m').eq('2024-11')]
                        cal = CALENDAR if year=='ALL' else [m for m in CALENDAR if m.startswith('2024')]
                        original = metrics(y,cal,col); removed = metrics(rest,[m for m in cal if m!='2024-11'],col)
                        november.append(idn | {'year':year,'november_closed':len(n),'november_R':float(n[col].sum()),
                            'full_R':original['gross_R'],'full_PF':original['gross_PF'],'ex_november_R':removed['gross_R'],
                            'ex_november_PF':removed['gross_PF'],'ex_november_drawdown_R':removed['max_drawdown_closed_R']})
                if scope=='ALL_FOUR':
                    q = ordered(f)
                    for norm,col in NORMALIZATIONS.items():
                        cum = peak = 0.
                        for r in q.to_dict('records'):
                            cum += r[col];peak = max(peak,cum)
                            equity.append(ids | {'normalization':norm,'exit_time':r['exit_time'],'instrument':r['instrument'],
                                'trade_id':r['trade_id'],'trade_R':r[col],'cumulative_closed_R':cum,'drawdown_R':peak-cum})
    for name,rows in [('overall_report.csv',overall),('yearly_report.csv',yearly),('direction_report.csv',direction),
        ('monthly_report.csv',monthly),('november_dependence.csv',november),('closed_equity.csv',equity),
        ('instrument_report.csv',[r for r in overall if r['scope']!='ALL_FOUR'])]:csv(output/name,rows)


def run(data_root,output,controls_only=False):
    output.mkdir(parents=True,exist_ok=True)
    assert output.resolve().is_relative_to(HERE.resolve())
    assert E.git(data_root,'rev-parse','HEAD')==E.DATA_COMMIT
    specs = json.loads((HERE/'EXPERIMENT_SPECS.json').read_text())
    assert specs['base_main']==MAIN and specs['data_commit']==E.DATA_COMMIT
    assert specs['configurations']=={v:asdict(p) for v,p in E.CONFIGS.items()}
    frames,lows = {},{}
    manifest = {'base_main':MAIN,'data_commit':E.DATA_COMMIT,'labels':LABELS,'future_OHLC_parsed':False,
        'full_file_integrity':'Opaque byte SHA only; parsers stop at timestamp before first 2025+ OHLC.',
        'sources':[],'runtime':{'python':platform.python_version(),'pandas':pd.__version__,'numpy':np.__version__},
        'freeze_commit':E.git(HERE,'log','-1','--format=%H','--','EXPERIMENT_SPECS.json'),
        'spec_sha256':E.sha_file(HERE/'EXPERIMENT_SPECS.json'),
        'implementation_sha256':{p.name:E.sha_file(p) for p in sorted(HERE.glob('*.py'))},
        'reference_sha256':{str(p.relative_to(HERE.parent)):E.sha_file(p) for p in [FROZEN/'engine.py',FROZEN/'trades.csv',FROZEN/'OPEN_POSITIONS.json',HERE.parent/'t3_m15_entry_regime_v1/results/trades_CONTROL.csv',HERE.parent/'ROADMAP.md',HERE.parent/'reports/STAGE1_EXECUTION_COSTS_SPEC.md']}}
    for symbol in E.SYMBOLS:
        relative = f'forever/{symbol}/{symbol}_M15.csv'
        src = E.verify_source(data_root,relative)
        raw, prefix_sha = E.read_prefix(data_root/relative)
        frames[symbol] = E.close_index(raw)
        lows[symbol],_ = features(frames[symbol],E.CONFIGS['BASELINE'])
        src.update(instrument=symbol,historical_prefix_sha256=prefix_sha,used_candles=len(frames[symbol]),
            first_open=raw.index[0].isoformat(),last_open=raw.index[-1].isoformat(),
            first_close=frames[symbol].index[0].isoformat(),last_close=frames[symbol].index[-1].isoformat())
        manifest['sources'].append(src)
    trades,opened,decisions,entries,snapshots = [],[],[],[],[]
    def replay(rule):
        for v,p in E.CONFIGS.items():
            for s in E.SYMBOLS:
                t,o,d,e,y = execute(lows[s],s,v,p,rule)
                trades.extend(t);decisions.extend(d);entries.extend(e);snapshots.extend(y)
                if o:opened.append(o)
    replay('CONTROL')
    control_gate(pd.DataFrame(trades),opened,output)
    csv(output/'control_gross_trades.csv',trades)
    js(output/'CONTROL_OPEN_POSITIONS.json',opened.copy())
    js(output/'SOURCE_MANIFEST.json',manifest)
    if controls_only:
        print(json.dumps({'control':'PASS','closed':len(trades),'open':len(opened)}));return
    assert (HERE/'PRE_VARIANT_GATE.json').exists(),'PRE_VARIANT_TEST_GATE_REQUIRED'
    gate = json.loads((HERE/'PRE_VARIANT_GATE.json').read_text())
    assert gate['control']=='PASS' and gate['tests']=='PASS' and gate['freeze_commit']==manifest['freeze_commit']
    for rule in RULES[1:]:replay(rule)
    f = pd.DataFrame(trades).sort_values(['version','rule','exit_time','instrument','trade_id'],kind='mergesort').reset_index(drop=True)
    csv(output/'trades.csv',f)
    for rule in RULES:csv(output/f'trades_{rule}.csv',f.loc[f.rule.eq(rule)])
    js(output/'OPEN_POSITIONS.json',opened)
    js(output/'YEAR_END_OPEN_POSITIONS.json',snapshots)
    csv(output/'stop_decisions.csv',decisions)
    csv(output/'entry_opportunities.csv',entries)
    reports(f,opened,snapshots,frames,output)
    from diagnostics import diagnostics
    diagnostics(f,opened,pd.DataFrame(entries),output)
    from render_report import render
    render(output)
    js(output/'GENERATED_SHA256.json',{p.name:E.sha_file(p) for p in sorted(output.iterdir()) if p.is_file() and p.name!='GENERATED_SHA256.json'})
    print(json.dumps({'control':'PASS','closed':len(f),'terminal_open':len(opened),'standalone_runs':8},sort_keys=True))

if __name__=='__main__':
    p = argparse.ArgumentParser();p.add_argument('--data-root',type=Path,required=True)
    p.add_argument('--output',type=Path,default=HERE/'results');p.add_argument('--controls-only',action='store_true')
    a=p.parse_args();run(a.data_root,a.output,a.controls_only)
