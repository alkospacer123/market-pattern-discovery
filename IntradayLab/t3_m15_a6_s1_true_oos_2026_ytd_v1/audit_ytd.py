"""Fresh stdlib/scalar process. Never imports primary engine, runner or reporting."""
import argparse
import csv
from datetime import datetime, timedelta
import hashlib
import json
import math
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'t3_m15_a6_s1_walk_forward_2025_v1'))
import common as C
import scalar as S
from scalar_metrics import stats
START=datetime(2026,1,1,tzinfo=C.TZ)
CEILING=datetime(2026,10,13,tzinfo=C.TZ)
NAMES=('trades','OPEN_POSITIONS','stop_decisions','entry_opportunities','observed_gaps','PERIOD_END_OPEN_POSITIONS')
KEYS={'trades':['instrument','trade_id'],'OPEN_POSITIONS':['instrument','trade_id'],
      'stop_decisions':['instrument','bar_close_time','trade_id'],'entry_opportunities':['instrument','signal_time'],
      'observed_gaps':['instrument','current_close'],'PERIOD_END_OPEN_POSITIONS':['instrument','month','trade_id']}

def read(path,end):
    assert end<=CEILING
    rows=[];previous=None;digest=hashlib.sha256();reason='EOF'
    with path.open('rb',buffering=0) as f:
        header=f.readline();assert header==b'Ticker;Datetime;Open;High;Low;Close;Volume\n';digest.update(header)
        while True:
            tokens=[]
            for field in range(2):
                token=bytearray()
                while True:
                    ch=f.read(1)
                    if not ch:break
                    if ch==b';':break
                    token+=ch;assert len(token)<30
                if not ch:break
                tokens.append(bytes(token))
            if not tokens:break
            assert len(tokens)==2
            at=datetime.fromisoformat(tokens[1].decode()).replace(tzinfo=C.TZ)+C.STEP
            if at>=end:reason='FIRST_COMPLETION_OUTSIDE_AUTHORIZED_CUTOFF';break
            assert C.START<=at and (previous is None or at>previous)
            assert at.minute%15==0 and at.second==0
            assert tokens[0].decode()==path.parent.name
            tail=f.readline();assert tail.endswith(b'\n')
            numbers=[float(v) for v in tail.rstrip(b'\r\n').split(b';')]
            assert len(numbers)==5 and all(math.isfinite(v) for v in numbers)
            o,h,l,c,v=numbers;assert l<=min(o,c)<=max(o,c)<=h
            rows.append(dict(at=at,o=o,h=h,l=l,c=c,v=v));previous=at
            digest.update(b';'.join(tokens)+b';'+tail)
        receipt={'instrument':path.parent.name,'rows':len(rows),'prefix_sha256':digest.hexdigest(),
                 'bytes_consumed':f.tell(),'stop_reason':reason,'excluded_OHLCV_read':False,'buffering':0}
    return rows,receipt

def csvread(path):
    with path.open(newline='') as f:return list(csv.DictReader(f))

def basic(rows):
    values=stats(rows,[])
    return {k:values[v] for k,v in [('closed','closed'),('wins','wins'),('losses','losses'),('gross_R','gross_R'),
        ('gross_PF','gross_PF'),('expectancy_R','expectancy_R'),('avg_win_R','mean_WIN_R'),
        ('avg_loss_R','mean_LOSS_R'),('closed_R_drawdown','closed_R_drawdown')]}

def metrics_check(cmp,rows,ref,label):
    for k,v in basic(rows).items():cmp.value(v,ref[k],label,0,k)

def audit(root,folder,end):
    assert C.git('rev-parse','HEAD',root=root).decode().strip()==C.DATA_SHA
    C.END=end;S.END=end
    out={k:[] for k in NAMES};features=[];coverage=[];receipts=[]
    for symbol in C.SYMBOLS:
        bars,receipt=read(root/f'forever/{symbol}/{symbol}_M15.csv',end);receipts.append(receipt)
        feature=C.build_features(bars)
        replay=S.simulate(feature,symbol,'TRAIL_375','C1','NEXT_OPEN')
        for k,rows in zip(NAMES,replay):out[k].extend(([rows] if rows else []) if k=='OPEN_POSITIONS' else rows)
        for b in feature:
            r={'instrument':symbol,'close_time':b['at'],'ATR':b['atr'],'PreviousATR':b['previous_atr'],
               'PriorHigh':b['upper'],'PriorLow':b['lower'],'Signal':b['signal']}
            for name,key in [('ADX','adx'),('Slope','slope'),('ATRRatio','ratio'),('AvailableAt','at')]:
                r['H1'+name]=b['h1'][key] if b['h1'] else None
                r['H1Previous'+name]=b['previous_h1'][key] if b['previous_h1'] else None
            features.append(r)
        ytd=[b for b in bars if b['at']>=START]
        coverage.append({'instrument':symbol,'loaded_bars_2023_YTD':len(bars),'bars_2026':len(ytd),
            'first_2026_close':ytd[0]['at'] if ytd else None,'last_available_open':bars[-1]['at']-C.STEP,
            'last_available_close':bars[-1]['at'],'uncovered_tail_start':bars[-1]['at'],
            'uncovered_tail_end_exclusive':end,'tail_days':(end-bars[-1]['at']).total_seconds()/86400})
    cmp=C.Comparison()
    for mode in ('primary','scalar'):
        for name in NAMES:
            path=folder/mode/(name+('.json' if 'POSITIONS' in name else '.csv'))
            ref=json.loads(path.read_text()) if 'POSITIONS' in name else csvread(path)
            fields=sorted(set(k for r in out[name]+ref for k in r))
            cmp.rows([{k:r.get(k) for k in fields} for r in out[name]],
                     [{k:r.get(k) for k in fields} for r in ref],'FRESH_'+mode+'_'+name,KEYS[name])
    cmp.rows(features,csvread(folder/'indicators.csv'),'FRESH_ALL_INDICATORS',['instrument','close_time'])
    frozen=C.HERE/'results/W4'
    cmp.rows([r for r in features if r['close_time']<START],csvread(frozen/'indicators.csv'),
             'PUBLISHED_W4_INDICATORS',['instrument','close_time'])
    summary=json.loads((folder/'SUMMARY.json').read_text())
    closed=[r for r in out['trades'] if START<=r['exit_time']<end]
    new=[r for r in closed if r['signal_time']>=START and r['entry_time']>=START]
    inherited=[r for r in closed if r not in new]
    metrics_check(cmp,closed,summary['calendar_CLOSED'],'CALENDAR')
    metrics_check(cmp,new,summary['new_2026_entry_CLOSED'],'NEW_COHORT')
    metrics_check(cmp,inherited,summary['inherited_pre_2026_CLOSED'],'INHERITED')
    cmp.value(len(out['OPEN_POSITIONS']),summary['OPEN'],'TERMINAL',0,'OPEN')
    cmp.rows(coverage,summary['source_coverage'],'COVERAGE',['instrument'])
    for i,r in enumerate(summary['slices']):
        selected=[t for t in closed if (r['scope']=='ALL_FOUR' or t['instrument']==r['scope']) and (r['direction']=='ALL' or t['direction']==r['direction'])]
        metrics_check(cmp,selected,r,'SLICE_'+str(i))
        count=sum((r['scope']=='ALL_FOUR' or t['instrument']==r['scope']) and (r['direction']=='ALL' or t['direction']==r['direction']) for t in out['OPEN_POSITIONS'])
        cmp.value(count,r['OPEN'],'SLICE',i,'OPEN')
    calendar=[f'2026-{m:02d}' for m in range(1,end.month+1)]
    arithmetic=stats(closed,calendar)
    for r in summary['monthly']:
        metrics_check(cmp,[t for t in closed if t['exit_time'].strftime('%Y-%m')==r['month']],r,'MONTH_'+r['month'])
        lo=datetime.fromisoformat(r['month']+'-01').replace(tzinfo=C.TZ)
        hi=(lo+timedelta(days=32)).replace(day=1)
        for c in r['coverage']:
            at=[x['close_time'] for x in features if x['instrument']==c['instrument'] and lo<=x['close_time']<min(hi,end)]
            last=next(v['last_available_close'] for v in coverage if v['instrument']==c['instrument'])
            state='NO_COVERAGE' if not at else 'PARTIAL_SOURCE_END' if lo<=last<min(hi,end) else 'PARTIAL_YTD_CUTOFF' if end<hi else 'AVAILABLE_SOURCE_PREFIX'
            for k,v in dict(bars=len(at),first_close=at[0] if at else None,last_close=at[-1] if at else None,coverage=state).items():cmp.value(v,c[k],'MONTH_COVERAGE',r['month']+c['instrument'],k)
        states=[c['coverage'] for c in r['coverage']]
        state='NO_COVERAGE' if set(states)=={'NO_COVERAGE'} else 'PARTIAL' if set(states)!={'AVAILABLE_SOURCE_PREFIX'} else 'AVAILABLE_SOURCE_PREFIX'
        cmp.value(state,r['coverage_status'],'MONTH_STATE',r['month'],'coverage_status')
        sign='NO_COVERAGE' if state=='NO_COVERAGE' else 'POSITIVE' if r['gross_R']>0 else 'NEGATIVE' if r['gross_R']<0 else 'ZERO'
        cmp.value(sign,r['result_sign'],'MONTH_SIGN',r['month'],'result_sign')
    for key in ('positive_months','negative_months'):cmp.value(arithmetic[key],summary[key],'MONTH_COUNTS',0,key)
    for k,v in summary['diagnostics'].items():
        if k.startswith('top1_winners') or k.startswith('top1_share_positive') or k.startswith('ex_top1_winners'):
            top=max((r['gross_R'] for r in closed if r['gross_R']>0),default=0)
            a={'top1_winners_R':top,'top1_share_positive_R':top/arithmetic['positive_R'] if arithmetic['positive_R'] else None,
                'ex_top1_winners_R':arithmetic['gross_R']-top,'ex_top1_winners_PF':(arithmetic['positive_R']-top)/arithmetic['negative_R'] if arithmetic['negative_R'] else None}[k]
        elif k.endswith('_share_total_R'):a=arithmetic[k.replace('_share_total_R','_share_annual_R')]
        else:a=arithmetic[k]
        cmp.value(a,v,'DIAGNOSTICS',0,k)
    ranked=sorted((r for r in closed if r['gross_R']>0),key=lambda r:(-r['gross_R'],r['exit_time'],r['instrument'],r['trade_id']))[:10]
    cmp.rows(ranked,summary['top_winners'],'TOP_WINNERS',['instrument','trade_id'])
    for i,r in enumerate(summary['historical_comparison']):
        y=int(r['year']);selected=[t for t in out['trades'] if t['exit_time'].year==y]
        metrics_check(cmp,selected,r,'HISTORY_'+str(y))
        a=stats(selected,[f'{y}-{m:02d}' for m in range(1,13)])
        for k in ('positive_months','negative_months'):cmp.value(a[k],r[k],'HISTORY_MONTHS',y,k)
    carry=summary['carry'];start=carry['start_position'];key=(start['instrument'],start['trade_id'])
    ref=json.loads((frozen/'scalar/OPEN_POSITIONS.json').read_text())
    cmp.rows(ref,[start],'CARRY_START',['instrument','trade_id'])
    outcome=next(r for r in out['trades']+out['OPEN_POSITIONS'] if (r['instrument'],r['trade_id'])==key)
    cmp.rows([outcome],[carry['outcome']],'CARRY_OUTCOME',['instrument','trade_id'])
    first=next(r for r in out['stop_decisions'] if (r['instrument'],r['trade_id'])==key and r['bar_close_time']>=START)
    cmp.rows([first],[carry['first_2026_stop']],'CARRY_FIRST_STOP',['instrument','trade_id'])
    for name,rows in [('trades_2026',closed),('new_2026_trades',new),('inherited_2025_trades',inherited)]:
        cmp.rows(rows,csvread(folder/(name+'.csv')),'COHORT_CSV_'+name,['instrument','trade_id'])
    tables=json.loads((folder/'REPORT_TABLES.json').read_text())
    for name,rows in tables.items():
        ref=csvread(folder/(name+'.csv'));cmp.value(len(rows),len(ref),'CSV_JSON',name,'row_count')
        for i,(a,b) in enumerate(zip(rows,ref)):
            for k,v in a.items():cmp.value(v,b[k],'CSV_JSON_'+name,i,k)
    cells=0;lines=(folder/'REPORT_RU.md').read_text().splitlines()
    for i,line in enumerate(lines):
        if not line.startswith('<!-- dataset '):continue
        name=line[len('<!-- dataset '):-4].strip();fields=[x.strip() for x in lines[i+1].strip('|').split('|')]
        j=i+3;refs=tables[name];actual=[]
        while j<len(lines) and lines[j].startswith('|'):
            actual.append([x.strip() for x in lines[j].strip('|').split('|')]);j+=1
        cmp.value(len(actual),len(refs),'MARKDOWN',name,'rows')
        for index,(a,b) in enumerate(zip(actual,refs)):
            assert len(a)==len(fields)
            for k,v in zip(fields,a):
                raw=b.get(k);w='N/A' if raw is None else f'{raw:.9f}' if isinstance(raw,float) else str(raw).replace('|',' / ').replace('\n',' ')
                cmp.value(v,w,'MARKDOWN_'+name,index,k);cells+=1
    result={'status':'PASS' if not cmp.diffs else 'FAIL','fields_compared':cmp.fields,
        'markdown_cells':cells,'differences':len(cmp.diffs),'max_numeric_delta':max(cmp.maxima.values(),default=0),
        'absolute_tolerance':1e-8,'fresh_scalar_process':True,'primary_imported':False,
        'independent_reader':True,'cost_deductions':False,'source_receipts':receipts,'tables':cmp.tables,
        'external_human_review':'PENDING'}
    C.write_json(folder/'INDEPENDENT_AUDIT.json',result)
    C.write_csv(folder/'INDEPENDENT_AUDIT_DIFF.csv',cmp.diffs,['table','row','field','actual','expected'])
    print(json.dumps({k:result[k] for k in ('status','fields_compared','markdown_cells','differences','max_numeric_delta')}),flush=True)
    assert not cmp.diffs,('INDEPENDENT_AUDIT_STOP',cmp.diffs[:3])

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data-root',type=Path,required=True)
    p.add_argument('--results',type=Path,required=True);p.add_argument('--end-exclusive',required=True)
    a=p.parse_args();audit(a.data_root,a.results,datetime.fromisoformat(a.end_exclusive))
