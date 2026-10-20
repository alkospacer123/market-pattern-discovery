"""Frozen-output comparison gate. Runs before PARTIAL; never repairs sources."""
import math,statistics
import pandas as pd
from common import *
POST='TradingSystemLab/results/post_v3_analysis/'
M15='IntradayLab/t3_m15_t1_entry_retest_v1/'

def stamp(x):return '' if x is None or str(x) in ('','nan','NaT') else pd.Timestamp(x).isoformat()
def value_match(a,e,numeric=False,timestamp=False,h1=False):
    if timestamp:return stamp(a)==stamp(e),0.
    if numeric:
        if a is None or str(a)=='nan':return str(e) in ('','nan'),0.
        if str(e) in ('','nan'):return False,0.
        a=float(a);e=float(e);delta=abs(a-e)
        return (float(format(a,'.12g'))==e if h1 else delta<=1e-8),delta
    if a is None:a=''
    return str(a)==str(e),0.

def reconcile(streams,controls,out):
    rows=[];totalfields=0
    def test(label,system,identity,actual,expected,fields,nums=(),dates=(),h1=False):
        nonlocal totalfields
        errors=[];maximum=0.
        for field,ref in fields.items():
            okay,d=value_match(actual.get(field),expected.get(ref),field in nums,field in dates,h1)
            totalfields+=1;maximum=max(maximum,d)
            if not okay:errors.append(f'{field}: {actual.get(field)!r} != {expected.get(ref)!r}')
        rows.append(dict(system=system,scope=label,identity=identity,status='MISMATCH' if errors else 'MATCH',fields=len(fields),max_raw_numeric_delta=maximum,diagnostic='; '.join(errors)))
    h1ref=csvin(ROOT/(POST+'stage6_fixed_basket_reassessment/trail1_authoritative_trades.csv'))
    m15ref=csvin(ROOT/(M15+'results/next_open_trades.csv'))
    refs={'H1':h1ref,'M15':m15ref}
    for system in ('H1','M15'):
        act=[x for r in controls for x in r['trades'] if x['system']==system and x['status']=='CLOSED']
        def key(x):return (x.get('lifecycle','') if system=='H1' else '',x.get('fold_id',''),x['instrument'],x['trade_id'])
        aa={key(x):x for x in act};ee={key(x):x for x in refs[system]}
        assert len(aa)==len(act) and len(ee)==len(refs[system])
        if aa.keys()!=ee.keys():
            rows.append(dict(system=system,scope='TRADE_KEYS',identity='ALL',status='MISMATCH',fields=1,max_raw_numeric_delta=0,diagnostic=str(dict(missing=sorted(ee.keys()-aa.keys()),extra=sorted(aa.keys()-ee.keys())))))
        for k in sorted(aa.keys()&ee.keys()):
            a,e=aa[k],ee[k]
            if system=='H1':
                a={**a,'trigger_price':a['entry_price']+(1 if a['direction']=='LONG' else -1)*a['initial_risk_price']}
                fields={f:f for f in ('direction','entry_time','entry_price','initial_stop_price','initial_risk_price','trigger_price','trail1_triggered','trigger_bar_time','stored_trail_candidate','trail1_activation_time','trail1_activated','candidate_already_looser','gap_through_activated_trail','exit_time','exit_price','exit_reason','gross_R','cost_R','net_R_C1','bars_held')}
                nums=('entry_price','initial_stop_price','initial_risk_price','trigger_price','stored_trail_candidate','exit_price','gross_R','cost_R','net_R_C1','bars_held')
                dates=('entry_time','trigger_bar_time','trail1_activation_time','exit_time')
            else:
                fields={f:f for f in ('direction','entry_time','signal_time','signal_close','entry_price','ATR','H1AvailableAt','breakout_level','exit_time','exit_price','gross_R','active_stop_at_exit','exit_at_open','gap_exit','exit_type','trailing_updates','bars_held','holding_minutes','observed_gaps_exposed','MFE_R','MAE_R')}
                fields.update(initial_stop_price='initial_stop',initial_risk_price='initial_risk')
                nums=set(fields)-{'direction','entry_time','signal_time','H1AvailableAt','exit_time','exit_at_open','gap_exit','exit_type'}
                dates=('entry_time','signal_time','H1AvailableAt','exit_time')
            test('TRADE','H1' if system=='H1' else 'M15','|'.join(k),a,e,fields,nums,dates,system=='H1')
    # M15's full observed stop and signal state sequence, beyond closed trades.
    actual_stops=[x for r in controls for x in r['trace'] if x['system']=='M15']
    expected_stops=csvin(ROOT/(M15+'results/next_open_stops.csv.gz'))
    def compare_events(actual,expected,kind,af,ef,fields,nums=(),dates=()):
        aa={(x['instrument'],stamp(x[af])):x for x in actual};ee={(x['instrument'],stamp(x[ef])):x for x in expected}
        assert aa.keys()==ee.keys(),('M15_EVENT_KEYS',kind)
        failures=[];maxdelta=0.;n=0
        for k in sorted(aa):
            for a,e in fields.items():
                ok,d=value_match(aa[k].get(a),ee[k].get(e),a in nums,a in dates)
                n+=1;maxdelta=max(maxdelta,d)
                if not ok and len(failures)<15:failures.append(str((k,a,aa[k].get(a),ee[k].get(e))))
        nonlocal totalfields
        totalfields+=n;rows.append(dict(system='M15',scope=kind,identity='ALL',status='MISMATCH' if failures else 'MATCH',fields=n,max_raw_numeric_delta=maxdelta,diagnostic='; '.join(failures)))
    compare_events(actual_stops,expected_stops,'BAR_STOP_STATES','at','bar_close',
                   dict(trade_id='trade_id',stop_entering='active_stop',stop_hit='stop_hit',stop_after='next_stop',candidate='proposal'),('stop_entering','stop_after','candidate'))
    compare_events([x for r in controls for x in r['signals'] if x['system']=='M15'],csvin(ROOT/(M15+'results/next_open_signals.csv.gz')),'SIGNAL_STATES','at','signal_time',
                   dict(trade_id='trade_id',reason='reason',entry_accepted='entry_accepted',occupied_trade_id='occupied_trade_id',same_close_exit_trade_id='same_close_exit_trade_id',entry_price='entry_price',initial_stop='initial_stop',execution_bar_close='execution_bar_close',next_observed_close='next_observed_close'),('entry_price','initial_stop'),('execution_bar_close','next_observed_close'))
    def stats(rs):
        win=[x for x in rs if x>0];loss=[x for x in rs if x<0];pos=math.fsum(win);neg=-math.fsum(loss)
        total=math.fsum(rs);curve=peak=draw=0.;streak=best=0
        for r in rs:
            curve+=r;peak=max(peak,curve);draw=max(draw,peak-curve);streak=streak+1 if r<0 else 0;best=max(best,streak)
        return dict(CLOSED=len(rs),gross_PF=pos/neg if neg else None,gross_R=total,win_rate=len(win)/len(rs) if rs else None,
            mean_win_R=pos/len(win) if win else None,mean_loss_R=-neg/len(loss) if loss else None,
            expectancy_R=total/len(rs) if rs else None,max_closed_R_DD=draw,max_losing_streak=best,gross_positive_R=pos,gross_negative_R=neg)
    # Frozen calendar attribution preserved for reconciliation (H1 UTC, M15 MSK).
    for system in ('H1','M15'):
        trades=[t for r in controls for t in r['trades'] if t['system']==system and t['status']=='CLOSED']
        if system=='H1':
            monthly=[r for r in csvin(ROOT/(POST+'stage6_fixed_basket_reassessment/basket_monthly_metrics.csv')) if r['basket']=='D']
            annual=[r for r in csvin(ROOT/(POST+'stage6_fixed_basket_reassessment/basket_yearly_metrics.csv')) if r['basket']=='D']
        else:
            monthly=[r for r in csvin(ROOT/(M15+'results/monthly_comparison.csv')) if r['model']=='T1_NEXT_OPEN_TRAIL_3p5' and r['gross_R']!='']
            annual=[r for r in csvin(ROOT/(M15+'results/yearly_comparison.csv')) if r['model']=='T1_NEXT_OPEN_TRAIL_3p5']
        reconstructed_months={};cumulative={}
        for name,expected in [('MONTH',monthly),('YEAR',annual)]:
            for e in expected:
                year=int(e['year']) if 'year' in e else int(e['month'][:4])
                month=(int(e['month']) if system=='H1' else int(e['month'][5:])) if name=='MONTH' else None
                subset=[]
                for t in trades:
                    at=pd.Timestamp(t['exit_time']);at=at.tz_convert('UTC') if system=='H1' else at
                    if at.year==year and (month is None or at.month==month) and (system=='M15' or t['lifecycle']==e['lifecycle']):subset.append(t)
                subset.sort(key=lambda t:(t['exit_time'],t['instrument'],t['trade_id']))
                rs=[t['net_R_C1'] if system=='H1' else t['gross_R'] for t in subset]
                a=dict(trades=len(rs),R=math.fsum(rs));fields=dict(trades='trades' if system=='H1' else 'CLOSED',R='net_R' if system=='H1' else 'gross_R')
                st=stats(rs)
                if system=='M15':
                    a.update(st);fields.update({k:k for k in st})
                    a['OPEN']=sum(t['entry_time'].year<=year and (t['status']=='OPEN' or t['exit_time'].year>year) for t in [x for r in controls for x in r['trades'] if x['system']=='M15']) if name=='YEAR' else 0
                    fields['OPEN']='OPEN'
                    if name=='MONTH':reconstructed_months[(year,month)]=a['R']
                    else:
                        vals=[v for (y,mo),v in reconstructed_months.items() if y==year]
                        worst=min(((v,mo) for (y,mo),v in reconstructed_months.items() if y==year))
                        a.update(positive_months=sum(v>1e-8 for v in vals),negative_months=sum(v< -1e-8 for v in vals),zero_months=sum(abs(v)<=1e-8 for v in vals),covered_months=len(vals),worst_month_R=worst[0])
                        fields.update({k:k for k in ('positive_months','negative_months','zero_months','covered_months','worst_month_R')})
                else:
                    a['PF']=st['gross_PF'] if len(rs)>=2 else None;fields['PF']='PF'
                    if name=='MONTH':
                        reconstructed_months[(e['lifecycle'],year,month)]=a['R'];cumulative[e['lifecycle']]=cumulative.get(e['lifecycle'],0.)+a['R']
                        a['cumulative_net_R']=cumulative[e['lifecycle']];fields['cumulative_net_R']='cumulative_net_R'
                    else:
                        vals=[v for (life,y,mo),v in reconstructed_months.items() if life==e['lifecycle'] and y==year]
                        stc=stats(vals)
                        a.update(expectancy_R=st['expectancy_R'],max_DD_R=-st['max_closed_R_DD'],recovery=a['R']/st['max_closed_R_DD'] if st['max_closed_R_DD'] else None,
                            win_rate=st['win_rate'],median_trade_R=statistics.median(rs) if rs else 0.,positive_months=sum(v>0 for v in vals),available_months=len(vals),
                            positive_month_share=sum(v>0 for v in vals)/len(vals),worst_month_R=min(vals),best_month_R=max(vals),median_monthly_R=statistics.median(vals),monthly_std_R=statistics.pstdev(vals),longest_negative_month_streak=stc['max_losing_streak'])
                        for k in ('expectancy_R','max_DD_R','recovery','win_rate','median_trade_R','positive_months','available_months','positive_month_share','worst_month_R','best_month_R','median_monthly_R','monthly_std_R','longest_negative_month_streak'):fields[k]=k
                        for s in SYMBOLS:
                            k=s+'_net_R';a[k]=math.fsum(t['net_R_C1'] for t in subset if t['instrument']==s);fields[k]=k
                identity=f"{e.get('lifecycle','history')}|{year}|{month or 'ALL'}"
                # Aggregates are serialized to 12 sig figs in H1; summation error tolerated.
                test(name,system,identity,a,e,fields,nums=fields.keys())
    csvout(out/'CONTROL_RECONCILIATION.csv',rows)
    errors=[r for r in rows if r['status']!='MATCH']
    result=dict(status='PASS' if not errors else 'STOP_CONTROL_MISMATCH',fields_checked=totalfields,checks=len(rows),mismatches=len(errors),first_errors=errors[:10],h1_closed=418,m15_closed=1114,
        precision='H1 per-trade equality at original 12 significant figures; M15 1e-8 absolute; aggregate 1e-8',calendar='Frozen H1 reports UTC, frozen M15 MSK; primary new calendar tables MSK')
    js(out/'CONTROL_GATE.json',result)
    return result
