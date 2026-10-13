"""Independent standard-library feature arithmetic, event replay and report audit.

Does not import the experiment engine/research implementation. Reuses only the
frozen PR #490 independent byte parser and recursive smoother. Same author;
external audit independence remains pending.
"""
import argparse
import csv
from datetime import datetime, timedelta
import importlib.util
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
FROZEN = HERE.parent/'t3_m15_forever_v1'
spec = importlib.util.spec_from_file_location('independent_frozen_parser',FROZEN/'audit.py')
A = importlib.util.module_from_spec(spec)
spec.loader.exec_module(A)
RULES = ('CONTROL','S1','S2','S3')
SYMBOLS = ('USDRUBF','CNYRUBF','GLDRUBF','IMOEXF')
DELTAS = {}


def read(p):
    with p.open() as f:return list(csv.DictReader(f))


def check(value,saved,label):
    if value is None:
        assert saved in ('',None),(label,value,saved)
    elif isinstance(value,bool):
        assert saved == value or saved == str(value),(label,value,saved)
    elif isinstance(value,datetime):
        assert value == datetime.fromisoformat(saved),(label,value,saved)
    elif isinstance(value,str):
        assert value == saved,(label,value,saved)
    else:
        difference = abs(value-float(saved))
        DELTAS[label] = max(DELTAS.get(label,0.),difference)
        assert math.isfinite(difference) and difference <= 1e-8,(label,value,saved,difference)


def ranges(bars):
    return [max(b['h']-b['l'],abs(b['h']-bars[i-1]['c']) if i else 0.,abs(b['l']-bars[i-1]['c']) if i else 0.) for i,b in enumerate(bars)]


def derive(raw,p):
    days = {}
    for b in raw:days.setdefault(b['at'].date(),[]).append(b)
    high = []
    for day in days.values():
        for j in range(0,len(day),4):
            w = day[j:j+4]
            if len(w) == 4 and all(b['at']-a['at'] == timedelta(minutes=15) for a,b in zip(w,w[1:])):
                high.append({'at':w[-1]['at'],'h':max(b['h'] for b in w),'l':min(b['l'] for b in w),'c':w[-1]['c']})
    atr = A.smooth(ranges(raw),1/p['atr_period'],p['atr_period'])
    ha = A.smooth(ranges(high),1/p['atr_period'],p['atr_period'])
    ema = A.smooth([b['c'] for b in high],2/(p['ema_period']+1),p['ema_period'])
    plus,minus = [0.],[0.]
    for a,b in zip(high,high[1:]):
        up,down = b['h']-a['h'],a['l']-b['l']
        plus.append(up if up > down and up > 0 else 0.)
        minus.append(down if down > up and down > 0 else 0.)
    plus = A.smooth(plus,1/p['adx_period'],p['adx_period'])
    minus = A.smooth(minus,1/p['adx_period'],p['adx_period'])
    adx = A.smooth([100*abs(a-b)/(a+b) if a is not None and b is not None and a+b > 0 else None for a,b in zip(plus,minus)],1/p['adx_period'],p['adx_period'])
    for j,b in enumerate(high):
        slope = ema[j]-ema[j-p['slope_lookback']] if j >= p['slope_lookback'] and ema[j] is not None and ema[j-p['slope_lookback']] is not None else None
        w = ha[max(0,j-p['atr_average_period']+1):j+1]
        average = sum(w)/len(w) if len(w) == p['atr_average_period'] and all(x is not None for x in w) else None
        ratio = ha[j]/average if average else None
        regime = 0
        if slope is not None and adx[j] is not None and average is not None and adx[j] > p['adx_threshold'] and ha[j] > average:
            if b['c'] > ema[j] and slope > 0:regime = 1
            if b['c'] < ema[j] and slope < 0:regime = -1
        b.update(slope=slope,adx=adx[j],ratio=ratio,regime=regime)
    cursor = -1
    rows = []
    for i,b in enumerate(raw):
        while cursor+1 < len(high) and high[cursor+1]['at'] <= b['at']:cursor += 1
        h = high[cursor] if cursor >= 0 else None
        previous_h = high[cursor-1] if cursor > 0 else None
        prior = raw[max(0,i-p['breakout_period']):i]
        upper = max(x['h'] for x in prior) if len(prior) == p['breakout_period'] else None
        lower = min(x['l'] for x in prior) if len(prior) == p['breakout_period'] else None
        signal = 0
        if h and upper is not None:
            if h['regime'] == 1 and b['c'] > upper:signal = 1
            if h['regime'] == -1 and b['c'] < lower:signal = -1
        rows.append(b | {'atr':atr[i],'previous_atr':atr[i-1] if i else None,'signal':signal,
            'upper':upper,'lower':lower,'h1':h,'previous_h1':previous_h})
    return rows


def simulate(rows,p,rule):
    """Independently reconstruct position path from raw-prefix derived features."""
    completed,decisions,opportunities,position = [],[],[],None
    threshold = {'CONTROL':None,'S1':1.,'S2':1.,'S3':2.}[rule]
    for i,b in enumerate(rows):
        if position:
            q = position
            start,s,entry,initial,active = q['index'],q['sign'],q['entry'],q['initial'],q['stop']
            risk = abs(entry-initial)
            opening = b['at']-timedelta(minutes=15)
            at_open = b['o'] <= active if s == 1 else b['o'] >= active
            stop_hit = at_open or (b['l'] <= active if s == 1 else b['h'] >= active)
            before_path = rows[start+1:i]
            before_extreme = max([entry]+[x['h'] for x in before_path]) if s == 1 else min([entry]+[x['l'] for x in before_path])
            d = {'ordinal':len(completed)+1,'bar_open_time':opening,'bar_close_time':b['at'],
                'active_stop':active,'initial_risk':risk,'extreme_before':before_extreme,
                'activated_before':q['activated'],'activation_time_before':q['activation_time'],
                'open':b['o'],'stop_hit':stop_hit,'stop_gap':bool(at_open and b['o'] != active),'threshold_R':threshold}
            if stop_hit:
                fill = min(b['o'],active) if s == 1 else max(b['o'],active)
                lo = min([entry]+[x['l'] for x in before_path]);hi = max([entry]+[x['h'] for x in before_path])
                completed.append({'entry_time':q['at'],'direction':'LONG' if s == 1 else 'SHORT',
                    'entry_price':entry,'initial_stop':initial,'initial_risk':risk,'breakout_level':q['level'],
                    'exit_time':b['at'],'exit_bar_open_time':opening,'exit_bar_close_time':b['at'],'exit_price':fill,
                    'gross_R':s*(fill-entry)/risk,'active_stop_at_exit':active,'trailing_updates':q['updates'],
                    'gap_exit':bool(fill != active),'exit_at_open':at_open,'rule_decision_time':None,'rule_stop_conflict_at_open':False,
                    'exit_type':'INITIAL_STOP' if active == initial else 'RATCHETED_STOP',
                    'bars_held':i-start,'holding_minutes':(b['at']-q['at']).total_seconds()/60,
                    'MAE_R':max(0.,entry-lo if s == 1 else hi-entry,s*(entry-fill))/risk,
                    'MFE_R':max(0.,hi-entry if s == 1 else entry-lo)/risk,
                    'cross_calendar_day':b['at'].date() != q['at'].date(),
                    'threshold_activated':q['activated'],'activation_time':q['activation_time'],
                    'stop_source_at_exit':q['source'],**q['features']})
                d.update(phase='EXIT',exit_price=fill,favorable_extreme_after=None,favorable_R_after=None,
                    activated_after=q['activated'],threshold_activated_now=False,activation_time_after=q['activation_time'],
                    original_trail_proposal=None,boundary_stop=None,active_stop_next_bar=None,ratchet_changed=False,stop_source_next=None)
                position = None
            else:
                path = rows[start+1:i+1]
                extreme = max([entry]+[x['h'] for x in path]) if s == 1 else min([entry]+[x['l'] for x in path])
                distance = s*(extreme-entry)
                triggered = threshold is not None and not q['activated'] and distance >= threshold*risk
                if triggered:q['activated'],q['activation_time'] = True,b['at']
                trail = extreme-s*p['trail_atr']*b['atr']
                floor = None
                if q['activated'] and rule == 'S2':floor = entry
                if q['activated'] and rule == 'S3':floor = entry+s*risk
                candidates = [(active,q['source'])]
                if rule in ('CONTROL','S2','S3') or q['activated']:candidates.append((trail,'ATR_TRAIL'))
                if floor is not None:candidates.append((floor,'BREAK_EVEN_1R' if rule == 'S2' else 'LOCK_1R_AFTER_2R'))
                # max is stable: equal proposals preserve existing source and Stop.
                new,source = max(candidates,key=lambda pair:s*pair[0])
                changed = new != active
                q['updates'] += int(changed);q['stop'],q['source'],q['extreme'] = new,source,extreme
                d.update(phase='SURVIVED',exit_price=None,favorable_extreme_after=extreme,favorable_R_after=distance/risk,
                    activated_after=q['activated'],threshold_activated_now=triggered,activation_time_after=q['activation_time'],
                    original_trail_proposal=trail,boundary_stop=floor,active_stop_next_bar=new,ratchet_changed=changed,stop_source_next=source)
            decisions.append(d)
        if b['atr'] is not None and b['signal']:
            accepted = position is None
            opportunities.append({'signal_time':b['at'],'direction':'LONG' if b['signal'] == 1 else 'SHORT',
                'rule_pass':True,'position_occupied':position is not None,'entry_accepted':accepted})
            if accepted:
                h,prev = b['h1'],b['previous_h1']
                feat = {'ATR':b['atr'],'PreviousATR':b['previous_atr'],'H1ADX':h['adx'],
                    'H1PreviousADX':prev['adx'] if prev else None,'H1Slope':h['slope'],
                    'H1PreviousSlope':prev['slope'] if prev else None,'H1ATRRatio':h['ratio'],
                    'H1PreviousATRRatio':prev['ratio'] if prev else None,'H1AvailableAt':h['at'],
                    'H1PreviousAvailableAt':prev['at'] if prev else None,'signal_open':b['o'],'signal_high':b['h'],'signal_low':b['l']}
                initial = b['c']-b['signal']*p['stop_atr']*b['atr']
                position = {'at':b['at'],'index':i,'sign':b['signal'],'entry':b['c'],'initial':initial,
                    'stop':initial,'updates':0,'level':b['upper'] if b['signal'] == 1 else b['lower'],
                    'activated':False,'activation_time':None,'features':feat,'source':'INITIAL_STOP','extreme':b['c']}
    return completed,position,decisions,opportunities


def aggregate(selected,calendar,opens):
    selected = sorted(selected,key=lambda r:(datetime.fromisoformat(r['exit_time']),r['instrument'],r['trade_id']))
    x = [float(r['gross_R']) for r in selected]
    positive,negative = sum(v for v in x if v > 0),-sum(v for v in x if v < 0)
    equity = peak = dd = 0.
    for v in x:
        equity += v; peak = max(peak,equity);dd = max(dd,peak-equity)
    m = {month:sum(float(r['gross_R']) for r in selected if r['exit_time'][:7] == month) for month in calendar}
    worst = min(m,key=m.get) if m else None
    run = longest = 0
    for v in m.values():
        run = run+1 if v < 0 else 0;longest = max(longest,run)
    trade_run = longest_trade = 0
    for v in x:
        trade_run = trade_run+1 if v < 0 else 0;longest_trade = max(longest_trade,trade_run)
    a = {'closed_trades':len(x),'open_terminal_positions':opens,'gross_PF':positive/negative if negative else None,
        'gross_R':sum(x),'gross_expectancy_R':sum(x)/len(x) if x else None,'positive_R':positive,'negative_R_volume':negative,
        'win_rate':sum(v > 0 for v in x)/len(x) if x else None,
        'mean_win_R':positive/sum(v > 0 for v in x) if positive else None,
        'mean_loss_R':-negative/sum(v < 0 for v in x) if negative else None,'max_losing_trade_streak':longest_trade,'max_drawdown_R':dd,
        'available_months':len(m),'positive_months':sum(v > 0 for v in m.values()),'negative_months':sum(v < 0 for v in m.values()),
        'zero_months':sum(v == 0 for v in m.values()),'positive_month_share':sum(v > 0 for v in m.values())/len(m) if m else None,
        'worst_month':worst,'worst_month_R':m.get(worst),'max_losing_month_streak':longest}
    wins = sorted((v for v in x if v > 0),reverse=True)
    for n in (5,10):
        top = sum(wins[:n]);a.update({f'top{n}_positive_R':top,f'top{n}_share_positive_R':top/positive if positive else None,
            f'gross_R_without_top{n}':sum(x)-top,f'gross_PF_without_top{n}':(positive-top)/negative if negative else None})
    return a


def month_range(a,b):
    values = []
    year,month = map(int,a.split('-'))
    while f'{year:04d}-{month:02d}' <= b:
        values.append(f'{year:04d}-{month:02d}')
        month += 1
        if month == 13:year += 1;month = 1
    return values


def main(data_root,root,report):
    assert root.resolve().is_relative_to(HERE.resolve()) and report.resolve().is_relative_to(HERE.resolve())
    manifest = json.loads((root/'SOURCE_MANIFEST.json').read_text())
    prereg = json.loads((HERE/'PREREGISTRATION.json').read_text())
    assert A.sha(HERE/'EXPERIMENT_SPECS.json') == prereg['spec_sha256']
    for name,h in prereg['read_only_reference_sha256'].items():assert A.sha(HERE.parent.parent/name) == h
    for name,h in manifest['implementation_sha256'].items():assert A.sha(HERE/name) == h
    config = json.loads((HERE/'EXPERIMENT_SPECS.json').read_text())['configurations']
    trades,decisions,opportunities = read(root/'trades.csv'),read(root/'stop_decisions.csv'),read(root/'entry_opportunities.csv')
    opened = json.loads((root/'OPEN_POSITIONS.json').read_text())
    for name,h in manifest['read_only_reference_sha256'].items():assert A.sha(HERE.parent/name) == h
    assert A.sha(HERE.parent/'ROADMAP.md') == manifest['roadmap_sha256']
    checked = path_decisions = signal_checks = 0
    details = []
    for src in manifest['sources']:
        assert A.sha(data_root/src['path']) == src['full_sha256']
        raw = A.prefix(data_root/src['path'])
        assert len(raw) == src['used_candles']
        for v,p in config.items():
            rows = derive(raw,p)
            for rule in RULES:
                generated,residual,d,e = simulate(rows,p,rule)
                matches = lambda r:r['version'] == v and r['rule'] == rule and r['instrument'] == src['instrument']
                saved = [t for t in trades if matches(t)]
                assert len(generated) == len(saved),(src['instrument'],v,rule,len(generated),len(saved))
                for ordinal,(g,t) in enumerate(zip(generated,saved),1):
                    alias = {'USDRUBF':'Si','CNYRUBF':'CNY'}.get(src['instrument'],src['instrument'])
                    assert t['trade_id'] == f'T3-M15-{alias}-{ordinal:06d}'
                    for col,val in g.items():check(val,t[col],'trade:'+col)
                    checked += 1
                saved_o = [x for x in opened if matches(x)]
                assert len(saved_o) == int(residual is not None)
                if residual:
                    o,q = saved_o[0],residual
                    for col,val in {'entry_time':q['at'],'entry_price':q['entry'],'initial_stop':q['initial'],
                        'active_stop':q['stop'],'initial_risk':abs(q['entry']-q['initial']),
                        'favorable_extreme':q['extreme'],'stop_source':q['source'],'stop_updates':q['updates'],
                        'breakout_level':q['level'],
                        'last_close':rows[-1]['at'],'last_close_price':rows[-1]['c'],'pending_exit_decision':None,
                        'direction':'LONG' if q['sign'] == 1 else 'SHORT','threshold_activated':q['activated'],'activation_time':q['activation_time'],
                        'unrealized_gross_R_at_last_close':q['sign']*(rows[-1]['c']-q['entry'])/abs(q['entry']-q['initial'])}.items():check(val,o[col],'open:'+col)
                saved_d = [x for x in decisions if matches(x)]
                assert len(d) == len(saved_d)
                for g,t in zip(d,saved_d):
                    assert t['trade_id'].endswith(f"{g.pop('ordinal'):06d}")
                    for col,val in g.items():check(val,t[col],'decision:'+col)
                    path_decisions += 1
                saved_e = [x for x in opportunities if matches(x)]
                assert len(e) == len(saved_e)
                for g,t in zip(e,saved_e):
                    for col,val in g.items():check(val,t[col],'signal:'+col)
                    signal_checks += 1
                details.append({'version':v,'rule':rule,'instrument':src['instrument'],'closed_trades':len(saved),'open_positions':len(saved_o),'status':'PASS'})
    # Every central metric in every calendar/instrument/direction report.
    report_rows = 0
    sources = {s['instrument']:s for s in manifest['sources']}
    report_names = ('overall_report.csv','yearly_report.csv','monthly_report.csv','instrument_report.csv','direction_report.csv','monthly_direction_report.csv')
    for name in report_names:
        for r in read(root/name):
            symbols = SYMBOLS if r['scope'] == 'ALL_FOUR' else (r['scope'],)
            selected = [x for x in trades if x['version'] == r['version'] and x['rule'] == r['rule'] and x['instrument'] in symbols]
            os = [x for x in opened if x['version'] == r['version'] and x['rule'] == r['rule'] and x['instrument'] in symbols]
            first,last = min(sources[s]['first_close'][:7] for s in symbols),max(sources[s]['last_close'][:7] for s in symbols)
            if r.get('year','ALL') != 'ALL':
                year = r['year'];selected = [x for x in selected if x['exit_time'][:4] == year]
                os = [x for x in os if x['entry_time'][:4] == year]
                first,last = max(first,year+'-01'),min(last,year+'-12')
            if 'direction' in r:
                selected = [x for x in selected if x['direction'] == r['direction']]
                os = [x for x in os if x['direction'] == r['direction']]
            calendar = month_range(first,last) if first <= last else []
            if 'month' in r:
                selected = [x for x in selected if x['exit_time'][:7] == r['month']];calendar = [r['month']]
                os = [x for x in os if x['entry_time'][:7] == r['month']]
            for col,val in aggregate(selected,calendar,len(os)).items():check(val,r[col],name+':'+col)
            report_rows += 1
    for r in read(root/'baseline_comparison.csv'):
        rows = read(root/'yearly_report.csv')
        find = lambda rule:next(x for x in rows if all(x[k] == r[k] for k in ('version','scope','year')) and x['rule'] == rule)
        actual,control = find(r['rule']),find('CONTROL')
        for col in r:
            if col.startswith('delta_'):
                field = col[6:];val = float(actual[field])-float(control[field]) if actual[field] and control[field] else None
                check(val,r[col],'comparison:'+col)
    november_rows = 0
    for r in read(root/'november_dependence.csv'):
        sel = [t for t in trades if t['version'] == r['version'] and t['rule'] == r['rule'] and (r['scope'] == 'ALL_FOUR' or t['instrument'] == r['scope']) and t['exit_time'][:4] == '2024']
        n = [t for t in sel if t['exit_time'][:7] == '2024-11'];rest = [t for t in sel if t['exit_time'][:7] != '2024-11']
        full = aggregate(sel,month_range('2024-01','2024-12'),0);nov = aggregate(n,['2024-11'],0)
        removed = aggregate(rest,[m for m in month_range('2024-01','2024-12') if m != '2024-11'],0)
        vals = {'gross_PF_2024':full['gross_PF'],'gross_R_2024':full['gross_R'],'november_R':nov['gross_R'],
            'november_PF':nov['gross_PF'],'november_trades':len(n),'ex_november_PF':removed['gross_PF'],
            'ex_november_R':removed['gross_R'],'ex_november_positive_months':removed['positive_months'],
            'ex_november_max_drawdown_R':removed['max_drawdown_R'],
            'november_share_positive_R':nov['positive_R']/full['positive_R'] if full['positive_R'] else None,
            'november_share_net_gross_R':nov['gross_R']/full['gross_R'] if full['gross_R'] else None}
        for col,val in vals.items():check(val,r[col],'november:'+col)
        november_rows += 1
    # Exact-entry attribution and fixed top-winner cohorts, no hindsight decisions.
    key = lambda t:(t['version'],t['instrument'],t['direction'],datetime.fromisoformat(t['entry_time']))
    controls = {key(t):t for t in trades if t['rule'] == 'CONTROL'}
    variants = {(t['rule'],key(t)):t for t in trades}
    opens = {(t['rule'],key(t)):t for t in opened}
    lineage = read(root/'trade_lineage.csv')
    for r in lineage:
        k = (r['version'],r['instrument'],r['direction'],datetime.fromisoformat(r['original_entry_time']))
        original = controls[k];variant = variants.get((r['rule'],k));op = opens.get((r['rule'],k))
        status = 'CLOSED_MATCH' if variant else 'OPEN_TERMINAL' if op else 'NO_MATCHING_ENTRY'
        check(status,r['match_status'],'lineage:status')
        check(float(original['gross_R']),r['original_gross_R'],'lineage:original_R')
        check(float(variant['gross_R']) if variant else None,r['variant_gross_R'],'lineage:variant_R')
        check(float(original['gross_R']) >= 2,r['original_trend_winner'],'lineage:trend')
        check(float(original['MFE_R']),r['original_MFE_R'],'lineage:MFE')
    for r in read(root/'winner_loss_changes.csv'):
        selected = [t for t in lineage if t['version'] == r['version'] and t['rule'] == r['rule'] and (r['scope'] == 'ALL_FOUR' or t['instrument'] == r['scope']) and (r['year'] == 'ALL' or t['original_year'] == r['year'])]
        wins = [t for t in selected if float(t['original_gross_R']) > 0]
        trends = [t for t in wins if float(t['original_gross_R']) >= 2]
        losses = [t for t in selected if float(t['original_gross_R']) < 0]
        weak = [t for t in losses if float(t['original_MFE_R']) < .5]
        missing = lambda t:t['match_status'] == 'NO_MATCHING_ENTRY'
        closed = lambda t:t['match_status'] == 'CLOSED_MATCH'
        old = lambda t:float(t['original_gross_R'])
        new = lambda t:float(t['variant_gross_R'])
        reduced = lambda t:closed(t) and new(t) < old(t)-1e-8
        improved = lambda t:closed(t) and new(t) > old(t)+1e-8
        extra = [t for t in trades if t['version'] == r['version'] and t['rule'] == r['rule'] and key(t) not in controls and (('CONTROL',key(t)) not in opens) and (r['scope'] == 'ALL_FOUR' or t['instrument'] == r['scope']) and (r['year'] == 'ALL' or t['exit_time'][:4] == r['year'])]
        vals = {'original_winners':len(wins),'winner_entries_lost':sum(missing(t) for t in wins),
            'winner_outcomes_reduced':sum(reduced(t) for t in wins),
            'winners_turned_nonpositive':sum(closed(t) and new(t) <= 0 for t in wins),
            'winner_R_skipped':sum(old(t) for t in wins if missing(t)),
            'winner_R_reduction_matched':sum(old(t)-new(t) for t in wins if reduced(t)),
            'original_trend_winners':len(trends),'trend_entries_lost':sum(missing(t) for t in trends),
            'trend_turned_nonpositive':sum(closed(t) and new(t) <= 0 for t in trends),
            'trend_reduced_below_2R':sum(closed(t) and new(t) < 2 for t in trends),
            'trend_outcomes_reduced':sum(reduced(t) for t in trends),
            'trend_fully_preserved':sum(closed(t) and new(t) >= old(t)-1e-8 for t in trends),
            'trend_open_unresolved':sum(t['match_status'] == 'OPEN_TERMINAL' for t in trends),
            'original_losses':len(losses),'loss_entries_eliminated':sum(missing(t) for t in losses),
            'losses_reduced_or_reversed':sum(improved(t) for t in losses),
            'losses_worsened':sum(closed(t) and new(t) < old(t)-1e-8 for t in losses),
            'losses_unchanged':sum(closed(t) and abs(new(t)-old(t)) <= 1e-8 for t in losses),
            'losses_open_unresolved':sum(t['match_status'] == 'OPEN_TERMINAL' for t in losses),
            'matched_original_loss_R_change':sum(new(t)-old(t) for t in losses if closed(t)),
            'matched_original_winner_R_change':sum(new(t)-old(t) for t in wins if closed(t)),
            'negative_R_eliminated_entries':-sum(old(t) for t in losses if missing(t)),
            'negative_R_reduced_matched':sum(min(0,new(t))-old(t) for t in losses if improved(t)),
            'new_entries':len(extra),
            'new_open_entries':sum(t['version'] == r['version'] and t['rule'] == r['rule'] and key(t) not in controls and ('CONTROL',key(t)) not in opens and (r['scope'] == 'ALL_FOUR' or t['instrument'] == r['scope']) and (r['year'] == 'ALL' or t['entry_time'][:4] == r['year']) for t in opened),'new_entry_negative_R':-sum(float(t['gross_R']) for t in extra if float(t['gross_R']) < 0),
            'new_entry_positive_R':sum(float(t['gross_R']) for t in extra if float(t['gross_R']) > 0),
            'original_weak_losses':len(weak),'original_weak_negative_R':-sum(old(t) for t in weak),
            'weak_loss_entries_eliminated':sum(missing(t) for t in weak),'weak_losses_reduced_or_reversed':sum(improved(t) for t in weak),
            'weak_negative_R_eliminated':-sum(old(t) for t in weak if missing(t)),
            'weak_negative_R_reduced':sum(min(0,new(t))-old(t) for t in weak if improved(t))}
        for col,val in vals.items():check(val,r[col],'winner_loss_changes:'+col)
    for r in read(root/'large_winners.csv'):
        selected = [t for t in lineage if t['version'] == r['version'] and t['rule'] == r['rule'] and (r['scope'] == 'ALL_FOUR' or t['instrument'] == r['scope']) and (r['year'] == 'ALL' or t['original_year'] == r['year']) and float(t['original_gross_R']) > 0]
        selected.sort(key=lambda t:(-float(t['original_gross_R']),t['instrument'],t['original_trade_id']))
        top = selected[:int(r['top_n'])]
        preserved = lambda t:t['match_status'] == 'CLOSED_MATCH' and float(t['variant_gross_R']) >= float(t['original_gross_R'])-1e-8
        vals = {'original_count':len(top),'original_positive_R':sum(float(t['original_gross_R']) for t in top),
            'entries_lost':sum(t['match_status'] == 'NO_MATCHING_ENTRY' for t in top),
            'fully_preserved':sum(preserved(t) for t in top),
            'reduced':sum(t['match_status'] == 'CLOSED_MATCH' and not preserved(t) for t in top),
            'open_unresolved':sum(t['match_status'] == 'OPEN_TERMINAL' for t in top),
            'matched_variant_R':sum(float(t['variant_gross_R']) for t in top if t['match_status'] == 'CLOSED_MATCH')}
        for col,val in vals.items():check(val,r[col],'large_winners:'+col)
    for r in read(root/'gross_R_attribution.csv'):
        old = [t for t in trades if t['version'] == r['version'] and t['rule'] == 'CONTROL' and (r['scope'] == 'ALL_FOUR' or t['instrument'] == r['scope'])]
        new_trades = [t for t in trades if t['version'] == r['version'] and t['rule'] == r['rule'] and (r['scope'] == 'ALL_FOUR' or t['instrument'] == r['scope'])]
        lookup_old = {key(t):t for t in old};lookup_new = {key(t):t for t in new_trades}
        period = lambda t:r['year'] == 'ALL' or t['exit_time'][:4] == r['year']
        groups = {'matched_original_winners_delta_R':0.,'matched_original_losses_delta_R':0.,'matched_zero_delta_R':0.,
            'absent_closed_outcome_delta_R':0.,'year_transfer_out_R':0.,'year_transfer_in_R':0.,'new_closed_entry_R':0.}
        for t in old:
            if not period(t):continue
            n = lookup_new.get(key(t));x = float(t['gross_R'])
            if n is None:groups['absent_closed_outcome_delta_R'] -= x
            elif not period(n):groups['year_transfer_out_R'] -= x
            else:
                field = 'matched_original_winners_delta_R' if x > 0 else 'matched_original_losses_delta_R' if x < 0 else 'matched_zero_delta_R'
                groups[field] += float(n['gross_R'])-x
        for t in new_trades:
            if not period(t):continue
            original = lookup_old.get(key(t))
            if original is None:groups['new_closed_entry_R'] += float(t['gross_R'])
            elif not period(original):groups['year_transfer_in_R'] += float(t['gross_R'])
        delta = sum(float(t['gross_R']) for t in new_trades if period(t))-sum(float(t['gross_R']) for t in old if period(t))
        for col,val in groups.items():check(val,r[col],'attribution:'+col)
        check(delta,r['gross_R_change'],'attribution:delta');check(sum(groups.values()),r['explained_delta_R'],'attribution:sum')
    for r in read(root/'activation_report.csv'):
        chosen = [t for t in trades if t['version'] == r['version'] and t['rule'] == r['rule'] and (r['scope'] == 'ALL_FOUR' or t['instrument'] == r['scope']) and (r['year'] == 'ALL' or t['exit_time'][:4] == r['year'])]
        vals = {'closed_trades':len(chosen),'threshold_activated_trades':sum(t['threshold_activated'] == 'True' for t in chosen),
            'initial_stop_exits':sum(t['exit_type'] == 'INITIAL_STOP' for t in chosen),
            'ATR_TRAIL_last_stop':sum(t['stop_source_at_exit'] == 'ATR_TRAIL' for t in chosen),
            'BE_last_stop':sum(t['stop_source_at_exit'] == 'BREAK_EVEN_1R' for t in chosen),
            'LOCK_last_stop':sum(t['stop_source_at_exit'] == 'LOCK_1R_AFTER_2R' for t in chosen),
            'gap_exits':sum(t['gap_exit'] == 'True' for t in chosen),
            'activated_nonpositive_exits':sum(t['threshold_activated'] == 'True' and float(t['gross_R']) <= 0 for t in chosen)}
        for col,val in vals.items():check(val,r[col],'activation:'+col)
    historical = json.loads((root/'HISTORICAL_BENCHMARKS.json').read_text())
    assert not historical['executed_in_this_experiment'] and not historical['combined']
    for name,evidence in historical['files'].items():
        original_path = HERE.parent/'t3_m15_entry_regime_v1/results'/name
        assert A.sha(original_path) == evidence['reference_sha256']
        expected = [r for r in read(original_path) if r['rule'] in ('A6','A7')]
        assert expected == read(root/('historical_A6_A7_'+name))
    hashes = json.loads((root/'GENERATED_SHA256.json').read_text())
    assert all(A.sha(root/name) == h for name,h in hashes.items())
    result = {'status':'PASS','independence':'Separate recursive standard-library implementation, same author; external reviewer PENDING',
        'closed_records_verified':checked,'terminal_positions_verified':len(opened),'stop_decisions_verified':path_decisions,
        'entry_opportunities_verified':signal_checks,'report_rows_verified':report_rows,'november_rows_verified':november_rows,
        'lineage_rows_verified':len(lineage),'artifact_hashes_verified':len(hashes),'numeric_tolerance':1e-8,
        'maximum_numeric_differences':DELTAS,'replays':details}
    report.write_text(json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:result[k] for k in ('status','closed_records_verified','stop_decisions_verified','entry_opportunities_verified','report_rows_verified')}))


if __name__ == '__main__':
    p = argparse.ArgumentParser();p.add_argument('--data-root',type=Path,required=True)
    p.add_argument('--root',type=Path,default=HERE/'results');p.add_argument('--report',type=Path,default=HERE/'AUDIT_RESULTS.json')
    a = p.parse_args();main(a.data_root,a.root,a.report)
