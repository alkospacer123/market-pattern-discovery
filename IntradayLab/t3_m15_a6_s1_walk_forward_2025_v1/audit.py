"""Fresh scalar replay and independently selected WF arithmetic/presentation audit.

Does not import engine, accounting, render, analysis, pipeline or primary_metrics.
No primary trajectory or metric function is called. Shared helpers only IO,
constants, scalar indicator recursion and comparison. External review PENDING.
"""
import argparse,csv,json,math,statistics
from datetime import datetime,timedelta
from pathlib import Path
import common as C,scalar as S,safe_source as B
from scalar_metrics import stats
START=datetime(2025,1,1,tzinfo=C.TZ)
SPEC=json.loads((C.HERE/'SPEC.json').read_text())
NAMES=('trades','OPEN_POSITIONS','stop_decisions','entry_opportunities','observed_gaps','PERIOD_END_OPEN_POSITIONS')
KEYS={'trades':['instrument','trade_id'],'OPEN_POSITIONS':['instrument','trade_id'],'stop_decisions':['instrument','bar_close_time','trade_id'],
 'entry_opportunities':['instrument','signal_time'],'observed_gaps':['instrument','current_close'],'PERIOD_END_OPEN_POSITIONS':['instrument','month','trade_id']}

def csvread(path):
    with path.open() as f:return list(csv.DictReader(f))
def months(period,end):
    if period.startswith('2025-'):return [period]
    if period=='FULL_WF':return [f'2025-{i:02d}' for i in range(1,end.month if end.year==2025 else 13)]
    if period.startswith('CUM_W'):return [f'2025-{i:02d}' for i in range(1,int(period[-1])*3+1)]
    q=int(period[-1]);return [f'2025-{i:02d}' for i in range((q-1)*3+1,q*3+1)]
def subset(rows,meta,end):
    wanted=months(meta['period'],end);group=meta['cohort'];result=[]
    for r in rows:
        new=START<=r['signal_time'] and START<=r['entry_time']
        if r['exit_time'].strftime('%Y-%m') not in wanted:continue
        if group=='NEW_WF_COHORT' and not new:continue
        if group=='INHERITED_DEVELOPMENT' and new:continue
        if meta['scope']!='ALL_FOUR' and r['instrument']!=meta['scope']:continue
        if meta['direction']!='ALL' and r['direction']!=meta['direction']:continue
        result.append(r)
    return result,wanted

def independent_recovery(rows):
    seq=sorted(rows,key=lambda r:(r['exit_time'],r['instrument'],r['trade_id']));curve=[0.]
    for r in seq:curve.append(curve[-1]+r['gross_R'])
    episodes=[];i=0;peak=0.;peak_at=None
    while i<len(seq):
        value=curve[i+1]
        if value>=peak:peak=value;peak_at=seq[i]['exit_time'];i+=1;continue
        start=i;depth=peak-value;trough=i
        while i<len(seq) and curve[i+1]<peak:
            if peak-curve[i+1]>depth:depth=peak-curve[i+1];trough=i
            i+=1
        recovered=i<len(seq)
        episodes.append({'peak_time':peak_at,'underwater_start':seq[start]['exit_time'],'max_depth_R':depth,
          'trough_time':seq[trough]['exit_time'],'recovered':recovered,'recovery_time':seq[i]['exit_time'] if recovered else None,
          'days_to_recovery':(seq[i]['exit_time']-seq[start]['exit_time']).total_seconds()/86400 if recovered else None,
          'peak_R':peak,'trough_R':curve[trough+1]})
    worst=max(episodes,key=lambda r:r['max_depth_R']) if episodes else None
    return {'median_holding_minutes':statistics.median(r['holding_minutes'] for r in seq) if seq else None,
      'mean_holding_minutes':statistics.mean(r['holding_minutes'] for r in seq) if seq else None,
      'max_DD_recovered':worst['recovered'] if worst else None,'max_DD_peak_time':worst['peak_time'] if worst else None,
      'max_DD_trough_time':worst['trough_time'] if worst else None,'max_DD_recovery_time':worst['recovery_time'] if worst else None,
      'max_DD_days_to_recovery':worst['days_to_recovery'] if worst else None,
      'terminal_underwater_R':episodes[-1]['peak_R']-math.fsum(r['gross_R'] for r in seq) if episodes and not episodes[-1]['recovered'] else 0.}

def changed(rows,calendar,scenario):
    if scenario=='BASE':return rows
    if scenario.startswith('LEAVE_OUT_'):return [r for r in rows if r['instrument']!=scenario[len('LEAVE_OUT_'):]]
    if scenario.startswith('R_STRESS_'):
        cost=float(scenario[len('R_STRESS_'):]);return [r|{'gross_R':r['gross_R']-cost} for r in rows]
    if scenario.startswith('EX_BEST'):
        n=int(scenario[len('EX_BEST'):].split('_')[0]);rank=sorted(calendar,key=lambda m:(-math.fsum(r['gross_R'] for r in rows if r['exit_time'].strftime('%Y-%m')==m),m));return [r for r in rows if r['exit_time'].strftime('%Y-%m') not in rank[:n]]
    n=int(scenario[len('EX_TOP'):].split('_')[0]);rank=sorted((r for r in rows if r['gross_R']>0),key=lambda r:(-r['gross_R'],r['exit_time'],r['instrument'],r['trade_id']));excluded={(r['instrument'],r['trade_id']) for r in rank[:n]};return [r for r in rows if (r['instrument'],r['trade_id']) not in excluded]

def verify_presentation(folder,tables,views,cmp):
    cells=0
    for filename in ('DETAILS.md','REPORT_RU.md'):
        lines=(folder/filename).read_text().splitlines();i=0
        while i<len(lines):
            if not lines[i].startswith('<!-- dataset '):i+=1;continue
            name=lines[i][13:-4].strip();expected=views[name[5:]] if name.startswith('view_') else tables[name];i+=1
            fields=[k.strip() for k in lines[i].strip('|').split('|')];i+=2;actual=[]
            while i<len(lines) and lines[i].startswith('|'):
                values=[k.strip() for k in lines[i].strip('|').split('|')];assert len(fields)==len(values);actual.append(dict(zip(fields,values)));i+=1
            cmp.value(len(actual),len(expected),'PRESENTATION_'+name,0,'row_count')
            for j,(a,e) in enumerate(zip(actual,expected)):
                for k,v in a.items():
                    raw=e.get(k)
                    if raw is None:w='N/A'
                    elif isinstance(raw,float):w=f'{raw:.6f}'
                    else:w=str(raw).replace('|',' / ').replace('\n',' ')
                    cmp.value(v,w,'PRESENTATION_'+name,j,k);cells+=1
    return cells

def run(root,primary,output):
    output.mkdir(parents=True,exist_ok=True);cmp=C.Comparison();origin=None;stages=[];cells=0
    for label,end in [('CONTROL',START)]+[(q['id'],datetime.fromisoformat(q['end'])) for q in SPEC['quarters']]:
        C.END=end;S.END=end;out={k:[] for k in NAMES};front={};receipts=[]
        assert C.git('rev-parse','HEAD',root=root).decode().strip()==C.DATA_SHA
        for spec in SPEC['sources']:
            symbol=spec['instrument'];raw,receipt=B.read_scalar(root/spec['path'],end);receipts.append(receipt)
            front[symbol]=C.build_features(raw);r=S.simulate(front[symbol],symbol,'TRAIL_375','C1','NEXT_OPEN')
            for k,v in zip(NAMES,r):out[k].extend(([v] if v else []) if k=='OPEN_POSITIONS' else v)
        folder=primary/label
        for name in NAMES:
            path=folder/'primary'/(name+('.json' if 'POSITIONS' in name else '.csv'))
            ref=json.loads(path.read_text()) if 'POSITIONS' in name else csvread(path)
            fields=sorted(set(k for r in ref for k in r)|set(k for r in out[name] for k in r))
            cmp.rows([{k:r.get(k) for k in fields} for r in out[name]],[{k:r.get(k) for k in fields} for r in ref],'FRESH_'+label+'_'+name,KEYS[name])
        indicator_ref=csvread(folder/'indicators.csv');indicator=[]
        for symbol,rows in front.items():
            for b in rows:
                r={'instrument':symbol,'close_time':b['at'],'ATR':b['atr'],'PreviousATR':b['previous_atr'],'PriorHigh':b['upper'],'PriorLow':b['lower'],'Signal':b['signal']}
                for label2,key in [('ADX','adx'),('Slope','slope'),('ATRRatio','ratio'),('AvailableAt','at')]:
                    r['H1'+label2]=b['h1'][key] if b['h1'] else None;r['H1Previous'+label2]=b['previous_h1'][key] if b['previous_h1'] else None
                indicator.append(r)
        cmp.rows(indicator,indicator_ref,'FRESH_INDICATORS_'+label,['instrument','close_time'])
        if label=='CONTROL':origin=out
        else:
            tables=json.loads((folder/'TABLES.json').read_text());view=json.loads((folder/'REPORT_TABLES.json').read_text())
            for name in ('summary','monthly','scenario_summary'):
                refs=csvread(folder/(name+'.csv'))
                for index,r in enumerate(refs):
                    selected,calendar=subset(out['trades'],r,end)
                    if name=='scenario_summary':selected=changed(selected,calendar,r['scenario'])
                    arithmetic=stats(selected,calendar)|independent_recovery(selected)
                    for k,v in arithmetic.items():cmp.value(v,r[k],'FRESH_ARITHMETIC_'+label+'_'+name,index,k)
                    if name!='scenario_summary':
                        op=[x for x in out['PERIOD_END_OPEN_POSITIONS'] if x['month']==calendar[-1] and (r['scope']=='ALL_FOUR' or x['instrument']==r['scope']) and (r['direction']=='ALL' or x['direction']==r['direction'])]
                        if r['cohort']!='CALENDAR_CLOSED':op=[x for x in op if (x['signal_time']>=START and x['entry_time']>=START)==(r['cohort']=='NEW_WF_COHORT')]
                        cmp.value(len(op),r['period_end_OPEN'],'FRESH_OPEN_'+label,index,'count')
                        cmp.value(math.fsum(x['unrealized_gross_R_at_last_close'] for x in op),r['period_end_OPEN_marked_R'],'FRESH_OPEN_'+label,index,'marked')
            for i,r in enumerate(csvread(folder/'marked_monthly.csv')):
                month=r['month'];m=int(month[-2:]);prev=f'2025-{m-1:02d}'
                a=origin['OPEN_POSITIONS'] if m==1 else [x for x in out['PERIOD_END_OPEN_POSITIONS'] if x['month']==prev]
                b=[x for x in out['PERIOD_END_OPEN_POSITIONS'] if x['month']==month]
                filtering=lambda xs:[x for x in xs if (r['scope']=='ALL_FOUR' or x['instrument']==r['scope']) and (r['direction']=='ALL' or x['direction']==r['direction'])]
                a,b=filtering(a),filtering(b);ts=filtering([x for x in out['trades'] if x['exit_time'].strftime('%Y-%m')==month])
                u0=math.fsum(x['unrealized_gross_R_at_last_close'] for x in a);u1=math.fsum(x['unrealized_gross_R_at_last_close'] for x in b);real=math.fsum(x['gross_R'] for x in ts)
                for k,v in {'CLOSED_R':real,'U_start_R':u0,'U_end_R':u1,'marked_R':real+u1-u0,'OPEN_start':len(a),'OPEN_end':len(b)}.items():cmp.value(v,r[k],'FRESH_MARKED_'+label,i,k)
            for i,r in enumerate(csvread(folder/'top_winners.csv')):
                selected,calendar=subset(out['trades'],r,end);wins=sorted([x for x in selected if x['gross_R']>0],key=lambda x:(-x['gross_R'],x['exit_time'],x['instrument'],x['trade_id']));row=wins[int(r['rank'])-1]
                for k in ('instrument','trade_id','signal_time','entry_time','exit_time','gross_R'):cmp.value(row[k],r[k],'FRESH_TOP_'+label,i,k)
            # CSV and JSON must contain identical data; compare scalar-arithmetic
            # audited primary CSV against every JSON cell with explicit types.
            for name,rows in tables.items():
                refs=csvread(folder/(name+'.csv'));cmp.value(len(rows),len(refs),'CSV_JSON_'+label+'_'+name,0,'row_count')
                for index,(row,ref) in enumerate(zip(rows,refs)):
                    for k,v in row.items():cmp.value(v,ref[k],'CSV_JSON_'+label+'_'+name,index,k)
            cells+=verify_presentation(folder,tables,view,cmp)
        stages.append({'stage':label,'source_receipts':receipts,'CLOSED':len(out['trades']),'OPEN':len(out['OPEN_POSITIONS'])})
        print(json.dumps({'fresh_audit_stage':label,'fields':cmp.fields,'differences':len(cmp.diffs)}),flush=True)
    result={'status':'PASS' if not cmp.diffs else 'FAIL','fields_compared':cmp.fields,'differences':len(cmp.diffs),'max_numeric_delta':max(cmp.maxima.values(),default=0),'tolerance':1e-8,
        'presentation_cells':cells,'fresh_scalar_replay_all_5_stages':True,'primary_engine_or_metrics_imported':False,
        'independence':'computational; independent tokenization, recursive features, position machine, metric arithmetic, recovery algorithm; one author; external human review PENDING','stages':stages}
    C.write_json(output/'AUDIT_RESULT.json',result);C.write_csv(output/'DIFFERENCES.csv',cmp.diffs,['table','row','field','actual','expected']);assert not cmp.diffs,'INDEPENDENT_AUDIT_STOP'
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data-root',type=Path,default=Path('/workspace/market-pattern-data'));p.add_argument('--primary',type=Path,default=C.HERE/'results');p.add_argument('--output',type=Path,default=C.HERE/'audit');a=p.parse_args();run(a.data_root,a.primary,a.output)
