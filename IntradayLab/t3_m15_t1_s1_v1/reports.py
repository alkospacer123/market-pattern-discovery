"""Primary gross accounting and descriptive comparison, no selection logic."""
import numpy as np
import pandas as pd
import independent as C
from engine import RULES

def metrics(rows,calendar,opened=0):
    ordered=sorted(rows,key=lambda r:(r['exit_time'],r['instrument'],r['trade_id']))
    x=np.array([r['gross_R'] for r in ordered],dtype=float)
    profit=float(x[x>0].sum());loss=float(-x[x<0].sum());total=float(x.sum())
    months={m:float(sum(r['gross_R'] for r in ordered if r['exit_time'].strftime('%Y-%m')==m)) for m in calendar}
    equity=np.r_[0.,np.cumsum(x)];streak=longest=0
    for r in x:streak=streak+1 if r<0 else 0;longest=max(longest,streak)
    worst=min(months,key=months.get) if months else None
    m={'closed_trades':len(rows),'open_positions_at_period_end':opened,'gross_PF':profit/loss if loss else None,
        'gross_R':total,'expectancy_R':float(x.mean()) if len(x) else None,'positive_R':profit,'negative_R_volume':loss,
        'max_drawdown_closed_R':float((np.maximum.accumulate(equity)-equity).max()),'max_consecutive_losses':longest,
        'calendar_months':len(calendar),'positive_months':sum(r>0 for r in months.values()),
        'negative_months':sum(r<0 for r in months.values()),'zero_months':sum(r==0 for r in months.values()),
        'no_closed_trade_months':sum(not any(r['exit_time'].strftime('%Y-%m')==month for r in ordered) for month in calendar),
        'worst_month':worst,'worst_month_R':months.get(worst),'win_rate':float((x>0).mean()) if len(x) else None}
    for sign in ('positive','negative','zero'):m[sign+'_month_share']=m[sign+'_months']/len(calendar) if calendar else None
    streak=longest=0
    for r in months.values():streak=streak+1 if r<0 else 0;longest=max(longest,streak)
    m['max_losing_month_streak']=longest
    wins=np.sort(x[x>0])[::-1]
    for n in (5,10):
        top=float(wins[:n].sum());m.update({f'top{n}_positive_R':top,f'top{n}_share_positive_R':top/profit if profit else None,
            f'gross_R_without_top{n}':total-top,f'gross_PF_without_top{n}':(profit-top)/loss if loss else None})
    return m

def build(t,o,sn,entries,gaps,frames,rules=RULES):
    tables={k:[] for k in ('overall_report','yearly_report','monthly_report','direction_report','november_dependence',
        'closed_equity','losing_month_runs','top_winners','holding_frequency','signal_funnel','stop_activation',
        'entry_lineage','winner_comparison','new_entries','chronology_changes')}
    for v in C.VERSIONS:
        for rule in rules:
            trades=[r for r in t if r['version']==v and r['rule']==rule]
            for scope in ('ALL_FOUR',*C.SYMBOLS):
                symbols=C.SYMBOLS if scope=='ALL_FOUR' else (scope,)
                base=[r for r in trades if r['instrument'] in symbols]
                opened=[r for r in o if r['version']==v and r['rule']==rule and r['instrument'] in symbols]
                snapshots=[r for r in sn if r['version']==v and r['rule']==rule and r['instrument'] in symbols]
                first=min(frames[s].index[0] for s in symbols).strftime('%Y-%m')
                covered=[m for m in C.CALENDAR if m>=first];ids={'version':v,'rule':rule,'scope':scope}
                tables['overall_report'].append(ids|{'first_available_month':first,'covered_calendar_months':len(covered),
                    'positive_share_covered_months':sum(sum(r['gross_R'] for r in base if r['exit_time'].strftime('%Y-%m')==m)>0 for m in covered)/len(covered)}|metrics(base,C.CALENDAR,len(opened)))
                for year in (2023,2024):
                    x=[r for r in base if r['exit_time'].year==year];months=[m for m in C.CALENDAR if m.startswith(str(year))]
                    op=[r for r in snapshots if r['month']==f'{year}-12']
                    tables['yearly_report'].append(ids|{'year':year}|metrics(x,months,len(op)))
                for direction in ('LONG','SHORT'):
                    for year in ('ALL',2023,2024):
                        x=[r for r in base if r['direction']==direction and (year=='ALL' or r['exit_time'].year==year)]
                        months=C.CALENDAR if year=='ALL' else [m for m in C.CALENDAR if m.startswith(str(year))]
                        op=opened if year=='ALL' else [r for r in snapshots if r['month']==f'{year}-12']
                        tables['direction_report'].append(ids|{'direction':direction,'year':year}|metrics(x,months,sum(r['direction']==direction for r in op)))
                for month in C.CALENDAR:
                    x=[r for r in base if r['exit_time'].strftime('%Y-%m')==month]
                    tables['monthly_report'].append(ids|{'month':month,'coverage':'NO_COVERAGE' if month<first else 'AVAILABLE'}|
                        metrics(x,[month],sum(r['month']==month for r in snapshots)))
                year=[r for r in base if r['exit_time'].year==2024];rest=[r for r in year if r['exit_time'].month!=11]
                a=metrics(year,C.CALENDAR[12:]);b=metrics(rest,[m for m in C.CALENDAR[12:] if m!='2024-11'])
                tables['november_dependence'].append(ids|{'year':2024,'full_PF':a['gross_PF'],'full_R':a['gross_R'],
                    'november_closed':len(year)-len(rest),'november_R':sum(r['gross_R'] for r in year if r['exit_time'].month==11),
                    'ex_november_closed':len(rest),'ex_november_PF':b['gross_PF'],'ex_november_R':b['gross_R'],
                    'ex_november_drawdown_R':b['max_drawdown_closed_R']})
                if scope=='ALL_FOUR':
                    total=peak=0.
                    for r in sorted(base,key=lambda r:(r['exit_time'],r['instrument'],r['trade_id'])):
                        total+=r['gross_R'];peak=max(peak,total)
                        tables['closed_equity'].append(ids|{k:r[k] for k in ('instrument','trade_id','exit_time')}|
                            {'trade_R':r['gross_R'],'cumulative_closed_R':total,'drawdown_R':peak-total})
                monthly={m:sum(r['gross_R'] for r in base if r['exit_time'].strftime('%Y-%m')==m) for m in C.CALENDAR};run=[]
                for month,val in list(monthly.items())+[('END',0)]:
                    if val<0:run.append(month)
                    elif run:
                        tables['losing_month_runs'].append(ids|{'first_month':run[0],'last_month':run[-1],'months':len(run),'gross_R':sum(monthly[m] for m in run)});run=[]
                for n in (5,10):
                    winners=sorted((r for r in base if r['gross_R']>0),key=lambda r:(-r['gross_R'],r['instrument'],r['trade_id']))[:n]
                    for rank,r in enumerate(winners,1):tables['top_winners'].append(ids|{'top_n':n,'rank':rank}|{k:r[k] for k in ('instrument','trade_id','entry_time','exit_time','gross_R')})
                for y in ('ALL',2023,2024):
                    q=[r for r in entries if r['version']==v and r['rule']==rule and r['instrument'] in symbols and (y=='ALL' or r['signal_time'].year==y)]
                    x=[r for r in base if y=='ALL' or r['exit_time'].year==y];accepted=sum(r['entry_accepted'] for r in q)
                    rejected=sum(not r['rule_pass'] for r in q);busy=sum(r['rule_pass'] and r['position_occupied'] for r in q)
                    ident=ids|{'year':y}
                    tables['signal_funnel'].append(ident|{'original_signals':len(q),'accepted_entries':accepted,'rule_forbidden_signals':rejected,
                        'rule_forbidden_when_flat':sum(not r['rule_pass'] and not r['position_occupied'] for r in q),
                        'rule_forbidden_and_busy':sum(not r['rule_pass'] and r['position_occupied'] for r in q),
                        'allowed_skipped_position_busy':busy,'all_busy_signals':sum(r['position_occupied'] for r in q),'partition_check':accepted+rejected+busy==len(q)})
                    days=[set(b.date() for b in frames[s].index if y=='ALL' or b.year==y) for s in symbols]
                    instrument_days=sum(map(len,days));portfolio_days=len(set.union(*days));minutes=[r['holding_minutes'] for r in x]
                    cohort=[r for r in opened if y=='ALL' or r['entry_time'].year==y]
                    tables['holding_frequency'].append(ident|{'closed_count':len(x),'terminal_open_entry_cohort_count':len(cohort),
                        'holding_minutes_mean':float(np.mean(minutes)) if minutes else None,'holding_minutes_median':float(np.median(minutes)) if minutes else None,
                        'holding_minutes_p90':float(np.quantile(minutes,.9)) if minutes else None,'bars_held_median':float(np.median([r['bars_held'] for r in x])) if x else None,
                        'accepted_entries':accepted,'observed_instrument_days':instrument_days,'observed_portfolio_days':portfolio_days,
                        'entries_per_observed_instrument_day':accepted/instrument_days if instrument_days else None,
                        'entries_per_observed_portfolio_day':accepted/portfolio_days if portfolio_days else None,
                        'closed_with_observed_overnight_gap':sum(r['observed_overnight_gaps_exposed']>0 for r in x),
                        'closed_with_observed_overnight_gap_share':sum(r['observed_overnight_gaps_exposed']>0 for r in x)/len(x) if x else None,
                        'total_observed_overnight_gap_exposures':sum(r['observed_overnight_gaps_exposed'] for r in x),
                        'cross_calendar_day_closed':sum(r['cross_calendar_day'] for r in x)})
                    tables['stop_activation'].append(ident|{'closed_count':len(x),'activated_closed':sum(r['threshold_activated'] for r in x),
                        'unactivated_closed':sum(not r['threshold_activated'] for r in x),'unactivated_closed_R':sum(r['gross_R'] for r in x if not r['threshold_activated']),
                        'activated_closed_R':sum(r['gross_R'] for r in x if r['threshold_activated']),
                        'same_entry_signal_candle_used_for_activation':False})
    # Each final comparison is against a separately replayed path, never row filtering.
    key=lambda r:(r['instrument'],r['direction'],r['entry_time'])
    for v in C.VERSIONS:
        for variant in rules:
            if variant=='CONTROL':continue
            targets=('CONTROL','T1','S1') if variant=='COMBINED' else ('CONTROL',)
            vt=[r for r in t if r['version']==v and r['rule']==variant];vo=[r for r in o if r['version']==v and r['rule']==variant]
            decisions={(r['instrument'],r['signal_time']):r for r in entries if r['version']==v and r['rule']==variant}
            closed={key(r):r for r in vt};opened={key(r):r for r in vo}
            for reference in targets:
                rt=[r for r in t if r['version']==v and r['rule']==reference];ro=[r for r in o if r['version']==v and r['rule']==reference]
                all_keys={key(r) for r in rt+ro};local=[]
                for r in rt:
                    match=closed.get(key(r));op=opened.get(key(r));decision=decisions[(r['instrument'],r['entry_time'])]
                    preserved=bool(match and abs(match['gross_R']-r['gross_R'])<=1e-8 and match['exit_time']==r['exit_time'] and abs(match['exit_price']-r['exit_price'])<=1e-8)
                    status='UNCHANGED_CLOSED' if preserved else 'CHANGED_CLOSED' if match else 'TERMINAL_OPEN' if op else 'LOST_ENTRY'
                    row={'version':v,'variant':variant,'reference':reference,'instrument':r['instrument'],'direction':r['direction'],
                        'reference_trade_id':r['trade_id'],'entry_time':r['entry_time'],'reference_exit_time':r['exit_time'],
                        'reference_gross_R':r['gross_R'],'reference_winner_ge_2R':r['gross_R']>=2,'match_status':status,
                        'variant_trade_id':(match or op or {}).get('trade_id'),'variant_exit_time':match['exit_time'] if match else None,
                        'variant_gross_R':match['gross_R'] if match else None,'delta_R':match['gross_R']-r['gross_R'] if match else None,
                        'variant_winner_ge_2R':bool(match and match['gross_R']>=2),'outcome_preserved':preserved,
                        'decision_reason':decision['decision_reason'],'rule_reason':decision['rule_reason'],'occupied_trade_id':decision['occupied_trade_id']}
                    local.append(row);tables['entry_lineage'].append(row)
                news=[r for r in vt if key(r) not in all_keys]
                for r in news:
                    tables['new_entries'].append(r|{'variant':variant,'reference':reference,
                        'reference_occupied_trade_id':next(e['occupied_trade_id'] for e in entries if e['version']==v and e['rule']==reference and e['instrument']==r['instrument'] and e['signal_time']==r['entry_time'])})
                re={(r['instrument'],r['signal_time']):r for r in entries if r['version']==v and r['rule']==reference}
                for k,r in decisions.items():
                    prior=re[k]
                    if r['entry_accepted']!=prior['entry_accepted'] or r['position_occupied']!=prior['position_occupied']:
                        tables['chronology_changes'].append({'version':v,'variant':variant,'reference':reference,
                            'instrument':r['instrument'],'signal_time':r['signal_time'],'direction':r['direction'],
                            'reference_accepted':prior['entry_accepted'],'variant_accepted':r['entry_accepted'],
                            'reference_busy':prior['position_occupied'],'variant_busy':r['position_occupied'],
                            'reference_occupied_trade_id':prior['occupied_trade_id'],'variant_occupied_trade_id':r['occupied_trade_id'],
                            'variant_rule_pass':r['rule_pass'],'variant_reason':r['decision_reason']})
                for scope in ('ALL_FOUR',*C.SYMBOLS):
                    for year in ('ALL',2023,2024):
                        rows=[r for r in local if (scope=='ALL_FOUR' or r['instrument']==scope) and (year=='ALL' or r['reference_exit_time'].year==year)]
                        ww=[r for r in rows if r['reference_winner_ge_2R']];lost=[r for r in rows if r['match_status']=='LOST_ENTRY']
                        nn=[r for r in news if (scope=='ALL_FOUR' or r['instrument']==scope) and (year=='ALL' or r['exit_time'].year==year)]
                        tables['winner_comparison'].append({'version':v,'variant':variant,'reference':reference,'scope':scope,'reference_exit_year':year,
                            'reference_large_winners_ge_2R':len(ww),'large_winners_unchanged':sum(r['outcome_preserved'] for r in ww),
                            'large_winners_changed_still_ge_2R':sum(r['match_status']=='CHANGED_CLOSED' and r['variant_winner_ge_2R'] for r in ww),
                            'large_winners_degraded_below_2R':sum(r['match_status']=='CHANGED_CLOSED' and not r['variant_winner_ge_2R'] for r in ww),
                            'large_winners_lost':sum(r['match_status']=='LOST_ENTRY' for r in ww),
                            'large_winners_terminal_OPEN':sum(r['match_status']=='TERMINAL_OPEN' for r in ww),
                            'lost_large_winner_R':sum(r['reference_gross_R'] for r in ww if r['match_status']=='LOST_ENTRY'),
                            'matched_large_winner_delta_R':sum(r['delta_R'] for r in ww if r['delta_R'] is not None),
                            'lost_entry_rule_blocked':sum(r['decision_reason'] in ('RULE_BLOCKED','RULE_AND_OCCUPIED') for r in lost),
                            'lost_entry_busy_only':sum(r['decision_reason']=='POSITION_OCCUPIED' for r in lost),
                            'new_closed_entries':len(nn),'new_closed_losses':sum(r['gross_R']<0 for r in nn),
                            'new_closed_gross_R':sum(r['gross_R'] for r in nn),'new_losses_R_volume':-sum(r['gross_R'] for r in nn if r['gross_R']<0)})
    tables['instrument_report']=[r for r in tables['overall_report'] if r['scope']!='ALL_FOUR']
    return tables

def render(tables,output):
    def table(rows,fields):
        def fmt(x):return '' if x is None else f'{x:.4f}' if isinstance(x,float) else str(x)
        return '\n'.join(['| '+' | '.join(fields)+' |','| '+' | '.join('---' for _ in fields)+' |']+['| '+' | '.join(fmt(r.get(k)) for k in fields)+' |' for r in rows])+'\n'
    prefix=f'{C.LABEL}\n\n2023–2024: DEVELOPMENT_EXPOSED. Historical signal-Close fills are UNVERIFIED. Terminal OPEN excluded from CLOSED metrics. CLOSED-R is cumulative trade accounting, not capital return.\n\n'
    overall=[r for r in tables['overall_report'] if r['scope']=='ALL_FOUR']
    text='# T3_M15_T1_S1_COMBINED_V1 — complete fixed comparisons\n\n'+prefix
    text+='All four paths are standalone replays with their own occupancy, protective Stops and subsequent entries. COMBINED is exactly T1 + S1; no numerical search or post-result rule change.\n\n'
    text+=table(overall,['version','rule','closed_trades','open_positions_at_period_end','gross_PF','gross_R','expectancy_R','max_drawdown_closed_R','positive_months','max_losing_month_streak','worst_month','worst_month_R'])+'\n'
    text+='## Each year\n\n'+table([r for r in tables['yearly_report'] if r['scope']=='ALL_FOUR'],['version','rule','year','closed_trades','open_positions_at_period_end','gross_PF','gross_R','expectancy_R','max_drawdown_closed_R','positive_months'])+'\n'
    text+='## All 24 calendar months\n\n'+table([r for r in tables['monthly_report'] if r['scope']=='ALL_FOUR'],['version','rule','month','closed_trades','open_positions_at_period_end','gross_PF','gross_R','expectancy_R','max_drawdown_closed_R'])+'\n'
    text+='## Instruments\n\n'+table(tables['instrument_report'],['version','rule','scope','first_available_month','closed_trades','gross_PF','gross_R','max_drawdown_closed_R','positive_months','covered_calendar_months'])+'\n'
    text+='## LONG / SHORT (portfolio and each instrument; all years and each year)\n\n'+table(tables['direction_report'],['version','rule','scope','direction','year','closed_trades','gross_PF','gross_R','max_drawdown_closed_R','positive_months'])+'\n'
    text+='## Top-winner concentration and removal\n\n'+table(overall,['version','rule','top5_share_positive_R','gross_PF_without_top5','gross_R_without_top5','top10_share_positive_R','gross_PF_without_top10','gross_R_without_top10'])+'\n'
    text+='## November 2024 dependence\n\n'+table([r for r in tables['november_dependence'] if r['scope']=='ALL_FOUR'],['version','rule','november_closed','november_R','ex_november_PF','ex_november_R','ex_november_drawdown_R'])+'\n'
    text+='## Winners and occupancy (COMBINED against each reference)\n\n'+table([r for r in tables['winner_comparison'] if r['variant']=='COMBINED' and r['scope']=='ALL_FOUR' and r['reference_exit_year']=='ALL'],['version','reference','reference_large_winners_ge_2R','large_winners_unchanged','large_winners_changed_still_ge_2R','large_winners_degraded_below_2R','large_winners_lost','matched_large_winner_delta_R','new_closed_entries','new_closed_losses','new_closed_gross_R'])+'\n'
    text+='## Duration, entry frequency and cross-session holding\n\n'+table([r for r in tables['holding_frequency'] if r['scope']=='ALL_FOUR' and r['year']=='ALL'],['version','rule','accepted_entries','holding_minutes_mean','holding_minutes_median','holding_minutes_p90','entries_per_observed_portfolio_day','closed_with_observed_overnight_gap','cross_calendar_day_closed'])+'\n'
    text+='Every instrument/month, losing-month run, top winner, entry-lineage decision and Stop/activation decision is available in the CSV/JSON journals beside this report. NO_COVERAGE months before late instrument starts remain in the 24-month calendar denominator and are separately marked. Worst month tie: first calendar month. DD order: exit Close, instrument, trade_id; ties are bookkeeping only. Observed overnight gaps are delta >15 minutes with different source Open dates; no exchange-calendar claim is made.\n'
    (output/'REPORT.md').write_text(text)
