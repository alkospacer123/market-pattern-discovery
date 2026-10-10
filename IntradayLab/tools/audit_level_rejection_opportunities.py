#!/usr/bin/env python3
"""Independent 2023-only segment/integer-grid opportunity audit.

No scanner/replay imports. Six-element slices of independent session segments,
integer price units, separate confirmation and scheduled-Open adjudication.
Never infer fills, positions, exits, target hits or economic outcomes.
"""
import argparse
import csv
from collections import Counter
from datetime import datetime, timedelta
from decimal import Decimal
import hashlib
import io
import json
from pathlib import Path
import subprocess

LAB = Path(__file__).resolve().parents[1]
DEST = LAB / 'results/stage2_level_rejection_m5_opportunity_v1'
CFG = LAB / 'config/stage2_level_rejection_m5_opportunity_v1.json'
SCALE = 1000
BASE = '832739dfb9c9ec8f4f2fc1768d7fc07fbc69521c'
START = '712dfb2d74c1ba9a1870ef56572ee25be94e8c48'
FREEZE = '1487d7e041e9e32122a5df9ae280386da8ebadb1'


def git(root,*args):
    return subprocess.check_output(['git','-C',str(root),*args],text=True).strip()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path,obj):
    path.write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n')


def csv_out(path,rows):
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n'); w.writeheader(); w.writerows(rows)


def grid(s,t):
    if s=='CNYRUBF': return 10 if t<datetime(2023,9,27,19) else 1
    return {'USDRUBF':10,'GLDRUBF':100,'IMOEXF':500}[s]


def session(t):
    # Independently reproduce only the frozen research calendar, not full venue hours.
    if t.year!=2023 or t.weekday()>4 or (t.month,t.day) in {(1,1),(1,2),(1,7),(2,23),(3,8),(5,1),(5,9),(6,12),(11,4)}:
        return None
    extended=datetime(2023,3,13).date()<=t.date()<datetime(2023,3,21).date()
    for h,m,end_h,end_m in ((10,0,14,0),(14,15 if extended else 5,18,50)):
        a=t.replace(hour=h,minute=m,second=0,microsecond=0)
        z=t.replace(hour=end_h,minute=end_m,second=0,microsecond=0)
        if a<=t and t+timedelta(minutes=5)<=z: return (a,z)
    return None


def independent_read(root,m):
    assert git(root,'rev-parse','HEAD')==m['source_ref']
    assert not git(root,'status','--porcelain=v1','--untracked-files=all')
    data={}; provenance={}
    for s,spec in m['inputs'].items():
        assert git(root,'ls-files','--stage','--',spec['path']).split()[1:3]==[spec['blob'],'0']
        path=root/spec['path']; before=path.stat()
        with path.open('rb',buffering=0) as raw:
            assert isinstance(raw,io.FileIO)
            payload=raw.read(spec['prefix_bytes'])
            assert raw.tell()==spec['prefix_bytes']  # no EOF or next-row probe
        assert path.stat()==before
        assert len(payload)==spec['prefix_bytes'] and payload.endswith(b'\n')
        assert hashlib.sha256(payload).hexdigest()==spec['prefix_sha256']
        reader=csv.reader(io.StringIO(payload.decode('utf-8-sig')),delimiter=';')
        assert next(reader)==['Ticker','Datetime','Open','High','Low','Close','Volume']
        rows=[]; regimes=Counter()
        for fields in reader:
            assert len(fields)==7 and fields[0]==s
            t=datetime.strptime(fields[1],'%Y-%m-%d %H:%M:%S')
            assert t.year==2023 and t.minute%5==0 and t.second==0
            values=[Decimal(x) for x in fields[2:]]
            assert all(x.is_finite() for x in values)
            prices=[int(x*SCALE) for x in values[:4]]
            assert all(Decimal(v)==p*SCALE for v,p in zip(prices,values[:4]))
            o,h,l,c=prices; v=values[4]
            assert 0<l<=min(o,c)<=max(o,c)<=h and v>=0
            assert all(p%grid(s,t)==0 for p in prices)
            assert not rows or t>rows[-1][0]
            rows.append((t,o,h,l,c,v>0))
            regimes[str(Decimal(grid(s,t))/SCALE)]+=1
        assert len(rows)==spec['rows_2023'] and str(rows[0][0])==spec['first']
        data[s]=rows
        provenance[s]={'source_ref':m['source_ref'],'blob':spec['blob'],'path':spec['path'],
                       'prefix_sha256':hashlib.sha256(payload).hexdigest(),'bytes_read':len(payload),
                       'rows':len(rows),'first':str(rows[0][0]),'last':str(rows[-1][0]),
                       'grid_regime_rows':dict(regimes),'bytes_2024_plus_read':0,'bytes_2025_plus_read':0,
                       'physical_reader':'unbuffered io.FileIO exact byte read'}
    return data,provenance


def reconstruct(s,rows,delay):
    # Feature segmentation is independent of scanner's streaming deque.
    parts=[]; part=[]; previous=None; old_window=None; dates=set(); count=Counter()
    for row in rows:
        t=row[0]; w=session(t); usable=w is not None and row[5]
        if not usable or previous is None or t-previous!=timedelta(minutes=5) or w!=old_window:
            if part: parts.append(part)
            part=[]
        if usable:
            part.append(row); dates.add(t.date().isoformat()); count['observed_m5']+=1
        previous=t if usable else None; old_window=w if usable else None
    if part: parts.append(part)
    confirmed=[]; raw_month=Counter(); penetrations_month=Counter()
    for part in parts:
        count['warmup']+=min(6,len(part)); cooldown={}
        for i in range(6,len(part)):
            t,o,h,l,c,_=part[i]; past=part[i-6:i]
            high=max(r[2] for r in past); low=min(r[3] for r in past); tick=grid(s,t)
            count['evaluated_test_bars']+=1
            if h>=high+tick or l<=low-tick:
                count['level_penetration_bars']+=1; penetrations_month[t.strftime('%Y-%m')]+=1
            short=h>=high+tick and c<=high-tick
            long=l<=low-tick and c>=low+tick
            if short and long: count['AMBIGUOUS_BOTH_SIDES']+=1; continue
            if not (long or short): continue
            count['raw_rejections']+=1; raw_month[t.strftime('%Y-%m')]+=1
            direction=1 if long else -1
            if direction in cooldown and t-cooldown[direction]<timedelta(minutes=30):
                count['DEDUP_30MIN']+=1; continue
            cooldown[direction]=t; count['unique_confirmed']+=1
            confirmed.append({'symbol':s,'scenario':delay,'direction':'LONG' if long else 'SHORT',
                              'signal_at':str(t),'available_at':str(t+timedelta(minutes=5+delay)),
                              'target_at':str(t+timedelta(minutes=10+delay)),
                              'level':low if long else high,'opposite':high if long else low,
                              'stop':l-tick if long else h+tick})
    # Adjudication receives only Open + presence flag, never target OHLC.
    openings={r[0]:(r[1],r[5]) for r in rows}
    for event in confirmed:
        t=datetime.fromisoformat(event['signal_at']); target=datetime.fromisoformat(event['target_at'])
        w=session(t); d=1 if event['direction']=='LONG' else -1
        event.update(entry_open=None,risk=None,legacy_take=None,full_net_take=None,
                     legacy_net_reward_to_gross_risk=None,full_net_reward_to_net_stop_loss=None,
                     within_known_range=None,tick=grid(s,t),status='',reason='')
        if session(target)!=w or target+timedelta(minutes=35)>w[1]:
            event.update(status='NONFILL',reason='SESSION_ENTRY_CUTOFF'); count['SESSION_ENTRY_CUTOFF']+=1; continue
        count['scheduled_in_window']+=1
        opening=openings.get(target)
        if opening is None or not opening[1]:
            event.update(status='UNKNOWN',reason='MISSING_SCHEDULED_M5_OPEN' if opening is None else 'ZERO_VOLUME_SCHEDULED_M5')
            count['UNKNOWN_POSSIBLE_FILL']+=1; continue
        # Only next source slot can reach its delivery deadline by strict target.
        next_completed=openings.get(t+timedelta(minutes=5))
        if next_completed is None or not next_completed[1]:
            event.update(status='NONFILL',reason='OBSERVABLE_GAP_RESET_BEFORE_ENTRY')
            count[event['reason']]+=1; continue
        entry=opening[0]; tick=grid(s,target); event['entry_open']=entry
        if d*(entry-event['level'])<tick:
            event.update(status='NONFILL',reason='OPEN_RECLAIM_NOT_PERSISTENT'); count[event['reason']]+=1; continue
        risk=d*(entry-event['stop']); event['risk']=risk
        if risk<=0:
            event.update(status='NONFILL',reason='INVALID_RISK'); count[event['reason']]+=1; continue
        if risk<4*tick:
            event.update(status='NONFILL',reason='RISK_BELOW_FOUR_TICKS'); count[event['reason']]+=1; continue
        # Integer ticks make outward rounding exact in the declared grids.
        legacy=entry+d*(3*risk+2*tick); full=entry+d*(3*risk+8*tick)
        assert legacy%tick==0 and full%tick==0
        assert (d*(legacy-entry)-2*tick)==3*risk
        assert (d*(full-entry)-2*tick)==3*(risk+2*tick)
        event.update(status='ELIGIBLE_GEOMETRY',tick=tick,legacy_take=legacy,full_net_take=full,
                     legacy_net_reward_to_gross_risk=3,full_net_reward_to_net_stop_loss=3,
                     within_known_range=d*(event['opposite']-entry)>=3*risk+8*tick)
        count['eligible_geometry']+=1
    return confirmed,dict(count),dates,raw_month,penetrations_month,len(parts)


def normalized(event):
    e=dict(event)
    for key in ('level','opposite','stop','entry_open','risk','tick','legacy_take','full_net_take'):
        if e.get(key) is not None: e[key]=Decimal(str(e[key]))
    for key in ('legacy_net_reward_to_gross_risk','full_net_reward_to_net_stop_loss'):
        if e.get(key) is not None: e[key]=Decimal(str(e[key]))
    return e


def protections(root):
    baseline=git(root,'ls-tree',BASE).splitlines()
    actual=git(root,'ls-tree','HEAD').splitlines()
    outer=lambda lines:[x for x in lines if x.split('\t')[1]!='IntradayLab']
    assert outer(baseline)==outer(actual)
    paths=git(root,'diff','--name-only',BASE,'HEAD').splitlines()
    assert all(p.startswith('IntradayLab/') for p in paths)
    for p in ('IntradayLab/config/stage2_level_rejection_m5_opportunity_v1.json',
              'IntradayLab/reports/STAGE2_LEVEL_REJECTION_M5_OPPORTUNITY_PREREGISTRATION.md'):
        expected=git(root,'rev-parse',FREEZE+':'+p)
        assert git(root,'hash-object',p)==expected
    # Every previously tracked file except this candidate's runner/tests is intact.
    mutable={'IntradayLab/tools/run_level_rejection_opportunities.py','IntradayLab/tests/test_level_rejection_opportunities.py'}
    old_changes=git(root,'diff','--name-only',START).splitlines()
    previous_paths=set(git(root,'ls-tree','-r','--name-only',START).splitlines())
    assert set(old_changes)&previous_paths<=mutable
    return {'base_main':BASE,'branch_start':START,'freeze_commit':FREEZE,
            'protected_root_entries':outer(actual),'protected_roots_equal_to_main':True,
            'all_prior_intraday_files_unchanged_except_candidate_runner_tests':True,
            'frozen_config_sha256':sha(CFG),
            'frozen_preregistration_sha256':sha(LAB/'reports/STAGE2_LEVEL_REJECTION_M5_OPPORTUNITY_PREREGISTRATION.md')}


def main():
    p=argparse.ArgumentParser(); p.add_argument('--data-root',type=Path,required=True); p.add_argument('--output',type=Path,default=DEST)
    args=p.parse_args(); out=args.output; m=json.loads(CFG.read_text())
    params=m['parameters']
    assert params['level_lookback_completed_m5']==6 and params['dedup_same_instrument_same_direction_minutes']==30
    assert params['min_initial_price_risk_ticks']==4 and params['max_session_entry_slack_minutes']==35
    assert all(params[k]==1 for k in ('min_level_penetration_ticks','min_close_reentry_ticks','stop_beyond_extreme_ticks','cost_C1_ticks_per_side'))
    assert params['planned_net_to_net_R']==params['planned_legacy_net_to_gross_R']=='3'
    authoritative=json.loads((out/'opportunity_funnel.json').read_text())
    data,provenance=independent_read(args.data_root,m)
    records=[]; counts={}; coverage={}; raw={}; penetrations={}; segments={}
    for s,rows in data.items():
        for delay in (10,15):
            events,c,days,rm,pm,n=reconstruct(s,rows,delay)
            counts[f'{s}_{delay}']=c; coverage[s]=days; raw[(s,delay)]=rm; penetrations[(s,delay)]=pm; segments[s]=n
            for event in events:
                for key in ('level','opposite','stop','entry_open','risk','tick','legacy_take','full_net_take'):
                    if event.get(key) is not None: event[key]=str(Decimal(event[key])/SCALE)
            records.extend(events)
    assert counts==authoritative['counters'], 'INDEPENDENT_FUNNEL_MISMATCH'
    identity=lambda e:(e['symbol'],e['scenario'],e['signal_at'])
    own={identity(e):normalized(e) for e in records}; original={identity(e):normalized(e) for e in authoritative['signals']}
    assert len(own)==len(records) and own==original, 'INDEPENDENT_ROW_MISMATCH'
    eligible=[e for e in records if e['status']=='ELIGIBLE_GEOMETRY']
    monthly=[]; daily=[]; weekly=[]; funnels=[]; reasons=[]; input_coverage=[]
    for s in m['instruments']:
        rows=data[s]; present={r[0] for r in rows if session(r[0]) and r[5]}
        source_dates={r[0].date() for r in rows}; expected=set(); day=rows[0][0].date()
        while day<=rows[-1][0].date():
            for minute in range(10*60,18*60+50,5):
                t=datetime(day.year,day.month,day.day)+timedelta(minutes=minute)
                if rows[0][0]<=t<=rows[-1][0] and session(t): expected.add(t)
            day+=timedelta(days=1)
        input_coverage.append({'symbol':s,'source_rows':len(rows),'source_days':len(source_dates),
             'source_first':str(rows[0][0]),'source_last':str(rows[-1][0]),'observed_research_days':len(coverage[s]),
             'observed_research_m5':len(present),'expected_research_slots_since_inception':len(expected),
             'missing_or_zero_volume_slots':len(expected-present),'continuous_positive_volume_segments':segments[s]})
        for delay in (10,15):
            es=[e for e in records if e['symbol']==s and e['scenario']==delay]
            accepted=[e for e in es if e['status']=='ELIGIBLE_GEOMETRY']; c=counts[f'{s}_{delay}']
            zero=len(coverage[s])-len({e['signal_at'][:10] for e in accepted})
            summary=authoritative['summary'][f'{s}_{delay}']
            assert summary['days_without_opportunities']==zero and summary['eligible']==len(accepted)
            funnels.append({'symbol':s,'scenario':delay,'level_penetration_bars':c.get('level_penetration_bars',0),
               'raw_rejections':c.get('raw_rejections',0),'ambiguous_both_sides':c.get('AMBIGUOUS_BOTH_SIDES',0),
               'dedup_30min':c.get('DEDUP_30MIN',0),'confirmed_signals':len(es),'scheduled_in_window':c.get('scheduled_in_window',0),
               'nonfill':sum(e['status']=='NONFILL' for e in es),'unknown':sum(e['status']=='UNKNOWN' for e in es),
               'eligible_full_net_3R':len(accepted),'within_known_range':sum(e['within_known_range'] for e in accepted),
               'observed_days':len(coverage[s]),'opportunities_per_observed_day':len(accepted)/len(coverage[s]),'days_without_opportunities':zero,
               'long_opportunities':sum(e['direction']=='LONG' for e in accepted),'short_opportunities':sum(e['direction']=='SHORT' for e in accepted)})
            for (status,reason),n in sorted(Counter((e['status'],e['reason']) for e in es).items()):
                reasons.append({'symbol':s,'scenario':delay,'status':status,'reason':reason,'count':n})
            for month in range(1,13):
                ym=f'2023-{month:02d}'; obs=sum(d.startswith(ym) for d in coverage[s]); ms=[e for e in es if e['signal_at'].startswith(ym)]
                ma=[e for e in accepted if e['signal_at'].startswith(ym)]
                state='PARTIAL_OR_UNVERIFIED_COVERAGE' if obs else ('PRE_INCEPTION_NO_COVERAGE' if ym<str(rows[0][0])[:7] else 'NO_COVERAGE')
                monthly.append({'symbol':s,'scenario':delay,'month':ym,'coverage':state,'observed_days':obs,
                    'level_penetration_bars':penetrations[(s,delay)].get(ym,0),'raw_rejections':raw[(s,delay)].get(ym,0),'confirmed_signals':len(ms),
                    'nonfill':sum(e['status']=='NONFILL' for e in ms),'unknown':sum(e['status']=='UNKNOWN' for e in ms),
                    'eligible_full_net_3R':len(ma),'within_known_range':sum(e['within_known_range'] for e in ma),
                    'opportunities_per_observed_day':len(ma)/obs if obs else None,
                    'days_without_opportunities':obs-len({e['signal_at'][:10] for e in ma}) if obs else None})
                original_month=next(x for x in authoritative['calendar'] if x['symbol']==s and x['scenario']==delay and x['month']==ym)
                assert original_month['eligible_geometry']==len(ma) and original_month['observed_dates']==obs
            for day in sorted(coverage[s]):
                n=sum(e['signal_at'].startswith(day) for e in accepted)
                daily.append({'symbol':s,'scenario':delay,'day':day,'eligible_full_net_3R':n})
                source_day=next(x for x in authoritative['daily'] if x['symbol']==s and x['scenario']==delay and x['day']==day)
                assert source_day['eligible_geometry']==n
            for week in sorted({datetime.fromisoformat(d).strftime('%G-W%V') for d in coverage[s]}):
                wd={d for d in coverage[s] if datetime.fromisoformat(d).strftime('%G-W%V')==week}
                n=sum(e['signal_at'][:10] in wd for e in accepted)
                weekly.append({'symbol':s,'scenario':delay,'iso_week':week,'observed_days':len(wd),'eligible_full_net_3R':n})
    combined=[]; combined_daily=[]; combined_monthly=[]
    union=set().union(*coverage.values())
    for delay in (10,15):
        sub=[e for e in eligible if e['scenario']==delay]; slots=Counter(e['target_at'] for e in sub)
        summary=authoritative['summary'][f'scenario_{delay}']
        assert summary['eligible_upper_bound']==len(sub) and summary['observed_union_days']==len(union)
        combined.append({'scenario':delay,'unique_opportunities':len(sub),'observed_union_days':len(union),
                         'opportunities_per_union_day':len(sub)/len(union),'days_without_opportunities':len(union)-len({e['signal_at'][:10] for e in sub}),
                         'distinct_instrument_entry_slots':len({(e['symbol'],e['target_at']) for e in sub}),
                         'distinct_wall_clock_slots':len(slots),'simultaneous_multi_instrument_slots':sum(n>1 for n in slots.values())})
        for day in sorted(union):
            combined_daily.append({'scenario':delay,'day':day,'eligible_full_net_3R':sum(e['signal_at'].startswith(day) for e in sub)})
        for month in range(1,13):
            ym=f'2023-{month:02d}'; obs=sum(d.startswith(ym) for d in union); n=sum(e['signal_at'].startswith(ym) for e in sub)
            combined_monthly.append({'scenario':delay,'month':ym,'observed_union_days':obs,'unique_opportunities':n,'opportunities_per_union_day':n/obs if obs else None})
    for name,rows in (('funnel',funnels),('rejections',reasons),('monthly',monthly),('daily',daily),('weekly',weekly),
                      ('input_coverage',input_coverage),('combined',combined),('combined_daily',combined_daily),('combined_monthly',combined_monthly)):
        csv_out(out/(name+'.csv'),rows)
    dump(out/'input_provenance.json',provenance)
    dump(out/'protected_trees.json',protections(LAB.parent))
    dump(out/'independent_audit.json',{'status':'PASS_INDEPENDENT_ALGORITHM','method':'independent CSV reader, contiguous session segments, six-row slices, integer grids; separate signal confirmation and Open adapter; no production imports',
         'compared_confirmed_rows':len(records),'compared_monthly_rows':len(monthly),'compared_daily_rows':len(daily),
         'all_funnels_rows_reasons_geometry_months_days_match':True,'combined':combined,
         'authoritative_funnel_sha256':sha(out/'opportunity_funnel.json'),'scanner_sha256':sha(LAB/'tools/run_level_rejection_opportunities.py'),
         'auditor_sha256':sha(Path(__file__)),'config_sha256':sha(CFG),
         'physical_protected_bytes_read_authoritative_and_audit':0,
         'external_acceptance':'PENDING; independent algorithm executed by the same task agent, not an external reviewer',
         'economic_baseline_pass':False,'actual_executable_trade_count':None})
    print(json.dumps({'audit':'PASS_INDEPENDENT_ALGORITHM','confirmed_rows':len(records),'combined':combined}))


if __name__=='__main__': main()
