"""Outcome diagnostics; never imported by signal feature builder."""
import importlib, math
from datetime import timedelta
from support import *
from features import uid

def calculate(streams,results,entries):
    forensic=importlib.import_module('forensics')
    entry_index={r['signal_id']:r for r in entries}
    outcomes=[];post=[];execution=[];disposition=[];compared=0
    for s,result in zip(streams,results):
        system=s['system'];symbol=s['instrument'];life=s['lifecycle'];fold=s['fold_id'];bars=s['bars']
        by_time={b['at']:i for i,b in enumerate(bars)}
        by_entry={t['entry_time']:t for t in result['trades']}
        archived={r['signal_id']:r for r in csvin(HERE/f'work/archives/pr560/{system}_TRADE_FORENSICS.csv') if r['variant']=='CONTROL' and r['lifecycle']==life}
        for sig in result['signals']:
            sign=int(sig['side']);ident=uid(system,life,fold,symbol,sig['at'],sign)
            if ident not in entry_index: continue
            accepted=sig['accepted'] if system=='H1' else sig['entry_accepted']
            t=by_entry.get(sig['at']) if accepted else None
            disposition.append(dict(signal_id=ident,system=system,instrument=symbol,signal_time=sig['at'],
              accepted=accepted,reason=('EXECUTED_SIGNAL_CLOSE' if accepted else 'POSITION_OCCUPIED') if system=='H1' else sig['reason'],
              trade_id=t['trade_id'] if t else None,occupied_trade_id=sig.get('occupied_trade_id')))
        for t in result['trades']:
            sign=1 if t['direction']=='LONG' else -1
            ident=uid(system,life,fold,symbol,t['entry_time'],sign)
            if ident not in entry_index:continue
            f,paths=forensic.excursions(t,bars,result['trace'])
            if t['status']=='CLOSED':
                ref=archived[ident]
                for name in ('gross_R','entry_price','initial_risk_price','MFE_pre_stop_R0','MAE_executable_R0','MFE_observed_upper_R0','MAE_observed_upper_R0','giveback_R0'):
                    assert abs(float(ref[name])-float(f[name]))<1e-8,('DEVELOPMENT_CONTROL_FORENSICS',ident,name)
                    compared+=1
            group='OPEN' if t['status']=='OPEN' else 'INITIAL_STOP' if t['exit_reason']=='INITIAL_STOP' else 'TRAILING_NEGATIVE' if t['gross_R']<0 else 'TRAILING_POSITIVE' if t['gross_R']>0 else 'TRAILING_ZERO'
            r={k:t.get(k) for k in ('system','instrument','lifecycle','fold_id','trade_id','direction','entry_time','entry_price','initial_stop_price','initial_risk_price','status','exit_time','exit_price','exit_reason','gross_R')}
            r.update(signal_id=ident,signal_year=t['entry_time'].year,signal_month=t['entry_time'].strftime('%Y-%m'),
              outcome_group=group,large_winner_ge_2R=t['status']=='CLOSED' and t['gross_R']>=2)
            for name in ('MFE_pre_stop_R0','MAE_executable_R0','MFE_observed_upper_R0','MAE_observed_upper_R0',
              'first_favorable_time_bound','first_adverse_time_bound','immediate_adverse_open',
              'immediate_adverse_survived_close','adverse_half_R_first4','held_execution_bars',
              'giveback_R0','categories','actual_exit_time_lower','actual_exit_time_upper'):
                r[name]=f[name]
            r['first_favorable_minutes_bound']=(f['first_favorable_time_bound']-t['entry_time']).total_seconds()/60 if f['first_favorable_time_bound'] else None
            r['first_favorable_observed']=f['first_favorable_time_bound'] is not None
            half=None;precision=None;half_bars=None;first_precision=None;first_bar=None
            step=timedelta(minutes=60 if system=='H1' else 15)
            for p in paths:
                exitbar=t['status']=='CLOSED' and p['bar_close']==t['exit_time']
                if p['open_R0']>0 or (not exitbar and max(p['high_R0'],p['low_R0'])>0):
                    first_precision='OPEN' if p['open_R0']>0 else 'BAR_INTERVAL';first_bar=p['held_bar_number'];break
            fav=f['first_favorable_time_bound']
            r.update(first_favorable_precision=first_precision,first_favorable_bar=first_bar,
              first_favorable_time_lower=fav-step if fav and first_precision=='BAR_INTERVAL' else fav,
              first_favorable_status='OBSERVED' if fav else 'CENSORED' if t['status']=='OPEN' else 'AMBIGUOUS_EXIT_BAR' if f['MFE_observed_upper_R0']>0 else 'NOT_OBSERVED')
            for p in paths:
                endbar=t['status']=='CLOSED' and p['bar_close']==t['exit_time']
                if p['open_R0']>=.5:
                    half=p['bar_open'];precision='OPEN';half_bars=p['held_bar_number'];break
                if not endbar and max(p['high_R0'],p['low_R0'])>=.5:
                    half=p['bar_close'];precision='BAR_INTERVAL';half_bars=p['held_bar_number'];break
            r.update(first_half_R_time_bound=half,first_half_R_precision=precision,first_half_R_bar=half_bars,
              first_half_R_minutes_bound=(half-t['entry_time']).total_seconds()/60 if half else None,
              half_R_status='OBSERVED' if half else f['MFE_before_stop_ge_0p5R'] if t['status']=='CLOSED' else 'CENSORED',
              A_low_follow_through=t['status']=='CLOSED' and t['exit_reason']=='INITIAL_STOP' and f['MFE_pre_stop_R0']<.5,
              A_exit_bar_ambiguous=f['MFE_before_stop_ge_0p5R']=='AMBIGUOUS_EXIT_BAR',
              E_negative_trailing_giveback=group=='TRAILING_NEGATIVE' and f['MFE_pre_stop_R0']>0)
            outcomes.append(r)
            index=by_time[t['entry_time']]
            execution.append(dict(signal_id=ident,system=system,instrument=symbol,
              signal_time=t['entry_time'],execution_open_event_time=t['entry_time'] if system=='M15' else None,
              availability='EXECUTION_OPEN_AFTER_SIGNAL' if system=='M15' else 'SIGNAL_CLOSE',
              signed_next_open_gap_atr=sign*(t['entry_price']-bars[index]['Close'])/bars[index]['ATR'],
              signal_predictor=False if system=='M15' else None))
            if t.get('exit_reason')=='INITIAL_STOP':
                for days in (1,2):post.append(forensic.post_stop(t,s['post_bars'],days))
    assert len(disposition)==len(entries)
    return outcomes,post,execution,disposition,dict(status='PASS',PR560_development_forensic_fields=compared,
      open_outcomes='Recomputed at development endpoint; later archive outcome not used')
