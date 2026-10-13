"""Descriptive full-replay lineage and causal decision diagnostics."""
import pandas as pd
from engine import E,RULES
from research import csv,js,metrics,CALENDAR


def diagnostics(trades,opened,entries,gaps,frames,output):
    funnel,hours,gap_counts,holding,lineage,new_entries,change,path=[],[],[],[],[],[],[],[]
    key=lambda r:(r['instrument'],r['direction'],pd.Timestamp(r['entry_time']))
    for v in E.CONFIGS:
        original=trades.loc[trades.version.eq(v)&trades.rule.eq('CONTROL')]
        original_keys={key(r) for r in original.to_dict('records')}|{key(r) for r in opened if r['version']==v and r['rule']=='CONTROL'}
        control_e=entries.loc[entries.version.eq(v)&entries.rule.eq('CONTROL')].set_index(['instrument','signal_time'])
        for rule in RULES:
            e=entries.loc[entries.version.eq(v)&entries.rule.eq(rule)]
            g=gaps.loc[gaps.version.eq(v)&gaps.rule.eq(rule)]
            f=trades.loc[trades.version.eq(v)&trades.rule.eq(rule)]
            for scope in ('ALL_FOUR',*E.SYMBOLS):
                symbols=E.SYMBOLS if scope=='ALL_FOUR' else (scope,)
                for year in ('ALL',2023,2024):
                    q=e.loc[e.instrument.isin(symbols)];gg=g.loc[g.instrument.isin(symbols)]
                    ff=f.loc[f.instrument.isin(symbols)]
                    if year!='ALL':
                        q=q.loc[q.signal_time.dt.year.eq(year)];gg=gg.loc[gg.current_close.dt.year.eq(year)];ff=ff.loc[ff.exit_time.dt.year.eq(year)]
                    ids={'version':v,'rule':rule,'scope':scope,'year':year}
                    accepted=int(q.entry_accepted.sum());rejected=int((~q.rule_pass).sum());busy=int((q.rule_pass&q.position_occupied).sum())
                    funnel.append(ids|{'original_signals':len(q),'rule_forbidden_signals':rejected,
                        'rule_forbidden_when_flat':int((~q.rule_pass&~q.position_occupied).sum()),
                        'rule_forbidden_and_busy':int((~q.rule_pass&q.position_occupied).sum()),
                        'accepted_entries':accepted,'allowed_skipped_position_busy':busy,
                        'all_busy_signals':int(q.position_occupied.sum()),'partition_check':len(q)==accepted+rejected+busy})
                    assert len(q)==accepted+rejected+busy
                    gap_counts.append(ids|{'observed_gaps_gt_15min':int(gg.reason.eq('OBSERVED_GAP_GT_15_MIN').sum()),
                        'no_previous_bars':int(gg.reason.eq('NO_PREVIOUS_OBSERVED_CLOSE').sum()),
                        'cross_close_date_gaps':int(gg.cross_date.sum()),'cross_observed_open_date_gaps':int(gg.cross_observed_open_date.sum()),
                        'signals_on_first_bar_after_gap':int((gg.original_signal.ne(0)&gg.reason.eq('OBSERVED_GAP_GT_15_MIN')).sum()),
                        'signals_without_previous':int((gg.original_signal.ne(0)&gg.reason.eq('NO_PREVIOUS_OBSERVED_CLOSE')).sum()),
                        'blocked_gap_signals':int(q.rule_reason.eq('FIRST_BAR_AFTER_OBSERVED_GAP').sum()),
                        'blocked_no_previous_signals':int(q.rule_reason.eq('NO_PREVIOUS_OBSERVED_CLOSE').sum())})
                    days=sum(len(set(at.date() for at in frames[s].index if year=='ALL' or at.year==year)) for s in symbols)
                    portfolio_days=len(set(at.date() for s in symbols for at in frames[s].index if year=='ALL' or at.year==year))
                    op=[o for o in opened if o['version']==v and o['rule']==rule and o['instrument'] in symbols and (year=='ALL' or pd.Timestamp(o['entry_time']).year==year)]
                    holding.append(ids|{'closed_count':len(ff),'terminal_open_entry_cohort_count':len(op),
                        'holding_minutes_mean':float(ff.holding_minutes.mean()) if len(ff) else None,
                        'holding_minutes_median':float(ff.holding_minutes.median()) if len(ff) else None,
                        'holding_minutes_p90':float(ff.holding_minutes.quantile(.9)) if len(ff) else None,
                        'bars_held_median':float(ff.bars_held.median()) if len(ff) else None,
                        'accepted_entries':accepted,'observed_instrument_days':days,'observed_portfolio_days':portfolio_days,
                        'entries_per_observed_portfolio_day':accepted/portfolio_days if portfolio_days else None,
                        'entries_per_observed_instrument_day':accepted/days if days else None,
                        'closed_with_observed_overnight_gap':int(ff.observed_overnight_gaps_exposed.gt(0).sum()),
                        'closed_with_observed_overnight_gap_share':float(ff.observed_overnight_gaps_exposed.gt(0).mean()) if len(ff) else None,
                        'total_observed_overnight_gap_exposures':int(ff.observed_overnight_gaps_exposed.sum())})
            if rule=='T1':
                for s in ('ALL_FOUR',*E.SYMBOLS):
                    q=e if s=='ALL_FOUR' else e.loc[e.instrument.eq(s)]
                    for hour in range(24):
                        h=q.loc[q.moscow_hour.eq(hour)]
                        hours.append({'version':v,'scope':s,'moscow_hour':hour,'original_signals':len(h),
                            'forbidden':int((~h.rule_pass).sum()),'forbidden_flat':int((~h.rule_pass&~h.position_occupied).sum()),
                            'forbidden_busy':int((~h.rule_pass&h.position_occupied).sum())})
            if rule=='CONTROL':continue
            lookup={key(r):r for r in f.to_dict('records')}
            for t in original.to_dict('records'):
                match=lookup.get(key(t));decision=e.loc[e.instrument.eq(t['instrument'])&e.signal_time.eq(t['entry_time'])].iloc[0]
                lineage.append({'version':v,'rule':rule,'instrument':t['instrument'],'direction':t['direction'],
                    'control_trade_id':t['trade_id'],'control_entry_time':t['entry_time'],'control_exit_time':t['exit_time'],
                    'control_gross_R':t['gross_R'],'control_winner_ge_2R':t['gross_R']>=2,
                    'match_status':'CLOSED_MATCH' if match else 'LOST_ENTRY',
                    'variant_trade_id':match['trade_id'] if match else None,'variant_gross_R':match['gross_R'] if match else None,
                    'decision_reason':decision.decision_reason,'rule_reason':decision.rule_reason,
                    'occupied_trade_id':decision.occupied_trade_id,'outcome_preserved':bool(match and abs(match['gross_R']-t['gross_R'])<=1e-8)})
                if match:
                    assert abs(match['gross_R']-t['gross_R'])<=1e-8 and match['exit_time']==t['exit_time'],'MATCHED_ENTRY_EXIT_CHANGED'
            news=[r for r in f.to_dict('records') if key(r) not in original_keys]
            new_entries.extend(news)
            for r in e.to_dict('records'):
                c=control_e.loc[(r['instrument'],r['signal_time'])]
                if bool(r['entry_accepted'])!=bool(c.entry_accepted) or bool(r['position_occupied'])!=bool(c.position_occupied):
                    path.append({'version':v,'rule':rule,'instrument':r['instrument'],'signal_time':r['signal_time'],
                        'direction':r['direction'],'control_accepted':bool(c.entry_accepted),'variant_accepted':r['entry_accepted'],
                        'control_busy':bool(c.position_occupied),'variant_busy':r['position_occupied'],
                        'variant_rule_pass':r['rule_pass'],'variant_reason':r['decision_reason'],
                        'control_occupied_trade_id':c.occupied_trade_id,'variant_occupied_trade_id':r['occupied_trade_id']})
            local=[r for r in lineage if r['version']==v and r['rule']==rule]
            for scope in ('ALL_FOUR',*E.SYMBOLS):
                for year in ('ALL',2023,2024):
                    selected=[r for r in local if (scope=='ALL_FOUR' or r['instrument']==scope) and (year=='ALL' or r['control_exit_time'].year==year)]
                    nn=[r for r in news if (scope=='ALL_FOUR' or r['instrument']==scope) and (year=='ALL' or r['exit_time'].year==year)]
                    winners=[r for r in selected if r['control_winner_ge_2R']]
                    lost=[r for r in selected if r['match_status']=='LOST_ENTRY']
                    change.append({'version':v,'rule':rule,'scope':scope,'control_exit_year':year,
                        'control_large_winners_ge_2R':len(winners),'large_winners_preserved':sum(r['outcome_preserved'] for r in winners),
                        'large_winners_lost':sum(r['match_status']=='LOST_ENTRY' for r in winners),
                        'lost_large_winner_R':sum(r['control_gross_R'] for r in winners if r['match_status']=='LOST_ENTRY'),
                        'lost_positive_R':sum(r['control_gross_R'] for r in lost if r['control_gross_R']>0),
                        'removed_negative_R_volume':-sum(r['control_gross_R'] for r in lost if r['control_gross_R']<0),
                        'lost_entry_rule_blocked':sum(r['decision_reason'] in ('RULE_BLOCKED','RULE_AND_OCCUPIED') for r in lost),
                        'lost_entry_busy_only':sum(r['decision_reason']=='POSITION_OCCUPIED' for r in lost),
                        'new_closed_entries':len(nn),'new_closed_losses':sum(r['gross_R']<0 for r in nn),
                        'new_closed_gross_R':sum(r['gross_R'] for r in nn),'new_losses_R_volume':-sum(r['gross_R'] for r in nn if r['gross_R']<0)})
    for name,rows in [('signal_funnel.csv',funnel),('t1_blocked_hours.csv',hours),('t2_gap_summary.csv',gap_counts),
        ('holding_frequency.csv',holding),('trade_lineage.csv',lineage),('new_entries.csv',new_entries),
        ('winner_comparison.csv',change),('chronology_changes.csv',path)]:csv(output/name,rows)
    overall=pd.read_csv(output/'overall_report.csv');years=pd.read_csv(output/'yearly_report.csv')
    objective=[]
    for r in overall.loc[overall.scope.eq('ALL_FOUR')].to_dict('records'):
        c=overall.loc[overall.scope.eq('ALL_FOUR')&overall.version.eq(r['version'])&overall.rule.eq('CONTROL')].iloc[0]
        objective.append({k:r[k] for k in ('version','rule','gross_PF','gross_R','closed_trades','positive_months','negative_months','max_drawdown_closed_R')}|
            {'full_PF_ge_2':bool(r['gross_PF']>=2),'positive_months_improved':bool(r['positive_months']>c.positive_months),
            'delta_gross_R':r['gross_R']-c.gross_R,'delta_drawdown_R':r['max_drawdown_closed_R']-c.max_drawdown_closed_R,
            'delta_closed':r['closed_trades']-int(c.closed_trades)})
    js(output/'OBJECTIVE_ASSESSMENT.json',{'labels':['GROSS_ONLY','COSTS_DEFERRED','NOT_LIVE_READY'],
        'year_2023_2024_status':'DEVELOPMENT_EXPOSED','rows':objective,
        'external_audit':'PENDING','no_auto_acceptance_or_next_stage':True})
