"""Separate stdlib retrospective arithmetic; never supplies trading inputs."""
import csv,io,math,subprocess
from collections import defaultdict
from datetime import datetime,timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
TZ=ZoneInfo('Europe/Moscow')
PIN={'H1':'50f1fd2178c18b7ab3bd969be82ad01f47a34745','M15':'f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8'}
KEY=('system','lifecycle','fold_id','instrument')

def forensics_audit(streams,results,rows):
    ss={tuple(s[k] for k in KEY):s for s in streams}
    rr={tuple(r[k if k!='instrument' else 'instrument'] for k in KEY)+(r['variant'],r['trade_id']):r for r in rows}
    fields=0;positions=0;maxerror=0.
    def same(e,a,context):
        nonlocal fields,maxerror
        fields+=1
        if isinstance(e,(int,float)) and not isinstance(e,bool):
            d=abs(e-a);maxerror=max(maxerror,d);assert d<=1e-8,(context,e,a)
        else:assert e==a,(context,e,a)
    for res in results:
        for trade in res['trades']:
            ident=tuple(trade[k] for k in KEY)+(trade['variant'],trade['trade_id']);actual=rr[ident];positions+=1
            bars=ss[ident[:4]]['bars'];sign=1 if trade['direction']=='LONG' else -1;e=trade['entry_price'];risk=trade['initial_risk_price'];step=timedelta(minutes=60 if trade['system']=='H1' else 15)
            index={b['at']:i for i,b in enumerate(bars)};first=index[trade['entry_time']]+1;last=index[trade['exit_time']] if trade['status']=='CLOSED' else len(bars)-1
            favourable=[];adverse=[];upper_fav=[];upper_adv=[];ft=at=None;immediate_open=immediate_close=early=False
            for i in range(first,last+1):
                b=bars[i];exitbar=trade['status']=='CLOSED' and b['at']==trade['exit_time'];o=sign*(b['Open']-e)/risk
                f=max(0.,sign*((b['High'] if sign==1 else b['Low'])-e)/risk);a=max(0.,-sign*((b['Low'] if sign==1 else b['High'])-e)/risk)
                favourable.extend([0.,o] if exitbar else [0.,o,f]);adverse.extend([0.,-o,-trade['gross_R']] if exitbar else [0.,-o,a]);upper_fav.append(f);upper_adv.append(a)
                if ft is None:
                    if o>0:ft=b['at']-step
                    elif not exitbar and f>0:ft=b['at']
                if at is None:
                    if o<0:at=b['at']-step
                    elif not exitbar and a>0 or exitbar and trade['gross_R']<0:at=b['at']
                if i==first:immediate_open=o<0;immediate_close=not exitbar and sign*(b['Close']-e)<0
                if i<first+4 and (o<=-.5 or not exitbar and a>=.5 or exitbar and trade['gross_R']<=-.5):early=True
            mfe=max(favourable,default=0.);mae=max(adverse,default=0.)
            expected=dict(MFE_pre_stop_R0=mfe,MAE_executable_R0=mae,MFE_observed_upper_R0=max(upper_fav,default=0.),MAE_observed_upper_R0=max(upper_adv,default=0.),first_favorable_time_bound=ft,first_adverse_time_bound=at,held_execution_bars=max(0,last-first+1),immediate_adverse_open=immediate_open,immediate_adverse_survived_close=immediate_close,adverse_half_R_first4=early)
            for key,value in expected.items():same(value,actual[key],ident+(key,))
            step_minutes=60 if trade['system']=='H1' else 15;held=max(0,last-first+1);label=trade.get('exit_time',trade.get('last_mark_time'))
            exposure=dict(frozen_exit_label_time=label,actual_exit_time_lower=label-step if trade['status']=='CLOSED' else None,actual_exit_time_upper=(label-step if trade.get('exit_at_open') else label) if trade['status']=='CLOSED' else None,observed_exposure_minutes_lower=max(0,held-1)*step_minutes,observed_exposure_minutes_upper=(max(0,held-1) if trade.get('exit_at_open') else held)*step_minutes)
            for k,v in exposure.items():same(v,actual[k],ident+(k,))
            future=[u for u in res['trades'] if u['trade_id']!=trade['trade_id'] and u['entry_time']>=label] if trade['status']=='CLOSED' else []
            nxt=min(future,key=lambda u:u['entry_time']) if future else None
            same(nxt['entry_time'] if nxt else None,actual['next_actual_entry_time'],ident+('next_actual_entry_time',));same(nxt['trade_id'] if nxt else None,actual['next_actual_entry_trade_id'],ident+('next_actual_entry_trade_id',))
            if trade['status']=='CLOSED':
                giveback=max(0.,mfe-trade['gross_R']);surrendered=max(0.,mfe-max(0.,trade['gross_R']));below=max(0.,-trade['gross_R'])
                same(giveback,actual['giveback_R0'],ident+('giveback_R0',));same(surrendered,actual['positive_MFE_surrendered_R0'],ident+('positive_MFE_surrendered_R0',));same(below,actual['loss_below_entry_R0'],ident+('loss_below_entry_R0',));same(giveback,surrendered+below,ident+('giveback_decomposition',))
            else:
                same(None,actual['positive_MFE_surrendered_R0'],ident+('open_surrendered',));same(None,actual['loss_below_entry_R0'],ident+('open_below',))
            if trade['variant']!='CONTROL':assert 'LOW_FOLLOW_THROUGH' not in actual['categories'],('LOW_FOLLOW_THROUGH_CONTROL_SCOPE',ident)
            same('CONTROL_ONLY',actual['LOW_FOLLOW_THROUGH_scope'],ident+('LOW_FOLLOW_THROUGH_scope',))
            for q in (.5,1.,1.5,2.):
                label='HIT_BEFORE_STOP' if mfe>=q else 'AMBIGUOUS_EXIT_BAR' if last>=first and trade['status']=='CLOSED' and upper_fav[-1]>=q else 'NOT_OBSERVED'
                same(label,actual[f'MFE_before_stop_ge_{str(q).replace(".","p")}R'],ident+('MFE_threshold',q))
    assert len(rr)==positions
    return dict(status='PASS',positions=positions,fields_checked=fields,max_abs_numeric_error=maxerror,method='Separate stdlib stop-first excursions, extrema bounds, first excursion times, early adverse and threshold recomputation from frozen bars; no primary forensics import')


def post_stop_audit(results,post,data_root):
    """Reopen the eight pinned source blobs; independent 1D/2D window arithmetic."""
    history={};symbols=sorted({(t['system'],t['instrument']) for r in results for t in r['trades'] if t['variant']=='CONTROL' and t.get('exit_reason')=='INITIAL_STOP'})
    for system,symbol in symbols:
        raw=subprocess.check_output(['git','-C',str(data_root),'show',PIN[system]+f':forever/{symbol}/{symbol}_{system}.csv'])
        step=timedelta(minutes=60 if system=='H1' else 15)
        history[(system,symbol)]=[dict(at=datetime.fromisoformat(r['Datetime']).replace(tzinfo=TZ)+step,**{k:float(r[k]) for k in ('Open','High','Low','Close')}) for r in csv.DictReader(io.StringIO(raw.decode()),delimiter=';')]
    post_index={(r['system'],r['lifecycle'],r['fold_id'],r['symbol'],r['trade_id'],r['window_full_next_trading_days']):r for r in post};fields=0;windows=0
    def eq(e,a,ctx):
        nonlocal fields
        fields+=1;assert e==a,(ctx,e,a)
    for result in results:
        for t in result['trades']:
            if t['variant']!='CONTROL' or t.get('exit_reason')!='INITIAL_STOP':continue
            bars=history[(t['system'],t['instrument'])];step=timedelta(minutes=60 if t['system']=='H1' else 15);stopdate=(t['exit_time']-step).date();sign=1 if t['direction']=='LONG' else -1;risk=t['initial_risk_price'];entry=t['entry_price']
            dates=sorted({(b['at']-step).date() for b in bars if (b['at']-step).date()>stopdate})
            for count in (1,2):
                identity=(t['system'],t['lifecycle'],t['fold_id'],t['instrument'],t['trade_id'],count);actual=post_index[identity];windows+=1
                target=dates[count-1] if len(dates)>=count else None;complete=len(dates)>count
                after=[b for b in bars if b['at']>t['exit_time'] and (target is None or (b['at']-step).date()<=target)]
                eq('COMPLETE_OBSERVED_DATE_WINDOW' if complete else 'CENSORED',actual['status'],identity+('status',));eq(len(after),actual['observed_bars'],identity+('bars',));eq(target,actual['target_trading_date'],identity+('targetdate',))
                if after:
                    eq(after[0]['at']-step,actual['window_start'],identity+('window_start',));eq(after[-1]['at'],actual['window_last_bar'],identity+('window_last_bar',))
                thresholds={0.:'RECOVERY_ENTRY',.5:'FAVORABLE_0p5R',1.:'FAVORABLE_1R',1.5:'FAVORABLE_1p5R',2.:'FAVORABLE_2R',-1.5:'ADVERSE_1p5R',-2.:'ADVERSE_2R'}
                first={};touches=0;crossings=0;previous=next((sign*(b['Close']-entry)/risk for b in reversed(bars) if b['at']<=t['exit_time']),0.)
                for ordinal,b in enumerate(after):
                    hi=max(sign*(b['High']-entry)/risk,sign*(b['Low']-entry)/risk);lo=min(sign*(b['High']-entry)/risk,sign*(b['Low']-entry)/risk);o=sign*(b['Open']-entry)/risk;c=sign*(b['Close']-entry)/risk
                    touches+=int(lo<=0<=hi);crossings+=int(previous<0<=c or previous>0>=c);previous=c
                    for level,name in thresholds.items():
                        hit=hi>=level if level>=0 else lo<=level
                        if hit and name not in first:
                            atopen=o>=level if level>=0 else o<=level
                            first[name]=(b['at']-step if atopen else b['at'],'OPEN' if atopen else 'BAR_INTERVAL',ordinal,0 if atopen else 1)
                recovery=first.get('RECOVERY_ENTRY');adverse=first.get('ADVERSE_1p5R')
                order='NEITHER_OBSERVED'
                if recovery and adverse:
                    if recovery[2:]<adverse[2:]:order='RECOVERY_FIRST'
                    elif adverse[2:]<recovery[2:]:order='ADVERSE_FIRST'
                    else:order='AMBIGUOUS_SAME_BAR'
                elif recovery:order='RECOVERY_ONLY_OBSERVED'
                elif adverse:order='ADVERSE_ONLY_OBSERVED'
                eq(order,actual['recovery_vs_adverse_1p5R_order'],identity+('post_stop_order',))
                eq(touches,actual['entry_touch_or_cross_bars'],identity+('entrytouch',));eq(crossings,actual['completed_close_crossings'],identity+('closecross',))
                for name in thresholds.values():
                    observed=first.get(name);eq('OBSERVED' if observed else 'NOT_OBSERVED' if complete else 'CENSORED',actual[name+'_status'],identity+(name,'status'));eq(observed[0] if observed else None,actual[name+'_first_time_bound'],identity+(name,'time'));eq(observed[1] if observed else None,actual[name+'_time_precision'],identity+(name,'precision'))
    assert len(post_index)==windows
    return dict(status='PASS',windows=windows,fields_checked=fields,method='Independent stdlib parser reopens pinned raw OHLC blobs; observed trading-date windows, completeness/censoring, every threshold, touch and close crossings independently recomputed; no primary post-stop import')
