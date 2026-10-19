"""Reproduce: develop -> tests -> freeze -> evaluate. Inputs stay outside Git."""
from __future__ import annotations
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
import platform
from pathlib import Path
import subprocess
import sys
import numpy as np
import pandas as pd

from . import engine, scalar

HERE = Path(__file__).resolve().parent
ROOT = engine.ROOT
MAIN = '38489db7e69336548a583f968f13aab49c20913b'
DATA_SHA = '888bf47b5030f362f2e83c018a18da6ec9ba49d1d9ded3fceed4293886cfd2a0'
CUTOFF = pd.Timestamp('2025-01-01', tz='Europe/Moscow')
LAST_OPEN = pd.Timestamp('2026-10-19 16:00', tz='Europe/Moscow')
SOURCE_PATHS = [
    'TradingSystemLab/strategies/trend/T3_MTF_Trend.py', 'TradingSystemLab/core/indicators.py',
    'TradingSystemLab/core/data_loader.py',
    *['TradingSystemLab/results/post_v3_analysis/stage5_structural_validation/'+s for s in ('stage5_trail1_lifecycle.py','stage5_trail1_execution.py')],
    *['TradingSystemLab/stage8_robot/'+s+'.py' for s in ('context_builder','strategy_core','trail1_state','production_replay','execution_grid','authority_replay')],
]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def jsonable(value):
    if isinstance(value, dict): return {str(k):jsonable(v) for k,v in value.items()}
    if isinstance(value, (list,tuple)): return [jsonable(v) for v in value]
    if isinstance(value, (pd.Timestamp,datetime)): return value.isoformat()
    if isinstance(value, np.generic): return jsonable(value.item())
    if isinstance(value,float) and not np.isfinite(value): return None
    return value


def write_json(path, value):
    Path(path).write_text(json.dumps(jsonable(value), ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)+'\n')


def write_csv(path, frame):
    frame.to_csv(path,index=False,lineterminator='\n',float_format='%.12g',na_rep='')


def setup_hashes():
    paths = sorted(HERE.glob('*.py')) + [HERE/'PROTOCOL_RU.md',HERE/'requirements.txt']
    return {str(p.relative_to(ROOT)):sha(p) for p in paths}


def authenticate():
    checks = {}
    specdir = engine.SPEC_DIR
    manifest = json.loads((specdir/'audit_manifest.json').read_text())
    for name, digest in manifest['core_artifacts'].items():
        assert sha(specdir/name) == digest, name
        checks[str((specdir/name).relative_to(ROOT))] = digest
    provenance = json.loads((specdir/'source_provenance.json').read_text())
    for v in provenance.values():
        if isinstance(v,dict) and 'path' in v:
            assert sha(ROOT/v['path']) == v['sha256'], v['path']
            checks[v['path']] = v['sha256']
    for name in SOURCE_PATHS:
        checks[name] = sha(ROOT/name)
    assert engine.PARAMETERS['stop_atr'] == 2.5
    assert engine.SPEC['strategy']['configuration_id'] == 'T3-H1-4e73cdb77246'
    # Verify the isolated branch was based on the observed main, without relying on mutable HEAD.
    subprocess.run(['git','merge-base','--is-ancestor',MAIN,'HEAD'],cwd=ROOT,check=True)
    return checks


def load(path, heldout):
    path = Path(path).resolve()
    if path.is_relative_to(ROOT): raise ValueError('RAW_DATA_MUST_BE_OUTSIDE_REPOSITORY')
    if sha(path) != DATA_SHA: raise ValueError('DATA_SHA256_MISMATCH')
    rows = []
    with path.open(encoding='utf-8-sig',newline='') as f:
        reader = csv.DictReader(f,delimiter=';')
        assert reader.fieldnames == ['Datetime','Open','High','Low','Close','Volume']
        for row in reader:
            # Only timestamp prefix is inspected at the boundary; no held-out OHLCV is converted in development.
            if not heldout and row['Datetime'][:4] >= '2025': break
            rows.append(row)
    frame = pd.DataFrame(rows)
    index = pd.DatetimeIndex(pd.to_datetime(frame.pop('Datetime'),format='%Y-%m-%d %H:%M:%S')).tz_localize('Europe/Moscow',ambiguous='raise',nonexistent='raise')
    frame = frame.apply(pd.to_numeric,errors='raise')
    frame.index = index
    if heldout:
        assert len(frame)==46751 and index[-1]==LAST_OPEN
    assert not index.has_duplicates and index.is_monotonic_increasing
    assert np.isfinite(frame.to_numpy()).all() and (frame[['Open','High','Low','Close']]>0).all().all()
    assert (frame.High >= frame[['Open','Close','Low']].max(axis=1)).all()
    assert (frame.Low <= frame[['Open','Close','High']].min(axis=1)).all()
    assert (frame.Volume >= 0).all()
    assert (index.minute == 0).all() and (index.second == 0).all()
    excluded = frame.loc[frame.index >= LAST_OPEN]
    usable = frame.loc[frame.index < LAST_OPEN]
    return frame, engine.DataLoader.close_index(usable), excluded


def audit_data(raw, closed, excluded, out):
    delta = raw.index.to_series().diff().dt.total_seconds()/3600
    gap = raw.Open/raw.Close.shift(1)-1
    details = pd.DataFrame({'time':raw.index,'elapsed_hours':delta.to_numpy(),'open_vs_previous_close_pct':gap.to_numpy()*100})
    write_csv(out/'extreme_gaps.csv',details.loc[(delta.to_numpy()>72)|(gap.abs().to_numpy()>.05)])
    rows = []
    for year,g in raw.groupby(raw.index.year):
        groups = []
        c = closed[closed.index.year == year]
        for _,day in c.groupby(c.index.normalize()):
            for start in range(0,len(day)-3,4): groups.append(day.index[start:start+4])
        prices = g[['Open','High','Low','Close']].to_numpy().ravel()
        offgrid = int((np.abs(prices/.01 - np.round(prices/.01))>1e-6).sum())
        rows.append({'year':year,'bars':len(g),'days':len(set(g.index.date)), 'first_open':g.index[0],'last_open':g.index[-1],
                     'zero_volume':int(g.Volume.eq(0).sum()),'flat_bars':int(g.High.eq(g.Low).sum()),
                     'min_open_hour':int(g.index.hour.min()),'max_open_hour':int(g.index.hour.max()),
                     'ohlc_off_assumed_001_grid':offgrid,'h4_blocks':len(groups),
                     'h4_blocks_with_time_gap':sum(any((b-a)!=pd.Timedelta(hours=1) for a,b in zip(x,x[1:])) for x in groups),
                     'midnight_close_bars':int((c.index.hour==0).sum())})
    write_csv(out/'data_yearly.csv',pd.DataFrame(rows))
    hours = pd.DataFrame({'year':raw.index.year,'open_hour':raw.index.hour}).value_counts().rename('bars').reset_index().sort_values(['year','open_hour'])
    write_csv(out/'session_hours.csv',hours)
    flat=raw.loc[raw.High.eq(raw.Low)]
    flat_hours=pd.DataFrame({'year':flat.index.year,'open_hour':flat.index.hour}).value_counts().rename('flat_bars').reset_index().sort_values(['year','open_hour'])
    write_csv(out/'flat_bars_by_hour.csv',flat_hours)
    range_pct=100*(raw.High-raw.Low)/raw.Close.shift(1)
    close_change=100*raw.Close.pct_change()
    extremes=pd.DataFrame({'time':raw.index,'range_pct_previous_close':range_pct.to_numpy(),'close_change_pct':close_change.to_numpy()})
    write_csv(out/'price_extremes.csv',extremes.loc[(range_pct.to_numpy()>10)|(close_change.abs().to_numpy()>10)])
    audit = {'main_sha':MAIN,'source_sha256':DATA_SHA,'raw_rows':len(raw),'usable_rows':len(closed),
             'first_open':raw.index[0],'last_source_open':raw.index[-1],'last_authorized_close':closed.index[-1],
             'excluded_potentially_incomplete_rows':len(excluded),'duplicate_timestamps':0,'null_or_nonfinite_ohlcv':0,
             'invalid_ohlc':0,'zero_volume':int(raw.Volume.eq(0).sum()),'flat_bars':int(raw.High.eq(raw.Low).sum()),
             'gaps_over_72h':int((delta>72).sum()),'gaps_over_5pct':int((gap.abs()>.05).sum()),
             'max_elapsed_hours':float(delta.max()),'timestamp_basis':'NAIVE_MOSCOW_OPEN_ASSUMED_CONSISTENT_NOT_INDEPENDENTLY_AUTHENTICATED',
             'price_adjustment':'UNKNOWN; treated as raw/unadjusted; no dividend income or corporate-action adjustment'}
    write_json(out/'data_audit.json',audit)
    return audit


def metrics(g):
    def pf(x):
        positive, negative = float(x[x>0].sum()),float(-x[x<0].sum())
        return positive/negative if negative else None
    x = g.net_R if len(g) else pd.Series(dtype=float)
    gross = g.gross_R if len(g) else x
    curve = np.r_[0.,x.cumsum().to_numpy()]
    winners,losers = x[x>0],x[x<0]
    positive = float(winners.sum())
    ordered = winners.sort_values(ascending=False)
    return {'trades':len(g),'gross_PF':pf(gross),'net_PF':pf(x),'gross_R':float(gross.sum()),'cost_R':float(g.cost_R.sum()) if len(g) else 0.,
            'net_R':float(x.sum()),'expectancy_R':float(x.mean()) if len(x) else None,
            'avg_winner_R':float(winners.mean()) if len(winners) else None,'avg_loser_R':float(losers.mean()) if len(losers) else None,
            'win_rate':float((x>0).mean()) if len(x) else None,'max_closed_R_DD':float((curve-np.maximum.accumulate(curve)).min()),
            'top1_share_positive_R':float(ordered.head(1).sum()/positive) if positive else None,
            'top5_share_positive_R':float(ordered.head(5).sum()/positive) if positive else None,
            'top10_share_positive_R':float(ordered.head(10).sum()/positive) if positive else None,
            'net_R_without_top5':float(x.sum()-ordered.head(5).sum()),
            'gap_exits':int(g.gap_through_stop.sum()) if len(g) and 'gap_through_stop' in g else None}


def tables(trades,frame,out):
    summary,annual,monthly,quarterly,directions,cohorts = [],[],[],[],[],[]
    start,end = frame.index[0].tz_localize(None),frame.index[-1].tz_localize(None)
    for scenario,g in trades.groupby('scenario',sort=True):
        g = g.sort_values(['exit_time','trade_id'],kind='stable')
        dates = pd.DatetimeIndex(g.exit_time)
        for label,mask in [('FULL',np.ones(len(g),dtype=bool)),('2011_2024',dates<CUTOFF),('2025_2026',dates>=CUTOFF)]:
            summary.append({'scenario':scenario,'period':label,**metrics(g[mask])})
        for frequency,destination,key in [('Y',annual,'year'),('M',monthly,'month'),('Q',quarterly,'quarter')]:
            labels = dates.tz_localize(None).to_period(frequency).astype(str)
            for label in pd.period_range(start,end,freq=frequency).astype(str):
                partial = label == str(start.to_period(frequency)) or label == str(end.to_period(frequency))
                destination.append({'scenario':scenario,key:label,'boundary_period':partial,**metrics(g[labels==label])})
        for d in ('LONG','SHORT'):
            directions.append({'scenario':scenario,'direction':d,**metrics(g[g.direction==d])})
        entries=pd.DatetimeIndex(g.entry_time)
        for label,mask in [('ENTRY_BEFORE_2025',entries<CUTOFF),('ENTRY_2025_PLUS',entries>=CUTOFF)]:
            cohorts.append({'scenario':scenario,'cohort':label,**metrics(g[mask])})
    for name,rows in [('summary',summary),('annual',annual),('monthly',monthly),('quarterly',quarterly),('directions',directions),('entry_cohorts',cohorts)]:
        write_csv(out/(name+'.csv'),pd.DataFrame(rows))
    return summary


def compare(a,b,label):
    """Every shared semantic column, in event order. Preserve all discrepancies."""
    columns = ['direction','entry_time','entry_price','initial_stop_price','initial_risk_price','exit_time','exit_price',
               'gross_R','cost_R','net_R','trail1_triggered','trigger_bar_time','stored_trail_candidate',
               'trail1_activation_time','trail1_activated','bars_held']
    errors=[]
    if len(a)!=len(b): errors.append({'column':'row_count','primary':len(a),'other':len(b)})
    maxima={}
    for col in columns:
        if col not in a or col not in b:
            errors.append({'column':col,'error':'MISSING_COLUMN'}); continue
        maximum=0.
        for i,(x,y) in enumerate(zip(a[col],b[col])):
            if pd.isna(x) and pd.isna(y): continue
            if col.endswith('time'):
                equal=pd.Timestamp(x)==pd.Timestamp(y)
            elif isinstance(x,(float,int,np.number)) and not isinstance(x,(bool,np.bool_)):
                delta=abs(float(x)-float(y)); maximum=max(maximum,delta)
                equal=np.isfinite(delta) and delta<=1e-9
            else: equal=x==y
            if not equal: errors.append({'row':i,'column':col,'primary':str(x),'other':str(y)})
        maxima[col]=maximum
    return {'label':label,'status':'FAIL' if errors else 'PASS','primary_rows':len(a),'other_rows':len(b),
            'maximum_numeric_deltas':maxima,'mismatches':errors,'tolerance':1e-9}


def calculate(frame,out):
    out.mkdir(parents=True,exist_ok=True)
    prepared=engine.features(frame)
    scalar_prepared=scalar.features(frame)
    feature_checks=[]
    for a,b in zip(prepared,scalar_prepared):
        assert a.index.equals(b.index)
        for col in b.columns:
            if col in a:
                diff=(a[col]-b[col]).abs()
                feature_checks.append({'column':col,'maximum_delta':float(diff.max()),
                                       'missing_mask_equal':a[col].isna().equals(b[col].isna()),
                                       'status':'PASS' if a[col].isna().equals(b[col].isna()) and (diff.dropna()<=1e-9).all() else 'FAIL'})
    frames,opens,checks,determinism=[],[],[],[]
    for name,cfg in engine.SCENARIOS.items():
        a,trace,opened=engine.run(frame,name,prepared)
        second,trace2,opened2=engine.run(frame,name,prepared)
        path=out/(name+'_trades.csv'); write_csv(path,a)
        second_bytes=second.to_csv(index=False,lineterminator='\n',float_format='%.12g',na_rep='').encode()
        repeat_sha=hashlib.sha256(second_bytes).hexdigest()
        determinism.append({'scenario':name,'run1_sha256':sha(path),'run2_sha256':repeat_sha,
                            'status':'PASS' if sha(path)==repeat_sha and trace.equals(trace2) and opened==opened2 else 'FAIL'})
        b,other_open=scalar.run(frame,long_only=cfg['long_only'],grid=cfg['grid'],cost_price=cfg['cost_price'],prepared=scalar_prepared)
        checks.append(compare(a,b,'SCALAR_'+name))
        # Open positions are checked separately; neither ledger fabricates a final exit.
        open_error=[]
        if (opened is None)!=(other_open is None): open_error.append('presence')
        if opened is not None and other_open is not None:
            for k,j in [('direction','direction'),('entry_time','entry_time'),('entry_price','entry_price'),('initial_risk_price','risk'),('stop','stop')]:
                x,y=opened[k],other_open[j]
                if isinstance(x,(float,int)):
                    if abs(x-y)>1e-9:open_error.append(k)
                elif x!=y:open_error.append(k)
        checks.append({'label':'SCALAR_OPEN_'+name,'status':'FAIL' if open_error else 'PASS','mismatches':open_error})
        write_csv(out/(name+'_trace.csv'),trace)
        frames.append(a)
        if opened: opens.append(opened)
    # Unmodified native research and production engines run on the identical completed data.
    from TradingSystemLab.stage8_robot.authority_replay import replay_authority
    from TradingSystemLab.stage8_robot.production_replay import replay_production
    baseline=frames[0]
    for label,runner in [('NATIVE_AUTHORITY',replay_authority),('NATIVE_PRODUCTION',replay_production)]:
        native=pd.DataFrame(runner(frame,'SBER',{'instrument':'SBER','lifecycle':'external_transfer','fold_id':''})).rename(columns={'net_R_C1':'net_R'})
        checks.append(compare(baseline,native,label))
    all_trades=pd.concat(frames,ignore_index=True)
    write_csv(out/'all_trades.csv',all_trades)
    write_json(out/'open_positions.json',opens)
    summary=tables(all_trades,frame,out)
    status='PASS' if all(c['status']=='PASS' for c in checks+feature_checks+determinism) else 'FAIL'
    audit={'main_sha':MAIN,'status':status,'checks':checks,'features':feature_checks,'determinism':determinism,
           'independence_limit':'Scalar arithmetic/lifecycle implemented separately by the same agent; not an external human or separate-agent audit.'}
    write_json(out/'audit.json',audit)
    return audit,summary


def freeze(dev,tests):
    audit=json.loads((dev/'audit.json').read_text())
    assert audit['status']=='PASS'
    log=Path(tests).read_text()
    assert 'passed' in log and 'failed' not in log and 'error' not in log.lower()
    frozen={'main_sha':MAIN,'source_sha256':DATA_SHA,'utc_time':datetime.now(timezone.utc),'setup_hashes':setup_hashes(),
            'source_hashes':authenticate(),'development_audit_sha256':sha(dev/'audit.json'),'test_log_sha256':sha(tests),
            'development_ledger_sha256':sha(dev/'all_trades.csv'),'scenarios':engine.SCENARIOS,'parameters':engine.PARAMETERS,
            'heldout_price_access_before_freeze':False,'heldout_evaluation_policy':'one frozen evaluation, second run is deterministic verification only'}
    target=HERE/'FREEZE.json'
    if target.exists(): raise RuntimeError('FREEZE_ALREADY_EXISTS')
    write_json(target,frozen)
    print('FROZEN',sha(target))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('stage',choices=['develop','freeze','evaluate'])
    p.add_argument('--data',type=Path)
    p.add_argument('--out',type=Path,default=HERE/'results')
    p.add_argument('--tests',type=Path)
    a=p.parse_args()
    if a.stage=='freeze': freeze(a.out,a.tests);return
    source_hashes=authenticate()
    heldout=a.stage=='evaluate'
    if heldout:
        f=json.loads((HERE/'FREEZE.json').read_text())
        assert f['setup_hashes']==setup_hashes(),'SETUP_CHANGED_AFTER_FREEZE'
        assert f['source_hashes']==source_hashes,'SOURCE_CHANGED_AFTER_FREEZE'
        a.out.mkdir(parents=True,exist_ok=True)
        gate=a.out/'EVALUATION_ACCESS.json'
        if gate.exists(): raise RuntimeError('HELDOUT_EVALUATION_ALREADY_STARTED; use recorded results')
        write_json(gate,{'main_sha':MAIN,'utc_time':datetime.now(timezone.utc),'freeze_sha256':sha(HERE/'FREEZE.json'),
                         'mode':'SINGLE_EVALUATION_WITH_DETERMINISTIC_REPLAY','source_sha256':DATA_SHA})
    raw,frame,excluded=load(a.data,heldout)
    a.out.mkdir(parents=True,exist_ok=True)
    data_audit=audit_data(raw,frame,excluded,a.out)  # Always before any backtest in the interval.
    write_json(a.out/'source_manifest.json',{'main_sha':MAIN,'source_sha256':DATA_SHA,'source_hashes':source_hashes,
        'setup_hashes':setup_hashes(),'python':platform.python_version(),'pandas':pd.__version__,'numpy':np.__version__,
        'authority':'Frozen Stage5 run_t3 + T3_H1_candidate_v3; native production replay is the second canonical comparator',
        'cost_contract':'C1=.002 price units round trip, normalized benchmark only; stock diagnostic=.02 RUB, not verified broker fees'})
    audit,summary=calculate(frame,a.out)
    if heldout:
        prior=pd.read_csv(HERE/'results/development/all_trades.csv')
        full=pd.read_csv(a.out/'all_trades.csv')
        prior_exit=pd.to_datetime(full.exit_time,utc=True)<CUTOFF.tz_convert('UTC')
        prefix=full[prior_exit].reset_index(drop=True)
        # Mixed historical UTC offsets: compare using UTC, never parse as one local fixed offset.
        prefix_check=compare(prior,prefix,'DEVELOPMENT_PREFIX_INVARIANCE')
        write_json(a.out/'prefix_invariance.json',prefix_check)
        assert prefix_check['status']=='PASS'
    print(json.dumps(jsonable({'stage':a.stage,'status':audit['status'],'data_audit':data_audit,'summary':summary}),ensure_ascii=False))
    if audit['status']!='PASS': sys.exit(1)


if __name__=='__main__':main()
