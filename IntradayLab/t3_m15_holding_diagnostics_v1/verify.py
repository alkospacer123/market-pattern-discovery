"""Separate standard-library path/features/aggregation verification.

Uses the already independent PR #490 oracle for source parsing and recursive
indicators, never imports diagnose.py or its pandas implementation. Same author;
external reviewer independence remains pending.
"""
import argparse
import csv
from datetime import datetime, timedelta
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import statistics

HERE=Path(__file__).resolve().parent
FROZEN=HERE.parent/'t3_m15_forever_v1'
spec=importlib.util.spec_from_file_location('baseline_standard_library_oracle',FROZEN/'audit.py')
A=importlib.util.module_from_spec(spec);spec.loader.exec_module(A)
KEY=('version','instrument','trade_id')

def read(p):
    with p.open() as f:return list(csv.DictReader(f))
def key(r):return tuple(r[x] for x in KEY)
def num(r,x):return float(r[x])
def flag(r,x):return r[x]=='True'
MAX_DELTA={}
def check(value,saved,label):
    if isinstance(value,bool):assert value==(saved=='True'),(label,value,saved)
    elif isinstance(value,str):assert value==saved,(label,value,saved)
    elif value is None:assert saved=='',(label,saved)
    else:
        delta=abs(value-float(saved));MAX_DELTA[label]=max(MAX_DELTA.get(label,0.),delta)
        tolerance=1e-8
        assert delta<=tolerance,(label,value,saved,delta)

def independent_h1(rows,p):
    groups={}
    for b in rows:groups.setdefault(b['at'].date(),[]).append(b)
    h=[]
    for day in groups.values():
        for i in range(0,len(day),4):
            w=day[i:i+4]
            if len(w)==4 and all(b['at']-a['at']==timedelta(minutes=15) for a,b in zip(w,w[1:])):
                h.append({'at':w[-1]['at'],'h':max(b['h'] for b in w),'l':min(b['l'] for b in w),'c':w[-1]['c']})
    tr=[max(b['h']-b['l'],abs(b['h']-h[i-1]['c']) if i else 0,abs(b['l']-h[i-1]['c']) if i else 0) for i,b in enumerate(h)]
    atr=A.smooth(tr,1/p['atr_period'],p['atr_period'])
    ema=A.smooth([b['c'] for b in h],2/(p['ema_period']+1),p['ema_period'])
    plus=[0.];minus=[0.]
    for a,b in zip(h,h[1:]):
        up=b['h']-a['h'];down=a['l']-b['l'];plus.append(up if up>down and up>0 else 0.);minus.append(down if down>up and down>0 else 0.)
    plus=A.smooth(plus,1/p['adx_period'],p['adx_period']);minus=A.smooth(minus,1/p['adx_period'],p['adx_period'])
    adx=A.smooth([100*abs(a-b)/(a+b) if a is not None and b is not None and a+b>0 else None for a,b in zip(plus,minus)],1/p['adx_period'],p['adx_period'])
    for i,b in enumerate(h):
        win=atr[max(0,i-p['atr_average_period']+1):i+1]
        b.update(atr=atr[i],ema=ema[i],adx=adx[i],slope=ema[i]-ema[i-p['slope_lookback']] if ema[i] is not None and i>=p['slope_lookback'] and ema[i-p['slope_lookback']] is not None else None,
            average=sum(win)/len(win) if len(win)==p['atr_average_period'] and all(x is not None for x in win) else None)
    return h

def main(data_root,root):
    assert root.resolve().is_relative_to(HERE.resolve())
    trades=read(root/'trade_diagnostics.csv');traces=read(root/'stop_trajectory.csv');candles=read(root/'first_candles.csv')
    opened=json.loads((root/'open_position_diagnostics.json').read_text())
    trace_map={};candle_map={}
    for x in traces:trace_map.setdefault(key(x),[]).append(x)
    for x in candles:candle_map.setdefault(key(x),[]).append(x)
    configs=json.loads((FROZEN/'BASELINE_CONFIGS.json').read_text())['fixed_control_versions']
    manifest=json.loads((root/'MANIFEST.json').read_text())
    checked=0;path_checked=0;early_checked=0;h1_checked=0;independent_replayed=0
    for src in manifest['sources']:
        assert A.sha(data_root/src['path'])==src['full_sha256']
        raw=A.prefix(data_root/src['path']);lookup={b['at']:i for i,b in enumerate(raw)}
        for version,config in configs.items():
            p=config['parameters'];rows=A.features(raw,p);higher=independent_h1(raw,p)
            generated,residual=A.simulate(rows,p,{'USDRUBF':.001,'CNYRUBF':.001,'GLDRUBF':.1,'IMOEXF':.5}[src['instrument']])
            subset=[t for t in trades if t['version']==version and t['instrument']==src['instrument']]
            assert len(generated)==len(subset)
            for a,t in zip(generated,subset):
                for col,val in a.items():
                    if col.endswith('_time'):assert datetime.fromisoformat(val)==datetime.fromisoformat(t[col])
                    else:check(val,t[col],col)
                independent_replayed+=1
            subset+= [t for t in opened if t['version']==version and t['instrument']==src['instrument']]
            for t in subset:
                is_open=t['record_status']=='OPEN_TERMINAL'
                at=datetime.fromisoformat(str(t['entry_time']));end=datetime.fromisoformat(str(t['last_close'] if is_open else t['exit_time']))
                i,j=lookup[at],lookup[end];s=1 if t['direction']=='LONG' else -1
                entry=float(t['entry_price']);initial=float(t['initial_stop']);risk=abs(entry-initial)
                stop=initial;updates=0;peak=0;lock=None;tight_no_extreme=0;close_through=0
                h=next(b for b in reversed(higher) if b['at']<=at)
                level=max(b['h'] for b in rows[i-20:i]) if s==1 else min(b['l'] for b in rows[i-20:i])
                fields={'breakout_level':level,'breakout_penetration_R':s*(entry-level)/risk,
                    'signal_body_R':s*(rows[i]['c']-rows[i]['o'])/risk,'signal_range_R':(rows[i]['h']-rows[i]['l'])/risk,
                    'entry_M15_ATR':rows[i]['atr'],'entry_H1_ATR':h['atr'],'entry_H1_ATRMean':h['average'],
                    'entry_H1_ATR_ratio':h['atr']/h['average'],'entry_H1_EMA':h['ema'],'entry_H1_slope':h['slope'],
                    'entry_H1_ADX':h['adx'],'entry_H1_close':h['c'],'entry_H1_ema_distance_R':s*(h['c']-h['ema'])/risk,
                    'entry_H1_slope_R':s*h['slope']/risk,'h1_age_minutes':(at-h['at']).total_seconds()/60,'entry_H1_trend':s}
                for col,val in fields.items():check(val,str(t[col]),col);h1_checked+=1
                assert datetime.fromisoformat(t['h1_available_at'])==h['at']<=at
                path=trace_map[key(t)];assert len(path)==j-i+1
                prev_mfe=0.
                for n,x in enumerate(path):
                    assert int(x['bar_number'])==n
                    assert datetime.fromisoformat(x['available_at'])==rows[i+n]['at']
                    active=stop;b=rows[i+n]
                    hit=n>0 and (b['l']<=stop if s==1 else b['h']>=stop)
                    event='ENTRY' if n==0 else 'EXIT' if hit else 'SURVIVED'
                    assert x['event']==event
                    assert hit==(not is_open and n==j-i)
                    eligible=rows[i+1:i+n+(0 if hit else 1)] if n else []
                    favorable=[0.]+[max(0.,s*((r['h'] if s==1 else r['l'])-entry)/risk) for r in eligible]
                    mfe=max(favorable)
                    adverse=[0.]+[max(0.,s*(entry-(r['l'] if s==1 else r['h']))/risk) for r in eligible]
                    mae=max(adverse);candidate=None;updated=False;without=False;through=False;gap=False;at_open=False
                    if hit:
                        fill=min(b['o'],stop) if s==1 else max(b['o'],stop);gap=fill!=stop;at_open=s*(b['o']-stop)<=0
                        mae=max(mae,-s*(fill-entry)/risk)
                        lower=max(mfe,0.,s*(b['o']-entry)/risk,s*(fill-entry)/risk)
                        upper=lower if at_open else max(lower,s*((b['h'] if s==1 else b['l'])-entry)/risk)
                        for col,val in {'observed_MFE_lower_R':lower,'possible_MFE_upper_R':upper,'recorded_MFE_R':mfe,'no_favorable_confirmed':upper<=1e-12,'no_favorable_unresolved':lower<=1e-12 and upper>1e-12,'giveback_recorded_R':mfe-num(t,'gross_R')}.items():check(val,t[col],col)
                    elif n:
                        if mfe>prev_mfe:peak=n
                        extreme=max([entry]+[r['h'] for r in eligible]) if s==1 else min([entry]+[r['l'] for r in eligible])
                        prev_extreme=max([entry]+[r['h'] for r in eligible[:-1]]) if s==1 else min([entry]+[r['l'] for r in eligible[:-1]])
                        candidate=extreme-s*p['trail_atr']*b['atr'];stop=max(active,candidate) if s==1 else min(active,candidate)
                        updated=stop!=active;updates+=int(updated);without=updated and extreme==prev_extreme;tight_no_extreme+=int(without)
                        through=s*(b['c']-stop)<=0;close_through+=int(through)
                        if lock is None and s*(stop-entry)>0:lock=n
                    for col,val in {'stop_before':active,'stop_after':stop,'stop_before_R':s*(active-entry)/risk,'stop_after_R':s*(stop-entry)/risk,
                        'MFE_recorded_so_far_R':mfe,'MAE_recorded_so_far_R':mae,'ATR_current_to_entry_ratio':1. if n==0 else b['atr']/rows[i]['atr'],
                        'proposed_stop':candidate,'stop_updated':updated,'tightened_without_new_extreme':without,'close_through_new_stop':through,'gap_exit':gap,'exit_at_open':at_open,
                        'trail_distance_R':p['trail_atr']*b['atr']/risk if n and not hit else None}.items():check(val,x[col],col)
                    prev_mfe=mfe;path_checked+=1
                for col,val in {'stop_updates_rebuilt':updates,'peak_MFE_bar':peak,'first_positive_stop_bar':lock,'bars_after_peak_MFE':j-i-peak,
                    'tightenings_without_new_extreme':tight_no_extreme,'close_through_new_stop_bars':close_through,'exit_stop_R':s*(stop-entry)/risk}.items():check(val,str(t.get(col,'')) if t.get(col) is not None else '',col)
                for x in candle_map[key(t)]:
                    n=int(x['horizon_bar']);available=i+n<len(rows);check(available,x['available'],'available')
                    check(available and i+n<j,x['completed_before_exit'],'before exit')
                    if available:
                        b=rows[i+n];w=rows[i+1:i+n+1]
                        vals={'elapsed_minutes':(b['at']-at).total_seconds()/60,'close_move_R':s*(b['c']-entry)/risk,
                            'bar_favorable_R':max(0.,s*((b['h'] if s==1 else b['l'])-entry)/risk),'bar_adverse_R':max(0.,s*(entry-(b['l'] if s==1 else b['h']))/risk),
                            'cumulative_favorable_R':max([0.]+[s*((r['h'] if s==1 else r['l'])-entry)/risk for r in w]),
                            'cumulative_adverse_R':max([0.]+[s*(entry-(r['l'] if s==1 else r['h']))/risk for r in w]),
                            'close_beyond_breakout':s*(b['c']-level)>0,'wick_back_through_breakout':s*((b['l'] if s==1 else b['h'])-level)<=0,
                            'any_close_back_by_horizon':any(s*(r['c']-level)<=0 for r in w),'close_continuation':s*(b['c']-entry)>0}
                        for col,val in vals.items():check(val,x[col],col)
                        early_checked+=1
                if not is_open:
                    check((end.date()-at.date()).days,t['calendar_midnights'],'midnights')
                    check('CROSS_MIDNIGHT' if end.date()!=at.date() else 'SAME_DAY',t['carry'],'carry')
                    gaps=sum((b['at']-a['at']).total_seconds()>900 and (b['at']-timedelta(minutes=15)).date()!=(a['at']-timedelta(microseconds=1)).date() for a,b in zip(rows[i:j+1],rows[i+1:j+1]))
                    check(gaps,t['night_nontrading_gaps'],'night gaps')
                    kind=('SAME_DATE_WITH_NONTRADING_NIGHT_GAP' if gaps else 'SAME_DAY') if end.date()==at.date() else 'CROSSED_NONTRADING_NIGHT_GAP' if gaps else 'MIDNIGHT_OR_CONTINUOUS_CROSS_ONLY'
                    check(kind,t['carry_kind'],'carry kind')
                    check(at.hour,t['entry_hour'],'entry hour')
                    check(end.hour==0 and end.minute==0,t['exit_at_midnight'],'midnight exit')
                    check(entry/risk/10000,t['additional_1bp_R'],'1bp')
                    check(entry/risk*(end-at).total_seconds()/3600,t['exposure_entry_notional_hours_R'],'exposure')
                    checked+=1
    # No pandas/numpy: independently recompute all central aggregation columns.
    aggregate_rows=0
    report_names=['instrument_year.csv','holding_by_year.csv','holding_by_direction.csv','holding_by_bars.csv','carry_by_year.csv',
        'carry_by_direction.csv','holding_carry_direction.csv','carry_kind.csv','entry_hour.csv','monthly.csv','monthly_carry.csv','stop_by_year.csv','outcome_by_year.csv','pooled_bookkeeping.csv','pooled_year.csv']
    dimensions=['version','instrument','year','holding_bucket','bar_bucket','direction','carry','carry_kind','entry_hour','month','exit_type','outcome']
    for filename in report_names:
        for r in read(root/filename):
            sel=[t for t in trades if all(t[d]==r[d] for d in dimensions if d in r)]
            sel.sort(key=lambda t:(datetime.fromisoformat(t['exit_time']),t['instrument'],t['trade_id']))
            vals=[num(t,'net_R') for t in sel];positive=sum(x for x in vals if x>0);negative=-sum(x for x in vals if x<0)
            eq=peak=dd=0.
            for x in vals:eq+=x;peak=max(peak,eq);dd=max(dd,peak-eq)
            top=sorted((x for x in vals if x>0),reverse=True)[:5]
            checks={'trades':len(sel),'wins':sum(x>0 for x in vals),'losses':sum(x<0 for x in vals),
                'gross_R':sum(num(t,'gross_R') for t in sel),'net_R':sum(vals),'C1_R':sum(num(t,'C1_R') for t in sel),
                'PF_net_C1':positive/negative if negative else None,'mean_net_R':sum(vals)/len(sel),
                'max_closed_trade_drawdown_R':dd,'mean_MAE_R':statistics.mean(num(t,'MAE_R') for t in sel),'mean_MFE_R':statistics.mean(num(t,'MFE_R') for t in sel),
                'median_MAE_R':statistics.median(num(t,'MAE_R') for t in sel),'median_MFE_R':statistics.median(num(t,'MFE_R') for t in sel),
                'top1_positive_net_R':max(top) if top else 0.,'top5_positive_net_R':sum(top),'top5_share_positive_R':sum(top)/positive if positive else None,
                'net_R_without_top5_winners':sum(vals)-sum(top),'initial_stop_exits':sum(t['exit_type']=='INITIAL_STOP' for t in sel),'gap_exits':sum(flag(t,'gap_exit') for t in sel),
                'extra_cost_break_even_R_per_trade':sum(vals)/len(sel),'extra_cost_break_even_bps_entry_notional':sum(vals)/sum(num(t,'additional_1bp_R') for t in sel),
                'extra_drag_break_even_bps_per_24h':sum(vals)/sum(num(t,'exposure_entry_notional_hours_R') for t in sel)*240000}
            for field in ['holding_minutes','bars_held','giveback_recorded_R','bars_after_peak_MFE','exit_stop_R','trailing_updates']:
                column={'giveback_recorded_R':'mean_giveback_R'}.get(field,'mean_'+field)
                checks[column]=statistics.mean(num(t,field) for t in sel)
            checks['median_holding_minutes']=statistics.median(num(t,'holding_minutes') for t in sel)
            checks['median_giveback_R']=statistics.median(num(t,'giveback_recorded_R') for t in sel)
            for field in ['tightenings_without_new_extreme','close_through_new_stop_bars']:checks[field]=sum(num(t,field) for t in sel)
            checks['C1_flipped_gross_profit']=sum(flag(t,'C1_flipped_gross_profit') for t in sel)
            gp=sum(num(t,'gross_R') for t in sel if num(t,'gross_R')>0);gn=-sum(num(t,'gross_R') for t in sel if num(t,'gross_R')<0)
            checks['PF_gross']=gp/gn if gn else None
            losses=[t for t in sel if num(t,'net_R')<0]
            for threshold in (1,2):
                for tag,field in [('recorded','MFE_R'),('confirmed','observed_MFE_lower_R'),('possible','possible_MFE_upper_R')]:checks[f'loss_{tag}_MFE_ge_{threshold}']=sum(num(t,field)>=threshold for t in losses)
            for threshold in (1,2):checks[f'gross_loss_recorded_MFE_ge_{threshold}']=sum(num(t,'gross_R')<0 and num(t,'MFE_R')>=threshold for t in sel)
            checks.update(loss_recorded_MFE_zero=sum(num(t,'MFE_R')<=1e-12 for t in losses),loss_no_favorable_confirmed=sum(flag(t,'no_favorable_confirmed') for t in losses),
                loss_no_favorable_unresolved=sum(flag(t,'no_favorable_unresolved') for t in losses),loss_recorded_MFE_lt_0_5=sum(num(t,'MFE_R')<.5 for t in losses))
            for col,val in checks.items():check(val,r[col],filename+':'+col)
            for low,high,label in [(0,.5,'lt_0_5'),(.5,1,'0_5_to_1'),(1,math.inf,'ge_1')]:
                check(sum(num(t,'net_R') for t in losses if low<=num(t,'MFE_R')<high),r['net_R_loss_MFE_'+label],label)
            aggregate_rows+=1
    # Independently check means in entry-feature and first-candle summaries.
    for r in read(root/'entry_features_by_outcome.csv'):
        sel=[t for t in trades if all(t[d]==r[d] for d in ['version','instrument','year','outcome'])]
        check(len(sel),r['trades'],'feature count')
        for col in r:
            if col.startswith('mean_'):check(statistics.mean(num(t,col[5:]) for t in sel),r[col],col)
            if col.startswith('median_'):check(statistics.median(num(t,col[7:]) for t in sel),r[col],col)
    trade_lookup={key(t):t for t in trades}
    summary_count=0
    for r in read(root/'first_candles_summary.csv'):
        dims=r['grouping'].split('|')
        sel=[x|{'direction':trade_lookup[key(x)]['direction']} for x in candles if x['record_status']=='CLOSED']
        sel=[x for x in sel if all(x[d]==r[d] for d in dims)]
        check(len(sel),r['trades'],'early count')
        avail=[x for x in sel if flag(x,'available')];alive=[x for x in avail if flag(x,'completed_before_exit')]
        check(len(avail),r['available'],'available count');check(len(alive),r['completed_before_exit'],'alive count')
        for label,sub in [('all_fixed_horizon',avail),('completed_in_position',alive)]:
            for col in r:
                prefix=label+'_mean_'
                if col.startswith(prefix):
                    field=col[len(prefix):]
                    value=statistics.mean((float(flag(x,field)) if x[field] in ('True','False') else num(x,field)) for x in sub) if sub else None
                    check(value,r[col],col)
        summary_count+=1
    pair_rows=read(root/'fixed_version_entry_pairs.csv')
    baseline={(t['instrument'],t['entry_time'],t['direction']):t for t in trades if t['version']=='BASELINE'}
    optimized={(t['instrument'],t['entry_time'],t['direction']):t for t in trades if t['version']=='OPTIMIZED'}
    assert len(pair_rows)==len(baseline.keys() & optimized.keys())
    for r in pair_rows:
        pair_key=(r['instrument'],r['entry_time'],r['direction'])
        a,b=baseline[pair_key],optimized[pair_key]
        for suffix,t in [('B',a),('O',b)]:
            for field in ['trade_id','exit_time']:assert t[field]==r[field+'_'+suffix]
            for field in ['net_R','MFE_R']:check(num(t,field),r[field+'_'+suffix],'pair '+field)
        check(num(b,'net_R')-num(a,'net_R'),r['net_R_O_minus_B'],'pair delta')
    hashes=json.loads((root/'ARTIFACT_SHA256.json').read_text())
    assert all(A.sha(root/n)==v for n,v in hashes.items())
    result={'status':'PASS','closed_trades':checked,'independent_original_replay_trades':independent_replayed,'open_terminal_positions':len(opened),
        'trajectory_rows':path_checked,'first_candles_checked':early_checked,'preentry_feature_values_checked':h1_checked,
        'aggregate_rows_reconciled':aggregate_rows,'first_candle_summary_rows':summary_count,'artifact_hashes_verified':len(hashes),'fixed_version_entry_pairs_checked':len(pair_rows),
        'numeric_tolerance':'Absolute 1e-8 for all numeric checks; exact booleans/timestamps/keys',
        'maximum_numeric_difference':max(MAX_DELTA.values()),'maximum_difference_by_check':MAX_DELTA,
        'independence':'Separate standard-library formulas and baseline independent oracle; same author. External reviewer pending.'}
    (root/'AUDIT_RESULTS.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='maximum_difference_by_check'},sort_keys=True))

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--data-root',type=Path,required=True);a.add_argument('--output',type=Path,default=HERE)
    args=a.parse_args();main(args.data_root,args.output)
