"""Full deterministic gross-only replays and complete diagnostic reports."""
import argparse
import csv as stdcsv
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import platform

import numpy as np
import pandas as pd

from engine import E, FROZEN, HERE, MAIN, RULES, execute, features


def js(path, value):
    path.write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False)+'\n')


def csv(path, rows, columns=None):
    f = rows if isinstance(rows, pd.DataFrame) else pd.DataFrame(rows, columns=columns)
    f.to_csv(path, index=False, float_format='%.15g', lineterminator='\n')


def order(f):
    return f.sort_values(['exit_time','instrument','trade_id'], kind='mergesort').reset_index(drop=True)


def months(first, last, year=None):
    a, b = first.strftime('%Y-%m'), last.strftime('%Y-%m')
    if year is not None:
        a, b = max(a, f'{year}-01'), min(b, f'{year}-12')
    return [] if a > b else [str(x) for x in pd.period_range(a,b,freq='M')]


def metrics(f, calendar, opened=0):
    f = order(f)
    x = f.gross_R.to_numpy(float)
    positive, negative = x[x > 0].sum(), -x[x < 0].sum()
    eq = np.r_[0., x.cumsum()]
    month_R = {m:float(f.loc[f.exit_time.dt.strftime('%Y-%m').eq(m),'gross_R'].sum()) for m in calendar}
    streak = longest = 0
    for v in month_R.values():
        streak = streak+1 if v < 0 else 0
        longest = max(longest, streak)
    trade_streak = longest_trade_streak = 0
    for v in x:
        trade_streak = trade_streak+1 if v < 0 else 0
        longest_trade_streak = max(longest_trade_streak, trade_streak)
    worst = min(month_R, key=month_R.get) if month_R else None
    wins = np.sort(x[x > 0])[::-1]
    result = {'closed_trades':len(f),'open_terminal_positions':opened,
        'gross_PF':float(positive/negative) if negative else None,
        'gross_R':float(x.sum()), 'gross_expectancy_R':float(x.mean()) if len(x) else None,
        'positive_R':float(positive),'negative_R_volume':float(negative),
        'win_rate':float((x > 0).mean()) if len(x) else None,
        'mean_win_R':float(x[x > 0].mean()) if positive else None,
        'mean_loss_R':float(x[x < 0].mean()) if negative else None,
        'max_losing_trade_streak':longest_trade_streak,
        'max_drawdown_R':float((np.maximum.accumulate(eq)-eq).max()),
        'available_months':len(calendar), 'positive_months':sum(v > 0 for v in month_R.values()),
        'negative_months':sum(v < 0 for v in month_R.values()), 'zero_months':sum(v == 0 for v in month_R.values()),
        'positive_month_share':sum(v > 0 for v in month_R.values())/len(calendar) if calendar else None,
        'worst_month':worst,'worst_month_R':month_R.get(worst), 'max_losing_month_streak':longest}
    for n in (5,10):
        top = float(wins[:n].sum())
        result.update({f'top{n}_positive_R':top, f'top{n}_share_positive_R':top/positive if positive else None,
            f'gross_R_without_top{n}':float(x.sum()-top),
            f'gross_PF_without_top{n}':float((positive-top)/negative) if negative else None})
    return result


def control_gate(trades, opened, output):
    ref = pd.read_csv(FROZEN/'trades.csv')
    diffs, details = [], []
    exact = ['trade_id','instrument','direction','bars_held','exit_type','trailing_updates','gap_exit','cross_calendar_day']
    numeric = ['entry_price','initial_stop','initial_risk','exit_price','gross_R','MAE_R','MFE_R','holding_minutes','active_stop_at_exit']
    for version in E.CONFIGS:
        a = order(trades.loc[trades.version.eq(version) & trades.rule.eq('CONTROL')])
        r = ref.loc[ref.version.eq(version)].copy()
        r['exit_time'] = pd.to_datetime(r.exit_time, utc=True).dt.tz_convert(E.TZ)
        r = order(r)
        assert len(a) == len(r), ('CONTROL_COUNT_FAIL',version,len(a),len(r))
        maximum = {}
        for col in exact+numeric+['entry_time','exit_time']:
            if col in numeric:
                delta = abs(a[col].to_numpy(float)-r[col].to_numpy(float))
                maximum[col] = float(delta.max())
                bad = delta > 1e-8
            elif col.endswith('_time'):
                bad = pd.to_datetime(a[col],utc=True).to_numpy() != pd.to_datetime(r[col],utc=True).to_numpy()
            else:
                bad = a[col].to_numpy() != r[col].to_numpy()
            for i in np.flatnonzero(bad):
                diffs.append({'version':version,'ordinal':int(i)+1,'field':col,'actual':str(a.iloc[i][col]),'reference':str(r.iloc[i][col])})
        details.append({'version':version,'closed_trades':len(a),'maximum_numeric_differences':maximum})
    ref_open = json.loads((FROZEN/'OPEN_POSITIONS.json').read_text())
    control_open = [o for o in opened if o['rule'] == 'CONTROL']
    assert len(control_open) == len(ref_open) == 2
    for r in ref_open:
        a = next(o for o in control_open if o['version'] == r['version'] and o['instrument'] == r['instrument'])
        for c,v in r.items():
            if c == 'exit_C1_and_funding':continue
            if isinstance(v,float):assert abs(a[c]-v) <= 1e-8,(c,a[c],v)
            else:assert a[c] == v,(c,a[c],v)
    csv(output/'CONTROL_DIFF.csv', diffs, ['version','ordinal','field','actual','reference'])
    # Reconcile EVERY common field against #495's preserved gross-only control.
    historical = HERE.parent/'t3_m15_entry_regime_v1/results'
    second = pd.read_csv(historical/'trades_CONTROL.csv')
    actual = trades.loc[trades.rule.eq('CONTROL')].copy()
    keys = ['version','exit_time','instrument','trade_id']
    for f in (actual,second):
        f['exit_time'] = pd.to_datetime(f.exit_time,utc=True)
    actual = actual.sort_values(keys,kind='mergesort').reset_index(drop=True)
    second = second.sort_values(keys,kind='mergesort').reset_index(drop=True)
    assert len(actual) == len(second) == 1442
    common = sorted(set(actual.columns) & set(second.columns))
    second_max = {}
    for c in common:
        a,r = actual[c],second[c]
        is_time = c.endswith('_time') or 'AvailableAt' in c
        if is_time:
            a,r = pd.to_datetime(a,utc=True),pd.to_datetime(r,utc=True)
        if pd.api.types.is_numeric_dtype(a) and not pd.api.types.is_bool_dtype(a):
            delta = (pd.to_numeric(a)-pd.to_numeric(r)).abs()
            bad = (delta > 1e-8) | (a.isna() != r.isna())
            second_max[c] = float(delta.max()) if delta.notna().any() else 0.
        else:
            bad = ~(a.eq(r) | (a.isna() & r.isna()))
        for i in np.flatnonzero(bad):
            diffs.append({'version':actual.iloc[i].version,'ordinal':int(i)+1,
                'field':'PR495:'+c,'actual':str(a.iloc[i]),'reference':str(r.iloc[i])})
    second_open = json.loads((historical/'CONTROL_OPEN_POSITIONS.json').read_text())
    for r in second_open:
        a = next(o for o in control_open if o['version'] == r['version'] and o['instrument'] == r['instrument'])
        for c,v in r.items():
            if isinstance(v,float):assert abs(a[c]-v) <= 1e-8,(c,a[c],v)
            else:assert a[c] == v,(c,a[c],v)
    csv(output/'CONTROL_DIFF.csv', diffs, ['version','ordinal','field','actual','reference'])
    status = {'status':'PASS' if not diffs else 'FAIL','expected_closed_total':1442,
        'actual_closed_total':sum(x['closed_trades'] for x in details), 'open_positions':2,
        'sequence_comparison':'exit_time/instrument/trade_id; all record fields except original C1/net economics',
        'numeric_absolute_tolerance':1e-8,'differences':len(diffs),'details':details,
        'PR490_mechanical_fields':exact+numeric+['entry_time','exit_time'],
        'PR495_all_common_fields':common,'PR495_maximum_numeric_differences':second_max,
        'PR490_PR495_terminal_open_comparison':'All preserved fields; #490 cost/funding label excluded'}
    js(output/'CONTROL_REPRODUCTION.json',status)
    assert not diffs and status['actual_closed_total'] == 1442, 'CONTROL_MECHANICS_FAILED_EXPERIMENTS_STOPPED'


def reports(trades, opened, frames, output):
    all_rows, year_rows, direction_rows, monthly_rows, sensitivity, changes, lineage, winner_sets = [], [], [], [], [], [], [], []
    monthly_direction_rows = []
    for version in E.CONFIGS:
        for rule in RULES:
            base = trades.loc[trades.version.eq(version) & trades.rule.eq(rule)]
            for scope in ('ALL_FOUR',*E.SYMBOLS):
                symbols = E.SYMBOLS if scope == 'ALL_FOUR' else (scope,)
                f = base.loc[base.instrument.isin(symbols)]
                first, last = min(frames[s].index[0] for s in symbols), max(frames[s].index[-1] for s in symbols)
                ids = {'version':version,'rule':rule,'scope':scope}
                o = [r for r in opened if r['version'] == version and r['rule'] == rule and r['instrument'] in symbols]
                all_rows.append(ids | metrics(f,months(first,last),len(o)))
                for year in (2023,2024):
                    y = f.loc[f.exit_time.dt.year.eq(year)]
                    oy = [r for r in o if pd.Timestamp(r['entry_time']).year == year]
                    year_rows.append(ids | {'year':year} | metrics(y,months(first,last,year),len(oy)))
                    for direction in ('LONG','SHORT'):
                        direction_rows.append(ids | {'year':year,'direction':direction} |
                            metrics(y.loc[y.direction.eq(direction)],months(first,last,year),sum(r['direction'] == direction for r in oy)))
                for direction in ('LONG','SHORT'):
                    direction_rows.append(ids | {'year':'ALL','direction':direction} |
                        metrics(f.loc[f.direction.eq(direction)],months(first,last),sum(r['direction'] == direction for r in o)))
                for m in months(first,last):
                    mf = f.loc[f.exit_time.dt.strftime('%Y-%m').eq(m)]
                    mo = [r for r in o if pd.Timestamp(r['entry_time']).strftime('%Y-%m') == m]
                    monthly_rows.append(ids | {'month':m} | metrics(mf,[m],len(mo)))
                    for direction in ('LONG','SHORT'):
                        monthly_direction_rows.append(ids | {'month':m,'direction':direction} |
                            metrics(mf.loc[mf.direction.eq(direction)],[m],sum(r['direction'] == direction for r in mo)))
                y = f.loc[f.exit_time.dt.year.eq(2024)]
                n = y.loc[y.exit_time.dt.month.eq(11)]
                rest = y.loc[~y.exit_time.dt.month.eq(11)]
                m = metrics(y,months(first,last,2024))
                mn = metrics(n,['2024-11']); mr = metrics(rest,[x for x in months(first,last,2024) if x != '2024-11'])
                sensitivity.append(ids | {'gross_PF_2024':m['gross_PF'],'gross_R_2024':m['gross_R'],
                    'november_R':mn['gross_R'],'november_PF':mn['gross_PF'],'november_trades':len(n),
                    'november_share_positive_R':mn['positive_R']/m['positive_R'] if m['positive_R'] else None,
                    'november_share_net_gross_R':mn['gross_R']/m['gross_R'] if m['gross_R'] else None,
                    'ex_november_PF':mr['gross_PF'],'ex_november_R':mr['gross_R'],
                    'ex_november_positive_months':mr['positive_months'],'ex_november_max_drawdown_R':mr['max_drawdown_R']})
            if rule == 'CONTROL':continue
            original = trades.loc[trades.version.eq(version) & trades.rule.eq('CONTROL')]
            key = lambda r:(r['instrument'],r['direction'],pd.Timestamp(r['entry_time']))
            lookup = {key(r):r for r in base.to_dict('records')}
            olookup = {key(r):r for r in opened if r['version'] == version and r['rule'] == rule}
            local = []
            for t in original.to_dict('records'):
                a, op = lookup.get(key(t)), olookup.get(key(t))
                status = 'NO_MATCHING_ENTRY' if a is None and op is None else 'OPEN_TERMINAL' if a is None else 'CLOSED_MATCH'
                local.append({'version':version,'rule':rule,'instrument':t['instrument'],'direction':t['direction'],
                    'original_trade_id':t['trade_id'],'original_entry_time':t['entry_time'],
                    'original_exit_time':t['exit_time'],'original_year':t['exit_time'].year,
                    'original_gross_R':t['gross_R'],'original_MFE_R':t['MFE_R'],
                    'original_trend_winner':t['gross_R'] >= 2,
                    'match_status':status,'variant_trade_id':a['trade_id'] if a else op['trade_id'] if op else None,
                    'variant_gross_R':a['gross_R'] if a else None,
                    'variant_exit_time':a['exit_time'] if a else None,
                    'variant_exit_type':a['exit_type'] if a else None})
            lineage += local
            for scope in ('ALL_FOUR',*E.SYMBOLS):
                for year in ('ALL',2023,2024):
                    selected = [r for r in local if (scope == 'ALL_FOUR' or r['instrument'] == scope) and (year == 'ALL' or r['original_year'] == year)]
                    winners = [r for r in selected if r['original_gross_R'] > 0]
                    trends = [r for r in winners if r['original_trend_winner']]
                    losses = [r for r in selected if r['original_gross_R'] < 0]
                    weak_losses = [r for r in losses if r['original_MFE_R'] < .5]
                    closed = lambda r:r['match_status'] == 'CLOSED_MATCH'
                    missing = lambda r:r['match_status'] == 'NO_MATCHING_ENTRY'
                    retained = lambda r:closed(r) and r['variant_gross_R'] >= r['original_gross_R']-1e-8
                    improved_loss = lambda r:closed(r) and r['variant_gross_R'] > r['original_gross_R']+1e-8
                    original_keys = {key(r) for r in original.to_dict('records')} | {key(r) for r in opened if r['version'] == version and r['rule'] == 'CONTROL'}
                    new = [r for r in base.to_dict('records') if key(r) not in original_keys and (scope == 'ALL_FOUR' or r['instrument'] == scope) and (year == 'ALL' or r['exit_time'].year == year)]
                    row = {'version':version,'rule':rule,'scope':scope,'year':year,
                        'original_winners':len(winners),'winner_entries_lost':sum(missing(r) for r in winners),
                        'winner_outcomes_reduced':sum(closed(r) and r['variant_gross_R'] < r['original_gross_R']-1e-8 for r in winners),
                        'winners_turned_nonpositive':sum(closed(r) and r['variant_gross_R'] <= 0 for r in winners),
                        'winner_R_skipped':sum(r['original_gross_R'] for r in winners if missing(r)),
                        'winner_R_reduction_matched':sum(max(0,r['original_gross_R']-r['variant_gross_R']) for r in winners if closed(r)),
                        'original_trend_winners':len(trends),'trend_entries_lost':sum(missing(r) for r in trends),
                        'trend_turned_nonpositive':sum(closed(r) and r['variant_gross_R'] <= 0 for r in trends),
                        'trend_reduced_below_2R':sum(closed(r) and r['variant_gross_R'] < 2 for r in trends),
                        'trend_outcomes_reduced':sum(closed(r) and r['variant_gross_R'] < r['original_gross_R']-1e-8 for r in trends),
                        'trend_fully_preserved':sum(retained(r) for r in trends),
                        'trend_open_unresolved':sum(r['match_status'] == 'OPEN_TERMINAL' for r in trends),
                        'original_losses':len(losses),'loss_entries_eliminated':sum(missing(r) for r in losses),
                        'losses_reduced_or_reversed':sum(improved_loss(r) for r in losses),
                        'losses_worsened':sum(closed(r) and r['variant_gross_R'] < r['original_gross_R']-1e-8 for r in losses),
                        'losses_unchanged':sum(closed(r) and abs(r['variant_gross_R']-r['original_gross_R']) <= 1e-8 for r in losses),
                        'losses_open_unresolved':sum(r['match_status'] == 'OPEN_TERMINAL' for r in losses),
                        'matched_original_loss_R_change':sum(r['variant_gross_R']-r['original_gross_R'] for r in losses if closed(r)),
                        'matched_original_winner_R_change':sum(r['variant_gross_R']-r['original_gross_R'] for r in winners if closed(r)),
                        'negative_R_eliminated_entries':-sum(r['original_gross_R'] for r in losses if missing(r)),
                        'negative_R_reduced_matched':sum(min(0,r['variant_gross_R'])-r['original_gross_R'] for r in losses if improved_loss(r)),
                        'new_entries':len(new),
                        'new_open_entries':sum(key(r) not in original_keys and (scope == 'ALL_FOUR' or r['instrument'] == scope) and (year == 'ALL' or pd.Timestamp(r['entry_time']).year == year) for r in opened if r['version'] == version and r['rule'] == rule),'new_entry_negative_R':-sum(r['gross_R'] for r in new if r['gross_R'] < 0),
                        'new_entry_positive_R':sum(r['gross_R'] for r in new if r['gross_R'] > 0),
                        'original_weak_losses':len(weak_losses),
                        'original_weak_negative_R':-sum(r['original_gross_R'] for r in weak_losses),
                        'weak_loss_entries_eliminated':sum(missing(r) for r in weak_losses),
                        'weak_losses_reduced_or_reversed':sum(improved_loss(r) for r in weak_losses),
                        'weak_negative_R_eliminated':-sum(r['original_gross_R'] for r in weak_losses if missing(r)),
                        'weak_negative_R_reduced':sum(min(0,r['variant_gross_R'])-r['original_gross_R'] for r in weak_losses if improved_loss(r))}
                    changes.append(row)
                    for n in (5,10):
                        top = sorted(winners,key=lambda r:(-r['original_gross_R'],r['instrument'],r['original_trade_id']))[:n]
                        winner_sets.append({'version':version,'rule':rule,'scope':scope,'year':year,'top_n':n,
                            'original_count':len(top),'original_positive_R':sum(r['original_gross_R'] for r in top),
                            'entries_lost':sum(missing(r) for r in top),'fully_preserved':sum(retained(r) for r in top),
                            'reduced':sum(closed(r) and not retained(r) for r in top),
                            'open_unresolved':sum(r['match_status'] == 'OPEN_TERMINAL' for r in top),
                            'matched_variant_R':sum(r['variant_gross_R'] for r in top if closed(r))})
    yr = pd.DataFrame(year_rows)
    comparisons = []
    for r in year_rows:
        c = next(x for x in year_rows if x['version'] == r['version'] and x['scope'] == r['scope'] and x['year'] == r['year'] and x['rule'] == 'CONTROL')
        comparisons.append({k:r[k] for k in ('version','rule','scope','year')} |
            {f'delta_{k}':r[k]-c[k] if r[k] is not None and c[k] is not None else None for k in ('gross_PF','gross_R','closed_trades','gross_expectancy_R','max_drawdown_R','positive_months','top10_share_positive_R')})
    for name,rows in [('overall_report.csv',all_rows),('yearly_report.csv',year_rows),('monthly_report.csv',monthly_rows),
        ('instrument_report.csv',[r for r in all_rows if r['scope'] != 'ALL_FOUR']),('direction_report.csv',direction_rows),
        ('monthly_direction_report.csv',monthly_direction_rows),
        ('november_dependence.csv',sensitivity),('baseline_comparison.csv',comparisons),('trade_lineage.csv',lineage),
        ('winner_loss_changes.csv',changes),('large_winners.csv',winner_sets)]:
        csv(output/name,rows)


def historical_benchmarks(output):
    """Copy unchanged textual metric rows from #495; no A6/A7 execution."""
    folder = HERE.parent/'t3_m15_entry_regime_v1/results'
    sources = {}
    for name in ('overall_report.csv','yearly_report.csv','monthly_report.csv','instrument_report.csv',
                 'direction_report.csv','november_dependence.csv','winner_loss_changes.csv','large_winners.csv'):
        with (folder/name).open() as f:
            reader = stdcsv.DictReader(f)
            columns = reader.fieldnames
            rows = [r for r in reader if r['rule'] in ('A6','A7')]
        with (output/('historical_A6_A7_'+name)).open('w') as f:
            writer = stdcsv.DictWriter(f,fieldnames=columns,lineterminator='\n')
            writer.writeheader();writer.writerows(rows)
        sources[name] = {'reference_sha256':E.sha_file(folder/name),'rows_copied':len(rows)}
    js(output/'HISTORICAL_BENCHMARKS.json',{'source':'Merged PR #495, immutable references',
        'executed_in_this_experiment':False,'combined':False,'source_main':MAIN,'files':sources})


def path_attribution(trades,opened,output):
    """Exact bookkeeping by original entry identity, including year transfers."""
    rows,activation_rows = [],[]
    key = lambda r:(r['instrument'],r['direction'],r['entry_time'])
    for version in E.CONFIGS:
        controls = trades.loc[trades.version.eq(version) & trades.rule.eq('CONTROL')].to_dict('records')
        lookup = {key(r):r for r in controls}
        for rule in RULES:
            variants = trades.loc[trades.version.eq(version) & trades.rule.eq(rule)].to_dict('records')
            alternative = {key(r):r for r in variants}
            for scope in ('ALL_FOUR',*E.SYMBOLS):
                in_scope = lambda r:scope == 'ALL_FOUR' or r['instrument'] == scope
                for year in ('ALL',2023,2024):
                    in_period = lambda r:year == 'ALL' or r['exit_time'].year == year
                    old = [r for r in controls if in_scope(r) and in_period(r)]
                    current = [r for r in variants if in_scope(r) and in_period(r)]
                    positive_delta = negative_delta = zero_delta = absent_R = outbound_R = inbound_R = fresh_R = 0.
                    for r in old:
                        a = alternative.get(key(r))
                        if a is None:absent_R -= r['gross_R']
                        elif not in_period(a):outbound_R -= r['gross_R']
                        elif r['gross_R'] > 0:positive_delta += a['gross_R']-r['gross_R']
                        elif r['gross_R'] < 0:negative_delta += a['gross_R']-r['gross_R']
                        else:zero_delta += a['gross_R']
                    for a in current:
                        r = lookup.get(key(a))
                        if r is None:fresh_R += a['gross_R']
                        elif not in_period(r):inbound_R += a['gross_R']
                    actual = sum(r['gross_R'] for r in current)-sum(r['gross_R'] for r in old)
                    explained = positive_delta+negative_delta+zero_delta+absent_R+outbound_R+inbound_R+fresh_R
                    assert abs(actual-explained) <= 1e-8
                    ids = {'version':version,'rule':rule,'scope':scope,'year':year}
                    rows.append(ids | {'gross_R_change':actual,'matched_original_winners_delta_R':positive_delta,
                        'matched_original_losses_delta_R':negative_delta,'matched_zero_delta_R':zero_delta,
                        'absent_closed_outcome_delta_R':absent_R,'year_transfer_out_R':outbound_R,
                        'year_transfer_in_R':inbound_R,'new_closed_entry_R':fresh_R,'explained_delta_R':explained})
                    activation_rows.append(ids | {'closed_trades':len(current),
                        'threshold_activated_trades':sum(r['threshold_activated'] for r in current),
                        'initial_stop_exits':sum(r['exit_type'] == 'INITIAL_STOP' for r in current),
                        'ATR_TRAIL_last_stop':sum(r['stop_source_at_exit'] == 'ATR_TRAIL' for r in current),
                        'BE_last_stop':sum(r['stop_source_at_exit'] == 'BREAK_EVEN_1R' for r in current),
                        'LOCK_last_stop':sum(r['stop_source_at_exit'] == 'LOCK_1R_AFTER_2R' for r in current),
                        'gap_exits':sum(r['gap_exit'] for r in current),
                        'activated_nonpositive_exits':sum(r['threshold_activated'] and r['gross_R'] <= 0 for r in current)})
    csv(output/'gross_R_attribution.csv',rows)
    csv(output/'activation_report.csv',activation_rows)


def run(data_root, output, controls_only=False):
    output.mkdir(parents=True,exist_ok=True)
    assert output.resolve().is_relative_to(HERE.resolve()), 'OUTPUT_MUST_STAY_INSIDE_NEW_DIRECTORY'
    assert E.git(data_root,'rev-parse','HEAD') == E.DATA_COMMIT, 'DATA_CHECKOUT_NOT_PINNED'
    specs = json.loads((HERE/'EXPERIMENT_SPECS.json').read_text())
    assert specs['main_commit'] == MAIN and specs['data_commit'] == E.DATA_COMMIT
    for v,p in E.CONFIGS.items():assert specs['configurations'][v] == asdict(p)
    prereg = json.loads((HERE/'PREREGISTRATION.json').read_text())
    assert E.sha_file(HERE/'EXPERIMENT_SPECS.json') == prereg['spec_sha256']
    for name,h in prereg['read_only_reference_sha256'].items():assert E.sha_file(HERE.parent.parent/name) == h
    manifest = {'base_main':MAIN,'pr495_merged':True,'data_commit':E.DATA_COMMIT,
        'data_repository':'alkospacer123/market-pattern-data','costs':'GROSS_ONLY_ZERO_DEDUCTED',
        'labels':['COSTS_DEFERRED','GROSS_ONLY','NOT_LIVE_READY'], 'future_OHLC_ingested':False,
        'full_hash_note':'Opaque full-file byte hash only; parser stops before first 2025+ OHLC.',
        'runtime':{'python':platform.python_version(),'pandas':pd.__version__,'numpy':np.__version__},
        'spec_sha256':E.sha_file(HERE/'EXPERIMENT_SPECS.json'),
        'spec_freeze_commit':E.git(HERE.parent.parent,'log','-1','--format=%H','--',str((HERE/'EXPERIMENT_SPECS.json').relative_to(HERE.parent.parent))),
        'preregistration_sha256':E.sha_file(HERE/'PREREGISTRATION.json'), 'sources':[],
        'read_only_reference_sha256':{str(p.relative_to(HERE.parent)):E.sha_file(p) for folder in (FROZEN,HERE.parent/'t3_m15_entry_regime_v1') for p in sorted(folder.iterdir()) if p.is_file()},
        'roadmap_sha256':E.sha_file(HERE.parent/'ROADMAP.md'),
        'implementation_sha256':{p.name:E.sha_file(p) for p in sorted(HERE.iterdir()) if p.suffix == '.py'}}
    frames, lows, trades, opened, decisions, opportunities = {}, {}, [], [], [], []
    for s in E.SYMBOLS:
        relative = f'forever/{s}/{s}_M15.csv'
        source = E.verify_source(data_root,relative)
        raw, prefix_hash = E.read_prefix(data_root/relative)
        frames[s] = E.close_index(raw)
        lows[s], _ = features(frames[s],E.CONFIGS['BASELINE'])
        source.update(instrument=s,historical_prefix_sha256=prefix_hash,used_candles=len(frames[s]),
            first_open=raw.index[0].isoformat(),last_open=raw.index[-1].isoformat(),
            first_close=frames[s].index[0].isoformat(),last_close=frames[s].index[-1].isoformat())
        manifest['sources'].append(source)
    def replay_rule(rule):
        for v,p in E.CONFIGS.items():
            for s in E.SYMBOLS:
                t,o,d,e = execute(lows[s],s,v,p,rule)
                trades.extend(t); decisions.extend(d); opportunities.extend(e)
                if o:opened.append(o)
    replay_rule('CONTROL')
    control = pd.DataFrame(trades)
    control_gate(control,opened,output)
    csv(output/'control_gross_trades.csv',control)
    js(output/'CONTROL_OPEN_POSITIONS.json',opened.copy())
    js(output/'SOURCE_MANIFEST.json',manifest)
    if controls_only:
        print(json.dumps({'control':'PASS','closed':len(control),'open':len(opened)},sort_keys=True))
        return
    for rule in RULES[1:]:replay_rule(rule)
    f = pd.DataFrame(trades).sort_values(['version','rule','exit_time','instrument','trade_id'],kind='mergesort').reset_index(drop=True)
    csv(output/'trades.csv',f)
    for rule in RULES:csv(output/f'trades_{rule}.csv',f.loc[f.rule.eq(rule)])
    js(output/'OPEN_POSITIONS.json',opened)
    csv(output/'stop_decisions.csv',decisions)
    csv(output/'entry_opportunities.csv',opportunities)
    reports(f,opened,frames,output)
    historical_benchmarks(output)
    path_attribution(f,opened,output)
    js(output/'GENERATED_SHA256.json',{p.name:E.sha_file(p) for p in sorted(output.iterdir()) if p.is_file() and p.name != 'GENERATED_SHA256.json'})
    print(json.dumps({'control':'PASS','closed_total':len(f),'open_total':len(opened),'rules':len(RULES),'configuration_count':2},sort_keys=True))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--data-root',type=Path,required=True)
    parser.add_argument('--output',type=Path,default=HERE/'results')
    parser.add_argument('--controls-only',action='store_true')
    a = parser.parse_args()
    run(a.data_root,a.output,a.controls_only)
