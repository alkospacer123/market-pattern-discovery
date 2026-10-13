"""Reproduce all six signal-Close configurations before any historical Next Open."""
import argparse,csv,json,sys
from pathlib import Path
import common as C
import engine as E
import scalar as S

def load(root,scalar=False):
    if scalar:return C.load_sources(root)
    assert C.git('rev-parse','HEAD',root=root).decode().strip()==C.DATA_SHA
    assert not C.git('status','--porcelain',root=root).strip()
    sources=json.loads((C.HERE/'SPEC.json').read_text())['sources'];frames={}
    for source in sources:
        path=root/source['path'];assert C.file_sha(path)==source['full_sha256']
        assert C.git('hash-object','--',str(path),root=root).decode().strip()==source['git_blob_sha']
        f=E.read_source(path)
        assert len(f)==source['used_candles'] and f.index[0].isoformat()==source['first_close'] and f.index[-1].isoformat()==source['last_close']
        frames[source['instrument']]=E.features(f)
    return frames,sources

def compute(frames,scalar=False,mode='SIGNAL_CLOSE'):
    out={k:[] for k in ('trades','OPEN_POSITIONS','stop_decisions','entry_opportunities','observed_gaps','PERIOD_END_OPEN_POSITIONS')}
    for v in C.VERSIONS:
        for rule in E.RULES:
            for symbol in C.SYMBOLS:
                if mode=='SIGNAL_CLOSE':r=S.simulate(frames[symbol],symbol,v,rule) if scalar else E.replay(frames[symbol],symbol,v,rule)
                else:r=S.simulate(frames[symbol],symbol,v,rule,mode) if scalar else E.replay(frames[symbol],symbol,v,rule,mode)
                for k,rows in zip(out,r):out[k].extend(([rows] if rows else []) if k=='OPEN_POSITIONS' else rows)
    return out

def persist(out,d):
    d.mkdir(parents=True,exist_ok=True)
    for k,rows in out.items():
        if 'POSITIONS' in k:C.write_json(d/(k+'.json'),rows)
        else:C.write_csv(d/(k+'.csv'),rows)

def gate(out,d):
    cmp=C.Comparison()
    refs={'C1':('t3_m15_combined_v1',497),'T1':('t3_m15_session_entry_v1',499),'COMBINED':('t3_m15_t1_s1_v1',500)}
    for rule,(folder,pr) in refs.items():
        for name in out:
            if name in ('observed_gaps','PERIOD_END_OPEN_POSITIONS') and rule=='C1':continue
            path=f'IntradayLab/{folder}/results/{name}.'+('json' if 'POSITIONS' in name else 'csv')
            ref=json.loads(C.historical(path)) if path.endswith('.json') else C.reference(path)
            ref=[r for r in ref if r['rule']==rule];actual=[r for r in out[name] if r['rule']==rule]
            key=['version','instrument','trade_id'] if name in ('trades','OPEN_POSITIONS') else ['version','instrument','bar_close_time'] if name=='stop_decisions' else ['version','instrument','signal_time'] if name=='entry_opportunities' else ['version','instrument','current_close'] if name=='observed_gaps' else ['version','instrument','month']
            cmp.rows(actual,ref,f'PR{pr}_{rule}_{name}',key,('C1_R','net_R','c1_price_unit','initial_risk_ticks','exit_C1_and_funding'))
    published={'C1':[(1.6373,151.06,19),(1.7377,176.34,17)],'T1':[(1.5475,135.52,17),(1.6784,175.74,18)],'COMBINED':[(1.5864,155.71,17),(1.7191,192.82,17)]}
    summary=[]
    for rule,pairs in published.items():
        for v,(pf,r,pos) in zip(C.VERSIONS,pairs):
            t=[x for x in out['trades'] if x['rule']==rule and x['version']==v]
            p=sum(x['gross_R'] for x in t if x['gross_R']>0);n=-sum(x['gross_R'] for x in t if x['gross_R']<0)
            months=sum(sum(x['gross_R'] for x in t if x['exit_time'].strftime('%Y-%m')==m)>0 for m in C.CALENDAR)
            cmp.value(round(p/n,4),pf,'PUBLISHED',v+rule,'PF');cmp.value(round(p-n,2),r,'PUBLISHED',v+rule,'R');cmp.value(months,pos,'PUBLISHED',v+rule,'positive_months')
            summary.append({'rule':rule,'version':v,'closed':len(t),'PF':p/n,'R':p-n,'positive_months':months,'terminal_OPEN':sum(x['rule']==rule and x['version']==v for x in out['OPEN_POSITIONS'])})
    C.write_csv(d/'CONTROL_DIFF.csv',cmp.diffs,['table','row','field','actual','expected'])
    result={'status':'PASS' if not cmp.diffs else 'FAIL','fields_compared':cmp.fields,'differences':len(cmp.diffs),'absolute_tolerance':1e-8,'tables':cmp.tables,'summary':summary,'max_numeric_delta':max(cmp.maxima.values(),default=0)}
    C.write_json(d/'CONTROL_GATE.json',result)
    assert not cmp.diffs,'CONTROL_MISMATCH_STOP_NEW_CALCULATIONS'
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data-root',type=Path,default=Path('/workspace/market-pattern-data'));p.add_argument('--output',type=Path,default=C.HERE/'control');p.add_argument('--scalar',action='store_true');a=p.parse_args()
    frames,sources=load(a.data_root,a.scalar);out=compute(frames,a.scalar);persist(out,a.output);r=gate(out,a.output)
    C.write_json(a.output/'SOURCE_MANIFEST.json',{'sources':sources,'data_commit':C.DATA_SHA,'OHLC_2025_plus_parsed':False})
    print(json.dumps(r,indent=2))
