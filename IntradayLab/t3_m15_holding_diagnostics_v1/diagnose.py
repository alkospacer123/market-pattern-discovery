"""Read-only diagnostics of frozen PR #490 records; no alternative trades/exits."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys
import platform
from dataclasses import asdict

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
FROZEN = HERE.parent / 't3_m15_forever_v1'
MAIN = 'd963b783b9de31fc0f2c965f6dfb11ab9cd90f5b'

def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m

E = module('frozen_engine_read_only', FROZEN/'engine.py')
KEY = ['version', 'instrument', 'trade_id']

def js(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False)+'\n')

def csv(path, rows):
    pd.DataFrame(rows).to_csv(path, index=False, float_format='%.15g', lineterminator='\n')

def bucket(minutes):
    return ('01_0_to_60m' if minutes <= 60 else '02_60_to_240m' if minutes <= 240 else
            '03_240_to_480m' if minutes <= 480 else '04_480_to_1440m' if minutes <= 1440 else '05_over_1440m')

def path_for_trade(t, low, high, p, opened=False):
    """Trace the original carried-stop recurrence. Stop-bar chronology is bounded."""
    at = pd.Timestamp(t['entry_time'])
    end = pd.Timestamp(t['last_close'] if opened else t['exit_time'])
    i, j = low.index.get_loc(at), low.index.get_loc(end)
    s = 1 if t['direction']=='LONG' else -1
    entry = float(t['entry_price'])
    stop = float(t['initial_stop'])
    risk = abs(entry-stop)
    extreme, mfe, mae, updates = entry, 0., 0., 0
    h = high.loc[:at].iloc[-1]
    b = low.iloc[i]
    level = float(b.PriorHigh if s==1 else b.PriorLow)
    info = {**t, 'record_status':'OPEN_TERMINAL' if opened else 'CLOSED',
        'signal_time':at.isoformat(), 'h1_available_at':h.name.isoformat(),
        'h1_age_minutes':(at-h.name).total_seconds()/60,
        'breakout_level':level, 'breakout_penetration_R':s*(entry-level)/risk,
        'signal_body_R':s*(b.Close-b.Open)/risk, 'signal_range_R':(b.High-b.Low)/risk,
        'entry_M15_ATR':float(b.ATR), 'entry_H1_ATR':float(h.ATR),
        'entry_H1_ATRMean':float(h.ATRMean), 'entry_H1_ATR_ratio':float(h.ATR/h.ATRMean),
        'entry_H1_EMA':float(h.EMA), 'entry_H1_slope':float(h.Slope),
        'entry_H1_ADX':float(h.ADX), 'entry_H1_close':float(h.Close),
        'entry_H1_ema_distance_R':s*(h.Close-h.EMA)/risk,
        'entry_H1_slope_R':s*h.Slope/risk, 'entry_H1_trend':int(b.Regime)}
    assert h.name <= at and int(b.Signal)==s
    trace=[{**{k:t[k] for k in KEY}, 'record_status':info['record_status'],
        'bar_number':0,'available_at':at.isoformat(),'event':'ENTRY',
        'stop_before':stop,'stop_after':stop,'stop_before_R':-1.,'stop_after_R':-1.,
        'MFE_recorded_so_far_R':0.,'MAE_recorded_so_far_R':0.,
        'ATR_current_to_entry_ratio':1.,'trail_distance_R':None,'proposed_stop':None,
        'stop_updated':False,'tightened_without_new_extreme':False,
        'close_through_new_stop':False,'gap_exit':False,'exit_at_open':False}]
    first_lock, peak_bar, exit_lower, exit_upper = None,0,0.,0.
    for k in range(i+1,j+1):
        b = low.iloc[k]
        n=k-i
        active=stop
        hit = b.Low<=active if s==1 else b.High>=active
        assert hit == (not opened and k==j), (t['trade_id'],n,hit)
        gap=False; at_open=False; proposed=None; tightened=False; through=False; new_extreme=False
        if hit:
            fill=min(b.Open,active) if s==1 else max(b.Open,active)
            gap=fill!=active
            at_open=s*(b.Open-active)<=0
            gross=s*(fill-entry)/risk
            exit_lower=max(mfe,0.,s*(b.Open-entry)/risk,gross)
            exit_upper=exit_lower if at_open else max(exit_lower, s*((b.High if s==1 else b.Low)-entry)/risk)
            mae=max(mae,0.,-gross)
            assert abs(fill-float(t['exit_price']))<1e-8
            assert abs(mfe-float(t['MFE_R']))<1e-8
            assert abs(mae-float(t['MAE_R']))<1e-8
            assert abs(active-float(t['active_stop_at_exit']))<1e-8
            assert updates==int(t['trailing_updates'])
        else:
            favorable=max(0.,s*((b.High if s==1 else b.Low)-entry)/risk)
            adverse=max(0.,s*(entry-(b.Low if s==1 else b.High))/risk)
            if favorable>mfe: peak_bar=n
            mfe=max(mfe,favorable);mae=max(mae,adverse)
            old_extreme=extreme
            extreme=max(extreme,b.High) if s==1 else min(extreme,b.Low)
            new_extreme=extreme!=old_extreme
            proposed=extreme-s*p.trail_atr*b.ATR
            stop=max(active,proposed) if s==1 else min(active,proposed)
            tightened=stop!=active
            updates+=int(tightened)
            if first_lock is None and s*(stop-entry)>0: first_lock=n
            through=s*(b.Close-stop)<=0
        trace.append({**{key:t[key] for key in KEY},'record_status':info['record_status'],
            'bar_number':n,'available_at':b.name.isoformat(),'event':'EXIT' if hit else 'SURVIVED',
            'stop_before':active,'stop_after':stop,'stop_before_R':s*(active-entry)/risk,
            'stop_after_R':s*(stop-entry)/risk,'MFE_recorded_so_far_R':mfe,
            'MAE_recorded_so_far_R':mae,'ATR_current_to_entry_ratio':float(b.ATR/low.iloc[i].ATR),
            'trail_distance_R':float(p.trail_atr*b.ATR/risk) if not hit else None,
            'proposed_stop':float(proposed) if proposed is not None else None,
            'stop_updated':bool(tightened),'tightened_without_new_extreme':bool(tightened and not new_extreme),
            'close_through_new_stop':bool(through),'gap_exit':bool(gap),'exit_at_open':bool(at_open)})
    info.update({'stop_updates_rebuilt':updates,'first_positive_stop_bar':first_lock,
        'peak_MFE_bar':peak_bar,'bars_after_peak_MFE':j-i-peak_bar,
        'tightenings_without_new_extreme':sum(x['tightened_without_new_extreme'] for x in trace),
        'close_through_new_stop_bars':sum(x['close_through_new_stop'] for x in trace),
        'recorded_MFE_R':mfe,'observed_MFE_lower_R':mfe if opened else exit_lower,
        'possible_MFE_upper_R':mfe if opened else exit_upper,
        'exit_stop_R':s*(stop-entry)/risk})
    if not opened:
        sequence=low.index[i:j+1]
        night_gaps=sum((b-a).total_seconds()>900 and (b-pd.Timedelta(minutes=15)).date()!=(a-pd.Timedelta(nanoseconds=1)).date() for a,b in zip(sequence,sequence[1:]))
        carry_kind=('SAME_DATE_WITH_NONTRADING_NIGHT_GAP' if night_gaps else 'SAME_DAY') if end.date()==at.date() else 'CROSSED_NONTRADING_NIGHT_GAP' if night_gaps else 'MIDNIGHT_OR_CONTINUOUS_CROSS_ONLY'
        info.update({'outcome':'WIN' if float(t['net_R'])>0 else 'LOSS' if float(t['net_R'])<0 else 'FLAT',
            'year':end.year,'month':end.strftime('%Y-%m'),'entry_year':at.year,'entry_hour':at.hour,
            'exit_at_midnight':bool(end.hour==0 and end.minute==0),
            'night_nontrading_gaps':int(night_gaps),'carry_kind':carry_kind,
            'carry':'CROSS_MIDNIGHT' if end.date()!=at.date() else 'SAME_DAY',
            'calendar_midnights':(end.date()-at.date()).days,
            'holding_bucket':bucket(float(t['holding_minutes'])),
            'bar_bucket':'01_1_to_4' if j-i<=4 else '02_5_to_16' if j-i<=16 else '03_17_to_32' if j-i<=32 else '04_over_32',
            'giveback_recorded_R':mfe-float(t['gross_R']),
            'no_favorable_confirmed':bool(exit_upper<=1e-12),
            'no_favorable_unresolved':bool(exit_lower<=1e-12 and exit_upper>1e-12),
            'exit_at_open':bool(at_open),
            'C1_flipped_gross_profit':bool(float(t['gross_R'])>0 and float(t['net_R'])<=0),
            'additional_1bp_R':entry/risk/10000,
            'exposure_entry_notional_hours_R':entry/risk*(end-at).total_seconds()/3600})
    candles=[]
    for n in (1,2,4):
        available=i+n<len(low)
        row={**{key:t[key] for key in KEY},'record_status':info['record_status'],'horizon_bar':n,
            'available':available,'completed_before_exit':bool(available and i+n<j),
            'exit_on_horizon_bar':bool(available and i+n==j and not opened),
            'year':end.year,'outcome':info.get('outcome','UNRESOLVED'),'carry':info.get('carry','UNRESOLVED')}
        if available:
            b=low.iloc[i+n];w=low.iloc[i+1:i+n+1]
            row.update({'available_at':b.name.isoformat(),'elapsed_minutes':(b.name-at).total_seconds()/60,
                'close_move_R':s*(b.Close-entry)/risk,
                'bar_favorable_R':max(0.,s*((b.High if s==1 else b.Low)-entry)/risk),
                'bar_adverse_R':max(0.,s*(entry-(b.Low if s==1 else b.High))/risk),
                'cumulative_favorable_R':max(0.,s*((w.High.max() if s==1 else w.Low.min())-entry)/risk),
                'cumulative_adverse_R':max(0.,s*(entry-(w.Low.min() if s==1 else w.High.max()))/risk),
                'close_beyond_breakout':bool(s*(b.Close-level)>0),
                'wick_back_through_breakout':bool(s*((b.Low if s==1 else b.High)-level)<=0),
                'any_close_back_by_horizon':bool((s*(w.Close-level)<=0).any()),
                'close_continuation':bool(s*(b.Close-entry)>0)})
        candles.append(row)
    return info, trace, candles


def metrics(f):
    f=f.sort_values(['exit_time','instrument','trade_id'],kind='stable')
    n=len(f);v=f.net_R.to_numpy(float)
    pos=v[v>0].sum();neg=-v[v<0].sum();eq=np.r_[0.,v.cumsum()]
    wins=np.sort(v[v>0])[::-1];top=wins[:5].sum()
    loss=f.net_R<0
    out={'trades':n,'wins':int((v>0).sum()),'losses':int((v<0).sum()),
        'PF_net_C1':pos/neg if neg else np.nan,
        'PF_gross':f.loc[f.gross_R>0,'gross_R'].sum()/-f.loc[f.gross_R<0,'gross_R'].sum() if (f.gross_R<0).any() else np.nan,
        'gross_R':f.gross_R.sum(),'C1_R':f.C1_R.sum(),'net_R':v.sum(),
        'mean_net_R':v.mean() if n else np.nan,'max_closed_trade_drawdown_R':(np.maximum.accumulate(eq)-eq).max(),
        'mean_MAE_R':f.MAE_R.mean(),'median_MAE_R':f.MAE_R.median(),
        'mean_MFE_R':f.MFE_R.mean(),'median_MFE_R':f.MFE_R.median(),
        'mean_holding_minutes':f.holding_minutes.mean(),'median_holding_minutes':f.holding_minutes.median(),
        'mean_bars_held':f.bars_held.mean(),'top1_positive_net_R':wins[:1].sum(),'top5_positive_net_R':top,
        'top5_share_positive_R':top/pos if pos else np.nan,'net_R_without_top5_winners':v.sum()-top,
        'initial_stop_exits':int((f.exit_type=='INITIAL_STOP').sum()),'gap_exits':int(f.gap_exit.sum()),
        'loss_recorded_MFE_zero':int((loss & (f.MFE_R<=1e-12)).sum()),
        'loss_no_favorable_confirmed':int((loss & f.no_favorable_confirmed).sum()),
        'loss_no_favorable_unresolved':int((loss & f.no_favorable_unresolved).sum()),
        'loss_recorded_MFE_lt_0_5':int((loss & (f.MFE_R<.5)).sum()),
        'loss_recorded_MFE_ge_1':int((loss & (f.MFE_R>=1)).sum()),
        'loss_recorded_MFE_ge_2':int((loss & (f.MFE_R>=2)).sum()),
        'gross_loss_recorded_MFE_ge_1':int(((f.gross_R<0) & (f.MFE_R>=1)).sum()),
        'gross_loss_recorded_MFE_ge_2':int(((f.gross_R<0) & (f.MFE_R>=2)).sum()),
        'loss_confirmed_MFE_ge_1':int((loss & (f.observed_MFE_lower_R>=1)).sum()),
        'loss_possible_MFE_ge_1':int((loss & (f.possible_MFE_upper_R>=1)).sum()),
        'loss_confirmed_MFE_ge_2':int((loss & (f.observed_MFE_lower_R>=2)).sum()),
        'loss_possible_MFE_ge_2':int((loss & (f.possible_MFE_upper_R>=2)).sum()),
        'net_R_loss_MFE_lt_0_5':f.loc[loss & (f.MFE_R<.5),'net_R'].sum(),
        'net_R_loss_MFE_0_5_to_1':f.loc[loss & (f.MFE_R>=.5) & (f.MFE_R<1),'net_R'].sum(),
        'net_R_loss_MFE_ge_1':f.loc[loss & (f.MFE_R>=1),'net_R'].sum(),
        'C1_flipped_gross_profit':int(f.C1_flipped_gross_profit.sum()),
        'mean_giveback_R':f.giveback_recorded_R.mean(),'median_giveback_R':f.giveback_recorded_R.median(),
        'mean_bars_after_peak_MFE':f.bars_after_peak_MFE.mean(),
        'mean_exit_stop_R':f.exit_stop_R.mean(),'mean_trailing_updates':f.trailing_updates.mean(),
        'tightenings_without_new_extreme':int(f.tightenings_without_new_extreme.sum()),
        'close_through_new_stop_bars':int(f.close_through_new_stop_bars.sum()),
        'extra_cost_break_even_R_per_trade':v.mean() if n else np.nan,
        'extra_cost_break_even_bps_entry_notional':v.sum()/f.additional_1bp_R.sum() if n else np.nan,
        'extra_drag_break_even_bps_per_24h':v.sum()/f.exposure_entry_notional_hours_R.sum()*240000 if n else np.nan}
    return out


def grouped(f, dims):
    rows=[]
    for keys,g in f.groupby(dims,sort=True,dropna=False):
        if not isinstance(keys,tuple):keys=(keys,)
        rows.append(dict(zip(dims,keys))|metrics(g))
    return rows


def main(data_root, output):
    assert output.resolve().is_relative_to(HERE.resolve()),'ALL_OUTPUTS_MUST_STAY_IN_NEW_DIRECTORY'
    output.mkdir(parents=True,exist_ok=True)
    source=json.loads((FROZEN/'SOURCE_MANIFEST.json').read_text())
    configs=json.loads((FROZEN/'BASELINE_CONFIGS.json').read_text())['fixed_control_versions']
    assert E.git(HERE.parent.parent,'rev-parse',f'{MAIN}:IntradayLab/t3_m15_forever_v1/trades.csv')==E.git(HERE.parent.parent,'hash-object',str(FROZEN/'trades.csv'))
    for name in E.SYMBOLS: assert name in E.UNITS
    frozen=pd.read_csv(FROZEN/'trades.csv')
    for col in ['entry_time','exit_time']:frozen[col]=pd.to_datetime(frozen[col]).dt.tz_convert(E.TZ)
    opens=json.loads((FROZEN/'OPEN_POSITIONS.json').read_text())
    infos=[];traces=[];candles=[];open_infos=[];records=[]
    for src in source['sources']:
        verified=E.verify_source(data_root,src['path'])
        assert verified['full_sha256']==src['full_sha256']
        raw,prefix=E.read_prefix(data_root/src['path'])
        assert prefix==src['historical_prefix_sha256']
        low,high=E.indicators(E.close_index(raw),E.CONFIGS['BASELINE'])
        for version,p in E.CONFIGS.items():
            assert asdict(p)==configs[version]['parameters']
            subset=frozen[(frozen.instrument==src['instrument']) & (frozen.version==version)]
            replay,residual=E.execute(low,src['instrument'],version,p,E.UNITS[src['instrument']])
            assert len(replay)==len(subset)
            max_delta=0.
            for a,b in zip(replay.to_dict('records'),subset.to_dict('records')):
                for col in a:
                    if isinstance(a[col],(float,int,np.number)):
                        d=abs(float(a[col])-float(b[col]));max_delta=max(max_delta,d);assert d<1e-8,(col,d)
                    else:assert a[col]==b[col],col
                info,path,early=path_for_trade(b,low,high,p)
                infos.append(info);traces.extend(path);candles.extend(early)
            for t in opens:
                if t['version']==version and t['instrument']==src['instrument']:
                    t=t|{'trade_id':'OPEN_TERMINAL'}
                    info,path,early=path_for_trade(t,low,high,p,True)
                    assert residual is not None and abs(info['exit_stop_R']-(1 if t['direction']=='LONG' else -1)*(t['active_stop']-t['entry_price'])/t['initial_risk'])<1e-8
                    open_infos.append(info);traces.extend(path);candles.extend(early)
            records.append({'version':version,'instrument':src['instrument'],'trades':len(subset),'maximum_replay_delta':max_delta})
    f=pd.DataFrame(infos);c=pd.DataFrame(candles)
    csv(output/'trade_diagnostics.csv',f)
    csv(output/'stop_trajectory.csv',traces)
    csv(output/'first_candles.csv',c)
    js(output/'open_position_diagnostics.json',open_infos)
    reports={
        'instrument_year.csv':['version','instrument','year'],
        'holding_by_year.csv':['version','instrument','year','holding_bucket'],
        'holding_by_direction.csv':['version','instrument','year','direction','holding_bucket'],
        'holding_by_bars.csv':['version','instrument','year','bar_bucket'],
        'carry_by_year.csv':['version','instrument','year','carry'],
        'carry_by_direction.csv':['version','instrument','year','direction','carry'],
        'holding_carry_direction.csv':['version','instrument','year','direction','carry','holding_bucket'],
        'monthly.csv':['version','instrument','month'],
        'carry_kind.csv':['version','instrument','year','carry_kind'],
        'entry_hour.csv':['version','instrument','year','entry_hour','carry'],
        'monthly_carry.csv':['version','instrument','month','direction','carry'],
        'stop_by_year.csv':['version','instrument','year','exit_type'],
        'outcome_by_year.csv':['version','instrument','year','outcome']}
    for filename,dims in reports.items():csv(output/filename,grouped(f,dims))
    # Explicit descriptive pooled risk-unit bookkeeping, never capital/portfolio return.
    csv(output/'pooled_bookkeeping.csv',grouped(f,['version','year','carry']))
    csv(output/'pooled_year.csv',grouped(f,['version','year']))
    feature_cols=['breakout_penetration_R','signal_body_R','signal_range_R','entry_M15_ATR','entry_H1_ATR',
        'entry_H1_ATR_ratio','entry_H1_ADX','entry_H1_ema_distance_R','entry_H1_slope_R','h1_age_minutes']
    rows=[]
    for keys,g in f.groupby(['version','instrument','year','outcome'],sort=True):
        row=dict(zip(['version','instrument','year','outcome'],keys))|{'trades':len(g)}
        for col in feature_cols:row['mean_'+col]=g[col].mean();row['median_'+col]=g[col].median()
        rows.append(row)
    csv(output/'entry_features_by_outcome.csv',rows)
    merged=c[c.record_status=='CLOSED'].merge(f[KEY+['direction']],on=KEY,validate='many_to_one')
    summaries=[]
    for dims in [['version','instrument','year','horizon_bar','outcome'],['version','year','horizon_bar','outcome'],['version','instrument','year','direction','horizon_bar','carry']]:
        for keys,g in merged.groupby(dims,sort=True):
            a=g[g.available];alive=a[a.completed_before_exit]
            row={'grouping':'|'.join(dims),**dict(zip(dims,keys)),'trades':len(g),'available':len(a),
                'completed_before_exit':len(alive),'exit_on_horizon':int(a.exit_on_horizon_bar.sum())}
            for label,sub in [('all_fixed_horizon',a),('completed_in_position',alive)]:
                for col in ['close_move_R','bar_favorable_R','bar_adverse_R','cumulative_favorable_R','cumulative_adverse_R',
                    'close_beyond_breakout','wick_back_through_breakout','any_close_back_by_horizon','close_continuation']:
                    row[label+'_mean_'+col]=sub[col].mean()
            summaries.append(row)
    csv(output/'first_candles_summary.csv',summaries)
    files=sorted(p.name for p in output.iterdir() if p.suffix in ('.csv','.json') and p.name not in ('MANIFEST.json','ARTIFACT_SHA256.json','AUDIT_RESULTS.json','REPEATABILITY.json','SCOPE_CHECK.json','fixed_version_entry_pairs.csv'))
    inputs={name:E.sha_file(FROZEN/name) for name in ('engine.py','audit.py','trades.csv','OPEN_POSITIONS.json','BASELINE_CONFIGS.json','SOURCE_MANIFEST.json')}
    js(output/'MANIFEST.json',{'discovery_main_observed':MAIN,'data_commit':E.DATA_COMMIT,
        'source_input_hashes':inputs,'sources':source['sources'],'fixed_parameters':{k:asdict(v) for k,v in E.CONFIGS.items()},
        'replay_checks':records,'closed_records':len(f),'open_terminal_records':len(open_infos),
        'time_zone':E.TZ,'year_month_assignment':'local actual exit timestamp; entry_year also retained',
        'future_OHLC_ingested':False,'scope':'read-only diagnostics; no alternate signals/exits or selection',
        'runtime':{'python':platform.python_version(),'numpy':np.__version__,'pandas':pd.__version__},
        'implementation_hashes':{n:E.sha_file(HERE/n) for n in ('diagnose.py','verify.py','test_diagnostics.py','render_report.py')},
        'deterministic_artifacts':files+['MANIFEST.json']})
    js(output/'ARTIFACT_SHA256.json',{n:E.sha_file(output/n) for n in files+['MANIFEST.json']})
    print(json.dumps({'closed':len(f),'open':len(open_infos),'trajectory_rows':len(traces),'artifacts':len(files)+1}))

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--data-root',type=Path,required=True);a.add_argument('--output',type=Path,default=HERE)
    args=a.parse_args();main(args.data_root,args.output)
